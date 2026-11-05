"""Konstanten: Größen, Raster, Familien der Flussmatrix, feste Reihen der Experimente, Farben und Presets."""

EXACT_SIZES = (6, 8, 9)                               # alle n! Anordnungen werden aufgezählt: das Optimum ist bekannt
LARGE_SIZES = (12, 16)                                # nicht aufgezählt: die beste von 100 Abstiegen aus Zufallsstarts ersetzt das Optimum
SIZES = EXACT_SIZES + LARGE_SIZES
DEFAULT_N = 8
SWEEP_N = 8                                           # Vergleich über feste Instanzen mit aufgezähltem Optimum
LARGE_SWEEP_SIZES = (12, 16)                          # Vergleiche gegen die beste gefundene Lösung
GRID = {6: (2, 3), 8: (2, 4), 9: (3, 3), 12: (3, 4), 16: (4, 4)}    # Plätze als Raster (Zeilen, Spalten), Abstand = Manhattan
SEED_MAX, DEFAULT_SEED = 999999, 46
SWEEP_SEEDS = tuple(range(100000, 100020))            # feste Instanzen: nie ein einzelner Seed als Befund
LARGE_SEEDS = {12: SWEEP_SEEDS[:5], 16: SWEEP_SEEDS[:3]}   # n = 12: fünf, n = 16: drei Instanzen je Familie
STARTS = 100                                          # Zahl der steilsten Abstiege aus Zufallsstarts für die beste gefundene Lösung (ab n = 12)

PAD_CHOICES = (2, 4, 8)                               # Zahl der festen Pads (Anker) auf dem Ring um das Raster
DEFAULT_PADS = 4
PAD_LINKS = 2                                         # jedes Pad hängt an so vielen zufälligen Bauteilen
DEFAULT_FACTOR = 1.0                                  # Pad-Gewicht = Faktor · Grundgewicht (Median der positiven Flüsse, mindestens 1); fest
EPS = 0.3                                             # untere Grenze der Länge in der Umgewichtung F / max(|Δ|, EPS) (in Platzabständen)
CENTER_ANCHOR = 1e-6                                  # schwacher Anker in der Mitte: Bauteile ohne Weg zu einem Pad fallen auf einen Punkt, das System bleibt lösbar
RING_MARGIN = 1.5                                     # Abstand des Pad-Rings vom Raster der Plätze (in Platzabständen)
TIE_DECIMALS = 8                                      # Stellen (relativ zum größten Betrag), auf die Abstandsquadrate und Koordinaten vor Zuordnung und Sortierung gerundet werden
LOOP_ROUNDS, LOOP_REWEIGHTS, LOOP_ANCHOR = 15, 2, 0.2  # die Schleife aus Stück 10 (Zuordnung), aus der die Startlösung „Schleife“ kommt
DEFAULT_ROUNDS, DEFAULT_REWEIGHTS, DEFAULT_ANCHOR = LOOP_ROUNDS, LOOP_REWEIGHTS, LOOP_ANCHOR
ROUND_REWEIGHTS = 2                                   # Umgewichtungen der Platzierung für die Startlösung „Rundung“ (Stück 9)
FACTOR_CHOICES = (0.25, 1.0, 4.0, 16.0)               # Faktoren auf das Pad-Gewicht, nur für Kern-Tests (aus Stück 9)
ANCHOR_CHOICES = (0.02, 0.2, 1.0)                     # nur für die Kern-Tests der Schleife (aus Stück 10)
REWEIGHT_CHOICES = (0, 2)
LEGALIZERS = ("assign", "bisect")
DEFAULT_LEGALIZER = "assign"

START_CHOICES = ("random", "round", "loop")           # Startlösungen für die Detailplatzierung
START_NAMES = {"random": "Zufall", "round": "Rundung (Stück 9)", "loop": "Schleife (Stück 10)"}
DEFAULT_START = "loop"
METHODS = ("descent", "anneal")
METHOD_NAMES = {"descent": "Tauschabstieg", "anneal": "Simulated Annealing"}
DEFAULT_METHOD = "descent"
T0_CHOICES = (0.1, 0.5, 2.0)                          # Starttemperatur in Vielfachen von s (mittlerer Betrag der Kostenänderung aller Tausche der Startanordnung)
DEFAULT_T0 = 0.5
T_END = 0.01                                          # Endtemperatur in Vielfachen von s
BUDGETS = {6: 800, 8: 1500, 9: 2000, 12: 3000, 16: 6000}   # Zugzahl des Annealing je Größe (Faktor wählbar)
BUDGET_FACTORS = (0.5, 1.0, 2.0)
DEFAULT_BUDGET_FACTOR = 1.0
RESTART_KS = (1, 3, 6, 20)                            # Neustarts des Abstiegs aus Zufallsstarts im Vergleich bei gleichem Aufwand
SA_RANDOM_T0, SA_LOOP_T0 = 2.0, 0.1                   # Starttemperaturen der Annealing-Läufe im Vergleich über feste Instanzen (heiß aus Zufall, kalt aus der Schleife)

