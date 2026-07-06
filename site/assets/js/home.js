/* ===================================================================
   BIBLIO — home.js
   Logique de l'accueil refondu (B6, C3, C7) et des nouvelles pages
   (une.html, actu.html, etat-corpus.html, outils.html).
   Vanilla JS. Dépend de app.js (escape, docScore, docTitle, formatDate,
   coverPath, scoreClass, scoreLabel, loadCatalog, loadBulle, renderCorpusStats)
   et de router.js (BiblioRouter).
   =================================================================== */

(function () {
  'use strict';

  /* ---- Helpers communs ------------------------------------------------- */

  // Score effectif : score_final ?? score_initial ?? latest_score. Délègue à
  // docScore (app.js) qui implémente déjà la règle d'or.
  function score(d) {
    return (typeof window.docScore === 'function') ? window.docScore(d) : (d.latest_score || 0);
  }

  // Date de collecte d'un document : collected_date prioritaire, sinon
  // first_seen / _latestRunDate / latest_run (formats "2026-05-15_16-10").
  function collectedDate(d) {
    return d.collected_date || d.first_seen || d._latestRunDate || d.latest_run || '';
  }

  // Parse une date BIBLIO ("2026-05-15_16-10" ou ISO) → objet Date ou null.
  function parseDate(s) {
    if (!s) return null;
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s));
    if (!m) return null;
    const dt = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return isNaN(dt.getTime()) ? null : dt;
  }

  // Nombre de jours entre une date et aujourd'hui (positif = dans le passé).
  function daysAgo(s) {
    const dt = parseDate(s);
    if (!dt) return Infinity;
    return Math.floor((Date.now() - dt.getTime()) / 86400000);
  }

  // Carte « livre » réutilisant le composant existant .book-card.
  function bookCard(doc, basePath) {
    const url = window.BiblioRouter.ficheUrl(doc.id, basePath);
    const cover = window.coverPath(doc, basePath);
    const title = window.docTitle(doc);
    const s = score(doc);
    const author = (window.docAuthor && window.docAuthor(doc)) || doc.source || '';
    const initial = window.escape(title.slice(0, 1).toUpperCase());
    return `
      <a href="${window.escape(url)}" class="book-card fade-in" aria-label="Lire la fiche : ${window.escape(title)}">
        <div class="book-cover" data-initial="${initial}">
          <img src="${window.escape(cover)}" alt="" loading="lazy" onerror="this.parentNode.classList.add('placeholder');this.parentNode.textContent=this.parentNode.dataset.initial||'';">
        </div>
        <div class="book-info">
          <h4 class="book-title">${window.escape(title)}</h4>
          <div class="book-meta">${window.escape(author)}</div>
          <span class="score-pill ${window.scoreClass(s)}" title="${window.escape(window.scoreLabel ? window.scoreLabel(s) : s + '/10')}">${s}/10</span>
        </div>
      </a>`;
  }
  window.bookCard = bookCard;

  // Lien interne JSON tolérant : renvoie {} si fetch échoue (dégradation).
  function loadJSON(path) {
    return fetch(path, { cache: 'default' })
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }
  window.loadJSON = loadJSON;

  /* =====================================================================
     ACCUEIL (index.html) — sections refondues
     ===================================================================== */

  // C7 — Preuve sociale : « N nouveaux documents ce mois-ci ». Le mini-fil
  // texte daté qui suivait a été retiré (session #21) : il répétait exactement
  // les mêmes fiches que la grille imagée juste en dessous (#derniers-ajouts-grid).
  function renderActivite(docs, basePath) {
    const counter = document.getElementById('activite-compte');
    if (!docs || !docs.length || !counter) return;
    const dated = docs
      .map(d => ({ d: d, when: collectedDate(d) }))
      .filter(x => x.when);
    const ceMois = dated.filter(x => daysAgo(x.when) <= 30).length;
    counter.textContent = ceMois > 0
      ? `${ceMois} nouveau${ceMois > 1 ? 'x' : ''} document${ceMois > 1 ? 's' : ''} versé${ceMois > 1 ? 's' : ''} ce mois-ci`
      : 'Veille en cours — le prochain lot arrive bientôt';
  }

  // C3 — « Elles et ils l'ont fait » : docs recit_de_lutte:true.
  function renderRecitsLutte(docs, basePath) {
    const wrap = document.getElementById('recits-lutte-grid');
    const section = document.getElementById('recits-lutte-section');
    if (!wrap) return;
    const recits = docs
      .filter(d => d.recit_de_lutte === true)
      .sort((a, b) => score(b) - score(a))
      .slice(0, 6);
    if (!recits.length) {
      // Dégradation : si le backend n'a pas encore peuplé recit_de_lutte,
      // on masque proprement la section plutôt que d'afficher un vide.
      if (section) section.style.display = 'none';
      return;
    }
    wrap.innerHTML = recits.map(d => bookCard(d, basePath)).join('');
  }

  // Section unifiée « Récemment ajoutés » (fusion B6 : ex-« Voix du Sud » +
  // « Récemment ajoutés » qui faisaient doublon de cartes-livres).
  function renderDerniersAjouts(docs, basePath) {
    const wrap = document.getElementById('derniers-ajouts-grid');
    if (!wrap) return;
    const recent = docs
      .slice()
      .sort((a, b) => String(collectedDate(b)).localeCompare(String(collectedDate(a))))
      .slice(0, 8);
    if (!recent.length) {
      wrap.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:var(--text-faint);font-style:italic;">Aucune fiche pour l\'instant.</p>';
      return;
    }
    wrap.innerHTML = recent.map(d => bookCard(d, basePath)).join('');
  }

  // Bandeau « document de la semaine » sur l'accueil (lit featured.json).
  function renderUneTeaser(basePath) {
    const wrap = document.getElementById('une-teaser');
    if (!wrap) return;
    loadJSON(`${basePath}data/featured.json`).then(data => {
      const f = data && data.featured;
      if (!f) {
        // Dégradation : pas de document de la semaine → masquer la section entière.
        const section = document.getElementById('une-teaser-section');
        if (section) section.style.display = 'none';
        else wrap.style.display = 'none';
        return;
      }
      const id = f.id || f.doc_id;
      const url = id ? window.BiblioRouter.ficheUrl(id, basePath) : `${basePath}une.html`;
      const titre = f.titre_accroche || f.title || f.titre || 'Document de la semaine';
      const teaser = f.teaser || f.chapo || '';
      wrap.querySelector('.une-teaser-titre').textContent = titre;
      wrap.querySelector('.une-teaser-texte').textContent = teaser;
      const link = wrap.querySelector('.une-teaser-link');
      link.setAttribute('href', `${basePath}une.html`);
    });
  }

  function initAccueil(basePath) {
    window.loadCatalog(basePath).then(({ docs, _error }) => {
      if (_error) return; // l'accueil garde son propre message via index.html
      renderActivite(docs, basePath);
      renderRecitsLutte(docs, basePath);
      renderDerniersAjouts(docs, basePath);
    });
    renderUneTeaser(basePath);
  }
  window.initAccueil = initAccueil;

  /* =====================================================================
     PAGE « UNE » (une.html) — document de la semaine
     ===================================================================== */
  function initUne(basePath) {
    const root = document.getElementById('une-root');
    if (!root) return;
    loadJSON(`${basePath}data/featured.json`).then(data => {
      const f = data && data.featured;
      if (!f) {
        root.innerHTML = `
          <div class="une-vide">
            <h1>Pas encore de document de la semaine</h1>
            <p class="prose">La rédaction n'a pas désigné de texte phare pour le moment.
            En attendant, parcourez le catalogue ou les dossiers thématiques.</p>
            <p><a class="btn btn-primary" href="${basePath}fiches/index.html">Explorer le catalogue</a>
               <a class="btn" href="${basePath}dossiers.html">Voir les dossiers</a></p>
          </div>`;
        return;
      }
      const id = f.id || f.doc_id;
      const titre = f.titre_accroche || f.title || f.titre || 'Document de la semaine';
      const teaser = f.teaser || f.chapo || '';
      const abstract = f.abstract_editorial || f.abstract || '';
      const ficheUrl = id ? window.BiblioRouter.ficheUrl(id, basePath) : `${basePath}fiches/index.html`;
      root.innerHTML = `
        <article class="une-article fade-in">
          <span class="une-kicker">Le document de la semaine</span>
          <h1 class="une-titre">${window.escape(titre)}</h1>
          ${teaser ? `<p class="une-teaser-lede">${window.escape(teaser)}</p>` : ''}
          ${abstract ? `<div class="prose une-abstract"><p>${window.escape(abstract)}</p></div>` : ''}
          <p class="mt-3"><a class="btn btn-primary" href="${window.escape(ficheUrl)}">Lire la fiche complète</a></p>
        </article>`;
    });
  }
  window.initUne = initUne;

  /* =====================================================================
     PAGE « ACTU » (actu.html) — ajouts des 7 derniers jours
     ===================================================================== */
  function initActu(basePath) {
    const root = document.getElementById('actu-root');
    if (!root) return;
    window.loadCatalog(basePath).then(({ docs, _error }) => {
      if (_error) {
        window.visitorError(root, {
          title: 'Les nouveautés n\'ont pas pu se charger',
          message: 'La bibliothèque est momentanément indisponible. Réessayez dans un instant.',
          onRetry: () => { window.resetCatalogCache(); initActu(basePath); },
        });
        return;
      }
      const recents = docs
        .filter(d => daysAgo(collectedDate(d)) <= 7)
        .sort((a, b) => String(collectedDate(b)).localeCompare(String(collectedDate(a))));
      if (!recents.length) {
        root.innerHTML = `
          <p class="actu-vide">Aucun document n'a été versé au catalogue ces sept derniers jours.
          La veille tourne en continu — revenez bientôt, ou abonnez-vous aux flux ci-dessous.</p>`;
        return;
      }
      // Regroupe par jour de collecte.
      const byDay = new Map();
      for (const d of recents) {
        const key = String(collectedDate(d)).slice(0, 10);
        if (!byDay.has(key)) byDay.set(key, []);
        byDay.get(key).push(d);
      }
      const buf = [`<p class="actu-compte">${recents.length} document${recents.length > 1 ? 's' : ''} ajouté${recents.length > 1 ? 's' : ''} cette semaine.</p>`];
      for (const [day, list] of byDay) {
        buf.push(`<h2 class="actu-jour">${window.escape(window.formatDate(day) || day)}</h2>`);
        buf.push('<div class="recent-grid">');
        buf.push(list.map(d => bookCard(d, basePath)).join(''));
        buf.push('</div>');
      }
      root.innerHTML = buf.join('');
    });
  }
  window.initActu = initActu;

  /* =====================================================================
     PAGE « ÉTAT DU CORPUS » (etat-corpus.html)
     Charge corpus_stats.json et délègue à window.renderCorpusStats (app.js).
     ===================================================================== */
  function initEtatCorpus(basePath) {
    const root = document.getElementById('corpus-stats-root');
    if (!root) return;
    loadJSON(`${basePath}data/corpus_stats.json`).then(stats => {
      if (!stats) {
        root.innerHTML = '<p class="biblio-empty-note">Les statistiques du corpus ne sont pas encore disponibles. Elles sont générées à chaque passage de la veille.</p>';
        return;
      }
      // Frontend-A expose renderCorpusStats(stats, container).
      if (typeof window.renderCorpusStats === 'function') {
        window.renderCorpusStats(stats, root);
      } else {
        root.innerHTML = '<p class="biblio-empty-note">Module de rendu des statistiques indisponible.</p>';
      }
      // Date de génération, si fournie.
      const meta = document.getElementById('corpus-generated');
      if (meta && stats.generated_at) {
        const dt = stats.generated_at.slice(0, 10);
        meta.textContent = 'Données arrêtées au ' + (window.formatDate(dt) || dt) + '.';
      }
      // Liste complète des sources surveillées (section #sources).
      renderSourcesList(stats.sources_list);
    });
  }
  function renderSourcesList(list) {
    const root = document.getElementById('corpus-sources-root');
    if (!root) return;
    const esc = window.escape || (s => String(s == null ? '' : s));
    if (!Array.isArray(list) || !list.length) {
      root.innerHTML = '<p class="biblio-empty-note">La liste des sources sera disponible au prochain passage de la veille.</p>';
      return;
    }
    const ORIENT = {
      militant: 'militante', academique: 'académique',
      institutionnel: 'institutionnelle', journalistique: 'journalistique',
    };
    const rows = list.map(s => {
      const name = esc(s.label || '');
      const titre = s.url
        ? `<a href="${esc(s.url)}" rel="noopener" target="_blank">${name}</a>`
        : name;
      const orient = ORIENT[s.orientation] || '';
      const n = s.count || 0;
      return `<li class="source-row">
        <span class="source-name">${titre}</span>
        ${orient ? `<span class="source-orient">${orient}</span>` : ''}
        <span class="source-count">${n} doc${n > 1 ? 's' : ''}</span>
      </li>`;
    }).join('');
    root.innerHTML = `<ul class="sources-liste">${rows}</ul>
      <p style="color:var(--text-faint);font-size:13px;margin-top:10px;">${list.length} sources au total.</p>`;
  }
  window.initEtatCorpus = initEtatCorpus;

  /* =====================================================================
     PAGE « OUTILS » (outils.html) — A1
     Filtre le catalog sur doc_type ∈ {guide_pratique, modele_juridique,
     retour_collectif, tract}.
     ===================================================================== */
  const OUTILS_TYPES = {
    guide_pratique: 'Guides pratiques',
    modele_juridique: 'Modèles juridiques',
    retour_collectif: 'Retours de collectifs',
    tract: 'Tracts & brochures',
  };

  function normType(t) {
    return String(t || '').toLowerCase().trim().replace(/[\s-]+/g, '_');
  }

  function initOutils(basePath) {
    const root = document.getElementById('outils-root');
    if (!root) return;
    window.loadCatalog(basePath).then(({ docs, _error }) => {
      if (_error) {
        window.visitorError(root, {
          title: 'La boîte à outils n\'a pas pu se charger',
          message: 'La bibliothèque est momentanément indisponible. Réessayez dans un instant.',
          onRetry: () => { window.resetCatalogCache(); initOutils(basePath); },
        });
        return;
      }
      const wanted = Object.keys(OUTILS_TYPES);
      const outils = docs.filter(d => wanted.indexOf(normType(d.doc_type)) !== -1);
      if (!outils.length) {
        root.innerHTML = `
          <p class="outils-vide">Aucune ressource actionnable n'est encore typée dans le catalogue.
          Les guides pratiques, modèles juridiques, retours de collectifs et tracts apparaîtront ici
          dès que la veille les aura classés. En attendant, le
          <a href="${basePath}fiches/index.html">catalogue complet</a> reste accessible.</p>`;
        return;
      }
      // Regroupe par type.
      const buf = [`<p class="outils-compte">${outils.length} ressource${outils.length > 1 ? 's' : ''} actionnable${outils.length > 1 ? 's' : ''} dans la boîte à outils.</p>`];
      for (const key of wanted) {
        const list = outils
          .filter(d => normType(d.doc_type) === key)
          .sort((a, b) => score(b) - score(a));
        if (!list.length) continue;
        buf.push(`<section class="outils-groupe">
          <h2 class="outils-groupe-titre">${window.escape(OUTILS_TYPES[key])}</h2>
          <div class="recent-grid">${list.map(d => bookCard(d, basePath)).join('')}</div>
        </section>`);
      }
      root.innerHTML = buf.join('');
    });
  }
  window.initOutils = initOutils;

  /* =====================================================================
     Formulaire newsletter — Buttondown si configuré, sinon mailto.
     Pour activer Buttondown : créer un compte sur buttondown.com,
     puis définir window.BUTTONDOWN_SLUG = 'votre-slug' dans index.html
     (avant le chargement de home.js).
     S'applique à tout formulaire portant la classe .newsletter-form.
     ===================================================================== */
  function initNewsletter() {
    const forms = document.querySelectorAll('.newsletter-form');
    forms.forEach(form => {
      form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const input = form.querySelector('input[type="email"]');
        const btn   = form.querySelector('button[type="submit"]');
        const email = input ? input.value.trim() : '';
        if (!email) return;

        const slug = window.BUTTONDOWN_SLUG || '';
        if (slug) {
          // ── Buttondown embed-subscribe ──────────────────────────────────
          if (btn) { btn.disabled = true; btn.textContent = '…'; }
          try {
            const res = await fetch(
              `https://buttondown.com/api/emails/embed-subscribe/${slug}`,
              { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }) }
            );
            if (res.ok || res.status === 201) {
              form.innerHTML = '<p style="color:var(--accent);font-family:var(--font-serif);margin:0;">✓ Inscription enregistrée — vérifiez votre boîte mail.</p>';
            } else {
              const err = await res.text().catch(() => '');
              form.innerHTML = `<p style="color:var(--text-dim);margin:0;">Erreur (${res.status}) — écrivez-nous à <a href="mailto:contact@actitude.org">contact@actitude.org</a>.</p>`;
            }
          } catch (_) {
            if (btn) { btn.disabled = false; btn.textContent = "S'inscrire"; }
          }
        } else {
          // ── Repli mailto ────────────────────────────────────────────────
          const subject = encodeURIComponent('Inscription newsletter biblio');
          const body = encodeURIComponent(
            'Bonjour,\n\nJe souhaite m\'abonner à la lettre de la veille BIBLIO.\n'
            + (email ? 'Adresse : ' + email + '\n' : '')
            + '\nMerci !');
          window.location.href = `mailto:contact@actitude.org?subject=${subject}&body=${body}`;
        }
      });
    });
  }
  window.initNewsletter = initNewsletter;

  /* ---- Bootstrap : appelle l'init de page si présente ------------------ */
  function boot() {
    const basePath = window.BIBLIO_BASE || '';
    initNewsletter();
    if (document.getElementById('une-root')) initUne(basePath);
    if (document.getElementById('actu-root')) initActu(basePath);
    if (document.getElementById('corpus-stats-root')) initEtatCorpus(basePath);
    if (document.getElementById('outils-root')) initOutils(basePath);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
