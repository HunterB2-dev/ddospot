#!/usr/bin/env python3
"""
DDoSPoT CLI - Command Line Interface for the honeypot system
Provides interactive menu for managing, monitoring, and testing the honeypot
"""

import os
import signal
import sys
import socket
import subprocess
import time
import psutil
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import HoneypotDatabase
from core.geolocation import GeolocationService
import random


class Colors:
    """ANSI color codes"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_banner():
    """Print the DDoSPoT banner in large ASCII art without border"""
    banner = f"""{Colors.BOLD}

{Colors.RED}██████╗ ██████╗  ██████╗ ███████╗{Colors.WHITE}██████╗  ██████╗ {Colors.BLACK}████████╗
{Colors.RED}██╔══██╗██╔══██╗██╔═══██╗██╔════╝{Colors.WHITE}██╔══██╗██╔═══██╗{Colors.BLACK}╚══██╔══╝
{Colors.RED}██║  ██║██║  ██║██║   ██║███████╗{Colors.WHITE}██████╔╝██║   ██║{Colors.BLACK}   ██║   
{Colors.RED}██║  ██║██║  ██║██║   ██║╚════██║{Colors.WHITE}██╔═══╝ ██║   ██║{Colors.BLACK}   ██║   
{Colors.RED}██████╔╝██████╔╝╚██████╔╝███████║{Colors.WHITE}██║     ╚██████╔╝{Colors.BLACK}   ██║   
{Colors.RED}╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝{Colors.WHITE}╚═╝      ╚═════╝{Colors.BLACK}    ╚═╝{Colors.RESET}

    🍯 Advanced DDoS/DoS Attack Honeypot System 🍯
       Real-time Threat Intelligence & Analysis

{Colors.RESET}
"""
    print(banner)


def print_menu():
    """Print the main menu"""
    menu = f"""
{Colors.BOLD}{Colors.YELLOW}╔══════════════════════════════════════════════════════════╗{Colors.RESET}
{Colors.BOLD}{Colors.YELLOW}║{Colors.RESET}            {Colors.BOLD}MAIN MENU - SELECT AN OPTION{Colors.RESET}            {Colors.BOLD}{Colors.YELLOW}║{Colors.RESET}
{Colors.BOLD}{Colors.YELLOW}╚══════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.CYAN}🚀 SERVICE MANAGEMENT:{Colors.RESET}
  {Colors.GREEN}1{Colors.RESET}. Start Honeypot Server
  {Colors.GREEN}2{Colors.RESET}. Start Dashboard (Web UI)
  {Colors.GREEN}3{Colors.RESET}. Start Both Services
  {Colors.GREEN}4{Colors.RESET}. Stop Honeypot Server
  {Colors.GREEN}5{Colors.RESET}. Stop Dashboard
  {Colors.GREEN}6{Colors.RESET}. Stop All Services

{Colors.CYAN}🎯 ATTACK SIMULATION:{Colors.RESET}
  {Colors.GREEN}7{Colors.RESET}. Simulate Quick Attack (100 events)
  {Colors.GREEN}8{Colors.RESET}. Simulate Botnet Attack (5 locations)
  {Colors.GREEN}9{Colors.RESET}. Simulate Custom Attack

{Colors.CYAN}📊 MONITORING & STATUS:{Colors.RESET}
  {Colors.GREEN}10{Colors.RESET}. View System Status
  {Colors.GREEN}11{Colors.RESET}. View Database Statistics
  {Colors.GREEN}12{Colors.RESET}. View Attack Map Data
  {Colors.GREEN}13{Colors.RESET}. View Top Attackers

