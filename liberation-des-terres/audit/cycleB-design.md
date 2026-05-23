# Cycle B — Audit design : sobriété et allègement visuel

Audit en lecture seule du site « Terres Libérées ».
Angle : design visuel et allègement. Objectif : un site sobre et élégant, **pas
trop chargé**. On affine, on n'opère pas une refonte.

Le socle est sain : palette terreuse cohérente, typo sérif lisible, échelle
maîtrisée, états focus présents. Les problèmes sont des excès d'accumulation —
trop de surfaces encadrées, trop d'accents colorés au même endroit, quelques
incohérences de finition. Les recommandations ci-dessous retirent du bruit sans
toucher au fond.

Fichiers concernés : `site/assets/style.css` (la feuille est servie depuis ce
fichier ; `scripts/generate_site.py` n'embarque pas de constante CSS — la
maintenance se fait dans `style.css`).

---

## CRITIQUE

### C1 — Surcharge de cartes : triangle SVG + barres redondants
`.card-viz` affiche **côte à côte** le triangle tri-axes ET les trois barres
chiffrées. Les deux disent exactement la même chose. Sur les pages catalogue et
l'accueil, chaque carte porte donc deux dataviz concurrentes — c'est la première
source de surcharge perçue.

Le triangle compact est joli mais décoratif (`aria-hidden`) et illisible à 78 px.
Recommandation : **retirer le triangle des cartes**, ne garder que les barres
chiffrées (précises, lisibles, accessibles). Garder le triangle uniquement sur la
fiche (`.score-panel`) où il a la place de s'exprimer.

Geste minimal côté CSS si on préfère ne pas toucher le Python — masquer le
triangle compact en contexte carte :
```css
.card-viz .tri.compact{display:none;}
.card-viz .axis-block{margin:.3rem 0 0;}
```
Idéalement, supprimer aussi l'appel `axis_triangle(..., compact=True)` dans
`card()` (generate_site.py l.577) pour ne pas générer du SVG mort.

### C2 — Inflation des surfaces « encadré » : trop de cartes blanches bordées
Le motif `background:var(--card);border:1px solid var(--line);border-radius`
est répété sur **9 composants** : `.step`, `.cat-card`, `.card`, `.axe-card`,
`.regime-card`, `.strat`, `.chip-rel`, `.score-panel`, `.an-col` (fond card).
Une page comme l'accueil empile steps + cat-cards + cards : une mosaïque de
rectangles blancs cernés qui « charge » l'œil.

Recommandation — alléger les conteneurs **secondaires** en retirant la bordure et
en ne gardant qu'un fond très discret :
```css
.step,.cat-card{background:var(--card);border:1px solid transparent;
 border-radius:var(--radius);}
.cat-card:hover{border-color:var(--line);box-shadow:none;}
```
Ou, plus radical et plus sobre, transformer `.steps` en liste numérotée sans
encadré (le `.step-n` rond suffit à structurer). Garder la bordure pleine
uniquement pour `.card` (élément cliquable principal du catalogue).

### C3 — Accumulation de barres d'accent colorées
On compte au moins **cinq systèmes de filets colorés** distincts :
`h2.sec::before` (tiret terra), `.score-panel` (border-left 5px palier),
`.callout` (border-left 3px gold/terra), `.an-col` (border-top 3px axe),
`.axe-card` / `.regime-card` (border-top 4px), `.enbref` / `.fiab-box`
(border-left 3px line), `.pal-chip` (border-left 4px). Sur la fiche détaillée,
ces accents se cumulent verticalement et créent un effet « sapin de Noël ».

Recommandations :
- **Uniformiser l'épaisseur** : tous les filets d'accent à `3px` (actuellement
  3, 4 et 5 px coexistent). `.score-panel{border-left-width:3px}`,
  `.axe-card{border-top-width:3px}`, `.regime-card` idem, `.pal-chip` idem.
- **Retirer l'accent des conteneurs neutres** : `.enbref` et `.fiab-box` ont un
  `border-left:3px solid var(--line)` — un filet de la couleur de la bordure
  n'apporte aucune information, il ajoute juste un trait. Le supprimer, garder le
  seul fond `var(--beige)` :
  ```css
  .enbref{background:var(--beige);border-radius:var(--radius);
   padding:1rem 1.3rem;margin:1.2rem 0;font-size:.92rem;}
  .fiab-box{background:var(--beige);border-radius:var(--radius);
   padding:.7rem 1.2rem;margin:1.4rem 0;}
  ```

---

## IMPORTANTE

### I1 — Incohérence des rayons de bordure
La variable `--radius:8px` existe mais n'est pas appliquée partout :
- `.tag` → `border-radius:4px` ; `.pal-chip` → `4px` ; `code` → `3px` ;
  `:focus-visible` → `3px` ; `.axis-fill` / `.axis-track` → `4px` ;
  `.skiplink` → `var(--radius)`.
