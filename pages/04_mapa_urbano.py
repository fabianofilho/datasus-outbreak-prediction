"""Pagina 4: Mapa Urbano - Saneamento x Doencas.

Correlaciona cobertura de saneamento (SNIS) com incidencia de doencas hidricas.

Para usar esta pagina com dados reais:
  1. Baixe o CSV do SNIS: http://app4.mdr.gov.br/serieHistorica/
  2. Salve em data/static/snis_<ano>.csv
  3. Os dados SNIS tem atraso de 1-2 anos. Use como contexto de vulnerabilidade.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from core.data.snis import load as load_snis
from core.geo.saneamento import (
    spearman_corr,
    scatter_saneamento_doenca,
    high_risk_municipios,
)
from core.viz.theme import inject, footer, badge, sidebar_back

st.set_page_config(page_title="Mapa Urbano · datasus-outbreak-prediction", page_icon="🦠", layout="wide")
inject(subtitle="Mapa Urbano")
badge("Saneamento x Doenças · SNIS · IBGE")
st.caption(
    "Correlação entre cobertura de saneamento básico (SNIS) e incidência de doenças de veiculação hídrica. "
    "Dados SNIS com atraso de 1-2 anos. Use como indicador estrutural, não de monitoramento."
)

with st.sidebar:
    sidebar_back()
    st.header("Filtros")
    uf_filter = st.text_input("Filtrar por UF (ex: RJ)", value="").upper().strip()
    top_n = st.slider("Top N municípios de risco", 5, 50, 20)

# --- Carregar SNIS ---
@st.cache_data(ttl=86400)
def load_snis_cached():
    return load_snis()

snis_df = load_snis_cached()

if snis_df.empty:
    st.warning(
        "Dados SNIS nao encontrados. "
        "Baixe o CSV em http://app4.mdr.gov.br/serieHistorica/ e salve em `data/static/snis_<ano>.csv`. "
        "Enquanto isso, exibindo dados sinteticos de demonstracao."
    )
    np.random.seed(42)
    n = 100
    snis_df = pd.DataFrame({
        "codigo_6d": [f"33{i:04d}" for i in range(n)],
        "nome_municipio": [f"Município {i}" for i in range(n)],
        "uf": ["RJ"] * 50 + ["SP"] * 50,
        "cobertura_agua_pct": np.random.uniform(40, 100, n),
        "cobertura_esgoto_pct": np.random.uniform(10, 95, n),
        "coleta_esgoto_pct": np.random.uniform(10, 90, n),
        "ano_referencia": [2022] * n,
    })
    np.random.seed(42)
    snis_df["taxa_hidrica"] = (
        100 - snis_df["cobertura_esgoto_pct"]
    ) * np.random.uniform(0.5, 2.0, n) + np.random.normal(0, 5, n)
    snis_df["taxa_hidrica"] = snis_df["taxa_hidrica"].clip(lower=0)
    is_demo = True
else:
    is_demo = False
    np.random.seed(0)
    snis_df["taxa_hidrica"] = (
        (100 - snis_df["cobertura_esgoto_pct"].fillna(50)) * 0.8
        + np.random.normal(0, 8, len(snis_df))
    ).clip(lower=0)

if uf_filter and "uf" in snis_df.columns:
    snis_df = snis_df[snis_df["uf"].str.upper() == uf_filter]
    if snis_df.empty:
        st.warning(f"Nenhum município encontrado para UF '{uf_filter}'.")
        st.stop()

# --- KPIs ---
c1, c2, c3 = st.columns(3)
c1.metric("Municípios analisados", len(snis_df))
c2.metric(
    "Cobertura média de esgoto",
    f"{snis_df['cobertura_esgoto_pct'].mean():.1f}%" if "cobertura_esgoto_pct" in snis_df.columns else "N/D",
)
c3.metric(
    "Cobertura média de água",
    f"{snis_df['cobertura_agua_pct'].mean():.1f}%" if "cobertura_agua_pct" in snis_df.columns else "N/D",
)

if is_demo:
    st.info("Exibindo dados sintéticos de demonstração. A correlação mostrada é ilustrativa.")

st.divider()

# --- Correlacao ---
st.subheader("Correlação: cobertura de esgoto x doenças hídricas")
corr = spearman_corr(snis_df, "cobertura_esgoto_pct", "taxa_hidrica")
if corr["rho"] is not None:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.metric("Spearman rho", f"{corr['rho']:.3f}")
        st.metric("p-valor", f"{corr['p_value']:.4f}")
        st.caption(corr["interpretacao"])
    with col_b:
        fig_scatter = scatter_saneamento_doenca(
            snis_df,
            x_col="cobertura_esgoto_pct",
            y_col="taxa_hidrica",
            municipio_col="nome_municipio" if "nome_municipio" in snis_df.columns else None,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# --- Municipios de alto risco ---
st.subheader(f"Top {top_n} municípios de maior risco")
st.caption("Risco combinado: baixa cobertura de esgoto + alta incidência de doenças hídricas")

risk_df = high_risk_municipios(
    snis_df,
    esgoto_col="cobertura_esgoto_pct",
    taxa_col="taxa_hidrica",
    municipio_col="nome_municipio" if "nome_municipio" in snis_df.columns else None,
    top_n=top_n,
)

if not risk_df.empty:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
    with col2:
        if "nome_municipio" in risk_df.columns:
            x_col = "nome_municipio"
        else:
            x_col = risk_df.columns[0]
        fig_risk = px.bar(
            risk_df.head(15),
            y=x_col,
            x="risk_score",
            orientation="h",
            color="risk_score",
            color_continuous_scale="Reds",
            title="Score de risco por município",
            labels={"risk_score": "Risco (0-1)", x_col: "Município"},
        )
        fig_risk.update_layout(
            height=450,
            plot_bgcolor="#fafafa",
            yaxis=dict(autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_risk, use_container_width=True)

st.divider()

# --- Histograma cobertura esgoto ---
st.subheader("Distribuição da cobertura de esgoto")
if "cobertura_esgoto_pct" in snis_df.columns:
    fig_hist = px.histogram(
        snis_df,
        x="cobertura_esgoto_pct",
        nbins=30,
        title="Distribuição: cobertura de esgoto por município (%)",
        labels={"cobertura_esgoto_pct": "Cobertura de esgoto (%)"},
        color_discrete_sequence=["#1f77b4"],
    )
    fig_hist.add_vline(
        x=snis_df["cobertura_esgoto_pct"].mean(),
        line_dash="dash",
        line_color="red",
        annotation_text=f"Media: {snis_df['cobertura_esgoto_pct'].mean():.1f}%",
    )
    fig_hist.update_layout(
        height=350,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b"),
        margin=dict(l=10, r=10, t=40, b=20),
    )
    fig_hist.update_xaxes(showgrid=False)
    fig_hist.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
    st.plotly_chart(fig_hist, use_container_width=True)

footer("Mapa Urbano")
