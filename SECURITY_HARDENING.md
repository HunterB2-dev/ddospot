# DDoSPoT Security Hardening

This document outlines the security features and best practices for deploying DDoSPoT in production.

## Overview

DDoSPoT includes configurable rate limiting and token-based authentication to protect the dashboard API and metrics endpoints from unauthorized access and abuse.

## Features

### 1. Rate Limiting

**Mechanism**: Per-IP rate limiting with automatic temporary blacklist.

**Configuration** (via environment variables):
- `DDOSPOT_RATE_LIMIT_MAX`: Maximum requests per window (default: 60)
- `DDOSPOT_RATE_LIMIT_WINDOW`: Time window in seconds (default: 60)
- `DDOSPOT_RATE_LIMIT_BLACKLIST`: Temporary blacklist duration in seconds (default: 120)

**Applies to**:
- `/api/*` endpoints
- `/metrics` endpoint
- `/health` endpoint

**Response**: HTTP 429 (Too Many Requests) when rate limit exceeded.

**Example**:
```bash
# Allow 30 requests per 30 seconds, blacklist for 5 minutes on violation
export DDOSPOT_RATE_LIMIT_MAX=30
export DDOSPOT_RATE_LIMIT_WINDOW=30
export DDOSPOT_RATE_LIMIT_BLACKLIST=300
```

### 2. Token-Based Authentication

**Mechanism**: Bearer token authentication via `Authorization` header or `X-API-Token` header or query parameter `token`.

**Configuration**:
- `DDOSPOT_API_TOKEN`: Shared secret token (recommended 32+ chars)
- `DDOSPOT_REQUIRE_TOKEN`: Enable enforcement (default: false)
- `DDOSPOT_METRICS_PUBLIC`: Keep `/metrics` public (default: true; set `false` to require token)
- `DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH`: Protect `/health` endpoint (default: false)

**Token Sources** (in priority order):
1. `Authorization: Bearer <token>` header
2. `X-API-Token: <token>` header
3. Query parameter: `?token=<token>`
4. `config.json` -> `api.token`

**Protected Endpoints** (when `DDOSPOT_REQUIRE_TOKEN=true`):
- POST `/api/alerts/config` - Update alert configuration
- POST `/api/alerts/test` - Send test alerts
- POST `/api/ml/train` - Train ML model
- POST `/api/ml/batch-predict` - Batch predict attack types

**Optional Protection**:
- GET `/metrics` (if `DDOSPOT_METRICS_PUBLIC=false`)
- GET `/health` (if `DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH=true`)

**Response**: HTTP 401 (Unauthorized) if token missing or invalid.

**Example**:
```bash
# Generate strong token
export DDOSPOT_API_TOKEN=$(openssl rand -hex 32)

# Enable all protections
export DDOSPOT_REQUIRE_TOKEN=true
export DDOSPOT_METRICS_PUBLIC=false

# Start dashboard
./cli.py
# Choose option 2 (Start Dashboard)
```

**CLI Support**:
- Health check automatically uses token if configured
- Example: `./cli.py` → option 22 (Health Check)

### 3. Input Validation

**POST endpoints** validate request payloads:
- `/api/alerts/config`: Requires JSON object (dict)
- `/api/ml/batch-predict`: Validates `ips` as list of strings, `limit` as integer (1-1000)

**Response**: HTTP 400 (Bad Request) for invalid payloads.

### 4. Proxy Headers

**Client IP detection** respects `X-Forwarded-For` header for rate limiting behind reverse proxies.

## Best Practices

### Development
```bash
# Disable auth for testing
export DDOSPOT_REQUIRE_TOKEN=false
export DDOSPOT_METRICS_PUBLIC=true

# Run with minimal rate limiting
export DDOSPOT_RATE_LIMIT_MAX=1000
export DDOSPOT_RATE_LIMIT_WINDOW=60
```

### Staging
```bash
# Enable token auth but keep metrics accessible
export DDOSPOT_API_TOKEN=staging-token-123
export DDOSPOT_REQUIRE_TOKEN=true
export DDOSPOT_METRICS_PUBLIC=true

# Moderate rate limits
export DDOSPOT_RATE_LIMIT_MAX=100
export DDOSPOT_RATE_LIMIT_WINDOW=60
export DDOSPOT_RATE_LIMIT_BLACKLIST=300
```

