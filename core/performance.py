"""
Performance Monitoring System for DDoSPot
Tracks API response times, database performance, resource usage, and throughput
"""

import time
import psutil
import threading
from collections import deque, defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and track system performance metrics"""
    
    def __init__(self, max_history=1000, window_minutes=60):
        self.max_history = max_history
        self.window_minutes = window_minutes
        
        # Response times tracking (endpoint -> list of response times)
        self.response_times = defaultdict(lambda: deque(maxlen=max_history))
        
        # Request counts
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
        # Database query tracking
        self.db_queries = deque(maxlen=max_history)
        self.db_query_times = deque(maxlen=max_history)
        
        # Overall throughput
        self.requests_per_second = deque(maxlen=60)  # Last 60 seconds
        self.errors_per_second = deque(maxlen=60)
        
        # System resources
        self.cpu_history = deque(maxlen=60)
        self.memory_history = deque(maxlen=60)
        
        # Timing for tracking
        self.last_update = time.time()
        self.start_time = time.time()
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        logger.info("Performance Monitor initialized")
    
    def track_request(self, endpoint, response_time, status_code, method='GET'):
        """Track an API request and its response time"""
        with self.lock:
            self.response_times[endpoint].append({
                'time': response_time,
                'timestamp': time.time(),
                'method': method,
                'status': status_code
            })
            
            self.request_counts[endpoint] += 1
            
            if status_code >= 400:
                self.error_counts[endpoint] += 1
    
    def track_db_query(self, query_time, query_type='select'):
        """Track a database query"""
        with self.lock:
            self.db_queries.append({
                'type': query_type,
                'timestamp': time.time()
            })
            self.db_query_times.append({
                'time': query_time,
                'timestamp': time.time()
            })
    
    def update_throughput(self):
        """Update throughput metrics (call once per second)"""
        with self.lock:
            now = time.time()
            
            # Count requests in current second
            recent_requests = sum(1 for endpoint in self.response_times.values() 
                                for item in endpoint 
                                if now - item['timestamp'] < 1)
            self.requests_per_second.append(recent_requests)
            
            # Count errors in current second
            recent_errors = sum(1 for endpoint in self.response_times.values()
                              for item in endpoint
                              if now - item['timestamp'] < 1 and item['status'] >= 400)
            self.errors_per_second.append(recent_errors)
    
    def update_system_resources(self):
        """Update CPU and memory usage (call periodically)"""
        try:
            with self.lock:
                process = psutil.Process()
                
                # CPU percentage
                cpu_percent = process.cpu_percent(interval=0.1)
                self.cpu_history.append({
                    'value': cpu_percent,
                    'timestamp': time.time()
                })
                
                # Memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = process.memory_percent()
                
                self.memory_history.append({
                    'value': memory_mb,
                    'percent': memory_percent,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.warning(f"Error updating system resources: {e}")
    
    def get_metrics_summary(self):
        """Get a summary of all performance metrics"""
        with self.lock:
            now = time.time()
            window_start = now - (self.window_minutes * 60)
            
            # Filter data within window
            recent_times = {}
            for endpoint, times in self.response_times.items():
                recent = [t for t in times if t['timestamp'] >= window_start]
                if recent:
                    recent_times[endpoint] = recent
            
            # Calculate statistics
            all_response_times = []
            for endpoint, times in recent_times.items():
                all_response_times.extend([t['time'] for t in times])
            
            if all_response_times:
                avg_response_time = sum(all_response_times) / len(all_response_times)
                min_response_time = min(all_response_times)
                max_response_time = max(all_response_times)
            else:
                avg_response_time = min_response_time = max_response_time = 0
            
            # Database stats
            recent_db_times = [t for t in self.db_query_times if t['timestamp'] >= window_start]
            if recent_db_times:
                avg_db_time = sum(t['time'] for t in recent_db_times) / len(recent_db_times)
                max_db_time = max(t['time'] for t in recent_db_times)
            else:
                avg_db_time = max_db_time = 0
            
            # Throughput stats
            if self.requests_per_second:
                avg_rps = sum(self.requests_per_second) / len(self.requests_per_second)
                max_rps = max(self.requests_per_second)
            else:
                avg_rps = max_rps = 0
            
            if self.errors_per_second:
                avg_eps = sum(self.errors_per_second) / len(self.errors_per_second)
                error_rate = (sum(self.errors_per_second) / (sum(self.requests_per_second) + 1)) * 100
            else:
                avg_eps = 0
                error_rate = 0
            
            # System resources
            cpu_value = self.cpu_history[-1]['value'] if self.cpu_history else 0
            if self.memory_history:
                memory_mb = self.memory_history[-1]['value']
                memory_percent = self.memory_history[-1]['percent']
            else:
                memory_mb = 0
                memory_percent = 0
            
            # Calculate uptime
            uptime_seconds = int(now - self.start_time)
            uptime_hours = uptime_seconds / 3600
            uptime_minutes = (uptime_seconds % 3600) / 60
            
            return {
                'response_times': {
                    'average': round(avg_response_time * 1000, 2),  # ms
                    'minimum': round(min_response_time * 1000, 2),
                    'maximum': round(max_response_time * 1000, 2),
                },
                'database': {
                    'average_query_time': round(avg_db_time * 1000, 2),  # ms
                    'max_query_time': round(max_db_time * 1000, 2),
                    'total_queries': len(self.db_queries),
                },
                'throughput': {
                    'avg_requests_per_second': round(avg_rps, 2),
                    'max_requests_per_second': max_rps,
                    'avg_errors_per_second': round(avg_eps, 2),
                    'error_rate_percent': round(error_rate, 2),
                },
                'system': {
                    'cpu_percent': round(cpu_value, 2),
                    'memory_mb': round(memory_mb, 2),
                    'memory_percent': round(memory_percent, 2),
                },
                'endpoints': self._get_endpoint_stats(recent_times),
                'uptime': {
                    'seconds': uptime_seconds,
                    'display': f"{int(uptime_hours)}h {int(uptime_minutes)}m",
                },
                'timestamp': now,
            }
    
    def _get_endpoint_stats(self, recent_times):
        """Get per-endpoint statistics"""
        stats = {}
        for endpoint, times in recent_times.items():
            if not times:
                continue
            
            response_times = [t['time'] for t in times]
            errors = sum(1 for t in times if t['status'] >= 400)
            
            stats[endpoint] = {
                'count': len(times),
                'errors': errors,
                'error_rate': round((errors / len(times)) * 100, 2) if times else 0,
                'avg_response_time': round((sum(response_times) / len(response_times)) * 1000, 2),
                'min_response_time': round(min(response_times) * 1000, 2),
                'max_response_time': round(max(response_times) * 1000, 2),
            }
        
        return stats
    
    def get_response_time_history(self, endpoint=None, limit=100):
        """Get response time history for an endpoint or all"""
        with self.lock:
            if endpoint:
                times = list(self.response_times.get(endpoint, []))
            else:
                times = []
                for endpoint_times in self.response_times.values():
                    times.extend(endpoint_times)
            
            # Sort by timestamp
            times.sort(key=lambda x: x['timestamp'])
            
            # Convert to display format
            result = []
            for t in times[-limit:]:
                result.append({
                    'time': round(t['time'] * 1000, 2),  # ms
                    'timestamp': datetime.fromtimestamp(t['timestamp']).isoformat(),
                    'status': t['status']
                })
            
            return result
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self.lock:
            self.response_times.clear()
            self.request_counts.clear()
            self.error_counts.clear()
            self.db_queries.clear()
            self.db_query_times.clear()
            self.requests_per_second.clear()
            self.errors_per_second.clear()
            self.cpu_history.clear()
            self.memory_history.clear()
            self.start_time = time.time()
            logger.info("Performance metrics reset")


# Global instance
_performance_monitor = None

def get_performance_monitor():
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def track_request(endpoint, response_time, status_code, method='GET'):
    """Convenience function to track a request"""
    get_performance_monitor().track_request(endpoint, response_time, status_code, method)

def track_db_query(query_time, query_type='select'):
    """Convenience function to track a database query"""
    get_performance_monitor().track_db_query(query_time, query_type)
