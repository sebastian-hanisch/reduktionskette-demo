"""Abbildungen: Positionen, Kanten, Farben; alle Achsen gesperrt; PDF baut mit Umlauten und bei Abbruch."""

import math

import red_constants as C
import red_evaluation as ev
import red_reduction as R
import red_visualization as V
from red_pdf_export import build_pdf
from red_scenario import random_formula


def test_node_positions_cluster_per_clause_and_stay_inside_the_frame():
    for m in (1, 3, 12, 30):
        pos = V.node_positions(m)
        assert len(pos) == 3 * m
        assert all(abs(x) < 1.3 and abs(y) < 1.3 for x, y in pos)
        for i in range(m):                                           # Dreiecke sind klein gegen den Abstand zweier Klauseln
            cx = sum(pos[3 * i + j][0] for j in range(3)) / 3
            cy = sum(pos[3 * i + j][1] for j in range(3)) / 3
            assert all(math.hypot(pos[3 * i + j][0] - cx, pos[3 * i + j][1] - cy) <= 0.12 for j in range(3))
    first = V.node_positions(4)
    assert first[0][1] > first[3][1] - 2 and abs(sum(p[0] for p in first[0:3]) / 3) < 1e-9            # Klausel 1 liegt oben (x ≈ 0)


def test_graph_figure_has_all_edges_nodes_and_marks_the_witness(mini):
    adj = R.build_graph(mini)
    fig = V.build_graph(mini, adj, (0, 5, 6))
    conflict, triangle, nodes = fig.data
    assert conflict.x.count(None) == 6 and triangle.x.count(None) == 9                         # 6 Konfliktkanten, 9 Dreieckskanten
    assert list(nodes.text) == ["x1", "x2", "x3", "¬x1", "¬x2", "x3", "x1", "¬x2", "¬x3"]
    assert [c for c in nodes.marker.color].count(C.COLOR_CHOSEN) == 3 and nodes.marker.color[0] == C.COLOR_CHOSEN
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_graph_figure_without_witness_marks_nothing(mini):
    fig = V.build_graph(mini, R.build_graph(mini))
    assert C.COLOR_CHOSEN not in fig.data[2].marker.color


def test_charts_lock_their_axes_and_have_the_expected_series():
    size = ev.sweep_size(ms=(6, 12), seeds=C.SWEEP_SEEDS[:2])
    effort = ev.sweep_effort(ms=(6,), n=6, seeds=(1, 2), budget=2000)
    rand = ev.refutation_random_rows(sizes=(10, 15), formulas=4)
    pigeon = ev.refutation_pigeon_rows(hs=(2, 3))
    figs = (V.build_size(size), V.build_effort(effort, 2000), V.build_random_refutation(rand), V.build_pigeon(pigeon))
    for fig in figs:
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    assert len(figs[0].data) == 3 and len(figs[1].data) == 5 and figs[1].layout.yaxis.type == "log" and figs[3].layout.yaxis.type == "log"
    assert len(figs[2].data) == 2


def test_random_refutation_chart_skips_sizes_without_unsat_formulas():
    rows = [{"n": 10, "median": 7.0, "max": 9}, {"n": 15, "median": None, "max": None}]
    assert list(V.build_random_refutation(rows).data[0].x) == [10]


def test_pdf_builds_for_satisfiable_unsatisfiable_and_aborted_runs():
    sat = build_pdf(ev.analyse(ev.Settings()))
    assert sat[:5] == b"%PDF-" and len(sat) > 1000
    assert build_pdf(ev.analyse(ev.Settings(**C.PRESETS["Unerfüllbar (alle Belegungen verboten)"])))[:5] == b"%PDF-"
    assert build_pdf(ev.analyse(ev.Settings(**C.PRESETS["Größte Formel (Budget reicht nicht)"])))[:5] == b"%PDF-"
    assert build_pdf(ev.analyse_formula(ev.Settings(n=3, m=1), random_formula(3, 1, 1)))[:5] == b"%PDF-"
