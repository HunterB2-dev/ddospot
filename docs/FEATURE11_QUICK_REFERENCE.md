# Feature #11 Quick Reference - Web Configuration UI

## What's New?
Feature #11 adds a complete web-based configuration interface so you can manage all DDoSPoT settings through a beautiful dashboard UI instead of editing files or making API calls.

## 📍 How to Access
1. **From Dashboard**: Click the ⚙️ settings icon in the header
2. **Direct URL**: Navigate to `http://localhost:5000/settings`

## 🎯 Configuration Categories

### 🍯 Honeypot Services
Configure which network services your honeypot emulates:
- **SSH Service** (Port 2222) - Enable/disable, customize port
- **HTTP Service** (Port 8080) - Enable/disable, customize port  
- **SSDP Service** (Port 1900) - Enable/disable, customize port
- **Logging Level** - DEBUG, INFO (default), WARNING, ERROR

**Quick Example:**
```
SSH Port: 2222 ✅
HTTP Port: 8080 ✅
SSDP Port: 1900 ✅
Log Level: INFO
```

### 🔔 Alert Configuration
Set thresholds for when the system should alert you:
- **Event Threshold** - Alert after N events per minute (default: 10)
- **Unique IP Threshold** - Alert after N unique IPs per hour (default: 5)
- **Alert Channels** - Enable/disable Email, Webhook, Slack notifications

**Quick Example:**
```
Events per minute threshold: 15
Unique IPs per hour threshold: 20
Email Alerts: Enabled ✅
Webhook Alerts: Disabled
Slack Alerts: Disabled
```

### ⚡ Response Actions
Configure how the honeypot responds to threats:
- **Auto-Block Threshold** - Threat score to trigger auto-blocking (0-10, default 7.0)
- **Block Duration** - How long to block an IP (default 24 hours)
- **Webhook Notifications** - Enable webhook alerts on actions

**Quick Example:**
```
Auto-block threshold: 7.5
Block duration: 12 hours
Webhooks enabled: ✅
```

### 🔧 System Preferences
General system settings:
- **UI Theme** - Light or dark mode
- **Refresh Interval** - How often to refresh dashboard (1-60 seconds)
- **Data Retention** - Keep data for N days (default 90)
- **Automatic Backups** - Enable/disable and set schedule
- **Backup Schedule** - Cron format (default: 0 2 * * * = 2 AM daily)

**Quick Example:**
```
Theme: Dark Mode 🌙
Refresh: 5 seconds
Data retention: 90 days
Backups: Enabled ✅ (Daily at 2:00 AM)
```

## 🔌 API Endpoints

All settings can be managed via REST API:

```bash
# Get all honeypot settings
curl http://localhost:5000/api/response/config/honeypot

# Update alert threshold
curl -X POST http://localhost:5000/api/response/config/alerts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-admin-key" \
  -d '{"alert_event_threshold": "20"}'

# Test email configuration
curl -X POST http://localhost:5000/api/response/config/test/email \
  -H "X-API-Key: demo-admin-key"

# Get system settings
curl http://localhost:5000/api/response/config/system
```

## 📊 Configuration Storage

Settings are stored in SQLite database with automatic type conversion:

| Setting | Type | Example | Default |
|---------|------|---------|---------|
| honeypot_ssh_port | int | 2222 | 2222 |
| honeypot_log_level | string | INFO | INFO |
| alert_event_threshold | int | 10 | 10 |
| response_auto_block_threshold | float | 7.5 | 7.0 |
| ui_theme | string | light/dark | light |
| system_backup_enabled | bool | true/false | true |

## ✨ Key Features

✅ **Tab-Based Organization** - Grouped by function (Honeypot, Alerts, Responses, System)  
✅ **Form Validation** - Client-side validation with helpful error messages  
✅ **Live Status Indicators** - See service health at a glance  
✅ **Type Safety** - Automatic type conversion (int, float, bool, string, json)  
✅ **Persistent Storage** - Settings survive restarts  
✅ **API Integration** - Manage settings programmatically  
✅ **Responsive Design** - Works on desktop and mobile  
✅ **Test Functions** - Test email/webhook configurations  

## 🧪 Testing Your Configuration

Each tab has test buttons:

- **Test Alert** - Send a test alert message
- **Test Webhook** - Send test data to your webhook URL
- **Restart Services** - Gracefully restart honeypot services

Click these to verify your settings work correctly.

## 📝 Common Configurations

### High-Security Setup
```
SSH Port: 2222 (custom, non-standard)
HTTP Port: 8080
Log Level: DEBUG (verbose logging)

Event Threshold: 5 (alert frequently)
Unique IP Threshold: 3
Email Alerts: ✅ Enabled
Webhook Alerts: ✅ Enabled

Auto-block threshold: 5.0 (block aggressively)
Block duration: 48 hours
Webhooks: ✅ Enabled
```

### Production Setup
```
SSH Port: 2222
HTTP Port: 8080  
Log Level: INFO (normal)

Event Threshold: 20
Unique IP Threshold: 50
Email Alerts: ✅ Enabled
Slack Alerts: ✅ Enabled

Auto-block threshold: 7.5
Block duration: 24 hours
Webhooks: ✅ Enabled

Data Retention: 180 days
Backups: ✅ Daily at 2 AM
```

### Development Setup
```
SSH Port: 2222
HTTP Port: 8080
Log Level: DEBUG (maximum detail)

Event Threshold: 100 (high, rarely alert)
Unique IP Threshold: 1000
All Alerts: Disabled

Auto-block threshold: 9.0 (rarely block)
Block duration: 1 hour
Webhooks: Disabled
```

## 🔒 Security Notes

- Configuration endpoints support API key authentication
- POST requests require `X-API-Key: demo-admin-key` header
- Port numbers must be 1024-65535
- Sensitive values (passwords) should not be stored in config
- All settings are validated before saving

## 🐛 Troubleshooting

**Settings not saving?**
- Check browser console for errors (F12)
- Verify API key is correct
- Ensure database has write permissions

**Webhooks not working?**
- Use the Test Webhook button to debug
- Check webhook URL is accessible from server
- Verify webhook server is listening on configured port

**Services won't restart?**
- Check server logs for errors
- Ensure no other process is holding ports
- Try manual restart: `systemctl restart ddospot`

## 📚 More Information

- **Full API Documentation**: [API_DOCUMENTATION.md](../docs/API_DOCUMENTATION.md)
- **Dashboard Guide**: [DASHBOARD_QUICK_START.md](../docs/DASHBOARD_QUICK_START.md)
- **Security Guide**: [SECURITY_HARDENING.md](../docs/SECURITY_HARDENING.md)
- **Complete Roadmap**: [FEATURES_11_12_ROADMAP.md](../docs/FEATURES_11_12_ROADMAP.md)

---

**DDoSPoT v2.0 | Feature #11 Web Configuration UI | Ready for Production ✅**
