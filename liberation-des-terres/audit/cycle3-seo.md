# Cycle 3 — Audit SEO technique « Terres Libérées »

Audit en lecture seule du site statique généré par `scripts/generate_site.py`,
destiné à GitHub Pages. Aucun fichier modifié.

Périmètre examiné : `generate_site.py` (fonction `page()`, `render_*`, constante
`CSS`), pages produites dans `site/` (accueil, catalogues, fiches `l|p|u|m/*`,
classement, grilles, méthode, glossaire), et recherche des fichiers
`sitemap.xml`, `robots.txt`, `feed*`, `404.html`, `manifest`, `favicon`.

## Synthèse de l'état actuel

Le `<head>` produit par `page()` (lignes 210-218) ne contient que :
`charset`, `viewport`, `<title>`, `<meta name="description">`, la feuille de
style. C'est un socle minimal. Manquent intégralement :

- Aucune balise `<link rel="canonical">`.
- Aucune balise Open Graph ni Twitter Card.
- Aucune donnée structurée JSON-LD.
- Aucun `sitemap.xml`, aucun `robots.txt`.
- Aucun favicon, manifest, page 404, humans.txt.
- Aucun flux RSS/Atom.
- Incohérence d'URL : `concepts.yml` déclare `url: https://terres-liberees.actitude.org`
  alors que la cible de publication annoncée est `communs.actitude.org`. Aucun
  fichier `CNAME` présent dans `site/` (le script le préserve pourtant, voir
  ligne 1776). À trancher avant toute génération de canonical/sitemap.

