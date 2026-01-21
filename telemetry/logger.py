import json
import logging
import threading
from datetime import datetime
from core.config import LOG_FILE
from telemetry.rotation import rotate_logs, enforce_disk_limit

_lock = threading.Lock()
_loggers = {}

def get_logger(name: str):
    """Get or create a logger with the specified name."""
    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        _loggers[name] = logger
    return _loggers[name]

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
