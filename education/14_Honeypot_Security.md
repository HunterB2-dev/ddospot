# Honeypot Security: Protecting DDoSPoT Itself

## Overview

Ironically, honeypots themselves need protection. This document covers securing DDoSPoT from honeypot breakouts and malware.

---

## Security Layers

```
┌─────────────────────────────────────┐
│ Internet / Attackers                │
├─────────────────────────────────────┤
│ Layer 1: Network Isolation          │
├─────────────────────────────────────┤
│ Layer 2: System Hardening           │
├─────────────────────────────────────┤
│ Layer 3: Process Isolation          │
├─────────────────────────────────────┤
│ Layer 4: Container Isolation        │
├─────────────────────────────────────┤
│ Layer 5: Monitoring & Detection     │
├─────────────────────────────────────┤
│ Real Systems (Protected)             │
└─────────────────────────────────────┘
```

---

## Layer 1: Network Isolation

### Air Gap (Strongest)

```
Internet
  │
  X (No direct connection)
  
DDoSPoT Network
└─ Completely isolated
   └─ No access to production systems
```

### Segmented Network (Strong)

```
Internet
  │
  ├─ Firewall (Strict rules)
  │
DDoSPoT Segment
├─ Can communicate with: Nothing
├─ Can be accessed from: Monitoring systems only
└─ All outbound blocked (except logging)
```

### DMZ Deployment (Recommended)

```
Internet
  │
  ├─ Perimeter Firewall
  │
DMZ Zone
├─ DDoSPoT
├─ Can reach: Monitoring network only
├─ Cannot reach: Internal network
└─ Only ports 2222, 8888, 1900 inbound
  │
Internal Firewall
  │
Internal Network
└─ Production Systems (Safe)
```

### Configuration Example

```bash
# Firewall rules for DDoSPoT network isolation

# Inbound: Only allow attacker connections
sudo ufw allow 2222/tcp  # SSH honeypot
sudo ufw allow 8888/tcp  # HTTP honeypot
sudo ufw allow 1900/udp  # SSDP honeypot
sudo ufw allow 22/tcp    # Admin SSH (restricted IPs)
sudo ufw allow 5000/tcp  # Dashboard (restricted IPs)

# Outbound: Only allow logging and updates
sudo ufw default deny outgoing
sudo ufw allow out to <monitoring-server>
sudo ufw allow out to security.ubuntu.com  # Updates only
sudo ufw allow out dns                     # DNS only

# Reject everything else
sudo ufw default deny incoming
sudo ufw default deny outgoing

# Enable firewall
sudo ufw enable
```

---

## Layer 2: System Hardening

### Minimal OS

```
Principle: Run only what's necessary

Traditional Linux: 5,000+ packages
Hardened Linux: 200-300 packages

Include only:
├─ Kernel
├─ Python runtime
├─ Network stack
├─ SSH for admin
├─ Logging tools
└─ Monitoring agent

Exclude:
├─ Development tools
├─ Compilers
├─ Package managers
├─ Web servers
├─ Interpreters (except Python)
└─ Unnecessary libraries
```

### Immutable System

```
Make filesystem read-only:

Boot behavior:
1. System mounts / as read-only
2. Only /var and /tmp writable
3. Cannot install new packages
4. Cannot modify binaries
5. Cannot change configuration

Impact on attackers:
├─ Cannot install rootkits
├─ Cannot modify system files
├─ Cannot install backdoors
└─ Limited to /tmp (cleared on reboot)
```

### SELinux / AppArmor

```
Mandatory Access Control: Restrict even root

Policy Example:
├─ Python process: Can only read specific files
├─ Python process: Can only write to /var/log
├─ Python process: Cannot execute binaries
├─ Python process: Cannot modify system files
└─ Result: If Python compromised, damage is limited
```

---

## Layer 3: Process Isolation

### Jailed Execution

```
Run honeypot in chroot jail:

Normal filesystem:
├─ / (root)
├─ /bin, /usr, /etc
├─ /home
└─ /var

Jailed filesystem:
├─ /jail/honeypot/ (becomes /)
├─ /jail/honeypot/bin
├─ /jail/honeypot/etc
├─ /jail/honeypot/var
└─ Cannot access anything outside /jail
```

### Process Capabilities

```
Instead of running as root:
├─ Run as unprivileged user
├─ Drop unnecessary capabilities
├─ Keep only what's needed

Capability Example:
├─ Need: CAP_NET_BIND_SERVICE (bind to port)
├─ Drop: CAP_SYS_ADMIN, CAP_SYS_TIME, etc.
├─ Result: Limited damage if compromised
```

