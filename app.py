"""datasus-outbreak-prediction: Sistema de vigilancia epidemiologica integrada."""

import streamlit as st
import pandas as pd
import plotly.express as px

from core.data.infodengue import fetch_city, series_for_forecast, DISEASES
from core.surtos.detector import classify_alert, summary_table, VERDE, AMARELO, VERMELHO, alert_color
from core.viz.theme import inject, footer, badge, module_card

st.set_page_config(
    page_title="datasus-outbreak-prediction",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Oculta sidebar completamente na home
st.markdown(
    "<style>[data-testid='stSidebar']{display:none!important}</style>",
    unsafe_allow_html=True,
)

inject(subtitle="Outbreak Prediction")

# --- Hero ---
badge("Plataforma de Vigilância Epidemiológica · Dados Públicos SUS")
st.markdown(
    "<h2 style='font-size:2rem;font-weight:700;color:#0f172a;line-height:1.2;margin:0 0 0.5rem 0'>"
    "Preveja surtos antes<br>que virem <span style='color:#009c3b;font-style:italic;"
    "font-family:Playfair Display,Georgia,serif'>crise</span>."
    "</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#64748b;font-size:1rem;margin:0 0 1.75rem 0'>"
    "Detecção de anomalias · Previsão LightGBM · Grafo MacroCID · Saneamento x doenças"
    "</p>",
    unsafe_allow_html=True,
)

# --- Cards de modulos ---
st.markdown(
    "<p style='font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;"
    "letter-spacing:0.1em;margin-bottom:0.75rem'>Módulos</p>",
    unsafe_allow_html=True,
)

MODULOS = [
    {
        "icon": "monitoring",
        "name": "Vigilância de Surtos",
        "desc": "Detecção de anomalias por z-score rolante e previsão de 4 semanas com LightGBM.",
        "source": "InfoDengue",
        "page": "pages/01_surtos.py",
        "label": "Abrir",
    },
    {
        "icon": "hub",
        "name": "Grafo MacroCID",
        "desc": "Rede de co-ocorrência entre grupos de CID-10 a partir do SIM/DATASUS.",
        "source": "SIM/DATASUS",
        "page": "pages/02_macrocid.py",
        "label": "Abrir",
    },
    {
        "icon": "inventory_2",
        "name": "Planejamento de Insumos",
        "desc": "Projeção de demanda por medicamentos baseada em casos previstos por município.",
        "source": "PCDT/MS",
        "page": "pages/03_insumos.py",
        "label": "Abrir",
    },
    {
        "icon": "water",
        "name": "Mapa Urbano",
        "desc": "Correlação Spearman entre cobertura de saneamento e incidência de doenças hídricas.",
        "source": "SNIS · IBGE",
        "page": "pages/04_mapa_urbano.py",
        "label": "Abrir",
    },
    {
        "icon": "pin_drop",
        "name": "Mapa de Surtos",
        "desc": "Distribuição geográfica dos alertas nas capitais e grandes municípios do Brasil.",
        "source": "InfoDengue",
        "page": "pages/05_mapa_surtos.py",
        "label": "Abrir",
    },
]

# Linha 1: 3 cards
row1 = st.columns(3, gap="medium")
for col, m in zip(row1, MODULOS[:3]):
    with col:
        module_card(m["icon"], m["name"], m["desc"], m["source"])
        st.markdown('<div class="sus-module-link">', unsafe_allow_html=True)
        st.page_link(m["page"], label=f"Acessar {m['name']} →")
        st.markdown("</div>", unsafe_allow_html=True)

# Linha 2: 2 cards centrados
_, c1, c2, _ = st.columns([0.5, 1, 1, 0.5], gap="medium")
for col, m in zip([c1, c2], MODULOS[3:]):
    with col:
        module_card(m["icon"], m["name"], m["desc"], m["source"])
        st.markdown('<div class="sus-module-link">', unsafe_allow_html=True)
        st.page_link(m["page"], label=f"Acessar {m['name']} →")
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- KPIs ao vivo ---
st.markdown(
    "<p style='font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;"
    "letter-spacing:0.1em;margin-bottom:0.75rem'>Alertas ao vivo · capitais selecionadas · dengue</p>",
    unsafe_allow_html=True,
)

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

with st.spinner("Carregando dados do InfoDengue..."):
    summaries = []
    for nome, gc in DEMO_CITIES.items():
        s = load_summary(gc, nome, "dengue", 2021, 2024)
        if not s.empty:
            summaries.append(s)

summary_df = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()

c1, c2, c3, c4 = st.columns(4)
with c1:
    n_vermelho = int((summary_df["nivel_alerta"] == VERMELHO).sum()) if not summary_df.empty else 0
    st.metric("Alerta vermelho", n_vermelho)
with c2:
    n_amarelo = int((summary_df["nivel_alerta"] == AMARELO).sum()) if not summary_df.empty else 0
    st.metric("Alerta amarelo", n_amarelo)
with c3:
    n_verde = int((summary_df["nivel_alerta"] == VERDE).sum()) if not summary_df.empty else 0
    st.metric("Dentro do esperado", n_verde)
with c4:
    total = int(summary_df["casos"].sum()) if not summary_df.empty and "casos" in summary_df.columns else 0
    st.metric("Casos ultima semana", f"{total:,}")

if not summary_df.empty:
    cols = [c for c in ["municipio", "ultima_semana", "casos", "casos_esperados", "z_score", "nivel_alerta"]
            if c in summary_df.columns]
    display = summary_df[cols].copy()
    display["nivel_alerta"] = display["nivel_alerta"].str.upper()

    def _highlight(row):
        nivel = row.get("nivel_alerta", "VERDE").lower()
        c = alert_color(nivel)
        return [f"background-color: {c}22"] * len(row)

    st.dataframe(display.style.apply(_highlight, axis=1), use_container_width=True, hide_index=True)

    fig = px.bar(
        summary_df.sort_values("z_score", ascending=False),
        x="municipio", y="z_score",
        color="nivel_alerta",
        color_discrete_map={VERDE: "#2ecc71", AMARELO: "#f39c12", VERMELHO: "#e74c3c"},
        labels={"z_score": "Z-score", "municipio": "", "nivel_alerta": "Alerta"},
    )
    fig.add_hline(y=1.5, line_dash="dash", line_color="#f39c12", annotation_text="Amarelo")
    fig.add_hline(y=3.0, line_dash="dash", line_color="#e74c3c", annotation_text="Vermelho")
    fig.update_layout(
        height=320,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b"),
        margin=dict(l=10, r=10, t=20, b=40),
        legend=dict(orientation="h", y=-0.3),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum dado disponível. Verifique a conexão com o InfoDengue.")

st.divider()

with st.expander("Sobre o sistema"):
    st.markdown("""
**datasus-outbreak-prediction** conecta dados epidemiológicos e infraestrutura urbana para
antecipar surtos e apoiar planejamento em saúde pública.

**Fontes:** InfoDengue · SIM/DATASUS · SNIS · IBGE

**Módulos:** Vigilância de surtos · Grafo MacroCID · Planejamento de insumos · Mapa urbano · Mapa de surtos

**Limitações:** Módulo de insumos projeta demanda estimada (sem dados de estoque real).
Dados SNIS com atraso de 1-2 anos. Demo restrito a capitais.
    """)

footer("V1.0")
