# Cycle B — Audit mobile & responsive

Site statique « Terres Libérées » — audit en lecture seule sous l'angle mobile
(~360-414 px) et tablette (~768 px).

Périmètre examiné : `scripts/generate_site.py` (constante `CSS`, lignes 1700-2134,
strictement identique à `site/assets/style.css`), `index.html`, `classement.html`,
`grilles.html`, `regimes.html`, fiche `l/larzac.html`.

## Méthode

Le CSS ne possède que **deux** points de rupture : `max-width:880px` (tablette)
et `max-width:620px` (mobile). Aucun palier intermédiaire pour les petits
téléphones. Le viewport meta est correct (`width=device-width, initial-scale=1`).
L'audit confronte chaque composant aux largeurs cibles 360, 414 et 768 px.

## Constat d'ensemble

Le socle est sain : `box-sizing:border-box` global, `.wrap` fluide
(`max-width:1080px` + padding latéral), grilles en `auto-fit`/`auto-fill` avec
`minmax`, tables enveloppées dans `.table-scroll` à `overflow-x:auto`. Les
problèmes mobiles sont donc localisés, pas structurels. Les points faibles
tiennent à : la barre de nav à 10 entrées, des `flex-basis` fixes en `rem`/`px`
qui ne se réinitialisent pas, des cibles tactiles sous le seuil de 44 px, et un
hero un peu généreux en petite largeur.

---

## CRITIQUE

### C1 — Barre de navigation : 10 entrées qui s'empilent sans hiérarchie
`index.html` ligne 36 : la `.topnav` contient **10 liens** (Accueil, Lieux,
Porteurs, Usufruitiers, Classement, Trois régimes, Grilles, Modèles voisins,
Glossaire, Méthode). En `flex-wrap`, à 360-414 px ils se répartissent sur
3-4 lignes et repoussent fortement le contenu sous le `.masthead`. Les liens
ont `padding:.45rem .2rem` + `min-height:24px` — la zone tactile horizontale
(`.2rem` de padding) est minuscule et deux liens adjacents sur la même ligne
sont quasi accolés (risque de tap erroné).

Correctifs (nouveau bloc dans `@media(max-width:620px)`) :
```css
.masthead .wrap{padding-bottom:.3rem;}
.topnav{gap:.15rem .55rem;width:100%;
 margin-top:.4rem;padding-top:.5rem;
 border-top:1px solid var(--line);}
.topnav a{padding:.5rem .55rem;min-height:44px;
 display:flex;align-items:center;}
```
Cible un meilleur compromis : zone tactile conforme (44 px), séparation visuelle,
nav rejetée en pleine largeur sous la marque. Idéalement, à terme, basculer la
nav en menu repliable (`<details>`/burger) — non bloquant ici mais recommandé
au prochain cycle.

### C2 — Tableau du classement : 7 colonnes, libellés de catégorie qui débordent
`classement.html` : `.table-scroll` (ligne 63) gère bien le scroll horizontal,
mais à 360 px le tableau est large et **la colonne « Entrée »** contient un
`.row-sub` (sous-titre long, ex. « Plateau agricole géré par une société civile
de droit privé ») sans contrainte de largeur : la cellule s'étire et le scroll
devient très long, peu lisible. La colonne « Catégorie » porte un `.tag`
(`white-space:nowrap`) qui ajoute encore de la largeur.

Correctifs (dans `@media(max-width:620px)`) :
```css
.rank-tbl{font-size:.82rem;}
.rank-tbl td,.rank-tbl th{padding:.4rem .4rem;}
.rank-tbl .name{min-width:11rem;max-width:13rem;}
.rank-tbl .row-sub{white-space:normal;line-height:1.25;}
.th-sort{padding:.45rem .4rem;}
```
Plus : rendre le scroll explicite — `.table-scroll` devrait recevoir une aide
visuelle (ombre de débord). Optionnel mais utile :
```css
.table-scroll{background:
 linear-gradient(90deg,var(--paper) 30%,transparent),
 linear-gradient(90deg,transparent,var(--paper) 70%) 100% 0,
 radial-gradient(farthest-side at 0 50%,rgba(0,0,0,.12),transparent),
 radial-gradient(farthest-side at 100% 50%,rgba(0,0,0,.12),transparent) 100% 0;
 background-repeat:no-repeat;background-size:32px 100%,32px 100%,14px 100%,14px 100%;
 background-attachment:local,local,scroll,scroll;}
```