{Colors.CYAN}🌐 DASHBOARD & LOGS:{Colors.RESET}
  {Colors.GREEN}14{Colors.RESET}. Open Dashboard (http://localhost:5000)
  {Colors.GREEN}15{Colors.RESET}. View Honeypot Logs
  {Colors.GREEN}16{Colors.RESET}. View Dashboard Logs

{Colors.CYAN}⚙️  MAINTENANCE:{Colors.RESET}
  {Colors.GREEN}17{Colors.RESET}. Reset Database
  {Colors.GREEN}18{Colors.RESET}. Cleanup Old Events
    {Colors.GREEN}19{Colors.RESET}. Check Disk Space
    {Colors.GREEN}21{Colors.RESET}. Rotate Logs Now
    {Colors.GREEN}22{Colors.RESET}. Health Check

{Colors.CYAN}ℹ️  HELP & INFO:{Colors.RESET}
  {Colors.GREEN}20{Colors.RESET}. Show Help
  {Colors.GREEN}0{Colors.RESET}. Exit

{Colors.YELLOW}Enter your choice (0-22):{Colors.RESET} """
    return menu


def _get_api_token() -> str | None:
    """Read API token from environment or config file.
    
    Priority: env var > config.json > None
    """
    import json
    
    token = os.getenv("DDOSPOT_API_TOKEN")
    if token:
        return str(token).strip()
    
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                api_config = config.get("api", {})
                token = api_config.get("token")
                if token:
                    return str(token).strip()
        except Exception:
            pass
    
    return None


def _log_rotation_settings():
    """Read log rotation settings from config file or environment with sane defaults.
    
    Priority: env vars > config.json > defaults
    """
    import json
    
    defaults = {
        "max_bytes": 5 * 1024 * 1024,
        "backups": 2
    }
    
    # Try loading from config file
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                log_config = config.get("log_rotation", {})
                defaults["max_bytes"] = log_config.get("max_bytes", defaults["max_bytes"])
                defaults["backups"] = log_config.get("backups", defaults["backups"])
        except Exception:
            pass
    
    # Environment variables override config file
    def _parse(name: str, default: int) -> int:
        try:
            value = int(os.getenv(name, "").strip() or 0)
            return value if value > 0 else default
        except Exception:
            return default
    
    max_bytes = _parse("DDOSPOT_LOG_MAX_BYTES", defaults["max_bytes"])
    backups = _parse("DDOSPOT_LOG_BACKUPS", defaults["backups"])
    return max_bytes, backups


def rotate_log(logfile: Path, max_bytes: int = 5 * 1024 * 1024, backups: int = 2, force: bool = False):
    """Truncate or rotate log file when exceeding max_bytes or when forced."""
    try:
        if not logfile.exists() and not force:
            return

        logfile.touch(exist_ok=True)
        if force or logfile.stat().st_size > max_bytes:
            for i in range(backups, 0, -1):
                older = logfile.with_suffix(f".log.{i}") if logfile.suffix == ".log" else Path(f"{logfile}.{i}")
                newer = logfile.with_suffix(f".log.{i - 1}") if logfile.suffix == ".log" else Path(f"{logfile}.{i - 1}")
                if i == 1:
                    newer = logfile
                if newer.exists():
                    older.unlink(missing_ok=True)
                    newer.rename(older)
            logfile.touch()
    except Exception:
        pass


def get_process_pid(name: str):
    """Get PID of a process by name"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if name.lower() in ' '.join(proc.info['cmdline'] or []).lower():
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None


def is_service_running(name: str) -> bool:
    """Check if a service is running"""
    return get_process_pid(name) is not None


def print_status():
    """Print system status"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 SYSTEM STATUS{Colors.RESET}\n")
    
    honeypot_running = is_service_running("main.py")
    dashboard_running = is_service_running("dashboard.py")
    
    honeypot_status = f"{Colors.GREEN}✓ RUNNING{Colors.RESET}" if honeypot_running else f"{Colors.RED}✗ STOPPED{Colors.RESET}"
    dashboard_status = f"{Colors.GREEN}✓ RUNNING{Colors.RESET}" if dashboard_running else f"{Colors.RED}✗ STOPPED{Colors.RESET}"
    
    print(f"  Honeypot Server:  {honeypot_status}")
    print(f"  Dashboard API:    {dashboard_status}")
    
    try:
        db = HoneypotDatabase("honeypot.db")
        stats = db.get_statistics()
        print(f"  Database:         {Colors.GREEN}✓ INITIALIZED{Colors.RESET}")
        print(f"  Total Events:     {Colors.YELLOW}{stats.get('total_events', 0)}{Colors.RESET}")
        print(f"  Unique IPs:       {Colors.YELLOW}{stats.get('unique_ips', 0)}{Colors.RESET}")
        print(f"  Top Protocol:     {Colors.YELLOW}{stats.get('top_protocol', 'N/A')}{Colors.RESET}")
    except Exception as e:
        print(f"  Database:         {Colors.RED}✗ ERROR{Colors.RESET}")
    
    # Log file status
    print(f"\n  {Colors.BOLD}Log Files:{Colors.RESET}")
    logs = [
        ("Honeypot", Path("/tmp/honeypot.log")),
        ("Dashboard", Path("/tmp/dashboard.log"))
    ]
    
    for name, log_path in logs:
        if log_path.exists():
            size_bytes = log_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_bytes / 1024:.1f} KB"
            print(f"    {name:10} {Colors.CYAN}{log_path}{Colors.RESET} ({Colors.YELLOW}{size_str}{Colors.RESET})")
        else:
            print(f"    {name:10} {Colors.YELLOW}Not found{Colors.RESET}")
    
    print()


def start_service(service_name: str, script: str):
    """Start a service"""
    if is_service_running(script):
        print(f"{Colors.YELLOW}ℹ️  {service_name} is already running{Colors.RESET}\n")
        return

    script_path = Path(__file__).parent / script
    logfile = Path("/tmp") / f"{script_path.stem}.log"
    expected_ports = {
        "dashboard.py": 5000,
    }

    try:
        max_bytes, backups = _log_rotation_settings()
        rotate_log(logfile, max_bytes=max_bytes, backups=backups)
        with open(logfile, "a") as log_handle:
            subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=script_path.parent
            )
        deadline = time.time() + 5
        while time.time() < deadline and not is_service_running(script):
            time.sleep(0.2)

        if not is_service_running(script):
            print(f"{Colors.RED}✗ {service_name} failed to start (process not found){Colors.RESET}\n")
            return

        port = expected_ports.get(script)
        if port:
            port_deadline = time.time() + 5
            port_ready = False
            while time.time() < port_deadline:
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                        port_ready = True
                        break
                except OSError:
                    time.sleep(0.3)
            if not port_ready:
                print(f"{Colors.YELLOW}ℹ️  {service_name} started but port {port} not reachable yet{Colors.RESET}\n")
                return

        print(f"{Colors.GREEN}✓ {service_name} started successfully{Colors.RESET}")
        print(f"{Colors.CYAN}  Log: {logfile}{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to start {service_name}: {e}{Colors.RESET}\n")


def stop_service(service_name: str, script: str):
    """Stop a service"""
    pid = get_process_pid(script)
    if not pid:
        print(f"{Colors.YELLOW}ℹ️  {service_name} is not running{Colors.RESET}\n")
        return
    
    try:
        os.kill(pid, signal.SIGTERM)
        deadline = time.time() + 5
        while time.time() < deadline and psutil.pid_exists(pid):
            time.sleep(0.2)
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.3)

        if psutil.pid_exists(pid):
            print(f"{Colors.RED}✗ Failed to stop {service_name}: process still running{Colors.RESET}\n")
        else:
            print(f"{Colors.GREEN}✓ {service_name} stopped successfully{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to stop {service_name}: {e}{Colors.RESET}\n")


def simulate_quick_attack():
    """Simulate a quick attack with 100 events"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🎯 SIMULATING QUICK ATTACK{Colors.RESET}\n")
    
    db = HoneypotDatabase("honeypot.db")
    
    attackers = ["10.0.1." + str(random.randint(1, 254)) for _ in range(3)]
    protocols = ["HTTP", "DNS", "SSH", "NTP", "SSDP"]
    ports = {"HTTP": 80, "DNS": 53, "SSH": 22, "NTP": 123, "SSDP": 1900}
    
    print("  Generating attack events...")
    for i in range(100):
        proto = random.choice(protocols)
        ip = random.choice(attackers)
        db.add_event(
            source_ip=ip,
            port=ports[proto],
            protocol=proto,
            payload_size=random.randint(100, 1000),
            event_type="attack"
        )
        if (i + 1) % 25 == 0:
            print(f"  {Colors.YELLOW}{i + 1}/100{Colors.RESET} events generated...")
    
    stats = db.get_statistics()
    print(f"\n{Colors.GREEN}✓ Attack simulation complete!{Colors.RESET}")
    print(f"  Total Events: {Colors.CYAN}{stats['total_events']}{Colors.RESET}")
    print(f"  Unique IPs: {Colors.CYAN}{stats['unique_ips']}{Colors.RESET}\n")


