"""PDF-Export (fpdf2, Kernschriften): Formel, Graphgröße, die vier Stufen und der Rückweg. Kein Gedankenstrich und kein Euro-Zeichen (Kernschriften)."""

from fpdf import FPDF

import red_evaluation as ev
from red_scenario import literal_name


def _text(value: str) -> str:
    """Zeichen, die die Kernschriften nicht kennen, ersetzen (Gedankenstrich, Pfeile, Fettdruck-Markierung, mathematische Zeichen)."""
    table = {"–": "-", "—": "-", "→": "->", "**": "", "€": "EUR", "·": "*", "³": "^3", "≤": "<=", "≥": ">=", "∨": "v", "¬": "-", "∧": "&", "⇔": "<=>", "α": "alpha", "τ": "tau", "ω": "omega", "≈": "~"}
    for old, new in table.items():
        value = value.replace(old, new)
    return value


def _para(pdf: FPDF, height: float, text: str) -> None:
    """Absatz über die volle Breite; danach steht der Cursor wieder am linken Rand (fpdf2 setzt ihn sonst an den rechten Rand)."""
    pdf.multi_cell(0, height, _text(text), new_x="LMARGIN", new_y="NEXT")


def build_pdf(a: ev.Analysis) -> bytes:
    s = a.settings
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _text("Reduktionskette: 3-SAT, unabhängige Menge, Knotenüberdeckung, Clique"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, f"Variablen: {s.n}   Klauseln: {s.m}   Zufalls-Seed: {s.seed}   Knotenbudget je Graphlöser: {ev.fmt_int(s.budget)}\n"
                    f"Graph G_F: {len(a.graph)} Knoten, {ev.fmt_int(a.triangle_edges + a.conflict_edges)} Kanten ({a.triangle_edges} Dreiecks-, {a.conflict_edges} Konfliktkanten)")
    pdf.ln(1)
    kind, verdict = ev.verdict_chain(a)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Ergebnis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, verdict)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Die vier Stufen", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for st in a.stages:
        _para(pdf, 5.5, f"{st.name}: {st.question} {ev.answer_word(st.answer)} ({st.detail})")
    if a.decoded is not None:
        _para(pdf, 5.5, "Unabhängige Menge der Größe m (Knoten): " + " ".join(str(v + 1) for v in a.witness))
        _para(pdf, 5.5, "Zurückübersetzte Belegung: " + ", ".join(f"x{v}={'wahr' if val else 'falsch'}" for v, val in sorted(a.decoded.items())) + f" (erfüllt F: {'ja' if a.decoded_ok else 'nein'})")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Klauseln", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for i, clause in enumerate(a.formula):
        _para(pdf, 4.8, f"{i + 1}: (" + " v ".join(literal_name(lit) for lit in clause) + ")")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    _para(pdf, 4.5, "Aufwand in Knoten der Suche, nicht in Sekunden. Sebastian Hanisch - Operations Research und Machine Learning.")
    return bytes(pdf.output())
