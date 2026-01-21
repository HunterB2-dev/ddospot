import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(
        self,
        max_events: int = 20,
        window_seconds: int = 10,
        blacklist_seconds: int = 60,
    ):
        self.max_events = max_events
        self.window = window_seconds
        self.blacklist_seconds = blacklist_seconds

        self.events = defaultdict(lambda: deque())
        self.blacklist = {}

    def is_blacklisted(self, ip: str) -> bool:
        until = self.blacklist.get(ip)
        if not until:
            return False

        if time.time() > until:
            del self.blacklist[ip]
            return False

        return True

    def register_event(self, ip: str) -> bool:
        """
        Returns True if allowed, False if rate-limited / blacklisted
        """
        now = time.time()

        q = self.events[ip]
        # Always allow the first event for a new IP
        if len(q) == 0:
            q.append(now)
            return True
        
        # Blacklist check after first event allowance
        if self.is_blacklisted(ip):
            return False
        
        q.append(now)

        while q and now - q[0] > self.window:
            q.popleft()

        if len(q) > self.max_events:
            self.blacklist[ip] = now + self.blacklist_seconds
            self.events[ip].clear()
            return False

        return True
