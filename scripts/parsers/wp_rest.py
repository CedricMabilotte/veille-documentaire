#!/usr/bin/env python3
"""
wp_rest.py — Parser pour l'API REST WordPress (media endpoint).

L'endpoint /wp-json/wp/v2/media?mime_type=application/pdf retourne des PDFs
avec métadonnées complètes (titre, date, source_url, filesize). Ce parser
pagine jusqu'à épuisement et retourne les documents au format standard du
pipeline biblio.

Exemple d'URL source :
    https://mst.org.br/wp-json/wp/v2/media?mime_type=application/pdf&per_page=100

Compatible avec l'API parser standard : find_documents(source: dict) -> list[dict]
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urlparse, urlencode, urlunparse, parse_qs, urljoin

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
TIMEOUT = 20
DEFAULT_PER_PAGE = 100
DEFAULT_MAX_PAGES = 20      # Limite de sécurité : 20 pages × 100 = 2 000 docs max
DEFAULT_THROTTLE  = 1.0     # Secondes entre deux requêtes de pagination

CONTEXT_MAX = 400


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_html(s: str) -> str:
    """Strip basique : retire les tags HTML et compresse les espaces blancs."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:CONTEXT_MAX]


def _rendered(field) -> str:
    """Extrait le champ `.rendered` d'un objet WP (titre, description, caption)."""
    if isinstance(field, dict):
        return field.get("rendered", "") or ""
    return str(field) if field else ""


def _norm_date(raw: str) -> str:
    """Normalise une date ISO WP (2026-06-09T10:00:00) en YYYY-MM-DD."""
    if not raw:
        return ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else ""


def _api_url(base_url: str, page: int, per_page: int) -> str:
    """Construit l'URL paginée à partir de l'URL de base fournie dans sources.yml.

    On injecte ou remplace les paramètres `page` et `per_page` proprement.
    """
    parsed = urlparse(base_url)
    # Récupère les query params existants (per_page peut déjà être dans l'URL source)
    existing = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
    existing["page"]     = str(page)
    existing["per_page"] = str(per_page)
    new_query = urlencode(existing)
    return urlunparse(parsed._replace(query=new_query))


# ── Pagination ────────────────────────────────────────────────────────────────

