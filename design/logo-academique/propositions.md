# BIBLIO — thème Académique : trois propositions pour les visuels de la charte

Proposé par @Graphiste, 2026-10-07. À trancher par Ced. Rien n’est appliqué dans `site/`.

Préalable, un manque structurel : il n’existe pas de `resources/shared/identites/identite-biblio.yaml`.
La seule source de vérité de l’identité est aujourd’hui `site/assets/css/style.css`, ce qui explique
que les visuels générés hors CSS (cartes sociales, favicon, og) soient restés sur l’ancienne palette.
Créer ce fichier de niveau 1 (palette Académique, typo, marque, règles d’usage) est une décision de Ced. C’est aussi la condition
pour que `scripts/social_cards.py` lise ses couleurs au lieu de les recopier en dur.

## Intégration de la marque (rappel, hors propositions)

- Dans l’en-tête, remplacer `<img src="assets/img/logo.svg" class="brand-mark">` par
  `<svg class="brand-mark" aria-hidden="true"><use href="assets/img/logo.svg#mark"/></svg>`.
  Avec un `<img>`, le SVG ne voit ni `color` ni les variables de la page : il resterait figé en clair.
  Avec `<use>`, il hérite de `color: var(--text)` et de `--brand-accent`.
- Variables à ajouter côté CSS (session principale) :
  `[data-palette="academique"] { --brand-accent: var(--gold); }`. Le thème sombre suit tout seul.
- Le `.brand` de base garde l’étiquette déchirée (rotation −1,6°, `clip-path`, scotch `::before`,
  fond `--bg-elev`) : la surcharge Académique ne la neutralise pas. Avec la marque sobre, il faut
  `transform:none; clip-path:none; background:none; box-shadow:none;` et `.brand::before{display:none}`.
- `.brand-mark` peut passer de 32 à 40 px. À 48 px, l’en-tête gagne environ 16 px de hauteur.
- Le favicon PNG (`icon-192.png`, `icon-512.png`) et `og-default.png` sont à re-rasteriser depuis les SVG. Utiliser
  Chrome headless, polices chargées (EB Garamond n’est pas installée sur la machine, donc
  rsvg ou ImageMagick retomberaient sur Georgia/DejaVu) :
  `google-chrome --headless=new --hide-scrollbars --window-size=1200,630 --screenshot=og-default.png og-default.svg`
  Le SVG doit d’abord être enveloppé dans une page HTML qui charge `fonts.css`, sinon on obtient Georgia.

---

## 1. Cartes sociales par fiche : les aligner sur Académique

**Problème observé.** `scripts/social_cards.py` produit les 2 218 images de `site/assets/cards/`
(carte 1200×630, portrait, citations). Elles reprennent toutes l’ancienne identité : fond parchemin
`(247,242,231)`, terre cuite `(164,74,44)`, grain papier, scotch, coin corné, tampon rond
« 8/10 VÉRIFIÉ » en monospace. Les polices sont DejaVu/Liberation. À chaque partage
(Mastodon, Bluesky, messageries), la fiche se présente donc avec une identité que le site a abandonnée.
C’est le visuel le plus vu hors du site.

**Proposition.** Un gabarit unique, sobre. Fond blanc, filet vertical marine de 24 px à gauche, marque
en haut à gauche (40 px). En haut, un kicker en Inter 600 capitales espacées (type de document · année).
Le titre est en EB Garamond 600, 56 px, sur trois lignes au plus, et l’auteur en Inter 28 px `#3f4a60`.
Le score devient une pastille rectangulaire discrète (« Fiabilité 8/10 », or `#7a6321`). Le tampon disparaît, il appartenait au registre militant.
Effets supprimés : `_paper_grain`, `_paste_tape`, `_dogear`, `_stamp`.
Les couleurs doivent être lues depuis le futur `identite-biblio.yaml`.

**Effort.** Moyen. Il faut réécrire environ 150 lignes du script et livrer les TTF EB Garamond et Inter avec le script
(dans `scripts/fonts/`, pas dans les polices système). Il faut ensuite régénérer 2 218 images (lot local, quelques minutes)
et vider les caches des réseaux, qui gardent l’ancienne carte plusieurs jours.
Pour juger le résultat, la taille réelle est celle de l’aperçu Mastodon, environ 500 px de large. À cette taille, le titre à 56 px descend à environ 23 px. Il reste lisible, mais pas en dessous.

**Mini-exemple** (maquette de la carte, 1200×630) :

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#fff"/>
  <rect width="24" height="630" fill="#1f3a5f"/>
  <text x="80" y="110" font-family="Inter,sans-serif" font-size="22" font-weight="600" letter-spacing="3" fill="#1f3a5f">OUVRAGE · 2019</text>
  <text x="80" y="210" font-family="EB Garamond,serif" font-size="56" font-weight="600" fill="#1a2233">La propriété d’usage</text>
  <text x="80" y="276" font-family="EB Garamond,serif" font-size="56" font-weight="600" fill="#1a2233">contre la rente foncière</text>
  <text x="80" y="340" font-family="Inter,sans-serif" font-size="28" fill="#3f4a60">Auteur Exemple</text>
  <rect x="80" y="520" width="190" height="44" rx="4" fill="none" stroke="#7a6321" stroke-width="2"/>
  <text x="96" y="550" font-family="Inter,sans-serif" font-size="20" font-weight="600" fill="#7a6321">Fiabilité 8/10</text>
  <text x="1120" y="550" text-anchor="end" font-family="Inter,sans-serif" font-size="20" font-weight="600" letter-spacing="2" fill="#1f3a5f">BIBLIO.ACTITUDE.ORG</text>
