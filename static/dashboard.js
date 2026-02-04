// DDoSPot Dashboard JavaScript

// Global state
const state = {
    charts: {},
    map: null,
    markers: {},
    updateInterval: 1000, // Real-time updates (1 second)
    isOnline: false,
    isRefreshPaused: false,
    attackersFilter: { ip: '', severity: '' },
    blacklistFilter: { ip: '', reason: '' },
    eventsFilter: { ip: '', protocol: '', type: '' },
    allAttackers: [],
    allBlacklist: [],
    allEvents: [],
    eventsPage: 1,
    eventsTotal: 0,
    eventsPageSize: 50,
    mapData: [],
    alertSettings: {
        channels: { email: true, discord: false, telegram: false },
        eventRateThreshold: 50,
        uniqueIpsThreshold: 20,
        durationThreshold: 5,
        severityLevels: ['critical', 'high', 'medium']
    }
};

// Load alert settings from localStorage
function loadAlertSettings() {
    const saved = localStorage.getItem('ddospot_alert_settings');
    if (saved) {
        try {
            state.alertSettings = JSON.parse(saved);
        } catch (e) {
            console.error('Failed to load alert settings:', e);
        }
    }
}

// Save alert settings to localStorage
function saveAlertSettings() {
    localStorage.setItem('ddospot_alert_settings', JSON.stringify(state.alertSettings));
}

// Initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DASHBOARD INITIALIZATION START ===');
    
    // Load saved settings
    console.log('Loading settings...');
    try {
        loadAlertSettings();
        console.log('✓ Alert settings loaded');
    } catch (e) { console.error('Alert settings load failed:', e.message); }
    
    try {
        loadDarkMode();
        console.log('✓ Dark mode loaded');
    } catch (e) { console.error('Dark mode load failed:', e.message); }
    
    console.log('Initializing components...');
    try {
        console.log('→ initCharts()...');
        initCharts();
        console.log('✓ Charts initialized');
    } catch (e) { console.error('✗ Chart init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initMap()...');
        initMap();
        console.log('✓ Map initialized');
    } catch (e) { console.error('✗ Map init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initFilters()...');
        initFilters();
        console.log('✓ Filters initialized');
    } catch (e) { console.error('✗ Filter init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initAlerts()...');
        initAlerts();
        console.log('✓ Alerts initialized');
    } catch (e) { console.error('✗ Alert init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initAlertSettings()...');
        initAlertSettings();
        console.log('✓ Alert settings initialized');
    } catch (e) { console.error('✗ Alert settings init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initIncidentResponse()...');
        initIncidentResponse();
        console.log('✓ Incident response initialized');
    } catch (e) { console.error('✗ Incident response init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initReports()...');
        initReports();
        console.log('✓ Reports initialized');
    } catch (e) { console.error('✗ Reports init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initDarkMode()...');
        initDarkMode();
        console.log('✓ Dark mode initialized');
    } catch (e) { console.error('✗ Dark mode init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initAPIKeyManagement()...');
        initAPIKeyManagement();
        console.log('✓ API Key Management initialized');
    } catch (e) { console.error('✗ API Key Management init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initExports()...');
        initExports();
        console.log('✓ Exports initialized');
    } catch (e) { console.error('✗ Export init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initLayoutSettings()...');
        initLayoutSettings();
        console.log('✓ Layout settings initialized');
    } catch (e) { console.error('✗ Layout settings init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initLiveIndicator()...');
        initLiveIndicator();
        console.log('✓ Live indicator initialized');
    } catch (e) { console.error('✗ Live indicator init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initPauseButton()...');
        initPauseButton();
        console.log('✓ Pause button initialized');
    } catch (e) { console.error('✗ Pause button init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initNotifications()...');
        initNotifications();
        console.log('✓ Notifications initialized');
    } catch (e) { console.error('✗ Notifications init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initSearchListeners()...');
        initSearchListeners();
        console.log('✓ Search initialized');
    } catch (e) { console.error('✗ Search init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initLiveLogs()...');
        initLiveLogs();
        console.log('✓ Live logs initialized');
    } catch (e) { console.error('✗ Live logs init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initAnomalyDetection()...');
        initAnomalyDetection();
        console.log('✓ Anomaly detection initialized');
    } catch (e) { console.error('✗ Anomaly detection init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initGeoHeatMap()...');
        initGeoHeatMap();
        console.log('✓ Geo heat map initialized');
    } catch (e) { console.error('✗ Geo heat map init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initThreatIntel()...');
        initThreatIntel();
        console.log('✓ Threat intelligence initialized');
    } catch (e) { console.error('✗ Threat intelligence init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initResponseActions()...');
        initResponseActions();
        console.log('✓ Response actions initialized');
    } catch (e) { console.error('✗ Response actions init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initRateLimitDashboard()...');
        initRateLimitDashboard();
        console.log('✓ Rate limit dashboard initialized');
    } catch (e) { console.error('✗ Rate limit dashboard init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initPerformanceDashboard()...');
        initPerformanceDashboard();
        console.log('✓ Performance dashboard initialized');
    } catch (e) { console.error('✗ Performance dashboard init failed:', e.message, e.stack); }
    
    try {
        console.log('→ initThreatIntelDashboard()...');
        initThreatIntelDashboard();
        console.log('✓ Threat intelligence dashboard initialized');
    } catch (e) { console.error('✗ Threat intelligence dashboard init failed:', e.message, e.stack); }
    
    console.log('Running initial checks and updates...');
    
    // Show connected status immediately
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    if (indicator) indicator.classList.add('healthy');
    if (text) text.textContent = 'Connected';
    state.isOnline = true;
    console.log('✓ Dashboard marked as connected');
    
    // Start health checks in background (non-blocking)
    checkHealth().catch(err => console.error('Health check error:', err));
    
    // Start data updates in background (non-blocking)
    updateDashboard().catch(err => console.error('Dashboard update error:', err));
    
    // Request notification permission in background
    setupNotificationPermissionRequest().catch(err => console.error('Notification setup error:', err));
    
    console.log('Setting up refresh timers...');
    try {
        console.log('→ setupRefreshControl()...');
        setupRefreshControl();
        console.log('✓ Refresh control setup done');
    } catch (e) { console.error('✗ Setup refresh control failed:', e.message, e.stack); }
    
    // Fallback: Set up refresh timers directly if setupRefreshControl fails
    if (!state._refreshTimer) {
        console.log('⚠ Fallback: Setting up real-time refresh directly');
        state._refreshTimer = setInterval(updateDashboard, 1000);
        console.log('✓ Fallback refresh started');
    }
    
    console.log('=== DASHBOARD INITIALIZATION COMPLETE ===');
});

// Update all dashboard data
async function updateDashboard() {
    try {
        console.log('[updateDashboard] Starting dashboard update');
        // Check health status (non-blocking)
        checkHealth().catch(err => console.error('Health check failed:', err));
        
        console.log('[updateDashboard] Making API calls');
        // Update all dashboard data
        const results = await Promise.all([
            updateStats(),
            updateTopAttackers(),
            updateBlacklist(),
            updateRecentEvents(),
            updateTimeline(),
            updateProtocols(),
            updateHeatmap(),
            updateMapData(),
            updateCountryStats(),
            updateDatabaseInfo(),
            updateLiveIndicator(),
            updateAlerts()
        ]);
        console.log('[updateDashboard] Dashboard update complete');
    } catch (error) {
        console.error('Failed to update dashboard:', error);
    }
}

// Initialize alerts
function initAlerts() {
    document.getElementById('test-alert-btn')?.addEventListener('click', sendTestAlert);
    document.getElementById('clear-alerts-btn')?.addEventListener('click', clearAlerts);
    updateAlerts();
}

// Send test alert
async function sendTestAlert() {
    try {
        const response = await fetch('/api/alerts/test?type=critical_attack', { method: 'POST' });
        const data = await response.json();
        alert(data.message || 'Test alert sent');
        updateAlerts();
    } catch (error) {
        console.error('Failed to send test alert:', error);
        alert('Failed to send test alert');
    }
}

// Clear alerts
function clearAlerts() {
    if (confirm('Clear all alert history?')) {
        document.getElementById('alerts-container').innerHTML = '<div class="loading">Alerts cleared</div>';
        setTimeout(() => updateAlerts(), 1000);
    }
}

// Update alerts display
async function updateAlerts() {
    try {
        const response = await fetch('/api/alerts/history?limit=20');
        const alerts = await response.json();
        
        const container = document.getElementById('alerts-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="loading">No alerts</div>';
            return;
        }
        
        alerts.forEach(alert => {
            const div = document.createElement('div');
            div.className = `alert-item ${alert.severity}`;
            
            const timestamp = new Date(alert.timestamp).toLocaleString();
            const ipInfo = alert.ip ? `<div class="alert-meta"><span>IP: ${alert.ip}</span></div>` : '';
            
            div.innerHTML = `
                <div class="alert-content">
                    <div class="alert-type">
                        ${alert.type.replace(/_/g, ' ').toUpperCase()}
                        <span class="alert-badge ${alert.severity}">${alert.severity}</span>
                    </div>
                    <div class="alert-message">${alert.message}</div>
                    ${ipInfo}
                    <div class="alert-meta">
                        <span>${timestamp}</span>
                        <span>${alert.sent ? '✓ Sent' : '○ Logged'}</span>
                    </div>
                </div>
            `;
            
            container.appendChild(div);
        });
    } catch (error) {
        console.error('Failed to update alerts:', error);
    }
}

// Initialize map
function initMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    
    // Create map centered on the world
    state.map = L.map('map').setView([20, 0], 2);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
    }).addTo(state.map);
    
    // Add marker cluster layer
    state.markers = {};
    console.log('Map initialized');
}

// Update map with attack data
async function updateMapData() {
    if (!state.map) return;
    
    try {
        const response = await fetch('/api/map-data');
        const mapData = await response.json();
        state.mapData = mapData;
        
        // Clear existing markers
        Object.values(state.markers).forEach(marker => state.map.removeLayer(marker));
        state.markers = {};
        
        if (!mapData || mapData.length === 0) {
            console.log('No map data available');
            return;
        }
        
        // Add markers for each attack location
        mapData.forEach(location => {
            if (!location.latitude || !location.longitude) return;
            
            const lat = location.latitude;
            const lon = location.longitude;
            const ip = location.ip;
            const events = location.events || 0;
            
            // Marker size based on event count
            const size = Math.min(30, 10 + Math.log(events + 1) * 5);
            const opacity = Math.min(1, 0.5 + (events / 1000));
            
            const marker = L.circleMarker([lat, lon], {
                radius: size,
                fillColor: '#ff3333',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: opacity,
                className: 'attack-marker'
            }).addTo(state.map);
            
            // Popup content
            const popupContent = `
                <strong>Attack Location</strong><br>
                IP: ${ip}<br>
                Country: ${location.country}<br>
                City: ${location.city || 'Unknown'}<br>
                ISP: ${location.isp}<br>
                Events: ${events}<br>
                Last Seen: ${new Date(location.last_seen).toLocaleString()}
            `;
            
            marker.bindPopup(popupContent);
            state.markers[ip] = marker;
        });
        
        console.log(`Map updated with ${mapData.length} locations`);
    } catch (error) {
        console.error('Failed to update map:', error);
    }
}

