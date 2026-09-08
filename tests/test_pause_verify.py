"""Gör → dur → doğrula → merkezle / AUTO'ya dön davranışları."""
from dataclasses import replace
from unittest.mock import Mock

import numpy as np
import pytest

from conftest import telemetry
from test_competition import plan, options, ready, candidate, link_ready
from safak_gorev2.competition.vision import DualVision
from safak_gorev2.types import Frame, Detection, Action


def stopped_controller(cfg, options, plan):
    c = ready(cfg, replace(options, strategy='center'), plan)
    for i in range(3):
        now = 100+i*.05
        d = c.step(now, telemetry(now), (candidate(i, now),), i, now, plan)
    assert c.state == 'REQUEST_STOP'
    return c


def test_raw_ai_triggers_stop_at_point_one_before_geometry(cfg, options, plan):
    c = ready(cfg, replace(options, strategy='center'), plan)
    for i in range(4):
        now = 100+i/30
        d = c.step(now, telemetry(now, vn=1.5), (candidate(i,now),), i, now, plan)
        if i < 3:
            assert not d.actions
    assert c.state == 'REQUEST_STOP'
    assert [a.kind for a in d.actions] == ['claim','mode']
    assert d.actions[1].values == ('GUIDED','AUTO')
    assert not c.requested


def test_duplicates_do_not_earn_point_one_seconds(cfg, options, plan):
    c = ready(cfg, replace(options, strategy='center'), plan)
    for i in range(20):
        now = 100+i*.01
        d = c.step(now, telemetry(now), (candidate(1,100),), 1, 100, plan)
        assert not d.actions


def test_mode_confirmation_then_measured_stop_before_verification(cfg, options, plan):
    c = stopped_controller(cfg, options, plan)
    d = c.step(100.15, telemetry(100.15), (), 3, 100.15, plan)
    assert c.state == 'REQUEST_STOP' and [a.kind for a in d.actions] == ['stop']
    for i in range(4, 20):
        now = 100+i*.05
        d = c.step(now, telemetry(now, mode='GUIDED', vn=1.5), (candidate(i,now,metric=True),), i, now, plan)
        assert c.state == 'STOPPING'
        assert [a.kind for a in d.actions] == ['stop']
    for i in range(20, 28):
        now = 100+i*.05
        d = c.step(now, telemetry(now, mode='GUIDED'), (candidate(i,now,metric=True),), i, now, plan)
        assert [a.kind for a in d.actions] == ['stop']
    assert c.state == 'VERIFYING'
    assert c.verify_hold.count <= 1  # Frenlenirken alınan kareler doğrulamaya eklenmedi.


@pytest.mark.parametrize('failure', ['no_target','no_geometry','wrong_color','jump','intermittent'])
def test_reject_resumes_same_waypoint_without_payload(cfg, options, plan, failure):
    c = stopped_controller(cfg, options, plan)
    seen, resume, mode = [], [], 'GUIDED'
    for i in range(3, 100):
        now = 100+i*.05
        xs = () if failure == 'no_target' else (candidate(i,now,
            color='kirmizi' if failure == 'wrong_color' else 'mavi',
            metric=failure in ('jump','intermittent'),
            box=(.01,.01,.1,.1) if failure == 'jump' else (.3,.2,.7,.8)),)
        if failure == 'intermittent' and i%2:
            xs = ()
        d = c.step(now, telemetry(now,mode=mode), xs, i, now, plan)
        seen.append(c.state)
        for a in d.actions:
            assert a.kind not in ('velocity','payload')
            if a.kind == 'resume': resume.append(a.values[0])
            if a.kind == 'mode': mode = a.values[0]
        if c.state == 'SEARCHING':
            break
    assert 'VERIFYING' in seen
    assert resume == [2] and mode == 'AUTO' and c.child is None
    assert c.retry_until['mavi'] > now
    assert not c.requested
    for j in range(1,10):
        at = now+j*.05
        d = c.step(at, telemetry(at), (candidate(100+j,at),), 100+j, at, plan)
        assert not d.actions  # Aynı yanlış renge hemen yeniden fren yok.


