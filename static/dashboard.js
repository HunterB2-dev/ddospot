// DDoSPot Dashboard JavaScript

// Global state
const state = {
    charts: {},
    map: null,
    markers: {},
    updateInterval: 5000,
    isOnline: false,
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
};

// Initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    console.log('Initializing components...');
    try {
        initCharts();
        console.log('Charts initialized');
    } catch (e) { console.error('Chart init failed:', e); }
    
    try {
        initMap();
        console.log('Map initialized');
    } catch (e) { console.error('Map init failed:', e); }
    
    try {
        initFilters();
        console.log('Filters initialized');
    } catch (e) { console.error('Filter init failed:', e); }
    
    try {
        initAlerts();
        console.log('Alerts initialized');
    } catch (e) { console.error('Alert init failed:', e); }
    
    console.log('Running initial checks and updates...');
    checkHealth();
    updateDashboard();
    setupRefreshControl();
    setInterval(updateDashboard, state.updateInterval);
    console.log('Dashboard fully initialized');
});

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
    const sel = document.getElementById('refresh-interval');
    if (!sel) return;
    sel.value = String(state.updateInterval);
    sel.addEventListener('change', () => {
        const val = parseInt(sel.value, 10) || 5000;
        state.updateInterval = val;
        // Reset existing interval
        if (state._refreshTimer) {
            clearInterval(state._refreshTimer);
        }
        state._refreshTimer = setInterval(updateDashboard, state.updateInterval);
    });
}

// Check health
async function checkHealth() {
    try {
        console.log('Checking health...');
        const response = await fetch('/health');
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
    const timelineCtx = document.getElementById('timeline-chart').getContext('2d');
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
}

// Main update function
async function updateDashboard() {
    try {
        console.log('[DASHBOARD UPDATE] Starting update cycle...');
        await checkHealth();
        if (!state.isOnline) {
            console.warn('Honeypot offline, skipping update');
            return;
        }

        console.log('[DASHBOARD UPDATE] System online, fetching data...');
        // Fetch all data
        await Promise.all([
            updateStats(),
            updateTopAttackers(),
            updateBlacklist(),
            updateRecentEvents(),
            updateTimeline(),
            updateProtocols(),
            updateDatabaseInfo(),
            updateMapData(),
            updateCountryStats(),
        ]);

        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) lastUpdateEl.textContent = new Date().toLocaleTimeString();
        console.log('[DASHBOARD UPDATE] Update cycle completed');
    } catch (error) {
        console.error('Dashboard update failed:', error);
    }
}

// Update statistics
async function updateStats() {
    try {
        console.log('Fetching stats...');
        const response = await fetch('/api/stats?hours=24');
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
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><a href="/profile/${attacker.ip}">${attacker.ip}</a></td>
                <td>${attacker.events}</td>
                <td>${attacker.type}</td>
                <td>${attacker.rate}</td>
                <td>${attacker.protocols.join(', ')}</td>
                <td><a href="/profile/${attacker.ip}">View</a></td>
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
        params.set('minutes', '60');
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
        const response = await fetch('/api/timeline?hours=24&bucket=5');
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
function initDarkMode() {
    const toggle = document.getElementById('dark-mode-toggle');
    if (!toggle) return;
    
    // Load saved preference
    const isDarkMode = localStorage.getItem('ddospot-dark-mode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        toggle.textContent = '☀️';
    }
    
    toggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isNowDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('ddospot-dark-mode', isNowDark ? 'true' : 'false');
        toggle.textContent = isNowDark ? '☀️' : '🌙';
    });
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
document.addEventListener('DOMContentLoaded', function() {
    try {
        initDarkMode();
        console.log('Dark mode initialized');
    } catch (e) { console.error('Dark mode init failed:', e); }
    
    try {
        initExports();
        console.log('Exports initialized');
    } catch (e) { console.error('Export init failed:', e); }
});

