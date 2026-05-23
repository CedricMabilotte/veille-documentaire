#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_site.py — Génère le site public « Terres Libérées ».

Fork de Résidence. À partir des fiches YAML (lieux/ porteurs/ usufruitiers/
modeles/) et de la configuration (config/), produit un site statique :
accueil, catalogues par catégorie, fiches détaillées, classement par l'Indice
de libération, pages grilles / modèles / méthode.

Aucune dépendance hors PyYAML. Usage : python3 scripts/generate_site.py
"""
from __future__ import annotations
import datetime
import html
import json
import math
import re
import shutil
import unicodedata
from pathlib import Path

import yaml

# Date de génération du site — affichée en pied de page et dans le sitemap.
BUILD_DATE = datetime.date.today().isoformat()

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
SITE = ROOT / "site"
ASSETS = SITE / "assets"

CAT_DIR = {"lieu": "lieux", "porteur": "porteurs",
           "usufruitier": "usufruitiers", "modele": "modeles"}
CAT_SLUG = {"lieu": "l", "porteur": "p", "usufruitier": "u", "modele": "m"}
CAT_PAGE = {"lieu": "lieux.html", "porteur": "porteurs.html",
            "usufruitier": "usufruitiers.html", "modele": "modeles.html"}

# ─────────────────────────────────────────────────────────────────────────────
# Chargement
# ─────────────────────────────────────────────────────────────────────────────

def load_yaml(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_config():
    return {
        "concepts": load_yaml(CONFIG / "concepts.yml"),
        "grilles": load_yaml(CONFIG / "grilles.yml"),
        "ranking": load_yaml(CONFIG / "ranking.yml"),
    }


def load_fiches():
    fiches = []
    for cat, d in CAT_DIR.items():
        folder = ROOT / d
        if not folder.exists():
            continue
        for fp in sorted(folder.glob("*.yml")):
            data = load_yaml(fp)
            if not data:
                continue
            data.setdefault("categorie", cat)
            data["_file"] = fp.name
            fiches.append(data)
    return fiches


# ─────────────────────────────────────────────────────────────────────────────
# Scoring — l'Indice de libération
# ─────────────────────────────────────────────────────────────────────────────

def grille_index(grilles_cfg):
    """Renvoie {categorie: {critere_id: {axe, poids, label, definition}}}."""
    idx = {}
    for cat, gril in grilles_cfg["grilles"].items():
        cmap = {}
        for fam in gril["familles"]:
            for cr in fam["criteres"]:
                cmap[cr["id"]] = {"axe": cr["axe"], "poids": cr["poids"],
                                  "label": cr["label"], "definition": cr["definition"],
                                  "famille": fam["label"]}
        idx[cat] = cmap
    return idx


def score_fiche(fiche, gidx, ranking):
    """Calcule axes A/B/C (0-100), Indice global, palier, complétude."""
    valeurs = ranking["valeurs"]
    cat = fiche["categorie"]

    if cat == "modele":
        ax = fiche.get("axes_estimes", {}) or {}
        axes = {k: (float(ax[k]) if ax.get(k) is not None else None)
                for k in ("A", "B", "C")}
        known = [v for v in axes.values() if v is not None]
        idl = round(sum(known) / len(known)) if known else None
        return {"axes": axes, "idl": idl, "idl_brut": idl,
                "palier": palier_for(idl, ranking),
                "completude": None, "estime": True,
                "score_type": "estime", "criteres_evalues": {}}

    cmap = gidx.get(cat, {})
    acc = {"A": [0.0, 0.0], "B": [0.0, 0.0], "C": [0.0, 0.0]}  # [poids_total, poids_obtenu]
    n_total = len(cmap)
    n_known = 0
    criteres_evalues = {}
    for entry in fiche.get("grille", []) or []:
        cid = entry.get("critere")
        if cid not in cmap:
            continue
        meta = cmap[cid]
        val = entry.get("valeur", "inconnu")
        criteres_evalues[cid] = {"valeur": val, "note": entry.get("note", ""),
                                 **meta}
        factor = valeurs.get(val)
        if factor is None:  # inconnu → exclu
            continue
        n_known += 1
        axe = meta["axe"]
        acc[axe][0] += meta["poids"]
        acc[axe][1] += meta["poids"] * factor

    axes = {}
    for axe, (wtot, wobt) in acc.items():
        axes[axe] = round(wobt / wtot * 100) if wtot > 0 else None

    known = [v for v in axes.values() if v is not None]
    idl_brut = round(sum(known) / len(known)) if known else None
    completude = (n_known / n_total) if n_total else 0.0
    # Pénalité de complétude : l'indice affiché est l'indice brut pondéré par la
    # complétude, pour ne pas surnoter les fiches lacunaires (cf. ranking.yml).
    if idl_brut is not None:
        idl = round(idl_brut * (0.5 + 0.5 * completude))
    else:
        idl = None
    return {"axes": axes, "idl": idl, "idl_brut": idl_brut,
            "palier": palier_for(idl, ranking),
            "completude": completude, "estime": False,
            "score_type": "calcule", "criteres_evalues": criteres_evalues}


def palier_for(idl, ranking):
    if idl is None:
        return None
    for p in ranking["paliers"]:  # ordonnés du plus haut au plus bas
        if idl >= p["min"]:
            return p
    return ranking["paliers"][-1]


def fiabilite_label(completude, ranking):
    if completude is None:
        return ("Estimation comparative", "faint")
    seuils = ranking["fiabilite"]
    if completude >= seuils["seuil_completude_bon"]:
        return ("Fiche bien renseignée", "ok")
    if completude >= seuils["seuil_completude_moyen"]:
        return ("Fiche fiable avec réserves", "gold")
    return ("Fiche à compléter", "faint")


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires HTML
# ─────────────────────────────────────────────────────────────────────────────

def e(x):
    return html.escape(str(x)) if x is not None else ""


def clean(text):
    """Replie les textes YAML multi-lignes."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def slugify(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "x"


def meta_desc(text, limit=155):
    """Tronque une description à ~155 caractères sur une frontière de mot."""
    t = clean(text)
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.")
    return cut + "…"


# ─────────────────────────────────────────────────────────────────────────────
# Gabarit de page
# ─────────────────────────────────────────────────────────────────────────────

NAV = [
    ("index.html", "Accueil"),
    ("lieux.html", "Lieux"),
    ("porteurs.html", "Porteurs"),
    ("usufruitiers.html", "Usufruitiers"),
    ("classement.html", "Classement"),
    ("grilles.html", "Grilles"),
    ("modeles.html", "Modèles voisins"),
    ("glossaire.html", "Glossaire"),
    ("methode.html", "Méthode"),
]

# URL canonique de base (sans barre oblique finale). Lue depuis concepts.yml.
BASE_URL = "https://communs.actitude.org"


def canonical_url(path):
    """URL absolue d'une page. L'accueil canonicalise vers la racine."""
    if path in ("", "index.html"):
        return BASE_URL + "/"
    return BASE_URL + "/" + path.lstrip("/")


def page(title, body, active, depth=0, project=None, description="",
         path="", jsonld=None, og_type="website", robots=None):
    up = "../" * depth
    nav = "".join(
        f'<a href="{up}{href}"{" class=\'active\'" if href == active else ""}>{e(label)}</a>'
        for href, label in NAV
    )
    pname = project["display_name"] if project else "Terres Libérées"
    mark = project["logo_mark"] if project else "TL"
    base = project["tagline"] if project else ""
    desc = e(meta_desc(description or base))
    canon = canonical_url(path)
    og_img = BASE_URL + "/assets/og-default.svg"
    full_title = f"{title} — {pname}"

    # données structurées JSON-LD
    ld = ""
    for block in (jsonld or []):
        ld += ('\n<script type="application/ld+json">'
               + json.dumps(block, ensure_ascii=False) + "</script>")

    robots_tag = f'\n<meta name="robots" content="{e(robots)}">' if robots else ""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#221f1a">{robots_tag}
<link rel="canonical" href="{e(canon)}">
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="{e(og_type)}">
<meta property="og:site_name" content="{e(pname)}">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{e(canon)}">
<meta property="og:image" content="{e(og_img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(full_title)}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{e(og_img)}">
<link rel="stylesheet" href="{up}assets/style.css">{ld}
</head>
<body>
<a class="skiplink" href="#contenu">Aller au contenu</a>
<header class="masthead">
  <div class="wrap">
    <a class="brand" href="{up}index.html">
      <span class="logo-mark">{e(mark)}</span>
      <span class="brand-txt"><span class="brand-name">{e(pname)}</span>
      <span class="baseline">{e(base)}</span></span>
    </a>
    <nav class="topnav">{nav}</nav>
  </div>
</header>
<main class="wrap" id="contenu">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <p>{e(pname)} — annuaire critique des montages de libération des terres en
    France. Données factuelles sourcées ; l'Indice de libération est une grille
    d'analyse explicite, non un jugement de valeur.</p>
    <p class="foot-links"><a href="{up}methode.html">Méthode &amp; sources</a> ·
    <a href="{up}grilles.html">Grilles d'analyse</a> ·
    <a href="{up}glossaire.html">Glossaire</a> ·
    <a href="{up}suggerer.html">Proposer un lieu</a> ·
    <a href="{up}data.json">Données ouvertes (JSON)</a></p>
    <p>Fork de « Résidence » · site statique généré automatiquement le
    {e(BUILD_DATE)}.</p>
  </div>
</footer>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Composants
# ─────────────────────────────────────────────────────────────────────────────

def montage_label(mid, concepts):
    if not mid:
        return "—"
    for m in concepts["montages"]:
        if m["id"] == mid:
            return m["label"]
    return mid


def _fmtnum(val):
    """Affiche un nombre sans décimale parasite (90.0 → 90)."""
    if val is None:
        return "—"
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val)


def axis_bar(axes_cfg, axes_scores, compact=False):
    """Barres horizontales des trois axes — lecture chiffrée précise."""
    rows = []
    for ax in axes_cfg:
        aid = ax["id"]
        val = axes_scores.get(aid)
        col = ax["couleur"]
        if val is None:
            w, txt, cls = 0, "n.r.", "axis-na"
        else:
            w, txt, cls = _fmtnum(val), _fmtnum(val), ""
        rows.append(f"""<div class="axis-row">
  <span class="axis-label" title="{e(clean(ax['question']))}">{e(ax['id'])} · {e(ax['label'])}</span>
  <span class="axis-track"><span class="axis-fill {cls}" style="width:{w}%;background:{col}"></span></span>
  <span class="axis-val">{e(txt)}</span>
</div>""")
    cls = "axis-block compact" if compact else "axis-block"
    return f'<div class="{cls}">' + "".join(rows) + "</div>"


# ── Triangle de profil tri-axes (SVG inline) ─────────────────────────────────

def _tri_geom(size=120):
    """Sommets équilatéraux (A haut, B bas-droite, C bas-gauche) et centre G."""
    cx, cy, r = size / 2, size * 0.46, size * 0.42
    verts = {}
    for i, ax in enumerate(("A", "B", "C")):
        ang = -math.pi / 2 + i * 2 * math.pi / 3
        verts[ax] = (cx + r * math.cos(ang), cy + r * math.sin(ang))
    return (cx, cy), verts


def axis_triangle(axes_cfg, axes_scores, size=120, compact=False):
    """Petit SVG : cadre équilatéral 100 %, polygone des trois scores A/B/C."""
    (gx, gy), verts = _tri_geom(size)
    col = {ax["id"]: ax["couleur"] for ax in axes_cfg}
    pts, missing = [], []
    for ax in ("A", "B", "C"):
        v = axes_scores.get(ax)
        vx, vy = verts[ax]
        if v is None:
            missing.append(ax)
            f = 0.0
        else:
            f = max(0.0, min(1.0, v / 100))
        pts.append(f"{gx + (vx - gx) * f:.1f},{gy + (vy - gy) * f:.1f}")
    frame = " ".join(f"{x:.1f},{y:.1f}" for x, y in verts.values())
    mid = " ".join(f"{gx + (x - gx) * 0.5:.1f},{gy + (y - gy) * 0.5:.1f}"
                   for x, y in verts.values())
    axname = {"A": "intérêt général", "B": "libération des terres",
              "C": "gouvernance participative"}
    label = "Profil tri-axes — " + ", ".join(
        f"{axname[a]} "
        f"{_fmtnum(axes_scores.get(a)) if axes_scores.get(a) is not None else 'non renseigné'}"
        for a in ("A", "B", "C"))
    dots = ""
    for ax in ("A", "B", "C"):
        vx, vy = verts[ax]
        # léger décalage du sommet vers l'extérieur pour la lettre
        lx = gx + (vx - gx) * 1.0
        ly = gy + (vy - gy) * 1.0
        na = " tri-na" if ax in missing else ""
        dots += (f'<circle class="tri-vtx{na}" cx="{vx:.1f}" cy="{vy:.1f}" '
                 f'r="5" fill="{col[ax]}"/>'
                 f'<text class="tri-lab" x="{lx:.1f}" y="{ly:.1f}">{ax}</text>')
    cls = "tri compact" if compact else "tri"
    # Compact (cartes / chips) : SVG décoratif — axis_bar fournit déjà les
    # chiffres A/B/C en texte. Pleine taille (fiche) : seule source accessible.
    if compact:
        a11y = 'aria-hidden="true" focusable="false"'
    else:
        a11y = f'role="img" aria-label="{e(label)}"'
    return (f'<svg class="{cls}" viewBox="0 0 {size} {size * 0.92:.0f}" {a11y}>'
            f'<polygon class="tri-frame" points="{frame}"/>'
            f'<polygon class="tri-grid" points="{mid}"/>'
            f'<polygon class="tri-fill" points="{" ".join(pts)}"/>'
            f'{dots}</svg>')


