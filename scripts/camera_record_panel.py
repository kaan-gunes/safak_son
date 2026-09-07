"""Kamera kalibrasyonu için salt okunur panel; Hailo/MAVLink/kontrol açmaz.

Pi: python3 scripts/camera_panel.py
SIGUSR1: mevcut odak konumunu kilitle; SIGUSR2: önizleme otomatik odağı.
"""
import json
from pathlib import Path
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
from libcamera import Transform, controls
from picamera2 import Picamera2

PAGE = """<!doctype html><html lang="tr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ŞAFAK • Kamera kalibrasyonu</title>
<style>body{margin:0;background:#10141d;color:#edf2f8;font:16px system-ui}
main{max-width:1280px;margin:auto;padding:20px}h1{font-size:24px}
img{width:100%;display:block;background:#202633;border-radius:10px}
p{color:#bccadb}b{color:#80e6b3}</style><main>
<h1>IMX708 · Temiz video kaydı · Model kapalı</h1>
<p><b>Otomatik kontrol kapalı</b> · Yalnız kamera · Hailo bağlantısı yok; temiz kamera videosu kaydediliyor</p>
<img id="v" alt="Kamera görüntüsü bekleniyor"><p id="s"></p></main>
<script>const v=document.getElementById('v'),s=document.getElementById('s');
let shown=0,lastId=null,displayFps=0,windowAt=performance.now(),cameraFps=0,previous=null;
async function frame(){const start=performance.now();try{
const r=await fetch('/frame.jpg',{cache:'no-store',signal:AbortSignal.timeout(1500)});
if(!r.ok)throw Error('Görüntü yok');
const id=r.headers.get('X-Frame-Id'),blob=await r.blob();
if(id!==lastId){const u=URL.createObjectURL(blob),old=v.src;v.src=u;
try{await v.decode();shown++;lastId=id;}finally{if(old.startsWith('blob:'))URL.revokeObjectURL(old)}}
}catch(e){v.removeAttribute('src')}
const now=performance.now();if(now-windowAt>=1000){displayFps=shown*1000/(now-windowAt);shown=0;windowAt=now}
setTimeout(frame,Math.max(0,1000/15-(performance.now()-start)))}
async function status(){try{const r=await fetch('/api/status',{cache:'no-store',signal:AbortSignal.timeout(1500)}),d=await r.json();
const stamp=d.metadata.SensorTimestamp;if(previous&&stamp>previous.stamp)cameraFps=(d.frame_id-previous.id)*1e9/(stamp-previous.stamp);
previous={id:d.frame_id,stamp};
s.textContent=d.error||`${d.camera.model} · Kamera ${cameraFps.toFixed(1)} FPS · Panel ${displayFps.toFixed(1)} FPS · Kare ${d.frame_id} · Yaş ${d.age_ms} ms · Odak: ${d.focus_mode} · KAYIT ${d.video_frames||0} kare`
}catch(e){s.textContent='Kamera bağlantısı yok'}setTimeout(status,1000)}frame();status();</script></html>"""

lock = threading.Lock()
stop = threading.Event()
focus_request = threading.Event()
auto_request = threading.Event()
state = {"frame_id": 0, "at": 0, "image": None, "jpeg": None,
         "jpeg_frame_id": 0, "jpeg_at": 0, "error": None, "metadata": {}, "focus_mode": "otomatik önizleme", "camera": {}}
stream_id = str(time.time_ns())


