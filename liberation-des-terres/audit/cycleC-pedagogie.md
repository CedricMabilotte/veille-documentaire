# Cycle C — Audit pédagogie & clarté du contenu

Audit en lecture seule. Angle : un non-juriste comprend-il l'enjeu et le
vocabulaire ? Pages examinées : `index`, `regimes`, `methode`, `grilles`,
`glossaire`, fiche `l/larzac`.

## Verdict global

Le site est **remarquablement clair et honnête** pour un sujet aussi technique.
Le ton est juste : précis sans être jargonneux, sobre sans être simpliste. Les
définitions sont exactes juridiquement (article 619, plafond 30 ans, baux,
domanialité — rien de faux relevé). La page « Trois régimes » est juste et bien
construite ; le callout « Un régime n'est pas une fatalité » évite le piège du
manichéisme. La méthode est transparente et assume ses limites.

Les faiblesses sont **uniquement des défauts de liaison et d'amorçage**, pas de
contenu. Le glossaire existe mais n'est presque jamais atteint depuis les
endroits où le lecteur bute sur un mot. Aucun dispositif ne prend le novice par
la main sur sa première fiche.

---

## CRITIQUE

### C1 — Le glossaire est un cul-de-sac : termes pivots jamais reliés en contexte
**Localisation :** toutes les pages de contenu (`index`, `regimes`, `methode`,
`grilles`, fiches `l/`, `p/`, `u/`).

Le glossaire est complet et bien rédigé, mais **aucune occurrence de terme
technique dans le corps des pages ne pointe vers sa définition**. Recherche
confirmée : `glossaire.html#g-` n'apparaît qu'une seule fois sur tout le site
(dans le JSON-LD du glossaire lui-même), et il n'existe **aucun élément
`<abbr>`**. Un non-juriste qui lit « démembrement », « nue-propriété »,
« usufruit », « dotation non consomptible », « bail emphytéotique »,
« inaliénabilité », « clause de dévolution » dans une fiche ou dans la grille
n'a aucun moyen d'obtenir la définition sans deviner que la page Glossaire
existe (elle n'est même pas dans la navigation principale, voir C2).

Le cas le plus aigu : la **page Grilles** emploie en cascade « dotation non
consomptible », « clause de dévolution désintéressée », « requalification
fiscale », « bail rural environnemental », « domanialité » dans les définitions
de critères — ces définitions de critères sont elles-mêmes le niveau
d'explication, mais elles s'appuient sur du vocabulaire non explicité sur place.

**Recommandation (sans surcharge) :** lier la **première occurrence** de chaque
terme pivot, par page, vers l'ancre du glossaire (`glossaire.html#g-usufruit`).
Les ancres existent déjà (`id="g-..."`). Un simple lien souligné discrètement,
une fois par page, suffit — pas besoin d'infobulle JavaScript. C'est l'amélioration
au meilleur rapport clarté/effort.

### C2 — Le glossaire et la page Régimes sont absents de la navigation principale
**Localisation :** `<nav class="topnav">` de toutes les pages.

La barre de navigation contient : Accueil, Lieux, Porteurs, Usufruitiers,
Classement, Méthode. **Ni « Glossaire » ni « Trois régimes » n'y figurent.**
Ces deux pages sont les portes d'entrée pédagogiques du site : un novice arrivé
sur une fiche depuis un moteur de recherche ne les trouvera que s'il repère les
liens en pied de page ou un lien contextuel. Pour un site dont la mission est
d'« expliquer les montages », c'est un défaut de hiérarchie.

**Recommandation :** ajouter au moins « Glossaire » à la `topnav` (le terme est
court, il tient). « Régimes » peut rester en lien contextuel si la barre devient
trop chargée, mais Glossaire doit être atteignable en un clic depuis n'importe
quelle page.

---

## IMPORTANTE

### I1 — Aucun exemple guidé « comment lire une fiche »
**Localisation :** absent ; à placer sur `index` (section « Comment lire cet
annuaire ») ou en tête de `methode`.

L'accueil explique le concept en 3 étapes, mais l'étape 3 (« Lire une note »)
reste abstraite : « notée de 0 à 100 sur trois axes — A, B, C ». Le lecteur qui
ouvre ensuite la fiche Larzac découvre d'un coup : un badge anneau, un triangle
tri-axes, trois barres d'axes, une échelle de paliers à curseur, un encart
complétude, une grille de 12 critères avec « oui/partiel/non », une « lecture »
par critère. **Rien ne lui dit dans quel ordre lire, ni ce que chaque bloc veut
dire.** Le triangle tri-axes en particulier n'est expliqué nulle part de façon
accessible (un novice ne devine pas qu'un triangle « plein » = bon score sur les
trois axes).

**Recommandation (légère) :** une courte section « Anatomie d'une fiche » — soit
sur la page Méthode, soit en encart dépliable. 5–6 lignes légendant les blocs
dans l'ordre : badge Indice → triangle (lire : plus la forme est grande et
régulière, plus le montage est solide sur les 3 axes) → barres d'axes → grille
détaillée → fiabilité. Pas un tutoriel long : une légende annotée.

