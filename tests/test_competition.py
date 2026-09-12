from dataclasses import replace
import hashlib
import json
from pathlib import Path
import threading
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from pymavlink.dialects.v20 import ardupilotmega as mav

from conftest import target, telemetry
from safak_gorev2.competition.config import Options, Servo, COLORS
from safak_gorev2.competition.controller import DualController
from safak_gorev2.competition.link import CompetitionLink
from safak_gorev2.competition.payload import PayloadLedger
from safak_gorev2.competition.runtime import CompetitionRuntime
from safak_gorev2.competition.route import (crossed, inside, RouteProgress,
                                             mission_contract_problem, mission_digest)
from safak_gorev2.competition.vision import Candidate, DualVision
from safak_gorev2.geometry import Calibration
from safak_gorev2.mavlink_io import TelemetryStore, PARAMETERS, validate_mission
from safak_gorev2.types import Action, Detection, Frame, PoseSample, MissionItem


@pytest.fixture
def plan(mission):
    return validate_mission(list(mission.items[:-1])+[
        MissionItem(3,16,3,410000100,290000100,6),
        replace(mission.items[-1],seq=4)])


@pytest.fixture
def options(plan):
    return Options(strategy='quick', vehicle_type=13, sortie_id='test-flight',
        mission_fingerprint=mission_digest(plan), search_start_seq=2,search_end_seq=2,route_reviewed=True,
        entry_gates=(((40.999,29.),(41.001,29.)),),
        finish_gate=((40.999,29.),(41.001,29.)),
        flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)))


def candidate(fid, now, color='mavi', metric=False, box=(.3,.2,.7,.8)):
    return Candidate(color,fid,now,None,box,target(fid,now) if metric else None,
                     source='opencv',color_verified=True,color_fill=.95)


def ready(cfg, options, plan):
    c=DualController(cfg,options)
    c.step(99,telemetry(99,armed=False,landed=1),(),None,0,plan)
    c.route.entry_count=1
    return c


def source(msg):
    msg._header.srcSystem=1
    msg._header.srcComponent=1
    return msg


def link_ready(cfg,options,plan,tmp_path):
    store=TelemetryStore()
    store.value=telemetry(100)
    store.mission=plan
    store.preflight_problem=lambda:None
    conn=Mock()
    ledger=PayloadLedger(tmp_path,'flight')
    link=CompetitionLink(cfg,store,True,threading.Event(),options,ledger,conn)
    link.route_authorized=True
    return link,conn,ledger


def test_speed_limit_is_thousand_for_both_tasks(cfg,options,plan,tmp_path):
    # Saha süresi nedeniyle ana görev de 1000 cm/s ile uçuyor; üst sınır aşılırsa
    # devralma yine reddedilir.
    center,_,_=link_ready(cfg,replace(options,strategy='center'),plan,tmp_path/'center')
    center.store.params['WPNAV_SPEED']=1000
    assert center.hardware_problem() is None
    center.store.params['WPNAV_SPEED']=1200
    assert center.hardware_problem() == 'WPNAV_SPEED center görev için 1–1000 cm/s aralığında olmalı'
    quick,_,_=link_ready(cfg,options,plan,tmp_path/'quick')
    quick.store.params['WPNAV_SPEED']=1000
    assert quick.hardware_problem() is None
    quick.store.params['WPNAV_SPEED']=0
    assert quick.hardware_problem() == 'WPNAV_SPEED quick görev için 1–1000 cm/s aralığında olmalı'


def test_disarmed_link_reloads_live_mission_instead_of_trusting_cached_copy(cfg,options,plan,tmp_path):
    link,conn,_=link_ready(cfg,options,plan,tmp_path)
    link.store.autopilot_confirmed=True
    link.store.value=telemetry(100,armed=False,landed=1)
    link._tick(100)
    conn.mav.mission_request_list_send.assert_called_once_with(
        cfg.link.target_system,cfg.link.target_component)
    conn.mav.mission_request_list_send.reset_mock()
    link.mission_stable_reads=2
    link._tick(101)
    conn.mav.mission_request_list_send.assert_not_called()
    link.store.value=telemetry(102,armed=True,landed=2)
    link._tick(102)
    conn.mav.mission_request_list_send.assert_not_called()


SERVOS_FIELD={'mavi':Servo(9,1800,True,function=58),
              'kirmizi':Servo(11,800,True,.3,1500,function=61)}
# 11 Eylül saha okumasi: SERVO9 MIN1100 MAX1900, SERVO11 MIN800 MAX1900.
LIMITS_FIELD={'SERVO9_MIN':1100.,'SERVO9_MAX':1900.,'SERVO11_MIN':800.,'SERVO11_MAX':1900.}


