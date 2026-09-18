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
import time
from collections import Counter
import yaml
import hashlib
import subprocess
import claude_guard
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse, quote, urlunparse

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
import translate_citations
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

# ── Budget de run (incident 2026-08-30 → 2026-09-15) ────────────────────────
# Pendant 17 jours, chaque run CI a été tué au timeout de 3 h AVANT l'étape de
# commit : tout le travail (téléchargements, synopsis) était perdu, le
# throttle n'était jamais persisté, donc toutes les sources redevenaient
# « dues » le lendemain → boucle infinie de runs à 3 h sans rien produire.
# Deux garde-fous :
#   1. WATCH_BUDGET_MIN : temps max de la boucle de collecte. Au-delà, on
#      s'arrête proprement (source en cours NON enregistrée dans le throttle,
#      reprise au run suivant) et on passe au catalogue/site/commit.
#   2. Les docs déjà connus et déjà traités sont écartés AVANT scoring et
#      téléchargement (sur CI, docs/ est vide : sans ce filtre, chaque PDF
#      déjà catalogué était re-téléchargé à chaque passage).
WATCH_BUDGET_MIN    = float(os.getenv("WATCH_BUDGET_MIN", "75"))
MAX_ENRICH_ATTEMPTS = int(os.getenv("MAX_ENRICH_ATTEMPTS", "4"))
# auto_download (score 8 sans LLM) n'est honoré que si l'historique post-
# lecture de la source le justifie : au moins AUTO_DL_MIN_READ docs lus, dont
# une part ≥ AUTO_DL_MIN_RATIO au seuil de publication. Sinon la source
# repasse par le scoring sur titre (cas CRAS : 7 faux positifs sur 14 lus).
AUTO_DL_MIN_READ  = 10
AUTO_DL_MIN_RATIO = 0.7
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def file_uid(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def safe_url(url: str) -> str:
    """Encode les espaces et accents dans le path d'une URL sans ré-encoder
    les caractères déjà encodés ou les délimiteurs structuraux.
    Appelé au premier stockage d'une URL dans le catalog."""
    if not url:
        return url
    try:
        p = urlparse(url)
        encoded_path = quote(p.path, safe='/:@!$&\'()*+,;=-.')
        return urlunparse(p._replace(path=encoded_path))
    except Exception:
        return url


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
        # T3 — normaliser le link_text avant de l'envoyer au scorer.
        # Sans ça, le scorer cite littéralement "(page par page) (PDF)" ou
        # "jeanne_squatteuse_enracinee-20p-A5-livret.pdf" dans sa raison,
        # et ces descripteurs de format se retrouvent dans le rendu visiteur.
        raw_link = d.get("link_text") or d.get("filename") or ""
        clean_link = doc_metadata.normalize_title(
            link_text=raw_link,
            filename=d.get("filename") or "",
        ) or raw_link
        docs_block += (
            f"\nDocument {i} :\n"
            f"  Source  : {d.get('source', '')}\n"
            f"  Titre   : {clean_link}\n"
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

4b. **Confiance par source** — si la Source est reconnue comme thématiquement fiable
    (exemples : Troisièmes Voix, HAL, International Land Coalition, Infokiosques Paysannerie,
    CLACSO, CRAS), accorde un bonus de +1 et descends le seuil d'incertitude.
    Si la Source est généraliste (The Anarchist Library, Archive.org, Böll Stiftung),
    reste strict sur les règles 1-4.

5. **Cite littéralement** dans ta raison le mot/phrase du titre, de la source ou du contexte
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
        claude_guard.guard_before_call()
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
            claude_guard.check_result(result.stdout, result.stderr)
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
        # Audit 17/09 (MD-14) : 15 fichiers de docs/ étaient des pages anti-bot
        # (HAL/Anubis, archive.org) écrites par-dessus le vrai PDF. On écrit
        # d'abord à côté, on vérifie la signature, et on ne remplace un fichier
        # existant que par un PDF valide.
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        head = tmp.open("rb").read(5)
        if dest.suffix.lower() == ".pdf" and not head.startswith(b"%PDF"):
            print(f"  ⛔  Contenu non-PDF refusé pour {url} "
                  f"(signature {head!r}) — fichier existant préservé")
            tmp.unlink(missing_ok=True)
            return False
        os.replace(tmp, dest)
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
                            keywords: list[str],
                            source_default_lang: str = "",
                            uid: str | None = None) -> dict:
    """Pour un PDF validé : extrait couverture, texte, et appelle Claude pour
    le synopsis enrichi. Si score ≥ 9, génère aussi la bulle de publication.

    `source_default_lang` : langue par défaut de la source (sources.yml),
    transmise à build_metadata comme filet de sécurité.

    Retourne un dict avec : cover_path, summary, citations,
    matched_keywords, relevance_score, bulle, references (si applicable).
    """
    out = {}
    # uid explicite possible : la clé catalogue ne vaut pas toujours
    # file_uid(url) (297 fiches sur 1904 au 2026-09-15, URL réécrite après coup).
    uid = uid or file_uid(doc["url"])

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

    # Couverture page 1 → JPEG
    cover_path = COVERS_PATH / f"{uid}.jpg"
    if pdf_processor.extract_cover(dest, cover_path, max_width=1200):
        out["cover"] = f"covers/{uid}.jpg"   # chemin relatif depuis interface/
        print(f"     🖼  Couverture extraite : {out['cover']}")

    # ── Archivage Wayback « à la capture » ───────────────────────────────────
    # Le document vient d'être téléchargé : sa source est encore vivante. C'est
    # le seul moment fiable pour en obtenir une copie pérenne — une fois la
    # source morte, la Wayback Machine ne peut plus la photographier. Le
    # link_check de fin de run reste un filet, mais arrive souvent trop tard.
    # Best-effort strict : un échec ou un timeout n'interrompt jamais le run.
    try:
        archive = link_check.submit_to_wayback(doc["url"])
        if archive:
            out["archive_url"] = archive
            print(f"     🏛  Copie Wayback : {archive}")
    except Exception as e:
        print(f"     ⚠  archivage Wayback raté : {e}")

    # Extraction des références bibliographiques (boucle de découverte)
    try:
        refs = bibliography_extractor.extract_references(dest, max_refs=30)
        if refs:
            out["references"] = refs
            print(f"     📚  {len(refs)} référence(s) bibliographique(s) extraite(s)")
    except Exception as e:
        print(f"     ⚠  extraction refs ratée : {e}")

    # Synopsis enrichi via Claude (sur le texte du PDF)
    # T2 — on passe le titre pour que _denoise_page() retire les lignes
    # qui le répètent (boilerplate Anarchist Library, Archive.org…).
    # skip_cover=True : ignore la page 1 si c'est une page de couverture
    # sans contenu réel (titre seul, auteur, date).
    _doc_title_hint = doc.get("title") or doc.get("link_text") or doc.get("filename") or ""
    text = pdf_processor.extract_text(dest, max_chars=10000,
                                      doc_title=_doc_title_hint)

    # ── S2 — Métadonnées bibliographiques fiables ────────────────────────────
    # doc_date / lang / editeur / doi / isbn / hal_id, sans jamais inférer
    # un auteur absent de la source (anonymat respecté).
    try:
        bib = doc_metadata.build_metadata(
            doc, pdf_meta=meta, pdf_text=text,
            source_default_lang=source_default_lang,
        )
        out["bib"] = bib
    except Exception as e:
        print(f"     ⚠  build_metadata raté : {e}")
        out["bib"] = {}

    # ── Skip enrichissement si score_final déjà présent ─────────────────────
    # Évite d'écraser un score_final existant valide lors d'un re-run CI.
    # Forcer le ré-enrichissement : FORCE_REENRICH=true en variable d'env.
    _force_reenrich = os.getenv("FORCE_REENRICH", "false").lower() == "true"
    _existing_score_final = None
    if not _force_reenrich:
        try:
            _catalog_path = SYNOPSIS_PATH / "catalog.json"
            if _catalog_path.exists():
                _cat = json.loads(_catalog_path.read_text(encoding="utf-8"))
                _fiche = _cat.get("docs", {}).get(uid, {})
                _sf = _fiche.get("score_final")
                if _sf is not None and _sf != "" and _sf != 0:
                    _existing_score_final = _sf
        except Exception as _e:
            print(f"     ⚠  lecture catalog pour skip-check raté : {_e}")

    if _existing_score_final is not None and not _force_reenrich:
        print(f"     ⏭  skip enrichissement — score_final déjà présent ({_existing_score_final})")
        # Réinjecter l'enrichissement existant depuis le catalog pour que
        # update_synopsis_catalog ne reparte pas de zéro.
        try:
            _catalog_path = SYNOPSIS_PATH / "catalog.json"
            _cat = json.loads(_catalog_path.read_text(encoding="utf-8"))
            _fiche = _cat.get("docs", {}).get(uid, {})
            if isinstance(_fiche.get("enrichment"), dict):
                out["enrichment"] = _fiche["enrichment"]
        except Exception:
            pass
        return out

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

    # Charge les UIDs de l'archive pour éviter la réinjection de docs archivés.
    # Un doc archivé est considéré "déjà connu" et ne doit pas réintégrer le
    # catalogue principal lors d'un re-scrape de sa source d'origine.
    archive_path = SYNOPSIS_PATH / "catalog_archive.json"
    archived_uids: set[str] = set()
    if archive_path.exists():
        try:
            _arc = json.loads(archive_path.read_text(encoding="utf-8"))
            archived_uids = set(_arc.get("docs", {}).keys())
        except Exception as _e:
            print(f"  ⚠  lecture catalog_archive raté (réinjections possibles) : {_e}")

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

        # Score post-lecture (S1) : produit par synopsis_enricher si enrichi.
        # Audit 17/09 (MD-09) : une lecture ratée (résumé vide, erreur Claude,
        # PDF scanné) laissait le score sur la fiche — un score sans lecture.
        # `enrich_failed` marque ces cas ; la publication les écarte.
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
                  "drive_url", "archive_url"):
            if k in r:
                extras[k] = r[k]

        # Skip les docs déjà archivés : ils ne doivent pas réintégrer le catalog.
        if doc_id in archived_uids:
            continue

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
            # T1 — titre normalisé : renseigner doc.title si absent, à la première
            # téléchargement. On ne l'écrase jamais (corrections manuelles préservées).
            if r["downloaded"] and not fiche.get("title"):
                _pdf_title = ""
                if isinstance(extras.get("meta"), dict):
                    _pdf_title = extras["meta"].get("pdf_title", "") or ""
                _norm = doc_metadata.normalize_title(
                    link_text=r.get("link_text", "") or "",
                    pdf_title=_pdf_title,
                    filename=r.get("filename", "") or "",
                    author_hint=fiche.get("author", "") or "",
                )
                if _norm:
                    fiche["title"] = _norm
        else:
            catalog["docs"][doc_id] = {
                "id":             doc_id,
                "url":            safe_url(r["url"]),
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
            # T1 — titre normalisé à la création du doc (premier téléchargement)
            if r["downloaded"]:
                _pdf_title = ""
                if isinstance(extras.get("meta"), dict):
                    _pdf_title = extras["meta"].get("pdf_title", "") or ""
                _norm = doc_metadata.normalize_title(
                    link_text=r.get("link_text", "") or "",
                    pdf_title=_pdf_title,
                    filename=r.get("filename", "") or "",
                    author_hint=bib.get("author", "") or "",
                )
                if _norm:
                    catalog["docs"][doc_id]["title"] = _norm

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

    # Overrides manuels de score_final — appliqués en dernier, après tout
    # enrichissement, pour garantir leur persistance aux ré-runs.
    for doc_id, override in _SCORE_OVERRIDES.items():
        if doc_id in catalog["docs"]:
            catalog["docs"][doc_id]["score_final"] = override["score"]

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
PUBLISH_THRESHOLD = int(os.getenv("PUBLISH_THRESHOLD", "4"))

# Seuil de téléchargement (S0) : score minimum pour déclencher le
# téléchargement du fichier. Volontairement plus bas que PUBLISH_THRESHOLD
# pour capter les docs incertains (scoring post-lecture affinera).
DOWNLOAD_THRESHOLD = int(os.getenv("DOWNLOAD_THRESHOLD", "4"))


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


def _load_exclusions() -> set:
    """IDs de documents écartés de la publication par décision éditoriale
    (`config/exclusions.yml`). Le catalogue source reste exhaustif ; ces
    documents ne sont simplement ni pré-rendus, ni au sitemap, ni aux flux,
    ni dans le catalogue publié.
    """
    path = Path("config") / "exclusions.yml"
    if not path.exists():
        return set()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return set((data.get("exclusions") or {}).keys())
    except Exception as e:
        print(f"  ⚠  exclusions.yml illisible : {e}")
        return set()


_EXCLUSIONS = _load_exclusions()


def _load_score_overrides() -> dict:
    """Overrides manuels de score_final (config/score_overrides.yml).

    Survivent aux ré-enrichissements : appliqués APRÈS chaque écriture de
    score_final dans update_synopsis_catalog, ils garantissent que les docs
    whitelistés conservent leur score même si synopsis_enricher les ré-évalue.
    """
    path = Path("config") / "score_overrides.yml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data.get("score_overrides") or {}
    except Exception as e:
        print(f"  ⚠  score_overrides.yml illisible : {e}")
        return {}


_SCORE_OVERRIDES = _load_score_overrides()


def _enrichment_failed(doc: dict) -> bool:
    """Lecture tentée mais sans résultat exploitable (audit 17/09, MD-09)."""
    enr = doc.get("enrichment")
    if not isinstance(enr, dict):
        return False
    if "error" in enr:
        return True
    if "summary" in enr and not (enr.get("summary") or "").strip():
        return True
    return False


def _is_publishable(doc: dict) -> bool:
    """True si le doc doit apparaître dans RSS / sitemap / fiches pré-rendues.

    Trois conditions : non écarté par décision éditoriale (exclusions.yml),
    score effectif suffisant, ET ouvrage dans un format ouvert (jamais un
    article HTML — bibliothèque, pas revue de presse).

    SOURCE UNIQUE — ne pas réimplémenter ce calcul ailleurs (ex. un simple
    `score >= seuil`). Au moins deux régressions distinctes ont déjà été
    causées par une réimplémentation partielle de ce prédicat, dans deux
    scripts différents (`corpus_stats.py` puis `social_cards.py` — voir
    L28 et L34 dans lecons-biblio.md). Tout script qui a besoin de savoir
    si un doc est publiable doit importer et appeler cette fonction
    (import différé si le script est lui-même importé par watch.py, pour
    éviter un cycle).
    """
    if doc.get("id") in _EXCLUSIONS:
        return False
    # Un score sans lecture exploitable n'est pas un score (MD-09) : on ne
    # publie pas une fiche dont l'enrichissement a échoué, sauf si un score
    # post-lecture valide existe malgré tout.
    if _enrichment_failed(doc) and doc.get("score_final") is None:
        return False
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
        # ── Titre : doc.title (backfillé) > link_text > filename ──────────────
        # doc.title est le titre éditorial soigné (backfillé session #5).
        # link_text est le texte brut du lien sur la page source (peut contenir
        # des indications de format : "(PDF)", "page par page"…).
        title = doc.get("title", "") or ""
        if not title and doc.get("runs"):
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
        # runs[].raison (« erreur scoring », « auto_download… ») est un message
        # interne du pipeline : jamais utilisé comme description (audit 17/09).
        if not description:
            description = fallback_desc
        description = description.strip()[:300]

        # ── Source + score pour le fallback HTML ─────────────────────────────
        source = doc.get("source", "") or ""
        # Score effectif : score_final > score_initial > latest_score (cohérent
        # avec _effective_score et docScore côté JS).
        score = _effective_score(doc)

        # ── JSON-LD ScholarlyArticle (mêmes champs que côté JS) ──────────────
        canonical_url = f"{SITE_BASE_URL}/fiches/{doc_id}.html"
        # A2 — og:image pointe vers la carte sociale générée (1200x630).
        # Priorité : assets/cards/, puis couverture PDF brute, puis image
        # OG par défaut. (assets/og/ supprimé le 2026-07-06 : dupliquait
        # byte-à-byte assets/cards/ pour 299 Mo — cf. lecons-biblio.md,
        # l'artefact de déploiement GitHub Pages avait dépassé 1 Go.)
        card_file = SITE_PATH / "assets" / "cards" / f"{doc_id}.jpg"
        cover_file = SITE_PATH / "assets" / "covers" / f"{doc_id}.jpg"
        if card_file.exists():
            og_image = f"{SITE_BASE_URL}/assets/cards/{doc_id}.jpg"
        elif cover_file.exists():
            og_image = f"{SITE_BASE_URL}/assets/covers/{doc_id}.jpg"
        else:
            og_image = f"{SITE_BASE_URL}/assets/img/og-default.png"
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

        # ── Sections de contenu pré-calculées (hors f-string) ───────────────
        html_lang  = 'fr'  # interface, synopsis et « En clair » sont en français (WCAG 3.1.1)
        doc_date_h = esc(doc.get('doc_date', '') or '')
        editeur_h  = esc(doc.get('editeur', '') or '')

        def _paras(text: str) -> str:
            parts = [p.strip() for p in (text or '').split('\n\n') if p.strip()]
            return '\n'.join(f'<p>{esc(p)}</p>' for p in parts) or f'<p>{esc(str(text))}</p>'

        _summary_sec = ''
        if summary:
            _summary_sec = (
                '<section class="fiche-section">'
                '<h2>Synopsis</h2>'
                + _paras(summary) + '</section>'
            )

        _ec = (enrich.get('en_clair', '') or '') if isinstance(enrich, dict) else ''
        _enclair_sec = ''
        if _ec:
            _enclair_sec = (
                '<section class="fiche-section">'
                '<h2>En clair</h2>'
                + _paras(_ec) + '</section>'
            )

        # Une citation non confirmée verbatim dans le texte source reste
        # masquée tant qu'elle n'est pas confirmée (verified === true) —
        # décision de Ced, 6 juillet 2026 (session #22, suite). Cohérent
        # avec le filtre appliqué côté SPA (fiche.html::citationsSectionHTML).
        # Les données ne sont pas supprimées, seul l'affichage filtre.
        _raw_cits = (enrich.get('citations') or []) if isinstance(enrich, dict) else []
        _valid_cits = [c for c in _raw_cits
                       if isinstance(c, dict) and (c.get('quote_fr') or c.get('quote'))
                       and c.get('verified') is True]
        _cits_sec = ''
        if _valid_cits:
            _items = []
            for _i, _c in enumerate(_valid_cits[:10], 1):
                _qt = esc(_c.get('quote_fr') or _c.get('quote') or '')
                _pg = _c.get('page') or ''
                _pg_html = f'<small>p. {esc(str(_pg))}</small>' if _pg else ''
                _items.append(
                    f'<blockquote id="c{_i}" class="fiche-citation">'
                    f'<p>{_qt}</p>'
                    + (f'<footer>{_pg_html}</footer>' if _pg_html else '')
                    + '</blockquote>'
                )
            _cits_sec = (
                '<section class="fiche-section">'
                '<h2>Extraits</h2>'
                + '\n'.join(_items) + '</section>'
            )

        _meta_extra = (
            (f' <span aria-hidden="true">·</span> <span>{doc_date_h}</span>'
             if doc_date_h else '')
            + (f' <span aria-hidden="true">·</span> <span>{editeur_h}</span>'
               if editeur_h else '')
        )
        _orig_html = (
            f'<a class="btn btn-sm btn-ghost" href="{esc(doc.get("url",""))}"'
            f' target="_blank" rel="noopener">Document original ↗</a>'
        ) if doc.get('url') else ''

        # ── HTML statique complet — crawlable et lisible sans JS ─────────────
        html = f"""<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_h} — BIBLIO</title>
<link rel="canonical" href="{canonical_url}">
<meta name="description" content="{desc_h}">
<meta property="og:title" content="{title_h}">
<meta property="og:description" content="{desc_h}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{canonical_url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="BIBLIO — biblio.actitude.org">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld_json}</script>
<link rel="stylesheet" href="../assets/css/fonts.css">
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/components.css">
</head>
<body>

<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <filter id="biblio-inkrough" x="-30%" y="-30%" width="160%" height="160%">
    <feTurbulence type="fractalNoise" baseFrequency="0.35" numOctaves="2" seed="7" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.35 0 0 0 0.65" result="a"/>
    <feComposite in="SourceGraphic" in2="a" operator="in"/>
  </filter>
</svg>

<header class="site-header" role="banner">
  <div class="container">
    <a href="../index.html" class="brand" aria-label="BIBLIO — accueil">
      <img src="../assets/img/logo.svg" alt="" class="brand-mark">
      <span class="brand-name">BIBLIO</span>
      <span class="brand-sub">Bibliothèque documentaire ouverte</span>
    </a>
    <nav class="site-nav" id="site-nav" aria-label="Navigation principale">
      <a href="index.html">Catalogue</a>
      <a href="../dossiers.html">Dossiers</a>
      <a href="../concepts/index.html">Concepts</a>
      <a href="../chronologie.html">Chronologie</a>
      <div class="nav-dropdown" id="nav-apropos">
        <button class="nav-dropdown-btn" aria-expanded="false" aria-haspopup="true" aria-controls="nav-apropos-menu">
          À propos<svg viewBox="0 0 10 6" width="10" height="6" aria-hidden="true" class="nav-dropdown-caret"><path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>
        </button>
        <ul class="nav-dropdown-menu" id="nav-apropos-menu" role="menu">
          <li><a href="../auteurs.html" role="menuitem">Auteurs</a></li>
          <li><a href="../etat-corpus.html" role="menuitem">Corpus</a></li>
          <li><a href="../apropos.html" role="menuitem">Méthodologie</a></li>
        </ul>
      </div>
    </nav>
    <div class="header-tools">
      <button class="theme-toggle" type="button" aria-label="Basculer le thème"></button>
      <button class="menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="site-nav">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
    </div>
  </div>
</header>

<main id="main">
  <div class="container">
    <nav aria-label="fil d'Ariane">
      <ol class="breadcrumbs">
        <li><a href="../index.html">Accueil</a></li>
        <li><a href="index.html">Catalogue</a></li>
        <li>{title_h}</li>
      </ol>
    </nav>

    <article class="mt-3">
      <header>
        <h1 style="font-family:var(--font-serif);font-size:clamp(20px,4vw,30px);font-weight:600;line-height:1.25;margin:14px 0 10px;">{title_h}</h1>
        <p style="font-size:14px;color:var(--text-dim);margin:0 0 14px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">{source_h}{_meta_extra} <span class="biblio-stampbox">SCORE {score}/10</span></p>
        {_orig_html}
      </header>

{_summary_sec}
{_enclair_sec}
{_cits_sec}

      <div style="border-top:1px solid var(--border);padding-top:20px;margin-top:32px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
        <a class="btn btn-sm" href="fiche.html?id={doc_id_h}">Version interactive ↗</a>
        <span style="font-size:13px;color:var(--text-faint)">Fiches proches · BibTeX · partage par citation</span>
      </div>
    </article>
  </div>
</main>

<footer class="site-footer" role="contentinfo">
  <div class="container">
    <div>
      <h4>BIBLIO</h4>
      <p>Bibliothèque documentaire ouverte sur les communs, la propriété d'usage et les paysanneries.</p>
      <p style="font-size:13px;">Un projet de <a href="https://actitude.org" rel="noopener">actitude.org</a>.</p>
    </div>
    <div>
      <h4>Naviguer</h4>
      <ul>
        <li><a href="../index.html">Accueil</a></li>
        <li><a href="index.html">Catalogue</a></li>
        <li><a href="../dossiers.html">Dossiers</a></li>
        <li><a href="../etat-corpus.html">Corpus</a></li>
        <li><a href="../apropos.html">Méthodologie</a></li>
      </ul>
    </div>
    <div>
      <h4>Suivre &amp; réutiliser</h4>
      <ul>
        <li><a href="../feed.xml">Flux RSS — nouvelles fiches</a></li>
        <li>Fiches sous <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr" rel="noopener">CC-BY-NC-SA 4.0</a></li>
        <li><a href="mailto:contact@actitude.org">Contact</a></li>
      </ul>
    </div>
    <div class="colophon">
      <span>© 2026 BIBLIO · <code>biblio.actitude.org</code></span>
    </div>
  </div>
</footer>

<script src="../assets/js/router.js"></script>
<script src="../assets/js/app.js"></script>
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
        # On vérifie uniquement le format (8 hex) — pas la présence dans docs.
        # Un UID qui a quitté le catalogue doit aussi être purgé.
        if len(head) == 8 and all(c in "0123456789abcdef" for c in head):
            return head
        return None

    targets = [
        (SITE_PATH / "fiches",            ["*.html"]),
        (SITE_PATH / "data" / "bulles",   ["*.json"]),
        # .jpg (convention depuis session #17-18) ET .png (fichiers plus
        # anciens pas encore migrés) — un glob *.jpg seul laissait les
        # orphelins PNG s'accumuler silencieusement (trouvé session #20,
        # symétrique au même bug côté copie dans publish_site()).
        (SITE_PATH / "assets" / "covers", ["*.jpg", "*.png"]),
        # cartes sociales (social_cards.py) : cards/<id>.jpg (og:image),
        # cards/<id>-portrait.jpg, cards/<id>-cite-N.jpg. JPEG depuis le
        # 2026-07-06 (l'ancien PNG + l'alias assets/og/ dupliqué avaient fait
        # dépasser 1 Go l'artefact de déploiement GitHub Pages — assets/og/
        # supprimé, cf. lecons-biblio.md).
        (SITE_PATH / "assets" / "cards",  ["*.jpg"]),
    ]
    removed: dict = {}
    for directory, patterns in targets:
        if not directory.is_dir():
            continue
        n = 0
        for pattern in patterns:
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


# Champs de provenance technique retirés de tout ce qui est publié (décision
# Ced, 2026-09-18) : le droit d'auteur n'attribue pas de droits à une machine,
# on n'expose donc plus le modèle ni la version de prompt sur le site. Ils
# restent dans synopsis/catalog.json (traçabilité interne).
_PROVENANCE_KEYS = ("model", "prompt_version", "prompt_hash")


def _strip_provenance(obj):
    """Retire récursivement les clés de provenance technique d'un JSON publié."""
    if isinstance(obj, dict):
        return {k: _strip_provenance(v) for k, v in obj.items()
                if k not in _PROVENANCE_KEYS}
    if isinstance(obj, list):
        return [_strip_provenance(x) for x in obj]
    return obj


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

    # 1. Catalog — le catalogue publié ne contient QUE les docs publiables :
    # score effectif >= PUBLISH_THRESHOLD ET non écartés par exclusions.yml.
    # Les 580 docs non publiés (~1,8 Mo) sont inutiles côté public.
    # Le catalogue source (synopsis/catalog.json) reste exhaustif.
    catalog_src = SYNOPSIS_PATH / "catalog.json"
    if catalog_src.exists():
        (SITE_PATH / "data").mkdir(parents=True, exist_ok=True)
        site_catalog = SITE_PATH / "data" / "catalog.json"
        _cat = json.loads(catalog_src.read_text(encoding="utf-8"))
        _cat["docs"] = {i: _strip_provenance(d)
                        for i, d in _cat.get("docs", {}).items()
                        if _is_publishable(d)}
        site_catalog.write_text(
            json.dumps(_cat, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"  📦 Catalog public filtré : {len(_cat['docs'])} docs publiés "
              f"(score eff. >= {PUBLISH_THRESHOLD}, hors exclusions)")

    # 1bis. Index full-text + JSON éditoriaux (recherche, dossiers, stats…)
    for name in ("fulltext_index.json", "dossiers.json", "featured.json",
                 "corpus_stats.json"):
        src = SYNOPSIS_PATH / name
        if src.exists() and name == "dossiers.json" and catalog_src.exists():
            # Ne publier que les pièces présentes au catalogue public (audit
            # 17/09 : 128 docs dépubliés listés, liens vers fiches introuvables).
            _dj = json.loads(src.read_text(encoding="utf-8"))
            for _d in _dj.get("dossiers", []):
                _d["docs"] = [i for i in _d.get("docs", []) if i in _cat["docs"]]
                _d["docs_detail"] = [x for x in _d.get("docs_detail", [])
                                     if x.get("id") in _cat["docs"]]
                _d["doc_count"] = len(_d["docs"])
            (SITE_PATH / "data" / name).write_text(
                json.dumps(_dj, ensure_ascii=False, indent=1), encoding="utf-8")
        elif src.exists():
            shutil.copy2(src, SITE_PATH / "data" / name)

    # 2. Bulles
    site_bulles = SITE_PATH / "data" / "bulles"
    site_bulles.mkdir(parents=True, exist_ok=True)
    bulle_count = 0
    for b in BULLES_PATH.glob("*.json"):
        _b = _strip_provenance(json.loads(b.read_text(encoding="utf-8")))
        (site_bulles / b.name).write_text(
            json.dumps(_b, ensure_ascii=False, indent=1), encoding="utf-8")
        bulle_count += 1

    # 3. Couvertures — JPEG (convention depuis session #17-18, 1200px) en
    # priorité ; PNG (interface/covers/ contient encore des couvertures
    # 400px pas migrées) uniquement en fallback quand aucun JPEG n'existe
    # pour ce doc. Un premier correctif (session #20) copiait *.png sans
    # condition — corrigé une seconde fois le jour même : ça dupliquait
    # 572 couvertures déjà migrées en JPEG (le PNG legacy coexistant à côté
    # de son JPEG, jamais nettoyé). La bonne règle : jamais de PNG si un
    # JPEG existe déjà pour l'id, que ce soit fraîchement copié ci-dessous
    # ou déjà présent depuis la migration session #18.
    site_covers = SITE_PATH / "assets" / "covers"
    site_covers.mkdir(parents=True, exist_ok=True)
    cover_count = 0
    for c in COVERS_PATH.glob("*.jpg"):
        shutil.copy2(c, site_covers / c.name)
        cover_count += 1
    for c in COVERS_PATH.glob("*.png"):
        if (site_covers / f"{c.stem}.jpg").exists():
            continue  # JPEG déjà présent pour ce doc — ne pas dupliquer
        shutil.copy2(c, site_covers / c.name)
        cover_count += 1

    # 3bis-cover-flag — has_cover par doc dans le catalog publié, calculé
    # d'après l'existence RÉELLE du fichier dans site/assets/covers/ (et non
    # d'après un champ `cover` du catalogue source, qui peut être obsolète —
    # cf. lecons-biblio.md : ~16% du corpus publiable sans couverture, PDF
    # source manquant ou jamais traité). Permet au JS client de sauter la
    # tentative de requête image plutôt que de laisser un 404 arriver puis
    # être rattrapé par onerror.
    if catalog_src.exists():
        _cat2 = json.loads(site_catalog.read_text(encoding="utf-8"))
        n_with_cover = 0
        for _id, _d in _cat2.get("docs", {}).items():
            has_cover = (site_covers / f"{_id}.jpg").exists()
            _d["has_cover"] = has_cover
            if has_cover:
                n_with_cover += 1
        site_catalog.write_text(
            json.dumps(_cat2, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"  🖼  has_cover : {n_with_cover}/{len(_cat2.get('docs', {}))} "
              f"docs publiés ont une couverture")

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

    # 4. Génération RSS + sitemap + robots.txt
    catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
    _write_rss(catalog, run_date)
    _write_sitemap(catalog)
    _write_robots()

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
    # Titre éditorial (backfillé) en priorité, sinon link_text, sinon filename.
    title = d.get("title", "") or ""
    if not title and d.get("runs"):
        link_text = d["runs"][-1].get("link_text", "")
        if link_text:
            title = link_text
    if not title:
        title = d.get("filename", d.get("id", ""))
    # Nettoyer le préfixe « · » et le suffixe « (PDF) » résiduels
    title = title.strip()
    if title.startswith("· "):
        title = title[2:].strip()
    if title.endswith(" (PDF)"):
        title = title[:-6].strip()
    url_fiche = f"{SITE_BASE_URL}/fiches/{d['id']}.html"
    enrich = d.get("enrichment") or {}
    description = ""
    if isinstance(enrich, dict):
        description = enrich.get("summary", "") or ""
    # Fix 3 — ne pas utiliser la raison si elle contient "erreur" ou est vide
    if not description and d.get("runs"):
        raison = d["runs"][-1].get("raison", "") or ""
        if raison and "erreur" not in raison.lower():
            description = raison
    pub = _rfc822(d.get("latest_run", "") or d.get("collected_date", ""))
    # Fix 3 — omettre <description> si vide plutôt que d'émettre une balise vide
    desc_tag = (f"\n      <description>{_xml_escape(description[:600])}</description>"
                if description.strip() else "")
    return f"""    <item>
      <title>{_xml_escape(title)}</title>
      <link>{url_fiche}</link>
      <guid isPermaLink="true">{url_fiche}</guid>
      <pubDate>{pub}</pubDate>{desc_tag}
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
    scoops = [d for d in publishable if (d.get("score_final") or 0) >= 9][:30]
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


def _write_robots() -> None:
    """Génère site/robots.txt (idempotent)."""
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_BASE_URL}/sitemap.xml\n"
    )
    (SITE_PATH / "robots.txt").write_text(content, encoding="utf-8")


SITEMAP_LASTMOD_PATH = SYNOPSIS_PATH / "sitemap_lastmod.json"


def _doc_fingerprint(doc: dict) -> str:
    """Empreinte du contenu visible d'une fiche publiée.

    Sert à ne mettre à jour <lastmod> dans le sitemap que si quelque chose a
    réellement changé pour ce document — sinon (comportement précédent) le
    sitemap datait TOUTES les fiches au jour du run, à chaque régénération
    (plusieurs fois par jour possible via enrich_loop). Un <lastmod> qui ment
    sur ~870 URLs à chaque run noie le signal que les moteurs utilisent pour
    prioriser le recrawl. Vérification indexation du 2026-07-27.
    """
    enr = doc.get("enrichment") or {}
    citations = enr.get("citations") or []
    payload = {
        "title":     doc.get("title") or doc.get("link_text") or "",
        "title_fr":  doc.get("title_fr") or "",
        "author":    doc.get("author") or "",
        "doc_date":  doc.get("doc_date") or "",
        "score":     _effective_score(doc),
        "summary":   enr.get("summary") or "",
        "en_clair":  enr.get("en_clair") or "",
        "citations": [
            [(c.get("quote_fr") or c.get("quote") or ""), bool(c.get("verified"))]
            for c in citations
        ],
        "cover":       doc.get("cover") or "",
        "url":         doc.get("url") or "",
        "link_status": doc.get("link_status") or "",
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _load_sitemap_lastmod() -> dict:
    if SITEMAP_LASTMOD_PATH.exists():
        try:
            return json.loads(SITEMAP_LASTMOD_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write_sitemap(catalog: dict) -> None:
    """Sitemap XML avec les pages principales + une fiche par doc.

    <lastmod> par fiche reflète la dernière fois où son contenu a réellement
    changé (empreinte comparée à `synopsis/sitemap_lastmod.json`), pas la
    date du run courant. Les pages agrégées (accueil, dossiers…) gardent
    `today` : leur contenu (liste des dernières fiches, compteurs) évolue
    structurellement à chaque publication.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    entries = [
        (f"{SITE_BASE_URL}/", today),
        (f"{SITE_BASE_URL}/fiches/", today),
        (f"{SITE_BASE_URL}/apropos.html", today),
        (f"{SITE_BASE_URL}/auteurs.html", today),
        (f"{SITE_BASE_URL}/chronologie.html", today),
        (f"{SITE_BASE_URL}/dossiers.html", today),
        (f"{SITE_BASE_URL}/concepts/", today),
        (f"{SITE_BASE_URL}/une.html", today),
        (f"{SITE_BASE_URL}/etat-corpus.html", today),
    ]

    store = _load_sitemap_lastmod()
    seen_ids = set()
    # S1 — seules les fiches publiables (score effectif >= seuil) sont indexées
    for d in catalog.get("docs", {}).values():
        if not _is_publishable(d):
            continue
        doc_id = d["id"]
        seen_ids.add(doc_id)
        fp = _doc_fingerprint(d)
        prev = store.get(doc_id)
        lastmod = prev["lastmod"] if prev and prev.get("hash") == fp else today
        store[doc_id] = {"hash": fp, "lastmod": lastmod}
        entries.append((f"{SITE_BASE_URL}/fiches/{doc_id}.html", lastmod))

    # Purge des entrées de docs dépubliés — évite un fichier qui grossit sans fin
    for doc_id in list(store.keys()):
        if doc_id not in seen_ids:
            del store[doc_id]
    SITEMAP_LASTMOD_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    body = "\n".join(
        f"  <url><loc>{_xml_escape(u)}</loc><lastmod>{lm}</lastmod></url>"
        for u, lm in entries
    )
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
def _load_known_docs() -> tuple[dict, set]:
    """Catalogue courant (docs par uid) + uids archivés."""
    docs, archived = {}, set()
    try:
        cp = SYNOPSIS_PATH / "catalog.json"
        if cp.exists():
            docs = json.loads(cp.read_text(encoding="utf-8")).get("docs", {})
    except Exception as e:
        print(f"  ⚠  lecture catalog (filtre docs connus) ratée : {e}")
    try:
        ap = SYNOPSIS_PATH / "catalog_archive.json"
        if ap.exists():
            archived = set(json.loads(ap.read_text(encoding="utf-8")).get("docs", {}).keys())
    except Exception as e:
        print(f"  ⚠  lecture catalog_archive ratée : {e}")
    return docs, archived


def _known_skip_reason(url: str, known: dict, archived: set,
                       download_threshold: int) -> str | None:
    """Raison d'écarter un doc déjà connu (repéré par son URL), ou None s'il
    reste à traiter."""
    if os.getenv("FORCE_REENRICH", "false").lower() == "true":
        return None
    uids = {file_uid(url), file_uid(safe_url(url))}
    if uids & archived:
        return "archivé"
    fiche = next((known[u] for u in uids if u in known), None)
    if fiche is None:
        return None
    return _fiche_skip_reason(fiche, download_threshold)


def _fiche_skip_reason(fiche: dict, download_threshold: int) -> str | None:
    """Même règle, à partir de la fiche. Un doc connu reste à traiter tant
    qu'il n'a pas été lu (score_final absent), n'a pas été mis de côté, et
    qu'on n'a pas épuisé MAX_ENRICH_ATTEMPTS tentatives."""
    if fiche.get("score_final") not in (None, ""):
        return "déjà lu"
    if fiche.get("enrich_abandon"):
        return "mis de côté"
    runs = fiche.get("runs") or []
    if (fiche.get("score_initial") or 0) < download_threshold and not fiche.get("downloaded"):
        return "déjà écarté sur titre"
    dl_runs = sum(1 for r in runs if r.get("downloaded"))
    if dl_runs >= MAX_ENRICH_ATTEMPTS or len(runs) >= 2 * MAX_ENRICH_ATTEMPTS:
        return "tentatives épuisées"
    return None


def _auto_download_trust(known: dict) -> dict:
    """{source: (docs lus, docs lus au seuil de publication)}."""
    stats: dict = defaultdict(lambda: [0, 0])
    for d in known.values():
        sf = d.get("score_final")
        if isinstance(sf, (int, float)):
            e = stats[d.get("source", "")]
            e[0] += 1
            e[1] += sf >= 4
    return stats


def main() -> None:
    config    = load_config()
    keywords  = config.get("keywords", [])
    sources   = config.get("sources", [])
    threshold = int(os.getenv("SCORE_THRESHOLD", str(config.get("threshold", 6))))
    download_threshold = int(os.getenv("DOWNLOAD_THRESHOLD", str(config.get("download_threshold", 4))))
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
        "interrupted":          None,
    }
    t0 = time.monotonic()
    known_docs, archived_uids = _load_known_docs()
    trust = _auto_download_trust(known_docs)

    def _stop_reason() -> str | None:
        if claude_guard.session_limit_active():
            return "limite de session Claude"
        if time.monotonic() - t0 > WATCH_BUDGET_MIN * 60:
            return f"budget de {WATCH_BUDGET_MIN:.0f} min atteint"
        return None

    for source in sources:
        stop = _stop_reason()
        if stop:
            report["interrupted"] = stop
            print(f"\n⏹   Collecte interrompue ({stop}) — sources restantes "
                  f"reportées au prochain run.")
            break
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
        # découverte même s'ils ne produisent aucune fiche. Appelé seulement
        # une fois la source ENTIÈREMENT traitée : une source interrompue par
        # le budget reste « due » et sera reprise au run suivant.
        def _record_fetch(source=source, docs_raw=docs_raw):
            try:
                throttle.record_fetch(
                    source,
                    success=bool(docs_raw),
                    doc_count=len(docs_raw),
                    status_code=200 if docs_raw else 204,
                )
            except Exception as e:
                print(f"  ⚠  throttle.record_fetch raté : {e}")

        # Docs déjà connus et déjà traités : écartés avant scoring/téléchargement.
        fresh, skipped = [], Counter()
        for d in docs:
            why = _known_skip_reason(d.get("url", ""), known_docs, archived_uids,
                                     download_threshold)
            if why:
                skipped[why] += 1
            else:
                fresh.append(d)
        if skipped:
            print(f"    ⏭  {sum(skipped.values())} doc(s) déjà connu(s) écarté(s) : "
                  + ", ".join(f"{k} ×{v}" for k, v in skipped.items()))
        docs = fresh
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
            _record_fetch()
            continue
        report["sources_scanned"] += 1
        print(f"    → {len(docs)} ouvrage(s) PDF trouvé(s)")
        report["documents_found"] += len(docs)

        # Injecter le label de la source dans chaque doc pour le scoring
        for d in docs:
            d.setdefault("source", label)

        # ── Auto-download : sources 100 % thématiques ───────────────────────
        # Certaines sources (marquées auto_download: true dans sources.yml)
        # sont considérées fiables par construction : on leur attribue un
        # score de 8 sans appel LLM, ce qui économise des tokens et accélère
        # le pipeline. Le scoring post-lecture reste actif.
        auto_dl = bool(source.get("auto_download"))
        if auto_dl:
            n_read, n_ok = trust.get(label, (0, 0))
            if n_read >= AUTO_DL_MIN_READ and n_ok / n_read < AUTO_DL_MIN_RATIO:
                auto_dl = False
                print(f"    ⚠  auto_download ignoré : seulement {n_ok}/{n_read} docs lus "
                      f"au seuil (< {AUTO_DL_MIN_RATIO:.0%}) — scoring sur titre")
        if auto_dl:
            print(f"    ⚡  auto_download activé — score 8 attribué sans LLM")
            all_scores = [
                {
                    "doc": idx + 1,
                    "score": 8,
                    "raison": "auto_download (source fiable)",
                    "doc_type": "autre",
                    "recit_de_lutte": False,
                }
                for idx in range(len(docs))
            ]
        else:
            # ── Scoring par batches ─────────────────────────────────────────
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
                        it["doc"] = d + i      # indice local au batch → global
                all_scores.extend(batch_scores)

        report["documents_scored"] += len(all_scores)
        interrupted = None
        for item in all_scores:
            interrupted = _stop_reason()
            if interrupted:
                break
            idx = item.get("doc", 0) - 1
            if idx < 0 or idx >= len(docs):
                continue
            doc    = docs[idx]
            score  = item.get("score", 0)
            raison = item.get("raison", "")

            result = {
                "url":          safe_url(doc["url"]),
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

            # S2 — Métadonnées légères pour TOUS les docs (pas seulement téléchargés)
            # Au minimum : detect_lang_hints sur titre/filename + default_lang source.
            # Sera enrichi avec le texte PDF si le doc est téléchargé.
            try:
                bib_light = doc_metadata.build_metadata(
                    doc, source_default_lang=source.get("default_lang", ""),
                )
                if bib_light:
                    result["bib"] = bib_light
            except Exception as e:
                print(f"     ⚠  build_metadata léger raté : {e}")

            if score >= download_threshold and not dry_run:
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
                    enrichment = analyse_pdf_and_enrich(
                        dest, doc, score, keywords,
                        source_default_lang=source.get("default_lang", ""),
                    )
                    result.update(enrichment)
            elif score >= download_threshold and dry_run:
                print(f"    [sim] Aurait téléchargé : {doc['filename']} ({score}/10)")
            else:
                print(f"    ✗  Ignoré          : {doc['filename']} ({score}/10 — {raison})")

            report["results"].append(result)
        if interrupted:
            report["interrupted"] = interrupted
            print(f"\n⏹   Collecte interrompue ({interrupted}) pendant « {label} » — "
                  f"source non marquée comme visitée, reprise au prochain run.")
            break
        _record_fetch()
    report["claude_session_limit_hit"] = claude_guard.session_limit_active()

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
    # Vérifications HTTP parallèles : tout le catalogue est couvert en un run
    # (les liens vérifiés récemment sont sautés, cf. RECHECK_AFTER_DAYS).
    # L'archivage Wayback reste séquentiel et borné (archive_limit) pour ne pas
    # marteler archive.org ; il cible en priorité les fiches publiées.
    if not dry_run:
        try:
            ls = link_check.check_catalog(
                SYNOPSIS_PATH / "catalog.json", limit=None, do_archive=True,
                prioritize=_is_publishable, archive_limit=30,
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

    # ── Traduction des citations en français ──────────────────────────────────
    print("\n🌐  Traduction des citations (→ fr)")
    try:
        tr_stats = translate_citations.run(
            catalog_path=SYNOPSIS_PATH / "catalog.json",
            verbose=True,
        )
        print(f"  📖  Traduction : {tr_stats['docs_processed']} doc(s), "
              f"{tr_stats['citations_translated']} citation(s)")
    except Exception as e:
        print(f"  ⚠  translate_citations raté : {e}")

    # ── Archivage des docs hors-sujet ────────────────────────────────────────
    # Déplace les docs à score faible des sources bruyantes vers
    # synopsis/catalog_archive.json. Non bloquant.
    try:
        import archive_catalog
        arc = archive_catalog.run(
            catalog_path=SYNOPSIS_PATH / "catalog.json",
            archive_path=SYNOPSIS_PATH / "catalog_archive.json",
            dry_run=False,
            verbose=True,
        )
    except Exception as e:
        print(f"  ⚠  archive_catalog raté : {e}")

    publish_site(run_date)

    # Garde-fou — contrôle de cohérence du site publié (orphelins, sitemap,
    # langue JSON-LD, licence). Non bloquant : un défaut est signalé, pas fatal.
    try:
        import audit_site
        if audit_site.main() != 0:
            print("  ⚠  audit_site : incohérence détectée — voir ci-dessus")
    except Exception as e:
        print(f"  ⚠  audit_site raté : {e}")

    if claude_guard.session_limit_active():
        print(f"⚠️  Limite de session Claude atteinte pendant ce run — scoring/"
              f"enrichissement dégradés pour le reste des documents (fallback "
              f"appliqué). Voir claude_session_limit_hit dans le rapport.")
    print(f"""
╔══════════════════════════════════════════╗
  Veille terminée — {run_date}
  Sources scannées    : {report['sources_scanned']}
  Documents trouvés   : {report['documents_found']}
  Scorés par Claude   : {report['documents_scored']}
  Téléchargés         : {report['documents_downloaded']}
  Collecte interrompue : {report['interrupted'] or "non"}
  Durée collecte      : {(time.monotonic() - t0) / 60:.0f} min
  Limite session Claude : {"OUI — voir ci-dessus" if claude_guard.session_limit_active() else "non"}
  Rapport             : {json_path}
╚══════════════════════════════════════════╝""")


if __name__ == "__main__":
    main()
