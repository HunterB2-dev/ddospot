"""
Real-time Threat Intelligence System
Provides IP reputation checking, geolocation analysis, threat feed integration,
and attack trend analysis for honeypot data enrichment.
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import threading
import logging
from math import sqrt

logger = logging.getLogger(__name__)

# ============================================================================
# IP REPUTATION MODULE
# ============================================================================

class IPReputationChecker:
    """Check and cache IP reputation scores"""
    
    # Known malicious IP ranges (examples)
    KNOWN_MALICIOUS_RANGES = [
        (0, 256),  # Reserved
        (2130706432, 2147483648),  # Loopback
    ]
    
    # Countries with high threat levels
    HIGH_RISK_COUNTRIES = {
        'CN', 'RU', 'KP', 'IR', 'SY',  # Known threat sources
    }
    
    def __init__(self):
        self.reputation_cache = {}
        self.last_update = {}
        self.cache_ttl = 86400  # 24 hours
        
    def check_ip_reputation(self, ip: str) -> Dict:
        """
        Check IP reputation from cache or external sources
        Returns dict with reputation score (0-100) and details
        """
        # Check cache first
        if ip in self.reputation_cache:
            cached_data = self.reputation_cache[ip]
            if time.time() - self.last_update.get(ip, 0) < self.cache_ttl:
                return cached_data
        
        # Simulate external API lookup (in production, use AbuseIPDB/OSINT)
        reputation = self._lookup_reputation(ip)
        
        # Cache result
        self.reputation_cache[ip] = reputation
        self.last_update[ip] = time.time()
        
        return reputation
    
    def _lookup_reputation(self, ip: str) -> Dict:
        """Internal reputation lookup logic"""
        score = 0
        sources = []
        
        # IP format check
        try:
            octets = list(map(int, ip.split('.')))
            if len(octets) != 4 or any(o > 255 for o in octets):
                return {'score': 0, 'sources': ['invalid_ip'], 'details': {}}
        except:
            return {'score': 0, 'sources': ['invalid_format'], 'details': {}}
        
        # Check against known ranges
        ip_int = sum(o << (8 * (3 - i)) for i, o in enumerate(octets))
        
        # Reserved range detection
        if ip_int < 16777216:  # 0.0.0.0/8
            score += 10
            sources.append('reserved_range')
        
        # Simulate threat feed matches (more predictable patterns)
        if sum(octets) % 2 == 0:  # Even sum = more likely to trigger
            score += 20
            sources.append('threat_feed_match')
        
        if sum(octets) % 3 == 0:
            score += 15
            sources.append('abuse_reports')
        
        if octets[0] > 100:  # High first octet = more suspicious
            score += 15
            sources.append('suspicious_range')
        
        if octets[0] < 50 and sum(octets) > 100:  # Low first octet but high overall sum
            score += 25
            sources.append('known_botnet')
        
        # Confidence based on number of sources
        confidence = min(100, len(sources) * 25)
        
        return {
            'score': min(100, score),
            'sources': sources,
            'confidence': confidence,
            'last_updated': datetime.now().isoformat(),
            'details': {
                'reports': len(sources),
                'threat_types': sources,
            }
        }

# ============================================================================
# GEOLOCATION MODULE
# ============================================================================

class GeoIPAnalyzer:
    """Analyze geolocation and geographic risk"""
    
    # Country risk mapping (simplified)
    COUNTRY_RISK_SCORES = {
        'CN': 85,  # China
        'RU': 80,  # Russia
        'KP': 95,  # North Korea
        'IR': 75,  # Iran
        'SY': 70,  # Syria
        'US': 30,  # USA
        'GB': 25,  # UK
        'DE': 20,  # Germany
        'JP': 15,  # Japan
        'AU': 20,  # Australia
    }
    
    def __init__(self):
        self.geo_cache = {}
        self.last_geo_update = {}
        self.cache_ttl = 86400
        
    def get_geolocation(self, ip: str) -> Dict:
        """Get geolocation data for IP"""
        if ip in self.geo_cache:
            cached_data = self.geo_cache[ip]
            if time.time() - self.last_geo_update.get(ip, 0) < self.cache_ttl:
                return cached_data
        
        geo_data = self._lookup_geolocation(ip)
        
        self.geo_cache[ip] = geo_data
        self.last_geo_update[ip] = time.time()
        
        return geo_data
    
    def _lookup_geolocation(self, ip: str) -> Dict:
        """Internal geolocation lookup"""
        try:
            octets = list(map(int, ip.split('.')))
        except:
            return {'country': 'UNKNOWN', 'risk_score': 0}
        
        # Simulate geolocation (in production, use MaxMind GeoIP2 or IP2Location)
        # Use octet sum for deterministic mapping
        octet_sum = sum(octets) % 10
        
        countries = ['US', 'RU', 'CN', 'GB', 'DE', 'FR', 'JP', 'IN', 'BR', 'AU']
        country_code = countries[octet_sum]
        
        risk_score = self.COUNTRY_RISK_SCORES.get(country_code, 50)
        
        return {
            'country': country_code,
            'country_name': self._country_name(country_code),
            'risk_score': risk_score,
            'lat': 0.0,  # Placeholder
            'lon': 0.0,  # Placeholder
            'city': 'Unknown',
            'isp': 'Unknown ISP',
            'last_updated': datetime.now().isoformat(),
        }
    
    @staticmethod
    def _country_name(code: str) -> str:
        """Get country name from code"""
        countries = {
            'US': 'United States', 'RU': 'Russia', 'CN': 'China',
            'GB': 'United Kingdom', 'DE': 'Germany', 'FR': 'France',
            'JP': 'Japan', 'IN': 'India', 'BR': 'Brazil', 'AU': 'Australia',
            'KP': 'North Korea', 'IR': 'Iran', 'SY': 'Syria',
        }
        return countries.get(code, 'Unknown')

# ============================================================================
# THREAT FEED MODULE
# ============================================================================

class ThreatFeedManager:
    """Manage threat feed integration"""
    
    def __init__(self):
        self.feeds_cache = {}
        self.feed_sources = {
            'abuse_ipdb': self._check_abuseipdb,
            'alienVault_otx': self._check_alienVault,
            'urlhaus': self._check_urlhaus,
            'shodan': self._check_shodan,
        }
        self.last_feed_update = {}
        self.feed_ttl = 86400
        
    def check_threat_feeds(self, ip: str) -> Dict:
        """Check IP against multiple threat feeds"""
        results = {}
        
        for feed_name, check_func in self.feed_sources.items():
            results[feed_name] = check_func(ip)
        
        # Count matches
        matches = sum(1 for v in results.values() if v.get('matched', False))
        
        return {
            'total_feeds_checked': len(self.feed_sources),
            'matches': matches,
            'details': results,
            'last_updated': datetime.now().isoformat(),
        }
    
    def _check_abuseipdb(self, ip: str) -> Dict:
        """Check AbuseIPDB feed"""
        # Simulate API check
        if sum(map(int, ip.split('.'))) % 3 == 0:
            return {
                'source': 'abuse_ipdb',
                'matched': True,
                'confidence': 85,
                'reports': 12,
                'threat_type': 'scanner',
            }
        return {'source': 'abuse_ipdb', 'matched': False}
    
    def _check_alienVault(self, ip: str) -> Dict:
        """Check AlienVault OTX feed"""
        if sum(map(int, ip.split('.'))) % 5 == 0:
            return {
                'source': 'alienVault_otx',
                'matched': True,
                'pulse_count': 3,
                'threat_types': ['malware', 'c2'],
            }
        return {'source': 'alienVault_otx', 'matched': False}
    
    def _check_urlhaus(self, ip: str) -> Dict:
        """Check URLhaus feed"""
        if sum(map(int, ip.split('.'))) % 7 == 0:
            return {
                'source': 'urlhaus',
                'matched': True,
                'malware_samples': 5,
            }
        return {'source': 'urlhaus', 'matched': False}
    
    def _check_shodan(self, ip: str) -> Dict:
        """Check Shodan honeypot feed"""
        if sum(map(int, ip.split('.'))) % 11 == 0:
            return {
                'source': 'shodan',
                'matched': True,
                'honeypot_score': 0.92,
            }
        return {'source': 'shodan', 'matched': False}

# ============================================================================
# ATTACK TREND ANALYSIS MODULE
# ============================================================================

class AttackTrendAnalyzer:
    """Analyze attack trends and patterns"""
    
    def __init__(self):
        self.attack_history = defaultdict(list)  # IP -> [(timestamp, protocol, payload_size)]
        self.attack_patterns = {}
        self.baseline_stats = {}
        
    def record_attack(self, ip: str, protocol: str, payload_size: int):
        """Record an attack event"""
        self.attack_history[ip].append({
            'timestamp': time.time(),
            'protocol': protocol,
            'payload_size': payload_size,
        })
    
    def analyze_trends(self, ip: str) -> Dict:
        """Analyze attack trends for an IP"""
        if ip not in self.attack_history or not self.attack_history[ip]:
            return {
                'attack_count': 0,
                'trend_score': 0,
                'velocity': 0,
                'consistency': 0,
                'anomaly_score': 0,
            }
        
        events = self.attack_history[ip]
        
        # Keep only recent events (24 hours)
        current_time = time.time()
        recent_events = [e for e in events if current_time - e['timestamp'] < 86400]
        
        if not recent_events:
            return {
                'attack_count': 0,
                'trend_score': 0,
                'velocity': 0,
                'consistency': 0,
                'anomaly_score': 0,
            }
        
        # Calculate metrics
        time_diffs = []
        for i in range(1, len(recent_events)):
            time_diffs.append(recent_events[i]['timestamp'] - recent_events[i-1]['timestamp'])
        
        # Attack velocity (attacks per hour)
        if time_diffs:
            avg_interval = sum(time_diffs) / len(time_diffs)
            velocity = max(0, min(100, (3600 / max(avg_interval, 1)) * 10))
        else:
            velocity = 10
        
        # Attack consistency (stddev of intervals)
        if len(time_diffs) > 1:
            mean = sum(time_diffs) / len(time_diffs)
            variance = sum((x - mean) ** 2 for x in time_diffs) / len(time_diffs)
            stddev = sqrt(max(0, variance))
            consistency = max(0, 100 - (stddev / max(mean, 1)) * 50)
        else:
            consistency = 0
        
        # Protocol diversity
        protocols = Counter(e['protocol'] for e in recent_events)
        protocol_diversity = len(protocols) / 11 * 100  # 11 protocols max
        
        # Payload size anomalies
        payload_sizes = [e['payload_size'] for e in recent_events]
        if len(payload_sizes) > 1:
            avg_size = sum(payload_sizes) / len(payload_sizes)
            size_variance = sum((x - avg_size) ** 2 for x in payload_sizes) / len(payload_sizes)
            size_stddev = sqrt(max(0, size_variance))
            size_anomaly = min(100, (size_stddev / max(avg_size, 1)) * 50)
        else:
            size_anomaly = 0
        
        # Anomaly score combines protocol diversity and payload anomalies
        anomaly_score = (protocol_diversity + size_anomaly) / 2
        
        # Trend score combines all factors
        trend_score = (velocity * 0.3 + consistency * 0.3 + anomaly_score * 0.4)
        
        return {
            'attack_count': len(recent_events),
            'trend_score': min(100, trend_score),
            'velocity': min(100, velocity),  # attacks per hour
            'consistency': min(100, consistency),  # regularity
            'anomaly_score': min(100, anomaly_score),  # deviation from normal
            'protocol_diversity': min(100, protocol_diversity),
            'unique_protocols': len(protocols),
            'protocols': list(protocols.keys()),
            'recent_attacks': len(recent_events),
        }

# ============================================================================
# THREAT INTELLIGENCE MANAGER (COORDINATOR)
# ============================================================================

import time

class ThreatIntelligenceManager:
    """Central threat intelligence coordinator"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.reputation_checker = IPReputationChecker()
        self.geo_analyzer = GeoIPAnalyzer()
        self.threat_feed_manager = ThreatFeedManager()
        self.trend_analyzer = AttackTrendAnalyzer()
        
        self._initialized = True
        logger.info("Threat Intelligence Manager initialized")
    
    def analyze_ip(self, ip: str, protocol: Optional[str] = None, payload_size: int = 0) -> Dict:
        """Comprehensive IP analysis"""
        
        # Record attack for trending
        if protocol:
            self.trend_analyzer.record_attack(ip, protocol, payload_size)
        
        # Gather intelligence
        reputation = self.reputation_checker.check_ip_reputation(ip)
        geo = self.geo_analyzer.get_geolocation(ip)
        feeds = self.threat_feed_manager.check_threat_feeds(ip)
        trends = self.trend_analyzer.analyze_trends(ip)
        
        # Calculate composite threat score
        score = self._calculate_threat_score(reputation, geo, feeds, trends)
        threat_level = self._get_threat_level(score)
        recommendations = self._get_recommendations(ip, score, reputation, geo, feeds, trends)
        
        return {
            'ip': ip,
            'reputation': reputation,
            'geolocation': geo,
            'threat_feeds': feeds,
            'trends': trends,
            'composite_threat_score': score,
            'threat_level': threat_level,
            'recommendations': recommendations,
            'analysis_timestamp': datetime.now().isoformat(),
        }
    
    def _calculate_threat_score(self, reputation: Dict, geo: Dict, feeds: Dict, trends: Dict) -> float:
        """Calculate weighted composite threat score (0-100)"""
        
        rep_score = reputation.get('score', 0)
        geo_score = geo.get('risk_score', 0)
        feed_score = min(100, feeds.get('matches', 0) * 20)  # 5 feeds = 100
        trend_score = trends.get('trend_score', 0)
        
        # Weighted average
        # Reputation: 30%, Geo: 20%, Feeds: 30%, Trends: 20%
        composite = (rep_score * 0.30 + 
                    geo_score * 0.20 + 
                    feed_score * 0.30 + 
                    trend_score * 0.20)
        
        return round(min(100, composite), 2)
    
    def _get_threat_level(self, score: float) -> str:
        """Convert score to threat level"""
        if score >= 80:
            return 'CRITICAL'
        elif score >= 60:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        elif score >= 20:
            return 'LOW'
        else:
            return 'INFO'
    
    def _get_recommendations(self, ip: str, score: float, reputation: Dict, 
                            geo: Dict, feeds: Dict, trends: Dict) -> List[str]:
        """Generate response recommendations"""
        
        recommendations = []
        
        if score >= 80:
            recommendations.append('Block IP immediately')
            recommendations.append('Add to firewall blacklist')
            recommendations.append('Alert security team ASAP')
            recommendations.append('Investigate for active intrusion')
        elif score >= 60:
            recommendations.append('Consider blocking IP')
            recommendations.append('Increase monitoring level')
            recommendations.append('Review all connections from this IP')
        elif score >= 40:
            recommendations.append('Monitor connections closely')
            recommendations.append('Log detailed forensic data')
            recommendations.append('Watch for escalation patterns')
        
        if feeds.get('matches', 0) > 2:
            recommendations.append('IP appears in multiple threat feeds')
        
        if trends.get('velocity', 0) > 80:
            recommendations.append('Very high attack frequency detected')
        
        if trends.get('anomaly_score', 0) > 70:
            recommendations.append('Unusual attack pattern detected')
        
        if geo.get('risk_score', 0) > 80:
            recommendations.append(f"IP from high-risk country: {geo.get('country')}")
        
        return recommendations
    
    def get_top_threats(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top threat IPs"""
        all_ips = set(self.reputation_checker.reputation_cache.keys())
        all_ips.update(self.geo_analyzer.geo_cache.keys())
        all_ips.update(self.threat_feed_manager.feeds_cache.keys())
        all_ips.update(self.trend_analyzer.attack_history.keys())
        
        scores = []
        for ip in all_ips:
            analysis = self.analyze_ip(ip)
            scores.append((ip, analysis['composite_threat_score']))
        
        return sorted(scores, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        return {
            'cached_ips': len(self.reputation_checker.reputation_cache),
            'total_threat_feeds': len(self.threat_feed_manager.feed_sources),
            'tracked_attack_ips': len(self.trend_analyzer.attack_history),
            'total_events_recorded': sum(len(v) for v in self.trend_analyzer.attack_history.values()),
            'threat_intelligence_sources': {
                'reputation': 'Cache + External APIs',
                'geolocation': 'MaxMind GeoIP2 (simulated)',
                'feeds': list(self.threat_feed_manager.feed_sources.keys()),
                'trends': 'Local analysis engine',
            }
        }

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

def get_threat_intelligence_manager() -> ThreatIntelligenceManager:
    """Get singleton instance of threat intelligence manager"""
    return ThreatIntelligenceManager()
