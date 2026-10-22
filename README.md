# Reduktionskette: 3-SAT, unabhängige Menge, Knotenüberdeckung, Clique – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-reduktionskette-demo.streamlit.app/)** -->

Drittes Stück der **Komplexitätsklassen-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, mit dem Tab **Zertifikate**. Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **eine Beziehung zwischen Problemen**: die **Reduktion**. Sie ist die **Konvergenz** mit der Härte-und-Struktur-Reihe: deren Löser ([max-clique-demo](https://github.com/sebastian-hanisch/max-clique-demo), [vertex-cover-demo](https://github.com/sebastian-hanisch/vertex-cover-demo), [mis-local-search-demo](https://github.com/sebastian-hanisch/mis-local-search-demo)) bekommen hier Instanzen, die aus Formeln gebaut sind. Kante in der Reihe: Stück 1 ([zuordnung-vs-rundreise-demo](https://github.com/sebastian-hanisch/zuordnung-vs-rundreise-demo)) hat die Rundreise als „schwer“ eingeordnet, ohne zu sagen, woher man die Härte nimmt; dieses Stück liefert die Beziehung zwischen Problemen, Folgestücke fragen, wie schwer typische Instanzen wirklich sind.

## Warum dieses Problem

„NP-vollständig“ heißt: das Problem ist in NP, und jedes andere NP-Problem lässt sich in polynomialer Zeit darauf zurückführen. Praktisch bedeutet das: **eine Frage wird in eine andere übersetzt, mit Rückweg für die Lösung**. Die Demo übersetzt eine Formel aus Zusammenladeregeln (jede Regel: „mindestens eine von drei Aussagen gilt“, **3-SAT**) in einen Graphen G_F und stellt dieselbe Ja/Nein-Frage nacheinander als **unabhängige Menge**, **Knotenüberdeckung** und **Clique**. Kernfrage: **Was erhält die Übersetzung, und was nicht?** Sie erhält die **Antwort** (in beide Richtungen, auch auf Nein-Instanzen) und lässt sich zurückrechnen; sie erhält nicht ohne Weiteres die **Handhabbarkeit**. Der Tab **Zertifikate** zeigt die andere Seite von NP: Ja-Belege sind schnell geprüft, für Nein-Belege ist bei 3-SAT kein allgemein kurzer Beleg bekannt.

## Modell

- **Formel.** 3-KNF über n Variablen mit m Klauseln, je drei verschiedene Variablen mit zufälligem Vorzeichen (eigener SplitMix64-Generator, deshalb auf jeder Plattform dieselben Formeln). Wächst m bei gleichem Zufalls-Seed, kommen Klauseln hinzu, die früheren bleiben.
- **Graph G_F.** Je Klausel ein Dreieck (ein Knoten je Literal), dazu eine Konfliktkante zwischen Knoten komplementärer Literale verschiedener Klauseln: 3m Knoten.
- **Äquivalenzen.** F erfüllbar ⇔ α(G_F) = m ⇔ τ(G_F) = 2m ⇔ ω(Komplement von G_F) = m, mit τ = 3m − α (Gallai-Identität) und α ≤ m (ein Knoten je Dreieck).
- **Rückweg.** Aus einer unabhängigen Menge der Größe m wird je Klausel das gewählte Literal wahr gesetzt; die Belegung wird gegen die Formel geprüft.
- **Löser.** Die kleinste Überdeckung von G_F (exakte Suche mit LP-Kern und Verzweigen), die größte Clique im Komplement (Branch-and-Bound mit Färbungsschranke) und die Reduktionsregeln der unabhängigen Menge. Alle mit **Knotenbudget**: bei Abbruch gilt nur, was belegt ist (gefundene Überdeckung bzw. Clique, untere Schranke), nie „optimal“.
- Mathematik und Annahmentabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Quelle | Anmerkung |
|---|---|---|
| Reduktion, Rückweg, Prüfer | `red_reduction.py` | eigene Einheiten: Dreieckskanten, Konfliktkanten, Komplement, Gallai, Rückübersetzung |
| DPLL (Einheitspropagation, Verzweigung) | `red_dpll.py` | eigene Suche auf der Formel; Aufwand in Knoten |
| Zertifikate | `red_certificates.py` | Prüfer mit Zählung, 2-Färbung oder ungerader Kreis, Schubfach-Formeln |
| Überdeckung, Clique, Reduktionsregeln | `red_cover.py`, `red_clique.py`, `red_mis_reduce.py` | **wörtliche Kopien** der Löser aus vertex-cover-demo (Commit 60180da), max-clique-demo (74e82af) und mis-local-search-demo (2fbf186); nur die Importzeile der Konstanten ist angepasst. Ein Test vergleicht die Kopie mit dem Original, solange es im Portfolio-Ordner liegt |

Experimente in der App: **Wächst die Reduktion polynomial?**, **Erhält die Reduktion die Handhabbarkeit?** (DPLL und Graphlöser gegen Zufallsgraphen gleicher Größe), **Was bleibt nach den Reduktionsregeln?**; im Tab **Zertifikate** Ja-Belege, bipartit (beide Seiten kurz) und Nein-Belege bei 3-SAT.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Medianwerte der Messreihen sind über 5 feste Formeln je Größe (`SWEEP_SEEDS`) gebildet, bei n = 8 Variablen und Knotenbudget 20.000 je Löser; die Zahlen der Presets sind Einzelinstanzen und als solche ausgewiesen.

| Frage | Befund |
|---|---|
| **Wie groß ist die Reduktion?** | Genau 3m Knoten. Kanten (Median): m = 6 / 12 / 18 / 24 / 30: 27 / 75 / 143 / 235 / 346, davon Konfliktkanten 9 / 39 / 89 / 163 / 256; das Komplement hat 126 / 555 / 1.288 / 2.321 / 3.659 Kanten. Linear in den Knoten, höchstens quadratisch in den Kanten (`test_claim_size_of_the_reduction`). |
| **Lehrbeispiel von Hand** | 3 Klauseln, 9 Knoten, 9 Dreiecks- und 6 Konfliktkanten, Komplement 21 Kanten; α = 3, τ = 6 = 2m (`test_claim_mini_formula_by_hand`). |
| **Unerfüllbares Beispiel von Hand** | Alle acht Klauseln über drei Variablen: 24 Knoten, 72 Kanten, Komplement 204; α = 7 = m − 1, τ = 17 > 16 (`test_claim_unsatisfiable_formula_by_hand`). |
| **Erhält die Reduktion die Handhabbarkeit?** | **Nicht in diesen Messungen** (n = 8 Variablen, 5 Formeln je Größe, Lehrbuch-Löser, Budget 20.000 Knoten). Das DPLL entscheidet die Formel im Median in 4 bis 5 Knoten (Einzelfälle bis 9). Die Überdeckungssuche auf G_F braucht im Median 31 / 332 / 1.954 / 10.415 / 20.001 Knoten (m = 6 bis 30) und bricht bei m = 30 (90 Knoten) in 5 von 5 Fällen am Budget ab, ein Zufallsgraph gleicher Größe aber ebenso; die Einzelzahlen sind als Größenordnung zu lesen. Die Cliquensuche 1 / 7 / 15 / 96 / 4.263 (Abbrüche 0 / 0 / 0 / 1 / 2 von 5) (`test_claim_effort_of_the_solvers_against_dpll_and_random_graphs`). |
| **Sind Reduktionsgraphen schwerer als Zufallsgraphen gleicher Größe?** | **Kein einheitliches Bild.** Überdeckungssuche: auf G_F schwerer bei m = 12, 18 und 24 (332, 1.954, 10.415 gegen 16, 494, 5.846), bei m = 30 brechen beide in 5 von 5 Fällen ab. Cliquensuche: bei m = 18 und 24 ist der Zufallsgraph schwerer (61 und 175 gegen 15 und 96), bei m = 30 G_F (4.263 gegen 1.528) (`test_claim_the_reduction_keeps_the_answer_but_not_the_ease`). |
| **Schrumpfen die Reduktionsregeln G_F?** | Der Kern (Anteil der Knoten) von G_F ist 0 / 58,3 / 100 / 100 / 100 %, der von Zufallsgraphen 0 / 0 / 79,6 / 91,7 / 97,8 % (m = 6 bis 30): ab m = 18 greift auf G_F im Median keine Regel mehr. Warum, ist nicht untersucht (`test_claim_kernel_after_the_reduction_rules`). |
| **Ja-Belege** | Standardformel (n = 8, m = 12): Prüfen höchstens 36 gelesene Literale, eine unabhängige Menge der Größe 12 prüft 66 Paare; eine Rundreise über 12 Orte 12 Matrixzugriffe, Held–Karp 56.342 (`test_claim_yes_certificates_are_cheap`). Bei der Zufallsformel braucht das Finden nur 6 DPLL-Aufrufe, gegenüber 16 gelesenen Literalen zum Prüfen (verschiedene Einheiten, nur als Größenordnung zu lesen): NP-vollständig heißt nicht „jede Instanz schwer“. |
| **Bipartit: beide Seiten haben einen kurzen Beleg** | Von 400 Zufallsgraphen sind 119 bipartit (2-Färbung) und 281 nicht (ungerader Kreis, längster 9 Knoten); jeder Beleg ist gegen die Definition geprüft (`test_claim_bipartite_certificates`). |
| **Nein-Beleg bei zufälligen unerfüllbaren Formeln** | Klein: bei m/n = 4,3 und n = 10 / 15 / 20 / 25 / 30 / 35 / 40 ein Median von 7 / 15 / 19 / 28 / 36 / 52 / 51 DPLL-Knoten, **aber** nur über 3 / 3 / 3 / 2 / 4 / 4 / 2 unerfüllbare unter je 12 Formeln (sehr kleine Stichproben) (`test_claim_random_unsatisfiable_formulas_have_small_refutations`). |
| **Nein-Beleg bei Schubfach-Formeln** | h + 1 Tauben in h Fächer: h = 2 bis 8: 3 / 11 / 47 / 239 / 1.439 / 10.079 / 80.639 Knoten, Faktor je Fach 3,7 / 4,3 / 5,1 / 6,0 / 7,0 (bis h = 7 live in der App, h = 8 in rund 18 Sekunden nachgerechnet) (`test_claim_pigeonhole_…`). |
| **Presets (Einzelinstanzen)** | Standardfall (n = 8, m = 12): erfüllbar, DPLL 6, Überdeckung 386, Clique 1 Knoten. Unerfüllbar (n = 3, m = 18): DPLL 7, Überdeckung 959, Clique 83. Nahe der Schwelle (n = 7, m = 28): unerfüllbar, DPLL 7, beide Graphlöser brechen bei 10.000 Knoten ab. Größte Formel (n = 12, m = 30, Budget 100.000): erfüllbar, DPLL 6, Überdeckung bricht ab, Clique 44.390 Knoten (`test_claim_presets_…`). |

## Ehrliche Grenzen

- **Zufalls-3-SAT ist eine Instanzfamilie.** Das DPLL löst diese Formeln auch bei m/n = 3,8 in wenigen Knoten; „NP-vollständig“ gilt für den schlimmsten Fall. Der Befund „DPLL ≪ Graphlöser“ gilt für **diese** Formeln, diese Löser und diese Größen (n = 8, m bis 30, Budget 20.000), nicht allgemein.
- **Die Graphlöser sind Lehrbuch-Verfahren** (exaktes Verzweigen, Branch-and-Bound mit Färbungsschranke); Profi-Löser (CDCL-SAT-Löser, moderne Branch-and-Reduce-Löser) schneiden anders ab. Ein Abbruch am Budget sagt etwas über diesen Lauf, nicht über die Instanz.
- **Fünf Formeln je Größe, ein einzelnes n.** Die Aussagen zu Zufallsgraphen und Kernen sind Medianwerte über fünf Instanzen; die Reihenfolge der Schwierigkeit hängt von Löser und Größe ab.
- **Die Nein-Beleg-Zahlen sind DPLL-Baumgrößen,** nicht kürzeste Beweise; die Zufallswerte stützen sich auf nur 2 bis 4 unerfüllbare Formeln je Größe.
- **Dass 3-SAT NP-vollständig ist (Cook–Levin), wird genannt, nicht gezeigt.** Die Reduktion beweist die NP-Schwere der drei Graphprobleme nur **unter** dieser Voraussetzung.
- **Kein Wettbewerbs-SAT-Löser.** Warum die Formel so viel leichter entschieden wird als der Graph, ist Gegenstand eines Folgestücks, nicht dieses.

## Befunde und Korrekturen gegenüber dem Plan

- **Presets über Zufalls-Seeds statt handgebauter Formeln.** Der Plan nannte „Lehrbeispiel“ und „unerfüllbares Beispiel“ als eigene Formeltypen; das hätte tote Regler (n, m, Seed) bedeutet. Stattdessen sind sie Presets (Lehrbeispiel: n = 3, m = 3; unerfüllbar: n = 3, m = 18, Seed 3); die handgebauten Formeln mit Handrechnung stehen in den Tests und Claims.
- **Der Vergleich mit Zufallsgraphen (Hypothese H3) ist gemessen** und ergibt kein einheitliches Bild (siehe Befunde); die im Plan erwogene Aussage „Reduktionsgraphen sind schwerer als Zufallsgraphen“ steht deshalb **nicht** in der App.
- **Mehr unerfüllbare Instanzen für die Kette:** die erste Vormessung hatte fast nur erfüllbare Formeln (399 von 400); die Messung arbeitet mit n = 3 bis 5 und m bis 22 (Nein-Seite gut besetzt).
- **Obergrenzen verkleinert:** n ≤ 12 und m ≤ 30 wie geplant, das Knotenbudget im Regler bis 100.000 (nicht 300.000), weil ein Lauf an der Grenze sonst zu lange dauert; die Messreihen laufen mit 20.000.
- **Stufen 1 und 2 aus einem Lauf:** die unabhängige Menge und die Knotenüberdeckung kommen aus derselben exakten Suche (Gallai); unabhängig davon prüft die Cliquensuche im Komplement dieselbe Antwort.
- **Schubfach h = 8** wird nicht live gerechnet (rund 18 Sekunden in Python), sondern im Test nachgerechnet.
- **Unerklärte Konsolenmeldung aus Stück 1** (`<text> attribute y: -Infinity` beim ersten Zeichnen) trat hier in keiner Ansicht auf; die Karte aus Stück 1 setzt Pfeile über leere Beschriftungen, diese Demo nicht. Die Ursache in Stück 1 ist damit nicht bewiesen.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung an den Mini-Formeln (`tests/conftest.py`): Konfliktkanten, Dreieckskanten, Komplement, Gallai, Rückübersetzung (`tests/test_reduction.py`); DPLL gegen Brute Force und Handwerte, Prüfer mit absichtlich verfälschten Eingaben (`tests/test_dpll_and_certificates.py`); Generator mit Referenzwerten von SplitMix64 (`tests/test_scenario.py`).
- **Orakel** (`tests/test_oracle_reduktionskette.py`): die vier Aussagen der Kette gegen Brute Force über alle Belegungen, α gegen CP-SAT und gegen Aufzählen aller Teilmengen, **beide Richtungen** (erfüllbare **und** unerfüllbare Formeln), Rückübersetzung erfüllt die Formel. Im Repo laufen kleine Fassungen; der **große Lauf im Scratch-Ordner** (420 Formeln mit n = 3 bis 5: 357 erfüllbar, 63 unerfüllbar, keine abgebrochen; α jeder siebten Formel gegen CP-SAT; DPLL gegen Brute Force auf 600 Formeln, davon 112 unerfüllbar; 600 Graphen für die Bipartit-Belege) fand **0 Abweichungen**.
- **Kopierte Löser** (`tests/test_copied_solvers.py`): wortgleich mit dem Original (Vergleich der Dateien), dazu Gegenproben gegen Aufzählen auf kleinen Zufallsgraphen (Clique, kleinste Überdeckung, Reduktionsregeln mit Rücklift).
- **Prüfung vor der Anzeige:** `validation_errors` prüft jede belegte Antwort der Kette gegen die Brute-Force-Probe und jeden Beleg (`tests/test_evaluation.py`); abgebrochene Läufe zählen nur belegte Aussagen (jeder Zweig von `cover_answer` und `clique_answer` einzeln getestet).
- **Verdikte** als reine Funktionen, jede Zahl im Text und jede Schwelle an handgesetzten Werten (`tests/test_verdicts.py`).
- **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Presets:** vollständig, gültige Werte, erstes Preset gleich Standard, jedes Preset zeigt, was seine Hilfe verspricht (`tests/test_presets.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum, alle zugleich), Permalink mit Begrenzung und unlesbaren Werten, beide Tabs, Abbruchanzeige, Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben), Footer.
- **Browser:** Standardansicht, Preset „Nahe der Schwelle“ (Abbruchanzeige), beide Tabs durchgespielt; keine Konsolenmeldung.
- **Mutationsprüfung (Vollauf über `red_reduction.py`, `red_dpll.py` und `red_certificates.py`, 141 Stellen):** 140 gesichert (gefangen oder als äquivalent festgehalten), 1 Mutation läuft in eine Endlosschleife (Zeitüberschreitung, zählt nicht als gefangen). Der erste Lauf fand echte Lücken, die jetzt Tests haben: Bit-Zuordnung der Brute-Force-Probe (Belegung mit wahrer letzter Variable), Konfliktkanten innerhalb einer Klausel, Reihenfolge der Rückübersetzung bei widersprüchlicher Menge, aufsteigende Variablenliste, Zählformel der Held–Karp-Zugriffe bei n = 3, Farben der Breitensuche und isolierter letzter Knoten, Reihenfolge der Paarprüfung. Als äquivalent festgehalten sind 13 Stellen (`lit > 0` gegen `lit >= 0` bzw. `lit > -1` bei Literalen ungleich null, doppelte Zählung in der Variablenwahl, zusätzliche Belegungen in der Aufzählung, Schleifenglieder bei symmetrischen Graphen); der Zustand steht in `tests/mutation_state.json`. **Ausgenommen:** die drei kopierten Löser (eine Stichprobe über sie ließ 29 von 57 geprüften Mutanten überleben; ihre Tests liegen in den Ursprungs-Demos und wurden hier nicht nachgearbeitet) sowie `red_evaluation.py`, `red_scenario.py`, Auswertung und Darstellung (vom Mutationswerkzeug über die Orakel-Tests nicht erreicht; abgesichert durch Claims-, Verdikt- und Rauchtests). „Mutation sauber“ gilt daher nur für die drei genannten Module.

## Einordnung und Quellen (anhand der Quellen geprüft)

Reduktionen und NP-Vollständigkeit: Cook, *The complexity of theorem-proving procedures*, Proceedings of the 3rd ACM Symposium on Theory of Computing (1971), S. 151 bis 158 (Cook–Levin: Erfüllbarkeit ist NP-vollständig; Levin 1973 unabhängig); Karp, *Reducibility among combinatorial problems*, in: Miller und Thatcher (Hrsg.), Complexity of Computer Computations, Plenum 1972, S. 85 bis 103 (21 Probleme, darunter Clique und Knotenüberdeckung). DPLL: Davis, Logemann und Loveland, *A machine program for theorem-proving*, Communications of the ACM 5 (1962), S. 394 bis 397. Die Gallai-Identität α + τ = n wird in Vorlesungsunterlagen auf 1959 datiert; das Original wurde nicht nachgeschlagen. Die Standardkonstruktion „Dreieck je Klausel plus Konfliktkanten“ ist Lehrbuchwissen und hier selbst gebaut und getestet.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: zwei Tabs, drei Experimente und die Zertifikat-Messungen, Annahmentabelle, Formeln |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur für die Gegenprobe) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `red_certificates.py` | Prüfer und Zählformeln, 2-Färbung oder ungerader Kreis, Schubfach-Formeln |
| `red_clique.py` | wörtliche Kopie: größte Clique (Branch-and-Bound) aus max-clique-demo |
| `red_constants.py` | Regler-Grenzen, Rechengrenzen, Farben, Presets |
| `red_cover.py` | wörtliche Kopie: kleinste Knotenüberdeckung aus vertex-cover-demo |
| `red_dpll.py` | DPLL mit Knotenzähler |
| `red_evaluation.py` | Analyse der Kette, Antwortlogik bei Abbruch, Messreihen, Prüfung vor der Anzeige, Verdikte |
| `red_layout.py` | Fester Kopf (Stylesheet) |
| `red_mis_reduce.py` | wörtliche Kopie: Reduktionsregeln der unabhängigen Menge aus mis-local-search-demo |
| `red_pdf_export.py` | PDF-Bericht (fpdf2) |
| `red_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `red_reduction.py` | Die Kette: Formel, G_F, Komplement, Gallai, Rückübersetzung, Brute-Force-Probe |
| `red_scenario.py` | SplitMix64, Zufallsformeln, Zufallsgraphen |
| `red_visualization.py` | Plotly-Abbildungen: G_F mit Dreiecken und Konfliktkanten, Größe, Aufwand, Belege (Achsen gesperrt) |
| `tests/` | Mini-Formeln, Orakel, kopierte Löser, DPLL und Zertifikate, Verdikte, Claims, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Beweis von Cook–Levin** und alle weiteren Reduktionen (Hamiltonkreis → Rundreise gehört in ein Folgestück zur Approximation).
- **CDCL-SAT-Löser und Phasenübergang von Zufalls-3-SAT:** Gegenstand des Folgestücks „SAT in der Praxis“.
- **Kürzeste Nein-Beweise** (Resolution) und ein Beweis, dass es keine kurzen gibt: die Demo zählt nur die Baumgröße einer bestimmten Suche.
- **Untersuchung, warum die Reduktionsregeln auf G_F nicht greifen:** Befund ohne Erklärung.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