### C3 — Tableau comparatif des régimes : 4 colonnes de texte dense, illisible à 360 px
`regimes.html` lignes 63-70 : `.regimes-tbl` a une 1re colonne en `<th scope="row">`
puis 3 colonnes de prose. À 360 px, 4 colonnes ⇒ chaque colonne fait ~80 px,
le texte se casse mot par mot sur 6-8 lignes. Le `.table-scroll` ne résout rien
car `table{width:100%}` force le tableau à se compresser dans le viewport au
lieu de déborder proprement.

Correctif (dans `@media(max-width:620px)`) :
```css
.regimes-tbl{min-width:34rem;font-size:.82rem;}
.regimes-tbl th,.regimes-tbl td{padding:.45rem .5rem;}
.regimes-tbl th[scope=row]{position:sticky;left:0;
 background:var(--card);z-index:1;}
```
`min-width` force le tableau à dépasser le viewport ⇒ le `.table-scroll`
redevient utile, chaque colonne garde une largeur lisible, et la colonne
critère reste figée à gauche pendant le défilement.

### C4 — Toolbar / filtres du classement : `<label>` orphelin et boutons serrés
`classement.html` lignes 53-59 : la `.toolbar` met sur une ligne flex le
`<label>` « Filtrer par catégorie : » suivi de 4 `.fbtn`. Le `<label>` n'est
pas dans la liste `.sans` et hérite du serif ; surtout, en `flex-wrap` à
360 px le label reste collé au 1er bouton et les boutons (`min-height:32px`,
sous le seuil tactile de 44 px) s'enroulent sans marge verticale.

Correctifs (dans `@media(max-width:620px)`) :
```css
.toolbar{gap:.45rem;}
.toolbar > label{flex:0 0 100%;font-size:.8rem;
 color:var(--muted);margin-bottom:.1rem;}
.fbtn{min-height:40px;padding:.5rem 1rem;}
.toolbar input[type=search]{flex:1 1 100%;min-width:0;}
```
Le champ de recherche (`min-width:180px`) sur `lieux.html`/`porteurs.html`
doit aussi passer en pleine largeur — d'où `flex:1 1 100%;min-width:0`.

---

## IMPORTANTE

### I1 — Hero : padding et titre encore généreux en très petite largeur
`index.html` lignes 40-51. À 620 px le hero passe à `padding:2.4rem 0 1.8rem`
et `h1` à `1.95rem` — correct vers 414 px, mais à 360 px le `h1`
(`max-width:18ch`, `letter-spacing:-.018em`) reste large et les deux boutons
`.hero-cta` (`.cta` `padding:.6rem 1.2rem`) débordent parfois sur 2 lignes
sans respiration. Ajouter un palier 380 px :
```css
@media(max-width:400px){
 .hero{padding:1.9rem 0 1.4rem;}
 .hero h1{font-size:1.7rem;}
 .hero-lead{font-size:1rem;}
 .hero-cta{gap:.5rem;}
 .hero-cta .cta{flex:1 1 100%;text-align:center;}
}
```
Les CTA en pleine largeur empilés sont une cible tactile nette sur petit écran.

### I2 — `axis-label` à `flex-basis` fixe : libellés tronqués sur la fiche
`style.css` ligne 176 : `.axis-label{flex:0 0 8.4rem;...white-space:nowrap;
text-overflow:ellipsis}`. Sur la fiche (`.score-axes`, ex. `larzac.html`
lignes 56-69) les libellés « A · Intérêt général », « B · Libération des
terres », « C · Gouvernance participative » sont systématiquement coupés en
ellipsis dès que la largeur du panneau descend sous ~320 px de zone utile —
c'est le cas à 360 px (panneau pleine largeur moins paddings `1.6rem`+`1.8rem`).
L'information clé (le nom de l'axe) disparaît.

Correctif (dans `@media(max-width:620px)`) :
```css
.score-panel{padding:1.1rem 1rem;}
.axis-row{flex-wrap:wrap;}
.axis-label{flex:1 1 100%;white-space:normal;
 overflow:visible;margin-bottom:.1rem;}
.axis-track{flex:1 1 auto;}
.axis-val{flex:0 0 2.1rem;}
```
Le libellé passe sur sa propre ligne, barre + valeur en dessous : plus de
troncature, lecture confortable.

