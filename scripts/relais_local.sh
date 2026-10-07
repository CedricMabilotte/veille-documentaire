#!/bin/bash
# Relais local — fait tourner depuis la machine de Ced les sources marquées
# `local_only: true` dans config/sources.yml (bloquées ou exclues sur CI),
# puis pousse le résultat comme le ferait le job CI « Veille documentaire ».
#
# Usage : bash scripts/relais_local.sh            (run réel)
#         DRY_RUN=true bash scripts/relais_local.sh (simulation, rien n'est poussé)
#
# Garde-fous : refuse de tourner si l'arbre suivi n'est pas propre ; se cale
# d'abord sur origin/main (la CI committe tous les deux jours — leçon L69).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "✗ Arbre de travail modifié : committer ou annuler avant le relais." >&2
  git status --short --untracked-files=no | head >&2
  exit 1
fi
git pull -q --ff-only origin main

# Pré-vol : le scoring post-lecture passe par la CLI Claude locale. Si elle
# n'est pas authentifiée, les PDF seraient téléchargés sans être lus, et
# chaque tentative ratée consommerait un des 4 essais d'enrichissement.
if ! timeout 90 claude -p "Réponds seulement : ok" </dev/null >/dev/null 2>&1; then
  echo "✗ CLI Claude non authentifiée : lance « claude » puis /login, et relance le relais." >&2
  exit 1
fi

WATCH_LOCAL_ONLY=1 python3 scripts/watch.py

if [ "${DRY_RUN:-false}" = "true" ]; then
  echo "→ Simulation : rien n'est committé. Annuler les fichiers régénérés avec : git checkout -- ."
  exit 0
fi

python3 scripts/export_bibtex.py || echo "  export_bibtex ignoré"

# Copie des PDF vers Drive si rclone est configuré (sinon ils restent dans docs/)
if command -v rclone >/dev/null && rclone listremotes 2>/dev/null | grep -q '^gdrive:'; then
  rclone copy docs/ gdrive:Veille_documentaire/ --stats-one-line --stats 30s || true
fi

git add reports/ synopsis/ interface/ bulles/ site/ discovery/ exports/ 2>/dev/null || true
if git diff --staged --quiet; then
  echo "→ Rien de nouveau à publier."
  exit 0
fi
BEFORE=$(git rev-parse HEAD)
git commit -q -m "veille (relais local): $(date '+%Y-%m-%d %H:%M') — sources local_only"
git push -q origin main
if ! git diff --quiet "$BEFORE" HEAD -- site/; then
  gh workflow run publish-only.yml --ref main && echo "→ publish-only.yml déclenché"
fi
echo "✓ Relais local terminé."
