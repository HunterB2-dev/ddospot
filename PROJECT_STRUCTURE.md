# DDoSPot Project Structure

```
ddospot/
├── config/                      # Configuration files (secrets - don't commit)
│   ├── config.example.json      # Example config template
│   ├── config.json              # Main config (DO NOT commit)
│   ├── alert_config.example.json # Example alerts template
│   └── alert_config.json        # Alert rules (DO NOT commit)
│
├── docs/                        # Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── SECURITY_HARDENING.md
│   ├── TESTING_GUIDE.md
│   ├── OPERATIONS_PLAYBOOK.md
│   └── ...
│
├── logs/                        # Runtime logs & database (don't commit)
│   ├── dashboard_output.log
│   └── honeypot.db
│
├── scripts/                     # Utility scripts
│   ├── backup.sh
│   ├── restore.sh
│   ├── setup-production.sh
│   └── ...
│
├── core/                        # Core honeypot modules
│   ├── database.py              # Database operations
│   ├── detection.py             # Attack detection
│   ├── geolocation.py           # IP geolocation
│   ├── server.py                # UDP/TCP server
│   ├── responses.py             # Protocol responses
│   └── ...
│
├── ml/                          # Machine learning
│   ├── model.py                 # ML attack classification
│   ├── features.py              # Feature extraction
│   ├── train.py                 # Model training
│   └── attack_model.pkl
│
├── telemetry/                   # Monitoring & alerts
│   ├── alerts.py                # Alert management
│   ├── logger.py                # Logging
│   ├── metrics.py               # Prometheus metrics
│   └── ...
│
├── replay/                      # PCAP replay tools
│   └── pcap_replay.py
│
├── docker/                      # Docker configuration
│   ├── dockerfile
│   └── docker-compose.yml
│
├── nginx/                       # Nginx reverse proxy config
│   └── ddospot.conf
│
├── systemd/                     # Linux service files
│   ├── ddospot-honeypot.service
│   └── ddospot-dashboard.service
│
├── monitoring/                  # Prometheus/Grafana config
│   ├── prometheus.yml
│   ├── grafana-dashboard.json
│   └── alertmanager.yml
│
├── templates/                   # Flask HTML templates
│   ├── index.html               # Dashboard UI
│   └── profile.html
│
├── static/                      # Frontend assets
│   ├── dashboard.js             # Dashboard logic
│   ├── dashboard.css            # Dashboard styles
│   └── ...
│
├── tests/                       # Pytest test suite
│   ├── test_api_endpoints.py
│   ├── test_security.py
│   └── ...
│
├── main.py                      # Honeypot entry point
├── dashboard.py                 # Flask dashboard server
├── cli.py                       # Command-line interface
├── maintenance.py               # Maintenance tasks
├── requirements.txt             # Python dependencies
├── README.md                    # Main documentation
├── .gitignore                   # Git ignore rules
├── LICENSE
└── docker-compose.prod.yml      # Production Docker setup
```

## Setup Instructions

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd ddospot
   ```

2. **Create config files from examples**
   ```bash
   cp config/config.example.json config/config.json
   cp config/alert_config.example.json config/alert_config.json
   ```

3. **Edit configuration**
   ```bash
   nano config/config.json
   nano config/alert_config.json
   ```

4. **Install dependencies**
   ```bash
   python -m venv myenv
   source myenv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run the honeypot**
   ```bash
   python main.py
   ```

6. **Access dashboard**
   ```
   http://localhost:5000
   ```

## Important Notes

- **config/** - Contains sensitive data. NEVER commit to git.
- **logs/** - Runtime data. NEVER commit to git.
- **myenv/** or **.venv/** - Virtual environment. NEVER commit to git.
- All secrets should be in `config/config.json` (not in git).
- Use environment variables for production secrets.
