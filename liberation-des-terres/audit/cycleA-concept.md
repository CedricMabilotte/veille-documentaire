# Cycle A — Audit conceptuel : les trois régimes du sol

Audit en lecture seule. Angle : le site doit faire ressortir clairement
l'opposition entre trois régimes juridiques du foncier — (1) le **droit civil
mis au service de l'intérêt général et des communs**, (2) le **droit
commercial** (sociétés, lucrativité, spéculation), (3) la **propriété privée
classique** — et montrer que la « libération des terres » consiste à réemployer
des outils de droit civil non lucratif *contre* la logique marchande.

Pages examinées : `index.html`, `methode.html`, `grilles.html`,
`glossaire.html`, `modeles.html`, `config/concepts.yml`, plus fiches et
`generate_site.py`.

---

## 1. Diagnostic : le site porte-t-il déjà cette opposition ?

**Réponse courte : l'opposition est présente partout, mais à l'état diffus et
implicite. Elle n'est jamais nommée, ni structurée, ni posée comme cadre de
lecture.** Le visiteur qui ne connaît pas déjà la distinction droit civil /
droit commercial ne la reconstruira pas seul.

### Ce qui existe déjà (la matière première est là)

L'opposition affleure dans presque toutes les pages, mais toujours par fragments :

- **`concepts.yml`** est le document le plus explicite. Le `ressort_juridique`
  oppose « la PROPRIÉTÉ (qui reste au collectif non lucratif) » et « l'USAGE ».
  Les `anti_concepts` nomment frontalement le repoussoir : « société (SCI, GFA
  familial) à but lucratif et parts librement cessibles », « optimisation
  fiscale ou patrimoniale », « dispositif spéculatif déguisé ». La catégorie
  `usufruitier` exige une « personne morale de droit civil à but non lucratif
  — et non une société commerciale de droit privé classique ».
- **`grilles.html`** : le premier critère de la grille usufruitier dit
  explicitement « association loi 1901, société civile non lucrative,
  coopérative ou GFA — **et non une société commerciale de droit privé
  classique** ». Le critère « Indépendance vis-à-vis d'une logique de
  rendement » et « Pas d'appropriation possible du foncier » visent le régime
  commercial. C'est, de toutes les pages, celle où l'opposition est la plus
  opérationnelle — mais éclatée en douze lignes de tableau.
- **`methode.html`** : la section « Pureté juridique » pose la question « le
  montage reste-t-il strictement dans le droit civil privé et la
  non-lucrativité, sans bascule vers le droit public ou une forme sociétaire
  lucrative ? ». C'est l'endroit le plus proche du cadre voulu — mais
  l'indicateur est traité comme un détail technique, en quatre lignes, après
  les paliers, et **ne distingue pas les trois régimes** (il met « droit
  public » et « forme sociétaire lucrative » dans le même sac « bascule »).
- **Les fiches** appliquent déjà le raisonnement : Lurzaindia est notée
  `purete_juridique: societaire` avec un commentaire qui pointe la cessibilité
  des actions et la non-lucrativité non garantie. La grille fonctionne ; le
  cadre conceptuel qui la sous-tend n'est nulle part exposé au lecteur.

### Où l'opposition est absente, implicite ou confuse

