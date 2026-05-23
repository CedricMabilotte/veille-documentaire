# Cycle B — Audit performance & poids

Audit en lecture seule du site statique « Terres Libérées » (`site/`, généré par `scripts/generate_site.py`). Angle : poids transféré et performance de rendu. Cible : GitHub Pages, site 100 % autonome (aucun CDN).

## 1. Mesures de référence

| Élément | Valeur |
|---|---|
| Poids total `site/` | 1,1 Mo |
| Pages HTML | 45 fichiers — HTML cumulé 946 Ko |
| CSS | 1 fichier — `assets/style.css`, 22,5 Ko (434 lignes) |
| SVG assets | 3 fichiers — favicon 280 o, og-default 1,1 Ko |
| JSON | `data.json` 12 Ko |
| Images bitmap | 0 (aucune) |
| Pages les plus lourdes | `porteurs.html` 45 Ko, `index.html` 42 Ko, `lieux.html` / `classement.html` 31 Ko |

### Constat global

Le site est déjà **léger et sain** : aucune image bitmap, aucune police web chargée (pile système + serif natif), un seul CSS partagé et bien mis en cache par le navigateur, aucune dépendance externe. La performance réelle est bonne. Les marges de gain portent donc sur la **réduction de redondance dans le HTML généré**, qui n'affecte qu'au premier chargement de chaque page mais grossit inutilement le dépôt et le transfert.

## 2. Problèmes identifiés

### 2.1 SVG inline massivement dupliqués (poids principal)

Chaque carte d'entité et chaque ligne porte un SVG « triangle tri-axes ». Sur les 4 pages-listes + fiches, on compte **127 triangles** et **77 anneaux IDL**.

Or, dans chaque triangle, une partie des nœuds est **rigoureusement identique d'un triangle à l'autre** : le cadre (`tri-frame`), la grille pointillée (`tri-grid`), les 3 cercles de sommet (`tri-vtx`) et les 3 lettres A/B/C (`tri-lab`). Seul le polygone `tri-fill` (les 3 points du profil) varie réellement.

- Partie fixe par triangle : **475 octets** → **× 127 = 58,9 Ko** de balisage strictement répété.
- Anneau IDL : le cercle `idl-track` est identique partout → **5,3 Ko** répétés sur 77 occurrences.

C'est, de loin, la plus grosse source de poids superflu (≈ 64 Ko de HTML brut, ~6 % du dépôt).

### 2.2 Attributs `title=` longs répétés sur chaque axe

Les 3 libellés d'axe portent un `title="…"` explicatif identique (ex. axe A = 145 octets), répété **77 fois** par axe. Soit ~33 Ko cumulés pour 3 phrases qui ne changent jamais. Ces tooltips natifs sont par ailleurs peu accessibles (invisibles au clavier, au tactile).

### 2.3 JS inline dupliqué sur les pages-listes

Le même script de filtre/tri (~1,4 Ko) est ré-inséré inline dans `porteurs.html`, `usufruitiers.html`, `modeles.html`, `lieux.html` ; `classement.html` a sa propre variante (1,7 Ko). Total ≈ 7,3 Ko de JS jamais mis en cache (réécrit dans chaque HTML).

### 2.4 HTML non minifié

Le HTML généré est indenté et aéré (328 lignes à indentation dans `porteurs.html`). L'indentation des centaines de nœuds SVG/`axis-row` représente un volume non négligeable d'espaces et de sauts de ligne.

### 2.5 Métadonnées OG/Twitter verbeuses

13 balises `og:`/`twitter:` par page, avec `og:description` et `twitter:description` qui répètent mot pour mot le `meta description`. Mineur, mais factorisable.

### 2.6 Absence de cache-control / compression

Hors de portée d'un site statique pur, mais **notable** : GitHub Pages sert déjà le contenu en gzip et avec un `Cache-Control` correct sur les assets. Aucune action possible côté dépôt — simplement à garder en tête : c'est la compression gzip qui rend les redondances ci-dessus peu coûteuses *en transfert*, mais elles restent un coût en poids de dépôt et en temps de parsing.

