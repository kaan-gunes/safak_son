import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataclasses import replace  # noqa: E402

from safak_gorev2.competition.config import Options  # noqa: E402
from safak_gorev2.competition.main import build_app  # noqa: E402
from safak_gorev2.competition.runtime import CompetitionRuntime  # noqa: E402
from safak_gorev2.link_health import (LinkHealth, heavy_stream_processes,  # noqa: E402
                                      interface_bytes, wireless_signal)


@pytest.fixture
def competition_client(cfg, tmp_path):
    options = Options()
    runtime = CompetitionRuntime(replace(cfg, runtime_dir=str(tmp_path/'link')), 'observe', options)
    try:
        app, _ = build_app(replace(cfg, runtime_dir=str(tmp_path/'link')), runtime, options,
                           'observe', [])
        yield app.test_client(), runtime.state
    finally:
        runtime.close()

WIRELESS = """Inter-| sta-|   Quality        |   Discarded packets               | Missed | WE
 face | tus | link level noise |  nwid  crypt   frag  retry   misc | beacon | 22
 wlan0: 0000   63.  -47.  -256        0      0      0     91     14        0
"""


def fake_root(tmp_path, *, wireless=WIRELESS, rx=0, tx=0, processes=()):
    (tmp_path/'proc/net').mkdir(parents=True, exist_ok=True)
    if wireless is not None:
        (tmp_path/'proc/net/wireless').write_text(wireless)
    stats = tmp_path/'sys/class/net/wlan0/statistics'
    stats.mkdir(parents=True, exist_ok=True)
    (stats/'rx_bytes').write_text(str(rx))
    (stats/'tx_bytes').write_text(str(tx))
    for pid, name in enumerate(processes, start=100):
        entry = tmp_path/'proc'/str(pid)
        entry.mkdir(parents=True, exist_ok=True)
        (entry/'comm').write_text(name+'\n')
    return tmp_path


def test_wireless_and_interface_read_or_degrade(tmp_path):
    root = fake_root(tmp_path, rx=10, tx=20)
    assert wireless_signal(root) == {'interface': 'wlan0', 'quality': 63., 'signal_dbm': -47.,
                                     'retry': 91, 'misc': 14}
    assert interface_bytes('wlan0', root) == (10, 20)
    # Pi olmayan makinede ölçüm yoktur; çağıran çökmez.
    assert wireless_signal(tmp_path/'yok') is None
    assert interface_bytes('yok', root) is None


def test_heavy_stream_processes_names_remote_desktop(tmp_path):
    root = fake_root(tmp_path, processes=('python3', 'nxnode.bin', 'bash'))
    assert heavy_stream_processes(root) == ['nxnode']
    assert heavy_stream_processes(fake_root(tmp_path/'clean', processes=('python3',))) == []


def test_panel_share_separates_own_load_from_interface_total(tmp_path):
    times = [100.]
    health = LinkHealth(window_s=10., root=fake_root(tmp_path, tx=0), clock=lambda: times[-1])
    health.sample_interface()
    # 1 s sonra panel 10 kB gönderdi, arayüz 250 kB: fark başka bir akıştır.
    times.append(times[-1]+1.)
    (tmp_path/'sys/class/net/wlan0/statistics/tx_bytes').write_text(str(250_000))
    health.record('192.168.137.2', '/frame.jpg', 200, 10_000, .05)
    health.sample_interface()
    snapshot = health.snapshot()
    assert snapshot['wifi']['signal_dbm'] == -47.
    assert snapshot['interface']['tx_bps'] == pytest.approx(2_000_000)
    # Panel 1 s'de 10 kB = 80 kbit/s; arayüz 2 Mbit/s gönderiyor.
    assert snapshot['served_bps'] == pytest.approx(80_000)
    assert snapshot['panel_share_of_tx'] < .05
    assert snapshot['clients']['192.168.137.2']['requests'] == 1


def test_window_forgets_old_requests():
    now = [0.]
    health = LinkHealth(window_s=2., clock=lambda: now[0])
    health.record('a', '/api/competition', 200, 1000, .01)
    now[0] = 5.
    assert health.snapshot()['requests'] == 0


def test_frame_etag_saves_repeat_download_and_link_endpoint_serves(competition_client):
    client, state = competition_client
    state.jpeg_put(b'x'*900, time.monotonic(), 12)
    first = client.get('/frame.jpg')
    assert first.status_code == 200 and first.headers['ETag'] == '"12"'
    again = client.get('/frame.jpg', headers={'If-None-Match': '"12"'})
    assert again.status_code == 304 and not again.data
    state.jpeg_put(b'y'*900, time.monotonic(), 13)
    assert client.get('/frame.jpg', headers={'If-None-Match': '"12"'}).status_code == 200
    link = client.get('/api/link').json
    assert link['requests'] >= 3 and link['served_bps'] > 0
    assert client.post('/api/link').status_code == 405
