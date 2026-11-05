"""Kennzahlen, Vergleiche über Instanzen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Alle Aussagen gelten für die gerechneten Instanzen, die sechs erfundenen Familien, die **erfundenen Pads** (Zahl, Ort, Gewicht, Verbindungen) und die **einfachen** Fassungen dieser Demo (Tauschabstieg, Annealing mit Tauschzügen); Zeiten stehen nie in Verdikten.
Aufwand wird in **Bewertungen** gezählt (Kosten einer Anordnung), nicht in Zeit. Die Lücke ist (Kosten − Vergleichswert) / Vergleichswert; der Vergleichswert ist bis n = 9 das aufgezählte Optimum, ab n = 12 die beste von 100 Abstiegen
(die Lücke ist dann eine **obere** Grenze der wahren Lücke; 0 heißt „so gut wie der Vergleichswert“)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import dtp_constants as C
import dtp_place as Pl
import dtp_search as S
from dtp_instance import hand_instance, make_instance


@dataclass(frozen=True)
class Settings:
    family: str = C.DEFAULT_FAMILY
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    pads: int = C.DEFAULT_PADS
    start: str = C.DEFAULT_START
    method: str = C.DEFAULT_METHOD
    t0: float = C.DEFAULT_T0
    budget: float = C.DEFAULT_BUDGET_FACTOR


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return de(100.0 * x, digits) + " %"


def fam(name: str) -> str:
    return C.FAMILY_NAMES.get(name, name)


def num(x: float) -> str:
    """Ganze Zahl ohne Nachkommastelle, sonst eine Stelle: 27 / 27,5 / −12,1."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else de(x, 1)


