#!/usr/bin/env python3
"""
Demo script to populate geolocation cache with realistic data for visualization.
"""

import sqlite3
import random
from datetime import datetime

# Sample geolocation data from real-world DDoS attacks
SAMPLE_DATA = [
    {
        'ip': '185.220.100.1',
        'country': 'Russia',
        'region': 'Moscow',
        'city': 'Moscow',
        'latitude': 55.7558,
        'longitude': 37.6173,
        'isp': 'Rostelecom',
        'org': 'PJSC Rostelecom',
        'asn': 'AS12389'
    },
    {
        'ip': '94.140.14.14',
        'country': 'Russia',
        'region': 'Moscow',
        'city': 'Moscow',
        'latitude': 55.7558,
        'longitude': 37.6173,
        'isp': 'Yandex',
        'org': 'Yandex LLC',
        'asn': 'AS13238'
    },
    {
        'ip': '203.0.113.45',
        'country': 'China',
        'region': 'Beijing',
        'city': 'Beijing',
        'latitude': 39.9042,
        'longitude': 116.4074,
        'isp': 'China Telecom',
        'org': 'China Telecom',
        'asn': 'AS4134'
    },
    {
        'ip': '202.103.24.68',
        'country': 'China',
        'region': 'Shanghai',
        'city': 'Shanghai',
        'latitude': 31.2304,
        'longitude': 121.4737,
        'isp': 'China Unicom',
        'org': 'China Unicom',
        'asn': 'AS9808'
    },
    {
        'ip': '195.154.0.1',
        'country': 'France',
        'region': 'Île-de-France',
        'city': 'Paris',
        'latitude': 48.8566,
        'longitude': 2.3522,
        'isp': 'Online S.a.s.',
        'org': 'Online S.a.s.',
        'asn': 'AS12876'
    },
    {
        'ip': '89.163.157.1',
        'country': 'Germany',
        'region': 'Berlin',
        'city': 'Berlin',
        'latitude': 52.5200,
        'longitude': 13.4050,
        'isp': 'Hetzner Online',
        'org': 'Hetzner Online GmbH',
        'asn': 'AS24940'
    },
    {
        'ip': '77.91.192.1',
        'country': 'Brazil',
        'region': 'São Paulo',
        'city': 'São Paulo',
        'latitude': -23.5505,
        'longitude': -46.6333,
        'isp': 'Claro S.A.',
        'org': 'Claro Brasil',
        'asn': 'AS8167'
    },
    {
        'ip': '80.82.77.1',
        'country': 'Netherlands',
        'region': 'North Holland',
        'city': 'Amsterdam',
        'latitude': 52.3676,
        'longitude': 4.9041,
        'isp': 'Leaseweb',
        'org': 'Leaseweb Global B.V.',
        'asn': 'AS60781'
    },
    {
        'ip': '216.58.217.46',
        'country': 'United States',
        'region': 'California',
        'city': 'Mountain View',
        'latitude': 37.3894,
        'longitude': -122.0819,
        'isp': 'Google LLC',
        'org': 'Google Inc.',
        'asn': 'AS15169'
    },
    {
        'ip': '198.51.100.1',
        'country': 'United States',
        'region': 'California',
        'city': 'San Francisco',
        'latitude': 37.7749,
        'longitude': -122.4194,
        'isp': 'Cogent Communications',
        'org': 'Cogent Communications',
        'asn': 'AS174'
    },
    {
        'ip': '1.1.1.1',
        'country': 'Australia',
        'region': 'Queensland',
        'city': 'Brisbane',
        'latitude': -27.4698,
        'longitude': 153.0251,
        'isp': 'Cloudflare Inc',
        'org': 'Cloudflare Inc',
        'asn': 'AS13335'
    },
    {
        'ip': '8.8.8.8',
        'country': 'United States',
        'region': 'Virginia',
        'city': 'Ashburn',
        'latitude': 39.0438,
        'longitude': -77.4874,
        'isp': 'Google LLC',
        'org': 'Google Public DNS',
        'asn': 'AS15169'
    },
]


def populate_demo_data():
    """Populate geolocation cache with sample data"""
    try:
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        # Check if table exists, create if not
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geolocation_cache (
                ip TEXT PRIMARY KEY,
                country TEXT,
                region TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                isp TEXT,
                org TEXT,
                asn TEXT,
                cached_at TIMESTAMP,
                ttl_hours INTEGER DEFAULT 48
            )
        ''')
        
        print("Populating geolocation cache with demo data...")
        
        for data in SAMPLE_DATA:
            cursor.execute('''
                INSERT OR REPLACE INTO geolocation_cache
                (ip, country, region, city, latitude, longitude, isp, org, asn, cached_at, ttl_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 48)
            ''', (
                data['ip'],
                data['country'],
                data['region'],
                data['city'],
                data['latitude'],
                data['longitude'],
                data['isp'],
                data['org'],
                data['asn']
            ))
            
            print(f"  ✓ {data['ip']:20} -> {data['country']:15} ({data['city']})")
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Successfully populated {len(SAMPLE_DATA)} geolocation records")
        print("\nNow refresh your dashboard to see the world map populated!")
        
    except Exception as e:
        print(f"✗ Error populating data: {e}")


def add_demo_events():
    """Add demo events for the sample IPs"""
    try:
        conn = sqlite3.connect('honeypot.db')
        cursor = conn.cursor()
        
        print("\nAdding demo events for visualization...")
        
        for i, data in enumerate(SAMPLE_DATA):
            ip = data['ip']
            
            # Add multiple events with varying intensity
            for j in range(20 + i * 5):  # More events for some IPs
                cursor.execute('''
                    INSERT INTO events (ip, port, protocol, size, type, timestamp, detection_score)
                    VALUES (?, ?, ?, ?, ?, datetime('now', '-' || ? || ' seconds'), ?)
                ''', (
                    ip,
                    random_port(),
                    random_protocol(),
                    random.randint(50, 2000),
                    'volumetric_attack',
                    random.randint(0, 3600),  # Last hour
                    random.uniform(0.5, 1.0)
                ))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Added demo events for all IPs")
        
    except Exception as e:
        print(f"✗ Error adding events: {e}")


def random_port():
    """Get a random common port"""
    ports = [22, 80, 443, 8080, 8443, 53, 1900, 3306, 5432, 27017]
    import random
    return random.choice(ports)


def random_protocol():
    """Get a random protocol"""
    protocols = ['HTTP', 'SSH', 'DNS', 'SSDP', 'UDP']
    import random
    return random.choice(protocols)


if __name__ == '__main__':
    print("=" * 65)
    print("DDoSPot Demo Data Population")
    print("=" * 65)
    print()
    
    populate_demo_data()
    
    print("\n" + "=" * 65)
    print("Dashboard URL: http://127.0.0.1:5000")
    print("=" * 65)
