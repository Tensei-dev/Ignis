import pytest

from ignis_cerebro.conferencia import conferir_chamado


@pytest.mark.parametrize(
    ("texto", "pedido"),
    [
        ("Ignis, coloca leite e café na lista", "coloca leite e café na lista"),
        ("Ignis Quais contas vencem esta semana?", "Quais contas vencem esta semana?"),
        ("Ignis Arise Que horas são?", "Que horas são?"),
        ("Ignis, arise! Que horas são?", "Que horas são?"),
        ("Igness, coloca leite e café na lista.", "coloca leite e café na lista."),
        ("Ignace, abre o Spotify.", "abre o Spotify."),
        ("IGNIS abre o Spotify", "abre o Spotify"),
        ("e aí, Ignis, que horas são", "que horas são"),
    ],
)
def test_acha_o_nome_e_devolve_o_pedido(texto, pedido):
    assert conferir_chamado(texto) == pedido


@pytest.mark.parametrize("texto", ["Ignis", "Ignis Arise.", "Ignis, arise!"])
def test_so_o_chamado_vira_pedido_vazio(texto):
    assert conferir_chamado(texto) == ""


@pytest.mark.parametrize(
    "texto",
    [
        "A igreja nova é bonita.",
        "Ignition, ignore it.",
        "Coloca leite e café na lista.",
        "Que horas são?",
        "",
        # O nome depois das primeiras palavras não conta como chamado.
        "Eu estava falando com o Pedro sobre o Ignis ontem",
        "Igris Arise",
    ],
)
def test_sem_o_nome_no_comeco_e_descartado(texto):
    assert conferir_chamado(texto) is None


def test_quantidade_de_palavras_antes_do_nome_e_configuravel():
    texto = "então eu disse Ignis abre o Spotify"
    assert conferir_chamado(texto, primeiras_palavras=3) is None
    assert conferir_chamado(texto, primeiras_palavras=4) == "abre o Spotify"
