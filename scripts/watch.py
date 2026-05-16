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

# Ajouter scripts/ au PYTHONPATH pour pouvoir importer parsers/ et utilitaires
sys.path.insert(0, str(Path(__file__).parent))
from parsers import dispatch as parser_dispatch
import pdf_processor
import synopsis_enricher

# ── Chemins ────────────────────────────────────────────────────────────────────
CONFIG_PATH    = Path("config/sources.yml")
DOCS_PATH      = Path("docs")
REPORTS_PATH   = Path("reports")
SYNOPSIS_PATH  = Path("synopsis")        # catalog.json (multi-runs, dédupliqué)
INTERFACE_PATH = Path("interface")       # index.html — fiches synopsis
COVERS_PATH    = INTERFACE_PATH / "covers"  # PNG des couvertures (page 1)
BULLES_PATH    = Path("bulles")          # JSON par doc ≥ 9 (publi troisiemesvoix)

for p in (DOCS_PATH, REPORTS_PATH, SYNOPSIS_PATH, INTERFACE_PATH, COVERS_PATH, BULLES_PATH):
    p.mkdir(parents=True, exist_ok=True)

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
    """Download standard. Le caller doit ensuite valider via pdf_processor."""
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


def download_and_validate(url: str, dest: Path) -> tuple[bool, str]:
    """Pipeline complet : download → validate → bypass si nécessaire.

    Retourne (success, status) où status ∈
      {'ok', 'ok_via_browser', 'ok_via_playwright',
       'failed_invalid_format', 'failed_network', 'failed_captcha'}.
    """
    if not download_file(url, dest):
        return False, "failed_network"

    if pdf_processor.validate_pdf(dest):
        return True, "ok"

    # Faux PDF détecté → essai bypass UA navigateur
    print(f"     ↻  Faux PDF détecté, retry avec UA navigateur…")
    ok, err = pdf_processor.redownload_with_bypass(url, dest)
    if ok:
        return True, "ok_via_browser"

    # Dernier recours : Playwright pour les sites avec JS challenge (HAL etc.)
    print(f"     ↻  Bypass UA insuffisant ({err}), retry avec Playwright…")
    ok, err = pdf_processor.download_with_playwright(url, dest)
    if ok:
        return True, "ok_via_playwright"

    # Échec total — supprimer le faux fichier
    if dest.exists():
        dest.unlink()
    return False, f"failed_captcha ({err})"


