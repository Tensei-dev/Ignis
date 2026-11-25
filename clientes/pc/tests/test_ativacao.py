import numpy as np
import pytest

from ignis_pc.ativacao import Ativador, Gatilho

BLOCO = np.zeros(1600, dtype=np.float32)


class DetectorRoteirizado:
    """Responde True nos blocos indicados e conta quantos blocos recebeu."""

    def __init__(self, ouve_nos_blocos: set[int]) -> None:
        self._ouve = ouve_nos_blocos
        self.recebidos = 0

    def processar(self, bloco) -> bool:
        ouviu = self.recebidos in self._ouve
        self.recebidos += 1
        return ouviu


class EstadoFalso:
    def __init__(self, bloqueado: bool = False, sem_uso: float = 0.0) -> None:
        self._bloqueado = bloqueado
        self._sem_uso = sem_uso

    def bloqueado(self) -> bool:
        return self._bloqueado

    def segundos_sem_uso(self) -> float:
        return self._sem_uso


def rodar(ativador: Ativador, blocos: int) -> list[tuple[int, Gatilho]]:
    gatilhos = []
    for indice in range(blocos):
        if (gatilho := ativador.processar(BLOCO)) is not None:
            gatilhos.append((indice, gatilho))
    return gatilhos


def montar(frase: set[int], nome: set[int], estado: EstadoFalso) -> Ativador:
    return Ativador(DetectorRoteirizado(frase), DetectorRoteirizado(nome), estado)


@pytest.mark.parametrize(
    "estado",
    [
        EstadoFalso(bloqueado=False, sem_uso=0),
        EstadoFalso(bloqueado=True, sem_uso=0),
        EstadoFalso(bloqueado=False, sem_uso=600),
    ],
    ids=["em uso", "bloqueado", "em repouso"],
)
def test_frase_ativa_em_qualquer_estado(estado):
    assert rodar(montar({3}, set(), estado), 10) == [(3, Gatilho.FRASE)]


def test_nome_ativa_com_o_pc_em_uso():
    estado = EstadoFalso(bloqueado=False, sem_uso=10)
    assert rodar(montar(set(), {3}, estado), 10) == [(3, Gatilho.NOME)]


def test_nome_nao_ativa_com_o_pc_bloqueado():
    estado = EstadoFalso(bloqueado=True)
    assert rodar(montar(set(), {3}, estado), 10) == []


def test_nome_nao_ativa_depois_de_5_minutos_sem_uso():
    assert rodar(montar(set(), {3}, EstadoFalso(sem_uso=299)), 10) != []
    assert rodar(montar(set(), {3}, EstadoFalso(sem_uso=300)), 10) == []


def test_frase_seguida_do_nome_nao_ativa_duas_vezes():
    ativador = montar({3}, {5}, EstadoFalso())
    assert rodar(ativador, 30) == [(3, Gatilho.FRASE)]


def test_volta_a_ativar_depois_da_pausa():
    # Pausa de 2 s = 20 blocos depois da ativação no bloco 3.
    ativador = montar(set(), {3, 23, 24}, EstadoFalso())
    assert rodar(ativador, 30) == [(3, Gatilho.NOME), (24, Gatilho.NOME)]


def test_os_dois_detectores_recebem_todos_os_blocos():
    frase, nome = DetectorRoteirizado({2}), DetectorRoteirizado(set())
    rodar(Ativador(frase, nome, EstadoFalso()), 10)
    assert frase.recebidos == nome.recebidos == 10


def test_ignis_arise_com_o_pc_em_uso_promove_o_chamado_para_frase():
    # O nome dispara no "Ignis" e a frase, 5 blocos depois, no "Arise".
    ativador = montar({8}, {3}, EstadoFalso())
    assert rodar(ativador, 30) == [(3, Gatilho.NOME), (8, Gatilho.FRASE)]


def test_so_promove_uma_vez():
    ativador = montar({8, 12}, {3}, EstadoFalso())
    assert rodar(ativador, 30) == [(3, Gatilho.NOME), (8, Gatilho.FRASE)]
