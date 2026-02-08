# Mobile Dashboard & Progressive Web App

**File 20: Mobile Monitoring and PWA Features**

*Level: Intermediate | Time: 1-2 hours | Prerequisites: Files 4, 9*

---

## Table of Contents
1. [Introduction](#introduction)
2. [PWA Features](#pwa-features)
3. [Offline Capabilities](#offline)
4. [Mobile Optimization](#mobile)
5. [Push Notifications](#push-notifications)
6. [Installation](#installation)
7. [Mobile-Specific Features](#mobile-features)
8. [Performance](#performance)

---

## Introduction {#introduction}

DDoSPoT includes a Progressive Web App (PWA) for mobile monitoring:

- **Install on Mobile**: Add to home screen on iOS/Android
- **Offline Access**: View cached data when offline
- **Push Notifications**: Instant alerts on threat detection
- **Fast Performance**: Optimized for mobile networks
- **Responsive Design**: Works on any screen size

---

## PWA Features {#pwa-features}

### Web App Manifest

**File**: `/static/manifest.json`

```json
{
  "name": "DDoSPoT Threat Monitor",
  "short_name": "DDoSPoT",
  "description": "Real-time DDoS and threat detection monitoring",
  "start_url": "/dashboard",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "background_color": "#ffffff",
  "theme_color": "#1e40af",
  "icons": [
    {
      "src": "/static/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/maskable-icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "categories": ["security", "productivity"],
  "screenshots": [
    {
      "src": "/static/screenshots/dashboard-320x568.png",
      "sizes": "320x568",
      "form_factor": "narrow"
    },
    {
      "src": "/static/screenshots/dashboard-1920x1080.png",
      "sizes": "1920x1080",
      "form_factor": "wide"
    }
  ],
  "shortcuts": [
    {
      "name": "View Threats",
      "short_name": "Threats",
      "description": "View recent threats and attacks",
      "url": "/dashboard/threats",
      "icons": [
        {
          "src": "/static/icons/threats-192x192.png",
          "sizes": "192x192"
        }
      ]
    },
    {
      "name": "System Status",
      "short_name": "Status",
      "description": "Check system health and status",
      "url": "/dashboard/status",
      "icons": [
        {
          "src": "/static/icons/status-192x192.png",
          "sizes": "192x192"
        }
      ]
    }
  ]
}
```

### Service Worker

**File**: `/static/service-worker.js`

```javascript
const CACHE_NAME = 'ddospot-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/dashboard',
  '/static/css/style.css',
  '/static/js/app.js',
  '/api/health',
  '/static/manifest.json'
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Caching assets');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fall back to network
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests
  if (!event.request.url.includes(self.location.origin)) {
    return;
  }

  if (event.request.method !== 'GET') {
    return;
  }

  // Network first for API calls
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            // Cache the response
            const cache_response = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, cache_response);
            });
          }
          return response;
        })
        .catch(() => {
          // Fall back to cache
          return caches.match(event.request);
        })
    );
    return;
  }

  // Cache first for static assets
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }
      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200) {
          return response;
        }
        const cache_response = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, cache_response);
        });
        return response;
      });
    })
  );
});

// Handle push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const options = {
    body: event.data.text(),
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    tag: 'ddospot-alert',
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification('DDoSPoT Alert', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // Focus existing window if open
      for (let client of clientList) {
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window if not open
      if (clients.openWindow) {
        return clients.openWindow('/dashboard/threats');
      }
    })
  );
});
```

---

## Offline Capabilities {#offline}

### Offline Data Sync

```javascript
// File: /static/js/offline-sync.js

class OfflineManager {
  constructor() {
    this.queue = [];
    this.isOnline = navigator.onLine;
    
    // Listen for online/offline events
    window.addEventListener('online', () => this.goOnline());
    window.addEventListener('offline', () => this.goOffline());
  }

  goOffline() {
    console.log('Going offline');
    this.isOnline = false;
    this.showOfflineIndicator();
  }

  goOnline() {
    console.log('Back online');
    this.isOnline = true;
    this.hideOfflineIndicator();
    this.syncQueue();
  }

  // Queue API requests while offline
  queueRequest(method, url, data) {
    this.queue.push({ method, url, data, timestamp: Date.now() });
    this.saveQueueToStorage();
  }

  // Sync queued requests when back online
  async syncQueue() {
    if (this.queue.length === 0) return;

    console.log(`Syncing ${this.queue.length} queued requests...`);

    for (const request of this.queue) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request.data)
        });

        if (response.ok) {
          // Remove from queue
          this.queue = this.queue.filter(r => r !== request);
        }
      } catch (error) {
        console.error('Sync failed:', error);
        break; // Stop syncing if network error
      }
    }

    this.saveQueueToStorage();
    console.log(`Sync complete. ${this.queue.length} requests remaining`);
  }

  saveQueueToStorage() {
    localStorage.setItem('ddospot_queue', JSON.stringify(this.queue));
  }

  loadQueueFromStorage() {
    const stored = localStorage.getItem('ddospot_queue');
    this.queue = stored ? JSON.parse(stored) : [];
  }

  showOfflineIndicator() {
    const banner = document.createElement('div');
    banner.id = 'offline-banner';
    banner.textContent = '⚠️ You are offline. Some features are limited.';
    banner.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      background: #f59e0b;
      color: white;
      padding: 12px;
      text-align: center;
      z-index: 9999;
    `;
    document.body.prepend(banner);
  }

  hideOfflineIndicator() {
    const banner = document.getElementById('offline-banner');
    if (banner) banner.remove();
  }
}

// Initialize
const offlineManager = new OfflineManager();
```

### Cached Data for Offline Viewing

```javascript
// Cache threat data for offline access
async function cacheThreats() {
  try {
    const response = await fetch('/api/threats?limit=100');
    const threats = await response.json();
    
    localStorage.setItem('cached_threats', JSON.stringify({
      data: threats,
      timestamp: Date.now()
    }));
  } catch (error) {
    console.error('Failed to cache threats:', error);
  }
}

// Get threat data (cache or network)
async function getThreats() {
  if (navigator.onLine) {
    await cacheThreats();
    return fetch('/api/threats').then(r => r.json());
  } else {
    // Offline - use cached data
    const cached = localStorage.getItem('cached_threats');
    if (cached) {
      const parsed = JSON.parse(cached);
      // Show age of cached data
      const age = Math.round((Date.now() - parsed.timestamp) / 60000);
      console.log(`Using cached data (${age} minutes old)`);
      return parsed.data;
    }
    return [];
  }
}
```

---

## Mobile Optimization {#mobile}

### Responsive Layout

**File**: `/static/css/mobile.css`

```css
/* Mobile-first design */
@media (max-width: 640px) {
  /* Hide desktop elements */
  .sidebar {
    display: none;
  }

  /* Full-width layout */
  .container {
    padding: 0;
    margin: 0;
  }

  /* Stack cards vertically */
  .card-grid {
    display: grid;
    grid-template-columns: 1fr;
  }

  /* Large touch targets */
  button, input, select {
    min-height: 44px;
    min-width: 44px;
  }

  /* Larger text for readability */
  body {
    font-size: 16px; /* Prevents zoom on input focus */
  }

  /* Hide non-essential info */
  .secondary-info {
    display: none;
  }

  /* Full-width modals */
  .modal {
    width: 100%;
    height: 100%;
  }
}

/* Tablet layout (641px - 1024px) */
@media (min-width: 641px) and (max-width: 1024px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .sidebar {
    width: 60px; /* Collapsed sidebar */
  }
}

/* Desktop layout (1025px+) */
@media (min-width: 1025px) {
  .card-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .sidebar {
    width: 250px;
  }
}

/* Touch-friendly spacing */
.touch-target {
  padding: 12px;
  min-height: 48px;
}

/* Prevent zoom on input focus */
input, select, textarea {
  font-size: 16px;
}
```

---

## Push Notifications {#push-notifications}

### Enable Push Notifications

```javascript
// File: /static/js/notifications.js

class NotificationManager {
  async requestPermission() {
    if (!('Notification' in window)) {
      console.log('Browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }

    return false;
  }

  async subscribeToPushNotifications() {
    try {
      const registration = await navigator.serviceWorker.ready;

      // Check if already subscribed
      const existingSubscription = await registration.pushManager.getSubscription();
      if (existingSubscription) {
        return existingSubscription;
      }

      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          'YOUR_VAPID_PUBLIC_KEY'
        )
      });

      // Send subscription to server
      await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription)
      });

      return subscription;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
    }
  }

  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Show local notification
  showNotification(title, options) {
    if (Notification.permission === 'granted') {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then((registration) => {
          registration.showNotification(title, {
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/badge-72x72.png',
            ...options
          });
        });
      }
    }
  }
}

// Initialize
const notificationManager = new NotificationManager();

// Request permission on first visit
window.addEventListener('load', async () => {
  const hasPermission = await notificationManager.requestPermission();
  if (hasPermission) {
    await notificationManager.subscribeToPushNotifications();
    console.log('Push notifications enabled');
  }
});
```

---

## Installation {#installation}

### Add to Home Screen

**iPhone (iOS 16.4+):**
1. Open Safari
2. Visit DDoSPoT dashboard
3. Tap Share button (↑)
4. Select "Add to Home Screen"
5. Name and confirm

**Android:**
1. Open Chrome
2. Visit DDoSPoT dashboard
3. Tap menu (⋮)
4. Select "Install app"
5. Confirm installation

**Desktop (Chrome/Edge):**
1. Visit DDoSPoT dashboard
2. Click install icon (⊕) in address bar
3. Confirm installation

---

## Mobile-Specific Features {#mobile-features}

### Touch Gestures

```javascript
// Swipe to refresh
let touchStartX = 0;
document.addEventListener('touchstart', (e) => {
  touchStartX = e.touches[0].clientX;
});

document.addEventListener('touchend', (e) => {
  const touchEndX = e.changedTouches[0].clientX;
  if (touchEndX - touchStartX > 100) { // Swiped right
    location.reload();
  }
});

// Double-tap to zoom (can disable if needed)
document.addEventListener('dblclick', (e) => {
  e.preventDefault();
  // Custom zoom behavior
});
```

### Landscape/Portrait Handling

```javascript
// Detect orientation change
window.addEventListener('orientationchange', () => {
  const orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
  document.body.setAttribute('data-orientation', orientation);
  console.log('Orientation changed to:', orientation);
});
```

### Battery Indicator

```javascript
// Reduce update frequency on low battery
const batteryManager = navigator.getBattery ? navigator.getBattery() : null;

if (batteryManager) {
  batteryManager.addEventListener('levelchange', () => {
    if (batteryManager.level < 0.2) {
      console.log('Low battery - reducing update frequency');
      updateInterval = 60000; // 1 minute instead of 10 seconds
    } else {
      updateInterval = 10000; // 10 seconds
    }
  });
}
```

---

## Performance {#performance}

### Performance Metrics

```javascript
// Track performance
class PerformanceMonitor {
  trackMetrics() {
    // First Contentful Paint (FCP)
    const fcpEntries = performance.getEntriesByName('first-contentful-paint');
    if (fcpEntries.length) {
      console.log('FCP:', fcpEntries[0].startTime, 'ms');
    }

    // Largest Contentful Paint (LCP)
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.renderTime || lastEntry.loadTime, 'ms');
    });
    observer.observe({ entryTypes: ['largest-contentful-paint'] });

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          console.log('CLS:', clsValue);
        }
      }
    });
    clsObserver.observe({ entryTypes: ['layout-shift'] });
  }
}

const perfMonitor = new PerformanceMonitor();
perfMonitor.trackMetrics();
```

### Code Splitting

```javascript
// Load threat view only when needed
const ThreatView = () =>
  import('./components/ThreatView.js');

// Lazy load charts on demand
const Charts = () =>
  import('./components/Charts.js').then(m => m.initCharts());
```

---

## Summary

Mobile Dashboard features:

✅ **Progressive Web App** - Install on phone
✅ **Offline Access** - View cached data without internet
✅ **Push Notifications** - Instant threat alerts
✅ **Responsive Design** - Works on all screen sizes
✅ **Touch Optimized** - Large buttons and gestures
✅ **Fast Performance** - Optimized for mobile networks

---

## Next Steps

- Install DDoSPoT mobile app on your phone
- Enable push notifications for alerts
- Test offline functionality
- Configure alert notification preferences

