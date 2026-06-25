#!/usr/bin/env python3
"""
Script ciblé : télécharge les docs avec score_initial 4-5 non téléchargés,
puis les enrichit directement (sans invoquer Claude CLI — Claude EST le LLM).

Usage : python3 scripts/_download_score45.py
"""

import sys
import json
import hashlib
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pdf_processor
import synopsis_enricher

# ── Chemins ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
CATALOG_PATH = PROJECT_ROOT / "synopsis" / "catalog.json"
DOCS_PATH    = PROJECT_ROOT / "docs"
DOCS_PATH.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}

# Mots-clés thématiques (repris de config/sources.yml via watch.py)
KEYWORDS = [
    "communs fonciers", "propriété d'usage", "libération des terres",
    "paysannerie", "alternatives à la propriété privée",
    "réforme agraire", "sans-terre", "zapatistes", "communs",
    "habitat partagé", "coopérative foncière", "fonds de dotation",
    "usufruit", "bien commun", "land reform", "commons",
    "peasant", "agroécologie", "tierra", "lutte foncière",
]


def file_uid(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def download_file(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    ECHEC téléchargement : {e}")
        return False


def _archive_org_variants(url: str):
    variants = []
    if "archive.org/download/" not in url:
        return variants
    try:
        prefix, rest = url.split("archive.org/download/", 1)
        parts = rest.split("/", 1)
        identifier = parts[0]
        filename = parts[1] if len(parts) > 1 else ""
        base = f"{prefix}archive.org/download/{identifier}"
    except Exception:
        return variants

    if filename:
        if filename.endswith("_text.pdf"):
            variants.append(f"{base}/{filename[:-len('_text.pdf')]}.pdf")
        if filename.endswith("_djvu.txt"):
            variants.append(f"{base}/{filename[:-len('_djvu.txt')]}.pdf")
    canonical = f"{base}/{identifier}.pdf"
    if canonical != url and canonical not in variants:
        variants.append(canonical)
    try:
        meta_url = f"https://archive.org/metadata/{identifier}"
        r = requests.get(meta_url, headers=HEADERS, timeout=8)
        if r.ok:
            data = r.json()
            for fmeta in (data.get("files") or []):
                name = fmeta.get("name", "")
                if name.lower().endswith(".pdf"):
                    candidate = f"{base}/{name}"
                    if candidate != url and candidate not in variants:
                        variants.append(candidate)
                    break
    except Exception as e:
        print(f"    archive.org metadata indisponible : {e}")
    return variants


def download_and_validate(url: str, dest: Path):
    """Retourne (success: bool, status: str)"""
    # HEAD rapide
    head_status = None
    try:
        head = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        head_status = head.status_code
        if head.status_code == 404 and "archive.org/download/" in url:
            variants = _archive_org_variants(url)
            for variant in variants:
                print(f"    Variante archive.org : {variant[:70]}")
                try:
                    vh = requests.head(variant, headers=HEADERS, timeout=8, allow_redirects=True)
                except Exception:
                    continue
                if vh.ok:
                    if download_file(variant, dest) and pdf_processor.validate_pdf(dest):
                        return True, "ok_via_variant"
            return False, "failed_404_after_variants"
    except Exception as e:
        print(f"    HEAD échoué ({e}), tentative download direct")

    if not download_file(url, dest):
        if "archive.org/download/" in url:
            variants = _archive_org_variants(url)
            for variant in variants:
                if download_file(variant, dest) and pdf_processor.validate_pdf(dest):
                    return True, "ok_via_variant"
            if variants:
                return False, "failed_404_after_variants"
        return False, "failed_network"

    if pdf_processor.validate_pdf(dest):
        return True, "ok"

    # Bypass UA navigateur
    print(f"    Faux PDF détecté, bypass UA…")
    ok, err = pdf_processor.redownload_with_bypass(url, dest)
    if ok:
        return True, "ok_via_browser"

    if dest.exists():
        dest.unlink()
    return False, f"failed_invalid ({err})"


def enrich_doc(dest: Path, doc: dict) -> dict:
    """Lit le PDF et génère l'enrichissement via synopsis_enricher."""
    text = pdf_processor.extract_text(dest, max_chars=8000)
    if not text or len(text) < 200:
        return {"error": "pdf_vide_ou_scanne", "char_count": len(text) if text else 0}

    link_text = ""
    if doc.get("runs"):
        link_text = doc["runs"][-1].get("link_text", "") or ""
    title_hint = link_text or doc.get("filename", "")

    print(f"    Texte extrait : {len(text)} chars, enrichissement en cours…")
    enrichment = synopsis_enricher.enrich(text, KEYWORDS, title_hint)
    return enrichment


def main():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    # Identifier les cibles
    targets = []
    for doc_id, doc in catalog["docs"].items():
        si = doc.get("score_initial")
        downloaded = doc.get("downloaded", False)
        url = doc.get("url", "")
        if si is not None and 4 <= si <= 5 and not downloaded and url:
            targets.append(doc)

    print(f"\n=== {len(targets)} docs score 4-5 non téléchargés ===\n")

    downloaded_count = 0
    enriched_count   = 0
    score6plus_count = 0
    failed_count     = 0

    for i, doc in enumerate(targets, 1):
        url      = doc["url"]
        filename = doc.get("filename", "")
        uid      = file_uid(url)
        dest     = DOCS_PATH / f"{uid}_{filename}"

        link_text = ""
        if doc.get("runs"):
            link_text = doc["runs"][-1].get("link_text", "") or ""
        label = link_text or filename

        print(f"[{i}/{len(targets)}] score={doc.get('score_initial')} | {label[:65]}")
        print(f"  URL: {url[:80]}")

        # Déjà présent sur disque ?
        if dest.exists() and pdf_processor.validate_pdf(dest):
            print(f"  Déjà présent sur disque, on enrichit.")
            success, status = True, "already_present"
        else:
            success, status = download_and_validate(url, dest)

        if success:
            downloaded_count += 1
            catalog["docs"][doc["id"]]["downloaded"]       = True
            catalog["docs"][doc["id"]]["saved_as"]         = f"docs/{uid}_{filename}"
            catalog["docs"][doc["id"]]["download_status"]  = status
            print(f"  OK ({status})")

            # Enrichissement
            enrichment = enrich_doc(dest, doc)
            if "error" in enrichment:
                print(f"  Enrichissement impossible : {enrichment['error']}")
                catalog["docs"][doc["id"]]["enrichment"] = enrichment
            else:
                rs = enrichment.get("relevance_score") or enrichment.get("score_final")
                catalog["docs"][doc["id"]]["enrichment"] = enrichment
                if isinstance(rs, (int, float)):
                    catalog["docs"][doc["id"]]["score_final"] = int(rs)
                    enriched_count += 1
                    print(f"  score_final={rs} | summary={len(enrichment.get('summary',''))} chars")
                    if int(rs) >= 6:
                        score6plus_count += 1
                        print(f"  *** PUBLIABLE (score_final >= 6) ***")
        else:
            failed_count += 1
            catalog["docs"][doc["id"]]["download_status"] = status
            print(f"  ECHEC : {status}")

        print()

        # Sauvegarde incrémentale toutes les 5 docs
        if i % 5 == 0:
            with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                json.dump(catalog, f, ensure_ascii=False, indent=2)
            print(f"  [catalog sauvegardé après {i} docs]\n")

    # Sauvegarde finale
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"""
=== RÉSUMÉ ===
Cibles total   : {len(targets)}
Téléchargés    : {downloaded_count}
Enrichis       : {enriched_count}
Score >= 6     : {score6plus_count}
Echecs         : {failed_count}
""")


if __name__ == "__main__":
    main()
