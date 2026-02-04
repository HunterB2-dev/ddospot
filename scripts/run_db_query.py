#!/usr/bin/env python3
"""
Direct database query runner - bypasses argparse issues
"""
import sys
sys.path.insert(0, '/home/hunter/Projekty/ddospot')

from core.database import HoneypotDatabase
from datetime import datetime

def format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

# Initialize database
db = HoneypotDatabase('logs/honeypot.db')

print("\n" + "="*80)
print("HONEYPOT DATABASE QUERY TOOL")
print("="*80)

# 1. Statistics
print("\n📊 STATISTICS (Last 24 hours)")
print("-"*80)
stats = db.get_statistics(24)
print(f"Total Events:        {stats['total_events']}")
print(f"Unique IPs:          {stats['unique_ips']}")
print(f"Blacklisted IPs:     {stats['blacklisted_ips']}")
print(f"Top Protocol:        {stats['top_protocol']}")
print(f"Top Port:            {stats['top_port']}")
print(f"Avg Payload Size:    {stats['avg_payload_size']} bytes")

# 2. Top Attackers
print("\n🔴 TOP 10 ATTACKING IPs")
print("-"*80)
attackers = db.get_top_attackers(10)
print(f"{'IP':<18} {'Events':<10} {'Type':<15} {'Rate/min':<10} {'Protocols':<25}")
print("-"*80)
for attacker in attackers:
    protocols = ', '.join(attacker['protocols_used']) if attacker['protocols_used'] else "N/A"
    print(f"{attacker['ip']:<18} {attacker['total_events']:<10} {attacker['attack_type']:<15} "
          f"{attacker['events_per_minute']:<10.1f} {protocols:<25}")

# 3. Blacklist
print("\n⛔ CURRENT BLACKLIST")
print("-"*80)
blacklist = db.get_blacklist()
if blacklist:
    print(f"{'IP':<18} {'Reason':<20} {'Severity':<10} {'Expires':<20}")
    print("-"*80)
    for entry in blacklist:
        expires = format_timestamp(entry['expiration_time'])
        print(f"{entry['ip']:<18} {entry['reason']:<20} {entry['severity']:<10} {expires:<20}")
else:
    print("No IPs currently blacklisted")

# 4. Recent Events
print("\n📝 RECENT EVENTS (Last 60 minutes)")
print("-"*80)
events = db.get_recent_events(60, 10)
print(f"{'Timestamp':<25} {'IP':<18} {'Port':<6} {'Protocol':<10} {'Size':<8} {'Type':<15}")
print("-"*80)
for event in events:
    ts = format_timestamp(event['timestamp'])
    print(f"{ts:<25} {event['source_ip']:<18} {event['port']:<6} {event['protocol']:<10} "
          f"{event['payload_size']:<8} {event['event_type']:<15}")

# 5. Database Info
print("\n💾 DATABASE INFORMATION")
print("-"*80)
info = db.get_database_size()
profiles = db.get_all_profiles()
print(f"Database Size:       {info['size_bytes']:,} bytes ({info['size_mb']:.2f} MB)")
print(f"Total Profiles:      {info['profile_count']}")
print(f"Total Events:        {info['event_count']}")
print(f"Age:                 {info['database_age_seconds']/3600:.1f} hours")

print("\n" + "="*80 + "\n")
