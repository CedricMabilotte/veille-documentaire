# Diagnostic d'angles morts — 2026-10-01 10:23 UTC

Catalog : **2061** docs.

## Stats de couverture

- Par langue : `{'fr': 1168, 'unknown': 797, 'en': 57, 'es': 36, 'de': 2, 'pt': 1}`
- Par décennie : `{'1800s': 2, '1810s': 1, '1820s': 2, '1830s': 6, '1840s': 8, '1850s': 7, '1860s': 5, '1870s': 4, '1880s': 5, '1890s': 6, '1900s': 9, '1910s': 9, '1920s': 12, '1930s': 15, '1940s': 6, '1950s': 11, '1960s': 25, '1970s': 24, '1980s': 47, '1990s': 52, '2000s': 125, '2010s': 311, '2020s': 334, '2030s': 1, '2050s': 1}`
- Sources stériles (≥3 scans, 0 doc ≥7) : ['Archive.org — anarchism + land/peasant (strict)', 'Archive.org — commons / enclosure', 'Archive.org — peasant movements', 'Archive.org — subject:anarchism (texts)', 'Böll Stiftung — Agriculture & Food (EN topic)', 'Böll Stiftung — publications DE', 'Böll Stiftung — publications DE (deep crawl)', 'CLACSO Libros (acceso abierto)', 'CLACSO — Libros en coedición', 'CLACSO — Publicaciones générales', 'CLACSO — búsqueda tierra y communs', 'CrimethInc — zines', 'Infokiosques.net — Anticolonialismes', "Infokiosques.net — Squat (rapport à l'habiter)", 'Infokiosques.net — index A', 'Infokiosques.net — index C', 'Infokiosques.net — index L (Libération, Luttes)', 'Infokiosques.net — nouveautés', 'Infokiosques.net — Écologie radicale', 'Portal OACA — Libros anarquistas (catégorie)', 'Tierra.org (Amigos de la Tierra ES)', 'Traficantes de Sueños — 15M (matière)']

## Synthèse

Le catalogue couvre bien la littérature grise francophone & latino-américaine activiste (1168 fr + 245 sources span ES/PT), mais souffre de concentration excessive (>50% en 4 sources) et de déficits majeurs : anglais (2,8%), portugais (1 doc), couverture autochtone quasi-nulle, histoire pré-1950 marginale (5%), et 38% des docs restent 'unknown' linguistiquement. Les sources stériles révèlent des hypothèses mal calibrées (Archive.org requêtes génériques, CLACSO manqué, Böll Stiftung hors-champ). Priorités : (1) diversifier EN/PT via CLT-Network, Landesa, INCRA, universidades brésiliennes, (2) rapatrier mouvements autochtones (native-land.ca, UNPFII), (3) rouvrir histoire longue par recalibrage Archive.org + HathiTrust, (4) réinvestir Afrique (CODESRIA, TWN), (5) nettoyer sources stériles & exploiter HAL français mieux.

### Angle mort 1 — langue (high)

Couverture anglophone gravement déficitaire : 57 docs EN (2,8%) vs attente ~25% pour langue déclarée. Cela exclut littérature majeure sur CLT (Community Land Trusts), land rights anglo-saxonnes, Ostrom/commons theory en EN

**Sources suggérées :**
- `html/api` — https://www.cltweb.org/ + api publications → Réseau CLT USA = expertise opérationnelle sur propriété collective du sol; peu exploité dans catalogue
- `rss/api` — https://www.landesa.org/knowledge-base/ (RSS ou JSON API) → Think tank international reconnu sur land rights & policy; couverture globale manquante en EN
- `api` — Cambridge Repository + JSTOR (requête 'commons land housing') → Littérature académique EN sur théorie des communs et cas d'étude

### Angle mort 2 — langue (high)

Couverture lusophone quasi-inexistante : 1 seul doc PT déclaré, mais 209 docs MST Brésil (probable classification en 'unknown'). Manque accès Brésil, Portugal, pays lusophones — régions centrales pour paysannerie & coopératives

**Sources suggérées :**
- `html/scrape` — https://www.incra.gov.br/pt-br/publicacoes (scrape ou RSS) → INCRA (réforme agraire Brésil) = source gouvernementale directe, non encore exploitée
- `oai-pmh/api` — Repositório Institucional UNICAMP + USP (OAI-PMH ou API) → Université brésiliennes = littérature lusophone sur terra, movimentos rurais, agroécologie
- `api/html` — https://www.fao.org/faostat/pt/ + publications FAO PT → Données agraires officielles & rapports politiques en portugais

### Angle mort 3 — thème (high)

Mouvements autochtones & Land Back = concept central déclaré mais quasi-absent en sources tangibles. Littérature anglophone (First Nations, Indigenous sovereignty, reclamos indígenas) manquante

