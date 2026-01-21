"""
Advanced DDoS detection engine for the honeypot.
Identifies attack patterns and determines blacklist actions.
"""

from typing import Tuple


class AttackDetector:
    """Multi-factor attack detection engine"""
    
    def __init__(self, rate_threshold: int = 100, window_seconds: int = 60):
        """
        Initialize the attack detector.
        
        Args:
            rate_threshold: Events per minute to trigger blacklist
            window_seconds: Time window for rate calculation
        """
        self.rate_threshold = rate_threshold
        self.window_seconds = window_seconds

    def analyze_attack(self, state, source_ip: str) -> Tuple[bool, str, int]:
        """
        Analyze an attack pattern and determine if blacklist is warranted.
        
        Returns:
            (should_blacklist, reason, suggested_duration_seconds)
        """
        # Get current attack rate
        rate = state.get_attack_rate(source_ip)
        
        # Get attack profile
        profile = state.attack_profiles.get(source_ip)
        
        if not profile:
            return False, "no_profile", 0
        
        # Decision factors
        should_blacklist = False
        reason = "unknown"
        duration = 0
        
        # Factor 1: High rate (volumetric attack)
        if rate > self.rate_threshold:
            should_blacklist = True
            reason = "volumetric_attack"
            duration = 3600  # 1 hour
        
        # Factor 2: Multi-protocol attack (coordinated attack)
        elif len(profile.protocols_used) >= 3:
            should_blacklist = True
            reason = "multi_protocol_attack"
            duration = 7200  # 2 hours - more suspicious
        
        # Factor 3: Very high average payload (amplification attack)
        elif profile.avg_payload_size > 5000 and rate > 50:
            should_blacklist = True
            reason = "amplification_attack"
            duration = 3600
        
        # Factor 4: Sustained attack (many events over long period)
        elif profile.total_events > 1000 and profile.events_per_minute > 100:
            should_blacklist = True
            reason = "sustained_attack"
            duration = 7200
        
        # Factor 5: Rapid escalation
        elif rate > self.rate_threshold * 2:
            should_blacklist = True
            reason = "rapid_escalation"
            duration = 1800  # 30 minutes
        
        return should_blacklist, reason, duration

    def get_attack_severity(self, state, source_ip: str) -> str:
        """
        Classify attack severity: low, medium, high, critical
        """
        profile = state.attack_profiles.get(source_ip)
        if not profile:
            return "none"
        
        rate = state.get_attack_rate(source_ip)
        
        # Severity scoring
        score = 0
        
        # Rate component (0-40 points)
        score += min(40, int((rate / self.rate_threshold) * 40))
        
        # Protocol diversity component (0-20 points)
        score += min(20, len(profile.protocols_used) * 5)
        
        # Payload size component (0-20 points)
        if profile.avg_payload_size > 1000:
            score += 20
        elif profile.avg_payload_size > 500:
            score += 10
        
        # Duration component (0-20 points)
        duration = profile.last_seen - profile.first_seen
        if duration > 3600:  # > 1 hour
            score += 20
        elif duration > 300:  # > 5 minutes
            score += 10
        
        # Classify
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def should_blacklist(self, events, threshold):
        """Legacy compatibility function"""
        return len(events) > threshold


def classify_attack_type(profile) -> str:
    """
    Classify the attack type based on profile characteristics.
    """
    if profile.events_per_minute > 1000:
        return "volumetric"  # Flood attack (SYN flood, UDP flood, etc.)
    elif len(profile.protocols_used) > 2:
        return "mixed"  # Multi-protocol coordinated attack
    elif profile.avg_payload_size > 1000:
        return "amplification"  # Amplification attack (DNS, NTP, SSDP)
    elif profile.avg_payload_size < 64:
        return "slowloris"  # Slow attacks
    else:
        return "protocol"  # Targeted protocol fuzzing/bruteforce


def format_attack_summary(ip: str, profile, severity: str) -> str:
    """Format a human-readable attack summary"""
    return (
        f"[{severity.upper()}] {ip}: "
        f"{profile.total_events} events, "
        f"{profile.events_per_minute:.1f} evt/min, "
        f"type={profile.attack_type}, "
        f"protocols={','.join(profile.protocols_used)}"
    )