# ── Badge d'Indice : anneau de progression SVG ───────────────────────────────

def idl_badge(sc, big=False):
    """Anneau de progression. Le SVG est décoratif (aria-hidden) : l'indice et le
    palier sont déjà disponibles en texte, doublés d'un libellé masqué accessible."""
    idl = sc["idl"]
    pal = sc["palier"]
    if idl is None or pal is None:
        return ('<span class="idl-badge idl-na">n.r.'
                '<span class="visually-hidden">Indice non renseigné</span></span>')
    estime = sc.get("score_type") == "estime"
    r, sw = (34, 7) if big else (16, 4)
    c = 2 * math.pi * r
    off = c * (1 - idl / 100)
    box = (r + sw) * 2
    cls = "idl-badge big" if big else "idl-badge"
    if estime:
        cls += " idl-estime"
    pal_lab = e(pal["label"]) + (" · estimé" if estime else "")
    num_sz = "1.6rem" if big else ".82rem"
    sr = (f'<span class="visually-hidden">Indice de libération {idl} sur 100, '
          f'{e(pal["label"])}{" (estimé)" if estime else ""}.</span>')
    return (
        f'<span class="{cls}" style="--pal:{pal["couleur"]}">'
        f'<svg class="idl-ring" viewBox="0 0 {box} {box}" aria-hidden="true" '
        f'focusable="false">'
        f'<circle class="idl-track" cx="{box / 2}" cy="{box / 2}" r="{r}" '
        f'stroke-width="{sw}"/>'
        f'<circle class="idl-arc" cx="{box / 2}" cy="{box / 2}" r="{r}" '
        f'stroke-width="{sw}" stroke-dasharray="{c:.1f}" '
        f'stroke-dashoffset="{off:.1f}" '
        f'transform="rotate(-90 {box / 2} {box / 2})"/>'
        f'<text class="idl-num" x="{box / 2}" y="{box / 2}" '
        f'style="font-size:{num_sz}">{idl}</text>'
        f'</svg>{sr}'
        f'<span class="idl-pal">{pal_lab}</span></span>')


def idl_scale(sc, ranking):
    """Jauge linéaire 0-100 avec bandes de palier et curseur (panneau de score)."""
    idl = sc["idl"]
    if idl is None:
        return ""
    paliers = sorted(ranking["paliers"], key=lambda p: p["min"])
    segs = ""
    for i, p in enumerate(paliers):
        left = p["min"]
        right = paliers[i + 1]["min"] if i + 1 < len(paliers) else 100
        segs += (f'<span class="idl-seg" style="left:{left}%;'
                 f'width:{right - left}%;background:{p["couleur"]}" '
                 f'title="{e(p["label"])} (≥ {p["min"]})"></span>')
    brut = sc.get("idl_brut")
    ghost = ""
    if brut is not None and brut != idl:
        ghost = (f'<span class="idl-ghost" style="left:{brut}%" '
                 f'title="Indice brut {brut}, avant pénalité de complétude"></span>')
    return (f'<div class="idl-scale" aria-hidden="true">'
            f'<span class="idl-scale-track">{segs}{ghost}'
            f'<span class="idl-cursor" style="left:{idl}%"></span></span>'
            f'<span class="idl-scale-ends"><span>0</span><span>100</span></span>'
            f'</div>')


def corpus_histogram(all_sc, ranking):
    """Histogramme SVG de la distribution des entrées notées par palier."""
    paliers = ranking["paliers"]
    counts = {p["id"]: 0 for p in paliers}
    for f, s in all_sc:
        if f["categorie"] == "modele":
            continue
        if s["palier"]:
            counts[s["palier"]["id"]] += 1
    total = sum(counts.values())
    mx = max(counts.values()) or 1
    W, H, pad = 360, 180, 30
    bw = (W - 2 * pad) / len(paliers)
    bars = ""
    for i, p in enumerate(reversed(paliers)):  # bas → haut de l'échelle
        n = counts[p["id"]]
        bh = (H - 2 * pad - 14) * n / mx
        x = pad + i * bw
        y = H - pad - bh
        bars += (f'<rect class="hg-bar" x="{x + 8:.1f}" y="{y:.1f}" '
                 f'width="{bw - 16:.1f}" height="{max(bh, 0.5):.1f}" '
                 f'fill="{p["couleur"]}" rx="2"/>'
                 f'<text class="hg-n" x="{x + bw / 2:.1f}" y="{y - 5:.1f}">{n}</text>'
                 f'<text class="hg-l" x="{x + bw / 2:.1f}" y="{H - pad + 13:.1f}">'
                 f'{e(p["label"])}</text>')
    return (f'<figure class="corpus-hist"><svg viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="Répartition des {total} entrées notées '
            f'par palier d\'Indice de libération">{bars}</svg>'
            f'<figcaption>Répartition des {total} entrées notées par palier '
            f'd\'Indice de libération (modèles voisins exclus).</figcaption>'
            f'</figure>')


def grille_recap(criteres_evalues, gril, axes_cfg):
    """Bandeau récapitulatif : part de oui/partiel/non/inconnu par axe."""
    order = ["oui", "partiel", "non", "inconnu"]
    olab = {"oui": "oui", "partiel": "partiel", "non": "non", "inconnu": "inconnu"}
    seg_col = {"oui": "var(--green)", "partiel": "var(--gold)",
               "non": "var(--terra)", "inconnu": "#cfc6b0"}
    rows = ""
    for ax in axes_cfg:
        crit_ids = [cr["id"] for fam in gril.get("familles", [])
                    for cr in fam["criteres"] if cr["axe"] == ax["id"]]
        if not crit_ids:
            continue
        tally = {k: 0 for k in order}
        for cid in crit_ids:
            ev = criteres_evalues.get(cid)
            tally[ev["valeur"] if ev else "inconnu"] += 1
        tot = sum(tally.values()) or 1
        segs, txt = "", []
        for k in order:
            if not tally[k]:
                continue
            segs += (f'<span class="rk-seg" style="width:{tally[k] / tot * 100:.1f}%;'
                     f'background:{seg_col[k]}" title="{tally[k]} {olab[k]}"></span>')
            txt.append(f"{tally[k]} {olab[k]}")
        rows += (f'<div class="rk-row"><span class="rk-ax">'
                 f'<span class="axe-dot axe-{ax["id"]}" aria-hidden="true"></span>'
                 f'{ax["id"]} · {e(ax["label"])}</span>'
                 f'<span class="rk-bar" aria-hidden="true">{segs}</span>'
                 f'<span class="rk-txt">{e(" · ".join(txt))}</span></div>')
    return f'<div class="grille-recap">{rows}</div>'


def card(fiche, sc, axes_cfg, depth=0, concepts=None):
    up = "../" * depth
    cat = fiche["categorie"]
    href = f'{up}{CAT_SLUG[cat]}/{fiche["uid"]}.html'
    loc = ""
    region = ""
    if fiche.get("localisation"):
        l = fiche["localisation"]
        loc = " · ".join(x for x in [l.get("commune"), l.get("departement")] if x)
        region = l.get("region", "") or ""
    elif fiche.get("forme_juridique"):
        loc = clean(fiche["forme_juridique"])
    if not loc:
        loc = "Réseau national" if cat == "lieu" else (fiche.get("pays") or "—")
    catlabel = {"lieu": "Lieu", "porteur": "Porteur",
                "usufruitier": "Usufruitier", "modele": "Modèle voisin"}[cat]
    # attributs data-* pour tri / filtres
    mont = fiche.get("montage", {}) or {}
    montage_id = mont.get("type", "") or ""
    montage_lab = montage_label(montage_id, concepts) if (montage_id and concepts) else ""
    pal_id = sc["palier"]["id"] if sc["palier"] else ""
    ax = sc["axes"]
    data = (f'data-idl="{sc["idl"] or 0}" data-nom="{e(fiche["nom"])}" '
            f'data-palier="{e(pal_id)}" data-region="{e(region)}" '
            f'data-montage="{e(montage_id)}" '
            f'data-axa="{ax.get("A") or 0}" data-axb="{ax.get("B") or 0}" '
            f'data-axc="{ax.get("C") or 0}"')
    return f"""<li class="card" {data}>
  <div class="card-head">
    <span class="tag tag-{cat}">{catlabel}</span>
    {idl_badge(sc)}
  </div>
  <h3><a href="{href}">{e(fiche['nom'])}</a></h3>
  <p class="card-sub">{e(clean(fiche.get('sous_titre','')))}</p>
  <p class="card-meta">{e(loc)}{(' · ' + e(montage_lab)) if montage_lab else ''}</p>
  <div class="card-viz">
    {axis_triangle(axes_cfg, sc['axes'], compact=True)}
    {axis_bar(axes_cfg, sc['axes'], compact=True)}
  </div>
</li>"""


def cards_grid(fiches_sc, axes_cfg, depth=0, concepts=None, grid_id=""):
    items = "".join(card(f, sc, axes_cfg, depth, concepts) for f, sc in fiches_sc)
    attr = f' id="{grid_id}"' if grid_id else ""
    return f'<ul class="cards"{attr}>{items}</ul>'


# ─────────────────────────────────────────────────────────────────────────────
# Pages — fiche détaillée
# ─────────────────────────────────────────────────────────────────────────────

def purete_label(niv, ranking):
    for n in ranking["purete_juridique"]["niveaux"]:
        if n["id"] == niv:
            return n["label"], n["sens"]
    return niv or "—", ""


