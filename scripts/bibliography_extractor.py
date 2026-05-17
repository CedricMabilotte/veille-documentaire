#!/usr/bin/env python3
"""
bibliography_extractor.py — Extraction best-effort de références bibliographiques.

Stratégie :
1. Lire le PDF avec PyMuPDF, page par page.
2. Localiser la dernière section ressemblant à une bibliographie :
   - soit par un header explicite ("Bibliographie", "Références", "References",
     "Cited Works", "Sources", "Œuvres citées", "Ouvrages cités"…)
   - soit par la densité de patterns "Nom, X. (YYYY)" sur les dernières pages.
3. Découper en entrées (paragraphes ou lignes) puis parser chaque entrée :
   - auteur (premier nom de famille rencontré),
   - année (premier groupe de 4 chiffres 1500-2099),
   - titre (segment entre l'année et le premier point fort/in/dans).
4. Renvoyer une liste de dicts (max_refs).

Pure Python + PyMuPDF, aucune nouvelle dépendance.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
    _PYMUPDF_OK = True
except ImportError:
    _PYMUPDF_OK = False

# ── Constantes de détection ───────────────────────────────────────────────────

# Headers de section bibliographique (FR / EN / ES, insensible à la casse)
_BIB_HEADERS = re.compile(
    r"^\s*(?:"
    r"bibliographie|r[ée]f[ée]rences(?:\s+bibliographiques)?|"
    r"references|cited\s+works|works\s+cited|sources?|"
    r"[œo]uvres?\s+cit[ée]es?|ouvrages?\s+cit[ée]s?|"
    r"bibliograf[ií]a|referencias|obras\s+citadas"
    r")\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Patterns typiques d'entrée bibliographique
# Ex : "Ostrom, E. (1990).", "Bourdieu P., 1979,", "Marx, K. (1867)."
_REF_PATTERN = re.compile(
    r"([A-ZÉÈÊÀÂÎÔÛÇ][A-Za-zÀ-ÿ'\-]+(?:\s+[A-ZÉÈÊÀÂÎÔÛÇ]\.?){0,3})"  # Nom + initiales
    r"[\s,]+\(?(\b1[5-9]\d{2}|20\d{2})\b\)?"                            # Année 1500-2099
)

# Année seule pour heuristique de densité
_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")

# Séparateurs probables entre entrées (ligne avec puce, retour double, etc.)
_ENTRY_SPLIT = re.compile(r"\n\s*\n|\n(?=[A-ZÉÈÊÀÂÎÔÛÇ][a-zà-ÿ]+,?\s+[A-Z])")


def _extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Retourne [(num_page_1based, texte), ...]."""
    if not _PYMUPDF_OK:
        return []
    pages: list[tuple[int, str]] = []
    try:
        doc = fitz.open(pdf_path)
        for p in doc:
            pages.append((p.number + 1, p.get_text("text") or ""))
        doc.close()
    except Exception as e:
        print(f"  ! extract_pages failed: {e}")
    return pages


def _locate_bibliography(pages: list[tuple[int, str]]) -> tuple[int, str] | None:
    """Trouve la page où débute la bibliographie ; retourne (page, texte_concatene).

    Priorité 1 : dernier match d'un header explicite.
    Priorité 2 : page du tiers final avec densité d'années élevée (>= 5 années).
    """
    if not pages:
        return None

    # 1) Header explicite — on prend le DERNIER (les vraies biblio sont à la fin)
    last_hit: tuple[int, int] | None = None  # (page_idx, char_offset)
    for idx, (_, txt) in enumerate(pages):
        for m in _BIB_HEADERS.finditer(txt):
            last_hit = (idx, m.end())
    if last_hit is not None:
        idx, offset = last_hit
        # Texte = reste de la page courante + pages suivantes
        chunks = [pages[idx][1][offset:]]
        chunks.extend(p[1] for p in pages[idx + 1:])
        return pages[idx][0], "\n".join(chunks)

    # 2) Heuristique densité : on cherche dans le dernier tiers la page avec
    #    le plus d'années détectées, à condition d'avoir au moins 5 années.
    start = max(0, int(len(pages) * 2 / 3))
    best_idx, best_count = -1, 0
    for idx in range(start, len(pages)):
        cnt = len(_YEAR_RE.findall(pages[idx][1]))
        if cnt > best_count:
            best_idx, best_count = idx, cnt
    if best_idx >= 0 and best_count >= 5:
        chunks = [pages[i][1] for i in range(best_idx, len(pages))]
        return pages[best_idx][0], "\n".join(chunks)

    return None


