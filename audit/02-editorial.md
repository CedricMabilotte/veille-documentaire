# Audit 02 — Éditorial (qualité du contenu)

Date : 2026-05-18  
Méthode : lecture directe de `site/data/catalog.json` (234 docs) et des 17 fichiers `site/data/bulles/*.json`. Échantillonnage random + ciblé sur score ≥ 8.

---

## 1. Catalogue global

- Total : 234 docs.
- Distribution scores : 53 à 0, 87 à 1, 35 à 2, 5 à 3, 7 à 4, 14 à 5, 2 à 6, 5 à 7, **10 à 8, 13 à 9, 3 à 10**.
- Enrichis (résumé long IA) : 39 / 234 (17 %).
- Bulles éditoriales : 17 / 234 (7 %).
- Score ≥ 8 : 26 docs, dont seulement **5 enrichis** (5/26 = 19 %).

**Constat clé** : 21 docs scorés 8+ n'ont **pas** de résumé enrichi. Soit ils ne sont pas téléchargeables (la plupart sont des HTML d'actu Vía Campesina, EZLN, CLOC), soit le pipeline `enrich_pdf` ne couvre pas le HTML. Conséquence : sur le live, ces fiches affichent juste le titre + la raison du scoring, c'est très maigre.

## 2. Sondage 10 docs score ≥ 8 (cohérence titre / contenu)

Tirage `random.seed(11)` sur les 26 docs scorés ≥ 8.

| ID | Score | Titre (link_text tronqué) | Verdict cohérence |
|---|---|---|---|
| dc08f627 | 8 | "LOS SUEÑOS QUE COMPARTIMOS" PUELMAPU Encuentro… | **TANGENT** — événement zapatiste/Puelmapu, lien indirect avec « terres ». Score 8 surévalué. |
| 2a1339ce | 10 | Brasil: Movimiento de Pequeños Agricultores… | **OK** — sujet pile dans la thématique (MPA, soberanía alimentaria). |
| 06d72700 | 9 | 8 de marzo 2026 – Día Internacional… Mujeres Trabajadoras | **TANGENT** — c'est un appel à mobilisation femmes-travailleuses, le lien « reforma agraria » apparaît dans la *raison* mais reste périphérique. Score 9 trop élevé. |
| 5bc070cc | 9 | CIRADR+20 debe ir más allá… reforma agraria | **OK** — pile thématique. |
| ff465ab4 | 8 | La UNDROP como escudo para los pueblos pescadores | **OK** — pêcheurs comme paysans de la mer, UNDROP. |
| ae3e9d34 | 9 | Irlanda: una crisis de gobernanza, no una crisis de combustible | **HORS-SUJET** — il s'agit en réalité d'un éditorial sur la crise du carburant en Irlande. La *raison* du scoring dit que « MST Brasil » et « 450 000 familles » apparaissent dans le contexte, mais le doc n'est pas sur la thématique. Erreur de scoring nette. |
| 97c3bbb4 | 9 | Le community land ownership écossais | **EXCELLENT** — pile cœur, enrichi, bulle. |
| 0b22d51b | 8 | Communs fonciers en conflit au Mexique : les ejidos | **EXCELLENT** — pile cœur. |
| 6a3a9d73 | 8 | #17Abril – Unidxs contra el imperialismo… | **OK** — Día Internacional Luchas Campesinas. |
| 141ead94 | 8 | Sexta Sesión… Semillero Abril 2026 Zapatistas | **TANGENT** — annonce de session en ligne, peu de contenu thématique propre. |

**Bilan** : sur 10 docs sondés, **6 OK, 3 tangents, 1 hors-sujet manifeste**. Précision du scoring sur la cohorte 8+ ≈ 60–70 %. C'est correct pour un pipeline IA, mais les hors-sujets ressortent en haut du classement (`sort=score-desc`) ce qui dégrade la première impression.

## 3. Cohérence enrichment ↔ citations

Sondage des 5 docs enrichis score ≥ 8 :

- **d647480f** (Coriat) — score 9, rel_score 6, 7 citations, 16 keywords. Citations vérifiées présentes textuellement dans l'extrait du PDF (échantillon vérifié `« substractability »` p. 5). Résumé fidèle.
- **e5341cc9** (Coriat, doublon partiel) — score 9, rel_score 8, 10 citations. **Quasi-doublon de d647480f** : même auteur, même thèse, deux versions HAL (hal-03366910 et hal-03380720). Le pipeline n'a pas détecté le doublon. Action : merge ou flag.
- **0b22d51b** (Redouté, ejidos Mexique) — score 8, rel_score 8, 10 citations, 23 keywords. Résumé fidèle, citations cohérentes.
- **97c3bbb4** (Deconchat, Ulva) — score 9, rel_score 8, 10 citations, 16 keywords. Excellent.
- **1b61c156** (Déjacque, "À bas les chefs") — résumé honnête mais le doc lui-même est noté score 2 / rel_score 2 (« faux ami thématique »), or il reste dans le catalogue. Pas de problème éditorial, juste un déchet de veille.

