from dataclasses import replace
import math

from ..controller import Controller, ContinuousHold, telemetry_problem
from ..geometry import bbox_iou
from ..types import Action, Decision
from .config import COLORS, PAYLOAD
from .route import RouteProgress, inside, mission_digest


class DualController:
    """AUTO rota + iki bağımsız yük. Eski Controller yalnız merkezleme alt yordamıdır."""
    def __init__(self, cfg, options):
        self.cfg, self.options = cfg, options
        self.route = RouteProgress(options)
        self.state, self.reason = 'WAIT_AUTO', 'Yerde başlatma ve AUTO kalkış bekleniyor'
        self.saw_disarmed = False
        self.started = False
        self.rc_slot = None
        self.child = None
        self.selected = None
        self.resume_seq = None
        self.return_alt = None
        self.entered = 0.
        self.last_step = None
        self.done = set()
        self.requested = set()
        self.holds = {c: ContinuousHold(cfg.control.max_lock_frame_gap_s) for c in COLORS}
        self.boxes = {}
        self.last_frame = None
        self.climb_hold = ContinuousHold(cfg.control.telemetry_timeout_s)

    def decision(self, *actions, reason=None):
        return Decision(self.state, reason or self.reason, tuple(actions))

    def transition(self, state, now, reason):
        self.state, self.entered, self.reason = state, now, reason

    def reset_holds(self):
        for h in self.holds.values():
            h.reset()
        self.boxes.clear()

    def abort(self, now, t, reason, pilot=False):
        self.transition('PILOT_CONTROL' if pilot else 'ABORTED', now, reason)
        self.reset_holds()
        actions = [Action('revoke')]
        if (not pilot and self.child is not None and t.mode == 'GUIDED' and t.rc_healthy
                and t.rc_slot == self.rc_slot and t.system_status == 4
                and 0 <= now-t.heartbeat_at <= self.cfg.control.heartbeat_timeout_s):
            actions = [Action('stop'), Action('mode', ('LOITER', 'GUIDED')), Action('revoke')]
        return self.decision(*actions)

    def step(self, now, t, candidates, frame_id, frame_at, mission, problem=None, release_status=None):
        statuses = release_status or {}
        dt = min(.1, max(.001, now-self.last_step)) if self.last_step is not None else .05
        gap = self.last_step is not None and now-self.last_step > self.cfg.link.command_lease_s
        self.last_step = now
        if self.state in ('DONE', 'INCOMPLETE', 'ABORTED', 'PILOT_CONTROL'):
            return self.decision()
        if not t.armed and t.landed == 1 and 0 <= now-t.heartbeat_at < self.cfg.control.heartbeat_timeout_s:
            if self.started:
                complete = len(self.done) == 2 and self.route.finished
                self.transition('DONE' if complete else 'INCOMPLETE', now,
                    'İniş görüldü; iki yük komutu ve bitiş geçişi kaydedildi' if complete else
                    'İniş görüldü; iki yük komutu veya bitiş geçişi eksik')
                return self.decision(Action('revoke'))
            self.saw_disarmed = True
            self.reset_holds()
            return self.decision(reason='DISARM görüldü; AUTO kalkış bekleniyor')
        if self.started:
            expected = {'AUTO'} if self.child is None else {'GUIDED'}
            if self.state == 'INTERCEPT' and self.child.state in ('WAIT_AUTO', 'SEARCHING', 'REQUEST_GUIDED'):
                expected.add('AUTO')
            if self.state == 'RESUME_AUTO':
                expected.add('AUTO')
            if self.state == 'AUTO_FINISH':
                expected.add('LAND')
            if t.rc_slot != self.rc_slot or t.rc_selected_mode != 'AUTO' or t.mode not in expected:
                return self.abort(now, t, 'Pilot/mod müdahalesi; bu oturumda tekrar devralınmaz', pilot=True)
            if gap and self.child is not None:
                return self.abort(now, t, 'Karar döngüsü kesildi')
        if self.state == 'AUTO_FINISH':
            if t.rebooted or problem:
                return self.abort(now, t, problem or 'Otopilot yeniden başladı')
            if 0 <= now-t.heartbeat_at < self.cfg.control.heartbeat_timeout_s:
                self.route.update(t, now, self.cfg.control.telemetry_timeout_s)
            return self.decision(reason='AUTO dönüş/bitiş/LAND sürüyor; yük komutları: '+str(len(self.done))+'/2')
        issue = telemetry_problem(t, now, self.cfg) or problem
        if mission is None:
            issue = issue or 'Görev okunamadı'
        elif mission_digest(mission) != self.options.mission_fingerprint:
            issue = 'Rota parmak izi onaylanan rotayla eşleşmiyor'
        elif (self.options.search_end_seq is None or self.options.search_end_seq >= mission.land_seq
              or any(mission.current_command(s) != 16 for s in range(
                  self.options.search_start_seq or 0, self.options.search_end_seq+1))):
            issue = 'Tarama bölümü yalnız waypoint içermeli ve son LAND öncesinde bitmeli'
        if issue:
            self.reset_holds()
            if self.started:
                return self.abort(now, t, issue)
            return self.decision(reason=issue)
        if not self.saw_disarmed:
            return self.decision(reason='Havada yeniden başlatma devralmaz; önce yerde DISARM görülmeli')
        if t.mode == 'AUTO' and t.rc_selected_mode == 'AUTO' and not self.started:
            self.started, self.rc_slot = True, t.rc_slot
        if not self.started:
            return self.decision()
        self.route.update(t, now, self.cfg.control.telemetry_timeout_s)
        if self.state == 'AUTO_FINISH':
            return self.decision(reason='AUTO dönüş/bitiş/LAND rotası sürüyor; yük komutları: '+str(len(self.done))+'/2')
        if not inside(self.options.flight_polygon, (t.lat, t.lon)):
            return self.abort(now, t, 'İzinli uçuş poligonu dışında')

        if self.state == 'RELEASE_WAIT':
            status = statuses.get(PAYLOAD[self.selected])
            if status in ('ACK_ACCEPTED', 'SIMULATED'):
                self.done.add(self.selected)
                self.reset_holds()
                if self.child is None:
                    self.selected = None
                    self.transition('SEARCHING', now, 'Diğer renk aranıyor; AUTO rota devam ediyor')
                    return self.decision()
                self.climb_hold.reset()
                self.transition('CLIMB', now, 'Yük komutu kabul edildi; tarama irtifasına dönülüyor')
                return self.decision(Action('stop'))
            if status in ('REJECTED', 'UNCERTAIN', 'BLOCKED') or now-self.entered > self.options.release_ack_timeout_s:
                return self.abort(now, t, 'Yük komutu doğrulanamadı; tekrar bırakma yok')
            return self.decision(*((Action('stop'),) if self.child else ()))
        if self.state in ('CLIMB', 'RESUME_SELECT', 'RESUME_AUTO'):
            if now-self.entered > (self.cfg.control.return_timeout_s if self.state == 'CLIMB' else self.cfg.control.mode_timeout_s):
                return self.abort(now, t, 'AUTO taramasına dönüş zaman aşımı')
            if self.state == 'CLIMB':
                error = self.return_alt-t.relative_alt_m
                held = self.climb_hold.update(t.position_at, t.position_at, abs(error)<.25 and abs(t.vd)<.15)
                if held >= 1.:
                    self.transition('RESUME_SELECT', now, 'Kesilen tarama waypoint sırası doğrulanıyor')
                    return self.decision(Action('stop'), Action('resume', (self.resume_seq, mission.fingerprint)))
                return self.decision(self.child._velocity(t, -self.cfg.control.kd_xy*t.vn,
                    -self.cfg.control.kd_xy*t.ve, -self.cfg.control.kp_height*error, dt))
            if self.state == 'RESUME_SELECT':
                if t.mission_seq == self.resume_seq and t.mission_at > self.entered:
                    self.transition('RESUME_AUTO', now, 'AUTO taramasına devrediliyor')
                    return self.decision(Action('stop'), Action('mode', ('AUTO','GUIDED')))
                return self.decision(Action('stop'))
            if t.mode == 'AUTO' and t.heartbeat_at > self.entered:
                if t.mission_seq != self.resume_seq:
                    return self.abort(now, t, 'AUTO yanlış waypoint sırasında başladı', pilot=True)
                self.child, self.selected = None, None
                self.transition('SEARCHING', now, 'Diğer hedef veya dönüş rotası devam ediyor')
                return self.decision(Action('revoke'))
            return self.decision(Action('stop'))

        if self.state == 'INTERCEPT':
            metrics = tuple(x.metric for x in candidates if x.color == self.selected and x.metric is not None)
            if (self.child.state in ('WAIT_AUTO', 'SEARCHING') and not metrics
                    and now-self.entered > self.cfg.control.lost_target_abort_s):
                self.child, self.selected = None, None
                self.transition('SEARCHING', now, 'Aday kayboldu; iki renk yeniden aranıyor')
                return self.decision()
            d = self.child.step(now, t, metrics, frame_id, frame_at, mission)
            if d.state in ('ABORTED','PILOT_CONTROL'):
                self.transition(d.state, now, d.reason)
                return d
            for action in d.actions:
                if action.kind == 'release':
                    return self.request_release(now, frame_id, frame_at, 'GUIDED')
            return replace(d, reason=self.selected+' hedef: '+d.reason.replace('Mavi hedef', 'Hedef'))

        if t.mission_seq is not None and t.mission_seq > self.options.search_end_seq:
            self.transition('AUTO_FINISH', now, 'Tarama bitti; kalan yükler korunarak dönüş/bitiş/LAND devam ediyor')
            self.reset_holds()
            return self.decision()
        if (not self.route.search_allowed(t, mission) or t.relative_alt_m < self.cfg.control.minimum_intercept_relative_alt_m):
            self.reset_holds()
            return self.decision(reason='Kalkış, direk dışı giriş kapıları ve izinli tarama bölümü bekleniyor')
        self.state = 'SEARCHING'
        if not 0 <= now-frame_at <= self.cfg.control.frame_timeout_s:
            self.reset_holds()
            return self.decision(reason='Güncel görüntü yok; bırakma yok')
        if frame_id is None or frame_id == self.last_frame:
            return self.decision()
        self.last_frame = frame_id
        eligible = [x for x in candidates if x.color in COLORS and x.color not in self.requested
                    and x.frame_id == frame_id and x.captured_at == frame_at
                    and math.isfinite(x.confidence) and self.cfg.camera.confidence_min <= x.confidence <= 1]
        if self.options.strategy == 'center':
            eligible = [x for x in eligible if x.metric is not None]
            if eligible:
                choice = max(eligible, key=lambda x: x.confidence)
                self.selected, self.resume_seq, self.return_alt = choice.color, t.mission_seq, t.relative_alt_m
                self.child = Controller(self.cfg)
                self.child.saw_disarmed = self.saw_disarmed
                self.transition('INTERCEPT', now, self.selected+' hedef doğrulanıyor')
                d = self.child.step(now, t, (choice.metric,), frame_id, frame_at, mission)
                return d
        else:
            ready = []
            for color in COLORS:
                choices = [x for x in eligible if x.color == color]
                choice = max(choices, key=lambda x:x.confidence) if choices else None
                h = self.holds[color]
                if choice is None:
                    h.reset()
                    self.boxes.pop(color, None)
                    continue
                if color in self.boxes and bbox_iou(choice.bbox, self.boxes[color]) < self.options.quick_iou:
                    h.reset()
                self.boxes[color] = choice.bbox
                h.update(frame_id, frame_at, True)
                if h.count >= self.options.quick_frames and h.elapsed+1e-9 >= self.options.quick_hold_s:
                    ready.append(choice)
            if ready:
                self.selected = max(ready, key=lambda x:x.confidence).color
                return self.request_release(now, frame_id, frame_at, 'AUTO')
        return self.decision(reason='Mavi/kırmızı hedef aranıyor; tamamlanan renk yeniden bırakılmaz')

    def request_release(self, now, frame_id, frame_at, expected_mode):
        if self.selected in self.requested:
            raise RuntimeError('Aynı renk için ikinci bırakma isteği')
        self.requested.add(self.selected)
        self.transition('RELEASE_WAIT', now, self.selected+' hedef için '+PAYLOAD[self.selected]+' yük komutu bekleniyor')
        actions = [Action('payload', (PAYLOAD[self.selected], self.selected, frame_id, frame_at, expected_mode))]
        if expected_mode == 'GUIDED':
            actions.insert(0, Action('stop'))
        return self.decision(*actions)
