# Cycle D — Étude : un comparateur de montages

Étude exploratoire du site statique « Terres Libérées ». Angle : faut-il
permettre la comparaison de deux (ou trois) montages côte à côte ? Si oui,
sous quelle forme la plus légère, en site statique autonome (JS vanilla,
aucune dépendance) ?

Date : 2026-05-23 · Lecture seule, aucune modification appliquée.

---

## Avis tranché

**À FAIRE — mais dans une version délibérément minimale.** Une page
« Comparer » à deux (et seulement deux) sélecteurs, rendu en deux colonnes,
sans triangle superposé, sans troisième entité. Le besoin est réel pour le
public visé ; le risque de surcharge est entièrement maîtrisable si l'on
s'en tient au strict nécessaire et qu'on réutilise les composants existants.

Ce qu'il ne faut **pas** faire : un mode comparaison greffé sur le
classement (cases à cocher dans le tableau + panneau flottant), ni un
comparateur à trois colonnes. Les deux alourdiraient `list.js`, la page
classement et le CSS pour un gain marginal — contraire à la commande
« sobre, pas surchargé ».

---

## Pourquoi c'est utile (et pour qui)

Le site sait déjà *noter* et *classer*, mais la comparaison fine est aujourd'hui
impossible :

- Le **classement** (`classement.html`) aligne tout le monde mais ne montre que
  A/B/C/IdL en mini-barres ; pas les critères de grille, pas les
  caractéristiques (forme juridique, type de montage, nature juridique).
- La **fiche** porte tout le détail (grille, en-bref, analyse) mais une seule
  entité à la fois ; comparer oblige à ouvrir deux onglets et faire l'aller-retour.
- Les **chips « Reliés dans l'annuaire »** ne relient que les fiches déjà liées
  entre elles (lieu ↔ son porteur ↔ son usufruitier) — jamais deux lieux
  concurrents, ni deux porteurs.

Le public — porteurs de projet et juristes — raisonne précisément par
comparaison de montages : « Terre de Liens fondation vs foncière », « fonds de
dotation vs fondation RUP », « démembrement vs bail emphytéotique ». Mettre deux
profils tri-axes et deux grilles en vis-à-vis répond directement à cette
question. C'est un usage central, pas un gadget.

**Réserve méthodologique importante :** trois grilles distinctes
(lieu / porteur / usufruitier), comme le rappelle déjà l'encart d'avertissement
du classement. Comparer un lieu et un porteur n'a pas de sens critère à critère.
Le comparateur doit donc, par défaut, **inviter à comparer des entités de même
catégorie** — et l'afficher clairement si l'utilisateur croise les catégories.

---

## Forme retenue : page « Comparer », deux colonnes, deux sélecteurs

Le choix le plus léger et le plus robuste. Une nouvelle page statique
`comparer.html` + un petit script `compare.js`. Le HTML de la page est quasi
vide à la génération ; tout le rendu se fait côté client depuis `data.json`,
**déjà publié** et déjà conçu comme export ouvert.

### Pourquoi pas le mode comparaison sur le classement

- Il faut ajouter des cases à cocher dans 28 lignes de tableau, gérer un état
  « 2 max sélectionnés », un panneau de comparaison, son ouverture/fermeture.
- `list.js` mélangerait alors filtre catégorie + tri colonnes + sélection
  comparaison : trois logiques dans un fichier qui en a déjà deux.
- Le tableau classement gagne en complexité visuelle (colonne de cases) pour
  tous les visiteurs, y compris ceux qui ne comparent pas.
- Gain réel faible par rapport à une page dédiée. **Écarté.**

### Pourquoi deux colonnes et pas trois

Trois colonnes : sur mobile (largeur ~380 px, cf. audit cycleB-mobile) elles
deviennent illisibles ou imposent un défilement horizontal ; le triangle et la
grille à trois exemplaires saturent l'écran. Deux colonnes tiennent en
empilement vertical propre sur mobile. La comparaison binaire couvre l'écrasante
majorité des besoins (« A ou B ? »). **Deux entités, point.**

---

## Ce que le comparateur affiche, par entité

Tout est dérivable de `data.json` actuel **sauf** les caractéristiques
descriptives et le détail de grille. Deux options :

