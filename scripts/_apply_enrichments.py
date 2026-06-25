#!/usr/bin/env python3
"""
Applique les enrichissements générés directement par Claude (sans CLI).
Chaque entrée est un dict avec : summary, citations, matched_keywords, acteurs, relevance_score.
"""
import json
from pathlib import Path

CATALOG_PATH = Path('/home/ced/Documents/Claude/Projects/biblio/synopsis/catalog.json')

# ── Enrichissements générés directement ──────────────────────────────────────
ENRICHMENTS = {

# === DOCS SCORE 5 ===

"514c1d0e": {
    "summary": "Résumé du livre 'Tentative communautaire' (1971-1972), récit d'une expérience collective libertaire dans une ferme abandonnée en Aveyron. Un groupe de jeunes militants achète collectivement la ferme S. grâce à un héritage, organise la propriété entre quatre communautés voisines pour préserver le lieu dans 'le milieu' en cas de dissolution. Le texte analyse les tensions entre autonomie individuelle et collective, le rapport à la propriété, et les limites de la tentative de 'terre libérée' hors transformation sociale globale.",
    "citations": [
        {"quote": "S. sera une « terre libérée »", "page": 2, "context": "Idéal du projet communautaire"},
        {"quote": "sa propriété officielle sera volontairement partagée entre 4 communautés voisines", "page": 1, "context": "Modèle de propriété collective"},
        {"quote": "faire entrer une analyse de notre démarche dans une analyse globale de la société", "page": 2, "context": "Articulation pratique/théorie"},
    ],
    "matched_keywords": ["terre libérée", "propriété collective", "communauté", "autonomie", "alternatives à la propriété privée"],
    "acteurs": ["Michel Bosson", "Françoise Denaud", "Bernard Vidal"],
    "relevance_score": 7
},

"8f7080e5": {
    "summary": "Version cahier du résumé de 'Tentative communautaire' (1971-1972). Même contenu que la version page par page : récit d'une expérience collective libertaire dans une ferme en Aveyron, organisée autour d'une propriété partagée entre communautés et d'un idéal de 'terre libérée'.",
    "citations": [
        {"quote": "S. sera une « terre libérée »", "page": 2, "context": "Idéal du projet"},
        {"quote": "sa propriété officielle sera volontairement partagée entre 4 communautés voisines", "page": 1, "context": "Propriété collective"},
    ],
    "matched_keywords": ["terre libérée", "propriété collective", "communauté libertaire"],
    "acteurs": ["Michel Bosson", "Françoise Denaud", "Bernard Vidal"],
    "relevance_score": 7
},

"fa6ceecb": {
    "summary": "Guide pratique (en anglais) sur les droits des personnes hébergées en urgence et en trêve hivernale en France. Détaille les droits à un hébergement digne, aux repas, à l'hygiène, à la liberté d'entrée/sortie, à la confidentialité. Explique les recours juridiques disponibles, les organismes à contacter, et les démarches pour défendre ses droits en cas de non-respect. Document pratique à destination des sans-abri et personnes précarisées.",
    "citations": [
        {"quote": "To be granted housing conditions that are in conformity with the human dignity", "page": 2, "context": "Droit à un logement digne"},
        {"quote": "To enter and exit the shelter freely", "page": 2, "context": "Liberté de mouvement"},
    ],
    "matched_keywords": ["logement d'urgence", "hébergement", "droits des sans-abri", "habitat"],
    "acteurs": [],
    "relevance_score": 4
},

"2c9c4d74": {
    "summary": "Guide pratique (en français) sur l'hébergement d'urgence et la trêve hivernale, produit par un collectif grenoblois. Explique les droits des personnes hébergées en CHRS/CADA/hôtels sociaux, les recours face aux expulsions, le 115, la trêve hivernale. Document militant à destination des personnes sans logement stable.",
    "citations": [
        {"quote": "On est un petit collectif grenoblois qui passe régulièrement du temps dans les centres d'hébergement", "page": 1, "context": "Origine militante"},
    ],
    "matched_keywords": ["hébergement d'urgence", "trêve hivernale", "logement", "sans-abri"],
    "acteurs": ["Collectif grenoblois"],
    "relevance_score": 4
},

"76ab1d39": {
    "summary": "Récit de la lutte contre les sfratti (expulsions locatives) à Turin entre 2011 et 2012. Décrit les assemblées de locataires, les piquets devant les logements menacés d'expulsion, et les occupations collectives organisées par des mouvements pour le droit au logement. Document de retour d'expérience sur une lutte urbaine pour le maintien dans les lieux.",
    "citations": [
        {"quote": "lutte contre les sfratti a turin assemblees piquets et occupations 2011-2012", "page": 1, "context": "Titre et objet du document"},
    ],
    "matched_keywords": ["expulsions locatives", "droit au logement", "lutte urbaine", "occupation", "résistance collective"],
    "acteurs": [],
    "relevance_score": 5
},

"a5df1a9d": {
    "summary": "Version page par page du récit de la lutte contre les sfratti (expulsions) à Turin 2011-2012. Même contenu que la version cahier : assemblées, piquets et occupations pour résister aux expulsions locatives.",
    "citations": [
        {"quote": "lutte contre les sfratti a turin assemblees piquets et occupations", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["expulsions", "droit au logement", "occupation", "lutte urbaine"],
    "acteurs": [],
    "relevance_score": 5
},

"cfea62d4": {
    "summary": "Récit historique de la résistance australienne aux expulsions locatives entre 1929 et 1936 pendant la Grande Dépression. 'Lock Out The Landlords!' documente les actions directes — barrages aux portes, réinstallation des expulsés, solidarité de quartier — menées par des locataires organisés pour résister aux propriétaires. Document de référence sur les luttes pour le droit au logement et contre la propriété privée lucrative.",
    "citations": [
        {"quote": "Lock Out The Landlords! Australian Eviction Resistance 1929-1936", "page": 1, "context": "Titre et période documentée"},
    ],
    "matched_keywords": ["expulsions", "droit au logement", "résistance collective", "propriété privée", "action directe"],
    "acteurs": [],
    "relevance_score": 6
},

"d7759e91": {
    "summary": "Compilation de quatre textes sur la colonisation de la Palestine et ses conséquences, dans sa version page par page. Analyse la situation coloniale historique et actuelle : dépossession foncière, effacement des droits territoriaux autochtones, résistance palestinienne. Perspective géopolitique et historique sur la question de la terre et de la souveraineté.",
    "citations": [
        {"quote": "4 textes sur la situation coloniale historique et actuelle en Palestine", "page": 1, "context": "Description du document"},
    ],
    "matched_keywords": ["colonisation", "dépossession foncière", "territoire", "Palestine", "droits autochtones"],
    "acteurs": [],
    "relevance_score": 5
},

"3fe8867b": {
    "summary": "Version anglaise (cahier) de '500 Years of Indigenous Resistance' de Gord Hill. Histoire de la résistance autochtone depuis la colonisation des Amériques. Couvre la conquête, le génocide, les luttes pour les terres et la souveraineté autochtone, du XVe siècle au mouvement AIM (American Indian Movement). Document de référence sur la résistance à la dépossession foncière coloniale.",
    "citations": [
        {"quote": "The Struggle for Land", "page": 3, "context": "Chapitre dédié aux luttes foncières"},
        {"quote": "500 years of Indigenous Resistance", "page": 2, "context": "Titre"},
    ],
    "matched_keywords": ["résistance autochtone", "dépossession foncière", "souveraineté", "colonisation", "luttes pour les terres"],
    "acteurs": ["Gord Hill"],
    "relevance_score": 7
},

"5eb432e1": {
    "summary": "Version française page par page de '500 ans de résistance autochtone' de Gord Hill. Histoire de la résistance des peuples autochtones des Amériques face à la colonisation, depuis 1492 jusqu'au mouvement AIM. Traite de la dépossession des terres, des politiques d'extermination et d'assimilation, et des luttes contemporaines pour la souveraineté territoriale.",
    "citations": [
        {"quote": "500 ANS DE RÉSISTANCE AUTOCHTONE", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["résistance autochtone", "dépossession foncière", "souveraineté territoriale", "colonisation", "luttes pour les terres"],
    "acteurs": ["Gord Hill"],
    "relevance_score": 7
},

"7cdc7e8f": {
    "summary": "Version cahier de '500 ans de résistance autochtone'. Les notes bibliographiques visibles suggèrent un document académique dense sur la résistance autochtone en Amérique latine et du Nord. Références à des luttes pour la terre ('Mexico: The Struggle for the Land'), à la stérilisation forcée des femmes autochtones, et aux politiques indiennes du Canada.",
    "citations": [
        {"quote": "Mexico: The Struggle for the Land", "page": 1, "context": "Source citée sur les luttes foncières"},
    ],
    "matched_keywords": ["résistance autochtone", "luttes pour la terre", "dépossession", "souveraineté"],
    "acteurs": ["Gord Hill"],
    "relevance_score": 6
},

"bd44cc6a": {
    "summary": "Version anglaise page par page de '500 Years of Indigenous Resistance' (PM Press, 2009). Histoire complète de la résistance autochtone depuis la colonisation. Table des matières couvre la conquête, l'expansion, le génocide, les guerres indiennes, 'The Struggle for Land', et la résistance totale. Édition de référence.",
    "citations": [
        {"quote": "The Struggle for Land", "page": 3, "context": "Chapitre sur les luttes foncières"},
        {"quote": "In Total Resistance", "page": 3, "context": "Chapitre final"},
    ],
    "matched_keywords": ["résistance autochtone", "luttes pour les terres", "souveraineté", "colonisation"],
    "acteurs": ["Gord Hill"],
    "relevance_score": 7
},

"e612942d": {
    "summary": "Atlas de l'Amazonie brésilienne 2025 (en portugais), publié par la Fondation Heinrich Böll. Recueil de données, faits et savoirs sur la plus grande forêt tropicale du monde. Couvre les dimensions écologiques, sociales, foncières et politiques de l'Amazonie : territoires autochtones, déforestation, conflits fonciers, droits des peuples de la forêt. Document de référence sur les enjeux territoriaux amazoniens.",
    "citations": [
        {"quote": "atlas DA AMAZÔNIA BRASILEIRA", "page": 1, "context": "Titre"},
        {"quote": "Fatos, dados e saberes da maior floresta tropical do mundo", "page": 1, "context": "Sous-titre"},
    ],
    "matched_keywords": ["territoires autochtones", "forêt amazonienne", "conflits fonciers", "droits territoriaux", "déforestation"],
    "acteurs": ["Fundação Heinrich Böll"],
    "relevance_score": 6
},

"b9a459d4": {
    "summary": "Texte zapatiste de décembre 2024 ('Atop the Watchtower — A Long Look at Yesterday'). L'EZLN retrace l'histoire de la naissance de l'idée des communs dans leur mouvement. Document rare : récit à la première personne de la construction de la pensée zapatiste sur les communs, la terre et l'autonomie, à l'occasion des 30 ans de l'insurrection. Critique des interprétations extérieures du zapatisme.",
    "citations": [
        {"quote": "this is a presentation over what the compañeros and compañeras will talk about how the idea of the Commons was born", "page": 1, "context": "Objet central du texte : naissance de l'idée des communs"},
        {"quote": "thirty year anniversary of the uprising", "page": 1, "context": "Contexte : 30 ans de l'insurrection zapatiste"},
    ],
    "matched_keywords": ["communs", "zapatistes", "autonomie", "terres", "EZLN", "libération"],
    "acteurs": ["EZLN", "Ejército Zapatista de Liberación Nacional"],
    "relevance_score": 9
},

"997d46c9": {
    "summary": "Essai de Alexander Atabekian (1920) sur la territorialité et l'anarchisme. Distingue la territorialité naturelle (attachement à un lieu, à une terre) de l'étatisme (frontières arbitraires imposées). Argumente que l'anarchisme, en rejetant l'État, n'implique pas de nier le lien au territoire — au contraire, il reconnaît la 'propriété de travail' liée à la production locale. Texte fondateur sur le rapport anarchiste à la terre et au territoire.",
    "citations": [
        {"quote": "Anarchism, while rejecting statehood, cannot deny territoriality", "page": 1, "context": "Thèse centrale"},
        {"quote": "it recognises labour property, which, thanks to its increased productivity", "page": 1, "context": "Sur la propriété d'usage par le travail"},
    ],
    "matched_keywords": ["territorialité", "propriété d'usage", "anarchisme", "terre", "autonomie territoriale"],
    "acteurs": ["Alexander Atabekian"],
    "relevance_score": 7
},

"597a51e1": {
    "summary": "Essai 'Against Agriculture & In Defense of Cultivation' (2003) de Witch Hazel. Critique de l'agriculture industrielle et plaidoyer pour la cultivation comme pratique écologique et anarchiste. Analyse la relation entre système alimentaire industriel, exploitation de la terre, et domination capitaliste. Défend une pratique de cultivation autonome, locale et respectueuse des sols, opposée à l'agro-industrie.",
    "citations": [
        {"quote": "the current food production system is a recipe for disaster. Soils are becoming sterile, salinated and toxic", "page": 3, "context": "Critique de l'agriculture industrielle"},
        {"quote": "Against Agriculture: Sowing the Seeds of Resistance", "page": 2, "context": "Sous-titre du texte"},
    ],
    "matched_keywords": ["agriculture", "cultivation", "terres", "agroécologie", "résistance alimentaire", "autonomie"],
    "acteurs": ["Witch Hazel"],
    "relevance_score": 6
},

"b50a887d": {
    "summary": "Essai 'Anarchism and Agriculture' d'Alan Albon (1964). Défend qu'une civilisation stable nécessite une agriculture stable et non-exploitative. Critique la propriété privée des terres et plaide pour une agriculture commune, écologique et autonome. Cite Virgile : avant Jupiter, 'All produce went to a common pool, and earth unprompted was free with all her fruits.' Texte anarchiste classique sur la relation terre-liberté.",
    "citations": [
        {"quote": "All produce went to a common pool, and earth unprompted Was free with all her fruits", "page": 1, "context": "Citation de Virgile sur les communs agraires primitifs"},
        {"quote": "The first essential for a stable civilisation is a stable, non-exploitive agriculture", "page": 1, "context": "Thèse centrale sur l'agriculture"},
    ],
    "matched_keywords": ["agriculture anarchiste", "communs agraires", "propriété de la terre", "terres libres", "autogestion"],
    "acteurs": ["Alan Albon"],
    "relevance_score": 7
},

"e0571d65": {
    "summary": "Interview (2005) avec Peter Sterling, organisateur agricole dans le Vermont, par David Van Deusen du Green Mountain Anarchist Collective. Témoignage d'un fermier-organisateur sur les luttes des agriculteurs, la crise agricole rurale, et les alliances entre paysans et mouvements radicaux. Aborde la résistance à l'agro-industrie et les alternatives d'organisation collective dans les zones rurales.",
    "citations": [
        {"quote": "Down on The Farm — Interview With Vermont Farm Organizer Peter Sterling", "page": 1, "context": "Titre et objet du document"},
    ],
    "matched_keywords": ["paysannerie", "agriculture", "organisation rurale", "alternatives agricoles", "luttes rurales"],
    "acteurs": ["Peter Sterling", "David Van Deusen", "Green Mountain Anarchist Collective"],
    "relevance_score": 6
},

"349ea93c": {
    "summary": "Essai de Camillo Berneri (1936) 'Problems of the Revolution — the City and the Country'. Analyse les contradictions entre ville et campagne dans le cadre révolutionnaire. Aborde la question paysanne, la collectivisation agraire, et les rapports de force entre prolétariat urbain et paysannerie dans la perspective anarchiste. Texte de référence sur la question agraire dans l'anarchisme européen des années 1930.",
    "citations": [
        {"quote": "Problems of the Revolution — the City and the Country", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["paysannerie", "question agraire", "révolution", "collectivisation", "ville/campagne"],
    "acteurs": ["Camillo Berneri"],
    "relevance_score": 7
},

"46f92da6": {
    "summary": "Édition numérique de la 'Théorie de la propriété' de Pierre-Joseph Proudhon (1862), texte posthume majeur. Proudhon y développe une théorie complexe de la propriété comme contre-pouvoir à l'État : la propriété individuelle est nécessaire à la liberté mais doit être limitée et ne peut devenir monopole. Réflexion fondamentale sur les alternatives à la propriété absolue et sur les communs.",
    "citations": [
        {"quote": "Pierre-Joseph Proudhon (1862) — THÉORIE DE LA PROPRIÉTÉ", "page": 1, "context": "Titre et auteur"},
    ],
    "matched_keywords": ["propriété", "Proudhon", "alternatives à la propriété privée", "contre-pouvoir", "communs"],
    "acteurs": ["Pierre-Joseph Proudhon"],
    "relevance_score": 7
},

# === DOCS SCORE 4 ===

"a4a76ee2": {
    "summary": "Enquête 'Le blanchiment des terres' (version page par page) sur le projet d'écoquartier Flaubert à Rouen, construit sur d'anciens terrains industriels pollués. Analyse comment les opérations immobilières 'durables' servent à valoriser des friches foncières sans régler les pollutions, au bénéfice des classes moyennes et supérieures. Critique des opérations de 'ripolinage' foncier qui déplacent les classes populaires.",
    "citations": [
        {"quote": "LE BLANCHIMENT DES TERRES — Les pollutions s'arrêtent-elles aux frontières des écoquartiers ?", "page": 1, "context": "Titre"},
        {"quote": "une manne foncière inestimable à deux pas du centre-ville", "page": 2, "context": "Rôle spéculatif du foncier"},
    ],
    "matched_keywords": ["foncier", "spéculation immobilière", "gentrification", "terres polluées", "communs urbains"],
    "acteurs": ["Laura Pandelle"],
    "relevance_score": 6
},

"5095e5aa": {
    "summary": "Version cahier de 'Le blanchiment des terres', enquête sur l'écoquartier Flaubert à Rouen. Même contenu que la version page par page : analyse critique de la valorisation spéculative de friches industrielles polluées sous couvert d'urbanisme durable, avec effets d'éviction des classes populaires.",
    "citations": [
        {"quote": "LE BLANCHIMENT DES TERRES — Les pollutions s'arrêtent-elles aux frontières des écoquartiers ?", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["foncier", "spéculation immobilière", "gentrification", "écoquartier"],
    "acteurs": ["Laura Pandelle"],
    "relevance_score": 6
},

"d022821b": {
    "summary": "Brochure 'Forêt en lutte — Lutte en forêt' (décembre 2018), version page par page. Récit des luttes contre la destruction des forêts, notamment la lutte victorieuse contre la méga-scierie Erscia dans le Morvan. Témoignages d'occupations de forêts, de solidarités inter-luttes, et de résistance à l'industrialisation forestière. Document sur la défense des communs forestiers contre la privatisation et l'exploitation industrielle.",
    "citations": [
        {"quote": "la lutte victorieuse contre la méga scierie", "page": 6, "context": "Victoire de la lutte contre Erscia"},
        {"quote": "occuper une foret menacée", "page": 6, "context": "Tactique d'occupation"},
    ],
    "matched_keywords": ["communs forestiers", "luttes anti-industrielles", "occupation", "forêt", "résistance territoriale"],
    "acteurs": ["Collectif Quelques Feuilles", "Lutte en Forêt en Lutte"],
    "relevance_score": 6
},

"a54f94c8": {
    "summary": "Version cahier de 'Forêt en lutte — Lutte en forêt'. Même contenu : luttes contre la destruction des forêts, récits d'occupations, résistance à l'industrialisation forestière dans le Morvan. Mentionne l'association ADRET (opposants à Erscia), le Réseau pour les Alternatives Forestières, et les luttes contre les centrales biomasse.",
    "citations": [
        {"quote": "L'association des oposant.e.s poursuit son combat pour rêver d'autres avenirs aux forêts", "page": 2, "context": "Continuation de la lutte"},
        {"quote": "L'association A.R.P.E.N.T lutte contre l'installation d'une centrale biomasse dans le Tonnerois", "page": 2, "context": "Luttes locales"},
    ],
    "matched_keywords": ["communs forestiers", "luttes anti-industrielles", "alternatives forestières", "occupation"],
    "acteurs": ["ADRET Morvan", "Réseau pour les Alternatives Forestières", "ARPENT"],
    "relevance_score": 6
},

"d616972c": {
    "summary": "Brochure critique 'Gaz de schiste : scénario pour un gazage programmé' (2011, format brochure). Analyse le rapport d'étape de la mission d'inspection sur les gaz de schiste, favorable à leur exploitation. Décrit la stratégie de l'État et des industriels (CGIET, CGEDD) pour ouvrir l'exploitation des GdS sur le territoire français. Critique de l'accaparement du sous-sol au profit du capital, aux dépens des territoires et des populations.",
    "citations": [
        {"quote": "la stratégie de l'Etat et des industriels en vue de passer, en deux ou trois ans, à l'exploitation massive de cette énergie sur le territoire français", "page": 3, "context": "Enjeu central"},
    ],
    "matched_keywords": ["accaparement du sous-sol", "territoire", "résistance locale", "communs naturels"],
    "acteurs": [],
    "relevance_score": 4
},

"8698e3de": {
    "summary": "Version page par page de la brochure 'Gaz de schiste : scénario pour un gazage programmé' (2011). Même analyse que la version brochure sur le rapport d'inspection et la stratégie d'exploitation des gaz de schiste. Document militant d'analyse critique des politiques énergétiques et de leurs impacts territoriaux.",
    "citations": [
        {"quote": "comment permettre l'exploitation massive des GdS", "page": 3, "context": "Question centrale du rapport d'État"},
    ],
    "matched_keywords": ["territoire", "communs naturels", "résistance locale", "sous-sol"],
    "acteurs": [],
    "relevance_score": 4
},

"83eafaac": {
    "summary": "Brochure de l'association Survie sur la lutte du peuple kanak pour l'indépendance de Kanaky Nouvelle-Calédonie (version cahier, 2021). Analyse le caractère colonial de la situation, les manœuvres de la France pour entraver l'émancipation, et appelle à la solidarité. Aborde la question de la dépossession foncière comme mécanisme colonial central. Document de mobilisation pour le soutien à l'indépendance kanak.",
    "citations": [
        {"quote": "KANAKY NOUVELLE-CALÉDONIE — UNE COLONIE EN LUTTE POUR SON INDÉPENDANCE", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["colonialisme", "dépossession foncière", "souveraineté", "luttes autochtones", "territoire"],
    "acteurs": ["Survie", "Collectif Solidarité Kanaky", "peuple kanak"],
    "relevance_score": 5
},

"0727b92e": {
    "summary": "Version page par page de la brochure Survie sur Kanaky Nouvelle-Calédonie. Même contenu : situation coloniale, lutte kanak pour l'indépendance, mécanismes de confiscation des terres et des ressources. Document de solidarité décoloniale.",
    "citations": [
        {"quote": "KANAKY NOUVELLE-CALÉDONIE — UNE COLONIE EN LUTTE POUR SON INDÉPENDANCE", "page": 1, "context": "Titre"},
        {"quote": "Partager l'analyse des mécanismes de confiscation des indépendances africaines pour éviter qu'ils soient reproduits", "page": 3, "context": "Objectif comparatif"},
    ],
    "matched_keywords": ["colonialisme", "dépossession foncière", "souveraineté territoriale", "luttes autochtones"],
    "acteurs": ["Survie", "Collectif Solidarité Kanaky"],
    "relevance_score": 5
},

"32ccb418": {
    "summary": "Atlas du sol ('Bodenatlas 2024', 2e édition, en allemand), publié par Heinrich Böll Stiftung, BUND et TMG. Recueil de données et faits sur le sol comme ressource vitale. Couvre la dégradation des sols, la propriété foncière, les modèles agricoles, la spéculation sur les terres, et les alternatives. Document de référence sur la question foncière en Allemagne et en Europe.",
    "citations": [
        {"quote": "BODENATLAS — Daten und Fakten über eine lebenswichtige Ressource", "page": 1, "context": "Titre : Atlas du sol, données sur une ressource vitale"},
    ],
    "matched_keywords": ["foncier", "sol", "propriété de la terre", "spéculation foncière", "agriculture"],
    "acteurs": ["Heinrich Böll Stiftung", "BUND", "TMG Think Tank for Sustainability"],
    "relevance_score": 6
},

"567a1117": {
    "summary": "Analyse politique 'Daten als öffentliche Infrastruktur' (Les données comme infrastructure publique, 2022, en allemand) de la Heinrich Böll Stiftung. Argumente pour un droit à l'open data comme bien commun numérique. Propose des recommandations pour traiter les données publiques comme infrastructure commune plutôt que comme propriété privée. Pertinence limitée pour la thématique foncière stricte.",
    "citations": [
        {"quote": "Daten als öffentliche Infrastruktur — Impulse für den Rechtsanspruch auf Open Data", "page": 1, "context": "Titre : données comme infrastructure publique"},
    ],
    "matched_keywords": ["communs numériques", "bien commun", "données publiques"],
    "acteurs": ["Friederike von Franqué", "Stefan Kaufmann", "Heinrich Böll Stiftung"],
    "relevance_score": 3
},

"3e817885": {
    "summary": "Texte de Raoul Vaneigem 'Avis aux civilisés relativement à l'autogestion généralisée' (édition italienne Gatti rossi, 2009). Essai situationniste sur l'autogestion généralisée comme dépassement du capitalisme et de l'État. Développe la critique de la propriété et de la marchandise, et la vision d'une société d'autogestion intégrale. Tangentiel à la thématique foncière stricto sensu.",
    "citations": [
        {"quote": "Avis aux civilisés relativement à l'autogestion généralisée", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["autogestion", "propriété", "alternatives sociales", "critique de la marchandise"],
    "acteurs": ["Raoul Vaneigem"],
    "relevance_score": 5
},

"6596ad83": {
    "summary": "Texte de Ratgeb (pseudonyme de Raoul Vaneigem) 'De la grève sauvage à l'autogestion généralisée'. Manifeste à destination des ouvriers révolutionnaires. Analyse les grèves sauvages comme embryon de l'autogestion et critique la bureaucratie syndicale et partisane. Plaide pour une autogestion généralisée dépassant le capitalisme. Peu centré sur la question foncière mais pertinent sur les alternatives à la propriété.",
    "citations": [
        {"quote": "DE LA GRÈVE SAUVAGE À L'AUTOGESTION GÉNÉRALISÉE", "page": 1, "context": "Titre"},
        {"quote": "briser les reins à l'impérialisme marchand", "page": 1, "context": "Objectif révolutionnaire"},
    ],
    "matched_keywords": ["autogestion", "alternatives à la propriété", "grève", "autogestion ouvrière"],
    "acteurs": ["Ratgeb (Raoul Vaneigem)"],
    "relevance_score": 4
},

"af8b18a5": {
    "summary": "Essai de John Creaghe (janvier 1890) 'The Argentine Republic and English Radical Reformers'. Témoignage d'un anarchiste ayant vécu en Argentine : la liberté politique formelle (suffrage universel, constitution) ne suffit pas face aux inégalités économiques, notamment foncières. Décrit la concentration des terres en Argentine, l'exploitation des paysans et des immigrants. Critique du réformisme politique sans remise en cause des conditions économiques.",
    "citations": [
        {"quote": "Land is free, and i[n theory available to all]", "page": 1, "context": "Liberté formelle sur les terres, contredite par les faits"},
        {"quote": "how utterly useless all political reforms are while economic conditions are opposed to freedom", "page": 1, "context": "Thèse centrale"},
    ],
    "matched_keywords": ["propriété foncière", "concentration des terres", "paysannerie", "liberté économique"],
    "acteurs": ["John Creaghe"],
    "relevance_score": 6
},

"cd8eaa5a": {
    "summary": "Pamphlet 'Make The Golf Course A Public Sex Forest!' (2021). Plaidoyer pour transformer un terrain de golf (Hiawatha Golf Club, Minneapolis) en forêt communautaire publique. Dénonce l'usage privatif et exclusif des terres de golf au détriment des espaces collectifs. Mêle critique de la privatisation de l'espace public, histoire de la dépossession des peuples autochtones, et imagination d'un commun naturel libéré.",
    "citations": [
        {"quote": "Before the genocidal takeover of this land by the United States, the lake and surrounding wetlands wer[e commons]", "page": 3, "context": "Histoire de la dépossession des terres autochtones"},
        {"quote": "A massive waste of space and water", "page": 3, "context": "Critique du golf"},
    ],
    "matched_keywords": ["communs", "espace public", "dépossession foncière", "terres autochtones", "propriété privée"],
    "acteurs": [],
    "relevance_score": 5
},

"9f16b851": {
    "summary": "Interview d'un activiste anarchiste présent à Dale Farm (2011), camp de gens du voyage irlandais menacé d'expulsion en Angleterre. Explique la position anarchiste face à la lutte pour le droit au logement et à la terre à Dale Farm. Document sur la résistance à l'expulsion et sur les articulations entre lutte des gens du voyage, droit à la terre et perspectives anarchistes.",
    "citations": [
        {"quote": "attempting also to solidify the Dale Farm struggles place in the broader class war", "page": 1, "context": "Inscription dans une perspective plus large"},
        {"quote": "people should be free to live as they wish (where that doesn't infringe on other people's freedoms)", "page": 1, "context": "Principe anarchiste appliqué à Dale Farm"},
    ],
    "matched_keywords": ["droit au logement", "expulsion", "gens du voyage", "résistance", "terres", "autogestion"],
    "acteurs": ["Dale Farm Activist"],
    "relevance_score": 6
},

"dcb30b82": {
    "summary": "Témoignage de Tim Meadows 'Why I Work on the Land' (1964). Récit personnel d'un homme qui a choisi le travail agricole plutôt que le travail de bureau. Réflexion sur le rapport à la terre, l'autosuffisance, la valeur du travail manuel, et le rejet de la 'rat-race'. Document sur la relation subjective à la terre et à l'agriculture comme mode de vie alternatif.",
    "citations": [
        {"quote": "Why I work on the land", "page": 1, "context": "Titre"},
        {"quote": "I determined to do a job I enjoyed for its own sake and not for the money involved", "page": 1, "context": "Motivation centrale"},
    ],
    "matched_keywords": ["travail de la terre", "agriculture", "autosuffisance", "mode de vie alternatif"],
    "acteurs": ["Tim Meadows"],
    "relevance_score": 4
},

"17e8cac0": {
    "summary": "'Against the Grain — A Deep History of the Earliest States' de James C. Scott (2017). Histoire profonde de l'émergence des premiers États et de l'agriculture sédentaire. Scott argue que la sédentarisation et l'agriculture céréalière n'ont pas été un progrès spontané mais une contrainte étatique sur des populations nomades. Analyse les résistances à l'État, la 'Zomia', et les formes d'organisation sociale sans État. Texte majeur sur les alternatives à la propriété étatique de la terre.",
    "citations": [
        {"quote": "Against the Grain — A Deep History of the Earliest States", "page": 1, "context": "Titre"},
        {"quote": "Concentration and Sedentism: A Wetlands Thesis", "page": 2, "context": "Thèse sur les origines de la sédentarisation"},
    ],
    "matched_keywords": ["État et territoire", "agriculture", "paysannerie", "résistance", "communs", "Zomia"],
    "acteurs": ["James C. Scott"],
    "relevance_score": 6
},

"f6970688": {
    "summary": "'Anthropology and Anarchism — Learning from Stateless Societies' de Brian Morris (1998). Explore les affinités entre anthropologie et anarchisme dans l'étude des sociétés sans État. Couvre des figures comme Reclus, Kropotkin, Bookchin, Clastres. Analyse les formes d'organisation sociale pré-étatiques, les communs, et les systèmes de propriété collective. Texte théorique sur les alternatives à la propriété privée et à l'État.",
    "citations": [
        {"quote": "Anthropology and Anarchism — Learning from stateless societies", "page": 1, "context": "Titre"},
        {"quote": "historically it has always had a rather specific focus—on the study of pre-state societies", "page": 3, "context": "Objet de l'anthropologie anarchiste"},
    ],
    "matched_keywords": ["sociétés sans État", "communs", "alternatives à la propriété", "anthropologie anarchiste"],
    "acteurs": ["Brian Morris"],
    "relevance_score": 5
},

"8fed461d": {
    "summary": "'A Brief Explanation of the Concept of Territory and Its Implications' de Miguel Amorós (2013). Essai sur le concept de territoire : fragmentation, planification, défense. Distingue territoire (espace vécu, approprié collectivement) de propriété étatique ou privée. Analyse la destruction des territoires par le capitalisme industriel et l'État. Plaide pour la défense du territoire comme résistance à la déterritorialisation capitaliste.",
    "citations": [
        {"quote": "A Brief Explanation of the Concept of Territory and Its Implications", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["territoire", "communs territoriaux", "résistance", "déterritorialisation", "propriété collective"],
    "acteurs": ["Miguel Amorós"],
    "relevance_score": 6
},

"961e54e4": {
    "summary": "'The Conquest of Bread' de Petr Kropotkin (1892). Texte anarchiste classique sur l'organisation d'une société post-révolutionnaire basée sur les communs et la satisfaction des besoins. Analyse la propriété collective des terres, des outils et des ressources. Argumente que la révolution doit commencer par s'emparer des moyens de subsistance (pain, logement, terres) pour les mettre en commun.",
    "citations": [
        {"quote": "The Conquest of Bread", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["communs", "propriété collective", "terres", "révolution agraire", "kropotkin"],
    "acteurs": ["Petr Kropotkin"],
    "relevance_score": 6
},

"fcb58745": {
    "summary": "Édition Vanguard Press 1926 de 'The Conquest of Bread' de Kropotkin (texte de 1892). Même contenu que l'autre édition : texte classique sur les communs, la propriété collective des terres et des ressources, et l'organisation anarchiste de la société après la révolution.",
    "citations": [
        {"quote": "The Conquest of Bread (1926 Vanguard Press edition)", "page": 1, "context": "Titre et édition"},
    ],
    "matched_keywords": ["communs", "propriété collective", "terres", "révolution agraire"],
    "acteurs": ["Petr Kropotkin"],
    "relevance_score": 6
},

"dc04dfbf": {
    "summary": "'The Next Eclipse — A Vision for Regional Autonomy' (2018, anonyme). Vision d'une autonomie régionale basée sur des territoires décentralisés et autogérés. Imagine une organisation politique et économique par régions autonomes, avec une gestion commune des terres et des ressources naturelles. Document prospectif sur les alternatives à l'État-nation centralisé.",
    "citations": [
        {"quote": "The Next Eclipse — A Vision for Regional Autonomy", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["autonomie régionale", "territoire", "communs", "décentralisation", "alternatives à l'État"],
    "acteurs": [],
    "relevance_score": 5
},

"e67b07b8": {
    "summary": "Texte de Kevin Carson 'Orcinus on the Rural Strategy' (2005). Commentaire sur une stratégie de développement rural basée sur l'organisation locale et l'économie alternative. Discute les potentialités des communautés rurales pour construire des alternatives autonomes au capitalisme.",
    "citations": [
        {"quote": "Orcinus on the Rural Strategy", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["économie rurale alternative", "autonomie locale", "organisation communautaire"],
    "acteurs": ["Kevin Carson"],
    "relevance_score": 4
},

"3620b85f": {
    "summary": "'A View from the Plains — On organizing in smaller areas of the Midwest' de R. Spourgitis. Témoignage sur l'organisation politique dans les zones rurales du Midwest américain. Réflexion sur les défis de l'organisation radicale dans des contextes ruraux dispersés, les alliances entre agriculteurs et militants, et les alternatives économiques locales.",
    "citations": [
        {"quote": "A View from the Plains — On organizing in smaller areas of the Midwest", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["organisation rurale", "paysannerie", "économie locale", "alternatives rurales"],
    "acteurs": ["R. Spourgitis"],
    "relevance_score": 4
},

"420a9fe6": {
    "summary": "'Against Eco-capitalism' de Contraciv (2016). Critique du capitalisme vert et de l'éco-capitalisme comme récupération marchande des préoccupations environnementales. Analyse comment le capitalisme instrumentalise les discours écologiques pour continuer l'exploitation des ressources naturelles et des terres. Plaide pour une écologie radicale anti-capitaliste.",
    "citations": [
        {"quote": "Against eco-capitalism", "page": 1, "context": "Titre"},
        {"quote": "Civilization, un[derstanding...]", "page": 2, "context": "Début de l'analyse"},
    ],
    "matched_keywords": ["éco-capitalisme", "alternatives écologiques", "communs naturels", "anti-capitalisme"],
    "acteurs": ["Contraciv"],
    "relevance_score": 4
},

"f9843fd9": {
    "summary": "'Anarchy, Geography, Modernity — Selected Writings of Elisée Reclus'. Anthologie des écrits de Reclus sur la géographie anarchiste, la relation entre espace, territoire et liberté. Reclus développe une vision des communs géographiques, de la nécessité de l'harmonie entre l'humain et la nature, et d'une géographie au service de l'émancipation. Texte fondamental pour la pensée anarchiste sur la terre et le territoire.",
    "citations": [
        {"quote": "Anarchy, Geography, Modernity — Selected Writings of Elisée Reclus", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["géographie anarchiste", "territoire", "communs géographiques", "nature et liberté"],
    "acteurs": ["Elisée Reclus"],
    "relevance_score": 6
},

"b2986cda": {
    "summary": "'The Anthropology of Utopia — Essays on Social Ecology and Community Development' de Dan Chodorkoff. Essais sur l'écologie sociale et le développement communautaire dans la perspective de Murray Bookchin. Explore les alternatives à la société industrielle : communautés autogérées, écologie des communs, développement local. Lien fort avec les questions de propriété collective et d'alternatives foncières.",
    "citations": [
        {"quote": "The Anthropology of Utopia — Essays on Social Ecology and Community Development", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["écologie sociale", "communauté autogérée", "communs", "alternatives", "Bookchin"],
    "acteurs": ["Dan Chodorkoff"],
    "relevance_score": 5
},

"98e8416d": {
    "summary": "'The Battle Against Bayer: The End...or is it?' (2004, anonyme). Récit de la campagne contre la multinationale agrochimique Bayer, notamment ses OGM et pesticides. Documente les mobilisations contre l'accaparement du vivant et des semences par les multinationales. Pertinence pour la thématique des communs agraires et de la résistance à la privatisation du vivant.",
    "citations": [
        {"quote": "The Battle Against Bayer: The End…or is it?", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["communs agraires", "semences", "multinationales agrochimiques", "résistance", "privatisation du vivant"],
    "acteurs": [],
    "relevance_score": 5
},

"a8cc6dcd": {
    "summary": "Brochure 'Crowbar Chronicles' (version anglaise, 2008). Texte trop court ou format invalide pour extraction complète. Titre évoque un récit d'action directe.",
    "citations": [],
    "matched_keywords": [],
    "acteurs": [],
    "relevance_score": 3
},

"fa200745": {
    "summary": "Brochure 'Squat et écriture' (version page par page, 2025). PDF composé d'images scannées, texte non extractible par OCR. Titre suggère un document sur le squat comme pratique et l'écriture comme outil militant.",
    "citations": [],
    "matched_keywords": ["squat", "occupation"],
    "acteurs": [],
    "relevance_score": 4
},

"940578dc": {
    "summary": "Brochure 'Squat et écriture' (version cahier, 2025). PDF composé d'images scannées, texte non extractible. Même contenu que la version page par page.",
    "citations": [],
    "matched_keywords": ["squat", "occupation"],
    "acteurs": [],
    "relevance_score": 4
},

"2f70c746": {
    "summary": "Document 'alpha_068' depuis archive.org. PDF scanné sans texte extractible. Contenu indéterminable à partir du texte.",
    "citations": [],
    "matched_keywords": [],
    "acteurs": [],
    "relevance_score": 2
},

"3486835f": {
    "summary": "Brochure italienne sur les OGM ('OGM : finale di partita'). Document en italien sur les enjeux des organismes génétiquement modifiés, probablement une analyse critique de la privatisation des semences et du contrôle industriel de l'agriculture.",
    "citations": [
        {"quote": "OGM : finale di partita", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["OGM", "semences", "agriculture", "privatisation du vivant"],
    "acteurs": [],
    "relevance_score": 4
},

"d560eee7": {
    "summary": "Brochure 'Racisme et néocolonialisme français' (version page par page), produite par Survie. Analyse les mécanismes de domination néocoloniale de la France, notamment en Afrique. Lien indirect avec la thématique foncière à travers les mécanismes d'accaparement des terres dans les pays colonisés.",
    "citations": [
        {"quote": "RACISME ET NÉOCOLONIALISME FRANÇAIS", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["néocolonialisme", "accaparement des terres", "domination"],
    "acteurs": ["Survie"],
    "relevance_score": 4
},

"1ce39b6d": {
    "summary": "'El poder de la propiedad — Élites y desamortización en la España interior, 1768-1878' (en espagnol). Étude historique sur les élites foncières et la désamortisation (vente des biens ecclésiastiques et communaux) en Espagne. Analyse comment la désamortisation a renforcé la concentration des terres dans les mains des élites plutôt que de créer un accès paysan à la propriété. Document académique majeur sur l'histoire de la propriété foncière espagnole.",
    "citations": [
        {"quote": "El poder de la propiedad — Elites y desamortización en la España interior", "page": 2, "context": "Titre"},
    ],
    "matched_keywords": ["propriété foncière", "élites foncières", "désamortisation", "communs ecclésiastiques", "concentration des terres", "paysannerie"],
    "acteurs": [],
    "relevance_score": 7
},

"6ed0da6d": {
    "summary": "Brochure 'La colonisation de la Palestine et ses conséquences' (version page par page). Analyse de la situation coloniale en Palestine : dépossession foncière systématique, effacement des droits territoriaux palestiniens, résistance. Document sur l'histoire et les mécanismes de la colonisation foncière israélienne.",
    "citations": [
        {"quote": "LA COLONISATION DE LA PALESTINE ET SES CONSÉQUENCES", "page": 1, "context": "Titre"},
    ],
    "matched_keywords": ["colonialisme", "dépossession foncière", "territoire", "résistance"],
    "acteurs": [],
    "relevance_score": 5
},
}

# Appliquer
with open(CATALOG_PATH) as f:
    cat = json.load(f)

applied = 0
for doc_id, enr_data in ENRICHMENTS.items():
    if doc_id in cat['docs']:
        cat['docs'][doc_id]['enrichment'] = enr_data
        rs = enr_data.get('relevance_score')
        if isinstance(rs, (int, float)):
            cat['docs'][doc_id]['score_final'] = int(rs)
        applied += 1
    else:
        print(f'  WARNING: {doc_id} not found in catalog')

with open(CATALOG_PATH, 'w') as f:
    json.dump(cat, f, ensure_ascii=False, indent=2)

print(f'Enrichissements appliques: {applied}')

# Stats finales
score45_dl = [(did, d) for did, d in cat['docs'].items()
              if d.get('score_initial') in (4,5) and d.get('downloaded')]
with_enr = [x for x in score45_dl if x[1].get('enrichment') and 'error' not in x[1].get('enrichment',{})]
score6 = [x for x in score45_dl if isinstance(x[1].get('score_final'),(int,float)) and x[1]['score_final']>=6]
print(f'Score 4-5 DL: {len(score45_dl)} | avec enrichissement: {len(with_enr)} | score_final>=6: {len(score6)}')
