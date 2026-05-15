#!/usr/bin/env python3
"""
Outil de veille documentaire — scrape des sites, score avec Claude, télécharge les docs pertinents.
Usage : python scripts/watch.py
"""

import os
import json
import yaml
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import anthropic

# ── Chemins ────────────────────────────────────────────────────────────────────
CONFIG_PATH  = Path("config/sources.yml")
DOCS_PATH    = Path("docs")
REPORTS_PATH = Path("reports")

DOCS_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

# ── Constantes ─────────────────────────────────────────────────────────────────
DOC_EXTENSIONS = {".pdf", ".txt", ".epub", ".doc", ".docx"}
BATCH_SIZE     = 8
HEADERS        = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def file_uid(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def fetch_page(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠  Impossible de charger {url} : {e}")
        return None


def find_documents(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.string.strip() if soup.title else urlparse(base_url).netloc

    seen, docs = set(), []
    for a in soup.find_all("a", href=True):
        full_url = urljoin(base_url, a["href"])
        ext = Path(urlparse(full_url).path).suffix.lower()
        if ext not in DOC_EXTENSIONS or full_url in seen:
            continue
        seen.add(full_url)

        link_text = a.get_text(strip=True)
        parent    = a.find_parent(["p", "li", "div", "td", "article"])
        context   = parent.get_text(" ", strip=True)[:400] if parent else link_text

        docs.append({
            "url":        full_url,
            "filename":   Path(urlparse(full_url).path).name or "document",
            "extension":  ext.lstrip("."),
            "link_text":  link_text,
            "context":    context,
            "page_title": page_title,
            "source_url": base_url,
        })

    return docs


def score_batch(docs: list[dict], keywords: list[str], client: anthropic.Anthropic) -> list[dict]:
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

    prompt = f"""Tu es un assistant de veille documentaire spécialisé en sciences humaines et sociales.

Mots-clés de recherche :
{keywords_block}

Évalue la pertinence de chaque document par rapport à ces mots-clés.
Pour chaque document retourne :
  - "doc"   : le numéro du document (entier)
  - "score" : pertinence de 0 à 10 (0 = hors sujet, 10 = très pertinent)
  - "raison": une phrase courte justifiant le score

Réponds UNIQUEMENT avec un tableau JSON valide, sans balise markdown.
Exemple : [{{"doc":1,"score":7,"raison":"Traite directement de la mémoire collective."}}]

Documents :
{docs_block}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  ⚠  Erreur scoring Claude : {e}")
        return [{"doc": i, "score": 0, "raison": "erreur scoring"} for i in range(1, len(docs) + 1)]


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
    lines = [
        f"# Rapport de veille — {report['date']}",
        "",
        f"- Sources scannées  : **{report['sources_scanned']}**",
        f"- Documents trouvés : **{report['documents_found']}**",
        f"- Scorés par Claude : **{report['documents_scored']}**",
        f"- Téléchargés       : **{report['documents_downloaded']}**",
        "",
        "## Documents téléchargés",
        "",
    ]

    downloaded = [r for r in report["results"] if r["downloaded"]]
    if downloaded:
        for r in downloaded:
            lines += [
                f"### {r['filename']}",
                f"- Source : [{r['source']}]({r['url']})",
                f"- Format : {r['format'].upper()}",
                f"- Score  : {r['score']}/10",
                f"- Raison : {r['raison']}",
                f"- Fichier: `{r['saved_as']}`",
                "",
            ]
    else:
        lines.append("_Aucun document téléchargé lors de cette veille._\n")

    lines += ["## Documents ignorés (score trop bas)", ""]
    for r in [r for r in report["results"] if not r["downloaded"]]:
        lines.append(f"- **{r['filename']}** (score {r['score']}/10) — {r['raison']}")

    path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config    = load_config()
    keywords  = config.get("keywords", [])
    sources   = config.get("sources", [])
    threshold = int(os.getenv("SCORE_THRESHOLD", str(config.get("threshold", 6))))
    dry_run   = os.getenv("DRY_RUN", "false").lower() == "true"

    if dry_run:
        print("🔎  Mode simulation — aucun fichier ne sera téléchargé.\n")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    run_date = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    report   = {
        "date": run_date,
        "sources_scanned":    0,
        "documents_found":    0,
        "documents_scored":   0,
        "documents_downloaded": 0,
        "results":            [],
    }

    for source in sources:
        url   = source.get("url", "")
        label = source.get("label", url)
        print(f"\n🔍  {label}\n    {url}")

        html = fetch_page(url)
        if not html:
            continue

        report["sources_scanned"] += 1
        docs = find_documents(html, url)
        print(f"    → {len(docs)} document(s) trouvé(s)")
        report["documents_found"] += len(docs)

        if not docs:
            continue

        all_scores: list[dict] = []
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i : i + BATCH_SIZE]
            print(f"    → Scoring batch {i // BATCH_SIZE + 1} ({len(batch)} docs)…")
            all_scores.extend(score_batch(batch, keywords, client))

        report["documents_scored"] += len(all_scores)

        for item in all_scores:
            idx    = item["doc"] - 1
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
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
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
