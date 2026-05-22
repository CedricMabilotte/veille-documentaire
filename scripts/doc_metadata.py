#!/usr/bin/env python3
"""
doc_metadata.py — Extraction de métadonnées bibliographiques fiables (item S2).

Distingue :
  - doc_date  : date de publication du document (≠ date de collecte)
  - lang      : langue du document (fr/en/es/pt/de)
  - editeur   : éditeur / organisation publiant le document
  - doi/isbn/hal_id : identifiants pérennes (item B8)

Stratégie de remplissage, par ordre de fiabilité :
  1. Métadonnées explicites de la source (HAL JSON, Archive.org JSON, OPDS,
     pubDate RSS) — fournies par les parsers via doc["src_meta"].
  2. Métadonnées intrinsèques du PDF (PyMuPDF : creationDate, author…).
  3. Détection de langue heuristique sur le texte extrait.
  4. Regex sur l'URL / le nom de fichier (dernier recours pour la date).

RÈGLE D'OR : ne JAMAIS inventer un auteur. Si la source ne donne pas
d'auteur, le champ reste vide (anonymat respecté — items B10/C9).

Pur Python (re). PyMuPDF optionnel.
"""

from __future__ import annotations

import re

# ── Détection de langue : mots-outils très fréquents par langue ──────────────
_LANG_STOPWORDS = {
    "fr": {"le", "la", "les", "des", "une", "dans", "pour", "que", "qui",
           "avec", "sur", "est", "pas", "plus", "cette", "nous", "comme",
           "aux", "par", "ont", "sont", "leur", "mais"},
    "en": {"the", "and", "for", "that", "with", "this", "from", "are",
           "was", "have", "not", "they", "their", "which", "been", "more",
           "would", "about", "there", "these"},
    "es": {"que", "los", "las", "una", "para", "con", "del", "por", "como",
           "más", "pero", "este", "esta", "son", "han", "sus", "muy",
           "también", "entre", "sobre"},
    "pt": {"que", "uma", "para", "com", "dos", "das", "por", "como", "mais",
           "mas", "este", "esta", "são", "não", "seu", "sua", "também",
           "entre", "sobre", "pelo"},
    "de": {"der", "die", "und", "den", "das", "ist", "ein", "eine", "von",
           "mit", "auf", "für", "nicht", "auch", "werden", "sich", "dass",
           "wird", "sind", "einen"},
}

