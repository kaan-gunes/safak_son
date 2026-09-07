from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .config import Config
from .geometry import body_to_ned, heading_velocity, local_distance
from .types import Action, Decision, MissionPlan, Target, Telemetry


ACTIVE = {"REQUEST_GUIDED", "CENTERING", "DESCENDING", "RELEASE_PENDING",
          "RETURN_CLIMB", "RETURN_TRANSIT", "SELECT_LAND", "HANDOFF_LAND", "REQUEST_RTL"}


class ContinuousHold:
    """Yalnız yeni örnekler, kesintisiz süre; yinelenen kare süre kazandırmaz."""
    def __init__(self, max_gap: float):
        self.max_gap = max_gap
        self.reset()

    def reset(self) -> None:
        self.start = None
        self.last_at = None
        self.last_id = None
        self.count = 0
        self.elapsed = 0.0

    def update(self, identity, at: float, valid: bool) -> float:
        if not valid:
            self.reset()
            return 0.0
        if identity == self.last_id:
            return self.elapsed
        if self.last_at is None or at <= self.last_at or at - self.last_at > self.max_gap:
            self.reset()
            self.start = at
        self.last_id, self.last_at = identity, at
        self.count += 1
        self.elapsed = at - self.start
        return self.elapsed


def telemetry_problem(t: Telemetry, now: float, cfg: Config) -> str | None:
    c = cfg.control
    if t.link_error:
        return t.link_error
    if t.rebooted:
        return "Pixhawk yeniden başladı"
    if now - t.heartbeat_at > c.heartbeat_timeout_s:
        return "Pixhawk heartbeat güncel değil"
    if not t.armed or t.landed != 2:
        return "Araç havada ve ARM durumda değil"
    if t.system_status != 4:
        return "Otopilot aktif/sağlıklı uçuş durumunda değil"
    for name, at in (("duruş", t.attitude_at), ("konum", t.position_at),
                     ("GPS konumu", t.global_at), ("kumanda", t.rc_at)):
        if now - at > c.telemetry_timeout_s or at > now + 0.05:
            return f"{name} verisi güncel değil"
    if now - t.timesync_at > 3.0:
        return "Pixhawk zaman eşleşmesi güncel değil"
    if now - t.ekf_at > 2 or (t.ekf_flags & 23) != 23:
        return "EKF mutlak yatay konum/hız/duruş çözümü geçersiz"
    if now - t.gps_at > 2 or (t.gps_fix or 0) < 3 or t.hdop is None or t.hdop > 1.5:
        return "GPS çözümü/HDOP merkezleme için yeterli değil"
    if now - t.status_at > 2 or not t.rc_healthy or t.rc_slot is None:
        return "RC alıcısı sağlıklı olarak doğrulanamadı"
    if now - t.landed_at > 2:
        return "Uçuş/yer durumu güncel değil"
    numbers = (t.roll, t.pitch, t.yaw, t.north, t.east, t.down, t.vn, t.ve, t.vd,
               t.lat, t.lon, t.relative_alt_m)
    if any(v is None or not math.isfinite(v) for v in numbers):
        return "Telemetride eksik/geçersiz sayısal değer"
    return None