def servo_link(cfg,options,plan,tmp_path,**over):
    link,_,_=link_ready(cfg,replace(options,actuator='servo',servos=SERVOS_FIELD,**over),plan,tmp_path)
    link.servo_params.update(LIMITS_FIELD)
    return link


def outputs(blue,red):
    return source(mav.MAVLink_servo_output_raw_message(0,0,*([1000]*8),
                                                       servo9_raw=blue,servo11_raw=red))


def test_both_servos_must_hold_safe_output_for_two_seconds_before_flight(cfg,options,plan,tmp_path):
    link=servo_link(cfg,options,plan,tmp_path)
    safe=outputs(1100,1495)
    link.ingest(safe,100)
    link.ingest(safe,101.9)
    assert 'kararlılığı bekleniyor' in link.startup_servo_problem(101.9)
    link.ingest(safe,102.05)
    assert link.startup_servo_problem(102.05) is None
    # 800 us kirmizinin birakma konumu: daha kesin olan mesaj verilir.
    link.ingest(outputs(1100,800),102.1)
    assert link.startup_servo_problem(102.1) == (
        'kirmizi servo BIRAKMA tarafında: 800 us, bırakma 800 us (alt uç, marj 100 us); '
        'yükü takmayın')
    # Birakma disinda ama notr de degil: notr mesaji korunur.
    link.ingest(outputs(1100,1200),102.2)
    assert link.startup_servo_problem(102.2) == 'kirmizi servo nötr değil: 1200 us; yükü takmayın'


def test_blue_servo_beyond_autopilot_limits_blocks_loading(cfg,options,plan,tmp_path):
    """11 Eylül sahasinda okunan gercek deger: AUX1/9 = 2006 us, MAX 1900.

    RC passthrough (RCIN8) kanali servoyu birakma tarafinda suruyordu. Eski
    kapi mavi'yi hic denetlemiyordu cunku neutral_pwm tanimi yok.
    """
    link=servo_link(cfg,options,plan,tmp_path)
    link.ingest(outputs(2006,1495),100)
    problem=link.startup_servo_problem(100)
    assert problem is not None and problem.startswith('mavi servo BIRAKMA tarafında')
    assert '2006' in problem and 'üst uç' in problem and 'yükü takmayın' in problem


def test_blue_servo_below_min_does_not_block_flight(cfg,options,plan,tmp_path):
    """Sahada olculen tutma konumu 982 us, MIN 1100'un altinda.

    Yuku dusurmez: birakma 1800, yani tam ters uc; mandal fiziksel olarak
    kapali dogrulandi. Sinir disi olmak yalnizca servoyu mekanizmaya dayar.
    Bunu ucus engeli yapmak calisan bir kurulumu yerde birakiyordu.
    """
    link=servo_link(cfg,options,plan,tmp_path)
    safe=outputs(982,1495)
    link.ingest(safe,100)
    link.ingest(safe,102.1)
    assert link.startup_servo_problem(102.1) is None
    # Birakma tarafindaki asim yine engel.
    link.ingest(outputs(2006,1495),102.2)
    assert 'BIRAKMA tarafında' in link.startup_servo_problem(102.2)


def test_blue_servo_at_release_position_blocks_loading(cfg,options,plan,tmp_path):
    """Sinirlarin icinde ama birakma konumunda: yine yuk takilmamali."""
    link=servo_link(cfg,options,plan,tmp_path)
    link.ingest(outputs(1800,1495),100)
    assert link.startup_servo_problem(100) == (
        'mavi servo BIRAKMA tarafında: 1800 us, bırakma 1800 us (üst uç, marj 100 us); '
        'yükü takmayın')
    link.ingest(outputs(1750,1495),100)   # marj 100 us icinde
    assert 'BIRAKMA tarafında' in link.startup_servo_problem(100)


def test_blue_servo_safe_hold_passes(cfg,options,plan,tmp_path):
    link=servo_link(cfg,options,plan,tmp_path)
    safe=outputs(1100,1495)
    link.ingest(safe,100)
    link.ingest(safe,102.1)
    assert link.startup_servo_problem(102.1) is None


def test_missing_servo_limits_block_loading(cfg,options,plan,tmp_path):
    """MIN/MAX okunmadan yuk takma izni verilmez."""
    link,_,_=link_ready(cfg,replace(options,actuator='servo',servos=SERVOS_FIELD),plan,tmp_path)
    link.ingest(outputs(1100,1495),100)
    assert link.startup_servo_problem(100) == 'mavi servo çıkış sınırları okunuyor; yükü takmayın'


