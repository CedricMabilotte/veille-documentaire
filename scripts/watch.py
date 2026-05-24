#!/usr/bin/env python3
"""
Outil de veille documentaire — scrape des sites, score avec Claude, télécharge les docs pertinents.

Architecture modulaire :
- Le dispatcher scripts/parsers/__init__.py choisit le bon parser selon `type:`
  défini dans chaque source de config/sources.yml.
- Types supportés : html, deep_html, opds, archive_org, hal.

Scoring : via Claude Code CLI (OAuth, consomme la subscription Pro/Max).

Usage :
  python scripts/watch.py
  python scripts/watch.py  # DRY_RUN=true pour simulation sans téléchargement
"""

import os
import sys
import json
import yaml
import hashlib
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse

# Ajouter scripts/ au PYTHONPATH pour pouvoir importer parsers/ et utilitaires
sys.path.insert(0, str(Path(__file__).parent))
from parsers import dispatch as parser_dispatch
import pdf_processor
import synopsis_enricher
import bibliography_extractor
import dedup
import fulltext_index
import throttle
import discovery_external_links
import discovery_bibliography
import discovery_footnotes
import discovery_promote
import doc_metadata
import link_check
import corpus_stats
import editorial
import export_bibtex
from prompt_version import prompt_hash
try:
    import social_cards
except Exception:  # Pillow absent : dégradation propre
    social_cards = None

# ── Chemins ────────────────────────────────────────────────────────────────────
CONFIG_PATH    = Path("config/sources.yml")
DOCS_PATH      = Path("docs")
REPORTS_PATH   = Path("reports")
SYNOPSIS_PATH  = Path("synopsis")        # catalog.json (multi-runs, dédupliqué)
INTERFACE_PATH = Path("interface")       # index.html — fiches synopsis
COVERS_PATH    = INTERFACE_PATH / "covers"  # PNG des couvertures (page 1)
BULLES_PATH    = Path("bulles")          # JSON par doc ≥ 9 (publi troisiemesvoix)

for p in (DOCS_PATH, REPORTS_PATH, SYNOPSIS_PATH, INTERFACE_PATH, COVERS_PATH, BULLES_PATH):
    p.mkdir(parents=True, exist_ok=True)

# ── Constantes ─────────────────────────────────────────────────────────────────
BATCH_SIZE = 8
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def file_uid(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


# Modèle utilisé pour le scoring sur titre (cf. invocation claude plus bas)
SCORING_MODEL = "claude-haiku-4-5"


def score_batch(docs: list[dict], keywords: list[str]) -> list[dict]:
    """Score un lot via Claude Code CLI (OAuth, consomme la subscription).

    Chaque entrée retournée contient, en plus de doc/score/raison :
      - `doc_type` (A1) : typologie documentaire
      - `recit_de_lutte` (C3) : booléen, texte racontant une lutte/victoire
      - `prompt_version` (C6) : hash du prompt de scoring utilisé
    """
    if not docs:
        return []

    docs_block = ""
    for i, d in enumerate(docs, 1):
        docs_block += (
            f"\nDocument {i} :\n"
            f"  Lien    : {d['link_text']}\n"
            f"  Format  : {d['extension'].upper()}\n"
            f"  Contexte: {d['context']}\n"
        )

    keywords_block = "\n".join(f"  - {kw}" for kw in keywords)

    prompt = f"""Tu es un assistant de veille documentaire STRICT et RIGOUREUX.

THÉMATIQUE ciblée — concepts qui doivent être au CŒUR du document, pas en marge :
{keywords_block}

RÈGLES DE NOTATION (à appliquer scrupuleusement) :

1. **Note basée UNIQUEMENT sur le titre et le contexte fournis.**
   N'INFÈRE PAS le contenu d'un document à partir de son auteur supposé,
   d'une école de pensée ou d'un mot isolé. Si le titre/contexte ne mentionne
   pas explicitement un des thèmes ci-dessus, score ≤ 4.

2. **Pas de "probablement", "vraisemblablement", "fondamental sur".**
   Si la raison contient ces mots, baisse ton score d'au moins 3 points.

3. **L'appartenance à l'anarchisme, au libertarianisme, à l'écologie,
   au féminisme, à l'antifascisme ou au syndicalisme N'EST PAS suffisante
   pour mériter un score élevé.** Beaucoup de textes libertaires/anarchistes
   ne parlent PAS de la thématique terres/communs. Score ≤ 5 dans ce cas.

4. **Échelle :**
   - 9-10 : le titre OU le contexte cite explicitement un mot-clé central
            (communs fonciers, paysannerie, sans-terre, propriété d'usage,
            réforme agraire, zapatistes, Tierra y Libertad…)
   - 7-8  : le titre OU le contexte évoque clairement la thématique
            par un terme proche, sans hallucination
   - 5-6  : tangentiel — le sujet pourrait recouper la thématique mais
            ce n'est pas explicite dans ce qui m'est fourni
   - 0-4  : hors-sujet ou indéterminable (titre obscur, contexte vide)

5. **Cite littéralement** dans ta raison le mot/phrase du titre ou du contexte
   qui justifie ton score. Si tu ne peux pas citer → score ≤ 3.

6. **Attribue chaque score au bon "doc" numéro**. Ne mélange pas.

7. **Typologie documentaire** — classe chaque document dans `doc_type` :
   - "essai"           : texte de réflexion, argumentaire théorique
   - "enquete"         : enquête de terrain, reportage documenté
   - "guide_pratique"  : manuel, mode d'emploi, ressource actionnable
   - "modele_juridique": bail type, statuts GFA/SCI, modèle de contrat
   - "retour_collectif": retour d'expérience d'un collectif, témoignage
   - "tract"           : tract, brochure courte de mobilisation
   - "rapport"         : rapport institutionnel, étude commanditée
   - "source_primaire" : archive, document d'époque, texte historique brut
   - "autre"           : si rien ne correspond clairement
   Base-toi sur le titre/contexte ; en cas de doute, mets "autre".

8. **Récit de lutte** — `recit_de_lutte` vaut true UNIQUEMENT si le
   titre/contexte indique que le texte RACONTE une lutte, une victoire ou
   une action concrète (terre reprise, foncière créée, expulsion stoppée,
   occupation racontée). false sinon (texte purement théorique/analytique).

Pour chaque document, retourne :
  - "doc"            : numéro du document (entier)
  - "score"          : 0 à 10
  - "raison"         : phrase brève citant LITTÉRALEMENT le titre/contexte
  - "doc_type"       : une des valeurs de la règle 7
  - "recit_de_lutte" : true ou false (règle 8)

EXEMPLES DE BONNES NOTATIONS :

  Document : "la_commune_p._kropotkine.pdf" — contexte "La Commune par Kropotkine, 1881"
  → {{"score": 6, "raison": "Texte sur la Commune de Paris ; recoupe la thématique communs/collectif sans la cibler"}}

  Document : "louis_rimbault_terre_liberee.pdf" — contexte "Louis Rimbault, Terre Libérée, 1905"
  → {{"score": 9, "raison": "Titre 'Terre Libérée' cite explicitement la libération des terres"}}

  Document : "affaire_8_decembre_2020-cahier.pdf" — contexte "perquisition antiterroriste 8 décembre 2020"
  → {{"score": 1, "raison": "Affaire de répression antiterroriste, hors thématique terres/communs"}}

  Document : "ni_dieu_ni_maitre.pdf" — contexte "Ni dieu ni maître ni ordre moral, slogan anarchiste"
  → {{"score": 2, "raison": "Slogan anarchiste général, aucun lien explicite avec terres/communs"}}

Réponds UNIQUEMENT avec un tableau JSON valide, sans balise markdown.

Documents :
{docs_block}"""

    try:
        result = subprocess.run(
            [
                "claude",
                "-p", prompt,
                "--model", "claude-haiku-4-5",
                "--output-format", "text",
                "--no-session-persistence",
                "--disable-slash-commands",
                "--tools", "",
                "--dangerously-skip-permissions",
            ],
            capture_output=True,
            text=True,
            timeout=180,
            cwd="/tmp",
            stdin=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"claude exit {result.returncode} — "
                f"stdout={result.stdout[:200]} stderr={result.stderr[:200]}"
            )
        raw = result.stdout.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0]
        parsed = json.loads(raw.strip())
        # Migration douce + C6 : on garantit les champs et le prompt_version
        pv = prompt_hash(prompt)
        for item in parsed:
            if isinstance(item, dict):
                item.setdefault("doc_type", "autre")
                item.setdefault("recit_de_lutte", False)
                item["prompt_version"] = pv
                item["model"] = SCORING_MODEL
        return parsed
    except Exception as e:
        print(f"  ⚠  Erreur scoring Claude : {e}")
        pv = prompt_hash(prompt)
        return [{"doc": i, "score": 0, "raison": "erreur scoring",
                 "doc_type": "autre", "recit_de_lutte": False,
                 "prompt_version": pv, "model": SCORING_MODEL}
                for i in range(1, len(docs) + 1)]


