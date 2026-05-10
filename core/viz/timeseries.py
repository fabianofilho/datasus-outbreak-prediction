"""Visualizacoes de series temporais com previsao e alertas."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from core.surtos.detector import alert_color, VERDE, AMARELO, VERMELHO


def plot_series_with_forecast(
    df: pd.DataFrame,
    municipio: str = "",
    doenca: str = "dengue",
) -> go.Figure:
    """Plota serie observada + banda de previsao + coloracao de nivel de alerta.

    Parameters
    ----------
    df : DataFrame com colunas data, casos, tipo (observado|previsto),
         lower_bound, upper_bound, nivel_alerta (opcional)
    """
    obs = df[df["tipo"] == "observado"]
    prev = df[df["tipo"] == "previsto"]

    fig = go.Figure()

    # Linha observada com coloracao por nivel de alerta
    if "nivel_alerta" in obs.columns:
        for nivel in [VERDE, AMARELO, VERMELHO]:
            sub = obs[obs["nivel_alerta"] == nivel]
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub["data"], y=sub["casos"],
                mode="lines+markers",
                name=f"Observado ({nivel})",
                line=dict(color=alert_color(nivel), width=2),
                marker=dict(size=4),
                showlegend=True,
            ))
    else:
        fig.add_trace(go.Scatter(
            x=obs["data"], y=obs["casos"],
            mode="lines+markers",
            name="Observado",
            line=dict(color="#2980b9", width=2),
            marker=dict(size=4),
        ))

    # Banda de previsao
    if not prev.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([prev["data"], prev["data"].iloc[::-1]]),
            y=pd.concat([prev["upper_bound"], prev["lower_bound"].iloc[::-1]]),
            fill="toself",
            fillcolor="rgba(231, 76, 60, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=prev["data"], y=prev["casos"],
            mode="lines+markers",
            name="Previsao",
            line=dict(color="#e74c3c", width=2, dash="dot"),
            marker=dict(size=6, symbol="diamond"),
        ))

    title = f"Casos de {doenca}"
    if municipio:
        title += f" - {municipio}"

    fig.update_layout(
        title=title,
        xaxis_title="Data",
        yaxis_title="Casos",
        hovermode="x unified",
        height=420,
        plot_bgcolor="#fafafa",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=50, r=20, t=50, b=80),
    )
    return fig


def plot_alert_table_bar(
    summary_df: pd.DataFrame,
    top_n: int = 20,
) -> go.Figure:
    """Grafico de barras horizontais dos municipios por nivel de alerta."""
    color_map = {"verde": "#2ecc71", "amarelo": "#f39c12", "vermelho": "#e74c3c"}

    if summary_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados de alerta", showarrow=False)
        return fig

    order = [VERMELHO, AMARELO, VERDE]
    df = summary_df[summary_df["nivel_alerta"].isin(order)].copy()
    df["nivel_ordem"] = df["nivel_alerta"].map({VERMELHO: 0, AMARELO: 1, VERDE: 2})
    df = df.sort_values(["nivel_ordem", "z_score"], ascending=[True, False]).head(top_n)

    colors = [color_map.get(n, "#95a5a6") for n in df["nivel_alerta"]]

    fig = go.Figure(go.Bar(
        y=df["municipio"],
        x=df["z_score"],
        orientation="h",
        marker_color=colors,
        hovertext=[
            f"{row['municipio']}<br>Casos: {row['casos']}<br>Z-score: {row['z_score']}<br>Nivel: {row['nivel_alerta']}"
            for _, row in df.iterrows()
        ],
        hoverinfo="text",
    ))

    fig.update_layout(
        title=f"Top {top_n} municipios por nivel de alerta",
        xaxis_title="Z-score",
        height=max(350, top_n * 22),
        plot_bgcolor="#fafafa",
        margin=dict(l=150, r=20, t=50, b=40),
        bargap=0.15,
    )
    return fig
