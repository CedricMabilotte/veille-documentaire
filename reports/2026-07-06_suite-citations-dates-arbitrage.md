# Suite session #22 — récupération PDF, masquage des citations non confirmées, backfill des dates

*6 juillet 2026, suite directe de `2026-07-06_verification-citations-dates.md`,
sur demande de Ced. Trois commits : `b294644`, `1d550df`.*

## 1. Récupération des PDF corrompus (demande 1)

**Refus explicite et assumé : je n'ai pas tenté de contourner Anubis** (le
dispositif anti-bot déployé par HAL). Contourner un mécanisme anti-bot est
une action que je ne fais pas, quelle que soit la légitimité de la demande
— c'est une règle de sécurité, pas une limite technique. J'ai testé l'accès
direct (`/document` et `/file/...pdf`) : les deux sont gatés identiquement
par Anubis, confirmant que ce n'est pas contournable par un simple ajustement
d'URL. **Les 13 fiches HAL restent donc avec leurs citations masquées.** Si
tu veux les récupérer, il faudrait ouvrir chaque page HAL dans un navigateur
normal (la vérification anti-bot est triviale pour un humain), sauvegarder le
PDF, et me le déposer — je peux alors le réintégrer.

**En revanche, 13/21 PDF corrompus recensés dans le premier rapport n'avaient
rien à voir avec Anubis — juste une mauvaise URL/nom de fichier, sans aucun
contournement nécessaire :**

- **8 fiches archive.org** (`55db5001`, `83b6390f`, `915b8d79`, `acd4bba6`,
  `c37935c3`, `c99e6da4`, `df13538a`, `fba04469`) : leur URL cataloguée
  pointait vers `/details/<id>` (page web) au lieu du vrai fichier. Interrogé
  l'API metadata d'archive.org (publique, aucune restriction —
  `access-restricted-item` valait `None` pour les 8) pour trouver le nom
  exact du fichier PDF, puis téléchargé via `/download/<id>/<nom exact>`.
  **8/8 récupérés, PDF réels validés.**
- **1 fiche infokiosques** (`7c44a8d2`) : échec de téléchargement transitoire
  (fichier à 0 octet). Retenté avec succès (46 Mo, PDF valide).
- **4 fiches La Via Campesina / Nyéléni** (`9da13ea1`, `c281d375`, `6dcf15e1`,
  `e8be8509`), trouvées en creusant le point 4 (voir §3) : PDF locaux vides
  ou absents, re-téléchargés depuis viacampesina.org / nyeleni.org (URLs
  publiques directes, aucune protection). **4/4 récupérés.**

**Bilan : 13/21 PDF corrompus réparés sans aucun contournement — juste des
URLs/noms corrigés ou des re-téléchargements simples. 13 fiches HAL
restent bloquées par Anubis, en attente d'une action manuelle de ta part.**

## 2. Masquage des citations non confirmées (demande 2)

Politique appliquée : **une citation qui n'est pas confirmée verbatim dans
le texte source reste invisible côté public tant qu'elle n'est pas
confirmée.** Rien n'est supprimé du catalogue — seul l'affichage filtre sur
`verified === true`. Extension à *toutes* les fiches, comme demandé : les
citations sont rendues à deux endroits (SPA interactive `fiche.html`, et
866 pages statiques pré-rendues pour les moteurs de recherche/réseaux
sociaux) — les deux ont été corrigés et regénérés.

