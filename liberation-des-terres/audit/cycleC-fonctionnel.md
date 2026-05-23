# Cycle C — Audit fonctionnel & non-régression

Audit du site statique « Terres Libérées ». Angle : fonctionnement du
générateur, intégrité des pages produites, JavaScript (`assets/list.js`),
SVG factorisés (`<defs>`/`<use>`), cartes *stretched-link*, cohérence de
l'Indice de libération. Recherche de régressions introduites par les
cycles A et B.

Date : 2026-05-23 · Générateur exécuté sur Python 3.12.3, PyYAML 6.0.1.

---

## Synthèse

Le site est **fonctionnellement sain**. Le générateur tourne sans erreur ni
warning ; les 41 pages attendues sont produites (33 fiches + 8 transverses) ;
`ferme-des-enfards` est bien supprimée ; la page `regimes.html` (cycle A) est
présente. Le JavaScript des catalogues et du classement a été testé
logiquement (Node) : filtres, tri et recherche fonctionnent, y compris sur
les valeurs accentuées et apostrophées. Les SVG `<use>`/`<defs>` se résolvent
sans `id` orphelin ni doublon. Les cartes *stretched-link* n'emprisonnent
aucun autre lien. L'Indice de libération a été **recalculé depuis la grille**
pour les 28 fiches notées : zéro écart avec `data.json` et avec le HTML.

**Un seul vrai défaut** : une fragilité de portabilité du générateur
(f-string Python 3.12+). Le reste relève du cosmétique / angle mort de
données.

| Priorité | Nombre |
|----------|--------|
| Critique | 0 |
| Importante | 1 |
| Mineure | 4 |

---

## Vérifications passées (aucune anomalie)

- **Générateur** : `python3 scripts/generate_site.py` → exit 0, sortie
  « Site généré : 33 fiches, 8 lieux / 13 porteurs / 7 usufruitiers /
  5 modèles ». Aucun warning même avec `-W all`.
- **Pages produites** : 8 `l/`, 13 `p/`, 7 `u/`, 5 `m/`, plus index,
  classement, regimes, grilles, glossaire, methode, suggerer, 404,
  catalogues `lieux/porteurs/usufruitiers/modeles.html`, `data.json`,
  `sitemap.xml` (44 URL), `robots.txt`, `CNAME`, assets. `ferme-des-enfards`
  absente partout.
- **JS catalogues** : recherche par nom (`indexOf` sur `dataset.nom`
  minuscule), tri (`idl/nom/axa/axb/axc`), filtres `palier/montage/region`
  testés sur le DOM réel de `lieux.html` — résultats corrects, y compris le
  filtre région « Provence-Alpes-Côte d'Azur » (apostrophe `&#x27;`
  re-décodée à l'identique côté carte et côté bouton).
- **JS classement** : 28 lignes, 7 cellules chacune, 5 en-têtes triables,
  filtre par catégorie cohérent avec `data-cat`. `cellVal` gère « — » → -1.
- **`<details>` filtres** : balises bien fermées ; le JS interroge les
  `.fbtn` par classe/ID au chargement, indépendamment de l'état
  ouvert/fermé du `<details>` — aucune rupture.
- **SVG `<defs>`/`<use>`** : `id="tri-base"` émis une seule fois par page
  (jamais de doublon), aucun `<use href="#tri-base">` orphelin. Le triangle
  pleine taille des fiches reste un SVG autonome (pas de `<use>`).
- **Stretched-link** : les cartes de catalogue ne contiennent qu'une seule
  ancre (`.card-link`) ; les chips « Reliés dans l'annuaire » sont hors
  `.card`. Aucun lien emprisonné.
- **Indice de libération** : recalcul depuis `grilles.yml` + `ranking.yml`
  pour les 28 fiches notées → `idl`, `idl_brut`, `axes` identiques à
  `data.json` (0 écart). Indice estimé des 5 modèles cohérent (moyenne
  arrondie des axes éditoriaux). Indice affiché en HTML = `data.json` pour
  les 33 fiches.
- **Liens internes** : 0 lien relatif cassé ; les liens absolus de
  `404.html` (`/index.html`, etc.) résolvent à la racine.
- **`data.json`** : JSON valide, 33 entrées. `sitemap.xml` : XML valide.

---

## Anomalies

### IMPORTANTE — I1. f-string non portable : le générateur ne tourne que sur Python 3.12+

**Localisation** : `scripts/generate_site.py`, fonction `page()`, ligne 236.

```python
f'<a href="{up}{href}"{" class=\'active\'" if href == active else ""}>{e(label)}</a>'
```

Le champ de remplacement contient un *backslash* (`\'`) pour échapper une
apostrophe réutilisant le délimiteur de la f-string. C'est **uniquement
légal depuis Python 3.12** (PEP 701). Sur Python 3.6 à 3.11, le module
lève `SyntaxError: f-string expression part cannot include a backslash`
**au chargement** — le script ne démarre pas du tout.

Impact réel : le workflow CI épingle `python-version: "3.12"`, donc la
publication automatique n'est pas cassée. Mais le docstring annonce un
script « sans dépendance hors PyYAML » sans mention de version minimale ;
tout contributeur sur une distribution avec Python ≤ 3.11 (Debian 12 =
3.11, Ubuntu 22.04 = 3.10) verra le générateur planter au lancement.
Régression introduite par le cycle B (NAV réécrit en compréhension de
f-string).

