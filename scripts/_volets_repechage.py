#!/usr/bin/env python3
"""
Script de repêchage — trois volets :
  A. Télécharger les "fiches creuses" à score_override élevé
  B. Enrichir les docs téléchargés à score 4-5 sans summary (et corriger titres)
  C. Vérifier les titres incertains des fiches publiées via fitz

Usage : python3 scripts/_volets_repechage.py
"""

import json
import sys
import re
from pathlib import Path

# On s'assure d'importer les modules du projet
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import fitz  # PyMuPDF
import requests
import yaml

CATALOG_PATH = PROJECT_ROOT / "synopsis" / "catalog.json"
EXCLUSIONS_PATH = PROJECT_ROOT / "config" / "exclusions.yml"
DOCS_DIR = PROJECT_ROOT / "docs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"
}

# ──────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ──────────────────────────────────────────────────────────────────────────────

def load_catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)

def save_catalog(cat):
    with open(CATALOG_PATH, "w") as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    print("  ✓ catalog.json sauvegardé")

def load_exclusions():
    with open(EXCLUSIONS_PATH) as f:
        return yaml.safe_load(f) or {"exclusions": {}}

def save_exclusions(exc):
    with open(EXCLUSIONS_PATH, "w") as f:
        yaml.dump(exc, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
    print("  ✓ exclusions.yml sauvegardé")

def extract_pdf_text(pdf_path: Path, max_chars: int = 8000) -> str:
    """Extrait le texte d'un PDF via fitz, limité à max_chars."""
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
            if len(text) >= max_chars:
                break
        doc.close()
        return text[:max_chars]
    except Exception as e:
        print(f"    ⚠ Erreur extraction texte {pdf_path}: {e}")
        return ""

def extract_pdf_title(pdf_path: Path) -> str:
    """Extrait le titre depuis métadonnées fitz ou première page."""
    try:
        doc = fitz.open(str(pdf_path))
        # Métadonnées
        meta_title = (doc.metadata or {}).get("title", "").strip()
        if meta_title and len(meta_title) > 4 and not meta_title.lower().startswith("microsoft"):
            doc.close()
            return meta_title
        # Première page — premier bloc de texte substantiel
        if doc.page_count > 0:
            page = doc[0]
            blocks = page.get_text("blocks")
            doc.close()
            for block in blocks:
                t = block[4].strip() if len(block) > 4 else ""
                t = re.sub(r'\s+', ' ', t)
                if 10 < len(t) < 200:
                    return t
        doc.close()
    except Exception as e:
        print(f"    ⚠ Erreur extraction titre {pdf_path}: {e}")
    return ""

def download_pdf(url: str, dest: Path) -> tuple[bool, str]:
    """Télécharge un PDF et vérifie sa validité basique."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        # Validation minimale
        if dest.stat().st_size < 1000:
            dest.unlink()
            return False, "trop petit"
        try:
            d = fitz.open(str(dest))
            n = d.page_count
            d.close()
            if n == 0:
                dest.unlink()
                return False, "0 pages"
            return True, f"{n} pages"
        except Exception as e:
            dest.unlink()
            return False, f"PDF invalide: {e}"
    except Exception as e:
        if dest.exists():
            dest.unlink()
        return False, str(e)

def score_thematique(text: str, title: str = "") -> int:
    """Score thématique 0-10 basé sur les thèmes communs fonciers/paysannerie/propriété d'usage."""
    combined = (title + " " + text).lower()

    # Thèmes centraux (très pertinents)
    themes_core = [
        "commun", "commons", "foncier", "land reform", "réforme agraire", "agrarian reform",
        "propriété d'usage", "use rights", "coopérative", "cooperative", "co-op", "cohousing",
        "community land trust", "clt", "paysann", "peasant", "paysan", "small farmer",
        "terra", "land rights", "droit foncier", "tenure", "usufruit", "usufruct",
        "bien commun", "common good", "communs", "collectif", "collectiv",
        "habitat participatif", "co-housing", "cohabitat",
    ]

    # Thèmes connexes (pertinents)
    themes_related = [
        "logement", "housing", "habitat", "propriété", "property", "ownership",
        "autonomie", "autogestion", "self-management", "autogouvernement",
        "alternative", "solidarity", "solidarité", "mutual aid", "entraide",
        "rural", "agriculture", "farm", "ferme", "peasantry",
        "customary", "coutumier", "indigenous", "autochtone",
        "coopérat", "coopérat", "association", "collectif",
    ]

    core_count = sum(1 for t in themes_core if t in combined)
    related_count = sum(1 for t in themes_related if t in combined)

    # Score de base
    score = min(4, core_count) * 1.5 + min(3, related_count) * 0.5
    score = min(10, round(score))

    # Bonus si très concentré en thèmes core
    if core_count >= 5:
        score = max(score, 7)
    elif core_count >= 3:
        score = max(score, 6)
    elif core_count >= 2:
        score = max(score, 5)

    return int(score)

def generate_summary(text: str, title: str, url: str) -> str:
    """Génère un résumé en français à partir du texte extrait (sans Claude API)."""
    # Extraction des premiers paragraphes significatifs
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 40]
    intro = ' '.join(lines[:5])[:500] if lines else text[:500]

    # Titre propre
    safe_title = title or "Ce document"

    return (
        f"{safe_title}. "
        f"Document accessible à {url}. "
        f"Extrait : {intro.strip()}"
    )[:800]

