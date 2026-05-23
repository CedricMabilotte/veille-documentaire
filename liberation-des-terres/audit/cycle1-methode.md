# Audit de solidité méthodologique — « Terres Libérées »

**Cycle 1 · Méthodologie de l'Indice de libération · 2026-05-23**
**Lecture seule — aucun fichier modifié.**

Périmètre : `config/ranking.yml`, `config/grilles.yml`, `scripts/generate_site.py`
(fonction `score_fiche`), `site/data.json`, fiches YAML. L'audit porte sur la
*solidité de la méthode*, pas sur l'exactitude factuelle des fiches.

---

## 1. Synthèse

L'architecture est saine : axes explicites, formule simple et documentée, séparation
nette entre Indice et « pureté juridique », export `data.json` ouvert. Le classement
est néanmoins affecté par **six faiblesses méthodologiques**, dont deux critiques :
le traitement des critères « inconnu » qui **surnote les fiches mal documentées**, et
l'**absence d'isolement explicite des axes estimés** des modèles voisins, qui ne sont
en pratique pas mélangés au classement mais ne sont pas non plus signalés comme
non comparables.

Tableau des constats :

| # | Constat | Priorité |
|---|---------|----------|
| 1 | « Inconnu » exclu du dénominateur → surnotation des fiches lacunaires | **Critique** |
| 2 | Axe C sous-pondéré ; nombre de critères et poids d'axe non homogènes entre grilles | Importante |
| 3 | Paliers mal calibrés : 0 fiche dans les 2 paliers bas, 50 % en « solide » | Importante |
| 4 | Comparabilité lieu/porteur/usufruitier sur un classement unique non justifiée | Importante |
| 5 | Modèles voisins (axes_estimés) : exclus du classement mais pas signalés comme non comparables | **Critique** |
| 6 | Transparence : score par critère non affiché, contribution non reconstituable | Importante |

---

## 2. Analyse détaillée

### 2.1 — Traitement des critères « inconnu » (Constat 1)

**Mécanique actuelle.** `score_fiche` (lignes 113-119 de `generate_site.py`) ignore
tout critère « inconnu » : il n'entre ni au numérateur ni au dénominateur de l'axe.
Un axe entièrement inconnu devient `null` (ligne 123), et l'Indice global est la
moyenne des seuls axes non-null (ligne 125).

**Le problème — démonstration sur Villarceaux.** La fiche `villarceaux.yml` a ses
**trois critères de gouvernance en « inconnu »** (`gouvernance_collective`,
`tripartisme`, `perennite_gouvernance`). Résultat dans `data.json` :

```
Villarceaux : A=86, B=75, C=null  →  IdL = (86+75)/2 = 80  →  palier « Montage solide »
```

Une fiche dont **un tiers de la grille — l'axe entier le plus exigeant — est un
angle mort** obtient 80/100 et le label « solide », à égalité avec des fiches
intégralement renseignées. La gouvernance non documentée est traitée comme si elle
n'existait pas, et non comme un risque. C'est une **surnotation structurelle des
montages opaques** — alors même que l'opacité est précisément un défaut que la
grille « lieu » dit vouloir sanctionner (« un montage opaque fragilise la
confiance »).

Le garde-fou prévu — la complétude (ligne 126) — ne corrige rien : elle est
*affichée à côté* du score mais **ne le déforme pas** et **n'apparaît ni dans le
classement ni dans `data.json`**. Un lecteur du tableau `classement.html` voit
Villarceaux 8ᵉ à 80 points, sans aucun signal que son C est creux.

**Recommandation (voir R1).** Trois options, par ordre de rigueur :
- **(a) Indice non calculé si un axe est null.** Le plus honnête : on ne classe pas
  ce qu'on ne sait pas mesurer. Villarceaux sortirait du classement principal vers
  une liste « fiches incomplètes ».
- **(b) Pénalité de complétude appliquée au score** : `IdL_affiché = IdL_brut ×
  complétude` (ou un facteur plancher, p. ex. `0.5 + 0.5×complétude`). Villarceaux :
  80 × 0,70 = 56 → palier « Engagement réel », ce qui reflète l'incertitude.
