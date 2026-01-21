# DDoSPoT Enhanced Monitoring Setup Guide

## Overview
DDoSPoT now includes comprehensive Prometheus metrics export and alerting capabilities for real-time monitoring of attack patterns, service health, and system performance.

## Components

### 1. Prometheus Metrics (`/metrics` endpoint)
The dashboard exposes metrics at `http://localhost:5000/metrics` for Prometheus scraping.

**Metric Categories:**
- **Attack Metrics**: Event counts, bytes, unique attackers, protocols
- **Service Health**: Status, uptime, resource usage
- **Database**: Size, event count, query performance
- **HTTP**: Request rates, latency histograms
- **Geolocation**: Cache hits/misses, country distribution
- **Machine Learning**: Prediction counts, latency
- **Alerts**: Sent/failed alert counts by channel
- **Logs**: File sizes, rotation events

### 2. Prometheus Configuration
File: `monitoring/prometheus.yml`

Scrape configuration for DDoSPoT:
- **Dashboard metrics**: http://localhost:5000/metrics (every 10s)
- **Alert rules**: Loaded from `ddospot_alerts.yml`
- **Alertmanager**: localhost:9093

### 3. Alert Rules
File: `monitoring/ddospot_alerts.yml`

Pre-configured alerts for:
- High/critical attack rates
- Distributed attacks (botnet detection)
- Service downtime
- Resource exhaustion (CPU, memory, disk)
- Database performance issues
- Large log files
- Slow ML predictions

### 4. Grafana Dashboard
File: `monitoring/grafana-dashboard.json`

Pre-built dashboard with 11 panels:
- Total events & unique attackers
- Attack rate by protocol
- Protocol distribution (pie chart)
- System resources (CPU, disk)
- Memory & storage usage
- HTTP request latency (p95, p99)
- HTTP request rates
- Geolocation cache performance
- Alert delivery status

## Installation

### Prerequisites
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64/

# Install Alertmanager (optional)
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz

# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
```

### Setup Steps

#### 1. Configure Prometheus
```bash
# Copy configuration files
cp monitoring/prometheus.yml /etc/prometheus/prometheus.yml
cp monitoring/ddospot_alerts.yml /etc/prometheus/ddospot_alerts.yml

# Start Prometheus
prometheus --config.file=/etc/prometheus/prometheus.yml
```

#### 2. Start DDoSPoT Services
```bash
# Start dashboard (metrics endpoint will be available)
./cli.py
# Choose option 2 (Start Dashboard)
```

#### 3. Verify Metrics Endpoint
```bash
# Check metrics are available
curl http://localhost:5000/metrics

# Should see output like:
# ddospot_attack_events_total{protocol="HTTP",event_type="attack"} 150.0
# ddospot_unique_attackers 23.0
# ddospot_cpu_usage_percent 45.2
# ...
```

#### 4. Setup Alertmanager (Optional)
```bash
# Create alertmanager.yml
cat > /etc/prometheus/alertmanager.yml << EOF
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'security@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'your-password'
EOF

# Start Alertmanager
alertmanager --config.file=/etc/prometheus/alertmanager.yml
```

#### 5. Import Grafana Dashboard
```bash
# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Open Grafana: http://localhost:3000
# Default login: admin / admin

# Add Prometheus data source:
# 1. Go to Configuration → Data Sources
# 2. Add Prometheus
# 3. URL: http://localhost:9090
# 4. Save & Test

# Import dashboard:
# 1. Go to Dashboards → Import
# 2. Upload monitoring/grafana-dashboard.json
# 3. Select Prometheus data source
# 4. Import
```

## Usage

### View Metrics in CLI
```bash
./cli.py
# Choose option 22 (Health Check)
# Metrics endpoint status will be shown
```

### Query Metrics with PromQL
```bash
# Attack rate (events per second)
rate(ddospot_attack_events_total[5m])

# Unique attackers over time
ddospot_unique_attackers

# HTTP request latency (95th percentile)
histogram_quantile(0.95, rate(ddospot_http_request_duration_seconds_bucket[5m]))

# Database size in MB
ddospot_database_size_bytes / 1024 / 1024

# CPU usage
ddospot_cpu_usage_percent
```

### Monitor Active Alerts
```bash
# View Prometheus alerts
# Open: http://localhost:9090/alerts

# View Alertmanager
# Open: http://localhost:9093
```

### Grafana Dashboards
```bash
# Open Grafana
# URL: http://localhost:3000
# Navigate to Dashboards → DDoSPoT Honeypot Dashboard
```

## Alerting Examples

### Email Notifications
Configure Alertmanager with SMTP:
```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'security@example.com'
        from: 'ddospot@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
        headers:
          Subject: '[DDoSPoT] {{ .GroupLabels.severity | toUpper }} - {{ .GroupLabels.alertname }}'
