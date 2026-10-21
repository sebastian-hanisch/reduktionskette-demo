"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import dataclasses

import red_constants as C
import red_evaluation as ev


def _chain(mini, unsat8):
    return (ev.analyse_formula(ev.Settings(n=3, m=3), mini), ev.analyse_formula(ev.Settings(n=3, m=8), unsat8))


def test_chain_verdict_success_names_m_and_the_roundtrip(mini, unsat8):
    sat, _ = _chain(mini, unsat8)
    kind, text = ev.verdict_chain(sat)
    assert kind == "success" and "Alle vier Stufen antworten **Ja**" in text
    assert "die 3 Regeln" in text and "Größe 3" in text and "erfüllt alle Klauseln" in text


def test_chain_verdict_success_without_a_decoded_assignment(mini, unsat8):
    sat, _ = _chain(mini, unsat8)
    text = ev.verdict_chain(dataclasses.replace(sat, decoded_ok=None))[1]
    assert "Belegung" not in text.split("Größe 3.")[-1]
    assert "NICHT" in ev.verdict_chain(dataclasses.replace(sat, decoded_ok=False))[1]


def test_chain_verdict_unsat_names_alpha_tau_and_the_missing_clauses(mini, unsat8):
    _, unsat = _chain(mini, unsat8)
    kind, text = ev.verdict_chain(unsat)
    assert kind == "info" and "**Nein**" in text
    assert "hat 7 statt 8 Knoten" in text and "τ = 17 > 16" in text and "mindestens 1 Klauseln" in text


def test_chain_verdict_unknown_is_a_warning_and_names_the_stages(mini, unsat8):
    sat, _ = _chain(mini, unsat8)
    stages = (sat.stages[0], dataclasses.replace(sat.stages[1], answer=None), dataclasses.replace(sat.stages[2], answer=None), sat.stages[3])
    a = dataclasses.replace(sat, stages=stages, settings=ev.Settings(n=3, m=3, budget=1_000))
    kind, text = ev.verdict_chain(a)
    assert kind == "warning" and "Knotenbudget von 1.000 reicht nicht" in text and "Unabhängige Menge, Knotenüberdeckung" in text and "erfüllbar" in text and "DPLL: 3 Knoten" in text


def test_size_verdict_names_first_and_last_row():
    rows = [{"m": 6, "nodes": 18, "edges": 27, "conflicts": 9}, {"m": 30, "nodes": 90, "edges": 346, "conflicts": 256}]
    kind, text = ev.verdict_size(rows)
    assert kind == "info" and "m = 6 Klauseln hat G_F 18 Knoten und im Median 27 Kanten" in text and "m = 30 sind es 90 Knoten und 346 Kanten (davon 256 Konfliktkanten)" in text


def _effort(m, ratio, dpll, cover, ca, clique, cla, rc, rca, rcl, rcla):
    return {"m": m, "ratio": ratio, "count": 5, "dpll": dpll, "cover": cover, "cover_aborted": ca, "clique": clique, "clique_aborted": cla,
            "rand_cover": rc, "rand_cover_aborted": rca, "rand_clique": rcl, "rand_clique_aborted": rcla}


def test_effort_verdict_uses_the_last_row_and_counts_aborts():
    rows = [_effort(6, 0.8, 4, 31, 0, 1, 0, 1, 0, 1, 0), _effort(30, 3.75, 5, 20001, 5, 4263, 2, 20001, 5, 1528, 0)]
    kind, text = ev.verdict_effort(rows)
    assert kind == "info"
    assert "m = 30 Klauseln (m/n = 3,8)" in text and "im Median 5 Knoten" in text
    assert "Überdeckungssuche auf G_F 20.001 (Abbrüche: 5 von 5)" in text and "Cliquensuche im Komplement 4.263 (Abbrüche: 2 von 5)" in text
    assert "Zufallsgraphen gleicher Größe sind es 20.001 bzw. 1.528 Knoten (Abbrüche: 5 bzw. 0 von 5)" in text and "als untere Schranke" in text


def test_kernel_verdict_names_both_ends():
    rows = [{"m": 6, "kernel": 0.0, "rand_kernel": 0.0}, {"m": 30, "kernel": 100.0, "rand_kernel": 97.8}]
    kind, text = ev.verdict_kernel(rows)
    assert kind == "info" and "bei m = 6 im Median 0,0 %" in text and "bei m = 30 sind es 100,0 %" in text and "97,8 %" in text


def test_yes_verdict_with_and_without_an_easy_search():
    hard = [{"problem": "Rundreise", "verify": 12, "verify_unit": "Zugriffe", "search": 56342, "search_unit": "Zugriffe (Held–Karp)"}]
    kind, text = ev.verdict_yes(hard)
    assert kind == "info" and "12 Zugriffe zum Prüfen, 56.342 Zugriffe (Held–Karp) zum Finden" in text and "sogar billiger" not in text
    easy = hard + [{"problem": "3-SAT: Belegung", "verify": 16, "verify_unit": "gelesene Literale", "search": 6, "search_unit": "DPLL-Knoten"}]
    text = ev.verdict_yes(easy)[1]
    assert "Bei dieser Zufallsformel ist das Finden (3-SAT: Belegung) dagegen sogar billiger als das Prüfen" in text
    equal = [{"problem": "x", "verify": 5, "verify_unit": "u", "search": 5, "search_unit": "u"}]
    assert "sogar billiger" not in ev.verdict_yes(equal)[1]


def test_bipartite_verdict_names_counts():
    kind, text = ev.verdict_bipartite({"graphs": 400, "bipartite": 157, "odd_cycle": 243, "longest_cycle": 11})
    assert kind == "info" and "Von 400 Zufallsgraphen sind 157 bipartit" in text and "und 243 nicht" in text and "längste hat 11 Knoten" in text


def test_refutation_verdict_uses_the_largest_size_with_unsat_formulas():
    random_rows = [{"n": 10, "median": 7.0, "max": 13}, {"n": 40, "median": 57.0, "max": 65}, {"n": 45, "median": None, "max": None}]
    pigeon = [{"h": 2, "nodes": 3}, {"h": 7, "nodes": 10079}]
    kind, text = ev.verdict_refutation(random_rows, pigeon)
    assert kind == "info" and f"(m/n = {ev.fmt_num(C.CERT_RATIO)})" in text
    assert "bis n = 40" in text and "Median 57 Knoten" in text and "3 Knoten bei 2 Fächern, 10.079 bei 7" in text and "NP = coNP" in text
