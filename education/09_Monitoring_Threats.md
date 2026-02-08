# Monitoring Threats in DDoSPoT Dashboard

## Dashboard Overview

The DDoSPoT dashboard provides real-time visibility into honeypot activity, detected threats, and automated responses.

```
┌─────────────────────────────────────────────────┐
│            DDoSPoT Dashboard                    │
├─────────────────────────────────────────────────┤
│  Home | Dashboard | Alerts | Configuration    │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │         System Status                   │  │
│  │  SSH: Running    HTTP: Running          │  │
│  │  SSDP: Running   Database: OK           │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐          │
│  │ Connections │  │ Threats      │          │
│  │ 1,234        │  │ 156 (Today)  │          │
│  └──────────────┘  └──────────────┘          │
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │      Recent Attacks                     │  │
│  │  [Attack logs and details]              │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Dashboard Components

### 1. System Status Panel

Shows health and status of all honeypot services.

```
System Status

Honeypots:
  ┌─ SSH (Port 2222)
  │  ├─ Status: Running ✅
  │  ├─ Uptime: 15 days 3 hours
  │  └─ Connections (24h): 1,234
  │
  ├─ HTTP (Port 8888)
  │  ├─ Status: Running ✅
  │  ├─ Uptime: 15 days 3 hours
  │  └─ Connections (24h): 856
  │
  └─ SSDP (Port 1900)
     ├─ Status: Running ✅
     ├─ Uptime: 15 days 3 hours
     └─ Connections (24h): 421

Database:
  ├─ Status: Healthy ✅
  ├─ Size: 1.2 GB
  ├─ Records: 45,230
  └─ Last Backup: 2 hours ago

Detection Engine:
  ├─ Status: Running ✅
  ├─ Accuracy: 99.2%
  └─ Average Latency: 47ms
```

### 2. Statistics Dashboard

Real-time statistics about attacks and traffic.

```
Statistics (Last 24 Hours)

Total Connections: 2,511
├─ SSH: 1,234 (49%)
├─ HTTP: 856 (34%)
└─ SSDP: 421 (17%)

Total Threats Detected: 156
├─ High Severity: 23
├─ Medium Severity: 67
└─ Low Severity: 66

Attack Types:
├─ SSH Brute Force: 45
├─ SQL Injection: 23
├─ Path Traversal: 18
├─ DDoS Amplification: 12
├─ Scanner Probes: 34
└─ Other: 24

Geographic Distribution:
├─ China: 42 attacks
├─ Russia: 28 attacks
├─ United States: 22 attacks
├─ India: 15 attacks
└─ Other: 49 attacks

Response Metrics:
├─ IPs Blocked: 89
├─ Average Response Time: 47ms
└─ Success Rate: 99.8%
```

### 3. Real-Time Activity Feed

Live log of attack attempts and responses.

```
Real-Time Activity Log

[14:30:45] ⚠️  HIGH - SSH Brute Force
  Source: 203.0.113.45
  Attempts: 15 in 2 minutes
  Action: IP Blocked for 1 hour
  Threat Score: 0.85

[14:29:12] 🔴 CRITICAL - SQL Injection
  Source: 198.51.100.42
  URL: /api/users?id=1' OR '1'='1
  Action: Rate Limited to 5 req/min
  Threat Score: 0.92

[14:28:33] ⚠️  HIGH - Scanner Probe
  Source: 192.0.2.100
  Type: Nikto Web Scanner
  Action: Logged
  Threat Score: 0.68

[14:27:15] ℹ️  LOW - SSH Connection Attempt
  Source: 10.0.0.50
  User: admin
  Password: admin123
  Action: Logged
  Threat Score: 0.22
```

### 4. Geographic Heat Map

Visual representation of attack origins.

```
Attack Heat Map - Last 24 Hours

    [Darker = More Attacks]

    North America
      Canada: 2 attacks
      USA: 22 attacks ███████
      Mexico: 1 attack

    Europe
      UK: 8 attacks ██
      Germany: 5 attacks █
      Russia: 28 attacks ██████████
      
    Asia
      China: 42 attacks ███████████████
      India: 15 attacks █████
      Japan: 3 attacks
      
    Other
      Brazil: 4 attacks
      Australia: 2 attacks
