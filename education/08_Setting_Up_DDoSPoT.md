# Setting Up DDoSPoT: Installation & Configuration

## Prerequisites

### System Requirements

#### Minimum Specifications
```
CPU: 2 cores
RAM: 2 GB
Disk: 20 GB free
Network: 1 Gbps connection recommended
OS: Linux (Ubuntu 20.04+) or Windows with WSL2
```

#### Recommended Specifications
```
CPU: 4+ cores
RAM: 8 GB
Disk: 50+ GB SSD
Network: 10+ Gbps
OS: Linux (Ubuntu 22.04 LTS recommended)
```

### Software Requirements

- **Python 3.8+** (tested on 3.9, 3.10, 3.11)
- **Docker** (for containerized deployment)
- **Git** (for cloning repository)
- **SQLite 3+** (usually pre-installed)
- **pip** (Python package manager)

### Network Requirements

```
Internet Connectivity: Yes (for updates, threat intel)
Firewall Ports:
  ├─ 2222 (SSH honeypot)
  ├─ 8888 (HTTP honeypot)
  ├─ 1900 (SSDP honeypot)
  └─ 5000 (Web dashboard)

Open to Internet: Ports 2222, 8888, 1900
Dashboard Access: 5000 (restrict by IP)
```

---

## Installation Methods

### Method 1: Docker (Recommended)

#### Step 1: Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/ddospot.git
cd ddospot
```

#### Step 3: Build Docker Image

```bash
# Build the image
docker build -t ddospot:latest .

# Or use docker-compose (faster)
docker-compose -f docker-compose-prod.yml build
```

#### Step 4: Run Container

```bash
# Production deployment
docker-compose -f docker-compose-prod.yml up -d

# Development deployment
docker-compose -f docker-compose-dev.yml up -d

# View logs
docker-compose logs -f ddospot
```

#### Step 5: Verify Installation

```bash
# Check if container is running
docker ps | grep ddospot

# Check logs for errors
docker logs ddospot

# Test SSH honeypot
ssh -p 2222 localhost

# Test HTTP honeypot
curl http://localhost:8888

# Access dashboard
open http://localhost:5000
```

---

### Method 2: Native Installation (Linux)

#### Step 1: Install Python Dependencies

```bash
# Update package manager
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y \
  python3.10 \
  python3.10-venv \
  python3-pip \
  git \
  curl \
  sqlite3 \
  build-essential

# Verify Python version
python3 --version  # Should be 3.10+
```

#### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ddospot.git
cd ddospot

# Or download as ZIP
wget https://github.com/yourusername/ddospot/archive/refs/heads/main.zip
unzip main.zip
cd ddospot-main
```

#### Step 3: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
python --version
```

#### Step 4: Install Python Requirements

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "flask|sqlalchemy"
```

#### Step 5: Configure DDoSPoT

```bash
# Copy example configuration
cp config/config.example.json config/config.json
cp config/alert_config.example.json config/alert_config.json

# Edit configuration
nano config/config.json
# Set your settings (see Configuration section below)
```

#### Step 6: Initialize Database

```bash
# Initialize database
python start-honeypot.py --init-db

# Verify database
sqlite3 ddospot.db ".tables"
```

#### Step 7: Start DDoSPoT

```bash
# Terminal 1: Start honeypot
python start-honeypot.py

# Terminal 2 (new): Start dashboard
python start-dashboard.py

# Verify services
curl http://localhost:5000  # Dashboard
ssh -p 2222 localhost       # SSH honeypot
curl http://localhost:8888  # HTTP honeypot
```

---

### Method 3: Systemd Service (Production)

#### Step 1: Create Service Files

```bash
# Create honeypot service
sudo nano /etc/systemd/system/ddospot-honeypot.service
```

```ini
[Unit]
Description=DDoSPoT Honeypot Service
After=network.target
Wants=ddospot-dashboard.service

[Service]
Type=simple
User=ddospot
WorkingDirectory=/opt/ddospot
ExecStart=/opt/ddospot/venv/bin/python start-honeypot.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

```bash
# Create dashboard service
sudo nano /etc/systemd/system/ddospot-dashboard.service
```

```ini
[Unit]
Description=DDoSPoT Dashboard Service
After=network.target

[Service]
Type=simple
User=ddospot
WorkingDirectory=/opt/ddospot
ExecStart=/opt/ddospot/venv/bin/python start-dashboard.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