def simulate_botnet_attack():
    """Simulate a distributed botnet attack"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🌍 SIMULATING BOTNET ATTACK{Colors.RESET}\n")
    
    db = HoneypotDatabase("honeypot.db")
    geo = GeolocationService()
    
    test_locations = [
        ("203.0.113.45", {"country": "United States", "region": "New York", "city": "New York", "lat": 40.7128, "lon": -74.0060, "isp": "Verizon", "org": "Verizon Communications", "as": "AS701"}),
        ("198.51.100.50", {"country": "China", "region": "Beijing", "city": "Beijing", "lat": 39.9042, "lon": 116.4074, "isp": "China Telecom", "org": "China Telecom", "as": "AS4134"}),
        ("192.0.2.100", {"country": "Japan", "region": "Tokyo", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503, "isp": "NTT", "org": "NTT Communications", "as": "AS2914"}),
        ("192.0.2.150", {"country": "Russia", "region": "Moscow", "city": "Moscow", "lat": 55.7558, "lon": 37.6173, "isp": "Rostelecom", "org": "Rostelecom", "as": "AS12389"}),
        ("198.51.100.75", {"country": "Brazil", "region": "São Paulo", "city": "São Paulo", "lat": -23.5505, "lon": -46.6333, "isp": "Claro Brasil", "org": "Claro Brasil", "as": "AS27595"}),
    ]
    
    print("  Caching geolocation data...")
    for ip, geo_data in test_locations:
        geo.cache.set(ip, geo_data)
        print(f"    {Colors.GREEN}✓{Colors.RESET} {ip} ({geo_data['country']})")
    
    print("\n  Generating attack events from each location...")
    protocols = ["HTTP", "DNS", "SSH", "NTP", "SSDP"]
    ports = {"HTTP": 80, "DNS": 53, "SSH": 22, "NTP": 123, "SSDP": 1900}
    
    for ip, geo_data in test_locations:
        events = random.randint(20, 50)
        for _ in range(events):
            proto = random.choice(protocols)
            db.add_event(
                source_ip=ip,
                port=ports[proto],
                protocol=proto,
                payload_size=random.randint(100, 5000),
                event_type="attack"
            )
        print(f"    {Colors.GREEN}✓{Colors.RESET} {geo_data['country']}: {events} events")
    
    print("\n  Attack distribution:")
    map_data = geo.cache.get_map_data()
    for point in map_data:
        print(f"    {Colors.CYAN}{point['country']:20}{Colors.RESET} {Colors.YELLOW}{point['events']:3}{Colors.RESET} events")
    
    print(f"\n{Colors.GREEN}✓ Botnet simulation complete!{Colors.RESET}\n")


def simulate_custom_attack():
    """Simulate a custom attack with user-defined parameters"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🛠️  CUSTOM ATTACK SIMULATION{Colors.RESET}\n")

    try:
        total_events = int(input("Number of events to generate (e.g., 200): ").strip() or "0")
        attacker_count = int(input("Number of attacker IPs (e.g., 5): ").strip() or "0")
        protocols_input = input("Protocols to include (comma-separated, default HTTP,DNS,SSH,NTP,SSDP): ").strip()
        if total_events <= 0 or attacker_count <= 0:
            print(f"{Colors.RED}✗ Invalid input. Values must be positive.{Colors.RESET}\n")
            return

        protocols = [p.strip().upper() for p in protocols_input.split(',') if p.strip()] or ["HTTP", "DNS", "SSH", "NTP", "SSDP"]
        ports = {
            "HTTP": 80,
            "DNS": 53,
            "SSH": 22,
            "NTP": 123,
            "SSDP": 1900,
        }

        attackers = [f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}" for _ in range(attacker_count)]

        db = HoneypotDatabase("honeypot.db")
        print(f"Generating {total_events} events from {attacker_count} attackers across {len(protocols)} protocol(s)...")

        for i in range(total_events):
            proto = random.choice(protocols)
            ip = random.choice(attackers)
            port = ports.get(proto, random.randint(1024, 65535))
            db.add_event(
                source_ip=ip,
                port=port,
                protocol=proto,
                payload_size=random.randint(100, 5000),
                event_type="attack"
            )
            if (i + 1) % max(1, total_events // 4) == 0:
                print(f"  {Colors.YELLOW}{i + 1}/{total_events}{Colors.RESET} events generated...")

        stats = db.get_statistics()
        print(f"\n{Colors.GREEN}✓ Custom attack simulation complete!{Colors.RESET}")
        print(f"  Total Events: {Colors.CYAN}{stats['total_events']}{Colors.RESET}")
        print(f"  Unique IPs: {Colors.CYAN}{stats['unique_ips']}{Colors.RESET}\n")
    except ValueError:
        print(f"{Colors.RED}✗ Invalid number entered. Aborting custom simulation.{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Error during custom simulation: {e}{Colors.RESET}\n")


def cleanup_old_events_cli():
    """Cleanup old events and vacuum the database"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🧹 CLEANUP OLD EVENTS{Colors.RESET}\n")

    try:
        days = input("Delete events older than how many days? (default 30): ").strip()
        days_int = int(days) if days else 30
        if days_int <= 0:
            print(f"{Colors.RED}✗ Invalid value. Days must be positive.{Colors.RESET}\n")
            return

        db = HoneypotDatabase("honeypot.db")
        removed = db.cleanup_old_events(days_int)
        db.vacuum()
        size_info = db.get_database_size()

        print(f"{Colors.GREEN}✓ Cleanup complete{Colors.RESET}")
        print(f"  Removed events: {Colors.YELLOW}{removed}{Colors.RESET}")
        print(f"  Cutoff: {Colors.CYAN}{days_int} day(s){Colors.RESET}\n")
        print(f"  DB size: {Colors.CYAN}{size_info['size_mb']} MB{Colors.RESET} | Events: {Colors.CYAN}{size_info['event_count']}{Colors.RESET} | Profiles: {Colors.CYAN}{size_info['profile_count']}{Colors.RESET}")
        print(f"  File: {Colors.YELLOW}{size_info['file_path']}{Colors.RESET}\n")
    except ValueError:
        print(f"{Colors.RED}✗ Invalid number entered. Aborting cleanup.{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Error during cleanup: {e}{Colors.RESET}\n")


def rotate_logs_now():
    """Force rotate honeypot and dashboard logs immediately."""

    logs = [Path("/tmp/honeypot.log"), Path("/tmp/dashboard.log")]
    max_bytes, backups = _log_rotation_settings()

    for log in logs:
        rotate_log(log, max_bytes=max_bytes, backups=backups, force=True)
        print(f"Rotated: {Colors.CYAN}{log}{Colors.RESET} (max_bytes={max_bytes}, backups={backups})")
    print()


def health_check():
    """Perform comprehensive health check on services."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🏥 HEALTH CHECK{Colors.RESET}\n")
    
    services = [
        ("Honeypot Server", "main.py", None, Path("/tmp/honeypot.log")),
        ("Dashboard", "dashboard.py", 5000, Path("/tmp/dashboard.log"))
    ]
    
    for name, script, port, log_path in services:
        print(f"{Colors.BOLD}{name}:{Colors.RESET}")
        
        # Check process
        pid = get_process_pid(script)
        if pid:
            print(f"  PID:      {Colors.GREEN}✓{Colors.RESET} {pid}")
        else:
            print(f"  PID:      {Colors.RED}✗ Not running{Colors.RESET}")
            print()
            continue
        
        # Check port if applicable
        if port:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    print(f"  Port {port}: {Colors.GREEN}✓ Reachable{Colors.RESET}")
            except OSError:
                print(f"  Port {port}: {Colors.RED}✗ Unreachable{Colors.RESET}")
        
        # Check metrics endpoint for dashboard
        if name == "Dashboard" and port:
            try:
                import urllib.request
                url = f"http://127.0.0.1:{port}/metrics"
                req = urllib.request.Request(url)
                
                # Add token header if available
                token = _get_api_token()
                if token:
                    req.add_header("Authorization", f"Bearer {token}")
                
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        print(f"  Metrics:  {Colors.GREEN}✓ {url}{Colors.RESET}")
                    else:
                        print(f"  Metrics:  {Colors.YELLOW}✗ HTTP {response.status}{Colors.RESET}")
            except Exception as e:
                import urllib.error
                if isinstance(e, urllib.error.HTTPError):
                    if e.code == 401:
                        print(f"  Metrics:  {Colors.YELLOW}✗ Requires token (set DDOSPOT_API_TOKEN){Colors.RESET}")
                    elif e.code == 429:
                        print(f"  Metrics:  {Colors.YELLOW}✗ Rate limited{Colors.RESET}")
                    else:
                        print(f"  Metrics:  {Colors.YELLOW}✗ HTTP {e.code}{Colors.RESET}")
                else:
                    print(f"  Metrics:  {Colors.YELLOW}✗ Unavailable{Colors.RESET}")
        
        # Check log file
        if log_path.exists():
            size_bytes = log_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_bytes / 1024:.1f} KB"
            print(f"  Log:      {Colors.GREEN}✓{Colors.RESET} {log_path} ({size_str})")
            
            # Show last 3 lines
            try:
                result = subprocess.run(["tail", "-3", str(log_path)], capture_output=True, text=True, timeout=2)
                if result.stdout.strip():
                    print(f"  {Colors.CYAN}Recent:{Colors.RESET}")
                    for line in result.stdout.strip().split('\n')[-3:]:
                        truncated = line[:80] + '...' if len(line) > 80 else line
                        print(f"    {Colors.YELLOW}{truncated}{Colors.RESET}")
            except Exception:
                pass
        else:
            print(f"  Log:      {Colors.YELLOW}✗ Not found{Colors.RESET}")
        
        print()
    
    print()


