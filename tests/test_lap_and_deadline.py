"""Tarama turunu başa sarma ve görev süresi sonunda LAND waypointine gitme."""
from dataclasses import replace

import pytest

from conftest import telemetry
from test_competition import candidate, options, plan, ready
from safak_gorev2.competition.config import COLORS, PAYLOAD, Options
from safak_gorev2.competition.route import mission_digest
from safak_gorev2.controller import Controller
from safak_gorev2.types import Action


def looping(options, laps=2, deadline=600., intercept=None):
    return replace(options, search_laps=laps, mission_deadline_s=deadline,
                   intercept_deadline_s=intercept)


def flying(cfg, options, plan, now=100.):
    """AUTO devralınmış, tarama bölümünde uçan denetleyici."""
    c = ready(cfg, options, plan)
    c.step(now, telemetry(now), (), 0, now, plan)
    assert c.started and c.started_at == now
    return c


def running(c, now):
    """Karar döngüsü 20 Hz akıyormuş gibi; `gap` iptali test kurgusundan doğmasın."""
    c.last_step = now-.05
    return c


def land_sequence(c, plan, start, mode='GUIDED'):
    """SELECT_LAND -> HANDOFF_LAND -> LANDING zincirini yürüt."""
    d = c.step(start+.05, telemetry(start+.05, mode='GUIDED', mission_seq=plan.land_seq), (),
               1, start+.05, plan)
    assert d.state == 'HANDOFF_LAND'
    d = c.step(start+.1, telemetry(start+.1, mode='AUTO', mission_seq=plan.land_seq), (),
               2, start+.1, plan)
    return d


# ------------------------------------------------------------------ tur başa sarma

def test_search_end_with_missing_payload_restarts_the_lap(cfg, options, plan):
    o = looping(options)
    c = flying(cfg, o, plan)
    assert c.lap == 1 and not c.route.finished
    # Tarama bölümü bitti (seq 3 > search_end_seq 2), hiç yük bırakılmadı.
    d = c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    assert d.state == 'RELAP_CLAIM' and c.lap == 2
    assert d.actions == (Action('claim', (6,)), Action('mode', ('GUIDED', 'AUTO')))
    # GUIDED doğrulanınca tarama başlangıç waypointi seçilir.
    d = c.step(140.05, telemetry(140.05, mode='GUIDED', mission_seq=3), (), 2, 140.05, plan)
    assert d.state == 'RESUME_SELECT'
    assert d.actions == (Action('stop'), Action('resume', (2, mission_digest(plan))))
    assert c.route.finished is False  # Yeni tur için tarama izni geri verildi.
    # Sıra doğrulanınca AUTO'ya devredilir.
    d = c.step(140.1, telemetry(140.1, mode='GUIDED', mission_seq=2, mission_at=140.09), (),
               3, 140.1, plan)
    assert d.state == 'RESUME_AUTO' and Action('mode', ('AUTO', 'GUIDED')) in d.actions
    d = c.step(140.15, telemetry(140.15, mode='AUTO', mission_seq=2), (), 4, 140.15, plan)
    assert d.state == 'SEARCHING' and d.actions == (Action('revoke'),)
    assert c.child is None and c.search_speed_set is False


def test_second_lap_can_still_drop_the_remaining_payload(cfg, options, plan):
    o = looping(options)
    c = flying(cfg, o, plan)
    c.done, c.requested = {'mavi'}, {'mavi'}
    c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    c.step(140.05, telemetry(140.05, mode='GUIDED', mission_seq=3), (), 2, 140.05, plan)
    c.step(140.1, telemetry(140.1, mode='GUIDED', mission_seq=2, mission_at=140.09), (), 3, 140.1, plan)
    c.step(140.15, telemetry(140.15, mode='AUTO', mission_seq=2), (), 4, 140.15, plan)
    # İkinci turda kalan renk yeniden aday olabilmeli.
    for i in range(5, 12):
        now = 140.15+(i-4)*.05
        d = c.step(now, telemetry(now, mission_seq=2), (candidate(i, now, color='kirmizi'),),
                   i, now, plan)
        if d.state == 'REQUEST_STOP':
            break
    assert d.state == 'REQUEST_STOP' and c.selected == 'kirmizi'


