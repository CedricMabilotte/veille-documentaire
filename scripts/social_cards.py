#!/usr/bin/env python3
"""
social_cards.py — Moteur de cartes de partage (item A2 de la revue).

Génère, par fiche publiée, des images Open Graph avec Pillow :
  - une carte sociale 1200x630 (og:image) : fond palette du site, titre,
    auteur, pastille de score, accroche ;
  - des citation-cards 1080x1080 carrées à partir des `citations_phares`
    présentes dans les bulles.

Génère aussi `site/assets/og-default.png` (image OG par défaut, actuellement
manquante).

Sortie : site/assets/cards/<id>.png  et  site/assets/cards/<id>-cite-N.png
         site/assets/og/<id>.png  (alias pour og:image)

Pur Python + Pillow. Dégradation propre si Pillow absent.

Usage autonome :
  python scripts/social_cards.py
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "synopsis" / "catalog.json"
BULLES_PATH = ROOT / "bulles"
CARDS_DIR = ROOT / "site" / "assets" / "cards"
OG_DIR = ROOT / "site" / "assets" / "og"

# ── Palette du site (clair) — cf. site/assets/css/style.css ──────────────────
COL_BG = (247, 242, 231)        # --bg
COL_BG_ALT = (239, 232, 214)    # --bg-alt
COL_TEXT = (35, 31, 28)         # --text
COL_TEXT_DIM = (90, 79, 67)     # --text-dim
COL_ACCENT = (164, 74, 44)      # --accent terre cuite
COL_GOOD = (90, 112, 72)        # --good vert mousse
COL_GOLD = (168, 137, 48)       # --gold
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
    """Charge une police TrueType ; fallback sur la police bitmap par défaut."""
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


def _score_color(score: int) -> tuple:
    """Couleur de la pastille selon le score."""
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


def render_social_card(doc: dict, out_path: Path) -> bool:
    """Carte Open Graph 1200x630 pour une fiche. Retourne True si écrite."""
    mods = _pillow()
    if mods is None:
        return False
    Image, ImageDraw, ImageFont = mods

    W, H = 1200, 630
    try:
        img = Image.new("RGB", (W, H), COL_BG)
        draw = ImageDraw.Draw(img)

        # Bande latérale terre cuite
        draw.rectangle([0, 0, 18, H], fill=COL_ACCENT)
        # Cadre intérieur
        draw.rectangle([40, 40, W - 40, H - 40], outline=COL_BORDER, width=2)

        f_kicker = _load_font(ImageFont, 28, bold=True)
        f_title = _load_font(ImageFont, 58, bold=True)
        f_meta = _load_font(ImageFont, 30)
        f_accroche = _load_font(ImageFont, 32)
        f_brand = _load_font(ImageFont, 26, bold=True)

        # Kicker
        draw.text((80, 80), "BIBLIO · COMMUNS · TERRES", font=f_kicker,
                  fill=COL_ACCENT)

        # Titre (3 lignes max)
        title = (doc.get("title") or "Sans titre").strip()
        lines = _wrap(draw, title, f_title, W - 320)[:3]
        y = 150
        for ln in lines:
            draw.text((80, y), ln, font=f_title, fill=COL_TEXT)
            y += 70

        # Auteur / source — jamais inféré, uniquement ce qui est fourni
        author = (doc.get("author") or "").strip()
        source = (doc.get("source") or "").strip()
        meta_line = author if author else source
        if author and source:
            meta_line = f"{author} · {source}"
        if meta_line:
            draw.text((80, y + 16), meta_line[:70], font=f_meta,
                      fill=COL_TEXT_DIM)

        # Accroche
        accroche = (doc.get("accroche") or "").strip()
        if accroche:
            alines = _wrap(draw, accroche, f_accroche, W - 320)[:3]
            ay = H - 200
            for ln in alines:
                draw.text((80, ay), ln, font=f_accroche, fill=COL_TEXT_DIM)
                ay += 42

        # Pastille de score (coin haut droit)
        score = int(doc.get("score", 0) or 0)
        sc_color = _score_color(score)
        cx, cy, r = W - 130, 130, 66
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sc_color)
        f_score = _load_font(ImageFont, 52, bold=True)
        s_txt = f"{score}"
        bbox = draw.textbbox((0, 0), s_txt, font=f_score)
        draw.text((cx - (bbox[2] - bbox[0]) / 2, cy - (bbox[3] - bbox[1]) / 2 - 8),
                  s_txt, font=f_score, fill=COL_WHITE)
        f_sc_sub = _load_font(ImageFont, 20)
        draw.text((cx - 14, cy + 22), "/10", font=f_sc_sub, fill=COL_WHITE)

        # Pied : marque
        draw.text((80, H - 88), "biblio.actitude.org", font=f_brand,
                  fill=COL_ACCENT)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG")
        return True
    except Exception as e:
        print(f"  ⚠  carte sociale ratée : {e}")
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
        draw = ImageDraw.Draw(img)
        draw.rectangle([36, 36, S - 36, S - 36], outline=COL_ACCENT, width=4)

        f_quote = _load_font(ImageFont, 50, bold=True)
        f_mark = _load_font(ImageFont, 160, bold=True)
        f_attr = _load_font(ImageFont, 30)
        f_brand = _load_font(ImageFont, 26, bold=True)

        # Guillemet décoratif
        draw.text((80, 60), "«", font=f_mark, fill=COL_BORDER)

        quote = quote.strip().strip('"«» ')
        lines = _wrap(draw, quote, f_quote, S - 200)[:9]
        # Centrage vertical
        total_h = len(lines) * 64
        y = max(240, (S - total_h) // 2 - 40)
        for ln in lines:
            draw.text((100, y), ln, font=f_quote, fill=COL_TEXT)
            y += 64

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
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 18, H], fill=COL_ACCENT)
        draw.rectangle([40, 40, W - 40, H - 40], outline=COL_BORDER, width=2)
        f_brand = _load_font(ImageFont, 90, bold=True)
        f_tag = _load_font(ImageFont, 38)
        f_url = _load_font(ImageFont, 30, bold=True)
        draw.text((80, 200), "BIBLIO", font=f_brand, fill=COL_TEXT)
        draw.text((80, 320),
                  "Bibliothèque documentaire ouverte",
                  font=f_tag, fill=COL_TEXT_DIM)
        draw.text((80, 372),
                  "communs · terres · paysanneries",
                  font=f_tag, fill=COL_ACCENT)
        draw.text((80, H - 100), "biblio.actitude.org", font=f_url,
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


def generate_all(catalog_path: Path = CATALOG_PATH,
                 min_score: int = 6) -> dict:
    """Génère les cartes pour toutes les fiches publiables (score >= min_score).

    Retourne des stats.
    """
    mods = _pillow()
    if mods is None:
        print("[social_cards] Pillow indisponible — skip")
        return {"error": "pillow_missing"}

    stats = {"cards": 0, "citation_cards": 0, "og_default": False}

    # OG par défaut (toujours) — généré dans assets/img/ pour correspondre
    # aux références dans les templates statiques
    og_default_path = ROOT / "site" / "assets" / "img" / "og-default.png"
    if render_og_default(og_default_path):
        stats["og_default"] = True

    if not catalog_path.exists():
        print(f"[social_cards] catalog introuvable : {catalog_path}")
        return stats

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for doc_id, doc in catalog.get("docs", {}).items():
        # On retient le même critère de publication que le RSS/sitemap
        sf = doc.get("score_final")
        si = doc.get("score_initial", doc.get("latest_score", 0))
        effective = sf if sf is not None else si
        if (effective or 0) < min_score:
            continue

        payload = _doc_payload(doc_id, doc)

        # Carte sociale principale
        card_path = CARDS_DIR / f"{doc_id}.png"
        if render_social_card(payload, card_path):
            stats["cards"] += 1
            # Alias og/<id>.png
            try:
                from PIL import Image as _I
                _I.open(card_path).save(OG_DIR / f"{doc_id}.png", "PNG")
            except Exception:
                pass

        # Citation-cards depuis la bulle
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
            except Exception as e:
                print(f"  ⚠  citation-cards {doc_id} : {e}")

    print(f"[social_cards] {stats}")
    return stats


if __name__ == "__main__":
    generate_all()
