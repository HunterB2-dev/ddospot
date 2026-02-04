# DDoSPot API Documentation

## Overview

The DDoSPot API provides comprehensive REST endpoints for accessing honeypot data, threat intelligence, and automated response capabilities. All requests should be made to `http://your-server:5000/api/`.

**Base URL:** `http://localhost:5000/api`

## Authentication

### API Keys

All protected endpoints require an API key. Include the key in the request header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/endpoint
```

Or as a query parameter:
```bash
curl http://localhost:5000/api/endpoint?api_key=your-api-key
```

### Getting an API Key

Admin users can create API keys via the management endpoint:

```bash
curl -X POST http://localhost:5000/api/auth/keys/create \
  -H "X-API-Key: admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "permissions": ["read", "write"]
  }'
```

### Permissions

API keys support the following permission levels:

- **read**: Access to GET endpoints (data retrieval)
- **write**: Access to POST/PUT endpoints (data modification)
- **admin**: Full access including key management

## Rate Limiting

All endpoints are rate-limited to prevent abuse. Rate limit information is included in response headers:

- `X-RateLimit-Limit`: Maximum requests per period
- `X-RateLimit-Remaining`: Requests remaining in current period
- `X-RateLimit-Reset`: Unix timestamp when limit resets

If rate limited, the API returns `429 Too Many Requests`:

```json
{
  "error": "Rate limit exceeded",
  "limit": 100,
  "period": 60,
  "retry_after": 60
}
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "Error description",
  "status": 400
}
```

### Common Status Codes

- `200`: Success
- `400`: Bad request
- `401`: Unauthorized (missing/invalid API key)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `429`: Rate limited
- `500`: Server error
- `503`: Service unavailable

## Endpoints

### Authentication & Management

#### List API Keys
```
GET /api/auth/keys
Headers:
  X-API-Key: admin-key
Permission: admin
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "count": 2,
  "keys": [
    {
      "key": "dGVzdC1rZXk...",
      "name": "Demo Admin Key",
      "permissions": ["read", "write", "admin"],
      "active": true,
      "created_at": "2026-01-28T10:30:00"
    }
  ]
}
```

#### Create API Key
```
POST /api/auth/keys/create
Headers:
  X-API-Key: admin-key
  Content-Type: application/json
Permission: admin
Rate Limit: 10 per 60s

Request Body:
{
  "name": "My Application",
  "permissions": ["read", "write"]
}

Response:
{
  "success": true,
  "key": "generated-api-key",
  "name": "My Application",
  "permissions": ["read", "write"]
}
```

#### Revoke API Key
```
POST /api/auth/keys/{key_prefix}/revoke
Headers:
  X-API-Key: admin-key
Permission: admin
Rate Limit: 10 per 60s

Response:
{
  "success": true,
  "message": "Key revoked"
}
```

### Health & Status

#### Health Check
```
GET /api/status/health
No authentication required
Rate Limit: 100 per 60s

Response:
{
  "status": "healthy",
  "timestamp": "2026-01-28T10:30:00",
  "database": "connected",
  "event_count": 1250
}
```

#### API Statistics
```
GET /api/status/stats
Headers:
  X-API-Key: your-api-key
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "stats": {
    "total_rate_limit_entries": 45,
    "active_api_keys": 3,
    "total_api_keys": 5,
    "rate_limit_store_keys": ["endpoint1:ip1", "endpoint2:ip2"]
  },
  "timestamp": "2026-01-28T10:30:00"
}
```

### Logs & Events

#### Get Recent Events
```
GET /api/logs/recent?limit=50&offset=0&source_ip=192.168.1.1&protocol=SSH&port=22
Headers:
  X-API-Key: your-api-key (optional)
Permission: read
Rate Limit: 100 per 60s

Response:
{
  "success": true,
  "total": 150,
  "limit": 50,
  "offset": 0,
  "events": [
    {
      "id": 1,
      "timestamp": 1704067800,
      "source_ip": "192.168.1.1",
      "port": 2222,
      "protocol": "SSH",
      "payload_size": 256,
      "event_type": "ssh_auth_attempt",
      "created_at": "2026-01-28T10:30:00"
    }
  ]
}
```

#### Get Live Event Stream
```
GET /api/logs/stream?since_timestamp=1704067800&limit=100
Headers:
  X-API-Key: your-api-key (optional)
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "new_events": 12,
  "events": [...]
}
```

#### Get Filter Options
```
GET /api/logs/filters
Permission: read (optional)
Rate Limit: 100 per 60s

