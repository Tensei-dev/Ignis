import ctypes
import sys

import pytest

so_no_windows = pytest.mark.skipif(sys.platform != "win32", reason="só no Windows")


@so_no_windows
def test_estrutura_tem_o_tamanho_que_o_windows_devolve():
    from ignis_pc.sessao import _InfoEx

    # 232 bytes, medidos no Windows 11 com WTSQuerySessionInformationW.
    assert ctypes.sizeof(_InfoEx) == 232


@so_no_windows
def test_le_o_estado_da_sessao():
    from ignis_pc.sessao import SessaoWindows

    sessao = SessaoWindows()
    assert isinstance(sessao.bloqueado(), bool)
    assert sessao.segundos_sem_uso() >= 0


def test_fora_do_windows_avisa_em_vez_de_falhar_em_silencio(monkeypatch):
    from ignis_pc import sessao

    monkeypatch.setattr(sessao.sys, "platform", "linux")
    with pytest.raises(OSError, match="só funciona no Windows"):
        sessao.SessaoWindows()
