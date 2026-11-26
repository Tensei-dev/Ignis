"""Confere, pelo texto, se o Ignis foi mesmo chamado (D47).

O detector do cliente às vezes confunde outras palavras com "Ignis". Depois da
transcrição, o cérebro procura o nome nas primeiras palavras. Se não achar, o
pedido é descartado e nada vai para a API.
"""

import re
import unicodedata

VARIANTES_DO_NOME = frozenset({"ignis", "igness", "ignes", "ignace"})
"""Como o Whisper escreveu "Ignis" nos testes. Com a dica, sempre "Ignis"."""

VARIANTES_DE_ARISE = frozenset({"arise", "araise", "araize"})

_PALAVRA = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?")
_PONTUACAO_INICIAL = " \t,.;:!?-–—\"'"


def _normalizar(palavra: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", palavra)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).lower()


def conferir_chamado(texto: str, primeiras_palavras: int = 4) -> str | None:
    """Devolve o pedido sem o chamado, ou None se o nome não estiver no começo.

    O que vem antes do nome é descartado: os 2 s guardados antes do chamado
    podem trazer o fim de outra frase. Um texto vazio quer dizer chamado sem
    pedido.
    """
    palavras = list(_PALAVRA.finditer(texto))
    for indice, palavra in enumerate(palavras[:primeiras_palavras]):
        if _normalizar(palavra.group()) not in VARIANTES_DO_NOME:
            continue
        fim = palavra.end()
        seguinte = palavras[indice + 1] if indice + 1 < len(palavras) else None
        if seguinte and _normalizar(seguinte.group()) in VARIANTES_DE_ARISE:
            fim = seguinte.end()
        return texto[fim:].lstrip(_PONTUACAO_INICIAL).strip()
    return None
