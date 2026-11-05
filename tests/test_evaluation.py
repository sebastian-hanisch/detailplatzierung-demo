"""Zeilen für die Vergleiche, Zusammenfassungen und Instanzdaten: Handwerte und Eigenschaften."""

import math

import numpy as np
import pytest

import dtp_constants as C
import dtp_evaluation as ev
import dtp_instance as I
import dtp_place as Pl
import dtp_search as S


def test_helpers():
    assert ev.de(-1.5, 1) == "−1,5" and ev.pct(0.266, 1) == "26,6 %" and ev.fam("star") == "Stern" and ev.num(27.0) == "27" and ev.num(26.5) == "26,5" and ev.count(3024) == "3 024" and ev.schritte(1) == "1 Schritt" and ev.schritte(3) == "3 Schritte"
    assert ev.schritten(1) == "1 Schritt" and ev.schritten(2) == "2 Schritten" and ev.neustarts(1) == "1 Neustart" and ev.neustarts(3) == "3 Neustarts"
    assert ev.rel(110, 100) == pytest.approx(0.1) and math.isnan(ev.rel(5, 0)) and ev.rel(100 + 1e-14, 100) == 0.0 and ev.median_of([{"v": 1}, {"v": 5}, {"v": 2}], "v") == 2.0


def test_instance_data_for_an_enumerated_and_a_large_size():
    s = ev.Settings("netlist", 6, 35, 4)
    v = ev.instance_data(s)
    inst = v["inst"]
    assert v["exact"] and set(v["starts"]) == set(C.START_CHOICES) == set(v["descents"]) == set(v["anneals"]) and v["ref"] == Pl.reference(inst, v["c"], 35)[0] and v["budget"] == 800 and len(v["restarts"]) == 20
    assert all(d.cost >= v["ref"] - 1e-9 and d.costs[0] == pytest.approx(v["start_costs"][k]) for k, d in v["descents"].items()) and all(a.cost >= v["ref"] - 1e-9 and a.moves == 800 for a in v["anneals"].values())
    assert v["gap_mean"] > 0
    big = ev.instance_data(ev.Settings("sparse", 12, 100000, 2, budget=0.5))
    assert not big["exact"] and big["mean"] is None and big["gap_mean"] is None and big["budget"] == 1500 and sorted(big["ref_perm"]) == list(range(12))


def test_main_result_follows_the_method():
    s = ev.Settings("cluster", 6, 100000, 4, "round", "descent")
    v = ev.instance_data(s)
    perm, cost, evals = ev.main_result(s, v)
    assert perm == v["descents"]["round"].perm and cost == v["descents"]["round"].cost and evals == v["descents"]["round"].evals
    s2 = ev.Settings("cluster", 6, 100000, 4, "random", "anneal", 2.0)
    v2 = ev.instance_data(s2)
    perm, cost, evals = ev.main_result(s2, v2)
    assert perm == v2["anneals"]["random"].perm and cost == v2["anneals"]["random"].cost and evals == 800


def test_row_of_and_the_summaries():
    rows = ev.sweep("sparse", 6, (100000, 100001, 100002), (2, 8))
    assert len(rows) == 6 and all(r["exact"] and r["budget"] == 800 for r in rows)
    r = rows[0]
    inst = I.make_instance("sparse", 6, 100000)
    pads = Pl.make_pads(inst, 2, 100000)
    c = Pl.linear_costs(inst, pads)
    F, D = inst.F.astype(float), inst.D.astype(float)
    ref = Pl.reference(inst, c, 100000)[0]
    st = S.start_perms(inst, pads, c, 100000)
    d = S.descent_counted(st["loop"], F, D, c)
    assert r["ref"] == ref and r["loop"]["desc"] == pytest.approx((d.cost - ref) / ref) and r["loop"]["steps"] == d.steps and r["loop"]["evals"] == d.evals and r["loop"]["hit"] == (d.cost <= ref + 1e-9)
    assert r["sa_loop"]["gap"] == pytest.approx((S.anneal(st["loop"], F, D, c, 800, C.SA_LOOP_T0, 100000).cost - ref) / ref)
    rs = S.restarts(inst, c, 100000)
    assert r["restarts"][3]["evals"] == rs[2][0] and r["restarts"][3]["gap"] == pytest.approx((rs[2][1] - ref) / ref) and set(r["restarts"]) == set(C.RESTART_KS)
    sm = ev.start_summary(rows, 2, "loop")
    assert sm["count"] == 3 and sm["desc"] == float(np.median([x["loop"]["desc"] for x in rows if x["p"] == 2])) and sm["hit"] <= 3 and sm["better"] <= 3
    assert ev.start_summary(rows, None, "random")["count"] == 6 and ev.sa_summary(rows, None, "sa_loop")["count"] == 6 and 0 <= ev.sa_summary(rows, 2, "sa_random")["accepted"] <= 1
    rsum = ev.restart_summary(rows, 6)
    assert rsum["count"] == 6 and rsum["gap"] <= ev.restart_summary(rows, 1)["gap"] + 1e-12 and rsum["evals"] > ev.restart_summary(rows, 1)["evals"] and ev.mean_gap(rows, 2) > 0
    assert len(ev.pooled({"sparse": rows, "star": rows})) == 12


def test_hand_data():
    h = ev.hand_data()["descent"]
    assert h.perm == [0, 1, 2] and h.cost == 6.0 and h.steps == 1 and h.evals == 6 and h.costs == (7.0, 6.0)
