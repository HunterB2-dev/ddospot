# Production Deployment Guide

**File 18: Advanced Deployment for Production Environments**

*Level: Advanced | Time: 2-3 hours | Prerequisites: Files 4, 8, 10, 14*

---

## Table of Contents
1. [Introduction](#introduction)
2. [Pre-Deployment Planning](#planning)
3. [Docker Production Setup](#docker-setup)
4. [Kubernetes Deployment](#kubernetes)
5. [High Availability Setup](#ha-setup)
6. [Load Balancing](#load-balancing)
7. [Persistent Storage](#storage)
8. [Backup & Recovery](#backup)
9. [Monitoring Integration](#monitoring)
10. [Security Hardening](#security)
11. [Capacity Planning](#capacity)
12. [Troubleshooting](#troubleshooting)

---

## Introduction {#introduction}

This guide covers deploying DDoSPoT in production environments with:

- **High Availability**: Multiple instances with failover
- **Scalability**: Handle thousands of attacks simultaneously
- **Reliability**: 99.9% uptime SLA
- **Security**: Production-grade isolation and hardening
- **Compliance**: Audit logging and data retention
- **Performance**: Optimized for real-world traffic

---

## Pre-Deployment Planning {#planning}

### 1. Capacity Requirements Assessment

**Determine your needs:**

```
Network Setup:
- Bandwidth: What's your network capacity? (e.g., 100 Mbps, 1 Gbps, 10 Gbps)
- Attack Types: What threats are you defending against?
  * DDoS (requires high throughput)
  * Application attacks (requires high connection rate)
  * Reconnaissance (requires moderate throughput)

Attack Volume Estimation:
- Expected attacks/day: 100? 1,000? 10,000?
- Peak duration: Minutes? Hours? Days?
- Concurrent connections: 100? 10,000? 100,000?

Server Resources:
- CPU: 4 cores for 1,000 attacks/day → 16 cores for 10,000/day
- RAM: 8 GB for basic → 32+ GB for production
- Disk: 50 GB baseline + logs (~100 MB/day per 1,000 attacks)
- Network: Gigabit Ethernet minimum
```

**Calculation Examples:**

**Small Organization** (Protecting single office)
```
Attacks/day: 100-500
Concurrent: 10-100
Resources: 
  - CPU: 4 cores
  - RAM: 8 GB
  - Storage: 100 GB
Deployment: Single Docker container or VM
Cost: Low
```

**Medium Organization** (Multiple offices, SMB)
```
Attacks/day: 500-5,000
Concurrent: 100-1,000
Resources:
  - CPU: 8-12 cores
  - RAM: 16 GB
  - Storage: 500 GB
Deployment: Docker Swarm or small Kubernetes cluster (3 nodes)
Cost: Medium
```

**Large Organization** (Enterprise, ISP)
```
Attacks/day: 5,000-50,000+
Concurrent: 1,000-10,000+
Resources:
  - CPU: 16+ cores (multiple machines)
  - RAM: 32-64 GB
  - Storage: 1-5 TB (with archival)
Deployment: Kubernetes cluster (5+ nodes) with load balancing
Cost: High
```

### 2. Network Architecture Design

**Network Diagram (Production):**

```
                    Internet
                       ↓
              ┌─────────────────┐
              │  Load Balancer  │
              │  (nginx/HAProxy)│
              └────────┬────────┘
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │DDoSPoT-1│  │DDoSPoT-2│  │DDoSPoT-3│
    │Container│  │Container│  │Container│
    └────┬────┘  └────┬────┘  └────┬────┘
         │            │            │
         └────────────┼────────────┘
                      ↓
              ┌─────────────────┐
              │  Shared Database│
              │   (PostgreSQL)  │
              └─────────────────┘
                      ↑
                      ├─── Persistent Volume
                      └─── Backup Storage
```

---

## Docker Production Setup {#docker-setup}

### Production Docker Compose

**File**: `docker-compose-prod.yml`

```yaml
version: '3.9'

services:
  ddospot-web:
    image: ddospot:latest-prod
    container_name: ddospot-web
    restart: always
    ports:
      - "2222:2222"  # SSH honeypot
      - "8888:8888"  # HTTP honeypot
      - "1900:1900/udp"  # SSDP honeypot
    environment:
      - FLASK_ENV=production
      - DB_HOST=postgres
      - DB_USER=ddospot
      - DB_PASSWORD=${DB_PASSWORD}  # From env file or secrets
      - REDIS_HOST=redis
      - LOG_LEVEL=INFO
      - MAX_WORKERS=8
    volumes:
      - /data/logs:/app/logs  # Persistent logs
      - /data/backups:/app/backups  # Persistent backups
      - /etc/ddospot/config.json:/app/config.json:ro  # Read-only config
    depends_on:
      - postgres
      - redis
    networks:
      - ddospot-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  postgres:
    image: postgres:15-alpine
    container_name: ddospot-db
    restart: always
    environment:
      - POSTGRES_DB=ddospot
      - POSTGRES_USER=ddospot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Named volume
      - /data/backups/postgres:/backups  # Backup location
    networks:
      - ddospot-network
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "effective_cache_size=1GB"
      - "-c"
      - "maintenance_work_mem=64MB"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ddospot"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true

  redis:
    image: redis:7-alpine
    container_name: ddospot-cache
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - ddospot-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  ddospot-network:
    driver: bridge
```

**Environment File**: `.env.prod`

```bash
# Database
DB_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_secure_redis_password

# System
COMPOSE_PROJECT_NAME=ddospot-prod
ENVIRONMENT=production

# Logging
LOG_LEVEL=WARNING
```

**Startup Command:**

```bash
# Pull latest images
docker-compose -f docker-compose-prod.yml pull

# Start services
docker-compose -f docker-compose-prod.yml up -d

# Verify all services running
docker-compose -f docker-compose-prod.yml ps

# Check logs
docker-compose -f docker-compose-prod.yml logs -f ddospot-web
```

---

## Kubernetes Deployment {#kubernetes}

### Kubernetes Architecture

For enterprise/large-scale deployments:

```
┌─────────────────────────────────────┐
│     Kubernetes Cluster (3+ nodes)   │
├─────────────────────────────────────┤
│  Master Node                        │
│  - API Server                       │
│  - Scheduler                        │
│  - Controller Manager               │
├─────────────────────────────────────┤
│  Worker Nodes (3+)                  │
│  - DDoSPoT Pods (replicated)       │
│  - Monitoring pods                  │
│  - Logging pods                     │
├─────────────────────────────────────┤
│  Persistent Storage                 │
│  - PostgreSQL StatefulSet           │
│  - Redis StatefulSet                │
│  - PersistentVolumes               │
└─────────────────────────────────────┘
```

### Kubernetes Manifests

**Namespace:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ddospot-prod
```

**DDoSPoT Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ddospot
  namespace: ddospot-prod
spec:
  replicas: 3  # High availability
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: ddospot
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero downtime
  template:
    metadata:
      labels:
        app: ddospot
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8888"
    spec:
      serviceAccountName: ddospot
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: ddospot
        image: ddospot:latest-prod
        imagePullPolicy: Always
        ports:
        - containerPort: 2222
          name: ssh
          protocol: TCP
        - containerPort: 8888
          name: http
          protocol: TCP
        - containerPort: 1900
          name: ssdp
          protocol: UDP
        env:
        - name: FLASK_ENV
          value: production
        - name: DB_HOST
          value: postgres.ddospot-prod.svc.cluster.local
        - name: DB_USER
          value: ddospot
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ddospot-secrets
              key: db-password
        - name: REDIS_HOST
          value: redis.ddospot-prod.svc.cluster.local
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ddospot-secrets
              key: redis-password
        resources:
          requests:
            cpu: 2
            memory: 2Gi
          limits:
            cpu: 4
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8888
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/ready
            port: 8888
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: config
          mountPath: /app/config.json
          subPath: config.json
          readOnly: true
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: ddospot-logs-pvc
      - name: config
        configMap:
          name: ddospot-config
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - ddospot
              topologyKey: kubernetes.io/hostname
```

**Service:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ddospot
  namespace: ddospot-prod
spec:
  selector:
    app: ddospot
  type: LoadBalancer  # Or NodePort for internal
  ports:
  - name: ssh
    port: 2222
    targetPort: 2222
    protocol: TCP
  - name: http
    port: 8888
    targetPort: 8888
    protocol: TCP
  - name: ssdp
    port: 1900
    targetPort: 1900
    protocol: UDP
  sessionAffinity: ClientIP  # Sticky sessions
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

**PostgreSQL StatefulSet:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: ddospot-prod
spec:
  serviceName: postgres
  replicas: 1  # For high availability, use 3+ with replication
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: ddospot
        - name: POSTGRES_USER
          value: ddospot
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ddospot-secrets
              key: db-password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 1
            memory: 2Gi
          limits:
            cpu: 2
            memory: 4Gi
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
```

**Apply to Cluster:**

```bash
# Create secrets
kubectl create secret generic ddospot-secrets \
  --from-literal=db-password=$(openssl rand -base64 32) \
  --from-literal=redis-password=$(openssl rand -base64 32) \
  -n ddospot-prod

# Apply all manifests
kubectl apply -f ddospot-namespace.yaml
kubectl apply -f ddospot-configmap.yaml
kubectl apply -f ddospot-secrets.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-statefulset.yaml
kubectl apply -f ddospot-deployment.yaml
kubectl apply -f ddospot-service.yaml

# Verify deployment
kubectl get pods -n ddospot-prod
kubectl rollout status deployment/ddospot -n ddospot-prod
```

---

## High Availability Setup {#ha-setup}

### Multi-Node Active-Active Configuration

**Architecture:**

```
                    DNS (Round-robin)
                           ↓
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
    DDoSPoT-1         DDoSPoT-2         DDoSPoT-3
    (Node-1)          (Node-2)          (Node-3)
         │                 │                 │
         └─────────────────┼─────────────────┘
                           ↓
              Shared PostgreSQL Cluster
              (Master-Slave Replication)
```

**Configuration for High Availability:**

```json
{
  "high_availability": {
    "enabled": true,
    "mode": "active_active",
    "sync_interval_seconds": 5,
    "nodes": [
      {
        "name": "ddospot-1",
        "address": "192.0.2.10",
        "port": 8888,
        "health_check_url": "http://192.0.2.10:8888/api/health"
      },
      {
        "name": "ddospot-2",
        "address": "192.0.2.11",
        "port": 8888,
        "health_check_url": "http://192.0.2.11:8888/api/health"
      },
      {
        "name": "ddospot-3",
        "address": "192.0.2.12",
        "port": 8888,
        "health_check_url": "http://192.0.2.12:8888/api/health"
      }
    ],
    "failover": {
      "auto_failover_enabled": true,
      "health_check_interval_seconds": 10,
      "failure_threshold": 3,
      "heartbeat_timeout_seconds": 30
    },
    "shared_storage": {
      "type": "postgresql",
      "host": "postgres-cluster.example.com",
      "port": 5432,
      "database": "ddospot",
      "replication_enabled": true,
      "backup_location": "s3://backups-bucket/ddospot/"
    }
  }
}
```

---

## Load Balancing {#load-balancing}

### Nginx Load Balancer Configuration

**File**: `/etc/nginx/conf.d/ddospot-lb.conf`

```nginx
# Upstream backend servers
upstream ddospot_backend {
    least_conn;  # Load balancing method
    server 192.0.2.10:8888 max_fails=2 fail_timeout=10s;
    server 192.0.2.11:8888 max_fails=2 fail_timeout=10s;
    server 192.0.2.12:8888 max_fails=2 fail_timeout=10s;
}

# SSL upstream (for secure connections to backends)
upstream ddospot_backend_ssl {
    least_conn;
    server 192.0.2.10:8889 ssl verify=off max_fails=2 fail_timeout=10s;
    server 192.0.2.11:8889 ssl verify=off max_fails=2 fail_timeout=10s;
    server 192.0.2.12:8889 ssl verify=off max_fails=2 fail_timeout=10s;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=1000r/s;

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name ddospot.example.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name ddospot.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/certs/ddospot.crt;
    ssl_certificate_key /etc/nginx/certs/ddospot.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/ddospot-access.log combined;
    error_log /var/log/nginx/ddospot-error.log warn;

    # API endpoint
    location /api/ {
        limit_req zone=api burst=100 nodelay;
        
        proxy_pass http://ddospot_backend;
        proxy_http_version 1.1;
        
        # Connection settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Dashboard
    location / {
        limit_req zone=general burst=50 nodelay;
        
        proxy_pass http://ddospot_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint (no logging)
    location /health {
        access_log off;
        proxy_pass http://ddospot_backend/api/health;
    }
}

# SSH Load Balancing (using HAProxy is better, but can use nginx stream)
# For SSH: Configure HAProxy instead (see below)
```

### HAProxy Configuration (Better for SSH/TCP)

**File**: `/etc/haproxy/haproxy.cfg`

```haproxy
global
    log /dev/log    local0
    log /dev/log    local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# HTTP/HTTPS Load Balancing
frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/ddospot.pem
    redirect scheme https if !{ ssl_fc }
    
    default_backend http_back

backend http_back
    balance leastconn
    http-reuse safe
    server ddospot1 192.0.2.10:8888 check inter 5s fall 2 rise 2
    server ddospot2 192.0.2.11:8888 check inter 5s fall 2 rise 2
    server ddospot3 192.0.2.12:8888 check inter 5s fall 2 rise 2

# SSH Load Balancing
frontend ssh_front
    bind *:2222
    mode tcp
    default_backend ssh_back

backend ssh_back
    mode tcp
    balance leastconn
    server ssh1 192.0.2.10:2222 check inter 5s fall 2 rise 2
    server ssh2 192.0.2.11:2222 check inter 5s fall 2 rise 2
    server ssh3 192.0.2.12:2222 check inter 5s fall 2 rise 2

# SSDP Load Balancing
frontend ssdp_front
    bind *:1900 udp
    mode udp
    default_backend ssdp_back

backend ssdp_back
    mode udp
    balance leastconn
    server ssdp1 192.0.2.10:1900 check inter 5s fall 2 rise 2
    server ssdp2 192.0.2.11:1900 check inter 5s fall 2 rise 2
    server ssdp3 192.0.2.12:1900 check inter 5s fall 2 rise 2

# Stats
listen stats
    bind 0.0.0.0:8080
    mode http
    stats enable
    stats uri /
    stats refresh 5s
    stats show-legends
```

---

## Persistent Storage {#storage}

### Database Replication Setup

**PostgreSQL Master-Slave Replication:**

**On Master Node:**

```bash
# Edit postgresql.conf
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB

# Restart PostgreSQL
systemctl restart postgresql

# Create replication user
sudo -u postgres psql -c "CREATE USER replicator WITH REPLICATION PASSWORD 'replicator_password';"

# Configure pg_hba.conf
echo "host    replication     replicator    CIDR    md5" >> /etc/postgresql/15/main/pg_hba.conf

# Reload config
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

**On Slave Node:**

```bash
# Stop PostgreSQL
systemctl stop postgresql

# Get base backup from master
sudo -u postgres pg_basebackup -h master_ip -D /var/lib/postgresql/15/main -U replicator -v -P

# Create standby signal
sudo -u postgres touch /var/lib/postgresql/15/main/standby.signal

# Configure recovery
cat > /var/lib/postgresql/15/main/recovery.conf <<EOF
standby_mode = 'on'
primary_conninfo = 'host=master_ip port=5432 user=replicator password=replicator_password'
EOF

# Start PostgreSQL
systemctl start postgresql
```

### Backup Strategy

**Automated Daily Backups:**

```bash
#!/bin/bash
# File: /usr/local/bin/ddospot-backup.sh

BACKUP_DIR="/backups/ddospot"
DB_HOST="postgres.ddospot-prod.svc.cluster.local"
DB_USER="ddospot"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
BACKUP_FILE="$BACKUP_DIR/ddospot_$(date +%Y%m%d_%H%M%S).sql.gz"
pg_dump -h $DB_HOST -U $DB_USER ddospot | gzip > $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE s3://backups-bucket/ddospot/

# Clean old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Verify backup
echo "Backup completed: $BACKUP_FILE"
```

**Add to Crontab:**

```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/ddospot-backup.sh >> /var/log/ddospot-backup.log 2>&1
```

---

## Monitoring Integration {#monitoring}

### Prometheus Metrics

**DDoSPoT exposes metrics on port 8888:**

```
GET http://ddospot-node:8888/metrics
```

**Key metrics:**
- `ddospot_threats_total` - Total threats detected
- `ddospot_false_positives_total` - False positive count
- `ddospot_response_actions_total` - Response actions executed
- `ddospot_api_requests_total` - API request count
- `ddospot_database_latency_seconds` - DB query latency

**Prometheus Configuration:**

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ddospot'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['192.0.2.10:8888', '192.0.2.11:8888', '192.0.2.12:8888']
        labels:
          cluster: 'production'
```

---

## Security Hardening {#security}

### Network Security

```bash
# Firewall rules (UFW on Ubuntu)
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (management only from specific IPs)
ufw allow from 203.0.113.0/24 to any port 22

# Allow honeypot traffic
ufw allow 2222/tcp  # SSH honeypot
ufw allow 8888/tcp  # HTTP honeypot
ufw allow 1900/udp  # SSDP honeypot

# Deny direct access to database
ufw deny 5432/tcp

# Enable firewall
ufw enable
```

### AppArmor Profile

```
# /etc/apparmor.d/ddospot-prod
#include <tunables/global>

/opt/ddospot/bin/ddospot {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/python>

  /app/logs/** rw,
  /app/config.json r,
  /var/lib/postgresql/** r,
  /proc/*/stat r,
  /sys/kernel/debug/kprobes/blacklist r,
  
  network inet stream,
  network inet dgram,
  
  deny /etc/shadow rwx,
  deny /root/** rwx,
}
```

---

## Capacity Planning {#capacity}

### Resource Allocation Table

```
Attacks/Day | CPU Cores | RAM  | Storage | Nodes
1,000       | 4         | 8GB  | 100GB   | 1
5,000       | 8         | 16GB | 500GB   | 2-3
10,000      | 12        | 32GB | 1TB     | 3-4
50,000+     | 16+       | 64GB | 5TB+    | 5+
```

### Growth Projection

If current traffic: 1,000 attacks/day
Expected growth: 30% year-over-year

```
Year 1: 1,000/day  → 4 cores needed
Year 2: 1,300/day  → 4 cores (still sufficient)
Year 3: 1,690/day  → 6 cores (upgrade)
Year 4: 2,197/day  → 8 cores (upgrade)
Year 5: 2,856/day  → 8 cores (still sufficient)
```

---

## Troubleshooting {#troubleshooting}

### Common Production Issues

**Issue 1: High Latency**

```bash
# Check database load
docker exec ddospot-db psql -U ddospot -d ddospot -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
docker exec ddospot-db psql -U ddospot -d ddospot -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Solution: Add database indexes or increase connections
```

**Issue 2: Memory Leaks**

```bash
# Monitor memory usage
docker stats ddospot-web

# Check for memory leaks in logs
docker logs ddospot-web | grep -i "memory"

# Solution: Restart container or optimize code
```

**Issue 3: Disk Full**

```bash
# Check disk usage
df -h

# Clean old logs
find /data/logs -name "*.log.*" -mtime +30 -delete

# Archive database
/usr/local/bin/ddospot-backup.sh
```

---

## Summary

Production deployment of DDoSPoT requires:

✅ **Capacity planning** - Matching resources to attack volume
✅ **High availability** - Multiple nodes with failover
✅ **Load balancing** - Distributing traffic efficiently
✅ **Persistent storage** - Database replication and backups
✅ **Monitoring** - Prometheus/Grafana integration
✅ **Security** - Hardening and network isolation
✅ **Scaling strategy** - Planning for growth

---

## Next Steps

- **For Kubernetes**: Review manifests and customize for your cluster
- **For Docker**: Use docker-compose-prod.yml as starting point
- **For Monitoring**: Set up Prometheus scraping
- **For Backup**: Test restore procedures regularly

---

## References

- Docker Production Best Practices
- Kubernetes Production Patterns
- PostgreSQL Replication Guide
- HAProxy Load Balancing