def render_fiche(fiche, sc, cfg, by_uid, sc_by_uid):
    concepts = cfg["concepts"]["concept_central"]
    project = cfg["concepts"]["project"]
    ranking = cfg["ranking"]
    axes_cfg = ranking["axes"]
    grilles = cfg["grilles"]["grilles"]
    cat = fiche["categorie"]
    catlabel = {"lieu": "Lieu", "porteur": "Porteur de nue-propriété",
                "usufruitier": "Organisme usufruitier",
                "modele": "Modèle voisin de référence"}[cat]

    # fil d'Ariane complet : Accueil › Catégorie › Fiche
    head = f"""<nav class="crumb" aria-label="Fil d'Ariane">
  <a href="../index.html">Accueil</a> ›
  <a href="../{CAT_PAGE[cat]}">{e(catlabel)}</a> ›
  <span aria-current="page">{e(fiche['nom'])}</span>
</nav>
<div class="fiche-head">
  <span class="tag tag-{cat}">{e(catlabel)}</span>
  <h1>{e(fiche['nom'])}</h1>
  <p class="fiche-sub">{e(clean(fiche.get('sous_titre', '')))}</p>
</div>"""
    sub = clean(fiche.get("sous_titre", ""))

    # bloc score — triangle de profil + barres chiffrées + jauge linéaire
    flabel, fcls = fiabilite_label(sc["completude"], ranking)
    comp = ""
    if sc["completude"] is not None:
        comp = (f'<p class="completude">Grille renseignée à '
                f'{round(sc["completude"] * 100)} %.')
        if sc.get("idl_brut") is not None and sc["idl_brut"] != sc["idl"]:
            comp += (f' Indice brut {sc["idl_brut"]}, ramené à {sc["idl"]} '
                     f'après pénalité de complétude.')
        comp += "</p>"
    pal_col = sc["palier"]["couleur"] if sc["palier"] else "var(--green)"
    score_block = f"""<section class="score-panel" style="--pal:{pal_col}">
  <div class="score-main">
    <p class="score-cap">Indice de libération</p>
    {idl_badge(sc, big=True)}
    {axis_triangle(axes_cfg, sc['axes'])}
  </div>
  <div class="score-axes">
    {axis_bar(axes_cfg, sc['axes'])}
    {idl_scale(sc, ranking)}
    <p class="fiab fiab-{fcls}">{e(flabel)}</p>
    {comp}
  </div>
</section>"""

    # en bref
    rows = []
    if fiche.get("forme_juridique"):
        rows.append(("Forme juridique", e(clean(fiche["forme_juridique"]))))
    if fiche.get("localisation"):
        l = fiche["localisation"]
        loc = ", ".join(x for x in [l.get("commune"), l.get("departement"),
                                    l.get("region")] if x)
        rows.append(("Localisation", e(loc)))
    if fiche.get("pays"):
        rows.append(("Pays", e(fiche["pays"])))
    if fiche.get("annee"):
        rows.append(("Année", e(fiche["annee"])))
    mont = fiche.get("montage", {}) or {}
    if mont.get("type"):
        rows.append(("Type de montage",
                     e(montage_label(mont["type"], cfg["concepts"]))))
    pj = fiche.get("purete_juridique", {}) or {}
    if pj.get("niveau"):
        plab, psens = purete_label(pj["niveau"], ranking)
        rows.append(("Pureté juridique",
                     f'<span title="{e(psens)}">{e(plab)}</span>'))
    if fiche.get("url"):
        rows.append(("Site", f'<a href="{e(fiche["url"])}" rel="noopener" '
                             f'target="_blank">{e(fiche["url"])}</a>'))
    enbref = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    enbref = f'<section class="enbref"><dl>{enbref}</dl></section>'

    # résumé
    resume = ""
    if fiche.get("resume"):
        resume = (f'<section><h2 class="sec">Présentation</h2>'
                  f'<p class="prose">{e(clean(fiche["resume"]))}</p></section>')

    # montage
    montage_html = ""
    if mont.get("description"):
        extra = []
        if mont.get("nu_proprietaire"):
            extra.append(f'<p><strong>Nue-propriété / propriété :</strong> '
                         f'{e(clean(mont["nu_proprietaire"]))}</p>')
        if mont.get("usufruitier"):
            extra.append(f'<p><strong>Usufruit / usage :</strong> '
                         f'{e(clean(mont["usufruitier"]))}</p>')
        montage_html = (f'<section><h2 class="sec">Le montage</h2>'
                        f'<p class="prose">{e(clean(mont["description"]))}</p>'
                        + "".join(extra) + '</section>')

    # grille détaillée + récapitulatif par axe
    grille_html = ""
    if cat != "modele" and sc["criteres_evalues"]:
        gril = grilles.get(cat, {})
        vmap = {"oui": ("Oui", "crit-oui"), "partiel": ("Partiel", "crit-partiel"),
                "non": ("Non", "crit-non"), "inconnu": ("Inconnu", "crit-inconnu")}
        fam_rows = []
        for fam in gril.get("familles", []):
            trs = []
            for cr in fam["criteres"]:
                ev = sc["criteres_evalues"].get(cr["id"])
                if not ev:
                    val, note = "inconnu", ""
                else:
                    val, note = ev["valeur"], ev["note"]
                vlab, vcls = vmap.get(val, vmap["inconnu"])
                trs.append(f"""<tr>
  <td class="crit-name"><span class="axe-dot axe-{cr['axe']}" title="Axe {cr['axe']}"></span>
      {e(cr['label'])}</td>
  <td class="num">{cr['poids']}</td>
  <td class="{vcls}">{e(vlab)}</td>
  <td class="crit-note">{e(clean(note))}</td>
</tr>""")
            fam_rows.append(f'<tr class="fam-row"><th colspan="4" scope="colgroup">{e(fam["label"])}</th></tr>'
                            + "".join(trs))
        recap = grille_recap(sc["criteres_evalues"], gril, axes_cfg)
        grille_html = f"""<section><h2 class="sec">Grille de lecture</h2>
<p class="grille-intro">{e(clean(gril.get('objet','')))}
<a href="../grilles.html#grille-{cat}">Comprendre la grille →</a></p>
{recap}
<div class="table-scroll"><table class="grille-tbl">
<caption class="visually-hidden">Grille de lecture de la fiche : critère, poids, évaluation et lecture.</caption>
<thead><tr><th scope="col">Critère</th><th scope="col" class="num">Poids</th><th scope="col">Évaluation</th><th scope="col">Lecture</th></tr></thead>
<tbody>{''.join(fam_rows)}</tbody></table></div>
<p class="axe-legend">
<span class="axe-dot axe-A"></span> A — Intérêt général
<span class="axe-dot axe-B"></span> B — Libération des terres
<span class="axe-dot axe-C"></span> C — Gouvernance participative</p>
</section>"""

    # analyse stratégique
    an = fiche.get("analyse", {}) or {}
    def lst(items):
        return "".join(f"<li>{e(clean(x))}</li>" for x in (items or []))
    analyse_html = ""
    if an:
        synth = (f'<p class="prose synthese">{e(clean(an.get("synthese","")))}</p>'
                 if an.get("synthese") else "")
        analyse_html = f"""<section><h2 class="sec">Analyse stratégique</h2>
{synth}
<div class="analyse-grid">
  <div class="an-col an-forces"><h3>Forces</h3><ul>{lst(an.get('forces'))}</ul></div>
  <div class="an-col an-frag"><h3>Fragilités</h3><ul>{lst(an.get('fragilites'))}</ul></div>
  <div class="an-col an-lev"><h3>Leviers</h3><ul>{lst(an.get('leviers'))}</ul></div>
</div></section>"""

    # liens — réciproques : liens déclarés + rétro-liens (fiches qui citent celle-ci)
    liens_html = ""
    liens = fiche.get("liens", {}) or {}
    rel_uids = set()
    for key in ("lieux", "porteurs", "usufruitiers"):
        for uid in liens.get(key, []) or []:
            rel_uids.add(uid)
    # rétro-liens : toute fiche qui cite la fiche courante
    me = fiche["uid"]
    for other_uid, other in by_uid.items():
        if other_uid == me:
            continue
        oliens = other.get("liens", {}) or {}
        for key in ("lieux", "porteurs", "usufruitiers"):
            if me in (oliens.get(key, []) or []):
                rel_uids.add(other_uid)
    chips = []
    for uid in sorted(rel_uids):
        tgt = by_uid.get(uid)
        if not tgt:
            continue
        tcat = tgt["categorie"]
        tsc = sc_by_uid.get(uid)
        tri = (axis_triangle(axes_cfg, tsc["axes"], compact=True)
               if tsc else "")
        chips.append(
            f'<a class="chip chip-rel" href="../{CAT_SLUG[tcat]}/{uid}.html">'
            f'{tri}<span class="chip-txt">{e(tgt["nom"])}'
            f'<span class="chip-cat">{e(tcat)}</span></span></a>')
    if chips:
        liens_html = (f'<section><h2 class="sec">Reliés dans l\'annuaire</h2>'
                      f'<p class="lead">Montages directement reliés à cette '
                      f'fiche ; le profil tri-axes permet la comparaison '
                      f'visuelle.</p>'
                      f'<div class="chips">{"".join(chips)}</div></section>')

    # fiabilité + sources
    fiab = ""
    if fiche.get("fiabilite"):
        fiab = (f'<section class="fiab-box"><h3>Fiabilité des informations</h3>'
                f'<p>{e(clean(fiche["fiabilite"]))}</p></section>')
    src_items = "".join(
        f'<li><a href="{e(s.get("url",""))}" target="_blank" rel="noopener">'
        f'{e(clean(s.get("titre","")))}</a></li>'
        for s in (fiche.get("sources", []) or []))
    sources_html = (f'<section><h2 class="sec">Sources</h2>'
                    f'<ul class="src-list">{src_items}</ul></section>'
                    if src_items else "")

    retlabel = {"lieu": "aux lieux", "porteur": "aux porteurs",
                "usufruitier": "aux usufruitiers",
                "modele": "aux modèles voisins"}[cat]
    backlink = (f'<p class="backlink">'
                f'<a href="../{CAT_PAGE[cat]}">← Retour {retlabel}</a>'
                f' · <a href="../classement.html">Voir le classement</a></p>')
    body = (head + score_block + enbref + resume + montage_html
            + grille_html + analyse_html + liens_html + fiab + sources_html
            + backlink)

    # données structurées : fil d'Ariane + entité principale
    fpath = f"{CAT_SLUG[cat]}/{fiche['uid']}.html"
    fdesc = meta_desc(fiche.get("resume", "") or sub, 250)
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil",
             "item": canonical_url("index.html")},
            {"@type": "ListItem", "position": 2, "name": catlabel,
             "item": canonical_url(CAT_PAGE[cat])},
            {"@type": "ListItem", "position": 3, "name": fiche["nom"]},
        ],
    }
    if cat == "lieu":
        entity = {"@context": "https://schema.org", "@type": "Place",
                  "name": fiche["nom"], "description": fdesc,
                  "url": canonical_url(fpath)}
        loc = fiche.get("localisation") or {}
        if loc:
            addr = {"@type": "PostalAddress", "addressCountry": "FR"}
            if loc.get("commune"):
                addr["addressLocality"] = loc["commune"]
            if loc.get("region"):
                addr["addressRegion"] = loc["region"]
            entity["address"] = addr
    else:
        entity = {"@context": "https://schema.org", "@type": "Organization",
                  "name": fiche["nom"], "description": fdesc,
                  "mainEntityOfPage": canonical_url(fpath)}
        if fiche.get("url"):
            entity["url"] = fiche["url"]
            entity["sameAs"] = [fiche["url"]]
    ogt = "article" if cat != "modele" else "website"
    return page(fiche["nom"], body, CAT_PAGE[cat], depth=1, project=project,
                description=clean(fiche.get("resume", "")) or sub,
                path=fpath, jsonld=[breadcrumb, entity], og_type=ogt)


# ─────────────────────────────────────────────────────────────────────────────
# Pages — catalogues
# ─────────────────────────────────────────────────────────────────────────────

def render_catalogue(cat, fiches_sc, cfg):
    project = cfg["concepts"]["project"]
    concepts = cfg["concepts"]
    axes_cfg = cfg["ranking"]["axes"]
    ranking = cfg["ranking"]
    catdef = next(c for c in concepts["categories"] if c["id"] == cat) \
        if cat != "modele" else None
    if cat == "modele":
        title = "Modèles voisins"
        intro = clean(concepts["modeles_voisins"]["description"])
        modeles_note = (
            '<div class="callout callout-note"><p><strong>Hors classement '
            'principal.</strong> Les modèles voisins ne sont pas notés par les '
            'grilles de l\'annuaire : leur Indice est <em>estimé</em> '
            '(axes posés éditorialement) et signalé par un anneau en pointillé. '
            'Ils servent de points de comparaison et n\'apparaissent pas dans '
            'le classement.</p></div>')
    else:
        title = catdef["label_pluriel"]
        intro = clean(catdef["definition"])
        modeles_note = ""
    fiches_sc = sorted(fiches_sc, key=lambda x: x[1]["idl"] or 0, reverse=True)
    n = len(fiches_sc)

    # filtres par palier
    pal_btns = "".join(
        f'<button class="fbtn" data-fk="palier" data-fv="{p["id"]}">'
        f'{e(p["label"])}</button>' for p in ranking["paliers"])
    # filtres par montage (montages présents dans le sous-ensemble)
    present_mont = []
    for f, _ in fiches_sc:
        m = (f.get("montage", {}) or {}).get("type")
        if m and m not in present_mont:
            present_mont.append(m)
    mont_btns = "".join(
        f'<button class="fbtn" data-fk="montage" data-fv="{m}">'
        f'{e(montage_label(m, concepts))}</button>' for m in present_mont)
    # filtres par région (lieux uniquement)
    region_block = ""
    if cat == "lieu":
        regions = []
        for f, _ in fiches_sc:
            r = (f.get("localisation", {}) or {}).get("region")
            if r and r not in regions:
                regions.append(r)
        if regions:
            reg_btns = "".join(
                f'<button class="fbtn" data-fk="region" data-fv="{e(r)}">'
                f'{e(r)}</button>' for r in sorted(regions))
            region_block = (
                f'<div class="filter-row"><span class="filter-lab">Région</span>'
                f'<button class="fbtn active" data-fk="region" data-fv="all">'
                f'Toutes</button>{reg_btns}</div>')

    body = f"""<h1>{e(title)}</h1>
<p class="lead">{e(intro)}
<a href="methode.html">Comprendre l'Indice et les axes →</a></p>
{modeles_note}
<div class="toolbar">
  <input type="search" id="q" placeholder="Filtrer par nom…" aria-label="Filtrer par nom" aria-controls="resultats">
  <label class="sort-lab" for="sort">Trier :</label>
  <select id="sort">
    <option value="idl">Par indice (décroissant)</option>
    <option value="nom">Par nom (A→Z)</option>
    <option value="axa">Par axe A — intérêt général</option>
    <option value="axb">Par axe B — libération des terres</option>
    <option value="axc">Par axe C — gouvernance</option>
  </select>
  <span class="count" aria-live="polite"><b id="cnt">{n}</b> entrée{'s' if n > 1 else ''}</span>
</div>
<div class="filter-bar">
  <div class="filter-row"><span class="filter-lab">Palier</span>
    <button class="fbtn active" data-fk="palier" data-fv="all">Tous</button>
    {pal_btns}</div>
  {f'<div class="filter-row"><span class="filter-lab">Montage</span><button class="fbtn active" data-fk="montage" data-fv="all">Tous</button>{mont_btns}</div>' if mont_btns else ''}
  {region_block}
</div>
<p class="axe-legend cat-legend">Profil tri-axes :
<span class="axe-dot axe-A"></span> A — Intérêt général
<span class="axe-dot axe-B"></span> B — Libération des terres
<span class="axe-dot axe-C"></span> C — Gouvernance participative</p>
{cards_grid(fiches_sc, axes_cfg, concepts=concepts, grid_id="resultats")}
<p class="no-result" id="noresult" role="status" hidden>Aucune entrée ne correspond aux filtres choisis.</p>
<script>
(function(){{
 const q=document.getElementById('q'),sort=document.getElementById('sort'),
   cnt=document.getElementById('cnt'),nores=document.getElementById('noresult'),
   grid=document.querySelector('.cards'),
   cards=[...document.querySelectorAll('.card')],
   fbtns=[...document.querySelectorAll('.fbtn')];
 const active={{}};
 fbtns.forEach(b=>{{const k=b.dataset.fk;if(b.classList.contains('active'))active[k]=b.dataset.fv;}});
 function apply(){{
  const v=q.value.toLowerCase().trim();let n=0;
  cards.forEach(c=>{{
   let ok=c.dataset.nom.toLowerCase().includes(v);
   for(const k in active){{
    if(active[k]&&active[k]!=='all'&&c.dataset[k]!==active[k]) ok=false;
   }}
   c.style.display=ok?'':'none';if(ok)n++;
  }});
  cnt.textContent=n;nores.hidden=n!==0;
 }}
 function doSort(){{
  const key=sort.value;
  const vis=cards.slice().sort((a,b)=>{{
   if(key==='nom') return a.dataset.nom.localeCompare(b.dataset.nom,'fr');
   return (parseFloat(b.dataset[key])||0)-(parseFloat(a.dataset[key])||0);
  }});
  vis.forEach(c=>grid.appendChild(c));
 }}
 q.addEventListener('input',apply);
 sort.addEventListener('change',doSort);
 fbtns.forEach(b=>b.addEventListener('click',()=>{{
  const k=b.dataset.fk;
  document.querySelectorAll('.fbtn[data-fk="'+k+'"]').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');active[k]=b.dataset.fv;apply();
 }}));
}})();
</script>"""
    active = CAT_PAGE[cat]
    return page(title, body, active, depth=0, project=project, description=intro,
                path=CAT_PAGE[cat])