- **Option légère (recommandée)** : le comparateur n'affiche que ce qui est
  déjà dans `data.json` — IdL, palier, axes A/B/C, complétude, score estimé/calculé
  — plus un lien « Voir la fiche complète ». Pas de détail de grille en vis-à-vis.
  Zéro modification du générateur côté données, sauf l'ajout des deux pages.
- **Option enrichie** : ajouter à `data.json` quelques champs descriptifs
  (`montage_type`, `forme_juridique`, `nature_juridique`, `sous_titre`) pour les
  afficher en colonnes. Léger surcoût générateur (~10 lignes dans `main()`),
  comparaison plus parlante.

**Recommandation : option enrichie sur les caractéristiques, mais SANS le
détail critère-par-critère de la grille.** Mettre 15-20 lignes de grille en
double colonne reproduirait la fiche et alourdirait franchement la page. La
synthèse par axe (le profil tri-axes + barres A/B/C) suffit à la comparaison ;
pour le détail, le lien « fiche complète » est à un clic.

---

## Plan d'implémentation léger et précis

### 1. Données — enrichir `data.json` (générateur, ~12 lignes)

Dans `main()`, bloc `data.json` (l. 2625-2635 de `generate_site.py`), ajouter à
chaque entrée quelques champs descriptifs déjà présents dans les fiches YAML :

```python
for f, sc in all_sc:
    mont = f.get("montage", {}) or {}
    pj = f.get("purete_juridique", {}) or {}
    data.append({
        "uid": f["uid"], "nom": f["nom"], "categorie": f["categorie"],
        "sous_titre": clean(f.get("sous_titre", "")),
        "idl": sc["idl"], "idl_brut": sc.get("idl_brut"),
        "score_type": sc.get("score_type"),
        "completude": (round(sc["completude"], 3)
                       if sc.get("completude") is not None else None),
        "axes": sc["axes"],
        "palier": sc["palier"]["id"] if sc["palier"] else None,
        # — champs ajoutés pour le comparateur —
        "forme_juridique": clean(f.get("forme_juridique", "")),
        "montage_type": mont.get("type", "") or "",
        "nature_juridique": pj.get("niveau", "") or "",
    })
```

Aucun changement de schéma cassant : l'export reste rétro-compatible (champs
ajoutés, aucun retiré). Penser à exporter aussi le **label** des paliers et des
montages, ou laisser `compare.js` recharger ces libellés — voir point 3.

### 2. Page — `render_comparer(cfg)` dans le générateur (~40 lignes)

Une fonction qui produit une page statique à structure fixe : deux `<select>`
construits depuis `all_sc` (groupés par catégorie via `<optgroup>`), et deux
conteneurs vides que `compare.js` remplira.

```python
def render_comparer(all_sc, cfg):
    project = cfg["concepts"]["project"]
    # options groupées par catégorie
    groups = {"lieu": [], "porteur": [], "usufruitier": [], "modele": []}
    for f, _ in all_sc:
        groups[f["categorie"]].append((f["uid"], f["nom"]))
    catlab = {"lieu": "Lieux", "porteur": "Porteurs",
              "usufruitier": "Usufruitiers", "modele": "Modèles voisins"}
    def opts():
        out = '<option value="">— Choisir —</option>'
        for cat, lab in catlab.items():
            items = sorted(groups[cat], key=lambda x: x[1])
            if not items:
                continue
            out += f'<optgroup label="{e(lab)}">'
            out += "".join(f'<option value="{e(u)}">{e(n)}</option>'
                            for u, n in items)
            out += '</optgroup>'
        return out
    body = f"""<h1>Comparer deux montages</h1>
<p class="lead">Choisissez deux entrées de l'annuaire pour voir leurs indices,
profils tri-axes et caractéristiques en vis-à-vis.
<a href="methode.html">Comprendre l'Indice →</a></p>
<div class="callout callout-warn"><p><strong>Comparer ce qui est comparable.</strong>
Lieux, porteurs et usufruitiers sont notés par trois grilles distinctes :
la comparaison critère à critère n'a de sens qu'entre entrées de même catégorie.</p></div>
<div class="cmp-pickers">
  <label>Montage A <select id="cmp-a">{opts()}</select></label>
  <label>Montage B <select id="cmp-b">{opts()}</select></label>
</div>
<p id="cmp-warn" class="note" role="status" hidden></p>
<div class="cmp-grid" id="cmp-grid"></div>
<noscript><p class="note">La comparaison nécessite JavaScript. Vous pouvez
consulter chaque fiche depuis le <a href="classement.html">classement</a>.</p></noscript>
<script defer src="assets/compare.js"></script>"""
    return page("Comparer", body, "comparer.html", project=project,
                description="Comparer deux montages de libération des terres : "
                            "indices, axes et caractéristiques en vis-à-vis.",
                path="comparer.html")
```