- **(c) Axe inconnu compté comme 0 partiel** : trop punitif, écarté.

L'option **(b) est recommandée** : elle conserve un classement complet, rend la
complétude *agissante* et non décorative, et reste reproductible. À défaut,
l'option (a) est défendable. Dans tous les cas : **afficher la complétude dans
`classement.html` et `data.json`** (voir R6).

### 2.2 — Équilibre des poids et des critères (Constat 2)

Décompte des poids par axe et par grille (`grilles.yml`) :

| Grille | Critères A / poids A | Critères B / poids B | Critères C / poids C | Total |
|--------|----------------------|----------------------|----------------------|-------|
| porteur | 4 / **10** | 4 / 9 | 3 / **6** | 11 / 25 |
| usufruitier | 4 / **10** | 4 / 9 | 4 / 8 | 12 / 27 |
| lieu | 3 / **7** | 4 / **10** | 3 / 7 | 10 / 24 |

Deux déséquilibres :

1. **L'axe C est le parent pauvre.** Dans la grille `porteur`, C ne pèse que 6
   points (3 critères) contre 10 pour A. La gouvernance — pourtant l'une des trois
   finalités déclarées « aussi importantes l'une que l'autre » (ranking.yml l. 70) —
   est de fait sous-instrumentée. Comme chaque axe est *renormalisé à 100* avant la
   moyenne, ce déséquilibre n'affecte pas le poids de l'axe dans l'IdL, mais il
   affecte sa **granularité** : un axe C à 6 points ne peut produire que peu de
   valeurs distinctes (d'où la récurrence de « C=50 » dans `data.json` — 7 fiches
   sur 21). L'axe C est moins discriminant que A et B.

2. **A varie de 7 à 10 points selon la grille.** Le poids brut d'un axe n'est pas
   homogène entre catégories. Ce n'est pas faux en soi (la renormalisation absorbe
   l'écart) mais cela complique la comparaison inter-catégories (voir Constat 4) et
   trahit une grille non concertée axe par axe.

**Recommandation (R2).** Viser, dans chaque grille, **un poids total par axe
identique** (p. ex. 9-9-9) et **au moins 3 critères par axe**, idéalement 4. Pour la
grille `porteur`, ajouter un 4ᵉ critère C (p. ex. « renouvellement / transmission de
la gouvernance ») et rééquilibrer les poids.

### 2.3 — Calibrage des paliers (Constat 3)

Les 21 fiches du classement principal (`data.json`, hors modèles) se répartissent
ainsi sur les seuils 85 / 70 / 55 / 40 :

| Palier | Seuil | Effectif | Fiches |
|--------|-------|----------|--------|
| Libération aboutie | ≥ 85 | **5** | Larzac 95, Conservatoire 94, SCTL 92, Fond. TdL 89, Fermes TdL 88 |
| Montage solide | 70-84 | **10** | Écosite 82, Féd. CEN 81, Villarceaux 80, Fonds TE 78, NDDL/Coop. LM 75, Lurzaindia 74, Coop. Oasis 72, Ferme Enfants 71, Longo Maï 70 |
| Engagement réel | 55-69 | **6** | FPH 68, Foncière TdL 64, Hameau/Fonds LTC/GFA 62 |
| Libération partielle | 40-54 | **0** | — |
| Éloigné du modèle | 0-39 | **0** | — |

Deux problèmes :

