# DDoSPot Docker Documentation

## Overview

DDoSPot can be deployed using Docker containers for isolated, scalable, and reproducible environments. This document covers development and production deployments.

## Quick Start - Development

```bash
# Make scripts executable
chmod +x scripts/start-dev-docker.sh

# Start development environment
./scripts/start-dev-docker.sh

# View logs
docker-compose -f docker-compose-dev.yml logs -f

# Stop services
docker-compose -f docker-compose-dev.yml down
```

**Development Environment includes:**
- DDoSPot Honeypot (with live code reload)
- DDoSPot Dashboard (Flask development mode)
- Shared database and logs
- Full source code mounted for development

## Quick Start - Production

```bash
# Make scripts executable
chmod +x scripts/deploy-production.sh

# Deploy production environment
./scripts/deploy-production.sh

# View logs
docker-compose -f docker-compose-prod.yml logs -f

# Stop services
docker-compose -f docker-compose-prod.yml down
```

**Production Environment includes:**
- DDoSPot Honeypot (optimized runtime)
- DDoSPot Dashboard (production Flask)
- Prometheus (metrics collection)
- Grafana (visualization & dashboards)
- AlertManager (alert routing & notifications)
- Persistent volumes for data retention
- Resource limits and health checks
- Comprehensive logging

## Architecture

### Development (`docker-compose-dev.yml`)

```
┌─────────────────────────────────────┐
│      Host Machine (Linux/Mac)       │
├─────────────────────────────────────┤
│  ┌──────────────────────────────┐   │
│  │  Docker Network (bridge)     │   │
│  ├──────────────────────────────┤   │
│  │ ┌────────────┐  ┌─────────┐ │   │
│  │ │ Honeypot   │  │Dashboard│ │   │
│  │ │ (Port 2222)│  │(Port 5K)│ │   │
│  │ └────────────┘  └─────────┘ │   │
│  │ Shared Volume: honeypot.db   │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Production (`docker-compose-prod.yml`)

```
┌────────────────────────────────────────────┐
│         Production Environment             │
├────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐  │
│  │  Docker Network (ddospot-network)   │  │
│  ├──────────────────────────────────────┤  │
│  │ Core Services:                       │  │
│  │ ┌──────────────┐  ┌──────────────┐  │  │
│  │ │ Honeypot     │  │ Dashboard    │  │  │
│  │ │ (2222, 8080) │  │ (5000)       │  │  │
│  │ └──────────────┘  └──────────────┘  │  │
│  │ Shared Volume: honeypot.db           │  │
│  │                                      │  │
│  │ Monitoring Stack:                    │  │
│  │ ┌────────────┐ ┌──────────────────┐ │  │
│  │ │Prometheus  │ │Grafana (3000)    │ │  │
│  │ │(9090)      │ │ + Dashboards     │ │  │
│  │ └────────────┘ └──────────────────┘ │  │
│  │                                      │  │
│  │ ┌────────────────────────────────┐  │  │
│  │ │ AlertManager (9093)            │  │  │
│  │ │ - Alert Routing                │  │  │
│  │ │ - Notifications                │  │  │
│  │ └────────────────────────────────┘  │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

## Service Details

### Honeypot Service

**Purpose:** Captures and logs attack traffic

**Ports:**
- 22 (SSH) → Container 2222
- 80 (HTTP) → Container 8080
- 1900 (SSDP/UDP)

**Configuration:**
```yaml
honeypot:
  ports:
    - "22:2222"        # SSH honeypot
    - "80:8080"        # HTTP honeypot
    - "1900:1900/udp"  # SSDP honeypot
```

**Logs:** `/app/logs/`
**Database:** `/app/honeypot.db`

### Dashboard Service

**Purpose:** Real-time attack visualization and analysis

**Port:** 5000

**Features:**
- Live attack monitoring
- Threat intelligence
- Geographic heat maps
- Automated responses
- Custom alert rules
- ML anomaly detection

**URL:** `http://localhost:5000`

### Prometheus Service

**Purpose:** Metrics collection and time-series data storage

**Port:** 9090
**URL:** `http://localhost:9090`

**Configuration:**
- Scrapes metrics from honeypot/dashboard
- Retention: 30 days
- Data storage: Named volume `prometheus-data`

**Metrics collected:**
- Attack frequency
- Protocol distribution
- Source IP statistics
- Response times
- System resources

### Grafana Service

**Purpose:** Visualization and alerting dashboards

**Port:** 3000
**URL:** `http://localhost:3000`
**Default Credentials:** admin / admin

**Pre-configured dashboards:**
- Attack Overview
- Geographic Distribution
- Threat Intelligence
- System Performance
- Custom metrics

### AlertManager Service

**Purpose:** Alert routing and notification management

**Port:** 9093
**URL:** `http://localhost:9093`

**Features:**
- Alert deduplication
- Routing rules
- Notification channels (email, webhooks, Slack, etc.)
- Alert grouping and silencing

