"""
IP Geolocation module for DDoSPot honeypot
Uses ip-api.com free API with caching to minimize API calls
"""

import asyncio
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
import urllib.request
import urllib.error

from telemetry.logger import get_logger

logger = get_logger(__name__)

class GeolocationCache:
    """Cache IP geolocation data with SQLite backend"""
    
    def __init__(self, db_path: str = 'honeypot.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize geolocation cache table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create geolocation cache table
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
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_country 
                ON geolocation_cache(country)
            ''')
            
            conn.commit()
            conn.close()
            logger.info('Geolocation cache table initialized')
        except Exception as e:
            logger.error(f'Failed to initialize geolocation cache: {e}')
    
    def get(self, ip: str) -> Optional[Dict]:
        """Get cached geolocation data for IP"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT country, region, city, latitude, longitude, isp, org, asn, cached_at
                FROM geolocation_cache
                WHERE ip = ? AND datetime(cached_at, '+' || ttl_hours || ' hours') > datetime('now')
            ''', (ip,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'ip': ip,
                    'country': row[0],
                    'region': row[1],
                    'city': row[2],
                    'latitude': row[3],
                    'longitude': row[4],
                    'isp': row[5],
                    'org': row[6],
                    'asn': row[7],
                    'cached_at': row[8],
                    'cached': True
                }
            
            return None
        except Exception as e:
            logger.error(f'Cache get failed for {ip}: {e}')
            return None
    
    def set(self, ip: str, data: Dict, ttl_hours: int = 48) -> bool:
        """Cache geolocation data for IP"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO geolocation_cache
                (ip, country, region, city, latitude, longitude, isp, org, asn, cached_at, ttl_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ''', (
                ip,
                data.get('country', 'Unknown'),
                data.get('region', 'Unknown'),
                data.get('city', 'Unknown'),
                data.get('lat', 0.0),
                data.get('lon', 0.0),
                data.get('isp', 'Unknown'),
                data.get('org', 'Unknown'),
                data.get('as', 'Unknown'),
                ttl_hours
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f'Cache set failed for {ip}: {e}')
            return False
    
    def get_country_stats(self) -> Dict[str, int]:
        """Get statistics of attacks by country"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count attacks per country from geolocation cache
            cursor.execute('''
                SELECT g.country, COUNT(DISTINCT e.id) as count
                FROM geolocation_cache g
                LEFT JOIN events e ON g.ip = e.source_ip
                WHERE g.country IS NOT NULL AND g.country != 'Unknown'
                GROUP BY g.country
                ORDER BY count DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return {row[0]: row[1] for row in results}
        except Exception as e:
            logger.error(f'Failed to get country stats: {e}')
            return {}
    
    def get_map_data(self) -> list:
        """Get geolocation data for map visualization"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all unique attacking IPs with their locations
            cursor.execute('''
                SELECT 
                    g.ip, g.country, g.region, g.city, 
                    g.latitude, g.longitude, g.isp,
                    COUNT(DISTINCT e.id) as event_count,
                    MAX(e.created_at) as last_seen
                FROM geolocation_cache g
                LEFT JOIN events e ON g.ip = e.source_ip
                WHERE g.latitude IS NOT NULL AND g.longitude IS NOT NULL
                  AND g.latitude != 0 AND g.longitude != 0
                GROUP BY g.ip
                ORDER BY event_count DESC
                LIMIT 500
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            data = []
            for row in results:
                data.append({
                    'ip': row[0],
                    'country': row[1],
                    'region': row[2],
                    'city': row[3],
                    'latitude': row[4],
                    'longitude': row[5],
                    'isp': row[6],
                    'events': row[7] or 0,
                    'last_seen': row[8]
                })
            
            return data
        except Exception as e:
            logger.error(f'Failed to get map data: {e}')
            return []


class GeolocationService:
    """Service to fetch and manage geolocation data"""
    
    # Use ip-api.com which offers free tier with 45 requests/minute
    API_URL = 'http://ip-api.com/json/'
    
    def __init__(self, cache_path: str = 'honeypot.db', rate_limit: int = 40):
        self.cache = GeolocationCache(cache_path)
        self.rate_limit = rate_limit  # requests per minute
        self.request_times = []
        self.session = None
    
    async def get_geolocation(self, ip: str) -> Optional[Dict]:
        """Get geolocation for IP, checking cache first"""
        # Skip private IPs
        if self._is_private_ip(ip):
            return {
                'ip': ip,
                'country': 'Private',
                'region': 'Local Network',
                'city': 'Local',
                'latitude': 0,
                'longitude': 0,
                'isp': 'Private Network',
                'org': 'Private',
                'asn': 'Private',
                'cached': True
            }
        
        # Check cache first
        cached = self.cache.get(ip)
        if cached:
            return cached
        
        # Rate limit API calls
        if not self._can_request():
            logger.debug(f'Rate limited, skipping API call for {ip}')
            return None
        
        # Fetch from API
        try:
            data = await self._fetch_from_api(ip)
            if data:
                self.cache.set(ip, data)
                data['cached'] = False
                return data
        except Exception as e:
            logger.error(f'Geolocation fetch failed for {ip}: {e}')
        
        return None
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private range"""
        parts = ip.split('.')
        if len(parts) != 4:
            return True
        
        try:
            first_octet = int(parts[0])
            second_octet = int(parts[1])
            
            # Private ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x, 127.x.x.x
            if first_octet == 10:
                return True
            if first_octet == 172 and 16 <= second_octet <= 31:
                return True
            if first_octet == 192 and second_octet == 168:
                return True
            if first_octet == 127:
                return True
            if first_octet == 0 or first_octet == 255:
                return True
        except:
            pass
        
        return False
    
    def _can_request(self) -> bool:
        """Check if we can make API request (rate limiting)"""
        now = time.time()
        # Remove old timestamps outside the 1-minute window
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) < self.rate_limit:
            self.request_times.append(now)
            return True
        
        return False
    
    async def _fetch_from_api(self, ip: str) -> Optional[Dict]:
        """Fetch geolocation from ip-api.com"""
        url = f'{self.API_URL}{ip}?fields=country,regionName,city,lat,lon,isp,org,as'
        
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'DDoSPot/1.0'}
            )
            
            # Run blocking request in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, req)
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'lat': float(data.get('lat', 0)),
                    'lon': float(data.get('lon', 0)),
                    'isp': data.get('isp', 'Unknown'),
                    'org': data.get('org', 'Unknown'),
                    'as': data.get('as', 'Unknown'),
                }
            
            return None
        except urllib.error.HTTPError as e:
            logger.error(f'API HTTP error for {ip}: {e.code}')
            return None
        except Exception as e:
            logger.error(f'API error for {ip}: {e}')
            return None
    
    def clear_old_cache(self, days: int = 7):
        """Clear cache entries older than N days"""
        try:
            conn = sqlite3.connect(self.cache.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM geolocation_cache
                WHERE datetime(cached_at, '+48 hours') < datetime('now')
            ''')
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f'Cleared {deleted} old geolocation cache entries')
        except Exception as e:
            logger.error(f'Failed to clear cache: {e}')


# Global instance
_geolocation_service = None

def get_geolocation_service(cache_path: str = 'honeypot.db') -> GeolocationService:
    """Get or create geolocation service instance"""
    global _geolocation_service
    if _geolocation_service is None:
        _geolocation_service = GeolocationService(cache_path)
    return _geolocation_service
