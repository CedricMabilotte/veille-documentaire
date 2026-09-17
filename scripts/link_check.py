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

import concurrent.futures
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

import requests

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
HEAD_TIMEOUT = 12
SAVE_TIMEOUT = 30
# Ne pas re-vérifier un lien vérifié il y a moins de N jours
RECHECK_AFTER_DAYS = 14


def encode_url(url: str) -> str:
    """Encode proprement une URL qui peut contenir des espaces ou accents.

    Ne ré-encode pas les caractères déjà encodés (%xx) ni les délimiteurs
    structuraux (/, :, ?, #, =, &). Indispensable pour les URLs stockées
    depuis du HTML sans encodage (espaces dans noms de fichiers PDF, etc.).
    """
    if not url:
        return url
    try:
        p = urlparse(url)
        # Encoder le path en préservant les séparateurs structuraux
        encoded_path = quote(p.path, safe='/:@!$&\'()*+,;=-.%')
        return urlunparse(p._replace(path=encoded_path))
    except Exception:
        return url


def archive_org_fallback(url: str) -> tuple[str, str | None]:
    """Pour une URL archive.org/download/ qui retourne 404 :
    tente la page /details/<item_id> et retourne (status, new_url).

    Logique :
    - /download/<item>/<fichier> peut disparaître (CDL, renommage, restriction).
    - /details/<item> est la page pérenne — toujours publique si l'item existe.
    Retourne ('ok', new_url) si /details/ répond, ('dead', None) sinon.
    """
    m = re.match(r'(https?://archive\.org)/download/([^/]+)/', url)
    if not m:
        return ('dead', None)
    details_url = f"{m.group(1)}/details/{m.group(2)}"
    try:
        r = requests.head(details_url, headers=HEADERS,
                          timeout=HEAD_TIMEOUT, allow_redirects=True)
        if 200 <= r.status_code < 400:
            return ('ok', details_url)
        r2 = requests.get(details_url, headers=HEADERS,
                          timeout=HEAD_TIMEOUT, stream=True)
        r2.close()
        if 200 <= r2.status_code < 400:
            return ('ok', details_url)
    except requests.RequestException:
        pass
    return ('dead', None)


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


