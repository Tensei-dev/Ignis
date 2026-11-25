import numpy as np
import pytest

from ignis_pc.fim_da_fala import FimDaFala, Resultado, Trecho

BLOCO = np.zeros(1600, dtype=np.float32)


class VozRoteirizada:
    """Detector de voz falso, que segue um roteiro bloco a bloco.

    `fala`: blocos (contados desde o chamado) em que há um trecho em andamento.
    Como no detector real, um trecho continua "em andamento" durante os 0,8 s
    de silêncio que antecedem a entrega dele.
    `trechos`: bloco em que um trecho é entregue -> (bloco do início, bloco do fim).
    """

    def __init__(self, fala=(), trechos=None) -> None:
        self._fala = set(fala)
        self._trechos = trechos or {}
        self._bloco = 0
        self.reinicios = 0

    def reiniciar(self) -> None:
        self.reinicios += 1
        self._bloco = 0

    def processar(self, bloco) -> list[Trecho]:
        trecho = self._trechos.get(self._bloco)
        self._bloco += 1
        if trecho is None:
            return []
        inicio, fim = trecho
        return [Trecho(inicio * 1600, fim * 1600)]

    def falando(self) -> bool:
        return (self._bloco - 1) in self._fala


def acompanhar(fim: FimDaFala, blocos: int = 400) -> tuple[Resultado, int] | None:
    """Faz o chamado e devolve o resultado e em qual bloco ele saiu."""
    fim.comecar()
    for indice in range(blocos):
        if (resultado := fim.processar(BLOCO)) is not None:
            return resultado, indice
    return None


def test_pedido_termina_quando_um_trecho_de_fala_acaba():
    voz = VozRoteirizada(fala=range(0, 38), trechos={38: (0, 30)})
    fim = FimDaFala(voz)
    assert acompanhar(fim) == (Resultado.FIM, 38)
    # Fala acabou no bloco 30 e foi percebida no fim do bloco 38: 0,9 s.
    assert fim.atraso == pytest.approx(0.9)


def test_pausa_depois_do_nome_nao_encerra_o_pedido():
    # "Ignis" ... 1,5 s pensando ... "quais contas vencem" (fala do bloco 15 ao 40,
    # mais 0,8 s até o trecho ser entregue)
    voz = VozRoteirizada(fala=range(15, 48), trechos={48: (15, 40)})
    assert acompanhar(FimDaFala(voz)) == (Resultado.FIM, 48)


def test_chamado_sem_pedido_encerra_em_3_segundos():
    assert acompanhar(FimDaFala(VozRoteirizada())) == (Resultado.NADA, 29)


def test_nao_desiste_se_a_fala_comecou_antes_dos_3_segundos():
    voz = VozRoteirizada(fala=range(25, 68), trechos={68: (25, 60)})
    assert acompanhar(FimDaFala(voz)) == (Resultado.FIM, 68)


def test_pedido_longo_para_no_limite():
    voz = VozRoteirizada(fala=range(0, 1000))
    assert acompanhar(FimDaFala(voz, maximo=30.0)) == (Resultado.LIMITE, 299)


def test_fora_de_um_pedido_ignora_o_audio():
    voz = VozRoteirizada(trechos={0: (0, 1)})
    fim = FimDaFala(voz)
    assert not fim.ativo
    assert fim.processar(BLOCO) is None
    assert voz.reinicios == 0


def test_cada_chamado_reinicia_o_detector():
    voz = VozRoteirizada()
    fim = FimDaFala(voz)
    acompanhar(fim)
    acompanhar(fim)
    assert voz.reinicios == 2
    assert not fim.ativo


def test_conversa_pode_esperar_mais_que_o_chamado():
    fim = FimDaFala(VozRoteirizada(), espera_pelo_pedido=3.0)
    fim.comecar(espera_pelo_pedido=5.0)
    resultados = [fim.processar(BLOCO) for _ in range(60)]
    assert resultados.index(Resultado.NADA) == 49
