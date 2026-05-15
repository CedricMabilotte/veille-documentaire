# Exploration Log

> Journal d'exploration des sources. Chaque fois qu'un agent (humain ou LLM)
> teste une nouvelle source, ajouter une entrée datée.

---

## 2026-05-15 — Probe initial (Phase 1)

**Contexte** : Démarrage de la veille sur la thématique communs/propriété d'usage/paysannerie.

**Méthode** : `curl + grep '\.pdf|\.epub|\.txt|\.doc'` pour compter les documents en HTML statique.

**Sites testés** : ~120 URLs en FR/EN/ES/DE/PT.

**Découvertes principales** :
- **Infokiosques.net** : seul site francophone vraiment scrapable, multi-milliers de PDFs accessibles via rubriques alphabétiques (rub5/A=290, rub7/C=273) et rubriques thématiques (rub22=236, rub24=124).
- **boell.de** : pépite institutionnelle DE/EN, pagination `?page=N` ultra-fiable, jusqu'à 60+ pages.
- **Sites JS-rendered (90% du corpus moderne)** : Persée, HAL search, OpenEdition, Cairn, MST, Via Campesina, Lundi.am, Reporterre, Atelier Paysan, theanarchistlibrary index, libcom search, crimethinc index, Portal Oaca, alasbarricadas, Anarkismo, etc. → invisibles au scraper actuel.
- **theanarchistlibrary.org expose un OPDS feed** : `https://theanarchistlibrary.org/opds` (XML standardisé) — débloque ~10 000 textes anarchistes multilingues sans JS.
- **APIs JSON publiques disponibles** : Archive.org (`advancedsearch.php`), HAL Science (`api.archives-ouvertes.fr`), OpenEdition Books, DOAB, FAO documents.

**Décisions** :
- Garder Infokiosques comme base FR.
- Implémenter parser OPDS pour theanarchistlibrary.
- Implémenter parsers API Archive.org et HAL.
- Implémenter crawl 2-niveaux pour libcom, crimethinc, sproutdistro, cras31, federation-anarchiste, portaloaca.
- Différer Playwright (gros effort, faible ROI immédiat).

**Documents associés** :
- `docs-meta/CATALOGUE-SOURCES.md` — catalogue complet
- `docs-meta/sources-veille-template.yml` — template multilingue réutilisable

---

## 2026-05-15 — Phase 2 : Implémentation modulaire (en cours)

**Objectif** : Architecturer `watch.py` pour supporter plusieurs types de parsers (html, deep_html, opds, archive_org, hal) via dispatch `type:` dans `config/sources.yml`.

**Livrables attendus** :
- `scripts/parsers/__init__.py` — registre des parsers
- `scripts/parsers/html_static.py` — extract direct (déjà existant, à modulariser)
- `scripts/parsers/deep_html.py` — crawl 2-niveaux
- `scripts/parsers/opds.py` — feed OPDS
- `scripts/parsers/archive_org.py` — API JSON Archive.org
- `scripts/parsers/hal.py` — API JSON HAL Science
- Refactor `watch.py` pour dispatcher selon `source.type`
- Mise à jour `SOURCES-REGISTRY.yml` au fil de l'eau

---

<!-- AJOUTER ICI les nouvelles explorations -->
