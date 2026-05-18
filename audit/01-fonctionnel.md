# Audit 01 — Fonctionnel

Date : 2026-05-18  
Cible : https://biblio.actitude.org/ (live) + repli sur `site/` local.  
Méthode : `curl` HEAD/GET + lecture statique du code JS, validation XML/JSON via `xml.etree` et `json` (Python 3).

---

## 1. Pages principales (HTTP statut + taille + Content-Type)

| URL | Code | Taille | Content-Type | Verdict |
|---|---|---|---|---|
| `/` | 200 | 14 334 B | `text/html; charset=utf-8` | OK |
| `/fiches/` | 200 | 22 985 B | `text/html; charset=utf-8` | OK |
| `/apropos.html` | 200 | 12 318 B | `text/html; charset=utf-8` | OK |
| `/auteurs.html` | 200 | 9 433 B | `text/html; charset=utf-8` | OK |
| `/chronologie.html` | 200 | 8 694 B | `text/html; charset=utf-8` | OK |
| `/dossiers.html` | 200 | 8 927 B | `text/html; charset=utf-8` | OK |
| `/graph.html` | 200 | 16 096 B | `text/html; charset=utf-8` | OK (publié live, absent du repo source) |
| `/feed.xml` | 200 | 17 334 B | `application/xml` | OK |
| `/sitemap.xml` | 200 | 19 739 B | `application/xml` | OK |
| `/data/catalog.json` | 200 | 506 847 B | `application/json` | OK |
| `/manifest.json` | 200 | 607 B | `application/json` | OK |
| `/robots.txt` | 200 | 73 B | `text/plain` | OK |
| `/assets/css/style.css` | 200 | 36 344 B | `text/css` | OK |
| `/assets/js/app.js` | 200 | 14 414 B | `application/javascript` | OK |

**Constat clé** : `site/graph.html` est publié sur le live mais absent du repo source `site/`. Soit il est généré par le workflow, soit il y a une dérive entre le code committé et le déploiement → à formaliser dans le pipeline.

## 2. Permaliens de fiches (10 IDs random)

Tirage `random.seed(42)` sur `site/data/catalog.json`. Tous renvoient HTTP 200 et le shell `fiche.html` (12 019 B) — qui est ensuite hydraté côté client via `loadCatalog()` puis `renderFiche()`.

| ID | HTTP | Taille |
|---|---|---|
| 52b5643d | 200 | 12 019 |
| 7a339627 | 200 | 12 019 |
| e3281a23 | 200 | 12 019 |
| 61470e2f | 200 | 12 019 |
| 4839c163 | 200 | 12 019 |
| 9bdc8c24 | 200 | 12 019 |
| e7de54e2 | 200 | 12 019 |
| 1ae61acb | 200 | 12 019 |
| 576f28a7 | 200 | 12 019 |
| 0507267c | 200 | 12 019 |

**Limite SEO importante** : le contenu de fiche est rendu côté client (SPA-style). Les crawlers qui n'exécutent pas JS voient une page vide « Chargement de la fiche… ». Googlebot rendu JS gère ça, mais les bots RSS / preview de chat (Slack, LinkedIn) ne récupèrent pas les meta dynamiques mises à jour par `updateMetaTags()`. Recommandation : pré-render des fiches en build (snapshot HTML statique par `id`).

Vérification : tous les `id` testés existent bien dans `catalog.json` → pas d'erreur "Aucune fiche…" à l'hydratation.

## 3. Recherche full-text

Code lu : `site/assets/js/search.js`.

- `buildSearchBlob()` agrège : `id`, `filename`, `source`, `pdf_title`, `pdf_author`, `enrichment.summary`, `matched_keywords`, citations (`quote` + `why_relevant`), `bulle_data` (titre, teaser, abstract, catégorisation, citations phares) et la `raison` de chaque run.
- Normalisation correcte : minuscules + suppression diacritiques (`NFD` + suppression marks combinants).
- Recherche AND multi-termes (`terms.every(...)`).
- Cache `d._blob` paresseux : OK.

**Bug léger / non bloquant** dans la regex `normalize()` : `.replace(/[̀-ͯ]/g, '')` utilise une range U+0300–U+036F encodée littéralement avec caractères combinants visibles dans le source. Cela fonctionne mais peut casser à la copie/édition. Préférer `/[̀-ͯ]/g`.  
Fichier : `site/assets/js/search.js:10`.

