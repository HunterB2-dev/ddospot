# DDoSPoT Production Security Checklist

Comprehensive security validation checklist for production deployment of DDoSPoT honeypot system.

## Pre-Deployment Security

### 1. System Hardening
- [ ] **OS Updates**: Latest kernel and security patches installed
  ```bash
  sudo apt update && sudo apt upgrade -y
  uname -r  # Verify kernel version
  ```

- [ ] **SSH Configuration**: Hardened SSH access
  ```bash
  # Verify SSH hardening in /etc/ssh/sshd_config
  sudo cat /etc/ssh/sshd_config | grep -E "PermitRootLogin|PasswordAuthentication|PubkeyAuthentication"
  # Should show: PermitRootLogin no, PasswordAuthentication no, PubkeyAuthentication yes
  ```

- [ ] **SSH Key Setup**: Key-based authentication configured
  ```bash
  ls -la ~/.ssh/authorized_keys
  chmod 600 ~/.ssh/authorized_keys
  ```

- [ ] **User Accounts**: No unnecessary user accounts, strong passwords
  ```bash
  sudo cut -d: -f1 /etc/passwd | sort
  # Review for unexpected users
  ```

- [ ] **Sudo Configuration**: Restricted sudo access, no password-less sudo
  ```bash
  sudo visudo
  # Verify no NOPASSWD entries for privileged commands
  ```

### 2. Firewall Configuration
- [ ] **UFW Enabled**: Firewall active and configured
  ```bash
  sudo ufw status
  # Should show: Status: active
  ```

- [ ] **Firewall Rules**: Only required ports open
  ```bash
  sudo ufw show added
  # Should show: 22/tcp (SSH), 80/tcp (HTTP), 443/tcp (HTTPS)
  ```

- [ ] **Network Isolation**: Internal Docker ports not exposed
  ```bash
  sudo netstat -tlnp | grep LISTEN
  # Only localhost and container networks should bind
  ```

- [ ] **Port Forwarding**: No unnecessary port forwarding rules
  ```bash
  sudo iptables -t nat -L -n
  # Review for suspicious rules
  ```

### 3. Access Control
- [ ] **Root Login Disabled**: SSH root access blocked
  ```bash
  sudo sshctl -T dropbear 2>/dev/null | grep -i root || echo "Root SSH access disabled"
  ```

- [ ] **API Token Generated**: Strong random token created
  ```bash
  openssl rand -hex 32  # Generate token
  # Store in .env.prod as DDOSPOT_API_TOKEN
  ```

- [ ] **Admin Credentials Set**: Nginx basic auth configured
  ```bash
  ls -la /etc/nginx/.htpasswd
  ```

- [ ] **Default Credentials Changed**: Grafana admin password changed
  ```bash
  # Login to Grafana and verify password changed from default
  ```

### 4. Network Security
- [ ] **SSL/TLS Installed**: Valid certificate in place
  ```bash
  sudo certbot certificates
  # Verify certificate is valid and not self-signed (except dev)
  ```

- [ ] **HTTPS Enforced**: All HTTP traffic redirects to HTTPS
  ```bash
  curl -I http://ddospot.example.com
  # Should see 301 redirect to HTTPS
  ```

- [ ] **TLS Version**: Only TLS 1.2+ supported
  ```bash
  sudo openssl s_client -connect localhost:443 < /dev/null
  # Verify TLSv1.2 or TLSv1.3
  ```

- [ ] **Cipher Suite**: Strong ciphers configured
  ```bash
  echo | openssl s_client -connect localhost:443 2>/dev/null | grep "Cipher"
  # Should not contain "NULL" or "EXPORT" ciphers
  ```

- [ ] **HSTS Enabled**: HTTP Strict Transport Security header present
  ```bash
  curl -I https://ddospot.example.com | grep -i "strict-transport"
  # Should return: Strict-Transport-Security: max-age=31536000
  ```

---

## Application Configuration Security

### 5. API Security
- [ ] **Token Authentication**: Required for sensitive endpoints
  ```bash
  grep "DDOSPOT_REQUIRE_TOKEN" /opt/ddospot/.env.prod
  # Should show: DDOSPOT_REQUIRE_TOKEN=true
  ```

- [ ] **Token Validation**: All POST requests require token
  ```bash
  curl -X POST https://ddospot.example.com/api/reset \
    -H "Authorization: Bearer invalid_token"
  # Should return 401 Unauthorized
  ```

- [ ] **Rate Limiting**: Enabled and configured
  ```bash
  grep "DDOSPOT_RATE_LIMIT" /opt/ddospot/.env.prod
  # Should show rate limiting enabled with configured thresholds
  ```

- [ ] **Metrics Endpoint Protected**: Metrics not publicly accessible
  ```bash
  curl https://ddospot.example.com/metrics
  # Should require authentication
  curl -u admin:password https://ddospot.example.com/metrics
  # Should return metrics with credentials
  ```

