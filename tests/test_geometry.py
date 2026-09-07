from dataclasses import replace

import cv2
import numpy as np
import pytest

from safak_gorev2.demo import demo_calibration
from safak_gorev2.geometry import CAMERA_TO_BODY, TargetGeometry, body_to_ned, quad_candidates
from safak_gorev2.types import Detection, Frame, PoseSample


def projection(cfg, roll=0., pitch=0., yaw=0., target=(.35, -.2, 0.)):
    cal = demo_calibration()
    geometry = TargetGeometry(cfg.camera, cal)
    position = np.array([0., 0., -6.])
    r = body_to_ned(roll, pitch, yaw)
    object_to_ned = np.array([[0., 1, 0], [1, 0, 0], [0, 0, -1]])
    rv, _ = cv2.Rodrigues(CAMERA_TO_BODY.T @ r.T @ object_to_ned)
    tv = CAMERA_TO_BODY.T @ (r.T @ (np.array(target) - position) - np.array(cfg.camera.offset_body_m))
    q, _ = cv2.projectPoints(geometry.object_points, rv, tv, cal.matrix, cal.distortion)
    q = q.reshape(4, 2)
    image = np.full((720, 1280, 3), 70, np.uint8)
    cv2.fillConvexPoly(image, q.astype(np.int32), (220, 65, 30))
    bbox = tuple(np.array([*q.min(axis=0), *q.max(axis=0)]) / [1280, 720, 1280, 720])
    detection = Detection("mavi_hedef", .94, bbox, 2)
    return geometry, Frame(1, 100., 100.02, image, (detection,)), detection, q, PoseSample(100., roll, pitch, yaw, *position)


@pytest.mark.parametrize("angles", [(0,0,0), (.08,-.1,.4), (-.09,.07,2.)])
def test_metric_pose_compensates_tilt_yaw_and_camera_offset(cfg, angles):
    geometry, frame, detection, q, pose = projection(cfg, *angles)
    target = geometry.from_corners(frame, detection, q, pose)
    assert target is not None
    assert (target.north, target.east, target.ground_down) == pytest.approx((.35,-.2,0.), abs=.03)


def test_ai_roi_to_quad_to_metric_target(cfg):
    geometry, frame, detection, q, pose = projection(cfg, .04, -.06, .3)
    found = geometry.detect(frame, pose)
    assert len(found) == 1
    assert (found[0].north, found[0].east, found[0].ground_down) == pytest.approx((.35,-.2,0), abs=.08)


def test_red_or_untrusted_ai_label_is_not_blue(cfg):
    geometry, frame, detection, q, pose = projection(cfg)
    for label in ("kirmizi_hedef", "person", "unknown"):
        frame = replace(frame, detections=(replace(detection, label=label),))
        assert geometry.detect(frame, pose) == ()


def test_clipped_target_cannot_create_release_geometry(cfg):
    geometry, frame, detection, q, pose = projection(cfg)
    q[:, 0] -= q[:, 0].min()
    assert geometry.from_corners(frame, detection, q, pose) is None


def test_wrong_calibration_resolution_is_rejected(cfg):
    geometry, frame, detection, q, pose = projection(cfg)
    assert geometry.from_corners(replace(frame, image=frame.image[:640]), detection, q, pose) is None


def test_white_and_red_square_fail_secondary_blue_check(cfg):
    geometry, frame, detection, q, pose = projection(cfg)
    for color in ((230,230,230), (20,40,230)):
        image = np.full_like(frame.image, 70)
        cv2.fillConvexPoly(image, q.astype(np.int32), color)
        assert quad_candidates(image, detection, cfg.camera) == []


def test_diagnostics_preserve_target_acceptance_and_explain_rejection(cfg):
    geometry, frame, detection, q, pose = projection(cfg)
    diagnostics = []
    before = geometry.detect(frame, pose)
    assert geometry.detect(frame, pose, diagnostics) == before
    assert len(before) == 1 and diagnostics[0]['accepted']
    weak = replace(frame, detections=(replace(detection, confidence=.42),))
    diagnostics = []
    assert geometry.detect(weak, pose, diagnostics) == ()
    assert diagnostics[0]['reasons'] == ['score']
    blank = replace(frame, image=np.full_like(frame.image, 100))
    diagnostics = []
    assert geometry.detect(blank, pose, diagnostics) == ()
    assert diagnostics[0]['reasons'] == ['no_corners']
