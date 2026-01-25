#!/usr/bin/env python3
"""
Extended test script for geolocation visualization.
Simulates attacks from various external IPs to populate the map.
"""

import asyncio
import socket
import time
import random
from concurrent.futures import ThreadPoolExecutor

# Simulated external attacker IPs from different countries
EXTERNAL_IPS = [
    "185.220.100.1",      # Russia
    "94.140.14.14",       # Russia
    "203.0.113.45",       # China
    "202.103.24.68",      # China
    "195.154.0.1",        # France
    "89.163.157.1",       # Germany
    "77.91.192.1",        # Brazil
    "80.82.77.1",         # Netherlands
    "216.58.217.46",      # USA
    "198.51.100.1",       # USA
]

def simulate_http_requests(target_ip: str = "127.0.0.1", target_port: int = 8080, count: int = 100):
    """Simulate HTTP requests with spoofed source IPs"""
    print(f"\n[*] Simulating {count} requests from various external IPs")
    
    successful = 0
    for i, attacker_ip in enumerate(EXTERNAL_IPS):
        # Send requests for each external IP
        requests_per_ip = count // len(EXTERNAL_IPS)
        
        for j in range(requests_per_ip):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((target_ip, target_port))
                
                request = f"GET / HTTP/1.1\r\nHost: localhost\r\nX-Forwarded-For: {attacker_ip}\r\nConnection: close\r\n\r\n".encode()
                sock.send(request)
                
                try:
                    response = sock.recv(4096)
                    if b"HTTP/1.1 200" in response:
                        successful += 1
                except:
                    pass
                
                sock.close()
            except Exception as e:
                pass
        
        if (i + 1) % 2 == 0:
            print(f"    Processed {i + 1}/{len(EXTERNAL_IPS)} external IPs...")
    
    print(f"    ✓ Requests complete: {successful} successful responses")
    return successful


def simulate_udp_flood(target_ip: str = "127.0.0.1", target_port: int = 1900, count: int = 50):
    """Simulate UDP flood with various source IPs"""
    print(f"\n[*] Simulating UDP flood from external IPs to {target_ip}:{target_port}")
    
    successful = 0
    
    for attacker_ip in EXTERNAL_IPS[:5]:  # Use first 5 IPs for UDP
        request = b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nST: ssdp:all\r\n\r\n"
        
        for i in range(count // 5):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(request, (target_ip, target_port))
                successful += 1
            except Exception as e:
                pass
    
    print(f"    ✓ UDP flood complete: {successful} packets sent")
    return successful


def check_geolocation_cache():
    """Check geolocation cache in database"""
    try:
        import sqlite3
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT ip, country, city, isp FROM geolocation_cache LIMIT 10')
        rows = cursor.fetchall()
        
        print("\n[*] Geolocation Cache Contents:")
        for row in rows:
            print(f"    {row[0]:20} -> {row[1]:15} {row[2]:15} ({row[3]})")
        
        conn.close()
    except Exception as e:
        print(f"    Error checking cache: {e}")


def check_events():
    """Check events in database"""
    try:
        import sqlite3
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT ip, protocol, type, COUNT(*) as count FROM events GROUP BY ip, protocol, type')
        rows = cursor.fetchall()
        
        print("\n[*] Events Summary:")
        print(f"    {'IP':20} {'Protocol':15} {'Type':20} {'Count':10}")
        print("    " + "-" * 65)
        
        for row in rows:
            print(f"    {row[0]:20} {row[1]:15} {row[2]:20} {row[3]:<10}")
        
        conn.close()
    except Exception as e:
        print(f"    Error checking events: {e}")


def check_blacklist():
    """Check blacklisted IPs"""
    try:
        import sqlite3
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT ip, reason, severity FROM blacklist LIMIT 10')
        rows = cursor.fetchall()
        
        print("\n[*] Blacklisted IPs:")
        print(f"    {'IP':20} {'Reason':30} {'Severity':15}")
        print("    " + "-" * 65)
        
        for row in rows:
            print(f"    {row[0]:20} {row[1]:30} {row[2]:15}")
        
        conn.close()
    except Exception as e:
        print(f"    Error checking blacklist: {e}")


async def main():
    print("=" * 65)
    print("DDoSPot Geolocation Test - Simulating Attacks from Various IPs")
    print("=" * 65)
    print("\n[!] Make sure the honeypot is running: python3 main.py")
    print("[!] This test will simulate attacks from multiple geographic IPs")
    print("[!] Geolocation will be fetched from ip-api.com (may take a few minutes)")
    
    input("\nPress ENTER to start attacks (honeypot must be running)...")
    
    try:
        # Simulate attacks from various external IPs
        simulate_http_requests(count=100)
        await asyncio.sleep(2)
        
        simulate_udp_flood(count=50)
        await asyncio.sleep(2)
        
        # Check database contents
        print("\n" + "=" * 65)
        print("DATABASE CONTENTS AFTER ATTACKS")
        print("=" * 65)
        
        check_events()
        check_blacklist()
        
        print("\n[*] Waiting for geolocation API to populate cache...")
        print("[*] This may take a few seconds (API rate limited to 45 req/min)")
        await asyncio.sleep(5)
        
        # Try to fetch geolocation for each IP
        print("\n[*] Fetching geolocation data for attacking IPs...")
        from core.geolocation import get_geolocation_service
        
        geo_service = get_geolocation_service('honeypot.db')
        
        for ip in EXTERNAL_IPS[:5]:  # Fetch first 5 IPs
            print(f"    Fetching geolocation for {ip}...", end="", flush=True)
            geo_data = await geo_service.get_geolocation(ip)
            if geo_data:
                print(f" ✓ {geo_data.get('country')}, {geo_data.get('city')}")
            else:
                print(" ✗ Failed")
            await asyncio.sleep(1)
        
        await asyncio.sleep(2)
        
        # Check cache
        check_geolocation_cache()
        
        print("\n" + "=" * 65)
        print("TEST COMPLETE!")
        print("=" * 65)
        print("\n[✓] Dashboard should now display:")
        print("    - Attack origins from multiple countries on world map")
        print("    - Country-by-country attack breakdown")
        print("    - IP profiles with geolocation details")
        print("\nOpen browser to: http://127.0.0.1:5000")
        
    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")


if __name__ == '__main__':
    asyncio.run(main())
