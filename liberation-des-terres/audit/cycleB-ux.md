# Audit UX — parcours, fluidité, allègement — « Terres Libérées »

**Cycle B · Expérience et forme · 2026-05-23**
**Lecture seule — aucun fichier modifié.**

Périmètre : pages de `site/` (index, regimes, lieux, porteurs, usufruitiers,
classement, grilles, modeles, glossaire, methode, suggerer, 404, fiches
`l|p|u|m/*.html`) et fonctions `render_*` de `scripts/generate_site.py`.
Angle exclusif : UX, parcours, fluidité. Objectif du commanditaire : un site
**pratique et fluide, pas trop chargé**. L'état actuel est déjà bon ; il s'agit
d'affiner sans ajouter de poids.

---

## 1. Synthèse

Le site est dans un très bon état. Les recommandations du cycle 2 UX ont été
appliquées : fil d'Ariane complet à trois segments, glossaire, rétro-liens
réciproques entre fiches, filtres palier/montage/région, tri de colonnes au
classement, sélecteur de tri dans les catalogues, message « aucun résultat »,
état `:focus-visible`, lien d'évitement. La fiche détaillée est exemplaire.

Il ne reste donc **aucune friction critique**. Les marges de progrès portent
sur l'**allègement** et la **fluidité fine** : un NAV à 10 entrées un peu long
(le commanditaire en cite 9 — l'écart vient d'un ajout récent), une page
d'accueil qui répète trois fois la même définition du concept, des catalogues
dont la barre de filtres peut occuper beaucoup de hauteur avant la première
carte, et quelques redondances d'information sur la fiche. Aucune de ces
corrections n'ajoute de poids — la plupart en retirent.

---

## 2. Recommandations — priorité CRITIQUE

Aucune. Aucun blocage de parcours, aucun lien mort, aucune page orpheline. Le
site est utilisable de bout en bout.

---

## 3. Recommandations — priorité IMPORTANTE

### I1. NAV à 10 entrées — regrouper pour alléger
**Fichier / fonction :** `generate_site.py` → constante `NAV` (l. 206-217).
Le NAV compte **10 entrées** : Accueil, Lieux, Porteurs, Usufruitiers,
Classement, Trois régimes, Grilles, Modèles voisins, Glossaire, Méthode. C'est
beaucoup pour un menu sur une seule ligne ; sur mobile (`@media max-width:620px`)
il passe en `flex-wrap` et occupe 2-3 lignes, repoussant le contenu. Quatre de
ces entrées (Trois régimes, Grilles, Glossaire, Méthode) sont des pages de
*référence documentaire* consultées une fois, pas des points de navigation
quotidiens — et elles sont **déjà toutes reprises dans le footer**.
**Modification :** réduire le NAV principal aux 6 entrées de parcours —
Accueil, Lieux, Porteurs, Usufruitiers, Classement, Méthode (ou « Comprendre »).
Déplacer Trois régimes / Grilles / Glossaire sous « Méthode » (elles forment un
bloc « comprendre la grille ») ou les laisser uniquement au footer, où elles
figurent déjà. « Modèles voisins » : voir I2. Gain : menu tenant sur une ligne,
hiérarchie plus lisible (faire / comprendre), zéro perte d'accès.

### I2. « Modèles voisins » : entrée de NAV ambiguë et redondante
**Fichier / fonction :** `NAV`, `render_index`, `render_catalogue` (branche
`cat == "modele"`).
« Modèles voisins » occupe une entrée de NAV pleine alors que c'est un contenu
*secondaire et explicitement hors classement*. L'accueil lui consacre déjà une
section dédiée en bas de page avec lien « Voir les modèles voisins → ». Garder
en plus une entrée de NAV gonfle le menu et place sur le même plan un catalogue
principal (Lieux) et un corpus de comparaison.
**Modification :** retirer « Modèles voisins » du NAV. L'accès reste assuré par
la section d'accueil et par un renvoi depuis `methode.html` (qui parle déjà des
modèles estimés). Le menu gagne une entrée.

### I3. Accueil — la définition du concept est répétée trois fois
**Fichier / fonction :** `render_index` (l. 1533-1610).
La même idée — « libérer la terre = dissocier propriété d'intérêt général /
usage non lucratif » — est formulée **trois fois** sur la page d'accueil :
dans le `hero-lead`, dans l'étape 1 du bloc `howto` (« Comprendre le concept »),
puis dans la section `explain` (« Le principe »). C'est de la charge inutile :
le visiteur scrolle sur du déjà-lu avant d'atteindre les catégories et le
classement.
**Modification :** fusionner. Garder le `hero` (accroche) + le bloc `howto` en
3 étapes (pédagogie de parcours, utile). **Supprimer la section `explain`
« Le principe »** : son seul apport propre est la triade de liens
régimes/glossaire/méthode, qui peut être déplacée en fin du bloc `howto` ou
dans l'étape 1. Résultat : une page d'accueil plus courte, sans redite, qui
amène plus vite à l'action (catégories, classement).

