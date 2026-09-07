"""Pi panelinden video/telemetri kaydı; kamera veya MAVLink bağlantısı açmaz."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
import time
import urllib.request
import zipfile

import cv2
import numpy as np


def get(url):
    with urllib.request.urlopen(url, timeout=.45) as response:
        return response.read(),dict(response.headers)


def overlay(jpeg, status, *, status_age, image_age, wall_time, error=None):
    image=cv2.imdecode(np.frombuffer(jpeg,np.uint8),cv2.IMREAD_COLOR) if jpeg else None
    if image is None:image=np.zeros((540,960,3),np.uint8)
    image=cv2.resize(image,(960,540),interpolation=cv2.INTER_AREA)
    canvas=np.zeros((700,960,3),np.uint8);canvas[:540]=image
    t=status.get('telemetry',{});v=status.get('vision',{});d=status.get('decision',{})
    stamp=datetime.fromtimestamp(wall_time).astimezone().isoformat(timespec='milliseconds')
    stale=status_age>1 or image_age>.5 or bool(error)
    lines=[f"KAYIT {stamp} | {'VERI/GORUNTU ESKI' if stale else 'CANLI'}",
           f"{status.get('mode','UNKNOWN')} | {t.get('mode','UNKNOWN')} | {'ARM' if t.get('armed') else 'DISARM/UNKNOWN'} | {d.get('state','UNKNOWN')}",
           f"GPS {t.get('satellites')} | HDOP {t.get('hdop')} | RC {t.get('rc_selected_mode')} | Batarya {t.get('voltage')} V",
           f"Bagil irtifa {t.get('relative_alt_m')} m | AI kutu {len(v.get('detections',[]))} | Gecerli hedef {len(v.get('targets',[]))}",
           f"Kare yasi {image_age:.2f}s | Telemetri yasi {status_age:.2f}s | {str(error or '')[:65]}"]
    for i,line in enumerate(lines):
        cv2.putText(canvas,line,(12,565+i*28),cv2.FONT_HERSHEY_SIMPLEX,.48,
                    (80,100,255) if stale and i==0 else (235,235,235),1,cv2.LINE_AA)
    ok,encoded=cv2.imencode('.jpg',canvas,[cv2.IMWRITE_JPEG_QUALITY,80])
    if not ok:raise RuntimeError('Kayit goruntusu kodlanamadi')
    return encoded.tobytes()


def run(args):
    if not shutil.which('ffmpeg'):raise RuntimeError('ffmpeg bulunamadi')
    root=Path(args.root).resolve();root.mkdir(parents=True,exist_ok=True)
    lock=(root/'.recorder.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if shutil.disk_usage(root).free<1024**3:raise RuntimeError('Kayit icin en az 1 GB bos alan gerekli')
    out=root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+f'-{os.getpid()}')
    out.mkdir(exist_ok=False)
    manifest={'schema':1,'status':'recording','pid':os.getpid(),'started_utc':datetime.now(timezone.utc).isoformat(),
              'panel_url':args.panel_url,'fps':8,'video':'video-%04d.mkv','segment_s':30,
              'scope':'Panelin etiketli kamera JPEG goruntusu ve telemetri HUD kaydi; tarayici penceresinin piksel kopyasi veya tum 30 FPS ham kamera akisi degildir.',
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    project=Path(__file__).resolve().parents[1]
    # Mevcut yazılım/ayarların kopyası; profil seçimi API mode/kamera alanlarıyla eşlenir.
    with zipfile.ZipFile(out/'software-config.zip','w',zipfile.ZIP_DEFLATED) as archive:
        paths=list((project/'safak_gorev2').rglob('*.py'))+list((project/'config').glob('*.json'))
        for path in sorted(paths):archive.write(path,str(path.relative_to(project)))
    model=project/'safak_v2_hailo_model/safak_v2.hef'
    if getattr(args, 'config', None):
        from .config import Config
        config = Config.load(args.config)
        config.verify_model()
        model = Path(config.hef_file)
        manifest['config_file'] = str(Path(args.config).resolve())
        manifest['config_sha256'] = hashlib.sha256(Path(args.config).read_bytes()).hexdigest()
    manifest['hef_file'] = str(model)
    manifest['hef_sha256']=hashlib.sha256(model.read_bytes()).hexdigest() if model.exists() else None
    stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
    state={'status':{},'at':-float('inf'),'errors':0};guard=threading.Lock()
    def status_loop():
        armed=None
        with (out/'telemetry.jsonl').open('w',buffering=1) as fp:
            last_sync=0
            while not stop.is_set():
                tick=time.monotonic();now=time.time()
                try:
                    body,_=get(args.panel_url+'/api/status');data=json.loads(body)
                    record={'wall_time':now,'received_monotonic':tick,'status':data}
                    with guard:state.update(status=data,at=tick)
                    t=data.get('telemetry',{});age=data.get('ages_s',{}).get('heartbeat')
                    if isinstance(age,(int,float)) and age<1.5 and isinstance(t.get('armed'),bool):
                        if armed is not None and t['armed']!=armed:record['arm_transition']='ARM' if t['armed'] else 'DISARM'
                        armed=t['armed']
                except Exception as e:
                    record={'wall_time':now,'received_monotonic':tick,'error':str(e)}
                    with guard:state['errors']+=1
                fp.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')
                if tick-last_sync>=1:fp.flush();os.fsync(fp.fileno());last_sync=tick
                stop.wait(max(0,.2-(time.monotonic()-tick)))
            fp.flush();os.fsync(fp.fileno())
    def save_status(status,error=None):
        with guard:errors=state['errors']
        record={'status':status,'pid':os.getpid(),'directory':str(out),'video_frames':count,
                'status_errors':errors,'updated_utc':datetime.now(timezone.utc).isoformat(),'error':error}
        tmp=root/f'.active-{os.getpid()}.json';tmp.write_text(json.dumps(record,ensure_ascii=False,indent=2));tmp.replace(root/'active.json')
        manifest.update(record);(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    ff_log=(out/'ffmpeg.log').open('w')
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','warning','-threads','1',
             '-f','image2pipe','-framerate','8','-vcodec','mjpeg','-i','pipe:0','-an','-c:v','copy',
             '-f','segment','-segment_time','30','-reset_timestamps','1','-segment_format','matroska',
             '-segment_format_options','cluster_time_limit=1000:flush_packets=1',str(out/'video-%04d.mkv')]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=ff_log)
    count=0;thread=threading.Thread(target=status_loop,daemon=True);thread.start()
    failure=None;started=time.monotonic();last_save=started;last_id=None
    try:
        save_status('recording');print(str(out),flush=True)
        with (out/'video-frames.jsonl').open('w',buffering=1) as fp:
            while not stop.is_set() and (not args.duration or time.monotonic()-started<args.duration):
                tick=time.monotonic();wall=time.time();error=None;jpeg=None;fid=None;image_age=float('inf')
                if process.poll() is not None:raise RuntimeError('ffmpeg beklenmeden kapandi')
                if not thread.is_alive():raise RuntimeError('Telemetri kayit is parcacigi durdu')
                try:
                    jpeg,headers=get(args.panel_url+'/frame.jpg')
                    if not jpeg:raise RuntimeError('Panel goruntusu bos')
                    fid=headers.get('X-Frame-Id');image_age=float(headers['X-Frame-Age-Ms'])/1000
                except Exception as e:error=str(e)
                with guard:data=state['status'];status_age=tick-state['at']
                hb=data.get('ages_s',{}).get('heartbeat')
                effective_age=status_age+hb if isinstance(hb,(int,float)) else float('inf')
                encoded=overlay(jpeg,data,status_age=effective_age,image_age=image_age,wall_time=wall,error=error)
                process.stdin.write(encoded)
                row={'video_frame':count,'wall_time':wall,'received_monotonic':tick,'frame_id':fid,
                     'duplicate_source_frame':fid==last_id,'source_age_s':image_age if np.isfinite(image_age) else None,
                     'status_age_s':effective_age if np.isfinite(effective_age) else None,'error':error,
                     'loop_duration_s':time.monotonic()-tick}
                fp.write(json.dumps(row,allow_nan=False)+'\n');last_id=fid;count+=1
                if tick-last_save>=1:
                    fp.flush();os.fsync(fp.fileno());save_status('recording');last_save=tick
                    if shutil.disk_usage(root).free<1024**3:raise RuntimeError('Disk bos alani 1 GB altina indi; kayit durduruldu')
                stop.wait(max(0,.125-(time.monotonic()-tick)))
            fp.flush();os.fsync(fp.fileno())
    except Exception as e:failure=str(e)
    finally:
        stop.set();thread.join(timeout=2)
        try:process.stdin.close()
        except OSError:pass
        try:code=process.wait(timeout=8)
        except subprocess.TimeoutExpired:process.kill();code=process.wait();failure=failure or 'ffmpeg kapanis zaman asimi'
        ff_log.close()
        if code:failure=failure or f'ffmpeg exit {code}'
        save_status('failed' if failure else 'complete',failure)
        lock.close()
    if failure:raise RuntimeError(failure)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel-url',default='http://127.0.0.1:8080')
    p.add_argument('--root',default='runtime/recordings')
    p.add_argument('--duration',type=float,default=0,help='0: SIGTERM gelene kadar kaydet')
    p.add_argument('--config',help='Kaydedilen uygulamanın gerçek profil/model kimliği')
    args=p.parse_args()
    if args.duration<0:p.error('duration negatif olamaz')
    try:run(args)
    except Exception as e:p.exit(2,f'Kayit hatasi: {e}\n')

if __name__=='__main__':main()