## Volume Management

### Persistent Volumes (Production)

```yaml
volumes:
  prometheus-data:    # Metrics history
  grafana-data:       # Dashboards and settings
  alertmanager-data:  # Alert state
```

### Bind Mounts

```yaml
volumes:
  - ./honeypot.db:/app/honeypot.db        # Attack database
  - ./logs:/app/logs                       # Application logs
  - ./config:/app/config                  # Configuration files
```

## Network Configuration

Both development and production use custom Docker networks:

- **Development:** `ddospot-dev-network` (bridge)
- **Production:** `ddospot-network` (bridge)

Services can communicate by hostname:
- `honeypot` (or `honeypot-dev`)
- `dashboard` (or `dashboard-dev`)
- `prometheus`
- `grafana`
- `alertmanager`

## Resource Limits

### Production Resource Allocation

```
Honeypot:
  Limit:   2 CPU, 1 GB RAM
  Reserve: 0.5 CPU, 256 MB RAM

Dashboard:
  Limit:   1 CPU, 512 MB RAM
  Reserve: 0.5 CPU, 256 MB RAM

Prometheus:
  Limit:   1 CPU, 512 MB RAM
  Reserve: 0.25 CPU, 128 MB RAM

Grafana:
  Limit:   1 CPU, 512 MB RAM
  Reserve: 0.25 CPU, 128 MB RAM

AlertManager:
  Limit:   0.5 CPU, 256 MB RAM
  Reserve: 0.25 CPU, 128 MB RAM
```

**Total Production Footprint:**
- CPU: ~4.5 cores
- Memory: ~2.5 GB

## Logging

### Docker Logging Configuration

All services use JSON file logging with rotation:
- Max size: 100 MB per file
- Max files: 10 files
- Auto-rotation enabled

**View logs:**
```bash
# All services
docker-compose -f docker-compose-prod.yml logs -f

# Specific service
docker-compose -f docker-compose-prod.yml logs -f honeypot

# Last 50 lines
docker-compose -f docker-compose-prod.yml logs --tail 50
```

## Deployment Scenarios

### Scenario 1: Local Development

```bash
./scripts/start-dev-docker.sh
# Access: http://localhost:5000
```

### Scenario 2: Single-Server Production

```bash
./scripts/deploy-production.sh
# Services exposed on host machine
# Suitable for small deployments
```

### Scenario 3: Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose-prod.yml ddospot

# Scale services
docker service scale ddospot_honeypot=3

# View services
docker service ls
```

### Scenario 4: Kubernetes Deployment

Convert docker-compose to Kubernetes manifests using:
```bash
kompose convert -f docker-compose-prod.yml -o k8s/
```

## Security Considerations

1. **Network Isolation:** Services communicate via bridge network
2. **Port Mapping:** Only necessary ports exposed
3. **Health Checks:** Automatic service restart on failure
4. **Resource Limits:** Prevents resource exhaustion attacks
5. **Read-only filesystem:** Can be enforced for honeypot
6. **Secrets Management:** Use Docker secrets for sensitive data
7. **Log Rotation:** Prevents disk space exhaustion

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose -f docker-compose-prod.yml logs

# Rebuild images
docker-compose -f docker-compose-prod.yml build --no-cache

# Restart services
docker-compose -f docker-compose-prod.yml restart
```

### High memory usage

```bash
# Check resource usage
docker stats

# Reduce container limits in docker-compose file
# Restart services
docker-compose -f docker-compose-prod.yml restart
```

### Database locked errors

```bash
# Database may be in use by another process
# Restart dashboard service first
docker-compose -f docker-compose-prod.yml restart dashboard

# Then restart honeypot
docker-compose -f docker-compose-prod.yml restart honeypot
```

### Port conflicts

```bash
# Change port mappings in docker-compose file
# Example: Change dashboard from 5000:5000 to 5001:5000

# Restart with new ports
docker-compose -f docker-compose-prod.yml down
docker-compose -f docker-compose-prod.yml up -d
```

## Performance Tuning

### For high-traffic environments

1. Increase resource limits
2. Scale honeypot service in Swarm/K8s
3. Increase Prometheus retention
4. Enable Grafana caching
5. Adjust alerting thresholds

### Example scaled deployment

```bash
docker service scale ddospot_honeypot=5 ddospot_dashboard=2
```

## Maintenance

### Regular backups

```bash
# Backup database
cp honeypot.db backups/honeypot_$(date +%Y%m%d_%H%M%S).db

# Backup volumes
docker run --rm -v ddospot_prometheus-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
```

### Clean up

```bash
# Remove stopped containers
docker container prune

# Remove dangling images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (careful!)
docker system prune -a --volumes
```

## Next Steps

1. Configure AlertManager for notifications
2. Customize Grafana dashboards
3. Set up log aggregation (ELK, Loki)
4. Implement CI/CD pipeline
5. Configure registry for image distribution
