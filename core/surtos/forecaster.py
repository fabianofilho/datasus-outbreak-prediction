"""Previsao de casos usando skforecast + LightGBM.

Adaptado de dengue-timeseries-skforecast/src/dengue_forecast/models.py.
Removido TimesFM, Prophet e SARIMAX para manter dependencias leves.
LightGBM e o padrao; XGBoost disponivel como alternativa.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from skforecast.recursive import ForecasterRecursive

warnings.filterwarnings("ignore", category=FutureWarning)
try:
    from skforecast.exceptions import IgnoredArgumentWarning
    warnings.filterwarnings("ignore", category=IgnoredArgumentWarning)
except ImportError:
    pass

MIN_TRAIN_WEEKS = 52


def forecast(
    series: pd.Series,
    horizon: int = 4,
    lags: int = 24,
    use_xgboost: bool = False,
) -> pd.DataFrame:
    """Treina um ForecasterRecursive e retorna previsao para horizonte semanas.

    Parameters
    ----------
    series      : Serie temporal de casos (index = data, freq semanal)
    horizon     : Numero de semanas a prever
    lags        : Numero de lags para o modelo
    use_xgboost : Se True, usa XGBoost; padrao LightGBM

    Returns
    -------
    DataFrame com colunas: data, previsao, lower_bound, upper_bound
    Retorna DataFrame vazio se serie muito curta.
    """
    series = series.dropna()
    if len(series) < MIN_TRAIN_WEEKS:
        return pd.DataFrame(columns=["data", "previsao", "lower_bound", "upper_bound"])

    if use_xgboost:
        from xgboost import XGBRegressor
        estimator = XGBRegressor(random_state=42, objective="reg:squarederror", verbosity=0)
    else:
        estimator = LGBMRegressor(random_state=42, verbosity=-1, n_estimators=200)

    lags = min(lags, len(series) // 2)
    forecaster = ForecasterRecursive(regressor=estimator, lags=lags)
    forecaster.fit(y=series)

    preds = forecaster.predict(steps=horizon)
    preds = np.maximum(0, preds.to_numpy())

    last_date = series.index[-1]
    dates = pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=horizon, freq="W")

    sigma = series.std()
    ci = 1.96 * sigma / np.sqrt(len(series))

    return pd.DataFrame({
        "data": dates,
        "previsao": preds,
        "lower_bound": np.maximum(0, preds - ci),
        "upper_bound": preds + ci,
    })


def forecast_with_history(
    series: pd.Series,
    horizon: int = 4,
    lags: int = 24,
) -> pd.DataFrame:
    """Retorna historico observado + previsao em um unico DataFrame.

    Colunas: data, casos, tipo (observado | previsto), lower_bound, upper_bound
    """
    hist = pd.DataFrame({
        "data": series.index,
        "casos": series.values,
        "tipo": "observado",
        "lower_bound": np.nan,
        "upper_bound": np.nan,
    })

    pred = forecast(series, horizon=horizon, lags=lags)
    if pred.empty:
        return hist

    pred_df = pd.DataFrame({
        "data": pred["data"],
        "casos": pred["previsao"],
        "tipo": "previsto",
        "lower_bound": pred["lower_bound"],
        "upper_bound": pred["upper_bound"],
    })

    return pd.concat([hist, pred_df], ignore_index=True)
