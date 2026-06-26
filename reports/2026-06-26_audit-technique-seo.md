# Audit technique & SEO — biblio.actitude.org
**Date :** 26 juin 2026  
**Périmètre :** site statique + application JS monopage (SPA hybride)  
**Sources :** `site/index.html`, `site/fiches/fiche.html`, `site/fiches/index.html`, `site/assets/css/style.css`, `site/assets/js/app.js`, `site/feed.xml`, fiche statique `site/fiches/e1e22d67.html`, `site/sitemap.xml`

---

## Résumé exécutif

Le site est techniquement solide pour un projet de veille documentaire. L'architecture hybride (fiches statiques HTML avec meta SEO complètes + application SPA pour le rendu interactif) est intelligente : elle assure l'indexabilité de chaque fiche sans JavaScript. Les points critiques concernent principalement deux absences structurelles (dossier `assets/cards/` manquant côté déploiement, formulaire newsletter sans backend réel), et une série d'améliorations SEO et accessibilité de priorité moyenne à faible.

---

## Problèmes critiques

### C1 — Dossier `assets/cards/` absent du dépôt / site

**Impact : SEO + partage social**

Les fiches statiques (`site/fiches/<id>.html`) déclarent toutes :
```
<meta property="og:image" content="https://biblio.actitude.org/assets/cards/<id>.png">
```
Or le dossier `site/assets/cards/` n'existe pas dans le dépôt. Les images de partage social (Twitter/X, Facebook, LinkedIn, WhatsApp) seront systématiquement cassées pour toutes les fiches indexées. Les covers existent bien dans `site/assets/covers/<id>.png` (et l'appli JS les utilise via `coverPath()`), mais le pipeline de génération des fiches statiques référence un chemin différent (`cards/` vs `covers/`).

**Action :** Soit créer `assets/cards/` et y placer les images (cartes au format 1200×630 px recommandé pour og:image), soit corriger le générateur de fiches statiques pour pointer vers `assets/covers/`.

### C2 — Formulaire newsletter sans action backend

**Impact : fonctionnel**

Le formulaire newsletter présent sur toutes les pages (accueil, footer, fiches, catalogue) :
```html
<form class="newsletter-form" aria-label="Inscription à la newsletter">
  <input type="email" name="email" …>
  <button type="submit">S'inscrire</button>
</form>
```
n'a ni `action` ni handler JS. La version dans le footer de `apropos.html` mentionne en texte d'aide une adresse mailto, mais le formulaire principal lui n'a aucune cible. Un clic sur "S'inscrire" ne fait rien (rechargement de page). L'implémentation correcte sur l'accueil (`hero-search`) passe par `action="fiches/index.html" method="get"` — le formulaire newsletter devrait au minimum rediriger vers une page de confirmation ou déclencher un email `mailto:`.

**Action :** Brancher le formulaire sur un service réel (Listmonk, Brevo, etc.) ou remplacer par un lien `mailto:` explicite avec `subject=` prérempli.

### C3 — Description RSS parasite : "erreur scoring"

**Impact : qualité des données, image de marque**

Dans `site/feed.xml`, l'item "Community Land Trust Book" contient :
```xml
<description>erreur scoring</description>
```
C'est une valeur de fallback du pipeline de génération qui s'est retrouvée publiée. Les agrégateurs RSS afficheront cette description vide de sens à la place d'un résumé. Tous les abonnés au flux verront cette entrée dégradée.

**Action :** Corriger dans le pipeline la logique de fallback pour ne jamais publier un message d'erreur interne comme description RSS. Si le résumé est absent, omettre le champ ou utiliser le titre.

---

## Problèmes importants

### I1 — `og:image` du template `fiche.html` pointe sur un SVG

**Impact : compatibilité réseaux sociaux**

Le fichier `site/fiches/fiche.html` (template SPA) déclare en statique :
```html
<meta property="og:image" content="https://biblio.actitude.org/assets/img/og-default.svg">
```
Les robots de scraping Open Graph (Twitter/X, Facebook) **ne supportent pas les SVG** pour les previews. Cette valeur par défaut est remplacée dynamiquement par JS mais uniquement après rendu côté client — ce que les robots ne font pas. Si une fiche est partagée sans JS ou avant que JS n'ait mis à jour le DOM, l'image de prévisualisation sera cassée ou absente.

