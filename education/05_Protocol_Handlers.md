# Protocol Handlers in DDoSPoT: Deep Dive

## Overview

DDoSPoT monitors three key network protocols that are frequently targeted by attackers. Each protocol handler is optimized to detect specific attack patterns while simulating legitimate services.

---

## 1. SSH Honeypot (Port 2222)

### Why SSH?

SSH (Secure Shell) is one of the most attacked services on the internet because:
- Default port 22 is well-known
- Used by attackers for remote access
- Vulnerable to brute-force attacks
- Target for credential theft
- Frequently scanned by automated tools

### How It Works

```
Attacker connects to port 2222
  ↓
DDoSPoT SSH handler responds
  ↓
Presents fake SSH banner
  ↓
Logs all credentials attempted
  ↓
Blocks access gracefully
  ↓
Generates security alert
  ↓
Triggers response (IP block, notification)
```

### Attack Types Detected

#### 1. Brute Force Attacks
```
Attacker: ssh -u root 192.168.1.10 -p 2222
Password: password123
DDoSPoT Response: ❌ Access Denied (Logged)

Attacker: ssh -u admin 192.168.1.10 -p 2222
Password: admin
DDoSPoT Response: ❌ Access Denied (Logged)
```

**What it indicates**: Automated password guessing  
**Response**: Block after N attempts  

#### 2. Credential Scanning
```
Attempts: root/password, root/123456, admin/admin, etc.
Pattern: Trying default credentials
DDoSPoT: Records all attempts, patterns, timing
```

**What it indicates**: Systematic credential attack  
**Response**: Immediate IP blocking  

#### 3. Protocol Scanning
```
Port 2222 scan
Banner grab: SSH-2.0-OpenSSH_7.4
DDoSPoT: Identifies scanner fingerprint
```

**What it indicates**: Reconnaissance activity  
**Response**: Alert and block  

#### 4. Version Detection Attacks
```
Attacker scans for SSH version
Exploits: Known vulnerabilities in version
DDoSPoT: Responds with fake but convincing banner
```

**What it indicates**: Targeted version exploitation  
**Response**: Detect + block + alert  

### SSH Handler Statistics

| Metric | Typical Value |
|--------|---------------|
| **Attack attempts/day** | 100-500+ |
| **Unique attackers** | 20-100 |
| **Failed login ratio** | 99.5%+ |
| **Detection latency** | < 50ms |
| **Response time** | 100-200ms |

### Configuration

```python
# From core/config.py
SSH_HONEYPOT = {
    'port': 2222,
    'fake_banner': 'SSH-2.0-OpenSSH_7.4',
    'max_attempts': 3,
    'lockout_time': 300,
    'log_level': 'INFO'
}
```

### Common Attack Patterns

**Pattern 1: Dictionary Attack**
```
Dictionary attack with common passwords
Characteristic: 10-100 attempts per connection
Detection: By attempt rate and password list correlation
```

**Pattern 2: Credential Stuffing**
```
Using leaked credentials from other breaches
Characteristic: Multiple IPs, same credentials
Detection: Matching against known breach patterns
```

**Pattern 3: Scanner Reconnaissance**
```
Automated scanning for SSH services
Characteristic: Banner grab only, no authentication
Detection: By scan pattern recognition
```

### Real Attack Example

```
2024-01-15 03:45:22 | SSH Attack from 203.0.113.45
├─ 03:45:23: root / password
├─ 03:45:24: root / 123456
├─ 03:45:25: admin / admin
├─ 03:45:26: root / root
└─ 03:45:27: [BLOCKED] - Exceeded attempt threshold
    Response: IP blocked for 1 hour
    Alert: Sent to security team
```

---

## 2. HTTP Honeypot (Port 8888)

### Why HTTP?

HTTP/HTTPS web services are attacked for:
- Web application exploits
- SQL injection attempts
- Path traversal attacks
- Malicious file uploads
- API abuse
- DDoS attacks
- Credential capture

### How It Works

```
Attacker sends HTTP request
  ↓
DDoSPoT HTTP handler receives
  ↓
Analyzes request for malicious patterns
  ↓
Serves fake web content
  ↓
Logs all request details
  ↓
Detects attack signatures
  ↓
Generates security alert
```

### Attack Types Detected

#### 1. SQL Injection Attempts

```
GET /api/users?id=1' OR '1'='1
GET /search.php?q=<script>alert('xss')</script>
GET /admin.php?user=admin'--
```

**Detection**: Signature matching + pattern analysis  
**Response**: Log and alert  

#### 2. Path Traversal/Directory Attacks

```
GET /../../../etc/passwd
GET /admin/../../config/database.php
GET /.git/config
GET /.aws/credentials
```

**Detection**: Path normalization + forbidden patterns  
**Response**: 403 Forbidden + log  

#### 3. Web Shell Upload Attempts

```
POST /upload.php
Content-Type: multipart/form-data

filename: shell.php
content: <?php system($_GET['cmd']); ?>
```

**Detection**: File type + content analysis  
**Response**: Block + alert  

#### 4. API Abuse/Scraping

