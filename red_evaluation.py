"""Kennzahlen, Messreihen und Verdikte (alle Verdikte sind reine Funktionen (Art, Text), DEMO-PLAYBOOK §12)."""

from dataclasses import dataclass
from statistics import median

import red_certificates as K
import red_clique as Q
import red_constants as C
import red_cover as V
import red_dpll as D
import red_mis_reduce as M
import red_reduction as R
from red_scenario import random_formula, random_graph, sparse_random_graph


@dataclass(frozen=True, kw_only=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    seed: int = C.DEFAULT_SEED
    budget: int = C.DEFAULT_BUDGET


@dataclass(frozen=True)
class Stage:
    name: str
    question: str
    answer: bool | None        # True = Ja, False = Nein, None = unbekannt (Budget)
    detail: str


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    formula: tuple
    graph: tuple               # Adjazenz von G_F
    triangle_edges: int
    conflict_edges: int
    brute: dict | None         # erfüllende Belegung (Orakel, Brute Force) oder None
    dpll: D.DpllResult
    cover: V.ExactResult       # kleinste Überdeckung von G_F (Löser aus vertex-cover-demo)
    clique: Q.Result           # größte Clique im Komplement von G_F (Löser aus max-clique-demo)
    kernel: M.Reduction        # Reduktionsregeln aus mis-local-search-demo auf G_F
    stages: tuple              # vier Stufen der Kette
    witness: tuple             # unabhängige Menge der Größe m (Knoten), sonst ()
    decoded: dict | None       # zurückübersetzte Belegung, sonst None
    decoded_ok: bool | None    # erfüllt die zurückübersetzte Belegung F?


# --- Zahlen im deutschen Format ------------------------------------------------------------------------------------------------------------------


def fmt_int(n: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (1.720.350)."""
    return f"{n:,}".replace(",", ".")


def fmt_num(x: float, digits: int = 1) -> str:
    """Dezimalzahl mit Komma (22,7)."""
    return f"{x:.{digits}f}".replace(".", ",")


def answer_word(answer: bool | None) -> str:
    return {True: "Ja", False: "Nein", None: "unbekannt (Budget)"}[answer]


# --- Einzelanalyse -------------------------------------------------------------------------------------------------------------------------------


def cover_answer(m: int, cover: V.ExactResult) -> tuple[bool | None, str]:
    """Antwort auf „Überdeckung der Größe höchstens 2m?“ aus einem (eventuell abgebrochenen) Lauf. Abgebrochen zählen nur belegte Aussagen:
    eine gefundene Überdeckung der Größe <= 2m heißt Ja, eine untere Schranke über 2m heißt Nein."""
    limit = R.cover_threshold(m)
    if not cover.aborted:
        return cover.tau <= limit, f"τ = {cover.tau}"
    if len(cover.cover) <= limit:
        return True, f"Abbruch, aber eine Überdeckung der Größe {len(cover.cover)} ≤ {limit} ist gefunden"
    if cover.lower > limit:
        return False, f"Abbruch, aber die untere Schranke {cover.lower} liegt über {limit}"
    return None, f"Abbruch nach {fmt_int(cover.nodes)} Knoten, τ ≥ {cover.lower}"


def clique_answer(m: int, clique: Q.Result) -> tuple[bool | None, str]:
    """Antwort auf „Clique der Größe m im Komplement?“: abgebrochen zählt nur ein Fund der Größe m (Ja)."""
    if not clique.aborted:
        return clique.value == m, f"ω = {clique.value}"
    if clique.value >= m:
        return True, f"Abbruch, aber eine Clique der Größe {clique.value} ist gefunden"
    return None, f"Abbruch nach {fmt_int(clique.nodes)} Knoten, bisher beste Clique {clique.value}"


def analyse(settings: Settings) -> Analysis:
    return analyse_formula(settings, random_formula(settings.n, settings.m, settings.seed))


def analyse_formula(settings: Settings, formula) -> Analysis:
    """Die Kette für eine gegebene Formel (settings.n = Zahl der Variablen, settings.budget = Knotenbudget; m ergibt sich aus der Formel)."""
    formula = tuple(formula)
    m = len(formula)
    graph = R.build_graph(formula)
    n_nodes = len(graph)
    triangle = len(R.clause_triangle_edges(m))
    conflict = len(R.conflict_edges(formula))
    brute = R.brute_force_sat(settings.n, formula)
    dp = D.dpll(formula)
    cover = V.exact_cover(graph, budget=settings.budget)
    clique = Q.largest_clique(R.complement(graph), [1] * n_nodes, bound="color", order="degree", prune=True, budget=settings.budget)
    kernel = M.reduce_graph(graph)

    cover_ans, cover_detail = cover_answer(m, cover)
    clique_ans, clique_detail = clique_answer(m, clique)
    alpha_detail = f"α = {n_nodes - cover.tau}" if not cover.aborted else cover_detail
    stages = (
        Stage("3-SAT", "Sind alle Klauseln gleichzeitig erfüllbar?", brute is not None, f"Brute Force über {fmt_int(2 ** settings.n)} Belegungen; DPLL: {fmt_int(dp.nodes)} Knoten"),
        Stage("Unabhängige Menge", f"Hat G_F eine unabhängige Menge der Größe {m}?", cover_ans, alpha_detail),
        Stage("Knotenüberdeckung", f"Hat G_F eine Überdeckung der Größe höchstens {R.cover_threshold(m)}?", cover_ans, cover_detail),
        Stage("Clique", f"Hat das Komplement von G_F eine Clique der Größe {m}?", clique_ans, clique_detail),
    )
    witness: tuple = ()
    if clique.value >= m and R.is_independent_set(graph, clique.clique):
        witness = tuple(sorted(clique.clique))             # eine Clique im Komplement ist eine unabhängige Menge in G_F
    elif cover_ans is True:
        candidate = R.independent_set_from_cover(n_nodes, cover.cover)
        if len(candidate) >= m and R.is_independent_set(graph, candidate):
            witness = candidate
    decoded = R.decode_assignment(formula, witness, settings.n) if witness else None
    decoded_ok = R.is_satisfying(formula, decoded) if decoded is not None else None
    return Analysis(settings, formula, graph, triangle, conflict, brute, dp, cover, clique, kernel, stages, witness, decoded, decoded_ok)


def validation_errors(a: Analysis) -> list[str]:
    """Ergebnis vor der Anzeige prüfen (DEMO-PLAYBOOK §1d): jede belegte Antwort der Kette stimmt mit der Brute-Force-Probe überein, Belege sind gültig."""
    errors = []
    truth = a.brute is not None
    for stage in a.stages:
        if stage.answer is not None and stage.answer != truth:
            errors.append(f"Stufe „{stage.name}“ antwortet {answer_word(stage.answer)}, die Brute-Force-Probe {answer_word(truth)}.")
    if a.dpll.satisfiable != truth:
        errors.append("Das DPLL und die Brute-Force-Probe widersprechen sich.")
    if a.witness and not R.is_independent_set(a.graph, a.witness):
        errors.append("Die gemeldete unabhängige Menge ist nicht unabhängig.")
    if a.decoded_ok is False:
        errors.append("Die zurückübersetzte Belegung erfüllt die Formel nicht.")
    if not a.cover.aborted and not V.is_cover(a.graph, a.cover.cover):
        errors.append("Die gemeldete Überdeckung überdeckt nicht alle Kanten.")
    return errors


# --- Messreihen ----------------------------------------------------------------------------------------------------------------------------------


def sweep_size(ms=C.SWEEP_M, n: int = C.SWEEP_N, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Größe der Reduktion über m: Knoten, Kanten, Konfliktkanten und Komplementkanten (Median über die festen Formeln)."""
    rows = []
    for m in ms:
        edges, conflicts, comp = [], [], []
        for seed in seeds:
            f = random_formula(n, m, seed)
            g = R.build_graph(f)
            e = R.edge_count(g)
            edges.append(e)
            conflicts.append(e - 3 * m)
            comp.append((3 * m) * (3 * m - 1) // 2 - e)
        rows.append({"m": m, "nodes": 3 * m, "triangle": 3 * m, "edges": median(edges), "conflicts": median(conflicts), "complement": median(comp)})
    return rows


def _solver_nodes(adj, budget):
    """Knoten des Überdeckungslösers auf `adj` und der Cliquensuche auf dem Komplement, je mit Abbruchzeichen."""
    cover = V.exact_cover(adj, budget=budget)
    clique = Q.largest_clique(R.complement(adj), [1] * len(adj), bound="color", order="degree", prune=True, budget=budget)
    return cover, clique


def sweep_effort(ms=C.SWEEP_M, n: int = C.SWEEP_N, seeds=C.SWEEP_SEEDS, budget: int = C.SWEEP_BUDGET) -> list[dict]:
    """Aufwand über m: DPLL auf der Formel gegen die beiden Graphlöser auf G_F, dazu als Gegenstück ein Zufallsgraph mit gleicher Knoten- und Kantenzahl (Median über feste Formeln)."""
    rows = []
    for m in ms:
        dpll_nodes, cover_nodes, clique_nodes, rcover_nodes, rclique_nodes = [], [], [], [], []
        cover_ab = clique_ab = rcover_ab = rclique_ab = sat = 0
        kernel_f, kernel_r = [], []
        for seed in seeds:
            f = random_formula(n, m, seed)
            g = R.build_graph(f)
            sat += R.brute_force_sat(n, f) is not None
            dpll_nodes.append(D.dpll(f).nodes)
            cv, cl = _solver_nodes(g, budget)
            cover_nodes.append(cv.nodes)
            clique_nodes.append(cl.nodes)
            cover_ab += cv.aborted
            clique_ab += cl.aborted
            kernel_f.append(M.reduce_graph(g).kernel_share)
            rg = random_graph(len(g), R.edge_count(g), 7000 + seed)
            rcv, rcl = _solver_nodes(rg, budget)
            rcover_nodes.append(rcv.nodes)
            rclique_nodes.append(rcl.nodes)
            rcover_ab += rcv.aborted
            rclique_ab += rcl.aborted
            kernel_r.append(M.reduce_graph(rg).kernel_share)
        rows.append({
            "m": m, "ratio": m / n, "count": len(seeds), "sat": sat, "dpll": median(dpll_nodes),
            "cover": median(cover_nodes), "cover_aborted": cover_ab, "clique": median(clique_nodes), "clique_aborted": clique_ab,
            "rand_cover": median(rcover_nodes), "rand_cover_aborted": rcover_ab, "rand_clique": median(rclique_nodes), "rand_clique_aborted": rclique_ab,
            "kernel": median(kernel_f), "rand_kernel": median(kernel_r),
        })
    return rows


# --- Zertifikate ---------------------------------------------------------------------------------------------------------------------------------


def yes_rows(a: Analysis, tour_n: int = 12) -> list[dict]:
    """Ja-Belege: Prüfschritte gegen Suchschritte. Nur wenn die Formel erfüllbar ist, gibt es eine Belegung (Beleg) und eine unabhängige Menge der Größe m."""
    rows = []
    if a.decoded is not None and a.decoded_ok:
        ok, reads = K.verify_assignment(a.formula, a.decoded)
        rows.append({"problem": "3-SAT: Belegung", "verify": reads, "verify_unit": "gelesene Literale", "bound": K.accesses_verify_assignment(len(a.formula)),
                     "search": a.dpll.nodes, "search_unit": "DPLL-Knoten"})
        ok2, pairs = K.verify_independent_set(a.graph, a.witness)
        rows.append({"problem": f"unabhängige Menge der Größe {len(a.witness)}", "verify": pairs, "verify_unit": "geprüfte Paare", "bound": K.pairs_verify_set(len(a.witness)),
                     "search": min(a.clique.nodes, a.cover.nodes), "search_unit": "Löser-Knoten (der kleinere der beiden Läufe)"})
    rows.append({"problem": f"Rundreise über {tour_n} Orte (Stück 1)", "verify": K.accesses_verify_tour(tour_n), "verify_unit": "Matrixzugriffe", "bound": K.accesses_verify_tour(tour_n),
                 "search": K.accesses_search_tour(tour_n), "search_unit": "Matrixzugriffe (Held–Karp)"})
    return rows


def bipartite_counts(count: int = C.BIPARTITE_GRAPHS) -> dict:
    """Beleg-Zählung über feste Zufallsgraphen (n = 6 bis 39, Dichte 40 bis 199 Promille): jede Instanz hat entweder eine 2-Färbung oder einen ungeraden Kreis, beides geprüft."""
    bip = odd = 0
    longest = 0
    for seed in range(count):
        n = 6 + seed % 34
        adj = sparse_random_graph(n, 40 + (seed * 13) % 160, 300000 + seed)
        kind, cert, _ = K.two_color_or_odd_cycle(adj)
        if kind == "bipartite":
            assert K.check_two_coloring(adj, cert)
            bip += 1
        else:
            assert K.check_odd_cycle(adj, cert)
            odd += 1
            longest = max(longest, len(cert))
    return {"graphs": count, "bipartite": bip, "odd_cycle": odd, "longest_cycle": longest}


def refutation_random_rows(sizes=C.CERT_N, ratio: float = C.CERT_RATIO, formulas: int = C.CERT_FORMULAS) -> list[dict]:
    """Größe des DPLL-Baums für UNERFÜLLBARE Zufallsformeln über n (Median und Maximum der unerfüllbaren unter `formulas` festen Formeln je Größe)."""
    rows = []
    for n in sizes:
        m = round(ratio * n)
        sizes_found = []
        for seed in range(200000, 200000 + formulas):
            r = D.dpll(random_formula(n, m, seed))
            if not r.satisfiable:
                sizes_found.append(r.nodes)
        rows.append({"n": n, "m": m, "formulas": formulas, "unsat": len(sizes_found),
                     "median": median(sizes_found) if sizes_found else None, "max": max(sizes_found) if sizes_found else None})
    return rows


def refutation_pigeon_rows(hs=C.PIGEON_H) -> list[dict]:
    """Größe des DPLL-Baums für die Schubfach-Formeln (h + 1 Tauben in h Fächer)."""
    rows = []
    for h in hs:
        clauses, variables = K.pigeonhole(h)
        r = D.dpll(clauses)
        rows.append({"h": h, "variables": variables, "clauses": len(clauses), "unsat": not r.satisfiable, "nodes": r.nodes})
    return rows


# --- Verdikte (rein) -----------------------------------------------------------------------------------------------------------------------------


def verdict_chain(a: Analysis) -> tuple[str, str]:
    """Kernergebnis der Kette: alle Stufen gleicher Antwort, Round-Trip, oder Abbruch durch das Budget."""
    s = a.settings
    unknown = [st.name for st in a.stages if st.answer is None]
    truth = a.brute is not None
    m = len(a.formula)
    if unknown:
        return "warning", (f"Das Knotenbudget von {fmt_int(s.budget)} reicht nicht für: {', '.join(unknown)}. Die Formel selbst ist entschieden "
                           f"({'erfüllbar' if truth else 'unerfüllbar'}, DPLL: {fmt_int(a.dpll.nodes)} Knoten); die Graphlöser brauchen mehr als das Budget.")
    if truth:
        back = "" if a.decoded_ok is None else (" Die zurückübersetzte Belegung erfüllt alle Klauseln." if a.decoded_ok else " Die zurückübersetzte Belegung erfüllt die Formel NICHT.")
        return "success", f"Alle vier Stufen antworten **Ja**: die {m} Regeln sind gleichzeitig erfüllbar, G_F hat eine unabhängige Menge der Größe {m}.{back}"
    alpha = len(a.graph) - a.cover.tau
    return "info", (f"Alle vier Stufen antworten **Nein**: die {m} Regeln sind nicht gleichzeitig erfüllbar. Die größte unabhängige Menge von G_F hat {alpha} statt {m} Knoten "
                    f"(τ = {a.cover.tau} > {R.cover_threshold(m)}); mindestens {m - alpha} Klauseln bleiben in jeder Belegung unbedient.")


def verdict_size(rows: list[dict]) -> tuple[str, str]:
    """Wächst die Reduktion polynomial? Knoten genau 3m, Kanten gegen m."""
    first, last = rows[0], rows[-1]
    return "info", (f"Bei m = {first['m']} Klauseln hat G_F {first['nodes']} Knoten und im Median {fmt_int(round(first['edges']))} Kanten, bei m = {last['m']} sind es {last['nodes']} Knoten und "
                    f"{fmt_int(round(last['edges']))} Kanten (davon {fmt_int(round(last['conflicts']))} Konfliktkanten). Die Knotenzahl wächst linear, die Kantenzahl höchstens quadratisch: "
                    "die Übersetzung selbst ist billig.")


def verdict_effort(rows: list[dict]) -> tuple[str, str]:
    """Reduktion erhält die Antwort, nicht die Handhabbarkeit: DPLL gegen Graphlöser in der letzten (größten) Zeile; Gegenstück Zufallsgraph."""
    r = rows[-1]
    c = r["count"]
    return "info", (
        f"Bei m = {r['m']} Klauseln (m/n = {fmt_num(r['ratio'])}) braucht das DPLL auf der Formel im Median {fmt_int(round(r['dpll']))} Knoten; "
        f"die Überdeckungssuche auf G_F {fmt_int(round(r['cover']))} (Abbrüche: {r['cover_aborted']} von {c}), die Cliquensuche im Komplement {fmt_int(round(r['clique']))} (Abbrüche: {r['clique_aborted']} von {c}). "
        f"Auf einem Zufallsgraphen gleicher Größe sind es {fmt_int(round(r['rand_cover']))} bzw. {fmt_int(round(r['rand_clique']))} Knoten (Abbrüche: {r['rand_cover_aborted']} bzw. {r['rand_clique_aborted']} von {c}). "
        "Abgebrochene Läufe zählen mit dem Budget als untere Schranke."
    )


def verdict_kernel(rows: list[dict]) -> tuple[str, str]:
    """Was die Reduktionsregeln der unabhängigen Menge auf G_F ausrichten: Anteil der Knoten, die im Kern bleiben (erste und letzte Zeile), gegen den Zufallsgraphen."""
    first, last = rows[0], rows[-1]
    return "info", (f"Nach den fünf Reduktionsregeln bleiben bei m = {first['m']} im Median {fmt_num(first['kernel'])} % der Knoten von G_F übrig, bei m = {last['m']} sind es {fmt_num(last['kernel'])} % "
                    f"(Zufallsgraph gleicher Größe: {fmt_num(first['rand_kernel'])} % bzw. {fmt_num(last['rand_kernel'])} %).")


def verdict_yes(rows: list[dict]) -> tuple[str, str]:
    """Ja-Belege: Prüfen wächst höchstens quadratisch in der Größe des Belegs. Die Einheiten der Zeilen sind verschieden (Lesezugriffe, Paare, Knoten einer Suche), deshalb nur die Größenordnung."""
    parts = [f"{r['problem']}: {fmt_int(r['verify'])} {r['verify_unit']} zum Prüfen, {fmt_int(r['search'])} {r['search_unit']} zum Finden" for r in rows]
    text = ("Ein Ja-Beleg ist schnell geprüft: " + "; ".join(parts) + ". Die Einheiten sind verschieden; der Punkt ist das Wachstum: Prüfen wächst höchstens quadratisch in der Größe des Belegs, "
            "Finden kann exponentiell wachsen (Rundreise).")
    easy = [r for r in rows if r["search"] < r["verify"]]
    if easy:
        text += f" Bei dieser Zufallsformel ist das Finden ({easy[0]['problem']}) dagegen sogar billiger als das Prüfen: NP-vollständig heißt nicht, dass jede Instanz schwer ist."
    return "info", text


def verdict_bipartite(counts: dict) -> tuple[str, str]:
    """Bipartit: beide Antworten haben einen kurzen Beleg."""
    return "info", (f"Von {counts['graphs']} Zufallsgraphen sind {counts['bipartite']} bipartit (Beleg: eine 2-Färbung) und {counts['odd_cycle']} nicht (Beleg: ein ungerader Kreis, der längste hat {counts['longest_cycle']} Knoten). "
                    "Jeder Beleg ist gegen die Definition geprüft: hier haben **beide** Antworten einen kurzen Beleg (NP ∩ coNP).")


def verdict_refutation(random_rows: list[dict], pigeon_rows: list[dict]) -> tuple[str, str]:
    """Nein-Beleg bei 3-SAT: kein kurzer Beleg bekannt; gemessen wird der DPLL-Baum als eine Art Beleg."""
    big = [r for r in random_rows if r["median"] is not None][-1]
    p0, p1 = pigeon_rows[0], pigeon_rows[-1]
    return "info", (f"Zufällige unerfüllbare Formeln (m/n = {fmt_num(C.CERT_RATIO)}) haben bis n = {big['n']} kleine Widerlegungsbäume (Median {fmt_int(round(big['median']))} Knoten). "
                    f"Die Schubfach-Formeln wachsen dagegen schnell: {fmt_int(p0['nodes'])} Knoten bei {p0['h']} Fächern, {fmt_int(p1['nodes'])} bei {p1['h']}. "
                    "Ein kurzer Nein-Beleg für 3-SAT ist nicht bekannt; ob es immer einen gibt (NP = coNP), ist offen.")
