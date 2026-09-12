"""Pi'de 20–60 s kamera/OpenCV/JPEG; connect=False, MAVLink açılmaz."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safak_gorev2.competition.config import Options
from safak_gorev2.competition.runtime import CompetitionRuntime
from safak_gorev2.opencv_backend import run_opencv_camera


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True)
    p.add_argument('--seconds',type=int,choices=range(20,61),default=30)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    cfg,o=Options.load(args.config)
    rt=CompetitionRuntime(cfg,'observe',o)
    samples=[]
    probe_errors=[]
    def monitor():
        startup_deadline=time.monotonic()+60
        deadline=None
        while not rt.stop.wait(.5):
            if deadline is None:
                if rt.performance_samples:
                    deadline=time.monotonic()+args.seconds
                elif time.monotonic()>=startup_deadline:
                    probe_errors.append("60 s içinde işlenmiş kamera karesi başlamadı")
                    rt.stop.set()
                    break
                else:
                    continue
            thermal=Path('/sys/class/thermal/thermal_zone0/temp')
            try: throttle=subprocess.run(['vcgencmd','get_throttled'],capture_output=True,text=True,timeout=2).stdout.strip()
            except (OSError,subprocess.SubprocessError): throttle=None
            samples.append({'at':time.monotonic(),'cpu_seconds':time.process_time(),
                'temperature_c':float(thermal.read_text())/1000 if thermal.exists() else None,'throttling':throttle})
            if time.monotonic()>=deadline:rt.stop.set()
    rt.start(connect=False)
    worker=threading.Thread(target=monitor,daemon=True);worker.start()
    error=None
    try:run_opencv_camera(cfg,rt.mailbox,rt.state,rt.stop)
    except Exception as e:error=str(e)
    finally:rt.close();worker.join(timeout=3)
    vision=list(rt.performance_samples)
    def stats(values):
        values=[x for x in values if x is not None]
        return {'median':float(np.median(values)),'p95':float(np.percentile(values,95))} if values else None
    span=vision[-1]['processed_at']-vision[0]['processed_at'] if len(vision)>1 else 0
    result={'scope':'gerçek kamera probe; observe/connect=False; metrik hedef/uçuş kabulü değildir',
        'camera_contract':rt.camera_contract,'actual_camera':rt.state.camera_info,
        'requested_seconds':args.seconds,'processed_frames':len(vision),'processed_fps':(len(vision)-1)/span if span else 0,
        'capture_to_result_ms':stats([(x['processed_at']-x['captured_at'])*1000 for x in vision]),
        'opencv_ms':stats([x['opencv_ms'] for x in vision]),
        'vision_total_ms':stats([x['vision_ms'] for x in vision]),
        'timing_note':'vision_total yalnız OpenCV renk+dörtgen ve varsa PnP toplamı',
        'capture_count':getattr(rt.state,'capture_count',0),'vision_backend':'opencv-color',
        'not_processed_including_shutdown':getattr(rt.state,'capture_count',0)-len(vision),
        'stale_processed':sum(x['stale'] for x in vision),'measured_span_s':span,
        'error':error or rt.state.pipeline_error or ('; '.join(probe_errors) if probe_errors else None),
        'system_samples':samples,'cpu_one_core_percent':100*(samples[-1]['cpu_seconds']-samples[0]['cpu_seconds'])/(samples[-1]['at']-samples[0]['at']) if len(samples)>1 else None,
        'vision_samples':vision}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    if rt.state.jpeg:
        args.output.with_suffix('.jpg').write_bytes(rt.state.jpeg)
    return 1 if result['error'] else 0

if __name__=='__main__':raise SystemExit(main())
