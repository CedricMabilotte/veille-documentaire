#!/usr/bin/env python3
"""Correction du summary de 28b7cb2c (The Cooperative Way of Housing in Canada).

Le summary précédent commençait par le titre en MAJUSCULES répété (artefact OCR
de la page 2), donnant "THE COOPERATIVE WAY OF HOUSING IN CANADA. THE COOPERATIVE
WAY OF HOUSING IN CANADA. A paper prepared for...".

Remplacé par un résumé rédigé depuis le contenu réel (17 pages, A.F. Laidlaw, 1973).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]
d = docs["28b7cb2c"]
e = d.get("enrichment") or {}

e["summary"] = (
    "Communication de A.F. Laidlaw (Société canadienne d'hypothèques et de logement) "
    "pour le 3e symposium international sur le logement à faible coût (Montréal, 1974). "
    "Présente le modèle coopératif d'habitation — une alternative à la propriété "
    "individuelle et à la location marchande — et son état de développement au Canada "
    "en 1973 : coopératives de construction individuelle, coopératives de logement "
    "collectif en location-accession. Analyse les principes fondateurs (un membre = une "
    "voix, profit redistribué aux usagers), compare avec les modèles scandinaves et "
    "nord-américains, et esquisse le potentiel de déploiement dans les grands centres "
    "urbains canadiens."
)

# Aussi mettre à jour l'auteur si absent
if not d.get("author"):
    d["author"] = "A.F. Laidlaw"

d["enrichment"] = e

CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("28b7cb2c : summary corrigé, auteur renseigné.")
print("Summary :", e["summary"][:120])
