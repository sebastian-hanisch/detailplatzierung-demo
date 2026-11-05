"""Orakel (ORACLE-PLAYBOOK §5): die Aufzählung aller Anordnungen für das Optimum; eine zweite, unabhängig geschriebene Kostenrechnung für jeden Tausch; `scipy` für die Zuordnung der Startlösung.
Ohne scipy (nur requirements-dev.txt; die App braucht scipy nicht) werden die scipy-Tests übersprungen."""

from itertools import permutations

import numpy as np
import pytest

import dtp_constants as C
import dtp_instance as I
import dtp_place as Pl
import dtp_search as S


def independent_cost(perm, inst, pads):
    """Kosten einer Anordnung als einfache Doppelschleife (ohne Matrixschreibweise): Σ_{i<k} F·|Δ|₁ + Σ_{i,Pad} w·|Δ|₁."""
    xy = inst.xy
    total = 0.0
    for i in range(inst.n):
        for k in range(i + 1, inst.n):
            total += float(inst.F[i, k]) * (abs(int(xy[perm[i]][0]) - int(xy[perm[k]][0])) + abs(int(xy[perm[i]][1]) - int(xy[perm[k]][1])))
        for j in range(pads.count):
            total += float(pads.w[i, j]) * (abs(xy[perm[i]][0] - pads.pos[j][0]) + abs(xy[perm[i]][1] - pads.pos[j][1]))
    return total


@pytest.mark.parametrize("family", C.FAMILIES)
def test_every_swap_cost_equals_the_independent_cost_and_the_descent_ends_in_a_local_optimum(family):
    inst = I.make_instance(family, 8, 100006)
    pads = Pl.make_pads(inst, 4, 100006)
    c = Pl.linear_costs(inst, pads)
    F, D = inst.F.astype(float), inst.D.astype(float)
    start = S.start_perms(inst, pads, c, 100006)["random"]
    ia, ib, cost = Pl.swap_costs(start, F, D, c)
    for k in range(len(ia)):
        q = list(start)
        q[ia[k]], q[ib[k]] = q[ib[k]], q[ia[k]]
        assert cost[k] == pytest.approx(independent_cost(q, inst, pads))
    d = S.descent_counted(start, F, D, c)
    assert d.cost == pytest.approx(independent_cost(d.perm, inst, pads)) and d.costs[0] == pytest.approx(independent_cost(start, inst, pads))
    for a in range(8):
        for b in range(a + 1, 8):
            q = list(d.perm)
            q[a], q[b] = q[b], q[a]
            assert independent_cost(q, inst, pads) >= d.cost - 1e-9


def test_no_method_beats_the_enumerated_optimum():
    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 6, 100007)
        for p in C.PAD_CHOICES:
            pads = Pl.make_pads(inst, p, 100007)
            c = Pl.linear_costs(inst, pads)
            F, D = inst.F.astype(float), inst.D.astype(float)
            ref = min(independent_cost(q, inst, pads) for q in permutations(range(6)))
            assert ref == pytest.approx(Pl.reference(inst, c, 100007)[0])
            for st in S.start_perms(inst, pads, c, 100007).values():
                assert S.descent_counted(st, F, D, c).cost >= ref - 1e-9
                for t0 in C.T0_CHOICES:
                    assert S.anneal(st, F, D, c, 200, t0, 3).cost >= ref - 1e-9
            assert all(b >= ref - 1e-9 for _, b in S.restarts(inst, c, 100007, 5))


def test_the_rounded_start_is_an_optimal_assignment_for_scipy():
    opt = pytest.importorskip("scipy.optimize")
    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 8, 100008)
        pads = Pl.make_pads(inst, 4, 100008)
        X = Pl.positions(inst, pads, C.ROUND_REWEIGHTS)
        perm = S.start_perms(inst, pads, Pl.linear_costs(inst, pads), 100008)["round"]
        d2 = ((X[:, None, :] - inst.xy[None, :, :].astype(float)) ** 2).sum(axis=2)
        r, cc = opt.linear_sum_assignment(d2)
        assert d2[np.arange(8), perm].sum() == pytest.approx(d2[r, cc].sum(), abs=1e-6)
