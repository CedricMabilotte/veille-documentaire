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
  3. Détection de langue heuristique sur le texte extrait (≥80 chars, ≥30 mots).
  4. Détection légère sur titre/filename/URL via mots-clés caractéristiques.
  5. Héritage du `default_lang` configuré sur la source dans sources.yml.
  6. Regex sur l'URL / le nom de fichier (dernier recours pour la date).

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
# Plages biographiques ou historiques du type « 1884-1951 » ou « 1929-1936 » :
# deux années séparées par un tiret. On les masque avant l'extraction heuristique
# pour ne pas capter des années de naissance, de décès ou de période couverte.
_YEAR_RANGE_RE = re.compile(r"\b1[5-9]\d{2}-(?:1[5-9]|20)\d{2}\b")

# Bornes de plausibilité pour une date de publication :
#
#   _PUB_YEAR_MIN_STRICT (1950) — utilisé pour les sources heuristiques
#     (filename, URL, context, link_text).  Ces chaînes contiennent souvent des
#     années qui ne sont pas des dates de publication : années biographiques dans
#     les métadonnées Archive.org (ex. « Borodin, 1884-1951 »), plages d'événements
#     historiques dans les noms de fichiers (ex. « australie_1929-1936 »).
#     Préférer une date vide plutôt qu'une date d'événement ou de naissance.
#
#   _PUB_YEAR_MIN_LOOSE (1800) — utilisé pour les métadonnées explicites
#     (src_meta, PDF creationDate) qui sont des sources autoritatives.
#
#   _PUB_YEAR_MAX — commun : date future trop lointaine → suspecte.
import datetime as _dt
_PUB_YEAR_MIN_STRICT = 1950   # seuil heuristiques (filename/URL/context)
_PUB_YEAR_MIN_LOOSE  = 1800   # seuil sources autoritatives (src_meta, PDF)
_PUB_YEAR_MAX = _dt.date.today().year + 2


def _is_plausible_pub_year(year_str: str, strict: bool = False) -> bool:
    """Retourne True si l'année est dans les bornes de publication plausibles.

    strict=True  → utilise _PUB_YEAR_MIN_STRICT (heuristiques sur filename/URL/context).
    strict=False → utilise _PUB_YEAR_MIN_LOOSE  (métadonnées explicites).
    """
    try:
        y = int(year_str)
        floor = _PUB_YEAR_MIN_STRICT if strict else _PUB_YEAR_MIN_LOOSE
        return floor <= y <= _PUB_YEAR_MAX
    except (ValueError, TypeError):
        return False
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


# Mots-clés caractéristiques par langue pour détecter sur titre/filename/URL
# (termes fréquents dans les noms de fichiers militants/académiques)
_LANG_TITLE_HINTS: dict[str, list[str]] = {
    "fr": [
        "les", "des", "une", "pour", "dans", "avec", "contre",
        "mouvement", "luttes", "communs", "terres", "paysannerie", "foncier",
        "paysan", "territoire", "commun", "propriété", "liberté", "espace",
        "rencontres", "cahier", "brochure", "texte", "rapport", "recueil",
        "histoire", "pratique", "manuel",
        "anticapitalisme", "ecologie", "squat", "anticolonialisme",
        "quelques", "vers", "après", "entre",
    ],
    "en": [
        "the", "and", "for", "land", "commons", "common", "peasant",
        "struggle", "movement", "rights", "agrarian", "enclosure", "trust",
        "cooperative", "community", "liberation", "freedom",
        "history", "practice", "toward", "against",
        "anarchism", "sabotage", "power", "state", "capital", "labor",
        "solidarity", "autonomy", "resistance",
    ],
    "es": [
        "los", "las", "una", "para", "con", "del", "por", "tierra",
        "campesino", "campesina", "movimiento", "reforma", "agraria",
        "comunes", "derechos", "lucha", "libertad", "autonomia", "resistencia",
        "jovenes", "acciones", "publicaciones", "libros", "manual",
        "zapatista", "sindicato", "trabajadores", "pueblos",
    ],
    "pt": [
        "dos", "das", "para", "com", "uma", "terra", "trabalhadores",
        "movimento", "agraria", "reforma", "camponeses", "questao",
        "biblioteca", "desenvolvimento", "desigualdade", "direitos",
        "sem-terra", "luta", "brasil",
    ],
    "de": [
        "der", "die", "und", "den", "das", "für", "eine", "boden",
        "gemeinsam", "bewegung", "kapital", "arbeit", "freiheit",
        "programm", "bericht", "handbuch", "einführung", "fehlende",
        "barrierefrei", "eigenmittel", "veröffentlichung",
    ],
}


