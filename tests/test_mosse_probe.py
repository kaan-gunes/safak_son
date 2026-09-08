import json

import cv2
import numpy as np
import pytest

from scripts.mosse_probe import MosseProbe, iou, run


class FakeTracker:
    def init(self, image, box):
        self.box = box
        return True

    def update(self, image):
        return True, self.box


def test_tracking_does_not_extend_detector_deadline():
    probe = MosseProbe(factory=FakeTracker)
    image = np.zeros((100, 100, 3), np.uint8)
    probe.step(0, 0., image, (20,20,30,30))
    for i in range(1, 4):
        result = probe.step(i, i*.09, image)
        assert result["source"] == "tracker"
        assert result["flight_eligible"] is False
    result = probe.step(4, .36, image)
    assert result["reason"] == "expired" and result["bbox_xywh"] is None
    assert probe.step(5, .40, image)["source"] == "none"


def test_frame_gap_and_fresh_detection_reseed():
    probe = MosseProbe(factory=FakeTracker)
    image = np.zeros((100,100,3), np.uint8)
    probe.step(0, 0., image, (20,20,30,30))
    assert probe.step(1, .2, image)["reason"] == "frame_gap"
    assert probe.step(2, .3, image, (40,40,30,30))["source"] == "detector"


def test_no_seed_and_bad_input():
    probe = MosseProbe(factory=FakeTracker)
    image = np.zeros((100,100,3), np.uint8)
    assert probe.step(0, 0., image)["source"] == "none"
    with pytest.raises(ValueError, match="kesin artmalı"):
        probe.step(0, .1, image)
    with pytest.raises(ValueError, match="kesin artmalı"):
        probe.step(1, 0., image)
    with pytest.raises(ValueError, match="boyutu"):
        probe.step(1, .1, image[:50])
    with pytest.raises(ValueError, match="kutusu"):
        probe.step(1, .1, image, (90,90,30,30))


def test_tracker_failure_discards_old_box():
    class Failed(FakeTracker):
        def update(self, image):
            return False, self.box
    probe = MosseProbe(factory=Failed)
    image = np.zeros((100,100,3), np.uint8)
    probe.step(0, 0., image, (20,20,30,30))
    result = probe.step(1, .1, image)
    assert result["source"] == "none" and result["reason"] == "tracker_failed"


@pytest.mark.skipif(not hasattr(getattr(cv2, "legacy", None), "TrackerMOSSE_create"), reason="Ayrı MOSSE deney ortamı gerekli")
def test_real_mosse_translation_and_cli_outputs(tmp_path):
    rng = np.random.default_rng(17)
    patch = rng.integers(30, 240, (64,64,3), dtype=np.uint8)
    rows = []
    for i in range(8):
        frame = np.full((240,320,3), 25, np.uint8)
        frame[80:144, 80+i:144+i] = patch
        path = tmp_path / f"{i}.png"
        assert cv2.imwrite(str(path), frame)
        rows.append({"frame_id": i, "timestamp_s": i/30, "image": path.name,
                     "detector_bbox_xywh": [80,80,64,64] if i == 0 else None})
    manifest = tmp_path / "input.jsonl"
    manifest.write_text("".join(json.dumps(row)+"\n" for row in rows))
    summary = run(manifest, tmp_path / "result")
    results = [json.loads(line) for line in (tmp_path / "result/frames.jsonl").read_text().splitlines()]
    assert summary["sources"] == {"detector": 1, "tracker": 7}
    assert min(iou(row["bbox_xywh"], [80+i,80,64,64]) for i,row in enumerate(results)) > .8
    assert len(list((tmp_path / "result").glob("*.jpg"))) == 8
    with pytest.raises(ValueError, match="zaten var"):
        run(manifest, tmp_path / "result")
