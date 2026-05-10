"""Interactive graph visualizations using Plotly."""

from __future__ import annotations

import math

import numpy as np
import networkx as nx
import plotly.graph_objects as go

from core.macrocid.catalog import chapter_color, chapter_label, code_display, CHAPTERS


def force_directed_plot(
    G: nx.DiGraph,
    width: int = 1000,
    height: int = 800,
    title: str = "",
    highlight_node: str | None = None,
) -> go.Figure:
    """Create an interactive force-directed graph plot.

    Uses NetworkX spring layout for positioning and Plotly Scattergl
    for WebGL-accelerated rendering of large graphs.

    Parameters
    ----------
    highlight_node : if set, dims all nodes except this one and its neighbors.
    """
    if len(G) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado para exibir", showarrow=False)
        return fig

    pos = nx.spring_layout(G, k=1.5 / math.sqrt(len(G)), iterations=50, seed=42)

    # Highlight set
    if highlight_node and highlight_node in G:
        hl_set = {highlight_node} | set(G.predecessors(highlight_node)) | set(G.successors(highlight_node))
    else:
        hl_set = None

    # -- Edges with variable thickness and hover ----------------------------

    max_weight = max((d["weight"] for _, _, d in G.edges(data=True)), default=1)
    min_w_log = math.log1p(1)
    max_w_log = math.log1p(max_weight) if max_weight > 1 else 1

    # Individual edge traces for variable width + hover
    edge_traces = []
    arrow_annotations = []
    top_edges = sorted(G.edges(data=True), key=lambda e: e[2].get("weight", 0), reverse=True)

    for rank, (u, v, d) in enumerate(top_edges):
        w = d.get("weight", 1)
        norm = (math.log1p(w) - min_w_log) / (max_w_log - min_w_log) if max_w_log > min_w_log else 0.5
        thickness = 0.3 + norm * 3.0
        opacity = 0.15 + norm * 0.6

        if hl_set:
            if u not in hl_set or v not in hl_set:
                opacity *= 0.1
                thickness *= 0.3

        x0, y0 = pos[u]
        x1, y1 = pos[v]

        edge_traces.append(go.Scattergl(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=thickness, color=f"rgba(100, 100, 100, {opacity:.2f})"),
            hovertext=f"{code_display(u)} -> {code_display(v)}<br>Peso: {w:,}",
            hoverinfo="text",
            showlegend=False,
        ))

        # Arrow annotations on top 15 edges
        if rank < 15:
            mx = x0 + 0.7 * (x1 - x0)
            my = y0 + 0.7 * (y1 - y0)
            dx = (x1 - x0)
            dy = (y1 - y0)
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                arrow_annotations.append(dict(
                    x=mx, y=my,
                    ax=mx - dx * 0.08, ay=my - dy * 0.08,
                    xref="x", yref="y", axref="x", ayref="y",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=max(1, thickness * 0.8),
                    arrowcolor=f"rgba(80, 80, 80, {min(opacity * 1.5, 0.7):.2f})",
                ))

    # -- Node traces grouped by chapter ------------------------------------

    node_traces = []
    chapters_seen = {}
    node_data_list = []

    for node in G.nodes():
        letter = G.nodes[node].get("chapter", "")
        if letter not in chapters_seen:
            chapters_seen[letter] = {
                "x": [], "y": [], "hover": [], "size": [], "labels": [],
                "color": G.nodes[node].get("color", "#999999"),
                "label": G.nodes[node].get("label", "Outros"),
                "nodes": [],
            }
        x, y = pos[node]
        count = G.nodes[node].get("count", 1)
        deg = G.degree(node, weight="weight")
        display = code_display(node)
        hover = f"{display}<br>{chapter_label(node)}<br>Ocorrencias: {count:,}<br>Grau ponderado: {deg:,}"
        size = max(6, min(45, math.sqrt(count) * 2))

        # Show label on nodes with size > 15
        show_label = display if size > 15 else ""

        chapters_seen[letter]["x"].append(x)
        chapters_seen[letter]["y"].append(y)
        chapters_seen[letter]["hover"].append(hover)
        chapters_seen[letter]["size"].append(size)
        chapters_seen[letter]["labels"].append(show_label)
        chapters_seen[letter]["nodes"].append(node)

    for letter, data in sorted(chapters_seen.items()):
        # Compute opacity per node for highlight mode
        if hl_set:
            opacities = [1.0 if n in hl_set else 0.12 for n in data["nodes"]]
            marker_colors = [
                data["color"] if n in hl_set
                else f"rgba(200, 200, 200, 0.3)"
                for n in data["nodes"]
            ]
        else:
            opacities = [1.0] * len(data["nodes"])
            marker_colors = data["color"]

        node_traces.append(go.Scattergl(
            x=data["x"], y=data["y"],
            mode="markers+text",
            marker=dict(
                size=data["size"],
                color=marker_colors,
                line=dict(width=0.5, color="white"),
                opacity=opacities if hl_set else 0.85,
            ),
            text=data["labels"],
            textposition="top center",
            textfont=dict(size=8, color="#333"),
            hovertext=data["hover"],
            hoverinfo="text",
            name=f"{letter}: {data['label']}",
            legendgroup=letter,
        ))

    fig = go.Figure(data=edge_traces + node_traces)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        showlegend=True,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        width=width,
        height=height,
        plot_bgcolor="#fafafa",
        paper_bgcolor="white",
        legend=dict(
            title="Capitulos CID-10",
            orientation="h",
            yanchor="top",
            y=-0.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.08)",
            borderwidth=1,
            font=dict(size=10),
        ),
        margin=dict(l=10, r=10, t=50, b=100),
        annotations=arrow_annotations,
    )

    return fig