def test_completed_payloads_go_to_land_not_another_lap(cfg, options, plan):
    o = looping(options)
    c = flying(cfg, o, plan)
    c.done = set(COLORS)
    d = c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    assert d.state == 'AUTO_FINISH' and c.lap == 1


def test_last_lap_falls_through_to_auto_finish(cfg, options, plan):
    c = flying(cfg, looping(options, laps=1), plan)
    d = c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    assert d.state == 'AUTO_FINISH' and c.lap == 1 and not d.actions


def test_lap_count_is_bounded(cfg, options, plan):
    c = flying(cfg, looping(options, laps=2), plan)
    c.lap = 2
    d = c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    assert d.state == 'AUTO_FINISH'


def test_relap_guided_timeout_aborts(cfg, options, plan):
    c = flying(cfg, looping(options), plan)
    c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    d = running(c, 144).step(144, telemetry(144, mission_seq=3), (), 2, 144, plan)
    assert d.state == 'ABORTED' and 'GUIDED' in d.reason


# ------------------------------------------------------------------ görev süresi

def test_deadline_from_searching_flies_to_land_waypoint(cfg, options, plan):
    o = looping(options, deadline=510.)
    c = flying(cfg, o, plan)
    d = c.step(100+509, telemetry(100+509), (), 1, 100+509, plan)
    assert d.state == 'SEARCHING'
    start = 100+510
    d = c.step(start, telemetry(start), (), 2, start, plan)
    assert d.state == 'TIME_LAND_CLAIM'
    assert d.actions == (Action('claim', (6,)), Action('mode', ('GUIDED', 'AUTO')))
    d = c.step(start+.01, telemetry(start+.01, mode='GUIDED'), (), 3, start+.01, plan)
    assert d.state == 'SELECT_LAND'
    assert d.actions == (Action('stop'), Action('mission_current', (plan.land_seq,)))
    assert land_sequence(c, plan, start+.01).state == 'LANDING'


def test_deadline_abandons_an_unfinished_intercept(cfg, options, plan):
    o = looping(options, deadline=510.)
    c = flying(cfg, o, plan)
    c.child, c.selected = Controller(cfg), 'mavi'
    c.transition('INTERCEPT', 200, 'Merkezleme sürüyor')
    start = 100+510
    d = running(c, start).step(start, telemetry(start, mode='GUIDED'), (), 1, start, plan)
    # Kontrol zaten bizdeyken ek mod isteği yok; doğrudan LAND sırası seçilir.
    assert d.state == 'SELECT_LAND'
    assert d.actions == (Action('stop'), Action('mission_current', (plan.land_seq,)))
    assert land_sequence(c, plan, start).state == 'LANDING'


def test_deadline_does_not_interrupt_a_pending_payload_command(cfg, options, plan):
    o = looping(options, deadline=510.)
    c = flying(cfg, o, plan)
    c.child, c.selected = Controller(cfg), 'mavi'
    c.requested = {'mavi'}
    c.transition('RELEASE_WAIT', 100+509, 'Yük komutu bekleniyor')
    start = 100+510
    d = running(c, start).step(start, telemetry(start, mode='GUIDED'), (), 1, start, plan,
                               release_status={PAYLOAD['mavi']: 'SIMULATED'})
    # Yük sonucu kaydedilir; süre sonu bir sonraki adımda devreye girer.
    assert d.state != 'TIME_LAND_CLAIM' and 'mavi' in c.done


def test_deadline_stops_a_second_lap_from_running_forever(cfg, options, plan):
    o = looping(options, laps=5, deadline=510.)
    c = flying(cfg, o, plan)
    start = 100+510
    d = c.step(start, telemetry(start, mission_seq=3), (), 1, start, plan)
    assert d.state == 'TIME_LAND_CLAIM' and c.lap == 1  # Yeni tur açılmadı.


