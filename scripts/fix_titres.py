#!/usr/bin/env python3
"""Corrections de titres — session #8 biblio.

Sources :
- PDF fitz (page 1 + métadonnées)
- link_text des runs (texte brut du lien source)
- summary (contexte éditorial)
- règles de style maison
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "synopsis" / "catalog.json"

data = json.loads(CAT.read_text(encoding="utf-8"))
docs = data["docs"]

CORRECTIONS = {
    # ── Titres incomplets (révélés par PDF fitz) ────────────────────────────
    "38a113bc": {
        "title": "La fin de la ZAD, le début de quoi ?",
        "_note": "PDF bloc 1 : 'La fin de la ZAD, le début de quoi ?'",
    },
    "54e772e7": {
        "title": "La République des Escartons",
        "_note": "PDF bloc 2 : 'La République des Escartons... autonomie communale dans le Briançonnais'",
    },
    "b9a459d4": {
        "title": "Atop the Watchtower — A Long Look at Yesterday",
        "_note": "PDF bloc 2 : 'A Long Look at Yesterday' (sous-titre confirmé)",
    },

    # ── Parasites de format retirés, titres canoniques rétablis ────────────
    "2c9a5575": {
        "title": "Acerca de las comunidades Mapuche en guerra — solidaridad anárquica",
        "_note": "link_text : 'comunidades mapuche en guerra y la solidaridad anárquica'",
    },
    "2d0a1772": {
        "title": "La résistance aux expulsions en Australie (1929–1936)",
        "_note": "Retiré 'page par page'",
    },
    "df840ff3": {
        "title": "Ocupar é lutar — version portugaise (1984)",
        "_note": "Retiré 'page par page', ajouté contexte langue",
    },
    "bc522fd4": {
        "title": "Ocupar é lutar — version portugaise, à imprimer (1984)",
        "_note": "Distingue de df840ff3 (même texte, format imprimable)",
    },

    # ── Auteur extrait du titre → champ author ──────────────────────────────
    "79cc5801": {
        "title": "Campagnes à vendre — Le miroir aux illusions",
        "author": "André Dréan",
        "_note": "Auteur retiré du titre, versé dans doc.author",
    },
    "ea71c1cb": {
        "title": "Worcester's Old Common",
        "author": "Nathaniel Paine",
        "_note": "link_text : 'Worcester's old common: remarks made at the annual banquet'"
                 " — 'Pain' dans l'ancien titre était une troncature de Paine",
    },

    # ── Typographie et casse ─────────────────────────────────────────────────
    "2db11a52": {
        "title": "Chaire Valcom — Valoriser les communs fonciers",
        "_note": "Tiret demi-cadratin ; VALCOM → Valcom (acronyme humanisé)",
    },
    "46327ff6": {
        "title": "Systèmes d'acteurs, freins et voies d'accès à la terre : "
                 "l'agriculture locale martiniquaise, entre cadre foncier formel et pratiques socio-spatiales",
        "_note": "Espace avant ':' (typographie française) ; retiré '…' final",
    },

    # ── Auteurs dans le titre → champ author ────────────────────────────────
    "8bfe460c": {
        "title": "The Peasant Movement in Kwantung — Materials on the Agrarian Question",
        "_note": "Auteurs (Borodin, Volin, Yolk) déjà dans doc.author, retirés du titre",
    },

    # ── Numérotation des ZADissidences (série à harmoniser) ─────────────────
    "5ea1719f": {
        "title": "ZADissidences 1",
        "_note": "Summary : 'numéros 1, janvier–avril 2018' (numéros 2 et 3 déjà titrés ZADissidences 2/3)",
    },

    # ── Série Mini-Manuel : harmoniser Titre (capitale) après le colon ──────
    "876db11d": {
        "title": "Mini-Manuel : Forêts nourricières",
        "_note": "Capitalisation après ':' ; cohérence de la série",
    },
    "b2d08fef": {
        "title": "Mini-Manuel : Droit civil",
        "_note": "Capitalisation après ':'",
    },
    "d3bd8707": {
        "title": "Mini-Manuel : Petite histoire du droit",
        "_note": "Capitalisation après ':' ; 'petite' → 'Petite'",
    },
    "f51dd9f5": {
        "title": "Mini-Manuel : Fonds de dotation",
        "_note": "Capitalisation après ':' ; 'fonds dotation' → 'Fonds de dotation'",
    },
    "ff069338": {
        "title": "Mini-Manuel : Communalisme et Nemeton",
        "_note": "Ajout du ':' pour cohérence de la série",
    },
}

applied = 0
for uid, patch in CORRECTIONS.items():
    d = docs.get(uid)
    if not d:
        print(f"  ⚠  {uid} absent du catalogue")
        continue
    note = patch.pop("_note", "")
    old_title = d.get("title", "")
    for k, v in patch.items():
        d[k] = v
    print(f"  {uid}: {old_title[:55]!r}")
    print(f"       → {patch.get('title', '(inchangé)')!r}")
    if note:
        print(f"       # {note}")
    applied += 1

print(f"\n{applied} corrections appliquées.")
CAT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Catalog sauvegardé.")
