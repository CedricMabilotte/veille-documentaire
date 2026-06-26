# Audit de cohérence des fiches publiées — 2026-06-26

Audit fiche par fiche sur les 98 docs publiés. Examen : titre, résumé, pertinence thématique, score, doublons.

---

## Tableau des actions

| UID | Titre (avant correction) | Problème | Action |
|-----|--------------------------|----------|--------|
| d64f2d03 | Document HAL — hal-02485830 | Titre = identifiant technique interne, pas lisible pour un humain | Titre corrigé : "Concurrence déloyale, créativité écrasée : l'agriculture vivrière en crise" (Hubert Cochet, depuis meta PDF) |
| a91bd215 | Zapatiste 2014 | Titre vague, filename opaque (`camotazo_2013_zapatiste_2014.pdf`). Le run indiquait "Islamic Anarchism" mais l'enrichissement confirme : lutte zapatiste pour la terre | Titre corrigé : "Quelques idées sur le mouvement zapatiste (2014)" |
| f2168aa7 | Skvotuoti Reiškia Kovoti (version lituanienne) | Titre en lituanien sans traduction | Titre complété : "Skvotuoti Reiškia Kovoti (Squatter c'est lutter) — version lituanienne" |
| 496c1d78 | make that future now | Tout en minuscules, vague — ressemble à une ligne de texte libre | Titre corrigé : "To Make That Future Now" |
| 28b7cb2c | The Cooperative Way of Housing in Canada | Résumé = texte brut répété du PDF (non traité) | Résumé remplacé par résumé propre |
| 2175f7a3 | Housing You Can Afford — Cooperative Housing in Canada | Résumé = texte brut non traité | Résumé remplacé par résumé propre |
| d64f2d03 | (idem ci-dessus) | Enrichissement spéculatif "Sans accès au PDF…" | Résumé remplacé par résumé propre tiré du meta PDF |
| b9a459d4 | Atop the Watchtower | Enrichissement = URL seule sans résumé réel | Résumé remplacé par résumé propre |
| 089ddfba | Notre blé est politique | Doublon de format avec 08baa6d1 (même texte, formats fil vs cahier) | Exclu dans exclusions.yml (doublon format, base : 08baa6d1) |
| 5c511048 | Acerca de las comunidades mapuche | Doublon de format avec 2c9a5575 (même texte Mapuche, cuaderno vs page par page). Score inférieur (6 vs 8). Titre en espagnol sans traduction. | Exclu dans exclusions.yml (doublon format, base : 2c9a5575) |
| 46327ff6 | Systèmes d'acteurs, freins et voies d'accès à la terre… | Dernier run disait "chiens de protection, hors-thématique" — mais enrichissement confirme pertinence (master géographie sur accès à la terre en Martinique) | Conservé. Résumé propagé depuis enrichissement. |
| 05392c72 | Observations sur le décret du 28 août 1792 | Run initial indiquait "North Carolina House of Commons" (erreur de contexte) — le doc réel est une critique du décret révolutionnaire sur le partage des biens communaux | Conservé. Résumé propagé depuis enrichissement. |

## Résumés propagés depuis enrichissement

86 fiches publiées n'avaient pas de `summary` dans le catalogue (champ vide), mais disposaient d'un `enrichment.summary` valide produit lors de la lecture du PDF. Ces résumés ont été propagés vers `doc["summary"]` pour que les fiches HTML les affichent correctement.

Les 4 cas exclus de la propagation automatique (résumés bruts ou spéculatifs) ont reçu un résumé manuel :
- `28b7cb2c`, `2175f7a3` : texte brut du PDF, non traité
- `d64f2d03` : enrichissement spéculatif "Sans accès au PDF"
- `b9a459d4` : enrichissement réduit à une URL

## Doublons de contenu identifiés

| Paire | Verdict |
|-------|---------|
| d647480f vs e5341cc9 | Même auteur (Benjamin Coriat), même sujet, mais deux dépôts HAL distincts (hal-03366910 / hal-03380720) — conservés tous les deux |
| 089ddfba vs 08baa6d1 | Même texte "Notre blé est politique", deux formats (fil / cahier) → doublon format, 089ddfba exclu |
| 5c511048 vs 2c9a5575 | Même texte Mapuche, deux formats (cuaderno / page par page) → doublon format, 5c511048 exclu |

## Pertinence thématique — aucune exclusion pour hors-sujet

Après vérification des enrichissements, tous les docs publiés sont thématiquement pertinents. Les cas suspects à la lecture des runs (46327ff6 "chiens de protection", 05392c72 "North Carolina") s'avèrent pertinents à la lecture de l'enrichissement — les raisons de runs erronées proviennent d'un mauvais contexte transmis au modèle lors du scoring initial.

## Scores — aucune correction

Aucun score n'a été modifié. Les overrides de Ced sont tous respectés. Les quelques scores élevés sur des docs sans enrichissement lisible (c99e6da4 score 8, e4f64264 score 8 override) sont protégés par score_overrides.yml ou confirmés par l'enrichissement.

---

## Résumé chiffré

| Catégorie | Nombre |
|-----------|--------|
| Fiches publiées examinées | 98 |
| Titres corrigés | 4 |
| Résumés propagés depuis enrichissement | 86 |
| Résumés manuels (remplacement) | 4 |
| Exclusions nouvelles (doublons format) | 2 |
| Exclusions hors-sujet | 0 |
| Scores modifiés | 0 |
| Fiches publiées après audit | 96 |
