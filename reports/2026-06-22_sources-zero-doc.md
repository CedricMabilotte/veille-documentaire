# Diagnostic sources à 0 document — 2026-06-22

Contexte : ~24 sources configurées dans `config/sources.yml` remontaient 0 document
au catalogue (`synopsis/catalog.json`). Ce rapport identifie la cause par source,
documente ce qui a été corrigé, et liste les décisions en attente pour Ced.

---

## Méthode d'investigation

1. Lecture du `throttle_state.json` pour voir le code HTTP synthétique (200 = docs
   trouvés, 204 = 0 doc) et le nombre de tentatives échouées.
2. Tests curl directs (`-L`, User-Agent LibraryBot) pour distinguer les vrais codes
   HTTP des codes synthétiques.
3. Exécution des parsers en mode test (`python3 -c "from parsers.deep_html import
   find_documents; ..."`) pour isoler le comportement réel.
4. Analyse du HTML de chaque source pour identifier la structure (JS dynamique,
   PDFs hors-domaine, pages de taxonomie, contenu éditorial sans PDF).

---

## Catégorie 1 — Sources RSS : comportement attendu (0 doc catalog = normal)

Ces sources sont configurées en `type: rss`. Elles renvoient des articles HTML,
jamais des liens PDF directs. Le pipeline les enregistre dans `candidates.yml`
(découverte) mais `_is_ouvrage_doc()` les filtre avant le catalogue : extension
`html` n'est pas dans `OUVRAGE_EXTENSIONS`. Ce comportement est voulu et documenté
dans `sources.yml` (commentaire « NB sur les RSS hispanophones »).

| Source | URL | Statut HTTP | Items trouvés | Cause 0 doc |
|---|---|---|---|---|
| GRAIN — entries RSS | grain.org/home/entries.rss | 200 | 10+ articles | RSS articles HTML |
| Lundi.am — RSS | lundi.am/spip.php?page=backend | 200 | 10 articles | RSS articles HTML |
| Reporterre — RSS | reporterre.net/spip.php?page=backend | 200 | 30 articles | RSS articles HTML |
| Sin Permiso | sinpermiso.info/rss.xml | 200 | 10 articles | RSS articles HTML |
| CNT-AIT España | cnt.es/feed/ | 200 | 10 articles | RSS articles HTML |
| Portal OACA — RSS | portaloaca.com/feed/ | 200 | 10 articles | RSS articles HTML |
| CGT España — RSS | cgt.org.es/feed/ | 200 | 10 articles | RSS articles HTML |
| Enlace Zapatista | enlacezapatista.ezln.org.mx/feed/ | 200 | 20 articles | RSS articles HTML |
| La Via Campesina ES | viacampesina.org/es/feed/ | 200 | 10 articles | RSS articles HTML |
| CLOC — Via Campesina | cloc-viacampesina.net/feed/ | 200 | 10 articles | RSS articles HTML |
| FIAN International ES | fian.org/es/feed/ | 200 | 10 articles | RSS articles HTML |
| Cultural Survival — RSS | culturalsurvival.org/rss.xml | 200 | 10 articles | RSS articles HTML |
| ENDA Tiers Monde — RSS | endatiersmonde.org/feed/ | 200 | 10 articles | RSS articles HTML |
| CEIPAZ — RSS | ceipaz.org/feed/ | 200 | 10 articles | RSS articles HTML |
| CELAG — RSS | celag.org/feed/ | 200 | 10 articles | RSS articles HTML |
| MST Brésil — RSS | mst.org.br/feed/ | 200 | 10 articles | RSS articles HTML |

**Action requise : aucune.** Ces sources fonctionnent comme prévu. Elles enrichissent
`candidates.yml` (pistes de découverte). Si on veut des PDFs de ces organisations,
il faut ajouter des sources `deep_html` pointant vers leurs bibliothèques de
publications (ex : GRAIN a une section « publications » sur son site).

