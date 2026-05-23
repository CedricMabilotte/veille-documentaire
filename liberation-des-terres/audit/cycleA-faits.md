# Cycle A — Audit factuel : exactitude et fraîcheur des 28 fiches

> Audit en lecture seule. Date : 2026-05-23.
> Angle : exactitude factuelle et fraîcheur des données. Confrontation des
> 28 fiches YAML aux rapports `recherche/02-lieux-organismes.md` et
> `recherche/03-modeles-puristes.md`, complétée par des recherches web
> ciblées (données 2025-2026).
>
> Ce rapport ne modifie aucun fichier. Il liste, fiche par fiche, les
> corrections recommandées avec leur priorité et la correction exacte.

## Méthode

- Lecture intégrale des 28 fiches : 6 lieux, 10 porteurs, 8 usufruitiers,
  4 modèles.
- Confrontation systématique aux deux rapports de recherche.
- 10 recherches web ciblées (mai 2026) : Terre de Liens, SCTL/Larzac,
  Lurzaindia, Coopérative Oasis, FEVE, Conservatoire du littoral, NDDL,
  FPH/Villarceaux, Hameau des Buis, CLT Bruxelles, Antidote.
- Aucun site bloqué contourné. Faits reformulés, pas de copie de source.

## Synthèse des priorités

| Priorité | Nombre | Nature |
|---|---|---|
| **Critique** | 4 | Faits faux ou périmés qui changent le sens de la fiche |
| **Importante** | 9 | Chiffres périmés, datations manquantes, libellés erronés |
| **Mineure** | 6 | Précisions souhaitables, formulations à nuancer |

Le problème le plus grave concerne **le Hameau des Buis** : deux fiches
(`hameau-des-buis.yml`, `ferme-des-enfants.yml`) décrivent un montage qui
n'existe plus depuis 2021.

---

# CRITIQUE — à corriger en priorité

## C1 — `lieux/hameau-des-buis.yml` : montage périmé, fait central faux

**Problème.** La fiche affirme comme situation actuelle que l'association
La Ferme des Enfants « exerce le pouvoir de décision final » et constitue
l'usufruitier du lieu. C'est **faux depuis 2021**. La recherche web établit
que :
- l'association La Ferme des Enfants a reçu un **avis d'expulsion le 12 mars
  2021** ; un jugement lui a été défavorable ;
- un **protocole d'accord sur son départ** du Hameau des Buis a été signé en
  **octobre 2021** ;
- la SAS coopérative Hameau des Buis a été constituée le **28 janvier 2023**,
  précisément pour remplacer la société civile **après** ce départ.

La fiche présente donc un montage conflictuel et révolu comme l'organisation
en vigueur. Le lien croisé `usufruitiers: [ferme-des-enfants]` est devenu
incohérent.

**Correction exacte.**
- Réécrire le `resume`, le bloc `montage` et la `synthese` pour décrire la
  situation réelle : foncier porté aujourd'hui par la **SAS coopérative
  Hameau des Buis** (créée le 28 janvier 2023), gérant un domaine d'environ
  **6 hectares** ; les habitant·es sont membres de la coopérative.
- Mentionner explicitement que La Ferme des Enfants, association
  cofondatrice, **a quitté le lieu en 2021** à l'issue d'un conflit, et que
  la SAS coopérative a été créée pour lui succéder.
- Retirer `ferme-des-enfants` de `liens.usufruitiers` ou le requalifier en
  lien historique.
- `montage.usufruitier` : remplacer « Association La Ferme des Enfants
  (décision finale) » par les membres de la SAS coopérative.
- Le `fiabilite` actuel affirme « pouvoir de décision final de l'association »
  comme fait vérifié : à corriger, c'est faux.

## C2 — `usufruitiers/ferme-des-enfants.yml` : fiche entièrement périmée

**Problème.** Toute la fiche repose sur le rôle de l'association comme
usufruitier du Hameau des Buis exerçant « le pouvoir de décision final ».
Or l'association **a été expulsée du lieu en 2021**. La fiche n'a plus
d'objet en tant qu'usufruitier du Hameau des Buis.

L'évaluation de grille `articulation_porteur: oui` (« l'association est
elle-même associée à la société civile portant le foncier et y détient la
décision finale ») est **insoutenable** : le lien a été rompu judiciairement.

**Correction exacte.** Deux options :
1. **Retrait** de la fiche (statut `archive`), l'association n'étant plus un
   usufruitier d'un lieu référencé.
