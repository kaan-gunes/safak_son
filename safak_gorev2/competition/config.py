from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import math
from pathlib import Path

from ..config import Config

COLORS = ('mavi', 'kirmizi')
PAYLOAD = {'mavi': 'kirmizi', 'kirmizi': 'mavi'}
SIDES = {'mavi': 2.0, 'kirmizi': 1.0}


@dataclass(frozen=True)
class Servo:
    channel: int | None = None
    release_pwm: int | None = None
    bench_verified: bool = False
    pulse_s: float | None = None
    neutral_pwm: int | None = None
    function: int = 0


@dataclass(frozen=True)
class ColorSearch:
    width: int = 640
    min_saturation: int = 70
    min_value: int = 35
    min_fill: float = 0.75
    max_aspect: float = 2.5
    match_iou: float = 0.5
    max_candidates: int = 6  # Renk başına tam çözünürlükte incelenecek bölge sınırı.

    def validate(self):
        if type(self.width) is not int or not 160 <= self.width <= 640:
            raise ValueError('Renk arama genişliği 160–640 olmalı')
        if type(self.max_candidates) is not int or not 1 <= self.max_candidates <= 12:
            raise ValueError('Renk aday sınırı 1–12 olmalı')
        for value in (self.min_saturation, self.min_value):
            if type(value) is not int or not 1 <= value <= 255:
                raise ValueError('Renk S/V eşiği 1–255 olmalı')
        for value in (self.min_fill, self.match_iou):
            if type(value) not in (int, float) or not math.isfinite(value) or not .5 <= value <= 1:
                raise ValueError('Renk doluluk/eşleme eşiği 0,5–1 olmalı')
        if type(self.max_aspect) not in (int, float) or not math.isfinite(self.max_aspect) or not 1 <= self.max_aspect <= 4:
            raise ValueError('Renk dörtgen oran sınırı 1–4 olmalı')


@dataclass(frozen=True)
class Tracking:
    """Zaman eksenli hedef takibi; kısa OpenCV boşluklarını köprüler.

    Varsayılan `enabled=False`: eski davranış hiç değişmez. Saha profilleri
    (`config/ana-gorev.json`, `config/hizli-gorev.json`) bunu açar; sahada
    tek alanı `false` yapmak anında eski akışa döner.
    """
    enabled: bool = False
    debug: bool = False  # Panel üstü teşhis metni ve durum geçişi terminal çıktısı.
    confirmation_frames: int = 2  # Köprülemeden önce istenen gerçek tespit sayısı.
    history_size: int = 8  # Tutulan son gerçek tespit kaydı.
    max_tracking_frames: int = 3  # Tahminle köprülenen en fazla ardışık kare.
    max_missed_frames: int = 8  # Bu kareden sonra iz tamamen bırakılır.
    max_gap_s: float = 0.25  # İki kare arası en büyük boşluk; aşılırsa iz sıfırlanır.
    smoothing_alpha: float = 0.45  # Kutu genişlik/yükseklik EMA ağırlığı.
    measurement_noise: float = 0.004  # Merkez ölçüm gürültüsü (normalize kare genişliği).
    process_accel: float = 8.0  # Beklenen kare içi ivme (kare genişliği/s²).
    max_jump: float = 0.12  # Sabit sıçrama payı (normalize).
    max_jump_rate: float = 3.0  # Süreye bağlı ek sıçrama payı (kare genişliği/s).
    min_score: float = 0.0  # Bu skorun altındaki aday izle ilişkilendirilmez.
    fill_weight: float = 0.6  # Skorda renk doluluğunun ağırlığı; kalanı süreklilik.
    bridge_search: bool = True  # Köprülenen kare tarama sayacını sıfırlamasın.

    def validate(self):
        for name in ('enabled', 'debug', 'bridge_search'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} açık/kapalı olmalı')
        for name in ('confirmation_frames', 'history_size', 'max_tracking_frames',
                     'max_missed_frames'):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 60:
                raise ValueError(f'{name} 1-60 arası tam sayı olmalı')
        if self.max_tracking_frames > self.max_missed_frames:
            raise ValueError('Köprüleme penceresi kayıp penceresinden uzun olamaz')
        for name in ('max_gap_s', 'smoothing_alpha', 'measurement_noise', 'process_accel',
                     'max_jump', 'max_jump_rate', 'fill_weight'):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} pozitif ve sonlu olmalı')
        for name in ('smoothing_alpha', 'fill_weight'):
            if getattr(self, name) > 1:
                raise ValueError(f'{name} 0-1 aralığında olmalı')
        if type(self.min_score) not in (int, float) or not math.isfinite(self.min_score) or not 0 <= self.min_score <= 1:
            raise ValueError('min_score 0-1 aralığında olmalı')
        if self.max_jump > 1 or self.measurement_noise > 1:
            raise ValueError('Sıçrama ve ölçüm gürültüsü normalize kare içinde kalmalı')