### I4. Catalogues — la barre de filtres pousse les cartes très bas
**Fichier / fonction :** `render_catalogue`, blocs `toolbar` + `filter-bar`
(l. 910-936).
Sur `lieux.html`, avant la première carte, l'utilisateur traverse : H1, lead +
lien, toolbar (recherche + tri + compteur), puis **trois rangées de filtres**
(Palier : 6 boutons ; Montage : 4 ; Région : 7), puis une légende tri-axes.
Pour 8 lieux seulement, la zone de contrôle est presque aussi haute que les
résultats — beaucoup de scroll pour peu de contenu, et impression de page
« chargée » contraire à l'objectif.
**Modification (sans poids) :**
- Replier `filter-bar` derrière un `<details>` « Filtres avancés » fermé par
  défaut (le tri et la recherche, plus courants, restent visibles). Le palier
  et le montage ne servent qu'à un usage de tri fin.
- Ou, plus simple : ne générer une rangée de filtres que si elle compte
  **≥ 4 valeurs** et concerne **≥ 8 entrées** — sur un catalogue de 7-8 fiches,
  filtrer par 6 paliers a peu d'intérêt et alourdit visuellement.
- Déplacer la légende tri-axes juste sous le H1 (info de lecture) plutôt qu'au
  ras des cartes, ou la fusionner avec le lead.

### I5. Fiche — l'indice et le palier apparaissent trois fois dans le premier écran
**Fichier / fonction :** `render_fiche`, `score_block` → `idl_badge(big=True)`
+ `axis_triangle` + `axis_bar` + `idl_scale` (l. 635-647).
Le `score-panel` empile : l'anneau d'indice (chiffre + palier), le triangle
tri-axes, les trois barres A/B/C chiffrées, **et** la jauge linéaire `idl-scale`
avec ses bandes de palier. Triangle et barres disent la même chose (A/B/C) sous
deux formes ; l'anneau et la jauge disent tous deux l'indice + le palier. C'est
redondant et dense pour un premier bloc.
**Modification :** garder l'anneau (synthèse) + les barres chiffrées (précision,
seule source accessible). Le **triangle** peut être déplacé plus bas (près de la
section « Reliés dans l'annuaire » où il sert vraiment à comparer) ou réduit.
La `idl-scale` fait doublon avec l'anneau : la conserver seulement si elle
apporte le positionnement par palier — sinon la retirer. Objectif : un bloc de
score lisible d'un coup d'œil, pas quatre visualisations concurrentes.

---

## 4. Recommandations — priorité MINEURE

### M1. NAV mobile sans repli — prévoir un menu compact
**Fichier / fonction :** `CSS`, `@media(max-width:620px)` (l. 2123-2133) ;
`.topnav`.
Sous 620 px le NAV reste en `flex-wrap` : 10 liens sur 2-3 lignes sous le logo.
Fonctionnel mais lourd en haut de chaque page.
**Modification :** si I1/I2 ramènent le NAV à 6 entrées, le wrap mobile devient
acceptable. Sinon, prévoir un `<details>`/`<summary>` (« Menu ») purement CSS,
sans JS — cohérent avec un site statique léger.

### M2. Fiche — backlink redondant avec le fil d'Ariane
**Fichier / fonction :** `render_fiche`, variable `backlink` (l. 806-808).
La fiche commence par un fil d'Ariane (Accueil › Catégorie › Fiche) et se
termine par `← Retour aux {catégorie} · Voir le classement`. Le premier lien du
backlink double exactement le 2e segment du fil d'Ariane.
**Modification :** alléger le backlink en ne gardant que « Voir le classement »
et éventuellement « Proposer un lieu / signaler une erreur » — le retour
catégorie est déjà couvert par le fil d'Ariane en haut. Mineur, mais c'est une
redite de plus.

### M3. Catalogue — légende tri-axes répétée alors qu'elle est sur chaque carte
**Fichier / fonction :** `render_catalogue`, bloc `axe-legend cat-legend`
(l. 933-936) ; `card`.
La légende A/B/C est affichée en pleine largeur sous les filtres, puis chaque
carte réaffiche « A · », « B · », « C · » devant ses barres. La légende
explicite est utile une fois, mais sa position actuelle (juste avant les cartes,
pleine largeur) ajoute une bande. Cf. I4 : la fusionner au lead.

### M4. Compteur d'entrées — `aria-live` sur un nombre déjà visible
**Fichier / fonction :** `render_catalogue`, `<span class="count">` (l. 924).
Détail : `aria-live="polite"` sur le compteur est correct, mais le libellé
« entrée(s) » n'est pas dans la zone live actualisée (seul `#cnt` change). Au
filtrage, un lecteur d'écran annonce « 3 » sans contexte.
**Modification :** englober « entrées » dans la zone `aria-live`, ou annoncer
« 3 entrées affichées » via un texte de statut dédié (le classement le fait
déjà avec `#sort-status`).

### M5. Page `suggerer.html` absente du NAV et du parcours principal
**Fichier / fonction :** `NAV`, `render_suggerer`.
« Proposer un lieu » n'existe qu'en lien de footer. C'est défendable (action
secondaire), mais c'est le seul point de contact / contribution du site. Un
renvoi en fin de fiche (« cette fiche est incomplète ? → signaler ») ou en bas
des catalogues fluidifierait la boucle de contribution sans charger le NAV.
**Modification :** ajouter un lien discret vers `suggerer.html` en fin de fiche
(cf. M2) et/ou sous la grille de cartes des catalogues.

