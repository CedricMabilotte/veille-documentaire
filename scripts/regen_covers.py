#!/usr/bin/env python3
"""
Régénère les couvertures existantes à 1200px depuis les PDFs locaux.

Usage :
  python3 scripts/regen_covers.py          # régénère tous les PDFs disponibles localement
  python3 scripts/regen_covers.py --dry-run  # liste sans modifier
  python3 scripts/regen_covers.py --fetch    # re-télécharge les PDFs manquants puis régénère

Phase 1 (sans --fetch) : ~191 covers depuis PDFs déjà en docs/
Phase 2 (avec --fetch)  : les ~537 covers restantes (nécessite réseau)
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
import time

ROOT    = Path(__file__).parent.parent
DOCS    = ROOT / "docs"
COVERS  = ROOT / "site" / "assets" / "covers"
CATALOG = ROOT / "synopsis" / "catalog.json"

sys.path.insert(0, str(ROOT / "scripts"))
import pdf_processor

MAX_WIDTH = 1200


def find_local_pdf(uid: str) -> Path | None:
    """Cherche un PDF local dont le nom commence par uid."""
    for fn in DOCS.iterdir():
        if fn.name.startswith(uid) and fn.suffix.lower() == ".pdf":
            return fn
    return None


def download_pdf(url: str, uid: str, filename: str) -> Path | None:
    """Télécharge un PDF et le sauve dans docs/.

    Valide les magic bytes (%PDF) avant d'accepter le téléchargement — sans
    ce contrôle, une page de blocage anti-bot ou une page "detail/borrow"
    d'archive.org (renvoyée avec un statut HTTP 200) est silencieusement
    sauvée comme si c'était le PDF réel, invisible jusqu'à un audit manuel
    (cf. lecons-biblio.md, session #21 suite — audit_citations.py a détecté
    20 fiches publiées dont le PDF local était en fait une telle page).
    """
    dest = DOCS / filename
    if dest.exists():
        return dest
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 biblio-regen"})
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
            f.write(r.read())
        if not pdf_processor.validate_pdf(dest):
            print(f"    ✗  Download for {uid} n'est pas un PDF valide "
                  f"(page de blocage/erreur ?) — rejeté")
            dest.unlink(missing_ok=True)
            return None
        return dest
    except Exception as e:
        print(f"    ✗  Download failed for {uid}: {e}")
        return None


def main():
    dry_run  = "--dry-run"  in sys.argv
    do_fetch = "--fetch"    in sys.argv
    only_uid  = next((a for a in sys.argv[1:] if not a.startswith("-")), None)

    # Charger le catalogue
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    docs_dict = cat["docs"]

    # Couvertures existantes
    covers_existing = sorted(COVERS.glob("*.png"))
    if only_uid:
        covers_existing = [c for c in covers_existing if c.stem == only_uid]

    total   = len(covers_existing)
    done    = 0
    skipped = 0
    errors  = 0
    fetched = 0

    print(f"🖼  Régénération des couvertures à {MAX_WIDTH}px")
    print(f"   Covers cibles : {total}")
    print(f"   Mode          : {'DRY-RUN' if dry_run else ('FETCH+REGEN' if do_fetch else 'LOCAL ONLY')}")
    print()

    for cover_png in covers_existing:
        uid = cover_png.stem
        fiche = docs_dict.get(uid, {})

        # 1. Chercher PDF local
        pdf_path = find_local_pdf(uid)

        # 2. Si absent et --fetch demandé : télécharger
        if not pdf_path and do_fetch:
            url      = fiche.get("url", "")
            filename = fiche.get("saved_as", f"docs/{uid}.pdf")
            # saved_as est relatif au projet (ex: "docs/xxxx_name.pdf")
            filename = Path(filename).name
            if url and url.startswith("http"):
                if not dry_run:
                    pdf_path = download_pdf(url, uid, filename)
                    if pdf_path:
                        fetched += 1
                        time.sleep(0.3)   # politesse serveur
                else:
                    print(f"  [DRY] Would fetch: {url[:80]}")
                    done += 1
                    continue

        if not pdf_path:
            skipped += 1
            continue

        if dry_run:
            print(f"  ✓  {uid} ({pdf_path.name})")
            done += 1
            continue

        ok = pdf_processor.extract_cover(pdf_path, cover_png, max_width=MAX_WIDTH)
        if ok:
            size_kb = cover_png.stat().st_size // 1024
            done += 1
            if done % 20 == 0 or done <= 5:
                print(f"  [{done}/{total - skipped}]  {uid}  → {size_kb} KB")
        else:
            print(f"  ✗  {uid} : échec extract_cover")
            errors += 1

    print()
    print(f"✅  Terminé : {done} régénérés, {fetched} téléchargés, {skipped} ignorés (PDF absent), {errors} erreurs")
    total_size_mb = sum(p.stat().st_size for p in COVERS.glob("*.png")) / 1024 / 1024
    print(f"   Taille totale covers : {total_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