</svg>
```

Option à trancher : (a) une seule carte, fond blanc, quel que soit le thème du lecteur. C’est le choix le plus simple, et les réseaux
affichent l’image telle quelle. (b) Une variante sombre `#0f1620`, pour les fils de discussion sombres. Elle double le nombre de fichiers, et la plupart des
plateformes ne savent pas choisir entre deux `og:image`. Ma recommandation est (a).

---

## 2. Couverture par défaut des fiches sans image

**Problème observé.** 854 fiches pour 798 couvertures : environ 56 fiches affichent le placeholder.
C’est une initiale en Garamond 80 px `--text-faint` sur `--bg-elev`. Elle est injectée par un `onerror`
dans `site/fiches/fiche.html` (ligne ~402) qui écrit six propriétés de style en ligne. Le résultat est un
rectangle presque vide, qui se lit comme une image cassée et pas comme un choix. Les styles en ligne
échappent en plus au thème : impossible de les régler depuis le CSS.

**Proposition.** Une « couverture de notice » purement CSS, typographique, cohérente avec la marque. Bandeau
marine en tête, avec le type de document en Inter capitales. Titre en EB Garamond au centre, auteur dessous.
Filet or et marque en pied. Le `onerror` se contente d’ajouter une classe (`cover--notice`) et de poser
`data-title` / `data-author`, et tout le rendu passe en CSS, donc il suit clair et sombre.
Ces fiches deviennent visuellement des notices de catalogue et ne se lisent plus comme des trous.

**Effort.** Faible. Une vingtaine de lignes de CSS (session principale ou @neo) et une ligne de JS dans `fiche.html` et
dans la carte de liste (`.book-cover.placeholder`). Le texte reste en HTML, rien à générer.

**Mini-exemple** :

```css
.cover--notice{
  display:flex;flex-direction:column;justify-content:space-between;
  aspect-ratio:3/4;padding:0 0 14px;background:var(--bg-card);
  border:1px solid var(--border);color:var(--text);
}
.cover--notice::before{ /* bandeau type de document */
  content:attr(data-type);display:block;padding:8px 12px;
  background:var(--accent);color:var(--bg);
  font:600 10px/1 var(--font-sans);letter-spacing:.12em;text-transform:uppercase;
}
.cover--notice .t{font:600 clamp(15px,2.2vw,22px)/1.15 var(--font-serif);padding:0 12px;text-wrap:balance}
.cover--notice .a{font:400 12px/1.3 var(--font-sans);color:var(--text-dim);padding:0 12px}
.cover--notice::after{ /* filet or */
  content:"";display:block;width:32px;height:2px;margin:0 12px;background:var(--gold);
}
```

À juger à la taille réelle de la grille du catalogue. Si la carte descend sous 120 px de large,
le titre passe sous 13 px : il faut alors tronquer à trois lignes (`-webkit-line-clamp:3`).

---

## 3. Typographie : héberger Inter et nettoyer les polices résiduelles

**Problème observé.** Le thème déclare `font-family: "Inter", system-ui…`, mais `site/assets/css/fonts.css`
n’héberge que EB Garamond, Special Elite et Caveat. Inter n’est jamais chargée. Le corps du texte s’affiche
donc en San Francisco sur Mac, en Segoe UI sous Windows, en Roboto ou Cantarell sous Linux. Le gris, la chasse
et l’interlignage changent d’une machine à l’autre, et le « lettrage académique » n’est pas tenu.
En sens inverse, Special Elite et Caveat (thèmes organique et militant, maintenant supprimés) sont encore déclarées
et encore référencées (1 occurrence dans `style.css`, 5 dans `components.css`). Ce sont des octets inutiles,
et un risque de voir réapparaître une écriture manuscrite dans un encart.

**Proposition.**
1. Héberger Inter en variable woff2, sous-ensemble latin + latin-ext (≈ 90–110 Ko pour 400–700), avec `font-display: swap`.
   L’alternative est d’assumer `system-ui` et de retirer « Inter » de la pile pour ne pas promettre ce qu’on ne livre pas.
2. Retirer Special Elite et Caveat de `fonts.css` et `components.css` après vérification des usages.
3. Fixer une hiérarchie de titres courte, à graver dans `identite-biblio.yaml` :
   h1 Garamond 600 / 0,02em, h2 Garamond 600, h3 Inter 600, kicker Inter 600 capitales / 0,12em / `--accent`.
   Les encarts (`.citation-block`) prennent un filet gauche marine de 3 px et un fond `--bg-alt`. Pas d’italique long.

**Effort.** Faible pour 1 et 2 (un fichier de police, quelques lignes de CSS, un grep).
Moyen pour 3, qui demande de passer en revue les sélecteurs `font-family: var(--font-serif)` (une cinquantaine dans `style.css`).

**Mini-exemple** :

```css
@font-face{
  font-family:"Inter";font-style:normal;font-weight:400 700;font-display:swap;
  src:url("../fonts/inter-latin-var.woff2") format("woff2");
}
[data-palette="academique"] .section-kicker{
  font:600 11px/1.2 var(--font-sans);letter-spacing:.12em;text-transform:uppercase;color:var(--accent);
}
[data-palette="academique"] .citation-block{
  border-left:3px solid var(--accent);background:var(--bg-alt);padding:12px 16px;font-style:normal;
}
```

Option à trancher : (a) Inter hébergée, pour un rendu identique partout (+100 Ko au premier chargement).
(b) `system-ui` assumé, sans poids ajouté, mais le rendu varie selon l’OS. Avec (b), il faut retirer « Inter » de la déclaration.
