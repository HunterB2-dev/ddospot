# 🚀 Getting Started: Your First Day with DDoSPoT

**A Practical Guide to Your First Honeypot Experience**

---

## ⏱️ Timeline: Your First 24 Hours

### **Hour 1: Setup (Installation)**

#### Step 1.1: Prerequisites Check
```bash
# Check if you have Docker
docker --version

# Check if you have Git
git --version

# Check Python (optional)
python3 --version
```

#### Step 1.2: Clone/Download DDoSPoT
```bash
# Clone from repository
git clone https://github.com/yourusername/ddospot.git

# Navigate to directory
cd ddospot
```

#### Step 1.3: Start DDoSPoT
```bash
# Option 1: Using Docker (Recommended)
docker-compose up -d

# Option 2: Without Docker
python3 start-dashboard.py &
python3 start-honeypot.py &
```

#### Step 1.4: Verify Installation
```bash
# Check if services are running
curl http://localhost:5000

# You should see: Welcome to DDoSPoT Dashboard
```

---

### **Hour 2: Dashboard Exploration**

#### Visit the Dashboard
```
Open browser: http://localhost:5000
Login with default credentials (if configured)
```

#### Explore These Sections

**1. Overview Tab**
```
Shows:
├─ Total attack attempts
├─ Number of unique attackers
├─ Blocked IPs
└─ Detection rate
```

**What to look for**:
- "Total Events" counter
- "Active Threats" indicator
- Recent attack list

**2. Threats Tab**
```
Shows:
├─ Attacker IP addresses
├─ Attack types
├─ Attack count per IP
└─ Geographic location
```

**What to do**:
- Click on an IP to see details
- View attack timestamps
- Check attack patterns

**3. Alerts Tab**
```
Shows:
├─ Alert history
├─ Severity levels (🔴 High, 🟡 Medium, 🔵 Low)
├─ Timestamps
└─ Alert messages
```

**What to check**:
- How many alerts today?
- Alert patterns
- Alert severity distribution

**4. Settings Tab** (if available)
```
Configure:
├─ SSH honeypot port
├─ HTTP honeypot port
├─ Alert thresholds
├─ Notification settings
└─ Response rules
```

---

### **Hour 3: Configuration**

#### Basic Configuration

**1. Set Your Email**
```
Settings → Notifications
Email: your@email.com
Test email: Send test alert
```

**2. Configure Alert Thresholds**
```
Settings → Alert Rules
├─ SSH brute force: 10+ attempts = Alert
├─ HTTP scanning: 5+ requests = Alert  
└─ SSDP scanning: 3+ requests = Alert
```

**3. Enable Automatic Blocking**
```
Settings → Response Actions
├─ Auto-block on: HIGH threat
├─ Block duration: 24 hours
└─ Notification: Send alert when blocked
```

---

### **Hours 4-6: Testing**

#### Simulate an Attack (Safe Testing)

**Test 1: SSH Brute Force Simulation**
```bash
# Connect to honeypot
ssh -p 2222 localhost

# Try a few wrong passwords
# Result: Should see alert in dashboard within 30 seconds
```

**Test 2: Check Monitoring**
```bash
# Look at dashboard
# Should show:
# - 1 source IP (localhost)
# - 1 failed attempt
# - New alert in alerts section
```

**Test 3: Verify Email Alert**
```bash
# Check your email
# Should receive notification about SSH attempt
# Check for:
# - Source IP
# - Attack type
# - Timestamp
```

---

### **Hours 7-12: Let It Run**

#### What Happens?

```
Honeypot Running in Background:

11:00 AM - 1 SSH attempt from somewhere
11:05 AM - 5 HTTP scan requests
11:15 AM - 3 SSDP probes
...continues throughout the day...

Dashboard updates in real-time
Alerts sent as attacks happen
Data logged for analysis
```

#### What You Should Do

1. **Keep checking dashboard** periodically
2. **Look for patterns** in attacks
3. **Note high-volume attacks**
4. **Check source countries**
5. **Monitor alert accuracy**

---

### **Hours 13-24: Analysis**

