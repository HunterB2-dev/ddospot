SERVICES = {
    "http": {"port": 8080, "protocol": "tcp"},
    "ssh": {"port": 2222, "protocol": "tcp"},
    "ftp": {"port": 21, "protocol": "tcp"},
    "telnet": {"port": 23, "protocol": "tcp"},
    "mysql": {"port": 3306, "protocol": "tcp"},
    "postgresql": {"port": 5432, "protocol": "tcp"},
    "redis": {"port": 6379, "protocol": "tcp"},
    "mongodb": {"port": 27017, "protocol": "tcp"},
    "ssdp": {"port": 1900, "protocol": "udp"},
}

# Extract TCP and UDP ports from SERVICES
TCP_PORTS = [service["port"] for service in SERVICES.values() if service["protocol"] == "tcp"]
UDP_PORTS = [service["port"] for service in SERVICES.values() if service["protocol"] == "udp"]

# Detection thresholds
THRESHOLD_PER_MIN = 100  # Events per minute to trigger blacklist (lowered for testing)
BLACKLIST_SECONDS = 3600

LOG_FILE = "honeypot.log"

MAX_LOG_SIZE_MB = 10       # max veľkosť jedného log súboru
MAX_LOG_FILES = 5          # počet rotated logov
DISK_USAGE_LIMIT_MB = 100  # ochrana disku