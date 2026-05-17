#!/usr/bin/env python3
"""
discovery_semantic_scholar.py — Recommandations citationnelles.

Semantic Scholar fournit deux endpoints utiles sans clé API (quota modéré) :
- /graph/v1/paper/search : recherche full-text par requête
- /recommendations/v1/papers/forpaper/<paper_id> : papers similaires

Stratégie : on prend les docs scorés ≥ 8 dans le catalog (les graines de
confiance), on cherche leur paper_id sur Semantic Scholar via fuzzy match
titre, puis on demande des recommandations. Les recos sont ajoutées à
discovery/candidates.yml.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse

import requests
import yaml

# ── Constantes ────────────────────────────────────────────────────────────────
SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
RECO_URL = "https://api.semanticscholar.org/recommendations/v1/papers/forpaper"
HEADERS = {"User-Agent": "LibraryBot/1.0 (mailto:cedric.mabilotte@gmail.com)"}
TIMEOUT = 30
DELAY = 1.5  # politesse : sans clé, le quota est strict (env. 100 req/5 min)
FUZZY_MIN_RATIO = 0.5  # ratio min de mots communs pour valider un match
FIELDS_SEARCH = "paperId,title,authors,year,externalIds,openAccessPdf,abstract"
FIELDS_RECO = FIELDS_SEARCH

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = ROOT / "synopsis" / "catalog.json"
DEFAULT_CANDIDATES = ROOT / "discovery" / "candidates.yml"


# ── Helpers communs candidates.yml ────────────────────────────────────────────
def _now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return _dt.date.today().isoformat()


def _load_candidates(path: Path) -> dict:
    if not path.exists():
        return {"last_updated": _now_iso(), "total_candidates": 0, "candidates": []}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"candidates": []}


def _save_candidates(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = _now_iso()
    data["total_candidates"] = len(data.get("candidates", []))
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _merge_candidate(existing: list[dict], new_cand: dict) -> None:
    for cand in existing:
        if cand.get("url") == new_cand["url"]:
            cand["seen_count"] = cand.get("seen_count", 1) + 1
            cand["last_seen"] = new_cand["last_seen"]
            for ff in new_cand.get("found_from", []):
                if ff not in cand.get("found_from", []):
                    cand.setdefault("found_from", []).append(ff)
            return
    existing.append(new_cand)


# ── Fuzzy match titre ─────────────────────────────────────────────────────────
def _tokenize(s: str) -> set[str]:
    """Tokenize ultra-simple : abaisse, garde mots de ≥ 4 lettres."""
    return {w for w in re.findall(r"[a-zA-Zà-ÿ]+", s.lower()) if len(w) >= 4}


def _ratio(a: str, b: str) -> float:
    """Ratio de mots communs entre deux titres (Jaccard)."""
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ── API ───────────────────────────────────────────────────────────────────────
def search_papers(query: str, limit: int = 20) -> list[dict]:
    """Recherche basique de papers par requête full-text."""
    params = {"query": query, "limit": str(min(limit, 100)), "fields": FIELDS_SEARCH}
    try:
        r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 429:
            time.sleep(5)
            return []
        r.raise_for_status()
        return r.json().get("data") or []
    except (requests.RequestException, ValueError):
        return []


def recommend_from(paper_id: str, limit: int = 10) -> list[dict]:
    """Recommandations à partir d'un paper Semantic Scholar (DOI: ou s2 ID)."""
    url = f"{RECO_URL}/{quote(paper_id, safe=':')}"
    params = {"limit": str(min(limit, 100)), "fields": FIELDS_RECO}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 429:
            time.sleep(5)
            return []
        r.raise_for_status()
        return r.json().get("recommendedPapers") or []
    except (requests.RequestException, ValueError):
        return []


