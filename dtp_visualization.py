"""Plotly-Abbildungen. Alle 2D-Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dtp_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend_below=True):
    legend = dict(orientation="h", yanchor="top", y=-0.22, x=0) if legend_below else dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    fig.update_layout(height=height + (40 if legend_below else 0), margin=dict(l=10, r=10, t=50, b=10), legend=legend, plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _extent(inst, pads, X):
    xs = [float(x) for x in inst.xy[:, 0]] + [float(x) for x in pads.pos[:, 0]] + [float(x) for x in X[:, 0]]
    ys = [-float(y) for y in inst.xy[:, 1]] + [-float(y) for y in pads.pos[:, 1]] + [-float(y) for y in X[:, 1]]
    return min(xs) - 0.6, max(xs) + 0.6, min(ys) - 0.6, max(ys) + 0.6


def build_arrangement(inst, perm, title: str) -> go.Figure:
    """Die gerundete Anordnung: Bauteile auf den Plätzen, Verbindungen mit Fluss als Linien."""
    fig = go.Figure()
    xs, ys = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    pos = [(xs[int(perm[i])], ys[int(perm[i])]) for i in range(inst.n)]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(symbol="square", size=36, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False))
    fmax = max(1, int(inst.F.max()))
    lx, ly = [], []
    for a in range(inst.n):
        for b in range(a + 1, inst.n):
            if inst.F[a, b]:
                lx += [pos[a][0], pos[b][0], None]
                ly += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(width=1.5, color="rgba(76,120,168,0.35)"), hoverinfo="skip", name="Fluss"))
    fig.add_trace(go.Scatter(x=[q[0] for q in pos], y=[q[1] for q in pos], mode="markers+text", text=list(inst.names), textposition="middle center", showlegend=False, marker=dict(size=26, color=C.COLORS["best"]), textfont=dict(color="white", size=10)))
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[xs.min() - 0.7, xs.max() + 0.7], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[ys.min() - 0.7, ys.max() + 0.7])
    return _base(fig, height=300)


# ----------------------------------------------------------------------------- Abstieg, Annealing, Aufwand

def build_descent_trace(d, ref: float, title: str = "Kosten je Schritt des Abstiegs") -> go.Figure:
    """Kosten vor dem ersten und nach jedem Schritt des Tauschabstiegs; gestrichelt der Vergleichswert."""
    xs = list(range(len(d.costs)))
    labels = ["Start"] + [f"Tausch {a + 1} ↔ {b + 1}" for a, b in d.swaps]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=list(d.costs), mode="lines+markers", name="Kosten", line=dict(color=C.COLORS["cont"], width=3), marker=dict(size=8), text=labels, hovertemplate="%{text}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[xs[0], xs[-1]], y=[ref, ref], mode="lines", name="Vergleichswert", line=dict(color=C.COLORS["best"], dash="dot", width=2)))
    fig.update_xaxes(title="Schritt", dtick=1)
    fig.update_yaxes(title="Kosten")
    fig.update_layout(title=title)
    return _base(fig, height=320)


def build_anneal_trace(a, ref: float, title: str = "Annealing: Kosten und Temperatur") -> go.Figure:
    """Aktuelle und beste Kosten über die Züge, dazu die Temperatur (zweite Achse); gestrichelt der Vergleichswert."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    xs = [t[0] for t in a.trace]
    fig.add_trace(go.Scatter(x=xs, y=[t[1] for t in a.trace], mode="lines", name="aktuelle Kosten", line=dict(color="rgba(150,150,150,0.8)", width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=xs, y=[t[2] for t in a.trace], mode="lines", name="beste Kosten", line=dict(color=C.COLORS["cont"], width=3)), secondary_y=False)
    fig.add_trace(go.Scatter(x=[xs[0], xs[-1]], y=[ref, ref], mode="lines", name="Vergleichswert", line=dict(color=C.COLORS["best"], dash="dot", width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=xs, y=[t[3] for t in a.trace], mode="lines", name="Temperatur", line=dict(color="#4c78a8", width=2, dash="dash")), secondary_y=True)
    fig.update_xaxes(title="Zug")
    fig.update_yaxes(title="Kosten", secondary_y=False, fixedrange=True)
    fig.update_yaxes(title="Temperatur", secondary_y=True, fixedrange=True)
    fig.update_layout(title=title)
    return _base(fig, height=340)


def build_start_bars(v: dict) -> go.Figure:
    """Je Startlösung: Kosten am Start, nach dem Abstieg und nach dem Annealing; gestrichelt der Vergleichswert."""
    ks = list(C.START_CHOICES)
    xs = [C.START_NAMES[k] for k in ks]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[v["start_costs"][k] for k in ks], name="Start", marker_color="rgba(150,150,150,0.7)"))
    fig.add_trace(go.Bar(x=xs, y=[v["descents"][k].cost for k in ks], name="nach dem Abstieg", marker_color="#4c78a8"))
    fig.add_trace(go.Bar(x=xs, y=[v["anneals"][k].cost for k in ks], name="nach dem Annealing", marker_color="#2F6B65"))
    fig.add_hline(y=v["ref"], line_dash="dot", line_color=C.COLORS["best"], annotation_text="Vergleichswert", annotation_position="top left")
    lo = min(min(v["start_costs"].values()), min(d.cost for d in v["descents"].values()), v["ref"])
    fig.update_yaxes(title="Kosten", range=[0.8 * lo, 1.05 * max(v["start_costs"].values())])
    fig.update_layout(title="Startlösungen, Abstieg und Annealing", barmode="group")
    return _base(fig, height=340)


