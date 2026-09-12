import time
from collections import deque

from ..controller import telemetry_problem
from ..mavlink_io import MavlinkLink
from ..types import Action
from .config import PAYLOAD
from ..camera_contract import metric_missing
from .route import area_allowed, mission_digest


class CompetitionLink(MavlinkLink):
    def __init__(self, cfg, store, allow_control, stop, options, ledger, connection=None):
        super().__init__(cfg, store, allow_control, stop, connection)
        self.options, self.ledger = options, ledger
        self.payload_status = ledger.statuses()
        self.pending = None
        self.servo_params = {}
        self.route_authorized = False
        self.pulse = None
        self.search_speed_status = None
        self.search_speed_sent_at = None
        self.search_speed_request_at = None
        self.fc_messages = deque(maxlen=30)
        # Uçuş başlamadan önce FC rotasını tek bir eski okumaya güvenmeden
        # yeniden indiririz. İki aynı tam okuma yarışma başlangıç kapısıdır.
        self.last_mission_refresh = -float('inf')
        self.mission_generation = 0
        self.mission_stable_reads = 0
        self.last_mission_digest = None
        self.mission_loaded_at = None
        # Süreli kırmızı servo yük takılmadan önce nötrde kararlı olmalı.
        # Bu kontrol yalnız başlangıç içindir; gerçek bırakma darbesini bozmaz.
        self.servo_outputs = {}
        self.servo_output_at = None
        self.servo_neutral_since = {}

    def control_fallback_mode(self):
        # Kumanda AUTO'da kalırken LOITER'a zorlamak, gaz kolu düşükse sert
        # alçalış üretiyor. Yarışma akışı yalnız onaylı AUTO rotasına döner.
        return 'AUTO'

    def _neutralize(self, now):
        pulse = self.pulse
        if pulse is None:
            return
        s = self.options.servos[pulse['color']]
        # Yalnız başlattığımız darbenin durdurulması; pilot devri/lease kaybında da gerekli.
        self._command(183, s.channel, s.neutral_pwm)
        self.pulse = None
        if self.pending is not None:
            p = self.pending
            p['release_ok'] = p['ack'] and p['output']
            p.update(at=now, ack=False, output=False, neutral=True)

    def _tick(self, now):
        if self.pulse is not None and now >= self.pulse['until']:
            self._neutralize(now)
        if self.pending is not None and now-self.pending['at'] > self.options.release_ack_timeout_s:
            self._neutralize(now)
            self._status(self.pending['color'], 'UNCERTAIN')
            self.pending = None
        # Mission Planner son anda LAND/waypoint yazarsa önceden alınmış rota
        # bellekte kalmasın. Yalnız yerde ve DISARM iken salt okunur yenileme.
        t = self.store.snapshot()
        if (self.allow_control and self.store.autopilot_confirmed and not t.armed
                and self.store.mission is not None and self.mission_count is None
                and self.mission_stable_reads < 2
                and now-self.last_mission_refresh >= 1.0):
            self.connection.mav.mission_request_list_send(
                self.cfg.link.target_system, self.cfg.link.target_component)
            self.last_mission_refresh = now

    def _shutdown_outputs(self):
        self._neutralize(time.monotonic())

    def quick_release_stopped(self, t):
        return (t.horizontal_speed <= self.options.stop_speed_mps
                and abs(t.vd) <= self.cfg.control.release_vertical_speed_mps
                and t.tilt_deg <= self.cfg.control.release_tilt_deg
                and t.relative_alt_m >= self.cfg.control.minimum_intercept_relative_alt_m)

    def snapshot_status(self):
        with self.store.lock:
            return dict(self.payload_status)

    def snapshot_search_speed_status(self):
        with self.store.lock:
            return {'status': self.search_speed_status, 'request_at': self.search_speed_request_at}

    def snapshot_fc_messages(self):
        with self.store.lock:
            return list(self.fc_messages)

    def _initial_requests(self):
        super()._initial_requests()
        if self.options.actuator == 'servo':
            self._command(511, 36, 100000)
            for color in self.options.payloads:
                s = self.options.servos[color]
                if s.channel is not None:
                    for suffix in ('FUNCTION','MIN','MAX'):
                        name = f'SERVO{s.channel}_{suffix}'
                        self.connection.mav.param_request_read_send(self.cfg.link.target_system,
                            self.cfg.link.target_component, name.encode(), -1)

    def hardware_problem(self):
        speed = self.store.params.get('WPNAV_SPEED')
        # Kullanıcı kararı 11 Eylül: saha süresi nedeniyle iki görevde de 1000 cm/s.
        # Bu hızda fren yaklaşık 3 s sürer; duruş/doğrulama mantığı buna göre
        # hedefi yeniden yakalar. Üst sınır FC preflight'ıyla aynı: 1000 cm/s.
        speed_limit = 1000
        if speed is not None and not 0 < speed <= speed_limit:
            return f'WPNAV_SPEED {self.options.strategy} görev için 1–{speed_limit} cm/s aralığında olmalı'
        if self.options.actuator == 'simulated':
            return None
        for color in self.options.payloads:
            s = self.options.servos[color]
            if not s.bench_verified or s.channel is None or s.release_pwm is None:
                return color+' servo fiziksel eşlemesi eksik'
            prefix = f'SERVO{s.channel}_'
            if self.servo_params.get(prefix+'FUNCTION') != s.function:
                return prefix+f'FUNCTION={s.function} okunmalı; tezgâh eşlemesi değişmiş'
            lower, upper = self.servo_params.get(prefix+'MIN'), self.servo_params.get(prefix+'MAX')
            if lower is None or upper is None or not lower <= s.release_pwm <= upper:
                return color+' PWM otopilot çıkış sınırlarında doğrulanmadı'
            if s.neutral_pwm is not None and not lower <= s.neutral_pwm <= upper:
                return color+' nötr PWM otopilot sınırlarında değil'
        return None

    def startup_servo_problem(self, now=None):
        """Yük takılmadan/ARM'dan önce süreli servonun nötr çıkışını doğrula."""
        if self.options.actuator != 'servo':
            return None
        now = time.monotonic() if now is None else now
        for color in self.options.payloads:
            s = self.options.servos[color]
            if s.neutral_pwm is None:
                continue
            output = self.servo_outputs.get(s.channel)
            if output is None or self.servo_output_at is None or now-self.servo_output_at > .5:
                return color+' servo çıkışı okunuyor; yükü takmayın'
            if abs(output-s.neutral_pwm) > 25:
                return f'{color} servo nötr değil: {output} us; yükü takmayın'
            since = self.servo_neutral_since.get(color)
            if since is None or now-since < 2.0:
                return color+' servo nötr kararlılığı bekleniyor; yükü takmayın'
        return None

    def _safe(self, now, mode):
        t = self.store.snapshot()
        m = self.store.mission
        return (not metric_missing(self.cfg.camera) and self.allow_control and not self.failure and not self.store.pilot_override
                and self.store.preflight_problem() is None and telemetry_problem(t, now, self.cfg) is None
                and t.mode == mode and t.rc_selected_mode == 'AUTO'
                and m is not None and mission_digest(m) == self.options.mission_fingerprint
                and area_allowed(self.options, (t.lat,t.lon)))

    def _status(self, color, status):
        self.ledger.update(color, status)
        with self.store.lock:
            self.payload_status[color] = status

    def ingest(self, msg, now):
        previous_mission = self.store.mission
        super().ingest(msg, now)
        if msg.get_srcSystem() != self.cfg.link.target_system or msg.get_srcComponent() != self.cfg.link.target_component:
            return
        kind = msg.get_type()
        if self.store.mission is not None and self.store.mission is not previous_mission:
            digest = mission_digest(self.store.mission)
            self.mission_stable_reads = self.mission_stable_reads+1 if digest == self.last_mission_digest else 1
            self.last_mission_digest = digest
            self.mission_generation += 1
            self.mission_loaded_at = now
            self.last_mission_refresh = now
        if kind == 'STATUSTEXT' and self.options.strategy == 'center':
            with self.store.lock:
                self.fc_messages.append({'at': now, 'severity': msg.severity, 'text': msg.text})
        if (kind == 'COMMAND_ACK' and msg.command == 178 and self.search_speed_sent_at is not None
                and now > self.search_speed_sent_at):
            with self.store.lock:
                self.search_speed_status = 'ACCEPTED' if msg.result == 0 else 'REJECTED'
            self.search_speed_sent_at = None
        if kind == 'HEARTBEAT':
            self.store.autopilot_confirmed = msg.autopilot == 3 and msg.type == self.options.vehicle_type
        if kind == 'MISSION_ITEM_INT' and msg.seq > 0:
            if (msg.command not in (16,22,21) or getattr(msg,'autocontinue',1) != 1
                    or any(getattr(msg,f'param{i}',0) != 0 for i in range(1,4))
                    or getattr(msg,'param4',0) not in ((-1,0,1) if msg.command == 21 else (0,))):
                self.failure = 'Yarışma rotasında desteklenmeyen komut/parametre var'
                self.store.update(link_error=self.failure)
        if kind == 'PARAM_VALUE':
            name = msg.param_id.decode().rstrip('\0') if isinstance(msg.param_id, bytes) else msg.param_id.rstrip('\0')
            allowed = {f'SERVO{self.options.servos[color].channel}_{suffix}'
                       for color in self.options.payloads
                       for suffix in ('FUNCTION','MIN','MAX')}
            if name in allowed:
                self.servo_params[name] = msg.param_value
        if kind == 'SERVO_OUTPUT_RAW' and msg.port == 0:
            self.servo_output_at = now
            for color in self.options.payloads:
                s = self.options.servos[color]
                if s.channel is None:
                    continue
                output = getattr(msg, f'servo{s.channel}_raw', None)
                self.servo_outputs[s.channel] = output
                if s.neutral_pwm is not None and output is not None and abs(output-s.neutral_pwm) <= 25:
                    self.servo_neutral_since.setdefault(color, now)
                else:
                    self.servo_neutral_since.pop(color, None)
        pending = self.pending
        if pending is None:
            return
        if now-pending['at'] > self.options.release_ack_timeout_s:
            self._neutralize(now)
            self._status(pending['color'], 'UNCERTAIN')
            self.pending = None
            return
        if kind == 'COMMAND_ACK' and msg.command == 183 and now > pending['at']:
            if (getattr(msg,'target_system',0) not in (0,self.cfg.link.source_system)
                    or getattr(msg,'target_component',0) not in (0,self.cfg.link.source_component)):
                return
            if msg.result == 0:
                pending['ack'] = True
            elif msg.result != 5:  # IN_PROGRESS: nihai cevap beklenir.
                self._neutralize(now)
                self._status(pending['color'], 'REJECTED')
                self.pending = None
                return
        if kind == 'SERVO_OUTPUT_RAW' and msg.port == 0 and now > pending['at']:
            s = self.options.servos[pending['color']]
            expected = s.neutral_pwm if pending.get('neutral') else s.release_pwm
            pending['output'] = getattr(msg, f'servo{s.channel}_raw', None) == expected
        if pending['ack'] and pending['output']:
            if self.pulse is not None:
                return
            self._status(pending['color'], 'ACK_ACCEPTED' if pending.get('release_ok', True) else 'UNCERTAIN')
            self.pending = None

    def _perform(self, now, actions):
        if not self.allow_control:
            return
        for a in actions:
            if a.kind == 'search_speed':
                speed, slot = a.values
                t = self.store.snapshot()
                if (self.options.strategy == 'center' and self.options.center_search_speed_mps is not None
                        and speed == self.options.center_search_speed_mps and slot == t.rc_slot
                        and self._safe(now, 'AUTO') and self.hardware_problem() is None
                        and t.mission_seq is not None
                        and self.options.search_start_seq is not None
                        and self.options.search_start_seq <= t.mission_seq <= self.options.search_end_seq):
                    with self.store.lock:
                        self.search_speed_status = 'PENDING'
                        self.search_speed_request_at = now
                    self.search_speed_sent_at = now
                    self._command(178, 1, speed, -1, 0)
                else:
                    with self.store.lock:
                        self.search_speed_status = 'REJECTED'
                        self.search_speed_request_at = now
            elif a.kind == 'resume':
                seq, fingerprint = a.values
                m = self.store.mission
                if (self._safe(now, 'GUIDED') and self.owned and self.store.snapshot().rc_slot == self.claim_slot
                        and m and fingerprint == mission_digest(m)
                        and self.options.search_start_seq <= seq <= self.options.search_end_seq
                        and m.current_command(seq) == 16):
                    self.connection.mav.mission_set_current_send(self.cfg.link.target_system,
                        self.cfg.link.target_component, seq)
            elif a.kind == 'payload':
                color, target, fid, captured_at, mode = a.values
                if color in self.payload_status or self.pending is not None:
                    continue
                t = self.store.snapshot()
                permitted = (color in self.options.payloads and PAYLOAD.get(target) == color and self.route_authorized
                    and self._safe(now, mode) and self.hardware_problem() is None
                    and t.mission_seq is not None
                    and self.options.search_start_seq <= t.mission_seq <= self.options.search_end_seq
                    and 0 <= now-captured_at <= self.cfg.control.frame_timeout_s
                    and mode == 'GUIDED' and self.options.strategy in ('center', 'quick') and self.owned
                    and t.rc_slot == self.claim_slot
                    and (self.options.strategy != 'quick' or self.quick_release_stopped(t)))
                if not permitted:
                    with self.store.lock:
                        self.payload_status[color] = 'BLOCKED'
                    continue
                if not self.ledger.reserve(color, {'target':target, 'frame_id':fid, 'captured_at':captured_at,
                                                  'wall_time':time.time(), 'actuator':self.options.actuator}):
                    with self.store.lock:
                        self.payload_status.update(self.ledger.statuses())
                    continue
                with self.store.lock:
                    self.payload_status[color] = 'RESERVED'
                # Disk yazılırken kare/telemetri eskimiş olabilir; lease tekrar kontrol edilir.
                sent_at = time.monotonic()
                if (sent_at-now > self.cfg.link.command_lease_s or not self._safe(sent_at, mode)
                        or not 0 <= sent_at-captured_at <= self.cfg.control.frame_timeout_s
                        or (self.options.strategy == 'quick' and not self.quick_release_stopped(self.store.snapshot()))):
                    self._status(color, 'BLOCKED')
                    continue
                if self.options.actuator == 'simulated':
                    self._status(color, 'SIMULATED')
                    continue
                s = self.options.servos[color]
                self.pending = {'color':color, 'at':sent_at, 'ack':False, 'output':False}
                if s.pulse_s is not None:
                    self.pulse = {'color':color, 'until':sent_at+s.pulse_s}
                with self.store.lock:
                    self.payload_status[color] = 'SENT'
                self._command(183, s.channel, s.release_pwm)
            else:
                super()._perform(now, (a,))
                if ((a.kind == 'mode' and a.values == ('GUIDED', 'AUTO') or a.kind == 'stop') and self.owned
                        and self.options.strategy in ('center', 'quick') and self._safe(now, 'AUTO')):
                    # Mod cevabı gelirken karar döngüsü dursa bile GUIDED boş hızla kalmasın.
                    # Üst sınıf göndericisi yalnız GUIDED'de uygular; süre aşımında AUTO'ya bırakır.
                    self.velocity = (0., 0., 0.)
                    self.velocity_until = now + self.cfg.link.command_lease_s
