#!/usr/bin/env python3
"""audit_dates.py — Vérification fine des dates de publication des fiches publiées.

Contrôle le champ `doc_date` (date de publication de la source, distincte
des dates de run `collected_date`/`runs[].date`) pour chaque fiche
effectivement publiée sur le site (site/fiches/*.html).

Catégories de résultat, par gravité décroissante :
  VIDE                — doc_date absent ou vide
  FORMAT_INVALIDE     — ne correspond à aucun des formats attendus
                        (AAAA, AAAA-MM, AAAA-MM-JJ)
  PLAGE_RESIDUELLE    — deux années collées "AAAA-AAAA" : régression du
                        garde-fou posé en L12 (doc_metadata.py) contre les
                        plages historiques prises pour une date de publication
  ANNEE_FUTURE        — année postérieure à l'année en cours
  ANTERIEUR_COLLECTE  — doc_date postérieur à collected_date (impossible :
                        un doc ne peut pas être collecté avant d'être publié)
  TRES_ANCIEN         — année < 1800 : à confirmer manuellement (les textes
                        du fonds anarchiste du XIXe siècle sont légitimes,
                        mais plus ancien que ça devient suspect)
  A_VERIFIER_TITRE    — heuristique, informationnel seulement : le titre
                        contient une année significativement différente de
                        doc_date. Peut être un doc légitimement écrit sur un
                        événement passé (pas une erreur en soi) — à relire au
                        cas par cas, jamais à corriger automatiquement.

Usage : python3 scripts/audit_dates.py [--json rapport.json]
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT_YEAR = datetime.now().year

DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
RANGE_RE = re.compile(r"^(\d{4})-(\d{4})$")
YEAR_TOKEN_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")


def _year_of(date_str: str) -> int | None:
    m = re.match(r"^(\d{4})", date_str or "")
    return int(m.group(1)) if m else None


def audit_doc_date(uid: str, doc: dict) -> list[str]:
    doc_date = (doc.get("doc_date") or "").strip()
    issues: list[str] = []

    if not doc_date:
        return ["VIDE"]

    range_m = RANGE_RE.match(doc_date)
    if range_m:
        issues.append("PLAGE_RESIDUELLE")
    elif not DATE_RE.match(doc_date):
        issues.append("FORMAT_INVALIDE")
        return issues  # pas de vérifs supplémentaires sur un format non parseable

    year = _year_of(doc_date)
    if year is None:
        return issues

    if year > CURRENT_YEAR:
        issues.append("ANNEE_FUTURE")
    if year < 1800:
        issues.append("TRES_ANCIEN")

    collected = doc.get("collected_date") or ""
    collected_year = _year_of(collected)
    if collected_year and year > collected_year:
        issues.append("ANTERIEUR_COLLECTE")

    title = doc.get("title") or ""
    title_years = {int(y) for y in YEAR_TOKEN_RE.findall(title)}
    title_years.discard(year)
    if title_years:
        # Ne signale que si l'écart est net (>=3 ans) pour limiter le bruit
        # des docs légitimement écrits/rétrospectifs sur un événement passé.
        if any(abs(ty - year) >= 3 for ty in title_years):
            issues.append("A_VERIFIER_TITRE")

    return issues


def run() -> list[dict]:
    with open(ROOT / "synopsis" / "catalog.json") as f:
        data = json.load(f)
    docs = data["docs"]

    fiches_uids = {
        f.replace(".html", "")
        for f in os.listdir(ROOT / "site" / "fiches")
        if f.endswith(".html") and len(f) == 13
    }

    problems = []
    for uid in sorted(fiches_uids):
        d = docs.get(uid) or {}
        issues = audit_doc_date(uid, d)
        if issues:
            problems.append({
                "uid": uid,
                "title": (d.get("title") or "")[:60],
                "doc_date": d.get("doc_date", ""),
                "collected_date": d.get("collected_date", ""),
                "issues": issues,
            })

    counts: dict[str, int] = {}
    for p in problems:
        for i in p["issues"]:
            counts[i] = counts.get(i, 0) + 1

    print(f"Fiches publiées auditées : {len(fiches_uids)}")
    print(f"Fiches avec un signalement : {len(problems)}\n")
    for cat in ("VIDE", "FORMAT_INVALIDE", "PLAGE_RESIDUELLE", "ANNEE_FUTURE",
                "ANTERIEUR_COLLECTE", "TRES_ANCIEN", "A_VERIFIER_TITRE"):
        print(f"  {cat:20s} {counts.get(cat, 0)}")
    print()

    graves = [p for p in problems
              if any(i != "A_VERIFIER_TITRE" and i != "TRES_ANCIEN" for i in p["issues"])]
    for p in graves:
        print(f"[{p['uid']}] {', '.join(p['issues'])}  {p['title']}")
        print(f"  doc_date={p['doc_date']!r}  collected_date={p['collected_date']!r}")
        print()

    return problems


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="chemin de sortie JSON détaillé")
    args = parser.parse_args()
    results = run()
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Détail JSON écrit dans {args.json}")
