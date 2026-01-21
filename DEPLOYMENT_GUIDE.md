# DDoSPoT Production Deployment Guide

Complete guide for deploying DDoSPoT honeypot system to production with monitoring, alerting, and high availability.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Nginx Reverse Proxy Setup](#nginx-reverse-proxy-setup)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Monitoring Stack Configuration](#monitoring-stack-configuration)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)
9. [Security Hardening](#security-hardening)
10. [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS or Rocky Linux 9+
- **CPU**: 4 cores minimum (8+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended for monitoring)
- **Storage**: 50GB minimum (100GB+ for long-term logs)
- **Network**: Static IP address, ports 80/443 open for web traffic

### Required Software
```bash
# Install system dependencies
sudo apt update && sudo apt install -y \
    docker.io \
    docker-compose-plugin \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    htpasswd \
    systemd

# Verify installations
docker --version
docker compose version
nginx -v
```

### User & Permissions
```bash
# Create ddospot user
sudo useradd -m -d /opt/ddospot -s /bin/bash ddospot

# Add current user to docker group (optional, restart required)
sudo usermod -aG docker $USER

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker
```

---

## Pre-Deployment Checklist

### Configuration Items
- [ ] Domain name ready (e.g., ddospot.example.com)
- [ ] Email address for SSL certificates
- [ ] SMTP server configured (for email alerts)
- [ ] Slack webhook URL (if using Slack alerts)
- [ ] PagerDuty API key (if using PagerDuty)
- [ ] Strong API token generated (`openssl rand -hex 32`)
- [ ] Backup storage location identified
- [ ] External IP whitelist for admin access (optional)

### Security Preparation
- [ ] Firewall rules configured
- [ ] SSH key-based access configured
- [ ] Root login disabled
- [ ] Fail2ban installed and configured
- [ ] UFW or iptables rules in place

### Network Validation
```bash
# Test connectivity to required ports
curl https://example.com  # Ensure DNS resolves
nc -zv example.com 443    # Test HTTPS port
```

---

## Step-by-Step Deployment

### Step 1: Clone Repository and Setup Directory

```bash
# Clone the DDoSPoT repository
sudo -u ddospot git clone https://github.com/your-org/ddospot.git /opt/ddospot
cd /opt/ddospot

# Create directory structure
sudo -u ddospot mkdir -p /opt/ddospot/{backups,logs,config}
sudo -u ddospot mkdir -p /var/lib/ddospot/{prometheus,grafana,alertmanager}
```

### Step 2: Create Production Environment File

```bash
# Copy template
sudo cp /opt/ddospot/.env.prod.template /opt/ddospot/.env.prod

# Edit with production values
sudo nano /opt/ddospot/.env.prod
```

**Critical environment variables** to set:
```env
# API Security
DDOSPOT_API_TOKEN=<your-strong-token-here>
DDOSPOT_REQUIRE_TOKEN=true

# Network
DDOSPOT_HOST=0.0.0.0
DDOSPOT_PORT=5000
DDOSPOT_WORKERS=4

# Database
DDOSPOT_DB_PATH=/var/lib/ddospot/honeypot.db

# Monitoring
DDOSPOT_METRICS_ENABLED=true
DDOSPOT_METRICS_PUBLIC=false

# Rate Limiting
DDOSPOT_RATE_LIMIT_ENABLED=true
DDOSPOT_RATE_LIMIT_REQUESTS=50
DDOSPOT_RATE_LIMIT_WINDOW=60

# Alerts
DDOSPOT_ALERT_THRESHOLD_HIGH=1000
DDOSPOT_ALERT_THRESHOLD_CRITICAL=5000

# SMTP Configuration
DDOSPOT_SMTP_SERVER=smtp.gmail.com
DDOSPOT_SMTP_PORT=587
DDOSPOT_SMTP_USERNAME=your-email@gmail.com
DDOSPOT_SMTP_PASSWORD=<app-password>
DDOSPOT_SMTP_FROM=alerts@ddospot.local

# Slack Configuration (optional)
DDOSPOT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# PagerDuty Configuration (optional)
DDOSPOT_PAGERDUTY_KEY=<your-pagerduty-integration-key>
```

### Step 3: Set Secure Permissions

```bash
# Set ownership
sudo chown -R ddospot:ddospot /opt/ddospot
sudo chown -R ddospot:ddospot /var/lib/ddospot

# Set restrictive permissions
sudo chmod 750 /opt/ddospot
sudo chmod 750 /var/lib/ddospot
sudo chmod 600 /opt/ddospot/.env.prod

# Verify
ls -la /opt/ddospot/.env.prod
```

### Step 4: Deploy Docker Compose Stack

```bash
# Navigate to deployment directory
cd /opt/ddospot

# Create Docker Compose override for production paths
cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  ddospot-dashboard:
    volumes:
      - /opt/ddospot:/app
      - /var/lib/ddospot:/data

  prometheus:
    volumes:
      - /var/lib/ddospot/prometheus:/prometheus

  grafana:
    volumes:
      - /var/lib/ddospot/grafana:/var/lib/grafana

  alertmanager:
    volumes:
      - /var/lib/ddospot/alertmanager:/alertmanager
EOF

# Build and start services
sudo docker compose build
sudo docker compose up -d

# Verify services
sudo docker compose ps
docker compose logs -f
```

### Step 5: Setup Systemd Services

```bash
# Copy systemd service files
sudo cp systemd/ddospot-honeypot.service /etc/systemd/system/
sudo cp systemd/ddospot-dashboard.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable ddospot-honeypot.service
sudo systemctl enable ddospot-dashboard.service
sudo systemctl start ddospot-honeypot.service
sudo systemctl start ddospot-dashboard.service

# Check status
sudo systemctl status ddospot-honeypot.service
sudo systemctl status ddospot-dashboard.service
```

### Step 6: Configure Nginx Reverse Proxy

```bash
# Create Nginx directories
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

# Copy Nginx configuration
sudo cp nginx/ddospot.conf /etc/nginx/sites-available/ddospot

# Create basic auth file for admin endpoints
sudo htpasswd -c /etc/nginx/.htpasswd admin
# Enter secure password when prompted

# Enable site
sudo ln -s /etc/nginx/sites-available/ddospot /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 7: SSL/TLS Setup with Let's Encrypt

See [SSL/TLS Configuration](#ssltls-configuration) section below.

---

## Nginx Reverse Proxy Setup

The Nginx configuration handles:
- HTTPS termination with TLS 1.2+
- Rate limiting at proxy level
- Request routing to application
- Static file caching
- Security headers
- Admin endpoint protection

### Key Features

**1. HTTPS Redirect**
```nginx
# All HTTP traffic redirected to HTTPS
location / {
    return 301 https://$server_name$request_uri;
}
```

**2. Rate Limiting**
```nginx
# Limit to 10 requests per second per IP
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

**3. Admin Protection**
```nginx
# Basic auth for sensitive endpoints
auth_basic "DDoSPoT Metrics";
auth_basic_user_file /etc/nginx/.htpasswd;
```

**4. Security Headers**
```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
```

---

## SSL/TLS Configuration

### Automatic SSL with Let's Encrypt

```bash
# Run Certbot with Nginx plugin
sudo certbot certonly --nginx -d ddospot.example.com

# Follow prompts:
# - Enter email for certificate renewal notifications
# - Accept Let's Encrypt terms
# - Choose option 1 for email notifications (recommended)

# Verify certificate
sudo certbot certificates

# Auto-renewal (certbot handles this automatically)
sudo systemctl status snap.certbot.renew.timer
```

### Manual SSL Certificate

If using self-signed or external certificates:

```bash
# Place certificates in /etc/letsencrypt/live/ddospot.example.com/
# - fullchain.pem (certificate chain)
# - privkey.pem (private key)

# Update Nginx configuration with paths
sudo nano /etc/nginx/sites-available/ddospot
# Edit:
# ssl_certificate /path/to/cert.pem;
# ssl_certificate_key /path/to/key.pem;

# Reload Nginx
sudo systemctl reload nginx
```

### Certificate Validation

```bash
# Test SSL/TLS configuration
sudo openssl s_client -connect localhost:443

# Check certificate expiration
sudo openssl x509 -in /etc/letsencrypt/live/ddospot.example.com/fullchain.pem -noout -dates

# Test from external site
curl -I https://ddospot.example.com
```

---

## Monitoring Stack Configuration

### Prometheus Setup

**Data Retention**: 30 days (configured in docker-compose.prod.yml)

```bash
# Verify Prometheus is running
docker compose logs prometheus | head -20

# Access Prometheus UI
# http://localhost:9090 (from behind Nginx)
# Browse → Status → Targets to verify data collection

# Query metrics (example)
curl "http://localhost:9090/api/v1/query?query=ddospot_requests_total"
```

### Grafana Dashboard Setup

```bash
# Access Grafana
# http://localhost:3000 (from behind Nginx)

# Initial login (default credentials)
# Username: admin
# Password: admin
# **IMPORTANT**: Change password immediately!

# Add Prometheus as data source:
# Configuration → Data Sources → Add
# - Name: Prometheus
# - URL: http://prometheus:9090
# - Save & Test

# Import DDoSPoT dashboard:
# Create → Import
# Paste dashboard JSON from /monitoring/grafana-dashboards/
```

### Alertmanager Configuration

**Alert Routing**:
- **Critical** (5000+ events): PagerDuty + Email
- **High** (1000+ events): Slack + Email  
- **Info** (<1000 events): Email only

```bash
# Verify Alertmanager config
docker compose exec alertmanager amtool config routes

# Test alert routing
docker compose exec alertmanager amtool alert

# View active alerts
curl http://localhost:9093/api/v1/alerts
```

---

## Backup & Recovery

### Automated Backups

Create backup script at `/opt/ddospot/backup.sh`:

```bash
#!/bin/bash
# Daily backup script for DDoSPoT

BACKUP_DIR="/opt/ddospot/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ddospot_backup_$TIMESTAMP.tar.gz"

# Create backup
tar -czf "$BACKUP_FILE" \
    /var/lib/ddospot/honeypot.db \
    /var/lib/ddospot/prometheus \
    /opt/ddospot/.env.prod \
    /opt/ddospot/alert_config.json

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

# Upload to remote storage (S3, NAS, etc.)
aws s3 cp "$BACKUP_FILE" s3://ddospot-backups/

echo "Backup completed: $BACKUP_FILE"
```

**Schedule with cron**:

```bash
# Add to crontab
(sudo -u ddospot crontab -l; echo "0 2 * * * /opt/ddospot/backup.sh") | sudo -u ddospot crontab -
```

### Manual Backup

```bash
# Backup application data
sudo tar -czf /opt/ddospot/backups/manual_backup_$(date +%s).tar.gz \
    /var/lib/ddospot \
    /opt/ddospot/.env.prod

# Backup with docker compose volumes
sudo docker compose exec prometheus tar -czf - /prometheus | \
    sudo tee /opt/ddospot/backups/prometheus_$(date +%s).tar.gz > /dev/null
```

### Recovery Procedure

```bash
# Stop services
sudo systemctl stop ddospot-dashboard.service
sudo docker compose down

# Restore from backup
sudo tar -xzf /opt/ddospot/backups/ddospot_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Restart services
sudo docker compose up -d
sudo systemctl start ddospot-dashboard.service

# Verify recovery
sudo docker compose ps
sudo systemctl status ddospot-dashboard.service
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker logs
sudo docker compose logs -f

# Check systemd journal
sudo journalctl -u ddospot-dashboard.service -n 50
sudo journalctl -u ddospot-honeypot.service -n 50

# Verify environment file
sudo cat /opt/ddospot/.env.prod

# Check permissions
ls -la /opt/ddospot
ls -la /var/lib/ddospot
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :5000
sudo lsof -i :9090
sudo lsof -i :3000

# Kill process
sudo kill -9 <PID>

# Or change port in .env.prod
DDOSPOT_PORT=5001
```

### Nginx Configuration Error

```bash
# Test Nginx config
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify upstream connectivity
curl http://127.0.0.1:5000

# Check SSL certificates
sudo certbot certificates
```

### Database Connection Errors

```bash
# Check database file
ls -la /var/lib/ddospot/honeypot.db

# Verify permissions
sudo chown ddospot:ddospot /var/lib/ddospot/honeypot.db
sudo chmod 644 /var/lib/ddospot/honeypot.db

# Reinitialize database
cd /opt/ddospot
sudo -u ddospot python3 -c "from core.database import init_db; init_db()"
```

### Monitoring Stack Issues

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify Grafana datasources
curl http://localhost:3000/api/datasources

# Check Alertmanager configuration
docker compose exec alertmanager amtool config

# View Prometheus logs
docker compose logs prometheus
```

---

## Security Hardening

### Production Security Checklist

- [ ] **SSH**: Disable root login, use key-based auth
- [ ] **Firewall**: Configure UFW or iptables
- [ ] **Fail2ban**: Protect against brute-force attacks
- [ ] **API Token**: Strong random value (32+ characters)
- [ ] **HTTPS**: Valid SSL certificate, TLS 1.2+
- [ ] **Admin Auth**: Basic auth on sensitive endpoints
- [ ] **Database**: Encrypted backups, secure permissions
- [ ] **Logs**: Centralized logging, rotate regularly
- [ ] **Updates**: Regular security patches
- [ ] **Monitoring**: Alert on security events

### Firewall Configuration (UFW)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block internal ports (only for Docker bridge)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Verify rules
sudo ufw status
```

### Fail2ban Setup

```bash
# Install Fail2ban
sudo apt install fail2ban

# Create filter for DDoSPoT
sudo cat > /etc/fail2ban/filter.d/ddospot.conf << 'EOF'
[Definition]
failregex = ^<HOST> .*"POST /api/.*" 40[13]
ignoreregex =
EOF

# Create jail
sudo cat > /etc/fail2ban/jail.d/ddospot.conf << 'EOF'
[ddospot]
enabled = true
port = http,https
filter = ddospot
logpath = /var/log/nginx/ddospot-access.log
maxretry = 5
findtime = 600
bantime = 3600
EOF

# Enable and restart
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban
```

---

## Post-Deployment Verification

### Health Checks

```bash
# 1. Dashboard health
curl -I https://ddospot.example.com/health

# 2. API connectivity
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
    https://ddospot.example.com/api/stats

# 3. Prometheus metrics
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
    https://ddospot.example.com/metrics

# 4. Docker services
sudo docker compose ps
# All services should be 'Up'

# 5. Systemd services
sudo systemctl status ddospot-honeypot.service
sudo systemctl status ddospot-dashboard.service
# Both should be 'active (running)'

# 6. Port connectivity
sudo netstat -tlnp | grep LISTEN
```

### Performance Validation

```bash
# Check resource usage
docker stats

# Monitor CPU/Memory
top -p $(pgrep -f "python.*dashboard.py" | tr '\n' ',')

# Check network traffic
sudo iftop

# Database query performance
sqlite3 /var/lib/ddospot/honeypot.db "SELECT COUNT(*) FROM honeypot_events;"
```

### Alert System Verification

```bash
# Test email alert delivery
# Trigger alert via API or check alert configuration

# Verify Slack webhook (if configured)
curl -X POST -d '{"text":"Test alert"}' $DDOSPOT_SLACK_WEBHOOK

# Check PagerDuty integration
# Use PagerDuty console to verify events are received
```

### Log Review

```bash
# Check application logs
sudo journalctl -u ddospot-dashboard.service --no-pager | head -50

# Check Nginx access/error logs
sudo tail -20 /var/log/nginx/ddospot-access.log
sudo tail -20 /var/log/nginx/ddospot-error.log

# Check Docker container logs
sudo docker compose logs --tail=50 ddospot-dashboard
```

---

## Maintenance Procedures

### Regular Backups
- Daily automated backups (configured in cron)
- Weekly full system snapshots
- Monthly off-site backup verification
- Quarterly restore drills

### Log Rotation
```bash
# Configure logrotate
sudo cat > /etc/logrotate.d/ddospot << 'EOF'
/var/log/ddospot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ddospot ddospot
    sharedscripts
}
EOF
```

### Certificate Renewal
```bash
# Manual renewal (if needed)
sudo certbot renew --force-renewal

# Automatic renewal (handled by certbot timer)
sudo systemctl start snap.certbot.renew.timer
```

### System Updates
```bash
# Security updates
sudo apt update && sudo apt upgrade -y

# Docker image updates
cd /opt/ddospot
sudo docker compose pull
sudo docker compose up -d
```

### Monitor Disk Space
```bash
# Check available space
df -h /var/lib/ddospot

# If low on space:
# 1. Archive old databases
# 2. Clean Prometheus data retention
# 3. Remove old Docker images
docker image prune -a
```

---

## Support & Escalation

For issues, follow this escalation path:

1. **Check logs** (application, Nginx, Docker, systemd)
2. **Review troubleshooting guide** (above)
3. **Verify configuration** (.env.prod, docker-compose.yml, nginx config)
4. **Restart services** (systemctl restart, docker compose restart)
5. **Contact support** with logs and configuration

---

## Appendix: Useful Commands

```bash
# View service status
sudo systemctl status ddospot-*

# Restart services
sudo systemctl restart ddospot-dashboard.service
sudo docker compose restart

# View logs
sudo journalctl -u ddospot-dashboard.service -f
docker compose logs -f

# Database query
sqlite3 /var/lib/ddospot/honeypot.db "SELECT * FROM honeypot_events LIMIT 10;"

# API token rotation
# Edit .env.prod, generate new token, restart services

# Backup now
/opt/ddospot/backup.sh

# Restore from backup
# See Recovery Procedure section
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Maintainer**: DDoSPoT Operations Team
