# DDoSPoT Production Deployment Documentation

Complete production deployment package for the DDoSPoT honeypot detection system.

## 📋 Overview

This directory contains everything needed to deploy DDoSPoT to production with:
- **Containerized deployment** (Docker Compose)
- **System-level process management** (Systemd)
- **Enterprise monitoring** (Prometheus + Grafana)
- **Automated alerting** (Alertmanager)
- **HTTPS with SSL/TLS** (Let's Encrypt ready)
- **Automated backups** (with retention policies)
- **Security hardening** (rate limiting, token auth, firewall)

## 🚀 Quick Start (Automated)

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/your-org/ddospot.git /opt/ddospot
cd /opt/ddospot

# Run automated setup (requires root)
sudo bash setup-production.sh
```

This script automatically:
- Creates system user and directories
- Configures Docker Compose
- Sets up Nginx reverse proxy
- Installs Systemd services
- Configures automated backups
- Sets up firewall rules
- Starts all services

## 📚 Documentation

### Core Guides
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step manual deployment
- **[OPERATIONS_PLAYBOOK.md](OPERATIONS_PLAYBOOK.md)** - Common operational tasks
- **[SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)** - Security validation checklist

### Configuration Files
- **[docker-compose.prod.yml](docker-compose.prod.yml)** - Production Docker stack
- **[.env.prod.template](.env.prod.template)** - Environment configuration template
- **[nginx/ddospot.conf](nginx/ddospot.conf)** - Nginx reverse proxy config
- **[systemd/ddospot-honeypot.service](systemd/ddospot-honeypot.service)** - Honeypot service unit
- **[systemd/ddospot-dashboard.service](systemd/ddospot-dashboard.service)** - Dashboard service unit
- **[monitoring/alertmanager.yml](monitoring/alertmanager.yml)** - Alert routing config
- **[monitoring/grafana-datasources.yml](monitoring/grafana-datasources.yml)** - Grafana config

### Operational Scripts
- **[backup.sh](backup.sh)** - Automated backup (daily recommended)
- **[restore.sh](restore.sh)** - Data recovery procedure
- **[setup-production.sh](setup-production.sh)** - Automated deployment setup

## 🔧 System Requirements

### Minimum
- **OS**: Ubuntu 22.04 LTS / Rocky Linux 9+
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB
- **Network**: Static IP, ports 80/443 open

### Recommended for Production
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 100GB+ (for long-term logs)
- **Redundancy**: High-availability setup

## 📦 What's Included

### Services
| Service | Port | Purpose |
|---------|------|---------|
| DDoSPoT Dashboard | 5000 | Web UI & API |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Visualization |
| Alertmanager | 9093 | Alert routing |
| Node Exporter | 9100 | System metrics |

### Features
- ✅ Multi-service orchestration with Docker Compose
- ✅ HTTP to HTTPS redirect (reverse proxy)
- ✅ SSL/TLS with Let's Encrypt support
- ✅ Rate limiting (API & request level)
- ✅ Token-based API authentication
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards
- ✅ Multi-channel alerting (email, Slack, PagerDuty)
- ✅ Automated daily backups
- ✅ System-level monitoring & logging
- ✅ Security hardening with systemd
- ✅ UFW firewall configuration

## 🛠️ Manual Deployment Steps

### Step 1: Prerequisites

```bash
# Install system dependencies
sudo apt update && sudo apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx git

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### Step 2: Configure Environment

```bash
# Copy to production location
sudo cp .env.prod.template /opt/ddospot/.env.prod

# Edit with your settings
sudo nano /opt/ddospot/.env.prod
```

**Critical settings**:
- `DDOSPOT_API_TOKEN` - Strong random token
- `DDOSPOT_SMTP_*` - Email configuration
- `DDOSPOT_SLACK_WEBHOOK` - (optional) Slack integration

### Step 3: Deploy Containers

```bash
# Build and start
cd /opt/ddospot
sudo docker-compose -f docker-compose.prod.yml build
sudo docker-compose -f docker-compose.prod.yml up -d

# Verify
sudo docker-compose ps
```

### Step 4: Setup SSL/TLS

```bash
# Get certificate from Let's Encrypt
sudo certbot certonly --standalone -d ddospot.example.com
```

### Step 5: Configure Nginx

```bash
# Copy configuration
sudo cp nginx/ddospot.conf /etc/nginx/sites-available/ddospot
sudo ln -s /etc/nginx/sites-available/ddospot /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Setup Systemd Services

```bash
# Install services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ddospot-honeypot.service ddospot-dashboard.service
sudo systemctl start ddospot-honeypot.service ddospot-dashboard.service
```

### Step 7: Configure Backups

```bash
# Make backup script executable
chmod +x backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/ddospot/backup.sh") | crontab -
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 🔐 Security Considerations

### Before Deployment
- [ ] Generate strong API token (`openssl rand -hex 32`)
- [ ] Configure SMTP for alerts
- [ ] Setup SSL/TLS certificate
- [ ] Configure firewall rules
- [ ] Review and customize `.env.prod`
- [ ] Set restrictive file permissions

### After Deployment
- [ ] Verify firewall rules
- [ ] Test SSL/TLS certificate
- [ ] Validate authentication works
- [ ] Test backup & recovery
- [ ] Review monitoring alerts
- [ ] Check application logs

See [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) for comprehensive security checklist.

## 📊 Monitoring & Dashboards

### Access Points
- **Dashboard**: https://ddospot.example.com/
- **Grafana**: https://ddospot.example.com/grafana/
- **Prometheus**: https://ddospot.example.com/prometheus/ (admin only)
- **Alertmanager**: https://ddospot.example.com/alertmanager/ (admin only)

### Default Credentials
| Service | User | Password |
|---------|------|----------|
| Grafana | admin | admin |
| Nginx | admin | *set during setup* |

⚠️ **Change all default passwords immediately!**

## 🚨 Alert Configuration

### Alert Channels

**Email Alerts**
```
DDOSPOT_SMTP_SERVER=smtp.gmail.com
DDOSPOT_SMTP_PORT=587
DDOSPOT_SMTP_USERNAME=your-email@gmail.com
DDOSPOT_SMTP_PASSWORD=<app-password>
```

**Slack Alerts**
```
DDOSPOT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**PagerDuty Alerts**
```
DDOSPOT_PAGERDUTY_KEY=<your-integration-key>
```

## 💾 Backup & Recovery

### Automated Backups
```bash
# Configured daily at 2 AM via cron
0 2 * * * /opt/ddospot/backup.sh
```

### Manual Backup
```bash
/opt/ddospot/backup.sh
```

### Recovery
```bash
# List available backups
ls -lh /opt/ddospot/backups/

# Restore from specific backup
./restore.sh /opt/ddospot/backups/ddospot_backup_YYYYMMDD_HHMMSS.tar.gz
```

## 🔧 Troubleshooting

### Services Won't Start
```bash
# Check status
sudo systemctl status ddospot-dashboard.service
docker-compose logs

# Common issues: missing .env.prod, port already in use, database corruption
```

### High CPU/Memory
```bash
# Monitor usage
docker stats
top

# Solution: restart service, check for memory leaks
sudo systemctl restart ddospot-dashboard.service
```

### Database Issues
```bash
# Check integrity
sqlite3 /var/lib/ddospot/honeypot.db "PRAGMA integrity_check;"

# Solution: restore from backup
./restore.sh /opt/ddospot/backups/[backup_file]
```

See [OPERATIONS_PLAYBOOK.md](OPERATIONS_PLAYBOOK.md) for detailed troubleshooting.

## 📈 Performance Optimization

### Scaling Configuration
```env
# Increase workers for high load
DDOSPOT_WORKERS=8

# Increase rate limit threshold
DDOSPOT_RATE_LIMIT_REQUESTS=100
DDOSPOT_RATE_LIMIT_WINDOW=60
```

### Database Optimization
```bash
# Optimize database
sqlite3 /var/lib/ddospot/honeypot.db "VACUUM;"
sqlite3 /var/lib/ddospot/honeypot.db "ANALYZE;"
```

### Monitoring Stack Optimization
```bash
# Adjust Prometheus retention
# Edit docker-compose.prod.yml --storage.tsdb.retention.time=15d
```

## 🆘 Support & Issues

### Getting Help
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions
2. Review [OPERATIONS_PLAYBOOK.md](OPERATIONS_PLAYBOOK.md) for common issues
3. Consult [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) for security questions
4. Check application logs: `sudo journalctl -u ddospot-dashboard.service -f`
5. Contact support team (see OPERATIONS_PLAYBOOK.md for contacts)

### Reporting Issues
Include in bug reports:
- System info: `uname -a`
- Service status: `sudo systemctl status ddospot-*`
- Docker status: `docker-compose ps`
- Error logs: `docker-compose logs`
- Configuration: sanitized `.env.prod`

## 📝 Maintenance Schedule

### Daily
- Monitor dashboard
- Review error logs
- Check disk space

### Weekly
- Verify backups completed
- Review security logs
- Update system packages

### Monthly
- Run full backups
- Verify recovery procedures
- Security audit

### Quarterly
- Penetration testing
- Performance analysis
- Disaster recovery drill

### Annually
- Full security assessment
- Compliance audit
- Infrastructure review

## 📄 License

DDoSPoT is released under the MIT License. See LICENSE file for details.

## 🙏 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Version**: 1.0  
**Last Updated**: 2024  
**Maintainer**: DDoSPoT Operations Team

For more information, visit: https://github.com/your-org/ddospot