def detect_lang_hints(text: str) -> str:
    """Détection légère sur un texte court (titre, filename, URL).
    Retourne la langue la plus probable parmi fr/en/es/pt/de, ou '' si
    le signal est insuffisant (score < 2 ou ambiguïté entre deux langues).
    """
    if not text:
        return ""
    # Normaliser : remplacer tirets/underscores/points par espaces
    normalized = re.sub(r"[-_./%+]", " ", text.lower())
    words = re.findall(r"[a-zà-öø-ÿ]{3,}", normalized)
    if not words:
        return ""
    scores: dict[str, int] = {}
    distinct_matches: dict[str, set] = {}
    for lang, hints in _LANG_TITLE_HINTS.items():
        hint_set = set(hints)
        matched = {w for w in words if w in hint_set}
        scores[lang] = sum(1 for w in words if w in hint_set)
        distinct_matches[lang] = matched
    best = max(scores, key=scores.get)
    second = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
    # Signal trop faible : exiger au moins 2 mots distincts matchés
    if len(distinct_matches[best]) < 2:
        return ""
    # Ambiguïté forte entre deux langues : ne pas trancher
    if second >= scores[best]:
        return ""
    return best


def extract_doc_date(*sources: str) -> str:
    """Cherche une date de publication (ISO si possible, sinon année) dans
    les chaînes heuristiques fournies (link_text, context, filename, URL),
    par ordre de priorité.

    Garde-fous appliqués sur les sources heuristiques :
    1. Les plages biographiques/historiques « NNNN-NNNN » (ex. « 1884-1951 »,
       « 1929-1936 ») sont masquées avant la recherche : les deux années d'une
       telle plage ne sont pas des dates de publication.
    2. Les années antérieures à 1950 sont rejetées (seuil strict) : les filenames
       et URLs encodant des événements historiques (ex. « barcelone-1931 ») ne
       doivent pas être pris pour des dates de publication.
    Préférer une date vide à une date fausse — c'est le fallback de dernier
    recours ; les sources autoritatives (src_meta, PDF) passent par build_metadata.
    """
    def _strip_ranges(s: str) -> str:
        """Masque les plages NNNN-NNNN pour ne pas capter les années isolées."""
        return _YEAR_RANGE_RE.sub("XXXX-XXXX", s)

    for s in sources:
        if not s:
            continue
        s = _strip_ranges(str(s))
        m = _ISODATE_RE.search(s)
        if m and _is_plausible_pub_year(m.group(1), strict=True):
            return m.group(0)
    for s in sources:
        if not s:
            continue
        # Chercher toutes les années candidates dans la chaîne et retourner
        # la première qui passe le filtre strict (≥ 1950).
        for m in _YEAR_RE.finditer(_strip_ranges(str(s))):
            if _is_plausible_pub_year(m.group(0), strict=True):
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
        for m in _ISBN_RE.finditer(str(t)):
            isbn = re.sub(r"[-\s]", "", m.group(0)).upper()
            if _isbn_checksum_ok(isbn):  # audit 17/09 : 24/44 ISBN étaient des nombres quelconques
                return isbn
    return ""


def _isbn_checksum_ok(isbn: str) -> bool:
    if len(isbn) == 10 and isbn[:9].isdigit() and (isbn[9].isdigit() or isbn[9] == "X"):
        s = sum((10 - k) * int(c) for k, c in enumerate(isbn[:9])) + (10 if isbn[9] == "X" else int(isbn[9]))
        return s % 11 == 0
    if len(isbn) == 13 and isbn.isdigit():
        return sum(int(c) * (1 if k % 2 == 0 else 3) for k, c in enumerate(isbn)) % 10 == 0
    return False


