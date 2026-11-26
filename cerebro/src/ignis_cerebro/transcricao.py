"""Transforma o áudio do pedido em texto com o faster-whisper, na GPU."""

import glob
import logging
import os
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from ignis_cerebro.gpu import MonitorDeGpu

log = logging.getLogger(__name__)

TAXA = 16_000


class GpuOcupada(Exception):
    """A GPU está ocupada por outro programa, e o Ignis não vai disputar com ele."""


@dataclass(frozen=True)
class Transcricao:
    texto: str
    segundos: float
    """Quanto tempo a transcrição levou."""
    duracao_do_audio: float


class Transcritor(Protocol):
    def transcrever(self, audio: np.ndarray) -> Transcricao: ...


def _registrar_bibliotecas_da_nvidia() -> None:
    """No Windows, as DLLs da NVIDIA instaladas pelo pip precisam ser apontadas."""
    if sys.platform != "win32":
        return
    try:
        import nvidia
    except ImportError:
        return
    for pasta in glob.glob(os.path.join(list(nvidia.__path__)[0], "*", "bin")):
        os.add_dll_directory(pasta)


class TranscritorWhisper:
    """O Whisper large-v3-turbo na GPU, compactado (int8_float16).

    A dica "Ignis" faz o Whisper escrever o nome certo, o que a conferência do
    chamado precisa. O modelo é aquecido ao carregar, porque a primeira
    transcrição é bem mais lenta que as outras.
    """

    def __init__(
        self,
        pasta_do_modelo: Path,
        monitor: MonitorDeGpu | None = None,
        dispositivo: str = "cuda",
        tipo: str = "int8_float16",
    ) -> None:
        _registrar_bibliotecas_da_nvidia()
        from faster_whisper import WhisperModel

        inicio = time.perf_counter()
        self._modelo = WhisperModel(
            str(pasta_do_modelo), device=dispositivo, compute_type=tipo
        )
        self._monitor = monitor
        self._transcrever(np.zeros(TAXA, dtype=np.float32))
        log.info("Whisper pronto em %.1f s", time.perf_counter() - inicio)

    def transcrever(self, audio: np.ndarray) -> Transcricao:
        if self._monitor is not None and self._monitor.ocupada():
            raise GpuOcupada(
                "A GPU está ocupada por outro programa. "
                "O Ignis não vai transcrever agora."
            )
        inicio = time.perf_counter()
        if self._monitor is None:
            texto = self._transcrever(audio)
        else:
            with self._monitor.trabalhando():
                texto = self._transcrever(audio)
        return Transcricao(
            texto=texto,
            segundos=time.perf_counter() - inicio,
            duracao_do_audio=len(audio) / TAXA,
        )

    def _transcrever(self, audio: np.ndarray) -> str:
        trechos, _ = self._modelo.transcribe(
            audio,
            language="pt",
            beam_size=1,
            hotwords="Ignis",
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=False,
        )
        return " ".join(trecho.text.strip() for trecho in trechos).strip()


def ler_wav(arquivo: Path) -> np.ndarray:
    """Lê um WAV de 16 kHz, mono e 16 bits, o formato que o cliente salva.

    O arquivo é lido aqui, e não pelo faster-whisper: a leitura dele quebrou
    com a versão nova da biblioteca de áudio (PyAV) num teste.
    """
    with wave.open(str(arquivo)) as wav:
        formato = (wav.getframerate(), wav.getnchannels(), wav.getsampwidth())
        if formato != (TAXA, 1, 2):
            raise ValueError(
                f"{arquivo.name}: esperado 16 kHz, mono e 16 bits; veio "
                f"{formato[0]} Hz, {formato[1]} canal(is) e {8 * formato[2]} bits."
            )
        dados = wav.readframes(wav.getnframes())
    return np.frombuffer(dados, dtype=np.int16).astype(np.float32) / 32768
