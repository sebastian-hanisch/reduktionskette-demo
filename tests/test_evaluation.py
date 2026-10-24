"""Kennzahlen, Antwortlogik bei Abbruch, Prüfung vor der Anzeige und Messreihen."""

import dataclasses

import pytest

import red_clique as Q
import red_constants as C
import red_cover as V
import red_evaluation as ev
import red_reduction as R
from red_scenario import random_formula


def test_number_formats():
    assert ev.fmt_int(0) == "0" and ev.fmt_int(999) == "999" and ev.fmt_int(1000) == "1.000" and ev.fmt_int(1720350) == "1.720.350"
    assert ev.fmt_num(22.66) == "22,7" and ev.fmt_num(5.0, 0) == "5"
    assert ev.answer_word(True) == "Ja" and ev.answer_word(False) == "Nein" and "unbekannt" in ev.answer_word(None)


def test_settings_are_keyword_only():
    with pytest.raises(TypeError):
        ev.Settings(8, 12, 35)                      # nie positional (Memory feedback_settings_dataclass_keyword_args)


def test_chain_on_the_satisfiable_mini_formula(mini):
    a = ev.analyse_formula(ev.Settings(n=3, m=3), mini)
    assert [s.answer for s in a.stages] == [True, True, True, True]
    assert len(a.graph) == 9 and a.triangle_edges == 9 and a.conflict_edges == 6
    assert a.cover.tau == 6 and a.clique.value == 3 and not a.cover.aborted and not a.clique.aborted
    assert len(a.witness) == 3 and R.is_independent_set(a.graph, a.witness)
    assert a.decoded_ok is True and R.is_satisfying(mini, a.decoded)
    assert ev.validation_errors(a) == []


def test_chain_on_the_unsatisfiable_formula(unsat8):
    a = ev.analyse_formula(ev.Settings(n=3, m=8), unsat8)
    assert [s.answer for s in a.stages] == [False, False, False, False]
    assert a.cover.tau == 17 and a.clique.value == 7                    # alpha = 7 = m - 1, tau = 24 - 7 = 17 > 2m = 16
    assert a.witness == () and a.decoded is None and a.decoded_ok is None
    assert ev.validation_errors(a) == []


def test_stage_details_name_the_numbers(mini, unsat8):
    a = ev.analyse_formula(ev.Settings(n=3, m=3), mini)
    assert a.stages[1].detail == "α = 3" and a.stages[2].detail == "τ = 6" and a.stages[3].detail == "ω = 3"
    assert "8 Belegungen" in a.stages[0].detail
    assert "9 Knoten" not in a.stages[0].detail
    b = ev.analyse_formula(ev.Settings(n=3, m=8), unsat8)
    assert b.stages[1].detail == "α = 7" and b.stages[2].detail == "τ = 17" and b.stages[3].detail == "ω = 7"


def _cover(tau, cover, aborted, lower, nodes=100):
    return V.ExactResult(tau, tuple(cover), nodes, aborted, lower)


def _clique(value, aborted, nodes=100):
    return Q.Result("color", "degree", True, tuple(range(value)), value, nodes, 0, 0, aborted, (), 0, 0, 0, 0, False)


def test_cover_answer_branches():
    assert ev.cover_answer(3, _cover(6, range(6), False, 6)) == (True, "τ = 6")                       # fertig, τ = 2m: Ja
    assert ev.cover_answer(3, _cover(7, range(7), False, 7)) == (False, "τ = 7")                      # fertig, τ > 2m: Nein
    ans, detail = ev.cover_answer(3, _cover(None, range(5), True, 4))                                 # Abbruch, aber Überdeckung der Größe 5 <= 6 gefunden: Ja
    assert ans is True and "5 ≤ 6" in detail
    ans, detail = ev.cover_answer(3, _cover(None, range(9), True, 7))                                 # Abbruch, untere Schranke 7 > 6: Nein
    assert ans is False and "untere Schranke 7" in detail
    ans, detail = ev.cover_answer(3, _cover(None, range(9), True, 5, nodes=2000))                     # Abbruch ohne Beleg: unbekannt
    assert ans is None and "2.000 Knoten" in detail and "τ ≥ 5" in detail


def test_clique_answer_branches():
    assert ev.clique_answer(3, _clique(3, False)) == (True, "ω = 3")
    assert ev.clique_answer(3, _clique(2, False)) == (False, "ω = 2")
    ans, detail = ev.clique_answer(3, _clique(3, True))                                               # Abbruch, aber Clique der Größe m gefunden
    assert ans is True and "Größe 3" in detail
    ans, detail = ev.clique_answer(3, _clique(2, True, nodes=5000))
    assert ans is None and "5.000 Knoten" in detail and "bisher beste Clique 2" in detail


def test_budget_exhaustion_gives_unknown_answers_but_a_decided_formula():
    a = ev.analyse(ev.Settings(n=12, m=30, seed=11, budget=1_000))
    assert a.stages[0].answer is not None and a.dpll.satisfiable == (a.brute is not None)
    assert any(s.answer is None for s in a.stages[1:])
    assert ev.validation_errors(a) == []                                    # unbekannt ist kein Fehler


