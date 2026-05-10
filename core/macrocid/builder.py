"""Build weighted directed graphs from causal chain edges."""

from __future__ import annotations

import networkx as nx
import pandas as pd

from core.macrocid.catalog import chapter_color, chapter_label, chapter_letter, code_display


def build_graph(edges_df: pd.DataFrame) -> nx.DiGraph:
    """Build a weighted DiGraph from causal chain edges.

    Parameters
    ----------
    edges_df : DataFrame with columns [source, target, ...].
        Each row is one edge occurrence. Duplicate (source, target) pairs
        are aggregated into edge weight.

    Returns
    -------
    nx.DiGraph with node attributes (chapter, label, color, count, display)
    and edge attribute (weight).
    """
    G = nx.DiGraph()

    if edges_df.empty:
        return G

    # Aggregate edge weights
    weight_df = (
        edges_df.groupby(["source", "target"])
        .size()
        .reset_index(name="weight")
    )

    for _, row in weight_df.iterrows():
        G.add_edge(row["source"], row["target"], weight=int(row["weight"]))

    # Node counts (total appearances as source or target)
    src_counts = edges_df["source"].value_counts()
    tgt_counts = edges_df["target"].value_counts()
    all_counts = src_counts.add(tgt_counts, fill_value=0).astype(int)

    for node in G.nodes():
        G.nodes[node]["chapter"] = chapter_letter(node)
        G.nodes[node]["label"] = chapter_label(node)
        G.nodes[node]["color"] = chapter_color(node)
        G.nodes[node]["count"] = int(all_counts.get(node, 0))
        G.nodes[node]["display"] = code_display(node)

    return G


def prune_graph(
    G: nx.DiGraph,
    min_weight: int = 1,
    top_n: int | None = None,
) -> nx.DiGraph:
    """Remove low-weight edges and keep only top_n nodes by degree.

    Parameters
    ----------
    min_weight : minimum edge weight to keep.
    top_n : if set, keep only the top_n nodes by weighted degree.
    """
    H = G.copy()

    # Remove edges below threshold
    if min_weight > 1:
        remove = [(u, v) for u, v, d in H.edges(data=True) if d.get("weight", 0) < min_weight]
        H.remove_edges_from(remove)

    # Remove isolated nodes after edge pruning
    isolates = list(nx.isolates(H))
    H.remove_nodes_from(isolates)

    # Keep top_n nodes by weighted degree
    if top_n and len(H) > top_n:
        deg = dict(H.degree(weight="weight"))
        top_nodes = sorted(deg, key=deg.get, reverse=True)[:top_n]
        H = H.subgraph(top_nodes).copy()

    return H


def graph_summary(G: nx.DiGraph) -> dict:
    """Compute summary statistics for a graph."""
    if len(G) == 0:
        return {"nodes": 0, "edges": 0}

    n = G.number_of_nodes()
    m = G.number_of_edges()
    total_weight = sum(d["weight"] for _, _, d in G.edges(data=True))

    deg = dict(G.degree(weight="weight"))
    avg_degree = sum(deg.values()) / n if n > 0 else 0
    density = m / (n * (n - 1)) if n > 1 else 0

    # Weakly connected components
    components = nx.number_weakly_connected_components(G)

    # Betweenness centrality (unweighted for speed on large graphs)
    betweenness = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G, weight="weight")

    top_nodes_deg = sorted(deg, key=deg.get, reverse=True)[:20]
    top_node_betw = max(betweenness, key=betweenness.get)

    return {
        "nodes": n,
        "edges": m,
        "total_weight": total_weight,
        "density": density,
        "avg_degree": avg_degree,
        "components": components,
        "top_betweenness": {
            "code": top_node_betw,
            "display": code_display(top_node_betw),
            "label": chapter_label(top_node_betw),
            "value": betweenness[top_node_betw],
        },
        "top_20": [
            {
                "code": node,
                "display": code_display(node),
                "label": chapter_label(node),
                "degree": deg[node],
                "betweenness": round(betweenness.get(node, 0), 4),
                "pagerank": round(pagerank.get(node, 0), 4),
            }
            for node in top_nodes_deg
        ],
    }


def ego_graph(G: nx.DiGraph, node: str, radius: int = 1) -> nx.DiGraph:
    """Extract ego graph centered on a specific ICD code."""
    if node not in G:
        return nx.DiGraph()
    return nx.ego_graph(G, node, radius=radius)
