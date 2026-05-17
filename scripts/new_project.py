#!/usr/bin/env python3
"""
new_project.py — Scaffolde un nouvel agent de veille thématique complet.

Usage :
    python scripts/new_project.py \
        --name=feminismes-decoloniaux \
        --display="Féminismes décoloniaux" \
        --tagline="Bibliothèque des féminismes décoloniaux" \
        --subdomain=feminismes.actitude.org \
        --target-dir=/tmp/agent-feminismes-decoloniaux

Optionnel : --init-git pour initialiser git + créer les repos GitHub via `gh`
            et déclarer un CNAME chez Gandi (si GANDI_PAT est exporté).

Ce script :
  1. Crée la structure de dossiers cible
  2. Copie tous les scripts de veille (watch.py, parsers/*, etc.)
  3. Copie le workflow GitHub Actions en l'adaptant
  4. Copie la structure du site (HTML / CSS / JS) en substituant :
       - le nom de marque (titre, manifest, OG, footer)
       - le subdomain (CNAME, balises canonical)
       - le logo SVG (palette + initiale dérivées du slug)
  5. Génère config/sources.yml (vide, 3 sources exemples)
  6. Génère config/concepts.yml (à partir du template)
  7. Génère README.md (étapes de setup)
  8. Génère .gitignore
  9. (optionnel) git init + gh repo create + Gandi DNS

Conçu pour être idempotent côté FS : si --target-dir existe et n'est PAS vide,
on refuse (sauf --force).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Permettre l'import de templating_helpers que ce soit appelé depuis
# scripts/ ou depuis la racine du repo.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from templating_helpers import (  # noqa: E402
    generate_simple_favicon_svg,
    generate_simple_logo_svg,
    pick_palette,
    slug_to_title,
    substitute_placeholders,
)

# Racine du repo de référence (parent de scripts/).
REPO_ROOT = SCRIPT_DIR.parent


# ═════════════════════════════════════════════════════════════════════════════
# 1. Squelette : fichiers à copier tels quels ou à régénérer
# ═════════════════════════════════════════════════════════════════════════════

# Scripts à copier intégralement vers <target>/scripts/.
SCRIPT_FILES = [
    "watch.py",
    "pdf_processor.py",
    "synopsis_enricher.py",
    "probe_source.py",
    "source_health.py",
    "interface_template.html",
    "templating_helpers.py",
    "new_project.py",
]

PARSER_FILES = [
    "__init__.py",
    "archive_org.py",
    "deep_html.py",
    "hal.py",
    "html_static.py",
    "opds.py",
    "playwright_parser.py",
]

# Fichiers du site à recopier puis ré-écrire avec substitutions.
SITE_FILES_RECURSIVE = [
    "site/index.html",
    "site/apropos.html",
    "site/fiches/index.html",
    "site/fiches/fiche.html",
    "site/manifest.json",
    "site/robots.txt",
    "site/sitemap.xml",
    "site/feed.xml",
    "site/assets/css/style.css",
    "site/assets/js/app.js",
    "site/assets/js/router.js",
    "site/assets/js/search.js",
    "site/assets/img/og-default.svg",
]

# Fichiers .gitkeep à recréer pour préserver les dossiers vides
GITKEEP_DIRS = [
    "site/data",
    "site/assets/covers",
    "docs",
    "reports",
    "synopsis",
    "bulles",
    "interface",
]


# ═════════════════════════════════════════════════════════════════════════════
# 2. Templates internes (README, .gitignore, sources.yml exemple)
# ═════════════════════════════════════════════════════════════════════════════

README_TEMPLATE = """# {{DISPLAY_NAME}}

> {{TAGLINE}}

