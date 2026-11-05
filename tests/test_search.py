"""Tauschabstieg, Annealing, Startlösungen und Neustarts: Handwerte, Eigenschaften, Randfälle (DEMO-PLAYBOOK §1b, ORACLE-PLAYBOOK §5)."""

import math
from itertools import permutations

import numpy as np
import pytest

import dtp_constants as C
import dtp_instance as I
import dtp_place as Pl
import dtp_search as S
from dtp_rng import SplitMix64


def _setup(family="cluster", n=8, seed=100000, p=4):
    inst = I.make_instance(family, n, seed)
    pads = Pl.make_pads(inst, p, seed)
    return inst, pads, Pl.linear_costs(inst, pads), inst.F.astype(float), inst.D.astype(float)


def test_hand_example_the_descent_by_hand(hand):
    """A–B 5, B–C 1 auf einer Zeile, Start A auf Platz 2, B auf 1, C auf 3 ([1, 0, 2], Kosten 7): die drei Tausche kosten 6 (A↔B), 11 (A↔C), 7 (B↔C); nach A↔B ([0, 1, 2], Kosten 6) verbessert keiner mehr (A↔C kostet 6, gleich)."""
    F, D = hand.F.astype(float), hand.D.astype(float)
    c = np.zeros((3, 3))
    _, _, costs = Pl.swap_costs([1, 0, 2], F, D, c)
    assert sorted(costs.tolist()) == [6.0, 7.0, 11.0]
    d = S.descent_counted([1, 0, 2], F, D, c)
    assert d.perm == [0, 1, 2] and d.cost == 6.0 and d.steps == 1 and d.evals == 6 and d.costs == (7.0, 6.0) and d.swaps == ((0, 1),)
    again = S.descent_counted([0, 1, 2], F, D, c)
    assert again.steps == 0 and again.evals == 3 and again.costs == (6.0,) and again.swaps == ()


def test_descent_is_a_local_optimum_the_costs_fall_and_the_evaluations_are_counted():
    for fam in C.FAMILIES:
        inst, pads, c, F, D = _setup(fam, 8, 100001)
        start = [int(x) for x in np.random.default_rng(1).permutation(8)]
        d = S.descent_counted(start, F, D, c)
        assert Pl.swap_costs(d.perm, F, D, c)[2].min() >= d.cost - 1e-9 and d.cost == pytest.approx(Pl.cost_of(d.perm, F, D, c))
        assert all(d.costs[i + 1] < d.costs[i] for i in range(d.steps)) and len(d.costs) == d.steps + 1 and d.costs[0] == pytest.approx(Pl.cost_of(start, F, D, c))
        assert d.evals == (d.steps + 1) * 28 and sorted(d.perm) == list(range(8)) and len(d.swaps) == d.steps


def test_descent_reproduces_the_best_found_function_and_is_a_permutation_search():
    inst, pads, c, F, D = _setup("uniform", 6, 100002)
    costs = {tuple(p): Pl.cost_of(p, F, D, c) for p in permutations(range(6))}
    for k in range(5):
        start = [int(x) for x in np.random.default_rng(k).permutation(6)]
        d = S.descent_counted(start, F, D, c)
        assert d.cost == pytest.approx(Pl.descent(start, F, D, c)[1]) and d.perm == Pl.descent(start, F, D, c)[0] and d.cost >= min(costs.values()) - 1e-9


def test_temperature_schedule_and_the_budget():
    assert S.temperature(0, 100, 0.5, 0.01, 10.0) == pytest.approx(5.0) and S.temperature(99, 100, 0.5, 0.01, 10.0) == pytest.approx(0.1) and S.temperature(0, 1, 0.5, 0.01, 10.0) == pytest.approx(5.0)
    mid = S.temperature(50, 101, 0.5, 0.01, 10.0)
    assert mid == pytest.approx(math.sqrt(5.0 * 0.1))                                  # geometrisch: das Mittel in der Mitte
    assert [S.budget_for(n) for n in C.SIZES] == [800, 1500, 2000, 3000, 6000] and S.budget_for(8, 2.0) == 3000 and S.budget_for(8, 0.5) == 750 and S.budget_for(6, 0.0001) == 10


def test_annealing_replays_against_a_plain_reimplementation():
    """Dieselben Zufallszahlen, die Annahmeregel von Hand: das Ergebnis des Annealing ist die beste besuchte Anordnung."""
    inst, pads, c, F, D = _setup("cluster", 8, 100003)
    start = [3, 1, 5, 0, 2, 4, 7, 6]
    budget, t0, seed = 400, 0.5, 7
    a = S.anneal(start, F, D, c, budget, t0, seed)
    perm = np.array(start)
    cur = Pl.cost_of(perm, F, D, c)
    _, _, sw = Pl.swap_costs(perm, F, D, c)
    scale = float(np.abs(sw - cur).mean())
    rng = SplitMix64(seed * 7919 + 17)
    best, acc = cur, 0
    for t in range(budget):
        T = t0 * scale * (C.T_END / t0) ** (t / (budget - 1))
        i = rng.below(8)
        j = rng.below(7)
        j = j if j < i else j + 1
        perm[i], perm[j] = perm[j], perm[i]
        new = Pl.cost_of(perm, F, D, c)
        if new - cur <= 0 or rng.random() < math.exp(-(new - cur) / T):
            cur, acc = new, acc + 1
            best = min(best, cur)
        else:
            perm[i], perm[j] = perm[j], perm[i]
    assert a.cost == pytest.approx(best) and a.accepted == acc and a.scale == pytest.approx(scale) and a.moves == budget and a.cost == pytest.approx(Pl.cost_of(a.perm, F, D, c))


