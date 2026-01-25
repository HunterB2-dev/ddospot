# Production Deployment Files Index

Complete list of all production deployment components for DDoSPoT honeypot system.

## 📚 Documentation Files (4)

### Core Guides
1. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** (800+ lines)
   - Comprehensive step-by-step deployment instructions
   - System requirements and prerequisites
   - Pre-deployment checklist
   - Complete deployment process (7 steps)
   - Nginx reverse proxy configuration
   - SSL/TLS setup with Let's Encrypt
   - Monitoring stack configuration
   - Backup and recovery procedures
   - Troubleshooting guide for 10+ common issues
   - Maintenance procedures
   
   **Use when**: Following manual deployment steps

2. **[OPERATIONS_PLAYBOOK.md](OPERATIONS_PLAYBOOK.md)** (600+ lines)
   - Quick reference command guide
   - 10 common operational scenarios with solutions
   - Service control procedures
   - Emergency procedures (service failure, data loss, security)
   - Maintenance window procedures
   - Performance optimization tips
   - Runbook templates
   - Support contacts and escalation paths
   
   **Use when**: Troubleshooting issues or performing routine operations

3. **[SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)** (500+ lines)
   - 18-category comprehensive security validation checklist
   - Pre-deployment security verification (18 categories)
   - Application configuration security
   - Database and data protection
   - Monitoring and logging security
   - Service and process hardening
   - Vulnerability and compliance assessment
   - Incident response readiness
   - Ongoing maintenance tasks
   - Sign-off sections for audit compliance
   
   **Use when**: Validating security posture before production

4. **[PRODUCTION_README.md](PRODUCTION_README.md)** (300+ lines)
   - Quick-start overview
   - System requirements summary
   - Quick start options (automated vs manual)
   - Pre-deployment checklist
   - Configuration overview
   - Architecture diagram
   - Service details table
   - Security features summary
   - Deployment readiness checklist
   - Support resources index
   
   **Use when**: Getting overview or quick reference

5. **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** (400+ lines)
   - Executive summary of deployment package
   - What was created (7 categories)
   - Quick start options
   - Configuration overview
   - Architecture diagram
   - Service details table
   - Security features summary
   - Next steps guide
   - Production readiness checklist
   
   **Use when**: Understanding what's included and planning deployment

---

## 🔧 Automation Scripts (3)

### Deployment Automation
1. **[setup-production.sh](setup-production.sh)** (executable, 350+ lines)
   - **Purpose**: One-command production deployment
   - **Time**: ~5 minutes
   - **What it does**:
     - Checks system requirements
     - Creates system user (ddospot)
     - Sets up directory structure
     - Configures environment variables
     - Builds and deploys Docker containers
     - Configures Nginx reverse proxy
     - Installs Systemd services
     - Sets up automated backup cron job
     - Configures firewall (UFW)
     - Verifies deployment
   - **Usage**: `sudo bash setup-production.sh`
   - **Target**: Users who want automated one-command deployment

### Backup & Recovery
2. **[backup.sh](backup.sh)** (executable, 150+ lines)
   - **Purpose**: Automated daily backup script
   - **Schedule**: 0 2 * * * (daily at 2 AM)
   - **What it backs up**:
     - SQLite database (honeypot_events)
     - Prometheus data (metrics)
     - Alertmanager configuration
     - Grafana dashboards
     - Application configuration
     - Alert configuration
   - **Features**:
     - Configurable retention (default: 30 days)
     - Automatic old backup cleanup
     - Optional S3 upload support
     - Optional NAS backup support
     - Comprehensive logging
   - **Usage**: `./backup.sh` (or automatic via cron)
   - **Target**: Regular system maintenance

3. **[restore.sh](restore.sh)** (executable, 200+ lines)
   - **Purpose**: Data recovery from backups
   - **What it does**:
     - Lists available backups
     - Confirms restore action
     - Creates safety backup before restore
     - Stops services before restore
     - Extracts backup archive
     - Fixes file permissions
     - Restarts services
     - Verifies restoration
   - **Features**:
     - Safety backup creation
     - Permission auto-correction
     - Pre-restore confirmation prompt
     - Post-restore verification
   - **Usage**: `./restore.sh /path/to/backup.tar.gz`
   - **Target**: Disaster recovery situations

