/**
 * Krishi Mitra Service Worker — PWA Application Shell Caching
 * Conforms to Directive M6 & 12_RESILIENCE_AND_OFFLINE.md:
 * 1. Caches application shell (HTML, CSS, JS, manifest, icons, fonts).
 * 2. CRITICAL INVARIANT: NEVER cache authenticated API responses (/api/*) or farmer PII.
 * 3. Never silently queue or upload raw audio in the background.
 * 4. Provides offline fallback to index.html for navigation.
 */

const CACHE_NAME = 'krishi-mitra-shell-v1';
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.svg',
  '/icons/icon-512.svg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(SHELL_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Invariant 1: DO NOT cache API calls, health probes, or authenticated audio
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/health/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Invariant 2: Navigation requests fallback to cached index.html when offline
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('/index.html') || caches.match('/');
      })
    );
    return;
  }

  // Cache-first strategy for static assets (scripts, styles, icons, fonts)
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then((response) => {
        // Cache successful GET static responses
        if (
          response &&
          response.status === 200 &&
          event.request.method === 'GET' &&
          (url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.svg') ||
           url.pathname.endsWith('.woff2') ||
           url.pathname.includes('/assets/'))
        ) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