#### Review Your First Day

**Activity Summary**
```bash
# Questions to answer:

1. How many total events?
2. How many unique attackers?
3. What time was most active?
4. What protocol most attacked?
   (SSH, HTTP, or SSDP)
5. What's the top attacker IP?
6. What geographic region most attacks?
```

**Example Report**
```
DDoSPoT First Day Report
════════════════════════════════════════
Total Events:           1,234
Unique Attackers:         45
Most Active Hour:      2:00 AM
Most Attacked Protocol: SSH (60%)
Top Attacker:    203.0.113.45 (89 attempts)
Top Region:           China (34%)
Blocked IPs:              12
════════════════════════════════════════
```

#### Document Findings
```
Create a file: my_first_day_analysis.txt

Document:
├─ Number of attacks
├─ Attack types observed
├─ Geographic distribution
├─ Notable patterns
└─ Next steps
```

---

## 📱 Mobile Access

### Access from Phone

**On Android**:
```
1. Open Chrome
2. Type: http://your-server-ip:5000
3. Tap menu (⋮)
4. Tap "Install app"
5. Tap "Install"
6. App appears on home screen
```

**On iPhone**:
```
1. Open Safari
2. Navigate to http://your-server-ip:5000
3. Tap Share button
4. Tap "Add to Home Screen"
5. Name it "DDoSPoT"
6. Tap "Add"
7. App appears on home screen
```

**Now you can**:
- Check threats on the go
- Get push notifications
- View dashboard anytime
- Work offline (cached data)

---

## 🔔 Understanding Your First Alerts

### SSH Attack Alert Example

```
ALERT RECEIVED:

Type: SSH Brute Force
Source IP: 203.0.113.45
Count: 47 attempts in 5 minutes
Location: Shanghai, China
Action: Automatic IP block
Threat Level: 🔴 HIGH

What it means:
- Botnet tried to break into SSH
- Used dictionary password attack
- Tried 47 different passwords
- Same usernames (root, admin)
- DDoSPoT blocked them automatically
```