### I3 — Le triangle tri-axes manque d'une clé de lecture explicite
**Localisation :** `index` (cartes), fiches (bloc score), `aria-label` corrects
mais aucune légende visible.

Le profil tri-axes est l'élément visuel signature du site. Son `aria-label` est
excellent pour les lecteurs d'écran (« intérêt général 100, libération 100,
gouvernance 86 »), mais **le lecteur voyant n'a pas l'équivalent** : il voit un
triangle déformé sans savoir que « sommet A en haut, B en bas à droite, C en bas
à gauche » ni que la surface remplie représente le score. La légende des pastilles
de couleur existe (« A — Intérêt général » etc.) mais pas la règle de lecture de
la forme.

**Recommandation :** une phrase unique, près du premier triangle de la fiche ou
dans la section « Anatomie d'une fiche » (I1) : « Plus la zone colorée s'étend
vers un sommet, plus le montage est noté sur cet axe. » Mutualisable avec I1.

### I4 — Termes employés mais absents du glossaire
**Localisation :** `glossaire.html` (lacunes), pages utilisatrices.

Le glossaire couvre bien les termes juridiques pivots. Manquent quelques termes
**structurants du vocabulaire propre au site**, que le novice rencontre sans
définition :

- **« Modèle voisin »** — catégorie entière du site (page `modeles.html`, cartes
  d'accueil), jamais définie au glossaire. La page d'accueil dit « modèles
  puristes proches » sans expliquer pourquoi ils sont « hors classement » ni ce
  que « estimé » veut dire précisément.
- **« Idéal-type »** — employé dans `methode.html` (« le montage de référence
  […] est un idéal-type »). Terme de sociologie non évident pour un novice.
- **« Démembrement » vs « dissociation »** — l'accueil parle de « dissocier la
  propriété », la méthode de « dissociation de la propriété et de l'usage », le
  glossaire ne définit que « démembrement ». Un novice peut croire à deux notions
  distinctes. Une ligne dans l'entrée Démembrement (« on parle aussi de
  *dissociation* propriété/usage ») lèverait l'ambiguïté.
- **« Porteur de nue-propriété »** / **« usufruitier »** comme *rôles* — les
  catégories du site. « Nue-propriété » et « usufruit » sont définis, mais pas
  les rôles d'acteur qui structurent toute la navigation.

**Recommandation :** ajouter 2–3 entrées (« Modèle voisin », « Idéal-type », et
éventuellement « Indice estimé ») et une demi-phrase de synonymie dans
« Démembrement ». Ne pas alourdir : ces ajouts sont brefs.

---

## MINEURE

