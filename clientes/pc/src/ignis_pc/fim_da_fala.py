"""Decide quando o pedido terminou, depois que o Ignis foi chamado."""

from enum import Enum
from pathlib import Path
from typing import Protocol

from ignis_pc.audio import TAXA, Bloco


class Resultado(Enum):
    FIM = "fim"
    """O pedido terminou: houve fala depois do chamado e, em seguida, silêncio."""
    NADA = "nada"
    """O Ignis foi chamado, mas ninguém pediu nada a tempo."""
    LIMITE = "limite"
    """O pedido passou do tempo máximo e foi encerrado."""


class DetectorDeVoz(Protocol):
    def reiniciar(self) -> None:
        """Esquece tudo o que ouviu até agora."""
        ...

    def processar(self, bloco: Bloco) -> list[float]:
        """Devolve a duração, em segundos, dos trechos de fala que terminaram."""
        ...

    def falando(self) -> bool:
        """True se há um trecho de fala em andamento."""
        ...


class VadSilero:
    """O Silero VAD do sherpa-onnx.

    Um trecho de fala só é entregue depois de `silencio` segundos calado: é esse
    tempo que impede de cortar o pedido numa pausa para respirar.
    """

    def __init__(
        self, pasta_do_modelo: Path, silencio: float = 0.8, limiar: float = 0.5
    ) -> None:
        import sherpa_onnx

        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(pasta_do_modelo / "silero_vad.onnx")
        config.silero_vad.threshold = limiar
        config.silero_vad.min_silence_duration = silencio
        config.silero_vad.min_speech_duration = 0.25
        config.silero_vad.max_speech_duration = 30
        config.sample_rate = TAXA
        self._vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=40)

    def reiniciar(self) -> None:
        self._vad.reset()

    def processar(self, bloco: Bloco) -> list[float]:
        self._vad.accept_waveform(bloco)
        duracoes = []
        while not self._vad.empty():
            duracoes.append(len(self._vad.front.samples) / TAXA)
            self._vad.pop()
        return duracoes

    def falando(self) -> bool:
        return self._vad.is_speech_detected()


class FimDaFala:
    """Acompanha um pedido, do chamado até o fim.

    O detector de voz é reiniciado no chamado. Assim, ele só conhece o que veio
    depois: se você disser "Ignis" e parar para pensar, a fala do nome não conta,
    e o pedido só termina depois que você falar de novo e se calar.

    Fora de um pedido, os blocos são ignorados e o detector não gasta CPU.
    """

    def __init__(
        self,
        detector: DetectorDeVoz,
        espera_pelo_pedido: float = 3.0,
        maximo: float = 30.0,
    ) -> None:
        self._detector = detector
        self._espera = round(espera_pelo_pedido * TAXA)
        self._maximo = round(maximo * TAXA)
        self._amostras = 0
        self._ativo = False

    @property
    def ativo(self) -> bool:
        return self._ativo

    def comecar(self) -> None:
        """Chamado no momento da ativação."""
        self._detector.reiniciar()
        self._amostras = 0
        self._ativo = True

    def processar(self, bloco: Bloco) -> Resultado | None:
        if not self._ativo:
            return None
        trechos = self._detector.processar(bloco)
        self._amostras += len(bloco)

        if trechos:
            return self._encerrar(Resultado.FIM)
        if self._amostras >= self._maximo:
            return self._encerrar(Resultado.LIMITE)
        if self._amostras >= self._espera and not self._detector.falando():
            return self._encerrar(Resultado.NADA)
        return None

    def _encerrar(self, resultado: Resultado) -> Resultado:
        self._ativo = False
        return resultado