def find_hal_id(*texts: str) -> str:
    for t in texts:
        if not t:
            continue
        m = _HALID_RE.search(str(t))
        if m:
            return m.group(0).lower()
    return ""


# ── Normalisation des titres ──────────────────────────────────────────────────

# Expressions de format à supprimer des titres (suffixes ou parenthétiques).
# Ordre : du plus long au plus court pour éviter les sous-matches.
_FORMAT_SUFFIXES = re.compile(
    r"\s*\(\s*(?:"
    r"PDF|pdf"
    r"|page\s+par\s+page|pageparpage"
    r"|cahier"
    r"|à\s+lire(?:\s+sur\s+(?:l[''’])?écran)?|to[\s_]read"
    r"|à\s+imprimer|to[\s_]print"
    r"|livret\s+A[3456]?|brochure|booklet"
    r"|[0-9]+\s*pages?\s*A[3-6]|[0-9]+\s*p\s*A[3-6]|[0-9]+\s*p\b"
    r"|version\s+(?:légère|light|recto-verso)"
    r"|fil\b|NB\b|noir[\s-]et[\s-]blanc"
    r"|x[0-9]+\s*A[3-6]"
    r"|recto[- ]verso|double[\s-]face"
    r")\s*\)\s*$",
    re.I,
)
# Préfixe « · » ou «·» (puce infokiosques)
_BULLET_PREFIX = re.compile(r"^[·•]\s*")
# Tiret simple ASCII entouré d'espaces → tiret demi-cadratin
_ASCII_DASH = re.compile(r"\s+-\s+")
# Colon sans espace avant (typographie française)
_BARE_COLON = re.compile(r"(\S):\s")
# Parenthétique auteur en fin de titre : « (Prénom Nom) »
_AUTHOR_PARENS = re.compile(
    r"\s*\(([A-ZÀÂÉÈÊÎÔÙÛ][a-zàâéèêîôùûäëïü]+"
    r"(?:\s+[A-ZÀÂÉÈÊÎÔÙÛ][a-zàâéèêîôùûäëïü]+)+)\)\s*$"
)
# pdf_title "empoisonné" — vient d'une app, d'un convertisseur ou est
# un nom de fichier sans valeur éditoriale.
_POISONED_PDF_TITLE = re.compile(
    r"(?:Microsoft\s+Word|Untitled|OpenOffice|LibreOffice"
    r"|InDesign|\.(pmd|qxd|odt|doc|indd|docx)\b"
    r"|\b[0-9]+p\s*A[3-6]\b|\b8pp\b|\bA[3456]\b"
    r"|World\s+Bank\s+Document|Public\s+Disclosure"
    r"|Working\s+Paper\b|Technical\s+(?:Note|Report)\b"
    r"|Thematic\s+(?:Note|Guidance)\s+Note"
    r"|Discussion\s+Paper\b|Policy\s+Brief\b)",
    re.I,
)
# Parenthétique de format (sans auteur) à nettoyer en fin de titre
_FORMAT_PARENS = re.compile(
    r"\s*\(\s*(?:version\s+(?:page\s+par\s+page|légère|light|cahier)"
    r"|[0-9]+\s*p|A[3456]|\d+\s*pages?)\s*\)\s*$",
    re.I,
)


