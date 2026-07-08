#!/usr/bin/env python3
"""
audit_site.py — Contrôle de cohérence du site publié.

Garde-fou de la routine de fin de session (étape 5) et du pipeline : vérifie
que les artefacts générés dans site/ sont synchronisés avec le catalogue et
entre eux. Cible les désynchronisations silencieuses qui ont, par le passé,
vécu longtemps sans être repérées :

  1. Orphelins      — fiche / bulle / couverture / carte d'un doc non publiable.
  2. Sitemap        — le sitemap liste exactement les fiches publiables, et
                      chacune existe sur le disque.
  3. Langue JSON-LD — l'inLanguage des fiches pré-rendues reflète la langue
                      réelle du document (et non un 'fr' figé).
  4. Licence        — la licence nommée dans LICENSE est celle annoncée sur le
                      site (page Méthodologie).
  5. Titres         — le titre affiché dans dossiers.json/featured.json
     éditoriaux       correspond à _doc_title() (editorial.py) appliqué aux
                      données actuelles du catalogue. Attrape toute nouvelle
                      divergence entre la logique de titre du pré-rendu
                      statique et celle du catalogue (cf. lecons-biblio.md
                      L49 : _doc_title() avait dérivé de doc["title"] pendant
                      plusieurs sessions sans qu'aucun contrôle ne le
                      détecte).

Sortie : code 0 si tout est cohérent, 1 sinon. Rapport lisible sur stdout.

Usage : python3 scripts/audit_site.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import watch  # noqa: E402  — _is_publishable, prédicat de publication
import editorial  # noqa: E402  — _doc_title, logique canonique de titre

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CATALOG = ROOT / "synopsis" / "catalog.json"

ID_RE = re.compile(r"^[0-9a-f]{8}$")


def _load_docs() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8")).get("docs", {})


def _doc_id_of(stem: str, docs: dict):
    """Identifiant de doc préfixant un nom de fichier généré, sinon None
    (gabarit statique ou fichier hors-corpus).

    On teste uniquement le format (8 hex) — pas la présence dans docs — pour
    attraper aussi les UIDs qui ont quitté le catalogue (archivés, supprimés).
    """
    head = stem[:8]
    return head if ID_RE.match(head) else None


def check_orphans(docs: dict, publishable: set) -> list[str]:
    """Aucun fichier par-document ne doit subsister pour un doc non publiable."""
    problems = []
    targets = [
        ("fiches", "*.html"),
        ("data/bulles", "*.json"),
        ("assets/covers", "*.png"),
        ("assets/cards", "*.jpg"),
    ]
    for sub, pattern in targets:
        directory = SITE / sub
        if not directory.is_dir():
            continue
        orphans = []
        for f in directory.glob(pattern):
            doc_id = _doc_id_of(f.stem, docs)
            if doc_id is not None and doc_id not in publishable:
                orphans.append(f.name)
        if orphans:
            problems.append(
                f"{sub}/ : {len(orphans)} orphelin(s) — ex. {orphans[0]}"
            )
    return problems


def check_sitemap(publishable: set) -> list[str]:
    """Le sitemap doit lister exactement les fiches publiables, toutes
    présentes sur le disque."""
    sitemap = SITE / "sitemap.xml"
    if not sitemap.exists():
        return ["sitemap.xml absent"]
    listed = set(re.findall(r"fiches/([0-9a-f]{8})\.html",
                            sitemap.read_text(encoding="utf-8")))
    fiches_dir = SITE / "fiches"
    on_disk = {f.stem for f in fiches_dir.glob("*.html") if ID_RE.match(f.stem)}

    problems = []
    missing_file = listed - on_disk
    if missing_file:
        problems.append(
            f"sitemap : {len(missing_file)} fiche(s) listée(s) mais absente(s) "
            f"du disque — ex. {sorted(missing_file)[0]}"
        )
    not_listed = publishable - listed
    if not_listed:
        problems.append(
            f"sitemap : {len(not_listed)} doc(s) publiable(s) absent(s) du "
            f"sitemap — ex. {sorted(not_listed)[0]}"
        )
    stale_listed = listed - publishable
    if stale_listed:
        problems.append(
            f"sitemap : {len(stale_listed)} fiche(s) listée(s) non "
            f"publiable(s) — ex. {sorted(stale_listed)[0]}"
        )
    return problems


def check_lang(docs: dict, publishable: set) -> list[str]:
    """L'inLanguage du JSON-LD d'une fiche pré-rendue doit refléter la langue
    réelle du document quand celle-ci est connue."""
    problems = []
    mismatches = []
    for doc_id in publishable:
        fiche = SITE / "fiches" / f"{doc_id}.html"
        if not fiche.exists():
            continue
        real = (docs[doc_id].get("lang") or "").strip().lower()
        if not real:
            continue  # langue inconnue : 'fr' par défaut, on ne tranche pas
        m = re.search(r'"inLanguage":\s*"([^"]*)"',
                      fiche.read_text(encoding="utf-8"))
        got = (m.group(1) if m else "").strip().lower()
        if got != real:
            mismatches.append(f"{doc_id} (doc={real or '∅'}, fiche={got or '∅'})")
    if mismatches:
        problems.append(
            f"langue : {len(mismatches)} fiche(s) avec inLanguage erroné — "
            f"ex. {mismatches[0]}"
        )
    return problems


def _detect_license(text: str):
    """Identifiant normalisé de licence repéré dans un texte, sinon None."""
    low = text.lower()
    if "peer production" in low:
        return "Peer Production License"
    if ("cc-by-nc-sa" in low or "cc by-nc-sa" in low
            or "attribution-noncommercial-sharealike" in low
            or "by-nc-sa" in low):
        return "CC BY-NC-SA 4.0"
    return None


def check_license() -> list[str]:
    """La licence du fichier LICENSE doit être celle annoncée sur le site."""
    license_file = ROOT / "LICENSE"
    apropos = SITE / "apropos.html"
    if not license_file.exists():
        return ["fichier LICENSE absent"]
    if not apropos.exists():
        return ["site/apropos.html absent — licence du site non vérifiable"]
    lic = _detect_license(license_file.read_text(encoding="utf-8"))
    site = _detect_license(apropos.read_text(encoding="utf-8"))
    if lic is None:
        return ["LICENSE : licence non reconnue"]
    if site is None:
        return ["apropos.html : aucune licence annoncée"]
    if lic != site:
        return [f"licence : LICENSE='{lic}' ≠ site='{site}'"]
    return []


def check_editorial_titles(docs: dict) -> list[str]:
    """Le titre affiché dans dossiers.json/featured.json doit correspondre à
    _doc_title() (scripts/editorial.py) appliqué aux données actuelles du
    catalogue. Garde-fou posé après L49 (2026-07-07) : ces deux JSON sont
    générés une fois puis committés — rien ne les revalide si _doc_title()
    change de logique, ou si un doc["title"] est corrigé après coup sans
    relancer editorial.build_dossiers()/build_featured()."""
    problems = []
    mismatches = []

    dossiers_path = SITE / "data" / "dossiers.json"
    if dossiers_path.exists():
        data = json.loads(dossiers_path.read_text(encoding="utf-8"))
        for dossier in data.get("dossiers", []):
            for entry in dossier.get("docs_detail", []):
                doc_id = entry.get("id")
                doc = docs.get(doc_id)
                if doc is None:
                    continue  # doc archivé/supprimé : hors périmètre de ce contrôle
                expected = editorial._doc_title(doc)
                got = entry.get("title", "")
                if got != expected:
                    mismatches.append(
                        f"{doc_id} (dossiers.json='{got}', attendu='{expected}')"
                    )

    featured_path = SITE / "data" / "featured.json"
    if featured_path.exists():
        data = json.loads(featured_path.read_text(encoding="utf-8"))
        feat = data.get("featured")
        if feat:
            doc_id = feat.get("id")
            doc = docs.get(doc_id)
            if doc is not None:
                expected = editorial._doc_title(doc)
                got = feat.get("title", "")
                if got != expected:
                    mismatches.append(
                        f"{doc_id} (featured.json='{got}', attendu='{expected}')"
                    )

    if mismatches:
        problems.append(
            f"{len(mismatches)} divergence(s) entre dossiers.json/"
            f"featured.json et _doc_title() — ex. {mismatches[0]} — "
            f"relancer editorial.build_dossiers()/build_featured() puis "
            f"republier"
        )
    return problems


def main() -> int:
    docs = _load_docs()
    publishable = {i for i, d in docs.items() if watch._is_publishable(d)}

    checks = [
        ("Orphelins", check_orphans(docs, publishable)),
        ("Sitemap", check_sitemap(publishable)),
        ("Langue JSON-LD", check_lang(docs, publishable)),
        ("Licence", check_license()),
        ("Titres éditoriaux", check_editorial_titles(docs)),
    ]

    print(f"audit_site — {len(docs)} docs au catalogue, "
          f"{len(publishable)} publiables\n")
    failed = 0
    for name, problems in checks:
        if problems:
            failed += 1
            print(f"  ✗  {name}")
            for p in problems:
                print(f"       {p}")
        else:
            print(f"  ✓  {name}")

    if failed:
        print(f"\nÉCHEC — {failed} contrôle(s) en défaut.")
        return 1
    print("\nOK — site cohérent avec le catalogue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
