# Wörtliche Kopie von vertex-cover-demo/vcv_algorithm.py (letzter Commit der Datei: 60180da, Arbeitsbaum sauber am 2026-10-21); einzige Änderung: die Importzeile der Konstanten (nur red_clique.py). Änderungen gehören ins Original, nicht hierher.
"""Knotenüberdeckung: Approximation, LP-Kern, Kernbildung und Verzweigen.

Eine Überdeckung ist eine Knotenmenge, die jede Kante berührt (hier: die Sendungen, die man auslagert, damit kein Konflikt bleibt). Jede Regel ist eine eigene
kleine Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK 1b); die großen Verfahren rufen sie nur der Reihe nach auf. Reine Python-Mengen, feste
Reihenfolgen (kleinster Index bei Gleichstand), kein Zufall: das Ergebnis ist vollständig deterministisch.

Der LP (jede Kante: x_u + x_v >= 1, minimiere die Summe) wird selbst gelöst: Jeder Knoten v wird im bipartiten Doppelgraphen zu v_L und v_R, jede Kante {u, v}
zu {u_L, v_R} und {v_L, u_R}; ein größtes Matching und die Überdeckung nach König liefern eine optimale halbganzzahlige Lösung x_v = (a_v + b_v) / 2.
Werte werden verdoppelt gespeichert (x2 in {0, 1, 2}), damit alles ganzzahlig und exakt bleibt."""

from dataclasses import dataclass, field


class BudgetExceeded(Exception):
    """Das Knotenbudget ist aufgebraucht; der Lauf bricht ab."""


# --- Hilfen ------------------------------------------------------------------------------------------------------------------------------------

def edge_list(adj):
    """Alle Kanten (u, v) mit u < v, aufsteigend."""
    return [(u, v) for u in range(len(adj)) for v in sorted(adj[u]) if u < v]


def is_cover(adj, cover):
    """Jede Kante hat mindestens ein Ende in `cover`."""
    c = set(cover)
    return all(u in c or v in c for u, v in edge_list(adj))


def bipartition(adj):
    """Zweifärbung per Breitensuche (Gleichstand: kleinster Index); (Seite je Knoten, True) oder (None, False), wenn der Graph nicht bipartit ist."""
    side = [None] * len(adj)
    for s in range(len(adj)):
        if side[s] is not None:
            continue
        side[s] = 0
        queue = [s]
        while queue:
            u = queue.pop(0)
            for w in sorted(adj[u]):
                if side[w] is None:
                    side[w] = 1 - side[u]
                    queue.append(w)
                elif side[w] == side[u]:
                    return None, False
    return side, True


# --- Approximation ----------------------------------------------------------------------------------------------------------------------------

def maximal_matching(adj):
    """Maximales Matching: die Kanten in fester Reihenfolge, eine Kante wird genommen, wenn beide Enden noch frei sind."""
    used, matching = set(), []
    for u, v in edge_list(adj):
        if u not in used and v not in used:
            used |= {u, v}
            matching.append((u, v))
    return matching


def matching_cover(adj):
    """Matching-Verfahren: alle Endpunkte eines maximalen Matchings. Es gilt |M| <= tau <= 2 |M|. Gibt (Überdeckung sortiert, Matching) zurück."""
    m = maximal_matching(adj)
    return tuple(sorted({x for e in m for x in e})), m


def greedy_degree_cover(adj):
    """Greedy: immer den Knoten mit dem größten Restgrad (Gleichstand: kleinster Index) in die Überdeckung. Gibt die Knoten in der Reihenfolge der Wahl zurück."""
    rest = [set(a) for a in adj]
    cover = []
    while True:
        v = max(range(len(rest)), key=lambda x: (len(rest[x]), -x)) if rest else None
        if v is None or not rest[v]:
            return cover
        for w in rest[v]:
            rest[w].discard(v)
        rest[v] = set()
        cover.append(v)


# --- LP und Kern ------------------------------------------------------------------------------------------------------------------------------