def view_database_stats():
    """View database statistics"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}📊 DATABASE STATISTICS{Colors.RESET}\n")
    
    try:
        db = HoneypotDatabase("honeypot.db")
        stats = db.get_statistics()
        
        print(f"  Total Events:        {Colors.YELLOW}{stats['total_events']}{Colors.RESET}")
        print(f"  Unique IPs:          {Colors.YELLOW}{stats['unique_ips']}{Colors.RESET}")
        print(f"  Blacklisted IPs:     {Colors.YELLOW}{stats['blacklisted_ips']}{Colors.RESET}")
        print(f"  Top Protocol:        {Colors.YELLOW}{stats['top_protocol']}{Colors.RESET}")
        print(f"  Top Port:            {Colors.YELLOW}{stats['top_port']}{Colors.RESET}")
        print(f"  Avg Payload Size:    {Colors.YELLOW}{stats['avg_payload_size']:.0f}{Colors.RESET} bytes")
        
        # Get top attackers
        attackers = db.get_top_attackers(5)
        if attackers:
            print(f"\n  {Colors.BOLD}Top 5 Attacking IPs:{Colors.RESET}")
            for attacker in attackers:
                print(f"    {Colors.YELLOW}{attacker['ip']:20}{Colors.RESET} {attacker['total_events']:4} events")
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
    
    print()


def view_map_data():
    """View attack map data"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🌍 ATTACK ORIGINS MAP{Colors.RESET}\n")
    
    try:
        geo = GeolocationService()
        map_data = geo.cache.get_map_data()
        
        if not map_data:
            print(f"{Colors.YELLOW}ℹ️  No geolocation data available{Colors.RESET}\n")
            return
        
        print(f"  {Colors.BOLD}Location{Colors.RESET:20} {Colors.BOLD}IP Address{Colors.RESET:18} {Colors.BOLD}Events{Colors.RESET:6} {Colors.BOLD}ISP{Colors.RESET}")
        print(f"  {'-' * 80}")
        
        for point in map_data[:20]:
            location = f"{point['city']}, {point['country']}"
            print(f"  {location:20} {point['ip']:18} {point['events']:6} {point['isp']}")
        
        if len(map_data) > 20:
            print(f"  ... and {len(map_data) - 20} more")
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
    
    print()


