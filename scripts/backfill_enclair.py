#!/usr/bin/env python3
"""Backfill en_clair pour les docs non-francophones publiés sans cet champ."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]

enclair_map = {
    "35641d6d": (
        "Un journal culturel de la révolution cubaine qui accompagnait les premières lois "
        "de réforme agraire. Pour comprendre comment une révolution articule la question "
        "foncière dès ses premiers jours."
    ),
    "2175f7a3": (
        "Un guide pratique sur les coopératives d'habitation au Canada (1977) montrant "
        "comment organiser un logement accessible et collectif. Utile pour quiconque "
        "cherche des alternatives concrètes à la propriété individuelle et à la location marchande."
    ),
    "5ea6c0cc": (
        "Un article sur les luttes foncières en Inde, notamment des communautés paysannes "
        "et adivasis qui résistent à l'accaparement de leurs terres. Un témoignage de terrain "
        "sur les mouvements pour les droits fonciers dans le Sud global."
    ),
    "8bfe460c": (
        "Analyse du mouvement paysan dans le sud de la Chine dans les années 1920, au "
        "coeur d'une révolution et de luttes agraires. Un document historique sur la question "
        "de la terre dans les révolutions du XXe siècle."
    ),
    "28b7cb2c": (
        "Présentation synthétique du modèle coopératif d'habitation au Canada, préparée "
        "pour un symposium international sur le logement abordable. Utile pour comprendre "
        "les fondements et l'organisation pratique des coopératives d'habitants."
    ),
    "dc1574ae": (
        "Un numéro du journal cubain Combate (avril 1959), en plein coeur de l'élaboration "
        "de la réforme agraire. Document d'archive pour saisir comment la question foncière "
        "a été débattue dans la révolution cubaine."
    ),
    "de3ff94a": (
        "L'ouvrage fondateur sur les Community Land Trusts -- modèle de propriété collective "
        "de la terre qui soustrait le foncier au marché. Un classique pour comprendre et "
        "mettre en place des structures d'accès durable à la terre ou au logement."
    ),
    "931fc89b": (
        "Un prospectus qui explique simplement ce qu'est un Community Land Trust et comment "
        "une communauté peut posséder collectivement la terre. Idéal pour initier quelqu'un "
        "au modèle CLT en quelques pages."
    ),
    "b0917bdf": (
        "Une note de la Banque mondiale sur comment reconnaître les droits fonciers coutumiers "
        "dans les systèmes juridiques formels. Utile pour comprendre les enjeux du droit "
        "foncier là où la terre est gérée collectivement par les communautés."
    ),
    "03b9d287": (
        "Un numéro du journal cubain Combate (avril 1959), pendant la révolution qui allait "
        "transformer l'agriculture cubaine. Document d'archive sur les débats qui ont entouré "
        "la réforme agraire à ses débuts."
    ),
    "acd4bba6": (
        "Une analyse des tensions entre le pouvoir de l'État et les pratiques des communs : "
        "peut-on s'appuyer sur l'État pour défendre les biens communs ? Une réflexion utile "
        "pour les mouvements cherchant à faire reconnaître leurs communs sans se faire récupérer."
    ),
    "ea71c1cb": (
        "Un document historique sur des soldats de la Révolution anglaise du XVIIe siècle "
        "qui revendiquaient l'accès collectif à la terre. Un exemple ancien de lutte pour "
        "les communs fonciers dans l'histoire britannique."
    ),
    "b9a459d4": (
        "Un texte de l'armée zapatiste (EZLN) sur leur vision politique et leur lutte pour "
        "la terre et l'autonomie des peuples indigènes. Un document de résistance qui articule "
        "la question foncière avec l'autodétermination."
    ),
    "8413ce56": (
        "Le premier numéro de The Land, magazine britannique qui défend le droit d'accès à "
        "la terre et les alternatives à l'agriculture industrielle. Lecture indispensable sur "
        "les débats contemporains autour de la terre comme bien commun en Angleterre."
    ),
    "05392c72": (
        "Une critique d'un décret révolutionnaire français de 1792 qui accordait le partage "
        "des biens communaux entre particuliers. Un document historique sur les résistances "
        "à l'enclosure des communs pendant la Révolution française."
    ),
    "a91bd215": (
        "Un texte qui retrace l'histoire du mouvement zapatiste mexicain comme lutte pour la "
        "terre et l'autonomie indigène depuis 1994. Utile pour comprendre comment la question "
        "foncière est au coeur des luttes d'émancipation contemporaines."
    ),
    "e4f64264": (
        "Des archives polonaises sur les fondements des mouvements agraires paysans du début "
        "du XXe siècle. Document d'archive pour les chercheurs en histoire des luttes paysannes "
        "en Europe centrale."
    ),
}

updated = 0
for uid, ec in enclair_map.items():
    d = docs.get(uid)
    if not d:
        print(f"  absent: {uid}")
        continue
    e = d.get("enrichment")
    if not isinstance(e, dict):
        d["enrichment"] = {"summary": "", "citations": [], "matched_keywords": [], "en_clair": ec}
    else:
        e["en_clair"] = ec
    updated += 1

# Corriger le summary OCR de 2175f7a3
d = docs.get("2175f7a3", {})
e = d.get("enrichment") or {}
if isinstance(e, dict):
    s = e.get("summary", "") or ""
    if s.startswith("Housing You Can Afford. Housing You Can Afford"):
        e["summary"] = (
            "Guide pratique de 237 pages (Green Tree Publishing, 1977) sur les coopératives "
            "d'habitation au Canada, préparé pour le troisième symposium international sur le "
            "logement abordable. Présente le modèle coopératif comme alternative concrète à "
            "la propriété privée et à la location marchande : fonctionnement, financement, "
            "montage juridique et exemples de coopératives canadiennes existantes."
        )
        print("  summary 2175f7a3 corrigé (OCR)")

# Nettoyer les faux positifs error:None
cleaned = 0
for d in docs.values():
    e = d.get("enrichment")
    if isinstance(e, dict) and "error" in e and e["error"] is None:
        del e["error"]
        cleaned += 1

print(f"{updated} en_clair ajoutés/mis à jour")
print(f"{cleaned} faux positifs error:None supprimés")

CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Catalog sauvegardé.")
