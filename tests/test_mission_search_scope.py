from dataclasses import replace

import pytest

from conftest import telemetry
from test_competition import options, plan, candidate, link_ready
from safak_gorev2.competition.controller import DualController
from safak_gorev2.competition.config import Options
from safak_gorev2.competition.route import RouteProgress
from scripts.route_digest import update_profile_route


def full_route(options, plan):
    return replace(options, search_scope='mission', entry_gates=(), finish_gate=(),
                   flight_polygon=(), search_start_seq=plan.takeoff_seq+1,
                   search_end_seq=plan.land_seq-1)


@pytest.mark.parametrize('strategy', ['center', 'quick'])
@pytest.mark.parametrize('color', ['mavi', 'kirmizi'])
@pytest.mark.parametrize('seq', [2, 3])
def test_every_waypoint_can_stop_without_old_field(cfg, options, plan, strategy, color, seq):
    opts = replace(full_route(options, plan), strategy=strategy)
    c = DualController(cfg, opts)
    c.step(99, telemetry(99, armed=False, landed=1), (), None, 0, plan)
    for i in range(4):
        now = 100+i*.05
        d = c.step(now, telemetry(now, lat=38.3527, lon=38.341, mission_seq=seq),
                   (candidate(i, now, color),), i, now, plan)
        if d.state == 'REQUEST_STOP': break
    assert d.state == 'REQUEST_STOP' and c.selected == color
    assert [a.kind for a in d.actions] == ['claim', 'mode']


@pytest.mark.parametrize('case', ['takeoff', 'land', 'low', 'wrong_digest', 'partial_route', 'midair'])
def test_full_route_still_rejects_invalid_acquisition(cfg, options, plan, case):
    opts = full_route(options, plan)
    if case == 'wrong_digest': opts = replace(opts, mission_fingerprint='wrong')
    if case == 'partial_route': opts = replace(opts, search_end_seq=2)
    c = DualController(cfg, opts)
    if case != 'midair': c.step(99, telemetry(99, armed=False, landed=1), (), None, 0, plan)
    for i in range(10):
        now = 100+i*.05
        t = telemetry(now, mission_seq=1 if case=='takeoff' else 4 if case=='land' else 2,
                      relative_alt_m=1 if case=='low' else 6)
        d = c.step(now, t, (candidate(i, now),), i, now, plan)
        assert not d.actions and c.child is None


def test_full_route_link_accepts_new_location_but_keeps_pilot_and_digest_checks(cfg, options, plan, tmp_path):
    link, _, _ = link_ready(cfg, full_route(options, plan), plan, tmp_path)
    link.store.value = telemetry(100, lat=38.3527, lon=38.341, mode='GUIDED')
    assert link._safe(100, 'GUIDED')
    link.store.value = replace(link.store.value, rc_selected_mode='LOITER')
    assert not link._safe(100, 'GUIDED')
    link.store.value = replace(link.store.value, rc_selected_mode='AUTO')
    link.options = replace(link.options, mission_fingerprint='wrong')
    assert not link._safe(100, 'GUIDED')


def test_field_remains_default_and_scope_is_explicit(options):
    assert Options().search_scope == 'field'
    assert not RouteProgress(replace(options, entry_gates=())).entered
    with pytest.raises(ValueError): replace(options, search_scope='typo').validate()


@pytest.mark.parametrize('path', ['config/ana-imx708.json', 'config/ana-gorev.json', 'config/hizli-gorev.json'])
def test_deployed_profiles_use_new_full_route(path):
    # Tarama sıraları ve parmak izi SAHA verisidir; rota her değiştiğinde
    # `scripts/route_digest.py --write` bunları yeniden türetir. Bu yüzden test
    # belirli sayıları değil, rotadan bağımsız değişmezi doğrular.
    cfg, opts = Options.load(path)
    assert opts.search_scope == 'mission'
    assert opts.search_start_seq >= 2  # TAKEOFF seq 1'den sonra başlar.
    assert opts.search_start_seq <= opts.search_end_seq
    assert opts.mission_fingerprint and len(opts.mission_fingerprint) == 64
    assert not opts.entry_gates and not opts.flight_polygon
    assert not any('poligon' in x for x in opts.missing(cfg))


def test_aux1_only_profile_matches_confirmed_fifteen_meter_route_contract():
    _, opts = Options.load('config/ana-aux1-only.json')
    assert (opts.search_start_seq, opts.search_end_seq) == (2, 6)
    assert opts.mission_fingerprint == '084b315891c3cee52707fd65beb970bd58f77b5505370365e6a8cb3c4dbbc47e'
    assert opts.payloads == ('mavi',)


@pytest.mark.parametrize('strategy', ['center', 'quick'])
def test_selected_start_waits_until_waypoint_two_is_passed(cfg, options, plan, strategy):
    opts = replace(full_route(options, plan), strategy=strategy, search_start_seq=3)
    c = DualController(cfg, opts)
    c.step(99, telemetry(99, armed=False, landed=1), (), None, 0, plan)
    for i in range(10):
        now = 100+i*.05
        d = c.step(now, telemetry(now, mission_seq=2), (candidate(i, now),), i, now, plan)
        assert not d.actions and c.child is None
    for i in range(10, 20):
        now = 100+i*.05
        d = c.step(now, telemetry(now, mission_seq=3), (candidate(i, now),), i, now, plan)
        if d.state == 'REQUEST_STOP': break
    assert d.state == 'REQUEST_STOP'


def test_route_write_preserves_selected_start_and_updates_end(plan):
    profile = {'search_scope': 'mission', 'mission_fingerprint': 'old',
               'search_start_seq': 3, 'search_end_seq': 2}
    changes = update_profile_route(profile, plan, 'new')
    assert profile == {'search_scope': 'mission', 'mission_fingerprint': 'new',
                       'search_start_seq': 3, 'search_end_seq': plan.land_seq-1}
    assert not any(x.startswith('search_start_seq') for x in changes)


def test_route_write_repairs_start_outside_new_route(plan):
    profile = {'search_scope': 'mission', 'mission_fingerprint': 'old',
               'search_start_seq': 99, 'search_end_seq': 99}
    update_profile_route(profile, plan, 'new')
    assert profile['search_start_seq'] == plan.takeoff_seq+1
    assert profile['search_end_seq'] == plan.land_seq-1
