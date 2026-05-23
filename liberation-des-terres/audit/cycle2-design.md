# Cycle 2 — Audit de design visuel et d'identité

**Objet.** Annuaire « Terres Libérées ». Audit en lecture seule du système visuel
(`site/assets/style.css`, constante `CSS` de `scripts/generate_site.py`, pages rendues).
Note méthodologique : le rendu navigateur (Claude-in-Chrome) n'était pas disponible ;
l'audit s'appuie sur une lecture experte du CSS et du HTML généré.

## Diagnostic d'ensemble

Le site n'est pas laid. Il a déjà des choix solides : fond papier, serif éditorial,
masthead à filet épais, palette terreuse. C'est un cran au-dessus du gabarit Bootstrap
moyen. Mais il reste **à mi-chemin** : la structure typographique est plate (un seul
niveau de titre vraiment travaillé), la palette est sous-exploitée (4 couleurs définies,
presque toutes cantonnées aux tags), les composants se ressemblent tous (même carte
beige, même bordure 1px, même radius 9px partout), et il manque les finitions qui
signent un référentiel sérieux : états focus, rythme vertical maîtrisé, hiérarchie
visuelle du score. Le hero, surtout, **rate sa promesse** : un paragraphe de 95 mots
en guise d'accroche. Aujourd'hui le site ressemble à un bon template ; il lui manque
un parti pris pour devenir une *publication*.

Incohérence technique relevée d'emblée : la couleur de l'axe B (`#bc4c3a`, issue de
`config/ranking.yml`) **diffère** du `--terra` du CSS (`#bc5d3a`). Deux terracotta
légèrement différents cohabitent sur la même page (tag Porteur vs barre axe B).

---

## RECOMMANDATIONS — Priorité CRITIQUE

### C1. Refondre le hero : promesse lisible en 3 secondes
**Problème.** `.hero-lead` reprend mot pour mot la meta-description : 95 mots, une seule
phrase, jargon juridique dès la 2ᵉ ligne. La promesse est noyée. `max-width:62ch` sur
du 1.12rem donne en plus une ligne trop longue pour un chapô.

**Quoi changer.**
- HTML (`generate_site.py`, bloc hero de `index.html`) : remplacer le pavé par un chapô
  court (25–35 mots max) — p.ex. « Partout en France, des terres sont sorties du marché
  spéculatif. Cet annuaire les recense, explique leurs montages juridiques et les note
  selon une grille d'analyse explicite. » Déplacer le texte juridique long dans la
  section « Le principe ».
- CSS : `.hero-lead{font-size:1.22rem;line-height:1.5;max-width:46ch;color:var(--ink);}`
  (passer en `--ink` plus dense, pas `--muted` : un chapô doit avoir du poids).
- Ajouter un sur-titre (eyebrow) au-dessus du h1 :
  `.hero-kicker{font-family:-apple-system,system-ui,sans-serif;font-size:.8rem;
  text-transform:uppercase;letter-spacing:.12em;color:var(--terra);font-weight:700;
  margin-bottom:.4rem;}` — texte type « Annuaire critique · France ».
- Donner de l'air et un fond distinct au hero :
  `.hero{padding:3.4rem 0 2.6rem;}` et envisager un léger dégradé papier ou un
  filet décoratif pour le séparer du flux.

### C2. Construire une vraie hiérarchie typographique
**Problème.** Il n'existe qu'un seul niveau de titre travaillé (`h1`). `h2.sec` est un
petit label sans-serif uppercase 0.95rem : ce n'est pas un titre de section, c'est une
étiquette. `h3` à 1.16rem est à peine au-dessus du corps (1rem). Du coup toutes les
pages intérieures (Larzac, Grilles) sont visuellement **plates** : aucune respiration,
aucun repère pour l'œil qui scanne.

**Quoi changer.**
- Introduire une échelle modulaire claire (ratio ~1.25) et l'assumer :
  `h1 2.6rem / h2 1.7rem / h3 1.22rem / corps 1.05rem / petit 0.875rem`.