---

## 🐳 Docker Configuration (2)

### Docker Compose Stack
1. **[docker-compose.prod.yml](docker-compose.prod.yml)** (750+ lines)
   - **Purpose**: Production container orchestration
   - **Services** (6):
     - **ddospot-dashboard**: Main API and web UI (Flask)
     - **prometheus**: Metrics collection and storage
     - **grafana**: Visualization and dashboards
     - **alertmanager**: Alert routing and notifications
     - **node-exporter**: System metrics collection
     - **honeypot**: DDoS attack detection service
   - **Features**:
     - Health checks for all services
     - Volume management for persistence
     - Network isolation
     - Environment variable configuration
     - Resource limits
     - Restart policies
   - **Usage**: `docker-compose -f docker-compose.prod.yml up -d`

### Docker Compose Override
2. **[docker-compose.override.yml](docker-compose.override.yml)** (created by setup-production.sh)
   - **Purpose**: Production-specific volume and environment overrides
   - **Customizations**:
     - Maps /var/lib/ddospot for persistent data
     - Sets PYTHONUNBUFFERED for real-time logs
     - Configures all volume paths for production

---

## ⚙️ Configuration Files (6)

### Reverse Proxy Configuration
1. **[nginx/ddospot.conf](nginx/ddospot.conf)** (250+ lines)
   - **Purpose**: Nginx reverse proxy for HTTPS termination
   - **Features**:
     - HTTP to HTTPS redirect
     - SSL/TLS configuration
     - Security headers (HSTS, X-Frame-Options, etc.)
     - Rate limiting zones and rules
     - Upstream routing to application services
     - Basic auth for admin endpoints
     - Static file caching
     - WebSocket support
     - Request timeout configuration
   - **Setup**: `sudo cp nginx/ddospot.conf /etc/nginx/sites-available/ddospot`
   - **Locations**:
     - `/` → Dashboard UI
     - `/api` → Dashboard API
     - `/metrics` → Prometheus metrics (auth required)
     - `/prometheus` → Prometheus UI (auth required)
     - `/grafana` → Grafana UI
     - `/alertmanager` → Alertmanager UI (auth required)

### Systemd Service Units
2. **[systemd/ddospot-honeypot.service](systemd/ddospot-honeypot.service)** (40+ lines)
   - **Purpose**: Systemd unit for honeypot process management
   - **Features**:
     - Security hardening (ProtectSystem, PrivateTmp)
     - Resource limits (512MB memory, 50% CPU)
     - Restart policy on failure
     - Journal logging
     - User: ddospot (non-root)
   - **Setup**: `sudo cp systemd/ddospot-honeypot.service /etc/systemd/system/`
   - **Commands**:
     - `sudo systemctl start ddospot-honeypot.service`
     - `sudo systemctl status ddospot-honeypot.service`

3. **[systemd/ddospot-dashboard.service](systemd/ddospot-dashboard.service)** (45+ lines)
   - **Purpose**: Systemd unit for dashboard process management
   - **Features**:
     - Security hardening (ProtectSystem, PrivateTmp)
     - Resource limits (768MB memory, 50% CPU)
     - Restart policy on failure
     - Journal logging
     - Health check configuration
   - **Setup**: `sudo cp systemd/ddospot-dashboard.service /etc/systemd/system/`

### Monitoring Configuration
4. **[monitoring/alertmanager.yml](monitoring/alertmanager.yml)** (120+ lines)
   - **Purpose**: Alert routing and notification configuration
   - **Features**:
     - Severity-based routing (critical/high/info)
     - Multiple receiver channels:
       - Email (SMTP)
       - Slack (webhooks)
       - PagerDuty (events)
     - Alert grouping and deduplication
     - Inhibition rules
     - Routing tree structure
   - **Setup**: Used by Alertmanager service automatically

5. **[monitoring/grafana-datasources.yml](monitoring/grafana-datasources.yml)** (20+ lines)
   - **Purpose**: Grafana data source provisioning
   - **Datasources**:
     - Prometheus (metrics collection)
     - Alertmanager (alert status)
   - **Setup**: Automatically provisioned by docker-compose

