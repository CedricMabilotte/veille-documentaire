#!/usr/bin/env python3
"""backfill_dates.py — Backfill de `doc_date` pour les fiches publiées qui
n'en ont aucun, en réutilisant `doc_metadata.build_metadata()` (source
unique de la logique de date — même garde-fous qu'à l'ingestion normale :
seuil ≥1950 pour les heuristiques filename/URL/context, ≥1800 pour les
sources autoritatives (métadonnées PDF, src_meta), masquage des plages
"AAAA-AAAA", pas d'invention d'une date pour un texte ancien sans preuve
d'édition (cf. L12, `Discours de la servitude volontaire` reste sans date
si rien ne l'atteste — ne PAS lui attribuer une date récente par défaut).

Calcul en parallèle (multiprocessing, lecture seule des PDF locaux — aucune
écriture concurrente possible pendant le calcul). Une seule écriture finale,
après relecture fraîche de catalog.json juste avant, pour minimiser la
fenêtre de collision avec toute autre session qui travaillerait en parallèle
sur ce même dépôt.

Crédibilité avant confirmation : une date n'est appliquée automatiquement
que si sa source est franche (métadonnée PDF ou heuristique déjà filtrée par
les seuils de doc_metadata) ET qu'elle ne contredit pas franchement une
année bien identifiée dans le titre (écart ≥ 3 ans → écarté, listé à part
pour arbitrage manuel plutôt que deviné).

Usage :
  python3 scripts/backfill_dates.py              # dry-run, rapport
  python3 scripts/backfill_dates.py --apply       # écrit catalog.json
"""

import argparse
import json
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

YEAR_TOKEN_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")


def _local_pdf_path(uid: str, doc: dict) -> Path | None:
    saved_as = doc.get("saved_as")
    if saved_as:
        p = ROOT / saved_as if not os.path.isabs(saved_as) else Path(saved_as)
        if p.exists():
            return p
    fname = doc.get("filename")
    if fname:
        p = ROOT / "docs" / f"{uid}_{fname}"
        if p.exists():
            return p
    return None


def _worker(item: tuple[str, dict]) -> dict:
    """Calcule un candidat doc_date pour un doc. Tourne dans un worker séparé
    (aucun état partagé, lecture seule sur disque).

    N'applique la simple confiance de `build_metadata()` : une métadonnée PDF
    `creationDate` reflète souvent la date de NUMÉRISATION/export du fichier,
    pas la date de publication réelle — dangereux pour les textes anciens
    republiés (ex. un classique de 1926 numérisé en 2025). Ce worker calcule
    donc, en plus du candidat, tous les indices textuels (title/link_text/
    context/filename/url) pour permettre à l'appelant de exiger une
    corroboration textuelle avant de faire confiance à une pure métadonnée
    PDF sans témoin dans le texte."""
    uid, doc = item
    import pdf_processor
    import doc_metadata

    pdf_path = _local_pdf_path(uid, doc)
    pdf_meta = {}
    if pdf_path and pdf_path.suffix.lower() == ".pdf" and pdf_processor.validate_pdf(pdf_path):
        pdf_meta = pdf_processor.extract_metadata(pdf_path)

    runs = doc.get("runs") or []
    last_run = runs[-1] if runs else {}
    context = last_run.get("context_seen", "") or ""
    link_text = last_run.get("link_text", "") or ""
    shim = dict(doc)
    shim["context"] = context
    shim["link_text"] = link_text

    meta = doc_metadata.build_metadata(shim, pdf_meta=pdf_meta, pdf_text="",
                                        source_default_lang=doc.get("lang", ""))
    candidate = meta.get("doc_date", "")

    evidence = "aucune"
    if candidate:
        if pdf_meta.get("creationDate") and candidate in str(pdf_meta.get("creationDate")):
            evidence = "pdf_metadata"
        else:
            evidence = "heuristique(filename/url/context)"

    title = doc.get("title") or ""
    # Tous les indices textuels disponibles — pas seulement le titre : un
    # "(1926 edition)" vit typiquement dans context/link_text, pas le titre.
    textual_blob = " ".join(filter(None, [
        title, link_text, context, doc.get("filename", ""), doc.get("url", ""),
    ]))
    textual_years = {int(y) for y in YEAR_TOKEN_RE.findall(textual_blob)}
    cand_year = int(candidate[:4]) if candidate and candidate[:4].isdigit() else None

    conflict = None
    corroborated = False
    if cand_year:
        others = textual_years - {cand_year}
        conflicting = [y for y in others if abs(y - cand_year) >= 3]
        if conflicting:
            conflict = sorted(conflicting)
        corroborated = cand_year in textual_years

    # Confiance : haute seulement si un indice TEXTUEL (pas juste la
    # métadonnée PDF brute) corrobore l'année candidate. Une métadonnée PDF
    # seule, sans aucun témoin dans le texte, reste une numérisation non
    # datée à vue humaine — pas une preuve de publication.
    if conflict:
        confidence = "conflit"
    elif corroborated:
        confidence = "haute"
    elif evidence == "heuristique(filename/url/context)":
        # extract_doc_date() a déjà extrait ce candidat DEPUIS le texte —
        # c'est en soi un témoin textuel, même si le regex générique ci-dessus
        # ne l'a pas capté à l'identique (ex. format non couvert par le regex
        # de contrôle mais bien lu par extract_doc_date).
        confidence = "moyenne"
    else:
        confidence = "basse"  # candidat = seulement pdf_metadata, sans témoin textuel

    return {
        "uid": uid, "candidate": candidate, "evidence": evidence,
        "confidence": confidence, "conflict_years": conflict,
        "title": title[:60],
    }


