"""Pagina 5: Mapa de Surtos - distribuicao geografica de alertas."""

import streamlit as st
import pandas as pd
import plotly.express as px

from core.data.infodengue import fetch_city, series_for_forecast, DISEASE_LABELS
from core.data.municipios import load as load_municipios, display_options, default_capitals
from core.surtos.detector import classify_alert, summary_table, VERDE, AMARELO, VERMELHO
from core.viz.theme import inject, footer, badge, sidebar_back, empty_state

st.set_page_config(
    page_title="Mapa de Surtos · datasus-outbreak-prediction",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject(subtitle="Mapa de Surtos")
badge("Distribuição Geográfica · InfoDengue · Municípios selecionados")
st.caption(
    "Nível de alerta calculado por z-score rolante de 52 semanas. "
    "Tamanho da bolha proporcional ao número de casos na última semana disponível."
)

COLOR_MAP = {VERDE: "#2ecc71", AMARELO: "#f39c12", VERMELHO: "#e74c3c"}
NIVEL_ORDER = [VERMELHO, AMARELO, VERDE]
NIVEL_RANK  = {VERMELHO: 3, AMARELO: 2, VERDE: 1}

# Coordenadas fixas para municipios conhecidos (evita chamadas lentas de API)
_COORDS_FIXAS: dict[str, tuple[float, float]] = {
    "3304557": (-22.9068, -43.1729),
    "3550308": (-23.5505, -46.6333),
    "3106200": (-19.9167, -43.9345),
    "2304400": (-3.7172,  -38.5433),
    "1302603": (-3.1190,  -60.0217),
    "2927408": (-12.9714, -38.5014),
    "2611606": (-8.0539,  -34.8811),
    "4314902": (-30.0346, -51.2177),
    "4106902": (-25.4284, -49.2733),
    "1501402": (-1.4558,  -48.5044),
    "5208707": (-16.6864, -49.2643),
    "5300108": (-15.7801, -47.9292),
    "2408102": (-5.7945,  -35.2110),
    "2704302": (-9.6658,  -35.7350),
    "5002704": (-20.4697, -54.6201),
    "2211001": (-5.0892,  -42.8019),
    "2507507": (-7.1195,  -34.8450),
    "2800308": (-10.9472, -37.0731),
    "5103403": (-15.5989, -56.0949),
    "1100205": (-8.7612,  -63.9004),
    "1600303": (0.0349,   -51.0694),
    "1400100": (2.8235,   -60.6758),
    "1721000": (-10.1689, -48.3317),
    "1200401": (-9.9754,  -67.8249),
    "2111300": (-2.5307,  -44.3068),
    "3205309": (-20.3222, -40.3381),
    "4205407": (-27.5954, -48.5480),
}


@st.cache_data(ttl=86400, show_spinner=False)
def get_municipio_options() -> dict[str, str]:
    return display_options(load_municipios())


with st.sidebar:
    sidebar_back()
    st.header("Filtros")

    doenca = st.selectbox(
        "Doença",
        options=list(DISEASE_LABELS.keys()),
        format_func=lambda d: DISEASE_LABELS[d],
        index=0,
    )
    _sintetico = doenca not in {"dengue", "chikungunya", "zika"}
    if _sintetico:
        st.caption("Dados simulados com sazonalidade epidemiológica real.")

    ano_inicio = st.slider("Ano inicio", 2019, 2024, 2021)
    ano_fim    = st.slider("Ano fim",    2020, 2024, 2024)

    st.divider()
    st.subheader("Municípios")
    st.caption("Digite nome ou UF para filtrar os 5.570 municípios brasileiros.")

    mun_opts    = get_municipio_options()
    caps_default = [k for k in default_capitals() if k in mun_opts]

    cidades_sel = st.multiselect(
        "Selecionar municípios",
        options=list(mun_opts.keys()),
        default=caps_default,
        placeholder="Ex: Campinas (SP)",
    )

    st.divider()
    st.caption("Municípios sem histórico mínimo de 26 semanas são omitidos.")
    analisar = st.button("Analisar", type="primary", use_container_width=True)


# --- Estado inicial ---
if analisar:
    st.session_state["mapa_ok"]  = True
    st.session_state["mapa_cfg"] = {
        "cidades": cidades_sel,
        "doenca":  doenca,
        "ano_inicio": ano_inicio,
        "ano_fim":    ano_fim,
    }

if not st.session_state.get("mapa_ok"):
    empty_state(
        "Configure os filtros e clique em Analisar",
        "Selecione municípios e doença para visualizar a distribuição geográfica dos alertas.",
    )
    footer("Mapa de Surtos")
    st.stop()

cfg         = st.session_state["mapa_cfg"]
cidades_sel = cfg["cidades"]
doenca      = cfg["doenca"]
ano_inicio  = cfg["ano_inicio"]
ano_fim     = cfg["ano_fim"]


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
        "municipio":   nome,
        "geocode":     geocode,
        "nivel_alerta": str(row.get("nivel_alerta", VERDE)),
        "casos":       float(row.get("casos", 0)),
        "z_score":     float(row.get("z_score", 0)),
    }