#### Step 2: Enable Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable ddospot-honeypot.service
sudo systemctl enable ddospot-dashboard.service

# Start services
sudo systemctl start ddospot-honeypot.service
sudo systemctl start ddospot-dashboard.service

# Check status
sudo systemctl status ddospot-honeypot.service
sudo systemctl status ddospot-dashboard.service
```

#### Step 3: Monitor Services

```bash
# View logs
sudo journalctl -u ddospot-honeypot.service -f
sudo journalctl -u ddospot-dashboard.service -f

# Check if running
systemctl is-active ddospot-honeypot.service
```

---

## Configuration

### Basic Configuration

```json
{
  "honeypots": {
    "ssh": {
      "enabled": true,
      "port": 2222,
      "banner": "SSH-2.0-OpenSSH_7.4"
    },
    "http": {
      "enabled": true,
      "port": 8888,
      "content_type": "wordpress"
    },
    "ssdp": {
      "enabled": true,
      "port": 1900,
      "device_model": "Generic-Router"
    }
  },
  "detection": {
    "enabled": true,
    "ml_enabled": true,
    "threat_threshold": 0.5
  },
  "response": {
    "enabled": true,
    "auto_block": true,
    "block_duration": 3600
  },
  "database": {
    "path": "/var/lib/ddospot/ddospot.db"
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/ddospot/honeypot.log"
  }
}
```

### Alert Configuration

```json
{
  "alerts": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender": "ddospot@company.com",
      "recipients": ["security@company.com"],
      "min_severity": "HIGH"
    },
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "min_severity": "HIGH"
    },
    "webhook": {
      "enabled": false,
      "url": "https://your-api.com/alerts",
      "min_severity": "MEDIUM"
    }
  }
}
```

---

## First-Time Setup Checklist

### Pre-Installation
- [ ] System meets minimum requirements
- [ ] 20+ GB disk space available
- [ ] Network ports 2222, 8888, 1900 accessible
- [ ] Python 3.8+ installed
- [ ] Git or download zip ready

### Installation
- [ ] Repository cloned/downloaded
- [ ] Virtual environment created (if native)
- [ ] Requirements installed
- [ ] Database initialized
- [ ] Configuration files created

### Configuration
- [ ] Edited config.json with your settings
- [ ] Set alert recipients
- [ ] Configured notification channels
- [ ] Set response thresholds
- [ ] Configured IP blocking

### Verification
- [ ] Honeypot service running
- [ ] Dashboard accessible on port 5000
- [ ] SSH port 2222 responding
- [ ] HTTP port 8888 responding
- [ ] SSDP port 1900 responding

### Testing
- [ ] Test SSH connection attempt
- [ ] Test HTTP request
- [ ] Check dashboard shows connections
- [ ] Test alert notification
- [ ] Verify IP blocking

---

## Troubleshooting Installation

### Issue: Port Already in Use

```bash
# Find what's using port 2222
sudo lsof -i :2222

# Kill process using port
sudo kill -9 <PID>

# Or change port in config.json
{
  "honeypots": {
    "ssh": {
      "port": 2223  # Changed from 2222
    }
  }
}
```

### Issue: Permission Denied

```bash
# Grant permissions to user
sudo chown -R $USER:$USER ddospot/

# Or run with sudo
sudo python start-honeypot.py
```

### Issue: Database Error

```bash
# Reset database
rm ddospot.db
python start-honeypot.py --init-db

# Check database integrity
sqlite3 ddospot.db "PRAGMA integrity_check;"
```

### Issue: ModuleNotFoundError

```bash
# Check virtual environment is activated
which python  # Should show venv path

# Reinstall requirements
pip install --force-reinstall -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

### Issue: Can't Access Dashboard

```bash
# Check if service is running
curl http://localhost:5000

# Check logs
tail -f logs/dashboard.log

# Verify port 5000 is open
sudo lsof -i :5000

# Test connectivity
netstat -tulpn | grep 5000
```

---

## Verification Steps

### Test Honeypot Connectivity

```bash
# Test SSH honeypot
ssh -v -p 2222 localhost
# Expected: SSH banner response, then connection closed

# Test HTTP honeypot
curl -v http://localhost:8888/
# Expected: HTTP 200 response with fake content

# Test SSDP honeypot
echo "M-SEARCH * HTTP/1.1" | nc -u localhost 1900
# Expected: SSDP response
```

