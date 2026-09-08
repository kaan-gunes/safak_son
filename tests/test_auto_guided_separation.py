"""Kullanıcının komut çakışması hipotezine yönelik davranış kontrolleri."""
import threading
from unittest.mock import Mock

from conftest import target, telemetry
from safak_gorev2.controller import Controller
from safak_gorev2.mavlink_io import MavlinkLink, TelemetryStore
from safak_gorev2.types import Action


def test_intermittent_targets_leave_auto_without_navigation_commands(cfg, mission):
    control = Controller(cfg)
    control.saw_disarmed = True
    for i in range(30):
        now = 100+i*.1
        targets = (target(i, now),) if i % 2 == 0 else ()
        decision = control.step(now, telemetry(now), targets, i, now, mission)
        assert decision.state == "SEARCHING"
        assert not decision.actions


def test_velocity_cannot_be_applied_while_auto_even_with_claim(cfg):
    store = TelemetryStore()
    store.value = telemetry(100.)
    connection = Mock()
    link = MavlinkLink(cfg, store, True, threading.Event(), connection)
    link._perform(100., (Action("claim", (6,)), Action("velocity", (.3,0.,0.)), Action("stop")))
    assert link.owned
    assert link.velocity is None
    connection.mav.set_position_target_local_ned_send.assert_not_called()
    store.value = telemetry(100.1, mode="GUIDED")
    link._perform(100.1, (Action("velocity", (.3,0.,0.)),))
    assert link.velocity == (.3,0.,0.)