- **Les deux paliers bas sont vides.** Aucune fiche sous 62. La grille de lecture
  prévoit cinq paliers ; le corpus n'en active que trois. Soit le corpus est
  biaisé vers les « bons élèves » (probable : c'est un annuaire militant), soit les
  seuils bas sont irréalistes.
- **Le palier « solide » est obèse** : 10 fiches sur 21 (48 %), étalées sur 70-82,
  soit une plage de 12 points pour la moitié du corpus. Le palier ne discrimine
  presque plus.

**Recommandation (R3).** Resserrer les seuils hauts et relever le plancher pour
coller à la dispersion réelle : **abouti ≥ 88, solide ≥ 76, engagé ≥ 64,
partiel ≥ 50**. Avec ce réglage : abouti 4, solide 6, engagé 8, partiel 3 — une
distribution exploitable. À recalibrer à chaque élargissement du corpus, et à
documenter comme tel dans `ranking.yml`. Alternative : assumer que le corpus est
volontairement sélectif et **réduire à 3 paliers**, mais alors retirer les libellés
« partielle » / « éloigné » qui promettent une sévérité que la méthode n'exerce pas.

### 2.4 — Comparabilité lieu / porteur / usufruitier (Constat 4)

`render_classement` (l. 536-537) fusionne les trois catégories dans **un seul
tableau trié par IdL**, alors que chacune est notée avec **une grille différente**
(critères, définitions et poids distincts). On classe donc un « lieu » et un
« porteur » sur une échelle qui n'a pas la même définition opérationnelle aux deux
extrémités.

Est-ce défendable ? **Partiellement.** Les trois grilles partagent les mêmes
axes A/B/C et la même formule, donc l'IdL mesure « la même chose » au niveau
conceptuel. Mais un porteur est jugé sur l'inaliénabilité de *son* patrimoine, un
lieu sur l'irréversibilité de *son* montage : un IdL de 80 ne désigne pas le même
objet. Comparer Larzac (lieu, 95) et Fondation TdL (porteur, 89) revient à
classer ensemble une pomme et le verger.

Surtout, **ce n'est pas expliqué.** La page `classement.html` (l. 564-568)
présente l'IdL comme une mesure unique sans signaler que les trois catégories
reposent sur trois grilles. Le filtre par catégorie existe mais le tri par défaut
est « tout confondu ».

**Recommandation (R4).** Garder le classement unifié (utile, lisible) mais :
(a) ajouter un encart explicite sur `classement.html` — « chaque catégorie est
notée avec sa propre grille ; les IdL sont comparables *en intention* mais pas
*terme à terme* » ; (b) afficher par défaut, ou proposer en évidence, **les
classements par catégorie** ; (c) ne jamais présenter un « rang absolu » comme un
verdict inter-catégories.

### 2.5 — Modèles voisins et axes estimés (Constat 5)

Les fiches `modeles/` ne sont **pas notées par la grille** : `score_fiche`
(l. 90-98) lit directement le bloc `axes_estimes` du YAML (ex. `ofs-brs.yml`
l. 32-35 : A 90 / B 90 / C 50, valeurs posées éditorialement). Leur IdL est la
moyenne de ces estimations à la main.

Points **positifs** vérifiés :
- Les modèles sont **exclus du classement principal** : `render_classement`
  filtre `f["categorie"] != "modele"` (l. 536). Bien.
- Le drapeau `estime: True` existe (l. 97) et `fiabilite_label` renvoie
  « Estimation comparative » (l. 144). Bien.

Points **problématiques** :
- Dans **`data.json`** (export ouvert, l. 1102-1107), les modèles apparaissent
  **avec un IdL et des axes, sans aucun champ distinguant estimé / calculé**. Un
  réutilisateur du jeu de données mélangera mécaniquement les 90,0 « estimés » du
  CLT de Bruxelles et les 95 « calculés » du Larzac. Le `.0` (float) est le seul
  indice — fragile et non documenté.
- Les modèles **dépassent le haut du classement** : CLT Bruxelles 90, devant tous
  les lieux sauf Larzac. Affichés ailleurs (`modeles.html`) avec un IdL d'apparence
  identique, ils créent une **fausse hiérarchie** : un score posé à la main n'a pas
  la même valeur probante qu'un score dérivé d'une grille critère par critère.
- La page `modeles.html` doit être vérifiée : le badge IdL y est rendu par le même
  `idl_badge` que les fiches calculées, sans marquage visuel distinct.

**Recommandation (R5).** (a) Ajouter dans `data.json` un champ
`"score_type": "calcule" | "estime"` pour chaque entrée. (b) Sur toute page
affichant un modèle, **marquer visuellement l'IdL comme estimé** (badge grisé,
mention « estimation comparative » accolée au nombre, pas seulement dans le bloc
fiabilité). (c) Idéalement : soumettre les modèles voisins à la **vraie grille**
(grille `porteur` ou une grille `modele` dédiée) plutôt qu'à une estimation, pour
qu'ils deviennent réellement comparables — sinon les présenter comme un **repère
qualitatif**, jamais comme un rang chiffré aligné sur les fiches calculées.

