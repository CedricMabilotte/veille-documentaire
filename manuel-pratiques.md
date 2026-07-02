# Manuel des bonnes pratiques — actitude.org
> Document vivant · À déplacer à terme vers un dossier parent partagé à tous les projets.  
> Chaque projet alimente ce fichier. Ce fichier irrigue tous les projets.

**Emplacement cible** : `/home/ced/Documents/Claude/Pratiques/manuel.md`  
**Initialisation** : 2026-07-02 · Source : projet biblio  
**Dernière mise à jour** : 2026-07-02

---

## Table des matières

- [N0 — Fondements](#n0--fondements-méta-de-la-méta)
- [N1 — Architecture](#n1--architecture-méta)
- [N2 — Audit](#n2--audit)
- [N3 — Interface](#n3--interface)
- [N4 — Fonctions](#n4--fonctions)
- [N5 — Contenus](#n5--contenus)
- [N6 — Pipeline](#n6--pipeline)
- [Projets](#projets)
- [Changelog](#changelog)

---

## N0 — Fondements (méta de la méta)

> Ce qui ne changera pas. Principes invariants qui gouvernent tous les choix ultérieurs.  
> Si une décision contredit ce niveau, c'est le niveau inférieur qui doit céder.

### 0.1 Philosophie

- **Ouverture par défaut** : les contenus produits sont sous licence ouverte (CC-BY-NC-SA au minimum). Le code est public.
- **Pas de traceur, pas de publicité** : aucun pixel tiers, aucune régie, aucune collecte de données comportementales.
- **Le lecteur d'abord** : chaque décision technique se justifie par l'expérience du lecteur, pas par la commodité du développeur.
- **Transparence éditoriale** : les biais, angles morts et limites des corpus sont documentés publiquement (cf. page Corpus sur biblio).

### 0.2 Contraintes non négociables

| Contrainte | Raison |
|---|---|
| Aucun JS tiers chargé au runtime | Vie privée + performance |
| Aucun `localStorage` avec données personnelles | RGPD |
| Toutes les pages rendues sans JS (au moins minimalement) | Accessibilité, SEO, crawlers |
| Polices Google Fonts via preconnect uniquement (aucun tracking) | Compromis perf/vie-privée acceptable |
| Contact toujours via email direct, jamais un formulaire tiers | Contrôle des données |

### 0.3 Axiomes techniques

1. **Static-first** : générer du HTML statique est toujours préférable à du rendu serveur ou client-side pour le contenu pérenne.
2. **Graceful degradation** : chaque fonctionnalité JS doit avoir un état HTML de repli lisible et navigable.
3. **Séparation données / présentation** : les données (JSON, YAML) ne doivent jamais être mélangées au code de rendu. Un changement de données ne doit pas nécessiter de modifier le code.
4. **Auditabilité** : tout pipeline automatisé doit pouvoir être rejoué, arrêté, et repris. Les logs doivent permettre de diagnostiquer sans exécuter.
5. **Minimalisme des dépendances** : préférer la bibliothèque standard Python / les APIs navigateur natives avant d'introduire une dépendance externe.

---

## N1 — Architecture (méta)

> Patterns structurels récurrents. Décisions d'architecture et leur justification.

### 1.1 Pattern : Static Site avec SPA optionnelle

```
site/
├── index.html              ← page d'accueil (HTML statique enrichi par home.js)
├── fiches/
│   ├── fiche.html          ← SPA : charge le doc via ?id=xxx depuis catalog.json
│   ├── index.html          ← liste statique + recherche fulltext
│   └── {uid}.html          ← pages statiques pré-rendues (SEO, crawlers)
├── assets/
│   ├── css/style.css       ← design system
│   ├── css/components.css  ← composants additionnels
│   ├── js/app.js           ← nav, thème, toast, utilitaires globaux
│   ├── js/home.js          ← logique pages publiques
│   └── js/router.js        ← SPA routing
└── data/
    └── catalog.json        ← source de vérité publiée (sous-ensemble du catalog source)
```

**Règle** : `search.js` ne se charge que sur la page catalogue (`fiches/index.html`). Les autres pages ne l'incluent pas (inutile, coût de parse inutile).

**Règle** : `home.js` est chargé en `defer` sur les pages secondaires, sans `defer` sur l'accueil où il est critique.

### 1.2 Pattern : Catalog JSON comme source de vérité

```python
# Structure minimale d'un document dans catalog.json
{
  "id": "8hex",           # identifiant stable
  "title": "...",
  "source": "...",        # source de surveillance
  "lang": "fr|en|pt|es",
  "score_final": 7,       # score éditorial 0-10
  "format": "pdf|html",
  "url": "...",           # URL d'origine
  "archive_url": "...",   # copie pérenne
  "doc_date": "2023",     # année de publication
  "enrichment": {
    "summary": "...",     # synopsis automatique (Claude)
    "en_clair": "...",    # reformulation accessible
    "citations": [
      {"quote": "...", "quote_fr": "...", "page": 12}
    ]
  }
}
```

**Règle** : Le catalog source (`synopsis/catalog.json`) est exhaustif. Le catalog publié (`site/data/catalog.json`) ne contient que les docs publiables (score ≥ seuil, format ouvert, non exclus).

### 1.3 Pattern : Génération statique depuis Python

```python
def _is_publishable(doc) -> bool:
    """Critère de publication : non exclu + score suffisant + format ouvert."""
    if doc.get("id") in _EXCLUSIONS:
        return False
    return doc.get("format") != "article_html" and _effective_score(doc) >= PUBLISH_THRESHOLD

def _effective_score(doc) -> int:
    """score_final > score_initial > latest_score (ordre de fiabilité décroissant)."""
    return doc.get("score_final") or doc.get("score_initial") or doc.get("latest_score") or 0
```

**Leçon (biblio)** : Ne jamais faire d'import circulaire entre `watch.py` et `corpus_stats.py`. Dupliquer la logique `_is_publishable` localement dans `corpus_stats.py` plutôt que d'importer depuis `watch.py`.

### 1.4 Pattern : Déploiement via GitHub Actions

```bash
# Déclencher un déploiement sans attendre le cron
gh workflow run {WORKFLOW_ID}

# Surveiller
gh run list --limit 3

# Annuler un run concurrent avant de déclencher
gh run cancel {RUN_ID}
```

**Règle** : toujours vérifier `gh run list` avant de déclencher un workflow. Deux runs simultanés sur le même repo peuvent provoquer des conflits de catalog.

**Script de vérification post-deploy** : `python3 scripts/check_deploy.py` compare les MD5 des assets JS/CSS locaux vs. production.

---

## N2 — Audit

> Outils et checklists pour évaluer la qualité d'un site avant publication ou en fin de session.

### 2.1 Checklist de lancement

- [ ] Toutes les pages ont `<link rel="canonical">` absolu
- [ ] `sitemap.xml` généré et à jour, soumis à Google Search Console
- [ ] `robots.txt` en place
- [ ] `404.html` branded (avec nav et lien vers catalogue)
- [ ] `og:image` 1200×630 px sur toutes les pages clés
- [ ] `manifest.json` pour PWA basique
- [ ] Flux RSS fonctionnel (`feed.xml`)
- [ ] Formulaire de contact/newsletter testé

### 2.2 Checklist SEO

- [ ] JSON-LD `ScholarlyArticle` ou `Book` sur chaque fiche (biblio : généré par `_prerender_fiches()`)
- [ ] `lang` correct sur `<html>` (jamais "fr" pour un doc en anglais)
- [ ] `meta name="description"` < 160 caractères, unique par page
- [ ] `search.js` chargé uniquement sur les pages où il est utile
- [ ] `defer` sur les scripts non-critiques
- [ ] Pas de contenu dupliqué entre URL SPA (`?id=xxx`) et URL statique (canonical résout)
- [ ] Fulltext index à jour (vérifier la date `last_build`)

### 2.3 Scripts d'audit disponibles (biblio)

```bash
# Contrôle de cohérence du site publié
python3 scripts/audit_site.py
# → vérifie orphelins, sitemap, lang JSON-LD, licences
# → exit 0 si OK, non-0 avec liste des problèmes

# Vérification post-déploiement
python3 scripts/check_deploy.py
# → compare MD5 assets locaux vs. production

# Reconstruction index fulltext
python3 scripts/fulltext_index.py
# → recharge depuis catalog.json, écrit synopsis/fulltext_index.json
```

### 2.4 Routine de fin de session

Fichier de référence : `routine-fin.md` dans chaque projet.

Étapes invariantes :
1. `git status` — aucune modification non commitée
2. `git log --oneline -5` — vérifier que les commits sont cohérents
3. `python3 scripts/audit_site.py` — si `site/` a été touché
4. `gh run list --limit 3` — workflow deploy en cours ?
5. Mettre à jour `etat-projet-*.md` (point de reprise)
6. Mettre à jour `lecons-*.md` (journal cumulatif)
7. **Mettre à jour ce manuel** si une nouvelle pratique a émergé

---

## N3 — Interface

> Design system partagé. Variables CSS, composants, patterns UX.

### 3.1 Tokens CSS (variables globales)

```css
/* Couleurs */
--accent          : couleur principale (liens, bordures actives, ribbons)
--accent-soft     : version atténuée (fonds, skeletons)
--bg              : fond de page
--bg-elev         : fond de carte / élément surélevé
--bg-card         : fond de carte alternative
--border          : couleur de bordure standard
--text            : texte principal
--text-dim        : texte secondaire
--text-faint      : texte tertiaire (métadonnées, dates)

/* Typographie */
--font-serif      : 'EB Garamond', serif  ← titres, corps éditorial
--font-sans       : system-ui, sans-serif ← UI, métadonnées

/* Formes */
--radius-md       : border-radius standard
--transition      : transition standard (hover, focus)
```

**Règle** : ne jamais coder de couleur en dur dans les composants. Toujours passer par les variables. Le dark mode et les palettes alternatives reposent entièrement sur cette convention.

### 3.2 Navigation — Pattern 4 liens + dropdown

```html
<nav class="site-nav" id="site-nav">
  <a href="catalogue">Catalogue</a>
  <a href="dossiers">Dossiers</a>
  <a href="concepts">Concepts</a>
  <a href="chronologie">Chronologie</a>
  <div class="nav-dropdown" id="nav-apropos">
    <button class="nav-dropdown-btn" aria-expanded="false"
            aria-haspopup="true" aria-controls="nav-apropos-menu">
      À propos
      <svg class="nav-dropdown-caret" viewBox="0 0 10 6" width="10" height="6">
        <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5"
              fill="none" stroke-linecap="round"/>
      </svg>
    </button>
    <ul class="nav-dropdown-menu" id="nav-apropos-menu" role="menu">
      <li><a href="auteurs" role="menuitem">Auteurs</a></li>
      <li><a href="corpus" role="menuitem">Corpus</a></li>
      <li><a href="apropos" role="menuitem">Méthodologie</a></li>
    </ul>
  </div>
</nav>
```

**JS associé** (dans `app.js`, appelé depuis `init()`) :

```javascript
function initNavDropdown() {
  const dropdown = document.getElementById('nav-apropos');
  if (!dropdown) return;
  const toggle = dropdown.querySelector('.nav-dropdown-btn');
  const close = () => { dropdown.removeAttribute('data-open'); toggle.setAttribute('aria-expanded','false'); };
  const open  = () => { dropdown.setAttribute('data-open',''); toggle.setAttribute('aria-expanded','true'); };
  toggle.addEventListener('click', e => { e.stopPropagation(); dropdown.hasAttribute('data-open') ? close() : open(); });
  document.addEventListener('click', e => { if (!dropdown.contains(e.target)) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
}
```

**Règle** : le dropdown se ferme sur Escape, sur clic extérieur, et à la navigation. Les items ont `role="menuitem"`. La navigation clavier (↑↓) est assurée par le CSS `:focus-visible`.

### 3.3 Composants — Fiche documentaire statique

Une fiche statique doit contenir dans cet ordre :
1. Nav + header du site
2. Breadcrumbs (`fil d'Ariane`)
3. Titre en `font-serif`, `clamp(20px, 4vw, 30px)`
4. Métadonnées : source · score/10 · date · éditeur
5. Lien "Document original" (si URL disponible)
6. Section Synopsis (`.fiche-section`)
7. Section En clair (`.fiche-section`)
8. Section Extraits/Citations (`.fiche-citation` × N)
9. Lien vers version interactive (SPA)
10. Footer du site

```css
.fiche-section { margin-bottom: 36px; }
.fiche-section h2 { font-family: var(--font-serif); font-size: 24px; font-weight: 600; }
.fiche-citation {
  margin: 0 0 16px;
  padding: 14px 18px;
  border-left: 3px solid var(--accent);
  background: var(--bg-elev);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  font-family: var(--font-serif);
  font-size: 16px;
  line-height: 1.6;
}
```

### 3.4 Patterns UX

**Toast / notification inline**

```javascript
function toast(msg, duration = 2800) {
  const el = document.createElement('div');
  el.className = 'biblio-toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), duration);
}
```

**Squelettes de chargement (skeleton)**

Classe `.skeleton-card` avec animation shimmer. Afficher pendant `loadCatalog()`, remplacer par le contenu réel dans le `.then()`.

**Stat cards cliquables**

```html
<a class="stat" href="destination.html">
  <span class="stat-n">870</span>
  <span class="stat-label">Documents</span>
</a>
```

```css
a.stat:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 16px var(--accent-soft);
  transform: translateY(-2px);
}
```

### 3.5 Accessibilité — Règles minimales

- Chaque image décorative : `alt=""`
- Chaque image informative : `alt` descriptif
- Boutons sans texte : `aria-label` obligatoire
- Sections avec titre : `aria-labelledby="id-du-titre"`
- Zones de contenu dynamique : `aria-live="polite"`
- Navigation principale : `role="banner"`, `role="contentinfo"`, `role="main"` sur `<main id="main">`
- Skip link (`<a class="skip-link" href="#main">Aller au contenu</a>`) en premier élément du body

---

## N4 — Fonctions

> Snippets de code réutilisables, documentés et testés en production.

### 4.1 Python — Échappement HTML dans les f-strings

```python
def esc(s: str) -> str:
    """Échappe les caractères HTML spéciaux pour insertion sûre."""
    return (str(s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def paras(text: str, esc_fn) -> str:
    """Convertit un texte (double saut = paragraphe) en balises <p>."""
    parts = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    return "\n".join(f"<p>{esc_fn(p)}</p>" for p in parts) or f"<p>{esc_fn(str(text))}</p>"
```

**Piège** : les sections HTML pré-calculées (comme `summary_html`) insérées via `{var}` dans une f-string ne sont PAS ré-interprétées. Les `{` et `}` du contenu de la variable sont sûrs. Pas besoin de les doubler.

### 4.2 Python — Détection de publiabilité

```python
PUBLISH_THRESHOLD = 4  # configurable

def _effective_score(doc: dict) -> int:
    return doc.get("score_final") or doc.get("score_initial") or doc.get("latest_score") or 0

def _is_publishable(doc: dict, exclusions: set) -> bool:
    return (
        doc.get("id") not in exclusions
        and doc.get("format") != "article_html"
        and _effective_score(doc) >= PUBLISH_THRESHOLD
    )
```

### 4.3 Python — Pipeline enrichissement avec reprise sur token limit

```python
# Pattern : exit code 2 = token limit (pipeline doit dormir et reprendre)
import sys, time, subprocess

MAX_SLEEP = 6 * 3600  # 6h max
SLEEP_CHUNK = 300     # vérifier toutes les 5 min

def run_with_resume(cmd: list[str]) -> int:
    """Lance cmd, retourne exit code. Si exit 2, dort et relance."""
    while True:
        result = subprocess.run(cmd)
        if result.returncode != 2:
            return result.returncode
        # Token limit : attendre le reset
        slept = 0
        while slept < MAX_SLEEP:
            time.sleep(SLEEP_CHUNK)
            slept += SLEEP_CHUNK
            # Vérifier si l'heure de reset est passée (20h Paris)
            # ...
```

### 4.4 Python — Merge de catalog après conflit git

```python
import json, subprocess

def merge_catalogs(local_path, remote_ref="origin/main"):
    """Fusionne deux versions de catalog.json : base = remote, patches = local."""
    remote_raw = subprocess.check_output(["git", "show", f"{remote_ref}:synopsis/catalog.json"])
    remote = json.loads(remote_raw)
    local  = json.loads(open(local_path).read())

    merged = remote.copy()
    merged["docs"] = dict(remote["docs"])

    # Appliquer les patches locaux (ex: corrections de champ)
    for uid, local_doc in local["docs"].items():
        if uid in merged["docs"]:
            # Fusionner champ par champ : le remote prime sauf si local a des données nouvelles
            for key in ("lang", "doc_date", "score_final", "enrichment"):
                if local_doc.get(key) and not merged["docs"][uid].get(key):
                    merged["docs"][uid][key] = local_doc[key]

    with open(local_path, "w") as f:
        json.dump(merged, f, ensure_ascii=False, separators=(",", ":"))
    return merged
```

### 4.5 JavaScript — Export BibTeX côté client

```javascript
function bibTexContent(doc, ctx) {
  const key  = doc.id || 'biblio';
  const type = (doc.format === 'pdf' && doc.meta?.page_count >= 60) ? 'book' : 'misc';
  const clean = s => (s || '').replace(/[{}]/g, '');
  let bib = `@${type}{${key},\n`;
  bib += `  title     = {${clean(ctx.title)}},\n`;
  if (ctx.author)  bib += `  author    = {${clean(ctx.author)}},\n`;
  if (ctx.pubYear) bib += `  year      = {${ctx.pubYear}},\n`;
  const ed = clean(doc.editeur || doc.source || '');
  if (ed)          bib += `  publisher = {${ed}},\n`;
  bib += `  url       = {${doc.url || window.location.href}},\n`;
  bib += `  note      = {Consulté via BIBLIO — biblio.actitude.org}\n`;
  bib += `}`;
  return bib;
}

// Téléchargement
function downloadBibTex(doc, ctx) {
  const blob = new Blob([bibTexContent(doc, ctx)], { type: 'text/plain;charset=utf-8' });
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: `biblio-${doc.id || 'doc'}.bib`
  });
  a.click();
  URL.revokeObjectURL(a.href);
}
```

### 4.6 JavaScript — Newsletter avec Buttondown

```javascript
// window.BUTTONDOWN_SLUG doit être défini avant home.js
// Exemple dans index.html : <script>window.BUTTONDOWN_SLUG = 'mon-slug';</script>

async function handleNewsletterSubmit(form) {
  const email = form.querySelector('input[type="email"]').value.trim();
  if (!email) return;
  const slug = window.BUTTONDOWN_SLUG || '';
  if (!slug) {
    // Repli mailto
    window.location.href = `mailto:contact@actitude.org?subject=Newsletter&body=${encodeURIComponent(email)}`;
    return;
  }
  const res = await fetch(`https://buttondown.com/api/emails/embed-subscribe/${slug}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  if (res.ok || res.status === 201) {
    form.innerHTML = '<p>✓ Inscription enregistrée — vérifiez votre boîte mail.</p>';
  }
}
```

### 4.7 JavaScript — Partage de citation avec ancre

```javascript
// Chaque citation reçoit un id="c1", "c2", etc.
// L'URL de partage = page courante + #cN

document.querySelectorAll('.biblio-cite-share').forEach(btn => {
  btn.addEventListener('click', () => {
    const url = btn.dataset.url; // ex: https://biblio.actitude.org/fiches/abc.html#c3
    navigator.clipboard.writeText(url)
      .then(() => toast('Lien copié !'))
      .catch(() => {
        // Fallback pour Firefox/vieux navigateurs
        const ta = document.createElement('textarea');
        ta.value = url;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        toast('Lien copié !');
      });
  });
});
```

### 4.8 Shell — Git : merge propre d'un catalog JSON conflictuel

```bash
# 1. Résoudre le conflit en prenant le remote comme base (plus récent)
git show origin/main:synopsis/catalog.json > /tmp/catalog_remote.json
# 2. Appliquer les patches locaux via script Python (cf. 4.4)
python3 scripts/merge_catalog.py
# 3. Finaliser le merge
git add synopsis/catalog.json
git -c core.editor=true merge --continue
```

---

## N5 — Contenus

> Conventions éditoriales, métadonnées, templates de pages.

### 5.1 Métadonnées obligatoires sur chaque page

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{Titre de la page} — {Nom du site}</title>
<link rel="canonical" href="https://domaine.org/chemin/page.html">
<meta name="description" content="{Description < 160 cars}">
<meta property="og:title" content="{Titre} — {Site}">
<meta property="og:description" content="{Description}">
<meta property="og:image" content="https://domaine.org/assets/img/og-default.png">
<meta property="og:url" content="{URL canonique}">
<meta property="og:type" content="website|article">
<meta property="og:site_name" content="{Nom du site}">
<meta name="twitter:card" content="summary_large_image">
```

**Règle** : `og:image` doit être 1200×630 px minimum. Tester avec [opengraph.xyz](https://www.opengraph.xyz).

### 5.2 JSON-LD — Fiche documentaire

```json
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "headline": "Titre du document",
  "name": "Titre du document",
  "url": "https://biblio.actitude.org/fiches/uid.html",
  "inLanguage": "fr",
  "abstract": "Première phrase du synopsis.",
  "image": "https://biblio.actitude.org/assets/og/uid.png",
  "isPartOf": { "@type": "WebSite", "name": "BIBLIO", "url": "https://biblio.actitude.org/" },
  "publisher": { "@type": "Organization", "name": "actitude.org", "url": "https://actitude.org" },
  "sourceOrganization": { "@type": "Organization", "name": "Nom de la source" },
  "mainEntityOfPage": "URL d'origine du document"
}
```

Utiliser `@type: "Book"` si `page_count >= 60`.

### 5.3 Conventions de nommage

| Élément | Convention |
|---|---|
| UID document | 8 caractères hexadécimaux (MD5 tronqué de l'URL) |
| Fichiers de config | `kebab-case.yml` |
| Fichiers de données | `kebab-case.json` |
| Scripts Python | `snake_case.py` |
| Classes CSS | `kebab-case` avec préfixe `biblio-` pour les composants custom |
| IDs HTML | `kebab-case` |
| Variables JS | `camelCase` |
| Constantes JS | `SCREAMING_SNAKE_CASE` |

### 5.4 Langue des documents

| Valeur `lang` | Usage |
|---|---|
| `fr` | Français |
| `en` | Anglais |
| `pt` | Portugais (MST Brésil) |
| `es` | Espagnol |
| `de` | Allemand |
| `xx` | Indéterminé (jamais laisser vide ou `?`) |

**Règle** : un document en langue inconnue → `lang: xx`, jamais `""` ou `"?"`.  
**Détection** : `langdetect` sur le titre si disponible, sinon détection manuelle.

### 5.5 Biais à documenter systématiquement

Chaque corpus doit avoir une page "Biais et angles morts" documentant :
- Surreprésentation d'une source (> 20% du corpus = biais à signaler)
- Langue dominante et son origine
- Sources inaccessibles (paywalls, offline)
- Géographies absentes
- Faillibilité du scoring automatique

---

## N6 — Pipeline

> Workflows de production, gestion des limites, monitoring.

### 6.1 Workflow de session standard

```
1. Lire INSTRUCTIONS.md + etat-projet.md + lecons.md
2. Vérifier l'état git : git status, git log --oneline -5
3. Travailler (commits atomiques et descriptifs)
4. Avant chaque deploy : audit_site.py
5. Push + trigger workflow
6. Vérifier deploy : check_deploy.py ou gh run list
7. Routine de fin : etat-projet.md + lecons.md + ce manuel
```

### 6.2 Gestion des limites de tokens Claude

```python
# Pattern standard (enrich_loop.py, translate_citations_batch.py)
# Exit code 0 = succès, 1 = erreur, 2 = token limit (resumable)

import sys
def handle_token_limit():
    print("Token limit détecté — exit 2 pour reprise")
    sys.exit(2)

# Dans le script orchestrateur :
MAX_SLEEP = 6 * 3600
CHUNK = 300  # vérifier toutes les 5 min

result = subprocess.run(["python3", "scripts/enrich_one.py", uid])
if result.returncode == 2:
    # Dormir jusqu'au reset (20h Paris par défaut)
    for _ in range(MAX_SLEEP // CHUNK):
        time.sleep(CHUNK)
        if is_past_reset_time():
            break
```

**Règle** : toujours prévoir la reprise sur token limit dans les pipelines longs. Ne jamais recommencer depuis zéro.

### 6.3 Commits — Convention de messages

```
type: description courte en français (< 72 chars)

Types :
  feat:   nouvelle fonctionnalité
  fix:    correction de bug
  chore:  maintenance, mise à jour de données
  docs:   documentation uniquement
  style:  CSS/formatting sans changement de logique
  refac:  refactoring sans changement de comportement
  perf:   amélioration de performance

Exemples :
  feat: BibTeX export par fiche (côté client)
  fix: fulltext_index — guard isinstance(cit, dict)
  chore: 915 traductions citations après token reset
  feat: fiches statiques enrichies — suppression meta refresh
```

### 6.4 Résolution de conflits git sur catalog.json

Le catalog JSON est la source de conflits la plus fréquente (CI + local modifient simultanément).

**Stratégie** : toujours prendre le remote comme base (plus récent), et ré-appliquer les modifications locales par-dessus.

```bash
git fetch origin
# Si conflit après merge :
git show origin/main:synopsis/catalog.json > /tmp/remote.json
python3 scripts/merge_catalog.py  # script dédié qui applique les patches locaux
git add synopsis/catalog.json
git -c core.editor=true merge --continue
```

**Prévention** : vérifier `gh run list` avant tout commit touchant le catalog.

---

## Projets

> Chaque projet documente ses spécificités ici. Ce qui est générique remonte dans les niveaux N0-N6.

### biblio.actitude.org

**Démarré** : 2025  
**Stack** : Python (watch.py, enrich_loop.py) + HTML/CSS/JS statique + GitHub Actions  
**Repo** : `CedricMabilotte/veille-documentaire`  
**URL** : https://biblio.actitude.org  
**GitHub Pages** : repo `biblio-actitude-org`  
**Workflow deploy** : ID `277288346` ("Veille documentaire")

**Spécificités** :
- Pipeline en 3 phases : summary → en_clair → traduction citations
- Seuil de publication : `PUBLISH_THRESHOLD = 4` (en discussion pour passer à 5)
- 870 fiches statiques, ~931 publiables
- Sources : 30+ dont La Vía Campesina (dominant), Infokiosques, MST Brésil, Anarchist Library, GRAIN, TNI, FIAN (nouveaux)
- Index fulltext inversé : `synopsis/fulltext_index.json` — reconstruire si daté de + 2 semaines
- Garde-fou : `python3 scripts/audit_site.py` à lancer après chaque touche à `site/`

**Décisions en attente** :
- Relever PUBLISH_THRESHOLD à 5 ? (40 fiches retirées)
- Compte Buttondown pour la newsletter ? (slug à définir dans index.html)
- Portal OACA : vérifier après 2026-09-30

**Outils Cowork spécifiques** :
- Pas de widget visuel inline (plante l'interface)
- Pas d'outil de questions à choix multiple (plante l'interface)
- Livrer les visuels en fichier HTML autonome

---

### actitude.org

*(À compléter lors de la prochaine session sur ce projet)*

---

## Changelog

| Date | Auteur | Modification |
|---|---|---|
| 2026-07-02 | Claude (session biblio #16) | Initialisation du manuel — structure 7 niveaux, pré-rempli avec biblio |

---

## Comment contribuer à ce manuel

### En cours de session
Quand une solution non-triviale est trouvée, l'ajouter immédiatement dans la section appropriée avec un commentaire `# Source : projet X`.

### En fin de session
Parcourir `lecons-*.md` du projet. Pour chaque leçon marquée `[transverse]`, la faire remonter dans ce manuel.

### Critère de remontée
Une pratique mérite d'être dans ce manuel si elle répond à **au moins deux** de ces critères :
- Elle a évité ou résolu un bug en production
- Elle peut s'appliquer à un autre projet que celui où elle a émergé
- Elle n'est pas documentée ailleurs (pas dans la doc officielle d'un outil)
- Sa découverte a pris > 30 minutes

### Ce qui ne doit PAS être dans ce manuel
- Les décisions propres à un projet (→ `etat-projet.md` du projet)
- Les solutions temporaires ou des hacks non généralisables
- La documentation des outils tiers (→ liens vers leur doc officielle)
- Les logs de session (→ `lecons-*.md` du projet)