def test_validation_catches_broken_results(mini):
    a = ev.analyse_formula(ev.Settings(n=3, m=3), mini)
    flipped = dataclasses.replace(a, stages=(a.stages[0], dataclasses.replace(a.stages[1], answer=False)) + a.stages[2:])
    assert "Unabhängige Menge" in ev.validation_errors(flipped)[0]
    bad_set = dataclasses.replace(a, witness=(0, 1, 2))
    assert any("nicht unabhängig" in e for e in ev.validation_errors(bad_set))
    bad_back = dataclasses.replace(a, decoded_ok=False)
    assert any("erfüllt die Formel nicht" in e for e in ev.validation_errors(bad_back))
    wrong_dpll = dataclasses.replace(a, dpll=dataclasses.replace(a.dpll, satisfiable=False))
    assert any("DPLL" in e for e in ev.validation_errors(wrong_dpll))
    bad_cover = dataclasses.replace(a, cover=dataclasses.replace(a.cover, cover=()))
    assert any("überdeckt nicht" in e for e in ev.validation_errors(bad_cover))


def test_analyse_is_deterministic_and_random_formulas_are_decided_consistently():
    a, b = ev.analyse(ev.Settings(n=6, m=14, seed=3)), ev.analyse(ev.Settings(n=6, m=14, seed=3))
    assert a == b
    for seed in range(40):
        r = ev.analyse(ev.Settings(n=4, m=4 + seed % 14, seed=seed, budget=C.BUDGETS[-1]))
        assert ev.validation_errors(r) == [], seed


def test_sweep_size_matches_a_direct_recomputation():
    rows = ev.sweep_size(ms=(6, 12), n=8, seeds=(1, 2, 3))
    assert [r["m"] for r in rows] == [6, 12] and [r["nodes"] for r in rows] == [18, 36] and [r["triangle"] for r in rows] == [18, 36]
    edges = sorted(R.edge_count(R.build_graph(random_formula(8, 12, s))) for s in (1, 2, 3))
    assert rows[1]["edges"] == edges[1]                                      # Median von drei
    assert rows[1]["conflicts"] == rows[1]["edges"] - 36
    assert rows[1]["complement"] == 36 * 35 // 2 - rows[1]["edges"]


def test_sweep_size_grows_with_m():
    rows = ev.sweep_size()
    assert [r["m"] for r in rows] == list(C.SWEEP_M)
    assert all(rows[i]["edges"] < rows[i + 1]["edges"] for i in range(len(rows) - 1))
    assert all(r["edges"] <= 3 * r["m"] + r["m"] * r["m"] * 9 // 8 for r in rows)       # höchstens quadratisch (grobe Schranke)


def test_sweep_effort_structure_on_a_tiny_run():
    rows = ev.sweep_effort(ms=(6,), n=6, seeds=(1, 2), budget=2_000)
    r = rows[0]
    assert r["m"] == 6 and r["ratio"] == 1.0 and r["count"] == 2 and 0 <= r["sat"] <= 2
    assert r["dpll"] >= 1 and r["cover"] >= 0 and r["clique"] >= 0 and 0 <= r["cover_aborted"] <= 2 and 0 <= r["kernel"] <= 100


def test_yes_rows_for_satisfiable_and_unsatisfiable(mini, unsat8):
    sat = ev.yes_rows(ev.analyse_formula(ev.Settings(n=3, m=3), mini))
    assert len(sat) == 3 and sat[0]["bound"] == 9 and sat[1]["bound"] == 3 and sat[1]["verify"] == 3
    assert sat[2]["verify"] == 12 and sat[2]["search"] == 56342
    unsat = ev.yes_rows(ev.analyse_formula(ev.Settings(n=3, m=8), unsat8))
    assert len(unsat) == 1 and "Rundreise" in unsat[0]["problem"]


def test_bipartite_counts_and_refutation_rows():
    c = ev.bipartite_counts(60)
    assert c["graphs"] == 60 and c["bipartite"] + c["odd_cycle"] == 60 and c["odd_cycle"] > 0 and 3 <= c["longest_cycle"] <= 39 and c["longest_cycle"] % 2 == 1
    rows = ev.refutation_random_rows(sizes=(10, 15), formulas=6)
    assert [r["n"] for r in rows] == [10, 15] and [r["m"] for r in rows] == [43, 64]
    assert all(r["unsat"] > 0 and r["median"] >= 1 and r["max"] >= r["median"] for r in rows)
    pigeon = ev.refutation_pigeon_rows(hs=(2, 3, 4))
    assert [(r["h"], r["variables"], r["clauses"], r["nodes"]) for r in pigeon] == [(2, 6, 9, 3), (3, 12, 22, 11), (4, 20, 45, 47)]
    assert all(r["unsat"] for r in pigeon)
