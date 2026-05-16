#!/usr/bin/env python3
"""
synopsis_enricher.py — Génère un synopsis enrichi via Claude Code CLI.

À partir du texte extrait d'un PDF (via PyMuPDF) :
- Résumé long (400-600 mots)
- 10 citations max avec référence de page
- Liste de mots-clés réellement présents dans le doc
- Évaluation finale de la pertinence

Pour les docs scorés ≥ 9, génère aussi une "bulle de publication" prête
à intégrer dans un site (troisiemesvoix.org/bibliothèque).
"""

import json
import subprocess
from pathlib import Path

CLAUDE_TIMEOUT_SEC  = 240
CLAUDE_MODEL        = "claude-haiku-4-5"
CLAUDE_FLAGS        = [
    "--output-format", "text",
    "--no-session-persistence",
    "--disable-slash-commands",
    "--tools", "",
    "--dangerously-skip-permissions",
]


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
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def enrich(text: str, keywords: list[str], doc_title: str = "") -> dict:
    """Produit le synopsis enrichi d'un document.

    Retourne :
    {
      "summary": str,              # résumé long (400-600 mots)
      "citations": [               # 10 max, dans l'ordre d'apparition
        {"page": int, "quote": str, "why_relevant": str},
        ...
      ],
      "matched_keywords": [str, ...],   # mots-clés réellement présents
      "relevance_score": int,           # confirmation 0-10 après lecture
      "relevance_notes": str,
    }

    En cas d'échec, retourne un dict avec champ "error".
    """
    if not text or len(text) < 200:
        return {"error": "text_too_short_or_empty"}

    keywords_block = "\n".join(f"  - {kw}" for kw in keywords)

    prompt = f"""Tu es un assistant de veille documentaire spécialisé en sciences humaines et sociales.

J'ai extrait le texte brut d'un PDF (les marqueurs [p.N] indiquent le numéro de page).
Le titre apparent du document est : "{doc_title}"

THÉMATIQUE de notre veille :
{keywords_block}

RÈGLES :
- Lis attentivement le texte et identifie les passages qui touchent réellement à la thématique.
- Ne fabrique RIEN. Si un mot-clé n'apparaît pas, ne le mentionne pas dans matched_keywords.
- Pour les citations : reproduis EXACTEMENT le texte tel qu'il apparaît, avec le numéro de page.
- Maximum 10 citations, sélectionne les plus pertinentes.

Génère ce JSON (un seul objet, pas de balise markdown) :

{{
  "summary": "résumé synthétique en 400-600 mots du document, centré sur ce qui touche à la thématique veille — utilise un français soigné et clair",
  "citations": [
    {{
      "page": 12,
      "quote": "citation EXACTE depuis le texte, max 250 caractères",
      "why_relevant": "phrase brève expliquant en quoi cette citation touche la thématique"
    }}
  ],
  "matched_keywords": ["liste des mots-clés de la thématique vraiment présents dans le texte"],
  "relevance_score": 7,
  "relevance_notes": "ton estimation finale 0-10 après lecture du contenu réel (ATTENTION : indépendante du score précédent qui s'appuyait sur le titre seulement) + 1 phrase qui explique"
}}

Texte du document (peut être tronqué) :
{text}"""

    try:
        raw = _call_claude(prompt)
        data = json.loads(raw)
        # Validation minimale du shape
        for field in ("summary", "citations", "matched_keywords",
                      "relevance_score", "relevance_notes"):
            if field not in data:
                data[field] = "" if field != "citations" else []
        return data
    except json.JSONDecodeError as e:
        return {"error": f"json_parse: {e}", "raw_response": raw[:500]}
    except Exception as e:
        return {"error": f"claude_call: {e}"}


def generate_bulle(enriched: dict, doc_meta: dict) -> dict:
    """Pour un doc scoré ≥ 9, produit une 'bulle de publication' éditorialisée
    destinée à figurer dans la rubrique 'bibliothèque' du site troisiemesvoix.org.

    Retourne :
    {
      "titre_accroche": str,    # 80 chars max, accrocheur
      "teaser": str,            # 250 chars max, accroche
      "abstract_editorial": str, # 300 mots, ton éditorial
      "citations_phares": [{"quote": str, "page": int}],  # 3 max
      "categorisation": [str],  # tags thématiques pour la rubrique
      "slug": str,              # url-safe pour intégration site
    }
    """
    if "error" in enriched:
        return {"error": "cannot_generate_bulle_from_error_enrichment"}

    summary = enriched.get("summary", "")
    citations = enriched.get("citations", [])
    title = doc_meta.get("link_text") or doc_meta.get("filename", "")

    citations_block = "\n".join(
        f"  [p.{c.get('page', '?')}] {c.get('quote', '')[:200]}"
        for c in citations[:5]
    )

    prompt = f"""Tu es un éditeur pour le site troisiemesvoix.org, rubrique "bibliothèque".
Tu prépares une fiche éditoriale qui présentera un texte pertinent au lectorat
intéressé par les communs, la propriété d'usage, la libération des terres et la paysannerie.

Document : "{title}"

Voici son résumé documentaire :
{summary}

Voici quelques citations clés extraites par l'agent de veille :
{citations_block}

Génère ce JSON (un seul objet, pas de balise markdown) :

{{
  "titre_accroche": "titre éditorial accrocheur, 80 caractères max, qui donne envie de cliquer",
  "teaser": "phrase d'accroche de 250 caractères max pour la rubrique bibliothèque (ton éditorial, pas descriptif)",
  "abstract_editorial": "résumé éditorialisé de 300 mots, soigné, sans copier le résumé brut, présentant le texte au lecteur de troisiemesvoix.org en le situant dans le débat sur les communs/la terre",
  "citations_phares": [
    {{"page": 12, "quote": "citation forte tirée du texte"}}
  ],
  "categorisation": ["tags thématiques pour la rubrique, ex: 'communs', 'paysannerie', 'autonomie territoriale'"],
  "slug": "url-safe-version-du-titre-en-minuscules-avec-tirets"
}}

Ne fabrique rien. Reste fidèle au document. 3 citations phares maximum."""

    try:
        raw = _call_claude(prompt, timeout=180)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"json_parse: {e}", "raw_response": raw[:500] if 'raw' in dir() else ''}
    except Exception as e:
        return {"error": f"claude_call: {e}"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage : synopsis_enricher.py <pdf_path>")
        sys.exit(1)
    from pdf_processor import extract_text, extract_metadata
    path = Path(sys.argv[1])
    text = extract_text(path)
    meta = extract_metadata(path)
    keywords = ["communs", "paysannerie", "libération des terres",
                "propriété d'usage", "sans-terre"]
    print(f"Texte extrait : {len(text)} chars sur {meta.get('page_count', 0)} pages")
    result = enrich(text, keywords, meta.get("title", path.stem))
    print(json.dumps(result, ensure_ascii=False, indent=2))
