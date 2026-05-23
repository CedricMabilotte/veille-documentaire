# Audit d'exactitude des données — Cycle 1

> Fact-checking en lecture seule des 24 fiches de l'annuaire « Terres Libérées »,
> confronté aux rapports de recherche `recherche/02-lieux-organismes.md` et
> `recherche/03-modeles-puristes.md`, avec vérifications web ciblées.
> Date : 23 mai 2026. Aucun fichier n'a été modifié.

## Méthode

Chaque fait présenté comme certain dans une fiche a été recherché dans les rapports
de référence. Les rapports distinguent explicitement « FAIT VÉRIFIÉ » et
« NON CONFIRMÉ » ; une fiche ne doit pas durcir un point non confirmé. Quelques
vérifications web ont confirmé ou infirmé des points douteux (Terre de Liens, SCTL,
Hameau des Buis, Lurzaindia, Coopérative Oasis).

Bilan : **2 erreurs factuelles** (dates), **1 fait vérifiable durci à tort** dans le
mauvais sens (Hameau des Buis), **1 fait majeur manquant** (bail emphytéotique du
Larzac), **2 incohérences de chiffres**, plusieurs `grille:` à requalifier et des
liens croisés lacunaires. Aucun lieu ni organisme inventé : la base est saine.

---

## CRITIQUE — à corriger avant publication

### C1. `usufruitiers/sctl.yml` et `lieux/larzac.yml` — date de création de la SCTL erronée

Les deux fiches indiquent `annee: 1982`, « créée à partir de décembre 1982 ».
La SCTL a été **formellement constituée le 29 avril 1985** ; décembre 1982 n'est que
le début de la recherche d'une structure de gestion. Le rapport `02-lieux-organismes.md`
(lignes 69 et 234) est lui-même imprécis sur ce point — l'erreur vient de la source.
- **Correction** : `annee: 1985` dans les deux fiches. Dans `resume`, `montage.description`
  et `fiabilite`, écrire « société civile constituée le 29 avril 1985, après une
  recherche de structure engagée dès décembre 1982 ».
- La fiche `larzac.yml` parle aussi de « gestion en continu depuis 1982 » dans la note
  du critère `perennite_gouvernance` : remplacer par 1985.

### C2. `lieux/larzac.yml` et `usufruitiers/sctl.yml` — fait majeur manquant : le bail emphytéotique de 99 ans

Les deux fiches décrivent la SCTL comme « gestionnaire et preneuse » du foncier de
l'État, sans préciser **le titre juridique** : la SCTL a signé avec l'État un **bail
emphytéotique, d'abord de 60 ans puis porté à 99 ans (maximum légal)**, sécurisant les
6 300 ha **jusqu'en 2083**. C'est précisément ce bail qui fonde l'irréversibilité.
- **Conséquence sur la grille `larzac.yml`** : le critère `irreversibilite` est noté
  `oui` avec pour seule justification « la propriété publique de l'État ». La vraie
  garantie pour les paysans est le bail emphytéotique de 99 ans, pas la seule
  domanialité (un bail peut prendre fin). La `valeur: oui` est défendable, mais la
  `note` est inexacte tant qu'elle ne mentionne pas le bail emphytéotique 99 ans / 2083.
- **Correction** : ajouter dans `montage.description` (les deux fiches) la mention du
  bail emphytéotique de 99 ans conclu avec l'État (échéance 2083) ; réécrire la `note`
  du critère `irreversibilite` de `larzac.yml` en s'appuyant sur ce bail.

### C3. `lieux/hameau-des-buis.yml` et `usufruitiers/ferme-des-enfants.yml` — l'évolution coopérative présentée comme « non confirmée » alors qu'elle est avérée

Les deux fiches qualifient le passage à une SAS coopérative à gouvernance partagée de
« non entièrement confirmé » et laissent `annee: null`. Vérification : la SC « Le Hameau
des Buis » a été constituée **en 2003** ; le Hameau **est aujourd'hui** organisé en
**SAS coopérative à gouvernance partagée**. Le rapport `02` (ligne 136) datait de la
prudence, mais le fait est désormais vérifiable.
- **Correction `hameau-des-buis.yml`** : `annee: 2003`. Reformuler `resume`, `montage`
  et `fiabilite` pour présenter la SAS coop comme la situation actuelle (et non comme
  une hypothèse), la SC de 2003 comme le montage d'origine.
- **Correction `ferme-des-enfants.yml`** : idem dans `resume`, `montage.description`,
  `analyse.leviers` et `fiabilite`.
