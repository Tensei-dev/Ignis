import hashlib
import io
from pathlib import Path

import pytest

from ignis_cerebro import modelos
from ignis_cerebro.modelos import ErroDeModelo, Modelo, baixar, esta_baixado

ARQUIVOS = {"config.json": b"{}", "model.bin": b"pesos"}


def modelo(arquivos: dict[str, bytes], errado: str | None = None) -> Modelo:
    hashes = {
        nome: hashlib.sha256(dados).hexdigest() for nome, dados in arquivos.items()
    }
    if errado:
        hashes[errado] = "0" * 64
    return Modelo("teste", "dono/repo", "abc123", hashes)


def abrir_falso(url: str) -> io.BytesIO:
    return io.BytesIO(ARQUIVOS[url.rsplit("/", 1)[1]])


def test_url_fica_presa_a_uma_revisao():
    assert modelo(ARQUIVOS).url("model.bin") == (
        "https://huggingface.co/dono/repo/resolve/abc123/model.bin"
    )


def test_baixa_e_confere_cada_arquivo(tmp_path):
    certo = modelo(ARQUIVOS)
    destino = baixar(certo, tmp_path, abrir=abrir_falso)
    assert sorted(p.name for p in destino.iterdir()) == ["config.json", "model.bin"]
    assert esta_baixado(certo, tmp_path)


def test_um_arquivo_alterado_descarta_tudo(tmp_path):
    errado = modelo(ARQUIVOS, errado="model.bin")
    with pytest.raises(ErroDeModelo, match="model.bin"):
        baixar(errado, tmp_path, abrir=abrir_falso)
    assert list(tmp_path.iterdir()) == []


def test_nao_baixa_de_novo(tmp_path):
    certo = modelo(ARQUIVOS)
    baixar(certo, tmp_path, abrir=abrir_falso)

    def nao_deveria(url: str):
        raise AssertionError("baixou de novo")

    baixar(certo, tmp_path, abrir=nao_deveria)


def test_pasta_padrao_fica_no_localappdata(monkeypatch, tmp_path):
    monkeypatch.delenv("IGNIS_MODELOS", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert modelos.pasta_de_modelos() == Path(tmp_path) / "Ignis" / "modelos"


def test_whisper_tem_revisao_e_hash_de_todos_os_arquivos():
    whisper = modelos.WHISPER_TURBO
    assert len(whisper.revisao) == 40
    assert set(whisper.arquivos) >= {"model.bin", "config.json", "tokenizer.json"}
    assert all(len(h) == 64 for h in whisper.arquivos.values())