_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20[0-4]\d)\b")
_ISODATE_RE = re.compile(r"\b(1[5-9]\d{2}|20[0-4]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
_ISBN_RE = re.compile(r"\b97[89][-\s]?(?:\d[-\s]?){9}\d\b|\b(?:\d[-\s]?){9}[\dXx]\b")
_HALID_RE = re.compile(r"\b(?:hal|tel|halshs|hprints)-\d{6,}\b", re.IGNORECASE)


def detect_lang(text: str) -> str:
    """Devine la langue d'un texte parmi fr/en/es/pt/de. '' si indéterminé."""
    if not text or len(text) < 80:
        return ""
    words = re.findall(r"[a-zà-öø-ÿ]+", text.lower())
    if len(words) < 30:
        return ""
    sample = words[:600]
    scores: dict[str, int] = {}
    for lang, stop in _LANG_STOPWORDS.items():
        scores[lang] = sum(1 for w in sample if w in stop)
    best = max(scores, key=scores.get)
    # Seuil minimal : éviter de classer un texte trop court / bruité
    if scores[best] < 5:
        return ""
    return best


def extract_doc_date(*sources: str) -> str:
    """Cherche une date de publication (ISO si possible, sinon année) dans
    les chaînes fournies, par ordre de priorité."""
    for s in sources:
        if not s:
            continue
        s = str(s)
        m = _ISODATE_RE.search(s)
        if m:
            return m.group(0)
    for s in sources:
        if not s:
            continue
        m = _YEAR_RE.search(str(s))
        if m:
            return m.group(0)
    return ""


def find_doi(*texts: str) -> str:
    for t in texts:
        if not t:
            continue
        m = _DOI_RE.search(str(t))
        if m:
            return m.group(0).rstrip(".,;)")
    return ""


def find_isbn(*texts: str) -> str:
    for t in texts:
        if not t:
            continue
        m = _ISBN_RE.search(str(t))
        if m:
            return re.sub(r"[-\s]", "", m.group(0))
    return ""


def find_hal_id(*texts: str) -> str:
    for t in texts:
        if not t:
            continue
        m = _HALID_RE.search(str(t))
        if m:
            return m.group(0).lower()
    return ""


def _parse_pdf_date(raw: str) -> str:
    """Convertit une date PDF (D:20210315...) en année/ISO."""
    if not raw:
        return ""
    raw = raw.strip()
    m = re.search(r"(1[5-9]\d{2}|20[0-4]\d)(\d{2})?(\d{2})?", raw)
    if not m:
        return ""
    year, month, day = m.group(1), m.group(2), m.group(3)
    if month and day and "01" <= month <= "12" and "01" <= day <= "31":
        return f"{year}-{month}-{day}"
    return year


def build_metadata(doc: dict, pdf_meta: dict | None = None,
                   pdf_text: str = "") -> dict:
    """Agrège toutes les métadonnées fiables d'un document.

    `doc`      : le dict du parser (url, filename, link_text, context,
                 éventuellement `src_meta` injecté par le parser).
    `pdf_meta` : sortie de pdf_processor.extract_metadata (optionnel).
    `pdf_text` : texte extrait du PDF (optionnel, pour la langue/identifiants).

    Retourne un dict avec : doc_date, lang, editeur, doi, isbn, hal_id.
    Champs absents → chaîne vide. Aucun auteur n'est inféré ici.
    """
    pdf_meta = pdf_meta or {}
    src_meta = doc.get("src_meta") or {}

    url = doc.get("url", "") or ""
    filename = doc.get("filename", "") or ""
    context = doc.get("context", "") or ""
    link_text = doc.get("link_text", "") or ""

    # ── doc_date : priorité aux métadonnées de source ────────────────────────
    doc_date = (
        str(src_meta.get("date") or src_meta.get("pubdate") or src_meta.get("year") or "")
        or _parse_pdf_date(pdf_meta.get("creationDate", ""))
        or extract_doc_date(link_text, context, filename, url)
    )
    # Normaliser : si on a une date complète, la garder ; sinon juste l'année
    norm_date = ""
    if doc_date:
        m_iso = _ISODATE_RE.search(str(doc_date))
        if m_iso:
            norm_date = m_iso.group(0)
        else:
            m_y = _YEAR_RE.search(str(doc_date))
            norm_date = m_y.group(0) if m_y else ""

    # ── lang : source explicite, puis détection sur le texte ─────────────────
    lang = str(src_meta.get("lang") or src_meta.get("language") or "").lower()[:2]
    if lang not in ("fr", "en", "es", "pt", "de"):
        lang = detect_lang(pdf_text) if pdf_text else ""

    # ── editeur : source explicite ou métadonnées PDF ────────────────────────
    editeur = str(
        src_meta.get("publisher") or src_meta.get("editeur")
        or pdf_meta.get("producer") or ""
    ).strip()
    # Le "creator" du PDF est souvent un logiciel (Scribus, LaTeX…) : on l'écarte
    SOFTWARE_HINTS = ("scribus", "latex", "word", "openoffice", "libreoffice",
                      "indesign", "acrobat", "pdftex", "ghostscript", "quartz")
    if editeur and any(h in editeur.lower() for h in SOFTWARE_HINTS):
        editeur = ""

    # ── identifiants pérennes ────────────────────────────────────────────────
    haystack_all = " ".join([url, link_text, context, filename,
                             str(src_meta), pdf_text[:4000] if pdf_text else ""])
    doi = str(src_meta.get("doi") or "") or find_doi(haystack_all)
    isbn = str(src_meta.get("isbn") or "") or find_isbn(haystack_all)
    hal_id = str(src_meta.get("hal_id") or "") or find_hal_id(url, haystack_all)

    return {
        "doc_date": norm_date,
        "lang": lang,
        "editeur": editeur,
        "doi": doi,
        "isbn": isbn,
        "hal_id": hal_id,
    }


if __name__ == "__main__":
    # Tests rapides
    txt_fr = ("Le mouvement des paysans sans terre lutte pour la réforme "
              "agraire dans les campagnes. Cette terre que les communes ont "
              "abandonnée doit revenir à tous, comme un bien commun.")
    txt_en = ("The landless movement fights for agrarian reform in the "
              "countryside. This land that the commons have been given must "
              "return to all, as a common good which they share.")
    print("lang fr :", detect_lang(txt_fr))
    print("lang en :", detect_lang(txt_en))
    print("date    :", extract_doc_date("brochure_1905.pdf", "publié en 2021-03-15"))
    print("doi     :", find_doi("voir https://doi.org/10.1234/abcd.5678 pour"))
    print("isbn    :", find_isbn("ISBN 978-2-07-040850-4 édition"))
    print("hal_id  :", find_hal_id("https://hal.science/hal-01234567"))
    d = build_metadata(
        {"url": "https://hal.science/hal-01234567/document",
         "filename": "communs_2019.pdf", "link_text": "Les communs fonciers",
         "context": "Étude 2019", "src_meta": {"lang": "fr", "publisher": "CNRS"}},
        pdf_meta={"creationDate": "D:20190612000000"},
        pdf_text=txt_fr,
    )
    print("build   :", d)
    assert d["lang"] == "fr" and d["hal_id"] == "hal-01234567"
    print("OK")
