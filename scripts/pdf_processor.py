#!/usr/bin/env python3
"""
pdf_processor.py — Validation des PDFs, bypass anti-bot, extraction texte/couverture.

Trois fonctions principales :
- validate_pdf(path)         : True si le fichier est un vrai PDF
- redownload_with_bypass(...) : retry avec UA navigateur + délai
- extract_text(path, max_chars) : extrait jusqu'à max_chars du PDF
- extract_cover(path, out)   : sauve la page 1 en PNG (thumbnail)
- extract_metadata(path)     : titre, auteur, nb pages, etc.
"""

import time
import requests
from pathlib import Path

# Magic bytes des vrais PDFs
PDF_MAGIC = b"%PDF-"

# User-agents : commence par celui du LibraryBot, fallback Chrome desktop
UA_BOT     = "Mozilla/5.0 (compatible; LibraryBot/1.0)"
UA_BROWSER = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# Headers compatibles navigateur (au cas où certains sites filtrent)
BROWSER_HEADERS = {
    "User-Agent":      UA_BROWSER,
    "Accept":          "application/pdf,application/octet-stream,*/*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":  "document",
    "Sec-Fetch-Mode":  "navigate",
}


def validate_pdf(path: Path) -> bool:
    """True si le fichier commence par les magic bytes PDF."""
    if not path.exists() or path.stat().st_size < 100:
        return False
    with open(path, "rb") as f:
        return f.read(5) == PDF_MAGIC


def redownload_with_bypass(url: str, dest: Path,
                            delay_sec: float = 2.0) -> tuple[bool, str]:
    """Retente le download avec un User-Agent navigateur + délai anti-rate-limit.

    Retourne (success, error_message).
    """
    time.sleep(delay_sec)
    try:
        # Session pour gérer cookies (utile sur HAL et autres)
        sess = requests.Session()
        sess.headers.update(BROWSER_HEADERS)
        r = sess.get(url, timeout=60, stream=True, allow_redirects=True)
        r.raise_for_status()

        # Si le content-type n'est pas PDF, c'est suspect
        ct = r.headers.get("content-type", "").lower()
        if "pdf" not in ct and "octet-stream" not in ct:
            return False, f"content-type={ct}"

        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        if validate_pdf(dest):
            return True, "bypass_ok"
        return False, "still_not_pdf_after_bypass"
    except requests.RequestException as e:
        return False, f"requests_error: {e}"


