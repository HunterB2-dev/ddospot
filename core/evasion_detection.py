"""
Advanced Evasion Detection System for DDoSPot Honeypot

Detects sophisticated attack patterns:
- Slow distributed attacks
- Protocol confusion attacks
- Polymorphic attack signatures
- Behavioral anomalies
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib


class SlowAttackDetector:
    """Detects slow distributed attacks that stay below rate thresholds"""
    
    def __init__(self, window_sizes=(60, 300, 3600)):
        """
        Args:
            window_sizes: Tuple of time windows in seconds (1min, 5min, 1hour)
        """
        self.window_sizes = window_sizes
        self.request_windows = defaultdict(lambda: {ws: deque() for ws in window_sizes})
        self.slow_attack_threshold = 5  # Minimum consistency score
    
    def record_request(self, source_ip: str, timestamp: float) -> None:
        """Record a request from an IP"""
        for window_size in self.window_sizes:
            window = self.request_windows[source_ip][window_size]
            window.append(timestamp)
            
            # Remove old requests outside window
            cutoff = timestamp - window_size
            while window and window[0] < cutoff:
                window.popleft()
    
    def calculate_consistency(self, source_ip: str) -> float:
        """
        Calculate how consistent the request pattern is.
        Slow attacks have regular, predictable timing.
        
        Returns: Score 0.0-1.0 (higher = more consistent = more suspicious)
        """
        window = self.request_windows[source_ip][60]  # Use 1-minute window
        
        if len(window) < 3:
            return 0.0
        
        # Calculate intervals between requests
        times = sorted(window)
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        
        if not intervals:
            return 0.0
        
        # Calculate variance in intervals (low variance = consistent = suspicious)
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        
        # Coefficient of variation (normalized standard deviation)
        if avg_interval > 0:
            cv = std_dev / avg_interval
            # Normalize: CV=0 is 1.0 score, CV>1 is 0.0 score
            consistency = max(0.0, 1.0 - cv)
        else:
            consistency = 0.0
        
        return consistency
    
    def detect_slow_attack(self, source_ip: str, min_requests: int = 5) -> Tuple[float, Dict]:
        """
        Detect if an IP is conducting a slow attack.
        
        Returns:
            (score, details) - Score 0.0-1.0, dict with detection details
        """
        window = self.request_windows[source_ip][60]
        
        # Need minimum request volume
        if len(window) < min_requests:
            return 0.0, {"reason": "insufficient_data"}
        
        consistency = self.calculate_consistency(source_ip)
        request_count = len(window)
        
        # Score based on consistency and request count
        score = consistency * 0.7 + (min(request_count, 20) / 20) * 0.3
        
        details = {
            "consistency_score": round(consistency, 3),
            "request_count": request_count,
            "score": round(score, 3),
            "pattern": "sustained_low_rate" if score > 0.6 else "normal"
        }
        
        return score, details


class ProtocolConfusionDetector:
    """Detects attacks using multiple protocols from single source"""
    
    def __init__(self, confusion_window: int = 300):
        """
        Args:
            confusion_window: Time window to track protocol usage (seconds)
        """
        self.confusion_window = confusion_window
        self.protocol_history = defaultdict(lambda: deque())
        self.protocol_signatures = defaultdict(lambda: deque())
    
    def record_protocol_use(self, source_ip: str, protocol: str, payload_hash: str, timestamp: float) -> None:
        """Record protocol usage from an IP"""
        self.protocol_history[source_ip].append({
            "protocol": protocol,
            "timestamp": timestamp,
            "payload_hash": payload_hash
        })
        
        self.protocol_signatures[source_ip].append({
            "protocol": protocol,
            "hash": payload_hash
        })
        
        # Remove old entries
        cutoff = timestamp - self.confusion_window
        while self.protocol_history[source_ip] and self.protocol_history[source_ip][0]["timestamp"] < cutoff:
            self.protocol_history[source_ip].popleft()
            self.protocol_signatures[source_ip].popleft()
    
    def detect_protocol_confusion(self, source_ip: str) -> Tuple[float, Dict]:
        """
        Detect if an IP is mixing protocols in suspicious ways.
        
        Returns:
            (score, details) - Score 0.0-1.0, dict with detection details
        """
        history = list(self.protocol_history[source_ip])
        
        if len(history) < 2:
            return 0.0, {"reason": "insufficient_data"}
        
        # Count unique protocols
        protocols = set(h["protocol"] for h in history)
        unique_count = len(protocols)
        
        # Calculate protocol switch frequency
        switches = sum(1 for i in range(len(history)-1) 
                      if history[i]["protocol"] != history[i+1]["protocol"])
        switch_rate = switches / len(history) if history else 0
        
        # Check for payload inconsistency per protocol
        protocol_payloads = defaultdict(set)
        for entry in history:
            protocol_payloads[entry["protocol"]].add(entry["payload_hash"])
        
        payload_variation = sum(len(hashes) for hashes in protocol_payloads.values()) / len(history)
        
        # Score: Higher for protocol mixing + payload inconsistency
        protocol_score = min(unique_count / 5, 1.0)  # Normalized by typical max 5 protocols
        switch_score = min(switch_rate * 2, 1.0)  # High switch rate is suspicious
        variation_score = min(payload_variation / 3, 1.0)  # Varied payloads suspicious
        
        score = (protocol_score * 0.3 + switch_score * 0.4 + variation_score * 0.3)
        
        details = {
            "unique_protocols": unique_count,
            "protocol_list": sorted(list(protocols)),
            "switch_rate": round(switch_rate, 3),
            "payload_variation": round(payload_variation, 3),
            "score": round(score, 3),
            "pattern": "protocol_confusion" if score > 0.6 else "normal"
        }
        
        return score, details


class PolymorphicDetector:
    """Detects polymorphic attacks with varying payloads"""
    
    def __init__(self):
        self.payload_cache = {}  # Map payload_hash -> base_pattern
        self.known_patterns = {}  # Known attack patterns
    
    def add_known_pattern(self, pattern_name: str, signatures: List[str]) -> None:
        """Add a known polymorphic attack pattern"""
        self.known_patterns[pattern_name] = signatures
    
    def calculate_payload_hash(self, payload: bytes) -> str:
        """Calculate hash of payload"""
        return hashlib.sha256(payload).hexdigest()
    
    def calculate_fuzzy_hash(self, payload: bytes) -> str:
        """
        Calculate a fuzzy hash that matches similar payloads
        (useful for polymorphic variants)
        """
        # Simple fuzzy approach: hash of sorted byte chunks
        chunk_size = 16
        chunks = [payload[i:i+chunk_size] for i in range(0, len(payload), chunk_size)]
        sorted_chunks = sorted(chunks)
        combined = b''.join(sorted_chunks)
        return hashlib.sha256(combined).hexdigest()
    
    def detect_polymorphic_attack(self, payload: bytes, source_ip: str) -> Tuple[float, Dict]:
        """
        Detect if payload is a polymorphic variant of known attack.
        
        Returns:
            (score, details) - Score 0.0-1.0, dict with detection details
        """
        payload_hash = self.calculate_payload_hash(payload)
        fuzzy_hash = self.calculate_fuzzy_hash(payload)
        
        # Check against known patterns
        matches = []
        for pattern_name, signatures in self.known_patterns.items():
            for sig in signatures:
                if sig in payload.decode('utf-8', errors='ignore'):
                    matches.append(pattern_name)
        
        # Payload size analysis
        payload_size = len(payload)
        entropy = self._calculate_entropy(payload)
        
        # Calculate obfuscation likelihood
        if entropy > 6.0:  # High entropy suggests compression/encryption
            obfuscation_score = min(entropy / 8.0, 1.0)
        else:
            obfuscation_score = 0.0
        
        # Overall score
        if matches:
            pattern_score = 0.8  # Known pattern detected
        else:
            pattern_score = 0.0
        
        score = (pattern_score * 0.5 + obfuscation_score * 0.5)
        
        details = {
            "payload_hash": payload_hash[:16],
            "fuzzy_hash": fuzzy_hash[:16],
            "payload_size": payload_size,
            "entropy": round(entropy, 2),
            "matched_patterns": matches,
            "obfuscation_score": round(obfuscation_score, 3),
            "score": round(score, 3),
            "pattern": "polymorphic" if score > 0.6 else "normal"
        }
        
        return score, details
    
    @staticmethod
    def _calculate_entropy(data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        entropy = 0.0
        for i in range(256):
            p_x = data.count(i) / len(data)
            if p_x > 0:
                entropy -= p_x * math.log2(p_x)
        
        return entropy


class BehavioralAnomalyDetector:
    """Detects behavioral anomalies and deviations from baseline"""
    
    def __init__(self, baseline_window: int = 3600):
        """
        Args:
            baseline_window: Time to establish baseline behavior (seconds)
        """
        self.baseline_window = baseline_window
        self.baselines = {}  # IP -> baseline profile
        self.observations = defaultdict(lambda: deque())
    
    def record_observation(self, source_ip: str, protocol: str, 
                          payload_size: int, timestamp: float) -> None:
        """Record observations for baseline establishment"""
        obs = {
            "protocol": protocol,
            "payload_size": payload_size,
            "timestamp": timestamp
        }
        self.observations[source_ip].append(obs)
        
        # Remove old observations
        cutoff = timestamp - self.baseline_window
        while self.observations[source_ip] and self.observations[source_ip][0]["timestamp"] < cutoff:
            self.observations[source_ip].popleft()
    
    def establish_baseline(self, source_ip: str) -> Dict:
        """Establish behavior baseline for an IP"""
        observations = list(self.observations[source_ip])
        
        if len(observations) < 10:
            return None  # type: ignore  # Not enough data
        
        # Calculate baseline metrics
        payload_sizes = [o["payload_size"] for o in observations]
        protocols = [o["protocol"] for o in observations]
        
        baseline = {
            "avg_payload_size": sum(payload_sizes) / len(payload_sizes),
            "median_payload_size": sorted(payload_sizes)[len(payload_sizes)//2],
            "min_payload_size": min(payload_sizes),
            "max_payload_size": max(payload_sizes),
            "common_protocols": dict((p, protocols.count(p)) for p in set(protocols)),
            "observation_count": len(observations),
            "established_at": datetime.now().isoformat()
        }
        
        self.baselines[source_ip] = baseline
        return baseline
    
    def detect_anomaly(self, source_ip: str, protocol: str, 
                      payload_size: int) -> Tuple[float, Dict]:
        """
        Detect behavioral anomalies compared to baseline.
        
        Returns:
            (score, details) - Score 0.0-1.0, dict with detection details
        """
        baseline = self.baselines.get(source_ip)
        
        if not baseline:
            return 0.0, {"reason": "no_baseline"}
        
        # Compare current observation to baseline
        size_deviation = abs(payload_size - baseline["avg_payload_size"])
        max_expected_deviation = baseline["max_payload_size"] - baseline["min_payload_size"]
        
        if max_expected_deviation > 0:
            size_anomaly_score = min(size_deviation / max_expected_deviation, 1.0)
        else:
            size_anomaly_score = 0.0
        
        # Protocol anomaly
        common_protocols = baseline["common_protocols"]
        protocol_frequency = common_protocols.get(protocol, 0) / baseline["observation_count"]
        
        if protocol_frequency < 0.1:  # Rare protocol for this IP
            protocol_anomaly_score = 0.7
        elif protocol_frequency < 0.3:
            protocol_anomaly_score = 0.3
        else:
            protocol_anomaly_score = 0.0
        
        # Combined anomaly score
        score = (size_anomaly_score * 0.4 + protocol_anomaly_score * 0.6)
        
        details = {
            "size_deviation": size_deviation,
            "expected_size": baseline["avg_payload_size"],
            "protocol_frequency": round(protocol_frequency, 3),
            "size_anomaly": round(size_anomaly_score, 3),
            "protocol_anomaly": round(protocol_anomaly_score, 3),
            "score": round(score, 3),
            "pattern": "behavioral_anomaly" if score > 0.6 else "normal"
        }
        
        return score, details


class EvasonDetectionManager:
    """Central manager for all evasion detection strategies"""
    
    def __init__(self):
        self.slow_detector = SlowAttackDetector()
        self.protocol_detector = ProtocolConfusionDetector()
        self.polymorphic_detector = PolymorphicDetector()
        self.behavioral_detector = BehavioralAnomalyDetector()
        
        # Detection results
        self.detections = defaultdict(list)
    
    def record_event(self, source_ip: str, protocol: str, payload: bytes, timestamp: float) -> None:
        """Record an event for analysis"""
        self.slow_detector.record_request(source_ip, timestamp)
        
        payload_hash = hashlib.sha256(payload).hexdigest()
        self.protocol_detector.record_protocol_use(source_ip, protocol, payload_hash, timestamp)
        
        self.behavioral_detector.record_observation(source_ip, protocol, len(payload), timestamp)
    
    def analyze_evasion(self, source_ip: str, payload: bytes) -> Dict:
        """
        Perform comprehensive evasion analysis for an IP.
        
        Returns:
            Dict with all detection scores and details
        """
        # Detect slow attacks
        slow_score, slow_details = self.slow_detector.detect_slow_attack(source_ip)
        
        # Detect protocol confusion
        proto_score, proto_details = self.protocol_detector.detect_protocol_confusion(source_ip)
        
        # Detect polymorphic attacks
        poly_score, poly_details = self.polymorphic_detector.detect_polymorphic_attack(payload, source_ip)
        
        # Detect behavioral anomalies
        behavioral_score, behavioral_details = self.behavioral_detector.detect_anomaly(
            source_ip, "unknown", len(payload)
        )
        
        # Calculate overall evasion score
        overall_score = (
            slow_score * 0.25 +
            proto_score * 0.25 +
            poly_score * 0.25 +
            behavioral_score * 0.25
        )
        
        # Determine threat level
        if overall_score >= 0.8:
            threat_level = "CRITICAL"
        elif overall_score >= 0.6:
            threat_level = "HIGH"
        elif overall_score >= 0.3:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"
        
        analysis = {
            "source_ip": source_ip,
            "timestamp": datetime.now().isoformat(),
            "overall_evasion_score": round(overall_score, 3),
            "threat_level": threat_level,
            "detections": {
                "slow_attack": {
                    "score": round(slow_score, 3),
                    "details": slow_details
                },
                "protocol_confusion": {
                    "score": round(proto_score, 3),
                    "details": proto_details
                },
                "polymorphic": {
                    "score": round(poly_score, 3),
                    "details": poly_details
                },
                "behavioral_anomaly": {
                    "score": round(behavioral_score, 3),
                    "details": behavioral_details
                }
            }
        }
        
        # Store detection if score is significant
        if overall_score > 0.3:
            self.detections[source_ip].append(analysis)
        
        return analysis
    
    def get_detections(self, source_ip: str) -> List[Dict]:
        """Get all evasion detections for an IP"""
        return self.detections.get(source_ip, [])
    
    def get_detection_summary(self, source_ip: str) -> Dict:
        """Get summary statistics of detections for an IP"""
        detections = self.get_detections(source_ip)
        
        if not detections:
            return {"total": 0}
        
        scores = [d["overall_evasion_score"] for d in detections]
        threats = [d["threat_level"] for d in detections]
        
        return {
            "total": len(detections),
            "avg_score": round(sum(scores) / len(scores), 3),
            "max_score": round(max(scores), 3),
            "threat_levels": dict((t, threats.count(t)) for t in set(threats)),
            "latest": detections[-1] if detections else None
        }


# Singleton instance
_evasion_manager = None


def get_evasion_manager() -> EvasonDetectionManager:
    """Get or create the evasion detection manager"""
    global _evasion_manager
    if _evasion_manager is None:
        _evasion_manager = EvasonDetectionManager()
    return _evasion_manager


def reset_evasion_manager() -> None:
    """Reset the evasion detection manager (for testing)"""
    global _evasion_manager
    _evasion_manager = None
