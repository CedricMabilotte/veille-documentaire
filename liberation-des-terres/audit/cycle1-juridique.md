# Audit de rigueur juridique — Cycle 1

*Annuaire « Terres Libérées ». Audit en lecture seule, mai 2026. Juriste relecteur critique.*

Périmètre : `config/concepts.yml`, `config/grilles.yml`, `config/ranking.yml`, les 24 fiches (`porteurs/`, `usufruitiers/`, `lieux/`, `modeles/`), le rapport `recherche/01-concept-montage.md`, et l'échantillon HTML (`site/methode.html`, `site/grilles.html`, `site/p/fonds-la-terre-en-commun.html`). Le HTML est fidèlement généré depuis les YAML : toute correction se fait dans les YAML/config, puis régénération.

---

## 1. Synthèse générale

Le rapport de référence `01-concept-montage.md` est globalement solide et bien sourcé : durée de l'usufruit (art. 619, 30 ans), répartition des charges (art. 605/606/608), fonds de dotation (loi LME 2008, art. 140), intérêt général vs utilité publique, art. 900-1, mécénat (art. 200 et 238 bis CGI). Ce socle est correct.

En revanche, deux problèmes de fond traversent tout le corpus :

1. **Inadéquation entre le concept affiché et les fiches réelles.** Le projet se présente comme un annuaire de montages de « **démembrement nue-propriété / usufruit** ». Or sur 7 lieux et 6 usufruitiers, **un seul cas (Fondation Terre de Liens, donations en démembrement) correspond réellement à un démembrement**. Tous les autres sont de la pleine propriété + bail, ou de la propriété publique + délégation. Le vocabulaire « usufruit / usufruitier » est employé de façon générique pour « titulaire de l'usage », ce qui est juridiquement imprécis et contredit le `ressort_juridique` affiché.

2. **La grille usufruitier mélange deux droits incompatibles.** Le critère `duree_usage` cite l'art. 619 (usufruit, 30 ans) mais sert aussi à noter des baux ruraux (statut du fermage, durée minimale 9 ans, droit au renouvellement quasi automatique) et des baux emphytéotiques (18-99 ans). Ce sont des régimes opposés : le preneur d'un bail rural est *protégé* par un droit au renouvellement d'ordre public, alors que l'usufruitier personne morale subit un terme couperet non renouvelable de plein droit. La grille les traite à l'identique, ce qui fausse la lecture.

Aucune erreur grossière de citation d'article n'a été trouvée. Les imprécisions portent sur la **qualification** des montages et sur la **conception des critères**.

---

## 2. Affirmations juridiques fausses ou imprécises

### 2.1 Vocabulaire « usufruitier » employé à tort (transversal — Critique)
`concepts.yml` définit la catégorie `usufruitier` comme « personne morale … qui reçoit l'**usufruit ou l'usage** ». Le mot « usufruit » est ensuite accolé à des situations qui n'en sont pas :
- `usufruitiers/sctl.yml` : champ `montage.usufruitier: "SCTL"` alors que le texte dit explicitement « la SCTL n'est pas propriétaire : elle est gestionnaire et **preneuse** ». Une société preneuse de baux n'est pas usufruitière. Idem `lieux/larzac.yml`.
- `usufruitiers/gfa-mutuels.yml` : `montage.usufruitier: "Fermier preneur via bail rural"`. Le fermier preneur d'un bail rural n'a pas d'usufruit : il a un droit personnel de jouissance (bail), régi par le statut du fermage. Le confondre avec un usufruit est une erreur de droit.
- `lieux/reseau-terre-de-liens.yml`, `lieux/lurzaindia.yml` : `montage.usufruitier: "Paysan·nes installé·es via bail rural"` / « Agriculteurs installés via baux ». Mêmes remarques : ce sont des preneurs à bail, pas des usufruitiers.
- `usufruitiers/cooperatives-longo-mai.yml`, `usufruitiers/ferme-des-enfants.yml` : l'« usage » repose sur l'autogestion / la qualité d'associé d'une société civile, pas sur un usufruit.

