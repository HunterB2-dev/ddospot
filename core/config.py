SERVICES = {
    "http": {"port": 8080, "protocol": "tcp"},
    "ssh": {"port": 2222, "protocol": "tcp"},
    "ssdp": {"port": 1900, "protocol": "udp"},
}

THRESHOLD_PER_MIN = 2000
BLACKLIST_SECONDS = 3600

LOG_FILE = "honeypot.log"

MAX_LOG_SIZE_MB = 10       # max veľkosť jedného log súboru
MAX_LOG_FILES = 5          # počet rotated logov
DISK_USAGE_LIMIT_MB = 100  # ochrana disku