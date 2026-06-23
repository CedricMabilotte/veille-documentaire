#!/usr/bin/env python3
"""
archive_catalog.py — Archivage des documents hors-sujet du catalogue principal.

Déplace les documents éligibles de synopsis/catalog.json vers
synopsis/catalog_archive.json. Idempotent : peut être appelé plusieurs fois
sans risque de déplacer deux fois le même document.

Critères d'archivage (toutes conditions requises) :
  - score_initial ≤ 2     : signal thématique faible sur le titre
  - score_final is None   : jamais enrichi — pas de lecture PDF confirmée
  - downloaded is False   : pas de PDF local — pas de faux négatif possible
  - source dans NOISY_SOURCES : sources à bruit fort identifiées
  - score effectif < 6    : non publié (sécurité finale)

Sources conservées intentionnellement (faux négatifs probables) :
  - Infokiosques.net — Paysannerie & ruralité
  - toutes les sources HAL, CLACSO, ILC, Archive.org commons/CLT, etc.

Usage :
  python3 scripts/archive_catalog.py               # depuis la racine du projet
  python3 scripts/archive_catalog.py --dry-run     # simule sans modifier
  python3 scripts/archive_catalog.py --stats       # affiche les statistiques
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Sources à bruit fort ──────────────────────────────────────────────────────
# Ces sources produisent majoritairement du bruit par rapport à la thématique
# terres/communs/paysannerie. Les documents à score faible et sans enrichissement
# sont archivés plutôt que conservés dans le catalogue actif.
NOISY_SOURCES: frozenset[str] = frozenset({
    # Böll Stiftung — toutes variantes
    "Böll Stiftung — publications DE (deep crawl)",
    "Böll Stiftung — Agriculture Atlas (EN)",
    "Böll Stiftung — Meat Atlas",
    "Böll Stiftung — publications EN",
    "Böll Stiftung — publications DE",
    # Archive.org — flux anarchisme (pas les communs fonciers)
    "Archive.org — anarchism + land/peasant (strict)",
    "Archive.org — subject:anarchism (texts)",
    # The Anarchist Library
    "The Anarchist Library — OPDS (new releases)",
    "The Anarchist Library — OPDS feed",
    # Infokiosques.net — catégories hors paysannerie
    "Infokiosques.net — Anticapitalisme",
    "Infokiosques.net — Anticolonialismes",
    "Infokiosques.net — Squat (rapport à l'habiter)",
    "Infokiosques.net — Écologie radicale",
    "Infokiosques.net — index A",
    "Infokiosques.net — index C",
    "Infokiosques.net — index L (Libération, Luttes)",
    "Infokiosques.net — index T (Terres, Travail)",
    "Infokiosques.net — nouveautés",
    # NB : "Infokiosques.net — Paysannerie & ruralité" est intentionnellement
    # absent : trop de faux négatifs probables dans cette catégorie.
})

# Score initial maximal pour qu'un doc soit archivable (inclus)
SCORE_INITIAL_MAX = 2

# Seuil de publication (cohérent avec watch.py PUBLISH_THRESHOLD)
PUBLISH_THRESHOLD = 6


def _eff_score(doc: dict) -> int | float:
    """Score effectif : score_final si présent, sinon score_initial ou latest_score."""
    sf = doc.get("score_final")
    if sf is not None:
        return sf
    return doc.get("score_initial") or doc.get("latest_score", 0) or 0


def is_archivable(doc: dict) -> bool:
    """Retourne True si le document remplit tous les critères d'archivage."""
    si = doc.get("score_initial")
    # score_initial absent ou nul → compté comme 0 (archivable)
    si_val = si if si is not None else 0

    return (
        si_val <= SCORE_INITIAL_MAX
        and doc.get("score_final") is None       # jamais enrichi
        and not doc.get("downloaded", False)     # pas de PDF local
        and doc.get("source", "") in NOISY_SOURCES  # source à bruit fort
        and _eff_score(doc) < PUBLISH_THRESHOLD  # non publié
    )


