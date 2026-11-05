"""Detailplatzierung: Tauschabstieg und Simulated Annealing mit Tauschzügen auf einer legalen Anordnung, Startlösungen aus den Stücken 9 und 10, Neustarts, Zählung der Bewertungen.

Kosten wie in Stück 9 und 10: cost(p) = Σ_{i<k} F[i,k] · |p_i − p_k|₁ + Σ_{i,Pad} w · |p_i − Pad|₁ (Kern in `dtp_place.py`). Gezählt wird die **Zahl der Bewertungen** (Kosten einer Anordnung):
ein Schritt des Abstiegs bewertet alle n(n−1)/2 Vertauschungen (in einem Stapel), ein Zug des Annealing eine Anordnung. Das ist ein Maß der Rechenarbeit in dieser Fassung, kein Zeitmaß.
**Tauschabstieg:** steilster Abstieg über alle Vertauschungen zweier Bauteile; bei Gleichstand gewinnt die erste Vertauschung (kleinster Index). **Annealing:** zufällige Vertauschung (SplitMix64), Annahme mit e^(−Δ/T),
Temperatur geometrisch von t0 · s auf t_end · s (s = mittlerer Betrag der Kostenänderung aller Vertauschungen der Startanordnung), beste besuchte Anordnung."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import dtp_constants as C
import dtp_loop as Lp
import dtp_place as Pl
from dtp_rng import SplitMix64


@dataclass(frozen=True, eq=False)
class Descent:
    perm: list
    cost: float
    steps: int
    evals: int
    costs: tuple              # Kosten vor dem ersten und nach jedem Schritt (Länge steps + 1)
    swaps: tuple              # die getauschten Bauteile je Schritt


def descent_counted(perm, F, D, c) -> Descent:
    """Steilster Tauschabstieg mit Zählung: bis kein Tausch mehr die Kosten senkt."""
    F, D = np.asarray(F, dtype=float), np.asarray(D, dtype=float)
    perm = np.array(perm, dtype=np.intp)
    cur = Pl.cost_of(perm, F, D, c)
    costs, swaps, evals = [cur], [], 0
    while True:
        ia, ib, cost = Pl.swap_costs(perm, F, D, c)
        evals += len(ia)
        k = int(cost.argmin())
        if cost[k] < cur - 1e-9:
            perm[ia[k]], perm[ib[k]] = perm[ib[k]], perm[ia[k]]
            cur = float(cost[k])
            costs.append(cur)
            swaps.append((int(ia[k]), int(ib[k])))
        else:
            return Descent([int(x) for x in perm], cur, len(swaps), evals, tuple(costs), tuple(swaps))


@dataclass(frozen=True, eq=False)
class Anneal:
    perm: list                # beste besuchte Anordnung
    cost: float
    start_cost: float
    moves: int
    accepted: int
    scale: float              # s: mittlerer Betrag der Kostenänderung aller Vertauschungen der Startanordnung
    t0: float
    trace: tuple              # (Zug, aktuelle Kosten, beste Kosten, Temperatur) an gleichmäßig verteilten Zügen
    best_at: int              # Zug, in dem die beste Anordnung gefunden wurde


def temperature(t: int, budget: int, t0: float, t_end: float, scale: float) -> float:
    """Geometrischer Plan von t0·s (Zug 0) auf t_end·s (letzter Zug)."""
    T0, T1 = t0 * scale, t_end * scale
    return T0 * (T1 / T0) ** (t / max(budget - 1, 1))


def anneal(perm, F, D, c, budget: int, t0: float, seed: int, t_end: float = C.T_END, samples: int = 60) -> Anneal:
    """Simulated Annealing mit Tauschzügen; `budget` Züge (= Bewertungen)."""
    F, D = np.asarray(F, dtype=float), np.asarray(D, dtype=float)
    perm = np.array(perm, dtype=np.intp)
    n = len(perm)
    cur = Pl.cost_of(perm, F, D, c)
    start = cur
    _, _, costs = Pl.swap_costs(perm, F, D, c)
    scale = float(np.abs(costs - cur).mean()) or 1.0
    rng = SplitMix64(seed * 7919 + 17)
    best, bestp, accepted, best_at = cur, perm.copy(), 0, 0
    every = max(budget // samples, 1)
    trace = []
    for t in range(budget):
        T = temperature(t, budget, t0, t_end, scale)
        a = rng.below(n)
        b = rng.below(n - 1)
        b = b if b < a else b + 1
        perm[a], perm[b] = perm[b], perm[a]
        new = Pl.cost_of(perm, F, D, c)
        d = new - cur
        if d <= 0 or rng.random() < math.exp(-d / T):
            cur = new
            accepted += 1
            if cur < best - 1e-9:
                best, bestp, best_at = cur, perm.copy(), t + 1
        else:
            perm[a], perm[b] = perm[b], perm[a]
        if t % every == 0 or t == budget - 1:
            trace.append((t + 1, cur, best, T))
    return Anneal([int(x) for x in bestp], best, start, budget, accepted, scale, t0, tuple(trace), best_at)


def budget_for(n: int, factor: float = C.DEFAULT_BUDGET_FACTOR) -> int:
    return max(int(round(C.BUDGETS[n] * factor)), 10)


def start_perms(inst, pads, c, seed: int) -> dict:
    """Startanordnungen: Zufall (SplitMix64), Rundung der Platzierung mit zwei Umgewichtungen (Stück 9), Ergebnis der Schleife aus Stück 10 (Zuordnung, 15 Runden, c = 0,2, zwei Umgewichtungen)."""
    rng = SplitMix64(seed * 31 + 5)
    rnd = list(range(inst.n))
    rng.shuffle(rnd)
    rounded = Pl.round_to_slots(inst, Pl.positions(inst, pads, C.ROUND_REWEIGHTS))
    loop = Lp.run_loop(inst, pads, c, "assign", C.LOOP_ROUNDS, C.LOOP_REWEIGHTS, C.LOOP_ANCHOR).rounds[-1].perm
    return {"random": rnd, "round": rounded, "loop": loop}


def restarts(inst, c, seed: int, k_max: int = max(C.RESTART_KS)) -> list:
    """Abstiege aus Zufallsstarts (SplitMix64): je Neustart (Gesamtbewertungen bis dahin, bester Wert bis dahin)."""
    F, D = np.asarray(inst.F, dtype=float), np.asarray(inst.D, dtype=float)
    rng = SplitMix64(seed * 977 + 3)
    out, evals, best = [], 0, None
    for _ in range(k_max):
        st = list(range(inst.n))
        rng.shuffle(st)
        d = descent_counted(st, F, D, c)
        evals += d.evals
        best = d.cost if best is None else min(best, d.cost)
        out.append((evals, best))
    return out
