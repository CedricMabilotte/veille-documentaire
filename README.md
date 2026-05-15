# Bibliothèque de veille documentaire

Outil de veille qui scrape des sites, score les documents avec Claude (API Anthropic),
et télécharge automatiquement les sources pertinentes.

## Structure du repo

```
config/sources.yml          ← URLs à surveiller + mots-clés + seuil
scripts/watch.py            ← script principal de veille
docs/                       ← documents téléchargés (PDF, TXT, EPUB…)
reports/                    ← rapports de chaque veille (JSON + Markdown)
.github/workflows/watch.yml ← workflow GitHub Actions (déclenchement manuel)
```

## Démarrage rapide

1. Édite `config/sources.yml` avec tes URLs et mots-clés
2. Dans GitHub → Settings → Secrets → Actions : ajoute `ANTHROPIC_API_KEY`
3. Dans GitHub → onglet Actions → "Veille documentaire" → Run workflow
