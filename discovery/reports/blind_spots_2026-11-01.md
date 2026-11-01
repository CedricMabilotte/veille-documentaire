# Diagnostic d'angles morts — 2026-11-01 10:30 UTC

Catalog : **2251** docs.

## Stats de couverture

- Par langue : `{'fr': 1209, 'unknown': 933, 'en': 70, 'es': 36, 'de': 2, 'pt': 1}`
- Par décennie : `{'1800s': 2, '1810s': 1, '1820s': 2, '1830s': 6, '1840s': 9, '1850s': 8, '1860s': 5, '1870s': 4, '1880s': 5, '1890s': 7, '1900s': 9, '1910s': 9, '1920s': 13, '1930s': 16, '1940s': 8, '1950s': 12, '1960s': 27, '1970s': 26, '1980s': 50, '1990s': 55, '2000s': 128, '2010s': 319, '2020s': 338, '2030s': 1, '2050s': 1}`
- Sources stériles (≥3 scans, 0 doc ≥7) : ['Archive.org — anarchism + land/peasant (strict)', 'Archive.org — commons / enclosure', 'Archive.org — peasant movements', 'Archive.org — subject:anarchism (texts)', 'Böll Stiftung — Agriculture & Food (EN topic)', 'Böll Stiftung — publications DE', 'Böll Stiftung — publications DE (deep crawl)', 'CLACSO Libros (acceso abierto)', 'CLACSO — Libros en coedición', 'CLACSO — Publicaciones générales', 'CLACSO — búsqueda tierra y communs', 'CrimethInc — zines', 'Infokiosques.net — Anticolonialismes', "Infokiosques.net — Squat (rapport à l'habiter)", 'Infokiosques.net — index A', 'Infokiosques.net — index C', 'Infokiosques.net — index L (Libération, Luttes)', 'Infokiosques.net — nouveautés', 'Infokiosques.net — Écologie radicale', 'Portal OACA — Libros anarquistas (catégorie)', 'Tierra.org (Amigos de la Tierra ES)', 'Traficantes de Sueños — 15M (matière)']

## Synthèse

Catalogue dominé français (54%) + latino-américain (La Vía Campesina 559, MST 209, CLACSO), avec 41% docs UNKNOWN masquant vraies lacunes linguistiques. Trois failles graves : anglais critique (3%), Afrique subsaharienne + autochtones absents, Asie du Sud/SE inexistante. Féminisme agraire et habitat collectif urbain sous-documentés malgré pertinence centrale. Sources stériles (16) pas dû absence pertinence, mais requêtes trop générales (CLACSO paradoxalement stérile = opportunité relance API) ou couverture déjà suffisante (Böll, radicalismes). Actions immédiatement productives : (1) reclassifier 933 docs UNKNOWN (priorité 1), (2) ajouter Landesa + RRI + GRAIN + PANLAC anglophone, (3) relancer CLACSO + Archive.org avec requêtes spécifiques, (4) approfondir féminisme agraire (AWID, Rosa Lux).

### Angle mort 1 — langue (high)

Anglais 3.1% (70 docs) vs projet multilingue; 933 docs (41%) classés UNKNOWN masquent vraies lacunes; PT quasi absent (0.04%) malgré source MST Brésil 209 docs (probablement mislassifiés). Faille critique : littérature anglophone (monde anglo-saxon, sciences sociales EN) et contenu lusophone (Brésil, Mozambique).

**Sources suggérées :**
- `html` — https://www.landesa.org/our-work/publications/ — Landesa Library → Leader droits fonciers global; 100+ publications EN/ES/FR; pays-fiches; couvrira faille anglophone immédiate sur foncier
- `rss` — https://www.grain.org/en/ + RSS https://www.grain.org/feed/en → GRAIN : paysannerie + agroécologie multilingue (EN/ES/FR/PT); bulletins trimestriels; comblera EN + PT lusophone
- `html` — https://foodfirst.org/publications/ — Food First (IFDP EN/ES) → 50 ans mouvements paysans + réforme agraire; publications accès libre; contenu EN/ES manquant

### Angle mort 2 — géographie (high)

Afrique subsaharienne : 0 source majeure alors que 'Communs africains & foncier coutumier' est concept central. Mouvements autochtones (Land Back) : aucune couverture structurée. Asie (Sud/SE) absente : zéro source Inde, Indonésie, Bangladesh = vides sur terrains majeurs mouvements paysans.

**Sources suggérées :**
- `html` — https://rightsandresources.org/publications/ — RRI (Rights & Resources Initiative) → Spécialiste droits fonciers autochtones + communs; 50+ pays couverts; comblera gap Afrique + mouvements Land Back
- `api` — https://www.panlac.org/ ou accès API — Pan African Land Coalition → Réseau panafricain 37 organisations; publications pays/sous-région; comblera faille Afrique subsaharienne directement
- `html` — https://focusweb.org/publications/ — Focus on the Global South → Based Bangkok; couverture Asie du Sud/SE sur terre, agroécologie, paysannerie; comblera faille Asie du Sud/SE

### Angle mort 3 — thème (medium)

Féminisme agraire & paysan : concept central mais source Archive.org dédiée = 2 docs seulement. Habitat collectif urbain/coopératives : une source (CLT) avec 25 docs, probablement sous-exploitée. Mutualisme foncier + coopératives non-agricoles : quasi absent.