def _fetch_page(url: str) -> tuple[list[dict], int]:
    """Récupère une page de l'API WP REST.

    Retourne (items, total_pages). En cas d'erreur HTTP non-bloquante,
    retourne ([], 0) pour arrêter la pagination proprement.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        print(f"  ⚠  wp_rest : timeout sur {url}")
        return [], 0
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  wp_rest : erreur réseau sur {url} : {e}")
        return [], 0

    if r.status_code == 400:
        # WP REST retourne 400 quand on dépasse le nombre de pages disponibles.
        return [], 0
    if r.status_code == 404:
        print(f"  ⚠  wp_rest : endpoint introuvable (404) : {url}")
        return [], 0
    if r.status_code == 429:
        print(f"  ⚠  wp_rest : rate-limit (429) sur {url} — pause 30 s")
        time.sleep(30)
        return [], 0
    if not r.ok:
        print(f"  ⚠  wp_rest : HTTP {r.status_code} sur {url}")
        return [], 0

    try:
        items = r.json()
    except ValueError as e:
        print(f"  ⚠  wp_rest : JSON invalide sur {url} : {e}")
        return [], 0

    if not isinstance(items, list):
        print(f"  ⚠  wp_rest : réponse inattendue (pas une liste) sur {url}")
        return [], 0

    # WP REST expose le total de pages dans l'en-tête X-WP-TotalPages
    try:
        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
    except (ValueError, TypeError):
        total_pages = 1

    return items, total_pages


# ── Extraction d'un media WP ──────────────────────────────────────────────────

def _media_to_doc(media: dict, source_url: str) -> dict | None:
    """Convertit un objet media WP REST en entrée pipeline biblio.

    Retourne None si l'objet ne contient pas d'URL de fichier utilisable.
    """
    pdf_url = media.get("source_url", "")
    if not pdf_url:
        return None

    # Titre : title.rendered (WP) ou fallback sur le slug
    title = _strip_html(_rendered(media.get("title")))
    if not title:
        title = media.get("slug", "") or Path(urlparse(pdf_url).path).stem

    # Description : description.rendered, sinon caption.rendered
    description = _strip_html(_rendered(media.get("description")))
    if not description:
        description = _strip_html(_rendered(media.get("caption")))

    date_str = _norm_date(media.get("date", ""))

    filename = Path(urlparse(pdf_url).path).name or "document.pdf"
    ext = Path(filename).suffix.lower().lstrip(".")

    doc: dict = {
        "url":        pdf_url,
        "filename":   filename,
        "extension":  ext or "pdf",
        "link_text":  title,
        "context":    description,
        "page_title": title,
        "source_url": source_url,
    }
    if date_str:
        doc["src_meta"] = {"date": date_str}

    return doc


# ── API parser standard ───────────────────────────────────────────────────────

def find_documents(source: dict) -> list[dict]:
    """Parcourt l'API WP REST media et retourne les PDFs au format pipeline.

    Paramètres reconnus dans la strophe source (sources.yml) :
      - url          : URL de base de l'endpoint (obligatoire)
      - per_page     : items par page (défaut 100, max WP = 100)
      - max_pages    : limite de sécurité sur le nombre de pages (défaut 20)
      - throttle_sec : pause entre pages en secondes (défaut 1.0)
    """
    base_url   = source.get("url", "")
    if not base_url:
        return []

    per_page   = int(source.get("per_page",    DEFAULT_PER_PAGE))
    max_pages  = int(source.get("max_pages",   DEFAULT_MAX_PAGES))
    throttle_s = float(source.get("throttle_sec", DEFAULT_THROTTLE))
    label      = source.get("label", base_url)

    all_docs: list[dict] = []
    seen_urls: set[str]  = set()
    page       = 1
    total_pages: int | None = None

    while True:
        if total_pages is not None and page > total_pages:
            break
        if page > max_pages:
            print(f"  ↳ wp_rest : limite max_pages={max_pages} atteinte "
                  f"pour {label}")
            break

        page_url = _api_url(base_url, page, per_page)
        items, discovered_total = _fetch_page(page_url)

        if not items:
            break  # Épuisement ou erreur non-bloquante

        if total_pages is None:
            total_pages = discovered_total

        page_docs = 0
        for media in items:
            doc = _media_to_doc(media, base_url)
            if doc is None or doc["url"] in seen_urls:
                continue
            seen_urls.add(doc["url"])
            all_docs.append(doc)
            page_docs += 1

        print(f"  ↳ wp_rest : page {page}/{total_pages} — "
              f"{page_docs} docs nouveaux ({len(all_docs)} total) — {label}")

        page += 1

        if page <= (total_pages or 1) and page <= max_pages:
            time.sleep(throttle_s)

    print(f"  ↳ wp_rest : {len(all_docs)} docs au total pour {label}")
    return all_docs


# ── Test autonome ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    test_sources = [
        {
            "label": "MST Brésil — biblioteca (WP REST API)",
            "url":   "https://mst.org.br/wp-json/wp/v2/media"
                     "?mime_type=application/pdf",
            "per_page":    5,
            "max_pages":   3,
            "throttle_sec": 1.0,
            "default_lang": "pt",
            "orientation":  "militant",
        },
    ]

    src = test_sources[int(sys.argv[1])] if len(sys.argv) > 1 else test_sources[0]
    print(f"=== Test wp_rest sur {src['label']} ===", file=sys.stderr)
    docs = find_documents(src)
    print(f"\n→ {len(docs)} docs trouvés", file=sys.stderr)
    for d in docs[:5]:
        date = (d.get("src_meta") or {}).get("date", "")
        print(f"  - [{date}] {d['link_text'][:70]}", file=sys.stderr)
        print(f"    {d['url']}", file=sys.stderr)
