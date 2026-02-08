# Monitoring and Alerting Guide

**File 19: Prometheus, Grafana, and Alert Configuration**

*Level: Intermediate-Advanced | Time: 2 hours | Prerequisites: Files 4, 8, 9*

---

## Table of Contents
1. [Introduction](#introduction)
2. [Monitoring Architecture](#architecture)
3. [Prometheus Setup](#prometheus)
4. [Grafana Dashboard](#grafana)
5. [Alert Rules](#alerts)
6. [Notification Channels](#notifications)
7. [Performance Metrics](#metrics)
8. [Troubleshooting Alerts](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Introduction {#introduction}

Effective monitoring of DDoSPoT requires:

- **Metrics Collection** - Prometheus scrapes DDoSPoT metrics
- **Visualization** - Grafana displays real-time dashboards
- **Alerting** - Alert rules trigger when thresholds exceeded
- **Notifications** - Alerts sent to Slack, email, etc.
- **Historical Data** - Long-term trends and analysis

---

## Monitoring Architecture {#architecture}

**Data Flow:**

```
DDoSPoT Instance
    ↓ (exposes metrics)
/metrics endpoint
    ↓
Prometheus Server
    ↓ (scrapes every 15 seconds)
Time-series Database
    ↓
Alert Manager
    ↓ (evaluates rules)
Notification Channels
    ↓
Slack / Email / PagerDuty / etc.

And simultaneously:
Prometheus → Grafana Dashboard (visualization)
```

---

## Prometheus Setup {#prometheus}

### Installation

**Using Docker:**

```yaml
# docker-compose.yml (partial)
prometheus:
  image: prom/prometheus:latest
  container_name: prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - ./alert-rules.yml:/etc/prometheus/alert-rules.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'
  networks:
    - monitoring
```

**Configuration File:**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'ddospot-monitor'

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

# Load alert rules
rule_files:
  - '/etc/prometheus/alert-rules.yml'

scrape_configs:
  # DDoSPoT Instances
  - job_name: 'ddospot'
    static_configs:
    - targets: ['ddospot-1:8888', 'ddospot-2:8888', 'ddospot-3:8888']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

  # Database metrics
  - job_name: 'postgres'
    static_configs:
    - targets: ['postgres-exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
    - targets: ['redis-exporter:9121']

  # Node metrics (system resources)
  - job_name: 'node'
    static_configs:
    - targets: ['node-exporter:9100']
```

### Available Metrics

**Core DDoSPoT Metrics:**

```
# Threats detected
ddospot_threats_detected_total{protocol="ssh",threat_type="brute_force"}
ddospot_threats_detected_total{protocol="http",threat_type="sql_injection"}
ddospot_threats_detected_total{protocol="ssdp",threat_type="scanning"}

# False positives
ddospot_false_positives_total{protocol="http",reason="legitimate_scanner"}

# Response actions
ddospot_response_actions_executed_total{action="ip_block",status="success"}
ddospot_response_actions_executed_total{action="rate_limit",status="success"}

# API performance
ddospot_api_requests_total{endpoint="/api/threats",method="GET",status="200"}
ddospot_api_request_duration_seconds{endpoint="/api/threats"}

# System resources
ddospot_system_memory_usage_bytes
ddospot_system_cpu_usage_percent
ddospot_system_disk_usage_bytes

# Database
ddospot_database_query_duration_seconds{query="insert_threat"}
ddospot_database_connections_active

# Detection accuracy
ddospot_detection_accuracy_percent{model="random_forest"}
ddospot_detection_precision_percent{protocol="ssh"}
ddospot_detection_recall_percent{protocol="ssh"}
```

---

## Grafana Dashboard {#grafana}

### Installation

```yaml
# docker-compose.yml (partial)
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
    - GF_INSTALL_PLUGINS=redis-datasource
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
  depends_on:
    - prometheus
  networks:
    - monitoring
```

### Dashboard Configuration

**File**: `grafana/provisioning/dashboards/ddospot-main.json`

```json
{
  "dashboard": {
    "title": "DDoSPoT Main Dashboard",
    "panels": [
      {
        "title": "Threats Detected (Last Hour)",
        "targets": [
          {
            "expr": "rate(ddospot_threats_detected_total[1h])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Detection Accuracy",
        "targets": [
          {
            "expr": "ddospot_detection_accuracy_percent"
          }
        ],
        "type": "stat",
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"color": "red", "value": null},
            {"color": "yellow", "value": 90},
            {"color": "green", "value": 95}
          ]
        }
      },
      {
        "title": "Threats by Protocol",
        "targets": [
          {
            "expr": "sum(rate(ddospot_threats_detected_total[1h])) by (protocol)"
          }
        ],
        "type": "piechart"
      },
      {
        "title": "Response Actions",
        "targets": [
          {
            "expr": "sum(rate(ddospot_response_actions_executed_total[1h])) by (action)"
          }
        ],
        "type": "barchart"
      },
      {
        "title": "API Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ddospot_api_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "System Resources",
        "targets": [
          {
            "expr": "ddospot_system_cpu_usage_percent"
          },
          {
            "expr": "ddospot_system_memory_usage_bytes"
          }
        ],
        "type": "graph"
      },
      {
        "title": "False Positives",
        "targets": [
          {
            "expr": "rate(ddospot_false_positives_total[1h])"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Database Connection Pool",
        "targets": [
          {
            "expr": "ddospot_database_connections_active"
          }
        ],
        "type": "gauge"
      }
    ]
  }
}
```

---

## Alert Rules {#alerts}

### Alert Rules Configuration

**File**: `prometheus/alert-rules.yml`

```yaml
groups:
  - name: ddospot_alerts
    interval: 30s
    rules:
      # Threat Detection Alerts
      - alert: HighThreatDetectionRate
        expr: rate(ddospot_threats_detected_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High threat detection rate"
          description: "{{ $value }} threats/sec detected"

      - alert: CriticalDDoSAttack
        expr: rate(ddospot_threats_detected_total{threat_type="ddos"}[1m]) > 1000
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical DDoS attack detected"
          description: "{{ $value }} DDoS threats/sec detected"

      # Accuracy Alerts
      - alert: LowDetectionAccuracy
        expr: ddospot_detection_accuracy_percent < 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Detection accuracy below threshold"
          description: "Current accuracy: {{ $value }}%"

      - alert: HighFalsePositiveRate
        expr: rate(ddospot_false_positives_total[1h]) / rate(ddospot_threats_detected_total[1h]) > 0.1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High false positive rate"
          description: "False positives: {{ $value | humanizePercentage }}"

      # System Alerts
      - alert: HighCPUUsage
        expr: ddospot_system_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage: {{ $value }}%"

      - alert: OutOfMemory
        expr: ddospot_system_memory_usage_bytes / ddospot_system_memory_available_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory usage critical"
          description: "Memory usage: {{ $value | humanizePercentage }}"

      - alert: DiskSpaceRunningOut
        expr: ddospot_system_disk_usage_bytes / ddospot_system_disk_available_bytes > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low"
          description: "Disk usage: {{ $value | humanizePercentage }}"

      # Database Alerts
      - alert: DatabaseConnections High
        expr: ddospot_database_connections_active > 180
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Active connections: {{ $value }}/200"

      - alert: SlowDatabaseQueries
        expr: histogram_quantile(0.95, rate(ddospot_database_query_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Database queries are slow"
          description: "95th percentile latency: {{ $value }}s"

      # API Alerts
      - alert: APIHighErrorRate
        expr: rate(ddospot_api_requests_total{status=~"5.."}[5m]) / rate(ddospot_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API error rate high"
          description: "Error rate: {{ $value | humanizePercentage }}"

      - alert: APISlowResponse
        expr: histogram_quantile(0.95, rate(ddospot_api_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API responses are slow"
          description: "95th percentile latency: {{ $value }}s"

      # Availability Alerts
      - alert: DDoSPotDown
        expr: up{job="ddospot"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "DDoSPoT instance down"
          description: "Instance {{ $labels.instance }} is down"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database down"
          description: "Database at {{ $labels.instance }} is down"

      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis cache down"
          description: "Redis at {{ $labels.instance }} is down"
```

---

## Notification Channels {#notifications}

### Alertmanager Configuration

**File**: `prometheus/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  receiver: 'default'
  group_by: ['alertname', 'cluster']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h

  routes:
    # Critical alerts go to PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'critical'
      continue: true

    # Warnings go to Slack only
    - match:
        severity: warning
      receiver: 'warnings'

    # DDoS attacks get immediate notification
    - match:
        alertname: CriticalDDoSAttack
      receiver: 'ddos-incident'
      repeat_interval: 5m

inhibit_rules:
  # Don't alert on high CPU if system is down
  - source_match:
      alertname: 'DDoSPotDown'
    target_match:
      alertname: 'HighCPUUsage'
    equal: ['instance']

receivers:
  # Default: Slack notification
  - name: 'default'
    slack_configs:
    - channel: '#security-alerts'
      title: 'Alert: {{ .GroupLabels.alertname }}'
      text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
      send_resolved: true

  # Critical: Slack + Email + PagerDuty
  - name: 'critical'
    slack_configs:
    - channel: '#critical-alerts'
      title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
      text: 'Immediate action required:\n{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
      send_resolved: true
    email_configs:
    - to: 'security-team@example.com'
      from: 'alertmanager@example.com'
      smarthost: 'smtp.gmail.com:587'
      auth_username: 'alertmanager@example.com'
      auth_password: 'YOUR_SMTP_PASSWORD'
      headers:
        Subject: 'CRITICAL ALERT: {{ .GroupLabels.alertname }}'
    pagerduty_configs:
    - service_key: 'YOUR_PAGERDUTY_KEY'
      description: '{{ .GroupLabels.alertname }}'

  # Warnings: Slack only
  - name: 'warnings'
    slack_configs:
    - channel: '#security-warnings'
      title: '⚠️ Warning: {{ .GroupLabels.alertname }}'
      text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  # DDoS Incidents: Multiple channels
  - name: 'ddos-incident'
    slack_configs:
    - channel: '#incident-response'
      title: '🔴 DDoS INCIDENT: {{ .GroupLabels.alertname }}'
      text: 'INCIDENT RESPONSE ACTIVATED\n{{ range .Alerts }}{{ .Annotations.description }}\nSeverity: {{ .Labels.severity }}{{ end }}'
    webhook_configs:
    - url: 'https://incident-response-system.example.com/webhook'
      send_resolved: true
```

---

## Performance Metrics {#metrics}

### Key Metrics to Monitor

**1. Threat Detection Metrics:**

| Metric | Good Value | Warning | Critical |
|--------|-----------|---------|----------|
| Detection Accuracy | >95% | 90-95% | <90% |
| False Positive Rate | <5% | 5-10% | >10% |
| Detection Latency | <100ms | 100-500ms | >500ms |
| Threats/Hour | Baseline ± 20% | Baseline ± 50% | >Baseline × 2 |

**2. System Metrics:**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| CPU Usage | <50% | 50-80% | >80% |
| Memory Usage | <70% | 70-85% | >85% |
| Disk Usage | <70% | 70-85% | >85% |
| API Response Time (p95) | <200ms | 200-500ms | >500ms |

**3. Database Metrics:**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Active Connections | <100 | 100-180 | >180 |
| Query Latency (p95) | <100ms | 100-500ms | >500ms |
| Replication Lag | <1s | 1-5s | >5s |
| Disk Usage | <70% | 70-85% | >85% |

---

## Troubleshooting Alerts {#troubleshooting}

### Alert Not Triggering When Expected

```bash
# 1. Check if metrics are being scraped
curl http://prometheus:9090/api/v1/targets

# 2. Query the metric directly
curl 'http://prometheus:9090/api/v1/query?query=ddospot_threats_detected_total'

# 3. Check alert rule evaluation
curl 'http://prometheus:9090/api/v1/rules'

# 4. Check alert status
curl 'http://prometheus:9090/api/v1/alerts'
```

### Too Many False Alerts

```yaml
# Increase evaluation window
- alert: HighCPUUsage
  expr: ddospot_system_cpu_usage_percent > 80
  for: 10m  # Increase from 5m
  
# OR: Increase threshold
  expr: ddospot_system_cpu_usage_percent > 85  # Increase from 80

# OR: Use rolling average
  expr: avg_over_time(ddospot_system_cpu_usage_percent[5m]) > 80
```

### Alert Firing But Notification Not Sent

```bash
# Check Alertmanager logs
docker logs alertmanager

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_SLACK_WEBHOOK_URL

# Verify alert routing rules
curl http://alertmanager:9093/api/v1/status
```

---

## Best Practices {#best-practices}

### 1. Alert Fatigue Prevention

```yaml
# Good: Context-aware alerts
- alert: HighThreatDetectionRate
  expr: rate(ddospot_threats_detected_total[5m]) > 100
  for: 5m  # Wait 5 minutes before alerting
  annotations:
    description: "{{ $value | humanize }} threats/sec. Expected baseline: 10-50."

# Bad: Too sensitive
- alert: AnyThreatDetected
  expr: ddospot_threats_detected_total > 0
  for: 0m  # Fires immediately
```

### 2. Clear Alert Messages

```yaml
# Good: Actionable and clear
annotations:
  summary: "High false positive rate ({{ $value | humanizePercentage }})"
  description: |
    False positive rate is {{ $value | humanizePercentage }}, indicating model may need retraining.
    Immediate actions:
    1. Review recent detections in dashboard
    2. Check if new attack types are emerging
    3. Consider retraining ML models

# Bad: Vague
annotations:
  summary: "Alert triggered"
  description: "Check system"
```

### 3. Alert Hierarchy

```yaml
# Level 1: Informational (no notification)
- alert: HighThreatVolumeInfo
  expr: rate(ddospot_threats_detected_total[1h]) > 10
  labels:
    severity: info

# Level 2: Warning (Slack notification)
- alert: HighThreatDetectionRate
  expr: rate(ddospot_threats_detected_total[5m]) > 100
  labels:
    severity: warning

# Level 3: Critical (Slack + Email + PagerDuty)
- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  labels:
    severity: critical
```

### 4. Regular Testing

```bash
# Test alert firing (temporarily lower threshold)
# In Prometheus console:
expr: count(up{job="ddospot"}) < 100  # Will be false
expr: count(up{job="ddospot"}) < 1    # Will be true

# Test notification channels monthly
- Run incident response drills
- Verify Slack/email delivery
- Test PagerDuty escalation
```

---

## Summary

Complete monitoring setup includes:

✅ **Prometheus** - Metrics collection and storage
✅ **Grafana** - Visualization dashboards
✅ **Alertmanager** - Alert routing and notifications
✅ **Alert Rules** - 15+ pre-configured alerts
✅ **Notification Channels** - Slack, Email, PagerDuty integration
✅ **Performance Baselines** - What's normal for your environment

---

## Next Steps

- Set up Prometheus scraping (File 18 deployment guide)
- Import Grafana dashboards
- Configure alert notification channels
- Test all alerts and notification delivery
- Establish on-call rotation

