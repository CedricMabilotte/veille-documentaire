#!/usr/bin/env python3
"""audit_apercus.py — Audit qualité des aperçus (enrichment.summary) des fiches publiées.

Va au-delà de la simple présence : détecte les aperçus sémantiquement vides
ou pollués que l'audit de format ne voit pas — exactement ce qu'un visiteur
lisant la fiche remarquerait immédiatement.

Critique appliquée (par ordre de gravité) :
  VIDE              — champ summary absent ou vide
  DEBUT_URL         — commence par ou contient "Document accessible à https://"
  URL_BRUTE         — contient une URL (souvent reprise du texte brut du PDF)
  MARQUEUR_EXTRAIT  — contient "Extrait :", "Voir le document" (copie extraction)
  REPETE_TITRE      — les 25 premiers chars du summary = début du titre
                      (enrichisseur a répété le titre avant de résumer)
  OCR_BRUIT         — ratio non-alphanumérique > 40% sur > 100 chars (PDF scanné)
  TROP_COURT        — moins de 80 chars de vrai contenu (hors URLs)

Faux positifs gérés :
  - "ZADissidences 2 est un recueil..." → style encyclopédique OK (suivi par "est")
  - Titres d'oeuvres qui commencent le summary suivi d'une description = OK

Usage : python3 scripts/audit_apercus.py
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_FICHES = ROOT / "site" / "fiches"


def _real_content_len(text: str) -> int:
    """Longueur du texte sans URLs."""
    return len(re.sub(r"https?://\S+", "", text).strip())


def audit_apercu(uid: str, doc: dict) -> list[str]:
    e = doc.get("enrichment") or {}
    summary = (e.get("summary") or "") if isinstance(e, dict) else ""
    title = (doc.get("title") or "").strip()
    issues = []

    if not summary.strip():
        return ["VIDE"]

    # URL brute dans le summary
    if re.search(r"https?://", summary):
        if re.search(r"Document accessible à https?://", summary, re.I):
            issues.append("DEBUT_URL")
        else:
            issues.append("URL_BRUTE")

    # Marqueurs d'extraction brute
    if re.search(r"Extrait\s*:|Voir le document|Accessible à :", summary, re.I):
        issues.append("MARQUEUR_EXTRAIT")

    # Le summary répète le titre SANS fournir d'information supplémentaire
    # (ex: "Atop the Watchtower. Document accessible à...")
    # On distingue du style encyclopédique "Titre est un..." → OK
    if title and len(title) >= 15:
        slug = re.sub(r"\s+", " ", title[:25]).lower()
        sum_start = re.sub(r"\s+", " ", summary[:30]).lower()
        if sum_start.startswith(slug):
            # Vérifier si le mot suivant est un verbe descriptif → style OK
            rest = summary[len(title):].strip()
            ok_verbs = re.match(r"^(est|is|are|constitue|présente|propose|recueille|compile|documente|analyse)\b", rest, re.I)
            if not ok_verbs:
                issues.append("REPETE_TITRE")

    # Bruit OCR
    ratio = sum(1 for c in summary if c.isalpha()) / max(len(summary), 1)
    if ratio < 0.55 and len(summary) > 100:
        issues.append("OCR_BRUIT")

    # Trop court (une fois les URLs retirées)
    if _real_content_len(summary) < 80:
        issues.append("TROP_COURT")

    return issues


def run() -> list[dict]:
    with open(ROOT / "synopsis" / "catalog.json") as f:
        data = json.load(f)
    docs = data["docs"]

    fiches_uids = {
        f.replace(".html", "")
        for f in os.listdir(SITE_FICHES)
        if f.endswith(".html") and len(f) == 13
    }

    problems = []
    for uid in sorted(fiches_uids):
        d = docs.get(uid) or {}
        issues = audit_apercu(uid, d)
        if issues:
            e = d.get("enrichment") or {}
            summary = (e.get("summary") or "") if isinstance(e, dict) else ""
            problems.append({
                "uid": uid,
                "lang": d.get("lang", "fr"),
                "title": (d.get("title") or "")[:55],
                "issues": issues,
                "preview": summary[:120].replace("\n", " | "),
                "pdf_on_disk": bool(d.get("saved_as") and os.path.exists(d["saved_as"])),
            })

    print(f"Aperçus problématiques : {len(problems)}/{len(fiches_uids)}\n")
    for p in problems:
        disk = "📄" if p["pdf_on_disk"] else "✗"
        print(f"[{p['uid']}] [{p['lang']}] {disk}  {p['title']}")
        print(f"  → {', '.join(p['issues'])}")
        print(f"  preview: {p['preview'][:100]}")
        print()

    return problems


if __name__ == "__main__":
    run()
