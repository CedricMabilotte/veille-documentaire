# Cycle 2 — Audit de la visualisation du classement et des données

Annuaire « Terres Libérées ». Audit en lecture seule des composants de
dataviz : `axis_bar()`, `idl_badge()`, `card()`, `render_classement()`,
`render_fiche()`, et des styles correspondants dans `style.css`.

Périmètre des données : 21 entrées notées (lieux/porteurs/usufruitiers) +
4 modèles voisins estimés. Indice 0–100, trois axes A/B/C (moyenne égale),
cinq paliers.

> Note méthode : l'audit a été conduit sur le code Python, le CSS et les
> pages HTML rendues (`classement.html`, `index.html`, `l/larzac.html`,
> `m/clt-bruxelles.html`, `data.json`). Le rendu navigateur n'a pas pu être
> ouvert (outils Claude-in-Chrome indisponibles) ; les jugements visuels
> s'appuient donc sur la lecture du CSS — fiables sur la structure, à
> reconfirmer visuellement pour le rendu pixel.

Toutes les propositions sont réalisables en HTML/CSS/SVG inline généré par
Python, sans dépendance externe ni framework. Un peu de JS vanilla est
employé là où c'est strictement nécessaire (tri du tableau).

---

## Constat d'ensemble

Le socle est sain : le code est lisible, les couleurs passent par des
variables CSS, les axes sont déjà colorés de façon cohérente (A vert,
B terracotta, C bleu), les pastilles `axe-dot` accompagnent toujours la
couleur d'un libellé texte. Trois faiblesses structurantes ressortent :

1. **Le badge d'Indice ne montre pas le 0–100.** `idl_badge()` affiche un
   nombre nu dans un cadre coloré. Rien ne situe « 95 » ou « 51 » sur
   l'échelle. Le palier est en toutes lettres, mais le lecteur doit déjà
   connaître les seuils pour interpréter.
2. **Le profil tri-axes n'est jamais lisible d'un coup d'œil.** Trois barres
   horizontales empilées se lisent séquentiellement, ligne par ligne. On ne
   « voit » pas qu'un montage est fort en B et faible en C : il faut lire
   trois nombres et les comparer mentalement. C'est le point le plus coûteux
   de tout le site, car le profil tri-axes EST le propos éditorial.
3. **Aucune vue de comparaison ni de synthèse de corpus.** Le classement est
   un tableau de chiffres bruts ; l'accueil n'a aucun visuel d'ensemble ;
   il n'existe nulle part de comparaison côte à côte de plusieurs montages.

Le détail point par point suit, classé par priorité.

---

# RECOMMANDATIONS CRITIQUES

## C1 — Remplacer les trois barres horizontales par un mini-triangle tri-axes

**Problème.** `axis_bar()` produit trois `.axis-row` empilées. La lecture est
séquentielle : le lecteur ne perçoit pas le *profil* (la forme) d'un montage,
seulement trois mesures isolées. Or l'intérêt éditorial de l'annuaire est
précisément de montrer qu'un montage peut être « fort en B, faible en C ».
Trois barres ne racontent pas cette histoire ; une figure tri-axes oui.

**Avis tranché sur la meilleure représentation des trois axes.**
Trois familles ont été pesées :

- *Radar / toile d'araignée* à 3 sommets : techniquement c'est un triangle,
  et un radar à seulement 3 axes dégénère en un triangle déformé difficile à
  lire (les aires trompent l'œil, un sommet à 100 et deux à 50 paraît
  « plus gros » qu'il n'est). **Écarté.**
- *Barres horizontales actuelles* : honnêtes, accessibles, mais sans pouvoir
  de synthèse. À **conserver en complément** sur la fiche détaillée (lecture
  précise), pas comme visuel principal.
- *Triangle de profil* (recommandé) : un triangle équilatéral fixe sert de
  cadre « 100 sur les trois axes ». À l'intérieur, un polygone à 3 points
  relie les valeurs A/B/C placées chacune sur la médiane de son sommet. La
  forme du polygone EST le profil : centré = équilibré, étiré vers un sommet
  = montage spécialisé. C'est compact (≈ 110×100 px), lisible en vignette
  comme en grand, et chaque sommet porte une couleur d'axe + une lettre.

