"""DPLL gegen Brute Force und Handrechnung; Zertifikat-Prüfer mit absichtlich verfälschten Eingaben; Schubfach-Formeln."""

import pytest

import red_certificates as K
import red_dpll as D
import red_reduction as R
from red_scenario import random_formula, sparse_random_graph


def test_dpll_on_the_mini_formulas(mini, unsat8):
    r = D.dpll(mini)
    assert r.satisfiable and R.is_satisfying(mini, {**{v: False for v in (1, 2, 3)}, **r.assignment})
    u = D.dpll(unsat8)
    assert not u.satisfiable and u.assignment is None and u.nodes > 1


def test_dpll_node_counts_by_hand():
    # (x1): ein Knoten, Einheitsklausel erzwingt x1; Formel ohne Klauseln: ein Knoten
    assert D.dpll([(1,)]).nodes == 1 and D.dpll([]).nodes == 1
    # (x1) ∧ (¬x1): Einheitspropagation führt in einen Widerspruch, ein Knoten
    r = D.dpll([(1,), (-1,)])
    assert not r.satisfiable and r.nodes == 1
    # (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (x1 ∨ ¬x2) ∧ (¬x1 ∨ ¬x2): unerfüllbar, Wurzel verzweigt, beide Äste enden durch Propagation: 3 Knoten
    assert D.dpll([(1, 2), (-1, 2), (1, -2), (-1, -2)]).nodes == 3


def test_propagate_by_hand():
    clauses, asg = D.propagate([(1,), (-1, 2), (2, 3)], {})
    assert asg == {1: True, 2: True} and clauses == []
    assert D.propagate([(1,), (-1,)], {}) is None
    clauses, asg = D.propagate([(1, 2, 3)], {1: False})
    assert clauses == [(2, 3)] and asg == {1: False}


def test_choose_variable_prefers_frequent_then_small():
    assert D.choose_variable([(1, 2), (2, 3), (3, 4)]) == 2          # 2 und 3 kommen je zweimal vor: die kleinere Nummer
    assert D.choose_variable([(5, 6), (-6, 7)]) == 6


def test_dpll_matches_brute_force():
    unsat = 0
    for seed in range(200):
        n = 3 + seed % 6
        m = 1 + (seed * 7) % (7 * n)
        f = random_formula(n, m, seed)
        r = D.dpll(f)
        b = R.brute_force_sat(n, f)
        assert r.satisfiable == (b is not None), (n, m, seed)
        unsat += b is None
        if r.satisfiable:
            full = {v: False for v in range(1, n + 1)}
            full.update(r.assignment)
            assert R.is_satisfying(f, full), (n, m, seed)
    assert unsat > 20, "zu wenige unerfüllbare Formeln: der Nein-Ausgang wird nicht geprüft"


def test_pigeonhole_formulas_are_unsatisfiable_and_have_known_node_counts():
    for h in (1, 2, 3):
        f, nv = K.pigeonhole(h)
        assert R.brute_force_sat(nv, f) is None if nv <= 12 else True
    expected = {2: 3, 3: 11, 4: 47, 5: 239, 6: 1439}                # gemessen mit diesem DPLL (Vormessung 2026-10-21, im Test fest)
    for h, nodes in expected.items():
        f, nv = K.pigeonhole(h)
        r = D.dpll(f)
        assert not r.satisfiable and r.nodes == nodes, h


def test_pigeonhole_sizes_by_hand():
    f, nv = K.pigeonhole(2)                       # 3 Tauben, 2 Fächer: 6 Variablen; 3 lange Klauseln + 2 Fächer · 3 Paare = 9
    assert nv == 6 and len(f) == 9 and f[:3] == [(1, 2), (3, 4), (5, 6)]
    assert (-1, -3) in f and (-2, -6) in f


# --- Zertifikat-Prüfer ----------------------------------------------------------------------------------------------------------------------------


def test_verify_assignment_accepts_and_rejects(mini):
    ok, reads = K.verify_assignment(mini, {1: True, 2: False, 3: True})
    assert ok and reads == 1 + 2 + 1                         # Klausel 1: x1 wahr (1 Lesen); Klausel 2: ¬x1 falsch, ¬x2 wahr (2); Klausel 3: x1 wahr (1)
    bad, reads = K.verify_assignment(mini, {1: False, 2: True, 3: True})
    assert not bad and reads == 2 + 1 + 3          # Klausel 1: x1 falsch, x2 wahr (2); Klausel 2: ¬x1 wahr (1); Klausel 3: alle drei Literale falsch (3)
    assert K.accesses_verify_assignment(3) == 9


def test_verify_independent_set_accepts_and_rejects(mini):
    g = R.build_graph(mini)
    assert K.verify_independent_set(g, (0, 5, 6)) == (True, 3)
    assert K.verify_independent_set(g, (0, 3, 6)) == (False, 1)        # Paar (0, 3) ist eine Konfliktkante: die Prüfung bricht beim ersten Paar ab
    assert K.pairs_verify_set(1) == 0 and K.pairs_verify_set(3) == 3 and K.pairs_verify_set(10) == 45


