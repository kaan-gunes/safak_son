"""11 Eylül 12:47/12:53: alan dışındaki AUTO kalkış taramayı kilitlememeli."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from conftest import telemetry
from test_competition import candidate, options, plan, ready
from safak_gorev2.competition.config import Options
from safak_gorev2.competition.controller import DualController
from safak_gorev2.competition.route import inside
from safak_gorev2.competition.vision import Candidate
from safak_gorev2.mavlink_io import validate_mission
from safak_gorev2.types import MissionItem, Target, Telemetry


@pytest.mark.parametrize('flight_index', [0, 1])
@pytest.mark.parametrize('color', ['mavi', 'kirmizi'])
def test_recorded_outside_takeoff_reaches_stop_for_each_color(flight_index, color):
    fixture = json.loads(Path('tests/fixtures/entry-polygon-20260911.json').read_text())
    cfg, opts = Options.load('config/ana-imx708.json')
    profile = fixture['profile']
    opts = replace(opts, search_scope='field', center_search_speed_mps=None,
                   mission_fingerprint=profile['mission_fingerprint'],
                   search_start_seq=profile['search_start_seq'], search_end_seq=profile['search_end_seq'],
                   entry_gates=profile['entry_gates'], flight_polygon=profile['flight_polygon'])
    mission = validate_mission([MissionItem(**x) for x in fixture['mission']['items']])
    c = DualController(cfg, opts)
    waited_outside = False
    for row in fixture['flights'][flight_index]['rows']:
        t = Telemetry(**row['telemetry'])
        xs = tuple(Candidate(**dict(x, confidence=None, source='opencv',
                     color_verified=True, color_fill=x.get('color_fill') or .95,
                     metric=Target(**x['metric']) if x['metric'] else None))
                   for x in row['candidates'] if x['color'] == color)
        d = c.step(row['monotonic'], t, xs, row['frame_id'], row['frame_at'], mission)
        if c.started and not inside(opts.flight_polygon, (t.lat, t.lon)):
            waited_outside = True
            assert not d.actions
            assert c.state == 'WAIT_AUTO'
        assert d.state not in ('ABORTED', 'PILOT_CONTROL')
        if d.state == 'REQUEST_STOP':
            assert waited_outside and c.route.entered and c.selected == color
            assert inside(opts.flight_polygon, (t.lat, t.lon))
            assert [a.kind for a in d.actions] == ['claim', 'mode']
            assert d.actions[1].values == ('GUIDED', 'AUTO')
            break  # Kayıt AUTO'da devam eder; karşıolgusal GUIDED telemetrisi uydurulmaz.
    else:
        pytest.fail('Kayıtlı hedefte duruş isteği oluşmadı')


@pytest.mark.parametrize('strategy', ['center', 'quick'])
def test_no_command_outside_or_before_gate_then_stop(cfg, options, plan, strategy):
    c = DualController(cfg, replace(options, strategy=strategy))
    c.step(99, telemetry(99, armed=False, landed=1), (), None, 0, plan)
    # Giriş kapısının batısında, önce poligon dışında sonra içinde.
    for i in range(20):
        now = 100+i*.05
        t = telemetry(now, lon=28.98 if i < 10 else 28.9999)
        d = c.step(now, t, (candidate(i, now),), i, now, plan)
        assert not d.actions and not c.route.entered and c.state == 'WAIT_AUTO'
    for i in range(20, 24):
        now = 100+i*.05
        d = c.step(now, telemetry(now, lon=29.0001), (candidate(i, now),), i, now, plan)
        if c.state == 'REQUEST_STOP':
            break
    assert c.route.entered and c.state == 'REQUEST_STOP'


@pytest.mark.parametrize('phase', ['SEARCHING', 'STOPPING'])
def test_exit_after_entry_still_aborts_and_cannot_rearm_search(cfg, options, plan, phase):
    c = ready(cfg, replace(options, strategy='center'), plan)
    c.step(100, telemetry(100), (), 0, 100, plan)
    if phase == 'STOPPING':
        for i in range(1, 4):
            now = 100+i*.05
            c.step(now, telemetry(now), (candidate(i, now),), i, now, plan)
        c.step(100.2, telemetry(100.2, mode='GUIDED'), (), 4, 100.2, plan)
        assert c.state == 'STOPPING'
    d = c.step(100.25, telemetry(100.25, lat=42., mode='GUIDED' if c.child else 'AUTO'),
               (), 5, 100.25, plan)
    assert d.state == 'ABORTED' and any(a.kind == 'revoke' for a in d.actions)
    d = c.step(100.3, telemetry(100.3), (candidate(6, 100.3),), 6, 100.3, plan)
    assert d.state == 'ABORTED' and not d.actions


def test_pilot_change_while_waiting_outside_is_permanent(cfg, options, plan):
    c = DualController(cfg, options)
    c.step(99, telemetry(99, armed=False, landed=1), (), None, 0, plan)
    c.step(100, telemetry(100, lat=42.), (), 0, 100, plan)
    d = c.step(100.05, telemetry(100.05, lat=42., mode='LOITER'), (), 1, 100.05, plan)
    assert d.state == 'PILOT_CONTROL'
    d = c.step(100.1, telemetry(100.1), (candidate(2, 100.1),), 2, 100.1, plan)
    assert d.state == 'PILOT_CONTROL' and not d.actions
