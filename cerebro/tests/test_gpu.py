from ignis_cerebro.gpu import LeituraDeGpu, MonitorDeGpu


def leitura(uso: float, vram: float = 6000.0) -> LeituraDeGpu:
    return LeituraDeGpu(uso=uso, vram_livre_mib=vram)


def monitor(**opcoes) -> MonitorDeGpu:
    # janela de 5 s com uma leitura a cada 0,5 s: guarda as 10 últimas.
    return MonitorDeGpu(ler=None, **opcoes)


def test_sem_leituras_nao_bloqueia():
    assert not monitor().ocupada()


def test_uso_baixo_esta_livre():
    m = monitor()
    for _ in range(10):
        m.registrar(leitura(3))
    assert not m.ocupada()


def test_jogo_usando_a_gpu_acima_do_limite_bloqueia():
    m = monitor(limite=60)
    for _ in range(10):
        m.registrar(leitura(95))
    assert m.ocupada()


def test_um_pico_isolado_nao_bloqueia():
    m = monitor(limite=60)
    for uso in [3, 3, 3, 100, 3, 3, 3, 3, 3, 3]:
        m.registrar(leitura(uso))
    assert not m.ocupada()


def test_so_as_leituras_recentes_contam():
    m = monitor(limite=60)
    for _ in range(10):
        m.registrar(leitura(95))
    for _ in range(10):
        m.registrar(leitura(5))
    assert not m.ocupada()


def test_pouca_memoria_de_video_bloqueia():
    m = monitor(vram_minima_mib=300)
    m.registrar(leitura(5, vram=200))
    assert m.ocupada()


def test_leituras_durante_o_trabalho_do_ignis_sao_descartadas():
    m = monitor(limite=60)
    for _ in range(10):
        m.registrar(leitura(3))
    with m.trabalhando():
        for _ in range(10):
            m.registrar(leitura(100))
    assert not m.ocupada()
    assert m.uso_medio() == 3


def test_sem_gpu_nvidia_o_monitor_fica_indisponivel():
    m = monitor()
    assert not m.disponivel
    m.iniciar()
    m.parar()