Le champ `montage.usufruitier` devrait être renommé conceptuellement « titulaire de l'usage » et la nature exacte du droit (usufruit / bail rural / bail emphytéotique / convention / qualité d'associé) précisée à chaque fois. Tant que ce n'est pas fait, l'annuaire affirme l'existence d'usufruits qui n'existent pas.

### 2.2 `concept_central.verrou_cle` — généralisation excessive (Importante)
`concepts.yml` affirme : « L'usufruit constitué au profit d'une personne morale ne peut excéder 30 ans … C'est **la fragilité structurelle de tout montage** ». C'est faux pour la majorité du corpus : le plafond de 30 ans (art. 619) ne s'applique **qu'aux montages réellement démembrés**. Les montages en pleine propriété + bail rural (Terre de Liens, Lurzaindia), en propriété publique (Larzac, Conservatoire) ou en superficie/Erbbaurecht ne sont pas concernés par l'art. 619. Le bail rural a même un régime *inverse* (renouvellement de droit). Affirmer que 30 ans est la fragilité de « tout montage » est une erreur.

### 2.3 `methode.html` reprend la même généralisation (Importante)
Conséquence directe de 2.2 : `site/methode.html` ligne 29 affiche « C'est la fragilité structurelle de tout montage ». Se corrige automatiquement en corrigeant `concepts.yml`.

