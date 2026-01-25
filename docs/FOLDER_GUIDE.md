# DDoSPot - Directory Structure Guide

## 📁 Folder Organization

```
ddospot/
│
├── 📂 app/                       # Main application code
│   ├── main.py                   # Honeypot entry point
│   ├── dashboard.py              # Flask web dashboard
│   ├── cli.py                    # Command-line interface
│   └── maintenance.py            # Maintenance tasks
│
├── 📂 core/                      # Core honeypot modules
│   ├── server.py                 # Network server (UDP/TCP)
│   ├── database.py               # SQLite operations
│   ├── detection.py              # Attack pattern detection
│   ├── geolocation.py            # IP geolocation
│   ├── protocol_handlers.py      # Protocol implementations
│   └── responses.py              # Protocol response generation
│
├── 📂 ml/                        # Machine Learning
│   ├── model.py                  # Attack classification
│   ├── features.py               # Feature extraction
│   ├── train.py                  # Model training
│   └── attack_model.pkl          # Trained model (binary)
│
├── 📂 telemetry/                 # Monitoring & Alerts
│   ├── alerts.py                 # Alert management
│   ├── logger.py                 # Logging system
│   ├── metrics.py                # Performance metrics
│   ├── prometheus_metrics.py     # Prometheus exporter
│   ├── ratelimit.py              # Rate limiting
│   └── stats.py                  # Statistics collection
│
├── 📂 tools/                     # Utility scripts
│   ├── populate_demo.py          # Demo data generator
│   ├── query_database.py         # Database query tool
│   ├── verify_security.py        # Security verification
│   └── run_tests.py              # Test runner
│
├── 📂 tests/                     # Test suite
│   ├── test_api_endpoints.py     # API tests
│   ├── test_security.py          # Security tests
│   ├── test_detection.py         # Detection tests
│   ├── test_ml_model.py          # ML tests
│   └── ... (more tests)
│
├── 📂 config/                    # Configuration files ⚠️ NEVER COMMIT
│   ├── config.json               # Main config (gitignored)
│   ├── config.example.json       # Template for users
│   ├── alert_config.json         # Alert rules (gitignored)
│   └── alert_config.example.json # Template for alerts
│
├── 📂 logs/                      # Runtime data ⚠️ NEVER COMMIT
│   ├── dashboard.log             # Dashboard logs
│   └── honeypot.db               # SQLite database
│
├── 📂 docs/                      # Documentation
│   ├── DEPLOYMENT_GUIDE.md       # Production deployment
│   ├── SECURITY_HARDENING.md     # Security setup
│   ├── TESTING_GUIDE.md          # Testing guide
│   ├── CLI_USAGE.md              # CLI reference
│   └── OPERATIONS_PLAYBOOK.md    # Ops guide
│
├── 📂 docker/                    # Docker configuration
│   ├── dockerfile                # Docker image
│   └── docker-compose.yml        # Docker Compose dev
│
├── 📂 systemd/                   # Linux service files
│   ├── ddospot-honeypot.service  # Honeypot service
│   └── ddospot-dashboard.service # Dashboard service
│
├── 📂 nginx/                     # Nginx configuration
│   └── ddospot.conf              # Reverse proxy config
│
├── 📂 monitoring/                # Prometheus/Grafana
│   ├── prometheus.yml            # Prometheus config
│   ├── alertmanager.yml          # Alert manager
│   └── grafana-dashboard.json    # Grafana dashboard
│
├── 📂 static/                    # Web frontend assets
│   ├── dashboard.js              # Dashboard logic
│   ├── dashboard.css             # Dashboard styles
│   └── profile.js                # Profile page JS
│
├── 📂 templates/                 # HTML templates
│   ├── index.html                # Dashboard UI
│   └── profile.html              # Profile page
│
├── 📂 replay/                    # PCAP replay tools
│   └── pcap_replay.py            # Replay traffic
│
├── 📂 scripts/                   # Bash utility scripts
│   ├── backup.sh                 # Database backup
│   ├── restore.sh                # Database restore
│   ├── setup-production.sh       # Production setup
│   └── install-cron.sh           # Cron job setup
│
├── 📄 start-honeypot.py          # ⭐ Run honeypot
├── 📄 start-dashboard.py         # ⭐ Run dashboard
├── 📄 requirements.txt           # Python dependencies
├── 📄 QUICK_START.md             # 5-minute guide
├── 📄 PROJECT_STRUCTURE.md       # This file
├── 📄 README.md                  # Main documentation
├── 📄 .gitignore                 # Git ignore rules
└── 📄 LICENSE                    # License
```

