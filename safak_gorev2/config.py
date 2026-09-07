from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class CameraConfig:
    width: int = 1280
    height: int = 720
    fps: int = 30
    calibration_file: str | None = None
    sensor_output_size: tuple[int, int] | None = None
    lens_position: float | None = None
    # Body FRD: ileri, sağ, aşağı; uçuş referans merkezinden lens merkezine.
    offset_body_m: tuple[float, float, float] | None = None
    target_side_m: float = 2.0
    blue_label: str = "mavi_hedef"
    confidence_min: float = 0.65
    max_reprojection_px: float = 2.5
    max_plane_tilt_deg: float = 15.0
    min_quad_area_px: float = 900.0
    min_border_px: int = 12
    max_frame_occupancy: float = 0.88


@dataclasses.dataclass(frozen=True)
class ControlConfig:
    rate_hz: float = 20.0
    target_camera_height_m: float = 3.5
    height_tolerance_m: float = 0.25
    minimum_camera_height_m: float = 2.9
    minimum_intercept_relative_alt_m: float = 4.0
    acquire_s: float = 0.8
    acquire_frames: int = 6
    center_hold_s: float = 1.5
    release_hold_s: float = 3.0
    center_tolerance_m: float = 0.20
    descent_center_tolerance_m: float = 0.30
    release_horizontal_speed_mps: float = 0.20
    release_vertical_speed_mps: float = 0.12
    release_tilt_deg: float = 8.0
    control_tilt_deg: float = 15.0
    max_horizontal_speed_mps: float = 0.40
    max_descent_mps: float = 0.15
    max_climb_mps: float = 0.30
    max_accel_mps2: float = 0.35
    kp_xy: float = 0.35
    kd_xy: float = 0.30
    kp_height: float = 0.30
    frame_timeout_s: float = 0.30
    max_lock_frame_gap_s: float = 0.25
    telemetry_timeout_s: float = 0.6
    heartbeat_timeout_s: float = 1.5
    exposure_sync_tolerance_s: float = 0.10
    lost_target_abort_s: float = 1.0
    target_association_m: float = 0.8
    interaction_timeout_s: float = 90.0
    mode_timeout_s: float = 3.0
    return_timeout_s: float = 180.0
    return_speed_mps: float = 1.0
    return_arrival_m: float = 1.0


@dataclasses.dataclass(frozen=True)
class LinkConfig:
    device: str | None = None
    baud: int = 115200
    target_system: int = 1
    target_component: int = 1
    source_system: int = 245
    source_component: int = 191
    max_timesync_rtt_s: float = 0.05
    command_lease_s: float = 0.25


@dataclasses.dataclass(frozen=True)
class MissionConfig:
    return_mode: str = "land"
    # Manuel kalkış yalnız quad testinde açıkça seçilir; varsayılan AUTO TAKEOFF.
    takeoff_mode: str = "auto"
    # Son LAND'e geçişten önce başlangıç arama irtifasına çıkılır.
    direct_land_corridor_checked: bool | None = None
    max_land_distance_m: float = 200.0


@dataclasses.dataclass(frozen=True)
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    fps: int = 8
    jpeg_quality: int = 65
    width: int = 960


