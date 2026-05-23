# Cycle 3 — Audit d'accessibilité (WCAG 2.1 AA)

Site « Terres Libérées ». Audit en lecture seule du générateur
`scripts/generate_site.py` (HTML + constante `CSS`) et des pages produites
(`site/`). Les ratios de contraste sont des estimations calculées sur la
formule WCAG (luminance relative) ; à vérifier avec un outil de mesure.

Palette de référence (`:root`, `generate_site.py` l.1338-1344) :
`--paper #f5f2e9`, `--card #fffdf6`, `--ink #221f1a`, `--muted #5f5849`,
`--faint #938a78`, `--green #4a7a3a`, `--terra #bc5d3a`, `--blue #36748a`,
`--gold #b0843a`.

Le site part d'une base saine : `lang="fr"`, `skiplink`, landmarks
`header/main/nav/footer`, un seul `h1` par page, `:focus-visible`,
`viewBox`/`role="img"` sur les SVG, `aria-sort` sur le tableau triable.
Les corrections ci-dessous comblent les écarts restants.

---

## CRITIQUE

### C1 — Contraste insuffisant de `--faint` sur fond clair
**Critère :** WCAG 1.4.3 Contraste (AA).
**Fichier :** `generate_site.py`, constante `CSS` l.1339 (`--faint:#938a78`).
`--faint` (#938a78) sur `--paper` (#f5f2e9) ≈ **3.1:1** ; sur `--card`
(#fffdf6) ≈ **3.4:1**. En dessous du seuil 4.5:1 pour le texte normal.
`--faint` porte de l'information de texte courant : `.card-meta`
(localisation des fiches), `.completude`, `.note`, `.row-sub` (sous-titres du
classement), `.count`, `.idl-scale-ends`, `.crit-inconnu`, `.chip-cat`,
`.cbar-na`, `.pal-chip em`, `.filter-lab`.
**Correction :** assombrir la variable —
`--faint:#6e6655;` (≈ 4.6:1 sur `--paper`). Si une nuance plus claire doit
être conservée pour des éléments purement décoratifs, créer une variable
distincte `--faint-deco` et ne l'utiliser que là.

### C2 — Texte des tags colorés sous le seuil
**Critère :** WCAG 1.4.3.
**Fichier :** `CSS` l.1453-1458 (`.tag`, `.tag-lieu/-porteur/-usufruitier/-modele`).
Les tags affichent du texte blanc `--paper` #fffdf6 en `.68rem` (≈11px) gras
majuscule — donc « texte normal », seuil 4.5:1. Ratios estimés du texte blanc :
sur `--gold` #b0843a ≈ **2.9:1**, sur `--terra` #bc5d3a ≈ **3.9:1**,
sur `--green` #4a7a3a ≈ **3.9:1**, sur `--blue` #36748a ≈ **3.5:1**.
Tous échouent. Même problème pour `.logo-mark` (blanc sur `--green`),
`.step-n` (blanc sur `--terra`), `.cta` (blanc sur `--green`), `.fbtn.active`
(blanc sur `--green`), `.pal-chip` colorés.
**Correction :** utiliser les variantes foncées comme fond de tag —
`.tag-lieu{background:var(--green-dk);}` (#356026, ≈ 5.7:1),
`.tag-porteur{background:var(--terra-dk);}` (#8f3f25, ≈ 6.4:1),
`.tag-usufruitier{background:var(--blue-dk);}` (#2a5566, ≈ 7.1:1),
`.tag-modele{background:var(--gold-dk);}` (#8a6420, ≈ 5.4:1).
Appliquer la même logique à `.logo-mark`, `.step-n`, `.cta`, `.fbtn.active`
(fond `--green-dk`). Alternative : ne pas mettre les tags en majuscules et
passer à `font-weight:700` + taille ≥ 14px pour bénéficier du seuil 3:1
« grand texte gras » — mais l'assombrissement du fond reste préférable.

### C3 — Visualisations SVG : information portée par la seule couleur
**Critère :** WCAG 1.4.1 Utilisation de la couleur.
**Fichiers :** `axis_bar` (l.273-290), `idl_scale` (l.378-402),
`grille_recap` (l.438-467), `corpus_histogram` (l.405-435), cellules `cell()`
du classement (l.884-888), pastilles `.axe-dot`.
Les barres d'axes, segments de palier, mini-barres du classement et segments
oui/partiel/non du récapitulatif se distinguent uniquement par la teinte.
Les barres d'axes A/B/C (`axis_bar`) sont identifiées par lettre+label, donc
acceptables ; en revanche `grille_recap` (segments oui/partiel/non/inconnu)
et l'histogramme reposent surtout sur la couleur. La valeur chiffrée à côté
des barres d'axes atténue le risque, mais `grille_recap` n'a qu'un texte
récapitulatif global.
**Correction :** pour `grille_recap`, ajouter un motif ou un libellé court
dans chaque segment, ou au minimum garantir un texte adjacent listant
« n oui · n partiel · n non · n inconnu » (déjà présent en `.rk-txt` —
le vérifier visible et non tronqué). Pour l'histogramme `corpus_histogram`,
ajouter sous chaque barre le libellé du palier (déjà fait via `.hg-l`) —
OK. Ne jamais retirer ces libellés. Pour les `cell()` du classement, la
valeur chiffrée `.cv` est présente : OK.

### C4 — SVG décoratifs non masqués pour les lecteurs d'écran
**Critère :** WCAG 1.1.1 Contenu non textuel.
**Fichier :** `axis_triangle` (l.305-341), `idl_badge` (l.346-375).
Sur une fiche, le profil tri-axes (`axis_triangle`) **et** l'anneau
(`idl_badge`) **et** la jauge (`idl_scale`) **et** les barres (`axis_bar`)
décrivent la **même donnée** (A/B/C + Indice). Chaque SVG porte
`role="img"` + `aria-label` : un lecteur d'écran annonce donc l'indice et
les axes 3 à 4 fois de suite dans le `score-panel`. C'est de la verbosité
redondante (échec de bonne pratique 1.1.1).
**Correction :** garder **une seule** source accessible. Conserver
`aria-label` sur le triangle (`axis_triangle`) qui est la synthèse la plus
complète ; ajouter `aria-hidden="true"` sur l'anneau `idl-ring`
(`idl_badge`) et sur la jauge `idl-scale` (`idl_scale`) **dès lors que la
valeur est déjà disponible en texte** — c'est le cas : le badge affiche
`<span class="idl-pal">` et le `<text class="idl-num">` ; ajouter un
`<span class="visually-hidden">Indice X sur 100</span>` à côté et masquer le
SVG. Idem dans les `card` : le triangle compact (`axis_triangle compact`)
ET les barres compactes (`axis_bar compact`) coexistent — masquer le
triangle compact avec `aria-hidden="true"` (l'`aria-label` y est de toute
façon peu lisible) puisque `axis_bar` donne déjà A/B/C chiffrés. Les barres
`axis_bar` étant des `<div>` avec chiffres visibles, elles sont nativement
lisibles : ne rien y ajouter.

### C5 — En-têtes de tableaux sans `scope`
**Critère :** WCAG 1.3.1 Information et relations.
**Fichiers :** `render_classement` `<thead>` (l.935-943),
`render_fiche` grille détaillée `<thead>` (l.656), `render_grilles`
`<thead>` (l.1032), `render_methode` table des paliers (l.1111).
Aucun `<th>` ne porte `scope="col"`. Les lignes de famille
(`<tr class="fam-row"><td colspan="4">`) sont des `<td>` : un lecteur
d'écran ne les annonce pas comme en-têtes de groupe. Le tableau du
classement n'a pas de `<caption>`.
**Correction :** ajouter `scope="col"` à chaque `<th>` de `<thead>`.
Pour les lignes de famille, transformer le `<td colspan>` en
`<th colspan="4" scope="colgroup">` (fonctions `render_fiche` l.648 et
`render_grilles` l.1023). Ajouter un `<caption>` à chaque table —
ex. classement : `<caption class="visually-hidden">Classement des entrées
par Indice de libération</caption>`. La classe `.table-scroll` étant un
conteneur scrollable, lui ajouter `tabindex="0"` et
`role="region"` + `aria-label` pour qu'il soit atteignable au clavier.

---

## IMPORTANTE

### I1 — Contraste de `--terra` et `--green` en texte sous le seuil
**Critère :** WCAG 1.4.3.
**Fichier :** `CSS` l.1340-1341, l.1350-1351 (`a:hover{color:var(--terra)}`),
`.hero-kicker` (`color:var(--terra)`), `.callout` accents.
`--terra` #bc5d3a sur `--paper` ≈ **4.0:1** ; `--green` #4a7a3a ≈ **4.1:1**.
En dessous de 4.5:1. `a:hover` passe le texte de lien en `--terra` : au
survol, un lien devient moins lisible qu'au repos. `.hero-kicker` est du
texte `--terra` `.8rem`.
**Correction :** pour les usages **texte**, employer `--terra-dk` #8f3f25
(≈ 6.5:1) et `--green-dk` #356026 (≈ 5.7:1). Concrètement :
`a:hover{color:var(--terra-dk);}` (l.1351),
`.hero-kicker{color:var(--terra-dk);}` (l.1395). `--green`/`--terra`
peuvent rester pour les **fonds** et traits décoratifs ≥ 3px (barres,
bordures), qui relèvent de 1.4.11 (seuil 3:1) — vérifier au cas par cas.

### I2 — Tris/filtres JS non annoncés (pas de région live)
**Critère :** WCAG 4.1.3 Messages d'état.
**Fichiers :** script de `render_catalogue` (l.829-865), script de
`render_classement` (l.949-991).
Quand l'utilisateur filtre ou trie, le nombre de résultats (`#cnt`) change
et des cartes/lignes apparaissent/disparaissent sans annonce. `#noresult`
est `hidden` puis dévoilé silencieusement. Le tri du classement réordonne
le DOM sans notification. `aria-sort` est bien géré sur les `<th>` (bon
point), mais le changement n'est pas verbalisé.
**Correction :** ajouter une région live polie. Dans `render_catalogue`,
englober le compteur : `<span class="count" aria-live="polite">…</span>`
et passer `#noresult` avec `role="status"`. Dans `render_classement`,
ajouter un conteneur masqué `<p id="sort-status" role="status"
class="visually-hidden"></p>` et, dans `sortBy()`, y écrire
`'Tableau trié par ' + th.innerText + ', ordre ' + (dir===1?'décroissant':'croissant')`.

### I3 — En-têtes de tableau triables : rôle inadéquat
**Critère :** WCAG 4.1.2 Nom, rôle, valeur ; 1.3.1.
**Fichier :** `render_classement` `<thead>` (l.937-942).
Les `<th>` triables ont `role="button"` — ce qui **écrase** le rôle natif
de cellule d'en-tête : un lecteur d'écran ne les annonce plus comme en-têtes
de colonne, et l'association `scope` est perdue. `aria-sort` sur un
`role="button"` n'est par ailleurs pas un usage standard.
**Correction :** retirer `role="button"`. Conserver le `<th>` comme
en-tête (`scope="col"`, cf. C5) et placer **à l'intérieur** un vrai
`<button>` portant le libellé et l'action de tri :
`<th scope="col" aria-sort="none"><button type="button" class="th-sort">A</button></th>`.
Le `tabindex="0"` sur le `<th>` devient alors inutile (le `<button>` est
focusable nativement) ; déplacer les écouteurs `click`/`keydown` sur le
`<button>` (le gestionnaire `keydown` Enter/Espace devient superflu, le
`<button>` le gère seul). Mettre à jour `aria-sort` sur le `<th>` parent.

### I4 — Champ de recherche : `aria-controls` et association absents
**Critère :** WCAG 1.3.1, 4.1.2.
**Fichier :** `render_catalogue` toolbar (l.804-815).
L'`<input type="search" id="q">` a un `aria-label` (bon) mais aucun lien
explicite vers la grille de résultats ni vers le compteur. Le `<select id="sort">`
a `aria-label="Trier les entrées"` ET un `<label for="sort">` visible
« Trier : » — la double étiquette peut produire une annonce confuse.
**Correction :** sur l'`<input>`, ajouter `aria-controls="…"` pointant
l'`id` de `<ul class="cards">` (lui donner un `id`, ex. `id="resultats"`).
Sur le `<select>`, supprimer l'`aria-label` redondant et garder uniquement
le `<label for="sort">` visible (ou l'inverse, mais pas les deux).

### I5 — Liens « cliquez sur un en-tête » et instructions visuelles
**Critère :** WCAG 1.3.3 Caractéristiques sensorielles ; 2.5.3.
**Fichier :** `render_classement` l.932-933 (`.sort-hint`).
L'instruction « Cliquez sur un en-tête de colonne… pour trier » suppose une
souris. Les en-têtes A/B/C sont identifiés par une seule lettre : hors
contexte (liste de liens d'un lecteur d'écran), « A », « B », « C » ne sont
pas explicites.
**Correction :** reformuler « Triez le tableau en activant un en-tête de
colonne ». Donner aux boutons de tri un nom accessible complet via
`aria-label` : `<button aria-label="Trier par axe A — intérêt général">A</button>`
(les `title` actuels « Intérêt général » sur les `<th>` ne sont pas un
substitut fiable).

### I6 — Cible tactile des boutons de filtre et liens de nav
**Critère :** WCAG 2.5.8 Taille de la cible (AA 2.2 ; recommandé) /
bonne pratique AA.
**Fichiers :** `.fbtn` (`CSS` l.1534-1537 : `padding:.34rem .7rem`,
hauteur ≈ 28-30px), `.topnav a` (l.1384 : `padding:.2rem 0`, hauteur
≈ 22px), `.crumb a`, `.foot-links a`, `.idl-scale` curseur.
Plusieurs cibles interactives sont sous 24×24 px (et loin des 44×44 px
confortables sur mobile).
**Correction :** porter `.fbtn` à `min-height:32px;padding:.4rem .8rem`.
Pour `.topnav a`, ajouter `padding:.5rem .2rem;` et un `min-height` ;
sur mobile (`@media max-width:620px`) viser 44px de hauteur de zone
cliquable. S'assurer d'au moins 24px entre cibles adjacentes.

### I7 — `axis_triangle` : `aria-label` peu intelligible sur les cartes
**Critère :** WCAG 1.1.1.
**Fichier :** `axis_triangle` (l.322-324, l.336-338).
Sur les cartes, le triangle compact porte un `aria-label` du type
« Profil tri-axes — A 100, B 100, C 86 ». Les lettres A/B/C ne sont pas
explicitées ; combiné à la redondance avec `axis_bar` (cf. C4), cela alourdit
la lecture.
**Correction :** si C4 est appliqué (triangle des cartes en
`aria-hidden="true"`), ce point disparaît. Sinon, expliciter le label :
« Profil : intérêt général 100, libération des terres 100, gouvernance 86 ».

---

## MINEURE

### M1 — Pas de classe utilitaire « visuellement masqué »
**Critère :** support des corrections C4/C5/I2.
**Fichier :** `CSS`.
Aucune classe `.visually-hidden` / `.sr-only` n'existe ; or plusieurs
corrections en ont besoin (caption, statut live, texte alternatif).
**Correction :** ajouter dans `CSS` :
`.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0;}`

### M2 — Abréviations non balisées
**Critère :** WCAG 3.1.4 Abréviations (AAA — donc hors AA strict, mais
recommandé).
**Fichiers :** `render_classement` (« IdL » l.911, l.942), `glossaire`,
fiches (« SCTL », « GFA », « OFS », « BRS », « RUP », « FPH »).
« IdL » et les sigles d'organismes ne sont jamais en `<abbr>`.
**Correction (optionnelle, AAA) :** au premier emploi par page, baliser
`<abbr title="Indice de libération">IdL</abbr>`. Non bloquant pour AA.

### M3 — Liens « → » et libellés de lien dépendants du contexte
**Critère :** WCAG 2.4.4 Fonction du lien (selon le contexte).
**Fichiers :** nombreux liens « Comprendre la grille → »,
« Méthode détaillée → », « Classement complet → », « ← Retour aux lieux ».
Ces libellés sont explicites **dans leur phrase** : conformes à 2.4.4 (AA),
qui autorise le contexte. La flèche `→`/`←` est un caractère décoratif lu
par certains lecteurs d'écran (« flèche vers la droite »).
**Correction (mineure) :** remplacer les flèches littérales par une
pseudo-classe CSS `::after{content:" →"}` non lue, ou les envelopper
`<span aria-hidden="true">→</span>`. Cosmétique.

### M4 — Liens externes : indication d'ouverture dans un nouvel onglet
**Critère :** WCAG 3.2.5 (AAA) / bonne pratique.
**Fichier :** `render_fiche` sources et champ « Site » (l.600, l.722-724 :
`target="_blank" rel="noopener"`).
Les liens externes ouvrent un nouvel onglet sans prévenir l'utilisateur.
**Correction :** ajouter un texte masqué ou un `aria-label` du type
« …(nouvel onglet) ». `rel="noopener"` est présent : bien.

### M5 — `meta name="description"` très longue sur les fiches
**Critère :** hors WCAG, qualité.
**Fichier :** `render_fiche` (l.738-739, `description=clean(resume)`).
La description (cf. `larzac.html` l.7) fait plusieurs centaines de
caractères. Sans impact d'accessibilité direct.
**Correction (optionnelle) :** tronquer à ~155 caractères comme le fait
déjà `render_index`.

### M6 — Contraste du focus visible sur fonds colorés
**Critère :** WCAG 1.4.11 / 2.4.13.
**Fichier :** `:focus-visible` (l.1352 : `outline:2px solid var(--green)`).
L'outline vert `--green` #4a7a3a a un contraste faible (~1.5:1) contre les
fonds verts (`.cta`, `.fbtn.active`, `.tag-lieu`). `.cta:focus-visible`
corrige déjà avec `outline-color:var(--ink)` — mais pas `.fbtn.active`.
**Correction :** définir un focus à fort contraste universel —
`:focus-visible{outline:2px solid var(--ink);outline-offset:2px;}` (l'encre
contraste partout), ou ajouter `.fbtn:focus-visible{outline-color:var(--ink);}`.

### M7 — Ordre de tabulation et pièges de focus
**Critère :** WCAG 2.4.3 / 2.1.2.
**Constat :** l'ordre de tabulation suit l'ordre du DOM (skiplink → nav →
contenu → footer), logique. Aucun piège de focus détecté (pas de modale,
pas de `tabindex` positif). Le `skiplink` cible bien `#contenu`
(`<main id="contenu">`). Aucun correctif nécessaire — point de
conformité confirmé.

---

## Synthèse de conformité

| Domaine | État |
|---|---|
| Landmarks, un seul h1, hiérarchie titres | Conforme |
| Skip link, ordre de tabulation, pièges de focus | Conforme |
| `lang="fr"`, `aria-current` fil d'Ariane | Conforme |
| `aria-sort` sur en-têtes triables | Présent (mais cf. I3) |
| Contrastes texte (`--faint`, tags, `--terra`/`--green`) | **Non conforme — C1, C2, I1** |
| SVG : alternatives, décoratif masqué, couleur seule | **Non conforme — C3, C4** |
| Tableaux : `scope`, `caption`, en-têtes de groupe | **Non conforme — C5** |
| Composants JS : annonce des changements (live) | **Non conforme — I2** |
| Rôle des en-têtes triables | **Non conforme — I3** |
| Cibles tactiles | À améliorer — I6 |

Priorité d'intervention : **C1, C2, C3, C4, C5** (bloquants AA), puis
**I1–I6**. Toutes les corrections sont à porter dans `generate_site.py`
(HTML des fonctions de rendu et constante `CSS`), puis à régénérer le site.
