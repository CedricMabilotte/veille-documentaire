#!/usr/bin/env python3
"""
Nettoyage des auteurs mal inférés — session #8
Corrections manuelles + logique améliorée
"""

import json
import re

CATALOG_PATH = "synopsis/catalog.json"

# ─────────────────────────────────────────────────────────────────────────────
# Corrections manuelles ciblées
# uid → (author_correct, raison)
# None = effacer le champ author (pas d'auteur identifiable)
# ─────────────────────────────────────────────────────────────────────────────

OVERRIDES = {
    # Erreurs produites par la logique filename (début de titre, pas auteur)
    "02b2b6df": (None, "collectif ZAD, pas d'auteur individuel"),
    "c99e6da4": (None, "acteur extrait = entité politique, pas auteur"),
    "779edb5d": (None, "filename = titre, pas auteur"),
    "79cc5801": (None, "filename = titre — auteur: André Dréan mentionné dans le titre"),
    "aff51cb1": (None, "filename = titre, pas auteur"),
    "c8d42f2f": (None, "filename = titre, pas auteur"),
    "2175f7a3": (None, "Housing You Can Afford = titre, pas auteur — org: Cooperative Housing Federation"),
    "9789d29b": (None, "To Squat is to Struggle = titre, pas auteur — publication collective"),
    "2e5629b5": (None, "Que reste-t-il = titre, pas auteur — publication collective"),
    "a90d3977": (None, "Que reste-t-il = titre, pas auteur — publication collective"),
    "67a24eca": (None, "Un an après = titre, pas auteur — publication collective"),
    "c97fba28": (None, "Un an après = titre, pas auteur — publication collective"),
    "5c511048": (None, "Acerca de = titre, pas auteur — publication collective"),
    "2c9a5575": (None, "Acerca de = titre, pas auteur — publication collective"),
    "467b0d83": (None, "Communautés mapuche = titre, pas auteur — publication collective"),
    "19101c21": (None, "Communautés mapuche = titre, pas auteur — publication collective"),
    "d992c836": (None, "Contre La = extrait titre, pas auteur — Collectif Troisièmes Voix"),
    "b85c8bc1": (None, "Contre La = extrait titre, pas auteur — Collectif Troisièmes Voix"),
    "5da811ca": (None, "Peuples Nasa = acteur/sujet, pas auteur — publication collective"),
    "915b8d79": (None, "IASET001 = identifiant, pas auteur"),
    "fba04469": ("durval", None),  # conserver — c'est le nom réel (archive.org uploader)
    "8413ce56": (None, "The Land = titre du périodique, pas auteur — publication collective"),
    # Mini-manuels: auteur = Collectif Troisièmes Voix
    "f51dd9f5": ("Collectif Troisièmes Voix", "éditeur connu des Mini-Manuels"),
    "ff069338": ("Collectif Troisièmes Voix", "éditeur connu des Mini-Manuels"),
    "b2d08fef": ("Collectif Troisièmes Voix", "éditeur connu des Mini-Manuels"),
    "d3bd8707": ("Collectif Troisièmes Voix", "éditeur connu des Mini-Manuels"),
    "876db11d": ("Collectif Troisièmes Voix", "éditeur connu des Mini-Manuels"),
    # Auteurs corrects mais format à améliorer
    "8bfe460c": ("Borodin, Volin, Yolk", "co-auteurs nettoyés depuis pdf_author"),
    "6325ebd3": ("Elsie N. Danenberg", "format nom nettoyé"),
    "ea71c1cb": ("Nathaniel Paine", "format nom nettoyé"),
    "05392c72": ("Jacques-Pierre Bridet", "format inversé corrigé"),
    # Journaux/périodiques cubains : pas d'auteur individuel
    "03b9d287": (None, "journal Combate, pas d'auteur individuel — Fidel Castro est acteur, pas auteur du journal"),
    "35641d6d": (None, "journal Lunes de Revolución, pas d'auteur individuel"),
    "dc1574ae": (None, "journal Combate, pas d'auteur individuel"),
    # Organisations collectives — OK comme auteur
    # "55db5001": "La Via Campesina" → correct
    # "9e831a55": EZLN → garder mais nettoyer
    "9e831a55": ("Ejército Zapatista de Liberación Nacional", "organisation auteur, Capitán Marcos est narrateur"),
    # Radio / sources collectives
    "a54f94c8": (None, "Radio Canut = éditeur/diffuseur, pas auteur du texte"),
    "bc522fd4": (None, "Radio Mouvance = source audio, pas auteur du texte"),
    # b9a459d4 : EZLN correct
    "b9a459d4": ("Ejército Zapatista de Liberación Nacional", "organisation auteur"),
    # "durval" : conserver
    "fba04469": (None, "durval = username archive.org, pas auteur réel"),
    # 79cc5801 already set to None above, but let's add André Dréan
    "79cc5801": ("André Dréan", "auteur mentionné dans le titre"),
}


def main():
    with open(CATALOG_PATH) as f:
        catalog = json.load(f)
    docs = catalog["docs"]

    fixed = 0
    cleared = 0

    for uid, (author, reason) in OVERRIDES.items():
        if uid not in docs:
            print(f"  {uid}: ABSENT du catalogue")
            continue
        old = docs[uid].get("author")
        if author is None:
            if "author" in docs[uid]:
                del docs[uid]["author"]
            print(f"  {uid}: cleared (was {old!r:.50}) — {reason}")
            cleared += 1
        else:
            docs[uid]["author"] = author
            print(f"  {uid}: '{old}' → '{author}' — {reason}")
            fixed += 1

    with open(CATALOG_PATH, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\n  → {fixed} corrigés, {cleared} effacés")


if __name__ == "__main__":
    main()