```

### 5. Threat Timeline

Threat activity over time.

```
Threat Timeline - Last 7 Days

Threats per Hour:
│
30  │     ╱╲       ╱╲    
    │    ╱  ╲     ╱  ╲   
20  │   ╱    ╲   ╱    ╲  
    │  ╱      ╲ ╱      ╲ 
10  │ ╱        ╲        ╲ 
    │╱__________╲________╲ 
 0  └─────────────────────
    Mon Tue Wed Thu Fri Sat Sun

Peak Times:
├─ Peak Hour: 02:00 UTC (12 threats/min)
├─ Quiet Hour: 09:00 UTC (1 threat/min)
└─ Average: 4 threats/min
```

---

## Using the Dashboard

### Accessing the Dashboard

```bash
# Open in browser
http://localhost:5000

# On remote machine
http://your-ip:5000

# With authentication (if enabled)
Username: admin
Password: [configured password]
```

### Dashboard Sections

#### Home Tab
- Quick overview of system status
- Key metrics at a glance
- Recent alerts summary
- Quick action buttons

#### Monitoring Tab
- Real-time threat feed
- Active sessions
- Current attacks
- System health metrics

#### Alerts Tab
- Detailed alert history
- Alert acknowledgment
- Alert filtering
- Alert trend analysis

#### Configuration Tab
- Honeypot settings
- Alert configuration
- Response rules
- User management

#### Reports Tab
- Daily/weekly/monthly reports
- Attack statistics
- Trend analysis
- Compliance reports

---

## Interpreting Attack Data

### SSH Attack Example

```
Alert Details:

Source IP: 203.0.113.45
Country: China
ISP: Alibaba Cloud
Port: 2222 (SSH)
Protocol: SSH
Timestamp: 2024-01-15 14:30:00 UTC

Attack Details:
├─ Attack Type: Brute Force
├─ Attempts: 15
├─ Time Window: 120 seconds
├─ Success Rate: 0%
├─ Usernames Tried: root, admin, test
├─ Passwords Tried: password, 123456, admin
└─ Threat Score: 0.85 (HIGH)

Response:
├─ Action Taken: IP Blocked
├─ Duration: 3600 seconds (1 hour)
├─ Block Level: Application + Firewall
├─ Notification: Sent to security@company.com
└─ Status: Active

Recommendation:
├─ Monitor for unblock time
├─ Check for other attacks from this IP
└─ Add to permanent blocklist if repeated
```

### SQL Injection Example

```
Alert Details:

Source IP: 198.51.100.42
Country: United States
ISP: Example ISP
Port: 8888 (HTTP)
Protocol: HTTP/HTTPS
Timestamp: 2024-01-15 14:30:23 UTC

Attack Details:
├─ Attack Type: SQL Injection
├─ Target URL: /api/users?id=1' OR '1'='1
├─ Method: GET
├─ Payload: 1' OR '1'='1
├─ Signature Match: SQL Injection (95% confidence)
└─ Threat Score: 0.92 (CRITICAL)

Response:
├─ Action Taken: Rate Limited
├─ New Limit: 5 requests/minute
├─ Duration: 3600 seconds (1 hour)
├─ Notification: Sent to SIEM
└─ Status: Active

Recommendation:
├─ Investigate if attacker targeted database
├─ Check for similar patterns from other IPs
├─ Review Web Application Firewall logs
└─ Consider IP reputation checking
```

### DDoS/Scanner Example

```
Alert Details:

Source IP: 192.0.2.100
Country: Unknown (VPN/Proxy)
Port: 1900 (SSDP)
Protocol: UDP
Timestamp: 2024-01-15 14:31:05 UTC

