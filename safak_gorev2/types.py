from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    # Orijinal, aynalanmamış görüntüde normalize xyxy.
    bbox: tuple[float, float, float, float]
    class_id: int | None = None


@dataclass(frozen=True)
class Frame:
    id: int
    captured_at: float
    received_at: float
    image: Any
    detections: tuple[Detection, ...]
    backend: str = "HAILO"


@dataclass(frozen=True)
class PoseSample:
    at: float
    roll: float
    pitch: float
    yaw: float
    north: float
    east: float
    down: float


@dataclass(frozen=True)
class Target:
    frame_id: int
    captured_at: float
    confidence: float
    north: float
    east: float
    ground_down: float
    camera_height_m: float
    reprojection_px: float
    corners: tuple[tuple[float, float], ...]
    bbox: tuple[float, float, float, float]
    occupancy: float


@dataclass(frozen=True)
class Telemetry:
    heartbeat_at: float = -math.inf
    attitude_at: float = -math.inf
    position_at: float = -math.inf
    global_at: float = -math.inf
    gps_at: float = -math.inf
    ekf_at: float = -math.inf
    rc_at: float = -math.inf
    status_at: float = -math.inf
    battery_at: float = -math.inf
    landed_at: float = -math.inf
    mission_at: float = -math.inf
    timesync_at: float = -math.inf
    mode: str = "UNKNOWN"
    armed: bool = False
    landed: int = 0
    system_status: int = 0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    north: float = 0.0
    east: float = 0.0
    down: float = 0.0
    vn: float = 0.0
    ve: float = 0.0
    vd: float = 0.0
    lat: float | None = None
    lon: float | None = None
    relative_alt_m: float | None = None
    gps_fix: int | None = None
    satellites: int | None = None
    hdop: float | None = None
    ekf_flags: int = 0
    rc_slot: int | None = None
    rc_selected_mode: str | None = None
    rc_healthy: bool = False
    voltage: float | None = None
    current: float | None = None
    battery_percent: int | None = None
    mission_seq: int | None = None
    firmware: str | None = None
    rebooted: bool = False
    link_error: str | None = None

    @property
    def horizontal_speed(self) -> float:
        return math.hypot(self.vn, self.ve)

    @property
    def tilt_deg(self) -> float:
        return math.degrees(math.acos(max(-1, min(1, math.cos(self.roll) * math.cos(self.pitch)))))


@dataclass(frozen=True)
class MissionItem:
    seq: int
    command: int
    frame: int
    x: int
    y: int
    z: float


@dataclass(frozen=True)
class MissionPlan:
    items: tuple[MissionItem, ...]
    takeoff_seq: int | None
    land_seq: int
    land_lat: float
    land_lon: float
    fingerprint: str

    def current_command(self, seq: int | None) -> int | None:
        if seq is None or seq < 0 or seq >= len(self.items):
            return None
        return self.items[seq].command


@dataclass(frozen=True)
class Action:
    kind: str
    values: tuple = ()


@dataclass(frozen=True)
class Decision:
    state: str
    reason: str
    actions: tuple[Action, ...] = ()
    lock_s: float = 0.0
    lock_required_s: float = 0.0
    error_m: float | None = None
    camera_height_m: float | None = None
