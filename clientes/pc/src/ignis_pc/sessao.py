"""Único módulo que pergunta ao Windows pelo estado da sessão."""

import ctypes
import logging
import sys
from typing import Protocol

log = logging.getLogger(__name__)


class EstadoDoPC(Protocol):
    def bloqueado(self) -> bool:
        """True se a tela estiver bloqueada."""
        ...

    def segundos_sem_uso(self) -> float:
        """Há quanto tempo o mouse e o teclado não são usados."""
        ...


_WTS_SESSION_INFO_EX = 25
_WTS_SESSIONSTATE_UNLOCK = 1

if sys.platform == "win32":
    # ctypes.wintypes pode falhar ao importar fora do Windows, por isso fica aqui.
    from ctypes import wintypes

    class _InfoNivel1(ctypes.Structure):
        """WTSINFOEX_LEVEL1_W, da API de sessões do Windows."""

        _fields_ = [
            ("SessionId", wintypes.ULONG),
            ("SessionState", ctypes.c_int),
            ("SessionFlags", wintypes.LONG),
            ("WinStationName", wintypes.WCHAR * 33),
            ("UserName", wintypes.WCHAR * 21),
            ("DomainName", wintypes.WCHAR * 18),
            ("LogonTime", wintypes.LARGE_INTEGER),
            ("ConnectTime", wintypes.LARGE_INTEGER),
            ("DisconnectTime", wintypes.LARGE_INTEGER),
            ("LastInputTime", wintypes.LARGE_INTEGER),
            ("CurrentTime", wintypes.LARGE_INTEGER),
            ("IncomingBytes", wintypes.DWORD),
            ("OutgoingBytes", wintypes.DWORD),
            ("IncomingFrames", wintypes.DWORD),
            ("OutgoingFrames", wintypes.DWORD),
            ("IncomingCompressedBytes", wintypes.DWORD),
            ("OutgoingCompressedBytes", wintypes.DWORD),
        ]

    class _InfoEx(ctypes.Structure):
        """WTSINFOEXW. Os campos de 64 bits criam um espaço depois de Level."""

        _fields_ = [("Level", wintypes.DWORD), ("Data", _InfoNivel1)]

    class _UltimaEntrada(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


class SessaoWindows:
    """Lê o bloqueio e o tempo sem uso da sessão do usuário."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("SessaoWindows só funciona no Windows.")
        self._kernel32 = ctypes.WinDLL("kernel32")
        self._user32 = ctypes.WinDLL("user32")
        self._wtsapi32 = ctypes.WinDLL("wtsapi32")
        self._kernel32.GetTickCount.restype = wintypes.DWORD
        self._sessao = wintypes.DWORD()
        self._kernel32.ProcessIdToSessionId(
            self._kernel32.GetCurrentProcessId(), ctypes.byref(self._sessao)
        )

    def bloqueado(self) -> bool:
        """Na dúvida, responde que está bloqueado: é o lado seguro do erro."""
        dados = ctypes.c_void_p()
        tamanho = wintypes.DWORD()
        ok = self._wtsapi32.WTSQuerySessionInformationW(
            None,
            self._sessao.value,
            _WTS_SESSION_INFO_EX,
            ctypes.byref(dados),
            ctypes.byref(tamanho),
        )
        if not ok:
            log.warning("Não deu para ler o estado da sessão; tratando como bloqueada.")
            return True
        try:
            if tamanho.value < ctypes.sizeof(_InfoEx):
                return True
            info = ctypes.cast(dados, ctypes.POINTER(_InfoEx)).contents
            return info.Data.SessionFlags != _WTS_SESSIONSTATE_UNLOCK
        finally:
            self._wtsapi32.WTSFreeMemory(dados)

    def segundos_sem_uso(self) -> float:
        """Só mouse e teclado contam: um controle de jogo não conta como uso."""
        ultima = _UltimaEntrada(ctypes.sizeof(_UltimaEntrada), 0)
        if not self._user32.GetLastInputInfo(ctypes.byref(ultima)):
            return 0.0
        # O contador do Windows dá a volta a cada 49,7 dias; a máscara corrige.
        decorrido = (self._kernel32.GetTickCount() - ultima.dwTime) & 0xFFFFFFFF
        return decorrido / 1000