**→ Recommandation : adopter le triangle de profil comme visuel tri-axes
principal (cartes, fiche, classement en survol), et conserver les barres
horizontales `axis_bar()` uniquement dans le panneau de score de la fiche,
pour la lecture chiffrée précise.**

**Composant SVG à ajouter — `axis_triangle(axes_cfg, axes_scores, size=110)`.**

Géométrie. Triangle équilatéral, sommet A en haut, B en bas-droite, C en
bas-gauche (ou ordre stable). Le centre de gravité G correspond à la valeur 0
sur les trois axes ; chaque sommet à la valeur 100. Pour un axe de valeur
`v` (0–100), le point se place sur le segment G→sommet à la fraction
`v/100`. Trois points → un polygone rempli semi-transparent + contour.

Esquisse (viewBox 0 0 120 110, sommets calculés en Python) :

```
<svg class="tri" viewBox="0 0 120 110" role="img"
     aria-label="Profil : intérêt général 100, libération 100, gouvernance 86">
  <!-- cadre 100% -->
  <polygon points="60,8 112,98 8,98" fill="none"
           stroke="var(--line)" stroke-width="1"/>
  <!-- graduation 50% (triangle médian, pointillé) -->
  <polygon points="60,53 86,98 34,98" fill="none"
           stroke="var(--line)" stroke-width="1" stroke-dasharray="2 2"/>
  <!-- profil mesuré -->
  <polygon points="Ax,Ay Bx,By Cx,Cy"
           fill="rgba(74,122,58,.18)" stroke="var(--ink)" stroke-width="1.5"/>
  <!-- sommets colorés + lettres -->
  <circle cx="60" cy="8" r="3" fill="#4a7a3a"/>
  <text x="60" y="4" class="tri-lab">A</text>
  ... B, C ...
</svg>
```

Calcul des points en Python (à insérer dans `generate_site.py`, section
Composants, après `axis_bar`) :

```python
import math

def _tri_geom(size=120):
    # sommets équilatéraux d'un triangle inscrit, centre G
    cx, cy, r = size/2, size*0.46, size*0.42
    verts = {}
    for i, ax in enumerate(("A", "B", "C")):       # A haut, puis sens horaire
        ang = -math.pi/2 + i*2*math.pi/3
        verts[ax] = (cx + r*math.cos(ang), cy + r*math.sin(ang))
    return (cx, cy), verts

def axis_triangle(axes_cfg, axes_scores, size=120, compact=False):
    (gx, gy), verts = _tri_geom(size)
    pts, missing = [], []
    for ax in ("A", "B", "C"):
        v = axes_scores.get(ax)
        vx, vy = verts[ax]
        if v is None:
            missing.append(ax)
            f = 0.0                      # axe n.r. ramené au centre
        else:
            f = max(0.0, min(1.0, v/100))
        pts.append(f"{gx+(vx-gx)*f:.1f},{gy+(vy-gy)*f:.1f}")
    frame  = " ".join(f"{x:.1f},{y:.1f}" for x, y in verts.values())
    mid    = " ".join(f"{gx+(x-gx)*0.5:.1f},{gy+(y-gy)*0.5:.1f}"
                       for x, y in verts.values())
    label  = "Profil tri-axes : " + ", ".join(
        f"{a} {axes_scores.get(a) if axes_scores.get(a) is not None else 'non renseigné'}"
        for a in ("A", "B", "C"))
    dots = ""
    for i, ax in enumerate(axes_cfg):
        vx, vy = verts[ax["id"]]
        na = " tri-na" if ax["id"] in missing else ""
        dots += (f'<circle class="tri-vtx{na}" cx="{vx:.1f}" cy="{vy:.1f}" '
                 f'r="3.4" fill="{ax["couleur"]}"/>'
                 f'<text class="tri-lab" x="{vx:.1f}" y="{vy:.1f}">'
                 f'{ax["id"]}</text>')
    cls = "tri compact" if compact else "tri"
    return (f'<svg class="{cls}" viewBox="0 0 {size} {size*0.92:.0f}" '
            f'role="img" aria-label="{e(label)}">'
            f'<polygon class="tri-frame" points="{frame}"/>'
            f'<polygon class="tri-grid" points="{mid}"/>'
            f'<polygon class="tri-fill" points="{" ".join(pts)}"/>'
            f'{dots}</svg>')
```

CSS (ajouter au bloc `CSS`) :

