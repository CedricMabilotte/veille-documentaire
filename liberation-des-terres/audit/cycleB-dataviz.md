# Cycle B — Audit de la visualisation des données et de la lisibilité des scores

Annuaire « Terres Libérées ». Audit en lecture seule, angle dataviz : composants
de `scripts/generate_site.py` (`axis_bar`, `axis_triangle`, `idl_badge`,
`idl_scale`, `corpus_histogram`, `grille_recap`, `cell` du classement, `card`)
et leur rendu (`site/index.html`, `site/classement.html`, `site/l/larzac.html`,
`site/methode.html`), plus `site/assets/style.css`.

> Méthode : audit conduit sur le code Python, le CSS et les pages HTML rendues.
> Le rendu navigateur n'a pas été ouvert : les jugements de forme s'appuient
> sur la lecture du CSS et du HTML généré — fiables sur la structure, à
> reconfirmer au pixel.

Le cycle 2 (`audit/cycle2-dataviz.md`) avait recommandé le triangle tri-axes,
l'anneau d'indice, les mini-barres de classement, l'histogramme de corpus et le
récap de grille. **Tout cela est en place et bien fait.** Le présent cycle audite
l'état post-implémentation : il ne reste plus de manque criant, mais quelques
**redondances** et **scories de finition** nuisent à l'objectif affiché —
lisibilité immédiate, sobriété, pas de surcharge.

Toutes les propositions restent en SVG/CSS inline généré par Python, sans
dépendance externe.

---

## Constat d'ensemble

Le socle dataviz est mûr et cohérent : couleurs d'axe stables (A vert, B
terracotta, C bleu) partagées entre `ranking.yml` et les variables CSS
`--axe-*`, redondance couleur+texte systématique, SVG décoratifs correctement
`aria-hidden` avec doublure texte. Trois points à corriger :

1. **La carte affiche DEUX visualisations tri-axes concurrentes** — le triangle
   compact ET les trois barres d'axes compactes, côte à côte. C'est la
   redondance la plus visible du site, et elle contredit la recommandation
   explicite du cycle 2 (« remplacer `axis_bar` par `axis_triangle` » dans la
   carte). Surcharge nette.
2. **L'histogramme de corpus est rendu deux fois à l'identique** (accueil +
   méthode), via le même `corpus_histogram()`. Acceptable, mais l'accueil
   gagnerait une variante plus légère, et la page méthode est la place
   canonique.
3. **Scories de finition** : décimales parasites sur les modèles estimés,
   triangle dégénéré illisible quand un axe est `n.r.`, et absence de toute
   échelle de référence sur le triangle plein de la fiche.

---

# RECOMMANDATIONS CRITIQUES

## C1 — Carte : supprimer les barres d'axes, ne garder que le triangle

**Problème.** `card()` (generate_site.py ~l. 576-579) produit :

```python
  <div class="card-viz">
    {axis_triangle(axes_cfg, sc['axes'], compact=True)}
    {axis_bar(axes_cfg, sc['axes'], compact=True)}
  </div>
```

Les deux composants encodent **exactement la même donnée** (A/B/C 0-100). Le
triangle donne la *forme* d'un coup d'œil ; les trois barres donnent les
*chiffres*. Les afficher ensemble dans la vignette d'une carte, c'est :
- doubler la hauteur du bloc viz pour zéro information nouvelle ;
- créer une hésitation de lecture (« lequel je regarde ? ») ;
- contredire le cycle 2, qui demandait le triangle *en remplacement* des barres
  sur la carte, les barres restant réservées au panneau de score de la fiche.

Sur l'accueil comme sur les catalogues, chaque carte porte donc 1 anneau +
1 triangle + 3 barres chiffrées : c'est la définition de la surcharge.

**Recommandation.** Dans `card()`, ne garder que le triangle :

```python
  <div class="card-viz">
    {axis_triangle(axes_cfg, sc['axes'], compact=True)}
  </div>
```

Les chiffres exacts A/B/C restent accessibles d'un clic, sur la fiche. La carte
est une vignette de repérage : la forme du triangle (centré = équilibré, étiré
= spécialisé) suffit, et c'est précisément le propos éditorial. Le triangle
compact porte déjà les lettres A/B/C sur ses sommets ; aucune perte
d'accessibilité (le triangle compact est `aria-hidden`, mais la carte porte le
nom, le palier et l'anneau ; le détail chiffré est sur la fiche liée).

Conséquence CSS : `.card-viz` (l. 118-119) peut être simplifié — le `flex` à
deux enfants devient un simple centrage du triangle. Le triangle compact peut
être légèrement agrandi (78 → ~92 px) puisqu'il occupe désormais seul la zone.