2. **Requalification** : si l'on conserve la fiche, indiquer clairement que
   l'association portait *historiquement* le projet, qu'elle a quitté le
   Hameau des Buis en 2021, et que l'usufruit est désormais exercé par la
   SAS coopérative. Dans ce cas, `articulation_porteur` doit passer à `non`
   et le lien `lieux: [hameau-des-buis]` être retiré ou requalifié.

Recommandation : option 1 (archive) — la fiche dans son état actuel induit
le lecteur en erreur.

## C3 — `porteurs/feve.yml` : chiffres d'activité fortement périmés

**Problème.** La fiche annonce « environ 37 fermes financées et une
trentaine de paysan·nes installé·es, près de 2 400 hectares ». Données
fin 2025 (sources FEVE, presse spécialisée) :
- **53 fermes financées** (et non ~37) ;
- **78 agriculteur·rices installé·es** (et non une trentaine) ;
- environ **3 300 hectares** accompagnés en transition (et non ~2 400) ;
- **60 M€ collectés** depuis la création (la fiche ne donne pas ce total).

L'écart est important : la fiche sous-estime l'activité de FEVE de moitié.

**Correction exacte.** Dans `resume` et `fiabilite`, remplacer par :
« environ 53 fermes financées, près de 78 agriculteur·rices installé·es,
environ 3 300 hectares accompagnés en transition agroécologique, plus de
60 M€ collectés depuis 2021 ». Conserver la mention « les chiffres
d'activité évoluent rapidement », exacte.

## C4 — `usufruitiers/cooperative-oasis.yml` : « ~80 écolieux » présenté comme acquis

**Problème.** La fiche affirme à plusieurs reprises, comme fait établi, que
la Coopérative Oasis « finance et accompagne environ 80 écolieux ». La
recherche web montre que **80 est un objectif fin 2025** : la coopérative
prévoyait de passer de **57 à 80 oasis financées** d'ici fin 2025. Le chiffre
« 80 » ne décrit donc pas une réalité passée mais une cible.

L'évaluation `public_non_restreint: oui` (« accompagne environ 80 écolieux »)
s'appuie sur un chiffre non établi.

**Correction exacte.** Remplacer « environ 80 écolieux » par une formulation
exacte : « environ 57 écolieux financés (objectif de 80 fin 2025) », ou
vérifier le chiffre réalisé le plus récent. Idem dans `resume`, `grille`
(`public_non_restreint`), `analyse.forces` et `fiabilite`.

---

# IMPORTANTE — à corriger

## I1 — `lieux/villarceaux.yml` et `usufruitiers/ecosite-villarceaux.yml` : exploitant mal nommé

**Problème.** Les deux fiches désignent l'exploitation agricole comme
« **EARL Olivier Ranke** ». La recherche web indique que l'exploitation est
l'**EARL du Chemin Neuf**. Olivier Ranke est l'agriculteur, mais la
dénomination sociale « EARL Olivier Ranke » n'est pas attestée — elle
paraît inventée à partir du nom de l'exploitant.

**Correction exacte.** Remplacer « EARL Olivier Ranke » par « EARL du
Chemin Neuf » dans `montage.usufruitier`, `montage.description`, le bloc
`grille` et le `fiabilite` des deux fiches. Si l'on veut conserver le nom
de l'agriculteur, écrire « EARL du Chemin Neuf (exploitant Olivier Ranke) ».

## I2 — `lieux/villarceaux.yml` : nom de la coopérative et nombre de structures

**Problème.** La fiche parle de la coopérative « **Coop'Saveur** » et de
« plusieurs personnes morales ». Les sources nomment la coopérative
**« Saveurs du Vexin »** (Coopérative Saveurs du Vexin) et indiquent que le
domaine accueille **six structures juridiques distinctes**.

**Correction exacte.** Remplacer « Coop'Saveur » par « Saveurs du Vexin »
(dans `villarceaux.yml` et `ecosite-villarceaux.yml`). Remplacer
« plusieurs structures » par « six structures juridiques » si le chiffre
est conservé comme vérifié.

## I3 — `lieux/lurzaindia.yml` et `porteurs/lurzaindia-sca.yml` : chiffres périmés

