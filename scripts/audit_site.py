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
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import watch  # noqa: E402  — _is_publishable, prédicat de publication
import editorial  # noqa: E402  — _doc_title, logique canonique de titre

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CATALOG = ROOT / "synopsis" / "catalog.json"


class SiteRef:
    """Lecture de `site/` depuis la bonne référence.

    `site/` est reconstruit par la CI (rebuild-site.yml) puis poussé sur
    origin/main ; il n'est jamais régénéré dans l'arbre de travail local, et le
    checkout local est un clone partiel. Auditer la copie du disque depuis un
    poste produisait donc des alertes entièrement fausses (18/09 : 4 contrôles
    en défaut, dont 192 « divergences de titres », alors que le site publié
    n'en avait aucune). La référence est donc :

    - l'arbre de travail quand on tourne dans la CI (site/ vient d'y être
      reconstruit et n'est pas encore poussé) ;
    - `origin/main` partout ailleurs.

    Forçable par la variable d'environnement BIBLIO_AUDIT_SITE=worktree|git.
    """

    def __init__(self) -> None:
        mode = os.environ.get("BIBLIO_AUDIT_SITE", "").strip().lower()
        if mode not in ("worktree", "git"):
            mode = "worktree" if os.environ.get("GITHUB_ACTIONS") else "git"
        if mode == "git" and not self._git_ok():
            mode = "worktree"
        self.mode = mode
        self.label = "arbre de travail" if mode == "worktree" else "origin/main"

    @staticmethod
    def _git_ok() -> bool:
        r = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                            "origin/main:site/sitemap.xml"], capture_output=True)
        return r.returncode == 0

    def _git(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)

    def exists(self, rel: str) -> bool:
        if self.mode == "worktree":
            return (SITE / rel).exists()
        return self._git("cat-file", "-e", f"origin/main:site/{rel}").returncode == 0

    def read_text(self, rel: str) -> str:
        if self.mode == "worktree":
            return (SITE / rel).read_text(encoding="utf-8")
        r = self._git("show", f"origin/main:site/{rel}")
        return r.stdout.decode("utf-8", "replace")

    def listdir(self, sub: str, suffix: str) -> list[str]:
        """Noms de fichiers de `site/<sub>` se terminant par `suffix`."""
        if self.mode == "worktree":
            d = SITE / sub
            if not d.is_dir():
                return []
            return [f.name for f in d.glob(f"*{suffix}")]
        r = self._git("ls-tree", "--name-only", f"origin/main:site/{sub}")
        if r.returncode != 0:
            return []
        return [n for n in r.stdout.decode().split("\n")
                if n.endswith(suffix)]

    def read_many(self, rels: list[str]) -> dict[str, str]:
        """Lecture groupée — un seul `git cat-file --batch` au lieu de N appels."""
        if self.mode == "worktree":
            out = {}
            for rel in rels:
                f = SITE / rel
                if f.exists():
                    out[rel] = f.read_text(encoding="utf-8")
            return out
        req = "".join(f"origin/main:site/{rel}\n" for rel in rels)
        r = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch"],
                           input=req.encode(), capture_output=True)
        out, buf, i = {}, r.stdout, 0
        for rel in rels:
            nl = buf.find(b"\n", i)
            if nl < 0:
                break
            header = buf[i:nl].decode("utf-8", "replace")
            if header.endswith("missing"):
                i = nl + 1
                continue
            size = int(header.rsplit(" ", 1)[1])
            out[rel] = buf[nl + 1:nl + 1 + size].decode("utf-8", "replace")
            i = nl + 1 + size + 1
        return out


SITE_REF = SiteRef()

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


class DEFERRED(list):
    """Contrôle non exécuté ici, et qui le dit — ni succès, ni échec.

    Un garde-fou qui signale à tort finit ignoré (18/09) : un contrôle qu'on
    choisit de ne pas faire sur ce poste doit s'annoncer comme différé, pas
    passer pour une anomalie.
    """

    def __init__(self, raison: str):
        super().__init__([raison])
        self.raison = raison


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
        suffix = pattern.lstrip("*")
        orphans = []
        for name in SITE_REF.listdir(sub, suffix):
            doc_id = _doc_id_of(name[: -len(suffix)], docs)
            if doc_id is not None and doc_id not in publishable:
                orphans.append(name)
        if orphans:
            problems.append(
                f"{sub}/ : {len(orphans)} orphelin(s) — ex. {orphans[0]}"
            )
    return problems


def check_sitemap(publishable: set) -> list[str]:
    """Le sitemap doit lister exactement les fiches publiables, toutes
    présentes sur le disque."""
    if not SITE_REF.exists("sitemap.xml"):
        return ["sitemap.xml absent"]
    listed = set(re.findall(r"fiches/([0-9a-f]{8})\.html",
                            SITE_REF.read_text("sitemap.xml")))
    on_disk = {n[:-5] for n in SITE_REF.listdir("fiches", ".html")
               if ID_RE.match(n[:-5])}

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
    concernes = [i for i in sorted(publishable)
                 if (docs[i].get("lang") or "").strip()]
    # Ce contrôle est le seul à lire le contenu de centaines de fiches. Dans la
    # CI, elles sont sur le disque et la lecture est immédiate. En local, elles
    # sont lues depuis origin/main : sur ce dépôt (historique volumineux,
    # compactage automatique en retard), une lecture groupée de ~800 objets
    # prend plus d'une minute. On le diffère alors explicitement plutôt que de
    # le faire silencieusement sur l'arbre de travail, qui est périmé.
    if SITE_REF.mode == "git" and not os.environ.get("BIBLIO_AUDIT_LANG_FULL"):
        return DEFERRED(f"{len(concernes)} fiches à lire depuis origin/main ; "
                       f"le contrôle tourne à chaque rebuild-site.yml — pour le "
                       f"forcer ici : BIBLIO_AUDIT_LANG_FULL=1")
    fiches = SITE_REF.read_many([f"fiches/{i}.html" for i in concernes])
    for doc_id in concernes:
        contenu = fiches.get(f"fiches/{doc_id}.html")
        if contenu is None:
            continue
        real = (docs[doc_id].get("lang") or "").strip().lower()
        m = re.search(r'"inLanguage":\s*"([^"]*)"', contenu)
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
    if not license_file.exists():
        return ["fichier LICENSE absent"]
    if not SITE_REF.exists("apropos.html"):
        return ["site/apropos.html absent — licence du site non vérifiable"]
    lic = _detect_license(license_file.read_text(encoding="utf-8"))
    site = _detect_license(SITE_REF.read_text("apropos.html"))
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

    if SITE_REF.exists("data/dossiers.json"):
        data = json.loads(SITE_REF.read_text("data/dossiers.json"))
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

    if SITE_REF.exists("data/featured.json"):
        data = json.loads(SITE_REF.read_text("data/featured.json"))
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
          f"{len(publishable)} publiables "
          f"— site/ lu depuis : {SITE_REF.label}\n")
    failed = 0
    for name, problems in checks:
        if isinstance(problems, DEFERRED):
            print(f"  ⏭  {name} — différé : {problems.raison}")
        elif problems:
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
