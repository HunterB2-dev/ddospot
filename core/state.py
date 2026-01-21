import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class AttackEvent:
    """Represents a single attack event"""
    timestamp: float
    source_ip: str
    port: int
    protocol: str
    payload_size: int
    event_type: str  # "connection", "packet", "http_request", etc.


@dataclass
class IPAttackProfile:
    """Profile of attacks from a single IP"""
    ip: str
    first_seen: float
    last_seen: float
    total_events: int
    events_per_minute: float
    attack_type: str  # "volumetric", "protocol", "application", "mixed"
    protocols_used: set
    avg_payload_size: float
    

class HoneypotState:
    """Enhanced honeypot state manager with advanced detection"""
    
    def __init__(self, window_size_seconds: int = 60, rate_threshold: int = 100):
        # Time window for rate limiting (default 60 seconds)
        self.window_size = window_size_seconds
        self.rate_threshold = rate_threshold
        
        # Track events per IP in time windows
        self.activity = defaultdict(lambda: deque())  # IP -> list of events
        
        # Blacklist: IP -> expiration_time
        self.blacklist = {}
        
        # Attack statistics for analysis
        self.attack_profiles: Dict[str, IPAttackProfile] = {}
        
        # Global statistics
        self.total_events = 0
        self.start_time = time.time()

    def record_event(self, source_ip: str, port: int, protocol: str, 
                    payload_size: int, event_type: str = "connection") -> bool:
        """
        Record an event from an IP.
        Returns True if the IP should be investigated, False if already blacklisted.
        """
        current_time = time.time()
        
        # Check if already blacklisted
        if self.is_blacklisted(source_ip):
            return False
        
        # Create event
        event = AttackEvent(
            timestamp=current_time,
            source_ip=source_ip,
            port=port,
            protocol=protocol,
            payload_size=payload_size,
            event_type=event_type
        )
        
        # Add to activity log
        self.activity[source_ip].append(event)
        self.total_events += 1
        
        # Update attack profile
        self._update_attack_profile(source_ip, event)
        
        return True
    
    def _update_attack_profile(self, source_ip: str, event: AttackEvent):
        """Update the attack profile for an IP"""
        if source_ip not in self.attack_profiles:
            self.attack_profiles[source_ip] = IPAttackProfile(
                ip=source_ip,
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                total_events=1,
                events_per_minute=1,
                attack_type="unknown",
                protocols_used={event.protocol},
                avg_payload_size=event.payload_size
            )
        else:
            profile = self.attack_profiles[source_ip]
            profile.last_seen = event.timestamp
            profile.total_events += 1
            profile.protocols_used.add(event.protocol)
            profile.avg_payload_size = (
                (profile.avg_payload_size * (profile.total_events - 1) + event.payload_size) 
                / profile.total_events
            )
            
            # Calculate events per minute
            time_elapsed = (event.timestamp - profile.first_seen) / 60
            if time_elapsed > 0:
                profile.events_per_minute = profile.total_events / time_elapsed
            
            # Classify attack type
            self._classify_attack_type(profile)

    def _classify_attack_type(self, profile: IPAttackProfile):
        """Classify the type of attack based on patterns"""
        if profile.events_per_minute > 1000:
            profile.attack_type = "volumetric"  # Flood attack
        elif len(profile.protocols_used) > 2:
            profile.attack_type = "mixed"  # Attacking multiple services
        elif profile.avg_payload_size > 1000:
            profile.attack_type = "amplification"  # Amplification attack (e.g., SSDP)
        else:
            profile.attack_type = "protocol"  # Targeted protocol attack

    def get_attack_rate(self, source_ip: str) -> int:
        """Get the number of events from an IP in the current time window"""
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Clean old events outside the window
        events = self.activity[source_ip]
        while events and events[0].timestamp < window_start:
            events.popleft()
        
        return len(events)

    def should_blacklist(self, source_ip: str) -> bool:
        """Determine if an IP should be blacklisted based on attack rate"""
        rate = self.get_attack_rate(source_ip)
        return rate >= self.rate_threshold

    def is_blacklisted(self, ip: str) -> bool:
        """Check if an IP is currently blacklisted"""
        if ip not in self.blacklist:
            return False
        
        # Check if blacklist has expired
        if self.blacklist[ip] > time.time():
            return True
        else:
            # Expired, remove from blacklist
            del self.blacklist[ip]
            return False

    def blacklist_ip(self, ip: str, duration: int):
        """Add an IP to the blacklist for a specified duration (seconds)"""
        self.blacklist[ip] = time.time() + duration

    def get_blacklist(self) -> Dict[str, float]:
        """Get all currently blacklisted IPs with their expiration times"""
        now = time.time()
        active_blacklist = {
            ip: exp_time for ip, exp_time in self.blacklist.items()
            if exp_time > now
        }
        return active_blacklist

    def cleanup_expired_blacklist(self):
        """Remove expired entries from blacklist"""
        now = time.time()
        expired = [ip for ip, exp_time in self.blacklist.items() if exp_time <= now]
        for ip in expired:
            del self.blacklist[ip]

    def get_statistics(self) -> dict:
        """Get overall honeypot statistics"""
        return {
            "total_events": self.total_events,
            "unique_ips": len(self.attack_profiles),
            "blacklisted_ips": len(self.get_blacklist()),
            "uptime_seconds": time.time() - self.start_time,
            "top_attackers": self._get_top_attackers(5),
        }

    def _get_top_attackers(self, limit: int = 5) -> List[dict]:
        """Get the top attacking IPs by event count"""
        sorted_profiles = sorted(
            self.attack_profiles.values(),
            key=lambda p: p.total_events,
            reverse=True
        )[:limit]
        
        return [
            {
                "ip": p.ip,
                "events": p.total_events,
                "type": p.attack_type,
                "rate": round(p.events_per_minute, 2),
                "protocols": list(p.protocols_used),
            }
            for p in sorted_profiles
        ]
