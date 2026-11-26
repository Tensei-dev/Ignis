import subprocess
import sys
import wave

import numpy as np
import pytest

from ignis_cerebro.gpu import LeituraDeGpu, MonitorDeGpu
from ignis_cerebro.transcricao import GpuOcupada, TranscritorWhisper, ler_wav


def gravar_wav(arquivo, audio, taxa=16000, canais=1, bits=16):
    with wave.open(str(arquivo), "wb") as saida:
        saida.setnchannels(canais)
        saida.setsampwidth(bits // 8)
        saida.setframerate(taxa)
        saida.writeframes((audio * 32767).astype(np.int16).tobytes())


def test_le_o_wav_salvo_pelo_cliente(tmp_path):
    audio = np.linspace(-0.5, 0.5, 16000, dtype=np.float32)
    gravar_wav(tmp_path / "pedido.wav", audio)
    lido = ler_wav(tmp_path / "pedido.wav")
    assert lido.dtype == np.float32
    np.testing.assert_allclose(lido, audio, atol=1e-4)


def test_recusa_wav_em_outro_formato(tmp_path):
    gravar_wav(tmp_path / "errado.wav", np.zeros(48000, np.float32), taxa=48000)
    with pytest.raises(ValueError, match="16 kHz"):
        ler_wav(tmp_path / "errado.wav")


class ModeloFalso:
    def __init__(self) -> None:
        self.chamadas = 0

    def transcribe(self, audio, **opcoes):
        self.chamadas += 1
        self.opcoes = opcoes

        class Trecho:
            text = " Ignis, que horas são? "

        return [Trecho()], None


def transcritor_falso(monitor=None) -> tuple[TranscritorWhisper, ModeloFalso]:
    transcritor = TranscritorWhisper.__new__(TranscritorWhisper)
    modelo = ModeloFalso()
    transcritor._modelo = modelo
    transcritor._monitor = monitor
    return transcritor, modelo


def test_transcreve_em_portugues_com_a_dica_do_nome():
    transcritor, modelo = transcritor_falso()
    resultado = transcritor.transcrever(np.zeros(32000, np.float32))
    assert resultado.texto == "Ignis, que horas são?"
    assert resultado.duracao_do_audio == 2.0
    assert resultado.segundos >= 0
    assert modelo.opcoes["language"] == "pt"
    assert modelo.opcoes["hotwords"] == "Ignis"


def test_com_a_gpu_ocupada_avisa_e_nao_transcreve():
    monitor = MonitorDeGpu(ler=None)
    for _ in range(10):
        monitor.registrar(LeituraDeGpu(uso=97, vram_livre_mib=2000))
    transcritor, modelo = transcritor_falso(monitor)
    with pytest.raises(GpuOcupada):
        transcritor.transcrever(np.zeros(16000, np.float32))
    assert modelo.chamadas == 0


def test_o_proprio_trabalho_nao_conta_como_uso():
    monitor = MonitorDeGpu(ler=None)
    transcritor, _ = transcritor_falso(monitor)

    class Espiao:
        def transcribe(self, audio, **opcoes):
            monitor.registrar(LeituraDeGpu(uso=100, vram_livre_mib=2000))
            return [], None

    transcritor._modelo = Espiao()
    transcritor.transcrever(np.zeros(16000, np.float32))
    assert monitor.uso_medio() is None


def test_importar_o_cerebro_nao_carrega_o_whisper():
    codigo = (
        "import sys, ignis_cerebro, ignis_cerebro.conferencia, ignis_cerebro.gpu,"
        " ignis_cerebro.modelos, ignis_cerebro.transcricao;"
        "print(sorted({'faster_whisper', 'ctranslate2'} & set(sys.modules)))"
    )
    saida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    )
    assert saida.stdout.strip() == "[]"


def test_comando_transcrever_confere_o_chamado_mas_nao_a_conversa(
    tmp_path, monkeypatch, capsys
):
    import ignis_cerebro
    from ignis_cerebro import modelos, transcricao

    class TranscritorDeMentira:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def transcrever(self, audio):
            return transcricao.Transcricao("quais contas vencem", 0.2, 1.0)

    monkeypatch.setattr(transcricao, "TranscritorWhisper", TranscritorDeMentira)
    monkeypatch.setattr(modelos, "esta_baixado", lambda modelo: True)
    for nome in ("pedido_1_nome.wav", "pedido_2_conversa.wav"):
        gravar_wav(tmp_path / nome, np.zeros(16000, np.float32))

    ignis_cerebro.main(
        [
            "transcrever",
            str(tmp_path / "pedido_1_nome.wav"),
            str(tmp_path / "pedido_2_conversa.wav"),
        ]
    )
    saida = capsys.readouterr().out
    nome, conversa = saida.split("pedido_2_conversa.wav")
    assert "seria descartado" in nome
    assert "pedido: 'quais contas vencem'" in conversa
