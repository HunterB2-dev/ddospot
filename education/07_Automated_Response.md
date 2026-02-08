# Automated Response in DDoSPoT

## Overview

DDoSPoT doesn't just detect threats—it automatically responds to them. This document explains the automated response system, how it works, and how to configure it.

---

## Response Architecture

```
Threat Detected (Score > Threshold)
    ↓
Identify Threat Type
├─ SSH Attack?
├─ HTTP Attack?
└─ SSDP Attack?
    ↓
Execute Response Actions
├─ IP Blocking
├─ Rate Limiting
├─ Notifications
└─ Integration hooks
    ↓
Log & Monitor Response
├─ Response success
├─ Side effects
└─ Effectiveness
```

---

## 1. Automatic IP Blocking

### How It Works

```
Malicious IP Detected
    ↓
Add to Block List
    ↓
Update Firewall Rules
    ↓
Drop all traffic from IP
    ↓
Alert security team
    ↓
Monitor for unblocking event
```

### Blocking Levels

#### Level 1: Application-Level Block
```
DDoSPoT internal block
├─ Blocks at honeypot level
├─ Still visible in logs
├─ Good for analysis
└─ Fast (< 50ms)
```

#### Level 2: Firewall-Level Block
```
Integrated with system firewall
├─ Uses iptables/nftables (Linux)
├─ Uses Windows Firewall (Windows)
├─ Blocks all traffic from IP
└─ System-wide protection
```

#### Level 3: ISP/Network Block
```
Via API integration
├─ Integrates with network equipment
├─ BGP route filtering
├─ Multi-layer protection
└─ Requires API keys
```

### Block Duration

```
Duration Strategies:

Temporary Block:
  Duration: 1 hour to 24 hours
  Use case: Single attack attempts
  Auto-unblock: After duration

Extended Block:
  Duration: 1 week to 30 days
  Use case: Multiple attack patterns
  Manual review required

Permanent Block:
  Duration: Until manual review
  Use case: Known malicious IPs
  Requires security team decision
```

### Configuration

```json
{
  "response": {
    "ip_blocking": {
      "enabled": true,
      "block_duration": 3600,
      "auto_unblock": true,
      "levels": {
        "application": true,
        "firewall": true,
        "network": false
      }
    }
  }
}
```

### Example: SSH Brute Force Response

```
Time: 14:30:00
Event: SSH brute force detected from 203.0.113.45
Threat Score: 0.85 (HIGH)

Action 1: Immediate Application Block
  ├─ Block applied to port 2222
  ├─ Latency: 15ms
  └─ Status: Active

Action 2: Firewall Block (if enabled)
  ├─ Execute: iptables -A INPUT -s 203.0.113.45 -j DROP
  ├─ Latency: 50ms
  └─ Status: Active

Action 3: Monitoring
  ├─ Watch for unblock time: 15:30:00 (1 hour)
  ├─ Monitor for new attacks from this IP
  └─ Log effectiveness

Result: All traffic from 203.0.113.45 blocked
Duration: 1 hour (auto-unblock at 15:30:00)
```

---

## 2. Rate Limiting

### How It Works

```
Request from IP
    ↓
Check request count in time window
    ↓
Under limit? → Allow
Over limit? → Throttle/Block
    ↓
Gradually reduce limit over time
```

### Rate Limit Types

#### Per-IP Rate Limiting
```
Example: 100 requests per minute per IP

IP 192.168.1.1:
├─ Minute 1: 50 requests ✓ (allowed)
├─ Minute 2: 100 requests ✓ (at limit)
├─ Minute 3: 120 requests ✗ (20 requests blocked)
└─ Minute 4: 80 requests ✓ (back under limit)
```

#### Per-Endpoint Rate Limiting
```
Example: /api/users - 50 requests per minute

Total: 150 requests to /api/users
├─ IP 192.168.1.1: 50 requests ✓
├─ IP 192.168.1.2: 50 requests ✓
├─ IP 192.168.1.3: 50 requests ✓
└─ IP 192.168.1.4: All requests ✗ (blocked)
```