---

## Layer 4: Container Isolation

### Docker Isolation

```
Attack path blocked at Docker level:

Attacker gains shell:
├─ Attempts to: modify /etc/passwd
├─ Docker blocks: /etc is read-only
├─ Attempts to: install malware
├─ Docker blocks: cannot execute from /tmp
├─ Attempts to: access host
├─ Docker blocks: cannot access ../../ (bind mount)
└─ Result: Trapped in container
```

### Container Hardening

```dockerfile
# Hardened DDoSPoT Dockerfile

FROM python:3.10-slim
WORKDIR /app

# Add security scanner
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN useradd -m -u 1000 honeypot

# Copy application
COPY --chown=honeypot:honeypot . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to unprivileged user
USER honeypot

# Remove setuid bits
RUN find / -perm /4000 -type f -delete 2>/dev/null || true

# Security options
SECURITY_OPT=
  --security-opt=no-new-privileges:true
  --security-opt=apparmor=docker-default
  --cap-drop=ALL
  --cap-add=NET_BIND_SERVICE

CMD ["python", "start-honeypot.py"]
```

### Kubernetes Security

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ddospot-honeypot
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsReadOnlyRootFilesystem: true
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: honeypot
    image: ddospot:latest
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
      readOnlyRootFilesystem: true
    
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: logs
      mountPath: /var/log
  
  volumes:
  - name: tmp
    emptyDir: {}
  - name: logs
    emptyDir: {}
```

---

## Layer 5: Monitoring & Detection

### Self-Monitoring

```
DDoSPoT monitors itself:

Processes:
├─ Normal: Python, logging
├─ Alert: New processes spawned
└─ Block: Kill unexpected processes

Network:
├─ Normal: Inbound SSH, HTTP, SSDP
├─ Alert: Outbound connection attempts
└─ Block: Drop unauthorized outbound

Filesystem:
├─ Normal: Read-only system, log writes
├─ Alert: Attempts to modify system files
└─ Block: Prevent unauthorized writes

Memory:
├─ Normal: Stable memory usage
├─ Alert: Abnormal spikes
└─ Block: Kill process if exceeds limit
```

### Integrity Monitoring

```
File integrity checking:

On startup:
├─ Calculate hash of all system files
├─ Store in protected location
└─ Baseline created

Continuously:
├─ Monitor critical files for changes
├─ SSH: /var/log/honeypot/ssh.log
├─ HTTP: /var/log/honeypot/http.log
├─ Config: /etc/ddospot/config.json
└─ Alert on any change
```

### Anomaly Detection

```
Detect abnormal honeypot behavior:

CPU Usage:
├─ Normal: 5-15%
├─ Alert: 80%+ sustained
├─ Action: Check for CPU-based exploit

Memory Usage:
├─ Normal: 200-300 MB
├─ Alert: > 1 GB
├─ Action: Check for memory bomb

Network:
├─ Normal: Inbound only (controlled)
├─ Alert: Outbound to unusual IPs
├─ Action: Check for reverse shell

Disk:
├─ Normal: Growing slowly (logs)
├─ Alert: Sudden large writes
├─ Action: Check for payload detonation
```

---

## Preventing Breakouts

### What is a Breakout?

```
Breakout: Attacker escapes from honeypot

Normal Scenario:
Attacker →[Honeypot]← Isolated

Breakout Scenario:
Attacker →[Honeypot]→ Reaches production systems

Prevention:
├─ Network isolation (most important)
├─ System hardening
├─ Process limitations
├─ Container isolation
└─ Monitoring (detect if still happens)
```

### Common Breakout Attempts

#### 1. Privilege Escalation

```
Attack: Attacker exploits OS vulnerability to become root

Example: CVE-2021-22911 (Linux privilege escalation)

DDoSPoT Defense:
├─ Run as unprivileged user
├─ Use AppArmor/SELinux
├─ Keep OS patched
├─ Monitor privilege changes
└─ Kill process if escalation detected
```

#### 2. Container Escape

```
Attack: Attacker breaks out of Docker container

Example: Docker socket access

DDoSPoT Defense:
├─ Do NOT expose Docker socket
├─ Do NOT run container as root
├─ Do NOT use --privileged flag
├─ Use read-only root filesystem
└─ Limit capabilities (--cap-drop=ALL)
```

#### 3. Kernel Exploitation

```
Attack: Attacker exploits kernel to escape container

Example: Memory corruption bug

