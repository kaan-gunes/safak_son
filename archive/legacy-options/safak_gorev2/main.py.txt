from __future__ import annotations

import argparse
import signal
import threading
from dataclasses import replace

from waitress import create_server, wasyncore

from .config import Config
from .demo import Demo
from .hailo_backend import run_hailo
from .runtime import Runtime
from .web import create_app


def main():
    parser = argparse.ArgumentParser(description="ŞAFAK Görev 2 quad test uygulaması")
    parser.add_argument("--config", default="config/quad.json")
    parser.add_argument("--mode", choices=("observe", "flight", "demo"), default="observe")
    parser.add_argument("--hailo-env", help="detection.py'nin kullandığı HAILO_ENV_FILE")
    args = parser.parse_args()
    cfg = Config.load(args.config)
    if args.mode == "flight":
        missing = cfg.flight_missing()
        if missing:
            parser.error("Uçuş yapılandırması eksik: " + "; ".join(missing))
    if args.mode == "demo":
        cfg = replace(cfg, camera=replace(cfg.camera, width=1280, height=720,
                       offset_body_m=(-.12, 0., .05), calibration_file=None),
                      web=replace(cfg.web, host="127.0.0.1"), runtime_dir=cfg.runtime_dir + "/demo")
    runtime = Runtime(cfg, args.mode)
    def shutdown(signum=None, frame=None):
        runtime.stop.set()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    demo = Demo(runtime) if args.mode == "demo" else None
    panel_sockets = {}
    server = create_server(create_app(cfg, runtime.state, runtime.telemetry), map=panel_sockets,
                           host=cfg.web.host, port=cfg.web.port, threads=6, channel_timeout=5)
    def serve_panel():
        try:
            while not runtime.stop.is_set():
                wasyncore.loop(timeout=.2, count=1, map=panel_sockets,
                               use_poll=server.adj.asyncore_use_poll)
        finally:
            server.task_dispatcher.shutdown(timeout=2)
            # Soketler I/O döngüsünün kendi iş parçacığında kapanır.
            wasyncore.close_all(panel_sockets)
    server_thread = threading.Thread(target=serve_panel, daemon=True, name="flask-panel")
    server_thread.start()
    runtime.start(connect=demo is None)
    if demo:
        demo.start_thread()
    print(f"Panel: http://{'127.0.0.1' if args.mode == 'demo' else 'RASPBERRY_PI_IP'}:{cfg.web.port}", flush=True)
    print(f"Çalışma modu: {args.mode}; bırakma daima TEMSİLİ", flush=True)
    try:
        if not demo:
            try:
                run_hailo(cfg, runtime.mailbox, runtime.state, runtime.stop, args.hailo_env)
            except Exception as e:
                runtime.state.pipeline_error = str(e)
                runtime.state.event("ERROR", str(e))
                print(f"HATA: {e}", flush=True)
        while not runtime.stop.wait(.25):
            pass
    finally:
        runtime.close()
        server_thread.join(timeout=3)


if __name__ == "__main__":
    main()
