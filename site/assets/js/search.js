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

  window.BiblioSearch = {
    normalize,
    buildSearchBlob,
    searchDocs,
  };
})();