**Your action**: Check if you have SSH port publicly exposed (decide if that's acceptable)

### HTTP Scan Alert Example

```
ALERT RECEIVED:

Type: Web Server Scanning
Source IP: 198.51.100.77
Count: 23 requests in 2 minutes
User Agent: Mozilla (malicious bot)
Threat Level: 🟡 MEDIUM

What it means:
- Scanner probing for vulnerabilities
- Checking common web paths
- Looking for exploitable services
- Automated bot behavior
```

**Your action**: These are common - monitor for patterns

### SSDP Scan Alert Example

```
ALERT RECEIVED:

Type: SSDP Device Discovery
Source IP: 192.0.2.88
Count: 5 requests in 1 minute
Bot Signature: Mirai variant
Threat Level: 🟡 MEDIUM

What it means:
- IoT botnet recruiting
- Looking for vulnerable devices
- Trying to add devices to botnet
- Known malware pattern
```

**Your action**: Secure IoT devices on network

---

## 🎯 Your First Week

### Day 1: Setup & Exploration
```
✅ Install DDoSPoT
✅ Explore dashboard
✅ Configure basics
✅ Run first test
```

### Day 2-3: Observation
```
✅ Watch for natural attacks
✅ Study patterns
✅ Review all alerts
✅ Understand threat types
```

### Day 4-5: Configuration Tuning
```
✅ Adjust alert thresholds
✅ Fine-tune response rules
✅ Add email notifications
✅ Test blocking functionality
```

### Day 6-7: Integration & Planning
```
✅ Integrate with other tools
✅ Set up backup alerts (Slack, SMS)
✅ Plan long-term strategy
✅ Document your setup
```

---

## 📊 Metrics to Track

### Key Performance Indicators

**Daily Tracking**:
```
Date: Feb 5, 2026
├─ Total attacks: 234
├─ Unique IPs: 23
├─ Most attacked: SSH (60%)
└─ Blocked: 15
```

**Weekly Summary**:
```
Week of Feb 1:
├─ Attacks: 1,240
├─ Trend: 🔴 Increasing
├─ Top region: China (40%)
└─ Top attack: SSH brute force
```

**Monthly Reports**:
```
Create monthly summary:
├─ Total threats
├─ Threat trends
├─ Effectiveness rating
└─ Recommendations
```

---

## 🚨 Critical Actions Checklist

### Things You MUST Do

- [ ] Install and start DDoSPoT
- [ ] Access dashboard successfully
- [ ] Configure email notifications
- [ ] Run test attack
- [ ] Verify alert received
- [ ] Check IP blocking works
- [ ] Set up mobile access
- [ ] Document your setup
- [ ] Create incident response plan
- [ ] Schedule daily reviews

### Things You SHOULD Do

- [ ] Monitor dashboard daily
- [ ] Review weekly trends
- [ ] Update firewall rules based on threats
- [ ] Backup configurations
- [ ] Test disaster recovery
- [ ] Train team on alerts
- [ ] Update incident response plan
- [ ] Share threat intelligence

### Things to AVOID

- ❌ Ignoring alerts
- ❌ Not blocking high-risk IPs
- ❌ Neglecting honeypot maintenance
- ❌ Storing sensitive data on honeypot
- ❌ Connecting honeypot to production
- ❌ Running other services on honeypot
- ❌ Disabling notifications
- ❌ Allowing honeypot breakout

---

## 🆘 Troubleshooting Your First Day

### "I don't see any attacks!"

**Possible reasons**:
1. Honeypot not publicly accessible
   - Fix: Check firewall, open ports
   
2. Running on private network
   - Fix: Wait for internal threats or place on internet
   
3. Monitoring not working
   - Fix: Check logs, restart service

**Solution**: Check [21_Troubleshooting.md](21_Troubleshooting.md)

### "Alerts aren't working!"

**Check**:
1. Email configured?
2. Email service running?
3. Firewall blocking outgoing email?
4. SMTP credentials correct?

**Test**: Send test alert manually

### "Dashboard shows errors"

**Solutions**:
1. Restart services
   ```bash
   docker-compose restart
   ```
   
2. Check logs
   ```bash
   docker-compose logs -f
   ```

3. Check database
   ```bash
   sqlite3 ddospot.db "SELECT COUNT(*) FROM threats;"
   ```

---

## 🎓 Learning Resources

### For Your First Week

**Read These Files**:
1. ✅ 01_Introduction_to_Honeypots.md (Already read!)
2. 📖 04_DDoSPoT_Overview.md
3. 📖 05_Protocol_Handlers.md
4. 📖 09_Monitoring_Threats.md

**Try These Exercises**:
1. ✅ Install DDoSPoT
2. ✅ Run test attack
3. ✅ Check alerts
4. ✅ Review dashboard
5. ⏭️ Configure settings
6. ⏭️ Set up notifications
7. ⏭️ Create analysis document

---

## 📈 Success Metrics

**You'll know DDoSPoT is working when**:

```
✅ Dashboard shows attack data
✅ Alerts are generated automatically
✅ IPs are blocked
✅ Email notifications arrive
✅ Mobile app shows live data
✅ You understand the threats
✅ You trust the system
✅ You can explain attacks to others
```

---

## 🎉 Congratulations!

You've now:
- ✅ Installed DDoSPoT
- ✅ Explored the dashboard
- ✅ Configured basic settings
- ✅ Tested the system
- ✅ Analyzed real-world attacks
- ✅ Learned threat detection

**Next Steps**:
1. Continue monitoring
2. Read advanced guides
3. Improve configurations
4. Integrate with other tools
5. Share with your team

---

## 📚 What's Next?

Continue learning with:
- [06_Threat_Detection.md](06_Threat_Detection.md) - How detection works
- [07_Automated_Response.md](07_Automated_Response.md) - Response mechanics
- [10_Configuration_Management.md](10_Configuration_Management.md) - Advanced config
- [11_Machine_Learning_Detection.md](11_Machine_Learning_Detection.md) - ML algorithms

---

**Welcome to the world of active threat detection!** 🛡️

*Last Updated: February 2026*
