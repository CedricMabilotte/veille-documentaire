#!/usr/bin/env python3
"""
link_check.py — Pérennité des liens sources (item S3 de la revue).

Pour chaque document du catalog :
  - effectue une requête HEAD (fallback GET) sur l'URL source ;
  - écrit `link_status` (ok / dead / unchecked) et `link_checked` (ISO date) ;
  - soumet l'URL à https://web.archive.org/save/ pour obtenir une copie
    pérenne, stockée dans `archive_url`.

Dégradation propre : si une API échoue, le doc reste `unchecked` ou conserve
son ancien statut, sans jamais faire planter le pipeline.

Pur Python (requests). Aucune autre dépendance.

Usage autonome :
  python scripts/link_check.py            # vérifie tout le catalog
  python scripts/link_check.py --limit 20 # n'en vérifie que 20
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
HEAD_TIMEOUT = 12
SAVE_TIMEOUT = 30
# Ne pas re-vérifier un lien vérifié il y a moins de N jours
RECHECK_AFTER_DAYS = 14


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _days_since(iso: str | None) -> float:
    """Nombre de jours écoulés depuis une date ISO. Infini si absente/invalide."""
    if not iso:
        return float("inf")
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
    except Exception:
        return float("inf")


def check_url(url: str) -> str:
    """Retourne 'ok', 'dead' ou 'unchecked' pour une URL.

    HEAD d'abord ; si la méthode HEAD est refusée (405/501) on tente un GET
    léger. Les erreurs réseau renvoient 'unchecked' (on ne marque pas dead
    un lien qu'on n'a pas pu joindre — prudence).
    """
    if not url:
        return "unchecked"
    try:
        r = requests.head(url, headers=HEADERS, timeout=HEAD_TIMEOUT,
                           allow_redirects=True)
        code = r.status_code
        if code in (405, 501, 403):
            # Certains serveurs refusent HEAD : on retente en GET (stream)
            try:
                rg = requests.get(url, headers=HEADERS, timeout=HEAD_TIMEOUT,
                                  allow_redirects=True, stream=True)
                code = rg.status_code
                rg.close()
            except requests.RequestException:
                return "unchecked"
        if 200 <= code < 400:
            return "ok"
        if code in (404, 410):
            return "dead"
        # 5xx, 429 : indéterminé, on ne tranche pas
        return "unchecked"
    except requests.RequestException:
        return "unchecked"


def submit_to_wayback(url: str) -> str | None:
    """Soumet l'URL à web.archive.org/save et retourne l'URL d'archive si connue.

    Best-effort : l'API Save Page Now peut être lente ou rate-limitée. On ne
    bloque jamais le pipeline. Retourne None en cas d'échec.
    """
    if not url:
        return None
    save_url = f"https://web.archive.org/save/{url}"
    try:
        r = requests.get(save_url, headers=HEADERS, timeout=SAVE_TIMEOUT,
                         allow_redirects=True)
        # L'archive finale est exposée dans le header Content-Location
        # (ex: /web/20260522.../http://...) ou dans l'URL finale.
        cl = r.headers.get("Content-Location") or r.headers.get("content-location")
        if cl:
            return "https://web.archive.org" + cl
        if "/web/" in r.url:
            return r.url
    except requests.RequestException:
        return None
    return None


def wayback_lookup(url: str) -> str | None:
    """Cherche une copie déjà existante via l'API availability (rapide)."""
    if not url:
        return None
    try:
        r = requests.get("https://archive.org/wayback/available",
                         params={"url": url}, headers=HEADERS, timeout=HEAD_TIMEOUT)
        data = r.json()
        snap = (data.get("archived_snapshots") or {}).get("closest") or {}
        if snap.get("available") and snap.get("url"):
            return snap["url"]
    except Exception:
        return None
    return None


def check_catalog(catalog_path: Path = CATALOG_PATH, limit: int | None = None,
                   do_archive: bool = True) -> dict:
    """Parcourt le catalog, met à jour link_status/link_checked/archive_url.

    Retourne un dict de stats.
    """
    if not catalog_path.exists():
        print(f"[link_check] catalog introuvable : {catalog_path}")
        return {"error": "no_catalog"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})

    stats = {"checked": 0, "ok": 0, "dead": 0, "unchecked": 0,
             "archived": 0, "skipped_recent": 0}

    processed = 0
    for doc_id, doc in docs.items():
        if limit is not None and processed >= limit:
            break
        url = doc.get("url", "")
        if not url:
            continue

        # Migration douce : on saute les liens vérifiés récemment
        if _days_since(doc.get("link_checked")) < RECHECK_AFTER_DAYS:
            stats["skipped_recent"] += 1
            continue

        status = check_url(url)
        doc["link_status"] = status
        doc["link_checked"] = _iso_now()
        stats["checked"] += 1
        stats[status] = stats.get(status, 0) + 1
        processed += 1

        if do_archive:
            # On privilégie une archive existante (rapide), sinon on en crée une
            archive = doc.get("archive_url") or wayback_lookup(url)
            if not archive and status != "dead":
                archive = submit_to_wayback(url)
            if not archive and status == "dead":
                # Lien mort : une copie ancienne est précieuse
                archive = wayback_lookup(url)
            if archive:
                doc["archive_url"] = archive
                stats["archived"] += 1
            # Politesse envers archive.org
            time.sleep(1.0)

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"[link_check] {stats}")
    return stats


if __name__ == "__main__":
    lim = None
    if "--limit" in sys.argv:
        try:
            lim = int(sys.argv[sys.argv.index("--limit") + 1])
        except (ValueError, IndexError):
            lim = None
    # En autonome on limite par défaut pour ne pas marteler archive.org
    check_catalog(limit=lim if lim is not None else 5)
