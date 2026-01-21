"""
SQLite database persistence for the honeypot.
Stores attack events, IP profiles, and statistics for analysis.
"""

import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class HoneypotDatabase:
    """SQLite database manager for persistent attack storage"""
    
    def __init__(self, db_path: str = "honeypot.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn: sqlite3.Connection = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Events table - stores individual attack packets/connections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                source_ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                payload_size INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for events table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_source_ip ON events(source_ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_protocol ON events(protocol)")
        
        # IP Profiles table - aggregated statistics per IP
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_profiles (
                ip TEXT PRIMARY KEY,
                first_seen REAL NOT NULL,
                last_seen REAL NOT NULL,
                total_events INTEGER DEFAULT 0,
                events_per_minute REAL DEFAULT 0,
                attack_type TEXT,
                protocols_used TEXT,
                avg_payload_size REAL DEFAULT 0,
                severity TEXT DEFAULT 'low',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Blacklist table - tracks blacklisted IPs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                ip TEXT PRIMARY KEY,
                reason TEXT,
                blacklist_time REAL NOT NULL,
                expiration_time REAL NOT NULL,
                duration_seconds INTEGER,
                severity TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blacklist_expiration ON blacklist(expiration_time)")
        
        # Attack summary table - aggregated daily statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attack_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_events INTEGER DEFAULT 0,
                unique_ips INTEGER DEFAULT 0,
                top_protocol TEXT,
                avg_severity TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        """)
        
        self.conn.commit()
    
    # ========================
    # EVENT OPERATIONS
    # ========================
    
    def add_event(self, source_ip: str, port: int, protocol: str, 
                 payload_size: int, event_type: str, timestamp: Optional[float] = None) -> int:
        """Add an attack event to the database and update IP profile"""
        if timestamp is None:
            timestamp = time.time()
        
            # Record metrics
            try:
                from telemetry.prometheus_metrics import get_metrics
                metrics = get_metrics()
                metrics.record_attack_event(protocol, event_type, payload_size)
            except Exception:
                pass  # Don't fail if metrics unavailable
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (timestamp, source_ip, port, protocol, payload_size, event_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (timestamp, source_ip, port, protocol, payload_size, event_type),
        )
        self.conn.commit()

        # Update or create IP profile based on aggregated stats
        try:
            cursor.execute(
                """
                SELECT MIN(timestamp) AS first_seen,
                       MAX(timestamp) AS last_seen,
                       COUNT(*) AS total_events,
                       AVG(payload_size) AS avg_payload,
                       GROUP_CONCAT(DISTINCT protocol) AS protocols_used
                FROM events
                WHERE source_ip = ?
                """,
                (source_ip,),
            )
            row = cursor.fetchone()
            if row and row["total_events"]:
                first_seen = float(row["first_seen"]) if row["first_seen"] else timestamp
                last_seen = float(row["last_seen"]) if row["last_seen"] else timestamp
                total_events = int(row["total_events"]) or 0
                avg_payload = float(row["avg_payload"]) if row["avg_payload"] else 0.0
                protocols_used = row["protocols_used"] or protocol

                # Events per minute based on active duration
                duration_minutes = max(1.0, (last_seen - first_seen) / 60.0)
                events_per_minute = total_events / duration_minutes

                # Basic severity heuristic (optional)
                severity = (
                    "critical" if total_events >= 1000 else
                    "high" if total_events >= 100 else
                    "medium" if total_events >= 20 else
                    "low"
                )

                self.add_or_update_profile(
                    ip=source_ip,
                    first_seen=first_seen,
                    last_seen=last_seen,
                    total_events=total_events,
                    events_per_minute=events_per_minute,
                    attack_type="unknown",
                    protocols_used=protocols_used.split(",") if protocols_used else [protocol],
                    avg_payload_size=avg_payload,
                    severity=severity,
                )
        except Exception:
            # Profile updates should not interrupt event ingestion
            pass

        return int(cursor.lastrowid) if cursor.lastrowid else 0
    
    def get_events_by_ip(self, source_ip: str, limit: int = 100) -> List[Dict]:
        """Retrieve all events from a specific IP"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM events 
            WHERE source_ip = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (source_ip, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_events_in_timerange(self, start_time: float, end_time: float, 
                               limit: int = 10000) -> List[Dict]:
        """Retrieve events within a time range"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM events 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (start_time, end_time, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_events(self, minutes: int = 60, limit: int = 10000) -> List[Dict]:
        """Retrieve events from the last N minutes"""
        start_time = time.time() - (minutes * 60)
        return self.get_events_in_timerange(start_time, time.time(), limit)

    def get_recent_events_filtered(self, minutes: int = 60, limit: int = 100, offset: int = 0,
                                   ip: Optional[str] = None, protocol: Optional[str] = None,
                                   event_type: Optional[str] = None) -> List[Dict]:
        """Retrieve filtered recent events with pagination"""
        start_time = time.time() - (minutes * 60)
        params: List = [start_time, time.time()]
        where = ["timestamp BETWEEN ? AND ?"]
        if ip:
            where.append("source_ip LIKE ?")
            params.append(f"%{ip}%")
        if protocol:
            where.append("protocol = ?")
            params.append(protocol)
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)
        where_sql = " AND ".join(where)
        sql = f"""
            SELECT * FROM events
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def count_recent_events_filtered(self, minutes: int = 60,
                                     ip: Optional[str] = None, protocol: Optional[str] = None,
                                     event_type: Optional[str] = None) -> int:
        """Count filtered recent events for pagination"""
        start_time = time.time() - (minutes * 60)
        params: List = [start_time, time.time()]
        where = ["timestamp BETWEEN ? AND ?"]
        if ip:
            where.append("source_ip LIKE ?")
            params.append(f"%{ip}%")
        if protocol:
            where.append("protocol = ?")
            params.append(protocol)
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)
        where_sql = " AND ".join(where)
        sql = f"SELECT COUNT(*) as count FROM events WHERE {where_sql}"
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return int(row["count"]) if row else 0
    
    def count_events_by_ip(self, source_ip: str, minutes: int = 60) -> int:
        """Count events from an IP in the last N minutes"""
        cursor = self.conn.cursor()
        start_time = time.time() - (minutes * 60)
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM events
            WHERE source_ip = ? AND timestamp > ?
        """, (source_ip, start_time))
        
        result = cursor.fetchone()
        return result['count'] if result else 0
    
    # ========================
    # IP PROFILE OPERATIONS
    # ========================
    
    def add_or_update_profile(self, ip: str, first_seen: float, last_seen: float,
                             total_events: int, events_per_minute: float,
                             attack_type: str, protocols_used: List[str],
                             avg_payload_size: float, severity: str):
        """Add or update an IP profile"""
        cursor = self.conn.cursor()
        protocols_str = ",".join(sorted(set(protocols_used)))
        
        cursor.execute("""
            INSERT INTO ip_profiles 
            (ip, first_seen, last_seen, total_events, events_per_minute, 
             attack_type, protocols_used, avg_payload_size, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ip) DO UPDATE SET
                last_seen = excluded.last_seen,
                total_events = excluded.total_events,
                events_per_minute = excluded.events_per_minute,
                attack_type = excluded.attack_type,
                protocols_used = excluded.protocols_used,
                avg_payload_size = excluded.avg_payload_size,
                severity = excluded.severity,
                updated_at = CURRENT_TIMESTAMP
        """, (ip, first_seen, last_seen, total_events, events_per_minute,
              attack_type, protocols_str, avg_payload_size, severity))
        
        self.conn.commit()
    
    def get_profile(self, ip: str) -> Optional[Dict]:
        """Retrieve an IP profile"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ip_profiles WHERE ip = ?", (ip,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_top_attackers(self, limit: int = 10) -> List[Dict]:
        """Retrieve the top attacking IPs by event count"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM ip_profiles
            ORDER BY total_events DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_profiles_by_severity(self, severity: str) -> List[Dict]:
        """Retrieve profiles by severity level"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM ip_profiles
            WHERE severity = ?
            ORDER BY total_events DESC
        """, (severity,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_profiles(self) -> List[Dict]:
        """Retrieve all IP profiles"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ip_profiles ORDER BY last_seen DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # BLACKLIST OPERATIONS
    # ========================
    
    def add_blacklist(self, ip: str, reason: str, duration_seconds: int, severity: str):
        """Add an IP to the blacklist"""
        now = time.time()
        expiration = now + duration_seconds
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO blacklist 
            (ip, reason, blacklist_time, expiration_time, duration_seconds, severity)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ip) DO UPDATE SET
                expiration_time = excluded.expiration_time,
                reason = excluded.reason
        """, (ip, reason, now, expiration, duration_seconds, severity))
        
        self.conn.commit()
    
    def get_blacklist(self) -> List[Dict]:
        """Retrieve currently active blacklist entries"""
        cursor = self.conn.cursor()
        now = time.time()
        
        cursor.execute("""
            SELECT * FROM blacklist
            WHERE expiration_time > ?
            ORDER BY expiration_time DESC
        """, (now,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def remove_expired_blacklist(self):
        """Remove expired blacklist entries"""
        cursor = self.conn.cursor()
        now = time.time()
        
        cursor.execute("DELETE FROM blacklist WHERE expiration_time <= ?", (now,))
        self.conn.commit()
    
    def is_blacklisted(self, ip: str) -> bool:
        """Check if an IP is currently blacklisted"""
        cursor = self.conn.cursor()
        now = time.time()
        
        cursor.execute("""
            SELECT 1 FROM blacklist
            WHERE ip = ? AND expiration_time > ?
            LIMIT 1
        """, (ip, now))
        
        return cursor.fetchone() is not None
    
    # ========================
    # STATISTICS & ANALYSIS
    # ========================
    
    def get_statistics(self, hours: Optional[int] = None) -> Dict:
        """Get honeypot statistics. If hours is None, use all-time data."""
        cursor = self.conn.cursor()
        now = time.time()
        start_time = None if hours is None else now - (hours * 3600)
        
        # Total events
        if start_time is None:
            cursor.execute("SELECT COUNT(*) as count FROM events")
        else:
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM events
                WHERE timestamp > ?
                """,
                (start_time,),
            )
        total_events = cursor.fetchone()["count"] or 0
        
        # Unique IPs
        if start_time is None:
            cursor.execute("SELECT COUNT(DISTINCT source_ip) as count FROM events")
        else:
            cursor.execute(
                """
                SELECT COUNT(DISTINCT source_ip) as count FROM events
                WHERE timestamp > ?
                """,
                (start_time,),
            )
        unique_ips = cursor.fetchone()["count"] or 0
        
        # Top protocol
        if start_time is None:
            cursor.execute(
                """
                SELECT protocol, COUNT(*) as count FROM events
                GROUP BY protocol
                ORDER BY count DESC
                LIMIT 1
                """
            )
        else:
            cursor.execute(
                """
                SELECT protocol, COUNT(*) as count FROM events
                WHERE timestamp > ?
                GROUP BY protocol
                ORDER BY count DESC
                LIMIT 1
                """,
                (start_time,),
            )
        result = cursor.fetchone()
        top_protocol = result['protocol'] if result else "N/A"
        
        # Top port
        if start_time is None:
            cursor.execute(
                """
                SELECT port, COUNT(*) as count FROM events
                GROUP BY port
                ORDER BY count DESC
                LIMIT 1
                """
            )
        else:
            cursor.execute(
                """
                SELECT port, COUNT(*) as count FROM events
                WHERE timestamp > ?
                GROUP BY port
                ORDER BY count DESC
                LIMIT 1
                """,
                (start_time,),
            )
        result = cursor.fetchone()
        top_port = result['port'] if result else 0
        
        # Average payload size
        if start_time is None:
            cursor.execute("SELECT AVG(payload_size) as avg FROM events")
        else:
            cursor.execute(
                """
                SELECT AVG(payload_size) as avg FROM events
                WHERE timestamp > ?
                """,
                (start_time,),
            )
        avg_payload = cursor.fetchone()["avg"] or 0
        
        return {
            "total_events": total_events,
            "unique_ips": unique_ips,
            "top_protocol": top_protocol,
            "top_port": top_port,
            "avg_payload_size": round(avg_payload, 2),
            "blacklisted_ips": len(self.get_blacklist()),
            "time_period_hours": hours,
        }
    
    def get_attack_timeline(self, hours: int = 24, bucket_minutes: int = 5) -> List[Dict]:
        """Get attack events grouped by time buckets"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        bucket_seconds = bucket_minutes * 60
        
        cursor.execute("""
            SELECT 
                CAST((timestamp - ?) / ? AS INTEGER) * ? + ? as bucket_time,
                COUNT(*) as event_count,
                COUNT(DISTINCT source_ip) as unique_ips,
                AVG(payload_size) as avg_payload
            FROM events
            WHERE timestamp > ?
            GROUP BY bucket_time
            ORDER BY bucket_time
        """, (start_time, bucket_seconds, bucket_seconds, start_time, start_time))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def generate_daily_summary(self, date: str):
        """Generate daily summary statistics"""
        cursor = self.conn.cursor()
        
        # Get date range
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        start_time = date_obj.timestamp()
        end_time = (date_obj + timedelta(days=1)).timestamp()
        
        # Calculate statistics
        cursor.execute("""
            SELECT COUNT(*) as count FROM events
            WHERE timestamp BETWEEN ? AND ?
        """, (start_time, end_time))
        total_events = cursor.fetchone()['count'] or 0
        
        cursor.execute("""
            SELECT COUNT(DISTINCT source_ip) as count FROM events
            WHERE timestamp BETWEEN ? AND ?
        """, (start_time, end_time))
        unique_ips = cursor.fetchone()['count'] or 0
        
        cursor.execute("""
            SELECT protocol FROM events
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY protocol
            ORDER BY COUNT(*) DESC
            LIMIT 1
        """, (start_time, end_time))
        result = cursor.fetchone()
        top_protocol = result['protocol'] if result else "N/A"
        
        # Insert summary
        cursor.execute("""
            INSERT OR REPLACE INTO attack_summaries
            (date, total_events, unique_ips, top_protocol)
            VALUES (?, ?, ?, ?)
        """, (date, total_events, unique_ips, top_protocol))
        
        self.conn.commit()
    
    # ========================
    # DATABASE MAINTENANCE
    # ========================
    
    def cleanup_old_events(self, days: int = 30):
        """Remove events older than N days"""
        cutoff_time = time.time() - (days * 86400)
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_time,))
        self.conn.commit()
        
        return cursor.rowcount

    def vacuum(self):
        """Run VACUUM to reclaim space"""
        cursor = self.conn.cursor()
        cursor.execute("VACUUM")
        self.conn.commit()
    
    def get_database_size(self) -> Dict:
        """Get database size and event count"""
        db_file = Path(self.db_path)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM events")
        event_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM ip_profiles")
        profile_count = cursor.fetchone()['count']
        
        size_mb = db_file.stat().st_size / (1024 * 1024) if db_file.exists() else 0
        
        return {
            "size_mb": round(size_mb, 2),
            "event_count": event_count,
            "profile_count": profile_count,
            "file_path": str(db_file.absolute()),
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
