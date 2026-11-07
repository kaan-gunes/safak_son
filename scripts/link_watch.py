#!/usr/bin/env python3
"""Yer istasyonu linkini ölç: sinyal, arayüz yükü, paneli paylaşan akışlar.

  python scripts/link_watch.py            uçuş öncesi tek seferlik kontrol
  python scripts/link_watch.py --watch    1 Hz JSONL kaydı (uçuş boyunca)

Salt okunurdur: hiçbir süreci kapatmaz, ağ ayarı değiştirmez, uçuş komutu
üretmez. Ölçüm menzil garantisi değildir; RF/anten/görüş hattı belirleyicidir.
"""
from __future__ import annotations

import argparse
import json
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from safak_gorev2.link_health import (heavy_stream_processes, interface_bytes,  # noqa: E402
                                      wireless_signal)

# Panel 640x360/4 FPS/Q35'te yaklaşık bu kadar üretir; üstü başka akış demektir.
PANEL_BUDGET_BPS = 600_000


def default_gateway(root: Path = Path('/')) -> str | None:
    try:
        lines = (root/'proc/net/route').read_text().splitlines()[1:]
    except OSError:
        return None
    for line in lines:
        fields = line.split()
        if len(fields) > 2 and fields[1] == '00000000':
            try:
                return socket.inet_ntoa(struct.pack('<L', int(fields[2], 16)))
            except (ValueError, OSError):
                return None
    return None


def ping_rtt_ms(host: str, count: int = 3) -> dict:
    try:
        done = subprocess.run(['ping', '-c', str(count), '-w', '5', host],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'host': host, 'error': str(error)}
    loss = None
    for line in done.stdout.splitlines():
        if 'packet loss' in line:
            for token in line.split(','):
                if 'packet loss' in token:
                    loss = token.strip().split('%')[0]
        if line.startswith(('rtt', 'round-trip')):
            numbers = line.split('=')[-1].strip().split()[0].split('/')
            if len(numbers) >= 3:
                return {'host': host, 'min_ms': float(numbers[0]), 'avg_ms': float(numbers[1]),
                        'max_ms': float(numbers[2]), 'loss_pct': loss}
    return {'host': host, 'loss_pct': loss, 'error': None if done.returncode == 0 else 'ping başarısız'}


def interface_load(interface: str, seconds: float, root: Path = Path('/')) -> dict | None:
    first = interface_bytes(interface, root)
    if first is None:
        return None
    began = time.monotonic()
    time.sleep(seconds)
    second = interface_bytes(interface, root)
    span = time.monotonic() - began
    if second is None or span <= 0:
        return None
    return {'rx_bps': (second[0]-first[0])*8/span, 'tx_bps': (second[1]-first[1])*8/span,
            'span_s': span}


def panel_cost(panel_url: str, samples: int = 8) -> dict:
    """Panelin bir saniyede ürettiği gerçek bayt: durum + değişen kare."""
    total, errors, etag, not_modified, began = 0, 0, None, 0, time.monotonic()
    for _ in range(samples):
        for path, headers in (('/api/competition', {}), ('/frame.jpg', {'If-None-Match': etag} if etag else {})):
            request = urllib.request.Request(panel_url+path, headers={k: v for k, v in headers.items() if v})
            try:
                with urllib.request.urlopen(request, timeout=1.) as response:
                    body = response.read()
                    total += len(body)
                    if path == '/frame.jpg':
                        etag = response.headers.get('ETag') or etag
            except urllib.error.HTTPError as error:
                if error.code == 304:
                    not_modified += 1
                    continue
                errors += 1
            except (OSError, urllib.error.URLError):
                errors += 1
        time.sleep(.25)
    span = max(1e-6, time.monotonic()-began)
    return {'bytes': total, 'bps': total*8/span, 'span_s': span, 'errors': errors,
            'not_modified': not_modified}