### I3 — Récap par axe (`.grille-recap`) : barre à largeur fixe en px
`style.css` ligne 262 : `.rk-bar{flex:0 0 130px}`. À 620 px le `@media`
existant repasse `.rk-ax` en `flex-basis:100%` (bien), mais la `.rk-bar`
garde `130px` et le `.rk-txt` la suit ; sur la fiche à 360 px le couple
barre+texte tient, mais la barre fixe à 130 px laisse un grand vide à droite.
Mineur visuellement mais incohérent. Améliorer :
```css
@media(max-width:620px){
 .rk-bar{flex:1 1 auto;}
}
```

### I4 — SVG `.tri` dans les cartes : taille fixe non fluide
`style.css` lignes 130-131 : `.tri{width:108px}`, `.tri.compact{width:78px}`.
Dans `.card-viz` (`display:flex;gap:.7rem`) le triangle `78px` + le
`.axis-block` cohabitent. À 300 px de carte (le `minmax(300px,1fr)` des
`.cards`, ligne 108) ça passe ; mais à 360 px de viewport une carte fait
~330 px utile, le triangle 78 px laisse ~245 px aux barres dont les libellés
`.compact` (`flex-basis:5.6rem` ≈ 90 px) — c'est juste mais acceptable.
Point de vigilance plutôt que défaut : si on réduit `.cards` à
`minmax(260px,1fr)` pour un meilleur remplissage mobile, prévoir
`.tri.compact{width:64px}` sous 620 px. Recommandation :
```css
@media(max-width:620px){
 .cards{grid-template-columns:1fr;}
 .tri.compact{width:68px;}
}
```
Forcer une colonne unique évite les cartes à 300 px comprimées entre les
paddings du `.wrap`.

### I5 — Histogramme du corpus : SVG correct mais texte petit
`index.html` ligne 113 : `.corpus-hist svg{width:100%;max-width:420px}` —
le dimensionnement est bon (fluide, plafonné). Mais les libellés de palier
(`.hg-l`, `font:9px`) sous chaque barre, à 360 px de rendu réel, tombent à
~7-8 px effectifs et certains libellés longs (« Libération partielle »,
« Éloigné du modèle ») se chevauchent car centrés sur des barres de ~38 px.
Le SVG a un `viewBox 0 0 360 180` figé ; sans réécriture du générateur, on
peut au moins éviter le chevauchement en agrandissant le viewBox côté Python,
ou accepter la limite. Recommandation CSS minimale (lisibilité) :
```css
@media(max-width:620px){
 .corpus-hist svg{max-width:100%;}
}
```
Note pour le générateur : produire les libellés sur 2 lignes (`<tspan>`) ou
incliner le texte réglerait le chevauchement à la source.

---

## MINEURE

### M1 — Masthead : marque + baseline peuvent serrer
`index.html` lignes 31-35 : `.brand-name` (`1.4rem`) + `.baseline`
(`.76rem`, texte long « Annuaire critique des montages… »). Le `.masthead .wrap`
est en `flex-wrap` avec `justify-content:space-between` ; à 360 px la marque
prend toute la ligne, la nav passe dessous (bien). La baseline longue peut
toutefois pousser à 2 lignes. Acceptable ; si on veut épurer :
```css
@media(max-width:620px){ .baseline{display:none;} }
```

### M2 — `.enbref dl` déjà géré
`style.css` ligne 429 : `@media(max-width:620px)` repasse `.enbref dl` en
`grid-template-columns:1fr`. RAS, bon réflexe déjà en place. À noter que
`.enbref dd` a `word-break:break-word` qui gère les URL longues — correct.

### M3 — `.steps` / `.explain-grid` / `.cat-cards` / `.regime-grid`
Toutes ces grilles sont en `auto-fit minmax(...)` (220-260 px) : elles
passent naturellement à 1 colonne sous ~280 px. RAS. Seule remarque :
`.cat-cards` en `minmax(260px,1fr)` — à 360 px une seule colonne, le
padding `1.1rem 1.2rem` est confortable. OK.

