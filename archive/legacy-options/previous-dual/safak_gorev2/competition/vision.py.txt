from dataclasses import dataclass, replace
import math
import cv2

from ..geometry import TargetGeometry
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
    def __init__(self, cfg, calibration=None):
        self.cfg = cfg
        self.geometry = {c: TargetGeometry(replace(cfg.camera, target_side_m=SIDES[c]), calibration)
                         for c in COLORS} if calibration else {}

    def detect(self, frame, pose=None, strategy='center'):
        candidates, diagnostics = [], []
        for color in COLORS:
            ds = tuple(d for d in frame.detections if d.label == color + '_hedef'
                       and math.isfinite(d.confidence) and self.cfg.camera.confidence_min <= d.confidence <= 1
                       and len(d.bbox) == 4 and all(math.isfinite(v) and 0 <= v <= 1 for v in d.bbox)
                       and d.bbox[0] < d.bbox[2] and d.bbox[1] < d.bbox[3])
            if strategy == 'sighting':
                # PnP/köşe/odak kalibrasyonu gerekmez; yalnız AI sınıfı ve geçerli kutu.
                candidates.extend(Candidate(color, frame.id, frame.captured_at, d.confidence, d.bbox) for d in ds)
            elif pose is not None and color in self.geometry:
                # Eski mavi geometriyi değiştirmeden kırmızı kanalı mavi konuma taşı.
                image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB) if color == 'kirmizi' else frame.image
                mapped = tuple(replace(d, label=self.cfg.camera.blue_label) for d in ds)
                adapted = replace(frame, image=image, detections=mapped)
                detail = []
                targets = self.geometry[color].detect(adapted, pose, detail)
                candidates.extend(Candidate(color, t.frame_id, t.captured_at, t.confidence, t.bbox, t) for t in targets)
                diagnostics.extend({'color': color, **d} for d in detail)
        return tuple(candidates), diagnostics
