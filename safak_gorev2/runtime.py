from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from .config import Config
from .controller import Controller
from .geometry import Calibration, TargetGeometry
from .mavlink_io import MavlinkLink, TelemetryStore
from .shared import EventLedger, LatestFrame, SharedState, finite_json
from .types import Decision


class Runtime:
    def __init__(self, cfg: Config, mode: str):
        self.cfg, self.mode = cfg, mode
        self.stop = threading.Event()
        self.mailbox = LatestFrame()
        self.state = SharedState(mode)
        self.telemetry = TelemetryStore()
        self.controller = Controller(cfg)
        self.link = None
        self.threads = []
        self.sortie_id = uuid.uuid4().hex
        self.ledger = EventLedger(cfg.runtime_dir, self.sortie_id)
        self.disk = ThreadPoolExecutor(max_workers=1, thread_name_prefix="event-ledger")
        self.release_job = None
        self.release_recorded = False
        self.demo_sink = None
        self.geometry_override = None

    def start(self, connect=True) -> None:
        if connect:
            self.link = MavlinkLink(self.cfg, self.telemetry, self.mode == "flight", self.stop)
            self.link.start()
        for name, function in (("vision-verification", self.vision_loop),
                               ("mission-control", self.control_loop),
                               ("panel-jpeg", self.render_loop), ("flight-record", self.record_loop)):
            def guarded(target=function, thread_name=name):
                try:
                    target()
                except Exception as e:
                    message = f"{thread_name}: {e}"
                    self.state.pipeline_error = message
                    self.state.event("ERROR", message)
                    if self.link:
                        self.link.failure = message
            thread = threading.Thread(target=guarded, name=name, daemon=True)
            thread.start()
            self.threads.append(thread)
        self.state.event("START", "Program başlatıldı", mode=self.mode, sortie=self.sortie_id)

    def close(self) -> None:
        self.stop.set()
        for thread in self.threads:
            thread.join(timeout=2)
        if self.link and self.link.thread:
            self.link.thread.join(timeout=2)
        self.disk.shutdown(wait=True)

    def vision_loop(self) -> None:
        cfg = self.cfg
        geometry = self.geometry_override
        if geometry is None and cfg.camera.calibration_file and cfg.camera.offset_body_m is not None:
            geometry = TargetGeometry(cfg.camera, Calibration.load(cfg.camera.calibration_file))
        last_id = -1
        while not self.stop.is_set():
            frame = self.mailbox.get_after(last_id)
            if frame is None:
                continue
            last_id = frame.id
            targets = ()
            diagnostics = []
            reason = "AI tespiti gösteriliyor; metrik konum için kalibrasyon ve kamera ofseti gerekli"
            if time.monotonic() - frame.captured_at > cfg.control.frame_timeout_s:
                reason = "Eski görüntü: kilit ve merkezleme için kullanılmadı"
            elif geometry:
                pose = self.telemetry.pose_at(frame.captured_at, cfg.control.exposure_sync_tolerance_s)
                if pose:
                    if isinstance(geometry, TargetGeometry):
                        targets = geometry.detect(frame, pose, diagnostics)
                    else:
                        targets = geometry.detect(frame, pose)
                    labels = {"score": "skor eşik altında", "no_corners": "dört köşe bulunamadı",
                              "border": "kadraj kenarı/kesik hedef", "occupancy": "kadraj doluluğu fazla",
                              "metric_geometry": "metrik geometri doğrulanmadı", "class": "mavi sınıf değil"}
                    rejected = sorted({labels[r] for d in diagnostics for r in d["reasons"]})
                    reason = ("Geometri geçerli; görev kilidi ayrıca gerekli" if targets else
                              "Hedef kabul edilmedi: " + ("; ".join(rejected) or "mavi aday yok"))
                else:
                    reason = "Çekim anıyla eşleşen Pixhawk duruş/konum verisi yok"
            self.state.vision(frame, targets, reason, diagnostics)

    def control_loop(self) -> None:
        previous_state = None
        interval = 1 / self.cfg.control.rate_hz
        while not self.stop.is_set():
            tick = time.monotonic()
            t = self.telemetry.snapshot()
            frame_id, frame_at, targets = self.state.vision_snapshot()
            if self.release_job and self.release_job.done() and not self.release_recorded:
                try:
                    if not self.release_job.result():
                        raise RuntimeError("Bu uçuş için temsili bırakma daha önce kaydedildi")
                    self.release_recorded = True
                    record = self.state.event("SIMULATED_RELEASE", "KIRMIZI YÜK TEMSİLİ OLARAK BIRAKILDI",
                                              simulated=True, frame_id=frame_id)
                    self.state.release = record
                except Exception as e:
                    self.state.pipeline_error = f"Temsili olay kaydı: {e}"
                    self.release_job = None
            if self.mode == "observe":
                decision = Decision("OBSERVING", "Hailo tespiti ve Pixhawk verileri izleniyor; uçuş komutu gönderilmez")
            else:
                problem = self.state.pipeline_error or self.telemetry.preflight_problem()
                decision = self.controller.step(tick, t, targets, frame_id, frame_at,
                            self.telemetry.mission, problem, self.release_recorded)
                link_actions = tuple(a for a in decision.actions if a.kind != "release")
                if self.link:
                    self.link.submit(link_actions)
                elif self.demo_sink:
                    self.demo_sink(link_actions)
                for action in decision.actions:
                    if action.kind == "release" and self.release_job is None:
                        body = {"frame_id": action.values[0], "error_m": action.values[1],
                                "camera_height_m": action.values[2], "telemetry": asdict(t), "mode": self.mode}
                        self.release_job = self.disk.submit(self.ledger.release_once, body)
            with self.state.lock:
                self.state.decision = decision
            if decision.state != previous_state:
                event = self.state.event("STATE", decision.reason, state=decision.state)
                self.disk.submit(self.ledger.record, "STATE", event)
                previous_state = decision.state
            self.stop.wait(max(0, interval - (time.monotonic() - tick)))

    def render_loop(self) -> None:
        last_id = -1
        interval = 1 / self.cfg.web.fps
        while not self.stop.is_set():
            tick = time.monotonic()
            frame = self.mailbox.get_after(last_id)
            if frame is None:
                continue
            last_id = frame.id
            image = frame.image.copy()
            h, w = image.shape[:2]
            for d in frame.detections:
                x1, y1, x2, y2 = [round(x) for x in np.array(d.bbox) * [w, h, w, h]]
                color = (255, 165, 45) if d.label == "mavi_hedef" else (90, 90, 240)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                cv2.putText(image, f"AI ADAYI {d.label} {d.confidence:.2f}", (max(0, x1), max(22, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, .6, color, 2)
            _, _, targets = self.state.vision_snapshot()
            for target in targets:
                if target.frame_id == frame.id:
                    cv2.polylines(image, [np.array(target.corners, np.int32)], True, (140, 245, 150), 2)
            center = (w // 2, h // 2)
            cv2.drawMarker(image, center, (210, 210, 210), cv2.MARKER_CROSS, 22, 1)
            cv2.putText(image, "KAMERA MERKEZI", (center[0] + 14, center[1] + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, .4, (200, 200, 200), 1)
            label = "SENTETIK DEMO" if self.mode == "demo" else self.state.backend
            cv2.putText(image, label, (18, 30), cv2.FONT_HERSHEY_SIMPLEX, .65, (255, 205, 105), 2)
            if self.state.release:
                cv2.rectangle(image, (0, h - 64), (w, h), (28, 65, 35), -1)
                cv2.putText(image, "KIRMIZI YUK TEMSILI OLARAK BIRAKILDI", (18, h - 26),
                            cv2.FONT_HERSHEY_SIMPLEX, .7, (160, 255, 180), 2)
            width = min(w, self.cfg.web.width)
            image = cv2.resize(image, (width, round(h * width / w)), interpolation=cv2.INTER_AREA)
            ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, self.cfg.web.jpeg_quality])
            if ok:
                self.state.jpeg_put(encoded.tobytes(), frame.captured_at, frame.id)
            self.stop.wait(max(0, interval - (time.monotonic() - tick)))

    def record_loop(self) -> None:
        path = Path(self.cfg.runtime_dir) / f"telemetry-{self.sortie_id}.jsonl"
        with path.open("a", buffering=1) as stream:
            while not self.stop.wait(0.2):
                now = time.monotonic()
                with self.state.lock:
                    frame_id, frame_at, targets = self.state.vision_snapshot()
                    detections = self.state.detections
                    diagnostics = self.state.diagnostics
                    geometry_reason = self.state.geometry_reason
                data = {"wall_time": time.time(), "monotonic": now, "mode": self.mode,
                        "backend": self.state.backend, "frame_id": frame_id, "frame_at": frame_at,
                        "targets": [asdict(x) for x in targets],
                        "detections": [asdict(x) for x in detections],
                        "diagnostics": diagnostics, "geometry_reason": geometry_reason,
                        "telemetry": asdict(self.telemetry.snapshot()),
                        "decision": asdict(self.state.decision)}
                stream.write(json.dumps(finite_json(data), ensure_ascii=False) + "\n")