// Update country statistics
async function updateCountryStats() {
    try {
        const response = await fetch('/api/country-stats');
        const stats = await response.json();
        
        const container = document.getElementById('country-stats');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (!stats || Object.keys(stats).length === 0) {
            container.innerHTML = '<div class="loading">No country data available</div>';
            return;
        }
        
        // Sort by count descending
        const sorted = Object.entries(stats).sort((a, b) => b[1] - a[1]);
        
        sorted.forEach(([country, count]) => {
            const div = document.createElement('div');
            div.className = 'country-stat';
            div.innerHTML = `
                <div class="country-stat-name">${country}</div>
                <div class="country-stat-count">${count}</div>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        console.error('Failed to update country stats:', error);
    }
}

// Initialize filters
function initFilters() {
    // Attackers filters
    document.getElementById('filter-attackers-ip')?.addEventListener('input', applyAttackersFilter);
    document.getElementById('filter-attackers-severity')?.addEventListener('change', applyAttackersFilter);
    
    // Blacklist filters
    document.getElementById('filter-blacklist-ip')?.addEventListener('input', applyBlacklistFilter);
    document.getElementById('filter-blacklist-reason')?.addEventListener('change', applyBlacklistFilter);
    
    // Events filters
    document.getElementById('filter-events-ip')?.addEventListener('input', applyEventsFilter);
    document.getElementById('filter-events-protocol')?.addEventListener('change', applyEventsFilter);
    document.getElementById('filter-events-type')?.addEventListener('change', applyEventsFilter);
    document.getElementById('events-page-size')?.addEventListener('change', () => {
        const val = parseInt(document.getElementById('events-page-size').value, 10) || 50;
        state.eventsPageSize = val;
        state.eventsPage = 1;
        updateRecentEvents();
    });
    
    // Export buttons
    document.getElementById('export-attackers')?.addEventListener('click', () => exportToCSV('attackers'));
    document.getElementById('export-blacklist')?.addEventListener('click', () => exportToCSV('blacklist'));
    document.getElementById('export-events')?.addEventListener('click', () => exportToCSV('events'));
}

// No-op filters for attackers/blacklist (UI hooks present)
function applyAttackersFilter() { /* Optional: implement client-side filter */ }
function applyBlacklistFilter() { /* Optional: implement client-side filter */ }

// Apply events filter and reload
function applyEventsFilter() {
    state.eventsFilter.ip = document.getElementById('filter-events-ip')?.value || '';
    state.eventsFilter.protocol = document.getElementById('filter-events-protocol')?.value || '';
    state.eventsFilter.type = document.getElementById('filter-events-type')?.value || '';
    state.eventsPage = 1;
    updateRecentEvents();
}

// CSV export for tables
function exportToCSV(type) {
    let data = [];
    let headers = [];
    let filename = '';
    if (type === 'attackers') {
        headers = ['IP', 'Events', 'Type', 'Rate', 'Protocols'];
        data = (state.allAttackers || []).map(a => [
            a.ip, a.events, a.type, a.rate, (a.protocols || []).join('; ')
        ]);
        filename = 'attackers.csv';
    } else if (type === 'blacklist') {
        headers = ['IP', 'Reason', 'Severity', 'Expires In'];
        data = (state.allBlacklist || []).map(b => [
            b.ip, b.reason || 'N/A', b.severity || 'Unknown', formatTimeRemaining(b.expires_in || 0)
        ]);
        filename = 'blacklist.csv';
    } else if (type === 'events') {
        headers = ['Timestamp', 'IP', 'Port', 'Protocol', 'Size (B)', 'Type'];
        data = (state.allEvents || []).map(e => [
            new Date(e.timestamp).toLocaleString(), e.ip, e.port || 'N/A', e.protocol || 'Unknown', e.size || 0, e.type || 'Unknown'
        ]);
        filename = 'events.csv';
    }
    let csv = headers.join(',') + '\n';
    data.forEach(row => {
        csv += row.map(cell => {
            const s = String(cell);
            return (s.includes(',') || s.includes('"')) ? '"' + s.replace(/"/g, '""') + '"' : s;
        }).join(',') + '\n';
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Setup refresh interval control
function setupRefreshControl() {
    console.log('Setting up refresh control...');
    const sel = document.getElementById('refresh-interval');
    if (!sel) {
        console.error('refresh-interval element not found');
        return;
    }
    
    sel.addEventListener('change', () => {
        const val = sel.value;
        console.log('Refresh interval changed to:', val);
        
        // Clear existing interval
        if (state._refreshTimer) {
            clearInterval(state._refreshTimer);
        }
        
        if (val === 'real-time') {
            // Real-time mode: update immediately and then continuously
            console.log('Switched to real-time refresh');
            updateDashboard();
            state._refreshTimer = setInterval(updateDashboard, 1000); // Update every 1 second
            state.updateInterval = 1000;
        } else {
            // Standard interval mode
            const interval = parseInt(val, 10) || 5000;
            console.log('Switched to interval refresh:', interval, 'ms');
            state.updateInterval = interval;
            state._refreshTimer = setInterval(updateDashboard, state.updateInterval);
        }
    });
    
    // Initialize with real-time by default
    console.log('Initializing with real-time mode');
    sel.value = 'real-time';
    // Don't wait for updateDashboard - start it in background
    updateDashboard().then(() => {
        console.log('First background update complete');
    }).catch(err => {
        console.error('Background update error:', err);
    });
    console.log('Refresh control setup complete');
}

// Check health
async function checkHealth() {
    try {
        console.log('Checking health...');
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        const response = await fetch('/health', { signal: controller.signal });
        clearTimeout(timeoutId);
        console.log('Health response status:', response.status);
        const data = await response.json();
        console.log('Health data:', data);
        
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (data.status === 'healthy') {
            if (indicator) indicator.classList.add('healthy');
            if (indicator) indicator.classList.remove('unhealthy');
            if (text) text.textContent = 'Connected';
            state.isOnline = true;
            console.log('System is healthy!');
        } else {
            if (indicator) indicator.classList.add('unhealthy');
            if (indicator) indicator.classList.remove('healthy');
            if (text) text.textContent = 'Offline';
            state.isOnline = false;
            console.log('System is offline');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        if (indicator) indicator.classList.add('unhealthy');
        if (text) text.textContent = 'Error';
        state.isOnline = false;
    }
}

// Initialize charts
function initCharts() {
    // Timeline chart
    const timelineElement = document.getElementById('timeline-chart');
    if (!timelineElement) {
        console.warn('⚠ timeline-chart element not found');
        return;
    }
    const timelineCtx = timelineElement.getContext('2d');
    state.charts.timeline = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Attack Events',
                data: [],
                borderColor: '#ff3333',
                backgroundColor: 'rgba(255, 51, 51, 0.1)',
                tension: 0.4,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                }
            }
        }
    });

    // Protocol chart
    const protocolCtx = document.getElementById('protocol-chart').getContext('2d');
    state.charts.protocol = new Chart(protocolCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#ff3333',
                    '#ff6b6b',
                    '#ff9999',
                    '#ffcccc',
                ],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });

    // Initialize heatmap chart
    initHeatmapChart();
}

// Initialize Heatmap Chart
function initHeatmapChart() {
    const heatmapCanvas = document.getElementById('heatmap-chart');
    if (!heatmapCanvas) return;
    
    state.charts.heatmap = new Chart(heatmapCanvas, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Attack Intensity',
                data: [],
                backgroundColor: [],
                borderColor: 'transparent',
                borderRadius: 0,
            }]
        },
        options: {
            indexAxis: 'x',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false,
                }
            },
            scales: {
                y: {
                    display: false,
                    beginAtZero: true,
                },
                x: {
                    ticks: {
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

// Update Heatmap
async function updateHeatmap() {
    try {
        const response = await fetch('/api/timeline?hours=720&bucket=60');
        const timeline = await response.json();
        
        if (!state.charts.heatmap || !timeline || timeline.length === 0) {
            return;
        }

        // Aggregate events by hour of day (0-23) across all 30 days
        const hourlyData = {};
        
        // Initialize 24 hours
        for (let i = 0; i < 24; i++) {
            hourlyData[i] = 0;
        }
        
        // Aggregate events by hour of day
        timeline.forEach(item => {
            if (item.time) {
                const date = new Date(item.time);
                const hour = date.getHours();
                hourlyData[hour] += item.events || 1;
            }
        });

        const labels = Object.keys(hourlyData).map(h => `${h}:00`);
        const data = Object.values(hourlyData);
        
        // Find max for normalization
        const maxValue = Math.max(...data, 1);
        
        // Generate colors based on intensity (heatmap: cool to hot)
        const colors = data.map(value => {
            const intensity = value / maxValue;
            
            if (intensity > 0.8) return '#8b0000';      // Very Dark Red
            if (intensity > 0.6) return '#d32f2f';      // Dark Red
            if (intensity > 0.4) return '#ff6b6b';      // Red
            if (intensity > 0.2) return '#ff9999';      // Light Red
            if (intensity > 0.05) return '#ffcccc';     // Very Light Red
            return '#ffe0e0';                           // Barely visible
        });

        state.charts.heatmap.data.labels = labels;
        state.charts.heatmap.data.datasets[0].data = data;
        state.charts.heatmap.data.datasets[0].backgroundColor = colors;
        state.charts.heatmap.update('none');
        
        console.log('Heatmap updated');
    } catch (error) {
        console.error('Failed to update heatmap:', error);
    }
}

// Update statistics
async function updateStats() {
    try {
        console.log('Fetching stats...');
        const response = await fetch('/api/stats?hours=24'); // Changed to 24 hours for consistency with mobile
        console.log('Stats response status:', response.status);
        const stats = await response.json();
        console.log('Stats data received:', stats);

        const totalEl = document.getElementById('stat-total-events');
        const ipsEl = document.getElementById('stat-unique-ips');
        const blacklistEl = document.getElementById('stat-blacklist');
        const protocolEl = document.getElementById('stat-top-protocol');

        if (totalEl) totalEl.textContent = stats.total_events.toLocaleString();
        if (ipsEl) ipsEl.textContent = stats.unique_ips;
        if (blacklistEl) blacklistEl.textContent = stats.blacklisted_ips;
        if (protocolEl) protocolEl.textContent = stats.top_protocol || 'N/A';
        
        console.log('Stats updated successfully');
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

// Update top attackers
async function updateTopAttackers() {
    try {
        const response = await fetch('/api/top-attackers?limit=10');
        const attackers = await response.json();

        const tbody = document.getElementById('attackers-tbody');
        tbody.innerHTML = '';

        if (attackers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No attacks yet</td></tr>';
            return;
        }

        attackers.forEach(attacker => {
            // Calculate risk score
            const riskScore = calculateRiskScore(attacker);
            const riskLevel = getRiskLevel(riskScore);
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <a href="/profile/${attacker.ip}">${attacker.ip}</a>
                        <div class="risk-score-badge ${riskLevel.level.toLowerCase().replace(' ', '-')}">
                            <span>${riskLevel.emoji} ${riskLevel.level}</span>
                            <span style="font-size: 11px; opacity: 0.8;">${riskScore}/100</span>
                        </div>
                        <div class="risk-score-bar">
                            <div class="risk-score-fill ${riskLevel.level.toLowerCase().replace(' ', '-')}" style="width: ${riskScore}%;"></div>
                        </div>
                    </div>
                </td>
                <td>${attacker.events}</td>
                <td>${attacker.type}</td>
                <td>${attacker.rate}</td>
                <td>${attacker.protocols.join(', ')}</td>
                <td>
                    <button class="action-btn-small view" onclick="openActionModal('${attacker.ip}')">👁️ View</button>
                    <button class="action-btn-small blacklist" onclick="confirmBlacklist('${attacker.ip}')">🚫 Block</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Failed to update top attackers:', error);
    }
}

// Update blacklist
async function updateBlacklist() {
    try {
        const response = await fetch('/api/blacklist');
        const blacklist = await response.json();

        const tbody = document.getElementById('blacklist-tbody');
        tbody.innerHTML = '';

        if (blacklist.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="loading">No blacklisted IPs</td></tr>';
            return;
        }

        blacklist.forEach(entry => {
            const row = document.createElement('tr');
            const severityClass = `severity ${entry.severity}`;
            row.innerHTML = `
                <td>${entry.ip}</td>
                <td>${entry.reason}</td>
                <td><span class="${severityClass}">${entry.severity}</span></td>
                <td>${formatTimeRemaining(entry.expires_in)}</td>
                <td>
                    <button class="action-btn-small view" onclick="openActionModal('${entry.ip}')">👁️ View</button>
                    <button class="action-btn-small whitelist" onclick="confirmUnblacklist('${entry.ip}')">✓ Unblock</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Failed to update blacklist:', error);
    }
}

// Update recent events
async function updateRecentEvents() {
    try {
        const params = new URLSearchParams();
        params.set('minutes', '43200');  // 30 days
        params.set('page', String(state.eventsPage));
        params.set('page_size', String(state.eventsPageSize));
        if (state.eventsFilter.ip) params.set('ip', state.eventsFilter.ip);
        if (state.eventsFilter.protocol) params.set('protocol', state.eventsFilter.protocol);
        if (state.eventsFilter.type) params.set('type', state.eventsFilter.type);
        const response = await fetch('/api/recent-events?' + params.toString());
        const data = await response.json();
        const events = Array.isArray(data) ? data : (data.items || []);

        state.allEvents = events;
        state.eventsTotal = data.total || events.length;
        state.eventsPageSize = data.page_size || state.eventsPageSize;
        state.eventsPage = data.page || state.eventsPage;

        const tbody = document.getElementById('events-tbody');
        tbody.innerHTML = '';

        if (events.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No events</td></tr>';
        } else {
            events.forEach(event => {
            const row = document.createElement('tr');
            const time = new Date(event.timestamp).toLocaleTimeString();
            row.innerHTML = `
                <td>${time}</td>
                <td><a href="/profile/${event.ip}">${event.ip}</a></td>
                <td>${event.port}</td>
                <td>${event.protocol}</td>
                <td>${event.size} B</td>
                <td>${event.type}</td>
            `;
            tbody.appendChild(row);
            });
        }
        updateEventsPaginationControls();
    } catch (error) {
        console.error('Failed to update recent events:', error);
    }
}

function updateEventsPaginationControls() {
    const prevBtn = document.getElementById('events-prev');
    const nextBtn = document.getElementById('events-next');
    const info = document.getElementById('events-page-info');
    if (!prevBtn || !nextBtn || !info) return;
    const maxPage = Math.max(1, Math.ceil(state.eventsTotal / state.eventsPageSize));
    info.textContent = `Page ${state.eventsPage} / ${maxPage}`;
    prevBtn.disabled = state.eventsPage <= 1;
    nextBtn.disabled = state.eventsPage >= maxPage;
    prevBtn.onclick = () => {
        if (state.eventsPage > 1) {
            state.eventsPage -= 1;
            updateRecentEvents();
        }
    };
    nextBtn.onclick = () => {
        const max = Math.max(1, Math.ceil(state.eventsTotal / state.eventsPageSize));
        if (state.eventsPage < max) {
            state.eventsPage += 1;
            updateRecentEvents();
        }
    };
}

// Update timeline chart
async function updateTimeline() {
    try {
        const response = await fetch('/api/timeline?hours=720&bucket=60');
        const timeline = await response.json();

        const labels = timeline.map(point => {
            const date = new Date(point.time);
            return date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        });
        const data = timeline.map(point => point.events);

        state.charts.timeline.data.labels = labels;
        state.charts.timeline.data.datasets[0].data = data;
        state.charts.timeline.update();
    } catch (error) {
        console.error('Failed to update timeline:', error);
    }
}

// Update protocol breakdown
async function updateProtocols() {
    try {
        const response = await fetch('/api/protocol-breakdown');
        const protocols = await response.json();

        const labels = Object.keys(protocols);
        const data = Object.values(protocols);

        state.charts.protocol.data.labels = labels;
        state.charts.protocol.data.datasets[0].data = data;
        state.charts.protocol.update();
    } catch (error) {
        console.error('Failed to update protocols:', error);
    }
}

// Update database info
async function updateDatabaseInfo() {
    try {
        const response = await fetch('/api/database-info');
        const info = await response.json();

        document.getElementById('db-size').textContent = info.size_mb + ' MB';
        document.getElementById('db-events').textContent = info.event_count.toLocaleString();
        document.getElementById('db-profiles').textContent = info.profile_count;
    } catch (error) {
        console.error('Failed to update database info:', error);
    }
}

// Helper function to format time remaining
function formatTimeRemaining(seconds) {
    if (seconds <= 0) return 'Expired';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
}

// ========================
// API KEY MANAGEMENT
// ========================

// Initialize API Keys UI
function initAPIKeyManagement() {
    const createBtn = document.getElementById('api-key-create-btn');
    const copyBtn = document.getElementById('copy-api-key-btn');
    const closeBtn = document.getElementById('close-api-key-display');
    
    if (createBtn) createBtn.addEventListener('click', createNewAPIKey);
    if (copyBtn) copyBtn.addEventListener('click', copyAPIKeyToClipboard);
    if (closeBtn) closeBtn.addEventListener('click', closeAPIKeyDisplay);
    
    loadAPIKeys();
}

// Load and display API keys
async function loadAPIKeys() {
    try {
        const response = await fetch('/api/auth/keys', {
            headers: {
                'X-API-Key': localStorage.getItem('admin_api_key') || ''
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                document.getElementById('api-keys-list').innerHTML = `
                    <div class="api-keys-empty">
                        <div class="api-keys-empty-icon">🔐</div>
                        <p>Admin API key required to manage keys</p>
                    </div>
                `;
                return;
            }
            throw new Error('Failed to load API keys');
        }
        
        const data = await response.json();
        displayAPIKeys(data.keys || []);
    } catch (error) {
        console.error('Error loading API keys:', error);
        document.getElementById('api-keys-list').innerHTML = `
            <div class="api-keys-empty">
                <div class="api-keys-empty-icon">❌</div>
                <p>Error loading API keys: ${error.message}</p>
            </div>
        `;
    }
}

// Display API keys in table
function displayAPIKeys(keys) {
    const container = document.getElementById('api-keys-list');
    
    if (keys.length === 0) {
        container.innerHTML = `
            <div class="api-keys-empty">
                <div class="api-keys-empty-icon">🔑</div>
                <p>No API keys yet. Create one to get started!</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="api-keys-table">';
    keys.forEach(key => {
        const permissions = (key.permissions || []).map(p => 
            `<span class="permission-badge">${p}</span>`
        ).join('');
        
        const createdDate = new Date(key.created_at * 1000).toLocaleDateString();
        
        html += `
            <div class="api-key-row">
                <div class="api-key-name">${escapeHtml(key.name)}</div>
                <div class="api-key-prefix">${key.prefix}...</div>
                <div class="api-key-permissions">${permissions}</div>
                <div class="api-key-created">${createdDate}</div>
                <button class="api-key-revoke-btn" onclick="revokeAPIKey('${key.prefix}')">🗑️ Revoke</button>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// Create new API key
async function createNewAPIKey() {
    try {
        const name = document.getElementById('api-key-name')?.value?.trim();
        if (!name) {
            alert('Please enter a key name');
            return;
        }
        
        const permissions = [];
        document.querySelectorAll('.api-permission:checked').forEach(checkbox => {
            permissions.push(checkbox.value);
        });
        
        if (permissions.length === 0) {
            alert('Please select at least one permission');
            return;
        }
        
        const adminKey = localStorage.getItem('admin_api_key') || '';
        const response = await fetch('/api/auth/keys/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': adminKey
            },
            body: JSON.stringify({ name, permissions })
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                alert('Admin API key required');
                return;
            }
            throw new Error('Failed to create API key');
        }
        
        const data = await response.json();
        showNewAPIKey(data.api_key);
        
        // Reset form
        document.getElementById('api-key-name').value = '';
        document.querySelectorAll('.api-permission').forEach(cb => {
            cb.checked = cb.value === 'read';
        });
        
        // Reload keys list
        setTimeout(loadAPIKeys, 1000);
    } catch (error) {
        console.error('Error creating API key:', error);
        alert('Error: ' + error.message);
    }
}

// Display new API key
function showNewAPIKey(apiKey) {
    const display = document.getElementById('api-key-display');
    const keyValue = document.getElementById('new-api-key-value');
    
    keyValue.textContent = apiKey;
    display.style.display = 'block';
    display.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Copy API key to clipboard
function copyAPIKeyToClipboard() {
    const keyValue = document.getElementById('new-api-key-value').textContent;
    navigator.clipboard.writeText(keyValue).then(() => {
        const btn = document.getElementById('copy-api-key-btn');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

// Close new key display
function closeAPIKeyDisplay() {
    document.getElementById('api-key-display').style.display = 'none';
}

// Revoke API key
async function revokeAPIKey(keyPrefix) {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
        return;
    }
    
    try {
        const adminKey = localStorage.getItem('admin_api_key') || '';
        const response = await fetch(`/api/auth/keys/${keyPrefix}/revoke`, {
            method: 'POST',
            headers: {
                'X-API-Key': adminKey
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to revoke API key');
        }
        
        alert('API key revoked successfully');
        loadAPIKeys();
    } catch (error) {
        console.error('Error revoking API key:', error);
        alert('Error: ' + error.message);
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================
// EXPORT FUNCTIONS
// ========================

// Initialize export buttons
function initExports() {
    document.getElementById('export-events-csv')?.addEventListener('click', () => exportData('events', 'csv'));
    document.getElementById('export-events-json')?.addEventListener('click', () => exportData('events', 'json'));
    document.getElementById('export-stats-json')?.addEventListener('click', () => exportData('stats', 'json'));
    document.getElementById('export-profiles-json')?.addEventListener('click', () => exportData('profiles', 'json'));
    document.getElementById('export-report-json')?.addEventListener('click', () => exportData('report', 'json'));
}

// Dark mode toggle
// Load dark mode preference from localStorage
function loadDarkMode() {
    const isDarkMode = localStorage.getItem('ddospot-dark-mode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
}

// Setup notification permission request to fire on first user interaction
function setupNotificationPermissionRequest() {
    // Minimal setup - just attach listener, don't do anything blocking
    if ('Notification' in window && Notification.permission === 'default') {
        // Use a simple one-time click listener
        const handleClick = () => {
            try {
                Notification.requestPermission();
            } catch (e) {
                console.log('Notification setup:', e);
            }
            document.removeEventListener('click', handleClick);
        };
        document.addEventListener('click', handleClick, { once: true });
    }
    return Promise.resolve();
}

// Manual request for notification permission (can be called from user handlers)
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(err => {
            console.log('Notification permission request failed:', err);
        });
    }
}

function initDarkMode() {
    const toggle = document.getElementById('dark-mode-toggle');
    if (!toggle) return;
    
    function applyDarkModeStyles(isDark) {
        const countryStats = document.querySelectorAll('.country-stat');
        countryStats.forEach(el => {
            if (isDark) {
                el.style.background = 'linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%)';
                el.style.color = '#e0e0e0';
                el.style.borderLeft = '4px solid #ff3333';
            } else {
                el.style.background = '';
                el.style.color = '';
                el.style.borderLeft = '';
            }
        });
        
        const countryStatNames = document.querySelectorAll('.country-stat-name');
        countryStatNames.forEach(el => {
            el.style.color = isDark ? '#e0e0e0' : '';
        });
        
        const countryStatCounts = document.querySelectorAll('.country-stat-count');
        countryStatCounts.forEach(el => {
            el.style.background = isDark ? '#ff3333' : '';
            el.style.color = isDark ? 'white' : '';
        });
    }
    
    // Load saved preference
    const isDarkMode = localStorage.getItem('ddospot-dark-mode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        toggle.textContent = '☀️';
        applyDarkModeStyles(true);
    }
    
    toggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isNowDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('ddospot-dark-mode', isNowDark ? 'true' : 'false');
        toggle.textContent = isNowDark ? '☀️' : '🌙';
        applyDarkModeStyles(isNowDark);
    });
    
    // Also apply styles when country stats are updated
    const originalUpdateCountryStats = window.updateCountryStats;
    window.updateCountryStats = async function() {
        await originalUpdateCountryStats.call(this);
        const isDark = document.body.classList.contains('dark-mode');
        if (isDark) {
            applyDarkModeStyles(true);
        }
    };
}

// Export data function
async function exportData(type, format) {
    const statusEl = document.getElementById('export-status');
    try {
        statusEl.textContent = '📥 Exporting...';
        statusEl.className = 'export-status';
        statusEl.style.display = 'block';
        
        const url = `/api/export/${type}/${format}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        // Get filename from response header or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = `ddospot_${type}.${format}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=([^;]+)/);
            if (match) filename = match[1].replace(/"/g, '');
        }
        
        const blob = await response.blob();
        const url_link = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url_link;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url_link);
        a.remove();
        
        statusEl.textContent = `✅ Downloaded: ${filename}`;
        statusEl.className = 'export-status success';
        
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    } catch (error) {
        console.error(`Export failed:`, error);
        statusEl.textContent = `❌ Export failed: ${error.message}`;
        statusEl.className = 'export-status error';
    }
}

// Call export init in main DOMContentLoaded
// (Moved to first DOMContentLoaded - consolidating all initialization)

// Format time difference for display
function formatTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 5) return 'just now';
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return date.toLocaleTimeString();
}

// Update live indicator timestamp
function updateLiveIndicator() {
    const updateTimeEl = document.getElementById('update-time');
    if (updateTimeEl) {
        updateTimeEl.textContent = formatTimeAgo(new Date());
    }
}

// Initialize live indicator
function initLiveIndicator() {
    updateLiveIndicator();
    // Update timestamp every 5 seconds
    setInterval(updateLiveIndicator, 5000);
}

// Pause/Resume Button
function initPauseButton() {
    const pauseBtn = document.getElementById('pause-refresh-btn');
    if (!pauseBtn) return;
    
    pauseBtn.addEventListener('click', () => {
        state.isRefreshPaused = !state.isRefreshPaused;
        
        if (state.isRefreshPaused) {
            pauseBtn.textContent = '⏸️';
            pauseBtn.title = 'Resume refresh';
            pauseBtn.classList.add('paused');
            console.log('Refresh paused');
        } else {
            pauseBtn.textContent = '▶️';
            pauseBtn.title = 'Pause refresh';
            pauseBtn.classList.remove('paused');
            updateDashboard();
            console.log('Refresh resumed');
        }
    });
}

// Browser Notifications
function initNotifications() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

function sendNotification(title, options = {}) {
    if ('Notification' in window && Notification.permission === 'granted') {
        try {
            const defaultOptions = {
                icon: '🍯',
                badge: '🍯',
                tag: 'ddospot-alert',
                requireInteraction: true,
                ...options
            };
            
            new Notification(title, defaultOptions);
            console.log('Notification sent:', title);
        } catch (e) {
            console.error('Failed to send notification:', e);
        }
    }
}

// Check for critical attacks and send notifications based on custom thresholds
async function checkCriticalAttacks() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Use custom alert thresholds
        const eventThreshold = state.alertSettings.eventRateThreshold;
        const ipThreshold = state.alertSettings.uniqueIpsThreshold;
        const enabledChannels = state.alertSettings.channels;
        const severityLevels = state.alertSettings.severityLevels;

        // Check if any channels are enabled and severity levels are selected
        const hasEnabledChannels = Object.values(enabledChannels).some(v => v);
        if (!hasEnabledChannels || severityLevels.length === 0) return;

        // Check if attack rate threshold is exceeded
        if (stats.events_per_minute && stats.events_per_minute > eventThreshold) {
            const channelList = Object.entries(enabledChannels)
                .filter(([_, enabled]) => enabled)
                .map(([channel, _]) => channel.toUpperCase())
                .join(', ');
            
            sendNotification('🚨 High Attack Rate Detected!', {
                body: `${stats.events_per_minute.toFixed(0)} events/min (threshold: ${eventThreshold})`,
                tag: 'high-attack-rate'
            });
        }
        
        // Check if unique IPs threshold is exceeded
        if (stats.unique_ips && stats.unique_ips > ipThreshold) {
            sendNotification('🔴 Multiple Attackers Alert', {
                body: `${stats.unique_ips} unique IPs (threshold: ${ipThreshold})`,
                tag: 'multiple-attackers'
            });
        }
    } catch (e) {
        console.error('Failed to check critical attacks:', e);
    }
}

// Calculate IP Risk Score
function calculateRiskScore(attacker) {
    let score = 0;
    
    // Base score from event count (0-40 points)
    if (attacker.events) {
        score += Math.min(40, Math.floor(attacker.events / 5));
    }
    
    // Severity multiplier (0-30 points)
    const severityMap = { 'critical': 30, 'high': 20, 'medium': 10, 'low': 5 };
    score += severityMap[attacker.severity] || 0;
    
    // Multi-protocol attacks (bonus 20 points)
    const protocols = attacker.protocols ? (Array.isArray(attacker.protocols) ? attacker.protocols.length : attacker.protocols.split(',').length) : 0;
    if (protocols > 2) score += 20;
    
    // Attack rate (0-10 points)
    if (attacker.rate_per_min) {
        score += Math.min(10, Math.floor(attacker.rate_per_min / 10));
    }
    
    // Cap at 100
    score = Math.min(100, score);
    
    return score;
}

// Get risk level from score
function getRiskLevel(score) {
    if (score >= 75) return { level: 'Very High', emoji: '🔴', color: '#d32f2f' };
    if (score >= 50) return { level: 'High', emoji: '🟠', color: '#ff6f00' };
    if (score >= 25) return { level: 'Medium', emoji: '🟡', color: '#fbc02d' };
    return { level: 'Low', emoji: '🟢', color: '#388e3c' };
}

// Alert Settings Configuration
function initAlertSettings() {
    const alertSettingsBtn = document.getElementById('alert-settings-btn');
    const alertModal = document.getElementById('alert-settings-modal');
    const alertModalClose = document.getElementById('alert-modal-close');
    const saveAlertsBtn = document.getElementById('save-alerts-btn');
    const resetAlertsBtn = document.getElementById('reset-alerts-btn');

    // Open modal
    alertSettingsBtn.addEventListener('click', () => {
        alertModal.style.display = 'flex';
        loadAlertSettingsToUI();
    });

    // Close modal
    const closeModal = () => {
        alertModal.style.display = 'none';
    };
    alertModalClose.addEventListener('click', closeModal);
    alertModal.addEventListener('click', (e) => {
        if (e.target === alertModal) closeModal();
    });

    // Save settings
    saveAlertsBtn.addEventListener('click', saveAlertSettingsFromUI);

    // Reset to defaults
    resetAlertsBtn.addEventListener('click', () => {
        state.alertSettings = {
            channels: { email: true, discord: false, telegram: false },
            eventRateThreshold: 50,
            uniqueIpsThreshold: 20,
            durationThreshold: 5,
            severityLevels: ['critical', 'high', 'medium']
        };
        saveAlertSettings();
        loadAlertSettingsToUI();
        showSettingsMessage('✓ Settings reset to default');
    });
}

// Load current settings into UI
function loadAlertSettingsToUI() {
    // Channels
    document.getElementById('alert-channel-email').checked = state.alertSettings.channels.email;
    document.getElementById('alert-channel-discord').checked = state.alertSettings.channels.discord;
    document.getElementById('alert-channel-telegram').checked = state.alertSettings.channels.telegram;

    // Thresholds
    document.getElementById('alert-events-threshold').value = state.alertSettings.eventRateThreshold;
    document.getElementById('alert-events-input').value = state.alertSettings.eventRateThreshold;
    document.getElementById('alert-unique-ips-threshold').value = state.alertSettings.uniqueIpsThreshold;
    document.getElementById('alert-unique-ips-input').value = state.alertSettings.uniqueIpsThreshold;
    document.getElementById('alert-duration-threshold').value = state.alertSettings.durationThreshold;
    document.getElementById('alert-duration-input').value = state.alertSettings.durationThreshold;

    // Severity levels
    document.querySelectorAll('.alert-severity').forEach(checkbox => {
        checkbox.checked = state.alertSettings.severityLevels.includes(checkbox.value);
    });

    // Sync slider/input pairs
    setupThresholdSync();
}

// Setup slider/input synchronization
function setupThresholdSync() {
    const thresholds = [
        { slider: 'alert-events-threshold', input: 'alert-events-input' },
        { slider: 'alert-unique-ips-threshold', input: 'alert-unique-ips-input' },
        { slider: 'alert-duration-threshold', input: 'alert-duration-input' }
    ];

    thresholds.forEach(pair => {
        const slider = document.getElementById(pair.slider);
        const input = document.getElementById(pair.input);

        if (!slider || !input) return;

        slider.removeEventListener('input', sliderSyncHandler);
        input.removeEventListener('input', inputSyncHandler);

        const sliderSyncHandler = () => { input.value = slider.value; };
        const inputSyncHandler = () => { slider.value = input.value; };

        slider.addEventListener('input', sliderSyncHandler);
        input.addEventListener('input', inputSyncHandler);
    });
}

// Save settings from UI
function saveAlertSettingsFromUI() {
    // Channels
    state.alertSettings.channels = {
        email: document.getElementById('alert-channel-email').checked,
        discord: document.getElementById('alert-channel-discord').checked,
        telegram: document.getElementById('alert-channel-telegram').checked
    };

    // Thresholds
    state.alertSettings.eventRateThreshold = parseInt(document.getElementById('alert-events-input').value);
    state.alertSettings.uniqueIpsThreshold = parseInt(document.getElementById('alert-unique-ips-input').value);
    state.alertSettings.durationThreshold = parseInt(document.getElementById('alert-duration-input').value);

    // Severity levels
    state.alertSettings.severityLevels = [];
    document.querySelectorAll('.alert-severity:checked').forEach(checkbox => {
        state.alertSettings.severityLevels.push(checkbox.value);
    });

    saveAlertSettings();
    showSettingsMessage('✓ Alert settings saved successfully!');
}

// Show temporary message in modal
function showSettingsMessage(message) {
    const msgDiv = document.getElementById('alert-settings-message');
    if (!msgDiv) return;
    msgDiv.textContent = message;
    msgDiv.style.display = 'block';
    setTimeout(() => {
        msgDiv.style.display = 'none';
    }, 3000);
}

function initLayoutSettings() {
    const layoutBtn = document.getElementById('layout-settings-btn');
    const layoutModal = document.getElementById('layout-modal');
    const closeBtn = document.getElementById('modal-close');
    const closeLayoutBtn = document.getElementById('close-layout-btn');
    const resetBtn = document.getElementById('reset-layout-btn');
    const toggles = document.querySelectorAll('.section-toggle');

    const sectionMap = {
        'section-alerts': '.section:has(+ .section h2:contains("Recent Alerts"))',
        'section-charts': '.charts-section',
        'section-attackers': '.section:has(+ .section h2:contains("Top Attacking"))',
        'section-blacklist': '.section:has(+ .section h2:contains("Blacklist"))',
        'section-events': '.section:has(+ .section h2:contains("Recent Attack"))',
        'section-database': '.section:has(+ .section h2:contains("Database"))',
        'section-map': '.section:has(+ .section h2:contains("Attack Origins"))',
        'section-export': '.export-section',
        'section-readme': '.readme-section'
    };

    const sectionSelectors = {
        'section-alerts': '[data-section="alerts"]',
        'section-reports': '[data-section="reports"]',
        'section-charts': '[data-section="charts"]',
        'section-heatmap': '[data-section="charts"]',
        'section-attackers': '[data-section="attackers"]',
        'section-blacklist': '[data-section="blacklist"]',
        'section-events': '[data-section="events"]',
        'section-logs': '[data-section="logs"]',
        'section-anomaly': '[data-section="anomaly"]',
        'section-database': '[data-section="database"]',
        'section-map': '[data-section="map"]',
        'section-threat': '[data-section="threat"]',
        'section-response': '[data-section="response"]',
        'section-export': '[data-section="export"]',
        'section-readme': '[data-section="readme"]'
    };

    // Load saved layout from localStorage
    function loadLayout() {
        // Clear old layout format and start fresh
        localStorage.removeItem('ddospot-layout');
        
        // All sections visible by default
        toggles.forEach(toggle => {
            toggle.checked = true;
        });
        applyLayoutVisibility();
    }

    // Apply visibility to sections
    function applyLayoutVisibility() {
        toggles.forEach(toggle => {
            const selector = sectionSelectors[toggle.name];
            const section = document.querySelector(selector);
            if (section) {
                if (toggle.checked) {
                    section.classList.remove('hidden');
                } else {
                    section.classList.add('hidden');
                }
            }
        });
    }

    // Save layout to localStorage
    function saveLayout() {
        const layout = {};
        toggles.forEach(toggle => {
            layout[toggle.name] = toggle.checked;
        });
        localStorage.setItem('ddospot-layout', JSON.stringify(layout));
    }

    // Open modal
    layoutBtn.addEventListener('click', () => {
        layoutModal.style.display = 'flex';
    });

    // Close modal
    function closeModal() {
        layoutModal.style.display = 'none';
    }

    closeBtn.addEventListener('click', closeModal);
    closeLayoutBtn.addEventListener('click', () => {
        saveLayout();
        closeModal();
    });

    // Close on background click
    layoutModal.addEventListener('click', (e) => {
        if (e.target === layoutModal) {
            closeModal();
        }
    });

    // Toggle handler
    toggles.forEach(toggle => {
        toggle.addEventListener('change', applyLayoutVisibility);
    });

    // Reset layout
    resetBtn.addEventListener('click', () => {
        toggles.forEach(toggle => {
            toggle.checked = true;
        });
        applyLayoutVisibility();
        saveLayout();
    });

    // Load on init
    loadLayout();
}

// Incident Response System
let currentActionIP = null;

function initIncidentResponse() {
    // Action modal
    const actionModal = document.getElementById('ip-action-modal');
    const actionModalClose = document.getElementById('action-modal-close');
    const profileModal = document.getElementById('ip-profile-modal');
    const profileModalClose = document.getElementById('profile-modal-close');
    const profileCloseBtn = document.getElementById('profile-close-btn');

    // Close action modal
    actionModalClose.addEventListener('click', () => { actionModal.style.display = 'none'; });
    actionModal.addEventListener('click', (e) => {
        if (e.target === actionModal) actionModal.style.display = 'none';
    });

    // Close profile modal
    profileModalClose.addEventListener('click', () => { profileModal.style.display = 'none'; });
    profileCloseBtn.addEventListener('click', () => { profileModal.style.display = 'none'; });
    profileModal.addEventListener('click', (e) => {
        if (e.target === profileModal) profileModal.style.display = 'none';
    });

    // Action buttons
    document.getElementById('action-view-profile').addEventListener('click', () => {
        actionModal.style.display = 'none';
        viewIPProfile(currentActionIP);
    });

    document.getElementById('action-blacklist-btn').addEventListener('click', () => {
        performBlacklist(currentActionIP);
        actionModal.style.display = 'none';
    });

    document.getElementById('action-whitelist-btn').addEventListener('click', () => {
        performWhitelist(currentActionIP);
        actionModal.style.display = 'none';
    });

    document.getElementById('action-block-country-btn').addEventListener('click', () => {
        blockCountryByIP(currentActionIP);
        actionModal.style.display = 'none';
    });
}

// Open action modal for IP
function openActionModal(ip) {
    currentActionIP = ip;
    const modal = document.getElementById('ip-action-modal');
    document.getElementById('action-ip-display').textContent = ip;
    document.getElementById('action-message').style.display = 'none';
    modal.style.display = 'flex';
}

// Confirm and blacklist
function confirmBlacklist(ip) {
    if (confirm(`Add ${ip} to blacklist?`)) {
        performBlacklist(ip);
    }
}

// Perform blacklist action
async function performBlacklist(ip) {
    try {
        const response = await fetch(`/api/blacklist/add?ip=${ip}&reason=auto-blocked&severity=critical`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showActionMessage(data.message || 'IP added to blacklist', 'success');
        setTimeout(() => {
            updateTopAttackers();
            updateBlacklist();
        }, 1000);
    } catch (error) {
        showActionMessage(`Error: ${error.message}`, 'error');
        console.error('Blacklist action failed:', error);
    }
}

// Perform whitelist action
async function performWhitelist(ip) {
    try {
        const response = await fetch(`/api/whitelist/add?ip=${ip}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showActionMessage(data.message || 'IP added to whitelist', 'success');
        setTimeout(() => updateTopAttackers(), 1000);
    } catch (error) {
        showActionMessage(`Error: ${error.message}`, 'error');
        console.error('Whitelist action failed:', error);
    }
}

// Block entire country by IP
async function blockCountryByIP(ip) {
    try {
        // First, get the country for this IP
        const profileResponse = await fetch(`/api/profile/${ip}`);
        const profile = await profileResponse.json();
        
        if (!profile.country) {
            showActionMessage('Could not determine country for this IP', 'error');
            return;
        }

        if (!confirm(`Block all IPs from ${profile.country}?`)) return;

        // Block the country
        const response = await fetch(`/api/blacklist/block-country?country=${profile.country}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showActionMessage(data.message || `Country ${profile.country} blocked`, 'success');
        setTimeout(() => updateBlacklist(), 1000);
    } catch (error) {
        showActionMessage(`Error: ${error.message}`, 'error');
        console.error('Block country action failed:', error);
    }
}

// View IP profile
async function viewIPProfile(ip) {
    try {
        const profileModal = document.getElementById('ip-profile-modal');
        document.getElementById('profile-ip-display').textContent = ip;
        
        // Fetch profile data
        const response = await fetch(`/api/profile/${ip}`);
        const profile = await response.json();

        // Populate profile fields
        document.getElementById('profile-events').textContent = profile.events || '-';
        document.getElementById('profile-type').textContent = profile.type || '-';
        document.getElementById('profile-rate').textContent = (profile.rate_per_min || '-') + ' events/min';
        document.getElementById('profile-severity').textContent = profile.severity || '-';
        document.getElementById('profile-protocols').textContent = (profile.protocols || []).join(', ') || '-';
        document.getElementById('profile-country').textContent = profile.country || '-';
        document.getElementById('profile-isp').textContent = profile.isp || '-';
        
        // Calculate and display risk score
        const riskScore = calculateRiskScore(profile);
        const riskLevel = getRiskLevel(riskScore);
        document.getElementById('profile-risk').innerHTML = 
            `${riskLevel.emoji} ${riskScore}/100 (<span style="color: ${riskLevel.color}">${riskLevel.level}</span>)`;

        // Fetch and display recent events
        const eventsResponse = await fetch(`/api/events?ip=${ip}&limit=10&minutes=60`);
        const events = await eventsResponse.json();
        
        const eventsList = document.getElementById('profile-recent-events');
        eventsList.innerHTML = '';
        
        if (!events || events.length === 0) {
            eventsList.innerHTML = '<div class="loading">No recent events</div>';
        } else {
            events.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'profile-event-item';
                eventDiv.innerHTML = `
                    <strong>${event.type || 'Unknown'}</strong> on port ${event.port || '-'}
                    <br><span class="timestamp">${new Date(event.timestamp).toLocaleString()}</span>
                `;
                eventsList.appendChild(eventDiv);
            });
        }

        profileModal.style.display = 'flex';
    } catch (error) {
        console.error('Failed to load profile:', error);
        alert('Error loading IP profile');
    }
}

// Show action message
function showActionMessage(message, type) {
    const msgDiv = document.getElementById('action-message');
    msgDiv.textContent = message;
    msgDiv.className = `action-message ${type}`;
    msgDiv.style.display = 'block';
    setTimeout(() => {
        msgDiv.style.display = 'none';
    }, 3000);
}

// ============================================================================
// ADVANCED SEARCH & FILTERING
// ============================================================================

// Load countries for search dropdown
async function loadSearchCountries() {
    try {
        const response = await fetch('/api/search/countries');
        const data = await response.json();
        
        const dropdown = document.getElementById('search-country');
        if (dropdown && data.countries) {
            data.countries.forEach(country => {
                const option = document.createElement('option');
                option.value = country;
                option.textContent = country;
                dropdown.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load countries:', error);
    }
}

// Perform advanced search
async function performAdvancedSearch() {
    try {
        const ip = document.getElementById('search-ip')?.value?.trim() || '';
        const protocol = document.getElementById('search-protocol')?.value?.trim() || '';
        const country = document.getElementById('search-country')?.value?.trim() || '';
        const hours = document.getElementById('search-hours')?.value || '24';
        
        // Build query parameters
        const params = new URLSearchParams();
        if (ip) params.append('ip', ip);
        if (protocol) params.append('protocol', protocol);
        if (country) params.append('country', country);
        params.append('hours', hours);
        params.append('limit', 1000);
        
        // Fetch search results
        const response = await fetch(`/api/search/advanced?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display results
        displaySearchResults(data);
        
    } catch (error) {
        console.error('Search error:', error);
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = `<div style="padding: 20px; color: #d32f2f;">Error: ${error.message}</div>`;
        }
    }
}

// Display search results in table
function displaySearchResults(data) {
    const resultsDiv = document.getElementById('search-results');
    if (!resultsDiv) return;
    
    const events = data.events || [];
    
    if (events.length === 0) {
        resultsDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No results found</div>';
        return;
    }
    
    let html = `<div class="search-results-count">Found ${data.returned}/${data.total} events</div>`;
    html += `<table class="search-results-table">
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Source IP</th>
                <th>Country</th>
                <th>Port</th>
                <th>Protocol</th>
                <th>Payload Size</th>
                <th>Type</th>
            </tr>
        </thead>
        <tbody>`;
    
    events.forEach(event => {
        const timestamp = new Date(event.timestamp * 1000).toLocaleString();
        const country = event.geolocation?.country || 'Unknown';
        html += `<tr>
            <td>${timestamp}</td>
            <td><code>${event.source_ip}</code></td>
            <td>${country}</td>
            <td>${event.port}</td>
            <td>${event.protocol}</td>
            <td>${event.payload_size} B</td>
            <td>${event.event_type}</td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    resultsDiv.innerHTML = html;
}

// Export search results as CSV
async function exportSearchResults() {
    try {
        const ip = document.getElementById('search-ip')?.value?.trim() || '';
        const protocol = document.getElementById('search-protocol')?.value?.trim() || '';
        const country = document.getElementById('search-country')?.value?.trim() || '';
        const hours = document.getElementById('search-hours')?.value || '24';
        
        // Build query parameters
        const params = new URLSearchParams();
        if (ip) params.append('ip', ip);
        if (protocol) params.append('protocol', protocol);
        if (country) params.append('country', country);
        params.append('hours', hours);
        
        // Download CSV
        window.location.href = `/api/search/export?${params}`;
        
    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting results');
    }
}

// Reset search form
function resetSearchForm() {
    document.getElementById('search-ip').value = '';
    document.getElementById('search-date-from').value = '';
    document.getElementById('search-date-to').value = '';
    document.getElementById('search-protocol').value = '';
    document.getElementById('search-country').value = '';
    document.getElementById('search-hours').value = '24';
    
    const resultsDiv = document.getElementById('search-results');
    if (resultsDiv) {
        resultsDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">Click "Search" to find attacks by IP, date, country, or protocol</div>';
    }
}

// Initialize search event listeners
function initSearchListeners() {
    const searchBtn = document.getElementById('search-btn');
    const resetBtn = document.getElementById('search-reset-btn');
    const exportBtn = document.getElementById('search-export-btn');
    
    if (searchBtn) searchBtn.addEventListener('click', performAdvancedSearch);
    if (resetBtn) resetBtn.addEventListener('click', resetSearchForm);
    if (exportBtn) exportBtn.addEventListener('click', exportSearchResults);
    
    // Allow Enter key to trigger search
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performAdvancedSearch();
        });
    });
    
    // Load countries on page load
    loadSearchCountries();
    
    // Initialize alert rules
    initAlertRules();
}

// ========================
// ALERT RULES FUNCTIONS
// ========================

function initAlertRules() {
    // Initialize alert rules UI and event listeners
    loadAlertRules();
    
    // Event listeners for rule management
    document.getElementById('new-rule-btn')?.addEventListener('click', showRuleForm);
    document.getElementById('cancel-rule-btn')?.addEventListener('click', hideRuleForm);
    document.getElementById('save-rule-btn')?.addEventListener('click', saveNewRule);
    document.getElementById('refresh-rules-btn')?.addEventListener('click', loadAlertRules);
}

async function loadAlertRules() {
    // Load and display all alert rules
    try {
        const response = await fetch('/api/alerts/rules');
        if (!response.ok) throw new Error('Failed to load rules');
        
        const data = await response.json();
        displayAlertRules(data.rules);
    } catch (error) {
        console.error('Error loading alert rules:', error);
        document.getElementById('rules-list').innerHTML = 
            `<div class="no-rules-message"><p>Error loading rules</p></div>`;
    }
}

function displayAlertRules(rules) {
    // Display alert rules as a professional table
    const rulesContainer = document.getElementById('rules-list');
    
    if (!rules || rules.length === 0) {
        rulesContainer.innerHTML = `
            <div class="no-rules-message">
                <p>📋 No alert rules created yet</p>
                <p style="font-size: 12px; color: #555;">Click "New Alert Rule" to create your first alert</p>
            </div>
        `;
        return;
    }
    
    rulesContainer.innerHTML = `
        <div class="rules-table-container">
            <table class="rules-table">
                <thead>
                    <tr>
                        <th>Rule Name</th>
                        <th>Status</th>
                        <th>Condition</th>
                        <th>Action</th>
                        <th>Threshold</th>
                        <th>Time Window</th>
                        <th>Last Triggered</th>
                        <th>Triggers</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${rules.map(rule => `
                        <tr class="rule-row ${!rule.enabled ? 'disabled' : ''}">
                            <td class="rule-name-cell">
                                <span class="rule-icon">🚨</span>
                                <strong>${rule.name}</strong>
                                ${rule.description ? `<br><small style="color: #a0a0a0;">${escapeHtml(rule.description)}</small>` : ''}
                            </td>
                            <td class="rule-status-cell">
                                <span class="status-badge ${rule.enabled ? 'enabled' : 'disabled'}">
                                    ${rule.enabled ? '✓ Enabled' : '✗ Disabled'}
                                </span>
                            </td>
                            <td class="rule-condition-cell">
                                <code>${rule.condition_field} ${rule.condition_operator} ${rule.condition_value}</code>
                            </td>
                            <td class="rule-action-cell">
                                ${rule.action.toUpperCase()}
                            </td>
                            <td class="rule-threshold-cell">
                                ${rule.threshold}
                            </td>
                            <td class="rule-timewindow-cell">
                                ${rule.time_window_minutes}m
                            </td>
                            <td class="rule-triggered-cell">
                                ${rule.last_triggered ? formatTimeAgo(new Date(rule.last_triggered * 1000)) : 'Never'}
                            </td>
                            <td class="rule-count-cell">
                                <strong>${rule.trigger_count || 0}</strong>
                            </td>
                            <td class="rule-actions-cell">
                                <button class="rule-action-btn test" onclick="testRule(${rule.id})" title="Test Rule">Test</button>
                                <button class="rule-action-btn edit" onclick="editRule(${rule.id})" title="Edit Rule">Edit</button>
                                <button class="rule-action-btn toggle" onclick="toggleRule(${rule.id}, ${rule.enabled})" title="${rule.enabled ? 'Disable' : 'Enable'} Rule">
                                    ${rule.enabled ? 'Disable' : 'Enable'}
                                </button>
                                <button class="rule-action-btn delete" onclick="deleteRule(${rule.id})" title="Delete Rule">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function showRuleForm() {
    // Show the rule creation form
    document.getElementById('rule-form-container').style.display = 'block';
    document.getElementById('rule-name').focus();
    
    // Reset form
    document.getElementById('rule-name').value = '';
    document.getElementById('rule-description').value = '';
}

function hideRuleForm() {
    // Hide the rule creation form
    document.getElementById('rule-form-container').style.display = 'none';
}

async function saveNewRule() {
    // Save new alert rule
    const name = document.getElementById('rule-name').value.trim();
    const description = document.getElementById('rule-description').value.trim();
    const conditionType = document.getElementById('rule-condition-type').value;
    const conditionField = document.getElementById('rule-condition-field').value;
    const conditionOperator = document.getElementById('rule-condition-operator').value;
    const conditionValue = document.getElementById('rule-condition-value').value.trim();
    const action = document.getElementById('rule-action').value;
    const actionTarget = document.getElementById('rule-action-target').value.trim();
    const threshold = parseInt(document.getElementById('rule-threshold').value) || 1;
    const timeWindow = parseInt(document.getElementById('rule-time-window').value) || 1;
    
    // Validation
    if (!name) {
        alert('Please enter a rule name');
        return;
    }
    if (!conditionValue) {
        alert('Please enter a condition value');
        return;
    }
    
    try {
        const response = await fetch('/api/alerts/rules', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name,
                description,
                condition_type: conditionType,
                condition_field: conditionField,
                condition_operator: conditionOperator,
                condition_value: conditionValue,
                action,
                action_target: actionTarget,
                threshold,
                time_window_minutes: timeWindow
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Alert rule created: ' + data.message);
            hideRuleForm();
            loadAlertRules();
        } else {
            alert('❌ Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error saving rule:', error);
        alert('Failed to save rule: ' + error.message);
    }
}

async function testRule(ruleId) {
    // Test an alert rule
    try {
        // Get the most recent event for testing
        const statsResp = await fetch('/api/stats');
        const statsData = await statsResp.json();
        
        const recentResp = await fetch('/api/recent-events?limit=1');
        const recentData = await recentResp.json();
        
        const testEvent = recentData.events?.[0] || {
            source_ip: '192.168.1.100',
            protocol: 'SSH',
            port: 22,
            payload_size: 100
        };
        
        const response = await fetch(`/api/alerts/rules/${ruleId}/test`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ test_event: testEvent })
        });
        
        const data = await response.json();
        
        if (data.matched) {
            alert(`✅ Test PASSED\n\nThe rule matched the test event:\n${JSON.stringify(testEvent, null, 2)}`);
        } else {
            alert(`⚠️ Test FAILED\n\nThe rule did not match the test event:\n${JSON.stringify(testEvent, null, 2)}`);
        }
    } catch (error) {
        console.error('Error testing rule:', error);
        alert('Failed to test rule: ' + error.message);
    }
}

async function editRule(ruleId) {
    // Edit an existing alert rule
    alert('Edit feature coming soon - Feature #3');
}

async function toggleRule(ruleId, currentlyEnabled) {
    // Enable or disable a rule
    try {
        const response = await fetch(`/api/alerts/rules/${ruleId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                enabled: !currentlyEnabled
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            loadAlertRules();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error toggling rule:', error);
        alert('Failed to toggle rule: ' + error.message);
    }
}

async function deleteRule(ruleId) {
    // Delete a rule
    if (!confirm('Are you sure you want to delete this alert rule?')) return;
    
    try {
        const response = await fetch(`/api/alerts/rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            loadAlertRules();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting rule:', error);
        alert('Failed to delete rule: ' + error.message);
    }
}

function escapeHtml(text) {
    // Escape HTML special characters
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ========================
// ATTACK PATTERN REPORTS
// ========================

function initReports() {
    // Initialize reports functionality
    document.getElementById('generate-report-btn')?.addEventListener('click', generateReport);
    document.getElementById('export-report-json')?.addEventListener('click', () => exportReport('json'));
    document.getElementById('export-report-csv')?.addEventListener('click', () => exportReport('csv'));
}

async function generateReport() {
    // Generate attack pattern report
    try {
        const reportType = document.getElementById('report-type').value;
        const timePeriod = document.getElementById('report-time-period').value;
        
        const container = document.getElementById('report-container');
        container.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading-spinner"></div><p>Generating report...</p></div>';
        
        let response;
        
        if (reportType === 'patterns') {
            response = await fetch(`/api/reports/patterns?hours=${timePeriod}`);
        } else if (reportType === 'statistics') {
            response = await fetch(`/api/reports/statistics?hours=${timePeriod}`);
        } else if (reportType === 'daily') {
            response = await fetch(`/api/reports/daily?days=7`);
        } else if (reportType === 'timeline') {
            response = await fetch(`/api/reports/timeline?hours=${timePeriod}&bucket_minutes=60`);
        }
        
        if (!response.ok) throw new Error('Failed to generate report');
        
        const data = await response.json();
        
        if (reportType === 'patterns') {
            displayPatternsReport(data.data);
        } else if (reportType === 'statistics') {
            displayStatisticsReport(data);
        } else if (reportType === 'daily') {
            displayDailyReport(data);
        } else if (reportType === 'timeline') {
            displayTimelineReport(data.timeline);
        }
        
    } catch (error) {
        console.error('Error generating report:', error);
        document.getElementById('report-container').innerHTML = 
            `<div class="report-error">❌ Error generating report: ${error.message}</div>`;
    }
}

function displayPatternsReport(data) {
    // Display attack patterns report
    const container = document.getElementById('report-container');
    
    let protocolRows = '';
    for (const [protocol, count] of Object.entries(data.protocols)) {
        protocolRows += `<tr><td>${protocol}</td><td>${count}</td><td>${((count/data.total_events)*100).toFixed(1)}%</td></tr>`;
    }
    
    let portRows = '';
    for (const [port, count] of data.top_ports.slice(0, 10)) {
        portRows += `<tr><td>${port}</td><td>${count}</td></tr>`;
    }
    
    container.innerHTML = `
        <div class="report-section">
            <h3 class="report-title">🎯 Attack Pattern Overview</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <div class="summary-label">Total Events</div>
                    <div class="summary-value">${data.total_events}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Unique IPs</div>
                    <div class="summary-value">${data.unique_ips}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Avg Payload</div>
                    <div class="summary-value">${data.payload_avg}B</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Max Payload</div>
                    <div class="summary-value">${data.payload_max}B</div>
                </div>
            </div>
        </div>
        
        <div class="report-section">
            <h3 class="report-title">📊 Protocol Distribution</h3>
            <table class="report-table">
                <thead>
                    <tr><th>Protocol</th><th>Events</th><th>Percentage</th></tr>
                </thead>
                <tbody>
                    ${protocolRows}
                </tbody>
            </table>
        </div>
        
        <div class="report-section">
            <h3 class="report-title">🔌 Top Ports Attacked</h3>
            <table class="report-table">
                <thead>
                    <tr><th>Port</th><th>Attack Count</th></tr>
                </thead>
                <tbody>
                    ${portRows}
                </tbody>
            </table>
        </div>
    `;
}

function displayStatisticsReport(data) {
    // Display detailed statistics report
    const container = document.getElementById('report-container');
    
    let topIpRows = '';
    for (const ip of data.top_ips.slice(0, 15)) {
        const firstAttack = new Date(ip.first_attack * 1000).toLocaleString();
        const lastAttack = new Date(ip.last_attack * 1000).toLocaleString();
        topIpRows += `
            <tr>
                <td>${ip.source_ip}</td>
                <td>${ip.attack_count}</td>
                <td>${ip.protocols_used}</td>
                <td>${ip.ports_hit}</td>
                <td>${ip.avg_payload.toFixed(0)}B</td>
                <td>${firstAttack}</td>
            </tr>
        `;
    }
    
    let protocolRows = '';
    for (const prot of data.protocols) {
        protocolRows += `
            <tr>
                <td>${prot.protocol}</td>
                <td>${prot.event_count}</td>
                <td>${prot.unique_ips}</td>
                <td>${prot.avg_payload.toFixed(0)}B</td>
                <td>${prot.ports_used}</td>
            </tr>
        `;
    }
    
    container.innerHTML = `
        <div class="report-section">
            <h3 class="report-title">📈 Overview</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <div class="summary-label">Total Events</div>
                    <div class="summary-value">${data.summary.total_events}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Unique Attackers</div>
                    <div class="summary-value">${data.summary.unique_ips}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Protocols</div>
                    <div class="summary-value">${Object.keys(data.summary.protocols).length}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Top Ports Hit</div>
                    <div class="summary-value">${data.summary.top_ports.length}</div>
                </div>
            </div>
        </div>
        
        <div class="report-section">
            <h3 class="report-title">🔴 Top Attacking IPs</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Source IP</th>
                        <th>Attacks</th>
                        <th>Protocols</th>
                        <th>Ports</th>
                        <th>Avg Payload</th>
                        <th>First Attack</th>
                    </tr>
                </thead>
                <tbody>${topIpRows}</tbody>
            </table>
        </div>
        
        <div class="report-section">
            <h3 class="report-title">📊 Protocol Analysis</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Protocol</th>
                        <th>Events</th>
                        <th>Unique IPs</th>
                        <th>Avg Payload</th>
                        <th>Ports Used</th>
                    </tr>
                </thead>
                <tbody>${protocolRows}</tbody>
            </table>
        </div>
    `;
}

function displayDailyReport(data) {
    // Display daily summary report
    const container = document.getElementById('report-container');
    
    let dailyRows = '';
    for (const day of data.daily) {
        dailyRows += `
            <tr>
                <td>${day.day}</td>
                <td>${day.event_count}</td>
                <td>${day.unique_ips}</td>
                <td>${day.avg_payload ? day.avg_payload.toFixed(0) : 0}B</td>
            </tr>
        `;
    }
    
    let protocolRows = '';
    for (const prot of data.protocols) {
        protocolRows += `<li class="report-list-item"><span class="list-item-label">${prot.protocol}</span><span class="list-item-value">${prot.event_count} events</span></li>`;
    }
    
    container.innerHTML = `
        <div class="report-section">
            <h3 class="report-title">📅 Daily Summary (Last 7 Days)</h3>
            <table class="report-table">
                <thead>
                    <tr><th>Date</th><th>Events</th><th>Unique IPs</th><th>Avg Payload</th></tr>
                </thead>
                <tbody>${dailyRows}</tbody>
            </table>
        </div>
        
        <div class="report-section">
            <h3 class="report-title">🔀 Protocol Distribution</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                ${protocolRows}
            </ul>
        </div>
    `;
}

function displayTimelineReport(timeline) {
    // Display timeline report
    const container = document.getElementById('report-container');
    
    let timelineRows = '';
    for (const point of timeline.slice(-24)) {  // Show last 24 buckets
        timelineRows += `
            <tr>
                <td>${point.bucket}</td>
                <td>${point.event_count}</td>
                <td>${point.unique_ips}</td>
            </tr>
        `;
    }
    
    container.innerHTML = `
        <div class="report-section">
            <h3 class="report-title">📈 Attack Timeline</h3>
            <table class="report-table">
                <thead>
                    <tr><th>Time Bucket</th><th>Events</th><th>Unique IPs</th></tr>
                </thead>
                <tbody>${timelineRows}</tbody>
            </table>
        </div>
        
        <div style="text-align: center; padding: 15px; color: #999; font-size: 12px;">
            Showing last ${timeline.length} hourly buckets
        </div>
    `;
}

async function exportReport(format) {
    // Export current report
    try {
        const reportType = document.getElementById('report-type').value;
        const timePeriod = document.getElementById('report-time-period').value;
        
        const response = await fetch(`/api/reports/export?type=${reportType}&format=${format}&hours=${timePeriod}`);
        
        if (!response.ok) throw new Error('Export failed');
        
        if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            downloadBlob(blob, `report_${reportType}.json`);
        } else if (format === 'csv') {
            const blob = await response.blob();
            downloadBlob(blob, `report_${reportType}.csv`);
        }
        
    } catch (error) {
        console.error('Error exporting report:', error);
        alert('Failed to export report: ' + error.message);
    }
}

function downloadBlob(blob, filename) {
    // Download blob as file
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
}


// ========================
// REAL-TIME LOG VIEWER
// ========================

const liveLogState = {
    events: [],
    isPlaying: true,
    updateInterval: 1000, // Real-time updates (1 second)
    lastTimestamp: null,
    filteredEvents: [],
    maxEventsDisplay: 100,
    uniqueIps: new Set(),
    protocolsSet: new Set(),
    streamStartTime: Date.now()
};

function initLiveLogs() {
    // Initialize real-time log viewer
    console.log('Initializing live log viewer...');
    
    // Load initial filters
    loadLiveLogFilters();
    
    // Setup event listeners
    document.getElementById('live-pause-btn').addEventListener('click', toggleLivePause);
    document.getElementById('live-clear-btn').addEventListener('click', clearLiveLogs);
    
    document.getElementById('live-filter-protocol').addEventListener('change', applyLiveFilters);
    document.getElementById('live-filter-port').addEventListener('change', applyLiveFilters);
    document.getElementById('live-filter-ip').addEventListener('change', applyLiveFilters);
    
    // Start polling for events
    pollLiveEvents();
    setInterval(pollLiveEvents, liveLogState.updateInterval);
}

async function loadLiveLogFilters() {
    // Load available filters for the live log viewer
    try {
        const response = await fetch('/api/logs/filters');
        const data = await response.json();
        
        if (data.success) {
            // Populate protocol dropdown
            const protocolSelect = document.getElementById('live-filter-protocol');
            data.protocols.forEach(protocol => {
                const option = document.createElement('option');
                option.value = protocol;
                option.textContent = protocol;
                protocolSelect.appendChild(option);
            });
            
            // Populate port dropdown
            const portSelect = document.getElementById('live-filter-port');
            data.ports.forEach(port => {
                const option = document.createElement('option');
                option.value = port;
                option.textContent = port;
                portSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading live log filters:', error);
    }
}

async function pollLiveEvents() {
    // Poll for new events from the server
    if (!liveLogState.isPlaying) return;
    
    try {
        const since = liveLogState.lastTimestamp || (Date.now() / 1000 - 2592000); // 30 days
        const response = await fetch(`/api/logs/stream?since=${since}&limit=50`);
        
        if (!response.ok) return;
        
        const data = await response.json();
        
        if (data.success && data.events && data.events.length > 0) {
            // Add new events to the beginning (reverse chronological)
            liveLogState.events = [...data.events, ...liveLogState.events];
            
            // Keep only recent events
            if (liveLogState.events.length > liveLogState.maxEventsDisplay * 2) {
                liveLogState.events = liveLogState.events.slice(0, liveLogState.maxEventsDisplay * 2);
            }
            
            // Track unique IPs and protocols
            data.events.forEach(event => {
                liveLogState.uniqueIps.add(event.source_ip);
                liveLogState.protocolsSet.add(event.protocol);
            });
            
            // Update latest timestamp
            if (data.latest_timestamp) {
                liveLogState.lastTimestamp = data.latest_timestamp;
            }
            
            // Apply filters and render
            applyLiveFilters();
        }
    } catch (error) {
        console.error('Error polling live events:', error);
    }
}

function applyLiveFilters() {
    // Apply filters to live events
    const protocolFilter = document.getElementById('live-filter-protocol').value;
    const portFilter = document.getElementById('live-filter-port').value;
    const ipFilter = document.getElementById('live-filter-ip').value.toLowerCase();
    
    liveLogState.filteredEvents = liveLogState.events.filter(event => {
        if (protocolFilter && event.protocol !== protocolFilter) return false;
        if (portFilter && event.port != portFilter) return false;
        if (ipFilter && !event.source_ip.toLowerCase().includes(ipFilter)) return false;
        return true;
    });
    
    renderLiveLogs();
    updateLiveStats();
}

function renderLiveLogs() {
    // Render filtered events in the live logs container
    const logsBody = document.getElementById('live-logs-body');
    
    if (liveLogState.filteredEvents.length === 0) {
        logsBody.innerHTML = '<div class="live-log-entry placeholder">No events matching filters...</div>';
        return;
    }
    
    // Show only the most recent N events
    const displayEvents = liveLogState.filteredEvents.slice(0, liveLogState.maxEventsDisplay);
    
    logsBody.innerHTML = displayEvents.map(event => `
        <div class="live-log-entry">
            <div class="log-time">${new Date(event.timestamp_iso).toLocaleTimeString()}</div>
            <div class="log-ip">${event.source_ip}</div>
            <div class="log-port">${event.port}</div>
            <div class="log-protocol">${event.protocol}</div>
            <div class="log-size">${event.payload_size}B</div>
            <div class="log-type">${event.event_type}</div>
        </div>
    `).join('');
    
    // Auto-scroll to top (newest events)
    logsBody.scrollTop = 0;
}

function updateLiveStats() {
    // Update live statistics display
    const eventCount = liveLogState.filteredEvents.length;
    const uniqueIps = new Set(liveLogState.filteredEvents.map(e => e.source_ip)).size;
    const protocols = new Set(liveLogState.filteredEvents.map(e => e.protocol)).size;
    
    // Calculate events per minute
    const streamDuration = (Date.now() - liveLogState.streamStartTime) / 1000 / 60;
    const eventsPerMin = streamDuration > 0 ? Math.round(eventCount / streamDuration) : 0;
    
    document.getElementById('live-event-count').textContent = `${eventCount} events`;
    document.getElementById('live-events-per-min').textContent = eventsPerMin;
    document.getElementById('live-unique-ips').textContent = uniqueIps;
    document.getElementById('live-protocol-count').textContent = protocols;
}

function toggleLivePause() {
    // Toggle pause/play for live logs
    const btn = document.getElementById('live-pause-btn');
    liveLogState.isPlaying = !liveLogState.isPlaying;
    
    if (liveLogState.isPlaying) {
        btn.textContent = '⏸️ Pause';
        btn.classList.remove('paused');
        pollLiveEvents(); // Resume immediately
    } else {
        btn.textContent = '▶️ Resume';
        btn.classList.add('paused');
    }
}

function clearLiveLogs() {
    // Clear all live logs
    liveLogState.events = [];
    liveLogState.filteredEvents = [];
    liveLogState.lastTimestamp = null;
    liveLogState.uniqueIps.clear();
    liveLogState.protocolsSet.clear();
    liveLogState.streamStartTime = Date.now();
    
    renderLiveLogs();
    updateLiveStats();
}


// ========================
// ML ANOMALY DETECTION
// ========================

const anomalyState = {
    anomalies: [],
    baseline: null,
    sensitivity: 2.0,
    hours: 720,  // 30 days
    lastScan: null
};

function initAnomalyDetection() {
    // Initialize anomaly detection system
    console.log('Initializing ML anomaly detection...');
    
    document.getElementById('anomaly-scan-btn').addEventListener('click', scanAnomalies);
    document.getElementById('anomaly-hours').addEventListener('change', (e) => {
        anomalyState.hours = parseInt(e.target.value);
    });
    document.getElementById('anomaly-sensitivity').addEventListener('change', (e) => {
        anomalyState.sensitivity = parseFloat(e.target.value);
    });
}

async function scanAnomalies() {
    // Scan for anomalies using ML-based detection
    try {
        const scanBtn = document.getElementById('anomaly-scan-btn');
        scanBtn.disabled = true;
        scanBtn.textContent = '🔄 Scanning...';
        
        const response = await fetch(
            `/api/anomalies/detect?hours=${anomalyState.hours}&sensitivity=${anomalyState.sensitivity}`
        );
        
        if (!response.ok) throw new Error('Scan failed');
        
        const data = await response.json();
        anomalyState.anomalies = data.anomalies || [];
        anomalyState.baseline = data.baseline;
        anomalyState.lastScan = new Date();
        
        // Get summary
        await updateAnomalySummary();
        
        // Display anomalies
        displayAnomalies();
        
        scanBtn.disabled = false;
        scanBtn.textContent = '🔍 Scan for Anomalies';
        
    } catch (error) {
        console.error('Error scanning anomalies:', error);
        document.getElementById('anomaly-scan-btn').disabled = false;
        document.getElementById('anomaly-scan-btn').textContent = '🔍 Scan for Anomalies';
        alert('Failed to scan for anomalies: ' + error.message);
    }
}

async function updateAnomalySummary() {
    // Fetch and display anomaly summary
    try {
        const response = await fetch(`/api/anomalies/summary?hours=${anomalyState.hours}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('anomaly-count').textContent = data.total_anomalies;
            document.getElementById('anomaly-severity').textContent = data.severity.toUpperCase();
            document.getElementById('anomaly-type-count').textContent = Object.keys(data.anomaly_types).length;
            document.getElementById('anomaly-suspicious-ips').textContent = data.top_anomalous_ips.length;
            
            // Display severity color
            const severityEl = document.getElementById('anomaly-severity');
            severityEl.classList.remove('low', 'medium', 'high');
            severityEl.classList.add(data.severity);
            
            // Display anomaly type breakdown
            displayAnomalyTypeBreakdown(data.anomaly_types);
        }
    } catch (error) {
        console.error('Error updating anomaly summary:', error);
    }
}

function displayAnomalies() {
    // Display detected anomalies in table
    const tbody = document.getElementById('anomaly-tbody');
    
    if (anomalyState.anomalies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No anomalies detected</td></tr>';
        return;
    }
    
    tbody.innerHTML = anomalyState.anomalies.slice(0, 50).map(anomaly => {
        const score = anomaly.anomaly_score || 0;
        let scoreClass = score > 7 ? 'high' : score > 4 ? 'medium' : 'low';
        
        let details = '';
        if (anomaly.anomaly_type === 'unusual_payload') {
            details = `Payload: ${anomaly.payload_size}B (unusual)`;
        } else if (anomaly.anomaly_type === 'high_frequency_attack') {
            details = `${anomaly.event_count} events @ ${anomaly.events_per_minute.toFixed(1)}/min`;
        }
        
        return `
            <tr>
                <td><span class="anomaly-score ${scoreClass}">${score.toFixed(1)}</span></td>
                <td><span class="anomaly-type">${anomaly.anomaly_type}</span></td>
                <td>${anomaly.source_ip || 'N/A'}</td>
                <td>${details}</td>
                <td>
                    ${anomaly.source_ip ? 
                        `<button class="action-btn secondary" onclick="getIPProfile('${anomaly.source_ip}')">Profile</button>` 
                        : '-'}
                </td>
            </tr>
        `;
    }).join('');
}

function displayAnomalyTypeBreakdown(types) {
    // Display breakdown of anomaly types
    const container = document.getElementById('anomaly-type-breakdown');
    
    if (Object.keys(types).length === 0) {
        container.innerHTML = '<div class="loading">No anomaly types detected</div>';
        return;
    }
    
    container.innerHTML = Object.entries(types).map(([type, count]) => `
        <div class="type-item">
            <div class="type-item-label">${type.replace(/_/g, ' ')}</div>
            <div class="type-item-count">${count}</div>
        </div>
    `).join('');
}

async function getIPProfile(sourceIp) {
    // Get detailed profile for an IP address
    try {
        const hours = anomalyState.hours || 720;
        const response = await fetch(`/api/anomalies/profile/${sourceIp}?hours=${hours}`);
        const data = await response.json();
        
        if (data.success && data.profile) {
            const profile = data.profile;
            const details = `
IP: ${profile.source_ip}
Events: ${profile.event_count}
Protocols: ${profile.protocol_count}
Ports: ${profile.port_count}
Avg Payload: ${profile.avg_payload.toFixed(0)}B
Duration: ${profile.duration_seconds.toFixed(0)}s
Rate: ${profile.events_per_minute.toFixed(1)}/min
Anomalous: ${profile.is_anomalous ? 'YES ⚠️' : 'No'}
            `;
            alert(details);
        } else {
            alert('No profile data found for this IP');
        }
    } catch (error) {
        console.error('Error fetching IP profile:', error);
        alert('Failed to fetch IP profile: ' + error.message);
    }
}

// Expose to global scope for inline onclick handlers
window.getIPProfile = getIPProfile;


// ========================
// GEOGRAPHIC HEAT MAP
// ========================

const geoState = {
    map: null,
    markers: {},
    selectedCountry: null,
    heatmapLayer: null,
    hours: 24
};

function initGeoHeatMap() {
    // Initialize geographic heat map
    console.log('Initializing geographic heat map...');
    
    // Initialize map if not already done
    const mapElement = document.getElementById('map');
    if (!geoState.map && mapElement && !mapElement._leaflet_id) {
        geoState.map = L.map('map').setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(geoState.map);
    }
    
    // Setup controls
    document.getElementById('geo-time-period').addEventListener('change', (e) => {
        geoState.hours = parseInt(e.target.value);
        loadGeoData();
    });
    
    document.getElementById('geo-load-btn').addEventListener('click', loadGeoData);
    document.getElementById('geo-clear-btn').addEventListener('click', clearGeoData);
    
    // Load initial data
    loadGeoData();
}

async function loadGeoData() {
    // Load geographic data and update map
    try {
        const btn = document.getElementById('geo-load-btn');
        btn.disabled = true;
        btn.textContent = '🔄 Loading...';
        
        // Load heatmap data
        const response = await fetch(`/api/geo/heatmap?hours=${geoState.hours}`);
        const data = await response.json();
        
        if (data.success) {
            // Clear old markers
            clearGeoData();
            
            // Add markers and data points
            data.heatmap.forEach(point => {
                // Add circle marker
                const radius = Math.sqrt(point.intensity) * 50000;
                const circle = L.circle([point.lat, point.lng], {
                    color: getIntensityColor(point.intensity),
                    fillColor: getIntensityColor(point.intensity),
                    fillOpacity: point.intensity * 0.7,
                    radius: radius,
                    weight: 2
                }).addTo(geoState.map);
                
                circle.bindPopup(`
                    <strong>${point.country}</strong><br>
                    Events: ${point.events}<br>
                    Intensity: ${(point.intensity * 100).toFixed(1)}%
                `);
                
                geoState.markers[`${point.lat}-${point.lng}`] = circle;
            });
            
            // Load country statistics
            await loadCountryStats();
            
            btn.disabled = false;
            btn.textContent = '🌍 Load Locations';
        }
    } catch (error) {
        console.error('Error loading geographic data:', error);
        document.getElementById('geo-load-btn').disabled = false;
        document.getElementById('geo-load-btn').textContent = '🌍 Load Locations';
    }
}

async function loadCountryStats() {
    // Load and display country statistics
    try {
        const response = await fetch(`/api/geo/countries?hours=${geoState.hours}`);
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('country-stats');
            
            if (data.countries.length === 0) {
                container.innerHTML = '<div class="loading">No geographic data available</div>';
                return;
            }
            
            container.innerHTML = data.countries.slice(0, 20).map((country, idx) => `
                <div class="country-stat-row" onclick="showCountryDetails('${country.country}')">
                    <span class="rank">${idx + 1}</span>
                    <span class="country-name">${country.country}</span>
                    <span class="stat-value">${country.event_count} events</span>
                    <span class="stat-value">${country.unique_ips} IPs</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading country stats:', error);
    }
}

async function showCountryDetails(country) {
    // Show details for a specific country
    try {
        const response = await fetch(`/api/geo/country/${encodeURIComponent(country)}?hours=${geoState.hours}`);
        const data = await response.json();
        
        if (data.success) {
            const detailsModal = document.createElement('div');
            detailsModal.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #1a1a2e;
                color: #fff;
                padding: 20px;
                border-radius: 8px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                border: 2px solid #4db8ff;
                z-index: 10000;
            `;
            
            detailsModal.innerHTML = `
                <button onclick="this.parentElement.remove()" style="float:right; background: #d946a6; border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer;">✕</button>
                <h2>${country}</h2>
                <div style="margin: 15px 0;">
                    <p><strong>Total Events:</strong> ${data.total_events}</p>
                    <p><strong>Unique IPs:</strong> ${data.total_ips}</p>
                </div>
                <h3>Top Attacking IPs:</h3>
                <div style="max-height: 400px; overflow-y: auto;">
                    ${data.ips.map(ip => `
                        <div style="padding: 8px; border-bottom: 1px solid #333; font-size: 12px;">
                            <strong>${ip.source_ip}</strong> - ${ip.event_count} events<br>
                            ${ip.city}, ${ip.region} (${ip.isp})
                        </div>
                    `).join('')}
                </div>
            `;
            
            document.body.appendChild(detailsModal);
            
            // Close modal when clicking outside
            detailsModal.addEventListener('click', (e) => {
                if (e.target === detailsModal) detailsModal.remove();
            });
        }
    } catch (error) {
        console.error('Error showing country details:', error);
        alert('Failed to load country details');
    }
}

function getIntensityColor(intensity) {
    // Get color based on intensity
    if (intensity > 0.8) return '#d32f2f';  // Red
    if (intensity > 0.6) return '#f57c00';  // Orange
    if (intensity > 0.4) return '#fbc02d';  // Yellow
    if (intensity > 0.2) return '#689f38';  // Light green
    return '#4caf50';  // Green
}

function clearGeoData() {
    // Clear geographic data from map
    Object.values(geoState.markers).forEach(marker => {
        if (geoState.map && marker.remove) {
            marker.remove();
        }
    });
    geoState.markers = {};
}

// ========== THREAT INTELLIGENCE FUNCTIONS ==========

function initThreatIntel() {
    console.log('Initializing Threat Intelligence module');
    
    const scanBtn = document.getElementById('threat-scan-btn');
    const highRiskBtn = document.getElementById('threat-high-risk-btn');
    
    if (scanBtn) {
        scanBtn.addEventListener('click', scanThreats);
    }
    
    if (highRiskBtn) {
        highRiskBtn.addEventListener('click', loadHighRiskIPs);
    }
}

async function scanThreats() {
    const scanBtn = document.getElementById('threat-scan-btn');
    const threshold = parseFloat(document.getElementById('threat-threshold').value);
    
    if (!scanBtn) return;
    
    scanBtn.disabled = true;
    scanBtn.textContent = '⏳ Scanning...';
    
    try {
        // Get threat summary
        const summaryRes = await fetch('/api/threat/summary');
        if (!summaryRes.ok) throw new Error('Failed to fetch threat summary');
        
        const summary = await summaryRes.json();
        
        // Update threat statistics
        const dist = summary.score_distribution || {};
        document.getElementById('threat-critical').textContent = dist.critical || 0;
        document.getElementById('threat-high').textContent = dist.high || 0;
        document.getElementById('threat-medium').textContent = dist.medium || 0;
        document.getElementById('threat-low').textContent = dist.low || 0;
        
        // Display threat distribution
        displayThreatDistribution(summary.threat_types || {});
        
        // Load high-risk IPs
        await loadHighRiskIPs();
        
        // Show message if no threats found
        if (summary.high_risk_count === 0) {
            const tbody = document.getElementById('threat-tbody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="5" class="loading">No high-risk threats detected. This is normal for honeypot data - threat scores are based on real-world threat intelligence databases.</td></tr>';
            }
        }
        
    } catch (error) {
        console.error('Error scanning threats:', error);
        alert('Failed to scan threats: ' + error.message);
    } finally {
        scanBtn.disabled = false;
        scanBtn.textContent = '🔍 Scan Threats';
    }
}

async function loadHighRiskIPs() {
    const threshold = parseFloat(document.getElementById('threat-threshold').value);
    const tbody = document.getElementById('threat-tbody');
    
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading high-risk IPs...</td></tr>';
    
    try {
        const response = await fetch(`/api/threat/high-risk?threshold=${threshold}&limit=50`);
        if (!response.ok) throw new Error('Failed to fetch high-risk IPs');
        
        const data = await response.json();
        const ips = data.high_risk_ips || [];
        
        if (ips.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No high-risk IPs found</td></tr>';
            return;
        }
        
        tbody.innerHTML = ips.map(ip => {
            const scoreClass = getSeverityClass(ip.risk_score);
            return `
                <tr>
                    <td><strong>${ip.source_ip}</strong></td>
                    <td>
                        <span class="risk-score ${scoreClass}">
                            ${ip.risk_score.toFixed(1)}/10
                        </span>
                    </td>
                    <td>${ip.threat_type || 'unknown'}</td>
                    <td>${ip.threat_description || 'N/A'}</td>
                    <td>
                        <button class="action-btn" onclick="blockIP('${ip.source_ip}')">Block</button>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading high-risk IPs:', error);
        tbody.innerHTML = `<tr><td colspan="5" class="loading">Error: ${error.message}</td></tr>`;
    }
}

function displayThreatDistribution(threatTypes) {
    const container = document.getElementById('threat-type-breakdown');
    if (!container) return;
    
    const total = Object.values(threatTypes).reduce((a, b) => a + b, 0) || 1;
    
    if (total === 0) {
        container.innerHTML = '<div class="loading">No threat data available</div>';
        return;
    }
    
    // Sort by count (descending)
    const sortedThreats = Object.entries(threatTypes).sort((a, b) => b[1] - a[1]);
    
    const tableRows = sortedThreats.map(([type, count]) => {
        const percentage = ((count / total) * 100).toFixed(1);
        const barWidth = Math.max(5, percentage);
        return `
            <tr>
                <td class="threat-name">${type}</td>
                <td class="threat-count">${count}</td>
                <td class="threat-percentage">
                    <div class="percentage-bar-container">
                        <div class="percentage-bar" style="width: ${barWidth}%"></div>
                        <span class="percentage-text">${percentage}%</span>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    container.innerHTML = `
        <table class="threat-table">
            <thead>
                <tr>
                    <th>Threat Type</th>
                    <th>Count</th>
                    <th>Distribution</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
}

function getSeverityClass(score) {
    if (score >= 9) return 'score-critical';
    if (score >= 7) return 'score-high';
    if (score >= 4) return 'score-medium';
    return 'score-low';
}

function blockIP(ip) {
    if (confirm(`Block IP ${ip}?`)) {
        console.log('Blocking IP:', ip);
        // This would integrate with automated response in Feature #8
        alert(`IP ${ip} has been added to block list (Feature #8 integration pending)`);
    }
}

// ========== AUTOMATED RESPONSE ACTIONS ==========

function initResponseActions() {
    console.log('Initializing Automated Response Actions module');
    
    const blockBtn = document.getElementById('response-block-btn');
    const webhookBtn = document.getElementById('response-webhook-btn');
    const refreshBtn = document.getElementById('response-refresh-btn');
    
    if (blockBtn) {
        blockBtn.addEventListener('click', showBlockIPDialog);
    }
    
    if (webhookBtn) {
        webhookBtn.addEventListener('click', showWebhookDialog);
    }
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshResponseData);
    }
    
    // Load initial data
    loadResponseSummary();
    loadBlockedIPs();
    loadActionLog();
}

async function refreshResponseData() {
    const refreshBtn = document.getElementById('response-refresh-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.textContent = '⏳ Loading...';
    }
    
    try {
        await loadResponseSummary();
        await loadBlockedIPs();
        await loadActionLog();
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.textContent = '🔄 Refresh';
        }
    }
}

async function loadResponseSummary() {
    try {
        const response = await fetch('/api/response/actions');
        if (!response.ok) throw new Error('Failed to fetch response actions');
        
        const data = await response.json();
        
        document.getElementById('response-blocked').textContent = data.blocked_ips_count || 0;
        document.getElementById('response-webhooks').textContent = data.active_webhooks || 0;
        document.getElementById('response-actions').textContent = 
            Object.values(data.action_counts || {}).reduce((a, b) => a + b, 0);
        
    } catch (error) {
        console.error('Error loading response summary:', error);
    }
}

async function loadBlockedIPs() {
    const tbody = document.getElementById('response-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading blocked IPs...</td></tr>';
    
    try {
        const response = await fetch('/api/response/blocked-ips?limit=50');
        if (!response.ok) throw new Error('Failed to fetch blocked IPs');
        
        const data = await response.json();
        const blockedIPs = data.blocked_ips || [];
        
        if (blockedIPs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No blocked IPs</td></tr>';
            return;
        }
        
        tbody.innerHTML = blockedIPs.map(ip => `
            <tr>
                <td><strong>${ip.ip}</strong></td>
                <td>${ip.reason || 'N/A'}</td>
                <td>${ip.threat_type || 'N/A'}</td>
                <td>${ip.risk_score ? ip.risk_score.toFixed(1) : 'N/A'}</td>
                <td>${new Date(ip.blocked_at).toLocaleString()}</td>
                <td>
                    <button class="action-btn-small view" onclick="openActionModal('${ip.ip}')">👁️ View</button>
                    <button class="action-btn-small whitelist" onclick="unblockIP('${ip.ip}')">✓ Unblock</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading blocked IPs:', error);
        tbody.innerHTML = `<tr><td colspan="6" class="loading">Error: ${error.message}</td></tr>`;
    }
}

async function loadActionLog() {
    const container = document.getElementById('action-history-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading action history...</div>';
    
    try {
        const response = await fetch('/api/response/action-log?limit=20');
        if (!response.ok) throw new Error('Failed to fetch action log');
        
        const data = await response.json();
        const actions = data.actions || [];
        
        if (actions.length === 0) {
            container.innerHTML = '<div class="loading">No recent actions</div>';
            return;
        }
        
        container.innerHTML = actions.map(action => `
            <div class="action-item ${action.status}">
                <div class="action-type">${formatActionType(action.action_type)}</div>
                <div class="action-detail">${action.action_details || action.source_ip || 'N/A'}</div>
                <div class="action-timestamp">${new Date(action.executed_at).toLocaleString()}</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading action log:', error);
        container.innerHTML = `<div class="loading">Error: ${error.message}</div>`;
    }
}

function formatActionType(type) {
    const typeMap = {
        'block_ip': '🚫 Block IP',
        'unblock_ip': '✅ Unblock IP',
        'webhook_trigger': '🔗 Webhook Triggered',
        'rate_limit_adjust': '⚡ Rate Limit Adjusted'
    };
    return typeMap[type] || type;
}

async function blockIP_Auto(ip, reason = 'Manual threat response', threatType = '', riskScore = 0) {
    try {
        const response = await fetch('/api/response/block-ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ip: ip,
                reason: reason,
                threat_type: threatType,
                risk_score: riskScore,
                permanent: true
            })
        });
        
        if (response.ok) {
            await refreshResponseData();
            alert(`IP ${ip} has been blocked`);
        } else {
            alert('Failed to block IP');
        }
    } catch (error) {
        console.error('Error blocking IP:', error);
        alert('Error blocking IP: ' + error.message);
    }
}

async function unblockIP(ip) {
    if (!confirm(`Unblock IP ${ip}?`)) return;
    
    try {
        const response = await fetch('/api/response/unblock-ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip: ip })
        });
        
        if (response.ok) {
            await refreshResponseData();
            alert(`IP ${ip} has been unblocked`);
        } else {
            alert('Failed to unblock IP');
        }
    } catch (error) {
        console.error('Error unblocking IP:', error);
        alert('Error unblocking IP: ' + error.message);
    }
}

function showBlockIPDialog() {
    const ip = prompt('Enter IP address to block:');
    if (!ip) return;
    
    const reason = prompt('Enter block reason (optional):') || 'Manual block';
    blockIP_Auto(ip, reason);
}

async function showWebhookDialog() {
    const url = prompt('Enter webhook URL:');
    if (!url) return;
    
    try {
        const response = await fetch('/api/response/webhook/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                event_type: 'all_threats'
            })
        });
        
        if (response.ok) {
            await loadResponseSummary();
            alert('Webhook added successfully');
        } else {
            alert('Failed to add webhook');
        }
    } catch (error) {
        console.error('Error adding webhook:', error);
        alert('Error adding webhook: ' + error.message);
    }
}

// ===== RATE LIMIT DASHBOARD =====
function initRateLimitDashboard() {
    console.log('Initializing rate limit dashboard...');
    
    // Setup refresh button
    const refreshBtn = document.getElementById('rate-limit-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadRateLimitStatus);
        console.log('✓ Rate limit refresh button setup');
    }
    
    // Load initial data
    loadRateLimitStatus();
    
    // Auto-refresh every 10 seconds
    setInterval(() => {
        if (!state.isRefreshPaused) {
            loadRateLimitStatus();
        }
    }, 10000);
}

async function loadRateLimitStatus() {
    try {
        const response = await fetch('/api/status/rate-limits');
        if (!response.ok) {
            console.error('Failed to load rate limit status:', response.status);
            return;
        }
        
        const jsonData = await response.json();
        const data = jsonData.rate_limits || jsonData;
        displayRateLimitData(data);
        updateLastUpdatedTimestamp();
    } catch (error) {
        console.error('Error loading rate limit status:', error);
    }
}

function displayRateLimitData(data) {
    console.log('Rate limit data:', data);
    
    // Update usage bar
    displayUsageBar(data);
    
    // Update status cards
    displayStatusCards(data);
    
    // Update configuration card
    displayConfigurationCard(data);
    
    // Update blacklist table
    displayBlacklistedIPs(data);
    
    // Update top IPs table
    displayTopIPs(data);
}

function displayUsageBar(data) {
    const usagePercent = data.usage_percentage || 0;
    const fillBar = document.getElementById('usage-bar-fill');
    const statsText = document.getElementById('usage-stats-text');
    
    if (fillBar) {
        fillBar.style.width = Math.min(usagePercent, 100) + '%';
        fillBar.textContent = usagePercent.toFixed(1) + '%';
    }
    
    if (statsText) {
        const requests = data.current_usage || 0;
        const limit = data.limit || 300;
        statsText.textContent = `${requests} / ${limit} requests`;
    }
    
    const windowEl = document.getElementById('usage-window-text');
    if (windowEl) {
        const window_sec = data.window_seconds || 60;
        windowEl.textContent = `Reset in ${window_sec} seconds`;
    }
}

function displayStatusCards(data) {
    // Current IP
    const currentIPEl = document.getElementById('status-current-ip');
    if (currentIPEl) {
        currentIPEl.textContent = data.current_ip || 'Unknown';
    }
    
    // Whitelist status
    const whitelistEl = document.getElementById('status-whitelist');
    if (whitelistEl) {
        const isWhitelisted = data.is_whitelisted || false;
        whitelistEl.textContent = isWhitelisted ? 'Whitelisted' : 'Normal';
        whitelistEl.className = 'status-badge' + (isWhitelisted ? ' whitelisted' : '');
    }
    
    // Blacklist status for current IP
    const isCurrentBlacklisted = document.getElementById('status-current-blacklisted');
    if (isCurrentBlacklisted) {
        const isBlacklisted = data.is_blacklisted || false;
        isCurrentBlacklisted.textContent = isBlacklisted ? 'Blacklisted' : 'Active';
        isCurrentBlacklisted.className = 'status-badge' + (isBlacklisted ? ' blacklisted' : '');
    }
    
    // Blacklist count
    const blacklistCountEl = document.getElementById('status-blacklist-count');
    if (blacklistCountEl) {
        const count = data.blacklist_count || 0;
        blacklistCountEl.textContent = count;
    }
}

function displayConfigurationCard(data) {
    // Rate limit max
    const maxEl = document.getElementById('config-limit-max');
    if (maxEl) {
        maxEl.textContent = data.limit || 300;
    }
    
    // Rate limit window
    const windowEl = document.getElementById('config-limit-window');
    if (windowEl) {
        windowEl.textContent = data.window_seconds || 60;
    }
    
    // Blacklist duration
    const durationEl = document.getElementById('config-blacklist-duration');
    if (durationEl) {
        durationEl.textContent = data.blacklist_duration || 120;
    }
}

function displayBlacklistedIPs(data) {
    const container = document.getElementById('blacklist-ips-list');
    if (!container) return;
    
    const entries = data.blacklist_entries || [];
    
    if (entries.length === 0) {
        container.innerHTML = '<div class="blacklist-empty">No IPs currently blacklisted</div>';
        return;
    }
    
    // Sort by remaining time (earliest expiration first)
    entries.sort((a, b) => (a.remaining_seconds || 0) - (b.remaining_seconds || 0));
    
    let html = '';
    entries.forEach(([ip, entry], idx) => {
        // Handle both old format (array) and new format (object)
        if (typeof ip === 'object') {
            entry = ip;
            ip = entry.ip;
        }
        
        const remaining = entry.remaining_seconds || 0;
        
        html += `
            <div class="blacklist-row">
                <div class="blacklist-ip">${ip}</div>
                <div class="remaining-time">${remaining}s remaining</div>
                <button class="remove-btn" onclick="removeFromBlacklist('${ip}')">Remove</button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayTopIPs(data) {
    const container = document.getElementById('top-ips-list');
    if (!container) return;
    
    const topIPs = data.top_ips || [];
    
    if (topIPs.length === 0) {
        container.innerHTML = '<div class="top-ips-empty">No request data available</div>';
        return;
    }
    
    // Find max count for percentage calculation
    const maxCount = topIPs[0]?.event_count || 1;
    
    let html = '';
    topIPs.forEach((item, index) => {
        const ip = item.ip || 'Unknown';
        const count = item.event_count || 0;
        const percentage = ((count / maxCount) * 100).toFixed(1);
        const isBlacklisted = item.is_blacklisted ? ' (blacklisted)' : '';
        
        html += `
            <div class="top-ip-row">
                <div>${index + 1}. ${ip}${isBlacklisted}</div>
                <div class="event-count">${count} events</div>
                <div style="color: var(--text-secondary); font-size: 0.85em;">${percentage}%</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function updateLastUpdatedTimestamp() {
    const el = document.getElementById('rate-limit-last-updated');
    if (el) {
        const now = new Date();
        const time = now.toLocaleTimeString();
        el.textContent = 'Last updated: ' + time;
    }
}

async function removeFromBlacklist(ip) {
    // This would require an API endpoint to remove IPs from blacklist
    // For now, just show a message
    console.log('Remove IP from blacklist:', ip);
    alert('Manual blacklist removal not yet implemented.\nIP will be automatically removed after blacklist duration expires.');
}

// ===== PERFORMANCE METRICS DASHBOARD =====
let perfCharts = {};

function initPerformanceDashboard() {
    console.log('Initializing performance dashboard...');
    
    // Setup refresh button
    const refreshBtn = document.getElementById('perf-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadPerformanceMetrics);
        console.log('✓ Performance refresh button setup');
    }
    
    // Load initial data
    loadPerformanceMetrics();
    
    // Auto-refresh every 5 seconds
    setInterval(() => {
        if (!state.isRefreshPaused) {
            loadPerformanceMetrics();
        }
    }, 5000);
}

async function loadPerformanceMetrics() {
    try {
        const response = await fetch('/api/performance/metrics');
        if (!response.ok) {
            console.error('Failed to load performance metrics:', response.status);
            return;
        }
        
        const data = await response.json();
        displayPerformanceMetrics(data);
        updateLastUpdatedTimestamp();
    } catch (error) {
        console.error('Error loading performance metrics:', error);
    }
}

function displayPerformanceMetrics(data) {
    if (!data.metrics) return;
    
    const metrics = data.metrics;
    
    // Display summary cards
    displaySummaryCards(metrics);
    
    // Display charts
    displayPerformanceCharts(metrics, data.response_time_history);
    
    // Display endpoint statistics
    displayEndpointStats(metrics);
    
    // Update uptime
    updateUptimeDisplay(metrics);
}

function displaySummaryCards(metrics) {
    // Response times
    const avgResp = document.getElementById('perf-avg-response');
    if (avgResp) {
        avgResp.textContent = metrics.response_times.average.toFixed(2) + ' ms';
    }
    
    const minMaxResp = document.getElementById('perf-minmax-response');
    if (minMaxResp) {
        minMaxResp.textContent = `${metrics.response_times.minimum.toFixed(2)} / ${metrics.response_times.maximum.toFixed(2)} ms`;
    }
    
    // Throughput
    const rps = document.getElementById('perf-rps');
    if (rps) {
        rps.textContent = metrics.throughput.avg_requests_per_second.toFixed(2) + ' req/s';
    }
    
    const errorRate = document.getElementById('perf-error-rate');
    if (errorRate) {
        errorRate.textContent = metrics.throughput.error_rate_percent.toFixed(2) + ' %';
        // Change color based on error rate
        if (metrics.throughput.error_rate_percent > 10) {
            errorRate.style.color = '#ff6b6b';
        } else if (metrics.throughput.error_rate_percent > 5) {
            errorRate.style.color = '#ffa94d';
        } else {
            errorRate.style.color = '#4caf50';
        }
    }
    
    // Database
    const dbAvg = document.getElementById('perf-db-avg');
    if (dbAvg) {
        dbAvg.textContent = metrics.database.average_query_time.toFixed(2) + ' ms';
    }
    
    const dbTotal = document.getElementById('perf-db-total');
    if (dbTotal) {
        dbTotal.textContent = metrics.database.total_queries;
    }
    
    // System resources
    const cpu = document.getElementById('perf-cpu');
    if (cpu) {
        cpu.textContent = metrics.system.cpu_percent.toFixed(1) + ' %';
    }
    
    const memory = document.getElementById('perf-memory');
    if (memory) {
        memory.textContent = metrics.system.memory_mb.toFixed(1) + ' MB';
    }
}

function displayPerformanceCharts(metrics, history) {
    // Response Time Chart
    const responseCtx = document.getElementById('perf-response-chart');
    if (responseCtx && history) {
        if (perfCharts.response) {
            perfCharts.response.destroy();
        }
        
        const times = history.map(h => h.time);
        const timestamps = history.map(h => {
            const date = new Date(h.timestamp);
            return date.toLocaleTimeString();
        });
        
        perfCharts.response = new Chart(responseCtx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Response Time (ms)',
                    data: times,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: '#4caf50'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true, labels: { color: 'var(--text)' } }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: 'var(--text-secondary)' },
                        grid: { color: 'rgba(0, 0, 0, 0.1)' }
                    },
                    x: {
                        ticks: { color: 'var(--text-secondary)' },
                        grid: { color: 'rgba(0, 0, 0, 0.1)' }
                    }
                }
            }
        });
    }
    
    // Throughput vs Errors Chart
    const throughputCtx = document.getElementById('perf-throughput-chart');
    if (throughputCtx) {
        if (perfCharts.throughput) {
            perfCharts.throughput.destroy();
        }
        
        perfCharts.throughput = new Chart(throughputCtx, {
            type: 'bar',
            data: {
                labels: ['Requests/sec', 'Errors/sec'],
                datasets: [{
                    label: 'Throughput Metrics',
                    data: [
                        metrics.throughput.avg_requests_per_second,
                        metrics.throughput.avg_errors_per_second
                    ],
                    backgroundColor: [
                        'rgba(76, 175, 80, 0.7)',
                        'rgba(244, 67, 54, 0.7)'
                    ],
                    borderColor: [
                        '#4caf50',
                        '#f44336'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { color: 'var(--text-secondary)' },
                        grid: { color: 'rgba(0, 0, 0, 0.1)' }
                    },
                    y: {
                        ticks: { color: 'var(--text-secondary)' },
                        grid: { color: 'rgba(0, 0, 0, 0.1)' }
                    }
                }
            }
        });
    }
}

