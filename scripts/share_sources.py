#!/usr/bin/env python3
"""
share_sources.py — Coopération inter-agents thématiques.

Permet à plusieurs instances de l'outil de veille (chacune avec sa thématique)
de partager leurs sources validées via un repo central qui agrège un YAML
`shared_sources.yml`.

  - export_my_sources()       : génère un YAML décrivant les sources actives
                                de cet agent avec leur fertilité.
  - pull_shared_sources()      : télécharge un shared_sources.yml distant.
  - suggest_cross_pollination() : score Jaccard entre mes mots-clés et ceux
                                  d'autres agents → suggestions.
  - run()                      : pipeline complet (export + pull + suggest).

Pure stdlib + requests + PyYAML.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests
import yaml


# ── Helpers candidates.yml ───────────────────────────────────────────────────
def _load_candidates(path: Path) -> dict:
    if not path.exists():
        return {"candidates": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"candidates": []}


def _save_candidates(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def _merge_candidate(data: dict, candidate: dict) -> bool:
    url = candidate.get("url", "").strip()
    if not url:
        return False
    for c in data.get("candidates", []):
        if c.get("url") == url:
            return False
    data.setdefault("candidates", []).append(candidate)
    return True


# ── Fertilité (à partir des reports) ────────────────────────────────────────
def _compute_fertility(reports_dir: Path) -> dict[str, dict]:
    """Pour chaque source label, calcule : nb_runs, nb_docs_total, nb_dl_total."""
    stats: dict[str, dict] = defaultdict(
        lambda: {"runs": 0, "docs_seen": 0, "docs_dl": 0})
    if not reports_dir.exists():
        return {}
    for rep in sorted(reports_dir.glob("run_*.json")):
        try:
            data = json.loads(rep.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Compte les runs uniques par source
        seen_in_run: set = set()
        for doc in data.get("results", []):
            src = doc.get("source", "?")
            stats[src]["docs_seen"] += 1
            if doc.get("downloaded"):
                stats[src]["docs_dl"] += 1
            seen_in_run.add(src)
        for src in seen_in_run:
            stats[src]["runs"] += 1
    # Score fertilité = ratio dl / runs (clamped)
    for src, s in stats.items():
        s["fertility"] = round(s["docs_dl"] / max(s["runs"], 1), 2)
    return dict(stats)


def export_my_sources(sources_path: Path,
                      project_name: str,
                      project_keywords: list[str],
                      out_path: Path,
                      reports_dir: Path | None = None) -> dict:
    """Génère un YAML décrivant les sources actives + fertilité.

    Format : {project_name, project_keywords, exported_at,
              sources: [{url, label, type, fertility, runs, docs_dl, docs_seen}]}
    """
    cfg = yaml.safe_load(sources_path.read_text(encoding="utf-8")) \
        if sources_path.exists() else {"sources": []}
    reports_dir = reports_dir or sources_path.parent.parent / "reports"
    fertility = _compute_fertility(reports_dir)

    exported_sources = []
    for s in cfg.get("sources", []):
        label = s.get("label", "")
        f = fertility.get(label, {})
        exported_sources.append({
            "url": s.get("url"),
            "label": label,
            "type": s.get("type", "html"),
            "fertility": f.get("fertility", 0.0),
            "runs": f.get("runs", 0),
            "docs_dl": f.get("docs_dl", 0),
            "docs_seen": f.get("docs_seen", 0),
        })

    payload = {
        "project_name": project_name,
        "project_keywords": project_keywords,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "sources": exported_sources,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    return payload


def pull_shared_sources(remote_yaml_url: str,
                        timeout: int = 30) -> list[dict]:
    """Télécharge un shared_sources.yml distant (raw GitHub URL).

    Retourne une liste plate : [{url, label, type, project_name,
    project_keywords, fertility, ...}].
    """
    try:
        r = requests.get(remote_yaml_url, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"  pull failed: {e}", file=sys.stderr)
        return []
    try:
        data = yaml.safe_load(r.text) or {}
    except Exception as e:
        print(f"  yaml parse failed: {e}", file=sys.stderr)
        return []

    # Format attendu : soit liste de projets (clé "projects"), soit projet seul
    flat: list[dict] = []
    projects = data.get("projects") or [data]
    for proj in projects:
        pname = proj.get("project_name", "?")
        pkw = proj.get("project_keywords", []) or []
        for s in proj.get("sources", []) or []:
            entry = dict(s)
            entry["project_name"] = pname
            entry["project_keywords"] = pkw
            flat.append(entry)
    return flat


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    """Jaccard simple sur deux listes de chaînes (case-insensitive)."""
    sa = {x.lower().strip() for x in a if x}
    sb = {x.lower().strip() for x in b if x}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def suggest_cross_pollination(my_keywords: list[str],
                              their_sources: list[dict],
                              threshold: float = 0.3) -> list[dict]:
    """Pour chaque source d'un autre agent, calcule un score d'overlap.

    Retourne les sources dont overlap ≥ threshold, triées par overlap décroissant.
    """
    suggestions = []
    for s in their_sources:
        their_kw = s.get("project_keywords", []) or []
        overlap = _jaccard(my_keywords, their_kw)
        if overlap >= threshold:
            suggestions.append({
                **s,
                "overlap_score": round(overlap, 3),
            })
    suggestions.sort(key=lambda x: x["overlap_score"], reverse=True)
    return suggestions


def _write_report(report_path: Path,
                  exported: dict,
                  pulled_count: int,
                  cross_polli: list[dict]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Share sources — {now}",
        "",
        f"## Export local — `{exported['project_name']}`",
        "",
        f"- Sources exportées : **{len(exported['sources'])}**",
        f"- Mots-clés : {exported['project_keywords'][:10]}",
        "",
        "### Top sources par fertilité",
        "",
    ]
    top = sorted(exported["sources"],
                 key=lambda x: x.get("fertility", 0), reverse=True)[:10]
    for s in top:
        lines.append(
            f"- **{s.get('label', '?')}** — fertility "
            f"{s.get('fertility')} ({s.get('docs_dl')} dl / "
            f"{s.get('runs')} runs)")
    lines += [
        "",
        f"## Pull distant — **{pulled_count}** sources trouvées",
        "",
        f"## Cross-pollination — **{len(cross_polli)}** suggestions",
        "",
    ]
    for s in cross_polli[:20]:
        lines.append(
            f"- [{s.get('overlap_score')}] `{s.get('project_name')}` → "
            f"{s.get('url')} ({s.get('label', '')})")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run(sources_path: Path,
        candidates_path: Path,
        project_name: str = "communs-terres-paysannerie",
        project_keywords: list[str] | None = None,
        export_out: Path | None = None,
        remote_url: str | None = None,
        report_path: Path | None = None,
        threshold: float = 0.3) -> dict:
    """Pipeline complet : export local + pull distant + cross-pollinations."""
    root = sources_path.parent.parent
    export_out = export_out or root / "discovery" / "shared_export.yml"
    report_path = report_path or (
        root / "discovery" / "reports"
        / f"share_sources_{datetime.now().strftime('%Y-%m-%d')}.md")

    # Lit project_keywords depuis sources.yml si non fourni
    if project_keywords is None:
        cfg = yaml.safe_load(sources_path.read_text(encoding="utf-8")) \
            if sources_path.exists() else {}
        project_keywords = cfg.get("keywords", [])

    exported = export_my_sources(
        sources_path, project_name, project_keywords, export_out)

    their_sources: list[dict] = []
    cross_polli: list[dict] = []
    if remote_url:
        their_sources = pull_shared_sources(remote_url)
        cross_polli = suggest_cross_pollination(
            project_keywords, their_sources, threshold=threshold)

        # Ajoute les cross-pollinations aux candidates.yml
        cands = _load_candidates(candidates_path)
        now_iso = datetime.now(timezone.utc).isoformat()
        added = 0
        for s in cross_polli:
            cand = {
                "url": s.get("url"),
                "type": "cross_pollination",
                "source_type": s.get("type"),
                "label": s.get("label"),
                "from_project": s.get("project_name"),
                "overlap_score": s.get("overlap_score"),
                "fertility": s.get("fertility"),
                "discovered_at": now_iso,
            }
            if _merge_candidate(cands, cand):
                added += 1
        _save_candidates(candidates_path, cands)
    else:
        added = 0

    _write_report(report_path, exported, len(their_sources), cross_polli)
    return {
        "exported_sources": len(exported["sources"]),
        "pulled_sources": len(their_sources),
        "cross_pollinations": len(cross_polli),
        "added_to_candidates": added,
        "export_path": str(export_out),
        "report": str(report_path),
    }


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    out = run(
        sources_path=root / "config" / "sources.yml",
        candidates_path=root / "discovery" / "candidates.yml",
        # remote_url=None : exporte sans importer (mode initial)
        remote_url=None,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
