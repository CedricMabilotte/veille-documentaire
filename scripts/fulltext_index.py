#!/usr/bin/env python3
"""
fulltext_index.py — Index inversé full-text en pur Python.

Construit un index `terms → [doc_ids]` à partir de synopsis/catalog.json :
- pour chaque document on agrège : link_text, summary, citations.quote,
  matched_keywords, raison du dernier run, pdf_title/author/creator.
- normalisation : lowercase, déaccentuation légère, ponctuation retirée,
  stopwords FR/EN/ES filtrés, tokens < 3 caractères ignorés.

API :
    build_index(catalog_path, index_path) -> dict (stats)
    search(query, index_path, top_k)      -> list[dict]

Le scoring est simple : score = somme des occurrences (TF) des termes matchés,
pondéré par le nombre de termes trouvés (recall × TF cumulée).
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ── Stopwords FR / EN / ES (liste compacte, suffisante pour la veille) ────────
_STOPWORDS: set[str] = {
    # Articles, prépositions, conjonctions, pronoms FR
    "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux",
    "et", "ou", "ni", "mais", "donc", "car", "or", "que", "qui", "quoi",
    "dont", "ce", "cet", "cette", "ces", "il", "elle", "ils", "elles",
    "nous", "vous", "leur", "leurs", "son", "sa", "ses", "mon", "ma", "mes",
    "ton", "ta", "tes", "pour", "par", "sur", "sous", "dans", "avec", "sans",
    "vers", "chez", "pas", "ne", "plus", "moins", "tres", "tout", "tous",
    "toute", "toutes", "etre", "avoir", "fait", "faire", "ete", "est", "sont",
    "etait", "etaient", "sera", "serait", "comme", "aussi", "ainsi", "donc",
    # EN
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on",
    "at", "by", "for", "with", "from", "as", "is", "are", "was", "were",
    "be", "been", "being", "has", "have", "had", "do", "does", "did",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "our", "you", "your", "he", "his", "she", "her", "i", "me", "my",
    "not", "no", "so", "than", "then", "there", "here", "what", "which",
    "who", "whom", "whose", "how", "why", "when", "where", "all", "any",
    "some", "such", "also", "only", "more", "less", "very", "can", "could",
    "would", "should", "may", "might", "must", "will", "shall",
    # ES
    "el", "los", "las", "una", "unos", "unas", "y", "o", "pero", "que",
    "como", "para", "por", "con", "sin", "sobre", "entre", "hacia", "hasta",
    "desde", "es", "son", "esta", "estan", "ser", "estar", "fue", "fueron",
    "ha", "han", "su", "sus", "este", "esta", "estos", "estas", "ese", "esa",
    "eso", "esos", "esas", "lo", "le", "les", "se", "yo", "tu", "el", "ella",
    "nosotros", "vosotros", "ellos", "ellas", "muy", "mas", "todo", "todos",
    "toda", "todas", "no", "ni", "si", "tambien", "tampoco",
    # Trop génériques pour notre corpus
    "page", "pages", "pdf", "doc", "document", "documents", "titre", "ref",
}

# Regex de tokenisation : on extrait des séquences de lettres (avec accents)
_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ]{3,}")


def _normalize(text: str) -> list[str]:
    """Lowercase, déaccentuation, tokenisation, filtrage stopwords."""
    if not text:
        return []
    # Déaccentuation NFKD pour matcher "communs" et "Communs" et "commúns"
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    tokens = _TOKEN_RE.findall(no_accents.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _gather_doc_text(doc: dict) -> str:
    """Concatène tous les champs textuels pertinents d'un doc du catalog."""
    parts: list[str] = []
    parts.append(doc.get("filename") or "")
    parts.append(doc.get("url") or "")

    enrichment = doc.get("enrichment") or {}
    parts.append(enrichment.get("summary") or "")
    parts.append(enrichment.get("relevance_notes") or "")
    for cit in enrichment.get("citations") or []:
        if not isinstance(cit, dict):
            continue
        parts.append(cit.get("quote") or "")
        parts.append(cit.get("why_relevant") or "")
    parts.extend(enrichment.get("matched_keywords") or [])

    meta = doc.get("meta") or {}
    parts.append(meta.get("pdf_title") or "")
    parts.append(meta.get("pdf_author") or "")
    parts.append(meta.get("first_words") or "")

    runs = doc.get("runs") or []
    if runs:
        last = runs[-1]
        parts.append(last.get("raison") or "")
        parts.append(last.get("link_text") or "")
        parts.append(last.get("context_seen") or "")

    return " ".join(p for p in parts if p)


