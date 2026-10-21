"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import red_constants as C
from red_scenario import literal_name


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.22), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def node_positions(m: int) -> list[tuple[float, float]]:
    """Ein kleines Dreieck je Klausel, die Dreiecke gleichmäßig auf einem großen Kreis (Klausel 1 oben); jedes Dreieck zeigt mit einer Ecke nach außen."""
    radius_small = min(0.11, 0.9 * math.pi / max(m, 1) * 0.55)
    positions = []
    for i in range(m):
        theta = 2 * math.pi * i / m
        cx, cy = math.sin(theta), math.cos(theta)
        for j in range(3):
            phi = theta + 2 * math.pi * j / 3
            positions.append((cx + radius_small * math.sin(phi), cy + radius_small * math.cos(phi)))
    return positions


def _edge_trace(pos, edges, color, width, dash=None, name=""):
    xs, ys = [], []
    for a, b in edges:
        xs += [pos[a][0], pos[b][0], None]
        ys += [pos[a][1], pos[b][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), hoverinfo="skip", name=name, showlegend=bool(name))


def build_graph(formula, adj, witness=()):
    """G_F: Dreieckskanten dunkel, Konfliktkanten gestrichelt rot; Knoten beschriftet mit ihrem Literal; die unabhängige Menge (der Beleg) grün."""
    m = len(formula)
    pos = node_positions(m)
    triangle = [(a, b) for a in range(len(adj)) for b in adj[a] if a < b and a // 3 == b // 3]
    conflict = [(a, b) for a in range(len(adj)) for b in adj[a] if a < b and a // 3 != b // 3]
    chosen = set(witness)
    fig = go.Figure()
    fig.add_trace(_edge_trace(pos, conflict, C.COLOR_CONFLICT, 1.2, "dash", "Konfliktkante (x gegen nicht x)"))
    fig.add_trace(_edge_trace(pos, triangle, C.COLOR_TRIANGLE, 2.0, None, "Klausel (Dreieck)"))
    labels = [literal_name(formula[v // 3][v % 3]) for v in range(len(adj))]
    hover = [f"Klausel {v // 3 + 1}: {labels[v]}" for v in range(len(adj))]
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers+text", text=labels, textposition="middle center", textfont=dict(size=8 if m > 14 else 10, color="white"),
        marker=dict(size=22 if m <= 14 else 17, color=[C.COLOR_CHOSEN if v in chosen else C.COLOR_NODE for v in range(len(adj))], line=dict(width=1, color="white")),
        hovertext=hover, hoverinfo="text", showlegend=False,
    ))
    fig.update_xaxes(range=[-1.3, 1.3], visible=False)
    fig.update_yaxes(range=[-1.3, 1.3], visible=False)
    return _base(fig, 520)


def build_size(rows):
    """Größe der Reduktion über m: Knoten, Kanten, Konfliktkanten (Median über feste Formeln)."""
    xs = [r["m"] for r in rows]
    fig = go.Figure()
    for key, name, color, dash in (("edges", "Kanten von G_F", C.COLOR_SERIES[1], "solid"), ("conflicts", "davon Konfliktkanten", C.COLOR_SERIES[3], "dot"), ("nodes", "Knoten (3m)", C.COLOR_SERIES[0], "solid")):
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in rows], mode="lines+markers", name=name, line=dict(color=color, width=2.5, dash=dash),
                                 hovertemplate="m = %{x}: %{y:,.0f}<extra></extra>"))
    fig.update_xaxes(title_text="Klauseln m", dtick=6)
    fig.update_yaxes(title_text="Anzahl", rangemode="tozero")
    return _base(fig, 340)


def build_effort(rows, budget):
    """Knoten über m (logarithmisch): DPLL auf der Formel, Überdeckungssuche und Cliquensuche auf G_F, Gegenstück Zufallsgraph; das Budget als Linie."""
    xs = [r["m"] for r in rows]
    fig = go.Figure()
    series = (
        ("dpll", "DPLL auf der Formel", C.COLOR_SERIES[0], "solid"),
        ("cover", "Überdeckungssuche auf G_F", C.COLOR_SERIES[1], "solid"),
        ("clique", "Cliquensuche im Komplement von G_F", C.COLOR_SERIES[3], "solid"),
        ("rand_cover", "Überdeckungssuche, Zufallsgraph", C.COLOR_SERIES[1], "dot"),
        ("rand_clique", "Cliquensuche, Zufallsgraph", C.COLOR_SERIES[3], "dot"),
    )
    for key, name, color, dash in series:
        fig.add_trace(go.Scatter(x=xs, y=[max(r[key], 1) for r in rows], mode="lines+markers", name=name, line=dict(color=color, width=2.5, dash=dash),
                                 hovertemplate="m = %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.add_hline(y=budget, line=dict(color="gray", width=1.5, dash="dot"), annotation_text="Budget", annotation_position="top left")
    fig.update_xaxes(title_text="Klauseln m", dtick=6)
    fig.update_yaxes(title_text="Knoten der Suche (log)", type="log")
    return _base(fig, 420)


def build_random_refutation(rows):
    """Größe des DPLL-Baums bei unerfüllbaren Zufallsformeln über n (Median und Maximum)."""
    rows = [r for r in rows if r["median"] is not None]
    xs = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["median"] for r in rows], mode="lines+markers", name="Median", line=dict(color=C.COLOR_SERIES[0], width=3),
                             hovertemplate="n = %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["max"] for r in rows], mode="lines", name="Maximum", line=dict(color=C.COLOR_SERIES[0], width=1.5, dash="dot"),
                             hovertemplate="n = %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.update_xaxes(title_text="Variablen n", dtick=5)
    fig.update_yaxes(title_text="Knoten des DPLL-Baums", rangemode="tozero")
    return _base(fig, 320)


def build_pigeon(rows):
    """Größe des DPLL-Baums bei den Schubfach-Formeln über die Zahl der Fächer (logarithmisch)."""
    xs = [r["h"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["nodes"] for r in rows], mode="lines+markers", name="Schubfach-Formeln", line=dict(color=C.COLOR_SERIES[3], width=3),
                             hovertemplate="h = %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.update_xaxes(title_text="Fächer h (h + 1 Tauben)", dtick=1)
    fig.update_yaxes(title_text="Knoten des DPLL-Baums (log)", type="log")
    return _base(fig, 320)
