"""Yalnız gözlem USB adaptörü. Zaman damgası exposure değil read dönüşüdür."""
import subprocess
import time
from pathlib import Path
import cv2
from .camera_contract import capture_missing


def usb_identity(device):
    resolved = Path(device).resolve(strict=True)
    result = subprocess.run(['udevadm', 'info', '--query=property', '--name', str(resolved)],
                            check=True, capture_output=True, text=True, timeout=5)
    props = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    return props.get('ID_SERIAL'), props.get('ID_VENDOR_ID', '')+':'+props.get('ID_MODEL_ID', '')


class V4L2Camera:
    def __init__(self, cfg):
        self.cfg = cfg
        c = cfg.camera
        missing = capture_missing(c)
        if missing:
            raise ValueError('; '.join(missing))
        identity, vidpid = usb_identity(c.device)
        if identity != c.identity or vidpid.lower() != c.usb_vid_pid.lower():
            raise ValueError('USB kamera kimliği/VID:PID uyuşmuyor; fallback yok')
        self.camera_properties = {'Model': identity}
        self.cap = cv2.VideoCapture(c.device, cv2.CAP_V4L2)
        try:
            if not self.cap.isOpened():
                raise RuntimeError('V4L2 açılamadı; backend fallback yok')
            settings = ((cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*c.pixel_format)),
                                (cv2.CAP_PROP_FRAME_WIDTH, c.width), (cv2.CAP_PROP_FRAME_HEIGHT, c.height),
                                (cv2.CAP_PROP_FPS, c.fps))
            for prop, value in settings:
                if not self.cap.set(prop, value):
                    raise RuntimeError(f"V4L2 ayarı reddedildi: property={prop}, istek={value}")
            # Boyut/FPS tek sözleşmedir; width yazılırken eski height ile geçici mod seçilebilir.
            for prop, value in settings:
                actual = self.cap.get(prop)
                if abs(actual-value) > .01:
                    raise RuntimeError(f"V4L2 format/boyut/FPS farklı: property={prop}, istek={value}, gerçek={actual}")
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            self.cap.release()
            raise

    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        self.cap.release()

    def capture_request(self):
        ok, frame = self.cap.read()
        stamp = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        if not ok or frame is None or frame.shape != (self.cfg.camera.height, self.cfg.camera.width, 3):
            raise RuntimeError('V4L2 kare eksik/boyut farklı')
        class Request:
            def get_metadata(self):
                return {'SensorTimestamp': stamp, 'TimestampSource': 'read-return; exposure unverified'}
            def make_array(self, _):
                return frame
            def release(self):
                pass
        return Request()
