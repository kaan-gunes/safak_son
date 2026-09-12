from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import Mock
import sys
from types import SimpleNamespace
import pytest
from safak_gorev2.competition.config import Options
from safak_gorev2.camera_contract import capture_missing, metric_missing, camera_manifest
from safak_gorev2.hailo_backend import create_picamera
from safak_gorev2.record import profile_manifest, verify_recording_source
from safak_gorev2.competition.route import mission_digest, mission_digest_problem
from safak_gorev2.competition.vision import DualVision
from safak_gorev2.types import Frame
import numpy as np


def test_profiles_separate_and_approximate():
    imx, a = Options.load('config/ana-imx708.json')
    usb, b = Options.load('config/ana-arducam.json')
    assert a.strategy == b.strategy == 'center'
    assert a.actuator == 'servo' and b.actuator == 'simulated'
    assert all(s.bench_verified for o in (a,b) for s in o.servos.values())
    assert imx.camera.identity == 'imx708' and imx.camera.lens_position == 0
    assert usb.camera.calibration_file is usb.camera.sensor_output_size is usb.camera.lens_position is None
    assert usb.camera.identity.endswith("SN0001")
    assert usb.camera.usb_vid_pid == "0c40:0559"
    assert (usb.camera.width,usb.camera.height,usb.camera.fps)==(1920,1080,50)
    assert usb.camera.offset_body_m is b.camera_mount_yaw_deg is None
    assert imx.runtime_dir != usb.runtime_dir
    assert not capture_missing(usb.camera) and metric_missing(usb.camera)
    assert capture_missing(replace(usb.camera,identity=None,device=None,pixel_format=None))
    m = camera_manifest(imx.camera)
    assert not m['physical_distance_verified'] and not m['focus_transfer_verified']
    assert m['calibration_capture_lens_position'] == pytest.approx(.1062771082)


@pytest.mark.parametrize('change', [dict(backend='picamera2'),dict(lens_position=0.),
    dict(sensor_output_size=(2304,1296)),dict(calibration_file='config/camera.imx708-infinity-approx.json')])
def test_arducam_rejects_imx_settings(change):
    cfg,_=Options.load('config/ana-arducam.json')
    with pytest.raises(ValueError):
        replace(cfg,camera=replace(cfg.camera,**change)).validate()


def test_imx_missing_identity_and_wrong_backend_rejected():
    cfg,_=Options.load('config/ana-imx708.json')
    for change in (dict(identity=None),dict(identity='usb'),dict(backend='v4l2-observe')):
        with pytest.raises(ValueError):
            replace(cfg,camera=replace(cfg.camera,**change)).validate()


def test_physical_wrong_camera_fails_before_configure(monkeypatch):
    cfg,_=Options.load('config/ana-imx708.json')
    cam=Mock(camera_properties={'Model':'imx219'})
    monkeypatch.setitem(sys.modules,'picamera2',SimpleNamespace(Picamera2=lambda:cam))
    monkeypatch.setitem(sys.modules,'libcamera',SimpleNamespace(Transform=None,controls=None))
    with pytest.raises(ValueError,match='kimliği'):
        create_picamera(cfg)
    cam.configure.assert_not_called()
    cam.close.assert_called_once()


def test_arducam_null_calibration_no_metric_and_no_flight():
    from safak_gorev2.competition.runtime import CompetitionRuntime
    cfg, opts=Options.load('config/ana-arducam.json')
    vision=DualVision(cfg,None,opts.camera_mount_yaw_deg)
    assert not vision.geometry
    frame=Frame(1,1.,1.,np.zeros((720,1280,3),np.uint8),())
    candidates,_=vision.detect(frame,None,'center')
    assert not any(c.metric for c in candidates)
    with pytest.raises(ValueError,match='yalnız gözlem'):
        CompetitionRuntime(cfg,'flight',opts)


def test_digest_contract_and_altitude_waypoint_changes(mission):
    assert mission_digest_problem(mission, mission.fingerprint)
    assert 'MissionPlan.fingerprint' in mission_digest_problem(mission,mission.fingerprint)
    digest=mission_digest(mission)
    assert mission_digest_problem(mission,digest) is None
    for change in (dict(z=10.),dict(x=mission.items[2].x+1)):
        altered=replace(mission,items=tuple(replace(x,**change) if x.seq==2 else x for x in mission.items))
        assert mission_digest_problem(altered,digest)


