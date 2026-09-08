from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import hashlib
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


@dataclass(frozen=True)
class Options:
    strategy: str = 'center'
    actuator: str = 'simulated'
    camera_mount_yaw_deg: int = 0  # Yere bakan kamera: görüntü üstü burun=0, arka=180.
    vehicle_type: int | None = None  # MAV_TYPE: quad=2, hexa=13; fiziksel seçim gerekli.
    sortie_id: str | None = None  # Yeniden başlatmada AYNI kimlik; yeniden yükleyince yeni kimlik.
    mission_fingerprint: str | None = None
    search_start_seq: int | None = None
    search_end_seq: int | None = None
    route_reviewed: bool = False
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
    servos: dict = field(default_factory=lambda: {c: Servo() for c in COLORS})

    @classmethod
    def load(cls, path):
        path = Path(path).resolve()
        data = json.loads(path.read_text())
        base = Config.load(path.parent / data.pop('base_config'))
        data['servos'] = {c: Servo(**v) for c, v in data.get('servos', {}).items()}
        options = cls(**data)
        options.validate()
        # Pi'deki yeniden adlandırmayı koru; Mac'teki eş hash'li özgün dosyayı da okuyabil.
        if not Path(base.hef_file).is_file():
            alternate = Path(base.hef_file).with_name('best.hef')
            if alternate.is_file() and hashlib.sha256(alternate.read_bytes()).hexdigest() == base.hef_sha256:
                base = replace(base, hef_file=str(alternate))
        if options.strategy == "quick":
            base = replace(base, camera=replace(base.camera, calibration_file=None))
        base = replace(base, runtime_dir=str(path.parent.parent / 'runtime' / 'competition' / options.strategy))
        return base, options

    def validate(self):
        if type(self.camera_mount_yaw_deg) is not int or self.camera_mount_yaw_deg not in (0, 180):
            raise ValueError('Yere bakan kamera montajı 0 veya 180 derece olmalı')
        if self.strategy not in ('center', 'quick') or self.actuator not in ('simulated', 'servo'):
            raise ValueError('Strateji/aktüatör seçimi geçersiz')
        if type(self.quick_frames) is not int or self.quick_frames < 1:
            raise ValueError('quick_frames pozitif tam sayı olmalı')
        if type(self.quick_verify_frames) is not int or self.quick_verify_frames < 1:
            raise ValueError('quick_verify_frames pozitif tam sayı olmalı')
        for name in ('quick_hold_s', 'release_ack_timeout_s', 'quick_iou', 'stop_speed_mps',
                     'stop_hold_s', 'stop_timeout_s', 'verify_timeout_s', 'retry_delay_s', 'quick_verify_s'):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} pozitif ve sonlu olmalı')
        if self.quick_iou > 1 or set(self.servos) != set(COLORS):
            raise ValueError('İki yük için ayrı servo tanımı gerekli')
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
        result = []
        for key in ('vehicle_type', 'sortie_id', 'mission_fingerprint', 'search_start_seq', 'search_end_seq'):
            if not getattr(self, key):
                result.append(key)
        if self.route_reviewed is not True or not self.entry_gates or not self.finish_gate or len(self.flight_polygon) < 3:
            result.append('sahada incelenmiş rota, giriş/bitiş kapıları ve uçuş poligonu')
        if self.search_start_seq and self.search_end_seq and self.search_start_seq > self.search_end_seq:
            result.append('tarama başlangıç/bitiş sırası')
        if base.mission.takeoff_mode != 'auto':
            result.append('yarışma profilinde AUTO TAKEOFF')
        if self.strategy == 'center':
            if self.verify_timeout_s <= base.control.acquire_s:
                result.append('verify_timeout_s ilk hedef doğrulama süresinden uzun olmalı')
            if not base.camera.calibration_file or not Path(base.camera.calibration_file).is_file():
                result.append('kamera kalibrasyonu')
            if base.camera.offset_body_m is None:
                result.append('hexacopter üzerinde ölçülmüş kamera FRD ofseti')
        if self.actuator == 'servo':
            for color, s in self.servos.items():
                if s.channel is None or s.release_pwm is None or s.bench_verified is not True:
                    result.append(f'{color} yük için ölçülmüş kanal/PWM ve tezgâh doğrulaması')
        return result