DDoSPoT Defense:
├─ Use seccomp profiles (limit syscalls)
├─ Keep kernel patched
├─ Minimal syscall surface
├─ Monitor unusual syscalls
└─ Run under different kernel namespace
```

### Configuration: Strict Lockdown

```json
{
  "security": {
    "honeypot_isolation": {
      "network": {
        "allow_inbound": ["2222", "8888", "1900"],
        "allow_outbound": "none",
        "block_internal_access": true
      },
      "process": {
        "run_as_user": "honeypot",
        "drop_capabilities": ["ALL"],
        "limit_syscalls": true,
        "max_memory_mb": 512,
        "max_cpu_percent": 80
      },
      "filesystem": {
        "read_only_root": true,
        "writable_paths": ["/var/log", "/tmp"],
        "monitor_critical_files": true
      },
      "container": {
        "privileged": false,
        "no_new_privileges": true,
        "security_opt": "apparmor=docker-default"
      }
    }
  }
}
```

---

## Detection Examples

### Example 1: Breakout Attempt Detected

```
Timeline:

12:00:00
  DDoSPoT processes normal
  SSH: Running as user 'honeypot'
  Memory: 250 MB

12:05:15
  SSH handler receives special payload
  Attempts: whoami
  Normal response: returns nothing (no shell)

12:05:20
  Alert: Process 'bash' spawned from honeypot
  Normal: Only Python should run
  Action: Immediate process termination
  Reason: Unsupported process execution

12:05:25
  Attempt 2: Process execution blocked
  Attacker tries again with: /bin/sh
  Result: Blocked (no new processes allowed)

12:05:30
  Attempt 3: Memory corruption exploit
  Monitor detects: Unusual system calls
  AppArmor blocks: Unauthorized syscalls
  Result: Process killed

12:05:35
  Final Status:
  ├─ Honeypot process restarted (auto-recovery)
  ├─ Attacker disconnected
  ├─ Incident logged with full details
  ├─ Alert sent to security team
  └─ Attack attempt recorded in database

Conclusion: Breakout prevented by layered security
```

### Example 2: Malware Analysis

```
Timeline:

Attack: Attacker uploads malware

Sequence:
1. HTTP request to upload endpoint
2. Contains suspicious binary payload
3. DDoSPoT accepts upload (honeypot behavior)
4. Stores in isolated /tmp directory
5. Malware cannot execute:
   ├─ /tmp is noexec mount
   ├─ Process cannot run binaries from /tmp
   ├─ AppArmor prevents execution
   └─ Docker prevents execution

Analysis:
├─ Honeypot captures malware sample
├─ Stores for analysis
├─ Cannot harm honeypot
├─ Cannot spread to other systems
└─ Security team receives alert

Result: Malware captured safely
```

---

## Best Practices

### 1. Defense in Depth

```
Don't rely on single security layer:
├─ Network isolation + System hardening
├─ + Process restrictions + Container isolation
├─ + Monitoring + Detection = Secure honeypot

Even if one layer fails:
├─ Others stop the attack
└─ Damage is contained
```

### 2. Regular Updates

```
Keep everything current:
├─ Linux kernel patches
├─ Container runtime updates
├─ Security tool upgrades
└─ Dependency updates

Schedule:
├─ Weekly: Security patches
├─ Monthly: Full system updates
└─ Quarterly: Major version upgrades
```

### 3. Regular Testing

```
Verify security measures:
├─ Attempt to break out
├─ Try known exploits
├─ Check isolation
├─ Verify monitoring
└─ Update based on findings
```

---

## Key Takeaways

1. **Layered Defense**: Multiple security layers needed
2. **Network Isolation**: Most critical control
3. **System Hardening**: Minimize attack surface
4. **Container Isolation**: Add extra protection
5. **Monitoring**: Detect what slips through

---

## Next Steps

- **Setup**: [Setting Up DDoSPoT](08_Setting_Up_DDoSPoT.md)
- **Deployment**: [Deployment Guide](18_Deployment_Guide.md)
- **Incident Response**: [Incident Response](15_Incident_Response.md)
- **Monitoring**: [Monitoring and Alerting](19_Monitoring_and_Alerting.md)

---

## Review Questions

1. What are the five security layers?
2. Why is network isolation most important?
3. What is a breakout and how can it be prevented?
4. How does a read-only filesystem help?
5. What self-monitoring should a honeypot have?

## Additional Resources

- OWASP Container Security
- Docker Security Best Practices
- Kubernetes Security Policies
- Honeypot Isolation Techniques