def test_recorder_profile_and_active_identity_match():
    imx=profile_manifest('config/ana-imx708.json')
    usb=profile_manifest('config/ana-arducam.json')
    assert imx['vision_backend'] == usb['vision_backend'] == 'opencv-color'
    assert 'hef_file' not in imx and 'hef_sha256' not in imx
    assert imx['camera_contract']['calibration_sha256'] and usb['camera_contract']['calibration_sha256'] is None
    verify_recording_source(imx, dict(imx,camera_actual={'identity':'imx708','backend':'picamera2'}))
    with pytest.raises(ValueError,match='profile_digest|camera_contract'):
        verify_recording_source(imx,usb)
    with pytest.raises(ValueError):
        verify_recording_source(imx,{})


def test_usb_wrong_identity_does_not_open_camera(monkeypatch):
    from safak_gorev2.v4l2_camera import V4L2Camera
    cfg,_=Options.load('config/ana-arducam.json')
    cfg=replace(cfg,camera=replace(cfg.camera,device='/dev/v4l/by-id/test',identity='expected',usb_vid_pid='1234:5678',pixel_format='MJPG'))
    monkeypatch.setattr('safak_gorev2.v4l2_camera.usb_identity',lambda _:('other','1234:5678'))
    factory=Mock();monkeypatch.setattr('safak_gorev2.v4l2_camera.cv2.VideoCapture',factory)
    with pytest.raises(ValueError): V4L2Camera(cfg)
    factory.assert_not_called()


def test_main_requires_six_fresh_common_metric_frames_and_half_second(cfg,mission):
    from test_competition import ready, candidate
    from conftest import telemetry
    cfg=replace(cfg,control=replace(cfg.control,acquire_frames=6,acquire_s=.5))
    options=Options(strategy='center',mission_fingerprint=mission_digest(mission),search_start_seq=2,search_end_seq=2,
        entry_gates=(((40.999,29.),(41.001,29.)),),
        flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)))
    c=ready(cfg,options,mission);mode='AUTO'
    for i in range(100):
        at=100+i*.05
        d=c.step(at,telemetry(at,mode=mode),(candidate(i,at,metric=True),),i,at,mission)
        for a in d.actions:
            if a.kind=='mode': mode=a.values[0]
        if c.state=='VERIFYING':break
    assert c.state=='VERIFYING'
    for j in range(6):
        at+=.1
        fid=i+j+1
        c.step(at,telemetry(at,mode=mode),(candidate(fid,at,metric=True),),fid,at,mission)
        if j<5: assert c.state=='VERIFYING'
    assert c.state=='INTERCEPT'


@pytest.mark.parametrize('alt,stopped',[(9.49,False),(9.5,True),(10.,True)])
def test_ten_meter_route_intercept_limit(cfg,mission,alt,stopped):
    from test_competition import ready,candidate
    from conftest import telemetry
    cfg=replace(cfg,control=replace(cfg.control,minimum_intercept_relative_alt_m=9.5))
    options=Options(strategy='center',mission_fingerprint=mission_digest(mission),search_start_seq=2,search_end_seq=2,
        entry_gates=(((40.999,29.),(41.001,29.)),),
        flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)))
    c=ready(cfg,options,mission);claims=[]
    for i in range(3):
        at=100+i*.05
        d=c.step(at,telemetry(at,relative_alt_m=alt),(candidate(i,at,metric=True),),i,at,mission)
        claims.extend(a for a in d.actions if a.kind=='claim')
    assert bool(claims)==stopped


def test_null_mount_loads_but_is_never_ready():
    cfg,opts=Options.load('config/ana-arducam.json')
    assert 'ölçülmüş kamera montaj yönü' in opts.missing(cfg)


def test_actual_profile_digest_detects_model_and_control_changes():
    from safak_gorev2.camera_contract import profile_digest
    cfg,o=Options.load('config/ana-imx708.json')
    digest=profile_digest(cfg,o)
    assert profile_digest(replace(cfg,control=replace(cfg.control,acquire_s=.7)),o)!=digest
    assert profile_digest(replace(cfg,hef_sha256='0'*64),o)!=digest