def view_top_attackers():
    """View top attacking IPs"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🔴 TOP ATTACKING IPs{Colors.RESET}\n")
    
    try:
        db = HoneypotDatabase("honeypot.db")
        attackers = db.get_top_attackers(15)
        
        if not attackers:
            print(f"{Colors.YELLOW}ℹ️  No attack data available{Colors.RESET}\n")
            return
        
        print(f"  {Colors.BOLD}IP Address{Colors.RESET:18} {Colors.BOLD}Events{Colors.RESET:7} {Colors.BOLD}Type{Colors.RESET:15} {Colors.BOLD}Rate/min{Colors.RESET:8} {Colors.BOLD}Severity{Colors.RESET}")
        print(f"  {'-' * 80}")
        
        for attacker in attackers:
            severity = attacker.get('severity', 'unknown')
            severity_color = Colors.RED if severity == 'critical' else Colors.YELLOW if severity == 'high' else Colors.CYAN
            
            print(f"  {attacker['ip']:18} {attacker['total_events']:7} {attacker.get('attack_type', 'unknown'):15} {attacker['events_per_minute']:8.1f} {severity_color}{severity}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
    
    print()


def reset_database():
    """Reset the database"""
    print(f"\n{Colors.BOLD}{Colors.RED}⚠️  DATABASE RESET{Colors.RESET}")
    response = input(f"{Colors.YELLOW}Are you sure? This will delete all events. (yes/no): {Colors.RESET}")
    
    if response.lower() == 'yes':
        try:
            db_path = Path(__file__).parent / "honeypot.db"
            if db_path.exists():
                db_path.unlink()
            print(f"{Colors.GREEN}✓ Database reset successfully{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}Cancelled{Colors.RESET}\n")


def show_help():
    """Show help information"""
    help_text = f"""
{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════════════════════════╗{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}                    {Colors.BOLD}DDOSPOT CLI HELP{Colors.RESET}                      {Colors.BOLD}{Colors.CYAN}║{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}╚════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.BOLD}{Colors.GREEN}DDoSPoT - Advanced Honeypot Monitoring System{Colors.RESET}

