// DDoSPot Dashboard JavaScript - Enhanced with Filtering & Export

// Global state
const state = {
    charts: {},
    updateInterval: 5000,
    isOnline: false,
    attackersFilter: { ip: '', severity: '' },
    blacklistFilter: { ip: '', reason: '' },
    eventsFilter: { ip: '', protocol: '', type: '' },
    allAttackers: [],
    allBlacklist: [],
    allEvents: [],
};

// Initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    initCharts();
    initFilters();
    checkHealth();
    updateDashboard();
    setInterval(updateDashboard, state.updateInterval);
});

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
    
    // Export buttons
    document.getElementById('export-attackers')?.addEventListener('click', () => exportToCSV('attackers'));
    document.getElementById('export-blacklist')?.addEventListener('click', () => exportToCSV('blacklist'));
    document.getElementById('export-events')?.addEventListener('click', () => exportToCSV('events'));
}

// Filter and export functions
function applyAttackersFilter() {
    state.attackersFilter.ip = document.getElementById('filter-attackers-ip')?.value || '';
    state.attackersFilter.severity = document.getElementById('filter-attackers-severity')?.value || '';
    displayFilteredAttackers();
}

function applyBlacklistFilter() {
    state.blacklistFilter.ip = document.getElementById('filter-blacklist-ip')?.value || '';
    state.blacklistFilter.reason = document.getElementById('filter-blacklist-reason')?.value || '';
    displayFilteredBlacklist();
}

function applyEventsFilter() {
    state.eventsFilter.ip = document.getElementById('filter-events-ip')?.value || '';
    state.eventsFilter.protocol = document.getElementById('filter-events-protocol')?.value || '';
    state.eventsFilter.type = document.getElementById('filter-events-type')?.value || '';
    displayFilteredEvents();
}

function displayFilteredAttackers() {
    const tbody = document.getElementById('attackers-tbody');
    tbody.innerHTML = '';
    
    let filtered = state.allAttackers;
    
    if (state.attackersFilter.ip) {
        filtered = filtered.filter(a => a.ip.includes(state.attackersFilter.ip));
    }
    if (state.attackersFilter.severity) {
        filtered = filtered.filter(a => a.avg_severity?.toLowerCase() === state.attackersFilter.severity);
    }
    
    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No results</td></tr>';
        return;
    }
    
    filtered.slice(0, 20).forEach(attacker => {
        const row = document.createElement('tr');
        const severity = attacker.avg_severity || 'Unknown';
        const severityClass = `severity-${severity.toLowerCase()}`;
        row.innerHTML = `
            <td><a href="/profile/${attacker.ip}">${attacker.ip}</a></td>
            <td>${attacker.total_events || attacker.events || 0}</td>
            <td>${attacker.attack_type || attacker.type || 'Unknown'}</td>
            <td>${attacker.rate || '0'}</td>
            <td>${(attacker.protocols_used || attacker.protocols || []).join(', ')}</td>
            <td><a href="/profile/${attacker.ip}">View</a></td>
        `;
        tbody.appendChild(row);
    });
}

function displayFilteredBlacklist() {
    const tbody = document.getElementById('blacklist-tbody');
    tbody.innerHTML = '';
    
    let filtered = state.allBlacklist;
    
    if (state.blacklistFilter.ip) {
        filtered = filtered.filter(b => b.ip.includes(state.blacklistFilter.ip));
    }
    if (state.blacklistFilter.reason) {
        filtered = filtered.filter(b => b.reason === state.blacklistFilter.reason);
    }
    
    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">No results</td></tr>';
        return;
    }
    
    filtered.forEach(entry => {
        const row = document.createElement('tr');
        const severity = entry.severity || 'Unknown';
        const severityClass = `severity-${severity.toLowerCase()}`;
        row.innerHTML = `
            <td>${entry.ip}</td>
            <td>${entry.reason || 'N/A'}</td>
            <td><span class="${severityClass}">${severity}</span></td>
            <td>${formatTimeRemaining(entry.expires_in || 0)}</td>
        `;
        tbody.appendChild(row);
    });
}

function displayFilteredEvents() {
    const tbody = document.getElementById('events-tbody');
    tbody.innerHTML = '';
    
    let filtered = state.allEvents;
    
    if (state.eventsFilter.ip) {
        filtered = filtered.filter(e => e.ip.includes(state.eventsFilter.ip));
    }
    if (state.eventsFilter.protocol) {
        filtered = filtered.filter(e => e.protocol === state.eventsFilter.protocol);
    }
    if (state.eventsFilter.type) {
        filtered = filtered.filter(e => e.type === state.eventsFilter.type);
    }
    
    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No results</td></tr>';
        return;
    }
    
    filtered.slice(0, 20).forEach(event => {
        const row = document.createElement('tr');
        const time = new Date(event.timestamp).toLocaleTimeString();
        row.innerHTML = `
            <td>${time}</td>
            <td><a href="/profile/${event.ip}">${event.ip}</a></td>
            <td>${event.port || 'N/A'}</td>
            <td>${event.protocol || 'Unknown'}</td>
            <td>${event.size || 0} B</td>
            <td>${event.type || 'Unknown'}</td>
        `;
        tbody.appendChild(row);
    });
}