### 6. Configuration Security
- [ ] **Environment File Locked**: .env.prod has restrictive permissions
  ```bash
  ls -la /opt/ddospot/.env.prod
  # Should show: -rw------- (600)
  ```

- [ ] **Secrets Not in Code**: No hardcoded secrets in application
  ```bash
  grep -r "password\|token\|secret\|key" /opt/ddospot/*.py \
    | grep -v "# " | grep -v ".pyc" || echo "No hardcoded secrets found"
  ```

- [ ] **Debug Mode Disabled**: Flask debug mode off
  ```bash
  grep "DEBUG" /opt/ddospot/dashboard.py
  # Should show: DEBUG = False or not set
  ```

- [ ] **CORS Configured Properly**: Only trusted origins
  ```bash
  grep -A5 "CORS" /opt/ddospot/dashboard.py
  # Should restrict to specific origins or disable if not needed
  ```

---

## Database & Data Security

### 7. Database Protection
- [ ] **Database Encrypted**: At rest encryption enabled (if applicable)
  ```bash
  sqlite3 /var/lib/ddospot/honeypot.db "PRAGMA query_only;"
  # Verify database responds
  ```

- [ ] **Database Permissions**: Restricted file permissions
  ```bash
  ls -la /var/lib/ddospot/honeypot.db
  # Should show: -rw-r--r-- (644) owned by ddospot:ddospot
  ```

- [ ] **SQL Injection Prevention**: Parameterized queries used
  ```bash
  grep -n "execute" /opt/ddospot/core/database.py
  # Verify all queries use parameters, not string concatenation
  ```

- [ ] **Data Retention**: Policy configured
  ```bash
  grep "RETENTION\|DAYS" /opt/ddospot/.env.prod
  # Verify retention policy is documented
  ```

### 8. Backup Security
- [ ] **Backups Encrypted**: Backup archives encrypted at rest
  ```bash
  ls -la /opt/ddospot/backups/
  # Check file permissions
  ```

- [ ] **Backup Retention**: Old backups deleted per policy
  ```bash
  find /opt/ddospot/backups -name "*.tar.gz" -type f
  # Verify reasonable number of recent backups
  ```

- [ ] **Backup Access Restricted**: Backups not publicly accessible
  ```bash
  sudo ls -la /opt/ddospot/backups/
  # Verify not in web root
  ```

- [ ] **Off-site Backup**: Backups replicated to remote storage
  ```bash
  # Verify S3, NAS, or other remote storage configured in backup.sh
  ```

---

## Monitoring & Logging Security

### 9. Logging Configuration
- [ ] **Access Logs Enabled**: Nginx access logs active
  ```bash
  tail -10 /var/log/nginx/ddospot-access.log
  # Should show recent requests
  ```

- [ ] **Error Logs Enabled**: Application error logging
  ```bash
  sudo journalctl -u ddospot-dashboard.service | tail -20
  # Should show application activity
  ```

- [ ] **Log Rotation Configured**: Logs rotated and archived
  ```bash
  sudo cat /etc/logrotate.d/ddospot
  # Verify daily rotation and retention configured
  ```

- [ ] **Sensitive Data Masked**: Passwords/tokens not in logs
  ```bash
  sudo grep -i "password\|token\|secret" /var/log/nginx/ddospot-access.log || echo "No sensitive data in logs"
  ```

### 10. Monitoring & Alerting
- [ ] **Prometheus Scraping**: Metrics collection active
  ```bash
  curl http://localhost:9090/api/v1/targets
  # Should show active targets
  ```

- [ ] **Alert Rules Configured**: Critical alerts defined
  ```bash
  curl http://localhost:9090/api/v1/rules
  # Verify critical alert rules present
  ```

- [ ] **Alerting Channels Tested**: Email/Slack/PagerDuty working
  ```bash
  # Manually trigger test alert and verify delivery
  ```

- [ ] **Alert Response**: On-call procedures documented
  ```bash
  # Verify runbooks and escalation procedures in place
  ```

---

## Service & Process Security

### 11. Service Configuration
- [ ] **Systemd Services Hardened**: Security options enabled
  ```bash
  sudo systemctl cat ddospot-dashboard.service | grep -E "PrivateTmp|ProtectSystem|NoNewPrivileges"
  # Should show security hardening options
  ```

- [ ] **Resource Limits**: Memory and CPU limits configured
  ```bash
  sudo systemctl show ddospot-dashboard.service | grep -E "MemoryLimit|TasksMax"
  # Verify limits set appropriately
  ```

- [ ] **Restart Policy**: Services auto-restart on failure
  ```bash
  sudo systemctl cat ddospot-dashboard.service | grep -E "Restart=|RestartSec="
  # Should show: Restart=on-failure
  ```

