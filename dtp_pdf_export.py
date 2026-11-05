"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import dtp_constants as C
from dtp_evaluation import Settings, count, main_result, num, pct, rel, tx

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "³": "3", "⁻": "-", "¹": "1", "½": "1/2", "⁴": "4"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, v: dict) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Detailplatzierung: Tausch und Annealing"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    inst = v["inst"]
    how = "alle Anordnungen aufgezählt" if v["exact"] else "nicht aufgezählt, beste von 100 Abstiegen als Vergleich (obere Grenze)"
    pdf.multi_cell(0, 5, _s(f"Familie {C.FAMILY_NAMES[s.family]}, {s.n} Bauteile, {inst.rows}x{inst.cols}-Raster, Seed {s.seed}; {s.pads} Pads; Startlösung {C.START_NAMES[s.start]}; Verfahren {C.METHOD_NAMES[s.method]}; Starttemperatur {tx(s.t0)} * s; Zugzahl x{tx(s.budget)}; {how}. "
                            "Eine Instanz, kein Befund über die Familie. Erfundene Pads, einfache Fassungen. Aufwand in Bewertungen, nicht in Zeit. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in ((45, "Startlösung"), (25, "Start"), (30, "Abstieg"), (30, "Annealing"), (30, "Bewertungen (Abstieg)")):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for k in C.START_CHOICES:
        d, a = v["descents"][k], v["anneals"][k]
        pdf.cell(45, 5.5, _s(C.START_NAMES[k]), border=1)
        pdf.cell(25, 5.5, _s(f"{num(d.costs[0])} ({pct(rel(d.costs[0], v['ref']), 1)})"), border=1)
        pdf.cell(30, 5.5, _s(f"{num(d.cost)} ({pct(rel(d.cost, v['ref']), 1)})"), border=1)
        pdf.cell(30, 5.5, _s(f"{num(a.cost)} ({pct(rel(a.cost, v['ref']), 1)})"), border=1)
        pdf.cell(30, 5.5, _s(count(d.evals)), border=1)
        pdf.ln()
    pdf.ln(3)
    perm, cost, evals = main_result(s, v)
    ref_name = "Optimum (aufgezählt)" if v["exact"] else "Beste gefundene Lösung (obere Grenze)"
    pdf.multi_cell(0, 5, _s(f"{ref_name}: {num(v['ref'])}. Gewähltes Verfahren aus der gewählten Startlösung: Kosten {num(cost)} (Lücke {pct(rel(cost, v['ref']), 1)}), {count(evals)} Bewertungen."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: detailplatzierung-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