function displayEndpointStats(metrics) {
    const container = document.getElementById('perf-endpoints-table');
    if (!container || !metrics.endpoints) return;
    
    const endpoints = Object.entries(metrics.endpoints);
    
    if (endpoints.length === 0) {
        container.innerHTML = '<div class="table-placeholder">No endpoint data available yet</div>';
        return;
    }
    
    // Sort by count descending
    endpoints.sort((a, b) => (b[1].count || 0) - (a[1].count || 0));
    
    let html = `
        <table class="endpoints-table">
            <thead>
                <tr>
                    <th>Endpoint</th>
                    <th>Requests</th>
                    <th>Avg Response</th>
                    <th>Min/Max</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    endpoints.slice(0, 20).forEach(([endpoint, stats]) => {
        const errorRate = stats.error_rate || 0;
        const errorColor = errorRate > 5 ? '#ff6b6b' : '#4caf50';
        
        html += `
            <tr>
                <td class="endpoint-name">${endpoint}</td>
                <td class="endpoint-metric">${stats.count}</td>
                <td class="endpoint-metric">${stats.avg_response_time.toFixed(2)}ms</td>
                <td class="endpoint-metric">${stats.min_response_time.toFixed(2)}/${stats.max_response_time.toFixed(2)}ms</td>
                <td class="endpoint-metric" style="color: ${errorColor};">${stats.errors} (${errorRate.toFixed(1)}%)</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

function updateUptimeDisplay(metrics) {
    const uptimeEl = document.getElementById('perf-uptime');
    if (uptimeEl && metrics.uptime) {
        uptimeEl.textContent = 'Uptime: ' + metrics.uptime.display;
    }
}

function updateLastUpdatedTimestamp() {
    const el = document.getElementById('perf-last-update');
    if (el) {
        const now = new Date();
        const time = now.toLocaleTimeString();
        el.textContent = 'Last updated: ' + time;
    }
}

// ========================
// THREAT INTELLIGENCE FUNCTIONS
// ========================

function initThreatIntelDashboard() {
    console.log('🎯 Initializing Threat Intelligence Dashboard...');
    
    const searchBtn = document.getElementById('threat-intel-search-btn');
    const clearBtn = document.getElementById('threat-intel-clear-btn');
    const ipInput = document.getElementById('threat-intel-ip-input');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const ip = ipInput.value.trim();
            if (ip) {
                loadThreatProfile(ip);
            } else {
                showNotification('Please enter an IP address', 'warning');
            }
        });
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            ipInput.value = '';
            document.getElementById('threat-intel-results').style.display = 'none';
            document.getElementById('threat-intel-no-results').style.display = 'block';
        });
    }
    
    if (ipInput) {
        ipInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }
    
    // Load top threats on dashboard load
    loadTopThreats();
}

