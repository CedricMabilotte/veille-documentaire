# Vérification fine des citations et des dates de publication — toutes les fiches

*Session « biblio #22 » — 6 juillet 2026. Audit, pas de correction de contenu
appliquée sans confirmation de Ced (voir décisions en attente, §5).*

## Méthode

Deux nouveaux scripts pérennes, dans la logique des garde-fous existants
(`audit_titres.py`, `audit_apercus.py`) :

- **`scripts/audit_citations.py`** — relit chaque citation (`enrichment.citations`)
  contre le texte du PDF local actuellement disponible, en réutilisant
  `synopsis_enricher.verify_citations()` (la même recherche littérale
  tolérante que celle appliquée à l'enrichissement, item A4 anti-hallucination).
  Contrairement à l'enrichissement d'origine (limité à ~12000 caractères),
  l'audit relit le document en quasi-intégralité, pour ne pas confondre une
  fenêtre de lecture plus courte avec une vraie régression.
- **`scripts/audit_dates.py`** — contrôle `doc_date` (date de publication de
  la source, distincte des dates de run) : vide, format invalide, plage
  résiduelle, année future, incohérence avec `collected_date`, année très
  ancienne, écart net avec une année mentionnée dans le titre.

Périmètre : les **866 fiches effectivement publiées** (`site/fiches/*.html`),
pas seulement les docs ayant un `score_final`.

## 1. Citations — résultat global

294 fiches publiées portent des citations (2156 citations au total).

| Catégorie | Nombre | Sens |
|---|---|---|
| CONFIRME | 1588 | vérifié à l'enrichissement, toujours vérifié |
| JAMAIS_VERIFIE | 298 | jamais retrouvé dans le texte, ni avant ni maintenant |
| PDF_INVALIDE_LOCAL | 158 | **le fichier local n'est pas un vrai PDF** (voir §2) |
| NOUVELLEMENT_VERIFIE | 76 | pas vérifié à l'époque, retrouvé maintenant (bonne nouvelle) |
| PDF_ABSENT | 29 | aucun PDF local, non vérifiable |
| REGRESSION | 7 | vérifié à l'enrichissement, ne matche plus maintenant |

**Le point le plus important n'est pas dans ce tableau : c'est la découverte
en §2.**

### JAMAIS_VERIFIE (298 citations) — beaucoup plus rassurant qu'il n'y paraît

Réparti sur 154 fiches, mais très majoritairement en quelques citations
isolées par fiche (152 fiches sont un mélange confirmé/non-vérifié — typique
d'une reformulation légère, d'un artefact d'OCR, ou d'une coupure de
paragraphe, pas d'une fabrication). Seules **2 fiches sont à 100 %
non-vérifiées** :

- `510c2d69` — *The Spatial Structure of a "Mura" (Village) Territory…*
  (japonais). Cas probable de limite technique : la normalisation de
  correspondance est pensée pour des scripts latins (accents), pas pour le
  CJK — pas un signal d'alarme en soi, mais à relire si le temps le permet.
- `b6f4faf4` — *IHUOnlineEdicao485* (portugais, 3 citations). PDF valide,
  aucune corruption détectée — à relire individuellement, cas isolé.

**11 fiches ont une majorité de citations non vérifiées** (mais pas 100 %) —
liste à relire en priorité si Ced veut auditer manuellement un échantillon :
`08baa6d1`, `14f9c4d0`, `469b3543`, `567a1117`, `679c85f6`, `6ac17e44`,
`804ecf0d`, `a54f94c8`, `aa5d50ec`, `ce08b5a4`, `f349dcb8`.

## 2. Découverte principale — 20 fiches publiées avec un PDF local corrompu

En creusant pourquoi certaines citations basculaient de CONFIRME à
REGRESSION, ou étaient massivement JAMAIS_VERIFIE en bloc plutôt qu'en
citations isolées, il s'avère que **le fichier `.pdf` local de 20 fiches
publiées n'est en réalité pas un PDF** — il échoue au contrôle de magic
bytes `pdf_processor.validate_pdf()` déjà existant dans le pipeline, mais
qui n'a jamais été appliqué à ces fichiers-là. Deux causes distinctes,
toutes deux vérifiées en ouvrant les fichiers :

**A. 13 fiches HAL** (`0b22d51b`, `2db11a52`, `46327ff6`, `572794b2`,
`5f5dadd2`, `7b89d6d1`, `85a0da6c`, `97c3bbb4`, `b8342aff`, `d647480f`,
`e5341cc9`, et `d64f2d03`/`e41de87d` sans citations) — le fichier local est
en réalité une page **Anubis** (système anti-scraping par preuve de travail,
déployé récemment par HAL) : « Making sure you're not a bot!… Please enable
JavaScript ». `verified` valait `None` (jamais évalué) sur ces citations
dans le catalogue — ces fiches semblent avoir été enrichies hors du pipeline
normal (`collected_date` vide), probablement via une session Cowork qui a lu
la page HAL directement (résumés cohérents et bien informés) mais n'a
jamais réussi à sauver le vrai PDF localement.
→ **Conséquence : toute nouvelle tentative de téléchargement automatisé
depuis HAL échouera de la même façon tant qu'Anubis est en place.**

**B. 7 fiches** (`55db5001`, `83b6390f`, `915b8d79`, `acd4bba6`, `c37935c3`,
`c99e6da4`, `df13538a`) + `fba04469` (8 au total) — le fichier local est en
réalité la **page « detail/borrow » d'archive.org** (« Free Download,
Borrow, and Streaming : Internet Archive »), pas le PDF. Root cause
identifiée dans le code : `scripts/regen_covers.py::download_pdf()`
(utilisé pour le Phase 2 de régénération des couvertures, sessions #17-18,
537 PDFs "manquants" re-téléchargés) **n'appelait jamais
`pdf_processor.validate_pdf()`** après téléchargement — contrairement au
flux normal (`download_and_validate` dans `watch.py`). Quand l'item
archive.org d'origine est passé en emprunt restreint (ou que l'URL ne pointe
plus vers un lien direct), le script a sauvé la page HTML de la fiche
archive.org sous l'extension `.pdf` sans qu'aucun contrôle ne s'y oppose.
C'est très probablement ce qui explique aussi la seule vraie REGRESSION
restante (`54ae9934` — PDF valide, non corrompu, à part) : citations
vérifiées à l'enrichissement (le vrai PDF existait alors), puis le PDF
local a été perdu entre-temps (cf. L29) et ce que Phase 2 a « récupéré » à
la place n'était pas le document réel pour 8 d'entre elles.