| Lieu | Problème |
|---|---|
| **Accueil (`hero` + `explain`)** | Oppose « marché spéculatif » à « usage collectif », mais ne nomme jamais l'outil : *droit civil*. Le mot « propriété privée » n'apparaît pas ; le « droit commercial » non plus. Le lecteur voit un *quoi* (sortir du marché) sans le *comment juridique* (réemployer le droit civil). |
| **`explain-grid` (3 cartes : Libérer / Dissocier / Verrou 30 ans)** | Ces trois cartes sont une occasion manquée : elles pourraient déjà *être* les trois régimes, mais décrivent trois aspects du seul régime « communs ». |
| **Méthode — « Pureté juridique »** | Confusion : amalgame « droit public » et « société lucrative » comme deux « bascules » équivalentes, alors que la propriété publique inaliénable est, dans le corpus, le montage le **mieux** noté (Larzac, Conservatoire du littoral, IdL 95). Le lecteur peut croire que sortir du droit civil privé est un défaut — ce que le texte dément ensuite maladroitement. |
| **Glossaire** | Définit « nue-propriété », « usufruit », « intérêt général », « bail rural »… mais **aucune entrée** pour « droit civil », « droit commercial », « société commerciale », « spéculation », « propriété privée ». Les trois régimes ne sont pas nommés. |
| **`modeles.html`** | Le Mietshäuser Syndikat (réseau de GmbH — sociétés !) et Lurzaindia (SCA) montrent un cas passionnant : *du droit commercial neutralisé / mis au service des communs*. Le site ne thématise jamais ce paradoxe, qui est pourtant au cœur de l'angle demandé. |
| **`anti_concepts` (concepts.yml)** | Excellente matière, mais **invisible sur le site** : ce champ n'est lu par aucune fonction de `generate_site.py`. La définition par contraste (« ce que l'annuaire ne référence PAS ») n'atteint jamais le visiteur. |

**Conclusion du diagnostic.** Le site connaît l'opposition, l'applique dans ses
notes, mais ne l'enseigne pas. Il manque une page-pivot qui *nomme* les trois
régimes et pose explicitement la thèse : la libération des terres = réemploi
d'outils de droit civil non lucratif contre la logique marchande.

---

## 2. Recommandations priorisées

### CRITIQUE

#### A1 — Créer une page « Trois régimes du sol »

C'est le cœur du livrable. Une page courte (un écran et demi), pédagogique, qui
nomme et oppose les trois régimes, avec un tableau comparatif. Plan et contenu
détaillés en partie 3.

- **Fichier / fonction** : nouvelle fonction `render_regimes(cfg)` dans
  `generate_site.py`, sur le modèle de `render_grilles` / `render_methode`
  (mêmes helpers `page()`, mêmes classes CSS `section`, `prose`, `sec`,
  `callout`, `rank-tbl`). Sortie : `site/regimes.html`.
- **Câblage** : ajouter `write(SITE / "regimes.html", render_regimes(cfg))`
  dans `main()` (~ligne 2106, près des autres pages transverses) ; ajouter
  `("regimes.html", "0.6")` à `sitemap_paths` (~ligne 2117).
- **Navigation** : insérer `("regimes.html", "Cadre")` ou
  `("regimes.html", "Trois régimes")` dans la liste `NAV` (~ligne 200), à
  placer **juste après `methode.html`** ou juste avant `grilles.html` (cadre →
  grilles → fiches est la progression logique). La nav compte déjà 9 entrées ;
  10 reste acceptable, mais voir A4 si on veut compenser.
- **Source de contenu** : alimenter la page depuis un nouveau bloc
  `regimes:` dans `concepts.yml` (voir A2) plutôt qu'en dur, pour rester
  cohérent avec l'architecture data-driven du projet.

#### A2 — Ajouter un bloc `regimes:` dans `config/concepts.yml`

Pour que la page A1 soit data-driven et non codée en dur. Ce bloc structure les
trois régimes de façon réutilisable.

- **Fichier** : `config/concepts.yml`, nouveau bloc de premier niveau (après
  `montages:` ou après `anti_concepts:`).
- **Contenu proposé** : voir partie 3, encadré YAML.

#### A3 — Reformuler la section « Pureté juridique » de la méthode

Lever la confusion qui assimile « droit public » à une « bascule » négative.

- **Fichier / fonction** : `render_methode()`, `generate_site.py` ~ligne
  1243-1248 (section `<h2>Pureté juridique</h2>`).
