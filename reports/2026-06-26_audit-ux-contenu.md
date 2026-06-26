# Audit UX et éditorial — biblio.actitude.org
**Date :** 2026-06-26  
**Périmètre :** 98 docs publiés (score_final ou score_initial ≥ 6, hors exclusions.yml)  
**Corpus :** 54 fr / 40 en / 4 es

---

## Chiffres clés avant tout

| Critère | N | % |
|---|---|---|
| Docs publiés | 98 | — |
| Avec résumé (summary) | 96 | 98 % |
| Avec explication grand public (en_clair) | 43 | 44 % |
| Avec au moins une citation | 71 | 72 % |
| **Avec auteur identifié** | **0** | **0 %** |
| Avec date de document | 56 | 57 % |
| Enrichissement en erreur | 28 | 29 % |
| Docs non-fr sans aucune citation | 12 | 12 % |
| Relevance_score < 6 (hors-sujet potentiel) | 8 | 8 % |
| Docs sans relevance_score évalué | 41 | 42 % |

Le chiffre qui devrait sauter aux yeux : **0 auteur sur 98 fiches publiées**. Ce n'est pas un oubli de pipeline, c'est un angle mort structurel de la métadonnée.

---

## 1. Top 10 titres problématiques à revoir

Classés par gravité décroissante.

### 1. `a91bd215` — *Zapatiste 2014*
**Problèmes :** tag interne + année utilisés comme titre, lang=en sans traduction, aucun sens pour un lecteur externe.  
**Ce qu'on devrait lire :** "Récit zapatiste — La liberté selon les Caracoles (2014)" ou similaire, avec le titre original entre parenthèses.

### 2. `f2168aa7` — *Skvotuoti Reiškia Kovoti*
**Problèmes :** titre en lituanien sur une fiche classée lang=fr. Totalement opaque. Le lecteur ne sait pas qu'il s'agit d'un texte sur le squat ("Squatter c'est lutter"). Aucune traduction, aucun sous-titre.

### 3. `d64f2d03` — *Document HAL — hal-02485830*
**Problèmes :** identifiant technique brut exposé comme titre. C'est un identifiant de dépôt, pas un titre humain. Le document a forcément un titre réel dans HAL — il n'a pas été récupéré.