**Correctif** — sortir l'expression de la f-string, sans backslash :

```python
def page(title, body, active, depth=0, project=None, description="",
         path="", jsonld=None, og_type="website", robots=None):
    up = "../" * depth
    nav_items = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ''
        nav_items.append(f'<a href="{up}{href}"{cls}>{e(label)}</a>')
    nav = "".join(nav_items)
```

Bénéfice annexe : la classe passe de `class='active'` (apostrophes) à
`class="active"` (guillemets doubles), plus conforme au reste du HTML
généré.

---

### MINEURE — M1. Boutons de filtre « palier » sans cible sur la page Modèles

**Localisation** : `render_catalogue()`, génération de `pal_btns` ;
visible dans `site/modeles.html`.

Les boutons de filtre par palier sont générés à partir de **tous** les
paliers de `ranking.yml` (5 boutons : abouti, solide, engage, partiel,
eloigne). Or les 5 modèles voisins ne portent que `data-palier="abouti"`
ou `"solide"`. Cliquer « Engagement réel », « Libération partielle » ou
« Éloigné du modèle » sur `modeles.html` masque toutes les cartes et
affiche « Aucune entrée ne correspond ». Comportement non cassé mais
trompeur (boutons morts).

**Correctif** — n'émettre que les paliers présents dans le sous-ensemble,
comme c'est déjà fait pour les montages (`present_mont`) :

```python
present_pal = []
for f, s in fiches_sc:
    pid = s["palier"]["id"] if s["palier"] else None
    if pid and pid not in present_pal:
        present_pal.append(pid)
pal_order = [p for p in ranking["paliers"] if p["id"] in present_pal]
pal_btns = "".join(
    f'<button class="fbtn" data-fk="palier" data-fv="{p["id"]}">'
    f'{e(p["label"])}</button>' for p in pal_order)
```

---

### MINEURE — M2. `<defs>` `tri-base` émis mais inutilisé sur les fiches modèles sans relation

**Localisation** : `render_fiche()` — `body` commence par `tri_defs(axes_cfg)`.

Une fiche modèle (`m/ofs-brs.html` p.ex.) reçoit le bloc `<defs id="tri-base">`
en tête de `<main>`, mais ne rend aucun triangle compact : son triangle de
score est autonome et elle n'a pas de chips reliés (`<use>` count = 0). Le
`<defs>` est alors du SVG mort (invisible, `width="0"`), sans effet visuel
ni bug — purement du poids inutile (~300 octets).

**Correctif** (facultatif, optimisation) — n'émettre `tri_defs()` que si la
fiche aura au moins un triangle compact, c'est-à-dire si `chips` est non
vide. À placer après le calcul de `liens_html` :

```python
defs = tri_defs(axes_cfg) if chips else ""
body = (defs + head + score_block + ...)
```

Faible priorité : aucun impact fonctionnel.

---

### MINEURE — M3. Tri « par nom » du classement pollué par le sous-titre

**Localisation** : `assets/list.js`, second IIFE, fonction `cellVal` ;
colonne « Entrée » de `classement.html`.

La cellule nom contient le lien **et** un `<span class="row-sub">` avec le
sous-titre. `cellVal` lit `tr.cells[i].innerText`, qui concatène
« Nom\nSous-titre ». Le tri alphabétique se fait donc sur la chaîne
« nom + sous-titre ». Comme le nom vient en premier, le classement reste
correct dans l'immense majorité des cas ; il ne diffèrerait que pour deux
entrées de nom strictement identique (cas absent du corpus).

**Correctif** — cibler le texte du lien seul :

```javascript
function cellVal(tr,i,type){
  var cell=tr.cells[i];
  var t=(type==='num') ? cell.innerText.trim()
       : (cell.querySelector('a')||cell).textContent.trim();
  if(type==='num') return t==='—'?-1:(parseFloat(t)||0);
  return t.toLowerCase();
}
```

---

### MINEURE — M4. Axe à 0 réel et axe non renseigné indistinguables au tri

**Localisation** : `card()` — `data-axa="{ax.get("A") or 0}"` (idem B, C).

Un axe dont le score vaut authentiquement 0 et un axe `None` (non
renseigné) sortent tous deux comme `0` dans `data-axa/b/c`. Le tri
« par axe » des catalogues les place donc ensemble en bas de liste. La
carte distingue pourtant visuellement les deux cas (arête hachurée). Le
corpus actuel ne contient pas d'axe authentiquement nul, donc l'effet est
théorique aujourd'hui.

**Correctif** (préventif) — émettre `-1` pour un axe `None` afin de le
trier sous un vrai 0, ou émettre une valeur vide et la traiter dans le tri.
Faible priorité tant que le corpus n'a pas d'axe à 0.

---

## Conclusion

Aucun bug critique ni régression bloquante des cycles A/B. Le site est
publiable en l'état via la CI (Python 3.12). La seule correction réellement
recommandée est **I1** (portabilité du générateur) — une ligne à réécrire,
sans changement de rendu. Les quatre points mineurs sont des finitions
(boutons morts sur Modèles, SVG mort, propreté du tri) sans incidence
fonctionnelle visible sur le corpus actuel.
