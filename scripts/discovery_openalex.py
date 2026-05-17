#!/usr/bin/env python3
"""
discovery_openalex.py — Découverte de nouveaux articles via l'API OpenAlex.

OpenAlex agrège HAL, arXiv, JSTOR, et 200+ sources scientifiques. L'API est
gratuite et sans clé (User-Agent avec mailto recommandé pour le 'polite pool').

Pour chaque core_concept défini dans config/concepts.yml (en FR/EN/ES), on
interroge OpenAlex avec is_oa:true (open access) et on ajoute les nouvelles
références à discovery/candidates.yml en mode merge idempotent.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlparse

import requests
import yaml

# ── Constantes ────────────────────────────────────────────────────────────────
API_URL = "https://api.openalex.org/works"
USER_AGENT = "LibraryBot/1.0 (mailto:cedric.mabilotte@gmail.com)"
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = 30
DELAY_BETWEEN_QUERIES = 1.0  # politesse envers l'API publique
ABSTRACT_TRUNCATE = 300

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONCEPTS = ROOT / "config" / "concepts.yml"
DEFAULT_CANDIDATES = ROOT / "discovery" / "candidates.yml"
DEFAULT_CATALOG = ROOT / "synopsis" / "catalog.json"


# ── Helpers : merge idempotent du fichier candidates.yml ──────────────────────
def _now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return _dt.date.today().isoformat()


def _load_candidates(path: Path) -> dict:
    """Charge le YAML existant ou retourne une structure vide."""
    if not path.exists():
        return {"last_updated": _now_iso(), "total_candidates": 0, "candidates": []}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("candidates", [])
    return data


def _save_candidates(path: Path, data: dict) -> None:
    """Écrit le YAML, parent créé si besoin."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = _now_iso()
    data["total_candidates"] = len(data.get("candidates", []))
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _merge_candidate(existing: list[dict], new_cand: dict) -> None:
    """Merge idempotent : si l'URL existe déjà, on incrémente seen_count
    et on ajoute la nouvelle entrée found_from sans dupliquer."""
    for cand in existing:
        if cand.get("url") == new_cand["url"]:
            cand["seen_count"] = cand.get("seen_count", 1) + 1
            cand["last_seen"] = new_cand["last_seen"]
            for ff in new_cand.get("found_from", []):
                if ff not in cand.get("found_from", []):
                    cand.setdefault("found_from", []).append(ff)
            return
    existing.append(new_cand)


def _known_dois_from_catalog(catalog_path: Path) -> set[str]:
    """Récupère les DOIs déjà connus dans le catalog (pour ne pas re-proposer)."""
    if not catalog_path.exists():
        return set()
    try:
        with catalog_path.open("r", encoding="utf-8") as f:
            cat = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set()
    dois: set[str] = set()
    for doc in (cat.get("docs") or {}).values():
        doi = (doc.get("doi") or "").lower().strip()
        if doi:
            dois.add(doi)
    return dois


# ── Concepts → requêtes ───────────────────────────────────────────────────────
def _load_queries_from_concepts(concepts_path: Path) -> list[tuple[str, str]]:
    """Lit ontology.core_concepts[].equivalents.{fr,en,es} et retourne
    une liste de (concept_name, query_term) à interroger."""
    with concepts_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    queries: list[tuple[str, str]] = []
    for c in (cfg.get("ontology") or {}).get("core_concepts") or []:
        name = c.get("name", "")
        eq = c.get("equivalents") or {}
        # On prend le 1er équivalent de chaque langue pour limiter le bruit.
        for lang in ("fr", "en", "es"):
            terms = eq.get(lang) or []
            if terms:
                queries.append((name, terms[0]))
    return queries


# ── Appel API ─────────────────────────────────────────────────────────────────
def query_openalex(query: str, max_results: int = 25,
                   year_from: Optional[int] = None) -> list[dict]:
    """Retourne [{"title", "authors", "year", "doi", "url_oa", "abstract"}].
    Filtre les résultats sans OA URL.
    """
    params = {
        "search": query,
        "filter": "is_oa:true" + (f",from_publication_date:{year_from}-01-01"
                                  if year_from else ""),
        "per_page": str(min(max_results, 50)),
    }
    try:
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        payload = r.json()
    except (requests.RequestException, ValueError):
        return []

    out: list[dict] = []
    for w in payload.get("results", []) or []:
        # url_oa : meilleure URL OA disponible (PDF si présent, sinon page).
        oa_loc = (w.get("best_oa_location") or {})
        url_oa = oa_loc.get("pdf_url") or oa_loc.get("landing_page_url") or ""
        if not url_oa:
            continue
        # Reconstruit l'abstract depuis l'index inversé (format OpenAlex).
        abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))
        authors = [a.get("author", {}).get("display_name", "")
                   for a in (w.get("authorships") or [])][:5]
        out.append({
            "title": w.get("title") or "",
            "authors": ", ".join(a for a in authors if a),
            "year": w.get("publication_year"),
            "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(),
            "url_oa": url_oa,
            "abstract": (abstract or "")[:ABSTRACT_TRUNCATE],
        })
    return out[:max_results]


def _reconstruct_abstract(inverted: Optional[dict]) -> str:
    """OpenAlex stocke les abstracts en index inversé {mot: [positions]}."""
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


# ── Orchestration ─────────────────────────────────────────────────────────────
def discover_from_openalex(concepts_path: Path = DEFAULT_CONCEPTS,
                           candidates_path: Path = DEFAULT_CANDIDATES,
                           results_per_concept: int = 20) -> dict:
    """Boucle sur tous les core_concepts (FR+EN+ES) et alimente candidates.yml.
    Skip les DOI déjà présents dans le catalog."""
    queries = _load_queries_from_concepts(concepts_path)
    known_dois = _known_dois_from_catalog(DEFAULT_CATALOG)
    data = _load_candidates(candidates_path)

    new_count = 0
    for concept, term in queries:
        works = query_openalex(term, max_results=results_per_concept)
        for w in works:
            if w["doi"] and w["doi"] in known_dois:
                continue
            url = w["url_oa"]
            cand = {
                "url": url,
                "type": "openalex",
                "found_from": [{
                    "source": f"OpenAlex query '{term}' (concept: {concept})",
                    "context": (w["title"] + " — " + w["abstract"])[:300],
                    "timestamp": _now_iso(),
                }],
                "seen_count": 1,
                "domain": urlparse(url).netloc,
                "first_seen": _today(),
                "last_seen": _today(),
                "metadata": {
                    "title": w["title"],
                    "authors": w["authors"],
                    "year": w["year"],
                    "doi": w["doi"],
                },
                "suggested_action": "follow_one_time",
            }
            _merge_candidate(data["candidates"], cand)
            new_count += 1
        time.sleep(DELAY_BETWEEN_QUERIES)

    _save_candidates(candidates_path, data)
    return {"queries": len(queries), "added_or_updated": new_count,
            "total_candidates": data["total_candidates"]}


if __name__ == "__main__":
    res = discover_from_openalex(results_per_concept=10)
    print(json.dumps(res, indent=2, ensure_ascii=False), file=sys.stderr)
