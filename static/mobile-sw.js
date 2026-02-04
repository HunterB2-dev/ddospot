// DDoSPot Mobile Service Worker
// Handles caching, offline support, and background sync

const CACHE_NAME = 'ddospot-mobile-v2';
const STATIC_ASSETS = [
    '/mobile',
    '/static/mobile-dashboard.css',
    '/static/mobile-dashboard.js',
    '/manifest.json',
    '/static/logo-192.png',
    '/static/logo-512.png',
    '/static/offline.html'
];

const API_CACHE_NAME = 'ddospot-api-v2';
const API_ENDPOINTS = [
    '/api/status/health',
    '/api/stats',
    '/api/top-attackers',
    '/api/protocol-breakdown',
    '/api/threat/summary',
    '/api/threat/high-risk',
    '/api/alerts/history',
    '/api/blacklist'
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS).catch(err => {
                console.warn('[SW] Some static assets failed to cache:', err);
            });
        })
    );
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - Cache with Network Fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Static assets
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Everything else
    event.respondWith(networkFirst(request));
});

// Network first strategy for dynamic content
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        if (response.ok && request.method === 'GET') {
            const cache = await caches.open(API_CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('[SW] Network request failed:', error);
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        return new Response('Offline - Data unavailable', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Cache first strategy for static assets
async function cacheFirst(request) {
    try {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('[SW] Cache first failed:', error);
        return new Response('Offline', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// Check if URL is a static asset
function isStaticAsset(pathname) {
    return pathname.endsWith('.css') ||
           pathname.endsWith('.js') ||
           pathname.endsWith('.png') ||
           pathname.endsWith('.jpg') ||
           pathname.endsWith('.jpeg') ||
           pathname.endsWith('.gif') ||
           pathname.endsWith('.svg') ||
           pathname.endsWith('.webp') ||
           pathname.endsWith('.json') ||
           pathname.startsWith('/static/') ||
           pathname === '/mobile' ||
           pathname === '/manifest.json';
}

// Background sync for alerts
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-alerts') {
        event.waitUntil(syncAlerts());
    }
});

async function syncAlerts() {
    try {
        const response = await fetch('/api/alerts/history');
        if (response.ok) {
            const alerts = await response.json();
            
            // Send notification for critical alerts
            alerts.forEach(alert => {
                if (alert.severity === 'critical') {
                    self.registration.showNotification('Critical Alert', {
                        body: alert.message || 'Critical security alert detected',
                        badge: '/static/badge.png',
                        icon: '/static/logo-192.png',
                        tag: 'critical-alert',
                        requireInteraction: true,
                        actions: [
                            { action: 'view', title: 'View Details' },
                            { action: 'dismiss', title: 'Dismiss' }
                        ]
                    });
                }
            });
        }
    } catch (error) {
        console.log('[SW] Alert sync failed:', error);
    }
}

// Push notifications
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        event.waitUntil(
            self.registration.showNotification(data.title || 'DDoSPot Alert', {
                body: data.message || 'New security alert',
                icon: '/static/logo-192.png',
                badge: '/static/badge.png',
                tag: 'ddospot-alert',
                data: data.url ? { url: data.url } : {}
            })
        );
    }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const urlToOpen = event.notification.data.url || '/mobile';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(
            (clientList) => {
                // Check if app is already open
                for (let i = 0; i < clientList.length; i++) {
                    const client = clientList[i];
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window if app not open
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            }
        )
    );
});

// Message from client
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('[SW] DDoSPot Mobile Service Worker loaded');
