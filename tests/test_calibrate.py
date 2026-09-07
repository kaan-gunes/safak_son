import json

import cv2
import numpy as np
import pytest

from safak_gorev2.calibrate import solve


def synthetic_observations(folder, monkeypatch, corrupt=False):
    """Bilinen kameranın farklı pozlardaki köşeleri; çözüm gerçek OpenCV'de çalışır."""
    matrix = np.array([[850., 0., 640.], [0., 840., 360.], [0., 0., 1.]])
    grid = np.zeros((54, 3), np.float32)
    grid[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2) * .025
    center = np.array([.1, .0625, 0.])
    observations = []
    for index in range(24):
        col, row = index % 6, index // 6
        rotation = np.array([-.3 + row * .2, -.25 + col * .1, .04 * row])
        depth = .65 + .03 * ((col + row) % 3)
        translation = np.array([(320 + col * 125 - 640) * depth / 850,
                                (180 + row * 110 - 360) * depth / 840, depth])
        translation -= cv2.Rodrigues(rotation)[0] @ center
        points, _ = cv2.projectPoints(grid, rotation, translation, matrix, np.zeros(5))
        if corrupt and index == 8:
            points[27, 0] += [20., -15.]
        observations.append(points)
        (folder / f"frame-{index:03d}.png").write_bytes(b"detector input stub")
    (folder / "camera.json").write_text(json.dumps({
        "width": 1280, "height": 720, "model": "synthetic",
        "scaler_crop": [0, 0, 1280, 720]}))
    iterator = iter(observations)
    monkeypatch.setattr(cv2, "imread", lambda *args: np.zeros((720, 1280), np.uint8))
    monkeypatch.setattr(cv2, "findChessboardCornersSB", lambda *args: (True, next(iterator)))
    return matrix


def test_calibration_recovers_known_intrinsics_without_claiming_physical_validation(tmp_path, monkeypatch):
    matrix = synthetic_observations(tmp_path, monkeypatch)
    output = tmp_path / "camera.json.result"
    solve(tmp_path, 9, 6, 25., output)
    result = json.loads(output.read_text())
    assert np.asarray(result["camera_matrix"]) == pytest.approx(matrix, abs=.1)
    assert result["physical_distance_verified"] is False


def test_one_bad_view_cannot_hide_in_low_global_rms(tmp_path, monkeypatch):
    synthetic_observations(tmp_path, monkeypatch, corrupt=True)
    output = tmp_path / "camera.json.result"
    with pytest.raises(ValueError, match="Tek görüntü RMS sınırı"):
        solve(tmp_path, 9, 6, 25., output)
    assert not output.exists()