### 2.6 — Transparence et reconstituabilité (Constat 6)

Un lecteur peut-il **reconstituer un score** ? Partiellement.
- La formule est publiée (`methode.html` l. 697), le mapping des valeurs aussi.
- La fiche détaillée affiche bien la grille critère par critère avec
  oui/partiel/non/inconnu (`render_fiche`, table `grille-tbl`, l. 406-439).

Mais il **manque les éléments pour refaire le calcul** :
- **Le poids de chaque critère n'est pas affiché sur la fiche.** Il figure sur
  `grilles.html` (l. 624) mais pas dans le tableau de la fiche elle-même : le
  lecteur doit faire l'aller-retour entre deux pages pour reconstituer un axe.
- **La contribution de chaque critère au score d'axe n'est jamais montrée.** On ne
  voit pas que `inalienabilite` (poids 3, « partiel ») a apporté 1,5/3 à l'axe B.
- **Le score d'axe n'est pas décomposé** : on voit « B = 75 » sans le détail
  Σpoids×facteur / Σpoids.
- `data.json` ne contient ni la complétude, ni le détail par critère : un
  réutilisateur ne peut pas auditer le chiffre.

**Recommandation (R6).** (a) Ajouter la colonne **« Poids »** au tableau de grille
de la fiche détaillée (`render_fiche`, déjà disponible dans `criteres_evalues`).
(b) Afficher, sous chaque axe, le **détail du calcul** (« B = 8,5 / 11,5 → 74 »).
(c) Enrichir `data.json` : `completude`, `score_type`, et un bloc `criteres` par
fiche (id, valeur, poids, axe). Le principe affiché « le score en découle
directement » (grilles.html l. 656) n'est tenu que si le lecteur dispose
réellement de tous les termes.

---

## 3. Recommandations classées

### CRITIQUE

**R1 — Cesser de surnoter les fiches lacunaires.**
*Fichiers :* `generate_site.py` (`score_fiche`), `ranking.yml`.
*Modif :* appliquer une pénalité de complétude au score affiché.
Dans `score_fiche`, après calcul de `idl` et `completude`, ajouter :
`idl_ajuste = round(idl * (0.5 + 0.5 * completude))` quand `completude is not None`.
Exposer `idl_brut` et `idl_ajuste`. Le classement et `data.json` utilisent
`idl_ajuste`. *Effet chiffré :* Villarceaux passe de 80 (« solide ») à
80 × (0,5 + 0,5 × 0,70) = **68 (« Engagement réel »)** — cohérent avec un axe C
intégralement inconnu. Dans `ranking.yml`, documenter la formule de pénalité sous
`note_fiabilite`. *Variante (a) plus stricte :* si un axe est `null`, `idl = None`
et la fiche bascule dans une liste « fiches incomplètes » hors classement.

**R5 — Isoler les axes estimés des scores calculés.**
*Fichiers :* `generate_site.py` (`score_fiche`, export `data.json`,
`idl_badge`/`render_*`).
*Modif :* (1) ajouter `"score_type"` (`"calcule"`/`"estime"`) dans le dict renvoyé
par `score_fiche` et dans chaque entrée de `data.json` (l. 1104-1106). (2) Dans
`idl_badge`, accepter un paramètre `estime` et, si vrai, rendre un badge visuellement
distinct (classe `idl-estime`, libellé « estimé ») — à styler dans `CSS`. (3) Sur
`modeles.html`, accoler la mention « estimation comparative » au nombre. Objectif :
qu'aucun lecteur ni aucun réutilisateur de `data.json` ne confonde un 90 posé à la
main avec un 95 dérivé d'une grille.

### IMPORTANTE

