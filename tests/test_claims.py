"""Die Zahlen der README (Abschnitte „Befunde“ und „Grenzen“) als Tests: Standardfall, Handbeispiel und die Vergleiche über feste Instanzen.
Prozentwerte auf eine Stelle (Toleranz 0,06), Zählungen exakt; Zeiten stehen nie in Tests (DEMO-PLAYBOOK §1b, Wiederholbarkeit)."""

import pytest

import dtp_constants as C
import dtp_evaluation as ev


def pc(x):
    return 100 * x


@pytest.fixture(scope="module")
def sweeps():
    return {n: ev.pooled({f: ev.sweep(f, n, seeds, C.PAD_CHOICES) for f in C.FAMILIES}) for n, seeds in ((8, C.SWEEP_SEEDS), (12, C.LARGE_SEEDS[12]), (16, C.LARGE_SEEDS[16]))}


def test_standard_instance_numbers():
    s = ev.Settings()
    v = ev.instance_data(s)
    assert (s.family, s.n, s.seed, s.pads, s.start, s.method, s.t0, s.budget) == ("cluster", 8, 46, 4, "loop", "descent", 0.5, 1.0) and v["exact"] and v["ref"] == 337.0 and pc(v["gap_mean"]) == pytest.approx(34.1, abs=0.06)
    assert v["start_costs"] == {"random": 448.0, "round": 414.0, "loop": 380.0}
    d = v["descents"]
    assert d["random"].costs == (448.0, 400.0, 356.0, 345.0, 337.0) and (d["random"].steps, d["random"].evals) == (4, 140)
    assert d["round"].costs == (414.0, 380.0, 363.0, 353.0, 346.0) and (d["round"].steps, d["round"].evals) == (4, 140)
    assert d["loop"].costs == (380.0, 363.0, 353.0, 346.0) and (d["loop"].steps, d["loop"].evals) == (3, 112) and pc((d["loop"].cost - 337) / 337) == pytest.approx(2.7, abs=0.06) and pc((380 - 337) / 337) == pytest.approx(12.8, abs=0.06)
    a = v["anneals"]
    assert [(a[k].cost, a[k].accepted, a[k].best_at) for k in C.START_CHOICES] == [(342.0, 77, 541), (342.0, 93, 219), (337.0, 133, 40)] and a["loop"].moves == 1500 and a["loop"].scale == pytest.approx(27.5, abs=0.05)
    assert [v["restarts"][k - 1] for k in C.RESTART_KS] == [(112, 342.0), (476, 337.0), (896, 337.0), (2828, 337.0)]


def test_standard_instance_other_temperatures():
    cold = ev.instance_data(ev.Settings(t0=0.1))["anneals"]
    assert [(cold[k].cost, cold[k].accepted, cold[k].best_at) for k in C.START_CHOICES] == [(337.0, 54, 180), (359.0, 9, 529), (342.0, 38, 183)]
    hot = ev.instance_data(ev.Settings(t0=2.0))["anneals"]
    assert [hot[k].cost for k in C.START_CHOICES] == [337.0, 337.0, 337.0] and [hot[k].accepted for k in C.START_CHOICES] == [255, 237, 342]


def test_hand_example():
    h = ev.hand_data()["descent"]
    assert h.perm == [0, 1, 2] and h.cost == 6.0 and (h.steps, h.evals, h.costs) == (1, 6, (7.0, 6.0))


