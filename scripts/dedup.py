#!/usr/bin/env python3
"""
dedup.py — Détection de doublons de PDFs par SHA-256 du contenu.

Maintient un registre `synopsis/duplicates.json` :
{
  "by_hash": { "<sha256>": ["doc_id_1", "doc_id_2", ...], ... },
  "by_doc":  { "doc_id_1": "<sha256>", ... },
  "meta":    { "last_update": "...", "total_pdfs": N, "duplicate_clusters": K }
}

Permet :
- d'enregistrer un nouveau PDF et de savoir s'il duplique un existant,
- de récupérer les grappes de doublons,
- de produire un rapport statistique (économie d'espace potentielle).

Pure Python (hashlib, json). Aucune dépendance externe.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# Chemin par défaut du registre
_DEFAULT_REGISTRY = Path(__file__).parent.parent / "synopsis" / "duplicates.json"

# Taille du buffer de lecture (64 Kio : bon compromis débit/RAM)
_CHUNK = 64 * 1024


def compute_hash(pdf_path: Path) -> str:
    """SHA-256 du contenu binaire du fichier. Lève FileNotFoundError si absent."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _load_registry(registry_path: Path) -> dict:
    """Charge le registre ou retourne une structure vierge."""
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  ! registre corrompu, repart de zéro : {registry_path}")
    return {"by_hash": {}, "by_doc": {}, "meta": {}}


def _save_registry(registry: dict, registry_path: Path) -> None:
    """Recalcule meta puis écrit le JSON (atomique : tmp + replace)."""
    by_hash = registry.get("by_hash", {})
    by_doc = registry.get("by_doc", {})
    clusters = sum(1 for ids in by_hash.values() if len(ids) > 1)
    registry["meta"] = {
        "last_update": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_pdfs": len(by_doc),
        "duplicate_clusters": clusters,
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = registry_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    tmp.replace(registry_path)


def register_pdf(pdf_path: Path, doc_id: str,
                 catalog_path: Path | None = None) -> dict:
    """Calcule le hash, l'ajoute au registre et signale les doublons.

    `catalog_path` est conservé pour compat API mais sert juste à dériver le
    chemin du registre (synopsis/duplicates.json dans le même dossier).
    """
    if catalog_path is not None:
        registry_path = catalog_path.parent / "duplicates.json"
    else:
        registry_path = _DEFAULT_REGISTRY

    registry = _load_registry(registry_path)
    sha = compute_hash(pdf_path)

    bucket = registry["by_hash"].setdefault(sha, [])
    is_new = doc_id not in bucket
    duplicate_of = bucket[0] if bucket and bucket[0] != doc_id else None
    if is_new:
        bucket.append(doc_id)
    registry["by_doc"][doc_id] = sha
    _save_registry(registry, registry_path)

    return {"is_new": is_new, "duplicate_of": duplicate_of, "hash": sha}


def find_clusters(synopsis_path: Path) -> list[list[str]]:
    """Retourne la liste des grappes de doc_ids partageant le même hash (>1)."""
    registry_path = (synopsis_path
                     if synopsis_path.name == "duplicates.json"
                     else synopsis_path.parent / "duplicates.json")
    registry = _load_registry(registry_path)
    return [sorted(ids) for ids in registry["by_hash"].values() if len(ids) > 1]


def report(registry_path: Path = _DEFAULT_REGISTRY,
           pdf_dir: Path | None = None) -> dict:
    """Statistiques globales : total, uniques, doublons, espace gagné (Mo)."""
    registry = _load_registry(registry_path)
    by_hash = registry["by_hash"]
    total = sum(len(ids) for ids in by_hash.values())
    uniques = len(by_hash)
    duplicates = total - uniques

    # Espace potentiellement récupérable : taille (hash → 1er doc_id présent)
    saved_bytes = 0
    if pdf_dir is not None:
        for sha, ids in by_hash.items():
            if len(ids) <= 1:
                continue
            sample = next((p for p in pdf_dir.glob(f"{ids[0]}*.pdf")), None)
            if sample is not None and sample.exists():
                # Chaque doublon supplémentaire = taille gagnée
                saved_bytes += sample.stat().st_size * (len(ids) - 1)

    return {
        "total_pdfs": total,
        "unique_hashes": uniques,
        "duplicate_count": duplicates,
        "duplicate_clusters": sum(1 for ids in by_hash.values() if len(ids) > 1),
        "saved_bytes_estimate": saved_bytes,
        "saved_mb_estimate": round(saved_bytes / (1024 * 1024), 2),
    }


# ── Validation CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    docs_dir = root / "docs"
    covers_dir = root / "interface" / "covers"
    registry_path = root / "synopsis" / "duplicates.json"

    print(f"Scan de {docs_dir} ...")
    count = 0
    for pdf in sorted(docs_dir.glob("*.pdf")):
        # doc_id = préfixe avant le premier "_" (cf. convention du projet)
        doc_id = pdf.stem.split("_", 1)[0]
        res = register_pdf(pdf, doc_id, catalog_path=registry_path)
        count += 1
        if res["duplicate_of"]:
            print(f"  ⚠ {doc_id} duplique {res['duplicate_of']} (sha={res['hash'][:10]}…)")
    print(f"→ {count} PDF(s) traité(s)")

    # On scanne aussi les couvertures, pour la démo (PNG ⇒ SHA distinct)
    if covers_dir.exists():
        cov_count = sum(1 for _ in covers_dir.glob("*.png"))
        print(f"  (couvertures présentes : {cov_count} PNG — non incluses)")

    stats = report(registry_path=registry_path, pdf_dir=docs_dir)
    clusters = find_clusters(registry_path)
    print("\n── Rapport ──")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if clusters:
        print(f"\n  Grappes de doublons ({len(clusters)}) :")
        for c in clusters[:5]:
            print(f"    {c}")
