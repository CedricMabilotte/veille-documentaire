# Audit 04 — Accessibilité & SEO

Date : 2026-05-18  
Méthode : lecture statique des HTML (`grep`/regex), validation XML (sitemap, feed) et JSON (manifest), test `curl` sur ressources.

---

## 1. Meta tags par page (HTML statique)

| Page | `<html lang>` | `description` | `og:title` | `og:description` | `og:image` | `canonical` |
|---|---|---|---|---|---|---|
| `index.html` | fr | OUI | OUI | OUI | OUI | OUI |
| `fiches/index.html` | fr | OUI | OUI | OUI | OUI | OUI |
| `fiches/fiche.html` | fr | OUI | OUI | **NON** | OUI | **NON** |
| `apropos.html` | fr | OUI | OUI | OUI | OUI | OUI |
| `auteurs.html` | fr | OUI | OUI | OUI | OUI | OUI |
| `chronologie.html` | fr | OUI | OUI | OUI | OUI | OUI |
| `dossiers.html` | fr | OUI | OUI | OUI | OUI | OUI |
| `graph.html` (live) | fr | OUI | OUI | OUI | OUI | OUI |

### Problèmes Open Graph / SEO

1. **`fiche.html` n'a pas de `<meta name="og:description">`** dans le statique → tout partage de fiche sur réseau social affiche la description par défaut « Fiche documentaire BIBLIO — analyse, citations, contexte. ». `updateMetaTags()` patche `og:title` dynamiquement mais oublie `og:description` ; même si elle le patchait, les crawlers non-JS (Facebook, LinkedIn, Slack hors Twitter X) ne verraient rien.  
   Fichier : `site/fiches/fiche.html:9-13` + `site/fiches/fiche.html:131-138` (`updateMetaTags`).
2. **Pas de `<link rel="canonical">`** sur `fiche.html` → risque de duplicate content si l'URL est partagée avec UTM. À ajouter dynamiquement et idéalement aussi en pré-rendu.
3. **OG image générique** sur toutes les fiches (`og-default.svg`) → manque d'identification visuelle. Quand une `cover` existe (`assets/covers/<id>.png`), elle devrait être utilisée. À patcher dans `updateMetaTags()` ET pré-rendre.

## 2. Attributs `alt` sur les images

Audit statique sur les 7 pages HTML : **15 images au total, 0 sans `alt`** ✅.

Bémol : la plupart des `alt` sont vides (`alt=""`), ce qui est correct pour les logos décoratifs (signaler comme décoratifs), mais perdure pour les couvertures de fiche générées dynamiquement. Vérifié dans `fiche.html:163` :

```js
<img src="${escape(cover)}" alt="Couverture de ${escape(title)}" onerror="…">
```

`alt` correctement défini avec le titre du document → ✅.

## 3. Langue, charset, viewport

- `<html lang="fr">` : présent sur toutes les pages testées ✅.
- `<meta charset="utf-8">` : présent partout ✅.
- `<meta name="viewport" content="width=device-width, initial-scale=1">` : présent partout ✅.

## 4. `robots.txt`

```
User-agent: *
Allow: /
Sitemap: https://biblio.actitude.org/sitemap.xml
```

- Indexation ouverte ✅.
- `Sitemap` déclaré ✅.

**Recommandation** : `Allow: /` est implicite ; on peut ajouter explicitement un `Disallow: /data/` ou non, selon la politique. Garder `/data/catalog.json` indexable est OK si on veut que les chercheurs trouvent le dump (c'est même un signal d'ouverture).

## 5. `sitemap.xml`

- 241 URLs : 7 pages principales + **234 fiches** (1 par doc).
- Toutes les fiches du catalog y sont (vérifié programmatiquement).
- Bien formé XML ✅.

**Manques** :
- Pas de `<lastmod>` → Google ne sait pas qui a changé. Ajouter `<lastmod>` à partir de `latest_run` (format ISO 8601).
- Pas de `<priority>` ni `<changefreq>` (acceptable, Google les ignore).

## 6. Manifest PWA (`manifest.json`)

```json
{
  "name": "BIBLIO — Bibliothèque documentaire ouverte",
  "short_name": "BIBLIO",
  "description": "…",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#f7f2e7",
  "theme_color": "#a44a2c",
  "lang": "fr",
  "icons": [
    { "src": "assets/img/favicon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any" },
    { "src": "assets/img/logo.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any" }
  ]
}
```

- Champs requis présents (`name`, `start_url`, `icons`) ✅.
- `theme_color`, `background_color`, `lang` ✅.

**Manques techniques** :
- Pas d'icône **PNG** 192×192 ni 512×512 → Android refuse d'installer la PWA sur la home screen (il exige au moins une PNG 192). Les SVG suffisent pour iOS Safari mais pas pour la majorité Android.  
  Action : ajouter `assets/img/icon-192.png` + `icon-512.png` avec `purpose: "any maskable"`.
- Pas de `service-worker.js` (vérifié absent : pas d'enregistrement `navigator.serviceWorker.register` dans `app.js`) → la PWA ne fonctionne pas offline. À mettre en cohérence avec la promesse « PWA / standalone ».

## 7. Accessibilité — autres points

Lecture statique :
- Skip link vers `#main` : **absent**. Recommandation : ajouter `<a class="skip-link" href="#main">Aller au contenu</a>` en tout début de `<body>`.
- `aria-label`, `role`, `aria-live` correctement utilisés sur header, nav, hero, sections principales et zones dynamiques (`#featured-grid`, `#result-count`, `#catalog-grid`) ✅.
- Boutons `theme-toggle`, `palette-toggle`, `menu-toggle` ont des `aria-label` et `aria-expanded` (vérifié `app.js:118-121`).
- Raccourcis clavier `/` (recherche), `g`/`e` (grille/étagère) : signalés via `title` mais pas dans une zone d'aide globale. Ajouter une page ou modal raccourcis.
- Contraste : non testable sans rendu — fichier CSS lu, palettes Bibliothèque/Académique/Militant. À tester via Lighthouse dès que disponible.

## 8. Performance — points statiques

- Polices Google Fonts (`EB+Garamond`) avec `preconnect` ✅ mais bloque rendu si lenteur. Considérer `font-display: swap` (à vérifier dans la stylesheet Google).
- `catalog.json` = 507 KB compressé probablement ~120 KB. Chargé par toutes les pages via `loadCatalog()`. Acceptable mais à surveiller à mesure que le catalog grossit (>2000 docs = problématique). Recommandation : split en `catalog-light.json` (sans `runs[]`/`enrichment`) pour la home et catalogue.

## 9. Synthèse des manques (priorité)

| # | Manque | Impact | Difficulté |
|---|---|---|---|
| 1 | Icônes PNG 192/512 dans le manifest | PWA non installable Android | Triviale (export PNG) |
| 2 | OG description + canonical sur `fiche.html` | Partages sociaux pauvres + risque duplicate | Faible |
| 3 | Pré-rendu HTML des fiches | SEO + previews + perf perçue | Moyenne |
| 4 | `<lastmod>` dans sitemap | Crawl prioritaire des nouveautés | Triviale |
| 5 | Service worker (cache assets) | Promesse PWA tenue, perf | Moyenne |
| 6 | Skip-link accessibilité | Conformité WCAG 2.4.1 | Triviale |
| 7 | Cover image en `og:image` quand dispo | Identité visuelle partages | Faible |
