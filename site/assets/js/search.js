/* ===================================================================
   BIBLIO — Moteur de recherche full-text simple
   =================================================================== */

(function () {
  'use strict';

  // Normalise : minuscules + suppression diacritiques pour matching tolérant
  function normalize(s) {
    return (s || '')
      .toString()
      .toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  // Construit le "texte recherchable" agrégé d'un doc
  function buildSearchBlob(doc) {
    const parts = [];
    parts.push(doc.id || '');
    parts.push(doc.filename || '');
    parts.push(doc.source || '');
    if (doc.meta) {
      parts.push(doc.meta.pdf_title || '');
      parts.push(doc.meta.pdf_author || '');
    }
    if (doc.enrichment) {
      parts.push(doc.enrichment.summary || '');
      parts.push((doc.enrichment.matched_keywords || []).join(' '));
      (doc.enrichment.citations || []).forEach(c => {
        parts.push(c.quote || '');
        parts.push(c.why_relevant || '');
      });
    }
    if (doc.bulle_data) {
      parts.push(doc.bulle_data.titre_accroche || '');
      parts.push(doc.bulle_data.teaser || '');
      parts.push(doc.bulle_data.abstract_editorial || '');
      parts.push((doc.bulle_data.categorisation || []).join(' '));
      (doc.bulle_data.citations_phares || []).forEach(c => {
        parts.push(c.quote || '');
      });
    }
    (doc.runs || []).forEach(r => {
      parts.push(r.raison || '');
    });
    return normalize(parts.join(' || '));
  }

  // Filtre les docs selon une requête (chaîne avec mots multiples)
  function searchDocs(docs, query) {
    if (!query || !query.trim()) return docs;
    const terms = normalize(query).split(/\s+/).filter(Boolean);
    return docs.filter(d => {
      if (!d._blob) d._blob = buildSearchBlob(d);
      return terms.every(t => d._blob.indexOf(t) !== -1);
    });
  }

  // ----- Auto-suggest -------------------------------------------------------
  // Construit (et cache) la liste des « termes suggérables » du corpus :
  //   - matched_keywords des enrichments
  //   - auteurs
  //   - sources
  //   - catégorisations des bulles
  // Retourne un Array<{term, source}> avec term normalisé attaché en _norm.
  let _suggestionsCache = null;
  function buildSuggestions(docs) {
    if (_suggestionsCache) return _suggestionsCache;
    const seen = new Map(); // term canonique -> {term, source}
    function add(term, source) {
      if (!term) return;
      const t = String(term).trim();
      if (t.length < 2 || t.length > 80) return;
      const norm = normalize(t);
      if (!norm) return;
      if (seen.has(norm)) return;
      seen.set(norm, { term: t, source, _norm: norm });
    }
    for (const d of docs || []) {
      // Mots-clés enrichment
      ((d.enrichment && d.enrichment.matched_keywords) || []).forEach(k => add(k, 'mot-clé'));
      // Auteur (explicite ou inféré côté window.inferAuthor)
      const a = (d.meta && d.meta.pdf_author) || (window.inferAuthor ? window.inferAuthor(d) : null);
      if (a) add(a, 'auteur');
      // Source
      if (d.source) add(d.source, 'source');
      // Categorisations bulles (chargées si dispo)
      if (d.bulle_data && Array.isArray(d.bulle_data.categorisation)) {
        d.bulle_data.categorisation.forEach(c => add(c, 'thème'));
      }
    }
    _suggestionsCache = Array.from(seen.values());
    return _suggestionsCache;
  }

  // Cherche les meilleures suggestions pour un préfixe (top N, par défaut 10).
  // Stratégie : (1) prefix match, (2) substring match — toléra accents/casse.
  function suggest(docs, prefix, limit = 10) {
    if (!prefix || prefix.trim().length < 2) return [];
    const pool = buildSuggestions(docs);
    const q = normalize(prefix);
    const starts = [];
    const contains = [];
    for (const s of pool) {
      const idx = s._norm.indexOf(q);
      if (idx === 0) starts.push(s);
      else if (idx > 0) contains.push(s);
      if (starts.length >= limit) break;
    }
    return starts.concat(contains).slice(0, limit);
  }

  // Permet aux pages d'invalider la cache (ex. après chargement de bulles)
  function resetSuggestionsCache() { _suggestionsCache = null; }

  window.BiblioSearch = {
    normalize,
    buildSearchBlob,
    searchDocs,
    buildSuggestions,
    suggest,
    resetSuggestionsCache,
  };
})();