**Effet.** Cartes plus courtes, grilles plus denses sans être chargées, lecture
immédiate du profil. C'est la correction la plus rentable du cycle.

---

# RECOMMANDATIONS IMPORTANTES

## I1 — Triangle : gérer proprement un axe non renseigné

**Problème.** Dans `axis_triangle()` (l. 366-410), un axe `None` est traité par
`f = 0.0` : le point est ramené au centre de gravité G. Si un seul axe manque,
le polygone se rétracte vers le centre sur ce sommet et prend une forme de
« cerf-volant » trompeuse — l'œil lit un score nul, alors que la donnée est
*absente*, pas *nulle*. Pour les fiches lacunaires (et le cycle 3 a montré que
le corpus en compte), le triangle ment visuellement.

Le sommet `n.r.` est certes marqué `tri-na` (cercle évidé pointillé), mais le
polygone rempli, lui, ne distingue pas absence et zéro.

**Recommandation.** Deux options, par ordre de préférence :

a) **Hacher le segment vers un sommet manquant.** Garder le point au centre
   mais rendre l'arête correspondante du polygone en pointillé via une seconde
   `<polyline>` superposée (les arêtes pleines pour les axes connus, pointillées
   vers le sommet absent). Signale « ce côté est indéterminé ».

b) Plus simple : si un axe manque, **ne pas tracer le `tri-fill`** et afficher
   à la place les seuls points connus reliés, plus une mention. Mais cela casse
   la lecture « forme ».

Recommandation : option (a), ou a minima ajouter dans le `aria-label` (déjà fait,
bien) et conserver le marqueur `tri-na` en le rendant plus visible (croix plutôt
que cercle évidé). À cadrer dans `axis_triangle()`, section géométrie.

## I2 — Histogramme de corpus : alléger la version d'accueil

**Problème.** `corpus_histogram()` (l. 476-506) est appelé tel quel deux fois :
`render_index()` (l. 1531) et `render_methode()` (l. 1381). Même SVG 360×180,
mêmes 5 barres, même `figcaption`. Ce n'est pas faux — la page méthode est la
place canonique — mais sur l'accueil, juste après les cartes de catégories et
avant les 6 cartes de tête, l'histogramme fait redite avec le reste et allonge
une page déjà longue.

**Recommandation.** Soit :
- garder l'histogramme **sur la méthode uniquement** (sa place naturelle :
  « État du corpus »), et sur l'accueil le remplacer par une ligne de synthèse
  chiffrée déjà présente (« 4 aboutis · 3 solides… ») éventuellement doublée
  d'une **barre empilée horizontale unique** (un seul `<div>` segmenté, 5
  couleurs de palier) — bien plus sobre qu'un histogramme à axes ;
- soit passer un paramètre `compact=True` à `corpus_histogram()` pour une
  version réduite (barres plus fines, sans `figcaption`) sur l'accueil.

La barre empilée horizontale est préférable : une seule ligne, lecture
immédiate de la distribution, cohérente avec les segments `idl-seg` et `rk-seg`
déjà employés ailleurs. Composant `corpus_bar(all_sc, ranking)` en regard de
`corpus_histogram()`.

## I3 — Fiche : doter le triangle plein d'un repère d'échelle lisible

**Problème.** Sur la fiche (`score-main`, l. 635-640), le triangle plein
(140 px) n'a que deux polygones de cadre : `tri-frame` (100 %) et `tri-grid`
(50 %, pointillé). Sans graduation chiffrée ni légende au pied du triangle, le
lecteur doit déjà savoir que « sommet = 100, centre = 0 » pour l'interpréter.
Les barres `axis_bar` en dessous compensent — mais le triangle, présenté en
premier et en grand, devrait se suffire un minimum.

**Recommandation.** Léger, sans surcharge :
- annoter les trois sommets du triangle plein (non compact) d'un petit « 100 »
  et le centre d'un « 0 », en `font-size` ~6 px, couleur `--faint` ; ou
- ajouter sous le triangle une micro-légende d'une ligne : « Sommet = 100 ·
  centre = 0 ». À placer dans `axis_triangle()` sous condition `not compact`,
  ou dans le `score-block` de `render_fiche()`.

Cela rend le triangle autoporteur pour un primo-lecteur, sans alourdir les
vignettes (réservé au format plein).

---

# RECOMMANDATIONS MINEURES