def test_flight_preflight_rejects_changed_land_before_camera_or_arm(cfg,options,plan,tmp_path):
    rt=CompetitionRuntime(replace(cfg,runtime_dir=str(tmp_path/'preflight')),'flight',options)
    changed=replace(plan,items=plan.items[:-1]+(replace(plan.items[-1],x=plan.items[-1].x+100),))
    rt.telemetry.mission=changed
    rt.telemetry.value=telemetry(100,armed=False,landed=1)
    rt.telemetry.preflight_problem=lambda:None
    rt.link=Mock(failure=None,mission_stable_reads=2)
    rt.link.hardware_problem.return_value=None
    rt.link.startup_servo_problem.return_value=None
    try:
        problem=rt.wait_for_flight_preflight(.1)
        assert 'Rota parmak izi' in problem
        assert not rt.flight_gate_open
    finally:
        rt.close()


def test_camera_preflight_opens_gate_only_for_fresh_opencv_frame(cfg,options,tmp_path):
    rt=CompetitionRuntime(replace(cfg,runtime_dir=str(tmp_path/'camera-gate')),'flight',options)
    rt.telemetry.value=telemetry(100,armed=False,landed=1)
    try:
        with rt.state.lock:
            rt.state.backend='OPENCV'
            rt.state.camera_info={'model':'IMX708'}
            rt.state.frame_at=99.9
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('safak_gorev2.competition.runtime.time.monotonic',lambda:100.)
            assert rt.wait_for_camera_preflight(.1) is None
        assert rt.flight_gate_open
    finally:
        rt.close()


def test_camera_preflight_rejects_arm_before_first_frame(cfg,options,tmp_path):
    rt=CompetitionRuntime(replace(cfg,runtime_dir=str(tmp_path/'camera-arm')),'flight',options)
    rt.telemetry.value=telemetry(100,armed=True,landed=2)
    try:
        assert 'Kamera ön kontrolü bitmeden ARM edildi' in rt.wait_for_camera_preflight(.1)
        assert not rt.flight_gate_open
    finally:
        rt.close()


def test_mission_contract_rejects_stale_land_minus_one_range(options,plan):
    mission_options=replace(options,search_scope='mission',search_end_seq=plan.land_seq-1)
    assert mission_contract_problem(plan,mission_options) is None
    assert mission_contract_problem(plan,replace(mission_options,search_end_seq=2)) == (
        'Rota taraması TAKEOFF sonrası seçilen waypointten LAND öncesine kadar olmalı')


def test_legacy_files_unchanged():
    manifest=json.loads(Path('docs/competition/legacy-sha256.json').read_text())
    moved=json.loads(Path('archive/legacy-options/preserved-paths.json').read_text())
    # Finder metadata'sı Linux'a dağıtılmaz; uygulama/profil kaynaklarını denetle.
    assert all(hashlib.sha256(Path(moved.get(p,p)).read_bytes()).hexdigest()==digest
               for p,digest in manifest.items() if Path(p).name != '.DS_Store')


@pytest.mark.parametrize('order',[('mavi','kirmizi'),('kirmizi','mavi')])
def test_quick_two_colors_correct_payload_once(cfg,options,plan,order):
    c=ready(cfg,options,plan)
    statuses={}
    releases=[]
    mode='AUTO'
    for i in range(140):
        now=100+i*.05
        color=order[0] if not statuses else order[1]
        d=c.step(now,telemetry(now,mode=mode),(candidate(i,now,color),),i,now,plan,release_status=statuses)
        for a in d.actions:
            if a.kind=='mode': mode=a.values[0]
            assert a.kind!='velocity'
            if a.kind=='payload':
                assert mode=='GUIDED' and a.values[-1]=='GUIDED'
                releases.append(a.values[:2]); statuses[a.values[0]]='SIMULATED'
    assert releases==[('kirmizi' if color=='mavi' else 'mavi',color) for color in order]
    assert c.done==set(COLORS)
    assert not any(a.kind=='mode' for a in d.actions)


@pytest.mark.parametrize('kind',['stale','future','duplicate','low_score','wrong_id','wrong_color','outside','takeoff','before_gate','wrong_route'])
def test_no_release_invalid_inputs(cfg,options,plan,kind):
    c=ready(cfg,options,plan)
    for i in range(20):
        now=100+i*.05
        at=now-1 if kind=='stale' else now+1 if kind=='future' else now
        fid=1 if kind=='duplicate' else i
        x=candidate(fid,at)
        if kind=='low_score': x=replace(x,confidence=.1)
        if kind=='wrong_id': x=replace(x,frame_id=fid+100)
        if kind=='wrong_color': x=replace(x,color='yesil')
        t=telemetry(now)
        if kind=='outside': t=replace(t,lat=42.)
        if kind=='takeoff': t=replace(t,mission_seq=1)
        if kind=='before_gate': c.route.entry_count=0
        p=replace(plan,items=plan.items[:2]+(replace(plan.items[2],z=30.),)+plan.items[3:]) if kind=='wrong_route' else plan
        d=c.step(now,t,(x,),fid,at,p)
        assert not any(a.kind=='payload' for a in d.actions)


