from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .config import CameraConfig
from .types import Detection, Frame, PoseSample, Target


# Kamera optik eksenleri: sağ, görüntüde aşağı, lensin baktığı yön.
# Kullanıcı montajı: görüntü üstü burun, lens yere bakıyor. Aynalama YOK.
CAMERA_TO_BODY = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])


def body_to_ned(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return np.array([
        [cp * cy, sr * sp * cy - cr * sy, cr * sp * cy + sr * sy],
        [cp * sy, sr * sp * sy + cr * cy, cr * sp * sy - sr * cy],
        [-sp, sr * cp, cr * cp],
    ])


def heading_velocity(north: float, east: float, yaw: float) -> tuple[float, float]:
    return (math.cos(yaw) * north + math.sin(yaw) * east,
            -math.sin(yaw) * north + math.cos(yaw) * east)


def local_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
    """Kısa saha mesafelerinde WGS84 küresel yaklaşımı; N/E metre."""
    r = 6378137.0
    return (math.radians(lat2 - lat1) * r,
            math.radians(lon2 - lon1) * r * math.cos(math.radians((lat1 + lat2) / 2)))


@dataclass(frozen=True)
class Calibration:
    width: int
    height: int
    matrix: np.ndarray
    distortion: np.ndarray
    camera_model: str
    scaler_crop: tuple[int, int, int, int]
    rms_px: float

    @classmethod
    def load(cls, path: str | Path) -> Calibration:
        d = json.loads(Path(path).read_text())
        if d.get("schema") != 1 or d.get("projection") != "pinhole":
            raise ValueError("Desteklenmeyen kamera kalibrasyonu")
        k = np.asarray(d["camera_matrix"], dtype=np.float64)
        distortion = np.asarray(d["distortion"], dtype=np.float64).reshape(-1)
        if k.shape != (3, 3) or not np.isfinite(k).all() or not np.isfinite(distortion).all():
            raise ValueError("Kalibrasyon matrisi geçersiz")
        if k[0, 0] <= 0 or k[1, 1] <= 0 or not np.allclose(k[2], [0, 0, 1]):
            raise ValueError("Kamera odak/matris değerleri geçersiz")
        if len(distortion) not in (4, 5, 8, 12, 14):
            raise ValueError("Distorsiyon katsayı sayısı desteklenmiyor")
        if not 0 <= d["rms_px"] <= 1.0:
            raise ValueError("Kalibrasyon RMS hatası 1 pikseli aşıyor veya geçersiz")
        return cls(int(d["width"]), int(d["height"]), k, distortion,
                   d["camera_model"], tuple(d["scaler_crop"]), float(d["rms_px"]))

    def verify_stream(self, width: int, height: int, model: str, crop: tuple) -> None:
        if (width, height) != (self.width, self.height):
            raise ValueError("Görüntü boyutu kalibrasyonla uyuşmuyor; sessiz ölçekleme yapılmaz")
        if model != self.camera_model or tuple(crop) != self.scaler_crop:
            raise ValueError("Kamera modeli/ScalerCrop kalibrasyondan farklı")


def order_corners(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=np.float64).reshape(4, 2)
    center = p.mean(axis=0)
    angles = np.arctan2(p[:, 1] - center[1], p[:, 0] - center[0])
    p = p[np.argsort(angles)]
    # Pozitif görüntü alanı: TL, TR, BR, BL. Kare dönükken başlangıç köşesi önemsizdir.
    start = int(np.argmin(p.sum(axis=1)))
    return np.roll(p, -start, axis=0)


def bbox_iou(a: tuple, b: tuple) -> float:
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0., x2 - x1) * max(0., y2 - y1)
    total = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / total if total > 0 else 0.


