# DDoSPoT Production Operations Playbook

Quick reference guides for common operational tasks and emergency procedures.

## Quick Reference

### Health Check Command
```bash
# Complete system health check
./scripts/health_check.sh

# Or manually:
sudo systemctl status ddospot-honeypot.service ddospot-dashboard.service
docker compose ps
curl -I https://ddospot.example.com/health
```

### Service Control
```bash
# Start all services
sudo systemctl start ddospot-honeypot.service ddospot-dashboard.service
docker compose up -d

# Stop all services
sudo systemctl stop ddospot-honeypot.service ddospot-dashboard.service
docker compose down

# Restart services
sudo systemctl restart ddospot-honeypot.service ddospot-dashboard.service
docker compose restart

# View logs
sudo journalctl -u ddospot-dashboard.service -f
docker compose logs -f
```

---

## Common Playbooks

### 1. Service Not Starting

**Symptom**: Dashboard or honeypot service fails to start

**Investigation**:
```bash
# Check systemd status
sudo systemctl status ddospot-dashboard.service
sudo journalctl -u ddospot-dashboard.service -n 50

# Check Docker logs
docker compose logs ddospot-dashboard

# Check if port is in use
sudo lsof -i :5000

# Verify environment
sudo cat /opt/ddospot/.env.prod | grep -v "^#"
```

**Resolution**:
1. Check `.env.prod` for missing required variables
2. Verify file permissions: `sudo chown -R ddospot:ddospot /opt/ddospot`
3. Verify database: `sqlite3 /var/lib/ddospot/honeypot.db ".tables"`
4. Check disk space: `df -h /var/lib/ddospot`
5. Restart services: `sudo systemctl restart ddospot-dashboard.service`

---

### 2. High CPU/Memory Usage

**Symptom**: System running slowly, alerts for high resource usage

**Investigation**:
```bash
# Check overall system
top -b -n 1 | head -20

# Check specific service memory
docker stats

# Check process details
ps aux | grep python | grep dashboard

# Check log volume
du -h /var/log/ddospot/
du -h /var/log/nginx/
```

**Resolution**:
1. **Memory Leak**: Restart dashboard service
   ```bash
   sudo systemctl restart ddospot-dashboard.service
   ```

2. **High Event Load**: Check alert thresholds
   ```bash
   grep "ALERT_THRESHOLD" /opt/ddospot/.env.prod
   ```

3. **Large Database**: Run maintenance
   ```bash
   sqlite3 /var/lib/ddospot/honeypot.db "VACUUM;"
   ```

4. **Log Growth**: Rotate logs manually
   ```bash
   sudo logrotate -f /etc/logrotate.d/ddospot
   ```

---

### 3. Database Corruption

**Symptom**: "database disk image is malformed" errors

**Investigation**:
```bash
# Test database integrity
sqlite3 /var/lib/ddospot/honeypot.db "PRAGMA integrity_check;"

# Check database size
ls -lh /var/lib/ddospot/honeypot.db

# View recent errors
sudo journalctl -u ddospot-dashboard.service | grep -i "database\|error"
```

**Resolution**:
1. Stop services: `sudo systemctl stop ddospot-dashboard.service`
2. Backup corrupted database: `cp /var/lib/ddospot/honeypot.db /var/lib/ddospot/honeypot.db.corrupt`
3. Attempt recovery:
   ```bash
   sqlite3 /var/lib/ddospot/honeypot.db << EOF
   .mode insert
   .output /tmp/dump.sql
   SELECT * FROM honeypot_events;
   EOF
   ```
4. If recovery fails, restore from backup: `./restore.sh /opt/ddospot/backups/[backup_file].tar.gz`
5. Restart services: `sudo systemctl start ddospot-dashboard.service`

---

### 4. Nginx Errors (502/503)

**Symptom**: "Bad Gateway" or "Service Unavailable" errors

**Investigation**:
```bash
# Check Nginx status
sudo systemctl status nginx

# Verify upstream connectivity
curl http://127.0.0.1:5000/health
curl http://localhost:5000/health

# Check Nginx logs
sudo tail -50 /var/log/nginx/ddospot-error.log

# Verify DNS/hosts
grep ddospot /etc/hosts
```

**Resolution**:
1. Check backend service: `sudo systemctl status ddospot-dashboard.service`
2. Verify Nginx config: `sudo nginx -t`
3. Check firewall: `sudo ufw status`
4. Restart Nginx: `sudo systemctl restart nginx`
5. If persistent, check Docker: `docker compose ps`

---

### 5. Authentication/Token Issues

**Symptom**: "401 Unauthorized" or "Invalid token" errors

