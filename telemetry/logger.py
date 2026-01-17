import json
import threading
from datetime import datetime
from config import LOG_FILE
from telemetry.rotation import rotate_logs, enforce_disk_limit

_lock = threading.Lock()

def log_event(event_type: str, data: dict):
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "type": event_type,
        **data
    }

    with _lock:
        rotate_logs(LOG_FILE)
        enforce_disk_limit(LOG_FILE)

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
