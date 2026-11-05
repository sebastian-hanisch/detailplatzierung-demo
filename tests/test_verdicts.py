"""Verdikte (reine Funktionen in dtp_evaluation.py) an handgesetzten Werten: Art, Schwellen und jede Zahl im Text (DEMO-PLAYBOOK §1b)."""

import dtp_evaluation as ev
import dtp_search as S


def _desc(costs, evals=112):
    return S.Descent([0, 1, 2], costs[-1], len(costs) - 1, evals, tuple(costs), tuple((0, 1) for _ in range(len(costs) - 1)))


def _anneal(cost, start=377.0, moves=1500, accepted=75, scale=13.1, best_at=107, t0=0.5):
    return S.Anneal([0, 1, 2], cost, start, moves, accepted, scale, t0, ((1, start, start, 6.5), (moves, cost, cost, 0.13)), best_at)


def _v(descents=None, anneals=None, ref=339.0, exact=True, mean=400.0, restarts=None):
    inst = type("I", (), {"rows": 2, "cols": 4})()
    d = descents or {"random": _desc([377, 346], 168), "round": _desc([377, 360, 354]), "loop": _desc([377, 360, 354])}
    a = anneals or {"random": _anneal(341), "round": _anneal(339), "loop": _anneal(339)}
    return {"inst": inst, "exact": exact, "ref": ref, "mean": mean, "gap_mean": (mean - ref) / ref if mean else None, "descents": d, "anneals": a, "starts": {}, "start_costs": {k: x.costs[0] for k, x in d.items()},
            "restarts": restarts or [(168, 346.0), (336, 346.0), (420, 341.0)] + [(500 + 100 * i, 339.0) for i in range(17)]}


def _row(p, loop=(0.10, 0.04, 3, 112, True, True), rnd=(0.30, 0.03, 4, 140, False, True), rd=(0.14, 0.04, 3, 112, False, True), exact=True, sa=(0.0, 0.01), mean=0.3):
    def st(t):
        return {"start": t[0], "desc": t[1], "steps": t[2], "evals": t[3], "hit": t[4], "better": t[5]}
    return {"p": p, "exact": exact, "budget": 1500, "gap_mean": mean, "loop": st(loop), "random": st(rnd), "round": st(rd), "sa_random": {"gap": sa[1], "hit": False, "accepted": 0.2}, "sa_loop": {"gap": sa[0], "hit": True, "accepted": 0.1},
            "restarts": {1: {"gap": 0.03, "evals": 140, "hit": False}, 3: {"gap": 0.01, "evals": 420, "hit": False}, 6: {"gap": 0.0, "evals": 812, "hit": True}, 20: {"gap": 0.0, "evals": 2772, "hit": True}}}


def test_descent_verdict_with_steps_without_steps_and_at_the_reference():
    s = ev.Settings("cluster", 8, 46, 4, "loop")
    kind, text = ev.verdict_descent(s, _v())
    assert kind == "info" and "Familie **Zwei Cluster**, 8 Bauteile, Raster 2×4, Seed 46, 4 Pads, Start Schleife (Stück 10)" in text and "braucht **2 Schritte** und 112 Bewertungen" in text and "von 377 (Lücke 11,2 %) auf **354** (Lücke 4,4 %) gegen das aufgezählte Optimum 339" in text and "nicht der Vergleichswert" in text
    k2, t2 = ev.verdict_descent(s, _v(descents={"loop": _desc([339, 339], 28), "random": _desc([377, 346]), "round": _desc([377, 346])}))
    assert k2 == "info" and "braucht **1 Schritt**" in t2 or "Schritt" in t2
    k3, t3 = ev.verdict_descent(s, _v(descents={"loop": _desc([380, 339]), "random": _desc([377, 346]), "round": _desc([377, 346])}))
    assert k3 == "success" and "das ist der Vergleichswert" in t3
    k4, t4 = ev.verdict_descent(s, _v(descents={"loop": S.Descent([0, 1, 2], 339.0, 0, 28, (339.0,), ()), "random": _desc([377, 346]), "round": _desc([377, 346])}))
    assert k4 == "info" and "schon ein **lokales Optimum der Tauschnachbarschaft**" in t4 and "prüft 28 Bewertungen und bewegt sich nicht" in t4
    assert "die beste von 100 Abstiegen (obere Grenze) 339" in ev.verdict_descent(s, _v(exact=False, mean=None))[1]