function loadThreatProfile(ip) {
    console.log(`Loading threat profile for ${ip}...`);
    
    fetch(`/api/threat-intel/${ip}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayThreatProfile(data.threat_profile);
            } else {
                showNotification(`Error: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading threat profile:', error);
            showNotification('Failed to load threat profile', 'error');
        });
}

function displayThreatProfile(profile) {
    const resultsDiv = document.getElementById('threat-intel-results');
    const noResultsDiv = document.getElementById('threat-intel-no-results');
    
    // Hide no results message, show results
    resultsDiv.style.display = 'block';
    noResultsDiv.style.display = 'none';
    
    // Update reputation gauge
    updateReputationGauge(profile);
    
    // Update quick stats
    updateQuickStats(profile);
    
    // Update WHOIS info
    updateWhoisInfo(profile);
    
    // Update threat indicators
    updateThreatIndicators(profile);
    
    // Update threat feeds
    updateThreatFeeds(profile);
    
    // Update botnet analysis
    updateBotnetAnalysis(profile);
    
    // Update score breakdown
    updateScoreBreakdown(profile);
}

function updateReputationGauge(profile) {
    const score = profile.reputation_score || 0;
    const level = profile.threat_level || 'minimal';
    
    document.getElementById('threat-score-text').textContent = `${score}/100`;
    document.getElementById('threat-level-text').textContent = level.toUpperCase();
    
    // Update gauge fill path (0-100 -> 0-180 degrees)
    const angle = (score / 100) * 180;
    const arcPath = generateGaugePath(angle);
    document.getElementById('threat-gauge-fill').setAttribute('d', arcPath);
    
    // Update gauge needle
    const needleAngle = (score / 100) * 180 - 90;
    const needleRad = (needleAngle * Math.PI) / 180;
    const x2 = 100 + 70 * Math.cos(needleRad);
    const y2 = 100 + 70 * Math.sin(needleRad);
    document.getElementById('threat-gauge-needle').setAttribute('x2', x2);
    document.getElementById('threat-gauge-needle').setAttribute('y2', y2);
    
    // Update gauge color based on score
    const color = getScoreColor(score);
    document.getElementById('threat-gauge-fill').setAttribute('stroke', color);
}

