#!/usr/bin/env python3
"""
discovery_bibliography.py — Candidats issus des références bibliographiques.

Exploite le champ `references[]` du catalog (rempli par bibliography_extractor)
pour découvrir de nouveaux candidats :

  1. Si la ref contient déjà une URL/DOI : candidat direct (type=bibliography).
  2. Sinon : on interroge Crossref (api.crossref.org/works?query=…) avec
     auteur+titre pour récupérer DOI + URL open access.
  3. URL contenant "fileMain" ou ".pdf" → candidat haute confiance.
  4. Sinon : ref enregistrée comme "à explorer manuellement".

Idempotent : merge avec discovery/candidates.yml existant.
Stdlib + requests uniquement.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

# Helper YAML commun (fichier voisin)
sys.path.insert(0, str(Path(__file__).parent))
from discovery_external_links import (   # noqa: E402
    load_candidates, save_candidates, merge_candidate,
)

CROSSREF_API = "https://api.crossref.org/works"
USER_AGENT = "LibraryBot/1.0 (mailto:cedric.mabilotte@gmail.com)"
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)\"'<>]+", re.IGNORECASE)


def _crossref_lookup(author: str | None, title: str | None,
                     timeout: int = 8) -> dict | None:
    """Interroge Crossref avec auteur+titre. Retourne le 1er hit ou None."""
    q_parts = [p for p in [title, author] if p]
    if not q_parts:
        return None
    params = {"query": " ".join(q_parts), "rows": 1}
    try:
        r = requests.get(CROSSREF_API, params=params,
                         headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if r.status_code != 200:
            return None
        items = r.json().get("message", {}).get("items", [])
        return items[0] if items else None
    except Exception as e:
        print(f"  ! Crossref lookup failed: {e}")
        return None


def _best_url_from_crossref(item: dict) -> tuple[str | None, str]:
    """Choisit la meilleure URL à partir d'une réponse Crossref.

    Retourne (url, confidence) où confidence ∈ {"high", "medium", "low"}.
    """
    # 1) Liens "fileMain" / pdf open access
    for link in item.get("link", []):
        url = link.get("URL", "")
        ct = (link.get("content-type") or "").lower()
        if "fileMain" in (link.get("intended-application") or "") \
                or "pdf" in ct or url.lower().endswith(".pdf"):
            return url, "high"
    # 2) Lien générique
    for link in item.get("link", []):
        if link.get("URL"):
            return link["URL"], "medium"
    # 3) DOI → URL stable
    doi = item.get("DOI")
    if doi:
        return f"https://doi.org/{doi}", "low"
    return None, "low"


def _extract_inline_url_doi(raw: str) -> tuple[str | None, str | None]:
    """Cherche directement une URL ou un DOI dans la ref brute."""
    url_m = URL_RE.search(raw or "")
    doi_m = DOI_RE.search(raw or "")
    url = url_m.group(0).rstrip(".,);") if url_m else None
    doi = doi_m.group(0).rstrip(".,);") if doi_m else None
    return url, doi


def _build_context(ref: dict) -> str:
    """Texte court décrivant la ref (pour le YAML)."""
    parts = []
    if ref.get("author"):
        parts.append(ref["author"])
    if ref.get("year"):
        parts.append(f"({ref['year']})")
    if ref.get("title"):
        parts.append(ref["title"][:120])
    return " ".join(parts) or (ref.get("raw") or "")[:160]


def discover_from_bibliography(catalog_path: Path,
                               candidates_path: Path,
                               limit_per_doc: int = 5,
                               limit_total: int = 100,
                               min_score: int = 7,
                               sleep_between: float = 0.5) -> dict:
    """Parcourt le catalog, prend les references[] des docs scorés ≥ min_score,
    interroge Crossref si pas d'URL, écrit dans candidates_path.

    Retourne {"added": int, "merged": int, "skipped": int}.
    """
    if not catalog_path.exists():
        return {"added": 0, "merged": 0, "skipped": 0, "error": "no_catalog"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})
    candidates = load_candidates(candidates_path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    added = merged = skipped = 0
    total_processed = 0

    for doc_id, doc in docs.items():
        if total_processed >= limit_total:
            break
        if (doc.get("latest_score") or 0) < min_score:
            continue
        refs = doc.get("references") or []
        if not refs:
            continue

        for ref in refs[:limit_per_doc]:
            if total_processed >= limit_total:
                break
            total_processed += 1

            # 1. URL/DOI inline ?
            url, doi = _extract_inline_url_doi(ref.get("raw", ""))
            confidence = "high" if (url and ".pdf" in url.lower()) else "medium"

            # 2. Sinon Crossref
            if not url:
                hit = _crossref_lookup(ref.get("author"), ref.get("title"))
                time.sleep(sleep_between)
                if hit:
                    url, confidence = _best_url_from_crossref(hit)
                    if not doi:
                        doi = hit.get("DOI")

            # 3. Pas d'URL → ref enregistrée comme "à explorer"
            if not url:
                skipped += 1
                continue

            domain = urlparse(url).netloc.lower()
            suggested = "add_source" if confidence == "high" else "follow_one_time"
            entry = {
                "url": url,
                "type": "bibliography",
                "domain": domain,
                "first_seen": today,
                "last_seen": today,
                "seen_count": 1,
                "suggested_action": suggested,
                "notes": f"confidence={confidence}"
                         + (f"; doi={doi}" if doi else ""),
                "found_from": [{
                    "doc_id": doc_id,
                    "context": _build_context(ref),
                    "page": ref.get("page"),
                }],
            }
            was_new = merge_candidate(candidates, entry, today)
            if was_new:
                added += 1
            else:
                merged += 1

    save_candidates(candidates_path, candidates)
    return {"added": added, "merged": merged, "skipped": skipped,
            "total_processed": total_processed}


# ── Validation CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    catalog = root / "synopsis" / "catalog.json"
    cand_path = root / "discovery" / "candidates.yml"
    cand_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[discovery_bibliography] catalog={catalog}")
    stats = discover_from_bibliography(catalog, cand_path,
                                       limit_per_doc=3, limit_total=20)
    print(f"  → {stats}")
    print(f"  candidates.yml : {cand_path}")
