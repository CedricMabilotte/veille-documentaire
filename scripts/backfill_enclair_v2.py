#!/usr/bin/env python3
"""Backfill en_clair pour les docs publiés avec PDF sur disque mais sans en_clair.

Rédigés directement depuis le summary existant (pas de subprocess Claude).
Docs couverts : FR + variantes linguistiques sans en_clair dont le summary
est déjà renseigné.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]

ENCLAIR = {
    "54e772e7": (
        "Les Escartons étaient des communes montagnardes médiévales qui géraient "
        "ensemble leurs terres et alpages sans seigneur ni propriétaire unique. "
        "Un modèle historique de commun foncier local à relire pour penser "
        "l'autonomie territoriale aujourd'hui."
    ),
    "19101c21": (
        "Un livret sur les communautés Mapuche et leur lutte pour récupérer leurs "
        "terres en Argentine et au Chili, avec un regard anarchiste sur leur "
        "organisation collective. Pour comprendre comment des peuples indigènes "
        "défendent leur rapport à la terre face à l'État et aux entreprises."
    ),
    "ba64641a": (
        "Le récit d'une communauté paysanne qui a repris collectivement des terres "
        "à Bejuco (Amérique latine) face à un propriétaire absent. "
        "Un exemple concret de réappropriation foncière par l'occupation et "
        "l'organisation communautaire."
    ),
    "08baa6d1": (
        "Les semences paysannes comme bien commun : le Groupe Blé explique pourquoi "
        "les variétés libres se cultivent et s'échangent hors du système des "
        "semences brevetées. Utile pour toute lutte autour des droits semenciers "
        "et de la souveraineté alimentaire."
    ),
    "d3bd8707": (
        "Une histoire du droit qui montre comment le Code Napoléon a transformé "
        "les communs en propriété privée et le travail en marchandise. "
        "Pour comprendre d'où viennent les règles qui gouvernent la terre "
        "et comment les alternatives juridiques sont possibles."
    ),
    "9789d29b": (
        "Un manifeste de 1984 qui explique simplement pourquoi squatter un logement "
        "vide est un acte politique contre la propriété privée spéculative. "
        "Un texte fondateur du mouvement squat européen, toujours d'actualité."
    ),
    "9e8c8fc5": (
        "Ce livret montre le lien direct entre agriculture industrielle et "
        "dérèglement climatique, traduit par les Brigades d'Actions Paysannes. "
        "Utile pour relier les luttes paysannes et écologiques dans une même "
        "critique de l'agrobusiness."
    ),
    "2d0a1772": (
        "Pendant la Grande Dépression, des locataires australiens ont organisé "
        "des comités de résistance aux expulsions et des réoccupations collectives. "
        "Un exemple historique d'auto-organisation face à la crise du logement."
    ),
    "f51dd9f5": (
        "Un fonds de dotation permet de confier une terre ou un bien à une "
        "structure qui ne peut pas le revendre, l'extrayant définitivement du marché. "
        "Ce mini-manuel explique comment monter ce type de structure pour protéger "
        "un lieu ou un projet collectif."
    ),
    "235a98fb": (
        "Jasmin, naturaliste et habitant de la ZAD de Notre-Dame-des-Landes, "
        "raconte comment son engagement écologique l'a conduit à lier lutte "
        "contre l'aéroport et gestion collective de la terre. "
        "Un témoignage sur la convergence entre naturalisme et ZAD."
    ),
    "f73fab0a": (
        "René Riesel s'est défendu seul au tribunal pour avoir détruit des "
        "cultures OGM au CIRAD, en assumant publiquement l'acte. "
        "Le texte intégral de sa plaidoirie, qui articule résistance au "
        "capitalisme agricole et refus de la propriété industrielle du vivant."
    ),
    "38a113bc": (
        "Qu'est-ce qui reste d'une ZAD après les expulsions ? Ce texte analyse "
        "lucidement ce que l'expérience de Notre-Dame-des-Landes a produit — "
        "et ce qu'elle n'a pas résolu. Pour penser la suite des luttes foncières."
    ),
    "876db11d": (
        "Les forêts nourricières peuvent être protégées par des montages juridiques "
        "de communs — fonds de dotation, usufruit collectif. Ce mini-manuel "
        "montre comment sortir une forêt du marché immobilier et la confier "
        "à une communauté pour toujours."
    ),
    "c97fba28": (
        "Un an après les expulsions de la ZAD, ce bilan honnête mesure ce qui "
        "reste des projets collectifs légalisés, des tensions internes et de "
        "l'élan politique. Lecture utile pour toute lutte qui passe d'une "
        "phase d'occupation à une phase d'installation durable."
    ),
    "98360cb9": (
        "En 1931 à Barcelone, des locataires anarchistes ont organisé une grève "
        "massive des loyers et l'ont gagnée en quelques semaines. "
        "Un modèle historique d'action directe sur le logement, porté par la CNT."
    ),
    "79cc5801": (
        "Un livret sur les campagnes rurales et les luttes paysannes, "
        "avec un regard critique sur les illusions du retour à la terre. "
        "Pour réfléchir aux conditions réelles d'une vie paysanne autonome."
    ),
    "ff069338": (
        "Nemeton est un projet de coalition de collectifs qui veulent acquérir "
        "une terre en commun, hors marché, via un fonds de dotation. "
        "Ce mini-manuel explique le modèle et comment monter une structure similaire."
    ),
    "b2d08fef": (
        "Le droit civil offre des outils pour sortir des terres et des biens "
        "de la propriété privée marchande : associations, fondations, fonds de "
        "dotation. Ce mini-manuel explique lesquels choisir et comment les utiliser "
        "pour sécuriser un commun foncier."
    ),
    "2478138a": (
        "Entre 1973 et 1981, des travailleurs immigrés ont mené une grève des "
        "loyers dans les foyers Sonacotra — l'une des plus longues de l'histoire "
        "sociale française. Pour comprendre la lutte pour le logement comme enjeu "
        "de dignité et de droits, pas seulement d'argent."
    ),
    "df840ff3": (
        "La version portugaise de 'Squatter c'est lutter', brochure de 1984 qui "
        "défend l'occupation illégale de logements vides comme acte politique. "
        "Un texte fondateur du mouvement squat, ici dans le contexte brésilien."
    ),
    "e9b2bf94": (
        "La version italienne de 'Squatter c'est lutter' (1984) : occuper un "
        "logement vide comme acte de résistance à la spéculation immobilière. "
        "Un texte court et incisif, toujours utile pour expliquer l'occupation "
        "comme outil de lutte pour le logement."
    ),
    "2c9a5575": (
        "Un texte en espagnol sur les communautés Mapuche en lutte pour leurs "
        "terres ancestrales, avec un regard anarchiste sur leur organisation. "
        "Pour comprendre la solidarité entre mouvements anticoloniaux et "
        "alternatives à la propriété privée de la terre."
    ),
}

updated = 0
for uid, ec in ENCLAIR.items():
    d = docs.get(uid)
    if not d:
        print(f"  absent: {uid}")
        continue
    e = d.get("enrichment") or {}
    if not isinstance(e, dict):
        d["enrichment"] = {"summary": "", "citations": [], "en_clair": ec}
    elif not (e.get("en_clair") or "").strip():
        e["en_clair"] = ec
        d["enrichment"] = e
        updated += 1
    else:
        print(f"  [skip déjà renseigné] {uid}")

print(f"{updated} en_clair ajoutés.")
CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Catalog sauvegardé.")