def uid_from_url(url: str) -> str:
    """Reproduit la logique file_uid du pipeline (hash MD5 tronqué)."""
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:8]

def safe_filename(uid: str, url: str) -> str:
    """Génère un nom de fichier depuis uid + fin de l'URL."""
    from urllib.parse import urlparse
    path = urlparse(url).path
    basename = Path(path).stem[:40]
    # Nettoyer
    basename = re.sub(r'[^a-zA-Z0-9_\-]', '_', basename).strip('_')
    if not basename:
        basename = "doc"
    return f"{uid}_{basename}.pdf"


# ──────────────────────────────────────────────────────────────────────────────
# VOLET A — Télécharger les fiches creuses à score_override élevé
# ──────────────────────────────────────────────────────────────────────────────

VOLET_A_UIDS = [
    '44510a9a',  # score 9
    '6d4f3628',  # score 8
    '2e2e4bc7',  # score 8
    'eb18a3de',  # score 7
    '28b7cb2c',  # score 7
    'b0917bdf',  # score 8
    '99a6d367',  # score 8
    '2175f7a3',  # score 7
    '941861fb',  # score 8
    '96563571',  # score 9
]

def volet_a(cat, exclusions):
    print("\n" + "="*60)
    print("VOLET A — Téléchargement fiches creuses (score élevé)")
    print("="*60)

    results = {"success": [], "failed": []}
    docs = cat["docs"]
    exc = exclusions["exclusions"]

    for uid in VOLET_A_UIDS:
        doc = docs.get(uid)
        if not doc:
            print(f"\n[{uid}] MANQUANT dans le catalogue — skip")
            results["failed"].append((uid, "absent du catalogue"))
            continue

        url = doc.get("url", "")
        title = doc.get("title", uid)
        print(f"\n[{uid}] {title[:60]}")
        print(f"  URL: {url}")

        # Nom de fichier destination
        fname = safe_filename(uid, url)
        dest = DOCS_DIR / fname

        if dest.exists():
            print(f"  ↳ Déjà sur disque : {fname}")
        else:
            # Tentative de téléchargement
            print(f"  → Téléchargement...")
            ok, status = download_pdf(url, dest)

            if not ok and "archive.org/download/" in url:
                # Tenter variante archive.org via metadata API
                try:
                    parts = url.split("archive.org/download/", 1)[1].split("/", 1)
                    identifier = parts[0]
                    meta_url = f"https://archive.org/metadata/{identifier}"
                    r = requests.get(meta_url, headers=HEADERS, timeout=10)
                    if r.ok:
                        data = r.json()
                        for fentry in (data.get("files") or []):
                            fname_entry = fentry.get("name", "")
                            if fname_entry.lower().endswith(".pdf"):
                                variant = f"https://archive.org/download/{identifier}/{fname_entry}"
                                if variant != url:
                                    print(f"  → Variante archive.org: {variant}")
                                    ok, status = download_pdf(variant, dest)
                                    if ok:
                                        doc["url"] = variant
                                        break
                except Exception as e:
                    print(f"  ⚠ metadata archive.org: {e}")

            if not ok:
                print(f"  ✗ Échec téléchargement: {status}")
                results["failed"].append((uid, status))
                continue

            print(f"  ✓ Téléchargé: {fname} ({status})")

        # Extraire texte et enrichir
        text = extract_pdf_text(dest, max_chars=8000)
        if not text.strip():
            print(f"  ⚠ Texte vide — PDF peut-être scanné sans OCR")

        # Extraire vrai titre
        real_title = extract_pdf_title(dest)
        if real_title and len(real_title) > 5:
            print(f"  → Titre PDF: {real_title[:70]}")
            doc["title"] = real_title

        # Score thématique
        computed_score = score_thematique(text, doc.get("title", ""))
        print(f"  → Score thématique: {computed_score}")

        # Summary
        summary = generate_summary(text, doc.get("title", ""), url)

        # Mettre à jour le doc
        doc["saved_as"] = f"docs/{fname}"
        if "enrichment" not in doc or doc["enrichment"] is None:
            doc["enrichment"] = {}
        doc["enrichment"]["summary"] = summary
        doc["enrichment"]["score_final"] = computed_score
        doc["score_final"] = computed_score

        # Dé-exclure si score >= 6
        if computed_score >= 6:
            if uid in exc:
                del exc[uid]
                print(f"  ✓ Dé-exclu (score {computed_score} ≥ 6)")
            results["success"].append((uid, computed_score, doc.get("title", "")[:50]))
        else:
            print(f"  → Score {computed_score} < 6 — reste exclu")
            results["failed"].append((uid, f"score trop bas ({computed_score})"))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# VOLET B — Enrichir les docs score 4-5 sans summary + corriger titres
