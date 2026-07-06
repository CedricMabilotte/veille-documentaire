#!/usr/bin/env python3
"""audit_citations.py — Vérification fine des citations des fiches publiées.

Re-exécute la même recherche littérale que `synopsis_enricher.verify_citations()`
contre le texte du PDF actuellement disponible sur disque, et compare le
résultat au champ `verified` déjà stocké dans le catalogue au moment de
l'enrichissement (item A4 — anti-hallucination). Contrairement à
l'enrichissement d'origine (limité à ~12000 caractères de texte extrait),
cet audit relit le document en quasi-intégralité (MAX_CHARS très large) pour
ne pas signaler une régression qui ne serait due qu'à une fenêtre de lecture
plus courte à l'époque.

Ne modifie jamais le catalogue — rapport seul.

Catégories de résultat par citation :
  CONFIRME              — verified=true à l'enrichissement, toujours vérifié
  REGRESSION            — verified=true à l'enrichissement, ne matche plus
                           (à examiner : dérive de citation, PDF remplacé,
                           extraction différente)
  JAMAIS_VERIFIE        — non vérifié à l'enrichissement ET toujours introuvable
                           (citation potentiellement fabriquée ou mal transcrite)
  NOUVELLEMENT_VERIFIE  — non vérifié à l'enrichissement, matche maintenant
                           (PDF récupéré depuis, ou extraction améliorée)
  PDF_ABSENT            — aucun PDF local exploitable : non vérifiable
  FORMAT_NON_PDF        — fichier local présent mais pas un PDF (epub/txt/odt) :
                           extract_text ne s'applique pas, non vérifiable ainsi
  PDF_INVALIDE_LOCAL    — fichier .pdf présent mais ne commence pas par les
                          magic bytes %PDF (`pdf_processor.validate_pdf()`
                          échoue) : souvent une page de blocage anti-bot
                          (ex. Anubis sur HAL) sauvegardée par erreur à la
                          place du vrai document — non vérifiable, ET perte
                          de la copie locale de la source

Usage : python3 scripts/audit_citations.py [--json rapport.json]
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pdf_processor                       # noqa: E402
from synopsis_enricher import verify_citations  # noqa: E402

MAX_CHARS_AUDIT = 2_000_000  # quasi-intégral : ne pas rater une citation tardive


def _local_pdf_path(uid: str, doc: dict) -> Path | None:
    """Retrouve le PDF local du doc, via `saved_as` (source unique) avec repli
    sur la convention docs/<id>_<filename> si `saved_as` est absent."""
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


def audit_doc_citations(uid: str, doc: dict) -> list[dict]:
    """Retourne une liste de résultats (un par citation) pour ce doc, ou []
    si le doc n'a pas de citations."""
    enrich = doc.get("enrichment") or {}
    citations = enrich.get("citations") or []
    if not isinstance(citations, list) or not citations:
        return []

    pdf_path = _local_pdf_path(uid, doc)
    results = []

    if pdf_path is None:
        for c in citations:
            if not isinstance(c, dict):
                continue
            results.append({
                "uid": uid, "categorie": "PDF_ABSENT",
                "stored_verified": bool(c.get("verified")),
                "quote": (c.get("quote") or "")[:160],
                "page_annoncee": c.get("page"),
            })
        return results

    if pdf_path.suffix.lower() != ".pdf":
        for c in citations:
            if not isinstance(c, dict):
                continue
            results.append({
                "uid": uid, "categorie": "FORMAT_NON_PDF",
                "stored_verified": bool(c.get("verified")),
                "quote": (c.get("quote") or "")[:160],
                "page_annoncee": c.get("page"),
                "format": pdf_path.suffix.lower(),
            })
        return results

    if not pdf_processor.validate_pdf(pdf_path):
        for c in citations:
            if not isinstance(c, dict):
                continue
            results.append({
                "uid": uid, "categorie": "PDF_INVALIDE_LOCAL",
                "stored_verified": bool(c.get("verified")),
                "quote": (c.get("quote") or "")[:160],
                "page_annoncee": c.get("page"),
            })
        return results

    title = doc.get("title") or ""
    text = pdf_processor.extract_text(pdf_path, max_chars=MAX_CHARS_AUDIT,
                                       doc_title=title, skip_cover=True)
    reverified = verify_citations(citations, text)

    for orig, fresh in zip(citations, reverified):
        if not isinstance(orig, dict):
            continue
        was = bool(orig.get("verified"))
        now = bool(fresh.get("verified"))
        if was and now:
            cat = "CONFIRME"
        elif was and not now:
            cat = "REGRESSION"
        elif not was and now:
            cat = "NOUVELLEMENT_VERIFIE"
        else:
            cat = "JAMAIS_VERIFIE"
        results.append({
            "uid": uid, "categorie": cat,
            "stored_verified": was, "reverified": now,
            "quote": (orig.get("quote") or "")[:160],
            "page_annoncee": orig.get("page"),
            "page_physique_enrichissement": orig.get("page_physical"),
            "page_physique_audit": fresh.get("page_physical"),
        })
    return results


def run() -> list[dict]:
    with open(ROOT / "synopsis" / "catalog.json") as f:
        data = json.load(f)
    docs = data["docs"]

    fiches_uids = {
        f.replace(".html", "")
        for f in os.listdir(ROOT / "site" / "fiches")
        if f.endswith(".html") and len(f) == 13
    }

    all_results = []
    docs_avec_citations = 0
    for uid in sorted(fiches_uids):
        d = docs.get(uid) or {}
        res = audit_doc_citations(uid, d)
        if res:
            docs_avec_citations += 1
            for r in res:
                r["title"] = (d.get("title") or "")[:60]
            all_results.extend(res)

    counts: dict[str, int] = {}
    for r in all_results:
        counts[r["categorie"]] = counts.get(r["categorie"], 0) + 1

    print(f"Fiches publiées auditées : {len(fiches_uids)}")
    print(f"Fiches avec citations    : {docs_avec_citations}")
    print(f"Citations examinées      : {len(all_results)}")
    for cat in ("CONFIRME", "REGRESSION", "JAMAIS_VERIFIE",
                "NOUVELLEMENT_VERIFIE", "PDF_ABSENT", "FORMAT_NON_PDF",
                "PDF_INVALIDE_LOCAL"):
        print(f"  {cat:22s} {counts.get(cat, 0)}")
    print()

    for r in all_results:
        if r["categorie"] in ("REGRESSION", "JAMAIS_VERIFIE", "PDF_INVALIDE_LOCAL"):
            print(f"[{r['uid']}] {r['categorie']}  {r['title']}")
            print(f"  quote (p.{r.get('page_annoncee')}) : {r['quote']}")
            print()

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="chemin de sortie JSON détaillé")
    args = parser.parse_args()
    results = run()
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Détail JSON écrit dans {args.json}")
