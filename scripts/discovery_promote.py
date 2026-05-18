#!/usr/bin/env python3
"""
discovery_promote.py — Promotion DOI → PDF via Unpaywall.

Pipeline gratuit : extrait les DOIs de `discovery/candidates.yml`, résout via
l'API publique Unpaywall (mailto, 100k req/j), enrichit les candidats Open
Access avec `promoted_pdf_url` + `promoted_metadata`, et peut télécharger les
PDFs (`--download`) vers `docs/` avec validation magic bytes (pdf_processor) +
enregistrement dans `synopsis/catalog.json`. Politesse : 1 s entre 2 requêtes,
cache mémoire sur le DOI, dédup côté YAML et côté catalog.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml

UNPAYWALL_API = "https://api.unpaywall.org/v2"
DEFAULT_EMAIL = "cedric.mabilotte@gmail.com"
HEADERS = {"User-Agent": f"LibraryBot/1.0 (mailto:{DEFAULT_EMAIL})"}
DELAY_BETWEEN_QUERIES = 1.0  # politesse Unpaywall
DOWNLOAD_TIMEOUT = 60

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES = ROOT / "discovery" / "candidates.yml"
DEFAULT_DOCS = ROOT / "docs"
DEFAULT_CATALOG = ROOT / "synopsis" / "catalog.json"

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", flags=re.IGNORECASE)
_UNPAYWALL_CACHE: dict[str, dict[str, Any] | None] = {}


def _now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _norm_doi(raw: str) -> str | None:
    """Extrait et normalise un DOI depuis une chaîne ou une URL doi.org."""
    if not raw:
        return None
    s = raw.strip().strip("/")
    if "doi.org/" in s.lower():
        s = s.split("doi.org/", 1)[1]
    m = _DOI_RE.search(s)
    return m.group(0).rstrip(".,;)") if m else None


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {"candidates": []}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("candidates", [])
    return data


def _save_yaml(path: Path, data: dict) -> None:
    data["last_updated"] = _now_iso()
    data["total_candidates"] = len(data.get("candidates", []))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=140)


def _load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"docs": {}}


def _save_catalog(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _doc_id_for_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]


def _doi_of(cand: dict) -> str | None:
    """DOI d'un candidat : metadata.doi prioritaire, sinon regex URL."""
    meta = cand.get("metadata") or {}
    if isinstance(meta, dict):
        d = _norm_doi(meta.get("doi", "") or "")
        if d:
            return d
    return _norm_doi(cand.get("url", "") or "")


def extract_dois(candidates_path: Path = DEFAULT_CANDIDATES) -> list[dict]:
    """Retourne les candidats avec DOI extractible (metadata.doi ou regex URL)."""
    data = _load_yaml(candidates_path)
    return [{"doi": _doi_of(c), "candidate": c}
            for c in data.get("candidates", []) if _doi_of(c)]


def resolve_doi_unpaywall(doi: str,
                           email: str = DEFAULT_EMAIL,
                           timeout: int = 15) -> dict | None:
    """Résout un DOI via Unpaywall. Retourne un dict OA exploitable ou None.
    Conditions : is_oa True ET best_oa_location.url_for_pdf renseigné.
    """
    if doi in _UNPAYWALL_CACHE:
        return _UNPAYWALL_CACHE[doi]
    try:
        r = requests.get(f"{UNPAYWALL_API}/{doi}", params={"email": email},
                         headers=HEADERS, timeout=timeout)
    except requests.RequestException:
        _UNPAYWALL_CACHE[doi] = None
        return None
    if r.status_code != 200:
        _UNPAYWALL_CACHE[doi] = None
        return None
    try:
        payload = r.json()
    except ValueError:
        _UNPAYWALL_CACHE[doi] = None
        return None
    is_oa = bool(payload.get("is_oa"))
    best = payload.get("best_oa_location") or {}
    pdf_url = best.get("url_for_pdf") or ""
    if not (is_oa and pdf_url):
        _UNPAYWALL_CACHE[doi] = None
        return None
    out = {"url_for_pdf": pdf_url, "url": best.get("url") or "",
           "title": payload.get("title") or "",
           "journal": payload.get("journal_name") or "", "is_oa": is_oa,
           "published_date": payload.get("published_date") or "",
           "genre": payload.get("genre") or "", "doi": doi}
    _UNPAYWALL_CACHE[doi] = out
    return out


def promote_candidates(candidates_path: Path = DEFAULT_CANDIDATES,
                        limit: int = 100,
                        update_in_place: bool = True) -> dict:
    """Promeut les candidats DOI via Unpaywall (sans télécharger).

    Pour chaque candidat avec DOI non promu : appelle Unpaywall ; si OA + PDF
    direct, ajoute promoted_pdf_url + promoted_at + promoted_metadata.
    Retourne {processed, promoted, skipped, errors, total_dois_in_file, examples}.
    """
    data = _load_yaml(candidates_path)
    processed = promoted = skipped = errors = queried = 0
    examples: list[dict] = []
    total_dois = sum(1 for c in data.get("candidates", []) if _doi_of(c))

    for cand in data.get("candidates", []):
        if queried >= limit:
            break
        if cand.get("promoted_pdf_url"):
            skipped += 1
            continue
        doi = _doi_of(cand)
        if not doi:
            continue
        processed += 1
        queried += 1
        if queried > 1:
            time.sleep(DELAY_BETWEEN_QUERIES)
        try:
            info = resolve_doi_unpaywall(doi)
        except Exception:
            errors += 1
            continue
        if info is None:
            continue

        cand["promoted_pdf_url"] = info["url_for_pdf"]
        cand["promoted_at"] = _now_iso()
        cand["promoted_metadata"] = {
            "doi": info["doi"], "title": info["title"],
            "journal": info["journal"], "published_date": info["published_date"],
            "genre": info["genre"], "html_url": info["url"], "source": "unpaywall",
        }
        promoted += 1
        if len(examples) < 10:
            examples.append({"doi": info["doi"], "title": info["title"][:120],
                             "pdf": info["url_for_pdf"]})

    if update_in_place and promoted > 0:
        _save_yaml(candidates_path, data)
    return {"processed": processed, "promoted": promoted, "skipped": skipped,
            "errors": errors, "total_dois_in_file": total_dois,
            "examples": examples}


