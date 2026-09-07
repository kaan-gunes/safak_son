"""Yalnız kendi başlattığı yerel ArduCopter SITL sürecini uçuran entegrasyon deneyi.

Gerçek Pi/Pixhawk adresi kabul etmez. AI kutuları ve kamera kalibrasyonu sentetiktir;
ArduCopter navigasyon, modlar, görev protokolü ve telemetri gerçekte SITL'de çalışır.
"""
from __future__ import annotations

import argparse
import json
import math
import socket
import subprocess
import sys
import threading
import time
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from pymavlink import mavutil

from safak_gorev2.config import Config
from safak_gorev2.demo import demo_calibration
from safak_gorev2.geometry import CAMERA_TO_BODY, TargetGeometry, body_to_ned
from safak_gorev2.mavlink_io import MavlinkLink
from safak_gorev2.runtime import Runtime
from safak_gorev2.shared import finite_json
from safak_gorev2.types import Detection, Frame


def wait_message(conn, kinds, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        msg = conn.recv_match(type=kinds, blocking=True, timeout=.2)
        if msg is not None:
            return msg
    raise TimeoutError(str(kinds))


def send_command(conn, command, *params):
    conn.mav.command_long_send(1, 1, command, 0, *params, *([0] * (7 - len(params))))


def upload_mission(conn, takeoff_mode="auto"):
    # Yalnız loopback'te, bu dosyanın başlattığı SITL için test rotası.
    values = [(16,0,410000000,290000000,0), (22,3,0,0,6),
              (16,3,410000000,290001430,6), (21,3,410000000,290000000,0)]
    if takeoff_mode == "manual":
        del values[1]
    conn.mav.mission_count_send(1, 1, len(values))
    for _ in range(15):
        msg = wait_message(conn, ["MISSION_REQUEST_INT", "MISSION_REQUEST", "MISSION_ACK"])
        if msg.get_type() == "MISSION_ACK":
            if msg.type != 0:
                raise RuntimeError(f"SITL mission ACK: {msg.type}")
            return
        command, frame, lat, lon, alt = values[msg.seq]
        conn.mav.mission_item_int_send(1,1,msg.seq,frame,command,0,1,0,0,0,0,lat,lon,alt)
    raise RuntimeError("SITL görev yüklemesi tamamlanmadı")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ardupilot", type=Path, required=True)
    parser.add_argument("--scenario", choices=("complete", "pilot", "pilot-search", "lost-target", "control-stall"), default="complete")
    parser.add_argument("--takeoff-mode", choices=("auto", "manual"), default="auto")
    parser.add_argument("--return-mode", choices=("land", "rtl"), default="land")
    parser.add_argument("--output", type=Path, default=Path("artifacts/sitl"))
    args = parser.parse_args()
    args.output = args.output.resolve() / args.scenario
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.ardupilot.resolve() / "build/sitl/bin/arducopter"
    if not binary.is_file():
        raise RuntimeError("Derlenmiş yerel SITL arducopter dosyası bulunamadı")
    for port in (5790,5792):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1",port))  # Var olan başka sürece bağlanmayı reddet.
    defaults = args.output / "sitl-only.parm"
    defaults.write_text("\n".join(["SERIAL1_PROTOCOL 2", "MIS_RESTART 0", "GUID_TIMEOUT 1",
        "FLTMODE_CH 5", "FLTMODE1 5", "FLTMODE6 3", "FS_THR_ENABLE 3", "AUTO_OPTIONS 3",
        "WPNAV_SPEED 80", "WPNAV_ACCEL 80", "SIM_GPS_DELAY 0", "SIM_GPS_GLITCH_X 0"]) + "\n")
    log = (args.output / "autopilot.log").open("w")
    proc = subprocess.Popen([str(binary), "--model", "quad", "--home", "41,29,50,0", "--speedup", "1",
        "--serial0", "tcp:5790", "--serial1", "tcp:5792", "--rc-in-port", "5799", "--wipe",
        "--defaults", str(args.ardupilot / "Tools/autotest/default_params/copter.parm") + "," + str(defaults)],
        cwd=args.output, stdout=log, stderr=subprocess.STDOUT)
    runtime = None
    ground = None
    stop = threading.Event()
    rc_slot_pwm = [1000 if args.takeoff_mode == "manual" else 2000]
    rc_throttle_pwm = [1000]
    try:
        deadline = time.monotonic() + 15
        while True:
            if proc.poll() is not None:
                raise RuntimeError("SITL erken kapandı; autopilot.log dosyasını inceleyin")
            try:
                ground = mavutil.mavlink_connection("tcp:127.0.0.1:5790", source_system=255, source_component=190)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(.1)
        # İlk HEARTBEAT, mission.init() öncesinde BOOT durumunda gelebilir;
        # bu sırada görev kapasitesi henüz sıfırdır.
        boot_deadline = time.monotonic() + 30
        while wait_message(ground, "HEARTBEAT").system_status == 1:
            if time.monotonic() > boot_deadline:
                raise TimeoutError("SITL BOOT durumundan çıkmadı")
        def pilot_radio():
            while not stop.wait(.1):
                ground.mav.heartbeat_send(6,8,0,0,4)
                ground.mav.rc_channels_override_send(1,1,1500,1500,rc_throttle_pwm[0],1500,rc_slot_pwm[0],1500,1500,1500)
        threading.Thread(target=pilot_radio,daemon=True).start()
        upload_mission(ground, args.takeoff_mode)
        cfg = Config()
        cfg = replace(cfg, camera=replace(cfg.camera, offset_body_m=(-.03,0,.05)),
            mission=replace(cfg.mission, direct_land_corridor_checked=True, takeoff_mode=args.takeoff_mode,
                            return_mode=args.return_mode),
            link=replace(cfg.link, device="tcp:127.0.0.1:5792"), runtime_dir=str(args.output / "runtime"))
        runtime = Runtime(cfg, "sitl")
        cal = demo_calibration()
        geometry = TargetGeometry(cfg.camera, cal)
        runtime.geometry_override = geometry
        runtime.link = MavlinkLink(cfg, runtime.telemetry, True, runtime.stop)
        runtime.link.start()
        runtime.start(connect=False)
        hidden = [False]

        def synthetic_camera():
            fid, last_at = 0, -1
            target_position = np.array([0.,4.,0.])
            while not stop.wait(.04):
                t = runtime.telemetry.snapshot()
                captured_at = min(t.attitude_at, t.position_at)
                if captured_at <= last_at:
                    continue
                pose = runtime.telemetry.pose_at(captured_at, .1)
                if pose is None:
                    continue
                last_at = captured_at
                image = np.full((720,1280,3),(55,70,55),np.uint8)
                r = body_to_ned(pose.roll,pose.pitch,pose.yaw)
                tv = CAMERA_TO_BODY.T @ (r.T @ (target_position - np.array([pose.north,pose.east,pose.down]))
                                         - np.array(cfg.camera.offset_body_m))
                detections = []
                if tv[2] > 1 and not hidden[0]:
                    ro = np.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,-1.]])
                    rv,_ = cv2.Rodrigues(CAMERA_TO_BODY.T @ r.T @ ro)
                    q,_ = cv2.projectPoints(geometry.object_points,rv,tv,cal.matrix,cal.distortion)
                    q = q.reshape(4,2)
                    if np.isfinite(q).all() and np.max(np.abs(q)) < 100000:
                        cv2.fillConvexPoly(image,q.astype(np.int32),(210,70,20))
                        box = tuple(np.clip(np.array([*q.min(axis=0),*q.max(axis=0)])/[1280,720,1280,720],0,1))
                        detections = [Detection("mavi_hedef",.95,box,2)]
                fid += 1
                runtime.mailbox.put(Frame(fid,captured_at,time.monotonic(),image,tuple(detections),"SITL · SENTETİK KAMERA"))
        threading.Thread(target=synthetic_camera,daemon=True).start()
        deadline = time.monotonic()+45
        last_preflight_log = -math.inf
        while time.monotonic()<deadline:
            t=runtime.telemetry.snapshot()
            problem=runtime.telemetry.preflight_problem()
            if problem is None and t.gps_fix and t.gps_fix>=3 and t.ekf_flags&23==23 and t.rc_healthy:
                break
            if time.monotonic() - last_preflight_log >= 5:
                print("SITL hazırlık:",problem,"GPS",t.gps_fix,"EKF",t.ekf_flags,"RC",t.rc_healthy,flush=True)
                last_preflight_log = time.monotonic()
            time.sleep(.2)
        else:
            raise RuntimeError("SITL ön koşulları: "+str(problem)+" "+json.dumps(finite_json(asdict(t))))
        ground.mav.set_mode_send(1,1,5 if args.takeoff_mode == "manual" else 3)
        send_command(ground,400,1)
        if args.takeoff_mode == "manual":
            # Yalnız bu süreçteki SITL: pilot RC gazıyla Loiter kalkışı, sonra AUTO.
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                t = runtime.telemetry.snapshot()
                if t.armed:
                    rc_throttle_pwm[0] = 1650
                if t.armed and t.landed == 2 and t.relative_alt_m >= 6:
                    rc_throttle_pwm[0] = 1500
                    rc_slot_pwm[0] = 2000
                    ground.mav.set_mode_send(1,1,3)
                    break
                if runtime.link.owned or runtime.state.release:
                    raise RuntimeError("Manuel kalkışta uygulama kontrol devraldı")
                time.sleep(.1)
            else:
                raise TimeoutError("SITL pilot RC kalkışı tamamlanamadı")
        state_before=None
        start=time.monotonic()
        injection=False
        injection_at=None
        result={"scenario":args.scenario,"takeoff_mode":args.takeoff_mode,"return_mode":args.return_mode,
                "firmware":t.firmware,"synthetic_vision":True,"states":[]}
        while time.monotonic()-start<210:
            d=runtime.state.decision
            t=runtime.telemetry.snapshot()
            if t.armed and t.landed == 2:
                rc_throttle_pwm[0] = 1500  # Loiter'a devirde pilot gazı nötr; iniş stick'i uygulanmaz.
            if injection_at is not None and t.mode == "LOITER" and "loiter_latency_s" not in result:
                result["loiter_latency_s"] = time.monotonic() - injection_at
            if d.state!=state_before:
                item={"state":d.state,"reason":d.reason,"elapsed_s":time.monotonic()-start,
                      "mode":t.mode,"mission_seq":t.mission_seq,"height":t.relative_alt_m}
                result["states"].append(item)
                print(json.dumps(item,ensure_ascii=False),flush=True)
                state_before=d.state
            if (d.state=="DESCENDING" or (args.scenario=="pilot-search" and d.state=="SEARCHING")) and not injection:
                if args.scenario in {"pilot", "pilot-search"}:
                    rc_slot_pwm[0]=1000
                    injection=True
                elif args.scenario=="lost-target":
                    hidden[0]=True
                    injection=True
                elif args.scenario=="control-stall":
                    original_step = runtime.controller.step
                    def stalled_step(*values, **keywords):
                        stop.wait(2)
                        runtime.controller.step = original_step
                        return original_step(*values, **keywords)
                    runtime.controller.step = stalled_step
                    injection=True
                if injection:
                    injection_at = time.monotonic()
            if d.state in {"DONE","ABORTED","PILOT_CONTROL"}:
                # Çekirdeğin devri kadar gerçek FC'nin modu ve tekrar devralmaması da ölçülür.
                if args.scenario != "complete":
                    settle_until = time.monotonic() + 3
                    while time.monotonic() < settle_until:
                        time.sleep(.1)
                        if runtime.state.decision.state != d.state or runtime.state.release:
                            raise RuntimeError("İptal sonrası kontrol yeniden devralındı veya bırakma oluştu")
                    t = runtime.telemetry.snapshot()
                    if t.mode != "LOITER" or runtime.link.owned:
                        raise RuntimeError("İptal sonrası gerçek SITL LOITER/kontrol devri doğrulanamadı")
                    if "loiter_latency_s" not in result:
                        result["loiter_latency_s"] = None  # Durum döngüsünden sonra gözlendi; uydurulmaz.
                result["final_state"]=d.state
                result["release"]=runtime.state.release
                result["final_telemetry"]=finite_json(asdict(t))
                expected={"complete":{"DONE"},"pilot":{"PILOT_CONTROL"},"pilot-search":{"PILOT_CONTROL"},"lost-target":{"ABORTED"},
                          "control-stall":{"ABORTED", "PILOT_CONTROL"}}[args.scenario]
                if d.state not in expected or (args.scenario=="complete") != bool(runtime.state.release):
                    raise RuntimeError("Beklenmeyen SITL sonucu: "+json.dumps(result,ensure_ascii=False))
                (args.output/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
                print("SITL PASS:",args.scenario,flush=True)
                return
            time.sleep(.1)
        raise TimeoutError("SITL senaryosu tamamlanmadı; son karar: "+str(runtime.state.decision))
    finally:
        stop.set()
        if runtime:
            runtime.close()
        if ground:
            ground.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        log.close()


if __name__=="__main__":
    main()
