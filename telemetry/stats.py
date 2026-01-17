from collections import defaultdict
import time

_service_counter = defaultdict(int)
_ip_timestamps = defaultdict(list)

def record(service: str, ip: str):
    _service_counter[service] += 1
    _ip_timestamps[ip].append(time.time())

def service_stats():
    return dict(_service_counter)

def ip_rate(ip: str, window: int = 60):
    now = time.time()
    return len([t for t in _ip_timestamps[ip] if now - t < window])