**Cohérence interne très solide** sur les 5 enrichis.

## 4. Sondage des 5 bulles les mieux notées

Bulles classées par `latest_score`, top 5 :

### d647480f (score 9) — Communs fonciers / Coriat
- `titre_accroche` : « Propriété dissociée : quand les terres échappent à la logique marchande » → **fidèle**, capte l'angle Coriat (distribution des droits ≠ nature du bien).
- `teaser` : « Qu'est-ce qui fait vraiment un commun foncier ? […] Pas une nature de bien, ni l'absence de propriété privée : c'est avant tout une question de droits. » → **accrocheur ET fidèle**.
- `abstract_editorial` : développe en 4-5 paragraphes, cohérent.
- 3 citations phares avec n° de page → vérifiables.
**Verdict : excellente bulle.**

### e5341cc9 (score 9) — Coriat (variante)
- `titre_accroche` : « De la terre aux données : penser les communs autrement ». OK.
- `teaser` : « Osez repenser la propriété. Benjamin Coriat nous offre une grille théorique rigoureuse… ». Accrocheur, fidèle.
- **Problème** : doublon avec d647480f. Deux bulles éditoriales pour le même contenu (le pipeline a publié deux versions HAL du même article). À fusionner.

### 97c3bbb4 (score 9) — Ulva / Écosse
- `titre_accroche` : « Ulva : quand l'État devient partenaire des communs fonciers ». **Excellent**.
- `teaser` : « En Écosse, le community land ownership redessine les règles du jeu foncier : une véritable troisième voie ou l'État qui contrôle les clés ? ». Accroche posant une vraie question. Fidèle au papier.
- `abstract` : développe `Scottish Land Fund`, Ulva 2018, mouvement depuis 80s. Cohérent.
**Verdict : excellente bulle.**

### 0b22d51b (score 8) — Ejidos / Mexique
- `titre_accroche` : « Ejidos mexicains : quand la terre devient marchandise ». Fidèle.
- `teaser` : pose la tension propriété collective / marché global. Bon.
- `abstract` : « Au cœur de la paysannerie mexicaine… ». Fidèle au papier Redouté.
**Verdict : excellente bulle.**

### 2db11a52 (score 5) — Chaire VALCOM
- `titre_accroche` : « Les communs fonciers : une autre histoire de la terre ». OK.
- `teaser` : présente VALCOM, accroche correcte.
- **Étrange** : score brut = 5, mais bulle publiée (théoriquement réservée aux 9–10). Probablement re-scoring à la baisse après publication de bulle. Politique de cohérence à fixer : si re-scoring abaisse en dessous d'un seuil, dépublier la bulle ou la signaler.

## 5. Trois fiches les plus problématiques

### Fiche 1 — `e4180dc7` (`medical_records_50_anthem_blue_cross_medicare.pdf`)
- Source : « Archive.org — commons / enclosure ».
- Score : 0 (catalog) — pas trompeur éditorialement, mais **bruit** sourcing : un dump de dossiers médicaux Anthem Blue Cross indexé par Archive.org sous un mot-clé « commons » homonyme. **HTTP 401** en plus côté source. À purger du catalog.

### Fiche 2 — `ae3e9d34` (score 9 — « Irlanda: una crisis de gobernanza, no una crisis de combustible »)
- Hors-sujet manifeste, score 9 erroné. La *raison* invoque des mots-clés trouvés dans le contexte (« MST Brasil », « 450 000 familias ») qui sont en réalité des liens latéraux dans la barre latérale du site source — pas le contenu de l'article. **Faux positif typique d'un scoring sur HTML mal segmenté.** À re-scorer ou flagger.

### Fiche 3 — Doublon `d647480f` / `e5341cc9`
- Même auteur (Coriat), même thèse, deux versions HAL. Deux bulles publiées. Sur la page d'accueil ils apparaissent côte à côte dans « À la une » → impression de redondance / d'erreur éditoriale. Action : déduplication par titre + auteur + DOI/HAL canonique.

## Recommandations éditoriales prioritaires

1. **Re-scoring HTML** : isoler le contenu principal (`<article>`, `<main>`) avant de scorer ; ne pas scorer sur barre latérale / footer / liens latéraux. C'est la cause racine des faux positifs Vía Campesina / cnt.es / Enlace Zapatista.
2. **Dédup auteur + titre canonique** sur les sources HAL (versions multiples du même papier).
3. **Politique de bulle vs score** : verrouiller la bulle après publication, ou la dépublier si rescore < 7.
4. **Filtrage source Archive.org** : la requête « commons » remonte trop de bruit homonyme. Restreindre par `subject:` ou collection.
5. **Pipeline d'enrichissement étendu au HTML** : 80 % du catalog (HTML) n'a pas de résumé long, donc 80 % des fiches sont creuses.
