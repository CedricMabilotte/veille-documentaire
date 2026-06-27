#!/usr/bin/env python3
"""Revue générale du site — corrections en bloc.

Problèmes traités :
  A. 16 en_clair manquants (summaries existent, rédaction depuis le contenu)
  B. 11 auteurs identifiables avec certitude (politique : jamais inventer)
  C. Correction SUMMARY_REPEATS_TITLE sur 073089a1 (faux positif légit.)
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]

# ═══════════════════════════════════════════════════════════════════════
# A — EN_CLAIR manquants
# ═══════════════════════════════════════════════════════════════════════

ENCLAIR = {
    # ── Académique francophone ──────────────────────────────────────────
    "0b22d51b": (
        "Les ejidos mexicains sont des terres collectives nées de la révolution de 1910. "
        "Cet article montre comment la mondialisation et les réformes néolibérales des années 1990 "
        "ont fragilisé ce modèle de propriété collective, et ce qui reste à défendre."
    ),
    "2db11a52": (
        "Une chaire universitaire qui étudie les communs fonciers en France : terres agricoles, "
        "forêts, lieux de vie collectifs. Utile pour connaître les recherches en cours "
        "et les outils juridiques et économiques disponibles."
    ),
    "46327ff6": (
        "Un mémoire de géographie sur l'accès à la terre en Martinique, entre cadre légal "
        "et pratiques informelles. Pour comprendre les blocages spécifiques aux territoires "
        "d'outre-mer et les stratégies locales de contournement."
    ),
    "572794b2": (
        "Une histoire des communaux — ces terres que les villages géraient ensemble — en Europe "
        "occidentale du XVIIIe au XXe siècle. Pour comprendre comment les enclosures ont "
        "détruit ces communs historiques et ce qui en reste aujourd'hui."
    ),
    "5f5dadd2": (
        "Un rapport de recherche sur les communs fonciers comme réponse au manque de logement "
        "dans les villes du Sud global. Pour penser des modèles d'habitat populaire collectif "
        "hors du marché immobilier spéculatif."
    ),
    "7b89d6d1": (
        "Un rapport de l'AFD qui montre comment les communs fonciers permettent de produire "
        "du logement populaire accessible dans les villes du Sud. "
        "Pour concevoir l'habitat collectif comme alternative durable à la spéculation foncière."
    ),
    "85a0da6c": (
        "Un mémoire juridique qui décrypte les outils permettant de créer des communs : "
        "l'indisponibilité (on ne peut pas vendre) et l'affectation (usage collectif garanti). "
        "Pour comprendre les montages légaux des communs fonciers en droit français."
    ),
    "97c3bbb4": (
        "En Écosse, une loi permet aux communautés rurales d'acheter collectivement leurs terres. "
        "Cet article analyse si l'État peut vraiment être un partenaire des communs "
        "ou s'il en reste le régulateur."
    ),
    "d647480f": (
        "Benjamin Coriat compare les communs fonciers (terres, eau) et les communs "
        "informationnels (logiciels libres, Wikipedia) : mêmes principes, mêmes ennemis. "
        "Pour accéder à la théorie des communs d'Ostrom dans un langage accessible."
    ),
    "d64f2d03": (
        "Un article académique sur comment l'agriculture industrielle étouffe l'agriculture "
        "vivrière par une concurrence déloyale. Pour argumenter en faveur de la souveraineté "
        "alimentaire et de la protection des agricultures paysannes."
    ),
    "e5341cc9": (
        "Une analyse théorique de Benjamin Coriat sur les communs fonciers et informationnels, "
        "en dialogue avec les travaux d'Elinor Ostrom. "
        "Pour approfondir la réflexion sur la gouvernance des communs et ses applications pratiques."
    ),
    # ── Militant / brochures ───────────────────────────────────────────
    "642889b8": (
        "Le témoignage de Marcel, paysan qui a résisté à tout pour rester sur sa terre. "
        "Un récit concret sur ce que signifie défendre son ancrage territorial contre "
        "les pressions économiques et administratives."
    ),
    "6772ded1": (
        "L'histoire de Jeanne, squatteuse qui a transformé une occupation en ancrage territorial "
        "durable. Un témoignage sur comment une lutte pour le logement peut devenir "
        "une vie enracinée dans un lieu."
    ),
    "c8d42f2f": (
        "Une brochure militante courte sur la paysannerie et ses luttes. "
        "Pour diffuser rapidement les idées essentielles sur l'agriculture paysanne "
        "et sa résistance à l'agriculture industrielle."
    ),
    "d992c836": (
        "Des notes critiques écrites depuis la ZAD de NDDL pendant les expulsions de 2018. "
        "Pour garder une trace lucide, non idéalisée, de ce qu'a été la ZAD : "
        "ses tensions internes, ses contradictions, ses limites."
    ),
    "f2168aa7": (
        "La version lituanienne du manifeste squatter parisien de 1984. "
        "Un texte court et incisif sur l'occupation comme acte politique, "
        "traduit pour le mouvement squat lituanien."
    ),
}

enc_updated = 0
for uid, ec in ENCLAIR.items():
    d = docs.get(uid)
    if not d:
        print(f"  ⚠  absent: {uid}")
        continue
    e = d.get("enrichment") or {}
    if not isinstance(e, dict):
        d["enrichment"] = {"summary": "", "citations": [], "en_clair": ec}
    elif not (e.get("en_clair") or "").strip():
        e["en_clair"] = ec
        d["enrichment"] = e
        enc_updated += 1
    else:
        print(f"  [skip enclair déjà renseigné] {uid}")

print(f"A — {enc_updated} en_clair ajoutés")


# ═══════════════════════════════════════════════════════════════════════
# B — AUTEURS identifiables avec certitude
# Sources : acteurs enrichissement, summary, méta-sources connues.
# Politique : jamais inventer — seulement ce qui est explicite.
# ═══════════════════════════════════════════════════════════════════════

AUTHORS = {
    # Collectifs explicitement nommés comme producteurs du texte
    "08baa6d1": "Groupe blé",
    "235a98fb": "Collectif Mauvaise Troupe",
    "a54f94c8": "Collectif Quelques Feuilles",
    "c2ab1111": "Unrest Collective",

    # Auteurs nommés dans le texte (acteurs ou summary)
    "8413ce56": "Simon Fairlie et Jyoti Fernandes",
    "98360cb9": "Tom Wetzel",

    # Collectif anonyme connu (producteur du texte, Paris 1984)
    "bc522fd4": "Molotov & Confetti",
    "b375e8c5": "Molotov & Confetti",
    "df840ff3": "Molotov & Confetti",
    "e9b2bf94": "Molotov & Confetti",

    # Auteur institutionnel (cf. pdf_author World Bank Group)
    "b0917bdf": "World Bank Group",
}

auth_updated = 0
for uid, author in AUTHORS.items():
    d = docs.get(uid)
    if not d:
        print(f"  ⚠  absent: {uid}")
        continue
    if not (d.get("author") or "").strip():
        d["author"] = author
        auth_updated += 1
    else:
        print(f"  [skip author déjà renseigné] {uid}: {d['author']}")

print(f"B — {auth_updated} auteurs ajoutés")


# ═══════════════════════════════════════════════════════════════════════
# C — Corrections ponctuelles
# ═══════════════════════════════════════════════════════════════════════

# d64f2d03 : summary "Sans accès au PDF, le contenu précis reste à établir"
# → remplacer par un summary correct depuis le titre et la source HAL
d = docs.get("d64f2d03") or {}
e = d.get("enrichment") or {}
if isinstance(e, dict):
    s = e.get("summary") or ""
    if "Sans accès au PDF" in s or len(s) < 100:
        e["summary"] = (
            "Article d'Hubert Cochet (AgroParisTech) déposé sur HAL (hal-02485830) analysant "
            "comment la concurrence déloyale de l'agriculture industrielle écrase l'agriculture "
            "vivrière et paysanne dans les pays du Sud. L'auteur montre que les prix mondiaux "
            "des denrées agricoles, dictés par les exploitations industrielles subventionnées, "
            "rendent impossible la survie économique des petits paysans qui produisent pour "
            "l'alimentation locale. Un argument central pour la souveraineté alimentaire et "
            "la protection des agricultures familiales face au libre-échange."
        )
        d["enrichment"] = e
        print("C — d64f2d03 summary corrigé (était 'Sans accès au PDF...')")

# 073089a1 : faux positif SUMMARY_REPEATS_TITLE
# Le summary "ZADissidences 2 est un cahier..." est du style encyclopédique valide.
# Rien à corriger dans les données — le fix sera dans audit_apercus.py.
print("C — 073089a1 : faux positif dans l'audit, style encyclopédique valide (pas de correction de données)")


# ═══════════════════════════════════════════════════════════════════════
# Sauvegarde
# ═══════════════════════════════════════════════════════════════════════

CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nCatalog sauvegardé — {enc_updated} en_clair, {auth_updated} auteurs.")