### Environment Configuration
6. **[.env.prod.template](.env.prod.template)** (190+ lines)
   - **Purpose**: Production environment variable template
   - **Sections**:
     - **App Configuration**: Host, port, workers
     - **Database**: Path, retention policy
     - **Monitoring**: Metrics, alert thresholds
     - **Rate Limiting**: Requests, window, blacklist
     - **Security**: API token, TLS
     - **Alerts**: SMTP, Slack, PagerDuty
     - **Backup**: Retention, remote storage
   - **Setup**: `cp .env.prod.template .env.prod && nano .env.prod`
   - **Critical Variables**:
     - `DDOSPOT_API_TOKEN` (generate: `openssl rand -hex 32`)
     - `DDOSPOT_REQUIRE_TOKEN=true`
     - `DDOSPOT_SMTP_*` (email configuration)
     - `DDOSPOT_SLACK_WEBHOOK` (optional)
     - `DDOSPOT_PAGERDUTY_KEY` (optional)

---

## 📋 Related Project Files

### Previously Configured (from phases 1-6)
- **core/database.py** - Event storage with filtering/pagination
- **dashboard.py** - Flask API with rate limiting and token auth
- **cli.py** - Command-line interface with authentication
- **docker-compose.prod.yml** - Production Docker stack (6 services)
- **alert_config.json** - Alert configuration
- **tests/** - Comprehensive test suite (66 tests)

---

## 🎯 Usage Flowchart

```
START: Production Deployment
  │
  ├─→ Read: PRODUCTION_README.md
  │   └─→ Overview and requirements check
  │
  ├─→ Review: DEPLOYMENT_SUMMARY.md
  │   └─→ Understand what's included
  │
  ├─→ Quick Start?
  │   │
  │   ├─ YES → Run: sudo bash setup-production.sh
  │   │         └─→ Verify with PRODUCTION_README.md
  │   │
  │   └─ NO → Read: DEPLOYMENT_GUIDE.md
  │           └─→ Follow manual steps (7 sections)
  │
  ├─→ Configure: .env.prod
  │   └─→ Set API token, SMTP, Slack, etc.
  │
  ├─→ Deploy: docker-compose + systemd
  │   └─→ Verify services running
  │
  ├─→ Secure: SECURITY_CHECKLIST.md
  │   └─→ Go through all 18 categories
  │
  ├─→ Test:
  │   ├─→ Access dashboard: https://ddospot.example.com
  │   ├─→ Access Grafana: https://ddospot.example.com/grafana
  │   └─→ Test alerts: Send test alert
  │
  ├─→ Monitor: OPERATIONS_PLAYBOOK.md
  │   └─→ Set up on-call and monitoring
  │
  └─→ Maintain:
      ├─→ Daily: Monitor dashboard
      ├─→ Weekly: Review logs and backups
      ├─→ Monthly: Test recovery procedures
      └─→ Quarterly: Security audit

```

---

## 📊 File Organization

```
/opt/ddospot/
├── Documentation/
│   ├── DEPLOYMENT_GUIDE.md (800+ lines)
│   ├── OPERATIONS_PLAYBOOK.md (600+ lines)
│   ├── SECURITY_CHECKLIST.md (500+ lines)
│   ├── PRODUCTION_README.md (300+ lines)
│   ├── DEPLOYMENT_SUMMARY.md (400+ lines)
│   └── DEPLOYMENT_FILES_INDEX.md (this file)
│
├── Scripts/
│   ├── setup-production.sh (automated deployment)
│   ├── backup.sh (daily backup)
│   └── restore.sh (recovery)
│
├── Configuration/
│   ├── .env.prod.template (environment variables)
│   ├── docker-compose.prod.yml (container stack)
│   ├── nginx/
│   │   └── ddospot.conf (reverse proxy)
│   ├── systemd/
│   │   ├── ddospot-honeypot.service
│   │   └── ddospot-dashboard.service
│   └── monitoring/
│       ├── alertmanager.yml
│       └── grafana-datasources.yml
│
├── Application/
│   ├── core/ (business logic)
│   ├── ml/ (ML models)
│   ├── telemetry/ (metrics)
│   ├── replay/ (traffic replay)
│   ├── dashboard.py (Flask API)
│   ├── cli.py (CLI)
│   └── main.py (entry point)
│
├── Data/
│   └── /var/lib/ddospot/
│       ├── honeypot.db (SQLite)
│       ├── prometheus/ (metrics)
│       ├── grafana/ (dashboards)
│       └── alertmanager/ (alerts)
│
└── Backups/
    ├── backups/ (daily archives)
    └── logs/ (application logs)
```

---

## ✅ Deployment Checklist

Before using these files:

**Preparation**
- [ ] Review PRODUCTION_README.md for overview
- [ ] Check system requirements (8GB RAM, 50GB storage)
- [ ] Prepare domain name and email
- [ ] Generate API token: `openssl rand -hex 32`

**Deployment**
- [ ] Copy files to /opt/ddospot
- [ ] Run: `sudo bash setup-production.sh`
  OR follow DEPLOYMENT_GUIDE.md manually
- [ ] Configure .env.prod with your settings
- [ ] Setup SSL/TLS certificate

**Security**
- [ ] Go through SECURITY_CHECKLIST.md (all 18 categories)
- [ ] Change all default credentials
- [ ] Test firewall and rate limiting
- [ ] Verify authentication on sensitive endpoints

**Validation**
- [ ] Access dashboard at https://your-domain
- [ ] Verify metrics in Prometheus
- [ ] Check Grafana dashboards
- [ ] Test alert channels (email, Slack, etc.)
- [ ] Run backup script manually
- [ ] Test restore procedure

**Maintenance**
- [ ] Schedule daily backups (0 2 * * *)
- [ ] Set up monitoring and on-call
- [ ] Document any customizations
- [ ] Plan quarterly security audits

---

## 📞 Support & Resources

### Documentation
| Document | Purpose | Time |
|----------|---------|------|
| PRODUCTION_README.md | Quick overview | 5 min |
| DEPLOYMENT_GUIDE.md | Step-by-step deployment | 30 min |
| OPERATIONS_PLAYBOOK.md | Operational procedures | 20 min |
| SECURITY_CHECKLIST.md | Security validation | 30 min |

### Automation
| Script | Purpose | Time |
|--------|---------|------|
| setup-production.sh | Full deployment | 5 min |
| backup.sh | Daily backups | automatic |
| restore.sh | Recovery | on-demand |

### Configuration
| File | Purpose | Lines |
|------|---------|-------|
| docker-compose.prod.yml | Container stack | 750+ |
| nginx/ddospot.conf | Reverse proxy | 250+ |
| .env.prod.template | Environment | 190+ |
| monitoring/alertmanager.yml | Alert routing | 120+ |
| systemd/*.service | Process management | 40-50 |

---

## 🎓 Learning Path

1. **Start Here** → PRODUCTION_README.md (5 min)
2. **Understand Architecture** → Check architecture diagram (5 min)
3. **Quick Deploy** → Run setup-production.sh (5 min)
   OR **Manual Deploy** → Read DEPLOYMENT_GUIDE.md (30 min)
4. **Secure Your System** → Follow SECURITY_CHECKLIST.md (30 min)
5. **Learn Operations** → Review OPERATIONS_PLAYBOOK.md (20 min)
6. **Test Everything** → Verify deployment (15 min)

**Total Time**: 80-120 minutes for complete production deployment

---

## 🔄 File Dependencies

```
setup-production.sh
├─ Reads: .env.prod.template
├─ Reads: docker-compose.prod.yml
├─ Reads: nginx/ddospot.conf
├─ Reads: systemd/*.service
├─ Copies: monitoring/*.yml
└─ Executes: backup.sh setup

restore.sh
├─ Reads: /opt/ddospot/backups/*.tar.gz
└─ Verifies: honeypot.db, service status

DEPLOYMENT_GUIDE.md
├─ References: .env.prod.template
├─ References: docker-compose.prod.yml
├─ References: nginx/ddospot.conf
└─ References: systemd/*.service

OPERATIONS_PLAYBOOK.md
├─ References: docker-compose.yml
└─ References: systemd service commands

SECURITY_CHECKLIST.md
├─ References: .env.prod
├─ References: nginx/ddospot.conf
└─ References: firewall configuration
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Status**: Complete & Production Ready ✅
