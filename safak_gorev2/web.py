from __future__ import annotations

import time
import json
from dataclasses import asdict

import cv2
from flask import Flask, Response, jsonify, render_template

from .config import Config
from .controller import telemetry_problem
from .mavlink_io import TelemetryStore
from .shared import SharedState, finite_json


def create_app(cfg: Config, state: SharedState, telemetry: TelemetryStore) -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.get("/")
    def index():
        return render_template("index.html", video_fps=cfg.web.fps)

    @app.get("/api/status")
    def status():
        now = time.monotonic()
        t = telemetry.snapshot()
        with state.lock:
            fps = ((len(state.frame_times) - 1) / (state.frame_times[-1] - state.frame_times[0])
                   if len(state.frame_times) > 1 and state.frame_times[-1] > state.frame_times[0] else None)
            ages = {"heartbeat": now - t.heartbeat_at, "attitude": now - t.attitude_at,
                    "position": now - t.position_at, "battery": now - t.battery_at,
                    "global": now - t.global_at, "ekf": now - t.ekf_at, "mission": now - t.mission_at,
                    "gps": now - t.gps_at, "rc": now - t.rc_at, "frame": now - state.frame_at}
            data = {"mode": state.mode, "backend": state.backend, "uptime_s": now - state.started,
                    "telemetry": asdict(t), "ages_s": ages, "vision_fps": fps,
                    "decision": asdict(state.decision), "geometry_reason": state.geometry_reason,
                    "pipeline_error": state.pipeline_error, "release": state.release,
                    "events": list(state.events)[:20], "camera": state.camera_info,
                    "vision": {"frame_id": state.frame_id, "frame_at": state.frame_at,
                               "detections": [asdict(d) for d in state.detections],
                               "targets": [asdict(tg) for tg in state.vision_snapshot()[2]],
                               "diagnostics": state.diagnostics,
                               "confidence_required": cfg.camera.confidence_min},
                    "mission": {"count": len(telemetry.mission.items), "land_seq": telemetry.mission.land_seq,
                                "takeoff_seq": telemetry.mission.takeoff_seq,
                                "items": [asdict(item) for item in telemetry.mission.items]}
                        if telemetry.mission else None,
                    "takeoff_mode": cfg.mission.takeoff_mode,
                    "return_mode": cfg.mission.return_mode,
                    "preflight": telemetry.preflight_problem(),
                    "height_target_m": cfg.control.target_camera_height_m}
        return jsonify(finite_json(data))

    @app.get("/frame.jpg")
    def frame():
        with state.jpeg_condition:
            if state.jpeg is None:
                return Response(status=204)
            jpeg, frame_at, frame_id = state.jpeg, state.jpeg_frame_at, state.jpeg_id
        response = Response(jpeg, mimetype="image/jpeg")
        response.headers["X-Frame-Id"] = str(frame_id)
        response.headers["X-Frame-Age-Ms"] = str(round(max(0, time.monotonic() - frame_at) * 1000))
        return response

    @app.get("/healthz")
    def health():
        now = time.monotonic()
        with state.lock:
            frame_ready = (state.backend == "HAILO" and state.frame_id is not None
                           and 0 <= now - state.frame_at <= cfg.control.frame_timeout_s)
        ready = (state.mode == "flight" and frame_ready
                 and not (cfg.flight_missing() or telemetry.preflight_problem()
                          or telemetry_problem(telemetry.snapshot(), now, cfg) or state.pipeline_error)
                 and state.decision.state not in {"ABORTED", "PILOT_CONTROL", "DONE", "STARTING"})
        return jsonify({"service": "safak-gorev2", "panel": "ok", "mode": state.mode,
                        "flight_ready": ready})

    @app.get("/calibration/frame.png")
    def calibration_frame():
        # Aynı fiziksel kameranın ölçeklenmemiş ve etiketsiz karesi.
        # Gözlem dışında büyük PNG kodlama işi açılmaz.
        with state.lock:
            frame, info = state.calibration_frame, state.camera_info
            if state.mode != "observe":
                return Response(status=403)
            if frame is None or not info or state.pipeline_error:
                return Response(status=503)
            age = time.monotonic() - frame.captured_at
            if not 0 <= age <= cfg.control.frame_timeout_s:
                return Response(status=503)
        ok, encoded = cv2.imencode(".png", frame.image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        if not ok:
            return Response(status=503)
        response = Response(encoded.tobytes(), mimetype="image/png")
        response.headers["X-Frame-Id"] = str(frame.id)
        response.headers["X-Frame-Age-Ms"] = str(round((time.monotonic() - frame.captured_at) * 1000))
        response.headers["X-Camera-Meta"] = json.dumps(info, separators=(",", ":"))
        response.headers["X-Detections"] = json.dumps(
            finite_json([asdict(d) for d in frame.detections]), separators=(",", ":"))
        response.headers["X-Frame-Backend"] = frame.backend
        response.headers["X-Stream-Id"] = str(state.started)
        return response

    return app