def run(apply: bool) -> None:
    cat_path = ROOT / "synopsis" / "catalog.json"
    with open(cat_path, encoding="utf-8") as f:
        catalog = json.load(f)
    docs = catalog["docs"]

    fiches_uids = {
        f[:-5] for f in os.listdir(ROOT / "site" / "fiches")
        if f.endswith(".html") and len(f) == 13
    }

    todo = [(uid, docs[uid]) for uid in sorted(fiches_uids)
            if uid in docs and not (docs[uid].get("doc_date") or "").strip()]
    print(f"Fiches publiées sans doc_date : {len(todo)}")

    with mp.Pool(processes=min(8, max(1, os.cpu_count() or 4))) as pool:
        results = pool.map(_worker, todo)

    applied, moyenne, conflicts, basse, no_candidate = [], [], [], [], []
    for r in results:
        if not r["candidate"]:
            no_candidate.append(r)
        elif r["confidence"] == "conflit":
            conflicts.append(r)
        elif r["confidence"] == "haute":
            applied.append(r)
        elif r["confidence"] == "moyenne":
            moyenne.append(r)
        else:
            basse.append(r)

    print(f"\nConfiance HAUTE — corroborée par un indice textuel (appliqué) : {len(applied)}")
    for r in applied:
        print(f"  [{r['uid']}] {r['candidate']:12s} ({r['evidence']:28s}) {r['title']}")

    print(f"\nConfiance MOYENNE — extrait par l'heuristique texte mais non recoupé au mot "
          f"près par le contrôle indépendant (NON appliqué par prudence, à valider) : {len(moyenne)}")
    for r in moyenne:
        print(f"  [{r['uid']}] {r['candidate']:12s} ({r['evidence']:28s}) {r['title']}")

    print(f"\nConfiance BASSE — SEULE preuve = métadonnée PDF brute, aucun témoin "
          f"textuel (NON appliqué, à vérifier à la main) : {len(basse)}")
    for r in basse:
        print(f"  [{r['uid']}] candidat={r['candidate']!r}  {r['title']}")

    print(f"\nConflit — le candidat contredit une année clairement citée dans le "
          f"texte (titre/lien/contexte) (NON appliqué, à ARBITRER) : {len(conflicts)}")
    for r in conflicts:
        print(f"  [{r['uid']}] candidat={r['candidate']!r} vs années citées={r['conflict_years']}  {r['title']}")

    print(f"\nAucun candidat trouvé (reste vide, incompressible sans nouvelle source) : {len(no_candidate)}")

    if apply and applied:
        # Relecture fraîche juste avant écriture — minimise la fenêtre de
        # collision avec une autre session qui modifierait catalog.json.
        with open(cat_path, encoding="utf-8") as f:
            fresh_catalog = json.load(f)
        fresh_docs = fresh_catalog["docs"]
        n_written = 0
        for r in applied:
            uid = r["uid"]
            if uid in fresh_docs and not (fresh_docs[uid].get("doc_date") or "").strip():
                fresh_docs[uid]["doc_date"] = r["candidate"]
                n_written += 1
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(fresh_catalog, f, ensure_ascii=False, indent=2)
        print(f"\ncatalog.json réécrit — {n_written} doc_date renseignés.")
    elif not apply:
        print("\n(dry-run — rien n'a été écrit ; relancer avec --apply)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(args.apply)
