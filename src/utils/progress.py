import threading


class ProgressTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProgressTracker, cls).__new__(cls)
                cls._instance._percentage = 0
                cls._instance._status = "Ready"
                cls._instance._active = False
            return cls._instance

    def update(self, percentage: int, status: str):
        with self._lock:
            self._percentage = percentage
            self._status = status
            self._active = True

    def reset(self):
        with self._lock:
            self._percentage = 0
            self._status = "Ready"
            self._active = False

    def get_state(self):
        with self._lock:
            return {
                "percentage": self._percentage,
                "status": self._status,
                "active": self._active,
            }


# Global instance for easy import
progress = ProgressTracker()