{Colors.BOLD}DESCRIPTION:{Colors.RESET}
DDoSPoT is a sophisticated honeypot system that simulates vulnerable services
and tracks DDoS/DoS attacks in real-time. It captures attack signatures, 
geolocates attackers, and displays an interactive world map of attack origins.

{Colors.BOLD}FEATURES:{Colors.RESET}
  • Multi-protocol honeypot (HTTP, SSH, DNS, NTP, SSDP)
  • Real-time attack detection and classification
  • Geolocation-based attack tracking
  • Interactive world map visualization
  • Machine learning attack prediction
  • Alert system with multiple notification channels
  • Comprehensive database statistics
  • Web dashboard for monitoring

{Colors.BOLD}QUICK START:{Colors.RESET}
  1. Start both services:      {Colors.CYAN}./cli.py{Colors.RESET} → Choose option 3
  2. Open dashboard:            {Colors.CYAN}./cli.py{Colors.RESET} → Choose option 14 or http://localhost:5000
  3. Simulate attacks:          {Colors.CYAN}./cli.py{Colors.RESET} → Choose option 8
  4. Monitor in real-time:      View the web dashboard

{Colors.BOLD}API ENDPOINTS:{Colors.RESET}
  • GET  /api/stats              - System statistics
  • GET  /api/top-attackers      - Top attacking IPs
  • GET  /api/map-data           - Geolocation coordinates
  • GET  /api/country-stats      - Attacks by country
  • GET  /api/recent-events      - Recent attack events
  • GET  /api/blacklist          - Active blacklist

