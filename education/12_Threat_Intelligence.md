# Threat Intelligence in DDoSPoT

## Overview

Threat Intelligence (TI) enriches attack data with external context, helping understand threats better and respond more effectively.

---

## TI Components

### 1. Geolocation Analysis

**Purpose**: Understand attack origins and patterns

```
IP Address: 203.0.113.45
    ↓
GeoIP Database Lookup
    ↓
Results:
├─ Country: China
├─ Region: Jiangsu
├─ City: Nanjing
├─ Latitude: 32.0603°N
├─ Longitude: 118.7969°E
├─ ISP: Alibaba Cloud
├─ ASN: AS37963
├─ Data Center: Yes
├─ Proxy: No
└─ Threat Level: Medium
```

### 2. IP Reputation

**Purpose**: Score based on historical behavior

```
IP Reputation Score: 45/100 (Medium Risk)

Reputation Factors:
├─ Previous attacks: 23
├─ Days since last attack: 5
├─ Blocklist entries: 3
│  ├─ AbuseIPDB: 25 reports
│  ├─ Spamhaus: Listed
│  └─ Project Honey Pot: 150 attacks
├─ Abuse reports: 12
├─ Scan activity: High
├─ Malware C&C: No
├─ Open ports: 5
├─ Services running: Web, SSH
└─ Vulnerability: None known
```

### 3. WHOIS Information

**Purpose**: Identify owner and contact

```
Querying: 203.0.113.45

Results:
├─ Organization: Example Cloud Services
├─ Country: China
├─ Abuse Email: abuse@example-cloud.com
├─ Tech Contact: tech@example-cloud.com
├─ Registration Date: 2015-03-20
├─ Last Updated: 2023-01-15
├─ CIDR Block: 203.0.113.0/24
├─ Block Size: 256 IPs
└─ Block Type: Datacenter
```

### 4. Threat Feed Integration

**Purpose**: Aggregate threat data from multiple sources

```
Threat Intelligence Feeds:

AbuseIPDB:
├─ Data: IP reputation scores
├─ Update: Hourly
├─ Coverage: 1M+ IPs
└─ Confidence: High

Spamhaus:
├─ Data: Botnet C&C, spam sources
├─ Update: Real-time
├─ Coverage: 10k+ IPs
└─ Confidence: Very High

Project Honey Pot:
├─ Data: Attacker activity
├─ Update: Real-time
├─ Coverage: 5M+ attacks
└─ Confidence: High

AlienVault OTX:
├─ Data: Community threat intel
├─ Update: Continuous
├─ Coverage: Varies
└─ Confidence: Medium

GreyNoise:
├─ Data: Internet scanner activity
├─ Update: Real-time
├─ Coverage: Internet scanners
└─ Confidence: High
```

### 5. Threat Scoring

**Purpose**: Combine TI data into risk score

```
Final Threat Score Calculation:

Score = 
  (Signature_Match × 0.35) +
  (Anomaly_Score × 0.25) +
  (ML_Confidence × 0.20) +
  (IP_Reputation × 0.10) +
  (TI_Factors × 0.10)

TI Factors Include:
├─ Geolocation (military/high-risk country)
├─ Blocklist status (multiple lists)
├─ Historical behavior (previous attacks)
├─ ASN reputation (ISP blocklisted)
├─ Malware associated (C&C links)
└─ Scan/bot activity (known scanner)

Example:
├─ Signature Match: 0.8
├─ Anomaly: 0.7
├─ ML: 0.85
├─ IP Reputation: 0.6
├─ TI Factors: 0.75
└─ Score: (0.8×0.35) + (0.7×0.25) + (0.85×0.20) + (0.6×0.10) + (0.75×0.10) = 0.745 (HIGH)
```

---

## Geolocation Features

### Geographic Risk Assessment

```
Risk by Country:

Very High Risk (Risk Level 4):
├─ Countries with high hacker activity
├─ Difficult legal jurisdiction
├─ Known botnet origins
└─ Examples: North Korea, Iran, Syria

High Risk (Risk Level 3):
├─ High hacker activity
├─ Limited law enforcement cooperation
├─ Examples: China, Russia

Medium Risk (Risk Level 2):
├─ Moderate hacker activity
├─ Variable law enforcement
├─ Examples: Eastern Europe, India

Low Risk (Risk Level 1):
├─ Low hacker activity
├─ Strong law enforcement
├─ Examples: US, Canada, Western Europe
```

### Distance-Based Risk