### M4 — Chips de relations (`.chip-rel`) sur les fiches
`style.css` lignes 351-356 : `.chip-rel` est un flex avec un `.tri` +
`.chip-txt`. En `.chips{flex-wrap:wrap}` ça s'empile bien. À 360 px un chip
peut occuper presque toute la largeur — acceptable. Pas de correctif requis.

### M5 — Profondeur de breakpoint
Le saut direct 880 → 620 → (rien) laisse la plage 360-414 px sans réglage
dédié. Les correctifs I1 (palier 400 px) et la révision du bloc 620 px
ci-dessus comblent l'essentiel. Envisager au cycle C un palier `max-width:520px`
si de nouveaux composants apparaissent.

### M6 — `:focus-visible` et cibles tactiles
Le focus est bien géré globalement (`outline:2px`). Les `.fbtn`/`.th-sort`
sont focusables. Le seul vrai défaut tactile est la taille — traité en C1
(nav) et C4 (filtres). Les liens `.topnav` à `min-height:24px` étaient le
point le plus faible : corrigé par C1 (44 px).

---

## Synthèse des blocs CSS à ajouter

À insérer dans la constante `CSS` de `generate_site.py` (puis régénérer), en
remplaçant/complétant le bloc `@media(max-width:620px)` existant et en ajoutant
un palier `400px` :

```css
/* mobile — révisé */
@media(max-width:620px){
 h1{font-size:1.85rem;}
 .hero{padding:2.4rem 0 1.8rem;}
 .hero h1{font-size:1.95rem;}
 .hero-lead{font-size:1.08rem;}
 .enbref dl{grid-template-columns:1fr;}
 .count{margin-left:0;}
 .rk-row{flex-wrap:wrap;}
 .rk-ax{flex-basis:100%;}
 .rk-bar{flex:1 1 auto;}                              /* I3 */

 /* nav — C1 */
 .masthead .wrap{padding-bottom:.3rem;}
 .topnav{gap:.15rem .55rem;width:100%;margin-top:.4rem;
  padding-top:.5rem;border-top:1px solid var(--line);font-size:.82rem;}
 .topnav a{padding:.5rem .55rem;min-height:44px;
  display:flex;align-items:center;}

 /* classement — C2 */
 .rank-tbl{font-size:.82rem;}
 .rank-tbl td,.rank-tbl th{padding:.4rem .4rem;}
 .rank-tbl .name{min-width:11rem;max-width:13rem;}
 .rank-tbl .row-sub{white-space:normal;line-height:1.25;}
 .th-sort{padding:.45rem .4rem;}

 /* régimes — C3 */
 .regimes-tbl{min-width:34rem;font-size:.82rem;}
 .regimes-tbl th,.regimes-tbl td{padding:.45rem .5rem;}
 .regimes-tbl th[scope=row]{position:sticky;left:0;
  background:var(--card);z-index:1;}

 /* toolbar / filtres — C4 */
 .toolbar{gap:.45rem;}
 .toolbar > label{flex:0 0 100%;font-size:.8rem;
  color:var(--muted);margin-bottom:.1rem;
  font-family:-apple-system,system-ui,sans-serif;}
 .fbtn{min-height:40px;padding:.5rem 1rem;}
 .toolbar input[type=search]{flex:1 1 100%;min-width:0;}

 /* fiche — score panel / axis — I2 */
 .score-panel{padding:1.1rem 1rem;}
 .axis-row{flex-wrap:wrap;}
 .axis-label{flex:1 1 100%;white-space:normal;
  overflow:visible;margin-bottom:.1rem;}
 .axis-track{flex:1 1 auto;}

 /* cartes — I4 */
 .cards{grid-template-columns:1fr;}
 .tri.compact{width:68px;}
}

/* très petit écran — I1 */
@media(max-width:400px){
 .hero{padding:1.9rem 0 1.4rem;}
 .hero h1{font-size:1.7rem;}
 .hero-lead{font-size:1rem;}
 .hero-cta{gap:.5rem;}
 .hero-cta .cta{flex:1 1 100%;text-align:center;}
}
```

Le bloc `@media(max-width:880px)` (tablette) n'appelle pas de correctif :
`.score-panel` en colonne, `.score-axes` sans bordure gauche et `.rk-ax`
à `8rem` couvrent correctement la cible 768 px. Les grilles `auto-fit`
gèrent le reste.
