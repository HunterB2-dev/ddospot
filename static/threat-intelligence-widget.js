/**
 * Threat Intelligence Dashboard Widget - Real-time Updates
 * Handles live data fetching, visualization, and user interactions
 */

// @ts-nocheck
// eslint-disable-next-line no-unexpected-multiline

class ThreatIntelligenceDashboard {
  constructor(containerSelector = '#threat-intel-section') {
    this.containerSelector = containerSelector;
    this.container = document.querySelector(containerSelector);
    this.apiBaseUrl = '/api/threat-intel';
    this.updateInterval = 10000; // 10 seconds
    this.threatData = {
      topThreats: [],
      statistics: {},
      distribution: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      }
    };
    this.currentPage = 1;
    this.pageSize = 10;
    this.isUpdating = false;
    this.activityLog = [];
    this.cacheEnabled = true;
    
    if (!this.container) {
      console.error('[TID] Container not found:', containerSelector);
      return;
    }
    
    this.init();
  }

  /**
   * Initialize the dashboard
   */
  async init() {
    console.log('[TID] Initializing Threat Intelligence Dashboard...');
    
    // Inject the widget HTML
    this.injectHTML();
    
    this.setupEventListeners();
    await this.initialLoad();
    this.startPeriodicUpdates();
    
    console.log('[TID] Dashboard initialized successfully');
  }

  /**
   * Inject widget HTML into the container
   */
  injectHTML() {
    this.container.innerHTML = `
<!-- Threat Intelligence Container -->
<div id="threat-intel-container" class="dashboard-section">
  <h2 class="section-title">
    ⚠️ Threat Intelligence
  </h2>

  <!-- Status Indicator -->
  <div class="threat-status-bar">
    <div class="status-item">
      <span class="label">System Status</span>
      <span class="status-badge" id="ti-system-status">●</span>
    </div>
    <div class="status-item">
      <span class="label">IPs Analyzed</span>
      <span class="value" id="ti-ips-analyzed">0</span>
    </div>
    <div class="status-item">
      <span class="label">Critical Threats</span>
      <span class="value" id="ti-critical-count">0</span>
    </div>
    <div class="status-item">
      <span class="label">Last Update</span>
      <span class="value" id="ti-last-update">--:--:--</span>
    </div>
  </div>

  <!-- Main Content Grid -->
  <div class="threat-content-grid">

    <!-- Left Column: Top Threats -->
    <div class="threat-column threat-column-left">
      <div class="threat-card">
        <h3 class="card-title">
          📋 Top Threats
        </h3>
        
        <!-- Top Threats Table -->
        <div class="threats-table-container">
          <table class="threats-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>IP Address</th>
                <th>Threat Score</th>
                <th>Level</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="top-threats-tbody">
              <!-- Populated by JavaScript -->
              <tr class="loading">
                <td colspan="5" class="text-center">Loading threats...</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="table-pagination">
          <button id="threats-prev" class="btn-small" disabled>← Previous</button>
          <span id="threats-page" class="page-info">Page 1</span>
          <button id="threats-next" class="btn-small">Next →</button>
        </div>
      </div>
    </div>

    <!-- Right Column: Statistics & Distribution -->
    <div class="threat-column threat-column-right">

      <!-- Threat Distribution Card -->
      <div class="threat-card">
        <h3 class="card-title">
          📊 Threat Distribution
        </h3>
        
        <div class="distribution-container">
          <div class="distribution-chart" id="threat-distribution-chart">
            <!-- SVG pie chart populated by JavaScript -->
          </div>
          
          <div class="distribution-legend">
            <div class="legend-item" id="legend-critical">
              <span class="legend-color critical"></span>
              <span class="legend-label">Critical</span>
              <span class="legend-count" data-level="CRITICAL">0</span>
            </div>
            <div class="legend-item" id="legend-high">
              <span class="legend-color high"></span>
              <span class="legend-label">High</span>
              <span class="legend-count" data-level="HIGH">0</span>
            </div>
            <div class="legend-item" id="legend-medium">
              <span class="legend-color medium"></span>
              <span class="legend-label">Medium</span>
              <span class="legend-count" data-level="MEDIUM">0</span>
            </div>
            <div class="legend-item" id="legend-low">
              <span class="legend-color low"></span>
              <span class="legend-label">Low</span>
              <span class="legend-count" data-level="LOW">0</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Statistics Card -->
      <div class="threat-card">
        <h3 class="card-title">
          📈 Statistics
        </h3>
        
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">Average Threat Score</span>
            <span class="stat-value" id="avg-threat-score">0.0</span>
            <span class="stat-unit">/100</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Threat Feeds Active</span>
            <span class="stat-value" id="active-feeds">4</span>
            <span class="stat-unit">sources</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Analysis Latency</span>
            <span class="stat-value" id="analysis-latency">0.0</span>
            <span class="stat-unit">ms</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Cache Hit Rate</span>
            <span class="stat-value" id="cache-hit-rate">95.0</span>
            <span class="stat-unit">%</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Detailed IP Analysis Section -->
  <div class="threat-card full-width">
    <h3 class="card-title">
      🔍 Analyze IP
    </h3>
    
    <div class="ip-analysis-container">
      <div class="ip-input-group">
        <input 
          type="text" 
          id="analyze-ip-input" 
          class="ip-input" 
          placeholder="Enter IP address (e.g., 1.2.3.4)"
          autocomplete="off"
        />
        <button id="analyze-ip-btn" class="btn-primary">Analyze</button>
        <span class="input-hint">Press Enter to analyze</span>
      </div>

      <!-- Analysis Result -->
      <div id="analysis-result" class="analysis-result hidden">
        <div class="analysis-header">
          <span class="result-ip" id="result-ip">--</span>
          <span class="result-threat-level" id="result-threat-level">--</span>
        </div>

        <div class="analysis-grid">
          <!-- Reputation Section -->
          <div class="analysis-section">
            <h4 class="section-header">IP Reputation</h4>
            <div class="metric-row">
              <span class="metric-name">Reputation Score</span>
              <div class="metric-bar-container">
                <div class="metric-bar" id="result-rep-bar" style="width: 0%"></div>
              </div>
              <span class="metric-value" id="result-rep-score">0/100</span>
            </div>
            <div class="metric-row">
              <span class="metric-name">Confidence</span>
              <span class="metric-value" id="result-rep-confidence">0%</span>
            </div>
            <div class="sources-list" id="result-rep-sources">
              <!-- Populated by JavaScript -->
            </div>
          </div>

          <!-- Geolocation Section -->
          <div class="analysis-section">
            <h4 class="section-header">Geolocation</h4>
            <div class="metric-row">
              <span class="metric-name">Country</span>
              <span class="metric-value" id="result-geo-country">--</span>
            </div>
            <div class="metric-row">
              <span class="metric-name">Geographic Risk</span>
              <div class="metric-bar-container">
                <div class="metric-bar" id="result-geo-bar" style="width: 0%"></div>
              </div>
              <span class="metric-value" id="result-geo-score">0/100</span>
            </div>
            <div class="metric-row">
              <span class="metric-name">ISP</span>
              <span class="metric-value" id="result-geo-isp">Unknown</span>
            </div>
          </div>

          <!-- Threat Feeds Section -->
          <div class="analysis-section">
            <h4 class="section-header">Threat Feeds</h4>
            <div class="feeds-list" id="result-feeds-list">
              <!-- Populated by JavaScript -->
            </div>
          </div>

          <!-- Trends Section -->
          <div class="analysis-section">
            <h4 class="section-header">Attack Trends</h4>
            <div class="metric-row">
              <span class="metric-name">Attack Count</span>
              <span class="metric-value" id="result-trend-count">0</span>
            </div>
            <div class="metric-row">
              <span class="metric-name">Velocity</span>
              <span class="metric-value" id="result-trend-velocity">0/hour</span>
            </div>
            <div class="metric-row">
              <span class="metric-name">Consistency</span>
              <span class="metric-value" id="result-trend-consistency">0%</span>
            </div>
          </div>
        </div>

        <!-- Composite Score -->
        <div class="analysis-composite">
          <div class="composite-score-display">
            <div class="composite-circle" id="composite-circle">
              <span class="composite-number" id="composite-score">0</span>
              <span class="composite-label">/100</span>
            </div>
          </div>

          <!-- Recommendations -->
          <div class="recommendations-box">
            <h4 class="recommendations-title">Recommendations</h4>
            <ul class="recommendations-list" id="recommendations-list">
              <!-- Populated by JavaScript -->
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Real-time Activity Feed -->
  <div class="threat-card full-width">
    <h3 class="card-title">
      📡 Real-time Activity
    </h3>
    
    <div class="activity-feed" id="activity-feed">
      <!-- Activity items populated by JavaScript -->
      <div class="activity-item info">
        <span class="timestamp" id="initial-timestamp">--:--:--</span>
        <span class="message">Threat Intelligence System initialized</span>
      </div>
    </div>
  </div>
</div>
    `;
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // IP Analysis
    document.getElementById('analyze-ip-btn')?.addEventListener('click', () => {
      this.analyzeIP();
    });

    document.getElementById('analyze-ip-input')?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.analyzeIP();
      }
    });

    // Pagination
    document.getElementById('threats-prev')?.addEventListener('click', () => {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.renderTopThreats();
      }
    });

    document.getElementById('threats-next')?.addEventListener('click', () => {
      this.currentPage++;
      this.renderTopThreats();
    });

    // Click on threat rows to analyze
    document.addEventListener('click', (e) => {
      if (e.target.closest('.analyze-ip-btn')) {
        const ip = e.target.closest('tr')?.querySelector('.ip')?.textContent;
        if (ip) {
          document.getElementById('analyze-ip-input').value = ip;
          this.analyzeIP();
        }
      }
    });
  }

  /**
   * Initial data load
   */
  async initialLoad() {
    this.logActivity('System initializing...', 'info');
    
    try {
      const [topThreats, stats] = await Promise.all([
        this.fetchTopThreats(),
        this.fetchStatistics()
      ]);

      this.threatData.topThreats = topThreats;
      this.threatData.statistics = stats;
      this.updateDistribution(topThreats);
      
      this.updateStatusBar();
      this.renderTopThreats();
      this.renderDistribution();
      this.renderStatistics();
      
      this.logActivity('Threat intelligence system online', 'info');
    } catch (error) {
      console.error('[TID] Initial load error:', error);
      this.logActivity('Error loading threat data', 'critical');
    }
  }

  /**
   * Start periodic updates
   */
  startPeriodicUpdates() {
    setInterval(() => {
      this.updateThreatData();
    }, this.updateInterval);
  }

  /**
   * Update threat data
   */
  async updateThreatData() {
    if (this.isUpdating) return;
    
    this.isUpdating = true;
    
    try {
      const startTime = performance.now();
      
      const [topThreats, stats] = await Promise.all([
        this.fetchTopThreats(),
        this.fetchStatistics()
      ]);

      const endTime = performance.now();
      const latency = (endTime - startTime).toFixed(2);

      // Check for new threats
      const newThreats = this.detectNewThreats(topThreats);
      if (newThreats.length > 0) {
        newThreats.forEach(threat => {
          this.logActivity(`New threat detected: ${threat.ip} (${threat.level})`, threat.level.toLowerCase());
        });
      }

      this.threatData.topThreats = topThreats;
      this.threatData.statistics = stats;
      this.updateDistribution(topThreats);
      
      this.updateStatusBar(latency);
      this.renderTopThreats();
      this.renderDistribution();
      this.renderStatistics();
      
    } catch (error) {
      console.error('[TID] Update error:', error);
      this.logActivity('Failed to update threat data', 'high');
    } finally {
      this.isUpdating = false;
    }
  }

  /**
   * Fetch top threats
   */
  async fetchTopThreats(limit = 50) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/top-threats?limit=${limit}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      return data.threats || [];
    } catch (error) {
      console.error('[TID] Error fetching top threats:', error);
      return [];
    }
  }

  /**
   * Fetch statistics
   */
  async fetchStatistics() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/statistics`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      return data.statistics || {};
    } catch (error) {
      console.error('[TID] Error fetching statistics:', error);
      return {};
    }
  }

  /**
   * Analyze a specific IP
   */
  async analyzeIP() {
    const input = document.getElementById('analyze-ip-input');
    const ip = input?.value?.trim();

    if (!ip) {
      this.logActivity('Invalid IP address provided', 'low');
      return;
    }

    if (!this.isValidIP(ip)) {
      this.logActivity(`Invalid IP format: ${ip}`, 'medium');
      return;
    }

    try {
      this.logActivity(`Analyzing IP: ${ip}`, 'info');
      
      const response = await fetch(`${this.apiBaseUrl}/analyze?ip=${ip}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const analysis = await response.json();
      this.displayAnalysis(analysis);
      
      this.logActivity(`Analysis complete for ${ip}`, 'info');
    } catch (error) {
      console.error('[TID] Analysis error:', error);
      this.logActivity(`Failed to analyze ${ip}`, 'high');
    }
  }

  /**
   * Display IP analysis result
   */
  displayAnalysis(analysis) {
    const resultDiv = document.getElementById('analysis-result');
    
    if (!analysis.success) {
      resultDiv.classList.add('hidden');
      return;
    }

    const data = analysis.analysis || {};
    
    // Update header
    document.getElementById('result-ip').textContent = data.ip || '--';
    const threatLevel = this.getThreatLevel(data.composite_score || 0);
    document.getElementById('result-threat-level').textContent = threatLevel;
    document.getElementById('result-threat-level').className = `result-threat-level ${threatLevel.toLowerCase()}`;

    // Update reputation
    const repScore = data.reputation_score || 0;
    document.getElementById('result-rep-score').textContent = `${repScore.toFixed(1)}/100`;
    document.getElementById('result-rep-bar').style.width = `${repScore}%`;

    // Update geolocation
    document.getElementById('result-geo-country').textContent = data.geolocation?.country || 'Unknown';
    const geoScore = data.geolocation?.risk_score || 0;
    document.getElementById('result-geo-score').textContent = `${geoScore.toFixed(1)}/100`;
    document.getElementById('result-geo-bar').style.width = `${geoScore}%`;
    document.getElementById('result-geo-isp').textContent = data.geolocation?.isp || 'Unknown';

    // Update threat feeds
    this.renderFeedsList(data.threat_feeds || []);

    // Update trends
    document.getElementById('result-trend-count').textContent = data.trends?.total_attacks || 0;
    document.getElementById('result-trend-velocity').textContent = `${(data.trends?.velocity || 0).toFixed(1)}/hour`;
    document.getElementById('result-trend-consistency').textContent = `${(data.trends?.consistency || 0).toFixed(1)}%`;

    // Update composite score
    const compositeScore = data.composite_score || 0;
    document.getElementById('composite-score').textContent = compositeScore.toFixed(0);

    // Update recommendations
    this.renderRecommendations(data.recommendations || []);

    // Show result
    resultDiv.classList.remove('hidden');
  }

  /**
   * Render feeds list
   */
  renderFeedsList(feeds) {
    const container = document.getElementById('result-feeds-list');
    container.innerHTML = '';

    if (!feeds || feeds.length === 0) {
      container.innerHTML = '<div class="feed-item"><span class="feed-name">No threats detected</span></div>';
      return;
    }

    feeds.forEach(feed => {
      const item = document.createElement('div');
      item.className = 'feed-item';
      item.innerHTML = `
        <span class="feed-name">${feed.source || 'Unknown'}</span>
        <span class="feed-status ${feed.matched ? 'matched' : 'unmatched'}">●</span>
      `;
      container.appendChild(item);
    });
  }

  /**
   * Render recommendations
   */
  renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
      const item = document.createElement('li');
      item.className = 'recommendation-item';
      item.innerHTML = '<span class="text">No specific recommendations</span>';
      container.appendChild(item);
      return;
    }

    recommendations.forEach(rec => {
      const item = document.createElement('li');
      item.className = 'recommendation-item';
      item.innerHTML = `
        <span class="icon">→</span>
        <span class="text">${rec}</span>
      `;
      container.appendChild(item);
    });
  }

  /**
   * Render top threats table
   */
  renderTopThreats() {
    const tbody = document.getElementById('top-threats-tbody');
    if (!tbody) return;

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pageThreats = this.threatData.topThreats.slice(start, end);

    if (pageThreats.length === 0) {
      tbody.innerHTML = '<tr class="loading"><td colspan="5" class="text-center">No threats detected</td></tr>';
      this.updatePaginationButtons();
      return;
    }

    tbody.innerHTML = pageThreats.map((threat, index) => {
      const threatLevel = this.getThreatLevel(threat.threat_score);
      const score = threat.threat_score || 0;

      return `
        <tr class="threat-row">
          <td class="rank">${start + index + 1}</td>
          <td class="ip">${threat.ip || '--'}</td>
          <td class="score">
            <div class="score-bar">
              <div class="score-fill" style="width: ${score}%"></div>
            </div>
            <span class="score-text">${score.toFixed(1)}</span>
          </td>
          <td class="level">
            <span class="level-badge ${threatLevel.toLowerCase()}">${threatLevel}</span>
          </td>
          <td class="action">
            <button class="btn-tiny analyze-ip-btn">Analyze</button>
          </td>
        </tr>
      `;
    }).join('');

    this.updatePaginationButtons();
  }

  /**
   * Update pagination buttons
   */
  updatePaginationButtons() {
    const prevBtn = document.getElementById('threats-prev');
    const nextBtn = document.getElementById('threats-next');
    const pageInfo = document.getElementById('threats-page');

    if (prevBtn) prevBtn.disabled = this.currentPage === 1;
    if (nextBtn) {
      const maxPage = Math.ceil(this.threatData.topThreats.length / this.pageSize);
      nextBtn.disabled = this.currentPage >= maxPage;
    }
    if (pageInfo) pageInfo.textContent = `Page ${this.currentPage}`;
  }

  /**
   * Render threat distribution pie chart
   */
  renderDistribution() {
    const dist = this.threatData.distribution;
    const total = dist.critical + dist.high + dist.medium + dist.low;

    if (total === 0) {
      document.getElementById('threat-distribution-chart').innerHTML = 
        '<div style="text-align: center; padding: 50px 0; color: rgba(255,255,255,0.5);">No data</div>';
      return;
    }

    // Update legend counts
    document.querySelector('[data-level="CRITICAL"]').textContent = dist.critical;
    document.querySelector('[data-level="HIGH"]').textContent = dist.high;
    document.querySelector('[data-level="MEDIUM"]').textContent = dist.medium;
    document.querySelector('[data-level="LOW"]').textContent = dist.low;

    // Create SVG pie chart
    const svg = this.createPieChart(dist);
    document.getElementById('threat-distribution-chart').innerHTML = '';
    document.getElementById('threat-distribution-chart').appendChild(svg);
  }

  /**
   * Create SVG pie chart
   */
  createPieChart(distribution) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 180 180');
    svg.setAttribute('width', '180');
    svg.setAttribute('height', '180');

    const total = distribution.critical + distribution.high + distribution.medium + distribution.low;
    const colors = {
      critical: '#ff2e3b',
      high: '#ff9500',
      medium: '#ffd700',
      low: '#4a90e2'
    };

    let currentAngle = -90;
    const segments = [
      { value: distribution.critical, color: colors.critical },
      { value: distribution.high, color: colors.high },
      { value: distribution.medium, color: colors.medium },
      { value: distribution.low, color: colors.low }
    ];

    const centerX = 90, centerY = 90, radius = 70;

    segments.forEach(segment => {
      if (segment.value > 0) {
        const sliceAngle = (segment.value / total) * 360;
        const endAngle = currentAngle + sliceAngle;

        const startRad = (currentAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = centerX + radius * Math.cos(startRad);
        const y1 = centerY + radius * Math.sin(startRad);
        const x2 = centerX + radius * Math.cos(endRad);
        const y2 = centerY + radius * Math.sin(endRad);

        const largeArc = sliceAngle > 180 ? 1 : 0;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
        
        path.setAttribute('d', d);
        path.setAttribute('fill', segment.color);
        path.setAttribute('opacity', '0.8');
        path.setAttribute('stroke', 'rgba(255,255,255,0.2)');
        path.setAttribute('stroke-width', '1');

        svg.appendChild(path);
        currentAngle = endAngle;
      }
    });

    // Center circle
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', centerX);
    circle.setAttribute('cy', centerY);
    circle.setAttribute('r', '35');
    circle.setAttribute('fill', 'rgba(20, 30, 48, 0.9)');
    circle.setAttribute('stroke', 'rgba(255,255,255,0.1)');
    circle.setAttribute('stroke-width', '1');
    svg.appendChild(circle);

    return svg;
  }

  /**
   * Render statistics
   */
  renderStatistics() {
    const stats = this.threatData.statistics;
    
    document.getElementById('avg-threat-score').textContent = 
      (stats.average_threat_score || 0).toFixed(1);
    document.getElementById('active-feeds').textContent = 
      stats.active_feeds || 4;
    document.getElementById('analysis-latency').textContent = 
      (stats.analysis_latency || 0.0).toFixed(2);
    document.getElementById('cache-hit-rate').textContent = 
      (stats.cache_hit_rate || 95.0).toFixed(1);
  }

  /**
   * Update status bar
   */
  updateStatusBar(latency = null) {
    const ipsAnalyzed = this.threatData.topThreats.length;
    const criticalCount = this.threatData.distribution.critical;
    const now = new Date();
    
    document.getElementById('ti-ips-analyzed').textContent = ipsAnalyzed;
    document.getElementById('ti-critical-count').textContent = criticalCount;
    document.getElementById('ti-last-update').textContent = 
      `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

    if (latency) {
      console.log(`[TID] Data update latency: ${latency}ms`);
    }
  }

  /**
   * Update threat distribution
   */
  updateDistribution(threats) {
    this.threatData.distribution = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    threats.forEach(threat => {
      const level = this.getThreatLevel(threat.threat_score);
      if (this.threatData.distribution.hasOwnProperty(level.toLowerCase())) {
        this.threatData.distribution[level.toLowerCase()]++;
      }
    });
  }

  /**
   * Get threat level from score
   */
  getThreatLevel(score) {
    if (score >= 80) return 'CRITICAL';
    if (score >= 60) return 'HIGH';
    if (score >= 40) return 'MEDIUM';
    return 'LOW';
  }

  /**
   * Detect new threats
   */
  detectNewThreats(newThreats) {
    const oldIPs = new Set(this.threatData.topThreats.map(t => t.ip));
    return newThreats.filter(t => !oldIPs.has(t.ip)).slice(0, 3);
  }

  /**
   * Log activity
   */
  logActivity(message, level = 'info') {
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    this.activityLog.push({
      timestamp,
      message,
      level
    });

    // Keep only last 100 items
    if (this.activityLog.length > 100) {
      this.activityLog.shift();
    }

    // Update activity feed
    this.renderActivityFeed();
  }

  /**
   * Render activity feed
   */
  renderActivityFeed() {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;

    feed.innerHTML = this.activityLog.slice(-20).map(item => `
      <div class="activity-item ${item.level}">
        <span class="timestamp">${item.timestamp}</span>
        <span class="message">${item.message}</span>
      </div>
    `).join('');

    // Scroll to bottom
    feed.scrollTop = feed.scrollHeight;
  }

  /**
   * Validate IP address
   */
  isValidIP(ip) {
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipv4Regex.test(ip)) return false;

    const parts = ip.split('.');
    return parts.every(part => {
      const num = parseInt(part, 10);
      return num >= 0 && num <= 255;
    });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('threat-intel-section')) {
    window.threatIntelligenceDashboard = new ThreatIntelligenceDashboard('#threat-intel-section');
  }
});


  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // IP Analysis
    document.getElementById('analyze-ip-btn')?.addEventListener('click', () => {
      this.analyzeIP();
    });

    document.getElementById('analyze-ip-input')?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.analyzeIP();
      }
    });

    // Pagination
    document.getElementById('threats-prev')?.addEventListener('click', () => {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.renderTopThreats();
      }
    });

    document.getElementById('threats-next')?.addEventListener('click', () => {
      this.currentPage++;
      this.renderTopThreats();
    });

    // Click on threat rows to analyze
    document.addEventListener('click', (e) => {
      if (e.target.closest('.analyze-ip-btn')) {
        const ip = e.target.closest('tr')?.querySelector('.ip')?.textContent;
        if (ip) {
          document.getElementById('analyze-ip-input').value = ip;
          this.analyzeIP();
        }
      }
    });
  }

  /**
   * Initial data load
   */
  async initialLoad() {
    this.logActivity('System initializing...', 'info');
    
    try {
      const [topThreats, stats] = await Promise.all([
        this.fetchTopThreats(),
        this.fetchStatistics()
      ]);

      this.threatData.topThreats = topThreats;
      this.threatData.statistics = stats;
      this.updateDistribution(topThreats);
      
      this.updateStatusBar();
      this.renderTopThreats();
      this.renderDistribution();
      this.renderStatistics();
      
      this.logActivity('Threat intelligence system online', 'info');
    } catch (error) {
      console.error('[TID] Initial load error:', error);
      this.logActivity('Error loading threat data', 'critical');
    }
  }

  /**
   * Start periodic updates
   */
  startPeriodicUpdates() {
    setInterval(() => {
      this.updateThreatData();
    }, this.updateInterval);
  }

  /**
   * Update threat data
   */
  async updateThreatData() {
    if (this.isUpdating) return;
    
    this.isUpdating = true;
    
    try {
      const startTime = performance.now();
      
      const [topThreats, stats] = await Promise.all([
        this.fetchTopThreats(),
        this.fetchStatistics()
      ]);

      const endTime = performance.now();
      const latency = (endTime - startTime).toFixed(2);

      // Check for new threats
      const newThreats = this.detectNewThreats(topThreats);
      if (newThreats.length > 0) {
        newThreats.forEach(threat => {
          this.logActivity(`New threat detected: ${threat.ip} (${threat.level})`, threat.level.toLowerCase());
        });
      }

      this.threatData.topThreats = topThreats;
      this.threatData.statistics = stats;
      this.updateDistribution(topThreats);
      
      this.updateStatusBar(latency);
      this.renderTopThreats();
      this.renderDistribution();
      this.renderStatistics();
      
    } catch (error) {
      console.error('[TID] Update error:', error);
      this.logActivity('Failed to update threat data', 'high');
    } finally {
      this.isUpdating = false;
    }
  }

  /**
   * Fetch top threats
   */
  async fetchTopThreats(limit = 50) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/top-threats?limit=${limit}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      return data.threats || [];
    } catch (error) {
      console.error('[TID] Error fetching top threats:', error);
      return [];
    }
  }

  /**
   * Fetch statistics
   */
  async fetchStatistics() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/statistics`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      return data.statistics || {};
    } catch (error) {
      console.error('[TID] Error fetching statistics:', error);
      return {};
    }
  }

  /**
   * Analyze a specific IP
   */
  async analyzeIP() {
    const input = document.getElementById('analyze-ip-input');
    const ip = input?.value?.trim();

    if (!ip) {
      this.logActivity('Invalid IP address provided', 'low');
      return;
    }

    if (!this.isValidIP(ip)) {
      this.logActivity(`Invalid IP format: ${ip}`, 'medium');
      return;
    }

    try {
      this.logActivity(`Analyzing IP: ${ip}`, 'info');
      
      const response = await fetch(`${this.apiBaseUrl}/analyze?ip=${ip}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const analysis = await response.json();
      this.displayAnalysis(analysis);
      
      this.logActivity(`Analysis complete for ${ip}`, 'info');
    } catch (error) {
      console.error('[TID] Analysis error:', error);
      this.logActivity(`Failed to analyze ${ip}`, 'high');
    }
  }

  /**
   * Display IP analysis result
   */
  displayAnalysis(analysis) {
    const resultDiv = document.getElementById('analysis-result');
    
    if (!analysis.success) {
      resultDiv.classList.add('hidden');
      return;
    }

    const data = analysis.analysis || {};
    
    // Update header
    document.getElementById('result-ip').textContent = data.ip || '--';
    const threatLevel = this.getThreatLevel(data.composite_score || 0);
    document.getElementById('result-threat-level').textContent = threatLevel;
    document.getElementById('result-threat-level').className = `result-threat-level ${threatLevel.toLowerCase()}`;

    // Update reputation
    const repScore = data.reputation_score || 0;
    document.getElementById('result-rep-score').textContent = `${repScore.toFixed(1)}/100`;
    document.getElementById('result-rep-bar').style.width = `${repScore}%`;

    // Update geolocation
    document.getElementById('result-geo-country').textContent = data.geolocation?.country || 'Unknown';
    const geoScore = data.geolocation?.risk_score || 0;
    document.getElementById('result-geo-score').textContent = `${geoScore.toFixed(1)}/100`;
    document.getElementById('result-geo-bar').style.width = `${geoScore}%`;
    document.getElementById('result-geo-isp').textContent = data.geolocation?.isp || 'Unknown';

    // Update threat feeds
    this.renderFeedsList(data.threat_feeds || []);

    // Update trends
    document.getElementById('result-trend-count').textContent = data.trends?.total_attacks || 0;
    document.getElementById('result-trend-velocity').textContent = `${(data.trends?.velocity || 0).toFixed(1)}/hour`;
    document.getElementById('result-trend-consistency').textContent = `${(data.trends?.consistency || 0).toFixed(1)}%`;

    // Update composite score
    const compositeScore = data.composite_score || 0;
    document.getElementById('composite-score').textContent = compositeScore.toFixed(0);

    // Update recommendations
    this.renderRecommendations(data.recommendations || []);

    // Show result
    resultDiv.classList.remove('hidden');
  }

  /**
   * Render feeds list
   */
  renderFeedsList(feeds) {
    const container = document.getElementById('result-feeds-list');
    container.innerHTML = '';

    if (!feeds || feeds.length === 0) {
      container.innerHTML = '<div class="feed-item"><span class="feed-name">No threats detected</span></div>';
      return;
    }

    feeds.forEach(feed => {
      const item = document.createElement('div');
      item.className = 'feed-item';
      item.innerHTML = `
        <span class="feed-name">${feed.source || 'Unknown'}</span>
        <span class="feed-status ${feed.matched ? 'matched' : 'unmatched'}">●</span>
      `;
      container.appendChild(item);
    });
  }

  /**
   * Render recommendations
   */
  renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
      const item = document.createElement('li');
      item.className = 'recommendation-item';
      item.innerHTML = '<span class="text">No specific recommendations</span>';
      container.appendChild(item);
      return;
    }

    recommendations.forEach(rec => {
      const item = document.createElement('li');
      item.className = 'recommendation-item';
      item.innerHTML = `
        <span class="icon">→</span>
        <span class="text">${rec}</span>
      `;
      container.appendChild(item);
    });
  }

  /**
   * Render top threats table
   */
  renderTopThreats() {
    const tbody = document.getElementById('top-threats-tbody');
    if (!tbody) return;

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pageThreats = this.threatData.topThreats.slice(start, end);

    if (pageThreats.length === 0) {
      tbody.innerHTML = '<tr class="loading"><td colspan="5" class="text-center">No threats detected</td></tr>';
      this.updatePaginationButtons();
      return;
    }

    tbody.innerHTML = pageThreats.map((threat, index) => {
      const threatLevel = this.getThreatLevel(threat.threat_score);
      const score = threat.threat_score || 0;

      return `
        <tr class="threat-row">
          <td class="rank">${start + index + 1}</td>
          <td class="ip">${threat.ip || '--'}</td>
          <td class="score">
            <div class="score-bar">
              <div class="score-fill" style="width: ${score}%"></div>
            </div>
            <span class="score-text">${score.toFixed(1)}</span>
          </td>
          <td class="level">
            <span class="level-badge ${threatLevel.toLowerCase()}">${threatLevel}</span>
          </td>
          <td class="action">
            <button class="btn-tiny analyze-ip-btn">Analyze</button>
          </td>
        </tr>
      `;
    }).join('');

    this.updatePaginationButtons();
  }

  /**
   * Update pagination buttons
   */
  updatePaginationButtons() {
    const prevBtn = document.getElementById('threats-prev');
    const nextBtn = document.getElementById('threats-next');
    const pageInfo = document.getElementById('threats-page');

    if (prevBtn) prevBtn.disabled = this.currentPage === 1;
    if (nextBtn) {
      const maxPage = Math.ceil(this.threatData.topThreats.length / this.pageSize);
      nextBtn.disabled = this.currentPage >= maxPage;
    }
    if (pageInfo) pageInfo.textContent = `Page ${this.currentPage}`;
  }

  /**
   * Render threat distribution pie chart
   */
  renderDistribution() {
    const dist = this.threatData.distribution;
    const total = dist.critical + dist.high + dist.medium + dist.low;

    if (total === 0) {
      document.getElementById('threat-distribution-chart').innerHTML = 
        '<div style="text-align: center; padding: 50px 0; color: rgba(255,255,255,0.5);">No data</div>';
      return;
    }

    // Update legend counts
    document.querySelector('[data-level="CRITICAL"]').textContent = dist.critical;
    document.querySelector('[data-level="HIGH"]').textContent = dist.high;
    document.querySelector('[data-level="MEDIUM"]').textContent = dist.medium;
    document.querySelector('[data-level="LOW"]').textContent = dist.low;

    // Create SVG pie chart
    const svg = this.createPieChart(dist);
    document.getElementById('threat-distribution-chart').innerHTML = '';
    document.getElementById('threat-distribution-chart').appendChild(svg);
  }

  /**
   * Create SVG pie chart
   */
  createPieChart(distribution) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 180 180');
    svg.setAttribute('width', '180');
    svg.setAttribute('height', '180');

    const total = distribution.critical + distribution.high + distribution.medium + distribution.low;
    const colors = {
      critical: '#ff2e3b',
      high: '#ff9500',
      medium: '#ffd700',
      low: '#4a90e2'
    };

    let currentAngle = -90;
    const segments = [
      { value: distribution.critical, color: colors.critical },
      { value: distribution.high, color: colors.high },
      { value: distribution.medium, color: colors.medium },
      { value: distribution.low, color: colors.low }
    ];

    const centerX = 90, centerY = 90, radius = 70;

    segments.forEach(segment => {
      if (segment.value > 0) {
        const sliceAngle = (segment.value / total) * 360;
        const endAngle = currentAngle + sliceAngle;

        const startRad = (currentAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = centerX + radius * Math.cos(startRad);
        const y1 = centerY + radius * Math.sin(startRad);
        const x2 = centerX + radius * Math.cos(endRad);
        const y2 = centerY + radius * Math.sin(endRad);

        const largeArc = sliceAngle > 180 ? 1 : 0;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
        
        path.setAttribute('d', d);
        path.setAttribute('fill', segment.color);
        path.setAttribute('opacity', '0.8');
        path.setAttribute('stroke', 'rgba(255,255,255,0.2)');
        path.setAttribute('stroke-width', '1');

        svg.appendChild(path);
        currentAngle = endAngle;
      }
    });

    // Center circle
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', centerX);
    circle.setAttribute('cy', centerY);
    circle.setAttribute('r', '35');
    circle.setAttribute('fill', 'rgba(20, 30, 48, 0.9)');
    circle.setAttribute('stroke', 'rgba(255,255,255,0.1)');
    circle.setAttribute('stroke-width', '1');
    svg.appendChild(circle);

    return svg;
  }

  /**
   * Render statistics
   */
  renderStatistics() {
    const stats = this.threatData.statistics;
    
    document.getElementById('avg-threat-score').textContent = 
      (stats.average_threat_score || 0).toFixed(1);
    document.getElementById('active-feeds').textContent = 
      stats.active_feeds || 4;
    document.getElementById('analysis-latency').textContent = 
      (stats.analysis_latency || 0.0).toFixed(2);
    document.getElementById('cache-hit-rate').textContent = 
      (stats.cache_hit_rate || 95.0).toFixed(1);
  }

  /**
   * Update status bar
   */
  updateStatusBar(latency = null) {
    const ipsAnalyzed = this.threatData.topThreats.length;
    const criticalCount = this.threatData.distribution.critical;
    const now = new Date();
    
    document.getElementById('ti-ips-analyzed').textContent = ipsAnalyzed;
    document.getElementById('ti-critical-count').textContent = criticalCount;
    document.getElementById('ti-last-update').textContent = 
      `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

    if (latency) {
      console.log(`[TID] Data update latency: ${latency}ms`);
    }
  }

  /**
   * Update threat distribution
   */
  updateDistribution(threats) {
    this.threatData.distribution = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    threats.forEach(threat => {
      const level = this.getThreatLevel(threat.threat_score);
      if (this.threatData.distribution.hasOwnProperty(level.toLowerCase())) {
        this.threatData.distribution[level.toLowerCase()]++;
      }
    });
  }

  /**
   * Get threat level from score
   */
  getThreatLevel(score) {
    if (score >= 80) return 'CRITICAL';
    if (score >= 60) return 'HIGH';
    if (score >= 40) return 'MEDIUM';
    return 'LOW';
  }

  /**
   * Detect new threats
   */
  detectNewThreats(newThreats) {
    const oldIPs = new Set(this.threatData.topThreats.map(t => t.ip));
    return newThreats.filter(t => !oldIPs.has(t.ip)).slice(0, 3);
  }

  /**
   * Log activity
   */
  logActivity(message, level = 'info') {
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    this.activityLog.push({
      timestamp,
      message,
      level
    });

    // Keep only last 100 items
    if (this.activityLog.length > 100) {
      this.activityLog.shift();
    }

    // Update activity feed
    this.renderActivityFeed();
  }

  /**
   * Render activity feed
   */
  renderActivityFeed() {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;

    feed.innerHTML = this.activityLog.slice(-20).map(item => `
      <div class="activity-item ${item.level}">
        <span class="timestamp">${item.timestamp}</span>
        <span class="message">${item.message}</span>
      </div>
    `).join('');

    // Scroll to bottom
    feed.scrollTop = feed.scrollHeight;
  }

  /**
   * Validate IP address
   */
  isValidIP(ip) {
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipv4Regex.test(ip)) return false;

    const parts = ip.split('.');
    return parts.every(part => {
      const num = parseInt(part, 10);
      return num >= 0 && num <= 255;
    });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('threat-intel-container')) {
    window.threatIntelligenceDashboard = new ThreatIntelligenceDashboard();
  }
});
