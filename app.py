"""epidemio-urbano: Sistema de vigilancia epidemiologica integrada.

Home: KPIs nacionais e mapa resumo de alertas.
"""

import streamlit as st
import pandas as pd

from core.data.infodengue import fetch_city, series_for_forecast, DISEASES
from core.surtos.detector import classify_alert, summary_table, VERDE, AMARELO, VERMELHO, alert_color

st.set_page_config(
    page_title="epidemio-urbano",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ---
st.title("epidemio-urbano")
st.caption(
    "Sistema de vigilancia epidemiologica integrada. "
    "Detecta surtos, preve demanda por insumos e correlaciona doencas com saneamento urbano."
)

# --- Sidebar ---
with st.sidebar:
    st.header("Configuracao global")
    doenca = st.selectbox("Doenca", DISEASES, index=0)
    ano_inicio = st.slider("Ano de inicio", 2019, 2024, 2021)
    ano_fim = st.slider("Ano de fim", 2020, 2024, 2024)
    st.divider()
    st.markdown("**Navegacao**")
    st.page_link("pages/01_surtos.py", label="Vigilancia de Surtos")
    st.page_link("pages/02_macrocid.py", label="Grafo MacroCID")
    st.page_link("pages/03_insumos.py", label="Planejamento de Insumos")
    st.page_link("pages/04_mapa_urbano.py", label="Mapa Urbano")

# --- Demo: capitais selecionadas ---
DEMO_CITIES = {
    "Rio de Janeiro": "3304557",
    "Sao Paulo": "3550308",
    "Fortaleza": "2304400",
    "Manaus": "1302603",
    "Salvador": "2927408",
    "Recife": "2611606",
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_summary(geocode: str, nome: str, doenca: str, y0: int, y1: int) -> pd.DataFrame:
    df = fetch_city(geocode, doenca, y0, y1)
    if df.empty:
        return pd.DataFrame()
    series = series_for_forecast(df)
    if len(series) < 26:
        return pd.DataFrame()
    alert_df = classify_alert(series)
    return summary_table(alert_df, municipio=nome, doenca=doenca)

with st.spinner("Carregando dados de vigilancia..."):
    summaries = []
    for nome, gc in DEMO_CITIES.items():
        s = load_summary(gc, nome, doenca, ano_inicio, ano_fim)
        if not s.empty:
            summaries.append(s)

summary_df = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()

# --- KPIs ---
st.subheader("Visao geral do monitoramento")
c1, c2, c3, c4 = st.columns(4)
with c1:
    n_vermelho = int((summary_df["nivel_alerta"] == VERMELHO).sum()) if not summary_df.empty else 0
    st.metric("Municipios: alerta vermelho", n_vermelho)
with c2:
    n_amarelo = int((summary_df["nivel_alerta"] == AMARELO).sum()) if not summary_df.empty else 0
    st.metric("Municipios: alerta amarelo", n_amarelo)
with c3:
    n_verde = int((summary_df["nivel_alerta"] == VERDE).sum()) if not summary_df.empty else 0
    st.metric("Municipios: dentro do esperado", n_verde)
with c4:
    total_casos = int(summary_df["casos"].sum()) if not summary_df.empty and "casos" in summary_df.columns else 0
    st.metric("Casos na ultima semana", f"{total_casos:,}")

st.divider()

# --- Tabela de resumo ---
st.subheader(f"Resumo de alertas: {doenca} ({ano_inicio}-{ano_fim})")
st.caption(f"Capitais monitoradas: {', '.join(DEMO_CITIES.keys())}")

if not summary_df.empty:
    cols = [c for c in ["municipio", "ultima_semana", "casos", "casos_esperados", "z_score", "nivel_alerta"] if c in summary_df.columns]
    summary_display = summary_df[cols].copy()
    summary_display["nivel_alerta"] = summary_display["nivel_alerta"].str.upper()

    def _highlight(row):
        nivel = row.get("nivel_alerta", "VERDE").lower()
        c = alert_color(nivel)
        return [f"background-color: {c}30"] * len(row)

    st.dataframe(
        summary_display.style.apply(_highlight, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # Grafico de barras por cidade
    import plotly.express as px
    fig = px.bar(
        summary_df.sort_values("z_score", ascending=False),
        x="municipio",
        y="z_score",
        color="nivel_alerta",
        color_discrete_map={VERDE: "#2ecc71", AMARELO: "#f39c12", VERMELHO: "#e74c3c"},
        title="Z-score por municipio (desvio da media historica)",
        labels={"z_score": "Z-score", "municipio": "Municipio", "nivel_alerta": "Alerta"},
    )
    fig.add_hline(y=1.5, line_dash="dash", line_color="#f39c12", annotation_text="Limiar amarelo")
    fig.add_hline(y=3.0, line_dash="dash", line_color="#e74c3c", annotation_text="Limiar vermelho")
    fig.update_layout(height=400, plot_bgcolor="#fafafa")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum dado de alerta disponivel. Verifique a conexao com o InfoDengue.")

st.divider()

# --- Sobre o sistema ---
with st.expander("Sobre este sistema"):
    st.markdown("""
**epidemio-urbano** e um sistema de vigilancia epidemiologica integrada com dados publicos do SUS.

**Fontes de dados:**
- SIM/DATASUS: mortalidade por CID-10 e municipio
- InfoDengue: casos semanais de dengue, chikungunya e zika
- SNIS: cobertura de saneamento basico por municipio
- IBGE: dados demograficos e shapefile de municipios

**Modulos:**
- Vigilancia de surtos: z-score rolling + CUSUM + previsao LightGBM (4 semanas)
- Grafo MacroCID: rede de co-ocorrencia entre grupos de CIDs
- Planejamento de insumos: projecao de demanda por medicamentos
- Mapa urbano: correlacao saneamento x incidencia de doencas hidricas

**Limitacoes:**
- O modulo de insumos projeta demanda estimada, nao estoque atual.
- Dados SNIS tem atraso de 1-2 anos.
- Demo limitado a capitais brasileiras. Para analise completa, use scripts/download_all.py.
    """)
