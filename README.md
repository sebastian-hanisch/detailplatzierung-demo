# Detailplatzierung – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-detailplatzierung-demo.streamlit.app/)** -->

Stück 12 von 15 der **Konzepte-Reihe „Anordnen: relaxieren und runden“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Konzepte-Seite der Reihe gibt es noch nicht). Die Stücke [9, Quadratische Platzierung](https://github.com/sebastian-hanisch/quadratische-platzierung-demo), und [10, Look-ahead-Legalisierung](https://github.com/sebastian-hanisch/look-ahead-legalisierung-demo), liefern eine **legale** Anordnung (Rundung der Platzierung, Ergebnis der Schleife). Dieses Stück fragt, **wie viel die letzte Meile bringt** (Kante der Reihe: Gegenprobe zu Stück 10): ein **Tauschabstieg** und **Simulated Annealing** mit Tauschzügen verbessern diese Anordnung, und gemessen werden die Lücke zum Optimum und der Aufwand in **Bewertungen**, je nach Startlösung. Abstieg und Annealing erklärt die Trajektorien-Linie (dort an einer Lieferroute), hier werden sie **angewendet**.

## Warum dieses Problem

Eine Platzierung liefert eine brauchbare, aber selten optimale Anordnung (Stück 9: Lücke 6 bis 14 %; Stück 10: 4 bis 11 %). Ein Tausch zweier Bauteile ist die kleinste Änderung einer Anordnung, und die Nachbarschaft aller Tausche ist klein genug, um sie vollständig zu prüfen. Die Kernfrage: **wie viel holt diese letzte Meile heraus, hängt es von der Startlösung ab, und ersetzt eine gute Startlösung Neustarts aus Zufall?**

Die Antwort dieser Messung: Bei acht Bauteilen holt der Abstieg aus der Rundung oder der Schleife fast alles (Lücke im Median 0,0 bis 0,2 %, Optimum in der Hälfte der Instanzen, nach im Median zwei Schritten); bei zwölf und sechzehn Bauteilen bleiben im Median 1,9 bzw. 2,2 % übrig. Die gute Startlösung **spart Aufwand** (ein Abstieg braucht 50 bis 70 % der Bewertungen gegenüber Zufall) und ein bis drei Prozentpunkte Lücke; **gleich gute Ergebnisse aus Zufall brauchen mehrere Neustarts**; Simulated Annealing aus der Schleife mit niedriger Starttemperatur holt mehr als der Abstieg, bei etwa acht- bis achtzehnmal so vielen Bewertungen (1500 / 3000 / 6000 Züge gegen 84 / 264 / 720). Das sind **Befunde an sechs erfundenen Familien, erfundenen Pads und einfachen Eigenfassungen**, keine Sätze.

## Modell

- **Aufgabe** (wie in Stück 9 und 10): `n` Bauteile auf `n` Plätze eines Rasters (Manhattan-Abstand), dazu `p` **feste Pads** auf einem Ring um das Raster; jedes Pad hängt mit dem Grundgewicht (Median der positiven Flüsse, mindestens 1) an zwei zufälligen Bauteilen. `cost(p) = Σ_{i<k} F[i,k] · |p_i − p_k|₁ + Σ_{i,Pad} w · |p_i − Pad|₁`. Kern (Kosten, Aufzählung, Zufall, sechs Familien der Flussmatrix, Pads, Platzierung, Rundung, Schleife, Ungarische Methode) als Kopie aus Stück 9 und 10 (`dtp_place.py`, `dtp_loop.py`, `dtp_cost.py`, `dtp_landscape.py`, `dtp_rng.py`, `dtp_instance.py`, `dtp_assignment.py`; Tests vergleichen die Instanzen mit den Schwester-Repos, wenn sie nebenan liegen). Die Familien und die Pads sind **eigene, einfache Erfindungen**, keine echten Platinen und keine QAPLIB-Instanzen.
- **Tauschabstieg** (`dtp_search.py`): in jedem Schritt werden alle `n(n−1)/2` Vertauschungen zweier Bauteile bewertet (in einem Stapel) und die billigste genommen, solange sie die Kosten senkt; bei Gleichstand gewinnt die erste. Das Ende ist ein **lokales Optimum der Tauschnachbarschaft**. Gezählt werden Schritte und **Bewertungen** (mit `k` Schritten `(k+1) · n(n−1)/2`: der letzte Durchlauf ohne Verbesserung zählt mit).
- **Simulated Annealing** mit Tauschzügen (eigene Fassung, SplitMix64): je Zug ein zufälliger Tausch, angenommen bei `Δ ≤ 0` oder mit der Wahrscheinlichkeit `e^(−Δ/T)`; die Temperatur sinkt geometrisch von `t0 · s` auf `0,01 · s` (`s` = mittlerer Betrag der Kostenänderung aller Vertauschungen der Startanordnung); beste besuchte Anordnung; Zugzahl 800 / 1 500 / 2 000 / 3 000 / 6 000 für n = 6 / 8 / 9 / 12 / 16 (Faktor wählbar), ein Zug zählt als eine Bewertung. Starttemperaturen `t0` = 0,1 / 0,5 / 2.
- **Startlösungen:** **Zufall** (SplitMix64), **Rundung** der Platzierung mit zwei Umgewichtungen (Stück 9) und das **Ergebnis der Schleife** aus Stück 10 (Zuordnung, 15 Runden, `c = 0,2`, zwei Umgewichtungen).
- **Neustarts:** der Abstieg aus 1, 3, 6, 20 Zufallsstarts, bester Wert und Gesamtzahl der Bewertungen (Vergleich bei gleichem Aufwand).
- **Lücke und Vergleichswert:** `(Kosten − Vergleichswert) / Vergleichswert`; bis `n = 9` ist der Vergleichswert das aufgezählte Optimum (mit den Pads der Instanz), ab `n = 12` die beste von 100 steilsten Abstiegen aus Zufallsstarts (obere Grenze der Lücke; „erreicht“ heißt gleich oder besser).
- **Experimente:** (1) der Abstieg Schritt für Schritt (Handbeispiel); (2) die Startlösungen im Vergleich; (3) Annealing (Temperatur, Zugzahl); (4) gleicher Aufwand: Neustarts gegen Abstieg und Annealing; (5) jenseits der Aufzählung (`n` = 12, 16). Formeln im 📐-Expander der App.

## Methodik

Experiment 1, 3 und 4 rechnen **eine** Instanz (Pads, Startlösung, Verfahren, Starttemperatur und Zugzahl sind Regler; `n` = 6, 8, 9 mit Aufzählung als Vergleichswert, `n` = 12, 16 mit der besten von 100 Abstiegen). Standard: Zwei Cluster, `n = 8`, Seed 46, vier Pads, Abstieg aus der Schleife. Der Vergleich in Experiment 2 rechnet auf Knopfdruck je Familie 20 Instanzen bei `n = 8` (Seeds 100000 bis 100019) mit 2, 4 und 8 Pads: drei Abstiege (je Startlösung), zwei Annealing-Läufe (heiß aus Zufall mit `t0 = 2`, kalt aus der Schleife mit `t0 = 0,1`) und 20 Neustarts; Experiment 5 rechnet dasselbe für `n = 12` (5 Instanzen je Familie) und `n = 16` (3 Instanzen je Familie). Der Vergleichswert hängt von den Pads ab und wird für jede Zahl von Pads neu bestimmt. Alle Aussagen laufen über feste Seeds, nie über einen einzelnen. **Aufwand wird in Bewertungen gezählt, nicht in Zeit**; Zeiten stehen nirgends als Zahl in Tests oder in dieser README.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (Prozentwerte auf eine Stelle, Zählungen exakt). Reihenfolge der Familien: Netzliste, gleichverteilt, dünn besetzt, zwei Cluster, Stern, wenige starke Flüsse. Medianwerte über alle Instanzen und Pad-Zahlen, sofern nicht anders genannt.

| Frage | Befund |
|---|---|
| Handbeispiel | Drei Bauteile auf einer Zeile (Plätze 1, 2, 3; Fluss A–B 5, B–C 1), Start A auf Platz 2, B auf 1, C auf 3: Kosten 7. Die drei Vertauschungen kosten 6 (A↔B), 11 (A↔C), 7 (B↔C); der Abstieg nimmt A↔B (**1 Schritt**, Kosten **6**), danach hilft keiner mehr (A↔C kostet ebenfalls 6): **6 Bewertungen** |
| Standardinstanz (Zwei Cluster, n = 8, Seed 46, 4 Pads) | Optimum **337**, mittlere Kosten aller Anordnungen 34,1 % darüber. Startlösungen: Zufall 448, Rundung 414, Schleife 380 (Lücke 12,8 %). **Abstieg aus der Schleife:** 3 Schritte, 112 Bewertungen, 380 → 363 → 353 → **346** (Lücke 2,7 %); aus Zufall 4 Schritte, 140 Bewertungen, **337 (Optimum)**; aus der Rundung 4 Schritte, 346. **Annealing** (1 500 Züge, `t0` = 0,5): 342 / 342 / **337** aus Zufall / Rundung / Schleife; bei `t0` = 0,1: 337 / 359 / 342, bei `t0` = 2: 337 aus allen drei. **Neustarts** aus Zufall (1 / 3 / 6 / 20): 342 bei 112, dann 337 bei 476 / 896 / 2 828 Bewertungen. **Eine Instanz, kein Befund über die Familie:** hier ist die schlechteste Startlösung beim Abstieg die beste |
| Abstieg, n = 8 (360 Instanzen) | Zufall: Start 32,4 % → Abstieg **2,2 %** (4 Schritte, 140 Bewertungen, Optimum in 104); Rundung: 8,1 % → **0,0 %** (2 Schritte, 84 Bewertungen, Optimum in 181); Schleife: 6,2 % → **0,2 %** (2 Schritte, 84 Bewertungen, Optimum in 179). Der Abstieg senkt die Kosten in 360 / 320 / 303 Instanzen |
| Abstieg je Pad-Zahl, n = 8 (120 Instanzen; 2 / 4 / 8 Pads) | Zufall 40,7 / 33,6 / 26,8 % → 2,4 / 2,8 / 1,6 %; Rundung 14,5 / 8,8 / 4,4 % → 0,4 / 0,6 / 0,0 %; Schleife 10,8 / 6,3 / 3,6 % → 0,6 / 0,6 / 0,0 %; Optimum erreicht: Zufall 38 / 28 / 38, Rundung 59 / 57 / 65, Schleife 58 / 56 / 65 (von 120) |
| Abstieg, n = 12 (90 Instanzen) | Zufall 40,1 % → **3,8 %** (7 Schritte, 528 Bewertungen); Rundung 12,5 % → **1,9 %** (4, 330); Schleife 9,1 % → **1,9 %** (3, 264). Vergleichswert erreicht in 5 / 15 / 14 von 90. Je Pad-Zahl (2 / 4 / 8): Schleife 10,6 / 10,6 / 5,9 % → 3,5 / 2,6 / 0,8 % |
| Abstieg, n = 16 (54 Instanzen) | Zufall 43,3 % → **5,2 %** (9 Schritte, 1 200 Bewertungen); Rundung 13,7 % → **2,2 %** (6, 840); Schleife 10,4 % → **2,2 %** (5, 720). Vergleichswert erreicht in 1 / 7 / 7 von 54 |
| **Die gute Startlösung spart Aufwand** | Bewertungen je Abstieg aus Zufall / Rundung / Schleife: n = 8: 140 / 84 / 84; n = 12: 528 / 330 / 264; n = 16: 1 200 / 840 / 720; Schritte n = 8: 4 / 2 / 2, n = 12: 7 / 4 / 3, n = 16: 9 / 6 / 5 |
| **Neustarts bei gleichem Aufwand** (Abstiege aus Zufall; beste von 1 / 3 / 6 / 20) | n = 8: Lücke 2,2 / 0,0 / 0,0 / 0,0 % bei 140 / 420 / 812 / 2 772 Bewertungen (Vergleichswert erreicht in 94 / 201 / 286 / 352 von 360); n = 12: 3,1 / 1,4 / 0,7 / 0,0 % bei 462 / 1 518 / 3 036 / 10 098 (9 / 22 / 29 / 56 von 90); n = 16: 4,7 / 2,1 / 1,5 / 0,3 % bei 1 200 / 3 660 / 7 440 / 24 600 (1 / 5 / 7 / 23 von 54). Ein Abstieg aus der Schleife (n = 12: 1,9 % bei 264 Bewertungen) erreicht, was aus Zufall erst **drei Neustarts** (1,4 % bei 1 518) übertreffen |
| Annealing, n = 8 (1 500 Züge; heiß aus Zufall `t0` = 2 / kalt aus der Schleife `t0` = 0,1) | Lücke im Median 0,0 / 0,0 %; Vergleichswert erreicht in 245 / 240 von 360 (gegen 179 des Abstiegs aus der Schleife); angenommen 20 % / 3 % der Züge. Je Pad-Zahl (2 / 4 / 8): 74 / 81 / 90 und 78 / 76 / 86 von 120 |
| Annealing, n = 12 (3 000 Züge) | aus Zufall (heiß) **0,8 %**, erreicht in 26 von 90; aus der Schleife (kalt) **0,5 %**, erreicht in 42 von 90 (Abstieg aus der Schleife 1,9 %, 14 von 90; sechs Neustarts 0,7 % bei 3 036 Bewertungen). Je Pad-Zahl (2 / 4 / 8): heiß 1,1 / 1,5 / 0,5 %, kalt 1,3 / 0,7 / 0,0 % |
| Annealing, n = 16 (6 000 Züge) | heiß aus Zufall **1,0 %**, erreicht in 15 von 54; kalt aus der Schleife **0,4 %**, erreicht in 22 von 54 (Abstieg aus der Schleife 2,2 %, 7 von 54; sechs Neustarts 1,5 % bei 7 440 Bewertungen). Je Pad-Zahl (2 / 4 / 8): heiß 1,3 / 1,3 / 0,9 %, kalt 0,3 / 0,7 / 0,2 % |
| Orakel | Jeder Tauschpreis des Stapels gleich einer unabhängig geschriebenen Doppelschleife; das Ende des Abstiegs ist ein lokales Optimum (kein Tausch ist billiger, geprüft mit der zweiten Rechnung); das Annealing gleich einer zweiten, einzeln geschriebenen Rechnung mit denselben Zufallszahlen; kein Verfahren und kein Neustart liegt unter dem aufgezählten Optimum (n = 6, alle Pad-Zahlen, alle Temperaturen); die Rundung der Startlösung gleich `scipy.optimize.linear_sum_assignment` |

**Was die Zahlen nicht sagen:** Die Familien und die **Pads** (Zahl, Ort, Gewicht, Verbindungen) sind erfunden; eine andere Ankeranordnung kann die Zahlen ändern. Das Annealing ist eine **eigene einfache Fassung** (feste Zugzahl je Größe, geometrischer Plan, eine Starttemperatur je Lauf); Tabu-Suche, Robust Tabu und Breakout Local Search der Literatur sind nicht gebaut und nicht nachgelesen. Ab `n = 12` sind die Lücken obere Grenzen: „0,0 %“ heißt „so gut wie die beste von 100 Abstiegen“, nicht „optimal“. Bewertungen sind ein Maß der Rechenarbeit in dieser Fassung (ein Abstiegsschritt wertet alle Tausche in einem Stapel aus), kein Zeitmaß. Bei `n = 16` sind es drei Instanzen je Familie.

## Ehrliche Grenzen

- **Erfundene Pads und Familien:** Befunde gelten für diese Anker und diese Familien.
- **Einfache Fassungen:** Abstieg und Annealing wie oben; stärkere Verfahren können weiter kommen (nicht nachgelesen).
- **Aufwand in Bewertungen, nicht in Zeit:** der Abstieg wertet n(n−1)/2 Anordnungen in einem Stapel aus, das Annealing eine je Zug; der Vergleich „bei gleichem Aufwand“ zählt Bewertungen.
- **Vergleichswert ab n = 12:** die beste von 100 Abstiegen ist selbst ein Abstiegsergebnis; die Lücke ist eine obere Grenze der wahren Lücke.
- **Nur Tauschnachbarschaft:** keine Verschiebungen mehrerer Bauteile, keine Ketten; ein lokales Optimum der Tausche muss keins dieser Nachbarschaften sein.
- **Wenige Instanzen:** n = 8: 20 je Familie, n = 12: 5, n = 16: 3.
- **Rechnerabhängige Gleichstände:** der Abstieg wählt bei exakten Gleichständen die erste Vertauschung; das Annealing hängt an der Starttemperatur (Mittel über alle Tausche); Änderungen daran ändern einzelne Zählungen („erreicht in …“).
- **Quellen:** Taillard (Robust Tabu Search), Benlic und Hao (Breakout Local Search) und die Metaheuristiken der Trajektorien-Linie sind aus der Fachliteratur übernommen und **nicht nachgelesen**; die Zählung der Bewertungen, der Temperaturplan und der Vergleich bei gleichem Aufwand sind eigene Herleitungen und werden durch Tests (Handrechnung, Aufzählung, zweite Rechnung) geprüft.

## Verifikation

- **Tests** (`pytest tests/`): **218 Tests** (Windows, Python 3.14). Handwerte (der Abstieg am Handbeispiel von Hand: Kosten 7 → 6, 6 Bewertungen; Pseudo-Anker und Zweiteilung von Hand aus Stück 10), Eigenschaften (das Ende des Abstiegs ist ein lokales Optimum, die Kosten fallen je Schritt, Bewertungen = (Schritte + 1) · n(n−1)/2; das Annealing ist deterministisch, nie schlechter als der Start, die Temperatur fällt geometrisch, bei fast null Temperatur nie bergauf; das Annealing ändert sich bei Rechenrauschen in der Temperaturskala nicht; Neustarts: Bewertungen steigen, bester Wert fällt; die Startlösungen sind Anordnungen; aus guter Startlösung weniger Schritte), Orakel (Aufzählung; zweite Kostenrechnung für jeden Tausch; `linear_sum_assignment`; nur mit `requirements-dev.txt`), Randfälle (null Fluss, zwei Bauteile, ein Zug), Verdikte an handgesetzten Werten, Abbildungen, PDF, Rauchtest und Pfade der App (jede Familie, jede Einstellung, `n` = 9, 12, 16, beide Vergleiche), Layout, Footer und Laufzeit-Importe. `test_claims.py` rechnet jede Zahl dieser README nach.
- **Kopie:** Tests vergleichen die Familien mit denen von Stück 1 bis 10, sofern die Schwester-Repos nebenan liegen.
- **Nicht getestet:** Zeiten; kein Mutationstest; Linux-CI: noch nicht gelaufen (Repo noch nicht veröffentlicht).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: fünf Experimente, Vergleiche über feste Instanzen, Grenzen, Formulierung |
| `dtp_rng.py` | SplitMix64 (Kopie aus Stück 1) |
| `dtp_instance.py` | Instanzen: sechs Familien der Flussmatrix, Raster, Handbeispiele |
| `dtp_cost.py` | Kosten, Tausch-`Δ` (Kopie aus Stück 2) |
| `dtp_landscape.py` | Aufzählung für das Optimum (Kopie aus Stück 2) |
| `dtp_assignment.py` | Ungarische Methode (Kopie aus Stück 8) |
| `dtp_place.py` | Pads, lineares System, Umgewichtung, Rundung, Kosten mit linearem Term, Abstieg (Kopie aus Stück 9) |
| `dtp_loop.py` | Pseudo-Anker, Legalisierer, Schleife (Kopie aus Stück 10) |
| `dtp_search.py` | Tauschabstieg mit Zählung, Annealing, Startlösungen, Neustarts |
| `dtp_evaluation.py` | Zeilen für die Vergleiche, Zusammenfassungen, Verdikte |
| `dtp_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `dtp_pdf_export.py` | PDF-Export des Ergebnisses |
| `dtp_constants.py` | Größen, Familien, feste Reihen, Farben, Presets |
| `dtp_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Button |
| `dtp_layout.py` | Fester Kopf (Stylesheet) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; kein `scipy` zur Laufzeit) |
| `tests/` | Abstieg und Annealing, Schleife, Platzierung, Zuordnung, Kosten, Instanzen, Landschaft, Auswertung, Verdikte, Abbildungen, Presets, Layout, AppTest, Orakel, Zahlen der README, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Tabu-Suche, Robust Tabu, Breakout Local Search, genetische Verfahren:** die Trajektorien-Linie und die Fall-Demo `dock_door-demo` zeigen sie; hier nur Abstieg und Annealing.
- **Größere Nachbarschaften** (Verschiebungen, Ketten) und **Detailplatzierung mit Dichte und Routing.**
- **Zeitmessung:** gezählt wird in Bewertungen.
- **Asymmetrische Flüsse und Abstände.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version in den App-Einstellungen prüfen (lokal Python 3.14, CI Python 3.12); der Code verwendet nur Merkmale, die in Python 3.12 laufen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