**Corrigé maintenant (garde-fou, code seul, aucune donnée modifiée) :**
`regen_covers.py::download_pdf()` appelle désormais `validate_pdf()` après
téléchargement et rejette (supprime le fichier, log explicite) toute
réponse qui n'est pas un vrai PDF — même logique que le pipeline principal,
pour que ce type de re-téléchargement défaillant ne puisse plus se
reproduire silencieusement.

**Ce qui reste à décider (Ced) :** ces 20 fiches restent publiées avec des
citations non re-vérifiables localement — pas parce que le contenu est
faux (les résumés sont cohérents), mais parce que la preuve matérielle
(le PDF) n'est plus disponible en local pour la re-contrôler. Options :
retenter un téléchargement manuel (nécessite de contourner Anubis/JS pour
HAL — pas faisable depuis ce bac à sable), accepter le statu quo en
l'état, ou dépublier au cas par cas si le doute est jugé trop important.

## 3. Dates de publication — résultat global

866 fiches auditées, 173 avec un signalement.

| Catégorie | Nombre | Gravité |
|---|---|---|
| VIDE | 159 | doc_date jamais renseigné (18 % des fiches publiées) |
| A_VERIFIER_TITRE | 14 | écart net titre/date — heuristique, informationnel |
| FORMAT_INVALIDE | 0 | — |
| PLAGE_RESIDUELLE | 0 | pas de régression du garde-fou L12 |
| ANNEE_FUTURE | 0 | — |
| ANTERIEUR_COLLECTE | 0 | — |
| TRES_ANCIEN (<1800) | 0 | — |

**Bonne nouvelle structurelle :** aucune plage résiduelle, aucune date
future, aucune incohérence de collecte — les garde-fous posés en L12
(session #3) tiennent toujours. Le vrai point d'attention est ailleurs :

**159 fiches publiées (18 %) n'ont aucune date de publication renseignée.**
C'est la lacune principale sur les dates — pas une donnée fausse, une donnée
absente. Backfill possible au cas par cas (métadonnée PDF, page source) mais
hors du périmètre de cette vérification (qui contrôle, ne corrige pas).

**14 écarts titre/date à reléguer** — dont un sous-groupe intéressant :
plusieurs déclarations historiques de La Via Campesina partagent une
`doc_date` identique en lot (`2017-12-01` ×4, `2021-06-29` ×3) alors que
leur titre porte une année bien différente et cohérente (2005, 2009, 2002,
2007, 1996, 2013) — signe probable que `doc_date` reflète une date de
récolte/mise en ligne groupée plutôt que la date de publication réelle du
texte. À vérifier et backfiller si confirmé : `20d3c68f`, `223de305`,
`59b9dd0b`, `6dcf15e1`, `710bd16d`, `9da13ea1`, `c281d375`, `e8be8509`.
Les autres de la liste (`2478138a`/`7c44a8d2` Sonacotra, `bc522fd4`,
`c37935c3`, `e5274460`, `fac367e2`) semblent plutôt être des documents
rétrospectifs légitimes sur un événement passé — pas une erreur.

## 4. Ce qui n'a pas été touché

Aucune modification du catalogue (`synopsis/catalog.json`), aucune fiche
dépubliée, aucune citation retirée. Seul changement de code : le garde-fou
`validate_pdf()` ajouté dans `regen_covers.py` (§2). Les deux scripts
d'audit sont pérennes et réutilisables (`python3 scripts/audit_citations.py`,
`python3 scripts/audit_dates.py`), sur le modèle de `audit_titres.py` /
`audit_apercus.py`.

## 5. Décisions en attente (Ced)

1. **20 fiches à PDF local corrompu (HAL/Anubis + archive.org borrow-page)**
   — statu quo, tentative de récupération manuelle, ou dépublication au cas
   par cas ?
2. **11 fiches à majorité de citations non vérifiées** — relecture manuelle
   souhaitée, ou accepté tel quel (l'algorithme de correspondance a ses
   limites — reformulation, OCR, CJK) ?
3. **159 fiches sans date de publication** — backfill à programmer en
   session dédiée (mêmes sources que `doc_metadata.build_metadata()`), ou
   accepté en l'état pour l'instant ?
4. **8 dates La Via Campesina à date de récolte groupée suspecte** —
   confirmer et corriger individuellement à partir de l'année visible dans
   le titre ?
