"""Pixhawk'taki rotayı salt okunur okur; irtifaları ve mission_digest'i yazar.

`--write <profil>` verilirse yalnız `mission_fingerprint` alanını günceller.
FC'ye hiçbir komut gönderilmez; ARM/mod/rota yazımı yoktur.
"""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from pymavlink import mavutil

from safak_gorev2.competition.route import mission_digest
from safak_gorev2.mavlink_io import validate_mission
from safak_gorev2.types import MissionItem

DEVICE = '/dev/serial/by-id/usb-Hex_ProfiCNC_CubeOrange_220047001251313132383631-if00'


def read_plan(device, target=1):
    c = mavutil.mavlink_connection(device, baud=115200, source_system=245, source_component=191)
    try:
        h = c.wait_heartbeat(timeout=8)
        if h is None:
            raise SystemExit('Pixhawk heartbeat yok')
        if h.base_mode & 128:
            raise SystemExit('Araç ARM durumda; rota okunmadı')
        c.mav.mission_request_list_send(target, 1)
        count = c.recv_match(type='MISSION_COUNT', blocking=True, timeout=6)
        if count is None:
            raise SystemExit('MISSION_COUNT alınamadı')
        items = []
        for seq in range(count.count):
            c.mav.mission_request_int_send(target, 1, seq)
            m = c.recv_match(type='MISSION_ITEM_INT', blocking=True, timeout=4)
            if m is None or m.seq != seq:
                raise SystemExit(f'{seq} numaralı görev satırı alınamadı')
            items.append(MissionItem(m.seq, m.command, m.frame, m.x, m.y, m.z))
        return validate_mission(items)
    finally:
        c.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device', default=DEVICE)
    p.add_argument('--write', help='mission_fingerprint alanı güncellenecek görev profili')
    p.add_argument('--profile', help='yalnız karşılaştır: bu profilin parmak izi rotayla eşleşiyor mu')
    args = p.parse_args()
    plan = read_plan(args.device)
    digest = mission_digest(plan)
    print(json.dumps({'mission_digest': digest, 'takeoff_seq': plan.takeoff_seq,
                      'land_seq': plan.land_seq,
                      'items': [asdict(x) for x in plan.items]}, ensure_ascii=False, indent=2))
    print('\nİrtifalar (m):', ', '.join(f'{x.seq}:{x.z:g}' for x in plan.items))
    compare = args.profile or args.write
    if compare:
        stored = json.loads(Path(compare).read_text()).get('mission_fingerprint')
        print(('EŞLEŞİYOR: profil rotayla aynı' if stored == digest else
               f'EŞLEŞMİYOR: profil {stored} != rota {digest}')+f'  ({compare})')
    if args.write:
        path = Path(args.write)
        profile = json.loads(path.read_text())
        previous = profile.get('mission_fingerprint')
        profile['mission_fingerprint'] = digest
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2)+'\n')
        print(f'\n{path}: mission_fingerprint {previous} -> {digest}')
        print('Rota içeriğini gözle doğrulamadan uçma; bu araç yalnız digest yazar.')


if __name__ == '__main__':
    main()
