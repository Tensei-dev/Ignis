"""Testes com o Whisper de verdade, na GPU. Rodam só onde houver modelo e GPU.

Para rodar: `uv run ignis-cerebro baixar-modelos` e depois `uv run pytest`.
"""

import numpy as np
import pytest

from ignis_cerebro.modelos import WHISPER_TURBO, caminho, esta_baixado


def tem_gpu_nvidia() -> bool:
    from ignis_cerebro.gpu import leitor_nvml

    return leitor_nvml() is not None


pytestmark = pytest.mark.skipif(
    not esta_baixado(WHISPER_TURBO) or not tem_gpu_nvidia(),
    reason="precisa do Whisper baixado e de uma GPU NVIDIA",
)


def test_carrega_na_gpu_e_transcreve_silencio_rapido():
    from ignis_cerebro.transcricao import TranscritorWhisper

    transcritor = TranscritorWhisper(caminho(WHISPER_TURBO))
    resultado = transcritor.transcrever(np.zeros(16000 * 3, dtype=np.float32))
    assert resultado.duracao_do_audio == 3.0
    assert resultado.segundos < 2.0
