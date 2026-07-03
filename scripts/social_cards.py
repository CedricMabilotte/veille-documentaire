#!/usr/bin/env python3
"""
social_cards.py — Moteur de cartes de partage (item A2 de la revue).

Génère, par fiche publiée, des images Open Graph avec Pillow :
  - une carte sociale 1200x630 (og:image) : fond papier, tampon de score,
    coin corné, grain léger — même langage graphique que le site
    (refonte anarcho-champêtre, session du 2026-07-09) ;
  - une carte portrait 1080x1350 (4:5) pour la publication native
    (Instagram, Mastodon, Telegram — format recommandé 2026, voir
    échanges de session) avec la couverture réelle si disponible ;
  - des citation-cards 1080x1080 carrées à partir des `citations_phares`
    présentes dans les bulles.

Génère aussi `site/assets/og-default.png` (image OG par défaut).

Sortie : site/assets/cards/<id>.png            (1200x630, alias og/<id>.png)
         site/assets/cards/<id>-portrait.png    (1080x1350)
         site/assets/cards/<id>-cite-N.png      (1080x1080)

Pur Python + Pillow. Dégradation propre si Pillow absent. Les polices
Special Elite / Caveat utilisées côté web n'existent pas forcément comme
TTF sur la machine qui génère ces images (fonts Google, pas des paquets
système) : DejaVu Sans Mono en fait office côté "tampon/machine à
écrire", DejaVu Serif côté "EB Garamond".

Usage autonome :
  python scripts/social_cards.py
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"
BULLES_PATH = ROOT / "bulles"
COVERS_DIR = ROOT / "site" / "assets" / "covers"
CARDS_DIR = ROOT / "site" / "assets" / "cards"
OG_DIR = ROOT / "site" / "assets" / "og"

# ── Palette du site (clair, palette "Bibliothèque" par défaut) ───────────────
# cf. :root dans site/assets/css/style.css — les cartes reflètent toujours
# la palette par défaut, indépendamment du thème choisi par un visiteur
# (préférence client-only, sans effet côté génération serveur).
COL_BG = (247, 242, 231)        # --bg
COL_BG_ALT = (239, 232, 214)    # --bg-alt
COL_BG_ELEV = (237, 228, 204)   # --bg-elev (papier légèrement plus foncé)
COL_TEXT = (35, 31, 28)         # --text
COL_TEXT_DIM = (90, 79, 67)     # --text-dim
COL_ACCENT = (164, 74, 44)      # --accent terre cuite
COL_GOOD = (90, 112, 72)        # --good vert mousse
COL_GOLD = (168, 137, 48)       # --gold
COL_BAD = (154, 59, 43)         # --bad (rouge de correction/rature)
COL_BORDER = (184, 171, 139)    # --border-strong
COL_WHITE = (251, 247, 236)


def _pillow():
    """Import paresseux de Pillow. Retourne le module ou None."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
        return Image, ImageDraw, ImageFont
    except ImportError:
        return None


def _load_font(ImageFont, size: int, bold: bool = False):
    """Charge une police serif (proxy EB Garamond) ; fallback bitmap."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _load_mono_font(ImageFont, size: int, bold: bool = False):
    """Police mono (proxy Special Elite/tampon) ; fallback sur la serif."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return _load_font(ImageFont, size, bold)


