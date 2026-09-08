import time

from ..controller import telemetry_problem
from ..mavlink_io import MavlinkLink
from ..types import Action
from .config import PAYLOAD
from .route import inside, mission_digest


class CompetitionLink(MavlinkLink):
    def __init__(self, cfg, store, allow_control, stop, options, ledger, connection=None):
        super().__init__(cfg, store, allow_control, stop, connection)
        self.options, self.ledger = options, ledger
        self.payload_status = ledger.statuses()
        self.pending = None
        self.servo_params = {}
        self.route_authorized = False

    def quick_release_stopped(self, t):
        return (t.horizontal_speed <= self.options.stop_speed_mps
                and abs(t.vd) <= self.cfg.control.release_vertical_speed_mps
                and t.tilt_deg <= self.cfg.control.release_tilt_deg
                and t.relative_alt_m >= self.cfg.control.minimum_intercept_relative_alt_m)

    def snapshot_status(self):
        with self.store.lock:
            return dict(self.payload_status)

    def _initial_requests(self):
        super()._initial_requests()
        if self.options.actuator == 'servo':
            self._command(511, 36, 100000)
            for s in self.options.servos.values():
                if s.channel is not None:
                    for suffix in ('FUNCTION','MIN','MAX'):
                        name = f'SERVO{s.channel}_{suffix}'
                        self.connection.mav.param_request_read_send(self.cfg.link.target_system,
                            self.cfg.link.target_component, name.encode(), -1)

    def hardware_problem(self):
        if self.options.actuator == 'simulated':
            return None
        for color, s in self.options.servos.items():
            if not s.bench_verified or s.channel is None or s.release_pwm is None:
                return color+' servo fiziksel eşlemesi eksik'
            prefix = f'SERVO{s.channel}_'
            if self.servo_params.get(prefix+'FUNCTION') != 0:
                return prefix+'FUNCTION=0 okunmalı; motor/atanmış çıkışa yazılmaz'
            lower, upper = self.servo_params.get(prefix+'MIN'), self.servo_params.get(prefix+'MAX')
            if lower is None or upper is None or not lower <= s.release_pwm <= upper:
                return color+' PWM otopilot çıkış sınırlarında doğrulanmadı'
        return None

    def _safe(self, now, mode):
        t = self.store.snapshot()
        m = self.store.mission
        return (self.allow_control and not self.failure and not self.store.pilot_override
                and self.store.preflight_problem() is None and telemetry_problem(t, now, self.cfg) is None
                and t.mode == mode and t.rc_selected_mode == 'AUTO'
                and m is not None and mission_digest(m) == self.options.mission_fingerprint
                and inside(self.options.flight_polygon, (t.lat,t.lon)))

    def _status(self, color, status):
        self.ledger.update(color, status)
        with self.store.lock:
            self.payload_status[color] = status

    def ingest(self, msg, now):
        super().ingest(msg, now)
        if msg.get_srcSystem() != self.cfg.link.target_system or msg.get_srcComponent() != self.cfg.link.target_component:
            return
        kind = msg.get_type()
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
            allowed = {f'SERVO{s.channel}_{suffix}' for s in self.options.servos.values()
                       for suffix in ('FUNCTION','MIN','MAX')}
            if name in allowed:
                self.servo_params[name] = msg.param_value
        pending = self.pending
        if pending is None:
            return
        if now-pending['at'] > self.options.release_ack_timeout_s:
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
                self._status(pending['color'], 'REJECTED')
                self.pending = None
                return
        if kind == 'SERVO_OUTPUT_RAW' and msg.port == 0 and now > pending['at']:
            s = self.options.servos[pending['color']]
            pending['output'] = getattr(msg, f'servo{s.channel}_raw', None) == s.release_pwm
        if pending['ack'] and pending['output']:
            self._status(pending['color'], 'ACK_ACCEPTED')
            self.pending = None

    def _perform(self, now, actions):
        if not self.allow_control:
            return
        for a in actions:
            if a.kind == 'resume':
                seq, fingerprint = a.values
                m = self.store.mission
                if (self._safe(now, 'GUIDED') and self.owned and self.store.snapshot().rc_slot == self.claim_slot
                        and m and fingerprint == m.fingerprint
                        and self.options.search_start_seq <= seq <= self.options.search_end_seq
                        and m.current_command(seq) == 16):
                    self.connection.mav.mission_set_current_send(self.cfg.link.target_system,
                        self.cfg.link.target_component, seq)
            elif a.kind == 'payload':
                color, target, fid, captured_at, mode = a.values
                if color in self.payload_status or self.pending is not None:
                    continue
                t = self.store.snapshot()
                permitted = (PAYLOAD.get(target) == color and self.route_authorized
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
                with self.store.lock:
                    self.payload_status[color] = 'SENT'
                self._command(183, s.channel, s.release_pwm)
            else:
                super()._perform(now, (a,))
                if ((a.kind == 'mode' and a.values == ('GUIDED', 'AUTO') or a.kind == 'stop') and self.owned
                        and self.options.strategy in ('center', 'quick') and self._safe(now, 'AUTO')):
                    # Mod cevabı gelirken karar döngüsü dursa bile GUIDED boş hızla kalmasın.
                    # Üst sınıf göndericisi yalnız GUIDED'de uygular; süre aşımında LOITER'a bırakır.
                    self.velocity = (0., 0., 0.)
                    self.velocity_until = now + self.cfg.link.command_lease_s