Response:
{
  "protocols": ["SSH", "HTTP", "SSDP"],
  "ports": [22, 80, 1900],
  "event_types": ["ssh_auth", "http_request", "ssdp_discovery"]
}
```

### Anomaly Detection

#### Detect Anomalies
```
GET /api/anomalies/detect?hours=24&sensitivity=2.0
Headers:
  X-API-Key: your-api-key
Permission: read
Rate Limit: 20 per 60s

Response:
{
  "success": true,
  "anomalies_found": 5,
  "anomalies": [
    {
      "type": "unusual_payload",
      "source_ip": "192.168.1.50",
      "event_count": 15,
      "severity": "medium"
    }
  ]
}
```

#### Get Anomaly Summary
```
GET /api/anomalies/summary?hours=24
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "total_anomalies": 8,
  "severity": "medium",
  "types_breakdown": {
    "unusual_payload": 3,
    "high_frequency": 5
  }
}
```

#### Get IP Behavior Profile
```
GET /api/anomalies/profile/{ip}?hours=168
Permission: read
Rate Limit: 100 per 60s

Response:
{
  "success": true,
  "source_ip": "192.168.1.1",
  "event_count": 125,
  "protocol_count": 3,
  "port_count": 5,
  "events_per_minute": 2.5,
  "protocols": ["SSH", "HTTP"],
  "ports": [22, 80, 443]
}
```

### Geographic Data

#### Get Heatmap Data
```
GET /api/geo/heatmap?hours=24
Permission: read
Rate Limit: 30 per 60s

Response:
{
  "success": true,
  "heatmap_points": [
    {
      "latitude": 35.6762,
      "longitude": 139.6503,
      "intensity": 0.85,
      "event_count": 120
    }
  ]
}
```

#### Get Geographic Locations
```
GET /api/geo/locations?hours=24&limit=50
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "locations": [
    {
      "source_ip": "192.168.1.1",
      "country": "JP",
      "city": "Tokyo",
      "latitude": 35.6762,
      "longitude": 139.6503,
      "event_count": 145
    }
  ]
}
```

#### Get Country Statistics
```
GET /api/geo/countries?hours=24
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "countries": [
    {
      "name": "Japan",
      "code": "JP",
      "event_count": 250,
      "unique_ips": 45,
      "severity": "high"
    }
  ]
}
```

### Threat Intelligence

#### Get Threat Score for IP
```
GET /api/threat/score/{ip}
Headers:
  X-API-Key: your-api-key
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "source_ip": "192.168.1.1",
  "threat_score": 7.5,
  "threat_type": "high_frequency_attack",
  "geolocation": {
    "country": "JP",
    "city": "Tokyo"
  },
  "behavior": {
    "events": 145,
    "protocols": 3,
    "ports": 5,
    "rate": 2.5
  }
}
```

#### Get High-Risk IPs
```
GET /api/threat/high-risk?threshold=7.0&limit=50
Permission: read
Rate Limit: 40 per 60s

Response:
{
  "success": true,
  "threshold": 7.0,
  "count": 8,
  "high_risk_ips": [
    {
      "source_ip": "192.168.1.50",
      "risk_score": 8.5,
      "threat_type": "multi_protocol_attack",
      "threat_description": "Multiple protocol attack detected"
    }
  ]
}
```

#### Get Threat Summary
```
GET /api/threat/summary
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "high_risk_count": 8,
  "overall_threat_level": "high",
  "score_distribution": {
    "critical": 2,
    "high": 6,
    "medium": 15,
    "low": 50
  },
  "threat_types": {
    "high_frequency_attack": 12,
    "multi_protocol_attack": 8,
    "port_scanning": 5
  }
}
```

#### Bulk IP Threat Scan
```
POST /api/threat/bulk-scan
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json
Permission: read
Rate Limit: 10 per 60s

Request Body:
{
  "ips": ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
}

Response:
{
  "success": true,
  "scanned": 3,
  "results": [
    {
      "source_ip": "192.168.1.1",
      "risk_score": 7.5,
      "threat_type": "high_frequency_attack"
    }
  ]
}
```

### Response Actions

#### Block IP
```
POST /api/response/block-ip
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json
Permission: write
Rate Limit: 20 per 60s

Request Body:
{
  "ip": "192.168.100.50",
  "reason": "High-frequency attack detected",
  "threat_type": "high_frequency_attack",
  "risk_score": 8.5,
  "permanent": true
}