# ─────────────────────────────────────────────────────────────────────────────
# Pages — classement
# ─────────────────────────────────────────────────────────────────────────────

def render_classement(all_sc, cfg):
    project = cfg["concepts"]["project"]
    ranking = cfg["ranking"]
    axes_cfg = ranking["axes"]
    core = [(f, s) for f, s in all_sc if f["categorie"] != "modele"]
    core = sorted(core, key=lambda x: x[1]["idl"] or 0, reverse=True)
    catlabel = {"lieu": "Lieu", "porteur": "Porteur", "usufruitier": "Usufruitier"}

    axcol = {a["id"]: a["couleur"] for a in axes_cfg}

    def cell(v, col):
        if v is None:
            return '<td class="num axc"><span class="cbar-na">—</span></td>'
        return (f'<td class="num axc" style="--w:{v}%;--ac:{col}">'
                f'<span class="cbar"></span><span class="cv">{v}</span></td>')

    rows = []
    for i, (f, s) in enumerate(core, 1):
        cat = f["categorie"]
        href = f'{CAT_SLUG[cat]}/{f["uid"]}.html'
        a = s["axes"]
        rows.append(f"""<tr data-cat="{cat}">
  <td class="rank">{i}</td>
  <td class="name"><a href="{href}">{e(f['nom'])}</a>
      <span class="row-sub">{e(clean(f.get('sous_titre','')))}</span></td>
  <td><span class="tag tag-{cat}">{catlabel[cat]}</span></td>
  {cell(a.get('A'), axcol['A'])}{cell(a.get('B'), axcol['B'])}{cell(a.get('C'), axcol['C'])}
  <td class="num idl-cell" style="--pal:{s['palier']['couleur'] if s['palier'] else '#999'}">
      <b>{s['idl'] if s['idl'] is not None else '—'}</b></td>
</tr>""")

    paliers_legend = "".join(
        f'<span class="pal-chip" style="--pal:{p["couleur"]}">'
        f'{e(p["label"])} <em>≥ {p["min"]}</em></span>'
        for p in ranking["paliers"])

    body = f"""<h1>Classement par l'Indice de libération</h1>
<p class="lead">L'Indice de libération (IdL) mesure, de 0 à 100, à quel point un
montage atteint trois finalités, chacune notée comme un axe : l'intérêt général
(A), la libération des terres (B) et la gouvernance participative (C).
L'indice global est leur moyenne — les trois finalités pèsent à parts égales.
<a href="methode.html">Méthode détaillée →</a></p>
<div class="callout callout-warn">
  <p><strong>Un classement croisé, indicatif.</strong> Lieux, porteurs de
  nue-propriété et usufruitiers sont notés par <strong>trois grilles
  distinctes</strong>, adaptées à chaque catégorie : un lieu et un porteur ayant
  le même indice ne sont pas pour autant strictement comparables. Le tableau les
  réunit pour donner une vue d'ensemble — utilisez le filtre par catégorie pour
  comparer des entrées de même nature.</p>
</div>
<div class="paliers-legend">{paliers_legend}</div>
<div class="toolbar">
  <label>Filtrer par catégorie : </label>
  <button class="fbtn active" data-f="all">Tout</button>
  <button class="fbtn" data-f="lieu">Lieux</button>
  <button class="fbtn" data-f="porteur">Porteurs</button>
  <button class="fbtn" data-f="usufruitier">Usufruitiers</button>
</div>
<p class="note sort-hint">Triez le tableau en activant un en-tête de colonne
(Entrée, A, B, C ou IdL).</p>
<p id="sort-status" role="status" class="visually-hidden"></p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Tableau du classement">
<table class="rank-tbl">
<caption class="visually-hidden">Classement des entrées de l'annuaire par
l'Indice de libération, du plus élevé au plus faible.</caption>
<thead><tr>
  <th scope="col">#</th>
  <th scope="col" class="sortable" data-sort="text" aria-sort="none"><button type="button" class="th-sort" aria-label="Trier par entrée, ordre alphabétique">Entrée</button></th>
  <th scope="col">Catégorie</th>
  <th scope="col" class="num sortable" data-sort="num" aria-sort="none"><button type="button" class="th-sort" aria-label="Trier par axe A — intérêt général">A</button></th>
  <th scope="col" class="num sortable" data-sort="num" aria-sort="none"><button type="button" class="th-sort" aria-label="Trier par axe B — libération des terres">B</button></th>
  <th scope="col" class="num sortable" data-sort="num" aria-sort="none"><button type="button" class="th-sort" aria-label="Trier par axe C — gouvernance participative">C</button></th>
  <th scope="col" class="num sortable idl-cell" data-sort="num" aria-sort="descending"><button type="button" class="th-sort" aria-label="Trier par Indice de libération">IdL</button></th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>
<p class="note">A — Intérêt général · B — Libération des terres · C — Gouvernance
participative. « — » : axe non renseigné. Les mini-barres de couleur doublent
la lecture chiffrée.</p>
<script>
(function(){{
 const tbl=document.querySelector('.rank-tbl'),tb=tbl.tBodies[0],
   ths=[...tbl.tHead.rows[0].cells],
   btns=[...document.querySelectorAll('.fbtn')],
   status=document.getElementById('sort-status');
 let curFilter='all';
 function reindex(){{
  let i=0;[...tb.rows].forEach(t=>{{
   if(t.style.display!=='none'){{i++;t.querySelector('.rank').textContent=i;}}
  }});
 }}
 btns.forEach(b=>b.addEventListener('click',()=>{{
  btns.forEach(x=>x.classList.remove('active'));b.classList.add('active');
  curFilter=b.dataset.f;
  [...tb.rows].forEach(t=>{{
   t.style.display=(curFilter==='all'||t.dataset.cat===curFilter)?'':'none';
  }});
  reindex();
 }}));
 function cellVal(tr,i,type){{
  const t=tr.cells[i].innerText.trim();
  if(type==='num') return t==='—'?-1:(parseFloat(t)||0);
  return t.toLowerCase();
 }}
 function sortBy(th){{
  const i=ths.indexOf(th),type=th.dataset.sort;
  const dir=th.getAttribute('aria-sort')==='ascending'?-1:1;
  ths.forEach(x=>{{if(x.classList.contains('sortable'))x.setAttribute('aria-sort','none');}});
  th.setAttribute('aria-sort',dir===1?'descending':'ascending');
  [...tb.rows].sort((a,b)=>{{
   const va=cellVal(a,i,type),vb=cellVal(b,i,type);
   if(va<vb)return dir;if(va>vb)return -dir;return 0;
  }}).forEach(r=>tb.appendChild(r));
  reindex();
  if(status){{
   const lab=(th.querySelector('.th-sort')||th).innerText.trim();
   status.textContent='Tableau trié par '+lab+', ordre '
    +(dir===1?'décroissant':'croissant')+'.';
  }}
 }}
 ths.forEach(th=>{{
  if(!th.classList.contains('sortable'))return;
  const btn=th.querySelector('.th-sort');
  (btn||th).addEventListener('click',()=>sortBy(th));
 }});
}})();
</script>"""
    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Classement par l'Indice de libération",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(core),
        "itemListElement": [
            {"@type": "ListItem", "position": i,
             "url": canonical_url(f'{CAT_SLUG[f["categorie"]]}/{f["uid"]}.html'),
             "name": f["nom"]}
            for i, (f, s) in enumerate(core, 1)
        ],
    }
    return page("Classement", body, "classement.html", project=project,
                description="Classement des montages de libération des terres par l'Indice de libération.",
                path="classement.html", jsonld=[itemlist])


# ─────────────────────────────────────────────────────────────────────────────
# Pages — grilles
# ─────────────────────────────────────────────────────────────────────────────

def render_grilles(cfg):
    project = cfg["concepts"]["project"]
    grilles = cfg["grilles"]["grilles"]
    axes_cfg = cfg["ranking"]["axes"]
    axe_name = {a["id"]: a["label"] for a in axes_cfg}

    blocks = []
    catorder = [("porteur", "Porteurs de nue-propriété"),
                ("usufruitier", "Organismes usufruitiers"),
                ("lieu", "Lieux")]
    for cat, lab in catorder:
        g = grilles[cat]
        fam_html = []
        for fam in g["familles"]:
            crit = []
            for cr in fam["criteres"]:
                crit.append(f"""<tr>
  <td class="crit-name"><span class="axe-dot axe-{cr['axe']}"></span>{e(cr['label'])}</td>
  <td class="crit-axe">{e(axe_name[cr['axe']])}</td>
  <td class="num">{cr['poids']}</td>
  <td class="crit-def">{e(clean(cr['definition']))}</td>
</tr>""")
            fam_html.append(f'<tr class="fam-row"><th colspan="4" scope="colgroup">{e(fam["label"])}</th></tr>'
                            + "".join(crit))
        ls = g["lecture_strategique"]
        def lst(x):
            return "".join(f"<li>{e(clean(i))}</li>" for i in x)
        blocks.append(f"""<section class="grille-block" id="grille-{cat}">
<h2 class="sec">{e(lab)}</h2>
<p class="prose">{e(clean(g['objet']))}</p>
<div class="table-scroll"><table class="grille-tbl">
<caption class="visually-hidden">Critères de lecture de la grille {e(lab)} : axe, poids et définition.</caption>
<thead><tr><th scope="col">Critère de lecture</th><th scope="col">Axe</th><th scope="col">Poids</th><th scope="col">Définition</th></tr></thead>
<tbody>{''.join(fam_html)}</tbody></table></div>
<div class="strat">
  <h3>Lecture stratégique</h3>
  <p class="prose"><strong>Enjeu.</strong> {e(clean(ls['enjeu']))}</p>
  <div class="analyse-grid">
    <div class="an-col an-forces"><h3>Forces typiques</h3><ul>{lst(ls['forces_typiques'])}</ul></div>
    <div class="an-col an-frag"><h3>Fragilités typiques</h3><ul>{lst(ls['fragilites_typiques'])}</ul></div>
    <div class="an-col an-lev"><h3>Leviers</h3><ul>{lst(ls['leviers'])}</ul></div>
  </div>
</div>
</section>""")

    body = f"""<h1>Grilles de lecture et d'analyse stratégique</h1>
<p class="lead">Chaque catégorie de l'annuaire est lue à travers une grille
dédiée. Une grille combine des <strong>critères de lecture</strong> — chacun
rattaché à un axe du classement et pondéré — et une <strong>lecture
stratégique</strong> qui cadre les enjeux, forces, fragilités et leviers
propres à la catégorie. Toute fiche évalue ces critères (oui · partiel · non ·
inconnu) ; le score en découle directement.</p>
<p class="axe-legend">
<span class="axe-dot axe-A"></span> Axe A — Intérêt général
<span class="axe-dot axe-B"></span> Axe B — Libération des terres
<span class="axe-dot axe-C"></span> Axe C — Gouvernance participative</p>
{''.join(blocks)}"""
    return page("Grilles", body, "grilles.html", project=project,
                description="Les trois grilles de lecture et d'analyse stratégique de l'annuaire.",
                path="grilles.html")