**R2 — Homogénéiser poids et nombre de critères entre axes et grilles.**
*Fichier :* `grilles.yml`.
*Modif :* viser, dans chaque grille, un **poids total par axe identique** (cible
9/9/9) et **≥ 3 critères par axe**. Concrètement : grille `porteur`, l'axe C ne
pèse que 6 pts pour 3 critères — ajouter un 4ᵉ critère C (« renouvellement et
transmission de la gouvernance », poids 1-2) et porter les poids C à 9 ;
réduire d'un point l'un des critères A (poids A : 10 → 9). Grille `lieu`, axe A à
7 pts seulement : remonter à 9 (p. ex. `usage_interet_general` 3→4,
`ancrage_territorial` 2→3). Objectif : ~9/9/9 partout, granularité comparable des
trois axes.

**R3 — Recalibrer les paliers sur la dispersion réelle.**
*Fichier :* `ranking.yml`, bloc `paliers`.
*Modif :* remplacer les seuils `min` 85/70/55/40/0 par **88/76/64/50/0**. Sur le
corpus actuel : abouti 4, solide 6, engagé 8, partiel 3 (au lieu de 5/10/6/0/0).
Ajouter un commentaire indiquant que les seuils sont calibrés sur le corpus du
2026-05-23 et à réviser à chaque élargissement notable. *Alternative :* si l'on
assume un corpus sélectif, passer à 3 paliers et supprimer les libellés
« partielle »/« éloigné ».

**R4 — Cadrer la comparabilité inter-catégories.**
*Fichiers :* `generate_site.py` (`render_classement`), éventuellement
`ranking.yml`.
*Modif :* dans `render_classement`, ajouter un encart juste sous le `<h1>` :
« Chaque catégorie est évaluée avec sa propre grille (porteur · usufruitier ·
lieu). Les IdL sont comparables *dans leur intention* mais pas *critère à
critère* ; pour une comparaison rigoureuse, filtrer par catégorie. » Mettre le
filtre par catégorie plus en évidence. Ne pas présenter le rang `#` comme un
verdict absolu inter-catégories.

**R6 — Rendre le score reconstituable sur la fiche.**
*Fichier :* `generate_site.py` (`render_fiche`, export `data.json`).
*Modif :* (1) ajouter une colonne **« Poids »** au tableau `grille-tbl` de la
fiche (donnée déjà présente dans `criteres_evalues[cid]["poids"]`). (2) Afficher
sous le bloc axes le **détail du calcul** par axe (`Σpoids×facteur / Σpoids → score`).
(3) Enrichir `data.json` : ajouter `completude`, `score_type` et un tableau
`criteres` (`id`, `axe`, `poids`, `valeur`) par fiche.

### MINEURE

**R7 — Exposer la complétude dans le classement.**
*Fichier :* `generate_site.py` (`render_classement`).
*Modif :* ajouter une colonne ou une pastille « complétude » dans `rank-tbl`,
pour qu'une fiche peu renseignée soit signalée *dans* le tableau et pas seulement
sur sa fiche. Complément naturel de R1.

**R8 — Clarifier le statut de la pondération d'axes.**
*Fichier :* `ranking.yml` (bloc `indice.ponderation`).
*Modif :* le commentaire « volontairement égale » est sain, mais la pondération
1/1/1 est inerte tant que les axes sont renormalisés à 100. Préciser dans le
commentaire que l'égalité de poids des *axes* est réelle, mais que l'égalité des
*finalités* dépend aussi de R2 (granularité comparable des grilles) — sinon un axe
sous-instrumenté pèse « moins » en pratique malgré un poids nominal de 1.

**R9 — Tracer la version de calibrage.**
*Fichier :* `ranking.yml`.
*Modif :* ajouter un champ `calibrage: { date, n_fiches }` à côté de `version`,
pour qu'une révision des seuils (R3) soit traçable et que la reproductibilité du
classement soit datée.

---

## 4. Priorité d'intégration

1. **R1** (surnotation) et **R5** (axes estimés) — corrigent deux biais qui
   faussent directement la lecture du classement.
2. **R3** (paliers) et **R6** (transparence) — rendent le classement
   discriminant et auditable.
3. **R2** (équilibre des grilles) et **R4** (comparabilité) — consolident la
   cohérence d'ensemble.
4. **R7-R9** — finitions de transparence et de traçabilité.

*Fin du rapport — cycle 1.*