```
Velocity Check: Is the geography plausible?

Scenario 1:
├─ First request: USA (San Francisco)
├─ Second request 1 second later: China (Beijing)
├─ Distance: 8,000 miles in 1 second
├─ Possible: No (satellite speed only)
├─ Risk: Very High (likely compromised account or proxy)

Scenario 2:
├─ First request: USA (San Francisco)
├─ Second request 12 hours later: UK (London)
├─ Distance: 5,000 miles in 43,200 seconds
├─ Possible: Yes (slow airplane travel)
├─ Risk: Low (legitimate travel)

Scenario 3:
├─ All requests: China
├─ Consistent IP range: Same ISP
├─ No velocity anomalies: No
├─ Risk: Normal for region
```

### GeoIP Database

```
Configuration:

{
  "threat_intelligence": {
    "geolocation": {
      "enabled": true,
      "database": "/var/lib/ddospot/GeoIP2-City.mmdb",
      "update_frequency": "monthly",
      "cache_size": 10000,
      "risk_levels": {
        "4": ["KP", "IR", "SY", "CU"],
        "3": ["CN", "RU"],
        "2": ["RO", "PK", "IN"],
        "1": ["US", "CA", "GB", "DE"]
      }
    }
  }
}
```

---

## IP Reputation Scoring

### Reputation Data Sources

```
Integrations:

AbuseIPDB API:
├─ Endpoint: https://api.abuseipdb.com/api/v2/check
├─ Rate Limit: 5k/day (free), unlimited (paid)
├─ Response Time: 200-500ms
└─ Confidence: 95%+ (community reported)

Spamhaus API:
├─ Endpoint: Varies by service
├─ Rate Limit: Real-time
├─ Response Time: < 100ms
└─ Confidence: 99%+ (curated)

ProjectHoneypot API:
├─ Endpoint: http://www.projecthoneypot.org/search_ip.php
├─ Rate Limit: Real-time
├─ Response Time: 200ms
└─ Confidence: 98%+
```

### Scoring Algorithm

```python
def calculate_reputation_score(ip):
    """
    Calculate IP reputation score 0-100
    Higher = more suspicious
    """
    score = 0
    
    # Factor 1: Historical attacks (0-30 points)
    attacks_30days = count_attacks(ip, days=30)
    score += min(attacks_30days * 1.5, 30)
    
    # Factor 2: Blocklist status (0-40 points)
    blocklist_count = count_blocklists(ip)
    score += min(blocklist_count * 10, 40)
    
    # Factor 3: ASN reputation (0-20 points)
    asn_reputation = check_asn_reputation(ip)
    score += asn_reputation * 20
    
    # Factor 4: Malware association (0-10 points)
    if is_malware_c2(ip):
        score += 10
    
    # Factor 5: Datacenter/Proxy (0-10 points)
    if is_datacenter(ip) or is_proxy(ip):
        score += 5  # Less suspicious (clearer attribution)
    
    return min(score, 100)
```

### Reputation Tiers

```
Score 80-100: Very High Risk (Red)
├─ Action: Immediate permanent block
├─ Examples: Known C&C, recent major attacks
└─ Example IPs: Botnet command centers

Score 60-79: High Risk (Orange)
├─ Action: Temporary block + monitoring
├─ Examples: Multiple blocklists, frequent attacks
└─ Block Duration: 24-72 hours

Score 40-59: Medium Risk (Yellow)
├─ Action: Rate limiting + alerts
├─ Examples: Some suspicious activity
└─ Monitor Duration: 7 days

Score 20-39: Low Risk (Light Yellow)
├─ Action: Log + monitoring
├─ Examples: Occasional anomalies
└─ Monitor Duration: 30 days

Score 0-19: Very Low Risk (Green)
├─ Action: None (normal traffic)
├─ Examples: Known good actors
└─ Whitelist handling: Preferred
```

---

## Threat Feed Management

### Updating Feeds

```
Feed Update Schedule:

Real-time Feeds (every minute):
├─ Project Honey Pot
├─ Emerging Threats
└─ Custom feeds

Hourly Feeds (every hour):
├─ AbuseIPDB
├─ AlienVault OTX
└─ Shodan data

Daily Feeds (every 24 hours):
├─ Spamhaus DROP list
├─ OSINT community feeds
└─ Custom intelligence

Weekly Feeds (every 7 days):
├─ Full GeoIP database
├─ Comprehensive vulnerability databases
└─ Archive and analysis

Configuration:
{
  "threat_feeds": {
    "abuseipdb": {
      "enabled": true,
      "update_interval": 3600,
      "api_key": "your-key",
      "confidence_min": 25
    },
    "spamhaus": {
      "enabled": true,
      "update_interval": 86400,
      "lists": ["drop", "edrop"]
    }
  }
}
```

### Custom Feed Integration

