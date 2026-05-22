#!/usr/bin/env python3
"""
editorial.py — Dossiers éditoriaux & document de la semaine (items A7, A3).

A7 — Dossiers éditoriaux nommés par lutte :
  Lit la section `dossiers` de config/concepts.yml (dossiers définis
  éditorialement, avec chapô et mots-clés de rattachement) et produit
  synopsis/dossiers.json rattachant chaque document du catalog aux dossiers
  pertinents.

A3 — Document de la semaine :
  Produit synopsis/featured.json identifiant le meilleur document récent
  (score_final le plus haut sur les N derniers jours).

Pur Python (json, yaml). Aucune autre dépendance.

Usage autonome :
  python scripts/editorial.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"
CONCEPTS_PATH = ROOT / "config" / "concepts.yml"
DOSSIERS_OUT = ROOT / "synopsis" / "dossiers.json"
FEATURED_OUT = ROOT / "synopsis" / "featured.json"

FEATURED_WINDOW_DAYS = 21


def _load_dossiers_config() -> list[dict]:
    """Lit la liste `dossiers` de concepts.yml. [] si absente."""
    if not CONCEPTS_PATH.exists():
        return []
    try:
        import yaml
        cfg = yaml.safe_load(CONCEPTS_PATH.read_text(encoding="utf-8")) or {}
        return cfg.get("dossiers", []) or []
    except Exception as e:
        print(f"  ⚠  concepts.yml illisible : {e}")
        return []


def _effective_score(doc: dict) -> int:
    sf = doc.get("score_final")
    if sf is not None:
        return int(sf)
    return int(doc.get("score_initial", doc.get("latest_score", 0)) or 0)


def _doc_haystack(doc: dict) -> str:
    """Concatène tout le texte exploitable d'un doc pour le matching de mots-clés."""
    parts = [
        doc.get("filename", ""),
        doc.get("source", ""),
    ]
    for r in doc.get("runs", []) or []:
        parts.append(r.get("link_text", ""))
        parts.append(r.get("raison", ""))
    enrich = doc.get("enrichment") or {}
    if isinstance(enrich, dict):
        parts.append(enrich.get("summary", ""))
        kws = enrich.get("matched_keywords", []) or []
        parts.extend(str(k) for k in kws)
    return " ".join(p for p in parts if p).lower()


def _doc_title(doc: dict) -> str:
    if doc.get("runs"):
        t = doc["runs"][-1].get("link_text", "")
        if t:
            return t
    t = doc.get("filename", "")
    return t.rsplit(".", 1)[0] if "." in t else t


def build_dossiers(catalog_path: Path = CATALOG_PATH,
                   out_path: Path = DOSSIERS_OUT) -> dict:
    """Rattache les docs aux dossiers éditoriaux. Écrit dossiers.json."""
    dossiers_cfg = _load_dossiers_config()
    if not dossiers_cfg:
        print("[editorial] aucun dossier défini dans concepts.yml")
    if not catalog_path.exists():
        print(f"[editorial] catalog introuvable : {catalog_path}")
        return {"error": "no_catalog"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})

    result_dossiers = []
    for d in dossiers_cfg:
        slug = d.get("slug", "")
        keywords = [str(k).lower() for k in (d.get("keywords", []) or [])]
        matched: list[dict] = []
        for doc_id, doc in docs.items():
            # On ne range que les docs publiables
            if _effective_score(doc) < 6:
                continue
            hay = _doc_haystack(doc)
            hits = [k for k in keywords if k and k in hay]
            if hits:
                matched.append({
                    "id": doc_id,
                    "title": _doc_title(doc),
                    "score": _effective_score(doc),
                    "matched_on": hits,
                })
        matched.sort(key=lambda x: -x["score"])
        result_dossiers.append({
            "slug": slug,
            "titre": d.get("titre", slug),
            "chapo": (d.get("chapo", "") or "").strip(),
            "doc_count": len(matched),
            "docs": [m["id"] for m in matched],
            "docs_detail": matched,
        })

    out = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_dossiers": len(result_dossiers),
        "dossiers": result_dossiers,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[editorial] dossiers.json : {len(result_dossiers)} dossiers")
    return out


def _run_dt(run_str: str):
    """Parse une date de run 'YYYY-MM-DD_HH-MM' en datetime UTC."""
    try:
        return datetime.strptime(run_str, "%Y-%m-%d_%H-%M").replace(
            tzinfo=timezone.utc)
    except Exception:
        return None


def build_featured(catalog_path: Path = CATALOG_PATH,
                   out_path: Path = FEATURED_OUT,
                   window_days: int = FEATURED_WINDOW_DAYS) -> dict:
    """Identifie le 'document de la semaine' : meilleur score_final récent."""
    if not catalog_path.exists():
        print(f"[editorial] catalog introuvable : {catalog_path}")
        return {"error": "no_catalog"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})
    now = datetime.now(timezone.utc)

    candidates = []
    for doc_id, doc in docs.items():
        score = doc.get("score_final")
        if score is None:
            continue  # le document de la semaine exige un score post-lecture
        latest = _run_dt(doc.get("latest_run", ""))
        recent = True
        if latest is not None:
            recent = (now - latest).days <= window_days
        candidates.append((doc_id, doc, int(score), recent))

    # Priorité : récent d'abord, puis score, puis date
    candidates.sort(key=lambda c: (c[3], c[2],
                                   _run_dt(c[1].get("latest_run", "")) or now),
                    reverse=True)

    out = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": window_days,
        "featured": None,
    }
    if candidates:
        doc_id, doc, score, recent = candidates[0]
        enrich = doc.get("enrichment") or {}
        out["featured"] = {
            "id": doc_id,
            "title": _doc_title(doc),
            "score_final": score,
            "score_initial": doc.get("score_initial",
                                     doc.get("latest_score", 0)),
            "source": doc.get("source", ""),
            "doc_date": doc.get("doc_date", ""),
            "lang": doc.get("lang", ""),
            "doc_type": doc.get("doc_type", ""),
            "summary": (enrich.get("summary", "")[:600]
                        if isinstance(enrich, dict) else ""),
            "is_recent": recent,
            "fiche_url": f"/fiches/{doc_id}.html",
        }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    feat = out["featured"]
    print(f"[editorial] featured.json : "
          f"{feat['title'] if feat else 'aucun candidat'}")
    return out


if __name__ == "__main__":
    build_dossiers()
    build_featured()
