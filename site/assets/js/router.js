/* ===================================================================
   BIBLIO — Mini-router (query params + lecture URL)
   =================================================================== */

(function () {
  'use strict';

  function getParam(key) {
    const u = new URL(window.location.href);
    return u.searchParams.get(key);
  }

  function setParam(key, value, replace = true) {
    const u = new URL(window.location.href);
    if (value === null || value === undefined || value === '') {
      u.searchParams.delete(key);
    } else {
      u.searchParams.set(key, value);
    }
    if (replace) {
      window.history.replaceState({}, '', u.toString());
    } else {
      window.history.pushState({}, '', u.toString());
    }
  }

  function getAllParams() {
    const u = new URL(window.location.href);
    const out = {};
    u.searchParams.forEach((v, k) => { out[k] = v; });
    return out;
  }

  // Construit une URL absolue (ou relative à basePath) vers une fiche
  function ficheUrl(docId, basePath = '') {
    return `${basePath}fiches/fiche.html?id=${encodeURIComponent(docId)}`;
  }

  window.BiblioRouter = { getParam, setParam, getAllParams, ficheUrl };
})();
