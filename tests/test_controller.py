import math
from collections import deque
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
    # PnP boşluğu kademeli: kısa boşlukta son komut korunur, kare aralığı
    # sınırı aşılınca hareket durur, uzun kayıpta görev iptal edilir.
    c, now, fid = engage(cfg, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    d = c.step(now + .1, telemetry(now + .1, mode="GUIDED"), (), fid + 1, now + .1, mission)
    assert [a.kind for a in d.actions] == ["velocity"]
    assert not any(a.kind == "release" for a in d.actions)
    gap = cfg.control.max_lock_frame_gap_s + .05
    d = c.step(now + gap, telemetry(now + gap, mode="GUIDED"), (), fid + 2, now + gap, mission)
    assert [a.kind for a in d.actions] == ["stop"]
    d = c.step(now + 1.2, telemetry(now + 1.2, mode="GUIDED"), (), fid + 3, now + 1.2, mission)
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


def test_soft_descent_caps_command_filters_height_spike_and_stops_overspeed(cfg, mission):
    control = replace(cfg.control, max_descent_mps=.25, max_accel_mps2=.2)
    selected = replace(cfg, control=control)
    c, now, fid = engage(selected, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    # Tek PnP karesi yer düzlemini 20 m sıçratsa bile son yedi ölçümün
    # medyanı kullanılır; komut yumuşak iniş sınırını aşmaz.
    stamp = now+.1
    spike = target(fid+1, stamp, ground_down=20., camera_height_m=25.)
    d = c.step(stamp, telemetry(stamp, mode='GUIDED'), (spike,), fid+1, stamp, mission)
    velocity = next(a.values for a in d.actions if a.kind == 'velocity')
    assert 0 <= velocity[2] <= .25
    assert d.camera_height_m < 8.
    # Araç yine de sınırdan hızlı aşağı gidiyorsa sıfır hız komutu verilir.
    stamp += .1
    d = c.step(stamp, telemetry(stamp, mode='GUIDED', vd=.5),
               (target(fid+2, stamp),), fid+2, stamp, mission)
    assert [a.kind for a in d.actions] == ['stop']
    assert 'Düşey hız sınırı' in d.reason


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


def test_descent_uses_conservative_fc_height_when_pnp_reads_too_high(cfg, mission):
    control = replace(cfg.control, target_camera_height_m=5., minimum_camera_height_m=3.,
                      height_tolerance_m=1., max_descent_mps=.25, max_accel_mps2=.2)
    selected = replace(cfg, control=control)
    c, now, fid = engage(selected, mission)
    now, fid = move_to_descent(c, now, fid, mission)
    releases = []
    # Gerçek kayıtta PnP yaklaşık 1,2 m yüksek okuyordu. FC kamera
    # yüksekliği 5 m iken PnP 6,2 m dese de kod daha da alçalmamalı.
    for i in range(1, 60):
        stamp = now + i * .1
        t = telemetry(stamp, mode='GUIDED', down=-5.05, relative_alt_m=5.05)
        reading = target(fid + i, stamp, ground_down=1.2, camera_height_m=6.2)
        d = c.step(stamp, t, (reading,), fid + i, stamp, mission)
        releases.extend(a for a in d.actions if a.kind == 'release')
        if releases:
            break
    assert len(releases) == 1
    assert releases[0].values[2] == pytest.approx(5., abs=.05)


def test_telemetry_failure_during_guided_aborts(cfg, mission):
    c, now, fid = engage(cfg, mission)
    d = c.step(now + .1, telemetry(now + .1, mode="GUIDED", position_at=now - 2),
               (target(fid + 1, now + .1),), fid + 1, now + .1, mission)
    assert d.state == "ABORTED"
    assert not any(a.kind == "release" for a in d.actions)


@pytest.mark.parametrize('start_height_m',[17., 35.])
def test_high_altitude_descent_reaches_release_before_timeout(cfg, mission, start_height_m):
    """35 m'den bırakma yüksekliğine inmek eski 0,15 m/s ile 173 s sürüyordu ve
    90 s'lik merkezleme/alçalma sınırına takılıyordu. Yarışma profili değerleriyle
    (9 m bırakma, 0,25 m/s alçalma, 200 s sınır) alçalma tamamlanmalı."""
    control = replace(cfg.control, target_camera_height_m=9., minimum_camera_height_m=8.5,
                      minimum_intercept_relative_alt_m=9.5, acquire_s=.5,
                      max_descent_mps=.25, max_climb_mps=1., max_accel_mps2=.2,
                      interaction_timeout_s=200.)
    c = replace(cfg, control=control)
    control_loop = Controller(c)
    ground_down, offset = 0., c.camera.offset_body_m[2]
    down, dt = -(start_height_m+offset), .05
    def sample(fid, now):
        return target(fid, now, ground_down=ground_down, camera_height_m=ground_down-down-offset,
                      north=0., east=0.)
    control_loop.step(99., telemetry(99., armed=False, landed=1), (), None, 0., mission)
    released, elapsed, vd, mode = None, None, 0., 'AUTO'
    start = 100.
    for i in range(4000):
        now = start+i*dt
        t = telemetry(now, mode=mode, down=down, vd=vd, relative_alt_m=-down)
        d = control_loop.step(now, t, (sample(i, now),), i, now, mission)
        for a in d.actions:
            if a.kind == 'mode': mode = a.values[0]
            if a.kind == 'velocity': vd = float(a.values[2])
            if a.kind == 'release': released, elapsed = now, now-control_loop.interaction_started
        if released: break
        down += vd*dt
    assert released is not None, f'{control_loop.state}: {control_loop.reason}'
    assert elapsed < control.interaction_timeout_s
    assert abs((ground_down-down-offset) - control.target_camera_height_m) <= control.height_tolerance_m


def simulate_center_release(cfg, mission, control, seed=7, metric_yield=.26, steps=8000,
                            start_height_m=17., filter_window=7):
    """Ölçülen PnP gürültüsüyle merkezleme→alçalma→bırakma benzetimi.
    11 Eylül ana uçuşu: yatay sd 0,12 m, görsel yükseklik sd 0,39 m, metrik
    geometri karelerin yaklaşık dörtte birinde çözüldü."""
    import random
    rng = random.Random(seed)
    c = replace(cfg, control=control)
    loop = Controller(c)
    loop.target_samples = deque(maxlen=filter_window)
    offset = c.camera.offset_body_m[2]
    north, east, down = 3., -2., -(start_height_m+offset)
    vn = ve = vd = 0.
    dt, mode, released = .05, 'AUTO', None
    loop.step(99., telemetry(99., armed=False, landed=1), (), None, 0., mission)
    last = None
    for i in range(steps):
        now = 100+i*dt
        t = telemetry(now, mode=mode, north=north, east=east, down=down,
                      vn=vn, ve=ve, vd=vd, relative_alt_m=-down)
        seen = ()
        height = -down-offset
        if rng.random() < metric_yield or loop.state == 'SEARCHING':
            # Gürültü yükseklikle büyür: 10 m'de ölçülen 0,12 m yatay ve 0,39 m
            # yükseklik saçılması açısal/menzil bağıntısıyla ölçeklenir.
            last = target(i, now, north=rng.gauss(0, .012*height), east=rng.gauss(0, .012*height),
                          ground_down=rng.gauss(0, .0039*height*height),
                          camera_height_m=height, reprojection_px=.7)
            seen = (last,)
        d = loop.step(now, t, seen, i, now, mission)
        for a in d.actions:
            if a.kind == 'mode': mode = a.values[0]
            if a.kind == 'velocity': vn, ve, vd = (float(v) for v in a.values)
            if a.kind == 'stop': vn = ve = vd = 0.
            if a.kind == 'release': released = now-loop.interaction_started
        if released or loop.state in ('ABORTED', 'PILOT_CONTROL'): break
        north += vn*dt; east += ve*dt; down += vd*dt
    return loop, released, math.hypot(north, east), -down-offset


def competition_control(cfg, **changes):
    base = dict(target_camera_height_m=9., minimum_camera_height_m=7., height_tolerance_m=1.,
                center_tolerance_m=.5, descent_center_tolerance_m=.7, acquire_s=.5,
                center_tolerance_height_ratio=.05, max_horizontal_speed_mps=.8,
                release_horizontal_speed_mps=.3, release_vertical_speed_mps=.2,
                lost_target_abort_s=2.5, max_descent_mps=.25, max_climb_mps=1.,
                max_accel_mps2=.2,
                interaction_timeout_s=200., minimum_intercept_relative_alt_m=9.5)
    return replace(cfg.control, **{**base, **changes})


@pytest.mark.parametrize('metric_yield',[.4,.6,.8])
def test_center_release_completes_under_measured_pnp_noise(cfg, mission, metric_yield):
    control = competition_control(cfg, max_horizontal_speed_mps=.8)
    loop, released, error, height = simulate_center_release(cfg, mission, control,
                                                            metric_yield=metric_yield)
    assert released is not None, f'{loop.state}: {loop.reason}'
    assert released < control.interaction_timeout_s
    assert error <= control.center_tolerance_m
    assert abs(height-control.target_camera_height_m) <= control.height_tolerance_m


def test_old_unsmoothed_tight_tolerances_could_not_release_under_that_noise(cfg, mission):
    # Eski tek-kare PnP kullanımı ve dar toleranslar kilidi tamamlayamıyordu.
    control = competition_control(cfg, center_tolerance_m=.2, descent_center_tolerance_m=.3,
                                  height_tolerance_m=.25, minimum_camera_height_m=8.5,
                                  release_horizontal_speed_mps=.2, release_vertical_speed_mps=.12,
                                  lost_target_abort_s=1., max_horizontal_speed_mps=.8)
    loop, released, _, _ = simulate_center_release(cfg, mission, control, metric_yield=.4,
                                                    filter_window=1)
    assert released is None


@pytest.mark.parametrize('start_height_m',[15., 17., 25.])
@pytest.mark.parametrize('metric_yield',[.5, .8])
def test_center_release_from_competition_altitude(cfg, mission, start_height_m, metric_yield):
    """25 m'den bırakma: gürültü yükseklikle büyüdüğü için kilit toleransı da
    yükseklikle genişler, bırakma yüksekliğinde sabit 0,5 m'ye iner."""
    control = competition_control(cfg)
    loop, released, error, height = simulate_center_release(
        cfg, mission, control, metric_yield=metric_yield, start_height_m=start_height_m)
    assert released is not None, f'{loop.state}: {loop.reason}'
    assert released < control.interaction_timeout_s
    assert error <= control.center_tolerance_m
    assert abs(height-control.target_camera_height_m) <= control.height_tolerance_m


def test_height_ratio_does_not_loosen_release_accuracy(cfg, mission):
    # Bırakma yüksekliğinde (9 m) oran 0,05 -> 0,45 m; sabit 0,50 m baskın kalır.
    control = competition_control(cfg)
    assert control.center_tolerance_height_ratio*control.target_camera_height_m < control.center_tolerance_m
    loop, released, error, height = simulate_center_release(
        cfg, mission, control, metric_yield=.8, start_height_m=25.)
    assert released is not None and error <= control.center_tolerance_m


def test_fixed_tolerance_cannot_lock_at_competition_altitude(cfg, mission):
    # Tek-kare PnP ve yükseklikle ölçeklenmeyen tolerans 25 m'de kilitlenemiyordu.
    control = competition_control(cfg, center_tolerance_height_ratio=0.)
    loop, released, _, height = simulate_center_release(
        cfg, mission, control, metric_yield=.6, start_height_m=25., filter_window=1)
    assert released is None and height > 15.