# ──────────────────────────────────────────────────────────────────────────────

VOLET_B1_UIDS = [
    'de093853', '2f70c746', 'bfc53f3a', 'ae302e09', '31c1c30a',
    'b9a459d4', '98e8416d', 'bd82431e', 'e41de87d',
]

VOLET_B2_UIDS = [
    'cf647afe', '1fe48a41', '3486835f', '514c1d0e', '5736cd8e',
    'b8342aff', '5517ea32', '6ac17e44', '7c44a8d2', '9f38ee12', 'cc483884',
]

def volet_b(cat):
    print("\n" + "="*60)
    print("VOLET B — Enrichissement docs téléchargés score 4-5")
    print("="*60)

    results = {"enriched": [], "corrected_title": [], "score_raised": []}
    docs = cat["docs"]

    all_b = VOLET_B1_UIDS + VOLET_B2_UIDS

    for uid in all_b:
        doc = docs.get(uid)
        if not doc:
            print(f"\n[{uid}] MANQUANT — skip")
            continue

        saved_as = doc.get("saved_as", "")
        if not saved_as:
            print(f"\n[{uid}] Pas de saved_as — skip")
            continue

        # Chemin absolu
        pdf_path = PROJECT_ROOT / saved_as
        if not pdf_path.exists():
            print(f"\n[{uid}] PDF absent: {pdf_path} — skip")
            continue

        print(f"\n[{uid}] {doc.get('title', 'N/A')[:60]}")

        # Extraire vrai titre
        real_title = extract_pdf_title(pdf_path)
        current_title = doc.get("title") or ""

        if real_title and len(real_title) > 5 and real_title != current_title:
            print(f"  → Titre extrait: {real_title[:70]}")
            doc["title"] = real_title
            results["corrected_title"].append((uid, real_title[:50]))

        # Extraire texte
        text = extract_pdf_text(pdf_path, max_chars=8000)

        enr = doc.get("enrichment") or {}

        # Enrichir si pas de summary
        if not enr.get("summary"):
            summary = generate_summary(text, doc.get("title", ""), doc.get("url", ""))
            enr["summary"] = summary
            computed_score = score_thematique(text, doc.get("title", ""))
            enr["score_final"] = computed_score
            doc["enrichment"] = enr
            doc["score_final"] = computed_score
            print(f"  → Summary généré, score: {computed_score}")
            results["enriched"].append((uid, computed_score))
            if computed_score >= 6:
                results["score_raised"].append((uid, computed_score, doc.get("title", "")[:50]))
        else:
            # Juste recalculer le score si manquant
            if not enr.get("score_final") and not doc.get("score_final"):
                computed_score = score_thematique(text, doc.get("title", ""))
                enr["score_final"] = computed_score
                doc["enrichment"] = enr
                doc["score_final"] = computed_score
                print(f"  → Score recalculé: {computed_score}")
                if computed_score >= 6:
                    results["score_raised"].append((uid, computed_score, doc.get("title", "")[:50]))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# VOLET C — Vérifier titres incertains des fiches publiées
# ──────────────────────────────────────────────────────────────────────────────

VOLET_C_UIDS = [
    '9e8c8fc5', '08baa6d1', '235a98fb', '8413ce56', 'cbb3d138',
    '79cc5801', 'c97fba28', '47c6599a', 'a54f94c8', 'de8665e3',
    'dd858578', '42750467', '95ced9d7',
]

def title_looks_like_filename(title: str) -> bool:
    """Détecte si un titre ressemble à un nom de fichier décodé."""
    if not title:
        return True
    # Beaucoup de tirets et underscores
    t = title.lower()
    dash_ratio = (t.count('-') + t.count('_')) / max(len(t), 1)
    if dash_ratio > 0.1:
        return True
    # Pas de majuscules naturelles (tout minuscule ou tout fichier)
    words = title.split()
    if len(words) > 2 and title == title.lower():
        return True
    # Patterns typiques de filename
    if re.search(r'\b(20\d\d|A4|A5|A6|p\d+|cahier|livret|fil|nb|bw)\b', title, re.I):
        return True
    return False

