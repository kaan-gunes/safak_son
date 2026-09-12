"""Yerde tek AUX çıkışı denemesi; varsayılan salt okunur, ARM/mod/parametre yazmaz."""
import argparse
import json
import time

from pymavlink import mavutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True)
    parser.add_argument('--channel', type=int, choices=(9, 10, 11))
    parser.add_argument('--pwm', type=int)
    args = parser.parse_args()
    if (args.channel is None) != (args.pwm is None):
        parser.error('channel ve pwm birlikte verilmeli')
    if args.pwm is not None and not 1000 <= args.pwm <= 2000:
        parser.error('Deneme sınırı 1000–2000 us')
    mavutil.set_dialect('ardupilotmega')
    conn = mavutil.mavlink_connection(args.device, baud=115200, source_system=245,
                                     source_component=191, autoreconnect=False)
    params, latest, timestamps = {}, {}, {}
    def command(cmd, *values):
        conn.mav.command_long_send(1, 1, cmd, 0, *(list(values) + [0]*(7-len(values))))
    def receive(duration):
        until = time.monotonic()+duration
        messages = []
        while time.monotonic() < until:
            msg = conn.recv_match(blocking=True, timeout=.1)
            if msg is None or msg.get_srcSystem() != 1 or msg.get_srcComponent() != 1:
                continue
            kind = msg.get_type()
            latest[kind], timestamps[kind] = msg.to_dict(), time.monotonic()
            if kind == 'PARAM_VALUE':
                name = msg.param_id
                if isinstance(name, bytes):
                    name = name.decode()
                params[name.rstrip('\0')] = msg.param_value
            messages.append(msg.to_dict())
        return messages
    def grounded():
        now = time.monotonic()
        hb, ext = latest.get('HEARTBEAT', {}), latest.get('EXTENDED_SYS_STATE', {})
        return (now-timestamps.get('HEARTBEAT', 0) < 2
                and now-timestamps.get('EXTENDED_SYS_STATE', 0) < 2
                and hb.get('autopilot') == 3 and hb.get('type') == 13
                and not hb.get('base_mode', 128) & 128 and ext.get('landed_state') == 1)
    try:
        receive(2)
        if 'HEARTBEAT' not in latest:
            raise RuntimeError('Cube heartbeat yok; komut gönderilmedi')
        names = [f'SERVO{ch}_{suffix}' for ch in (9, 10, 11)
                 for suffix in ('FUNCTION', 'MIN', 'MAX', 'TRIM', 'REVERSED')]
        names += ['BRD_SAFETY_DEFLT', 'BRD_SAFETY_MASK', 'SERVO_GPIO_MASK']
        names += [f'RC{ch}_{suffix}' for ch in (9, 10, 11, 12)
                  for suffix in ('OPTION', 'MIN', 'MAX', 'TRIM', 'DZ', 'REVERSED')]
        for name in names:
            conn.mav.param_request_read_send(1, 1, name.encode(), -1)
            receive(.1)
        # Tek seferlik mesaj istekleri; stream hızı/FC parametresi değiştirilmez.
        for mid in (245, 36, 65, 148):
            command(512, mid)
        receive(1)
        report = {'device': args.device, 'parameters': params,
                  'heartbeat': latest.get('HEARTBEAT'),
                  'extended_sys_state': latest.get('EXTENDED_SYS_STATE'),
                  'rc_channels': latest.get('RC_CHANNELS'),
                  'servo_output': latest.get('SERVO_OUTPUT_RAW'),
                  'autopilot_version': latest.get('AUTOPILOT_VERSION'),
                  'grounded': grounded()}
        print(json.dumps(report, ensure_ascii=False), flush=True)
        if args.channel is None:
            return
        prefix = f'SERVO{args.channel}_'
        # ArduPilot DO_SET_SERVO: Disabled veya RC passthrough çıkışları.
        # Motor/kontrol yüzeyi işlevlerini kabul etmez; FC parametresi yazılmaz.
        if params.get(prefix+'FUNCTION') not in (0, 1, *range(51, 67)):
            raise RuntimeError('Çıkış servo denemesine uygun değil; servo gönderilmedi')
        if not params.get(prefix+'MIN', 9999) <= args.pwm <= params.get(prefix+'MAX', 0):
            raise RuntimeError('PWM okunan MIN/MAX dışında; servo gönderilmedi')
        command(512, 245)
        receive(.3)
        if not grounded():
            raise RuntimeError('Taze hex/DISARM/ON_GROUND teyidi yok; servo gönderilmedi')
        command(183, args.channel, args.pwm)
        print(json.dumps({'sent_once': True, 'channel': args.channel, 'pwm': args.pwm}), flush=True)
        messages = receive(.7)
        command(512, 36)
        messages += receive(.7)
        print(json.dumps({'acks': [m for m in messages if m['mavpackettype']=='COMMAND_ACK' and m['command']==183],
                          'servo_output': latest.get('SERVO_OUTPUT_RAW'),
                          'status_text': [m for m in messages if m['mavpackettype']=='STATUSTEXT']},
                         ensure_ascii=False), flush=True)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