- **Action** : remplacer le paragraphe par une formulation qui (a) renvoie à la
  nouvelle page « Trois régimes », (b) précise que l'indicateur situe le
  montage sur l'axe droit civil non lucratif ↔ forme commerciale lucrative, et
  (c) rappelle que la propriété publique inaliénable n'est pas un défaut mais
  un *quatrième* point d'ancrage hors marché. La donnée source est
  `ranking.yml > purete_juridique` : vérifier si les `niveaux` y distinguent
  bien droit public et forme sociétaire ; si oui, l'exploiter, sinon affiner la
  formulation côté méthode sans toucher au scoring.

### IMPORTANTE

#### A4 — Reformuler l'accueil pour nommer le réemploi du droit civil

Aujourd'hui l'accueil dit *quoi* mais pas *avec quel outil*. Une ou deux
phrases suffisent.

- **Fichier / fonction** : `render_index()`, `generate_site.py`.
- **Actions ciblées, sans alourdir** :
  1. **`hero-lead`** (~ligne 1401) : ajouter une demi-phrase nommant le moyen.
     Ex. : après « explique leurs montages juridiques », insérer une incise du
     type « — des outils de droit civil détournés de l'usage marchand — ».
  2. **`explain-grid`** (~ligne 1438-1453) : transformer la 3ᵉ carte ou en
     ajouter une 4ᵉ. Option sobre : remplacer la carte « Le verrou des 30 ans »
     (très technique pour un accueil) par une carte **« Trois régimes du
     sol »** qui résume l'opposition en 2 phrases et pointe vers
     `regimes.html`. Le verrou des 30 ans reste expliqué en méthode et dans
     `concepts.yml`.
  3. Ajouter `regimes.html` comme 3ᵉ CTA discret, ou comme lien dans le
     paragraphe `lead` de clôture de la section `explain` (~ligne 1455), aux
     côtés de glossaire et méthode.

#### A5 — Exposer les `anti_concepts` sur le site

