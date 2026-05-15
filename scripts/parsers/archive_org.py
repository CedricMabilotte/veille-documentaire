#!/usr/bin/env python3
"""
Parser pour l'API JSON d'Archive.org (advancedsearch.php).

Stratégie : on interroge advancedsearch.php (qui retourne un JSON listant des items),
puis on construit l'URL de téléchargement directe à l'aveugle selon la convention
Archive.org : https://archive.org/download/<identifier>/<identifier>.pdf

Si l'URL 404, le téléchargement échouera côté download_file — c'est géré ailleurs.
"""

import json
import requests
from typing import Any

# ── Constantes ────────────────────────────────────────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
TIMEOUT = 20
MAX_ITEMS = 50
CONTEXT_MAX_LEN = 400
DOWNLOAD_BASE = "https://archive.org/download"


def _flatten(value: Any) -> str:
    """Aplatit une valeur potentiellement liste (Archive.org renvoie souvent des listes)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    return str(value)


def _truncate(text: str, max_len: int = CONTEXT_MAX_LEN) -> str:
    """Tronque proprement à max_len caractères."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _extract_docs(payload: dict) -> list[dict]:
    """Extrait la liste des docs du JSON Archive.org (gère deux variantes d'API)."""
    response = payload.get("response", {})
    # Variante 1 : response.docs (format Solr classique)
    if isinstance(response, dict) and "docs" in response:
        return response.get("docs", []) or []
    # Variante 2 : response.results.docs (format plus récent)
    if isinstance(response, dict) and "results" in response:
        results = response.get("results", {})
        if isinstance(results, dict):
            return results.get("docs", []) or []
    return []


def find_documents(source: dict) -> list[dict]:
    """
    Interroge l'API advancedsearch.php d'Archive.org et retourne une liste
    de documents (PDFs) téléchargeables au format standardisé.
    """
    url = source.get("url", "")
    label = source.get("label", "")

    if not url:
        return []

    # ── Requête HTTP ──────────────────────────────────────────────────────────
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ⚠  Archive.org : requête échouée ({e})")
        return []

    # ── Parsing JSON (robuste face aux malformés) ─────────────────────────────
    try:
        payload = resp.json()
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠  Archive.org : JSON malformé ({e})")
        return []

    docs = _extract_docs(payload)
    if not docs:
        return []

    # ── Construction des résultats ────────────────────────────────────────────
    results: list[dict] = []
    seen_identifiers: set[str] = set()

    for doc in docs[:MAX_ITEMS]:
        identifier = _flatten(doc.get("identifier")).strip()
        if not identifier or identifier in seen_identifiers:
            continue
        seen_identifiers.add(identifier)

        title = _flatten(doc.get("title")) or identifier
        creator = _flatten(doc.get("creator"))
        description = _flatten(doc.get("description"))

        # Contexte = creator + description, tronqué
        context_parts = [p for p in (creator, description) if p]
        context = _truncate(" — ".join(context_parts))

        # URL "à l'aveugle" : convention Archive.org
        filename = f"{identifier}.pdf"
        pdf_url = f"{DOWNLOAD_BASE}/{identifier}/{filename}"

        results.append({
            "url": pdf_url,
            "filename": filename,
            "extension": "pdf",
            "link_text": title,
            "context": context,
            "page_title": label,
            "source_url": url,
        })

    return results


# ── Validation ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_source = {
        "url": (
            "https://archive.org/advancedsearch.php"
            "?q=collection%3Afolksonomy_anarchism"
            "&fl%5B%5D=identifier&fl%5B%5D=title"
            "&fl%5B%5D=creator&fl%5B%5D=description"
            "&output=json&rows=20"
        ),
        "label": "TestAnarch",
    }

    docs = find_documents(test_source)
    print(f"Nombre de documents trouvés : {len(docs)}")
    print("─" * 60)
    for i, d in enumerate(docs[:5], 1):
        print(f"\n[{i}] {d['link_text']}")
        print(f"    URL      : {d['url']}")
        print(f"    Filename : {d['filename']}")
        print(f"    Context  : {d['context'][:120]}")