def test_tour_certificate_formulas():
    assert K.accesses_verify_tour(12) == 12
    assert K.accesses_search_tour(12) == 56342 and K.accesses_search_tour(4) == 18 and K.accesses_search_tour(2) == 2 and K.accesses_search_tour(1) == 0


def test_two_color_or_odd_cycle_by_hand():
    path = tuple(frozenset(s) for s in ({1}, {0, 2}, {1}))                          # Pfad 0-1-2: bipartit
    kind, color, steps = K.two_color_or_odd_cycle(path)
    assert kind == "bipartite" and K.check_two_coloring(path, color) and steps == 4
    triangle = tuple(frozenset(s) for s in ({1, 2}, {0, 2}, {0, 1}))
    kind, cycle, _ = K.two_color_or_odd_cycle(triangle)
    assert kind == "odd_cycle" and sorted(cycle) == [0, 1, 2] and K.check_odd_cycle(triangle, cycle)
    five = tuple(frozenset({(i - 1) % 5, (i + 1) % 5}) for i in range(5))           # Fünfeck: ungerader Kreis der Länge 5
    kind, cycle, _ = K.two_color_or_odd_cycle(five)
    assert kind == "odd_cycle" and len(cycle) == 5 and K.check_odd_cycle(five, cycle)
    assert K.two_color_or_odd_cycle(()) == ("bipartite", (), 0)


def test_checkers_reject_broken_certificates():
    triangle = tuple(frozenset(s) for s in ({1, 2}, {0, 2}, {0, 1}))
    assert not K.check_two_coloring(triangle, (0, 1, 0))                            # Kante 0-2 hat gleiche Farben
    assert not K.check_two_coloring(triangle, (0, 1))                               # zu kurz
    assert not K.check_odd_cycle(triangle, (0, 1))                                  # gerade Länge
    path = tuple(frozenset(s) for s in ({1}, {0, 2}, {1}))
    assert not K.check_odd_cycle(path, (0, 1, 2))                                   # 2-0 ist keine Kante
    assert not K.check_odd_cycle(triangle, (0, 1, 1))                               # Knoten doppelt
    assert K.check_odd_cycle(triangle, (0, 1, 2)) and not K.check_odd_cycle(triangle, ())


def test_every_random_graph_has_exactly_one_kind_of_certificate():
    kinds = {"bipartite": 0, "odd_cycle": 0}
    for seed in range(150):
        n = 6 + seed % 30
        adj = sparse_random_graph(n, 40 + (seed * 13) % 160, seed)
        kind, cert, steps = K.two_color_or_odd_cycle(adj)
        kinds[kind] += 1
        assert (K.check_two_coloring(adj, cert) if kind == "bipartite" else K.check_odd_cycle(adj, cert)), (n, seed)
        assert steps <= sum(len(a) for a in adj)                                    # jeder Knoten wird höchstens einmal abgearbeitet: jede Kante höchstens zweimal gelesen
    assert kinds["bipartite"] > 10 and kinds["odd_cycle"] > 10, kinds


# --- Lücken aus der Mutationsprüfung ----------------------------------------------------------------------------------------------------------------


def test_search_formula_at_three_places():
    """n = 3: (2)(1) · 2^0 + 2 · 2 = 6 Held–Karp-Zugriffe (Mutation der Grenze n >= 3)."""
    assert K.accesses_search_tour(3) == 6 and K.accesses_search_tour(5) == 4 * 3 * 4 + 8


def test_colors_are_zero_or_one_and_an_isolated_last_node_is_colored():
    """Die Breitensuche färbt mit 0 und 1; auch ein isolierter Knoten am Ende bekommt eine Farbe (Mutationen von Farbformel und Startknoten-Schleife)."""
    kind, color, _ = K.two_color_or_odd_cycle(tuple(frozenset(s) for s in ({1}, {0, 2}, {1}, frozenset())))
    assert kind == "bipartite" and color == (0, 1, 0, 0)
    kind, color, _ = K.two_color_or_odd_cycle(tuple(frozenset(s) for s in ({1}, {0}, frozenset())))
    assert color == (0, 1, 0)
    for seed in range(30):
        kind, color, _ = K.two_color_or_odd_cycle(sparse_random_graph(12, 80, 9000 + seed))
        if kind == "bipartite":
            assert set(color) <= {0, 1}


def test_independent_set_check_reads_pairs_in_ascending_order(mini):
    """Die Prüfung geht die Paare aufsteigend durch: bei (0, 1, 3) scheitert schon das erste Paar (0, 1), eine Dreieckskante (Mutation der Reihenfolge)."""
    g = R.build_graph(mini)
    assert K.verify_independent_set(g, (3, 1, 0)) == (False, 1)
