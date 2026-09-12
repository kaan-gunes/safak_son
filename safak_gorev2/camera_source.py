"""Picamera2 yapılandırması ve sensör zaman damgası eşlemesi."""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
import threading
import time

from .config import Config


def create_picamera(cfg: Config):
    if cfg.camera.backend != "picamera2":
        raise ValueError("Bu profil Picamera2 kullanamaz; fallback yok")
    from picamera2 import Picamera2
    from libcamera import Transform, controls
    camera = Picamera2()
    if cfg.camera.identity and camera.camera_properties.get("Model") != cfg.camera.identity:
        camera.close()
        raise ValueError("Gerçek kamera kimliği profille uyuşmuyor; fallback yok")
    capture_controls = {"FrameRate": cfg.camera.fps}
    sensor_args = {}
    if cfg.camera.sensor_output_size is not None:
        sensor_args["sensor"] = {"output_size": tuple(cfg.camera.sensor_output_size), "bit_depth": 10}
    if cfg.camera.lens_position is not None:
        limits = camera.camera_controls.get("LensPosition")
        if limits is None or not limits[0] <= cfg.camera.lens_position <= limits[1]:
            camera.close()
            raise ValueError("Kamera istenen sabit odak konumunu desteklemiyor")
        capture_controls.update(AfMode=controls.AfModeEnum.Manual, LensPosition=cfg.camera.lens_position)
    if cfg.camera.calibration_file:
        saved = json.loads(Path(cfg.camera.calibration_file).read_text())
        if saved.get("lens_position") is not None and (
            cfg.camera.lens_position != saved["lens_position"] or
            tuple(cfg.camera.sensor_output_size or ()) != tuple(saved.get("sensor_output_size", ()))
        ):
            camera.close()
            raise ValueError("Kalibrasyonun sabit odak/sensör modu yapılandırmayla uyuşmuyor")
    camera.configure(camera.create_video_configuration(
        main={"size": (cfg.camera.width, cfg.camera.height), "format": "RGB888"},
        controls=capture_controls, buffer_count=4,
        transform=Transform(hflip=False, vflip=False), queue=False, **sensor_args))
    return camera


class CaptureClock:
    def __init__(self):
        self.origin_ns = time.monotonic_ns()
        self.lock = threading.Lock()
        self.frames = OrderedDict()
        self.last_sensor_ns = -1
        self.sequence = 0

    def register(self, sensor_ns: int) -> tuple[int, float, int] | None:
        if sensor_ns <= self.last_sensor_ns:
            return None
        # libcamera SensorTimestamp CLOCK_BOOTTIME tabanlı; uygulama MONOTONIC kullanır.
        boot = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        monotonic = time.monotonic_ns()
        age = boot - sensor_ns
        if age < 0 or age > 2_000_000_000:
            raise RuntimeError("Kamera SensorTimestamp geçersiz/eski")
        captured = monotonic - age
        pts = max(0, captured - self.origin_ns)
        self.last_sensor_ns = sensor_ns
        self.sequence += 1
        with self.lock:
            self.frames[pts] = (self.sequence, captured / 1e9)
            while len(self.frames) > 128:
                self.frames.popitem(last=False)
        return pts, captured / 1e9, self.sequence

    def lookup(self, pts: int):
        with self.lock:
            return self.frames.get(pts)