def test_quick_target_jump_and_gap_reset(cfg,options,plan):
    c=ready(cfg,replace(options,quick_frames=4),plan)
    for i in range(20):
        now=100+i*.1
        box=(.1,.1,.2,.2) if i%2 else (.7,.7,.8,.8)
        d=c.step(now,telemetry(now),(candidate(i,now,box=box),),i,now,plan)
        assert not d.actions


def test_no_midair_restart_and_pilot_latch(cfg,options,plan):
    c=DualController(cfg,options); c.route.entry_count=1
    for i in range(10):
        now=100+i*.05
        assert not c.step(now,telemetry(now),(candidate(i,now),),i,now,plan).actions
    c=ready(cfg,options,plan)
    c.step(100,telemetry(100),(),0,100,plan)
    d=c.step(100.05,telemetry(100.05,mode='LOITER'),(),1,100.05,plan)
    assert d.state=='PILOT_CONTROL'
    d=c.step(100.1,telemetry(100.1),(),2,100.1,plan)
    assert not d.actions


def test_quick_ack_timeout_never_retries(cfg,options,plan):
    c=ready(cfg,options,plan)
    mode='AUTO'
    for i in range(100):
        now=100+i*.05
        d=c.step(now,telemetry(now,mode=mode),(candidate(i,now),),i,now,plan)
        for a in d.actions:
            if a.kind=='mode': mode=a.values[0]
    assert c.state=='ABORTED'
    assert c.requested=={'mavi'}


def test_metric_full_cycle_resume_then_other_color_lands(cfg,options,plan):
    options=replace(options,strategy='center')
    c=ready(cfg,options,plan)
    statuses={}; releases=[]; resumes=[]; mode='AUTO'; down=-6.; seq=2
    for i in range(600):
        now=100+i*.05
        if c.state=='INTERCEPT' and c.child.state=='DESCENDING': down=-3.55
        if c.state=='CLIMB': down=-6.
        t=telemetry(now,mode=mode,down=down,relative_alt_m=-down,mission_seq=seq)
        color='mavi' if 'mavi' not in c.done else 'kirmizi'
        d=c.step(now,t,(candidate(i,now,color,metric=True),),i,now,plan,release_status=statuses)
        for a in d.actions:
            if a.kind=='mode': mode=a.values[0]
            if a.kind=='resume': seq=a.values[0]; resumes.append(seq)
            if a.kind=='mission_current': seq=a.values[0]
            if a.kind=='payload':
                releases.append(a.values[:2]); statuses[a.values[0]]='SIMULATED'
        if c.state=='LANDING': break
    assert releases==[('kirmizi','mavi'),('mavi','kirmizi')]
    assert c.done==set(COLORS)
    # İkinci yükten sonra kalan tarama waypointleri atlanır; AUTO ile LAND waypointi.
    assert mode=='AUTO' and seq==plan.land_seq and resumes==[2]
    assert down == -3.55  # İkinci yükten sonra tarama irtifasına yükselmez.


def test_target_loss_during_center_returns_to_auto_and_can_retry(cfg,options,plan):
    c=ready(cfg,replace(options,strategy='center'),plan)
    mode='AUTO'
    centering_started = False
    for i in range(100):
        now=100+i*.05
        centering_started = centering_started or c.state == 'INTERCEPT'
        xs=() if centering_started else (candidate(i,now,metric=True),)
        d=c.step(now,telemetry(now,mode=mode),xs,i,now,plan)
        for a in d.actions:
            assert a.kind!='payload'
            if a.kind=='mode': mode=a.values[0]
        if c.state=='RESUME_SELECT': break
    assert c.state=='RESUME_SELECT' and mode=='GUIDED'
    assert Action('resume',(2,mission_digest(plan))) in d.actions
    assert not any(a.kind in ('payload','release') for a in d.actions)
    now += .05
    d=c.step(now,telemetry(now,mode='GUIDED',mission_seq=2),(),101,now,plan)
    assert d.state=='RESUME_AUTO' and Action('mode',('AUTO','GUIDED')) in d.actions
    now += .05
    d=c.step(now,telemetry(now,mode='AUTO',mission_seq=2),(),102,now,plan)
    assert d.state=='SEARCHING' and d.actions==(Action('revoke'),)


