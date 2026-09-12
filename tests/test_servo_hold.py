"""Acilista yuk servolarini dogrulanmis tutma PWM'inde kilitle.

12 Eylul saha olcumu (verici acik, DISARM, yerde):
    SERVO9  cikis 1100 us  <-  RC girisi 982 us    (ayrismis: override calisti)
    SERVO11 cikis 1495 us  ==  RC girisi 1495 us   (passthrough)
DO_SET_SERVO yerde/DISARM'da passthrough'u eziyor ve kalici. 1100 us'te
mandal kapali kaldi, yani mavi icin dogrulanmis tutma degeri 1100.

Sorun: her iki kanal da RC passthrough. Kumandadaki kol birakma ucundayken
verici acilirsa servo oraya gider ve yuk duser (11 Eylul: SERVO9 = 2006 us,
birakma 1800).
"""
from dataclasses import replace

import pytest
from pymavlink.dialects.v20 import ardupilotmega as mav

from test_competition import link_ready, outputs, LIMITS_FIELD, plan, options  # noqa: F401
from safak_gorev2.competition.config import Servo


HOLD = {'mavi': Servo(9, 1800, True, function=58, hold_pwm=1100),
        'kirmizi': Servo(11, 800, True, .3, 1500, function=61, hold_pwm=1500)}


def hold_link(cfg, options, plan, tmp_path, acik=True):
    o = replace(options, actuator='servo', servos=HOLD, hold_servos_at_startup=acik)
    link, conn, _ = link_ready(cfg, o, plan, tmp_path)
    link.servo_params.update(LIMITS_FIELD)
    return link, conn


def servo_cmds(conn):
    return [c.args for c in conn.mav.command_long_send.call_args_list if c.args[2] == 183]


def test_hold_is_commanded_when_output_is_on_release_side(cfg, options, plan, tmp_path):
    """11 Eylul'de olculen 2006 us: kol birakma ucunda. Tutmaya cekilmeli."""
    link, conn = hold_link(cfg, options, plan, tmp_path)
    link.ingest(outputs(2006, 1495), 100)
    link._tick(100)
    cmds = servo_cmds(conn)
    assert (1, 1, 183, 0, 9, 1100, 0, 0, 0, 0, 0) in cmds, cmds
    # kirmizi zaten 1495, tutma 1500'e 25 us'ten yakin: komut gerekmez
    assert not [c for c in cmds if c[4] == 11]


def test_hold_not_resent_while_output_already_correct(cfg, options, plan, tmp_path):
    link, conn = hold_link(cfg, options, plan, tmp_path)
    link.ingest(outputs(1100, 1495), 100)
    link._tick(100)
    assert servo_cmds(conn) == []


def test_hold_is_reasserted_if_output_drifts_away(cfg, options, plan, tmp_path):
    """Kol birakma ucuna oynatilirsa tutma yenilenir."""
    link, conn = hold_link(cfg, options, plan, tmp_path)
    link.ingest(outputs(1100, 1495), 100)
    link._tick(100)
    assert servo_cmds(conn) == []
    link.ingest(outputs(2006, 1495), 101.5)      # biri kola dokundu
    link._tick(101.5)
    assert [c for c in servo_cmds(conn) if c[4] == 9 and c[5] == 1100]


def test_hold_is_rate_limited(cfg, options, plan, tmp_path):
    link, conn = hold_link(cfg, options, plan, tmp_path)
    link.ingest(outputs(2006, 1495), 100)
    link._tick(100)
    link._tick(100.2)
    link._tick(100.9)
    assert len([c for c in servo_cmds(conn) if c[4] == 9]) == 1


def test_hold_stops_after_payload_released(cfg, options, plan, tmp_path):
    """Birakilmis yuk tekrar tutmaya cekilmez; mandal geri kapanmaz."""
    link, conn = hold_link(cfg, options, plan, tmp_path)
    link.payload_status['mavi'] = 'ACK_ACCEPTED'
    link.ingest(outputs(1800, 1495), 100)
    link._tick(100)
    assert not [c for c in servo_cmds(conn) if c[4] == 9]


def test_hold_does_not_interrupt_a_release_in_progress(cfg, options, plan, tmp_path):
    link, conn = hold_link(cfg, options, plan, tmp_path)
    link.pending = {'color': 'mavi', 'at': 100., 'ack': False, 'output': False}
    link.ingest(outputs(1800, 1495), 100)
    link._tick(100)
    assert servo_cmds(conn) == []
    link.pending = None
    link.pulse = {'color': 'kirmizi', 'until': 200.}
    link._tick(100)
    assert servo_cmds(conn) == []


def test_disabled_by_default_sends_nothing(cfg, options, plan, tmp_path):
    """Varsayilan kapali: bugun dogrulanan davranis bit bit ayni kalir."""
    link, conn = hold_link(cfg, options, plan, tmp_path, acik=False)
    link.ingest(outputs(2006, 1495), 100)
    link._tick(100)
    assert servo_cmds(conn) == []


def test_hold_pwm_near_release_is_rejected(options):
    bad = replace(options, servos={'mavi': Servo(9, 1800, True, function=58, hold_pwm=1750),
                                   'kirmizi': Servo(11, 800, True, .3, 1500, function=61)})
    with pytest.raises(ValueError, match='hold_pwm bırakma değerine çok yakın'):
        bad.validate()


def test_enabling_without_hold_pwm_is_rejected(options):
    bad = replace(options, actuator='servo', hold_servos_at_startup=True,
                  servos={'mavi': Servo(9, 1800, True, function=58),
                          'kirmizi': Servo(11, 800, True, .3, 1500, function=61)})
    with pytest.raises(ValueError, match='hold_servos_at_startup için hold_pwm gerekli'):
        bad.validate()
