"""
Unit tests for DDoSPoT core modules.
Tests database operations, geolocation, ML features, and rate limiting.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import json
import random

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import HoneypotDatabase
from telemetry.ratelimit import RateLimiter


class TestHoneypotDatabase:
    """Tests for core.database.HoneypotDatabase"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        db = HoneypotDatabase(db_path)
        yield db
        
        # Cleanup
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    def test_database_init(self, temp_db):
        """Test database initialization"""
        assert temp_db is not None
        stats = temp_db.get_statistics()
        assert stats['total_events'] == 0
        assert stats['unique_ips'] == 0
    
    def test_add_event(self, temp_db):
        """Test adding attack events"""
        temp_db.add_event(
            source_ip="192.0.2.1",
            port=80,
            protocol="HTTP",
            payload_size=1024,
            event_type="attack"
        )
        
        stats = temp_db.get_statistics()
        assert stats['total_events'] == 1
        assert stats['unique_ips'] == 1
    
    def test_add_multiple_events(self, temp_db):
        """Test adding multiple events from different IPs"""
        ips = ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
        
        for ip in ips:
            for _ in range(5):
                temp_db.add_event(
                    source_ip=ip,
                    port=80,
                    protocol="HTTP",
                    payload_size=1024,
                    event_type="attack"
                )
        
        stats = temp_db.get_statistics()
        assert stats['total_events'] == 15
        assert stats['unique_ips'] == 3
    
    def test_get_events_by_ip(self, temp_db):
        """Test retrieving events by IP"""
        ip = "192.0.2.1"
        
        for i in range(10):
            temp_db.add_event(
                source_ip=ip,
                port=80 + i,
                protocol="HTTP",
                payload_size=1024,
                event_type="attack"
            )
        
        events = temp_db.get_events_by_ip(ip)
        assert len(events) == 10
    
    def test_get_recent_events_filtered(self, temp_db):
        """Test filtering recent events"""
        # Add events
        ips = ["192.0.2.1", "192.0.2.2"]
        protocols = ["HTTP", "DNS"]
        
        for ip in ips:
            for proto in protocols:
                for _ in range(5):
                    temp_db.add_event(
                        source_ip=ip,
                        port=80,
                        protocol=proto,
                        payload_size=1024,
                        event_type="attack"
                    )
        
        # Filter by protocol
        http_events = temp_db.get_recent_events_filtered(
            minutes=60,
            protocol="HTTP"
        )
        assert all(e['protocol'] == "HTTP" for e in http_events)
        
        # Filter by IP
        ip1_events = temp_db.get_recent_events_filtered(
            minutes=60,
            ip="192.0.2.1"
        )
        assert all(e['source_ip'] == "192.0.2.1" for e in ip1_events)
    
    def test_count_recent_events_filtered(self, temp_db):
        """Test counting filtered events"""
        # Add 20 events
        for i in range(20):
            temp_db.add_event(
                source_ip="192.0.2.1",
                port=80,
                protocol="HTTP",
                payload_size=1024,
                event_type="attack"
            )
        
        total = temp_db.count_recent_events_filtered(minutes=60)
        assert total == 20
        
        # With offset and limit
        events = temp_db.get_recent_events_filtered(
            minutes=60,
            limit=5,
            offset=0
        )
        assert len(events) == 5
    
    def test_get_top_attackers(self, temp_db):
        """Test retrieving top attackers"""
        # Add events from multiple IPs
        ips_events = {"192.0.2.1": 50, "192.0.2.2": 30, "192.0.2.3": 10}
        
        for ip, count in ips_events.items():
            for _ in range(count):
                temp_db.add_event(
                    source_ip=ip,
                    port=80,
                    protocol="HTTP",
                    payload_size=1024,
                    event_type="attack"
                )
        
        attackers = temp_db.get_top_attackers(3)
        assert len(attackers) == 3
        assert attackers[0]['ip'] == "192.0.2.1"
        assert attackers[0]['total_events'] == 50
    
    def test_cleanup_old_events(self, temp_db):
        """Test cleaning up old events"""
        import time
        
        # Add old event
        db_path = temp_db.db_path
        
        # Insert manually into database (circumvent timestamp)
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        old_timestamp = (datetime.now() - timedelta(days=40)).timestamp()
        cursor.execute(
            "INSERT INTO events (source_ip, port, protocol, payload_size, event_type, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            ("192.0.2.1", 80, "HTTP", 1024, "attack", old_timestamp)
        )
        conn.commit()
        conn.close()
        
        # Add recent event
        temp_db.add_event(
            source_ip="192.0.2.2",
            port=80,
            protocol="HTTP",
            payload_size=1024,
            event_type="attack"
        )
        
        stats_before = temp_db.get_statistics()
        assert stats_before['total_events'] == 2
        
        # Cleanup events older than 30 days
        removed = temp_db.cleanup_old_events(30)
        assert removed == 1
        
        stats_after = temp_db.get_statistics()
        assert stats_after['total_events'] == 1
    
    def test_get_database_size(self, temp_db):
        """Test getting database size info"""
        # Add some events
        for _ in range(100):
            temp_db.add_event(
                source_ip="192.0.2.1",
                port=80,
                protocol="HTTP",
                payload_size=1024,
                event_type="attack"
            )
        
        size_info = temp_db.get_database_size()
        assert size_info['size_mb'] > 0
        assert size_info['event_count'] == 100
        assert 'file_path' in size_info


