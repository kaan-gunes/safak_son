import threading
import time
import json
from dataclasses import replace
from unittest.mock import Mock

import pytest
from pymavlink.dialects.v20 import ardupilotmega as mav

from safak_gorev2.mavlink_io import MavlinkLink, TelemetryStore, validate_mission
from safak_gorev2.shared import EventLedger, SharedState
from safak_gorev2.types import Action, Decision, Detection, Frame
from safak_gorev2.web import create_app
from conftest import telemetry


def sourced(msg, sysid=1, compid=1):
    msg._header.srcSystem, msg._header.srcComponent = sysid, compid
    return msg


def test_ledger_is_durable_and_only_once(tmp_path):
    ledger = EventLedger(tmp_path, "same-sortie")
    assert ledger.release_once({"frame": 1})
    reopened = EventLedger(tmp_path, "same-sortie")
    assert not reopened.release_once({"frame": 2})
    assert EventLedger(tmp_path, "different-sortie").release_once({"frame": 3})


def test_reject_land_here_and_missing_terminal_land(mission):
    for changes in ({"x":0,"y":0}, {"command":16}, {"frame":0}):
        items = list(mission.items)
        items[-1] = replace(items[-1], **changes)
        with pytest.raises(ValueError):
            validate_mission(items)


def test_observe_refuses_control_commands(cfg):
    link = MavlinkLink(cfg, TelemetryStore(), False, threading.Event(), Mock())
    with pytest.raises(RuntimeError):
        link.submit((Action("mode", ("GUIDED", "AUTO")),))


def test_pilot_rc_override_revokes_link_before_control_loop(cfg):
    store = TelemetryStore()
    store.value = telemetry(100.)
    store.params.update({"FLTMODE_CH":5, "FLTMODE1":5, "FLTMODE6":3})
    connection = Mock()
    link = MavlinkLink(cfg, store, True, threading.Event(), connection)
    link._perform(100., (Action("claim", (6,)), Action("mode", ("GUIDED","AUTO"))))
    assert connection.mav.set_mode_send.call_count == 1
    rc = mav.MAVLink_rc_channels_message(100000, 8, *([1500]*4 + [1000] + [1500]*13), 200)
    link.ingest(sourced(rc), 100.1)
    assert store.pilot_override
    link._perform(100.1, (Action("mode", ("GUIDED", "AUTO")),))
    assert connection.mav.set_mode_send.call_count == 1


def test_wrong_system_heartbeat_ignored(cfg):
    store = TelemetryStore()
    link = MavlinkLink(cfg, store, False, threading.Event(), Mock())
    link.ingest(sourced(mav.MAVLink_heartbeat_message(2,3,128,3,4,3), 42), 100.)
    assert not store.autopilot_confirmed


def test_timesync_matches_boot_time_not_receive_time(cfg):
    store = TelemetryStore()
    link = MavlinkLink(cfg, store, False, threading.Event(), Mock())
    request = 100_000_000_000
    link.timesync_requests[request] = 100.
    # ArduCopter 4.6.3 GCS_Common.cpp: tc1 = FC receive time, ts1 = echoed request.
    link.ingest(sourced(mav.MAVLink_timesync_message(10_010_000_000, request)), 100.02)
    assert link._fc_time(10020, 100.08) == pytest.approx(100.02)


def test_read_only_flask_has_no_command_endpoint(cfg):
    state, store = SharedState("observe"), TelemetryStore()
    client = create_app(cfg, state, store).test_client()
    assert client.get("/").status_code == 200
    assert client.get("/api/status").json["ages_s"]["heartbeat"] is None
    assert client.post("/api/status").status_code == 405
    for route in ("/arm", "/release", "/mode", "/api/command"):
        assert client.post(route).status_code == 404
    assert client.get("/frame.jpg").status_code == 204