```python
# Add custom threat intelligence feed

class CustomTIFeed:
    def __init__(self):
        self.url = "https://your-org.com/threat-feed.json"
        self.api_key = "secret-key"
    
    def fetch_feed(self):
        """Fetch latest threat data"""
        response = requests.get(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def process_feed(self, feed_data):
        """Process feed into DDoSPoT format"""
        for entry in feed_data['threats']:
            ip = entry['ip']
            severity = entry['severity']
            category = entry['type']
            
            # Store in TI database
            store_threat_intelligence(ip, {
                'source': 'custom',
                'severity': severity,
                'category': category,
                'timestamp': datetime.now()
            })

# Register feed
ti_manager.register_feed(CustomTIFeed())
```

---

## Integration with Detection

### TI-Enhanced Detection

```
Attack Detection Flow with TI:

1. Attack detected
2. Signature/ML/Anomaly analysis
3. Generate initial threat score: 0.75
4. Query threat intelligence:
   ├─ IP reputation: 0.65
   ├─ Geolocation risk: 0.50
   ├─ Blocklist status: 0.80
   └─ Historical activity: 0.70
5. Adjust final score:
   ├─ Average TI score: 0.66
   ├─ Combined with detection: 0.75
   └─ Final: 0.78 (HIGH)
6. Generate higher-confidence alert
```

### Context-Aware Responses

```
Same attack signature:
Different reputation = Different response

SQL Injection from IP with:
├─ Score < 30: Log only (likely development)
├─ Score 30-60: Rate limit (moderate risk)
├─ Score 60-80: Block 1 hour (suspicious)
└─ Score > 80: Block 24h + escalate (malicious)
```

---

## Incident Investigation

### TI for Forensics

```
Question: Where did this attack come from?

Investigation:
1. Get attacker IP: 203.0.113.45
2. Query geolocation: China, Jiangsu, Nanjing
3. Query WHOIS: Alibaba Cloud Services
4. Check reputation: 75/100 (High Risk)
5. Check blocklists:
   ├─ AbuseIPDB: 23 reports
   ├─ Spamhaus: Listed
   └─ Project Honey Pot: 150 attacks
6. Historical activity:
   ├─ First seen: 6 months ago
   ├─ Attacks: 45 total
   ├─ Attack types: SSH, HTTP, SSDP
   └─ Targets: Your company only
7. Correlate:
   ├─ Same ASN: 5 other IPs attacking
   ├─ Same pattern: Coordinated campaign
   ├─ Timing: Daily 02:00 UTC
   └─ Conclusion: Organized botnet

Recommendation:
├─ Block entire ASN (if policy allows)
├─ Report to Alibaba Cloud abuse team
├─ Share intel with threat community
└─ Expect continued attempts
```

---

## Configuration Example

```json
{
  "threat_intelligence": {
    "enabled": true,
    
    "geolocation": {
      "enabled": true,
      "database": "/var/lib/ddospot/GeoIP2-City.mmdb",
      "update_frequency": "monthly",
      "country_risk_levels": {
        "4": ["KP", "IR"],
        "3": ["CN", "RU"],
        "2": ["PK", "IN"],
        "1": ["US", "GB", "CA"]
      },
      "distance_check": true,
      "max_velocity_kmh": 900
    },
    
    "ip_reputation": {
      "enabled": true,
      "cache_size": 100000,
      "cache_ttl": 3600,
      "score_threshold": 30
    },
    
    "feeds": {
      "abuseipdb": {
        "enabled": true,
        "api_key": "your-api-key",
        "update_interval": 3600,
        "confidence_threshold": 25
      },
      "spamhaus": {
        "enabled": true,
        "update_interval": 86400
      },
      "project_honeypot": {
        "enabled": true,
        "api_key": "your-api-key",
        "update_interval": 3600
      }
    },
    
    "whois": {
      "enabled": true,
      "cache_size": 50000,
      "cache_ttl": 86400
    }
  }
}
```

---

## Key Takeaways

1. **Enrichment**: TI adds context to raw attack data
2. **Multiple Sources**: Combine feeds for better accuracy
3. **Reputation Scores**: Quantify IP risk automatically
4. **Geolocation**: Identify origin and verify plausibility
5. **Integration**: TI improves response decisions

---

## Next Steps

- **Setup**: [Setting Up DDoSPoT](08_Setting_Up_DDoSPoT.md)
- **Monitoring**: [Monitoring Threats](09_Monitoring_Threats.md)
- **ML Detection**: [Machine Learning](11_Machine_Learning_Detection.md)
- **Evasion**: [Evasion Detection](13_Evasion_Detection.md)

---

## Review Questions

1. What information does geolocation provide?
2. How is IP reputation score calculated?
3. What are the main threat intelligence feeds?
4. How does TI improve threat scoring?
5. What can you learn from WHOIS information?

## Additional Resources

- GeoIP2 Documentation
- AbuseIPDB API
- Spamhaus DNSBL
- Project Honey Pot
- AlienVault OTX
