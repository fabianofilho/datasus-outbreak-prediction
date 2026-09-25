"""Previsao com skforecast: garante compatibilidade com a API estimator=."""

from __future__ import annotations

import numpy as np
import pandas as pd

from core.data.sinan import generate
from core.data.infodengue import series_for_forecast
from core.surtos.forecaster import MIN_TRAIN_WEEKS, forecast, forecast_with_history


def _serie_sintetica() -> pd.Series:
    return series_for_forecast(generate("3304557", "diarreia_aguda", 2020, 2024))


def test_forecast_retorna_horizonte_pedido():
    pred = forecast(_serie_sintetica(), horizon=4)

    assert list(pred.columns) == ["data", "previsao", "lower_bound", "upper_bound"]
    assert len(pred) == 4
    assert (pred["previsao"] >= 0).all()
    assert (pred["lower_bound"] <= pred["previsao"]).all()
    assert (pred["previsao"] <= pred["upper_bound"]).all()


def test_forecast_serie_curta_retorna_vazio():
    serie = _serie_sintetica().iloc[: MIN_TRAIN_WEEKS - 1]
    assert forecast(serie).empty


def test_forecast_with_history_marca_previstos():
    serie = _serie_sintetica()
    out = forecast_with_history(serie, horizon=3)

    assert (out["tipo"] == "observado").sum() == len(serie)
    assert (out["tipo"] == "previsto").sum() == 3
    assert np.isfinite(out.loc[out["tipo"] == "previsto", "casos"]).all()
