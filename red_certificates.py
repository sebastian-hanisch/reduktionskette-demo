"""Zertifikate: Ja-Belege prüfen, bipartit mit 2-Färbung oder ungeradem Kreis, Schubfach-Formeln als Beispiel ohne kurzen Nein-Beleg (reines Python).

Ein Zertifikat ist ein Beleg, den ein Prüfer in polynomialer Zeit kontrolliert. „In NP“ heißt: jede Ja-Instanz hat einen kurzen, schnell prüfbaren Beleg."""

import itertools
from collections import deque

import red_reduction as R


# --- Ja-Belege prüfen: Prüfschritte (Zählformeln) -------------------------------------------------------------------------------------------------


def accesses_verify_assignment(m: int) -> int:
    """Eine Belegung prüfen: jede der m Klauseln liest ihre drei Literale (3m Zugriffe), im ungünstigen Fall."""
    return 3 * m


def pairs_verify_set(k: int) -> int:
    """Eine Clique oder unabhängige Menge der Größe k prüfen: k(k-1)/2 Paare."""
    return k * (k - 1) // 2


def accesses_verify_tour(n: int) -> int:
    """Eine Rundreise (Stück 1) prüfen: n Matrixeinträge entlang der Reise."""
    return n


def accesses_search_tour(n: int) -> int:
    """Held–Karp (Stück 1) für dieselbe Rundreise: (n-1)(n-2) 2^(n-3) + 2(n-1) Zugriffe (n = 2: 2, n = 1: 0)."""
    if n >= 3:
        return (n - 1) * (n - 2) * 2 ** (n - 3) + 2 * (n - 1)
    return 2 if n == 2 else 0


def verify_assignment(formula, assignment) -> tuple[bool, int]:
    """Prüft die Belegung und zählt die gelesenen Literale. Prüfer mit Zählung: lehnt eine Belegung ab, die eine Klausel verletzt (liest dann weniger)."""
    reads = 0
    for clause in formula:
        ok = False
        for lit in clause:
            reads += 1
            if R.literal_true(lit, assignment):
                ok = True
                break
        if not ok:
            return False, reads
    return True, reads


def verify_independent_set(adj, vertices) -> tuple[bool, int]:
    """Prüft paarweise, dass keine Kante innerhalb der Menge liegt; zählt die geprüften Paare."""
    pairs = 0
    for a, b in itertools.combinations(sorted(vertices), 2):
        pairs += 1
        if b in adj[a]:
            return False, pairs
    return True, pairs


# --- Bipartit: beide Seiten haben einen kurzen Beleg -----------------------------------------------------------------------------------------------


def two_color_or_odd_cycle(adj) -> tuple[str, object, int]:
    """Breitensuche: entweder eine 2-Färbung ("bipartite", Farbe je Knoten) oder ein ungerader Kreis ("odd_cycle", Knotenfolge). Dritter Wert: gelesene Nachbarn."""
    n = len(adj)
    color = [-1] * n
    parent = [-1] * n
    steps = 0
    for start in range(n):
        if color[start] != -1:
            continue
        color[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for w in sorted(adj[u]):
                steps += 1
                if color[w] == -1:
                    color[w] = 1 - color[u]
                    parent[w] = u
                    queue.append(w)
                elif color[w] == color[u]:
                    up, wp = [u], [w]
                    while parent[up[-1]] != -1:
                        up.append(parent[up[-1]])
                    while parent[wp[-1]] != -1:
                        wp.append(parent[wp[-1]])
                    on_u = set(up)
                    meet = next(x for x in wp if x in on_u)
                    cycle = up[: up.index(meet) + 1] + list(reversed(wp[: wp.index(meet)]))
                    return "odd_cycle", tuple(cycle), steps
    return "bipartite", tuple(color), steps


def check_two_coloring(adj, color) -> bool:
    """Jede Kante verbindet zwei verschiedene Farben."""
    return len(color) == len(adj) and all(color[a] != color[b] for a in range(len(adj)) for b in adj[a])


def check_odd_cycle(adj, cycle) -> bool:
    """Ungerade Länge, verschiedene Knoten, jeder Schritt (auch zurück zum Start) ist eine Kante."""
    k = len(cycle)
    return k % 2 == 1 and k >= 3 and len(set(cycle)) == k and all(cycle[(i + 1) % k] in adj[cycle[i]] for i in range(k))


# --- Formeln ohne kurzen Nein-Beleg: Schubfach -------------------------------------------------------------------------------------------------------


def pigeonhole(h: int) -> tuple[list[tuple[int, ...]], int]:
    """h + 1 Tauben in h Fächer: Variable (Taube i, Fach j) = i·h + j + 1. Klauseln: jede Taube sitzt in einem Fach; kein Fach hat zwei Tauben. Unerfüllbar.
    Rückgabe (Klauseln, Zahl der Variablen). Keine 3-KNF (die ersten Klauseln haben h Literale)."""
    tauben = h + 1

    def var(i, j):
        return i * h + j + 1

    clauses = [tuple(var(i, j) for j in range(h)) for i in range(tauben)]
    for j in range(h):
        for a, b in itertools.combinations(range(tauben), 2):
            clauses.append((-var(a, j), -var(b, j)))
    return clauses, tauben * h