def load_json(path: Path) -> dict:
    """Charge un fichier JSON ou retourne une structure vide."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  ⚠  JSON corrompu ({path}): {e}", file=sys.stderr)
    return {}


def save_json(path: Path, data: dict) -> None:
    """Écriture atomique (tmp + replace) pour éviter la corruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def run(
    catalog_path: Path,
    archive_path: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Déplace les docs éligibles du catalog vers l'archive.

    Retourne un dict avec :
      - moved       : nombre de docs déplacés ce run
      - already_archived : docs déjà présents dans l'archive (idempotence)
      - remaining   : taille du catalog après archivage
      - archive_total : taille de l'archive après archivage
    """
    catalog = load_json(catalog_path)
    archive = load_json(archive_path)

    if "docs" not in catalog:
        catalog["docs"] = {}
    if "docs" not in archive:
        archive["docs"] = {}

    to_archive: list[str] = []
    already_archived = 0

    for uid, doc in catalog["docs"].items():
        if not is_archivable(doc):
            continue
        if uid in archive["docs"]:
            already_archived += 1
            # Le doc est déjà dans l'archive mais encore dans le catalog —
            # on le marque pour suppression du catalog (idempotence)
            to_archive.append(uid)
        else:
            to_archive.append(uid)

    moved = 0
    for uid in to_archive:
        doc = catalog["docs"][uid]
        if uid not in archive["docs"]:
            archive["docs"][uid] = doc
            moved += 1

    # Supprimer du catalog
    for uid in to_archive:
        catalog["docs"].pop(uid, None)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Mettre à jour les méta du catalog
    catalog["meta"] = catalog.get("meta") or {}
    catalog["meta"].update({
        "last_updated": now,
        "total_docs": len(catalog["docs"]),
        "last_archive_run": now,
        "archived_total": len(archive["docs"]),
    })

    # Mettre à jour les méta de l'archive
    archive["meta"] = archive.get("meta") or {}
    archive["meta"].update({
        "last_updated": now,
        "total_docs": len(archive["docs"]),
        "description": (
            "Documents archivés — hors-sujet confirmé (score_initial ≤ 2, "
            "source à bruit fort, jamais enrichis, non téléchargés)."
        ),
        "criteria": {
            "score_initial_max": SCORE_INITIAL_MAX,
            "score_final_required": None,
            "downloaded_required": False,
            "noisy_sources": sorted(NOISY_SOURCES),
        },
    })

    if not dry_run:
        save_json(catalog_path, catalog)
        save_json(archive_path, archive)

    result = {
        "moved": moved,
        "already_archived": already_archived,
        "remaining": len(catalog["docs"]),
        "archive_total": len(archive["docs"]),
        "dry_run": dry_run,
    }

    if verbose:
        prefix = "[DRY-RUN] " if dry_run else ""
        print(
            f"  {prefix}archive_catalog : {moved} doc(s) archivé(s), "
            f"{already_archived} déjà présents, "
            f"{result['remaining']} restants dans le catalogue, "
            f"{result['archive_total']} dans l'archive"
        )

    return result


def print_stats(catalog_path: Path, archive_path: Path) -> None:
    """Affiche les statistiques des deux fichiers."""
    from collections import Counter

    catalog = load_json(catalog_path)
    archive = load_json(archive_path)
    cat_docs = catalog.get("docs", {})
    arc_docs = archive.get("docs", {})

    print(f"Catalogue principal : {len(cat_docs)} docs")
    print(f"Archive             : {len(arc_docs)} docs")
    print(f"Total               : {len(cat_docs) + len(arc_docs)} docs")

    if arc_docs:
        src_c = Counter(d.get("source", "") for d in arc_docs.values())
        print("\nDistribution de l'archive par source :")
        for s, c in sorted(src_c.items(), key=lambda x: -x[1]):
            print(f"  {c:4d}  {s}")

    # Docs encore archivables dans le catalog (si script non encore appliqué)
    remaining_archivable = sum(1 for d in cat_docs.values() if is_archivable(d))
    if remaining_archivable:
        print(f"\n⚠  {remaining_archivable} docs encore archivables dans le catalogue "
              f"(relancer sans --stats)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive les docs hors-sujet de synopsis/catalog.json "
                    "vers synopsis/catalog_archive.json."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simule sans modifier les fichiers."
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Affiche les statistiques et quitte."
    )
    parser.add_argument(
        "--catalog", default="synopsis/catalog.json",
        help="Chemin vers catalog.json (défaut: synopsis/catalog.json)"
    )
    parser.add_argument(
        "--archive", default="synopsis/catalog_archive.json",
        help="Chemin vers catalog_archive.json (défaut: synopsis/catalog_archive.json)"
    )
    args = parser.parse_args()

    # Résolution des chemins depuis la racine du projet (ou cwd)
    root = Path(__file__).parent.parent
    catalog_path = root / args.catalog
    archive_path = root / args.archive

    if args.stats:
        print_stats(catalog_path, archive_path)
        return 0

    result = run(
        catalog_path=catalog_path,
        archive_path=archive_path,
        dry_run=args.dry_run,
        verbose=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