Points déjà corrects : `lang="fr"`, `charset utf-8`, `viewport` responsive, un
seul `<h1>` par page, hiérarchie Hn cohérente (`h1` → `h2.sec` → `h3`), URLs
propres et stables (`/l/larzac.html` etc.), maillage interne riche (nav, fil
d'Ariane, rétro-liens, cartes), CSS unique externalisé et léger, SVG inline
(pas d'images bitmap à charger), aucun polyfill ni JS de tiers.

---

## RECOMMANDATIONS — Priorité CRITIQUE

### C1. Trancher et centraliser l'URL canonique du site

Fichier : `config/concepts.yml`, clé `project.url`.

Le reste de l'audit suppose une URL de base unique. Le brief indique une
publication sur `communs.actitude.org`. Décider :
soit le site est servi à la racine `https://communs.actitude.org/`,
soit dans un sous-chemin `https://communs.actitude.org/terres-liberees/`.
Cette `BASE_URL` doit être lue depuis `concepts.yml` et passée à `page()`.
Ajouter aussi un fichier `site/CNAME` contenant `communs.actitude.org`
(le script le conserve déjà, ligne 1776). **Tout ce qui suit dépend de ce choix.**

### C2. Balise canonical sur chaque page

Fichier/fonction : `generate_site.py`, fonction `page()`.

Actuellement `page()` ne reçoit pas l'URL de la page courante. Ajouter un
paramètre `path` (chemin relatif du fichier, ex. `"l/larzac.html"`,
`"index.html"`) transmis par chaque `render_*` et `main()`.

Dans le `<head>`, ajouter :

```html
<link rel="canonical" href="{BASE_URL}/{path}">
```

Pour l'accueil, canonicaliser vers la racine sans `index.html` :
`href="{BASE_URL}/"`. Sans canonical, GitHub Pages expose la même page sous
plusieurs URLs (`/l/larzac.html` et `/l/larzac`) — risque de contenu dupliqué.

### C3. Générer `site/robots.txt`

Fichier : nouveau `site/robots.txt`, écrit depuis `main()` (à côté de
`data.json`, ligne 1813).

```
User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
```

### C4. Générer `site/sitemap.xml`

Fichier : nouveau `site/sitemap.xml`, écrit en fin de `main()` une fois toutes
les pages connues.

Recenser : `index.html`, les 4 catalogues, `classement.html`, `grilles.html`,
`methode.html`, `glossaire.html`, et chaque fiche `CAT_SLUG[cat]/{uid}.html`.
Exclure `data.json`. Modèle d'entrée :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{BASE_URL}/</loc>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{BASE_URL}/l/larzac.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <!-- ... une <url> par page ... -->
</urlset>
```

Le site étant entièrement statique, omettre `<lastmod>` ou y mettre la date de
génération (`datetime.date.today().isoformat()`).

### C5. Corriger la longueur des meta descriptions

Fichier/fonction : `render_fiche()` (ligne 738-739) et `page()` (ligne 216).

`render_fiche` passe `description=clean(fiche.get("resume", "")) or sub` SANS
troncature. Résultat constaté sur `site/l/larzac.html` : meta description de
~600 caractères (le `resume` complet). Google n'affiche que ~150-160 caractères.

Corriger dans `page()` en tronquant proprement à ~155 caractères sur une
frontière de mot :

```python
def _meta_desc(text, limit=155):
    t = clean(text)
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0]
    return cut + "…"
```

Appliquer `desc = e(_meta_desc(description or base))`.
`render_index` tronque déjà à `[:155]` (ligne 1330) mais coupe en plein mot —
à remplacer par la même fonction. Vérifier que chaque description fait
50-160 caractères et décrit *spécifiquement* la page.

---

## RECOMMANDATIONS — Priorité IMPORTANTE

### I1. Open Graph + Twitter Card dans `page()`

Fichier/fonction : `generate_site.py`, `page()`, dans le `<head>`.

Aucune balise OG/Twitter actuellement : le partage sur réseaux sociaux et
messageries (Mastodon, Slack, etc.) n'affiche ni titre ni vignette. Ajouter,
en réutilisant `title`, `desc`, l'URL canonique (C2) et `BASE_URL` :

```html
<meta property="og:type" content="website">
<meta property="og:site_name" content="Terres Libérées">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{title} — Terres Libérées">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE_URL}/{path}">
<meta property="og:image" content="{BASE_URL}/assets/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} — Terres Libérées">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{BASE_URL}/assets/og-default.png">
```

Pour les fiches, `og:type` peut passer à `article`.

### I2. Image Open Graph par défaut

Fichier : nouveau `site/assets/og-default.png` (1200×630).

Créer une image OG sobre, cohérente avec la charte (papier `#f5f2e9`, encre
`#221f1a`, vert `#4a7a3a`, terracotta `#bc5d3a`). Méthode recommandée : générer
d'abord un SVG `assets/og-default.svg` puis le rasteriser en PNG (les
crawlers sociaux gèrent mal le SVG en `og:image`). Modèle de SVG source :

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#f5f2e9"/>
  <rect x="0" y="0" width="1200" height="14" fill="#221f1a"/>
  <rect x="80" y="120" width="64" height="64" rx="10" fill="#4a7a3a"/>
  <text x="96" y="166" font-family="system-ui,sans-serif" font-size="34"
        font-weight="800" fill="#f5f2e9">TL</text>
  <text x="170" y="166" font-family="system-ui,sans-serif" font-size="40"
        font-weight="700" fill="#221f1a">Terres Libérées</text>
  <text x="80" y="320" font-family="Georgia,serif" font-size="76"
        font-weight="700" fill="#221f1a">La terre, soustraite</text>
  <text x="80" y="408" font-family="Georgia,serif" font-size="76"
        font-weight="700" fill="#221f1a">au marché.</text>
  <rect x="80" y="452" width="60" height="8" fill="#bc5d3a"/>
  <text x="80" y="520" font-family="system-ui,sans-serif" font-size="30"
        fill="#5f5849">Annuaire critique des montages de libération des terres en France</text>
</svg>
```

Idéalement, générer une image OG *par fiche* (titre + indice + palier) ; à
défaut, l'image par défaut suffit pour une v1.

### I3. JSON-LD — `WebSite` + `SearchAction` sur l'accueil

Fichier/fonction : `render_index()`, injecter un `<script type="application/ld+json">`
dans le `body` (ou via un nouveau paramètre `head_extra` de `page()`).

Recommandation : ajouter à `page()` un paramètre optionnel `jsonld` (liste de
dicts) sérialisé dans le `<head>`. Pour l'accueil :

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Terres Libérées",
  "alternateName": "Annuaire critique des montages de libération des terres en France",
  "url": "{BASE_URL}/",
  "inLanguage": "fr",
  "description": "{description tronquée}"
}
```