#### Adaptive Rate Limiting
```
Initial limit: 100 requests/min
Detected attack: Yes
Action: Reduce limit to 10 requests/min
Gradually increase back to 100 after 1 hour

Timeline:
├─ 00:00 - Attack detected
├─ 00:00-01:00 - Limit: 10 req/min
├─ 01:00-02:00 - Limit: 20 req/min
├─ 02:00-03:00 - Limit: 50 req/min
└─ 03:00+ - Limit: 100 req/min (normal)
```

### Configuration

```json
{
  "response": {
    "rate_limiting": {
      "enabled": true,
      "limits": {
        "ssh": {
          "per_ip": 10,
          "window_seconds": 60
        },
        "http": {
          "per_ip": 100,
          "per_endpoint": 50,
          "window_seconds": 60
        },
        "ssdp": {
          "per_ip": 5,
          "window_seconds": 60
        }
      },
      "adaptive": true,
      "reduce_factor": 0.1
    }
  }
}
```

---

## 3. Alert Notifications

### Notification Channels

#### Email Alerts
```
To: security-team@company.com
Subject: CRITICAL - SSH Brute Force Attack Detected
Body:
  Threat Score: 0.85 (HIGH)
  Source IP: 203.0.113.45
  Attack Type: SSH Brute Force
  Time: 2024-01-15 14:30:00
  Action Taken: IP Blocked for 1 hour
  Details: 15 failed login attempts in 2 minutes
```

#### Webhook Notifications
```
POST https://security-platform.company.com/alerts
{
  "timestamp": "2024-01-15T14:30:00Z",
  "severity": "HIGH",
  "threat_type": "SSH_BRUTE_FORCE",
  "source_ip": "203.0.113.45",
  "threat_score": 0.85,
  "action_taken": "IP_BLOCKED",
  "duration": 3600,
  "details": {
    "protocol": "SSH",
    "port": 2222,
    "attempts": 15,
    "window": 120
  }
}
```

#### Slack Integration
```
[🚨 CRITICAL ALERT]
SSH Brute Force Attack Detected

Source: 203.0.113.45
Severity: HIGH (Score: 0.85)
Attempts: 15 in 2 minutes
Action: IP blocked for 1 hour

#ddospot #security
```

#### PagerDuty Integration
```
Incident: SSH Brute Force Attack
Severity: High
Source: 203.0.113.45
Status: Assigned to on-call engineer
Auto-escalate if not acknowledged in 15 minutes
```

### Configuration

```json
{
  "notifications": {
    "email": {
      "enabled": true,
      "recipients": ["security-team@company.com"],
      "min_severity": "MEDIUM"
    },
    "webhook": {
      "enabled": true,
      "url": "https://your-platform.com/alerts",
      "min_severity": "MEDIUM"
    },
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/...",
      "channel": "#security-alerts",
      "min_severity": "HIGH"
    },
    "pagerduty": {
      "enabled": true,
      "api_key": "your-pagerduty-key",
      "min_severity": "CRITICAL"
    }
  }
}
```

---

## 4. Custom Response Rules

### Rule Structure

```
Rule Definition:
  Condition: (Threat Type AND Threat Score > X)
  Then: Execute Action(s)

Example:
  IF: SSH_ATTACK AND Threat_Score > 0.8
  AND: Attempts > 5
  THEN:
    1. Block IP for 1 day
    2. Send critical alert
    3. Add to watchlist
```

### Example Rules

#### Rule 1: Aggressive SSH Attack
```json
{
  "name": "Aggressive SSH Attack Response",
  "condition": {
    "threat_type": "SSH_BRUTE_FORCE",
    "threat_score": "> 0.8",
    "attempts": "> 5",
    "time_window": "< 5 minutes"
  },
  "actions": [
    {
      "type": "block_ip",
      "duration": 86400,
      "scope": "firewall"
    },
    {
      "type": "notify",
      "channels": ["email", "slack", "pagerduty"],
      "severity": "CRITICAL"
    },
    {
      "type": "add_to_list",
      "list_name": "suspicious_ips",
      "ttl": 604800
    }
  ]
}
```

