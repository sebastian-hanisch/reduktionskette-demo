"""Gemeinsame Fixtures: Mini-Formeln, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """F = (x1 ∨ x2 ∨ x3) ∧ (¬x1 ∨ ¬x2 ∨ x3) ∧ (x1 ∨ ¬x2 ∨ ¬x3), n = 3, m = 3.

    Handrechnung: Knoten 0, 1, 2 = Klausel 1 (x1, x2, x3); 3, 4, 5 = Klausel 2 (¬x1, ¬x2, x3); 6, 7, 8 = Klausel 3 (x1, ¬x2, ¬x3).
    Dreieckskanten: 3 je Klausel, also 9. Konfliktkanten: x1 (Knoten 0, 6) gegen ¬x1 (3): 0-3 und 3-6; x2 (1) gegen ¬x2 (4, 7): 1-4 und 1-7; x3 (2, 5) gegen ¬x3 (8): 2-8 und 5-8;
    also 6. Zusammen 15 Kanten, das Komplement hat 36 - 15 = 21. Erfüllbar, z. B. x1 = x3 = wahr, x2 = falsch; unabhängige Menge {0, 5, 6} (x1 in Klausel 1, x3 in Klausel 2,
    x1 in Klausel 3): alpha = 3 = m, tau = 9 - 3 = 6 = 2m."""
    return [(1, 2, 3), (-1, -2, 3), (1, -2, -3)]


@pytest.fixture
def unsat8():
    """Alle acht Vorzeichenmuster über drei Variablen: jede Belegung verletzt genau eine Klausel, also unerfüllbar, aber sieben Klauseln lassen sich zugleich erfüllen.

    Handrechnung: 8 Klauseln, 24 Knoten, 24 Dreieckskanten. Konfliktkanten: jede Variable kommt in vier Klauseln positiv und in vier negativ vor, also 16 Paare je Variable, 48 zusammen;
    kein Paar liegt in einer Klausel (jede enthält die Variable nur einmal). 72 Kanten, Komplement 276 - 72 = 204. alpha = 7 (m - 1), tau = 24 - 7 = 17 > 2m = 16."""
    return [tuple(s * v for s, v in zip(signs, (1, 2, 3))) for signs in itertools.product((1, -1), repeat=3)]
