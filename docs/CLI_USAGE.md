# DDoSPoT CLI - Command Line Interface

## 🎯 Overview

A comprehensive command-line interface for managing and monitoring the DDoSPoT honeypot system. Features an interactive menu with service management, attack simulation, real-time monitoring, and dashboard integration.

## 🚀 Quick Start

### Launch the CLI

```bash
cd /home/hunter/Projekty/ddospot
./myenv/bin/python3 cli.py
```

### Create an Alias (Recommended)

Add to your `~/.bashrc`:

```bash
alias ddospot='cd /home/hunter/Projekty/ddospot && ./myenv/bin/python3 cli.py'
```

Then reload:

```bash
source ~/.bashrc
```

Now you can simply run:

```bash
ddospot
```

## 📋 Menu Options

### 🚀 SERVICE MANAGEMENT (1-6)

| Option | Command | Description |
|--------|---------|-------------|
| 1 | Start Honeypot Server | Starts the honeypot on ports 22, 53, 80, 123, 1900 |
| 2 | Start Dashboard | Starts Flask web dashboard on port 5000 |
| 3 | Start Both Services | **RECOMMENDED** - Starts everything |
| 4 | Stop Honeypot Server | Gracefully stops the honeypot |
| 5 | Stop Dashboard | Stops the Flask dashboard |
| 6 | Stop All Services | Stops all running services |

### 🎯 ATTACK SIMULATION (7-9)

| Option | Command | Description |
|--------|---------|-------------|
| 7 | Quick Attack | Generates 100 attack events from 3 IPs |
| 8 | Botnet Attack | **RECOMMENDED** - 160 events from 5 countries with geolocation |
| 9 | Custom Attack | Framework for custom simulation (coming soon) |

### 📊 MONITORING & STATUS (10-13)

| Option | Command | Description |
|--------|---------|-------------|
| 10 | System Status | Shows running services and basic stats |
| 11 | Database Statistics | Total events, unique IPs, top protocol |
| 12 | Attack Map Data | Geolocation details for all attacking IPs |
| 13 | Top Attackers | Table of most active attacking IPs |

### 🌐 DASHBOARD & LOGS (14-16)

| Option | Command | Description |
|--------|---------|-------------|
| 14 | Open Dashboard | Opens browser at http://localhost:5000 |
| 15 | View Honeypot Logs | Last 50 lines of /tmp/honeypot.log |
| 16 | View Dashboard Logs | Last 50 lines of /tmp/dashboard.log |

### ⚙️ MAINTENANCE (17-19)

| Option | Command | Description |
|--------|---------|-------------|
| 17 | Reset Database | **WARNING** - Deletes all events! |
| 18 | Cleanup Old Events | Removes events older than 30 days |
| 19 | Check Disk Space | Shows disk usage of project directory |

### ℹ️ HELP & INFO (20, 0)

| Option | Command | Description |
|--------|---------|-------------|
| 20 | Show Help | Displays detailed help and documentation |
| 0 | Exit | Exits the CLI |

## ⚡ Recommended Workflow

### Basic Monitoring

1. **Start the system:**
   ```
   Choose: 3 (Start Both Services)
   ```

2. **Check status:**
   ```
   Choose: 10 (View System Status)
   ```

3. **View dashboard:**
   ```
   Choose: 14 (Open Dashboard)
   ```

### With Attack Simulation

1. **Start the system:**
   ```
   Choose: 3 (Start Both Services)
   ```

2. **Generate attacks:**
   ```
   Choose: 8 (Simulate Botnet Attack)
   ```

3. **Monitor in real-time:**
   ```
   Choose: 14 (Open Dashboard)
   ```

4. **View statistics:**
   ```
   Choose: 11 (View Database Statistics)
   ```

5. **Check attackers:**
   ```
   Choose: 13 (View Top Attackers)
   ```

## 🗺️ Interactive Features

### System Status Display

```
🔍 SYSTEM STATUS

  Honeypot Server:  ✓ RUNNING
  Dashboard API:    ✓ RUNNING
  Database:         ✓ INITIALIZED
  Total Events:     763
  Unique IPs:       13
  Top Protocol:     SSH
```

### Database Statistics

