"""Aynı Picamera2 akışında satranç tahtasıyla ölçülmüş kamera kalibrasyonu."""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from .config import Config
from .hailo_backend import create_picamera


def solve(folder: Path, cols: int, rows: int, square_mm: float, output: Path,
          detector: str = "sb"):
    if not 3 <= cols <= 20 or not 3 <= rows <= 20 or not 0 < square_mm < 200:
        raise ValueError("İç köşe sayıları ve ölçülmüş kare boyutu geçersiz")
    if detector not in {"sb", "classic"}:
        raise ValueError("Köşe bulucu sb veya classic olmalı")
    info = json.loads((folder / "camera.json").read_text())
    grid = np.zeros((cols * rows, 3), np.float32)
    grid[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_mm / 1000
    objects, images, filenames = [], [], []
    for path in sorted(folder.glob("*.png")):
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None or image.shape[::-1] != (info["width"], info["height"]):
            continue
        if detector == "classic":
            ok, corners = cv2.findChessboardCorners(
                image, (cols, rows), cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE)
            if ok:
                corners = cv2.cornerSubPix(image, corners, (7, 7), (-1, -1),
                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 50, .001))
        else:
            ok, corners = cv2.findChessboardCornersSB(image, (cols, rows), cv2.CALIB_CB_NORMALIZE_IMAGE)
        if ok:
            objects.append(grid.copy())
            images.append(corners.astype(np.float32))
            filenames.append(path.name)
    if len(images) < 18:
        raise ValueError(f"Yalnız {len(images)} uygun görüntü var; farklı konum/açılardan en az 18 gerekli")
    centers = np.array([p.reshape(-1, 2).mean(axis=0) for p in images])
    spans = np.ptp(centers, axis=0) / [info["width"], info["height"]]
    if spans.min() < .25:
        raise ValueError("Tahta kadrajın yeterince farklı bölgelerini kapsamıyor; kenar/köşe görüntüleri ekleyin")
    size = (info["width"], info["height"])
    rms, matrix, distortion, rotations, translations = cv2.calibrateCamera(objects, images, size, None, None)
    per_view = []
    for obj, points, rv, tv in zip(objects, images, rotations, translations):
        projected, _ = cv2.projectPoints(obj, rv, tv, matrix, distortion)
        per_view.append(float(np.sqrt(np.mean(np.sum((projected - points) ** 2, axis=2)))))
    if not np.isfinite(matrix).all() or not 0 <= rms <= 1.0:
        raise ValueError(f"Kalibrasyon RMS {rms:.3f} px; kabul sınırı 1 px")
    if not np.isfinite(distortion).all() or not np.isfinite(per_view).all():
        raise ValueError("Kalibrasyon katsayıları veya görüntü hataları sonlu değil")
    bad = [(name, error) for name, error in zip(filenames, per_view) if error > 1.0]
    if bad:
        details = ", ".join(f"{name}: {error:.2f} px" for name, error in bad)
        raise ValueError("Tek görüntü RMS sınırı 1 px aşıldı; kareleri gözden geçirin: " + details)
    result = {"schema": 1, "projection": "pinhole", "width": size[0], "height": size[1],
              "camera_model": info["model"], "scaler_crop": info["scaler_crop"],
              "camera_matrix": matrix.tolist(), "distortion": distortion.reshape(-1).tolist(),
              "rms_px": float(rms), "views": len(images), "per_view_rms_px": per_view,
              "source_files": filenames, "board_inner_corners": [cols, rows], "measured_square_mm": square_mm,
              "corner_detector": detector, "center_span_xy": spans.tolist(),
              "physical_distance_verified": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(f"Kalibrasyon: {output.resolve()} · {len(images)} kare · RMS {rms:.3f} px")


def capture_from_panel(folder: Path, count: int, interval: float, panel_url: str):
    """Çalışan gözlem uygulamasının aynı fiziksel kamerasından, kayıpsız kareler."""
    first_info, last_id, first_stream = None, None, None
    for i in range(count):
        time.sleep(interval)
        with urllib.request.urlopen(panel_url.rstrip("/") + "/calibration/frame.png", timeout=3) as response:
            body = response.read()
            fid = int(response.headers["X-Frame-Id"])
            age = float(response.headers["X-Frame-Age-Ms"])
            raw_info = json.loads(response.headers["X-Camera-Meta"])
            detections_header = response.headers.get("X-Detections")
            detections = json.loads(detections_header) if detections_header is not None else None
            backend = response.headers.get("X-Frame-Backend", "UNKNOWN")
            stream_id = response.headers.get("X-Stream-Id")
        if (last_id is not None and fid <= last_id) or not 0 <= age <= 500:
            raise ValueError("Kalibrasyon için yinelenen/eski kamera karesi geldi")
        if first_info is not None and stream_id != first_stream:
            raise ValueError("Yakalama sırasında uygulama/kamera oturumu değişti")
        if raw_info.get("mirror") is not False:
            raise ValueError("Kalibrasyon görüntüsünün aynasız olduğu doğrulanmadı")
        info = {k: raw_info[k] for k in ("width", "height", "model", "scaler_crop")}
        decoded = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)
        if decoded is None or decoded.shape[:2] != (info["height"], info["width"]):
            raise ValueError("Tam çözünürlüklü kamera PNG'si geçersiz")
        if first_info is not None and info != first_info:
            raise ValueError("Kalibrasyon sırasında kamera/crop değişti")
        if first_info is None:
            first_info = info
            first_stream = stream_id
            (folder / "camera.json").write_text(json.dumps(info, indent=2))
        (folder / f"frame-{i:03d}.png").write_bytes(body)
        (folder / f"frame-{i:03d}.json").write_text(json.dumps({
            "frame_id": fid, "stream_id": stream_id, "age_ms_at_response": age,
            "received_unix_s": time.time(), "backend": backend,
            "camera": raw_info, "detections": detections}, ensure_ascii=False, indent=2))
        last_id = fid
        print(f"{i + 1}/{count} tam çözünürlüklü kare kaydedildi (kamera karesi {fid})", flush=True)


