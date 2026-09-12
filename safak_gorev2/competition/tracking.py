"""Kısa OpenCV tespit boşluklarını köprüleyen zaman eksenli hedef takibi.

Döner kanat için tasarlandı: hareket yönü varsayımı yoktur. Hedefe yaklaşma,
hedefi geçme veya uzaklaşırken "en iyi tespiti kilitleme" gibi sabit kanat
kabulleri yoktur; hover, geri gidiş, yana kayma ve yaw ile hedef etrafında
dönme aynı sabit hızlı kestirimle ele alınır.

GÜVENLİK SINIRI — tahmin uçuş kanıtı üretmez:

* Köprülenen aday `source='tracked'`, `color_verified=False`, `color_fill=None`
  ve `metric=None` kalır. Mevcut `corroborated` koşulu bunları duruş sonrası
  doğrulama, merkezleme ve bırakma yollarından zaten eler.
* Gerçek tespitin `bbox` alanına DOKUNULMAZ. PnP, köşe ölçümü ve kutu
  eşleştirmesi ham OpenCV ölçümünü görmeye devam eder; süzgeç sonucu ayrı
  `filtered_bbox` alanında yalnız etiket/teşhis için taşınır.

Maliyet: kare başına renk başına birkaç skaler işlem. Görüntü kopyalanmaz,
gri dönüşüm yapılmaz, korelasyon takipçisi (MOSSE/KCF/CSRT) çalıştırılmaz.
"""
from collections import deque
import math

CANDIDATE = 'CANDIDATE'
DETECTED = 'DETECTED'
TRACKED = 'TRACKED'
TEMP_LOST = 'TEMPORARILY_LOST'
LOST = 'LOST'


def box_center(box):
    return (box[0]+box[2])/2, (box[1]+box[3])/2


def box_size(box):
    return max(box[2]-box[0], 1e-6), max(box[3]-box[1], 1e-6)


def make_box(cx, cy, w, h):
    """Merkez/boyuttan normalize kutu; kadraj dışına taşan kutu üretilmez."""
    a, b, c, d = cx-w/2, cy-h/2, cx+w/2, cy+h/2
    a, b, c, d = max(0., a), max(0., b), min(1., c), min(1., d)
    if not (c-a > 1e-6 and d-b > 1e-6):
        return None
    return (a, b, c, d)


class Axis:
    """Sabit hızlı tek eksen Kalman süzgeci; ölçüm yalnız konumdur.

    Durum (konum, hız). Süreç gürültüsü ayrık beyaz ivme modelidir: kare içi
    ivme `process_accel` (kare genişliği/s²) mertebesinde varsayılır. Böylece
    yaw/pitch/roll kaynaklı hızlı kaymalar tek karede tahmine yansır, ölçüm
    gürültüsü ise `measurement_noise` ile bastırılır.
    """
    def __init__(self, position, measurement_noise, process_accel):
        self.r = measurement_noise*measurement_noise
        self.q = process_accel*process_accel
        self.x, self.v = position, 0.
        self.p00, self.p01, self.p11 = self.r, 0., self.q

    def predict(self, dt):
        self.x += self.v*dt
        t2 = dt*dt
        p00 = self.p00 + dt*(2*self.p01 + dt*self.p11) + self.q*t2*t2/4
        p01 = self.p01 + dt*self.p11 + self.q*t2*dt/2
        p11 = self.p11 + self.q*t2
        self.p00, self.p01, self.p11 = p00, p01, p11
        return self.x

    def correct(self, z):
        s = self.p00 + self.r
        k0, k1 = self.p00/s, self.p01/s
        residual = z - self.x
        self.x += k0*residual
        self.v += k1*residual
        p00, p01, p11 = self.p00, self.p01, self.p11
        self.p00, self.p01, self.p11 = p00*(1-k0), p01*(1-k0), p11 - k1*p01
        return self.x


class Track:
    """Tek renk için hedef geçmişi, süzgeç durumu ve durum makinesi."""
    def __init__(self, options, frame_id, at, box, fill):
        self.options = options
        self.history = deque(maxlen=options.history_size)
        cx, cy = box_center(box)
        self.x = Axis(cx, options.measurement_noise, options.process_accel)
        self.y = Axis(cy, options.measurement_noise, options.process_accel)
        self.w, self.h = box_size(box)
        self.hits = 0
        self.missed = 0
        self.state = CANDIDATE
        self.last_at = at
        self.last_real_at = at
        self.detected(frame_id, at, box, fill, fill)

    @property
    def confirmed(self):
        return self.hits >= self.options.confirmation_frames

    def predicted_center(self, dt):
        return self.x.predict(dt), self.y.predict(dt)

    def allowed_jump(self, dt):
        """Fiziksel olarak mümkün kare-içi kayma sınırı (normalize)."""
        return self.options.max_jump + self.options.max_jump_rate*max(0., dt)

    def detected(self, frame_id, at, box, fill, score):
        cx, cy = box_center(box)
        w, h = box_size(box)
        alpha = self.options.smoothing_alpha
        self.w += alpha*(w-self.w)
        self.h += alpha*(h-self.h)
        self.hits += 1
        self.missed = 0
        self.last_at = self.last_real_at = at
        self.score = score
        self.state = DETECTED if self.confirmed else CANDIDATE
        self.history.append({'frame_id': frame_id, 'captured_at': at, 'bbox': box,
                             'center': (cx, cy), 'area': w*h, 'fill': fill, 'score': score})
        return (self.x.correct(cx), self.y.correct(cy))

    def missed_frame(self, at):
        self.missed += 1
        self.last_at = at
        if self.missed > self.options.max_missed_frames:
            self.state = LOST
        elif self.confirmed and self.missed <= self.options.max_tracking_frames:
            self.state = TRACKED
        else:
            self.state = TEMP_LOST
        return self.state

    def filtered_box(self):
        return make_box(self.x.x, self.y.x, self.w, self.h)

    def mean_area(self):
        return sum(r['area'] for r in self.history)/len(self.history) if self.history else None


