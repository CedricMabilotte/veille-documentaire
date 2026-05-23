# Déploiement — Communs / communs.actitude.org

Le site est un statique autonome ; la veille et la publication tournent via
GitHub Actions. Voici la marche à suivre, à exécuter une seule fois.

## 1. Créer le dépôt GitHub

Sur le compte GitHub du projet (CedricMabilotte), créer un dépôt **public**
nommé **`Communs`** — vide, sans README initial (le projet en contient déjà un).

## 2. Pousser le projet

Depuis le dossier `liberation-des-terres/` :

```bash
git init
git add .
git commit -m "Communs — annuaire des montages de libération des terres"
git branch -M main
git remote add origin https://github.com/CedricMabilotte/Communs.git
git push -u origin main
```

> Le dossier `liberation-des-terres/` est aujourd'hui imbriqué dans le dépôt
> « Agent recup web github ». Pour en faire un dépôt autonome, le plus simple
> est de le copier hors de ce dossier avant le `git init`, ou d'utiliser
> `git subtree`.

## 3. Activer GitHub Pages

Dans le dépôt **Communs** → **Settings → Pages** :

- **Source** : *GitHub Actions* (et non « Deploy from a branch »).

Le workflow [`.github/workflows/veille.yml`](.github/workflows/veille.yml)
construit et publie le site automatiquement. Aucun secret n'est nécessaire :
la veille fonctionne sans clé d'API.

## 4. Configurer le domaine communs.actitude.org

Le fichier [`site/CNAME`](site/CNAME) contient déjà `communs.actitude.org`.

Côté DNS — le domaine `actitude.org` est géré via **@neo** (Gandi). Lui
demander de créer un enregistrement :

```
CNAME   communs   →   cedricmabilotte.github.io.
```

Puis, dans **Settings → Pages → Custom domain**, saisir
`communs.actitude.org` et cocher **Enforce HTTPS** une fois le certificat émis.

## 5. Vérifier

- Onglet **Actions** → le workflow « Veille & publication — Communs » doit
  réussir (ou le lancer manuellement via *Run workflow*).
- Le site doit s'afficher sur <https://communs.actitude.org>.

## Fonctionnement courant

- **À chaque modification** d'une fiche (`lieux/`, `porteurs/`, `usufruitiers/`,
  `modeles/`) ou de la config, un `push` sur `main` régénère et republie le site.
- **Chaque lundi**, le workflow lance la veille (`watch.py`), régénère le site,
  committe les candidats dans `discovery/` et republie.
- Les candidats de veille sont des **pistes à examiner** : les promouvoir en
  fiche reste une décision humaine (créer le YAML correspondant).

## Option — veille assistée par Claude

`watch.py` se limite à une détection par mots-clés, sans clé d'API. Pour une
qualification plus fine (extraction structurée d'une fiche candidate par
Claude, à l'image du pipeline de « Résidence »), ajouter un secret
`ANTHROPIC_API_KEY` au dépôt et un script d'extraction — non inclus par défaut
pour garder le déploiement sans friction.