def test_center_keeps_verified_fixed_target_while_visual_quad_remains(cfg,options,plan):
    """Gerçek uçuşta dururken PnP doğrulandıktan sonra renk dörtgeni
    sürdü, fakat PnP düzlem çözümü kesildi. Sabit yer hedefi yeni bir
    PnP kabul etmeden aynı OpenCV iziyle merkezleme/alçalmayı sürdürmeli.
    """
    c=ready(cfg,replace(options,strategy='center'),plan)
    mode='AUTO'; down=-6.; statuses={}; releases=[]; metric=True
    for i in range(260):
        now=100+i*.05
        if c.state=='INTERCEPT':
            metric=False
            if c.child.state=='DESCENDING':
                down=-3.55
        t=telemetry(now,mode=mode,down=down,relative_alt_m=-down)
        d=c.step(now,t,(candidate(i,now,metric=metric),),i,now,plan,release_status=statuses)
        for a in d.actions:
            if a.kind=='mode': mode=a.values[0]
            if a.kind=='payload':
                releases.append(a.values[:2]); statuses[a.values[0]]='SIMULATED'
        if releases:
            break
    assert releases==[('kirmizi','mavi')]
    assert c.state=='RELEASE_WAIT'


def test_route_end_preserves_payload_and_requires_finish(cfg,options,plan):
    c=ready(cfg,options,plan)
    c.step(100,telemetry(100),(),0,100,plan)
    d=c.step(100.05,telemetry(100.05,mission_seq=3),(candidate(1,100.05),),1,100.05,plan)
    assert d.state=='AUTO_FINISH' and not d.actions
    d=c.step(100.1,telemetry(100.1,armed=False,landed=1),(),2,100.1,plan)
    assert d.state=='INCOMPLETE'


def test_directed_finite_gate_and_freshness(options):
    gate=((40.999,29.),(41.001,29.))
    assert crossed(gate,(41.,28.9999),(41.,29.0001))
    assert not crossed(gate,(41.,29.0001),(41.,28.9999))
    assert not crossed(gate,(42.,28.9999),(42.,29.0001))
    route=RouteProgress(options)
    route.update(telemetry(100,lon=28.9999),100,.6)
    route.update(telemetry(102,lon=29.0001),102,.6)
    assert not route.entered
    route.update(telemetry(102.1,lon=28.9999),102.1,.6)
    route.update(telemetry(102.2,lon=29.0001),102.2,.6)
    assert route.entered


def test_ledger_restart_each_payload_once(tmp_path):
    a=PayloadLedger(tmp_path,'flight')
    assert a.reserve('kirmizi',{})
    b=PayloadLedger(tmp_path,'flight')
    assert b.statuses()=={'kirmizi':'UNCERTAIN'}
    assert not b.reserve('kirmizi',{})
    assert b.reserve('mavi',{})
    assert PayloadLedger(tmp_path,'new-loaded-flight').reserve('kirmizi',{})


def test_hex_identity(cfg,options,plan,tmp_path):
    link,conn,ledger=link_ready(cfg,options,plan,tmp_path)
    link.ingest(source(mav.MAVLink_heartbeat_message(13,3,128,3,4,3)),100)
    assert link.store.autopilot_confirmed
    link.ingest(source(mav.MAVLink_heartbeat_message(2,3,128,3,4,3)),100.1)
    assert not link.store.autopilot_confirmed


def test_real_servo_exact_channel_ack_and_output(cfg,options,plan,tmp_path,monkeypatch):
    options=replace(options,actuator='servo',servos={'kirmizi':Servo(9,1500,True),'mavi':Servo(10,1500,True)})
    link,conn,ledger=link_ready(cfg,options,plan,tmp_path)
    link.store.value=telemetry(100.,mode='GUIDED');link.owned=True;link.claim_slot=6
    for ch in (9,10):
        link.servo_params.update({f'SERVO{ch}_FUNCTION':0,f'SERVO{ch}_MIN':1000,f'SERVO{ch}_MAX':2000})
    monkeypatch.setattr('safak_gorev2.competition.link.time.monotonic',lambda:100.)
    a=Action('payload',('kirmizi','mavi',7,100.,'GUIDED'))
    link._perform(100,(a,))
    args=conn.mav.command_long_send.call_args.args
    assert args[2:6]==(183,0,9,1500)
    link._perform(100,(a,))
    assert conn.mav.command_long_send.call_count==1
    ack=source(mav.MAVLink_command_ack_message(183,0,0,0,245,191))
    link.ingest(ack,100.05)
    assert link.snapshot_status()['kirmizi']=='SENT'
    output=source(mav.MAVLink_servo_output_raw_message(100000,0,*([1000]*8),servo9_raw=1500))
    link.ingest(output,100.1)
    assert link.snapshot_status()['kirmizi']=='ACK_ACCEPTED'
    assert ledger.statuses()['kirmizi']=='ACK_ACCEPTED'