def build_index(catalog_path: Path = Path("synopsis/catalog.json"),
                index_path: Path = Path("synopsis/fulltext_index.json")) -> dict:
    """Construit l'index inversé et l'écrit sur disque. Retourne les stats."""
    if not catalog_path.exists():
        raise FileNotFoundError(catalog_path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})

    # term → {doc_id: tf}
    postings: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for doc_id, doc in docs.items():
        text = _gather_doc_text(doc)
        for tok in _normalize(text):
            postings[tok][doc_id] += 1

    # Sérialisation : on stocke la TF dans "tf" séparément pour permettre
    # un scoring efficace côté search() ; la liste de doc_ids reste lisible.
    terms_out: dict[str, list[str]] = {}
    tf_out: dict[str, dict[str, int]] = {}
    for term, doc_tfs in postings.items():
        terms_out[term] = sorted(doc_tfs.keys())
        tf_out[term] = dict(doc_tfs)

    index = {
        "terms": terms_out,
        "tf": tf_out,
        "stats": {
            "total_docs": len(docs),
            "total_terms": len(terms_out),
            "last_build": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return index["stats"]


def search(query: str, index_path: Path, top_k: int = 20) -> list[dict]:
    """Recherche multi-mot AND. Retourne [{doc_id, score, matched_terms}]."""
    if not index_path.exists():
        return []
    index = json.loads(index_path.read_text(encoding="utf-8"))
    terms_map: dict[str, list[str]] = index.get("terms", {})
    tf_map: dict[str, dict[str, int]] = index.get("tf", {})

    q_tokens = _normalize(query)
    if not q_tokens:
        return []

    # Intersection des doc_ids pour chaque token (AND strict)
    matching: set[str] | None = None
    for tok in q_tokens:
        bucket = set(terms_map.get(tok, []))
        if not bucket:
            return []  # un terme absent ⇒ AND vide
        matching = bucket if matching is None else matching & bucket
        if not matching:
            return []

    # Scoring : somme des TF pour chaque terme matché
    scored: list[dict] = []
    for doc_id in matching or []:
        score = 0
        matched_terms = []
        for tok in q_tokens:
            tf = tf_map.get(tok, {}).get(doc_id, 0)
            if tf:
                score += tf
                matched_terms.append(tok)
        scored.append({"doc_id": doc_id, "score": score,
                       "matched_terms": matched_terms})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ── Validation CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    catalog = root / "synopsis" / "catalog.json"
    idx = root / "synopsis" / "fulltext_index.json"

    print(f"Build de l'index depuis {catalog} ...")
    stats = build_index(catalog, idx)
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n── Recherches test ──")
    for q in ["communs", "tierra y libertad", "ostrom",
              "anarchiste", "paysannerie", "réforme agraire"]:
        hits = search(q, idx, top_k=5)
        print(f"\n  query={q!r} → {len(hits)} hit(s)")
        for h in hits[:3]:
            print(f"    doc={h['doc_id']} score={h['score']} "
                  f"terms={h['matched_terms']}")

    # Aperçu du vocabulaire (top 10 termes par fréquence postings)
    index = json.loads(idx.read_text(encoding="utf-8"))
    top_terms = sorted(index["terms"].items(),
                       key=lambda kv: len(kv[1]), reverse=True)[:10]
    print("\n  Top termes (par nb de docs) :")
    for term, ids in top_terms:
        print(f"    {term}: {len(ids)} doc(s)")
