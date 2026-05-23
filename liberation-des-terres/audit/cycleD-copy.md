# Cycle D — Audit copywriting & micro-polish

Audit en lecture seule. Angle : pure qualité d'écriture des textes d'interface
produits par `scripts/generate_site.py` (et microcopie de `site/assets/list.js`).
Aucun ajout de contenu : seulement reformulations, registre, microcopie,
typographie. Le fond — données, juridique, méthode — n'est pas touché.

## Verdict global

L'écriture est déjà solide : ton documentaire tenu, sobre, sans dérive
marketing. Les faiblesses sont rares et localisées. Le défaut le plus
systématique n'est pas une formulation mais la **typographie française** :
aucune espace insécable n'est posée devant `: ; ? !` ni à l'intérieur des
guillemets `«  »`. Le reste relève du micro-polish : quelques accroches
plates, des libellés perfectibles et deux ou trois tournures vagues.

---

## IMPORTANTE

### D1 — Typographie française : espaces insécables absentes
**Localisation :** transversal — fonction `clean()` / `e()` dans
`generate_site.py`, et toutes les chaînes littérales du script + YAML.

Le site emploie correctement les guillemets « » et l'apostrophe typographique,
mais **aucune espace insécable** n'est insérée. Conséquences visibles à
l'écran : ponctuation double (`: ; ? !`) collée ou pouvant passer à la ligne
seule ; texte intérieur des guillemets `« puristes »` séparable du chevron.

Recommandation : une passe de typographie dans `clean()` (ou une fonction
`typo()` appliquée au texte visible), insérant U+202F (espace fine
insécable) devant `; ? !` et `:`, et après `«` / avant `»`. Effet global,
zéro ajout de poids, gain net de qualité perçue.

Exemples (avant → après) :
- `modèles « puristes » proches` → `modèles «‍ puristes‍ » proches`
- `Trier :` → `Trier :` (espace fine insécable avant les deux-points)
- `Filtrer par nom…` (ailleurs `Filtrer par nom…` est correct, pas de double ponctuation)

### D2 — Accroche hero : la baseline juxtapose trois fragments sans liant
**Localisation :** `concepts.yml` → `project.baseline` ; rendu dans
`page()` (`<span class="baseline">`).

Avant : `nue-propriété d'intérêt général · usufruit citoyen · sortie du marché`

« usufruit citoyen » est la formule la plus faible du site : « citoyen » est un
adjectif passe-partout, vaguement militant, en décalage avec le registre
documentaire tenu partout ailleurs (le glossaire et la méthode parlent d'usage
« confié à une personne morale non lucrative »). Le terme n'apparaît nulle part
ailleurs — incohérence de registre.

Après : `nue-propriété d'intérêt général · usufruit non lucratif · sortie du marché`

### D3 — Titre de section accueil : « Trois catégories analysées » est plat
**Localisation :** `render_index()`, section `<h2 class="sec">`.

Avant : `Trois catégories analysées`

« analysées » est faible et redondant avec le reste de la page. Le titre
n'oriente pas le lecteur. Préférer une formulation qui dit ce qu'on y fait.

Après : `Explorer par catégorie`
(ou, plus descriptif : `Lieux, porteurs, usufruitiers`)

### D4 — Message « aucun résultat » : décalage de registre entre les deux pages
**Localisation :** catalogues `render_catalogue()` (`<p class="no-result">`)
vs classement `render_classement()` (pas de message équivalent — voir D11).

Avant (catalogue) : `Aucune entrée ne correspond aux filtres choisis.`

Correct mais sec et tourné « système ». Le reste du site s'adresse au lecteur.
Une formulation légèrement plus orientante, sans devenir bavarde :

Après : `Aucune entrée ne correspond à ces filtres. Élargissez la sélection.`

### D5 — Libellé de tri ambigu : « Par axe C — gouvernance »
**Localisation :** `render_catalogue()`, `<select id="sort">`.

Les trois options d'axe sont libellées de façon inégale :
`Par axe A — intérêt général`, `Par axe B — libération des terres`,
`Par axe C — gouvernance`. La troisième est tronquée par rapport au nom réel
de l'axe (`Gouvernance participative`, cf. `ranking.yml` et toutes les autres
légendes du site).

Après : `Par axe C — gouvernance participative`
(harmonise avec la légende `axe-legend` et le `aria-label` du classement).

### D6 — Intro page « Proposer un lieu » : « corpus volontairement mince »
**Localisation :** `render_suggerer()`, `<p class="lead">`.

Avant : `un annuaire évolutif au corpus volontairement mince et exigeant`

« mince » a une connotation de pauvreté/insuffisance peu valorisante pour un
choix éditorial assumé. « restreint » est déjà employé ailleurs sur le site
(404, accueil : « corpus restreint ») — l'harmonisation lève le décalage.

Après : `un annuaire évolutif au corpus volontairement restreint et exigeant`

---

## MINEURE

### D7 — Hero kicker : « Annuaire critique · France » manque de tenue
**Localisation :** `render_index()`, `<p class="hero-kicker">`.

`France` posé seul après un point médian se lit comme une étiquette brute.
Le `tagline` complet (« …de libération des terres en France ») est déjà la
référence. Suggestion sobre :

