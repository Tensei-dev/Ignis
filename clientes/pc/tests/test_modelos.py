import hashlib
import io
import tarfile
from pathlib import Path

import pytest

from ignis_pc import modelos
from ignis_pc.modelos import ErroDeModelo, Modelo, baixar, esta_baixado


def pacote_tar(arquivos: dict[str, bytes]) -> bytes:
    memoria = io.BytesIO()
    with tarfile.open(fileobj=memoria, mode="w:bz2") as tar:
        for nome, conteudo in arquivos.items():
            info = tarfile.TarInfo(nome)
            info.size = len(conteudo)
            tar.addfile(info, io.BytesIO(conteudo))
    return memoria.getvalue()


CONTEUDO = {
    "pasta/a.onnx": b"modelo a",
    "pasta/tokens.txt": b"tokens",
    "pasta/sobra.txt": b"nao pedido",
    "../../fora.onnx": b"malicioso",
}
PACOTE = pacote_tar(CONTEUDO)


def modelo(sha256: str, arquivos=("a.onnx", "tokens.txt")) -> Modelo:
    return Modelo("teste", "https://exemplo/pacote.tar.bz2", sha256, arquivos)


def abrir_falso(url: str) -> io.BytesIO:
    return io.BytesIO(PACOTE)


def test_baixa_confere_e_extrai_so_os_arquivos_pedidos(tmp_path):
    certo = modelo(hashlib.sha256(PACOTE).hexdigest())
    destino = baixar(certo, tmp_path, abrir=abrir_falso)

    assert sorted(p.name for p in destino.iterdir()) == ["a.onnx", "tokens.txt"]
    assert (destino / "a.onnx").read_bytes() == b"modelo a"
    assert esta_baixado(certo, tmp_path)
    assert not list(tmp_path.rglob("fora.onnx"))
    assert not (tmp_path.parent / "fora.onnx").exists()


def test_recusa_pacote_com_sha256_diferente(tmp_path):
    errado = modelo("0" * 64)
    with pytest.raises(ErroDeModelo, match="SHA-256"):
        baixar(errado, tmp_path, abrir=abrir_falso)
    assert not esta_baixado(errado, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_avisa_quando_falta_arquivo_no_pacote(tmp_path):
    incompleto = modelo(hashlib.sha256(PACOTE).hexdigest(), ("a.onnx", "b.onnx"))
    with pytest.raises(ErroDeModelo, match=r"b\.onnx"):
        baixar(incompleto, tmp_path, abrir=abrir_falso)


def test_nao_baixa_de_novo_o_que_ja_existe(tmp_path):
    certo = modelo(hashlib.sha256(PACOTE).hexdigest())
    baixar(certo, tmp_path, abrir=abrir_falso)

    def nao_deveria_baixar(url: str):
        raise AssertionError("baixou de novo")

    baixar(certo, tmp_path, abrir=nao_deveria_baixar)


def test_pasta_vem_da_variavel_de_ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("IGNIS_MODELOS", str(tmp_path))
    assert modelos.pasta_de_modelos() == Path(tmp_path)


def test_pasta_padrao_fica_no_localappdata(monkeypatch, tmp_path):
    monkeypatch.delenv("IGNIS_MODELOS", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert modelos.pasta_de_modelos() == tmp_path / "Ignis" / "modelos"