def download_file(url: str, dest: Path) -> bool:
    """Download standard. Le caller doit ensuite valider via pdf_processor."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  ⚠  Téléchargement échoué pour {url} : {e}")
        return False


def _archive_org_variants(url: str) -> list[str]:
    """Génère des URL alternatives pour les liens archive.org/download/<id>/<file>.

    Stratégie : Archive.org expose souvent un même item sous plusieurs formats
    (PDF natif, OCR _djvu.txt, version _text.pdf). Quand l'URL fournie renvoie
    404, on tente :
      1. swap des suffixes (_text.pdf / _djvu.txt → .pdf)
      2. <base>/<identifier>.pdf (fichier "canonique" à la racine du record)
      3. parcours du JSON /metadata/<identifier> pour récupérer le premier .pdf
    """
    variants: list[str] = []
    if "archive.org/download/" not in url:
        return variants

    # On isole <base>=https://archive.org/download/<identifier> et <filename>
    try:
        prefix, rest = url.split("archive.org/download/", 1)
        parts = rest.split("/", 1)
        identifier = parts[0]
        filename = parts[1] if len(parts) > 1 else ""
        base = f"{prefix}archive.org/download/{identifier}"
    except Exception:
        return variants

    # 1. Variantes locales sur le filename
    if filename:
        if filename.endswith("_text.pdf"):
            variants.append(f"{base}/{filename[:-len('_text.pdf')]}.pdf")
        if filename.endswith("_djvu.txt"):
            variants.append(f"{base}/{filename[:-len('_djvu.txt')]}.pdf")

    # 2. <base>/<identifier>.pdf — fichier "canonique" du record
    canonical = f"{base}/{identifier}.pdf"
    if canonical != url and canonical not in variants:
        variants.append(canonical)

    # 3. Listing du record via l'API metadata (JSON)
    try:
        meta_url = f"https://archive.org/metadata/{identifier}"
        r = requests.get(meta_url, headers=HEADERS, timeout=8)
        if r.ok:
            data = r.json()
            for f in (data.get("files") or []):
                name = f.get("name", "")
                if name.lower().endswith(".pdf"):
                    candidate = f"{base}/{name}"
                    if candidate != url and candidate not in variants:
                        variants.append(candidate)
                    break  # on prend le premier .pdf trouvé
    except Exception as e:
        print(f"     ⚠  metadata archive.org indisponible : {e}")

    return variants


def download_and_validate(url: str, dest: Path) -> tuple[bool, str]:
    """Pipeline complet : HEAD probe → download → validate → bypass si besoin.

    1. HEAD rapide (timeout 8s) : si 200 + content-type pdf/octet-stream, on continue.
    2. Si 404 et URL archive.org : on tente des variantes (_text.pdf → .pdf,
       <id>.pdf, et listing /metadata/<id>).
    3. Sinon pipeline standard (download → validate → bypass UA → Playwright).

    Retourne (success, status) où status ∈
      {'ok', 'ok_via_variant', 'ok_via_browser', 'ok_via_playwright',
       'failed_invalid_format', 'failed_network',
       'failed_404_after_variants', 'failed_captcha'}.
    """
    # 1. HEAD rapide pour détecter les 404 avant de tout télécharger
    head_status = None
    try:
        head = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        head_status = head.status_code
        ctype = (head.headers.get("content-type") or "").lower()
        if head.ok and ("pdf" in ctype or "octet-stream" in ctype):
            # Cas nominal : on enchaîne sur le download standard
            pass
        elif head.status_code == 404 and "archive.org/download/" in url:
            # 2. 404 sur archive.org → on tente les variantes
            variants = _archive_org_variants(url)
            for variant in variants:
                print(f"     ↻  Variante archive.org testée : {variant}")
                try:
                    vh = requests.head(variant, headers=HEADERS, timeout=8,
                                       allow_redirects=True)
                except Exception:
                    continue
                if vh.ok:
                    if download_file(variant, dest) and pdf_processor.validate_pdf(dest):
                        return True, "ok_via_variant"
            return False, "failed_404_after_variants"
        # Pour les autres codes (403, 5xx…) on laisse le pipeline standard tenter
    except Exception as e:
        # Si le HEAD échoue (timeout, DNS…), on laisse le download tenter sa chance
        print(f"     ⚠  HEAD échec ({e}), on tente le download direct")

    if not download_file(url, dest):
        # Le download peut avoir échoué sur 404 ; tenter les variantes archive.org
        if "archive.org/download/" in url:
            variants = _archive_org_variants(url)
            for variant in variants:
                print(f"     ↻  Variante archive.org (post-fail) : {variant}")
                if download_file(variant, dest) and pdf_processor.validate_pdf(dest):
                    return True, "ok_via_variant"
            if variants:
                return False, "failed_404_after_variants"
        return False, "failed_network"

    if pdf_processor.validate_pdf(dest):
        return True, "ok"

    # Faux PDF détecté → essai bypass UA navigateur
    print(f"     ↻  Faux PDF détecté, retry avec UA navigateur…")
    ok, err = pdf_processor.redownload_with_bypass(url, dest)
    if ok:
        return True, "ok_via_browser"

    # Dernier recours : Playwright pour les sites avec JS challenge (HAL etc.)
    print(f"     ↻  Bypass UA insuffisant ({err}), retry avec Playwright…")
    ok, err = pdf_processor.download_with_playwright(url, dest)
    if ok:
        return True, "ok_via_playwright"

    # Échec total — supprimer le faux fichier
    if dest.exists():
        dest.unlink()
    return False, f"failed_captcha ({err})"


def analyse_pdf_and_enrich(dest: Path, doc: dict, score: int,
                            keywords: list[str]) -> dict:
    """Pour un PDF validé : extrait couverture, texte, et appelle Claude pour
    le synopsis enrichi. Si score ≥ 9, génère aussi la bulle de publication.

    Retourne un dict avec : cover_path, summary, citations,
    matched_keywords, relevance_score, bulle, references (si applicable).
    """
    out = {}
    uid = file_uid(doc["url"])

    # 0. Déduplication par hash de contenu : skip Claude si déjà vu ailleurs
    try:
        dedup_result = dedup.register_pdf(
            dest, uid, catalog_path=SYNOPSIS_PATH / "catalog.json"
        )
        if dedup_result["duplicate_of"]:
            print(f"     ♻  Doublon de {dedup_result['duplicate_of']} "
                  f"(hash={dedup_result['hash'][:10]}…) — skip enrichissement")
            out["duplicate_of"] = dedup_result["duplicate_of"]
            out["content_hash"] = dedup_result["hash"]
            return out
        out["content_hash"] = dedup_result["hash"]
    except Exception as e:
        print(f"     ⚠  dedup raté : {e}")

    # Métadonnées + premières pages
    meta = pdf_processor.extract_metadata(dest)
    out["meta"] = {
        "page_count":  meta.get("page_count", 0),
        "pdf_title":   meta.get("title", ""),
        "pdf_author":  meta.get("author", ""),
        "pdf_creator": meta.get("creator", ""),
    }

    # Couverture page 1 → PNG
    cover_path = COVERS_PATH / f"{uid}.png"
    if pdf_processor.extract_cover(dest, cover_path, max_width=400):
        out["cover"] = f"covers/{uid}.png"   # chemin relatif depuis interface/
        print(f"     🖼  Couverture extraite : {out['cover']}")

    # Extraction des références bibliographiques (boucle de découverte)
    try:
        refs = bibliography_extractor.extract_references(dest, max_refs=30)
        if refs:
            out["references"] = refs
            print(f"     📚  {len(refs)} référence(s) bibliographique(s) extraite(s)")
    except Exception as e:
        print(f"     ⚠  extraction refs ratée : {e}")

    # Synopsis enrichi via Claude (sur le texte du PDF)
    text = pdf_processor.extract_text(dest, max_chars=10000)

    # ── S2 — Métadonnées bibliographiques fiables ────────────────────────────
    # doc_date / lang / editeur / doi / isbn / hal_id, sans jamais inférer
    # un auteur absent de la source (anonymat respecté).
    try:
        bib = doc_metadata.build_metadata(doc, pdf_meta=meta, pdf_text=text)
        out["bib"] = bib
    except Exception as e:
        print(f"     ⚠  build_metadata raté : {e}")
        out["bib"] = {}

    if text:
        print(f"     📖  Texte extrait ({len(text)} chars), enrichissement…")
        title_hint = doc.get("link_text") or doc["filename"]
        enrichment = synopsis_enricher.enrich(text, keywords, title_hint)
        out["enrichment"] = enrichment

        if "error" in enrichment:
            print(f"     ⚠  Enrichissement raté : {enrichment['error']}")
        else:
            print(f"     ✨  Synopsis : {len(enrichment.get('summary', ''))} chars, "
                  f"{len(enrichment.get('citations', []))} citations, "
                  f"score post-lecture = {enrichment.get('relevance_score', '?')}/10")

            # Bulle de publication pour les meilleurs scores
            if score >= 9 or enrichment.get("relevance_score", 0) >= 9:
                print(f"     📝  Génération de la bulle de publication…")
                bulle = synopsis_enricher.generate_bulle(enrichment, doc)
                if "error" not in bulle:
                    bulle_path = BULLES_PATH / f"{uid}.json"
                    bulle_path.write_text(
                        json.dumps(bulle, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    out["bulle"] = f"bulles/{uid}.json"
                    print(f"     ✅  Bulle enregistrée : {out['bulle']}")
                else:
                    print(f"     ⚠  Bulle ratée : {bulle['error']}")

    return out


def _link_versions(catalog: dict) -> None:
    """B12 — Expose un champ `versions` par doc : liste des doc_id qui sont des
    doublons textuels/binaires du même texte (autres éditions, traductions).

    S'appuie sur synopsis/duplicates.json (registre maintenu par dedup.py).
    Migration douce : si le registre est absent, `versions` reste [].
    """
    registry_path = SYNOPSIS_PATH / "duplicates.json"
    docs = catalog.get("docs", {})
    # Init à vide partout
    for d in docs.values():
        d.setdefault("versions", [])

    if not registry_path.exists():
        return
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return

    clusters: list[list[str]] = []
    # Grappes binaires : by_hash → [doc_id, ...]
    for ids in (registry.get("by_hash") or {}).values():
        if len(ids) > 1:
            clusters.append(list(ids))

    for cluster in clusters:
        present = [cid for cid in cluster if cid in docs]
        for cid in present:
            others = sorted(set(present) - {cid})
            docs[cid]["versions"] = others


def update_synopsis_catalog(report: dict) -> None:
    """Met à jour synopsis/catalog.json (catalogue dédupliqué, multi-runs).

    Pour chaque doc scoré dans ce run :
    - Si déjà présent (clé = hash de l'URL) : ajoute une entrée dans `runs[]`
    - Sinon : crée la fiche

    Champs notables (cf. revue) :
      - score_initial : score sur titre seul (ex-latest_score)
      - score_final   : score post-lecture (synopsis_enricher), null si absent
      - collected_date: date de collecte (ex-date du dernier run)
      - doc_date/lang/editeur/doi/isbn/hal_id : métadonnées bibliographiques
      - doc_type/recit_de_lutte : typologie & tag de récit de lutte
      - versions      : doc_id des doublons/traductions
    Le catalog reste COMPLET ; le filtrage de publication est fait ailleurs.
    """
    catalog_path = SYNOPSIS_PATH / "catalog.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    else:
        catalog = {"docs": {}, "meta": {}}

    run_date = report["date"]

    for r in report["results"]:
        doc_id = file_uid(r["url"])
        run_entry = {
            "date":           run_date,
            "score":          r["score"],
            "raison":         r["raison"],
            "context_seen":   r.get("context_seen", ""),
            "link_text":      r.get("link_text", ""),
            "downloaded":     r["downloaded"],
            # C6 — reproductibilité : modèle + version du prompt de scoring
            "model":          r.get("model", ""),
            "prompt_version": r.get("prompt_version", ""),
        }

        # Score post-lecture (S1) : produit par synopsis_enricher si enrichi
        enrichment = r.get("enrichment") or {}
        score_final = None
        if isinstance(enrichment, dict) and "error" not in enrichment:
            rs = enrichment.get("relevance_score")
            if isinstance(rs, (int, float)):
                score_final = int(rs)

        # S2 — métadonnées bibliographiques (calculées dans analyse_pdf...)
        bib = r.get("bib") or {}

        # Champs d'enrichissement éventuels (cover, synopsis, bulle)
        extras = {}
        for k in ("cover", "bulle", "meta", "enrichment", "download_status",
                  "drive_url"):
            if k in r:
                extras[k] = r[k]

        if doc_id in catalog["docs"]:
            fiche = catalog["docs"][doc_id]
            fiche["runs"] = [run for run in fiche["runs"]
                             if run["date"] != run_date]
            fiche["runs"].append(run_entry)
            # S1 — score sur titre = score_initial ; on conserve latest_score
            # pour rétrocompatibilité de l'interface.
            fiche["score_initial"] = r["score"]
            fiche["latest_score"]  = r["score"]
            if score_final is not None:
                fiche["score_final"] = score_final
            elif "score_final" not in fiche:
                fiche["score_final"] = None
            fiche["latest_run"]     = run_date
            fiche["collected_date"] = run_date  # S2 — date de collecte
            # A1/C3 — typologie & récit de lutte
            fiche["doc_type"]       = r.get("doc_type", fiche.get("doc_type", "autre"))
            fiche["recit_de_lutte"] = bool(r.get("recit_de_lutte",
                                                 fiche.get("recit_de_lutte", False)))
            # S2 — métadonnées : on ne remplace que si on a une valeur nouvelle
            for k in ("doc_date", "lang", "editeur", "doi", "isbn", "hal_id"):
                v = bib.get(k)
                if v:
                    fiche[k] = v
                else:
                    fiche.setdefault(k, "")
            if r["downloaded"] and not fiche.get("downloaded"):
                fiche["downloaded"] = True
                fiche["saved_as"]   = r["saved_as"]
            fiche.update({k: v for k, v in extras.items() if v})
        else:
            catalog["docs"][doc_id] = {
                "id":             doc_id,
                "url":            r["url"],
                "filename":       r["filename"],
                "format":         r["format"],
                "source":         r["source"],
                "first_seen":     run_date,
                "latest_run":     run_date,
                "collected_date": run_date,
                "score_initial":  r["score"],
                "score_final":    score_final,
                "latest_score":   r["score"],
                "doc_type":       r.get("doc_type", "autre"),
                "recit_de_lutte": bool(r.get("recit_de_lutte", False)),
                "doc_date":       bib.get("doc_date", ""),
                "lang":           bib.get("lang", ""),
                "editeur":        bib.get("editeur", ""),
                "doi":            bib.get("doi", ""),
                "isbn":           bib.get("isbn", ""),
                "hal_id":         bib.get("hal_id", ""),
                "versions":       [],
                "downloaded":     r["downloaded"],
                "saved_as":       r.get("saved_as"),
                "runs":           [run_entry],
                **extras,
            }

    # B12 — recoupement versions/traductions
    try:
        _link_versions(catalog)
    except Exception as e:
        print(f"  ⚠  _link_versions raté : {e}")

    # S1 — réconciliation globale des scores sur TOUT le catalogue (et pas
    # seulement les docs du run courant) : rétro-remplit score_initial depuis
    # latest_score, et score_final depuis enrichment.relevance_score. Migration
    # idempotente — corrige les fiches enrichies lors de runs antérieurs.
    for fiche in catalog["docs"].values():
        if fiche.get("score_initial") is None:
            fiche["score_initial"] = fiche.get("latest_score", 0)
        if fiche.get("score_final") is None:
            enr = fiche.get("enrichment")
            if isinstance(enr, dict) and "error" not in enr:
                rs = enr.get("relevance_score")
                if isinstance(rs, (int, float)):
                    fiche["score_final"] = int(rs)
        fiche.setdefault("score_final", None)

    # Méta — migration douce : .get() partout
    def _eff(f: dict) -> int:
        sf = f.get("score_final")
        return int(sf) if sf is not None else int(f.get("score_initial",
                                                        f.get("latest_score", 0)) or 0)

    catalog["meta"] = {
        "last_updated":     run_date,
        "total_docs":       len(catalog["docs"]),
        "total_downloaded": sum(1 for f in catalog["docs"].values()
                                if f.get("downloaded")),
        "total_published":  sum(1 for f in catalog["docs"].values()
                                if _eff(f) >= 6),
        "score_distribution": {
            i: sum(1 for f in catalog["docs"].values()
                   if f.get("latest_score", 0) == i)
            for i in range(11)
        },
        "score_final_distribution": {
            i: sum(1 for f in catalog["docs"].values()
                   if f.get("score_final") == i)
            for i in range(11)
        },
    }

    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  📒 Catalog mis à jour : {catalog['meta']['total_docs']} docs dont "
          f"{catalog['meta']['total_downloaded']} téléchargés, "
          f"{catalog['meta']['total_published']} publiables")


def generate_interface(catalog_path: Path = SYNOPSIS_PATH / "catalog.json") -> None:
    """Génère interface/index.html avec catalog embarqué."""
    interface_template = Path(__file__).parent / "interface_template.html"
    if not interface_template.exists():
        print(f"  ⚠  Template introuvable : {interface_template}")
        return

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    template = interface_template.read_text(encoding="utf-8")

    # Inject le catalog comme variable JS embarquée — pas de fetch (marche en file://)
    embedded = json.dumps(catalog, ensure_ascii=False)
    final = template.replace("/*__CATALOG_INJECTED_HERE__*/null", embedded)

    out = INTERFACE_PATH / "index.html"
    out.write_text(final, encoding="utf-8")
    print(f"  🖥  Interface générée : {out} ({len(catalog['docs'])} fiches)")


SITE_PATH = Path("site")
SITE_BASE_URL = "https://biblio.actitude.org"

# Seuil de publication (S1) : un doc n'est publié (RSS, sitemap, fiche
# pré-rendue) que si son score post-lecture l'autorise. catalog.json reste
# complet pour la transparence.
PUBLISH_THRESHOLD = 6


def _effective_score(doc: dict) -> int:
    """Score effectif d'un doc : score_final si présent, sinon score_initial.

    Migration douce : les vieux catalogs sans ces champs retombent sur
    latest_score.
    """
    sf = doc.get("score_final")
    if sf is not None:
        return int(sf)
    return int(doc.get("score_initial", doc.get("latest_score", 0)) or 0)


# Formats d'ouvrage acceptés : gratuits ET ouverts uniquement.
#   pdf  — ISO 32000          epub — standard W3C
#   txt  — texte brut         odt  — OpenDocument (ISO/IEC 26300)
# Exclus : .doc/.docx (formats propriétaires Microsoft) et les pages HTML
# (articles de presse — pas des ouvrages : ceci est une bibliothèque).
OUVRAGE_EXTENSIONS = {"pdf", "epub", "txt", "odt"}


def _is_ouvrage_doc(doc: dict) -> bool:
    """Garde-fou « bibliothèque » : une fiche correspond toujours à un ouvrage
    dans un format gratuit et ouvert (PDF, EPUB, TXT, ODT), jamais à un
    article HTML (flux RSS, lien de presse).

    Accepte le candidat si son extension déclarée appartient aux formats
    ouverts OU si l'URL pointe explicitement vers un tel fichier. Les articles
    HTML restent exploités comme pistes de découverte (candidates.yml) mais ne
    deviennent jamais des fiches.
    """
    ext = (doc.get("extension") or doc.get("format") or "").lower().lstrip(".")
    if ext in OUVRAGE_EXTENSIONS:
        return True
    path = urlparse(doc.get("url", "")).path.lower()
    return any(path.endswith("." + e) for e in OUVRAGE_EXTENSIONS)


def _is_publishable(doc: dict) -> bool:
    """True si le doc doit apparaître dans RSS / sitemap / fiches pré-rendues.

    Deux conditions : score effectif suffisant ET ouvrage dans un format
    ouvert (jamais un article HTML — bibliothèque, pas revue de presse).
    """
    return _is_ouvrage_doc(doc) and _effective_score(doc) >= PUBLISH_THRESHOLD


def _prerender_fiches(catalog: dict) -> int:
    """Génère un HTML statique minimaliste par fiche dans site/fiches/<id>.html.

    Objectif : fournir aux crawlers (Twitter/Mastodon/Facebook/LinkedIn) et aux
    moteurs de recherche un HTML pré-rendu avec les bons og:* et un canonical
    statique, AVANT toute exécution JS. Le fichier redirige automatiquement
    vers fiche.html?id=<id> via meta refresh pour les utilisateurs.

    Retourne le nombre de fichiers générés.
    """
    fiches_dir = SITE_PATH / "fiches"
    fiches_dir.mkdir(parents=True, exist_ok=True)

    fallback_desc = (
        "Fiche du corpus BIBLIO — communs, terres, paysanneries."
    )

    docs = catalog.get("docs", {})
    count = 0
    skipped = 0

    for doc_id, doc in docs.items():
        # ── S1 — ne pré-rendre que les docs publiables ───────────────────────
        if not _is_publishable(doc):
            skipped += 1
            continue
        # ── Titre : link_text du dernier run, sinon filename sans extension ──
        title = ""
        if doc.get("runs"):
            title = doc["runs"][-1].get("link_text", "") or ""
        if not title:
            title = doc.get("filename", "")
            # Retire l'extension pour avoir un titre lisible
            if "." in title:
                title = title.rsplit(".", 1)[0]
        title = title.strip() or f"Fiche {doc_id}"

        # ── Description : 1re phrase du summary, sinon raison, tronqué 300 ───
        description = ""
        enrich = doc.get("enrichment") or {}
        summary = enrich.get("summary", "") if isinstance(enrich, dict) else ""
        if summary:
            # Première phrase : on coupe au premier . ! ?
            first = summary
            for sep in (". ", "! ", "? "):
                if sep in first:
                    first = first.split(sep, 1)[0] + sep.strip()
                    break
            description = first.strip()
        if not description and doc.get("runs"):
            description = doc["runs"][-1].get("raison", "") or ""
        if not description:
            description = fallback_desc
        description = description.strip()[:300]

        # ── Source + score pour le fallback HTML ─────────────────────────────
        source = doc.get("source", "") or ""
        score = doc.get("latest_score", 0)

        # ── JSON-LD ScholarlyArticle (mêmes champs que côté JS) ──────────────
        canonical_url = f"{SITE_BASE_URL}/fiches/{doc_id}.html"
        # A2 — og:image pointe vers la carte sociale générée (1200x630).
        # Fallback : couverture PDF brute, puis image OG par défaut.
        card_file = SITE_PATH / "assets" / "cards" / f"{doc_id}.png"
        cover_file = SITE_PATH / "assets" / "covers" / f"{doc_id}.png"
        if card_file.exists():
            og_image = f"{SITE_BASE_URL}/assets/cards/{doc_id}.png"
        elif cover_file.exists():
            og_image = f"{SITE_BASE_URL}/assets/covers/{doc_id}.png"
        else:
            og_image = f"{SITE_BASE_URL}/assets/og-default.png"
        page_count = 0
        if isinstance(doc.get("meta"), dict):
            page_count = doc["meta"].get("page_count", 0) or 0
        is_book = page_count >= 60
        # La langue est un champ de premier niveau du doc (renseigné par
        # doc_metadata.py), jamais une sous-clé de `meta` — lire `meta`
        # renvoyait toujours "" et figeait inLanguage à "fr" pour tout le
        # corpus, y compris les ouvrages anglophones et hispanophones.
        lang = (doc.get("lang") or "fr")

        ld = {
            "@context": "https://schema.org",
            "@type": "Book" if is_book else "ScholarlyArticle",
            "headline": title,
            "name": title,
            "url": canonical_url,
            "inLanguage": lang,
            "abstract": description,
            "image": og_image,
            "isPartOf": {
                "@type": "WebSite",
                "name": "BIBLIO — Bibliothèque documentaire ouverte",
                "url": "https://biblio.actitude.org/",
            },
            "publisher": {
                "@type": "Organization",
                "name": "actitude.org",
                "url": "https://actitude.org",
            },
        }
        if source:
            ld["sourceOrganization"] = {
                "@type": "Organization",
                "name": source,
            }
        if doc.get("url"):
            ld["mainEntityOfPage"] = doc["url"]
        ld_json = json.dumps(ld, ensure_ascii=False)

        # ── Échappement HTML minimal pour insérer dans des attributs/texte ──
        def esc(s: str) -> str:
            return (str(s or "")
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;"))

        title_h    = esc(title)
        desc_h     = esc(description)
        source_h   = esc(source)
        doc_id_h   = esc(doc_id)

        # ── HTML statique — minimal, ciblé crawlers + SEO ────────────────────
        html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{title_h} — BIBLIO</title>
<link rel="canonical" href="{canonical_url}">
<meta name="description" content="{desc_h}">
<meta property="og:title" content="{title_h}">
<meta property="og:description" content="{desc_h}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{canonical_url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="BIBLIO — biblio.actitude.org">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld_json}</script>
<meta http-equiv="refresh" content="0; url=fiche.html?id={doc_id_h}">
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<main style="max-width: 60ch; margin: 4rem auto; padding: 0 1.5rem; font-family: 'EB Garamond', serif;">
  <h1>{title_h}</h1>
  <p><em>{source_h}</em> · Score : {score}/10</p>
  <p>{desc_h}</p>
  <p><a href="fiche.html?id={doc_id_h}">Voir la fiche détaillée →</a></p>
</main>
</body>
</html>
"""
        (fiches_dir / f"{doc_id}.html").write_text(html, encoding="utf-8")
        count += 1

    if skipped:
        print(f"  ℹ  Pré-rendu : {skipped} fiche(s) non publiée(s) "
              f"(score effectif < {PUBLISH_THRESHOLD})")
    return count


def _prune_site_orphans(catalog: dict) -> dict:
    """Garde-fou — retire de site/ les fichiers par-document orphelins.

    Un document repassé sous le seuil de publication (re-scoring, réconciliation
    des scores) laissait derrière lui sa fiche pré-rendue, sa bulle, sa
    couverture et ses cartes sociales : la génération n'ajoutait que, ne
    purgeait jamais. Résultat : des fichiers crawlables désynchronisés du
    catalogue. On reconstruit l'ensemble publiable et on supprime tout fichier
    `<id>.*` (ou `<id>-cite-N.png`) dont le document n'en fait plus partie.

    Les gabarits statiques (fiche.html, index.html) et les fichiers dont le
    préfixe n'est pas un identifiant de document connu ne sont jamais touchés.

    Retourne le nombre de fichiers retirés par dossier.
    """
    docs = catalog.get("docs", {})
    keep = {doc_id for doc_id, doc in docs.items() if _is_publishable(doc)}

    def _doc_id_of(stem: str):
        head = stem[:8]
        if (len(head) == 8
                and all(c in "0123456789abcdef" for c in head)
                and head in docs):
            return head
        return None

    targets = [
        (SITE_PATH / "fiches",            "*.html"),
        (SITE_PATH / "data" / "bulles",   "*.json"),
        (SITE_PATH / "assets" / "covers", "*.png"),
        (SITE_PATH / "assets" / "cards",  "*.png"),
    ]
    removed: dict = {}
    for directory, pattern in targets:
        if not directory.is_dir():
            continue
        n = 0
        for f in directory.glob(pattern):
            doc_id = _doc_id_of(f.stem)
            if doc_id is None:        # gabarit ou fichier hors-corpus → garder
                continue
            if doc_id not in keep:    # document non publiable → orphelin
                f.unlink()
                n += 1
        if n:
            removed[directory.name] = n
    return removed


def publish_site(run_date: str) -> None:
    """Prépare le dossier site/ pour publication :
    - copie le catalog vers site/data/catalog.json
    - copie les bulles vers site/data/bulles/
    - copie les couvertures vers site/assets/covers/
    - régénère feed.xml et sitemap.xml dynamiquement
    """
    import shutil

    if not SITE_PATH.exists():
        print("  ⚠  site/ inexistant — skip publish")
        return

    # 1. Catalog
    catalog_src = SYNOPSIS_PATH / "catalog.json"
    if catalog_src.exists():
        (SITE_PATH / "data").mkdir(parents=True, exist_ok=True)
        shutil.copy2(catalog_src, SITE_PATH / "data" / "catalog.json")

    # 1bis. Index full-text + JSON éditoriaux (recherche, dossiers, stats…)
    for name in ("fulltext_index.json", "dossiers.json", "featured.json",
                 "corpus_stats.json"):
        src = SYNOPSIS_PATH / name
        if src.exists():
            shutil.copy2(src, SITE_PATH / "data" / name)

    # 2. Bulles
    site_bulles = SITE_PATH / "data" / "bulles"
    site_bulles.mkdir(parents=True, exist_ok=True)
    bulle_count = 0
    for b in BULLES_PATH.glob("*.json"):
        shutil.copy2(b, site_bulles / b.name)
        bulle_count += 1

    # 3. Couvertures
    site_covers = SITE_PATH / "assets" / "covers"
    site_covers.mkdir(parents=True, exist_ok=True)
    cover_count = 0
    for c in COVERS_PATH.glob("*.png"):
        shutil.copy2(c, site_covers / c.name)
        cover_count += 1

    # 3bis. A2 — Cartes sociales Open Graph + citation-cards + og-default.png
    # (généré AVANT le pré-rendu pour que og:image pointe vers la carte)
    if social_cards is not None:
        try:
            cs = social_cards.generate_all(catalog_src,
                                           min_score=PUBLISH_THRESHOLD)
            if "error" not in cs:
                print(f"  🖼  Cartes sociales : {cs.get('cards', 0)} cartes, "
                      f"{cs.get('citation_cards', 0)} citation-cards")
        except Exception as e:
            print(f"  ⚠  social_cards raté : {e}")
    else:
        print("  ℹ  Pillow indisponible — cartes sociales non générées")

    # 4. Génération RSS + sitemap
    catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
    _write_rss(catalog, run_date)
    _write_sitemap(catalog)

    # 4bis. Pré-rendu HTML statique par fiche (og:* + canonical + JSON-LD)
    # → pour les crawlers sociaux (Twitter/Mastodon/FB/LI) et le SEO
    try:
        n_prerender = _prerender_fiches(catalog)
        print(f"  🔗 Pré-rendu : {n_prerender} fiches statiques")
    except Exception as e:
        print(f"  ⚠  pré-rendu fiches raté : {e}")

    # 4ter. Garde-fou — purge des fichiers par-document devenus orphelins
    # (fiche / bulle / couverture / carte d'un doc repassé sous le seuil).
    try:
        pruned = _prune_site_orphans(catalog)
        if pruned:
            detail = ", ".join(f"{v} {k}" for k, v in pruned.items())
            print(f"  🧹 Orphelins purgés : {detail}")
    except Exception as e:
        print(f"  ⚠  purge des orphelins ratée : {e}")

    # 5. Copie récursive des exports (BibTeX, RIS, CSL JSON…) vers site/exports/
    exports_src = Path("exports")
    export_count = 0
    if exports_src.exists() and exports_src.is_dir():
        site_exports = SITE_PATH / "exports"
        site_exports.mkdir(parents=True, exist_ok=True)
        for entry in exports_src.rglob("*"):
            if entry.is_file():
                rel = entry.relative_to(exports_src)
                target = site_exports / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry, target)
                export_count += 1
        print(f"  📦 Exports copiés : {export_count} fichier(s) → site/exports/")
    else:
        print("  ℹ  Aucun dossier exports/ à copier")

    print(f"  🌐 Site publié : {cover_count} couvertures, {bulle_count} bulles, "
          f"{export_count} exports, "
          f"{len(catalog.get('docs', {}))} fiches au catalog")


