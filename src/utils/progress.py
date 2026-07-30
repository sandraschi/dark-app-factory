import asyncio
import threading
import time


class ProgressTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._percentage = 0
                cls._instance._status = "Ready"
                cls._instance._active = False
                cls._instance._steps: list[dict] = []
                cls._instance._specialists: dict[str, str] = {}
                cls._instance._files: list[str] = []
                cls._instance._run_id: str = ""
                cls._instance._events: asyncio.Queue = asyncio.Queue()
            return cls._instance

    def start_run(self, run_id: str):
        with self._lock:
            self._run_id = run_id
            self._percentage = 0
            self._status = "Starting"
            self._active = True
            self._steps = []
            self._specialists = {}
            self._files = []
        self._emit({"type": "run_start", "run_id": run_id})

    def update(self, percentage: int, status: str):
        with self._lock:
            self._percentage = percentage
            self._status = status
            self._active = True
        self._emit({"type": "progress", "percentage": percentage, "status": status})

    def add_step(self, name: str, detail: str = ""):
        entry = {"name": name, "detail": detail, "ts": time.time(), "status": "running"}
        with self._lock:
            self._steps.append(entry)
        self._emit({"type": "step_start", "step": entry})

    def complete_step(self, name: str, status: str = "done"):
        with self._lock:
            for s in self._steps:
                if s["name"] == name:
                    s["status"] = status
                    break
        self._emit({"type": "step_done", "name": name, "status": status})

    def specialist_status(self, name: str, status: str, detail: str = ""):
        with self._lock:
            self._specialists[name] = status
        self._emit({"type": "specialist", "name": name, "status": status, "detail": detail})

    def add_file(self, path: str):
        with self._lock:
            self._files.append(path)
        self._emit({"type": "file", "path": path})

    def reset(self):
        with self._lock:
            self._percentage = 0
            self._status = "Ready"
            self._active = False
            self._steps = []
            self._specialists = {}
            self._files = []
            self._run_id = ""
        while not self._events.empty():
            try:
                self._events.get_nowait()
            except asyncio.QueueEmpty:
                break

    def get_state(self):
        with self._lock:
            return {
                "percentage": self._percentage,
                "status": self._status,
                "active": self._active,
                "run_id": self._run_id,
                "steps": list(self._steps),
                "specialists": dict(self._specialists),
                "files": list(self._files),
            }

    def subscribe(self) -> asyncio.Queue:
        return self._events

    def _emit(self, event: dict):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(lambda: self._events.put_nowait(event))
        except RuntimeError:
            pass


progress = ProgressTracker()
