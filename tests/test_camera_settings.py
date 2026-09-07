import json
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

from safak_gorev2.config import Config
from safak_gorev2.hailo_backend import create_picamera


def test_fixed_focus_zero_is_valid_but_negative_is_rejected():
    cfg = Config()
    replace(cfg, camera=replace(cfg.camera, lens_position=0., sensor_output_size=(2304, 1296))).validate()
    with pytest.raises(ValueError, match="lens_position"):
        replace(cfg, camera=replace(cfg.camera, lens_position=-1.)).validate()


def test_calibrated_camera_rejects_different_focus_before_configuration(tmp_path, monkeypatch):
    class Camera:
        camera_controls = {"LensPosition": (0., 32., 1.)}
        closed = False

        def close(self):
            self.closed = True

        def configure(self, *args):
            pytest.fail("Uyumsuz odakla kamera yapılandırılmamalı")

    camera = Camera()
    monkeypatch.setitem(sys.modules, "picamera2", SimpleNamespace(Picamera2=lambda: camera))
    monkeypatch.setitem(sys.modules, "libcamera", SimpleNamespace(
        Transform=None, controls=SimpleNamespace(AfModeEnum=SimpleNamespace(Manual=0))))
    path = tmp_path / "camera.json"
    path.write_text(json.dumps({"lens_position": .1, "sensor_output_size": [2304, 1296]}))
    cfg = Config()
    cfg = replace(cfg, camera=replace(cfg.camera, calibration_file=str(path),
        sensor_output_size=(2304, 1296), lens_position=.2))
    with pytest.raises(ValueError, match="odak/sensör"):
        create_picamera(cfg)
    assert camera.closed


def test_sensor_mode_requires_two_positive_integers():
    cfg = Config()
    with pytest.raises(ValueError, match="sensor_output_size"):
        replace(cfg, camera=replace(cfg.camera, sensor_output_size=(2304, 0))).validate()
