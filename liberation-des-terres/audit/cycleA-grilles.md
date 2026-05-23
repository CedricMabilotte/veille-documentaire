# Audit de fond — Grilles & ranking sous l'angle droit civil / commercial / propriété privée

**Cycle A · Fond conceptuel et juridique · 2026-05-23**
**Lecture seule — aucun fichier de production modifié.**

Périmètre : `config/grilles.yml`, `config/ranking.yml`,
`scripts/generate_site.py` (fonction `score_fiche`), fiches YAML.
Angle : les grilles et l'Indice capturent-ils correctement le degré auquel un
montage relève du **droit civil non lucratif d'intérêt général** plutôt que du
**droit commercial** ou de la **propriété privée appropriable** ?

---

## 1. Synthèse

L'architecture conceptuelle est bonne : trois axes lisibles, une « pureté
juridique » sortie de l'Indice à juste titre. Mais l'opposition centrale du
projet — *droit civil non lucratif vs droit commercial / propriété privée* —
est **mal instrumentée sur un point précis et structurant : la cessibilité des
parts**. Cet angle mort fait que des montages sociétaires dont la valeur
foncière reste captable individuellement (Foncière TdL, Lurzaindia, GFA)
obtiennent un axe A et B comparables à des montages non lucratifs purs, alors
que c'est exactement la ligne de partage que le site prétend éclairer.

Trois autres réglages méritent correction : le critère `non_lucrativite_effective`
absent de la grille `porteur`, l'axe A qui mélange « forme » et « lucrativité »
sans pouvoir les distinguer, et la définition de la « pureté juridique » dont le
niveau `societaire` est ambigu.

| # | Constat | Priorité |
|---|---------|----------|
| 1 | Aucun critère ne capture la **cessibilité des parts / appropriabilité de la valeur** | **Critique** |
| 2 | `non_lucrativite_effective` absent de la grille `porteur` | **Critique** |
| 3 | « Pureté juridique » : niveau `societaire` mal défini, échelle non ordonnée | Importante |
| 4 | Axe A : « forme non lucrative » et « lucrativité effective » non distingués | Importante |
| 5 | Pondérations axe B : `independance_rendement` sous-pesé | Importante |
| 6 | Paliers : la zone sociétaire (IdL 50-70) est tassée, peu discriminante | Mineure |

---

## 2. Constats détaillés et réglages proposés

### Constat 1 — Aucun critère ne capture la cessibilité des parts — **CRITIQUE**

**Fichier : `config/grilles.yml`**

C'est le défaut de fond. L'opposition droit civil non lucratif / propriété
privée se joue d'abord sur **une question** : *la valeur du foncier peut-elle
être captée à titre individuel, notamment par revente de parts sociales ?*

Or cette question n'a **aucun critère dédié**. Elle apparaît seulement dans les
*notes* éditoriales des fiches :
- `fonciere-terre-de-liens.yml` : « les actions restent cessibles »
- `lurzaindia-sca.yml` : « les actions restent cessibles »
- `gfa-mutuels.yml` (critère `non_appropriation`, valeur `partiel`) : « les parts
  du GFA restent cessibles, ce qui ouvre une appropriation possible de la valeur »

Côté `porteur`, le critère le plus proche, `non_appropriation`, **n'existe que
dans la grille `usufruitier`** — la grille `porteur` ne le contient pas. Un
porteur sociétaire à parts librement cessibles et revalorisées (cas exact de la
Foncière TdL) n'est donc évalué nulle part sur ce point structurant. Résultat :
son axe B est seulement pénalisé par `inalienabilite` (poids 3, mis à `partiel`)
et `nature_protectrice` (poids 2, `partiel`) — soit la même décote qu'un
montage non lucratif imparfait, alors que la nature du risque est radicalement
différente.

**Réglage proposé — ajouter un critère identique dans les trois grilles, axe B :**

Dans `grilles.yml`, famille `verrou_foncier` (porteur), `securite_usage`
(usufruitier) et `sortie_marche` (lieu), ajouter :

