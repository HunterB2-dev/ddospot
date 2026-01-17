import os
from config import MAX_LOG_SIZE_MB, MAX_LOG_FILES, DISK_USAGE_LIMIT_MB

def get_dir_size_mb(path="."):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)

def rotate_logs(log_file: str):
    if not os.path.exists(log_file):
        return

    size_mb = os.path.getsize(log_file) / (1024 * 1024)
    if size_mb < MAX_LOG_SIZE_MB:
        return

    for i in range(MAX_LOG_FILES - 1, 0, -1):
        src = f"{log_file}.{i}"
        dst = f"{log_file}.{i+1}"
        if os.path.exists(src):
            os.rename(src, dst)

    os.rename(log_file, f"{log_file}.1")

def enforce_disk_limit(log_file: str):
    if get_dir_size_mb(".") < DISK_USAGE_LIMIT_MB:
        return

    for i in range(MAX_LOG_FILES, 0, -1):
        f = f"{log_file}.{i}"
        if os.path.exists(f):
            os.remove(f)
            return