def _rfc822(run_date: str) -> str:
    """Convertit une date de run 'YYYY-MM-DD_HH-MM' en date RFC822 (RSS).

    Ex: 'Thu, 22 May 2026 14:30:00 +0000'. Fallback : maintenant UTC.
    """
    from email.utils import format_datetime
    try:
        dt = datetime.strptime(run_date, "%Y-%m-%d_%H-%M")
        dt = dt.replace(tzinfo=__import__("datetime").timezone.utc)
        return format_datetime(dt)
    except Exception:
        from datetime import timezone
        return format_datetime(datetime.now(timezone.utc))


def _rss_item(d: dict) -> str:
    """Construit un <item> RSS 2.0 pour un doc du catalog."""
    title = d.get("filename", d.get("id", ""))
    if d.get("runs"):
        link_text = d["runs"][-1].get("link_text", "")
        if link_text:
            title = link_text
    url_fiche = f"{SITE_BASE_URL}/fiches/{d['id']}.html"
    enrich = d.get("enrichment") or {}
    description = ""
    if isinstance(enrich, dict):
        description = enrich.get("summary", "") or ""
    if not description and d.get("runs"):
        description = d["runs"][-1].get("raison", "") or ""
    pub = _rfc822(d.get("latest_run", "") or d.get("collected_date", ""))
    return f"""    <item>
      <title>{_xml_escape(title)}</title>
      <link>{url_fiche}</link>
      <guid isPermaLink="true">{url_fiche}</guid>
      <pubDate>{pub}</pubDate>
      <description>{_xml_escape(description[:600])}</description>
      <category>{_xml_escape(d.get('source', ''))}</category>
    </item>"""