## 3. Recommandations priorisées

### CRITIQUE — aucune (le site est déjà performant)

Aucun problème ne dégrade l'expérience utilisateur réelle. Les recommandations ci-dessous sont des optimisations de propreté et de poids, pas des correctifs urgents.

### IMPORTANTE

**B-1. Factoriser les parties fixes du triangle SVG via `<defs>` + `<use>`**
Définir une fois par page le cadre, la grille et les sommets dans un `<symbol>`/`<defs>` en tête de `<body>`, puis chaque carte ne rend que `<use href="#tri-base"/>` + le polygone `tri-fill` variable.
*Gain estimé : ~50 Ko de HTML brut sur l'ensemble du site (~5 % du dépôt). Sur `porteurs.html` seul : 13 triangles × ~400 o ≈ 5 Ko (de 45 Ko à ~40 Ko).* Modification localisée dans `generate_site.py` (fonction de rendu du triangle). N'enlève rien à l'usage : rendu visuel identique.

**B-2. Externaliser le JS des pages-listes dans `assets/list.js`**
Un seul fichier `assets/list.js` (filtre/tri générique) chargé en `<script defer src>` sur les 4 pages-listes ; idem `assets/rank.js` pour le classement.
*Gain : le JS passe en cache navigateur partagé — économie de ~5,5 Ko re-téléchargés à chaque navigation entre listes ; HTML allégé d'autant.* Conforme à l'autonomie (fichier local, pas de CDN).

### MINEURE

**B-3. Remplacer les `title=` d'axe répétés par une légende unique**
Les explications d'axe figurent déjà dans la légende `.axe-legend` en haut de page et sur `methode.html`. Supprimer les `title=` redondants des 231 `axis-label` (77 × 3).
*Gain : ~33 Ko de HTML brut cumulé. Bénéfice accessibilité : un tooltip natif est invisible au clavier/tactile ; la légende visible est meilleure.*

**B-4. Minifier le HTML à la génération**
Ajouter une passe de compactage en fin de `generate_site.py` (suppression de l'indentation et des sauts de ligne non significatifs hors `<pre>`).
*Gain : 10–15 % du HTML brut, soit ~100 Ko sur l'ensemble. Sans effet visible.* À garder lisible en dev via une option `--pretty`.

**B-5. Réutiliser le cercle `idl-track` de l'anneau via `<use>`**
Même principe que B-1 pour l'anneau IDL.
*Gain : ~5 Ko de HTML brut.*

**B-6. Dédupliquer `og:description` / `twitter:description`**
Twitter sait lire `og:description` ; supprimer la balise `twitter:description` (et `twitter:title`, couvert par `og:title`).
*Gain : ~3 balises × 45 pages ≈ 5–7 Ko. Négligeable mais propre.*

## 4. Synthèse des gains

| Reco | Priorité | Gain HTML brut estimé | Effort |
|---|---|---|---|
| B-1 `<use>` triangle | Importante | ~50 Ko | moyen |
| B-2 JS externalisé | Importante | ~5,5 Ko + cache | faible |
| B-3 retrait `title=` | Mineure | ~33 Ko | faible |
| B-4 minification HTML | Mineure | ~100 Ko | faible |
| B-5 `<use>` anneau | Mineure | ~5 Ko | faible |
| B-6 méta dédupliquées | Mineure | ~6 Ko | très faible |

**Gain cumulé potentiel : ~200 Ko de HTML brut**, soit le dépôt `site/` ramené d'environ 1,1 Mo à ~0,9 Mo, sans aucune perte fonctionnelle ni visuelle, et avec un bénéfice accessibilité (B-3) et de cache (B-2).

## 5. Note de méthode

Toutes les recommandations se appliquent dans `scripts/generate_site.py` (le `site/` est régénéré). Aucune ne requiert de CDN, de build tool externe ni de dépendance : l'autonomie du site est préservée. Le site est déjà performant pour l'utilisateur final ; ces optimisations améliorent la propreté du dépôt, le temps de parsing et la mise en cache.
