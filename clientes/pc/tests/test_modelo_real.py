"""Testes com os modelos de verdade. Rodam só onde eles já foram baixados.

Para rodar: `uv run ignis-pc baixar-modelos` e depois `uv run pytest`.
"""

import shutil

import numpy as np
import pytest

from ignis_pc.modelos import DETECTOR_DE_FRASES, DETECTOR_DE_VOZ, caminho, esta_baixado


def precisa_de(modelo):
    return pytest.mark.skipif(
        not esta_baixado(modelo),
        reason="modelo não baixado: rode `uv run ignis-pc baixar-modelos`",
    )


def silencio_e_ruido(nivel: float = 0.05) -> np.ndarray:
    ruido = np.random.default_rng(0).normal(0, nivel, 16000 * 5).astype(np.float32)
    return np.concatenate([np.zeros(16000 * 5, dtype=np.float32), ruido])


def blocos(audio: np.ndarray):
    for inicio in range(0, len(audio), 1600):
        yield audio[inicio : inicio + 1600]


@precisa_de(DETECTOR_DE_FRASES)
@pytest.mark.parametrize("frases", ["FRASES_DA_FRASE", "FRASES_DO_NOME"])
def test_detector_de_frases_nao_dispara_com_silencio_nem_ruido(frases, tmp_path):
    from ignis_pc import ativacao

    # Usa uma cópia, para não gravar o arquivo de frases na pasta real.
    pasta = tmp_path / "modelo"
    shutil.copytree(caminho(DETECTOR_DE_FRASES), pasta)
    detector = ativacao.DetectorSherpa(pasta, getattr(ativacao, frases))

    assert not any(detector.processar(bloco) for bloco in blocos(silencio_e_ruido()))


@precisa_de(DETECTOR_DE_VOZ)
def test_detector_de_voz_nao_ve_fala_no_silencio():
    from ignis_pc.fim_da_fala import VadSilero

    vad = VadSilero(caminho(DETECTOR_DE_VOZ))
    silencio = np.zeros(16000 * 10, dtype=np.float32)
    assert [d for bloco in blocos(silencio) for d in vad.processar(bloco)] == []
    assert not vad.falando()


@precisa_de(DETECTOR_DE_VOZ)
@pytest.mark.parametrize("nivel", [0.01, 0.05])
def test_ruido_continuo_gera_no_maximo_um_trecho_no_comeco(nivel):
    # O começo brusco de um ruído pode parecer fala (D57), mas um ruído que
    # continua não deve gerar trechos novos.
    from ignis_pc.fim_da_fala import VadSilero

    vad = VadSilero(caminho(DETECTOR_DE_VOZ))
    gerador = np.random.default_rng(0)
    ruido = gerador.normal(0, nivel, 16000 * 30).astype(np.float32)
    audio = np.concatenate([np.zeros(16000 * 2, dtype=np.float32), ruido])
    assert len([d for bloco in blocos(audio) for d in vad.processar(bloco)]) <= 1


@precisa_de(DETECTOR_DE_VOZ)
def test_chamado_sem_pedido_com_o_detector_real():
    from ignis_pc.fim_da_fala import FimDaFala, Resultado, VadSilero

    fim = FimDaFala(VadSilero(caminho(DETECTOR_DE_VOZ)))
    fim.comecar()
    resultados = [fim.processar(bloco) for bloco in blocos(silencio_e_ruido())]
    assert Resultado.NADA in resultados
