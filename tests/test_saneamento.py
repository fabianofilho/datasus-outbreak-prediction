"""Reta de tendencia do scatter saneamento x doenca sem statsmodels."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.geo.saneamento import linha_tendencia, scatter_saneamento_doenca


def test_linha_tendencia_recupera_reta_exata():
    x = pd.Series([10.0, 20.0, 30.0, 40.0])
    y = 100.0 - 2.0 * x

    x_reta, y_reta, a, b = linha_tendencia(x, y)

    assert a == pytest.approx(-2.0)
    assert b == pytest.approx(100.0)
    assert list(x_reta) == [10.0, 40.0]
    assert list(y_reta) == pytest.approx([80.0, 20.0])


@pytest.mark.parametrize("x, y", [
    ([50.0], [1.0]),
    ([30.0, 30.0, 30.0], [1.0, 2.0, 3.0]),
    ([np.nan, 10.0], [1.0, np.nan]),
])
def test_linha_tendencia_sem_ajuste_possivel(x, y):
    assert linha_tendencia(pd.Series(x), pd.Series(y)) is None


def test_scatter_tem_reta_sem_statsmodels(monkeypatch):
    import sys

    # Simula ambiente sem statsmodels: a figura nao pode depender dele
    monkeypatch.setitem(sys.modules, "statsmodels", None)
    monkeypatch.setitem(sys.modules, "statsmodels.api", None)

    df = pd.DataFrame({
        "cobertura_esgoto_pct": [10.0, 30.0, 50.0, 70.0, 90.0, 95.0],
        "taxa_hidrica": [90.0, 70.0, 55.0, 30.0, 12.0, 8.0],
        "nome_municipio": list("ABCDEF"),
    })
    fig = scatter_saneamento_doenca(df)

    modos = [t.mode for t in fig.data]
    assert modos == ["markers", "lines"]
