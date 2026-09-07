"""Yalnız Picamera2 + Hailo kutu önizlemesi. MAVLink/servo/controller başlatmaz."""
import dataclasses
import json
from pathlib import Path
import signal
import threading
import time
import cv2
import camera_panel as panel
from safak_gorev2.config import Config
from safak_gorev2.hailo_backend import run_hailo
import safak_gorev2.hailo_backend as backend
from safak_gorev2.shared import LatestFrame, SharedState


def main():
    cfg = Config.load('config/camera-hailo-only.json')
    cfg.verify_model()
    initial_lens = cfg.camera.lens_position
    cfg = dataclasses.replace(cfg, camera=dataclasses.replace(cfg.camera,lens_position=None))
    camera_metadata = {}
    control_path = Path('runtime/camera-hailo-controls.json')
    original_create = backend.create_picamera
    class CameraProxy:
        def __init__(self, camera):
            self.camera = camera
            self.control_version = None
            self.checked_at = 0
        def __getattr__(self, name):
            return getattr(self.camera, name)
        def capture_request(self):
            if time.monotonic()-self.checked_at > .25:
                self.checked_at = time.monotonic()
                if control_path.exists():
                    version = control_path.stat().st_mtime_ns
                    if version != self.control_version:
                        values = json.loads(control_path.read_text())
                        if set(values)-{'LensPosition','ExposureValue'}:
                            raise ValueError('Desteklenmeyen kamera ayarı')
                        for key,value in values.items():
                            lo,hi,_ = self.camera.camera_controls[key]
                            if not isinstance(value,(int,float)) or not lo <= value <= hi:
                                raise ValueError('Kamera ayarı sınır dışında')
                        self.camera.set_controls(values)
                        with panel.lock:
                            panel.state['requested_controls'] = values
                        self.control_version = version
            request = self.camera.capture_request()
            with panel.lock:
                camera_metadata.clear()
                camera_metadata.update(request.get_metadata())
            return request
    backend.create_picamera = lambda config: CameraProxy(original_create(dataclasses.replace(config,camera=dataclasses.replace(config.camera,lens_position=initial_lens))))
    mailbox = LatestFrame()
    shared = SharedState('observe')
    panel.PAGE = panel.PAGE.replace('Camera Module 3 · Kalibrasyon önizlemesi', 'IMX708 + Hailo · Branda tespiti')
    panel.PAGE = panel.PAGE.replace('Kalibrasyon henüz yok', 'Yalnız AI kutusu; merkezleme/mesafe hesabı yok')
    panel.PAGE = panel.PAGE.replace('d.metadata.SensorTimestamp', 'd.metadata.CaptureMonotonicNs')
    panel.PAGE = panel.PAGE.replace('· Odak: ${d.focus_mode}', '· Odak: ${d.focus_mode} · AI kutusu: ${(d.detections||[]).length} · KAYIT ${(d.video_frames||0)} kare · Eşik 0,40 · Pozlama ${d.live_camera_metadata?.ExposureTime||0} µs · Gain ${Number(d.live_camera_metadata?.AnalogueGain||0).toFixed(2)}')
    panel.state['focus_mode'] = 'sabit'
    root = Path('runtime/camera-hailo-only') / time.strftime('%Y%m%dT%H%M%S')
    root.mkdir(parents=True, exist_ok=False)
    (root/'manifest.json').write_text(json.dumps({'hef_file':cfg.hef_file,'hef_sha256':cfg.hef_sha256,'lens_position':initial_lens,'calibration_loaded':False,'mavlink':False,'confidence_min':cfg.camera.confidence_min,'video_overlay':False,'video_fps_nominal':30,'video_timing':'captured_at in detections.jsonl; nominal FPS is not measured FPS'},indent=2))
    server = panel.ThreadingHTTPServer(('0.0.0.0',8080),panel.Handler)
    server.timeout = .25
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_:panel.stop.set())

    def serve():
        while not panel.stop.is_set():
            server.handle_request()

    def render():
        last = 0
        saved_at = 0
        writer = None
        video_count = 0
        segment = -1
        segment_started = 0
        try:
            with (root/'detections.jsonl').open('w') as log:
                while not panel.stop.is_set():
                    frame = mailbox.get_after(last)
                    if frame is None:
                        continue
                    last = frame.id
                    detections = [d for d in frame.detections if d.confidence >= cfg.camera.confidence_min]
                    image = frame.image.copy()
                    for d in detections:
                        x1,y1,x2,y2 = [int(v*s) for v,s in zip(d.bbox,(1280,720,1280,720))]
                        color = (255,140,40) if d.label == 'mavi_hedef' else (50,50,255)
                        cv2.rectangle(image,(x1,y1),(x2,y2),color,3)
                        cv2.putText(image,f'{d.label} {d.confidence:.2f}',(max(0,x1),max(22,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.65,color,2)
                    ok,jpg = cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,80])
                    if not ok:
                        raise RuntimeError('JPEG üretilemedi')
                    now = time.monotonic()
                    if writer is None or now-segment_started >= 30:
                        if writer is not None:
                            writer.release()
                        segment += 1
                        video_name = f'video-{segment:04d}.avi'
                        writer = cv2.VideoWriter(str(root/video_name),cv2.VideoWriter_fourcc(*'MJPG'),30,(1280,720))
                        if not writer.isOpened():
                            raise RuntimeError('Video kaydı açılamadı')
                        segment_started = now
                    writer.write(frame.image)
                    video_count += 1
                    with panel.lock:
                        live_meta = dict(camera_metadata)
                    record = {'video':video_name,'video_frame_total':video_count,'latest_camera_metadata_unmatched':live_meta,'frame_id':last,'captured_at':frame.captured_at,'detections':[dataclasses.asdict(d) for d in frame.detections]}
                    if now-saved_at >= 1:
                        name = f'{last:08d}.jpg'
                        (root/name).write_bytes(jpg.tobytes())
                        record['image'] = name
                        saved_at = now
                    log.write(json.dumps(record)+'\n')
                    log.flush()
                    with panel.lock:
                        panel.state.update(frame_id=last,at=frame.captured_at,image=image,jpeg=jpg.tobytes(),jpeg_frame_id=last,jpeg_at=frame.captured_at,
                            metadata={'CaptureMonotonicNs':int(frame.captured_at*1e9),'LensPosition':live_meta.get('LensPosition')},
                            camera=shared.camera_info or {},detections=[dataclasses.asdict(d) for d in detections],backend='HAILO',recording=str(root),error=None,live_camera_metadata=live_meta,video_frames=video_count,video_file=video_name)
        except Exception as error:
            with panel.lock:
                panel.state['error'] = str(error)
            panel.stop.set()
        finally:
            if writer is not None:
                writer.release()

    threading.Thread(target=serve,daemon=True).start()
    worker = threading.Thread(target=render,daemon=True)
    worker.start()
    try:
        run_hailo(cfg,mailbox,shared,panel.stop)
    except Exception as error:
        with panel.lock:
            panel.state['error'] = str(error)
        print('HAILO ERROR:',error,flush=True)
        raise
    finally:
        panel.stop.set()
        worker.join(timeout=3)
        server.server_close()


if __name__ == '__main__':
    main()
