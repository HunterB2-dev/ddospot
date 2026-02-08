# Feature #12: Mobile Dashboard & PWA - Quick Reference

**Version**: 1.0  
**Status**: Production-Ready  
**Last Updated**: February 2026

---

## 🚀 Quick Start

### 1. Enable PWA (First-Time Setup)

**Files to verify**:
```bash
# Check all PWA files exist
ls -la static/mobile.css
ls -la static/service-worker.js
ls -la static/manifest.json
ls -la templates/mobile-dashboard.html
```

**HTTPS Requirement** (Production):
```bash
# Service Worker requires HTTPS
# Development (localhost) works without HTTPS
```

### 2. Install App on Mobile

**Android**:
1. Open DDoSPoT in Chrome
2. Tap menu (⋮) → "Install app"
3. Tap "Install" to add to home screen
4. App appears with launcher icon

**iOS**:
1. Open DDoSPoT in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. Name and tap "Add"
5. App launches in fullscreen mode

**Desktop** (Chromium):
1. Open DDoSPoT
2. Click install icon (next to URL bar)
3. Click "Install"
4. App window opens

### 3. Access Mobile View

**Desktop Chrome**:
- Press `F12` for DevTools
- Click device icon (top-left)
- Select mobile device preset
- View responsive design

---

## 📱 Device Support

| Device Type | Screen Size | Breakpoint | Features |
|-------------|------------|-----------|----------|
| Phone | < 768px | Mobile | Full touch optimization, bottom nav |
| Tablet | 768px-1199px | Tablet | 2-column layout, better spacing |
| Desktop | 1200px+ | Desktop | Multi-column, sidebar navigation |

---

## 🔧 Configuration

### Customize Theme Colors

**Edit** `static/mobile.css`:
```css
:root {
    /* Change primary color */
    --primary: #ff6b6b;      /* Change red to your color */
    --secondary: #ff8787;
    --accent: #ffa5a5;
    --bg: #0a0e27;           /* Dark background */
    --surface: #1a1f3a;      /* Card background */
    --text: #e0e0e0;         /* Text color */
    --success: #2ecc71;      /* Success indicator */
    --warning: #f39c12;      /* Warning color */
    --danger: #ff6b6b;       /* Danger/error color */
}
```

### Change App Name & Icon

**Edit** `static/manifest.json`:
```json
{
  "name": "DDoSPoT - Your Title",
  "short_name": "DDoSPoT",
  "icons": [
    {
      "src": "/static/logo-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

### Configure Service Worker Cache

**Edit** `static/service-worker.js`:
```javascript
// Change cache version to clear old caches
const CACHE_NAME = 'ddospot-v2';  // Was v1

// Add/remove assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/mobile.css',
  // Add your files here
];
```

---

## 💡 Features & How-To

### 1. Real-Time Data Updates

**Default**: Updates every second (real-time)

**To Change Interval**:
1. Open Settings ⚙️
2. Change "Refresh Interval"
3. Options: Real-time, 5s, 30s, Manual

### 2. Offline Mode

**Automatic**:
- Service Worker caches all pages and data
- When offline, cached data is displayed
- API requests queue for sync when online
- Works without internet connection

**Manually Trigger**:
1. Tap Menu ☰
2. Tap "Go Offline"
3. Cached data shows with offline badge
4. Changes sync when reconnected

### 3. Push Notifications

**Enable** (if supported):
1. First visit → Install prompt appears
2. Allow notifications when asked
3. Receive alerts for critical threats
4. Tap notification to jump to threat

**Disable**:
1. Browser notifications settings
2. Find DDoSPoT app
3. Disable notifications
4. Or tap "Critical Alerts Only" in settings

### 4. Background Sync

**Automatic**:
- Failed API requests are queued
- Syncs when network returns
- Shows sync status in UI
- No manual action needed

**Manual Sync**:
1. Tap refresh button (⚡)
2. "Real-time" shows active
3. "Syncing..." appears while updating
4. Threat data refreshes automatically

### 5. Settings Access

**From Mobile Dashboard**:
1. Tap menu (☰) top-left
2. Select "Settings"
3. Modify honeypot config
4. Change alert thresholds
5. Adjust service ports
6. Save changes

**From Settings Page** (/settings):
- Full configuration UI
- All options available
- Validation included
- Changes apply immediately

---

## 🎨 Interface Guide

### Bottom Navigation (Mobile)

| Icon | Function | Long-Press |
|------|----------|------------|
| ⚡ | Refresh/Real-time | Toggle auto-refresh |
| ⛶ | Fullscreen | Maximize window |
| ❓ | Help | Open help modal |

### Tab Navigation

| Tab | Content | Updates |
|-----|---------|---------|
| 📊 Overview | Stats, attackers, system health | Real-time |
| 🔴 Threats | IP list, attack details | Real-time |
| 🔔 Alerts | Notifications by severity | Real-time |
| ⚡ Control | Service toggles, actions | On-demand |

### Status Indicators

```
● = Running (green)
● = Warning (yellow)
● = Offline (red)
● = Unknown (gray)
```

### Stat Cards

**Quick Stats**:
- Total Events (last hour)
- Unique IPs (last 24h)
- IPs Blocked (active blocks)
- Detection Rate (current hour)

---

## 🔍 Troubleshooting

### Issue: Service Worker Not Registering

**Solution 1**: Check HTTPS
```bash
# Must use HTTPS (localhost OK)
https://yourdomain.com/

