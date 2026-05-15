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
import yaml
import hashlib
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Ajouter scripts/ au PYTHONPATH pour pouvoir importer parsers/
sys.path.insert(0, str(Path(__file__).parent))
from parsers import dispatch as parser_dispatch

# ── Chemins ────────────────────────────────────────────────────────────────────
CONFIG_PATH  = Path("config/sources.yml")
DOCS_PATH    = Path("docs")
REPORTS_PATH = Path("reports")

DOCS_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

# ── Constantes ─────────────────────────────────────────────────────────────────
BATCH_SIZE = 8
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def file_uid(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def score_batch(docs: list[dict], keywords: list[str]) -> list[dict]:
    """Score un lot via Claude Code CLI (OAuth, consomme la subscription)."""
    if not docs:
        return []

    docs_block = ""
    for i, d in enumerate(docs, 1):
        docs_block += (
            f"\nDocument {i} :\n"
            f"  Lien    : {d['link_text']}\n"
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

5. **Cite littéralement** dans ta raison le mot/phrase du titre ou du contexte
   qui justifie ton score. Si tu ne peux pas citer → score ≤ 3.

6. **Attribue chaque score au bon "doc" numéro**. Ne mélange pas.

Pour chaque document, retourne :
  - "doc"   : numéro du document (entier)
  - "score" : 0 à 10
  - "raison": phrase brève citant LITTÉRALEMENT le titre/contexte

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
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  ⚠  Erreur scoring Claude : {e}")
        return [{"doc": i, "score": 0, "raison": "erreur scoring"}
                for i in range(1, len(docs) + 1)]


def download_file(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  ⚠  Téléchargement échoué pour {url} : {e}")
        return False


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


def main() -> None:
    config    = load_config()
    keywords  = config.get("keywords", [])
    sources   = config.get("sources", [])
    threshold = int(os.getenv("SCORE_THRESHOLD", str(config.get("threshold", 6))))
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
    }

    for source in sources:
        url       = source.get("url", "")
        label     = source.get("label", url)
        src_type  = source.get("type", "html")
        print(f"\n🔍  {label}  [type={src_type}]\n    {url}")

        # ── Dispatch vers le bon parser ────────────────────────────────────
        docs = parser_dispatch(source)
        if not docs:
            continue

        report["sources_scanned"] += 1
        print(f"    → {len(docs)} document(s) trouvé(s)")
        report["documents_found"] += len(docs)

        # ── Scoring par batches ─────────────────────────────────────────────
        all_scores: list[dict] = []
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i : i + BATCH_SIZE]
            print(f"    → Scoring batch {i // BATCH_SIZE + 1} ({len(batch)} docs)…")
            all_scores.extend(score_batch(batch, keywords))

        report["documents_scored"] += len(all_scores)

        for item in all_scores:
            idx = item["doc"] - 1
            if idx >= len(docs):
                continue
            doc    = docs[idx]
            score  = item.get("score", 0)
            raison = item.get("raison", "")

            result = {
                "url":        doc["url"],
                "filename":   doc["filename"],
                "format":     doc["extension"],
                "source":     label,
                "score":      score,
                "raison":     raison,
                "downloaded": False,
                "saved_as":   None,
            }

            if score >= threshold and not dry_run:
                uid  = file_uid(doc["url"])
                dest = DOCS_PATH / f"{uid}_{doc['filename']}"
                if dest.exists():
                    print(f"    ✓  Déjà présent   : {doc['filename']} ({score}/10)")
                    result["downloaded"] = True
                    result["saved_as"]   = str(dest)
                else:
                    print(f"    ↓  Téléchargement : {doc['filename']} ({score}/10)")
                    if download_file(doc["url"], dest):
                        result["downloaded"] = True
                        result["saved_as"]   = str(dest)
                        report["documents_downloaded"] += 1
            elif score >= threshold and dry_run:
                print(f"    [sim] Aurait téléchargé : {doc['filename']} ({score}/10)")
            else:
                print(f"    ✗  Ignoré          : {doc['filename']} ({score}/10 — {raison})")

            report["results"].append(result)

    json_path = REPORTS_PATH / f"run_{run_date}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    save_markdown_report(report, json_path)

    print(f"""
╔══════════════════════════════════════════╗
  Veille terminée — {run_date}
  Sources scannées    : {report['sources_scanned']}
  Documents trouvés   : {report['documents_found']}
  Scorés par Claude   : {report['documents_scored']}
  Téléchargés         : {report['documents_downloaded']}
  Rapport             : {json_path}
╚══════════════════════════════════════════╝""")


if __name__ == "__main__":
    main()
