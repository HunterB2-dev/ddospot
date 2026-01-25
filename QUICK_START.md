# DDoSPot - Quick Start (5 Minutes)

## What is DDoSPot?

DDoSPot is an **advanced DDoS/DoS attack honeypot** that:
- Captures and analyzes attack traffic from multiple protocols
- Detects attack patterns using machine learning
- Provides real-time dashboard visualization
- Generates alerts and maintains blacklists

## System Requirements

- Python 3.10+
- Linux/macOS
- ~500MB disk space
- Ports: 80, 443, 53, 5000 (configurable)

## Installation (2 minutes)

```bash
# Clone the repository
git clone <repo-url>
cd ddospot

# Create config files from examples
cp config/config.example.json config/config.json
cp config/alert_config.example.json config/alert_config.json

# Create virtual environment
python -m venv myenv
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration (1 minute)

Edit `config/config.json`:
```json
{
  "api": {
    "token": "your-secret-token-here"
  },
  "server": {
    "bind_ip": "0.0.0.0",
    "ports": [80, 443, 53, 8080]
  }
}
```

## Run the Honeypot (1 minute)

```bash
# Start honeypot server
python app/main.py

# In another terminal, start dashboard
source myenv/bin/activate
python app/dashboard.py

# Access dashboard at http://localhost:5000
```

## Key Features

| Feature | Purpose |
|---------|---------|
| **Attack Detection** | Captures HTTP, DNS, UDP floods, SSH brute-force |
| **Dashboard** | Real-time visualization of attacks by country/IP |
| **Machine Learning** | Classifies attack types automatically |
| **Alerts** | Email/Slack notifications for critical events |
| **Blacklist** | Auto-blocks repeat offenders |
| **Metrics** | Prometheus metrics for monitoring |

## Project Structure

```
ddospot/
├── app/              # Main application
│   ├── main.py       # Start honeypot
│   ├── dashboard.py  # Start web UI
│   └── cli.py        # Command-line tools
├── core/             # Core modules
├── ml/               # Machine learning
├── telemetry/        # Alerts & metrics
├── config/           # Configuration (don't commit)
├── logs/             # Logs & database
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── tools/            # Helper utilities
```

## Common Tasks

### View live attacks
```bash
curl http://localhost:5000/api/recent-events
```

### Export data
```bash
python tools/query_database.py --hours 24 --format csv
```

### Check security
```bash
python tools/verify_security.py
```

### Backup data
```bash
bash scripts/backup.sh
```

## Troubleshooting

**Port already in use?**
```bash
# Change port in config.json or environment
export DDOSPOT_PORT=8080
```

**No attacks detected?**
```bash
# Populate demo data
python tools/populate_demo.py

# Or generate test traffic
curl -X GET http://localhost/test
curl -X POST http://localhost/ -d "payload=test" (repeated)
```

**Dashboard not loading?**
```bash
# Check dashboard is running
ps aux | grep dashboard.py

# View logs
tail -50 logs/dashboard.log
```

## Production Deployment

For production use, see `docs/DEPLOYMENT_GUIDE.md`:
- Docker Compose setup
- Nginx reverse proxy
- SSL/TLS configuration
- Systemd service setup
- Monitoring with Prometheus

## Support & Docs

- Full guide: `docs/DEPLOYMENT_GUIDE.md`
- Security: `docs/SECURITY_HARDENING.md`
- Testing: `docs/TESTING_GUIDE.md`
- Operations: `docs/OPERATIONS_PLAYBOOK.md`

---

**Ready to go!** Start with `python app/main.py` and access the dashboard at http://localhost:5000