def check_url(url: str) -> tuple[str, str | None]:
    """Retourne (status, corrected_url) pour une URL.

    status : 'ok', 'dead' ou 'unchecked'.
    corrected_url : URL corrigée si une alternative a été trouvée (ex: archive.org
      /download/ → /details/), None sinon.

    Stratégie :
    1. Encodage URL (espaces, accents) avant tout test.
    2. HEAD d'abord.
    3. Fallback GET si HEAD retourne 4xx/5xx ambigu ou refus méthode
       (405, 501, 403, 500) — certains serveurs (archive.org CDN) retournent
       500 sur HEAD mais 200 sur GET.
    4. Si archive.org /download/ retourne 404 : essai automatique /details/.
    Les erreurs réseau → 'unchecked' (pas de verdict définitif).
    """
    if not url:
        return ("unchecked", None)

    url = encode_url(url)  # fix 2 : espaces / accents dans le path

    def _get_fallback(u: str) -> int | None:
        try:
            rg = requests.get(u, headers=HEADERS, timeout=HEAD_TIMEOUT,
                              allow_redirects=True, stream=True)
            code = rg.status_code
            rg.close()
            return code
        except requests.RequestException:
            return None

    try:
        r = requests.head(url, headers=HEADERS, timeout=HEAD_TIMEOUT,
                          allow_redirects=True)
        code = r.status_code

        # fix 3 : 405/501 = HEAD refusé ; 403/500 = parfois refus discret
        # (archive.org CDN retourne 500 sur HEAD mais 200 sur GET)
        if code in (403, 405, 500, 501):
            fallback = _get_fallback(url)
            if fallback is not None:
                code = fallback

        if 200 <= code < 400:
            return ("ok", None)

        if code in (404, 410):
            # fix 1 : archive.org /download/ → /details/
            if "archive.org/download/" in url:
                status, new_url = archive_org_fallback(url)
                return (status, new_url)
            return ("dead", None)

        # 5xx résiduel, 429, etc. : indéterminé
        return ("unchecked", None)

    except requests.RequestException:
        return ("unchecked", None)


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
                   do_archive: bool = True, max_workers: int = 12,
                   prioritize=None, archive_limit: int | None = None) -> dict:
    """Parcourt le catalog, met à jour link_status/link_checked/archive_url.

    Les vérifications HTTP (HEAD) sont menées **en parallèle** (`max_workers`) :
    ce sont des entrées-sorties indépendantes, sûres à paralléliser. Un seul
    processus, une seule écriture du catalogue à la fin — pas de conflit.

    L'archivage Wayback, lui, reste **séquentiel et poli** : c'est le point
    que archive.org rate-limite. Il est borné par `archive_limit` pour ne pas
    allonger indéfiniment un run.

    `prioritize` : callable(doc) -> bool, optionnel. Si fourni, les documents
    prioritaires (typiquement les fiches publiées, via `_is_publishable`) sont
    vérifiés en premier sous `limit`, et sont les seuls soumis à l'archivage.
    Cela évite d'importer watch.py ici (dépendance injectée par l'appelant).

    Retourne un dict de stats.
    """
    if not catalog_path.exists():
        print(f"[link_check] catalog introuvable : {catalog_path}")
        return {"error": "no_catalog"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})

    stats = {"checked": 0, "ok": 0, "dead": 0, "unchecked": 0,
             "archived": 0, "skipped_recent": 0}

    # Liste des docs à vérifier : URL présente, pas vérifié récemment.
    to_check = []
    for doc in docs.values():
        if not doc.get("url"):
            continue
        if _days_since(doc.get("link_checked")) < RECHECK_AFTER_DAYS:
            stats["skipped_recent"] += 1
            continue
        to_check.append(doc)

    # Priorité : les fiches publiées d'abord (elles comptent le plus, et le
    # `limit` doit les couvrir en premier).
    if prioritize is not None:
        to_check.sort(key=lambda d: 0 if prioritize(d) else 1)
    if limit is not None:
        to_check = to_check[:limit]

    # ── Phase 1 — vérifications HTTP en parallèle ────────────────────────────
    now = _iso_now()
    url_corrections = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(check_url, d["url"]): d for d in to_check}
        for fut in concurrent.futures.as_completed(futures):
            doc = futures[fut]
            try:
                status, corrected_url = fut.result()
            except Exception:
                status, corrected_url = "unchecked", None
            doc["link_status"] = status
            # Si une URL alternative a été trouvée (archive.org /details/),
            # on met à jour le catalog pour les runs suivants.
            if corrected_url:
                doc["url"] = corrected_url
                url_corrections += 1
            # On n'horodate que les résultats définitifs (ok / dead). Un
            # statut « unchecked » (timeout, 5xx, 429 — souvent transitoire)
            # reste sans date `link_checked` : le doc redevient éligible dès
            # le prochain run au lieu d'attendre RECHECK_AFTER_DAYS.
            if status != "unchecked":
                doc["link_checked"] = now
            stats["checked"] += 1
            stats[status] = stats.get(status, 0) + 1
    if url_corrections:
        stats["url_corrections"] = url_corrections
        print(f"[link_check] {url_corrections} URL(s) corrigée(s) "
              f"(archive.org /download/→/details/ ou encodage)")

    # ── Phase 2 — archivage Wayback : séquentiel, poli, borné ────────────────
    # archive.org rate-limite Save Page Now : on ne parallélise jamais ici.
    # Si une fonction de priorité est fournie, on n'archive que les docs
    # prioritaires — les autres seront archivés « à la capture » (watch.py).
    if do_archive:
        targets = [d for d in to_check
                   if prioritize is None or prioritize(d)]
        if archive_limit is not None:
            targets = targets[:archive_limit]
        for doc in targets:
            url = doc["url"]
            archive = doc.get("archive_url") or wayback_lookup(url)
            if not archive and doc.get("link_status") != "dead":
                archive = submit_to_wayback(url)
            if not archive and doc.get("link_status") == "dead":
                # Lien mort : une copie ancienne reste précieuse
                archive = wayback_lookup(url)
            if archive:
                doc["archive_url"] = archive
                stats["archived"] += 1
            time.sleep(1.0)  # politesse envers archive.org

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"[link_check] {stats}")
    return stats


if __name__ == "__main__":
    # Usage :
    #   python scripts/link_check.py                   # tout le catalog, vérif seule
    #   python scripts/link_check.py --limit 200       # borne le nombre vérifié
    #   python scripts/link_check.py --archive         # active l'archivage Wayback
    lim = None
    if "--limit" in sys.argv:
        try:
            lim = int(sys.argv[sys.argv.index("--limit") + 1])
        except (ValueError, IndexError):
            lim = None
    do_archive = "--archive" in sys.argv
    # En autonome : vérification de tout le catalog (rapide car parallèle) ;
    # archivage désactivé par défaut (lent, rate-limité) — l'opt-in --archive
    # le réactive, borné pour rester poli envers archive.org.
    check_catalog(limit=lim, do_archive=do_archive,
                  archive_limit=20 if do_archive else None)