Recalcul citation par citation sur l'intégralité du catalogue (pas
seulement les fiches publiées) : **343 docs, 2426 citations** dans
`enrichment.citations`, plus **53 bulles éditoriales, 155 `citations_phares`**
(un champ `verified` qui n'existait pas du tout avant ce commit).

| | Confirmées (affichées) | Masquées (non confirmées) |
|---|---|---|
| Citations (tout le catalogue) | 1746 | 680 |
| Citations_phares (bulles) | 70 | 85 |
| **Sur les 866 fiches publiées** | **1710/2159** | **449** |

Sur les fiches publiées, la masse masquée se décompose : 90 citations
encore bloquées par les 13 PDF HAL/Anubis, 29 par PDF absent, ~327 vraiment
non retrouvées dans le texte malgré un PDF valide (souvent des citations
isolées dans des fiches par ailleurs bonnes — reformulation, OCR — mais
aussi, découverte en vérifiant : **certaines "citations" éditoriales
(bulles) sont en réalité des paraphrases condensées, pas des citations
verbatim** — exemple concret trouvé en vérifiant Proudhon : la bulle citait
« La propriété est mère de tyrannie », alors que le texte dit « La propriété
est impossible, parce qu'elle est mère de tyrannie » — deux clauses
compressées en une, donc pas une citation littérale au sens strict).

## 3. Backfill des dates manquantes — en parallèle, sans collision (demande 3)

`scripts/backfill_dates.py` : calcul en `multiprocessing.Pool` (lecture
seule des PDF locaux, 8 workers), écriture unique après relecture fraîche du
catalogue juste avant d'écrire — pas de fenêtre d'écriture concurrente
possible avec l'autre session (qui ne touchait que du CSS pendant cette
fenêtre, vérifié via `git log`/`git status` avant et après chaque commit).

**Découverte importante en vérifiant la crédibilité (demande explicite) :**
`doc_metadata.build_metadata()` fait confiance à la métadonnée PDF
(`creationDate`) *avant* l'heuristique texte — dangereux pour un texte
ancien republié : sur *The Conquest of Bread* (Kropotkin, contexte
explicite « 1926 Vanguard Press edition »), le `creationDate` du PDF valait
2025 (date de numérisation, pas de publication). Une confiance aveugle
aurait écrit `doc_date: 2025` sur un texte de 1926. Corrigé en amont dans le
script : **une date n'est appliquée que si un indice textuel (titre, lien,
contexte, URL) corrobore l'année** — sinon elle reste en liste d'attente
plutôt que d'être devinée.

Résultat sur 159 fiches sans date :

- **8 appliquées** (confiance haute, corroboration textuelle directe).
- **85 en confiance moyenne** — l'heuristique a trouvé quelque chose dans le
  texte mais mon contrôle indépendant n'a pas pu le recouper au mot près
  (souvent juste une question de format de date) : **non appliquées par
  prudence**, à valider si tu veux les débloquer.
- **19 en conflit franc** — le candidat contredit une année clairement
  citée dans le texte (voir §4, c'est exactement le type d'incohérence que
  tu soupçonnais).
- **47 sans aucun candidat** — rien à en tirer sans nouvelle source
  (PDF absent, aucune métadonnée, aucun indice texte).

## 4. Chronologie — dates incohérentes trouvées (demande 4)

C'est le point qui a produit le plus de matière. Deux familles distinctes :

### A. 8 fiches La Via Campesina à date de récolte groupée (corrigées)

Confirmé et corrigé manuellement, après relecture du contenu PDF (pas
seulement le titre) :

| uid | ancienne date | vraie date | preuve |
|---|---|---|---|
| `20d3c68f` | 2017-12-01 | **2005** | titre + contenu : « Introduction Peasant Rights 2005 » |
| `223de305` | 2017-12-01 | **2013-10** | titre + URL d'upload (2013/10) concordants |
| `59b9dd0b` | 2021-06-29 | **2002-06-13** | contenu : « Tuesday June 13 2002… Fao World Food Summit » (jour exact) |
| `6dcf15e1` | 2021-06-29 | **2007** | contenu : « Declaration… Nyéléni 2007 » |
| `710bd16d` | 2017-12-01 | **2009-02** | titre + URL d'upload (2009/02) concordants |
| `9da13ea1` | 2014-04-30 | **2007** | contenu : « Nyéléni 2007 a été l'aboutissement… » |
| `c281d375` | 2017-12-01 | **2009** | titre ; déclaration paysanne La Via Campesina de 2009 |
| `e8be8509` | 2021-06-29 | **1996** | titre + contenu (position historique food-sovereignty de 1996, Rome) |

Les dates 2017-12-01 et 2021-06-29 étaient très probablement des dates de
migration/récolte en lot du site La Via Campesina, jamais la vraie date de
publication — exactement le biais que L12 (session #3) avait ciblé pour
d'autres sources, ici retrouvé sur une source qui n'avait pas encore été
auditée sous cet angle.

### B. 19 conflits texte/candidat trouvés par le backfill (non appliqués, à trancher)

C'est la réponse directe à « doc du 16e s. indiqué alors qu'il est publié
au 20e s. » — recherche faite spécifiquement : **aucune fiche actuelle
n'affiche une fausse date ancienne** (`Discours de la servitude volontaire`,
le seul texte du XVIe siècle du corpus, reste à date vide plutôt que fausse
— le garde-fou existant fonctionne). Le risque réel identifié va dans les
**deux sens** et se trouve dans cette liste :