def _score_color(score: int) -> tuple:
    """Couleur de tampon selon le score."""
    if score >= 9:
        return COL_GOOD
    if score >= 7:
        return COL_GOLD
    return COL_ACCENT


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    """Découpe un texte en lignes tenant dans max_width pixels."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        trial = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def _paper_grain(Image, img, seed: int | None = None, opacity: int = 10):
    """Superpose un grain de papier léger (bruit gris, faible opacité).

    Équivalent du radial-gradient de bruit utilisé en CSS (style.css) —
    ici via Image.effect_noise, sans dépendance externe (numpy…).
    """
    try:
        rng = random.Random(seed)
        noise = Image.effect_noise(img.size, 24)
        noise = noise.convert("RGB")
        return Image.blend(img, noise, opacity / 255)
    except Exception:
        return img


def _paste_tape(Image, ImageDraw, img, cx: int, top: int,
                 w: int = 130, h: int = 40, angle: float = -3.5):
    """Colle un petit bout de scotch (rectangle translucide, légèrement
    tourné) en haut d'une zone — même geste que .biblio-fichecard-tape
    en CSS. cx = centre horizontal, top = bord supérieur visé."""
    tape = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tape)
    d.rectangle([0, 0, w, h], fill=COL_BORDER + (140,))
    tape = tape.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(tape, (cx - tape.width // 2, top - tape.height // 2), tape)


def _dogear(draw, W: int, H: int, margin: int, size: int = 34):
    """Coin de page légèrement écorné, en bas à droite du cadre intérieur."""
    x0, y0 = W - margin, H - margin
    draw.polygon(
        [(x0 - size, y0), (x0, y0), (x0, y0 - size)],
        fill=COL_BG_ELEV,
        outline=COL_BORDER,
    )


def _stamp(draw, ImageFont, cx: int, cy: int, r: int, lines: list[str],
           color: tuple, ring_width: int = 3):
    """Tampon rond à double cercle (fiche de bibliothèque tamponnée) —
    texte centré, non pivoté (plus fiable en rendu bitmap qu'un texte
    pivoté, et un tampon appliqué à la main n'est pas toujours de travers
    non plus)."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=ring_width)
    draw.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10],
                 outline=color, width=1)
    f = _load_mono_font(ImageFont, 17, bold=True)
    total_h = len(lines) * 20
    y = cy - total_h / 2
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=f)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, y), ln, font=f, fill=color)
        y += 20