```css
.tri{width:120px;height:auto;display:block;}
.tri.compact{width:84px;}
.tri-frame{fill:none;stroke:var(--line);stroke-width:1;}
.tri-grid{fill:none;stroke:var(--line);stroke-width:1;stroke-dasharray:2 2;}
.tri-fill{fill:rgba(74,122,58,.16);stroke:var(--ink);stroke-width:1.5;
 stroke-linejoin:round;}
.tri-vtx.tri-na{fill:none;stroke:var(--faint);stroke-width:1;
 stroke-dasharray:2 1.5;}
.tri-lab{font:700 7px -apple-system,system-ui,sans-serif;fill:var(--paper);
 text-anchor:middle;dominant-baseline:central;}
```

**Où l'insérer.**
- `card()` : remplacer `axis_bar(axes_cfg, sc['axes'], compact=True)` par
  `axis_triangle(axes_cfg, sc['axes'], compact=True)`. La carte gagne en
  densité et en lisibilité immédiate.
- `render_fiche()` / `score_block` : à côté de l'`idl_badge` big, ajouter le
  triangle en grand format ; **garder `axis_bar()`** en dessous pour le
  détail chiffré. Le triangle donne la forme, les barres donnent les nombres.

**Accessibilité.** L'attribut `aria-label` énonce les trois valeurs ;
les sommets portent la lettre A/B/C en plus de la couleur ; le profil est
une forme, donc lisible même en niveaux de gris. Garder un fond de polygone
clair pour le contraste du contour `--ink`.

---

## C2 — Faire du badge d'Indice une jauge 0–100, pas un nombre nu

**Problème.** `idl_badge()` rend `<span class="idl-num">95</span>` dans un
cadre dont seule la *couleur de bordure* varie selon le palier. Le lecteur
ne voit pas que 95 est « presque au maximum » et que 51 est « bas ».
L'échelle 0–100 est invisible : le badge ne communique qu'un nombre + un
mot.

**Recommandation : badge avec anneau de progression SVG.** Un anneau
(donut) circulaire est le compromis idéal pour un score unique 0–100 :
compact, fonctionne en vignette comme en grand, le « plein » de l'arc dit
immédiatement la position sur l'échelle, le nombre reste au centre, la
couleur du palier renforce sans être seule porteuse de sens.

Une alternative — jauge linéaire (barre horizontale graduée avec curseur) —
est aussi acceptable et un peu plus précise sur la position exacte ; mais
elle occupe plus de largeur et s'intègre moins bien dans le coin d'une
carte. **L'anneau est recommandé pour le badge ; la jauge linéaire est
réservée au panneau de score grand format de la fiche (C2-bis).**

**Composant — réécrire `idl_badge()` :**

```python
def idl_badge(sc, big=False):
    idl, pal = sc["idl"], sc["palier"]
    if idl is None or pal is None:
        return '<span class="idl-badge idl-na">n.r.</span>'
    estime = sc.get("score_type") == "estime"
    r, sw = (34, 7) if big else (15, 3.4)          # rayon, épaisseur
    c = 2*math.pi*r
    off = c*(1 - idl/100)
    box = (r+sw)*2
    pal_lab = e(pal["label"]) + (" · estimé" if estime else "")
    cls = "idl-badge big" if big else "idl-badge"
    if estime:
        cls += " idl-estime"
    num_sz = "1.55rem" if big else ".82rem"
    return (
      f'<span class="{cls}" style="--pal:{pal["couleur"]}">'
      f'<svg class="idl-ring" viewBox="0 0 {box} {box}" role="img" '
      f'aria-label="Indice de libération {idl} sur 100, {e(pal["label"])}">'
      f'<circle class="idl-track" cx="{box/2}" cy="{box/2}" r="{r}" '
      f'stroke-width="{sw}"/>'
      f'<circle class="idl-arc" cx="{box/2}" cy="{box/2}" r="{r}" '
      f'stroke-width="{sw}" stroke-dasharray="{c:.1f}" '
      f'stroke-dashoffset="{off:.1f}" '
      f'transform="rotate(-90 {box/2} {box/2})"/>'
      f'<text class="idl-num" x="{box/2}" y="{box/2}" '
      f'style="font-size:{num_sz}">{idl}</text>'
      f'</svg>'
      f'<span class="idl-pal">{pal_lab}</span></span>')
```

