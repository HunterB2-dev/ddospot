# 🍯 DDoSPoT - Complete Project Documentation

**Version:** 2.0 | **Status:** ✅ Production Ready | **Last Updated:** February 3, 2026

---

## 📖 Table of Contents

1. [What is DDoSPoT?](#what-is-ddospot)
2. [Quick Start (5 Minutes)](#quick-start)
3. [System Overview](#system-overview)
4. [Installation & Setup](#installation--setup)
5. [Project Structure](#project-structure)
6. [Core Features](#core-features)
7. [Running the Honeypot](#running-the-honeypot)
8. [Dashboard & Monitoring](#dashboard--monitoring)
9. [API Reference](#api-reference)
10.[Configuration](#configuration)
11.[Security](#security)
12.[Troubleshooting](#troubleshooting)
13.[Advanced Features](#advanced-features)
14.[FAQ](#faq)

---

## 🎯 What is DDoSPoT?

### In Simple Terms
DDoSPoT is a **DDoS honeypot** - a fake vulnerable server that attracts and logs attacks. Instead of protecting a real system, it sits on the internet looking like an easy target. When attackers find it and try to break in, DDoSPoT records everything they do.

### What Makes It Special?
- **11 Different Services** - Mimics real servers (HTTP, SSH, FTP, Telnet, MySQL, PostgreSQL, Redis, MongoDB, DNS, NTP, SSDP)
- **Smart Detection** - Uses machine learning to identify attack patterns
- **Beautiful Dashboard** - See attacks happening in real-time on a world map
- **REST API** - Integrate with your monitoring systems
- **Automatic Alerts** - Get notified of critical events via email or Slack
- **Production-Ready** - Docker support, high performance, secure

### Why Use It?
1. **Understand Attack Patterns** - See what attackers target and how they work
2. **Threat Intelligence** - Get IP reputation data and geographic attack sources
3. **Early Warning System** - Detect new threats before they hit real systems
4. **Educational** - Learn about network security and common vulnerabilities
5. **No Risk** - It's a honeypot, not a real service

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites
- Linux/Mac/Windows (with WSL)
- Python 3.8+
- ~1GB disk space
- Internet connection (for geolocation data)

### Step 1: Clone & Install (2 minutes)
```bash
# Clone the project
git clone <https://github.com/HunterB2-dev/ddospot>
cd ddospot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure (1 minute)
```bash
# Copy example configs
cp config/config.example.json config/config.json
cp config/alert_config.example.json config/alert_config.json

# Edit if you want custom settings
nano config/config.json  # Optional
```

### Step 3: Run (1 minute)
```bash
# Terminal 1: Start the honeypot
python start-honeypot.py

# Terminal 2: Start the dashboard (in new terminal)
python start-dashboard.py

# Open in browser
# Dashboard: http://localhost:5000
# API: http://localhost:5000/api/
```

**That's it!** Your honeypot is now running. 🎉

---

## 🏗️ System Overview

### Architecture Diagram
```
┌──────────────────────────────────────────────────────────────┐
│                     INTERNET / ATTACKERS                     │
└────────────┬─────────────────────────────────┬───────────────┘
             │                                 │
             │ Sends Attack Traffic            │
             ▼                                 ▼
    ┌────────────────┐             ┌────────────────────┐
    │  HONEYPOT      │             │  WEB DASHBOARD     │
    │  (app/main.py) │◄────────────│  (app/dashboard.py)│
    │                │             │                    │
    │ 11 Services:   │             │ Real-time Stats    │
    │ - HTTP         │             │ World Map          │
    │ - SSH          │             │ Attack Timeline    │
    │ - MySQL        │             │ Alert Rules        │
    │ - PostgreSQL   │             │ API Tokens         │
    │ - Redis        │             └────────────────────┘
    │ - MongoDB      │
    │ - FTP, Telnet  │
    │ - DNS, NTP     │
    │ - SSDP         │
    └────────┬───────┘
             │
             │ Logs Events
             ▼
    ┌────────────────────┐
    │  SQLite Database   │
    │  (honeypot.db)     │
    │                    │
    │ Tables:            │
    │ - events           │
    │ - attacks          │
    │ - ips              │
    │ - protocols        │
    │ - geolocations     │
    │ - anomalies        │
    │ - predictions      │
    │ - patterns         │
    └────────────────────┘
             ▲
             │
    ┌────────┴────────┐
    │   ML MODELS     │
    │ (ml/ folder)    │
    │                 │
    │ - Anomaly       │
    │   Detection     │
    │ - Attack        │
    │   Prediction    │
    │ - Pattern       │
    │   Learning      │
    │ - Feature       │
    │   Extraction    │
    └─────────────────┘
```

### How It Works (Step by Step)

1. **Attacker Connects** → Sends traffic to one of the honeypot's ports
2. **Service Response** → Honeypot pretends to be vulnerable service (HTTP, SSH, etc.)
3. **Attack Logging** → Records all interaction details
4. **Geolocation** → Looks up attacker's IP address location
5. **ML Analysis** → Analyzes patterns to identify attack type
6. **Database Storage** → Saves to SQLite database
7. **Alerts** → Triggers alerts (email, Slack, webhooks)
8. **Dashboard Update** → Displays on real-time dashboard

---

## 🔧 Installation & Setup

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Linux, macOS, or Windows (WSL2) |
| **Python** | 3.8 or higher |
| **Memory** | 512 MB minimum (1GB recommended) |
| **Disk** | 1 GB for code, grows with attacks |
| **Network** | Public IP (for internet-facing attacks) |
| **Internet** | Required for geolocation data |

### Full Installation

#### Option 1: Local Development
```bash
# 1. Clone repository
git clone <repo-url>
cd ddospot

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy configurations
cp config/config.example.json config/config.json
cp config/alert_config.example.json config/alert_config.json

# 5. Run honeypot (in terminal 1)
python start-honeypot.py

# 6. Run dashboard (in terminal 2)
python start-dashboard.py

# 7. Access dashboard
open http://localhost:5000
```

#### Option 2: Docker (Production)
```bash
# Run with Docker Compose
docker-compose -f docker-compose-prod.yml up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

#### Option 3: Systemd Service (Linux)
```bash
# Install as system service
sudo bash scripts/setup-production.sh

# Start service
sudo systemctl start ddospot-honeypot
sudo systemctl start ddospot-dashboard

# View logs
journalctl -u ddospot-honeypot -f
```

### Configuration

#### Main Config (config/config.json)
```json
{
  "debug": false,
  "log_level": "INFO",
  "database": {
    "path": "logs/honeypot.db"
  },
  "services": {
    "http": {"port": 8080, "enabled": true},
    "ssh": {"port": 2222, "enabled": true},
    "ftp": {"port": 21, "enabled": true},
    "mysql": {"port": 3306, "enabled": true},
    "postgresql": {"port": 5432, "enabled": true},
    "redis": {"port": 6379, "enabled": true},
    "mongodb": {"port": 27017, "enabled": true},
    "dns": {"port": 53, "enabled": true},
    "ntp": {"port": 123, "enabled": true},
    "ssdp": {"port": 1900, "enabled": true}
  },
  "geolocation": {
    "enabled": true,
    "provider": "maxmind"
  },
  "alerts": {
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "from": "your@email.com"
    },
    "slack": {
      "enabled": false,
      "webhook_url": "https://hooks.slack.com/..."
    }
  }
}
```

#### Alert Rules (config/alert_config.json)
```json
{
  "rules": [
    {
      "name": "High Rate Attack",
      "condition": "attack_rate > 100",
      "action": "email,slack"
    },
    {
      "name": "New Country Attack",
      "condition": "country_change",
      "action": "email"
    }
  ]
}
```

---

## 📁 Project Structure

### Main Folders

```
ddospot/
│
├── 🍯 app/                          # Main Application
│   ├── main.py                      # Honeypot entry point
│   ├── dashboard.py                 # Web dashboard server
│   ├── cli.py                       # Command-line tools
│   └── maintenance.py               # Background maintenance
│
├── 🔧 core/                         # Core Honeypot Logic
│   ├── server.py                    # Network server (TCP/UDP)
│   ├── database.py                  # SQLite operations
│   ├── detection.py                 # Attack detection
│   ├── geolocation.py               # IP geolocation lookup
│   ├── protocol_handlers.py         # Service protocols
│   ├── responses.py                 # Protocol responses
│   ├── config.py                    # Configuration loader
│   └── state.py                     # State management
│
├── 🤖 ml/                           # Machine Learning
│   ├── features.py                  # Feature extraction (28 features)
│   ├── detection.py                 # Anomaly detection
│   ├── prediction.py                # Attack prediction
│   ├── patterns.py                  # Pattern discovery
│   ├── training.py                  # Model training pipeline
│   ├── api.py                       # ML REST endpoints
│   └── model.pkl                    # Trained model file
│
├── 📊 telemetry/                    # Monitoring & Alerts
│   ├── alerts.py                    # Alert management
│   ├── logger.py                    # Logging system
│   ├── metrics.py                   # Performance metrics
│   ├── prometheus_metrics.py        # Prometheus exporter
│   ├── ratelimit.py                 # Rate limiting
│   └── stats.py                     # Statistics
│
├── 🧪 tests/                        # Test Suite
│   ├── test_*.py                    # Unit tests
│   ├── test_ml_integration.py       # ML integration tests
│   └── comprehensive_test.py        # Full system tests
│
├── 📝 static/                       # Web Frontend Assets
│   ├── dashboard.js                 # Dashboard JavaScript
│   ├── dashboard.css                # Dashboard styles
│   ├── mobile-dashboard.js          # Mobile PWA support
│   └── settings.js                  # Settings page
│
├── 🎨 templates/                    # HTML Templates
│   ├── index.html                   # Dashboard UI
│   ├── profile.html                 # User profile
│   └── settings.html                # Settings page
│
├── 🛠️ tools/                        # Utility Scripts
│   ├── populate_demo.py             # Generate demo data
│   ├── query_database.py            # Database queries
│   ├── verify_security.py           # Security checks
│   └── run_tests.py                 # Run test suite
│
├── 📚 scripts/                      # Bash Scripts
│   ├── backup.sh                    # Backup database
│   ├── restore.sh                   # Restore database
│   ├── setup-production.sh          # Production setup
│   ├── deploy-production.sh         # Deploy to production
│   └── enable-security.sh           # Security hardening
│
├── ⚙️ monitoring/                   # Monitoring Configs
│   ├── prometheus.yml               # Prometheus config
│   ├── alertmanager.yml             # Alert manager config
│   ├── grafana-dashboard.json       # Grafana dashboard
│   └── README.md                    # Setup instructions
│
├── 🐳 docker/                       # Docker Setup
│   ├── Dockerfile                   # Docker image
│   └── docker-compose.yml           # Docker Compose
│
├── 🔒 systemd/                      # Linux Services
│   ├── ddospot-honeypot.service     # Honeypot service
│   └── ddospot-dashboard.service    # Dashboard service
│
├── ⚙️ config/                       # Configuration (⚠️ Secrets!)
│   ├── config.example.json          # Template
│   ├── config.json                  # Live config (git-ignored)
│   └── alert_config.json            # Alert rules
│
├── 📖 docs/                         # Documentation
│   ├── API_DOCUMENTATION.md         # REST API docs
│   ├── CLI_USAGE.md                 # CLI commands
│   ├── SECURITY_HARDENING.md        # Security guide
│   ├── DOCKER_DEPLOYMENT.md         # Docker guide
│   ├── TESTING_GUIDE.md             # Testing guide
│   └── FOLDER_GUIDE.md              # Folder organization
│
├── 📋 logs/                         # Runtime Data (⚠️ Don't commit!)
│   ├── honeypot.db                  # Event database
│   └── honeypot.log                 # Log files
│
├── 📄 README.md                     # Main documentation
├── 📄 QUICK_START.md                # 5-minute guide
├── 📄 requirements.txt              # Python dependencies
├── 🐍 start-honeypot.py             # ⭐ Run honeypot
├── 🌐 start-dashboard.py            # ⭐ Run dashboard
└── 📄 LICENSE                       # License
```

### Key Files Explained

| File | Purpose | How to Use |
|------|---------|-----------|
| **start-honeypot.py** | Starts the honeypot server | `python start-honeypot.py` |
| **start-dashboard.py** | Starts web dashboard | `python start-dashboard.py` |
| **config/config.json** | Main configuration | Edit settings here |
| **logs/honeypot.db** | Event database | Query with SQLite3 |
| **ml/model.pkl** | ML model file | Auto-loads when dashboard starts |
| **requirements.txt** | Python packages | `pip install -r requirements.txt` |

---

## ✨ Core Features

### 1. **11 Service Protocols** 🔌
Emulates these vulnerable services to attract attackers:

| Protocol | Port | Purpose |
|----------|------|---------|
| **HTTP** | 8080 | Web server attacks |
| **SSH** | 2222 | Brute-force attempts |
| **FTP** | 21 | File transfer attacks |
| **Telnet** | 23 | Remote access attempts |
| **MySQL** | 3306 | Database scanning |
| **PostgreSQL** | 5432 | Database attacks |
| **Redis** | 6379 | Cache exploitation |
| **MongoDB** | 27017 | NoSQL database attacks |
| **DNS** | 53 | DNS amplification attacks |
| **NTP** | 123 | NTP reflection attacks |
| **SSDP** | 1900 | Service discovery attacks |

### 2. **Real-Time Dashboard** 📊
Visual display of attacks as they happen:
- **World Map** - See attack sources geographically
- **Live Timeline** - Watch attacks in real-time
- **Attack Stats** - Total attacks, unique IPs, top countries
- **Attack Breakdown** - Attacks by protocol and type
- **Performance Metrics** - Response times, throughput

### 3. **Machine Learning** 🤖
Advanced threat detection using AI:
- **Anomaly Detection** - Detects unusual patterns
- **Attack Prediction** - Predicts attack types
- **Pattern Learning** - Discovers attack patterns
- **Feature Extraction** - Analyzes 28+ network features
- **Training Pipeline** - Continuously improves with new data

### 4. **REST API** 🔌
42+ endpoints for integration:
- **Events API** - Query attack events
- **Statistics API** - Get aggregated data
- **Alerts API** - Manage alerts
- **Configuration API** - Update settings
- **ML API** - Use prediction models
- **Authentication** - Token-based access control
- **Rate Limiting** - Prevent abuse

### 5. **Alert System** 🚨
Get notified of critical events:
- **Email Alerts** - SMTP support
- **Slack Integration** - Send to Slack channels
- **Webhooks** - Custom HTTP callbacks
- **Custom Rules** - Define alert conditions
- **Thresholds** - Alert on attack rates

### 6. **Geolocation** 🌍
Know where attacks come from:
- **Country Detection** - Identify attacker location
- **ISP Information** - Get network provider details
- **Autonomous System** - Know network owner
- **Coordinates** - Exact latitude/longitude
- **Visualization** - See attacks on map

### 7. **Database** 💾
Comprehensive event logging:
- **SQLite3** - Built-in, no setup needed
- **8 Tables** - Events, attacks, IPs, protocols, etc.
- **Full History** - Never loses data
- **Easy Queries** - SQL access to all events
- **Export** - Extract data for analysis

### 8. **Docker Support** 🐳
Production deployment made easy:
- **Docker Image** - Pre-built container
- **Docker Compose** - Multi-container setup
- **Environment Variables** - External config
- **Health Checks** - Auto-restart on failure
- **Production Ready** - Recommended for deployments

### 9. **Monitoring** 📈
Integration with observability tools:
- **Prometheus Metrics** - /metrics endpoint
- **Grafana Dashboards** - Pre-built visualizations
- **Alert Manager** - Centralized alerting
- **System Metrics** - CPU, memory, disk usage
- **Performance Metrics** - Honeypot performance

### 10. **Security** 🔒
Built-in protection mechanisms:
- **Token Authentication** - API key-based auth
- **Rate Limiting** - DDoS protection
- **SSL/TLS** - HTTPS support
- **CORS** - Cross-origin control
- **Input Validation** - Sanitize all inputs

### 11. **CLI Tools** 💻
Command-line interface for management:
```bash
# Query events
python app/cli.py query --type http --limit 100

# Generate reports
python app/cli.py report --format json

# Manage alerts
python app/cli.py alert --list

# Export data
python app/cli.py export --format csv
```

### 12. **Mobile Dashboard** 📱
Progressive Web App (PWA) support:
- **Responsive Design** - Works on all devices
- **Offline Support** - View cached data offline
- **Home Screen** - Install like native app
- **Touch Optimized** - Mobile-friendly interface

---

## 🚀 Running the Honeypot

### Starting the Honeypot

#### Method 1: Direct Python
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the honeypot
python start-honeypot.py
```

Expected output:
```
[INFO] Starting DDoSPot honeypot...
[INFO] TCP server started on 0.0.0.0:8080 (HTTP)
[INFO] TCP server started on 0.0.0.0:2222 (SSH)
[INFO] TCP server started on 0.0.0.0:21 (FTP)
[INFO] TCP server started on 0.0.0.0:23 (Telnet)
[INFO] TCP server started on 0.0.0.0:3306 (MySQL)
[INFO] TCP server started on 0.0.0.0:5432 (PostgreSQL)
[INFO] TCP server started on 0.0.0.0:6379 (Redis)
[INFO] TCP server started on 0.0.0.0:27017 (MongoDB)
[INFO] UDP socket bound on 0.0.0.0:53 (DNS)
[INFO] UDP socket bound on 0.0.0.0:123 (NTP)
[INFO] UDP socket bound on 0.0.0.0:1900 (SSDP)
[INFO] Honeypot is running. Press Ctrl+C to stop.
```

#### Method 2: Docker
```bash
docker-compose -f docker-compose-prod.yml up -d
```

#### Method 3: Systemd Service
```bash
sudo systemctl start ddospot-honeypot
sudo systemctl status ddospot-honeypot
```

### Starting the Dashboard

#### In a New Terminal
```bash
source .venv/bin/activate
python start-dashboard.py
```

Expected output:
```
[INFO] Loading ML model...
[INFO] ML model loaded successfully
[INFO] Starting dashboard server...
[INFO] Flask server starting on 0.0.0.0:5000
[INFO] Open browser to http://localhost:5000
```

#### Access the Dashboard
- **Local**: http://localhost:5000
- **Remote**: http://your-server-ip:5000
- **Mobile**: http://your-server-ip:5000 (PWA)

### Monitoring Logs

#### View Live Logs
```bash
# Honeypot logs
tail -f logs/honeypot.log

# Dashboard logs
tail -f logs/dashboard.log
```

#### Check Process Status
```bash
# Check if running
ps aux | grep python

# Check port usage
netstat -tulpn | grep python
```

### Stopping the Honeypot

#### Method 1: Keyboard Interrupt
```bash
# In the running terminal
Ctrl + C
```

#### Method 2: Kill Process
```bash
pkill -f start-honeypot.py
```

#### Method 3: Systemd
```bash
sudo systemctl stop ddospot-honeypot
```

#### Method 4: Docker
```bash
docker-compose -f docker-compose-prod.yml down
```

---

## 📊 Dashboard & Monitoring

### Dashboard Overview

The web dashboard provides real-time attack visualization:

```
┌─ DDoSPoT Dashboard ─────────────────────────────────┐
│                                                     │
│  [🌍 World Map] - Attack Locations                  │
│                                                     │
│  📊 Stats:                                          │
│  • Total Attacks: 2,847                             │
│  • Unique IPs: 156                                  │
│  • Top Country: China (34%)                         │
│  • Attack Types: HTTP, SSH, DNS                     │
│                                                     │
│  [Timeline] - Attacks Over Time                     │
│                                                     │
│  [Recent Events]                                    │
│  • 12:34 SSH 192.168.1.1 - Brute force              │
│  • 12:33 HTTP 10.0.0.1 - Scanning                   │
│  • 12:32 Redis 172.16.0.1 - Exploitation            │
│                                                     │
│  [⚙️ Settings] [📈 Reports] [🔔 Alerts] [🔑 API]    │
└─────────────────────────────────────────────────────┘
```

### Key Dashboard Features

1. **World Map**
   - Red dots = attack sources
   - Cluster view for multiple attacks
   - Click for details
   - Real-time updates

2. **Statistics**
   - Total attacks
   - Unique attackers
   - Top countries
   - Attack breakdown by type
   - Attack rate (per minute)

3. **Timeline**
   - Attacks over time
   - Filter by protocol/country
   - Zoom and pan
   - Export to image

4. **Event List**
   - Real-time event stream
   - Search and filter
   - Copy to clipboard
   - Export events

5. **Alerts**
   - View active alerts
   - Create alert rules
   - Test alerts
   - View alert history

6. **Settings**
   - Update configuration
   - Manage services
   - Configure alerts
   - API tokens

7. **API Documentation**
   - Interactive API explorer
   - Request examples
   - Response schemas
   - Rate limit info

### API Tokens

Generate API tokens for programmatic access:

```bash
# In dashboard, go to Settings > API Tokens

# Create new token
curl -X POST http://localhost:5000/api/tokens \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d {"name": "Integration Token"}

# Use token in requests
curl -H "Authorization: Bearer token_abc123" \
  http://localhost:5000/api/events
```

---

## 🔌 API Reference

### Quick API Overview

**Base URL:** `http://localhost:5000/api`

**Authentication:** Token-based (Bearer token in Authorization header)

**Rate Limit:** 100 requests/minute per token

### Event Endpoints

#### Get All Events
```bash
GET /api/events
Query params:
  - limit: 100
  - offset: 0
  - protocol: http (optional)
  - country: US (optional)
  - start_time: 2026-02-03 (optional)
  - end_time: 2026-02-04 (optional)

Example:
curl http://localhost:5000/api/events?limit=10
```

#### Get Event Details
```bash
GET /api/events/{id}

Example:
curl http://localhost:5000/api/events/123
```

### Statistics Endpoints

#### Get Overall Stats
```bash
GET /api/statistics

Returns:
{
  "total_events": 2847,
  "total_unique_ips": 156,
  "total_countries": 42,
  "events_per_minute": 3.2,
  "top_protocols": [
    {"protocol": "http", "count": 1200},
    {"protocol": "ssh", "count": 890},
    {"protocol": "dns", "count": 757}
  ],
  "top_countries": [
    {"country": "China", "count": 968},
    {"country": "Russia", "count": 456},
    {"country": "USA", "count": 234}
  ]
}
```

#### Get Protocol Stats
```bash
GET /api/statistics/protocols

Example:
curl http://localhost:5000/api/statistics/protocols
```

#### Get Geographic Stats
```bash
GET /api/statistics/geography

Returns:
{
  "countries": [
    {"code": "CN", "name": "China", "count": 968, "lat": 35.86, "lon": 104.19},
    ...
  ]
}
```

### IP Reputation Endpoints

#### Get IP Details
```bash
GET /api/ip/{ip_address}

Returns:
{
  "ip": "192.168.1.1",
  "country": "China",
  "city": "Beijing",
  "isp": "China Telecom",
  "asn": "AS4134",
  "threat_level": "high",
  "last_seen": "2026-02-03T12:34:56Z",
  "attack_count": 12,
  "protocols_used": ["http", "ssh", "dns"]
}
```

#### Get Top IPs
```bash
GET /api/statistics/top-ips?limit=10

Returns:
{
  "ips": [
    {"ip": "192.168.1.1", "count": 847, "country": "China"},
    ...
  ]
}
```

### Alert Endpoints

#### Get All Alerts
```bash
GET /api/alerts

Returns:
{
  "alerts": [
    {
      "id": 1,
      "name": "High HTTP Rate",
      "condition": "protocol=http AND rate>100",
      "enabled": true,
      "actions": ["email", "slack"]
    },
    ...
  ]
}
```

#### Create Alert
```bash
POST /api/alerts
Content-Type: application/json

{
  "name": "Suspicious SSH",
  "condition": "protocol=ssh AND country=RU",
  "actions": ["email", "slack"],
  "enabled": true
}
```

#### Update Alert
```bash
PUT /api/alerts/{id}
Content-Type: application/json

{
  "enabled": false
}
```

#### Delete Alert
```bash
DELETE /api/alerts/{id}
```

### ML Prediction Endpoints

#### Predict Attack Type
```bash
POST /api/ml/predict
Content-Type: application/json

{
  "features": [0.5, 0.3, 0.8, ...],  // 28 features
  "source_ip": "192.168.1.1"
}

Returns:
{
  "attack_probability": 0.89,
  "predicted_type": "HTTP Flood",
  "confidence": 0.95,
  "top_features": ["packet_rate", "payload_size"]
}
```

#### Detect Anomaly
```bash
POST /api/ml/detect-anomaly
Content-Type: application/json

{
  "features": [0.5, 0.3, 0.8, ...]
}

Returns:
{
  "is_anomaly": true,
  "anomaly_score": 0.87,
  "detection_method": "ensemble"
}
```

### Complete API Documentation

For the full list of 42+ endpoints with detailed examples, see:
- **docs/API_DOCUMENTATION.md** - Complete reference
- **Dashboard API Explorer** - http://localhost:5000/api/docs

---

## ⚙️ Configuration

### Configuration Files

#### config/config.json (Main)
```json
{
  "debug": false,
  "log_level": "INFO",
  
  "server": {
    "host": "0.0.0.0",
    "port_range": [21, 27017],
    "timeout": 30,
    "max_connections": 1000
  },
  
  "database": {
    "type": "sqlite",
    "path": "logs/honeypot.db",
    "backup": true
  },
  
  "services": {
    "http": {"port": 8080, "enabled": true},
    "ssh": {"port": 2222, "enabled": true},
    "ftp": {"port": 21, "enabled": true},
    "telnet": {"port": 23, "enabled": true},
    "mysql": {"port": 3306, "enabled": true},
    "postgresql": {"port": 5432, "enabled": true},
    "redis": {"port": 6379, "enabled": true},
    "mongodb": {"port": 27017, "enabled": true},
    "dns": {"port": 53, "enabled": true},
    "ntp": {"port": 123, "enabled": true},
    "ssdp": {"port": 1900, "enabled": true}
  },
  
  "geolocation": {
    "enabled": true,
    "provider": "maxmind",
    "cache": true
  },
  
  "ml": {
    "enabled": true,
    "model_path": "ml/model.pkl",
    "auto_retrain": false
  },
  
  "alerts": {
    "enabled": true,
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "from": "your-email@gmail.com",
      "password": "your-app-password"
    },
    "slack": {
      "enabled": false,
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    },
    "webhook": {
      "enabled": false,
      "url": "https://your-server.com/webhook"
    }
  },
  
  "dashboard": {
    "port": 5000,
    "auth_required": true,
    "rate_limit": 100,
    "session_timeout": 3600
  }
}
```

#### config/alert_config.json (Alert Rules)
```json
{
  "rules": [
    {
      "id": 1,
      "name": "High Attack Rate",
      "description": "Alert when attack rate exceeds 100/min",
      "condition": "event_rate > 100",
      "window": 60,
      "actions": ["email", "slack"],
      "enabled": true
    },
    {
      "id": 2,
      "name": "New Country Attack",
      "description": "Alert when attack from new country",
      "condition": "country_new = true",
      "actions": ["email"],
      "enabled": true
    },
    {
      "id": 3,
      "name": "Database Attack",
      "description": "Alert on database service attacks",
      "condition": "protocol IN (mysql, postgresql, mongodb)",
      "actions": ["slack"],
      "enabled": true
    }
  ]
}
```

### Environment Variables

Configure via environment variables (override config.json):

```bash
# Server
export DDOSPOT_HOST=0.0.0.0
export DDOSPOT_DEBUG=false
export DDOSPOT_LOG_LEVEL=INFO

# Database
export DDOSPOT_DB_PATH=/var/lib/ddospot/honeypot.db

# Geolocation
export DDOSPOT_GEOLOCATION_ENABLED=true
export DDOSPOT_GEOLOCATION_KEY=your-maxmind-key

# Alerts
export DDOSPOT_ALERT_EMAIL_ENABLED=true
export DDOSPOT_ALERT_EMAIL_FROM=alerts@example.com
export DDOSPOT_ALERT_EMAIL_PASSWORD=your-password

export DDOSPOT_ALERT_SLACK_ENABLED=true
export DDOSPOT_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...

# ML
export DDOSPOT_ML_ENABLED=true
export DDOSPOT_ML_MODEL_PATH=/path/to/model.pkl

# Dashboard
export DDOSPOT_DASHBOARD_PORT=5000
export DDOSPOT_DASHBOARD_AUTH_REQUIRED=true
```

### Enabling Services

To disable a service:
```json
"http": {"port": 8080, "enabled": false}
```

To change a port:
```json
"ssh": {"port": 2222, "enabled": true}
// Change to:
"ssh": {"port": 2223, "enabled": true}
```

---

## 🔒 Security

### Security Best Practices

#### 1. Network Security
```bash
# Only expose honeypot ports you need
# Use firewall to restrict dashboard access:
sudo ufw allow 8080/tcp  # Only honeypot
sudo ufw allow 5000/tcp from 192.168.1.0/24  # Dashboard from internal only

# Or with iptables:
sudo iptables -A INPUT -p tcp --dport 5000 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j REJECT
```

#### 2. Authentication
```bash
# Always use API tokens
# Generate strong tokens
python -c "import secrets; print(secrets.token_hex(32))"

# Rotate tokens regularly
# Never commit tokens to git
```

#### 3. SSL/TLS
```bash
# Enable HTTPS for dashboard
# Generate self-signed certificate:
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Or use Let's Encrypt with Certbot
sudo certbot certonly --standalone -d your-domain.com
```

#### 4. Database
```bash
# Regular backups
bash scripts/backup.sh

# Encrypt sensitive data
# Use config files with restricted permissions
chmod 600 config/config.json
```

#### 5. Monitoring
```bash
# Watch for suspicious dashboard access
tail -f logs/dashboard.log | grep -i "error\|warning\|unauthorized"

# Monitor system resources
watch -n 1 'ps aux | grep python'
```

### Common Security Scenarios

#### Scenario 1: Dashboard on Internet
```bash
# Use reverse proxy (Nginx)
# Add authentication
# Use strong SSL certificates
# Enable rate limiting
```

See **docs/SECURITY_HARDENING.md** for detailed setup.

#### Scenario 2: Multi-user Access
```bash
# Generate API tokens for each user
# Set rate limits per token
# Log all API access
# Review logs regularly
```

#### Scenario 3: Production Deployment
```bash
# Use Docker with network isolation
# Run as non-root user
# Regular security updates
# Automated backups
# Monitoring and alerting
```

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### Issue 1: Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8080

# Kill existing process
sudo kill -9 <PID>

# Or change port in config:
"http": {"port": 8090, "enabled": true}
```

#### Issue 2: Database Lock Error
```bash
# Honeypot might be using database
# Try restarting both services

# Or check if multiple instances running:
ps aux | grep python | grep -v grep

# Kill duplicates
pkill -f start-honeypot.py
pkill -f start-dashboard.py
```

#### Issue 3: High Memory Usage
```bash
# Check memory:
ps aux | grep python

# Reduce log level if too much logging:
"log_level": "WARNING"

# Reduce database retention (old events)
python -c "import sqlite3; \
  conn = sqlite3.connect('logs/honeypot.db'); \
  conn.execute('DELETE FROM events WHERE timestamp < datetime(\"now\", \"-30 days\")'); \
  conn.commit()"
```

#### Issue 4: Geolocation Not Working
```bash
# Check geolocation provider setup:
curl https://geoip.maxmind.com/

# Verify API key:
grep GEOLOCATION_KEY config/config.json

# Enable debug logging:
"log_level": "DEBUG"
```

#### Issue 5: Dashboard Not Loading
```bash
# Check if dashboard is running:
ps aux | grep start-dashboard.py

# Check logs:
tail -f logs/dashboard.log

# Restart:
python start-dashboard.py
```

### Debug Mode

Enable debugging for more information:

```json
{
  "debug": true,
  "log_level": "DEBUG"
}
```

Then check logs:
```bash
tail -f logs/honeypot.log | grep DEBUG
```

### Getting Help

1. **Check Logs**
   ```bash
   tail -f logs/honeypot.log
   tail -f logs/dashboard.log
   ```

2. **Check Configuration**
   ```bash
   cat config/config.json
   ```

3. **Run Tests**
   ```bash
   python tools/run_tests.py
   python tools/verify_security.py
   ```

4. **Check Documentation**
   - See **docs/** folder for detailed guides
   - See **QUICK_START.md** for basic setup
   - See **README.md** for overview

---

## 🚀 Advanced Features

### Machine Learning System

The honeypot includes advanced ML capabilities:

#### Feature Extraction
28 network features are extracted from each attack:
- Packet rate
- Payload size distribution
- Protocol combinations
- Timing patterns
- Source IP reputation
- Geographic indicators
- ...and more

#### Anomaly Detection
Multiple algorithms detect unusual patterns:
- **Isolation Forest** - Fast, high-dimensional anomaly detection
- **Local Outlier Factor** - Density-based detection
- **Statistical Methods** - Z-score based detection
- **Ensemble** - Combines all three

#### Attack Prediction
Classifies attack types using:
- **XGBoost** - Gradient boosting classifier
- **LightGBM** - Fast boosting with GPU support
- **Ensemble** - Combines both models

#### Pattern Learning
Discovers attack patterns using:
- **K-means Clustering** - Groups similar attacks
- **Feature Importance** - Identifies key indicators
- **Temporal Analysis** - Time-based pattern detection

### Training the ML Model

```bash
# Manual training
python ml/train.py

# Or in dashboard: Settings > ML > Retrain Model

# Check model performance
python tools/run_tests.py test_ml
```

### Custom Alert Rules

Create complex alert conditions:

```python
# In config/alert_config.json

{
  "rules": [
    {
      "name": "Sophisticated Scan",
      "condition": "protocol IN (http, ssh, mysql) AND country NOT IN (US, UK)",
      "actions": ["email", "slack"]
    },
    {
      "name": "Rapid Fire",
      "condition": "event_rate > 1000 OVER 60s",
      "actions": ["webhook"],
      "webhook": "https://your-server.com/alert"
    }
  ]
}
```

### Integration with External Tools

#### Prometheus Integration
```bash
# Scrape honeypot metrics
# Add to prometheus.yml:

scrape_configs:
  - job_name: 'ddospot'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/api/metrics'
```

#### Slack Integration
```bash
# Send alerts to Slack
# Set in config.json:

"slack": {
  "enabled": true,
  "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

#### SIEM Integration
```bash
# Forward events to SIEM
# Use webhook endpoint:

POST /api/webhooks/siem
Content-Type: application/json

{
  "events": [...]
}
```

### Performance Tuning

#### Optimize for High Volume
```json
{
  "server": {
    "max_connections": 5000,
    "timeout": 60
  },
  "database": {
    "batch_insert": true,
    "batch_size": 100
  },
  "geolocation": {
    "cache": true,
    "cache_ttl": 86400
  }
}
```

#### Reduce Resource Usage
```json
{
  "log_level": "WARNING",
  "ml": {
    "enabled": false
  },
  "database": {
    "auto_backup": false
  }
}
```

---

## ❓ FAQ

### General Questions

**Q: Is it safe to run a honeypot?**
A: Yes! A honeypot is designed to be attacked. It records attacks without affecting real systems. It should only run on isolated networks or public-facing servers dedicated for this purpose.

**Q: What's the difference between DDoS and attacks the honeypot detects?**
A: A DDoS is a flood attack trying to overwhelm a server. DDoSPoT detects any attack attempts (DDoS, brute-force, scanning, exploits) on its emulated services.

**Q: How much data will my database grow?**
A: About 1-10 KB per attack event. A busy honeypot might generate 100-1000 events/day, so ~1-10 MB/month. Use archival/pruning scripts if needed.

**Q: Can I run multiple honeypots?**
A: Yes! Run multiple instances on different machines with different port ranges, or on different IPs.

**Q: Is the data stored securely?**
A: The database contains attack data, not sensitive information. However, config files contain secrets—keep them secure (git-ignored, restricted permissions).

### Technical Questions

**Q: What Python version is required?**
A: Python 3.8+. Tested with 3.8, 3.9, 3.10, 3.11.

**Q: Can I use PostgreSQL instead of SQLite?**
A: Not currently, but SQLite is sufficient for most use cases. SQLite can handle millions of events.

**Q: Does it work on Windows?**
A: Yes, via WSL2 (Windows Subsystem for Linux). Native Windows is not recommended due to port binding differences.

**Q: Can I run the honeypot and dashboard on different machines?**
A: Yes, but they need to share the same database. Set up a remote SQLite access or use PostgreSQL.

**Q: What's the performance impact?**
A: Minimal. Each connection takes milliseconds. A single server can handle 1000+ connections/second.

### Operational Questions

**Q: How often should I back up the database?**
A: Daily for production. Use `bash scripts/backup.sh`.

**Q: How do I clean old attack data?**
A: Use the database query tool or delete old events before a date.

**Q: Can I update while the honeypot is running?**
A: No, restart required. Use `git pull`, then restart services.

**Q: How do I deploy to production?**
A: Use Docker or systemd services. See **docs/DOCKER_DEPLOYMENT.md**.

**Q: What about SSL/TLS for the dashboard?**
A: Use a reverse proxy (Nginx) with Let's Encrypt. See **docs/SECURITY_HARDENING.md**.

### Monitoring Questions

**Q: How do I know if the honeypot is working?**
A: Check the dashboard (http://localhost:5000) or query events via API. Also check logs: `tail -f logs/honeypot.log`.

**Q: What should I monitor?**
A: Attack rate, unique IPs, protocol distribution, database size, and resource usage.

**Q: Can I get alerts for every event?**
A: Yes, but it might be too noisy. Set thresholds instead (e.g., alert on 100 events/min).

**Q: How do I integrate with my SIEM?**
A: Use webhook endpoint to forward events. See advanced features section.

---

## 📞 Support & Resources

### Documentation Files

| Document | Purpose |
|----------|---------|
| **README.md** | Main overview |
| **QUICK_START.md** | 5-minute setup |
| **docs/API_DOCUMENTATION.md** | REST API reference |
| **docs/CLI_USAGE.md** | Command-line tools |
| **docs/DOCKER_DEPLOYMENT.md** | Docker setup |
| **docs/SECURITY_HARDENING.md** | Security guide |
| **docs/TESTING_GUIDE.md** | Running tests |
| **docs/OPERATIONS_PLAYBOOK.md** | Operational procedures |

### Quick Commands

```bash
# Start honeypot
python start-honeypot.py

# Start dashboard (in new terminal)
python start-dashboard.py

# Run tests
python tools/run_tests.py

# Query events
python app/cli.py query

# Generate demo data
python tools/populate_demo.py

# Backup database
bash scripts/backup.sh

# Restore database
bash scripts/restore.sh
```

### Key Metrics

- **11 Protocols** - Complete service coverage
- **42+ API Endpoints** - Full REST API
- **8 Database Tables** - Comprehensive logging
- **150+ Tests** - High code quality
- **Real-time Dashboard** - Live attack visualization
- **ML-powered Detection** - AI-based threat analysis
- **Production Ready** - Docker, systemd, monitoring

---

## 🎉 Conclusion

DDoSPoT is a powerful, production-ready DDoS honeypot that provides comprehensive attack detection, logging, and analysis. Whether you're learning about network security or actively monitoring threats, DDoSPoT gives you deep visibility into attack patterns and sources.

**Next Steps:**
1. ✅ Follow the Quick Start (above)
2. 🔍 Explore the dashboard at http://localhost:5000
3. 📖 Read docs/API_DOCUMENTATION.md for API integration
4. 🔒 Review docs/SECURITY_HARDENING.md for production deployment
5. 🧪 Run tools/run_tests.py to verify everything works

---

**Happy Honeypot Hunting! 🍯**

**DDoSPoT Team** | February 3, 2026 | Production v2.0

---

*This documentation covers DDoSPoT features, setup, configuration, security, troubleshooting, and advanced usage. For detailed technical information on specific components, see the individual documentation files in the `docs/` folder.*