def heatmap_plot(
    G: nx.DiGraph,
    title: str = "Co-ocorrencia entre capitulos CID-10",
    normalize: bool = False,
    split_direction: bool = False,
) -> go.Figure:
    """Create a heatmap of co-occurrence between ICD-10 chapters.

    Parameters
    ----------
    normalize : normalize each row by its total (shows relative co-occurrence).
    split_direction : if True, upper triangle = source->target, lower = target->source.
    """
    import pandas as pd

    if len(G) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado para exibir", showarrow=False)
        return fig

    chapters = sorted(set(
        G.nodes[n].get("chapter", "") for n in G.nodes()
    ))
    chapters = [c for c in chapters if c]

    if split_direction:
        # Upper triangle: source chapter -> target chapter
        # Lower triangle: target chapter -> source chapter
        matrix_upper = pd.DataFrame(0.0, index=chapters, columns=chapters)
        matrix_lower = pd.DataFrame(0.0, index=chapters, columns=chapters)
        for u, v, d in G.edges(data=True):
            ch_u = G.nodes[u].get("chapter", "")
            ch_v = G.nodes[v].get("chapter", "")
            w = d.get("weight", 1)
            if ch_u and ch_v:
                matrix_upper.loc[ch_u, ch_v] += w
                matrix_lower.loc[ch_v, ch_u] += w

        # Combine: upper triangle from matrix_upper, lower from matrix_lower
        matrix = pd.DataFrame(0.0, index=chapters, columns=chapters)
        for i, ci in enumerate(chapters):
            for j, cj in enumerate(chapters):
                if j >= i:
                    matrix.loc[ci, cj] = matrix_upper.loc[ci, cj]
                else:
                    matrix.loc[ci, cj] = matrix_lower.loc[ci, cj]

        hover_template = "Linha %{y} -> Coluna %{x}<br>Peso: %{z:,.0f}<extra></extra>"
    else:
        matrix = pd.DataFrame(0, index=chapters, columns=chapters)
        for u, v, d in G.edges(data=True):
            ch_u = G.nodes[u].get("chapter", "")
            ch_v = G.nodes[v].get("chapter", "")
            if ch_u and ch_v:
                matrix.loc[ch_u, ch_v] += d.get("weight", 1)
        hover_template = "De %{y} para %{x}<br>Peso: %{z:,.0f}<extra></extra>"

    if normalize:
        row_sums = matrix.sum(axis=1).replace(0, 1)
        matrix = matrix.div(row_sums, axis=0)
        hover_template = "De %{y} para %{x}<br>Proporcao: %{z:.2%}<extra></extra>"

    labels = [f"{c}: {CHAPTERS.get(c, {}).get('label', '')[:25]}" for c in chapters]

    z_values = matrix.values
    if normalize:
        colorscale = "Greys"
    else:
        # Use log scale for better contrast
        z_values = np.log1p(z_values)
        colorscale = "Greys"

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=labels,
        y=labels,
        colorscale=colorscale,
        hovertemplate=hover_template,
        showscale=True,
        colorbar=dict(title="log(peso)" if not normalize else "proporcao"),
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        width=800,
        height=700,
        xaxis=dict(tickangle=45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=9)),
        margin=dict(l=140, r=20, t=50, b=140),
        plot_bgcolor="white",
    )

    return fig


def sankey_plot(
    G: nx.DiGraph,
    top_n: int = 30,
    title: str = "Fluxo causal: causa basica -> causa imediata",
) -> go.Figure:
    """Create a Sankey diagram showing flow from underlying to immediate causes."""
    if len(G) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado para exibir", showarrow=False)
        return fig

    edges = sorted(G.edges(data=True), key=lambda e: e[2].get("weight", 0), reverse=True)[:top_n]

    nodes = list(set(e[0] for e in edges) | set(e[1] for e in edges))
    node_idx = {n: i for i, n in enumerate(nodes)}

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=[code_display(n) for n in nodes],
            color=[chapter_color(n) for n in nodes],
            hovertemplate="%{label}<br>%{value:,} ocorrencias<extra></extra>",
        ),
        link=dict(
            source=[node_idx[e[0]] for e in edges],
            target=[node_idx[e[1]] for e in edges],
            value=[e[2].get("weight", 1) for e in edges],
            hovertemplate="De %{source.label} para %{target.label}<br>Peso: %{value:,}<extra></extra>",
        ),
    )])

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        width=1000,
        height=600,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def top_cids_bar(G: nx.DiGraph, top_n: int = 20) -> go.Figure:
    """Horizontal bar chart of top CIDs by weighted degree, colored by chapter."""
    if len(G) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado para exibir", showarrow=False)
        return fig

    deg = dict(G.degree(weight="weight"))
    top_nodes = sorted(deg, key=deg.get, reverse=True)[:top_n]

    labels = [code_display(n) for n in top_nodes]
    values = [deg[n] for n in top_nodes]
    colors = [chapter_color(n) for n in top_nodes]
    hovers = [f"{code_display(n)}<br>{chapter_label(n)}<br>Grau: {deg[n]:,}" for n in top_nodes]

    fig = go.Figure(data=go.Bar(
        y=labels[::-1],
        x=values[::-1],
        orientation="h",
        marker=dict(color=colors[::-1]),
        hovertext=hovers[::-1],
        hoverinfo="text",
    ))

    fig.update_layout(
        title=dict(text="Top CIDs por grau ponderado", font=dict(size=14)),
        xaxis=dict(title="Grau ponderado"),
        yaxis=dict(tickfont=dict(size=10)),
        height=max(400, top_n * 22),
        margin=dict(l=80, r=20, t=50, b=40),
        plot_bgcolor="#fafafa",
        bargap=0.15,
    )

    return fig
