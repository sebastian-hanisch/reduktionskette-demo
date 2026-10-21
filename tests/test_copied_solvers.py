"""Die kopierten Löser der Härte-Reihe (DEMO-PLAYBOOK, Entscheidung 2026-10-21: wörtlich kopieren, Quelle im Kopf der Datei).

Zwei Schutzschichten: (1) die Kopie ist bis auf die Kopfzeile und die Importzeile wortgleich mit dem Original, solange das Original im Portfolio-Ordner liegt (sonst übersprungen);
(2) die Kopie besteht ihre eigenen Gegenproben gegen Aufzählen auf kleinen Zufallsgraphen (die Tests der Ursprungs-Demos in verkleinerter Fassung)."""

import itertools
from pathlib import Path

import pytest

import red_clique as Q
import red_cover as V
import red_mis_reduce as M
from red_scenario import random_graph

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "red_clique.py": ("max-clique-demo", "mxc_algorithm.py"),
    "red_cover.py": ("vertex-cover-demo", "vcv_algorithm.py"),
    "red_mis_reduce.py": ("mis-local-search-demo", "mls_reductions.py"),
}


@pytest.mark.parametrize("copy", list(SOURCES))
def test_copy_is_verbatim_apart_from_the_header_and_the_constants_import(copy):
    folder, original = SOURCES[copy]
    source = ROOT.parent / folder / original
    if not source.exists():
        pytest.skip("Original liegt nicht im Portfolio-Ordner")
    mine = (ROOT / copy).read_text(encoding="utf-8").splitlines()
    theirs = source.read_text(encoding="utf-8").splitlines()
    assert mine[0].startswith(f"# Wörtliche Kopie von {folder}/{original}")
    body = [line.replace("import red_constants as C", "import mxc_constants as C") for line in mine[1:]]
    assert body == theirs, "die Kopie weicht vom Original ab: Änderungen gehören ins Original, danach neu kopieren"


def _graph(seed, n=None):
    n = n or 5 + seed % 7
    edges = (seed * 3) % (n * (n - 1) // 2 + 1)
    return random_graph(n, edges, 70 + seed)


def test_largest_clique_matches_enumeration():
    for seed in range(60):
        g = _graph(seed)
        w = [1 + (v * 3 + seed) % 4 for v in range(len(g))]
        for bound in ("simple", "color"):
            r = Q.largest_clique(g, w, bound=bound, order="degree", prune=bool(seed % 2))
            best, _ = Q.brute_force_max_clique(g, w)
            assert r.value == best and Q.is_clique(g, r.clique) and Q.clique_value(w, r.clique) == r.value, (seed, bound)


def test_exact_cover_matches_enumeration():
    for seed in range(60):
        g = _graph(seed, 4 + seed % 7)
        n = len(g)
        smallest = next(k for k in range(n + 1) if any(V.is_cover(g, c) for c in itertools.combinations(range(n), k)))
        r = V.exact_cover(g)
        assert r.tau == smallest and V.is_cover(g, r.cover) and len(r.cover) == smallest, seed


def test_reduction_rules_lift_to_an_optimal_independent_set():
    for seed in range(60):
        g = _graph(seed, 4 + seed % 8)
        n = len(g)
        red = M.reduce_graph(g)
        best = max(k for k in range(n + 1) if any(M.is_independent(g, c) for c in itertools.combinations(range(n), k)))
        kernel_best = max((k for k in range(len(red.kernel) + 1) if any(M.is_independent(red.kernel, c) for c in itertools.combinations(range(len(red.kernel)), k))), default=0)
        assert red.offset + kernel_best == best, seed
        lifted = M.lift(red, next(c for k in range(len(red.kernel), -1, -1) for c in itertools.combinations(range(len(red.kernel)), k) if k == kernel_best and M.is_independent(red.kernel, c)))
        assert M.is_independent(g, lifted) and len(lifted) == best, seed
