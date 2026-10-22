"""Jede Zahl der README steht hier und wird über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Alle Instanzen kommen aus dem eigenen SplitMix64-Generator (plattform- und versionsunabhängig); Zähler sind ganzzahlig und exakt, Mediane über eine gerade Zahl von Werten
und Prozentanteile als Bänder."""

import pytest

import red_certificates as K
import red_constants as C
import red_dpll as D
import red_evaluation as ev
import red_reduction as R

# --- Befund 1: die Kette in der Handrechnung ----------------------------------------------------------------------------------------------------


def test_claim_mini_formula_by_hand(mini):
    """README, Lehrbeispiel: 3 Klauseln, 9 Knoten, 9 Dreiecks- und 6 Konfliktkanten (15), Komplement 21; α = 3, τ = 6 = 2m; erfüllbar."""
    a = ev.analyse_formula(ev.Settings(n=3, m=3), mini)
    assert (len(a.graph), a.triangle_edges, a.conflict_edges) == (9, 9, 6)
    assert R.edge_count(R.complement(a.graph)) == 21
    assert (a.cover.tau, a.clique.value) == (6, 3) and all(s.answer is True for s in a.stages) and a.decoded_ok is True


def test_claim_unsatisfiable_formula_by_hand(unsat8):
    """README, unerfüllbares Beispiel: alle acht Klauseln über drei Variablen: 24 Knoten, 72 Kanten (24 + 48), Komplement 204; α = 7 = m − 1, τ = 17 > 16."""
    a = ev.analyse_formula(ev.Settings(n=3, m=8), unsat8)
    assert (len(a.graph), a.triangle_edges, a.conflict_edges) == (24, 24, 48)
    assert R.edge_count(R.complement(a.graph)) == 204
    assert (a.cover.tau, a.clique.value) == (17, 7) and all(s.answer is False for s in a.stages)


# --- Befund 2: Größe der Reduktion ---------------------------------------------------------------------------------------------------------------


def test_claim_size_of_the_reduction():
    """README, Größentabelle (n = 8, Median über 5 feste Formeln): m = 6, 12, 18, 24, 30: Knoten 3m; Kanten 27, 75, 143, 235, 346; davon Konflikt 9, 39, 89, 163, 256; Komplement 126, 555, 1.288, 2.321, 3.659."""
    rows = ev.sweep_size()
    assert [r["nodes"] for r in rows] == [18, 36, 54, 72, 90]
    assert [r["edges"] for r in rows] == [27, 75, 143, 235, 346]
    assert [r["conflicts"] for r in rows] == [9, 39, 89, 163, 256]
    assert [r["complement"] for r in rows] == [126, 555, 1288, 2321, 3659]


# --- Befund 3: Aufwand der Löser auf Reduktionsgraphen --------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def effort():
    """Die Messreihe läuft einmal je Testlauf (rund 12 Sekunden) und dient drei Tests."""
    return ev.sweep_effort()


def test_claim_effort_of_the_solvers_against_dpll_and_random_graphs(effort):
    """README, Aufwandstabelle (n = 8, Budget 20.000 Knoten, Median über 5 feste Formeln): m, erfüllbar, DPLL, Überdeckung G_F (Abbrüche), Clique G_F (Abbrüche), Überdeckung Zufallsgraph (Abbrüche), Clique Zufallsgraph (Abbrüche)."""
    rows = {r["m"]: r for r in effort}
    expected = {
        6: (5, 4, 31, 0, 1, 0, 1, 0, 1, 0),
        12: (5, 4, 332, 0, 7, 0, 16, 0, 15, 0),
        18: (5, 4, 1954, 0, 15, 0, 494, 0, 61, 0),
        24: (5, 5, 10415, 1, 96, 1, 5846, 0, 175, 0),
        30: (4, 5, 20001, 5, 4263, 2, 20001, 5, 1528, 0),
    }
    for m, (sat, dpll, cover, cab, clique, clab, rcover, rcab, rclique, rclab) in expected.items():
        r = rows[m]
        assert (r["sat"], r["dpll"], r["cover"], r["cover_aborted"], r["clique"], r["clique_aborted"]) == (sat, dpll, cover, cab, clique, clab), m
        assert (r["rand_cover"], r["rand_cover_aborted"], r["rand_clique"], r["rand_clique_aborted"]) == (rcover, rcab, rclique, rclab), m


def test_claim_the_reduction_keeps_the_answer_but_not_the_ease(effort):
    """README: DPLL braucht auf allen fünf Größen im Median höchstens 5 Knoten (Einzelfälle mehr), die Überdeckungssuche auf G_F bei m = 30 in 5 von 5 Fällen das ganze Budget; kein einheitliches Bild gegen Zufallsgraphen."""
    rows = effort
    assert max(r["dpll"] for r in rows) == 5
    assert rows[-1]["cover_aborted"] == 5 and rows[-1]["rand_cover_aborted"] == 5
    # Überdeckungssuche: G_F ist bei m = 12 bis 24 schwerer als der Zufallsgraph; Cliquensuche: bei m = 18 und 24 ist der Zufallsgraph schwerer, bei m = 30 G_F
    assert all(rows[i]["cover"] > rows[i]["rand_cover"] for i in (1, 2, 3))
    assert rows[2]["clique"] < rows[2]["rand_clique"] and rows[3]["clique"] < rows[3]["rand_clique"] and rows[4]["clique"] > rows[4]["rand_clique"]


