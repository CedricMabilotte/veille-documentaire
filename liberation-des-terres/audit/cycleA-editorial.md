# Cycle A — Audit éditorial du site généré : cohérence et allègement

> Audit en lecture seule. Aucun fichier modifié.
> Date : 23 mai 2026. Périmètre : pages générées dans `site/` (accueil, méthode,
> grilles, glossaire, modèles, classement, catalogues, suggérer + fiches lieux et
> modèles), et `scripts/generate_site.py`.
> Angle : cohérence éditoriale et **allègement**. L'état actuel est bon ; il s'agit
> d'affiner vers plus de sobriété et de fluidité, pas de surcharger ni de réécrire.

---

## 0. Synthèse

Le site est solide : ton sobre et juridique constant, écriture inclusive
appliquée partout dans le contenu généré (`paysan·nes`, `usager·es`,
`habitant·es`), aucune faute relevée, aucun anglicisme fautif. Les redites notées
dans `cycle3-editorial.md` au niveau des fiches YAML existent toujours, mais le
problème éditorial le plus visible **sur le site** est ailleurs : quelques
**définitions tournent en boucle entre accueil / méthode / glossaire**, et deux ou
trois blocs de texte sont **plus denses que nécessaire** pour un site qui se veut
pratique. Rien de critique. Une douzaine d'ajustements ciblés suffisent.

Légende priorité : **[C]** Critique · **[I]** Importante · **[M]** Mineure.

---

## A. Redondances de contenu entre pages

### A.1 — [I] La définition de « libération des terres » apparaît trois fois, à l'identique ou presque
- **`index.html`** section « Le principe » (3 encadrés) + section « Comment lire
  cet annuaire » étape 1 : deux formulations du même concept sur la **même page**.
- **`methode.html`** section « Ce que recense l'annuaire », §1 : reprend mot pour
  mot la définition longue (« Ensemble de pratiques visant à soustraire
  durablement un foncier… »).
- **`glossaire.html`** entrée « Libération des terres » : encore la même phrase.
- **`suggerer.html`** section « Ce que recense l'annuaire » : une 4ᵉ reformulation.
- **Recommandation (sobriété)** : faire porter **une seule version pleine** à la
  Méthode ; sur l'accueil, garder l'étape 1 de « Comment lire » (courte, suffisante)
  et **supprimer la section « Le principe »** ou la réduire à une seule phrase
  renvoyant au glossaire. Les trois encadrés « Libérer la terre / Dissocier /
  Verrou des 30 ans » dupliquent le glossaire sans rien ajouter. Gain : une section
  entière en moins sur l'accueil, page nettement plus fluide.

### A.2 — [M] Le « verrou des 30 ans » est expliqué trois fois
Encadré accueil, glossaire (entrée « Usufruit »), méthode (« Verrou central »).
La version méthode est la bonne (nuancée, complète). Sur l'accueil, l'encadré dédié
fait doublon — disparaît avec A.1. Conserver glossaire + méthode uniquement.

