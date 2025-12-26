const CACHE_NAME = 'md-app-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/assets/index-Bf0YVzYc.css',
  '/assets/index-CwgGBtqI.js',
  '/manifest.json',
  '/sw.js', // Also cache the service worker itself
  '/wolf_icon_192.png', // Placeholder for the icon
  '/wolf_icon_512.png', // Placeholder for the icon
  // Add other assets like images, fonts etc. if known
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
