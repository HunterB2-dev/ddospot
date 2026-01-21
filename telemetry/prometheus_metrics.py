"""
Prometheus metrics collection for DDoSPoT honeypot system.
Exposes comprehensive metrics for monitoring attack patterns, service health, and performance.
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client.multiprocess import MultiProcessCollector
import time
import psutil
import os
from pathlib import Path
from typing import Optional


class PrometheusMetrics:
    """Centralized Prometheus metrics for DDoSPoT"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize all Prometheus metrics with optional custom registry"""
        self.registry = registry or CollectorRegistry()
        
        # ===== ATTACK METRICS =====
        self.attack_events_total = Counter(
            'ddospot_attack_events_total',
            'Total number of attack events captured',
            ['protocol', 'event_type'],
            registry=self.registry
        )
        
        self.attack_bytes_total = Counter(
            'ddospot_attack_bytes_total',
            'Total bytes received from attacks',
            ['protocol'],
            registry=self.registry
        )
        
        self.unique_attackers = Gauge(
            'ddospot_unique_attackers',
            'Number of unique attacker IPs',
            registry=self.registry
        )
        
        self.blacklisted_ips = Gauge(
            'ddospot_blacklisted_ips',
            'Number of IPs on blacklist',
            registry=self.registry
        )
        
        # ===== SERVICE HEALTH =====
        self.service_status = Gauge(
            'ddospot_service_status',
            'Service running status (1=running, 0=stopped)',
            ['service'],
            registry=self.registry
        )
        
        self.service_uptime_seconds = Gauge(
            'ddospot_service_uptime_seconds',
            'Service uptime in seconds',
            ['service'],
            registry=self.registry
        )
        
        # ===== DATABASE METRICS =====
        self.database_size_bytes = Gauge(
            'ddospot_database_size_bytes',
            'Database file size in bytes',
            registry=self.registry
        )
        
        self.database_events_total = Gauge(
            'ddospot_database_events_total',
            'Total events in database',
            registry=self.registry
        )
        
        self.database_profiles_total = Gauge(
            'ddospot_database_profiles_total',
            'Total attacker profiles in database',
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'ddospot_database_query_duration_seconds',
            'Database query execution time',
            ['operation'],
            registry=self.registry
        )
        
        # ===== SYSTEM METRICS =====
        self.cpu_usage_percent = Gauge(
            'ddospot_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage_bytes = Gauge(
            'ddospot_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.disk_usage_percent = Gauge(
            'ddospot_disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )
        
        # ===== HTTP METRICS =====
        self.http_requests_total = Counter(
            'ddospot_http_requests_total',
            'Total HTTP requests to dashboard',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'ddospot_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # ===== GEOLOCATION METRICS =====
        self.geolocation_cache_hits = Counter(
            'ddospot_geolocation_cache_hits_total',
            'Geolocation cache hits',
            registry=self.registry
        )
        
        self.geolocation_cache_misses = Counter(
            'ddospot_geolocation_cache_misses_total',
            'Geolocation cache misses',
            registry=self.registry
        )
        
        self.geolocation_countries_total = Gauge(
            'ddospot_geolocation_countries_total',
            'Number of unique countries',
            registry=self.registry
        )
        
        # ===== MACHINE LEARNING METRICS =====
        self.ml_predictions_total = Counter(
            'ddospot_ml_predictions_total',
            'Total ML predictions made',
            ['prediction'],
            registry=self.registry
        )
        
        self.ml_prediction_duration_seconds = Histogram(
            'ddospot_ml_prediction_duration_seconds',
            'ML prediction latency',
            registry=self.registry
        )
        
        # ===== ALERT METRICS =====
        self.alerts_sent_total = Counter(
            'ddospot_alerts_sent_total',
            'Total alerts sent',
            ['channel', 'severity'],
            registry=self.registry
        )
        
        self.alerts_failed_total = Counter(
            'ddospot_alerts_failed_total',
            'Failed alert deliveries',
            ['channel', 'reason'],
            registry=self.registry
        )
        
        # ===== LOG METRICS =====
        self.log_file_size_bytes = Gauge(
            'ddospot_log_file_size_bytes',
            'Log file size in bytes',
            ['log_type'],
            registry=self.registry
        )
        
        self.log_rotations_total = Counter(
            'ddospot_log_rotations_total',
            'Total log rotations performed',
            ['log_type'],
            registry=self.registry
        )
        
        # ===== INFO METRIC =====
        self.build_info = Info(
            'ddospot_build',
            'DDoSPoT build information',
            registry=self.registry
        )
        self.build_info.info({
            'version': '2.0.0',
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        })
        
        # Track start time for uptime calculation
        self.start_time = time.time()
    
    def record_attack_event(self, protocol: str, event_type: str, payload_size: int):
        """Record an attack event"""
        self.attack_events_total.labels(protocol=protocol, event_type=event_type).inc()
        self.attack_bytes_total.labels(protocol=protocol).inc(payload_size)
    
    def update_database_metrics(self, size_bytes: int, event_count: int, profile_count: int):
        """Update database-related metrics"""
        self.database_size_bytes.set(size_bytes)
        self.database_events_total.set(event_count)
        self.database_profiles_total.set(profile_count)
    
    def update_service_status(self, service: str, running: bool):
        """Update service status (1=running, 0=stopped)"""
        self.service_status.labels(service=service).set(1 if running else 0)
    
    def update_service_uptime(self, service: str, uptime_seconds: float):
        """Update service uptime"""
        self.service_uptime_seconds.labels(service=service).set(uptime_seconds)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage_percent.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage_bytes.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.disk_usage_percent.set(disk.percent)
        except Exception:
            pass
    
    def update_log_metrics(self):
        """Update log file metrics"""
        logs = [
            ("honeypot", Path("/tmp/honeypot.log")),
            ("dashboard", Path("/tmp/dashboard.log"))
        ]
        
        for log_type, log_path in logs:
            if log_path.exists():
                size = log_path.stat().st_size
                self.log_file_size_bytes.labels(log_type=log_type).set(size)
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_alert(self, channel: str, severity: str, success: bool, reason: str = ""):
        """Record alert metrics"""
        if success:
            self.alerts_sent_total.labels(channel=channel, severity=severity).inc()
        else:
            self.alerts_failed_total.labels(channel=channel, reason=reason).inc()
    
    def record_geolocation_lookup(self, cache_hit: bool):
        """Record geolocation cache metrics"""
        if cache_hit:
            self.geolocation_cache_hits.inc()
        else:
            self.geolocation_cache_misses.inc()
    
    def record_ml_prediction(self, prediction: str, duration: float):
        """Record ML prediction metrics"""
        self.ml_predictions_total.labels(prediction=prediction).inc()
        self.ml_prediction_duration_seconds.observe(duration)
    
    def record_log_rotation(self, log_type: str):
        """Record log rotation event"""
        self.log_rotations_total.labels(log_type=log_type).inc()
    
    def get_metrics(self) -> bytes:
        """Generate Prometheus metrics output"""
        return generate_latest(self.registry)


# Global metrics instance
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """Get or create the global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def reset_metrics():
    """Reset metrics instance (useful for testing)"""
    global _metrics_instance
    _metrics_instance = None
