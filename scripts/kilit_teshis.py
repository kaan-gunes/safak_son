"""Neden kilitlenmedi: kilit kapilarini kayittan yeniden kurar.

Esikler profilden okunur, betige elle yazilmaz.
    python kilit_teshis.py [kayit.jsonl]
"""
import json, math, sys
from pathlib import Path
from safak_gorev2.competition.config import Options

PROFIL = 'config/ana-imx708.json'
cfg, opt = Options.load(PROFIL)
MIN_FILL = opt.color_search.min_fill
MIN_ALT = cfg.control.minimum_intercept_relative_alt_m
print(f'esikler ({PROFIL}): min_fill={MIN_FILL}  quick_frames={opt.quick_frames}  '
      f'quick_hold_s={opt.quick_hold_s}  quick_iou={opt.quick_iou}  min_irtifa={MIN_ALT} m')

if len(sys.argv) > 1:
    path = Path(sys.argv[1])
else:
    files = sorted(Path('runtime').glob('competition/*/competition-*.jsonl'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit('kayit bulunamadi; dosyayi arguman olarak ver')
    path = files[0]

rows = []
for line in path.read_text(errors='replace').splitlines():
    line = line.strip()
    if line:
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
if not rows:
    raise SystemExit(f'kayit bos: {path}')
print(f'dosya: {path}\nsatir: {len(rows)}  sortie: {rows[0].get("sortie_id")}  '
      f'son durum: {rows[-1].get("decision",{}).get("state")}')

print('\n=== SEBEPLER (en cok gorulen = asil engel) ===')
cnt = {}
for r in rows:
    k = r.get('decision',{}).get('reason','')
    cnt[k] = cnt.get(k,0)+1
for k,v in sorted(cnt.items(), key=lambda kv:-kv[1])[:8]:
    print(f'  x{v:<5} {k[:95]}')

def bad(c):
    """fresh_candidates()'in hangi kosulunu gecemedi (controller.py:421)."""
    if c.get('source') != 'opencv':          return f"source={c.get('source')} (kopruleme/AI, kilit sayilmaz)"
    if c.get('confidence') is not None:      return 'confidence dolu (AI kutusu)'
    if c.get('color_verified') is not True:  return f"color_verified={c.get('color_verified')} (renk dogrulamasi gecmedi)"
    f = c.get('color_fill')
    if not isinstance(f,(int,float)) or not math.isfinite(f): return f'color_fill={f}'
    if not (MIN_FILL <= f <= 1):             return f'color_fill {f:.3f} < min_fill {MIN_FILL}'
    b = c.get('bbox')
    if not b or len(b)!=4:                   return 'bbox yok'
    if not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in b): return 'bbox aralik disi'
    if not (b[0]<b[2] and b[1]<b[3]):        return 'bbox ters'
    return None

print('\n=== ADAY KAPI HUNISI ===')
for color in ('mavi','kirmizi'):
    toplam = gecen = 0; sebepler = {}; fills = []
    for r in rows:
        for c in (r.get('candidates') or []):
            if c.get('color') != color: continue
            toplam += 1
            why = bad(c)
            if why is None:
                gecen += 1
                if isinstance(c.get('color_fill'),(int,float)): fills.append(c['color_fill'])
            else: sebepler[why] = sebepler.get(why,0)+1
    print(f'\n  {color}: {toplam} aday ornegi, kilit kapisindan GECEN {gecen}')
    if toplam and not gecen:
        print('    >>> HIC GECMEDI — kilit fiziksel olarak imkansizdi.')
    for k,v in sorted(sebepler.items(), key=lambda kv:-kv[1]):
        print(f'      x{v:<5} {k}')
    if fills:
        fills.sort()
        print(f'      gecen adaylarin color_fill: min={fills[0]:.3f} '
              f'orta={fills[len(fills)//2]:.3f} max={fills[-1]:.3f}')

print('\n=== GECEN ADAY VARKEN ARACIN DURUMU ===')
ok_rows = [r for r in rows if any(bad(c) is None for c in (r.get('candidates') or []))]
print(f'  gecen aday iceren kayit satiri: {len(ok_rows)} / {len(rows)}')
if ok_rows:
    st, mod, seq_set, alt_dusuk = {}, {}, set(), 0
    for r in ok_rows:
        d, t = r.get('decision',{}), r.get('telemetry',{})
        st[d.get('state')] = st.get(d.get('state'),0)+1
        mod[t.get('mode')] = mod.get(t.get('mode'),0)+1
        a = t.get('relative_alt_m')
        if isinstance(a,(int,float)) and a < MIN_ALT: alt_dusuk += 1
        seq_set.add(t.get('mission_seq'))
    print('  durumlar :', ', '.join(f'{k}={v}' for k,v in sorted(st.items(), key=lambda kv:-kv[1])))
    print('  modlar   :', ', '.join(f'{k}={v}' for k,v in sorted(mod.items(), key=lambda kv:-kv[1])))
    print(f'  seq      : {sorted(x for x in seq_set if x is not None)}  '
          f'(tarama izni {opt.search_start_seq}..{opt.search_end_seq})')
    print(f'  irtifa < {MIN_ALT} m olan satir: {alt_dusuk}')
    disari = sorted(x for x in seq_set if isinstance(x,int)
                    and not (opt.search_start_seq <= x <= opt.search_end_seq))
    if disari:
        print(f'  >>> TARAMA ARALIGI DISINDA gorulen seq: {disari}')
print('\nNOT: kayit 0,2 s araliklidir (50 FPS\'in 1/10\'u). Kare-kare sureklilik')
print('bu dosyadan olculemez; bu teshis kapilarin gecilip gecilmedigini gosterir.')
