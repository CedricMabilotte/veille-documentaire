#!/usr/bin/env python3
"""Download missing PDFs and generate covers for 13 infokiosques entries."""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"
DOCS_DIR = ROOT / "docs"
COVERS_SITE = ROOT / "site" / "assets" / "covers"
COVERS_IFACE = ROOT / "interface" / "covers"

DOCS_DIR.mkdir(exist_ok=True)
COVERS_SITE.mkdir(parents=True, exist_ok=True)
COVERS_IFACE.mkdir(parents=True, exist_ok=True)

TARGET_UIDS = [
    "2478138a", "38a113bc", "ba64641a", "54e772e7", "79cc5801",
    "c97fba28", "df840ff3", "9789d29b", "e9b2bf94", "2d0a1772",
    "98360cb9", "2c9a5575", "19101c21",
]

with open(CATALOG_PATH) as f:
    catalog = json.load(f)

downloaded_count = 0
cover_count = 0
errors = []

for uid in TARGET_UIDS:
    entry = catalog["docs"].get(uid)
    if not entry:
        print(f"[SKIP] {uid} not found in catalog")
        errors.append(f"{uid}: not in catalog")
        continue

    url = entry["url"]
    filename = entry["filename"]
    dest = DOCS_DIR / f"{uid}_{filename}"

    # Download PDF
    print(f"[DL] {uid} → {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"  OK — {len(data)//1024} KB saved to {dest.name}")
        downloaded_count += 1

        # Update catalog
        entry["downloaded"] = True
        entry["saved_as"] = f"docs/{uid}_{filename}"

    except Exception as e:
        print(f"  ERROR downloading {uid}: {e}")
        errors.append(f"{uid}: download failed — {e}")
        continue

    # Generate cover
    try:
        import fitz
        from PIL import Image

        doc_pdf = fitz.open(str(dest))
        page = doc_pdf[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((400, 600))
        img.save(str(COVERS_SITE / f"{uid}.png"))
        img.save(str(COVERS_IFACE / f"{uid}.png"))
        doc_pdf.close()
        print(f"  Cover generated: {uid}.png")
        cover_count += 1
    except Exception as e:
        print(f"  ERROR generating cover for {uid}: {e}")
        errors.append(f"{uid}: cover failed — {e}")

# Save updated catalog
with open(CATALOG_PATH, "w") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)
print(f"\nCatalog updated.")

print(f"\n=== RÉSULTATS ===")
print(f"PDFs téléchargés : {downloaded_count}/13")
print(f"Couvertures générées : {cover_count}/13")
if errors:
    print(f"Erreurs ({len(errors)}) :")
    for e in errors:
        print(f"  - {e}")
