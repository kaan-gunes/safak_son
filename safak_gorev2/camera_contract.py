"""Kamera sözleşmesi: bilinmeyen fiziksel özelliklere sessiz yedek yok."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path


def validate_camera(c):
    if c.backend not in ('picamera2', 'v4l2-observe'):
        raise ValueError('Kamera backend desteklenmiyor; sessiz fallback yok')
    if c.variant not in (None, 'imx708', 'arducam-ezbox-swift'):
        raise ValueError('Bilinmeyen kamera varyantı')
    if c.variant == 'imx708' and (c.backend != 'picamera2' or c.identity != 'imx708'):
        raise ValueError('IMX708 backend/kimlik uyuşmazlığı')
    if c.variant == 'arducam-ezbox-swift':
        if c.backend != 'v4l2-observe' or c.lens_position is not None or c.sensor_output_size is not None:
            raise ValueError('Arducam IMX708 backend/odak/sensör ayarını kullanamaz')
        if c.calibration_file:
            saved = json.loads(Path(c.calibration_file).read_text())
            if (saved.get('camera_variant') != c.variant or not c.identity
                    or saved.get('camera_identity') != c.identity
                    or saved.get('backend') != c.backend):
                raise ValueError('Arducam kalibrasyon kimliği/backend farklı; IMX708 matrisi kullanılamaz')
    if c.variant == 'imx708' and c.calibration_file:
        saved = json.loads(Path(c.calibration_file).read_text())
        if saved.get('camera_model') != 'imx708':
            raise ValueError('IMX708 kalibrasyon kamera kimliği farklı')
        if (saved.get('lens_position') != c.lens_position
                or tuple(saved.get('sensor_output_size', ())) != tuple(c.sensor_output_size or ())):
            raise ValueError('IMX708 kalibrasyon odak/sensör modu farklı')


def capture_missing(c):
    missing = []
    if c.variant and not c.identity:
        missing.append('gerçek kamera kimliği')
    if c.backend == 'v4l2-observe':
        if not c.device or not c.device.startswith(('/dev/v4l/by-id/', '/dev/v4l/by-path/')):
            missing.append('sabit V4L2 by-id/by-path cihazı')
        if not c.usb_vid_pid:
            missing.append('USB VID:PID')
        if not c.pixel_format or len(c.pixel_format) != 4:
            missing.append('ölçülmüş V4L2 FOURCC')
    return missing


def metric_missing(c):
    # USB backend teslim alma zamanını ölçer; poz zaman eşlemesi kabul edilmiş değil.
    if c.backend == 'v4l2-observe':
        return ['Arducam poz zaman damgası/backend ve ayrı montaj/metrik kabulü; yalnız gözlem']
    return []


def camera_manifest(c):
    saved = json.loads(Path(c.calibration_file).read_text()) if c.calibration_file else {}
    return {'variant': c.variant, 'backend': c.backend, 'identity': c.identity,
            'device': c.device, 'usb_vid_pid': c.usb_vid_pid,
            'requested_size': [c.width, c.height], 'requested_fps': c.fps,
            'pixel_format': c.pixel_format, 'calibration_file': c.calibration_file,
            'calibration_sha256': hashlib.sha256(Path(c.calibration_file).read_bytes()).hexdigest() if c.calibration_file else None,
            'calibration_capture_lens_position': saved.get('calibration_capture_lens_position'),
            'runtime_lens_position': c.lens_position, 'sensor_output_size':c.sensor_output_size,
            'offset_body_m':c.offset_body_m,
            'focus_transfer_verified': saved.get('focus_transfer_verified', False),
            'physical_distance_verified': saved.get('physical_distance_verified', False),
            'metric_status': 'yaklaşık/deneysel; saha kabulü yok' if saved and not saved.get('physical_distance_verified') else ('kalibrasyon yok' if not saved else 'dosya beyanı; canlı kabul ayrıca gerekli')}


def profile_digest(cfg, options):
    body = {'config':asdict(cfg),'options':asdict(options)}
    return hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
