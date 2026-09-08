"""Pi'de mevcut ortamı yalnız okuyarak inceler; paket/parametre değiştirmez."""
from __future__ import annotations

import argparse
import glob
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .config import Config


def command(argv):
    if not shutil.which(argv[0]):
        return {"available": False}
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=12)
        return {"returncode": result.returncode, "output": (result.stdout + result.stderr)[-10000:]}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/quad.json")
    parser.add_argument("--output", default="runtime/doctor.json")
    args = parser.parse_args()
    cfg = Config.load(args.config)
    report = {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
              "machine": platform.machine(), "serial_devices": glob.glob("/dev/serial/by-id/*"),
              "missing_flight_config": cfg.flight_missing(), "modules": {}, "commands": {}}
    for name in ("hailo", "hailo_platform", "gi", "picamera2", "cv2", "numpy", "flask", "pymavlink",
                 "hailo_apps.hailo_app_python.apps.detection.detection_pipeline"):
        try:
            module = importlib.import_module(name)
            report["modules"][name] = {"path": getattr(module, "__file__", None),
                                       "version": getattr(module, "__version__", None)}
        except Exception as e:
            report["modules"][name] = {"error": str(e)}
    for argv in (["hailortcli", "--version"], ["hailortcli", "scan"],
                 ["hailortcli", "fw-control", "identify"], ["hailortcli", "parse-hef", cfg.hef_file],
                 ["gst-inspect-1.0", "hailonet"], ["rpicam-hello", "--list-cameras"]):
        report["commands"][" ".join(argv)] = command(argv)
    # Ortamın tamamı/parolalar/anahtarlar rapora alınmaz; yalnız Hailo yol bilgileri.
    report["hailo_paths"] = {key: os.environ.get(key) for key in
                            ("HAILO_ENV_FILE", "TAPPAS_POST_PROC_DIR", "TAPPAS_POSTPROC_PATH")}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Salt okunur ortam raporu: {output.resolve()}")
    print(json.dumps({"modules": report["modules"], "missing_flight_config": cfg.flight_missing()},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
