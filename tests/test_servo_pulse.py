from dataclasses import replace
import pytest
from pymavlink.dialects.v20 import ardupilotmega as mav
from conftest import telemetry
from test_competition import options, plan, link_ready, source
from safak_gorev2.competition.config import Servo
from safak_gorev2.types import Action


def setup(cfg, options, plan, tmp_path, monkeypatch):
    o=replace(options,actuator='servo',servos={'mavi':Servo(9,1800,True,function=58),
        'kirmizi':Servo(11,800,True,.3,1500,function=61)})
    link,conn,ledger=link_ready(cfg,o,plan,tmp_path)
    link.store.value=telemetry(100,mode='GUIDED');link.owned=True;link.claim_slot=6
    for ch,fn,lo in ((9,58,1100),(11,61,800)):
        link.servo_params.update({f'SERVO{ch}_FUNCTION':fn,f'SERVO{ch}_MIN':lo,f'SERVO{ch}_MAX':1900})
    monkeypatch.setattr('safak_gorev2.competition.link.time.monotonic',lambda:100.)
    link._perform(100,(Action('payload',('kirmizi','mavi',1,100,'GUIDED')),))
    return link,conn,ledger


def ack_output(link,at,pwm):
    link.ingest(source(mav.MAVLink_command_ack_message(183,0,0,0,245,191)),at)
    link.ingest(source(mav.MAVLink_servo_output_raw_message(0,0,*([1000]*8),servo11_raw=pwm)),at+.01)


def test_pulse_neutral_must_be_confirmed_before_success(cfg,options,plan,tmp_path,monkeypatch):
    link,conn,ledger=setup(cfg,options,plan,tmp_path,monkeypatch)
    ack_output(link,100.1,800)
    assert link.snapshot_status()['kirmizi']=='SENT'
    link._tick(100.29)
    assert conn.mav.command_long_send.call_count==1
    link._tick(100.31)
    assert conn.mav.command_long_send.call_args.args[2:6]==(183,0,11,1500)
    assert link.snapshot_status()['kirmizi']=='SENT'
    ack_output(link,100.4,1500)
    assert ledger.statuses()['kirmizi']=='ACK_ACCEPTED'
    link._perform(100.5,(Action('payload',('kirmizi','mavi',2,100.5,'GUIDED')),))
    assert conn.mav.command_long_send.call_count==2


@pytest.mark.parametrize('case',['pilot','shutdown','missing_ack'])
def test_neutral_even_when_release_cannot_complete(cfg,options,plan,tmp_path,monkeypatch,case):
    link,conn,ledger=setup(cfg,options,plan,tmp_path,monkeypatch)
    if case=='pilot':link.store.pilot_override=True;link.owned=False
    if case=='shutdown':link._shutdown_outputs()
    else:link._tick(100.31)
    assert conn.mav.command_long_send.call_args.args[2:6]==(183,0,11,1500)
    link._tick(103)
    assert ledger.statuses()['kirmizi']=='UNCERTAIN'
    assert link.pulse is None


def test_neutral_output_cannot_hide_missing_release_evidence(cfg,options,plan,tmp_path,monkeypatch):
    link,conn,ledger=setup(cfg,options,plan,tmp_path,monkeypatch)
    link._tick(100.31)
    ack_output(link,100.4,1500)
    assert ledger.statuses()['kirmizi']=='UNCERTAIN'


@pytest.mark.parametrize('changes',[{'pulse_s':.3},{'neutral_pwm':1500},{'pulse_s':float('nan'),'neutral_pwm':1500},{'function':33}])
def test_bad_pulse_configuration(options,changes):
    servos=dict(options.servos);servos['kirmizi']=Servo(11,800,True,**changes)
    with pytest.raises(ValueError):replace(options,servos=servos).validate()
