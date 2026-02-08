# Configuration Management in DDoSPoT

## Configuration Overview

DDoSPoT is highly configurable to meet different organizational needs. Configuration is managed through JSON files and the web interface.

---

## Configuration Files

### Main Configuration File

**Location**: `/config/config.json`

```json
{
  "app": {
    "name": "DDoSPoT",
    "version": "1.0.0",
    "debug": false,
    "host": "0.0.0.0",
    "port": 5000
  },
  
  "honeypots": {
    "enabled": true,
    "ssh": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 2222,
      "banner": "SSH-2.0-OpenSSH_7.4",
      "max_attempts": 3,
      "lockout_duration": 300
    },
    "http": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8888,
      "banner": "Apache/2.4.41",
      "content_type": "wordpress",
      "max_requests_per_minute": 100
    },
    "ssdp": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 1900,
      "device_model": "Generic-Router",
      "max_requests_per_minute": 1000
    }
  },
  
  "detection": {
    "enabled": true,
    "signature_matching": true,
    "anomaly_detection": true,
    "ml_detection": true,
    "threat_threshold": 0.5,
    "high_threshold": 0.7,
    "critical_threshold": 0.9
  },
  
  "response": {
    "enabled": true,
    "auto_respond": true,
    "ip_blocking": {
      "enabled": true,
      "block_duration": 3600,
      "auto_unblock": true,
      "firewall_integration": true
    },
    "rate_limiting": {
      "enabled": true,
      "adaptive": true
    }
  },
  
  "database": {
    "type": "sqlite",
    "path": "/var/lib/ddospot/ddospot.db",
    "backup_enabled": true,
    "backup_path": "/var/backups/ddospot/",
    "backup_frequency": "daily",
    "retention_days": 90
  },
  
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "/var/log/ddospot/honeypot.log",
    "max_size_mb": 100,
    "backup_count": 10,
    "detailed_logging": false
  }
}
```

### Alert Configuration File

**Location**: `/config/alert_config.json`

```json
{
  "alerts": {
    "enabled": true,
    
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "sender_email": "ddospot@company.com",
      "sender_password": "app-specific-password",
      "recipients": ["security@company.com"],
      "cc": ["manager@company.com"],
      "min_severity": "MEDIUM",
      "batch_enabled": false,
      "batch_interval": 300
    },
    
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "channel": "#security-alerts",
      "mention_on_critical": "@security-team",
      "min_severity": "HIGH",
      "include_details": true
    },
    
    "webhook": {
      "enabled": true,
      "url": "https://your-siem.com/api/alerts",
      "method": "POST",
      "auth_type": "api_key",
      "auth_header": "X-API-Key",
      "auth_value": "your-api-key",
      "min_severity": "MEDIUM",
      "timeout_seconds": 5,
      "retry_attempts": 3
    },
    
    "pagerduty": {
      "enabled": false,
      "api_key": "your-pagerduty-key",
      "service_id": "your-service-id",
      "min_severity": "CRITICAL",
      "urgency": "high"
    }
  },
  
  "thresholds": {
    "ssh_attempt_limit": 5,
    "http_request_limit": 100,
    "ssdp_request_limit": 50,
    "block_duration_hours": 1,
    "escalation_threshold": 0.9
  }
}
```

---

## Configuring Honeypots

### SSH Configuration

```json
{
  "ssh": {
    "enabled": true,
    "port": 2222,
    "banner": "SSH-2.0-OpenSSH_8.2p1",
    
    "security": {
      "max_attempts": 3,
      "lockout_duration": 300,
      "require_password": true,
      "require_username": true
    },
    
    "content": {
      "allow_list_users": false,
      "fake_user_list": ["root", "admin", "test"],
      "supported_algorithms": ["ssh-rsa", "rsa-sha2-256"]
    },
    
    "logging": {
      "log_all_attempts": true,
      "log_payload": false,
      "store_passwords": true
    }
  }
}
```

### HTTP Configuration

```json
{
  "http": {
    "enabled": true,
    "port": 8888,
    "ssl_enabled": false,
    "ssl_port": 8889,
    
    "server": {
      "banner": "Apache/2.4.41",
      "fake_content_type": "wordpress"
    },
    
    "paths": {
      "fake_paths": [
        "/wp-admin/",
        "/admin/",
        "/phpmyadmin/",
        "/administrator/",
        "/index.php"
      ],
      "return_404_on_unknown": true
    },
    
    "security": {
      "max_requests_per_minute": 100,
      "block_after_attempts": 1000,
      "block_duration": 3600
    },
    
    "logging": {
      "log_all_requests": true,
      "log_payloads": true,
      "log_headers": true
    }
  }
}
```

### SSDP Configuration