function exportToCSV(type) {
    let data = [];
    let headers = [];
    let filename = '';
    
    if (type === 'attackers') {
        headers = ['IP', 'Events', 'Type', 'Rate', 'Protocols', 'Severity'];
        data = state.allAttackers.map(a => [
            a.ip,
            a.total_events || a.events || 0,
            a.attack_type || a.type || 'Unknown',
            a.rate || '0',
            (a.protocols_used || a.protocols || []).join('; '),
            a.avg_severity || 'Unknown'
        ]);
        filename = 'attackers.csv';
    } else if (type === 'blacklist') {
        headers = ['IP', 'Reason', 'Severity', 'Expires In'];
        data = state.allBlacklist.map(b => [
            b.ip,
            b.reason || 'N/A',
            b.severity || 'Unknown',
            formatTimeRemaining(b.expires_in || 0)
        ]);
        filename = 'blacklist.csv';
    } else if (type === 'events') {
        headers = ['Timestamp', 'IP', 'Port', 'Protocol', 'Size (B)', 'Type'];
        data = state.allEvents.map(e => [
            new Date(e.timestamp).toLocaleString(),
            e.ip,
            e.port || 'N/A',
            e.protocol || 'Unknown',
            e.size || 0,
            e.type || 'Unknown'
        ]);
        filename = 'events.csv';
    }
    
    let csv = headers.join(',') + '\n';
    data.forEach(row => {
        csv += row.map(cell => {
            if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
                return `"${cell.replace(/"/g, '""')}"`;
            }
            return cell;
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

// Check health
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (data.status === 'healthy') {
            indicator.classList.add('healthy');
            indicator.classList.remove('unhealthy');
            text.textContent = 'Connected';
            state.isOnline = true;
        } else {
            indicator.classList.add('unhealthy');
            indicator.classList.remove('healthy');
            text.textContent = 'Offline';
            state.isOnline = false;
        }
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('status-indicator').classList.add('unhealthy');
        document.getElementById('status-text').textContent = 'Error';
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
        await checkHealth();
        if (!state.isOnline) {
            console.warn('Honeypot offline, skipping update');
            return;
        }

        // Fetch all data
        await Promise.all([
            updateStats(),
            updateTopAttackers(),
            updateBlacklist(),
            updateRecentEvents(),
            updateTimeline(),
            updateProtocols(),
            updateDatabaseInfo(),
        ]);

        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    } catch (error) {
        console.error('Dashboard update failed:', error);
    }
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch('/api/stats?hours=24');
        const stats = await response.json();

        document.getElementById('stat-total-events').textContent = stats.total_events?.toLocaleString() || '0';
        document.getElementById('stat-unique-ips').textContent = stats.unique_ips || '0';
        document.getElementById('stat-blacklist').textContent = stats.blacklisted_ips || '0';
        document.getElementById('stat-top-protocol').textContent = stats.top_protocol || 'N/A';
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

// Update top attackers
async function updateTopAttackers() {
    try {
        const response = await fetch('/api/top-attackers?limit=100');
        state.allAttackers = await response.json();
        displayFilteredAttackers();
    } catch (error) {
        console.error('Failed to update attackers:', error);
        document.getElementById('attackers-tbody').innerHTML = '<tr><td colspan="6" class="loading">Error loading</td></tr>';
    }
}

// Update blacklist
async function updateBlacklist() {
    try {
        const response = await fetch('/api/blacklist');
        state.allBlacklist = await response.json();
        displayFilteredBlacklist();
    } catch (error) {
        console.error('Failed to update blacklist:', error);
        document.getElementById('blacklist-tbody').innerHTML = '<tr><td colspan="4" class="loading">Error loading</td></tr>';
    }
}

// Update recent events
async function updateRecentEvents() {
    try {
        const response = await fetch('/api/recent-events?minutes=60&limit=100');
        state.allEvents = await response.json();
        displayFilteredEvents();
    } catch (error) {
        console.error('Failed to update recent events:', error);
        document.getElementById('events-tbody').innerHTML = '<tr><td colspan="6" class="loading">Error loading</td></tr>';
    }
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
        document.getElementById('db-events').textContent = info.event_count?.toLocaleString() || '0';
        document.getElementById('db-profiles').textContent = info.profile_count || '0';
    } catch (error) {
        console.error('Failed to update database info:', error);
    }
}

// Helper function to format time remaining
function formatTimeRemaining(seconds) {
    if (seconds <= 0) return 'Expired';
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
}

// Helper function to format date
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString();
}