{Colors.BOLD}LOGS:{Colors.RESET}
  • Honeypot:  /tmp/honeypot.log
  • Dashboard: /tmp/dashboard.log

{Colors.BOLD}DEFAULT PORTS:{Colors.RESET}
  • HTTP:     80
  • SSH:      22
  • DNS:      53
  • NTP:      123
  • SSDP:     1900
  • Dashboard: 5000

{Colors.BOLD}SECURITY & RATE LIMITS:{Colors.RESET}
    • Set API token:            {Colors.CYAN}DDOSPOT_API_TOKEN=...{Colors.RESET}
    • Require token on POSTs:   {Colors.CYAN}DDOSPOT_REQUIRE_TOKEN=true{Colors.RESET}
    • Protect /metrics:         {Colors.CYAN}DDOSPOT_METRICS_PUBLIC=false{Colors.RESET}
    • Protect /health:          {Colors.CYAN}DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH=true{Colors.RESET}
    • Rate limit window (s):    {Colors.CYAN}DDOSPOT_RATE_LIMIT_WINDOW=60{Colors.RESET}
    • Rate limit max events:    {Colors.CYAN}DDOSPOT_RATE_LIMIT_MAX=60{Colors.RESET}
    • Blacklist duration (s):   {Colors.CYAN}DDOSPOT_RATE_LIMIT_BLACKLIST=120{Colors.RESET}