def test_intercept_deadline_blocks_new_targets_only(cfg, options, plan):
    o = looping(options, deadline=510., intercept=450.)
    c = flying(cfg, o, plan)
    seen = None
    for i in range(1, 12):
        now = 100+449+i*.05
        seen = c.step(now, telemetry(now), (candidate(i, now),), i, now, plan)
        if seen.state == 'REQUEST_STOP':
            break
    assert seen.state == 'REQUEST_STOP'  # Sınırdan önce normal davranış.

    c = flying(cfg, o, plan)
    for i in range(1, 12):
        now = 100+450+i*.05
        d = c.step(now, telemetry(now), (candidate(i, now),), i, now, plan)
        assert d.state == 'SEARCHING'
    assert 'Süre sonuna yakın' in d.reason


def test_deadline_only_counts_from_auto_takeover(cfg, options, plan):
    o = looping(options, deadline=510.)
    c = ready(cfg, o, plan)
    assert c.started_at is None
    # Yerde beklerken saat işlemez.
    c.step(100, telemetry(100, mode='LOITER', rc_selected_mode='AUTO'), (), 0, 100, plan)
    assert c.started_at is None
    c.step(1000, telemetry(1000), (), 1, 1000, plan)
    assert c.started_at == 1000
    d = c.step(1000+509, telemetry(1000+509), (), 2, 1000+509, plan)
    assert d.state == 'SEARCHING'
    d = c.step(1000+510, telemetry(1000+510), (), 3, 1000+510, plan)
    assert d.state == 'TIME_LAND_CLAIM'


# ------------------------------------------------------------------ yapılandırma

@pytest.mark.parametrize('values', [
    {'search_laps': 0}, {'search_laps': 11}, {'search_laps': 2},
    {'mission_deadline_s': 10}, {'mission_deadline_s': 4000},
    {'mission_deadline_s': 300, 'intercept_deadline_s': 400},
])
def test_invalid_lap_and_deadline_settings_rejected(values):
    with pytest.raises(ValueError):
        replace(Options(), **values).validate()


def test_defaults_keep_the_old_behaviour():
    o = Options()
    assert o.search_laps == 1 and o.mission_deadline_s is None and o.intercept_deadline_s is None


# ------------------------------------------------------------------ MAVLink'e ulaşan komut

def test_relap_actually_sends_mission_set_current_to_the_autopilot(cfg, options, plan, tmp_path):
    """Kararın MAVLink'e döndüğünü kanıtlar; SITL rotası bu pencereyi sınamıyor."""
    from test_competition import link_ready
    o = looping(options)
    link, conn, _ = link_ready(cfg, o, plan, tmp_path)
    link.owned, link.claim_slot = True, 6
    link.store.value = telemetry(100, mode='GUIDED')
    c = flying(cfg, o, plan)
    c.step(140, telemetry(140, mission_seq=3), (), 1, 140, plan)
    d = c.step(140.05, telemetry(140.05, mode='GUIDED', mission_seq=3), (), 2, 140.05, plan)
    assert d.state == 'RESUME_SELECT'
    link._perform(100, d.actions)
    conn.mav.mission_set_current_send.assert_called_once_with(1, 1, o.search_start_seq)


def test_time_land_actually_sends_the_land_waypoint(cfg, options, plan, tmp_path):
    from test_competition import link_ready
    o = looping(options, deadline=510.)
    link, conn, _ = link_ready(cfg, o, plan, tmp_path)
    link.owned, link.claim_slot = True, 6
    link.store.value = telemetry(100, mode='GUIDED')
    c = flying(cfg, o, plan)
    start = 100+510
    c.step(start, telemetry(start), (), 1, start, plan)
    d = c.step(start+.01, telemetry(start+.01, mode='GUIDED'), (), 2, start+.01, plan)
    assert d.state == 'SELECT_LAND'
    link._perform(100, d.actions)
    conn.mav.mission_set_current_send.assert_called_once_with(1, 1, plan.land_seq)
