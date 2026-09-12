"""Yük servolarini SALT OKUNUR incele: RC girisi mi servoyu suruyor?

Her iki yuk kanali da RC passthrough islevinde (SERVO9_FUNCTION=58 -> RCIN8,
SERVO11_FUNCTION=61 -> RCIN11). Bu islevde servo cikisi VERICININ o kanaldaki
konumunu izler; uygulama hic komut vermeden servo hareket eder. Bu betik
kanal degerini, servo cikisini ve sinirlari yan yana koyar.

FC'ye hicbir komut gonderilmez: ARM yok, mod yok, parametre yazimi yok,
servo komutu yok. Yalniz okuma.

    python scripts/servo_teshis.py
"""
import argparse
import json
import sys
from pathlib import Path

from pymavlink import mavutil

from safak_gorev2.competition.config import Options

DEVICE = '/dev/serial/by-id/usb-Hex_ProfiCNC_CubeOrange_220047001251313132383631-if00'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default=DEVICE)
    ap.add_argument('--profile', default='config/ana-imx708.json')
    ap.add_argument('--saniye', type=float, default=6.0, help='kac saniye izlensin')
    a = ap.parse_args()

    _, opt = Options.load(a.profile)
    kanallar = {}
    for color, s in opt.servos.items():
        if color in opt.payloads and s.channel is not None:
            kanallar[color] = s
    if not kanallar:
        raise SystemExit('profilde yük servosu yok')

    print('SALT OKUNUR. ARM/mod/parametre/servo komutu gönderilmez.\n')
    for color, s in kanallar.items():
        rcin = s.function-50 if 51 <= s.function <= 66 else None
        print(f'{color:8} kanal AUX/SERVO{s.channel}  FUNCTION={s.function}'
              + (f'  -> RCIN{rcin} passthrough (verici bu kanalı sürüyor)' if rcin
                 else '  -> passthrough değil')
              + f'\n{"":8} bırakma={s.release_pwm} us'
              + (f'  nötr={s.neutral_pwm} us' if s.neutral_pwm is not None else '  nötr tanımı YOK'))
    print()

    c = mavutil.mavlink_connection(a.device, baud=115200, source_system=245, source_component=191)
    try:
        h = c.wait_heartbeat(timeout=8)
        if h is None:
            raise SystemExit('Pixhawk heartbeat yok')
        if h.base_mode & 128:
            raise SystemExit('Araç ARM durumda; inceleme yapılmadı')
        for s in kanallar.values():
            for suffix in ('FUNCTION', 'MIN', 'MAX', 'TRIM'):
                c.mav.param_request_read_send(1, 1, f'SERVO{s.channel}_{suffix}'.encode(), -1)
        # SERVO_OUTPUT_RAW (36) ve RC_CHANNELS (65) akisi
        for stream, hz in ((36, 5), (65, 5)):
            c.mav.command_long_send(1, 1, 511, 0, stream, int(1e6/hz), 0, 0, 0, 0, 0)

        params, cikis, rc = {}, {}, {}
        import time
        son = time.monotonic()+a.saniye
        while time.monotonic() < son:
            m = c.recv_match(type=['PARAM_VALUE', 'SERVO_OUTPUT_RAW', 'RC_CHANNELS'],
                             blocking=True, timeout=1)
            if m is None:
                continue
            k = m.get_type()
            if k == 'PARAM_VALUE':
                params[m.param_id.strip('\x00') if isinstance(m.param_id, str) else
                       m.param_id.decode().strip('\x00')] = m.param_value
            elif k == 'SERVO_OUTPUT_RAW' and m.port == 0:
                for color, s in kanallar.items():
                    v = getattr(m, f'servo{s.channel}_raw', None)
                    if v is not None:
                        cikis.setdefault(color, []).append(v)
            elif k == 'RC_CHANNELS':
                for color, s in kanallar.items():
                    if 51 <= s.function <= 66:
                        v = getattr(m, f'chan{s.function-50}_raw', None)
                        if v is not None:
                            rc.setdefault(color, []).append(v)
    finally:
        c.close()

    print('='*70)
    sorun = []
    for color, s in kanallar.items():
        o = cikis.get(color, [])
        r = rc.get(color, [])
        lo = params.get(f'SERVO{s.channel}_MIN')
        hi = params.get(f'SERVO{s.channel}_MAX')
        trim = params.get(f'SERVO{s.channel}_TRIM')
        print(f'\n{color.upper()}  (SERVO{s.channel})')
        print(f'  MIN={lo} MAX={hi} TRIM={trim}')
        print(f'  servo çıkışı : {min(o) if o else "?"}..{max(o) if o else "?"} us  ({len(o)} örnek)')
        print(f'  RC girişi    : {min(r) if r else "?"}..{max(r) if r else "?"} us  ({len(r)} örnek)')
        if not o:
            print('  >>> SERVO ÇIKIŞI HİÇ OKUNAMADI'); sorun.append(color); continue
        son_o = o[-1]
        if lo is not None and hi is not None and not lo <= son_o <= hi:
            print(f'  >>> ÇIKIŞ SINIR DIŞI: {son_o} us  (RC kanalı servoyu doğrudan sürüyor)')
            sorun.append(color)
        if s.release_pwm is not None and abs(son_o-s.release_pwm) < opt.servo_release_margin_pwm:
            print(f'  >>> BIRAKMA KONUMUNDA: {son_o} us, bırakma {s.release_pwm} us')
            sorun.append(color)
        if o and r and max(abs(x-y) for x, y in zip(o[-len(r):], r[-len(o):])) < 30:
            print('  >>> Çıkış RC girişini birebir izliyor: passthrough doğrulandı.')
    print('\n'+'='*70)
    if sorun:
        print('YÜKÜ TAKMAYIN. Sorunlu: '+', '.join(sorted(set(sorun))))
        print('Servo bırakma konumundaysa önce RC kolunu/anahtarını tutma tarafına al,')
        print('çıkışın tutma değerine indiğini bu betikle tekrar gör, sonra yükü tak.')
        return 1
    print('Her iki servo da güvenli konumda görünüyor.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