Aucun autre bug logique détecté. Pas d'index inversé : le scan est linéaire sur 234 docs — performance acceptable, mais le `data/fulltext_index.json` (810 KB, structure `{terms, tf, stats}`) chargé inutilement par personne (aucune référence dans les pages HTML). À supprimer ou à brancher.

## 4. Filtres du catalogue

Code lu : `site/fiches/index.html` (script inline).

Filtres implémentés et vérifiés :

| Filtre | Type | Implémenté | Persisté URL | Remarque |
|---|---|---|---|---|
| `q` | recherche texte | OUI | OUI (`?q=`) | OK |
| `score_min` / `score_max` | range 0–10 | OUI | OUI | UX bonne (val live) |
| `sources[]` | cases à cocher | OUI | NON | absence d'URL state → non partageable |
| `formats[]` | cases à cocher | OUI | NON | idem |
| `bulle` | bool | OUI | OUI | OK |
| `downloaded` | bool | OUI | NON | non partageable |
| `enriched` | bool | OUI | NON | non partageable |
| `sort` (5 options) | select | OUI | OUI | OK |
| Vues grille / étagère | toggle | OUI | NON (mais localStorage) | OK |

**Action recommandée** : router `sources`, `formats`, `downloaded`, `enriched` dans l'URL pour permettre des permaliens de listes filtrées (utile pour partage et SEO).

## 5. Exports

Local : `exports/catalog.bib` (199 lignes), `exports/catalog.csl.json` (408 lignes), `exports/catalog.ris` (271 lignes).  
Live :

| URL | Code |
|---|---|
| `/exports/catalog.bib` | **404** |
| `/exports/catalog.ris` | **404** |
| `/exports/catalog.json` | 404 (n'existe pas, le fichier est `catalog.csl.json`) |
| `/exports/` | 404 |

**Problème** : les exports ne sont **pas publiés**. Or le catalogue `/fiches/` propose des boutons `Exporter CSV` et `Exporter BibTeX` qui regénèrent côté client → cela évite le 404 dans l'usage, mais les fichiers `exports/*` sont morts (le dossier `exports/` n'est apparemment pas copié dans le déploiement). Choix à faire : soit retirer ce dossier du repo, soit l'inclure dans la publication (`exports/` → `site/exports/`).

Par ailleurs `catalog.bib` est très pauvre (titres = noms de fichiers comme `eskum-3-in-1-hil.pdf`). À régénérer avec `bulle_data.titre_accroche` quand dispo, sinon `meta.pdf_title`, sinon filename normalisé.

## 6. RSS — validation et liens

`feed.xml` :
- XML bien formé (parsé par `xml.etree.ElementTree` sans erreur).
- 27 `<item>` (> 1 ✅).
- Chaque item a `<link>`, `<guid>`, `<title>`, `<description>`, `<category>`.
- Toutes les `<link>` pointent bien vers `https://biblio.actitude.org/fiches/fiche.html?id=<id>` cohérent avec la structure URL.

**Petits défauts** :
- `lastBuildDate` au format `2026-05-17_23-39` — RSS 2.0 attend RFC-822 (`Mon, 17 May 2026 23:39:00 +0000`). Les agrégateurs stricts peuvent ignorer la date.  
  Fichier : `site/feed.xml:8`.
- Pas de `<pubDate>` par item — l'ordre d'arrivée est implicite. Conséquence : pas de "nouveaux items" reconnaissables côté lecteur RSS.
- Manque de namespace `xmlns:atom` au niveau `<rss>` alors que `<atom:link>` est utilisé → certains parseurs râlent.  
  Fichier : `site/feed.xml:2,9`.

## Résumé fonctionnel

- 100 % des URLs structurelles répondent 200, sitemap (241 URLs, dont 234 fiches) complet.
- Permaliens de fiches OK fonctionnellement, mais SEO/preview cassés sans pré-rendu.
- Recherche, filtres, vues, exports CSV/BibTeX côté client : implémentés, propres.
- 4 chantiers : (a) pré-rendu HTML des fiches ; (b) publication du dossier `exports/` ; (c) flux RSS aux normes RFC-822 + `pubDate` ; (d) `fulltext_index.json` orphelin à brancher ou supprimer ; (e) router quelques filtres dans l'URL.
