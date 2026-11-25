"""Decide quando o Ignis foi chamado: pela frase ou pelo nome."""

from enum import Enum
from pathlib import Path
from typing import Protocol

from ignis_pc.audio import AMOSTRAS_POR_BLOCO, TAXA, Bloco
from ignis_pc.sessao import EstadoDoPC


class Gatilho(Enum):
    FRASE = "frase"
    """'Ignis Arise': vale sempre, inclusive com o PC bloqueado ou em repouso."""
    NOME = "nome"
    """'Ignis' no começo do pedido: só vale com o PC em uso."""


# As frases já estão no formato do modelo (pedaços do vocabulário dele). Para
# gerar outras, use o arquivo bpe.model do pacote com o sentencepiece:
#   " ".join(sp.encode("IGNIS ARISE", out_type=str))
# As iscas competem com a frase certa e, quando vencem, não ativam nada (D47).
ISCAS_DA_FRASE = (
    "▁I G RI S ▁A RI SE @isca_IGRIS",
    "▁I RI S ▁A RI SE @isca_IRIS",
    "▁A G NE S ▁A RI SE @isca_AGNES",
)
FRASES_DA_FRASE = ("▁I G N IS ▁A RI SE @IGNIS_ARISE", *ISCAS_DA_FRASE)
FRASES_DO_NOME = (
    "▁I G N IS @IGNIS",
    "▁I G RI S @isca_IGRIS",
    "▁I RI S @isca_IRIS",
    "▁A G NE S @isca_AGNES",
)


class Detector(Protocol):
    def processar(self, bloco: Bloco) -> bool:
        """True se a frase deste detector terminou neste bloco."""
        ...


class DetectorSherpa:
    """Um detector do sherpa-onnx com uma frase principal e as suas iscas."""

    def __init__(
        self,
        pasta_do_modelo: Path,
        frases: tuple[str, ...],
        limiar: float = 0.1,
        peso: float = 2.0,
    ) -> None:
        import sherpa_onnx

        self._principal = frases[0].rsplit("@", 1)[1]
        rotulo = self._principal.lower()
        arquivo_de_frases = pasta_do_modelo / f"frases_{rotulo}.txt"
        arquivo_de_frases.write_text("\n".join(frases) + "\n", encoding="utf-8")
        sufixo = "epoch-12-avg-2-chunk-16-left-64.onnx"
        self._spotter = sherpa_onnx.KeywordSpotter(
            tokens=str(pasta_do_modelo / "tokens.txt"),
            encoder=str(pasta_do_modelo / f"encoder-{sufixo}"),
            decoder=str(pasta_do_modelo / f"decoder-{sufixo}"),
            joiner=str(pasta_do_modelo / f"joiner-{sufixo}"),
            keywords_file=str(arquivo_de_frases),
            keywords_score=peso,
            keywords_threshold=limiar,
            num_threads=1,
            provider="cpu",
        )
        self._fluxo = self._spotter.create_stream()

    def processar(self, bloco: Bloco) -> bool:
        self._fluxo.accept_waveform(TAXA, bloco)
        ouviu = False
        while self._spotter.is_ready(self._fluxo):
            self._spotter.decode_stream(self._fluxo)
            resultado = self._spotter.get_result(self._fluxo)
            if resultado:
                self._spotter.reset_stream(self._fluxo)
                ouviu = ouviu or resultado == self._principal
        return ouviu


class Ativador:
    """Junta os dois detectores e aplica a regra da D48.

    - Bloqueado ou em repouso: só a frase ativa.
    - Em uso: a frase ou o nome ativam.

    Os dois detectores recebem todos os blocos, para estarem sempre em dia.
    Depois de uma ativação, outras são ignoradas por um tempo: ao dizer
    "Ignis Arise", o detector do nome dispara no "Ignis" e o da frase logo
    depois, e isso não pode virar duas ativações.
    """

    def __init__(
        self,
        frase: Detector,
        nome: Detector,
        estado: EstadoDoPC,
        repouso_apos: float = 300.0,
        pausa_apos_ativar: float = 2.0,
    ) -> None:
        self._frase = frase
        self._nome = nome
        self._estado = estado
        self._repouso_apos = repouso_apos
        self._blocos_de_pausa = round(pausa_apos_ativar * TAXA / AMOSTRAS_POR_BLOCO)
        self._pausa_restante = 0

    def em_uso(self) -> bool:
        if self._estado.bloqueado():
            return False
        return self._estado.segundos_sem_uso() < self._repouso_apos

    def processar(self, bloco: Bloco) -> Gatilho | None:
        ouviu_frase = self._frase.processar(bloco)
        ouviu_nome = self._nome.processar(bloco)

        if self._pausa_restante > 0:
            self._pausa_restante -= 1
            return None

        gatilho = None
        if ouviu_frase:
            gatilho = Gatilho.FRASE
        elif ouviu_nome and self.em_uso():
            gatilho = Gatilho.NOME

        if gatilho is not None:
            self._pausa_restante = self._blocos_de_pausa
        return gatilho


def criar_ativador(pasta_do_modelo: Path, estado: EstadoDoPC) -> Ativador:
    """Monta o ativador com os detectores reais do sherpa-onnx."""
    return Ativador(
        frase=DetectorSherpa(pasta_do_modelo, FRASES_DA_FRASE),
        nome=DetectorSherpa(pasta_do_modelo, FRASES_DO_NOME),
        estado=estado,
    )
