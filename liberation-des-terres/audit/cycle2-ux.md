# Audit UX, architecture de l'information et navigation — « Terres Libérées »

**Cycle 2 · Parcours, navigation, compréhension · 2026-05-23**
**Lecture seule — aucun fichier modifié.**

Périmètre : toutes les pages générées dans `site/`, le générateur
`scripts/generate_site.py` (constante `NAV`, fonctions `render_*`, `page`,
`card`, `axis_bar`), la configuration `config/`. L'audit porte sur les parcours
utilisateurs, l'architecture de l'information et la navigation — pas sur
l'exactitude factuelle ni sur la méthode de notation (cycle 1).

Note : le navigateur Claude-in-Chrome n'était pas joignable pendant l'audit ;
l'analyse repose sur la lecture intégrale du HTML généré, du CSS et du
générateur, ce qui suffit à juger structure, parcours et accessibilité de base.

---

## 1. Synthèse

Le site est soigné, cohérent visuellement, sobre et lisible. La hiérarchie
typographique est claire, le code couleur des trois axes (A/B/C) est constant
sur toutes les pages, les fiches détaillées sont riches et bien structurées.

Les faiblesses UX sont concentrées sur trois points : (1) **la pédagogie
d'entrée** — un visiteur novice n'a aucun sas pour comprendre « libération des
terres », « nue-propriété/usufruit » et l'Indice avant d'être plongé dans des
notes chiffrées ; (2) **la navigation transversale** — fil d'Ariane tronqué,
fiches mal reliées entre elles, aucun renvoi porteur↔lieu↔usufruitier complet,
modèles voisins à demi cachés ; (3) **les outils d'exploration** — catalogues
et classement réduits à un filtre par nom, sans tri, sans filtre par
palier/région/montage, sans comparaison de fiches.

Aucun lien mort détecté ; aucune page réellement orpheline (toutes accessibles
via NAV ou cartes), mais `modeles.html` est sous-exposée et `data.json` n'est
mentionné nulle part dans l'interface.

---

## 2. Recommandations — priorité CRITIQUE