**Sources suggérées :**
- `api` — https://native-land.ca/api/ (données + ressources) → Base de données cartographique + archives sur territoires autochtones; couverture mondiale
- `html/pdf` — https://www.un.org/development/desa/indigenouspeoples/documents.html (UNPFII publications) → Institutions ONU = rapports officiels sur land rights autochtones, multilangues
- `html` — First Nations Information Governance Centre (Canada) — publications & data → Source nord-américaine structurée sur gouvernance territoriale autochtone

### Angle mort 4 — période (high)

Couverture historique pré-1950 très limitée : ~112 docs (5%) avant 1950. Grave lacune pour comprendre enclosure, mouvements paysans historiques, réformes agraires du XXe, contexte long des communs

**Sources suggérées :**
- `api/scrape` — Archive.org + date:1800-1950 (requête historique ciblée : 'peasant movement' OR 'land reform' OR 'commoning') → Reciblage Archive.org avec contrainte temporelle; actuelle requête 'anarchism+land' probablement trop bruitée
- `oai-pmh` — HathiTrust Digital Library (oai.cdlib.org) — French & Spanish land/peasant materials pre-1950 → Corpus numérisé massif de périodiques & monographies historiques français/espagnols
- `api` — Institut de l'Histoire de la Révolution Française (IHRF) — Gallica API → Collections spécialisées sur histoire agraire révolutionnaire & XIXe rural français

### Angle mort 5 — géographie (medium)

Concentration extrême : La Vía Campesina (27%) + MST Brésil (10%) = 37% du total. Couverture Afrique, Asie, Moyen-Orient pratiquement absente; sous-représentation Europe centrale & Sud

**Sources suggérées :**
- `rss/api` — https://www.codesria.org/index.php/publications (RSS / JSON API) → Conseil pour le développement de la recherche en Afrique = littérature majeure sur communs fonciers africains, droit coutumier, mouvements paysans subsahariens
- `html/rss` — Third World Network (TWN) — publications + archives (https://twn.my/) → Coordination Sud Global sur land rights, agrarian movements; couverture Asie + Afrique peu exploitée
- `html` — Rural Advancement Foundation International (RAFI) → ETC Group publications → Expertise semences, agrobiodiversité, droit des paysans (Colombie, Inde, Philippines)

### Angle mort 6 — format/diversité_sources (medium)

38% des docs classés 'unknown' (797 docs) masque réalité couverture linguistique & thématique. Concentration excessive sur 4 sources (>50% du total); manque diversité : universités, journalisme enquête, archives gouvernementales numérisées

**Sources suggérées :**
- `oai-pmh/api` — HAL (Hyper Articles en Ligne) — requête affinée 'commons fonciers' + 'agriculture paysanne' + 'habitat coopératif' → Archive ouverte française/francophone = thèses & rapports de recherche; HAL listée mais peu exploitée (4-1 docs)
- `api` — Europeana + Europeana Pro (données patrimoniales + sources primaires sur histoire agraire européenne) → Corpus numériques décentralisé = archives régionales sur communs, Allmende, coopératives historiques
- `oai-pmh/api` — Agraria.org (réseau recherche agroécologie italie) + universités méditerranéennes (OAI-PMH) → Couverture Europe du Sud (Italie, Espagne, Grèce) sur histoire agraire & mouvements contemporains

## Verdict sources stériles

- **Archive.org — anarchism + land/peasant (strict)** → `drop` (Requête trop générale & mal calibrée; bruit anarchiste noie contenu foncier réel. Remplacer par requêtes temporelles + thématiques ciblées ('enclosure 1750-1850', 'peasant resistance 1800-2000'))
- **CLACSO Libros (acceso abierto) + CLACSO — tous indices** → `drop` (4 requêtes différentes, 0 docs retournés après 3+ scans. Plateforme probablement hors-champ ou requêtes mal formulées pour CLACSO. Chercher plutôt par thèses individuelles)
- **Böll Stiftung — publications DE, Agriculture & Food (EN), deep crawl** → `review` (3 tentatives stériles; hypothèse : Böll Stiftung a couverture environnement/genre, pas foncier paysan. Investiguer si thématique 'communs fonciers' existe chez Böll ou si autre fondation allemande mieux ciblée (Rosa Luxemburg, Boell alternative))
- **Infokiosques.net — Anticolonialismes, Squat, index A/C/L, Écologie radicale** → `review` (Plusieurs index stériles mais 'Paysannerie & ruralité' retourne 46 docs. Garder la requête productive, investiguer si index non-productifs sont hors-scope réel ou mal formulés)
- **CrimethInc — zines** → `drop` (Zines anarchistes/antimilitaristes stérile; hors-champ probable pour communs fonciers institutionnels & théorie académique)
- **Portal OACA — Libros anarquistas (catégorie)** → `drop` (Focus anarchisme littéraire; chevauchement avec Archive.org + CrimethInc. Bruit trop élevé pour ROI)
- **Tierra.org (Amigos de la Tierra ES)** → `review` (Environnement ES, pas forcément foncier paysan. Investiguer si requête était 'terre/land' générique ou si 'communs fonciers' n'existe pas dans thématique Amigos)