```

### Slack Notifications
```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#security-alerts'
        title: 'DDoSPoT Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### PagerDuty Integration
```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-service-key'
        description: '{{ .GroupLabels.alertname }} - {{ .GroupLabels.severity }}'
```

## Monitoring Best Practices

1. **Set appropriate scrape intervals**
   - Real-time attack monitoring: 10-15s
   - System metrics: 30-60s

2. **Configure alert thresholds**
   - Tune based on your baseline traffic
   - Adjust in `monitoring/ddospot_alerts.yml`

3. **Data retention**
   - Prometheus default: 15 days
   - Configure in prometheus.yml: `--storage.tsdb.retention.time=30d`

4. **Performance considerations**
   - Metrics endpoint adds minimal overhead (~1-2ms per request)
   - Scraping every 10s = ~8,640 requests/day
   - Database metrics updated on demand

5. **Security**
   - Restrict metrics endpoint access (firewall rules)
   - Use authentication proxy if exposing externally
   - Monitor for metrics endpoint abuse
   - Optional token protection: set `DDOSPOT_API_TOKEN`, then `DDOSPOT_REQUIRE_TOKEN=true`
   - Make `/metrics` private: set `DDOSPOT_METRICS_PUBLIC=false`
   - Protect `/health`: set `DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH=true`
   - Enable rate limiting: tune `DDOSPOT_RATE_LIMIT_MAX`, `DDOSPOT_RATE_LIMIT_WINDOW`, `DDOSPOT_RATE_LIMIT_BLACKLIST`

## Troubleshooting

### Metrics endpoint returns 500 error
```bash
# Check dashboard logs
tail -f /tmp/dashboard.log

# Verify dashboard is running
./cli.py
# Option 22 - Health Check
```

### Prometheus can't scrape metrics
```bash
# Test connectivity
curl http://localhost:5000/metrics

# Check Prometheus targets
# Open: http://localhost:9090/targets
```

### No data in Grafana
```bash
# Verify Prometheus data source
# Grafana → Configuration → Data Sources

# Test PromQL query in Prometheus
# Open: http://localhost:9090/graph
# Query: ddospot_attack_events_total
```

### Alerts not firing
```bash
# Check alert rules syntax
promtool check rules /etc/prometheus/ddospot_alerts.yml

# Verify alert evaluation
# Open: http://localhost:9090/alerts

# Check Alertmanager logs
journalctl -u alertmanager -f
```

## Metrics Reference

### Attack Metrics
- `ddospot_attack_events_total{protocol, event_type}` - Counter
- `ddospot_attack_bytes_total{protocol}` - Counter
- `ddospot_unique_attackers` - Gauge
- `ddospot_blacklisted_ips` - Gauge

### Service Health
- `ddospot_service_status{service}` - Gauge (1=running, 0=stopped)
- `ddospot_service_uptime_seconds{service}` - Gauge
- `ddospot_cpu_usage_percent` - Gauge
- `ddospot_memory_usage_bytes` - Gauge
- `ddospot_disk_usage_percent` - Gauge

### Database
- `ddospot_database_size_bytes` - Gauge
- `ddospot_database_events_total` - Gauge
- `ddospot_database_profiles_total` - Gauge
- `ddospot_database_query_duration_seconds` - Histogram

### HTTP
- `ddospot_http_requests_total{method, endpoint, status}` - Counter
- `ddospot_http_request_duration_seconds{method, endpoint}` - Histogram

### Geolocation
- `ddospot_geolocation_cache_hits_total` - Counter
- `ddospot_geolocation_cache_misses_total` - Counter
- `ddospot_geolocation_countries_total` - Gauge

### Machine Learning
- `ddospot_ml_predictions_total{prediction}` - Counter
- `ddospot_ml_prediction_duration_seconds` - Histogram

### Alerts
- `ddospot_alerts_sent_total{channel, severity}` - Counter
- `ddospot_alerts_failed_total{channel, reason}` - Counter

### Logs
- `ddospot_log_file_size_bytes{log_type}` - Gauge
- `ddospot_log_rotations_total{log_type}` - Counter

## Docker Deployment

```yaml
# docker-compose.yml for monitoring stack
version: '3.8'
services:
  ddospot-dashboard:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./honeypot.db:/app/honeypot.db
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/ddospot_alerts.yml:/etc/prometheus/ddospot_alerts.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/ddospot.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
  
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

volumes:
  grafana-storage:
```

Deploy:
```bash
docker-compose up -d
```

## Next Steps
- Configure alert channels (email, Slack, PagerDuty)
- Customize alert thresholds for your environment
- Set up long-term metric storage (e.g., Thanos, Cortex)
- Create custom Grafana dashboards
- Integrate with SIEM systems
