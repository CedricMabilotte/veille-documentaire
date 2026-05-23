# Cycle C — Audit accessibilité WCAG 2.1 AA

Audit en lecture seule du site statique « Terres Libérées ».
Périmètre : `scripts/generate_site.py` (source unique), `site/assets/style.css`,
`site/assets/list.js`, pages générées (`site/`). Référentiel : WCAG 2.1 niveau AA.

Le site a déjà reçu plusieurs passages a11y (skip link, `:focus-visible`,
`role="img"` sur SVG, `scope` sur tableaux, `aria-live`, cibles tactiles mobiles).
Cet audit vérifie les points listés dans la commande et hiérarchise ce qui reste.

Codes : **Critique** (blocage ou échec AA franc) · **Importante** (échec AA
limité ou risque sérieux) · **Mineure** (bonne pratique, confort).

---

## Synthèse

| # | Sévérité | Sujet | Critère WCAG |
|---|----------|-------|--------------|
| C1 | Critique | Tri du catalogue (`<select>`) sans annonce + tri visuel non synchronisé | 4.1.3, 1.3.1 |
| C2 | Critique | Filtres `.fbtn` : faux boutons d'état, pas de `aria-pressed` | 4.1.2 |
| I1 | Importante | Contraste : nombre d'IdL coloré (paliers clairs) sous 4.5:1 | 1.4.3 |
| I2 | Importante | Contraste : couleurs d'axe utilisées comme texte / fond de barre | 1.4.3, 1.4.11 |
| I3 | Importante | Filtres catalogue : changement de résultats non annoncé | 4.1.3 |
| I4 | Importante | `<select>` de tri sans `<label>` associé visible (id `sort`) | 1.3.1, 3.3.2 |
| I5 | Importante | Carte « stretched-link » : triangle SVG focusable interactif masqué | 2.4.3, 1.3.1 |
| M1 | Mineure | Sigles (SCTL, BRS, GFA, SCIC, RUP, FPH…) sans `<abbr>` | 3.1.4 |
| M2 | Mineure | Liens « → » répétés, intitulés peu distinctifs hors contexte | 2.4.4 |
| M3 | Mineure | `lang` des termes étrangers (Mietshäuser Syndikat…) non balisé | 3.1.2 |
| M4 | Mineure | `tri-lab` texte blanc sur sommets colorés < 4.5:1 (non bloquant) | 1.4.11 |
| M5 | Mineure | Liens externes `target="_blank"` sans indication | 3.2.5 (confort) |

Points **conformes** confirmés : un seul `<h1>` par page ; hiérarchie Hn correcte ;
landmarks `header`/`main`/`footer`/`nav` présents et nommés ; skip link
fonctionnel ; `:focus-visible` global visible (outline 2px `--ink`) ; SVG
factorisé via `<use>` conserve l'accessibilité (voir §SVG) ; tableau comparatif
des régimes correctement structuré (voir §Tableau régimes) ; `aria-live` sur le
compteur ; tableau de classement avec `aria-sort` et vrais `<button>`.

---

## 1. Contrastes

Fond de référence : `--paper #f5f2e9`, cartes `--card #fffdf6`.

### I1 — Nombre d'Indice coloré illisible sur les paliers clairs · Critique de contraste · WCAG 1.4.3

`generate_site.py` → `idl_badge()` (l. 509-510) génère `<text class="idl-num">`
dont la couleur est `--pal` (couleur du palier). CSS `.idl-num{fill:var(--pal)}`
(l. 1865) et `.idl-cell b{color:var(--pal)}` (l. 2039).

Les couleurs de palier (`config/ranking.yml`) :

- `engage` `#b08431` sur carte `#fffdf6` → ratio ≈ **3.5:1** — échec AA (seuil 4.5:1).
- `solide` `#4a7a3a` sur carte → ratio ≈ **4.3:1** — échec AA de justesse.
- `partiel` `#bc5d3a` sur carte → ratio ≈ **3.6:1** — échec AA.

Le chiffre de l'Indice est une information primaire ; il échoue pour trois des
cinq paliers. Le `<text>` du badge fait ~13 px (gros badge ~26 px) : seul le gros
badge `idl-badge.big` (≥ 24 px → texte large, seuil 3:1) passe pour `solide` et
`engage` ; le petit badge sur les cartes échoue.

