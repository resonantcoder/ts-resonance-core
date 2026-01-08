import time
from collections import deque

class Debouncer:
    """
    Temporal logic gate.
    Trips ONLY if 'threshold' events occur within 'window_seconds'.
    """
    def __init__(self, threshold: int = 5, window_seconds: int = 60):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.events = deque()
        self.is_active = False 

    def prune(self):
        """Remove old events from history."""
        now = time.time()
        while len(self.events) > 0 and self.events[0] < (now - self.window_seconds):
            self.events.popleft()

    def trigger(self, score: float) -> bool:
        """
        Ingests a score. 
        Returns True ONLY if this specific event pushed us over the threshold.
        """
        # If normal, just prune and return current state
        if score == 1:
            self.prune()
            # Auto-reset if the window clears? Optional. 
            # For now, we manually reset via CLI logic or keep the latch open.
            if len(self.events) == 0:
                self.is_active = False
            return self.is_active

        # If Anomaly (-1)
        now = time.time()
        self.events.append(now)
        self.prune()

        if len(self.events) >= self.threshold:
            if not self.is_active:
                self.is_active = True
                return True # RISING EDGE (New Alarm)
            
        return False # Already active or threshold not met

    @property
    def current_load(self) -> int:
        self.prune()
        return len(self.events)