### C1. Fil d'Ariane complet sur les fiches
**Fichier / fonction :** `generate_site.py` → `render_fiche`, variable `head`.
Actuellement le « fil d'Ariane » est un seul lien : `<p class="crumb"><a
href="../{CAT_PAGE[cat]}">{catlabel}</a></p>`. Il ne ramène ni à l'accueil ni
ne situe la page courante.
**Modification :** produire un vrai fil : `Accueil › [Catégorie] › [Nom de la
fiche]`, le dernier segment non cliquable. Exemple :
`<p class="crumb"><a href="../index.html">Accueil</a> › <a
href="../{CAT_PAGE[cat]}">{catlabel}</a> › <span>{nom}</span></p>`.

### C2. Sas pédagogique « novice » dès l'accueil
**Fichier / fonction :** `generate_site.py` → `render_index`.
La section « Le principe » est correcte mais dense (paragraphes de définition
juridique bruts tirés de `concepts.yml`). Un porteur de projet ou un donateur
non-juriste décroche.
**Modification :** ajouter au-dessus ou au sein de `render_index` un bloc
« Comment lire cet annuaire » en 3 étapes illustrées (1. Un lieu = un porteur +
un usufruitier ; 2. Chaque entrée est notée sur 3 axes ; 3. L'Indice résume).
Reformuler les définitions de la section « Le principe » en une phrase simple
suivie du détail juridique en repli (`<details>`), plutôt que d'injecter tel
quel le texte de `concepts.yml`.

### C3. Glossaire / page « Comprendre » et infobulles sur les termes-clés
**Fichier :** nouvelle page `glossaire.html` (nouvelle fonction
`render_glossaire`) + entrée dans `NAV`, OU section dédiée dans `methode.html`.
Les termes « nue-propriété », « usufruit », « démembrement », « bail
emphytéotique », « domanialité », « SCIC », « GFA », « fonds de dotation »
apparaissent partout sans définition accessible. La page `methode.html` les
suppose connus.
**Modification :** créer un glossaire (les données peuvent venir d'un nouveau
bloc dans `concepts.yml`). À défaut de tout balisage, au minimum envelopper les
2-3 termes pivots dans un `<abbr title="…">` ou un `<span>` avec `title`,
comme c'est déjà fait pour la pureté juridique (`purete_label` génère un
`title`). Lier le glossaire depuis le footer et depuis `methode.html`.

### C4. Relier réellement les fiches entre elles (porteur ↔ lieu ↔ usufruitier)
**Fichier / fonction :** `render_fiche`, section `liens_html` + données YAML
(`liens:`).
La fiche **Terres du Larzac** ne relie que la SCTL (`liens.porteurs: []`) :
l'État/propriété publique n'est pas une fiche, soit, mais le lieu devrait
pointer vers son porteur quand il existe. Surtout, les liens sont
**unidirectionnels** : si `larzac` cite `sctl`, rien ne garantit que `sctl`
cite `larzac`. Le parcours « explorer un lieu → voir qui le porte → voir les
autres lieux de ce porteur » est donc cassé.
**Modification :** dans `render_fiche`, calculer aussi les **rétro-liens** (les
fiches qui citent la fiche courante) en parcourant `by_uid`, et les fusionner
avec `liens_html` pour garantir la réciprocité. Compléter les `liens:` manquants
dans les YAML (le Larzac doit pointer un porteur si modélisable, Villarceaux
doit relier porteur FPH ↔ lieu ↔ écosite, etc.).

### C5. Expliquer le classement mixte lieux/porteurs/usufruitiers
**Fichier / fonction :** `render_classement`, bloc `body` (le `<p class="lead">`).
La table mélange 21 entrées de 3 natures différentes (un lieu, un porteur et un
usufruitier ne sont pas comparables sur la même échelle). Le `lead` explique
l'Indice mais jamais *pourquoi* ces trois objets cohabitent dans un même
classement, ni comment lire ce mélange. Un juriste comparant « Conservatoire du
littoral » (porteur, 95) et « Terres du Larzac » (lieu, 95) est induit en erreur.
**Modification :** ajouter une phrase explicite dans le `lead` (« lieux,
porteurs et usufruitiers sont notés par la même grille à 3 axes mais ne sont pas
substituables ; le filtre ci-dessous isole chaque type ») ; envisager de
**séparer visuellement** par sous-tableaux ou de faire de « Tout » un état
optionnel et non par défaut.

---

## 3. Recommandations — priorité IMPORTANTE

### I1. Tri des colonnes du classement
**Fichier / fonction :** `render_classement`, `<table class="rank-tbl">` + script.
La table est triée par IdL décroissant, figé. Impossible de trier par axe A, B,
C ou par nom. Un donateur qui privilégie la gouvernance (axe C) ne peut pas
réordonner.
**Modification :** rendre les `<th>` cliquables (tri ascendant/descendant en JS,
sur `data-*` ou contenu cellule), avec indicateur visuel de tri. Le script
actuel ne gère que le filtre par catégorie ; ajouter un trieur générique.

### I2. Tri et filtres dans les catalogues (lieux / porteurs / usufruitiers)
**Fichier / fonction :** `render_catalogue`, bloc `toolbar` + script.
Le seul outil est un `<input type="search">` filtrant `data-nom`. Les cartes
portent déjà `data-idl` (inutilisé) mais pas `data-region`, `data-palier`,
`data-montage`.
**Modification :** dans `card`, ajouter des attributs `data-region`,
`data-palier`, `data-montage`, `data-axeA/B/C`. Dans `render_catalogue`, ajouter
un sélecteur de tri (par indice, par nom, par axe) et des filtres (par palier,
par région pour les lieux, par type de montage). Réutiliser le pattern de
boutons `.fbtn` déjà stylé pour le classement — cohérence assurée.

### I3. Page de comparaison de fiches
**Fichier :** nouvelle fonction `render_comparaison` ou mode comparaison côté
client.
Aucun moyen de mettre deux montages côte à côte. Le cas d'usage « comparer des
montages » (porteur de projet hésitant entre fonds de dotation et fondation,
juriste comparant démembrement vs bail emphytéotique) n'est pas couvert.
**Modification :** soit une page `comparer.html` avec sélection de 2-3 fiches et
affichage en colonnes (en-bref, axes, grille), soit des cases à cocher sur les
cartes du catalogue ouvrant une vue comparative. Au minimum, sur la fiche,
ajouter un lien « comparer avec un montage similaire » vers les fiches de même
catégorie et palier voisin.

### I4. Exposer les « Modèles voisins » et clarifier leur statut
**Fichier / fonction :** `NAV`, `render_index`, `render_modeles` (catalogue).
« Modèles » est noyé en 7e position du NAV, après « Modèles » vient « Méthode ».
L'accueil ne mentionne jamais les modèles voisins ; un visiteur ignore qu'ils
existent. Leur statut « hors classement, indice estimé » n'est expliqué que sur
la page modèles elle-même.
**Modification :** ajouter sur l'accueil une courte section « Modèles voisins de
référence » avec renvoi ; sur la page modèles, ajouter en tête un encart
explicatif (pourquoi ils ne sont pas dans le classement principal, ce que
« estimé » signifie). Envisager de renommer l'entrée NAV « Modèles voisins »
pour lever l'ambiguïté.

### I5. Liens de retour contextuels sur les fiches
**Fichier / fonction :** `render_fiche`, variable `body` (`backlink`).
La fiche se termine par un unique lien « ← Retour au classement », même quand
l'utilisateur vient du catalogue Lieux ou de l'accueil. Le retour ne correspond
pas au parcours réel.
**Modification :** remplacer le lien fixe par un retour vers la page catégorie
(`CAT_PAGE[cat]`, déjà connu) — cohérent avec le fil d'Ariane (C1) — et/ou
ajouter « ← Retour aux {catégorie} ». Le retour au classement peut rester en
second lien.

### I6. Carte « En tête du classement » : libellés d'axes ambigus
**Fichier / fonction :** `axis_bar` (mode `compact`) appelé par `card`.
Sur les cartes, les trois barres portent les labels « Intérêt général »,
« Libération des terres », « Gouvernance participative » sans rappel A/B/C ;
le `title` au survol n'est pas accessible au clavier ni au mobile. Le novice ne
sait pas que la barre = un axe de l'Indice.
**Modification :** ajouter une légende A/B/C compacte une fois par grille de
cartes (réutiliser `.axe-legend`), ou préfixer les labels « A · Intérêt
général ». Lier au moins une fois vers `methode.html` depuis les blocs de cartes
des catalogues (déjà fait sur l'accueil et le classement, absent des catalogues).

### I7. Décimales parasites sur les modèles voisins
**Fichier / fonction :** `score_fiche` (branche `cat == "modele"`) et `axis_bar`.
Sur `modeles.html`, les axes affichent « 90.0 » et la barre `width:90.0%` — les
fiches calculées affichent « 86 ». Incohérence visuelle.
**Modification :** dans `score_fiche` pour les modèles, arrondir les axes
estimés en `int` (`round(...)`) comme pour les fiches calculées, afin que
`axis_bar` reçoive des entiers.

---

## 4. Recommandations — priorité MINEURE

### M1. Accessibilité clavier de la navigation et des contrôles
**Fichier / fonction :** `CSS` (états `:focus`), scripts de `render_classement`
et `render_catalogue`.
Aucun style `:focus` visible n'est défini (le CSS n'a que `:hover`). Les
boutons-filtres `.fbtn` sont de vrais `<button>` (bon), mais le focus n'est pas
mis en évidence. Les `title` des axes ne sont pas atteignables au clavier.
**Modification :** ajouter des règles `a:focus-visible`, `.fbtn:focus-visible`,
`input:focus-visible` avec un contour net. Prévoir un lien d'évitement « Aller
au contenu » en tête de `page()`.

### M2. État « aucun résultat » des filtres
**Fichier / fonction :** scripts de `render_catalogue` et `render_classement`.
Si la recherche ne renvoie rien, la liste devient vide sans message. Le compteur
passe à « 0 » mais aucune phrase n'explique.
**Modification :** afficher un message « Aucune entrée ne correspond » quand le
compteur tombe à 0.

### M3. `data.json` invisible dans l'interface
**Fichier / fonction :** `render_methode` ou `page` (footer).
L'export ouvert `data.json` est généré mais jamais lié.
**Modification :** ajouter un lien « Données ouvertes (JSON) » dans la section
sources de `methode.html` ou dans le footer.

### M4. Métadonnée `<meta name="description">` trop longue
**Fichier / fonction :** `page`, paramètre `description`.
Sur l'accueil et les catalogues, la description fait 400+ caractères (texte
intégral de `concepts.yml`). Tronquée par les moteurs.
**Modification :** tronquer à ~160 caractères, ou prévoir un champ
`meta_description` court dans `concepts.yml`. (Recouvre le cycle 3 SEO.)

### M5. Cartes : meta vide pour les lieux sans localisation
**Fichier / fonction :** `card`, variable `loc`.
« Fermes Terre de Liens » affiche une `<p class="card-meta">` vide (réseau
national sans commune). Le bloc vide crée un trou visuel.
**Modification :** si `loc` est vide, afficher une mention de repli (« Réseau
national », ou le type de montage) ou masquer le `<p>`.

### M6. Cohérence du libellé de catégorie
**Fichier / fonction :** `card` (`catlabel` court) vs `render_fiche`
(`catlabel` long).
Une carte affiche le tag « Porteur » ; la fiche affiche « Porteur de
nue-propriété ». Acceptable, mais le tag du classement et celui des cartes
gagneraient à renvoyer (lien ou `title`) vers la définition de la catégorie.
**Modification :** rendre le tag catégorie cliquable vers la page catalogue
correspondante, ou au moins lui donner un `title` avec la définition courte.

### M7. Ancres des grilles non exploitées
**Fichier / fonction :** `render_grilles` (`id="grille-{cat}"`) et
`render_fiche` (`grille-intro`).
Les sections de `grilles.html` ont des ancres `#grille-porteur` etc., mais le
lien « Comprendre la grille → » des fiches pointe vers `../grilles.html` sans
ancre.
**Modification :** faire pointer le lien vers `../grilles.html#grille-{cat}`
pour amener directement à la bonne grille.

