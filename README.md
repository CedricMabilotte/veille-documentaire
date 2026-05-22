# BIBLIO — bibliothèque de veille documentaire

Agent de veille automatisé sur les **communs fonciers, la propriété d'usage,
la libération des terres et les paysanneries**. Il scrute des sources web,
note la pertinence des documents avec Claude, télécharge et analyse les
plus pertinents, puis publie une bibliothèque consultable en ligne.

Site public : <https://biblio.actitude.org>

## Architecture du pipeline

Le pipeline tourne via GitHub Actions (`.github/workflows/watch.yml`) et
s'articule en six étages :

### 1. Veille — `scripts/watch.py`

Orchestrateur principal. Pour chaque source de `config/sources.yml` :

- **Throttle** (`throttle.py`) — décide s'il faut interroger la source
  maintenant (TTL adaptatif, cooldown sur erreurs, robots.txt, politesse).
- **Parsers** (`scripts/parsers/`) — dispatchés selon le `type` de la
  source : `html`, `deep_html` (crawl 2 niveaux), `opds`, `archive_org`,
  `hal`, `rss`, `playwright` (sites JS).
- **Scoring sur titre** — Claude note chaque document de 0 à 10 sur le
  seul titre + contexte (`score_initial`), et le classe par typologie
  (`doc_type`) et tag `recit_de_lutte`.
- **Téléchargement + validation** (`pdf_processor.py`) — détection des
  faux PDF, bypass anti-bot, repli Playwright.

### 2. Synopsis — `scripts/synopsis_enricher.py`

Pour chaque PDF téléchargé au-dessus du seuil : extraction du texte
(PyMuPDF) puis appel à Claude pour produire un **synopsis enrichi** :
résumé, citations littérales (re-vérifiées dans le PDF, champ `verified`),
mots-clés réellement présents, **score post-lecture** (`score_final`),
acteurs, controverse, angle journalistique et formule « en clair ».

### 3. Bulles — `bulles/<id>.json`

Pour les documents les mieux notés, une « bulle de publication »
éditorialisée (titre d'accroche, teaser, abstract, citations phares).

### 4. Métadonnées & pérennité

- `doc_metadata.py` — extrait `doc_date`, `lang`, `editeur`, `doi`,
  `isbn`, `hal_id` à partir des API (HAL, Archive.org, RSS) et du PDF.
- `link_check.py` — vérifie la validité de chaque lien source
  (`link_status`) et archive une copie pérenne sur web.archive.org
  (`archive_url`).
- `dedup.py` — détecte les doublons (binaires et textuels) ; le champ
  `versions` du catalog relie les éditions/traductions d'un même texte.

### 5. Catalogue & site — `synopsis/catalog.json` → `site/`

`update_synopsis_catalog` agrège tous les runs dans `catalog.json`
(catalogue complet, jamais filtré). `publish_site` génère ensuite :

- les fiches HTML pré-rendues (`site/fiches/<id>.html`, og:image, JSON-LD) ;
- les cartes sociales et citation-cards (`social_cards.py`, Pillow) ;
- les flux RSS conformes (`feed.xml`, `feeds/scoops.xml`, feeds par concept) ;
- le sitemap, les dossiers éditoriaux (`dossiers.json`), le document de la
  semaine (`featured.json`) et l'état du corpus (`corpus_stats.json`).

Seuls les documents dont le **score effectif** (`score_final` ou, à défaut,
`score_initial`) atteint le seuil de publication sont exposés au RSS, au
sitemap et aux fiches pré-rendues. `catalog.json` reste exhaustif pour la
transparence.

### 6. Exports & découverte

- `export_bibtex.py` — exporte le corpus en BibTeX / RIS / CSL JSON
  (Zotero), avec DOI/ISBN/HAL.
- `discovery_*.py` — boucle de découverte de nouvelles sources
  (bibliographies, notes de bas de page, OpenAlex, Semantic Scholar,
  Mastodon, suggestions LLM, angles morts).

## Structure du dépôt

```
config/sources.yml          ← sources surveillées, mots-clés, seuil, orientation
config/concepts.yml         ← ontologie thématique + dossiers éditoriaux
scripts/watch.py            ← orchestrateur principal
scripts/parsers/            ← parsers pluggables par type de source
scripts/synopsis_enricher.py← synopsis enrichi via Claude
scripts/doc_metadata.py     ← extraction métadonnées bibliographiques
scripts/link_check.py       ← vérification + archivage des liens
scripts/social_cards.py     ← cartes de partage Open Graph (Pillow)
scripts/corpus_stats.py     ← état du corpus & transparence des biais
scripts/editorial.py        ← dossiers éditoriaux + document de la semaine
docs/                       ← PDF téléchargés
synopsis/catalog.json       ← catalogue agrégé multi-runs
bulles/                     ← bulles de publication éditoriales
site/                       ← site statique publié sur GitHub Pages
exports/                    ← exports BibTeX / RIS / CSL
reports/                    ← rapports JSON + Markdown de chaque run
.github/workflows/watch.yml ← workflow GitHub Actions
```

## Démarrage

1. Éditer `config/sources.yml` (URLs, mots-clés, seuil) et
   `config/concepts.yml` (ontologie, dossiers éditoriaux).
2. Renseigner les secrets GitHub : `CLAUDE_CODE_OAUTH_TOKEN`,
   `RCLONE_CONFIG_B64`, `BIBLIO_PUBLISH_TOKEN`.
3. Onglet **Actions** → « Veille documentaire » → *Run workflow*.

## Limites connues

- **Biais du corpus** : majoritairement francophone et de sources
  militantes ; les corpus académiques, institutionnels et du Sud global
  sont sous-représentés. `corpus_stats.json` quantifie ces biais.
- **Notation par un modèle** : les scores et synopsis sont générés par
  Claude. Les citations sont re-vérifiées dans le PDF mais le résumé et le
  score restent une lecture automatisée, à recouper.
- **Métadonnées imparfaites** : `doc_date`, `editeur` et `lang` ne sont
  pas toujours déterminables ; les champs restent vides plutôt que
  devinés. Un auteur absent de la source n'est **jamais** inféré
  (anonymat respecté).
- **Liens fragiles** : les sites militants sont instables. `link_check.py`
  signale les liens morts et conserve une copie Wayback, sans garantie.
- **Couverture** : seules les sources web accessibles sont veillées ; les
  corpus papier, oraux et hors-ligne sont structurellement absents.

## Licence

Ce projet est distribué sous **Peer Production License (PPL)**, une
licence à réciprocité « copyfarleft » : libre usage, partage et adaptation
pour les collectifs, coopératives de travail et personnes ; usage
commercial réservé aux structures où la valeur produite revient aux
travailleur·ses. Voir le fichier [`LICENSE`](LICENSE). Titulaire :
actitude.org.
