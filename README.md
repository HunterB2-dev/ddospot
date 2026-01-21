# DDoSPoT - Advanced DDoS Honeypot System

A sophisticated honeypot system for detecting, analyzing, and visualizing DDoS/DoS attacks in real-time.

## Features

- **Multi-Protocol Honeypot**: Captures attacks across HTTP, SSH, DNS, NTP, SSDP
- **Real-time Visualization**: Interactive world map of attack origins
- **Attack Analysis**: Protocol breakdown, payload analysis, rate detection
- **Geolocation Tracking**: IP geolocation with ISP and autonomous system data
- **Machine Learning**: Attack type prediction and anomaly detection
- **Alert System**: Multi-channel notifications (email, Slack, webhooks)
- **Dashboard**: Web-based monitoring and statistics
- **Prometheus Integration**: Metrics export for monitoring stacks
- **Security**: Token-based authentication, rate limiting, input validation

## Quick Start

```bash
# Start services
./cli.py
# Choose 3 (Start Both Services)

# Open dashboard
# URL: http://localhost:5000

# Simulate attack
./cli.py
# Choose 8 (Simulate Botnet Attack)
```

## Documentation

- [CLI Usage Guide](CLI_USAGE.md)
- [Enhanced Monitoring Setup](monitoring/README.md)
- **[Security Hardening](SECURITY_HARDENING.md)** ← Read before production deployment
- [About DDoSPoT](About%20DDoSPoT/)

## Requirements

- Python 3.8+
- pip
- Internet connection (for geolocation)

## Installation

```bash
# Create virtual environment
python3 -m venv myenv
source myenv/bin/activate

# Install dependencies
pip install -r requerements.txt

# Run CLI
./cli.py
```

## Architecture

### Core Components

- **core/**: Database, detection, geolocation, protocol handlers
- **ml/**: Machine learning attack prediction
- **telemetry/**: Metrics, logging, alerting, rate limiting
- **dashboard.py**: Flask web API and UI
- **main.py**: Honeypot service

### Database

SQLite database storing:
- Attack events with timestamps, IPs, protocols
- Attacker profiles with statistics
- Geolocation cache
- Blacklist entries

### Monitoring

- **Prometheus**: `/metrics` endpoint with 30+ metrics
- **Grafana**: Pre-built dashboard with 11 panels
- **Alertmanager**: Alert routing and notifications

## Configuration

### Environment Variables

See [SECURITY_HARDENING.md](SECURITY_HARDENING.md#configuration) for security options.

### config.json

```json
{
  "api": {
    "token": "optional-token-here"
  },
  "log_rotation": {
    "max_bytes": 5242880,
    "backups": 2
  }
}
```

## Security

**⚠️ Important**: Review [SECURITY_HARDENING.md](SECURITY_HARDENING.md) before production deployment.

Key features:
- Token-based API authentication
- Per-IP rate limiting with blacklist
- Input validation on POST endpoints
- Prometheus metrics access control
- Health check endpoint protection

Quick production setup:
```bash
# Generate token
export DDOSPOT_API_TOKEN=$(openssl rand -hex 32)
export DDOSPOT_REQUIRE_TOKEN=true
export DDOSPOT_METRICS_PUBLIC=false

./cli.py
```

## API Endpoints

### Statistics
- `GET /api/stats` - Overall statistics
- `GET /api/top-attackers` - Top attacking IPs
- `GET /api/recent-events` - Recent attack events with pagination
- `GET /api/timeline` - Attack timeline

### Data
- `GET /api/map-data` - Geolocation coordinates
- `GET /api/country-stats` - Attacks by country
- `GET /api/database-info` - Database metrics
- `GET /api/protocol-breakdown` - Protocol distribution

### Management
- `GET /api/alerts/config` - Alert configuration
- `POST /api/alerts/config` - Update alerts (token required)
- `POST /api/alerts/test` - Send test alert (token required)
- `GET /api/alerts/history` - Alert history

### ML
- `GET /api/ml/model-stats` - Model performance
- `GET /api/ml/predict/<ip>` - Predict attack type
- `POST /api/ml/train` - Train model (token required)
- `POST /api/ml/batch-predict` - Batch predictions (token required)

### System
- `GET /metrics` - Prometheus metrics (optional token)
- `GET /health` - Health check (optional token)

## CLI Commands

```bash
./cli.py

🚀 SERVICE MANAGEMENT
  1. Start Honeypot Server
  2. Start Dashboard (Web UI)
  3. Start Both Services
  4-6. Stop services

🎯 ATTACK SIMULATION
  7. Quick Attack (100 events)
  8. Botnet Attack (5 locations)
  9. Custom Attack

📊 MONITORING & STATUS
  10. System Status
  11. Database Statistics
  12. Attack Map Data
  13. Top Attackers

🌐 DASHBOARD & LOGS
  14. Open Dashboard
  15. View Honeypot Logs
  16. View Dashboard Logs

⚙️ MAINTENANCE
  17. Reset Database
  18. Cleanup Old Events
  19. Check Disk Space
  21. Rotate Logs Now
  22. Health Check

ℹ️ HELP
  20. Show Help
  0. Exit
```

## Scheduled Maintenance

Automate log rotation and cleanup:

```bash
# Install cron jobs
./install-cron.sh

# Uninstall cron jobs
./uninstall-cron.sh
```

Tasks:
- Daily: Rotate logs
- Weekly: Cleanup events older than 30 days
- Monthly: Full maintenance (rotate + cleanup + vacuum)

## Monitoring Stack

Deploy with Docker Compose:

```bash
cd monitoring/
docker-compose -f docker-compose.yml up -d
```

Services:
- Dashboard: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Alertmanager: http://localhost:9093

See [monitoring/README.md](monitoring/README.md) for detailed setup.

## Performance

- **Attack processing**: ~1-5ms per event
- **Database queries**: <50ms typical
- **Metrics endpoint**: ~1-2ms per request
- **Geolocation lookup**: 5-100ms (cached)

## Troubleshooting

### Dashboard won't start
```bash
./cli.py
# Choose 22 (Health Check)
# Check logs: tail -f /tmp/dashboard.log
```

### Rate limit errors
```bash
# Check current limits
env | grep DDOSPOT_RATE_LIMIT

# Temporarily increase for testing
export DDOSPOT_RATE_LIMIT_MAX=1000
```

### Metrics endpoint returns 401
```bash
# Set token if configured
export DDOSPOT_API_TOKEN=your-token

# Test with token
curl -H "Authorization: Bearer $DDOSPOT_API_TOKEN" http://localhost:5000/metrics
```

## License

See [LICENSE](LICENSE) file.

## Contributing

Contributions welcome! Please submit issues and pull requests.

## Author

DDoSPoT Development Team

---

**Security First**: Always review [SECURITY_HARDENING.md](SECURITY_HARDENING.md) before production deployment.