**Sources suggérées :**
- `html` — https://www.awid.org/ — AWID Resources (Association Women's Rights in Development) → ONG féministe; dossiers terre + genre + paysannerie; couvrira faille féminisme agraire + paysan
- `html` — https://www.rosalux.de/en/publications/ — Rosa Luxemburg Stiftung (Land + Gender) → Fondation mouvement; publications intersectionnelles genre/terre/commune; comblera théorie + pratiques féminisme paysan
- `html` — https://www.fian.org/resources — FIAN International (Food & Land Justice) → ONG justice foncière; couvre féminisme + habitat collectif + souveraineté alimentaire; comblera habitat urbain + coopératives

### Angle mort 4 — période (low)

Pré-2000 : 350 docs (15.5%) vs 2010-2020s : 657 docs (29%). Or, enclosures (XVIIe-XIXe) + mouvements anarchistes paysans (XIXe-début XXe) sont contexte théorique central. Faible couverture historique mouvements agraires 1800-1950.

**Sources suggérées :**
- `html` — https://www.hathitrust.org/ — HathiTrust Digital Library (recherche avancée : 'peasant movements' OR 'agrarian history' 1800-1950) → 10M+ livres numérisés public domain; couverture XIXe-XXe siècles anarchisme agraire, mouvements paysans, foncier historique
- `html` — https://persee.fr/ — Persée (histoire agraire France + Europe 1800-1950) → Revues scientifiques en accès libre; articles histoire communs, enclosures, coopératives agricoles; approfondissement contexte européen

### Angle mort 5 — source / filtrage (medium)

16 sources stériles (≥3 scans, 0 doc). Anomalie majeure : CLACSO (paradoxal = réseau académique AL très pertinent pour foncier) retourne 0 doc. Archive.org réussit requêtes précises (CLT 25 docs, Federici 2) mais échoue sur génériques. Problème d'extraction/filtrage, pas de pertinence fondamentale.

**Sources suggérées :**
- `api` — API CLACSO — https://biblioteca-virtual.clacso.org.ar/ → CLACSO stérile = requête initiale trop générale/mal formulée. Relancer avec : 'tierra común', 'reforma agraria', 'movimientos campesinos'. Réseau 70+ instituts = potentiel très haut restauration.
- `html` — Archive.org — requêtes ciblées remplaçant généralités (abandonner 'anarchism', 'peasant movements'; lancer 'community land trusts', 'commons enclosure 1500-1850', 'cooperative housing') → Archive.org ROI inversement proportionnel à généralité requête. Réussit spécifique (CLT, Federici), échoue générique. Rebudgétiser requêtes = gain immédiat.

### Angle mort 6 — classification / couverture (high)

933 docs (41.4%) classés UNKNOWN : ratio catastrophique. Révèle soit bug détection langue (script TextCat/langdetect défaillant) soit volume mélange multilingue non-analysé. Impact : impossible diagnostiquer vraies lacunes linguistiques sous ce brouillard; vraie répartition EN/ES/PT inconnue.

**Sources suggérées :**
- `other` — Audit + réexécution détection langue (langdetect Python, ou Hugging Face transformers small multilingual) → 933 'unknown' masquent vraies failles. Reclassifier réduira incertitude, révèlera ex. vraie couverture PT (peut-être 5% hidden), comblera lacunes avec priorités justes. Priorité 1 avant ajouter sources.

## Verdict sources stériles

- **CLACSO Libros (acceso abierto)** → `review` (Paradoxe sévère : CLACSO = réseau 70+ instituts Amérique latine sur société/politique/foncier; très pertinent; 0 doc = requête initiale insuffisante ou mal spécifiée. Tenter accès API + requêtes ciblées ['tierra', 'reforma agraria', 'campesino']. Potentiel restauration très haut.)
- **Archive.org — recherches générales (anarchism/peasant movements/commons enclosure)** → `drop` (Stériles mais Archive.org *réussit* requêtes précises (CLT=25, Federici=2, théorie communs=2). Problème = overbreadth. Abandonner requêtes génériques; lancer ciblées : 'community land trusts', 'commons enclosure 1500-1850', 'cooperative housing 1900-1950'. Investissement requêtes = gain immédiat.)
- **Böll Stiftung (publications DE, Agriculture EN topic)** → `drop` (0 doc sur foncier français (FR déjà couvert 54%); DE seul représenté 2 docs catalogue. Source trop générale + thème agriculture ≠ foncier-communs. Budget requête plus efficace sur RRI/PANLAC/GRAIN.)
- **CrimethInc (zines), Portal OACA (Libros anarquistas), Traficantes de Sueños (15M matière)** → `drop` (Stériles après scans répétés. Contenu anarchiste/niche/daté (15M 2011) = retour très faible. Conserver seulement si cadrage projet spécifique 'couverture mouvements radicaux'; sinon abandon recommandé.)
- **Infokiosques.net — index généraux (A, C, L, Anticolonialismes, Écologie radicale, Squat)** → `review` (Index génériques stériles (0 docs). Mais fonds 'Paysannerie & ruralité' = 46 docs ✓. Stratégie : conserver requête-fonds spécifique, abandonner index génériques A/C/L/Anticolonialismes. Indexation trop large = bruit.)