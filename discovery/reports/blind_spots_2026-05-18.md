# Diagnostic d'angles morts — 2026-05-18 00:27 UTC

Catalog : **234** docs.

## Stats de couverture

- Par langue : `{'unknown': 167, 'fr': 52, 'es': 10, 'en': 4, 'de': 1}`
- Par décennie : `{'1850s': 2, '1910s': 2, '1920s': 2, '1970s': 1, '1990s': 2, '2000s': 4, '2010s': 7, '2020s': 20}`
- Sources stériles (≥3 scans, 0 doc ≥7) : ['Archive.org — commons / enclosure', 'Archive.org — subject:anarchism (texts)', 'Böll Stiftung — publications DE', 'Böll Stiftung — publications EN', 'CEIPAZ (Cultura de Paz)', 'CGT España', 'CLACSO Libros (acceso abierto)', 'CRAS (Centre de Recherches sur les Alternatives Sociales)', 'Infokiosques.net — index A', 'Infokiosques.net — index C', 'Infokiosques.net — index L (Libération, Luttes)', 'Infokiosques.net — index T (Terres, Travail)', 'Infokiosques.net — nouveautés', 'Lundi.am — RSS principal', 'Portal OACA (anarcosindicalisme ES)', 'Reporterre — RSS principal', 'Sin Permiso (revue radicale ES)', 'The Anarchist Library — OPDS feed', 'Tierra.org (Amigos de la Tierra ES)']

## Synthèse

Catalogue gravement déséquilibré : 71% langue unknown, 30% Archive.org, 8.5% sur 2020s seul, 4% ES/1.7% EN. Vide historique pré-2000 (3.8%) fatal pour thématique 170 ans. Sources stériles nombreuses révèlent mauvaise stratégie requêtes (trop larges) plutôt que absence pertinence conceptuelle. Anglais et espagnol critiques mais quasi-absents. Priorités immédiatement : (1) diversifier EN/ES via GRAIN, TNI, ALAI, CLACSO ; (2) combler historique via Google Books + Gallica ; (3) affiner Archive.org requêtes (AND filtering strict) ; (4) abandonner flux génériques (Reporterre, Lundi.am, Infokiosques).

### Angle mort 1 — langue (high)

Couverture EN catastrophique (4 docs, 1.7% du catalogue) et ES très insuffisante (10 docs, 4.3%), alors que ces deux langues sont déclarées dans le projet. 167 docs (71%) sans identification de langue complique analyse fiable. Littérature anglophone sur commons et land rights existe abondamment mais quasi absente du catalogue.

**Sources suggérées :**
- `html` — https://www.grain.org/ — Library & mapping (ES/EN) → Spécialisée agriculture, semences, droits fonciers Amérique Latine et Asie. Publications EN/ES directement alignées sur paysannerie et propriété d'usage. Accès libre articles et dossiers thématiques.
- `html` — https://www.tni.org/ — publications sur commons et land rights (EN) → Think tank avec corpus académique dense : propriété, communs, mouvements paysans. Rapports téléchargeables EN, nombreuses ressources peer-reviewed.

### Angle mort 2 — période (high)

Vide historique critique : 9 docs seuls avant 2000 (3.8%), concentration extrême 2020s (20 docs). Thématique (enclosures, mouvements agraires, paysannerie) a histoire continue 1850-2020 mais 170 ans absents du catalogue.

**Sources suggérées :**
- `api` — Google Books API — requête 'peasant movements' OR 'land commons' filtré 1850-1990, license libre → Indexe millions ouvrages numérisés. Comblerait vide pré-2000 sans surcharge Archive.org. Nécessite intégration API pour harvesting automatisé.
- `html` — https://gallica.bnf.fr/ — collections 'paysannerie', 'propriété collective', 'mouvements agraires' XVIIIe-XXe → Bibliothèque numérique française riche en sources historiques. Recherche par sujet et année possible. Nombreux documents en libre accès.

### Angle mort 3 — géographie / langue (high)

Hispanophonie très faible malgré pertinence. Sources ES spécialisées (Vía Campesina 6, EZLN 5, CLOC 5) produisent peu dans catalogue. Infokiosques.net (stérile, 35 scans) monopolise veille FR au lieu de diversifier vers Amérique Latine et Ibérie.

**Sources suggérées :**
- `rss` — https://www.alainet.org/ — RSS/archives 'tierra', 'campesinos', 'propiedad' (ES/PT) → Agence péruvienne information spécialisée mouvements sociaux et droits fonciers Amérique Latine. Publications archivées en libre accès, RSS actif.
- `html` — https://www.clacso.org/ — Biblioteca Digital CLACSO, recherche 'tierra' OR 'propiedad' (ES/PT) → Consortium latino-américain accumule thèses et articles EN/ES/PT sur propriété foncière, agriculture vivrière, mouvements agraires. Base de 200k+ documents.

### Angle mort 4 — thème (medium)