# ─────────────────────────────────────────────────────────────────────────────
# Pages — méthode
# ─────────────────────────────────────────────────────────────────────────────

def render_methode(cfg, n_by_cat, all_sc):
    project = cfg["concepts"]["project"]
    ranking = cfg["ranking"]
    cc = cfg["concepts"]["concept_central"]
    axes_html = "".join(
        f"""<div class="axe-card" style="--c:{a['couleur']}">
  <h3>Axe {a['id']} — {e(a['label'])}</h3>
  <p class="axe-q">{e(clean(a['question']))}</p>
  <p>{e(clean(a['description']))}</p>
</div>""" for a in ranking["axes"])
    paliers_html = "".join(
        f"""<tr><td><span class="pal-chip" style="--pal:{p['couleur']}">
{e(p['label'])}</span></td><td class="num">≥ {p['min']}</td>
<td>{e(clean(p['sens']))}</td></tr>""" for p in ranking["paliers"])
    body = f"""<h1>Méthode</h1>

<section><h2 class="sec">Ce que recense l'annuaire</h2>
<p class="prose">« Terres Libérées » recense des lieux français où le foncier a
été soustrait au marché spéculatif par dissociation de la propriété et de
l'usage. {e(clean(cc['definition']))}</p>
<p class="prose"><strong>Ressort juridique.</strong> {e(clean(cc['ressort_juridique']))}</p>
<p class="prose"><strong>Verrou central.</strong> {e(clean(cc['verrou_cle']))}</p>
</section>

<section><h2 class="sec">L'Indice de libération</h2>
<p class="prose">Chaque entrée est notée de 0 à 100 sur trois axes. Pour une
fiche, le score d'un axe est la somme pondérée des critères remplis, ramenée à
100 : <code>score = Σ(poids × facteur) / Σ(poids) × 100</code>. Le facteur vaut
1 pour « oui », 0,5 pour « partiel », 0 pour « non ». Les critères « inconnu »
sont <strong>exclus du calcul</strong> — ils ne pénalisent pas la note mais
abaissent la complétude affichée de la fiche.</p>
<div class="axe-cards">{axes_html}</div>
<p class="prose">L'Indice global est la moyenne des trois axes, à parts égales :
les trois finalités sont tenues pour aussi importantes. La transparence du
calcul prime sur tout réglage fin de pondération.</p>
<p class="prose"><strong>Pénalité de complétude.</strong> Pour ne pas surnoter
les fiches lacunaires, l'indice affiché est pénalisé par la complétude :
<code>IdL affiché = IdL brut × (0,5 + 0,5 × complétude)</code>. Une fiche
entièrement renseignée n'est pas pénalisée ; une fiche dont la moitié des
critères restent « inconnu » voit son indice ramené aux trois quarts de l'indice
brut. L'indice brut est conservé pour information ; c'est l'indice affiché,
pénalisé, qui sert au badge, au classement et à l'export <code>data.json</code>.
Les modèles voisins ne sont pas notés par la grille : leur indice est
<strong>estimé</strong> (axes posés éditorialement) et marqué comme tel ; ils
restent hors du classement principal.</p>
<table class="rank-tbl small">
<caption class="visually-hidden">Paliers de l'Indice de libération : seuil et sens.</caption>
<thead><tr><th scope="col">Palier</th><th scope="col" class="num">Seuil</th><th scope="col">Sens</th></tr></thead>
<tbody>{paliers_html}</tbody></table>
</section>

<section><h2 class="sec">Pureté juridique</h2>
<p class="prose">{e(clean(ranking['purete_juridique']['question']))} Cet
indicateur complémentaire n'entre pas dans l'Indice : il situe le montage sans
le noter, car rester en droit public ou en forme sociétaire n'est pas en soi un
défaut.</p>
</section>

<section><h2 class="sec">Limites</h2>
<ul class="prose">
<li>Les fiches reposent sur des sources publiques ; les montages réels peuvent
être plus précis ou avoir évolué. Chaque fiche distingue les faits vérifiés des
points non confirmés.</li>
<li>L'Indice est une grille d'analyse explicite, reproductible et discutable —
pas un label ni un jugement de valeur.</li>
<li>Une part élevée de critères « inconnu » rend une note peu fiable : la
complétude est toujours affichée.</li>
<li>Le « montage de référence » (nue-propriété d'intérêt général + usufruit
associatif) est un idéal-type ; peu de lieux réels le réalisent à la lettre.</li>
</ul>
</section>

<section><h2 class="sec">État du corpus</h2>
<p class="prose">{n_by_cat['lieu']} lieux · {n_by_cat['porteur']} porteurs de
nue-propriété · {n_by_cat['usufruitier']} organismes usufruitiers ·
{n_by_cat['modele']} modèles voisins de comparaison.</p>
{corpus_histogram(all_sc, ranking)}
</section>"""
    return page("Méthode", body, "methode.html", project=project,
                description="Méthode de l'annuaire et calcul de l'Indice de libération.",
                path="methode.html")


# ─────────────────────────────────────────────────────────────────────────────
# Page — glossaire
# ─────────────────────────────────────────────────────────────────────────────

GLOSSAIRE = [
    ("Libération des terres",
     "Ensemble de pratiques visant à soustraire durablement un foncier à la "
     "logique spéculative et marchande, pour le placer au service d'un usage "
     "défini collectivement et d'intérêt général. Le terme n'est pas un "
     "concept juridique codifié."),
    ("Démembrement",
     "Division du droit de propriété (article 544 du Code civil) en deux "
     "droits distincts confiés à des titulaires différents : la nue-propriété "
     "et l'usufruit."),
    ("Nue-propriété",
     "Droit de propriété privé de l'usage et des revenus du bien : le "
     "nu-propriétaire détient le bien mais n'en a ni l'usage ni la jouissance. "
     "Dans l'annuaire, elle est portée par un organisme d'intérêt général."),
    ("Usufruit",
     "Droit d'user d'un bien et d'en percevoir les revenus sans en être "
     "propriétaire (articles 578 et suivants du Code civil). Constitué au "
     "profit d'une personne morale, il ne peut excéder 30 ans."),
    ("Bail rural",
     "Contrat par lequel un propriétaire confie l'exploitation d'un fonds "
     "agricole à un preneur. D'une durée minimale de neuf ans, il ouvre un "
     "droit au renouvellement d'ordre public."),
    ("Bail emphytéotique",
     "Bail de très longue durée — de 18 à 99 ans — qui confère au preneur un "
     "droit réel sur le bien, proche de la propriété pour la durée du contrat, "
     "en échange d'une redevance modique."),
    ("Fonds de dotation",
     "Personne morale de droit privé à but non lucratif (loi du 4 août 2008) "
     "qui reçoit et gère des biens pour réaliser une œuvre d'intérêt général "
     "ou les redistribuer à un organisme poursuivant un tel but."),
    ("Dotation consomptible / non consomptible",
     "Une dotation est dite non consomptible lorsque les biens qui la "
     "composent ne peuvent pas être vendus ou dépensés : seuls leurs revenus "
     "sont utilisés. La dotation est consomptible lorsque le fonds peut "
     "entamer le capital lui-même. Pour un fonds de dotation portant du "
     "foncier, le caractère non consomptible rend la terre juridiquement très "
     "difficile à sortir : c'est un verrou central des montages de l'annuaire."),
    ("Bail réel solidaire",
     "Bail de longue durée (le BRS) par lequel un organisme de foncier "
     "solidaire dissocie durablement la propriété du terrain, qu'il conserve, "
     "de la propriété du bâti, cédée au ménage. Il encadre les prix de "
     "revente pour maintenir des logements abordables sur le long terme."),
    ("Fondation RUP",
     "Fondation reconnue d'utilité publique : organisme sans but lucratif "
     "doté de la personnalité morale par décret, voué à une mission d'intérêt "
     "général et soumis à un contrôle de l'État."),
    ("Intérêt général",
     "Caractère d'une activité non lucrative, à gestion désintéressée, "
     "ouverte et qui ne profite pas à un cercle restreint de personnes. "
     "Condition centrale de plusieurs montages de l'annuaire."),
    ("Utilité publique",
     "Reconnaissance officielle, par l'État, qu'un organisme ou un projet "
     "sert l'intérêt de la collectivité. Elle conditionne notamment le statut "
     "de fondation reconnue d'utilité publique."),
    ("Indice de libération",
     "Note de synthèse de 0 à 100 attribuée à chaque entrée de l'annuaire. "
     "Elle est la moyenne de trois axes — intérêt général (A), libération des "
     "terres (B), gouvernance participative (C) — et résume la solidité du "
     "montage. Voir la page Méthode."),
    ("Pureté juridique",
     "Indicateur complémentaire, non noté : il situe le montage selon qu'il "
     "reste ou non strictement dans le droit civil privé et la "
     "non-lucrativité, sans bascule vers le droit public ou une forme "
     "sociétaire lucrative."),
]


def render_glossaire(cfg):
    project = cfg["concepts"]["project"]
    items = "".join(
        f'<div class="gloss-item" id="g-{slugify(term)}">'
        f'<dt>{e(term)}</dt><dd>{e(defn)}</dd></div>'
        for term, defn in GLOSSAIRE)
    body = f"""<h1>Glossaire</h1>
<p class="lead">Définitions simples des termes pivots employés dans l'annuaire.
Pour le détail du calcul de l'Indice, voir la <a href="methode.html">Méthode</a>.</p>
<dl class="glossaire">{items}</dl>
<p class="backlink"><a href="index.html">← Retour à l'accueil</a></p>"""
    termset = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "name": "Glossaire — Terres Libérées",
        "url": canonical_url("glossaire.html"),
        "hasDefinedTerm": [
            {"@type": "DefinedTerm", "name": term, "description": defn,
             "url": canonical_url("glossaire.html") + f"#g-{slugify(term)}"}
            for term, defn in GLOSSAIRE
        ],
    }
    return page("Glossaire", body, "glossaire.html", project=project,
                description="Glossaire des termes de la libération des terres : "
                            "nue-propriété, usufruit, démembrement, intérêt général.",
                path="glossaire.html", jsonld=[termset])


# ─────────────────────────────────────────────────────────────────────────────
# Page — accueil
# ─────────────────────────────────────────────────────────────────────────────