**Action :** Remplacer `og-default.svg` par un PNG/JPEG au format 1200×630 px pour toutes les pages qui n'ont pas d'image spécifique (pages de catalogue, auteurs, chronologie, concepts).

### I2 — Balise `<link rel="canonical">` absente de `fiche.html`

**Impact : duplicate content SEO**

La page `site/fiches/fiche.html` n'a pas de balise canonical statique. Une URL du type `fiche.html?id=e1e22d67` coexiste avec la fiche statique `e1e22d67.html` qui pointe en canonical vers `https://biblio.actitude.org/fiches/e1e22d67.html`. Les moteurs peuvent indexer les deux URLs comme des pages distinctes avec contenu identique (ou presque — la SPA n'a pas de contenu textuel visible sans JS). La balise canonical est injectée dynamiquement par JS dans `updateMetaTags()`, mais elle n'est pas lisible par les robots.

**Action :** Ajouter dans `fiche.html` une balise canonical statique générique, ou mieux, s'assurer que le rendu statique (les `e1e22d67.html`) est le seul point d'entrée indexé via le sitemap et que `fiche.html?id=…` est exclue du sitemap et marquée `noindex` via un meta robots.

### I3 — Sitemap sans `<lastmod>`, `<changefreq>` ni `<priority>`

**Impact : crawl budget, fraîcheur**

Le `site/sitemap.xml` ne contient que des `<loc>`. L'absence de `<lastmod>` empêche Google de prioriser les pages modifiées récemment lors du recrawl. Avec un catalogue qui grossit régulièrement, le crawl budget sera moins bien utilisé.

