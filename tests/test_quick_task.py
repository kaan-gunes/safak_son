from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import telemetry
from test_competition import options, plan, ready, candidate, link_ready
from safak_gorev2.competition.config import Options
from safak_gorev2.types import Action


def test_quick_entire_two_color_flow_has_no_movement_or_altitude_commands(cfg,options,plan):
    c=ready(cfg,options,plan)
    mode='AUTO';statuses={};states=[];actions=[];releases=[]
    for i in range(180):
        at=100+i*.05
        color='mavi' if 'mavi' not in c.done else 'kirmizi'
        # Hiçbir kare metrik hedef sağlamıyor. Hızlı görev PnP olmadan çalışmalı.
        d=c.step(at,telemetry(at,mode=mode),(candidate(i,at,color),),i,at,plan,release_status=statuses)
        states.append(c.state)
        for a in d.actions:
            actions.append(a.kind)
            if a.kind=='mode': mode=a.values[0]
            if a.kind=='payload':
                assert mode=='GUIDED'
                assert c.verify_hold.elapsed >= options.quick_verify_s-1e-9
                assert c.verify_hold.count >= options.quick_verify_frames
                releases.append(a.values[:2]);statuses[a.values[0]]='SIMULATED'
        if c.done=={'mavi','kirmizi'} and c.child is None: break
    assert releases==[('kirmizi','mavi'),('mavi','kirmizi')]
    assert not set(states)&{'INTERCEPT','CLIMB','CENTERING','DESCENDING'}
    assert 'velocity' not in actions
    assert actions.count('resume')==2 and mode=='AUTO'
    assert not set(c.requested)-set(c.done)


@pytest.mark.parametrize('case',['missing','wrong_color','intermittent','duplicate','jump'])
def test_quick_requires_new_same_target_after_stop(cfg,options,plan,case):
    c=ready(cfg,options,plan);mode='AUTO';resumes=[]
    for i in range(150):
        at=100+i*.05;fid=i;frame_at=at;xs=(candidate(fid,at),)
        if c.state=='VERIFYING':
            if case=='missing' or (case=='intermittent' and i%2): xs=()
            if case=='wrong_color': xs=(candidate(fid,at,'kirmizi'),)
            if case=='jump': xs=(candidate(fid,at,box=(.01,.01,.1,.1)),)
            if case=='duplicate':
                fid=c.verify_frame;frame_at=c.entered;xs=(candidate(fid,frame_at),)
        d=c.step(at,telemetry(at,mode=mode),xs,fid,frame_at,plan)
        for a in d.actions:
            assert a.kind not in ('payload','velocity')
            if a.kind=='mode': mode=a.values[0]
            if a.kind=='resume': resumes.append(a.values[0])
        if c.state in ('ABORTED','PILOT_CONTROL'): break
        if resumes and c.state=='SEARCHING': break
    if case=='duplicate':
        assert c.state=='ABORTED' and not resumes  # Tekrar edilen görüntü sonunda bayatlar.
    else:
        assert resumes==[2] and mode=='AUTO'


def test_quick_cannot_verify_while_moving(cfg,options,plan):
    c=ready(cfg,options,plan);mode='AUTO'
    for i in range(140):
        at=100+i*.05
        d=c.step(at,telemetry(at,mode=mode,vn=1.5),(candidate(i,at),),i,at,plan)
        for a in d.actions:
            assert a.kind not in ('payload','velocity')
            if a.kind=='mode': mode=a.values[0]
        if c.state=='ABORTED': break
    assert c.state=='ABORTED' and mode=='LOITER'


@pytest.mark.parametrize('changes',[{'mode':'AUTO'},{'vn':.3},{'vd':.3},{'roll':.3},{'relative_alt_m':1.}])
def test_quick_link_independently_blocks_moving_or_wrong_mode(cfg,options,plan,tmp_path,monkeypatch,changes):
    link,conn,_=link_ready(cfg,options,plan,tmp_path)
    link.store.value=replace(telemetry(100.,mode='GUIDED'),**changes)
    link.owned=True;link.claim_slot=6
    monkeypatch.setattr('safak_gorev2.competition.link.time.monotonic',lambda:100.)
    link._perform(100.,(Action('payload',('kirmizi','mavi',1,100.,link.store.value.mode)),))
    assert link.snapshot_status()=={'kirmizi':'BLOCKED'}
    conn.mav.command_long_send.assert_not_called()


def test_only_two_current_profiles_and_removed_strategy(cfg):
    files=list(Path('config').glob('*.json'))
    tasks=[p.name for p in files if 'strategy' in json.loads(p.read_text())]
    assert sorted(tasks)==['ana-gorev.json','hizli-gorev.json']
    for name in ('competition-center','competition-sighting','flight-imx708','flight-imx219-new-model','flight.field-candidate','quad'):
        assert not Path('config',name+'.json').exists()
    with pytest.raises(ValueError):
        replace(Options(),strategy='sighting').validate()
    base,opts=Options.load('config/hizli-gorev.json')
    assert opts.strategy=='quick' and base.camera.calibration_file is None
    assert tuple(base.camera.offset_body_m)==(.11,0.,.05)
    assert opts.camera_mount_yaw_deg==180
    assert tuple(base.camera.sensor_output_size)==(2304,1296)


def test_old_entry_stops_without_loading_hardware():
    script="import sys; from safak_gorev2.main import main; assert main()==2; assert not ({'picamera2','hailo','gi','pymavlink','flask'} & set(sys.modules))"
    subprocess.run([sys.executable,'-c',script],check=True,capture_output=True)


def test_quick_import_has_no_tracker_dependency():
    script="import sys; from safak_gorev2.competition.controller import DualController; assert not any('mosse' in k.lower() for k in sys.modules)"
    subprocess.run([sys.executable,'-c',script],check=True,capture_output=True)
