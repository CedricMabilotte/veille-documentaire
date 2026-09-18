#!/usr/bin/env python3
"""
check_deploy.py — Détecte une désynchronisation entre site/ local et le site live.

Compare quelques fichiers sentinelles (app.js, catalog.json meta, style.css)
entre la version locale et biblio.actitude.org, ET vérifie que le dernier
déploiement GitHub Pages sur le dépôt public a réellement réussi.

Garde-fou ajouté le 2026-07-06 (session #22) : le workflow publish-only.yml
ne vérifie que le succès de son propre `git push` vers biblio-actitude-org —
pas le déploiement Pages déclenché en aval par GitHub sur CE dépôt, qui peut
échouer silencieusement (ex. artefact > 1 Go) sans qu'aucune alerte ne
remonte côté dépôt source. Voir lecons-biblio.md L45 et le manuel transverse
§6.11.

Sortie 0  → site live à jour ET dernier déploiement Pages réussi.
Sortie 1  → écart de contenu détecté → lancer publish_direct.sh.
Sortie 2  → dernier déploiement Pages en échec → voir le diagnostic affiché.

Usage : python3 scripts/check_deploy.py
"""

import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://biblio.actitude.org"
SITE_PATH = Path(__file__).parent.parent / "site"
PAGES_REPO = "CedricMabilotte/biblio-actitude-org"
MAX_SITE_MB = 700  # limite GitHub Pages = 1024 Mo ; marge de sécurité ~30 %

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

def reference_bytes(rel: str) -> tuple[bytes | None, str]:
    """Contenu de référence d'un fichier sentinelle de `site/`.

    `site/` est un artefact reconstruit par la CI (rebuild-site.yml) puis poussé
    sur origin/main — il n'est jamais régénéré dans l'arbre de travail local, et
    le checkout est un clone partiel. Comparer le live à la copie du disque
    produisait donc de fausses alertes (18/09 : copie locale à 998 fiches contre
    817 réellement publiées). La référence est `origin/main`, avec repli sur le
    disque quand git n'est pas disponible.
    """
    r = subprocess.run(["git", "-C", str(SITE_PATH.parent), "show",
                        f"origin/main:site/{rel}"], capture_output=True)
    if r.returncode == 0 and r.stdout:
        return r.stdout, "origin/main"
    local_path = SITE_PATH / rel
    if local_path.exists():
        return local_path.read_bytes(), "arbre local"
    return None, "-"


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

def check_site_size() -> bool:
    """Alerte si site/ approche la limite de 1 Go de GitHub Pages."""
    total = sum(f.stat().st_size for f in SITE_PATH.rglob("*") if f.is_file())
    mb = total / (1024 * 1024)
    if mb > MAX_SITE_MB:
        print(f"  ✗  site/ pèse {mb:.0f} Mo (seuil d'alerte {MAX_SITE_MB} Mo, "
              f"limite dure GitHub Pages = 1024 Mo) — voir manuel §6.11")
        return False
    print(f"  ✓  Taille de site/ : {mb:.0f} Mo (< {MAX_SITE_MB} Mo)")
    return True


def check_pages_deployment() -> bool:
    """Vérifie que le dernier déploiement GitHub Pages du dépôt public a
    réussi — gh run list sur le dépôt source ne le détecte PAS (cf. docstring)."""
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{PAGES_REPO}/deployments?per_page=1"],
            capture_output=True, text=True, timeout=20, check=True,
        )
        deployments = json.loads(out.stdout)
        if not deployments:
            print("  ?  Aucun déploiement trouvé — ignoré")
            return True
        dep_id = deployments[0]["id"]
        sha = deployments[0]["sha"][:8]
        out2 = subprocess.run(
            ["gh", "api", f"repos/{PAGES_REPO}/deployments/{dep_id}/statuses"],
            capture_output=True, text=True, timeout=20, check=True,
        )
        statuses = json.loads(out2.stdout)
        if not statuses:
            print(f"  ?  Déploiement {sha} sans statut — ignoré")
            return True
        state = statuses[0]["state"]
        if state == "success":
            print(f"  ✓  Dernier déploiement Pages ({sha}) : success")
            return True
        print(f"  ✗  Dernier déploiement Pages ({sha}) : {state} — "
              f"log : {statuses[0].get('log_url', '?')}")
        return False
    except Exception as e:
        print(f"  ⚠  Impossible de vérifier le déploiement Pages : {e}")
        return True  # ne bloque pas si gh/API indisponible — vérif best-effort


def main() -> int:
    print("check_deploy — comparaison local ↔ biblio.actitude.org")
    ecarts = []

    for local_rel, live_rel in SENTINELS:
        local_data, origine = reference_bytes(local_rel)
        if local_data is None:
            print(f"  ?  {local_rel} introuvable (ni sur origin/main, ni localement) — ignoré")
            continue
        live_data   = fetch(f"{BASE_URL}/{live_rel}")
        if live_data is None:
            ecarts.append(local_rel)
            continue
        if md5(local_data) != md5(live_data):
            ecarts.append(local_rel)
            print(f"  ✗  ÉCART : {local_rel}")
            print(f"       {origine:<12} md5={md5(local_data)}")
            print(f"       live         md5={md5(live_data)}")
        else:
            print(f"  ✓  {local_rel}  (référence : {origine})")

    print()
    size_ok = check_site_size()
    deploy_ok = check_pages_deployment()

    if ecarts:
        print()
        print("⚠  Le site live n'est PAS à jour.")
        print("   → bash scripts/publish_direct.sh")
        return 1
    if not deploy_ok:
        print()
        print("⚠  Le dernier déploiement GitHub Pages a échoué — voir le log ci-dessus.")
        return 2
    print()
    print("✓  Site live synchronisé avec les sources locales" +
          ("" if size_ok else " (mais taille à surveiller)") + ".")
    return 0

if __name__ == "__main__":
    sys.exit(main())