Avant : `Annuaire critique · France`
Après : `Annuaire critique · libération des terres`
(le « France » est déjà porté par la baseline juste en dessous ; éviter la
répétition et préciser l'objet plutôt que le territoire).

### D8 — « En tête du classement » : le chapô dit deux fois la même chose
**Localisation :** `render_index()`, section « En tête du classement ».

Avant : `Les montages dont l'Indice de libération est le plus élevé — tous
axes confondus.`

« le plus élevé » et « tous axes confondus » se recoupent (l'Indice est par
définition la moyenne des axes). « tous axes confondus » est de plus
légèrement trompeur — un lecteur peut croire à un tri multi-axes.

Après : `Les montages dont l'Indice de libération est le plus élevé.`

### D9 — Étape 2 de l'accueil : « trois objets » est froid
**Localisation :** `render_index()`, section `howto`, étape 2.

Avant : `Chaque montage se lit à travers trois objets : le lieu, son porteur
de nue-propriété et son usufruitier.`

« objets » est un terme de modélisation, étranger au registre. Le site parle
ailleurs de « catégories » et de « rôles ».

Après : `Chaque montage réunit trois acteurs : le lieu, son porteur de
nue-propriété et son usufruitier.`

### D10 — Toolbar : libellé du champ de recherche / placeholder
**Localisation :** `render_catalogue()`, `<input type="search" id="q">`.

`placeholder="Filtrer par nom…"` et `aria-label="Filtrer par nom"` : correct,
mais « Filtrer » fait doublon avec le bloc « Filtres avancés » juste dessous,
alors que le champ fait surtout une recherche texte. « Rechercher » lèverait
l'ambiguïté fonctionnelle.

Avant : `placeholder="Filtrer par nom…"` / `aria-label="Filtrer par nom"`
Après : `placeholder="Rechercher un nom…"` / `aria-label="Rechercher par nom"`

### D11 — Classement : pas de message quand le filtre par catégorie ne renvoie rien
**Localisation :** `render_classement()` — le filtre `data-f` masque des
lignes mais aucun équivalent du `no-result` du catalogue n'existe.

Cas de portée limitée (chaque catégorie a des entrées), mais si un filtre vide
la table le lecteur voit un tableau sans corps, sans explication. Microcopie
manquante plutôt que fautive — à noter pour cohérence avec D4. Mineur.

### D12 — Note bas de classement : « doublent la lecture chiffrée »
**Localisation :** `render_classement()`, dernier `<p class="note">`.

Avant : `Les mini-barres de couleur doublent la lecture chiffrée.`

« doublent » est juste mais peu clair pour un lecteur pressé (on peut lire
« multiplient par deux »). « appuient » ou « accompagnent » est plus net.

Après : `Les mini-barres de couleur accompagnent la lecture chiffrée.`

### D13 — Footer : phrase descriptive un peu longue et scolaire
**Localisation :** `page()`, premier `<p>` du `<footer>`.

Avant : `annuaire critique des montages de libération des terres en France.
Données factuelles sourcées ; l'Indice de libération est une grille d'analyse
explicite, non un jugement de valeur.`

Correct sur le fond. « Données factuelles sourcées » est un peu télégraphique.
Polissage léger optionnel :

Après : `annuaire critique des montages de libération des terres en France.
Les données sont sourcées ; l'Indice de libération est une grille d'analyse
explicite, non un jugement de valeur.`

### D14 — `aria-label` du tri par entrée vs intitulé visible
**Localisation :** `render_classement()`, en-tête de colonne `Entrée`.

L'`aria-label` dit `Trier par entrée, ordre alphabétique` ; l'intitulé visible
est `Entrée`. La hint `sort-hint` parle de « En-tête de colonne (Entrée, A, B,
C ou IdL) ». Cohérent. Rien à corriger — vérifié, simple confirmation.

### D15 — Callout modèles voisins : « axes posés éditorialement »
**Localisation :** `render_catalogue()` (modeles_note) et `render_methode()`.

`axes posés éditorialement` est un peu jargonneux (« posés » + « éditorialement »
côte à côte). La formule revient deux fois à l'identique — bonne cohérence,
mais l'occasion de la clarifier partout :

Avant : `leur Indice est estimé (axes posés éditorialement)`
Après : `leur Indice est estimé (axes évalués à dire d'expert, hors grille)`
(ou plus simple : `axes estimés, hors grille`).

---

## Synthèse de priorisation

| #  | Sévérité   | Action                                                        |
|----|------------|---------------------------------------------------------------|
| D1 | Importante | Espaces insécables (`: ; ? !`, intérieur des « »)             |
| D2 | Importante | Baseline : « usufruit citoyen » → « usufruit non lucratif »   |
| D3 | Importante | Titre accueil : « Trois catégories analysées » → reformuler   |
| D4 | Importante | Message « aucun résultat » plus orientant                     |
| D5 | Importante | Libellé tri axe C : ajouter « participative »                 |
| D6 | Importante | « corpus mince » → « corpus restreint »                       |
| D7 | Mineure    | Hero kicker : préciser l'objet plutôt que « France »          |
| D8 | Mineure    | Chapô « En tête du classement » : supprimer la redite         |
| D9 | Mineure    | Étape 2 : « trois objets » → « trois acteurs »                |
| D10| Mineure    | Champ de recherche : « Filtrer » → « Rechercher »             |
| D11| Mineure    | Classement : ajouter un message « aucun résultat »            |
| D12| Mineure    | Note classement : « doublent » → « accompagnent »             |
| D13| Mineure    | Footer : alléger « Données factuelles sourcées »              |
| D15| Mineure    | « axes posés éditorialement » → formulation plus claire       |

Aucune faute de langue ni contresens relevés. Le registre documentaire est
tenu ; les corrections ci-dessus ne changent pas le fond, seulement la finition.