def test_verify_success_starts_centering_only_after_fresh_metric_hold(cfg, options, plan):
    c = stopped_controller(cfg, options, plan)
    began = None
    for i in range(3,60):
        now = 100+i*.05
        before = c.state
        d = c.step(now, telemetry(now,mode='GUIDED'), (candidate(i,now,metric=True),), i, now, plan)
        assert [a.kind for a in d.actions] == ['stop']
        if c.state == 'VERIFYING' and began is None: began = now
        if c.state == 'INTERCEPT':
            assert before == 'VERIFYING'
            assert now-began >= cfg.control.acquire_s
            assert c.verify_hold.count >= cfg.control.acquire_frames
            break
    assert c.state == 'INTERCEPT' and c.child.state == 'CENTERING'


@pytest.mark.parametrize('phase', ['REQUEST_STOP','STOPPING','VERIFYING'])
def test_pilot_keeps_control_in_every_new_phase(cfg, options, plan, phase):
    c = stopped_controller(cfg, options, plan)
    now = 100.1
    for i in range(3,30):
        if c.state == phase: break
        now = 100+i*.05
        c.step(now, telemetry(now,mode='GUIDED'), (), i, now, plan)
    assert c.state == phase
    now += .05
    d = c.step(now, telemetry(now,mode='LOITER',rc_selected_mode='LOITER'), (), 100, now, plan)
    assert d.state == 'PILOT_CONTROL' and [a.kind for a in d.actions] == ['revoke']
    d = c.step(now+.05, telemetry(now+.05), (), 101, now+.05, plan)
    assert not d.actions


def test_braking_timeout_aborts_without_center_or_release(cfg, options, plan):
    c = stopped_controller(cfg, replace(options, stop_timeout_s=.5), plan)
    for i in range(3,20):
        now = 100+i*.05
        d = c.step(now, telemetry(now,mode='GUIDED',vn=1), (), i, now, plan)
        if c.state == 'ABORTED': break
    assert c.state == 'ABORTED'
    assert [a.kind for a in d.actions] == ['stop','mode','revoke']


def test_camera_failure_during_verification_aborts_instead_of_resume(cfg, options, plan):
    c = stopped_controller(cfg, options, plan)
    for i in range(3,30):
        now = 100+i*.05
        c.step(now, telemetry(now,mode='GUIDED'), (), i, now, plan)
        if c.state == 'VERIFYING': break
    d = c.step(now+.05, telemetry(now+.05,mode='GUIDED'), (), i, now-1, plan)
    assert d.state == 'ABORTED'
    assert not any(a.kind in ('resume','payload') for a in d.actions)


def test_controller_stall_during_braking_aborts(cfg, options, plan):
    c = stopped_controller(cfg, options, plan)
    c.step(100.15, telemetry(100.15,mode='GUIDED'), (), 3, 100.15, plan)
    d = c.step(101., telemetry(101.,mode='GUIDED'), (), 4, 101., plan)
    assert d.state == 'ABORTED'
    assert [a.kind for a in d.actions] == ['stop','mode','revoke']


def test_raw_candidate_survives_missing_pose_or_rejected_geometry(cfg):
    f = Frame(1,100.,100.,np.zeros((720,1280,3),np.uint8),
              (Detection('mavi_hedef',.9,(.3,.2,.7,.8)),),'TEST')
    vision = DualVision(cfg)
    xs, _ = vision.detect(f)
    assert len(xs) == 1 and xs[0].metric is None
    vision.geometry['mavi'] = Mock()
    vision.geometry['mavi'].detect.return_value = ()
    xs, _ = vision.detect(f,pose=Mock())
    assert len(xs) == 1 and xs[0].metric is None


def test_mode_transition_arms_zero_velocity_watchdog(cfg, options, plan, tmp_path):
    link, conn, _ = link_ready(cfg, replace(options,strategy='center'), plan, tmp_path)
    link._perform(100., (Action('claim',(6,)),Action('mode',('GUIDED','AUTO'))))
    assert link.velocity == (0.,0.,0.)
    assert link.velocity_until == 100.+cfg.link.command_lease_s
    conn.mav.set_position_target_local_ned_send.assert_not_called()
    link.store.value = telemetry(100.1)
    link._perform(100.1,(Action('stop'),))
    assert link.velocity_until == 100.1+cfg.link.command_lease_s
