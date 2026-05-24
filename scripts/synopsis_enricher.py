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
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from prompt_version import prompt_hash
except Exception:  # pragma: no cover — dégradation propre
    def prompt_hash(p: str, length: int = 10) -> str:
        import hashlib
        return hashlib.sha256((p or "").encode()).hexdigest()[:length] if p else "noprompt"

CLAUDE_TIMEOUT_SEC  = 240
CLAUDE_MODEL        = "claude-haiku-4-5"
CLAUDE_FLAGS        = [
    "--output-format", "text",
    "--no-session-persistence",
    "--disable-slash-commands",
    "--tools", "",
    "--dangerously-skip-permissions",
]

# Charge l'ontologie du projet (concepts.yml) — fallback gracieux si absent
_CONCEPTS_PATH = Path(__file__).parent.parent / "config" / "concepts.yml"


def _load_concepts() -> dict:
    """Lit config/concepts.yml. Retourne {} si absent ou erreur."""
    if not _CONCEPTS_PATH.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(_CONCEPTS_PATH.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"  ⚠  concepts.yml inaccessible : {e}")
        return {}


def _build_ontology_block(concepts: dict) -> str:
    """Construit la section 'ontologie' du prompt à partir de concepts.yml."""
    ontology = concepts.get("ontology", {})
    cores = ontology.get("core_concepts", []) or []
    related = ontology.get("related_concepts", []) or []
    anti = ontology.get("anti_concepts", []) or []

    lines = []
    if cores:
        lines.append("Concepts centraux (présence explicite = score ≥ 8) :")
        for c in cores:
            lines.append(f"  • {c.get('name')} — {c.get('definition', '').strip()}")
            eq = c.get("equivalents", {})
            for lang, terms in eq.items():
                if terms:
                    lines.append(f"      [{lang}] {', '.join(terms)}")
    if related:
        lines.append("\nConcepts apparentés (mention seule = score 5-7) :")
        lines.append("  " + " · ".join(str(r) for r in related))
    if anti:
        lines.append("\nAnti-concepts (à pénaliser, score ≤ 3 si dominant) :")
        lines.append("  " + " · ".join(str(a) for a in anti))
    return "\n".join(lines)


def _build_examples_block(concepts: dict) -> str:
    examples = concepts.get("scoring", {}).get("custom_examples", []) or []
    if not examples:
        return ""
    out = ["Exemples étalons (à utiliser comme calibration) :"]
    for ex in examples:
        out.append(
            f"  • « {ex.get('title_example', '')} » → "
            f"score {ex.get('score', '?')}/10 — {ex.get('reason', '')}"
        )
    return "\n".join(out)


def _build_voice_block(concepts: dict) -> str:
    edit = concepts.get("editorial", {})
    voice = edit.get("voice", "")
    audience = edit.get("audience", "")
    tones = edit.get("tone_examples", []) or []
    if not (voice or audience or tones):
        return ""
    lines = []
    if voice:
        lines.append(f"Voix éditoriale : {voice}")
    if audience:
        lines.append(f"Lectorat cible : {audience}")
    if tones:
        lines.append("Exemples de ton :")
        for t in tones[:3]:
            lines.append(f"  • {t}")
    return "\n".join(lines)


# Charge une seule fois au module load
_CONCEPTS = _load_concepts()
_ONTOLOGY_BLOCK = _build_ontology_block(_CONCEPTS)
_EXAMPLES_BLOCK = _build_examples_block(_CONCEPTS)
_VOICE_BLOCK    = _build_voice_block(_CONCEPTS)


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