- Les « pilules » (`.fbtn`, `.chip`) utilisent `20px`, deux valeurs différentes
  bien que visuellement identiques en intention.

Recommandation : introduire deux variables et s'y tenir.
```css
:root{ --radius:8px; --radius-sm:4px; --radius-pill:999px; }
```
Puis : `.tag`, `.pal-chip`, `.axis-fill`, `.axis-track`, `.rk-bar` →
`var(--radius-sm)` ; `.fbtn`, `.chip` → `var(--radius-pill)` ;
`code` et `:focus-visible` → `var(--radius-sm)`. Cela supprime les `3px`/`4px`
épars.

### I2 — Incohérence du nuancier vert (palier vs UI)
Deux verts foncés très proches cohabitent sans logique claire : `--green-dk`
`#356026` (liens, CTA, boutons actifs) et le `#2f6b34` du palier « Libération
aboutie » injecté en `--pal` (badges, accents fiche). Sur une fiche en tête de
classement, le `border-left` du `.score-panel`, l'anneau du badge et les liens
verts affichent **trois verts légèrement différents** côte à côte — l'œil lit
une imprécision.

Recommandation : aligner le vert de palier le plus haut sur `--green-dk`
(`#356026`) dans `config/ranking.yml`, OU assumer que `--pal` est une couleur de
donnée distincte de la couleur d'UI — mais alors ne pas l'utiliser pour le
`border-left` du panneau (cf. C3, le ramener à 3px atténue déjà le conflit).

### I3 — Hiérarchie : `.lead` sert deux rôles incompatibles
`.lead` est à la fois le **chapô de page** (gros texte d'introduction sous le
H1, `font-size:1.05rem`, couleur `--muted`) ET un fil de liens secondaires
(« Les trois régimes → · Glossaire → · Méthode → » sur l'accueil). Même style
pour une fonction structurante et une fonction utilitaire : la hiérarchie se
brouille.

Recommandation : créer une classe dédiée aux fils de liens et la dégrader
visuellement.
```css
.linkrow{font-family:-apple-system,system-ui,sans-serif;font-size:.9rem;
 color:var(--faint);margin:.6rem 0;}
```
(à appliquer dans generate_site.py là où `.lead` ne contient que des liens
fléchés). À défaut, accepter le compromis mais ne pas cumuler chapô + fil de
liens dans la même section.

### I4 — `.hero` : dégradé superflu
`.hero` porte `background:linear-gradient(180deg,rgba(221,212,191,.22),
transparent)`. Sur un fond papier déjà chaud, ce dégradé est quasi invisible
mais ajoute une « zone » mal délimitée sous le H1. Pour un rendu plus net et plus
sobre :
```css
.hero{padding:3.4rem 0 2.6rem;border-bottom:1px solid var(--line);}
```
Le filet inférieur suffit à séparer le hero du reste.

### I5 — États hover incohérents entre composants cliquables
- `.card:hover` et `.cat-card:hover` → `border-color:var(--green)` +
  `box-shadow`.
- `.chip:hover` / `.chip-rel` → `border-color:var(--green)` mais **le texte
  passe à `var(--terra)`** : un seul composant fait virer sa couleur de texte au
  survol, sans raison.
- `.fbtn:hover` → `border-color:var(--green)` + texte `--ink` (OK).

Recommandation : harmoniser. Le survol des chips ne devrait pas recolorer le
texte en terra :
```css
.chip:hover{border-color:var(--green);color:var(--ink);}
```
Garder un seul langage : au survol, la **bordure** passe au vert, le texte reste
stable.

### I6 — Liens : couleur hover déroutante
Règle globale `a:hover{color:var(--terra-dk)}` : tous les liens du corps virent
au terracotta au survol. Sur une page dense en liens (grilles, méthode), le
survol fait « sauter » la couleur d'un mot. C'est défendable comme parti pris,
mais combiné à I5 (chips terra) cela multiplie le terra. Option plus sobre :
garder le vert et signaler le survol par le seul soulignement déjà présent sur
`.prose a` :
```css
a:hover{color:var(--green);}
```

---

## MINEURE

### M1 — Triangle SVG : viewBox incohérent
`axis_triangle` génère `viewBox="0 0 120 110"` (hauteur `size*0.92`) alors que
`_tri_geom` place le centre à `cy=size*0.46` et un rayon `0.42` — les sommets
hauts/bas tiennent dans ~`0.88*size`. Le `viewBox` à 110 laisse une marge basse
asymétrique. Sans gravité (le SVG est `display:block`), mais un `viewBox` calé
sur la géométrie réelle (`0 0 120 92`) supprimerait le léger décentrage vertical.

### M2 — `.no-result` : accent terra pour une information neutre
`.no-result` (« Aucune entrée ne correspond ») porte un `border-left:3px solid
var(--terra)` — le terra est aussi la couleur de `.callout-warn`. Un filtre sans
résultat n'est pas un avertissement. Passer le filet en `var(--line)` ou le
retirer (le fond beige suffit).

### M3 — `table th` : double signal de hiérarchie
Les en-têtes de tableau cumulent `text-transform:uppercase` +
`letter-spacing` + `font-size:.72rem` + `border-bottom:2px solid var(--ink)`.
Le filet noir épais sous des capitales déjà très marquées est redondant. Un
`border-bottom:1px solid var(--ink)` allège sans perdre la séparation.

### M4 — `.masthead` / `.footer` : filet noir 3px
`border-bottom:3px solid var(--ink)` (masthead) et `border-top:3px solid
var(--ink)` (footer). Cohérent entre eux, mais 3px de noir pur est l'élément le
plus « dur » de la page. `2px` resterait affirmé tout en s'accordant mieux à la
finesse du reste (filets à 1px partout ailleurs).

### M5 — `.score-panel` : double séparateur interne
Le panneau a un `gap:1.6rem` ET la colonne `.score-axes` ajoute
`border-left:1px solid var(--line);padding-left:1.6rem`. Le filet + le gap font
double emploi. Garder l'un des deux — le gap seul suffit, le filet peut sauter :
```css
.score-axes{flex:1;min-width:260px;padding-left:0;}
```
(Le panneau garde alors une seule respiration, plus aérée.)

### M6 — `.steps` et `.explain-grid` : `<h3>` de tailles différentes
Dans `.step`, le `h3` hérite de `1.28rem` ; dans `.an-col` et `.axe-card`, des
`h3` sont ramenés à `.82rem`–`1.05rem` en capitales. Trois traitements de `h3`
coexistent. Acceptable, mais documenter l'intention (titre de carte vs label de
colonne) éviterait des divergences futures. Au minimum, `.an-col h3` et
`.axe-card h3` partagent le même rôle « étiquette » : leur donner exactement le
même style (`.82rem` uppercase) plutôt que `.82rem` d'un côté et `1.05rem` de
l'autre.