---

## 5. Parcours utilisateurs — verdict par profil

- **Porteur de projet foncier** : trouve les catégories sur l'accueil, mais
  aucun parcours « je veux monter un projet, par où commencer » ni comparaison
  de montages (cf. C2, I3). Parcours moyen.
- **Juriste** : `methode.html` et `grilles.html` sont solides et précises ;
  bonne matière. Mais classement mixte trompeur (C5) et absence de glossaire/
  renvois entre termes (C3). Parcours correct mais perfectible.
- **Donateur** : comprend vite « la terre soustraite au marché », voit le
  classement, mais ne peut pas trier par l'axe qui l'intéresse (I1) ni
  comprendre pourquoi un porteur et un lieu ont la même note (C5). Parcours
  faible sur l'aide à la décision.
- **Visiteur novice** : décroche sur le vocabulaire juridique non explicité
  (C2, C3). Parcours faible.

Parcours « comprendre une note » : la fiche détaillée est **le point fort** du
site — score, axes, grille critère par critère, analyse forces/fragilités,
fiabilité. L'ordre des sections est logique. Il manque surtout le pont entre la
note et la pédagogie (infobulles, glossaire) et la comparaison.

---

## 6. Points positifs à conserver

- Hiérarchie typographique et code couleur A/B/C constants et lisibles.
- Fiche détaillée : structure exemplaire (en-bref → présentation → montage →
  grille → analyse → liens → fiabilité → sources).
- Badge d'Indice + paliers colorés : lecture immédiate.
- Distinction nette entre Indice (noté) et pureté juridique (non notée).
- Aucun lien mort ; NAV cohérente et `active` correctement marqué partout.
- Filtre par catégorie du classement : fonctionnel, réindexe le rang.
