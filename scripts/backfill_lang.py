#!/usr/bin/env python3
"""
backfill_lang.py — Rétro-renseigne le champ `lang` pour les docs existants.

Pour chaque doc du catalogue dont lang est vide :
  1. detect_lang_hints sur titre + filename + URL (mots-clés caractéristiques)
  2. default_lang configuré sur la source dans sources.yml (filet de sécurité)

Ne touche jamais aux docs qui ont déjà une langue détectée.
N'appelle aucun service externe.

Usage :
    python3 scripts/backfill_lang.py [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Chemin absolu du dépôt
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import doc_metadata
import yaml

CATALOG_PATH = REPO / "synopsis" / "catalog.json"
SOURCES_PATH = REPO / "config" / "sources.yml"

VALID_LANGS = {"fr", "en", "es", "pt", "de"}

# Correspondances pour les sources qui n'ont pas (ou plus) de default_lang
# dans sources.yml (sources désactivées, renommées, ou multi-langues à dominante
# connue). Appliquées après hints et après sources.yml.
_LEGACY_SOURCE_LANGS: dict[str, str] = {
    # Index Infokiosques alphabétiques (anciens, tous FR)
    "Infokiosques.net — index A": "fr",
    "Infokiosques.net — index C": "fr",
    "Infokiosques.net — index L (Libération, Luttes)": "fr",
    "Infokiosques.net — index T (Terres, Travail)": "fr",
    # Böll Stiftung EN (ancienne source généraliste)
    "Böll Stiftung — publications EN": "en",
    # Böll Stiftung DE (ancienne source, nom légèrement différent)
    "Böll Stiftung — publications DE": "de",
    # Tierra.org (ancienne source sans suffixe)
    "Tierra.org (Amigos de la Tierra ES)": "es",
    # The Anarchist Library : à dominante EN (78% des docs avec lang = en)
    "The Anarchist Library — OPDS (new releases)": "en",
    "The Anarchist Library — OPDS feed": "en",
}

# Pour Archive.org multi-langues : heuristique sur la requête source
# Les requêtes en language:(eng OR fra OR spa) sont mixtes mais à dominante EN
# (les mots-clés sont anglais : commons, enclosure, agrarian, peasant...).
# On applique "en" comme filet de dernier recours, mieux que "inconnu".
_ARCHIVE_LANG_BY_SOURCE: dict[str, str] = {
    # Requête forcée language:"spa" — toujours espagnol
    "Archive.org — Cuba (ES, réforme agraire & coopératives)": "es",
    # Requêtes à mots-clés anglais, mixtes mais dominante EN
    "Archive.org — commons / enclosure / agrarian (strict)": "en",
    "Archive.org — community land trusts & housing commons": "en",
    "Archive.org — commons / enclosure": "en",
    "Archive.org — anarchism + land/peasant (strict)": "en",
    "Archive.org — peasant movements": "en",
    "Archive.org — subject:anarchism (texts)": "en",
}


def load_source_default_langs() -> dict[str, str]:
    """Retourne un dict {label_source: default_lang} depuis sources.yml."""
    with open(SOURCES_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    result: dict[str, str] = {}
    for src in data.get("sources", []):
        label = src.get("label", "")
        dlang = src.get("default_lang", "")
        if label and dlang in VALID_LANGS:
            result[label] = dlang
    return result


def detect_for_doc(doc: dict, source_langs: dict[str, str]) -> str:
    """Retourne la langue détectée pour un doc, ou '' si indéterminé."""
    url = doc.get("url", "") or ""
    filename = doc.get("filename", "") or ""
    link_text = doc.get("link_text", "") or ""

    # 1. detect_lang_hints sur le titre + filename + URL
    hint_src = " ".join(filter(None, [link_text, filename, url]))
    lang = doc_metadata.detect_lang_hints(hint_src)
    if lang:
        return lang

    # 2. default_lang de la source
    source_label = doc.get("source", "")
    lang = source_langs.get(source_label, "")
    return lang


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill du champ lang dans catalog.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche les changements sans écrire le catalogue")
    args = parser.parse_args()

    # Charger le catalogue
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    # Charger les default_lang par source
    source_langs = load_source_default_langs()
    print(f"Sources avec default_lang : {len(source_langs)}")

    docs = catalog["docs"]
    total = len(docs)

    # Stats avant
    already_set = sum(1 for d in docs.values() if d.get("lang") in VALID_LANGS)
    empty = total - already_set
    print(f"Catalogue : {total} docs, {already_set} avec lang, {empty} sans")

    # Appliquer la détection
    filled = 0
    by_method: dict[str, int] = {"hints": 0, "default_lang": 0, "legacy_source": 0, "not_found": 0}
    by_lang: dict[str, int] = {}

    for doc_id, doc in docs.items():
        # Ne pas écraser une langue existante valide
        if doc.get("lang") in VALID_LANGS:
            continue

        url = doc.get("url", "") or ""
        filename = doc.get("filename", "") or ""
        link_text = doc.get("link_text", "") or ""

        # 1. detect_lang_hints
        hint_src = " ".join(filter(None, [link_text, filename, url]))
        lang = doc_metadata.detect_lang_hints(hint_src)
        method = "hints"

        if not lang:
            # 2. default_lang depuis sources.yml
            source_label = doc.get("source", "")
            lang = source_langs.get(source_label, "")
            if lang:
                method = "default_lang"

        if not lang:
            # 3. default_lang depuis les correspondances legacy/multi-langues
            source_label = doc.get("source", "")
            lang = (
                _LEGACY_SOURCE_LANGS.get(source_label, "")
                or _ARCHIVE_LANG_BY_SOURCE.get(source_label, "")
            )
            if lang:
                method = "legacy_source"

        if not lang:
            method = "not_found"

        by_method[method] = by_method.get(method, 0) + 1

        if lang:
            by_lang[lang] = by_lang.get(lang, 0) + 1
            filled += 1
            if not args.dry_run:
                doc["lang"] = lang
            else:
                print(f"  [{method}] {lang}  {doc_id}  {filename[:50]}")

    # Écrire le catalogue
    if not args.dry_run and filled > 0:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"\nCatalogue mis à jour : {filled} docs renseignés")
    elif args.dry_run:
        print(f"\n[dry-run] {filled} docs seraient renseignés")
    else:
        print(f"\nAucun doc à renseigner")

    print(f"\nPar méthode : {dict(by_method)}")
    print(f"Par langue  : {dict(sorted(by_lang.items(), key=lambda x: -x[1]))}")

    # Stats après
    after_set = already_set + (filled if not args.dry_run else 0)
    print(f"\nAprès backfill : {after_set}/{total} docs ont une langue "
          f"({after_set / total * 100:.1f}%)")


if __name__ == "__main__":
    main()