Le `SearchAction` n'est pertinent que si une vraie URL de recherche existe.
Le filtre des catalogues est en JavaScript pur (pas d'URL paramétrée) : NE PAS
déclarer de `SearchAction` tant qu'il n'y a pas d'endpoint `?q=` réel, sous
peine de balisage trompeur. À considérer seulement si une page de recherche
avec paramètre d'URL est ajoutée plus tard.

### I4. JSON-LD — `BreadcrumbList` sur les fiches

Fichier/fonction : `render_fiche()`. Le fil d'Ariane HTML existe déjà
(lignes 540-544) ; le doubler en JSON-LD :

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Accueil",
     "item": "{BASE_URL}/"},
    {"@type": "ListItem", "position": 2, "name": "{catlabel}",
     "item": "{BASE_URL}/{CAT_PAGE[cat]}"},
    {"@type": "ListItem", "position": 3, "name": "{fiche.nom}"}
  ]
}
```

(Le dernier `ListItem` n'a pas d'`item` : c'est la page courante.)

### I5. JSON-LD — entité principale de chaque fiche

Fichier/fonction : `render_fiche()`.

- Fiches **lieu** : `@type: "Place"`, avec `name`, `description` (le `resume`),
  `url` canonique, et — si `fiche.localisation` est renseigné — un sous-objet
  `address` de type `PostalAddress` (`addressLocality` = commune,
  `addressRegion` = region, `addressCountry` = "FR"). Si des coordonnées
  existent un jour, ajouter `geo` (`GeoCoordinates`).
- Fiches **porteur** et **usufruitier** : `@type: "Organization"` (ou
  `"NGO"` quand la forme juridique est associative/fondation), avec `name`,
  `description`, `url` (lien externe `fiche.url` en `sameAs`), et
  l'URL canonique de la fiche comme `mainEntityOfPage`.
- Fiches **modèle voisin** : `@type: "Organization"` également, avec une
  `description` signalant le caractère comparatif.

Modèle pour un porteur :

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{fiche.nom}",
  "description": "{resume tronqué ~250 car.}",
  "url": "{fiche.url}",
  "mainEntityOfPage": "{BASE_URL}/p/{uid}.html"
}
```

Ne PAS inventer de champs `aggregateRating` à partir de l'Indice de
libération : ce n'est pas une note d'avis consommateur, le baliser ainsi
serait trompeur pour les moteurs.

### I6. JSON-LD — `ItemList` sur le classement

Fichier/fonction : `render_classement()`.

Le classement est une liste ordonnée d'entrées notées — `ItemList` est
exactement adapté :

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Classement par l'Indice de libération",
  "itemListOrder": "https://schema.org/ItemListOrderDescending",
  "numberOfItems": 21,
  "itemListElement": [
    {"@type": "ListItem", "position": 1,
     "url": "{BASE_URL}/l/larzac.html", "name": "Terres du Larzac"},
    {"@type": "ListItem", "position": 2,
     "url": "{BASE_URL}/p/conservatoire-littoral.html", "name": "Conservatoire du littoral"}
  ]
}
```

Boucler sur la liste `core` déjà triée (ligne 879).

### I7. JSON-LD — `DefinedTermSet` sur le glossaire

Fichier/fonction : `render_glossaire()`. La constante `GLOSSAIRE`
(lignes 1150-1202) se mappe directement :

```json
{
  "@context": "https://schema.org",
  "@type": "DefinedTermSet",
  "name": "Glossaire — Terres Libérées",
  "url": "{BASE_URL}/glossaire.html",
  "hasDefinedTerm": [
    {"@type": "DefinedTerm", "name": "Nue-propriété",
     "description": "{définition}",
     "url": "{BASE_URL}/glossaire.html#g-nue-propriete"}
  ]
}
```

Les ancres `#g-{slug}` existent déjà (ligne 1208), réutilisables comme `url`
de chaque `DefinedTerm`.

### I8. Page 404 personnalisée

Fichier : nouveau `site/404.html`, écrit depuis `main()`.

GitHub Pages sert automatiquement `/404.html` sur toute URL inconnue.
La générer avec le gabarit `page()` (donc nav + style cohérents) :
titre « Page introuvable », un `<h1>`, un message bref et des liens vers
l'accueil, le classement et les catalogues. Ajouter `<meta name="robots"
content="noindex">` dans cette page uniquement.

### I9. Favicon

Fichiers : nouveaux `site/favicon.svg` (+ `site/favicon.ico` de repli),
référencés dans `page()` :

```html
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{up}favicon.ico" sizes="any">
```

Favicon SVG simple reprenant le logo-mark « TL » (carré vert `#4a7a3a`,
lettres claires) — cohérent avec `.logo-mark` du CSS.