- **Grilles concernées** : les notes des critères `montage_documente`, `perennite_gouvernance`
  (hameau) et `ouverture_entrants` (ferme-des-enfants) reposent sur l'incertitude
  « évolution non confirmée » : à réécrire une fois le fait acté.
- Note de prudence : si la situation juridique exacte de 2026 ne peut être tranchée à
  la date de publication, conserver `partiel` mais formuler « le Hameau a évolué vers
  une SAS coopérative » sans le mot « non confirmé ».

### C4. `porteurs/fondation-terre-de-liens.yml` — année manquante (la Fondation date de 2013)

La fiche a `annee: null`. La Fondation Terre de Liens a été **créée en mai 2013**
(succédant à un fonds de dotation), distincte du mouvement/association de 2003 et de
la Foncière de 2006. Le `null` prive la fiche d'un fait pourtant vérifiable et présent
en filigrane dans le rapport `02` (« issue d'un fonds de dotation, puis reconnue
fondation »).
- **Correction** : `annee: 2013` ; préciser dans `resume` et `fiabilite` « créée en
  mai 2013, en succession d'un fonds de dotation ».

### C5. `lieux/lurzaindia.yml` — fiche sans aucun lien croisé et catégorisation à clarifier

Le bloc `liens:` de `lurzaindia.yml` a `porteurs: []`, `usufruitiers: []`, `lieux: []`.
Or Lurzaindia est, dans la fiche elle-même, à la fois le lieu **et** son porteur (la
SCA détient les terres) ; les agriculteurs preneurs sont les usufruitiers de fait.
La fiche est donc orpheline alors que toutes les autres fiches « lieu » pointent vers
au moins un porteur. Deux options :
- **Option recommandée** : créer une fiche `porteurs/lurzaindia-fonciere.yml` (la SCA)
  et faire pointer `lieux/lurzaindia.yml` → `porteurs: [lurzaindia-fonciere]`, de la
  même façon que `reseau-terre-de-liens` pointe vers la Foncière.
- **Option minimale** : si l'on conserve une fiche unique, l'indiquer explicitement
  dans `montage.description` (« la foncière est elle-même le lieu référencé ») pour
  justifier l'absence de lien, et ne pas laisser le lecteur croire à un oubli.

---

## IMPORTANTE — à corriger pour la rigueur

### I1. Incohérence du chiffre de hausse du nombre de paysans au Larzac (25 % vs 20 %)

`larzac.yml` (critère `ancrage_territorial`) et `sctl.yml` (`public_non_restreint`,
`ouverture_entrants`, `fiabilite`) affirment une hausse « d'environ 25 % ». Le rapport
`02` écrit « environ +25 % selon les sources » (ligne 71), mais la vérification web
donne **+20 %** (chiffre attribué à José Bové / présentation du Larzac comme
« laboratoire foncier »). Le « 25 % » n'est pas étayé.
- **Correction** : harmoniser sur « environ 20 % » dans les deux fiches, ou écrire
  « hausse du nombre de paysans » sans pourcentage si la source exacte n'est pas sûre.
  Aligner aussi le rapport `02` (hors périmètre lecture seule, mais à signaler).

### I2. `usufruitiers/cooperative-oasis.yml` et `lieux/...` — « début 2018 » à préciser