# NOT http
http://yourdomain.com/
```

**Solution 2**: Clear Browser Cache
```bash
# Chrome DevTools
1. Open DevTools (F12)
2. Application tab
3. Clear Site Data
4. Reload page
```

**Solution 3**: Check Manifest
```bash
# Open DevTools
1. Application tab
2. Manifest section
3. Verify all fields present
4. Check icons load
```

### Issue: App Won't Install

**Android Chrome**:
1. Ensure HTTPS enabled
2. Add "Install app" button to page
3. Try alternate browsers (Firefox, Samsung)
4. Clear app cache & data

**iOS Safari**:
1. iOS 14.4+ required for PWA
2. Add to Home Screen (not "Open Link")
3. Check manifest.json exists
4. Try `beforeinstallprompt` handler

### Issue: Data Not Syncing Offline

**Check**:
1. Is Service Worker active? (DevTools → Application)
2. Is cache populated? (Storage tab)
3. Are you actually offline? (DevTools → Network → Offline)

**Fix**:
1. Re-install app
2. Go online to initial sync
3. Check network in DevTools
4. Verify API endpoints accessible

### Issue: Wrong Colors/Theme

**Solution**:
1. Hard refresh: `Ctrl+Shift+R`
2. Clear browser cache
3. Reinstall app
4. Check CSS variables in `mobile.css`

### Issue: Performance Slow

**Optimization**:
1. Enable compression on server
2. Minify CSS/JS
3. Optimize images
4. Use lazy loading
5. Check network tab (DevTools)

---

## 📊 Performance Tips

### Improve Loading Speed

1. **Enable GZIP Compression**:
```nginx
gzip on;
gzip_types text/css application/javascript;
```

2. **Browser Caching**:
```
Cache-Control: public, max-age=31536000
```

3. **Lazy Load Images**:
```html
<img src="image.jpg" loading="lazy">
```

4. **Minify CSS/JS**:
```bash
# Use build tools (webpack, parcel)
npm run build
```

### Optimize Battery Usage

1. Reduce animation frequency
2. Disable auto-refresh when not visible
3. Use dark theme (OLED screens)
4. Limit push notification frequency
5. Close unused browser tabs

### Reduce Data Usage

1. Use "Manual" refresh mode
2. Disable image loading in settings
3. Request CSV export (smaller file)
4. Clear cache periodically
5. Monitor data usage in DevTools

---

## 🔐 Security Notes

### HTTPS Required
- Service Worker needs HTTPS
- API endpoints must be HTTPS
- Localhost development exception only
- Use valid SSL certificate

### Cache Security
- Local device storage (not cloud)
- Only public data cached
- No passwords/secrets stored
- Encrypted transmission required

### Push Notifications
- Server-sent only
- Require user consent
- Encrypted in transit
- Unsubscribe available

### Offline Access
- Limited to previously cached data
- No real-time updates offline
- Changes queue for sync
- Sensitive data protected

---

## 📱 Advanced Usage

### Access Service Worker Console

**Chrome DevTools**:
```javascript
// In Console tab
navigator.serviceWorker.ready.then(reg => {
  console.log('Service Worker active:', reg);
});