@dataclass(frozen=True)
class Options:
    strategy: str = 'center'
    actuator: str = 'simulated'
    camera_mount_yaw_deg: int | None = 0  # Yere bakan kamera: görüntü üstü burun=0, arka=180.
    color_search: ColorSearch = field(default_factory=ColorSearch)
    tracking: Tracking = field(default_factory=Tracking)
    vehicle_type: int | None = None  # MAV_TYPE: quad=2, hexa=13; fiziksel seçim gerekli.
    sortie_id: str | None = None  # Yeniden başlatmada AYNI kimlik; yeniden yükleyince yeni kimlik.
    mission_fingerprint: str | None = None
    search_start_seq: int | None = None
    search_end_seq: int | None = None
    route_reviewed: bool = False
    search_scope: str = 'field'  # field: saha kapıları; mission: TAKEOFF sonrası tüm waypointler.
    # Tarama bölümünün kaç kez uçulacağı. 1 = bugünkü davranış (tek tur).
    # Tur sonunda takılı yüklerden biri hâlâ duruyorsa search_start_seq'e dönülür.
    search_laps: int = 1
    # Kalkıştan (AUTO devralma anından) itibaren saniye. Süre dolunca yarım
    # kalan her iş bırakılıp LAND waypointine gidilir. None = sınır yok.
    mission_deadline_s: float | None = None
    # Bu andan sonra YENİ hedefe durulmaz; başlamış iş sürer. None = sınır yok.
    intercept_deadline_s: float | None = None
    center_search_speed_mps: float | None = None  # Yalnız ana AUTO oturumu; PARAM_SET yok.
    # Otopilot DO_CHANGE_SPEED'i kabul edip AUTO bacağı yeniden başlayınca
    # WPNAV_SPEED'e dönebiliyor. Ölçülen hız isteği bu payı aşarsa istek
    # yenilenir; aynı istek bu aralıktan sık tekrarlanmaz.
    search_speed_margin_mps: float = 1.0
    search_speed_retry_s: float = 2.0
    # Sıralı, sonlu yönlü geçiş kapıları: [[latA,lonA],[latB,lonB]].
    # A->B doğrultusunun negatif yanından pozitif yanına geçilir.
    entry_gates: tuple = ()
    finish_gate: tuple = ()
    flight_polygon: tuple = ()  # İzinli uçuş alanı; GPS lat/lon köşeleri.
    quick_frames: int = 3
    quick_hold_s: float = 0.10
    quick_iou: float = 0.25
    stop_speed_mps: float = 0.20
    stop_hold_s: float = 0.30
    stop_timeout_s: float = 5.0
    verify_timeout_s: float = 3.0
    quick_verify_s: float = 0.10
    quick_verify_frames: int = 3
    retry_delay_s: float = 5.0
    release_ack_timeout_s: float = 2.0
    payloads: tuple = COLORS  # Bu sortiede fiziksel olarak takılı yükler.
    servos: dict = field(default_factory=lambda: {c: Servo() for c in COLORS})

    @classmethod
    def load(cls, path):
        path = Path(path).resolve()
        data = json.loads(path.read_text())
        base = Config.load(path.parent / data.pop('base_config'))
        if base.camera.variant is None:
            raise ValueError('Yarışma profilinde açık kamera variant/backend/identity gerekli; fallback yok')
        data['servos'] = {c: Servo(**v) for c, v in data.get('servos', {}).items()}
        data['payloads'] = tuple(data.get('payloads', COLORS))
        data['color_search'] = ColorSearch(**data.get('color_search', {}))
        data['tracking'] = Tracking(**data.get('tracking', {}))
        options = cls(**data)
        options.validate()
        if options.strategy == 'center' and (base.control.acquire_frames < 6 or base.control.acquire_s < .5):
            raise ValueError('Ana doğrulama en az 6 bağımsız kare ve 0.5 s olmalı')
        if options.strategy == "quick":
            base = replace(base, camera=replace(base.camera, calibration_file=None))
        base = replace(base, runtime_dir=str(path.parent.parent / 'runtime' / 'competition' / (options.strategy + '-' + (base.camera.variant or 'legacy'))))
        return base, options

    def validate(self):
        self.color_search.validate()
        self.tracking.validate()
        if self.search_scope not in ('field', 'mission'):
            raise ValueError('Tarama kapsamı field veya mission olmalı')
        if self.center_search_speed_mps is not None and (self.strategy != 'center'
                or type(self.center_search_speed_mps) not in (int, float)
                or not math.isfinite(self.center_search_speed_mps)
                or not .5 <= self.center_search_speed_mps <= 8):
            # Üst sınır fren mesafesi/kadraj ayak izi analizinden geldi: 15 m'de
            # 5,8 m/s, 25 m'de 7,7 m/s hedefi frenden sonra kadrajda tutuyor.
            # Uygun değeri irtifaya göre kullanıcı seçer.
            raise ValueError('Geçici tarama hızı yalnız ana görevde 0,5–8 m/s olabilir')
        if self.camera_mount_yaw_deg is not None and (type(self.camera_mount_yaw_deg) is not int or self.camera_mount_yaw_deg not in (0, 180)):
            raise ValueError('Yere bakan kamera montajı 0 veya 180 derece olmalı')
        if self.strategy not in ('center', 'quick') or self.actuator not in ('simulated', 'servo'):
            raise ValueError('Strateji/aktüatör seçimi geçersiz')
        for name in ('mission_deadline_s', 'intercept_deadline_s'):
            value = getattr(self, name)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)
                                      or not 30 <= value <= 3600):
                raise ValueError(f'{name} 30-3600 saniye arası olmalı veya null')
        if (self.intercept_deadline_s is not None and self.mission_deadline_s is not None
                and self.intercept_deadline_s > self.mission_deadline_s):
            raise ValueError('intercept_deadline_s mission_deadline_s değerini aşamaz')
        if self.search_laps > 1 and self.mission_deadline_s is None:
            raise ValueError('Birden çok tarama turu için mission_deadline_s zorunlu')
        if type(self.search_laps) is not int or not 1 <= self.search_laps <= 10:
            raise ValueError('search_laps 1-10 arası tam sayı olmalı')
        if type(self.quick_frames) is not int or self.quick_frames < 1:
            raise ValueError('quick_frames pozitif tam sayı olmalı')
        if type(self.quick_verify_frames) is not int or self.quick_verify_frames < 1:
            raise ValueError('quick_verify_frames pozitif tam sayı olmalı')
        for name in ('search_speed_margin_mps', 'search_speed_retry_s',
                     'quick_hold_s', 'release_ack_timeout_s', 'quick_iou', 'stop_speed_mps',
                     'stop_hold_s', 'stop_timeout_s', 'verify_timeout_s', 'retry_delay_s', 'quick_verify_s'):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} pozitif ve sonlu olmalı')
        if self.quick_iou > 1 or set(self.servos) != set(COLORS):
            raise ValueError('İki yük için ayrı servo tanımı gerekli')
        if not self.payloads or len(self.payloads) != len(set(self.payloads)) or not set(self.payloads) <= set(COLORS):
            raise ValueError('Takılı yükler mavi/kırmızı listesinin boş olmayan alt kümesi olmalı')
        if self.stop_timeout_s <= self.stop_hold_s:
            raise ValueError('Durma zaman aşımı kararlılık süresinden uzun olmalı')
        if self.verify_timeout_s <= self.quick_verify_s:
            raise ValueError('Doğrulama zaman aşımı kısa doğrulama süresinden uzun olmalı')
        if self.vehicle_type not in (None, 2, 13):
            raise ValueError('Yalnız quad veya hexacopter desteklenir')
        for seq in (self.search_start_seq, self.search_end_seq):
            if seq is not None and (type(seq) is not int or seq < 1):
                raise ValueError('Tarama sıraları pozitif tam sayı olmalı')
        for servo in self.servos.values():
            if servo.function not in (0, 1, *range(51, 67)):
                raise ValueError('Servo işlevi motor/kontrol yüzeyi olamaz')
            if (servo.pulse_s is None) != (servo.neutral_pwm is None):
                raise ValueError('Süreli servo için pulse_s ve neutral_pwm birlikte gerekli')
            if servo.pulse_s is not None:
                if (type(servo.pulse_s) not in (int, float) or not math.isfinite(servo.pulse_s)
                        or not .05 <= servo.pulse_s <= 1 or servo.pulse_s >= self.release_ack_timeout_s
                        or type(servo.neutral_pwm) is not int or not 800 <= servo.neutral_pwm <= 2200):
                    raise ValueError('Servo darbe süresi veya nötr PWM geçersiz')
            if servo.channel is not None and (type(servo.channel) is not int or not 1 <= servo.channel <= 16):
                raise ValueError('Servo çıkışı 1–16 olmalı')
            if servo.release_pwm is not None and (type(servo.release_pwm) is not int or not 800 <= servo.release_pwm <= 2200):
                raise ValueError('Servo PWM değeri geçersiz')
        channels = [s.channel for s in self.servos.values() if s.channel is not None]
        if len(channels) != len(set(channels)):
            raise ValueError('İki yük aynı servo çıkışını kullanamaz')
        for gate in (*self.entry_gates, *((self.finish_gate,) if self.finish_gate else ())):
            if len(gate) != 2 or gate[0] == gate[1]:
                raise ValueError('Geçiş kapısı farklı iki GPS noktası olmalı')
            for p in gate:
                self._point(p)
        for p in self.flight_polygon:
            self._point(p)

    @staticmethod
    def _point(p):
        if (len(p) != 2 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in p)
                or abs(p[0]) > 90 or abs(p[1]) > 180):
            raise ValueError('Geçersiz GPS noktası')

    def missing(self, base):
        from ..camera_contract import capture_missing, metric_missing
        result = capture_missing(base.camera) + metric_missing(base.camera)
        if self.camera_mount_yaw_deg is None:
            result.append('ölçülmüş kamera montaj yönü')
        for key in ('vehicle_type', 'sortie_id', 'mission_fingerprint', 'search_start_seq', 'search_end_seq'):
            if not getattr(self, key):
                result.append(key)
        if self.route_reviewed is not True or (self.search_scope == 'field' and (
                not self.entry_gates or not self.finish_gate or len(self.flight_polygon) < 3)):
            result.append('sahada incelenmiş rota, giriş/bitiş kapıları ve uçuş poligonu')
        if self.search_start_seq and self.search_end_seq and self.search_start_seq > self.search_end_seq:
            result.append('tarama başlangıç/bitiş sırası')
        if base.mission.takeoff_mode != 'auto':
            result.append('yarışma profilinde AUTO TAKEOFF')
        if base.mission.direct_land_corridor_checked is not True:
            result.append('iki yük sonrası doğrudan LAND bölgesinin açık olduğu saha kontrolü')
        if self.strategy == 'center':
            if self.verify_timeout_s <= base.control.acquire_s:
                result.append('verify_timeout_s ilk hedef doğrulama süresinden uzun olmalı')
            if not base.camera.calibration_file or not Path(base.camera.calibration_file).is_file():
                result.append('kamera kalibrasyonu')
            if base.camera.offset_body_m is None:
                result.append('hexacopter üzerinde ölçülmüş kamera FRD ofseti')
        if self.actuator == 'servo':
            for color in self.payloads:
                s = self.servos[color]
                if s.channel is None or s.release_pwm is None or s.bench_verified is not True:
                    result.append(f'{color} yük için ölçülmüş kanal/PWM ve tezgâh doğrulaması')
        return result