def build_effort_curve(v: dict) -> go.Figure:
    """Kosten gegen Bewertungen (logarithmisch): Neustarts aus Zufall, Annealing aus Zufall und aus der Schleife (beste Kosten über die Züge), Abstiege aus den Startlösungen als Punkte."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[e for e, _ in v["restarts"]], y=[b for _, b in v["restarts"]], mode="lines+markers", name="Neustarts des Abstiegs aus Zufall", line=dict(color="#9aa0a6", width=3, shape="hv"), marker=dict(size=5)))
    for k, col, nm in (("random", "#b08a2e", "Annealing aus Zufall"), ("loop", "#2F6B65", "Annealing aus der Schleife")):
        a = v["anneals"][k]
        fig.add_trace(go.Scatter(x=[t[0] for t in a.trace], y=[t[2] for t in a.trace], mode="lines", name=nm, line=dict(color=col, width=3, shape="hv")))
    pts = {"random": "#9aa0a6", "round": "#4c78a8", "loop": "#c0504d"}
    for k in C.START_CHOICES:
        d = v["descents"][k]
        fig.add_trace(go.Scatter(x=[d.evals], y=[d.cost], mode="markers", name=f"Abstieg aus {C.START_NAMES[k]}", marker=dict(size=13, color=pts[k], symbol="diamond", line=dict(width=1, color="white"))))
    fig.add_hline(y=v["ref"], line_dash="dot", line_color=C.COLORS["best"], annotation_text="Vergleichswert", annotation_position="top left")
    fig.update_xaxes(type="log", title="Bewertungen (logarithmisch)")
    fig.update_yaxes(title="beste Kosten")
    fig.update_layout(title="Kosten gegen Aufwand")
    return _base(fig, height=400)


def build_sweep_bars(rows: list, median_of, start_summary, title: str) -> go.Figure:
    """Median der Lücke je Zahl der Pads: am Start und nach dem Abstieg, für jede Startlösung."""
    ps = sorted({r["p"] for r in rows})
    fig = go.Figure()
    colors = {"random": "#9aa0a6", "round": "#4c78a8", "loop": "#c0504d"}
    for k in C.START_CHOICES:
        fig.add_trace(go.Bar(x=[f"{p} Pads" for p in ps], y=[100 * start_summary(rows, p, k)["start"] for p in ps], name=f"Start: {C.START_NAMES[k]}", marker_color=colors[k], opacity=0.35))
        fig.add_trace(go.Bar(x=[f"{p} Pads" for p in ps], y=[100 * start_summary(rows, p, k)["desc"] for p in ps], name=f"nach dem Abstieg: {C.START_NAMES[k]}", marker_color=colors[k]))
    fig.update_yaxes(title="Lücke (%, Median)")
    fig.update_layout(title=title, barmode="group")
    return _base(fig, height=400)


def build_restart_bars(rows: list, restart_summary, start_summary, sa_summary, title: str) -> go.Figure:
    """Median der Lücke gegen Median der Bewertungen: Neustarts aus Zufall (1, 3, 6, 20), Abstieg aus der Schleife, Annealing aus Zufall und aus der Schleife."""
    fig = go.Figure()
    ks = list(C.RESTART_KS)
    sums = [restart_summary(rows, k) for k in ks]
    fig.add_trace(go.Scatter(x=[s["evals"] for s in sums], y=[100 * s["gap"] for s in sums], mode="lines+markers+text", text=[f"{k}" for k in ks], textposition="top center", name="Neustarts aus Zufall (Zahl der Läufe)", line=dict(color="#9aa0a6", width=3)))
    lp = start_summary(rows, None, "loop")
    fig.add_trace(go.Scatter(x=[lp["evals"]], y=[100 * lp["desc"]], mode="markers", name="Abstieg aus der Schleife", marker=dict(size=14, color="#c0504d", symbol="diamond")))
    for key, col, nm in (("sa_random", "#b08a2e", "Annealing aus Zufall"), ("sa_loop", "#2F6B65", "Annealing aus der Schleife")):
        sa = sa_summary(rows, None, key)
        fig.add_trace(go.Scatter(x=[rows[0]["budget"]], y=[100 * sa["gap"]], mode="markers", name=nm, marker=dict(size=14, color=col, symbol="square")))
    fig.update_xaxes(type="log", title="Bewertungen (Median, logarithmisch)")
    fig.update_yaxes(title="Lücke (%, Median)")
    fig.update_layout(title=title)
    return _base(fig, height=380)