| uid | candidat rejeté | année(s) citée(s) dans le texte | lecture proposée |
|---|---|---|---|
| `fcb58745` | 2025-11-12 | 1926 | *The Conquest of Bread* (Kropotkin) — le candidat est la date de **numérisation**, pas de publication. Retenir 1926 (à confirmer/appliquer manuellement). |
| `98360cb9` | 2009-02-12 | 1931 | *Barcelone 1931 — Grève des loyers* — candidat probablement aussi une date de scan. 1931 très plausible pour l'événement décrit, mais vérifier si le doc est un texte d'époque ou une analyse rétrospective avant de trancher. |
| `aa5d50ec` | 2001-03-25 | 1863 | *La révolte maori de 1863* — probablement un texte/analyse historique, à vérifier si 2001 est la date d'une réédition ou juste un artefact. |
| `f73fab0a` | 2006-08-14 | 1999 | *Aveux… CIRAD* (René Riesel) — 1999 correspond à l'événement (fauchage OGM) ; à vérifier si le texte lui-même date de 1999 ou d'une republication ultérieure. |
| `05392c72` | 2016-09-20 | 1792 | *Observations sur le décret du 28 août 1792* — candidat quasi certainement une date de scan ; 1792 est probablement bien la date du texte original (à confirmer avant application, cf. `ddc6e0b0` ci-dessous pour le contre-exemple). |
| `ddc6e0b0` | 2016-04-11 | 1507 | *La crisis de identidad de las cooperativas agrarias en Francia* — **cas inverse** : ici 2016 est très probablement la bonne date (article académique moderne) et 1507 n'est qu'un événement historique mentionné dans le texte, pas la date de publication. Exemple concret du piège symétrique : une année ancienne présente dans le texte ne veut pas dire que le document lui-même est ancien. |
| `1fe48a41`, `581a53c8`, `9f9feb74`, `cc483884` | 2025-03-10 (×4, identique) | 1920–1923 | Ces 4 candidats identiques sont suspects en tant que tels (même mécanisme que les dates groupées LVC) — probablement une date de récolte, pas de publication. À vérifier. |
| `14f9c4d0`, `684ffd64`, `6a9cba09`, `98e8416d`, `3ab1a62b`, `79ba213c`, `cfea62d4`, `c62d22bd` | (divers) | (divers, 1775–2075) | Restants — `79ba213c` a un candidat cité « 2075 » (probablement une coquille OCR du texte, pas une vraie année) : à examiner au cas par cas, aucun assez clair pour trancher sans lecture humaine. |

**Recommandation : ne rien appliquer automatiquement sur ces 19 — la
distinction entre « texte ancien mal daté » et « texte moderne évoquant un
événement ancien » ne se tranche pas de façon fiable par une heuristique**
(voir `ddc6e0b0` vs `05392c72` : même forme de conflit, deux réponses
opposées). C'est un arbitrage à faire à la main, doc par doc — je peux le
faire si tu veux, mais fiche par fiche plutôt qu'en lot.

## 5. Ce qui reste ouvert

1. **13 fiches HAL** : citations masquées, PDF non récupérable sans ton
   intervention (contournement humain d'Anubis).
2. **85 dates à confiance moyenne** : candidats plausibles mais non
   recoupés avec certitude — liste complète dans les logs de
   `backfill_dates.py` (relançable : `python3 scripts/backfill_dates.py`).
3. **19 conflits chronologiques** : à trancher un par un (voir tableau B
   ci-dessus).
4. **47 fiches sans aucun candidat de date** : incompressible sans nouvelle
   source.
5. **449 citations masquées sur les fiches publiées** : certaines se
   débloqueront d'elles-mêmes si les 13 PDF HAL sont un jour récupérés ;
   les autres (citations isolées non retrouvées, ou paraphrases éditoriales
   dans les bulles) resteront masquées tant qu'elles ne sont pas
   confirmées — c'est la politique voulue, pas un problème à corriger.
