import subprocess
import sys

import numpy as np

from ignis_pc.audio import TAXA
from ignis_pc.memoria import UltimosSegundos


def test_guarda_so_os_ultimos_2_segundos(fonte_falsa):
    audio = np.arange(5 * TAXA, dtype=np.float32)
    memoria = UltimosSegundos(2.0)
    with fonte_falsa(audio) as fonte:
        while (bloco := fonte.ler()) is not None:
            memoria.guardar(bloco)
    np.testing.assert_array_equal(memoria.copia(), audio[-2 * TAXA :])


def test_vazia_devolve_array_vazio():
    assert UltimosSegundos().copia().size == 0


def test_so_o_modulo_microfone_importa_o_sounddevice():
    # Num processo novo, para não depender da ordem dos outros testes.
    codigo = "import sys, ignis_pc.memoria; print('sounddevice' in sys.modules)"
    saida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    )
    assert saida.stdout.strip() == "False"


def test_modulos_sem_hardware_nao_importam_bibliotecas_pesadas():
    codigo = (
        "import sys, ignis_pc, ignis_pc.ativacao, ignis_pc.fim_da_fala,"
        " ignis_pc.escuta, ignis_pc.modelos, ignis_pc.memoria, ignis_pc.terminal;"
        "print(sorted({'sounddevice', 'sherpa_onnx'} & set(sys.modules)))"
    )
    saida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    )
    assert saida.stdout.strip() == "[]"