#### Rule 2: SQL Injection Attack
```json
{
  "name": "SQL Injection Response",
  "condition": {
    "threat_type": "SQL_INJECTION",
    "threat_score": "> 0.7"
  },
  "actions": [
    {
      "type": "rate_limit",
      "requests_per_minute": 5,
      "duration": 3600
    },
    {
      "type": "notify",
      "channels": ["webhook"],
      "severity": "HIGH"
    },
    {
      "type": "log_detailed",
      "include_payload": true
    }
  ]
}
```

#### Rule 3: DDoS Amplification Attack
```json
{
  "name": "SSDP DDoS Amplification Response",
  "condition": {
    "threat_type": "SSDP_AMPLIFICATION",
    "threat_score": "> 0.9"
  },
  "actions": [
    {
      "type": "block_ip",
      "duration": 604800,
      "scope": "network_level"
    },
    {
      "type": "notify",
      "channels": ["email", "slack", "pagerduty"],
      "severity": "CRITICAL"
    },
    {
      "type": "report_to_isp",
      "enable": true
    }
  ]
}
```

### Response Actions Available

```
Available Actions:

├─ IP Actions
│  ├─ block_ip (temporary or permanent)
│  ├─ rate_limit
│  ├─ add_to_list (whitelist/blacklist)
│  └─ remove_from_list
│
├─ Alert Actions
│  ├─ notify (email, webhook, slack, etc.)
│  ├─ escalate (PagerDuty, Opsgenie)
│  └─ log_detailed
│
├─ Network Actions
│  ├─ drop_packets
│  ├─ redirect_to_honeypot
│  └─ limit_bandwidth
│
├─ Integration Actions
│  ├─ create_ticket (Jira, Azure Devops)
│  ├─ report_to_isp
│  └─ share_intelligence
│
└─ Data Collection Actions
   ├─ capture_traffic
   ├─ log_full_request
   └─ store_for_analysis
```

---

## 5. Response Workflow Examples

### Example 1: SSH Brute Force Response

```
Timeline: Real-world SSH attack

14:30:00
  Event: Connection from 203.0.113.45:52345 → localhost:2222
  Action: Accept connection, log details

14:30:01
  Event: SSH login attempt: root/password
  Status: FAILED ❌
  Action: Log attempt

14:30:02
  Event: SSH login attempt: root/12345
  Status: FAILED ❌
  Action: Log attempt

14:30:03
  Event: SSH login attempt: admin/admin
  Status: FAILED ❌
  Action: Log attempt, check threat level

14:30:04
  Analysis:
  ├─ Signature Match: SSH Brute Force (0.8)
  ├─ Anomaly: 3 attempts in 4 seconds (0.8)
  ├─ ML Score: 0.88 malicious
  ├─ IP Reputation: 0.5 risky
  └─ Threat Score: 0.786 (HIGH)

14:30:05
  Action: IP Block
  ├─ Block at application level (immediate)
  ├─ Update firewall (if enabled)
  └─ Set block duration: 1 hour

14:30:06
  Notification: Email to security team
  Subject: "HIGH - SSH Brute Force Attack from 203.0.113.45"
  
14:30:07
  Notification: Slack message to #security-alerts
  
14:30:08
  Database: Log incident
  ├─ ID: INCIDENT-2024-001234
  ├─ Status: ACTIVE
  ├─ Action: IP Blocked
  └─ Unblock time: 15:30:05

15:30:05
  Auto-unblock: IP 203.0.113.45 removed from block list
  Monitoring: No new attacks detected
  Status: Closed - Attack responded successfully
```

### Example 2: SQL Injection Attack Response

