---
name: Suggérer une nouvelle source à surveiller
about: Proposer un site, archive ou flux à ajouter au crawl
title: "[Source] "
labels: ["new-source", "veille"]
---

## Source proposée

- **Nom** :
- **URL d'index** (page listant les documents) :
- **Langue principale** :
- **Licence/Conditions d'utilisation** (libre / CC / domaine public / inconnu) :

## Pertinence thématique

Comment cette source recoupe-t-elle la veille (communs, terres, paysannerie, propriété collective, luttes foncières) ?

<!-- 2-3 phrases suffisent. Citez des documents emblématiques si possible. -->

## Caractéristiques techniques

- [ ] Site statique (HTML simple)
- [ ] API/OPDS/Atom disponible
- [ ] Site dynamique (JS, nécessite Playwright)
- [ ] Téléchargement direct PDF possible
- [ ] Nécessite navigation 2 niveaux (page index -> page document -> PDF)

**Parser recommandé** (cocher) :
- [ ] `html_static`
- [ ] `deep_html`
- [ ] `opds`
- [ ] `archive_org`
- [ ] `hal`
- [ ] `playwright`
- [ ] À déterminer

## Volume estimé

- Nombre approximatif de documents disponibles :
- Fréquence de mise à jour (quotidienne / hebdo / sporadique / inconnu) :

## Exemples concrets

Listez 2-3 URLs de documents PDF déjà publiés pour qu'on puisse tester :

1.
2.
3.

## Risques / vigilance

- [ ] Robots.txt à respecter
- [ ] Rate limiting / risque de blocage
- [ ] Contenu sensible nécessitant prudence (anonymat, etc.)
