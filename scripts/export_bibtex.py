#!/usr/bin/env python3
"""Exporte le catalog en BibTeX, RIS et CSL JSON (Zotero/EndNote)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
_YEAR_RE = re.compile(r"(19|20)\d{2}")


def _extract_year(doc: dict) -> str:
    """Cherche une année dans le filename ou meta.creationDate, sinon ''."""
    meta = doc.get("meta", {}) or {}
    for src in (meta.get("creationDate"), doc.get("filename", ""),
                doc.get("url", ""), meta.get("pdf_title", "")):
        if not src:
            continue
        m = _YEAR_RE.search(str(src))
        if m:
            return m.group(0)
    return ""


def _extract_author(doc: dict) -> str:
    """Best-effort : meta.pdf_author, sinon premier mot du link_text."""
    meta = doc.get("meta", {}) or {}
    if a := meta.get("pdf_author"):
        return str(a).strip()
    runs = doc.get("runs", []) or []
    if runs:
        link = runs[-1].get("link_text", "") or ""
        m = re.match(r"([A-Z][a-zà-öø-ÿ\-]+(?:\s+[A-Z][a-zà-öø-ÿ\-]+){0,2})", link)
        if m:
            return m.group(1)
    return ""


def _extract_title(doc: dict) -> str:
    """Titre = bulle.titre_accroche > meta.pdf_title > filename."""
    bp = doc.get("bulle")
    if bp:
        p = ROOT / bp
        if p.exists():
            try:
                b = json.loads(p.read_text(encoding="utf-8"))
                if t := b.get("titre_accroche"):
                    return str(t)
            except Exception:
                pass
    meta = doc.get("meta", {}) or {}
    return str(meta.get("pdf_title") or doc.get("filename", "") or "Sans titre")


def _extract_note(doc: dict, max_chars: int = 400) -> str:
    """Synopsis court depuis bulle.teaser ou enrichment.summary."""
    bp = doc.get("bulle")
    if bp:
        p = ROOT / bp
        if p.exists():
            try:
                b = json.loads(p.read_text(encoding="utf-8"))
                if t := b.get("teaser"):
                    return str(t)[:max_chars]
            except Exception:
                pass
    enr = doc.get("enrichment", {}) or {}
    return str(enr.get("summary", ""))[:max_chars]


def _keywords(doc: dict) -> list[str]:
    """Mots-clés depuis enrichment.matched_keywords ou bulle.categorisation."""
    enr = doc.get("enrichment", {}) or {}
    if kw := enr.get("matched_keywords"):
        return list(kw)
    bp = doc.get("bulle")
    if bp:
        p = ROOT / bp
        if p.exists():
            try:
                b = json.loads(p.read_text(encoding="utf-8"))
                if c := b.get("categorisation"):
                    return list(c)
            except Exception:
                pass
    return []


def _bib_escape(s: str) -> str:
    """Échappement minimal pour BibTeX."""
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def _iter_eligible(catalog_path: Path, min_score: int) -> Iterable[tuple[str, dict]]:
    """Itère sur les docs du catalog scorés >= min_score."""
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for doc_id, doc in catalog.get("docs", {}).items():
        if int(doc.get("latest_score", 0)) >= min_score:
            yield doc_id, doc


def export_bibtex(catalog_path: Path, out_path: Path, min_score: int = 7) -> int:
    """Génère un .bib (@misc) avec champs title, author, year, url, note, keywords."""
    entries: list[str] = []
    n = 0
    for doc_id, doc in _iter_eligible(catalog_path, min_score):
        title = _bib_escape(_extract_title(doc))
        author = _bib_escape(_extract_author(doc))
        year = _extract_year(doc)
        url = doc.get("url", "")
        note = _bib_escape(_extract_note(doc))
        kws = ", ".join(_keywords(doc))
        fields = [f"  title = {{{title}}}"]
        if author:
            fields.append(f"  author = {{{author}}}")
        if year:
            fields.append(f"  year = {{{year}}}")
        if url:
            fields.append(f"  url = {{{url}}}")
        if note:
            fields.append(f"  note = {{{note}}}")
        if kws:
            fields.append(f"  keywords = {{{kws}}}")
        entries.append("@misc{" + doc_id + ",\n" + ",\n".join(fields) + "\n}")
        n += 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    return n


def export_ris(catalog_path: Path, out_path: Path, min_score: int = 7) -> int:
    """Format RIS (TY/TI/AU/PY/UR/N1/KW/ER)."""
    chunks: list[str] = []
    n = 0
    for _doc_id, doc in _iter_eligible(catalog_path, min_score):
        lines = ["TY  - GEN", f"TI  - {_extract_title(doc)}"]
        if a := _extract_author(doc):
            lines.append(f"AU  - {a}")
        if y := _extract_year(doc):
            lines.append(f"PY  - {y}")
        if u := doc.get("url"):
            lines.append(f"UR  - {u}")
        if note := _extract_note(doc):
            lines.append(f"N1  - {note}")
        for kw in _keywords(doc):
            lines.append(f"KW  - {kw}")
        lines.append("ER  - ")
        chunks.append("\n".join(lines))
        n += 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    return n


def export_csl_json(catalog_path: Path, out_path: Path, min_score: int = 7) -> int:
    """Format CSL JSON natif Zotero (type 'document')."""
    items: list[dict] = []
    for doc_id, doc in _iter_eligible(catalog_path, min_score):
        item: dict = {
            "id": doc_id,
            "type": "document",
            "title": _extract_title(doc),
            "URL": doc.get("url", ""),
        }
        if a := _extract_author(doc):
            # On scinde grossièrement "Prénom Nom"
            parts = a.rsplit(" ", 1)
            if len(parts) == 2:
                item["author"] = [{"given": parts[0], "family": parts[1]}]
            else:
                item["author"] = [{"literal": a}]
        if y := _extract_year(doc):
            item["issued"] = {"date-parts": [[int(y)]]}
        if note := _extract_note(doc):
            item["note"] = note
        if kws := _keywords(doc):
            item["keyword"] = ", ".join(kws)
        items.append(item)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(items)


if __name__ == "__main__":
    # Validation : exporte les trois formats dans exports/.
    catalog = ROOT / "synopsis" / "catalog.json"
    if not catalog.exists():
        print(f"[export] catalog introuvable: {catalog}", file=sys.stderr)
        sys.exit(1)
    out_dir = ROOT / "exports"
    n_bib = export_bibtex(catalog, out_dir / "catalog.bib")
    n_ris = export_ris(catalog, out_dir / "catalog.ris")
    n_csl = export_csl_json(catalog, out_dir / "catalog.csl.json")
    print(f"[export] BibTeX: {n_bib} | RIS: {n_ris} | CSL JSON: {n_csl}")
    print(f"[export] sortie: {out_dir}")
