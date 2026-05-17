# Diagnostic d'angles morts — 2026-05-17 21:06 UTC

Catalog : **151** docs.

## Stats de couverture

- Par langue : `{'unknown': 112, 'fr': 36, 'en': 2, 'de': 1}`
- Par décennie : `{'1850s': 2, '1910s': 2, '1920s': 2, '1970s': 1, '1990s': 1, '2000s': 4, '2010s': 7, '2020s': 13}`
- Sources stériles (≥3 scans, 0 doc ≥7) : ['Archive.org — commons / enclosure', 'Archive.org — subject:anarchism (texts)', 'Böll Stiftung — publications DE', 'Böll Stiftung — publications EN', 'CRAS (Centre de Recherches sur les Alternatives Sociales)', "HAL — propriété d'usage / fonds de dotation", 'Infokiosques.net — index A', 'Infokiosques.net — index C', 'Infokiosques.net — index L (Libération, Luttes)', 'Infokiosques.net — index T (Terres, Travail)', 'Infokiosques.net — nouveautés', 'Lundi.am — RSS principal', 'The Anarchist Library — OPDS feed']

## Synthèse

Couverture fortement biaisée (French 24%, 112 docs non-classés, post-2010 dominant). Espagnol absent malgré déclaration projet ; anglais anecdotique ; Hémisphère Sud inexistant. Vide critique 1930-1960s (réformes agraires coloniales/postcoloniales). Littérature grise (ONG, bulletins syndicaux) = 0 doc. 13 sources stériles révèlent problème de requêtes mal formulées (Archive.org 'anarchism' hors-scope) et sourcing idéologiquement décalé (Infokiosques). Priorités : (1) audit métadonnées 112 docs non-catégorisés, (2) requêtes ciblées Archive.org/Gallica pour 1930-1960, (3) intégration SciELO+Google Scholar pour EN/ES/Sud global, (4) contact direct ONG paysannes (Conf. Paysanne, MST, Via Campesina) pour littérature grise, (5) drop sources anarchistes/infokiosques.

### Angle mort 1 — langue (high)

Anglais : 2 docs (1,3%), Espagnol : 0 docs (0%) malgré déclaration projet. Allemand : 1 seul doc. Sources EN/DE testées (Böll Stiftung 16 scans) sont stériles, signe de mauvaises requêtes plutôt que mauvaises sources.

**Sources suggérées :**
- `html` — scholar.google.com : recherche avancée '(commons OR enclosure OR land rights) AND (peasant OR rural OR agriculture)' filtrée EN, 2015-2026 → Couverture articles académiques anglais ; meilleure structure de recherche qu'Archive.org pour ce scope multidimensionnel
- `html` — scielo.org : recherche 'tierras comunes' OR 'reforma agraria' OR 'movimientos campesinos' (couverture ES/PT Amérique latine) → Espagnol absent du catalogue ; SciELO maîtrise études agraires et mouvements paysans pour zone géographique stratégique

### Angle mort 2 — période (high)

Vide critique 1930s-1960s : 0 doc (décolonisation, réformes agraires majeures). Couverture pré-1900 anecdotique (4 docs). 74% des docs post-2010 = absence de perspective diachronique.

**Sources suggérées :**
- `html` — archive.org/advancedsearch.php : année 1930-1960, mots-clés 'land reform' OR 'agrarian' OR 'peasant', langues fr/en/es → Requêtes Archive.org actuelles ('anarchism', 'commons') = hors-scope ; ciblage précis par période+concept maximise ROI
- `html` — gallica.bnf.fr : recherche 'réforme agraire' OR 'communes foncières' OR 'paysannerie' filtrée 1900-1970 → Gallica (BnF numérisée) jamais exploitée ; couverture dense française pré-1970 + communs fonciers français historiques

### Angle mort 3 — type_source (high)

Littérature grise absente : 0 rapports ONG, bulletins syndicaux, archives gouvernementales. HAL : 4 docs pertinents en paysannerie, 0 en 'propriété d'usage'. Thèses académiques quasi-absentes.

**Sources suggérées :**
- `api` — openaccess.proquest.com (ou accès institutionnel ProQuest Dissertations & Theses) : '(commons OR land rights OR agrarian reform) AND (peasant OR rural)' 1990-2026 → Thèses = profondeur analytique absente des datasets ; ouvre accès via institutions avec souscription
- `api` — HAL.science : recherche avancée 'propriété' AND ('usage' OR 'usufruit' OR 'tenure') + agritrop.cirad.fr collections 'paysannerie' → HAL propriété-usage = 0 doc = requête mal formulée (synonymes manquants) ; Agritrop (CIRAD agriculture) jamais scanné

