"""Alçalma sırasında metrik geometrinin (PnP) neden reddedildiğini sayar.

Yalnız uçuş kaydını okur; kamera, MAVLink veya araç açmaz.

    python3 scripts/pnp_teshis.py            # en yeni kayıt
    python3 scripts/pnp_teshis.py <dosya>
"""
import collections
import glob
import json
import os
import sys

PHASES = ('CENTERING', 'DESCENDING', 'VERIFYING', 'INTERCEPT')
ACIKLAMA = {
    'border': 'köşe kadraj kenarına çok yakın (min_border_px)',
    'occupancy': 'hedef kareyi fazla dolduruyor (max_frame_occupancy)',
    'no_corners': 'renk bölgesinde dört köşe bulunamadı',
    'nonfinite_corners': 'köşe koordinatı sayısal değil',
    'metric_geometry': 'PnP reddi: düzlem eğimi >15°, reprojeksiyon >2,5 px veya poz belirsizliği',
    'class': 'etiket eşleşmedi',
    'score': 'güven eşiğin altında',
}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else max(
        glob.glob('runtime/competition/*/competition-*.jsonl'), key=os.path.getmtime)
    rows = [json.loads(l) for l in open(path) if l.strip()]
    print('dosya:', path)

    reasons = collections.Counter()
    trials = collections.Counter()
    accepted = rejected = 0
    for r in rows:
        if r['decision']['state'] not in PHASES:
            continue
        for d in r.get('diagnostics') or []:
            if not isinstance(d, dict):
                continue
            if d.get('accepted'):
                accepted += 1
            else:
                rejected += 1
                for reason in d.get('reasons') or ['(sebep kaydedilmemiş)']:
                    reasons[reason] += 1
            for t in d.get('corner_trials') or []:
                trials[(t.get('method'), bool(t.get('accepted')))] += 1

    total = accepted+rejected
    print()
    print('=== merkezleme/alçalma boyunca metrik ölçüm ===')
    print('  kabul : %d' % accepted)
    print('  ret   : %d' % rejected)
    if total:
        print('  oran  : %.0f%% kabul' % (100.0*accepted/total))
    print()
    print('=== RET SEBEPLERİ ===')
    for reason, n in reasons.most_common():
        pay = (100.0*n/rejected) if rejected else 0
        print('  x%-5d %5.1f%%  %-20s %s' % (n, pay, reason, ACIKLAMA.get(reason, '')))
    if trials:
        print()
        print('=== köşe ölçüm yöntemi ===')
        for (method, ok), n in trials.most_common():
            print('  x%-5d %-9s kabul=%s' % (n, method, ok))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