Attack Details:
├─ Attack Type: SSDP Discovery Scan
├─ Requests: 100+ in 10 seconds
├─ Response Size: 5KB each (amplification)
├─ Scan Pattern: Random device searches
├─ Threat Score: 0.78 (HIGH)

Analysis:
├─ Fingerprint: nmap SSDP scan
├─ Likely Intent: Device discovery
├─ IoT Botnet Risk: Moderate
└─ DDoS Amplification: Yes

Response:
├─ Action Taken: IP Blocked
├─ Duration: 86400 seconds (1 day)
├─ Block Level: Network + Firewall
├─ Notification: Critical alert sent
└─ Status: Active

Recommendation:
├─ Check for botnet activity
├─ Monitor for other commands from this IP
├─ Consider reporting to ISP
└─ Add to external threat intelligence feed
```

---

## Key Metrics Explained

### Threat Score (0.0 - 1.0)
```
0.0 - 0.3: Normal Traffic (Green)
  └─ No action needed
  
0.3 - 0.5: Low Risk (Yellow)
  └─ Monitor, log for review
  
0.5 - 0.7: Medium Risk (Orange)
  └─ Rate limit or alert
  
0.7 - 0.9: High Risk (Red)
  └─ Block or rate limit
  
0.9 - 1.0: Critical (Dark Red)
  └─ Immediate block
```

### False Positive Rate

```
Industry Standard: 1-5%
DDoSPoT Performance: 0.8%
├─ Meaning: Only 0.8 out of 100 alerts are false
├─ Impact: High confidence in alerts
└─ Action: Most alerts are real threats
```

### Detection Latency

```
Time from Attack to Alert: < 100ms
├─ Capture: 1ms
├─ Detection: 47ms
├─ Alert: < 52ms
└─ Response: < 100ms total
```

### Coverage

```
SSH Honeypot: Monitors SSH attacks
├─ Brute force ✓
├─ Credential stuffing ✓
├─ Scanner probes ✓
└─ Version detection ✓

HTTP Honeypot: Monitors web attacks
├─ SQL injection ✓
├─ Path traversal ✓
├─ XSS attempts ✓
└─ File upload ✓

SSDP Honeypot: Monitors IoT/DDoS
├─ Amplification ✓
├─ Device discovery ✓
├─ Botnet recruitment ✓
└─ Network mapping ✓
```

---

## Common Dashboard Tasks

### Task 1: Check Today's Attacks

```
1. Click "Dashboard" tab
2. Look at "Statistics (24h)" panel
3. Review "Recent Attacks" section
4. Click on attack for details
5. Check "Response" status
```

### Task 2: Find Attacks from Specific Country

```
1. Click "Monitor" tab
2. Scroll to "Activity Feed"
3. Use filter by "Country"
4. Select country (e.g., "China")
5. Review matching attacks
```

### Task 3: Identify Top Attackers

```
1. Click "Reports" tab
2. Select "Daily Report"
3. Look for "Top Source IPs" section
4. Click on IP for details
5. View attack history
```

### Task 4: Verify IP Block

```
1. Find threat in activity log
2. Check "Response" shows "IP Blocked"
3. Click "Blocked IPs" section
4. Search for IP address
5. Verify status is "Active"
```

### Task 5: Test Alert Notification

```
1. Click "Configuration" tab
2. Click "Alert Settings"
3. Find notification channel
4. Click "Send Test Alert"
5. Verify notification received
```

---

## Dashboard Customization

### Create Custom View

```
1. Click "Dashboard" tab
2. Click "Customize"
3. Add widgets:
   ├─ System Status
   ├─ Threat Timeline
   ├─ Geographic Heat Map
   ├─ Attack Type Distribution
   └─ Top Attackers
4. Arrange as needed
5. Save layout
```

### Set Alert Thresholds

```
Configuration → Alerts → Thresholds

├─ High Severity Threshold: 0.7
├─ Medium Severity Threshold: 0.5
├─ Low Severity Threshold: 0.3
├─ SSH Attack Threshold: 0.6
├─ HTTP Attack Threshold: 0.7
└─ SSDP Attack Threshold: 0.8
```

### Configure Notifications

```
Configuration → Alerts → Notifications