with st.spinner("Carregando alertas para o mapa..."):
    rows = []
    for nome in cidades_sel:
        geocode = mun_opts.get(nome)
        if not geocode:
            continue
        result = _load_alert(geocode, nome, doenca, ano_inicio, ano_fim)
        if result:
            lat, lon = _COORDS_FIXAS.get(geocode, (-14.5, -51.0))
            uf = nome.split("(")[-1].rstrip(")") if "(" in nome else ""
            rows.append({**result, "lat": lat, "lon": lon, "uf": uf})

if not rows:
    st.warning(
        "Nenhum dado disponível para o período selecionado. "
        "Tente ampliar o intervalo de anos ou selecionar outra doença."
    )
    footer("Mapa de Surtos")
    st.stop()

map_df = pd.DataFrame(rows)
map_df["nivel_rank"] = map_df["nivel_alerta"].map(NIVEL_RANK).fillna(1)
map_df["casos_size"] = (map_df["casos"] + 5).clip(upper=400)
map_df = map_df.sort_values("nivel_rank", ascending=False)

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cidades monitoradas", len(map_df))
c2.metric("Alerta vermelho",      int((map_df["nivel_alerta"] == VERMELHO).sum()))
c3.metric("Alerta amarelo",       int((map_df["nivel_alerta"] == AMARELO).sum()))
c4.metric("Dentro do esperado",   int((map_df["nivel_alerta"] == VERDE).sum()))

st.divider()

# --- Mapa ---
fig = px.scatter_mapbox(
    map_df,
    lat="lat", lon="lon",
    color="nivel_alerta",
    size="casos_size",
    hover_name="municipio",
    hover_data={
        "casos": True, "z_score": ":.2f", "uf": True,
        "lat": False, "lon": False, "casos_size": False,
        "nivel_rank": False, "geocode": False,
    },
    color_discrete_map=COLOR_MAP,
    category_orders={"nivel_alerta": NIVEL_ORDER},
    mapbox_style="carto-positron",
    zoom=3.5,
    center={"lat": -14.5, "lon": -51.0},
    size_max=45,
    labels={"nivel_alerta": "Alerta", "casos": "Casos (ult. sem.)", "z_score": "Z-score", "uf": "UF"},
)
fig.update_layout(
    height=520,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="#ffffff",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b"),
    legend=dict(
        title="Nível de alerta", orientation="v",
        x=0.01, y=0.98,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#e2e8f0", borderwidth=1,
        font=dict(size=11),
    ),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Tabela ---
st.subheader("Ranking de alertas")
display = map_df[["municipio", "uf", "nivel_alerta", "casos", "z_score"]].copy()
display = display.sort_values("nivel_rank" if "nivel_rank" in map_df.columns else "casos", ascending=False)
display["nivel_alerta"] = display["nivel_alerta"].str.upper()
display["z_score"]      = display["z_score"].round(2)
display["casos"]        = display["casos"].astype(int)


def _row_style(row):
    nivel  = row["nivel_alerta"].lower()
    colors = {"vermelho": "#fff5f5", "amarelo": "#fffbf0", "verde": "#f0fff4"}
    bg     = colors.get(nivel, "#ffffff")
    return [f"background-color: {bg}"] * len(row)


st.dataframe(
    display.style.apply(_row_style, axis=1),
    use_container_width=True,
    hide_index=True,
)

footer("Mapa de Surtos")