### A.3 — [M] Intro de catalogue = définition de catégorie déjà sur l'accueil
Les `lead` de `usufruitiers.html`, `porteurs.html`, `lieux.html` reprennent
**mot pour mot** les paragraphes des `cat-card` de l'accueil (cf. `concepts.yml >
categories[].definition`). Acceptable (pages distinctes), mais la définition
« usufruitier » est **longue** (5 lignes, voir A.5). C'est surtout sa densité qui
pose problème, pas la répétition en soi.

### A.4 — [M] Phrase « non un jugement de valeur » répétée
Présente dans le footer (toutes pages), dans le `lead` du classement, et en
substance dans les Limites de la méthode. Le footer suffit ; on peut alléger le
`lead` du classement (voir B.2).

---

## B. Sections trop denses ou textes à resserrer

### B.1 — [I] Définition « Organismes usufruitiers » trop chargée
`usufruitiers.html` lead et `index.html` cat-card : un seul paragraphe de ~70 mots
qui enchaîne définition + énumération des modalités (usufruit stricto sensu, art.
578, bail rural, bail emphytéotique, convention de mise à disposition) +
typologie des formes juridiques. Pour un site « pratique », c'est le bloc le plus
indigeste. **Recommandation** : couper après « gouvernance des usagers » ; déplacer
la nuance « l'usufruit stricto sensu n'est qu'une modalité… » vers la page Grilles
ou Méthode, où elle est attendue. La cat-card de l'accueil doit rester courte.

### B.2 — [M] Lead du classement : deux phrases denses qui se chevauchent
`classement.html` : le `lead` (définition de l'IdL + 3 axes) puis le callout
« Un classement croisé, indicatif » disent partiellement la même chose sur la
comparabilité. Resserrer le `lead` à une phrase (l'IdL note de 0 à 100 sur trois
axes, lien Méthode) et laisser le callout porter l'avertissement.

### B.3 — [M] Méthode, § « Pénalité de complétude »
Paragraphe long avec formule, exemple chiffré, mention de l'indice brut, mention
des modèles voisins. Information juste mais dense. Suggestion légère : isoler la
mention « modèles voisins estimés » dans sa propre phrase courte (elle traite
d'un autre sujet que la pénalité) — la lecture en sera plus aérée.

### B.4 — [M] Fiches : champ `fiabilite` parfois en bloc long
Ex. `l/larzac.html` : « Faits vérifiés : … » énumère 6 éléments d'affilée en une
phrase. Lisible mais lourd. Non bloquant ; si retouche un jour, préférer une
énumération courte. À traiter au niveau YAML, hors site généré.

---

## C. Cohérence du ton d'une page/fiche à l'autre

### C.1 — [M] Ton homogène — RAS notable
Fiches lieux et modèles partagent la même structure et le même registre sobre.
La synthèse d'analyse reformule le résumé (signature éditoriale assumée, déjà
notée en cycle 3) — cohérent sur le site, pas un défaut de ton.

### C.2 — [M] Libellé de catégorie « modèle » incohérent selon la page
- Catalogue/accueil : tag « **Modèle voisin** ».
- Fiche détaillée : tag et fil d'Ariane « **Modèle voisin de référence** ».
- Nav : « **Modèles voisins** ».
Trois variantes pour la même chose. Choisir une forme (« Modèle voisin » suffit)
et l'unifier — voir `generate_site.py` : `catlabel` dans `card()` vs
`render_fiche()`, et le fil d'Ariane.

### C.3 — [M] « Méthode & sources » dans le footer
Le footer pointe « Méthode &amp; **sources** » mais `methode.html` ne contient
aucune liste de sources (chaque fiche a les siennes). Soit retirer « & sources »
du libellé, soit le mot promet une page qui n'existe pas. Incohérence visible.

---

## D. Écriture inclusive, langue, fautes

### D.1 — [M] Écriture inclusive : cohérente sur le site généré
Contrairement au constat du cycle 3 sur les YAML, le **site rendu** est homogène
(`paysan·nes`, `usager·es`, `citoyen·nes` dans larzac, méthode, grilles). Le point
médian est appliqué partout. RAS au niveau site. (Si les YAML sont harmonisés,
vérifier que la régénération conserve cette homogénéité.)

### D.2 — [M] Anglicismes — aucun
« écolieu », « tiers-lieu » sont des termes français admis. Rien à corriger.

### D.3 — [—] Orthographe — aucune faute relevée sur les pages auditées.

---

## E. À alléger ou supprimer sans perte

| Élément | Page | Action |
|---|---|---|
| Section « Le principe » (3 encadrés) | `index.html` | **Supprimer** ou réduire à 1 phrase (cf. A.1) — doublon du glossaire |
| Encadré « Le verrou des 30 ans » | `index.html` | Disparaît avec la section ci-dessus (cf. A.2) |
| 2ᵉ moitié de la déf. « usufruitiers » | `usufruitiers.html`, `index.html` | Couper / déplacer la nuance art. 578 vers Grilles (cf. B.1) |
| Lead du classement | `classement.html` | Resserrer à 1 phrase, le callout porte l'avertissement (cf. B.2) |
| « & sources » du footer | toutes pages | Retirer le mot ou créer la page (cf. C.3) |

---

## F. Manques de clarté (rares)

### F.1 — [M] Accueil : « 24 entrées notées » vs « 7 + 10 + 7 »
La section « État du corpus » dit « 7 lieux, 10 porteurs et 7 usufruitiers » (= 24)
puis l'histogramme parle de « 24 entrées notées ». Cohérent arithmétiquement, mais
le lecteur ne sait pas que les **modèles voisins** sont exclus du compte ici alors
qu'ils apparaissent juste en dessous. Une demi-phrase (« hors modèles voisins »)
dans le `lead` lèverait l'ambiguïté — la `figcaption` le précise déjà, le `lead`
non.

### F.2 — [M] « Fork de Résidence » dans le footer
Mention présente sur **toutes les pages** sans aucune explication accessible
(pas de page « à propos »). Pour un visiteur, « Fork de Résidence » est obscur.
Soit l'expliquer une fois, soit la retirer du footer public (détail technique).

### F.3 — [M] Date de génération seule
Le footer affiche « généré automatiquement le 2026-05-23 » au format ISO. Pour un
site grand public, préférer « le 23 mai 2026 ». Détail de fluidité.

---

## G. Récapitulatif priorisé

| Priorité | Action | Localisation |
|---|---|---|
| **Importante** | Supprimer la triple définition « libération des terres » : une version pleine en Méthode, accueil réduit | `index.html`, `generate_site.py` |
| **Importante** | Resserrer la définition « usufruitiers » (couper la nuance art. 578) | `usufruitiers.html`, `concepts.yml` |
| **Mineure** | Unifier le libellé « Modèle voisin » (3 variantes) | `generate_site.py` |
| **Mineure** | Resserrer le lead du classement ; retirer « & sources » du footer ou créer la page | `classement.html`, `generate_site.py` |
| **Mineure** | Préciser « hors modèles voisins » dans le lead de l'État du corpus | `index.html` |
| **Mineure** | Date footer en français ; clarifier ou retirer « Fork de Résidence » | `generate_site.py` |
| **Mineure** | Aérer le § « Pénalité de complétude » (isoler la phrase modèles voisins) | `methode.html` |

*Fin de l'audit cycle A — éditorial, orienté sobriété et fluidité. Lecture seule.*