Email:
├─ Enable: ✓
├─ Recipients: security@company.com
├─ Min Severity: HIGH
└─ Summary: Daily

Slack:
├─ Enable: ✓
├─ Channel: #security-alerts
├─ Min Severity: HIGH
└─ Format: Detailed

Webhook:
├─ Enable: ✓
├─ URL: https://your-siem.com/alerts
├─ Min Severity: MEDIUM
└─ Auth: API Key
```

---

## Performance Monitoring

### System Resources

```
Dashboard → System → Resources

CPU Usage:
├─ Current: 12%
├─ 24h Average: 15%
├─ 24h Peak: 45%
└─ Health: ✓ Good

Memory Usage:
├─ Current: 512 MB
├─ Limit: 2 GB
├─ Usage: 25%
└─ Health: ✓ Good

Disk Usage:
├─ Database: 1.2 GB
├─ Logs: 300 MB
├─ Total: 1.5 GB
└─ Health: ✓ Good

Network:
├─ Incoming: 2.3 Mbps
├─ Outgoing: 0.8 Mbps
├─ Connections: 1,234
└─ Health: ✓ Good
```

### Database Performance

```
Dashboard → Database → Performance

Queries/sec: 1,200
├─ Reads: 900
├─ Writes: 300
└─ Performance: ✓ Excellent

Database Size:
├─ Current: 1.2 GB
├─ Growth/day: 50 MB
├─ Estimated Full: 60 days
└─ Action: Plan backup/archive

Last Backup:
├─ Time: 2 hours ago
├─ Status: ✓ Success
├─ Size: 1.2 GB
└─ Duration: 5 minutes
```

---

## Troubleshooting Dashboard

### Issue: Dashboard Won't Load

```
Solution:
1. Check if service is running:
   systemctl status ddospot-dashboard.service
   
2. Check port 5000:
   sudo netstat -tulpn | grep 5000
   
3. View logs:
   tail -f logs/dashboard.log
   
4. Restart service:
   systemctl restart ddospot-dashboard.service
```

### Issue: Slow Dashboard Performance

```
Solution:
1. Check system resources:
   top
   
2. Check database size:
   du -sh ddospot.db
   
3. Archive old data:
   python scripts/archive-data.py --days 90
   
4. Optimize database:
   sqlite3 ddospot.db "VACUUM;"
```

### Issue: Missing Data in Graphs

```
Solution:
1. Check honeypot is running:
   systemctl status ddospot-honeypot.service
   
2. Check database:
   sqlite3 ddospot.db "SELECT COUNT(*) FROM logs;"
   
3. Check disk space:
   df -h
   
4. Review logs for errors:
   tail -f logs/honeypot.log
```

---

## Key Takeaways

1. **Real-time Monitoring**: See attacks as they happen
2. **Rich Analytics**: Understand attack patterns
3. **Quick Response**: Identify and block threats fast
4. **Customizable**: Configure for your needs
5. **User-Friendly**: Intuitive interface for all skill levels

---

## Next Steps

- **Configuration**: [Configuration Management](10_Configuration_Management.md)
- **Setup Guide**: [Setting Up DDoSPoT](08_Setting_Up_DDoSPoT.md)
- **Alerts**: [Alert Configuration](10_Configuration_Management.md)
- **Reports**: [Understanding Reports](09_Monitoring_Threats.md#reports)

---

## Review Questions

1. What are the main dashboard tabs?
2. How do you interpret a threat score of 0.85?
3. What information is shown in the activity feed?
4. How can you filter attacks by country?
5. What does a 0.8% false positive rate mean?

## Additional Resources

- [Configuration Management](10_Configuration_Management.md)
- [Alert Configuration](../docs/API_DOCUMENTATION.md)
- [Dashboard Quick Start](../docs/DASHBOARD_QUICK_START.md)
- [Mobile Dashboard](20_Mobile_Dashboard.md)