def capture():
    camera = None
    writer = None
    log = None
    root = Path('runtime/red-blue-camera-recordings') / time.strftime('%Y%m%dT%H%M%S')
    root.mkdir(parents=True,exist_ok=False)
    (root/'manifest.json').write_text(json.dumps({'mode':'camera_only','hailo':False,'overlay':False,'fps_nominal':30,'timing':'SensorTimestamp in frames.jsonl','lens_position':0.1}))
    log = (root/'frames.jsonl').open('w')
    segment = -1
    segment_at = 0
    total = 0
    try:
        camera = Picamera2()
        if camera.camera_properties.get("Model") != "imx708":
            raise RuntimeError("Bu panel IMX708 için hazırlanmıştır; kamera modeli uyuşmuyor")
        camera.configure(camera.create_video_configuration(
            main={"size": (1280, 720), "format": "RGB888"},
            sensor={"output_size": (2304, 1296), "bit_depth": 10},
            controls={"FrameRate": 30, "AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.1},
            transform=Transform(hflip=False, vflip=False), buffer_count=4, queue=False))
        camera.start()
        last_jpeg = 0
        while not stop.is_set():
            request = camera.capture_request()
            try:
                meta = request.get_metadata()
                frame = request.make_array("main").copy()
            finally:
                request.release()
            now = time.monotonic()
            crop = list(meta.get("ScalerCrop", []))
            if crop != [0, 0, 4608, 2592]:
                raise RuntimeError(f"Beklenmeyen kamera crop: {crop}")
            if focus_request.is_set():
                position = meta.get("LensPosition")
                if position is None:
                    raise RuntimeError("Odak konumu okunamadı")
                camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": position})
                with lock:
                    state["focus_mode"] = "sabit"
                focus_request.clear()
            if auto_request.is_set():
                camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
                with lock:
                    state["focus_mode"] = "otomatik önizleme"
                auto_request.clear()
            if writer is None or now-segment_at >= 30:
                if writer is not None:
                    writer.release()
                segment += 1
                video_name = f'video-{segment:04d}.avi'
                writer = cv2.VideoWriter(str(root/video_name),cv2.VideoWriter_fourcc(*'MJPG'),30,(1280,720))
                if not writer.isOpened():
                    raise RuntimeError('Video dosyası açılamadı')
                segment_at = now
                segment_frame = 0
            writer.write(frame)
            total += 1
            segment_frame += 1
            log.write(json.dumps({'video':video_name,'segment_frame':segment_frame,'total':total,'metadata':meta},default=str)+'\n')
            log.flush()
            with lock:
                state.update(recording=str(root),video_frames=total,video_file=video_name,focus_mode='sabit',backend='PICAMERA2; HAILO KAPALI')
            jpeg = None
            if now - last_jpeg >= 1 / 30:
                ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if ok:
                    jpeg = encoded.tobytes()
                    last_jpeg = now
            with lock:
                state.update(frame_id=state["frame_id"] + 1, at=now, image=frame, metadata=meta,
                             camera={"model": "imx708", "width": 1280, "height": 720,
                                     "scaler_crop": crop, "mirror": False,
                                     "sensor_output_size": [2304, 1296],
                                     "lens_position": meta.get("LensPosition"),
                                     "focus_mode": state["focus_mode"]})
                if jpeg is not None:
                    state["jpeg"] = jpeg
                    state["jpeg_frame_id"] = state["frame_id"]
                    state["jpeg_at"] = now
    except Exception as error:
        with lock:
            state["error"] = str(error)
    finally:
        if writer is not None:
            writer.release()
        if log is not None:
            log.close()
        if camera is not None:
            camera.stop()
            camera.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        with lock:
            current = dict(state)
        age = time.monotonic() - current["at"]
        extra = {}
        status = 200
        if path == "/":
            body, mime = PAGE.encode(), "text/html; charset=utf-8"
        elif path == "/api/status":
            report = {k: v for k, v in current.items() if k not in ("image", "jpeg", "at")}
            report.update(age_ms=round(age * 1000), stream_id=stream_id,
                          mode="camera_only", calibration_loaded=False, automatic_control=False,
                          lens_position=current["metadata"].get("LensPosition"))
            body, mime = json.dumps(report).encode(), "application/json"
        elif path in ("/frame.jpg", "/calibration/frame.png"):
            mime = "image/jpeg" if path == "/frame.jpg" else "image/png"
            if age > .5 or current["error"] or current["image"] is None:
                status, body = 503, b"Camera unavailable"
            elif path == "/frame.jpg":
                body = current["jpeg"] or b""
                if not body:
                    status = 503
            else:
                ok, encoded = cv2.imencode(".png", current["image"], [cv2.IMWRITE_PNG_COMPRESSION, 3])
                body = encoded.tobytes() if ok else b""
                status = 200 if ok else 503
            image_id = current["jpeg_frame_id"] if path == "/frame.jpg" else current["frame_id"]
            image_age = time.monotonic() - current["jpeg_at"] if path == "/frame.jpg" else age
            extra = {"X-Frame-Id": str(image_id), "X-Frame-Age-Ms": str(round(image_age * 1000)),
                     "X-Camera-Meta": json.dumps(current["camera"]), "X-Stream-Id": stream_id,
                     "X-Frame-Backend": "PICAMERA2"}
        else:
            status, body, mime = 404, b"Not found", "text/plain"
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in extra.items():
            self.send_header(key, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGUSR1, lambda *_: focus_request.set())
    signal.signal(signal.SIGUSR2, lambda *_: auto_request.set())
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    server.timeout = .25
    worker = threading.Thread(target=capture, daemon=True)
    worker.start()
    print("Yalnız kamera paneli :8080; uçuş/kontrol bağlantısı yok", flush=True)
    try:
        while not stop.is_set():
            server.handle_request()
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=5)