@pytest.mark.parametrize('bad',['observe','pilot','disarm','stale','wrong_payload','motor','no_gate','outside'])
def test_servo_refuses_unsafe_or_unverified(cfg,options,plan,tmp_path,bad,monkeypatch):
    options=replace(options,actuator='servo',servos={'kirmizi':Servo(9,1500,True),'mavi':Servo(10,1500,True)})
    link,conn,ledger=link_ready(cfg,options,plan,tmp_path)
    link.store.value=telemetry(100.,mode='GUIDED');link.owned=True;link.claim_slot=6
    for ch in (9,10):
        link.servo_params.update({f'SERVO{ch}_FUNCTION':0,f'SERVO{ch}_MIN':1000,f'SERVO{ch}_MAX':2000})
    if bad=='observe': link.allow_control=False
    if bad=='pilot': link.store.pilot_override=True
    if bad=='disarm': link.store.value=telemetry(100,mode='GUIDED',armed=False)
    if bad=='motor': link.servo_params['SERVO9_FUNCTION']=33
    if bad=='no_gate': link.route_authorized=False
    if bad=='outside': link.store.value=telemetry(100,mode='GUIDED',lat=42.)
    monkeypatch.setattr('safak_gorev2.competition.link.time.monotonic',lambda:100.)
    link._perform(100,(Action('payload',('kirmizi','kirmizi' if bad=='wrong_payload' else 'mavi',7,99. if bad=='stale' else 100.,'GUIDED')),))
    conn.mav.command_long_send.assert_not_called()


def test_vision_both_colors_and_one_meter_red(cfg):
    cal=Calibration(1280,720,np.array([[800.,0,640],[0,800,360],[0,0,1]]),np.zeros(5),"synthetic",(0,0,1280,720),.1)
    vision=DualVision(cfg,cal)
    image=np.full((720,1280,3),80,np.uint8)
    cv2.rectangle(image,(480,200),(800,520),(255,20,20),-1)
    cv2.rectangle(image,(940,280),(1100,440),(20,20,255),-1)
    ds=(Detection('mavi_hedef',.95,(480/1280,200/720,800/1280,520/720)),
        Detection('kirmizi_hedef',.95,(940/1280,280/720,1100/1280,440/720)))
    frame=Frame(1,100,100,image,ds)
    candidates,_=vision.detect(frame,PoseSample(100,0,0,0,0,0,-5.05),'center')
    assert {x.color for x in candidates}==set(COLORS)
    assert all(x.metric.camera_height_m==pytest.approx(5.,abs=.1) for x in candidates)
    candidates,_=DualVision(cfg).detect(frame,None,'quick')
    assert len(candidates)==2 and all(x.metric is None for x in candidates)


def test_current_profile_readiness_and_safety_fields(cfg):
    for task in ('ana','hizli'):
        base,o=Options.load(f'config/{task}-gorev.json')
        assert o.vehicle_type==13 and o.servos['mavi'].channel==9 and o.servos['kirmizi'].channel==11
        assert o.servos['mavi'].release_pwm == 1800
        assert o.servos['kirmizi'].function == 61
        assert o.servos['kirmizi'].neutral_pwm == 1500
        assert bool(o.missing(base)) == (task == 'ana')
        unchecked=replace(base,mission=replace(base.mission,direct_land_corridor_checked=None))
        assert 'iki yük sonrası doğrudan LAND bölgesinin açık olduğu saha kontrolü' in o.missing(unchecked)
    with pytest.raises(ValueError):
        replace(Options(),servos={'mavi':Servo(9,1500),'kirmizi':Servo(9,1500)}).validate()


def test_autonomous_landing_transition_not_false_abort(cfg,options,plan):
    c=ready(cfg,options,plan)
    c.step(100,telemetry(100),(),0,100,plan)
    c.step(100.05,telemetry(100.05,mission_seq=3),(),1,100.05,plan)
    c.done=set(COLORS); c.route.finished=True
    d=c.step(100.1,telemetry(100.1,landed=4,mission_seq=4),(),2,100.1,plan)
    assert d.state=='AUTO_FINISH'
    d=c.step(100.15,telemetry(100.15,armed=False,landed=1,mission_seq=4),(),3,100.15,plan)
    assert d.state=='DONE'


def test_home_is_not_flight_path_but_nav_changes_are(cfg,options,plan):
    new_home=replace(plan,items=(replace(plan.items[0],x=0,y=0,z=50.),)+plan.items[1:])
    assert mission_digest(new_home)==mission_digest(plan)
    new_path=replace(plan,items=plan.items[:2]+(replace(plan.items[2],x=410001000),)+plan.items[3:])
    assert mission_digest(new_path)!=mission_digest(plan)


def test_strategy_switch_does_not_reset_physical_payload(cfg,options,tmp_path):
    from safak_gorev2.competition.runtime import CompetitionRuntime
    a=CompetitionRuntime(replace(cfg,runtime_dir=str(tmp_path/'center')),'observe',options)
    assert a.payload_ledger.reserve('kirmizi',{})
    a.close()
    b=CompetitionRuntime(replace(cfg,runtime_dir=str(tmp_path/'quick')),'observe',replace(options,strategy='quick'))
    assert b.payload_status=={'kirmizi':'UNCERTAIN'}
    b.close()


