#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watch.py — Veille automatisée du projet « Communs / Terres Libérées ».

Lit config/sources.yml, interroge chaque source web, repère les liens dont le
texte évoque la libération des terres (mots-clés), écarte ce qui est déjà
référencé, et écrit une liste de CANDIDATS à examiner dans discovery/.

Volontairement sans dépendance lourde (urllib + html.parser de la stdlib ;
PyYAML pour la config). Aucune clé d'API requise. La promotion d'un candidat
en fiche reste une décision humaine — la veille ne fait que défricher.

Usage : python3 scripts/watch.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
DISCOVERY = ROOT / "discovery"
UA = "CommunsVeilleBot/1.0 (+https://communs.actitude.org ; veille documentaire)"
TIMEOUT = 20
POLITE_DELAY = 2.0  # secondes entre deux requêtes


# ─────────────────────────────────────────────────────────────────────────────
# Extraction des liens d'une page
# ─────────────────────────────────────────────────────────────────────────────

class LinkHarvester(HTMLParser):
    """Collecte (href, texte) de chaque <a> de la page."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._buf = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = href
                self._buf = []
                self._depth = 1
        elif self._href is not None:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._href is not None:
            if tag == "a" and self._depth <= 1:
                txt = re.sub(r"\s+", " ", "".join(self._buf)).strip()
                if txt:
                    self.links.append((self._href, txt))
                self._href = None
                self._buf = []
                self._depth = 0
            else:
                self._depth -= 1

    def handle_data(self, data):
        if self._href is not None:
            self._buf.append(data)


def fetch(url: str) -> str | None:
    """Récupère le HTML d'une URL ; renvoie None en cas d'échec (sans planter)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "fr,en;q=0.7"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "xml" not in ctype and ctype:
                return None
            raw = resp.read(2_500_000)  # plafond de sécurité
        return raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ConnectionError, ValueError) as exc:
        print(f"  ! échec {url} : {exc}", file=sys.stderr)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Scoring d'un candidat
# ─────────────────────────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def score_candidate(text: str, source_kw: list[str],
                     transverse_kw: list[str]) -> tuple[int, list[str]]:
    """Score heuristique : nombre de mots-clés trouvés dans le texte du lien."""
    t = normalise(text)
    hits = []
    for kw in (source_kw or []) + (transverse_kw or []):
        if normalise(kw) in t:
            hits.append(kw)
    # un mot-clé transverse fort vaut double
    score = len(set(hits))
    for strong in ("libération des terres", "nue-propriété", "usufruit",
                    "fonds de dotation", "démembrement"):
        if strong in t:
            score += 1
    return score, sorted(set(hits))


# ─────────────────────────────────────────────────────────────────────────────
# Connaissance de l'existant (pour ne pas re-proposer)
# ─────────────────────────────────────────────────────────────────────────────

def known_urls() -> set[str]:
    urls = set()
    for folder in ("lieux", "porteurs", "usufruitiers", "modeles"):
        d = ROOT / folder
        if not d.exists():
            continue
        for fp in d.glob("*.yml"):
            try:
                data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            for key in ("url",):
                if data.get(key):
                    urls.add(urlparse(str(data[key])).netloc.lower())
    return urls


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def main():
    cfg = yaml.safe_load((CONFIG / "sources.yml").read_text(encoding="utf-8"))
    sources = cfg.get("sources", [])
    transverse = cfg.get("mots_cles_transverses", [])
    seen_domains = known_urls()
    DISCOVERY.mkdir(exist_ok=True)

    candidates = []
    for src in sources:
        url = src.get("url")
        if not url:
            continue
        print(f"· {src.get('id','?')} — {url}")
        html_doc = fetch(url)
        time.sleep(POLITE_DELAY)
        if not html_doc:
            continue
        harvester = LinkHarvester()
        try:
            harvester.feed(html_doc)
        except Exception as exc:  # parsing best-effort
            print(f"  ! parsing {url} : {exc}", file=sys.stderr)
            continue
        src_kw = src.get("mots_cles", [])
        vus = set()
        for href, text in harvester.links:
            link = urljoin(url, href)
            if link in vus or len(text) < 12:
                continue
            vus.add(link)
            score, hits = score_candidate(text, src_kw, transverse)
            if score < 2:
                continue
            domain = urlparse(link).netloc.lower()
            candidates.append({
                "texte": text[:200],
                "url": link,
                "source_id": src.get("id"),
                "categorie_probable": src.get("categorie_probable", []),
                "score": score,
                "mots_cles": hits,
                "deja_reference": domain in seen_domains,
            })

    # tri : score décroissant, nouveautés d'abord
    candidates.sort(key=lambda c: (not c["deja_reference"], c["score"]),
                    reverse=True)

    today = dt.date.today().isoformat()
    out_json = DISCOVERY / f"candidats-{today}.json"
    out_md = DISCOVERY / f"candidats-{today}.md"
    out_json.write_text(json.dumps(candidates, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    lines = [f"# Veille — candidats du {today}", "",
             f"{len(candidates)} candidat·s repéré·s sur {len(sources)} sources. "
             "Score = nombre de mots-clés ; à examiner et promouvoir manuellement "
             "en fiche.", ""]
    nouveaux = [c for c in candidates if not c["deja_reference"]]
    lines.append(f"## Nouveautés possibles ({len(nouveaux)})\n")
    for c in nouveaux[:60]:
        lines.append(f"- **[{c['score']}]** [{c['texte']}]({c['url']}) "
                     f"— source : {c['source_id']} — mots-clés : "
                     f"{', '.join(c['mots_cles'])}")
    deja = [c for c in candidates if c["deja_reference"]]
    if deja:
        lines.append(f"\n## Domaines déjà référencés ({len(deja)})\n")
        for c in deja[:30]:
            lines.append(f"- [{c['score']}] [{c['texte']}]({c['url']}) "
                         f"— {c['source_id']}")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nVeille terminée : {len(candidates)} candidats "
          f"({len(nouveaux)} nouveautés possibles).")
    print(f"→ {out_md}")


if __name__ == "__main__":
    main()