---

## RECOMMANDATIONS — Priorité MINEURE

### M1. Flux Atom des nouveaux lieux

Fichier : nouveau `site/feed.xml` (Atom), généré depuis `main()`, plus
`<link rel="alternate" type="application/atom+xml" href="{up}feed.xml">` dans
`page()`.

Pertinent pour la veille (« nouveaux lieux référencés »), MAIS seulement si
une **date** existe par fiche. Aujourd'hui les YAML n'ont pas de champ
`date_ajout` / `date_maj` fiable. Recommandation : ajouter d'abord un champ
`date_ajout` dans les fiches YAML, puis générer un flux Atom des fiches `lieu`
triées par date décroissante. Sans ce champ, un flux n'apporte rien. Priorité
basse : à faire après la stabilisation du corpus.

### M2. `web app manifest`

Fichier : nouveau `site/manifest.webmanifest` + `<link rel="manifest">`.

Faible enjeu SEO pur, utile surtout pour l'« ajout à l'écran d'accueil ».
Optionnel pour un annuaire documentaire. Si ajouté : `name`, `short_name`
(« Terres Libérées »), `theme_color: "#221f1a"`, `background_color: "#f5f2e9"`,
`display: "minimal-ui"`, `icons` pointant le favicon. Ajouter aussi
`<meta name="theme-color" content="#221f1a">` dans `page()`.

### M3. `humans.txt`

Fichier : nouveau `site/humans.txt`. Purement informatif (auteurs, outils,
remerciements). Aucun impact SEO ; à inclure si souhaité par cohérence
« communs / open data ».

### M4. Attributs des liens externes

Fichier/fonction : `render_fiche()` lignes 600-601 et 722-724.

Les liens externes (`fiche.url`, sources) ont `target="_blank" rel="noopener"`.
Ajouter `rel="noopener noreferrer"` voire `rel="noopener nofollow ugc"` pour
les sources tierces si l'on ne veut pas transmettre de signal de lien vers
elles. Détail mineur ; `noopener` actuel est déjà acceptable côté sécurité.

### M5. `<title>` — ordre et longueur

Fichier/fonction : `page()` ligne 215. Format actuel
`{title} — Terres Libérées`. Correct et unique par page. Vérifier que les
titres de fiches longs (`Organisme de Foncier Solidaire + Bail Réel Solidaire`)
ne dépassent pas ~60 caractères une fois le suffixe ajouté ; sinon, prévoir un
champ `titre_court` dans le YAML pour le `<title>`. Mineur.

### M6. `preload` de la feuille de style

Fichier/fonction : `page()`. Le CSS est déjà unique, externe et léger : le
chargement bloquant est acceptable. Un `<link rel="preload" as="style">` est
superflu ici. **Ne rien faire** — noté pour écarter explicitement cette
micro-optimisation.

### M7. `aria` / accessibilité (recoupe le SEO)

Les SVG `role="img"` ont des `aria-label` : bon. Vérifier que la page 404
(I8) et les nouveaux blocs gardent un seul `<h1>`. RAS sur l'existant.

---

## Récapitulatif par fichier à toucher

| Fichier / fonction | Recommandations |
|---|---|
| `config/concepts.yml` (`project.url`) | C1 |
| `generate_site.py` — `page()` | C2, I1, I3 (param `jsonld`/`head_extra`), I9, M2, M5 |
| `generate_site.py` — `render_fiche()` | C5, I4, I5, M4 |
| `generate_site.py` — `render_index()` | C5, I3 |
| `generate_site.py` — `render_classement()` | I6 |
| `generate_site.py` — `render_glossaire()` | I7 |
| `generate_site.py` — `main()` | C3, C4, I8 (404), M1 (feed) |
| Nouveaux fichiers dans `site/` | `CNAME`, `robots.txt`, `sitemap.xml`, `404.html`, `favicon.svg`, `assets/og-default.png` |

## Ordre d'implémentation conseillé

1. C1 (URL) — prérequis de tout le reste.
2. C2, C3, C4, C5 — indexabilité de base.
3. I1, I2 — partage social.
4. I3-I7 — données structurées.
5. I8, I9 — 404 et favicon.
6. M1-M7 — finitions, après stabilisation du corpus.
