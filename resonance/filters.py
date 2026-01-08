import time
from collections import deque

class Debouncer:
    """
    A temporal logic gate that triggers only if 'threshold' events 
    occur within 'window_seconds'.
    Useful for preventing alert fatigue (flapping) from noisy sensors.
    """
    def __init__(self, threshold: int = 5, window_seconds: int = 60):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.events = deque()
        self.is_active = False # Tracks if the gate has been tripped (Latch)

    def prune(self):
        """Remove old events from history."""
        now = time.time()
        while len(self.events) > 0 and self.events[0] < (now - self.window_seconds):
            self.events.popleft()

    def trigger(self, score: float) -> bool:
        """
        Registers a score event.
        Returns True ONLY if this specific event caused the gate to trip (Rising Edge).
        """
        # 1. If Normal (1.0), just prune and check if we should reset
        if score == 1:
            self.prune()
            # Optional: Auto-reset latch if buffer clears? 
            # For now, we keep the latch logic simple (manual reset or decay)
            if len(self.events) == 0:
                self.is_active = False
            return False

        # 2. If Anomaly (-1.0), add to buffer
        now = time.time()
        self.events.append(now)
        self.prune()

        # 3. Check Threshold (Rising Edge Detection)
        if len(self.events) >= self.threshold:
            if not self.is_active:
                self.is_active = True
                return True # RISING EDGE
            
        return False

    def reset(self):
        """Resets the gate state (release latch)."""
        self.events.clear()
        self.is_active = False

    @property
    def count(self) -> int:
        """Current number of active events in the window."""
        self.prune()
        return len(self.events)