'Habitat et collectifs' quasi invisible (0 source spécialisée identifiée). 'Propriété d'usage' génère 1 seul doc (HAL). Risque angle mort sur coopératives d'habitation, logements collectifs, communs urbains — axe pourtant central aux concepts déclarés.

**Sources suggérées :**
- `api` — https://hal.archives-ouvertes.fr/ — API requête ('fonds de dotation' OR 'propriété d'usage') AND ('habitat' OR 'logement') (FR/EN) → Base académique française. Requête ultra-ciblée sur habitat + propriété d'usage pourrait générer 10-20 articles supplémentaires non surfacés. Intégration API possible.
- `html` — https://www.righttothecity.org/ — archives RTTC coalitions + publications housing commons (EN/ES) → Réseau global mouvements habitat droit à la ville. Documents, études cas, analyses mouvements urbains pour propriété collective et communs urbains.

### Angle mort 5 — format & diversification sources (medium)

Dépendance Archive.org 30% (69 docs). Infokiosques stérile malgré efforts (35 scans). Absence quasi-totale format interactif (vidéos, podcasts, cartes, bases données brutes). Aucune source 'données foncières' (cadastres alternatifs, mappings participatifs).

**Sources suggérées :**
- `other` — https://landmatrix.org/ — cartographie et base données acquisitions foncières, mouvements résistance (EN/ES) → Hybrid données géospatiales + récits militants. Couverture mondiale, librement interrogeable, API accessible. Enrichirait perspective données brutes.
- `html` — https://viacampesina.org/ — canal YouTube + site web (ES/EN/FR/multiling) → Mouvements paysans produisent vidéos, communiqués, analyses. Format décentralisé. Diversifie du texte, capture voix directes mouvements.

### Angle mort 6 — rigueur académique (medium)

Couverture académique anglophone effondrée (4 docs EN, provenance floue). Sources prestigieuses Böll Stiftung EN/DE retournent 0 doc. Anarchist Library OPDS = 0 doc. Risque biais dominant : gris et militant sans contrepoids institutionnel EN.

**Sources suggérées :**
- `html` — https://www.academia.edu/ — recherche 'commons' OR 'land rights' OR 'peasant movements' (EN/ES/FR) filtrée 2000+ → Réseau académique global. Chercheurs postent directement articles, thèses, preprints. Filtre langue/année possible. Capture chercheurs hors circuits institutionnels.
- `html` — https://www.jstor.org/ — accès institutionnel si possible, sinon 'Land', 'Property rights', 'Agrarian' (EN/ES) → Archive revues académiques 350+ ans. Indexation précise. Sans accès institutionnel, recommander chercheurs libres accès (ResearchGate, ArXiv mouvements paysans).

## Verdict sources stériles

- **Infokiosques.net — index A, C, L, T (Terres/Travail) + nouveautés** → `drop` (35+ scans, 0 doc pertinent. Archives radicales FR mériteraient confiance mais ROI nul suggest mauvaise interaction requête/site ou mismatch contenu. Index génériques trop larges. Effort sans résultat 3+ mois = à abandonner pour réallouer ressources.)
- **Archive.org — subject:anarchism (texts)** → `review` (20 scans, 0 doc. Requête très appropriée (anarchisme → paysannerie/communs, Kropotkine etc.) mais execution = bruit maximal. À revoir avec AND filtering strict : ('land' OR 'property' OR 'peasant' OR 'earth') ET année >= 1850.)
- **Archive.org — commons / enclosure** → `review` (16 scans, 0 doc. Vocabulaire pertinent mais requête trop large ('commons' seul = résultats ultra-bruitées). À raffiner : 'commons enclosure' + year 1700-2020 + language:en OR fr, ou filtrer par license CC.)
- **Böll Stiftung — publications EN et DE** → `review` (16 scans (8 each), 0 doc. Böll = fondation sérieuse (Heinrich Böll, écologie politique). Requêtes probablement génériques ('property', 'commons' solo). À explorer directement site + requêtes ciblées : 'land reform', 'agrarian', 'smallholder', 'cooperative'.)
- **Reporterre — RSS principal** → `drop` (Média écologie généraliste FR. Couverture thématique aléatoire, 0 match constant. À remplacer par source spécialisée mouvements paysans (Vía Campesina RSS, ALAI, Mediapart Enquêtes si accès).)
- **Lundi.am — RSS principal** → `drop` (Flux radical-anarcho très généraliste FR. Faible signal/bruit pour thématique précise. ROI très faible après mois(?) de scanage.)
- **The Anarchist Library — OPDS feed** → `drop` (Qualité source excellente mais OPDS = format obsolète pour veille ciblée. Requête mauvaise ou feed non-parsable. À abandonner ou remplacer par API site si existe.)
- **Sin Permiso (revue radicale ES) | CGT España | Portal OACA** → `review` (3 sources ES/FR légitimes mais 0 doc catalogue = inexploitées. Potentiel réel mais accès/format peuvent poser problème. Ajouter RSS/site si dispo, sinon ne pas prioritiser vs Vía Campesina/CLOC/ALAI qui performent déjà.)