@dataclasses.dataclass(frozen=True)
class Config:
    camera: CameraConfig = dataclasses.field(default_factory=CameraConfig)
    control: ControlConfig = dataclasses.field(default_factory=ControlConfig)
    link: LinkConfig = dataclasses.field(default_factory=LinkConfig)
    mission: MissionConfig = dataclasses.field(default_factory=MissionConfig)
    web: WebConfig = dataclasses.field(default_factory=WebConfig)
    hef_file: str = "safak_v2_hailo_model/safak_v2.hef"
    hef_sha256: str = "b43dfac55acae45ce5db26301b6b7e9d63dc9be64e77a2f5069566068db45291"
    labels_file: str = "config/hailo_labels.json"
    runtime_dir: str = "runtime"

    @classmethod
    def load(cls, path: str | Path) -> Config:
        path = Path(path).resolve()
        data = json.loads(path.read_text())
        unknown = set(data) - {f.name for f in dataclasses.fields(cls)}
        if unknown:
            raise ValueError(f"Bilinmeyen yapılandırma alanı: {sorted(unknown)}")
        kinds = {"camera": CameraConfig, "control": ControlConfig, "link": LinkConfig,
                 "mission": MissionConfig, "web": WebConfig}
        for key, kind in kinds.items():
            if key in data:
                data[key] = kind(**data[key])
        config = cls(**data)
        # Dosya yolları config/ dosyasının bir üstündeki proje köküne göredir.
        root = path.parent.parent
        resolve = lambda p: str((root / p).resolve()) if p else None
        config = dataclasses.replace(
            config, hef_file=resolve(config.hef_file), labels_file=resolve(config.labels_file),
            runtime_dir=resolve(config.runtime_dir), camera=dataclasses.replace(
                config.camera, calibration_file=resolve(config.camera.calibration_file)))
        config.validate()
        return config

    def validate(self) -> None:
        if self.mission.return_mode not in ("land", "rtl"):
            raise ValueError("return_mode land veya rtl olmalı")
        if self.mission.takeoff_mode not in ("auto", "manual"):
            raise ValueError("takeoff_mode auto veya manual olmalı")
        for group in (self.camera, self.control, self.link, self.mission, self.web):
            for f in dataclasses.fields(group):
                value = getattr(group, f.name)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if f.name == "lens_position":
                        if not math.isfinite(value) or value < 0:
                            raise ValueError("lens_position sıfır veya pozitif ve sonlu olmalı")
                        continue
                    if not math.isfinite(value) or value <= 0:
                        raise ValueError(f"{f.name} pozitif ve sonlu olmalı")
        if not 0 < self.camera.confidence_min <= 1:
            raise ValueError("confidence_min 0–1 aralığında olmalı")
        if self.camera.sensor_output_size is not None:
            if len(self.camera.sensor_output_size) != 2 or any(
                type(v) is not int or v <= 0 for v in self.camera.sensor_output_size
            ):
                raise ValueError("sensor_output_size iki pozitif tam sayı olmalı")
        if not 0 < self.camera.max_frame_occupancy < 1:
            raise ValueError("max_frame_occupancy 0–1 aralığında olmalı")
        if self.camera.offset_body_m is not None:
            if len(self.camera.offset_body_m) != 3 or not all(
                isinstance(x, (int, float)) and math.isfinite(x) and abs(x) < 1
                for x in self.camera.offset_body_m
            ):
                raise ValueError("Kamera ofseti metre cinsinden üç ölçülmüş FRD değeri olmalı")
        c = self.control
        if c.target_camera_height_m - c.height_tolerance_m <= c.minimum_camera_height_m:
            raise ValueError("Bırakma yüksekliği alt sınırdan yeterince büyük olmalı")
        if c.max_lock_frame_gap_s > c.frame_timeout_s:
            raise ValueError("Kilit kare aralığı görüntü zaman aşımını aşamaz")
        if self.link.source_system == self.link.target_system:
            raise ValueError("Pi ve Pixhawk MAVLink sistem kimlikleri farklı olmalı")
        if self.web.fps > 30 or not 20 <= self.web.jpeg_quality <= 95:
            raise ValueError("Panel FPS/kalite aralığı geçersiz")

    def flight_missing(self) -> list[str]:
        missing = []
        if not self.camera.calibration_file or not Path(self.camera.calibration_file).is_file():
            missing.append("IMX219 kamera kalibrasyon dosyası")
        if self.camera.offset_body_m is None:
            missing.append("ölçülmüş kamera merkez ofseti")
        if self.mission.direct_land_corridor_checked is not True:
            missing.append("son LAND'e geçiş koridorunun açık olduğu bilgisi")
        return missing

    def verify_model(self) -> None:
        if hashlib.sha256(Path(self.hef_file).read_bytes()).hexdigest() != self.hef_sha256:
            raise ValueError("HEF dosyası yüklenen modelin SHA256 değeriyle uyuşmuyor")
        labels = json.loads(Path(self.labels_file).read_text())
        if labels.get("labels") != ["unlabeled", "kirmizi_hedef", "mavi_hedef"]:
            raise ValueError("TAPPAS etiket eşlemesi bu iki sınıflı modele uymuyor")
