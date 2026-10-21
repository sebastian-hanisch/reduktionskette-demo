"""DPLL: Erfüllbarkeit durch Suche mit Einheitspropagation (reines Python). Wird in Stück 4 der Reihe (SAT in der Praxis) wörtlich weiterverwendet.

Ein *Knoten* ist ein Aufruf der Suche. Regeln: (1) Einheitsklausel: eine Klausel mit genau einem freien Literal erzwingt es; (2) Verzweigung auf der Variablen, die in den
meisten noch offenen Klauseln vorkommt (Gleichstand: kleinere Nummer), erst wahr, dann falsch. Eine leere Klausel ist ein Widerspruch (Sackgasse)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DpllResult:
    satisfiable: bool
    assignment: dict | None    # erfüllende (teilweise) Belegung bei Erfolg, sonst None
    nodes: int                 # Aufrufe der Suche; bei einer unerfüllbaren Formel die Größe des Widerlegungsbaums


def propagate(clauses, assignment):
    """Einheitspropagation bis zum Fixpunkt. Rückgabe (offene Klauseln, Belegung) oder None bei Widerspruch (leere Klausel).
    Erfüllte Klauseln fallen weg, falsche Literale werden aus den Klauseln gestrichen."""
    clauses = list(clauses)
    while True:
        unit = None
        remaining = []
        for clause in clauses:
            if any(assignment.get(abs(lit)) is not None and assignment[abs(lit)] == (lit > 0) for lit in clause):
                continue
            rest = tuple(lit for lit in clause if assignment.get(abs(lit)) is None)
            if not rest:
                return None
            if len(rest) == 1 and unit is None:
                unit = rest[0]
            remaining.append(rest)
        clauses = remaining
        if unit is None:
            return clauses, assignment
        assignment = dict(assignment)
        assignment[abs(unit)] = unit > 0


def choose_variable(clauses) -> int:
    """Verzweigungsvariable: die häufigste in den offenen Klauseln, bei Gleichstand die kleinere Nummer."""
    count: dict[int, int] = {}
    for clause in clauses:
        for lit in clause:
            count[abs(lit)] = count.get(abs(lit), 0) + 1
    return max(count, key=lambda v: (count[v], -v))


def dpll(formula) -> DpllResult:
    nodes = [0]

    def search(clauses, assignment):
        nodes[0] += 1
        step = propagate(clauses, assignment)
        if step is None:
            return None
        clauses, assignment = step
        if not clauses:
            return assignment
        v = choose_variable(clauses)
        for value in (True, False):
            trial = dict(assignment)
            trial[v] = value
            found = search(clauses, trial)
            if found is not None:
                return found
        return None

    found = search([tuple(c) for c in formula], {})
    return DpllResult(found is not None, found, nodes[0])
