# Communs — Terres Libérées

Annuaire critique des montages de **libération des terres** en France :
recensement et analyse stratégique des lieux où le foncier a été soustrait au
marché spéculatif par dissociation de la propriété et de l'usage — la
nue-propriété (ou la propriété sanctuarisée) portée par un organisme d'intérêt
général ou d'utilité publique, l'usufruit ou l'usage confié à une personne
morale de droit civil à but non lucratif.

Site public : <https://communs.actitude.org>

Fork de [« Résidence »](../) (veille des opportunités arts plastiques),
lui-même fork de BIBLIO (veille des communs fonciers). Même choix technique :
données en YAML, générateur Python sans dépendance lourde, site statique publié
sur GitHub Pages, veille via GitHub Actions.

## Ce que fait le projet

1. **Recense** trois catégories d'entités, une fiche YAML par entité :
   - `porteurs/` — organismes porteurs de nue-propriété (fondations, fonds de
     dotation, collectivités, foncières solidaires) ;
   - `usufruitiers/` — organismes titulaires de l'usage (associations, sociétés
     civiles, coopératives, GFA) ;
   - `lieux/` — les lieux eux-mêmes (fermes, domaines, hameaux, écolieux) ;
   - `modeles/` — modèles voisins de référence, pour comparaison (OFS/BRS,
     CLT, Stiftung trias, Mietshäuser Syndikat).
2. **Analyse** chaque entité avec une *grille de lecture et d'analyse
   stratégique* propre à sa catégorie (`config/grilles.yml`).
3. **Classe** chaque entité par un **Indice de libération** (0-100) sur trois
   axes — intérêt général, libération des terres, gouvernance participative
   (`config/ranking.yml`).
4. **Surveille** des sources web pour repérer de nouveaux lieux et montages
   (`scripts/watch.py`, `config/sources.yml`).
5. **Publie** un site statique consultable (`scripts/generate_site.py`).

## Structure du dépôt

```
config/
  concepts.yml      ← ontologie : 3 catégories, concept central, typologie
  grilles.yml       ← 3 grilles de lecture et d'analyse stratégique
  ranking.yml       ← l'Indice de libération : axes, formule, paliers
  sources.yml       ← sources web surveillées par la veille
porteurs/           ← fiches YAML — porteurs de nue-propriété
usufruitiers/       ← fiches YAML — organismes usufruitiers
lieux/              ← fiches YAML — les lieux
modeles/            ← fiches YAML — modèles voisins de référence
scripts/
  watch.py          ← veille : interroge les sources, écrit des candidats
  generate_site.py  ← génère le site statique dans site/
recherche/          ← rapports de recherche fondateurs (sourcés)
audit/              ← rapports des cycles d'amélioration et de vérification
discovery/          ← candidats issus de la veille (à promouvoir manuellement)
site/               ← site statique publié (généré ; ne pas éditer à la main)
.github/workflows/  ← veille + publication automatisées
```

## Utilisation

Régénérer le site après avoir modifié une fiche ou la configuration :

```bash
pip install pyyaml
python3 scripts/generate_site.py     # → site/
```

Lancer une passe de veille :

```bash
python3 scripts/watch.py             # → discovery/candidats-AAAA-MM-JJ.md
```

Ouvrir `site/index.html` dans un navigateur pour consulter le site localement.

## Ajouter une entité

Créer un fichier YAML dans `lieux/`, `porteurs/` ou `usufruitiers/` en
reprenant le schéma d'une fiche existante (champs `uid`, `categorie`, `nom`,
`montage`, `grille`, `analyse`, `fiabilite`, `liens`, `sources`…). Les
identifiants de critères du bloc `grille:` doivent correspondre à ceux de la
catégorie dans `config/grilles.yml`. Régénérer le site : le classement, les
fiches et le sitemap se recalculent automatiquement.

## Déploiement

Voir [`DEPLOIEMENT.md`](DEPLOIEMENT.md).

## Méthode et limites

L'Indice de libération est une **grille d'analyse explicite et reproductible**,
pas un label ni un jugement de valeur. Chaque fiche distingue les faits
vérifiés des points non confirmés. Les sources sont citées. La page *Méthode*
du site détaille le calcul et ses limites.

## Licence

Distribué sous **Peer Production License (PPL)**, licence à réciprocité
« copyfarleft ». Titulaire : actitude.org.
