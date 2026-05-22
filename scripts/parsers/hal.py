#!/usr/bin/env python3
"""
hal.py — Parser pour l'API JSON de HAL Science (api.archives-ouvertes.fr).

HAL est l'archive ouverte française d'articles académiques. Ce module
interroge son API de recherche et retourne uniquement les notices qui
exposent un PDF directement téléchargeable (champ `fileMain_s`).
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

import requests

# En-tête HTTP générique : HAL accepte les bots tant qu'on s'identifie.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
TIMEOUT = 30           # HAL peut être lent, surtout sur les grosses requêtes.
MAX_DOCS = 50          # Garde-fou côté client (l'API a déjà `rows=N`).
ABSTRACT_TRUNCATE = 400  # Longueur max du contexte (auteurs + abstract).


def _first(value: Any) -> str:
    """Retourne le premier élément si liste, sinon la valeur convertie en str."""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    if value is None:
        return ""
    return str(value)


def _extract_hal_id(uri: str) -> str:
    """Extrait l'identifiant HAL (ex: 'hal-01234567') depuis l'URI de la notice."""
    if not uri:
        return "unknown"
    # Les URI HAL ressemblent à https://hal.science/hal-01234567 ou .../tel-...
    basename = urlparse(uri).path.rstrip("/").split("/")[-1]
    return basename or "unknown"


def _build_filename(file_url: str, uri: str) -> str:
    """Construit un nom de fichier .pdf à partir de l'URL du PDF ou de l'ID HAL."""
    path = urlparse(file_url).path
    basename = os.path.basename(path)
    if basename.lower().endswith(".pdf"):
        return basename
    # HAL utilise parfois des URLs « propres » sans extension : on en fabrique une.
    return f"hal_{_extract_hal_id(uri)}.pdf"


def _build_context(authors: Any, abstract: Any) -> str:
    """Concatène auteurs + résumé (tronqué) pour le champ `context`."""
    parts: list[str] = []
    if authors:
        if isinstance(authors, list):
            parts.append(", ".join(str(a) for a in authors))
        else:
            parts.append(str(authors))
    abstract_str = _first(abstract).strip()
    if abstract_str:
        parts.append(abstract_str)
    ctx = " — ".join(p for p in parts if p)
    if len(ctx) > ABSTRACT_TRUNCATE:
        ctx = ctx[:ABSTRACT_TRUNCATE].rstrip() + "..."
    return ctx


def find_documents(source: dict) -> list[dict]:
    """Interroge l'API HAL et renvoie les documents PDF disponibles.

    Voir docstring de spec dans la consigne du module.
    """
    url = source.get("url", "")
    if not url:
        return []

    # 1) Requête HTTP
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return []

    # 2) Parsing JSON (tolérant aux corps invalides)
    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError):
        return []

    docs = (payload.get("response") or {}).get("docs") or []
    if not isinstance(docs, list):
        return []

    results: list[dict] = []
    source_label = source.get("label", "")
    source_url = source.get("url", "")

    for doc in docs[:MAX_DOCS]:
        if not isinstance(doc, dict):
            continue

        # 3) Filtre : pas de PDF accessible -> on ignore la notice.
        file_main = _first(doc.get("fileMain_s"))
        if not file_main:
            continue

        uri = _first(doc.get("uri_s"))
        title = _first(doc.get("title_s"))

        # src_meta : métadonnées fiables fournies directement par l'API HAL
        # (exploitées par doc_metadata pour doc_date/lang/editeur/identifiants).
        src_meta = {
            "lang": _first(doc.get("language_s")),
            "date": (_first(doc.get("producedDate_s"))
                     or _first(doc.get("publicationDate_s"))
                     or _first(doc.get("submittedDate_s"))),
            "publisher": (_first(doc.get("journalPublisher_s"))
                          or _first(doc.get("publisher_s"))),
            "doi": _first(doc.get("doiId_s")),
            "hal_id": _extract_hal_id(uri),
        }

        results.append({
            "url": file_main,
            "filename": _build_filename(file_main, uri),
            "extension": "pdf",
            "link_text": title,
            "context": _build_context(doc.get("authFullName_s"), doc.get("abstract_s")),
            "page_title": source_label,
            "source_url": source_url,
            "src_meta": {k: v for k, v in src_meta.items() if v},
        })

    return results


if __name__ == "__main__":
    # Validation minimale : on interroge HAL sur « communs fonciers ».
    test_source = {
        "url": (
            "https://api.archives-ouvertes.fr/search/"
            "?q=communs+fonciers"
            "&fl=title_s,uri_s,fileMain_s,language_s,authFullName_s,abstract_s"
            "&wt=json&rows=20"
        ),
        "label": "TestHAL",
    }
    found = find_documents(test_source)
    print(f"Documents trouvés : {len(found)}")
    for i, item in enumerate(found[:5], start=1):
        print(f"\n--- {i} ---")
        print(f"  titre     : {item['link_text']}")
        print(f"  fileMain_s: {item['url']}")
        print(f"  filename  : {item['filename']}")