def test_velocity_packet_is_body_heading_frame_and_zero_yaw_rate(cfg):
    connection = Mock()
    link = MavlinkLink(cfg, TelemetryStore(), True, threading.Event(), connection)
    link._send_velocity((.1, -.2, .05))
    args = connection.mav.set_position_target_local_ned_send.call_args.args
    assert args[3:5] == (9, 1479)
    assert args[8:11] == (.1,-.2,.05)
    assert args[-1] == 0


def test_panel_health_never_calls_missing_or_stale_vision_ready(cfg, monkeypatch):
    state, store = SharedState("flight"), TelemetryStore()
    monkeypatch.setattr(type(cfg), "flight_missing", lambda self: [])
    monkeypatch.setattr(store, "preflight_problem", lambda: None)
    store.value = telemetry(time.monotonic())
    state.decision = Decision("SEARCHING", "Test")
    client = create_app(cfg, state, store).test_client()
    assert client.get("/healthz").json["flight_ready"] is False
    state.backend, state.frame_id, state.frame_at = "HAILO", 1, time.monotonic()
    assert client.get("/healthz").json["flight_ready"] is True
    state.frame_at -= 1
    assert client.get("/healthz").json["flight_ready"] is False
    state.frame_at = time.monotonic()
    store.value = replace(store.value, position_at=time.monotonic() - 1)
    assert client.get("/healthz").json["flight_ready"] is False


def test_calibration_png_preserves_source_size_and_rejects_stale_or_flight(cfg):
    import cv2
    import numpy as np
    state, store = SharedState("observe"), TelemetryStore()
    source = np.zeros((720,1280,3),np.uint8)
    source[200:400,300:600] = (220,30,10)
    now = time.monotonic()
    detection = Detection("mavi_hedef",.51,(.23,.27,.47,.56),2)
    frame = Frame(7,now,now,source,(detection,))
    state.vision(frame,(),"calibration")
    state.camera_info = {"width":1280,"height":720,"model":"imx219",
                         "scaler_crop":[680,692,1920,1080],"mirror":False}
    client = create_app(cfg,state,store).test_client()
    response = client.get("/calibration/frame.png")
    assert response.status_code == 200
    decoded = cv2.imdecode(np.frombuffer(response.data,np.uint8),cv2.IMREAD_COLOR)
    assert np.array_equal(decoded,source)
    assert json.loads(response.headers["X-Camera-Meta"])["width"] == 1280
    assert response.headers["X-Frame-Id"] == "7"
    assert response.headers["X-Frame-Backend"] == "HAILO"
    assert float(response.headers["X-Stream-Id"]) == state.started
    recorded = json.loads(response.headers["X-Detections"])
    assert recorded == [{"label":"mavi_hedef","confidence":.51,
                         "bbox":[.23,.27,.47,.56],"class_id":2}]
    vision = client.get("/api/status").json["vision"]
    assert vision["frame_id"] == 7 and vision["detections"] == recorded
    assert vision["confidence_required"] == .65
    state.calibration_frame = replace(frame,captured_at=now-1)
    assert client.get("/calibration/frame.png").status_code == 503
    state.mode = "flight"
    assert client.get("/calibration/frame.png").status_code == 403


def test_auto_search_rc_override_rejects_queued_claim_before_guided(cfg):
    store=TelemetryStore();store.value=telemetry(100.)
    store.params.update({'FLTMODE_CH':5,'FLTMODE1':5,'FLTMODE6':3})
    connection=Mock();link=MavlinkLink(cfg,store,True,threading.Event(),connection)
    assert not link.owned
    rc=mav.MAVLink_rc_channels_message(100000,8,*([1500]*4+[1000]+[1500]*13),200)
    link.ingest(sourced(rc),100.1)
    assert store.pilot_override and not link.owned
    store.update(mode='AUTO',rc_slot=6,rc_selected_mode='AUTO')
    link._perform(100.2,(Action('claim',(6,)),Action('mode',('GUIDED','AUTO'))))
    assert not link.owned and connection.mav.set_mode_send.call_count==0
