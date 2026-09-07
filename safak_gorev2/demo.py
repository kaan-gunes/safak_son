"""Görsel/karar akışı için sentetik demo. SITL veya fiziksel uçuş kanıtı değildir."""
from __future__ import annotations

import math
import threading
import time
from dataclasses import replace

import cv2
import numpy as np

from .geometry import CAMERA_TO_BODY, Calibration, TargetGeometry, body_to_ned
from .mavlink_io import validate_mission
from .types import Detection, Frame, MissionItem, Telemetry


def demo_calibration():
    return Calibration(1280, 720, np.array([[820., 0, 640.], [0, 820., 360.], [0, 0, 1.]]),
                       np.zeros(5), "SYNTHETIC", (0, 0, 1280, 720), 0.0)


class Demo:
    def __init__(self, runtime):
        self.runtime = runtime
        self.lock = threading.Lock()
        self.mode = "AUTO"
        self.seq = 0
        self.velocity = np.zeros(3)
        self.position = np.array([0., 0., 0.])
        self.actual_velocity = np.zeros(3)
        self.start = time.monotonic()
        self.frame_id = 0
        self.target = np.array([1., .6, 0.])
        self.cal = demo_calibration()
        self.geometry = TargetGeometry(runtime.cfg.camera, self.cal)
        runtime.geometry_override = self.geometry
        runtime.demo_sink = self.submit
        runtime.telemetry.autopilot_confirmed = True
        runtime.telemetry.params.update({"MIS_RESTART": 0, "GUID_TIMEOUT": 1, "FS_THR_ENABLE": 3,
            "FLTMODE_CH": 5, **{f"FLTMODE{i}": 3 if i == 6 else 5 for i in range(1, 7)}})
        runtime.telemetry.mission = validate_mission([
            MissionItem(0, 16, 0, 410000000, 290000000, 0),
            MissionItem(1, 22, 3, 0, 0, 6),
            MissionItem(2, 16, 3, 410000450, 290000000, 6),
            MissionItem(3, 21, 3, 410000000, 290000000, 0)])
        runtime.state.camera_info = {"model": "SYNTHETIC", "width": 1280, "height": 720,
                                     "scaler_crop": self.cal.scaler_crop, "mirror": False}

    def submit(self, actions):
        with self.lock:
            for a in actions:
                if a.kind == "velocity":
                    self.velocity = np.array(a.values)
                elif a.kind == "stop":
                    self.velocity[:] = 0
                elif a.kind == "mode":
                    self.mode = a.values[0]
                elif a.kind == "mission_current":
                    self.seq = a.values[0]

    def start_thread(self):
        thread = threading.Thread(target=self.run, daemon=True, name="synthetic-demo")
        thread.start()
        return thread

    def run(self):
        rt = self.runtime
        previous = time.monotonic()
        while not rt.stop.is_set():
            now = time.monotonic()
            elapsed, dt = now - self.start, min(.1, now - previous)
            previous = now
            armed = elapsed > 2
            with self.lock:
                if elapsed < 6:
                    self.position[2] = -min(6, max(0, elapsed - 2) * 1.5)
                    self.seq = 1 if armed else 0
                elif self.mode == "AUTO" and self.seq < 3:
                    self.seq = 2
                    self.position[2] = -6
                elif self.mode == "GUIDED":
                    self.actual_velocity += (self.velocity - self.actual_velocity) * min(1, dt * 3)
                    self.position += self.actual_velocity * dt
                elif self.mode == "AUTO" and self.seq == 3:
                    self.position[2] = min(0, self.position[2] + .7 * dt)
                if self.seq == 3 and self.position[2] >= -.05:
                    armed = False
                roll = .01 * math.sin(elapsed)
                pitch = .008 * math.cos(elapsed * .8)
                t = Telemetry(**{f"{name}_at": now for name in (
                    "heartbeat", "attitude", "position", "global", "gps", "ekf", "rc", "status",
                    "battery", "landed", "mission", "timesync")},
                    mode=self.mode, armed=armed, landed=2 if armed else 1, system_status=4,
                    roll=roll, pitch=pitch, yaw=0, north=self.position[0], east=self.position[1], down=self.position[2],
                    vn=self.actual_velocity[0], ve=self.actual_velocity[1], vd=self.actual_velocity[2],
                    lat=41 + math.degrees(self.position[0] / 6378137),
                    lon=29 + math.degrees(self.position[1] / (6378137 * math.cos(math.radians(41)))),
                    relative_alt_m=-self.position[2], gps_fix=3, satellites=16, hdop=.8,
                    ekf_flags=831, rc_slot=6, rc_selected_mode="AUTO", rc_healthy=True,
                    voltage=15.4, current=12.6, battery_percent=78, mission_seq=self.seq, firmware="4.6.3 · DEMO")
            with rt.telemetry.lock:
                rt.telemetry.value = t
                rt.telemetry.attitudes.append((now, t.roll, t.pitch, t.yaw))
                rt.telemetry.positions.append((now, t.north, t.east, t.down))
            image = np.full((720, 1280, 3), (48, 65, 54), np.uint8)
            for x in range(0, 1280, 80):
                cv2.line(image, (x, 0), (x, 720), (55, 72, 61), 1)
            for y in range(0, 720, 80):
                cv2.line(image, (0, y), (1280, y), (55, 72, 61), 1)
            detections = []
            if self.position[2] < -1:
                rotation = body_to_ned(roll, pitch, 0)
                center_camera = CAMERA_TO_BODY.T @ (rotation.T @ (self.target - self.position) - np.array(rt.cfg.camera.offset_body_m))
                # Hedefin yüzeyi yatay; IPPE nesne +Y kamera görüntüsünde yukarıya karşılık gelir.
                object_to_ned = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1.]])
                object_to_camera = CAMERA_TO_BODY.T @ rotation.T @ object_to_ned
                rvec, _ = cv2.Rodrigues(object_to_camera)
                projected, _ = cv2.projectPoints(self.geometry.object_points, rvec, center_camera,
                                                self.cal.matrix, self.cal.distortion)
                corners = projected.reshape(4, 2)
                if np.isfinite(corners).all() and center_camera[2] > 0:
                    cv2.fillConvexPoly(image, corners.astype(np.int32), (208, 77, 26))
                    box = (*corners.min(axis=0), *corners.max(axis=0))
                    box = tuple(np.clip(np.array(box) / [1280, 720, 1280, 720], 0, 1))
                    detections = [Detection("mavi_hedef", .94, box, 2)]
            self.frame_id += 1
            rt.mailbox.put(Frame(self.frame_id, now, now, image, tuple(detections), "SENTETİK DEMO"))
            rt.stop.wait(max(0, .05 - (time.monotonic() - now)))

