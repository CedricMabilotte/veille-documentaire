# Revue critique + durcissement — 6 juillet 2026

Suite de la session #22 (après l'arbitrage des 104 dates, commit `58a754a`).
Quatre demandes : disponibilité des thèmes sur les pages, dates incohérentes
dans la chronologie, page concepts qui ne charge pas, test de durcissement +
alimentation du manuel de bonnes pratiques transverse.

## 1. Page concepts qui ne charge pas

**Symptôme** : `https://biblio.actitude.org/concepts/index.html` affichait
« Les concepts n'ont pas pu se charger ». Confirmé en direct via Chrome
(console : `ReferenceError: BiblioSearch is not defined` à
`concepts/index.html:235`, dans `matchDocsForConcept` appelée depuis
`renderConceptIndex`).

**Cause** : `site/concepts/index.html` appelle `BiblioSearch.normalize()`
mais ne chargeait que `router.js`, `app.js`, `home.js` — sans `search.js`
(qui définit `BiblioSearch`). `site/fiches/index.html`, qui utilise la même
fonction, charge correctement `router.js` → `search.js` → `app.js` →
`home.js`.

Vérifié par grep négatif que `dossiers.html`, `auteurs.html`,
`chronologie.html`, `index.html` n'utilisent pas `BiblioSearch` — seule
`concepts/index.html` était concernée.

**Fix** : ajout de `<script src="../assets/js/search.js"></script>` avant
`app.js`, à l'identique de `fiches/index.html`. Commit `c8d2f86`. Vérifié en
direct après déploiement : la page rend les 5 concepts avec leurs compteurs.

## 2. Disponibilité des thèmes/palettes sur les pages

Deux dispositifs distincts existent : le bouton `.theme-toggle` (clair/sombre,
`localStorage` `biblio-theme`) et le bouton `.palette-toggle` (4 palettes —
Bibliothèque/Académique/Militant/Champêtre, `localStorage` `biblio-palette`),
tous deux initialisés par `app.js` (`initTheme()`, `initPalette()`).

Vérification sur les 11 gabarits de page (`index`, `dossiers`, `auteurs`,
`chronologie`, `concepts/index`, `une`, `apropos`, `etat-corpus`,
`fiches/index`, `fiches/fiche`, `404`) :

- `theme-toggle` : présent partout.
- `palette-toggle` : présent partout **sauf `404.html`**. Pas un bug
  fonctionnel (`initPalette()` a une garde `if (!btn) return`), juste une
  incohérence — corrigée par ajout du même markup que les autres pages.

**Fix** : commit `0409034`.

## 3. Dates incohérentes dans la chronologie

Le symptôme signalé initialement (docs du 16e siècle affichés comme publiés
au 20e) avait déjà été traité au niveau des données (`doc_date` en base,
arbitrage manuel des 104 cas). Mais le symptôme réapparaissait en direct sur
`chronologie.html`, preuve qu'une cause distincte du problème de données
subsistait au niveau du rendu.

### 3.a — `inferYear()` réinvente une fausse date côté client

`chronologie.html`, `fiches/fiche.html` (affichage + JSON-LD `datePublished`
+ export BibTeX) et `fiches/index.html` (filtre décennie) utilisent tous
`docYear(doc)` (`app.js`), qui — avant correction — retombait sur
`inferYear(doc)` quand `doc_date` était vide. Cette fonction cherchait un
motif AAAA dans `meta.creationDate` (date de numérisation PDF, pas de
publication), `filename` ou `link_text`, **sans aucun des garde-fous de
crédibilité déjà appliqués côté serveur** (`doc_metadata.build_metadata()` :
seuils 1950/1800, corroboration textuelle requise).

