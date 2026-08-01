#!/usr/bin/env python3
"""
discovery_footnotes.py — Capture des URLs/DOI dans les notes de bas de page.

Complète bibliography_extractor en ratissant les NBP, qui contiennent
souvent des URLs et des citations courtes oubliées par l'extraction biblio
classique.

Stratégie :
  1. Lire le PDF page par page (PyMuPDF).
  2. Repérer les lignes d'apparence NBP :
     - début par superscript Unicode (¹²³⁴⁵⁶⁷⁸⁹)
     - début par "N " ou "N. " (N=1-3 chiffres) puis majuscule
  3. Extraire URL (http[s]) et DOI (10.xxxx/yyy) dans le texte de la NBP.
  4. Pour chaque (url|doi) → 1 candidat type=footnote dans candidates.yml.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import fitz  # PyMuPDF
    _PYMUPDF_OK = True
except ImportError:
    _PYMUPDF_OK = False

sys.path.insert(0, str(Path(__file__).parent))
from discovery_external_links import (   # noqa: E402
    load_candidates, save_candidates, merge_candidate,
)

# ── Regex ────────────────────────────────────────────────────────────────────
SUPERSCRIPT = "¹²³⁴⁵⁶⁷⁸⁹⁰"
_FN_SUPERSCRIPT = re.compile(rf"^[{SUPERSCRIPT}]+\s*(.+)$")
_FN_NUMERIC = re.compile(r"^(\d{1,3})[.\)]?\s+([A-ZÉÈÊÂÔÛÇ].+)$")
_URL_RE = re.compile(r"https?://[^\s)\"'<>\]]+", re.IGNORECASE)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)


def _is_footnote_line(line: str, fallback_if_has_url: bool = False) -> str | None:
    """Retourne le texte de la NBP si la ligne ressemble à une NBP, sinon None.

    Si fallback_if_has_url=True, toute ligne contenant une URL/DOI est acceptée
    (utile pour les brochures qui n'utilisent pas de marqueurs explicites).
    """
    line = line.strip()
    if len(line) < 8:
        return None
    m = _FN_SUPERSCRIPT.match(line)
    if m:
        return m.group(1).strip()
    m = _FN_NUMERIC.match(line)
    if m:
        body = m.group(2).strip()
        if len(body) >= 12:
            return body
    # Fallback : ligne contenant directement une URL ou un DOI
    if fallback_if_has_url and (_URL_RE.search(line) or _DOI_RE.search(line)):
        return line
    return None


def extract_footnotes(pdf_path: Path) -> list[dict]:
    """Retourne [{"page", "text", "urls_found", "dois_found"}, ...].

    Best-effort : ne renvoie que les NBP contenant URL ou DOI (les autres
    n'apportent pas de candidat, donc on les ignore ici).
    """
    if not _PYMUPDF_OK or not pdf_path.exists():
        return []
    out: list[dict] = []
    try:
        doc = fitz.open(pdf_path)
        for p in doc:
            text = p.get_text("text") or ""
            # On scanne le dernier tiers de la page (NBP = en bas)
            lines = text.splitlines()
            # Heuristique : NBP probables = lignes du 2e tiers à la fin
            # En mode fallback, on accepte aussi toute ligne contenant URL/DOI.
            start = max(0, int(len(lines) * 0.5))
            for i, ln in enumerate(lines):
                # Marqueurs explicites partout, fallback URL/DOI seulement
                # en bas de page (réduit le bruit du corps de texte).
                in_lower_half = i >= start
                body = _is_footnote_line(ln, fallback_if_has_url=in_lower_half)
                if not body:
                    continue
                urls = [u.rstrip(".,);") for u in _URL_RE.findall(body)]
                dois = [d.rstrip(".,);") for d in _DOI_RE.findall(body)]
                if not urls and not dois:
                    continue
                out.append({
                    "page": p.number + 1,
                    "text": body[:300],
                    "urls_found": urls,
                    "dois_found": dois,
                })
        doc.close()
    except Exception as e:
        print(f"  ! extract_footnotes failed for {pdf_path.name}: {e}")
    return out


def _url_from_doi(doi: str) -> str:
    return f"https://doi.org/{doi}"


def discover_from_footnotes(docs_dir: Path,
                            catalog_path: Path,
                            candidates_path: Path,
                            min_score: int = 0,
                            max_per_pdf: int = 30) -> dict:
    """Pour chaque PDF de docs_dir, extrait les NBP avec URL/DOI et ajoute
    aux candidats type=footnote. min_score filtre via le catalog si présent.

    Retourne {"added": int, "merged": int, "pdfs": int}.
    """
    if not docs_dir.exists():
        return {"added": 0, "merged": 0, "pdfs": 0, "error": "no_docs_dir"}

    catalog_docs: dict = {}
    if catalog_path.exists():
        try:
            catalog_docs = json.loads(catalog_path.read_text(encoding="utf-8"))\
                .get("docs", {})
        except Exception:
            catalog_docs = {}
    # Index doc_id par filename pour retrouver le score
    by_filename = {d.get("filename"): (did, d)
                   for did, d in catalog_docs.items() if d.get("filename")}

    store = load_candidates(candidates_path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    added = merged = pdfs = 0

    for pdf in sorted(docs_dir.glob("*.pdf")):
        # Le filename "réel" dans le catalog = nom sans le préfixe "xxxxxxxx_"
        real_name = pdf.name.split("_", 1)[1] if "_" in pdf.name else pdf.name
        doc_id, doc_meta = by_filename.get(real_name, (pdf.stem, {}))
        score = doc_meta.get("latest_score") or 0
        if score < min_score:
            continue

        notes = extract_footnotes(pdf)
        if not notes:
            continue
        pdfs += 1
        count_for_this_pdf = 0

        for fn in notes:
            if count_for_this_pdf >= max_per_pdf:
                break
            candidates_urls: list[tuple[str, str]] = []  # (url, note)
            for u in fn["urls_found"]:
                candidates_urls.append((u, ""))
            for d in fn["dois_found"]:
                candidates_urls.append((_url_from_doi(d), f"doi={d}"))

            for url, extra_note in candidates_urls:
                count_for_this_pdf += 1
                entry = {
                    "url": url,
                    "type": "footnote",
                    "domain": urlparse(url).netloc.lower(),
                    "first_seen": today,
                    "last_seen": today,
                    "seen_count": 1,
                    "suggested_action": "follow_one_time",
                    "notes": extra_note,
                    "found_from": [{
                        "doc_id": doc_id,
                        "context": fn["text"],
                        "page": fn["page"],
                    }],
                }
                if merge_candidate(store, entry, today):
                    added += 1
                else:
                    merged += 1

    save_candidates(candidates_path, store)
    return {"added": added, "merged": merged, "pdfs": pdfs}


# ── Validation CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    docs_dir = root / "docs"
    catalog = root / "synopsis" / "catalog.json"
    cand_path = root / "discovery" / "candidates.yml"
    cand_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[discovery_footnotes] docs_dir={docs_dir}")
    stats = discover_from_footnotes(docs_dir, catalog, cand_path)
    print(f"  → {stats}")

    # Quick check : extraction sur 1 PDF concret
    sample = next(iter(sorted(docs_dir.glob("*.pdf"))), None)
    if sample:
        fns = extract_footnotes(sample)
        print(f"  [sample] {sample.name} → {len(fns)} NBP avec URL/DOI")
        for fn in fns[:3]:
            print(f"    p.{fn['page']} | urls={fn['urls_found']} "
                  f"| dois={fn['dois_found']}")
            print(f"      txt: {fn['text'][:100]}…")
