"""Guarda só os últimos segundos de áudio."""

from collections import deque

import numpy as np

from ignis_pc.audio import AMOSTRAS_POR_BLOCO, TAXA, Bloco


class UltimosSegundos:
    """Mantém os blocos mais recentes e descarta os antigos sozinho."""

    def __init__(self, segundos: float = 2.0) -> None:
        blocos = round(segundos * TAXA / AMOSTRAS_POR_BLOCO)
        self._blocos: deque[Bloco] = deque(maxlen=blocos)

    def guardar(self, bloco: Bloco) -> None:
        self._blocos.append(bloco)

    def copia(self) -> Bloco:
        """Devolve os blocos guardados, do mais antigo ao mais novo, num só array."""
        if not self._blocos:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._blocos)

    def esvaziar(self) -> None:
        self._blocos.clear()