```yaml
- id: parts_non_cessibles
  label: "Parts / titres non cessibles ou cession encadrée"
  axe: B
  poids: 3
  definition: >
    Les parts, actions ou titres de la structure ne sont pas librement
    cessibles sur un marché : soit la structure n'a pas de capital social
    appropriable (fondation, association), soit ses statuts encadrent
    strictement la cession (agrément, prix plafonné à la valeur nominale,
    inaliénabilité). « oui » : aucune part appropriable, ou cession verrouillée
    au nominal ; « partiel » : cession soumise à agrément mais à un prix non
    plafonné ; « non » : parts librement cessibles, valeur foncière captable.
```

Effet attendu : Fondation TdL, Conservatoire du littoral, associations →
`oui` (pas de capital appropriable) ; SCTL, GFA mutuels → `partiel` ;
Foncière TdL, Lurzaindia → `non`. L'axe B des trois foncières sociétaires
baisserait nettement (de l'ordre de 10-15 points), ce qui est l'effet *voulu* :
le site doit montrer que ces montages, utiles, ne « libèrent » pas le foncier au
même degré qu'une fondation.

> Ne PAS créer un quatrième axe ni un sous-indice : un seul critère, poids 3,
> dans l'axe B existant suffit. La cessibilité *est* une question de sortie du
> marché.

---

### Constat 2 — `non_lucrativite_effective` absent de la grille `porteur` — **CRITIQUE**

**Fichier : `config/grilles.yml`**

La grille `usufruitier` contient `non_lucrativite_effective` (axe A, poids 2 :
« absence de partage de bénéfices ; les excédents sont réinvestis »). La grille
`porteur` **ne l'a pas**. Elle a `forme_non_lucrative` (la *forme*) et
`gestion_desinteressee` (la *gestion des dirigeants*) — mais pas le critère
central : *les excédents/plus-values sont-ils distribués aux apporteurs de
capital ?*

C'est précisément le point qui distingue la Foncière TdL (revalorisation des
parts → captation, fût-elle limitée à l'inflation) d'une fondation (aucune
distribution possible). Aujourd'hui la grille `porteur` ne peut pas l'exprimer :
la note de `gestion_desinteressee` pour la Foncière dit « une revalorisation des
parts est prévue ; la gestion n'est pas strictement désintéressée » — le critère
est détourné de son objet (il vise les *dirigeants*, pas le *capital*).

**Réglage proposé — ajouter à la grille `porteur`, famille `statut_ig`, axe A :**

```yaml
- id: non_lucrativite_effective
  label: "Non-lucrativité effective (capital non rémunéré)"
  axe: A
  poids: 2
  definition: >
    Le capital apporté n'est pas rémunéré : ni dividende, ni intérêt, ni
    plus-value distribuée aux apporteurs. « partiel » si une revalorisation
    des parts existe, même plafonnée à l'inflation ; « non » si dividende ou
    plus-value sont possibles.
```

Cela rend `gestion_desinteressee` à son sens propre (rémunération des
dirigeants) et donne à l'axe A un vrai critère de lucrativité. Sur la Foncière
TdL : `non_lucrativite_effective` = `partiel`, `gestion_desinteressee` peut
repasser à `oui` ou `partiel` selon les dirigeants — gain de précision sans
double pénalité injuste.

---

### Constat 3 — « Pureté juridique » : niveau `societaire` mal défini — **IMPORTANTE**

**Fichier : `config/ranking.yml`, bloc `purete_juridique`**

Le placement *hors Indice, en indicateur complémentaire* est **le bon choix** :
la pureté juridique mêle des dimensions qualitatives (droit public vs privé) qui
ne s'ordonnent pas linéairement et qu'on ne veut pas faire entrer dans un score.
À conserver.

Mais les quatre niveaux ont deux défauts :

1. **Le niveau `societaire` confond deux choses.** Sa définition — « forme de
   société pouvant comporter une part de lucrativité » — range ensemble une SCA
   à actionnariat solidaire sans dividende (Foncière TdL) et, potentiellement,
   une société purement lucrative. Or une société civile **non lucrative** n'est
   pas « impure » : elle est du droit civil pur. Le problème n'est pas la forme
   société, c'est la **lucrativité** et la **cessibilité**.

2. **L'échelle n'est pas ordonnée et le lecteur croit qu'elle l'est.** `pur` >
   `encadre` > `public` > `societaire` : présentés dans cet ordre, ils suggèrent
   un classement du meilleur au pire. Mais `public` (domanialité) est *plus*
   protecteur que `pur`, pas moins — la grille `nature_protectrice` le dit
   elle-même (« personne publique > fondation RUP »). L'ordre actuel est
   trompeur.

**Réglage proposé — reformuler les niveaux et expliciter la non-hiérarchie :**

```yaml
purete_juridique:
  label: "Nature juridique du montage"
  question: >
    De quel régime relève le montage ? L'indicateur situe — il ne classe pas :
    chaque régime a ses forces.
  note_lecture: >
    Cet indicateur n'est PAS une échelle de qualité. La protection effective
    est mesurée par l'axe B de l'Indice. Ici on situe seulement le régime.
  niveaux:
    - id: civil_non_lucratif
      label: "Droit civil non lucratif"
      sens: "Fondation, association, société civile sans lucrativité ni parts cessibles."
    - id: civil_encadre
      label: "Droit civil sous encadrement public"
      sens: "Droit civil mais agrément, plafonds ou contrôle étatique fort."
    - id: societaire_solidaire
      label: "Forme sociétaire solidaire"
      sens: "Société (SCA, coopérative) à vocation solidaire ; parts cessibles, lucrativité possible."
    - id: droit_public
      label: "Droit public"
      sens: "Le foncier relève de la domanialité ou d'un établissement public."
```

`societaire` → `societaire_solidaire` (assume la part de cessibilité au lieu de
la masquer) ; `pur` → `civil_non_lucratif` (nomme ce qui compte) ;
`note_lecture` coupe court à la lecture en classement. Mettre à jour le champ
`purete_juridique.niveau` des fiches en conséquence (renommage 1:1).

---

### Constat 4 — Axe A : « forme » et « lucrativité » non distingués — **IMPORTANTE**

**Fichier : `config/grilles.yml`, grille `porteur`, famille `statut_ig`**

Une fois le constat 2 corrigé, la famille `statut_ig` du porteur compte 6
critères axe A (forme_non_lucrative 3, agrement_ig 3, objet_foncier_protecteur 2,
gestion_desinteressee 2, risque_requalification 1, + non_lucrativite_effective
2). C'est cohérent. Mais `forme_non_lucrative` (poids 3) reste le critère le plus
lourd alors qu'il évalue seulement *l'enveloppe juridique*. Une SCA solidaire y
est mise à `partiel` — décote de 1,5 point sur 3 — alors même que dans les faits
elle peut être plus désintéressée qu'une association captée par un cercle
restreint.

**Réglage proposé — rééquilibrer les poids axe A du porteur :**

| Critère | Poids actuel | Poids proposé |
|---|---|---|
| `forme_non_lucrative` | 3 | **2** |
| `non_lucrativite_effective` *(nouveau)* | — | **3** |
| `agrement_ig` | 3 | 3 |
| `objet_foncier_protecteur` | 2 | 2 |
| `gestion_desinteressee` | 2 | 2 |
| `risque_requalification` | 1 | 1 |

Logique : la lucrativité *effective* (ce que devient l'argent) doit peser plus
lourd que la *forme* (l'étiquette). Total axe A porteur : 13 (vs 11
aujourd'hui) — homogène avec usufruitier (10) à un point près, acceptable.

> Aligner aussi la grille `usufruitier` : y faire passer `non_lucrativite_effective`
> de poids 2 à 3, pour la même raison et pour cohérence inter-grilles.

---

### Constat 5 — Axe B : `independance_rendement` sous-pesé — **IMPORTANTE**

**Fichier : `config/grilles.yml`, grille `porteur`, famille `verrou_foncier`**

`independance_rendement` (axe B, poids 2) — « le capital n'est pas soumis à des
investisseurs attendant une plus-value ou un dividende » — est le critère qui
distingue le plus nettement un porteur de droit civil d'un véhicule
d'investissement. Il pèse aujourd'hui autant que `clause_devolution` et
`nature_protectrice`. Combiné au nouveau `parts_non_cessibles` (poids 3
proposé), l'axe B aura alors les bons leviers ; mais `independance_rendement`
mérite poids **3**, à parité avec `inalienabilite`.

**Réglage proposé — famille `verrou_foncier` (porteur), poids axe B :**

| Critère | Poids actuel | Poids proposé |
|---|---|---|
| `inalienabilite` | 3 | 3 |
| `parts_non_cessibles` *(nouveau)* | — | 3 |
| `independance_rendement` | 2 | **3** |
| `nature_protectrice` | 2 | 2 |
| `clause_devolution` | 2 | 2 |

Total axe B porteur passe de 9 à 13. La sortie effective du marché est ainsi
portée par les trois bons critères (inaliénabilité du bien, non-cessibilité des
parts, indépendance vis-à-vis du rendement) — exactement les trois portes par
lesquelles la valeur foncière peut fuir vers le privé.

---

### Constat 6 — Paliers : zone sociétaire peu discriminante — **MINEURE**

**Fichier : `config/ranking.yml`, bloc `paliers`**

Après application des constats 1-5, les montages sociétaires (Foncière TdL,
Lurzaindia, GFA) verront leur IdL baisser de 8-15 points et se concentreront
autour de 45-58. Les seuils actuels `partiel` (50) / `eloigne` (0) laisseraient
alors une zone large et peu lue. Ce n'est pas urgent — à revoir **après**
recalcul, pas avant. Réglage indicatif seulement :

```yaml
# après recalcul, vérifier la dispersion réelle ; piste :
paliers:
  - { id: abouti,  min: 85 }   # au lieu de 88
  - { id: solide,  min: 72 }   # au lieu de 76
  - { id: engage,  min: 58 }   # au lieu de 64
  - { id: partiel, min: 42 }   # au lieu de 50
  - { id: eloigne, min: 0  }
```

Ne pas appliquer à l'aveugle : régénérer le site après les constats 1-5, lire la
nouvelle distribution de `data.json`, puis caler les seuils sur les quintiles
observés.

---

## 3. Ce qui est déjà sain — à ne pas toucher

- **Pureté juridique hors Indice** : choix correct, conservé. Seule sa
  définition est revue (constat 3).
- **Mapping `oui/partiel/non/inconnu`** : simple et lisible.
- **Pondération égale des axes A/B/C** : défendable et transparente ; ne pas la
  modifier dans ce cycle.
- **Pénalité de complétude** : correctement spécifiée (déjà couverte cycle 1).
- **`inconnu` exclu du dénominateur d'axe** : déjà traité au cycle 1, hors
  périmètre ici.

---

## 4. Récapitulatif des réglages, par priorité

| Pr. | Fichier | Réglage | Valeur |
|---|---|---|---|
| **Critique** | `grilles.yml` | Ajouter `parts_non_cessibles` dans les 3 grilles, axe B | poids **3** |
| **Critique** | `grilles.yml` | Ajouter `non_lucrativite_effective` à la grille `porteur`, axe A | poids **3** |
| Importante | `ranking.yml` | Reformuler les 4 niveaux de `purete_juridique` + `note_lecture` | renommage 1:1 |
| Importante | `grilles.yml` | `forme_non_lucrative` (porteur) | poids 3 → **2** |
| Importante | `grilles.yml` | `non_lucrativite_effective` (usufruitier) | poids 2 → **3** |
| Importante | `grilles.yml` | `independance_rendement` (porteur) | poids 2 → **3** |
| Mineure | `ranking.yml` | Recalibrer les paliers **après** régénération | 85/72/58/42/0 (indicatif) |

Toutes les fiches sociétaires devront recevoir une valeur pour les deux nouveaux
critères ; renommage du champ `purete_juridique.niveau`. Aucun changement de
logique dans `score_fiche` n'est nécessaire — les deux critères s'intègrent au
calcul existant.
