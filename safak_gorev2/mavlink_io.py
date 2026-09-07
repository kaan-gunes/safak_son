from __future__ import annotations

import glob
import hashlib
import json
import math
import os
import queue
import threading
import time
from collections import deque
from dataclasses import replace

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil

from .config import Config
from .types import Action, MissionItem, MissionPlan, PoseSample, Telemetry


MODE_IDS = {"AUTO": 3, "GUIDED": 4, "LOITER": 5, "RTL": 6, "LAND": 9}
# Gönderilebilen modlar yukarıdaki dar listede kalır; panel tüm bilinen
# ArduCopter modlarını (ör. yerde STABILIZE) gerçek adlarıyla gösterir.
MODE_NAMES = dict(mavutil.mode_mapping_acm)
PARAMETERS = ("MIS_RESTART", "GUID_TIMEOUT", "FLTMODE_CH", "FS_THR_ENABLE",
              "FLTMODE1", "FLTMODE2", "FLTMODE3", "FLTMODE4", "FLTMODE5", "FLTMODE6")
STREAMS = {30: 20, 32: 20, 33: 10, 24: 5, 193: 5, 65: 10, 1: 2, 245: 2, 42: 2}


def rc_slot(pwm: int) -> int | None:
    if not 900 < pwm < 2200:
        return None
    # ArduCopter flight_mode.cpp read_control_switch() eşikleri.
    return next((i for i, bound in enumerate((1231, 1361, 1491, 1621, 1750), 1) if pwm < bound), 6)


def validate_mission(items: list[MissionItem], *, takeoff_mode: str = "auto") -> MissionPlan:
    if takeoff_mode not in ("auto", "manual"):
        raise ValueError("Bilinmeyen kalkış biçimi")
    if len(items) < 3 or [x.seq for x in items] != list(range(len(items))):
        raise ValueError("Görev listesi eksik/sırasız")
    if any(not math.isfinite(x.z) for x in items):
        raise ValueError("Görevde geçersiz irtifa var")
    first_nav = next((x for x in items[1:] if x.command in (16, 17, 18, 19, 21, 22, 82)), None)
    if takeoff_mode == "auto" and (first_nav is None or first_nav.command != 22):
        raise ValueError("İlk navigasyon komutu otonom TAKEOFF olmalı")
    if takeoff_mode == "manual" and (first_nav is None or first_nav.command != 16
                                    or any(x.command == 22 for x in items[1:])):
        raise ValueError("Manuel kalkış test rotası waypoint ile başlamalı ve TAKEOFF içermemeli")
    land = items[-1]
    if land.command != 21 or land.frame not in (3, 6):
        raise ValueError("Son görev maddesi göreli irtifa çerçevesinde NAV_LAND olmalı")
    if land.x == 0 or land.y == 0 or abs(land.x) > 900000000 or abs(land.y) > 1800000000:
        raise ValueError("Son LAND açık ve geçerli koordinat içermeli; 0/0 bulunduğu yere iniş kabul edilmez")
    if any(x.command in (177, 600, 601) for x in items):
        raise ValueError("Bu test sürümünde DO_JUMP/JUMP_TAG rotası desteklenmiyor")
    start = first_nav.seq + 1 if takeoff_mode == "auto" else first_nav.seq
    if not any(x.command == 16 for x in items[start:land.seq]):
        raise ValueError("TAKEOFF ile LAND arasında tarama waypoint'i yok")
    digest = hashlib.sha256(json.dumps([vars(x) for x in items], sort_keys=True).encode()).hexdigest()
    return MissionPlan(tuple(items), first_nav.seq if takeoff_mode == "auto" else None,
                       land.seq, land.x / 1e7, land.y / 1e7, digest)


