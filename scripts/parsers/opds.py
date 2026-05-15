#!/usr/bin/env python3
"""Parser OPDS pour theanarchistlibrary.org (Atom XML d'acquisition)."""

from __future__ import annotations

import sys
from typing import Optional
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

# ── Constantes ────────────────────────────────────────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
TIMEOUT = 20
MAX_DOCS = 100

# Namespaces XML utilisés par OPDS / Atom
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opds": "http://opds-spec.org/2010/catalog",
    "dc":   "http://purl.org/dc/terms/",
    "dc11": "http://purl.org/dc/elements/1.1/",
}

# Types MIME OPDS pour les liens d'acquisition
MIME_PDF  = "application/pdf"
MIME_EPUB = "application/epub+zip"
MIME_TXT  = "text/plain"

# Sous-feeds intéressants pour la thématique communs / paysannerie / terres.
# Le feed racine fournit "New" ; on ajoute quelques topics pertinents qui
# existent réellement (vérifiés via probe HTTP). Les slugs "commons" et
# "peasantry" n'existent pas sur theanarchistlibrary.
EXTRA_FEEDS = [
    "https://theanarchistlibrary.org/opds/new",
    "https://theanarchistlibrary.org/opds/category/topic/land",
    "https://theanarchistlibrary.org/opds/category/topic/farming",
    "https://theanarchistlibrary.org/opds/category/topic/agriculture",
    "https://theanarchistlibrary.org/opds/category/topic/rural",
    "https://theanarchistlibrary.org/opds/category/topic/ecology",
    "https://theanarchistlibrary.org/opds/category/topic/indigenous",
]

# Pagination : nombre max de pages consécutives suivies par feed
MAX_PAGES_PER_FEED = 5


# ── Utilitaires ───────────────────────────────────────────────────────────────
def _warn(msg: str) -> None:
    """Imprime un warning sur stderr."""
    print(f"[opds] {msg}", file=sys.stderr)


def _fetch(url: str) -> Optional[bytes]:
    """Récupère le contenu brut d'une URL, ou None en cas d'erreur."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.content
    except requests.RequestException as e:
        _warn(f"requête échouée pour {url} : {e}")
        return None


def _parse_xml(raw: bytes) -> Optional[ET.Element]:
    """Parse XML, retourne la racine ou None si mal-formé."""
    try:
        return ET.fromstring(raw)
    except ET.ParseError as e:
        _warn(f"XML mal-formé : {e}")
        return None


def _text(elem: Optional[ET.Element]) -> str:
    """Texte d'un élément, ou chaîne vide si absent."""
    return elem.text.strip() if (elem is not None and elem.text) else ""


def _filename_from_url(url: str) -> str:
    """Nom de fichier depuis l'URL (sans query string)."""
    return urlparse(url).path.rsplit("/", 1)[-1] or "document"


def _extension_for(mime: str, url: str) -> str:
    """Extension à partir du MIME, fallback sur l'URL."""
    mapping = {MIME_PDF: "pdf", MIME_EPUB: "epub", MIME_TXT: "txt"}
    if mime in mapping:
        return mapping[mime]
    suffix = url.rsplit(".", 1)[-1].lower()
    return suffix if suffix in {"pdf", "epub", "txt"} else "bin"


# ── Extraction des métadonnées d'une entry ────────────────────────────────────
def _entry_authors(entry: ET.Element) -> str:
    """Concatène les noms d'auteurs d'une entry Atom."""
    names = [_text(a.find("atom:name", NS)) for a in entry.findall("atom:author", NS)]
    return ", ".join(n for n in names if n)


def _entry_summary(entry: ET.Element) -> str:
    """Résumé : <summary> en priorité, sinon texte agrégé de <content>."""
    summary = _text(entry.find("atom:summary", NS))
    if summary:
        return summary
    content = entry.find("atom:content", NS)
    return " ".join(content.itertext()).strip() if content is not None else ""


def _pick_acquisition_link(entry: ET.Element) -> Optional[tuple[str, str]]:
    """Retourne (url, mime) du meilleur lien d'acquisition. Priorité PDF>EPUB>TXT."""
    by_mime: dict[str, str] = {}
    for link in entry.findall("atom:link", NS):
        if "opds-spec.org/acquisition" not in link.get("rel", ""):
            continue
        href, mime = link.get("href"), link.get("type", "")
        if href:
            by_mime.setdefault(mime, href)
    for mime in (MIME_PDF, MIME_EPUB, MIME_TXT):
        if mime in by_mime:
            return by_mime[mime], mime
    return None


