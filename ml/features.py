"""
Feature extraction from honeypot events for ML model training.
Converts raw events into feature vectors for attack classification.
"""

from typing import List, Dict, Optional
from collections import defaultdict
import time


class FeatureExtractor:
    """Extract ML features from attack events"""
    
    def __init__(self):
        self.protocol_map = {
            'HTTP': 0, 'DNS': 1, 'SSDP': 2, 'NTP': 3,
            'SNMP': 4, 'MEMCACHED': 5, 'CHARGEN': 6,
            'UDP': 7, 'TCP': 8, 'ICMP': 9
        }
    
    def extract_from_events(self, events: List[Dict]) -> Dict:
        """
        Extract features from a list of events.
        
        Args:
            events: List of event dictionaries with source_ip, protocol, 
                   payload_size, timestamp, port
        
        Returns:
            Dictionary with feature name -> value pairs
        """
        if not events:
            return self._get_null_features()
        
        features = {}
        
        # 1. Event Count Features
        features['event_count'] = len(events)
        features['unique_ips'] = len(set(e.get('source_ip', '') for e in events))
        
        # 2. Protocol Features
        protocol_counts = defaultdict(int)
        for event in events:
            proto = event.get('protocol', 'unknown').upper()
            protocol_counts[proto] += 1
        
        features['protocol_diversity'] = len(protocol_counts)
        features['dominant_protocol_ratio'] = (
            max(protocol_counts.values()) / len(events) if events else 0
        )
        
        # 3. Temporal Features
        if len(events) > 1:
            timestamps = sorted([e.get('timestamp', 0) for e in events])
            time_span = timestamps[-1] - timestamps[0]
            features['time_span_seconds'] = time_span
            features['events_per_second'] = len(events) / (time_span + 1)
        else:
            features['time_span_seconds'] = 0
            features['events_per_second'] = 0
        
        # 4. Payload Features
        payload_sizes = [e.get('payload_size', 0) for e in events]
        features['avg_payload_size'] = sum(payload_sizes) / len(events) if events else 0
        features['max_payload_size'] = max(payload_sizes) if payload_sizes else 0
        features['min_payload_size'] = min(payload_sizes) if payload_sizes else 0
        features['payload_variance'] = self._calculate_variance(payload_sizes)
        
        # 5. Port Features
        port_counts = defaultdict(int)
        for event in events:
            port = event.get('port', 0)
            port_counts[port] += 1
        
        features['port_diversity'] = len(port_counts)
        if port_counts:
            features['ports_per_ip_avg'] = sum(port_counts.values()) / len(port_counts)
        else:
            features['ports_per_ip_avg'] = 0
        
        # 6. Attack Pattern Features
        features['has_high_rate'] = 1 if features['events_per_second'] > 10 else 0
        features['has_amplification'] = 1 if features['max_payload_size'] > 5000 else 0
        features['has_multi_protocol'] = 1 if features['protocol_diversity'] >= 3 else 0
        features['has_port_scanning'] = 1 if features['port_diversity'] > 100 else 0
        
        # 7. Protocol-Specific Features
        for proto in ['HTTP', 'DNS', 'SSDP', 'NTP']:
            count = protocol_counts.get(proto, 0)
            features[f'{proto.lower()}_ratio'] = count / len(events) if events else 0
        
        return features
    
    def _get_null_features(self) -> Dict:
        """Get zero-valued features for empty event lists"""
        return {
            'event_count': 0,
            'unique_ips': 0,
            'protocol_diversity': 0,
            'dominant_protocol_ratio': 0,
            'time_span_seconds': 0,
            'events_per_second': 0,
            'avg_payload_size': 0,
            'max_payload_size': 0,
            'min_payload_size': 0,
            'payload_variance': 0,
            'port_diversity': 0,
            'ports_per_ip_avg': 0,
            'has_high_rate': 0,
            'has_amplification': 0,
            'has_multi_protocol': 0,
            'has_port_scanning': 0,
            'http_ratio': 0,
            'dns_ratio': 0,
            'ssdp_ratio': 0,
            'ntp_ratio': 0,
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def extract_ip_features(self, profile: Dict) -> Dict:
        """
        Extract features from an IP profile (pre-aggregated data).
        
        Args:
            profile: IP profile with aggregated attack statistics
        
        Returns:
            Feature dictionary
        """
        features = {}
        
        features['total_events'] = profile.get('total_events', 0)
        features['events_per_minute'] = profile.get('events_per_minute', 0)
        features['avg_payload_size'] = profile.get('avg_payload_size', 0)
        features['protocol_count'] = len(profile.get('protocols_used', []))
        
        # Compute derived features
        features['attack_persistence'] = min(
            profile.get('events_per_minute', 0) * profile.get('total_events', 0) / 100,
            1.0
        )
        
        features['is_sustained'] = 1 if features['total_events'] > 500 else 0
        features['is_intensive'] = 1 if features['events_per_minute'] > 100 else 0
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Get ordered list of feature names"""
        return [
            'event_count', 'unique_ips', 'protocol_diversity',
            'dominant_protocol_ratio', 'time_span_seconds', 'events_per_second',
            'avg_payload_size', 'max_payload_size', 'min_payload_size',
            'payload_variance', 'port_diversity', 'ports_per_ip_avg',
            'has_high_rate', 'has_amplification', 'has_multi_protocol',
            'has_port_scanning', 'http_ratio', 'dns_ratio', 'ssdp_ratio', 'ntp_ratio'
        ]


def extract(events):
    """Backward-compatible function for basic feature extraction"""
    extractor = FeatureExtractor()
    return extractor.extract_from_events(events)