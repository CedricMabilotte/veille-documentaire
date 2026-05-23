# Cycle C — Audit SEO technique « Terres Libérées »

Audit en lecture seule du site statique généré par `scripts/generate_site.py`,
publié sur `communs.actitude.org`. Fait suite au passage SEO du cycle 3
(`audit/cycle3-seo.md`), qui avait été pleinement implémenté. Le présent audit
contrôle la non-régression après les cycles A et B (ajout de la page
« Trois régimes », NAV réduit, suppression de la fiche `ferme-des-enfants`,
ajout de `glossaire.html` et `suggerer.html`).

Périmètre : 44 pages HTML produites dans `site/`, `sitemap.xml`, `robots.txt`,
`404.html`, et les fonctions `page()`, `render_regimes()`, `render_fiche()`,
`render_classement()`, `render_glossaire()`, `render_index()`, `build_sitemap()`,
`main()` de `generate_site.py`.

## Synthèse de l'état actuel

Le socle SEO du cycle 3 a bien tenu. Sur l'ensemble des points contrôlés, **un
seul vrai défaut** est apparu après les cycles A/B : la nouvelle page
`regimes.html` n'a **pas de données structurées JSON-LD**, alors que toutes les
autres pages éditoriales comparables (accueil, glossaire, classement, fiches)
en ont. Tout le reste est conforme.

Points vérifiés et conformes :

- **`regimes.html`** — `<title>` unique, `<meta name="description">` correcte
  (148 car.), `<link rel="canonical">` présent et exact, bloc Open Graph +
  Twitter Card complet, `theme-color`. Seul manque : le JSON-LD.
- **`sitemap.xml`** — généré dynamiquement depuis le corpus réel
  (`build_sitemap()` / `main()` lignes 2444-2453). Il inclut bien `regimes.html`,
  `glossaire.html`, `suggerer.html`, les 4 catalogues, les pages transverses et
  **chacune des 31 fiches** (`l|p|u|m`). Aucune URL fantôme : `ferme-des-enfants`
  n'apparaît nulle part dans `site/` ni dans les YAML — la suppression est
  propre, et comme le sitemap boucle sur `all_sc` (fiches réellement chargées),
  il ne peut pas contenir de page supprimée. Les fiches créées au cycle A sont
  présentes. 64 entrées `<url>` au total, toutes avec `loc` absolu, `lastmod`,
  `changefreq`, `priority`.
- **`robots.txt`** — `User-agent: * / Allow: /` + ligne `Sitemap:` en URL
  absolue. Correct.
- **Titres & meta descriptions** — les 44 pages ont un `<title>` unique et une
  `<meta name="description">` unique, descriptive et tronquée proprement à
  ~155 caractères sur une frontière de mot (`meta_desc()`). Aucun doublon.
- **JSON-LD des autres pages** — accueil (`WebSite`), glossaire
  (`DefinedTermSet`, 18 termes avec ancres `#g-…`), classement (`ItemList`),
  fiches (`BreadcrumbList` + `Place`/`Organization`). Tous syntaxiquement
  valides, échappés, et cohérents avec le corpus post-cycles A/B.
- **404** — `site/404.html` présent, `<meta name="robots" content="noindex">`,
  un seul `<h1>`, liens de secours.
- **Maillage interne malgré le NAV réduit** — voir analyse détaillée ci-dessous.
  Conforme.

## Analyse — maillage interne et NAV réduit

Le NAV (`<nav class="topnav">`) ne contient plus que 6 entrées : Accueil, Lieux,
Porteurs, Usufruitiers, Classement, Méthode. Les pages **Grilles, Trois régimes,
Glossaire, Modèles voisins** en sont sorties. Risque classique : pages
orphelines, peu de jus de lien.

Vérification effectuée (`grep` sur `site/`) : ces 4 pages restent **bien
reliées**. Le footer (`render` commun, présent sur les 44 pages) contient
systématiquement la rangée :
`Méthode · Trois régimes · Grilles d'analyse · Modèles voisins · Glossaire ·
Proposer un lieu · Données ouvertes (JSON)`.
Chacune des 4 pages hors-NAV reçoit donc un lien entrant depuis **toutes** les
pages du site. En complément, l'accueil les relie en contexte
(section « Comment lire cet annuaire » : `linkrow` vers regimes, grilles,
glossaire), `methode.html` et `glossaire.html` pointent vers `regimes.html`,
et `regimes.html` renvoie vers `grilles.html` et `methode.html`.

Conclusion : le maillage est solide. Une seule réserve mineure (M2 ci-dessous) :
le lien footer est le seul vecteur pour certaines de ces pages depuis les
fiches — un lien contextuel ne ferait pas de mal mais n'est pas un défaut.

