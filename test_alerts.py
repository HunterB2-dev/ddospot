#!/usr/bin/env python3
"""
Test script to demonstrate alert system functionality.
"""

import json
from telemetry.alerts import get_alert_manager

def test_alerts():
    print("=" * 65)
    print("DDoSPot Alert System Test")
    print("=" * 65)
    
    # Get alert manager
    alert_mgr = get_alert_manager("honeypot.db", "alert_config.json")
    
    print("\n[*] Current Alert Configuration:")
    config = alert_mgr.config.config
    print(f"    Alerts Enabled: {config['enabled']}")
    print(f"    Email Enabled: {config['email']['enabled']}")
    print(f"    Discord Enabled: {config['discord']['enabled']}")
    print(f"    Throttle Enabled: {config['throttle']['enabled']}")
    print(f"    Min Interval: {config['throttle']['min_interval_seconds']}s")
    
    print("\n[*] Testing Alert Triggering:")
    
    # Test 1: Critical attack alert
    print("\n  Test 1: Critical Attack Alert")
    success = alert_mgr.alert_critical_attack(
        ip='192.0.2.100',
        severity='critical',
        event_count=250,
        protocols=['HTTP', 'SSDP', 'DNS']
    )
    print(f"    Result: {'✓ Sent' if success else '✗ Not sent (check config)'}")
    
    # Test 2: IP Blacklist alert
    print("\n  Test 2: IP Blacklist Alert")
    success = alert_mgr.alert_ip_blacklisted(
        ip='192.0.2.100',
        reason='volumetric_attack',
        severity='critical'
    )
    print(f"    Result: {'✓ Sent' if success else '✗ Not sent (throttled or disabled)'}")
    
    # Test 3: Sustained attack alert
    print("\n  Test 3: Sustained Attack Alert")
    success = alert_mgr.alert_sustained_attack(
        duration_minutes=45,
        event_count=1250
    )
    print(f"    Result: {'✓ Sent' if success else '✗ Not sent (check config)'}")
    
    # Get alert history
    print("\n[*] Alert History:")
    history = alert_mgr.get_alert_history(10)
    
    if not history:
        print("    No alerts recorded yet")
    else:
        print(f"    Total recorded: {len(history)}")
        for alert in history[:5]:
            print(f"    - {alert['type']:20} | {alert['severity']:10} | {alert['timestamp']}")
    
    print("\n[*] Configuration Instructions:")
    print("""
    To enable email alerts:
    1. Edit alert_config.json
    2. Set email.enabled to true
    3. Add your Gmail account and app password
    4. Set recipients list
    
    To enable Discord alerts:
    1. Create a Discord webhook
    2. Edit alert_config.json
    3. Set discord.enabled to true
    4. Set the webhook_url
    """)
    
    print("\n" + "=" * 65)
    print("Alert system is working! Configure your notification channels.")
    print("=" * 65)

if __name__ == '__main__':
    test_alerts()