def quad_candidates(image: np.ndarray, detection: Detection, cfg: CameraConfig) -> list[np.ndarray]:
    """Yalnız AI'nin mavi ROI'sinde adaptif renk kontrastı + kenar/geometri kontrolü."""
    h, w = image.shape[:2]
    box = np.array(detection.bbox) * [w, h, w, h]
    x1, y1, x2, y2 = box
    if not np.isfinite(box).all() or x2 <= x1 or y2 <= y1:
        return []
    pad = max(8, int(0.1 * max(x2 - x1, y2 - y1)))
    left, top = max(0, int(x1) - pad), max(0, int(y1) - pad)
    right, bottom = min(w, int(x2) + pad + 1), min(h, int(y2) + pad + 1)
    roi = image[top:bottom, left:right]
    if roi.size == 0:
        return []
    blur = cv2.GaussianBlur(roi, (5, 5), 0)
    blue, green, red = cv2.split(blur.astype(np.float32))
    # Beyaz denge/gölge için mutlak HSV aralığı kullanılmaz.
    excess = (blue - np.maximum(red, green)) / np.maximum(blue + green + red, 16.)
    salience = np.uint8(np.clip((excess + 1) * 127.5, 0, 255))
    _, color_mask = cv2.threshold(salience, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    color_mask[excess < 0.015] = 0
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    median = float(np.median(gray))
    edges = cv2.Canny(gray, max(10, int(median * 0.5)), max(30, int(median * 1.3)))
    kernel = np.ones((3, 3), np.uint8)
    masks = (cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel),
             cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel))
    found = []
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < cfg.min_quad_area_px or area < 0.40 * (x2 - x1) * (y2 - y1):
                continue
            quad = cv2.approxPolyDP(contour, 0.025 * cv2.arcLength(contour, True), True)
            if len(quad) != 4 or not cv2.isContourConvex(quad):
                continue
            q_local = order_corners(quad)
            interior = np.zeros(gray.shape, np.uint8)
            cv2.fillConvexPoly(interior, q_local.astype(np.int32), 255)
            interior = cv2.erode(interior, np.ones((7, 7), np.uint8))
            values = excess[interior > 0]
            if len(values) < 100 or np.median(values) < 0.025:
                continue
            q = q_local + [left, top]
            qbox = (q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max())
            if bbox_iou(tuple(box), qbox) < 0.55:
                continue
            if any(np.linalg.norm(q - other, axis=1).mean() < 5 for other in found):
                continue
            found.append(q)
    return sorted(found, key=lambda q: cv2.contourArea(q.astype(np.float32)), reverse=True)[:4]


def corner_screen(corners: np.ndarray, width: int, height: int, cfg: CameraConfig):
    """Mevcut sınır/doluluk koşulları; PnP veya görev kabulü değildir."""
    if not np.isfinite(corners).all():
        return None, ('nonfinite_corners',)
    reasons = []
    if (corners[:, 0].min() < cfg.min_border_px or corners[:, 1].min() < cfg.min_border_px
        or corners[:, 0].max() > width - cfg.min_border_px
        or corners[:, 1].max() > height - cfg.min_border_px):
        reasons.append('border')
    occupancy = float(max(np.ptp(corners[:, 0]) / width, np.ptp(corners[:, 1]) / height))
    if occupancy > cfg.max_frame_occupancy:
        reasons.append('occupancy')
    return occupancy, tuple(reasons)


