"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink-Begrenzung; jedes Preset zeigt, was seine Hilfe verspricht."""

import red_constants as C
import red_evaluation as ev
import red_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regulator_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.M_MIN <= preset["m"] <= C.M_MAX and 0 <= preset["seed"] <= C.SEED_MAX and preset["budget"] in C.BUDGETS


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    assert next(iter(C.PRESETS)) == "Standardfall (Voreinstellung)"


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_coerce_limits_numbers_and_rejects_unknown_choices():
    n = P.SETTING_SPECS["n_slider"]
    assert P._coerce(n, "1") == C.N_MIN and P._coerce(n, "99") == C.N_MAX and P._coerce(n, "7") == 7 and P._coerce(n, "x") is None
    assert P._coerce(n, ["9"]) == 9 and P._coerce(n, []) is None
    b = P.SETTING_SPECS["budget_select"]
    assert P._coerce(b, "10000") == 10000 and P._coerce(b, "123") is None


def test_presets_show_what_their_help_promises():
    r = {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}
    std = r["Standardfall (Voreinstellung)"]
    assert all(s.answer is True for s in std.stages) and std.decoded_ok is True
    teach = r["Lehrbeispiel (3 Klauseln)"]
    assert len(teach.graph) == 9 and all(s.answer is True for s in teach.stages)
    unsat = r["Unerfüllbar (alle Belegungen verboten)"]
    assert all(s.answer is False for s in unsat.stages) and unsat.brute is None
    near = r["Nahe der Schwelle (m/n = 4)"]
    assert near.dpll.nodes < 20 and near.cover.aborted and near.clique.aborted              # DPLL entscheidet, beide Graphlöser brechen ab
    big = r["Größte Formel (Budget reicht nicht)"]
    assert big.settings.n == C.N_MAX and big.settings.m == C.M_MAX and big.cover.aborted and not big.clique.aborted
    for a in r.values():
        assert ev.validation_errors(a) == []
