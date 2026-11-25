"""Formato do áudio e a interface de qualquer fonte de áudio."""

from typing import Protocol

import numpy as np

TAXA = 16_000
"""Amostras por segundo."""

AMOSTRAS_POR_BLOCO = 1_600
"""Cada bloco tem 100 ms."""

Bloco = np.ndarray
"""Um bloco de áudio: float32, mono, valores entre -1 e 1."""


class FonteDeAudio(Protocol):
    """Algo que entrega blocos de áudio: o microfone, ou um arquivo nos testes."""

    def __enter__(self) -> "FonteDeAudio": ...

    def __exit__(self, *erro: object) -> None: ...

    def ler(self, espera: float | None = None) -> Bloco | None:
        """Devolve o próximo bloco, ou None se nada chegar em `espera` segundos."""
        ...
