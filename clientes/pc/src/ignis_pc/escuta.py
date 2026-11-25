"""Liga as peças da escuta: memória de 2 s, ativação e fim do pedido.

É uma máquina de estados: o Ignis está sempre em um estado, e cada bloco de
áudio pode fazê-lo mudar. O que sai dela são eventos.

    ESPERANDO --chamado--> OUVINDO --você parou--> CONVERSA --nada em 5 s--> ESPERANDO
                              ^                       |
                              +----fala sem o nome----+

    MUDO: ignora todo o áudio até ser desligado.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

import numpy as np

from ignis_pc.ativacao import Gatilho
from ignis_pc.audio import TAXA, Bloco
from ignis_pc.fim_da_fala import Resultado
from ignis_pc.memoria import UltimosSegundos


class Estado(Enum):
    ESPERANDO = "esperando"
    OUVINDO = "ouvindo o pedido"
    CONVERSA = "conversa"
    MUDO = "mudo"


@dataclass(frozen=True)
class Chamado:
    """O Ignis foi chamado. Serve para avisar quem estiver olhando."""

    gatilho: Gatilho


@dataclass(frozen=True)
class Pedido:
    audio: Bloco
    """Os 2 s antes do chamado, com a frase, mais o pedido."""
    gatilho: Gatilho | None
    """None quando o pedido veio na conversa, sem o nome."""
    limite: bool
    """True se o pedido foi cortado no tempo máximo."""
    atraso: float | None
    """Segundos entre o fim da sua fala e o Ignis perceber (D58)."""

    @property
    def segundos(self) -> float:
        return len(self.audio) / TAXA


@dataclass(frozen=True)
class SemPedido:
    """O Ignis foi chamado, ou a conversa abriu, e ninguém pediu nada."""

    gatilho: Gatilho | None


Evento = Chamado | Pedido | SemPedido


class Ativacao(Protocol):
    def processar(self, bloco: Bloco) -> Gatilho | None: ...


class Acompanhamento(Protocol):
    atraso: float | None

    def comecar(self, espera_pelo_pedido: float | None = None) -> None: ...

    def processar(self, bloco: Bloco) -> Resultado | None: ...


class Escuta:
    def __init__(
        self,
        ativacao: Ativacao,
        fim: Acompanhamento,
        memoria: UltimosSegundos | None = None,
        conversa: float = 5.0,
    ) -> None:
        self._ativacao = ativacao
        self._fim = fim
        self._memoria = memoria or UltimosSegundos(2.0)
        self._conversa = conversa
        self._estado = Estado.ESPERANDO
        self._gatilho: Gatilho | None = None
        self._audio: list[Bloco] = []

    @property
    def estado(self) -> Estado:
        return self._estado

    def definir_mudo(self, mudo: bool) -> None:
        if mudo:
            self._estado = Estado.MUDO
            self._audio = []
        elif self._estado is Estado.MUDO:
            self._estado = Estado.ESPERANDO
        self._memoria.esvaziar()

    def processar(self, bloco: Bloco) -> Evento | None:
        if self._estado is Estado.MUDO:
            return None

        self._memoria.guardar(bloco)
        # Os detectores de frase ouvem sempre, para não perderem o compasso,
        # mas um chamado só vale quando o Ignis está esperando.
        gatilho = self._ativacao.processar(bloco)

        if self._estado is Estado.ESPERANDO:
            if gatilho is None:
                return None
            self._estado = Estado.OUVINDO
            self._gatilho = gatilho
            self._audio = [self._memoria.copia()]
            self._fim.comecar()
            return Chamado(gatilho)

        self._audio.append(bloco)
        if (
            self._estado is Estado.OUVINDO
            and self._gatilho is Gatilho.NOME
            and gatilho is Gatilho.FRASE
        ):
            # Era "Ignis Arise": o "Arise" fazia parte do chamado, e não do
            # pedido. O acompanhamento recomeça a partir daqui.
            self._gatilho = Gatilho.FRASE
            self._fim.comecar()
            return None
        resultado = self._fim.processar(bloco)
        if resultado is None:
            return None
        return self._concluir(resultado)

    def _concluir(self, resultado: Resultado) -> Evento:
        gatilho = self._gatilho
        if resultado is Resultado.NADA:
            self._estado = Estado.ESPERANDO
            self._audio = []
            return SemPedido(gatilho)

        pedido = Pedido(
            audio=np.concatenate(self._audio),
            gatilho=gatilho,
            limite=resultado is Resultado.LIMITE,
            atraso=self._fim.atraso,
        )
        # Depois de um pedido, abre a conversa: o próximo dispensa o nome (D48).
        self._estado = Estado.CONVERSA
        self._gatilho = None
        self._audio = []
        self._fim.comecar(self._conversa)
        return pedido
