"""Testes com o modelo de verdade. Rodam só onde ele já foi baixado.

Para rodar: `uv run ignis-pc baixar-modelos` e depois `uv run pytest`.
"""

import numpy as np
import pytest

from ignis_pc.modelos import DETECTOR_DE_FRASES, caminho, esta_baixado

pytestmark = pytest.mark.skipif(
    not esta_baixado(DETECTOR_DE_FRASES),
    reason="modelo não baixado: rode `uv run ignis-pc baixar-modelos`",
)


@pytest.mark.parametrize("frases", ["FRASES_DA_FRASE", "FRASES_DO_NOME"])
def test_carrega_e_nao_dispara_com_silencio_nem_ruido(frases, tmp_path):
    import shutil

    from ignis_pc import ativacao

    # Usa uma cópia, para não gravar o arquivo de frases na pasta real.
    pasta = tmp_path / "modelo"
    shutil.copytree(caminho(DETECTOR_DE_FRASES), pasta)
    detector = ativacao.DetectorSherpa(pasta, getattr(ativacao, frases))

    ruido = np.random.default_rng(0).normal(0, 0.05, 16000 * 5).astype(np.float32)
    audio = np.concatenate([np.zeros(16000 * 5, dtype=np.float32), ruido])
    assert not any(
        detector.processar(audio[i : i + 1600]) for i in range(0, len(audio), 1600)
    )