class TelemetryStore:
    def __init__(self):
        self.lock = threading.RLock()
        self.value = Telemetry()
        self.attitudes = deque(maxlen=200)
        self.positions = deque(maxlen=200)
        self.params: dict[str, float] = {}
        self.mission: MissionPlan | None = None
        self.mission_error: str | None = None
        self.autopilot_confirmed = False
        self.pilot_override = False

    def update(self, **values) -> None:
        with self.lock:
            self.value = replace(self.value, **values)

    def snapshot(self) -> Telemetry:
        with self.lock:
            return self.value

    def pose_at(self, at: float, tolerance: float) -> PoseSample | None:
        def interpolate(samples, angle=False):
            if not samples:
                return None
            before = next((x for x in reversed(samples) if x[0] <= at), None)
            after = next((x for x in samples if x[0] >= at), None)
            if before and after and at - before[0] <= tolerance and after[0] - at <= tolerance:
                if after[0] == before[0]:
                    return before[1:]
                fraction = (at - before[0]) / (after[0] - before[0])
                delta = [b - a for a, b in zip(before[1:], after[1:])]
                if angle:
                    delta = [(v + math.pi) % (2 * math.pi) - math.pi for v in delta]
                return tuple(a + fraction * d for a, d in zip(before[1:], delta))
            nearest = min(samples, key=lambda x: abs(at - x[0]))
            return nearest[1:] if abs(at - nearest[0]) <= tolerance else None
        with self.lock:
            angles = interpolate(self.attitudes, True)
            position = interpolate(self.positions)
        if angles is None or position is None:
            return None
        return PoseSample(at, *angles, *position)

    def preflight_problem(self) -> str | None:
        with self.lock:
            if self.pilot_override:
                return "Pilot kontrolü geri aldı; bu çalıştırmada tekrar devralınmaz"
            if not self.autopilot_confirmed:
                return "ArduCopter quad kimliği doğrulanmadı"
            if not self.value.firmware or not self.value.firmware.startswith("4."):
                return "ArduCopter 4.x firmware kimliği okunamadı"
            missing = [p for p in PARAMETERS if p not in self.params]
            if missing:
                return "Parametreler okunuyor: " + ", ".join(missing)
            if self.params["MIS_RESTART"] != 0:
                return "MIS_RESTART=0 gerekli; mevcut değer AUTO'da görevi baştan başlatabilir"
            if not 0 < self.params["GUID_TIMEOUT"] <= 3:
                return "GUID_TIMEOUT 0–3 saniye aralığında doğrulanmadı"
            if self.params["FS_THR_ENABLE"] == 0:
                return "RC kaybı failsafe'i kapalı"
            if not 1 <= self.params["FLTMODE_CH"] <= 18:
                return "FLTMODE_CH geçerli bir RC kanalı değil"
            if not self.mission:
                return self.mission_error or "AUTO rotası henüz okunmadı"
        return None


