# Cycle D — Transparence du corpus et de ses biais

**Date :** 2026-05-23
**Angle :** honnêteté documentaire — le site dit-il assez clairement ce qu'il
couvre, ce qu'il ne couvre PAS, et de quels biais il est porteur ?
**Mode :** lecture seule. Aucune fiche ni page modifiée — proposition d'édition
ciblée pour la page Méthode existante.

---

## 1. Constat : la transparence actuelle est partielle

La page `methode.html` fait du bon travail sur le **comment** : calcul de
l'Indice exposé en clair, pénalité de complétude expliquée, paliers tabulés,
section « Limites » honnête (sources publiques, indice = grille discutable,
« inconnu » signalé, idéal-type rarement atteint). Le principe éditorial
« distinguer faits vérifiés et non confirmés » est tenu : chaque fiche a un
bloc `fiabilite` qui sépare explicitement les deux.

Mais la section **« État du corpus »** se limite à une ligne de comptage
(« 8 lieux · 13 porteurs · 7 usufruitiers · 5 modèles ») et à un histogramme
de distribution des notes. Elle ne dit **rien** :

- de ce que le corpus **ne couvre pas** (les angles morts) ;
- de sa **composition déséquilibrée** (poids de la galaxie Terre de Liens) ;
- de son **taux de complétude réel** ni de la **part de critères « inconnu »**.

Le projet parent BIBLIO publiait un « état du corpus » quantifiant ses propres
biais. Ici, l'honnêteté est présente sur la *méthode de notation* mais pas sur
la *représentativité du corpus*. C'est l'angle mort de la transparence.

L'audit `cycleA-corpus.md` avait déjà identifié les angles morts et proposé
des fiches pour les combler ; plusieurs l'ont été (Habicoop, Village Vertical,
coopérative ALUR, Foncière Chênelet, SCIC Terres de Sources, Champs des
Possibles). Mais ce travail d'autocritique est resté **dans l'audit** : il n'a
jamais été restitué au lecteur du site. Le public ne voit ni les angles morts
restants, ni le fait que l'habitat n'est représenté que par une poignée de
fiches récemment ajoutées.

---

## 2. Chiffres réels du corpus (33 fiches, vérifiés)

### 2.1 Composition

| Catégorie | Effectif |
|---|---|
| Lieux | 8 |
| Porteurs de nue-propriété | 13 |
| Organismes usufruitiers | 7 |
| Modèles voisins | 5 |
| **Total** | **33** |

Entrées notées par la grille (modèles exclus) : **28**.

### 2.2 Statut des fiches

Les **33 fiches sont en statut `publie`**. Aucune ébauche : la distinction
ébauche / publié existe dans le schéma mais n'a, à ce jour, aucun cas. Il est
plus honnête de **le dire** que de laisser croire à un filtre actif — ou de
supprimer la mention si elle n'est pas utilisée.

### 2.3 Complétude des grilles

Critères évaluables, toutes fiches notées confondues : **381**
(lieu 11×8 + usufruitier 14×7 + porteur 15×13).

| Valeur | Nombre | Part |
|---|---|---|
| oui | 183 | 48 % |
| partiel | 148 | 39 % |
| non | 8 | 2 % |
| **inconnu** | **42** | **11 %** |

**Complétude moyenne du corpus : ~89 %.** C'est bon. Mais la moyenne masque
des fiches nettement plus lacunaires :

- Écosite de Villarceaux — 5 « inconnu » / 14 → complétude ~64 %
- Fondation FPH — 4 / 15 → ~73 %
- GFA mutuels — 4 / 14 → ~71 %

Le générateur affiche déjà la complétude **par fiche** (bandeau de fiabilité),
mais le **chiffre global** n'apparaît nulle part. C'est précisément le genre
de chiffre qu'un « état du corpus » honnête doit donner.

### 2.4 Biais de sources : la galaxie Terre de Liens

Trois fiches **sont** la galaxie Terre de Liens : Fondation Terre de Liens,
Foncière Terre de Liens, Fermes Terre de Liens (fiche-réseau). Au-delà, la
mouvance TdL irrigue le corpus : 8 fiches sur 33 citent Terre de Liens comme
partenaire, source ou matrice (FEVE, Antidote, Lurzaindia, GFA mutuels,
RENETA…). Ce n'est pas un défaut — TdL est l'acteur structurant du sujet en
France — mais c'est un **biais de centralité** qu'il faut nommer : le corpus
regarde le paysage en grande partie depuis ce point de vue.

### 2.5 Biais thématique et géographique

**Thématique.** Le corpus est très majoritairement **agricole / rural**.
L'habitat n'est représenté que par 4 entrées récentes (Village Vertical,
Habicoop, coopérative ALUR — un modèle —, Foncière Chênelet). Le foncier
naturel est présent (Conservatoire du littoral, CEN). Restent faibles ou
absents : le **foncier solidaire de logement urbain** hors agricole,
le **périurbain** structuré (une seule entrée nette, Terres de Sources).

**Géographique.** Les 7 lieux localisés couvrent 6 régions
(Auvergne-Rhône-Alpes ×2, Occitanie, PACA, Nouvelle-Aquitaine, Pays de la
Loire, Île-de-France), plus une fiche-réseau nationale. Concentration sur la
moitié sud et est. **Absents :** Hauts-de-France, Grand Est, Normandie,
Bourgogne-Franche-Comté, Centre-Val de Loire, Corse — et **la totalité de
l'Outre-mer**, écarté faute de cible vérifiable (cf. `cycleA-corpus.md`).

