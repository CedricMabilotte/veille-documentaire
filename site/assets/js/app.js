/* ===================================================================
   BIBLIO — Application principale (vanilla JS)
   =================================================================== */

(function () {
  'use strict';

  // ----- Utilitaires globaux ------------------------------------------------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  // Échappement HTML (sécurité XSS) — exposé globalement pour les autres modules
  function escape(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
  window.escape = escape;

  // Score → classe CSS de pastille
  function scoreClass(s) {
    const n = Number(s) || 0;
    if (n >= 7) return 's-high';
    if (n >= 4) return 's-mid';
    return 's-low';
  }
  window.scoreClass = scoreClass;

  // Formate une date `2026-05-15_16-10` → `15 mai 2026`
  const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
                'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  function formatDate(s) {
    if (!s) return '';
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
    if (!m) return s;
    const y = m[1], mo = parseInt(m[2], 10) - 1, d = parseInt(m[3], 10);
    return `${d} ${MOIS[mo] || ''} ${y}`;
  }
  window.formatDate = formatDate;

  // Chemin de la couverture (les PNG sont copiées dans assets/covers/<id>.png)
  function coverPath(doc, basePath = '') {
    if (!doc || !doc.id) return null;
    return `${basePath}assets/covers/${doc.id}.png`;
  }
  window.coverPath = coverPath;

  // Titre éditorial : bulle.titre_accroche > doc.title (backfillé) > pdf_title > filename
  // doc.title est le titre soigné renseigné en session #5 (session biblio).
  function docTitle(doc) {
    if (doc.bulle_data && doc.bulle_data.titre_accroche) return doc.bulle_data.titre_accroche;
    if (doc.title) return doc.title;
    if (doc.meta && doc.meta.pdf_title) return doc.meta.pdf_title;
    if (doc.filename) return doc.filename.replace(/\.[a-z0-9]+$/i, '').replace(/[_-]+/g, ' ');
    return doc.id;
  }
  window.docTitle = docTitle;

  // Auteur : doc.author (backfillé) > meta.pdf_author
  function docAuthor(doc) {
    if (doc.author) return doc.author;
    if (doc.meta && doc.meta.pdf_author) return doc.meta.pdf_author;
    return null;
  }
  window.docAuthor = docAuthor;

  function docSummary(doc) {
    if (doc.bulle_data && doc.bulle_data.abstract_editorial) return doc.bulle_data.abstract_editorial;
    if (doc.enrichment && doc.enrichment.summary) return doc.enrichment.summary;
    return '';
  }
  window.docSummary = docSummary;

  function docTeaser(doc) {
    if (doc.bulle_data && doc.bulle_data.teaser) return doc.bulle_data.teaser;
    if (doc.runs && doc.runs.length) return doc.runs[doc.runs.length - 1].raison || '';
    return '';
  }
  window.docTeaser = docTeaser;

  function docLatestRun(doc) {
    if (doc.runs && doc.runs.length) return doc.runs[doc.runs.length - 1];
    return null;
  }
  window.docLatestRun = docLatestRun;

  // ----- Score : règle d'or score_final ?? score_initial ?? latest_score ----
  // Renvoie le score effectif d'un doc, en tenant compte des nouveaux champs
  // backend (score_final, score_initial) avec repli sur l'ancien latest_score.
  function docScore(doc) {
    if (!doc) return 0;
    const run = docLatestRun(doc);
    const candidates = [
      doc.score_final,
      doc.score_initial,
      doc.latest_score,
      run ? run.score : undefined,
    ];
    for (const c of candidates) {
      if (c !== null && c !== undefined && c !== '') {
        const n = Number(c);
        if (!Number.isNaN(n)) return n;
      }
    }
    return 0;
  }
  window.docScore = docScore;

  // Libellé textuel du score : « 7/10 · pertinent » (C5)
  function scoreLabel(s) {
    const n = Number(s) || 0;
    let word;
    if (n >= 9) word = 'incontournable';
    else if (n >= 7) word = 'pertinent';
    else if (n >= 5) word = 'à explorer';
    else if (n >= 3) word = 'marginal';
    else word = 'hors-sujet probable';
    return `${n}/10 · ${word}`;
  }
  window.scoreLabel = scoreLabel;

  // Type documentaire lisible (A1) — repli si doc_type absent
  const DOC_TYPE_LABELS = {
    tract: 'Tract',
    etude: 'Étude académique',
    'étude': 'Étude académique',
    article: 'Article',
    rapport: 'Rapport',
    livre: 'Livre',
    brochure: 'Brochure',
    guide: 'Guide pratique',
    'source_primaire': 'Source primaire',
    primaire: 'Source primaire',
    entretien: 'Entretien',
    revue: 'Revue',
  };
  function docType(doc) {
    if (doc && doc.doc_type) return String(doc.doc_type).toLowerCase();
    return '';
  }
  window.docType = docType;
  function docTypeLabel(t) {
    if (!t) return '';
    return DOC_TYPE_LABELS[String(t).toLowerCase()] || String(t);
  }
  window.docTypeLabel = docTypeLabel;

  // Orientation de la source (B1) — militant / academique / institutionnel
  const ORIENTATION_LABELS = {
    militant: 'Source militante',
    academique: 'Source académique',
    'académique': 'Source académique',
    institutionnel: 'Source institutionnelle',
    presse: 'Source de presse',
    independant: 'Source indépendante',
  };
  function docOrientation(doc) {
    if (doc && doc.orientation) return String(doc.orientation).toLowerCase();
    return '';
  }
  window.docOrientation = docOrientation;
  function orientationLabel(o) {
    if (!o) return '';
    return ORIENTATION_LABELS[String(o).toLowerCase()] || String(o);
  }
  window.orientationLabel = orientationLabel;

  // Date de publication (B11/chronologie) : doc_date prioritaire, puis inférence
  function docDate(doc) {
    if (doc && doc.doc_date) return String(doc.doc_date);
    return '';
  }
  window.docDate = docDate;
  // Année de publication : doc_date prioritaire, puis inferYear
  function docYear(doc) {
    const dd = docDate(doc);
    if (dd) {
      const m = dd.match(/(?:1[5-9]\d{2}|20\d{2})/);
      if (m) return parseInt(m[0], 10);
    }
    return (window.inferYear ? window.inferYear(doc) : null);
  }
  window.docYear = docYear;

  // ----- Rendu réutilisable : statistiques du corpus (A8) -------------------
  // Sait rendre un objet corpus_stats.json dans un conteneur donné.
  // Tolère un objet partiel ; n'affiche que les sections présentes.
  // Exposé pour qu'une page « État du corpus » créée ailleurs puisse l'appeler.
  function renderCorpusStats(stats, container) {
    const el = (typeof container === 'string')
      ? document.querySelector(container) : container;
    if (!el) return;
    if (!stats || typeof stats !== 'object') {
      el.innerHTML = '<p class="biblio-empty-note">Statistiques du corpus indisponibles pour le moment.</p>';
      return;
    }
    const buf = [];
    function barBlock(title, dist, totalHint) {
      if (!dist || typeof dist !== 'object') return '';
      const entries = Object.entries(dist).filter(([, v]) => Number(v) > 0);
      if (!entries.length) return '';
      const total = totalHint || entries.reduce((s, [, v]) => s + Number(v), 0) || 1;
      entries.sort((a, b) => Number(b[1]) - Number(a[1]));
      const rows = entries.map(([k, v]) => {
        const pct = Math.round((Number(v) / total) * 100);
        return `<li class="corpus-bar-row">
          <span class="corpus-bar-label">${escape(k)}</span>
          <span class="corpus-bar-track"><span class="corpus-bar-fill" style="width:${pct}%"></span></span>
          <span class="corpus-bar-val">${Number(v)} · ${pct}%</span>
        </li>`;
      }).join('');
      return `<section class="corpus-stat-block">
        <h3>${escape(title)}</h3>
        <ul class="corpus-bar-list">${rows}</ul>
      </section>`;
    }
    if (typeof stats.total === 'number') {
      buf.push(`<p class="corpus-total"><strong>${stats.total}</strong> documents dans le corpus complet.</p>`);
    }
    buf.push(barBlock('Répartition par langue', stats.by_lang || stats.langues));
    buf.push(barBlock('Répartition par décennie', stats.by_decade || stats.decennies));
    buf.push(barBlock('Répartition par score', stats.by_score || stats.scores));
    buf.push(barBlock('Répartition par type de document', stats.by_doc_type || stats.types));
    buf.push(barBlock('Orientation des sources', stats.by_orientation || stats.orientations));
    if (stats.blind_spots || stats.angles_morts) {
      const txt = stats.blind_spots || stats.angles_morts;
      buf.push(`<section class="corpus-stat-block">
        <h3>Ce que cette veille ne couvre pas</h3>
        <p class="prose">${escape(txt)}</p>
      </section>`);
    }
    const html = buf.filter(Boolean).join('');
    el.innerHTML = html || '<p class="biblio-empty-note">Aucune statistique exploitable dans corpus_stats.json.</p>';
  }
  window.renderCorpusStats = renderCorpusStats;

  // ----- Cartes squelettes (A5) --------------------------------------------
  // Renvoie le HTML de N cartes-fantômes à afficher pendant le fetch.
  function skeletonCards(n = 8) {
    let out = '';
    for (let i = 0; i < n; i++) {
      out += `<div class="skeleton-card" aria-hidden="true">
        <div class="skeleton-cover"></div>
        <div class="skeleton-lines">
          <span class="skeleton-line w90"></span>
          <span class="skeleton-line w60"></span>
          <span class="skeleton-line w30"></span>
        </div>
      </div>`;
    }
    return out;
  }
  window.skeletonCards = skeletonCards;

  // Message d'erreur orienté visiteur (A5) — pas de jargon développeur.
  function visitorError(container, opts) {
    const el = (typeof container === 'string')
      ? document.querySelector(container) : container;
    if (!el) return;
    opts = opts || {};
    const retryAttr = opts.onRetry ? ' data-biblio-retry="1"' : '';
    el.innerHTML = `<div class="biblio-error" role="alert">
      <p class="biblio-error-title">${escape(opts.title || 'Le contenu n’a pas pu se charger')}</p>
      <p class="biblio-error-msg">${escape(opts.message || 'La bibliothèque est momentanément indisponible. Vérifiez votre connexion, puis réessayez.')}</p>
      <p><button type="button" class="btn btn-sm"${retryAttr}>Réessayer</button></p>
    </div>`;
    if (opts.onRetry) {
      const b = el.querySelector('[data-biblio-retry]');
      if (b) b.addEventListener('click', opts.onRetry);
    }
  }
  window.visitorError = visitorError;

  // Surligne les occurrences des termes (B7) dans une chaîne déjà échappée-safe.
  // Renvoie du HTML : on échappe d'abord puis on ré-insère les <mark>.
  function highlightTerms(text, terms) {
    const safe = escape(text || '');
    if (!terms || !terms.length) return safe;
    const norm = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    // Construit une regex tolérante aux accents par approximation : on échappe
    // les termes et on cherche en insensible casse sur le texte échappé.
    const cleaned = terms
      .map(t => String(t).trim())
      .filter(t => t.length >= 2)
      .map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    if (!cleaned.length) return safe;
    try {
      const re = new RegExp('(' + cleaned.join('|') + ')', 'gi');
      return safe.replace(re, '<mark class="biblio-hl">$1</mark>');
    } catch (e) {
      return safe;
    }
  }
  window.highlightTerms = highlightTerms;

  // ----- Chargement catalog -------------------------------------------------
  let _catalogPromise = null;
  function loadCatalog(basePath = '') {
    if (_catalogPromise) return _catalogPromise;
    _catalogPromise = fetch(`${basePath}data/catalog.json`, { cache: 'default' })
      .then(r => {
        if (!r.ok) throw new Error('catalog.json indisponible (' + r.status + ')');
        return r.json();
      })
      .then(data => {
        // Normalise : transforme docs en array trié
        const docsObj = data.docs || {};
        const docs = Object.values(docsObj).map(d => {
          const run = (d.runs && d.runs.length) ? d.runs[d.runs.length - 1] : null;
          return {
            ...d,
            _latestRunDate: run ? run.date : (d.latest_run || ''),
            _latestRaison: run ? run.raison : '',
          };
        });
        return { meta: data.meta || {}, docs };
      })
      .catch(err => {
        console.error('Erreur chargement catalog:', err);
        return { meta: {}, docs: [], _error: err.message };
      });
    return _catalogPromise;
  }
  window.loadCatalog = loadCatalog;

  // Permet de forcer un re-fetch du catalogue (utilisé par les boutons
  // « Réessayer » des messages d'erreur orientés visiteur — A5).
  function resetCatalogCache() { _catalogPromise = null; }
  window.resetCatalogCache = resetCatalogCache;

  // Charge la bulle d'un doc (si disponible) — tente data/bulles/<id>.json
  function loadBulle(docId, basePath = '') {
    return fetch(`${basePath}data/bulles/${docId}.json`, { cache: 'default' })
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }
  window.loadBulle = loadBulle;

  // ----- Helpers d'inférence (auteur, année) --------------------------------
  // Tente d'extraire un nom d'auteur à partir du filename ou link_text si pdf_author manque.
  // Heuristique conservatrice : on cherche un motif "Nom – Titre" ou "Nom_Titre.pdf".
  function inferAuthor(doc) {
    const explicit = (doc.meta && doc.meta.pdf_author) ? String(doc.meta.pdf_author).trim() : '';
    if (explicit && explicit.length > 1 && !/^(unknown|n\/a|inconnu)$/i.test(explicit)) return explicit;
    // tentative : link_text « Auteur — Titre »
    const candidates = [doc.link_text, doc.filename];
    for (const c of candidates) {
      if (!c) continue;
      // pattern : "Nom Prenom - Titre" ou "Nom_Prenom_-_Titre.pdf"
      const cleaned = String(c).replace(/\.[a-z0-9]+$/i, '').replace(/_/g, ' ');
      const m = cleaned.match(/^([A-Z][\p{L}\.\-]+(?:\s+[A-Z][\p{L}\.\-]+){0,3})\s*[—–\-]\s*(.+)$/u);
      if (m && m[1].length < 60) return m[1].trim();
    }
    return null;
  }
  window.inferAuthor = inferAuthor;

  // Tente d'extraire une année (4 chiffres 1500-2099) depuis meta.creationDate, filename, link_text
  function inferYear(doc) {
    const cand = [];
    if (doc.meta && doc.meta.creationDate) cand.push(String(doc.meta.creationDate));
    if (doc.meta && doc.meta.pdf_creation_date) cand.push(String(doc.meta.pdf_creation_date));
    if (doc.filename) cand.push(doc.filename);
    if (doc.link_text) cand.push(doc.link_text);
    if (doc.bulle_data && doc.bulle_data.date) cand.push(String(doc.bulle_data.date));
    for (const s of cand) {
      const m = s.match(/(?:1[5-9]\d{2}|20\d{2})/);
      if (m) return parseInt(m[0], 10);
    }
    return null;
  }
  window.inferYear = inferYear;

  // ----- Recherche avancée multi-critères (B11) -----------------------------
  // Filtre une liste de docs sur la conjonction (ET) de plusieurs critères
  // structurés. Tous les critères sont optionnels ; un critère absent ne
  // filtre pas. Repose sur les champs structurés du catalog (+ fallbacks).
  //   crit = {
  //     author: 'texte',          // sous-chaîne dans l'auteur
  //     yearMin, yearMax,         // période de publication (docYear)
  //     lang: 'fr',               // langue exacte
  //     scoreMin, scoreMax,       // bornes sur docScore (score_final prioritaire)
  //     docType: 'tract',         // type documentaire exact
  //     orientation: 'militant',  // orientation de la source
  //   }
  function advancedFilter(docs, crit) {
    crit = crit || {};
    const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const authorQ = crit.author ? norm(crit.author) : '';
    return (docs || []).filter(d => {
      if (authorQ) {
        const a = norm(docAuthor(d) || (window.inferAuthor ? window.inferAuthor(d) : ''));
        if (a.indexOf(authorQ) === -1) return false;
      }
      if (crit.yearMin != null || crit.yearMax != null) {
        const y = docYear(d);
        if (!y) return false;
        if (crit.yearMin != null && y < crit.yearMin) return false;
        if (crit.yearMax != null && y > crit.yearMax) return false;
      }
      if (crit.lang) {
        const l = (d.lang || (d.meta && d.meta.lang) || '').toLowerCase().slice(0, 2);
        if (l !== String(crit.lang).toLowerCase().slice(0, 2)) return false;
      }
      if (crit.scoreMin != null || crit.scoreMax != null) {
        const s = docScore(d);
        if (crit.scoreMin != null && s < crit.scoreMin) return false;
        if (crit.scoreMax != null && s > crit.scoreMax) return false;
      }
      if (crit.docType) {
        if (docType(d) !== String(crit.docType).toLowerCase()) return false;
      }
      if (crit.orientation) {
        if (docOrientation(d) !== String(crit.orientation).toLowerCase()) return false;
      }
      return true;
    });
  }
  window.advancedFilter = advancedFilter;

  // ----- Theme toggle -------------------------------------------------------
  function initTheme() {
    const stored = localStorage.getItem('biblio-theme');
    const sysDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = stored || (sysDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);

    const btn = $('.theme-toggle');
    if (!btn) return;
    updateThemeBtn(btn, theme);
    btn.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme') || 'light';
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('biblio-theme', next);
      updateThemeBtn(btn, next);
    });
  }
  function updateThemeBtn(btn, theme) {
    const isDark = theme === 'dark';
    btn.setAttribute('aria-label', isDark ? 'Activer le mode clair' : 'Activer le mode sombre');
    btn.innerHTML = isDark
      ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }

  // ----- Sélecteur de palette (Bibliothèque / Académique / Militant) -------
  const PALETTES = [
    { id: 'biblio',     label: 'Bibliothèque', swatch: 'sw-biblio' },
    { id: 'academique', label: 'Académique',   swatch: 'sw-academique' },
    { id: 'militant',   label: 'Militant',     swatch: 'sw-militant' },
  ];
  function applyPalette(palette) {
    if (palette === 'biblio') {
      document.documentElement.removeAttribute('data-palette');
    } else {
      document.documentElement.setAttribute('data-palette', palette);
    }
  }
  function initPalette(basePath) {
    // Les palettes (académique, militant) sont définies directement dans
    // style.css via les sélecteurs [data-palette="…"] : aucun chargement
    // dynamique de feuille de style, donc aucune dépendance au chemin ni au
    // cache du service worker.
    const stored = localStorage.getItem('biblio-palette') || 'biblio';
    applyPalette(stored);

    const btn = $('.palette-toggle');
    if (!btn) return;
    // Construit le menu
    const menu = document.createElement('div');
    menu.className = 'palette-menu';
    menu.setAttribute('role', 'menu');
    menu.innerHTML = PALETTES.map(p => `
      <button type="button" role="menuitem" data-palette="${p.id}" class="${p.id === stored ? 'active' : ''}">
        <span class="palette-swatch ${p.swatch}" aria-hidden="true"></span>
        <span>${p.label}</span>
      </button>
    `).join('');
    btn.appendChild(menu);
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (e.target.closest('.palette-menu button')) {
        const b = e.target.closest('button[data-palette]');
        const p = b.getAttribute('data-palette');
        localStorage.setItem('biblio-palette', p);
        applyPalette(p);
        menu.querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
        menu.classList.remove('open');
        return;
      }
      menu.classList.toggle('open');
    });
    document.addEventListener('click', (e) => {
      if (!btn.contains(e.target)) menu.classList.remove('open');
    });
    // Touche Échap ferme le menu
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') menu.classList.remove('open');
    });
  }

  // ----- Menu mobile --------------------------------------------------------
  function initMenu() {
    const btn = $('.menu-toggle');
    const nav = $('.site-nav');
    if (!btn || !nav) return;
    btn.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // ----- Dropdown "À propos" ------------------------------------------------
  function initNavDropdown() {
    const dropdown = $('#nav-apropos');
    if (!dropdown) return;
    const toggle = dropdown.querySelector('.nav-dropdown-btn');
    const closeDropdown = () => {
      dropdown.removeAttribute('data-open');
      toggle.setAttribute('aria-expanded', 'false');
    };
    const openDropdown = () => {
      dropdown.setAttribute('data-open', '');
      toggle.setAttribute('aria-expanded', 'true');
    };
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.hasAttribute('data-open') ? closeDropdown() : openDropdown();
    });
    // Fermer sur clic extérieur
    document.addEventListener('click', (e) => {
      if (!dropdown.contains(e.target)) closeDropdown();
    });
    // Fermer sur Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeDropdown();
    });
    // Navigation clavier dans le menu
    const items = Array.from(dropdown.querySelectorAll('.nav-dropdown-menu a'));
    toggle.addEventListener('keydown', (e) => {
      if ((e.key === 'ArrowDown' || e.key === 'Enter') && !dropdown.hasAttribute('data-open')) {
        e.preventDefault(); openDropdown(); items[0] && items[0].focus();
      }
    });
    items.forEach((item, i) => {
      item.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') { e.preventDefault(); items[i + 1] && items[i + 1].focus(); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); i === 0 ? toggle.focus() : items[i - 1].focus(); }
        if (e.key === 'Escape')    { closeDropdown(); toggle.focus(); }
      });
    });
  }

  // ----- Recherche header (redirige vers /fiches/?q=...) --------------------
  function initHeaderSearch(basePath = '') {
    const input = $('#header-search');
    if (!input) return;
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = input.value.trim();
        if (q.length === 0) return;
        const target = window.location.pathname.endsWith('/fiches/index.html') ||
                       window.location.pathname.endsWith('/fiches/')
          ? '?q=' + encodeURIComponent(q)
          : `${basePath}fiches/index.html?q=${encodeURIComponent(q)}`;
        window.location.href = target;
      }
    });
  }

  // ----- Raccourcis clavier globaux ----------------------------------------
  function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // '/' focus la recherche (sauf si on est déjà dans un input)
      const inField = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
      if (e.key === '/' && !inField) {
        e.preventDefault();
        const s = $('#header-search') || $('.search-box input');
        if (s) s.focus();
      }
      // Esc dégage la nav mobile
      if (e.key === 'Escape') {
        const nav = $('.site-nav.open');
        if (nav) nav.classList.remove('open');
      }
    });
  }

  // ----- Toast --------------------------------------------------------------
  function toast(msg, ms = 2200) {
    let t = $('.toast');
    if (!t) {
      t = document.createElement('div');
      t.className = 'toast';
      t.setAttribute('role', 'status');
      t.setAttribute('aria-live', 'polite');
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), ms);
  }
  window.toast = toast;

  // ----- Copier presse-papier ----------------------------------------------
  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
    return Promise.resolve();
  }
  window.copyToClipboard = copyToClipboard;

  // ----- Init --------------------------------------------------------------
  function init() {
    // Calcule le basePath pour les pages internes (e.g. /fiches/index.html)
    const path = window.location.pathname;
    // Les pages situées dans un sous-dossier (fiches/, concepts/) doivent
    // remonter d'un cran pour atteindre data/ et assets/.
    const basePath = /\/(fiches|concepts)\//.test(path) ? '../' : '';
    window.BIBLIO_BASE = basePath;

    initTheme();
    initPalette(basePath);
    initMenu();
    initNavDropdown();
    initHeaderSearch(basePath);
    initKeyboardShortcuts();

    // Active link dans la nav
    $$('.site-nav a').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (href && path.endsWith(href.replace(/^\.\.?\//, '/').replace(/^\//, ''))) {
        a.classList.add('active');
      }
    });

    // Hook page-specific init
    if (typeof window.pageInit === 'function') {
      window.pageInit(basePath);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/* ── Lightbox couvertures ─────────────────────────────────────────── */
(function () {
  function openLightbox(src, alt) {
    const overlay = document.createElement('div');
    overlay.className = 'lb-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Couverture agrandie');

    const img = document.createElement('img');
    img.src = src;
    img.alt = alt || '';

    const btn = document.createElement('button');
    btn.className = 'lb-close';
    btn.setAttribute('aria-label', 'Fermer');
    btn.textContent = '×';

    overlay.appendChild(img);
    overlay.appendChild(btn);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    function close() {
      overlay.remove();
      document.body.style.overflow = '';
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e) { if (e.key === 'Escape') close(); }

    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    btn.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
  }

  // Délégation : clic sur la zone de couverture (image OU padding du container)
  // On monte vers le container (.fiche-cover-wrap, .fiche-cover, .book-cover),
  // puis on trouve l'img à l'intérieur — couvre tous les cas de clic.
  document.addEventListener('click', function (e) {
    const wrap = e.target.closest('.fiche-cover-wrap, .fiche-cover, .book-cover');
    if (!wrap || wrap.classList.contains('placeholder')) return;
    const img = wrap.querySelector('img');
    if (!img || img.naturalWidth === 0) return; // image absente ou non chargée
    e.preventDefault();
    openLightbox(img.src, img.alt);
  });
})();