def render_social_card(doc: dict, out_path: Path) -> bool:
    """Carte Open Graph 1200x630 pour une fiche. Retourne True si écrite."""
    mods = _pillow()
    if mods is None:
        return False
    Image, ImageDraw, ImageFont = mods

    W, H = 1200, 630
    try:
        img = Image.new("RGB", (W, H), COL_BG)
        img = _paper_grain(Image, img, seed=hash(doc.get("id", "")) & 0xFFFF)
        draw = ImageDraw.Draw(img)

        margin = 40
        draw.rectangle([margin, margin, W - margin, H - margin],
                        outline=COL_BORDER, width=2)
        _dogear(draw, W, H, margin)
        _paste_tape(Image, ImageDraw, img, W // 2, margin)

        f_kicker = _load_mono_font(ImageFont, 22, bold=True)
        f_title = _load_font(ImageFont, 56, bold=True)
        f_meta = _load_font(ImageFont, 28)
        f_accroche = _load_font(ImageFont, 30)
        f_brand = _load_mono_font(ImageFont, 22, bold=True)

        draw.text((80, 76), "BIBLIO · COMMUNS · TERRES", font=f_kicker,
                  fill=COL_ACCENT)

        title = (doc.get("title") or "Sans titre").strip()
        lines = _wrap(draw, title, f_title, W - 320)[:3]
        y = 150
        for ln in lines:
            draw.text((80, y), ln, font=f_title, fill=COL_TEXT)
            y += 68

        author = (doc.get("author") or "").strip()
        source = (doc.get("source") or "").strip()
        meta_line = author if author else source
        if author and source:
            meta_line = f"{author} · {source}"
        if meta_line:
            draw.text((80, y + 14), meta_line[:70], font=f_meta,
                      fill=COL_TEXT_DIM)

        accroche = (doc.get("accroche") or "").strip()
        if accroche:
            alines = _wrap(draw, accroche, f_accroche, W - 320)[:3]
            ay = H - 190
            for ln in alines:
                draw.text((80, ay), ln, font=f_accroche, fill=COL_TEXT_DIM)
                ay += 40

        # Tampon de score (coin haut droit) — remplace l'ancienne pastille pleine
        score = int(doc.get("score", 0) or 0)
        sc_color = _score_color(score)
        _stamp(draw, ImageFont, W - 130, 130, 62,
               [f"{score}/10", "VÉRIFIÉ"], sc_color)

        draw.text((80, H - 76), "biblio.actitude.org", font=f_brand,
                  fill=COL_ACCENT)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG")
        return True
    except Exception as e:
        print(f"  ⚠  carte sociale ratée : {e}")
        return False


def render_portrait_card(doc: dict, out_path: Path,
                          cover_path: Path | None = None) -> bool:
    """Carte portrait 1080x1350 (4:5) — publication native (Instagram,
    Mastodon, Telegram). Reprend la couverture réelle si disponible.
    Retourne True si écrite."""
    mods = _pillow()
    if mods is None:
        return False
    Image, ImageDraw, ImageFont = mods

    W, H = 1080, 1350
    try:
        img = Image.new("RGB", (W, H), COL_BG)
        img = _paper_grain(Image, img, seed=(hash(doc.get("id", "")) + 1) & 0xFFFF)
        draw = ImageDraw.Draw(img)

        cover_h = 620
        if cover_path and cover_path.exists():
            try:
                cover = Image.open(cover_path).convert("RGB")
                cw, ch = cover.size
                scale = max(W / cw, cover_h / ch)
                cover = cover.resize((int(cw * scale), int(ch * scale)))
                cx0 = (cover.width - W) // 2
                cy0 = (cover.height - cover_h) // 2
                cover = cover.crop((cx0, cy0, cx0 + W, cy0 + cover_h))
                img.paste(cover, (0, 0))
                draw = ImageDraw.Draw(img)
            except Exception:
                cover_path = None
        if not cover_path or not cover_path.exists():
            draw.rectangle([0, 0, W, cover_h], fill=COL_BG_ELEV)
            f_ph = _load_font(ImageFont, 160, bold=True)
            initial = (doc.get("title") or "?").strip()[:1].upper()
            bbox = draw.textbbox((0, 0), initial, font=f_ph)
            draw.text(((W - (bbox[2] - bbox[0])) / 2, (cover_h - (bbox[3] - bbox[1])) / 2 - 20),
                      initial, font=f_ph, fill=COL_BORDER)

        margin = 44
        draw.rectangle([margin, cover_h + 24, W - margin, H - margin],
                        outline=COL_BORDER, width=2)
        _dogear(draw, W, H, margin)
        _paste_tape(Image, ImageDraw, img, W // 2, cover_h + 24)

        f_title = _load_font(ImageFont, 46, bold=True)
        f_body = _load_font(ImageFont, 30)
        f_brand = _load_mono_font(ImageFont, 22, bold=True)

        title = (doc.get("title") or "Sans titre").strip()
        tlines = _wrap(draw, title, f_title, W - 2 * margin - 80)[:3]
        y = cover_h + 70
        for ln in tlines:
            draw.text((margin + 40, y), ln, font=f_title, fill=COL_TEXT)
            y += 56

        accroche = (doc.get("accroche") or "").strip()
        if accroche:
            blines = _wrap(draw, accroche, f_body, W - 2 * margin - 80)[:5]
            y += 14
            for ln in blines:
                draw.text((margin + 40, y), ln, font=f_body, fill=COL_TEXT_DIM)
                y += 40

        score = int(doc.get("score", 0) or 0)
        sc_color = _score_color(score)
        _stamp(draw, ImageFont, W - margin - 90, H - margin - 90, 56,
               [f"{score}/10"], sc_color)

        draw.text((margin + 40, H - margin - 46), "biblio.actitude.org",
                  font=f_brand, fill=COL_ACCENT)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG")
        return True
    except Exception as e:
        print(f"  ⚠  carte portrait ratée : {e}")
        return False


def render_citation_card(quote: str, attribution: str, out_path: Path) -> bool:
    """Citation-card carrée 1080x1080. Retourne True si écrite."""
    mods = _pillow()
    if mods is None:
        return False
    Image, ImageDraw, ImageFont = mods
    if not quote:
        return False

    S = 1080
    try:
        img = Image.new("RGB", (S, S), COL_BG_ALT)
        img = _paper_grain(Image, img, seed=hash(quote) & 0xFFFF)
        draw = ImageDraw.Draw(img)

        margin = 40
        draw.rectangle([margin, margin, S - margin, S - margin],
                        outline=COL_BORDER, width=2)
        _dogear(draw, S, S, margin)
        _paste_tape(Image, ImageDraw, img, S // 2, margin)
        _stamp(draw, ImageFont, S - 130, 130, 60, ["CITATION", "VÉRIFIÉE"], COL_GOOD)

        f_quote = _load_font(ImageFont, 48, bold=True)
        f_mark = _load_font(ImageFont, 150, bold=True)
        f_attr = _load_mono_font(ImageFont, 24)
        f_brand = _load_mono_font(ImageFont, 22, bold=True)

        draw.text((80, 70), "«", font=f_mark, fill=COL_BORDER)

        quote = quote.strip().strip('"«» ')
        lines = _wrap(draw, quote, f_quote, S - 200)[:9]
        total_h = len(lines) * 62
        y = max(250, (S - total_h) // 2 - 20)
        for ln in lines:
            draw.text((100, y), ln, font=f_quote, fill=COL_TEXT)
            y += 62

        if attribution:
            draw.text((100, S - 170), attribution[:80], font=f_attr,
                      fill=COL_TEXT_DIM)
        draw.text((100, S - 110), "biblio.actitude.org", font=f_brand,
                  fill=COL_ACCENT)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG")
        return True
    except Exception as e:
        print(f"  ⚠  citation-card ratée : {e}")
        return False


def render_og_default(out_path: Path) -> bool:
    """Génère l'image OG générique du site (og-default.png)."""
    mods = _pillow()
    if mods is None:
        return False
    Image, ImageDraw, ImageFont = mods
    W, H = 1200, 630
    try:
        img = Image.new("RGB", (W, H), COL_BG)
        img = _paper_grain(Image, img, seed=42)
        draw = ImageDraw.Draw(img)
        margin = 40
        draw.rectangle([margin, margin, W - margin, H - margin],
                        outline=COL_BORDER, width=2)
        _dogear(draw, W, H, margin)
        _paste_tape(Image, ImageDraw, img, W // 2, margin)
        f_brand = _load_font(ImageFont, 88, bold=True)
        f_tag = _load_font(ImageFont, 36)
        f_url = _load_mono_font(ImageFont, 26, bold=True)
        draw.text((80, 200), "BIBLIO", font=f_brand, fill=COL_TEXT)
        draw.text((80, 320),
                  "Bibliothèque documentaire ouverte",
                  font=f_tag, fill=COL_TEXT_DIM)
        draw.text((80, 372),
                  "communs · terres · paysanneries",
                  font=f_tag, fill=COL_ACCENT)
        draw.text((80, H - 96), "biblio.actitude.org", font=f_url,
                  fill=COL_ACCENT)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG")
        return True
    except Exception as e:
        print(f"  ⚠  og-default ratée : {e}")
        return False


def _doc_payload(doc_id: str, doc: dict) -> dict:
    """Construit le payload d'affichage d'un doc (titre, auteur, score…).

    N'infère JAMAIS un auteur absent de la source (anonymat respecté).
    """
    title = ""
    if doc.get("runs"):
        title = (doc["runs"][-1].get("link_text") or "").strip()
    if not title:
        title = doc.get("filename", "")
        if "." in title:
            title = title.rsplit(".", 1)[0]

    enrich = doc.get("enrichment") or {}
    accroche = ""
    bulle_path = None
    bp = doc.get("bulle")
    if bp:
        p = ROOT / bp
        if p.exists():
            bulle_path = p
            try:
                b = json.loads(p.read_text(encoding="utf-8"))
                accroche = b.get("teaser", "") or ""
                if b.get("titre_accroche"):
                    title = b["titre_accroche"]
            except Exception:
                pass
    if not accroche and isinstance(enrich, dict):
        accroche = (enrich.get("relevance_notes") or "")[:200]

    # Auteur : uniquement champ explicite editeur/auteur, jamais inféré
    author = doc.get("doc_author") or ""
    meta = doc.get("meta") or {}
    if not author and isinstance(meta, dict):
        # pdf_author vient des métadonnées du PDF lui-même = source explicite
        author = (meta.get("pdf_author") or "").strip()

    score = doc.get("score_final")
    if score is None:
        score = doc.get("score_initial", doc.get("latest_score", 0))

    return {
        "id": doc_id,
        "title": title.strip() or f"Fiche {doc_id}",
        "author": author,
        "source": doc.get("source", ""),
        "accroche": accroche.strip(),
        "score": score or 0,
        "bulle_path": bulle_path,
    }


def _publishable_predicate(min_score: int):
    """Retourne un prédicat doc -> bool aligné sur watch._is_publishable
    (exclusions.yml + format ouvrage + score effectif), avec repli sur un
    simple seuil de score si le module watch n'est pas importable (usage
    autonome de social_cards.py hors pipeline).

    Import tardif (à l'intérieur de la fonction, pas au niveau module) :
    watch.py fait lui-même `import social_cards` — un import de watch en
    tête de ce fichier créerait une dépendance circulaire à l'import. En
    différant l'import ici, au moment de l'appel, watch.py a déjà terminé
    son propre chargement (generate_all n'est invoqué que depuis son corps
    de fonction, jamais à l'import).
    """
    try:
        import watch as _watch
        return lambda doc: _watch._is_publishable(doc)
    except Exception as e:
        print(f"  ℹ  watch._is_publishable indisponible ({e}) — repli sur score seul")

        def _fallback(doc: dict) -> bool:
            sf = doc.get("score_final")
            si = doc.get("score_initial", doc.get("latest_score", 0))
            effective = sf if sf is not None else si
            return (effective or 0) >= min_score
        return _fallback


def generate_all(catalog_path: Path = CATALOG_PATH,
                 min_score: int = 6) -> dict:
    """Génère les cartes pour toutes les fiches publiables.

    Le critère de publication est le même que celui du RSS/sitemap/fiches
    pré-rendues (watch._is_publishable : exclusions éditoriales + format
    ouvrage + score effectif) — pas un simple seuil de score, pour éviter
    de générer des cartes orphelines pour des docs exclus ou non-ouvrage.
    `min_score` ne sert que de repli si watch n'est pas importable.

    Retourne des stats.
    """
    mods = _pillow()
    if mods is None:
        print("[social_cards] Pillow indisponible — skip")
        return {"error": "pillow_missing"}

    stats = {"cards": 0, "portrait_cards": 0, "citation_cards": 0, "og_default": False}

    # OG par défaut (toujours) — généré dans assets/img/ pour correspondre
    # aux références dans les templates statiques
    og_default_path = ROOT / "site" / "assets" / "img" / "og-default.png"
    if render_og_default(og_default_path):
        stats["og_default"] = True

    if not catalog_path.exists():
        print(f"[social_cards] catalog introuvable : {catalog_path}")
        return stats

    is_publishable = _publishable_predicate(min_score)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for doc_id, doc in catalog.get("docs", {}).items():
        if not is_publishable(doc):
            continue

        payload = _doc_payload(doc_id, doc)

        # Carte sociale principale (1200x630, og:image)
        card_path = CARDS_DIR / f"{doc_id}.png"
        if render_social_card(payload, card_path):
            stats["cards"] += 1
            # Alias og/<id>.png
            try:
                from PIL import Image as _I
                _I.open(card_path).save(OG_DIR / f"{doc_id}.png", "PNG")
            except Exception:
                pass

        # Carte portrait (1080x1350, publication native)
        cover_path = COVERS_DIR / f"{doc_id}.jpg"
        portrait_path = CARDS_DIR / f"{doc_id}-portrait.png"
        if render_portrait_card(payload, portrait_path, cover_path):
            stats["portrait_cards"] += 1

        # Citation-cards depuis la bulle
        n_cit = 0
        if payload["bulle_path"] is not None:
            try:
                b = json.loads(payload["bulle_path"].read_text(encoding="utf-8"))
                attribution = payload["title"]
                for i, cit in enumerate(b.get("citations_phares", [])[:3], 1):
                    quote = cit.get("quote", "") if isinstance(cit, dict) else str(cit)
                    page = cit.get("page", "") if isinstance(cit, dict) else ""
                    attr = f"{attribution}"
                    if page:
                        attr += f" — p.{page}"
                    cc_path = CARDS_DIR / f"{doc_id}-cite-{i}.png"
                    if render_citation_card(quote, attr, cc_path):
                        stats["citation_cards"] += 1
                        n_cit = i
            except Exception as e:
                print(f"  ⚠  citation-cards {doc_id} : {e}")
        # Nettoyage des citation-cards devenues excédentaires (moins de
        # citations_phares qu'au run précédent) pour ce doc
        for stale in CARDS_DIR.glob(f"{doc_id}-cite-*.png"):
            m = re.search(r"-cite-(\d+)\.png$", stale.name)
            if m and int(m.group(1)) > n_cit:
                stale.unlink(missing_ok=True)

    # Nettoyage des cartes orphelines : docs qui ne sont plus publiables
    # (score retombé, exclusion éditoriale, doc retiré du catalogue…)
    publishable_ids = {doc_id for doc_id, doc in catalog.get("docs", {}).items()
                        if is_publishable(doc)}
    n_removed = 0
    id_re = re.compile(r"^[0-9a-f]{8}")
    for directory in (CARDS_DIR, OG_DIR):
        if not directory.is_dir():
            continue
        for f in directory.glob("*.png"):
            m = id_re.match(f.stem)
            if m and m.group(0) not in publishable_ids:
                f.unlink(missing_ok=True)
                n_removed += 1
    if n_removed:
        stats["orphans_removed"] = n_removed

    print(f"[social_cards] {stats}")
    return stats


if __name__ == "__main__":
    generate_all()
