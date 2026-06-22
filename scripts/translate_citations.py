#!/usr/bin/env python3
"""
translate_citations.py — Traduit les citations en français via claude CLI.

Pour chaque doc du catalogue dont la langue n'est pas le français :
- Prend les citations de doc["enrichment"]["citations"]
- Traduit le champ "quote" vers le français
- Stocke la traduction dans "quote_fr" à côté de "quote" (l'original est préservé)
- N'appelle le modèle que si "quote_fr" est absent (idempotent)

Usage standalone :
  python3 scripts/translate_citations.py

Appelé aussi depuis watch.py après l'enrichissement.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

CATALOG_PATH = Path("synopsis/catalog.json")

# Même modèle que synopsis_enricher — cohérence du projet
CLAUDE_MODEL = "claude-haiku-4-5"
CLAUDE_FLAGS = [
    "--output-format", "text",
    "--no-session-persistence",
    "--disable-slash-commands",
    "--dangerously-skip-permissions",
]
CLAUDE_TIMEOUT_SEC = 120

# Throttle minimal entre appels API (secondes)
_INTER_CALL_DELAY = 0.5


def _call_claude(prompt: str, timeout: int = CLAUDE_TIMEOUT_SEC) -> str:
    """Appelle claude -p et retourne le texte brut. Lève RuntimeError si exit ≠ 0."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", CLAUDE_MODEL] + CLAUDE_FLAGS,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd="/tmp",
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude exit {result.returncode} — "
            f"stdout={result.stdout[:200]} stderr={result.stderr[:200]}"
        )
    raw = result.stdout.strip()
    # Retire les éventuels blocs markdown si le modèle les produit
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def translate_batch(quotes: list[str], source_lang: str) -> list[str]:
    """Traduit une liste de citations en français via un seul appel Claude.

    Retourne une liste de même longueur. En cas d'erreur, retourne les
    originaux inchangés.
    """
    if not quotes:
        return []

    lang_label = {
        "en": "anglais",
        "es": "espagnol",
        "de": "allemand",
        "pt": "portugais",
        "it": "italien",
        "nl": "néerlandais",
    }.get(source_lang, source_lang or "langue source")

    numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(quotes))

    prompt = f"""Traduis les citations suivantes de l'{lang_label} vers le français.

Règles :
- Traduction fidèle, sans paraphrase ni omission.
- Conserve le registre (académique, militant, technique…).
- NE modifie pas les noms propres, les titres d'œuvres, les sigles.
- Réponds avec un tableau JSON d'exactement {len(quotes)} chaînes, dans le même ordre.
  Exemple pour 2 citations : ["Traduction 1", "Traduction 2"]
- Aucun texte hors du JSON.

Citations à traduire :
{numbered}"""

    try:
        raw = _call_claude(prompt)
        translations = json.loads(raw)
        if not isinstance(translations, list) or len(translations) != len(quotes):
            print(f"  ⚠  translate_batch : réponse inattendue ({len(translations) if isinstance(translations, list) else type(translations).__name__} ≠ {len(quotes)})")
            return quotes
        # Valider que chaque traduction est une chaîne
        return [str(t) if t is not None else q for t, q in zip(translations, quotes)]
    except json.JSONDecodeError as e:
        print(f"  ⚠  translate_batch : json_parse : {e} — raw={repr(raw[:200])}")
        return quotes
    except Exception as e:
        print(f"  ⚠  translate_batch : {e}")
        return quotes