**Problème.** Les deux fiches donnent : ~480 ha, 35 agriculteurs / « une
trentaine », ~3 674 actionnaires, ~1,57 M€. Données actualisées (sources
Lurzaindia / Arrapitz, 2025) :
- **486 hectares** (et non ~480) ;
- **41 agriculteur·rices** installé·es (et non 35 ni « une trentaine ») ;
- **3 775 actionnaires** solidaires (et non 3 674) ;
- **1 670 445 €** investis, soit ~1,67 M€ (et non ~1,57 M€).

**Correction exacte.** Mettre à jour les quatre chiffres dans `resume`,
`montage`, `grille` (`origine_non_speculative` cite « 3 674 actionnaires »)
et `fiabilite` des deux fiches. La mention « ces chiffres évoluent au fil
des campagnes » est exacte et à conserver.

## I4 — `lieux/larzac.yml` et `usufruitiers/sctl.yml` : datation de la prolongation du bail manquante

**Problème.** Les deux fiches indiquent un bail emphytéotique « d'abord de
60 ans puis porté à 99 ans (échéance 2083) », ce qui est exact, mais sans
dater la prolongation. La recherche confirme : bail signé le **29 avril
1985 pour 60 ans** (échéance initiale 2045), **renégocié en 2013** pour le
porter à 99 ans (échéance 2083). L'absence de date peut laisser croire que
les 99 ans étaient acquis dès 1985.

**Correction exacte.** Préciser dans `montage.description` et `fiabilite` :
« bail emphytéotique signé en 1985 pour 60 ans, prolongé en 2013 à 99 ans
(échéance 2083) ».

## I5 — `lieux/reseau-terre-de-liens.yml` : risque de confusion entre deux jeux de chiffres