La définition par contraste (« ce que l'annuaire ne référence PAS ») est
rédigée mais morte dans le YAML. Elle est l'illustration la plus directe de
l'opposition aux régimes commercial et privé.

- **Fichier / fonction** : idéalement intégrée à la page « Trois régimes »
  (A1), en bloc de clôture « Aux frontières du modèle » ; sinon dans
  `render_methode()` en sous-section. Lire `cfg["concepts"]["anti_concepts"]`
  (liste de chaînes) et la rendre en `<ul>`.

#### A6 — Ajouter au glossaire les termes des trois régimes

- **Fichier** : constante `GLOSSAIRE` dans `generate_site.py` (~ligne 1279).
- **Entrées à ajouter** : « Droit civil », « Droit commercial / société
  commerciale », « Spéculation foncière », « Propriété privée », et
  éventuellement « Communs ». Définitions courtes, neutres, registre
  documentaire (cohérent avec l'`editorial.voice` de `concepts.yml`).
  Le `DefinedTermSet` JSON-LD se met à jour automatiquement.

### MINEURE

#### A7 — Lier la page « Trois régimes » depuis les grilles et les fiches

- **`render_grilles()`** : dans le `<p class="lead">` d'introduction, ajouter
  un lien « Le cadre des trois régimes → ».
- **`render_fiche()`** : la ligne « Pureté juridique » du bloc `enbref`
  (~ligne 661-663) pourrait pointer vers `regimes.html` plutôt que rester un
  simple `title`. Optionnel, à faire seulement si cela n'alourdit pas la fiche.

#### A8 — Harmoniser le vocabulaire « marché » / « spéculatif »

Le site alterne « marché spéculatif », « logique marchande », « logique de
marché », « logique de rendement ». Une fois la page « Trois régimes » en
place, ces termes gagneront à renvoyer implicitement au même régime nommé
(« droit commercial »). Pas d'urgence ; simple cohérence éditoriale à surveiller.

---

## 3. Plan et contenu de la page « Trois régimes du sol »

Objectif : **une page courte, sobre, pédagogique** — pas un essai long. Elle
nomme le cadre, le rend visible, puis renvoie vers méthode et grilles pour le
détail. Réutilise les composants CSS existants ; aucun nouveau style nécessaire.

### Plan de la page (`render_regimes`)

```
H1  Trois régimes du sol

§   Chapeau (lead) — 2-3 phrases
    « En droit français, une même parcelle peut relever de logiques
    opposées. La libération des terres ne crée pas un droit nouveau :
    elle réemploie des outils de droit civil — démembrement, baux longs,
    statuts non lucratifs — pour soustraire le foncier à la logique
    marchande. Cette page nomme les trois régimes que l'annuaire oppose. »

H2  Les trois régimes              ← 3 blocs courts (réutiliser .explain-grid
                                      ou .axe-cards), un par régime :

    1. Droit civil au service de l'intérêt général et des communs
       Outils : démembrement (art. 544, 578 C. civ.), fondation, fonds de
       dotation, bail rural/emphytéotique, association, SCIC.
       Finalité : usage collectif, sortie durable du marché. → Régime de
       référence de l'annuaire.

    2. Droit commercial : sociétés, lucrativité, spéculation
       Outils : société commerciale, parts/actions librement cessibles,
       recherche de plus-value et de dividende.
       Finalité : valorisation du capital. → Régime repoussoir — mais
       parfois neutralisé (cf. Lurzaindia, Mietshäuser Syndikat).

    3. Propriété privée classique
       Outil : pleine propriété individuelle (art. 544 C. civ.).
       Finalité : maîtrise et transmission patrimoniale privées. → Ni
       libération, ni spéculation : le point de départ ordinaire.

H2  Tableau comparatif             ← voir ci-dessous

H2  Aux frontières du modèle       ← rend les anti_concepts (A5) :
    ce que l'annuaire ne référence pas, et pourquoi.

§   Renvois : « La grille de notation traduit ce cadre en critères →
    grilles » · « Le calcul de l'Indice → méthode ».
```

### Tableau comparatif (réutilise `table.rank-tbl`)

| Critère | Droit civil / intérêt général | Droit commercial | Propriété privée classique |
|---|---|---|---|
| **Outil juridique type** | Démembrement, fondation, fonds de dotation, bail long, association, SCIC | Société commerciale, parts/actions cessibles | Pleine propriété individuelle (art. 544 C. civ.) |
| **But poursuivi** | Usage collectif d'intérêt général | Profit, valorisation du capital | Jouissance et transmission privées |
| **Lucrativité** | Non lucratif, gestion désintéressée | Lucratif par construction | Indifférente (usage privé) |
| **Cessibilité du foncier** | Verrouillée (inaliénabilité, dévolution) | Libre — parts cessibles, revente | Libre |
| **Rapport au marché** | Soustrait durablement | Soumis, voire spéculatif | Soumis (mais sans visée spéculative) |
| **Gouvernance** | Collective, ouverte, « une voix par personne » | Proportionnelle au capital | Individuelle |
| **Place dans l'annuaire** | Régime de référence (noté) | Repoussoir — sauf si neutralisé | Point de départ, non référencé |

> Note de rédaction : garder les cellules très courtes (3-6 mots). Le tableau
> doit tenir sans scroll horizontal sur desktop ; envelopper dans
> `.table-scroll` pour le mobile, comme les grilles.

### Encadré de clôture — le paradoxe à thématiser

Un `callout` (classe `.callout-note` existante) signalant que certains montages
réels (Lurzaindia en SCA, Mietshäuser Syndikat en réseau de GmbH) **partent du
droit commercial mais en neutralisent la lucrativité par leurs statuts** : la
frontière entre régimes 1 et 2 n'est pas la forme juridique seule, mais l'usage
qu'on en fait. C'est précisément la thèse que le commanditaire veut voir
ressortir.

### Bloc YAML proposé pour `concepts.yml` (recommandation A2)

```yaml
# ───────────────────────────────────────────────────────────────────────────
# Les trois régimes du sol — cadre conceptuel
# ───────────────────────────────────────────────────────────────────────────
regimes:
  chapeau: >
    En droit français, une même parcelle peut relever de logiques opposées.
    La libération des terres ne crée pas un droit nouveau : elle réemploie des
    outils de droit civil — démembrement, baux longs, statuts non lucratifs —
    pour soustraire le foncier à la logique marchande.
  liste:
    - id: civil_commun
      label: "Droit civil au service de l'intérêt général et des communs"
      outils: "Démembrement (art. 544, 578 C. civ.), fondation, fonds de
        dotation, bail rural ou emphytéotique, association, SCIC."
      but: "Placer le foncier au service d'un usage collectif d'intérêt
        général et l'y maintenir durablement."
      role: "Régime de référence de l'annuaire."
    - id: commercial
      label: "Droit commercial : sociétés, lucrativité, spéculation"
      outils: "Société commerciale, parts ou actions librement cessibles,
        recherche de plus-value et de dividende."
      but: "Valoriser un capital ; le foncier y est un actif."
      role: "Régime repoussoir — parfois neutralisé par les statuts."
    - id: propriete_privee
      label: "Propriété privée classique"
      outils: "Pleine propriété individuelle (art. 544 du Code civil)."
      but: "Maîtrise et transmission patrimoniale privées."
      role: "Point de départ ordinaire ; non référencé par l'annuaire."
  paradoxe: >
    Certains montages réels partent du droit commercial — Lurzaindia en
    société en commandite par actions, le Mietshäuser Syndikat en réseau de
    sociétés — mais en neutralisent la lucrativité par leurs statuts. La
    frontière entre les régimes ne tient pas à la seule forme juridique, mais
    à l'usage qu'on en fait.
```

La page `render_regimes()` lit alors `cfg["concepts"]["regimes"]` pour le
chapeau, les trois blocs et l'encadré paradoxe, et `cfg["concepts"]["anti_concepts"]`
pour la section « Aux frontières du modèle ». Le tableau comparatif peut rester
en dur dans la fonction (structure stable) ou être ajouté au YAML si l'on veut
le rendre entièrement éditable.

---

## 4. Garde-fous — rester sobre

- **Une seule page nouvelle.** Ne pas disperser le cadre sur plusieurs pages.
- **Page courte** : viser ~250-350 mots de prose + un tableau. Pas un essai
  académique. Le détail technique reste en méthode et grilles.
- **Réemployer le CSS existant** (`section`, `prose`, `sec`, `explain-grid` /
  `axe-cards`, `rank-tbl`, `table-scroll`, `callout`). Aucun nouveau style.
- **Nav** : 10 entrées est le plafond raisonnable ; si cela paraît trop, fusionner
  visuellement n'est pas nécessaire — « Cadre » est un libellé court.
- **Ton** : registre documentaire et juridique, neutre, conforme à
  `editorial.voice`. Nommer le « repoussoir » sans le diaboliser : le site
  reste un annuaire critique, pas un pamphlet.

---

## Résumé des recommandations

| Priorité | Réf. | Action | Localisation |
|---|---|---|---|
| Critique | A1 | Créer la page « Trois régimes du sol » | `render_regimes()` (nouvelle) + `main()` + `NAV` |
| Critique | A2 | Bloc `regimes:` data-driven | `config/concepts.yml` |
| Critique | A3 | Reformuler « Pureté juridique » | `render_methode()` ~l.1243 |
| Importante | A4 | Accueil : nommer le réemploi du droit civil | `render_index()` hero + explain-grid |
| Importante | A5 | Exposer les `anti_concepts` | page A1 / `render_methode()` |
| Importante | A6 | Glossaire : droit civil, droit commercial, spéculation, propriété privée | constante `GLOSSAIRE` |
| Mineure | A7 | Liens vers « Trois régimes » depuis grilles et fiches | `render_grilles()`, `render_fiche()` |
| Mineure | A8 | Harmoniser le vocabulaire « marché / spéculatif » | éditorial transverse |
