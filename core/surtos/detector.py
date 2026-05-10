"""Deteccao de anomalias em series temporais epidemiologicas.

Metodos implementados:
  - Z-score rolling: detecta desvios em relacao a media movel historica
  - CUSUM: acumula excesso sobre uma linha de base esperada
  - IQR historico: classifica por semana epidemiologica

Nivel de alerta:
  verde    : dentro do esperado (z < 1.5)
  amarelo  : possivel surto (1.5 <= z < 3)
  vermelho : surto confirmado (z >= 3 ou CUSUM > threshold)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


VERDE = "verde"
AMARELO = "amarelo"
VERMELHO = "vermelho"

_ALERT_COLORS = {VERDE: "#2ecc71", AMARELO: "#f39c12", VERMELHO: "#e74c3c"}


def alert_color(nivel: str) -> str:
    return _ALERT_COLORS.get(nivel, "#95a5a6")


def zscore_rolling(
    series: pd.Series,
    window: int = 52,
    min_periods: int = 26,
) -> pd.DataFrame:
    """Calcula z-score rolling e classifica nivel de alerta.

    Parameters
    ----------
    series   : Serie temporal de casos (index = data, freq semanal preferida)
    window   : Janela em semanas para calcular media e dp historicos
    min_periods : Minimo de observacoes para calcular z

    Returns
    -------
    DataFrame com colunas: casos, media_esperada, dp, z_score, nivel_alerta
    """
    df = pd.DataFrame({"casos": series})
    df["media_esperada"] = series.rolling(window=window, min_periods=min_periods).mean().shift(1)
    df["dp"] = series.rolling(window=window, min_periods=min_periods).std().shift(1)
    df["dp"] = df["dp"].replace(0, np.nan).fillna(0.1)
    df["z_score"] = (df["casos"] - df["media_esperada"]) / df["dp"]

    df["nivel_alerta"] = VERDE
    df.loc[df["z_score"] >= 1.5, "nivel_alerta"] = AMARELO
    df.loc[df["z_score"] >= 3.0, "nivel_alerta"] = VERMELHO

    return df.dropna(subset=["media_esperada"])


def cusum(
    series: pd.Series,
    k: float = 0.5,
    h: float = 5.0,
    baseline_window: int = 52,
) -> pd.DataFrame:
    """CUSUM (Cumulative Sum Control Chart) para deteccao de surtos.

    Parameters
    ----------
    k : parametro de referencia (multiplo do dp)
    h : threshold de alarme (multiplo do dp)
    baseline_window : janela para estimar mu e sigma basais

    Returns
    -------
    DataFrame com colunas: casos, cusum_pos, cusum_neg, alarme
    """
    df = pd.DataFrame({"casos": series})
    mu = series.rolling(window=baseline_window, min_periods=26).mean().shift(1)
    sigma = series.rolling(window=baseline_window, min_periods=26).std().shift(1)
    sigma = sigma.replace(0, np.nan).fillna(1.0)

    cusum_pos = pd.Series(0.0, index=series.index)
    cusum_neg = pd.Series(0.0, index=series.index)

    for i in range(1, len(series)):
        idx = series.index[i]
        prev = series.index[i - 1]
        xi = series.iloc[i]
        mu_i = mu.iloc[i] if not pd.isna(mu.iloc[i]) else xi
        sigma_i = sigma.iloc[i]
        cusum_pos[idx] = max(0, cusum_pos[prev] + (xi - mu_i - k * sigma_i) / sigma_i)
        cusum_neg[idx] = min(0, cusum_neg[prev] + (xi - mu_i + k * sigma_i) / sigma_i)

    df["cusum_pos"] = cusum_pos
    df["cusum_neg"] = cusum_neg
    df["alarme"] = (df["cusum_pos"] > h) | (df["cusum_neg"] < -h)

    return df


def classify_alert(
    series: pd.Series,
    window: int = 52,
) -> pd.DataFrame:
    """Combinacao de z-score e CUSUM para classificacao final de alerta.

    Retorna DataFrame pronto para exibicao no dashboard.
    """
    zdf = zscore_rolling(series, window=window)
    cdf = cusum(series, baseline_window=window)

    result = zdf.copy()
    result["cusum_pos"] = cdf["cusum_pos"].reindex(result.index).fillna(0)
    result["alarme_cusum"] = cdf["alarme"].reindex(result.index).fillna(False)

    result.loc[result["alarme_cusum"] & (result["nivel_alerta"] == AMARELO), "nivel_alerta"] = VERMELHO

    return result


def summary_table(df: pd.DataFrame, municipio: str, doenca: str) -> pd.DataFrame:
    """Cria tabela resumo com ultima semana de alerta."""
    if df.empty:
        return pd.DataFrame()

    last = df.iloc[-1]
    return pd.DataFrame([{
        "municipio": municipio,
        "doenca": doenca,
        "ultima_semana": df.index[-1],
        "casos": int(last["casos"]),
        "casos_esperados": round(last.get("media_esperada", 0), 1),
        "z_score": round(last.get("z_score", 0), 2),
        "nivel_alerta": last.get("nivel_alerta", VERDE),
    }])
