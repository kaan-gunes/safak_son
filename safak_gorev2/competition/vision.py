from dataclasses import asdict, dataclass, replace
import time
import cv2

from .color_search import ColorDetector
from .geometry import MountedTargetGeometry
from ..types import Detection, Frame, Target
from .config import COLORS, SIDES, Tracking
from .tracking import CANDIDATE, TRACKED, TargetTracker


@dataclass(frozen=True)
class Candidate:
    color: str
    frame_id: int
    captured_at: float
    confidence: float | None
    bbox: tuple
    metric: Target | None = None
    source: str = 'opencv'
    color_verified: bool = False
    color_fill: float | None = None
    # Aşağıdaki alanlar yalnız zaman eksenli takibin teşhis/etiket çıktısıdır.
    # Uçuş kararı üretmezler; `bbox` her zaman ham OpenCV ölçümüdür.
    track_state: str | None = None
    score: float | None = None
    missed: int | None = None
    filtered_bbox: tuple | None = None

    @property
    def corroborated(self):
        # Eski ad API/kayıt uyumluluğu için korunur; OpenCV dörtgeninin kendi
        # renk/doluluk doğrulaması artık tek görüntü kanıtıdır. Köprülenen
        # tahmin `source='tracked'` olduğu için burada asla doğru dönmez.
        return self.source == 'opencv' and self.color_verified is True

    @property
    def bridged(self):
        """Bu karede gerçek tespit yok; kutu kısa süreli kestirimdir."""
        return self.source == 'tracked'

    @property
    def rank(self):
        # Takip kapalıyken skor None'dır ve sıralama bugünkü ile aynı kalır.
        return (self.corroborated, self.color_fill or 0. if self.score is None else self.score)


class DualVision:
    def __init__(self, cfg, calibration=None, mount_yaw_deg=0, color_options=None, tracking=None):
        self.cfg = cfg
        self.opencv_ms = 0.
        self.tracking_ms = 0.
        self.colors = ColorDetector(cfg.camera, color_options)
        self.tracking = tracking or Tracking()
        self.tracking.validate()
        self.tracker = TargetTracker(self.tracking, COLORS) if self.tracking.enabled else None
        self.geometry = {c: MountedTargetGeometry(replace(cfg.camera, target_side_m=SIDES[c]), calibration,
                                                  mount_yaw_deg)
                         for c in COLORS} if calibration else {}

    def detect(self, frame, pose=None, strategy='center'):
        if strategy not in ('center', 'quick'):
            raise ValueError('Yalnız ana (center) ve hızlı (quick) görev destekleniyor')
        candidates, diagnostics = [], []
        started = time.monotonic()
        # Kenara değen hedef aday olur; metrik ölçümün kendi kenar payı
        # (corner_screen/min_border_px) ana görevde ayrıca uygulanır.
        regions = self.colors.detect(frame.image, border_px=0)
        self.opencv_ms = (time.monotonic()-started)*1000
        for color in COLORS:
            available = tuple(r for r in regions if r.color == color)
            # PnP eski ve test edilmiş geometri hattını kullanır; iç skor
            # OpenCV bölgesinin ölçülen renk doluluğudur.
            measured = tuple(Detection(color+'_hedef', r.fill, r.bbox) for r in available)
            targets = ()
            if strategy == 'center' and pose is not None and color in self.geometry and measured:
                started = time.monotonic()
                targets, detail = self.metric_targets(frame, pose, color, measured)
                self.opencv_ms += (time.monotonic()-started)*1000
                diagnostics.extend({'color': color, **d} for d in detail)
            for region in available:
                metric = next((t for t in targets if t.bbox == region.bbox), None)
                candidates.append(Candidate(color, frame.id, frame.captured_at, None, region.bbox, metric,
                                            'opencv', True, region.fill))
        if self.tracker is None:
            return tuple(candidates), diagnostics
        started = time.monotonic()
        candidates = self.track(frame, candidates)
        self.tracking_ms = (time.monotonic()-started)*1000
        return candidates, diagnostics

    def track(self, frame, candidates):
        """Gerçek adayları etiketle, kısa boşlukları köprülenmiş adayla doldur.

        Gerçek adayın hiçbir uçuş alanı (bbox, metric, color_fill, source,
        color_verified) değişmez; yalnız teşhis alanları eklenir.
        """
        order = {color: [i for i, x in enumerate(candidates) if x.color == color] for color in COLORS}
        results = self.tracker.update(frame.id, frame.captured_at,
            {color: tuple((candidates[i].bbox, candidates[i].color_fill) for i in order[color])
             for color in COLORS})
        for color, result in results.items():
            for position, index in enumerate(order[color]):
                associated = result['chosen'] == position
                candidates[index] = replace(candidates[index],
                    track_state=result['state'] if associated else CANDIDATE,
                    score=result['scores'][position],
                    missed=result['missed'] if associated else None,
                    filtered_bbox=result['filtered'] if associated else None)
            if result['bridge'] is not None:
                candidates.append(Candidate(color, frame.id, frame.captured_at, None,
                    result['bridge'], None, 'tracked', False, None, TRACKED,
                    result['score'], result['missed'], result['bridge']))
        if self.tracking.debug:
            for color, previous, state in self.tracker.transitions:
                print(f'[TAKIP] kare {frame.id} {color}: {previous} -> {state}', flush=True)
        return tuple(candidates)

    def metric_targets(self, frame, pose, color, ds):
        # Eski mavi geometriyi değiştirmeden kırmızı kanalı mavi konuma taşı.
        image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB) if color == 'kirmizi' else frame.image
        mapped = tuple(replace(d, label=self.cfg.camera.blue_label) for d in ds)
        adapted = replace(frame, image=image, detections=mapped)
        detail = []
        targets = self.geometry[color].detect(adapted, pose, detail)
        return targets, [dict(d, pose=asdict(pose)) for d in detail]
