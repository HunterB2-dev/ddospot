// DDoSPot Mobile Dashboard JavaScript

class MobileDashboard {
    constructor() {
        this.apiKey = localStorage.getItem('api_key') || 'demo-key-admin';
        this.refreshInterval = 1000; // 1 second - real-time updates
        this.autoRefreshId = null;
        this.currentSeverityFilter = 'all';
        this.isOnline = navigator.onLine;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupTabs();
        this.setupPWA();
        this.setupServiceWorker();
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        this.loadDashboardData();
        this.setupAutoRefresh();
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
    }

    setupEventListeners() {
        // Menu
        document.getElementById('menuBtn').addEventListener('click', () => this.openMenu());
        document.getElementById('closeMenuBtn').addEventListener('click', () => this.closeMenu());
        document.getElementById('menuOverlay').addEventListener('click', () => this.closeMenu());

        // Bottom bar
        document.querySelectorAll('.bottom-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleBottomAction(e.currentTarget));
        });

        // Tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Threats
        document.getElementById('threatSearch').addEventListener('input', (e) => this.filterThreats(e.target.value));

        // Alerts filter
        document.querySelectorAll('.filter-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => this.setAlertFilter(e.target));
        });

        // Quick actions
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseDetection());
        document.getElementById('clearBlockBtn').addEventListener('click', () => this.clearBlocks());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportData());
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettings());

        // Service toggles
        ['sshToggle', 'httpToggle', 'ssdpToggle'].forEach(id => {
            document.getElementById(id).addEventListener('change', (e) => this.toggleService(id, e.target.checked));
        });

        // Notification settings
        document.getElementById('pushToggle').addEventListener('change', (e) => this.setPushNotifications(e.target.checked));
        document.getElementById('criticalOnlyToggle').addEventListener('change', (e) => this.setCriticalOnly(e.target.checked));

        // Menu links
        document.getElementById('offlineToggle').addEventListener('click', () => this.toggleOfflineMode());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());
    }

    setupTabs() {
        this.currentTab = 'overview';
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

        document.getElementById(tabName).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        this.currentTab = tabName;
        
        if (tabName === 'threats') {
            this.loadThreats();
        } else if (tabName === 'alerts') {
            this.loadAlerts();
        }
    }

    updateTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        document.querySelector('.time').textContent = `${hours}:${minutes}`;
    }

    async loadDashboardData() {
        try {
            const results = await Promise.allSettled([
                this.fetchAPI('/api/stats?hours=24'),
                this.fetchAPI('/api/top-attackers?limit=5'),
                this.fetchAPI('/api/protocol-breakdown'),
                this.fetchAPI('/api/threat/summary')
            ]);

            const [statsResult, attackersResult, protocolResult, threatResult] = results;
            
            const stats = statsResult.status === 'fulfilled' ? statsResult.value : null;
            const attackers = attackersResult.status === 'fulfilled' ? attackersResult.value : null;
            const protocolBreakdown = protocolResult.status === 'fulfilled' ? protocolResult.value : null;
            const threatSummary = threatResult.status === 'fulfilled' ? threatResult.value : null;

            if (stats) this.updateStats(stats, threatSummary);
            if (attackers) this.updateTopAttackers(attackers);
            if (protocolBreakdown) this.updateProtocolBreakdown(protocolBreakdown);
            if (stats) this.updateBlockedCount(stats);
            
            this.retryCount = 0; // Reset retry count on success
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.retryCount++;
            if (this.retryCount <= this.maxRetries) {
                console.log(`Retry attempt ${this.retryCount}/${this.maxRetries}`);
                setTimeout(() => this.loadDashboardData(), 2000); // Retry after 2 seconds
            } else {
                this.showToast('Failed to load data - check connection', 'error');
                this.retryCount = 0;
            }
        }
    }

    updateStats(stats, threatSummary) {
        if (!stats) return;

        document.getElementById('totalEvents').textContent = this.formatNumber(stats.total_events || 0);
        document.getElementById('uniqueIPs').textContent = this.formatNumber(stats.unique_ips || 0);
        document.getElementById('blocked').textContent = this.formatNumber(stats.blacklisted_ips || 0);

        const activeThreats = threatSummary && threatSummary.success
            ? threatSummary.high_risk_count
            : 0;
        document.getElementById('activeCount').textContent = this.formatNumber(activeThreats || 0);
    }

    updateProtocolBreakdown(protocolBreakdown) {
        const protoCounts = protocolBreakdown || {};
        const ssh = protoCounts.SSH || protoCounts.ssh || 0;
        const http = protoCounts.HTTP || protoCounts.http || 0;
        const ssdp = protoCounts.SSDP || protoCounts.ssdp || 0;
        const total = ssh + http + ssdp || 1;

        document.getElementById('sshBar').style.width = (ssh / total * 100) + '%';
        document.getElementById('httpBar').style.width = (http / total * 100) + '%';
        document.getElementById('ssdpBar').style.width = (ssdp / total * 100) + '%';

        document.getElementById('sshValue').textContent = Math.round(ssh / total * 100) + '%';
        document.getElementById('httpValue').textContent = Math.round(http / total * 100) + '%';
        document.getElementById('ssdpValue').textContent = Math.round(ssdp / total * 100) + '%';
    }

    updateTopAttackers(attackers) {
        const list = document.getElementById('topAttackersList');
        if (!attackers || attackers.length === 0) {
            list.innerHTML = '<div class="placeholder">No attacks detected</div>';
            return;
        }

        list.innerHTML = attackers.map(attacker => `
            <div class="attacker-item">
                <div class="attacker-info">
                    <div class="attacker-ip">${attacker.ip}</div>
                    <div class="attacker-details">
                        ${this.formatProtocol(attacker.type || (attacker.protocols && attacker.protocols[0]))} •
                        ${attacker.rate ? `${attacker.rate}/min` : 'activity'}
                    </div>
                </div>
                <div class="attacker-count">${attacker.events}</div>
            </div>
        `).join('');
    }

    updateBlockedCount(stats) {
        if (!stats) return;
        document.getElementById('blocked').textContent = this.formatNumber(stats.blacklisted_ips || 0);
    }

    async loadThreats() {
        try {
            const result = await this.fetchAPI('/api/threat/high-risk?limit=20');
            const threats = result && result.success ? result.high_risk_ips : (Array.isArray(result) ? result : []);
            this.displayThreats(threats);
        } catch (error) {
            console.error('Failed to load threats:', error);
            this.showToast('Failed to load threats', 'error');
            this.displayThreats([]); // Show empty state
        }
    }

    displayThreats(threats) {
        const list = document.getElementById('threatsList');
        if (!threats || threats.length === 0) {
            list.innerHTML = '<div class="placeholder">No threats detected</div>';
            return;
        }

        list.innerHTML = threats.map(threat => {
            const severity = this.getThreatSeverity(threat.risk_score);
            return `
                <div class="threat-item">
                    <div class="threat-header">
                        <div class="threat-ip">${threat.source_ip}</div>
                        <span class="threat-severity ${severity}">${severity.toUpperCase()}</span>
                    </div>
                    <div class="threat-row">
                        <span>Risk Score: ${threat.risk_score || 0}</span>
                        <span>Updated: ${this.formatTime(threat.last_updated)}</span>
                    </div>
                    <div class="threat-row">
                        <span>Type: ${threat.threat_type || 'unknown'}</span>
                        <span>${threat.threat_description || ''}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    filterThreats(query) {
        const items = document.querySelectorAll('.threat-item');
        items.forEach(item => {
            const ip = item.querySelector('.threat-ip').textContent;
            item.style.display = ip.includes(query) ? 'block' : 'none';
        });
    }

    async loadAlerts() {
        try {
            const result = await this.fetchAPI('/api/alerts/history?limit=20');
            const alerts = Array.isArray(result) ? result : (result && result.alerts ? result.alerts : []);
            this.displayAlerts(alerts);
        } catch (error) {
            console.error('Failed to load alerts:', error);
            this.showToast('Failed to load alerts', 'error');
            this.displayAlerts([]); // Show empty state
        }
    }

    displayAlerts(alerts) {
        const list = document.getElementById('alertsList');
        if (!alerts || alerts.length === 0) {
            list.innerHTML = '<div class="placeholder">No alerts</div>';
            return;
        }

        let filtered = alerts;
        if (this.currentSeverityFilter !== 'all') {
            filtered = alerts.filter(a => this.normalizeAlertSeverity(a.severity) === this.currentSeverityFilter);
        }

        list.innerHTML = filtered.map(alert => {
            const severity = this.normalizeAlertSeverity(alert.severity);
            const icons = { critical: '🔴', warning: '🟡', info: '🔵' };
            const title = alert.type ? alert.type.replace(/_/g, ' ') : 'Alert';
            return `
                <div class="alert-item ${severity}">
                    <div class="alert-icon">${icons[severity] || '📌'}</div>
                    <div class="alert-content">
                        <div class="alert-title">${title}</div>
                        <div class="alert-message">${alert.message || 'No details'}${alert.ip ? ` • ${alert.ip}` : ''}</div>
                        <div class="alert-time">${this.formatTime(alert.timestamp)}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    setAlertFilter(btn) {
        document.querySelectorAll('.filter-toggle').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentSeverityFilter = btn.dataset.severity;
        this.loadAlerts();
    }

    openMenu() {
        document.getElementById('mobileMenu').classList.add('open');
    }

    closeMenu() {
        document.getElementById('mobileMenu').classList.remove('open');
    }

    handleBottomAction(btn) {
        const action = btn.dataset.action;
        switch (action) {
            case 'refresh':
                this.loadDashboardData();
                this.showToast('Refreshed', 'success');
                break;
            case 'fullscreen':
                this.toggleFullscreen();
                break;
            case 'help':
                this.showHelp();
                break;
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    }

    showHelp() {
        this.showToast('Swipe left/right to navigate tabs. Pull down to refresh.', 'info');
    }

    async pauseDetection() {
        this.showToast('Detection paused for 5 minutes', 'warning');
    }

    async clearBlocks() {
        if (confirm('Clear all IP blocks?')) {
            try {
                await this.fetchAPI('/api/blocked-ips', 'DELETE');
                this.showToast('Blocks cleared', 'success');
                this.loadDashboardData();
            } catch (error) {
                this.showToast('Failed to clear blocks', 'error');
            }
        }
    }

    async exportData() {
        const data = {
            timestamp: new Date().toISOString(),
            stats: document.querySelector('.stat-number').textContent,
            exportedAt: new Date().toLocaleString()
        };
        
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ddospot-export-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Data exported', 'success');
    }

    openSettings() {
        window.location.href = '/settings';
    }

    async toggleService(serviceId, enabled) {
        const service = serviceId.replace('Toggle', '');
        this.showToast(`${service} ${enabled ? 'enabled' : 'disabled'}`, 'info');
    }

    setPushNotifications(enabled) {
        if (enabled && 'Notification' in window) {
            Notification.requestPermission();
        }
    }

    setCriticalOnly(enabled) {
        this.showToast(`Critical only: ${enabled ? 'ON' : 'OFF'}`, 'info');
    }

    toggleOfflineMode() {
        // In a real app, this would sync data when offline
        this.showToast('Offline mode: ' + (!this.isOnline ? 'ON' : 'OFF'), 'info');
    }

    logout() {
        localStorage.removeItem('api_key');
        window.location.href = '/';
    }

    handleOnline() {
        this.isOnline = true;
        document.getElementById('onlineStatus').textContent = 'Online';
        this.showToast('Back online', 'success');
        this.loadDashboardData();
    }

    handleOffline() {
        this.isOnline = false;
        document.getElementById('onlineStatus').textContent = 'Offline';
        this.showToast('Offline mode', 'warning');
    }

    setupAutoRefresh() {
        this.autoRefreshId = setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }

    setupPWA() {
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            this.showPWAPrompt();
        });

        document.getElementById('pwaInstall').addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    this.showToast('DDoSPot installed!', 'success');
                }
                deferredPrompt = null;
            }
        });

        document.getElementById('pwaDismiss').addEventListener('click', () => {
            this.dismissPWAPrompt();
        });
    }

    showPWAPrompt() {
        const prompt = document.getElementById('pwaPrompt');
        if (!localStorage.getItem('pwaPromptDismissed')) {
            prompt.classList.add('show');
        }
    }

    dismissPWAPrompt() {
        document.getElementById('pwaPrompt').classList.remove('show');
        localStorage.setItem('pwaPromptDismissed', 'true');
    }

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/mobile-sw.js').catch(err => {
                console.log('ServiceWorker registration failed:', err);
            });
        }
    }

    async fetchAPI(endpoint, method = 'GET', retries = 2) {
        const headers = {
            'X-API-Key': this.apiKey,
            'Content-Type': 'application/json'
        };

        try {
            const response = await fetch(endpoint, { 
                method, 
                headers,
                timeout: 5000
            });
            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                }
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            if (retries > 0) {
                console.log(`Retrying ${endpoint} (${retries} retries left)`);
                await new Promise(resolve => setTimeout(resolve, 1000));
                return this.fetchAPI(endpoint, method, retries - 1);
            }
            throw error;
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    formatProtocol(protocol) {
        const map = { 'ssh': 'SSH', 'http': 'HTTP', 'ssdp': 'SSDP', 'dns': 'DNS' };
        return map[protocol] || protocol || 'Unknown';
    }

    normalizeAlertSeverity(severity) {
        const value = (severity || 'info').toLowerCase();
        if (value === 'critical') return 'critical';
        if (value === 'high' || value === 'warning') return 'warning';
        if (value === 'medium' || value === 'low') return 'info';
        return value;
    }

    getThreatSeverity(score) {
        const value = Number(score) || 0;
        if (value >= 9) return 'critical';
        if (value >= 7) return 'high';
        if (value >= 4) return 'medium';
        return 'low';
    }

    formatTime(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileDashboard = new MobileDashboard();
});

// Handle visibility changes to optimize battery life
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.mobileDashboard) {
        clearInterval(window.mobileDashboard.autoRefreshId);
    } else if (!document.hidden && window.mobileDashboard) {
        window.mobileDashboard.setupAutoRefresh();
    }
});