def analyse_pdf_and_enrich(dest: Path, doc: dict, score: int,
                            keywords: list[str]) -> dict:
    """Pour un PDF validé : extrait couverture, texte, et appelle Claude pour
    le synopsis enrichi. Si score ≥ 9, génère aussi la bulle de publication.

    Retourne un dict avec : cover_path, summary, citations,
    matched_keywords, relevance_score, bulle (si applicable).
    """
    out = {}
    uid = file_uid(doc["url"])

    # Métadonnées + premières pages
    meta = pdf_processor.extract_metadata(dest)
    out["meta"] = {
        "page_count":  meta.get("page_count", 0),
        "pdf_title":   meta.get("title", ""),
        "pdf_author":  meta.get("author", ""),
        "pdf_creator": meta.get("creator", ""),
    }

    # Couverture page 1 → PNG
    cover_path = COVERS_PATH / f"{uid}.png"
    if pdf_processor.extract_cover(dest, cover_path, max_width=400):
        out["cover"] = f"covers/{uid}.png"   # chemin relatif depuis interface/
        print(f"     🖼  Couverture extraite : {out['cover']}")

    # Synopsis enrichi via Claude (sur le texte du PDF)
    text = pdf_processor.extract_text(dest, max_chars=10000)
    if text:
        print(f"     📖  Texte extrait ({len(text)} chars), enrichissement…")
        title_hint = doc.get("link_text") or doc["filename"]
        enrichment = synopsis_enricher.enrich(text, keywords, title_hint)
        out["enrichment"] = enrichment

        if "error" in enrichment:
            print(f"     ⚠  Enrichissement raté : {enrichment['error']}")
        else:
            print(f"     ✨  Synopsis : {len(enrichment.get('summary', ''))} chars, "
                  f"{len(enrichment.get('citations', []))} citations, "
                  f"score post-lecture = {enrichment.get('relevance_score', '?')}/10")

            # Bulle de publication pour les meilleurs scores
            if score >= 9 or enrichment.get("relevance_score", 0) >= 9:
                print(f"     📝  Génération de la bulle de publication…")
                bulle = synopsis_enricher.generate_bulle(enrichment, doc)
                if "error" not in bulle:
                    bulle_path = BULLES_PATH / f"{uid}.json"
                    bulle_path.write_text(
                        json.dumps(bulle, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    out["bulle"] = f"bulles/{uid}.json"
                    print(f"     ✅  Bulle enregistrée : {out['bulle']}")
                else:
                    print(f"     ⚠  Bulle ratée : {bulle['error']}")

    return out


def update_synopsis_catalog(report: dict) -> None:
    """Met à jour synopsis/catalog.json (catalogue dédupliqué, multi-runs).

    Pour chaque doc scoré dans ce run :
    - Si déjà présent (clé = hash de l'URL) : ajoute une entrée dans `runs[]`
    - Sinon : crée la fiche

    Le catalog est consommé par interface/index.html.
    """
    catalog_path = SYNOPSIS_PATH / "catalog.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    else:
        catalog = {"docs": {}, "meta": {}}

    run_date = report["date"]

    for r in report["results"]:
        doc_id = file_uid(r["url"])
        run_entry = {
            "date":         run_date,
            "score":        r["score"],
            "raison":       r["raison"],
            "context_seen": r.get("context_seen", ""),
            "link_text":    r.get("link_text", ""),
            "downloaded":   r["downloaded"],
        }
        # Champs d'enrichissement éventuels (cover, synopsis, bulle)
        extras = {}
        for k in ("cover", "bulle", "meta", "enrichment", "download_status",
                  "drive_url"):
            if k in r:
                extras[k] = r[k]

        if doc_id in catalog["docs"]:
            fiche = catalog["docs"][doc_id]
            fiche["runs"] = [run for run in fiche["runs"] if run["date"] != run_date]
            fiche["runs"].append(run_entry)
            fiche["latest_score"] = r["score"]
            fiche["latest_run"]   = run_date
            if r["downloaded"] and not fiche.get("downloaded"):
                fiche["downloaded"] = True
                fiche["saved_as"]   = r["saved_as"]
            # Mise à jour des champs enrichis
            fiche.update({k: v for k, v in extras.items() if v})
        else:
            catalog["docs"][doc_id] = {
                "id":           doc_id,
                "url":          r["url"],
                "filename":     r["filename"],
                "format":       r["format"],
                "source":       r["source"],
                "first_seen":   run_date,
                "latest_run":   run_date,
                "latest_score": r["score"],
                "downloaded":   r["downloaded"],
                "saved_as":     r.get("saved_as"),
                "runs":         [run_entry],
                **extras,
            }

    # Méta
    catalog["meta"] = {
        "last_updated":      run_date,
        "total_docs":        len(catalog["docs"]),
        "total_downloaded":  sum(1 for f in catalog["docs"].values() if f["downloaded"]),
        "score_distribution": {
            i: sum(1 for f in catalog["docs"].values() if f["latest_score"] == i)
            for i in range(11)
        },
    }

    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  📒 Catalog mis à jour : {catalog['meta']['total_docs']} docs dont "
          f"{catalog['meta']['total_downloaded']} téléchargés")


def generate_interface(catalog_path: Path = SYNOPSIS_PATH / "catalog.json") -> None:
    """Génère interface/index.html avec catalog embarqué."""
    interface_template = Path(__file__).parent / "interface_template.html"
    if not interface_template.exists():
        print(f"  ⚠  Template introuvable : {interface_template}")
        return

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    template = interface_template.read_text(encoding="utf-8")

    # Inject le catalog comme variable JS embarquée — pas de fetch (marche en file://)
    embedded = json.dumps(catalog, ensure_ascii=False)
    final = template.replace("/*__CATALOG_INJECTED_HERE__*/null", embedded)

    out = INTERFACE_PATH / "index.html"
    out.write_text(final, encoding="utf-8")
    print(f"  🖥  Interface générée : {out} ({len(catalog['docs'])} fiches)")


SITE_PATH = Path("site")
SITE_BASE_URL = "https://biblio.actitude.org"


def publish_site(run_date: str) -> None:
    """Prépare le dossier site/ pour publication :
    - copie le catalog vers site/data/catalog.json
    - copie les bulles vers site/data/bulles/
    - copie les couvertures vers site/assets/covers/
    - régénère feed.xml et sitemap.xml dynamiquement
    """
    import shutil

    if not SITE_PATH.exists():
        print("  ⚠  site/ inexistant — skip publish")
        return

    # 1. Catalog
    catalog_src = SYNOPSIS_PATH / "catalog.json"
    if catalog_src.exists():
        (SITE_PATH / "data").mkdir(parents=True, exist_ok=True)
        shutil.copy2(catalog_src, SITE_PATH / "data" / "catalog.json")

    # 2. Bulles
    site_bulles = SITE_PATH / "data" / "bulles"
    site_bulles.mkdir(parents=True, exist_ok=True)
    bulle_count = 0
    for b in BULLES_PATH.glob("*.json"):
        shutil.copy2(b, site_bulles / b.name)
        bulle_count += 1

    # 3. Couvertures
    site_covers = SITE_PATH / "assets" / "covers"
    site_covers.mkdir(parents=True, exist_ok=True)
    cover_count = 0
    for c in COVERS_PATH.glob("*.png"):
        shutil.copy2(c, site_covers / c.name)
        cover_count += 1

    # 4. Génération RSS + sitemap
    catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
    _write_rss(catalog, run_date)
    _write_sitemap(catalog)

    print(f"  🌐 Site publié : {cover_count} couvertures, {bulle_count} bulles, "
          f"{len(catalog.get('docs', {}))} fiches au catalog")


def _write_rss(catalog: dict, run_date: str) -> None:
    """RSS 2.0 des 30 dernières fiches scorées ≥ 7."""
    docs = sorted(
        catalog.get("docs", {}).values(),
        key=lambda d: (d.get("latest_run", ""), d.get("latest_score", 0)),
        reverse=True,
    )
    items = []
    for d in docs[:30]:
        if d.get("latest_score", 0) < 7:
            continue
        title = d.get("filename", d.get("id", ""))
        if d.get("runs"):
            link_text = d["runs"][-1].get("link_text", "")
            if link_text:
                title = link_text
        url_fiche = f"{SITE_BASE_URL}/fiches/fiche.html?id={d['id']}"
        description = (d.get("enrichment", {}).get("summary", "") or
                       (d.get("runs", [{}])[-1] if d.get("runs") else {}).get("raison", ""))
        # Échapper les XML chars
        title = _xml_escape(title)
        description = _xml_escape(description[:600])
        items.append(f"""    <item>
      <title>{title}</title>
      <link>{url_fiche}</link>
      <guid isPermaLink="true">{url_fiche}</guid>
      <description>{description}</description>
      <category>{_xml_escape(d.get('source', ''))}</category>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BIBLIO — bibliothèque documentaire ouverte</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Veille documentaire : communs, terres, paysanneries</description>
    <language>fr</language>
    <lastBuildDate>{run_date}</lastBuildDate>
    <atom:link xmlns:atom="http://www.w3.org/2005/Atom" href="{SITE_BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (SITE_PATH / "feed.xml").write_text(rss, encoding="utf-8")


def _write_sitemap(catalog: dict) -> None:
    """Sitemap XML avec les pages principales + une fiche par doc."""
    urls = [
        f"{SITE_BASE_URL}/",
        f"{SITE_BASE_URL}/fiches/",
        f"{SITE_BASE_URL}/apropos.html",
    ]
    for d in catalog.get("docs", {}).values():
        urls.append(f"{SITE_BASE_URL}/fiches/fiche.html?id={d['id']}")
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    (SITE_PATH / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def _xml_escape(s: str) -> str:
    return (str(s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


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
                "url":          doc["url"],
                "filename":     doc["filename"],
                "format":       doc["extension"],
                "source":       label,
                "score":        score,
                "raison":       raison,
                "downloaded":   False,
                "saved_as":     None,
                # Citations littérales — ce que Claude a effectivement vu :
                "link_text":    doc.get("link_text", ""),
                "context_seen": doc.get("context", "")[:400],
            }

            if score >= threshold and not dry_run:
                uid  = file_uid(doc["url"])
                dest = DOCS_PATH / f"{uid}_{doc['filename']}"
                if dest.exists() and pdf_processor.validate_pdf(dest):
                    print(f"    ✓  Déjà présent   : {doc['filename']} ({score}/10)")
                    result["downloaded"]      = True
                    result["saved_as"]        = str(dest)
                    result["download_status"] = "already_present"
                else:
                    print(f"    ↓  Téléchargement : {doc['filename']} ({score}/10)")
                    success, status = download_and_validate(doc["url"], dest)
                    result["download_status"] = status
                    if success:
                        result["downloaded"] = True
                        result["saved_as"]   = str(dest)
                        report["documents_downloaded"] += 1
                        if status != "ok":
                            print(f"    ✓  Récupéré via {status}")
                    else:
                        print(f"    ❌  {doc['filename']} — {status}")

                # Enrichissement post-download : couverture + synopsis + bulle
                if result["downloaded"]:
                    enrichment = analyse_pdf_and_enrich(dest, doc, score, keywords)
                    result.update(enrichment)
            elif score >= threshold and dry_run:
                print(f"    [sim] Aurait téléchargé : {doc['filename']} ({score}/10)")
            else:
                print(f"    ✗  Ignoré          : {doc['filename']} ({score}/10 — {raison})")

            report["results"].append(result)

    json_path = REPORTS_PATH / f"run_{run_date}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    save_markdown_report(report, json_path)
    update_synopsis_catalog(report)
    generate_interface()
    publish_site(run_date)

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
