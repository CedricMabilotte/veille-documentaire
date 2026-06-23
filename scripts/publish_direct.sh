#!/bin/bash
# Publie site/ directement vers biblio-actitude-org sans passer par le workflow.
# Usage : bash scripts/publish_direct.sh ["message de commit optionnel"]
set -e
MSG="${1:-publish: $(date '+%Y-%m-%d %H:%M')}"
TOKEN=$(gh auth token)
REPO="https://x-access-token:${TOKEN}@github.com/CedricMabilotte/biblio-actitude-org.git"
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT
git clone "$REPO" "$TMP" --depth=1 -q
rsync -a --delete --exclude='.git' site/ "$TMP/"
cd "$TMP"
git config user.name "Library Bot"
git config user.email "bot@library.local"
git add -A
git diff --staged --quiet && echo "rien à publier" && exit 0
git commit -m "$MSG" -q
git push origin main -q
echo "✓ Publié : $MSG"