def test_resume_only_approved_waypoint_while_owned(cfg,options,plan,tmp_path):
    link,conn,_=link_ready(cfg,options,plan,tmp_path)
    link.store.value=telemetry(100,mode='GUIDED');link.owned=True;link.claim_slot=6
    link._perform(100,(Action('resume',(2,mission_digest(plan))),))
    assert conn.mav.mission_set_current_send.call_args.args==(1,1,2)
    link._perform(100,(Action('resume',(4,mission_digest(plan))),))
    link._perform(100,(Action('resume',(2,'wrong')),))
    link.store.pilot_override=True
    link._perform(100,(Action('resume',(2,mission_digest(plan))),))
    assert conn.mav.mission_set_current_send.call_count==1


def test_quick_configuration_needs_no_calibration():
    cfg,o=Options.load('config/hizli-gorev.json')
    assert cfg.camera.calibration_file is None
    assert 'kamera kalibrasyonu' not in o.missing(cfg)


def test_observe_runtime_runs_both_colors_without_commands(cfg,options,tmp_path):
    import time
    from safak_gorev2.competition.runtime import CompetitionRuntime
    cfg=replace(cfg,runtime_dir=str(tmp_path/'quick'))
    rt=CompetitionRuntime(cfg,'observe',options)
    rt.start(connect=False)
    try:
        now=time.monotonic()
        image=np.full((720,1280,3),80,np.uint8)
        cv2.rectangle(image,(180,180),(380,380),(220,65,30),-1)
        cv2.rectangle(image,(760,320),(920,480),(30,65,220),-1)
        frame=Frame(1,now,now,image,(),backend='OPENCV')
        rt.mailbox.put(frame)
        until=time.monotonic()+1
        while time.monotonic()<until and (len(rt.candidates)!=2 or rt.state.jpeg is None): time.sleep(.01)
        assert {x.color for x in rt.candidates}==set(COLORS)
        assert rt.state.jpeg is not None and rt.state.decision.state=='OBSERVING'
        assert not rt.state.decision.actions and not rt.payload_ledger.statuses()
        assert rt.state.pipeline_error is None
    finally: rt.close()


def test_delayed_ack_and_wrong_component_not_success(cfg,options,plan,tmp_path,monkeypatch):
    options=replace(options,actuator='servo',servos={'kirmizi':Servo(9,1500,True),'mavi':Servo(10,1500,True)})
    link,conn,ledger=link_ready(cfg,options,plan,tmp_path)
    link.store.value=telemetry(100.,mode='GUIDED');link.owned=True;link.claim_slot=6
    for ch in (9,10):
        link.servo_params.update({f'SERVO{ch}_FUNCTION':0,f'SERVO{ch}_MIN':1000,f'SERVO{ch}_MAX':2000})
    monkeypatch.setattr('safak_gorev2.competition.link.time.monotonic',lambda:100.)
    link._perform(100,(Action('payload',('kirmizi','mavi',1,100.,'GUIDED')),))
    wrong=source(mav.MAVLink_command_ack_message(183,0,0,0,245,191));wrong._header.srcComponent=42
    link.ingest(wrong,100.1)
    assert not link.pending['ack']
    link.ingest(source(mav.MAVLink_command_ack_message(183,0,0,0,245,191)),103.)
    assert link.snapshot_status()['kirmizi']=='UNCERTAIN'
    assert link.pending is None and ledger.statuses()['kirmizi']=='UNCERTAIN'


def test_arducopter_land_wire_parameter_is_supported(cfg,options,plan,tmp_path):
    link,_,_=link_ready(cfg,options,plan,tmp_path)
    item=source(mav.MAVLink_mission_item_int_message(245,191,4,3,21,0,1,0,0,0,1,410000000,290000000,0))
    link.ingest(item,100)
    assert link.failure is None
    item.param1=5
    link.ingest(item,100.1)
    assert link.failure is not None


def test_center_search_speed_upper_bound_follows_braking_analysis():
    # Üst sınır 3 -> 8 m/s: büyük sahada tarama hızı irtifayla seçilir.
    # Fren mesafesi v^2/(2*2.5)+0.3v modeli saha kaydıyla doğrulandı
    # (2,49 m/s -> 1,9 m; 7,04 m/s -> 11,9 m). 25 m irtifada 7,7 m/s hedefi
    # frenden sonra hâlâ kadrajda tutuyor; 8 m/s bunun hemen üstü.
    for value in (0.5, 3.0, 8.0):
        replace(Options(), strategy='center', center_search_speed_mps=value).validate()
    for value in (0.49, 8.01):
        with pytest.raises(ValueError):
            replace(Options(), strategy='center', center_search_speed_mps=value).validate()


