/**
 * Service Worker for DDoSPoT (Feature #12)
 * Enables offline support, background sync, and PWA capabilities
 */

const CACHE_NAME = 'ddospot-v1';
const RUNTIME_CACHE = 'ddospot-runtime-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/settings',
  '/static/dashboard.css',
  '/static/mobile.css',
  '/static/settings.css',
  '/static/settings.js',
  '/static/dashboard.js',
  '/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // API requests - network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful responses
          if (response && response.status === 200) {
            const cache = caches.open(RUNTIME_CACHE);
            cache.then(c => c.put(request, response.clone()));
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache
          return caches.match(request)
            .then(response => {
              if (response) {
                console.log('[Service Worker] Serving from cache:', url.pathname);
                return response;
              }
              // Return offline response
              return new Response(
                JSON.stringify({
                  offline: true,
                  message: 'You are offline. Some data may be unavailable.',
                  cached_at: new Date().toISOString()
                }),
                {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            });
        })
    );
    return;
  }

  // Static assets - cache first, network fallback
  event.respondWith(
    caches.match(request)
      .then(response => {
        if (response) {
          console.log('[Service Worker] Serving from cache:', url.pathname);
          return response;
        }

        return fetch(request)
          .then(response => {
            // Cache successful responses
            if (response && response.status === 200) {
              const cache = caches.open(RUNTIME_CACHE);
              cache.then(c => c.put(request, response.clone()));
            }
            return response;
          })
          .catch(() => {
            // Return offline page
            return caches.match('/')
              .then(response => {
                return response || new Response(
                  'Offline - Page not in cache',
                  { status: 503 }
                );
              });
          });
      })
  );
});

// Background sync - queue failed requests
self.addEventListener('sync', event => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-alerts') {
    event.waitUntil(
      // Retry any failed alert API calls
      caches.open(RUNTIME_CACHE)
        .then(cache => {
          // Implementation depends on how alerts are stored
          console.log('[Service Worker] Syncing alerts...');
          return Promise.resolve();
        })
    );
  }
});

// Message event - communicate with clients
self.addEventListener('message', event => {
  console.log('[Service Worker] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.delete(RUNTIME_CACHE)
      .then(() => {
        event.ports[0].postMessage({ success: true });
      });
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    const { urls } = event.data;
    caches.open(RUNTIME_CACHE)
      .then(cache => {
        cache.addAll(urls);
        event.ports[0].postMessage({ success: true });
      });
  }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', event => {
  console.log('[Service Worker] Periodic sync:', event.tag);
  
  if (event.tag === 'update-threats') {
    event.waitUntil(
      fetch('/api/threats')
        .then(response => response.json())
        .then(data => {
          // Store latest threat data
          console.log('[Service Worker] Updated threat data');
          return caches.open(RUNTIME_CACHE)
            .then(cache => {
              cache.put('/api/threats', new Response(JSON.stringify(data)));
            });
        })
        .catch(() => {
          console.log('[Service Worker] Failed to sync threats');
        })
    );
  }
});

// Push notifications (if supported)
self.addEventListener('push', event => {
  console.log('[Service Worker] Push notification received');
  
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'New alert from DDoSPoT',
      icon: '/static/logo-192.png',
      badge: '/static/badge-72.png',
      tag: data.tag || 'ddospot-alert',
      requireInteraction: data.severity === 'critical',
      data: {
        url: data.url || '/'
      }
    };

    if (data.threat_level) {
      options.tag = `threat-${data.threat_level}`;
    }

    event.waitUntil(
      self.registration.showNotification(data.title || 'DDoSPoT Alert', options)
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Notification clicked');
  event.notification.close();

  const url = event.notification.data.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then(clientList => {
        // Check if window is already open
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if not found
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Notification close handler
self.addEventListener('notificationclose', event => {
  console.log('[Service Worker] Notification closed');
  // Track notification dismissals if needed
});

console.log('[Service Worker] Loaded successfully');
