"""Kullanıcının detection.py hattı: GStreamerDetectionApp → hailonet → Hailo ROI.

AI için CPU/ONNX/PyTorch yedeği yoktur. OpenCV yalnız ikincil görüntü işlemedir.
Hailo paketleri Pi'nin mevcut ortamından alınır; uygulama sürücü kurmaz/değiştirmez.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from collections import OrderedDict, deque
from pathlib import Path

import cv2

from .config import Config
from .geometry import Calibration
from .shared import LatestFrame, SharedState
from .types import Detection, Frame


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


def run_hailo(cfg: Config, mailbox: LatestFrame, state: SharedState,
              stop: threading.Event, hailo_env: str | None = None) -> None:
    if hailo_env:
        if not Path(hailo_env).is_file():
            raise RuntimeError("Belirtilen Hailo .env dosyası bulunamadı")
        os.environ["HAILO_ENV_FILE"] = str(Path(hailo_env).resolve())
    from .camera_contract import validate_camera, capture_missing
    validate_camera(cfg.camera)
    missing = capture_missing(cfg.camera)
    if missing:
        raise ValueError("Kamera: " + "; ".join(missing))
    cfg.verify_model()
    try:
        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst, GLib
        import hailo
        # detection.py dosyasındaki modül yolları korunuyor.
        from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
        from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
        from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp
        from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import (
            INFERENCE_PIPELINE, INFERENCE_PIPELINE_WRAPPER, USER_CALLBACK_PIPELINE)
    except ImportError as e:
        raise RuntimeError("Hailo ortamı açılamadı. detection.py'nin çalıştığı ortamı etkinleştirin; CPU'ya geçilmedi. " + str(e)) from e

    clock = CaptureClock()
    state.hailo_samples = deque(maxlen=10000)
    state.capture_count = 0
    inference_started = OrderedDict()
    inference_ms = OrderedDict()
    calibration = Calibration.load(cfg.camera.calibration_file) if cfg.camera.calibration_file and cfg.camera.backend == "picamera2" else None
    source_stop = threading.Event()
    errors = []

    class Data(app_callback_class):
        def __init__(self):
            super().__init__()
            self.use_frame = True

    def app_callback(pad, info, user_data):
        try:
            buffer = info.get_buffer()
            if buffer is None:
                return Gst.PadProbeReturn.OK
            identity = clock.lookup(buffer.pts)
            if identity is None:
                raise RuntimeError("Hailo çıkış karesi gerçek kamera zaman damgasıyla eşleşmiyor")
            fmt, width, height = get_caps_from_pad(pad)
            if fmt != "RGB" or (width, height) != (cfg.camera.width, cfg.camera.height):
                raise RuntimeError("Hailo çıkış görüntü boyutu/renk düzeni beklenenden farklı")
            image = get_numpy_from_buffer(buffer, fmt, width, height)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            roi = hailo.get_roi_from_buffer(buffer)
            detections = []
            for item in roi.get_objects_typed(hailo.HAILO_DETECTION):
                label = item.get_label()
                class_id = item.get_class_id()
                # TAPPAS HailoNMSDecode, model indeksine +1 uygular.
                expected = {1: "kirmizi_hedef", 2: "mavi_hedef"}
                if class_id not in expected or label != expected[class_id]:
                    raise RuntimeError(f"Hailo sınıf/etiket eşlemesi uyuşmuyor: {class_id}/{label}")
                b = item.get_bbox()
                detections.append(Detection(label, float(item.get_confidence()),
                                  (b.xmin(), b.ymin(), b.xmax(), b.ymax()), class_id))
            with state.lock:
                state.hailo_samples.append({"frame_id": identity[0], "captured_at": identity[1],
                    "result_at": time.monotonic(), "hailo_element_ms": inference_ms.pop(buffer.pts, None)})
            user_data.increment()
            mailbox.put(Frame(identity[0], identity[1], time.monotonic(), image, tuple(detections)))
        except Exception as e:
            errors.append(str(e))
            source_stop.set()
        return Gst.PadProbeReturn.OK

    class QuadDetectionApp(GStreamerDetectionApp):
        def get_pipeline_string(self):
            # AI hattı Hailo'nun kendi elemanlarıdır. Tracker hayalet tespitleri kullanılmaz.
            self.batch_size = 1
            self.video_width, self.video_height = cfg.camera.width, cfg.camera.height
            quote = lambda value: json.dumps(str(value), ensure_ascii=False)
            inference = INFERENCE_PIPELINE(
                hef_path=quote(self.hef_path), post_process_so=quote(self.post_process_so),
                post_function_name=self.post_function_name, batch_size=1,
                config_json=quote(self.labels_json),
                additional_params="nms-score-threshold=0.25 nms-iou-threshold=0.7 output-format-type=HAILO_FORMAT_TYPE_FLOAT32")
            wrapped = INFERENCE_PIPELINE_WRAPPER(inference, bypass_max_size_buffers=4)
            # appsrc önünde yalnız son kare tutulur. Bölünmüş Hailo dalları bağımsız düşürülmez.
            source = ("appsrc name=app_source is-live=true format=time block=false "
                      "leaky-type=downstream max-buffers=2 ! "
                      f"video/x-raw,format=RGB,width={cfg.camera.width},height={cfg.camera.height},"
                      f"framerate={cfg.camera.fps}/1,pixel-aspect-ratio=1/1")
            return f"{source} ! {wrapped} ! {USER_CALLBACK_PIPELINE()} ! fakesink sync=false qos=false"

        def run(self):
            identity = self.pipeline.get_by_name("identity_callback")
            infer = self.pipeline.get_by_name("inference_hailonet")
            if identity is None or infer is None:
                raise RuntimeError("Hailo NPU çıkarım elemanı veya callback bulunamadı")
            if Path(infer.get_property("hef-path")).resolve() != Path(cfg.hef_file).resolve():
                raise RuntimeError("Hailo elemanında yanlış HEF seçili")
            identity.get_static_pad("src").add_probe(Gst.PadProbeType.BUFFER, app_callback, self.user_data)
            def inference_probe(pad, info, started):
                buffer = info.get_buffer()
                if buffer is not None:
                    now = time.monotonic()
                    if started:
                        inference_started[buffer.pts] = now
                        while len(inference_started) > 128:
                            inference_started.popitem(last=False)
                    else:
                        began = inference_started.pop(buffer.pts, None)
                        if began is not None:
                            inference_ms[buffer.pts] = (now-began)*1000
                            while len(inference_ms) > 128:
                                inference_ms.popitem(last=False)
                return Gst.PadProbeReturn.OK
            infer.get_static_pad("sink").add_probe(Gst.PadProbeType.BUFFER, inference_probe, True)
            infer.get_static_pad("src").add_probe(Gst.PadProbeType.BUFFER, inference_probe, False)
            loop = GLib.MainLoop()
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()

            def bus_message(bus, message):
                if message.type == Gst.MessageType.ERROR:
                    error, debug = message.parse_error()
                    errors.append(f"Hailo/GStreamer: {error.message}")
                    source_stop.set()
                elif message.type == Gst.MessageType.EOS:
                    errors.append("Kamera/Hailo akışı sona erdi")
                    source_stop.set()

            bus.connect("message", bus_message)

            def capture():
                camera = None
                try:
                    if cfg.camera.backend == "v4l2-observe":
                        from .v4l2_camera import V4L2Camera
                        camera = V4L2Camera(cfg)
                    else:
                        camera = create_picamera(cfg)
                    camera.start()
                    # Lens hareketinin tamamlanması için ilk kareleri kontrol akışına verme.
                    focus_deadline = time.monotonic() + 3.0
                    source = self.pipeline.get_by_name("app_source")
                    source.set_property("caps", Gst.Caps.from_string(
                        f"video/x-raw,format=RGB,width={cfg.camera.width},height={cfg.camera.height},"
                        f"framerate={cfg.camera.fps}/1,pixel-aspect-ratio=1/1"))
                    model = camera.camera_properties.get("Model", "UNKNOWN")
                    while not stop.is_set() and not source_stop.is_set():
                        request = camera.capture_request()
                        try:
                            meta = request.get_metadata()
                            crop = tuple(meta.get("ScalerCrop", ()))
                            if cfg.camera.lens_position is not None:
                                actual_focus = meta.get("LensPosition")
                                if actual_focus is None or abs(actual_focus - cfg.camera.lens_position) > .001:
                                    if time.monotonic() < focus_deadline:
                                        continue
                                    raise RuntimeError("Kamera odağı kalibrasyonun sabit konumuyla uyuşmuyor")
                            if calibration:
                                calibration.verify_stream(cfg.camera.width, cfg.camera.height, model, crop)
                            stream_info = {"model": model, "width": cfg.camera.width,
                                "height": cfg.camera.height, "scaler_crop": crop,
                                "mirror": False, "timestamp": meta.get("TimestampSource", "SensorTimestamp"),
                                "backend": cfg.camera.backend, "identity": model, "device": cfg.camera.device,
                                "usb_vid_pid": cfg.camera.usb_vid_pid}
                            if cfg.camera.lens_position is not None:
                                stream_info.update(lens_position=cfg.camera.lens_position,
                                    focus_mode="manual", sensor_output_size=tuple(cfg.camera.sensor_output_size or ()))
                            if state.camera_info and state.camera_info != stream_info:
                                raise RuntimeError("Çalışma sırasında kamera modeli/ScalerCrop değişti")
                            state.camera_info = stream_info
                            sensor_ns = meta.get("SensorTimestamp")
                            if sensor_ns is None:
                                raise RuntimeError("Kamera SensorTimestamp sağlamıyor")
                            registered = clock.register(int(sensor_ns))
                            if registered is None:
                                continue
                            state.capture_count += 1
                            frame_bgr = request.make_array("main")
                            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                            buffer = Gst.Buffer.new_wrapped(rgb.tobytes())
                            buffer.pts = registered[0]
                            buffer.duration = Gst.SECOND // cfg.camera.fps
                            flow = source.emit("push-buffer", buffer)
                            if flow != Gst.FlowReturn.OK:
                                if stop.is_set() or source_stop.is_set():
                                    break
                                raise RuntimeError(f"Kamera → Hailo akış hatası: {flow}")
                        finally:
                            request.release()
                except Exception as e:
                    errors.append(str(e))
                    source_stop.set()
                finally:
                    if camera is not None:
                        camera.stop()
                        camera.close()

            def check_stop():
                if stop.is_set() or source_stop.is_set():
                    loop.quit()
                    return False
                return True

            timer = GLib.timeout_add(100, check_stop)
            self.pipeline.set_state(Gst.State.PLAYING)
            worker = threading.Thread(target=capture, name="camera-capture", daemon=True)
            worker.start()
            try:
                loop.run()
            finally:
                source_stop.set()
                self.pipeline.set_state(Gst.State.NULL)
                worker.join(timeout=3)
                bus.remove_signal_watch()
            if errors:
                raise RuntimeError(errors[0])

    argv = sys.argv
    sys.argv = ["safak-hailo", "--input", "rpi", "--hef-path", cfg.hef_file,
                "--labels-json", cfg.labels_file, "--arch", "hailo8l", "--frame-rate", str(cfg.camera.fps)]
    old_sigint = signal.getsignal(signal.SIGINT)
    try:
        app = QuadDetectionApp(app_callback, Data())
    finally:
        sys.argv = argv
        signal.signal(signal.SIGINT, old_sigint)
    state.backend = "HAILO · BAŞLATILIYOR"
    app.run()
