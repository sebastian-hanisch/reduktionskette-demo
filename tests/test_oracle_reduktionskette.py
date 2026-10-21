"""Orakel-Test: die Reduktionskette gegen unabhängige Rechenwege (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK).

- F erfüllbar: Brute Force über alle 2^n Belegungen (n <= 5) gegen die vier Aussagen der Kette.
- alpha(G_F): CP-SAT (Solver-Modell, anderer Rechenweg als die kopierte Verzweigung) und Aufzählen aller Teilmengen bei kleinen Graphen.
- DPLL: Brute Force über alle Belegungen (Erfüllbarkeit und gefundene Belegung); bipartit: Aufzählen aller 2-Färbungen gegen die Breitensuche.
- Beide Seiten der Kette werden ausgeführt: erfüllbare UND unerfüllbare Formeln (sonst bliebe die Nein-Hälfte der Reduktion ungeprüft).
Im Repo laufen kleine Fassungen (unter 10 s); der große Lauf im Scratch-Ordner ist in der README genannt. Das Orakel ist an der Mini-Formel von Hand geprüft (conftest: alpha 3, tau 6; unsat8: alpha 7, tau 17)."""

import pytest

import itertools

import red_certificates as K
import red_clique as Q
import red_cover as V
import red_dpll as D
import red_reduction as R
from red_scenario import random_formula, sparse_random_graph


def _cpsat_alpha(adj):
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
    n = len(adj)
    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{v}") for v in range(n)]
    for a in range(n):
        for b in adj[a]:
            if a < b:
                model.Add(x[a] + x[b] <= 1)
    model.Maximize(sum(x))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 20
    assert solver.Solve(model) == cp_model.OPTIMAL
    return int(round(solver.ObjectiveValue()))


def _chain(formula, n):
    """Alle Stufen einer Formel: (erfüllbar nach Brute Force, alpha nach Clique, tau nach Überdeckung, Clique, Überdeckung)."""
    g = R.build_graph(formula)
    N = len(g)
    c = Q.largest_clique(R.complement(g), [1] * N, bound="color", order="degree", prune=True, budget=100_000)
    v = V.exact_cover(g, budget=100_000)
    return R.brute_force_sat(n, formula), g, c, v


def test_oracle_on_the_mini_formulas_by_hand(mini, unsat8):
    sat, g, c, v = _chain(mini, 3)
    assert sat is not None and c.value == 3 and v.tau == 6
    assert _cpsat_alpha(g) == 3
    sat, g, c, v = _chain(unsat8, 3)
    assert sat is None and c.value == 7 and v.tau == 17 and not c.aborted and not v.aborted
    assert _cpsat_alpha(g) == 7


def test_chain_agrees_with_brute_force_in_both_directions():
    sat_count = unsat_count = 0
    for seed in range(160):
        n = 3 + seed % 3
        m = 6 + (seed * 5) % 17
        f = random_formula(n, m, 500 + seed)
        sat, g, c, v = _chain(f, n)
        if c.aborted or v.aborted:
            continue
        is_sat = sat is not None
        assert (c.value == m) == is_sat, (n, m, seed)                    # alpha = m  <=>  erfüllbar
        assert v.tau == len(g) - c.value, (n, m, seed)                   # Gallai: tau = 3m - alpha
        assert (v.tau <= R.cover_threshold(m)) == is_sat, (n, m, seed)   # tau <= 2m  <=>  erfüllbar
        assert R.is_independent_set(g, c.clique) and R.is_clique(R.complement(g), c.clique)
        assert V.is_cover(g, v.cover) and len(v.cover) == v.tau
        if is_sat:
            sat_count += 1
            back = R.decode_assignment(f, c.clique, n)                   # Rückweg: die Belegung erfüllt F
            assert R.is_satisfying(f, back), (n, m, seed)
            back2 = R.decode_assignment(f, R.independent_set_from_cover(len(g), v.cover), n)
            assert R.is_satisfying(f, back2), (n, m, seed)
        else:
            unsat_count += 1
            assert c.value < m, (n, m, seed)
    assert sat_count > 20 and unsat_count > 20, (sat_count, unsat_count)


def test_alpha_agrees_with_cp_sat():
    for seed in range(20):
        n = 3 + seed % 3
        m = 5 + (seed * 3) % 14
        f = random_formula(n, m, 900 + seed)
        sat, g, c, v = _chain(f, n)
        assert not c.aborted
        assert c.value == _cpsat_alpha(g), (n, m, seed)


def test_alpha_agrees_with_enumeration_on_small_graphs():
    for seed in range(40):
        f = random_formula(3 + seed % 3, 2 + seed % 4, 1300 + seed)       # bis 15 Knoten: alle Teilmengen aufzählbar
        g = R.build_graph(f)
        c = Q.largest_clique(R.complement(g), [1] * len(g), bound="color", order="degree", prune=True)
        assert c.value == Q.brute_force_max_independent_set(g, [1] * len(g)), seed


def test_dpll_matches_brute_force_and_returns_a_model():
    unsat = 0
    for seed in range(120):
        n = 3 + seed % 6
        f = random_formula(n, 1 + (seed * 7) % (7 * n), 3000 + seed)
        r = D.dpll(f)
        b = R.brute_force_sat(n, f)
        assert r.satisfiable == (b is not None), (n, seed)
        unsat += b is None
        if r.satisfiable:
            full = {v: False for v in range(1, n + 1)}
            full.update(r.assignment)
            assert R.is_satisfying(f, full), (n, seed)
        else:
            assert r.assignment is None
    assert unsat > 10, "zu wenige unerfüllbare Formeln: der Nein-Ausgang wird nicht geprüft"


def test_two_color_or_odd_cycle_matches_enumeration_of_all_two_colorings():
    bip = odd = 0
    for seed in range(120):
        n = 3 + seed % 8
        adj = sparse_random_graph(n, 150 + (seed * 17) % 300, 4000 + seed)
        colorable = any(all(((c >> a) & 1) != ((c >> b) & 1) for a in range(n) for b in adj[a]) for c in range(1 << n))
        kind, cert, _ = K.two_color_or_odd_cycle(adj)
        assert (kind == "bipartite") == colorable, (n, seed)
        assert K.check_two_coloring(adj, cert) if colorable else K.check_odd_cycle(adj, cert), (n, seed)
        bip += colorable
        odd += not colorable
    assert bip > 10 and odd > 10, (bip, odd)


def test_odd_cycle_exists_exactly_when_enumeration_finds_one():
    """Gegenprobe des Nein-Belegs: jeder gemeldete ungerade Kreis ist wirklich ein Kreis ungerader Länge im Graphen (Aufzählen aller Knotenfolgen bis Länge 5 bei kleinen Graphen)."""
    for seed in range(60):
        n = 4 + seed % 4
        adj = sparse_random_graph(n, 300, 5000 + seed)
        has_odd = any(
            all(p[(i + 1) % k] in adj[p[i]] for i in range(k))
            for k in (3, 5) if k <= n for p in itertools.permutations(range(n), k)
        )
        kind, cert, _ = K.two_color_or_odd_cycle(adj)
        if has_odd:
            assert kind == "odd_cycle", (n, seed)
        else:
            assert kind == "bipartite" or len(cert) > 5, (n, seed)
