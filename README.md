<div align="center">

# 🍯 DDoSPoT

**Advanced DDoS Honeypot System**

Real-time detection and analysis of DDoS/DoS attacks with machine learning

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/HunterB2-dev/ddospot)

</div>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-Protocol Detection** | HTTP, SSH, DNS, NTP, SSDP attack detection |
| 📊 **Real-time Dashboard** | Interactive web-based monitoring with live charts |
| 🌍 **Geolocation Tracking** | Global attack map with ISP and AS data |
| 🤖 **ML-Powered Analysis** | Attack type prediction and anomaly detection |
| 🔔 **Smart Alerts** | Email, Slack, webhook notifications |
| 📈 **Prometheus Metrics** | Integration with monitoring stacks |
| 🛡️ **Security First** | Token auth, rate limiting, input validation |
| 🐳 **Docker Ready** | Docker Compose deployment included |

---

## 🚀 Quick Start

### 1️⃣ Clone & Setup
```bash
git clone https://github.com/HunterB2-dev/ddospot.git
cd ddospot
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Run Honeypot
```bash
python start-honeypot.py
```

### 3️⃣ Open Dashboard
```bash
python start-dashboard.py
# Visit: http://localhost:5000
```

---

## 📁 Project Structure

```
ddospot/
├── app/                 # Main application (honeypot, dashboard, CLI)
├── core/                # Core modules (detection, database, geolocation)
├── ml/                  # Machine learning models
├── telemetry/           # Metrics, alerts, logging
├── tests/               # Comprehensive test suite
├── tools/               # Utility scripts
├── config/              # Configuration templates
├── static/              # Dashboard assets (CSS, JS)
├── templates/           # HTML templates
└── docs/                # Detailed documentation
```

---

## 🎮 Usage

### Via CLI
```bash
./start-honeypot.py  # Start honeypot server
./start-dashboard.py # Start web dashboard
```

### Via Docker
```bash
docker-compose -f docker/docker-compose.yml up
```

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[FOLDER_GUIDE.md](FOLDER_GUIDE.md)** - File location guide
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Full documentation hub
- **[SECURITY_HARDENING.md](docs/SECURITY_HARDENING.md)** - Production deployment
- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Running tests

---

## 🔧 Requirements

- **Python:** 3.8+
- **OS:** Linux, macOS, Windows
- **Memory:** 512 MB minimum
- **Network:** Local or remote deployment

---

## 📊 Dashboard Features

- **Real-time Attack Visualization** - Live world map of attacks
- **Attack Timeline** - Hourly attack volume tracking
- **Protocol Breakdown** - Attack method distribution
- **Top Attackers** - Ranked by frequency and severity
- **Event History** - Full event log with filtering
- **Database Stats** - Size, events, profiles
- **Alert Management** - View and manage alerts

---

## ⚠️ Disclaimer

This project is **for research, educational, and defensive purposes only**.

- ❌ Do **NOT** use this to launch attacks
- ✅ Do **USE** to improve your security posture
- ⚖️ Author assumes **NO responsibility** for misuse

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

<div align="center">

**Made with ❤️ for cybersecurity research**

[Report Issue](https://github.com/HunterB2-dev/ddospot/issues) · [Documentation](DOCUMENTATION_INDEX.md) · [Contribute](CONTRIBUTING.md)

</div>