def _derive_pdf_url(entry_id: str) -> Optional[str]:
    """Sur theanarchistlibrary.org, le PDF existe par convention à `{id}.pdf`."""
    if not entry_id.startswith("https://theanarchistlibrary.org/library/"):
        return None
    return entry_id + ".pdf"


def _find_next_url(root: ET.Element) -> Optional[str]:
    """Retourne l'URL du feed suivant (lien rel='next'), ou None."""
    for link in root.findall("atom:link", NS):
        if link.get("rel") == "next":
            href = link.get("href")
            if href:
                return href
    return None


# ── Parsing d'un feed d'acquisition (avec pagination) ────────────────────────
def _parse_acquisition_feed(
    url: str,
    source_url: str,
    budget: int,
) -> list[dict]:
    """
    Parse un feed d'acquisition et retourne au plus `budget` documents.
    Suit la pagination via <link rel="next"> jusqu'à MAX_PAGES_PER_FEED.
    """
    results: list[dict] = []
    current_url: Optional[str] = url
    pages_seen = 0

    while current_url and len(results) < budget and pages_seen < MAX_PAGES_PER_FEED:
        raw = _fetch(current_url)
        pages_seen += 1
        if raw is None:
            break
        root = _parse_xml(raw)
        if root is None:
            break

        feed_title = _text(root.find("atom:title", NS)) or "OPDS feed"

        for entry in root.findall("atom:entry", NS):
            if len(results) >= budget:
                break

            title = _text(entry.find("atom:title", NS))
            entry_id = _text(entry.find("atom:id", NS))
            authors = _entry_authors(entry)
            summary = _entry_summary(entry)

            picked = _pick_acquisition_link(entry)
            if picked is None:
                continue
            link_url, mime = picked

            # Préférence PDF : si le feed n'exposait qu'EPUB, on tente la
            # convention `{id}.pdf` propre à theanarchistlibrary.
            if mime != MIME_PDF:
                pdf_url = _derive_pdf_url(entry_id)
                if pdf_url:
                    link_url, mime = pdf_url, MIME_PDF

            context = (authors + " — " + summary).strip(" —")
            results.append({
                "url":        link_url,
                "filename":   _filename_from_url(link_url),
                "extension":  _extension_for(mime, link_url),
                "link_text":  title,
                "context":    context[:400],
                "page_title": feed_title,
                "source_url": source_url,
            })

        current_url = _find_next_url(root)

    return results


# ── API publique ──────────────────────────────────────────────────────────────
def find_documents(source: dict) -> list[dict]:
    """Point d'entrée du parser OPDS."""
    root_url = source.get("url")
    if not root_url:
        _warn("source sans 'url'")
        return []

    # On commence par charger la racine (juste pour valider l'accès et
    # potentiellement enrichir le titre), puis on parse les sous-feeds.
    raw = _fetch(root_url)
    if raw is None:
        return []
    if _parse_xml(raw) is None:
        return []

    # Feeds d'acquisition à parcourir, en partant des EXTRA_FEEDS.
    feeds = [f for f in EXTRA_FEEDS]
    if root_url not in feeds:
        feeds.insert(0, root_url)  # tolérant si l'utilisateur passe autre chose

    seen_urls: set[str] = set()
    all_docs: list[dict] = []

    for feed_url in feeds:
        if len(all_docs) >= MAX_DOCS:
            break
        budget = MAX_DOCS - len(all_docs)
        docs = _parse_acquisition_feed(feed_url, root_url, budget)
        for d in docs:
            if d["url"] in seen_urls:
                continue
            seen_urls.add(d["url"])
            all_docs.append(d)
            if len(all_docs) >= MAX_DOCS:
                break

    return all_docs


# ── Validation manuelle ───────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = find_documents({
        "url":   "https://theanarchistlibrary.org/opds",
        "label": "TAL",
    })
    print(f"Total : {len(docs)} documents trouvés")
    for d in docs[:5]:
        print(f"  - {d['link_text']!r}")
        print(f"      {d['url']}")
