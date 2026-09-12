"""Gerçek kameradan doğrudan OpenCV kare kaynağı."""
from __future__ import annotations

import time

from .camera_contract import capture_missing, validate_camera
from .camera_source import CaptureClock, create_picamera
from .geometry import Calibration
from .types import Frame


def run_opencv_camera(cfg, mailbox, state, stop) -> None:
    validate_camera(cfg.camera)
    missing = capture_missing(cfg.camera)
    if missing:
        raise ValueError("Kamera: " + "; ".join(missing))
    calibration = (Calibration.load(cfg.camera.calibration_file)
                   if cfg.camera.calibration_file and cfg.camera.backend == "picamera2" else None)
    camera = None
    clock = CaptureClock()
    state.capture_count = 0
    try:
        if cfg.camera.backend == "v4l2-observe":
            from .v4l2_camera import V4L2Camera
            camera = V4L2Camera(cfg)
        else:
            camera = create_picamera(cfg)
        camera.start()
        focus_deadline = time.monotonic() + 3.0
        model = camera.camera_properties.get("Model", "UNKNOWN")
        while not stop.is_set():
            request = camera.capture_request()
            try:
                meta = request.get_metadata()
                crop = tuple(meta.get("ScalerCrop", ()))
                if cfg.camera.lens_position is not None:
                    actual_focus = meta.get("LensPosition")
                    if actual_focus is None or abs(actual_focus-cfg.camera.lens_position) > .001:
                        if time.monotonic() < focus_deadline:
                            continue
                        raise RuntimeError("Kamera odağı kalibrasyonun sabit konumuyla uyuşmuyor")
                if calibration:
                    calibration.verify_stream(cfg.camera.width, cfg.camera.height, model, crop)
                stream_info = {"model": model, "width": cfg.camera.width,
                    "height": cfg.camera.height, "scaler_crop": crop, "mirror": False,
                    "timestamp": meta.get("TimestampSource", "SensorTimestamp"),
                    "backend": cfg.camera.backend, "identity": model, "device": cfg.camera.device,
                    "usb_vid_pid": cfg.camera.usb_vid_pid, "vision_backend": "opencv-color"}
                if cfg.camera.lens_position is not None:
                    stream_info.update(lens_position=cfg.camera.lens_position, focus_mode="manual",
                        sensor_output_size=tuple(cfg.camera.sensor_output_size or ()))
                if state.camera_info and state.camera_info != stream_info:
                    raise RuntimeError("Çalışma sırasında kamera modeli/ScalerCrop değişti")
                state.camera_info = stream_info
                sensor_ns = meta.get("SensorTimestamp")
                if sensor_ns is None:
                    raise RuntimeError("Kamera SensorTimestamp sağlamıyor")
                registered = clock.register(int(sensor_ns))
                if registered is None:
                    continue
                image = request.make_array("main").copy()
                state.capture_count += 1
                mailbox.put(Frame(registered[2], registered[1], time.monotonic(), image, (), "OPENCV"))
            finally:
                request.release()
    finally:
        if camera is not None:
            camera.stop()
            camera.close()