class TargetGeometry:
    def __init__(self, cfg: CameraConfig, calibration: Calibration):
        self.cfg, self.calibration = cfg, calibration
        s = cfg.target_side_m / 2
        self.object_points = np.array([[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]], np.float64)
        if cfg.offset_body_m is None:
            raise ValueError("Metrik merkezleme için kamera ofseti eksik")
        self.offset = np.array(cfg.offset_body_m, np.float64)

    def from_corners(self, frame: Frame, detection: Detection, corners: np.ndarray,
                     pose: PoseSample) -> Target | None:
        cfg, cal = self.cfg, self.calibration
        h, w = frame.image.shape[:2]
        if (w, h) != (cal.width, cal.height):
            return None
        corners = order_corners(corners)
        occupancy, rejected = corner_screen(corners, w, h, cfg)
        if rejected:
            return None
        rotation = body_to_ned(pose.roll, pose.pitch, pose.yaw)
        camera_to_ned = rotation @ CAMERA_TO_BODY
        solutions = cv2.solvePnPGeneric(self.object_points, corners, cal.matrix, cal.distortion,
                                        flags=cv2.SOLVEPNP_IPPE_SQUARE)
        candidates = list(zip(solutions[1], solutions[2]))
        # Tam karşıdan bakışta IPPE'nin Rodrigues çözümü sayısal olarak tekilleşebilir.
        # Planar homografiyle başlayan ITERATIVE çözüm de aynı fiziksel/reprojeksiyon
        # denetimlerinden geçer; sadece düşük hata üretmesi yeterli sayılmaz.
        success, iterative_r, iterative_t = cv2.solvePnP(
            self.object_points, corners, cal.matrix, cal.distortion, flags=cv2.SOLVEPNP_ITERATIVE)
        if success:
            candidates.append((iterative_r, iterative_t))
        acceptable = []
        for rvec, tvec in candidates:
            t = tvec.reshape(3)
            if not np.isfinite(t).all() or t[2] <= 0 or not np.isfinite(rvec).all():
                continue
            object_to_camera, _ = cv2.Rodrigues(rvec)
            depths = (object_to_camera @ self.object_points.T + t[:, None])[2]
            if np.min(depths) <= 0:
                continue
            normal = camera_to_ned @ object_to_camera[:, 2]
            tilt = math.degrees(math.acos(np.clip(abs(normal[2]), 0, 1)))
            projected, _ = cv2.projectPoints(self.object_points, rvec, tvec, cal.matrix, cal.distortion)
            error = float(np.sqrt(np.mean(np.sum((projected.reshape(4, 2) - corners) ** 2, axis=1))))
            camera_vector_ned = camera_to_ned @ t
            if tilt > cfg.max_plane_tilt_deg or error > cfg.max_reprojection_px or camera_vector_ned[2] <= 0:
                continue
            acceptable.append((error, t, camera_vector_ned))
        if not acceptable:
            return None
        acceptable.sort(key=lambda x: x[0])
        error, t, camera_vector_ned = acceptable[0]
        for other in acceptable[1:]:
            if other[0] - error < 0.5 and np.linalg.norm(other[1] - t) > 0.25:
                return None  # Planar poz belirsizliği bırakmaya taşınmaz.
        position = np.array([pose.north, pose.east, pose.down]) + rotation @ self.offset + camera_vector_ned
        return Target(frame.id, frame.captured_at, detection.confidence,
                      *map(float, position), float(camera_vector_ned[2]), error,
                      tuple(tuple(map(float, p)) for p in corners), detection.bbox, float(occupancy))

    def detect(self, frame: Frame, pose: PoseSample, diagnostics: list | None = None) -> tuple[Target, ...]:
        targets = []
        for index, d in enumerate(frame.detections):
            detail = {"index": index, "confidence": d.confidence, "reasons": [], "accepted": False}
            if diagnostics is not None:
                diagnostics.append(detail)
            if d.label != self.cfg.blue_label:
                detail["reasons"].append("class")
            elif not math.isfinite(d.confidence) or d.confidence < self.cfg.confidence_min:
                detail["reasons"].append("score")
            if (d.label != self.cfg.blue_label or not math.isfinite(d.confidence)
                or d.confidence < self.cfg.confidence_min):
                continue
            quads = quad_candidates(frame.image, d, self.cfg)
            if not quads:
                detail["reasons"].append("no_corners")
            for q in quads:
                target = self.from_corners(frame, d, q, pose)
                if target is not None:
                    targets.append(target)
                    detail["accepted"] = True
                    detail["reasons"] = []
                    break
                _, reasons = corner_screen(q, frame.image.shape[1], frame.image.shape[0], self.cfg)
                detail["reasons"].extend(reasons or ("metric_geometry",))
            detail["reasons"] = list(dict.fromkeys(detail["reasons"]))
        return tuple(targets)