class TestRateLimiter:
    """Tests for telemetry.ratelimit.RateLimiter"""
    
    def test_rate_limiter_init(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(max_events=10, window_seconds=60)
        assert limiter.max_events == 10
        assert limiter.window == 60
    
    def test_register_event_within_limit(self):
        """Test registering events within limit"""
        limiter = RateLimiter(max_events=5, window_seconds=60)
        ip = "192.0.2.1"
        
        for i in range(5):
            allowed = limiter.register_event(ip)
            assert allowed is True
    
    def test_register_event_exceeds_limit(self):
        """Test that exceeding limit returns False"""
        limiter = RateLimiter(max_events=3, window_seconds=60)
        ip = "192.0.2.1"
        
        # First 3 should be allowed
        for i in range(3):
            allowed = limiter.register_event(ip)
            assert allowed is True
        
        # 4th should be denied and IP blacklisted
        allowed = limiter.register_event(ip)
        assert allowed is False
    
    def test_ip_blacklist(self):
        """Test that IP is blacklisted after exceeding limit"""
        limiter = RateLimiter(max_events=2, window_seconds=60, blacklist_seconds=60)
        ip = "192.0.2.1"
        
        # Exceed limit
        for i in range(3):
            limiter.register_event(ip)
        
        # Check blacklist
        assert limiter.is_blacklisted(ip) is True
    
    def test_multiple_ips(self):
        """Test that different IPs are tracked separately"""
        limiter = RateLimiter(max_events=3, window_seconds=60)
        ips = ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
        
        for ip in ips:
            for i in range(3):
                allowed = limiter.register_event(ip)
                assert allowed is True
        
        # Each IP should have 3 events registered
        for ip in ips:
            assert limiter.register_event(ip) is False
    
    def test_sliding_window(self):
        """Test sliding window behavior"""
        import time
        
        limiter = RateLimiter(max_events=2, window_seconds=1)
        ip = "192.0.2.1"
        
        # Register 2 events
        for i in range(2):
            assert limiter.register_event(ip) is True
        
        # 3rd within window should fail
        assert limiter.register_event(ip) is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.register_event(ip) is True


class TestEventStatistics:
    """Tests for event statistics and aggregation"""
    
    @pytest.fixture
    def temp_db_with_events(self):
        """Create DB with sample events"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        db = HoneypotDatabase(db_path)
        
        # Add events across multiple protocols and IPs
        protocols = ["HTTP", "DNS", "SSH", "NTP"]
        ips = [f"192.0.2.{i}" for i in range(1, 6)]
        
        for ip in ips:
            for proto in protocols:
                for _ in range(random.randint(1, 10)):
                    db.add_event(
                        source_ip=ip,
                        port=80 if proto == "HTTP" else 53,
                        protocol=proto,
                        payload_size=random.randint(100, 5000),
                        event_type="attack"
                    )
        
        yield db
        
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    def test_statistics_consistency(self, temp_db_with_events):
        """Test that statistics are consistent"""
        stats = temp_db_with_events.get_statistics()
        
        assert stats['total_events'] > 0
        assert stats['unique_ips'] > 0
        assert stats['unique_ips'] <= len([f"192.0.2.{i}" for i in range(1, 6)])
        assert stats['top_protocol'] is not None
        assert stats['top_port'] is not None


# Run with: pytest test_core_modules.py -v
if __name__ == "__main__":
    import random
    pytest.main([__file__, "-v"])

