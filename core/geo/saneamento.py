"""Correlacao entre cobertura de saneamento e incidencia de doencas.

Analises:
  - Correlacao de Spearman: cobertura_esgoto x taxa_doencas_hidricas
  - Scatter com linha de regressao
  - Identificacao de municipios de alto risco (baixo saneamento + alta incidencia)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats


def risk_score(
    cobertura_esgoto: float,
    taxa_doenca: float,
    cobertura_max: float = 100.0,
    taxa_max: float = 1.0,
) -> float:
    """Score de risco combinado: baixo saneamento + alta taxa de doenca.

    Retorna valor entre 0 (baixo risco) e 1 (alto risco).
    """
    deficit = (cobertura_max - cobertura_esgoto) / cobertura_max
    normalized_taxa = min(taxa_doenca / taxa_max, 1.0) if taxa_max > 0 else 0
    return (deficit * 0.5 + normalized_taxa * 0.5)


def merge_snis_incidencia(
    snis_df: pd.DataFrame,
    incidencia_df: pd.DataFrame,
    codigo_col_snis: str = "codigo_6d",
    codigo_col_inc: str = "municipio_geocodigo",
) -> pd.DataFrame:
    """Faz merge entre dados SNIS e dados de incidencia por municipio.

    Retorna DataFrame com: codigo, cobertura_esgoto_pct, taxa_hidrica (casos/100k hab)
    """
    if snis_df.empty or incidencia_df.empty:
        return pd.DataFrame()

    inc = incidencia_df.copy()
    if codigo_col_inc in inc.columns:
        inc[codigo_col_inc] = inc[codigo_col_inc].astype(str).str[:6]

    merged = snis_df.merge(
        inc,
        left_on=codigo_col_snis,
        right_on=codigo_col_inc,
        how="inner",
    )
    return merged


def spearman_corr(
    df: pd.DataFrame,
    x_col: str = "cobertura_esgoto_pct",
    y_col: str = "taxa_hidrica",
) -> dict:
    """Calcula correlacao de Spearman entre cobertura de esgoto e incidencia.

    Returns dict com: rho, p_value, interpretacao
    """
    valid = df[[x_col, y_col]].dropna()
    if len(valid) < 5:
        return {"rho": None, "p_value": None, "interpretacao": "dados insuficientes"}

    rho, p = stats.spearmanr(valid[x_col], valid[y_col])

    if p > 0.05:
        interp = "sem correlacao estatisticamente significativa"
    elif rho < -0.5:
        interp = "correlacao negativa forte (mais esgoto = menos doenca)"
    elif rho < -0.2:
        interp = "correlacao negativa moderada"
    else:
        interp = "correlacao fraca ou positiva (inesperada)"

    return {"rho": round(rho, 3), "p_value": round(p, 4), "interpretacao": interp}


def scatter_saneamento_doenca(
    df: pd.DataFrame,
    x_col: str = "cobertura_esgoto_pct",
    y_col: str = "taxa_hidrica",
    municipio_col: str = "nome_municipio",
    title: str = "Cobertura de esgoto x Incidencia de doencas hidricas",
) -> go.Figure:
    """Scatter plot com linha de regressao e identificacao de municipios."""
    valid = df.dropna(subset=[x_col, y_col])

    if valid.empty:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes", showarrow=False)
        return fig

    fig = px.scatter(
        valid,
        x=x_col,
        y=y_col,
        hover_name=municipio_col if municipio_col in valid.columns else None,
        trendline="ols",
        labels={
            x_col: "Cobertura de esgoto (%)",
            y_col: "Taxa doencas hidricas (casos/100k hab)",
        },
        title=title,
        color_discrete_sequence=["#1f77b4"],
    )

    corr = spearman_corr(df, x_col, y_col)
    if corr["rho"] is not None:
        fig.add_annotation(
            x=0.02, y=0.97,
            xref="paper", yref="paper",
            text=f"Spearman rho={corr['rho']} | p={corr['p_value']}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#ccc",
            font=dict(size=11),
        )

    fig.update_layout(
        height=500,
        plot_bgcolor="#fafafa",
        margin=dict(l=60, r=20, t=50, b=60),
    )
    return fig


def high_risk_municipios(
    df: pd.DataFrame,
    esgoto_col: str = "cobertura_esgoto_pct",
    taxa_col: str = "taxa_hidrica",
    municipio_col: str = "nome_municipio",
    top_n: int = 20,
) -> pd.DataFrame:
    """Identifica os municipios de maior risco (baixo saneamento + alta incidencia)."""
    valid = df.dropna(subset=[esgoto_col, taxa_col]).copy()
    if valid.empty:
        return pd.DataFrame()

    taxa_max = valid[taxa_col].quantile(0.95)
    valid["risk_score"] = valid.apply(
        lambda r: risk_score(r[esgoto_col], r[taxa_col], taxa_max=max(taxa_max, 1)),
        axis=1,
    )

    cols = [municipio_col, esgoto_col, taxa_col, "risk_score"] if municipio_col in valid.columns else [esgoto_col, taxa_col, "risk_score"]
    return valid[cols].sort_values("risk_score", ascending=False).head(top_n).reset_index(drop=True)
