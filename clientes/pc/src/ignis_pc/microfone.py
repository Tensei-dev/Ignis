"""Único módulo que conhece o sounddevice."""

import logging
import queue

import numpy as np

from ignis_pc.audio import AMOSTRAS_POR_BLOCO, TAXA, Bloco

log = logging.getLogger(__name__)


def escolher_dispositivo(nome: str | None) -> int | None:
    """Acha o primeiro microfone cujo nome contém `nome` e aceita 16 kHz.

    Sem nome, ou se nenhum servir, devolve None: o padrão do Windows.
    """
    if not nome:
        return None
    import sounddevice as sd

    for indice, dispositivo in enumerate(sd.query_devices()):
        if dispositivo["max_input_channels"] < 1:
            continue
        if nome.lower() not in dispositivo["name"].lower():
            continue
        try:
            sd.check_input_settings(
                device=indice, channels=1, samplerate=TAXA, dtype="float32"
            )
        except Exception:  # noqa: BLE001 - o dispositivo recusou o formato
            continue
        return indice
    log.warning("Microfone %r não encontrado; usando o padrão.", nome)
    return None


class Microfone:
    """Captura blocos de 100 ms numa thread do sounddevice."""

    def __init__(self, nome: str | None = None, fila_maxima: int = 50) -> None:
        self._dispositivo = escolher_dispositivo(nome)
        self._fila: queue.Queue[Bloco] = queue.Queue(maxsize=fila_maxima)
        self.perdidos = 0
        self._stream = None

    def _ao_receber(self, dados: np.ndarray, _quadros, _tempo, status) -> None:
        # Roda na thread de áudio: só copia e enfileira, nada pesado aqui.
        if status:
            log.warning("Áudio: %s", status)
        try:
            self._fila.put_nowait(dados[:, 0].copy())
        except queue.Full:
            self.perdidos += 1

    def __enter__(self) -> "Microfone":
        import sounddevice as sd

        self._stream = sd.InputStream(
            device=self._dispositivo,
            samplerate=TAXA,
            channels=1,
            dtype="float32",
            blocksize=AMOSTRAS_POR_BLOCO,
            callback=self._ao_receber,
        )
        self._stream.start()
        return self

    def __exit__(self, *erro: object) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def ler(self, espera: float | None = None) -> Bloco | None:
        try:
            return self._fila.get(timeout=espera)
        except queue.Empty:
            return None
