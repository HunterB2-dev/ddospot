<div align="center">

# 🍯 DDoSPoT

**Advanced DDoS Honeypot System**

Real-time detection and analysis of DDoS/DoS attacks

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ✨ Features

🎯 **Multi-Protocol Detection** · 📊 **Real-time Dashboard** · 📱 **Mobile Dashboard** · 🌍 **Geolocation Tracking**  
🤖 **ML-Powered Analysis** · 🔔 **Smart Alerts** · 🐳 **Docker Support** · 🔐 **Advanced Authentication** · 📡 **REST API**

### Core Capabilities
- **8+ Protocol Services**: TCP, UDP, HTTP, SSH, FTP, SMTP, DNS, NTP handlers
- **Attack Detection**: Real-time anomaly detection with ML models (XGBoost, LightGBM)
- **Threat Intelligence**: IP reputation scoring and geolocation analysis
- **Automated Responses**: IP blocking, webhook notifications, SOAR integration
- **Type-Safe Code**: Full type annotations for production reliability

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/HunterB2-dev/ddospot.git
cd ddospot

# Setup
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

# Run
python start-honeypot.py    # Terminal 1
python start-dashboard.py   # Terminal 2
# Open advanced: http://localhost:5000/advanced
# Open simple: http://localhost:5000
# Mobile: http://localhost:5000/mobile
```

---

## �️ 12-Feature Roadmap

| # | Feature | Status | Details |
|---|---------|--------|---------|
| 1 | Advanced Search | ✅ Complete | Full-text search across events |
| 2 | Custom Alert Rules | ✅ Complete | User-defined alert conditions |
| 3 | Attack Pattern Reports | ✅ Complete | Statistical analysis and reports |
| 4 | Real-Time Log Viewer | ✅ Complete | Live event streaming |
| 5 | ML Anomaly Detection | ✅ Complete | ML-powered threat detection |
| 6 | Geographic Heat Map | ✅ Complete | World map visualization |
| 7 | Threat Intelligence | ✅ Complete | IP reputation scoring |
| 8 | Automated Responses | ✅ Complete | IP blocking and webhooks |
| 9 | Docker Deployment | ✅ Complete | Production-ready containers |
| 10 | API Enhancements | ✅ Complete | Authentication & rate limiting |
| 11 | Web Configuration UI | 🔄 Planned | Settings management |
| 12 | Mobile Dashboard | ✅ Complete | PWA-ready mobile interface |

**Overall Progress**: 11/12 Features Complete (92%)

---

## 📱 Mobile Dashboard

- Desktop: http://localhost:5000
- Mobile: http://<server-ip>:5000/mobile (phone and server on same Wi‑Fi)

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) | 5-minute setup guide |
| [DDoSPoT_DOCUMENTATION.md](DDoSPoT_DOCUMENTATION.md) | Comprehensive project documentation |
| [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) | 42 API endpoints reference |
| [DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) | Production deployment guide |
| [Security Hardening](docs/SECURITY_HARDENING.md) | Security best practices |
| [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Test suite documentation |

---

## 🏗️ Architecture

**Modular Design** with clear separation of concerns:
- `core/` - Core honeypot engine (server, detection, responses, threat intelligence)
- `ml/` - Machine learning modules (detection, prediction, pattern learning)
- `app/` - Flask API and CLI interfaces
- `telemetry/` - Monitoring and alerting system
- `static/` & `templates/` - Web dashboards (desktop & mobile)

**Type System**: Full Python type annotations across all modules for production-grade reliability.

---

## 🔧 Production Deployment

### Docker (Recommended)
```bash
# Development environment
docker-compose -f docker-compose-dev.yml up

# Production environment
docker-compose -f docker-compose-prod.yml up -d
```

### Manual Setup
```bash
# Clone & install
git clone https://github.com/HunterB2-dev/ddospot.git
cd ddospot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run honeypot
python start-honeypot.py &

# Run dashboard (new terminal)
python start-dashboard.py
```

---

## ⚠️ Disclaimer

**For research & defensive purposes only** - Do not use for attacks. Author assumes no responsibility for misuse.

---

<div align="center">Made with ❤️ for cybersecurity research</div>