**Problème.** La fiche reprend les chiffres « plus de 338 agriculteur·rices,
environ 240 fermes, près de 7 000 hectares, 78 fermes acquises en 2024,
~20 M€/an ». La recherche web 2025-2026 confirme que **« 338 agriculteurs /
240 fermes / 7 000 ha »** est le bilan de la **collaboration avec les Safer**
(chiffre stable, cité encore au Salon de l'agriculture 2025). Mais Terre de
Liens communique par ailleurs un périmètre « mouvement » bien plus large
(de l'ordre de plusieurs milliers de fermes accompagnées et plusieurs
dizaines de milliers de citoyens engagés). La fiche présente le périmètre
« Safer » sans dire que c'en est un sous-ensemble, ce qui peut laisser
croire que c'est le total du mouvement.

**Correction exacte.** Préciser dans `resume` et `fiabilite` que les
chiffres « 338 / 240 / 7 000 ha » concernent **la collaboration Terre de
Liens–Safer** (et non l'ensemble du mouvement). Vérifier et, si possible,
ajouter le chiffre à jour des fermes portées par la Foncière + la Fondation
à partir du rapport annuel 2024-2025 de la Fondation (publié en janvier
2026 — la fiche cite encore le rapport 2023-2024).

## I6 — `lieux/reseau-terre-de-liens.yml` : source datée

**Problème.** La fiche cite le « Rapport annuel de la Fondation 2023-2024 ».
Le **rapport 2024-2025 a été publié le 14 janvier 2026** et est désormais
la source de référence.

**Correction exacte.** Mettre à jour la `source` :
`titre: "Terre de Liens — Rapport annuel de la Fondation 2024-2025"`,
`url: "https://terredeliens.org/national/actu/rapport-annuel-de-la-fondation-2024-2025-14-01-2026/"`.
Vérifier au passage si les chiffres du rapport 2024-2025 modifient les
mentions de la fiche.

## I7 — `porteurs/fondation-terre-de-liens.yml` : `annee` et incohérence interne

**Problème.** Le champ `annee: 2013` correspond à la création de la
fondation reconnue d'utilité publique, ce qui est cohérent avec le `resume`
(« créée en mai 2013 »). Mais la fiche-lieu `reseau-terre-de-liens.yml`
porte `annee: 2003` (fondation du mouvement) et la fiche
`fonciere-terre-de-liens.yml` porte `annee: 2006`. Ces dates différentes
sont correctes individuellement, mais le site doit veiller à ne pas les
présenter comme contradictoires. Point de cohérence éditoriale, pas une
erreur factuelle.

**Correction exacte.** Aucune correction de donnée ; s'assurer que
l'affichage distingue bien « mouvement (2003) », « Foncière (2006) » et
« Fondation (2013) ». À traiter plutôt en cycle B (éditorial).

## I8 — `porteurs/fondation-fph.yml` : champ `annee` vide

**Problème.** `annee: null`. La FPH **existe depuis 1982** (fondation de
droit suisse, siège à Lausanne) — fait vérifiable.

**Correction exacte.** Renseigner `annee: 1982` et l'ajouter au `fiabilite`
comme fait vérifié. Préciser éventuellement le siège (Lausanne) dans le
`resume`.

## I9 — `porteurs/fonciere-antidote.yml` : changement de nom de l'organisme

**Problème.** L'organisme a **abandonné le nom « La Foncière Antidote »**
pour s'appeler désormais simplement **« Antidote »**. La fiche conserve
l'ancien nom partout (`nom`, `resume`, `synthese`).

**Correction exacte.** Mettre à jour le `nom` en « Antidote » (ou
« Antidote — fonds de dotation »), en signalant dans le `resume` l'ancienne
appellation « La Foncière Antidote » pour la continuité. Conserver l'`uid`
`fonciere-antidote` pour ne pas casser les liens et URLs.

---

# MINEURE — précisions souhaitables

## M1 — `porteurs/conservatoire-littoral.yml` : cinquantenaire 2025

Le Conservatoire a fêté ses **50 ans en 2025** (créé le 10 juillet 1975) et
protège désormais ~**220 000 ha** sur **plus de 840 sites**. Le chiffre
« 18 % du littoral » de la fiche reste exact en 2025. Suggestion : ajouter
au `resume` l'ordre de grandeur « environ 220 000 hectares, plus de
840 sites » pour la fraîcheur. Le « ~13 % des sites gérés par des
associations (2015) » est ancien : le signaler comme datant de 2015 (déjà
fait) ou chercher un chiffre plus récent.

## M2 — `usufruitiers/cooperatives-longo-mai.yml` : « statut associatif privilégié »

La formule `forme_juridique: "Coopératives autogérées (statut associatif
privilégié selon les sources)"` est floue et reprend une formulation de
source non vérifiée. La recherche web n'a pas confirmé de statut juridique
précis. Suggestion : reformuler en « statut juridique précis non confirmé
par les sources ; fonctionnement coopératif autogéré » et ne pas affirmer
« associatif » si ce n'est pas établi. La fiche `personne_morale_civile:
oui` (« relèvent d'un statut associatif privilégié ») s'appuie sur ce point
non vérifié — la passer à `partiel` serait plus prudent.

## M3 — `lieux/longo-mai.yml` : siège et nombre de coopératives

La fiche indique « cinq implantations en France » : cohérent avec le
rapport de recherche. Rappel : Longo Maï est un réseau **transnational**
(implantations aussi en Suisse, Autriche, Allemagne, Ukraine). Le `resume`
pourrait préciser « cinq implantations *en France*, au sein d'un réseau
européen » pour éviter de laisser croire que le réseau se limite à la
France. Mineur.

## M4 — `modeles/clt-bruxelles.yml` : gouvernance tripartite présentée comme « idéale variable »

La fiche qualifie la répartition des sièges en trois tiers de « structure
idéale » qui « peut varier en pratique ». La recherche confirme que la
répartition en trois tiers égaux (habitants / voisinage / pouvoirs publics)
est la **règle effective du conseil d'administration de l'ASBL CLTB**, pas
seulement un idéal. La prudence du rapport de recherche est ici excessive.
Suggestion : reformuler en « répartition statutaire en trois tiers égaux »,
tout en gardant une réserve sur les évolutions possibles.

## M5 — `modeles/clt-bruxelles.yml` : date précise disponible

L'ASBL et la fondation d'utilité publique CLTB ont été constituées le
**20 décembre 2012**. La fiche dit « fondé fin 2012 » : exact mais
imprécis. Suggestion : préciser « 20 décembre 2012 » dans `resume` et
`fiabilite`.

## M6 — `lieux/nddl.yml` et `porteurs/fonds-la-terre-en-commun.yml` : chiffre de collecte ancien

Les deux fiches citent « environ 700 000 € collectés en moins d'un an »,
chiffre de 2019. Sept ans plus tard, ce montant n'est plus représentatif.
Les recherches web n'ont **pas** permis de trouver un chiffre récent fiable
(acquisitions et surfaces 2023-2025). La fiche reste donc honnête en
qualifiant les données récentes de « non confirmées ». Suggestion : dater
explicitement « ~700 000 € collectés dès 2019 » (déjà fait pour
l'essentiel) et, si possible, consulter directement encommun.eco pour un
bilan à jour avant publication. Pas d'erreur, mais fraîcheur faible.

---

# Champ `fiabilite` : appréciation de l'honnêteté

Globalement, les champs `fiabilite` sont **honnêtes et bien construits** :
ils distinguent systématiquement faits vérifiés et points non confirmés,
et signalent l'évolutivité des chiffres (Lurzaindia, FEVE, RENETA). C'est
une bonne pratique.

Trois réserves :
- **`hameau-des-buis.yml`** : le `fiabilite` classe « pouvoir de décision
  final de l'association » parmi les **faits vérifiés**. C'est faux (cf. C1).
  Malhonnête au sens où un fait erroné est présenté comme vérifié.
- **`ferme-des-enfants.yml`** : même problème (cf. C2).
- **`cooperative-oasis.yml`** : « accompagnement d'environ 80 écolieux »
  classé en fait vérifié alors que 80 est un objectif (cf. C4).

Les autres fiches ne présentent pas de `fiabilite` malhonnête : les points
incertains y sont correctement signalés.

# Évaluations de grille (`grille:` valeur+note) insoutenables

- **`ferme-des-enfants.yml` / `articulation_porteur: oui`** — insoutenable :
  le lien avec le porteur a été rompu judiciairement en 2021. Doit passer à
  `non` (ou la fiche être archivée).
- **`hameau-des-buis.yml` / `montage_documente: oui`** — la note décrit un
  montage (SC + décision finale de l'association) qui n'est plus en vigueur.
  La valeur peut rester `oui` (le montage *actuel*, SAS coopérative, est
  documenté) mais **la note doit être réécrite** pour décrire la SAS
  coopérative et non l'ancienne SC.
- **`cooperative-oasis.yml` / `public_non_restreint: oui`** — la valeur
  `oui` reste défendable, mais la **note s'appuie sur le chiffre « 80 »**
  non établi : réécrire la note avec le chiffre réalisé.

Aucune autre évaluation de grille n'apparaît manifestement insoutenable :
les valeurs `partiel` / `inconnu` sont employées avec prudence et les notes
sont en général cohérentes avec les faits.

# Liens croisés incohérents

- **`hameau-des-buis.yml` → `usufruitiers: [ferme-des-enfants]`** :
  incohérent (l'association a quitté le lieu). À retirer ou requalifier.
- **`ferme-des-enfants.yml` → `lieux: [hameau-des-buis]`** : même
  incohérence symétrique.
- **`cooperative-oasis.yml` → `lieux: [hameau-des-buis]`** : à vérifier —
  la fiche Oasis lie le Hameau des Buis, mais aucune des deux fiches
  Hameau/Ferme ne mentionne un financement par la Coopérative Oasis. Lien
  possiblement injustifié ; à confirmer ou retirer.
- **`feve.yml` → `porteurs: [lurzaindia-sca, fonciere-terre-de-liens]`** :
  liens « entre porteurs comparables », acceptables s'ils sont présentés
  comme des analogies de modèle et non comme des liens capitalistiques.
  Pas une erreur factuelle, mais à clarifier éditorialement.

Les autres liens croisés (porteur ↔ lieu ↔ usufruitier) sont cohérents.

---

# Récapitulatif des corrections par fiche

| Fiche | Priorité | Correction |
|---|---|---|
| `lieux/hameau-des-buis.yml` | Critique | Montage périmé : décrire la SAS coopérative (28/01/2023) ; La Ferme des Enfants a quitté le lieu en 2021 |
| `usufruitiers/ferme-des-enfants.yml` | Critique | Fiche périmée : archiver ou requalifier en rôle historique |
| `porteurs/feve.yml` | Critique | Chiffres : 53 fermes, 78 paysan·nes, 3 300 ha, 60 M€ |
| `usufruitiers/cooperative-oasis.yml` | Critique | « 80 écolieux » est un objectif 2025 ; mettre le chiffre réalisé (~57) |
| `lieux/villarceaux.yml` | Importante | « EARL du Chemin Neuf » et non « EARL Olivier Ranke » ; « Saveurs du Vexin » ; six structures |
| `usufruitiers/ecosite-villarceaux.yml` | Importante | Mêmes corrections que villarceaux (EARL, coopérative) |
| `lieux/lurzaindia.yml` | Importante | Chiffres : 486 ha, 41 agriculteurs, 3 775 actionnaires, 1,67 M€ |
| `porteurs/lurzaindia-sca.yml` | Importante | Mêmes chiffres que lurzaindia |
| `lieux/larzac.yml` | Importante | Dater la prolongation du bail : 1985 (60 ans) → 2013 (99 ans) |
| `usufruitiers/sctl.yml` | Importante | Même datation du bail |
| `lieux/reseau-terre-de-liens.yml` | Importante | Préciser périmètre Safer ; source rapport 2024-2025 |
| `porteurs/fondation-fph.yml` | Importante | `annee: 1982` ; siège Lausanne |
| `porteurs/fonciere-antidote.yml` | Importante | Nouveau nom « Antidote » |
| `porteurs/conservatoire-littoral.yml` | Mineure | Ajouter ~220 000 ha / 840 sites ; cinquantenaire 2025 |
| `usufruitiers/cooperatives-longo-mai.yml` | Mineure | « Statut associatif privilégié » non vérifié : reformuler |
| `lieux/longo-mai.yml` | Mineure | Préciser réseau européen, pas seulement France |
| `modeles/clt-bruxelles.yml` | Mineure | Répartition tripartite = règle effective ; date 20/12/2012 |
| `lieux/nddl.yml` | Mineure | Dater le chiffre de collecte (2019) ; chercher données récentes |
| `porteurs/fonds-la-terre-en-commun.yml` | Mineure | Idem nddl |

---

# Sources de vérification (web, mai 2026)

- Terre de Liens — Rapport annuel de la Fondation 2024-2025 (14/01/2026) :
  https://terredeliens.org/national/actu/rapport-annuel-de-la-fondation-2024-2025-14-01-2026/
- Banque des Territoires — 20 ans Terre de Liens / Safer :
  https://www.banquedesterritoires.fr/20-ans-de-collaboration-entre-terre-de-liens-et-les-safer
- AGTER — La SCTL du Larzac :
  https://www.agter.org/bdf/fr/corpus_chemin/fiche-chemin-9.html
- Basta! — Le plateau du Larzac à l'abri jusqu'en 2083 :
  https://www.bastamag.net/Le-plateau-du-Larzac-a-l-abri-des
- Lurzaindia — site officiel : https://lurzaindia.eu/
- Arrapitz — Lurzaindia :
  https://www.arrapitz.eus/les-associations-reseau-arrapitz/lurzaindia/
- Coopérative Oasis — Investir : https://cooperative-oasis.org/soutenir/investir/
- Weelim — FEVE, 19 M€ collectés en 2024 :
  https://www.weelim.fr/actualites-placement/finance-durable/ferme-en-vie-19-me-collectes-en-2024-et-24-fermes-supplementaires/
- Reussir — FEVE, collecte 2025 :
  https://www.reussir.fr/renouvellement-agricole-25-millions-deuros-par-la-fonciere-feve-en-2025-un-record
- Conservatoire du littoral — 200 000 hectares protégés :
  https://www.conservatoire-du-littoral.fr/actualite/247/4-l-actualite.htm
- info.gouv.fr — Conservatoire du littoral, 50 ans :
  https://www.info.gouv.fr/actualite/conservatoire-du-littoral-50-ans-au-service-de-la-protection-des-rivages
- Bergerie de Villarceaux — site officiel : https://www.bergerie-villarceaux.org/
- Val d'Oise Tourisme — Ferme de la Bergerie de Villarceaux :
  https://www.valdoise-tourisme.com/fiches/ferme-de-la-bergerie-de-villarceaux/
- Hameau des Buis — L'histoire : https://hameaudesbuis.org/lhistoire/
- La Ferme des Enfants — Comprendre le conflit :
  https://la-ferme-des-enfants.com/wp-content/uploads/sites/2/2020/01/comprendre-conflit.pdf
- Oasis de Poulart — Comprendre le conflit :
  https://oasisdepoulart.org/comprendre-le-conflit/
- CLT Bruxelles — 2012 : https://cltb.be/ligne_du_temps/2012/
- Citego — CLT Bruxelles : https://www.citego.org/bdf_fiche-document-871_fr.html
- Antidote — Notre fonctionnement :
  https://aventure-antidote.org/comment-ca-marche/notre-fonctionnement/
- Wikipédia — Fondation Charles Léopold Mayer :
  https://fr.wikipedia.org/wiki/Fondation_Charles_L%C3%A9opold_Mayer_pour_le_progr%C3%A8s_de_l'Homme