```
📊 DATABASE STATISTICS

  Total Events:        763
  Unique IPs:          13
  Blacklisted IPs:     1
  Top Protocol:        SSH
  Top Port:            22
  Avg Payload Size:    940 bytes

  Top 5 Attacking IPs:
    127.0.0.1             101 events
    192.168.169.219         1 events
```

### Attack Map Data

```
🌍 ATTACK ORIGINS MAP

  Location             IP Address         Events  ISP
  ──────────────────────────────────────────────────────
  Tokyo, Japan         192.0.2.100           48   NTT
  São Paulo, Brazil    198.51.100.75         35   Claro Brasil
  Beijing, China       198.51.100.50         27   China Telecom
  New York, USA        203.0.113.45          26   Verizon
  Moscow, Russia       192.0.2.150           24   Rostelecom
```

## 📂 Files & Locations

### Main Files

- **CLI Script:** `/home/hunter/Projekty/ddospot/cli.py`
- **Database:** `/home/hunter/Projekty/ddospot/honeypot.db`
- **Logs:** `/tmp/honeypot.log` and `/tmp/dashboard.log`

## 🔌 Default Ports

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| HTTP | 80 | TCP | Web server honeypot |
| SSH | 22 | TCP | SSH server honeypot |
| DNS | 53 | UDP | DNS server honeypot |
| NTP | 123 | UDP | NTP server honeypot |
| SSDP | 1900 | UDP | SSDP discovery honeypot |
| Dashboard | 5000 | TCP | Web UI |

## 🎨 Features

### Color-Coded Output

- 🟢 Green: Success messages
- 🟡 Yellow: Warnings and information
- �� Red: Errors
- 🔵 Cyan: Section headers

### Automatic Features

- ✓ Detects if services are already running
- ✓ Prevents duplicate service starts
- ✓ Creates log files automatically
- ✓ Proper process management with signal handling
- ✓ Graceful error handling
- ✓ Real-time status updates

## 📊 Data Visualization

The dashboard displays:

- **Real-time Statistics:** Total events, unique IPs, protocols
- **Attack Timeline:** Graphs showing attacks over time
- **Protocol Breakdown:** Pie chart of protocol distribution
- **World Map:** Interactive Leaflet.js map with attack origins
  - Red circle markers for each location
  - Marker size = attack volume
  - Marker opacity = attack intensity
  - Country-by-country distribution
  - Click markers for detailed information

## 🔗 API Integration

The CLI can work with these API endpoints:

- `GET /api/stats` - System statistics
- `GET /api/top-attackers` - Top attacking IPs
- `GET /api/map-data` - Geolocation coordinates
- `GET /api/country-stats` - Attacks by country
- `GET /api/recent-events` - Recent events
- `GET /api/blacklist` - Blacklisted IPs
- `GET /api/timeline` - Timeline data

## 💡 Tips & Tricks

### View Live Logs

In separate terminal:

```bash
tail -f /tmp/honeypot.log
tail -f /tmp/dashboard.log
```

### Monitor in Real-Time

Use watch command:

```bash
watch -n 1 'ps aux | grep -E "main.py|dashboard.py"'
```

### Check Database Size

From CLI: choose option 19 (Check Disk Space)

### Keep Services Running

Use nohup for persistent operation:

```bash
nohup ./myenv/bin/python3 main.py > /tmp/honeypot.log 2>&1 &
nohup ./myenv/bin/python3 dashboard.py > /tmp/dashboard.log 2>&1 &
```

## 🆘 Troubleshooting

### CLI not executable

```bash
chmod +x /home/hunter/Projekty/ddospot/cli.py
```

### Missing psutil module

```bash
./myenv/bin/pip install psutil
```

### Services won't start

Check if ports are already in use:

```bash
netstat -tuln | grep -E "22|53|80|123|1900|5000"
```

### Dashboard not responding

Check logs:

```bash
tail -f /tmp/dashboard.log
```

## 📚 Additional Resources

- Complete commands: `About DDoSPoT/Commands.txt`
- CLI guide: This file
- Dashboard: http://localhost:5000
- Database: SQLite3 in `honeypot.db`

## ✨ What's Next?

After using the CLI:

1. **Monitor attacks** via the interactive dashboard
2. **Analyze patterns** in the database
3. **Fine-tune detection** based on your environment
4. **Integrate alerts** for real-time notifications
5. **Export data** for further analysis

---

**Created:** January 20, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
