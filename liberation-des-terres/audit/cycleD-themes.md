# Cycle D — Parcours thématiques / dossiers

Étude (lecture seule) : faut-il offrir une porte d'entrée par sujet au corpus
de « Terres Libérées » ? Si oui, sous quelle forme la plus légère ?

---

## 1. État des lieux

Le corpus compte 32 fiches publiées : 8 lieux, 12 porteurs, 7 usufruitiers,
5 modèles voisins. Aujourd'hui il s'explore par **catégorie** (lieux / porteurs /
usufruitiers) et par **classement** (Indice de libération).

Trois axes de lecture transversaux **existent déjà** dans le générateur :

- les **catégories** (rôle dans le montage) ;
- les **paliers** d'Indice (filtre dans les catalogues) ;
- les **montages** (`montage.type` : démembrement, propriété sanctuarisée,
  propriété publique, propriété collective) — déjà exposés en `data-montage` et
  en boutons de filtre dans `render_catalogue`.

Ce qui **n'existe pas** : une entrée par **sujet** (à quoi sert la terre, qui
porte). Or les fiches sont riches d'un sujet implicite, jamais nommé : foncier
agricole, habitat, espace naturel, eau, portage public vs citoyen. Un·e
visiteur·se qui cherche « habitat coopératif » ou « protéger une zone naturelle »
n'a aujourd'hui aucun point d'entrée : il faut lire les fiches une à une.

BIBLIO et « Résidence » utilisaient des dossiers éditoriaux. Mais ce projet est
un fork avec un parti pris **sobre, documentaire, non surchargé** : 32 fiches,
ce n'est pas un volume qui justifie un appareil éditorial lourd.

---

## 2. Verdict : **À FAIRE — version minimale uniquement**

**À faire :** une seule page « Thèmes » discrète, statique, sans filtre JS, sans
nouveau champ dans les YAML.

**À ne pas faire :** dossiers éditoriaux rédigés, tags par fiche, système de
filtres thématiques, entrée « Thèmes » dans la barre de navigation principale.

### Justification

Pour :
- Le corpus se prête naturellement à 5 thèmes nets et non recouvrants (cf. §4) —
  ils ne sont pas plaqués, ils décrivent un fait réel des fiches.
- C'est la **seule** dimension de lecture qui manque : on entre par « quel
  rôle » et par « quelle note », jamais par « quel sujet ». Un·e porteur·se de
  projet pense d'abord en termes de sujet (« je veux installer un paysan »,
  « je veux monter un habitat »).
- Bénéfice SEO réel : une page « Thèmes » crée des ancres et un maillage interne
  par sujet, ce que le site n'a pas.

Contre une version lourde :
- Des tags par fiche imposeraient un champ `themes:` dans 32 YAML, une logique
  de collecte/déduplication, des chips sur chaque carte et fiche : c'est
  exactement la surcharge que le commanditaire refuse, pour 32 entrées.
- Des dossiers éditoriaux supposeraient d'écrire 5 textes d'introduction
  sourcés et de les maintenir — un travail de fond disproportionné en cycle D.
- Le générateur a déjà 4 axes de filtrage (catégorie, palier, montage, région).
  Un 5e mécanisme interactif diluerait la sobriété et alourdirait `list.js`.

La forme retenue ci-dessous coûte **une fonction de rendu et une entrée de
footer** — rien d'autre.

---

## 3. Forme retenue — la plus légère

Une page `themes.html` générée par une nouvelle fonction `render_themes(all_sc, cfg)`.

- **Contenu** : 5 sections, une par thème. Chaque section = un titre (`h2`),
  une phrase de cadrage (1 ligne, factuelle, pas un dossier rédigé), puis la
  grille de cartes existante (`cards_grid`) filtrée sur les fiches du thème.
  On réutilise `card()`, `tri_defs()` et `axis_triangle()` : zéro composant neuf.
- **Répartition** : codée **dans le générateur**, en dur, sous forme d'un
  dictionnaire `{theme_id: [uid, …]}`. Aucun champ ajouté aux YAML, aucune
  migration de données, aucune dépendance.
- **Accès** : un lien dans le **footer** (`page()`), à côté de « Trois régimes »
  et « Grilles d'analyse » — les pages de référence secondaires. **Pas** dans le
  `NAV` principal, qui reste à 6 entrées (parti pris déjà documenté ligne 273
  du générateur). Optionnellement, un renvoi depuis l'accueil dans la `linkrow`
  de la section « howto » (`<a href="themes.html">Explorer par thème →</a>`).
- **Pas de JavaScript**, pas de filtre, pas d'`og:image` dédié : page statique
  classique, comme `regimes.html` ou `glossaire.html`.

Une entité peut apparaître dans **deux thèmes** au plus (ex. Hameau des Buis =
habitat + pédagogie). C'est assumé et géré par le simple fait qu'un uid peut
figurer dans deux listes — pas besoin d'unicité.

---

## 4. Les thèmes concrets et la répartition

Cinq thèmes. Les deux premiers répondent à « à quoi sert la terre », les trois
suivants à « comment elle est portée ». Ils couvrent les 32 fiches sans trou.

### Thème A — Foncier agricole et installation paysanne
*Cadrage : terres cultivées sorties du marché pour installer ou maintenir des paysan·nes.*

