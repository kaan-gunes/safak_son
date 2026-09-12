"""Anlık sahte GPS karesi görevi öldürmemeli; gerçek sürekli kayıp öldürmeli.

12 Eylül akşam uçuşu (sortie 20260912T180522Z) 26,8. saniyede ABORTED'a düştü:
`gps_fix=1 hdop=100.0 uydu=0`, GPS mesajı 0,189 s tazeydi, EKF bayrakları
geçerliydi (831 & 23 == 23) ve uçuşun kalanında gerçek alıcı 16 uyduyla
fix=5 (RTK) okudu. Örneklerin yalnız %3,4'ü sahteydi ve öbekler ~0,4 s
sürüyordu. Tek örnekte kalıcı iptal, 107 saniyelik uçuşu ve iki yükü kaybetti.
"""
from dataclasses import replace

import pytest

from conftest import telemetry
from safak_gorev2.competition.config import Options, Servo
from safak_gorev2.competition.controller import DualController, GPS_PROBLEM
from safak_gorev2.competition.route import mission_digest
from safak_gorev2.controller import telemetry_problem
from safak_gorev2.mavlink_io import validate_mission
from safak_gorev2.types import MissionItem


@pytest.fixture
def plan(mission):
    from dataclasses import replace as _r
    return validate_mission(list(mission.items[:-1])+[
        MissionItem(3, 16, 3, 410000100, 290000100, 6),
        _r(mission.items[-1], seq=4)])


@pytest.fixture
def options(plan):
    return Options(strategy='center', vehicle_type=13, sortie_id='test-flight',
        mission_fingerprint=mission_digest(plan), search_start_seq=2, search_end_seq=2,
        route_reviewed=True,
        entry_gates=(((40.999, 29.), (41.001, 29.)),),
        finish_gate=((40.999, 29.), (41.001, 29.)),
        flight_polygon=((40.99, 28.99), (41.01, 28.99), (41.01, 29.01), (40.99, 29.01)))


def test_gps_problem_text_matches_legacy(cfg):
    """Sabit, korunan controller.py'deki metinle birebir aynı olmalı."""
    now = 100.
    bad = telemetry(now, gps_fix=1, hdop=100., satellites=0)
    assert telemetry_problem(bad, now, cfg) == GPS_PROBLEM
    assert telemetry_problem(telemetry(now), now, cfg) is None


def running(c, now, plan, mode='AUTO'):
    """AUTO devralmis, karar dongusu kesintisiz bir kontrolcu."""
    c.saw_disarmed = True
    for i in range(3):
        t = telemetry(now-.15+i*.05, mode=mode)
        c.step(now-.15+i*.05, t, (), None, now-.15+i*.05, plan)
    assert c.started
    return c


def feed(c, plan, start, duration, step=.05, **bad):
    """bad telemetriyi duration boyunca besle; son karari dondur."""
    d = None
    now = start
    while now < start+duration:
        d = c.step(now, telemetry(now, **bad), (), None, now, plan)
        now += step
    return d


@pytest.fixture
def sahte():
    """Sahada olculen sahte kare: fix yok, uydu yok, HDOP tavan."""
    return dict(gps_fix=1, hdop=100., satellites=0)


def test_transient_spurious_gps_frame_does_not_abort(cfg, options, plan, sahte):
    o = replace(options, strategy='center', gps_grace_s=1.)
    c = running(DualController(cfg, o), 100., plan)
    d = feed(c, plan, 100., .4, **sahte)          # sahada olculen ~0,4 s obek
    assert d.state != 'ABORTED', d.reason
    assert 'sürerse iptal' in d.reason
    # Duzelince normale donmeli
    d = c.step(100.5, telemetry(100.5), (), None, 100.5, plan)
    assert d.state != 'ABORTED'
    assert c.gps_issue_since is None


def test_sustained_gps_loss_still_aborts(cfg, options, plan, sahte):
    o = replace(options, strategy='center', gps_grace_s=1.)
    c = running(DualController(cfg, o), 100., plan)
    d = feed(c, plan, 100., 1.5, **sahte)
    assert d.state == 'ABORTED'
    assert d.reason == GPS_PROBLEM


def test_grace_does_not_accumulate_lock_evidence(cfg, options, plan, sahte):
    """Bekleme suresince tarama sayaci sifirlanir; supheli karede kilit ilerlemez."""
    o = replace(options, strategy='center', gps_grace_s=1.)
    c = running(DualController(cfg, o), 100., plan)
    for h in c.holds.values():
        h.update(1, 100., True)
        assert h.count == 1
    feed(c, plan, 100., .2, **sahte)
    assert all(h.count == 0 for h in c.holds.values())


def test_zero_grace_keeps_old_behaviour(cfg, options, plan, sahte):
    """gps_grace_s=0 eski davranis: ilk ornekte iptal."""
    o = replace(options, strategy='center', gps_grace_s=0.)
    c = running(DualController(cfg, o), 100., plan)
    d = c.step(100., telemetry(100., **sahte), (), None, 100., plan)
    assert d.state == 'ABORTED'
    assert d.reason == GPS_PROBLEM


def test_other_problems_are_not_debounced(cfg, options, plan):
    """Yalniz GPS kapisi beklemeli; heartbeat/mod/EKF anlik kalmali."""
    o = replace(options, strategy='center', gps_grace_s=1.)
    for ad, kotu in (('EKF', dict(ekf_flags=0)),
                     ('heartbeat', dict(heartbeat_at=0.)),
                     ('sistem durumu', dict(system_status=3))):
        c = running(DualController(cfg, o), 100., plan)
        d = c.step(100., telemetry(100., **kotu), (), None, 100., plan)
        assert d.state == 'ABORTED', f'{ad} anlik iptal etmeliydi: {d.reason}'


def test_grace_is_validated(options):
    with pytest.raises(ValueError, match='gps_grace_s'):
        replace(options, gps_grace_s=-1.).validate()
    with pytest.raises(ValueError, match='gps_grace_s'):
        replace(options, gps_grace_s=99.).validate()
    replace(options, gps_grace_s=0.).validate()
    replace(options, gps_grace_s=3.).validate()
