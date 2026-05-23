# Bilan des cycles d'amélioration — Terres Libérées

*Synthèse, 2026-05-23. Site : https://communs.actitude.org · dépôt : github.com/CedricMabilotte/Communs*

## Méthode

Quatre cycles autonomes, chacun : 5 agents d'audit lancés en parallèle sur des
angles variés → 1 agent d'intégration appliquant les recommandations
raisonnables → régénération, vérification, publication. 24 audits au total,
conservés dans `audit/`.

## Cycle A — fond conceptuel & juridique

Angle directeur : faire ressortir l'opposition entre droit civil d'intérêt
général, droit commercial et propriété privée.

- Nouvelle page **« Trois régimes du sol »** (tableau comparatif, frontières du
  modèle), bloc `regimes:` data-driven dans la configuration.
- Grilles : nouveaux critères `parts_non_cessibles` (axe B) et
  `non_lucrativite_effective` (axe A, porteur) — la (non-)cessibilité des parts
  et la (non-)lucrativité étaient l'angle mort central ; poids rééquilibrés.
- « Pureté juridique » → « Nature juridique du montage » : échelle non
  hiérarchique (la propriété publique n'est plus une « bascule » négative).
- Corpus : 28 → 33 fiches (Habicoop, Village Vertical, Foncière Chênelet,
  SCIC Terres de Sources, Les Champs des Possibles, coopérative d'habitants
  loi ALUR) — angles morts habitat / périurbain comblés.
- ~15 corrections factuelles (Hameau des Buis réécrit, FEVE, Lurzaindia,
  Villarceaux, bail du Larzac, FPH…) ; fiche périmée supprimée.

## Cycle B — expérience & forme (allègement)

- Navigation ramenée de 10 à 6 entrées ; pages de référence en pied de page.
- Cartes épurées : triangle de profil seul, conteneurs secondaires dé-bordurés,
  filets d'accent uniformisés, cartes entièrement cliquables.
- Performance : SVG factorisés (`<defs>`/`<use>`), JavaScript de tri/filtre
  externalisé et mis en cache, attributs répétés supprimés.
- Correctifs mobile : nav pleine largeur, cibles tactiles ≥ 44 px, tableaux et
  filtres adaptés aux petits écrans.

## Cycle C — finition & robustesse

- Accessibilité : annonce des tris (`role="status"`), `aria-pressed` sur les
  filtres, contraste du chiffre d'indice corrigé, focus sur la carte entière,
  tableaux défilables en régions navigables.
- Bug corrigé : f-string du générateur incompatible Python ≤ 3.11.
- Liens : URL morte corrigée, incohérence de données rectifiée.
- SEO : données structurées ajoutées à la page « Trois régimes ».
- Pédagogie : liage des termes pivots vers le glossaire, légende
  « Comment lire cette fiche », glossaire complété.

## Cycle D — exploration libre

- Page **« Thèmes »** : 5 portes d'entrée transversales (foncier agricole,
  habitat, espaces naturels, portage public, portage citoyen).
- Page **« Comparer »** : deux montages en vis-à-vis, alimentée par `data.json`.
- **Transparence du corpus** : section « État du corpus » enrichie — complétude
  moyenne, part de critères « inconnu », angles morts assumés.
- Copywriting : espaces fines insécables, microcopie, libellés resserrés.
- Veille (`watch.py`) : scoring pondéré, analyse de la page candidate,
  détecteur d'angles morts, mémoire des passes — de 3 à 29 candidats par passe.

## État final

33 fiches (8 lieux, 13 porteurs, 7 organismes usufruitiers, 5 modèles voisins),
47 pages, site statique autonome ~1,1 Mo, publié en continu via GitHub Actions.
Navigation à 6 entrées, pages de référence : Trois régimes, Grilles, Thèmes,
Comparer, Glossaire, Modèles. Aucun lien interne cassé, HTML valide,
accessibilité AA, veille hebdomadaire active.

## Principes tenus

Sobriété (rien n'a été ajouté sans retrait ou justification), faits vérifiés
distingués des points non confirmés, sources citées, Indice de libération
transparent et reproductible.
