import numpy as np

from ignis_pc.ativacao import Gatilho
from ignis_pc.audio import AMOSTRAS_POR_BLOCO
from ignis_pc.escuta import Chamado, Escuta, Estado, Pedido, SemPedido
from ignis_pc.fim_da_fala import Resultado


class AtivacaoRoteirizada:
    """Chama o Ignis nos blocos indicados (contados desde o começo)."""

    def __init__(self, chamados: dict[int, Gatilho] | None = None) -> None:
        self._chamados = chamados or {}
        self.blocos = 0

    def processar(self, bloco):
        gatilho = self._chamados.get(self.blocos)
        self.blocos += 1
        return gatilho


class FimRoteirizado:
    """Encerra cada acompanhamento depois de N blocos, com o resultado dado.

    `roteiro`: um (blocos, resultado) para cada acompanhamento, em ordem.
    """

    def __init__(self, roteiro: list[tuple[int, Resultado]]) -> None:
        self._roteiro = list(roteiro)
        self._restante: tuple[int, Resultado] | None = None
        self.esperas: list[float | None] = []
        self.atraso = None

    def comecar(self, espera_pelo_pedido=None) -> None:
        self.esperas.append(espera_pelo_pedido)
        self._restante = self._roteiro.pop(0) if self._roteiro else (10**9, None)

    def processar(self, bloco):
        blocos, resultado = self._restante
        blocos -= 1
        self._restante = (blocos, resultado)
        if blocos == 0:
            self.atraso = 0.9 if resultado is Resultado.FIM else None
            return resultado
        return None


def bloco(valor: float) -> np.ndarray:
    return np.full(AMOSTRAS_POR_BLOCO, valor, dtype=np.float32)


def rodar(escuta: Escuta, blocos: int) -> list[tuple[int, object]]:
    eventos = []
    for indice in range(blocos):
        if (evento := escuta.processar(bloco(indice))) is not None:
            eventos.append((indice, evento))
    return eventos


def test_chamado_e_pedido_com_os_2_segundos_anteriores():
    escuta = Escuta(
        AtivacaoRoteirizada({30: Gatilho.NOME}),
        FimRoteirizado([(15, Resultado.FIM)]),
    )
    eventos = rodar(escuta, 50)

    assert eventos[0] == (30, Chamado(Gatilho.NOME))
    indice, pedido = eventos[1]
    assert indice == 45
    assert isinstance(pedido, Pedido)
    assert pedido.gatilho is Gatilho.NOME
    assert pedido.atraso == 0.9
    assert not pedido.limite
    # 20 blocos de memória (11 a 30) + 15 do pedido (31 a 45), em ordem.
    valores = pedido.audio[::AMOSTRAS_POR_BLOCO]
    np.testing.assert_array_equal(valores, np.arange(11, 46))
    assert pedido.segundos == 3.5


def test_depois_do_pedido_abre_a_conversa_de_5_segundos():
    fim = FimRoteirizado([(5, Resultado.FIM)])
    escuta = Escuta(AtivacaoRoteirizada({3: Gatilho.FRASE}), fim)
    rodar(escuta, 10)
    assert escuta.estado is Estado.CONVERSA
    assert fim.esperas == [None, 5.0]


def test_pedido_na_conversa_vem_sem_o_nome():
    fim = FimRoteirizado([(5, Resultado.FIM), (10, Resultado.FIM)])
    escuta = Escuta(AtivacaoRoteirizada({3: Gatilho.NOME}), fim)
    eventos = rodar(escuta, 20)

    segundo = eventos[2][1]
    assert isinstance(segundo, Pedido)
    assert segundo.gatilho is None
    assert len(segundo.audio) == 10 * AMOSTRAS_POR_BLOCO


def test_conversa_sem_fala_volta_a_esperar():
    fim = FimRoteirizado([(5, Resultado.FIM), (50, Resultado.NADA)])
    escuta = Escuta(AtivacaoRoteirizada({3: Gatilho.NOME}), fim)
    eventos = rodar(escuta, 60)
    assert eventos[-1] == (58, SemPedido(None))
    assert escuta.estado is Estado.ESPERANDO


def test_chamado_sem_pedido():
    fim = FimRoteirizado([(30, Resultado.NADA)])
    escuta = Escuta(AtivacaoRoteirizada({3: Gatilho.FRASE}), fim)
    eventos = rodar(escuta, 40)
    assert eventos == [(3, Chamado(Gatilho.FRASE)), (33, SemPedido(Gatilho.FRASE))]
    assert escuta.estado is Estado.ESPERANDO


def test_pedido_cortado_no_limite():
    fim = FimRoteirizado([(300, Resultado.LIMITE)])
    escuta = Escuta(AtivacaoRoteirizada({3: Gatilho.NOME}), fim)
    pedido = rodar(escuta, 310)[1][1]
    assert pedido.limite
    assert pedido.atraso is None


def test_chamado_durante_o_pedido_e_ignorado():
    fim = FimRoteirizado([(20, Resultado.FIM)])
    ativacao = AtivacaoRoteirizada({3: Gatilho.FRASE, 10: Gatilho.FRASE})
    eventos = rodar(Escuta(ativacao, fim), 30)
    assert [type(e) for _, e in eventos] == [Chamado, Pedido]
    assert ativacao.blocos == 30


def test_mudo_ignora_tudo_ate_ser_desligado():
    ativacao = AtivacaoRoteirizada({3: Gatilho.FRASE, 8: Gatilho.FRASE})
    escuta = Escuta(ativacao, FimRoteirizado([(100, Resultado.FIM)]))
    escuta.definir_mudo(True)
    assert rodar(escuta, 5) == []
    assert ativacao.blocos == 0

    escuta.definir_mudo(False)
    assert escuta.estado is Estado.ESPERANDO
    # O roteiro não andou no mudo: o chamado do bloco 3 só chega agora.
    eventos = rodar(escuta, 10)
    assert eventos == [(3, Chamado(Gatilho.FRASE))]


def test_mudo_no_meio_do_pedido_descarta_o_pedido():
    escuta = Escuta(
        AtivacaoRoteirizada({3: Gatilho.NOME}), FimRoteirizado([(50, Resultado.FIM)])
    )
    rodar(escuta, 10)
    assert escuta.estado is Estado.OUVINDO
    escuta.definir_mudo(True)
    escuta.definir_mudo(False)
    assert escuta.estado is Estado.ESPERANDO


def test_ignis_arise_promovido_recomeca_o_acompanhamento():
    # Nome no bloco 3, frase no 8: o "Arise" não pode encerrar o pedido.
    fim = FimRoteirizado([(10, Resultado.FIM), (12, Resultado.FIM)])
    ativacao = AtivacaoRoteirizada({3: Gatilho.NOME, 8: Gatilho.FRASE})
    eventos = rodar(Escuta(ativacao, fim), 30)

    assert eventos[0] == (3, Chamado(Gatilho.NOME))
    indice, pedido = eventos[1]
    assert isinstance(pedido, Pedido)
    assert pedido.gatilho is Gatilho.FRASE
    assert indice == 20
    assert fim.esperas[:2] == [None, None]
