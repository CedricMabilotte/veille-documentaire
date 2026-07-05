/* ============================================================
 * BIBLIO — Service Worker (PWA)
 * ------------------------------------------------------------
 * Stratégies par type de ressource :
 *   - assets statiques (CSS/JS/fonts/images de l'app) → cache-first
 *   - data/*.json (catalog, full-text…)               → network-first, fallback cache
 *   - tout le reste (CDN, API externes…)              → network-only
 *
 * Cache versionné : changer `CACHE_VERSION` invalide tous les caches précédents.
 * ============================================================ */

const CACHE_VERSION = 'biblio-v4';

// Pré-cache minimal : la home et les pages clés (en cas d'offline)
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/une.html',
  '/etat-corpus.html',
  '/apropos.html',
  '/assets/css/style.css',
  '/assets/img/favicon.svg',
  '/assets/img/icon-192.png',
  '/assets/img/icon-512.png',
  '/manifest.json',
];

// Extensions considérées comme "asset statique" (cacheable agressivement)
const STATIC_EXTS = /\.(?:css|js|woff2?|ttf|svg|png|jpg|jpeg|webp|ico|gif)$/i;

// ── Install : pré-cache la liste minimale ────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      // addAll échoue en bloc si une URL 404 → on les ajoute une par une
      return Promise.all(
        PRECACHE_URLS.map((u) =>
          cache.add(u).catch(() => { /* ignore individual failure */ })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// ── Activate : purge les anciens caches ──────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Helpers ──────────────────────────────────────────────────────────────────
function isSameOrigin(url) {
  return url.origin === self.location.origin;
}

function isDataJson(url) {
  // Catalog, full-text index, bulles : tout ce qui vit sous /data/*.json
  return url.pathname.includes('/data/') && url.pathname.endsWith('.json');
}

function isStaticAsset(url) {
  return STATIC_EXTS.test(url.pathname);
}

// Cache-first : sert depuis le cache, fallback réseau, puis met en cache
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    return cached || Response.error();
  }
}

// Network-first : tente le réseau, fallback cache si offline
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    return cached || Response.error();
  }
}

// ── Fetch handler : aiguillage selon la stratégie ────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // On ne gère que GET (POST/PUT/etc. → laisser passer)
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Stratégie "network-only" pour tout ce qui est cross-origin
  if (!isSameOrigin(url)) {
    return;  // pas d'intercept → fetch direct par le navigateur
  }

  if (isDataJson(url)) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // HTML / autres routes same-origin → network-first (pour récup MAJ rapide)
  event.respondWith(networkFirst(request));
});
