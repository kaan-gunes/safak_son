import math
from dataclasses import replace

import pytest

from safak_gorev2.controller import Controller, ContinuousHold
from conftest import target, telemetry


def engage(cfg, mission):
    control = Controller(cfg)
    control.step(99., telemetry(99., armed=False, landed=1), (), None, 0., mission)
    for i in range(15):
        now = 100 + i * .1
        d = control.step(now, telemetry(now), (target(i, now),), i, now, mission)
        if d.state == "REQUEST_GUIDED":
            return control, now, i
    raise AssertionError("GUIDED istenmedi")


def move_to_descent(control, now, frame_id, mission):
    for i in range(1, 22):
        stamp = now + i * .1
        d = control.step(stamp, telemetry(stamp, mode="GUIDED"),
                         (target(frame_id + i, stamp),), frame_id + i, stamp, mission)
        if d.state == "DESCENDING":
            return stamp, frame_id + i
    raise AssertionError("Merkezleme kilidi alınamadı")


def test_no_midair_restart_takeover(cfg, mission):
    c = Controller(cfg)
    for i in range(50):
        now = 100 + i * .1
        d = c.step(now, telemetry(now), (target(i, now),), i, now, mission)
        assert not d.actions
    assert c.state == "WAIT_AUTO"


def test_detection_during_takeoff_does_not_interrupt_takeoff(cfg, mission):
    c = Controller(cfg)
    c.saw_disarmed = True
    for i in range(50):
        now = 100 + i * .1
        d = c.step(now, telemetry(now, mission_seq=1), (target(i, now),), i, now, mission)
        assert not d.actions


def test_dwell_only_unique_contiguous_samples():
    hold = ContinuousHold(.25)
    assert hold.update(1, 100., True) == 0
    assert hold.update(2, 100.2, True) == pytest.approx(.2)
    for _ in range(100):
        assert hold.update(2, 100.2, True) == pytest.approx(.2)
    assert hold.update(3, 100.8, True) == 0
    assert hold.update(4, 100.9, False) == 0


def test_guided_mode_must_be_observed(cfg, mission):
    c, now, fid = engage(cfg, mission)
    d = c.step(now + .1, telemetry(now + .1), (target(fid + 1, now + .1),), fid + 1, now + .1, mission)
    assert d.state == "REQUEST_GUIDED"
    assert not d.actions


@pytest.mark.parametrize("change", [{"mode": "LOITER"}, {"rc_slot": 1, "rc_selected_mode": "LOITER"}, {"mode": "LAND"}])
def test_pilot_or_autopilot_mode_change_revokes_without_countercommand(cfg, mission, change):
    c, now, fid = engage(cfg, mission)
    t = telemetry(now + .1, mode="GUIDED")
    d = c.step(now + .1, replace(t, **change), (target(fid + 1, now + .1),), fid + 1, now + .1, mission)
    assert d.state == "PILOT_CONTROL"
    assert [a.kind for a in d.actions] == ["revoke"]
    d = c.step(now + 1, telemetry(now + 1), (target(fid + 2, now + 1),), fid + 2, now + 1, mission)
    assert not d.actions


def test_target_loss_stops_descent_and_never_releases(cfg, mission):
    c, now, fid = engage(cfg, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    d = c.step(now + .1, telemetry(now + .1, mode="GUIDED"), (), fid + 1, now + .1, mission)
    assert [a.kind for a in d.actions] == ["stop"]
    assert d.lock_s == 0
    d = c.step(now + 1.2, telemetry(now + 1.2, mode="GUIDED"), (), fid + 2, now + 1.2, mission)
    assert d.state == "ABORTED"
    assert not c.release_requested


def test_stale_or_future_frame_never_counts(cfg, mission):
    for difference in (-1, 1):
        c = Controller(cfg)
        c.saw_disarmed = True
        for i in range(40):
            now = 100 + i * .1
            d = c.step(now, telemetry(now), (target(i, now + difference),), i, now + difference, mission)
            assert not d.actions


@pytest.mark.parametrize("bad", [{"roll": .25}, {"vn": .4}, {"vd": .25}])
def test_unstable_quad_cannot_release(cfg, mission, bad):
    c, now, fid = engage(cfg, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    for i in range(1, 60):
        stamp = now + i * .1
        t = telemetry(stamp, mode="GUIDED", down=-3.55, relative_alt_m=3.55)
        d = c.step(stamp, replace(t, **bad), (target(fid + i, stamp, camera_height_m=3.5),), fid + i, stamp, mission)
        assert not any(a.kind == "release" for a in d.actions)


def test_descent_does_not_stop_merely_because_it_is_descending(cfg, mission):
    c, now, fid = engage(cfg, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    for i in range(1, 8):
        stamp = now + i * .1
        d = c.step(stamp, telemetry(stamp, mode="GUIDED", vd=.15),
                   (target(fid + i, stamp),), fid + i, stamp, mission)
    velocity = next(a.values for a in d.actions if a.kind == "velocity")
    assert velocity[2] > 0
    assert d.lock_s == 0


def test_release_once_then_confirmed_land_handoff(cfg, mission):
    c, now, fid = engage(cfg, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    releases = []
    for i in range(1, 40):
        stamp = now + i * .1
        d = c.step(stamp, telemetry(stamp, mode="GUIDED", down=-3.55, relative_alt_m=3.55),
                   (target(fid + i, stamp, camera_height_m=3.5),), fid + i, stamp, mission)
        releases += [a for a in d.actions if a.kind == "release"]
        if d.state == "RELEASE_PENDING":
            now = stamp
            break
    assert len(releases) == 1
    assert d.state == "RELEASE_PENDING"
    d = c.step(now + .1, telemetry(now + .1, mode="GUIDED"), (), None, 0, mission, release_recorded=True)
    assert d.state == "RETURN_CLIMB"
    for i in range(2, 30):
        stamp = now + i * .1
        d = c.step(stamp, telemetry(stamp, mode="GUIDED"), (), None, 0, mission, release_recorded=True)
        if d.state == "SELECT_LAND":
            now = stamp
            break
    assert d.state == "SELECT_LAND"
    assert [a.kind for a in d.actions] == ["stop", "mission_current"]
    # Eski MISSION_CURRENT doğrulama sayılmaz.
    d = c.step(now + .1, telemetry(now + .1, mode="GUIDED", mission_seq=3, mission_at=now - 1),
               (), None, 0, mission, release_recorded=True)
    assert d.state == "SELECT_LAND"
    d = c.step(now + .2, telemetry(now + .2, mode="GUIDED", mission_seq=3), (), None, 0, mission, release_recorded=True)
    assert d.state == "HANDOFF_LAND"
    assert any(a.values == ("AUTO", "GUIDED") for a in d.actions)
    d = c.step(now + .3, telemetry(now + .3, mode="AUTO", mission_seq=3), (), None, 0, mission, release_recorded=True)
    assert d.state == "LANDING"
    d = c.step(now + .4, telemetry(now + .4, mode="AUTO", mission_seq=3, armed=False, landed=1),
               (), None, 0, mission, release_recorded=True)
    assert d.state == "DONE"


def test_telemetry_failure_during_guided_aborts(cfg, mission):
    c, now, fid = engage(cfg, mission)
    d = c.step(now + .1, telemetry(now + .1, mode="GUIDED", position_at=now - 2),
               (target(fid + 1, now + .1),), fid + 1, now + .1, mission)
    assert d.state == "ABORTED"
    assert not any(a.kind == "release" for a in d.actions)
