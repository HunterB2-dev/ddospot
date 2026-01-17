from prometheus_client import start_http_server, Counter

REQUESTS = Counter(
    "honeypot_requests_total",
    "Total honeypot events"
)

def start_metrics():
    start_http_server(9000)
