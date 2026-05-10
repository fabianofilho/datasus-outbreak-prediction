"""Pagina 5: Mapa de Surtos - distribuicao geografica de alertas.

Visualiza onde os alertas epidemiologicos estao ocorrendo no Brasil,
colorindo cada municipio pelo nivel de alerta e dimensionando pelo volume de casos.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from core.data.infodengue import fetch_city, series_for_forecast, DISEASES
from core.surtos.detector import classify_alert, summary_table, VERDE, AMARELO, VERMELHO
from core.viz.theme import inject, footer, badge, sidebar_back

st.set_page_config(
    page_title="Mapa de Surtos · datasus-outbreak-prediction",
    page_icon="🦠",
    layout="wide",
)
inject(subtitle="Mapa de Surtos")
badge("Distribuição Geográfica · InfoDengue · Capitais e Grandes Municípios")
st.caption(
    "Nível de alerta calculado por z-score rolante de 52 semanas. "
    "Tamanho da bolha proporcional ao número de casos na última semana disponível."
)

CIDADES: dict[str, dict] = {
    "Rio de Janeiro (RJ)":   {"geocode": "3304557", "lat": -22.9068, "lon": -43.1729, "uf": "RJ"},
    "Sao Paulo (SP)":        {"geocode": "3550308", "lat": -23.5505, "lon": -46.6333, "uf": "SP"},
    "Belo Horizonte (MG)":   {"geocode": "3106200", "lat": -19.9167, "lon": -43.9345, "uf": "MG"},
    "Fortaleza (CE)":        {"geocode": "2304400", "lat": -3.7172,  "lon": -38.5433, "uf": "CE"},
    "Manaus (AM)":           {"geocode": "1302603", "lat": -3.1190,  "lon": -60.0217, "uf": "AM"},
    "Salvador (BA)":         {"geocode": "2927408", "lat": -12.9714, "lon": -38.5014, "uf": "BA"},
    "Recife (PE)":           {"geocode": "2611606", "lat": -8.0539,  "lon": -34.8811, "uf": "PE"},
    "Porto Alegre (RS)":     {"geocode": "4314902", "lat": -30.0346, "lon": -51.2177, "uf": "RS"},
    "Curitiba (PR)":         {"geocode": "4106902", "lat": -25.4284, "lon": -49.2733, "uf": "PR"},
    "Belem (PA)":            {"geocode": "1501402", "lat": -1.4558,  "lon": -48.5044, "uf": "PA"},
    "Goiania (GO)":          {"geocode": "5208707", "lat": -16.6864, "lon": -49.2643, "uf": "GO"},
    "Brasilia (DF)":         {"geocode": "5300108", "lat": -15.7801, "lon": -47.9292, "uf": "DF"},
    "Natal (RN)":            {"geocode": "2408102", "lat": -5.7945,  "lon": -35.2110, "uf": "RN"},
    "Maceio (AL)":           {"geocode": "2704302", "lat": -9.6658,  "lon": -35.7350, "uf": "AL"},
    "Campo Grande (MS)":     {"geocode": "5002704", "lat": -20.4697, "lon": -54.6201, "uf": "MS"},
    "Teresina (PI)":         {"geocode": "2211001", "lat": -5.0892,  "lon": -42.8019, "uf": "PI"},
    "Joao Pessoa (PB)":      {"geocode": "2507507", "lat": -7.1195,  "lon": -34.8450, "uf": "PB"},
    "Aracaju (SE)":          {"geocode": "2800308", "lat": -10.9472, "lon": -37.0731, "uf": "SE"},
    "Cuiaba (MT)":           {"geocode": "5103403", "lat": -15.5989, "lon": -56.0949, "uf": "MT"},
    "Porto Velho (RO)":      {"geocode": "1100205", "lat": -8.7612,  "lon": -63.9004, "uf": "RO"},
}

COLOR_MAP = {VERDE: "#2ecc71", AMARELO: "#f39c12", VERMELHO: "#e74c3c"}
NIVEL_ORDER = [VERMELHO, AMARELO, VERDE]
NIVEL_RANK = {VERMELHO: 3, AMARELO: 2, VERDE: 1}

with st.sidebar:
    sidebar_back()
    st.header("Filtros")
    doenca = st.selectbox("Doença", DISEASES, index=0)
    ano_inicio = st.slider("Ano inicio", 2019, 2024, 2021)
    ano_fim = st.slider("Ano fim", 2020, 2024, 2024)
    st.divider()
    st.caption("Municípios sem histórico mínimo de 26 semanas são omitidos.")


@st.cache_data(ttl=3600, show_spinner=False)
def _load_alert(geocode: str, nome: str, doenca: str, y0: int, y1: int) -> dict:
    df = fetch_city(geocode, doenca, y0, y1)
    if df.empty:
        return {}
    series = series_for_forecast(df)
    if len(series) < 26:
        return {}
    alert_df = classify_alert(series)
    s = summary_table(alert_df, municipio=nome, doenca=doenca)
    if s.empty:
        return {}
    row = s.iloc[0]
    return {
        "municipio": nome,
        "nivel_alerta": str(row.get("nivel_alerta", VERDE)),
        "casos": float(row.get("casos", 0)),
        "z_score": float(row.get("z_score", 0)),
    }


with st.spinner("Carregando alertas para o mapa..."):
    rows = []
    for nome, info in CIDADES.items():
        result = _load_alert(info["geocode"], nome, doenca, ano_inicio, ano_fim)
        if result:
            rows.append({**result, "lat": info["lat"], "lon": info["lon"], "uf": info["uf"]})

if not rows:
    st.warning(
        "Nenhum dado disponível para o período selecionado. "
        "Tente ampliar o intervalo de anos ou selecionar outra doença."
    )
    st.stop()

map_df = pd.DataFrame(rows)
map_df["nivel_rank"] = map_df["nivel_alerta"].map(NIVEL_RANK).fillna(1)
map_df["casos_size"] = (map_df["casos"] + 5).clip(upper=400)
map_df = map_df.sort_values("nivel_rank", ascending=False)

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cidades monitoradas", len(map_df))
c2.metric("Alerta vermelho", int((map_df["nivel_alerta"] == VERMELHO).sum()))
c3.metric("Alerta amarelo", int((map_df["nivel_alerta"] == AMARELO).sum()))
c4.metric("Dentro do esperado", int((map_df["nivel_alerta"] == VERDE).sum()))

st.divider()

# --- Mapa ---
fig = px.scatter_mapbox(
    map_df,
    lat="lat",
    lon="lon",
    color="nivel_alerta",
    size="casos_size",
    hover_name="municipio",
    hover_data={
        "casos": True,
        "z_score": ":.2f",
        "uf": True,
        "lat": False,
        "lon": False,
        "casos_size": False,
        "nivel_rank": False,
    },
    color_discrete_map=COLOR_MAP,
    category_orders={"nivel_alerta": NIVEL_ORDER},
    mapbox_style="carto-positron",
    zoom=3.5,
    center={"lat": -14.5, "lon": -51.0},
    size_max=45,
    labels={
        "nivel_alerta": "Alerta",
        "casos": "Casos (ult. sem.)",
        "z_score": "Z-score",
        "uf": "UF",
    },
)
fig.update_layout(
    height=560,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="#ffffff",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b"),
    legend=dict(
        title="Nível de alerta",
        orientation="v",
        x=0.01,
        y=0.98,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#e2e8f0",
        borderwidth=1,
        font=dict(size=11),
    ),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Tabela de detalhes ---
st.subheader("Ranking de alertas")
display = (
    map_df[["municipio", "uf", "nivel_alerta", "casos", "z_score"]]
    .copy()
    .sort_values("nivel_rank", ascending=False)
    .drop(columns=[], errors="ignore")
)
display["nivel_alerta"] = display["nivel_alerta"].str.upper()
display["z_score"] = display["z_score"].round(2)
display["casos"] = display["casos"].astype(int)

def _row_style(row):
    nivel = row["nivel_alerta"].lower()
    colors = {"vermelho": "#fff5f5", "amarelo": "#fffbf0", "verde": "#f0fff4"}
    bg = colors.get(nivel, "#ffffff")
    return [f"background-color: {bg}"] * len(row)

st.dataframe(
    display.style.apply(_row_style, axis=1),
    use_container_width=True,
    hide_index=True,
)

footer("Mapa de Surtos")
