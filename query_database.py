#!/usr/bin/env python3
"""
Command-line utility for querying and analyzing honeypot attack data.
"""

import sys
import argparse
from datetime import datetime, timedelta
from core.database import HoneypotDatabase


def format_timestamp(timestamp: float) -> str:
    """Convert unix timestamp to readable format"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def cmd_stats(db: HoneypotDatabase, hours: int = 24):
    """Display overall statistics"""
    stats = db.get_statistics(hours)
    
    print("\n" + "=" * 60)
    print("HONEYPOT STATISTICS")
    print("=" * 60)
    print(f"Time Period:         Last {stats['time_period_hours']} hours")
    print(f"Total Events:        {stats['total_events']}")
    print(f"Unique IPs:          {stats['unique_ips']}")
    print(f"Blacklisted IPs:     {stats['blacklisted_ips']}")
    print(f"Top Protocol:        {stats['top_protocol']}")
    print(f"Top Port:            {stats['top_port']}")
    print(f"Avg Payload Size:    {stats['avg_payload_size']} bytes")
    print("=" * 60 + "\n")


def cmd_top_attackers(db: HoneypotDatabase, limit: int = 10):
    """List top attacking IPs"""
    attackers = db.get_top_attackers(limit)
    
    print("\n" + "=" * 100)
    print(f"TOP {limit} ATTACKING IPS")
    print("=" * 100)
    print(f"{'IP Address':<15} {'Events':<10} {'Type':<15} {'Rate/min':<10} {'Protocols':<20}")
    print("-" * 100)
    
    for attacker in attackers:
        protocols = attacker['protocols_used'] if attacker['protocols_used'] else "N/A"
        print(f"{attacker['ip']:<15} {attacker['total_events']:<10} {attacker['attack_type']:<15} "
              f"{attacker['events_per_minute']:<10.1f} {protocols:<20}")
    
    print("=" * 100 + "\n")


def cmd_blacklist(db: HoneypotDatabase):
    """Display current blacklist"""
    blacklist = db.get_blacklist()
    
    print("\n" + "=" * 100)
    print("CURRENT BLACKLIST")
    print("=" * 100)
    
    if not blacklist:
        print("No IPs currently blacklisted")
    else:
        print(f"{'IP Address':<15} {'Reason':<20} {'Severity':<10} {'Expires':<20}")
        print("-" * 100)
        
        for entry in blacklist:
            expires = format_timestamp(entry['expiration_time'])
            print(f"{entry['ip']:<15} {entry['reason']:<20} {entry['severity']:<10} {expires:<20}")
    
    print("=" * 100 + "\n")


def cmd_profile(db: HoneypotDatabase, ip: str):
    """Display detailed profile for an IP"""
    profile = db.get_profile(ip)
    
    print("\n" + "=" * 60)
    print(f"PROFILE FOR {ip}")
    print("=" * 60)
    
    if not profile:
        print(f"No profile found for {ip}")
    else:
        print(f"First Seen:          {format_timestamp(profile['first_seen'])}")
        print(f"Last Seen:           {format_timestamp(profile['last_seen'])}")
        print(f"Total Events:        {profile['total_events']}")
        print(f"Events per Minute:   {profile['events_per_minute']:.1f}")
        print(f"Attack Type:         {profile['attack_type']}")
        print(f"Protocols Used:      {profile['protocols_used']}")
        print(f"Avg Payload Size:    {profile['avg_payload_size']:.0f} bytes")
        print(f"Severity:            {profile['severity']}")
        
        # Get recent events
        print("\nRecent Events (last 10):")
        print("-" * 60)
        events = db.get_events_by_ip(ip, limit=10)
        for event in events:
            print(f"  {format_timestamp(event['timestamp'])} | "
                  f"Port: {event['port']:<6} | Proto: {event['protocol']:<6} | "
                  f"Size: {event['payload_size']} bytes")
    
    print("=" * 60 + "\n")


def cmd_recent(db: HoneypotDatabase, minutes: int = 60, limit: int = 20):
    """Display recent events"""
    events = db.get_recent_events(minutes, limit)
    
    print("\n" + "=" * 100)
    print(f"RECENT EVENTS (last {minutes} minutes, showing {len(events)} of {db.get_statistics(int(minutes/60))['total_events']})")
    print("=" * 100)
    print(f"{'Timestamp':<20} {'IP':<15} {'Port':<6} {'Protocol':<10} {'Size':<8} {'Type':<15}")
    print("-" * 100)
    
    for event in events:
        ts = format_timestamp(event['timestamp'])
        print(f"{ts:<20} {event['source_ip']:<15} {event['port']:<6} {event['protocol']:<10} "
              f"{event['payload_size']:<8} {event['event_type']:<15}")
    
    print("=" * 100 + "\n")


def cmd_severity(db: HoneypotDatabase, severity: str):
    """Display profiles by severity"""
    profiles = db.get_profiles_by_severity(severity)
    
    print("\n" + "=" * 100)
    print(f"PROFILES WITH SEVERITY: {severity.upper()}")
    print("=" * 100)
    
    if not profiles:
        print(f"No profiles found with severity {severity}")
    else:
        print(f"{'IP Address':<15} {'Events':<10} {'Rate/min':<10} {'Type':<15} {'Protocols':<20}")
        print("-" * 100)
        
        for profile in profiles:
            protocols = profile['protocols_used'] if profile['protocols_used'] else "N/A"
            print(f"{profile['ip']:<15} {profile['total_events']:<10} {profile['events_per_minute']:<10.1f} "
                  f"{profile['attack_type']:<15} {protocols:<20}")
    
    print("=" * 100 + "\n")


def cmd_database_info(db: HoneypotDatabase):
    """Display database information"""
    info = db.get_database_size()
    profiles = db.get_all_profiles()
    
    print("\n" + "=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)
    print(f"File Path:           {info['file_path']}")
    print(f"Size:                {info['size_mb']} MB")
    print(f"Total Events:        {info['event_count']}")
    print(f"Total Profiles:      {info['profile_count']}")
    print(f"Blacklist Entries:   {len(db.get_blacklist())}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Honeypot attack data analysis utility"
    )
    
    parser.add_argument("--db", default="honeypot.db", help="Database file path (default: honeypot.db)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Statistics command
    stats_parser = subparsers.add_parser("stats", help="Display overall statistics")
    stats_parser.add_argument("--hours", type=int, default=24, help="Time period in hours (default: 24)")
    
    # Top attackers command
    top_parser = subparsers.add_parser("top", help="List top attacking IPs")
    top_parser.add_argument("--limit", type=int, default=10, help="Number of IPs to display (default: 10)")
    
    # Blacklist command
    subparsers.add_parser("blacklist", help="Display current blacklist")
    
    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Display profile for an IP")
    profile_parser.add_argument("ip", help="IP address to profile")
    
    # Recent events command
    recent_parser = subparsers.add_parser("recent", help="Display recent events")
    recent_parser.add_argument("--minutes", type=int, default=60, help="Time window in minutes (default: 60)")
    recent_parser.add_argument("--limit", type=int, default=20, help="Max events to display (default: 20)")
    
    # Severity command
    severity_parser = subparsers.add_parser("severity", help="Display profiles by severity")
    severity_parser.add_argument("severity", choices=["low", "medium", "high", "critical"], 
                               help="Severity level to filter")
    
    # Database info command
    subparsers.add_parser("info", help="Display database information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Connect to database
    db = HoneypotDatabase(args.db)
    
    try:
        if args.command == "stats":
            cmd_stats(db, args.hours)
        elif args.command == "top":
            cmd_top_attackers(db, args.limit)
        elif args.command == "blacklist":
            cmd_blacklist(db)
        elif args.command == "profile":
            cmd_profile(db, args.ip)
        elif args.command == "recent":
            cmd_recent(db, args.minutes, args.limit)
        elif args.command == "severity":
            cmd_severity(db, args.severity)
        elif args.command == "info":
            cmd_database_info(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