def download_promoted(candidates_path: Path = DEFAULT_CANDIDATES,
                       docs_dir: Path = DEFAULT_DOCS,
                       catalog_path: Path = DEFAULT_CATALOG,
                       limit: int = 50) -> dict:
    """Télécharge les PDFs promus, valide via pdf_processor, dédup via catalog
    URLs et register_pdf, ajoute au catalog source="discovery_promoted".
    Retour : {downloaded, skipped, failed, details}.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pdf_processor import validate_pdf, BROWSER_HEADERS  # type: ignore
    from dedup import register_pdf  # type: ignore

    data = _load_yaml(candidates_path)
    catalog = _load_catalog(catalog_path)
    catalog.setdefault("docs", {})
    docs_dir.mkdir(parents=True, exist_ok=True)
    downloaded = skipped = failed = done = 0
    details: list[dict] = []
    known_urls = {d.get("url") for d in catalog["docs"].values() if d.get("url")}

    for cand in data.get("candidates", []):
        if done >= limit:
            break
        pdf_url = cand.get("promoted_pdf_url")
        if not pdf_url:
            continue
        if pdf_url in known_urls:
            skipped += 1
            continue
        done += 1
        doc_id = _doc_id_for_url(pdf_url)
        tail = urlparse(pdf_url).path.rsplit("/", 1)[-1] or "paper.pdf"
        safe_tail = re.sub(r"[^A-Za-z0-9._-]", "_", tail)[:80]
        if not safe_tail.lower().endswith(".pdf"):
            safe_tail += ".pdf"
        dest = docs_dir / f"{doc_id}_{safe_tail}"

        try:
            sess = requests.Session()
            sess.headers.update(BROWSER_HEADERS)
            r = sess.get(pdf_url, timeout=DOWNLOAD_TIMEOUT,
                         stream=True, allow_redirects=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.RequestException as e:
            failed += 1
            details.append({"url": pdf_url, "error": f"requests: {e}"})
            dest.unlink(missing_ok=True) if dest.exists() else None
            continue

        if not validate_pdf(dest):
            failed += 1
            details.append({"url": pdf_url, "error": "not_a_valid_pdf"})
            dest.unlink(missing_ok=True)
            continue

        try:
            register_pdf(dest, doc_id, catalog_path=catalog_path)
        except Exception:
            pass  # best-effort : dédup non bloquant

        meta = cand.get("promoted_metadata") or {}
        now = _now_iso()
        saved_as = str(dest.relative_to(ROOT)) if dest.is_relative_to(ROOT) else str(dest)
        catalog["docs"][doc_id] = {
            "id": doc_id, "url": pdf_url, "filename": dest.name, "format": "pdf",
            "source": "discovery_promoted", "first_seen": now, "latest_run": now,
            "latest_score": None, "downloaded": True, "saved_as": saved_as,
            "title": meta.get("title", ""), "journal": meta.get("journal", ""),
            "doi": meta.get("doi", ""),
            "published_date": meta.get("published_date", ""), "runs": [],
        }
        downloaded += 1
        details.append({"url": pdf_url, "saved_as": dest.name})

    _save_catalog(catalog_path, catalog)
    return {"downloaded": downloaded, "skipped": skipped, "failed": failed,
            "details": details[:20]}


if __name__ == "__main__":
    args = set(sys.argv[1:])
    print(f"[discovery_promote] candidates: {DEFAULT_CANDIDATES}")
    print("[discovery_promote] début promotion (limit=50) …")
    report = promote_candidates(limit=50, update_in_place=True)
    print("\n── Rapport promotion ──")
    for k in ("total_dois_in_file", "processed", "promoted", "skipped", "errors"):
        print(f"  {k:<22s}: {report[k]}")
    if report["examples"]:
        print("\n  Exemples de promotions réussies :")
        for ex in report["examples"][:5]:
            print(f"   • {ex['title'] or '(sans titre)'}")
            print(f"     DOI={ex['doi']}  →  {ex['pdf']}")
    if "--download" in args:
        print("\n[discovery_promote] téléchargement (limit=20) …")
        dl = download_promoted(limit=20)
        print("\n── Rapport téléchargement ──")
        for k in ("downloaded", "skipped", "failed"):
            print(f"  {k:<22s}: {dl[k]}")
        for d in dl["details"][:5]:
            print(f"   • {d['url']}  →  {d.get('saved_as') or d.get('error')}")