- [ ] **Service User**: Running as unprivileged user
  ```bash
  sudo systemctl show -p User ddospot-dashboard.service
  # Should show: User=ddospot (not root)
  ```

### 12. Docker Security
- [ ] **Docker Daemon Configured**: Only trusted users can access
  ```bash
  sudo ls -la /var/run/docker.sock
  # Verify restrictive permissions
  ```

- [ ] **Container Images**: From trusted sources only
  ```bash
  sudo docker images
  # Verify all images are from official or trusted registries
  ```

- [ ] **Container Runtime Limits**: Memory/CPU limits set
  ```bash
  docker inspect <container> | grep -A 10 "HostConfig"
  # Verify Memory and CpuQuota set
  ```

- [ ] **Volume Mounts**: Read-only where appropriate
  ```bash
  docker compose config | grep -A 5 "volumes:"
  # Verify sensitive volumes have :ro flags
  ```

---

## Vulnerability & Compliance

### 13. Dependency Security
- [ ] **No Known Vulnerabilities**: Python packages up to date
  ```bash
  cd /opt/ddospot
  pip check
  # Should return no issues
  ```

- [ ] **Dependency Audit**: Check for outdated packages
  ```bash
  pip list --outdated
  # Review for critical updates
  ```

- [ ] **Security Advisories**: Monitor advisory databases
  ```bash
  # Check CVE databases for Flask, numpy, scikit-learn versions
  ```

### 14. Network Vulnerability Assessment
- [ ] **Port Scan**: Only required ports exposed
  ```bash
  sudo nmap -sV localhost
  # Should only show SSH (22), HTTP (80), HTTPS (443)
  ```

- [ ] **SSL/TLS Scan**: SSL Labs report (if public)
  ```bash
  # Run at https://www.ssllabs.com/ssltest/ for public deployment
  # Target grade: A or A+
  ```

- [ ] **Firewall Rules Audit**: No unnecessary open ports
  ```bash
  sudo ufw status verbose
  # Review each rule for necessity
  ```

### 15. Compliance & Standards
- [ ] **GDPR Compliance**: If handling EU personal data
  ```bash
  # Verify data retention policies
  # Ensure GDPR data processing agreement in place
  ```

- [ ] **Data Classification**: Sensitive data identified and protected
  ```bash
  # Review what data is collected, stored, and transmitted
  ```

- [ ] **Security Policy**: Documented and communicated
  ```bash
  # Verify incident response procedures in place
  ```

---

## Incident Response

### 16. Incident Preparedness
- [ ] **Incident Response Plan**: Documented procedures
  ```bash
  # Verify incident response playbook exists
  ```

- [ ] **Contact Information**: Emergency contacts documented
  ```bash
  # Maintain on-call contact list
  ```

- [ ] **Recovery Procedures**: Tested and validated
  ```bash
  # Perform quarterly disaster recovery drill
  ```

- [ ] **Forensics Preparation**: Logs retained for investigation
  ```bash
  # Verify 30+ day log retention
  ```

---

## Post-Deployment Validation

### 17. Security Testing
- [ ] **Penetration Testing**: Conducted by authorized security team
  ```bash
  # Schedule quarterly penetration tests
  ```

- [ ] **Vulnerability Scan**: Regular automated scans
  ```bash
  # Use Trivy, Snyk, or similar tools
  ```

- [ ] **Configuration Audit**: Security settings verified
  ```bash
  # Use CIS benchmarks or similar frameworks
  ```

### 18. Final Sign-Off
- [ ] **Security Review Complete**: All items verified
- [ ] **Risk Assessment**: Residual risks documented
- [ ] **Approval**: Authorized by security team
- [ ] **Deployment Authorized**: Ready for production

---

## Ongoing Security Maintenance

### Monthly Tasks
- [ ] Review access logs for anomalies
- [ ] Update Python dependencies
- [ ] Verify backup integrity
- [ ] Check certificate expiration (30+ days notice)
- [ ] Review firewall logs

### Quarterly Tasks
- [ ] Penetration testing
- [ ] Disaster recovery drill
- [ ] Security patch review
- [ ] Configuration audit
- [ ] Access control review

### Annual Tasks
- [ ] Full security assessment
- [ ] Compliance audit
- [ ] Incident response plan update
- [ ] Risk assessment update
- [ ] Vendor security review

---

## Security Contacts & Escalation

| Role | Contact | Backup Contact |
|------|---------|-----------------|
| Security Lead | [name] | [name] |
| On-Call Engineer | [name] | [name] |
| Infrastructure Lead | [name] | [name] |
| DBA | [name] | [name] |

---

## Sign-Off

**Reviewed By**: _________________ **Date**: _______

**Authorized By**: _________________ **Date**: _______

**Next Review Date**: _____________________________

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Classification**: Internal Use Only