{Colors.BOLD}DOCUMENTATION:{Colors.RESET}
  See 'About DDoSPoT/Commands.txt' for complete command reference.

"""
    print(help_text)


def main():
    """Main CLI loop"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print_banner()
    
    while True:
        try:
            choice = input(print_menu()).strip()
            
            if choice == '0':
                print(f"\n{Colors.GREEN}✓ Goodbye!{Colors.RESET}\n")
                break
            elif choice == '1':
                start_service("Honeypot Server", "main.py")
            elif choice == '2':
                start_service("Dashboard", "dashboard.py")
            elif choice == '3':
                start_service("Honeypot Server", "main.py")
                time.sleep(1)
                start_service("Dashboard", "dashboard.py")
                print(f"{Colors.CYAN}📍 Dashboard URL: http://localhost:5000{Colors.RESET}\n")
            elif choice == '4':
                stop_service("Honeypot Server", "main.py")
            elif choice == '5':
                stop_service("Dashboard", "dashboard.py")
            elif choice == '6':
                stop_service("Honeypot Server", "main.py")
                time.sleep(0.5)
                stop_service("Dashboard", "dashboard.py")
            elif choice == '7':
                simulate_quick_attack()
            elif choice == '8':
                simulate_botnet_attack()
            elif choice == '9':
                simulate_custom_attack()
            elif choice == '10':
                print_status()
            elif choice == '11':
                view_database_stats()
            elif choice == '12':
                view_map_data()
            elif choice == '13':
                view_top_attackers()
            elif choice == '14':
                print(f"\n{Colors.CYAN}📍 Opening dashboard: http://localhost:5000{Colors.RESET}\n")
                try:
                    subprocess.run(["xdg-open", "http://localhost:5000"], timeout=2)
                except:
                    print(f"{Colors.YELLOW}ℹ️  Please open http://localhost:5000 in your browser{Colors.RESET}\n")
            elif choice == '15':
                print("\n" + "=" * 60)
                print("HONEYPOT LOGS (last 50 lines)")
                print("=" * 60 + "\n")
                try:
                    subprocess.run(["tail", "-50", "/tmp/honeypot.log"])
                except:
                    print(f"{Colors.YELLOW}ℹ️  Log file not available{Colors.RESET}")
                print()
            elif choice == '16':
                print("\n" + "=" * 60)
                print("DASHBOARD LOGS (last 50 lines)")
                print("=" * 60 + "\n")
                try:
                    subprocess.run(["tail", "-50", "/tmp/dashboard.log"])
                except:
                    print(f"{Colors.YELLOW}ℹ️  Log file not available{Colors.RESET}")
                print()
            elif choice == '17':
                reset_database()
            elif choice == '18':
                cleanup_old_events_cli()
            elif choice == '19':
                print("\n" + "=" * 60)
                print("DISK SPACE USAGE")
                print("=" * 60 + "\n")
                subprocess.run(["du", "-sh", "."])
                print()
            elif choice == '20':
                show_help()
            elif choice == '21':
                rotate_logs_now()
            elif choice == '22':
                health_check()
            else:
                print(f"\n{Colors.RED}✗ Invalid choice. Please try again.{Colors.RESET}\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
            print(f"{Colors.GREEN}✓ Goodbye!{Colors.RESET}\n")
            break
        except Exception as e:
            print(f"\n{Colors.RED}✗ Error: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    main()