Vérification programmatique sur les 159 fiches publiées sans `doc_date` :
**41 auraient affiché une fausse année**, la plupart lues dans un fragment
du hash-UID qui préfixe systématiquement `filename` (ex. `a1543a19_...pdf`
→ année lue : 1543). Exemples réels : `b54759fb` (thèse 2008 sur le
Zimbabwe) → 1634 ; `ca782793` (article 2013 sur l'agroécologie) → 1523 ;
`ddc6e0b0` (article 2016 sur les coopératives) → 1507.

**Fix** : `inferYear()` supprimée, `docYear()` ne lit plus que `doc_date`.
Une fiche sans date fiable reste sans date — cohérent avec la politique déjà
en place pour les citations non vérifiées (masquer plutôt qu'inventer).
Commit `649e331`.

### 3.b — `site/data/catalog.json` périmé depuis le début de la session

Après le fix 3.a, le symptôme persistait (chronologie recommençait toujours
vers 1500-1600, avec d'autres titres). Investigation : `site/data/catalog.json`
(copie filtrée aux docs publiables, consommée par le JS client) n'avait
**jamais été resynchronisée** depuis le backfill/l'arbitrage des 159 dates —
ces scripts n'écrivent que dans `synopsis/catalog.json` (+ `bulles/*.json`
pour les citations). Seule `publish_site()` (fonction complète du pipeline,
non rappelée par les scripts de backfill ciblés) régénère ce fichier.

Vérifié : 110 `doc_date` différaient entre `synopsis/catalog.json` (à jour)
et `site/data/catalog.json` (périmé) au moment du contrôle.

**Fix** : script minimal (relit la source, ré-applique `_is_publishable()`,
écrit `site/data/catalog.json` — sans toucher au reste du pipeline
RSS/sitemap/cartes/exports pour ne pas produire un diff hors-sujet ni
risquer une collision avec la session parallèle). Commit `6cd5d32`.

**Vérification finale** (après propagation du cache CDN, voir §4) :
la chronologie live commence désormais en 1950 avec des dates réelles
(ex. *Combate*, *Lunes de Revolución* — presse cubaine 1959).

## 4. Test de durcissement

Angles couverts, méthode et résultat pour chacun :

- **Dépendances tierces** : aucun script CDN (`cdnjs`/`unpkg`/`jsdelivr`)
  chargé nulle part — zéro surface d'attaque supply-chain.
- **Échappement HTML** : fonction `escape()` unique (`app.js`), utilisée de
  façon cohérente à tous les points d'interpolation vérifiés (titres,
  résumés, liens). Aucune fuite trouvée sur les gabarits audités.
- **Liens externes** : les 10 occurrences de `target="_blank"` trouvées
  (`fiche.html` ×9, `home.js` ×1) ont toutes `rel="noopener"`.
- **Service worker** (`sw.js`) : stratégie network-only pour tout ce qui est
  cross-origin, cache-first uniquement pour les assets statiques
  same-origin, network-first pour le HTML et les JSON de données. Pas de
  vecteur de cache-poisoning identifié. `CACHE_VERSION` déjà auto-dérivé du
  SHA du commit publié à chaque déploiement (L36, session antérieure).
- **Secrets** : grep ciblé sur `site/` et `scripts/` — aucun secret en
  clair ; le seul token (`BIBLIO_PUBLISH_TOKEN`) est un secret GitHub
  Actions, jamais committé. Clé SSH de déploiement (`~/.ssh/id_biblio_push`)
  confirmée absente du dépôt.
- **En-têtes de sécurité HTTP** : GitHub Pages (y compris domaine
  personnalisé) ne permet **aucun** en-tête personnalisé (CSP, HSTS,
  X-Frame-Options, X-Content-Type-Options) — limite de plateforme actée,
  pas une négligence. HTTPS forcé (redirect 301 automatique) confirmé. Seule
  solution complète : proxy devant le domaine (Cloudflare). Mitigations déjà
  en place listées ci-dessus.
- **`robots.txt`** : `Allow: /` + référence au sitemap — cohérent, pas de
  fuite de chemins sensibles.
- **CDN du domaine personnalisé** : Fastly, `Cache-Control: max-age=600`
  sur les fichiers JSON, ignore la query string de cache-busting — a
  provoqué une fausse alerte pendant la vérification du fix 3.b (voir L44).

**Garde-fou renforcé** : `check_deploy.py` ne comparait que `app.js` et
`style.css` — c'est précisément ce qui a permis au problème 3.b de rester
invisible. Ajout de `data/catalog.json` comme sentinelle. Commit `a61850d`.

## 5. Manuel de bonnes pratiques transverse

Quatre entrées ajoutées à `~/Documents/Claude/Pratiques/manuel.md`
(généralisables au-delà de biblio) : 6.9bis (artefact dérivé non
resynchronisé après un backfill ciblé), 1.10 (logique de crédibilité
serveur contournée par un chemin client parallèle), 1.11 (cache CDN Fastly
sur domaine personnalisé GitHub Pages), 3.8 (limites d'en-têtes de sécurité
sur GitHub Pages + mitigations).

## Commits de la session

`c8d2f86` (fix concepts) → `649e331` (fix dates client) → `6cd5d32` (resync
catalog.json) → `0409034` (palette 404) → `a61850d` (garde-fou
check_deploy). Chaque push vérifié sans collision avec la session parallèle
(`git fetch` + `gh run list` avant/après chaque commit) et déployé avec
succès (`publish-only.yml`).