- Donner à `h2.sec` un vrai poids de titre tout en gardant le filet :
  `h2.sec{font-size:1.5rem;font-family:inherit;text-transform:none;letter-spacing:-.01em;
  color:var(--ink);font-weight:600;border-bottom:1px solid var(--line);
  padding-bottom:.4rem;margin:3rem 0 1.2rem;}`.
  Si l'on tient au registre « label éditorial », alors le garder petit MAIS ajouter
  au-dessus un vrai `<h2>` serif — ne pas faire porter les deux rôles par un seul élément.
- Augmenter le contraste titre/corps sur `h3` : `font-size:1.28rem;font-weight:600;
  letter-spacing:-.005em;`.
- `.fiche-head h1` : actuellement collé au `.fiche-sub`. Donner `margin:.3rem 0 .15rem`
  au h1 et `font-size:1.08rem;line-height:1.45` au `.fiche-sub`.

### C3. Hiérarchiser le `.score-panel` — c'est le cœur de chaque fiche
**Problème.** Le panneau de score est traité comme un encadré ordinaire (même `--card`,
même bordure 1px, même radius). Or c'est l'information reine de la fiche. Le badge
`big` (`idl-num 2.6rem`) est juste posé à côté des barres, sans dominance, et
`.score-cap` est minuscule (0.74rem). Rien ne dit « voici la note ».

**Quoi changer.**
- Distinguer le panneau du reste : fond légèrement plus soutenu et bordure
  colorée selon le palier — `.score-panel{background:var(--card);
  border:1px solid var(--line);border-left:5px solid var(--pal,var(--green));
  border-radius:12px;padding:1.6rem 1.8rem;}` (faire remonter `--pal` sur le panel).
- Agrandir et asseoir le score : `.idl-badge.big .idl-num{font-size:3.4rem;
  line-height:1;}` et ajouter un séparateur vertical entre `.score-main` et
  `.score-axes` : `.score-axes{border-left:1px solid var(--line);padding-left:1.6rem;}`.
- `.score-cap` : `font-size:.78rem;letter-spacing:.08em;` — et le placer AU-DESSUS du
  chiffre, pas en dessous, pour qu'on lise « Indice de libération : 95 » naturellement.

---

## RECOMMANDATIONS — Priorité IMPORTANTE

### I1. Unifier et corriger la palette des axes
**Problème.** `#bc4c3a` (axe B, depuis `ranking.yml`) ≠ `--terra #bc5d3a` (CSS). Deux
rouges presque identiques mais pas tout à fait : c'est le genre de détail qui trahit
un site « bricolé ». Par ailleurs les trois couleurs d'axes (vert / terracotta / bleu)
sont correctes mais le bleu `#3b5b6b` est terne et peu différenciable du gris `--ink`
en petit format (les `.axe-dot` font 0.62rem).

**Quoi changer.**
- Aligner `config/ranking.yml` sur les variables CSS : axe A `#4a7a3a`, axe B `#bc5d3a`,
  axe C — remonter le bleu vers `#36748a` (plus saturé, meilleure distinction).
  Idéalement, définir les couleurs d'axes comme variables CSS (`--axe-a/-b/-c`) et que
  le générateur les référence, pour une source unique de vérité.
- Vérifier le contraste : terracotta `#bc5d3a` sur papier `#f5f2e9` ≈ 3.2:1 — suffisant
  pour une barre/dot mais **insuffisant pour du texte** (`.crit-partiel` en gold,
  `.an-frag`). Pour le texte, n'utiliser que les variantes `-dk`.

### I2. Différencier les familles de composants
**Problème.** `.card`, `.cat-card`, `.enbref`, `.an-col`, `.axe-card`, `.strat`,
`.score-panel`, `.fiab-box` partagent quasiment tous le même habillage : fond `--card`
ou `#efe9d8`, bordure `1px solid --line`, radius 9–10px. Résultat : aucune hiérarchie
de lecture, tout a le même « poids » visuel. Les pages Grilles et Méthode deviennent
une succession de rectangles beiges.