class MavlinkLink:
    """Tek iş parçacığı MAVLink okur/yazar; kısa ömürlü hız komutları kuyruğa yığılmaz."""
    def __init__(self, cfg: Config, store: TelemetryStore, allow_control: bool,
                 stop: threading.Event, connection=None):
        self.cfg, self.store, self.allow_control, self.stop = cfg, store, allow_control, stop
        self.connection = connection
        self.thread = None
        self.actions = queue.Queue(maxsize=8)
        self.owned = False
        self.claim_slot = None
        self.expected_modes = {"GUIDED"}
        self.velocity = None
        self.velocity_until = 0.0
        self.last_velocity_sent = 0.0
        self.clock_offset = None
        self.clock_samples = deque(maxlen=30)
        self.timesync_requests: dict[int, float] = {}
        self.last_fc_ms = None
        self.items = {}
        self.mission_count = None
        self.mission_last_request = 0.0
        self.mission_retries = 0
        self.connected_at = None
        self.failure = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self.run, name="pixhawk-link", daemon=True)
        self.thread.start()

    def submit(self, actions: tuple[Action, ...]) -> None:
        if not actions:
            return
        if not self.allow_control:
            raise RuntimeError("Gözlem modunda uçuş komutu reddedildi")
        try:
            self.actions.put_nowait((time.monotonic(), actions))
        except queue.Full:
            self.failure = "Komut kuyruğu doldu"
            self.store.update(link_error=self.failure)

    def _send_velocity(self, v) -> None:
        # BODY_OFFSET_NED hız eksenleri başlığa göredir; sıfır yaw rate, yaw sabit.
        self.connection.mav.set_position_target_local_ned_send(
            int(time.monotonic() * 1000) & 0xffffffff,
            self.cfg.link.target_system, self.cfg.link.target_component,
            9, 1479, 0, 0, 0, *v, 0, 0, 0, 0, 0)

    def _perform(self, now: float, actions: tuple[Action, ...]) -> None:
        t = self.store.snapshot()
        for action in actions:
            if action.kind == "revoke":
                self.owned, self.velocity = False, None
                continue
            if action.kind == "claim":
                if (not self.store.pilot_override and t.mode == "AUTO" and t.armed
                    and t.rc_slot == action.values[0] and t.rc_selected_mode == "AUTO"):
                    self.owned, self.claim_slot = True, t.rc_slot
                    self.expected_modes = {"AUTO", "GUIDED"}
                continue
            if (not self.owned or self.store.pilot_override or t.rc_slot != self.claim_slot
                or t.rc_selected_mode != "AUTO" or not t.rc_healthy or t.system_status != 4
                or now - t.heartbeat_at > self.cfg.control.heartbeat_timeout_s):
                continue
            if action.kind in {"velocity", "stop"}:
                if t.mode == "GUIDED":
                    self.velocity = (0., 0., 0.) if action.kind == "stop" else action.values
                    if not all(math.isfinite(x) for x in self.velocity):
                        raise ValueError("Geçersiz hız komutu")
                    self.velocity_until = now + self.cfg.link.command_lease_s
                    if action.kind == "stop":
                        self._send_velocity(self.velocity)
            elif action.kind == "mode":
                desired, expected = action.values
                if t.mode == expected and desired in MODE_IDS:
                    self.expected_modes = {expected, desired}
                    self.connection.mav.set_mode_send(self.cfg.link.target_system, 1, MODE_IDS[desired])
            elif action.kind == "mission_current":
                if t.mode == "GUIDED" and self.store.mission and action.values[0] == self.store.mission.land_seq:
                    self.connection.mav.mission_set_current_send(
                        self.cfg.link.target_system, self.cfg.link.target_component, action.values[0])
            else:
                raise ValueError(f"İzin verilmeyen uçuş eylemi: {action.kind}")

    def _fc_time(self, time_boot_ms: int, received: float) -> float | None:
        if self.clock_offset is None:
            return None
        if self.last_fc_ms is not None and time_boot_ms + 2000 < self.last_fc_ms:
            self.store.update(rebooted=True)
            self.clock_offset = None
            return None
        self.last_fc_ms = max(time_boot_ms, self.last_fc_ms or 0)
        stamp = time_boot_ms / 1000 + self.clock_offset
        if abs(received - stamp) > 2:
            return None
        return stamp

    def ingest(self, msg, now: float) -> None:
        if msg.get_srcSystem() != self.cfg.link.target_system or msg.get_srcComponent() != self.cfg.link.target_component:
            return
        kind = msg.get_type()
        if kind == "HEARTBEAT":
            self.store.autopilot_confirmed = msg.autopilot == 3 and msg.type == 2
            mode = MODE_NAMES.get(msg.custom_mode, f"MODE_{msg.custom_mode}")
            self.store.update(heartbeat_at=now, mode=mode, armed=bool(msg.base_mode & 128),
                              system_status=msg.system_status)
            if self.owned and mode not in self.expected_modes:
                self.owned, self.velocity = False, None
                self.store.pilot_override = True
        elif kind == "TIMESYNC" and msg.tc1 > 0 and msg.ts1 in self.timesync_requests:
            sent = self.timesync_requests.pop(msg.ts1)
            rtt = now - sent
            if 0 <= rtt <= self.cfg.link.max_timesync_rtt_s:
                offset = (sent + now) / 2 - msg.tc1 / 1e9
                self.clock_samples.append((rtt, offset))
                self.clock_offset = min(self.clock_samples, key=lambda x: x[0])[1]
                self.store.update(timesync_at=now)
        elif kind == "AUTOPILOT_VERSION":
            v = msg.flight_sw_version
            self.store.update(firmware=f"{v >> 24}.{(v >> 16) & 255}.{(v >> 8) & 255}")
        elif kind in {"ATTITUDE", "LOCAL_POSITION_NED", "GLOBAL_POSITION_INT"}:
            stamp = self._fc_time(msg.time_boot_ms, now)
            if stamp is None:
                return
            if kind == "ATTITUDE":
                values = (msg.roll, msg.pitch, msg.yaw)
                if not all(math.isfinite(x) for x in values):
                    return
                with self.store.lock:
                    self.store.attitudes.append((stamp, *values))
                self.store.update(attitude_at=stamp, roll=msg.roll, pitch=msg.pitch, yaw=msg.yaw)
            elif kind == "LOCAL_POSITION_NED":
                values = (msg.x, msg.y, msg.z, msg.vx, msg.vy, msg.vz)
                if not all(math.isfinite(x) for x in values):
                    return
                with self.store.lock:
                    self.store.positions.append((stamp, *values[:3]))
                self.store.update(position_at=stamp, north=msg.x, east=msg.y, down=msg.z,
                                  vn=msg.vx, ve=msg.vy, vd=msg.vz)
            else:
                self.store.update(global_at=stamp, lat=msg.lat / 1e7, lon=msg.lon / 1e7,
                                  relative_alt_m=msg.relative_alt / 1000)
        elif kind == "GPS_RAW_INT":
            self.store.update(gps_at=now, gps_fix=msg.fix_type, satellites=msg.satellites_visible,
                              hdop=msg.eph / 100 if msg.eph != 65535 else None)
        elif kind == "EKF_STATUS_REPORT":
            self.store.update(ekf_at=now, ekf_flags=msg.flags)
        elif kind == "EXTENDED_SYS_STATE":
            self.store.update(landed_at=now, landed=msg.landed_state)
        elif kind == "SYS_STATUS":
            rc_bit = 1 << 16
            healthy = bool(msg.onboard_control_sensors_present & rc_bit
                           and msg.onboard_control_sensors_enabled & rc_bit
                           and msg.onboard_control_sensors_health & rc_bit)
            self.store.update(status_at=now, rc_healthy=healthy, battery_at=now,
                              voltage=msg.voltage_battery / 1000 if msg.voltage_battery != 65535 else None,
                              current=msg.current_battery / 100 if msg.current_battery != -1 else None,
                              battery_percent=msg.battery_remaining if msg.battery_remaining >= 0 else None)
        elif kind == "PARAM_VALUE":
            name = msg.param_id.decode().rstrip("\x00") if isinstance(msg.param_id, bytes) else msg.param_id.rstrip("\x00")
            if name in PARAMETERS and math.isfinite(msg.param_value):
                self.store.params[name] = msg.param_value
        elif kind == "RC_CHANNELS":
            previous = self.store.snapshot()
            channel = int(self.store.params.get("FLTMODE_CH", 0))
            pwm = getattr(msg, f"chan{channel}_raw", 0) if 1 <= channel <= msg.chancount else 0
            slot = rc_slot(pwm)
            selected = MODE_NAMES.get(int(self.store.params.get(f"FLTMODE{slot}", -1)), "UNKNOWN")
            self.store.update(rc_at=now, rc_slot=slot, rc_selected_mode=selected)
            interrupted_auto = (self.allow_control and previous.armed and previous.mode == "AUTO"
                                and previous.rc_selected_mode == "AUTO"
                                and (slot != previous.rc_slot or selected != "AUTO"))
            if interrupted_auto or (self.owned and (slot != self.claim_slot or selected != "AUTO")):
                self.store.pilot_override = True
                self.owned, self.velocity = False, None
        elif kind == "MISSION_CURRENT":
            self.store.update(mission_at=now, mission_seq=msg.seq)
        elif kind == "MISSION_COUNT":
            if getattr(msg, "target_system", 0) not in (0, self.cfg.link.source_system):
                return
            if getattr(msg, "mission_type", 0) != 0 or not 3 <= msg.count <= 1000:
                self.store.mission_error = "Görev sayısı/türü geçersiz"
                return
            if self.store.snapshot().armed and self.store.mission and len(self.store.mission.items) != msg.count:
                self.store.mission = None
                self.store.mission_error = "Uçuş sırasında görev listesi değişti"
                return
            self.items, self.mission_count = {}, msg.count
            self.mission_retries = 0
            self._request_item(0, now)
        elif kind == "MISSION_ITEM_INT" and self.mission_count is not None:
            if (getattr(msg, "target_system", 0) not in (0, self.cfg.link.source_system)
                or getattr(msg, "mission_type", 0) != 0 or not 0 <= msg.seq < self.mission_count):
                return
            self.items[msg.seq] = MissionItem(msg.seq, msg.command, msg.frame, msg.x, msg.y, msg.z)
            self.mission_retries = 0
            missing = next((i for i in range(self.mission_count) if i not in self.items), None)
            if missing is None:
                self.connection.mav.mission_ack_send(self.cfg.link.target_system, self.cfg.link.target_component, 0)
                try:
                    plan = validate_mission([self.items[i] for i in range(self.mission_count)],
                                            takeoff_mode=self.cfg.mission.takeoff_mode)
                    if self.store.mission and self.store.snapshot().armed and self.store.mission.fingerprint != plan.fingerprint:
                        raise ValueError("Uçuş sırasında görev içeriği değişti")
                    self.store.mission, self.store.mission_error = plan, None
                except ValueError as e:
                    self.store.mission, self.store.mission_error = None, str(e)
                self.mission_count = None
            else:
                self._request_item(missing, now)

    def _request_item(self, seq: int, now: float) -> None:
        self.connection.mav.mission_request_int_send(self.cfg.link.target_system, self.cfg.link.target_component, seq)
        self.mission_last_request = now

    def _command(self, command: int, *params) -> None:
        params = (*params, *(0 for _ in range(7 - len(params))))
        self.connection.mav.command_long_send(self.cfg.link.target_system, self.cfg.link.target_component,
                                             command, 0, *params)

    def _initial_requests(self) -> None:
        for mid, hz in STREAMS.items():
            self._command(511, mid, 1e6 / hz)
        self._command(512, 148)
        for name in PARAMETERS:
            self.connection.mav.param_request_read_send(self.cfg.link.target_system,
                        self.cfg.link.target_component, name.encode(), -1)
        self.connection.mav.mission_request_list_send(self.cfg.link.target_system, self.cfg.link.target_component)

    def run(self) -> None:
        try:
            if self.connection is None:
                device = self.cfg.link.device
                if not device:
                    devices = sorted(glob.glob("/dev/serial/by-id/*"))
                    if len(devices) != 1:
                        raise RuntimeError("Tek bir USB seri cihaz seçilemiyor; link.device yolunu belirtin")
                    device = devices[0]
                self.connection = mavutil.mavlink_connection(device, baud=self.cfg.link.baud,
                        source_system=self.cfg.link.source_system, source_component=self.cfg.link.source_component,
                        dialect="ardupilotmega", autoreconnect=False)
            last_heartbeat = last_sync = last_requests = -math.inf
            initialized = False
            while not self.stop.is_set():
                now = time.monotonic()
                # Yoğun telemetri, RC okumasını veya komut son kullanma kontrolünü aç bırakmaz.
                for _ in range(60):
                    msg = self.connection.recv_match(blocking=False)
                    if msg is None:
                        break
                    self.ingest(msg, time.monotonic())
                t = self.store.snapshot()
                if now - last_heartbeat >= 1:
                    self.connection.mav.heartbeat_send(18, 8, 0, 0, 4)
                    last_heartbeat = now
                if self.store.autopilot_confirmed:
                    if not initialized:
                        self._initial_requests()
                        initialized, last_requests = True, now
                    if now - last_sync >= 0.5:
                        stamp = time.monotonic_ns()
                        self.timesync_requests[stamp] = stamp / 1e9
                        self.timesync_requests = {k: v for k, v in self.timesync_requests.items() if now - v < 3}
                        self.connection.mav.timesync_send(0, stamp)
                        last_sync = now
                    if now - last_requests >= 5:
                        for name in PARAMETERS:
                            if name not in self.store.params:
                                self.connection.mav.param_request_read_send(self.cfg.link.target_system,
                                    self.cfg.link.target_component, name.encode(), -1)
                        if not t.firmware:
                            self._command(512, 148)
                        if not self.store.mission and self.mission_count is None:
                            self.connection.mav.mission_request_list_send(self.cfg.link.target_system,
                                                                         self.cfg.link.target_component)
                        last_requests = now
                    if self.mission_count is not None and now - self.mission_last_request > 1:
                        self.mission_retries += 1
                        if self.mission_retries > 5:
                            self.store.mission_error = "AUTO görevi indirme zaman aşımı"
                            self.mission_count = None
                        else:
                            seq = next(i for i in range(self.mission_count) if i not in self.items)
                            self._request_item(seq, now)
                for _ in range(8):
                    try:
                        created, actions = self.actions.get_nowait()
                    except queue.Empty:
                        break
                    if now - created < self.cfg.link.command_lease_s:
                        self._perform(now, actions)
                    elif any(a.kind == "revoke" for a in actions):
                        self.owned, self.velocity = False, None
                if self.owned and self.velocity is not None and t.mode == "GUIDED":
                    if now > self.velocity_until or self.failure:
                        self._send_velocity((0., 0., 0.))
                        if t.rc_slot == self.claim_slot and t.system_status == 4:
                            self.connection.mav.set_mode_send(self.cfg.link.target_system, 1, MODE_IDS["LOITER"])
                        self.owned, self.velocity = False, None
                        self.store.update(link_error="Kontrol döngüsü komut süresini aştı")
                    elif now - self.last_velocity_sent >= 0.05:
                        self._send_velocity(self.velocity)
                        self.last_velocity_sent = now
                self.stop.wait(0.01)
        except Exception as e:
            self.failure = f"Pixhawk bağlantısı: {e}"
            self.store.update(link_error=self.failure)
        finally:
            if self.connection is not None:
                t = self.store.snapshot()
                try:
                    if (self.allow_control and self.owned and t.mode == "GUIDED"
                        and not self.store.pilot_override and t.rc_slot == self.claim_slot):
                        self._send_velocity((0., 0., 0.))
                        self.connection.mav.set_mode_send(self.cfg.link.target_system, 1, MODE_IDS["LOITER"])
                finally:
                    self.connection.close()
