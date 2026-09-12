"""Ana görev hızı ACK ile sınırlanır; hızlı görev komutları değişmez."""
from dataclasses import replace

import pytest
from pymavlink.dialects.v20 import ardupilotmega as mav

from conftest import telemetry
from test_competition import options, plan, candidate, ready, link_ready, source
from safak_gorev2.competition.config import Options
from safak_gorev2.types import Action


def speed_options(options):
    return replace(options, strategy='center', center_search_speed_mps=1.5)


def test_deployed_center_profiles_use_requested_two_point_five_mps():
    for path in ('config/ana-gorev.json', 'config/ana-imx708.json',
                 'config/ana-opencv-test.json', 'config/ana-aux1-only.json'):
        _, opts = Options.load(path)
        assert opts.center_search_speed_mps == 2.5


def test_search_waits_for_own_speed_ack_then_detects(cfg, options, plan):
    c = ready(cfg, speed_options(options), plan)
    d = c.step(100, telemetry(100), (candidate(0, 100),), 0, 100, plan)
    assert d.state == 'SET_SEARCH_SPEED'
    assert d.actions == (Action('search_speed', (1.5, 6)),)
    for i in range(1, 5):
        now = 100+i*.05
        d = c.step(now, telemetry(now), (candidate(i, now),), i, now, plan,
                   search_speed_status={'request_at': 90., 'status': 'ACCEPTED'})
        assert d.state == 'SET_SEARCH_SPEED' and not d.actions
    for i in range(5, 9):
        now = 100+i*.05
        d = c.step(now, telemetry(now), (candidate(i, now),), i, now, plan,
                   search_speed_status={'request_at': 100.01, 'status': 'ACCEPTED'})
        if d.state == 'REQUEST_STOP': break
    assert d.state == 'REQUEST_STOP'


@pytest.mark.parametrize('failure', ['timeout', 'rejected', 'pilot'])
def test_failed_speed_setup_never_claims_control(cfg, options, plan, failure):
    c = ready(cfg, speed_options(options), plan)
    c.step(100, telemetry(100), (), 0, 100, plan)
    now = 100.1 if failure != 'timeout' else 100+cfg.control.mode_timeout_s+.1
    d = c.step(now, telemetry(now, mode='LOITER' if failure=='pilot' else 'AUTO'),
               (candidate(1, now),), 1, now, plan,
               search_speed_status={'request_at': 100.01, 'status': 'REJECTED'} if failure=='rejected' else None)
    assert d.state == ('PILOT_CONTROL' if failure=='pilot' else 'ABORTED')
    assert [a.kind for a in d.actions] == ['revoke']


def test_link_speed_command_is_transient_center_only_and_acknowledged(cfg, options, plan, tmp_path):
    link, conn, _ = link_ready(cfg, speed_options(options), plan, tmp_path)
    link._perform(100, (Action('search_speed', (1.5, 6)),))
    conn.mav.command_long_send.assert_called_once_with(1, 1, 178, 0, 1, 1.5, -1, 0, 0, 0, 0)
    conn.mav.param_set_send.assert_not_called()
    assert link.snapshot_search_speed_status()['status'] == 'PENDING'
    link.ingest(source(mav.MAVLink_command_ack_message(183, 0)), 100.1)
    assert link.snapshot_search_speed_status()['status'] == 'PENDING'
    link.ingest(source(mav.MAVLink_command_ack_message(178, 0)), 100.2)
    assert link.snapshot_search_speed_status() == {'status': 'ACCEPTED', 'request_at': 100}


@pytest.mark.parametrize('bad', ['quick', 'disarmed', 'pilot', 'wrong_slot', 'wrong_speed', 'land', 'wrong_route', 'observe'])
def test_speed_command_guards(cfg, options, plan, tmp_path, bad):
    opts = options if bad=='quick' else speed_options(options)
    link, conn, _ = link_ready(cfg, opts, plan, tmp_path)
    if bad=='disarmed': link.store.value = telemetry(100, armed=False)
    if bad=='pilot': link.store.value = telemetry(100, mode='LOITER')
    if bad=='land': link.store.value = telemetry(100, mission_seq=plan.land_seq)
    if bad=='wrong_route': link.options = replace(opts, mission_fingerprint='wrong')
    if bad=='observe': link.allow_control = False
    link._perform(100, (Action('search_speed', (2 if bad=='wrong_speed' else 1.5, 4 if bad=='wrong_slot' else 6)),))
    conn.mav.command_long_send.assert_not_called()
    conn.mav.param_set_send.assert_not_called()


def test_quick_does_not_emit_speed_setup(cfg, options, plan):
    c = ready(cfg, options, plan)
    for i in range(4):
        now = 100+i*.05
        d = c.step(now, telemetry(now), (candidate(i, now),), i, now, plan)
        assert all(a.kind != 'search_speed' for a in d.actions)
        if c.state == 'REQUEST_STOP': break
    assert c.state == 'REQUEST_STOP'


def test_auto_resume_reapplies_center_speed(cfg, options, plan):
    c = ready(cfg, speed_options(options), plan)
    c.started = True
    c.rc_slot = 6
    c.search_speed_set = True
    c.begin_stop(100, telemetry(100), candidate(0, 100))
    c.transition('RESUME_AUTO', 100.1, 'test')
    c.last_step = 100.1
    c.step(100.2, telemetry(100.2), (), 1, 100.2, plan)
    assert c.state == 'SEARCHING' and not c.search_speed_set
    d = c.step(100.25, telemetry(100.25), (), 2, 100.25, plan)
    assert d.state == 'SET_SEARCH_SPEED'
    assert d.actions == (Action('search_speed', (1.5, 6)),)


def test_center_speed_waits_outside_field_before_entry(cfg, options, plan):
    c = ready(cfg, speed_options(options), plan)
    c.route.entry_count = 0
    c.route.previous = None
    d = c.step(100, telemetry(100, lat=40., lon=28.), (), 0, 100, plan)
    assert d.state not in ('ABORTED', 'SET_SEARCH_SPEED')
    assert not d.actions


def test_center_speed_waits_before_takeoff_sequence(cfg, options, plan):
    c = ready(cfg, speed_options(options), plan)
    d = c.step(100, telemetry(100, mission_seq=0), (), 0, 100, plan)
    assert not d.actions
