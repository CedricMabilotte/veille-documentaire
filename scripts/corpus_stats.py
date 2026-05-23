#!/usr/bin/env python3
"""
corpus_stats.py — État du corpus & transparence des biais (item A8).

Produit synopsis/corpus_stats.json : répartition du corpus par langue,
source, décennie de doc_date, score, type documentaire et orientation des
sources (militant / academique / institutionnel / journalistique).

Lit aussi config/sources.yml pour rattacher chaque source à son champ
`orientation`.

Pur Python (json, yaml). Aucune autre dépendance.

Usage autonome :
  python scripts/corpus_stats.py
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"
SOURCES_PATH = ROOT / "config" / "sources.yml"
OUT_PATH = ROOT / "synopsis" / "corpus_stats.json"


def _load_sources() -> list[dict]:
    """Liste des sources depuis config/sources.yml :
    [{label, url, type, orientation}, ...]."""
    sources: list[dict] = []
    if not SOURCES_PATH.exists():
        return sources
    try:
        import yaml
        cfg = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
        for src in cfg.get("sources", []) or []:
            label = src.get("label", "")
            if not label:
                continue
            sources.append({
                "label":       label,
                "url":         src.get("url", ""),
                "type":        src.get("type", "html"),
                "orientation": src.get("orientation", "non_renseigne"),
            })
    except Exception as e:
        print(f"  ⚠  sources.yml illisible : {e}")
    return sources


def _load_source_orientations() -> dict:
    """Map {label_source: orientation} depuis config/sources.yml."""
    return {s["label"]: s["orientation"] for s in _load_sources()}


def _decade(doc_date: str) -> str:
    """Renvoie la décennie (ex '1990s') depuis une date ISO/année, ou 'inconnu'."""
    if not doc_date:
        return "inconnu"
    s = str(doc_date)
    for i in range(len(s) - 3):
        chunk = s[i:i + 4]
        if chunk.isdigit():
            year = int(chunk)
            if 1400 <= year <= 2100:
                return f"{(year // 10) * 10}s"
    return "inconnu"


def _effective_score(doc: dict) -> int:
    """Score effectif : score_final si présent, sinon score_initial."""
    sf = doc.get("score_final")
    if sf is not None:
        return int(sf)
    return int(doc.get("score_initial", doc.get("latest_score", 0)) or 0)


def build_stats(catalog_path: Path = CATALOG_PATH,
                out_path: Path = OUT_PATH) -> dict:
    """Construit et écrit corpus_stats.json. Retourne le dict produit."""
    if not catalog_path.exists():
        print(f"[corpus_stats] catalog introuvable : {catalog_path}")
        return {"error": "no_catalog"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})
    orientations = _load_source_orientations()

    by_lang = Counter()
    by_source = Counter()
    by_decade = Counter()
    by_score = Counter()
    by_type = Counter()
    by_orientation = Counter()
    downloaded = 0
    published = 0  # score effectif >= 6

    for doc in docs.values():
        lang = doc.get("lang") or "inconnu"
        by_lang[lang] += 1

        source = doc.get("source") or "inconnu"
        by_source[source] += 1
        by_orientation[orientations.get(source, "non_renseigne")] += 1

        by_decade[_decade(doc.get("doc_date", ""))] += 1
        by_type[doc.get("doc_type") or "non_classe"] += 1

        score = _effective_score(doc)
        by_score[str(score)] += 1
        if score >= 6:
            published += 1

        if doc.get("downloaded"):
            downloaded += 1

    # Section honnête sur les biais : ce que la veille ne couvre pas
    total = len(docs)
    fr_share = round(100 * by_lang.get("fr", 0) / total, 1) if total else 0
    militant_share = round(
        100 * by_orientation.get("militant", 0) / total, 1) if total else 0

    biais = []
    if fr_share >= 55:
        biais.append(
            f"Corpus majoritairement francophone ({fr_share}%) — sous-représentation "
            "des sources anglophones, hispanophones, lusophones et du Sud global.")
    if militant_share >= 50:
        biais.append(
            f"Forte dominante militante ({militant_share}%) — les sources "
            "académiques et institutionnelles sont minoritaires.")
    if by_decade.get("inconnu", 0) > total * 0.3:
        biais.append(
            "Plus de 30% des documents n'ont pas de date de publication fiable.")
    biais.append(
        "La veille s'appuie sur des sources web accessibles : les corpus "
        "papier, oraux et hors-ligne sont structurellement absents.")

    # Liste complète des sources surveillées (pour la page Corpus), enrichie
    # du nombre de documents collectés chez chacune.
    sources_list = []
    for s in _load_sources():
        entry = dict(s)
        entry["count"] = by_source.get(s["label"], 0)
        sources_list.append(entry)
    sources_list.sort(key=lambda s: (-s["count"], s["label"].lower()))

    stats = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "total_docs": total,
        "total_downloaded": downloaded,
        "total_published": published,
        "by_lang": dict(by_lang.most_common()),
        "by_language": dict(by_lang.most_common()),
        "by_source": dict(by_source.most_common()),
        "by_decade": dict(sorted(by_decade.items())),
        "by_score": {str(i): by_score.get(str(i), 0) for i in range(11)},
        "by_doc_type": dict(by_type.most_common()),
        "by_orientation": dict(by_orientation.most_common()),
        "blind_spots": biais,
        "biais_connus": biais,
        "sources_list": sources_list,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[corpus_stats] {total} docs — écrit {out_path}")
    return stats


if __name__ == "__main__":
    build_stats()
