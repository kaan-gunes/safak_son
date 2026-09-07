from dataclasses import replace
from safak_gorev2.controller import Controller
from conftest import telemetry


def released_controller(cfg):
    cfg=replace(cfg,mission=replace(cfg.mission,return_mode='rtl'))
    c=Controller(cfg);c.state='RELEASE_PENDING';c.entered=99.5;c.rc_slot=6;c.release_requested=True
    return c


def test_rtl_waits_for_durable_release_and_fresh_mode_confirmation(cfg,mission):
    c=released_controller(cfg)
    d=c.step(100.,telemetry(100.,mode='GUIDED'),(),None,0,mission,release_recorded=False)
    assert [a.kind for a in d.actions]==['stop']
    d=c.step(100.1,telemetry(100.1,mode='GUIDED'),(),None,0,mission,release_recorded=True)
    assert d.state=='REQUEST_RTL' and [a.values for a in d.actions]==[(),('RTL','GUIDED')]
    d=c.step(100.2,telemetry(100.2,mode='RTL',heartbeat_at=100.),(),None,0,mission)
    assert d.state=='REQUEST_RTL'
    d=c.step(100.3,telemetry(100.3,mode='RTL'),(),None,0,mission)
    assert d.state=='RTL_RETURN' and [a.kind for a in d.actions]==['revoke']
    d=c.step(101.,telemetry(101.,mode='RTL',armed=False,landed=1),(),None,0,mission)
    assert d.state=='DONE' and not d.actions


def test_rtl_pilot_loiter_is_terminal_and_no_velocity_after_handoff(cfg,mission):
    c=released_controller(cfg)
    c.step(100.,telemetry(100.,mode='GUIDED'),(),None,0,mission,release_recorded=True)
    c.step(100.1,telemetry(100.1,mode='RTL'),(),None,0,mission)
    d=c.step(100.2,telemetry(100.2,mode='RTL'),(),None,0,mission)
    assert not d.actions
    d=c.step(100.3,telemetry(100.3,mode='LOITER',rc_slot=1,rc_selected_mode='LOITER'),(),None,0,mission)
    assert d.state=='PILOT_CONTROL'
    assert not c.step(100.4,telemetry(100.4),(),None,0,mission).actions


def test_unconfirmed_rtl_fails_to_loiter_without_selecting_land(cfg,mission):
    c=released_controller(cfg)
    c.step(100.,telemetry(100.,mode='GUIDED'),(),None,0,mission,release_recorded=True)
    d=c.step(103.1,telemetry(103.1,mode='GUIDED'),(),None,0,mission)
    assert d.state=='ABORTED'
    assert any(a.values==('LOITER','GUIDED') for a in d.actions)
    assert not any(a.kind=='mission_current' for a in d.actions)