@pytest.mark.parametrize('profile', ['config/ana-gorev.json', 'config/ana-imx708.json',
                                     'config/ana-aux1-only.json'])
def test_main_panel_is_low_bandwidth_but_readable(profile):
    cfg, _ = Options.load(profile)
    assert cfg.web.width == 640
    assert cfg.web.fps == 4
    assert cfg.web.jpeg_quality == 35


def test_panel_altitude_hides_stale_global_position():
    from safak_gorev2.competition.runtime import CompetitionRuntime
    from safak_gorev2.types import Telemetry
    fresh = Telemetry(global_at=99.8, relative_alt_m=14.96)
    stale = Telemetry(global_at=98., relative_alt_m=14.96)
    assert CompetitionRuntime.altitude_label(fresh,100.,.6) == 'IRTIFA 15.0 m'
    assert CompetitionRuntime.altitude_label(stale,100.,.6) == 'IRTIFA --'


def test_aux1_only_hardware_check_and_initial_requests_never_touch_aux3(cfg, options, plan, tmp_path):
    servos = dict(options.servos)
    servos['mavi'] = Servo(9, 1800, True, function=58)
    servos['kirmizi'] = Servo(11, 800, True, pulse_s=.3, neutral_pwm=1500, function=61)
    opts = replace(options, actuator='servo', payloads=('mavi',), servos=servos)
    link, conn, _ = link_ready(cfg, opts, plan, tmp_path)
    link.store.params['WPNAV_SPEED'] = 1000
    link.servo_params.update(SERVO9_FUNCTION=58, SERVO9_MIN=1100, SERVO9_MAX=1900)
    assert link.hardware_problem() is None
    link._initial_requests()
    names = {call.args[2] for call in conn.mav.param_request_read_send.call_args_list}
    assert {b'SERVO9_FUNCTION', b'SERVO9_MIN', b'SERVO9_MAX'} <= names
    assert not any(name.startswith(b'SERVO11_') for name in names)


@pytest.mark.parametrize('profile',['config/ana-gorev.json','config/ana-imx708.json'])
def test_main_profiles_can_descend_from_competition_altitude(profile):
    # Hedef görülüp ortalandığında 5 m'ye inme süresi
    # merkezleme/alçalma sınırının altında kalmalı (15 m'den yaklaşık 40 s).
    cfg, _ = Options.load(profile)
    c = cfg.control
    assert c.target_camera_height_m == 5. and c.minimum_camera_height_m <= 3.
    assert c.max_climb_mps >= 1.
    assert c.interaction_timeout_s >= 200.
    assert (15.-c.target_camera_height_m)/c.max_descent_mps < c.interaction_timeout_s
    # Alçalma hızının üst sınırı ayarlanan bir sayı değil, türetilen iki kural:
    # (1) P-yasası bırakma penceresine girerken kp_height*hız kadar yavaşlama
    # ister; düşey rampa sınırı bundan küçükse pencere aşılır.
    assert c.kp_height*c.max_descent_mps <= c.max_accel_mps2
    # (2) Rampa sınırıyla durma mesafesi bırakma penceresinin yarı genişliğini
    # aşmamalı, yoksa araç minimum_camera_height_m'ye doğru sarkar.
    assert c.max_descent_mps**2/(2*c.max_accel_mps2) <= c.height_tolerance_m
    # Yüksekte kilit toleransı ölçüm gürültüsüyle birlikte büyür, bırakma
    # yüksekliğinde sabit değere iner: 15 m'de 0,75 m, 5 m'de 0,50 m.
    assert .03 <= c.center_tolerance_height_ratio <= .08
    assert c.center_tolerance_height_ratio*c.target_camera_height_m < c.center_tolerance_m


@pytest.mark.parametrize('profile',['config/ana-gorev.json','config/ana-imx708.json'])
def test_main_profile_tolerances_exceed_measured_pnp_noise(profile):
    # 11 Eylül ana uçuşunda 10 m'de ölçülen PnP saçılması: yatay sd ~0,12 m,
    # görsel yükseklik sd ~0,39 m (9,04–10,15 m). Toleranslar bu gürültünün
    # altında kalırsa kilit hiç tamamlanmaz; en az ~3 sigma pay bırakılır.
    cfg, _ = Options.load(profile)
    c = cfg.control
    assert c.center_tolerance_m >= .4 and c.descent_center_tolerance_m > c.center_tolerance_m
    assert c.height_tolerance_m >= .9
    assert c.target_camera_height_m - c.height_tolerance_m > c.minimum_camera_height_m + .9
    # GUIDED'de ölçülen sürüklenme 0,20–0,27 m/s idi; bırakma eşiği bunun üstünde.
    assert c.release_horizontal_speed_mps >= .3
    assert c.lost_target_abort_s >= 2.