## M1 — Modèles estimés : décimales parasites dans le triangle et le aria-label
`score_fiche()` pour `cat == "modele"` conserve les `axes_estimes` en `float`.
`axis_bar()` est protégé par `_fmtnum()` (bien), mais `axis_triangle()` injecte
les valeurs brutes dans le `aria-label` via `_fmtnum()` — vérifier que c'est
appliqué partout. Le plus propre : arrondir les axes à l'entier dès
`score_fiche()` pour le cas `modele` (`round(float(ax[k]))`), une seule source.

## M2 — `idl_scale` : la jauge linéaire est invisible aux lecteurs d'écran
`idl_scale()` (l. 451-473) est entièrement `aria-hidden="true"`. C'est défendable
(le badge anneau et les barres portent déjà la donnée), mais la jauge montre une
information que les autres composants n'ont pas : la **position de l'indice
parmi les paliers** et le **repère fantôme de l'indice brut**. Le paragraphe
`.completude` mentionne déjà l'indice brut en toutes lettres quand il diffère —
donc l'info chiffrée n'est pas perdue. Acceptable en l'état ; à documenter comme
choix assumé. Aucune action requise, simple traçabilité.

## M3 — `card-viz` : le triangle compact est `aria-hidden`, vérifier le contexte
Une fois C1 appliqué (triangle seul sur la carte), le triangle reste
`aria-hidden` car « `axis_bar` fournit les chiffres » — or `axis_bar` disparaît
de la carte. La donnée chiffrée reste accessible sur la fiche liée, et la carte
porte nom + palier + anneau : un lecteur d'écran n'est pas privé de l'essentiel.
Mais le commentaire du code (l. 401-402) devient faux. **Mettre à jour le
commentaire** ; envisager de passer le triangle compact en `role="img"` avec un
`aria-label` court (« Profil A/B/C ») puisqu'il devient le seul porteur visuel
du profil sur la carte.

## M4 — Légende du triangle absente des catalogues et de l'accueil
Les catalogues affichent bien une `.cat-legend` (« Profil tri-axes : A… B… C »).
L'accueil, lui, place des cartes à triangle (`top` et `modeles`) **sans aucune
légende** des trois axes au-dessus. Ajouter une ligne `.axe-legend` avant la
grille de cartes de tête dans `render_index()`, identique à celle des
catalogues. Cohérence et autoportance.

## M5 — `tri-fill` toujours teinté vert, quelle que soit l'entité
`.tri-fill` (CSS l. 135) a `fill:rgba(74,122,58,.16)` — un vert fixe, qui est
aussi la couleur de l'axe A. Sur une entité faible en A mais forte en B, le
remplissage vert peut suggérer à tort « bon score A ». Choisir un remplissage
**neutre** (gris très clair, `rgba(34,31,26,.10)`) découplé des couleurs d'axe :
le polygone porte la forme, les sommets portent la couleur ; le fond ne doit
rien signifier.

## M6 — Triangle compact : épaisseur du contour et taille des sommets
Sur le triangle compact (78 px), les `tri-vtx` ont `r="5"` et `tri-fill` un
contour `stroke-width:1.6` : à cette échelle, les trois pastilles de 5 px de
rayon mangent une grande part de la figure et peuvent masquer les arêtes du
polygone quand un score est élevé (point proche du sommet). Réduire `r` à ~3.5
pour le rendu compact (paramétrer le rayon selon `compact`), garder 5 pour le
plein format.

---

# Synthèse — ordre d'intégration recommandé

| Prio | Reco | Effort | Impact |
|------|------|--------|--------|
| Critique | C1 Carte : triangle seul, retirer les barres | Faible | Très fort — supprime la surcharge n°1 |
| Importante | I1 Triangle : axe n.r. non trompeur | Moyen | Fort — honnêteté de la figure |
| Importante | I2 Histogramme accueil → barre empilée sobre | Faible | Moyen |
| Importante | I3 Repère d'échelle sur le triangle plein | Faible | Moyen |
| Mineure | M1 Décimales modèles | Faible | Finition |
| Mineure | M2 idl_scale a11y (traçabilité) | — | — |
| Mineure | M3 Commentaire + a11y triangle de carte | Faible | Cohérence |
| Mineure | M4 Légende d'axes sur l'accueil | Faible | Cohérence |
| Mineure | M5 tri-fill neutre, découplé de l'axe A | Faible | Honnêteté |
| Mineure | M6 Sommets compacts plus petits | Faible | Lisibilité |

Aucune proposition n'introduit de dépendance : tout est SVG/CSS généré par
Python. Le geste central de ce cycle est soustractif — **retirer** les barres
redondantes de la carte (C1) — fidèle à l'objectif : sobriété, pas de surcharge.