À câbler dans `main()` : `write(SITE / "comparer.html", render_comparer(all_sc, cfg))`,
et l'ajouter au `sitemap_paths` (priorité `0.6`).

### 3. Script — `compare.js` (~70 lignes vanilla, aucune dépendance)

Logique :

1. `fetch('data.json')` une fois, indexer par `uid`.
2. Lire `?a=uid&b=uid` dans l'URL au chargement pour pré-remplir les sélecteurs
   (permet de partager un lien de comparaison — utile pour les juristes).
3. Sur changement d'un `<select>` : mettre à jour l'URL (`history.replaceState`)
   et rerendre.
4. Rendu d'une colonne = un petit gabarit HTML : nom, badge IdL (chiffre +
   palier coloré), trois barres A/B/C, complétude, ligne « estimé » le cas
   échéant, caractéristiques (forme juridique, type de montage, nature),
   lien « Fiche complète ».
5. Si les deux entités n'ont pas la même `categorie` : afficher le message
   `#cmp-warn` (« grilles distinctes — comparaison indicative »), sans bloquer.

Le triangle SVG n'est **pas** indispensable côté JS : reconstruire `axis_triangle()`
en JavaScript dupliquerait de la géométrie. Les **barres A/B/C** suffisent à la
comparaison chiffrée et sont triviales à générer (une `<div>` à `width:N%`).
C'est le choix sobre. Les libellés de palier (couleur, nom) peuvent être
inlinés dans `compare.js` en petit objet constant, ou exportés dans un
`meta` de `data.json` — l'objet constant est plus simple et le jeu de paliers
est stable.

### 4. Navigation & CSS

- **NAV** : ne PAS ajouter d'entrée principale (la barre a déjà 6 entrées,
  volontairement limitée — cf. commentaire l. 277). Mettre « Comparer » dans le
  **footer** `foot-links`, à côté de « Méthode », et un lien depuis le chapô du
  **classement** (« Comparer deux entrées en vis-à-vis → »).
- **CSS** : ~25-30 lignes. `.cmp-pickers` (flex, deux `label` côte à côte),
  `.cmp-grid` (`display:grid;grid-template-columns:1fr 1fr;gap:1rem`, repassant
  à `1fr` sous 560 px), `.cmp-col` (réutilise le style `.card` existant). On
  réemploie au maximum `.axis-row`/`.axis-fill`/`.idl-pal` déjà définis.

### Coût total estimé

| Élément | Volume |
|---|---|
| `data.json` enrichi | ~10 lignes générateur |
| `render_comparer()` + câblage | ~45 lignes générateur |
| `compare.js` | ~70 lignes, nouveau fichier |
| CSS | ~30 lignes |
| Liens footer + classement | ~3 lignes |

Une page de plus, un fichier JS de plus, zéro dépendance, zéro impact sur les
pages existantes hors deux liens ajoutés. `list.js` n'est pas touché. C'est
proportionné et réversible.

---

## Garde-fous pour rester sobre

- **Deux entités, jamais trois.** Si la demande de 3 colonnes revient, la
  refuser : mobile + densité visuelle.
- **Pas de détail de grille en vis-à-vis.** Profil A/B/C + caractéristiques +
  lien fiche. Le critère-par-critère reste sur la fiche.
- **Pas de triangle SVG reconstruit en JS.** Barres horizontales seulement.
- **Pas dans la NAV principale.** Footer + renvoi depuis le classement.
- **Dégradation propre sans JS** (`<noscript>`), comme le reste du site.
- Réutiliser les classes CSS existantes (`.card`, `.axis-*`, `.callout`,
  `.idl-pal`) plutôt que créer un nouveau langage visuel.

Si l'une de ces lignes saute, le comparateur dérive vers la surcharge que le
commanditaire refuse. Tenues, elles donnent une fonctionnalité réellement utile
pour un coût marginal.
