"""Detailplatzierung - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 12 der Reihe „Anordnen: relaxieren und runden“: die letzte Meile. Auf der legalen Anordnung aus den Stücken 9 und 10 tauscht ein Abstieg (und Simulated Annealing) Bauteile. Gemessen wird, wie viel das bringt, je nach Startlösung,
und was es kostet (gezählt in Bewertungen). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import dtp_constants as C
from dtp_evaluation import (
    Settings,
    count,
    de,
    fam,
    hand_data,
    instance_data,
    main_result,
    mean_gap,
    median_of,
    num,
    pct,
    pooled,
    rel,
    restart_summary,
    sa_summary,
    schritte,
    start_summary,
    sweep,
    tx,
    verdict_anneal,
    verdict_core,
    verdict_descent,
    verdict_effort,
    verdict_starts,
    verdict_sweep_anneal,
    verdict_sweep_restarts,
    verdict_sweep_starts,
)
from dtp_layout import dunkles_design, kopf_css
from dtp_pdf_export import build_pdf
from dtp_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from dtp_visualization import build_anneal_trace, build_arrangement, build_descent_trace, build_effort_curve, build_restart_bars, build_start_bars, build_sweep_bars

st.set_page_config(page_title="Detailplatzierung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne Abstieg und Annealing …")
def _instance(settings: Settings):
    return instance_data(settings)


@st.cache_data(show_spinner=False)
def _sweep(family, n, seeds, pads_list):
    return sweep(family, n, seeds, pads_list)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


def sweep_tables(rows, n):
    """Tabellen und Abbildungen für einen Vergleich über feste Instanzen."""
    st.plotly_chart(build_sweep_bars(rows, median_of, start_summary, f"Lücke am Start und nach dem Abstieg, n = {n}"), width="stretch", key=f"sweep_chart_{n}")
    table = []
    for p in C.PAD_CHOICES:
        row = {"Pads": p}
        for k in C.START_CHOICES:
            sm = start_summary(rows, p, k)
            row[f"{C.START_NAMES[k]}: Start → Abstieg"] = f"{pct(sm['start'], 1)} → {pct(sm['desc'], 1)}"
            row[f"{C.START_NAMES[k]}: Schritte / Bewertungen"] = f"{de(sm['steps'], 0)} / {count(sm['evals'])}"
        if rows[0]["exact"]:
            row["Zufall (mittlere Kosten)"] = pct(mean_gap(rows, p))
        table.append(row)
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_sweep_starts(n, rows))
    verdict(verdict_sweep_anneal(n, rows))
    st.plotly_chart(build_restart_bars(rows, restart_summary, start_summary, sa_summary, f"Gleicher Aufwand: Neustarts, Abstieg, Annealing, n = {n}"), width="stretch", key=f"restart_chart_{n}")
    verdict(verdict_sweep_restarts(n, rows))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in dtp_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔧 Detailplatzierung")
st.markdown(
    """
**Wie viel bringt die letzte Meile?** Dieselbe Aufgabe wie in Stück 1 bis 10: `n` Bauteile auf `n` Plätze, Kosten gleich der Summe aus **Fluss mal Abstand**, dazu **feste Pads**. Die Stücke 9 und 10 haben eine **legale** Anordnung geliefert (Rundung der Platzierung, Ergebnis der Schleife). Hier wird sie **durch Tausch** verbessert:
ein **Tauschabstieg** (alle Vertauschungen zweier Bauteile prüfen, die beste nehmen, bis keine mehr hilft) und **Simulated Annealing** mit Tauschzügen (auch Verschlechterungen mit abnehmender Wahrscheinlichkeit annehmen). Gemessen werden die **Lücke zum Optimum** und der **Aufwand in Bewertungen**
(Kosten einer Anordnung), nicht in Zeit. Dazu die Frage, ob eine gute **Startlösung** oder mehrere **Neustarts aus Zufall** mehr bringen.
Die sechs Familien der Flussmatrix sind **eigene, einfache Erfindungen** (aus Stück 2), die **Pads ebenso**; Abstieg und Annealing sind **eigene einfache Fassungen**, die in der Trajektorien-Linie erklärt werden (dort an einer Lieferroute). Stück 12 der Reihe „Anordnen: relaxieren und runden“.

