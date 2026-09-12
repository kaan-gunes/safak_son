from dataclasses import replace

import pytest

from conftest import telemetry
from test_competition import candidate, link_ready, options, plan, ready
from safak_gorev2.competition.config import COLORS, PAYLOAD
from safak_gorev2.controller import Controller
from safak_gorev2.types import Action


def awaiting_second(cfg, options, plan):
    c = ready(cfg, options, plan)
    c.step(100, telemetry(100), (), 0, 100, plan)
    c.child = Controller(cfg)
    c.selected = 'kirmizi'
    c.done = {'mavi'}
    c.requested = set(COLORS)
    c.transition('RELEASE_WAIT', 100, 'İkinci yük onayı bekleniyor')
    return c


@pytest.mark.parametrize('strategy', ['center', 'quick'])
@pytest.mark.parametrize('status', ['ACK_ACCEPTED', 'SIMULATED'])
def test_second_ack_flies_straight_to_land_waypoint(cfg, options, plan, strategy, status):
    # Kullanıcı isteği: ikinci yükten sonra kalan tarama waypointleri atlanır ve
    # doğrudan LAND waypointine uçulur.
    c = awaiting_second(cfg, replace(options, strategy=strategy), plan)
    assert not c.route.finished
    d = c.step(100.05, telemetry(100.05, mode='GUIDED'), (), 1, 100.05, plan,
               release_status={PAYLOAD[c.selected]: status})
    assert d.state == 'SELECT_LAND'
    assert d.actions == (Action('stop'), Action('mission_current', (plan.land_seq,)))
    # Görev sırası henüz doğrulanmadı: AUTO devri veya yükselme yapılmaz.
    d = c.step(100.1, telemetry(100.1, mode='GUIDED'), (), 2, 100.1, plan)
    assert d.state == 'SELECT_LAND' and d.actions == (Action('stop'),)
    d = c.step(100.15, telemetry(100.15, mode='GUIDED', mission_seq=plan.land_seq), (), 3, 100.15, plan)
    assert d.state == 'HANDOFF_LAND' and d.actions == (Action('stop'), Action('mode', ('AUTO', 'GUIDED')))
    d = c.step(100.2, telemetry(100.2, mode='AUTO', mission_seq=plan.land_seq), (), 4, 100.2, plan)
    assert d.state == 'LANDING' and d.actions == (Action('revoke'),)
    # İniş görüntüye veya kalan rotanın bitiş kapısına bağlı değildir.
    d = c.step(101, telemetry(101, mode='AUTO', mission_seq=plan.land_seq, landed=4), (), None, 0, plan)
    assert d.state == 'LANDING' and not d.actions
    d = c.step(101.05, telemetry(101.05, mode='AUTO', mission_seq=plan.land_seq,
                                 armed=False, landed=1), (), None, 0, plan)
    assert d.state == 'DONE' and not c.route.finished
    assert not c.step(101.1, telemetry(101.1), (candidate(6, 101.1),), 6, 101.1, plan).actions


def test_aux1_only_ignores_blue_target_and_lands_after_red_target_ack(cfg, options, plan):
    opts = replace(options, strategy='center', payloads=('mavi',))
    c = ready(cfg, opts, plan)
    c.step(100, telemetry(100), (), 0, 100, plan)
    for i in range(1, 12):
        now = 100+i*.05
        d = c.step(now, telemetry(now), (candidate(i, now, 'mavi'),), i, now, plan)
        assert c.child is None and not any(a.kind == 'payload' for a in d.actions)
    c.child = Controller(cfg)
    c.selected = 'kirmizi'
    c.requested = {'kirmizi'}
    c.transition('RELEASE_WAIT', 100.6, 'AUX1 onayı bekleniyor')
    d = c.step(100.65, telemetry(100.65, mode='GUIDED'), (), 20, 100.65, plan,
               release_status={'mavi': 'ACK_ACCEPTED'})
    assert c.done == {'kirmizi'}
    assert d.state == 'SELECT_LAND'
    assert d.actions == (Action('stop'), Action('mission_current', (plan.land_seq,)))