**Correctif.** Dans `ranking.yml`, foncer les couleurs de palier servant de
**texte**, ou — plus simple et sans toucher la charte — découpler couleur de
remplissage et couleur de texte : ajouter une variante foncée par palier.
Concrètement, dans `idl_badge()` et `idl-cell`, n'utiliser `--pal` que pour le
trait de l'anneau / le filet, et fixer le **chiffre** sur `var(--ink)`
(`#221f1a`, ratio > 12:1). La couleur reste portée par l'anneau. Modifier
`.idl-num{fill:var(--pal)}` → `.idl-num{fill:var(--ink)}` (l. 1865) et
`.idl-cell b{color:var(--pal)}` → `color:var(--ink)` (l. 2039).

### I2 — Couleurs d'axe : contraste de texte et de composants · WCAG 1.4.3 / 1.4.11

Les couleurs d'axe (`ranking.yml`) : A `#4a7a3a`, B `#bc5d3a`, C `#36748a`.

- **Barres d'axe** (`axis_bar`, l. 348-352) : `axis-fill` est un remplissage de
  jauge sur fond `--beige-dk #e6ddc6`. B `#bc5d3a` vs `#e6ddc6` ≈ **2.9:1** —
  échec du seuil 3:1 pour un composant graphique porteur d'information (1.4.11).
  La valeur chiffrée est doublée à côté (`axis-val`), donc l'information n'est
  pas perdue ; à traiter comme **Importante** et non Critique.
- **Pastilles `.axe-dot`** (l. 2022-2028) : petits disques de 0.62rem côte à
  côte avec un libellé texte ; décoratifs, l'information est dans le texte
  adjacent. Conforme.
- **Cellules d'axe du classement** (`cell()`, l. 1026-1030) : `--ac` colore une
  mini-barre de 3 px ; la valeur est en chiffres. Conforme (la barre « double »).

**Correctif.** Pour les barres d'axe : foncer légèrement B et C **uniquement
pour la jauge** (p. ex. utiliser `--terra-dk`/`--blue-dk` comme `background` de
`axis-fill`), ou ajouter un liseré 1px `--ink` sur `.axis-fill` pour garantir le
3:1 de délimitation. Le chiffre restant affiché, l'urgence est modérée.

### M4 — Lettres d'axe blanches sur sommets du triangle · WCAG 1.4.11

`tri_defs()` / `axis_triangle()` posent `<text class="tri-lab">` (blanc
`--paper`) sur les cercles de sommet colorés. Sur `#bc5d3a` : ≈ 3.7:1 ; sur
`#36748a` : ≈ 3.9:1 — sous 4.5:1. Le SVG porte `role="img"` + `aria-label`
décrivant les trois axes chiffrés : ce texte interne est **non essentiel** pour
un lecteur d'écran. Reste un inconfort visuel pour malvoyants.

**Correctif (Mineure).** Ajouter un fin halo : `.tri-lab{paint-order:stroke;
stroke:rgba(34,31,26,.55);stroke-width:1.5px}` (l. 1853), ou agrandir le rayon
des cercles. Aucune incidence sémantique.

### Points de contraste conformes vérifiés

- `--muted #5f5849` sur paper ≈ 6.3:1 — OK (texte courant secondaire).
- `--faint #6e6655` sur paper ≈ 4.5:1 — limite mais conforme pour texte normal
  (`.completude`, `.card-meta`, `.note`). Ne pas l'assombrir davantage de fond.
- Tags : texte blanc sur `tag-modele` `--gold-dk #8a6420` ≈ 4.9:1 — OK ;
  les trois autres tags (verts/terra/bleu foncés) > 5:1 — OK.
- `.crit-partiel` `--gold-dk` ≈ 4.9:1 — OK.
- `.fbtn.active` texte `--paper` sur `--green-dk #356026` > 7:1 — OK.

---

## 2. Sémantique : titres, hiérarchie, landmarks

### Conforme

- **Un seul `<h1>` par page** : vérifié sur `page()` (gabarit) et chaque
  `render_*`. Fiches : `h1` dans `.fiche-head`. Catalogues, classement, méthode,
  régimes, grilles, glossaire, accueil, suggérer, 404 : un `h1` chacun.
- **Hiérarchie Hn** : `h2.sec` pour les sections, `h3` pour sous-blocs
  (axes, analyse, familles). Pas de saut de niveau constaté. Les `h3` des
  `.regime-card`, `.axe-card`, `.an-col`, `.step` sont bien sous un `h2`.
