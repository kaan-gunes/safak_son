from dataclasses import dataclass, replace
import math
import cv2

from .geometry import MountedTargetGeometry
from ..types import Detection, Frame, Target
from .config import COLORS, SIDES


@dataclass(frozen=True)
class Candidate:
    color: str
    frame_id: int
    captured_at: float
    confidence: float
    bbox: tuple
    metric: Target | None = None


class DualVision:
    def __init__(self, cfg, calibration=None, mount_yaw_deg=0):
        self.cfg = cfg
        self.geometry = {c: MountedTargetGeometry(replace(cfg.camera, target_side_m=SIDES[c]), calibration,
                                                  mount_yaw_deg)
                         for c in COLORS} if calibration else {}

    def detect(self, frame, pose=None, strategy='center'):
        if strategy not in ('center', 'quick'):
            raise ValueError('Yalnız ana (center) ve hızlı (quick) görev destekleniyor')
        candidates, diagnostics = [], []
        for color in COLORS:
            ds = tuple(d for d in frame.detections if d.label == color + '_hedef'
                       and math.isfinite(d.confidence) and self.cfg.camera.confidence_min <= d.confidence <= 1
                       and len(d.bbox) == 4 and all(math.isfinite(v) and 0 <= v <= 1 for v in d.bbox)
                       and d.bbox[0] < d.bbox[2] and d.bbox[1] < d.bbox[3])
            if strategy == 'quick':
                # PnP/köşe/odak kalibrasyonu gerekmez; yalnız AI sınıfı ve geçerli kutu.
                candidates.extend(Candidate(color, frame.id, frame.captured_at, d.confidence, d.bbox) for d in ds)
            else:
                # Erken duruş AI kutusuyla tetiklenir; köşe/PnP yalnız sonraki doğrulamadır.
                # Geometri reddedilse de ham aday kaybolmamalı.
                targets = ()
                if pose is not None and color in self.geometry:
                    targets, detail = self.metric_targets(frame, pose, color, ds)
                    diagnostics.extend({'color': color, **d} for d in detail)
                for d in ds:
                    metric = next((t for t in targets if t.bbox == d.bbox and t.confidence == d.confidence), None)
                    candidates.append(Candidate(color, frame.id, frame.captured_at, d.confidence, d.bbox, metric))
        return tuple(candidates), diagnostics

    def metric_targets(self, frame, pose, color, ds):
        # Eski mavi geometriyi değiştirmeden kırmızı kanalı mavi konuma taşı.
        image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB) if color == 'kirmizi' else frame.image
        mapped = tuple(replace(d, label=self.cfg.camera.blue_label) for d in ds)
        adapted = replace(frame, image=image, detections=mapped)
        detail = []
        targets = self.geometry[color].detect(adapted, pose, detail)
        return targets, detail