### 2.4 Fonds « La Terre en commun » — déductibilité présentée comme acquise (Importante)
`porteurs/fonds-la-terre-en-commun.yml` (résumé + critère `agrement_ig`) présente la déduction de 66 % comme un fait. Or le rapport de référence rappelle lui-même (point que les fiches n'ont pas répercuté) qu'un fonds de dotation **redistributeur** n'ouvre droit au mécénat que sous conditions, et que la qualité d'intérêt général n'est jamais définitivement acquise. La fiche devrait mentionner le risque de requalification fiscale comme fragilité, ce qu'elle ne fait pas. Le `resume` se couvre par « selon les sources » mais le critère `agrement_ig` (noté `partiel`) ne signale pas le risque.

### 2.5 Fonds de Terre Européenne — « inaliénabilité » sous droit suisse (Mineure)
`porteurs/fonds-terre-europeenne.yml` note `inalienabilite: oui` au motif que la fondation « détient les terres de façon explicitement inaliénable ». L'inaliénabilité invoquée relève du droit suisse et des statuts de la fondation, non d'un mécanisme de droit français vérifiable. La note du critère devrait préciser que l'inaliénabilité est statutaire/suisse et non confirmée par un acte de droit français — cohérence à aligner avec la prudence affichée ailleurs dans la même fiche.

### 2.6 FPH — forme juridique (correct mais à surveiller)
`porteurs/fondation-fph.yml` indique honnêtement que la forme exacte au regard du droit français n'est pas confirmée (cadre de droit suisse). C'est rigoureux. Aucune correction, mais cohérence à maintenir.

---

## 3. Audit des grilles (`grilles.yml`)

### 3.1 Critère `duree_usage` — confond usufruit et bail (Critique)
Grille `usufruitier`, critère `duree_usage` : « L'usufruit ou le bail est de longue durée … (l'usufruit d'une personne morale est plafonné à 30 ans : art. 619) ». Un seul critère ne peut pas évaluer correctement à la fois :
- un **usufruit** de personne morale : plafond 30 ans, **pas** de renouvellement de plein droit (fragilité) ;
- un **bail rural** : durée minimale 9 ans mais **droit au renouvellement** d'ordre public (solidité du preneur) ;
- un **bail emphytéotique** : 18-99 ans, droit réel.

Conséquences concrètes : `sctl.yml` et `gfa-mutuels.yml` cochent `duree_usage: oui` pour des baux ruraux, en s'appuyant sur un critère dont la définition parle d'usufruit 30 ans. La lecture est incohérente. **Recommandation** : scinder en deux critères ou reformuler la définition pour qu'elle traite distinctement (a) le type de droit détenu et (b) sa durée/renouvellement.

### 3.2 Angle mort : qualité de la clause de dévolution côté usufruitier (Importante)
La grille `porteur` a un critère `clause_devolution`. La grille `usufruitier` n'en a **aucun**, alors que la dévolution de l'usufruitier (association loi 1901, SCI, GFA, SCIC) est tout aussi décisive : si l'association usufruitière se dissout et que ses statuts permettent un retour de valeur aux membres, le verrou saute. À ajouter dans la grille `usufruitier`, famille `securite_usage` ou `statut_ig`.

### 3.3 Angle mort : risque de requalification fiscale (Importante)
Le rapport de référence identifie explicitement la requalification fiscale (perte de l'intérêt général) et l'abus de droit / libéralité déguisée comme des risques majeurs. **Aucune grille ne comporte de critère dédié.** Le critère `agrement_ig` (porteur) et `objet_ig` (usufruitier) mesurent l'éligibilité *actuelle*, pas la *robustesse dans le temps* face à une requalification. Recommandation : ajouter un critère « Solidité de la qualification d'intérêt général / absence de risque de requalification » (axe A) dans les grilles `porteur` et `usufruitier`.

### 3.4 Angle mort : durée et renouvellement de l'usufruit comme critère explicite côté porteur (Importante)
Le rapport de référence liste, parmi les 7 facteurs de solidité d'un montage : « (5) la durée et les modalités de renouvellement de l'usufruit ». Côté `usufruitier`, ce point est noyé dans `duree_usage` (voir 3.1). Côté `porteur`, il est **absent** : or pour un nu-propriétaire, savoir si l'usufruit consenti est renouvelé ou s'éteint au terme conditionne la reconcentration de pleine propriété. Recommandation : un critère explicite sur le sort de l'usufruit au terme (renouvellement organisé / extinction / non documenté).

### 3.5 Critère `nature_protectrice` — échelle correcte mais discutable (Mineure)
Grille `porteur`, `nature_protectrice` : « personne publique > fondation RUP > fonds de dotation > société civile ». L'échelle est défendable mais lacunaire : elle omet la **fondation abritée** (pourtant citée dans `concepts.yml` et le rapport) et n'indique pas où se classe une association loi 1901 d'intérêt général agréée (cf. fiche `federation-cen`, notée `partiel`). À compléter pour cohérence.

### 3.6 Critère `inalienabilite` — formulation à préciser (Mineure)
La définition mêle « dotation non consomptible », « domanialité » et « clause statutaire d'inaliénabilité temporaire et justifiée ». C'est correct, mais la mention de l'art. 900-1 (clause conventionnelle d'inaliénabilité : valable seulement si temporaire et justifiée par un intérêt sérieux et légitime, nullité de la perpétuelle) gagnerait à figurer dans la définition, pour éviter que des fiches cochent `oui` sur la foi d'une inaliénabilité « perpétuelle » annoncée — qui serait juridiquement fragile.

### 3.7 Redondance mineure : `non_lucratif_global` / `non_appropriation` / `independance_rendement`
Pas d'erreur de droit, mais ces trois critères (répartis entre grilles) se recouvrent partiellement. Acceptable car rattachés à des objets différents ; signalé pour information.

---

## 4. Audit des fiches : qualifications et évaluations

### 4.1 `montage.type` mal qualifié — Fondation Terre de Liens (Critique)
`porteurs/fondation-terre-de-liens.yml` porte `montage.type: demembrement`. C'est le **seul cas du corpus où le démembrement est réellement établi** (donations de nue-propriété avec réserve d'usufruit, donations temporaires d'usufruit). La qualification est ici correcte — mais la fiche `lieux/reseau-terre-de-liens.yml`, qui agrège le même réseau, porte `montage.type: propriete_sanctuarisee` et son `montage.usufruitier` est « Paysan·nes … via bail rural ». Les deux fiches du même mouvement décrivent donc deux montages différents sans l'expliquer clairement. À harmoniser : la Fondation reçoit des démembrements ; la Foncière/Fondation louent ensuite par bail rural. Ce ne sont pas les mêmes opérations et la fiche réseau devrait le dire.

### 4.2 `montage.type` discutable — Hameau des Buis (Importante)
`lieux/hameau-des-buis.yml` et `usufruitiers/ferme-des-enfants.yml` portent `montage.type: propriete_collective`. Le foncier est détenu par une **société civile dont une SARL (MV Finances) est associée** et dont les **parts restent cessibles**. `concepts.yml` range explicitement dans les `anti_concepts` la « société … à but lucratif et parts librement cessibles ». La présence d'une SARL associée et de parts cessibles place ce montage à la limite du périmètre de l'annuaire. La fiche le signale en fragilité, mais la qualification `propriete_collective` (présentée comme « statuts qui verrouillent la revente et la lucrativité ») est généreuse : rien n'indique que les statuts verrouillent la cession des parts. À requalifier ou à assortir d'une réserve explicite.

### 4.3 `purete_juridique.niveau` incohérent — Ferme des Enfants (Importante)
`usufruitiers/ferme-des-enfants.yml` : `purete_juridique.niveau: pur` (« Droit civil pur »), alors que le commentaire reconnaît lui-même « malgré la présence d'une **SARL** dans la société civile ». Une SARL est une société commerciale ; sa présence dans le montage contredit la qualification « pur » telle que définie dans `ranking.yml` (« droit civil privé + non lucratif, sans … forme sociétaire lucrative »). Le niveau cohérent serait `societaire` (comme la fiche-lieu jumelle `hameau-des-buis.yml`, qui porte justement `societaire`). Les deux fiches du même lieu se contredisent.

### 4.4 `purete_juridique.niveau` discutable — Conservatoires d'espaces naturels (Mineure)
`porteurs/federation-cen.yml` : `niveau: pur`. Les CEN sont des associations loi 1901, donc droit civil — mais ils sont **agréés conjointement par le préfet et la région** (la fiche le souligne). `ranking.yml` définit `encadre` comme « droit civil mais encadrement public fort (agrément …) ». L'agrément CEN est un agrément public. `encadre` serait plus cohérent, ou alors il faut assumer que l'agrément CEN reste léger — mais il faut trancher, car `ofs-brs.yml` est classé `encadre` pour un motif comparable (agrément préfectoral).

### 4.5 Évaluation de grille insoutenable — `clause_devolution` Fonds La Terre en commun (Mineure)
`fonds-la-terre-en-commun.yml`, `clause_devolution: partiel`, note : « Un fonds de dotation ne peut restituer son actif au fondateur ». L'interdiction de retour au fondateur découle de la loi de 2008 ; sur ce point précis le critère mériterait au moins une note plus ferme, ou un `oui` partiel assumé. Inversement, `fonciere-terre-de-liens.yml` coche `clause_devolution: inconnu` : pour une SCA, le sort de l'actif en cas de liquidation suit le droit des sociétés (partage entre actionnaires) sauf clause statutaire contraire — `inconnu` est défendable, mais la note pourrait signaler que, par défaut, une SCA *partage* son boni de liquidation (donc plutôt défavorable que neutre).

### 4.6 Catégorisation — Conservatoires d'espaces naturels en doublon (Mineure)
`concepts.yml` liste « Conservatoires d'espaces naturels (CEN) » dans `modeles_voisins.exemples`, mais le corpus contient `porteurs/federation-cen.yml` (catégorie `porteur`, fiche pleine). Un même objet est à la fois « modèle voisin » et « porteur référencé ». À trancher : soit le retirer de `modeles_voisins`, soit clarifier que la fiche porteur est l'entrée réelle et la mention `modeles_voisins` une coquille.

### 4.7 Cohérence terminologique « propriété sanctuarisée » (Mineure)
`concepts.yml` emploie « (ou la propriété sanctuarisée) » comme quasi-synonyme de nue-propriété dans la définition de la catégorie `porteur`. « Propriété sanctuarisée » n'est pas un terme juridique : c'est une métaphore. Elle est acceptable si elle est définie une fois comme telle, mais elle est utilisée sans guillemets ni définition dans plusieurs fiches. Recommander une définition unique (« pleine propriété détenue par un organisme non lucratif et grevée de clauses limitant la cession ») et un emploi cohérent.

---

## 5. Recommandations classées par priorité

### CRITIQUE

| # | Fichier(s) | Correction précise |
|---|-----------|---------------------|
| C1 | `usufruitiers/sctl.yml`, `usufruitiers/gfa-mutuels.yml`, `lieux/larzac.yml`, `lieux/reseau-terre-de-liens.yml`, `lieux/lurzaindia.yml` | Dans chaque champ `montage.usufruitier`, ne plus écrire « usufruitier » pour des preneurs à bail. Renommer la valeur en « Titulaire de l'usage : … » et préciser la nature exacte du droit (bail rural / bail rural environnemental / délégation de gestion). Le fermier preneur d'un bail rural n'a **pas** d'usufruit. |
| C2 | `config/concepts.yml` (`categorie usufruitier.definition` et, idéalement, le libellé de catégorie) | Préciser que la catégorie regroupe les « titulaires de l'usage » et que l'usufruit *stricto sensu* n'est que l'une des modalités (avec bail rural, bail emphytéotique, convention, qualité d'associé). Lever l'ambiguïté du mot « usufruitier ». |
| C3 | `config/grilles.yml`, grille `usufruitier`, critère `duree_usage` | Scinder ou reformuler : un critère ne peut pas évaluer ensemble un usufruit (30 ans, non renouvelable de droit) et un bail rural (9 ans min., renouvellement d'ordre public). Distinguer (a) nature du droit détenu, (b) durée et modalités de renouvellement. |
| C4 | `portemers/fondation-terre-de-liens.yml` + `lieux/reseau-terre-de-liens.yml` | Harmoniser : la Fondation reçoit de vrais démembrements (correct) ; le réseau, lui, loue par bail rural. Expliciter dans la fiche réseau que « démembrement » ne s'applique qu'aux donations à la Fondation, pas au portage courant Foncière. |

### IMPORTANTE

| # | Fichier(s) | Correction précise |
|---|-----------|---------------------|
| I1 | `config/concepts.yml`, `concept_central.verrou_cle` | Remplacer « C'est la fragilité structurelle de **tout** montage » par une formule exacte : le plafond de 30 ans (art. 619) ne concerne **que les montages réellement démembrés** ; il ne s'applique ni aux baux ruraux, ni à la propriété publique, ni au droit de superficie. (Corrige automatiquement `site/methode.html`.) |
| I2 | `config/grilles.yml`, grilles `porteur` et `usufruitier` | Ajouter un critère axe A « Solidité / pérennité de la qualification d'intérêt général » couvrant le risque de requalification fiscale (cf. risque explicitement identifié par le rapport de référence, absent des grilles). |
| I3 | `config/grilles.yml`, grille `usufruitier` | Ajouter un critère « Clause de dévolution désintéressée » (l'usufruitier — association, SCI, GFA — peut, à sa dissolution, faire fuir la valeur si ses statuts le permettent ; angle mort actuel). |
| I4 | `config/grilles.yml`, grille `porteur` | Ajouter un critère explicite sur le sort de l'usufruit au terme (renouvellement organisé / extinction / non documenté) — facteur (5) du rapport de référence, actuellement non couvert côté porteur. |
| I5 | `porteurs/fonds-la-terre-en-commun.yml` | Ajouter en `fragilites` le risque de requalification fiscale (fonds de dotation : qualité d'intérêt général non acquise ; fonds redistributeur éligible au mécénat sous conditions). Nuancer la note du critère `agrement_ig`. |
| I6 | `lieux/hameau-des-buis.yml`, `usufruitiers/ferme-des-enfants.yml` | Requalifier ou assortir d'une réserve nette : SARL associée + parts cessibles non verrouillées rapprochent ce montage des `anti_concepts`. Ne pas présenter `propriete_collective` comme un verrouillage acquis. |
| I7 | `usufruitiers/ferme-des-enfants.yml` | Corriger `purete_juridique.niveau: pur` → `societaire` (présence d'une SARL ; cohérence avec la fiche-lieu jumelle `hameau-des-buis.yml` qui porte déjà `societaire`). |

### MINEURE

| # | Fichier(s) | Correction précise |
|---|-----------|---------------------|
| M1 | `porteurs/federation-cen.yml` | Réexaminer `purete_juridique.niveau: pur` : l'agrément conjoint préfet/région est un encadrement public ; `encadre` serait plus cohérent avec le traitement d'`ofs-brs.yml`. |
| M2 | `config/concepts.yml` | Trancher le doublon CEN : présents à la fois en `modeles_voisins.exemples` et comme fiche `porteur`. Retirer de l'un des deux. |
| M3 | `config/grilles.yml`, critère `nature_protectrice` | Compléter l'échelle de protection : situer la fondation abritée et l'association loi 1901 d'intérêt général agréée. |
| M4 | `config/grilles.yml`, critère `inalienabilite` | Ajouter dans la définition la règle de l'art. 900-1 (clause d'inaliénabilité valable seulement si temporaire et justifiée ; nullité de la perpétuelle), pour éviter des `oui` fondés sur une inaliénabilité « perpétuelle » fragile. |
| M5 | `porteurs/fonds-terre-europeenne.yml` | Préciser dans la note du critère `inalienabilite` que l'inaliénabilité invoquée est statutaire et de droit suisse, non un mécanisme de droit français vérifiable. |
| M6 | `porteurs/fonciere-terre-de-liens.yml` | Note du critère `clause_devolution` : signaler qu'une SCA partage en principe son boni de liquidation entre actionnaires sauf clause statutaire contraire (orientation plutôt défavorable que neutre). |
| M7 | `config/concepts.yml` + fiches | Définir une fois « propriété sanctuarisée » comme métaphore (non un terme juridique) et l'employer de façon cohérente, entre guillemets. |

---

## 6. Points jugés corrects (aucune action)

- Citations d'articles du Code civil (544, 578 et s., 605, 606, 608, 587, 617, 619, 900-1) : exactes dans `01-concept-montage.md`.
- Fonds de dotation : dotation minimale 15 000 €, création par dépôt en préfecture, dotation consomptible/non consomptible, interdiction de recevoir des fonds publics sauf dérogation : conformes.
- Distinction intérêt général (notion fiscale, 3 conditions cumulatives) / utilité publique (reconnaissance par décret) : correcte et bien expliquée.
- Mécénat : 66 % particuliers (art. 200 CGI), 60 % entreprises (art. 238 bis CGI), absence de réduction d'IFI pour un don à un fonds de dotation : conformes.
- Conservatoire du littoral : domaine propre inaliénable, aliénation par décret en Conseil d'État à la majorité des trois quarts : conforme.
- OFS/BRS : loi ALUR 2014, ordonnance BRS 2016, durée 18-99 ans, rechargement à chaque mutation : conformes ; la fiche note justement que l'OFS porte la *pleine propriété* du sol, pas une nue-propriété.
- Le générateur HTML reproduit fidèlement les YAML : corriger les YAML/config et régénérer suffit.
