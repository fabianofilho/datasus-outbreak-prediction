"""Pagina 3: Planejamento de Insumos.

Projeta demanda de medicamentos e insumos a partir de previsoes de casos.

AVISO: Projeta DEMANDA estimada. Nao ha dados de estoque do SUS em tempo real.
"""

import streamlit as st
import pandas as pd

from core.data.infodengue import fetch_city, series_for_forecast, DISEASES, DISEASE_LABELS, DISEASE_CID
from core.surtos.forecaster import forecast
from core.insumos.mapping import all_insumos, cids_with_mapping
from core.insumos.demand import project_demand, project_by_municipio
from core.viz.theme import inject, footer, badge, sidebar_back

st.set_page_config(page_title="Insumos · datasus-outbreak-prediction", page_icon="🦠", layout="wide", initial_sidebar_state="expanded")
inject(subtitle="Planejamento de Insumos")
badge("Projeção de Demanda · PCDT/MS · Estimativa")
st.markdown(
    "<div style='background:#f0f7ff;border-left:4px solid #0047bb;border-radius:0 8px 8px 0;"
    "padding:0.75rem 1rem;font-size:0.875rem;color:#1e293b;margin-bottom:1rem'>"
    "Demanda estimada com base em previsões epidemiológicas. "
    "Não há dados de estoque em tempo real no SUS público."
    "</div>",
    unsafe_allow_html=True,
)

DEMO_CITIES_GEO = {
    "Rio de Janeiro (RJ)": "3304557",
    "Sao Paulo (SP)": "3550308",
    "Belo Horizonte (MG)": "3106200",
    "Fortaleza (CE)": "2304400",
    "Manaus (AM)": "1302603",
}

with st.sidebar:
    sidebar_back()
    st.header("Configuração")
    doenca = st.selectbox(
        "Doença",
        options=list(DISEASE_LABELS.keys()),
        format_func=lambda d: DISEASE_LABELS[d],
        index=0,
    )
    horizon = st.slider("Horizonte de planejamento (semanas)", 1, 12, 4)
    cidades_sel = st.multiselect(
        "Municípios",
        list(DEMO_CITIES_GEO.keys()),
        default=list(DEMO_CITIES_GEO.keys())[:3],
    )

@st.cache_data(ttl=3600, show_spinner=False)
def get_forecast(geocode: str, cid: str, doenca: str, horizon: int) -> dict:
    df = fetch_city(geocode, doenca, 2020, 2024)
    if df.empty:
        return {"cid": cid, "casos_semana": 0}
    series = series_for_forecast(df)
    pred = forecast(series, horizon=horizon)
    if pred.empty:
        casos = float(series.tail(4).mean()) if len(series) >= 4 else 0
    else:
        casos = float(pred["previsao"].mean())
    return {"cid": cid, "casos_semana": casos}

if not cidades_sel:
    st.warning("Selecione ao menos um município.")
    st.stop()

with st.spinner("Calculando previsões e demanda..."):
    cid = DISEASE_CID.get(doenca, "A90")
    rows = []
    for nome in cidades_sel:
        geocode = DEMO_CITIES_GEO[nome]
        result = get_forecast(geocode, cid, doenca, horizon)
        rows.append({"municipio": nome, "cid": cid, "casos_semana": result["casos_semana"]})

    forecast_df = pd.DataFrame(rows)

    if forecast_df.empty or forecast_df["casos_semana"].sum() == 0:
        st.warning("Sem previsões disponíveis. Verifique os dados.")
        st.stop()

    demand_df = project_by_municipio(
        forecast_df,
        municipio_col="municipio",
        cid_col="cid",
        casos_col="casos_semana",
        horizon_weeks=horizon,
    )

# --- Visao geral ---
st.subheader(f"Demanda projetada para {horizon} semanas")

col1, col2 = st.columns([2, 1])
with col1:
    if not demand_df.empty:
        st.dataframe(
            demand_df.sort_values("demanda_total", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
        csv = demand_df.to_csv(index=False).encode("utf-8")
        st.download_button("Exportar CSV", csv, file_name=f"demanda_insumos_{horizon}sem.csv", mime="text/csv")
    else:
        st.info("Sem demanda calculada.")

with col2:
    st.subheader("Previsão de casos")
    st.dataframe(
        forecast_df.rename(columns={"casos_semana": "casos/semana (média)"}),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# --- Grafico por municipio ---
if not demand_df.empty:
    st.subheader("Top insumos por município")
    municipio_vis = st.selectbox("Município", demand_df["municipio"].unique())
    sub = demand_df[demand_df["municipio"] == municipio_vis].head(15)

    import plotly.express as px
    fig = px.bar(
        sub,
        y="insumo",
        x="demanda_total",
        orientation="h",
        color="unidade",
        title=f"Demanda projetada - {municipio_vis} ({horizon} semanas)",
        labels={"demanda_total": "Unidades", "insumo": "Insumo"},
    )
    fig.update_layout(
        height=400,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=40, b=20),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

footer("Insumos")
