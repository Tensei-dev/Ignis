import numpy as np
import pytest

from ignis_pc.audio import AMOSTRAS_POR_BLOCO, Bloco


class FonteFalsa:
    """Entrega um áudio pronto em blocos de 100 ms, como o microfone faria."""

    def __init__(self, audio: np.ndarray) -> None:
        self._blocos = [
            audio[i : i + AMOSTRAS_POR_BLOCO].astype(np.float32)
            for i in range(0, len(audio), AMOSTRAS_POR_BLOCO)
        ]

    def __enter__(self) -> "FonteFalsa":
        return self

    def __exit__(self, *erro: object) -> None:
        pass

    def ler(self, espera: float | None = None) -> Bloco | None:
        return self._blocos.pop(0) if self._blocos else None


@pytest.fixture
def fonte_falsa():
    """Use assim no teste: `with fonte_falsa(audio) as fonte:`."""
    return FonteFalsa
