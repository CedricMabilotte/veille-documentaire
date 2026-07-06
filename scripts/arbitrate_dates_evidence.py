#!/usr/bin/env python3
"""arbitrate_dates_evidence.py — Rassemble les indices nécessaires pour
arbitrer à la main les dates en confiance moyenne / conflit issues de
`backfill_dates.py` (ne décide de rien lui-même, ne recalcule que des
preuves : extraits de texte avec un mot-clé de publication à proximité
d'une année, pour que l'arbitrage humain/LLM qui suit ait de quoi trancher
sans deviner).

Usage : python3 scripts/arbitrate_dates_evidence.py > /tmp/evidence.json
"""

import json
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import backfill_dates as bd  # noqa: E402

KEYWORD_YEAR_RE = re.compile(
    r"(?:©|copyright|published|first published|first edition|edition|"
    r"printed|imprim[ée]|[ée]dition|publi[ée]|droits? r[ée]serv[ée]s?|"
    r"date de publication)\W{0,40}?(1[5-9]\d{2}|20\d{2})",
    re.IGNORECASE,
)
YEAR_KEYWORD_RE = re.compile(
    r"(1[5-9]\d{2}|20\d{2})\W{0,40}?(?:©|copyright|published|edition|"
    r"printed|imprim[ée]|[ée]dition|publi[ée])",
    re.IGNORECASE,
)


def _evidence_worker(item: tuple[str, dict]) -> dict:
    uid, doc = item
    import pdf_processor
    pdf_path = bd._local_pdf_path(uid, doc)
    snippets = []
    if pdf_path and pdf_path.suffix.lower() == ".pdf" and pdf_processor.validate_pdf(pdf_path):
        text = pdf_processor.extract_text(pdf_path, max_chars=6000,
                                           doc_title=doc.get("title") or "",
                                           skip_cover=False)
        for rx in (KEYWORD_YEAR_RE, YEAR_KEYWORD_RE):
            for m in rx.finditer(text):
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                snippets.append(text[start:end].replace("\n", " ").strip())
    runs = doc.get("runs") or []
    last_run = runs[-1] if runs else {}
    return {
        "uid": uid,
        "title": doc.get("title", ""),
        "url": doc.get("url", ""),
        "filename": doc.get("filename", ""),
        "link_text": last_run.get("link_text", ""),
        "context": last_run.get("context_seen", ""),
        "keyword_year_snippets": snippets[:8],
        "pdf_present": bool(pdf_path),
    }


def main():
    cat_path = ROOT / "synopsis" / "catalog.json"
    with open(cat_path, encoding="utf-8") as f:
        catalog = json.load(f)
    docs = catalog["docs"]

    fiches_uids = {
        f[:-5] for f in os.listdir(ROOT / "site" / "fiches")
        if f.endswith(".html") and len(f) == 13
    }
    todo = [(uid, docs[uid]) for uid in sorted(fiches_uids)
            if uid in docs and not (docs[uid].get("doc_date") or "").strip()]

    with mp.Pool(processes=min(8, max(1, os.cpu_count() or 4))) as pool:
        base_results = pool.map(bd._worker, todo)

    target_uids = {r["uid"] for r in base_results if r["confidence"] in ("moyenne", "conflit")}
    todo2 = [(uid, docs[uid]) for uid in target_uids]

    with mp.Pool(processes=min(8, max(1, os.cpu_count() or 4))) as pool:
        evidence_results = pool.map(_evidence_worker, todo2)

    base_by_uid = {r["uid"]: r for r in base_results}
    merged = []
    for ev in evidence_results:
        base = base_by_uid[ev["uid"]]
        merged.append({**ev, "candidate": base["candidate"],
                        "confidence": base["confidence"],
                        "conflict_years": base["conflict_years"]})

    print(json.dumps(merged, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
