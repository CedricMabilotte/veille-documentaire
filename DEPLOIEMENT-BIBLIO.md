# Déploiement de biblio.actitude.org

> Ce document décrit comment activer le sous-domaine `biblio.actitude.org`
> pour qu'il serve le site publié à chaque veille.

## État actuel

- **Repo public** : https://github.com/CedricMabilotte/biblio-actitude-org
- **GitHub Pages** : activé, branche `main`, racine `/`
- **CNAME** : `biblio.actitude.org` (déjà configuré côté GitHub)
- **URL temporaire (active immédiatement)** : https://cedricmabilotte.github.io/biblio-actitude-org/
- **URL cible (en attente DNS)** : https://biblio.actitude.org

## Étape DNS — à faire côté registrar (Gandi/OVH/…)

Connecte-toi à l'interface de gestion DNS de **`actitude.org`** et ajoute un enregistrement **CNAME** :

| Type  | Nom (sous-domaine) | Cible                              | TTL  |
|-------|--------------------|------------------------------------|------|
| CNAME | `biblio`           | `cedricmabilotte.github.io.`        | 3600 |

⚠️ Notes :
- La cible **n'est pas** `cedricmabilotte.github.io/biblio-actitude-org` — c'est juste `cedricmabilotte.github.io.` (point final inclus).
- Le `nom` est juste `biblio`, pas `biblio.actitude.org` (le suffixe `.actitude.org` est implicite).
- Si ton registrar ne permet pas le `.` final, mettre `cedricmabilotte.github.io` sans point.

## Propagation et HTTPS

Une fois le CNAME publié :

1. La propagation prend **15 min à 24 h** (selon TTL et resolver).
2. Vérifier la propagation : `dig biblio.actitude.org +short` doit afficher `cedricmabilotte.github.io.` puis une IP GitHub Pages.
3. Une fois propagé, GitHub provisionne automatiquement un **certificat Let's Encrypt** (1-24 h supplémentaires).
4. Forcer HTTPS depuis l'interface GitHub Pages du repo (`Settings → Pages → Enforce HTTPS`).

## Pipeline de publication automatique

À chaque exécution du workflow **"Veille documentaire"** sur le repo privé `veille-documentaire`, le site est automatiquement republiée :

```
veille-documentaire (privé)
   ↓ python scripts/watch.py
   ↓   ├── scrape sources
   ↓   ├── score Claude
   ↓   ├── download + validation PDF
   ↓   ├── extract texte/couverture
   ↓   ├── synopsis enrichi + bulles
   ↓   ├── update catalog
   ↓   ├── régénère interface + site
   ↓   └── publie le contenu de site/ vers
   ↓
biblio-actitude-org (public, repo)
   ↓ GitHub Pages auto-deploy
   ↓
https://biblio.actitude.org
```

Secret nécessaire (déjà configuré) : `BIBLIO_PUBLISH_TOKEN` dans le repo `veille-documentaire`.

## Vérifier le statut côté GitHub

```bash
# Status Pages
gh api /repos/CedricMabilotte/biblio-actitude-org/pages

# Status des derniers déploiements
gh api /repos/CedricMabilotte/biblio-actitude-org/pages/builds --jq '.[0]'

# Forcer un rebuild si besoin
gh api -X POST /repos/CedricMabilotte/biblio-actitude-org/pages/builds
```

## Maintenance

- **Changer le sous-domaine** : éditer `site/CNAME` et adapter le DNS
- **Désactiver Pages** : `gh api -X DELETE /repos/CedricMabilotte/biblio-actitude-org/pages`
- **Rotater le PAT de publication** : générer un nouveau token GitHub avec scope `repo`, puis :
  ```bash
  echo "NEW_TOKEN" | gh secret set BIBLIO_PUBLISH_TOKEN --repo CedricMabilotte/veille-documentaire
  ```

## Sécurité

- Le repo public **ne contient que** : le site HTML/CSS/JS, le catalog public (titres, URLs, scores, synopsis), les couvertures (page 1 des PDFs), et les bulles éditoriales pour les docs 9+.
- Les PDFs eux-mêmes restent sur Google Drive privé (pas exposés publiquement).
- Les liens des fiches pointent vers (a) la source originale (publique par nature) et (b) une URL de recherche Drive (privée, accessible uniquement à l'utilisateur connecté à son compte Google).