function generateGaugePath(angle) {
    const rad = (angle * Math.PI) / 180;
    const x = 100 + 80 * Math.cos((angle - 90) * Math.PI / 180);
    const y = 100 + 80 * Math.sin((angle - 90) * Math.PI / 180);
    const largeArc = angle > 90 ? 1 : 0;
    return `M 20 100 A 80 80 0 ${largeArc} 1 ${x} ${y}`;
}

function getScoreColor(score) {
    if (score >= 80) return '#f44336';  // Red
    if (score >= 60) return '#ff9800';  // Orange
    if (score >= 40) return '#ffc107';  // Yellow
    if (score >= 20) return '#8bc34a';  // Light Green
    return '#4caf50';  // Green
}

function updateQuickStats(profile) {
    // These would be populated from attack profile if available
    document.getElementById('threat-total-events').textContent = '0';
    document.getElementById('threat-attack-rate').textContent = '0/min';
    document.getElementById('threat-protocols').textContent = '0';
    
    const knownStatus = profile.threat_feeds && profile.threat_feeds.length > 0 ? 'Yes' : 'No';
    const statusEl = document.getElementById('threat-known-status');
    statusEl.textContent = knownStatus;
    statusEl.className = 'stat-value threat-' + (knownStatus === 'Yes' ? 'known' : 'unknown');
}