- **Landmarks** : `header.masthead`, `main.wrap#contenu`, `footer.footer`,
  `nav.topnav`, `nav.crumb` (avec `aria-label="Fil d'Ariane"`),
  `nav.page-toc` (avec `aria-label="Sommaire de la page"`). Le fil d'Ariane et
  le sommaire portent un `aria-label` distinct — bonne pratique respectée.
- **`aria-current="page"`** sur l'élément courant du fil d'Ariane. La nav
  principale marque l'actif par classe `.active` seulement — voir M ci-dessous.

### Mineure — nav principale sans `aria-current`

`page()` (l. 234-237) génère le lien actif avec `class="active"` uniquement.
**Correctif.** Ajouter `aria-current="page"` sur le lien actif de `.topnav`
(en plus de la classe), pour les lecteurs d'écran. WCAG 1.3.1.

---

## 3. SVG factorisés via `<defs>`/`<use>`

`tri_defs()` (l. 388-408) émet un SVG `width="0" height="0"` portant
`aria-hidden="true"` et `focusable="false"`, contenant `<defs><g id="tri-base">`.
`axis_triangle(compact=True)` (l. 448-452) émet le SVG visible avec
`role="img" aria-label="..."` puis `<use href="#tri-base"/>`.

**Verdict : conforme.** Le SVG de `<defs>` est correctement masqué
(`aria-hidden`) ; le SVG visible conserve `role="img"` et un `aria-label`
complet (profil tri-axes chiffré). Le `<use>` n'importe que des formes
décoratives (cadre, grille, sommets) — il n'introduit pas de contenu
accessible parasite et n'a pas besoin de `role`/`aria-label` propre.
La version pleine taille (fiche) est un SVG autonome également `role="img"`.

Réserve **Mineure** : le SVG de `<defs>` est en `position:absolute` sans
`width/height` CSS ; certains anciens lecteurs pourraient le survoler — le
`aria-hidden="true"` neutralise ce risque. Rien à corriger.

---

## 4. Tableau comparatif des trois régimes

`render_regimes()` → `table` (l. 1234-1241).

**Verdict : conforme.**

- `<caption class="visually-hidden">` présent et descriptif.
- `<thead>` avec quatre `<th scope="col">`.
- Première colonne de chaque ligne : `<th scope="row">` (généré l. 1231) —
  en-tête de ligne correctement déclaré.
- Enveloppé dans `.table-scroll` ; en mobile la colonne `th[scope=row]` est
  `position:sticky` (l. 2183-2184), `min-width:34rem` pour défilement propre.

Réserve **Mineure** : le `.table-scroll` des régimes n'a **pas** de
`tabindex="0"` + `role="region"` + `aria-label`, contrairement au
`.table-scroll` du classement (`render_classement`, l. 1075). Un tableau qui
défile horizontalement devrait être atteignable au clavier pour le scroll.
**Correctif.** Aligner `render_regimes()` sur `render_classement()` :
`<div class="table-scroll" tabindex="0" role="region" aria-label="Tableau
comparatif des trois régimes">`. Idem pour les `.table-scroll` des grilles
(`render_grilles`, l. 1146) et de la grille de fiche (`render_fiche`, l. 791).
WCAG 2.1.1.

---

## 5. Cartes en « stretched-link » et navigation clavier

`card()` (l. 632-643) : `<li class="card">` en `position:relative`, titre
`<h3><a class="card-link">`, et `.card-link::after{position:absolute;inset:0}`
(CSS l. 1827) étire la zone cliquable sur toute la carte.

### Bon

- Un **seul** élément focusable par carte (le lien du titre) : conforme à
  l'intention « stretched link ». `:focus-visible` global s'applique au lien.
- `.card:focus-within{border-color}` (l. 1821) donne un retour visuel quand le
  lien interne reçoit le focus — utile car le `::after` n'a pas de contour
  propre.

### I5 — Le contour de focus ne couvre que le titre, pas la carte · WCAG 2.4.7 (confort) / 2.4.11

Le lien est `.card-link` ; son `:focus-visible` dessine un outline autour du
**texte du titre** seulement, alors que la zone cliquable est toute la carte.
Le focus visible existe (`focus-within` change la bordure) mais l'indicateur
réglementaire (outline) ne reflète pas la cible réelle. C'est un défaut de
**qualité** d'indicateur de focus, pas une absence.