def volet_c(cat):
    print("\n" + "="*60)
    print("VOLET C — Vérification titres incertains")
    print("="*60)

    results = {"updated": [], "kept": [], "no_pdf": []}
    docs = cat["docs"]

    for uid in VOLET_C_UIDS:
        doc = docs.get(uid)
        if not doc:
            print(f"\n[{uid}] MANQUANT — skip")
            continue

        current_title = doc.get("title", "")
        saved_as = doc.get("saved_as", "")
        print(f"\n[{uid}] Titre actuel: {current_title[:70]}")

        if not saved_as:
            print(f"  ⚠ Pas de saved_as")
            results["no_pdf"].append((uid, current_title))
            continue

        pdf_path = PROJECT_ROOT / saved_as
        if not pdf_path.exists():
            print(f"  ⚠ PDF absent: {pdf_path}")
            results["no_pdf"].append((uid, current_title))
            continue

        # Extraire titre depuis PDF
        real_title = extract_pdf_title(pdf_path)

        if real_title and len(real_title) > 5:
            print(f"  → Titre PDF: {real_title[:70]}")

            # Décider si on met à jour
            should_update = (
                title_looks_like_filename(current_title) or
                real_title.lower() not in current_title.lower() and
                len(real_title) > len(current_title)
            )

            if should_update and real_title != current_title:
                doc["title"] = real_title
                print(f"  ✓ Titre mis à jour")
                results["updated"].append((uid, current_title[:50], real_title[:50]))
            else:
                print(f"  → Titre conservé (OK ou pas mieux)")
                results["kept"].append((uid, current_title[:50]))
        else:
            print(f"  ⚠ Pas de titre extrait du PDF")
            results["kept"].append((uid, current_title[:50]))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("Chargement du catalogue et des exclusions...")
    cat = load_catalog()
    exclusions = load_exclusions()

    total_docs_before = len(cat["docs"])
    print(f"  Catalogue: {total_docs_before} docs")

    # Volet A
    res_a = volet_a(cat, exclusions)

    # Volet B
    res_b = volet_b(cat)

    # Volet C
    res_c = volet_c(cat)

    # Sauvegarder
    print("\n" + "="*60)
    print("SAUVEGARDE")
    print("="*60)
    save_catalog(cat)
    save_exclusions(exclusions)

    # Rapport
    print("\n" + "="*60)
    print("RAPPORT FINAL")
    print("="*60)

    print(f"\n[Volet A] Fiches creuses téléchargées et dé-exclues:")
    for uid, score, title in res_a["success"]:
        print(f"  ✓ {uid} (score {score}) — {title}")
    print(f"[Volet A] Échecs:")
    for uid, reason in res_a["failed"]:
        print(f"  ✗ {uid} — {reason}")

    print(f"\n[Volet B] Docs enrichis (nouveaux summaries):")
    for uid, score in res_b["enriched"]:
        print(f"  ✓ {uid} (score {score})")
    print(f"[Volet B] Titres corrigés:")
    for uid, title in res_b["corrected_title"]:
        print(f"  ✓ {uid} → {title}")
    print(f"[Volet B] Score ≥ 6 (candidats publication):")
    for uid, score, title in res_b["score_raised"]:
        print(f"  ★ {uid} (score {score}) — {title}")

    print(f"\n[Volet C] Titres mis à jour:")
    for uid, old, new in res_c["updated"]:
        print(f"  ✓ {uid}: '{old}' → '{new}'")
    print(f"[Volet C] Titres conservés: {len(res_c['kept'])}")
    print(f"[Volet C] PDFs absents: {len(res_c['no_pdf'])}")

    # Stats globales
    a_ok = len(res_a["success"])
    b_enr = len(res_b["enriched"])
    b_tit = len(res_b["corrected_title"])
    b_pub = len(res_b["score_raised"])
    c_upd = len(res_c["updated"])

    print(f"\n{'─'*40}")
    print(f"  Volet A: {a_ok}/{len(VOLET_A_UIDS)} docs téléchargés et dé-exclus")
    print(f"  Volet B: {b_enr} enrichis, {b_tit} titres corrigés, {b_pub} nouveaux ≥ 6")
    print(f"  Volet C: {c_upd} titres PDF mis à jour")
    print(f"{'─'*40}")

if __name__ == "__main__":
    main()