### M7 — Espacement `h2.sec` : marge haute généreuse
`h2.sec{margin:2.8rem 0 1.2rem}`. Sur les pages courtes c'est bien ; sur la
fiche (8+ sections) cela étire beaucoup. `2.4rem` resterait aéré tout en
resserrant légèrement le rythme vertical. Ajustement de confort, optionnel.

### M8 — `.idl-pal` : casse + graisse sous le badge de carte
Sous chaque badge de carte, `.idl-pal` répète le palier en petites capitales.
Comme le badge est déjà coloré par palier et que le tableau/les filtres
nomment les paliers, ce libellé sous chaque carte est une répétition. Le
réduire (déjà `.62rem`) ou le masquer en contexte carte allègerait la grille :
```css
.card .idl-pal{display:none;}
```
(à arbitrer selon l'importance accordée au nom du palier au niveau carte).

---

## Récapitulatif priorisé

| #  | Priorité   | Geste | Effet |
|----|-----------|-------|-------|
| C1 | Critique  | Retirer le triangle des cartes, garder les barres | Supprime la dataviz redondante |
| C2 | Critique  | Débordurer steps/cat-cards | Casse la mosaïque de rectangles |
| C3 | Critique  | Filets d'accent uniformes à 3px ; retirer filet des conteneurs neutres | Calme la fiche |
| I1 | Importante| Variables `--radius-sm` / `--radius-pill`, appliquées partout | Cohérence des rayons |
| I2 | Importante| Aligner vert palier haut ↔ `--green-dk` | Supprime le triple vert |
| I3 | Importante| Classe `.linkrow` distincte de `.lead` | Hiérarchie claire |
| I4 | Importante| Retirer le dégradé du hero | Hero plus net |
| I5 | Importante| Hover chips : texte stable, pas de terra | Langage de survol unifié |
| I6 | Importante| Hover liens en vert plutôt que terra | Moins de terra parasite |
| M1 | Mineure   | viewBox triangle calé sur la géométrie | Centrage |
| M2 | Mineure   | `.no-result` : filet neutre | Pas de fausse alerte |
| M3 | Mineure   | `table th` : filet 1px | Allège les tableaux |
| M4 | Mineure   | Masthead/footer : filet 2px | Adoucit |
| M5 | Mineure   | `.score-panel` : un seul séparateur | Respiration |
| M6 | Mineure   | Unifier les `h3` étiquettes | Cohérence |
| M7 | Mineure   | `h2.sec` marge 2.4rem | Rythme resserré |
| M8 | Mineure   | Masquer `.idl-pal` sur carte | Allège la grille |