```json
{
  "ssdp": {
    "enabled": true,
    "port": 1900,
    "protocol": "udp",
    
    "device_info": {
      "device_model": "Generic-Router-2024",
      "vendor": "Generic Systems Inc",
      "serial_number": "ABC123XYZ",
      "firmware_version": "1.0.0"
    },
    
    "behavior": {
      "respond_to_discovery": true,
      "respond_to_search": true,
      "include_device_description": true,
      "response_delay_ms": 0
    },
    
    "security": {
      "max_requests_per_minute": 10000,
      "detect_amplification_attacks": true,
      "amplification_threshold": 30
    }
  }
}
```

---

## Configuring Detection

### Signature Settings

```json
{
  "detection": {
    "signature_matching": {
      "enabled": true,
      "database_path": "/var/lib/ddospot/signatures.db",
      "update_frequency": "daily",
      "confidence_threshold": 0.7
    }
  }
}
```

### Anomaly Detection Settings

```json
{
  "detection": {
    "anomaly_detection": {
      "enabled": true,
      "baseline_days": 30,
      "std_dev_threshold": 3.0,
      "min_baseline_samples": 100,
      "adaptive_threshold": true
    }
  }
}
```

### ML Detection Settings

```json
{
  "detection": {
    "ml_detection": {
      "enabled": true,
      "model_path": "/var/lib/ddospot/models/",
      "confidence_threshold": 0.6,
      "batch_size": 32,
      "update_models": true,
      "update_frequency": "weekly"
    }
  }
}
```

---

## Configuring Response

### IP Blocking

```json
{
  "response": {
    "ip_blocking": {
      "enabled": true,
      
      "duration": {
        "default": 3600,
        "ssh_attack": 3600,
        "http_attack": 1800,
        "ssdp_attack": 86400,
        "critical": 604800
      },
      
      "levels": {
        "application": true,
        "firewall": true,
        "network": false
      },
      
      "whitelist": [
        "192.168.1.0/24",
        "10.0.0.0/8"
      ],
      
      "auto_unblock": true
    }
  }
}
```

### Rate Limiting

```json
{
  "response": {
    "rate_limiting": {
      "enabled": true,
      "adaptive": true,
      "reduce_factor": 0.1,
      "recovery_time": 3600,
      
      "limits": {
        "ssh": {
          "per_ip": 10,
          "per_minute": 10,
          "window_seconds": 60
        },
        "http": {
          "per_ip": 100,
          "per_endpoint": 50,
          "window_seconds": 60
        },
        "ssdp": {
          "per_ip": 1000,
          "window_seconds": 60
        }
      }
    }
  }
}
```

---

## Advanced Configuration

### Custom Response Rules

```json
{
  "response_rules": [
    {
      "id": "rule_001",
      "name": "Aggressive SSH Attack",
      "enabled": true,
      "condition": {
        "threat_type": "SSH_BRUTE_FORCE",
        "threat_score": "> 0.8",
        "attempts": "> 5"
      },
      "actions": [
        "block_ip_permanent",
        "notify_critical",
        "escalate_to_soc"
      ]
    },
    {
      "id": "rule_002",
      "name": "SQL Injection Attempt",
      "enabled": true,
      "condition": {
        "threat_type": "SQL_INJECTION",
        "threat_score": "> 0.7"
      },
      "actions": [
        "rate_limit_5_per_minute",
        "log_detailed",
        "notify_high"
      ]
    }
  ]
}
```

### Custom Threat Intelligence Feeds

```json
{
  "threat_intelligence": {
    "enabled": true,
    
    "feeds": [
      {
        "id": "feed_001",
        "name": "AbuseIPDB",
        "url": "https://api.abuseipdb.com/api/v2/blocklist",
        "api_key": "your-api-key",
        "update_frequency": "hourly",
        "threshold": 25
      },
      {
        "id": "feed_002",
        "name": "Spamhaus",
        "url": "https://www.spamhaus.org/drop/drop.txt",
        "update_frequency": "daily"
      }
    ],
    
    "geolocation": {
      "enabled": true,
      "database": "/var/lib/ddospot/GeoIP2-City.mmdb",
      "block_by_country": false,
      "country_whitelist": ["US", "CA", "UK"]
    }
  }
}
```

### Performance Tuning

```json
{
  "performance": {
    "database": {
      "connections": 10,
      "pool_size": 5,
      "timeout": 10,
      "wal_mode": true
    },
    
    "detection": {
      "batch_processing": true,
      "batch_size": 100,
      "worker_threads": 4,
      "cache_enabled": true,
      "cache_size_mb": 256
    },
    
    "memory": {
      "max_memory_mb": 1024,
      "gc_enabled": true,
      "gc_interval": 300
    }
  }
}
```

---

## Configuration via Web Interface

### Access Configuration UI

```
1. Open Dashboard: http://localhost:5000
2. Click "Configuration" tab
3. Select setting category:
   ├─ Honeypots
   ├─ Detection
   ├─ Response
   ├─ Alerts
   └─ System
4. Make changes
5. Click "Save" and "Restart Services" if needed
```

### Honeypot Settings UI

