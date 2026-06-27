#!/usr/bin/env python3
"""Correction du summary de b9a459d4 (Atop the Watchtower — EZLN).

Le summary précédent commençait par le titre + URL (marqueur d'extraction brute
depuis l'Anarchist Library). Remplacé par un résumé rédigé depuis le texte réel
du PDF (6 pages, 28 décembre 2024).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]
d = docs["b9a459d4"]
e = d.get("enrichment") or {}

e["summary"] = (
    "Texte de l’EZLN du 28 décembre 2024, pour le 30e anniversaire du soulèvement du "
    "1er janvier 1994 au Chiapas. L’EZLN retrace la nuit précédant le soulèvement — "
    "milices qui font leurs adieux, insurgent·e·s qui descendent de la montagne — et explique "
    "comment l’idée des communs a émergé de cette expérience : pas comme concept "
    "préfabriqué mais comme pratique née de la survie collective de communautés "
    "indigènes mayas organisées en silence, sans soutien extérieur ni médias. "
    "Réponse aux récupérations et falsifications de l’histoire zapatiste des 30 ans."
)

e["citations"] = [
    {
        "quote": (
            "This is a presentation over what the compañeros and compañeras, "
            "jefas and jefes will talk about how the idea of the Commons was born."
        ),
        "quote_fr": (
            "C’est une présentation sur comment l’idée des Communs est née, "
            "telle que la racontent les compas, jefas et jefes."
        ),
        "page": 1,
    },
    {
        "quote": "Tomorrow, when the morning star rises, we will turn the world on its head.",
        "quote_fr": (
            "Demain, quand l’étoile du matin se lèvera, "
            "nous allons renverser le monde."
        ),
        "page": 3,
    },
]

d["enrichment"] = e

CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("b9a459d4 : summary et citations corrigés.")
print("Nouveau summary :", e["summary"][:120])