def translate_doc_citations(doc: dict) -> int:
    """Traduit les citations d'un document si nécessaire.

    Modifie doc["enrichment"]["citations"] en place.
    Retourne le nombre de citations effectivement traduites.
    """
    lang = (doc.get("lang") or "").strip().lower()

    # Ne pas traduire si la langue est française ou inconnue
    # (les docs "unknown" ont souvent des citations mixtes extraites en fr
    # par Claude depuis un texte en langue étrangère — on traduit quand même
    # si lang est un code connu non-fr)
    if lang in ("fr", ""):
        return 0

    enrichment = doc.get("enrichment")
    if not isinstance(enrichment, dict) or "error" in enrichment:
        return 0

    citations = enrichment.get("citations", [])
    if not citations:
        return 0

    # Collecter les citations sans quote_fr
    to_translate_idx = []
    to_translate_quotes = []
    for i, c in enumerate(citations):
        if not isinstance(c, dict):
            continue
        quote = (c.get("quote") or "").strip()
        if not quote:
            continue
        if c.get("quote_fr"):
            continue  # déjà traduit — idempotent
        to_translate_idx.append(i)
        to_translate_quotes.append(quote)

    if not to_translate_quotes:
        return 0

    translations = translate_batch(to_translate_quotes, lang)

    count = 0
    for i, tr in zip(to_translate_idx, translations):
        original = citations[i].get("quote", "")
        # Ne stocker que si la traduction est différente de l'original
        if tr and tr.strip() and tr.strip() != original.strip():
            citations[i]["quote_fr"] = tr.strip()
            count += 1
        else:
            # Même si identique (cas rare), on marque quand même pour
            # éviter de re-tenter à chaque run
            citations[i]["quote_fr"] = tr.strip() if tr else original

    return count


def run(catalog_path: Path = CATALOG_PATH, verbose: bool = True) -> dict:
    """Point d'entrée principal. Modifie le catalogue sur disque.

    Retourne des statistiques : {"docs_processed": int, "citations_translated": int}.
    """
    if not catalog_path.exists():
        print(f"  ⚠  translate_citations : catalogue introuvable ({catalog_path})")
        return {"docs_processed": 0, "citations_translated": 0}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    docs = catalog.get("docs", {})

    docs_processed = 0
    citations_translated = 0
    modified = False

    # Langues non-fr à traiter
    supported_langs = {"en", "es", "de", "pt", "it", "nl"}

    for doc_id, doc in docs.items():
        lang = (doc.get("lang") or "").strip().lower()
        if lang not in supported_langs:
            continue

        enrichment = doc.get("enrichment")
        if not isinstance(enrichment, dict) or "error" in enrichment:
            continue

        citations = enrichment.get("citations", [])
        if not citations:
            continue

        # Vérifier si ce doc a des citations non encore traduites
        needs_translation = any(
            isinstance(c, dict) and (c.get("quote") or "").strip() and not c.get("quote_fr")
            for c in citations
        )
        if not needs_translation:
            continue

        if verbose:
            title = ""
            if doc.get("runs"):
                title = doc["runs"][-1].get("link_text", "") or ""
            print(f"  🌐  [{lang}] {doc_id} — {title[:60] or doc.get('filename', '')}")

        n = translate_doc_citations(doc)
        if n > 0:
            docs_processed += 1
            citations_translated += n
            modified = True
            if verbose:
                print(f"       → {n} citation(s) traduite(s)")
            time.sleep(_INTER_CALL_DELAY)

    if modified:
        catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=1),
            encoding="utf-8"
        )
        if verbose:
            print(f"  ✅  Catalogue mis à jour : "
                  f"{docs_processed} doc(s), {citations_translated} citation(s) traduite(s)")
    else:
        if verbose:
            print("  ℹ  translate_citations : aucune nouvelle citation à traduire")

    return {"docs_processed": docs_processed, "citations_translated": citations_translated}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Traduit les citations en français.")
    parser.add_argument("--catalog", default=str(CATALOG_PATH),
                        help="Chemin vers catalog.json")
    parser.add_argument("--quiet", action="store_true",
                        help="Sortie minimale")
    args = parser.parse_args()
    stats = run(
        catalog_path=Path(args.catalog),
        verbose=not args.quiet,
    )
    print(f"\nBilan : {stats['docs_processed']} doc(s) traité(s), "
          f"{stats['citations_translated']} citation(s) traduite(s).")