---

## Catégorie 2 — Bugs corrigés dans cette session

### 2.1 — `deep_html` : les pages de taxonomie consommaient les slots de crawl

**Bug.** `_find_article_links()` ne filtrait pas les URLs de catégories (`/categoria/`,
`tag:XXX`, etc.). Sur des sites comme Troisièmes Voix (Grav, URLs `tag:Communs`) ou
Portal OACA (WordPress, URLs `/categoria/...`), ces pages de taxonomie étaient crawlées
en priorité, consommant tous les `max_pages` avant d'atteindre les vraies pages-articles
contenant des PDFs.

- **Troisièmes Voix** : 17 des 25 liens de la page d'index étaient des `tag:XXX` →
  les 5 pages d'éditions avec PDFs jamais crawlées → **0 doc**.
- **Portal OACA Libros** : 34 des 53 liens étaient des `/categoria/...` →
  les 12 pages de livres en position 34+ jamais atteintes avec `max_pages=15` → **0 doc**.

**Correction** (`scripts/parsers/deep_html.py`, commit `1e35db3`).
Blacklist de `_find_article_links` étendue aux patterns :
`tag:`, `category:`, `categor[íi]a:`, `/categoria/`, `/categor[íi]a/`, `/tags?/`,
`/etiqueta/` (EN + ES, forme brute et encodée `%3A`).

**Tests post-fix :**
- Troisièmes Voix `/fr` → **5 PDFs trouvés** (Mini-Manuels éditions 001–005)
- Portal OACA `/categoria/pensamientolibertario/libros-anarquistas/` → **8 PDFs trouvés**
  (hébergés sur domaines tiers : solidaridadobrera.org, editorialautodidacta.com)

### 2.2 — Böll Stiftung Agriculture & Food EN : URL 404

**Bug.** URL `https://www.boell.de/en/topics/agriculture-food` retourne HTTP 404.
Le throttle_state enregistrait 5 tentatives échouées, code 204 synthétique.

**Correction** (`config/sources.yml`). URL remplacée par
`https://www.boell.de/en/topics/agriculture` (HTTP 200 confirmé, **43 PDFs trouvés**
au test deep_html).

### 2.3 — CrimethInc : mauvaise page d'entrée

**Bug.** `https://crimethinc.com/library` liste des articles sans aucun PDF.
La page elle-même indique que les PDFs sont sur `/tools` puis `/zines`.

**Correction** (`config/sources.yml`). URL changée vers
`https://crimethinc.com/zines` + label renommé `CrimethInc — zines`.
Les PDFs sont hébergés sur le sous-domaine `cdn.crimethinc.com` (cross-sous-domaine) ;
`_extract_docs` les capture sans filtrage de domaine. **5 PDFs trouvés au test**
(fonctionne, scoring à vérifier au prochain run).

---

## Catégorie 3 — Sources irrécupérables sans JS

### 3.1 — MST Brésil — biblioteca questão agraria

**Cause.** La page `https://mst.org.br/biblioteca-da-questao-agraria/` charge son
catalogue via DataTables JS avec appels AJAX WordPress. Le HTML statique affiche
uniquement « Sem resultados ». Aucun lien PDF dans le DOM initial.
Ni `deep_html` ni `playwright` (sans JS execution) ne peuvent lire ce contenu.

**Action prise.** Source commentée dans `sources.yml` avec note explicative.

**Décision pour Ced.** Chercher si le MST expose une API REST WP ou un CSV des
publications. Sinon, la bibliothèque est accessible manuellement mais pas crawlable
sans Playwright + JS execution.

---

## Catégorie 4 — Sources fonctionnelles mais rendement nul attendu

### 4.1 — TNI — Land & Food topic

**Cause.** `https://www.tni.org/en/topic/land-food` retourne HTTP 429
(rate-limiting agressif) à chaque tentative — même avec délai entre appels.
5 tentatives échouées dans le throttle_state.