### Angle mort 4 — géographie (medium)

Hémisphère Sud quasi-absent : 0 Amérique latine, Afrique, Asie du Sud détectable. Mouvements paysans contemporains (MST Brésil, Via Campesina, Africa Land Network) inexistants.

**Sources suggérées :**
- `html` — scielo.org + redalyc.org : recherches 'assentamento' OR 'reforma agraria' OR 'terras comuns' (couverture Brésil 40% de SciELO, agrarisme fort) → SciELO domine sciences sociales Amérique latine open-access ; couvre mouvements sociaux + analyses agraires MST/paysannes
- `html` — ajol.info (African Journals Online) : recherche 'land commons' OR 'land rights' OR 'tenure' → Zone géographique entièrement absente ; revues africaines scientifiques en open-access jamais exploitées

### Angle mort 5 — format_gris (medium)

Rapports/bulletins institutionnels : 0 doc. Seules sources = textes numériques. Organisations paysannes (Confédération, MST, Via Campesina) = source documentaire directe jamais testée.

**Sources suggérées :**
- `other` — Sites directs organisations : confederation-paysanne.fr/ressources + mstzinho.org/biblioteca + viacampesina.org/en/publications (documents PDF, littérature grise) → Littérature grise = analyses pratiques des mouvements eux-mêmes ; sources stériles (CRAS, Lundi.am) probablement nécessitent accès direct ou API spécifique

### Angle mort 6 — metadata (medium)

112/151 docs (74%) sans langue détectée (heuristique) : problème d'encoding/catalogage masquant couverture réelle. Métadonnées sous-exploitées avant ajout nouvelles sources.

**Sources suggérées :**
- `other` — Audit interne : enrichissement détection langue sur 112 docs (langdetect Python ou API) avant nouvelles acquisitions → Problème interne prioritaire : 74% non-classés masquent ratios réels EN/ES/DE. Hygiène métadonnées = meilleur ROI que nouvelles sources avant nettoyage

## Verdict sources stériles

- **Infokiosques.net (index A,C,T,L + nouveautés)** → `drop` (43 scans cumulés (11+8+8+8+8) = 0 docs pertinents. ROI zéro. Index par lettre = requêtes trop génériques ; hors-scope idéologique apparent (infokiosques = activisme généraliste). Coût humain prohibitif.)
- **Archive.org — commons / enclosure** → `drop` (20 scans, 0 doc. Concept 'enclosure' trop polysémique (économie, technologie, architecture) = bruyant. Mieux vaut requête ciblée Archive.org Adv.Search ou abandon.)
- **Archive.org — subject:anarchism (texts)** → `drop` (20 scans, 0 doc. Anarchisme ≠ couverture terrestre/paysannerie ; hors-scope idéologique. Redondant avec Anarchist Library (aussi stérile).)
- **Böll Stiftung — publications EN/DE** → `review` (16 scans cumulés, 0 doc. Source réputée (think tank allemand) = probable problème de requête plutôt que source. Tenter accès direct boell.de + requêtes ciblées avant drop.)
- **HAL — propriété d'usage / fonds de dotation** → `review` (0 doc. Concept 'propriété d'usage' sous-indexé ou mal traduit. Requery avec synonymes (usufruit, tenure, droit d'usage) + inclure Agritrop collection CIRAD avant abandon.)
- **The Anarchist Library — OPDS feed** → `drop` (Hors-scope idéologique (anarchisme vs couverture foncière). Redondant avec Archive.org anarchism (aussi stérile). Aucune pertinence méthodique.)
- **CRAS (Centre Recherches Alternatives Sociales)** → `review` (0 doc. Source thématiquement cohérente (alternatives sociales ⊃ communs fonciers). Probable problème d'accès ou indexation fermée. Vérifier site direct cras-solaris.org avant drop.)
- **Lundi.am — RSS principal** → `review` (0 doc capturé. RSS généraliste peut être bruyant (actualité large) ou déphasé. Vérifier : flux réellement exploité ? Filtrer mots-clés ('terre', 'foncier', 'paysan') plutôt qu'abandon immédiat.)