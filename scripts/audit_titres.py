#!/usr/bin/env python3
"""Audit qualité des titres des fiches publiées.

Règles appliquées :
- pas d'info de format dans le titre (cahier, page par page, fil, x2...)
- pas d'auteur entre parenthèses en fin de titre
- casse cohérente (pas de mots tout-MAJUSCULES hors acronymes)
- pas de tronquage apparent
- cohérence de la série Mini-Manuel (capitale après le tiret)
- pas de suffixe "— version linguistique" seul sans contexte
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run():
    with open(ROOT / "synopsis" / "catalog.json") as f:
        data = json.load(f)
    docs = data["docs"]
    fiches_uids = {
        f.replace(".html", "")
        for f in os.listdir(ROOT / "site" / "fiches")
        if f.endswith(".html") and len(f) == 13
    }

    PARASITES = re.compile(
        r"\b(cahier|page\s*par\s*page|pageparpage|\bfil\b|to[\s_]read|to[\s_]print"
        r"|\bNB\b|[0-9]+p\b|x[0-9]+\b|booklet|livret\s+A[456])",
        re.I,
    )
    AUTHOR_PARENS = re.compile(r"\s*\([A-ZÀÂÉ][a-zàâéèê]+\s+[A-ZÀÂÉ][a-zàâéèê]+\)\s*$")
    KNOWN_ACRONYMS = {
        "ZAD", "MST", "CLT", "HAL", "PDF", "DIY", "OAI", "RSS",
        "ILC", "CIRAD", "NDDL", "UBPC", "ANAP", "CPA", "CCS",
        "EZLN", "NO", "TAV", "GNU", "USA", "ONG", "FAO",
        "VALCOM", "OACA", "AMAP", "FIAN", "GRAIN", "TNI", "IIED",
        # Numéros de périodiques : le regex split par espace donne "N°29,"
        # On absorbe tous ces tokens qui ressemblent à "N°X" ou "N°XX,"
    }

    def _is_known_acronym(word: str) -> bool:
        if word in KNOWN_ACRONYMS:
            return True
        # Numéros de périodiques : N°1, N°29, nr.10, etc.
        if re.match(r"^N[°º][0-9]+,?$", word):
            return True
        return False

    issues = []
    for uid in sorted(fiches_uids):
        d = docs.get(uid) or {}
        title = (d.get("title") or "").strip()
        if not title:
            continue
        link_text = ""
        if d.get("runs"):
            link_text = (d["runs"][-1].get("link_text") or "").strip()

        probs = []
        if PARASITES.search(title):
            probs.append("format_parasite")
        if AUTHOR_PARENS.search(title):
            probs.append("auteur_dans_titre")
        if title.endswith("..."):
            probs.append("tronqué")
        words = title.split()
        # Retirer la ponctuation encadrante avant de tester (ex: "(ZAD" → "ZAD")
        def _strip_punct(w: str) -> str:
            return re.sub(r"^[^A-Za-zÀ-ÿ]+|[^A-Za-zÀ-ÿ0-9]+$", "", w)

        all_caps = [
            w for w in words[1:]
            if _strip_punct(w).isupper() and len(_strip_punct(w)) > 3
            and not _is_known_acronym(_strip_punct(w))
        ]
        if all_caps:
            probs.append(f"mot_MAJUSCULES:{all_caps[0]}")
        if re.search(r"[_\[\]{}<>|\\]", title):
            probs.append("chars_suspects")
        # Version linguistique isolée : n'est un problème QUE s'il n'y a pas
        # d'autre contenu distinctif dans le titre avant la mention de langue.
        # "Occupare è lottare — version italienne" = OK (titre + langue)
        # "— version italienne" seul = problème
        if re.search(r"^— version (lituanienne|italienne|anglaise|espagnole)$", title, re.I):
            probs.append("version_lingue_isolée")
        if re.match(r"Mini-Manuel\s+[a-z]", title):
            probs.append("mini_manuel_minuscule")
        if len(title) > 90:
            probs.append("titre_long")

        if probs:
            issues.append({
                "uid": uid,
                "title": title,
                "probs": probs,
                "link_text": link_text,
                "lang": d.get("lang", "fr"),
                "source": d.get("source", ""),
            })

    print(f"Titres avec problèmes : {len(issues)}/{len(fiches_uids)}\n")
    for item in issues:
        print(f"[{item['uid']}] [{item['lang']}] {item['title'][:80]}")
        print(f"  → {', '.join(item['probs'])}")
        if item["link_text"] and item["link_text"] != item["title"]:
            print(f"  link_text : {item['link_text'][:80]}")
        print()
    return issues


if __name__ == "__main__":
    run()