## 🚀 Quick Start

### Start the Honeypot
```bash
python start-honeypot.py
```

### Start the Dashboard
```bash
python start-dashboard.py
```

### Access Dashboard
```
http://localhost:5000
```

## 📁 File Organization Tips

### App Files (app/)
- **main.py** - Starts the honeypot server, listens on configured ports
- **dashboard.py** - Flask web UI, API endpoints
- **cli.py** - Command-line tools for management
- **maintenance.py** - Background maintenance tasks

### Tools (tools/)
- **populate_demo.py** - Generate fake attack data for testing
- **query_database.py** - Export/query attack database
- **verify_security.py** - Security checks and validation
- **run_tests.py** - Execute all tests

### Core Modules (core/)
- **Detection & Analysis** - detection.py, geolocation.py
- **Storage** - database.py, config.py
- **Networking** - server.py, protocol_handlers.py, responses.py

### Telemetry (telemetry/)
- **Alerts** - alerts.py, prometheus_metrics.py
- **Monitoring** - metrics.py, logger.py
- **Control** - ratelimit.py, stats.py

## 🔍 How to Find Things

| What I need | Where to look |
|-----------|---------------|
| Start honeypot | `start-honeypot.py` or `app/main.py` |
| Start dashboard | `start-dashboard.py` or `app/dashboard.py` |
| API endpoints | `app/dashboard.py` (routes) |
| Database operations | `core/database.py` |
| Attack detection logic | `core/detection.py` |
| ML model | `ml/model.py` and `ml/features.py` |
| Alerts & notifications | `telemetry/alerts.py` |
| Tests | `tests/` folder |
| Helper tools | `tools/` folder |
| Configuration | `config/` folder |
| Documentation | `docs/` folder |

## 📦 Installation

```bash
# 1. Create virtual environment
python -m venv myenv
source myenv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create config from examples
cp config/config.example.json config/config.json
cp config/alert_config.example.json config/alert_config.json

# 4. Edit config
nano config/config.json
```

## 🧪 Running Tests

```bash
# Run all tests
python tools/run_tests.py

# Or use pytest directly
pytest tests/

# Run specific test
pytest tests/test_security.py -v
```

## 🔧 Maintenance Tools

```bash
# Generate demo data
python tools/populate_demo.py

# Query database
python tools/query_database.py --hours 24 --limit 100

# Verify security
python tools/verify_security.py

# Backup database
bash scripts/backup.sh

# Restore database
bash scripts/restore.sh
```

## ⚠️ Important Notes

**DO NOT COMMIT TO GITHUB:**
- `config/config.json` - Contains API tokens
- `config/alert_config.json` - Contains alert rules
- `logs/` - Contains runtime data
- `myenv/` or `.venv/` - Virtual environment
- `*.db` - Database files

**USE EXAMPLES INSTEAD:**
- `config/config.example.json` - Configuration template
- `config/alert_config.example.json` - Alert template

See `.gitignore` for complete list of ignored files.

## 📚 Full Documentation

- **QUICK_START.md** - 5-minute overview
- **README.md** - Full documentation
- **docs/DEPLOYMENT_GUIDE.md** - Production deployment
- **docs/SECURITY_HARDENING.md** - Security hardening
- **docs/TESTING_GUIDE.md** - Testing guide
- **docs/OPERATIONS_PLAYBOOK.md** - Operations reference

---

**Happy exploring!** Use this guide to navigate the codebase efficiently. 🎯