def download_with_playwright(url: str, dest: Path,
                              timeout_ms: int = 45000) -> tuple[bool, str]:
    """Bypass ultime : Playwright avec navigateur headless. Résout les JS
    challenges (HAL, Cloudflare, etc.) puis intercepte la réponse PDF.

    Stratégie :
    - Active le téléchargement automatique côté navigateur
    - Navigue vers l'URL
    - Si le navigateur déclenche un download → on l'intercepte
    - Sinon, on tente de lire la page comme PDF inline (response body)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright_not_installed"

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                context = browser.new_context(
                    user_agent=UA_BROWSER,
                    accept_downloads=True,
                )
                page = context.new_page()

                # Cas 1 : la page déclenche un download automatique
                download_caught = []
                page.on("download", lambda dl: download_caught.append(dl))

                try:
                    response = page.goto(url, timeout=timeout_ms,
                                         wait_until="networkidle")
                except Exception as e:
                    # Parfois networkidle timeout mais le DL a déjà eu lieu
                    print(f"  ↳ playwright nav warning: {e}")
                    response = None

                # Attendre brièvement qu'un éventuel challenge JS se résolve
                page.wait_for_timeout(3000)

                if download_caught:
                    download_caught[0].save_as(dest)
                else:
                    # Cas 2 : la page elle-même est le PDF (inline)
                    if response is not None:
                        body = response.body()
                        if body and body.startswith(PDF_MAGIC):
                            dest.write_bytes(body)
                        else:
                            # Tenter de re-télécharger avec les cookies de la session
                            cookies = context.cookies()
                            sess = requests.Session()
                            sess.headers.update(BROWSER_HEADERS)
                            for c in cookies:
                                sess.cookies.set(c["name"], c["value"],
                                                 domain=c.get("domain"))
                            r = sess.get(url, timeout=60, stream=True,
                                         allow_redirects=True)
                            with open(dest, "wb") as f:
                                for chunk in r.iter_content(8192):
                                    f.write(chunk)
                    else:
                        return False, "no_response_no_download"

                if validate_pdf(dest):
                    return True, "playwright_ok"
                return False, "playwright_not_pdf"
            finally:
                browser.close()
    except Exception as e:
        return False, f"playwright_exception: {e}"


# ── PyMuPDF (lazy import — pas bloquant si manquant) ──────────────────────────
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def _is_cover_page(text: str) -> bool:
    """Heuristique : page 1 est-elle une page de couverture sans contenu ?

    Une page de couverture typique a peu de texte réel — principalement
    titre, auteur, date, éditeur — et aucune phrase complète de plus de
    15 mots. On la détecte par : moins de 120 chars de contenu réel (hors
    lignes courtes < 40 chars) OU moins de 3 lignes de texte substantiel.
    """
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    # Lignes substantielles = contiennent au moins 5 mots
    substantial = [ln for ln in lines if len(ln.split()) >= 5]
    real_chars = sum(len(ln) for ln in substantial)
    return len(substantial) <= 2 or real_chars < 120


# Patterns de bruit connus, source par source.
# Chaque entrée est un regex compilé qui matche une ligne entière de bruit.
import re as _re

_NOISE_LINE_PATTERNS = [
    # Banque mondiale — "Public Disclosure Authorized" répété
    _re.compile(r"^Public\s+Disclosure\s+Authorized\s*$", _re.I),
    # Archive.org boilerplate
    _re.compile(r"^Digitized by\s+Google\b", _re.I),
    _re.compile(r"^Google\s*$", _re.I),
    _re.compile(r"^INTERNET\s+ARCHIVE\s*$", _re.I),
    # HAL — en-tête de dépôt
    _re.compile(r"^HAL\s+Id\s*:", _re.I),
    _re.compile(r"^Submitted on\s+\d", _re.I),
    _re.compile(r"^https?://hal\.", _re.I),
    # Anarchist Library — URL et boilerplate
    _re.compile(r"^https?://theanarchistlibrary\.org/", _re.I),
    _re.compile(r"^Retrieved on\s+\d", _re.I),
    # Infokiosques.net — signature de bas/haut de page
    _re.compile(r"^infokiosques\.net\s*$", _re.I),
    _re.compile(r"^https?://infokiosques\.net/\s*$", _re.I),
    # Mentions de copyright/tous droits réservés seules sur une ligne
    _re.compile(r"^(?:©|Copyright|All\s+rights\s+reserved|Tous\s+droits\s+réservés)\b",
                _re.I),
    # Ligne composée uniquement de séparateurs
    _re.compile(r"^[\s\-_=*·•]{5,}$"),
]

# Blocs multi-lignes à supprimer (regex sur le texte de la page complet)
_NOISE_BLOCKS = [
    # Banque mondiale — bloc "Public Disclosure Authorized" (apparaît 4 fois)
    _re.compile(
        r"(?:Public\s+Disclosure\s+Authorized\s*){2,}",
        _re.I,
    ),
    # Anarchist Library — ligne "Document accessible à URL"
    _re.compile(r"Document accessible à https?://\S+\s*", _re.I),
]


def _denoise_page(text: str, doc_title: str = "") -> str:
    """Retire les lignes/blocs parasites d'un texte de page PDF.

    Applique dans l'ordre :
      1. Blocs multi-lignes connus (World Bank, Anarchist Library…)
      2. Bloc d'en-tête structuré : si les N premières lignes non-vides
         ressemblent à (titre, sous-titre, auteur, date), on les saute
         pour démarrer à la première phrase complète (≥ 6 mots).
      3. Ligne par ligne : patterns connus + lignes répétant le titre.

    Ne touche pas au contenu substantiel.
    """
    # 1. Blocs multi-lignes
    for pat in _NOISE_BLOCKS:
        text = pat.sub(" ", text)

    # Préparer les formes normalisées du titre (et ses composantes)
    title_parts = set()
    if doc_title:
        # Titre complet
        title_parts.add(doc_title.strip().lower())
        # Composantes séparées par "—", "–", ":", "/"
        for sep in ("—", "–", ":", "/"):
            for part in doc_title.split(sep):
                p = part.strip().lower()
                if len(p) > 8:
                    title_parts.add(p)

    # 2. Détection du bloc d'en-tête structuré en début de page
    #    (titre + sous-titre + auteur + date — typique de l'Anarchist Library)
    _DATE_RE = _re.compile(
        r"^(?:January|February|March|April|May|June|July|August|September"
        r"|October|November|December|janvier|février|mars|avril|mai|juin"
        r"|juillet|août|septembre|octobre|novembre|décembre)"
        r"\s+\d{1,2},?\s+\d{4}$",
        _re.I,
    )
    lines = text.split("\n")
    non_empty = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip()]

    # Chercher où le vrai contenu commence : première ligne de ≥ 7 mots
    # après un bloc initial de ≤ 6 lignes courtes
    header_end = 0
    if len(non_empty) > 2:
        candidate_header = non_empty[:6]
        for idx, (orig_i, stripped) in enumerate(candidate_header):
            word_count = len(stripped.split())
            is_short = len(stripped) < 80
            is_date = bool(_DATE_RE.match(stripped))
            is_title_part = stripped.lower() in title_parts
            is_url = bool(_re.search(r"https?://", stripped))
            is_header_line = (is_short and
                              (is_date or is_title_part or is_url
                               or word_count <= 6))
            if is_header_line:
                header_end = orig_i + 1  # sauter jusqu'ici
            else:
                break  # premier non-header → on arrête

    # 3. Ligne à ligne : filtrage des patterns connus
    clean = []
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Dans le bloc d'en-tête → sauter
        if i < header_end and stripped:
            continue

        if not stripped:
            clean.append(line)
            continue

        # Pattern connu
        if any(pat.match(stripped) for pat in _NOISE_LINE_PATTERNS):
            continue

        # Répétition d'une composante du titre (ligne courte)
        if title_parts and len(stripped) < 80:
            if stripped.lower() in title_parts:
                continue

        clean.append(line)

    result = "\n".join(clean)
    result = _re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def extract_text(path: Path, max_chars: int = 12000,
                 doc_title: str = "", skip_cover: bool = True) -> str:
    """Extrait le texte d'un PDF, filtré et prêt pour l'enrichissement.

    Nouveautés vs la version initiale :
      - `skip_cover=True` : si la page 1 ressemble à une page de couverture
        (< 3 lignes substantielles, < 120 chars réels), elle est omise.
        L'extraction commence à la page 2.
      - `doc_title` : si fourni, les lignes qui répètent exactement le titre
        sont supprimées (boilerplate Anarchist Library, Archive.org…).
      - `_denoise_page()` : retire les lignes parasites connues par source.

    Retourne une chaîne tronquée à max_chars, avec marqueurs [p.N].
    """
    if not PYMUPDF_AVAILABLE:
        return ""
    try:
        doc = fitz.open(path)
        chunks = []
        running = 0
        for page in doc:
            page_num = page.number + 1
            txt = page.get_text("text") or ""

            # Ignorer la page de couverture (page 1 sans contenu réel)
            if skip_cover and page_num == 1 and _is_cover_page(txt):
                continue

            # Débruitage ligne par ligne
            txt = _denoise_page(txt, doc_title=doc_title)

            if not txt.strip():
                continue

            chunks.append(f"[p.{page_num}]\n{txt}")
            running += len(txt)
            if running >= max_chars:
                break
        doc.close()

        # Si skip_cover a sauté la page 1 et qu'il n'y a rien d'autre,
        # recommencer sans skip (doc très court / page 1 = tout le contenu)
        if not chunks and skip_cover:
            return extract_text(path, max_chars=max_chars,
                                doc_title=doc_title, skip_cover=False)

        full = "\n\n".join(chunks)
        return full[:max_chars]
    except Exception as e:
        print(f"  ⚠  extract_text failed for {path.name}: {e}")
        return ""


def extract_cover(path: Path, out_png: Path,
                   max_width: int = 400) -> bool:
    """Sauve la page 1 du PDF comme PNG (largeur max=max_width)."""
    if not PYMUPDF_AVAILABLE:
        return False
    try:
        doc = fitz.open(path)
        if doc.page_count == 0:
            doc.close()
            return False
        page = doc.load_page(0)
        # Calculer le zoom pour atteindre max_width
        rect = page.rect
        zoom = max_width / rect.width if rect.width > 0 else 1.0
        zoom = min(zoom, 2.0)  # cap à 2x pour éviter PNG énormes
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_png))
        doc.close()
        return out_png.exists()
    except Exception as e:
        print(f"  ⚠  extract_cover failed for {path.name}: {e}")
        return False


def extract_metadata(path: Path) -> dict:
    """Métadonnées + nb de pages + premiers mots."""
    if not PYMUPDF_AVAILABLE:
        return {}
    try:
        doc  = fitz.open(path)
        meta = dict(doc.metadata or {})
        meta["page_count"] = doc.page_count
        if doc.page_count > 0:
            first_text = doc.load_page(0).get_text("text") or ""
            meta["first_words"] = first_text.strip()[:300]
        doc.close()
        return meta
    except Exception as e:
        print(f"  ⚠  extract_metadata failed for {path.name}: {e}")
        return {}


def quick_check(path: Path) -> dict:
    """Diagnostic rapide d'un fichier : valid? size? pages? quel content?"""
    if not path.exists():
        return {"exists": False}
    info = {
        "exists": True,
        "size":   path.stat().st_size,
        "valid_pdf": validate_pdf(path),
    }
    if info["valid_pdf"] and PYMUPDF_AVAILABLE:
        info.update(extract_metadata(path))
    elif not info["valid_pdf"]:
        with open(path, "rb") as f:
            head = f.read(200)
        info["head_preview"] = head.decode("utf-8", errors="replace")[:150]
    return info


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage : pdf_processor.py <path>")
        sys.exit(1)
    path = Path(sys.argv[1])
    print(json.dumps(quick_check(path), ensure_ascii=False, indent=2))