### M6. `methode.html` — page longue, sans sommaire
**Fichier / fonction :** `render_methode`.
La page Méthode enchaîne 5 sections denses (ce que recense l'annuaire, l'Indice,
nature juridique, limites, état du corpus) sur un seul long scroll. Si I1
regroupe régimes/grilles/glossaire sous « Méthode », elle s'allonge encore.
**Modification :** ajouter en tête un mini-sommaire ancré (`<nav>` de liens vers
les `id` de section) — quelques lignes, zéro poids, navigation immédiate dans
une page de référence.

### M7. Cartes — `card` entière non cliquable
**Fichier / fonction :** `card` (l. 568-580).
Seul le titre `<h3><a>` est cliquable. Sur des cartes riches (triangle, barres,
meta), l'utilisateur clique souvent la zone visuelle sans atteindre le lien.
**Modification :** rendre toute la carte cliquable — soit en étendant la zone
de clic du lien via un pseudo-élément `::after` en `position:absolute` sur la
`.card` (technique « stretched link », zéro JS, zéro poids), soit en s'assurant
que le hover de carte (déjà stylé) accompagne un lien pleine carte. Améliore
nettement la fluidité au clic.

---

## 5. Parcours utilisateurs — verdict par profil

- **Visiteur novice** : hero clair, bloc « Comment lire » en 3 étapes efficace,
  glossaire accessible. Parcours bon. Seule gêne : redites de l'accueil (I3) et
  NAV un peu intimidant (I1).
- **Porteur de projet** : trouve catégories et méthode ; pas de comparateur
  dédié, mais les rétro-liens et le profil tri-axes sur les chips suffisent à
  comparer de proche en proche. Parcours bon.
- **Donateur** : classement triable par axe, paliers colorés, filtres — l'aide
  à la décision est là. Parcours bon.
- **Juriste** : méthode, grilles, régimes, glossaire complets et reliés.
  Parcours bon ; gagnerait un sommaire sur Méthode (M6).

Aucun parcours n'est cassé. Les frictions restantes sont des **frictions de
densité**, pas de navigation.

---

## 6. Points forts à conserver

- Fil d'Ariane complet et cohérent sur toutes les fiches.
- Filtres + tri des catalogues et du classement : fonctionnels, accessibles,
  avec message « aucun résultat ».
- Rétro-liens réciproques entre fiches : le maillage interne est solide.
- Fiche détaillée : ordre des sections logique et stable.
- `:focus-visible`, skiplink, `aria-sort`, `aria-live` : socle d'accessibilité
  en place.
- Code couleur A/B/C et hiérarchie typographique constants partout.

---

## 7. Priorisation pour intégration

À intégrer en priorité, dans cet ordre (chacun **allège** le site) :

1. **I1 + I2** — ramener le NAV de 10 à 6 entrées (regrouper la doc, retirer
   « Modèles voisins »). Effet immédiat sur la sensation de légèreté.
2. **I3** — supprimer la section « Le principe » de l'accueil (redite x3).
3. **I4** — replier la barre de filtres des catalogues (`<details>`) ou la
   conditionner au volume d'entrées.
4. **I5** — désempiler le bloc de score de la fiche (triangle déplacé/réduit).
5. **M7** — carte entièrement cliquable (gain de fluidité au clic, zéro poids).
6. M1, M2, M3, M5, M6 — finitions d'allègement.