Response:
{
  "success": true,
  "ip": "192.168.100.50",
  "status": "blocked",
  "reason": "High-frequency attack detected"
}
```

#### Unblock IP
```
POST /api/response/unblock-ip
Permission: write
Rate Limit: 20 per 60s

Request Body:
{
  "ip": "192.168.100.50"
}

Response:
{
  "success": true,
  "ip": "192.168.100.50",
  "status": "unblocked"
}
```

#### Get Blocked IPs
```
GET /api/response/blocked-ips?limit=50
Permission: read
Rate Limit: 50 per 60s

Response:
{
  "success": true,
  "count": 12,
  "blocked_ips": [
    {
      "ip": "192.168.100.50",
      "reason": "High-frequency attack detected",
      "threat_type": "high_frequency_attack",
      "risk_score": 8.5,
      "blocked_at": "2026-01-28T10:30:00",
      "is_permanent": true
    }
  ]
}
```

#### Add Webhook
```
POST /api/response/webhook/add
Permission: write
Rate Limit: 10 per 60s

Request Body:
{
  "url": "https://webhook.example.com/ddospot",
  "event_type": "all_threats"
}

Response:
{
  "success": true,
  "url": "https://webhook.example.com/ddospot",
  "event_type": "all_threats",
  "status": "added"
}
```

## Pagination

Endpoints supporting pagination use these query parameters:

- `limit`: Number of results to return (default: 50, max: 500)
- `offset`: Offset for pagination (default: 0)

Example:
```bash
curl "http://localhost:5000/api/logs/recent?limit=100&offset=50"
```

## Filtering

Most list endpoints support filtering via query parameters:

- `source_ip`: Filter by source IP
- `protocol`: Filter by protocol (SSH, HTTP, SSDP)
- `port`: Filter by port number
- `hours`: Time range in hours (default: 24)

Example:
```bash
curl "http://localhost:5000/api/logs/recent?source_ip=192.168.1.1&protocol=SSH&hours=48"
```

## Request/Response Format

### Request Headers
```
X-API-Key: your-api-key
Content-Type: application/json
Accept: application/json
```

### Response Format
All responses include:
- `success`: Boolean indicating success/failure
- `data`: Response data (varies by endpoint)
- `error`: Error message (if applicable)
- `timestamp`: Request timestamp

### Timestamps
Timestamps are provided in two formats:
- Unix timestamp (seconds since epoch)
- ISO 8601 format (e.g., `2026-01-28T10:30:00`)

## Examples

### Python

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost:5000/api"

headers = {"X-API-Key": API_KEY}

# Get recent events
response = requests.get(
    f"{BASE_URL}/logs/recent?limit=50",
    headers=headers
)
events = response.json()

# Get threat summary
response = requests.get(
    f"{BASE_URL}/threat/summary",
    headers=headers
)
threats = response.json()

# Block an IP
response = requests.post(
    f"{BASE_URL}/response/block-ip",
    headers=headers,
    json={
        "ip": "192.168.1.100",
        "reason": "Malicious activity",
        "permanent": True
    }
)
```

### cURL

```bash
# List API keys (admin only)
curl -H "X-API-Key: admin-key" \
  http://localhost:5000/api/auth/keys

# Get threat summary
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/threat/summary

# Block an IP
curl -X POST http://localhost:5000/api/response/block-ip \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "reason": "Malicious activity",
    "permanent": true
  }'
```

### JavaScript/Node.js

```javascript
const API_KEY = "your-api-key";
const BASE_URL = "http://localhost:5000/api";

// Get recent events
const response = await fetch(`${BASE_URL}/logs/recent?limit=50`, {
  headers: { "X-API-Key": API_KEY }
});
const events = await response.json();

// Block an IP
const blockResponse = await fetch(`${BASE_URL}/response/block-ip`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    ip: "192.168.1.100",
    reason: "Malicious activity",
    permanent: true
  })
});
```

## Best Practices

1. **Security**: Never commit API keys to version control. Use environment variables.
2. **Rate Limiting**: Implement exponential backoff when receiving 429 responses.
3. **Monitoring**: Monitor rate limit headers to avoid hitting limits.
4. **Error Handling**: Implement proper error handling for all HTTP status codes.
5. **Caching**: Cache responses when appropriate to reduce API calls.
6. **Authentication**: Use strong, unique API keys for each application.
7. **HTTPS**: Always use HTTPS in production environments.

## Support

For issues or questions about the API:
- Check the troubleshooting section in docs/
- Review error messages and status codes
- Enable debug logging with `LOG_LEVEL=DEBUG`
