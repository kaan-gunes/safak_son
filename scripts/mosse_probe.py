"""Yalnız dosyalarla MOSSE deneyi; kamera, Hailo veya araç bağlantısı yok.

JSONL: frame_id, timestamp_s, image, detector_bbox_xywh (piksel veya null).
Kutu kaynak kareyle tam eşleşmeli; video HUD'undan yakın zamanla eşleştirmeyin.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time

import cv2
import numpy as np


def make_tracker():
    factory = getattr(getattr(cv2, "legacy", None), "TrackerMOSSE_create", None)
    if factory is None:
        raise RuntimeError("MOSSE yok; ayrı deney ortamına opencv-contrib-python-headless kurun.")
    return factory()


def valid_box(box, shape):
    if box is None or len(box) != 4 or not all(math.isfinite(v) for v in box):
        return False
    x, y, w, h = box
    return x >= 0 and y >= 0 and w >= 4 and h >= 4 and x+w <= shape[1] and y+h <= shape[0]


def iou(a, b):
    if a is None or b is None:
        return None
    x = max(0., min(a[0]+a[2], b[0]+b[2])-max(a[0], b[0]))
    y = max(0., min(a[1]+a[3], b[1]+b[3])-max(a[1], b[1]))
    intersection = x*y
    return intersection / (a[2]*a[3]+b[2]*b[3]-intersection)


class MosseProbe:
    """Takip süresi son AI kutusuna göre sınırlıdır; takip bunu uzatmaz.

    Çıktılar yalnız teşhistir. AI skoru, köşe/PnP veya uçuş kabulü üretmez.
    0,30s boşluk/0,15s kare aralığı yalnız deney başlangıç tercihleridir.
    """
    def __init__(self, max_bridge_s=.30, max_frame_gap_s=.15, factory=make_tracker):
        if not all(math.isfinite(v) and v > 0 for v in (max_bridge_s, max_frame_gap_s)):
            raise ValueError("Süreler pozitif ve sonlu olmalı")
        self.max_bridge_s, self.max_frame_gap_s = max_bridge_s, max_frame_gap_s
        self.factory = factory
        self.tracker = None
        self.last_id = self.last_at = self.last_detection_at = self.shape = None

    def step(self, frame_id, at, bgr, detection=None):
        if type(frame_id) is not int or not math.isfinite(at):
            raise ValueError("Kare kimliği tam sayı, zaman sonlu olmalı")
        if self.last_id is not None and (frame_id <= self.last_id or at <= self.last_at):
            raise ValueError("Kare kimliği ve zaman kesin artmalı")
        if bgr.dtype != np.uint8 or bgr.ndim != 3 or bgr.shape[2] != 3:
            raise ValueError("Görüntü UINT8 BGR, üç kanallı olmalı")
        if self.shape is not None and self.shape != bgr.shape:
            raise ValueError("Görüntü boyutu değişti")
        if detection is not None and not valid_box(detection, bgr.shape):
            raise ValueError("AI kutusu geçersiz veya kadraj dışında")
        reason, predicted = "unseeded", None
        if self.tracker is not None:
            if at-self.last_at > self.max_frame_gap_s:
                reason, self.tracker = "frame_gap", None
            elif at-self.last_detection_at > self.max_bridge_s:
                reason, self.tracker = "expired", None
            else:
                ok, box = self.tracker.update(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
                if ok and valid_box(box, bgr.shape):
                    predicted, reason = tuple(float(v) for v in box), "tracked"
                else:
                    reason, self.tracker = "tracker_failed", None
        agreement = iou(predicted, detection)
        if detection is not None:
            # Her gerçek AI kutusunda yeniden başlat: MOSSE ölçek kestirimi değildir.
            self.tracker = self.factory()
            ok = self.tracker.init(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), tuple(detection))
            if not ok:
                self.tracker = None
            self.last_detection_at = at
            reason = "detector_seed" if ok else "detector_seed_failed"
        self.last_id, self.last_at, self.shape = frame_id, at, bgr.shape
        return {"frame_id": frame_id, "timestamp_s": at,
                "source": "detector" if detection is not None else "tracker" if predicted else "none",
                "bbox_xywh": detection if detection is not None else predicted,
                "reason": reason, "detector_tracker_iou": agreement,
                "seconds_since_detector": None if self.last_detection_at is None else at-self.last_detection_at,
                "flight_eligible": False}


def run(manifest: Path, output: Path):
    # Var olan sonuçları/özgün veriyi değiştirme. Hatalı turda summary oluşmaz.
    if output.exists():
        raise ValueError("Sonuç klasörü zaten var; yeni klasör seçin")
    make_tracker()  # Eksik contrib, AI kutusu olmayan kayıtta da açık hata verir.
    raw = manifest.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if not rows:
        raise ValueError("Manifesto boş")
    output.mkdir(parents=True)
    probe, counts, timings = MosseProbe(), Counter(), []
    with (output / "frames.jsonl").open("x") as stream:
        for row in rows:
            path = manifest.parent / row["image"]
            data = path.read_bytes()
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError(f"Görüntü okunamadı: {path}")
            start = time.perf_counter()
            result = probe.step(row["frame_id"], row["timestamp_s"], frame, row["detector_bbox_xywh"])
            timings.append((time.perf_counter()-start)*1000)
            result["image_sha256"] = hashlib.sha256(data).hexdigest()
            counts[result["source"]] += 1
            stream.write(json.dumps(result, allow_nan=False)+"\n")
            preview = frame.copy()
            if result["bbox_xywh"] is not None:
                x, y, w, h = (round(v) for v in result["bbox_xywh"])
                cv2.rectangle(preview, (x,y), (x+w,y+h), (0,255,0) if result["source"] == "detector" else (0,165,255), 2)
            cv2.putText(preview, result["source"]+" / OFFLINE", (10,25), cv2.FONT_HERSHEY_SIMPLEX, .6, (0,0,255), 2)
            if not cv2.imwrite(str(output / f"{row['frame_id']:08d}.jpg"), preview):
                raise RuntimeError("Karşılaştırma görüntüsü yazılamadı")
    summary = {"frames": len(rows), "sources": dict(counts), "opencv": cv2.__version__,
               "manifest_sha256": hashlib.sha256(raw).hexdigest(),
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "max_bridge_s": probe.max_bridge_s, "max_frame_gap_s": probe.max_frame_gap_s,
               "median_processing_ms": float(np.median(timings)), "flight_eligible": False,
               "note": "Takip sayısı doğruluk değildir; gerçek hedef etiketleriyle ayrıca değerlendirilmeli."}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.manifest, args.output), indent=2, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, cv2.error) as error:
        parser.exit(1, f"HATA: {error}\n")