### Check Logs

```bash
# View honeypot log
tail -f logs/honeypot.log

# View dashboard log
tail -f logs/dashboard.log

# Count entries
wc -l logs/honeypot.log

# Search for attacks
grep "ATTACK\|BLOCKED" logs/honeypot.log
```

### Verify Services

```bash
# Docker
docker ps
docker logs ddospot

# Systemd
systemctl status ddospot-honeypot
systemctl status ddospot-dashboard

# Native
ps aux | grep python
```

---

## Performance Tuning

### For Small Deployments

```json
{
  "database": {
    "connections": 5,
    "timeout": 10
  },
  "honeypots": {
    "max_concurrent": 1000
  }
}
```

### For Large Deployments

```json
{
  "database": {
    "connections": 20,
    "timeout": 5,
    "pool_size": 15
  },
  "honeypots": {
    "max_concurrent": 10000,
    "buffer_size": 1024
  },
  "detection": {
    "batch_size": 100,
    "worker_threads": 4
  }
}
```

### Monitor Resources

```bash
# CPU and Memory
top -p $(pgrep -f start-honeypot.py)

# Disk usage
du -sh ddospot/
du -sh ddospot.db

# Network connections
ss -s
ss -tnp | grep 2222
ss -tnp | grep 8888
```

---

## Next Steps

1. **Monitor Dashboard**: [Monitoring Threats](09_Monitoring_Threats.md)
2. **Configure Alerts**: [Configuration Management](10_Configuration_Management.md)
3. **Test Attack**: [Testing & Validation](08_Setting_Up_DDoSPoT.md#testing)
4. **Deploy Monitoring**: [Monitoring and Alerting](19_Monitoring_and_Alerting.md)

---

## Quick Start Commands

```bash
# Docker quick start
docker-compose -f docker-compose-prod.yml up -d
open http://localhost:5000

# Native quick start
source venv/bin/activate
python start-honeypot.py &
python start-dashboard.py &
open http://localhost:5000

# Systemd quick start
sudo systemctl start ddospot-honeypot.service
sudo systemctl start ddospot-dashboard.service
sudo journalctl -u ddospot-honeypot.service -f
```

---

## Common Configuration Scenarios

### Scenario 1: Small Office

```json
{
  "honeypots": {
    "ssh": {"enabled": true, "port": 2222},
    "http": {"enabled": true, "port": 8888},
    "ssdp": {"enabled": false}
  },
  "response": {"auto_block": true, "block_duration": 3600},
  "alerts": {"email": {"enabled": true}, "slack": {"enabled": true}}
}
```

### Scenario 2: Enterprise

```json
{
  "honeypots": {
    "ssh": {"enabled": true, "port": 2222},
    "http": {"enabled": true, "port": 8888},
    "ssdp": {"enabled": true, "port": 1900}
  },
  "response": {"auto_block": true, "block_duration": 86400},
  "alerts": {
    "email": {"enabled": true},
    "slack": {"enabled": true},
    "webhook": {"enabled": true}
  },
  "database": {"backup": {"enabled": true, "frequency": "daily"}}
}
```

### Scenario 3: Research Lab

```json
{
  "honeypots": {
    "ssh": {"enabled": true, "port": 2222},
    "http": {"enabled": true, "port": 8888},
    "ssdp": {"enabled": true, "port": 1900}
  },
  "logging": {
    "level": "DEBUG",
    "capture_full_request": true,
    "capture_payload": true
  },
  "response": {"auto_block": false},
  "alerts": {"webhook": {"enabled": true}}
}
```

---

## Key Takeaways

1. **Easy Setup**: Docker recommended for fastest deployment
2. **Flexible**: Native installation for custom configurations
3. **Production-Ready**: Systemd integration for auto-start
4. **Verified**: Simple testing to confirm everything works
5. **Optimizable**: Can be tuned for different scales

---

## Review Questions

1. What are the minimum system requirements?
2. What's the quickest way to get DDoSPoT running?
3. How do you verify the honeypot is working?
4. What ports need to be open for DDoSPoT?
5. How would you configure DDoSPoT for your organization?

## Additional Resources

- [Quick Start Guide](00_QUICK_START.md)
- [Docker Deployment](../docs/DOCKER_DEPLOYMENT.md)
- [Configuration Management](10_Configuration_Management.md)
- [Troubleshooting](21_Troubleshooting.md)