Weiter unten: **fünf Experimente** (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Startlösungen:** eine **zufällige** Anordnung, die **Rundung** der Platzierung mit zwei Umgewichtungen (Stück 9) und das Ergebnis der **Schleife** mit Pseudo-Ankern (Stück 10).
2. **Tauschabstieg:** in jedem Schritt werden alle `n(n−1)/2` Vertauschungen zweier Bauteile bewertet und die billigste genommen, solange sie die Kosten senkt. Das Ende ist ein **lokales Optimum der Tauschnachbarschaft**. Gezählt werden die Schritte und die **Bewertungen**.
3. **Simulated Annealing:** je Zug ein zufälliger Tausch; ein Tausch, der die Kosten um `Δ` erhöht, wird mit der Wahrscheinlichkeit `e^(−Δ/T)` trotzdem angenommen. Die Temperatur sinkt geometrisch von `t0 · s` auf `0,01 · s` (`s` = mittlere Kostenänderung der Tausche der Startanordnung); gezählt wird ein Zug als eine Bewertung. Am Ende zählt die beste besuchte Anordnung.
4. **Neustarts:** der Abstieg aus 1, 3, 6, 20 Zufallsstarts, bester Wert und Gesamtzahl der Bewertungen: der Vergleich bei gleichem Aufwand.
5. **Die Lücke:** (Kosten − Vergleichswert) / Vergleichswert; bis n = 9 ist der Vergleichswert das aufgezählte Optimum, ab n = 12 die beste von 100 steilsten Abstiegen (obere Grenze der Lücke; 0 heißt „so gut wie der Vergleichswert“).
6. **Feste Instanzen:** Vergleiche laufen über feste Seeds (n = 8: 20 Instanzen je Familie, n = 12: 5, n = 16: 3), nie über einen einzelnen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Instanz**")
    family = st.selectbox("Familie der Flussmatrix", C.FAMILIES, key="family_select", format_func=lambda f: C.FAMILY_NAMES[f], help="Wie der Fluss zwischen den Bauteilen verteilt ist. Die Beschreibung steht unter dem Regler.")
    st.caption(C.FAMILY_HELP[family])
    n = st.select_slider("Bauteile n", options=C.SIZES, key="n_select", help="Bis n = 9 wird alles aufgezählt (Vergleichswert: Optimum); ab n = 12 steht die beste von 100 steilsten Abstiegen an seiner Stelle.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed)
    pads_n = st.select_slider("Zahl der Pads", options=C.PAD_CHOICES, key="pads_select", help="Feste Anker auf dem Ring um das Raster (Gewicht: Grundgewicht, Median der positiven Flüsse).")
    st.markdown("**Die letzte Meile**")
    start = st.selectbox("Startlösung", C.START_CHOICES, key="start_select", format_func=lambda k: C.START_NAMES[k], help="Zufall, Rundung der Platzierung (Stück 9) oder Ergebnis der Schleife (Stück 10).")
    method = st.selectbox("Verfahren", C.METHODS, key="method_select", format_func=lambda k: C.METHOD_NAMES[k], help="Tauschabstieg (nur bergab) oder Simulated Annealing (auch bergauf, mit abnehmender Wahrscheinlichkeit).")
    t0 = st.select_slider("Starttemperatur (Annealing)", options=C.T0_CHOICES, key="t0_select", format_func=lambda x: f"{tx(x)} · s", help="In Vielfachen der mittleren Kostenänderung der Tausche der Startanordnung: niedrig bleibt nahe der Startlösung, hoch kann sie weit verlassen.")
    budget = st.select_slider("Zugzahl (Annealing)", options=C.BUDGET_FACTORS, key="budget_select", format_func=lambda x: f"×{tx(x)}", help="Faktor auf die Zugzahl je Größe (800 / 1 500 / 2 000 / 3 000 / 6 000 für n = 6 / 8 / 9 / 12 / 16).")

sync_query_params({"family_select": family, "n_select": int(n), "seed_input": int(seed), "pads_select": int(pads_n), "start_select": start, "method_select": method, "t0_select": float(t0), "budget_select": float(budget)})
settings = Settings(family, int(n), int(seed), int(pads_n), start, method, float(t0), float(budget))

v = _instance(settings)
perm_out, cost_out, evals_out = main_result(settings, v)
d = v["descents"][start]
ref_label = "Optimum" if v["exact"] else "Beste gefundene Lösung"

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m4, m5 = st.columns(2)
m1.metric("Lücke am Start", pct(rel(d.costs[0], v["ref"]), 1), delta=f"Kosten {num(d.costs[0])}", delta_color="off", help=f"Kosten der Startlösung {C.START_NAMES[start]} gegen den Vergleichswert.")
m2.metric(f"Lücke nach {C.METHOD_NAMES[method]}", pct(rel(cost_out, v["ref"]), 1), delta=f"Kosten {num(cost_out)}", delta_color="off", help="Dasselbe nach dem gewählten Verfahren.")
m3.metric("Bewertungen", count(evals_out), delta=(schritte(d.steps) if method == "descent" else f"{pct(v['anneals'][start].accepted / v['anneals'][start].moves)} angenommen"), delta_color="off", help="Kosten einer Anordnung, die das Verfahren bewertet hat: ein Abstiegsschritt n(n−1)/2, ein Annealing-Zug eine.")
m4.metric(ref_label, num(v["ref"]), help="Die kleinsten Kosten aller n! Anordnungen (aufgezählt)." if v["exact"] else "Die beste von 100 steilsten Abstiegen aus Zufallsstarts: eine obere Schranke des Optimums.")
m5.metric("Pads", f"{settings.pads}", help="Zahl der festen Pads.")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(build_arrangement(v["inst"], v["starts"][start], f"Start: {C.START_NAMES[start]} (Kosten {num(d.costs[0])})"), width="stretch", key="arrangement_start")
with c2:
    st.plotly_chart(build_arrangement(v["inst"], perm_out, f"Nach {C.METHOD_NAMES[method]} (Kosten {num(cost_out)})"), width="stretch", key="arrangement_result")

if st.button("📄 PDF des aktuellen Ergebnisses erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(settings, v))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="detailplatzierung.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel bringt die letzte Meile?")
verdict(verdict_core(settings, v))

st.markdown("---")

# --- Experiment 1 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Der Tauschabstieg")
st.caption("Die Kosten vor dem ersten und nach jedem Schritt des Abstiegs aus der gewählten Startlösung; gestrichelt der Vergleichswert. Der Abstieg endet in einem lokalen Optimum der Tauschnachbarschaft, das nicht das Optimum sein muss.")
st.plotly_chart(build_descent_trace(d, v["ref"], f"Abstieg aus {C.START_NAMES[start]}"), width="stretch", key="descent_trace")
verdict(verdict_descent(settings, v))
with st.expander("Handbeispiel zum Nachrechnen"):
    h = hand_data()["descent"]
    st.markdown(
        f"**Drei Bauteile auf einer Zeile** (Plätze 1, 2, 3 mit Abständen 1, 1 und 2), Fluss A–B 5, B–C 1. Start: A auf Platz 2, B auf Platz 1, C auf Platz 3, Kosten `5·1 + 1·2 = 7`. Die drei Vertauschungen: A↔B (A auf 1, B auf 2: `5·1 + 1·1 = 6`), A↔C (`5·2 + 1·1 = 11`), B↔C (`5·1 + 1·2 = 7`). "
        f"Der Abstieg nimmt A↔B: **{schritte(h.steps)}**, Kosten **{num(h.cost)}**. Danach kostet kein Tausch weniger (A↔C kostet ebenfalls 6, gleich, keine Verbesserung): lokales Optimum nach **{h.evals} Bewertungen** (ein Schritt mit drei Tauschen, dann die Prüfung mit drei Tauschen)."
    )

st.markdown("---")

# --- Experiment 2 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Startlösungen im Vergleich")
st.caption("Die drei Startlösungen derselben Instanz: Kosten am Start, nach dem Abstieg und nach dem Annealing (Starttemperatur und Zugzahl nach den Reglern). Darunter, über feste Instanzen, Lücke und Aufwand je Startlösung.")
st.plotly_chart(build_start_bars(v), width="stretch", key="start_bars")
verdict(verdict_starts(settings, v))
st.markdown(f"**Vergleich über feste Instanzen** (n = {C.SWEEP_N}, je Familie {len(C.SWEEP_SEEDS)} Instanzen, 2, 4 und 8 Pads, Optimum aufgezählt).")
if not st.session_state.get("sweep_ok"):
    st.info("Der Vergleich rechnet 6 Reihen zu je 20 Instanzen, drei Pad-Zahlen, drei Abstiege, zwei Annealing-Läufe und 20 Neustarts und dauert rund eine Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Vergleich rechnen (n = 8)", key="sweep_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["sweep_ok"] = True
        st.rerun()
else:
    rows8 = pooled({f: _sweep(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES})
    sweep_tables(rows8, C.SWEEP_N)

st.markdown("---")

# --- Experiment 3 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Simulated Annealing")
st.caption("Aktuelle und beste Kosten über die Züge (links die Skala der Kosten), dazu die Temperatur (gestrichelt, rechte Achse), aus der gewählten Startlösung mit den gewählten Reglern. Aus einer guten Startlösung genügt eine niedrige Starttemperatur; aus Zufall braucht es eine hohe.")
a = v["anneals"][start]
st.plotly_chart(build_anneal_trace(a, v["ref"], f"Annealing aus {C.START_NAMES[start]} (Starttemperatur {tx(t0)} · s, {count(a.moves)} Züge)"), width="stretch", key="anneal_trace")
verdict(verdict_anneal(settings, v))

st.markdown("---")

# --- Experiment 4 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Gleicher Aufwand")
st.caption("Die besten Kosten gegen die Zahl der Bewertungen (logarithmisch): Neustarts des Abstiegs aus Zufall (grau), Annealing aus Zufall und aus der Schleife (Linien) und die Abstiege aus den drei Startlösungen (Rauten). Weiter unten dasselbe über feste Instanzen (Experiment 2 und 5).")
st.plotly_chart(build_effort_curve(v), width="stretch", key="effort_curve")
verdict(verdict_effort(settings, v))

st.markdown("---")

# --- Experiment 5: große Instanzen --------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Jenseits der Aufzählung")
st.caption(f"Für n = 12 und 16: Abstieg, Annealing und Neustarts gegen die beste von {C.STARTS} steilsten Abstiegen (obere Grenze der Lücke), je Familie 5 bzw. 3 feste Instanzen, 2, 4 und 8 Pads. Die Plateaus um ein Prozent, an denen auch stärkere Metaheuristiken enden, zeigt die Fall-Demo `dock_door-demo`.")
if not st.session_state.get("large_ok"):
    st.info("Die Rechnung dauert rund zwei Minuten (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Große Instanzen rechnen (n = 12, 16)", key="large_button"):
        bar = st.progress(0.0, text="Rechne die großen Instanzen …")
        todo = [(f, m) for m in C.LARGE_SWEEP_SIZES for f in C.FAMILIES]
        for i, (f, m) in enumerate(todo):
            _sweep(f, m, C.LARGE_SEEDS[m], C.PAD_CHOICES)
            bar.progress((i + 1) / len(todo), text=f"n = {m}, {C.FAMILY_NAMES[f]} fertig")
        st.session_state["large_ok"] = True
        st.rerun()
else:
    for m in C.LARGE_SWEEP_SIZES:
        sweep_tables(pooled({f: _sweep(f, m, C.LARGE_SEEDS[m], C.PAD_CHOICES) for f in C.FAMILIES}), m)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Pads sind erfunden** | Zahl, Ort, Gewicht und Verbindungen der Pads sind eigene Erfindungen (aus Stück 9); eine andere Ankeranordnung kann die Lücken ändern. | – |
| **Die sechs Familien sind erfunden** | Echte Platinen haben andere Strukturen; Aussagen über Familien gelten nur für diese. | – |
| **Abstieg und Annealing sind einfache Fassungen** | Eine feste Zugzahl je Größe, ein geometrischer Plan, eine Starttemperatur: Tabu-Suche, Robust Tabu und Breakout Local Search aus der Literatur sind nicht gebaut und nicht nachgelesen und können weiter kommen. | Trajektorien-Linie, `dock_door-demo` |
| **Aufwand in Bewertungen, nicht in Zeit** | Ein Abstiegsschritt wertet alle Tausche in einem Stapel aus, ein Annealing-Zug einzeln; Bewertungen sind ein Maß der Rechenarbeit, kein Zeitmaß. | – |
| **Vergleichswert ab n = 12** | Die beste von 100 Abstiegen ist eine obere Grenze des Optimums und selbst ein Abstiegsergebnis; „0 %“ heißt „so gut wie der Vergleichswert“, nicht „optimal“. | Stück 8 (Beweis bis n ≈ 12) |
| **Nur Tauschnachbarschaft** | Verschiebungen mehrerer Bauteile, Zyklen und Ketten sind nicht Teil der Nachbarschaft; ein lokales Optimum der Tausche muss keins dieser Nachbarschaften sein. | – |
| **Wenige Instanzen** | n = 8: 20 Instanzen je Familie, n = 12: 5, n = 16: 3; kleine Unterschiede sind nicht belastbar. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Die Aufgabe (wie in Stück 9).** Flüsse $F$, Plätze $s_1, \dots, s_n$, Pads $a_j$ mit Gewichten $w_{ij}$; Kosten einer Anordnung $\pi$ ($\pi_i$ = Platz des Bauteils $i$): $\mathrm{cost}(\pi) = \sum_{i<k} F_{ik} \lVert s_{\pi_i} - s_{\pi_k} \rVert_1 + \sum_{i,j} w_{ij} \lVert s_{\pi_i} - a_j \rVert_1$.

**Tauschnachbarschaft und Abstieg.** Die Nachbarn von $\pi$ sind die $\binom{n}{2}$ Anordnungen $\pi^{(a,b)}$, die entstehen, wenn man die Plätze der Bauteile $a$ und $b$ vertauscht. Der **steilste Abstieg** nimmt $\pi \leftarrow \arg\min_{a<b} \mathrm{cost}(\pi^{(a,b)})$, solange das die Kosten senkt (bei Gleichstand die erste Vertauschung in der Reihenfolge der Paare).
Jeder Schritt bewertet $\binom{n}{2}$ Anordnungen; mit $k$ Schritten sind es $(k+1)\binom{n}{2}$ **Bewertungen** (der letzte Durchlauf ohne Verbesserung zählt mit). Das Ende ist ein **lokales Optimum** der Tauschnachbarschaft.

**Simulated Annealing.** Je Zug ein gleichverteilt zufälliger Tausch $(a, b)$; mit $\Delta = \mathrm{cost}(\pi^{(a,b)}) - \mathrm{cost}(\pi)$ wird er angenommen, wenn $\Delta \le 0$ oder mit der Wahrscheinlichkeit $e^{-\Delta/T}$. Die Temperatur fällt geometrisch,
$$T_t = t_0 s \left( \frac{0{,}01}{t_0} \right)^{t/(B-1)}, \qquad s = \frac{1}{\binom{n}{2}} \sum_{a<b} \left| \mathrm{cost}(\pi^{(a,b)}) - \mathrm{cost}(\pi) \right|$$
für die Startanordnung $\pi$, $B$ Züge, also $T_0 = t_0 s$ und $T_{B-1} = 0{,}01\,s$. Ergebnis ist die beste besuchte Anordnung. Ein Zug zählt als eine Bewertung.

**Gleicher Aufwand.** Die Neustarts rechnen $k$ Abstiege aus zufälligen Startanordnungen und nehmen den besten Wert; die Gesamtzahl der Bewertungen ist die Summe über die Abstiege.

**Lücke.** $(\mathrm{cost} - U)/U$ mit dem Vergleichswert $U$ (aufgezähltes Optimum bis $n = 9$, sonst die beste von 100 steilsten Abstiegen aus Zufallsstarts: eine **obere** Grenze des Optimums, die Lücke ist dann eine obere Grenze der wahren Lücke).

**Literatur.** Taillard (Robust Tabu Search), Benlic und Hao (Breakout Local Search) und die Metaheuristiken der Trajektorien-Linie: Angaben aus der Fachliteratur übernommen, hier **nicht nachgelesen**; Selbstangaben der Autoren zur Güte werden nicht übernommen.
Die Zählung der Bewertungen, der Temperaturplan und der Vergleich bei gleichem Aufwand sind **eigene** Herleitungen und werden durch Tests (Handrechnung, Aufzählung, eine zweite Rechnung des Annealing) geprüft. Die Zahlen dieser Demo sind eigene Rechnungen an eigenen, erfundenen Familien und Pads.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
