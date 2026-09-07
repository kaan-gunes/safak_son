from dataclasses import replace

import pytest

from safak_gorev2.config import Config
from safak_gorev2.mavlink_io import validate_mission
from safak_gorev2.types import MissionItem, Target, Telemetry


@pytest.fixture
def cfg():
    c = Config()
    return replace(c, camera=replace(c.camera, offset_body_m=(-.03, 0., .05)),
                   mission=replace(c.mission, direct_land_corridor_checked=True))


@pytest.fixture
def mission():
    return validate_mission([MissionItem(0, 16, 0, 410000000, 290000000, 0),
        MissionItem(1, 22, 3, 0, 0, 6), MissionItem(2, 16, 3, 410000100, 290000100, 6),
        MissionItem(3, 21, 3, 410000000, 290000000, 0)])


def telemetry(now, **changes):
    t = Telemetry(**{f"{name}_at": now for name in (
        "heartbeat", "attitude", "position", "global", "gps", "ekf", "rc", "status",
        "battery", "landed", "mission", "timesync")},
        mode="AUTO", armed=True, landed=2, system_status=4, down=-6., lat=41., lon=29.,
        relative_alt_m=6., gps_fix=3, hdop=.8, satellites=16, ekf_flags=831,
        rc_slot=6, rc_selected_mode="AUTO", rc_healthy=True, mission_seq=2, firmware="4.6.3")
    return replace(t, **changes)


def target(frame_id, now, **changes):
    value = Target(frame_id, now, .95, 0., 0., 0., 5.95, .2,
        ((400., 180.), (800., 180.), (800., 580.), (400., 580.)), (.3, .2, .7, .8), .56)
    return replace(value, **changes)