**Quoi changer.**
- Établir 3 niveaux d'encadré et s'y tenir :
  - **Primaire** (score, à-la-une) : ombre portée + bordure colorée.
  - **Secondaire** (cartes navigables `.card`, `.cat-card`) : bordure 1px, hover marqué.
  - **Tertiaire** (`.enbref`, `.fiab-box`, encarts d'info) : pas de bordure, simple
    fond `#efe9d8` ou filet latéral 3px — distinguer « bloc cliquable » de « bloc info ».
- Harmoniser les radius : choisir **une** valeur (8px) et l'appliquer partout. Aujourd'hui
  on a 3px, 4px, 5px, 6px, 8px, 9px, 10px, 20px — c'est du bruit.
- Les `.an-col` (Forces / Fragilités / Leviers) : très réussis avec leur filet
  supérieur coloré. En faire le **modèle** du composant « analyse » et retirer la
  bordure complète, ne garder que le filet de 3px + fond.

### I3. États focus et accessibilité visuelle
**Problème.** Aucune règle `:focus` / `:focus-visible` dans tout le CSS. Les boutons
filtres `.fbtn`, l'input `[type=search]`, tous les liens : navigation clavier invisible.
Pour un « référentiel sérieux », c'est rédhibitoire.

**Quoi changer.**
- Ajouter un anneau de focus global :
  `a:focus-visible,button:focus-visible,input:focus-visible{outline:2px solid var(--green);
  outline-offset:2px;border-radius:3px;}`.
- `.toolbar input:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(74,122,58,.15);}`.
- `.cta:focus-visible` : anneau contrasté (le vert sur vert ne suffit pas — utiliser
  `outline-color:var(--ink)`).

### I4. Rythme vertical et densité
**Problème.** `line-height:1.62` sur du serif à 1rem, c'est un peu lâche pour de
longues proses juridiques (la fiche Larzac enchaîne 5 sections de prose dense).
Les marges de section sont irrégulières (`h2.sec` margin-top 2.6rem, mais `.score-panel`
1.2rem, `.enbref` 1.1rem). Pas de grille de rythme.

**Quoi changer.**
- Corps de prose : `line-height:1.58` et `.prose{max-width:68ch;}` (la largeur de
  ligne idéale pour du serif est 60–70 caractères ; certaines proses n'ont aucune
  contrainte de largeur et s'étalent sur 1080px).
- Adopter un rythme par multiples de 0.4rem : sections espacées de `2.8rem`,
  sous-blocs de `1.6rem`, éléments de `.8rem`. Remplacer les valeurs au cas par cas.
- `.enbref dl` : `gap:.55rem 1.6rem` et aligner `dt` en `font-weight:600` plutôt que
  juste `--faint` (un terme de définition doit se repérer).

### I5. Tableaux — densité et lisibilité du classement
**Problème.** Le tableau `.rank-tbl` (21 lignes) et les grilles (`.grille-tbl`,
~14 lignes) sont fonctionnels mais ternes : `border-bottom` 1px partout, aucun
striping, en-têtes en `--faint` 0.78rem à peine visibles, pas de hover de ligne.
Sur 21 lignes l'œil se perd entre A/B/C/IdL.

**Quoi changer.**
- Hover de ligne : `.rank-tbl tbody tr:hover{background:#efe9d8;}`.
- Striping discret pour le classement : `.rank-tbl tbody tr:nth-child(even) td{
  background:rgba(221,212,191,.18);}` (compatible avec le hover).
- En-têtes plus présents : `table th{color:var(--muted);font-size:.72rem;
  border-bottom:2px solid var(--ink);}` — le filet épais sépare nettement l'en-tête.
- Colonne IdL : la mettre en valeur visuelle — `.rank-tbl td.idl-cell{
  border-left:1px solid var(--line);}` pour isoler la note de synthèse des trois axes.
- `.fam-row` (ligne de famille) : déjà bien, mais ajouter `border-top:2px solid var(--line)`
  pour marquer le début de groupe.

### I6. Le badge d'indice — finition
**Problème.** `.idl-badge` empile num + label dans une bordure 2px. En petit format
(cartes), le label `idl-pal` à 0.6rem est quasi illisible. La variante `idl-estime`
avec son hachuré diagonal est astucieuse mais lourde visuellement.

**Quoi changer.**
- Carte : masquer le label texte sous une certaine taille et ne garder que le chiffre
  coloré + une pastille de palier ; OU agrandir `idl-pal` à 0.66rem avec
  `line-height:1.2`.
- Donner au badge un fond très léger teinté du palier plutôt que blanc :
  `.idl-badge{background:color-mix(in srgb,var(--pal) 8%,var(--card));}` — le badge
  « vibre » alors avec sa couleur de palier.
- `idl-estime` : remplacer le hachuré agressif par une simple bordure `dashed` +
  l'italique sur le chiffre (déjà présent) ; retirer le `repeating-linear-gradient`.

---

## RECOMMANDATIONS — Priorité MINEURE

### M1. Logo / marque
`.logo-mark` (« TL » sur pavé vert, radius 5px) fait très « app SaaS ». Pour un
référentiel éditorial, envisager un traitement plus sobre : monogramme sans fond, ou
filet d'encadrement fin. À défaut, au moins aligner son radius (8px) et lui donner
`letter-spacing:0` (le -.03em serre trop deux lettres déjà étroites).

### M2. Navigation active
`.topnav a.active` ne se distingue de `:hover` que par… rien (mêmes règles). Ajouter
`font-weight:600` à `.active` pour que la page courante se repère sans survol.

### M3. Micro-transitions
Les `.card:hover` ont une transition (bien), mais `.cta`, `.fbtn`, `.chip`, `.topnav a`
changent d'état sans transition — effet « sec ». Ajouter `transition:.15s ease` sur
`background`, `color`, `border-color` pour ces éléments.

### M4. Liens dans la prose
`a{color:var(--green-dk)}` sans soulignement : dans un corps de texte serif dense, les
liens « Comprendre la grille → », « Méthode détaillée → » se distinguent mal. Souligner
les liens en prose (`.prose a,.lead a{text-decoration:underline;
text-underline-offset:2px;text-decoration-thickness:1px;}`) tout en gardant les liens
de navigation/cartes sans soulignement.

### M5. Footer
`.footer` reprend `--card` : il se fond presque dans la dernière carte de la page.
Lui donner le fond `--paper` ou un beige légèrement plus soutenu, et augmenter le
contraste du texte (`--muted` sur `--card` est faible). Le filet `2px solid --ink`
en haut est bon.

### M6. `.prose.synthese` et encarts colorés
La synthèse stratégique (`#efe9d8` + filet vert gauche) est un bon pattern. Le
généraliser : en faire un composant `.callout` réutilisable avec variantes
`.callout--note / --warn` (filet gold / terracotta) pour les avertissements
juridiques, plutôt que des styles ad hoc.

### M7. Responsive
Un seul breakpoint à 620px. Les cartes `minmax(300px,1fr)` et la grille `enbref`
(`max-content 1fr`) se comportent mal entre 620 et 900px (tablette). Ajouter un
breakpoint intermédiaire ~860px : réduire `h1` à 2.1rem, passer `.score-panel` en
colonne, et tester le tableau `.rank-tbl` (7 colonnes) qui déborde probablement —
prévoir un `overflow-x:auto` sur un conteneur table.

### M8. Numériques
Bien : `font-variant-numeric:tabular-nums` est déjà appliqué sur `.axis-val`, `.num`.
À étendre à `.idl-num` et `.idl-cell b` pour que les scores s'alignent parfaitement.

---

## Synthèse — ce qu'il faut pour « l'allure d'un référentiel sérieux »

Trois leviers, dans l'ordre :

1. **Un hero qui tient sa promesse** (C1) — aujourd'hui le visiteur doit lire 95 mots
   pour comprendre. Un kicker + h1 + chapô de 30 mots changerait tout.
2. **Une hiérarchie typographique assumée** (C2) — passer d'un système plat à une
   échelle modulaire à 4 niveaux nets donne instantanément le ton « publication ».
3. **Une hiérarchie de composants** (C3, I2) — distinguer le primaire (score) du
   tertiaire (encarts info) par l'ombre, la couleur de bordure et le radius unifié.

Le reste (focus, palette unifiée, rythme, tableaux) relève de la finition — mais
c'est précisément la finition qui sépare un template d'un référentiel soigné.