---

## RECOMMANDATIONS — Priorité IMPORTANTE

### I1. Ajouter le JSON-LD manquant sur `regimes.html`

Fichier/fonction : `generate_site.py`, `render_regimes()` (lignes 1183-1278).

C'est le seul vrai écart SEO introduit par les cycles A/B. `render_regimes()`
appelle `page(...)` **sans** le paramètre `jsonld` (ligne 1274-1278), alors que
toutes les autres pages éditoriales en passent un. La page décrit explicitement
trois régimes juridiques sous forme de blocs nommés (`label` / `outils` / `but`
/ `role`) et d'un tableau comparatif — un contenu directement balisable.

Recommandation : construire dans `render_regimes()` un bloc `Article` (ou, au
choix, un `DefinedTermSet` à 3 `DefinedTerm` reprenant les trois régimes) et le
passer à `page()` via `jsonld=[…]`. Modèle `Article` minimal :

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Trois régimes du sol",
  "description": "{reg.chapeau tronqué}",
  "inLanguage": "fr",
  "url": "https://communs.actitude.org/regimes.html",
  "isPartOf": {"@type": "WebSite", "name": "Terres Libérées",
              "url": "https://communs.actitude.org/"}
}
```

Variante recommandée (plus riche) — un `DefinedTermSet` bâti depuis la liste
`reg["liste"]` déjà bouclée ligne 1191, chaque régime devenant un `DefinedTerm`
(`name` = `label`, `description` = `but`). Cela aligne `regimes.html` sur le
traitement déjà appliqué au glossaire et reste cohérent après tout changement
de `concepts.yml`, puisque la source est la même que le HTML.

### I2. `grilles.html` et `suggerer.html` — vérifier la présence du JSON-LD

Fichier/fonction : `render_grilles()`, `render_suggerer()`.

Par cohérence avec I1 : ces deux pages hors flux principal n'ont pas non plus
de JSON-LD (à confirmer dans le code). Ce sont des pages plus secondaires, mais
si l'on standardise, leur ajouter au minimum un `WebPage`/`Article`
`isPartOf` le `WebSite` évite l'incohérence « certaines pages balisées,
d'autres non ». Priorité moindre que I1.

---

## RECOMMANDATIONS — Priorité MINEURE

### M1. Titre trop long sur une fiche

Fichier/fonction : `page()` (format `{title} — Terres Libérées`).

`m/ofs-brs.html` produit le `<title>` :
`Organisme de Foncier Solidaire + Bail Réel Solidaire — Terres Libérées`
(~70 caractères). Google tronquera l'affichage. Déjà signalé en M5 du cycle 3,
non traité. Solution : champ optionnel `titre_court` dans le YAML de la fiche,
utilisé pour le `<title>` quand présent. Cosmétique.

### M2. Renforcer le maillage contextuel vers les pages hors-NAV

Fichiers : `render_fiche()`.

Les fiches `l|p|u|m` ne lient les pages Grilles / Régimes / Glossaire que via
le footer. Optionnel : dans le bloc méthodologique d'une fiche (là où l'Indice
et les axes sont expliqués), ajouter un lien contextuel vers `grilles.html` ou
`regimes.html`. Le maillage actuel est déjà suffisant — amélioration de confort,
pas une correction.

### M3. `lastmod` du sitemap

Fichier/fonction : `build_sitemap()` (ligne 2373).

Toutes les `<url>` portent le même `lastmod` = date de build. Acceptable pour un
site statique régénéré en bloc. Si un champ `date_maj` par fiche est ajouté un
jour, le réutiliser ici donnerait un signal de fraîcheur plus juste. Non
bloquant.

---

## Récapitulatif par fichier à toucher

| Fichier / fonction | Reco | Priorité |
|---|---|---|
| `generate_site.py` — `render_regimes()` | I1 | Importante |
| `generate_site.py` — `render_grilles()`, `render_suggerer()` | I2 | Importante |
| `generate_site.py` — `page()` + YAML fiches | M1 | Mineure |
| `generate_site.py` — `render_fiche()` | M2 | Mineure |
| `generate_site.py` — `build_sitemap()` | M3 | Mineure |

## Conclusion

Aucun défaut critique. Le travail SEO du cycle 3 a parfaitement résisté aux
cycles A et B : sitemap dynamique fidèle au corpus (regimes/glossaire inclus,
ferme-des-enfants absente), titres et descriptions uniques, robots et 404
corrects, maillage interne préservé par le footer global malgré le NAV réduit.
**Une seule correction à intégrer en priorité : ajouter le JSON-LD sur
`regimes.html` (I1)** pour aligner la nouvelle page sur le reste du site.