Agent de veille documentaire automatisé, dérivé du système
[veille-documentaire](https://github.com/CedricMabilotte/veille-documentaire).

Le scoreur Claude lit `config/concepts.yml` pour calibrer son ontologie : ce
fichier décrit formellement la thématique du projet (concepts centraux,
adjacents, faux amis, voix éditoriale, exemples étalons).

## Structure

```
config/
  sources.yml       ← URLs surveillées + seuil + mots-clés
  concepts.yml      ← ontologie + voix éditoriale (anti-hallucination)
scripts/            ← watch.py, parsers/*, pdf_processor, synopsis_enricher
site/               ← interface publique (déployée via GitHub Pages)
.github/workflows/  ← run automatique de la veille
```

## Setup

### 1. Secrets GitHub à configurer

Dans `Settings → Secrets and variables → Actions` :

| Secret                       | Description                                  |
|------------------------------|----------------------------------------------|
| `CLAUDE_CODE_OAUTH_TOKEN`    | Token long-lived Claude Code CLI             |
| `RCLONE_CONFIG_B64`          | Config rclone Drive en base64 (optionnel)    |
| `BIBLIO_PUBLISH_TOKEN`       | PAT pour push vers le repo public           |

### 2. Repo public (pages)

Créer un repo public `{{PROJECT_NAME}}-public` qui hébergera le site statique.
Pointer le CNAME `{{SUBDOMAIN}}` vers GitHub Pages.

### 3. DNS Gandi (ou autre)

Ajouter un enregistrement CNAME :
```
{{SUBDOMAIN_PREFIX}}  CNAME  cedricmabilotte.github.io.  (TTL 3600)
```

### 4. Premier run

Dans l'onglet `Actions` du repo privé, déclencher manuellement le workflow
`Veille documentaire`. Le premier run télécharge les PDFs, génère le
catalogue, et publie le site.

## Lancer un run local

```bash
export CLAUDE_CODE_OAUTH_TOKEN=...
export SCORE_THRESHOLD=7
python scripts/watch.py
python scripts/pdf_processor.py
python scripts/synopsis_enricher.py
```

## Personnaliser l'ontologie

Édite `config/concepts.yml` : remplis les sections `core_concepts`,
`related_concepts`, `anti_concepts` et `custom_examples`. C'est ce qui
permet au scoreur Claude de désambiguïser les faux amis spécifiques à
ta thématique.

## Documentation du système

[github.com/CedricMabilotte/veille-documentaire](https://github.com/CedricMabilotte/veille-documentaire)
"""


GITIGNORE_TEMPLATE = """# Caches Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Environnements
.venv/
venv/
.env

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Fichiers temporaires
*.tmp
*.swp
*~

# Documents lourds : versionnés via Drive (rclone) — pas dans git
# Décommenter si tu veux exclure :
# docs/*.pdf
# docs/*.epub
"""


SOURCES_TEMPLATE = """# ── Seuil de pertinence ─────────────────────────────────────────────────────
# Score minimum (0-10) pour qu'un document soit téléchargé. Voir
# config/concepts.yml → scoring.threshold pour la valeur canonique.
threshold: 7

# ── Mots-clés de veille (multilingues FR + EN + ES) ──────────────────────────
# Ces mots-clés servent au pré-filtrage AVANT scoring Claude. Ils doivent
# couvrir le champ lexical des core_concepts définis dans concepts.yml.
# À COMPLÉTER après avoir précisé l'ontologie.
keywords:
  # Français
  - À COMPLÉTER

  # English
  - TODO

  # Español
  - POR HACER

# ── Sources à surveiller ─────────────────────────────────────────────────────
# Types disponibles : html | deep_html | opds | archive_org | hal | playwright
# Voir scripts/parsers/ pour les implémentations.
sources:
  # Exemple 1 — page HTML simple
  - label: "Exemple — page d'index"
    url: "https://example.org/articles/"
    type: html

  # Exemple 2 — crawl 2-niveaux (page d'index + pages d'articles)
  - label: "Exemple — bibliothèque deep crawl"
    url: "https://example.org/library"
    type: deep_html
    max_pages: 15

  # Exemple 3 — recherche Archive.org
  - label: "Exemple — Archive.org subject:{{PROJECT_NAME}}"
    url: "https://archive.org/advancedsearch.php?q=subject%3A{{PROJECT_NAME}}+AND+mediatype%3Atexts&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=creator&fl%5B%5D=description&output=json&rows=50"
    type: archive_org
"""


# ═════════════════════════════════════════════════════════════════════════════
# 3. Helpers de copie / substitution
# ═════════════════════════════════════════════════════════════════════════════
def _copy_file(src: Path, dst: Path) -> None:
    """Copie binaire fidèle, en créant les dossiers parents au besoin."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _write_text(path: Path, content: str) -> None:
    """Écrit un fichier texte UTF-8 en créant les dossiers parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _apply_site_substitutions(text: str, ctx: dict[str, str]) -> str:
    """
    Substitutions sur le contenu des fichiers du site.

    On remplace les chaînes en dur du site BIBLIO de référence par les
    valeurs du nouveau projet. C'est pragmatique (pas un vrai moteur de
    template) mais c'est suffisant pour le site actuel.
    """
    display = ctx["DISPLAY_NAME"]
    tagline = ctx["TAGLINE"]
    sub = ctx["SUBDOMAIN"]
    project = ctx["PROJECT_NAME"]
    short = ctx["BRAND_SHORT"]
    description = ctx["DESCRIPTION"]

    rules = [
        # Domaine canonique
        ("biblio.actitude.org", sub),
        # Marque courte affichée dans le header / footer / titres
        # On remplace les apparitions isolées de "BIBLIO" en gardant la sémantique.
        (">BIBLIO<", f">{short}<"),
        ("BIBLIO — Bibliothèque documentaire ouverte", f"{display} — Bibliothèque documentaire ouverte"),
        ("BIBLIO — bibliothèque documentaire ouverte", f"{display} — bibliothèque documentaire ouverte"),
        ("BIBLIO — Nouvelles fiches", f"{short} — Nouvelles fiches"),
        ("Méthodologie — BIBLIO", f"Méthodologie — {short}"),
        ("Catalogue — BIBLIO", f"Catalogue — {short}"),
        ("name=\"BIBLIO", f"name=\"{short}"),
        # Attributs aria-label
        ('aria-label="BIBLIO', f'aria-label="{short}'),
        # manifest.json — short_name (chaîne JSON exacte)
        ('"short_name": "BIBLIO"', f'"short_name": "{short}"'),
        ('"name": "BIBLIO — Bibliothèque documentaire ouverte"', f'"name": "{display}"'),
        # Description du manifest
        (
            '"Veille documentaire ouverte sur les communs, la propriété d\'usage et les paysanneries."',
            f'"{description}"',
        ),
        # Tagline et descriptions
        (
            "Bibliothèque documentaire ouverte sur les communs, la propriété d'usage et les paysanneries.",
            description,
        ),
        ("Bibliothèque documentaire ouverte.<br>Communs, terres, paysanneries.", tagline.replace(". ", ".<br>")),
        (
            "Une veille documentaire ouverte sur les communs, la propriété d'usage, la libération des terres et les paysanneries. Fiches, citations, méthodologie transparente.",
            description,
        ),
        (
            "Communs, terres, paysanneries — une veille documentaire ouverte. Un projet de actitude.org.",
            f"{tagline} — Un projet de actitude.org.",
        ),
        (
            "Veille documentaire ouverte sur les communs, la propriété d'usage et les paysanneries.",
            description,
        ),
        (
            "Veille documentaire : communs, terres, paysanneries",
            description,
        ),
        # Lien vers le code source (on garde le repo système comme doc)
        # mais on note le projet courant
        ("biblio-actitude-org", f"{project}-public"),
        # Code colophon
        ("<code>biblio.actitude.org</code>", f"<code>{sub}</code>"),
    ]
    out = text
    for old, new in rules:
        out = out.replace(old, new)
    return out


def _apply_workflow_substitutions(text: str, ctx: dict[str, str]) -> str:
    """Adapte le workflow GitHub Actions au repo public cible."""
    project = ctx["PROJECT_NAME"]
    # Remplace le nom du repo public cible
    out = text.replace(
        "CedricMabilotte/biblio-actitude-org.git",
        f"CedricMabilotte/{project}-public.git",
    )
    out = out.replace(
        "https://biblio.actitude.org",
        f"https://{ctx['SUBDOMAIN']}",
    )
    out = out.replace(
        "cedricmabilotte.github.io/biblio-actitude-org",
        f"cedricmabilotte.github.io/{project}-public",
    )
    return out


def _apply_manifest_substitutions(text: str, ctx: dict[str, str]) -> str:
    """Substitutions JSON pour manifest.json (theme color depuis la palette)."""
    palette = ctx["_palette"]
    out = text
    out = out.replace('"#a44a2c"', f'"{palette["primary"]}"')
    out = out.replace('"#f7f2e7"', f'"{palette["bg"]}"')
    return out


# ═════════════════════════════════════════════════════════════════════════════
# 4. Étapes principales du scaffolding
# ═════════════════════════════════════════════════════════════════════════════
def scaffold_scripts(target: Path) -> None:
    """Copie scripts/*.py + scripts/parsers/*.py."""
    print("  → scripts/")
    src_scripts = REPO_ROOT / "scripts"
    for name in SCRIPT_FILES:
        src = src_scripts / name
        if not src.exists():
            print(f"    [skip] {name} (introuvable dans le repo source)")
            continue
        _copy_file(src, target / "scripts" / name)

    src_parsers = src_scripts / "parsers"
    for name in PARSER_FILES:
        src = src_parsers / name
        if not src.exists():
            print(f"    [skip] parsers/{name}")
            continue
        _copy_file(src, target / "scripts" / "parsers" / name)


def scaffold_workflow(target: Path, ctx: dict) -> None:
    """Copie .github/workflows/watch.yml en l'adaptant."""
    print("  → .github/workflows/watch.yml")
    src = REPO_ROOT / ".github" / "workflows" / "watch.yml"
    text = src.read_text(encoding="utf-8")
    text = _apply_workflow_substitutions(text, ctx)
    _write_text(target / ".github" / "workflows" / "watch.yml", text)


def scaffold_site(target: Path, ctx: dict) -> None:
    """Copie le site/ en substituant marque/domaine/logo."""
    print("  → site/")
    for rel in SITE_FILES_RECURSIVE:
        src = REPO_ROOT / rel
        if not src.exists():
            print(f"    [skip] {rel}")
            continue
        dst = target / rel
        # Fichiers texte → on substitue ; binaires (png) → on copie tel quel
        if src.suffix.lower() in {".html", ".css", ".js", ".xml", ".json", ".txt", ".svg"}:
            text = src.read_text(encoding="utf-8")
            if rel.endswith("manifest.json"):
                text = _apply_manifest_substitutions(text, ctx)
            text = _apply_site_substitutions(text, ctx)
            _write_text(dst, text)
        else:
            _copy_file(src, dst)

    # CNAME : on écrit la valeur exacte du subdomain choisi
    _write_text(target / "site" / "CNAME", ctx["SUBDOMAIN"] + "\n")

    # Logo et favicon : régénérés à partir de la palette du projet
    palette = ctx["_palette"]
    initial = ctx["BRAND_SHORT"][:1].upper()
    logo = generate_simple_logo_svg(initial, palette["primary"], palette["secondary"])
    favicon = generate_simple_favicon_svg(palette["primary"], palette["secondary"], palette["bg"])
    _write_text(target / "site" / "assets" / "img" / "logo.svg", logo)
    _write_text(target / "site" / "assets" / "img" / "favicon.svg", favicon)


def scaffold_config(target: Path, ctx: dict) -> None:
    """Écrit config/sources.yml (squelette) et config/concepts.yml (rempli)."""
    print("  → config/sources.yml")
    sources_text = SOURCES_TEMPLATE.replace("{{PROJECT_NAME}}", ctx["PROJECT_NAME"])
    _write_text(target / "config" / "sources.yml", sources_text)

    print("  → config/concepts.yml")
    template_path = REPO_ROOT / "config" / "concepts.yml.template"
    template_text = template_path.read_text(encoding="utf-8")
    mapping = {
        "PROJECT_NAME": ctx["PROJECT_NAME"],
        "PROJECT_DISPLAY_NAME": ctx["DISPLAY_NAME"],
        "PROJECT_TAGLINE": ctx["TAGLINE"],
        "PROJECT_DESCRIPTION": ctx["DESCRIPTION"],
        "EDITORIAL_VOICE": "militant+académique",
        "EDITORIAL_AUDIENCE": "Militant·es, chercheur·ses, journalistes intéressé·es par la thématique.",
    }
    concepts_text = substitute_placeholders(template_text, mapping)
    _write_text(target / "config" / "concepts.yml", concepts_text)


def scaffold_meta_files(target: Path, ctx: dict) -> None:
    """README.md + .gitignore + .gitkeep dans les dossiers de données."""
    print("  → README.md, .gitignore, .gitkeep")
    subdomain_prefix = ctx["SUBDOMAIN"].split(".")[0]
    readme = substitute_placeholders(
        README_TEMPLATE,
        {
            "DISPLAY_NAME": ctx["DISPLAY_NAME"],
            "TAGLINE": ctx["TAGLINE"],
            "SUBDOMAIN": ctx["SUBDOMAIN"],
            "SUBDOMAIN_PREFIX": subdomain_prefix,
            "PROJECT_NAME": ctx["PROJECT_NAME"],
        },
    )
    _write_text(target / "README.md", readme)
    _write_text(target / ".gitignore", GITIGNORE_TEMPLATE)
    for d in GITKEEP_DIRS:
        _write_text(target / d / ".gitkeep", "")


# ═════════════════════════════════════════════════════════════════════════════
# 5. Initialisation Git + GitHub + Gandi (optionnel)
# ═════════════════════════════════════════════════════════════════════════════
def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Wrapper subprocess avec affichage."""
    print(f"    $ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def init_git_and_github(target: Path, ctx: dict) -> None:
    """
    git init + premier commit + création repos via `gh` + CNAME Gandi.
    Best-effort : on log les erreurs sans tout casser.
    """
    project = ctx["PROJECT_NAME"]
    try:
        _run(["git", "init", "-b", "main"], cwd=target)
        _run(["git", "add", "-A"], cwd=target)
        _run(
            ["git", "commit", "-m", f"init: scaffold {project} via new_project.py"],
            cwd=target,
        )
    except subprocess.CalledProcessError as e:
        print(f"    [git] erreur : {e.stderr}")
        return

    # Repos GitHub via gh
    try:
        _run(
            ["gh", "repo", "create", project, "--private", "--source=.", "--push"],
            cwd=target,
        )
    except subprocess.CalledProcessError as e:
        print(f"    [gh private] erreur : {e.stderr}")

    try:
        _run(
            ["gh", "repo", "create", f"{project}-public", "--public"],
            cwd=target,
        )
    except subprocess.CalledProcessError as e:
        print(f"    [gh public] erreur : {e.stderr}")

    # Gandi DNS — si GANDI_PAT exporté
    gandi_pat = os.environ.get("GANDI_PAT")
    if not gandi_pat:
        print("    [gandi] GANDI_PAT non exporté → skip DNS")
        return
    sub = ctx["SUBDOMAIN"]
    parts = sub.split(".")
    if len(parts) < 3:
        print(f"    [gandi] subdomain '{sub}' inattendu → skip")
        return
    prefix = parts[0]
    domain = ".".join(parts[1:])
    try:
        import json
        import urllib.request

        req = urllib.request.Request(
            f"https://api.gandi.net/v5/livedns/domains/{domain}/records",
            method="POST",
            data=json.dumps({
                "rrset_name": prefix,
                "rrset_type": "CNAME",
                "rrset_ttl": 3600,
                "rrset_values": ["cedricmabilotte.github.io."],
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {gandi_pat}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"    [gandi] CNAME {prefix}.{domain} créé (HTTP {resp.status})")
    except Exception as e:
        print(f"    [gandi] erreur API : {e}")


# ═════════════════════════════════════════════════════════════════════════════
# 6. CLI
# ═════════════════════════════════════════════════════════════════════════════
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scaffolde un nouvel agent de veille thématique.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--name", required=True, help="Slug url-safe (ex: feminismes-decoloniaux)")
    p.add_argument("--display", help="Nom affiché (défaut : dérivé du slug)")
    p.add_argument("--tagline", required=True, help="Phrase courte qui résume la thématique")
    p.add_argument("--subdomain", required=True, help="ex: feminismes.actitude.org")
    p.add_argument("--target-dir", required=True, help="Dossier cible (créé si absent)")
    p.add_argument("--description", help="Description longue (défaut : tagline étendue)")
    p.add_argument(
        "--brand-short",
        help="Nom court affiché dans le header (défaut : premier mot du display en MAJ)",
    )
    p.add_argument("--init-git", action="store_true", help="git init + gh repo create + Gandi DNS")
    p.add_argument("--force", action="store_true", help="Écraser un target-dir non vide")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    slug = args.name.strip().lower()
    if not SLUG_RE.match(slug):
        print(f"[!] --name doit être un slug url-safe (kebab-case). Reçu : '{slug}'", file=sys.stderr)
        return 2

    display = args.display or slug_to_title(slug)
    tagline = args.tagline.strip()
    description = (args.description or tagline).strip()
    sub = args.subdomain.strip().lower()
    # Marque courte : premier mot du display, en majuscules
    brand_short = (
        args.brand_short.strip().upper()
        if args.brand_short
        else display.split()[0].upper()
    )

    target = Path(args.target_dir).expanduser().resolve()
    if target.exists() and any(target.iterdir()) and not args.force:
        print(f"[!] target-dir '{target}' existe et n'est pas vide. Utilise --force pour écraser.", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)

    palette = pick_palette(slug)

    ctx = {
        "PROJECT_NAME": slug,
        "DISPLAY_NAME": display,
        "TAGLINE": tagline,
        "DESCRIPTION": description,
        "SUBDOMAIN": sub,
        "BRAND_SHORT": brand_short,
        "_palette": palette,
    }

    print("─" * 70)
    print(f"Scaffolding agent de veille → {target}")
    print(f"  Slug      : {slug}")
    print(f"  Display   : {display}")
    print(f"  Marque    : {brand_short}")
    print(f"  Tagline   : {tagline}")
    print(f"  Subdomain : {sub}")
    print(f"  Palette   : primary={palette['primary']}  secondary={palette['secondary']}")
    print("─" * 70)

    scaffold_scripts(target)
    scaffold_workflow(target, ctx)
    scaffold_site(target, ctx)
    scaffold_config(target, ctx)
    scaffold_meta_files(target, ctx)

    if args.init_git:
        print("─" * 70)
        print("Initialisation git + GitHub + Gandi…")
        init_git_and_github(target, ctx)

    print("─" * 70)
    print(f"✓ Agent scaffoldé : {target}")
    print("Étapes suivantes :")
    print(f"  1. cd {target}")
    print("  2. Éditer config/concepts.yml (sections 'À COMPLÉTER')")
    print("  3. Éditer config/sources.yml (URLs réelles + mots-clés)")
    print("  4. Configurer les secrets GitHub (voir README.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
