"""Uçuş kaydından tek sayfalık rapor: durum akışı, hız/fren, bırakma anı ve takip kanıtı.

Yalnız `competition-*.jsonl` dosyasını okur. Kamera, MAVLink, Hailo veya servo
açmaz; hiçbir dosyayı değiştirmez. Uçuştan sonra çalıştırılır.

    python scripts/ucus_raporu.py                # en yeni kaydı bulur
    python scripts/ucus_raporu.py --dosya <yol>  # belirli kayıt
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TERMINAL = ('DONE', 'INCOMPLETE', 'ABORTED', 'PILOT_CONTROL')


def newest_record(root: Path):
    files = sorted(root.glob('competition/*/competition-*.jsonl'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load(path: Path):
    rows = []
    for line in path.read_text(errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # Güç kesilmesinde son satır yarım kalabilir.
    return rows


def speed(t):
    vn, ve = t.get('vn'), t.get('ve')
    return math.hypot(vn, ve) if isinstance(vn, (int, float)) and isinstance(ve, (int, float)) else None


def travelled(a, b):
    for key in ('north', 'east'):
        if not isinstance(a.get(key), (int, float)) or not isinstance(b.get(key), (int, float)):
            return None
    return math.hypot(b['north']-a['north'], b['east']-a['east'])


def number(value, digits=2, unit=''):
    return f'{value:.{digits}f}{unit}' if isinstance(value, (int, float)) and math.isfinite(value) else '?'


def centre_offset(candidate):
    """Hedef merkezinin kare ortasından uzaklığı (0 = tam altında, 0.5 = kenar)."""
    box = candidate.get('bbox')
    if not box or len(box) != 4:
        return None
    return math.hypot((box[0]+box[2])/2-.5, (box[1]+box[3])/2-.5)


def header(title):
    print('\n' + title)
    print('-'*len(title))


def report(path: Path):
    rows = load(path)
    if not rows:
        print(f'Kayıt boş veya okunamadı: {path}')
        return 1
    first, last = rows[0], rows[-1]
    start = first.get('monotonic') or 0

    header('KAYIT')
    print(f'dosya      : {path}')
    print(f'satır      : {len(rows)}')
    print(f'görev      : {first.get("strategy")} / aktüatör: {first.get("actuator")}')
    print(f'sortie     : {first.get("sortie_id")}')
    print(f'süre       : {number((last.get("monotonic") or 0)-start, 1, " s")}')
    print(f'son durum  : {last.get("decision", {}).get("state")}')
    print(f'yükler     : {last.get("payloads")}')

    tracking = first.get('tracking')
    header('TAKIP AYARI')
    if tracking is None:
        print('kayıtta yok — bu kayıt takip katmanından ESKİ bir sürümle alınmış.')
    else:
        print(f'enabled={tracking.get("enabled")} debug={tracking.get("debug")} '
              f'köprü<={tracking.get("max_tracking_frames")} kare  '
              f'kayıp>{tracking.get("max_missed_frames")} kare  '
              f'onay={tracking.get("confirmation_frames")} kare')

    # ---- Neden ilerlemedi: durum hiç değişmezse akış tek satır kalır ve
    # asıl engel görünmez. Bütün sebepler sayılarıyla listelenir.
    header('SEBEPLER (en çok görülen = asıl engel)')
    counts, first = {}, {}
    for row in rows:
        reason = row.get('decision', {}).get('reason', '')
        counts[reason] = counts.get(reason, 0)+1
        first.setdefault(reason, (row.get('monotonic') or 0)-start)
    for reason, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'{first[reason]:7.1f}s  x{n:<5} {reason}')
    print(f'\nSON SEBEP: {last.get("decision", {}).get("reason")}')
    t = last.get('telemetry', {})
    print(f'son telemetri : mod={t.get("mode")} armed={t.get("armed")} '
          f'landed={t.get("landed")} seq={t.get("mission_seq")} '
          f'rc={t.get("rc_selected_mode")} alt={number(t.get("relative_alt_m"), 1, " m")}')

    # ---- Durum akışı
    header('DURUM AKIŞI')
    timeline, previous = [], None
    for row in rows:
        state = row.get('decision', {}).get('state')
        if state == previous:
            continue
        previous = state
        t = row.get('telemetry', {})
        timeline.append(row)
        print(f'{(row.get("monotonic") or 0)-start:7.1f}s  {state:<15} '
              f'hız={number(speed(t), 2, " m/s"):>10}  '
              f'irtifa={number(t.get("relative_alt_m"), 1, " m"):>8}  '
              f'mod={t.get("mode")}  {row.get("decision", {}).get("reason", "")[:58]}')

    # ---- Fren mesafesi: hedefi görüp durma isteği ile duruşun arası
    header('FREN / GECIKME')
    # REQUEST_STOP çok kısa sürer ve 0,2 s'lik kayıt örneklemesi onu kaçırabilir;
    # taramadan duruş dizisine ilk geçiş esas alınır.
    stops, previous_state = [], None
    for row in timeline:
        state = row.get('decision', {}).get('state')
        if state in ('REQUEST_STOP', 'STOPPING') and previous_state not in ('REQUEST_STOP', 'STOPPING'):
            stops.append(row)
        previous_state = state
    if not stops:
        print('Araç hiçbir hedef için durmaya çalışmadı (duruş dizisine hiç girilmedi).')
    for request in stops:
        began = request.get('monotonic')
        t0 = request.get('telemetry', {})
        after = [r for r in rows if (r.get('monotonic') or 0) >= began]
        stopped = next((r for r in after
                        if (speed(r.get('telemetry', {})) or 9e9) <= .25), None)
        print(f'{began-start:7.1f}s  hedef görüldü, duruş başladı — o andaki hız '
              f'{number(speed(t0), 2, " m/s")}')
        if stopped is None:
            print('           araç bu istekten sonra hiç durmadı (kayıt bitti veya iptal)')
            continue
        distance = travelled(t0, stopped.get('telemetry', {}))
        print(f'{(stopped.get("monotonic") or 0)-start:7.1f}s  durdu — '
              f'aradan {number((stopped.get("monotonic") or 0)-began, 1, " s")} geçti, '
              f'ARAÇ {number(distance, 1, " m")} YOL ALDI')

    # ---- Bırakma anı
    header('BIRAKMA ANI')
    seen = set()
    released = False
    for row in rows:
        payloads = row.get('payloads') or {}
        fresh = set(payloads) - seen
        if not fresh:
            continue
        seen |= fresh
        released = True
        t = row.get('telemetry', {})
        print(f'{(row.get("monotonic") or 0)-start:7.1f}s  YÜK: {sorted(fresh)} durum={payloads}')
        print(f'           hız={number(speed(t), 2, " m/s")}  '
              f'irtifa={number(t.get("relative_alt_m"), 1, " m")}  '
              f'eğim/mod={t.get("mode")}')
        cands = row.get('candidates') or []
        if not cands:
            print('           >>> O KAREDE HİÇ ADAY YOK (hedef görünmüyordu)')
        for c in cands:
            offset = centre_offset(c)
            flag = ''
            if offset is not None:
                flag = ('  <<< KARE ORTASINDAN UZAK, yük hedefin yanına düşer'
                        if offset > .18 else '  (ortaya yakın)')
            print(f'           aday {c.get("color"):<8} kaynak={c.get("source"):<8} '
                  f'takip={c.get("track_state")} merkez_sapma={number(offset, 3)}{flag}')
    if not released:
        print('hiç yük komutu verilmedi.')

    # ---- Takip kanıtı
    header('TAKIP KANITI')
    states, bridged_rows, streak, best_streak = {}, 0, 0, 0
    tracked_seen = False
    ms = []
    for row in rows:
        if isinstance(row.get('tracking_ms'), (int, float)):
            ms.append(row['tracking_ms'])
        cands = row.get('candidates') or []
        has_bridge = False
        for c in cands:
            state = c.get('track_state')
            if state is not None:
                tracked_seen = True
                states[state] = states.get(state, 0)+1
            if c.get('source') == 'tracked':
                has_bridge = True
        if has_bridge:
            bridged_rows += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
    if not tracked_seen:
        print('Adaylarda track_state alanı YOK.')
        print('→ Ya takip kapalıydı (tracking.enabled=false) ya da bu kayıt eski sürümden.')
    else:
        print('aday durumları :', ', '.join(f'{k}={v}' for k, v in sorted(states.items())))
        print(f'köprülenen kayıt satırı : {bridged_rows} (en uzun ardışık: {best_streak})')
        if bridged_rows:
            print('→ TAKİP ÇALIŞTI: OpenCV kaçırdığı karelerde etiket köprülendi.')
        else:
            print('→ Takip açıktı ama hiç köprüleme gerekmedi (tespit hiç kesilmemiş).')
    if ms:
        ms.sort()
        print(f'takip maliyeti : ortanca {ms[len(ms)//2]:.3f} ms, '
              f'en yüksek {ms[-1]:.3f} ms')

    # ---- Hız özeti
    header('TARAMA HIZI (WPNAV_SPEED etkisi)')
    searching = [speed(r.get('telemetry', {})) for r in rows
                 if r.get('decision', {}).get('state') == 'SEARCHING']
    searching = sorted(v for v in searching if v is not None)
    if searching:
        print(f'SEARCHING sırasında ölçülen yatay hız: ortanca '
              f'{searching[len(searching)//2]:.2f} m/s, en yüksek {searching[-1]:.2f} m/s')
        if searching[-1] > 3:
            print('>>> Tarama hızı yüksek. Fren mesafesi büyür, araç hedefi geçer.')
    else:
        print('SEARCHING durumunda hız örneği yok.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dosya', type=Path, help='Belirli bir competition-*.jsonl')
    parser.add_argument('--runtime', type=Path, default=Path('runtime'),
                        help='Kayıt kökü (varsayılan: runtime)')
    args = parser.parse_args()
    path = args.dosya or newest_record(args.runtime)
    if path is None or not path.is_file():
        print(f'Kayıt bulunamadı. --dosya ile yol verin. (aranan kök: {args.runtime})')
        return 2
    return report(path)


if __name__ == '__main__':
    raise SystemExit(main())
