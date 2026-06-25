#!/usr/bin/env python3
"""Script d'enrichissement des docs repêchés (score_initial=3, sources thématiques)."""
import json
from datetime import datetime

with open('synopsis/catalog.json') as f:
    raw = json.load(f)

docs = raw['docs']

enrichments = {
    '08baa6d1': {
        'downloaded': True,
        'saved_as': 'docs/08baa6d1_Notre_ble_est_politique-24p-cahier-juil2019.pdf',
        'score_final': 8,
        'summary': (
            "Brochure du Groupe blé (actif depuis 2004) présentant les semences paysannes comme un commun vivant, "
            "géré collectivement par des paysan·nes, meuniers et boulangers. Le texte critique la standardisation "
            "imposée par l'industrie semencière (DHS : Distinction, Homogénéité, Stabilité) et défend les mélanges "
            "dynamiques autopollinisants, librement échangeables, comme alternative à la brevetabilité du vivant. "
            "Les semences paysannes y sont définies comme relevant des droits d'usage collectifs, non de la propriété privée."
        ),
        'citations': [
            (
                "« Les semences paysannes sont des semences issues d'une population ou d'un ensemble de populations "
                "dynamiques reproductibles par le cultivateur... Elles sont librement échangeables dans le respect des "
                "droits d'usage définis par les collectifs qui les font vivre. »"
            ),
            "« Le mélange s'adapte. Pour garder un maximum de diversité, on peut toutefois réinjecter de petites quantités de semences. »",
        ],
        'matched_keywords': ['semences paysannes', 'communs', "droits d'usage", 'paysannerie', 'autonomie', 'biodiversité', 'brevetabilité'],
    },
    '581a53c8': {
        'downloaded': True,
        'saved_as': 'docs/581a53c8_2025_3_ilc_po_maps_of_all_constituencies_by_country_women.pdf',
        'score_final': 4,
        'summary': (
            "Document cartographique de l'International Land Coalition (2025) répertoriant 27 organisations membres "
            "représentant 1,134,790 personnes dans les circonscriptions femmes rurales, autochtones et paysannes, "
            "réparties dans une vingtaine de pays (Amérique latine, Afrique, Asie). "
            "Document institutionnel de recensement des membres, sans analyse des droits fonciers."
        ),
        'citations': [
            "27 ORGANISATIONS — 1,134,790 PEOPLE REPRESENTED",
        ],
        'matched_keywords': ['femmes rurales', 'paysannerie', 'International Land Coalition', 'organisations rurales'],
    },
    '95e763e1': {
        'downloaded': True,
        'saved_as': 'docs/95e763e1_agriculture_industrielle_et_chaos_climatique-couleur_inverse-cahier.pdf',
        'score_final': 6,
        'summary': (
            "Brochure militante du Climate Collective (Danemark), traduite par les Brigades d'Actions Paysannes "
            "(Belgique), qui dénonce le rôle de l'agriculture industrielle dans la crise climatique (44-57 % des GES). "
            "Le texte critique la dépossession des terres paysannes par les méga-plantations en monoculture, la "
            "brevetabilité des semences, et la domination des décisions politiques par quelques multinationales. "
            "Il défend la souveraineté alimentaire et l'agroécologie comme alternatives."
        ),
        'citations': [
            (
                "« Le système agricole industriel dépossède les paysan·ne·s de leurs terres et crée des méga-plantations "
                "en monoculture, produisant pour le marché mondial des bio-carburants. »"
            ),
            (
                "« Les applications agricoles du génie génétique achèvent de réduire l'autonomie des agriculteurs, "
                "précipitent l'éradication des paysanneries. »"
            ),
        ],
        'matched_keywords': ['paysannerie', 'dépossession des terres', 'souveraineté alimentaire', 'agroécologie', 'semences brevetées', 'agriculture industrielle'],
    },
    '9e8c8fc5': {
        'downloaded': True,
        'saved_as': 'docs/9e8c8fc5_agriculture_industrielle_et_chaos_climatique-20p-fil-2018.pdf',
        'score_final': 6,
        'summary': (
            "Version format fil (20p, 2018) de la brochure du Climate Collective traduite par les Brigades "
            "d'Actions Paysannes. Critique de la dépossession des terres paysannes, souveraineté alimentaire, "
            "agroécologie. Appel à une action collective de masse en Europe du Nord (2019) contre l'agriculture industrielle."
        ),
        'citations': [
            "« Le système agricole industriel dépossède les paysan·ne·s de leurs terres et crée des méga-plantations en monoculture. »",
            "« Nous savons déjà à quoi ressemblent les solutions : l'agroécologie, les pratiques agricoles durables et la souveraineté alimentaire. »",
        ],
        'matched_keywords': ['paysannerie', 'dépossession des terres', 'souveraineté alimentaire', 'agroécologie', 'agriculture industrielle'],
    },
    '6161499c': {
        'downloaded': True,
        'saved_as': 'docs/6161499c_agriculture_industrielle_et_chaos_climatique-20p-cahier-2018.pdf',
        'score_final': 6,
        'summary': (
            "Version format cahier (20p, 2018) de la brochure du Climate Collective, traduite par les Brigades "
            "d'Actions Paysannes. Même contenu que les autres versions : dépossession des terres paysannes, "
            "critique des OGM et semences brevetées, souveraineté alimentaire. Inclut sources et ressources complémentaires."
        ),
        'citations': [
            "« Le système agricole industriel dépossède les paysan·ne·s de leurs terres. »",
            "« De la nourriture pour les peuples, pas pour le profit ! »",
        ],
        'matched_keywords': ['paysannerie', 'dépossession des terres', 'souveraineté alimentaire', 'agroécologie', 'agriculture industrielle'],
    },
    'b8b0bfd8': {
        'downloaded': True,
        'saved_as': 'docs/b8b0bfd8_agriculture_booklet_swedish.pdf',
        'score_final': 4,
        'summary': (
            "Version suédoise de la brochure militante sur l'agriculture industrielle et le climat "
            "(« För klimaträttvisa — Krossa det industriella jordbruket »). Contenu identique aux versions françaises : "
            "dépossession des terres, souveraineté alimentaire, agroécologie. Document en suédois."
        ),
        'citations': [
            "« Det industriella jordbrukssystemet fördriver småskaliga jordbrukare från deras mark. »",
        ],
        'matched_keywords': ['agriculture industrielle', 'paysannerie', 'souveraineté alimentaire'],
    },
    '3d9a76fb': {
        'downloaded': True,
        'saved_as': 'docs/3d9a76fb_agriculture_booklet_german.pdf',
        'score_final': 4,
        'summary': (
            "Version allemande de la brochure militante sur l'agriculture industrielle et le climat "
            "(« Zerstört die industrielle Landwirtschaft! »). Mentionne explicitement le land grabbing : "
            "accaparement des terres paysannes pour les méga-plantations. Document en allemand."
        ),
        'citations': [
            "« Die Industrielle Landwirtschaft eignet sich Land von Kleinbauern und Kleinbäuerinnen an (land grabbing). »",
        ],
        'matched_keywords': ['land grabbing', 'paysannerie', 'semences brevetées', 'agriculture industrielle'],
    },
    '31c1c30a': {
        'downloaded': True,
        'saved_as': 'docs/31c1c30a_agriculture_booklet_english.pdf',
        'score_final': 5,
        'summary': (
            "English version of the Climate Collective booklet (« Smash Industrial Agriculture for Climate Justice »). "
            "Covers land dispossession of small-scale farmers, monocultures, patented seeds, food sovereignty "
            "and agroecology as alternatives. More accessible than Scandinavian versions for international use."
        ),
        'citations': [
            "« The industrial agricultural system dispossesses small-scale farmers of their land and creates monocultural production on mega-plantations. »",
            "« Agroecology, sustainable farming practices and food sovereignty secure self-determination over the food systems. »",
        ],
        'matched_keywords': ['land dispossession', 'food sovereignty', 'agroecology', 'patented seeds', 'peasantry'],
    },
    'fe77002b': {
        'downloaded': True,
        'saved_as': 'docs/fe77002b_agriculture_booklet_danish.pdf',
        'score_final': 4,
        'summary': (
            "Version danoise de la brochure sur l'agriculture industrielle et le climat "
            "(« Knus det industrielle landbrug i klimaretfærdighedens navn »). "
            "Identique aux autres versions : accaparement des terres, monocultures, semences brevetées. Document en danois."
        ),
        'citations': [
            "« Det industrielle landbrug tager land fra småbønder og skaber i stedet monokulturel produktion på megaplantager. »",
        ],
        'matched_keywords': ['accaparement des terres', 'paysannerie', 'monoculture'],
    },
    'cbb3d138': {
        'downloaded': True,
        'saved_as': 'docs/cbb3d138_rene_riesel-aveux-20pa6-pageparpage-2001.pdf',
        'score_final': 6,
        'summary': (
            "Brochure de René Riesel reproduisant ses aveux politiques au procès de Montpellier (2001) pour la "
            "destruction de riz OGM au CIRAD. Riesel formule une critique radicale du génie génétique comme instrument "
            "d'éradication des paysanneries et de réduction de leur autonomie, refusant toute compromission régulatrice. "
            "Il cite la Caravane intercontinentale avec des paysans du sud de l'Inde et appelle à remettre en cause "
            "les rapports sociaux producteurs du déchaînement technologique."
        ),
        'citations': [
            (
                "« Les applications agricoles du génie génétique achèvent de réduire l'autonomie des agriculteurs, "
                "précipitent l'éradication des paysanneries. »"
            ),
            "« Le temps perdu par la recherche est, à coup sûr, du temps gagné pour la conscience. »",
        ],
        'matched_keywords': ['paysannerie', 'autonomie paysanne', 'OGM', 'sabotage', 'éradication des paysanneries', 'génie génétique'],
    },
    'f73fab0a': {
        'downloaded': True,
        'saved_as': 'docs/f73fab0a_Rene_Riesel_-_Aveux_Complet.pdf',
        'score_final': 6,
        'summary': (
            "Version complète de la brochure de René Riesel « Aveux complets des véritables mobiles du crime commis "
            "au CIRAD » (2001), publiée par les Schizoïdes Associés / Infokiosques. Discours politique de Riesel au "
            "tribunal, critique radicale du génie génétique agricole comme éradication des paysanneries, refus de tout "
            "moratoire ou régulation. Inclut le contexte de la Caravane intercontinentale avec des paysans indiens."
        ),
        'citations': [
            (
                "« Les applications agricoles du génie génétique achèvent de réduire l'autonomie des agriculteurs, "
                "précipitent l'éradication des paysanneries. »"
            ),
            "« Le temps perdu par la recherche est, à coup sûr, du temps gagné pour la conscience. »",
        ],
        'matched_keywords': ['paysannerie', 'autonomie paysanne', 'OGM', 'éradication des paysanneries', 'sabotage', 'lutte paysanne'],
    },
    '235a98fb': {
        'downloaded': True,
        'saved_as': 'docs/235a98fb_jasmin_naturaliste_en_lutte-40p-A5-livret.pdf',
        'score_final': 7,
        'summary': (
            "Entretien avec Jasmin, naturaliste et militant de la ZAD de Notre-Dame-des-Landes (Collectif Mauvaise "
            "Troupe, juillet 2015), format livret A5. Le texte documente la défense collective du bocage face au projet "
            "d'aéroport Vinci, les pratiques d'agriculture paysanne sur la ZAD (60 lieux de vie, centaines d'hectares "
            "cultivés), la contre-expertise naturaliste juridique, et l'émergence d'une zone libre autogérée. "
            "Illustre concrètement la lutte pour la libération des terres."
        ),
        'citations': [
            "« Sur la ZAD de Notre-Dame-des-Landes, on dénombre 60 lieux de vie et des centaines d'hectares de terres reprises à Vinci sont cultivées. »",
            (
                "« L'impuissance de la Préfecture et de Vinci sur le terrain se confirme : les arrêtés juridiques sont "
                "systématiquement transgressés et les tentatives de travaux sabotées. »"
            ),
        ],
        'matched_keywords': ['ZAD', 'libération des terres', 'communs fonciers', 'agriculture paysanne', 'autogestion', 'bocage', 'lutte foncière'],
    },
    '78b90a95': {
        'downloaded': True,
        'saved_as': 'docs/78b90a95_jasmin_naturaliste_en_lutte-40p-A4-fil.pdf',
        'score_final': 7,
        'summary': (
            "Version format A4 fil du même entretien avec Jasmin, naturaliste à la ZAD de Notre-Dame-des-Landes "
            "(Collectif Mauvaise Troupe, 2015). Défense collective du bocage, agriculture paysanne sur la ZAD, "
            "contre-expertise naturaliste, zone libre autogérée. Contenu identique à la version A5."
        ),
        'citations': [
            "« Sur la ZAD de Notre-Dame-des-Landes, on dénombre 60 lieux de vie et des centaines d'hectares de terres reprises à Vinci sont cultivées. »",
        ],
        'matched_keywords': ['ZAD', 'libération des terres', 'communs fonciers', 'agriculture paysanne', 'autogestion', 'bocage'],
    },
    '8413ce56': {
        'downloaded': True,
        'saved_as': 'docs/8413ce56_fa_The_Land_Issue1.pdf',
        'score_final': 8,
        'summary': (
            "Premier numéro du magazine britannique « The Land » (hiver/printemps 2006), qui articule un manifeste "
            "pour les droits fonciers et l'accès à la terre comme fondement de la justice, de la liberté et de la "
            "démocratie. Le texte critique la mainmise du marché sur la terre, défend la terre comme outil convivial "
            "au sens d'Ivan Illich, et couvre les communs fonciers, les droits de planification et les luttes pour "
            "l'accès à la terre au Royaume-Uni."
        ),
        'citations': [
            "« Access to land is not simply a threat to landowning elites — it is a threat to the religion of unlimited economic growth. »",
            "« The only source of wealth is the earth. Anyone who has land has access to energy, water, nourishment, shelter, healing, wisdom. »",
            "« The politics of land — who owns it, who controls it and who has access to it — is more important than ever. »",
        ],
        'matched_keywords': ['land rights', 'communs fonciers', 'accès à la terre', 'politique foncière', 'Ivan Illich', 'droits fonciers'],
    },
}

now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
applied = 0
for uid, enrich in enrichments.items():
    if uid in docs:
        for k, v in enrich.items():
            docs[uid][k] = v
        docs[uid]['enriched_at'] = now
        docs[uid]['enrichment_method'] = 'manual_rescue_score3'
        applied += 1
    else:
        print(f'WARNING: uid {uid} non trouvé dans catalog')

with open('synopsis/catalog.json', 'w') as f:
    json.dump(raw, f, ensure_ascii=False, indent=2)

print(f'Enrichissements appliqués : {applied}')

score_ge6 = [(uid, enrichments[uid]['score_final']) for uid in enrichments if enrichments[uid]['score_final'] >= 6]
print(f'Docs score_final >= 6 : {len(score_ge6)}')
for uid, sc in sorted(score_ge6, key=lambda x: -x[1]):
    print(f'  [{uid}] score={sc} — {docs[uid].get("filename", "")[:60]}')