class TargetTracker:
    """Renk başına tek iz. Girdi ham OpenCV bölgeleri, çıktı saf karardır.

    `update()` görüntüye, OpenCV'ye veya uçuş durumuna erişmez; bu yüzden
    birim testleri kamera/araç olmadan koşar.
    """
    def __init__(self, options, colors):
        self.options = options
        self.colors = tuple(colors)
        self.tracks = {}
        self.transitions = []

    def update(self, frame_id, at, observations):
        """observations: {renk: ((bbox, fill), ...)} → {renk: sonuç sözlüğü}."""
        self.transitions = []
        return {color: self._color(color, frame_id, at, tuple(observations.get(color, ())))
                for color in self.colors}

    def _color(self, color, frame_id, at, observations):
        o = self.options
        track = self.tracks.get(color)
        previous = track.state if track else LOST
        dt = at-track.last_at if track else 0.
        if track is not None and (dt <= 0 or dt > o.max_gap_s):
            # Geri giden zaman veya uzun boru hattı boşluğu: kestirim
            # güvenilmez; iz bırakılır, yeniden doğrulama baştan istenir.
            self.tracks.pop(color, None)
            track, previous, dt = None, LOST, 0.
        predicted = track.predicted_center(dt) if track is not None else None
        scores = [self._score(track, predicted, dt, box, fill) for box, fill in observations]
        chosen = self._choose(track, scores)
        if track is not None and chosen is not None:
            box, fill = observations[chosen]
            track.detected(frame_id, at, box, fill, scores[chosen][0])
        elif track is not None:
            if track.missed_frame(at) == LOST:
                self.tracks.pop(color, None)
                track = None
        if track is None and observations:
            best = max(range(len(observations)), key=lambda i: observations[i][1])
            track = self.tracks[color] = Track(o, frame_id, at, *observations[best])
            chosen = best
            scores[best] = (observations[best][1], None, None)
        state = track.state if track is not None else LOST
        if state != previous:
            self.transitions.append((color, previous, state))
        bridge = track.filtered_box() if track is not None and state == TRACKED else None
        if track is not None and state == TRACKED and bridge is None:
            # Tahmin kadrajı terk etti: hedef gerçekten çıkmıştır, etiket tutulmaz.
            track.state = state = TEMP_LOST
            self.transitions.append((color, TRACKED, state))
        return {'state': state, 'chosen': chosen, 'scores': [s[0] for s in scores],
                'score': track.score if track is not None else None,
                'plausible': [s[1] for s in scores], 'bridge': bridge,
                'filtered': track.filtered_box() if track is not None and chosen is not None else None,
                'predicted': predicted, 'missed': track.missed if track is not None else None,
                'hits': track.hits if track is not None else 0,
                'history': len(track.history) if track is not None else 0}

    def _score(self, track, predicted, dt, box, fill):
        """(skor, ilişkilendirilebilir mi, merkez uzaklığı).

        İz yokken skor ham renk doluluğudur; sıralama bugünkü davranışla aynı
        kalır. İz varken süreklilik (tahmine yakınlık) ve alan tutarlılığı
        skora karışır, böylece birden çok aday arasından zamanla tutarlı olan
        seçilir.
        """
        if track is None or predicted is None:
            return (fill, None, None)
        cx, cy = box_center(box)
        distance = math.hypot(cx-predicted[0], cy-predicted[1])
        allowed = track.allowed_jump(dt)
        plausible = distance <= allowed
        position_term = max(0., 1.-distance/allowed) if allowed > 0 else 0.
        w, h = box_size(box)
        reference = track.mean_area()
        area = w*h
        area_term = (min(area, reference)/max(area, reference)
                     if reference and reference > 0 else 1.)
        weight = self.options.fill_weight
        return (weight*fill + (1-weight)*position_term*area_term, plausible, distance)

    def _choose(self, track, scores):
        """İzle ilişkilendirilecek gözlem; sıçrayan ölçüm süzgeci bozamaz."""
        if track is None:
            return None
        usable = [i for i, (score, plausible, _) in enumerate(scores)
                  if plausible and score >= self.options.min_score]
        if not usable:
            return None
        return max(usable, key=lambda i: scores[i][0])

    def forget(self, color=None):
        """Denetleyici hedefi bıraktığında izi de bırak."""
        if color is None:
            self.tracks.clear()
        else:
            self.tracks.pop(color, None)
