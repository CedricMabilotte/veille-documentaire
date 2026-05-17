# Pull request — biblio.actitude.org

Merci de contribuer ! Cochez la case qui décrit le mieux votre PR.

## Type de contribution

- [ ] Nouvelle source à surveiller (ajout dans `config/sources.yml`)
- [ ] Correction d'une fiche existante (titre, auteur, scoring, traduction)
- [ ] Amélioration du code (parser, scoring, interface)
- [ ] Documentation / méthodologie
- [ ] Autre (préciser ci-dessous)

## Contexte / motivation

<!-- Pourquoi cette modification ? Quel manque comble-t-elle ? -->

## Si nouvelle source

- **Nom de la source** :
- **URL d'index** :
- **Type de parser estimé** (html_static / opds / archive_org / hal / deep_html / playwright) :
- **Pourquoi pertinente pour la thématique communs / terres / paysannerie** :
- **Estimation du volume** (nb de docs par run) :

## Si correction de fiche

- **ID du document** (ex. `d647480f`) :
- **Champ corrigé** (title / author / score / catégorisation / synopsis) :
- **Valeur actuelle** :
- **Valeur proposée** :
- **Source de la correction** (lecture du PDF, connaissance du sujet, etc.) :

## Checklist

- [ ] J'ai testé localement (`python scripts/watch.py --dry-run` ou équivalent)
- [ ] Je n'ai pas modifié les fichiers de données générés (`bulles/`, `covers/`, `reports/`)
- [ ] J'ai mis à jour `feedback.json` si la correction concerne une fiche existante
- [ ] Le scoring ne dépasse pas 10/10