function updateWhoisInfo(profile) {
    const whois = profile.whois || {};
    
    document.getElementById('threat-whois-ip').textContent = whois.ip || '-';
    document.getElementById('threat-whois-hostname').textContent = whois.hostname || '-';
    document.getElementById('threat-whois-org').textContent = whois.organization || '-';
    document.getElementById('threat-whois-asn').textContent = whois.asn || '-';
    document.getElementById('threat-whois-country').textContent = whois.country || '-';
}

function updateThreatIndicators(profile) {
    const indicators = profile.indicators || [];
    const listEl = document.getElementById('threat-indicators-list');
    
    if (indicators.length === 0) {
        listEl.innerHTML = '<div class="indicator-placeholder">No threat indicators</div>';
        return;
    }
    
    let html = '';
    indicators.forEach(ind => {
        const severity = ind.severity || 'medium';
        const severityClass = severity.toLowerCase();
        
        html += `
            <div class="indicator-item indicator-${severityClass}">
                <div class="indicator-type">${ind.type.toUpperCase()}</div>
                <div class="indicator-desc">${ind.description}</div>
            </div>
        `;
    });
    
    listEl.innerHTML = html;
}

function updateThreatFeeds(profile) {
    const feeds = profile.threat_feeds || [];
    const listEl = document.getElementById('threat-feeds-list');
    
    if (feeds.length === 0) {
        listEl.innerHTML = '<div class="feed-placeholder">Not found in threat feeds</div>';
        return;
    }
    
    let html = '';
    feeds.forEach(feed => {
        html += `
            <div class="feed-item">
                <div style="font-weight: 600; margin-bottom: 4px;">${feed.feed}</div>
                <div style="font-size: 0.85em; color: var(--text-secondary);">
                    ${feed.threat || 'Listed in threat database'}
                    ${feed.confidence ? `<br>Confidence: ${(feed.confidence * 100).toFixed(0)}%` : ''}
                </div>
            </div>
        `;
    });
    
    listEl.innerHTML = html;
}