```
Configuration → Honeypots

SSH:
  ├─ Enabled: [✓] Toggle
  ├─ Port: [2222] Input
  ├─ Banner: [SSH-2.0-OpenSSH_7.4] Input
  ├─ Max Attempts: [3] Slider
  └─ Lockout Duration: [300s] Input

HTTP:
  ├─ Enabled: [✓] Toggle
  ├─ Port: [8888] Input
  ├─ Content Type: [WordPress] Dropdown
  ├─ Max Requests/Min: [100] Slider
  └─ [Save] Button

SSDP:
  ├─ Enabled: [✓] Toggle
  ├─ Port: [1900] Input
  ├─ Device Model: [Generic-Router] Input
  └─ [Save] Button
```

### Alert Configuration UI

```
Configuration → Alerts

Channels:
  ├─ Email
  │  ├─ Enabled: [✓]
  │  ├─ Recipients: [security@company.com] Input
  │  ├─ Min Severity: [HIGH] Dropdown
  │  └─ [Test] Button
  │
  ├─ Slack
  │  ├─ Enabled: [✓]
  │  ├─ Webhook URL: [https://...] Input
  │  ├─ Channel: [#security-alerts] Input
  │  ├─ Min Severity: [HIGH] Dropdown
  │  └─ [Test] Button
  │
  └─ Webhook
     ├─ Enabled: [✓]
     ├─ URL: [https://...] Input
     ├─ Auth Type: [API Key] Dropdown
     ├─ Min Severity: [MEDIUM] Dropdown
     └─ [Test] Button
```

---

## Configuration Scenarios

### Small Office Setup

```json
{
  "honeypots": {
    "ssh": {"port": 2222, "enabled": true},
    "http": {"port": 8888, "enabled": true},
    "ssdp": {"enabled": false}
  },
  "response": {
    "auto_respond": true,
    "block_duration": 3600
  },
  "alerts": {
    "email": {"enabled": true},
    "slack": {"enabled": false}
  }
}
```

### Enterprise Setup

```json
{
  "honeypots": {
    "ssh": {"port": 2222, "enabled": true},
    "http": {"port": 8888, "enabled": true},
    "ssdp": {"port": 1900, "enabled": true}
  },
  "response": {
    "auto_respond": true,
    "block_duration": 86400,
    "levels": ["application", "firewall", "network"]
  },
  "alerts": {
    "email": {"enabled": true},
    "slack": {"enabled": true},
    "webhook": {"enabled": true},
    "pagerduty": {"enabled": true}
  }
}
```

### Research Lab Setup

```json
{
  "honeypots": {
    "ssh": {"port": 2222, "enabled": true},
    "http": {"port": 8888, "enabled": true},
    "ssdp": {"port": 1900, "enabled": true}
  },
  "detection": {
    "enabled": true,
    "log_detailed": true,
    "capture_full_payload": true
  },
  "response": {
    "auto_respond": false,
    "manual_review_required": true
  },
  "alerts": {
    "webhook": {"enabled": true}
  }
}
```

---

## Best Practices

### 1. Backup Configuration

```bash
# Backup configuration files
cp -r config/ config.backup.$(date +%Y%m%d)

# Keep version history
git add config/
git commit -m "Update DDoSPoT configuration"
```

### 2. Test Changes

```bash
# Test configuration before applying
python -m json.tool config/config.json > /dev/null

# Validate configuration
ddospot --validate-config

# Apply changes gradually
# Start with test/staging environment
```

### 3. Monitor Configuration Impact

```bash
# Monitor system after config change
watch -n 1 'curl -s http://localhost:5000/api/status'

# Check logs for errors
tail -f logs/honeypot.log
tail -f logs/dashboard.log
```

### 4. Document Changes

```
Configuration Change Log:

Date: 2024-01-15
Change: Increased SSH lockout from 300s to 600s
Reason: Reduce false positives on bulk SSH connections
Impact: Slower response to SSH attacks
Tested: Yes - Lab environment
Approved: John Doe
Status: Applied
```

---

## Key Takeaways

1. **Flexible Configuration**: Fine-tune every aspect of DDoSPoT
2. **Multiple Options**: JSON files or web interface
3. **Scenario Templates**: Pre-configured setups for common scenarios
4. **Safe Changes**: Test before applying in production
5. **Documentation**: Keep track of changes and reasons

---

## Next Steps

- **Advanced Settings**: [Threat Detection](06_Threat_Detection.md)
- **Alerts**: [Alert Configuration](../docs/API_DOCUMENTATION.md)
- **Rules**: [Automated Response](07_Automated_Response.md)
- **Monitoring**: [Monitoring Threats](09_Monitoring_Threats.md)

---

## Review Questions

1. Where is the main configuration file located?
2. How do you configure email alerts?
3. What's the difference between temporary and permanent IP blocks?
4. How would you set up custom response rules?
5. What configuration is recommended for enterprise environments?

## Additional Resources

- [API Documentation](../docs/API_DOCUMENTATION.md)
- [Quick Start Guide](00_QUICK_START.md)
- [Threat Detection Guide](06_Threat_Detection.md)
