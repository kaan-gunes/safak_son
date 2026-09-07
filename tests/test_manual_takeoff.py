from dataclasses import replace
import pytest
from safak_gorev2.controller import Controller
from safak_gorev2.mavlink_io import validate_mission
from safak_gorev2.types import MissionItem
from conftest import telemetry, target


def manual_plan():
    return [MissionItem(0,16,0,410000000,290000000,0),
            MissionItem(1,16,3,410000100,290000100,10),
            MissionItem(2,21,3,410000000,290000000,0)]


def test_manual_takeoff_requires_explicit_setting_and_keeps_land_checks():
    items=manual_plan()
    with pytest.raises(ValueError):validate_mission(items)
    plan=validate_mission(items,takeoff_mode='manual')
    assert plan.takeoff_seq is None and plan.land_seq==2
    for changes in ({'x':0,'y':0},{'command':16},{'frame':0}):
        with pytest.raises(ValueError):
            validate_mission(items[:-1]+[replace(items[-1],**changes)],takeoff_mode='manual')
    with pytest.raises(ValueError):
        validate_mission([items[0],replace(items[1],command=22),items[2]],takeoff_mode='manual')


@pytest.mark.parametrize('changes',[
    {'armed':False,'landed':1}, {'landed':1},
    {'mode':'LOITER','rc_selected_mode':'LOITER'},
    {'relative_alt_m':3.}, {'mission_seq':0},
])
def test_manual_takeoff_never_claims_on_ground_loiter_low_altitude_or_home(cfg,changes):
    cfg=replace(cfg,mission=replace(cfg.mission,takeoff_mode='manual'))
    plan=validate_mission(manual_plan(),takeoff_mode='manual')
    c=Controller(cfg)
    c.step(99.,telemetry(99.,armed=False,landed=1),(),None,0.,plan)
    for i in range(20):
        now=100+i*.1
        t=replace(telemetry(now,mission_seq=1),**changes)
        d=c.step(now,t,(target(i,now),),i,now,plan)
        assert not d.actions


def test_manual_takeoff_acquires_only_after_auto_and_pilot_override_stays_latched(cfg):
    cfg=replace(cfg,mission=replace(cfg.mission,takeoff_mode='manual'))
    plan=validate_mission(manual_plan(),takeoff_mode='manual')
    c=Controller(cfg)
    # Havada yeni uygulama başlatılması manuel seçenekte de devralmaz.
    for i in range(20):
        now=90+i*.1
        assert not c.step(now,telemetry(now,mission_seq=1),(target(i,now),),i,now,plan).actions
    c.step(99.,telemetry(99.,armed=False,landed=1),(),None,0.,plan)
    for i in range(20):
        now=100+i*.1
        d=c.step(now,telemetry(now,mission_seq=1),(target(i+20,now),),i+20,now,plan)
        if d.state=='REQUEST_GUIDED':break
    assert d.state=='REQUEST_GUIDED'
    assert [a.kind for a in d.actions]==['claim','mode']
    d=c.step(now+.1,telemetry(now+.1,mode='LOITER',rc_selected_mode='LOITER',rc_slot=1),(),None,0.,plan)
    assert d.state=='PILOT_CONTROL' and [a.kind for a in d.actions]==['revoke']
    assert not c.step(now+.2,telemetry(now+.2,mission_seq=1),(target(99,now+.2),),99,now+.2,plan).actions


def test_auto_search_loiter_override_latches_before_guided(cfg):
    cfg=replace(cfg,mission=replace(cfg.mission,takeoff_mode='manual'))
    plan=validate_mission(manual_plan(),takeoff_mode='manual')
    c=Controller(cfg)
    c.step(99.,telemetry(99.,armed=False,landed=1),(),None,0.,plan)
    d=c.step(100.,telemetry(100.,mission_seq=1),(),1,100.,plan)
    assert d.state=='SEARCHING' and not d.actions
    d=c.step(100.1,telemetry(100.1,mode='LOITER',rc_selected_mode='LOITER',rc_slot=1),(),2,100.1,plan)
    assert d.state=='PILOT_CONTROL'
    for i in range(20):
        now=101+i*.1
        assert not c.step(now,telemetry(now,mission_seq=1),(target(i+3,now),),i+3,now,plan).actions
