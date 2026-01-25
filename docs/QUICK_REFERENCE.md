# 🎯 DDoSPot Quick Reference Card

## One-Liner Cheat Sheet

```bash
# START HONEYPOT
python start-honeypot.py

# START DASHBOARD  
python start-dashboard.py

# ACCESS DASHBOARD
http://localhost:5000

# RUN TESTS
python tools/run_tests.py

# GENERATE DEMO DATA
python tools/populate_demo.py

# QUERY DATABASE
python tools/query_database.py --hours 24

# BACKUP DATA
bash scripts/backup.sh

# RESTORE DATA
bash scripts/restore.sh

# CHECK SECURITY
python tools/verify_security.py

# HELP
python app/cli.py --help
```

---

## File Locations (Where to Find Things)

| What | Where |
|-----|-------|
| **Start honeypot** | `start-honeypot.py` or `app/main.py` |
| **Start dashboard** | `start-dashboard.py` or `app/dashboard.py` |
| **Command-line tools** | `app/cli.py` |
| **Maintenance tasks** | `app/maintenance.py` |
| **Core honeypot logic** | `core/` folder |
| **ML attack classification** | `ml/` folder |
| **Alerts & monitoring** | `telemetry/` folder |
| **Utility scripts** | `tools/` folder |
| **Tests** | `tests/` folder |
| **Configuration** | `config/` folder (⚠️ don't commit) |
| **Logs & database** | `logs/` folder (⚠️ don't commit) |
| **Documentation** | `docs/` folder |
| **Web UI files** | `static/` and `templates/` |
| **Deployment** | `docker/` and `systemd/` |

---

## Documentation Quick Links

| Document | Time | Purpose |
|----------|------|---------|
| **QUICK_START.md** | 5 min | Get started immediately |
| **FOLDER_GUIDE.md** | 5-10 min | Understand file structure |
| **README.md** | 15 min | Full project overview |
| **DOCUMENTATION_INDEX.md** | 5 min | Navigate all docs |
| **docs/DEPLOYMENT_GUIDE.md** | 30 min | Deploy to production |
| **docs/SECURITY_HARDENING.md** | 30 min | Security configuration |
| **docs/TESTING_GUIDE.md** | 15 min | Run & write tests |
| **docs/CLI_USAGE.md** | 10 min | Command reference |
| **docs/OPERATIONS_PLAYBOOK.md** | 20 min | Day-to-day operations |

---

## 5-Minute Setup

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp config/config.example.json config/config.json
nano config/config.json  # Edit with your settings

# 3. Run
python start-honeypot.py &
python start-dashboard.py

# 4. Access
open http://localhost:5000
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Dashboard won't start** | Check port 5000 isn't in use: `lsof -i :5000` |
| **Port 5000 in use** | Kill old process: `pkill -f "python start-dashboard"` |
| **No attacks showing** | Generate demo: `python tools/populate_demo.py` |
| **Can't connect to dashboard** | Check if running: `curl http://localhost:5000/health` |
| **Import errors** | Reinstall dependencies: `pip install -r requirements.txt` |
| **Database locked** | Stop dashboard/honeypot and retry |
| **Permission denied** | Make scripts executable: `chmod +x scripts/*.sh` |

---

## Environment Variables

```bash
# Dashboard settings
export DDOSPOT_PORT=5000
export DDOSPOT_HOST=127.0.0.1
export DDOSPOT_API_TOKEN="your-token"
export DDOSPOT_REQUIRE_TOKEN=False

# Rate limiting
export DDOSPOT_RATE_LIMIT_MAX=300
export DDOSPOT_RATE_LIMIT_WINDOW=60

# Testing
export DDOSPOT_TESTING=False
```

---

## Common Tasks

### See recent attacks
```bash
python tools/query_database.py --hours 1 --limit 50
```

### Generate test data
```bash
python tools/populate_demo.py
```

### Backup database
```bash
bash scripts/backup.sh
```

### Run all tests
```bash
python tools/run_tests.py
```

### Check security status
```bash
python tools/verify_security.py
```

### View API stats
```bash
curl http://localhost:5000/api/stats
```

### See top attackers
```bash
curl http://localhost:5000/api/top-attackers?limit=10
```

---

## Project Structure Tree

```
ddospot/
├── app/                    ← Main application
├── core/                   ← Core modules
├── ml/                     ← Machine learning
├── telemetry/              ← Monitoring & alerts
├── tools/                  ← Utility scripts
├── tests/                  ← Test suite
├── config/                 ← Configuration (⚠️)
├── logs/                   ← Runtime data (⚠️)
├── docs/                   ← Documentation
├── static/                 ← Web files
├── templates/              ← HTML templates
├── start-honeypot.py       ← Run honeypot ⭐
├── start-dashboard.py      ← Run dashboard ⭐
├── QUICK_START.md          ← Quick guide ⭐
└── FOLDER_GUIDE.md         ← File locations ⭐
```

---

## Git Commands

```bash
# Clone
git clone <url>
cd ddospot

# Create config from examples
cp config/config.example.json config/config.json

# Install
pip install -r requirements.txt

# Run
python start-honeypot.py
python start-dashboard.py

# Commit (safe files)
git add app/ core/ ml/ telemetry/ tests/ tools/
git add docs/ static/ templates/ docker/ scripts/
git add *.md requirements.txt .gitignore LICENSE
git commit -m "Your message"
git push
```

---

## Key Ports

| Port | Service | Purpose |
|------|---------|---------|
| **5000** | Flask Dashboard | Web UI |
| **80** | HTTP | Honeypot (configurable) |
| **443** | HTTPS | Honeypot (configurable) |
| **53** | DNS | Honeypot (configurable) |
| **9090** | Prometheus | Metrics (optional) |
| **3000** | Grafana | Dashboards (optional) |

---

## Dependencies (Quick View)

```
Core:
- Flask - Web framework
- SQLite3 - Database
- scikit-learn - ML models

Optional:
- Docker - Containerization
- Prometheus - Metrics
- Grafana - Visualization
```

See `requirements.txt` for full list.

---

## Security Notes

⚠️ **NEVER COMMIT:**
- `config/config.json` - Contains API tokens
- `config/alert_config.json` - Contains rules
- `logs/` - Runtime data
- `.db` files - Database
- Virtual environment folders

✅ **ALWAYS COMMIT:**
- `config/config.example.json` - Template
- `.gitignore` - Ignore rules
- Documentation files
- Source code

---

## Support & Resources

- **Quick help:** `cat QUICK_START.md`
- **Find files:** `cat FOLDER_GUIDE.md`
- **Doc index:** `cat DOCUMENTATION_INDEX.md`
- **Full guide:** `cat README.md`
- **Issues:** Check `docs/` folder
- **CLI help:** `python app/cli.py --help`

---

## Status Dashboard

```
✓ Project organized
✓ Documentation complete
✓ Dashboard running
✓ Tests passing
✓ Ready for GitHub
✓ Production-ready
```

---

**Print this card or bookmark it!** 📌

Last updated: January 25, 2026