def render_index(all_sc, cfg, n_by_cat):
    project = cfg["concepts"]["project"]
    concepts = cfg["concepts"]
    ranking = cfg["ranking"]
    axes_cfg = ranking["axes"]
    core = sorted([(f, s) for f, s in all_sc if f["categorie"] != "modele"],
                  key=lambda x: x[1]["idl"] or 0, reverse=True)
    top = core[:6]
    modeles = sorted([(f, s) for f, s in all_sc if f["categorie"] == "modele"],
                     key=lambda x: x[1]["idl"] or 0, reverse=True)

    cat_cards = "".join(
        f"""<a class="cat-card" href="{CAT_PAGE[c['id']]}">
  <h3>{e(c['label_pluriel'])}</h3>
  <p>{e(clean(c['definition']))}</p>
  <span class="cat-n">{n_by_cat[c['id']]} entrées →</span>
</a>""" for c in concepts["categories"])

    hist = corpus_histogram(all_sc, ranking)

    body = f"""<section class="hero">
  <p class="hero-kicker">Annuaire critique · France</p>
  <h1>La terre, soustraite au marché.</h1>
  <p class="hero-lead">Partout en France, des terres sont sorties du marché
  spéculatif. Cet annuaire les recense, explique leurs montages juridiques et
  les note selon une grille d'analyse explicite.</p>
  <p class="hero-cta">
    <a class="cta" href="classement.html">Voir le classement</a>
    <a class="cta cta-ghost" href="methode.html">Comprendre la méthode</a>
  </p>
</section>

<section class="howto">
  <h2 class="sec">Comment lire cet annuaire</h2>
  <ol class="steps">
    <li class="step">
      <span class="step-n">1</span>
      <h3>Comprendre le concept</h3>
      <p>« Libérer la terre », c'est dissocier la propriété — confiée à un
      organisme d'intérêt général — de l'usage, confié à un collectif non
      lucratif. <a href="glossaire.html">Glossaire des termes →</a></p>
    </li>
    <li class="step">
      <span class="step-n">2</span>
      <h3>Explorer une catégorie</h3>
      <p>Chaque montage se lit à travers trois objets : le lieu, son porteur de
      nue-propriété et son usufruitier. Chacun a son catalogue filtrable.</p>
    </li>
    <li class="step">
      <span class="step-n">3</span>
      <h3>Lire une note</h3>
      <p>Chaque entrée est notée de 0 à 100 sur trois axes — A, B, C — résumés
      par un Indice de libération et un palier. <a href="methode.html">La
      méthode →</a></p>
    </li>
  </ol>
</section>

<section class="explain">
  <h2 class="sec">Le principe</h2>
  <div class="explain-grid">
    <div>
      <h3>Libérer la terre</h3>
      <p>Soustraire durablement un foncier à la logique spéculative pour le
      placer au service d'un usage collectif d'intérêt général.</p>
    </div>
    <div>
      <h3>Dissocier propriété et usage</h3>
      <p>La propriété reste à un collectif non lucratif ; l'usage est confié à
      des usager·es — par démembrement, bail long ou propriété publique.</p>
    </div>
    <div>
      <h3>Le verrou des 30 ans</h3>
      <p>L'usufruit d'une personne morale ne peut excéder 30 ans ; baux ruraux,
      baux emphytéotiques et propriété publique y échappent.</p>
    </div>
  </div>
  <p class="lead">Définitions complètes dans le <a href="glossaire.html">glossaire</a>
  et le détail juridique dans la <a href="methode.html">méthode</a>.</p>
</section>

<section>
  <h2 class="sec">Trois catégories analysées</h2>
  <div class="cat-cards">{cat_cards}</div>
</section>

<section class="corpus">
  <h2 class="sec">État du corpus</h2>
  <p class="lead">L'annuaire compte {n_by_cat['lieu']} lieux,
  {n_by_cat['porteur']} porteurs et {n_by_cat['usufruitier']} usufruitiers
  notés. Leur répartition par palier d'Indice :</p>
  {hist}
</section>

<section>
  <h2 class="sec">En tête du classement</h2>
  <p class="lead">Les montages dont l'Indice de libération est le plus élevé —
  tous axes confondus. <a href="classement.html">Classement complet →</a></p>
  {cards_grid(top, axes_cfg, concepts=concepts)}
</section>

<section>
  <h2 class="sec">Modèles voisins de référence</h2>
  <p class="lead">Des modèles « puristes » proches — français et étrangers —
  recensés à titre de comparaison. Hors classement principal, leur indice est
  <em>estimé</em>. <a href="modeles.html">Voir les modèles voisins →</a></p>
  {cards_grid(modeles, axes_cfg, concepts=concepts)}
</section>"""
    site_desc = meta_desc(concepts["project"]["description"])
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": project["display_name"],
        "alternateName": "Annuaire critique des montages de libération des terres en France",
        "url": canonical_url("index.html"),
        "inLanguage": "fr",
        "description": site_desc,
    }
    return page("Accueil", body, "index.html", project=project,
                description=site_desc, path="index.html", jsonld=[website])


# ─────────────────────────────────────────────────────────────────────────────
# Page — proposer un lieu
# ─────────────────────────────────────────────────────────────────────────────

def render_suggerer(cfg):
    project = cfg["concepts"]["project"]
    body = """<h1>Proposer un lieu</h1>
<p class="lead">« Terres Libérées » est un annuaire évolutif au corpus volontairement
mince et exigeant. Si vous connaissez un lieu, un porteur ou un montage réel de
libération des terres qui n'y figure pas encore, vous pouvez le signaler.</p>

<section><h2 class="sec">Ce que recense l'annuaire</h2>
<p class="prose">Sont référencés les lieux français dont le foncier a été
soustrait au marché spéculatif par dissociation de la propriété et de l'usage :
la propriété est portée par un organisme d'intérêt général ou d'utilité publique
et l'usage confié à une personne morale non lucrative. La page
<a href="methode.html">Méthode</a> détaille les critères ; les
<a href="grilles.html">grilles</a> précisent ce qui est analysé.</p></section>

<section><h2 class="sec">Comment signaler un lieu ou un montage</h2>
<p class="prose">Écrivez à l'adresse ci-dessous en indiquant, autant que possible :</p>
<ul class="prose">
  <li>le nom du lieu, du porteur de nue-propriété et de l'usufruitier ;</li>
  <li>la commune et la région ;</li>
  <li>le type de montage juridique (démembrement, bail emphytéotique, propriété
  publique, propriété collective verrouillée…) ;</li>
  <li>des sources publiques vérifiables (site officiel, presse, rapports) ;</li>
  <li>l'année de création ou d'acquisition, si elle est connue.</li>
</ul>
<p class="prose">Chaque proposition est vérifiée avant publication : seules les
informations sourcées et confirmées sont retenues ; les points non confirmés
sont signalés comme tels dans la fiche.</p>
<p class="prose"><strong>Contact :</strong>
<a href="mailto:cedric.mabilotte@gmail.com">cedric.mabilotte@gmail.com</a></p></section>

<section><h2 class="sec">Limites assumées du corpus</h2>
<p class="prose">L'annuaire reste lacunaire sur certains angles — habitat partagé,
foncier périurbain, outre-mer, espaces naturels concrets. Les signalements
portant sur ces angles morts sont particulièrement bienvenus.</p></section>

<p class="backlink"><a href="index.html">← Retour à l'accueil</a></p>"""
    return page("Proposer un lieu", body, "suggerer.html", project=project,
                description="Comment signaler un lieu ou un montage réel de "
                            "libération des terres à référencer dans l'annuaire.",
                path="suggerer.html")


# ─────────────────────────────────────────────────────────────────────────────
# Page — 404
# ─────────────────────────────────────────────────────────────────────────────

def render_404(cfg):
    project = cfg["concepts"]["project"]
    body = """<h1>Page introuvable</h1>
<p class="lead">La page demandée n'existe pas ou a été déplacée. Le site est un
annuaire au corpus restreint : la page que vous cherchez n'a peut-être jamais
existé.</p>
<p class="prose">Vous pouvez repartir de l'une de ces pages :</p>
<ul class="prose">
  <li><a href="/index.html">Accueil de l'annuaire</a></li>
  <li><a href="/classement.html">Classement par l'Indice de libération</a></li>
  <li><a href="/lieux.html">Catalogue des lieux</a></li>
  <li><a href="/porteurs.html">Catalogue des porteurs de nue-propriété</a></li>
  <li><a href="/usufruitiers.html">Catalogue des organismes usufruitiers</a></li>
  <li><a href="/glossaire.html">Glossaire</a></li>
</ul>"""
    return page("Page introuvable", body, "", project=project,
                description="Page introuvable — Terres Libérées.",
                path="404.html", robots="noindex")


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
:root{
 --ink:#221f1a;--muted:#5f5849;--faint:#6e6655;--paper:#f5f2e9;--card:#fffdf6;
 --line:#ddd4bf;--green:#4a7a3a;--green-dk:#356026;--terra:#bc5d3a;
 --terra-dk:#8f3f25;--blue:#36748a;--blue-dk:#2a5566;--gold:#b0843a;
 --gold-dk:#8a6420;--beige:#efe9d8;--beige-dk:#e6ddc6;
 --axe-a:#4a7a3a;--axe-b:#bc5d3a;--axe-c:#36748a;--radius:8px;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
 color:var(--ink);background:var(--paper);line-height:1.58;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1080px;margin:0 auto;padding:0 1.3rem;}
a{color:var(--green-dk);}
a:hover{color:var(--terra-dk);}
:focus-visible{outline:2px solid var(--ink);outline-offset:2px;border-radius:3px;}

/* utilitaire : visuellement masqué mais lisible par lecteur d'écran */
.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;
 overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0;}
.skiplink{position:absolute;left:-999px;top:0;background:var(--ink);
 color:var(--paper);padding:.6rem 1rem;z-index:100;border-radius:0 0 var(--radius) 0;
 font-family:-apple-system,system-ui,sans-serif;font-size:.9rem;}
.skiplink:focus{left:0;color:var(--paper);}

/* échelle typographique */
h1{font-size:2.6rem;line-height:1.15;letter-spacing:-.018em;margin:1.4rem 0 .6rem;}
h2.sec{font-size:1.7rem;font-family:inherit;text-transform:none;
 letter-spacing:-.01em;color:var(--ink);font-weight:600;
 border-bottom:1px solid var(--line);padding-bottom:.4rem;margin:2.8rem 0 1.2rem;}
h2.sec::before{content:"";display:inline-block;width:1.5rem;height:3px;
 background:var(--terra);vertical-align:.35em;margin-right:.55rem;border-radius:2px;}
h3{font-size:1.28rem;font-weight:600;letter-spacing:-.005em;margin:1.2rem 0 .4rem;}
p{font-size:1.05rem;}
.sans,.topnav,.toolbar,.tag,.axis-block,.card-meta,.enbref,.idl-badge,.fiab,
.completude,.note,.crumb,.foot-links,.score-cap,.pal-chip,.fbtn,.count,
.cat-n,.row-sub,table,.chip,.axe-legend,.crit-axe,.hero-kicker,.step-n,
.sort-lab,.filter-lab,select,.no-result,.gloss-item dt{
 font-family:-apple-system,system-ui,"Segoe UI",sans-serif;}

/* masthead */
.masthead{border-bottom:3px solid var(--ink);background:var(--paper);}
.masthead .wrap{display:flex;flex-wrap:wrap;align-items:center;
 justify-content:space-between;gap:.6rem 1.4rem;padding-top:1.1rem;padding-bottom:.6rem;}
.brand{display:flex;align-items:center;gap:.7rem;text-decoration:none;color:var(--ink);}
.logo-mark{font-family:-apple-system,system-ui,sans-serif;font-size:1.2rem;font-weight:800;
 letter-spacing:0;background:var(--green-dk);color:var(--paper);
 padding:.32rem .5rem;border-radius:var(--radius);line-height:1;}
.brand-name{font-size:1.4rem;font-weight:700;letter-spacing:-.01em;display:block;}
.baseline{font-size:.76rem;color:var(--muted);font-family:-apple-system,system-ui,sans-serif;}
.topnav{display:flex;gap:1.05rem;flex-wrap:wrap;font-size:.88rem;}
.topnav a{text-decoration:none;color:var(--muted);padding:.45rem .2rem;
 display:inline-block;min-height:24px;
 border-bottom:2px solid transparent;transition:color .15s,border-color .15s;}
.topnav a:hover{color:var(--terra-dk);border-bottom-color:var(--line);}
.topnav a.active{color:var(--ink);font-weight:600;border-bottom-color:var(--terra);}

main.wrap{padding-bottom:4rem;}

/* hero */
.hero{padding:3.4rem 0 2.6rem;border-bottom:1px solid var(--line);
 background:linear-gradient(180deg,rgba(221,212,191,.22),transparent);}
.hero-kicker{font-size:.8rem;text-transform:uppercase;letter-spacing:.12em;
 color:var(--terra-dk);font-weight:700;margin:0 0 .4rem;}
.hero h1{font-size:2.9rem;max-width:18ch;margin:.1rem 0 .7rem;}
.hero-lead{font-size:1.22rem;line-height:1.5;color:var(--ink);max-width:46ch;}
.hero-cta{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.4rem;}
.cta{display:inline-block;background:var(--green-dk);color:var(--paper)!important;
 text-decoration:none;padding:.6rem 1.2rem;border-radius:var(--radius);font-weight:600;
 font-family:-apple-system,system-ui,sans-serif;font-size:.92rem;
 transition:background .15s,box-shadow .15s;}
.cta:hover{background:var(--green);}
.cta:focus-visible{outline-color:var(--ink);}
.cta-ghost{background:transparent;color:var(--green-dk)!important;border:1.5px solid var(--green);}
.cta-ghost:hover{background:var(--card);}
.lead{font-size:1.05rem;color:var(--muted);max-width:70ch;}
.lead a,.prose a,.grille-intro a{text-decoration:underline;text-underline-offset:2px;
 text-decoration-thickness:1px;}

/* comment lire — étapes */
.steps{list-style:none;padding:0;margin:1.2rem 0;display:grid;gap:1rem;
 grid-template-columns:repeat(auto-fit,minmax(240px,1fr));}
.step{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:1.1rem 1.2rem 1.2rem;position:relative;}
.step-n{display:inline-flex;align-items:center;justify-content:center;
 width:1.9rem;height:1.9rem;border-radius:50%;background:var(--terra-dk);
 color:var(--paper);font-weight:700;font-size:.95rem;}
.step h3{margin:.6rem 0 .3rem;}
.step p{font-size:.95rem;color:var(--muted);}

