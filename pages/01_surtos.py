"""Pagina 1: Vigilancia de Surtos.

Detecta anomalias em series temporais e exibe previsao de 4 semanas.
Dados: InfoDengue (arboviroses) ou gerador sintetico SINAN (demais doencas).
"""

import streamlit as st
import pandas as pd

from core.data.infodengue import fetch_city, DISEASE_LABELS
from core.data.infodengue import series_for_forecast
from core.data.municipios import load as load_municipios, display_options, default_capitals
from core.surtos.detector import classify_alert, summary_table, alert_color, VERMELHO, AMARELO
from core.surtos.forecaster import forecast_with_history
from core.viz.timeseries import plot_series_with_forecast, plot_alert_table_bar
from core.viz.theme import inject, footer, badge, sidebar_back, empty_state

st.set_page_config(
    page_title="Surtos · datasus-outbreak-prediction",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject(subtitle="Vigilância de Surtos")
badge("Detecção de Anomalias · Previsão 4 Semanas · InfoDengue")


@st.cache_data(ttl=86400, show_spinner=False)
def get_municipio_options() -> dict[str, str]:
    return display_options(load_municipios())


# --- Sidebar ---
with st.sidebar:
    sidebar_back()
    st.header("Configuração")

    doenca = st.selectbox(
        "Doença",
        options=list(DISEASE_LABELS.keys()),
        format_func=lambda d: DISEASE_LABELS[d],
        index=0,
    )
    _sintetico = doenca not in {"dengue", "chikungunya", "zika"}
    if _sintetico:
        st.caption("Dados simulados com sazonalidade epidemiológica. SINAN sem API pública.")

    ano_inicio = st.slider("Ano de início", 2019, 2024, 2020)
    ano_fim = st.slider("Ano de fim", 2020, 2024, 2024)

    st.divider()
    st.subheader("Municípios")
    st.caption("Digite nome ou UF para filtrar os 5.570 municípios brasileiros.")

    mun_opts = get_municipio_options()
    caps_default = [k for k in default_capitals() if k in mun_opts]

    cidades_sel = st.multiselect(
        "Selecionar municípios",
        options=list(mun_opts.keys()),
        default=caps_default[:3],
        placeholder="Ex: São Paulo (SP)",
    )

    st.divider()
    analisar = st.button("Analisar", type="primary", use_container_width=True)

# --- Estado inicial ---
if analisar:
    st.session_state["surtos_ok"] = True
    st.session_state["surtos_cfg"] = {
        "cidades": cidades_sel,
        "doenca": doenca,
        "ano_inicio": ano_inicio,
        "ano_fim": ano_fim,
    }

if not st.session_state.get("surtos_ok"):
    empty_state(
        "Configure os filtros e clique em Analisar",
        "Selecione municípios, doença e período na barra lateral para iniciar a análise de surtos.",
    )
    footer("Surtos")
    st.stop()

cfg = st.session_state["surtos_cfg"]
cidades_sel = cfg["cidades"]
doenca = cfg["doenca"]
ano_inicio = cfg["ano_inicio"]
ano_fim = cfg["ano_fim"]

if not cidades_sel:
    st.warning("Selecione ao menos um município na barra lateral e clique em Analisar.")
    footer("Surtos")
    st.stop()


# --- Carregar dados ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(geocode: str, doenca: str, y0: int, y1: int) -> pd.DataFrame:
    return fetch_city(geocode, doenca, y0, y1)


with st.spinner("Carregando dados..."):
    all_summaries = []
    city_data = {}

    for nome in cidades_sel:
        gc = mun_opts.get(nome)
        if not gc:
            continue
        df = load_data(gc, doenca, ano_inicio, ano_fim)
        if df.empty:
            continue
        series = series_for_forecast(df)
        if len(series) < 26:
            continue
        alert_df = classify_alert(series)
        alert_df = alert_df.join(
            pd.Series(df.set_index("data_iniSE")["nivel"].reindex(alert_df.index), name="nivel_infodengue"),
            how="left",
        )
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
    st.metric("Total de casos (última semana)", f"{total_casos:,}")

st.divider()

# --- Tabs: alertas + serie temporal ---
tab1, tab2 = st.tabs(["Resumo de alertas", "Série temporal e previsão"])

with tab1:
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

with tab2:
    if city_data:
        municipio_sel = st.selectbox("Município", list(city_data.keys()))
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
