"""O comando `ignis-pc escutar`: abre o microfone e mostra os eventos.

Por enquanto, nada é enviado ao cérebro (isso vem na T09).
"""

import logging
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np

from ignis_pc.audio import TAXA, Bloco, FonteDeAudio
from ignis_pc.escuta import Chamado, Escuta, Evento, Pedido, SemPedido
from ignis_pc.modelos import (
    DETECTOR_DE_FRASES,
    DETECTOR_DE_VOZ,
    TODOS,
    caminho,
    esta_baixado,
    pasta_do_ignis,
)

log = logging.getLogger(__name__)


def escutar_no_terminal(microfone: str | None, depurar: bool) -> int:
    faltando = [m.nome for m in TODOS if not esta_baixado(m)]
    if faltando:
        log.error(
            "Modelos não baixados: %s. Rode `uv run ignis-pc baixar-modelos`.", faltando
        )
        return 1

    from ignis_pc.ativacao import criar_ativador
    from ignis_pc.fim_da_fala import FimDaFala, VadSilero
    from ignis_pc.microfone import Microfone
    from ignis_pc.sessao import SessaoWindows

    sessao = SessaoWindows()
    escuta = Escuta(
        ativacao=criar_ativador(caminho(DETECTOR_DE_FRASES), sessao),
        fim=FimDaFala(VadSilero(caminho(DETECTOR_DE_VOZ))),
    )
    pasta = pasta_do_ignis() / "depuracao" if depurar else None
    if pasta:
        pasta.mkdir(parents=True, exist_ok=True)
        log.info("Modo de depuração: os pedidos serão salvos em %s", pasta)

    fonte = Microfone(microfone)
    estado = "em uso" if not sessao.bloqueado() else "bloqueado"
    print(f"PC {estado}, {sessao.segundos_sem_uso():.0f} s sem mouse e teclado.")
    print('Diga "Ignis Arise", ou só "Ignis" com o PC em uso. Ctrl+C para sair.\n')
    try:
        rodar(fonte, escuta, lambda evento: mostrar(evento, pasta))
    except KeyboardInterrupt:
        print("\nEncerrado.")
    if fonte.perdidos:
        print(
            f"Atenção: {fonte.perdidos} blocos de áudio foram descartados por atraso."
        )
    return 0


def rodar(fonte: FonteDeAudio, escuta: Escuta, ao_evento) -> None:
    """Lê o áudio até a fonte acabar (nos testes) ou o usuário interromper."""
    with fonte:
        while True:
            bloco = fonte.ler(espera=1.0)
            if bloco is None:
                if getattr(fonte, "terminou", False):
                    return
                continue
            if (evento := escuta.processar(bloco)) is not None:
                ao_evento(evento)


def mostrar(evento: Evento, pasta: Path | None) -> None:
    hora = time.strftime("%H:%M:%S")
    match evento:
        case Chamado(gatilho):
            print(f"{hora}  chamado ({gatilho.value}), ouvindo o pedido...")
        case Pedido() as pedido:
            origem = pedido.gatilho.value if pedido.gatilho else "conversa, sem o nome"
            detalhes = f"{pedido.segundos:.1f} s de áudio, {origem}"
            if pedido.atraso is not None:
                detalhes += f", percebeu o fim {pedido.atraso:.1f} s depois"
            if pedido.limite:
                detalhes += ", cortado no limite de 30 s"
            print(f"{hora}  PEDIDO: {detalhes}")
            if pasta:
                arquivo = salvar_wav(pedido.audio, pasta, origem_do_pedido(pedido))
                print(f"          salvo em {arquivo}")
            print(f"{hora}  conversa aberta: fale de novo sem dizer o nome")
        case SemPedido(gatilho):
            if gatilho is None:
                print(f"{hora}  conversa encerrada, esperando ser chamado\n")
            else:
                print(f"{hora}  chamado sem pedido\n")


def origem_do_pedido(pedido: Pedido) -> str:
    """ "frase", "nome" ou "conversa": vai no nome do WAV, para o cérebro saber."""
    return pedido.gatilho.value if pedido.gatilho else "conversa"


def salvar_wav(audio: Bloco, pasta: Path, origem: str) -> Path:
    arquivo = pasta / f"pedido_{datetime.now():%Y%m%d_%H%M%S_%f}_{origem}.wav"
    amostras = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(arquivo), "wb") as saida:
        saida.setnchannels(1)
        saida.setsampwidth(2)
        saida.setframerate(TAXA)
        saida.writeframes(amostras.tobytes())
    return arquivo