**Action :** Ajouter `<lastmod>` (date de dernière modification de la fiche) et optionnellement `<changefreq>` (`monthly` pour les fiches, `weekly` pour l'accueil et le catalogue).

### I4 — `twitter:image` absent de toutes les pages

**Impact : partage sur Twitter/X**

Aucune page du site ne déclare `<meta name="twitter:image">`. La balise `twitter:card` est présente (`summary_large_image`) mais sans l'image correspondante. Twitter/X peut tomber en repli sur `og:image` mais ce comportement n'est pas garanti, surtout pour les SVG (voir I1).

**Action :** Ajouter `<meta name="twitter:image" content="…">` avec une URL vers un PNG.

### I5 — Chargement de Google Fonts sans `font-display: swap`

**Impact : performance — LCP (Largest Contentful Paint)**

La feuille de style Google Fonts est chargée via :
```html
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
```
Le paramètre `display=swap` est bien présent dans l'URL. Cependant, EB Garamond est une police d'affichage lourde (plusieurs variants chargés). Sur connexion lente, le texte principal restera invisible jusqu'au chargement de la police (FOIT). Le `<link rel="preconnect">` est en place pour `fonts.googleapis.com` et `fonts.gstatic.com`, ce qui est bien — mais il manque un `preload` explicite pour le fichier de fonte le plus critique (le regular 400).

**Action (optionnelle):** Ajouter un `<link rel="preload">` pour le subset latin de EB Garamond 400, ou envisager l'auto-hébergement de la fonte pour supprimer la dépendance externe.

### I6 — Le logo SVG dans le header a `alt=""` vide sans `aria-hidden`

**Impact : accessibilité**

```html
<img src="../assets/img/logo.svg" alt="" class="brand-mark">
```
L'attribut `alt=""` est correct pour une image décorative, mais le lien parent `<a class="brand" aria-label="BIBLIO — accueil">` fournit le label accessible complet. Ce point est techniquement conforme (alt="" vide sur image décorative dans un lien labelisé). Aucune action nécessaire sur ce point précis, mais il faut documenter ce choix pour éviter de le corriger par erreur.

### I7 — `<meta http-equiv="Cache-Control">` invalide en HTML

**Impact : cohérence technique**

Toutes les pages principales déclarent :
```html
<meta http-equiv="Cache-Control" content="max-age=3600">
```
Cette directive est ignorée par les navigateurs modernes (et les proxies) quand elle est dans le HTML — le contrôle du cache HTTP doit se faire via les en-têtes HTTP du serveur, pas via les meta HTML. Ce meta n'a aucun effet pratique et encombre le `<head>`.

**Action :** Supprimer ce meta et configurer le cache côté serveur web (nginx, Apache, CDN).

### I8 — `<h4>` dans le footer sans hiérarchie cohérente

**Impact : accessibilité / structure sémantique**

Le footer utilise des `<h4>` ("BIBLIO", "Naviguer", "Suivre & réutiliser") qui ne s'inscrivent pas dans une hiérarchie de titres cohérente sur les pages. Sur `index.html`, la structure est : `h1` (hero) → `h2` (sections) → `h3` (cartes) → `h4` (footer). C'est acceptable, mais sur les pages avec un seul niveau de heading (`auteurs.html` etc.), les `h4` du footer peuvent être perçus comme des sous-titres de section hors-contexte par les lecteurs d'écran.

**Action :** Considérer l'utilisation de `<p>` avec un style de titre dans le footer, ou conserver `h4` mais s'assurer que la hiérarchie est cohérente sur toutes les pages.

---

## Quick wins (< 1 heure chacun)

### Q1 — Ajouter `twitter:image` sur toutes les pages de gabarit

5 fichiers à modifier (`index.html`, `fiches/index.html`, `fiches/fiche.html`, `apropos.html`, pages secondaires). Ajouter :
```html
<meta name="twitter:image" content="https://biblio.actitude.org/assets/img/og-default.png">
```
Nécessite d'abord de créer `og-default.png` (voir I1).

### Q2 — Corriger l'item RSS "Community Land Trust Book"

Éditer `feed.xml` (ou le template de génération) pour remplacer `<description>erreur scoring</description>` par une description pertinente ou par le titre du document.

### Q3 — Supprimer le `<meta http-equiv="Cache-Control">` inutile

Retrait simple sur tous les gabarits HTML. Gain : head plus propre, aucun risque de régression.

### Q4 — Ajouter `<lastmod>` dans le sitemap

Modifier le script de génération du sitemap pour inclure la date de dernière modification de chaque fiche. Si le script est Python, `datetime.date.today().isoformat()` suffit comme valeur par défaut pour les pages dynamiques.

### Q5 — Corriger le chemin `assets/cards/` → `assets/covers/` dans les fiches statiques

Si les fiches statiques sont générées par un script, corriger le template pour pointer vers `assets/covers/<id>.png` au lieu de `assets/cards/<id>.png`. Impact immédiat sur toutes les prévisualisations sociales.

### Q6 — Descriptions RSS tronquées

Plusieurs descriptions dans `feed.xml` sont coupées en plein milieu d'une phrase (ex. : "Le document structure l'enseignement autour de la « problema sa duta » (problème de la terre) aux Philippines, analysé comme résultant de l'appropriation et de la dépossession orchestrées par les"). Vérifier et augmenter la limite de caractères dans le générateur RSS (ou utiliser `<content:encoded>` pour la version longue).

### Q7 — Titres RSS avec préfixe parasite

Plusieurs titres RSS commencent par un point médian (`·`) suivi d'un espace : `· Cultiver ou mourir (page par page) (PDF)`. Ces artefacts proviennent probablement du `link_text` brut des sources. Filtrer ce préfixe dans le pipeline RSS.

### Q8 — Suffixe `(PDF)` dans les titres RSS

De même, `(PDF)` dans les titres (`· La fin de la ZAD, le début de quoi ? (cahier) (PDF)`) est redondant et peu élégant dans un lecteur RSS. Nettoyer dans le pipeline.

---

## Améliorations long terme

### L1 — Rendu côté serveur (SSR) ou pré-rendu des fiches

**Priorité : haute pour le SEO**

Le contenu principal des fiches (titre, résumé, citations, mots-clés) est rendu entièrement par JavaScript à partir de `catalog.json`. Les moteurs de recherche indexent de plus en plus les pages JS, mais avec un délai et une fiabilité moindres par rapport au HTML statique. Les fiches `.html` statiques fournissent un fallback avec du contenu minimal, mais pas l'intégralité du contenu.

Piste : enrichir les fiches statiques (générées par le pipeline) avec le contenu HTML complet de la fiche (résumé, mots-clés, citations) au lieu du simple fallback `<meta http-equiv="refresh">`. Le meta refresh vers `fiche.html?id=…` est une pratique que Google pénalise potentiellement (assimilé à un cloaking).

### L2 — Schema.org : `datePublished` au format ISO 8601 complet

Dans `fiche.html`, le JSON-LD injecte `"datePublished": "2024"` (l'année seule). Le format recommandé est `"datePublished": "2024-01-01"` (ISO 8601). Certains validateurs Schema.org rejettent la valeur année-seule pour le champ `datePublished` d'un `ScholarlyArticle`.

### L3 — Lazy loading des images de couverture dans `fiche.html`

L'image de couverture principale de la fiche (dans `.fiche-cover`) n'a pas `loading="lazy"`. Pour la fiche, c'est justifié (c'est above-the-fold sur desktop) — mais sur mobile la couverture est en bas de la mise en page réorganisée en colonne unique. Ajouter `loading="lazy"` conditionnel ou utiliser `fetchpriority="low"` sur mobile.

### L4 — Optimisation des images PNG de couverture

Les couvertures (extraites de PDF) peuvent être volumineuses. Sans passer par la compression ou la conversion WebP/AVIF, les pages catalogue (grille de 10+ couvertures) peuvent charger plusieurs Mo d'images. Envisager :
- Conversion en WebP avec fallback PNG (via `<picture>`)
- Compression lossy à 80 % via `cwebp` ou Pillow dans le pipeline
- Dimensionnement adapté (max 400×550 px pour les vignettes)

### L5 — `manifest.json` et service worker référencés mais absents

Les pages déclarent :
```html
<link rel="manifest" href="../manifest.json">
```
et le code d'enregistrement du service worker est présent dans plusieurs pages, mais ni `manifest.json` ni `sw.js` ne sont présents dans le dépôt (Glob retourne rien). Ces fichiers existent peut-être en dehors de ce qui est versionné, mais s'ils sont absents en déploiement, le navigateur enregistrera des 404 silencieux qui polluent la console et empêchent l'installation PWA.

**Action :** Vérifier que `manifest.json` et `sw.js` sont bien présents sur le serveur et versionnés.

### L6 — Pas de `robots.txt` visible dans le dépôt

Aucun `robots.txt` trouvé dans `site/`. Un robots.txt permet de contrôler ce que les crawlers indexent (notamment `fiche.html?id=…` qui est la version SPA non-canonique) et d'indiquer l'emplacement du sitemap.

**Action :** Créer `site/robots.txt` avec au minimum :
```
User-agent: *
Allow: /
Sitemap: https://biblio.actitude.org/sitemap.xml
Disallow: /fiches/fiche.html
```

### L7 — Accessibilité : contrastes dans le thème "palette militant"

Le thème `[data-palette="militant"]` utilise rouge vif `#cc0000` comme accent sur blanc `#ffffff`. Le ratio est d'environ 5.9:1 (conforme AA) pour le texte normal, mais les badges, pills et éléments `font-size: 11-12px` avec fond `#cc0000` et texte blanc doivent atteindre 4.5:1 (AA) ou 7:1 (AAA) selon leur taille. À vérifier en particulier pour les `.score-pill` et `.section-kicker`.

### L8 — Accessibilité : focus trap absent dans la lightbox couverture

La lightbox (composant JS dans `app.js`) ouvre un `<div role="dialog" aria-modal="true">` mais ne piège pas le focus à l'intérieur. L'attribut `aria-modal` seul ne suffit pas : il faut gérer le focus manuellement (Tab cycle dans la boîte de dialogue, retour au focus d'origine à la fermeture). Actuellement, Tab depuis la lightbox navigue dans le fond de page.

### L9 — Accessibilité : `aria-haspopup="menu"` incorrect sur le bouton palette

```html
<button class="palette-toggle" type="button" aria-label="Changer de palette" aria-haspopup="menu">
```
Le menu généré est un `<div role="menu">` avec des `<button role="menuitem">`. L'attribut `aria-expanded` est absent — quand le menu est ouvert ou fermé, les technologies d'assistance ne reçoivent pas de notification de changement d'état. Ajouter `aria-expanded="false/true"` synchronisé avec l'état du menu.

### L10 — Feeds RSS thématiques non référencés dans le `<head>`

Le site génère des flux thématiques (`/feeds/communs.xml`, `/feeds/paysannerie.xml`, etc.) mais ils ne sont pas référencés par des balises `<link rel="alternate" type="application/rss+xml">` dans le `<head>`. Seul `feed.xml` est référencé. Les agrégateurs et navigateurs ne peuvent donc pas les découvrir automatiquement.

**Action :** Ajouter dans `<head>` les balises alternate pour chaque flux thématique, ou au minimum les lister sur la page d'accueil et dans la page Méthodologie.

---

## Points positifs notables

- **Accessibilité de base bien traitée :** `role="banner"`, `role="contentinfo"`, `aria-label` sur toutes les navigations, `aria-live` sur les zones de contenu dynamique, `aria-expanded` sur le menu mobile, skip-to-content implicite via structure sémantique.
- **ARIA sur les boutons interactifs :** `aria-pressed` sur les boutons grille/étagère, labels sur tous les inputs.
- **Skeleton screens :** les cartes squelettes pendant le chargement sont une bonne pratique UX (A5 dans les commentaires).
- **JSON-LD Schema.org :** présent sur l'accueil (WebSite + SearchAction + Organization) et injecté dynamiquement sur les fiches (ScholarlyArticle/Book). La SearchAction est correctement formée.
- **Breadcrumb sémantique :** `<nav aria-label="fil d'Ariane"><ol class="breadcrumbs">` — conforme aux recommandations d'accessibilité.
- **PWA :** enregistrement du service worker en place, meta manifest référencé.
- **Responsive :** breakpoints à 700 px et 900 px bien calibrés, menu mobile avec burger.
- **Thème sombre / préférences système :** `matchMedia('(prefers-color-scheme: dark)')` pris en compte.
- **Contrastes WCAG :** `--text-faint` corrigé de `#7a6f60` (sous AA) à `#6b6051` (~4.6:1, conforme AA) — commentaire C4 dans style.css.
- **`prefers-reduced-motion` :** pris en compte dans components.css pour les animations shimmer.
- **Export CSV/BibTeX :** fonctionnalité utile pour un public académique, bien implémentée.
- **Noscript fallback :** la fiche affiche un message lisible sans JS avec des liens de navigation.
- **Sécurité XSS :** la fonction `escape()` est systématiquement utilisée avant tout rendu HTML généré côté client.

---

## Synthèse priorisée

| Priorité | Item | Effort |
|----------|------|--------|
| Critique | C1 — `assets/cards/` absent (og:image cassées) | Moyen (pipeline) |
| Critique | C2 — Newsletter sans backend | Moyen |
| Critique | C3 — RSS "erreur scoring" publiée | Rapide |
| Important | I1 — og:image SVG incompatible réseaux sociaux | Rapide |
| Important | I2 — Canonical absent de fiche.html (SPA) | Rapide |
| Important | I3 — Sitemap sans lastmod | Rapide (script) |
| Important | I4 — twitter:image absent | Rapide |
| Important | I5 — Google Fonts sans preload | Rapide |
| Important | I7 — meta Cache-Control HTML inutile | Trivial |
| Quick win | Q5 — Corriger chemin cards/ → covers/ | 15 min |
| Quick win | Q6/Q7/Q8 — Nettoyage titres/descriptions RSS | 30 min |
| Long terme | L1 — SSR / pré-rendu fiches complet | Long |
| Long terme | L6 — robots.txt manquant | 10 min |
| Long terme | L5 — manifest.json / sw.js absents du repo | Vérification |
| Long terme | L8 — Focus trap lightbox | Moyen |
| Long terme | L10 — Feeds thématiques non référencés | 15 min |