```
Timeline: SQL Injection attempt

10:45:23
  Event: HTTP request from 198.51.100.42
  URL: /api/users?id=1' OR '1'='1
  Content: SQL keywords detected (OR, UNION, SELECT)

10:45:24
  Analysis:
  ├─ Signature Match: SQL Injection (0.95)
  ├─ Anomaly: Unusual characters (0.7)
  ├─ ML Score: 0.92 attack
  └─ Threat Score: 0.866 (HIGH)

10:45:25
  Action: Rate Limiting
  ├─ Limit for IP: 5 req/min
  ├─ Duration: 1 hour
  └─ Enforce at application level

10:45:26
  Notification: Webhook to SIEM
  {
    "alert_id": "ALT-2024-005678",
    "threat_type": "SQL_INJECTION",
    "severity": "HIGH",
    "source_ip": "198.51.100.42",
    "url": "/api/users?id=1' OR '1'='1"
  }

10:45:27
  Logging: Detailed request logged
  ├─ Full headers
  ├─ Full payload
  ├─ Response sent
  └─ Timestamp: 10:45:23 UTC

10:46:00
  Follow-up: Rate limiting in effect
  ├─ Normal request from attacker IP: BLOCKED
  ├─ Message: Rate limit exceeded
  ├─ Requests: 5/5 remaining
  └─ Reset in: 55 minutes

11:45:00
  Status: Auto-reset
  ├─ Rate limit removed
  ├─ IP can make normal requests again
  ├─ Incident logged
  └─ Analysis available in dashboard
```

---

## 6. Response Effectiveness Monitoring

### Metrics Tracked

```
Block Effectiveness:
├─ Attacks blocked: 98.5%
├─ Block success rate: 99.9%
└─ False positives: 0.8%

Response Time:
├─ Detection to action: < 100ms
├─ IP block latency: 15-50ms
└─ Notification delivery: 100-500ms

Block Coverage:
├─ Application level: 100%
├─ Firewall level: 98%
├─ Network level: 60% (if configured)
```

### Dashboard View

```
Response Status Dashboard:

Active Blocks:
├─ Total IPs blocked: 1,247
├─ SSH: 523 (42%)
├─ HTTP: 614 (49%)
├─ SSDP: 110 (9%)
└─ Temporary: 1,200 / Permanent: 47

Block Effectiveness (24h):
├─ Attacks prevented: 45,230
├─ Avg response time: 47ms
├─ Block success: 99.8%
└─ False positive rate: 0.7%

Response Actions (24h):
├─ IP blocks: 1,200
├─ Rate limits: 340
├─ Alerts sent: 2,150
└─ Incidents created: 12
```

---

## Configuration Example

### Complete Response Configuration

```json
{
  "response_system": {
    "enabled": true,
    "auto_respond": true,
    "ip_blocking": {
      "enabled": true,
      "block_duration": 3600,
      "levels": ["application", "firewall"],
      "auto_unblock": true
    },
    "rate_limiting": {
      "enabled": true,
      "adaptive": true,
      "ssh": {
        "per_ip": 10,
        "window": 60
      },
      "http": {
        "per_ip": 100,
        "window": 60
      },
      "ssdp": {
        "per_ip": 5,
        "window": 60
      }
    },
    "notifications": {
      "email": {
        "enabled": true,
        "recipients": ["security@company.com"],
        "min_severity": "HIGH"
      },
      "slack": {
        "enabled": true,
        "webhook": "https://hooks.slack.com/...",
        "min_severity": "HIGH"
      },
      "webhook": {
        "enabled": true,
        "url": "https://siem.company.com/alerts",
        "min_severity": "MEDIUM"
      }
    },
    "custom_rules": [
      {
        "name": "Aggressive Attack",
        "condition": "threat_score > 0.8 AND attempts > 5",
        "actions": ["block_ip", "notify_critical", "escalate"]
      }
    ]
  }
}
```

---

## Key Takeaways

1. **Automatic**: Responses trigger instantly (< 100ms)
2. **Multi-level**: IP blocking at app/firewall/network
3. **Flexible**: Rate limiting and custom rules
4. **Alert-driven**: Multiple notification channels
5. **Effective**: 99.8% success rate in practice

---

## Next Steps

- **Setup**: [Setting Up DDoSPoT](08_Setting_Up_DDoSPoT.md)
- **Monitoring**: [Monitoring Threats](09_Monitoring_Threats.md)
- **Configuration**: [Configuration Management](10_Configuration_Management.md)
- **Incidents**: [Incident Response](15_Incident_Response.md)

---

## Review Questions

1. What are the three levels of IP blocking?
2. How does adaptive rate limiting work?
3. What notification channels are available?
4. How would you create a custom response rule?
5. What metrics indicate response effectiveness?

## Additional Resources

- Incident Response Best Practices
- Network Firewall Configuration
- Alert Management Systems
- SOAR Platform Integration