// Check cache
caches.keys().then(names => console.log(names));

// Clear cache
caches.delete('ddospot-v1');
```

### Manual Cache Management

**Add URLs to Cache**:
```javascript
if (navigator.serviceWorker.controller) {
  navigator.serviceWorker.controller.postMessage({
    type: 'CACHE_URLS',
    urls: ['/api/threats', '/api/alerts']
  });
}
```

**Clear Cache**:
```javascript
navigator.serviceWorker.controller.postMessage({
  type: 'CLEAR_CACHE'
});
```

### Check Sync Status

**View Pending Syncs**:
```javascript
navigator.serviceWorker.ready.then(reg => {
  reg.sync.getTags().then(tags => {
    console.log('Pending syncs:', tags);
  });
});
```

---

## 🛠️ Maintenance

### Monthly Tasks

- [ ] Review logs for errors
- [ ] Clear old caches
- [ ] Update Service Worker version
- [ ] Check HTTPS certificate expiry
- [ ] Test backup/restore

### Quarterly Tasks

- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance review
- [ ] User feedback analysis
- [ ] Feature planning

### Annual Tasks

- [ ] Major version update
- [ ] Architecture review
- [ ] Capacity planning
- [ ] Disaster recovery drill
- [ ] Training updates

---

## 📞 Support Commands

### Check System Status

```bash
# Service Worker status
systemctl status ddospot-dashboard

# View logs
journalctl -u ddospot-dashboard -n 100

# Check database
sqlite3 ddospot.db "SELECT COUNT(*) FROM threats;"

# Test API
curl https://localhost:5000/api/threats
```

### Reset App State

```bash
# Clear Service Worker
# DevTools → Application → Service Worker → Unregister

# Clear Site Data
# DevTools → Application → Clear Site Data

# Clear Browser Cache
Ctrl+Shift+Delete (most browsers)
```

### Enable Debug Mode

**In Settings**:
1. Enable "Debug Mode"
2. Check browser console (F12)
3. View network requests
4. Monitor performance

---

## 🎓 Resources

### Documentation
- [FEATURE12_COMPLETION.md](FEATURE12_COMPLETION.md) - Technical details
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API endpoints
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - Getting started

### External Resources
- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Responsive Design](https://web.dev/responsive-web-design-basics/)

### Tutorials
- "Building Progressive Web Apps"
- "Offline-First Mobile Web Development"
- "PWA Performance Optimization"

---

## 📋 Checklists

### Initial Setup

- [ ] Verify all PWA files present
- [ ] Test on mobile device
- [ ] Enable HTTPS
- [ ] Install app on phone
- [ ] Test offline mode
- [ ] Verify push notifications
- [ ] Customize theme colors
- [ ] Configure settings

### Weekly Maintenance

- [ ] Monitor app usage
- [ ] Check error logs
- [ ] Verify data sync
- [ ] Test notifications
- [ ] Monitor performance

### Pre-Deployment

- [ ] HTTPS certificate valid
- [ ] Service Worker tested
- [ ] Mobile layout verified
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] Security checklist passed

---

## ✨ Summary

Feature #12 provides a **complete mobile-first PWA experience** with:

- ✅ Responsive design (mobile → desktop)
- ✅ Offline access via Service Worker
- ✅ App installation capability
- ✅ Push notifications
- ✅ Background sync
- ✅ Touch optimization
- ✅ Performance optimized
- ✅ Security hardened

**Status**: Production-ready, fully tested, documented

For more information, see [FEATURE12_COMPLETION.md](FEATURE12_COMPLETION.md)

---

**Quick Links**:
- [Mobile Dashboard](/)
- [Settings](/settings)
- [Advanced Dashboard](/advanced)
- [API Docs](docs/API_DOCUMENTATION.md)
- [Full Docs](docs/)

**Support**: Check documentation or GitHub issues