**Investigation**:
```bash
# Verify token in environment
grep "DDOSPOT_API_TOKEN" /opt/ddospot/.env.prod

# Check if token auth is enabled
grep "DDOSPOT_REQUIRE_TOKEN" /opt/ddospot/.env.prod

# Test with curl
curl -H "Authorization: Bearer YOUR_TOKEN" https://ddospot.example.com/api/stats
```

**Resolution**:
1. Verify token in request header
2. Regenerate token if compromised:
   ```bash
   NEW_TOKEN=$(openssl rand -hex 32)
   sed -i "s/DDOSPOT_API_TOKEN=.*/DDOSPOT_API_TOKEN=$NEW_TOKEN/" /opt/ddospot/.env.prod
   sudo systemctl restart ddospot-dashboard.service
   ```
3. Disable token requirement (NOT recommended):
   ```bash
   sed -i 's/DDOSPOT_REQUIRE_TOKEN=.*/DDOSPOT_REQUIRE_TOKEN=false/' /opt/ddospot/.env.prod
   ```

---

### 6. Monitoring Stack Issues

**Symptom**: No metrics, Grafana shows "No Data", alerts not firing

**Investigation**:
```bash
# Check Prometheus status
docker compose exec prometheus curl http://localhost:9090/api/v1/status/tsdb

# View Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana data source
curl http://localhost:3000/api/datasources

# View Alertmanager configuration
docker compose exec alertmanager amtool config
```

**Resolution**:
1. Restart Prometheus: `docker compose restart prometheus`
2. Restart Grafana: `docker compose restart grafana`
3. Check dashboard service metrics endpoint:
   ```bash
   curl -u admin:password http://127.0.0.1:5000/metrics | head -20
   ```
4. Verify scrape interval: `grep scrape_interval docker-compose.prod.yml`

---

### 7. SSL/TLS Certificate Issues

**Symptom**: "Certificate has expired" or browser SSL warnings

**Investigation**:
```bash
# Check certificate expiration
sudo certbot certificates

# View certificate details
echo | sudo openssl s_client -connect localhost:443 2>/dev/null | grep -A 5 "Validity"

# Test with curl
curl -v https://ddospot.example.com 2>&1 | grep "SSL"
```

**Resolution**:
1. Manual renewal: `sudo certbot renew --force-renewal`
2. Update Nginx config with new certificate paths if needed
3. Reload Nginx: `sudo systemctl reload nginx`
4. Verify: `echo | openssl s_client -connect localhost:443`

---

### 8. Alerts Not Sending

**Symptom**: Critical events detected but no email/Slack notifications

**Investigation**:
```bash
# Check Alertmanager status
docker compose exec alertmanager amtool status

# View active alerts
docker compose exec alertmanager amtool alert

# Check SMTP configuration
grep -E "SMTP|SLACK|PAGERDUTY" /opt/ddospot/.env.prod

# View alertmanager logs
docker compose logs alertmanager
```

**Resolution**:
1. Verify SMTP credentials: Edit `.env.prod` and test SMTP connection
   ```bash
   python3 << 'EOF'
   import smtplib
   server = smtplib.SMTP("smtp.gmail.com", 587)
   server.starttls()
   server.login("your-email@gmail.com", "app-password")
   print("SMTP connection successful")
   EOF
   ```

2. Verify Slack webhook:
   ```bash
   curl -X POST -d '{"text":"Test"}' $DDOSPOT_SLACK_WEBHOOK
   ```

3. Restart Alertmanager: `docker compose restart alertmanager`

---

### 9. Disk Space Issues

**Symptom**: "No space left on device" errors, storage alerts

**Investigation**:
```bash
# Check disk usage
df -h

# Find large directories
du -sh /var/lib/ddospot/*
du -sh /var/log/*
du -sh /opt/ddospot/backups/*
```

**Resolution**:
1. **Clean old backups**:
   ```bash
   find /opt/ddospot/backups -name "*.tar.gz" -mtime +30 -delete
   ```

2. **Reduce Prometheus retention**:
   ```bash
   # Edit docker-compose.prod.yml, change --storage.tsdb.retention.time
   docker compose up -d prometheus
   ```

3. **Archive old logs**:
   ```bash
   sudo logrotate -f /etc/logrotate.d/ddospot
   ```

4. **Expand storage** (if available):
   ```bash
   # Add new volume and remount
   ```

---

### 10. Network Connectivity Issues

**Symptom**: Intermittent connection failures, timeouts

**Investigation**:
```bash
# Check network status
ip addr show
route -n

# Test DNS
nslookup ddospot.example.com
dig ddospot.example.com

# Check firewall
sudo iptables -L
sudo ufw status verbose

# Test connectivity
ping 8.8.8.8
traceroute 8.8.8.8
```