def _max_matching(nbrs, left):
    """Größtes Matching im bipartiten Doppelgraphen auf der Knotenmenge `left` (v_L verbunden mit w_R für jeden Nachbarn w von v innerhalb der Menge).
    Greedy-Start, dann Erweiterungswege (iterative Tiefensuche, Nachbarn aufsteigend). Gibt (match_l, match_r) zurück: v_L -> w_R bzw. w_R -> v_L."""
    match_l, match_r = {}, {}
    for v in sorted(left):
        for w in sorted(nbrs[v]):
            if w not in match_r:
                match_l[v], match_r[w] = w, v
                break
    for v in sorted(left):
        if v not in match_l:
            _augment(nbrs, v, match_l, match_r)
    return match_l, match_r


def _augment(nbrs, root, match_l, match_r):
    """Sucht von dem freien v_L = root einen Erweiterungsweg; True und das Matching ist um eins größer, sonst False und es bleibt unverändert."""
    parent = {}                                   # w_R -> v_L, von dem aus w erreicht wurde
    stack = [root]
    seen_l = {root}
    while stack:
        u = stack.pop()
        for w in sorted(nbrs[u], reverse=True):
            if w in parent:
                continue
            parent[w] = u
            if w not in match_r:                 # freier Endpunkt: Weg zurückverfolgen und umkehren
                cur = w
                while True:
                    u2 = parent[cur]
                    prev = match_l.get(u2)
                    match_l[u2], match_r[cur] = cur, u2
                    if u2 == root:
                        return True
                    cur = prev
            nxt = match_r[w]
            if nxt not in seen_l:
                seen_l.add(nxt)
                stack.append(nxt)
    return False


def _koenig(nbrs, left, match_l, match_r):
    """Überdeckung nach König: Z = alle Knoten, die von freien v_L aus über abwechselnd Nicht-Matching- und Matching-Kanten erreichbar sind;
    Überdeckung = (L ohne Z) vereinigt (R in Z). Gibt (a, b) zurück: a_v = 1, wenn v_L in der Überdeckung, b_v = 1, wenn v_R."""
    z_l = {v for v in left if v not in match_l}
    z_r = set()
    stack = sorted(z_l)
    while stack:
        u = stack.pop()
        for w in nbrs[u]:
            if w in z_r or match_l.get(u) == w:
                continue
            z_r.add(w)
            nxt = match_r.get(w)
            if nxt is not None and nxt not in z_l:
                z_l.add(nxt)
                stack.append(nxt)
    a = {v: 0 if v in z_l else 1 for v in left}
    b = {v: 1 if v in z_r else 0 for v in left}
    return a, b


def lp_solution(adj, vertices=None):
    """Optimale halbganzzahlige LP-Lösung auf dem von `vertices` induzierten Teilgraphen (Standard: alle). Gibt ({v: x2}, lp2) zurück:
    x2 = 2 x in {0, 1, 2}, lp2 = 2 * LP-Wert = Größe des größten Matchings im Doppelgraphen."""
    left = set(range(len(adj))) if vertices is None else set(vertices)
    nbrs = {v: adj[v] & left for v in left}
    match_l, match_r = _max_matching(nbrs, left)
    a, b = _koenig(nbrs, left, match_l, match_r)
    x2 = {v: a[v] + b[v] for v in left}
    return x2, len(match_l)


def nt_split(x2):
    """Nemhauser–Trotter: Zerlegung in V1 (x = 1, in die Überdeckung), V0 (x = 0, nicht in die Überdeckung) und den Kern V½."""
    return (sorted(v for v, x in x2.items() if x == 2), sorted(v for v, x in x2.items() if x == 0), sorted(v for v, x in x2.items() if x == 1))


