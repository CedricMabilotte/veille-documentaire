#!/usr/bin/env python3
"""
prompt_version.py — Reproductibilité (item C6 de la revue).

Fournit un hash court et stable d'un texte de prompt, pour stocker
`prompt_version` dans chaque enregistrement de run et chaque fiche/bulle.
Permet de savoir avec quel prompt exact une fiche a été produite.

Pur Python (hashlib). Aucune dépendance.
"""

from __future__ import annotations

import hashlib


def prompt_hash(prompt: str, length: int = 10) -> str:
    """Retourne un hash court (SHA-256 tronqué) d'un prompt.

    Le hash est stable : le même prompt produit toujours le même hash.
    Sert d'identifiant de version reproductible.
    """
    if not prompt:
        return "noprompt"
    digest = hashlib.sha256(prompt.encode("utf-8", errors="ignore")).hexdigest()
    return digest[:max(4, length)]


def provenance(model: str, prompt: str) -> dict:
    """Petit dict de provenance reproductible à insérer dans les enregistrements.

    {"model": "claude-haiku-4-5", "prompt_version": "ab12cd34ef"}
    """
    return {
        "model": model or "unknown",
        "prompt_version": prompt_hash(prompt),
    }


if __name__ == "__main__":
    sample = "Tu es un assistant de veille documentaire STRICT."
    print("hash :", prompt_hash(sample))
    print("prov :", provenance("claude-haiku-4-5", sample))
    # Stabilité : deux appels identiques
    assert prompt_hash(sample) == prompt_hash(sample)
    assert prompt_hash("") == "noprompt"
    print("OK — prompt_version stable")
