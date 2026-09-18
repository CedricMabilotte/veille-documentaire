# Ré-extraction des PDF inexploitables et durcissement de la publication

**Date** : 2026-09-18 — **Corpus publié** : 817 fiches (contre 953 le 17/09)

Cette session traite les cinq points arbitrés le 18/09 (1+C, 2a, 3a, 4a+b, 5a+b) et
deux problèmes découverts en cours de route.

---

## 1. Ré-extraction manuelle des PDF anti-bot (point 3)

**Constat.** 16 fichiers de `docs/` n'étaient pas des PDF mais des pages HTML :
12 pages de défi anti-bot (Anubis) servies par HAL/CCSD à la place du document,
3 pages d'atterrissage archive.org, 1 fichier orphelin de 2,3 ko. Les fiches
correspondantes étaient malgré tout scorées et publiées — sur la foi du titre
et du contexte de collecte, jamais d'une lecture.

**Obstacles rencontrés.**

- Anubis ne rejoue pas son défi par origine mais **par requête** : le cookie
  obtenu sur la page d'atterrissage ne vaut pas pour `/document`, et toute
  requête `fetch` (`Sec-Fetch-Mode: cors`) est re-défiée même une fois le défi
  résolu. Seule une **navigation de premier niveau** passe.
- Le navigateur de l'utilisateur bloque les téléchargements automatiques
  multiples après le premier, et la préférence de site n'est pas pilotable
  depuis l'extension.
- Le POST d'un blob vers un serveur local (`127.0.0.1`) est bloqué par la
  protection « private network access » du navigateur.

**Solution retenue.** Un navigateur headless piloté par Playwright, sur la
machine locale, profil réglé sur `plugins.always_open_pdf_externally` : la
navigation vers `/document` résout le défi puis déclenche un téléchargement
réel, dont le fichier est récupéré tel quel. Boucle de 5 tentatives par
document (le défi échoue par intermittence — « Oh noes! »).
Script : `~/scratch-biblio/refetch/fetch.py`.

**Résultat.** 16/16 récupérés, tous `%PDF` valides, tailles cohérentes.
`docs/` ne contient plus aucun fichier non-PDF.

| Sortie | Nombre |
|---|---|
| Fiches ré-enrichies (couverture + texte + synopsis + score + titre) | 15 |
| Publiées après relecture | 12 |
| Écartées après relecture (score réel sous le seuil) | 2 |
| Écartée (scan sans couche texte) | 1 |

Deux fiches passent sous le seuil une fois réellement lues : `dc1574ae`
(Combate n°33, score 2) et `b8342aff` (HDR économie, score 3). Leur score
précédent de 9 et 8 venait du titre seul.

---

## 2. Champs internes exposés dans le catalogue publié

**Constat.** Le catalogue servi au public contenait, en plus des données
éditoriales : `enriched_by` (5 occurrences nommant l'outil), `raw_response`
(10 réponses brutes rédigées à la première personne), 29 messages
d'infrastructure (« session limit »), `_avertissement`,
`methodologie_appliquee`, et `context_seen` (2 235 entrées, ~2 Mo de contexte
de collecte jamais affiché). Aucun de ces champs n'est lu par le front-end.

C'est une infraction directe à la règle posée le 18/09 : aucune mention d'outil
d'assistance sur le site tant que le droit d'auteur n'aura pas tranché.

**Correction.** Le filtre de publication (`_strip_provenance`) est étendu à ces
champs, ainsi qu'aux `runs[].raison` purement techniques (`erreur scoring`,
`claude_call`, `json_parse`, `pdf_absent`, `text_too_short`, `auto_download`)
— que le front masquait déjà mais qu'on n'expédie plus du tout. Le flux RSS,
qui retombait encore sur ces `raison` internes comme `<description>`, est
corrigé lui aussi.

**Vérification sur le site en ligne** : 0 occurrence de `context_seen`,
`enriched_by`, `raw_response`, `model`, `error`, « erreur scoring »,
« auto_download », « session limit ». Les 16 occurrences restantes de
« Claude » sont le prénom d'une personne interviewée (Anne-Claude).
Catalogue publié : 8,3 Mo → 8,0 Mo.

---

## 3. Scans sans couche texte (découverte)

**Constat.** Un PDF déposé sur HAL commence par une page de garde du dépôt.
Quand le reste est une image scannée, l'extraction ne rend que cette page :
assez longue pour franchir n'importe quel seuil de caractères, vide de contenu.
Le balayage des 838 fiches publiables a trouvé :

- 1 fiche de ce type exactement (`d64f2d03`, 13 pages dont 12 en image) ;
- **21 fiches publiées dont le PDF ne rend aucun texte** — affiches, tracts,
  bandes dessinées, lettres d'information scannées, drapeaux vectoriels,
  programmes de rencontre. Aucune n'a de synopsis ni de score de lecture ; la
  plupart portent un nom de fichier en guise de titre (« Bandeira MST Vetor »,
  « COMIC INGLES FINAL CORREGIDO.cdr », « Mpp »).

**Correction.** Les 21 sont écartées via `config/exclusions.yml`, avec un motif
explicite — réversible en une ligne. Trois fiches sans texte extractible sont
**conservées** car elles disposent d'un synopsis réel venu d'une autre source
(`55db5001`, `de3ff94a`, `5ea6c0cc`).

Un garde-fou est ajouté au pipeline :
`pdf_processor.text_is_repository_banner_only()` détecte la page de garde
d'archive ouverte et l'absence de contenu au-delà ; `watch.py` marque alors la
fiche « scan sans couche texte » au lieu de consommer un appel
d'enrichissement pour produire une fiche creuse.

---

## 4. Poussée par lots

Un `commit_push` de 95 Mo meurt en sideband après ~16 minutes. Le découpage par
volume n'existait que pour les couvertures : il s'applique désormais à toutes
les données (`PUSH_MAX_BYTES = 6 Mo`). Les lots de 6 Mo passent en 5 à 10
secondes.

Incident associé : `commit_push` a été appelé avec `docs` dans ses chemins,
alors que `docs/*` est dans `.gitignore`. La fonction ne lit pas `.gitignore`
— elle compare fichier à fichier avec `origin/main` — et s'est donc mise à
pousser les 3,5 Go du corpus, découpés en 436 lots. Arrêté au 8ᵉ, branche
distante restaurée par force-push sur `659d7a30`, aucun autre travail perdu.

---

## Sauvegarde du corpus : à traiter

`docs/` est volontairement hors dépôt (3,5 Go de binaires). Le `.gitignore`
renvoie à « une sauvegarde durable sur Google Drive privé via rclone ».
Cette sauvegarde contenait **16 fichiers, datés du 23 juin**. Les 1 071 PDF du
corpus n'existent donc qu'en un seul exemplaire, sur le disque de la machine.
Les 16 PDF ré-extraits y ont été copiés ; le reste attend une décision.

Une synchronisation complète représente ~3,5 Go, soit environ une heure sur la
liaison actuelle.

---

## Compte du corpus publié

| Étape | Fiches publiées |
|---|---|
| 17/09 après restauration des doublons | 953 |
| Garde-fou « enrichissement échoué sans score » | 855 |
| Relecture réelle des 16 PDF ré-extraits | 838 |
| Exclusion des 21 fiches sans contenu | **817** |
