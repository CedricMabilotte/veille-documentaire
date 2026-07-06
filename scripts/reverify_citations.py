#!/usr/bin/env python3
"""reverify_citations.py — Recalcule `verified` sur toutes les citations du
catalogue (enrichment.citations) ET des bulles éditoriales (citations_phares),
et écrit le résultat.

Politique de sourçage (demande explicite de Ced, 6 juillet 2026) : une
citation qui ne peut pas être confirmée dans le texte source reste MASQUÉE
côté public tant qu'elle n'est pas confirmée. Ce script ne masque rien
lui-même (c'est `fiche.html` / `_prerender_fiches` qui filtrent sur
`verified === true`) — il se contente de calculer, pour chaque citation, la
valeur `verified` la plus à jour possible :

  - PDF local valide présent  → verify_citations() (recherche littérale
    tolérante, cf. synopsis_enricher) contre le texte quasi-intégral.
  - PDF absent / invalide / non-PDF → `verified = False` explicitement :
    on ne peut rien confirmer maintenant, donc on ne publie pas — mais rien
    n'est supprimé, une future récupération du PDF permettra de re-confirmer.

`citations_phares` (bulles) n'a jamais porté de champ `verified` : ce script
lui en ajoute un, calculé de la même façon (les quotes de citations_phares
sont un sous-ensemble édité de enrichment.citations, mais vérifiées
indépendamment ici pour ne pas dépendre d'une correspondance textuelle
exacte entre les deux listes).

Usage :
  python3 scripts/reverify_citations.py            # dry-run, rapport seul
  python3 scripts/reverify_citations.py --apply    # écrit catalog.json + bulles/*.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pdf_processor                            # noqa: E402
from synopsis_enricher import verify_citations   # noqa: E402

MAX_CHARS = 2_000_000


def _local_pdf_path(uid: str, doc: dict) -> Path | None:
    saved_as = doc.get("saved_as")
    if saved_as:
        p = ROOT / saved_as if not os.path.isabs(saved_as) else Path(saved_as)
        if p.exists():
            return p
    fname = doc.get("filename")
    if fname:
        p = ROOT / "docs" / f"{uid}_{fname}"
        if p.exists():
            return p
    return None


def _get_text(uid: str, doc: dict, cache: dict) -> str:
    """Texte PDF quasi-intégral, mis en cache par doc (réutilisé pour les
    citations_phares de la même fiche)."""
    if uid in cache:
        return cache[uid]
    pdf_path = _local_pdf_path(uid, doc)
    text = ""
    if pdf_path and pdf_path.suffix.lower() == ".pdf" and pdf_processor.validate_pdf(pdf_path):
        text = pdf_processor.extract_text(pdf_path, max_chars=MAX_CHARS,
                                           doc_title=doc.get("title") or "",
                                           skip_cover=True)
    cache[uid] = text
    return text


def run(apply: bool) -> dict:
    cat_path = ROOT / "synopsis" / "catalog.json"
    with open(cat_path, encoding="utf-8") as f:
        catalog = json.load(f)
    docs = catalog["docs"]

    text_cache: dict[str, str] = {}
    stats = {"docs_citations": 0, "citations_total": 0,
             "verified_true": 0, "verified_false": 0,
             "bulles_processed": 0, "bulle_citations": 0,
             "bulle_verified_true": 0, "bulle_verified_false": 0}

    for uid, doc in docs.items():
        enrich = doc.get("enrichment")
        if not isinstance(enrich, dict):
            continue
        citations = enrich.get("citations")
        if not isinstance(citations, list) or not citations:
            continue
        stats["docs_citations"] += 1
        text = _get_text(uid, doc, text_cache)
        if text:
            fresh = verify_citations(citations, text)
        else:
            fresh = []
            for c in citations:
                c = dict(c) if isinstance(c, dict) else {"quote": str(c)}
                c["verified"] = False
                c["page_physical"] = None
                fresh.append(c)
        for c in fresh:
            stats["citations_total"] += 1
            if c.get("verified") is True:
                stats["verified_true"] += 1
            else:
                stats["verified_false"] += 1
        if apply:
            enrich["citations"] = fresh

    # ── Bulles (citations_phares) ────────────────────────────────────────
    bulles_dir = ROOT / "bulles"
    site_bulles_dir = ROOT / "site" / "data" / "bulles"
    bulle_updates: dict[str, dict] = {}

    for bf in sorted(bulles_dir.glob("*.json")):
        uid = bf.stem
        with open(bf, encoding="utf-8") as f:
            bulle = json.load(f)
        phares = bulle.get("citations_phares")
        if not isinstance(phares, list) or not phares:
            continue
        doc = docs.get(uid) or {}
        stats["bulles_processed"] += 1
        text = _get_text(uid, doc, text_cache)
        if text:
            fresh = verify_citations(phares, text)
        else:
            fresh = []
            for c in phares:
                c = dict(c) if isinstance(c, dict) else {"quote": str(c)}
                c["verified"] = False
                c["page_physical"] = None
                fresh.append(c)
        for c in fresh:
            stats["bulle_citations"] += 1
            if c.get("verified") is True:
                stats["bulle_verified_true"] += 1
            else:
                stats["bulle_verified_false"] += 1
        bulle["citations_phares"] = fresh
        bulle_updates[uid] = bulle

    print(f"Docs avec citations (enrichment)     : {stats['docs_citations']}")
    print(f"Citations examinées                  : {stats['citations_total']}")
    print(f"  verified=True                      : {stats['verified_true']}")
    print(f"  verified=False (masquées)          : {stats['verified_false']}")
    print(f"Bulles avec citations_phares         : {stats['bulles_processed']}")
    print(f"Citations_phares examinées            : {stats['bulle_citations']}")
    print(f"  verified=True                      : {stats['bulle_verified_true']}")
    print(f"  verified=False (masquées)          : {stats['bulle_verified_false']}")

    if apply:
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"\ncatalog.json réécrit ({cat_path}).")

        for uid, bulle in bulle_updates.items():
            with open(bulles_dir / f"{uid}.json", "w", encoding="utf-8") as f:
                json.dump(bulle, f, ensure_ascii=False, indent=2)
            site_copy = site_bulles_dir / f"{uid}.json"
            if site_copy.exists():
                with open(site_copy, "w", encoding="utf-8") as f:
                    json.dump(bulle, f, ensure_ascii=False, indent=2)
        print(f"{len(bulle_updates)} bulles réécrites (bulles/ + site/data/bulles/ si présent).")
    else:
        print("\n(dry-run — rien n'a été écrit ; relancer avec --apply)")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(args.apply)
