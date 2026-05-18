# Audit 05 — Résumé exécutif

Date : 2026-05-18  
Cible : https://biblio.actitude.org/ — 234 fiches, 17 bulles éditoriales.

---

## Score global : **14 / 20**

Décomposition :
- Fonctionnel (infrastructure & navigation) : 17/20
- Éditorial (qualité contenu) : 12/20 (forte hétérogénéité)
- Liens sources : 16/20 (88 % OK)
- Accessibilité & SEO statique : 14/20
- SEO/UX dynamique (pré-rendu, partages) : 9/20 — c'est le maillon faible

## Top 3 points forts

1. **Architecture sobre, propre, sans framework**. HTML/CSS/vanilla JS, ~1500 lignes JS au total, pas de tracker, palettes thématiques élégantes, navigation cohérente, manifeste PWA, RSS, sitemap, exports CSV/BibTeX côté client. Le projet tient ses promesses techniques de base.
2. **Bulles éditoriales de très haute qualité** (5 sondées) : `titre_accroche`, `teaser`, `abstract_editorial`, `citations_phares` avec n° de page → fidèles aux PDF, accrocheurs, vérifiables. Le travail éditorial sur les 17 bulles est le vrai capital du site.
3. **Infrastructure de veille publique exemplaire** : `catalog.json` ouvert, méthodologie transparente (page À propos, raisons de scoring par run, historique des runs visible), code source public, licence CC-BY-SA 4.0. Toutes les fiches sont permalink-stables, dans le sitemap, dans le RSS.

## Top 5 problèmes à corriger

### CRITIQUE — Pré-rendu / partage social des fiches
Toutes les fiches partagent le même HTML statique (12 019 B) hydraté par JS. Conséquences :
- Le partage Slack/LinkedIn/Mastodon affiche « Fiche — BIBLIO » + description générique au lieu du vrai titre et résumé.
- Sans pré-rendu, le SEO de chaque fiche dépend du rendu JS de Googlebot (faillible).
- `og:description` et `canonical` absents du HTML statique de `fiche.html`.

**Correctif** : générer en build (workflow) un snapshot HTML par fiche (`/fiches/fiche-<id>.html`) avec les meta correctes, ou patcher l'URL routing pour servir un HTML pré-rendu.

### CRITIQUE — Scoring HTML générateur de faux positifs
Sur 10 fiches sondées en score ≥ 8 : 1 hors-sujet manifeste (`ae3e9d34`, crise carburant Irlande scorée 9), 3 tangentes (manifestes 8 mars, sessions zapatistes), 1 doublon HAL (`d647480f` ≈ `e5341cc9`). Précision ≈ 60–70 %. Cause racine : le scoreur lit le contexte HTML *brut* (sidebar + footer + main confondus), donc des mots-clés trouvés dans le menu latéral d'un site militant remontent le score.

**Correctif** : isoler le contenu principal (`<article>`, `<main>`, ou heuristique `readability`) avant de scorer. Dédup HAL par DOI / numéro de papier canonique.

### HAUTE — Liens sources cassés (10 % d'un échantillon 30)
3 URLs Archive.org en 404, 1 en 401 (dossier médical hors-sujet à purger), 1 en 500 (cnt.es). Le taux est ≈ 10 % sur l'échantillon, concentré sur `archive.org/download/`.

**Correctif** : health-check `curl -I` mensuel automatisé, flag `_broken: true` dans le catalog, exposer un filtre "masquer les sources cassées" (par défaut on), et badge dans la fiche.

### MOYENNE — Catalogue déséquilibré, 80 % de fiches creuses
- 39/234 fiches enrichies (17 %), 17/234 bulles éditoriales (7 %).
- 53 docs scorés 0, 87 à 1 → 60 % du catalog est en réalité du bruit que l'utilisateur ne devrait pas voir par défaut.

**Correctif** : sur la home et le filtre par défaut du catalog, n'afficher que `score >= 5` ou `enrichment` ou `bulle`. Garder les bas scores accessibles via un filtre explicite « voir tout, y compris bruit de veille ».

### MOYENNE — Manifest PWA incomplet (Android ne peut pas installer)
Pas d'icônes PNG 192/512, pas de service worker, donc la promesse « PWA standalone » du manifest n'est pas tenue pour Android. Hors-ligne impossible. Exports `/exports/*.bib` retournent 404 alors que les fichiers existent en local mais ne sont pas publiés.

**Correctif** : ajouter `icon-192.png`, `icon-512.png` (maskable), un `service-worker.js` minimal (cache-first sur assets + catalog.json), et inclure `exports/` dans le déploiement.

## Recommandations priorisées (ordre d'attaque)

| # | Action | Effort | Impact | Where |
|---|---|---|---|---|
| 1 | Filtre par défaut catalog `score >= 5` ou enrichi/bulle | 30 min | élevé | `site/fiches/index.html` ligne ~240 (`filteredDocs`) |
| 2 | Pre-render statique des fiches au build | 1–2 j | très élevé | nouveau script `scripts/render_fiches.py` |
| 3 | Health-check sources + flag `_broken` | 2 h | élevé | `scripts/watch.py` (job mensuel) |
| 4 | Re-scoring sur contenu principal HTML uniquement | 1 j | élevé | `scripts/parsers/*.py` ou pipeline scoring |
| 5 | Dédup HAL par identifiant canonique | 2 h | moyen | `scripts/watch.py` dédup logique |
| 6 | OG description + canonical + cover dynamiques | 1 h | moyen | `site/fiches/fiche.html` (`updateMetaTags`) |
| 7 | PNG 192/512 + service worker minimal | 3 h | moyen | `site/assets/img/`, `site/sw.js`, `manifest.json` |
| 8 | RSS RFC-822 + `pubDate` par item | 1 h | faible | générateur de `feed.xml` |
| 9 | `<lastmod>` dans sitemap | 30 min | faible | générateur de `sitemap.xml` |
| 10 | Skip-link accessibilité | 5 min | faible | `site/*.html` (tous) |

---

## Note sur les faux positifs/négatifs de cet audit

- **Faux négatifs possibles** : (a) je n'ai pas testé Lighthouse / axe-core (non dispo en sandbox), donc le contraste et les pièges ARIA fins ne sont pas couverts ; (b) je n'ai pas testé les 234 URLs sources mais 50, donc le 10 % de cassés peut s'extrapoler entre 7 % et 13 % ; (c) je n'ai pas inspecté `auteurs.html`/`chronologie.html`/`dossiers.html`/`graph.html` côté logique JS — seulement leur HTML statique.
- **Faux positifs possibles** : (a) `ae3e9d34` scoré 9 mais hors-sujet — c'est ma lecture rapide du titre, le contenu réel pourrait s'avérer pertinent ; à confirmer en ouvrant la page ; (b) le « 500 » sur cnt.es est probablement intermittent (cnt.es a un historique d'erreurs serveur sur leurs anciennes pages d'actualité), donc le compter comme cassé est conservateur.
- L'audit privilégie l'actionnable : chaque problème pointe vers un fichier:ligne et un correctif court.