/* explain */
.explain-grid,.cat-cards{display:grid;gap:1rem;}
.explain-grid{grid-template-columns:repeat(auto-fit,minmax(220px,1fr));}
.explain-grid h3{margin-top:0;}
.explain-grid p{font-size:.95rem;color:var(--muted);}
.cat-cards{grid-template-columns:repeat(auto-fit,minmax(260px,1fr));}
.cat-card{display:block;background:var(--card);border:1px solid var(--line);
 border-radius:var(--radius);padding:1.1rem 1.2rem;text-decoration:none;
 color:var(--ink);transition:border-color .15s,box-shadow .15s;}
.cat-card:hover{border-color:var(--green);box-shadow:0 4px 16px rgba(33,29,24,.08);}
.cat-card h3{margin-top:0;}
.cat-card p{font-size:.92rem;color:var(--muted);}
.cat-n{font-family:-apple-system,system-ui,sans-serif;font-size:.83rem;
 font-weight:600;color:var(--green-dk);}

/* cards */
.cards{list-style:none;padding:0;margin:1.2rem 0;display:grid;gap:.9rem;
 grid-template-columns:repeat(auto-fill,minmax(300px,1fr));}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:1rem 1.15rem;transition:border-color .15s,box-shadow .15s;}
.card:hover{border-color:var(--green);box-shadow:0 4px 16px rgba(33,29,24,.07);}
.card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:.5rem;}
.card h3{margin:.5rem 0 .2rem;font-size:1.16rem;line-height:1.3;}
.card h3 a{text-decoration:none;color:var(--ink);}
.card h3 a:hover{color:var(--terra);}
.card-sub{font-size:.9rem;color:var(--muted);margin:.1rem 0;}
.card-meta{font-size:.8rem;color:var(--faint);margin:.2rem 0 .5rem;}
.card-viz{display:flex;gap:.7rem;align-items:center;}
.card-viz .axis-block{flex:1;margin:.2rem 0;}

/* tags */
.tag{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;
 padding:.2rem .5rem;border-radius:4px;color:var(--paper);white-space:nowrap;}
.tag-lieu{background:var(--green-dk);}
.tag-porteur{background:var(--terra-dk);}
.tag-usufruitier{background:var(--blue-dk);}
.tag-modele{background:var(--gold-dk);}

/* triangle de profil tri-axes */
.tri{width:108px;height:auto;display:block;flex:0 0 auto;}
.tri.compact{width:78px;}
.score-main .tri{width:140px;margin:.6rem auto 0;}
.tri-frame{fill:none;stroke:var(--line);stroke-width:1;}
.tri-grid{fill:none;stroke:var(--line);stroke-width:1;stroke-dasharray:2 2;}
.tri-fill{fill:rgba(74,122,58,.16);stroke:var(--ink);stroke-width:1.6;
 stroke-linejoin:round;}
.tri-vtx.tri-na{fill:var(--paper);stroke:var(--faint);stroke-width:1;
 stroke-dasharray:2 1.5;}
.tri-lab{font:700 7px -apple-system,system-ui,sans-serif;fill:var(--paper);
 text-anchor:middle;dominant-baseline:central;}

/* idl badge — anneau */
.idl-badge{display:inline-flex;flex-direction:column;align-items:center;
 gap:.15rem;line-height:1.1;}