**Resolution**:
1. Verify firewall rules: `sudo ufw status`
2. Check DNS resolution: `nslookup ddospot.example.com`
3. Verify network interface: `ip addr show`
4. Restart networking: `sudo systemctl restart networking`

---

## Emergency Procedures

### Service Failure Recovery

**When all services are down**:

```bash
# 1. Check system status
systemctl status

# 2. Verify hardware/network
ip link
df -h

# 3. Start Docker
sudo systemctl start docker

# 4. Start services
cd /opt/ddospot
sudo docker compose up -d
sudo systemctl start ddospot-honeypot.service
sudo systemctl start ddospot-dashboard.service

# 5. Verify services
docker compose ps
sudo systemctl status ddospot-*

# 6. Test connectivity
curl -I https://ddospot.example.com/health
```

### Data Loss Recovery

**Immediate actions**:

```bash
# 1. Stop services (prevent further writes)
sudo systemctl stop ddospot-dashboard.service

# 2. Check available backups
ls -lah /opt/ddospot/backups/

# 3. Identify latest good backup
# Choose recent backup without corruption signs

# 4. Restore from backup
./restore.sh /opt/ddospot/backups/[backup_file].tar.gz

# 5. Verify data
sqlite3 /var/lib/ddospot/honeypot.db "SELECT COUNT(*) FROM honeypot_events;"
```

### Security Breach Response

**Immediate containment**:

```bash
# 1. Disable external access
sudo ufw default deny incoming

# 2. Kill suspicious processes
ps aux | grep -v grep | grep -E "suspicious_command"

# 3. Change credentials
# Regenerate API token
# Change Grafana admin password
# Rotate database credentials

# 4. Review logs
sudo journalctl --since "1 hour ago" > /tmp/incident_logs.txt
sudo tail -1000 /var/log/nginx/ddospot-access.log > /tmp/nginx_logs.txt

# 5. Isolate compromised data
# Restore from latest clean backup

# 6. Full security audit (see SECURITY_CHECKLIST.md)
```

---

## Maintenance Windows

### Scheduled Maintenance

```bash
# 1. Announce maintenance window
# Notify users 24-48 hours in advance

# 2. Create backup
./backup.sh

# 3. Perform updates
sudo apt update && sudo apt upgrade -y
cd /opt/ddospot && git pull
docker compose pull

# 4. Stop services
sudo systemctl stop ddospot-*
docker compose down

# 5. Apply changes
docker compose build

# 6. Restart services
docker compose up -d
sudo systemctl start ddospot-*

# 7. Verify services
sleep 30
curl -I https://ddospot.example.com/health

# 8. Announce completion
```

---

## Performance Optimization

### Slow Dashboard

```bash
# Check database performance
sqlite3 /var/lib/ddospot/honeypot.db "VACUUM;"
sqlite3 /var/lib/ddospot/honeypot.db "ANALYZE;"

# Check query load
sqlite3 /var/lib/ddospot/honeypot.db << EOF
SELECT name FROM sqlite_master WHERE type='index';
EOF

# Monitor real-time load
docker stats
```

### High Event Processing Load

```bash
# Increase worker processes
sed -i 's/DDOSPOT_WORKERS=.*/DDOSPOT_WORKERS=8/' /opt/ddospot/.env.prod
sudo systemctl restart ddospot-dashboard.service

# Increase rate limit threshold if necessary
sed -i 's/DDOSPOT_RATE_LIMIT_REQUESTS=.*/DDOSPOT_RATE_LIMIT_REQUESTS=100/' /opt/ddospot/.env.prod
```

---

## Runbook Template

Use this template for custom runbooks:

```markdown
## [Issue Title]

**Severity**: [Critical/High/Medium/Low]  
**MTTR Target**: [Time to resolve]  

### Symptoms
- [Symptom 1]
- [Symptom 2]

### Root Causes
- [Cause 1]
- [Cause 2]

### Detection
[How to detect this issue]

### Resolution Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Verification
[How to verify fix worked]

### Prevention
[How to prevent in future]

### Escalation
- [Escalation path]
- [Contact info]
```

---

## Support Contacts

| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| On-Call | [Name] | [Phone] | [Email] | 24/7 |
| Engineering Lead | [Name] | [Phone] | [Email] | Business hours |
| Security | [Name] | [Phone] | [Email] | Business hours |
| Manager | [Name] | [Phone] | [Email] | Business hours |

---

**Last Updated**: 2024  
**Next Review**: [Date]  
**Owner**: Operations Team
