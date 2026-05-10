"""Pagina 1: Vigilancia de Surtos.

Detecta anomalias em series temporais de arboviroses e exibe previsao 4 semanas.
Dados: InfoDengue por municipio e semana epidemiologica.
"""

import streamlit as st
import pandas as pd

from core.data.infodengue import fetch_city, fetch_state, DISEASES
from core.surtos.detector import classify_alert, summary_table, alert_color, VERMELHO, AMARELO
from core.surtos.forecaster import forecast_with_history
from core.viz.timeseries import plot_series_with_forecast, plot_alert_table_bar
from core.viz.theme import inject, footer, badge, sidebar_back

st.set_page_config(page_title="Surtos · datasus-outbreak-prediction", page_icon="🦠", layout="wide")
inject(subtitle="Vigilância de Surtos")
badge("Detecção de Anomalias · Previsão 4 Semanas · InfoDengue")

# Municipios de demo (geocodigos IBGE de capitais)
DEMO_CITIES = {
    "Rio de Janeiro (RJ)": "3304557",
    "Sao Paulo (SP)": "3550308",
    "Belo Horizonte (MG)": "3106200",
    "Salvador (BA)": "2927408",
    "Fortaleza (CE)": "2304400",
    "Manaus (AM)": "1302603",
    "Recife (PE)": "2611606",
    "Porto Alegre (RS)": "4314902",
}

# --- Sidebar ---
with st.sidebar:
    sidebar_back()
    st.header("Filtros")
    doenca = st.selectbox("Doença", DISEASES, index=0)
    ano_inicio = st.slider("Ano de início", 2019, 2024, 2020)
    ano_fim = st.slider("Ano de fim", 2020, 2024, 2024)
    cidades_sel = st.multiselect(
        "Municípios (demo)",
        list(DEMO_CITIES.keys()),
        default=["Rio de Janeiro (RJ)", "Sao Paulo (SP)", "Fortaleza (CE)"],
    )

# --- Carregar dados ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(geocode: str, doenca: str, y0: int, y1: int) -> pd.DataFrame:
    return fetch_city(geocode, doenca, y0, y1)

if not cidades_sel:
    st.warning("Selecione ao menos um município na barra lateral.")
    st.stop()

with st.spinner("Carregando dados do InfoDengue..."):
    all_summaries = []
    city_data = {}

    for nome in cidades_sel:
        gc = DEMO_CITIES[nome]
        df = load_data(gc, doenca, ano_inicio, ano_fim)
        if df.empty:
            continue

        from core.data.infodengue import series_for_forecast
        series = series_for_forecast(df)
        if len(series) < 26:
            continue

        alert_df = classify_alert(series)
        alert_df = alert_df.join(pd.Series(df.set_index("data_iniSE")["nivel"].reindex(alert_df.index), name="nivel_infodengue"), how="left")
        summ = summary_table(alert_df, municipio=nome, doenca=doenca)
        all_summaries.append(summ)
        city_data[nome] = {"series": series, "alert_df": alert_df}

summary_df = pd.concat(all_summaries, ignore_index=True) if all_summaries else pd.DataFrame()

# --- KPIs ---
col1, col2, col3 = st.columns(3)
with col1:
    n_vermelho = int((summary_df["nivel_alerta"] == VERMELHO).sum()) if not summary_df.empty else 0
    st.metric("Municípios em alerta vermelho", n_vermelho)
with col2:
    n_amarelo = int((summary_df["nivel_alerta"] == AMARELO).sum()) if not summary_df.empty else 0
    st.metric("Municípios em alerta amarelo", n_amarelo)
with col3:
    total_casos = int(summary_df["casos"].sum()) if not summary_df.empty and "casos" in summary_df.columns else 0
    st.metric("Total de casos na última semana", f"{total_casos:,}")

st.divider()

# --- Tabela de alertas ---
st.subheader("Resumo de alertas por município")
if not summary_df.empty:
    def _color_row(row):
        c = alert_color(row.get("nivel_alerta", "verde"))
        return [f"background-color: {c}20"] * len(row)

    cols_show = [c for c in ["municipio", "doenca", "ultima_semana", "casos", "casos_esperados", "z_score", "nivel_alerta"] if c in summary_df.columns]
    styled = summary_df[cols_show].style.apply(_color_row, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.plotly_chart(plot_alert_table_bar(summary_df), use_container_width=True)
else:
    st.info("Nenhum dado de alerta disponível para os municípios e período selecionados.")

st.divider()

# --- Serie temporal + previsao ---
st.subheader("Série temporal e previsão (4 semanas)")

if city_data:
    municipio_sel = st.selectbox("Selecione um município", list(city_data.keys()))
    series = city_data[municipio_sel]["series"]
    alert_df = city_data[municipio_sel]["alert_df"]

    with st.spinner("Calculando previsão..."):
        hist_pred = forecast_with_history(series, horizon=4)

        if "nivel_alerta" in alert_df.columns:
            alert_map = alert_df["nivel_alerta"].to_dict()
            hist_pred["nivel_alerta"] = hist_pred["data"].map(alert_map).fillna("verde")

    fig = plot_series_with_forecast(hist_pred, municipio=municipio_sel, doenca=doenca)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver dados brutos"):
        st.dataframe(hist_pred, use_container_width=True)
else:
    st.info("Nenhuma série disponível. Verifique a conexão com o InfoDengue.")

footer("Surtos")