def test_claim_kernel_after_the_reduction_rules(effort):
    """README, Kern-Tabelle: Anteil der Knoten nach den Reduktionsregeln, G_F gegen Zufallsgraph: m = 6: 0 / 0, 12: 58,3 / 0, 18: 100 / 79,6, 24: 100 / 91,7, 30: 100 / 97,8 (Prozent)."""
    rows = effort
    assert [round(r["kernel"], 1) for r in rows] == [0.0, 58.3, 100.0, 100.0, 100.0]
    assert [round(r["rand_kernel"], 1) for r in rows] == [0.0, 0.0, 79.6, 91.7, 97.8]


# --- Befund 4: Zertifikate -----------------------------------------------------------------------------------------------------------------------


def test_claim_bipartite_certificates():
    """README: von 400 Zufallsgraphen sind 119 bipartit (2-Färbung) und 281 haben einen ungeraden Kreis (längster: 9 Knoten); jeder Beleg wird geprüft."""
    assert ev.bipartite_counts() == {"graphs": 400, "bipartite": 119, "odd_cycle": 281, "longest_cycle": 9}


def test_claim_random_unsatisfiable_formulas_have_small_refutations():
    """README, Tabelle (m/n = 4,3, 12 feste Formeln je n, nur die unerfüllbaren zählen): n = 10 bis 40: unerfüllbar 3, 3, 3, 2, 4, 4, 2; Median 7, 15, 19, 28, 36, 52, 51 Knoten; Maximum 13, 15, 21, 31, 53, 67, 69."""
    rows = ev.refutation_random_rows()
    assert [r["n"] for r in rows] == [10, 15, 20, 25, 30, 35, 40] and [r["m"] for r in rows] == [43, 64, 86, 108, 129, 150, 172]
    assert [r["unsat"] for r in rows] == [3, 3, 3, 2, 4, 4, 2]
    assert [r["median"] for r in rows] == [7, 15, 19, 28, 36, 52, 51]
    assert [r["max"] for r in rows] == [13, 15, 21, 31, 53, 67, 69]


def test_claim_pigeonhole_refutations_grow_fast():
    """README: Schubfach-Formeln mit h = 2 bis 7 Fächern: 3, 11, 47, 239, 1.439, 10.079 Knoten; Faktor je Fach 3,7 / 4,3 / 5,1 / 6,0 / 7,0."""
    rows = ev.refutation_pigeon_rows()
    nodes = [r["nodes"] for r in rows]
    assert nodes == [3, 11, 47, 239, 1439, 10079]
    assert [round(b / a, 1) for a, b in zip(nodes, nodes[1:])] == [3.7, 4.3, 5.1, 6.0, 7.0]


def test_claim_pigeonhole_h8_precomputed():
    """README: h = 8 braucht 80.639 Knoten (in der App nicht live gerechnet, hier nachgerechnet; rund 18 Sekunden)."""
    clauses, nv = K.pigeonhole(C.PIGEON_H_PRECOMPUTED)
    r = D.dpll(clauses)
    assert not r.satisfiable and r.nodes == 80639 and nv == 72 and len(clauses) == 297


def test_claim_yes_certificates_are_cheap():
    """README: eine erfüllende Belegung der Standardformel (n = 8, m = 12) kostet 3m = 36 Literalzugriffe höchstens; eine unabhängige Menge der Größe 12 prüft 66 Paare; die Rundreise über 12 Orte 12 Zugriffe gegen 56.342 bei Held–Karp."""
    rows = ev.yes_rows(ev.analyse(ev.Settings()))
    assert rows[0]["bound"] == 36 and rows[1]["bound"] == 66 and rows[1]["verify"] == 66
    assert rows[2]["verify"] == 12 and rows[2]["search"] == 56342


# --- Presets (Einzelinstanzen) -------------------------------------------------------------------------------------------------------------------


def test_claim_presets_are_single_instances_with_these_values():
    """README, Preset-Tabelle (Einzelinstanzen, Zufalls-Seed je Preset): erfüllbar?, DPLL-Knoten, Überdeckungssuche, Cliquensuche (Knoten, Abbruch)."""
    got = {}
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**p))
        got[name] = (a.brute is not None, a.dpll.nodes, a.cover.nodes, a.cover.aborted, a.clique.nodes, a.clique.aborted)
    assert got["Standardfall (Voreinstellung)"] == (True, 6, 386, False, 1, False)
    assert got["Lehrbeispiel (3 Klauseln)"] == (True, 3, 5, False, 1, False)
    assert got["Unerfüllbar (alle Belegungen verboten)"] == (False, 7, 959, False, 83, False)
    assert got["Nahe der Schwelle (m/n = 4)"] == (False, 7, 10001, True, 10001, True)
    assert got["Größte Formel (Budget reicht nicht)"] == (True, 6, 100001, True, 44390, False)


def test_claim_unit_is_search_nodes_not_seconds():
    a = ev.analyse(ev.Settings(**C.PRESETS["Nahe der Schwelle (m/n = 4)"]))
    text = ev.verdict_chain(a)[1]
    assert "Sekunden" not in text and "Knotenbudget" in text
