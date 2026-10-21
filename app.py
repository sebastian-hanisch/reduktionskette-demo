"""Reduktionskette: 3-SAT, unabhängige Menge, Knotenüberdeckung, Clique - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Komplexitätsklassen-Reihe (mit Tab „Zertifikate“): eine Formel wird in drei Graphprobleme übersetzt, jede Lösung lässt sich zurückübersetzen.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import red_constants as C
from red_certificates import check_odd_cycle, check_two_coloring, two_color_or_odd_cycle
from red_evaluation import (
    Settings,
    analyse,
    answer_word,
    bipartite_counts,
    fmt_int,
    fmt_num,
    refutation_pigeon_rows,
    refutation_random_rows,
    sweep_effort,
    sweep_size,
    validation_errors,
    verdict_bipartite,
    verdict_chain,
    verdict_effort,
    verdict_kernel,
    verdict_refutation,
    verdict_size,
    verdict_yes,
    yes_rows,
)
from red_layout import dunkles_design, kopf_css
from red_pdf_export import build_pdf
from red_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from red_scenario import literal_name, sparse_random_graph
from red_visualization import build_effort, build_graph, build_pigeon, build_random_refutation, build_size

st.set_page_config(page_title="Reduktionskette – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _size_rows():
    return sweep_size()


@st.cache_data(show_spinner=False)
def _effort_rows():
    return sweep_effort()


@st.cache_data(show_spinner=False)
def _bipartite():
    return bipartite_counts()


@st.cache_data(show_spinner=False)
def _refutation_random():
    return refutation_random_rows()


@st.cache_data(show_spinner=False)
def _refutation_pigeon():
    return refutation_pigeon_rows()


@st.cache_data(show_spinner=False)
def _pdf(settings):
    return build_pdf(analyse(settings))


def _md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _clause_text(clause):
    return "(" + " ∨ ".join(literal_name(lit) for lit in clause) + ")"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in red_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔗 Reduktionskette: 3-SAT, unabhängige Menge, Knotenüberdeckung, Clique")
st.markdown(
    """
Wie ordnet man ein Problem als „NP-vollständig“ ein? Indem man es **in ein anderes übersetzt**, mit Rückweg für die Lösung. Die Demo übersetzt eine Formel aus **Zusammenladeregeln**
(jede Regel: „mindestens eine dieser drei Aussagen gilt“, **3-SAT**) in einen Graphen G_F und stellt dieselbe Ja/Nein-Frage nacheinander als **unabhängige Menge**,
**Knotenüberdeckung** und **Clique**. Gelöst wird mit den Verfahren der Härte-und-Struktur-Reihe; die gefundene Lösung wird zurückübersetzt und gegen die Formel geprüft.
Der zweite Tab **🧾 Zertifikate** zeigt, was an „NP“ leicht ist (Ja-Belege prüfen) und was nicht (Nein-Belege). Drittes Stück der Komplexitätsklassen-Reihe; die Fall-Demos behandeln
einzelne Anwendungen, hier steht eine Beziehung zwischen Problemen im Mittelpunkt.

