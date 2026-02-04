"""
Threat Intelligence Module
Provides IP reputation scoring, WHOIS lookups, threat feeds, and botnet detection
"""

import socket
import json
import time
import logging
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

# Known threat feeds and blocklists
KNOWN_THREAT_IPS = {
    # Botnet C&C servers (example)
    '192.168.1.100': {'name': 'Mirai C&C', 'confidence': 0.95},
    '10.0.0.1': {'name': 'DDoS Botnet', 'confidence': 0.90},
}

# Known malicious ASNs (examples)
MALICIOUS_ASNS = {
    'AS16509': {'name': 'AWS (abuse common)', 'threat_level': 'low'},
    'AS15169': {'name': 'Google (abuse possible)', 'threat_level': 'low'},
}

# Country threat levels
COUNTRY_THREAT_LEVELS = {
    'KP': 'critical',  # North Korea
    'IR': 'high',      # Iran
    'SY': 'high',      # Syria
    'CU': 'medium',    # Cuba
}

class WHOISLookup:
    """Handle WHOIS lookups for IP information"""
    
    def __init__(self, cache_timeout=86400):
        self.cache = {}
        self.cache_timeout = cache_timeout
        self.lock = threading.Lock()
    
    def lookup(self, ip: str) -> Optional[Dict]:
        """
        Perform WHOIS lookup for an IP address
        Returns cached result if available
        """
        with self.lock:
            # Check cache
            if ip in self.cache:
                cached_time, cached_data = self.cache[ip]
                if time.time() - cached_time < self.cache_timeout:
                    return cached_data
        
        # Perform lookup
        try:
            result = self._perform_whois(ip)
            
            # Cache result
            with self.lock:
                self.cache[ip] = (time.time(), result)
            
            return result
        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {ip}: {e}")
            return None
    
    def _perform_whois(self, ip: str) -> Dict:
        """Simulate WHOIS lookup (in production, use real WHOIS service)"""
        try:
            # Try to resolve reverse DNS
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "Unknown"
            
            # Extract ISP/Organization from IP range (simplified)
            asn = self._estimate_asn(ip)
            
            return {
                'ip': ip,
                'hostname': hostname,
                'asn': asn,
                'organization': self._get_org_name(asn),
                'country': self._get_country_from_ip(ip),
                'lookup_time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in WHOIS lookup: {e}")
            return None  # type: ignore
    
    def _estimate_asn(self, ip: str) -> str:
        """Estimate ASN from IP (simplified - real implementation would use GeoIP DB)"""
        parts = ip.split('.')
        if len(parts) >= 2:
            first_octet = int(parts[0])
            
            # Simple heuristics for common ASNs
            if first_octet < 10:
                return 'AS16509'  # AWS
            elif first_octet < 50:
                return 'AS15169'  # Google
            elif first_octet < 100:
                return 'AS8452'    # TeData (Egypt)
            elif first_octet < 150:
                return 'AS3352'    # Telefonica
            else:
                return 'AS3741'    # Saturn Naptali (UK)
        return 'AS0'
    
    def _get_org_name(self, asn: str) -> str:
        """Get organization name from ASN"""
        asn_map = {
            'AS16509': 'Amazon Web Services',
            'AS15169': 'Google LLC',
            'AS8452': 'TeData',
            'AS3352': 'Telefonica',
            'AS3741': 'Saturn Naptali',
            'AS0': 'Unknown'
        }
        return asn_map.get(asn, 'Unknown ISP')
    
    def _get_country_from_ip(self, ip: str) -> str:
        """Get country code from IP (simplified)"""
        parts = ip.split('.')
        if len(parts) >= 2:
            first_octet = int(parts[0])
            
            # Simplified geolocation based on IP ranges
            if first_octet < 10:
                return 'US'
            elif first_octet < 20:
                return 'GB'
            elif first_octet < 50:
                return 'DE'
            elif first_octet < 100:
                return 'EG'
            elif first_octet < 150:
                return 'ES'
            else:
                return 'RU'
        return 'XX'


class IPReputationScorer:
    """Calculate IP reputation score (0-100 scale)"""
    
    def __init__(self):
        self.scores = {}
    
    def calculate_score(self, ip: str, attack_profile: Dict) -> Tuple[int, Dict]:
        """
        Calculate reputation score for an IP based on:
        - Number of attacks
        - Attack diversity
        - Known threat lists
        - ASN reputation
        - Country reputation
        - Attack patterns
        
        Returns: (score: 0-100, factors: dict)
        """
        factors = {}
        score = 0
        
        # Factor 1: Attack volume (0-40 points)
        attack_count = attack_profile.get('total_events', 0)
        if attack_count > 1000:
            factors['attack_volume'] = 40
        elif attack_count > 100:
            factors['attack_volume'] = 30
        elif attack_count > 10:
            factors['attack_volume'] = 20
        else:
            factors['attack_volume'] = 5
        score += factors['attack_volume']
        
        # Factor 2: Attack diversity (0-20 points)
        protocols = len(attack_profile.get('protocols_used', set()))
        if protocols > 5:
            factors['attack_diversity'] = 20
        elif protocols > 3:
            factors['attack_diversity'] = 15
        elif protocols > 1:
            factors['attack_diversity'] = 10
        else:
            factors['attack_diversity'] = 0
        score += factors['attack_diversity']
        
        # Factor 3: Attack rate (0-20 points)
        events_per_minute = attack_profile.get('events_per_minute', 0)
        if events_per_minute > 100:
            factors['attack_rate'] = 20
        elif events_per_minute > 10:
            factors['attack_rate'] = 15
        elif events_per_minute > 1:
            factors['attack_rate'] = 10
        else:
            factors['attack_rate'] = 0
        score += factors['attack_rate']
        
        # Factor 4: Known threat list (0-15 points)
        factors['known_threats'] = 0
        if ip in KNOWN_THREAT_IPS:
            factors['known_threats'] = 15
            score += 15
        
        # Factor 5: Country reputation (0-5 points)
        country = attack_profile.get('country', 'XX')
        threat_level = COUNTRY_THREAT_LEVELS.get(country)
        if threat_level == 'critical':
            factors['country_threat'] = 5
            score += 5
        elif threat_level == 'high':
            factors['country_threat'] = 3
            score += 3
        else:
            factors['country_threat'] = 0
        
        # Ensure score is within bounds
        score = min(100, max(0, score))
        factors['final_score'] = score
        
        return score, factors
    
    def get_threat_level(self, score: int) -> str:
        """Convert numeric score to threat level"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        elif score >= 20:
            return 'low'
        else:
            return 'minimal'
    
    def get_score_color(self, score: int) -> str:
        """Get color for reputation score display"""
        if score >= 80:
            return '#f44336'  # Red
        elif score >= 60:
            return '#ff9800'  # Orange
        elif score >= 40:
            return '#ffc107'  # Yellow
        elif score >= 20:
            return '#8bc34a'  # Light Green
        else:
            return '#4caf50'  # Green


class ThreatFeedMatcher:
    """Match IPs against known threat feeds"""
    
    def __init__(self):
        self.threat_feeds = []
        self._load_threat_feeds()
    
    def _load_threat_feeds(self):
        """Load known threat feeds (in production, fetch from external sources)"""
        self.threat_feeds = [
            {
                'name': 'Spamhaus DROP',
                'ips': set(),
                'updated': datetime.now()
            },
            {
                'name': 'NIST Botnet IPs',
                'ips': set(),
                'updated': datetime.now()
            },
            {
                'name': 'AbuseCH URLhaus',
                'ips': set(),
                'updated': datetime.now()
            }
        ]
    
    def check_ip(self, ip: str) -> List[Dict]:
        """Check if IP appears in any threat feeds"""
        matches = []
        
        # Check known threat IPs
        if ip in KNOWN_THREAT_IPS:
            matches.append({
                'feed': 'Internal Threat List',
                'ip': ip,
                'threat': KNOWN_THREAT_IPS[ip]['name'],
                'confidence': KNOWN_THREAT_IPS[ip]['confidence'],
                'last_seen': datetime.now().isoformat()
            })
        
        # Check against threat feeds
        for feed in self.threat_feeds:
            if ip in feed['ips']:
                matches.append({
                    'feed': feed['name'],
                    'ip': ip,
                    'last_seen': feed['updated'].isoformat()
                })
        
        return matches


class BotnetDetector:
    """Detect botnet activity and cluster attacks"""
    
    def __init__(self):
        self.botnets = defaultdict(list)
        self.ip_signatures = {}
    
    def analyze_attack_pattern(self, ip: str, attack_profile: Dict) -> Optional[Dict]:
        """
        Analyze attack pattern to detect botnet signatures
        """
        signature = self._extract_signature(attack_profile)
        
        # Check if similar signature exists (possible botnet member)
        for existing_ip, existing_sig in self.ip_signatures.items():
            similarity = self._calculate_similarity(signature, existing_sig)
            if similarity > 0.8:  # High similarity threshold
                return {
                    'type': 'botnet_member',
                    'confidence': similarity,
                    'similar_to': existing_ip,
                    'botnet_family': self._identify_botnet_family(signature)
                }
        
        # Store signature for future comparison
        self.ip_signatures[ip] = signature
        
        return None
    
    def _extract_signature(self, profile: Dict) -> Dict:
        """Extract behavioral signature from attack profile"""
        return {
            'protocols': frozenset(profile.get('protocols_used', [])),
            'avg_payload': profile.get('avg_payload_size', 0),
            'event_rate': profile.get('events_per_minute', 0),
            'attack_type': profile.get('attack_type', 'unknown'),
        }
    
    def _calculate_similarity(self, sig1: Dict, sig2: Dict) -> float:
        """Calculate similarity between two attack signatures"""
        scores = []
        
        # Protocol similarity
        if sig1['protocols'] == sig2['protocols']:
            scores.append(1.0)
        else:
            intersection = len(sig1['protocols'] & sig2['protocols'])
            union = len(sig1['protocols'] | sig2['protocols'])
            if union > 0:
                scores.append(intersection / union)
            else:
                scores.append(0)
        
        # Payload size similarity
        payload_diff = abs(sig1['avg_payload'] - sig2['avg_payload'])
        if payload_diff < 100:
            scores.append(0.9)
        elif payload_diff < 500:
            scores.append(0.7)
        else:
            scores.append(0.3)
        
        # Attack type similarity
        if sig1['attack_type'] == sig2['attack_type']:
            scores.append(1.0)
        else:
            scores.append(0.5)
        
        # Average similarity
        return sum(scores) / len(scores) if scores else 0
    
    def _identify_botnet_family(self, signature: Dict) -> str:
        """Identify botnet family from signature"""
        if 'DNS' in signature['protocols'] and signature['avg_payload'] > 500:
            return 'Possible DNS Amplification Bot'
        elif 'SSDP' in signature['protocols']:
            return 'Possible SSDP Amplification Bot'
        elif 'NTP' in signature['protocols']:
            return 'Possible NTP Amplification Bot'
        elif 'HTTP' in signature['protocols'] and signature['event_rate'] > 1000:
            return 'Possible HTTP Flood Bot'
        else:
            return 'Unknown Botnet Family'


class ThreatIntelligenceManager:
    """Central threat intelligence manager"""
    
    def __init__(self):
        self.whois = WHOISLookup()
        self.scorer = IPReputationScorer()
        self.threat_feed = ThreatFeedMatcher()
        self.botnet_detector = BotnetDetector()
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour
    
    def get_threat_profile(self, ip: str, attack_profile: Optional[Dict] = None) -> Dict[str, Any]:  # type: ignore
        """
        Get complete threat profile for an IP
        
        Returns:
        {
            'ip': str,
            'reputation_score': int (0-100),
            'threat_level': str,
            'whois': dict,
            'threat_feeds': list,
            'botnet_analysis': dict,
            'indicators': list,
            'timestamp': str
        }
        """
        # Check cache
        cache_key = f"threat_{ip}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_timeout:
                return cached_data
        
        profile: Dict[str, Any] = {
            'ip': ip,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get WHOIS information
        whois_data = self.whois.lookup(ip)
        profile['whois'] = whois_data or {}  # type: ignore
        
        # Calculate reputation score
        if attack_profile:
            score, factors = self.scorer.calculate_score(ip, attack_profile)
            profile['reputation_score'] = score  # type: ignore
            profile['threat_level'] = self.scorer.get_threat_level(score)
            profile['score_factors'] = factors  # type: ignore
            profile['score_color'] = self.scorer.get_score_color(score)
        else:
            profile['reputation_score'] = 0  # type: ignore
            profile['threat_level'] = 'minimal'
            profile['score_factors'] = {}  # type: ignore
            profile['score_color'] = '#4caf50'
        
        # Check threat feeds
        profile['threat_feeds'] = self.threat_feed.check_ip(ip)  # type: ignore
        
        # Analyze for botnet patterns
        if attack_profile:
            botnet_info = self.botnet_detector.analyze_attack_pattern(ip, attack_profile)
            profile['botnet_analysis'] = botnet_info or {}  # type: ignore
        
        # Generate indicators
        profile['indicators'] = self._generate_indicators(profile, attack_profile or {})  # type: ignore
        
        # Cache result
        self.cache[cache_key] = (time.time(), profile)
        
        return profile
    
    def _generate_indicators(self, threat_profile: Dict, attack_profile: Dict) -> List[Dict]:
        """Generate threat indicators"""
        indicators = []
        
        # High reputation score
        if threat_profile['reputation_score'] > 70:
            indicators.append({
                'type': 'high_reputation_score',
                'severity': 'high',
                'description': f"High reputation score: {threat_profile['reputation_score']}/100"
            })
        
        # Known threat feed
        if threat_profile['threat_feeds']:
            indicators.append({
                'type': 'known_threat',
                'severity': 'critical',
                'description': f"Found in {len(threat_profile['threat_feeds'])} threat feed(s)"
            })
        
        # Botnet detected
        if threat_profile['botnet_analysis']:
            indicators.append({
                'type': 'botnet_detected',
                'severity': 'high',
                'description': threat_profile['botnet_analysis'].get('botnet_family', 'Unknown Botnet')
            })
        
        # High attack rate
        if attack_profile.get('events_per_minute', 0) > 100:
            indicators.append({
                'type': 'high_attack_rate',
                'severity': 'high',
                'description': f"Attack rate: {attack_profile['events_per_minute']:.1f} events/min"
            })
        
        # Multi-protocol attack
        if len(attack_profile.get('protocols_used', [])) > 2:
            indicators.append({
                'type': 'multi_protocol_attack',
                'severity': 'medium',
                'description': f"Attacking {len(attack_profile['protocols_used'])} protocols"
            })
        
        # High country threat level
        country = threat_profile['whois'].get('country', 'XX')
        threat_level = COUNTRY_THREAT_LEVELS.get(country)
        if threat_level in ['high', 'critical']:
            indicators.append({
                'type': 'high_risk_country',
                'severity': threat_level,
                'description': f"Attack from high-risk country: {country}"
            })
        
        return indicators


# Global instance
_threat_manager = None

def get_threat_intelligence_manager() -> ThreatIntelligenceManager:
    """Get or create global threat intelligence manager"""
    global _threat_manager
    if _threat_manager is None:
        _threat_manager = ThreatIntelligenceManager()
    return _threat_manager


def get_threat_profile(ip: str, attack_profile: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function to get threat profile"""
    return get_threat_intelligence_manager().get_threat_profile(ip, attack_profile)