def test_starts_anneal_and_effort_verdicts():
    s = ev.Settings("cluster", 8, 46, 4, "loop", "anneal", 0.5)
    v = _v()
    kind, text = ev.verdict_starts(s, v)
    assert kind == "info" and "Zufall: Start 377 (Lücke 11,2 %) → Abstieg 346 (Lücke 2,1 %) in 1 Schritt und 168 Bewertungen" in text and "Rundung (Stück 9): Start 377 (Lücke 11,2 %) → Abstieg 354 (Lücke 4,4 %) in 2 Schritten und 112 Bewertungen" in text and "Eine Instanz" in text
    kind, text = ev.verdict_anneal(s, v)
    assert kind == "success" and "Starttemperatur 0,5 · s mit s = 13,1: 1 500 Züge, 5 % angenommen" in text and "(Kosten **339**, Lücke 0,0 % gegen das aufgezählte Optimum 339) wurde in Zug 107 gefunden" in text and "besser als der Abstieg aus derselben Startlösung (354 in 112 Bewertungen)" in text
    same = _v(anneals={"random": _anneal(341), "round": _anneal(354, best_at=0), "loop": _anneal(354, best_at=0)})
    text = ev.verdict_anneal(s, same)[1]
    assert "blieb die Startanordnung" in text and "gleich der Abstieg" in text
    worse = _v(anneals={"random": _anneal(341), "round": _anneal(360), "loop": _anneal(360)})
    assert "schlechter als der Abstieg" in ev.verdict_anneal(s, worse)[1] and ev.verdict_anneal(s, worse)[0] == "info"
    text = ev.verdict_effort(s, v)[1]
    assert "Neustarts aus Zufall: 1 Neustart: Kosten 346 (Lücke 2,1 %) bei 168 Bewertungen; 3 Neustarts: Kosten 341 (Lücke 0,6 %) bei 420 Bewertungen; 6 Neustarts: Kosten 339 (Lücke 0,0 %) bei 700 Bewertungen; 20 Neustarts: Kosten 339 (Lücke 0,0 %) bei 2 100 Bewertungen" in text
    assert "Abstieg aus der Schleife: Kosten 354 (Lücke 4,4 %) bei 112 Bewertungen; Annealing aus der Schleife (Starttemperatur 0,5 · s): Kosten 339 (Lücke 0,0 %) bei 1 500 Bewertungen" in text


def test_sweep_verdicts():
    rows = [_row(2), _row(4, loop=(0.12, 0.06, 4, 140, False, True)), _row(8)]
    kind, text = ev.verdict_sweep_starts(8, rows)
    assert kind == "info" and "Bei n = 8, Median über 3 Instanzen (alle Pad-Zahlen)" in text and "Zufall: Start 30,0 % → Abstieg 3,0 % (4 Schritte, 140 Bewertungen, Vergleichswert erreicht in 0 von 3)" in text and "Schleife (Stück 10): Start 10,0 % → Abstieg 4,0 % (3 Schritte, 112 Bewertungen, Vergleichswert erreicht in 2 von 3)" in text and "obere Grenze" not in text
    assert "obere Grenze der Lücke" in ev.verdict_sweep_starts(12, [_row(2, exact=False)])[1]
    text = ev.verdict_sweep_anneal(8, rows)[1]
    assert "Annealing aus Zufall (Starttemperatur 2 · s, 1 500 Züge) Lücke 1,0 %, Vergleichswert erreicht in 0; Annealing aus der Schleife (Starttemperatur 0,1 · s) Lücke 0,0 %, erreicht in 3; Abstieg aus der Schleife Lücke 4,0 %, erreicht in 2" in text
    text = ev.verdict_sweep_restarts(8, rows)[1]
    assert "1: Lücke 3,0 % bei 140 Bewertungen; 3: Lücke 1,0 % bei 420 Bewertungen; 6: Lücke 0,0 % bei 812 Bewertungen; 20: Lücke 0,0 % bei 2 772 Bewertungen" in text and "Abstieg aus der Schleife: Lücke 4,0 % bei 112 Bewertungen" in text


def test_core_verdict_quotes_the_numbers():
    s = ev.Settings("cluster", 8, 46, 4, "loop", "descent")
    text = ev.verdict_core(s, _v())[1]
    assert "Tauschabstieg aus der Startlösung Schleife (Stück 10) die Kosten von 377 auf 354 (Lücke 11,2 % → 4,4 % gegen das aufgezählte Optimum 339) mit 112 Bewertungen" in text and "Experiment 1 bis 5" in text
    s2 = ev.Settings("cluster", 8, 46, 4, "loop", "anneal")
    assert "Simulated Annealing aus der Startlösung Schleife (Stück 10) die Kosten von 377 auf 339 (Lücke 11,2 % → 0,0 %" in ev.verdict_core(s2, _v())[1] and "mit 1 500 Bewertungen" in ev.verdict_core(s2, _v())[1]
