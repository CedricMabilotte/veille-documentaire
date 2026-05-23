# Vérification finale QA — Terres Libérées

Date : 2026-05-23. Site régénéré après correction. Verdict : **bon pour livraison**.

## 1. Régénération
`python3 scripts/generate_site.py` s'exécute sans erreur.
Sortie : 28 fiches (7 lieux / 10 porteurs / 7 usufruitiers / 4 modèles), 47 fichiers
dans `site/`. Note : le glob initial faisait apparaître 11 fichiers « porteurs » ;
en réalité `lurzaindia.yml` est dans `lieux/` — corpus cohérent à 28 fiches.

## 2. Liens internes
0 lien `<a href>` interne cassé sur les 39 pages HTML (toutes cibles vérifiées
présentes dans `site/`). Nav, footer, fil d'Ariane, rétro-liens entre fiches :
tous valides. Les 4 modèles voisins n'ont pas de bloc « Reliés » — comportement
voulu (hors classement, sans liens dans l'annuaire).

## 3. Cohérence des scores
Recalcul manuel depuis les blocs `grille:` YAML + `grilles.yml`/`ranking.yml`
(formule Σpoids×facteur/Σpoids×100, indice = brut×(0,5+0,5×complétude)) :
- 24 fiches notées : **0 écart** entre recalcul, `data.json` et HveML affiché.
- Échantillon vérifié page par page (Larzac 95, SCTL 81, Fève 40, Foncière TdL 60,
  Villarceaux 68 avec axe C `n.r.`, NDDL 68, Réneta 71, Conservatoire 95,
  OFS-BRS 77 estimé) : indice, axes A/B/C et badge concordants.

## 4. Rendu HTML
0 accolade de template Python orpheline (hors `<script>`), 0 `None`/`null`/`nan`
affiché brut, 0 texte YAML multi-lignes mal replié. Balises équilibrées sur les
pages testées. 184 SVG inline (triangles, anneaux, histogrammes) : tous bien
formés (parsing XML OK).

## 5. Cohérence visuelle et éditoriale
Nav identique sur les 39 pages (1 seule variante après normalisation). Footer
présent partout. Aucun `<h2 class="sec">` dupliqué dans une même page : pas de
section orpheline laissée par les 3 cycles.

## 6. Accessibilité
- Exactement 1 `<h1>` par page (39/39).
- Tous les SVG porteurs de sens ont `role="img"`+`aria-label` ; les SVG
  décoratifs ont `aria-hidden="true"`. 0 `<img>` sans `alt`.
- Contrastes WCAG AA : tous les couples texte/fond ≥ 4.5:1 (le plus faible,
  `gold-dk` sur papier, 4.78 ; `faint` sur beige, 4.69 — conformes).

## 7. SEO
- `<title>` uniques sur les 39 pages **après correction** (voir §Bugs).
- Meta descriptions toutes uniques. `<link rel=canonical>` présent partout.
- 8 blocs JSON-LD types (WebSite, BreadcrumbList, Place, Organization,
  ItemList, DefinedTermSet) : tous parsables.
- `sitemap.xml` : XML valide, 38 URLs. `robots.txt` présent.

## 8. Fiches YAML
28 fiches valides, tous champs obligatoires présents (`uid`, `nom`,
`sous_titre`, `categorie`) ; `grille` et `sources` présentes sur les 24 fiches
notées ; catégories cohérentes avec le dossier.

## Bug critique corrigé
**Titres SEO dupliqués.** Le lieu `lieux/longo-mai.yml` et l'usufruitier
`usufruitiers/cooperatives-longo-mai.yml` portaient le même `nom`
« Coopératives Longo Maï » → deux `<title>` identiques. `nom` du lieu renommé
en « Longo Maï » (le lieu = le réseau ; l'usufruitier = le collectif autogéré).
Site régénéré : 0 titre dupliqué.

## Problèmes résiduels
Aucun bug. Observations mineures sans gravité :
- `gold-dk` (4.78:1) et `faint/beige` (4.69:1) passent AA de justesse — OK pour
  du texte normal, non bloquant.
- 4 modèles voisins sans bloc « Reliés » — choix éditorial assumé.
