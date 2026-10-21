"""Die Reduktionskette gegen Handrechnung an den Mini-Formeln (conftest): jede Einheit einzeln (DEMO-PLAYBOOK §1b)."""

import pytest

import red_reduction as R


def test_literal_true_and_is_satisfying(mini):
    assignment = {1: True, 2: False, 3: True}
    assert R.literal_true(1, assignment) and not R.literal_true(-1, assignment) and R.literal_true(-2, assignment)
    assert R.is_satisfying(mini, assignment)
    assert not R.is_satisfying(mini, {1: False, 2: True, 3: True})           # Klausel 3 (x1 ∨ ¬x2 ∨ ¬x3) ist falsch, die beiden anderen sind wahr


def test_brute_force_sat_on_the_mini_formulas(mini, unsat8):
    found = R.brute_force_sat(3, mini)
    assert found is not None and R.is_satisfying(mini, found)
    assert R.brute_force_sat(3, unsat8) is None
    assert R.brute_force_sat(3, []) is not None                                # keine Klausel: jede Belegung erfüllt


def test_node_numbers():
    assert [R.node(i, j) for i in range(3) for j in range(3)] == list(range(9))


def test_triangle_edges_by_hand():
    assert sorted(R.clause_triangle_edges(2)) == [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)]
    assert R.clause_triangle_edges(0) == []


def test_conflict_edges_by_hand(mini):
    assert sorted(R.conflict_edges(mini)) == [(0, 3), (1, 4), (1, 7), (2, 8), (3, 6), (5, 8)]


def test_no_conflict_inside_one_clause_and_none_for_equal_literals():
    # Klauseln (x1 ∨ x2 ∨ x3) und (x1 ∨ x2 ∨ x3): gleiche Literale widersprechen sich nicht
    assert R.conflict_edges([(1, 2, 3), (1, 2, 3)]) == []
    # (x1 ∨ x2 ∨ x3) gegen (¬x1 ∨ x4 ∨ x5): genau eine Konfliktkante, x1 (Knoten 0) gegen ¬x1 (Knoten 3)
    assert R.conflict_edges([(1, 2, 3), (-1, 4, 5)]) == [(0, 3)]


def test_build_graph_sizes_by_hand(mini, unsat8):
    g = R.build_graph(mini)
    assert len(g) == 9 and R.edge_count(g) == 15
    assert all(v not in g[v] for v in range(9)) and all(v in g[w] for v in range(9) for w in g[v])       # schleifenfrei, symmetrisch
    h = R.build_graph(unsat8)
    assert len(h) == 24 and R.edge_count(h) == 72


def test_complement_by_hand(mini, unsat8):
    g = R.build_graph(mini)
    c = R.complement(g)
    assert R.edge_count(c) == 36 - 15 == 21
    assert all(c[v] == frozenset(set(range(9)) - set(g[v]) - {v}) for v in range(9))
    assert R.complement(R.complement(g)) == g
    assert R.edge_count(R.complement(R.build_graph(unsat8))) == 276 - 72 == 204


def test_cover_threshold_and_gallai():
    assert R.cover_threshold(3) == 6 and R.cover_threshold(8) == 16
    assert R.independent_set_from_cover(9, (1, 2, 3, 4, 7, 8)) == (0, 5, 6)
    assert R.independent_set_from_cover(3, ()) == (0, 1, 2)


def test_independent_set_and_clique_checkers(mini):
    g = R.build_graph(mini)
    assert R.is_independent_set(g, (0, 5, 6))
    assert not R.is_independent_set(g, (0, 1))                                  # Dreieckskante
    assert not R.is_independent_set(g, (0, 3))                                  # Konfliktkante
    assert R.is_clique(R.complement(g), (0, 5, 6)) and not R.is_clique(R.complement(g), (0, 1))
    assert R.is_independent_set(g, ()) and R.is_clique(g, ())


def test_decode_assignment_by_hand(mini):
    assignment = R.decode_assignment(mini, (0, 5, 6), 3)
    assert assignment == {1: True, 3: True, 2: False}                          # x1 wahr, x3 wahr, x2 unberührt: falsch
    assert R.is_satisfying(mini, assignment)


def test_decode_ignores_variables_without_a_node():
    formula = [(1, 2, 3)]
    assert R.decode_assignment(formula, (1,), 5) == {2: True, 1: False, 3: False, 4: False, 5: False}


def test_independent_set_of_size_m_decodes_to_a_model(mini):
    """Jede unabhängige Menge der Größe m ergibt eine erfüllende Belegung (alle Mengen von Hand aufgezählt: eine Wahl je Klausel, ohne Konflikt)."""
    g = R.build_graph(mini)
    sets = [(a, b, c) for a in (0, 1, 2) for b in (3, 4, 5) for c in (6, 7, 8) if R.is_independent_set(g, (a, b, c))]
    assert (0, 5, 6) in sets and len(sets) > 0
    for s in sets:
        assert R.is_satisfying(mini, R.decode_assignment(mini, s, 3)), s


@pytest.mark.parametrize("m", [1, 4, 11])
def test_node_count_is_three_m(m):
    formula = [(1, 2, 3)] * m
    assert len(R.build_graph(formula)) == 3 * m
    assert len(R.clause_triangle_edges(m)) == 3 * m


# --- Lücken aus der Mutationsprüfung ----------------------------------------------------------------------------------------------------------------


def test_brute_force_finds_every_one_of_the_eight_assignments_by_unit_clauses():
    """Drei Einheitsklauseln legen die Belegung eindeutig fest: die Probe muss jede der acht Belegungen finden, auch die mit x3 = wahr (Mutation der Bit-Zuordnung)."""
    import itertools
    for pattern in itertools.product((True, False), repeat=3):
        formula = [(v if val else -v,) for v, val in zip((1, 2, 3), pattern)]
        assert R.brute_force_sat(3, formula) == {1: pattern[0], 2: pattern[1], 3: pattern[2]}, pattern


def test_no_conflict_edges_inside_one_clause():
    """Konfliktkanten verbinden nur Knoten VERSCHIEDENER Klauseln (Mutation der Schleifengrenze k > i); eine Klausel mit x und nicht x bekommt keine Selbstkante."""
    assert R.conflict_edges([(1, -1, 2)]) == []
    assert R.conflict_edges([(1, -1, 2), (3, 4, 5)]) == []


def test_decode_prefers_the_smaller_node_for_an_inconsistent_set(mini):
    """Eine nicht unabhängige Menge ist kein gültiger Beleg; für sie gilt festgelegt: der kleinere Knoten setzt die Variable zuerst (Mutation der Reihenfolge).
    Knoten 0 = x1 (wahr), Knoten 3 = ¬x1 (falsch): x1 wird wahr."""
    assert R.decode_assignment(mini, (3, 0), 3)[1] is True
    assert R.decode_assignment(mini, (0, 3), 3)[1] is True


def test_variables_of_is_ascending():
    assert R.variables_of([(3, -1, 2), (-5, 1, 4)]) == [1, 2, 3, 4, 5] and R.variables_of([]) == []