def count(x: float) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 1200 → „1 200“."""
    return C.n_text(int(round(x)))


def rel(a: float, b: float) -> float:
    """(a − b) / b; NaN, wenn b = 0; Rundungsreste unter 1e-12 werden zu 0."""
    if not b:
        return float("nan")
    r = (a - b) / b
    return 0.0 if abs(r) < 1e-12 else r


def median_of(rows: list, key: str) -> float:
    return float(np.median([r[key] for r in rows]))


def tx(x: float) -> str:
    """Zahl mit Dezimalkomma ohne überflüssige Nullen: 0,1 / 0,5 / 2."""
    return de(x, 2).rstrip("0").rstrip(",")


def schritte(k: int) -> str:
    return f"{k} Schritt" if k == 1 else f"{k} Schritte"


def schritten(k: int) -> str:
    return f"{k} Schritt" if k == 1 else f"{k} Schritten"


def neustarts(k: int) -> str:
    return "1 Neustart" if k == 1 else f"{k} Neustarts"


# ----------------------------------------------------------------------------- eine Instanz

def instance_data(s: Settings) -> dict:
    """Instanz, Pads, Vergleichswert, die drei Startlösungen mit ihrem Abstieg und ihrem Annealing (Starttemperatur und Zugzahl nach den Einstellungen) und die Neustarts aus Zufall."""
    inst = make_instance(s.family, s.n, s.seed)
    pads = Pl.make_pads(inst, s.pads, s.seed, C.DEFAULT_FACTOR)
    c = Pl.linear_costs(inst, pads)
    ref, perm_ref, exact, mean = Pl.reference(inst, c, s.seed)
    F, D = inst.F.astype(float), inst.D.astype(float)
    starts = S.start_perms(inst, pads, c, s.seed)
    budget = S.budget_for(s.n, s.budget)
    descents = {k: S.descent_counted(p, F, D, c) for k, p in starts.items()}
    anneals = {k: S.anneal(p, F, D, c, budget, s.t0, s.seed) for k, p in starts.items()}
    return {"inst": inst, "pads": pads, "c": c, "ref": ref, "ref_perm": perm_ref, "exact": exact, "mean": mean, "gap_mean": rel(mean, ref) if mean is not None else None, "starts": starts,
            "start_costs": {k: Pl.cost_of(p, F, D, c) for k, p in starts.items()}, "descents": descents, "anneals": anneals, "budget": budget, "restarts": S.restarts(inst, c, s.seed)}


def main_result(s: Settings, v: dict):
    """Ergebnis der gewählten Startlösung mit dem gewählten Verfahren: (Anordnung, Kosten, Bewertungen)."""
    if s.method == "descent":
        d = v["descents"][s.start]
        return d.perm, d.cost, d.evals
    a = v["anneals"][s.start]
    return a.perm, a.cost, a.moves


# ----------------------------------------------------------------------------- Zeilen für die Vergleiche

def row_of(family: str, n: int, seed: int, p: int) -> dict:
    """Eine Instanz: Start, Abstieg (Kosten, Schritte, Bewertungen) aus jeder Startlösung, Annealing heiß aus Zufall und kalt aus der Schleife, Neustarts aus Zufall."""
    inst = make_instance(family, n, seed)
    pads = Pl.make_pads(inst, p, seed, C.DEFAULT_FACTOR)
    c = Pl.linear_costs(inst, pads)
    ref, _, exact, mean = Pl.reference(inst, c, seed)
    F, D = inst.F.astype(float), inst.D.astype(float)
    starts = S.start_perms(inst, pads, c, seed)
    budget = S.budget_for(n)
    row = {"family": family, "n": n, "seed": seed, "p": p, "ref": ref, "exact": exact, "gap_mean": rel(mean, ref) if mean is not None else float("nan"), "budget": budget}
    for k, perm in starts.items():
        d = S.descent_counted(perm, F, D, c)
        row[k] = {"start": rel(Pl.cost_of(perm, F, D, c), ref), "desc": rel(d.cost, ref), "steps": d.steps, "evals": d.evals, "hit": d.cost <= ref + 1e-9, "better": d.cost < d.costs[0] - 1e-9}
    row["sa_random"] = S.anneal(starts["random"], F, D, c, budget, C.SA_RANDOM_T0, seed)
    row["sa_loop"] = S.anneal(starts["loop"], F, D, c, budget, C.SA_LOOP_T0, seed)
    row["sa_random"], row["sa_loop"] = ({"gap": rel(a.cost, ref), "hit": a.cost <= ref + 1e-9, "accepted": a.accepted / a.moves} for a in (row["sa_random"], row["sa_loop"]))
    rs = S.restarts(inst, c, seed)
    row["restarts"] = {k: {"gap": rel(rs[k - 1][1], ref), "evals": rs[k - 1][0], "hit": rs[k - 1][1] <= ref + 1e-9} for k in C.RESTART_KS}
    return row


def sweep(family: str, n: int, seeds, pads_list) -> list:
    return [row_of(family, n, s, p) for s in seeds for p in pads_list]


def pooled(by_family: dict) -> list:
    return [r for f in C.FAMILIES if f in by_family for r in by_family[f]]


def start_summary(rows: list, p, start: str) -> dict:
    """Median von Start, Abstieg, Schritten und Bewertungen für die Zeilen mit `p` Pads (p = None: alle)."""
    rs = [r for r in rows if p is None or r["p"] == p]
    return {"count": len(rs), "start": median_of([r[start] for r in rs], "start"), "desc": median_of([r[start] for r in rs], "desc"), "steps": median_of([r[start] for r in rs], "steps"), "evals": median_of([r[start] for r in rs], "evals"),
            "hit": sum(r[start]["hit"] for r in rs), "better": sum(r[start]["better"] for r in rs)}


def sa_summary(rows: list, p, key: str) -> dict:
    rs = [r for r in rows if p is None or r["p"] == p]
    return {"count": len(rs), "gap": median_of([r[key] for r in rs], "gap"), "hit": sum(r[key]["hit"] for r in rs), "accepted": median_of([r[key] for r in rs], "accepted")}


def restart_summary(rows: list, k: int) -> dict:
    return {"count": len(rows), "gap": median_of([r["restarts"][k] for r in rows], "gap"), "evals": median_of([r["restarts"][k] for r in rows], "evals"), "hit": sum(r["restarts"][k]["hit"] for r in rows)}


def mean_gap(rows: list, p: int) -> float:
    return median_of([r for r in rows if r["p"] == p], "gap_mean")


# ----------------------------------------------------------------------------- Verdikte

def _head(s: Settings, v: dict) -> str:
    inst = v["inst"]
    return f"Familie **{fam(s.family)}**, {s.n} Bauteile, Raster {inst.rows}×{inst.cols}, Seed {s.seed}, {s.pads} Pads"


def _refname(v: dict) -> str:
    return "das aufgezählte Optimum" if v["exact"] else "die beste von 100 Abstiegen (obere Grenze)"


def verdict_descent(s: Settings, v: dict):
    """Der Tauschabstieg aus der gewählten Startlösung."""
    d = v["descents"][s.start]
    g0, g1 = rel(d.costs[0], v["ref"]), rel(d.cost, v["ref"])
    if d.steps == 0:
        return "info", (f"{_head(s, v)}, Start {C.START_NAMES[s.start]}: die Startanordnung (Kosten {num(d.cost)}, Lücke {pct(g0, 1)} gegen {_refname(v)} {num(v['ref'])}) ist schon ein **lokales Optimum der Tauschnachbarschaft**; der Abstieg prüft {count(d.evals)} Bewertungen und bewegt sich nicht.")
    kind = "success" if d.cost <= v["ref"] + 1e-9 else "info"
    return kind, (f"{_head(s, v)}, Start {C.START_NAMES[s.start]}: der Abstieg braucht **{schritte(d.steps)}** und {count(d.evals)} Bewertungen; die Kosten sinken von {num(d.costs[0])} (Lücke {pct(g0, 1)}) auf **{num(d.cost)}** (Lücke {pct(g1, 1)}) gegen {_refname(v)} {num(v['ref'])}"
                  + ("; das ist der Vergleichswert." if d.cost <= v["ref"] + 1e-9 else "; ein lokales Optimum der Tauschnachbarschaft, aber nicht der Vergleichswert."))


def verdict_starts(s: Settings, v: dict):
    """Die drei Startlösungen und ihr Abstieg."""
    parts = []
    for k in C.START_CHOICES:
        d = v["descents"][k]
        parts.append(f"{C.START_NAMES[k]}: Start {num(d.costs[0])} (Lücke {pct(rel(d.costs[0], v['ref']), 1)}) → Abstieg {num(d.cost)} (Lücke {pct(rel(d.cost, v['ref']), 1)}) in {schritten(d.steps)} und {count(d.evals)} Bewertungen")
    return "info", f"{_head(s, v)}, Vergleichswert {num(v['ref'])} ({_refname(v)}): " + "; ".join(parts) + ". Eine Instanz, kein Befund über die Familie."


def verdict_anneal(s: Settings, v: dict):
    """Annealing aus der gewählten Startlösung."""
    a, d = v["anneals"][s.start], v["descents"][s.start]
    kind = "success" if a.cost <= v["ref"] + 1e-9 else "info"
    cmp = ("besser als" if a.cost < d.cost - 1e-9 else ("gleich" if abs(a.cost - d.cost) < 1e-9 else "schlechter als")) + f" der Abstieg aus derselben Startlösung ({num(d.cost)} in {count(d.evals)} Bewertungen)"
    return kind, (f"{_head(s, v)}, Start {C.START_NAMES[s.start]}, Starttemperatur {tx(s.t0)} · s mit s = {de(a.scale, 1)}: {count(a.moves)} Züge, {pct(a.accepted / a.moves)} angenommen; die beste Anordnung (Kosten **{num(a.cost)}**, Lücke {pct(rel(a.cost, v['ref']), 1)} gegen {_refname(v)} {num(v['ref'])}) "
                  f"{'blieb die Startanordnung' if a.best_at == 0 else 'wurde in Zug ' + count(a.best_at) + ' gefunden'}; {cmp}.")


def verdict_effort(s: Settings, v: dict):
    """Neustarts aus Zufall gegen Abstieg und Annealing aus guter Startlösung bei der gewählten Instanz."""
    parts = []
    for k in C.RESTART_KS:
        ev, best = v["restarts"][k - 1]
        parts.append(f"{neustarts(k)}: Kosten {num(best)} (Lücke {pct(rel(best, v['ref']), 1)}) bei {count(ev)} Bewertungen")
    d = v["descents"]["loop"]
    a = v["anneals"]["loop"]
    return "info", (f"{_head(s, v)}: Neustarts aus Zufall: " + "; ".join(parts) + f". Abstieg aus der Schleife: Kosten {num(d.cost)} (Lücke {pct(rel(d.cost, v['ref']), 1)}) bei {count(d.evals)} Bewertungen; Annealing aus der Schleife (Starttemperatur {tx(s.t0)} · s): "
                    f"Kosten {num(a.cost)} (Lücke {pct(rel(a.cost, v['ref']), 1)}) bei {count(a.moves)} Bewertungen.")


def verdict_sweep_starts(n: int, rows: list):
    """Abstieg aus den drei Startlösungen über feste Instanzen, Median über alle Pad-Zahlen."""
    exact = rows[0]["exact"]
    parts = []
    for k in C.START_CHOICES:
        sm = start_summary(rows, None, k)
        parts.append(f"{C.START_NAMES[k]}: Start {pct(sm['start'], 1)} → Abstieg {pct(sm['desc'], 1)} ({de(sm['steps'], 0)} Schritte, {count(sm['evals'])} Bewertungen, Vergleichswert erreicht in {sm['hit']} von {sm['count']})")
    return "info", (f"Bei n = {n}, Median über {len(rows)} Instanzen (alle Pad-Zahlen): " + "; ".join(parts) + "." + ("" if exact else " Der Vergleichswert ist die beste von 100 Abstiegen: obere Grenze der Lücke; „erreicht“ heißt gleich oder besser."))


def verdict_sweep_anneal(n: int, rows: list):
    """Annealing heiß aus Zufall und kalt aus der Schleife gegen den Abstieg aus der Schleife."""
    r, lo = sa_summary(rows, None, "sa_random"), sa_summary(rows, None, "sa_loop")
    d = start_summary(rows, None, "loop")
    return "info", (f"Bei n = {n}, Median über {len(rows)} Instanzen: Annealing aus Zufall (Starttemperatur {tx(C.SA_RANDOM_T0)} · s, {count(rows[0]['budget'])} Züge) Lücke {pct(r['gap'], 1)}, Vergleichswert erreicht in {r['hit']}; "
                    f"Annealing aus der Schleife (Starttemperatur {tx(C.SA_LOOP_T0)} · s) Lücke {pct(lo['gap'], 1)}, erreicht in {lo['hit']}; Abstieg aus der Schleife Lücke {pct(d['desc'], 1)}, erreicht in {d['hit']}.")


def verdict_sweep_restarts(n: int, rows: list):
    """Neustarts aus Zufall bei gleichem Aufwand."""
    parts = []
    for k in C.RESTART_KS:
        sm = restart_summary(rows, k)
        parts.append(f"{k}: Lücke {pct(sm['gap'], 1)} bei {count(sm['evals'])} Bewertungen")
    loop = start_summary(rows, None, "loop")
    return "info", (f"Bei n = {n}, beste von 1 / 3 / 6 / 20 Abstiegen aus Zufallsstarts, Median über {len(rows)} Instanzen: " + "; ".join(parts) + f". Zum Vergleich ein Abstieg aus der Schleife: Lücke {pct(loop['desc'], 1)} bei {count(loop['evals'])} Bewertungen.")


def verdict_core(s: Settings, v: dict):
    perm, cost, evals = main_result(s, v)
    d = v["descents"][s.start]
    return "info", (f"Die Detailplatzierung tauscht Bauteile auf einer legalen Anordnung: bei {_head(s, v)} bringt {C.METHOD_NAMES[s.method]} aus der Startlösung {C.START_NAMES[s.start]} die Kosten von {num(d.costs[0])} auf {num(cost)} "
                    f"(Lücke {pct(rel(d.costs[0], v['ref']), 1)} → {pct(rel(cost, v['ref']), 1)} gegen {_refname(v)} {num(v['ref'])}) mit {count(evals)} Bewertungen. Wie sich Startlösungen, Annealing und Neustarts unterscheiden und wie es bei vielen Instanzen aussieht: Experiment 1 bis 5.")


# ----------------------------------------------------------------------------- Handbeispiel

def hand_data() -> dict:
    """Drei Bauteile auf einer Zeile (Fluss A–B 5, B–C 1), Start A auf Platz 2, B auf 1, C auf 3 (Plätze 1, 2, 3, hier 0-basiert [1, 0, 2]): der Abstieg von Hand."""
    inst = hand_instance()
    F, D = inst.F.astype(float), inst.D.astype(float)
    c = np.zeros((3, 3))
    d = S.descent_counted([1, 0, 2], F, D, c)
    return {"inst": inst, "descent": d}