def lp_kernel(adj):
    """LP-Kern mit Sondierung. Gibt (forced, excluded, kernel) zurück: `forced` gehören in die Überdeckung, `excluded` nicht, `kernel` bleibt offen.
    Es gilt tau(G) = |forced| + tau(G[kernel]), und jede Kante zwischen `excluded` und dem Rest endet in `forced`.

    1. Optimale halbganzzahlige Lösung auf dem Rest: x = 1 -> forced, x = 0 -> excluded (Nemhauser–Trotter), x = ½ -> Kern.
    2. Im Kern ist x = ½ überall optimal. Sondiere jede Sendung v in aufsteigender Reihenfolge: Lässt sich der LP-Wert halten, wenn v auf 1 (bzw. v auf 0 und
       alle Nachbarn auf 1) gesetzt wird, ist das wieder eine optimale halbganzzahlige Lösung, also gilt dasselbe Persistenzargument für v. Dann weiter bei 1."""
    forced, excluded = set(), set()
    kernel = set(range(len(adj)))
    while kernel:
        x2, _ = lp_solution(adj, kernel)
        v1, v0, half = nt_split(x2)
        forced |= set(v1)
        excluded |= set(v0)
        kernel = set(half)
        if not kernel:
            break
        progressed = False
        size = len(kernel)
        assert _nu(adj, kernel) == size            # im Kern ist x = ½ optimal, also hat der Doppelgraph ein perfektes Matching
        for v in sorted(kernel):
            rest1 = kernel - {v}
            if _nu(adj, rest1) + 2 == size:                       # v auf 1: der LP-Wert bleibt erhalten
                forced.add(v)
                kernel = rest1
                progressed = True
                break
            nb = adj[v] & kernel
            rest0 = kernel - nb - {v}
            if nb and _nu(adj, rest0) + 2 * len(nb) == size:      # v auf 0, alle Nachbarn auf 1: der LP-Wert bleibt erhalten
                excluded.add(v)
                forced |= nb
                kernel = rest0
                progressed = True
                break
        if not progressed:
            break
    return sorted(forced), sorted(excluded), sorted(kernel)


def _nu(adj, left):
    """Größe des größten Matchings im Doppelgraphen des induzierten Teilgraphen (= 2 * LP-Wert)."""
    nbrs = {v: adj[v] & left for v in left}
    ml, _ = _max_matching(nbrs, left)
    return len(ml)


def lp_value2(adj):
    """2 * LP-Wert des ganzen Graphen."""
    return _nu(adj, set(range(len(adj))))


def lp_round_cover(adj):
    """LP-Rundung der Lösung aus `lp_kernel`: x = 1 -> in die Überdeckung, x = ½ -> aufrunden, also forced + Kern. Gibt (Überdeckung sortiert, forced, excluded, Kern) zurück."""
    forced, excluded, kernel = lp_kernel(adj)
    return tuple(sorted(set(forced) | set(kernel))), forced, excluded, kernel


# --- Kernbildung ------------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class BussResult:
    forced: tuple         # Knoten, die wegen Grad > k in die Überdeckung müssen
    k_rest: int           # verbleibender Parameter
    edges: int            # Kanten im Kern
    vertices: int         # Knoten mit mindestens einer Kante im Kern
    verdict: object       # False: sicher Nein; None: offen (der Kern muss gelöst werden)


def buss_kernel(adj, k):
    """Buss: Ein Knoten mit mehr als k_rest Nachbarn muss in jede Überdeckung der Größe <= k (sonst müssten alle seine Nachbarn hinein). Wiederholen; danach hat ein Ja-Kern
    höchstens k_rest^2 Kanten (jeder der k_rest Knoten deckt höchstens k_rest Kanten). Mehr Kanten: sicher Nein."""
    rest = [set(a) for a in adj]
    forced = []
    changed = True
    while changed:
        changed = False
        for v in range(len(rest)):
            if rest[v] and len(rest[v]) > k - len(forced):
                for w in rest[v]:
                    rest[w].discard(v)
                rest[v] = set()
                forced.append(v)
                changed = True
    k_rest = k - len(forced)
    edges = sum(len(a) for a in rest) // 2
    vertices = sum(1 for a in rest if a)
    verdict = False if (k_rest < 0 or edges > k_rest * k_rest) else None
    return BussResult(tuple(forced), k_rest, edges, vertices, verdict), rest


def reduce_degree_one(rest):
    """Grad-1-Regel auf der Restadjazenz `rest` (Liste von Mengen, wird verändert): Hat v genau einen Nachbarn u, gibt es eine optimale Überdeckung mit u.
    Gibt die so genommenen Knoten zurück."""
    taken = []
    changed = True
    while changed:
        changed = False
        for v in range(len(rest)):
            if len(rest[v]) == 1:
                u = next(iter(rest[v]))
                for w in rest[u]:
                    rest[w].discard(u)
                rest[u] = set()
                taken.append(u)
                changed = True
    return taken


