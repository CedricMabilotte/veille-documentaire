---
name: Signaler un faux positif / faux négatif de scoring
about: Une fiche est sur/sous-estimée par le scoring automatique
title: "[Scoring] "
labels: ["scoring", "feedback"]
---

## Fiche concernée

- **ID** (ex. `d647480f`) :
- **Titre** :
- **URL** :
- **Score actuel** : /10

## Type d'erreur

- [ ] Faux positif (scoré trop haut — pas réellement pertinent)
- [ ] Faux négatif (scoré trop bas — devrait être mis en avant)
- [ ] Catégorisation incorrecte
- [ ] Synopsis/teaser erroné
- [ ] Auteur / titre mal extrait

## Score proposé

**Score correct estimé** : /10

## Justification

Pourquoi pensez-vous que le scoring est incorrect ? Quels passages/aspects du document soutiennent votre évaluation ?

<!-- Citez idéalement des extraits ou pages précises. -->

## Suggestions de correction du prompt de scoring

Si l'erreur révèle un biais systématique, comment ajuster le prompt ou les mots-clés ?

<!-- Optionnel mais précieux pour faire évoluer le système. -->

## Action attendue

- [ ] Rescorer ce document uniquement
- [ ] Ajuster le prompt et rescorer tout le batch concerné
- [ ] Ajouter une entrée dans `feedback.json` pour mémoriser la correction