**Correctif.** Porter l'outline sur la carte entière au focus du lien :
```
.card:focus-within{outline:2px solid var(--ink);outline-offset:2px;}
.card-link:focus-visible{outline:none;}
```
(remplacer / compléter l. 1821 et neutraliser l'outline du lien interne, le
relais visuel étant assuré par la carte). WCAG 2.4.7.

### Vérifié — triangle SVG dans la carte non focusable

`.card-viz` contient `axis_triangle(compact=True)`. Le SVG `<use>` n'a pas de
`focusable` explicite. Sous IE/anciens Edge, les SVG peuvent être tabbables.
**Correctif (Mineure mais simple).** Ajouter `focusable="false"` au `<svg>`
compact dans `axis_triangle()` (l. 449-450), comme c'est déjà fait pour le SVG
de `tri_defs()` et le badge `idl-ring`. Évite un arrêt de tabulation parasite
dans une carte censée n'en avoir qu'un.

---

## 6. `assets/list.js` — annonces de tri et de filtre

### 6a. Catalogues (`lieux/porteurs/usufruitiers/modeles`)

Le `<select id="sort">` (`render_catalogue`, l. 982-987) et `doSort()`
(`list.js` l. 31-38).

#### C1 — Le tri par `<select>` réordonne le DOM sans aucune annonce · WCAG 4.1.3 / 1.3.1 · Critique

`doSort()` fait `grid.appendChild(c)` pour chaque carte : l'ordre visuel et
l'ordre DOM changent, mais **rien n'est annoncé** à un lecteur d'écran et il
n'existe **aucun `aria-live`** pour le tri (le `aria-live="polite"` existant est
sur le **compteur** `#cnt`, qui ne change pas lors d'un tri). Un utilisateur
non-voyant ne sait pas que la liste a été réordonnée.

Comparaison : la page **classement** fait bien les choses — `#sort-status`
`role="status"` annonce « Tableau trié par… ordre… » (`list.js` l. 96-100). Le
catalogue n'a pas l'équivalent.

**Correctif.**
1. Dans `render_catalogue()`, ajouter après la toolbar un
   `<p id="sort-status" role="status" class="visually-hidden"></p>`.
2. Dans `list.js`, `doSort()` : après le réordonnancement, écrire
   `var s=document.getElementById('sort-status'); if(s)
   s.textContent='Liste triée : '+sort.options[sort.selectedIndex].text+'.';`.

#### I3 — Filtres `.fbtn` et recherche : nombre de résultats annoncé partiellement · WCAG 4.1.3 · Importante

`apply()` (l. 16-30) met à jour `#cnt` (qui est `aria-live="polite"` — bien) et
masque/affiche `#noresult` (`role="status"` — bien). **Mais** `apply()` fait
`cnt.innerHTML='<b>'+n+'</b> entrée…'` : remplacer le `innerHTML` complet d'une
région live peut, selon le lecteur, ne pas déclencher l'annonce de façon fiable,
ou annoncer le balisage. Préférer ne mettre à jour que le **texte**.

**Correctif.** Garder le `<b>` statique et n'écrire que le nombre :
structurer `#cnt` en `<span id="cnt" aria-live="polite"><b id="cntn">N</b>
<span id="cntl">entrées affichées</span></span>` et, dans `apply()`, faire
`cntn.textContent=n; cntl.textContent=' entrée'+(n>1?'s':'')+' affichée…';`.
Évite l'injection de HTML dans une région live.

#### C2 — Les filtres `.fbtn` sont des `<button>` mais sans état programmatique · WCAG 4.1.2 · Critique

`render_catalogue()` génère `<button class="fbtn" data-fk=… data-fv=…>` ; l'état
sélectionné est porté **uniquement** par la classe `.active` (`list.js`
l. 41-49). Aucun `aria-pressed`. Un lecteur d'écran annonce « bouton Palier » sans
dire s'il est actif ; l'utilisateur ne sait pas quel filtre est appliqué.

Ces boutons fonctionnent en groupe à choix exclusif (un seul actif par `data-fk`)
— ils se comportent comme des boutons radio. Deux corrections possibles :

**Correctif (recommandé, minimal).** Traiter chaque `.fbtn` comme un bouton à
bascule : ajouter `aria-pressed="true"` sur le bouton actif, `"false"` sinon.
- Dans `render_catalogue()`, émettre `aria-pressed="true"` sur le bouton « Tous »
  / « Toutes » initialement actif, `aria-pressed="false"` sur les autres.
