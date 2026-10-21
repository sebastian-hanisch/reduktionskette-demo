"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


# --- Eckfall-Matrix über die Regler (DEMO-PLAYBOOK §1d) und Permalink -----------------------------------------------------------------------------

import pytest  # noqa: E402

import red_presets as P  # noqa: E402

REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio")


def _widget(at, key):
    for art in REGLER_ARTEN:
        try:
            return getattr(at.sidebar, art)(key=key)
        except KeyError:
            continue
    raise AssertionError(f"Regler {key} steht nicht in der Seitenleiste")


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_every_setting_at_each_extreme_does_not_raise(state_key):
    spec = P.SETTING_SPECS[state_key]
    for value in (spec.lo, spec.hi):
        at = _fresh_app()
        _widget(at, state_key).set_value(value).run(timeout=TIMEOUT)
        assert not at.exception, (state_key, value, [str(e) for e in at.exception])


@pytest.mark.parametrize("edge", ["lo", "hi"])
def test_all_minima_and_all_maxima_together_do_not_raise(edge):
    at = _fresh_app()
    for state_key, spec in P.SETTING_SPECS.items():
        _widget(at, state_key).set_value(getattr(spec, edge))
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]


def test_permalink_sets_the_controls_and_clamps_values():
    at = AppTest.from_file(APP_PATH)
    at.query_params["n"] = "99"
    at.query_params["m"] = "1"
    at.query_params["b"] = "1000"
    at.query_params["seed"] = "abc"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state["n_slider"] == 12 and at.session_state["m_slider"] == 3          # auf die Reglergrenzen begrenzt
    assert at.session_state["budget_select"] == 1000 and at.session_state["seed_input"] == 35  # unlesbarer Seed: Standard


def test_default_view_shows_a_success_verdict_and_both_tabs():
    at = _fresh_app()
    assert any("Alle vier Stufen antworten **Ja**" in s.value for s in at.success)
    assert [t.label for t in at.tabs] == ["🔗 Reduktionskette", "🧾 Zertifikate"]
    assert not at.error and not at.warning


def test_exhausted_budget_shows_a_warning_not_an_empty_view():
    at = AppTest.from_file(APP_PATH)
    at.query_params["n"] = "7"
    at.query_params["m"] = "28"
    at.query_params["seed"] = "7"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("reicht nicht" in w.value for w in at.warning)
    assert not at.error