def test_arducam_link_refuses_payload_even_in_simulation(cfg,mission,tmp_path,monkeypatch):
    from test_competition import link_ready
    from conftest import telemetry
    from safak_gorev2.types import Action
    camera,_=Options.load('config/ana-arducam.json')
    cfg=replace(cfg,camera=camera.camera)
    options=Options(strategy='center',mission_fingerprint=mission_digest(mission),search_start_seq=2,search_end_seq=2,
        flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)))
    link,conn,ledger=link_ready(cfg,options,mission,tmp_path)
    link.store.value=telemetry(100,mode='GUIDED');link.owned=True;link.claim_slot=6
    link._perform(100,(Action('payload',('kirmizi','mavi',1,100,'GUIDED')),))
    assert link.snapshot_status()['kirmizi']=='BLOCKED' and not ledger.statuses()
    conn.mav.command_long_send.assert_not_called()


def test_simulated_payload_has_no_mavlink_and_is_persistent_once(cfg,mission,tmp_path,monkeypatch):
    from test_competition import link_ready
    from conftest import telemetry
    from safak_gorev2.types import Action
    options=Options(strategy='center',actuator='simulated',mission_fingerprint=mission_digest(mission),
        search_start_seq=2,search_end_seq=2,
        flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)))
    link,conn,ledger=link_ready(cfg,options,mission,tmp_path)
    link.store.value=telemetry(100,mode='GUIDED');link.owned=True;link.claim_slot=6
    monkeypatch.setattr('safak_gorev2.competition.link.time.monotonic',lambda:100.)
    action=__import__('safak_gorev2.types',fromlist=['Action']).Action('payload',('kirmizi','mavi',1,100,'GUIDED'))
    link._perform(100,(action,action))
    assert ledger.statuses()=={'kirmizi':'SIMULATED'}
    assert not conn.mav.method_calls
    with ledger.connect() as db:
        rows=db.execute('SELECT sortie,color,status,body FROM payloads').fetchall()
    assert len(rows)==1 and rows[0][:3]==('flight','kirmizi','SIMULATED')
    assert json.loads(rows[0][3])['target']=='mavi'


def test_profile_loader_rejects_implicit_camera(tmp_path):
    from dataclasses import asdict
    cfg,_=Options.load('config/ana-imx708.json')
    base=asdict(cfg);base['camera']['variant']=None
    b=tmp_path/'base.json';b.write_text(json.dumps(base))
    options=json.loads(Path('config/ana-imx708.json').read_text());options['base_config']=str(b)
    p=tmp_path/'profile.json';p.write_text(json.dumps(options))
    with pytest.raises(ValueError,match='kamera variant'):
        Options.load(p)


def test_wrong_resume_general_fingerprint_is_rejected(cfg,mission,tmp_path):
    from test_competition import link_ready
    from conftest import telemetry
    from safak_gorev2.types import Action
    o=Options(mission_fingerprint=mission_digest(mission),search_start_seq=2,search_end_seq=2,
        flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)))
    link,conn,_=link_ready(cfg,o,mission,tmp_path)
    link.store.value=telemetry(100,mode='GUIDED');link.owned=True;link.claim_slot=6
    link._perform(100,(Action('resume',(2,mission.fingerprint)),))
    conn.mav.mission_set_current_send.assert_not_called()
    link._perform(100,(Action('resume',(2,mission_digest(mission))),))
    conn.mav.mission_set_current_send.assert_called_once()


def test_v4l2_checks_final_negotiated_mode_not_intermediate_width(monkeypatch):
    from safak_gorev2.v4l2_camera import V4L2Camera
    import cv2
    cfg,_=Options.load('config/ana-arducam.json')
    monkeypatch.setattr('safak_gorev2.v4l2_camera.usb_identity',lambda _:(cfg.camera.identity,cfg.camera.usb_vid_pid))
    values={};camera=Mock();camera.isOpened.return_value=True
    def set_value(prop,value):
        values[prop]=value
        return True
    def get_value(prop):
        if prop==cv2.CAP_PROP_FRAME_WIDTH and cv2.CAP_PROP_FRAME_HEIGHT not in values:
            return 640
        return values[prop]
    camera.set.side_effect=set_value;camera.get.side_effect=get_value
    monkeypatch.setattr('safak_gorev2.v4l2_camera.cv2.VideoCapture',lambda *a:camera)
    instance=V4L2Camera(cfg)
    instance.close()
    camera.release.assert_called_once()
