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

  // Titre éditorial : préfère bulle.titre_accroche > pdf_title > filename
  function docTitle(doc) {
    if (doc.bulle_data && doc.bulle_data.titre_accroche) return doc.bulle_data.titre_accroche;
    if (doc.meta && doc.meta.pdf_title) return doc.meta.pdf_title;
    if (doc.filename) return doc.filename.replace(/\.[a-z0-9]+$/i, '').replace(/[_-]+/g, ' ');
    return doc.id;
  }
  window.docTitle = docTitle;

  // Auteur (depuis meta PDF)
  function docAuthor(doc) {
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

  // Charge la bulle d'un doc (si disponible) — tente data/bulles/<id>.json
  function loadBulle(docId, basePath = '') {
    return fetch(`${basePath}data/bulles/${docId}.json`, { cache: 'default' })
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }
  window.loadBulle = loadBulle;

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
    const basePath = /\/fiches\//.test(path) ? '../' : '';
    window.BIBLIO_BASE = basePath;

    initTheme();
    initMenu();
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
