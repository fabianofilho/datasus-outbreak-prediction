"""Pagina 2: Grafo MacroCID.

Visualiza rede de co-ocorrencia entre grupos de CIDs a partir do SIM/DATASUS.
"""

import streamlit as st
import pandas as pd

from core.data import downloader
from core.data import sim as sim_mod
from core.macrocid.groups import all_group_names, label_of, color_of, add_macrocid_column
from core.macrocid.builder import build_graph, prune_graph, graph_summary
from core.macrocid.cooccurrence import build_cooccurrence, normalized_cooccurrence
from core.viz.plotly_graph import force_directed_plot, heatmap_plot
from core.viz.theme import inject, footer, badge, sidebar_back

st.set_page_config(page_title="MacroCID · datasus-outbreak-prediction", page_icon="🦠", layout="wide")
inject(subtitle="Grafo MacroCID")
badge("Rede de Co-ocorrência CID-10 · SIM/DATASUS")

STATES = ["RJ", "SP", "MG", "BA", "CE", "PE", "RS", "PR", "GO", "AM"]

with st.sidebar:
    sidebar_back()
    st.header("Filtros")
    state = st.selectbox("Estado", STATES, index=0)
    year = st.selectbox("Ano", list(range(2018, 2024)), index=4)
    min_weight = st.slider("Peso minimo de aresta", 1, 50, 5)
    top_n = st.slider("Top N nos", 20, 200, 80)
    normalize_heatmap = st.checkbox("Normalizar heatmap", value=False)
    highlight = st.text_input("Destacar CID (ex: I21)", value="").upper().strip()

@st.cache_data(ttl=7200, show_spinner=False)
def load_graph_data(state: str, year: int):
    try:
        raw = downloader.fetch(state, year)
        df = sim_mod.preprocess(raw)
        edges = sim_mod.extract_causal_chains(df)
        return df, edges
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

with st.spinner(f"Carregando SIM {state} {year}..."):
    sim_df, edges_df = load_graph_data(state, year)

if edges_df.empty:
    st.warning(f"Não foi possível carregar dados do SIM para {state} {year}. Verifique sua conexão ou tente outro estado/ano.")
    st.stop()

G_full = build_graph(edges_df)
G = prune_graph(G_full, min_weight=min_weight, top_n=top_n)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Grafo CID-CID", "Heatmap MacroCID", "Top CIDs"])

with tab1:
    stats = graph_summary(G)
    c1, c2, c3 = st.columns(3)
    c1.metric("Nós (CIDs)", stats["nodes"])
    c2.metric("Arestas", stats["edges"])
    c3.metric("Peso total", f"{stats.get('total_weight', 0):,}")

    fig = force_directed_plot(G, title=f"Rede CID-10 - {state} {year}", highlight_node=highlight or None)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    with st.spinner("Calculando co-ocorrências por MacroCID..."):
        add_macrocid_column(sim_df, cid_col="CAUSABAS" if "CAUSABAS" in sim_df.columns else sim_df.columns[0])
        matrix = build_cooccurrence(sim_df)

    if normalize_heatmap:
        matrix = normalized_cooccurrence(matrix)

    import plotly.express as px
    import numpy as np

    labels = [f"{g}\n{label_of(g)}" for g in matrix.index]
    z = matrix.values.astype(float)
    if not normalize_heatmap:
        z = np.log1p(z)

    fig2 = px.imshow(
        z,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        color_continuous_scale="Blues",
        title="Co-ocorrência entre MacroCIDs" + (" (normalizada)" if normalize_heatmap else " (log)"),
        labels={"color": "proporção" if normalize_heatmap else "log(casos)"},
    )
    fig2.update_layout(height=600, margin=dict(l=150, r=20, t=50, b=150))
    fig2.update_xaxes(tickangle=45)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    from core.viz.plotly_graph import top_cids_bar
    fig3 = top_cids_bar(G, top_n=30)
    st.plotly_chart(fig3, use_container_width=True)

    if stats.get("top_20"):
        top_df = pd.DataFrame(stats["top_20"])
        st.dataframe(top_df, use_container_width=True, hide_index=True)

footer("MacroCID")
