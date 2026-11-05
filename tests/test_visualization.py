"""Abbildungen: sie entstehen für jede Eingabe, Achsen sind gesperrt, Beschriftungen und Daten stimmen mit den Werten überein; PDF-Export."""

import dtp_constants as C
import dtp_evaluation as ev
import dtp_instance as I
import dtp_visualization as V
from dtp_pdf_export import build_pdf


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_descent_trace_carries_the_costs_and_the_reference():
    s = ev.Settings("cluster", 8, 46)
    v = ev.instance_data(s)
    d = v["descents"]["random"]
    fig = V.build_descent_trace(d, v["ref"])
    assert [t.name for t in fig.data] == ["Kosten", "Vergleichswert"] and list(fig.data[0].y) == list(d.costs) and list(fig.data[0].x) == list(range(d.steps + 1)) and list(fig.data[1].y) == [v["ref"], v["ref"]] and fig.data[0].text[0] == "Start" and _locked(fig)
    none = v["descents"]["loop"]
    assert len(V.build_descent_trace(none, v["ref"]).data[0].x) == none.steps + 1


def test_anneal_trace_has_cost_best_reference_and_temperature():
    s = ev.Settings("cluster", 8, 46, method="anneal")
    v = ev.instance_data(s)
    a = v["anneals"]["loop"]
    fig = V.build_anneal_trace(a, v["ref"])
    assert [t.name for t in fig.data] == ["aktuelle Kosten", "beste Kosten", "Vergleichswert", "Temperatur"] and list(fig.data[1].y) == [t[2] for t in a.trace] and list(fig.data[3].y) == [t[3] for t in a.trace] and list(fig.data[0].x)[-1] == a.moves and fig.data[3].y[0] > fig.data[3].y[-1]


def test_start_bars_and_effort_curve():
    s = ev.Settings("cluster", 8, 46)
    v = ev.instance_data(s)
    f1 = V.build_start_bars(v)
    assert [t.name for t in f1.data] == ["Start", "nach dem Abstieg", "nach dem Annealing"] and list(f1.data[0].x) == [C.START_NAMES[k] for k in C.START_CHOICES] and list(f1.data[1].y) == [v["descents"][k].cost for k in C.START_CHOICES] and _locked(f1)
    f2 = V.build_effort_curve(v)
    names = [t.name for t in f2.data]
    assert names[:3] == ["Neustarts des Abstiegs aus Zufall", "Annealing aus Zufall", "Annealing aus der Schleife"] and names[3:] == [f"Abstieg aus {C.START_NAMES[k]}" for k in C.START_CHOICES] and f2.layout.xaxis.type == "log"
    assert list(f2.data[0].y) == [b for _, b in v["restarts"]] and list(f2.data[3].x) == [v["descents"]["random"].evals] and _locked(f2)


def test_sweep_charts():
    rows = [r for f in C.FAMILIES for r in ev.sweep(f, 6, (100000, 100001), (2, 8))]
    f1 = V.build_sweep_bars(rows, ev.median_of, ev.start_summary, "t")
    assert len(f1.data) == 6 and [t.name for t in f1.data][1] == "nach dem Abstieg: Zufall" and list(f1.data[0].x) == ["2 Pads", "8 Pads"] and _locked(f1)
    f2 = V.build_restart_bars(rows, ev.restart_summary, ev.start_summary, ev.sa_summary, "t")
    assert [t.name for t in f2.data] == ["Neustarts aus Zufall (Zahl der Läufe)", "Abstieg aus der Schleife", "Annealing aus Zufall", "Annealing aus der Schleife"] and list(f2.data[0].text) == ["1", "3", "6", "20"] and f2.layout.xaxis.type == "log" and _locked(f2)


def test_arrangement_chart_for_every_family_and_size(hand):
    for fam in C.FAMILIES:
        for n in (6, 9, 12, 16):
            assert len(V.build_arrangement(I.make_instance(fam, n, 3), list(range(n)), fam).data[-1].x) == n
    assert len(V.build_arrangement(hand, [0, 1, 2], "Hand").data[-1].x) == 3


def test_the_pdf_export_returns_a_pdf_for_an_exact_and_a_large_instance():
    s = ev.Settings("netlist", 6, 35)
    assert build_pdf(s, ev.instance_data(s))[:5] == b"%PDF-"
    s2 = ev.Settings("uniform", 12, 35, 2, "random", "anneal", 2.0, 0.5)
    data = build_pdf(s2, ev.instance_data(s2))
    assert data[:5] == b"%PDF-" and len(data) > 1500