| uid | nom | cat. |
|---|---|---|
| reseau-terre-de-liens | Fermes Terre de Liens | lieu |
| lurzaindia | Lurzaindia — terres du Pays Basque | lieu |
| larzac | Terres du Larzac | lieu |
| villarceaux | Bergerie de Villarceaux | lieu |
| nddl | ZAD de Notre-Dame-des-Landes | lieu |
| fondation-terre-de-liens | Fondation Terre de Liens | porteur |
| fonciere-terre-de-liens | Foncière Terre de Liens | porteur |
| lurzaindia-sca | Lurzaindia (SCA) | porteur |
| feve | FEVE — Fermes en Vie | porteur |
| sctl | Société Civile des Terres du Larzac | usufruitier |
| gfa-mutuels | GFA mutuels et solidaires | usufruitier |
| champs-des-possibles | Les Champs des Possibles | usufruitier |
| reneta | RENETA — espaces-test agricoles | usufruitier |

### Thème B — Habitat et logement non spéculatif
*Cadrage : immeubles et écolieux dont la propriété du logement est déconnectée du marché.*

| uid | nom | cat. |
|---|---|---|
| village-vertical | Le Village Vertical | lieu |
| hameau-des-buis | Le Hameau des Buis | lieu |
| longo-mai | Longo Maï | lieu |
| habicoop | Habicoop | porteur |
| fonciere-chenelet | Foncière Chênelet | porteur |
| cooperative-oasis | Coopérative Oasis | usufruitier |
| cooperatives-longo-mai | Coopératives Longo Maï | usufruitier |
| cooperative-habitants-alur | Coopérative d'habitants (loi ALUR) | modèle |
| ofs-brs | Foncier Solidaire (OFS-BRS) | modèle |
| clt-bruxelles | Community Land Trust de Bruxelles | modèle |
| stiftung-trias | Stiftung trias | modèle |
| mietshauser-syndikat | Mietshäuser Syndikat | modèle |

### Thème C — Espaces naturels et protection de l'eau
*Cadrage : foncier naturel ou sensible protégé pour des raisons écologiques.*

| uid | nom | cat. |
|---|---|---|
| conservatoire-littoral | Conservatoire du littoral | porteur |
| federation-cen | Conservatoires d'espaces naturels | porteur |
| scic-terres-de-sources | SCIC Terres de Sources | porteur |
| nddl | ZAD de Notre-Dame-des-Landes | lieu *(aussi thème A — bocage)* |

### Thème D — Portage public et collectivités
*Cadrage : montages où une personne publique détient ou sécurise le foncier.*

| uid | nom | cat. |
|---|---|---|
| larzac | Terres du Larzac | lieu *(aussi thème A)* |
| conservatoire-littoral | Conservatoire du littoral | porteur *(aussi thème C)* |
| scic-terres-de-sources | SCIC Terres de Sources | porteur *(aussi thème C)* |
| federation-cen | Conservatoires d'espaces naturels | porteur *(aussi thème C)* |
| ofs-brs | Foncier Solidaire (OFS-BRS) | modèle *(aussi thème B)* |

### Thème E — Portage citoyen et fondations
*Cadrage : foncier sécurisé par l'épargne, les dons ou une fondation, hors puissance publique.*

| uid | nom | cat. |
|---|---|---|
| fondation-terre-de-liens | Fondation Terre de Liens | porteur *(aussi A)* |
| fonciere-terre-de-liens | Foncière Terre de Liens | porteur *(aussi A)* |
| fonds-la-terre-en-commun | Fonds « La Terre en commun » | porteur |
| fonds-terre-europeenne | Fonds de Terre Européenne | porteur |
| fonciere-antidote | Antidote | porteur |
| fondation-fph | Fondation Charles Léopold Mayer | porteur |
| lurzaindia-sca | Lurzaindia (SCA) | porteur *(aussi A)* |
| feve | FEVE — Fermes en Vie | porteur *(aussi A)* |
| stiftung-trias | Stiftung trias | modèle *(aussi B)* |

**Couverture.** Les 32 fiches apparaissent au moins une fois. Les thèmes A et B
sont les plus volumineux et autoporteurs ; C/D/E se recoupent volontairement
(un foncier peut être public *et* naturel) — ce recoupement est documenté par
les mentions *(aussi …)* et reste lisible tant qu'on ne dépasse pas 2 thèmes par
fiche. Si l'on voulait des thèmes strictement disjoints, fusionner D et E en un
seul thème « Qui porte le foncier : public ou citoyen » serait l'alternative la
plus sobre.

---

## 5. Recommandation de mise en œuvre (pour information, hors périmètre lecture seule)

Si le commanditaire valide :

1. Ajouter `render_themes(all_sc, cfg)` sur le modèle de `render_regimes` —
   réutilise `cards_grid`, dictionnaire `THEMES = {id: (titre, cadrage, [uids])}`
   en tête de fonction.
2. Générer `themes.html` dans `main()` et l'ajouter au sitemap.
3. Ajouter `<a href="themes.html">Thèmes</a>` dans la `foot-links` de `page()`.
4. Optionnel : un renvoi unique depuis la `linkrow` de l'accueil.

Coût estimé : ~60 lignes de générateur, 0 ligne de YAML, 0 ligne de JS, 0
nouveau composant CSS. C'est l'option la plus légère qui apporte réellement la
porte d'entrée par sujet aujourd'hui absente.
