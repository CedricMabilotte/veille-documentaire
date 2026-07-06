#!/usr/bin/env python3
"""
check_deploy.py — Détecte une désynchronisation entre site/ local et le site live.

Compare quelques fichiers sentinelles (app.js, catalog.json meta, style.css)
entre la version locale et biblio.actitude.org.

Sortie 0  → site live à jour.
Sortie 1  → écart détecté → lancer publish_direct.sh.

Usage : python3 scripts/check_deploy.py
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://biblio.actitude.org"
SITE_PATH = Path(__file__).parent.parent / "site"

# Fichiers sentinelles : (chemin local dans site/, URL relative sur le live)
SENTINELS = [
    ("assets/js/app.js",       "assets/js/app.js"),
    ("assets/css/style.css",   "assets/css/style.css"),
    # Ajouté (biblio session #22, 2026-07-06) : data/catalog.json n'est
    # normalement resynchronisé que par publish_site() — un backfill/correctif
    # ciblé qui n'appelle que la source (synopsis/catalog.json) peut le
    # laisser périmé sans que rien ne le signale. Cf. lecons-biblio.md L42.
    ("data/catalog.json",      "data/catalog.json"),
]

def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def fetch(url: str, timeout: int = 10) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "biblio-check/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"  ⚠  Impossible de joindre {url} : {e}")
        return None

def main() -> int:
    print("check_deploy — comparaison local ↔ biblio.actitude.org")
    ecarts = []

    for local_rel, live_rel in SENTINELS:
        local_path = SITE_PATH / local_rel
        if not local_path.exists():
            print(f"  ?  {local_rel} absent localement — ignoré")
            continue
        local_data  = local_path.read_bytes()
        live_data   = fetch(f"{BASE_URL}/{live_rel}")
        if live_data is None:
            ecarts.append(local_rel)
            continue
        if md5(local_data) != md5(live_data):
            ecarts.append(local_rel)
            print(f"  ✗  ÉCART : {local_rel}")
            print(f"       local  md5={md5(local_data)}")
            print(f"       live   md5={md5(live_data)}")
        else:
            print(f"  ✓  {local_rel}")

    if ecarts:
        print()
        print("⚠  Le site live n'est PAS à jour.")
        print("   → bash scripts/publish_direct.sh")
        return 1
    else:
        print()
        print("✓  Site live synchronisé avec les sources locales.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
