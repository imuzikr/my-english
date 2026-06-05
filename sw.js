/* My English — Service Worker
 * Strategy:
 *   - HTML pages: Network Only (prevents stale lesson lists in installed/PWA views)
 *   - Static assets (icons, manifest): Cache First
 *   - All other GETs in scope: Stale While Revalidate
 * Scope: /my-english/
 * Bump CACHE version to invalidate old caches on next visit.
 */

const CACHE = 'my-english-20260604';
const SCOPE = '/my-english/';

const CORE_ASSETS = [
  '/my-english/manifest.json',
  '/my-english/icons/icon-192.png',
  '/my-english/icons/icon-512.png',
  '/my-english/icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(CORE_ASSETS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

function isHtmlRequest(request) {
  if (request.mode === 'navigate') return true;
  const accept = request.headers.get('accept') || '';
  return accept.includes('text/html');
}

function isStaticAsset(url) {
  return /\.(png|jpg|jpeg|svg|webp|ico|woff2?|ttf|otf|css)$/i.test(url.pathname)
    || url.pathname.endsWith('/manifest.json');
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (!url.pathname.startsWith(SCOPE)) return;

  if (isHtmlRequest(request)) {
    event.respondWith(networkOnly(request));
    return;
  }
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request));
    return;
  }
  event.respondWith(staleWhileRevalidate(request));
});

async function networkOnly(request) {
  try {
    return await fetch(request, { cache: 'no-store' });
  } catch (err) {
    return new Response(
      '<!doctype html><meta charset="utf-8"><title>Offline</title><body style="font-family:system-ui;padding:2rem"><h1>Offline</h1><p>인터넷 연결을 확인한 뒤 다시 열어 주세요.</p></body>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  const fresh = await fetch(request);
  if (fresh && fresh.status === 200) cache.put(request, fresh.clone());
  return fresh;
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((fresh) => {
      if (fresh && fresh.status === 200) cache.put(request, fresh.clone());
      return fresh;
    })
    .catch(() => cached);
  return cached || fetchPromise;
}
