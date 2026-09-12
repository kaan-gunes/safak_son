"""telemetry_problem()'un GPS kapisindaki dort alt kosuldan hangisi tetikledi.

Kapi (controller.py:66) tek mesaj dondurur:
    now-gps_at > 2  |  gps_fix < 3  |  hdop is None  |  hdop > 1.5
Bu betik kayittan hangisinin gerceklestigini ve HDOP dagilimini cikarir.
"""
import json, sys
from pathlib import Path

LIMIT = 1.5
if len(sys.argv) > 1:
    path = Path(sys.argv[1])
else:
    files = sorted(Path('runtime').glob('competition/*/competition-*.jsonl'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit('kayit bulunamadi')
    path = files[0]

rows = []
for line in path.read_text(errors='replace').splitlines():
    line = line.strip()
    if line:
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
start = rows[0].get('monotonic') or 0
print(f'dosya: {path}\nsatir: {len(rows)}')

# --- iptal anini bul
abort_at = None
prev = None
for r in rows:
    st = r.get('decision', {}).get('state')
    if st == 'ABORTED' and prev != 'ABORTED':
        abort_at = r
        break
    prev = st

def gps(r):
    t = r.get('telemetry', {})
    now = r.get('monotonic')
    yas = None
    if isinstance(now,(int,float)) and isinstance(t.get('gps_at'),(int,float)):
        yas = now - t['gps_at']
    return t.get('gps_fix'), t.get('hdop'), t.get('satellites'), yas, t.get('ekf_flags')

print('\n=== IPTAL ANI ===')
if abort_at is None:
    print('  kayitta ABORTED gecisi yok')
else:
    fix, hdop, sat, yas, ekf = gps(abort_at)
    t = abort_at.get('telemetry', {})
    print(f'  zaman   : {(abort_at.get("monotonic") or 0)-start:.1f}s')
    print(f'  sebep   : {abort_at.get("decision",{}).get("reason")}')
    print(f'  gps_fix={fix}  hdop={hdop}  uydu={sat}  gps yasi={yas if yas is None else round(yas,3)} s')
    print(f'  ekf_flags={ekf} (gereken 23 biti: {"TAMAM" if isinstance(ekf,int) and (ekf & 23)==23 else "EKSIK"})')
    print(f'  irtifa={t.get("relative_alt_m")}  mod={t.get("mode")}  seq={t.get("mission_seq")}')
    print('  --- dort alt kosul ---')
    print(f'    gps yasi > 2 s        : {"TETIKLEDI" if (yas is not None and yas > 2) else "hayir"}')
    print(f'    gps_fix < 3           : {"TETIKLEDI" if (fix or 0) < 3 else "hayir"}')
    print(f'    hdop is None          : {"TETIKLEDI" if hdop is None else "hayir"}')
    print(f'    hdop > {LIMIT}          : {"TETIKLEDI" if (isinstance(hdop,(int,float)) and hdop > LIMIT) else "hayir"}')

print('\n=== TUM UCUS BOYUNCA HDOP ===')
vals = [(r.get('monotonic',0)-start, r['telemetry']['hdop']) for r in rows
        if isinstance(r.get('telemetry',{}).get('hdop'),(int,float))]
if not vals:
    print('  hic hdop ornegi yok (gps mesaji hic gelmedi)')
else:
    h = sorted(v for _, v in vals)
    n = len(h)
    print(f'  ornek={n}  min={h[0]:.2f}  p10={h[n//10]:.2f}  orta={h[n//2]:.2f}  '
          f'p90={h[min(n-1,9*n//10)]:.2f}  max={h[-1]:.2f}')
    ustu = [(ts, v) for ts, v in vals if v > LIMIT]
    print(f'  {LIMIT} ustunde olan ornek: {len(ustu)} / {n}  (%{100*len(ustu)/n:.1f})')
    for ts, v in ustu[:12]:
        print(f'    {ts:7.1f}s  hdop={v:.2f}')
    if len(ustu) > 12:
        print(f'    ... {len(ustu)-12} tane daha')

print('\n=== UYDU SAYISI ve FIX ===')
fixes, sats = {}, []
for r in rows:
    t = r.get('telemetry', {})
    fixes[t.get('gps_fix')] = fixes.get(t.get('gps_fix'), 0)+1
    if isinstance(t.get('satellites'), int): sats.append(t['satellites'])
print('  gps_fix dagilimi:', ', '.join(f'{k}={v}' for k, v in sorted(fixes.items(), key=lambda kv: -kv[1])))
if sats:
    s = sorted(sats)
    print(f'  uydu: min={s[0]} orta={s[len(s)//2]} max={s[-1]}')