def capture(cfg: Config, folder: Path, count: int, interval: float, panel_url: str | None = None):
    folder.mkdir(parents=True, exist_ok=True)
    if list(folder.glob("*.png")):
        raise ValueError("Farklı oturumları karıştırmamak için boş bir çıktı klasörü kullanın")
    if panel_url:
        capture_from_panel(folder, count, interval, panel_url)
        return
    camera = create_picamera(cfg)
    try:
        camera.start()
        print("Kamera kalibrasyonu: tahtayı kadrajın farklı köşelerinde, farklı açılarda tutun.", flush=True)
        first_info = None
        for i in range(count):
            time.sleep(interval)
            request = camera.capture_request()
            try:
                meta = request.get_metadata()
                info = {"width": cfg.camera.width, "height": cfg.camera.height,
                        "model": camera.camera_properties.get("Model", "UNKNOWN"),
                        "scaler_crop": list(meta.get("ScalerCrop", []))}
                if first_info is not None and info != first_info:
                    raise RuntimeError("Kalibrasyon sırasında kamera/crop değişti")
                if first_info is None:
                    first_info = info
                    (folder / "camera.json").write_text(json.dumps(info, indent=2))
                frame = request.make_array("main")
                if not cv2.imwrite(str(folder / f"frame-{i:03d}.png"), frame):
                    raise RuntimeError("Kalibrasyon görüntüsü yazılamadı")
                print(f"{i + 1}/{count} görüntü kaydedildi", flush=True)
            finally:
                request.release()
    finally:
        camera.stop()
        camera.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    take = commands.add_parser("capture")
    take.add_argument("--config", default="config/quad.json")
    take.add_argument("--folder", required=True, type=Path)
    take.add_argument("--count", type=int, default=35)
    take.add_argument("--interval", type=float, default=1.5)
    take.add_argument("--panel-url", help="Çalışan gözlem paneli; ör. http://127.0.0.1:8080")
    fit = commands.add_parser("solve")
    fit.add_argument("--folder", required=True, type=Path)
    fit.add_argument("--cols", required=True, type=int, help="Yatay iç köşe sayısı")
    fit.add_argument("--rows", required=True, type=int, help="Düşey iç köşe sayısı")
    fit.add_argument("--square-mm", required=True, type=float, help="Basılmış tek karenin ölçülmüş kenarı")
    fit.add_argument("--output", default="config/camera.local.json", type=Path)
    fit.add_argument("--detector", choices=("sb", "classic"), default="sb",
                     help="Köşe bulucu; iki yöntemin de sonuçları görsel olarak incelenmelidir")
    args = parser.parse_args()
    if args.command == "capture":
        if not 18 <= args.count <= 100 or not .5 <= args.interval <= 10:
            parser.error("count 18–100, interval 0.5–10 aralığında olmalı")
        capture(Config.load(args.config), args.folder, args.count, args.interval, args.panel_url)
    else:
        solve(args.folder, args.cols, args.rows, args.square_mm, args.output, args.detector)


if __name__ == "__main__":
    main()