La fiche dit « cofondée par Colibris début 2018 ». La SCIC Coopérative Oasis a été
**immatriculée en mai 2018** (premier conseil d'administration en janvier 2018).
« Début 2018 » n'est pas faux mais imprécis ; le rapport `02` (ligne 263) dit lui-même
« début 2018 ».
- **Correction (mineure-importante)** : écrire « SCIC créée en mai 2018, premier conseil
  d'administration en janvier 2018 ». Sans cela, garder « 2018 » simple plutôt que
  « début 2018 ».

### I3. `lieux/reseau-terre-de-liens.yml` — lien `usufruitiers: [gfa-mutuels]` conceptuellement faux

La fiche réseau Terre de Liens liste `gfa-mutuels` comme usufruitier. Or, dans le
montage Terre de Liens décrit par la fiche elle-même, l'usufruitier réel des fermes
est **le ou la paysan·ne preneur·euse via bail rural**, pas le GFA. Les GFA mutuels
sont un outil distinct, accompagné par Terre de Liens (rapport `02` §3.2), mais ils ne
sont pas les usufruitiers des ~240 fermes du réseau.
- **Correction** : retirer `gfa-mutuels` du bloc `usufruitiers:` de `reseau-terre-de-liens.yml`,
  ou requalifier le lien (les GFA sont une famille d'outils « apparentés », pas
  l'usufruitier du réseau). Symétriquement, revoir `gfa-mutuels.yml` → `lieux: [reseau-terre-de-liens]`.

### I4. Emploi du mot « usufruitier » pour des structures qui ne détiennent pas d'usufruit

`config/concepts.yml` rappelle le verrou juridique : l'usufruit d'une personne morale
ne peut excéder 30 ans (art. 619 C. civ.). Or plusieurs fiches classées en catégorie
`usufruitier` ne détiennent juridiquement **pas un usufruit** :
- `sctl` : preneuse d'un **bail emphytéotique** (droit réel, mais pas un usufruit) ;
- `cooperative-oasis` : **financeur**, la fiche le reconnaît elle-même (« rôle de
  financeur plus que d'usufruitier direct ») ;
- `cooperatives-longo-mai`, `ferme-des-enfants` : usage / décision, sans usufruit
  formalisé documenté.

Ce n'est pas une erreur de donnée à proprement parler, mais une **imprécision de
vocabulaire transversale**. La catégorie est définie largement dans `concepts.yml`
(« reçoit l'usufruit ou l'usage »), donc c'est acceptable — mais chaque fiche devrait,
dans `montage.description`, nommer le titre réel (bail emphytéotique, convention,
autogestion, financement) plutôt que de laisser planer le mot « usufruit ».
- **Correction** : revue rédactionnelle légère des `montage.description` des 4 fiches
  citées pour nommer le titre juridique exact.

### I5. `lieux/larzac.yml` — `forme_juridique: null` discutable

Toutes les fiches « lieu » ont `forme_juridique: null`, ce qui est cohérent (un lieu
n'a pas de forme juridique). Pas une erreur. Mais `lurzaindia.yml` est un cas limite :
la fiche « lieu » décrit en réalité une **société (SCA)**. Voir C5 — soit scinder, soit
documenter. Pas de correction de champ `forme_juridique` requise si C5 est traité.

---

## MINEURE — améliorations de cohérence

### M1. `villarceaux.yml` — surface « ~370 ha » de la ferme à tracer

La fiche dit « ferme d'environ 370 hectares ». Le rapport `02` (ligne 44) écrit « la
ferme exploitée représente ~370 ha » : **fait tracé, conforme**. RAS — simple
confirmation. Le « ~600 ha » du domaine est également conforme au rapport. Bon point.

### M2. `nddl.yml` — bien calibré sur le « non confirmé »

La fiche NDDL distingue correctement les faits 2019 vérifiés (~700 000 €) des
acquisitions 2023-2024 « non confirmées », exactement comme le demande le rapport `02`
(lignes 117-119). `grille.irreversibilite: partiel` avec note sur la dotation
consomptible : **honnête et bien justifié**. Aucune correction. À citer comme modèle
de calibrage pour les autres fiches.

### M3. `fondation-fph.yml` — forme juridique : bonne prudence

Le champ `forme_juridique` indique explicitement « de droit suisse selon les sources ;
forme exacte au regard du droit français non confirmée ». C'est **exactement** le
niveau de prudence demandé par le rapport `02` (lignes 188-190, 297). Aucune
correction. Modèle à suivre.

### M4. Cohérence des `grille:` — `oui` à surveiller

Revue des `valeur: oui` potentiellement trop généreux :
- `larzac.yml` / `irreversibilite: oui` — défendable **à condition** de citer le bail
  emphytéotique 99 ans (cf. C2) ; en l'état la note est insuffisante.
- `fondation-terre-de-liens.yml` / `clause_devolution: oui`, `ca_collegial: oui` — la
  note invoque « le statut de FRUP impose… ». C'est une déduction du statut, pas un
  fait observé sur la Fondation Terre de Liens elle-même. Acceptable car le statut FRUP
  emporte effectivement ces obligations en droit ; mais formuler « le statut de FRUP
  impose » plutôt que d'affirmer l'observation directe — ce qui est déjà le cas. RAS.
- `conservatoire-littoral.yml` / `agrement_ig: oui` avec note « créé par la loi du
  10 juillet 1975 » : un établissement public créé par la loi n'a pas d'« agrément »
  au sens d'un agrément administratif ; la `valeur: oui` se justifie par la mission
  d'intérêt général, mais le mot « agrément » dans l'intitulé du critère colle mal.
  Reformuler la note (« investi par la loi d'une mission d'intérêt général ») — c'est
  déjà à peu près le cas, simple polissage.
- `ferme-des-enfants.yml` / `purete_juridique.niveau: pur` : discutable. La fiche
  reconnaît la présence d'une SARL dans la SC porteuse et le statut de simple créancier
  des habitants. `pur` semble optimiste pour un montage où une SARL est associée ;
  `encadre` serait plus cohérent avec la fiche `hameau-des-buis.yml` qui, pour le même
  lieu, retient `niveau: societaire`. **Incohérence inter-fiches à trancher** : le même
  montage est noté `pur` (usufruitier) et `societaire` (lieu). Harmoniser — `encadre`
  est le compromis raisonnable.

### M5. Liens croisés — réciprocité globalement bonne, deux lacunes

Vérification de tous les blocs `liens:` :
- Réciprocité correcte : villarceaux↔fph↔ecosite, longo-mai↔fonds-terre-europeenne↔
  cooperatives-longo-mai, nddl↔fonds-la-terre-en-commun, larzac↔sctl,
  hameau-des-buis↔ferme-des-enfants, reseau-terre-de-liens↔fondation/foncière↔gfa.
- **Lacune 1** : `lurzaindia.yml` n'a aucun lien (cf. C5).
- **Lacune 2** : `conservatoire-littoral.yml` → `usufruitiers: [federation-cen]` et
  `federation-cen.yml` → `porteurs: [conservatoire-littoral]`. Ce lien est **réciproque
  mais conceptuellement infondé** : les CEN ne sont pas les usufruitiers des terrains
  du Conservatoire du littoral. Ce sont deux porteurs/gestionnaires distincts. Le
  rapport `02` ne décrit aucune relation usufruitier/porteur entre eux.
  **Correction** : supprimer ce lien croisé des deux fiches, ou le requalifier en
  simple « voir aussi » s'il existe un champ approprié.

### M6. Sources — présentes et plausibles partout

Les 24 fiches ont toutes un bloc `sources:` avec 2 entrées, titres et URL cohérents
avec le rapport `02` ou `03`. Aucune source inventée détectée. Remarque mineure :
`reseau-terre-de-liens.yml` et plusieurs fiches Terre de Liens citent
`terredeliens.org` — le rapport `02` (ligne 154) note que ce site « n'est pas
récupérable via fetch » ; la source reste valide comme référence, simplement
non vérifiée en direct. Pas de correction, mais à garder en tête.

### M7. `modeles/*.yml` — `axes_estimes` honnêtement étiquetés

Les 4 modèles portent un bloc `axes_estimes` (A/B/C chiffrés) et le champ `fiabilite`
précise bien « conversion indicative du tableau comparatif du rapport de recherche ».
La conversion +++/++/+ → 90/70/50 est cohérente avec le tableau du rapport `03`.
`mietshauser-syndikat` : A=70 correspond bien à « ++ » du tableau (ligne 135). RAS.
Le rapport `03` signale lui-même que les pourcentages (1 M m² Stiftung trias, 191
projets MHS, 18 % littoral) sont à revérifier — les fiches `stiftung-trias.yml` et
`clt-bruxelles.yml` reprennent cette prudence dans `fiabilite`. Bon calibrage.

---

## Synthèse des priorités

| # | Fichier(s) | Nature | Priorité |
|---|---|---|---|
| C1 | `sctl.yml`, `larzac.yml` | Date SCTL : 1985, pas 1982 | Critique |
| C2 | `larzac.yml`, `sctl.yml` | Bail emphytéotique 99 ans manquant | Critique |
| C3 | `hameau-des-buis.yml`, `ferme-des-enfants.yml` | SAS coop = situation actuelle, année 2003 | Critique |
| C4 | `fondation-terre-de-liens.yml` | `annee: 2013` à renseigner | Critique |
| C5 | `lurzaindia.yml` | Fiche sans liens croisés | Critique |
| I1 | `larzac.yml`, `sctl.yml` | Hausse paysans : 20 %, pas 25 % | Importante |
| I2 | `cooperative-oasis.yml` | « début 2018 » → mai 2018 | Importante |
| I3 | `reseau-terre-de-liens.yml`, `gfa-mutuels.yml` | Lien GFA usufruitier erroné | Importante |
| I4 | `sctl`, `cooperative-oasis`, `cooperatives-longo-mai`, `ferme-des-enfants` | Vocabulaire « usufruit » imprécis | Importante |
| M4 | `ferme-des-enfants.yml` vs `hameau-des-buis.yml` | `purete_juridique` incohérente (pur vs societaire) | Mineure |
| M5 | `conservatoire-littoral.yml`, `federation-cen.yml` | Lien croisé infondé | Mineure |

Aucune fiche ne contient de fait inventé ni de contradiction grave avec les rapports.
Les défauts dominants sont : deux dates fausses héritées de sources imprécises, un
fait juridique central omis (bail emphytéotique du Larzac), une prudence devenue
excessive (Hameau des Buis) et quelques liens croisés mal posés.
