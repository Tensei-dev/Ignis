"""Baixa, confere e localiza os modelos do cérebro.

Os modelos ficam fora do repositório, em `%LOCALAPPDATA%\\Ignis\\modelos`, e só
são baixados pelo comando `ignis-cerebro baixar-modelos`. Cada arquivo é
conferido pelo SHA-256, e a versão do repositório é fixada por um commit.
"""

import hashlib
import logging
import os
import shutil
import tempfile
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

log = logging.getLogger(__name__)


class ErroDeModelo(Exception):
    """O modelo não pôde ser baixado ou não passou na conferência."""


@dataclass(frozen=True)
class Modelo:
    nome: str
    repositorio: str
    """Repositório no Hugging Face."""
    revisao: str
    """Commit exato do repositório, para o modelo nunca mudar sem aviso."""
    arquivos: dict[str, str]
    """Nome do arquivo -> SHA-256 esperado."""

    def url(self, arquivo: str) -> str:
        return f"https://huggingface.co/{self.repositorio}/resolve/{self.revisao}/{arquivo}"


WHISPER_TURBO = Modelo(
    nome="whisper-large-v3-turbo",
    repositorio="dropbox-dash/faster-whisper-large-v3-turbo",
    revisao="0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf",
    arquivos={
        "config.json": (
            "b0253ea6c0d3bea6b1e19e91a02acfd3b53f4467362efcb5a3e6b16c9b3a9b7e"
        ),
        "preprocessor_config.json": (
            "7ccc62c6f2765af1f3b46c00c9b5894426835a05021c8b9c01eecb6dfb542711"
        ),
        "tokenizer.json": (
            "297b13372ac43916285644fb9687add3cc62ee2a1adb60da3dc25cc94c1871fd"
        ),
        "vocabulary.json": (
            "c69260f2ab26d659b7c398f9a2b2b48ed0df16c3b47d7326782fd9cba71690c1"
        ),
        "model.bin": (
            "e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da"
        ),
    },
)
"""Whisper large-v3-turbo para o faster-whisper, licença MIT. 1,6 GB."""

TODOS = (WHISPER_TURBO,)


def pasta_do_ignis() -> Path:
    """Onde o Ignis guarda os seus dados nesta máquina, fora do repositório."""
    if local := os.environ.get("LOCALAPPDATA"):
        return Path(local) / "Ignis"
    return Path.home() / ".local" / "share" / "ignis"


def pasta_de_modelos() -> Path:
    """Onde os modelos ficam. A variável IGNIS_MODELOS muda o lugar."""
    if escolhida := os.environ.get("IGNIS_MODELOS"):
        return Path(escolhida)
    return pasta_do_ignis() / "modelos"


def caminho(modelo: Modelo, pasta: Path | None = None) -> Path:
    return (pasta or pasta_de_modelos()) / modelo.nome


def esta_baixado(modelo: Modelo, pasta: Path | None = None) -> bool:
    destino = caminho(modelo, pasta)
    return all((destino / arquivo).is_file() for arquivo in modelo.arquivos)


def baixar(
    modelo: Modelo,
    pasta: Path | None = None,
    abrir: Callable[[str], BinaryIO] = urllib.request.urlopen,
) -> Path:
    """Baixa cada arquivo e confere o SHA-256. Se algum falhar, nada é gravado."""
    destino = caminho(modelo, pasta)
    if esta_baixado(modelo, pasta):
        log.info("%s já está em %s", modelo.nome, destino)
        return destino

    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent) as temporaria:
        baixados = Path(temporaria) / "baixados"
        baixados.mkdir()
        for arquivo, esperado in modelo.arquivos.items():
            log.info("Baixando %s", modelo.url(arquivo))
            resumo = hashlib.sha256()
            with (
                abrir(modelo.url(arquivo)) as resposta,
                (baixados / arquivo).open("wb") as saida,
            ):
                while parte := resposta.read(1 << 20):
                    resumo.update(parte)
                    saida.write(parte)
            if resumo.hexdigest() != esperado:
                raise ErroDeModelo(
                    f"{modelo.nome}/{arquivo}: SHA-256 diferente do esperado. "
                    "O arquivo foi alterado ou corrompido, e foi descartado."
                )
        shutil.rmtree(destino, ignore_errors=True)
        baixados.rename(destino)

    log.info("%s pronto em %s", modelo.nome, destino)
    return destino