# ── Catalog seed loader ───────────────────────────────────────────────────────
def _high_score_seeds(catalog_path: Path, min_score: int) -> list[dict]:
    """Retourne les docs scorés ≥ min_score avec un titre exploitable."""
    if not catalog_path.exists():
        return []
    try:
        with catalog_path.open("r", encoding="utf-8") as f:
            cat = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    out: list[dict] = []
    for doc in (cat.get("docs") or {}).values():
        if (doc.get("latest_score") or 0) >= min_score:
            # Préfère meta.pdf_title (extrait du PDF) au filename brut.
            meta = doc.get("meta") or {}
            title = (meta.get("pdf_title") or doc.get("title")
                     or doc.get("filename", ""))
            if title:
                out.append({"title": title, "doi": doc.get("doi", ""),
                            "id": doc.get("id", "")})
    return out


def _best_match(query_title: str, hits: list[dict]) -> Optional[dict]:
    """Choisit le meilleur match parmi les résultats de search_papers."""
    best, best_r = None, 0.0
    for h in hits:
        r = _ratio(query_title, h.get("title") or "")
        if r > best_r:
            best, best_r = h, r
    return best if best and best_r >= FUZZY_MIN_RATIO else None


# ── Orchestration ─────────────────────────────────────────────────────────────
def _paper_to_url(paper: dict) -> str:
    """Préfère le PDF OA, sinon construit l'URL DOI ou la page S2."""
    oa = paper.get("openAccessPdf") or {}
    if oa.get("url"):
        return oa["url"]
    doi = (paper.get("externalIds") or {}).get("DOI")
    if doi:
        return f"https://doi.org/{doi}"
    return f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"


def discover_from_semantic_scholar(catalog_path: Path = DEFAULT_CATALOG,
                                    candidates_path: Path = DEFAULT_CANDIDATES,
                                    seeds_min_score: int = 8) -> dict:
    """Pour chaque doc scoré ≥ seeds_min_score, cherche le paper sur S2,
    puis recommande 10 papers similaires. Ajoute aux candidats."""
    seeds = _high_score_seeds(catalog_path, seeds_min_score)
    data = _load_candidates(candidates_path)
    new_count, matched, unmatched = 0, 0, 0

    for seed in seeds:
        # Match par DOI si dispo, sinon par titre (fuzzy).
        paper_id = None
        if seed["doi"]:
            paper_id = f"DOI:{seed['doi']}"
        else:
            hits = search_papers(seed["title"], limit=5)
            match = _best_match(seed["title"], hits)
            if match:
                paper_id = match["paperId"]
        time.sleep(DELAY)
        if not paper_id:
            unmatched += 1
            continue
        matched += 1
        recos = recommend_from(paper_id, limit=10)
        time.sleep(DELAY)
        for p in recos:
            url = _paper_to_url(p)
            cand = {
                "url": url,
                "type": "semantic_scholar",
                "found_from": [{
                    "source": f"S2 recommendation from '{seed['title'][:80]}'",
                    "context": (p.get("abstract") or p.get("title") or "")[:300],
                    "timestamp": _now_iso(),
                }],
                "seen_count": 1,
                "domain": urlparse(url).netloc,
                "first_seen": _today(),
                "last_seen": _today(),
                "metadata": {
                    "title": p.get("title") or "",
                    "authors": ", ".join(a.get("name", "")
                                          for a in (p.get("authors") or []))[:200],
                    "year": p.get("year"),
                    "doi": (p.get("externalIds") or {}).get("DOI", ""),
                },
                "suggested_action": "follow_one_time",
            }
            _merge_candidate(data["candidates"], cand)
            new_count += 1

    _save_candidates(candidates_path, data)
    return {"seeds": len(seeds), "matched": matched, "unmatched": unmatched,
            "added_or_updated": new_count,
            "total_candidates": data["total_candidates"]}


if __name__ == "__main__":
    res = discover_from_semantic_scholar(seeds_min_score=8)
    print(json.dumps(res, indent=2, ensure_ascii=False), file=sys.stderr)
