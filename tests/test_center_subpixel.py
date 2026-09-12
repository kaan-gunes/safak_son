"""Bağımsız izdüşümle köşe gürültüsü; fiziksel saha kabulü değildir."""
from dataclasses import replace
import math

import cv2
import numpy as np
import pytest

from safak_gorev2.competition.config import Options
from safak_gorev2.competition.geometry import MountedTargetGeometry
from safak_gorev2.geometry import Calibration, order_corners, body_to_ned, TargetGeometry
from safak_gorev2.types import Detection, Frame, PoseSample


def rendered_square(side, height, yaw=.3, mount=180, plane_tilt=0., max_plane_tilt=None):
    cfg, opt = Options.load('config/ana-imx708.json')
    cal = Calibration.load(cfg.camera.calibration_file)
    camera = replace(cfg.camera, target_side_m=side,
                     **({} if max_plane_tilt is None else
                        {'max_plane_tilt_deg': max_plane_tilt}))
    angles = (.04, -.05, yaw)
    rotation = body_to_ned(*angles)
    optical = (np.array([[0., 1., 0.], [-1., 0., 0.], [0., 0., 1.]])
               if mount == 180 else np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]))
    vehicle = np.array([3., 4., -height])
    ground = np.array([3.3, 3.8, 0.])
    orientation = body_to_ned(plane_tilt, 0, .5) @ np.diag([1., -1., -1.])
    rvec, _ = cv2.Rodrigues(optical.T @ rotation.T @ orientation)
    tvec = optical.T @ (rotation.T @ (ground-vehicle)-np.array(camera.offset_body_m))
    s = side/2
    obj = np.array([[-s, s, 0.], [s, s, 0.], [s, -s, 0.], [-s, -s, 0.]])
    q, _ = cv2.projectPoints(obj, rvec, tvec, cal.matrix, cal.distortion)
    q = order_corners(q.reshape(4, 2))
    image = np.full((720, 1280, 3), 70, np.uint8)
    cv2.fillConvexPoly(image, np.round(q*16).astype(np.int32), (220, 65, 30), shift=4)
    image = cv2.GaussianBlur(image, (3, 3), .6)
    box = tuple(np.r_[q.min(0), q.max(0)]/[1280, 720, 1280, 720])
    detection = Detection('mavi_hedef', .95, box)
    frame = Frame(1, 100., 100., image, (detection,))
    pose = PoseSample(100., *angles, *vehicle)
    geometry = MountedTargetGeometry(camera, cal, mount)
    return geometry, frame, detection, q, pose, ground


@pytest.mark.parametrize('side,height', [(1., 10.), (2., 15.), (1., 15.)])
@pytest.mark.parametrize('mount', [0, 180])
def test_subpixel_recovers_noisy_corners_without_relaxing_pnp(side, height, mount):
    # Bu regresyon, alt piksel kurtarmanın eklendiği eski 15° kapıyı
    # sınar. Aktif saha kapısı 30° olduğu için aynı gürültülü örnekler
    # zaten ilk denemede kabul edilir ve "recovered" doğal olarak sıfır olur.
    geometry, frame, detection, q, pose, ground = rendered_square(
        side, height, mount=mount, max_plane_tilt=15.)
    virtual = replace(pose, roll=-pose.roll, pitch=-pose.pitch, yaw=pose.yaw+math.pi) if mount==180 else pose
    rng = np.random.default_rng(147)
    old_count = recovered = 0
    for _ in range(100):
        noisy = q+rng.normal(0, 2., q.shape)
        old = TargetGeometry.from_corners(geometry, frame, detection, noisy, virtual)
        new = geometry.from_corners(frame, detection, noisy, pose)
        old_count += old is not None
        if old is not None:
            assert new == old  # Mevcut kabul edilen ölçüm değişmez.
        elif new is not None:
            recovered += 1
            assert np.linalg.norm(np.array([new.north, new.east])-ground[:2]) < .10
            assert abs(new.camera_height_m - (height-.05)) < .5
            assert new.reprojection_px <= geometry.cfg.max_reprojection_px
    assert recovered >= 1  # Geri kazanılan kare de aynı fiziksel eşikleri geçer.


def test_steep_plane_and_clipped_corners_still_rejected():
    geometry, frame, detection, q, pose, _ = rendered_square(2., 10., plane_tilt=.6)
    assert geometry.from_corners(frame, detection, q, pose) is None
    geometry, frame, detection, q, pose, _ = rendered_square(1., 10.)
    q[:, 0] -= q[:, 0].min()
    assert geometry.from_corners(frame, detection, q, pose) is None


def test_corner_diagnostics_record_actual_measurements_and_acceptance():
    geometry, frame, _, _, pose, _ = rendered_square(1., 10.)
    diagnostics = []
    geometry.detect(frame, pose, diagnostics)
    assert diagnostics and diagnostics[0]['corner_trials']
    for trial in diagnostics[0]['corner_trials']:
        assert len(trial['raw']) == len(trial['refined']) == 4
        assert np.max(np.linalg.norm(np.array(trial['raw'])-trial['refined'], axis=1)) <= 3