def cover_paths_and_cycles(rest):
    """Exakte Überdeckung, wenn der Restgraph Maximalgrad <= 2 hat (Pfade und Kreise): Pfad mit m Knoten braucht m // 2 (jeder zweite Knoten ab dem zweiten),
    Kreis (m + 1) // 2 (jeder zweite Knoten ab dem ersten)."""
    seen, cover = set(), []
    for s in range(len(rest)):
        if s in seen or not rest[s]:
            continue
        members, stack = set(), [s]
        while stack:
            u = stack.pop()
            if u in members:
                continue
            members.add(u)
            stack.extend(sorted(rest[u]))
        seen |= members
        is_cycle = all(len(rest[u]) == 2 for u in members)
        start = min(members) if is_cycle else min(u for u in members if len(rest[u]) == 1)
        order, prev, cur = [], None, start
        while True:
            order.append(cur)
            nxt = [w for w in sorted(rest[cur]) if w != prev]
            if not nxt or nxt[0] == start:
                break
            prev, cur = cur, nxt[0]
        cover.extend(order[0::2] if is_cycle else order[1::2])
    return cover


# --- Verzweigen -------------------------------------------------------------------------------------------------------------------------------

@dataclass
class Decision:
    rule: str
    k: int
    answer: object        # True / False; None bei Abbruch
    cover: tuple          # eine Überdeckung der Größe <= k bei Ja, sonst ()
    nodes: int
    aborted: bool
    kernel: object = None # BussResult bei Regel "buss"


def decide(adj, k, rule, budget=None):
    """Entscheidung „gibt es eine Überdeckung der Größe <= k?“ mit der gewählten Regel:
    "edge": Kante (u, v) wählen, u oder v nehmen (2^k Knoten);
    "degree": Knoten höchsten Grades v: v nehmen oder alle Nachbarn von v nehmen; bei Maximalgrad <= 2 exakt in Polynomialzeit;
    "degree_reduce": wie "degree", dazu in jedem Knoten die Grad-1-Regel;
    "buss": zuerst der Buss-Kern, dann "degree_reduce" auf dem Rest."""
    if rule not in ("edge", "degree", "degree_reduce", "buss"):
        raise ValueError(f"unbekannte Regel: {rule}")
    nodes = [0]
    rest = [set(a) for a in adj]
    kernel = None
    taken_prefix = []
    k_left = k
    if rule == "buss":
        kernel, rest = buss_kernel(adj, k)
        taken_prefix = list(kernel.forced)
        k_left = kernel.k_rest
        if kernel.verdict is False:
            return Decision(rule, k, False, (), 0, False, kernel)
    inner = "degree_reduce" if rule == "buss" else rule
    chosen = []

    def take(v):
        removed = list(rest[v])
        for w in removed:
            rest[w].discard(v)
        rest[v] = set()
        return removed

    def put_back(v, removed):
        rest[v] = set(removed)
        for w in removed:
            rest[w].add(v)

    def rec(kk):
        nodes[0] += 1
        if budget is not None and nodes[0] > budget:
            raise BudgetExceeded
        undo = []
        used = 0
        if inner == "degree_reduce":
            changed = True
            while changed:
                changed = False
                for v in range(len(rest)):
                    if len(rest[v]) == 1:
                        u = next(iter(rest[v]))
                        undo.append((u, take(u)))
                        chosen.append(u)
                        used += 1
                        changed = True
        left = kk - used

        def restore():
            for u, removed in reversed(undo):
                put_back(u, removed)
            for _ in undo:
                chosen.pop()

        if left < 0:
            restore()
            return False
        if inner == "edge":
            edge = next(((u, min(rest[u])) for u in range(len(rest)) if rest[u]), None)
            if edge is None:
                return True
            if left == 0:
                restore()
                return False
            for take_v in edge:
                removed = take(take_v)
                chosen.append(take_v)
                if rec(left - 1):
                    return True
                chosen.pop()
                put_back(take_v, removed)
            restore()
            return False
        v = max(range(len(rest)), key=lambda x: (len(rest[x]), -x)) if rest else None
        d = len(rest[v]) if v is not None else 0
        if d == 0:
            return True
        if d <= 2:
            extra = cover_paths_and_cycles(rest)
            if len(extra) <= left:
                chosen.extend(extra)
                return True
            restore()
            return False
        if left == 0:
            restore()
            return False
        removed = take(v)
        chosen.append(v)
        if rec(left - 1):
            return True
        chosen.pop()
        put_back(v, removed)
        if left >= d:
            neighbours = sorted(rest[v])
            logs = []
            for w in neighbours:
                logs.append((w, take(w)))
                chosen.append(w)
            if rec(left - d):
                return True
            for w, rem in reversed(logs):
                put_back(w, rem)
                chosen.pop()
        restore()
        return False

    try:
        ok = rec(k_left)
    except BudgetExceeded:
        return Decision(rule, k, None, (), nodes[0], True, kernel)
    cover = tuple(sorted(set(taken_prefix) | set(chosen))) if ok else ()
    return Decision(rule, k, bool(ok), cover, nodes[0], False, kernel)