.idl-ring{width:46px;height:46px;}
.idl-badge.big .idl-ring{width:92px;height:92px;}
.idl-track{fill:none;stroke:var(--beige-dk);}
.idl-arc{fill:none;stroke:var(--pal,#999);stroke-linecap:round;}
.idl-num{fill:var(--pal,#999);font-weight:800;text-anchor:middle;
 dominant-baseline:central;font-family:-apple-system,system-ui,sans-serif;}
.idl-pal{font-size:.62rem;text-transform:uppercase;letter-spacing:.04em;
 color:var(--muted);text-align:center;max-width:9rem;}
.idl-badge.big .idl-pal{font-size:.78rem;letter-spacing:.06em;}
.idl-estime .idl-arc{stroke-dasharray:4 3;}
.idl-estime .idl-num{font-style:italic;}
.idl-na{display:inline-block;border:2px solid var(--faint);color:var(--faint);
 border-radius:var(--radius);padding:.3rem .6rem;font-family:-apple-system,system-ui,sans-serif;
 font-size:.8rem;}

/* jauge linéaire idl */
.idl-scale{margin:.8rem 0 .2rem;}
.idl-scale-track{position:relative;display:block;height:12px;border-radius:6px;
 overflow:hidden;background:var(--beige-dk);}
.idl-seg{position:absolute;top:0;height:100%;}
.idl-cursor{position:absolute;top:-3px;width:3px;height:18px;background:var(--ink);
 border-radius:2px;transform:translateX(-50%);}
.idl-ghost{position:absolute;top:-2px;width:0;height:0;
 border-left:4px solid transparent;border-right:4px solid transparent;
 border-top:6px solid rgba(34,31,26,.45);transform:translateX(-50%);}
.idl-scale-ends{display:flex;justify-content:space-between;font-size:.68rem;
 color:var(--faint);font-family:-apple-system,system-ui,sans-serif;margin-top:.15rem;}

/* axis bars */
.axis-block{margin:.6rem 0;}
.axis-row{display:flex;align-items:center;gap:.5rem;margin:.3rem 0;font-size:.82rem;}
.axis-label{flex:0 0 8.4rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
 white-space:nowrap;}
.axis-track{flex:1;height:.5rem;background:var(--beige-dk);border-radius:4px;overflow:hidden;}
.axis-fill{display:block;height:100%;border-radius:4px;}
.axis-fill.axis-na{background:repeating-linear-gradient(45deg,#ddd,#ddd 3px,#eee 3px,#eee 6px)!important;}
.axis-val{flex:0 0 2.1rem;text-align:right;font-weight:700;font-variant-numeric:tabular-nums;}
.axis-block.compact .axis-label{flex-basis:5.6rem;font-size:.72rem;}
.axis-block.compact .axis-row{font-size:.72rem;margin:.22rem 0;}

/* toolbar / filtres */
.toolbar{display:flex;gap:.6rem;flex-wrap:wrap;align-items:center;margin:1.3rem 0 .7rem;}
.toolbar input[type=search]{flex:1;min-width:180px;font:inherit;font-size:.9rem;
 padding:.45rem .65rem;border:1px solid var(--line);border-radius:var(--radius);
 background:var(--card);font-family:-apple-system,system-ui,sans-serif;
 transition:border-color .15s,box-shadow .15s;}
.toolbar input[type=search]:focus{border-color:var(--green);
 box-shadow:0 0 0 3px rgba(74,122,58,.15);outline:none;}
.sort-lab{font-size:.85rem;color:var(--muted);}
select{font:inherit;font-family:-apple-system,system-ui,sans-serif;font-size:.85rem;
 padding:.4rem .6rem;border:1px solid var(--line);border-radius:var(--radius);
 background:var(--card);color:var(--ink);cursor:pointer;}
.count{margin-left:auto;color:var(--faint);font-size:.85rem;}
.count b{color:var(--green-dk);}
.filter-bar{display:flex;flex-direction:column;gap:.5rem;margin:.6rem 0 1.2rem;}
.filter-row{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;}
.filter-lab{font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;
 color:var(--faint);font-weight:700;flex:0 0 4.4rem;}
.fbtn{font:inherit;font-family:-apple-system,system-ui,sans-serif;font-size:.83rem;
 min-height:32px;padding:.4rem .8rem;border:1px solid var(--line);border-radius:20px;
 background:var(--card);color:var(--muted);cursor:pointer;
 transition:background .15s,color .15s,border-color .15s;}
.fbtn:hover{border-color:var(--green);color:var(--ink);}
.fbtn.active{background:var(--green-dk);color:var(--paper);border-color:var(--green-dk);}
.fbtn:focus-visible{outline-color:var(--ink);}
.no-result{background:var(--beige);border-left:3px solid var(--terra);
 padding:.7rem 1rem;border-radius:var(--radius);font-size:.92rem;color:var(--muted);}

/* fiche */
.crumb{font-size:.85rem;font-family:-apple-system,system-ui,sans-serif;
 margin:1.2rem 0 0;color:var(--muted);}
.crumb a{text-decoration:none;}
.crumb a:hover{text-decoration:underline;}
.crumb [aria-current]{color:var(--faint);}
.fiche-head{margin:.5rem 0 1rem;}
.fiche-head h1{margin:.3rem 0 .15rem;}
.fiche-sub{color:var(--muted);font-size:1.08rem;line-height:1.45;margin:0;}

/* score panel — composant primaire */
.score-panel{display:flex;gap:1.6rem;flex-wrap:wrap;align-items:flex-start;
 background:var(--card);border:1px solid var(--line);
 border-left:5px solid var(--pal,var(--green));border-radius:var(--radius);
 padding:1.6rem 1.8rem;margin:1.4rem 0;box-shadow:0 3px 14px rgba(33,29,24,.06);}
.score-main{text-align:center;}
.score-cap{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;
 color:var(--muted);margin:0 0 .35rem;}
.score-axes{flex:1;min-width:260px;border-left:1px solid var(--line);
 padding-left:1.6rem;}
.fiab{font-size:.82rem;margin:.6rem 0 0;font-weight:600;}
.fiab-ok{color:var(--green-dk);}
.fiab-gold{color:var(--gold-dk);}
.fiab-faint{color:var(--faint);}
.completude{font-size:.8rem;color:var(--faint);margin:.2rem 0 0;}

/* en bref — composant tertiaire (info) */
.enbref{background:var(--beige);border-left:3px solid var(--line);
 border-radius:var(--radius);padding:1rem 1.3rem;margin:1.2rem 0;font-size:.92rem;}
.enbref dl{display:grid;grid-template-columns:max-content 1fr;gap:.55rem 1.6rem;margin:0;}
.enbref dt{color:var(--muted);font-weight:600;}
.enbref dd{margin:0;word-break:break-word;}
.prose{font-size:1.05rem;max-width:68ch;}
.prose.synthese{background:var(--beige);border-left:3px solid var(--green);
 padding:.8rem 1.1rem;border-radius:var(--radius);max-width:none;}
.grille-intro{font-size:.9rem;color:var(--muted);font-family:-apple-system,system-ui,sans-serif;}

/* callouts */
.callout{border-radius:var(--radius);padding:.8rem 1.1rem;margin:1.2rem 0;
 background:var(--beige);}
.callout p{font-size:.95rem;margin:.3rem 0;}
.callout-note{border-left:3px solid var(--gold);}
.callout-warn{border-left:3px solid var(--terra);}

/* récap grille par axe */
.grille-recap{margin:.8rem 0 1rem;display:flex;flex-direction:column;gap:.4rem;}
.rk-row{display:flex;align-items:center;gap:.6rem;font-size:.82rem;
 font-family:-apple-system,system-ui,sans-serif;}
.rk-ax{flex:0 0 11rem;color:var(--muted);}
.rk-bar{flex:0 0 130px;display:flex;height:.7rem;border-radius:4px;
 overflow:hidden;background:var(--beige-dk);}
.rk-seg{display:block;height:100%;}
.rk-txt{color:var(--faint);font-size:.78rem;}

/* corpus histogram */
.corpus-hist{margin:1rem 0;}
.corpus-hist svg{width:100%;max-width:420px;height:auto;}
.corpus-hist figcaption{font-size:.82rem;color:var(--faint);
 font-family:-apple-system,system-ui,sans-serif;margin-top:.3rem;}
.hg-n{font:700 12px -apple-system,system-ui,sans-serif;text-anchor:middle;fill:var(--ink);}
.hg-l{font:9px -apple-system,system-ui,sans-serif;text-anchor:middle;fill:var(--muted);}

/* tables */
.table-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.6rem 0;}
table{width:100%;border-collapse:collapse;font-size:.9rem;margin:.6rem 0;}
table th,table td{border-bottom:1px solid var(--line);padding:.5rem .55rem;
 text-align:left;vertical-align:top;}
table th{color:var(--muted);font-weight:700;font-size:.72rem;text-transform:uppercase;
 letter-spacing:.04em;border-bottom:2px solid var(--ink);}
.fam-row td,.fam-row th{background:var(--beige);font-weight:700;font-size:.8rem;
 text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
 border-top:2px solid var(--line);text-align:left;}
.crit-name{font-weight:600;}
.crit-note,.crit-def{color:var(--muted);font-size:.86rem;}
.crit-oui{color:var(--green-dk);font-weight:700;}
.crit-partiel{color:var(--gold-dk);font-weight:700;}
.crit-non{color:var(--terra-dk);font-weight:700;}
.crit-inconnu{color:var(--faint);font-style:italic;}
.num{text-align:right;font-variant-numeric:tabular-nums;}
.axe-dot{display:inline-block;width:.62rem;height:.62rem;border-radius:50%;
 margin-right:.35rem;vertical-align:baseline;}
.axe-A{background:var(--axe-a);}
.axe-B{background:var(--axe-b);}
.axe-C{background:var(--axe-c);}
.axe-legend{font-size:.82rem;color:var(--muted);}
.axe-legend .axe-dot{margin-left:.8rem;}
.cat-legend{margin:.4rem 0 1rem;}

/* classement — tri + mini-barres */
.rank-tbl tbody tr:nth-child(even) td{background:rgba(221,212,191,.18);}
.rank-tbl tbody tr:hover td{background:var(--beige);}
.rank-tbl .rank{color:var(--faint);font-weight:700;font-variant-numeric:tabular-nums;}
.rank-tbl .name a{font-weight:700;text-decoration:none;}
.rank-tbl .name a:hover{text-decoration:underline;}
.row-sub{display:block;font-size:.78rem;color:var(--faint);font-weight:400;}
.rank-tbl td.idl-cell,.rank-tbl th.idl-cell{border-left:1px solid var(--line);}
.idl-cell b{color:var(--pal,#999);font-size:1.05rem;font-variant-numeric:tabular-nums;}
.rank-tbl.small{max-width:640px;}
th.sortable{white-space:nowrap;padding:0;}
.th-sort{font:inherit;font-family:-apple-system,system-ui,sans-serif;
 font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;
 color:var(--muted);background:none;border:0;cursor:pointer;width:100%;
 text-align:inherit;padding:.5rem .55rem;}
th.num.sortable .th-sort{text-align:right;}
.th-sort:hover{color:var(--terra-dk);}
th.sortable::after{content:" \\2195";opacity:.4;font-size:.8em;
 display:inline-block;padding-right:.4rem;}
th.sortable[aria-sort=ascending]::after{content:" \\25B2";opacity:1;}
th.sortable[aria-sort=descending]::after{content:" \\25BC";opacity:1;}
.sort-hint{margin:.4rem 0;}
.axc{position:relative;}
.axc .cbar{position:absolute;left:0;bottom:0;height:3px;width:var(--w,0);
 background:var(--ac,#999);opacity:.85;}
.axc .cv{position:relative;font-variant-numeric:tabular-nums;}
.cbar-na{color:var(--faint);}

/* analyse */
.analyse-grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
 margin:1rem 0;}
.an-col{border-radius:var(--radius);padding:.4rem 1rem 1rem;background:var(--card);}
.an-col h3{font-size:.82rem;text-transform:uppercase;letter-spacing:.05em;}
.an-col ul{margin:.3rem 0;padding-left:1.1rem;font-size:.92rem;}
.an-col li{margin:.35rem 0;}
.an-forces{border-top:3px solid var(--axe-a);}
.an-frag{border-top:3px solid var(--axe-b);}
.an-lev{border-top:3px solid var(--axe-c);}

/* strat (grilles page) */
.strat{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:.6rem 1.2rem 1.2rem;margin:1rem 0 2rem;}

/* chips — montages reliés avec profil */
.chips{display:flex;flex-wrap:wrap;gap:.6rem;margin:.6rem 0;}
.chip{display:inline-block;background:var(--card);border:1px solid var(--line);
 border-radius:20px;padding:.3rem .8rem;font-size:.85rem;text-decoration:none;
 color:var(--ink);font-family:-apple-system,system-ui,sans-serif;
 transition:background .15s,border-color .15s,color .15s;}
.chip:hover{border-color:var(--green);color:var(--terra);}
.chip-rel{display:flex;align-items:center;gap:.55rem;border-radius:var(--radius);
 padding:.5rem .8rem;}
.chip-rel .tri{flex:0 0 auto;}
.chip-txt{display:flex;flex-direction:column;line-height:1.25;}
.chip-cat{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;
 color:var(--faint);}

/* fiab box / sources — tertiaire */
.fiab-box{background:var(--beige);border-left:3px solid var(--line);
 border-radius:var(--radius);padding:.7rem 1.2rem;margin:1.4rem 0;}
.fiab-box h3{margin:.3rem 0;font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;
 font-family:-apple-system,system-ui,sans-serif;color:var(--muted);}
.fiab-box p{font-size:.9rem;margin:.3rem 0;}
.src-list{font-size:.9rem;}
.backlink{font-family:-apple-system,system-ui,sans-serif;font-size:.88rem;margin-top:2rem;}

/* classement legend */
.paliers-legend{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0;}
.pal-chip{font-size:.78rem;font-weight:600;border-left:4px solid var(--pal,#999);
 background:var(--card);padding:.25rem .6rem;border-radius:4px;}
.pal-chip em{color:var(--faint);font-style:normal;}

/* axe cards (methode) */
.axe-cards{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
 margin:1.1rem 0;}
.axe-card{border:1px solid var(--line);border-top:4px solid var(--c,#999);
 border-radius:var(--radius);padding:.4rem 1.1rem 1rem;background:var(--card);}
.axe-card h3{font-size:1.05rem;}
.axe-q{font-style:italic;color:var(--muted);font-size:.92rem;}
.axe-card p{font-size:.9rem;}
code{background:var(--beige);padding:.1rem .35rem;border-radius:3px;font-size:.86rem;}
.note{font-size:.83rem;color:var(--faint);}

/* glossaire */
.glossaire{margin:1.4rem 0;display:flex;flex-direction:column;gap:0;}
.gloss-item{border-bottom:1px solid var(--line);padding:.9rem 0;}
.gloss-item dt{font-size:1.05rem;font-weight:700;color:var(--ink);
 margin-bottom:.2rem;}
.gloss-item dd{margin:0;font-size:1.02rem;color:var(--muted);max-width:70ch;}

/* footer */
.footer{border-top:3px solid var(--ink);margin-top:3rem;background:var(--paper);}
.footer .wrap{padding:1.6rem 1.3rem 2.2rem;}
.footer p{font-size:.86rem;color:var(--muted);margin:.4rem 0;
 font-family:-apple-system,system-ui,sans-serif;}
.foot-links a{color:var(--green-dk);}

/* tablette */
@media(max-width:880px){
 h1{font-size:2.1rem;}
 .hero h1{font-size:2.2rem;}
 h2.sec{font-size:1.45rem;}
 .score-panel{flex-direction:column;}
 .score-axes{border-left:none;border-top:1px solid var(--line);
  padding-left:0;padding-top:1rem;}
 .rk-ax{flex-basis:8rem;}
}

/* mobile */
@media(max-width:620px){
 h1{font-size:1.85rem;}
 .hero{padding:2.4rem 0 1.8rem;}
 .hero h1{font-size:1.95rem;}
 .hero-lead{font-size:1.08rem;}
 .enbref dl{grid-template-columns:1fr;}
 .topnav{gap:.7rem;font-size:.82rem;}
 .count{margin-left:0;}
 .rk-row{flex-wrap:wrap;}
 .rk-ax{flex-basis:100%;}
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── Ressources statiques générées ────────────────────────────────────────────

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#356026"/>
<text x="32" y="44" font-family="-apple-system,system-ui,Segoe UI,sans-serif"
 font-size="34" font-weight="800" fill="#f5f2e9" text-anchor="middle">TL</text>
</svg>
"""

OG_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#f5f2e9"/>
<rect x="0" y="0" width="1200" height="14" fill="#221f1a"/>
<rect x="80" y="118" width="64" height="64" rx="10" fill="#356026"/>
<text x="112" y="164" font-family="-apple-system,system-ui,Segoe UI,sans-serif"
 font-size="32" font-weight="800" fill="#f5f2e9" text-anchor="middle">TL</text>
<text x="168" y="164" font-family="-apple-system,system-ui,Segoe UI,sans-serif"
 font-size="40" font-weight="700" fill="#221f1a">Terres Libérées</text>
<text x="80" y="320" font-family="Georgia,serif" font-size="76"
 font-weight="700" fill="#221f1a">La terre, soustraite</text>
<text x="80" y="408" font-family="Georgia,serif" font-size="76"
 font-weight="700" fill="#221f1a">au marché.</text>
<rect x="80" y="452" width="60" height="8" fill="#8f3f25"/>
<text x="80" y="520" font-family="-apple-system,system-ui,Segoe UI,sans-serif"
 font-size="30" fill="#5f5849">Annuaire critique des montages de libération des terres en France</text>
</svg>
"""


def build_robots():
    return (f"User-agent: *\nAllow: /\n\n"
            f"Sitemap: {BASE_URL}/sitemap.xml\n")


def build_sitemap(paths):
    """paths : liste de (chemin_relatif, priorité)."""
    urls = ""
    for path, prio in paths:
        urls += (f"  <url>\n    <loc>{canonical_url(path)}</loc>\n"
                 f"    <lastmod>{BUILD_DATE}</lastmod>\n"
                 f"    <changefreq>monthly</changefreq>\n"
                 f"    <priority>{prio}</priority>\n  </url>\n")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + urls + "</urlset>\n")


def main():
    global BASE_URL
    cfg = load_config()
    # URL canonique centralisée depuis concepts.yml
    cfg_url = (cfg["concepts"].get("project", {}) or {}).get("url")
    if cfg_url:
        BASE_URL = cfg_url.rstrip("/")
    fiches = load_fiches()
    gidx = grille_index(cfg["grilles"])
    ranking = cfg["ranking"]

    all_sc = []
    by_uid = {}
    for f in fiches:
        sc = score_fiche(f, gidx, ranking)
        all_sc.append((f, sc))
        by_uid[f["uid"]] = f

    sc_by_uid = {f["uid"]: sc for f, sc in all_sc}

    # nettoyage du site
    if SITE.exists():
        for child in SITE.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            elif child.name != "CNAME":
                child.unlink()
    SITE.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    write(ASSETS / "style.css", CSS)
    write(ASSETS / "favicon.svg", FAVICON_SVG)
    write(ASSETS / "og-default.svg", OG_SVG)
    write(SITE / "favicon.svg", FAVICON_SVG)

    n_by_cat = {c: sum(1 for f in fiches if f["categorie"] == c)
                for c in ("lieu", "porteur", "usufruitier", "modele")}

    # fiches individuelles
    for f, sc in all_sc:
        cat = f["categorie"]
        html_doc = render_fiche(f, sc, cfg, by_uid, sc_by_uid)
        write(SITE / CAT_SLUG[cat] / f'{f["uid"]}.html', html_doc)

    # catalogues
    for cat in ("lieu", "porteur", "usufruitier", "modele"):
        subset = [(f, sc) for f, sc in all_sc if f["categorie"] == cat]
        write(SITE / CAT_PAGE[cat], render_catalogue(cat, subset, cfg))

    # pages transverses
    write(SITE / "index.html", render_index(all_sc, cfg, n_by_cat))
    write(SITE / "classement.html", render_classement(all_sc, cfg))
    write(SITE / "grilles.html", render_grilles(cfg))
    write(SITE / "glossaire.html", render_glossaire(cfg))
    write(SITE / "methode.html", render_methode(cfg, n_by_cat, all_sc))
    write(SITE / "suggerer.html", render_suggerer(cfg))
    write(SITE / "404.html", render_404(cfg))

    # CNAME — domaine personnalisé GitHub Pages
    write(SITE / "CNAME", BASE_URL.split("//")[-1] + "\n")

    # robots.txt + sitemap.xml
    sitemap_paths = [("index.html", "1.0")]
    for cat in ("lieu", "porteur", "usufruitier", "modele"):
        sitemap_paths.append((CAT_PAGE[cat], "0.8"))
    for p in ("classement.html", "grilles.html", "methode.html",
              "glossaire.html", "suggerer.html"):
        sitemap_paths.append((p, "0.6"))
    for f, sc in all_sc:
        sitemap_paths.append((f'{CAT_SLUG[f["categorie"]]}/{f["uid"]}.html', "0.7"))
    write(SITE / "robots.txt", build_robots())
    write(SITE / "sitemap.xml", build_sitemap(sitemap_paths))

    # data.json (export ouvert)
    data = []
    for f, sc in all_sc:
        data.append({"uid": f["uid"], "nom": f["nom"], "categorie": f["categorie"],
                      "idl": sc["idl"], "idl_brut": sc.get("idl_brut"),
                      "score_type": sc.get("score_type"),
                      "completude": (round(sc["completude"], 3)
                                     if sc.get("completude") is not None else None),
                      "axes": sc["axes"],
                      "palier": sc["palier"]["id"] if sc["palier"] else None})
    write(SITE / "data.json", json.dumps(data, ensure_ascii=False, indent=2))

    total = len(fiches)
    print(f"Site généré : {total} fiches, "
          f"{n_by_cat['lieu']} lieux / {n_by_cat['porteur']} porteurs / "
          f"{n_by_cat['usufruitier']} usufruitiers / {n_by_cat['modele']} modèles.")
    print(f"→ {SITE}")


if __name__ == "__main__":
    main()