- Dans `list.js`, le gestionnaire de clic des `.fbtn` (l. 41-49) : à la place
  de (ou en plus de) `classList`, faire
  `document.querySelectorAll('.fbtn[data-fk="'+k+'"]').forEach(x=>
  x.setAttribute('aria-pressed','false'))` puis
  `b.setAttribute('aria-pressed','true')`.
- Idem pour les boutons de filtre catégorie du **classement** (`data-f`,
  l. 66-76) : ils ont le même défaut.

**Alternative plus correcte sémantiquement.** Envelopper chaque rangée de
filtres dans un `<div role="group" aria-label="Filtrer par palier">` (le
`.filter-lab` peut servir d'`aria-labelledby`). Le `render_catalogue` produit
déjà `.filter-row` avec `.filter-lab` — il suffit d'ajouter `role="group"` et de
lier le label.

### 6b. Classement (`classement.html`)

Le tri de colonnes est **déjà bien fait** : `<th class="sortable"
aria-sort="none">` contenant un vrai `<button class="th-sort">` avec
`aria-label` explicite ; `sortBy()` met à jour `aria-sort`
(`ascending`/`descending`/`none`) et `#sort-status` `role="status"` annonce le
tri. **Conforme** WCAG 4.1.2 / 4.1.3.

Réserve **Mineure** : le filtre de catégorie du classement utilise les mêmes
`.fbtn` sans `aria-pressed` (voir C2) — à corriger en même temps.

---

## 7. `<select>` de tri — étiquette · WCAG 1.3.1 / 3.3.2

### I4 — `<label for="sort">` présent mais formulation et `<select id="q">`

`render_catalogue()` : le champ de recherche `<input type="search" id="q">` a un
`aria-label="Filtrer par nom"` — **conforme**. Le `<select id="sort">` a un
`<label class="sort-lab" for="sort">Trier :</label>` — **conforme** également.

Reclassé : ce point est **conforme**. Reste une **Mineure** : sur la page
**classement**, le filtre catégorie est précédé d'un `<label>Filtrer par
catégorie :</label>` **sans `for`** et sans groupe — ce `<label>` orphelin
n'est rattaché à rien (les cibles sont des `<button>`, qu'un `<label>` ne peut
pas étiqueter). **Correctif.** Remplacer ce `<label>` par un `<span>` ou un
`role="group" aria-label="Filtrer par catégorie"` sur le conteneur (voir C2,
alternative).

---

## 8. Cibles tactiles · WCAG 2.5.5 (AAA) / 2.5.8 (AA, 24px)

- **Nav principale** : `.topnav a` a `min-height:24px` en desktop, élargi à
  `min-height:44px` + `display:flex` en mobile (l. 2170-2171) — conforme AA
  (24px) partout, AAA en mobile.
- **`.fbtn`** : `min-height:32px` desktop, `40px` mobile — conforme AA.
- **`.th-sort`** : `width:100%` + `padding:.5rem` → hauteur ~34px — conforme AA.
- **Liens inline** (`.foot-links a`, `.page-toc a`, liens de prose) : hauteur de
  ligne ~1.5 ; cibles fines mais conformes à l'exception « inline » de 2.5.8.

Réserve **Mineure** : `.crumb a` (fil d'Ariane) et `.linkrow a` sont des liens
texte serrés ; conformes au titre de l'exception inline, rien à corriger.

**Verdict : conforme AA.**

---

## 9. Navigation clavier (synthèse)

- Skip link `.skiplink` → `#contenu` : fonctionnel, visible au focus.
- Ordre de tabulation : header → nav → contenu → footer, logique (pas de
  `tabindex` positif).
- `:focus-visible` global : outline 2px `--ink`, offset 2px — visible sur fond
  clair. **Conforme** 2.4.7.
- `.filter-details > summary` : `<details>` natif, ouvrable au clavier — OK.
- **Carte stretched-link** : voir I5 (indicateur de focus à porter sur la carte).
- **Triangle SVG des cartes** : ajouter `focusable="false"` (voir §5).
- Tri de colonnes du classement : vrais `<button>`, activables Entrée/Espace.

---

## 10. `<abbr>` et `lang`

### M1 — Sigles non explicités · WCAG 3.1.4 (AAA, mais recommandé)

Le corpus emploie de nombreux sigles : SCTL, BRS, OFS, GFA, SCIC, SCA, RUP, FPH,
CEN, ALUR, CLT… `generate_site.py` ne génère **aucun `<abbr title="…">`**
(grep : 0 occurrence). Le glossaire définit certains termes mais pas tous les
sigles, et n'est pas lié contextuellement.

**Correctif (Mineure).** 3.1.4 est AAA — non requis pour AA. Recommandation
pragmatique : à la première occurrence par page, baliser les sigles structurants
en `<abbr title="Société Civile des Terres du Larzac">SCTL</abbr>`. Comme le
texte vient des fiches YAML, le plus réaliste est une petite table de sigles
appliquée à la volée dans `clean()`/`e()` n'est pas souhaitable (risque sur
contenu déjà échappé) ; préférer un champ optionnel `sigles:` par fiche, ou
laisser tel quel et renvoyer vers le glossaire. Faible priorité.

