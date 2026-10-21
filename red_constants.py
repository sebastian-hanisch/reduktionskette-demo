"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Annahmen, Farben und Presets.

Rechengrenze am Regler-Maximum (DEMO-PLAYBOOK §1c): n = 12, m = 30 heißt 90 Knoten im Graphen G_F, rund 1 000 Kanten und ein Komplement mit rund 3 000 Kanten.
Die beiden Graphlöser (Knotenüberdeckung auf G_F, größte Clique im Komplement) laufen mit einem Knotenbudget (BUDGETS) und brechen dort ab;
die Formel selbst entscheidet die Brute-Force-Probe in höchstens 2^12 Belegungen und das DPLL in wenigen Knoten."""

N_MIN, N_MAX, DEFAULT_N = 3, 12, 8
M_MIN, M_MAX, DEFAULT_M = 3, 30, 12
SEED_MAX, DEFAULT_SEED = 999999, 35
BUDGETS = (1_000, 10_000, 100_000)        # Knoten je Graphlöser
DEFAULT_BUDGET = 10_000

SWEEP_SEEDS = tuple(range(100000, 100005))  # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
SWEEP_N = 8                                 # Zahl der Variablen in den Messreihen über m
SWEEP_M = (6, 12, 18, 24, 30)               # Klauselzahlen der Messreihen (Formel wächst: dieselbe Zufalls-Seed, Klauseln kommen dazu)
SWEEP_BUDGET = 20_000                       # Knotenbudget der Messreihen (kleiner als der Reglerbereich, damit die Messreihe in Sekunden läuft)

# Zertifikat-Tab
CERT_RATIO = 4.3                            # Klauseln je Variable für die Zufallsformeln der Nein-Beleg-Messung
CERT_N = (10, 15, 20, 25, 30, 35, 40)
CERT_FORMULAS = 12                          # Formeln je Größe; nur die unerfüllbaren zählen
PIGEON_H = (2, 3, 4, 5, 6, 7)               # Fächer; h + 1 Tauben
PIGEON_H_PRECOMPUTED = 8                    # h = 8 braucht in Python rund 18 Sekunden und wird nicht live gerechnet (Test rechnet es nach)
BIPARTITE_GRAPHS = 400                      # Zufallsgraphen für die Beleg-Zählung (n = 6 bis 40)

BOUNDS = {"simple": "Größe + Restkandidaten", "color": "Färbungsschranke"}          # für red_clique.py (Kopie aus max-clique-demo)
ORDERS = {"index": "nach Nummer", "degree": "nach Grad (größter zuerst)", "degeneracy": "nach Degeneracy (kleinster Grad zuletzt)"}

COLOR_NODE = "#8D99A6"
COLOR_CHOSEN = "#2F6B65"
COLOR_TRIANGLE = "#34495E"
COLOR_CONFLICT = "rgba(192,57,43,0.35)"
COLOR_LINE = "#4c78a8"
COLOR_SERIES = ("#2F6B65", "#4c78a8", "#B8860B", "#C0392B")

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "m": DEFAULT_M, "seed": DEFAULT_SEED, "budget": DEFAULT_BUDGET},
    "Lehrbeispiel (3 Klauseln)": {"n": 3, "m": 3, "seed": 1, "budget": DEFAULT_BUDGET},
    "Unerfüllbar (alle Belegungen verboten)": {"n": 3, "m": 18, "seed": 3, "budget": DEFAULT_BUDGET},
    "Nahe der Schwelle (m/n = 4)": {"n": 7, "m": 28, "seed": 7, "budget": DEFAULT_BUDGET},
    "Größte Formel (Budget reicht nicht)": {"n": N_MAX, "m": M_MAX, "seed": 11, "budget": BUDGETS[-1]},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "8 Variablen, 12 Klauseln: Formel, Graph und alle Antworten ohne Abbruch.",
    "Lehrbeispiel (3 Klauseln)": "3 Variablen, 3 Klauseln: 9 Knoten, zum Nachvollziehen von Hand.",
    "Unerfüllbar (alle Belegungen verboten)": "3 Variablen, 18 Klauseln: keine Belegung erfüllt alle, also keine unabhängige Menge der Größe m.",
    "Nahe der Schwelle (m/n = 4)": "7 Variablen, 28 Klauseln (Verhältnis 4): die Graphlöser brauchen schon deutlich mehr Knoten als das DPLL auf der Formel.",
    "Größte Formel (Budget reicht nicht)": "12 Variablen, 30 Klauseln, 90 Knoten: die Überdeckungssuche bricht am Knotenbudget ab, die Cliquensuche und das DPLL kommen durch.",
}