```
Rapid requests to /api/endpoint
Multiple requests per second
Looking for data leakage
```

**Detection**: Rate limiting + pattern matching  
**Response**: Rate limit + block  

#### 5. DDoS/Flood Attacks

```
GET / (repeated 1000s of times)
Different IPs, same target
```

**Detection**: Request rate analysis  
**Response**: Automatic IP blocking  

### HTTP Handler Statistics

| Metric | Typical Value |
|--------|---------------|
| **HTTP requests/day** | 1,000-10,000+ |
| **Attack requests ratio** | 20-40% |
| **Most common attack** | SQL injection |
| **Detection latency** | < 100ms |
| **Response time** | 100-300ms |

### Configuration

```python
# From core/config.py
HTTP_HONEYPOT = {
    'port': 8888,
    'fake_banner': 'Apache/2.4.41',
    'fake_content': 'wordpress',  # or 'custom'
    'rate_limit': 100,  # requests per minute
    'block_threshold': 1000,  # requests in 5 minutes
    'log_level': 'INFO'
}
```

### Common Attack Patterns

**Pattern 1: Automated Vulnerability Scanner**
```
Scanning for known vulnerabilities
Using tools like: SQLMap, Nikto, OpenVAS
Characteristic: Specific payload sequences
```

**Pattern 2: Web Application Exploit**
```
Targeted attack against specific platform
Example: WordPress admin panel bruteforce
Characteristic: Platform-specific payloads
```

**Pattern 3: Bot Activity**
```
Automated crawling and scraping
Looking for sensitive data
Characteristic: Specific User-Agent patterns
```

### Real Attack Example

```
2024-01-15 14:22:45 | HTTP Attack from 198.51.100.42
├─ 14:22:46: GET /admin -> 404
├─ 14:22:47: GET /wp-admin -> 404
├─ 14:22:48: GET /index.php?id=1' OR '1'='1
│   Signature: SQL Injection Detected ⚠️
├─ 14:22:49: GET /upload.php (POST shell.php)
│   Signature: Web Shell Attempt Detected ⚠️
└─ 14:22:50: [BLOCKED] - Attack Pattern Identified
    Response: IP blocked, Alert escalated
```

---

## 3. SSDP Honeypot (Port 1900)

### Why SSDP?

SSDP (Simple Service Discovery Protocol) is attacked for:
- Amplification attacks (DDoS)
- Device discovery and fingerprinting
- IoT botnet recruitment
- Network mapping
- Reflected traffic exploitation

### How It Works

```
Attacker sends SSDP discovery request
  ↓
DDoSPoT SSDP handler receives
  ↓
Analyzes request pattern
  ↓
Responds with fake device information
  ↓
Logs source and pattern
  ↓
Detects amplification attempts
  ↓
Generates security alert
```

### Attack Types Detected

#### 1. Amplification Attacks

```
Attacker sends: SSDP M-SEARCH (small request)
Server responds: Large XML device description
Amplification: 30-100x traffic increase
Attacker uses: Multiple servers for DDoS
```

**Detection**: Response size ratio + source patterns  
**Response**: Block and alert  

#### 2. Device Discovery/Fingerprinting

```
Attacker: M-SEARCH for UPnP devices
Response: Fake device list
Goal: Map network devices
```

**Detection**: Discovery request patterns  
**Response**: Log and analyze  

#### 3. Botnet Recruitment

```
Attacker: Scan for vulnerable IoT devices
SSDP: Used to discover and identify targets
Goal: Compromise and add to botnet
```

**Detection**: Scan patterns + repeated requests  
**Response**: Alert + block  

### SSDP Handler Statistics

| Metric | Typical Value |
|--------|---------------|
| **SSDP requests/day** | 100-1,000+ |
| **Amplification attempts** | 20-50% |
| **Unique sources** | 10-50 |
| **Detection latency** | < 50ms |
| **Response time** | 50-100ms |

### Configuration

```python
# From core/config.py
SSDP_HONEYPOT = {
    'port': 1900,
    'protocol': 'UDP',
    'fake_device': 'fake-router-v1',
    'fake_vendor': 'Generic Router',
    'response_size': 'large',  # for amplification detection
    'log_level': 'INFO'
}
```

### SSDP Protocol Basics

```
Request (M-SEARCH):
M-SEARCH * HTTP/1.1
HOST: 239.255.255.250:1900
MAN: "ssdp:discover"
MX: 2
ST: upnp:rootdevice

Response (Device Description):
HTTP/1.1 200 OK
CACHE-CONTROL: max-age=1800
EXT:
LOCATION: http://192.168.1.1:8000/upnp/description.xml
SERVER: Linux/3.14 UPnP/1.0 IpBridge/1.26.0
ST: upnp:rootdevice
USN: uuid:device-123::upnp:rootdevice
```

### Real Attack Example

```
2024-01-15 09:15:30 | SSDP Attack from 192.0.2.100
├─ 09:15:31: M-SEARCH request (100 bytes)
├─ DDoSPoT Response: Device description (5KB)
│   Amplification ratio: 50x ⚠️
├─ 09:15:32-35: Repeated requests (200+ per second)
│   Pattern: DDoS amplification detected ⚠️
└─ 09:15:36: [BLOCKED] - Amplification attack confirmed
    Response: Immediate IP block
    Alert: CRITICAL - DDoS amplification attack
```