Weiter unten: die Experimente **🔬 Wächst die Reduktion polynomial?**, **🔬 Erhält die Reduktion die Handhabbarkeit?** und **🔬 Was bleibt nach den Reduktionsregeln?**,
dann **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert eine Reduktion", expanded=True):
    st.markdown(
        """
1. **Ein Dreieck je Klausel.** Jedes Literal einer Klausel wird ein Knoten, die drei Knoten einer Klausel sind paarweise verbunden: höchstens einer davon darf in die **unabhängige Menge** (eine Menge ohne Kante darin).
2. **Konfliktkanten.** Zwischen Knoten, die einander widersprechen (x und nicht x) in verschiedenen Klauseln, liegt eine Kante: so kann man nie x und nicht x zugleich wählen.
3. **Die Frage wird übersetzt.** Die Formel hat m Klauseln. Sie ist **erfüllbar** genau dann, wenn G_F eine unabhängige Menge der Größe m hat (eine Wahl je Klausel, ohne Widerspruch). Dasselbe als **Knotenüberdeckung** (höchstens 2m, denn τ = 3m − α) und als **Clique** im Komplementgraphen (Größe m).
4. **Der Rückweg.** Aus einer unabhängigen Menge der Größe m liest man je Klausel das gewählte Literal ab und erhält eine erfüllende Belegung.
5. **Was das nicht sagt.** Die Übersetzung braucht nur polynomial viel Aufwand (3m Knoten) und erhält die **Antwort**. Ob die Zielprobleme dadurch leichter zu lösen sind, sagt sie nicht (Experiment unten).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Formel**")
    n = st.slider("Variablen n", *bounds("n_slider"), key="n_slider", help="Ja/Nein-Entscheidungen. Die Brute-Force-Probe probiert alle 2^n Belegungen.")
    m = st.slider("Klauseln m", *bounds("m_slider"), key="m_slider",
                  help="Regeln der Form „mindestens eine von drei Aussagen“. Der Graph G_F hat 3m Knoten. Wächst m bei gleichem Zufalls-Seed, kommen Klauseln hinzu, die früheren bleiben.")
    seed = st.number_input("Zufalls-Seed der Formel", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Formel generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Graphlöser**")
    budget = st.select_slider("Knotenbudget je Graphlöser", options=list(C.BUDGETS), format_func=fmt_int, key="budget_select",
                              help="Die Überdeckungssuche auf G_F und die Cliquensuche im Komplement brechen ab, bevor sie mehr Knoten der Suche besuchen.")

sync_query_params({"n_slider": int(n), "m_slider": int(m), "seed_input": int(seed), "budget_select": int(budget)})

settings = Settings(n=int(n), m=int(m), seed=int(seed), budget=int(budget))
a = _analysis(settings)
for message in validation_errors(a):
    st.error(message)

tab_chain, tab_cert = st.tabs(["🔗 Reduktionskette", "🧾 Zertifikate"])

# =====================================================================================================================================================
# Tab 1: Reduktionskette
# =====================================================================================================================================================

with tab_chain:
    st.markdown("## 🎯 Eine Formel, vier Fragen")
    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(build_graph(a.formula, a.graph, a.witness), width="stretch", key="graph_fig")
        st.caption("G_F: ein Dreieck je Klausel (dunkel), Konfliktkanten gestrichelt rot, Knoten mit ihrem Literal beschriftet. Grün: die unabhängige Menge der Größe m, falls eine gefunden ist.")
    with right:
        c1, c2, c3 = st.columns(3)
        c1.metric("Knoten von G_F", fmt_int(len(a.graph)), help="Genau 3m: ein Knoten je Literal.")
        c2.metric("Kanten von G_F", fmt_int(a.triangle_edges + a.conflict_edges), help=f"{a.triangle_edges} Dreiecks- und {a.conflict_edges} Konfliktkanten.")
        c3.metric("DPLL-Knoten", fmt_int(a.dpll.nodes), help="Suche direkt auf der Formel (Einheitspropagation und Verzweigung).")
        c4, c5, c6 = st.columns(3)
        c4.metric("Überdeckung", fmt_int(a.cover.nodes) + (" (Abbruch)" if a.cover.aborted else ""), help="Knoten der exakten Suche nach der kleinsten Überdeckung von G_F (Löser aus vertex-cover-demo).")
        c5.metric("Clique", fmt_int(a.clique.nodes) + (" (Abbruch)" if a.clique.aborted else ""), help="Knoten der Branch-and-Bound-Suche nach der größten Clique im Komplement.")
        c6.metric("Kern", f"{fmt_num(a.kernel.kernel_share)} %", help="Anteil der Knoten, die nach den Reduktionsregeln der unabhängigen Menge übrig bleiben.")
        st.markdown(_md_table(
            ["Stufe", "Frage", "Antwort", "Beleg / Zahl"],
            [[s.name, s.question, f"**{answer_word(s.answer)}**", s.detail] for s in a.stages],
        ))
        with st.expander("Die Klauseln"):
            st.markdown("\n".join(f"{i + 1}. {_clause_text(c)}" for i, c in enumerate(a.formula)))

    if a.decoded is not None:
        names = ", ".join(f"x{v} = {'wahr' if val else 'falsch'}" for v, val in sorted(a.decoded.items()))
        chosen = ", ".join(f"Klausel {v // 3 + 1}: {literal_name(a.formula[v // 3][v % 3])}" for v in a.witness)
        st.markdown(f"**Rückweg.** Gewählte Knoten (ein Literal je Klausel): {chosen}.  \nZurückübersetzte Belegung: {names}.")
        if a.decoded_ok:
            st.success("Geprüft: die zurückübersetzte Belegung erfüllt alle Klauseln.")
    if st.button("📄 PDF erstellen"):
        st.session_state["pdf_for"] = settings
    if st.session_state.get("pdf_for") == settings:
        st.download_button("⬇️ PDF herunterladen", data=_pdf(settings), file_name="reduktionskette.pdf", mime="application/pdf")

    st.markdown("## ❓ Kernfrage: Sind die Regeln gleichzeitig erfüllbar, und sagen alle vier Stufen dasselbe?")
    vkind, vtext = verdict_chain(a)
    getattr(st, vkind)(vtext)

    st.markdown("---")

    st.subheader("🔬 Experiment: Wächst die Reduktion polynomial?")
    size_rows = _size_rows()
    st.caption(f"Größe von G_F über die Zahl der Klauseln m bei {C.SWEEP_N} Variablen; Median über {len(C.SWEEP_SEEDS)} feste Formeln (SWEEP_SEEDS). Die Formel wächst: dieselbe Zufalls-Seed, Klauseln kommen dazu.")
    st.plotly_chart(build_size(size_rows), width="stretch", key="size_chart")
    st.markdown(_md_table(
        ["m", "Knoten", "Kanten", "davon Konflikt", "Kanten im Komplement"],
        [[r["m"], r["nodes"], fmt_int(round(r["edges"])), fmt_int(round(r["conflicts"])), fmt_int(round(r["complement"]))] for r in size_rows],
    ))
    vkind, vtext = verdict_size(size_rows)
    getattr(st, vkind)(vtext)

    st.markdown("---")

    st.subheader("🔬 Experiment: Erhält die Reduktion die Handhabbarkeit?")
    with st.spinner(f"Rechne die Messreihe ({len(C.SWEEP_SEEDS)} feste Formeln je Größe, Budget {fmt_int(C.SWEEP_BUDGET)} Knoten) …"):
        effort_rows = _effort_rows()
    st.caption(f"Knoten der Suche über m bei {C.SWEEP_N} Variablen (Median über {len(C.SWEEP_SEEDS)} feste Formeln, Budget {fmt_int(C.SWEEP_BUDGET)} Knoten je Lauf, logarithmische Achse): "
               "das DPLL auf der Formel gegen die beiden Graphlöser auf G_F. Gestrichelt: ein Zufallsgraph mit **gleicher Knoten- und Kantenzahl** als Gegenstück.")
    st.plotly_chart(build_effort(effort_rows, C.SWEEP_BUDGET), width="stretch", key="effort_chart")
    st.markdown(_md_table(
        ["m", "m/n", "erfüllbar", "DPLL", "Überdeckung G_F", "Clique G_F", "Überdeckung Zufall", "Clique Zufall"],
        [[r["m"], fmt_num(r["ratio"]), f"{r['sat']} von {r['count']}", fmt_int(round(r["dpll"])),
          f"{fmt_int(round(r['cover']))} ({r['cover_aborted']} Abbrüche)", f"{fmt_int(round(r['clique']))} ({r['clique_aborted']})",
          f"{fmt_int(round(r['rand_cover']))} ({r['rand_cover_aborted']})", f"{fmt_int(round(r['rand_clique']))} ({r['rand_clique_aborted']})"] for r in effort_rows],
    ))
    vkind, vtext = verdict_effort(effort_rows)
    getattr(st, vkind)(vtext)

    st.markdown("---")

    st.subheader("🔬 Experiment: Was bleibt nach den Reduktionsregeln?")
    st.caption("Die Reduktionsregeln der unabhängigen Menge (Grad 0, Grad 1, Dreieck, Faltung, Dominanz) verkleinern einen Graphen, ohne die Antwort zu ändern. Hier der Anteil der Knoten, "
               "der im Kern übrig bleibt (Median über dieselben Formeln und Zufallsgraphen wie oben).")
    st.markdown(_md_table(
        ["m", "Kern von G_F", "Kern des Zufallsgraphen"],
        [[r["m"], f"{fmt_num(r['kernel'])} %", f"{fmt_num(r['rand_kernel'])} %"] for r in effort_rows],
    ))
    vkind, vtext = verdict_kernel(effort_rows)
    getattr(st, vkind)(vtext)

# =====================================================================================================================================================
# Tab 2: Zertifikate
# =====================================================================================================================================================

with tab_cert:
    st.markdown("## 🧾 Was an „NP“ leicht ist: Belege prüfen")
    st.markdown(
        """
Ein **Zertifikat** ist ein Beleg, den man in polynomialer Zeit prüft. „In NP“ heißt: jede **Ja**-Instanz hat einen kurzen, schnell prüfbaren Beleg, auch wenn das **Finden** schwer sein kann.
Für **Nein**-Instanzen verlangt NP nichts; dort liegt das Gegenstück **coNP**. Probleme, die auf beiden Seiten einen kurzen Beleg haben, liegen in **NP ∩ coNP**.
        """
    )
    st.subheader("🔬 Ja-Belege: Prüfen gegen Finden")
    yrows = yes_rows(a)
    st.markdown(_md_table(
        ["Problem", "Prüfen", "Obergrenze beim Prüfen", "Finden"],
        [[r["problem"], f"{fmt_int(r['verify'])} {r['verify_unit']}", fmt_int(r["bound"]), f"{fmt_int(r['search'])} {r['search_unit']}"] for r in yrows],
    ))
    if len(yrows) == 1:
        st.info("Die aktuelle Formel ist nicht erfüllbar oder die Löser sind am Budget abgebrochen: es gibt keinen Beleg der Größe m zu prüfen. Wählen Sie im Schnellstart ein erfüllbares Beispiel.")
    vkind, vtext = verdict_yes(yrows)
    getattr(st, vkind)(vtext)

    st.markdown("---")

    st.subheader("🔬 Beide Seiten mit kurzem Beleg: bipartit")
    st.caption("Ein Graph ist bipartit, wenn man seine Knoten so in zwei Gruppen teilen kann, dass jede Kante die Gruppen verbindet. Ja-Beleg: die **2-Färbung**. Nein-Beleg: ein **Kreis ungerader Länge**.")
    counts = _bipartite()
    ex_cols = st.columns(2)
    shown = {"bipartite": None, "odd_cycle": None}
    for seed_ in range(2000):
        adj = sparse_random_graph(8, 200, 400000 + seed_)
        kind_, cert_, _ = two_color_or_odd_cycle(adj)
        if shown[kind_] is None:
            shown[kind_] = (adj, cert_)
        if all(shown.values()):
            break
    adj_b, color = shown["bipartite"]
    adj_o, cycle = shown["odd_cycle"]
    with ex_cols[0]:
        st.markdown("**Ein bipartiter Graph (8 Knoten):**")
        st.markdown(f"2-Färbung (Farbe je Knoten 1 bis 8): {' '.join(str(c) for c in color)}  \nGeprüft: jede der {sum(len(x) for x in adj_b) // 2} Kanten verbindet zwei Farben: {'ja' if check_two_coloring(adj_b, color) else 'nein'}.")
    with ex_cols[1]:
        st.markdown("**Ein Graph mit ungeradem Kreis (8 Knoten):**")
        st.markdown(f"Ungerader Kreis (Knoten): {' → '.join(str(v + 1) for v in cycle)} → {cycle[0] + 1} (Länge {len(cycle)})  \nGeprüft: ungerade Länge, jeder Schritt ist eine Kante: {'ja' if check_odd_cycle(adj_o, cycle) else 'nein'}.")
    vkind, vtext = verdict_bipartite(counts)
    getattr(st, vkind)(vtext)

    st.markdown("---")

    st.subheader("🔬 Nein-Belege bei 3-SAT: kein kurzer Beleg bekannt")
    st.caption("Für „diese Formel ist unerfüllbar“ ist kein kurzer, leicht prüfbarer Beleg bekannt. Gemessen wird deshalb die **Größe des DPLL-Baums**: sie ist eine Art Beleg (eine Widerlegung, deren Größe man zählt), "
               "aber nicht der kürzeste mögliche.")
    with st.spinner("Rechne die Widerlegungsbäume …"):
        rrows = _refutation_random()
        prows = _refutation_pigeon()
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"**Zufällige unerfüllbare Formeln** (m/n = {fmt_num(C.CERT_RATIO)}, je {C.CERT_FORMULAS} feste Formeln je n)")
        st.plotly_chart(build_random_refutation(rrows), width="stretch", key="rand_ref_chart")
    with g2:
        st.markdown("**Schubfach-Formeln** (h + 1 Tauben passen nicht in h Fächer)")
        st.plotly_chart(build_pigeon(prows), width="stretch", key="pigeon_chart")
    st.markdown(_md_table(
        ["n", "m", "unerfüllbar (von 12)", "Median der Knoten", "Maximum"],
        [[r["n"], r["m"], r["unsat"], "–" if r["median"] is None else fmt_int(round(r["median"])), "–" if r["max"] is None else fmt_int(r["max"])] for r in rrows],
    ))
    st.markdown(_md_table(
        ["Fächer h", "Variablen", "Klauseln", "Knoten des DPLL-Baums"],
        [[r["h"], r["variables"], r["clauses"], fmt_int(r["nodes"])] for r in prows],
    ))
    st.caption(f"Für h = {C.PIGEON_H_PRECOMPUTED} Fächer braucht dieses DPLL in Python rund eine Viertelminute und wird hier nicht live gerechnet; der Test `tests/test_claims.py` rechnet es nach.")
    vkind, vtext = verdict_refutation(rrows, prows)
    getattr(st, vkind)(vtext)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Reduktion erhält die Antwort** | Sie erhält nicht die Rechenzeit: dieselbe Frage kann auf der Formel in wenigen Schritten entschieden sein und auf dem Graphen das Budget sprengen. | Stück 4 (SAT in der Praxis) |
| **Gelöst wird mit Lehrbuch-Verfahren** | Die Graphlöser sind die einfachen Verfahren der Härte-und-Struktur-Reihe (Branch-and-Bound, Verzweigen); Profi-Löser schneiden anders ab. Ein Abbruch am Budget sagt nichts über die Instanz an sich. | Härte-und-Struktur-Reihe |
| **NP-vollständig gilt für den schlimmsten Fall** | Zufallsformeln sind eine Instanzfamilie und oft leicht; „NP-vollständig“ heißt nicht „jede Instanz schwer“. | Stück 4 |
| **Ein Zufallsgraph ist ein fairer Vergleich** | Gleiche Knoten- und Kantenzahl, aber andere Struktur; die Reihenfolge der Schwierigkeit ist nicht einheitlich (je nach Löser und Größe). Die Tabelle zeigt es, die Demo behauptet keine Reihenfolge. | – |
| **Die DPLL-Baumgröße ist ein Nein-Beleg** | Sie ist die Größe einer bestimmten Suche, nicht des kürzesten Belegs. Dass kein kurzer Nein-Beleg bekannt ist, heißt nicht, dass es keinen gibt (NP = coNP ist offen). | – |
| **Cook–Levin wird vorausgesetzt** | Dass 3-SAT NP-vollständig ist, wird hier genannt, nicht bewiesen oder nachgebaut. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(r"**Formel.** Eine 3-KNF-Formel über den Variablen $x_1, \dots, x_n$ besteht aus $m$ Klauseln, jede mit drei Literalen:")
    st.latex(r"F = C_1 \wedge \dots \wedge C_m, \qquad C_i = (\ell_{i1} \vee \ell_{i2} \vee \ell_{i3})")
    st.markdown(r"**Der Graph $G_F$.** Knoten sind die Paare $(i, j)$ (Literal $j$ der Klausel $i$), also $3m$ Stück. Kanten:")
    st.latex(r"E = \{\, (i,j)(i,j') : j \ne j' \,\} \;\cup\; \{\, (i,j)(k,l) : i \ne k,\; \ell_{ij} = \neg \ell_{kl} \,\}")
    st.markdown(r"**Behauptung.** $F$ ist genau dann erfüllbar, wenn $G_F$ eine unabhängige Menge der Größe $m$ hat; mehr als $m$ Knoten gehen nie (ein Knoten je Dreieck):")
    st.latex(r"F \text{ erfüllbar} \iff \alpha(G_F) = m")
    st.markdown(
        r"""
*Hin:* in einer erfüllenden Belegung wählt man je Klausel ein wahres Literal; zwei gewählte Knoten liegen in verschiedenen Klauseln und widersprechen sich nicht (die Belegung ist widerspruchsfrei), also keine Kante.
*Zurück:* eine unabhängige Menge der Größe $m$ enthält genau einen Knoten je Dreieck und nie $x$ zusammen mit $\neg x$; setzt man die gewählten Literale wahr, ist jede Klausel bedient.

**Überdeckung und Clique.** Das Komplement einer Knotenüberdeckung ist eine unabhängige Menge (Gallai), und eine unabhängige Menge von $G$ ist eine Clique des Komplementgraphen $\overline{G}$:
"""
    )
    st.latex(r"\tau(G_F) = 3m - \alpha(G_F), \qquad \omega(\overline{G_F}) = \alpha(G_F)")
    st.latex(r"F \text{ erfüllbar} \iff \tau(G_F) \le 2m \iff \omega(\overline{G_F}) = m")
    st.markdown(
        """
| Annahme | Bedeutung | Wer setzt an |
|---|---|---|
| Je Klausel drei verschiedene Variablen | keine Klausel enthält x und nicht x; keine Wiederholung | – |
| Konfliktkanten nur zwischen verschiedenen Klauseln | innerhalb einer Klausel verbindet das Dreieck ohnehin alle | – |
| Obere Grenze α ≤ m | ein Knoten je Dreieck; daher ist τ ≥ 2m immer und „Nein“ heißt τ > 2m | – |
| Lösung durch exakte Suche mit Knotenbudget | bei Abbruch gilt nur, was belegt ist (gefundene Überdeckung, untere Schranke, gefundene Clique) | Härte-und-Struktur-Reihe |

**Folgestücke.** Stück 4 der Reihe (SAT in der Praxis) fragt, warum die Formel selbst so viel leichter zu entscheiden ist als der Graph; Stück 6 (Approximation) und Stück 7 (parametrisierte Komplexität) bauen auf diesen Reduktionen auf.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
