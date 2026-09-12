from dataclasses import replace
import math

from ..controller import Controller, ContinuousHold, telemetry_problem
from ..geometry import bbox_iou
from ..types import Action, Decision
from .config import COLORS, PAYLOAD
from ..camera_contract import metric_missing
from .route import RouteProgress, area_allowed, mission_digest, mission_contract_problem


class DualController:
    """AUTO rota + iki bağımsız yük. Eski Controller yalnız merkezleme alt yordamıdır."""
    def __init__(self, cfg, options):
        options.validate()
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
        self.required_targets = {target for target, payload in PAYLOAD.items()
                                 if payload in options.payloads}
        self.holds = {c: ContinuousHold(cfg.control.max_lock_frame_gap_s) for c in COLORS}
        self.boxes = {}
        self.last_frame = None
        self.climb_hold = ContinuousHold(cfg.control.telemetry_timeout_s)
        self.stop_hold = ContinuousHold(cfg.control.telemetry_timeout_s)
        self.verify_hold = ContinuousHold(cfg.control.max_lock_frame_gap_s)
        self.selected_box = None
        self.verify_xy = None
        self.verify_frame = None
        self.retry_until = {c: -math.inf for c in COLORS}
        self.search_speed_set = False
        self.speed_requested_at = -math.inf
        self.lap = 1  # Uçulan tarama turu; search_laps bunu sınırlar.
        self.started_at = None  # AUTO devralma anı; görev süresi buradan sayılır.
        # Köprüleme yalnız taramada, yalnız sayaç sıfırlanmasını önlemek için
        # kullanılır. Duruş, doğrulama, merkezleme ve bırakma yolları gerçek
        # OpenCV kanıtı ister; tahmin oralara hiç girmez.
        self.bridge_enabled = options.tracking.enabled and options.tracking.bridge_search

    def decision(self, *actions, reason=None):
        return Decision(self.state, reason or self.reason, tuple(actions))

    def transition(self, state, now, reason):
        self.state, self.entered, self.reason = state, now, reason

    def reset_holds(self):
        for h in self.holds.values():
            h.reset()
        self.boxes.clear()

    def safe_auto_abort_actions(self, now, t):
        """Kontrol bizdeyken dur ve RC anahtarının seçtiği AUTO rotasına dön."""
        if (self.child is not None and t.mode == 'GUIDED' and t.rc_healthy
                and t.rc_slot == self.rc_slot and t.rc_selected_mode == 'AUTO'
                and t.system_status == 4
                and 0 <= now-t.heartbeat_at <= self.cfg.control.heartbeat_timeout_s):
            return (Action('stop'), Action('mode', ('AUTO', 'GUIDED')), Action('revoke'))
        return (Action('revoke'),)

    def abort(self, now, t, reason, pilot=False):
        auto_return_allowed = self.state in {
            'REQUEST_STOP', 'STOPPING', 'VERIFYING', 'INTERCEPT',
            'RELEASE_WAIT', 'CLIMB', 'RESUME_SELECT', 'RESUME_AUTO',
        }
        self.transition('PILOT_CONTROL' if pilot else 'ABORTED', now, reason)
        self.reset_holds()
        actions = ((Action('revoke'),) if pilot or not auto_return_allowed
                   else self.safe_auto_abort_actions(now, t))
        return self.decision(*actions)

    def step(self, now, t, candidates, frame_id, frame_at, mission, problem=None, release_status=None,
             search_speed_status=None):
        if metric_missing(self.cfg.camera):
            return self.decision(reason='Kamera yalnız gözlem; merkezleme ve bırakma kapalı')
        statuses = release_status or {}
        dt = min(.1, max(.001, now-self.last_step)) if self.last_step is not None else .05
        gap = self.last_step is not None and now-self.last_step > self.cfg.link.command_lease_s
        self.last_step = now
        if self.state in ('DONE', 'INCOMPLETE', 'ABORTED', 'PILOT_CONTROL'):
            return self.decision()
        if not t.armed and t.landed == 1 and 0 <= now-t.heartbeat_at < self.cfg.control.heartbeat_timeout_s:
            if self.started:
                complete = self.done == self.required_targets
                self.transition('DONE' if complete else 'INCOMPLETE', now,
                    'İniş görüldü; takılı yük komutları tamamlandı' if complete else
                    'İniş görüldü; takılı yük komutları tamamlanmadı')
                return self.decision(Action('revoke'))
            self.saw_disarmed = True
            self.reset_holds()
            return self.decision(reason='DISARM görüldü; AUTO kalkış bekleniyor')
        if self.started:
            expected = {'AUTO'} if self.child is None else {'GUIDED'}
            if self.state == 'REQUEST_STOP':
                expected.add('AUTO')
            if self.state == 'RESUME_AUTO':
                expected.add('AUTO')
            if self.state in ('RELAP_CLAIM', 'TIME_LAND_CLAIM'):
                # AUTO'dan GUIDED'e geçiş isteniyor; iki mod da bu kısa pencerede olağan.
                expected.update(('AUTO', 'GUIDED'))
            if self.state == 'AUTO_FINISH':
                expected.add('LAND')
            if self.state == 'SELECT_LAND':
                expected = {'GUIDED'}
            if self.state == 'HANDOFF_LAND':
                expected = {'GUIDED', 'AUTO'}
            if self.state == 'LANDING':
                expected = {'AUTO', 'LAND'}
            if t.rc_slot != self.rc_slot or t.rc_selected_mode != 'AUTO' or t.mode not in expected:
                return self.abort(now, t, 'Pilot/mod müdahalesi; bu oturumda tekrar devralınmaz', pilot=True)
            if gap and self.child is not None:
                return self.abort(now, t, 'Karar döngüsü kesildi')
        if self.state in ('SELECT_LAND', 'HANDOFF_LAND', 'LANDING'):
            if t.rebooted or problem:
                return self.abort(now, t, problem or 'Otopilot yeniden başladı')
            if not 0 <= now-t.heartbeat_at < self.cfg.control.heartbeat_timeout_s:
                return self.abort(now, t, 'İnişte otopilot heartbeat güncel değil')
            if self.state == 'SELECT_LAND':
                if t.mission_seq == mission.land_seq and t.mission_at > self.entered:
                    self.transition('HANDOFF_LAND', now, 'LAND waypointi seçildi; AUTO inişine devrediliyor')
                    return self.decision(Action('stop'), Action('mode', ('AUTO', 'GUIDED')))
                if now-self.entered > self.cfg.control.mode_timeout_s:
                    return self.abort(now, t, 'LAND görev sırası doğrulanamadı; rotaya dönülmez')
                return self.decision(Action('stop'))
            if self.state == 'HANDOFF_LAND':
                if t.mode == 'AUTO' and t.heartbeat_at > self.entered:
                    if t.mission_seq != mission.land_seq:
                        return self.abort(now, t, 'AUTO yanlış görev sırasıyla başladı', pilot=True)
                    self.child, self.selected = None, None
                    self.transition('LANDING', now, 'İki yük sonrası kalan waypointler atlanarak LAND waypointine iniliyor')
                    return self.decision(Action('revoke'))
                if now-self.entered > self.cfg.control.mode_timeout_s:
                    return self.abort(now, t, 'AUTO inişine devir doğrulanamadı')
                return self.decision(Action('stop'))
            return self.decision()
        if self.state == 'AUTO_FINISH':
            if t.rebooted or problem:
                return self.abort(now, t, problem or 'Otopilot yeniden başladı')
            if 0 <= now-t.heartbeat_at < self.cfg.control.heartbeat_timeout_s:
                self.route.update(t, now, self.cfg.control.telemetry_timeout_s)
            return self.decision(reason='AUTO dönüş/bitiş/LAND sürüyor; yük komutları: '+str(len(self.done))+'/2')
        issue = telemetry_problem(t, now, self.cfg) or problem
        route_problem = mission_contract_problem(mission, self.options)
        if route_problem:
            issue = issue or route_problem
        if issue:
            self.reset_holds()
            if self.started:
                return self.abort(now, t, issue)
            return self.decision(reason=issue)
        if not self.saw_disarmed:
            return self.decision(reason='Havada yeniden başlatma devralmaz; önce yerde DISARM görülmeli')
        if t.mode == 'AUTO' and t.rc_selected_mode == 'AUTO' and not self.started:
            self.started, self.rc_slot, self.started_at = True, t.rc_slot, now
        if not self.started:
            return self.decision()
        self.route.update(t, now, self.cfg.control.telemetry_timeout_s)
        if self.state == 'AUTO_FINISH':
            return self.decision(reason='AUTO dönüş/bitiş/LAND rotası sürüyor; yük komutları: '+str(len(self.done))+'/2')
        if not area_allowed(self.options, (t.lat, t.lon)):
            if not self.route.entered and self.child is None:
                # Kalkış/giriş AUTO rotasında alan dışında başlayabilir. Henüz
                # devralmadığımız bu aşama kalıcı iptal değildir; kapı ve alan
                # birlikte doğrulanana kadar hiçbir hareket komutu üretme.
                self.reset_holds()
                return self.decision(reason='AUTO giriş rotası bekleniyor; araç henüz izinli poligon içinde değil')
            return self.abort(now, t, 'İzinli uçuş poligonu dışında')

        # Görev süresi: yarım kalan merkezleme/alçalma/tur dahil her iş bırakılır.
        # RELEASE_WAIT hariç tutulur; yük komutu zaten en fazla
        # release_ack_timeout_s içinde sonuçlanır ve sonucu kaydedilmelidir.
        if (self.past(now, self.options.mission_deadline_s)
                and self.state not in ('RELEASE_WAIT', 'TIME_LAND_CLAIM', 'SELECT_LAND',
                                       'HANDOFF_LAND', 'LANDING', 'AUTO_FINISH')):
            return self.begin_time_land(now, t, mission)

        if self.state == 'SET_SEARCH_SPEED':
            speed_reply = search_speed_status or {}
            fresh_reply = speed_reply.get('request_at') is not None and speed_reply['request_at'] >= self.entered
            if fresh_reply and speed_reply.get('status') == 'ACCEPTED':
                self.search_speed_set = True
                self.transition('SEARCHING', now, 'Ana görev tarama hızı kabul edildi')
            elif (fresh_reply and speed_reply.get('status') == 'REJECTED') or now-self.entered > self.cfg.control.mode_timeout_s:
                return self.abort(now, t, 'Ana görev tarama hızı doğrulanamadı; kontrol devralınmadı')
            else:
                return self.decision()
        if (self.options.strategy == 'center' and self.options.center_search_speed_mps is not None
                and self.search_speed_set and self.child is None and t.mode == 'AUTO'
                and t.horizontal_speed > self.options.center_search_speed_mps+self.options.search_speed_margin_mps
                and now-self.speed_requested_at > self.options.search_speed_retry_s):
            # Otopilot isteği kabul etse bile AUTO bacağı yeniden başlayınca
            # WPNAV_SPEED'e dönebiliyor; ölçülen hız bunu ele veriyor.
            self.search_speed_set = False
        if (self.options.strategy == 'center' and self.options.center_search_speed_mps is not None
                and not self.search_speed_set and self.child is None and t.mode == 'AUTO'
                and t.mission_seq is not None
                and self.options.search_start_seq is not None
                and self.options.search_start_seq <= t.mission_seq <= self.options.search_end_seq):
            # search_start_seq'den önceki transit bacağı FC'nin WPNAV_SPEED
            # değerinde kalır. Örneğin start=3 iken TAKEOFF→WP2 hızlı,
            # WP2 tamamlanıp seq3 başladığında tarama hızı uygulanır.
            self.speed_requested_at = now
            self.transition('SET_SEARCH_SPEED', now, 'Ana görev için geçici AUTO tarama hızı ayarlanıyor')
            return self.decision(Action('search_speed', (self.options.center_search_speed_mps, self.rc_slot)))

        if self.state == 'TIME_LAND_CLAIM':
            if now-self.entered > self.cfg.control.mode_timeout_s:
                return self.abort(now, t, 'Süre sonu inişi için GUIDED geçişi doğrulanamadı')
            if t.mode != 'GUIDED' or t.heartbeat_at <= self.entered:
                return self.decision(Action('stop'))
            self.transition('SELECT_LAND', now, 'Görev süresi doldu; LAND waypointi seçiliyor')
            return self.decision(Action('stop'), Action('mission_current', (mission.land_seq,)))

        if self.state == 'RELAP_CLAIM':
            if now-self.entered > self.cfg.control.mode_timeout_s:
                return self.abort(now, t, 'Yeni tarama turu için GUIDED geçişi doğrulanamadı')
            if t.mode != 'GUIDED' or t.heartbeat_at <= self.entered:
                return self.decision(Action('stop'))
            # Duruştayız ve kontrol bizde: kesilen tur yerine tarama başına dön.
            # route.finished burada sıfırlanır; GUIDED'de olduğumuz için
            # RouteProgress.update() onu yeniden doğru yapmaz.
            self.route.finished = False
            self.resume_seq = self.options.search_start_seq
            self.transition('RESUME_SELECT', now,
                            str(self.lap)+'. tarama turu için başlangıç waypointi seçiliyor')
            return self.decision(Action('stop'),
                                 Action('resume', (self.resume_seq, mission_digest(mission))))

        if self.state == 'RELEASE_WAIT':
            status = statuses.get(PAYLOAD[self.selected])
            if status in ('ACK_ACCEPTED', 'SIMULATED'):
                self.done.add(self.selected)
                self.reset_holds()
                if self.done == self.required_targets:
                    # Takılı bütün yüklerden sonra kalan tarama
                    # waypointlerine gidilmez, doğrudan LAND waypointine uçulur.
                    self.transition('SELECT_LAND', now, 'Takılı yük komutları kabul edildi; LAND waypointi seçiliyor')
                    return self.decision(Action('stop'), Action('mission_current', (mission.land_seq,)))
                if self.options.strategy == 'quick':
                    self.transition('RESUME_SELECT', now, 'Yük komutu kabul edildi; irtifa değiştirmeden rotaya dönülüyor')
                    return self.decision(Action('stop'), Action('resume', (self.resume_seq, mission_digest(mission))))
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
                    return self.decision(Action('stop'), Action('resume', (self.resume_seq, mission_digest(mission))))
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
                self.search_speed_set = False
                self.reset_holds()
                self.transition('SEARCHING', now, 'Diğer hedef veya dönüş rotası devam ediyor')
                return self.decision(Action('revoke'))
            return self.decision(Action('stop'))

        if self.state in ('REQUEST_STOP', 'STOPPING', 'VERIFYING'):
            return self.stop_and_verify(now, t, candidates, frame_id, frame_at, mission)

        if self.state == 'INTERCEPT':
            visual = [x for x in self.fresh_candidates(candidates,frame_id,frame_at)
                      if x.color == self.selected and x.corroborated]
            metrics = tuple(x.metric for x in visual if x.metric is not None)
            if metrics:
                metric_boxes = {x.metric.bbox for x in visual if x.metric is not None}
                tracked = [x for x in visual if x.bbox in metric_boxes]
                if tracked:
                    self.selected_box = max(tracked, key=lambda x:x.rank).bbox
            elif self.child.target is not None:
                # Duruşta PnP ile doğrulanmış mutlak hedef konumu sabittir.
                # Merkezleme sırasında dörtgen görünmeye devam ederken PnP'nin
                # anık düzlem çözümü bozulursa aynı OpenCV kutusuyla bu sabit
                # konumu tazele. Böylece sahte/yeni hedef PnP'siz devralınmaz.
                matches = [x for x in visual
                           if bbox_iou(x.bbox, self.selected_box) >= self.options.quick_iou]
                if matches:
                    tracked = max(matches, key=lambda x:bbox_iou(x.bbox, self.selected_box))
                    self.selected_box = tracked.bbox
                    metrics = (replace(self.child.target, frame_id=frame_id,
                                       captured_at=frame_at, confidence=tracked.color_fill,
                                       bbox=tracked.bbox),)
            d = self.child.step(now, t, metrics, frame_id, frame_at, mission)
            if d.state in ('ABORTED','PILOT_CONTROL'):
                if (d.state == 'ABORTED'
                        and d.reason == 'Hedef/güncel görüntü kayboldu; kilit ve alçalma iptal'):
                    # Tek hedef/geometri kaybı bütün sortiyi kalıcı kapatmasın.
                    # GUIDED'de dur, kesilen waypointi doğrula ve AUTO taramasına
                    # dön; aynı renk kısa retry gecikmesi boyunca yeniden seçilmez.
                    self.retry_until[self.selected] = now+self.options.retry_delay_s
                    self.reset_holds()
                    self.transition('RESUME_SELECT', now,
                                    'Hedef kayboldu; yük korunarak AUTO taramasına dönülüyor')
                    return self.decision(Action('stop'),
                                         Action('resume', (self.resume_seq, mission_digest(mission))))
                self.transition(d.state, now, d.reason)
                # Alt denetleyicinin genel LOITER geri dönüşünü yarışma
                # akışında kullanma. AUTO seçiliyken düşük gazlı LOITER
                # aracı sert alçaltabilir; doğrulanmış göreve geri dön.
                if d.state == 'ABORTED':
                    d = replace(d, actions=self.safe_auto_abort_actions(now, t))
                return d
            for action in d.actions:
                if action.kind == 'release':
                    if not metrics or not 0 <= now-frame_at <= self.cfg.control.frame_timeout_s:
                        return self.abort(now,t,'Bırakma anında taze OpenCV renk/geometri kanıtı yok')
                    return self.request_release(now, frame_id, frame_at, 'GUIDED')
            return replace(d, reason=self.selected+' hedef: '+d.reason.replace('Mavi hedef', 'Hedef'))

        if t.mission_seq is not None and t.mission_seq > self.options.search_end_seq:
            self.reset_holds()
            if (self.done != self.required_targets and self.lap < self.options.search_laps
                    and self.child is None and self.options.search_start_seq is not None):
                self.lap += 1
                # Eksik yük var ve tur hakkı kaldı: AUTO bitiş/LAND'e bırakmak
                # yerine duruş alıp tarama başına dön. Yük komutu verilmiş
                # renkler `requested` içinde kaldığı için ikinci kez denenmez.
                self.child = Controller(self.cfg)
                self.transition('RELAP_CLAIM', now, 'Tarama bitti, yük kaldı; '+str(self.lap)
                                +'. tur için '+str(self.options.search_start_seq)+'. waypointe dönülüyor')
                return self.decision(Action('claim', (t.rc_slot,)), Action('mode', ('GUIDED', 'AUTO')))
            self.transition('AUTO_FINISH', now, 'Tarama bitti; kalan yükler korunarak dönüş/bitiş/LAND devam ediyor')
            return self.decision()
        if (not self.route.search_allowed(t, mission) or t.relative_alt_m < self.cfg.control.minimum_intercept_relative_alt_m):
            self.reset_holds()
            return self.decision(reason=('Kalkış sonrası waypoint ve tarama irtifası bekleniyor'
                if self.options.search_scope == 'mission' else
                'Kalkış, direk dışı giriş kapıları ve izinli tarama bölümü bekleniyor'))
        self.state = 'SEARCHING'
        if not 0 <= now-frame_at <= self.cfg.control.frame_timeout_s:
            self.reset_holds()
            return self.decision(reason='Güncel görüntü yok; bırakma yok')
        if frame_id is None or (self.last_frame is not None and frame_id <= self.last_frame):
            return self.decision()
        self.last_frame = frame_id
        searchable = lambda color: (color in self.required_targets and color not in self.requested
                                    and now >= self.retry_until[color])
        eligible = [x for x in self.fresh_candidates(candidates, frame_id, frame_at)
                    if searchable(x.color)]
        bridges = {x.color: x for x in self.bridged_candidates(candidates, frame_id, frame_at)
                   if searchable(x.color)} if self.bridge_enabled else {}
        ready = []
        for color in COLORS:
            choices = [x for x in eligible if x.color == color]
            associated = [x for x in choices if color in self.boxes
                          and bbox_iou(x.bbox,self.boxes[color]) >= self.options.quick_iou]
            choice = max(associated or choices, key=lambda x:x.rank) if choices else None
            h = self.holds[color]
            if choice is None:
                if color in bridges and color in self.boxes:
                    # Motion blur/tek karelik OpenCV boşluğu: biriken tarama
                    # kanıtı silinmez. Sayaç ARTMAZ da; gereken bağımsız kare
                    # sayısı yine gerçek tespitlerden gelir. Süreklilik bundan
                    # sonra ContinuousHold'un kendi max_lock_frame_gap_s boşluk
                    # sınırıyla korunur, sonsuza kadar değil.
                    self.boxes[color] = bridges[color].bbox
                    continue
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
            if self.past(now, self.options.intercept_deadline_s):
                # Süre sonuna yakın yeni hedefe durma: bitiremeyeceğimiz bir
                # merkezleme için rotayı kesmek iniş payını yer.
                return self.decision(reason='Süre sonuna yakın; yeni hedefe durulmuyor')
            choice = max(ready, key=lambda x:x.rank)
            return self.begin_stop(now, t, choice)
        return self.decision(reason='Mavi/kırmızı aday aranıyor; ilk doğrulama '+str(self.options.quick_hold_s)+' s')

    def elapsed(self, now):
        """Kalkıştan (AUTO devralma) beri geçen saniye; devralınmadıysa None."""
        return None if self.started_at is None else now-self.started_at

    def past(self, now, limit):
        elapsed = self.elapsed(now)
        return limit is not None and elapsed is not None and elapsed >= limit

    def begin_time_land(self, now, t, mission):
        """Süre doldu: yarım kalan her iş bırakılır, LAND waypointine gidilir."""
        if self.child is not None or t.mode == 'GUIDED':
            self.reset_holds()
            self.transition('SELECT_LAND', now, 'Görev süresi doldu; LAND waypointi seçiliyor')
            return self.decision(Action('stop'), Action('mission_current', (mission.land_seq,)))
        self.reset_holds()
        self.transition('TIME_LAND_CLAIM', now,
                        'Görev süresi doldu; inişe geçmek için GUIDED isteniyor')
        return self.decision(Action('claim', (t.rc_slot,)), Action('mode', ('GUIDED', 'AUTO')))

    def fresh_candidates(self, candidates, frame_id, frame_at):
        return [x for x in candidates if x.color in COLORS
                    and x.frame_id == frame_id and x.captured_at == frame_at
                    and x.source == 'opencv' and x.confidence is None and x.color_verified is True
                    and type(x.color_fill) in (int,float) and math.isfinite(x.color_fill)
                    and self.options.color_search.min_fill <= x.color_fill <= 1
                    and len(x.bbox) == 4 and all(math.isfinite(v) and 0 <= v <= 1 for v in x.bbox)
                    and x.bbox[0] < x.bbox[2] and x.bbox[1] < x.bbox[3]]

    def bridged_candidates(self, candidates, frame_id, frame_at):
        """Kısa süreli kestirimle köprülenen adaylar; yalnız tarama sayacı içindir.

        Bunlar `corroborated` değildir ve `fresh_candidates()` onları hiçbir
        zaman döndürmez; duruş sonrası doğrulama, merkezleme ve bırakma yolları
        etkilenmez.
        """
        limit = self.options.tracking.max_tracking_frames
        return [x for x in candidates if x.color in COLORS
                    and x.frame_id == frame_id and x.captured_at == frame_at
                    and x.source == 'tracked' and x.confidence is None
                    and x.color_verified is False and x.metric is None and x.color_fill is None
                    and type(x.missed) is int and 0 < x.missed <= limit
                    and len(x.bbox) == 4 and all(math.isfinite(v) and 0 <= v <= 1 for v in x.bbox)
                    and x.bbox[0] < x.bbox[2] and x.bbox[1] < x.bbox[3]]

    def begin_stop(self, now, t, choice):
        self.selected, self.selected_box = choice.color, choice.bbox
        self.resume_seq, self.return_alt = t.mission_seq, t.relative_alt_m
        self.child = Controller(self.cfg)
        self.stop_hold.reset()
        self.verify_hold.reset()
        self.verify_xy, self.verify_frame = None, None
        self.reset_holds()
        self.transition('REQUEST_STOP', now, 'Aday görüldü; GUIDED ile durma isteniyor')
        return self.decision(Action('claim', (t.rc_slot,)), Action('mode', ('GUIDED', 'AUTO')))

    def stop_and_verify(self, now, t, candidates, frame_id, frame_at, mission):
        """Önce sıfır hız; duruştan sonra aynı OpenCV dörtgeni zorunlu."""
        if self.state == 'REQUEST_STOP':
            if now-self.entered > self.cfg.control.mode_timeout_s:
                return self.abort(now, t, 'GUIDED duruş geçişi doğrulanamadı')
            if t.mode != 'GUIDED' or t.heartbeat_at <= self.entered:
                return self.decision(Action('stop'))
            self.transition('STOPPING', now, 'Frenleniyor; '+('merkezleme ve alçalma kapalı' if self.options.strategy == 'quick'
                            else 'merkezleme öncesi duruş bekleniyor'))
            return self.decision(Action('stop'))

        fresh = frame_id is not None and 0 <= now-frame_at <= self.cfg.control.frame_timeout_s
        choice = None
        if fresh:
            usable = [x for x in self.fresh_candidates(candidates, frame_id, frame_at)
                      if x.color == self.selected]
            if self.state == 'VERIFYING':
                usable = [x for x in usable if x.corroborated]
            matches = [x for x in usable if bbox_iou(x.bbox, self.selected_box) >= self.options.quick_iou]
            choice = max(matches, key=lambda x:bbox_iou(x.bbox, self.selected_box)) if matches else None
            if choice is None and self.state == 'STOPPING' and len(usable) == 1:
                # Fren sırasında hedef kadrajda hızla kaydığı için kutu örtüşmesi
                # kopuyor. Yalnız frenleme aşamasında ve aynı renkten tek aday
                # varsa hedef yeniden yakalanır; duruştan sonra kural katı kalır.
                choice = usable[0]
                self.verify_hold.reset()
            if choice:
                self.selected_box = choice.bbox
        stopped = (t.horizontal_speed <= self.options.stop_speed_mps
                   and abs(t.vd) <= self.cfg.control.release_vertical_speed_mps
                   and t.tilt_deg <= self.cfg.control.release_tilt_deg)
        if self.state == 'STOPPING':
            if now-self.entered > self.options.stop_timeout_s:
                return self.abort(now, t, 'Araç zamanında durmadı; kontrol AUTO rotasına bırakılıyor')
            held = self.stop_hold.update(t.position_at, t.position_at, stopped)
            if held+1e-9 >= self.options.stop_hold_s:
                self.verify_frame = frame_id
                self.transition('VERIFYING', now, 'Araç yavaşladı; '+('taze OpenCV renk/dörtgen doğrulaması' if self.options.strategy == 'quick'
                                else 'hedef OpenCV renk, köşe ve metrik geometriyle doğrulanıyor'))
            return self.decision(Action('stop'))

        if not fresh:
            return self.abort(now, t, 'Doğrulamada kamera güncel değil; körlemesine rota devri yok')
        if now-self.entered > self.options.verify_timeout_s:
            self.retry_until[self.selected] = now+self.options.retry_delay_s
            self.reset_holds()
            self.transition('RESUME_SELECT', now, 'Hedef doğrulanamadı; yük korunarak kesilen waypoint seçiliyor')
            return self.decision(Action('stop'), Action('resume', (self.resume_seq, mission_digest(mission))))
        if not stopped:
            if self.options.strategy == 'quick':
                self.verify_hold.reset()
                return self.decision(Action('stop'), reason='Araç hâlâ hareketli; hedef doğrulaması sıfırlandı')
            # Ana görevde GUIDED sürüklenmesi 0,2 m/s eşiğini kısa süre aşınca
            # tüm ölçüm siliniyordu. Bu kare sayılmaz; süreklilik ContinuousHold
            # boşluk sınırıyla (max_lock_frame_gap_s) korunur.
            return self.decision(Action('stop'), reason='Araç hâlâ hareketli; bu kare ölçüme sayılmıyor')
        if (frame_at <= self.entered or (self.verify_frame is not None and frame_id <= self.verify_frame)):
            return self.decision(Action('stop'))
        self.verify_frame = frame_id
        if self.options.strategy == 'quick':
            if choice is None:
                self.verify_hold.reset()
                return self.decision(Action('stop'), reason='Aynı hedefte taze OpenCV dörtgeni bekleniyor')
            held = self.verify_hold.update(frame_id, frame_at, True)
            if (held+1e-9 >= self.options.quick_verify_s
                    and self.verify_hold.count >= self.options.quick_verify_frames):
                return self.request_release(now, frame_id, frame_at, 'GUIDED')
            return self.decision(Action('stop'), reason=f'Kısa doğrulama: {held:.2f}/{self.options.quick_verify_s:.2f} s')
        if choice is None:
            self.verify_hold.reset()
            return self.decision(Action('stop'), reason='Aynı hedefte taze OpenCV dörtgeni bekleniyor')
        metric = choice.metric
        if (metric is None or metric.frame_id != frame_id or metric.captured_at != frame_at
                or not all(math.isfinite(v) for v in (metric.north, metric.east, metric.ground_down,
                           metric.camera_height_m, metric.confidence))):
            # PnP her karede çözülmüyor; hedef görünürken geometrisiz kare
            # birikimi silmez, yalnız sayılmaz. Boşluk sınırı yine geçerli.
            return self.decision(Action('stop'), reason='Hedefte taze OpenCV köşe/geometri kanıtı yok; bekleniyor')
        if self.verify_xy is not None and math.hypot(metric.north-self.verify_xy[0], metric.east-self.verify_xy[1]) > self.cfg.control.target_association_m:
            self.verify_hold.reset()
            return self.decision(Action('stop'), reason='Hedef konumu sıçradı; doğrulama kabul edilmedi')
        self.verify_xy = (metric.north, metric.east)
        held = self.verify_hold.update(frame_id, frame_at, True)
        if held+1e-9 >= self.cfg.control.acquire_s and self.verify_hold.count >= self.cfg.control.acquire_frames:
            # Eski merkezleme kodu korunur. Bu noktada duruş ve taze hedef ayrıca doğrulandı.
            self.child.saw_disarmed = True
            self.child.rc_slot = self.rc_slot
            self.child.return_alt = self.return_alt
            self.child.interaction_started = now
            self.child.track_xy = self.verify_xy
            self.child.last_valid_at = frame_at
            self.child.last_frame_id = frame_id
            self.child.target = metric
            self.child._state('CENTERING', now, 'Dururken doğrulanan hedefe merkezleniyor')
            self.transition('INTERCEPT', now, 'Hedef doğrulandı; merkezleme başlıyor')
        return self.decision(Action('stop'), reason=self.reason if self.state == 'INTERCEPT' else
                             f'Hedef doğrulanıyor: {held:.2f}/{self.cfg.control.acquire_s:.2f} s')

    def request_release(self, now, frame_id, frame_at, expected_mode):
        if self.selected in self.requested:
            raise RuntimeError('Aynı renk için ikinci bırakma isteği')
        self.requested.add(self.selected)
        self.transition('RELEASE_WAIT', now, self.selected+' hedef için '+PAYLOAD[self.selected]+' yük komutu bekleniyor')
        actions = [Action('payload', (PAYLOAD[self.selected], self.selected, frame_id, frame_at, expected_mode))]
        if expected_mode == 'GUIDED':
            actions.insert(0, Action('stop'))
        return self.decision(*actions)
