"""Acompanha o uso da placa de vídeo, para o Ignis não disputar com um jogo.

O Windows não informa o uso por programa, então o monitor mede o uso total e
descarta as leituras feitas enquanto o próprio Ignis está trabalhando.
"""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LeituraDeGpu:
    uso: float
    """Porcentagem de uso da GPU, de 0 a 100."""
    vram_livre_mib: float


def leitor_nvml() -> Callable[[], LeituraDeGpu] | None:
    """Devolve uma função que lê a GPU, ou None se não houver GPU NVIDIA."""
    try:
        import pynvml

        pynvml.nvmlInit()
        aparelho = pynvml.nvmlDeviceGetHandleByIndex(0)
    except Exception as erro:  # noqa: BLE001 - sem driver ou sem GPU NVIDIA
        log.warning("Não deu para ler a GPU: %s", erro)
        return None

    def ler() -> LeituraDeGpu:
        uso = pynvml.nvmlDeviceGetUtilizationRates(aparelho).gpu
        memoria = pynvml.nvmlDeviceGetMemoryInfo(aparelho)
        return LeituraDeGpu(uso=float(uso), vram_livre_mib=memoria.free / 2**20)

    return ler


class MonitorDeGpu:
    """Decide se a GPU está ocupada por outro programa, como um jogo.

    Ocupada quando o uso médio dos últimos `janela` segundos passa de `limite`
    por cento, ou quando sobra menos de `vram_minima_mib` de memória de vídeo.
    """

    def __init__(
        self,
        ler: Callable[[], LeituraDeGpu] | None,
        limite: float = 60.0,
        janela: float = 5.0,
        intervalo: float = 0.5,
        vram_minima_mib: float = 300.0,
    ) -> None:
        self._ler = ler
        self.limite = limite
        self.vram_minima_mib = vram_minima_mib
        self._intervalo = intervalo
        self._leituras: deque[LeituraDeGpu] = deque(
            maxlen=max(1, round(janela / intervalo))
        )
        self._trabalhando = 0
        self._trava = threading.Lock()
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def disponivel(self) -> bool:
        return self._ler is not None

    def iniciar(self) -> None:
        if self._ler is None or self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._acompanhar, name="monitor-gpu", daemon=True
        )
        self._thread.start()

    def parar(self) -> None:
        self._parar.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _acompanhar(self) -> None:
        while not self._parar.wait(self._intervalo):
            try:
                self.registrar(self._ler())
            except Exception as erro:  # noqa: BLE001 - a leitura não pode derrubar o Ignis
                log.warning("Leitura da GPU falhou: %s", erro)

    def registrar(self, leitura: LeituraDeGpu) -> None:
        """Guarda uma leitura, a menos que o próprio Ignis esteja usando a GPU."""
        with self._trava:
            if self._trabalhando == 0:
                self._leituras.append(leitura)

    @contextmanager
    def trabalhando(self) -> Iterator[None]:
        """Enquanto ativo, as leituras são descartadas: o uso é do próprio Ignis."""
        with self._trava:
            self._trabalhando += 1
        try:
            yield
        finally:
            with self._trava:
                self._trabalhando -= 1

    def uso_medio(self) -> float | None:
        with self._trava:
            if not self._leituras:
                return None
            return sum(leitura.uso for leitura in self._leituras) / len(self._leituras)

    def ocupada(self) -> bool:
        with self._trava:
            if not self._leituras:
                return False
            media = sum(leitura.uso for leitura in self._leituras) / len(self._leituras)
            vram = self._leituras[-1].vram_livre_mib
        return media > self.limite or vram < self.vram_minima_mib


def acompanhar_no_terminal(
    monitor: MonitorDeGpu, segundos: float | None = None
) -> None:
    """Mostra o uso a cada segundo: ajuda a escolher o limite com um jogo aberto."""
    inicio = time.monotonic()
    while segundos is None or time.monotonic() - inicio < segundos:
        time.sleep(1)
        media = monitor.uso_medio()
        estado = "OCUPADA" if monitor.ocupada() else "livre"
        texto = "sem leituras" if media is None else f"média {media:5.1f}%"
        hora = time.strftime("%H:%M:%S")
        print(f"{hora}  GPU {texto} (limite {monitor.limite:.0f}%): {estado}")
