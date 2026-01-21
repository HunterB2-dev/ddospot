#!/usr/bin/env python3
"""
DDoSPoT Maintenance Script
Automated maintenance tasks for scheduled execution (cron, systemd timers, etc.)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import HoneypotDatabase


def rotate_logs(max_bytes: int = 5 * 1024 * 1024, backups: int = 2):
    """Rotate log files if they exceed max_bytes."""
    import json
    
    # Try to load settings from config
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                log_config = config.get("log_rotation", {})
                max_bytes = log_config.get("max_bytes", max_bytes)
                backups = log_config.get("backups", backups)
        except Exception:
            pass
    
    # Environment variables override
    max_bytes = int(os.getenv("DDOSPOT_LOG_MAX_BYTES", max_bytes))
    backups = int(os.getenv("DDOSPOT_LOG_BACKUPS", backups))
    
    logs = [
        Path("/tmp/honeypot.log"),
        Path("/tmp/dashboard.log")
    ]
    
    rotated = []
    for log in logs:
        if not log.exists():
            continue
            
        if log.stat().st_size > max_bytes:
            # Perform rotation
            for i in range(backups, 0, -1):
                older = log.with_suffix(f".log.{i}")
                newer = log.with_suffix(f".log.{i - 1}") if i > 1 else log
                if newer.exists():
                    if older.exists():
                        older.unlink()
                    newer.rename(older)
            log.touch()
            rotated.append(str(log))
    
    return rotated


def cleanup_old_events(days: int = 30):
    """Remove events older than specified days and vacuum database."""
    try:
        db = HoneypotDatabase("honeypot.db")
        removed = db.cleanup_old_events(days)
        db.vacuum()
        size_info = db.get_database_size()
        return {
            "removed": removed,
            "days": days,
            "db_size_mb": size_info["size_mb"],
            "event_count": size_info["event_count"]
        }
    except Exception as e:
        return {"error": str(e)}


def full_maintenance(cleanup_days: int = 30):
    """Run full maintenance: log rotation + database cleanup."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {
        "timestamp": timestamp,
        "log_rotation": [],
        "cleanup": {}
    }
    
    # Rotate logs
    rotated = rotate_logs()
    results["log_rotation"] = rotated
    
    # Cleanup database
    cleanup_result = cleanup_old_events(cleanup_days)
    results["cleanup"] = cleanup_result
    
    return results


def print_results(results):
    """Pretty print maintenance results."""
    print(f"[{results['timestamp']}] DDoSPoT Maintenance")
    print(f"  Log Rotation: {len(results['log_rotation'])} file(s) rotated")
    for log in results['log_rotation']:
        print(f"    - {log}")
    
    if "error" in results["cleanup"]:
        print(f"  Cleanup: ERROR - {results['cleanup']['error']}")
    else:
        print(f"  Cleanup: {results['cleanup']['removed']} events removed (>{results['cleanup']['days']} days)")
        print(f"    DB Size: {results['cleanup']['db_size_mb']} MB")
        print(f"    Events: {results['cleanup']['event_count']}")


def main():
    """Main entry point for maintenance script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DDoSPoT Maintenance Utilities")
    parser.add_argument(
        "task",
        choices=["rotate", "cleanup", "full"],
        help="Maintenance task to perform"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days to keep for cleanup (default: 30)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (useful for cron)"
    )
    
    args = parser.parse_args()
    
    if args.task == "rotate":
        rotated = rotate_logs()
        if not args.quiet:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Rotated {len(rotated)} log file(s)")
            for log in rotated:
                print(f"  - {log}")
    
    elif args.task == "cleanup":
        result = cleanup_old_events(args.days)
        if not args.quiet:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if "error" in result:
                print(f"[{timestamp}] Cleanup failed: {result['error']}")
                sys.exit(1)
            else:
                print(f"[{timestamp}] Removed {result['removed']} events (>{args.days} days)")
                print(f"  DB: {result['db_size_mb']} MB, {result['event_count']} events")
    
    elif args.task == "full":
        results = full_maintenance(args.days)
        if not args.quiet:
            print_results(results)
        if "error" in results["cleanup"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