CSS (remplace les règles `.idl-badge*` existantes) :

```css
.idl-badge{display:inline-flex;flex-direction:column;align-items:center;
 gap:.15rem;line-height:1.1;}
.idl-ring{width:42px;height:42px;}
.idl-badge.big .idl-ring{width:92px;height:92px;}
.idl-track{fill:none;stroke:#e6ddc6;}
.idl-arc{fill:none;stroke:var(--pal,#999);stroke-linecap:round;
 transition:stroke-dashoffset .4s;}
.idl-num{fill:var(--pal,#999);font-weight:800;text-anchor:middle;
 dominant-baseline:central;font-family:-apple-system,system-ui,sans-serif;}
.idl-pal{font-size:.6rem;text-transform:uppercase;letter-spacing:.04em;
 color:var(--muted);text-align:center;}
.idl-badge.big .idl-pal{font-size:.74rem;}
.idl-na{display:inline-block;border:2px solid var(--faint);color:var(--faint);
 border-radius:8px;padding:.3rem .6rem;}
.idl-estime .idl-arc{stroke-dasharray:4 3;}      /* arc tireté = estimé */
.idl-estime .idl-num{font-style:italic;}
```

L'arc tireté pour les modèles estimés conserve le signal « estimé » sans
recourir au seul motif de fond. La transition CSS est purement décorative
(le SVG est statique au chargement).

**C2-bis — jauge linéaire dans le panneau de score.** Sous le badge grand
format de `render_fiche()`, ajouter une barre 0–100 avec les seuils de
palier marqués, pour situer l'indice dans le corpus :

```html
<div class="idl-scale" role="img" aria-label="Indice 95 sur 100, paliers à 50, 64, 76, 88">
  <span class="idl-scale-track">
    <!-- bandes de palier (largeurs = seuils) -->
    <span class="seg" style="left:0;width:50%;background:#8f3829"></span>
    <span class="seg" style="left:50%;width:14%;background:#bc4c3a"></span>
    <span class="seg" style="left:64%;width:12%;background:#b08431"></span>
    <span class="seg" style="left:76%;width:12%;background:#4a7a3a"></span>
    <span class="seg" style="left:88%;width:12%;background:#2f6b34"></span>
    <span class="idl-cursor" style="left:95%"></span>
  </span>
</div>
```

Les bandes se génèrent en Python depuis `ranking["paliers"]` (déjà triés) ;
le curseur est positionné à `idl%`. CSS : `.idl-scale-track` hauteur ~10px,
`.seg` en `position:absolute`, `.idl-cursor` un trait vertical sombre de
2–3px dépassant la barre. Cela rend les seuils de palier *visibles* au lieu
de figurer seulement dans une légende textuelle.

---

## C3 — Tableau de classement : mini-barres en cellule + tri par colonne

**Problème.** `render_classement()` rend les colonnes A/B/C en chiffres bruts
(`cell()` → `<td class="num">100</td>`). 21 lignes × 3 colonnes de nombres :
le lecteur ne distingue pas d'un coup d'œil les profils, ne repère pas les
points faibles d'une catégorie. De plus, **aucun tri par colonne** : on ne
peut pas reclasser par axe B ou par gouvernance C, alors que c'est l'usage
naturel d'un tableau analytique.

**Recommandation 3a — mini-barre datavisuelle dans chaque cellule A/B/C.**
Conserver le nombre (lecture exacte, accessibilité) mais l'adosser à une
micro-barre de fond proportionnelle, colorée à la couleur de l'axe.
Réécrire `cell()` :

```python
def cell(v, col):
    if v is None:
        return '<td class="num axc"><span class="cbar-na">—</span></td>'
    return (f'<td class="num axc" style="--w:{v}%;--ac:{col}">'
            f'<span class="cbar"></span><span class="cv">{v}</span></td>')
```

Appel : `cell(a.get('A'), '#4a7a3a')` etc. (les couleurs viennent déjà de
`axes_cfg`). CSS :

```css
.axc{position:relative;}
.axc .cbar{position:absolute;left:0;bottom:0;height:3px;width:var(--w,0);
 background:var(--ac,#999);opacity:.8;}
.axc .cv{position:relative;font-variant-numeric:tabular-nums;}
.cbar-na{color:var(--faint);}
```

