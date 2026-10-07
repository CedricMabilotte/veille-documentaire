# BIBLIO — proposition unique pour la charte : « la notice »

*Synthèse des trois propositions de @graphiste (`propositions.md`), 7 octobre 2026.*

## Le constat commun

Les trois propositions décrivent un seul problème sous trois angles : **biblio n'a pas
de source unique d'identité**. Chaque surface recopie ses valeurs à la main :

| Surface | Où vit son style | Résultat aujourd'hui |
|---|---|---|
| Pages du site | `style.css` | Académique (à jour) |
| Couverture par défaut (~56 fiches) | styles en ligne d'un `onerror` | initiale grise, lue comme une image cassée |
| Cartes de partage (2 218) | couleurs en dur dans `social_cards.py` | ancienne identité parchemin / terre cuite |
| Polices | `fonts.css` | Inter promise mais jamais livrée ; Caveat et Special Elite livrées mais plus voulues |

Corriger les surfaces une à une reproduirait la dérive au prochain changement.

## La proposition

**Un objet graphique unique, la notice, décliné partout, et alimenté par une seule
source de vérité.**

La notice, c'est la fiche de catalogue d'une bibliothèque : bandeau du type de document,
titre en EB Garamond, auteur en Inter, filet or, marque « rayonnage commun » en pied.
C'est le cœur du projet, une bibliothèque qui catalogue, rendu visible.

```
┌──────────────────────────┐
│ OUVRAGE · 2019           │  ← bandeau marine, Inter 600 capitales
│                          │
│ La propriété d'usage     │  ← EB Garamond 600
│ contre la rente foncière │
│ Auteur Exemple           │  ← Inter, texte atténué
│ ──                       │  ← filet or
│ ▮▮▮⟋  biblio.actitude.org│  ← marque
└──────────────────────────┘
```

Elle remplace trois choses avec un même dessin :

1. **la couverture par défaut** des fiches sans image (en CSS, suit clair et sombre) ;
2. **la carte de partage** des réseaux (même composition en 1200 × 630, version claire seule) ;
3. **l'en-tête des fiches** (même hiérarchie : type, titre, auteur), ce qui rend le
   passage carte de partage → fiche visuellement continu.

### Les deux fondations

- **`identite-biblio.yaml`** (niveau 1) : palette clair / sombre, polices, échelle
  typographique, marque, règles d'usage. `style.css` en reprend les valeurs, et
  `social_cards.py` les lit au lieu de les recopier.
- **Polices tenues** : héberger Inter (variable, latin, environ 100 Ko) et retirer Caveat
  et Special Elite (environ 150 Ko déclarés). Le poids total ne bouge presque pas. Le texte
  s'affiche enfin pareil sur Mac, Windows et Linux, ce qui conditionne aussi les tailles
  ergonomiques réglées le 7/10.

## Ordre de réalisation

| Étape | Contenu | Effort |
|---|---|---|
| 1 | `identite-biblio.yaml` + Inter hébergée + retrait de Caveat / Special Elite | faible |
| 2 | Notice CSS pour les couvertures par défaut (`onerror` → une classe) | faible |
| 3 | `social_cards.py` réécrit sur la notice, polices livrées avec le script, régénération des 2 218 cartes | moyen |

Les étapes 1 et 2 se font en une session. L'étape 3 se fait ensuite, en lot local.

## Ce qu'on écarte, et pourquoi

- **Une carte de partage sombre** : la plupart des réseaux ne savent pas choisir entre
  deux images. Elle doublerait les fichiers sans être affichée.
- **Assumer la police système** : c'est plus léger de 100 Ko, mais la typographie varie selon
  l'OS. Ce n'est pas tenable pour un projet dont l'identité est d'abord typographique.
- **Une refonte complète des titres** (la proposition 3, point 3) : on la reporte. L'échelle posée
  le 7/10 et le yaml suffisent pour l'instant.