### M3 — Termes en langue étrangère · WCAG 3.1.2

Les modèles voisins comportent des noms étrangers (Mietshäuser Syndikat,
Stiftung trias, Community Land Trust de Bruxelles…). Le document est
`lang="fr"` ; les passages étrangers ne sont pas balisés `lang="de"` /
`lang="en"`. Pour un lecteur d'écran, la prononciation sera francisée.

**Correctif (Mineure).** Sur les fiches « modèle » concernées, envelopper le
**nom propre étranger** dans `<span lang="de">…</span>` etc. Réalisable via un
champ `langue_nom:` optionnel dans les YAML des modèles, lu par `render_fiche()`
et `card()`. Impact limité (peu de fiches).

---

## 11. Divers — Mineures

- **M2 — Liens « → » répétés.** « Comprendre la méthode → », « Voir le
  classement → », « Comprendre la grille → » : intitulés corrects et
  distinctifs en contexte ; conformes 2.4.4. Pas d'action requise (la flèche
  est du texte, pas une image — pas de problème de nom accessible).
- **M5 — Liens externes `target="_blank"`.** `render_fiche()` génère les liens
  de sources et le lien « Site » avec `target="_blank" rel="noopener"` sans
  signaler l'ouverture dans un nouvel onglet. WCAG 3.2.5 (AAA) suggère de
  prévenir. **Correctif optionnel** : ajouter une mention masquée
  `<span class="visually-hidden"> (nouvelle fenêtre)</span>` dans ces liens.
- **`prefers-reduced-motion`** : le CSS définit plusieurs `transition` (cartes,
  nav, boutons). Aucune animation forte ; les transitions de couleur/ombre
  ≤ .15s ne posent pas de problème vestibulaire. Pas d'action requise, mais une
  règle `@media(prefers-reduced-motion:reduce){*{transition:none!important}}`
  serait un plus (Mineure).

---

## Plan d'action priorisé

**Critique — à corriger d'abord :**
1. **C1** — Ajouter `#sort-status role="status"` au catalogue + annonce du tri
   dans `doSort()` (`render_catalogue` + `list.js`).
2. **C2** — `aria-pressed` sur les `.fbtn` (filtres catalogue + filtres
   catégorie du classement), dans le générateur et `list.js`.

**Importante :**
3. **I1** — Chiffre d'IdL en `var(--ink)` (`.idl-num`, `.idl-cell b`) au lieu de
   `--pal`.
4. **I2** — Barres d'axe : foncer/cerner `axis-fill` pour atteindre 3:1.
5. **I3** — `apply()` : mettre à jour le texte du compteur, pas l'`innerHTML`.
6. **I5** — Porter l'outline de focus sur `.card` entière (stretched-link).
7. Tableaux qui défilent (régimes, grilles, grille de fiche) : `tabindex="0"
   role="region" aria-label` comme le classement.

**Mineure :**
8. `aria-current="page"` sur le lien actif de la nav principale.
9. `focusable="false"` sur le SVG triangle compact des cartes.
10. `<label>` orphelin du filtre classement → `role="group"`.
11. `<abbr>` / `lang` des sigles et noms étrangers (faible priorité, AAA).
12. Halo sur `.tri-lab` ; `prefers-reduced-motion` ; mention « nouvelle
    fenêtre » sur liens externes.

Toutes les corrections se font dans **trois fichiers** : `scripts/generate_site.py`
(gabarits, `idl_badge`, `axis_triangle`, `render_catalogue`, `render_regimes`,
`render_grilles`, `render_fiche`, constante `CSS`, constante `LIST_JS`). Le site
étant entièrement régénéré, aucune retouche directe dans `site/` n'est pertinente.
