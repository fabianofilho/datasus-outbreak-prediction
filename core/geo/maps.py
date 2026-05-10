"""Mapas geograficos: choropleth e mapas de calor por municipio."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

_STATIC = Path(__file__).parent.parent.parent / "data" / "static"


def choropleth_by_municipio(
    df: pd.DataFrame,
    value_col: str,
    municipio_col: str = "codigo_6d",
    geojson_path: str | Path | None = None,
    title: str = "",
    colorscale: str = "Reds",
    hover_cols: list[str] | None = None,
) -> go.Figure:
    """Cria mapa choropleth por municipio usando GeoJSON do IBGE.

    Parameters
    ----------
    df           : DataFrame com municipio e valor
    value_col    : Coluna com o valor a exibir
    geojson_path : Path para GeoJSON de municipios. Se None, usa data/static/br_municipios.geojson
    """
    import json

    if geojson_path is None:
        geojson_path = _STATIC / "br_municipios.geojson"

    if not Path(geojson_path).exists():
        fig = go.Figure()
        fig.add_annotation(
            text="GeoJSON nao encontrado. Veja data/static/ para instrucoes.",
            showarrow=False,
        )
        return fig

    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    hover_data = {value_col: True}
    if hover_cols:
        for c in hover_cols:
            if c in df.columns:
                hover_data[c] = True

    import plotly.express as px
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations=municipio_col,
        color=value_col,
        color_continuous_scale=colorscale,
        title=title,
        hover_data=hover_data,
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title=value_col),
    )
    return fig


def alert_summary_map(
    alert_df: pd.DataFrame,
    municipio_col: str = "municipio",
    nivel_col: str = "nivel_alerta",
) -> go.Figure:
    """Mapa simples de alertas por municipio (sem GeoJSON, usando scatter)."""
    color_map = {"verde": "#2ecc71", "amarelo": "#f39c12", "vermelho": "#e74c3c"}

    if alert_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem alertas", showarrow=False)
        return fig

    fig = go.Figure()
    for nivel, color in color_map.items():
        sub = alert_df[alert_df[nivel_col] == nivel]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            name=nivel.capitalize(),
            x=sub[municipio_col],
            y=sub.get("casos", [1] * len(sub)),
            marker_color=color,
        ))

    fig.update_layout(
        barmode="group",
        title="Alertas por municipio",
        height=400,
        xaxis_tickangle=45,
        plot_bgcolor="#fafafa",
        margin=dict(l=20, r=20, t=50, b=100),
    )
    return fig