Une barre fine de 3px au bas de la cellule transforme la colonne en
mini-histogramme lisible verticalement, sans masquer le chiffre. Variante
plus dense : code couleur de fond de cellule (heatmap) — déconseillé car le
fond coloré nuit au contraste du texte ; la barre de pied est préférable.

**Recommandation 3b — tri par colonne (JS vanilla).** Rendre les `<th>` des
colonnes A, B, C, IdL cliquables (tri ascendant/descendant), avec un
indicateur de sens (▲▼). Le JS reste léger et autonome :

```javascript
const tbl=document.querySelector('.rank-tbl'),
      tb=tbl.tBodies[0],
      ths=[...tbl.tHead.rows[0].cells];
function val(tr,i){const t=tr.cells[i].innerText.trim();
  return t==='—'?-1:parseFloat(t)||0;}
ths.forEach((th,i)=>{
  if(!th.classList.contains('sortable'))return;
  th.addEventListener('click',()=>{
    const dir=th.dataset.dir==='asc'?-1:1;
    ths.forEach(x=>x.removeAttribute('data-dir'));
    th.dataset.dir=dir===1?'asc':'desc';
    [...tb.rows].sort((a,b)=>(val(a,i)-val(b,i))*dir)
                .forEach((r,n)=>{tb.appendChild(r);
                  r.cells[0].textContent=n+1;});
  });
});
```

Marquer les `<th>` triables avec `class="sortable"` et un libellé accessible
(`aria-sort`, mis à jour côté JS). Conserver le filtre par catégorie existant
— les deux interactions sont compatibles. Recalculer le numéro de rang après
chaque tri (déjà fait dans le filtre, à factoriser).

**Accessibilité.** Le tri ajoute `aria-sort="ascending|descending"` sur le
`<th>` actif ; les `<th>` triables sont des `<button>` internes ou portent
`tabindex="0"` + gestion de la touche Entrée pour rester utilisables au
clavier. La mini-barre est purement décorative (`aria-hidden` implicite, pas
de texte) : le chiffre reste la donnée lue par les lecteurs d'écran.

---

# RECOMMANDATIONS IMPORTANTES

## I1 — Page d'accueil : visuel de synthèse du corpus

**Problème.** L'accueil n'offre aucune vue d'ensemble : 6 cartes « en tête de
classement » et c'est tout. Le lecteur ne perçoit ni la taille du corpus,
ni sa distribution (combien d'aboutis ? combien de partiels ?).

**Recommandation — histogramme de distribution des paliers, en SVG.** Un
bloc « État du corpus » sur l'accueil (et utilement repris sur `methode.html`)
avec un histogramme empilé ou cinq barres, une par palier, hauteur =
nombre d'entrées, couleur = couleur du palier. Le corpus actuel : 4 aboutis,
3 solides, 6 engagés, 8 partiels, 0 éloigné — une distribution qui se
raconte d'un coup d'œil.

Composant `corpus_histogram(all_sc, ranking)` : compter les entrées par
`palier["id"]` (hors modèles estimés, ou en série distincte), produire un
`<svg>` de barres. viewBox ~ `0 0 320 160`. Chaque barre : un `<rect>` +
le compte au-dessus + le libellé du palier dessous. Hauteur proportionnelle
au max. Optionnellement une seconde série discrète pour les 4 modèles.

```python
def corpus_histogram(all_sc, ranking):
    paliers = ranking["paliers"]                  # haut → bas
    counts = {p["id"]: 0 for p in paliers}
    for f, s in all_sc:
        if f["categorie"] == "modele":            # estimés exclus
            continue
        if s["palier"]:
            counts[s["palier"]["id"]] += 1
    mx = max(counts.values()) or 1
    W, H, pad = 340, 170, 28
    bw = (W - 2*pad) / len(paliers)
    bars = ""
    for i, p in enumerate(reversed(paliers)):     # bas → haut de l'échelle
        n = counts[p["id"]]
        bh = (H - 2*pad) * n / mx
        x = pad + i*bw
        y = H - pad - bh
        bars += (f'<rect x="{x+6:.1f}" y="{y:.1f}" width="{bw-12:.1f}" '
                 f'height="{bh:.1f}" fill="{p["couleur"]}" rx="2"/>'
                 f'<text class="hg-n" x="{x+bw/2:.1f}" y="{y-4:.1f}">{n}</text>'
                 f'<text class="hg-l" x="{x+bw/2:.1f}" y="{H-pad+12:.1f}">'
                 f'{e(p["label"])}</text>')
    return (f'<figure class="corpus-hist"><svg viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="Répartition des {sum(counts.values())} '
            f'entrées notées par palier">{bars}</svg>'
            f'<figcaption>Répartition des entrées notées par palier '
            f'd’Indice de libération.</figcaption></figure>')
```

CSS : `.hg-n{font:700 11px sans-serif;text-anchor:middle;fill:var(--ink);}`,
`.hg-l{font:9px sans-serif;text-anchor:middle;fill:var(--muted);}`. Insérer
dans `render_index()` une section « État du corpus » avant ou après les
cartes de tête, et idéalement réutiliser le composant dans `render_methode()`
(section « État du corpus » actuellement purement textuelle).

## I2 — Une vue de comparaison de plusieurs montages

**Problème.** Rien ne compare visuellement plusieurs entrées. Le tableau les
juxtapose en chiffres ; aucune page ne montre les profils côte à côte.

**Recommandation — deux dispositifs complémentaires, tous deux sans JS lourd.**

a) **Nuage de dispersion B × C** sur la page classement (ou méthode) : un
plan SVG, axe horizontal = libération B, axe vertical = gouvernance C,
chaque entrée un point coloré par catégorie, taille ∝ axe A (ou IdL). Cela
révèle d'un coup les montages « forts foncier / faible gouvernance » (bas-
droite) vs équilibrés (haut-droite). viewBox `0 0 360 360`, marges pour les
graduations 0/50/100. Chaque point : `<circle>` + `<title>` (infobulle
native accessible) portant le nom et les trois valeurs. Composant
`scatter_bc(core_sc)`.