def _parse_entry(raw: str, page: int) -> dict | None:
    """Parse une entrée brute en {raw, author, year, title, page}."""
    raw = re.sub(r"\s+", " ", raw).strip(" .;,-—–\n\t")
    if len(raw) < 15:  # trop court pour être une ref crédible
        return None

    m = _REF_PATTERN.search(raw)
    if not m:
        # Pas de pattern Nom+Année → on garde quand même si elle contient une année
        ym = _YEAR_RE.search(raw)
        if not ym:
            return None
        return {"raw": raw[:300], "author": None,
                "year": int(ym.group(1)), "title": None, "page": page}

    author = m.group(1).strip(" ,.")
    year = int(m.group(2))
    # Titre : segment entre l'année et le prochain point/in/dans (best-effort)
    after = raw[m.end():].lstrip(" .,):")
    title_match = re.split(r"(?:\.|,)\s+(?:[Ii]n\s|[Dd]ans\s|[Ee]d[s]?\.|[Vv]ol\.)|"
                           r"\.\s+[A-ZÉÈ]", after, maxsplit=1)
    title = (title_match[0] if title_match else after)[:200].strip(" .,")
    return {"raw": raw[:400], "author": author, "year": year,
            "title": title or None, "page": page}


def extract_references(pdf_path: Path, max_refs: int = 50) -> list[dict]:
    """API publique : retourne la liste des références extraites.

    Best-effort : si aucune biblio détectée, retourne [].
    """
    if not _PYMUPDF_OK:
        print("  ! PyMuPDF indisponible, extraction impossible")
        return []
    if not pdf_path.exists():
        return []

    pages = _extract_pages(pdf_path)
    located = _locate_bibliography(pages)
    if not located:
        return []
    start_page, bib_text = located

    # Découpe en entrées
    raw_entries = _ENTRY_SPLIT.split(bib_text)
    # Filtre : on garde celles contenant une année (signe fort d'une vraie ref)
    refs: list[dict] = []
    for entry in raw_entries:
        if not _YEAR_RE.search(entry):
            continue
        parsed = _parse_entry(entry, start_page)
        if parsed:
            refs.append(parsed)
        if len(refs) >= max_refs:
            break
    return refs


# ── Validation CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    docs_dir = Path(__file__).parent.parent / "docs"
    pdfs = sorted(docs_dir.glob("*.pdf"))
    if len(sys.argv) > 1:
        pdfs = [Path(sys.argv[1])]
    elif not pdfs:
        print("Aucun PDF dans docs/. Usage: bibliography_extractor.py <pdf>")
        sys.exit(0)

    # On teste sur les 3 plus gros (plus de chances d'avoir une biblio)
    pdfs_sorted = sorted(pdfs, key=lambda p: p.stat().st_size, reverse=True)[:3]
    for pdf in pdfs_sorted:
        print(f"\n=== {pdf.name} ({pdf.stat().st_size // 1024} Ko) ===")
        refs = extract_references(pdf, max_refs=20)
        print(f"  → {len(refs)} référence(s) détectée(s)")
        for r in refs[:5]:
            auth = r.get("author") or "?"
            yr = r.get("year") or "?"
            title = (r.get("title") or "")[:80]
            print(f"    [{r['page']}] {auth} ({yr}) — {title}")