def normalize_title(
    link_text: str = "",
    pdf_title: str = "",
    filename: str = "",
    author_hint: str = "",
) -> str:
    """Produit un titre éditorial propre depuis les sources brutes disponibles.

    Ordre de préférence :
      1. pdf_title — si non empoisonné (pas un nom d'app, pas un nom de fichier)
      2. link_text — texte du lien sur la page source
      3. filename  — fallback : nom de fichier humanisé

    Nettoyages appliqués (tous les cas) :
      - Préfixe « · » retiré
      - Suffixe « (PDF) » et parenthétiques de format retirés
      - Tiret ASCII ` - ` → tiret demi-cadratin ` — `
      - Colon non précédé d'espace → espace inséré (typographie française)
      - Parenthétique auteur retiré si l'auteur est déjà fourni
      - Série Mini-Manuel : normalisation `Mini-Manuel : Titre`
    """
    # Détecter si le link_text indique une série Mini-Manuel (lien générique)
    _is_mini_manuel_series = bool(
        re.search(r"mini[-\s]manuel", link_text, re.I)
        and not re.search(r"mini[-\s]manuel.{3,}", link_text, re.I)
    )

    # Choisir la source la moins bruitée
    raw = ""
    if pdf_title and not _POISONED_PDF_TITLE.search(pdf_title):
        raw = pdf_title
    elif link_text and not re.match(r"^mini[-\s]manuel\s*$", link_text.strip(), re.I):
        # link_text = "mini-manuel" seul est trop générique ; on passe au pdf_title
        raw = link_text
    elif pdf_title and not _POISONED_PDF_TITLE.search(pdf_title):
        # Deuxième chance : pdf_title (même si on a préféré l'ignorer pour link_text)
        raw = pdf_title

    if not raw and filename:
        # Humaniser le filename en dernier recours
        raw = re.sub(r"\.[a-z0-9]+$", "", filename, flags=re.I)
        raw = raw.replace("_", " ").replace("-", " ")

    if not raw:
        return ""

    t = raw.strip()

    # Rejeter le résultat si c'est entièrement un code de format (ex: "8pp A5")
    _FORMAT_ONLY = re.compile(
        r"^(?:[0-9]+\s*(?:p|pp|pages?)\s*A[3-6]?|[0-9]+\s*pp?\b|A[3-6]\b"
        r"|\bNB\b|fil\b|cahier\b|booklet\b)\s*$",
        re.I,
    )
    if _FORMAT_ONLY.match(t):
        # Repli sur le filename humanisé
        if filename:
            raw = re.sub(r"\.[a-z0-9]+$", "", filename, flags=re.I)
            t = raw.replace("_", " ").replace("-", " ").strip()
        if not t or _FORMAT_ONLY.match(t):
            return ""   # impossible de produire un titre propre

    # 1. Préfixe puce
    t = _BULLET_PREFIX.sub("", t)

    # 2. Suffixes de format en fin de titre  « (PDF) », « (page par page) »…
    for _ in range(3):          # passer plusieurs fois pour les doubles parenthèses
        t = _FORMAT_SUFFIXES.sub("", t)
        t = _FORMAT_PARENS.sub("", t)
    t = t.strip()

    # 3. Suffixe « (PDF) » nu non couvert par le regex ci-dessus
    t = re.sub(r"\s*\(PDF\)\s*$", "", t, flags=re.I).strip()

    # 3b. Suffixes de format NON parenthétiques en fin de titre :
    #     "Titre 16 pages A5" → "Titre" ; "Titre NB" → "Titre"
    t = re.sub(
        r"\s+(?:[0-9]+\s*pages?\s*A[3-6]|[0-9]+\s*pp?\s*A[3-6]"
        r"|[0-9]+\s*pp?\b(?!\s*[A-Za-z])"
        r"|\bNB\b|\bfil\b)\s*$",
        "", t, flags=re.I,
    ).strip()

    # 3c. Dans les parenthèses mixtes "(version X, format)" retirer la partie
    #     format (après virgule) tout en conservant la partie éditoriale :
    #     "(version italienne, à imprimer)" → "(version italienne)"
    def _clean_mixed_parens(m: re.Match) -> str:
        content = m.group(1)
        # Retirer les sous-segments de format après une virgule
        parts = [p.strip() for p in content.split(",")]
        _fmt_re = re.compile(
            r"^(?:à\s+(?:lire|imprimer)|to\s+(?:read|print)|page\s+par\s+page"
            r"|cahier|[0-9]+\s*p|NB|fil|booklet|sur\s+(?:l')?écran)\b",
            re.I,
        )
        kept = [p for p in parts if not _fmt_re.match(p)]
        if not kept:
            return ""   # tout était du format → supprimer toute la parenthèse
        return f"({', '.join(kept)})"

    t = re.sub(r"\(([^)]+)\)", _clean_mixed_parens, t)

    # 4. Tiret ASCII → demi-cadratin
    t = _ASCII_DASH.sub(" — ", t)

    # 5. Colon sans espace avant (FR)
    t = _BARE_COLON.sub(r"\1 : ", t)

    # 6. Auteur entre parenthèses en fin → retire si hint fourni
    if author_hint:
        t = _AUTHOR_PARENS.sub("", t).strip()

    # 7. Série Mini-Manuel : normaliser « Mini-Manuel X » → « Mini-Manuel : X »
    #    et s'assurer que ce qui suit est en majuscule.
    #    Cas spécial : si le link_text était "mini-manuel" (lien générique) et
    #    que le titre vient du pdf_title "Manuel X", préfixer "Mini-Manuel :".
    m = re.match(r"^(Mini[-\s]Manuel)\s*[:\-]?\s*(.+)$", t, re.I)
    if m:
        rest = m.group(2).strip()
        rest = rest[0].upper() + rest[1:] if rest else rest
        t = f"Mini-Manuel : {rest}"
    elif _is_mini_manuel_series and re.match(r"^Manuel\s+", t, re.I):
        # pdf_title "Manuel X" → "Mini-Manuel : X"
        rest = re.sub(r"^Manuel\s+", "", t, flags=re.I).strip()
        rest = rest[0].upper() + rest[1:] if rest else rest
        t = f"Mini-Manuel : {rest}"

    # 8. Nettoyage final
    t = re.sub(r"\s{2,}", " ", t).strip()
    # Retirer les points de suspension orphelins en fin
    t = re.sub(r"\s*\.\.\.\s*$", "", t).strip()

    return t


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
                   pdf_text: str = "",
                   source_default_lang: str = "") -> dict:
    """Agrège toutes les métadonnées fiables d'un document.

    `doc`                : le dict du parser (url, filename, link_text, context,
                           éventuellement `src_meta` injecté par le parser).
    `pdf_meta`           : sortie de pdf_processor.extract_metadata (optionnel).
    `pdf_text`           : texte extrait du PDF (optionnel, pour la langue/ids).
    `source_default_lang`: langue par défaut de la source (sources.yml), utilisée
                           en dernier recours si aucune détection n'aboutit.

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
    # Normaliser : si on a une date complète, la garder ; sinon juste l'année.
    # Garde-fou final (seuil loose ≥ 1800) : rejeter les années hors bornes.
    # Les sources autoritatives (src_meta, PDF) peuvent légitimement donner une
    # date antérieure à 1950 pour un document historique ; on n'applique donc pas
    # le seuil strict ici. L'extraction heuristique (extract_doc_date) a déjà
    # appliqué le filtre strict en amont.
    norm_date = ""
    if doc_date:
        m_iso = _ISODATE_RE.search(str(doc_date))
        if m_iso and _is_plausible_pub_year(m_iso.group(1), strict=False):
            norm_date = m_iso.group(0)
        else:
            m_y = _YEAR_RE.search(str(doc_date))
            if m_y and _is_plausible_pub_year(m_y.group(0), strict=False):
                norm_date = m_y.group(0)

    # ── lang : 4 niveaux de fiabilité décroissante ───────────────────────────
    # 1. Métadonnées explicites de la source (HAL language_s, OPDS, src_meta)
    lang = str(src_meta.get("lang") or src_meta.get("language") or "").lower()[:2]
    if lang not in ("fr", "en", "es", "pt", "de"):
        # 2. Détection sur le texte extrait du PDF (≥80 chars, ≥30 mots)
        lang = detect_lang(pdf_text) if pdf_text else ""
    if not lang:
        # 3. Détection légère sur titre/filename/URL (mots-clés caractéristiques)
        hint_sources = " ".join(filter(None, [link_text, filename, url]))
        lang = detect_lang_hints(hint_sources)
    if not lang:
        # 4. Héritage du default_lang configuré sur la source dans sources.yml
        if source_default_lang in ("fr", "en", "es", "pt", "de"):
            lang = source_default_lang

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