@dataclass
class ExactResult:
    tau: object           # kleinste Überdeckungsgröße, None bei Abbruch
    cover: tuple          # eine kleinste Überdeckung (bei Abbruch die beste bekannte)
    nodes: int            # Knoten aller Verzweigungsläufe zusammen
    aborted: bool
    lower: int            # untere Schranke: ceil(LP-Wert) und |Matching|
    forced: tuple = ()
    kernel: tuple = ()
    history: list = field(default_factory=list)   # [(k, Antwort, Knoten)] je getestetem k


def exact_cover(adj, budget=None):
    """Kleinste Überdeckung: LP-Kern (V1 hinein, V0 heraus, nur der Kern bleibt), dann iterative Vertiefung über k ab der LP-Untergrenze mit „Grad + Grad-1-Regel“.
    Bei Abbruch (Knotenbudget) gelten die untere Schranke und die beste bekannte Überdeckung (Greedy)."""
    n = len(adj)
    forced, excluded, kernel = lp_kernel(adj)
    matching = maximal_matching(adj)
    kernel_set = set(kernel)
    sub = [set(adj[v]) & kernel_set if v in kernel_set else set() for v in range(n)]
    sub_adj = tuple(frozenset(a) for a in sub)
    lower_kernel = (_nu(adj, kernel_set) + 1) // 2 if kernel_set else 0
    lower = len(forced) + lower_kernel
    lower = max(lower, len(matching))
    history = []
    total = 0
    if not kernel:
        cover = tuple(sorted(forced))
        return ExactResult(len(cover), cover, 0, False, lower, tuple(forced), (), history)
    k = lower_kernel
    best_greedy = greedy_degree_cover(sub_adj)
    while True:
        left = None if budget is None else budget - total
        d = decide(sub_adj, k, "degree_reduce", left)
        total += d.nodes
        history.append((k, d.answer, d.nodes))
        if d.aborted:
            cover = tuple(sorted(set(forced) | set(best_greedy)))
            return ExactResult(None, cover, total, True, lower, tuple(forced), tuple(kernel), history)
        if d.answer:
            cover = tuple(sorted(set(forced) | set(d.cover)))
            return ExactResult(len(cover), cover, total, False, lower, tuple(forced), tuple(kernel), history)
        k += 1


def bipartite_matching_size(adj):
    """Größe des größten Matchings eines bipartiten Graphen (Kuhn: Erweiterungswege von jedem Knoten der Seite 0); None, wenn der Graph nicht bipartit ist.
    Nach König ist das die kleinste Überdeckung."""
    side, ok = bipartition(adj)
    if not ok:
        return None
    left = [v for v in range(len(adj)) if side[v] == 0]
    nbrs = {v: adj[v] for v in left}
    match_l, match_r = {}, {}
    for v in left:
        _augment(nbrs, v, match_l, match_r)
    return len(match_l)
