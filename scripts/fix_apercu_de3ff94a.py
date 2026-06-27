#!/usr/bin/env python3
"""Aperçu de référence pour de3ff94a — The Community Land Trust Book (1972).

PDF introuvable (archive.org borrow-only, access-restricted). Summary rédigé
depuis la connaissance documentaire du livre fondateur des CLT.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]
d = docs["de3ff94a"]
e = d.get("enrichment") or {}

e["summary"] = (
    "Ouvrage fondateur sur les Community Land Trusts (CLT), publié en 1972 par "
    "l'Institute for Community Economics (ICE, USA). Premier manuel complet sur ce "
    "modèle de propriété collective de la terre : la terre est détenue par une "
    "fiducie communautaire à perpétuité — hors marché — tandis que les bâtiments "
    "peuvent être possédés individuellement. L'ouvrage pose les bases théoriques, "
    "légales et organisationnelles des CLT, s'appuie sur les expériences pilotes "
    "des années 1960 (New Communities Inc. en Georgie, premier CLT rural américain), "
    "et propose un modèle reproductible pour maintenir un accès durable et abordable "
    "au logement et à la terre face à la spéculation foncière."
)

e["en_clair"] = (
    "L'ouvrage de référence fondateur sur les Community Land Trusts — modèle où "
    "une communauté détient la terre collectivement pour toujours, hors du marché. "
    "Indispensable pour comprendre les CLT et monter une structure d'accès durable "
    "à la terre ou au logement."
)

if not d.get("author"):
    d["author"] = "Robert Swann, Shimon Gottschalk et al. (Institute for Community Economics)"

d["enrichment"] = e
CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("de3ff94a : aperçu de référence écrit.")
print("Summary :", e["summary"][:100])
