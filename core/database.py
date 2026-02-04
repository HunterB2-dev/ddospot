"""
SQLite database persistence for the honeypot.
Stores attack events, IP profiles, and statistics for analysis.
"""

import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


class HoneypotDatabase:
    """SQLite database manager for persistent attack storage"""
    
    def __init__(self, db_path: str = "honeypot.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Ensure the directory exists
        db_path_obj = Path(db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Use check_same_thread=False but with proper timeout and WAL mode
        self.conn: sqlite3.Connection = sqlite3.connect(
            db_path, 
            check_same_thread=False, 
            timeout=30,
            isolation_level=None  # Autocommit mode to avoid locking
        )
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        self._lock = threading.RLock()  # Recursive lock for thread safety
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
        
        # Alert rules table - custom alert rules for attack detection
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                enabled BOOLEAN DEFAULT 1,
                condition_type TEXT NOT NULL,
                condition_field TEXT NOT NULL,
                condition_operator TEXT NOT NULL,
                condition_value TEXT NOT NULL,
                action TEXT NOT NULL,
                action_target TEXT,
                threshold INTEGER DEFAULT 1,
                time_window_minutes INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered REAL,
                trigger_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_name ON alert_rules(name)")
        
        # Threat Intelligence tables - stores IP reputation and threat data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whois_cache (
                ip TEXT PRIMARY KEY,
                hostname TEXT,
                asn TEXT,
                organization TEXT,
                country TEXT,
                lookup_time DATETIME,
                cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whois_country ON whois_cache(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whois_asn ON whois_cache(asn)")
        
        # IP Reputation scores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_reputation (
                ip TEXT PRIMARY KEY,
                reputation_score INTEGER DEFAULT 0,
                threat_level TEXT DEFAULT 'minimal',
                threat_indicators TEXT,
                botnet_detected BOOLEAN DEFAULT 0,
                botnet_family TEXT,
                feeds_matched INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reputation_score ON ip_reputation(reputation_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_level ON ip_reputation(threat_level)")
        
        # Threat feeds matches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                feed_name TEXT NOT NULL,
                threat_name TEXT,
                confidence REAL DEFAULT 1.0,
                matched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ip, feed_name)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_feeds_ip ON threat_feeds(ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_feeds_name ON threat_feeds(feed_name)")
        
        # Botnet clusters - group similar attack patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS botnet_clusters (
                cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_name TEXT NOT NULL UNIQUE,
                description TEXT,
                signature_type TEXT,
                member_count INTEGER DEFAULT 0,
                threat_level TEXT DEFAULT 'medium',
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Botnet members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS botnet_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id INTEGER NOT NULL,
                ip TEXT NOT NULL UNIQUE,
                confidence REAL DEFAULT 0.8,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cluster_id) REFERENCES botnet_clusters(cluster_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_botnet_members_cluster ON botnet_members(cluster_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_botnet_members_ip ON botnet_members(ip)")
        
        # Evasion Detection tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evasion_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ip TEXT NOT NULL,
                detection_type TEXT NOT NULL,
                evasion_score REAL NOT NULL,
                threat_level TEXT,
                details TEXT,
                timestamp REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(source_ip) REFERENCES ip_profiles(ip)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evasion_source_ip ON evasion_detections(source_ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evasion_timestamp ON evasion_detections(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evasion_type ON evasion_detections(detection_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evasion_score ON evasion_detections(evasion_score)")
        
        # Behavioral baselines - tracks normal behavior for anomaly detection
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavioral_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ip TEXT UNIQUE NOT NULL,
                protocol TEXT,
                avg_request_rate REAL,
                avg_payload_size REAL,
                common_patterns TEXT,
                observation_count INTEGER DEFAULT 0,
                last_updated REAL,
                FOREIGN KEY(source_ip) REFERENCES ip_profiles(ip)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_baseline_ip ON behavioral_baselines(source_ip)")
        
        # Polymorphic attack patterns - tracks known polymorphic variants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS polymorphic_signatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_pattern TEXT NOT NULL UNIQUE,
                pattern_description TEXT,
                variants TEXT,
                detection_hits INTEGER DEFAULT 0,
                severity TEXT,
                first_seen REAL NOT NULL,
                last_seen REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_polymorphic_pattern ON polymorphic_signatures(base_pattern)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_polymorphic_severity ON polymorphic_signatures(severity)")
        
        # IP Reputation Cache table - threat intelligence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_reputation_cache (
                ip TEXT PRIMARY KEY,
                reputation_score INTEGER,
                sources TEXT,
                confidence INTEGER,
                report_count INTEGER DEFAULT 0,
                threat_types TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reputation_score ON ip_reputation_cache(reputation_score)")
        
        # Geolocation Cache table - threat intelligence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geo_data_cache (
                ip TEXT PRIMARY KEY,
                country_code TEXT,
                country_name TEXT,
                city TEXT,
                isp TEXT,
                risk_score INTEGER,
                latitude REAL,
                longitude REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_country ON geo_data_cache(country_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_risk ON geo_data_cache(risk_score)")
        
        # Threat Feed Cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_feed_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                feed_source TEXT NOT NULL,
                matched INTEGER DEFAULT 0,
                match_details TEXT,
                confidence INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ip, feed_source)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feed_ip ON threat_feed_cache(ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feed_source ON threat_feed_cache(feed_source)")
        
        # Attack Trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attack_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                timestamp REAL NOT NULL,
                protocol TEXT,
                attack_count INTEGER,
                trend_score REAL,
                velocity REAL,
                consistency REAL,
                anomaly_score REAL,
                protocol_diversity REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ip) REFERENCES ip_profiles(ip)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trend_ip ON attack_trends(ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trend_timestamp ON attack_trends(timestamp)")
        
        # Threat Intelligence Scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_intelligence_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                reputation_score REAL,
                geo_risk_score REAL,
                feed_match_score REAL,
                trend_score REAL,
                composite_threat_score REAL,
                threat_level TEXT,
                recommendations TEXT,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ip) REFERENCES ip_profiles(ip)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ti_ip ON threat_intelligence_scores(ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ti_score ON threat_intelligence_scores(composite_threat_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ti_level ON threat_intelligence_scores(threat_level)")
        
        self.conn.commit()
        
        # Also ensure response/config tables are created
        self._ensure_response_tables()
    
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
        with self._lock:
            try:
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
                return int(row["count"] or 0) if row and row["count"] is not None else 0
            except sqlite3.InterfaceError:
                # Return 0 if there's a database lock
                return 0
    
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
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT * FROM ip_profiles
                    ORDER BY total_events DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.InterfaceError:
                # Return empty list if there's a database lock
                return []
    
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
        with self._lock:
            try:
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
                result = cursor.fetchone()
                total_events = result["count"] if result else 0
                
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
                result = cursor.fetchone()
                unique_ips = result["count"] if result else 0
                
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
                result = cursor.fetchone()
                avg_payload = result["avg"] if result and result["avg"] else 0
                
                return {
                    "total_events": total_events,
                    "unique_ips": unique_ips,
                    "top_protocol": top_protocol,
                    "top_port": top_port,
                    "avg_payload_size": round(avg_payload, 2),
                    "blacklisted_ips": len(self.get_blacklist()),
                    "time_period_hours": hours,
                }
            except sqlite3.InterfaceError:
                # Return default stats if there's a database lock
                return {
                    "total_events": 0,
                    "unique_ips": 0,
                    "top_protocol": "N/A",
                    "top_port": 0,
                    "avg_payload_size": 0,
                    "blacklisted_ips": 0,
                    "time_period_hours": hours,
                }
    
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
    
    # ========================
    # ALERT RULES OPERATIONS
    # ========================
    
    def create_alert_rule(self, name: str, description: str, condition_type: str,
                         condition_field: str, condition_operator: str, condition_value: str,
                         action: str, action_target: Optional[str] = None,
                         threshold: int = 1, time_window_minutes: int = 1) -> int:
        """Create a new alert rule"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO alert_rules 
            (name, description, condition_type, condition_field, condition_operator, 
             condition_value, action, action_target, threshold, time_window_minutes, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (name, description, condition_type, condition_field, condition_operator,
              condition_value, action, action_target, threshold, time_window_minutes))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_alert_rules(self, enabled_only: bool = False) -> List[Dict]:
        """Get all alert rules"""
        cursor = self.conn.cursor()
        if enabled_only:
            cursor.execute("SELECT * FROM alert_rules WHERE enabled = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM alert_rules ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_alert_rule(self, rule_id: int) -> Optional[Dict]:
        """Get specific alert rule"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_alert_rule(self, rule_id: int, **kwargs) -> bool:
        """Update alert rule"""
        allowed_fields = {'name', 'description', 'enabled', 'condition_type', 'condition_field',
                         'condition_operator', 'condition_value', 'action', 'action_target',
                         'threshold', 'time_window_minutes'}
        
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not update_fields:
            return False
        
        update_fields['updated_at'] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [rule_id]
        
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE alert_rules SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_alert_rule(self, rule_id: int) -> bool:
        """Delete alert rule"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def record_alert_trigger(self, rule_id: int) -> None:
        """Record that an alert rule was triggered"""
        cursor = self.conn.cursor()
        current_time = time.time()
        cursor.execute("""
            UPDATE alert_rules 
            SET last_triggered = ?, trigger_count = trigger_count + 1
            WHERE id = ?
        """, (current_time, rule_id))
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
    
    # ========================
    # ATTACK PATTERN ANALYSIS
    # ========================
    
    def get_attack_patterns(self, hours: int = 24) -> Dict:
        """Get overall attack patterns for the specified time period"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        # Overall stats
        cursor.execute("""
            SELECT COUNT(*) as total_events, COUNT(DISTINCT source_ip) as unique_ips
            FROM events WHERE timestamp > ?
        """, (start_time,))
        stats = dict(cursor.fetchone())
        
        # Protocol distribution
        cursor.execute("""
            SELECT protocol, COUNT(*) as count
            FROM events WHERE timestamp > ?
            GROUP BY protocol ORDER BY count DESC
        """, (start_time,))
        protocols = {row['protocol']: row['count'] for row in cursor.fetchall()}
        
        # Port distribution (top 10)
        cursor.execute("""
            SELECT port, COUNT(*) as count
            FROM events WHERE timestamp > ?
            GROUP BY port ORDER BY count DESC LIMIT 10
        """, (start_time,))
        top_ports = [(row['port'], row['count']) for row in cursor.fetchall()]
        
        # Average payload size
        cursor.execute("""
            SELECT AVG(payload_size) as avg_size, MAX(payload_size) as max_size,
                   MIN(payload_size) as min_size
            FROM events WHERE timestamp > ?
        """, (start_time,))
        payload_stats = dict(cursor.fetchone())
        
        return {
            'total_events': stats['total_events'],
            'unique_ips': stats['unique_ips'],
            'protocols': protocols,
            'top_ports': top_ports,
            'payload_avg': round(payload_stats['avg_size'], 2) if payload_stats['avg_size'] else 0,
            'payload_max': payload_stats['max_size'],
            'payload_min': payload_stats['min_size'],
        }
    
    def get_hourly_patterns(self, hours: int = 24) -> List[Dict]:
        """Get attack frequency by hour"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                datetime(timestamp, 'unixepoch') as hour,
                COUNT(*) as event_count,
                COUNT(DISTINCT source_ip) as unique_ips
            FROM events
            WHERE timestamp > ?
            GROUP BY datetime(timestamp, 'unixepoch', 'start of hour')
            ORDER BY hour ASC
        """, (start_time,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_patterns(self, days: int = 7) -> List[Dict]:
        """Get attack frequency by day"""
        cursor = self.conn.cursor()
        start_time = time.time() - (days * 86400)
        
        cursor.execute("""
            SELECT 
                date(timestamp, 'unixepoch') as day,
                COUNT(*) as event_count,
                COUNT(DISTINCT source_ip) as unique_ips,
                AVG(payload_size) as avg_payload
            FROM events
            WHERE timestamp > ?
            GROUP BY date(timestamp, 'unixepoch')
            ORDER BY day ASC
        """, (start_time,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_attacking_ips(self, limit: int = 20, hours: int = 24) -> List[Dict]:
        """Get top attacking IPs with statistics"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                source_ip,
                COUNT(*) as attack_count,
                COUNT(DISTINCT protocol) as protocols_used,
                COUNT(DISTINCT port) as ports_hit,
                AVG(payload_size) as avg_payload,
                MIN(timestamp) as first_attack,
                MAX(timestamp) as last_attack
            FROM events
            WHERE timestamp > ?
            GROUP BY source_ip
            ORDER BY attack_count DESC
            LIMIT ?
        """, (start_time, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_protocol_distribution(self, hours: int = 24) -> List[Dict]:
        """Get protocol usage statistics"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                protocol,
                COUNT(*) as event_count,
                COUNT(DISTINCT source_ip) as unique_ips,
                AVG(payload_size) as avg_payload,
                COUNT(DISTINCT port) as ports_used
            FROM events
            WHERE timestamp > ?
            GROUP BY protocol
            ORDER BY event_count DESC
        """, (start_time,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_attack_timeline(self, hours: int = 24, bucket_size: int = 60) -> List[Dict]:
        """Get attack frequency over time with custom bucket size (in minutes)"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        bucket_seconds = bucket_size * 60
        
        cursor.execute(f"""
            SELECT 
                CAST((timestamp - ?) / ? AS INTEGER) * ? + ? as bucket_time,
                COUNT(*) as event_count,
                COUNT(DISTINCT source_ip) as unique_ips,
                AVG(payload_size) as avg_payload
            FROM events
            WHERE timestamp > ?
            GROUP BY CAST((timestamp - ?) / ? AS INTEGER)
            ORDER BY bucket_time ASC
        """, (start_time, bucket_seconds, bucket_seconds, start_time, start_time, start_time, bucket_seconds))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_port_distribution(self, hours: int = 24, limit: int = 15) -> List[Dict]:
        """Get port attack distribution"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                port,
                COUNT(*) as attack_count,
                COUNT(DISTINCT protocol) as protocols,
                COUNT(DISTINCT source_ip) as unique_ips
            FROM events
            WHERE timestamp > ?
            GROUP BY port
            ORDER BY attack_count DESC
            LIMIT ?
        """, (start_time, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_event_type_distribution(self, hours: int = 24) -> List[Dict]:
        """Get distribution of event types"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                event_type,
                COUNT(*) as count,
                COUNT(DISTINCT source_ip) as unique_ips
            FROM events
            WHERE timestamp > ?
            GROUP BY event_type
            ORDER BY count DESC
        """, (start_time,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_events_paginated(self, limit: int = 50, offset: int = 0, 
                         source_ip: Optional[str] = None, 
                         protocol: Optional[str] = None,
                         port: Optional[int] = None,
                         last_timestamp: Optional[float] = None) -> Tuple[List[Dict], int]:
        """Get recent events with optional filtering for real-time log viewer.
        
        Args:
            limit: Max events to return
            offset: Pagination offset
            source_ip: Filter by source IP
            protocol: Filter by protocol
            port: Filter by port
            last_timestamp: Only return events after this timestamp (for real-time)
            
        Returns:
            Tuple of (events list, total count)
        """
        cursor = self.conn.cursor()
        
        # Clamp limit for performance
        limit = min(limit, 500)
        
        # Build query dynamically
        query = "SELECT id, timestamp, source_ip, port, protocol, payload_size, event_type FROM events"
        params = []
        conditions = []
        
        if last_timestamp is not None:
            conditions.append("timestamp > ?")
            params.append(last_timestamp)
        
        if source_ip:
            conditions.append("source_ip = ?")
            params.append(source_ip)
        
        if protocol:
            conditions.append("protocol = ?")
            params.append(protocol)
        
        if port:
            conditions.append("port = ?")
            params.append(port)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM events{' WHERE ' + ' AND '.join(conditions) if conditions else ''}", params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        events = [dict(row) for row in cursor.fetchall()]
        
        # Convert timestamps to ISO format strings
        for event in events:
            event['timestamp_iso'] = datetime.fromtimestamp(event['timestamp']).isoformat()
        
        return events, total
    
    def get_live_event_stream(self, since_timestamp: Optional[float] = None,
                             limit: int = 20) -> List[Dict]:
        """Get events for live stream (last N events or since timestamp)"""
        cursor = self.conn.cursor()
        
        if since_timestamp is not None:
            cursor.execute("""
                SELECT id, timestamp, source_ip, port, protocol, payload_size, event_type
                FROM events
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (since_timestamp, limit))
        else:
            cursor.execute("""
                SELECT id, timestamp, source_ip, port, protocol, payload_size, event_type
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        events = [dict(row) for row in cursor.fetchall()]
        for event in events:
            event['timestamp_iso'] = datetime.fromtimestamp(event['timestamp']).isoformat()
        
        return list(reversed(events))  # Return in chronological order
    
    def get_anomaly_baseline(self, hours: int = 24) -> Dict:
        """Calculate baseline statistics for anomaly detection"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT source_ip) as unique_ips,
                AVG(payload_size) as avg_payload,
                MAX(payload_size) as max_payload,
                MIN(payload_size) as min_payload
            FROM events
            WHERE timestamp > ?
        """, (start_time,))
        
        row = cursor.fetchone()
        if row:
            # Calculate standard deviation manually if we have data
            cursor.execute("""
                SELECT payload_size FROM events WHERE timestamp > ?
            """, (start_time,))
            payloads = [r[0] for r in cursor.fetchall()]
            
            avg = row[2] or 0
            if payloads and len(payloads) > 1:
                variance = sum((x - avg) ** 2 for x in payloads) / len(payloads)
                stddev = variance ** 0.5
            else:
                stddev = 1
            
            return {
                'total_events': row[0] or 0,
                'unique_ips': row[1] or 0,
                'avg_payload': avg,
                'max_payload': row[3] or 0,
                'min_payload': row[4] or 0,
                'stddev_payload': stddev,
                'period_hours': hours
            }
        
        return {
            'total_events': 0,
            'unique_ips': 0,
            'avg_payload': 0,
            'max_payload': 0,
            'min_payload': 0,
            'stddev_payload': 1,
            'period_hours': hours
        }
    
    def detect_anomalies(self, hours: int = 24, sensitivity: float = 2.0) -> List[Dict]:
        """Detect anomalous events based on statistical deviations"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        # Get baseline statistics
        baseline = self.get_anomaly_baseline(hours=hours)
        
        if baseline['total_events'] == 0:
            return []
        
        avg_payload = baseline['avg_payload']
        stddev_payload = baseline['stddev_payload']
        avg_events_per_hour = baseline['total_events'] / hours if hours > 0 else 0
        
        # Detect anomalies
        anomalies = []
        
        # Anomaly 1: Unusually large payloads (payload > avg + sensitivity*stdev)
        threshold_payload = avg_payload + (sensitivity * stddev_payload)
        
        cursor.execute("""
            SELECT id, timestamp, source_ip, port, protocol, payload_size, event_type
            FROM events
            WHERE timestamp > ? AND payload_size > ?
            ORDER BY payload_size DESC
            LIMIT 50
        """, (start_time, threshold_payload))
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            anomaly_score = (row_dict['payload_size'] - avg_payload) / max(stddev_payload, 1)
            row_dict['anomaly_type'] = 'unusual_payload'
            row_dict['anomaly_score'] = min(anomaly_score, 10.0)  # Cap at 10
            row_dict['timestamp_iso'] = datetime.fromtimestamp(row_dict['timestamp']).isoformat()
            anomalies.append(row_dict)
        
        # Anomaly 2: IPs with unusual activity rates (high attack frequency)
        cursor.execute("""
            SELECT 
                source_ip,
                COUNT(*) as event_count,
                MIN(timestamp) as first_timestamp,
                MAX(timestamp) as last_timestamp
            FROM events
            WHERE timestamp > ?
            GROUP BY source_ip
            ORDER BY event_count DESC
            LIMIT 100
        """, (start_time,))
        
        avg_per_ip = baseline['total_events'] / max(baseline['unique_ips'], 1)
        
        for row in cursor.fetchall():
            event_count = row[1]
            if event_count > avg_per_ip * 2:  # 2x average per IP
                anomaly_score = min((event_count / avg_per_ip) * 2, 10.0)
                duration = row[3] - row[2]
                rate = event_count / (duration / 60) if duration > 0 else 0
                
                anomalies.append({
                    'source_ip': row[0],
                    'event_count': event_count,
                    'duration_seconds': duration,
                    'events_per_minute': rate,
                    'anomaly_type': 'high_frequency_attack',
                    'anomaly_score': min(anomaly_score, 10.0)
                })
        
        return sorted(anomalies, key=lambda x: x.get('anomaly_score', 0), reverse=True)
    
    def get_ip_behavior_profile(self, source_ip: str, hours: int = 24) -> Dict:
        """Get behavioral profile for a specific IP address"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as event_count,
                COUNT(DISTINCT protocol) as protocol_count,
                COUNT(DISTINCT port) as port_count,
                AVG(payload_size) as avg_payload,
                MAX(payload_size) as max_payload,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM events
            WHERE source_ip = ? AND timestamp > ?
        """, (source_ip, start_time))
        
        row = cursor.fetchone()
        if not row or row[0] == 0:
            return None
        
        first_seen = row[5]
        last_seen = row[6]
        duration = last_seen - first_seen
        
        # Get protocol distribution
        cursor.execute("""
            SELECT protocol, COUNT(*) as count
            FROM events
            WHERE source_ip = ? AND timestamp > ?
            GROUP BY protocol
            ORDER BY count DESC
        """, (source_ip, start_time))
        
        protocols = [{
            'protocol': p[0],
            'count': p[1]
        } for p in cursor.fetchall()]
        
        return {
            'source_ip': source_ip,
            'event_count': row[0],
            'protocol_count': row[1],
            'port_count': row[2],
            'avg_payload': row[3],
            'max_payload': row[4],
            'first_seen': first_seen,
            'last_seen': last_seen,
            'duration_seconds': duration,
            'events_per_minute': (row[0] / (duration / 60)) if duration > 0 else 0,
            'protocols': protocols
        }
    
    def get_geographic_distribution(self, hours: int = 24) -> List[Dict]:
        """Get attack distribution by geographic location (country/region)"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        # This requires geolocation data to be joined with events
        # For now, return attack stats grouped by unique IPs
        # The geolocation enrichment happens in the API layer
        cursor.execute("""
            SELECT 
                source_ip,
                COUNT(*) as event_count,
                AVG(payload_size) as avg_payload,
                COUNT(DISTINCT protocol) as protocol_count
            FROM events
            WHERE timestamp > ?
            GROUP BY source_ip
            ORDER BY event_count DESC
            LIMIT 200
        """, (start_time,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_hotspot_locations(self, limit: int = 50, hours: int = 24) -> List[Dict]:
        """Get geographic hotspots of attack activity"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                source_ip,
                COUNT(*) as event_count,
                SUM(payload_size) as total_payload,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM events
            WHERE timestamp > ?
            GROUP BY source_ip
            ORDER BY event_count DESC
            LIMIT ?
        """, (start_time, limit))
        
        locations = []
        for row in cursor.fetchall():
            locations.append({
                'source_ip': row[0],
                'event_count': row[1],
                'total_payload': row[2],
                'first_event': row[3],
                'last_event': row[4],
                'severity': 'critical' if row[1] > 100 else 'high' if row[1] > 50 else 'medium' if row[1] > 20 else 'low'
            })
        
        return locations
    
    def get_country_stats(self, hours: int = 24) -> List[Dict]:
        """Get aggregate statistics per country (requires geolocation enrichment)"""
        cursor = self.conn.cursor()
        start_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT 
                source_ip,
                COUNT(*) as event_count
            FROM events
            WHERE timestamp > ?
            GROUP BY source_ip
        """, (start_time,))
        
        # Group by source IP for now
        # Geolocation enrichment happens in API layer
        ip_stats = [dict(row) for row in cursor.fetchall()]
        return ip_stats
    
    def add_threat_intelligence(self, source_ip: str, threat_data: Dict) -> bool:
        """Store threat intelligence data for an IP"""
        cursor = self.conn.cursor()
        
        try:
            # Create threat_intelligence table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_intelligence (
                    source_ip TEXT PRIMARY KEY,
                    risk_score REAL,
                    threat_type TEXT,
                    is_vpn BOOLEAN,
                    is_proxy BOOLEAN,
                    is_datacenter BOOLEAN,
                    threat_description TEXT,
                    last_updated TIMESTAMP,
                    source TEXT
                )
            """)
            
            cursor.execute("""
                INSERT OR REPLACE INTO threat_intelligence 
                (source_ip, risk_score, threat_type, is_vpn, is_proxy, is_datacenter, threat_description, last_updated, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """, (
                source_ip,
                threat_data.get('risk_score', 0),
                threat_data.get('threat_type', 'unknown'),
                threat_data.get('is_vpn', False),
                threat_data.get('is_proxy', False),
                threat_data.get('is_datacenter', False),
                threat_data.get('description', ''),
                threat_data.get('source', 'local')
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding threat intelligence: {e}")
            return False
    
    def get_threat_intelligence(self, source_ip: str) -> Optional[Dict]:
        """Get threat intelligence data for an IP"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM threat_intelligence WHERE source_ip = ?
            """, (source_ip,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'source_ip': row[0],
                    'risk_score': row[1],
                    'threat_type': row[2],
                    'is_vpn': row[3],
                    'is_proxy': row[4],
                    'is_datacenter': row[5],
                    'threat_description': row[6],
                    'last_updated': row[7],
                    'source': row[8]
                }
        except:
            pass
        
        return None
    
    def get_high_risk_ips(self, threshold: float = 7.0, limit: int = 50) -> List[Dict]:
        """Get IPs with high risk scores"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    source_ip,
                    risk_score,
                    threat_type,
                    threat_description,
                    last_updated
                FROM threat_intelligence
                WHERE risk_score >= ?
                ORDER BY risk_score DESC
                LIMIT ?
            """, (threshold, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    # ========== AUTOMATED RESPONSE ACTIONS ==========
    
    def _ensure_response_tables(self):
        """Create response management tables"""
        cursor = self.conn.cursor()
        
        # Blocked IPs table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    ip TEXT PRIMARY KEY,
                    reason TEXT,
                    threat_type TEXT,
                    risk_score REAL,
                    blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    is_permanent BOOLEAN DEFAULT 1,
                    blocked_by TEXT DEFAULT 'automated'
                )
            """)
        except:
            pass
        
        # Webhooks table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_triggered DATETIME,
                    trigger_count INTEGER DEFAULT 0
                )
            """)
        except:
            pass
        
        # Automated actions log
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automated_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    source_ip TEXT,
                    action_details TEXT,
                    triggered_by TEXT,
                    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success'
                )
            """)
        except:
            pass
        
        # Configuration storage (Feature #11)
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    type TEXT DEFAULT 'string',
                    description TEXT,
                    category TEXT DEFAULT 'system',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except:
            pass
        
        self.conn.commit()
    
    def block_ip(self, source_ip: str, reason: str = '', threat_type: str = '', risk_score: float = 0.0, 
                 permanent: bool = True, expires_in_hours: int = 24) -> bool:
        """Block an IP address"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            expires_at = None
            if not permanent:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            cursor.execute("""
                INSERT OR REPLACE INTO blocked_ips 
                (ip, reason, threat_type, risk_score, is_permanent, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_ip, reason, threat_type, risk_score, permanent, expires_at))
            
            # Log action
            cursor.execute("""
                INSERT INTO automated_actions 
                (action_type, source_ip, action_details, triggered_by)
                VALUES ('block_ip', ?, ?, 'automated_response')
            """, (source_ip, f'Blocked: {reason}'))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error blocking IP {source_ip}: {e}")
            return False
    
    def unblock_ip(self, source_ip: str) -> bool:
        """Unblock an IP address"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("DELETE FROM blocked_ips WHERE ip = ?", (source_ip,))
            
            cursor.execute("""
                INSERT INTO automated_actions 
                (action_type, source_ip, triggered_by)
                VALUES ('unblock_ip', ?, 'manual')
            """, (source_ip,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error unblocking IP {source_ip}: {e}")
            return False
    
    def is_ip_blocked(self, source_ip: str) -> bool:
        """Check if IP is blocked"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ip FROM blocked_ips 
                WHERE ip = ? AND (is_permanent = 1 OR expires_at > CURRENT_TIMESTAMP)
            """, (source_ip,))
            
            return cursor.fetchone() is not None
        except:
            return False
    
    def get_blocked_ips(self, limit: int = 100) -> List[Dict]:
        """Get list of blocked IPs"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    ip,
                    reason,
                    threat_type,
                    risk_score,
                    blocked_at,
                    expires_at,
                    is_permanent
                FROM blocked_ips
                WHERE is_permanent = 1 OR expires_at > CURRENT_TIMESTAMP
                ORDER BY blocked_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def add_webhook(self, url: str, event_type: str = 'all_threats') -> bool:
        """Add a webhook for automated notifications"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO webhooks (url, event_type, is_active)
                VALUES (?, ?, 1)
            """, (url, event_type))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding webhook: {e}")
            return False
    
    def get_webhooks(self, active_only: bool = True) -> List[Dict]:
        """Get configured webhooks"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            if active_only:
                cursor.execute("SELECT * FROM webhooks WHERE is_active = 1")
            else:
                cursor.execute("SELECT * FROM webhooks")
            
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def log_action(self, action_type: str, source_ip: str = '', details: str = '', status: str = 'success') -> bool:
        """Log an automated action"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO automated_actions 
                (action_type, source_ip, action_details, triggered_by, status)
                VALUES (?, ?, ?, 'automated_response', ?)
            """, (action_type, source_ip, details, status))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging action: {e}")
            return False
    
    def get_action_log(self, limit: int = 100, action_type: str = '') -> List[Dict]:
        """Get automated action logs"""
        self._ensure_response_tables()
        cursor = self.conn.cursor()
        
        try:
            if action_type:
                cursor.execute("""
                    SELECT * FROM automated_actions 
                    WHERE action_type = ?
                    ORDER BY executed_at DESC
                    LIMIT ?
                """, (action_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM automated_actions 
                    ORDER BY executed_at DESC
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    # ============= Configuration Management (Feature #11) =============
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        except:
            return None
    
    def set_config(self, key: str, value: str, config_type: str = 'string', 
                   description: str = '', category: str = 'system') -> bool:
        """Set a configuration value"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO config 
                (key, value, type, description, category, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, str(value), config_type, description, category))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error setting config {key}: {e}")
            return False
    
    def get_all_config(self, category: str = None) -> Dict[str, Any]:
        """Get all configuration values, optionally filtered by category"""
        cursor = self.conn.cursor()
        try:
            if category:
                cursor.execute(
                    "SELECT key, value, type FROM config WHERE category = ? ORDER BY key",
                    (category,)
                )
            else:
                cursor.execute("SELECT key, value, type FROM config ORDER BY key")
            
            result = {}
            for row in cursor.fetchall():
                key, value, config_type = row
                # Type conversion
                if config_type == 'int':
                    result[key] = int(value) if value else 0
                elif config_type == 'float':
                    result[key] = float(value) if value else 0.0
                elif config_type == 'bool':
                    result[key] = value.lower() in ('true', '1', 'yes')
                elif config_type == 'json':
                    import json
                    result[key] = json.loads(value) if value else {}
                else:
                    result[key] = value
            return result
        except Exception as e:
            print(f"Error getting all config: {e}")
            return {}
    
    def delete_config(self, key: str) -> bool:
        """Delete a configuration value"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM config WHERE key = ?", (key,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting config {key}: {e}")
            return False
    
    def get_config_history(self, key: str, limit: int = 50) -> List[Dict]:
        """Get configuration change history (track changes via audit)"""
        # This would require an audit table - for now return current value
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT key, value, type, updated_at FROM config WHERE key = ? ORDER BY updated_at DESC LIMIT ?",
                (key, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def init_default_config(self):
        """Initialize default configuration values"""
        defaults = {
            # Honeypot services
            'honeypot_ssh_enabled': ('true', 'bool', 'SSH service enabled'),
            'honeypot_ssh_port': ('2222', 'int', 'SSH service port'),
            'honeypot_http_enabled': ('true', 'bool', 'HTTP service enabled'),
            'honeypot_http_port': ('8080', 'int', 'HTTP service port'),
            'honeypot_ssdp_enabled': ('true', 'bool', 'SSDP service enabled'),
            'honeypot_ssdp_port': ('1900', 'int', 'SSDP service port'),
            'honeypot_log_level': ('INFO', 'string', 'Logging level'),
            
            # Alert configuration
            'alert_event_threshold': ('10', 'int', 'Events per minute threshold'),
            'alert_unique_ip_threshold': ('5', 'int', 'Unique IPs per hour threshold'),
            'alert_enable_email': ('false', 'bool', 'Enable email alerts'),
            'alert_enable_webhook': ('false', 'bool', 'Enable webhook alerts'),
            'alert_enable_slack': ('false', 'bool', 'Enable Slack alerts'),
            
            # Response configuration
            'response_auto_block_threshold': ('7.0', 'float', 'Threat score to auto-block'),
            'response_block_duration': ('24', 'int', 'Block duration in hours'),
            'response_enable_webhooks': ('true', 'bool', 'Enable webhook notifications'),
            
            # UI preferences
            'ui_theme': ('light', 'string', 'UI theme (light/dark)'),
            'ui_data_retention_days': ('90', 'int', 'Data retention in days'),
            'ui_refresh_interval': ('5', 'int', 'Dashboard refresh interval in seconds'),
            
            # System settings
            'system_backup_enabled': ('true', 'bool', 'Automatic backups enabled'),
            'system_backup_schedule': ('0 2 * * *', 'string', 'Backup cron schedule'),
        }
        
        for key, (value, config_type, description) in defaults.items():
            # Only set if not already exists
            if not self.get_config(key):
                category = key.split('_')[0]  # honeypot, alert, response, ui, system
                self.set_config(key, value, config_type, description, category)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    # ========================
    # THREAT INTELLIGENCE OPERATIONS
    # ========================
    
    def add_whois_cache(self, ip: str, hostname: str, asn: str, 
                       organization: str, country: str) -> bool:
        """Cache WHOIS lookup result"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO whois_cache 
                (ip, hostname, asn, organization, country, lookup_time)
                VALUES (?, ?, ?, ?, ?, DATETIME('now'))
            """, (ip, hostname, asn, organization, country))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error caching WHOIS for {ip}: {e}")
            return False
    
    def get_whois_cache(self, ip: str) -> Optional[Dict]:
        """Get cached WHOIS data"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM whois_cache WHERE ip = ?", (ip,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except:
            return None
    
    def store_reputation(self, ip: str, score: int, threat_level: str, 
                        threat_indicators: List[Dict] = None, 
                        botnet_detected: bool = False, 
                        botnet_family: str = None) -> bool:
        """Store/update IP reputation score"""
        import json
        cursor = self.conn.cursor()
        try:
            indicators_json = json.dumps(threat_indicators or [])
            cursor.execute("""
                INSERT OR REPLACE INTO ip_reputation
                (ip, reputation_score, threat_level, threat_indicators, botnet_detected, botnet_family)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ip, score, threat_level, indicators_json, botnet_detected, botnet_family))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing reputation for {ip}: {e}")
            return False
    
    def get_reputation(self, ip: str) -> Optional[Dict]:
        """Get IP reputation data"""
        import json
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM ip_reputation WHERE ip = ?", (ip,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                try:
                    data['threat_indicators'] = json.loads(data['threat_indicators'] or '[]')
                except:
                    data['threat_indicators'] = []
                return data
            return None
        except:
            return None
    
    def add_threat_feed_match(self, ip: str, feed_name: str, 
                             threat_name: str = None, confidence: float = 1.0) -> bool:
        """Record a threat feed match"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO threat_feeds
                (ip, feed_name, threat_name, confidence)
                VALUES (?, ?, ?, ?)
            """, (ip, feed_name, threat_name, confidence))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding threat feed match for {ip}: {e}")
            return False
    
    def get_threat_feeds(self, ip: str) -> List[Dict]:
        """Get all threat feed matches for an IP"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT feed_name, threat_name, confidence, matched_at FROM threat_feeds WHERE ip = ?",
                (ip,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def create_botnet_cluster(self, family_name: str, description: str = None, 
                             threat_level: str = 'medium') -> Optional[int]:
        """Create a new botnet cluster"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO botnet_clusters (family_name, description, threat_level)
                VALUES (?, ?, ?)
            """, (family_name, description, threat_level))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating botnet cluster: {e}")
            return None
    
    def add_botnet_member(self, cluster_id: int, ip: str, confidence: float = 0.8) -> bool:
        """Add IP to botnet cluster"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO botnet_members
                (cluster_id, ip, confidence)
                VALUES (?, ?, ?)
            """, (cluster_id, ip, confidence))
            
            # Update member count
            cursor.execute(
                "UPDATE botnet_clusters SET member_count = (SELECT COUNT(*) FROM botnet_members WHERE cluster_id = ?) WHERE cluster_id = ?",
                (cluster_id, cluster_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding botnet member: {e}")
            return False
    
    def get_botnet_cluster(self, cluster_id: int) -> Optional[Dict]:
        """Get botnet cluster details"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM botnet_clusters WHERE cluster_id = ?", (cluster_id,))
            cluster = cursor.fetchone()
            if cluster:
                cluster_dict = dict(cluster)
                cursor.execute(
                    "SELECT ip, confidence FROM botnet_members WHERE cluster_id = ?",
                    (cluster_id,)
                )
                cluster_dict['members'] = [dict(row) for row in cursor.fetchall()]
                return cluster_dict
            return None
        except:
            return None
    
    def find_botnet_cluster_by_family(self, family_name: str) -> Optional[Dict]:
        """Find botnet cluster by family name"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT cluster_id FROM botnet_clusters WHERE family_name = ?", (family_name,))
            row = cursor.fetchone()
            if row:
                return self.get_botnet_cluster(row[0])
            return None
        except:
            return None
    
    def is_ip_in_botnet(self, ip: str) -> Optional[Dict]:
        """Check if IP is in any botnet cluster"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT c.cluster_id, c.family_name, c.threat_level, m.confidence
                FROM botnet_members m
                JOIN botnet_clusters c ON m.cluster_id = c.cluster_id
                WHERE m.ip = ?
            """, (ip,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except:
            return None
    
    def get_high_reputation_ips(self, threshold: int = 70, limit: int = 100) -> List[Dict]:
        """Get IPs with high reputation scores"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT ip, reputation_score, threat_level FROM ip_reputation
                WHERE reputation_score >= ?
                ORDER BY reputation_score DESC
                LIMIT ?
            """, (threshold, limit))
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []    
    # ========================
    # EVASION DETECTION
    # ========================
    
    def add_evasion_detection(self, source_ip: str, detection_type: str, 
                             evasion_score: float, threat_level: str,
                             details: Dict, timestamp: Optional[float] = None) -> int:
        """Store an evasion detection result"""
        if timestamp is None:
            timestamp = time.time()
        
        import json
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO evasion_detections
                (source_ip, detection_type, evasion_score, threat_level, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_ip, detection_type, evasion_score, threat_level, json.dumps(details), timestamp))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding evasion detection: {e}")
            return -1
    
    def get_evasion_detections(self, source_ip: str, limit: int = 100) -> List[Dict]:
        """Get evasion detections for an IP"""
        import json
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT id, source_ip, detection_type, evasion_score, threat_level, details, timestamp
                FROM evasion_detections
                WHERE source_ip = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (source_ip, limit))
            
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                r['details'] = json.loads(r['details']) if r['details'] else {}
                results.append(r)
            return results
        except Exception as e:
            print(f"Error getting evasion detections: {e}")
            return []
    
    def get_evasion_statistics(self, source_ip: str) -> Dict:
        """Get statistics of evasion detections for an IP"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(evasion_score) as avg_score,
                    MAX(evasion_score) as max_score,
                    COUNT(DISTINCT detection_type) as detection_types,
                    GROUP_CONCAT(DISTINCT threat_level) as threat_levels
                FROM evasion_detections
                WHERE source_ip = ?
            """, (source_ip,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "total_detections": row[0],
                    "avg_evasion_score": round(row[1], 3) if row[1] else 0,
                    "max_evasion_score": round(row[2], 3) if row[2] else 0,
                    "detection_types": row[3],
                    "threat_levels": row[4]
                }
            return {"total_detections": 0}
        except Exception as e:
            print(f"Error getting evasion statistics: {e}")
            return {"total_detections": 0}
    
    # ===================================
    # THREAT INTELLIGENCE OPERATIONS
    # ===================================
    
    def cache_ip_reputation(self, ip: str, reputation_score: int, sources: List[str], 
                          confidence: int, report_count: int, threat_types: List[str]) -> None:
        """Cache IP reputation data"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO ip_reputation_cache 
                    (ip, reputation_score, sources, confidence, report_count, threat_types, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (ip, reputation_score, ','.join(sources), confidence, report_count, ','.join(threat_types)))
                self.conn.commit()
            except Exception as e:
                print(f"Error caching IP reputation: {e}")
    
    def get_ip_reputation(self, ip: str) -> Dict:
        """Get cached IP reputation"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT reputation_score, sources, confidence, report_count, threat_types 
                    FROM ip_reputation_cache WHERE ip = ?
                """, (ip,))
                row = cursor.fetchone()
                if row:
                    return {
                        'score': row[0],
                        'sources': row[1].split(',') if row[1] else [],
                        'confidence': row[2],
                        'reports': row[3],
                        'threat_types': row[4].split(',') if row[4] else []
                    }
                return None
            except Exception as e:
                print(f"Error getting IP reputation: {e}")
                return None
    
    def cache_geolocation(self, ip: str, country_code: str, country_name: str, city: str, 
                         isp: str, risk_score: int, lat: float, lon: float) -> None:
        """Cache geolocation data"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO geo_data_cache
                    (ip, country_code, country_name, city, isp, risk_score, latitude, longitude, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (ip, country_code, country_name, city, isp, risk_score, lat, lon))
                self.conn.commit()
            except Exception as e:
                print(f"Error caching geolocation: {e}")
    
    def get_geolocation(self, ip: str) -> Dict:
        """Get cached geolocation"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT country_code, country_name, city, isp, risk_score, latitude, longitude
                    FROM geo_data_cache WHERE ip = ?
                """, (ip,))
                row = cursor.fetchone()
                if row:
                    return {
                        'country': row[0],
                        'country_name': row[1],
                        'city': row[2],
                        'isp': row[3],
                        'risk_score': row[4],
                        'lat': row[5],
                        'lon': row[6]
                    }
                return None
            except Exception as e:
                print(f"Error getting geolocation: {e}")
                return None
    
    def cache_threat_feed(self, ip: str, feed_source: str, matched: bool, 
                         match_details: str, confidence: int) -> None:
        """Cache threat feed match"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO threat_feed_cache
                    (ip, feed_source, matched, match_details, confidence, last_updated)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (ip, feed_source, 1 if matched else 0, match_details, confidence))
                self.conn.commit()
            except Exception as e:
                print(f"Error caching threat feed: {e}")
    
    def get_threat_feeds(self, ip: str) -> List[Dict]:
        """Get cached threat feeds for IP"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT feed_source, matched, match_details, confidence
                    FROM threat_feed_cache WHERE ip = ?
                """, (ip,))
                return [
                    {
                        'source': row[0],
                        'matched': bool(row[1]),
                        'details': row[2],
                        'confidence': row[3]
                    }
                    for row in cursor.fetchall()
                ]
            except Exception as e:
                print(f"Error getting threat feeds: {e}")
                return []
    
    def record_attack_trend(self, ip: str, protocol: str, attack_count: int, 
                           trend_score: float, velocity: float, consistency: float, 
                           anomaly_score: float, protocol_diversity: float) -> None:
        """Record attack trend data"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO attack_trends
                    (ip, timestamp, protocol, attack_count, trend_score, velocity, consistency, anomaly_score, protocol_diversity, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (ip, time.time(), protocol, attack_count, trend_score, velocity, consistency, anomaly_score, protocol_diversity))
                self.conn.commit()
            except Exception as e:
                print(f"Error recording attack trend: {e}")
    
    def get_attack_trends(self, ip: str, hours: int = 24) -> List[Dict]:
        """Get attack trends for IP"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cutoff_time = time.time() - (hours * 3600)
                cursor.execute("""
                    SELECT timestamp, protocol, attack_count, trend_score, velocity, consistency, anomaly_score
                    FROM attack_trends 
                    WHERE ip = ? AND timestamp > ?
                    ORDER BY timestamp ASC
                """, (ip, cutoff_time))
                return [
                    {
                        'timestamp': row[0],
                        'protocol': row[1],
                        'attack_count': row[2],
                        'trend_score': row[3],
                        'velocity': row[4],
                        'consistency': row[5],
                        'anomaly_score': row[6]
                    }
                    for row in cursor.fetchall()
                ]
            except Exception as e:
                print(f"Error getting attack trends: {e}")
                return []
    
    def save_threat_intelligence_score(self, ip: str, reputation_score: float, 
                                      geo_risk_score: float, feed_match_score: float,
                                      trend_score: float, composite_score: float, 
                                      threat_level: str, recommendations: List[str]) -> None:
        """Save threat intelligence analysis score"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO threat_intelligence_scores
                    (ip, reputation_score, geo_risk_score, feed_match_score, trend_score, 
                     composite_threat_score, threat_level, recommendations, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (ip, reputation_score, geo_risk_score, feed_match_score, trend_score,
                     composite_score, threat_level, '\n'.join(recommendations)))
                self.conn.commit()
            except Exception as e:
                print(f"Error saving threat intelligence score: {e}")
    
    def get_top_threat_ips(self, limit: int = 20) -> List[Dict]:
        """Get top threat IPs by composite score"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                # SQLite compatible query for top threats
                cursor.execute("""
                    SELECT ip, composite_threat_score, threat_level, analyzed_at
                    FROM (
                        SELECT ip, composite_threat_score, threat_level, analyzed_at,
                               ROW_NUMBER() OVER (PARTITION BY ip ORDER BY analyzed_at DESC) as rn
                        FROM threat_intelligence_scores
                    )
                    WHERE rn = 1
                    ORDER BY composite_threat_score DESC
                    LIMIT ?
                """, (limit,))
                results = cursor.fetchall()
                
                # Fallback if window functions not available
                if not results:
                    cursor.execute("""
                        SELECT ip, MAX(composite_threat_score), threat_level, analyzed_at
                        FROM threat_intelligence_scores
                        GROUP BY ip
                        ORDER BY composite_threat_score DESC
                        LIMIT ?
                    """, (limit,))
                    results = cursor.fetchall()
                
                return [
                    {
                        'ip': row[0],
                        'threat_score': row[1],
                        'threat_level': row[2],
                        'analyzed_at': row[3]
                    }
                    for row in results
                ]
            except Exception as e:
                print(f"Error getting top threat IPs: {e}")
                return []
    
    def get_threat_statistics(self) -> Dict:
        """Get threat intelligence statistics"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Total IPs analyzed
                cursor.execute("SELECT COUNT(DISTINCT ip) FROM threat_intelligence_scores")
                total_ips = cursor.fetchone()[0] or 0
                
                # Threat level distribution
                cursor.execute("""
                    SELECT threat_level, COUNT(*) FROM threat_intelligence_scores
                    GROUP BY threat_level
                """)
                threat_dist = dict(cursor.fetchall())
                
                # Average threat score
                cursor.execute("SELECT AVG(composite_threat_score) FROM threat_intelligence_scores")
                avg_score = cursor.fetchone()[0] or 0
                
                # Critical threats
                cursor.execute("SELECT COUNT(*) FROM threat_intelligence_scores WHERE threat_level = 'CRITICAL'")
                critical_count = cursor.fetchone()[0] or 0
                
                # Cached reputations
                cursor.execute("SELECT COUNT(*) FROM ip_reputation_cache")
                cached_rep = cursor.fetchone()[0] or 0
                
                # Cached geolocations
                cursor.execute("SELECT COUNT(*) FROM geo_data_cache")
                cached_geo = cursor.fetchone()[0] or 0
                
                # Feed matches
                cursor.execute("SELECT COUNT(*) FROM threat_feed_cache WHERE matched = 1")
                feed_matches = cursor.fetchone()[0] or 0
                
                return {
                    'total_ips_analyzed': total_ips,
                    'threat_level_distribution': threat_dist,
                    'average_threat_score': round(avg_score, 2),
                    'critical_threat_count': critical_count,
                    'cached_reputations': cached_rep,
                    'cached_geolocations': cached_geo,
                    'feed_matches': feed_matches,
                }
            except Exception as e:
                print(f"Error getting threat statistics: {e}")
                return {}
    
    def add_behavioral_baseline(self, source_ip: str, protocol: str,
                               avg_rate: float, avg_size: float,
                               patterns: Dict) -> bool:
        """Add or update behavioral baseline for an IP"""
        import json
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO behavioral_baselines
                (source_ip, protocol, avg_request_rate, avg_payload_size, common_patterns, observation_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (source_ip, protocol, avg_rate, avg_size, json.dumps(patterns), 1, time.time()))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding behavioral baseline: {e}")
            return False
    
    def get_behavioral_baseline(self, source_ip: str) -> Optional[Dict]:
        """Get behavioral baseline for an IP"""
        import json
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT source_ip, protocol, avg_request_rate, avg_payload_size, 
                       common_patterns, observation_count, last_updated
                FROM behavioral_baselines
                WHERE source_ip = ?
            """, (source_ip,))
            
            row = cursor.fetchone()
            if row:
                baseline = dict(row)
                baseline['common_patterns'] = json.loads(baseline['common_patterns']) if baseline['common_patterns'] else {}
                return baseline
            return None
        except Exception as e:
            print(f"Error getting behavioral baseline: {e}")
            return None
    
    def add_polymorphic_signature(self, base_pattern: str, description: str,
                                 severity: str = 'medium') -> bool:
        """Add a known polymorphic attack pattern"""
        cursor = self.conn.cursor()
        try:
            timestamp = time.time()
            cursor.execute("""
                INSERT OR REPLACE INTO polymorphic_signatures
                (base_pattern, pattern_description, severity, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (base_pattern, description, severity, timestamp, timestamp))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding polymorphic signature: {e}")
            return False
    
    def update_polymorphic_hit_count(self, base_pattern: str) -> bool:
        """Increment hit count for polymorphic pattern"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE polymorphic_signatures
                SET detection_hits = detection_hits + 1, last_seen = ?
                WHERE base_pattern = ?
            """, (time.time(), base_pattern))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating polymorphic hit count: {e}")
            return False
    
    def get_top_evasion_ips(self, limit: int = 10) -> List[Dict]:
        """Get IPs with highest evasion detection scores"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT source_ip, 
                       COUNT(*) as detection_count,
                       AVG(evasion_score) as avg_score,
                       MAX(evasion_score) as max_score
                FROM evasion_detections
                GROUP BY source_ip
                ORDER BY max_score DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting top evasion IPs: {e}")
            return []