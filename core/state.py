import time
from collections import defaultdict, deque

class HoneypotState:
    def __init__(self):
        self.activity = defaultdict(lambda: deque(maxlen=100))
        self.blacklist = {}

    def is_blacklisted(self, ip: str) -> bool:
        return ip in self.blacklist and self.blacklist[ip] > time.time()

    def blacklist_ip(self, ip: str, duration: int):
        self.blacklist[ip] = time.time() + duration
