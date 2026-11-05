"""Pfade der App, die der Rauchtest nicht erreicht: die Experimente im Seiteninhalt, PDF, jede Familie, jede Einstellung, große Instanzen, die Rechenknöpfe (DEMO-PLAYBOOK §1d)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import dtp_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
KIND = {"family_select": "selectbox", "n_select": "select_slider", "seed_input": "number_input", "pads_select": "select_slider", "start_select": "selectbox", "method_select": "selectbox", "t0_select": "select_slider", "budget_select": "select_slider"}


def _app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    for key, value in state.items():
        getattr(at.sidebar, KIND[key])(key=key).set_value(value)
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.success) + list(at.info) + list(at.warning) + list(at.error) + list(at.markdown))


def test_default_page_shows_the_metrics_and_the_verdicts():
    at = _app()
    values = {m.label: m.value for m in at.metric}
    assert set(values) == {"Lücke am Start", "Lücke nach Tauschabstieg", "Bewertungen", "Optimum", "Pads"}
    assert values["Optimum"] == "337" and values["Lücke am Start"] == "12,8 %" and values["Lücke nach Tauschabstieg"] == "2,7 %" and values["Bewertungen"] == "112" and values["Pads"] == "4"
    text = _texts(at)
    for part in ("Familie **Zwei Cluster**, 8 Bauteile, Raster 2×4, Seed 46, 4 Pads, Start Schleife (Stück 10)", "braucht **3 Schritte** und 112 Bewertungen", "Zufall: Start 448", "Neustarts aus Zufall: 1 Neustart", "Experiment 1 bis 5"):
        assert part in text, part


def test_the_experiments_the_hand_example_the_limits_table_and_the_formulation_are_on_the_page():
    at = _app()
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬 Experiment")] == [f"🔬 Experiment {i}" for i in (1, 2, 3, 4, 5)] and "🚧 Wo die Annahmen enden" in headings
    assert [e.label for e in at.expander] == ["So funktioniert es", "Handbeispiel zum Nachrechnen", "📐 Mathematische Formulierung"]
    assert not at.error and len(at.get("plotly_chart")) == 6
    assert any("Kosten **6**" in str(m.value) and "6 Bewertungen" in str(m.value) for m in at.markdown)


def test_every_family_every_setting_and_size_renders():
    for fam in C.FAMILIES:
        at = _app(family_select=fam, n_select=6)
        assert f"Familie **{C.FAMILY_NAMES[fam]}**" in _texts(at) and len(at.get("plotly_chart")) == 6
    for key, values in (("pads_select", C.PAD_CHOICES), ("start_select", C.START_CHOICES), ("method_select", C.METHODS), ("t0_select", C.T0_CHOICES), ("budget_select", C.BUDGET_FACTORS)):
        for value in values:
            at = _app(n_select=6, **{key: value})
            assert len(at.get("plotly_chart")) == 6 and not at.exception, (key, value)
    for n in (9, 12, 16):
        at = _app(n_select=n, budget_select=0.5)
        assert f"{n} Bauteile" in _texts(at) and len(at.get("plotly_chart")) == 6


def test_the_start_and_the_method_change_the_result():
    base = {m.label: m.value for m in _app().metric}
    rnd = {m.label: m.value for m in _app(start_select="random").metric}
    assert base["Lücke am Start"] != rnd["Lücke am Start"]
    an = _app(method_select="anneal", t0_select=0.1)
    labels = {m.label: m.value for m in an.metric}
    assert "Lücke nach Simulated Annealing" in labels and labels["Bewertungen"] == "1 500" and "angenommen" in " ".join(str(m.delta) for m in an.metric if m.label == "Bewertungen")
    assert "Annealing aus Schleife (Stück 10)" not in _texts(an) and "Starttemperatur 0,1 · s" in _texts(an)


def test_the_pdf_button_makes_a_download():
    at = _app(n_select=6)
    at.button(key="pdf_make").click().run()
    assert not at.exception
    assert any(d.proto.label == "⬇️ PDF herunterladen" for d in at.get("download_button"))


def test_the_comparison_buttons_fill_their_sections(monkeypatch):
    monkeypatch.setattr(C, "SWEEP_SEEDS", C.SWEEP_SEEDS[:2])                       # nur für die Geschwindigkeit des Tests: die echten Reihen stehen in test_claims.py
    monkeypatch.setattr(C, "LARGE_SEEDS", {12: C.SWEEP_SEEDS[:1], 16: C.SWEEP_SEEDS[:1]})
    at = _app(n_select=6)
    assert [b.label for b in at.button if "⏱️" in b.label] == ["⏱️ Vergleich rechnen (n = 8)", "⏱️ Große Instanzen rechnen (n = 12, 16)"]
    at.button(key="sweep_button").click().run()
    text = _texts(at)
    assert not at.exception and "Bei n = 8, Median über 36 Instanzen (alle Pad-Zahlen)" in text and "Annealing aus Zufall (Starttemperatur 2 · s" in text and "beste von 1 / 3 / 6 / 20 Abstiegen aus Zufallsstarts" in text and len(at.get("plotly_chart")) == 6 + 2
    at.button(key="large_button").click().run()
    text = _texts(at)
    assert not at.exception and "Bei n = 12, Median über 18 Instanzen" in text and "Bei n = 16, Median über 18 Instanzen" in text and "obere Grenze der Lücke" in text and len(at.get("plotly_chart")) == 6 + 2 + 4