---

## 3. Proposition : enrichir « État du corpus » — sobrement

Pas de nouvelle page, pas de tableau de bord. **Une réécriture ciblée de la
section `#etat` existante** dans `render_methode()` : on garde l'histogramme
(déjà disponible, déjà accessible), on ajoute deux courts paragraphes —
« Complétude » et « Ce que le corpus ne couvre pas encore » — et on rend
quelques chiffres explicites. Trois à cinq phrases honnêtes suffisent.

### 3.1 Texte proposé pour la section « État du corpus »

> **État du corpus**
>
> 8 lieux · 13 porteurs de nue-propriété · 7 organismes usufruitiers ·
> 5 modèles voisins de comparaison. Les 33 fiches sont publiées ; le corpus
> est construit, non exhaustif.
>
> *[histogramme inchangé]*
>
> **Complétude.** Les 28 entrées notées renseignent environ 89 % des critères
> de leur grille ; 11 % restent « inconnu », faute de source publique. La
> complétude de chaque fiche est affichée sur la fiche elle-même ; quelques
> fiches (Écosite de Villarceaux, Fondation FPH, GFA mutuels) restent
> nettement plus lacunaires et leur Indice est à lire avec prudence.
>
> **Ce que le corpus ne couvre pas encore.** Le recensement est partiel et
> assume ses angles morts. Il regarde le sujet en grande partie depuis la
> mouvance Terre de Liens, acteur structurant du foncier agricole non
> spéculatif en France. Il est très majoritairement **rural et agricole** :
> l'habitat coopératif n'y figure que par quelques entrées récentes, le
> foncier solidaire de logement urbain et le périurbain structuré restent peu
> représentés. Géographiquement, les lieux se concentrent sur la moitié sud et
> est de la métropole ; plusieurs régions et **l'ensemble de l'Outre-mer** ne
> sont pas couverts. Ces manques sont documentés dans les notes d'audit du
> projet et signalent des pistes d'enrichissement, non des choix d'exclusion.

### 3.2 Mise en œuvre technique (légère)

Trois options, par ordre de sobriété croissante de l'effort :

1. **Minimal — texte statique.** Ajouter les deux paragraphes en dur dans la
   `body` de `render_methode()`. Les chiffres « 89 % / 11 % » sont stables
   tant que les grilles ne bougent pas. Risque : se périmer si le corpus
   évolue. Acceptable pour un site qui se régénère à chaque commit.

2. **Recommandé — chiffres calculés.** `render_methode()` reçoit déjà
   `all_sc` (tous les scores). La complétude moyenne et la part d'« inconnu »
   se calculent en quelques lignes à partir de `sc["completude"]` et de
   `sc["criteres_evalues"]`, puis s'injectent dans le texte. Le commentaire
   sur les angles morts reste éditorial (rédigé à la main) : c'est un jugement,
   pas une statistique, et il doit le rester. Aucune dépendance nouvelle,
   aucune page nouvelle, ~15 lignes de Python.

3. **À ne PAS faire.** Créer une page « Transparence » dédiée, un second
   histogramme (complétude par fiche), un tableau région par région. Cela
   alourdirait le site pour un gain marginal : l'honnêteté tient en un
   paragraphe, pas en un tableau de bord. Le triangle, l'histogramme et le
   bandeau de complétude par fiche couvrent déjà le besoin visuel.

**La petite visualisation déjà disponible** — l'histogramme de distribution —
est conservée telle quelle. Elle est pertinente et accessible (`aria-label`,
`figcaption`). Inutile d'en ajouter une autre : le texte fait le reste.

### 3.3 Retouches connexes (optionnelles, mineures)

- **Section « Limites ».** Ajouter une puce : « Le corpus est construit et
  non exhaustif ; sa composition (forte présence de la mouvance Terre de
  Liens, sous-représentation de l'habitat et de l'Outre-mer) est détaillée
  dans l'État du corpus. » Un lien interne `#etat` suffit.
- **Sommaire de page (`page-toc`).** L'entrée « État du corpus » existe déjà :
  rien à faire.

---

## 4. Avis tranché

**Le site n'est pas assez transparent sur ce qu'il ne couvre pas.** Il est
rigoureux et honnête sur sa *méthode de notation* — c'est même un point fort
réel — mais il laisse le lecteur ignorer que le corpus est construit, partiel,
centré sur la galaxie Terre de Liens et quasi exclusivement rural et
métropolitain. Un lecteur pressé peut croire l'annuaire représentatif du
paysage français de la libération des terres. Il ne l'est pas, et le projet
le sait : l'audit `cycleA-corpus.md` l'a écrit noir sur blanc. Ne pas le dire
au public est une **incohérence entre l'exigence interne et la façade
publique**.

Le correctif est petit, et c'est ce qui le rend obligatoire : **deux
paragraphes dans une section qui existe déjà**, des chiffres réels que le
générateur peut produire seul (option 2), zéro page nouvelle, zéro poids
supplémentaire de chargement. Le rapport bénéfice/coût est imbattable.

**Recommandation : appliquer l'option 2** (chiffres calculés + commentaire
éditorial sur les angles morts) et ajouter la puce de la section « Limites ».
C'est l'enrichissement le plus fidèle à l'esprit du projet parent BIBLIO :
une honnêteté documentaire qui se chiffre, sobrement, sans se mettre en scène.