### Production
```bash
# Generate strong token
DDOSPOT_API_TOKEN=$(openssl rand -hex 32)
export DDOSPOT_API_TOKEN

# Enable all protections
export DDOSPOT_REQUIRE_TOKEN=true
export DDOSPOT_METRICS_PUBLIC=false
export DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH=true

# Strict rate limits
export DDOSPOT_RATE_LIMIT_MAX=50
export DDOSPOT_RATE_LIMIT_WINDOW=60
export DDOSPOT_RATE_LIMIT_BLACKLIST=600

# Store in config.json for persistence (optional)
```

## Configuration File

**File**: `config.json`

```json
{
  "api": {
    "token": "your-strong-secret-token-here"
  },
  "log_rotation": {
    "max_bytes": 5242880,
    "backups": 2
  }
}
```

**Priority**: Environment variables override `config.json`.

## Monitoring & Logging

### CLI Health Check
```bash
./cli.py
# Choose 22 (Health Check)
```

Output shows:
- Metrics endpoint status
- 401 Unauthorized → token required or invalid
- 429 Too Many Requests → rate limited
- ✓ → healthy

### Logs
- Dashboard: `/tmp/dashboard.log`
- Rate limit violations: Logged at info level
- Token auth failures: Logged at debug level

### Prometheus Metrics
Monitor security events via `/metrics` endpoint:
- HTTP request rates and latencies
- Rate limit violations (via 429 responses)
- Endpoint access patterns

## Deployment Examples

### Docker Compose
```yaml
services:
  dashboard:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DDOSPOT_API_TOKEN=${DDOSPOT_API_TOKEN}
      - DDOSPOT_REQUIRE_TOKEN=true
      - DDOSPOT_METRICS_PUBLIC=false
      - DDOSPOT_RATE_LIMIT_MAX=50
      - DDOSPOT_RATE_LIMIT_WINDOW=60
      - DDOSPOT_RATE_LIMIT_BLACKLIST=600
    volumes:
      - ./honeypot.db:/app/honeypot.db
      - ./config.json:/app/config.json
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 443 ssl;
    server_name ddospot.example.com;

    ssl_certificate /etc/ssl/certs/ddospot.crt;
    ssl_certificate_key /etc/ssl/private/ddospot.key;

    # Optional: Add API key header at proxy level
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Authorization "Bearer ${DDOSPOT_API_TOKEN}";
        proxy_set_header X-Forwarded-For $remote_addr;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

### Systemd Service
```ini
[Unit]
Description=DDoSPoT Dashboard
After=network.target

[Service]
Type=simple
User=ddospot
WorkingDirectory=/opt/ddospot
Environment="DDOSPOT_API_TOKEN=<strong-token>"
Environment="DDOSPOT_REQUIRE_TOKEN=true"
Environment="DDOSPOT_METRICS_PUBLIC=false"
ExecStart=/opt/ddospot/myenv/bin/python dashboard.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Security Checklist

- [ ] Generate strong `DDOSPOT_API_TOKEN` (32+ random characters)
- [ ] Set `DDOSPOT_REQUIRE_TOKEN=true` in production
- [ ] Set `DDOSPOT_METRICS_PUBLIC=false` if exposing externally
- [ ] Configure firewall to restrict dashboard access
- [ ] Use HTTPS/TLS for external exposure (reverse proxy)
- [ ] Store token securely (environment, secrets manager)
- [ ] Monitor `/tmp/dashboard.log` for suspicious activity
- [ ] Test rate limiting: `for i in {1..100}; do curl -s http://localhost:5000/api/stats; done`
- [ ] Review Prometheus alerts configuration
- [ ] Enable `DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH=true` if needed
- [ ] Keep dependencies updated: `pip install --upgrade -r requerements.txt`

## Troubleshooting

### 401 Unauthorized on /metrics
```bash
# Verify token is set and correct
echo $DDOSPOT_API_TOKEN

# Request with token
curl -H "Authorization: Bearer $DDOSPOT_API_TOKEN" http://localhost:5000/metrics
```

### 429 Rate Limited
```bash
# Check rate limit settings
env | grep DDOSPOT_RATE_LIMIT

# Wait for blacklist to expire or restart dashboard
```

### Token not reading from config.json
```bash
# Verify config.json exists and is valid JSON
cat config.json | python3 -m json.tool

# Prefer environment variable for production
export DDOSPOT_API_TOKEN=<token>
```

## Support

For security issues, report via the project's security policy or contact the maintainers directly.