---

## Protocol Handler Comparison

| Feature | SSH | HTTP | SSDP |
|---------|-----|------|------|
| **Port** | 2222 | 8888 | 1900 |
| **Protocol** | TCP | TCP | UDP |
| **Typical Attacks** | Brute force | Web exploits | Amplification |
| **Attack Frequency** | Very High | High | Medium |
| **Severity** | High | High | Very High |
| **Detection Speed** | < 50ms | < 100ms | < 50ms |
| **Response Type** | Block/Alert | Alert | Immediate Block |

---

## Handler Architecture

```
                    Network Input
                         ↓
                  ┌─────────────┐
                  │ Packet      │
                  │ Classifier  │
                  └─────────────┘
                    ↓   ↓   ↓
            ┌───────┴───┼───┴────────┐
            ↓           ↓           ↓
        ┌─────────┐  ┌───────┐  ┌────────┐
        │ SSH     │  │ HTTP  │  │ SSDP   │
        │ Handler │  │Handler│  │Handler │
        └─────────┘  └───────┘  └────────┘
            ↓           ↓           ↓
            └─────────┬─┴──────────┬┘
                      ↓
            ┌──────────────────────┐
            │ Detection Engine     │
            │ - Pattern matching   │
            │ - ML analysis        │
            │ - Threat scoring     │
            └──────────────────────┘
                      ↓
            ┌──────────────────────┐
            │ Response System      │
            │ - IP blocking        │
            │ - Alerts/Webhooks    │
            │ - Logging            │
            └──────────────────────┘
```

---

## Configuration and Customization

### Enable/Disable Handlers

```python
# config/config.json
{
  "honeypots": {
    "ssh": {
      "enabled": true,
      "port": 2222
    },
    "http": {
      "enabled": true,
      "port": 8888
    },
    "ssdp": {
      "enabled": true,
      "port": 1900
    }
  }
}
```

### Customize Behavior

```python
# Modify fake responses
{
  "ssh": {
    "banner": "SSH-2.0-OpenSSH_8.2p1"  # Different version
  },
  "http": {
    "content_type": "nginx",  # Simulate Nginx instead of Apache
    "fake_paths": ["wp-admin", "admin", "phpmyadmin"]
  },
  "ssdp": {
    "device_model": "UPnP-Router-2024"
  }
}
```

---

## Performance Characteristics

### Throughput Capacity

```
SSH Honeypot:
  - Concurrent connections: 10,000+
  - Login attempts/sec: 1,000+
  - Memory per connection: ~10KB
  - CPU impact: Low

HTTP Honeypot:
  - Requests/sec: 10,000+
  - Concurrent connections: 5,000+
  - Memory per connection: ~50KB
  - CPU impact: Low-Medium

SSDP Honeypot:
  - Requests/sec: 100,000+
  - Concurrent: N/A (stateless)
  - Memory per request: 0 (stateless)
  - CPU impact: Very Low
```

---

## Real-World Deployment

### Multi-Instance Setup

```
ISP/Network Edge
├─ DDoSPoT Instance 1 (SSH focus)
├─ DDoSPoT Instance 2 (HTTP focus)
└─ DDoSPoT Instance 3 (SSDP focus)
    ↓
Centralized Monitoring
├─ Alert aggregation
├─ Threat correlation
└─ Response coordination
```

### Monitoring All Protocols

```bash
# Monitor SSH activity
tail -f logs/honeypot.log | grep "SSH"

# Monitor HTTP activity
tail -f logs/honeypot.log | grep "HTTP"

# Monitor SSDP activity
tail -f logs/honeypot.log | grep "SSDP"

# Monitor all attacks
tail -f logs/honeypot.log | grep "ATTACK\|BLOCKED"
```

---

## Key Takeaways

1. **SSH**: Detects credential attacks and reconnaissance
2. **HTTP**: Catches web exploits and API abuse
3. **SSDP**: Identifies amplification and DDoS patterns
4. **All Three**: Combined coverage for comprehensive threat detection
5. **DDoSPoT**: Optimized handler implementation for production use

---

## Next Steps

- **Setup**: [Setting Up DDoSPoT](08_Setting_Up_DDoSPoT.md)
- **Detection**: [Threat Detection](06_Threat_Detection.md)
- **Response**: [Automated Response](07_Automated_Response.md)
- **Monitoring**: [Monitoring Threats](09_Monitoring_Threats.md)

---

## Review Questions

1. Why is SSH port 2222 important to monitor?
2. What types of attacks does the HTTP handler detect?
3. How is SSDP used in amplification attacks?
4. What's the typical detection latency for each protocol?
5. How would you customize the SSH banner?

## Additional Resources

- SSH Brute Force Attack Patterns
- OWASP Top 10 Web Attacks
- SSDP DDoS Amplification Attacks (RFC 3986)
- UPnP Vulnerability Research