def _rss_document(items: list[str], run_date: str, title: str,
                  description: str, feed_path: str) -> str:
    """Assemble un flux RSS 2.0 valide (namespace Atom déclaré sur <rss>)."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{_xml_escape(title)}</title>
    <link>{SITE_BASE_URL}/</link>
    <description>{_xml_escape(description)}</description>
    <language>fr</language>
    <lastBuildDate>{_rfc822(run_date)}</lastBuildDate>
    <atom:link href="{SITE_BASE_URL}/{feed_path}" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


def _write_rss(catalog: dict, run_date: str) -> None:
    """B5 — RSS 2.0 conforme : date RFC822, namespace Atom déclaré sur <rss>.

    Génère :
      - feed.xml          : 30 dernières fiches publiables (score eff. >= 6)
      - feeds/scoops.xml  : feed « scoops » (score_final >= 9)
      - feeds/<concept>.xml : un feed par concept (matched_keywords / dossier)
    """
    docs = sorted(
        catalog.get("docs", {}).values(),
        key=lambda d: (d.get("latest_run", ""), _effective_score(d)),
        reverse=True,
    )
    publishable = [d for d in docs if _is_publishable(d)]

    # ── Feed principal ───────────────────────────────────────────────────────
    main_items = [_rss_item(d) for d in publishable[:30]]
    (SITE_PATH / "feed.xml").write_text(
        _rss_document(main_items, run_date,
                      "BIBLIO — bibliothèque documentaire ouverte",
                      "Veille documentaire : communs, terres, paysanneries",
                      "feed.xml"),
        encoding="utf-8")

    feeds_dir = SITE_PATH / "feeds"
    feeds_dir.mkdir(parents=True, exist_ok=True)

    # ── Feed « scoops » : score_final >= 9 ───────────────────────────────────
    scoops = [d for d in docs if (d.get("score_final") or 0) >= 9][:30]
    (feeds_dir / "scoops.xml").write_text(
        _rss_document([_rss_item(d) for d in scoops], run_date,
                      "BIBLIO — Scoops (score 9+)",
                      "Les documents les mieux notés après lecture",
                      "feeds/scoops.xml"),
        encoding="utf-8")

    # ── Feeds dérivés par concept (mots-clés des core_concepts) ──────────────
    concept_slugs = {
        "communs": ["communs", "communaux", "commons"],
        "propriete-usage": ["propriété d'usage", "fonds de dotation",
                            "fiducie", "usufruct"],
        "paysannerie": ["paysan", "agroécologie", "campesin", "peasant"],
        "sans-terre": ["sans-terre", "réforme agraire", "land", "mst"],
        "habitat": ["habitat", "logement", "coopérative d'habitants",
                    "housing"],
    }
    feed_index = []
    for slug, kws in concept_slugs.items():
        kws_l = [k.lower() for k in kws]
        matched = []
        for d in publishable:
            hay = " ".join([
                d.get("filename", ""),
                (d.get("runs", [{}])[-1].get("link_text", "")
                 if d.get("runs") else ""),
                " ".join((d.get("enrichment") or {}).get("matched_keywords", [])
                         if isinstance(d.get("enrichment"), dict) else []),
            ]).lower()
            if any(k in hay for k in kws_l):
                matched.append(d)
        if matched:
            (feeds_dir / f"{slug}.xml").write_text(
                _rss_document([_rss_item(d) for d in matched[:30]], run_date,
                              f"BIBLIO — {slug}",
                              f"Veille BIBLIO : concept « {slug} »",
                              f"feeds/{slug}.xml"),
                encoding="utf-8")
            feed_index.append(slug)
    print(f"  📡 RSS : feed principal ({len(main_items)}), scoops "
          f"({len(scoops)}), {len(feed_index)} feed(s) par concept")


def _write_sitemap(catalog: dict) -> None:
    """Sitemap XML avec les pages principales + une fiche par doc."""
    urls = [
        f"{SITE_BASE_URL}/",
        f"{SITE_BASE_URL}/fiches/",
        f"{SITE_BASE_URL}/apropos.html",
        f"{SITE_BASE_URL}/auteurs.html",
        f"{SITE_BASE_URL}/chronologie.html",
        f"{SITE_BASE_URL}/graph.html",
        f"{SITE_BASE_URL}/dossiers.html",
    ]
    # S1 — seules les fiches publiables (score effectif >= seuil) sont indexées
    for d in catalog.get("docs", {}).values():
        if _is_publishable(d):
            urls.append(f"{SITE_BASE_URL}/fiches/{d['id']}.html")
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    (SITE_PATH / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def _xml_escape(s: str) -> str:
    return (str(s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def save_markdown_report(report: dict, path: Path) -> None:
    """Écrit un rapport Markdown lisible, avec stats par source."""
    lines = [
        f"# Rapport de veille — {report['date']}",
        "",
        "## Synthèse",
        "",
        f"- Sources scannées  : **{report['sources_scanned']}**",
        f"- Documents trouvés : **{report['documents_found']}**",
        f"- Scorés par Claude : **{report['documents_scored']}**",
        f"- Téléchargés       : **{report['documents_downloaded']}**",
        "",
    ]

    # Stats par source
    by_source: dict[str, dict] = defaultdict(
        lambda: {"found": 0, "downloaded": 0, "scores": []}
    )
    for r in report["results"]:
        s = by_source[r["source"]]
        s["found"] += 1
        if r["downloaded"]:
            s["downloaded"] += 1
        s["scores"].append(r["score"])

    if by_source:
        lines += [
            "## Performance par source",
            "",
            "| Source | Trouvés | Téléchargés | Score moyen | Score max |",
            "|--------|---------|-------------|-------------|-----------|",
        ]
        for label, s in sorted(by_source.items(), key=lambda kv: -kv[1]["downloaded"]):
            mean = round(sum(s["scores"]) / len(s["scores"]), 1) if s["scores"] else 0
            mx   = max(s["scores"]) if s["scores"] else 0
            lines.append(
                f"| {label} | {s['found']} | {s['downloaded']} | {mean}/10 | {mx}/10 |"
            )
        lines.append("")

    # Documents téléchargés
    downloaded = [r for r in report["results"] if r["downloaded"]]
    lines += ["## Documents téléchargés", ""]
    if downloaded:
        # Trier par score décroissant
        for r in sorted(downloaded, key=lambda x: -x["score"]):
            lines += [
                f"### {r['filename']} ({r['score']}/10)",
                f"- Source : [{r['source']}]({r['url']})",
                f"- Format : {r['format'].upper()}",
                f"- Raison : {r['raison']}",
                f"- Fichier: `{r['saved_as']}`",
                "",
            ]
    else:
        lines.append("_Aucun document téléchargé lors de cette veille._\n")

    # Top 10 ignorés (juste pour comprendre les raisons)
    ignored = [r for r in report["results"] if not r["downloaded"]]
    if ignored:
        lines += [
            "## Documents ignorés (top 10 — score le plus haut, mais sous seuil)",
            "",
        ]
        for r in sorted(ignored, key=lambda x: -x["score"])[:10]:
            lines.append(
                f"- **{r['filename']}** ({r['score']}/10) — {r['raison']}"
            )

    path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config    = load_config()
    keywords  = config.get("keywords", [])
    sources   = config.get("sources", [])
    threshold = int(os.getenv("SCORE_THRESHOLD", str(config.get("threshold", 6))))
    dry_run   = os.getenv("DRY_RUN", "false").lower() == "true"

    if dry_run:
        print("🔎  Mode simulation — aucun fichier ne sera téléchargé.\n")

    run_date = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    report   = {
        "date":                 run_date,
        "sources_scanned":      0,
        "documents_found":      0,
        "documents_scored":     0,
        "documents_downloaded": 0,
        "results":              [],
    }

    for source in sources:
        url       = source.get("url", "")
        label     = source.get("label", url)
        src_type  = source.get("type", "html")

        # ── Throttle : décider si on fetch cette source maintenant ───────────
        try:
            ok_fetch, skip_reason = throttle.should_fetch(source)
            if not ok_fetch:
                print(f"\n⏭   {label}  [skip: {skip_reason}]")
                continue
        except Exception as e:
            print(f"  ⚠  throttle.should_fetch raté pour {label} : {e}")

        print(f"\n🔍  {label}  [type={src_type}]\n    {url}")

        # ── Dispatch vers le bon parser ────────────────────────────────────
        docs_raw = parser_dispatch(source)

        # ── Garde-fou « bibliothèque » ─────────────────────────────────────
        # Une fiche pointe TOUJOURS vers un ouvrage dans un format gratuit et
        # ouvert (PDF, EPUB, TXT, ODT), jamais vers un article HTML ni un
        # format propriétaire. Les liens écartés (flux RSS, presse, .doc…) ne
        # deviennent pas des fiches mais restent collectés comme pistes de
        # découverte (candidates.yml, alimenté par les parsers eux-mêmes).
        docs = [d for d in docs_raw if _is_ouvrage_doc(d)]
        n_dropped = len(docs_raw) - len(docs)
        if n_dropped:
            print(f"    ⊘  {n_dropped} lien(s) écarté(s) — non-ouvrage ou "
                  f"format non ouvert (bibliothèque = PDF/EPUB/TXT/ODT)")

        # Enregistrer le résultat dans le throttle. On compte le rendement brut
        # (docs_raw) pour ne pas étrangler les flux RSS qui servent la
        # découverte même s'ils ne produisent aucune fiche.
        try:
            throttle.record_fetch(
                source,
                success=bool(docs_raw),
                doc_count=len(docs_raw),
                status_code=200 if docs_raw else 204,
            )
        except Exception as e:
            print(f"  ⚠  throttle.record_fetch raté : {e}")

        # ── Capture des liens externes : alimente discovery/candidates.yml ─
        # On re-fetche la vraie page d'index pour parser TOUS ses <a href>
        # (pas seulement les docs déjà extraits). Coût : 1 GET de plus par
        # source HTML, négligeable. Skip pour les types non-HTML (api, opds…).
        # Exécuté AVANT le filtre de fiches : la découverte continue même
        # quand une source ne produit aucun ouvrage PDF.
        if src_type in ("html", "deep_html", "rss"):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    new_links = discovery_external_links.capture_links(
                        resp.text, url, label,
                        Path("discovery") / "candidates.yml",
                    )
                    if new_links:
                        print(f"    🌐  {new_links} nouveaux candidats (liens externes)")
            except Exception as e:
                print(f"  ⚠  capture_links raté : {e}")

        if not docs:
            continue

        report["sources_scanned"] += 1
        print(f"    → {len(docs)} ouvrage(s) PDF trouvé(s)")
        report["documents_found"] += len(docs)

        # ── Scoring par batches ─────────────────────────────────────────────
        # score_batch numérote les documents 1..N À L'INTÉRIEUR de son batch.
        # On rebase donc chaque indice « doc » sur la position GLOBALE dans la
        # liste `docs` (offset = début du batch) — sans quoi les batches ≥ 2
        # écraseraient les scores des tout premiers documents.
        all_scores: list[dict] = []
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i : i + BATCH_SIZE]
            print(f"    → Scoring batch {i // BATCH_SIZE + 1} ({len(batch)} docs)…")
            batch_scores = score_batch(batch, keywords)
            for it in batch_scores:
                d = it.get("doc")
                if isinstance(d, int):
                    it["doc"] = d + i          # indice local au batch → global
            all_scores.extend(batch_scores)

        report["documents_scored"] += len(all_scores)

        for item in all_scores:
            idx = item.get("doc", 0) - 1
            if idx < 0 or idx >= len(docs):
                continue
            doc    = docs[idx]
            score  = item.get("score", 0)
            raison = item.get("raison", "")

            result = {
                "url":          doc["url"],
                "filename":     doc["filename"],
                "format":       doc["extension"],
                "source":       label,
                "score":        score,
                "raison":       raison,
                "downloaded":   False,
                "saved_as":     None,
                # Citations littérales — ce que Claude a effectivement vu :
                "link_text":    doc.get("link_text", ""),
                "context_seen": doc.get("context", "")[:400],
            }

            if score >= threshold and not dry_run:
                uid  = file_uid(doc["url"])
                dest = DOCS_PATH / f"{uid}_{doc['filename']}"
                if dest.exists() and pdf_processor.validate_pdf(dest):
                    print(f"    ✓  Déjà présent   : {doc['filename']} ({score}/10)")
                    result["downloaded"]      = True
                    result["saved_as"]        = str(dest)
                    result["download_status"] = "already_present"
                else:
                    print(f"    ↓  Téléchargement : {doc['filename']} ({score}/10)")
                    success, status = download_and_validate(doc["url"], dest)
                    result["download_status"] = status
                    if success:
                        result["downloaded"] = True
                        result["saved_as"]   = str(dest)
                        report["documents_downloaded"] += 1
                        if status != "ok":
                            print(f"    ✓  Récupéré via {status}")
                    else:
                        print(f"    ❌  {doc['filename']} — {status}")

                # Enrichissement post-download : couverture + synopsis + bulle
                if result["downloaded"]:
                    enrichment = analyse_pdf_and_enrich(dest, doc, score, keywords)
                    result.update(enrichment)
            elif score >= threshold and dry_run:
                print(f"    [sim] Aurait téléchargé : {doc['filename']} ({score}/10)")
            else:
                print(f"    ✗  Ignoré          : {doc['filename']} ({score}/10 — {raison})")

            report["results"].append(result)

    json_path = REPORTS_PATH / f"run_{run_date}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    save_markdown_report(report, json_path)
    update_synopsis_catalog(report)
    generate_interface()

    # Index full-text reconstruit à chaque run pour la recherche côté client
    try:
        idx_path = SYNOPSIS_PATH / "fulltext_index.json"
        idx = fulltext_index.build_index(
            SYNOPSIS_PATH / "catalog.json", idx_path
        )
        print(f"  🔍  Index full-text : {idx.get('total_terms', '?')} termes "
              f"sur {idx.get('total_docs', '?')} docs")
    except Exception as e:
        print(f"  ⚠  build_index raté : {e}")

    # Rapport de déduplication global
    try:
        dedup_stats = dedup.report(
            registry_path=SYNOPSIS_PATH / "duplicates.json"
        )
        if dedup_stats.get("duplicate_clusters", 0) > 0:
            print(f"  ♻  Dedup : {dedup_stats}")
    except Exception:
        pass

    # ── Discoveries "cheap" (sans appel LLM) lancées à chaque run ────────────
    print("\n🔭  Découvertes post-veille (cheap, sans LLM)")

    discovery_path = Path("discovery") / "candidates.yml"
    discovery_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Footnotes : extrait les notes de bas de page des PDFs téléchargés
        # → nouveaux candidats (URLs/DOIs cités dans les notes)
        r = discovery_footnotes.discover_from_footnotes(
            DOCS_PATH, SYNOPSIS_PATH / "catalog.json", discovery_path
        )
        print(f"  • footnotes : {r.get('added', 0)} ajoutés")
    except Exception as e:
        print(f"  ⚠  discovery_footnotes : {e}")

    try:
        # Biblio récursive : exploite les references[] des docs scorés ≥ 7
        # → trouve les DOI/URLs cités, interroge Crossref
        r = discovery_bibliography.discover_from_bibliography(
            SYNOPSIS_PATH / "catalog.json", discovery_path,
            limit_per_doc=5, limit_total=50,
        )
        print(f"  • bibliographies : {r.get('added', 0)} ajoutés")
    except Exception as e:
        print(f"  ⚠  discovery_bibliography : {e}")

    try:
        # Pipeline DOI → Unpaywall : promeut les candidats OpenAlex qui ont
        # un DOI en URL PDF directement téléchargeable (open access)
        r = discovery_promote.promote_candidates(
            discovery_path, limit=100, update_in_place=True
        )
        print(f"  • doi promotions : {r.get('promoted', 0)} sur {r.get('processed', 0)} traités")
    except Exception as e:
        print(f"  ⚠  discovery_promote : {e}")

    # Rapport throttle final
    try:
        t = throttle.report()
        print(f"  🚦  Throttle : {t}")
    except Exception:
        pass

    # ── S3 — Vérification de pérennité des liens + archivage Wayback ─────────
    # Limité par run pour ne pas marteler archive.org ; les liens vérifiés
    # récemment sont automatiquement sautés (cf. link_check.RECHECK_AFTER_DAYS).
    if not dry_run:
        try:
            ls = link_check.check_catalog(
                SYNOPSIS_PATH / "catalog.json", limit=40, do_archive=True
            )
            print(f"  🔗  Liens : {ls}")
        except Exception as e:
            print(f"  ⚠  link_check raté : {e}")

    # ── A8 — État du corpus (répartitions, biais) ────────────────────────────
    try:
        corpus_stats.build_stats(SYNOPSIS_PATH / "catalog.json")
    except Exception as e:
        print(f"  ⚠  corpus_stats raté : {e}")

    # ── A7 / A3 — Dossiers éditoriaux + document de la semaine ───────────────
    try:
        editorial.build_dossiers(SYNOPSIS_PATH / "catalog.json")
        editorial.build_featured(SYNOPSIS_PATH / "catalog.json")
    except Exception as e:
        print(f"  ⚠  editorial raté : {e}")

    # ── B8 — Exports bibliographiques (BibTeX/RIS/CSL avec DOI/ISBN/HAL) ─────
    try:
        exp_dir = Path("exports")
        cat = SYNOPSIS_PATH / "catalog.json"
        export_bibtex.export_bibtex(cat, exp_dir / "catalog.bib")
        export_bibtex.export_ris(cat, exp_dir / "catalog.ris")
        export_bibtex.export_csl_json(cat, exp_dir / "catalog.csl.json")
        print("  📑  Exports BibTeX/RIS/CSL régénérés")
    except Exception as e:
        print(f"  ⚠  export_bibtex raté : {e}")

    publish_site(run_date)

    # Garde-fou — contrôle de cohérence du site publié (orphelins, sitemap,
    # langue JSON-LD, licence). Non bloquant : un défaut est signalé, pas fatal.
    try:
        import audit_site
        if audit_site.main() != 0:
            print("  ⚠  audit_site : incohérence détectée — voir ci-dessus")
    except Exception as e:
        print(f"  ⚠  audit_site raté : {e}")

    print(f"""
╔══════════════════════════════════════════╗
  Veille terminée — {run_date}
  Sources scannées    : {report['sources_scanned']}
  Documents trouvés   : {report['documents_found']}
  Scorés par Claude   : {report['documents_scored']}
  Téléchargés         : {report['documents_downloaded']}
  Rapport             : {json_path}
╚══════════════════════════════════════════╝""")


if __name__ == "__main__":
    main()
