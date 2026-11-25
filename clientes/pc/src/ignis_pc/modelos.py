"""Baixa, confere e localiza os modelos de voz.

Os modelos ficam fora do repositório, em `%LOCALAPPDATA%\\Ignis\\modelos`, e só
são baixados pelo comando `ignis-pc baixar-modelos`.
"""

import hashlib
import logging
import os
import shutil
import tarfile
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
    url: str
    sha256: str
    arquivos: tuple[str, ...]
    compactado: bool = True
    """False quando a URL aponta direto para o único arquivo do modelo."""


DETECTOR_DE_FRASES = Modelo(
    nome="kws-zipformer-gigaspeech-3.3M",
    url=(
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/"
        "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01.tar.bz2"
    ),
    sha256="f170013b4716e41b62b9bfd809687c207cef798ef9bc6534d524e17af9b6561a",
    arquivos=(
        "encoder-epoch-12-avg-2-chunk-16-left-64.onnx",
        "decoder-epoch-12-avg-2-chunk-16-left-64.onnx",
        "joiner-epoch-12-avg-2-chunk-16-left-64.onnx",
        "tokens.txt",
    ),
)
"""Detector de frases do sherpa-onnx, licença Apache 2.0 segundo o autor."""

DETECTOR_DE_VOZ = Modelo(
    nome="silero-vad",
    url=(
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
        "silero_vad.onnx"
    ),
    sha256="9e2449e1087496d8d4caba907f23e0bd3f78d91fa552479bb9c23ac09cbb1fd6",
    arquivos=("silero_vad.onnx",),
    compactado=False,
)
"""Silero VAD, que diz se há voz humana no áudio. Licença MIT."""

TODOS = (DETECTOR_DE_FRASES, DETECTOR_DE_VOZ)


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
    """Baixa o modelo, confere o SHA-256 e extrai só os arquivos necessários.

    Se a conferência falhar, nada é gravado no destino.
    """
    destino = caminho(modelo, pasta)
    if esta_baixado(modelo, pasta):
        log.info("%s já está em %s", modelo.nome, destino)
        return destino

    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent) as temporaria:
        pacote = Path(temporaria) / "pacote"
        log.info("Baixando %s", modelo.url)
        resumo = hashlib.sha256()
        with abrir(modelo.url) as resposta, pacote.open("wb") as saida:
            while parte := resposta.read(1 << 20):
                resumo.update(parte)
                saida.write(parte)

        if resumo.hexdigest() != modelo.sha256:
            raise ErroDeModelo(
                f"{modelo.nome}: SHA-256 diferente do esperado. "
                "O arquivo foi alterado ou corrompido, e foi descartado."
            )

        extraidos = Path(temporaria) / "extraidos"
        extraidos.mkdir()
        if modelo.compactado:
            _extrair(pacote, modelo.arquivos, extraidos)
        else:
            pacote.rename(extraidos / modelo.arquivos[0])

        shutil.rmtree(destino, ignore_errors=True)
        extraidos.rename(destino)

    log.info("%s pronto em %s", modelo.nome, destino)
    return destino


def _extrair(pacote: Path, arquivos: tuple[str, ...], destino: Path) -> None:
    """Copia do pacote só os arquivos pedidos, pelo nome, ignorando as pastas.

    Os caminhos de dentro do pacote nunca são usados para gravar, então um
    pacote malicioso não consegue escrever fora de `destino`.
    """
    faltando = set(arquivos)
    with tarfile.open(pacote) as tar:
        for membro in tar:
            nome = Path(membro.name).name
            if nome not in faltando or not membro.isfile():
                continue
            origem = tar.extractfile(membro)
            if origem is None:
                continue
            with origem, (destino / nome).open("wb") as saida:
                shutil.copyfileobj(origem, saida)
            faltando.discard(nome)
    if faltando:
        raise ErroDeModelo(f"Arquivos ausentes no pacote: {sorted(faltando)}")
