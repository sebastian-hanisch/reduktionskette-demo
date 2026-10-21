"""Die Reduktionskette 3-SAT -> unabhängige Menge -> Knotenüberdeckung -> Clique (reines Python), jede Regel eine eigene Funktion (DEMO-PLAYBOOK §1b).

Eine Formel F mit m Klauseln wird in einen Graphen G_F mit 3m Knoten übersetzt: je Klausel ein Dreieck (ein Knoten je Literal), dazu eine Konfliktkante zwischen Knoten
komplementärer Literale verschiedener Klauseln. Knoten 3i + j ist das Literal j der Klausel i. Dann gilt
    F erfüllbar  <=>  alpha(G_F) = m  <=>  tau(G_F) = 2m  <=>  omega(Komplement von G_F) = m
und aus einer unabhängigen Menge der Größe m lässt sich eine erfüllende Belegung zurückgewinnen."""

import itertools


# --- Formel ---------------------------------------------------------------------------------------------------------------------------------------


def literal_true(lit: int, assignment) -> bool:
    """Ist das Literal unter der Belegung (Variable -> bool) wahr?"""
    return assignment[abs(lit)] == (lit > 0)


def is_satisfying(formula, assignment) -> bool:
    """Unabhängiger Prüfer: jede Klausel hat mindestens ein wahres Literal."""
    return all(any(literal_true(lit, assignment) for lit in clause) for clause in formula)


def variables_of(formula) -> list[int]:
    return sorted({abs(lit) for clause in formula for lit in clause})


def brute_force_sat(n: int, formula):
    """Alle 2^n Belegungen durchprobieren (Orakel für n <= 12): die erste erfüllende Belegung (Variable -> bool) oder None."""
    for bits in range(1 << n):
        assignment = {v: bool(bits >> (v - 1) & 1) for v in range(1, n + 1)}
        if is_satisfying(formula, assignment):
            return assignment
    return None


# --- Graph ---------------------------------------------------------------------------------------------------------------------------------------


def node(clause_index: int, position: int) -> int:
    """Knotennummer des Literals `position` (0 bis 2) der Klausel `clause_index`."""
    return 3 * clause_index + position


def clause_triangle_edges(m: int) -> list[tuple[int, int]]:
    """Dreieckskanten: die drei Literale einer Klausel sind paarweise verbunden (höchstens eines davon darf in die unabhängige Menge)."""
    return [(node(i, a), node(i, b)) for i in range(m) for a, b in itertools.combinations(range(3), 2)]


def conflict_edges(formula) -> list[tuple[int, int]]:
    """Konfliktkanten: zwei Knoten verschiedener Klauseln, deren Literale einander widersprechen (x und nicht x)."""
    edges = []
    for i, ci in enumerate(formula):
        for k in range(i + 1, len(formula)):
            for a, la in enumerate(ci):
                for b, lb in enumerate(formula[k]):
                    if la == -lb:
                        edges.append((node(i, a), node(k, b)))
    return edges


def build_graph(formula) -> tuple[frozenset, ...]:
    """G_F als Adjazenz (Tupel von frozensets): Dreieckskanten plus Konfliktkanten."""
    adj = [set() for _ in range(3 * len(formula))]
    for a, b in clause_triangle_edges(len(formula)) + conflict_edges(formula):
        adj[a].add(b)
        adj[b].add(a)
    return tuple(frozenset(s) for s in adj)


def complement(adj) -> tuple[frozenset, ...]:
    """Komplementgraph: zwei verschiedene Knoten sind genau dann verbunden, wenn sie es im Original nicht sind."""
    n = len(adj)
    return tuple(frozenset(set(range(n)) - set(adj[v]) - {v}) for v in range(n))


def edge_count(adj) -> int:
    return sum(len(a) for a in adj) // 2


def cover_threshold(m: int) -> int:
    """Eine Überdeckung der Größe höchstens 2m gibt es genau dann, wenn F erfüllbar ist (tau = 3m - alpha, alpha = m)."""
    return 2 * m


def independent_set_from_cover(n_nodes: int, cover) -> tuple[int, ...]:
    """Gallai: das Komplement einer Knotenüberdeckung ist eine unabhängige Menge."""
    covered = set(cover)
    return tuple(v for v in range(n_nodes) if v not in covered)


def is_independent_set(adj, vertices) -> bool:
    s = set(vertices)
    return all(not (set(adj[v]) & s) for v in s)


def is_clique(adj, vertices) -> bool:
    vs = list(vertices)
    return all(b in adj[a] for a, b in itertools.combinations(vs, 2))


# --- Rückweg -------------------------------------------------------------------------------------------------------------------------------------


def decode_assignment(formula, independent_set, n: int) -> dict[int, bool]:
    """Aus einer unabhängigen Menge: je gewähltem Knoten (Klausel i, Position j) wird das Literal wahr gesetzt; nicht berührte Variablen bekommen falsch.
    Ist die Menge unabhängig, widerspricht sich keine Wahl (Konfliktkanten); hat sie m Knoten, ist jede Klausel bedient."""
    assignment: dict[int, bool] = {}
    for v in sorted(independent_set):
        i, j = divmod(v, 3)
        lit = formula[i][j]
        assignment.setdefault(abs(lit), lit > 0)
    for v in range(1, n + 1):
        assignment.setdefault(v, False)
    return assignment