function updateBotnetAnalysis(profile) {
    const botnet = profile.botnet_analysis || {};
    const infoEl = document.getElementById('threat-botnet-info');
    
    if (!botnet.type) {
        infoEl.innerHTML = '<div class="botnet-placeholder">No botnet activity detected</div>';
        return;
    }
    
    let html = `
        <div class="botnet-details">
            <div class="botnet-family">${botnet.botnet_family || botnet.type}</div>
            <div class="botnet-confidence">
                Confidence: ${(botnet.confidence * 100).toFixed(0)}%
                ${botnet.similar_to ? `<br>Similar to: ${botnet.similar_to}` : ''}
            </div>
        </div>
    `;
    
    infoEl.innerHTML = html;
}

function updateScoreBreakdown(profile) {
    const factors = profile.score_factors || {};
    const factorsEl = document.getElementById('threat-score-factors');
    
    let html = '';
    Object.entries(factors).forEach(([name, value]) => {
        if (name === 'final_score') return;
        
        const displayName = name.replace(/_/g, ' ').toUpperCase();
        html += `
            <div class="score-factor">
                <div class="factor-name">${displayName}</div>
                <div class="factor-value">${value}/100</div>
            </div>
        `;
    });
    
    factorsEl.innerHTML = html;
}

function loadTopThreats() {
    fetch('/api/threat-intel/top-threats?limit=10')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTopThreats(data.threats);
            }
        })
        .catch(error => console.error('Error loading top threats:', error));
}

function displayTopThreats(threats) {
    const tableEl = document.getElementById('threat-top-list');
    
    if (threats.length === 0) {
        tableEl.innerHTML = '<div class="table-placeholder">No threats detected yet</div>';
        return;
    }
    
    let html = `
        <table class="threats-table">
            <thead>
                <tr>
                    <th>IP Address</th>
                    <th>Reputation</th>
                    <th>Threat Level</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    threats.forEach(threat => {
        const score = threat.reputation_score || 0;
        const color = getScoreColor(score);
        
        html += `
            <tr>
                <td>${threat.ip}</td>
                <td><span style="color: ${color}; font-weight: bold;">${score}/100</span></td>
                <td>${(threat.threat_level || 'unknown').toUpperCase()}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    tableEl.innerHTML = html;
}