def test_annealing_properties_trace_and_determinism():
    inst, pads, c, F, D = _setup("star", 8, 100004)
    start = list(range(8))
    a = S.anneal(start, F, D, c, 600, 2.0, 3)
    b = S.anneal(start, F, D, c, 600, 2.0, 3)
    assert a.perm == b.perm and a.cost == b.cost and a.trace == b.trace and a.cost <= a.start_cost + 1e-9 and 0 <= a.accepted <= 600 and sorted(a.perm) == list(range(8))
    assert a.trace[0][0] == 1 and a.trace[-1][0] == 600 and all(a.trace[i + 1][2] <= a.trace[i][2] + 1e-9 for i in range(len(a.trace) - 1)) and a.trace[-1][2] == pytest.approx(a.cost) and a.trace[0][3] > a.trace[-1][3]
    assert 0 <= a.best_at <= 600 and (a.best_at == 0) == (a.cost == a.start_cost)
    cold = S.anneal(start, F, D, c, 300, 1e-9, 3, t_end=1e-10)
    assert cold.cost <= cold.start_cost and all(t[1] <= cold.start_cost + 1e-9 for t in cold.trace)       # fast eiskalt: nie bergauf
    assert S.anneal(start, F, D, c, 1, 0.5, 3).moves == 1


def test_annealing_does_not_depend_on_rounding_noise_in_the_scale(monkeypatch):
    inst, pads, c, F, D = _setup("uniform", 8, 100005)
    start = [4, 2, 6, 1, 7, 0, 3, 5]
    base = S.anneal(start, F, D, c, 500, 0.5, 11)
    orig = Pl.swap_costs
    monkeypatch.setattr(Pl, "swap_costs", lambda *a, **k: (lambda r: (r[0], r[1], r[2] + 1e-13 * np.arange(len(r[2]))))(orig(*a, **k)))
    noisy = S.anneal(start, F, D, c, 500, 0.5, 11)
    assert noisy.perm == base.perm and noisy.cost == base.cost and noisy.accepted == base.accepted


def test_start_perms_and_restarts():
    inst, pads, c, F, D = _setup("cluster", 8, 46, 4)
    st = S.start_perms(inst, pads, c, 46)
    assert set(st) == set(C.START_CHOICES) and all(sorted(p) == list(range(8)) for p in st.values())
    assert st["round"] == Pl.round_to_slots(inst, Pl.positions(inst, pads, C.ROUND_REWEIGHTS)) and st == S.start_perms(inst, pads, c, 46)
    rs = S.restarts(inst, c, 46)
    assert len(rs) == max(C.RESTART_KS) and all(rs[i + 1][0] > rs[i][0] and rs[i + 1][1] <= rs[i][1] for i in range(len(rs) - 1)) and rs[0][0] % 28 == 0
    ref = Pl.reference(inst, c, 46)[0]
    assert rs[-1][1] >= ref - 1e-9


def test_descent_from_a_good_start_needs_fewer_evaluations_on_average():
    steps = {k: [] for k in C.START_CHOICES}
    for fam in C.FAMILIES:
        for seed in range(100000, 100004):
            inst, pads, c, F, D = _setup(fam, 12, seed, 4)
            for k, p in S.start_perms(inst, pads, c, seed).items():
                steps[k].append(S.descent_counted(p, F, D, c).steps)
    assert np.mean(steps["loop"]) < np.mean(steps["random"]) and np.mean(steps["round"]) < np.mean(steps["random"])


def test_edge_cases():
    inst = I.make_instance("star", 6, 100000)
    pads = Pl.make_pads(inst, 2, 1)
    c = Pl.linear_costs(inst, pads)
    F, D = inst.F.astype(float), inst.D.astype(float)
    z = np.zeros((6, 6))
    d = S.descent_counted(list(range(6)), z, D, np.zeros((6, 6)))
    assert d.steps == 0 and d.cost == 0.0 and d.evals == 15
    a = S.anneal(list(range(6)), z, D, np.zeros((6, 6)), 50, 0.5, 1)
    assert a.cost == 0.0 and a.scale == 1.0 and a.best_at == 0
    two = I.hand_instance([(0, 1, 3)], 1, 2)
    d2 = S.descent_counted([1, 0], two.F.astype(float), two.D.astype(float), np.zeros((2, 2)))
    assert d2.cost == 3.0 and d2.steps == 0 and sorted(d2.perm) == [0, 1]
