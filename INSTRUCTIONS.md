# Instructions — biblio

> Document d'orientation interne du projet. Une session fraîche le lit avant
> de toucher quoi que ce soit. Le `README.md` est la vitrine éditoriale
> publique (sans vocabulaire technique) ; `DEPLOIEMENT.md` couvre la mise en
> ligne ; ce fichier-ci décrit le projet pour qui le maintient.

## Statut

```
projet         : biblio — veille documentaire sur les communs, la propriété
                 d'usage, la libération des terres et les paysanneries
nature         : pipeline de veille automatisé (Python) + site statique publié
phase          : en production — veille active, site en ligne
agent_porteur  : @ced
site public    : https://biblio.actitude.org
dépôt source   : CedricMabilotte/veille-documentaire (privé)
dépôt publié   : CedricMabilotte/biblio-actitude-org (public, GitHub Pages)
statut         : actif
```

## biblio en quelques phrases

biblio collecte en continu des ouvrages en accès libre sur les communs
fonciers et les alternatives à la propriété privée, les évalue, en produit des
fiches documentaires, et publie le tout sous forme d'un site statique
consultable. C'est un pipeline Python (`scripts/`) déclenché par une GitHub
Action ; il génère le dossier `site/`, qui est ensuite publié sur le dépôt
public. Le catalogue (`synopsis/catalog.json`) reste exhaustif ; seuls les
documents dont le score effectif atteint le seuil sont exposés au public.

## Rôle attendu de Claude

Maintenir et faire évoluer le pipeline, le site et la ligne éditoriale. Sur ce
projet, Claude corrige des bugs, renforce des garde-fous, affine l'interface et
l'éditorial — toujours par étapes lisibles et vérifiées. Les refontes
structurelles (changement de seuil, d'ontologie, d'architecture) se décident
avec Ced, pas seul. Toute affirmation publiée doit rester sourçable.

## Architecture du pipeline

Le pipeline s'articule en étages, orchestrés par `scripts/watch.py` :

1. **Veille** — pour chaque source de `config/sources.yml` : throttle adaptatif,
   parsers par type (`scripts/parsers/`), scoring sur titre (`score_initial`),
   téléchargement et validation des PDF.
2. **Synopsis** — `synopsis_enricher.py` extrait le texte des PDF retenus et
   produit un synopsis enrichi : résumé, citations vérifiées dans le PDF,
   score post-lecture (`score_final`), acteurs, controverse.
3. **Bulles** — pour les documents les mieux notés, une bulle éditoriale
   (`bulles/<id>.json`).
4. **Métadonnées & pérennité** — `doc_metadata.py` (date, langue, éditeur, DOI,
   ISBN), `link_check.py` (validité + archivage Wayback), `dedup.py` (doublons).
5. **Catalogue & site** — `catalog.json` agrège tous les runs ; `publish_site`
   génère fiches pré-rendues, cartes sociales, flux RSS, sitemap, dossiers.
6. **Exports & découverte** — `export_bibtex.py` (BibTeX/RIS/CSL) et les
   `discovery_*.py` (découverte de nouvelles sources).

Seuil de publication : `PUBLISH_THRESHOLD = 4` dans `watch.py` (via `os.getenv`,
défaut `4` — tranché session #20, cf. `etat-projet-biblio.md` §4.1) — un document
n'est exposé (RSS, sitemap, fiche pré-rendue) que si son score effectif
(`score_final`, sinon `score_initial`) l'atteint, et s'il s'agit d'un ouvrage
en format ouvert (PDF, EPUB, TXT, ODT), et s'il n'est pas dans `config/exclusions.yml`.

Exécution : `watch.yml` (cron un jour sur deux à 03:00 UTC, budget
`WATCH_BUDGET_MIN`) ; `rebuild-site.yml` régénère le site sans veille ;
`publish-only.yml` pousse `site/` vers le repo public. Détails : `DEPLOIEMENT.md`.

## Méthode de travail & conventions

- **Langue** : français, tutoiement chaleureux. Prose claire, affirmations
  factuelles sourcées.
- **Règle d'accents** (convention des projets de Ced) : *technique sans accent*
  — noms de fichiers, clés, statuts, identifiants ; *narratif avec accent* —
  corps de texte, documentation. Le prénom s'écrit **« Cedric »**, jamais
  accentué, y compris en signature.
- **Nommage daté** : les fichiers de travail datés suivent `AAAA-MM-JJ_objet.md`
  (rapports, rapports de découverte le font déjà).
- **Trois documents, trois rôles** : `README.md` = vitrine publique éditoriale ;
  `INSTRUCTIONS.md` (ce fichier) = orientation technique interne ;
  `DEPLOIEMENT.md` = procédure de mise en ligne.
- **Par étapes lisibles** : commits cohérents et atomiques ; travail inachevé
  jamais laissé orphelin dans l'arbre de travail.

## Garde-fous

- **`python3 scripts/audit_site.py`** — contrôle de cohérence du site publié
  (orphelins, sitemap, langue JSON-LD, licence). Sortie 0 = OK. Tourne en fin
  de `watch.py` et à l'étape 5 de la routine-fin.
- **Aucun secret dans le dépôt** — les credentials vivent dans
  `~/.claude/credentials/`, jamais en dur dans le code.
- **Le dépôt public ne contient que `site/`** — pas les PDF, pas les scripts
  (voir `DEPLOIEMENT.md`, section Sécurité).
- **Forcer un re-scan complet** : supprimer `synopsis/throttle_state.json`.
- **Clôture de session** : dérouler `routine-fin.md` avant de fermer.

## Agents transverses & accès

biblio dépend du domaine et de la messagerie d'**actitude.org**, gérés en
dehors de ce dépôt, dans le workspace **para**
(`~/Documents/Ced_Cabinet/Activities/agents/`).

- **@neo** — admin numérique : domaine, DNS, messagerie Gandi, déploiement,
  credentials. Pour toute demande, déposer un fichier dans
  `agents/neo/inbox/YYYY-MM-DD_biblio-<besoin>.md` (workspace para), ou agir
  à sa place en suivant son protocole.
- **Registre des accès** : `resources/shared/acces-connecteurs.md` (para) —
  source unique de vérité sur les API et credentials. **Lecture / audit
  libre ; écriture (DNS, envoi, déploiement, suppression) → confirmation
  explicite de Ced.**

## Relation à actitude.org

biblio publie sur le sous-domaine `biblio.actitude.org`. Le branchement DNS et
la messagerie (`contact@actitude.org`) relèvent de @neo. La publication
elle-même est automatique : voir `DEPLOIEMENT.md`.