def test_wrong_waypoint_after_handoff_aborts(cfg, options, plan):
    c = awaiting_second(cfg, options, plan)
    c.step(100.05, telemetry(100.05, mode='GUIDED'), (), 1, 100.05, plan,
           release_status={PAYLOAD[c.selected]: 'SIMULATED'})
    c.step(100.15, telemetry(100.15, mode='GUIDED', mission_seq=plan.land_seq), (), 3, 100.15, plan)
    d = c.step(100.2, telemetry(100.2, mode='AUTO', mission_seq=2), (), 4, 100.2, plan)
    assert d.state == 'PILOT_CONTROL' and not any(a.kind == 'resume' for a in d.actions)


@pytest.mark.parametrize('status', ['SENT', 'RESERVED', 'REJECTED', 'UNCERTAIN', 'BLOCKED'])
def test_unconfirmed_second_payload_never_requests_land(cfg, options, plan, status):
    c = awaiting_second(cfg, options, plan)
    d = c.step(100.05, telemetry(100.05, mode='GUIDED'), (), 1, 100.05, plan,
               release_status={PAYLOAD[c.selected]: status})
    assert c.done == {'mavi'}
    assert not any(a.kind == 'mission_current' for a in d.actions)


@pytest.mark.parametrize('case', ['timeout', 'pilot', 'stale'])
def test_land_failure_never_resumes_route(cfg, options, plan, case):
    c = awaiting_second(cfg, options, plan)
    c.step(100.05, telemetry(100.05, mode='GUIDED'), (), 1, 100.05, plan,
           release_status={PAYLOAD[c.selected]: 'SIMULATED'})
    now = 100.1
    t = telemetry(now, mode='GUIDED')
    if case == 'timeout':
        c.entered = now - cfg.control.mode_timeout_s - .1
    if case == 'pilot':
        t = replace(t, mode='LOITER', rc_selected_mode='LOITER', rc_slot=1)
    if case == 'stale':
        t = replace(t, heartbeat_at=90)
    d = c.step(now, t, (), 2, now, plan)
    assert d.state == ('PILOT_CONTROL' if case == 'pilot' else 'ABORTED')
    assert not any(a.kind == 'resume' or (a.kind == 'mode' and a.values[0] in ('AUTO', 'LAND')) for a in d.actions)
    assert not c.step(100.15, telemetry(100.15), (), 3, 100.15, plan).actions


def test_link_selects_land_waypoint_then_hands_off_and_releases_ownership(cfg, options, plan, tmp_path):
    link, conn, _ = link_ready(cfg, options, plan, tmp_path)
    link.store.value = telemetry(100, mode='GUIDED')
    link.owned = True
    link.claim_slot = 6
    link._perform(100, (Action('stop'), Action('mission_current', (plan.land_seq,))))
    conn.mav.mission_set_current_send.assert_called_once_with(1, 1, plan.land_seq)
    conn.mav.set_mode_send.assert_not_called()
    link._perform(100.02, (Action('stop'), Action('mode', ('AUTO', 'GUIDED'))))
    conn.mav.set_mode_send.assert_called_once_with(1, 1, 3)
    assert link.expected_modes == {'GUIDED', 'AUTO'}
    link.store.value = telemetry(100.05, mode='AUTO', mission_seq=plan.land_seq)
    link._perform(100.05, (Action('revoke'),))
    assert not link.owned and link.velocity is None


def test_link_refuses_mission_current_for_non_land_sequence(cfg, options, plan, tmp_path):
    link, conn, _ = link_ready(cfg, options, plan, tmp_path)
    link.store.value = telemetry(100, mode='GUIDED')
    link.owned = True
    link.claim_slot = 6
    link._perform(100, (Action('mission_current', (2,)),))
    conn.mav.mission_set_current_send.assert_not_called()
