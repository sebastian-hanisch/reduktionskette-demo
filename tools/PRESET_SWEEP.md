# Preset-Abstimmung (2026-10-21)

Jedes Preset wurde mit `red_evaluation.analyse` gerechnet; die Spalten sind dieselben Zahlen, die die App zeigt (Einzelinstanzen, Seed je Preset). Gegen die Hilfetexte in `red_constants.PRESET_HELP` geprüft; `tests/test_presets.py` (`test_presets_show_what_their_help_promises`) und `tests/test_claims.py` (`test_claim_presets_are_single_instances_with_these_values`) halten die Aussagen fest.

| Preset | n | m | Seed | Budget | erfüllbar | DPLL | Überdeckung (Knoten, Abbruch) | Clique (Knoten, Abbruch) | Kern |
|---|---|---|---|---|---|---|---|---|---|
| Standardfall (Voreinstellung) | 8 | 12 | 35 | 10.000 | ja | 6 | 386, nein | 1, nein | 0 % |
| Lehrbeispiel (3 Klauseln) | 3 | 3 | 1 | 10.000 | ja | 3 | 5, nein | 1, nein | 0 % |
| Unerfüllbar (alle Belegungen verboten) | 3 | 18 | 3 | 10.000 | nein | 7 | 959, nein | 83, nein | 100 % |
| Nahe der Schwelle (m/n = 4) | 7 | 28 | 7 | 10.000 | nein | 7 | 10.001, **ja** | 10.001, **ja** | 100 % |
| Größte Formel (Budget reicht nicht) | 12 | 30 | 11 | 100.000 | ja | 6 | 100.001, **ja** | 44.390, nein | 100 % |

Hinweise: Beim Preset „Größte Formel“ bricht nur die Überdeckungssuche ab, die Cliquensuche kommt durch; der Hilfetext sagt das. Bei „Nahe der Schwelle“ ist die Formel unerfüllbar und die DPLL-Suche braucht 7 Knoten, die Graphlöser brechen beide ab: das Preset zeigt den Unterschied zwischen Formel und Graph in einer Einzelinstanz, die Messreihe (README, Befunde) zeigt ihn über fünf feste Formeln je Größe.