def sample(panel_url: str, root: Path = Path('/')) -> dict:
    wifi = wireless_signal(root)
    counters = interface_bytes(wifi['interface'], root) if wifi else None
    link = None
    try:
        with urllib.request.urlopen(panel_url+'/api/link', timeout=1.) as response:
            link = json.loads(response.read())
    except (OSError, ValueError, urllib.error.URLError):
        link = None
    return {'at': time.time(), 'wifi': wifi,
            'rx_bytes': counters[0] if counters else None,
            'tx_bytes': counters[1] if counters else None,
            'panel': link}


def check(panel_url: str, root: Path = Path('/')) -> int:
    wifi = wireless_signal(root)
    print('--- WiFi ---')
    if wifi:
        print(f"  arayüz {wifi['interface']}  sinyal {wifi['signal_dbm']:.0f} dBm  "
              f"kalite {wifi['quality']:.0f}  retry {wifi['retry']}")
    else:
        print('  okunamadı (/proc/net/wireless yok; bu makine Pi değil mi?)')
    gateway = default_gateway(root)
    if gateway:
        print(f"  ağ geçidi {gateway}: {json.dumps(ping_rtt_ms(gateway), ensure_ascii=False)}")
    problems = []
    print('--- arayüz yükü (2 s) ---')
    load = interface_load(wifi['interface'], 2., root) if wifi else None
    if load:
        print(f"  gönderim {load['tx_bps']/1000:.0f} kbit/s  alım {load['rx_bps']/1000:.0f} kbit/s")
    else:
        print('  okunamadı')
    print('--- panel maliyeti ---')
    cost = panel_cost(panel_url)
    print(f"  {cost['bps']/1000:.0f} kbit/s  ({cost['bytes']} bayt / {cost['span_s']:.1f} s, "
          f"değişmeyen kare {cost['not_modified']}, hata {cost['errors']})")
    if cost['errors']:
        problems.append(f"panel {panel_url} yanıt vermiyor ({cost['errors']} hata); görev süreci açık mı?")
    if load and load['tx_bps'] - cost['bps'] > PANEL_BUDGET_BPS:
        problems.append(f"linki paylaşan başka akış: arayüz {load['tx_bps']/1000:.0f} kbit/s "
                        f"gönderirken panel yalnız {cost['bps']/1000:.0f} kbit/s")
    print('--- linki paylaşan ağır süreçler ---')
    heavy = heavy_stream_processes(root)
    if heavy:
        print('  ' + ', '.join(heavy))
        problems.append('uzak masaüstü/ekran paylaşımı açık: ' + ', '.join(heavy) +
                        ' — uçuşta kapatın, panel aynı WiFi\'yi bunlarla paylaşamaz')
    else:
        print('  yok')
    if wifi and wifi['signal_dbm'] <= -75:
        problems.append(f"WiFi sinyali zayıf: {wifi['signal_dbm']:.0f} dBm")
    print()
    if problems:
        print('LINK UYARISI:')
        for problem in problems:
            print('  - ' + problem)
        return 1
    print('Link ölçümü temiz. Bu menzil garantisi değildir; sahada anten/görüş hattı belirleyicidir.')
    return 0


def watch(panel_url: str, out: Path, seconds: float | None, root: Path = Path('/')) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    print(f'1 Hz link kaydı: {out} (Ctrl+C ile bitir)')
    written = 0
    try:
        with out.open('a', encoding='utf-8') as handle:
            while seconds is None or time.monotonic()-began < seconds:
                handle.write(json.dumps(sample(panel_url, root), ensure_ascii=False)+'\n')
                handle.flush()
                written += 1
                time.sleep(1.)
    except KeyboardInterrupt:
        pass
    print(f'{written} örnek yazıldı: {out}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--panel-url', default='http://127.0.0.1:8081')
    parser.add_argument('--watch', action='store_true', help='1 Hz JSONL kaydı')
    parser.add_argument('--seconds', type=float, default=None)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    if args.watch:
        out = Path(args.out or Path(__file__).resolve().parents[1] /
                   f"runtime/link/{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.jsonl")
        return watch(args.panel_url, out, args.seconds)
    return check(args.panel_url)


if __name__ == '__main__':
    raise SystemExit(main())