EXP = {  # (Größe, p) -> {Start: (Start %, Abstieg %, Schritte, Bewertungen, erreicht)}, Annealing (Lücke % zufall, erreicht, Lücke % Schleife, erreicht)
    (8, None): ({"random": (32.4, 2.2, 4, 140, 104), "round": (8.1, 0.0, 2, 84, 181), "loop": (6.2, 0.2, 2, 84, 179)}, (0.0, 245, 0.0, 240)),
    (8, 2): ({"random": (40.7, 2.4, 4, 140, 38), "round": (14.5, 0.4, 2, 84, 59), "loop": (10.8, 0.6, 2, 84, 58)}, (0.0, 74, 0.0, 78)),
    (8, 4): ({"random": (33.6, 2.8, 4, 140, 28), "round": (8.8, 0.6, 2, 84, 57), "loop": (6.3, 0.6, 2, 84, 56)}, (0.0, 81, 0.0, 76)),
    (8, 8): ({"random": (26.8, 1.6, 4, 140, 38), "round": (4.4, 0.0, 1, 56, 65), "loop": (3.6, 0.0, 1, 56, 65)}, (0.0, 90, 0.0, 86)),
    (12, None): ({"random": (40.1, 3.8, 7, 528, 5), "round": (12.5, 1.9, 4, 330, 15), "loop": (9.1, 1.9, 3, 264, 14)}, (0.8, 26, 0.5, 42)),
    (12, 2): ({"random": (41.9, 4.1, 7, 528, 2), "round": (26.3, 3.8, 5, 396, 1), "loop": (10.6, 3.5, 4, 330, 2)}, (1.1, 11, 1.3, 13)),
    (12, 4): ({"random": (42.1, 4.1, 6, 462, 1), "round": (11.8, 2.9, 4, 330, 3), "loop": (10.6, 2.6, 4, 330, 2)}, (1.5, 5, 0.7, 11)),
    (12, 8): ({"random": (35.0, 3.0, 7, 528, 2), "round": (7.0, 0.6, 3, 264, 11), "loop": (5.9, 0.8, 3, 264, 10)}, (0.5, 10, 0.0, 18)),
    (16, None): ({"random": (43.3, 5.2, 9, 1200, 1), "round": (13.7, 2.2, 6, 840, 7), "loop": (10.4, 2.2, 5, 720, 7)}, (1.0, 15, 0.4, 22)),
    (16, 2): ({"random": (43.3, 4.8, 9, 1200, 1), "round": (24.8, 2.4, 7, 960, 2), "loop": (14.5, 2.9, 5, 720, 2)}, (1.3, 6, 0.3, 7)),
    (16, 4): ({"random": (45.0, 5.6, 9, 1200, 0), "round": (15.0, 3.6, 6, 840, 2), "loop": (11.1, 2.7, 6, 840, 2)}, (1.3, 3, 0.7, 7)),
    (16, 8): ({"random": (41.2, 5.3, 9.5, 1260, 0), "round": (8.7, 1.6, 5, 720, 3), "loop": (7.3, 1.7, 4, 600, 3)}, (0.9, 6, 0.2, 8)),
}


@pytest.mark.parametrize("n,p", sorted(EXP, key=lambda k: (k[0], 0 if k[1] is None else k[1])))
def test_starts_descents_and_annealing(sweeps, n, p):
    rows = sweeps[n]
    starts, (g_r, h_r, g_l, h_l) = EXP[(n, p)]
    for k, (st, de, steps, evals, hit) in starts.items():
        sm = ev.start_summary(rows, p, k)
        assert pc(sm["start"]) == pytest.approx(st, abs=0.06) and pc(sm["desc"]) == pytest.approx(de, abs=0.06) and (sm["steps"], sm["evals"], sm["hit"]) == (steps, evals, hit), (n, p, k)
    ra, lo = ev.sa_summary(rows, p, "sa_random"), ev.sa_summary(rows, p, "sa_loop")
    assert pc(ra["gap"]) == pytest.approx(g_r, abs=0.06) and ra["hit"] == h_r and pc(lo["gap"]) == pytest.approx(g_l, abs=0.06) and lo["hit"] == h_l, (n, p)


def test_improvement_counts_and_budgets(sweeps):
    assert [ev.start_summary(sweeps[8], None, k)["better"] for k in C.START_CHOICES] == [360, 320, 303] and [ev.start_summary(sweeps[12], None, k)["better"] for k in C.START_CHOICES] == [90, 87, 86]
    assert [sweeps[n][0]["budget"] for n in (8, 12, 16)] == [1500, 3000, 6000] and [len(sweeps[n]) for n in (8, 12, 16)] == [360, 90, 54]
    assert pc(ev.mean_gap(sweeps[8], 2)) == pytest.approx(38.1, abs=0.06) and pc(ev.mean_gap(sweeps[8], 4)) == pytest.approx(34.5, abs=0.06) and pc(ev.mean_gap(sweeps[8], 8)) == pytest.approx(26.1, abs=0.06)
    assert [round(pc(ev.sa_summary(sweeps[8], None, "sa_random")["accepted"])), round(pc(ev.sa_summary(sweeps[8], None, "sa_loop")["accepted"]))] == [20, 3]


def test_restarts_at_equal_effort(sweeps):
    exp = {8: ((2.2, 140, 94), (0.0, 420, 201), (0.0, 812, 286), (0.0, 2772, 352)), 12: ((3.1, 462, 9), (1.4, 1518, 22), (0.7, 3036, 29), (0.0, 10098, 56)), 16: ((4.7, 1200, 1), (2.1, 3660, 5), (1.5, 7440, 7), (0.3, 24600, 23))}
    for n, vals in exp.items():
        for k, (gap, evals, hit) in zip(C.RESTART_KS, vals):
            sm = ev.restart_summary(sweeps[n], k)
            assert pc(sm["gap"]) == pytest.approx(gap, abs=0.06) and sm["evals"] == evals and sm["hit"] == hit, (n, k)