FAMILIES = ("netlist", "uniform", "sparse", "cluster", "star", "skewed")
DEFAULT_FAMILY = "cluster"
FAMILY_NAMES = {"netlist": "Netzliste", "uniform": "Gleichverteilt", "sparse": "Dünn besetzt", "cluster": "Zwei Cluster", "star": "Stern", "skewed": "Wenige starke Flüsse"}
FAMILY_HELP = {
    "netlist": "Netzliste aus Dreiergruppen (IC, Kondensator, Widerstand), jedes Paar in einem Netz zählt Fluss 1: die Familie aus Stück 1.",
    "uniform": "Jedes Paar von Bauteilen hat einen zufälligen Fluss von 0 bis 9, gleichverteilt: dichte Matrix ohne Struktur.",
    "sparse": "Nur drei von zehn Paaren haben Fluss (1 bis 9), die übrigen keinen: dünn besetzt ohne weitere Struktur.",
    "cluster": "Zwei Gruppen von Bauteilen: innerhalb einer Gruppe starker Fluss (8 bis 10), zwischen den Gruppen schwacher (0 bis 2).",
    "star": "Ein Bauteil (die Nabe) hat starken Fluss (1 bis 9) zu allen anderen; zwischen den übrigen höchstens 1.",
    "skewed": "Die Flüsse sind schief verteilt: viele Paare ohne oder mit kleinem Fluss, wenige mit sehr großem (bis 60).",
}

# Netzliste (wie in Stück 1 bis 5)
N_NETS_PER_COMPONENT = 1.5
NET_SIZES = (2, 3, 4)
NET_WEIGHTS = (5, 3, 2)
LOCAL_NET_PERCENT = 70
GROUP = 3
# Dünn besetzt, Cluster, Stern, schief (wie in Stück 2)
SPARSE_PERCENT = 30
UNIFORM_MAX = 9
CLUSTER_STRONG, CLUSTER_WEAK_MAX = 8, 2
SKEW_VALUES = (0, 1, 2, 4, 8, 16, 32, 60)
SKEW_WEIGHTS = (45, 22, 13, 8, 6, 3, 2, 1)           # ganzzahlige Gewichte (Summe 100), schweres Ende

HAND_FLOWS = ((0, 1, 5), (1, 2, 1))                   # Handbeispiel 1: drei Bauteile auf einer Zeile, Fluss A–B 5, B–C 1
HAND_GRID = (1, 3)
HAND_GAP_FLOWS = ((0, 2, 1), (0, 3, 1), (1, 2, 1), (1, 3, 1))   # Handbeispiel 3: vier Bauteile auf einer Zeile, A und B gegen C und D
HAND_GAP_GRID = (1, 4)
HAND_GRID_FLOWS = ((0, 1, 3), (0, 2, 1), (1, 3, 2), (2, 3, 4))  # Handbeispiel 2 (aus Stück 1): Raster 2×2
HAND_GRID_GRID = (2, 2)

COLORS = {"best": "#2F6B65", "local": "#c0504d", "pad": "#b08a2e", "cont": "#c0504d", "other": "rgba(150,150,150,0.6)", "line": "#4c78a8", "ok": "#2F6B65", "warn": "#b08a2e", "bad": "#b34a4a",
          "family": {"netlist": "#4c78a8", "uniform": "#9c755f", "sparse": "#b08a2e", "cluster": "#2F6B65", "star": "#8e6bb0", "skewed": "#c0504d"}}

_BASE = {"family": DEFAULT_FAMILY, "n": DEFAULT_N, "seed": DEFAULT_SEED, "pads": DEFAULT_PADS, "start": DEFAULT_START, "method": DEFAULT_METHOD, "t0": DEFAULT_T0, "budget": DEFAULT_BUDGET_FACTOR}
PRESETS = {
    "Standardfall: Abstieg aus der Schleife": dict(_BASE),
    "Abstieg aus Zufall": dict(_BASE, start="random"),
    "Abstieg aus der Rundung": dict(_BASE, start="round"),
    "Annealing aus der Schleife": dict(_BASE, method="anneal", t0=0.1),
    "Annealing aus Zufall": dict(_BASE, start="random", method="anneal", t0=2.0),
    "Zwölf Bauteile": dict(_BASE, n=12),
    "Sechzehn Bauteile": dict(_BASE, n=16),
}
PRESET_HELP = {
    "Standardfall: Abstieg aus der Schleife": "Acht Bauteile, vier Pads: der Tauschabstieg aus dem Ergebnis der Schleife (Stück 10); meist genügen wenige Schritte.",
    "Abstieg aus Zufall": "Derselbe Abstieg aus einer zufälligen Anordnung: mehr Schritte, mehr Bewertungen und ein schlechteres lokales Optimum.",
    "Abstieg aus der Rundung": "Der Abstieg aus der einmaligen Rundung der Platzierung (Stück 9).",
    "Annealing aus der Schleife": "Simulated Annealing mit niedriger Starttemperatur aus der guten Startlösung: es verbessert die Anordnung weiter, ohne sie zu verwerfen.",
    "Annealing aus Zufall": "Simulated Annealing mit hoher Starttemperatur aus einer zufälligen Anordnung: es braucht die ganze Zugzahl, um herunterzukühlen.",
    "Zwölf Bauteile": "Zwölf Bauteile auf dem 3×4-Raster: nicht aufzählbar; verglichen wird mit der besten von 100 steilsten Abstiegen (obere Grenze der Lücke).",
    "Sechzehn Bauteile": "Sechzehn Bauteile auf dem 4×4-Raster: nicht aufzählbar; der Abstieg braucht mehr Schritte und lässt mehr Lücke übrig.",
}


def n_text(n: int) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 362880 → „362 880“."""
    return f"{n:,}".replace(",", " ")


assert set(PRESETS) == set(PRESET_HELP) and set(FAMILY_NAMES) == set(FAMILIES) == set(FAMILY_HELP)
assert all(p["n"] in SIZES and p["family"] in FAMILIES and 0 <= p["seed"] <= SEED_MAX and p["pads"] in PAD_CHOICES and p["start"] in START_CHOICES and p["method"] in METHODS and p["t0"] in T0_CHOICES and p["budget"] in BUDGET_FACTORS for p in PRESETS.values())
assert all(r * c == n for n, (r, c) in GRID.items()) and sum(SKEW_WEIGHTS) == 100 and set(GRID) == set(SIZES)