**Action prise.** `min_interval_days` augmenté de 14 à 30 dans `sources.yml`.
Note de diagnostic ajoutée.

**Décision pour Ced.** Garder en observation. Si le 429 persiste après 30 jours,
envisager de retirer la source ou de chercher un miroir / flux RSS TNI.

### 4.2 — JSTOR Daily — topic land

**Cause.** JSTOR Daily est un magazine d'articles en ligne, pas une bibliothèque.
La page `/topic/land/` ne contient aucun PDF sur l'index ni sur les sous-pages.
0 doc = comportement structurellement attendu.

**Action prise.** Note ajoutée dans `sources.yml`.

**Décision pour Ced.** Retirer la source ou la remplacer par un flux RSS JSTOR Daily
(s'il existe) pour alimenter uniquement `candidates.yml`.

### 4.3 — Tierra.org — Agricultura et Biodiversidad

**Cause.** Les rubriques d'actualités de Tierra.org contiennent quelques PDFs
(2–3 trouvés), mais il s'agit de documents **institutionnels internes** (protocoles RH,
rapports de gestion interne) — hors-sujet éditorial. Les rapports thématiques
pertinents ne sont pas listés dans ces rubriques d'actualités.

**Action prise.** Note ajoutée dans `sources.yml`.

**Décision pour Ced.** Explorer si Tierra.org a une section « publicaciones » ou
« informes » dédiée aux rapports sur la souveraineté alimentaire et la biodiversité
agricole. Les deux URLs actuelles (`/01agricultura-y-alimentacion/02actualidad-…`
et `/06_biodiversidad/02actualidad-…`) ne sont pas les bons points d'entrée.

### 4.4 — Portal OACA — Libros anarquistas

**Cause partielle corrigée.** Après le fix `deep_html` (§2.1), Portal OACA trouve
maintenant 8 PDFs au test. Cependant, les livres thématiques (agroécologie, paysannerie,
communs fonciers) sont probablement rares dans ce corpus anarchiste généraliste.
Le scoring sur titre (`score_initial`) risque de rester bas.

**Action.** Aucune supplémentaire — la source est maintenant fonctionnelle.
Les docs trouveront leur chemin si leurs titres sont suffisamment thématiques.

---

## Résumé des commits de session

| Commit | Fichier | Contenu |
|---|---|---|
| `1e35db3` | `scripts/parsers/deep_html.py` | Fix blacklist `_find_article_links` : filtrer `/categoria/`, `tag:`, etc. |
| `8ada5ac`* | `config/sources.yml` | Böll URL 404→200, CrimethInc /library→/zines, MST commenté, notes TNI/JSTOR/Tierra/Portal OACA |

*`8ada5ac` est un commit de session antérieur (même journée) qui embarquait déjà
les corrections de `sources.yml` ainsi que l'ajout des `default_lang`.

---

## Décisions en attente pour Ced

1. **MST Brésil biblioteca** — chercher API REST WP ou CSV. Sinon accepter la perte
   de cette source (le RSS fonctionne pour la découverte).
2. **TNI** — observer les prochains runs. Si 429 persiste, retirer ou chercher
   un autre point d'entrée TNI (ils ont un fil RSS publications).
3. **JSTOR Daily** — retirer ou convertir en `type: rss` (chercher leur feed RSS).
4. **Tierra.org** — trouver la rubrique « publicaciones/informes » plutôt que
   les rubriques d'actualités.
5. **Portal OACA** — après quelques runs, vérifier si des docs atteignent le
   seuil de scoring. Si 0 doc publié après 3 mois, reconsidérer.
6. **Sources RSS à forte thématique** (GRAIN, FIAN, TNI RSS si trouvé) — envisager
   d'ajouter des sources `deep_html` pointant vers leurs bibliothèques de rapports
   PDF, en complément des RSS qui ne peuvent qu'alimenter `candidates.yml`.