b) **Profils côte à côte** : réutiliser le triangle C1. Sur la fiche, dans la
section « Reliés dans l'annuaire », afficher pour chaque entrée liée son
mini-triangle sous la puce — le lecteur compare directement le profil de la
fiche courante et de ses voisins. Aucune nouvelle page nécessaire, simple
réemploi de `axis_triangle(compact=True)` dans la boucle `chips`.

Le nuage de dispersion est la priorité de I2 : c'est la seule vue qui donne
une lecture *relationnelle* du corpus.

## I3 — Récapitulatif visuel de la grille par axe (fiche)

**Problème.** `render_fiche()` rend la grille en tableau oui/partiel/non/
inconnu, regroupé par famille. La lecture critère par critère est correcte
mais il n'y a aucune synthèse : combien de « oui » sur l'axe B ? La couleur
des cellules (`.crit-oui` vert, `.crit-non` terracotta) aide ligne à ligne
mais ne se totalise pas.

**Recommandation — bandeau récap par axe, en tête du tableau de grille.**
Pour chaque axe A/B/C, une mini-barre segmentée montrant la part de oui /
partiel / non / inconnu parmi ses critères :

```python
def grille_recap(criteres_evalues, gril, axes_cfg):
    order = ["oui", "partiel", "non", "inconnu"]
    seg_col = {"oui":"var(--green)","partiel":"var(--gold)",
               "non":"var(--terra)","inconnu":"#cfc6b0"}
    rows = ""
    for ax in axes_cfg:
        crit_ids = [cr["id"] for fam in gril.get("familles",[])
                    for cr in fam["criteres"] if cr["axe"]==ax["id"]]
        tally = {k:0 for k in order}
        for cid in crit_ids:
            ev = criteres_evalues.get(cid)
            tally[ev["valeur"] if ev else "inconnu"] += 1
        tot = sum(tally.values()) or 1
        segs, txt = "", []
        for k in order:
            if not tally[k]: continue
            segs += (f'<span class="rk-seg" style="width:{tally[k]/tot*100:.1f}%;'
                     f'background:{seg_col[k]}" title="{tally[k]} {k}"></span>')
            txt.append(f"{tally[k]} {k}")
        rows += (f'<div class="rk-row"><span class="rk-ax">'
                 f'<span class="axe-dot axe-{ax["id"]}"></span>{e(ax["label"])}'
                 f'</span><span class="rk-bar">{segs}</span>'
                 f'<span class="rk-txt">{e(" · ".join(txt))}</span></div>')
    return f'<div class="grille-recap">{rows}</div>'
```

