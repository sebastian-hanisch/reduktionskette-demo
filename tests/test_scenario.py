"""Szenario: deterministisch, plattformunabhängig (eigener Generator), Klauseln gültig, wachsende Formel."""

import pytest

from red_scenario import SplitMix64, literal_name, random_clause, random_formula, random_graph, sparse_random_graph


def test_splitmix64_reference_values():
    """Referenzwerte von SplitMix64 mit Seed 0 (aus der Definition von Hand berechnet: 0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4)."""
    r = SplitMix64(0)
    assert r.next() == 0xE220A8397B1DCDAF
    assert r.next() == 0x6E789E6AA1B965F4


def test_splitmix64_below_and_coin_cover_their_ranges():
    r = SplitMix64(5)
    assert {r.below(4) for _ in range(200)} == {0, 1, 2, 3}
    assert {r.coin() for _ in range(50)} == {True, False}


def test_clause_has_three_distinct_variables_in_range():
    r = SplitMix64(1)
    for n in (3, 4, 12):
        for _ in range(100):
            c = random_clause(n, r)
            assert len(c) == 3 and len({abs(x) for x in c}) == 3 and all(1 <= abs(x) <= n for x in c)


def test_formula_is_deterministic_and_seeds_differ():
    assert random_formula(8, 12, 35) == random_formula(8, 12, 35)
    assert random_formula(8, 12, 35) != random_formula(8, 12, 36)
    assert random_formula(5, 0, 1) == []


def test_formula_grows_by_appending_clauses():
    big = random_formula(8, 30, 99)
    for m in (1, 6, 12, 29):
        assert random_formula(8, m, 99) == big[:m]


def test_formula_needs_three_variables():
    with pytest.raises(ValueError):
        random_formula(2, 3, 1)


def test_random_graph_has_exactly_the_requested_edges():
    for n, e in ((6, 0), (6, 7), (6, 15), (20, 57)):
        g = random_graph(n, e, 4)
        assert len(g) == n and sum(len(a) for a in g) == 2 * e
        assert all(v not in g[v] and all(v in g[w] for w in g[v]) for v in range(n))
    assert random_graph(9, 11, 3) == random_graph(9, 11, 3) and random_graph(9, 11, 3) != random_graph(9, 11, 4)
    with pytest.raises(ValueError):
        random_graph(4, 7, 1)


def test_sparse_graph_density_follows_per_mille():
    assert sum(len(a) for a in sparse_random_graph(30, 0, 1)) == 0
    assert sum(len(a) for a in sparse_random_graph(30, 1000, 1)) == 30 * 29
    mid = sum(len(a) for a in sparse_random_graph(40, 500, 2)) / (40 * 39)
    assert 0.4 < mid < 0.6


def test_literal_names():
    assert literal_name(3) == "x3" and literal_name(-2) == "¬x2"