### 4. `dc1574ae` — *Combate, Año 3, N°33, 23 de Abril de 1959*
**Problèmes :** métadonnée bibliographique de revue cubaine utilisée comme titre, en espagnol, sans traduction, sans enrichissement (erreur d'enrichissement). Le lecteur ne sait pas de quoi ça parle.

### 5. `35641d6d` — *Lunes de Revolución, N°1, 18 de Mayo de 1959*
**Problèmes :** idem — numéro de revue cubaine révolutionnaire. Même format, même erreur d'enrichissement, même opacité.

### 6. `03b9d287` — *Combate, Año 3, N°29, 18 de Abril de 1959*
**Problèmes :** troisième déclinaison du même problème. Ces trois revues cubaines (03b9d287, 35641d6d, dc1574ae) forment un groupe homogène sans aucune valeur documentaire visible pour l'utilisateur.

### 7. `5ea6c0cc` — *Ulka Mahajan — Manthan (Nov-Dec 2006)*
**Problèmes :** format "Auteur — Revue (période)" sans titre réel du texte. Qui est Ulka Mahajan ? Qu'est-ce que Manthan ? Le visiteur n'a aucune entrée. Erreur d'enrichissement, pas de citations.

### 8. `b9a459d4` — *Atop the Watchtower*
**Problèmes :** titre poétique en anglais, court, sans traduction, sans contexte visible (relevance_score non calculé, pas de en_clair, pas de citations, erreur d'enrichissement). Inaccessible à un lecteur francophone.

### 9. `d89a50ee` — *Green Anarchism*
**Problèmes :** titre générique en anglais, sans traduction, sans sous-titre. "Anarchisme vert" couvre un spectre trop large — le lecteur ne sait pas s'il s'agit d'un manifeste, d'une analyse, d'un pamphlet. Aucune accroche différenciatrice.

### 10. `83b6390f` — *Commonist Tendencies*
**Problèmes :** jeu de mot anglais intraduisible ("communist" + "commons") sans explication. Aucun sous-titre. Pour un lecteur francophone qui ne connaît pas ce texte spécifique de Massimo De Angelis, c'est un mur opaque.

---

## 2. Docs non-fr sans citations (traduites ou brutes)

Ces 12 docs en anglais ou espagnol n'ont aucune citation extraite. Pour les 6 marqués "ERREUR ENRICH", le pipeline a planté avant de produire la moindre extraction — la fiche publiée est une coquille vide avec seulement un résumé généré. Pour les 3 restants sans erreur, l'enrichissement a tourné mais n'a rien extrait.

**Docs avec erreur d'enrichissement (aucune citation, aucun en_clair) :**

| UID | Titre | Langue |
|---|---|---|
| `e4f64264` | Podłoże ruchu (Les fondements du mouvement) — Archives polonaises | en |
| `8bfe460c` | The Peasant Movement in Kwantung — Materials on the Agrarian Question | en |
| `5ea6c0cc` | Ulka Mahajan — Manthan (Nov-Dec 2006) | en |
| `03b9d287` | Combate, Año 3, N°29, 18 de Abril de 1959 | es |
| `35641d6d` | Lunes de Revolución, N°1, 18 de Mayo de 1959 | es |
| `dc1574ae` | Combate, Año 3, N°33, 23 de Abril de 1959 | es |
| `b9a459d4` | Atop the Watchtower | en |
| `ea71c1cb` | Worcester Soldiers' Commonwealth | en |
| `de3ff94a` | Community Land Trust Book | en |

**Docs sans erreur mais sans citations (enrichissement incomplet) :**

| UID | Titre | Langue |
|---|---|---|
| `28b7cb2c` | The Cooperative Way of Housing in Canada | en |
| `2175f7a3` | Housing You Can Afford — Cooperative Housing in Canada | en |
| `b0917bdf` | Integrating Customary Tenure into Formal Systems | en |

**Conséquence directe :** ces fiches ne transmettent rien de la matière du document. Le lecteur n'a aucune raison de télécharger le PDF. Pour les docs en espagnol et anglais, l'absence totale de traduction les rend inaccessibles à un public francophone.

**Cas particulier notable — `de3ff94a` (Community Land Trust Book) :** ce doc a score=9, il est probablement l'un des textes de référence sur les Community Land Trusts. C'est une fiche prioritaire à réparer : l'erreur d'enrichissement masque un document central pour le sujet.

---

## 3. Docs publiés hors-sujet éditorial

Le site se positionne sur "communs fonciers, paysannerie, propriété d'usage". Les 8 docs suivants ont un `relevance_score < 6` attribué par le pipeline lui-même :

### Clairement périphériques (score ≤ 3)

**`095f8db9` — *ZADissidences 3*** (relevance=3, score_final=6)  
Le pipeline dit lui-même : "ne traite pas réellement de la thématique." C'est un fanzine de ZAD sur la vie sociale interne, pas sur le foncier. Publié au seuil minimal (score 6). À reconsidérer.

### En zone grise (score = 5)

**`d992c836` — *Contre la légende et l'oubli*** (relevance=5, score=6)  
Touche la Confédération paysanne mais reste prioritairement un document commémoratif. Pertinence tangentielle.

**`073089a1` — *ZADissidences 2*** (relevance=5, score=6)  
Même problème que ZADissidences 3. La série ZADissidences semble mal seuillée dans le pipeline.

**`5ea1719f` — *ZADissidences*** (relevance=5, score=6)  
Idem. Les trois numéros de ZADissidences sont tous au score 5-6, tous au seuil. Soit on assume qu'ils appartiennent au corpus (les ZADs comme forme de commun foncier), soit on les exclut ensemble — mais la cohérence éditoriale demande une décision explicite.

**`bc522fd4` — *Ocupar e Lutar*** (relevance=5, score=6)  
Occupation urbaine au Portugal. Intéressant mais décalé : c'est de l'habitat squatté urbain, pas du commun foncier agricole ni rural.

**`41e09539` — *Qu'est-ce que la propriété ?*** (relevance=5, score=6)  
Proudhon. Le pipeline note une pertinence élevée en théorie mais l'extrait fourni ne portait pas sur le foncier. Cas à défendre ou à réévaluer sur un extrait plus représentatif.

**`f6ebd39c` — *In Defense — Such As It Is — of Usufructory Land Ownership*** (relevance=5, score=6)  
Traite frontalement la propriété d'usage (usufruit). Le score de 5 semble trop sévère — c'est probablement un faux hors-sujet. À réévaluer manuellement.

**`c0744b42` — *Some Social Remedies*** (relevance=5, score=6)  
Texte de réforme sociale abstracte, historique, peu opérationnel pour le sujet. Hors-sujet probable.

**Verdict global :** 5 docs sont clairement à la marge éditoriale (ZADissidences ×3, Ocupar e Lutar, Some Social Remedies). 2 sont probablement mal évalués par le pipeline (Proudhon, usufruit). La série ZADissidences demande une décision de politique éditoriale.

---

## 4. Cinq meilleures fiches — ce qui marche

Critères : qualité de contenu (résumé + en_clair + citations traduites), pertinence thématique, score final élevé.

### 1. `42750467` — *Struggle for the Land* (en, score=9, quality=85/100)
Texte documentant la réappropriation de terres par les Six Nations (Iroquois) au Canada en 2006. Fiche complète : résumé analytique riche, en_clair accessible, 10 citations toutes traduites en français. L'en_clair est exemplaire : il explique en deux phrases à qui s'adresse le document et quel geste politique il décrit. Manque : auteur non renseigné.

### 2. `dd858578` — *With the Peasants of Aragon* (en, score=9, quality=85/100)
Témoignage direct sur les collectifs agricoles anarchistes d'Aragon (1936-1939). 10 citations, toutes traduites. Le résumé pose le contexte historique, l'en_clair traduit l'enjeu pour un lecteur non-spécialiste ("en 1936-1939, les paysans pauvres et ouvriers agricoles d'Aragon ont choisi volontairement de mettre…"). Exemplaire sur la forme.

### 3. `2ab410d3` — *Radicaux urbains, paysans : la révolution anglaise* (fr, score=9, quality=85/100)
Texte sur les Diggers et les mouvements radicaux de la Révolution anglaise. Titre en français immédiatement lisible, résumé solide, en_clair percutant ("il y a 400 ans, les élites ont fermé les terres communes"), 5 citations en français. Parfaitement ancré dans le sujet communs/paysannerie.

### 4. `b4712d32` — *Agricultures libertaires DIY* (fr, score=8, quality=85/100)
Réflexion sur la place de l'agriculture dans les horizons révolutionnaires. Titre clair, résumé analytique précis, en_clair efficace, 10 citations. Bonne fiche thématiquement centrale.

### 5. `de8665e3` — *The Agricultural Collectives of Aragon* (en, score=8, quality=85/100)
Témoignage de Felix Carrasquer (CNT) sur les collectifs agricoles aragonais. 10 citations toutes traduites, résumé historiquement ancré, en_clair chiffré ("300 000 paysans espagnols ont géré en commun leurs terres, leurs récoltes…"). Le chiffrage dans l'en_clair est un excellent réflexe éditorial.

**Ce qui fait une bonne fiche ici :**
- Un résumé qui situe le document (qui écrit, pour qui, dans quel contexte)
- Un en_clair qui reformule le geste politique en une ou deux phrases
- Des citations toutes traduites pour les docs non-fr (aucune lacune partielle)
- Un titre humainement lisible qui n'oblige pas à ouvrir le PDF pour comprendre le sujet

---

## 5. Recommandations priorisées

### P0 — Blocages immédiats (fiches publiées mais vides ou invalides)

**R1. Réparer les 28 erreurs d'enrichissement.**  
29 % des fiches publiées ont un enrichissement en erreur. Pour les docs non-fr, cela signifie : pas de citations, pas d'en_clair, fiche inutilisable. Priorité absolue : `de3ff94a` (Community Land Trust Book, score=9), `8bfe460c` (Peasant Movement in Kwantung, score=9), les trois revues cubaines (score=9).

**R2. Corriger `d64f2d03` (Document HAL — hal-02485830).**  
Titre technique brut exposé publiquement. Le titre réel existe dans HAL, il faut le récupérer et écraser le champ.

**R3. Corriger `a91bd215` (Zapatiste 2014).**  
Ce n'est pas un titre, c'est un tag de veille. Trouver le titre réel du document.

### P1 — Lacune structurelle : auteurs

**R4. Pipeline : récupérer systématiquement l'auteur.**  
0 auteur sur 98 fiches est une lacune critique. Les docs FR (articles HAL, textes militants) ont souvent un auteur dans le PDF ou la source. Pour les pièces anonymes, afficher explicitement "Anonyme" ou "Collectif" — ne rien laisser vide.

### P2 — Couverture incomplète de l'en_clair

**R5. Générer l'en_clair pour les 55 fiches qui en sont dépourvues.**  
44 % des fiches ont un en_clair, 56 % n'en ont pas. L'en_clair est le seul élément qui rend le document accessible à un visiteur non-spécialiste. Il devrait être systématique.

### P3 — Titres illisibles

**R6. Traduire ou contextualiser les titres non-fr.**  
Convention recommandée : `Titre original (Traduction française)` — comme le fait déjà `e4f64264` : *Podłoże ruchu (Les fondements du mouvement)*. Appliquer ce modèle à tous les titres anglais/espagnol non traduits. Minimum : 30 titres concernés.

**R7. Renoncer au format "revue + numéro + date" comme titre.**  
Les trois revues cubaines (03b9d287, 35641d6d, dc1574ae) nécessitent un titre éditorial : extraire le titre de l'article principal, ou composer un titre descriptif du type "Combate (Cuba, 1959) — [thème principal]".

### P4 — Cohérence éditoriale

**R8. Décision explicite sur les ZADissidences (×3).**  
Les trois numéros sont tous au seuil (score 6, relevance 5). Soit on assume qu'ils appartiennent au corpus et on élève leur enrichissement pour le justifier, soit on les bascule dans les exclusions. Laisser trois fiches borderline sans décision n'est pas une posture éditoriale.

**R9. Réévaluer manuellement les 41 docs sans relevance_score.**  
42 % du corpus publié n'a jamais été évalué pour sa pertinence thématique. Ce sont des docs intégrés avant ou sans le pipeline de scoring éditorial. Parmi eux se trouvent probablement d'autres hors-sujets non détectés.

**R10. Introduire un champ `titre_fr` distinct du champ `title` pour les docs non-fr.**  
Le titre lisible pour le visiteur francophone ne devrait pas être le titre original brut. Séparer les deux champs permettrait d'afficher un titre accessible sans écraser la métadonnée originale.

---

## Synthèse

Le corpus est thématiquement solide sur son noyau dur : les meilleures fiches (Aragon, Six Nations, Diggers, Via Campesina) sont de bonne tenue documentaire. Deux problèmes systémiques dominent tout le reste :

1. **L'absence d'auteurs sur l'intégralité du corpus** — ce n'est pas une finition manquante, c'est une lacune de pipeline qui rend impossible toute navigation par auteur et retire une information de crédibilité essentielle.

2. **Les 28 erreurs d'enrichissement non traitées** — presque un tiers des fiches publiées sont des coquilles dont le résumé est parfois le seul contenu. Pour les docs non-francophones, c'est une impasse totale pour le lecteur.

Les problèmes de titres sont réels mais secondaires : ils nuisent à la découvrabilité, pas à la qualité intrinsèque du contenu quand il est présent.
