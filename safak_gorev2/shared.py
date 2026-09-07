from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from collections import deque
from dataclasses import asdict
from pathlib import Path

from .types import Decision, Detection, Frame, Target


class LatestFrame:
    """Tek yuvalı posta kutusu. Yavaş tüketici geçmiş görüntüyü biriktiremez."""
    def __init__(self):
        self.condition = threading.Condition()
        self.frame: Frame | None = None
        self.replaced = 0

    def put(self, frame: Frame) -> None:
        with self.condition:
            if self.frame and frame.id <= self.frame.id:
                return
            self.frame = frame
            self.condition.notify_all()

    def get_after(self, frame_id: int, timeout: float = 0.25) -> Frame | None:
        with self.condition:
            self.condition.wait_for(lambda: self.frame is not None and self.frame.id > frame_id, timeout)
            return self.frame if self.frame is not None and self.frame.id > frame_id else None


def finite_json(value):
    if isinstance(value, dict):
        return {key: finite_json(v) for key, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


class SharedState:
    def __init__(self, mode: str):
        self.lock = threading.RLock()
        self.mode = mode
        self.started = time.monotonic()
        self.frame_id = None
        self.calibration_frame: Frame | None = None
        self.frame_at = -math.inf
        self.targets: tuple[Target, ...] = ()
        self.detections: tuple[Detection, ...] = ()
        self.diagnostics = []
        self.decision = Decision("STARTING", "Sistem başlatılıyor")
        self.backend = "BEKLENİYOR"
        self.pipeline_error = None
        self.geometry_reason = "Kalibrasyon/telemetri bekleniyor"
        self.camera_info = None
        self.frame_times = deque(maxlen=60)
        self.events = deque(maxlen=80)
        self.release = None
        self.jpeg = None
        self.jpeg_frame_at = -math.inf
        self.jpeg_id = 0
        self.jpeg_condition = threading.Condition()

    def event(self, kind: str, message: str, **details) -> dict:
        record = {"kind": kind, "message": message, "at": time.time(), **details}
        with self.lock:
            self.events.appendleft(record)
        return record

    def vision(self, frame: Frame, targets: tuple[Target, ...], reason: str, diagnostics=None) -> None:
        with self.lock:
            if self.mode == "observe":
                self.calibration_frame = frame
            self.frame_id, self.frame_at = frame.id, frame.captured_at
            self.targets, self.geometry_reason = targets, reason
            self.detections = frame.detections
            self.diagnostics = diagnostics or []
            self.frame_times.append(frame.received_at)
            self.backend = frame.backend

    def vision_snapshot(self):
        with self.lock:
            return self.frame_id, self.frame_at, self.targets

    def jpeg_put(self, jpeg: bytes, at: float, frame_id: int) -> None:
        with self.jpeg_condition:
            self.jpeg, self.jpeg_frame_at, self.jpeg_id = jpeg, at, frame_id
            self.jpeg_condition.notify_all()


class EventLedger:
    """Temsili olay diske atomik yazılır; aynı uçuş kimliği ikinci bırakmayı reddeder."""
    def __init__(self, root: str | Path, sortie_id: str):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self.path, self.sortie_id = root / "events.sqlite3", sortie_id
        self.lock = threading.Lock()
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at REAL NOT NULL, sortie TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL)")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS release_once ON events(sortie) WHERE kind='SIMULATED_RELEASE'")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=0.5)
        db.execute("PRAGMA synchronous=FULL")
        return db

    def record(self, kind: str, body: dict) -> None:
        with self.lock, self._connect() as db:
            db.execute("INSERT INTO events(at,sortie,kind,body) VALUES (?,?,?,?)",
                       (time.time(), self.sortie_id, kind, json.dumps(finite_json(body), ensure_ascii=False)))

    def release_once(self, body: dict) -> bool:
        try:
            self.record("SIMULATED_RELEASE", {"simulated": True, "payload": "KIRMIZI", **body})
            return True
        except sqlite3.IntegrityError:
            return False