class Controller:
    """Saf karar çekirdeği; MAVLink, disk, kamera veya web erişimi yapmaz."""
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.state = "WAIT_AUTO"
        self.reason = ("Manuel kalkış sonrası AUTO tarama bekleniyor" if cfg.mission.takeoff_mode == "manual"
                       else "AUTO kalkışın tamamlanması bekleniyor")
        self.entered = 0.0
        self.interaction_started = None
        self.return_started = None
        self.return_alt = None
        self.rc_slot = None
        self.search_rc_slot = None
        self.target: Target | None = None
        self.track_xy = None
        self.last_frame_id = None
        self.last_valid_at = -math.inf
        self.hold = ContinuousHold(cfg.control.max_lock_frame_gap_s)
        self.transit_hold = ContinuousHold(cfg.control.telemetry_timeout_s)
        self.released = False
        self.release_requested = False
        self.last_step = None
        self.last_velocity = np.zeros(3)
        self.saw_disarmed = False

    def _state(self, state: str, now: float, reason: str) -> None:
        self.state, self.entered, self.reason = state, now, reason
        self.hold.reset()
        self.transit_hold.reset()

    def _decision(self, *actions: Action, error=None, height=None, required=0.0) -> Decision:
        return Decision(self.state, self.reason, tuple(actions), self.hold.elapsed,
                        required, error, height)

    def _abort(self, now: float, t: Telemetry, reason: str, pilot=False) -> Decision:
        self._state("PILOT_CONTROL" if pilot else "ABORTED", now, reason)
        self.target = None
        self.last_velocity[:] = 0
        actions = [Action("revoke")]
        # Pilota/otopilot failsafe'ine karşı mod zorlaması yok.
        if (not pilot and t.mode == "GUIDED" and t.system_status == 4
            and now - t.heartbeat_at < self.cfg.control.heartbeat_timeout_s
            and t.rc_slot == self.rc_slot and t.rc_healthy):
            actions = [Action("stop"), Action("mode", ("LOITER", "GUIDED")), Action("revoke")]
        return self._decision(*actions)

    def _velocity(self, t: Telemetry, north: float, east: float, down: float,
                  dt: float, limit: float | None = None) -> Action:
        c = self.cfg.control
        horizontal = np.array([north, east], float)
        limit = c.max_horizontal_speed_mps if limit is None else limit
        length = np.linalg.norm(horizontal)
        if length > limit:
            horizontal *= limit / length
        desired = np.array([*horizontal, np.clip(down, -c.max_climb_mps, c.max_descent_mps)])
        delta = desired - self.last_velocity
        norm = np.linalg.norm(delta)
        max_delta = c.max_accel_mps2 * dt
        if norm > max_delta:
            delta *= max_delta / norm
        self.last_velocity += delta
        forward, right = heading_velocity(*self.last_velocity[:2], t.yaw)
        return Action("velocity", (forward, right, float(self.last_velocity[2])))

    def step(self, now: float, t: Telemetry, targets: tuple[Target, ...],
             frame_id: int | None, frame_at: float, mission: MissionPlan | None,
             preflight_problem: str | None = None, release_recorded=False) -> Decision:
        c = self.cfg.control
        dt = min(0.1, max(0.001, now - self.last_step)) if self.last_step is not None else 1 / c.rate_hz
        self.last_step = now
        if not t.armed and now - t.heartbeat_at < c.heartbeat_timeout_s:
            self.saw_disarmed = True
        if self.state in {"DONE", "ABORTED", "PILOT_CONTROL"}:
            return self._decision()
        if self.state == "RTL_RETURN":
            if now - t.heartbeat_at >= c.heartbeat_timeout_s:
                self.reason = "RTL telemetrisi güncel değil; dönüş tamamlandı sayılmadı"
                return self._decision()
            if not t.armed and t.landed == 1 and now - t.landed_at < 2:
                self._state("DONE", now, "RTL inişi tamamlandı; temsili bırakma kaydı korunuyor")
            elif (t.mode not in {"RTL", "LAND"} or t.rc_slot != self.rc_slot
                  or t.rc_selected_mode != "AUTO"):
                return self._abort(now, t, "RTL sırasında pilot/mod müdahalesi; kontrol pilotta", pilot=True)
            return self._decision()
        if self.state == "LANDING":
            if not t.armed and t.landed == 1 and now - t.heartbeat_at < c.heartbeat_timeout_s:
                self._state("DONE", now, "Son LAND tamamlandı; temsili bırakma kaydı korunuyor")
            elif t.mode not in {"AUTO", "LAND"}:
                self._state("PILOT_CONTROL", now, "İniş sırasında mod değişti; kontrol pilotta")
            return self._decision()

        if self.state == "SEARCHING" and (t.mode != "AUTO" or t.rc_selected_mode != "AUTO"
                                          or t.rc_slot != self.search_rc_slot):
            return self._abort(now, t, "AUTO taraması sırasında pilot/mod müdahalesi; kontrol pilotta", pilot=True)
        active = self.state in ACTIVE
        if active:
            if t.rc_slot != self.rc_slot or t.rc_selected_mode != "AUTO":
                return self._abort(now, t, "Kumanda anahtarı değişti; kontrol pilotta", pilot=True)
            expected = {"GUIDED"}
            if self.state == "REQUEST_GUIDED":
                expected.add("AUTO")
            if self.state == "HANDOFF_LAND":
                expected.add("AUTO")
            if self.state == "REQUEST_RTL":
                expected.add("RTL")
            if t.mode not in expected:
                return self._abort(now, t, f"Uçuş modu {t.mode}; kontrol bırakıldı", pilot=True)

        issue = telemetry_problem(t, now, self.cfg)
        if issue:
            if active:
                return self._abort(now, t, issue)
            self.hold.reset()
            self.reason = issue
            return self._decision()
        if preflight_problem or mission is None:
            if active:
                return self._abort(now, t, preflight_problem or "Görev bilgisi kayboldu")
            self.reason = preflight_problem or "AUTO görevi okunuyor"
            self.hold.reset()
            return self._decision()
        if self.state == "REQUEST_RTL":
            if t.mode == "RTL" and t.heartbeat_at > self.entered:
                self._state("RTL_RETURN", now, "RTL doğrulandı; HOME dönüşü ve iniş otopilotta")
                return self._decision(Action("revoke"))
            if now - self.entered > c.mode_timeout_s:
                return self._abort(now, t, "RTL geçişi doğrulanamadı")
            return self._decision(Action("stop"))

        if self.state in {"WAIT_AUTO", "SEARCHING"}:
            if not self.saw_disarmed:
                self.reason = "Program uçuş öncesinde DISARM durumunu görmeli; havada yeniden başlatma devralmaz"
                return self._decision()
            if (t.mode != "AUTO" or t.rc_selected_mode != "AUTO" or t.mission_seq is None
                or t.mission_seq < 1
                or (mission.takeoff_seq is not None and t.mission_seq <= mission.takeoff_seq)
                or mission.current_command(t.mission_seq) != 16
                or t.relative_alt_m < c.minimum_intercept_relative_alt_m):
                self.reason = "Havada, yeterli irtifada AUTO waypoint uçuşu bekleniyor; görüntü taraması sürüyor"
                self.hold.reset()
                return self._decision()
            if self.state != "SEARCHING":
                self.search_rc_slot = t.rc_slot
            self.state = "SEARCHING"

        if self.state.startswith("RETURN") or self.state in {"SELECT_LAND", "HANDOFF_LAND"}:
            return self._return(now, t, mission, dt)
        if self.state == "RELEASE_PENDING":
            if release_recorded:
                self.released = True
                self.return_started = now
                if self.cfg.mission.return_mode == "rtl":
                    self._state("REQUEST_RTL", now, "Temsili bırakma kaydedildi; otopilottan RTL isteniyor")
                    return self._decision(Action("stop"), Action("mode", ("RTL", "GUIDED")))
                self._state("RETURN_CLIMB", now, "Temsili bırakma kaydedildi; arama irtifasına çıkılıyor")
                return self._decision(Action("stop"))
            if now - self.entered > 1:
                return self._abort(now, t, "Temsili bırakma kaydı doğrulanamadı")
            return self._decision(Action("stop"))
        if self.state == "REQUEST_GUIDED":
            if t.mode == "GUIDED":
                self._state("CENTERING", now, "GUIDED doğrulandı; hedef üzerine merkezleniyor")
            elif now - self.entered > c.mode_timeout_s:
                return self._abort(now, t, "GUIDED geçişi doğrulanamadı")
            else:
                return self._decision()

        new_frame = frame_id is not None and frame_id != self.last_frame_id
        frame_fresh = 0 <= now - frame_at <= c.frame_timeout_s
        if new_frame:
            self.last_frame_id = frame_id
            valid = [x for x in targets if x.frame_id == frame_id and x.captured_at == frame_at
                     and all(math.isfinite(v) for v in (x.north, x.east, x.ground_down,
                                                       x.camera_height_m, x.confidence))]
            if self.track_xy is not None:
                valid = [x for x in valid if math.hypot(x.north - self.track_xy[0], x.east - self.track_xy[1])
                         <= c.target_association_m]
            self.target = max(valid, key=lambda x: x.confidence) if valid and frame_fresh else None
            if self.target:
                self.last_valid_at = frame_at
                self.track_xy = (self.target.north, self.target.east)
        target = self.target if frame_fresh else None
        if target is None or now - target.captured_at > c.frame_timeout_s:
            self.hold.reset()
            self.last_velocity[:] = 0
            if self.state == "SEARCHING":
                self.reason = "Mavi hedef aranıyor; AUTO rota devam ediyor"
                if now - self.last_valid_at > c.lost_target_abort_s:
                    self.track_xy = None
                return self._decision()
            if now - self.last_valid_at > c.lost_target_abort_s:
                return self._abort(now, t, "Hedef/güncel görüntü kayboldu; kilit ve alçalma iptal")
            self.reason = "Hedef doğrulanamıyor; hareket durduruldu, kilit sıfırlandı"
            return self._decision(Action("stop"))

        if self.state == "SEARCHING":
            self.reason = "Mavi hedef bağımsız karelerde doğrulanıyor"
            self.hold.update(target.frame_id, target.captured_at, True)
            if self.hold.elapsed >= c.acquire_s and self.hold.count >= c.acquire_frames:
                dn, de = local_distance(t.lat, t.lon, mission.land_lat, mission.land_lon)
                if math.hypot(dn, de) > self.cfg.mission.max_land_distance_m:
                    self.reason = "Son LAND noktası izin verilen test uzaklığının dışında"
                    return self._decision()
                self.rc_slot, self.return_alt = t.rc_slot, t.relative_alt_m
                self.interaction_started = now
                self._state("REQUEST_GUIDED", now, "Mavi hedef doğrulandı; GUIDED geçişi bekleniyor")
                return self._decision(Action("claim", (t.rc_slot,)), Action("mode", ("GUIDED", "AUTO")))
            return self._decision(required=c.acquire_s)

        if now - self.interaction_started > c.interaction_timeout_s:
            return self._abort(now, t, "Merkezleme/alçalma süresi doldu; bırakma yapılmadı")
        offset_down = float((body_to_ned(t.roll, t.pitch, t.yaw) @ np.array(self.cfg.camera.offset_body_m))[2])
        height = target.ground_down - t.down - offset_down
        en, ee = target.north - t.north, target.east - t.east
        error = math.hypot(en, ee)
        if height < c.minimum_camera_height_m:
            return self._abort(now, t, "Görsel yükseklik alt sınırın altında; alçalma iptal")
        if t.tilt_deg > c.control_tilt_deg:
            self.hold.reset()
            self.last_velocity[:] = 0
            self.reason = "Eğim fazla; merkezleme kilidi sıfırlandı, alçalma durdu"
            return self._decision(Action("stop"), error=error, height=height)
        vn = c.kp_xy * en - c.kd_xy * t.vn
        ve = c.kp_xy * ee - c.kd_xy * t.ve
        stable = (error <= c.center_tolerance_m and t.horizontal_speed <= c.release_horizontal_speed_mps
                  and abs(t.vd) <= c.release_vertical_speed_mps and t.tilt_deg <= c.release_tilt_deg)
        if self.state == "CENTERING":
            self.reason = "Hedef üstünde kararlı merkezleme bekleniyor"
            held = self.hold.update(target.frame_id, target.captured_at, stable)
            if held >= c.center_hold_s:
                self._state("DESCENDING", now, "Merkez kilidi alındı; kontrollü alçalma")
            return self._decision(self._velocity(t, vn, ve, 0, dt), error=error, height=height,
                                  required=c.center_hold_s)
        if self.state == "DESCENDING":
            if error > c.descent_center_tolerance_m:
                self._state("CENTERING", now, "Merkezden sapma; alçalma durdu, tekrar merkezleniyor")
                self.last_velocity[2] = 0
                return self._decision(self._velocity(t, vn, ve, 0, dt), error=error, height=height)
            height_ok = abs(height - c.target_camera_height_m) <= c.height_tolerance_m
            held = self.hold.update(target.frame_id, target.captured_at, stable and height_ok)
            if held >= c.release_hold_s and not self.release_requested:
                self.release_requested = True
                self._state("RELEASE_PENDING", now, "Kararlı kilit tamamlandı; temsili bırakma kaydı yazılıyor")
                self.last_velocity[:] = 0
                return self._decision(Action("stop"), Action("release", (target.frame_id, error, height)))
            vd = 0.0 if height_ok else c.kp_height * (height - c.target_camera_height_m)
            descent_stable = (error <= c.center_tolerance_m
                              and t.horizontal_speed <= c.release_horizontal_speed_mps
                              and t.tilt_deg <= c.release_tilt_deg)
            if not descent_stable:
                vd = 0.0
                self.last_velocity[2] = 0  # Eğim/hız artışında düşey yumuşatma alçalmayı uzatmaz.
            self.reason = "Bırakma yüksekliğinde kararlı kilit" if height_ok else "Merkez korunarak alçalıyor"
            return self._decision(self._velocity(t, vn, ve, vd, dt), error=error, height=height,
                                  required=c.release_hold_s)
        raise RuntimeError(f"Beklenmeyen durum: {self.state}")

    def _return(self, now: float, t: Telemetry, mission: MissionPlan, dt: float) -> Decision:
        c = self.cfg.control
        if now - self.return_started > c.return_timeout_s:
            return self._abort(now, t, "Son LAND'e geçiş süresi doldu")
        if self.state == "RETURN_CLIMB":
            error = self.return_alt - t.relative_alt_m
            stable = abs(error) < 0.25 and abs(t.vd) < 0.15
            held = self.transit_hold.update(t.position_at, t.position_at, stable)
            if held >= 1.0:
                self._state("RETURN_TRANSIT", now, "Son LAND konumuna arama irtifasında gidiliyor")
            return self._decision(self._velocity(t, 0, 0, -c.kp_height * error, dt))
        if self.state == "RETURN_TRANSIT":
            dn, de = local_distance(t.lat, t.lon, mission.land_lat, mission.land_lon)
            distance = math.hypot(dn, de)
            if distance > self.cfg.mission.max_land_distance_m:
                return self._abort(now, t, "LAND uzaklığı test sınırını aştı")
            held = self.transit_hold.update(t.global_at, t.global_at,
                    distance <= c.return_arrival_m and t.horizontal_speed < 0.25)
            if held >= 1.0:
                self._state("SELECT_LAND", now, "Son LAND görev sırası seçiliyor")
                return self._decision(Action("stop"), Action("mission_current", (mission.land_seq,)))
            return self._decision(self._velocity(t, c.kp_xy * dn - c.kd_xy * t.vn,
                    c.kp_xy * de - c.kd_xy * t.ve,
                    c.kp_height * (t.relative_alt_m - self.return_alt), dt, c.return_speed_mps))
        if self.state == "SELECT_LAND":
            if t.mission_seq == mission.land_seq and t.mission_at > self.entered:
                self._state("HANDOFF_LAND", now, "Son LAND doğrulandı; AUTO inişine devrediliyor")
                return self._decision(Action("stop"), Action("mode", ("AUTO", "GUIDED")))
            if now - self.entered > c.mode_timeout_s:
                return self._abort(now, t, "Son LAND görev sırası doğrulanamadı")
            return self._decision(Action("stop"))
        if self.state == "HANDOFF_LAND":
            if t.mode == "AUTO":
                if t.mission_seq != mission.land_seq:
                    self._state("ABORTED", now, "AUTO yanlış görev sırasıyla başladı")
                    return self._decision(Action("mode", ("LOITER", "AUTO")), Action("revoke"))
                self._state("LANDING", now, "Son LAND otopilotta yürütülüyor")
                return self._decision(Action("revoke"))
            if now - self.entered > c.mode_timeout_s:
                return self._abort(now, t, "AUTO inişine devir doğrulanamadı")
            return self._decision(Action("stop"))
        raise RuntimeError(self.state)