### M1 — Pas de FAQ courte
Le site n'a pas de FAQ. Ce n'est **pas un manque grave** — méthode et limites
répondent déjà à l'essentiel — et une FAQ pléthorique surchargerait. Mais 4–5
questions franches manqueraient utilement : « Est-ce un label ? » (non, déjà dit
mais dispersé), « Pourquoi noter des lieux militants ? », « Qui peut proposer un
lieu ? », « L'usufruit de 30 ans veut-il dire que tout s'effondre dans 30 ans ? »
(question naturelle après lecture de la méthode — la réponse nuancée existe déjà
dans le « Verrou central » mais mériterait d'être posée comme une question).
**Recommandation :** optionnel. Si ajout, une FAQ *courte* (5 Q/R max), en bas
de Méthode, sans page dédiée.

### M2 — « Verrou central » de la méthode : excellent mais dense
`methode.html` §Corpus, paragraphe « Verrou central » : le passage sur le plafond
de 30 ans, ses exceptions (baux ruraux, emphytéotiques, propriété publique) est
**juridiquement irréprochable et pédagogiquement précieux** — c'est ce qui évite
le contresens « tout montage est fragile ». Mais il est livré en un seul bloc
dense de 6 lignes. Un novice peut décrocher.
**Recommandation :** scinder en deux phrases courtes ou poser la nuance en
incise visuelle (gras sur « QUE les démembrements véritables » déjà présent —
bien). Amélioration de confort, pas de correction.

### M3 — Première occurrence du sigle « SCIC », « FRUP », « OFS », « BRS », « GFA »
`index` et fiches emploient des sigles parfois développés une fois, parfois non.
« FRUP » est développé sur l'accueil (« Fondation reconnue d'utilité publique
(FRUP) »), bien. « SCIC » est développé en card-meta. Mais l'usage est inégal
selon les pages. Idéalement, première occurrence = forme développée + sigle, et
sigle relié au glossaire (rejoint C1). Le glossaire a « Fondation RUP » mais pas
d'entrée « SCIC », « OFS », « BRS », « GFA ». **Recommandation :** harmoniser ;
soit entrées de glossaire, soit développement systématique à la première
occurrence. Mineur car le contexte aide souvent à deviner.

### M4 — Pas de schéma simple du montage
Le site visualise très bien la *notation* (triangle, anneaux, histogramme) mais
**jamais le montage lui-même** : qui détient la nue-propriété, qui a l'usage,
quel contrat les lie. Un schéma minimal — trois boîtes « Porteur (nue-propriété)
→ contrat → Usufruitier (usage) → Lieu » — sur la page Régimes ou Méthode
ancrerait le concept central pour les visuels. **Recommandation :** optionnel et
seulement s'il reste léger (SVG statique, pas d'interaction). À ne PAS faire si
cela doit alourdir : la priorité reste C1/C2/I1.

---

## Synthèse de priorisation

| # | Sévérité | Action | Effort |
|---|----------|--------|--------|
| C1 | Critique | Lier la 1ʳᵉ occurrence des termes pivots au glossaire (ancres déjà là) | Moyen |
| C2 | Critique | Ajouter « Glossaire » à la navigation principale | Faible |
| I1 | Importante | Section « Anatomie d'une fiche » (légende des blocs) | Moyen |
| I3 | Importante | Clé de lecture visible du triangle tri-axes (mutualisable I1) | Faible |
| I4 | Importante | 2–3 entrées glossaire manquantes + synonymie « dissociation » | Faible |
| M1 | Mineure | FAQ courte (5 Q/R) en bas de Méthode — optionnel | Faible |
| M2 | Mineure | Aérer le paragraphe « Verrou central » | Faible |
| M3 | Mineure | Harmoniser sigles + entrées glossaire SCIC/OFS/BRS/GFA | Faible |
| M4 | Mineure | Schéma simple du montage — optionnel, seulement si léger | Moyen |

**Aucune explication fausse ou trompeuse n'a été relevée.** Le contenu juridique
est exact et nuancé. Les améliorations portent toutes sur la *liaison* et
l'*amorçage* pédagogiques, pas sur le fond.
