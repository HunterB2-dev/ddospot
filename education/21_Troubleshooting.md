# Troubleshooting Guide

**File 21: Common Issues, Solutions, and Diagnostics**

*Level: All Levels | Time: Reference guide*

---

## Table of Contents
1. [Quick Diagnostics](#diagnostics)
2. [Installation Issues](#installation)
3. [Runtime Problems](#runtime)
4. [Database Issues](#database)
5. [Detection Problems](#detection)
6. [Performance Issues](#performance)
7. [Network Issues](#network)
8. [Security Issues](#security)
9. [Log Interpretation](#logs)
10. [Getting Help](#help)

---

## Quick Diagnostics {#diagnostics}

### Diagnostic Checklist

Run this first:

```bash
#!/bin/bash
# File: /usr/local/bin/ddospot-diagnose.sh

echo "=== DDoSPoT System Diagnostics ==="
echo

echo "[1/8] Service Status"
if command -v docker &> /dev/null; then
  docker ps --filter "name=ddospot" --format "table {{.Names}}\t{{.Status}}"
else
  systemctl status ddospot 2>/dev/null || echo "Not running as systemd service"
fi
echo

echo "[2/8] Network Connectivity"
netstat -tuln | grep -E "(2222|8888|1900)" || echo "Honeypot ports not listening"
echo

echo "[3/8] Database Status"
curl -s http://localhost:8888/api/health | python3 -m json.tool || echo "API unreachable"
echo

echo "[4/8] Disk Space"
df -h | grep -E "(/|data|docker)" || df -h
echo

echo "[5/8] Memory Usage"
free -h || echo "Memory: $(vm_stat | grep 'Pages free' | awk '{print $3}')"
echo

echo "[6/8] CPU Load"
uptime
echo

echo "[7/8] Recent Errors"
journalctl -u ddospot -n 10 --no-pager 2>/dev/null || docker logs --tail=10 ddospot-web 2>/dev/null || tail -20 /var/log/ddospot/error.log 2>/dev/null
echo

echo "[8/8] Latest Alerts"
curl -s http://localhost:8888/api/threats?limit=5 | python3 -m json.tool 2>/dev/null || echo "Unable to fetch alerts"
```

**Run it:**

```bash
chmod +x /usr/local/bin/ddospot-diagnose.sh
./ddospot-diagnose.sh
```

---

## Installation Issues {#installation}

### Issue 1: Docker Image Won't Build

**Error:**
```
ERROR: failed to solve with frontend dockerfile.v0: failed to build LLB: executor failed
```

**Solutions:**

```bash
# 1. Clean Docker cache
docker builder prune -a

# 2. Check Docker daemon
docker ps

# 3. Build with no cache
docker build --no-cache -t ddospot:latest .

# 4. Check available disk space
df -h /var/lib/docker

# 5. Increase Docker memory (if using Docker Desktop)
# Settings → Resources → Memory: 4GB minimum, 8GB+ recommended
```

---

### Issue 2: Port Already in Use

**Error:**
```
docker: Error response from daemon: driver failed programming external connectivity on endpoint ddospot: Error starting userland proxy: listen tcp 0.0.0.0:8888: bind: address already in use.
```

**Solutions:**

```bash
# 1. Find what's using the port
lsof -i :8888
netstat -tuln | grep 8888

# 2. Kill the process (replace PID)
kill -9 <PID>

# 3. OR change DDoSPoT port in docker-compose.yml
# ports:
#   - "9999:8888"  # External:Internal

# 4. Check for zombie processes
ps aux | grep ddospot | grep -v grep

# 5. Change SELinux policy (if needed)
sudo semanage port -a -t http_port_t -p tcp 8888
```

---

### Issue 3: Out of Memory During Installation

**Error:**
```
E: Unable to locate package python3-dev
MemoryError: Unable to allocate X MB for...
```

**Solutions:**

```bash
# 1. Free up memory
sync; echo 3 > /proc/sys/vm/drop_caches

# 2. Check available RAM
free -h

# 3. Increase swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 4. Install with limited resources
docker run --memory=2g -it ddospot:latest bash

# 5. Remove unnecessary images
docker image prune -a
```

---

## Runtime Problems {#runtime}

### Issue 1: Web Interface Not Accessible

**Error:**
```
curl: (7) Failed to connect to localhost port 8888: Connection refused
```

**Diagnosis:**

```bash
# 1. Check if container is running
docker ps | grep ddospot

# 2. Check if port is listening
netstat -tuln | grep 8888

# 3. Check logs for errors
docker logs ddospot-web --tail=50

# 4. Check if service crashed
docker ps -a | grep ddospot-web  # Look for Exit status

# 5. Check system resources
docker stats
```

**Solutions:**

```bash
# If container crashed
docker restart ddospot-web

# If port not listening
docker exec ddospot-web curl localhost:8888/api/health

# If health check fails
docker exec ddospot-web python3 -m flask run --host=0.0.0.0

# If all else fails, rebuild
docker-compose down
docker-compose up -d --build
```

---

### Issue 2: High CPU Usage

**Symptoms:**
- System running slowly
- Fans loud
- Load average very high

**Investigation:**

```bash
# 1. Identify problematic process
top -b -n 1 | head -20

# 2. Check DDoSPoT specifically
docker stats --no-stream ddospot-web

# 3. Check database load
docker exec ddospot-db psql -U ddospot -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# 4. Look for infinite loops in logs
docker logs ddospot-web | grep -i "error\|exception" | tail -20
```

**Solutions:**

```bash
# Restart the service
docker restart ddospot-web

# Reduce worker threads (in config.json)
{
  "system": {
    "max_workers": 4  # Reduce from 8
  }
}

# Disable heavy features temporarily
{
  "detection": {
    "machine_learning": false,
    "threat_intelligence": false
  }
}

# Scale down if using Kubernetes
kubectl scale deployment ddospot --replicas=1 -n ddospot-prod
```

---

### Issue 3: Memory Leak

**Symptoms:**
- Memory usage increases over time
- Process becomes slower
- Eventually runs out of memory

**Investigation:**

```bash
# 1. Monitor memory trend
for i in {1..10}; do
  docker stats --no-stream ddospot-web
  sleep 60
done | grep "MEMORY"

# 2. Check for file descriptor leaks
lsof -p $(docker inspect -f '{{.State.Pid}}' ddospot-web) | wc -l

# 3. Profile with memory profiler
docker exec ddospot-web python3 -m memory_profiler app/main.py
```

**Solutions:**

```bash
# 1. Restart service regularly (cron job)
0 */6 * * * docker restart ddospot-web

# 2. Enable memory limits
# In docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G
#     reservations:
#       memory: 1G

# 3. Report bug with profiling data
# Include: memory_profiler output + heap dump
```

---

## Database Issues {#database}

### Issue 1: Database Connection Failed

**Error:**
```
FATAL: remaining connection slots are reserved
psycopg2.OperationalError: could not connect to server
```

**Investigation:**

```bash
# 1. Check database is running
docker ps | grep postgres

# 2. Test connection
docker exec ddospot-db psql -U ddospot -d ddospot -c "SELECT 1;"

# 3. Check connection count
docker exec ddospot-db psql -U ddospot -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Check logs
docker logs ddospot-db | tail -50
```

**Solutions:**

```bash
# 1. Increase max connections
# In postgres settings (docker-compose.yml):
# command:
#   - "postgres"
#   - "-c"
#   - "max_connections=200"

# 2. Kill long-running queries
docker exec ddospot-db psql -U ddospot -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '1 hour';"

# 3. Restart database
docker restart ddospot-db

# 4. Check for connection leaks in application
# Review connection pooling settings in config.json
```

---

### Issue 2: Slow Database Queries

**Symptoms:**
- Dashboard loads slowly
- API responses delayed
- High database CPU usage

**Investigation:**

```bash
# 1. Enable query logging
docker exec ddospot-db psql -U ddospot -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"

# 2. Restart database
docker restart ddospot-db

# 3. Check slow query log
docker exec ddospot-db tail -100 /var/log/postgresql/postgresql.log | grep "duration:"

# 4. Check table sizes
docker exec ddospot-db psql -U ddospot -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# 5. Check missing indexes
docker exec ddospot-db psql -U ddospot -c "SELECT * FROM pg_stat_user_tables WHERE seq_scan > 10000 ORDER BY seq_scan DESC;"
```

**Solutions:**

```bash
# 1. Add index on frequently queried columns
docker exec ddospot-db psql -U ddospot -c "CREATE INDEX idx_threats_timestamp ON threats(timestamp DESC);"

# 2. Vacuum and analyze
docker exec ddospot-db psql -U ddospot -c "VACUUM ANALYZE;"

# 3. Archive old data
# Move data older than 90 days to archive table

# 4. Increase query timeout
# In config.json: "database_query_timeout_seconds": 30
```

---

### Issue 3: Database Disk Full

**Symptoms:**
- New attacks not recorded
- Database stops responding
- Disk space full

**Investigation:**

```bash
# 1. Check disk usage
du -sh /var/lib/docker/volumes/*/

# 2. Check database size
docker exec ddospot-db psql -U ddospot -c "SELECT pg_size_pretty(pg_database_size('ddospot'));"

# 3. Check table sizes
docker exec ddospot-db psql -U ddospot -c "SELECT tablename, pg_size_pretty(pg_total_relation_size('public.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size('public.'||tablename) DESC;"
```

**Solutions:**

```bash
# 1. Delete old data
docker exec ddospot-db psql -U ddospot -c "DELETE FROM threats WHERE timestamp < NOW() - INTERVAL '90 days';"

# 2. Vacuum to reclaim space
docker exec ddospot-db psql -U ddospot -c "VACUUM FULL;"

# 3. Increase volume size
# Stop container, resize volume, restart

# 4. Archive to external storage
# Implement data retention policy
```

---

## Detection Problems {#detection}

### Issue 1: No Threats Being Detected

**Symptoms:**
- Zero alerts for days
- Dashboard shows no activity
- But traffic is being received

**Investigation:**

```bash
# 1. Check if honeypot is receiving traffic
docker exec ddospot-web netstat -unt | grep ESTABLISHED

# 2. Check detection module
docker logs ddospot-web | grep -i "detection\|threat" | tail -20

# 3. Verify detection is enabled
curl http://localhost:8888/api/status | python3 -m json.tool | grep -i detection

# 4. Check detection threshold
curl http://localhost:8888/api/config | python3 -m json.tool | grep -A5 "detection"

# 5. Check attack logs directly
docker exec ddospot-db psql -U ddospot -c "SELECT COUNT(*) FROM threats;"
```

**Solutions:**

```bash
# 1. Lower detection sensitivity
# In config.json:
# "detection": {
#   "sensitivity": "medium"  # Change from "high" to "medium"
# }

# 2. Check threat Intelligence is working
curl http://localhost:8888/api/threat_intelligence/status

# 3. Retrain ML models
# See File 11: Machine Learning Detection

# 4. Enable logging
# "logging": { "level": "DEBUG" }

# 5. Test with known attack pattern
curl "http://localhost:8888/search?q=<script>alert(1)</script>"
```

---

### Issue 2: Too Many False Positives

**Symptoms:**
- Legitimate traffic blocked
- False positive rate > 10%
- Users complaining about blocks

**Investigation:**

```bash
# 1. Check false positive rate
curl http://localhost:8888/api/analytics/false_positive_rate | python3 -m json.tool

# 2. Review recent false positives
curl "http://localhost:8888/api/threats?filter=false_positive&limit=20" | python3 -m json.tool

# 3. Check detection thresholds
curl http://localhost:8888/api/config | grep -A10 "thresholds"

# 4. Identify patterns
# Look for common patterns in false positives
```

**Solutions:**

```bash
# 1. Whitelist legitimate sources
# In config.json:
# "whitelist": {
#   "ips": ["192.0.2.1"],
#   "user_agents": ["curl", "Postman"],
#   "keywords": ["legitimate_tool"]
# }

# 2. Increase thresholds
# "detection": {
#   "thresholds": {
#     "brute_force_attempts": 10,  # Increase from 5
#     "request_rate": 10000  # Increase from 1000
#   }
# }

# 3. Adjust ML model
# Lower sensitivity or retrain with more false positive examples

# 4. Disable specific detection rules
# "detection": {
#   "rules": {
#     "sql_injection": true,
#     "scanning": false  # Disable if too many false positives
#   }
# }
```

---

### Issue 3: Detection Lag

**Symptoms:**
- Threats detected after 1-5 minutes
- Real-time alerting not working
- Dashboard updates slowly

**Investigation:**

```bash
# 1. Check API response time
time curl http://localhost:8888/api/threats

# 2. Check processing queue
curl http://localhost:8888/api/status | grep -i queue

# 3. Monitor system resources
docker stats --no-stream

# 4. Check detection module load
docker logs ddospot-web | grep -i "processing\|queue" | tail -20

# 5. Check database latency
docker exec ddospot-db pgbench -c 10 -j 2 -t 1000 ddospot
```

**Solutions:**

```bash
# 1. Increase worker threads
# In config.json:
# "system": {
#   "max_workers": 16  # Increase from 8
# }

# 2. Optimize database
# Add indexes, increase connection pool

# 3. Disable heavy features temporarily
# "detection": {
#   "machine_learning": false,
#   "threat_intelligence": false
# }

# 4. Scale horizontally
# Add more DDoSPoT instances (Kubernetes)

# 5. Adjust buffering
# "buffer_size": 10000,  # Increase
# "flush_interval_seconds": 5  # Decrease
```

---

## Performance Issues {#performance}

### Issue 1: Dashboard Slow to Load

**Solutions:**

```bash
# 1. Enable caching
# In config.json:
# "cache": {
#   "enabled": true,
#   "ttl_seconds": 300
# }

# 2. Reduce data fetched
curl "http://localhost:8888/api/threats?limit=50"  # Reduce from 500

# 3. Enable compression
# In nginx config:
# gzip on;
# gzip_types text/plain application/json text/css;

# 4. Use CDN for static assets
# Serve CSS/JS from CDN, images from cache

# 5. Optimize database queries
# Add indexes for frequently accessed columns
```

---

### Issue 2: API Rate Limiting Issues

**Symptoms:**
- Getting 429 (Too Many Requests) errors
- Legitimate requests blocked

**Solutions:**

```bash
# 1. Check current limits
curl http://localhost:8888/api/config | grep -A5 "rate_limit"

# 2. Increase rate limit
# In config.json:
# "api": {
#   "rate_limit": {
#     "requests_per_minute": 600  # Increase from 300
#   }
# }

# 3. Whitelist your IP
# "api": {
#   "rate_limit": {
#     "whitelist": ["192.0.2.1"]
#   }
# }

# 4. Use authentication token (higher limits)
# Get token: POST /api/auth/login
# Use token: Authorization: Bearer <token>
```

---

## Network Issues {#network}

### Issue 1: Firewall Blocking Traffic

**Symptoms:**
- Honeypot not receiving attacks
- Connection refused errors
- Slow response times

**Investigation:**

```bash
# 1. Check firewall status
sudo ufw status
sudo firewall-cmd --list-all

# 2. Test connectivity
nc -zv localhost 2222
nc -zv localhost 8888

# 3. Check network interface
ip addr | grep "inet "

# 4. Check routing
ip route
```

**Solutions:**

```bash
# UFW (Ubuntu)
sudo ufw allow 2222/tcp
sudo ufw allow 8888/tcp
sudo ufw allow 1900/udp
sudo ufw enable

# firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --permanent --add-port=8888/tcp
sudo firewall-cmd --permanent --add-port=1900/udp
sudo firewall-cmd --reload

# iptables (generic)
sudo iptables -A INPUT -p tcp --dport 2222 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8888 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 1900 -j ACCEPT
```

---

### Issue 2: High Latency / Slow Network

**Investigation:**

```bash
# 1. Check network latency
ping -c 4 8.8.8.8

# 2. Check packet loss
mtr -r 8.8.8.8

# 3. Check bandwidth usage
iftop -n

# 4. Check DNS resolution
dig example.com +stats
```

**Solutions:**

```bash
# 1. Use local DNS instead of public
# In /etc/resolv.conf:
# nameserver 8.8.8.8  → nameserver 127.0.0.1

# 2. Optimize network settings
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728

# 3. Increase TCP backlog
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096
```

---

## Security Issues {#security}

### Issue 1: Unauthorized Access Attempt

**Symptoms:**
- Failed login attempts in logs
- Suspicious API calls

**Investigation:**

```bash
# 1. Check authentication logs
docker logs ddospot-web | grep -i "authentication\|unauthorized" | tail -20

# 2. Check API access logs
curl http://localhost:8888/api/logs | grep "unauthorized"

# 3. Check who's accessing
netstat -tn | grep 8888 | awk '{print $5}' | sort | uniq -c
```

**Solutions:**

```bash
# 1. Change default password
curl -X POST http://localhost:8888/api/auth/change-password \
  -H "Content-Type: application/json" \
  -d '{"old_password":"admin","new_password":"new_strong_password"}'

# 2. Enable MFA
# In config.json:
# "security": {
#   "mfa_enabled": true
# }

# 3. Restrict API access
# "api": {
#   "allowed_ips": ["192.0.2.0/24"],
#   "require_authentication": true
# }

# 4. Review audit log
curl http://localhost:8888/api/audit
```

---

## Log Interpretation {#logs}

### Reading DDoSPoT Logs

**Log Levels:**

```
DEBUG   - Detailed information, usually only of interest when diagnosing problems
INFO    - Confirmation that things are working as expected
WARNING - An indication that something unexpected happened
ERROR   - A serious problem; the software has not been able to perform some function
CRITICAL - A very serious error; the program itself may not be able to continue
```

**Analyzing Logs:**

```bash
# 1. Filter by severity
docker logs ddospot-web | grep "ERROR\|CRITICAL"

# 2. Follow logs in real-time
docker logs -f ddospot-web

# 3. Search for specific events
docker logs ddospot-web | grep "threat_detected\|response_action"

# 4. Count occurrences
docker logs ddospot-web | grep "ERROR" | wc -l

# 5. Get timestamp range
docker logs --since 2024-01-15 --until 2024-01-16 ddospot-web

# 6. Combine multiple filters
docker logs ddospot-web | grep -E "ERROR|CRITICAL|timeout" | tail -100
```

---

## Getting Help {#help}

### When to Report a Bug

Include:

1. **System Information**
   ```bash
   uname -a
   docker --version
   docker logs ddospot-web --tail=100
   ```

2. **Configuration**
   ```bash
   cat config/config.json  # Sanitize sensitive data
   ```

3. **Diagnostic Output**
   ```bash
   ./ddospot-diagnose.sh > diagnostic_report.txt
   ```

4. **Reproduction Steps**
   - What did you do?
   - What happened?
   - What did you expect?

5. **Error Messages**
   - Full error text
   - Stack trace if available
   - Surrounding log lines (context)

### Reporting Resources

**For Bugs/Issues:**
```
GitHub: https://github.com/your-org/ddospot/issues
Include: diagnostic_report.txt + steps to reproduce + expected behavior
```

**For Security Issues:**
```
Email: security@example.com
DO NOT post security issues on GitHub
```

**For Questions:**
```
Discussion Forum: https://github.com/your-org/ddospot/discussions
Documentation: https://docs.example.com
```

---

## Summary

Quick reference for common issues:

| Problem | Check | Solution |
|---------|-------|----------|
| Service won't start | Logs, ports, resources | Restart, check firewall, free disk |
| High CPU/Memory | docker stats, processes | Restart, reduce workers, scale |
| No threats detected | Detection enabled?, thresholds | Lower sensitivity, enable features |
| Too many false positives | Rules, thresholds | Whitelist, increase thresholds |
| Slow dashboard | Database, API, network | Add indexes, scale, optimize |
| Database full | Disk usage | Delete old data, increase volume |

---

## Next Steps

- Read relevant File based on your issue
- Check logs first, always
- Restart service before escalating
- Collect diagnostic data before reporting