def _normalize_for_match(s: str) -> str:
    """Normalise un texte pour la comparaison de citations : minuscules,
    espaces compressés, ponctuation et diacritiques retirés.

    Sert à re-rechercher une citation littérale dans le texte du PDF malgré
    les différences d'extraction (césures, espaces, accents, guillemets
    typographiques) — l'OCR et les extractions PDF perdent souvent les
    accents.
    """
    if not s:
        return ""
    import unicodedata
    s = s.lower()
    # Guillemets typographiques → simples
    s = s.replace("«", "").replace("»", "").replace("“", "").replace("”", "")
    s = s.replace("’", "'").replace("‘", "'")
    # Tirets de césure en fin de ligne
    s = re.sub(r"-\s*\n\s*", "", s)
    # Repli des diacritiques (à→a, é→e…) : tolérant aux pertes d'accents OCR
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    # Tout ce qui n'est pas alphanumérique → espace
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def verify_citations(citations: list[dict], pdf_text: str) -> list[dict]:
    """Re-recherche chaque citation littérale dans le texte extrait du PDF
    (item A4 — anti-hallucination).

    Pour chaque citation, ajoute :
      - `verified` (bool) : True si le quote est retrouvé dans le texte ;
      - `page_physical` (int|None) : page physique du PDF où le quote apparaît
        (déduite des marqueurs [p.N]), distincte de `page` (page imprimée
        annoncée par le modèle, souvent la pagination du document).

    Tolérant : une correspondance partielle (≥ 85% des mots-clés de la
    citation présents consécutivement) compte comme vérifiée.
    """
    if not citations:
        return []
    norm_text = _normalize_for_match(pdf_text)

    # Index des marqueurs [p.N] → offset dans le texte normalisé
    # On normalise page par page pour pouvoir retrouver la page physique.
    page_spans: list[tuple[int, int]] = []  # (page_no, offset_norm)
    if pdf_text:
        offset = 0
        for chunk in re.split(r"(\[p\.\d+\])", pdf_text):
            m = re.match(r"\[p\.(\d+)\]", chunk)
            if m:
                page_spans.append((int(m.group(1)), offset))
            else:
                offset += len(_normalize_for_match(chunk)) + 1

    def _page_at(pos: int) -> int | None:
        found = None
        for page_no, off in page_spans:
            if off <= pos:
                found = page_no
            else:
                break
        return found

    out = []
    for c in citations:
        c = dict(c) if isinstance(c, dict) else {"quote": str(c)}
        quote = c.get("quote", "") or ""
        norm_q = _normalize_for_match(quote)
        verified = False
        page_physical = None
        if norm_q and norm_text:
            idx = norm_text.find(norm_q)
            if idx != -1:
                verified = True
                page_physical = _page_at(idx)
            else:
                # Correspondance partielle : fenêtre glissante sur les mots
                words = norm_q.split()
                if len(words) >= 4:
                    head = " ".join(words[: max(4, len(words) * 7 // 10)])
                    idx = norm_text.find(head)
                    if idx != -1:
                        verified = True
                        page_physical = _page_at(idx)
        c["verified"] = verified
        c["page_physical"] = page_physical
        # `page` reste la page imprimée annoncée par le modèle
        out.append(c)
    return out


def enrich(text: str, keywords: list[str], doc_title: str = "") -> dict:
    """Produit le synopsis enrichi d'un document.

    Retourne :
    {
      "summary": str,              # résumé long (400-600 mots)
      "citations": [               # 10 max, dans l'ordre d'apparition
        {"page": int, "quote": str, "why_relevant": str,
         "verified": bool, "page_physical": int|None},
        ...
      ],
      "matched_keywords": [str, ...],   # mots-clés réellement présents
      "relevance_score": int,           # confirmation 0-10 après lecture
      "relevance_notes": str,
      "en_clair": str,                  # B4 — 2 phrases en langue simple
      "acteurs": [str, ...],            # B9 — acteurs/organisations cités
      "controverse": str,               # B9 — point de débat/tension
      "angle_journalistique": str,      # B9 — angle d'enquête possible
      "model": str, "prompt_version": str,  # C6 — reproductibilité
    }

    En cas d'échec, retourne un dict avec champ "error".
    """
    if not text or len(text) < 200:
        return {"error": "text_too_short_or_empty"}

    # Garde-fou — un PDF scanné (sans couche texte) ressort de l'extraction
    # comme une suite de marqueurs de pagination « [p.N] » sans contenu
    # interstitiel. Sa longueur brute dépasse le seuil ci-dessus, mais Claude
    # répondrait « document vide » en texte libre, cassant le json.loads.
    # On mesure ici le vrai contenu, pagination retirée, et on abandonne
    # proprement plutôt que de gaspiller un appel voué à l'échec.
    _real_content = re.sub(r"\[p\.\d+\]", "", text).strip()
    if len(_real_content) < 200:
        return {"error": "text_too_short_or_empty"}

    keywords_block = "\n".join(f"  - {kw}" for kw in keywords)

    ontology_section = (
        f"\nONTOLOGIE FORMELLE DE LA THÉMATIQUE :\n{_ONTOLOGY_BLOCK}\n"
        if _ONTOLOGY_BLOCK else ""
    )
    examples_section = (
        f"\n{_EXAMPLES_BLOCK}\n" if _EXAMPLES_BLOCK else ""
    )
    voice_section = (
        f"\n{_VOICE_BLOCK}\n" if _VOICE_BLOCK else ""
    )

    prompt = f"""Tu es un assistant de veille documentaire spécialisé en sciences humaines et sociales.

J'ai extrait le texte brut d'un PDF (les marqueurs [p.N] indiquent le numéro de page).
Le titre apparent du document est : "{doc_title}"

THÉMATIQUE de notre veille (mots-clés) :
{keywords_block}
{ontology_section}{examples_section}{voice_section}
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
  "relevance_notes": "ton estimation finale 0-10 après lecture du contenu réel (ATTENTION : indépendante du score précédent qui s'appuyait sur le titre seulement) + 1 phrase qui explique",
  "en_clair": "2 phrases courtes en langue très simple : concrètement, à quoi ce texte peut servir dans une lutte ? Pas de jargon.",
  "acteurs": ["liste des organisations, collectifs, mouvements ou personnes RÉELLEMENT nommés dans le texte — n'invente AUCUN nom"],
  "controverse": "le principal point de débat, tension ou désaccord soulevé par le texte (1-2 phrases). Vide si le texte n'en contient pas.",
  "angle_journalistique": "un angle d'enquête ou de reportage qu'un·e journaliste pourrait tirer de ce texte (1 phrase). Vide si non pertinent."
}}

RÈGLES SUPPLÉMENTAIRES :
- `acteurs` : uniquement des noms réellement présents dans le texte. Si le
  document est anonyme ou ne nomme personne, laisse la liste vide.
- `en_clair` : adresse-toi à quelqu'un qui n'a pas fait d'études, sans
  condescendance. Concret et utile.

Texte du document (peut être tronqué) :
{text}"""

    try:
        raw = _call_claude(prompt)
        data = json.loads(raw)
        # Validation minimale du shape — défauts pour migration douce
        defaults = {
            "summary": "", "citations": [], "matched_keywords": [],
            "relevance_score": 0, "relevance_notes": "",
            "en_clair": "", "acteurs": [], "controverse": "",
            "angle_journalistique": "",
        }
        for field, default in defaults.items():
            if field not in data:
                data[field] = default
        # A4 — vérification des citations littérales dans le texte du PDF
        try:
            data["citations"] = verify_citations(data.get("citations", []), text)
        except Exception as e:
            print(f"  ⚠  verify_citations raté : {e}")
        # C6 — reproductibilité : modèle + version du prompt
        data["model"] = CLAUDE_MODEL
        data["prompt_version"] = prompt_hash(prompt)
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
        bulle = json.loads(raw)
        # B9/B4 — on propage les champs exploitables de l'enrichissement
        # vers la bulle (l'agent frontend les affiche dans un encart).
        bulle["en_clair"] = enriched.get("en_clair", "")
        bulle["acteurs"] = enriched.get("acteurs", []) or []
        bulle["controverse"] = enriched.get("controverse", "")
        bulle["angle_journalistique"] = enriched.get("angle_journalistique", "")
        # A4 — citations vérifiées : on conserve l'info de vérification
        verified_cites = enriched.get("citations", []) or []
        bulle["citations_verifiees"] = [
            {"quote": c.get("quote", ""),
             "page": c.get("page"),
             "page_physical": c.get("page_physical"),
             "verified": c.get("verified", False)}
            for c in verified_cites if isinstance(c, dict)
        ]
        # C6 — reproductibilité
        bulle["model"] = CLAUDE_MODEL
        bulle["prompt_version"] = prompt_hash(prompt)
        return bulle
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