CSS : `.rk-bar` une piste flex de ~120px, `.rk-seg` des blocs `display:inline-
block` accolés ; `.rk-txt` répète le décompte en toutes lettres (couleur
jamais seule porteuse de sens). Insérer juste sous le `<h2>Grille de
lecture</h2>`, avant le `<table>`. Le lecteur voit instantanément « axe C :
1 oui, 1 partiel, 1 non » avant de plonger dans le détail.

---

# RECOMMANDATIONS MINEURES

## M1 — Modèles estimés : afficher les axes sans décimales
`data.json` et les fiches modèles affichent `90.0` (les `axes_estimes` sont
des `float`). `axis_bar()` rend `width:90.0%` et `<span class="axis-val">
90.0</span>`. Cosmétique mais visible. Dans `axis_bar()`, formater :
`txt = str(int(val)) if val == int(val) else str(val)` — ou arrondir à
l'entier dans `score_fiche()` pour le cas `modele`. Le triangle de C1
prend déjà `v/100` donc n'est pas affecté, mais le `aria-label` le serait.

## M2 — Légende de palier : rendre les chips actifs
`.paliers-legend` affiche les 5 paliers avec seuil. Une fois le tri C3 en
place, ces chips peuvent devenir des filtres (clic = ne montrer que ce
palier), cohérents avec les boutons de catégorie. Optionnel.

## M3 — Pénalité de complétude : la rendre visible sur la fiche
`score_fiche()` calcule `idl` (pénalisé) et `idl_brut`. La fiche n'affiche
que `idl` ; `idl_brut` n'apparaît nulle part malgré la promesse de la page
méthode (« conservé et affiché pour information »). Sur la jauge linéaire
C2-bis, ajouter un repère fantôme à la position `idl_brut` (petit triangle
clair) pour visualiser l'écart dû à la complétude. Sinon, une mention
`<span class="completude">Indice brut 80, ramené à 68 (grille à 70 %).</span>`.
Améliore la transparence, déjà revendiquée éditorialement.

## M4 — Carte : l'attribut `data-idl` est inexploité
`card()` pose `data-idl` mais aucune page ne s'en sert (le tri des
catalogues se fait par nom seulement). Soit ajouter un tri par indice dans
les catalogues (`render_catalogue`), soit retirer l'attribut. Cohérence
mineure.

## M5 — Contraste du jaune `--gold` / `#b08431`
Le palier « engagement réel » et `.crit-partiel` utilisent un ocre
(`#b08431` / `#b0843a`). Sur fond papier `#f5f2e9`, le ratio de contraste du
texte ocre est limite pour du petit texte (à vérifier ≥ 4.5:1 ; il est
probablement autour de 3:1). Recommandation : assombrir l'ocre utilisé pour
le *texte* (ex. `#8a6420`) tout en gardant le ton clair pour les
*remplissages* (barres, segments), où le contraste texte ne s'applique pas.
À confirmer au rendu navigateur.

## M6 — Triangle et barres : ne jamais coder l'info par la seule couleur
Transversal, déjà bien respecté ailleurs (les `axe-dot` accompagnent
toujours un libellé). Pour les nouveaux composants : le triangle porte les
lettres A/B/C sur ses sommets ; les mini-barres du tableau gardent le
chiffre ; l'histogramme garde les libellés de palier ; les segments du
récap I3 répètent le décompte en texte. À tenir comme règle pour tout ajout.

---

# Synthèse — ordre d'intégration recommandé

| Prio | Reco | Effort | Impact |
|------|------|--------|--------|
| Critique | C1 Triangle tri-axes | Moyen | Très fort — c'est le cœur du propos |
| Critique | C2 Badge en anneau 0–100 | Faible | Fort — partout sur le site |
| Critique | C3 Mini-barres + tri colonne | Moyen | Fort — page classement |
| Importante | I1 Histogramme de corpus (accueil) | Faible | Moyen-fort |
| Importante | I2 Nuage B×C + profils voisins | Moyen | Moyen-fort |
| Importante | I3 Récap grille par axe | Faible | Moyen |
| Mineure | M1–M6 | Faible | Finitions / accessibilité |

Aucune de ces propositions n'introduit de dépendance externe : tout est du
SVG/CSS généré par Python, plus deux poignées de JS vanilla (tri du tableau,
filtres optionnels). Le site reste un statique autonome.
