from dataclasses import replace

import cv2
import numpy as np
import pytest

from safak_gorev2.competition.config import Options, SIDES
from safak_gorev2.competition.vision import DualVision
from safak_gorev2.demo import demo_calibration
from safak_gorev2.geometry import body_to_ned
from safak_gorev2.types import Detection, Frame, PoseSample


@pytest.mark.parametrize('mount', [0, 180])
@pytest.mark.parametrize('color', ['mavi', 'kirmizi'])
@pytest.mark.parametrize('angles', [(0., 0., 0.), (.08, -.1, .4), (-.09, .07, 2.)])
def test_mounted_camera_recovers_ground_position(cfg, mount, color, angles):
    cfg = replace(cfg, camera=replace(cfg.camera, offset_body_m=(.11, 0., .05)))
    cal = demo_calibration()
    # Bağımsız fiziksel izdüşüm: ters montajda görüntü sağı gövde solu,
    # görüntü aşağısı gövde ilerisi; optik eksen her iki durumda aşağı.
    optical_to_body = (np.array([[0., 1., 0.], [-1., 0., 0.], [0., 0., 1.]])
                       if mount == 180 else np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]))
    r = body_to_ned(*angles)
    vehicle = np.array([1., 2., -9.])
    ground = np.array([1.45, 1.65, 0.])
    object_to_ned = np.array([[0., 1., 0.], [1., 0., 0.], [0., 0., -1.]])
    rv, _ = cv2.Rodrigues(optical_to_body.T @ r.T @ object_to_ned)
    tv = optical_to_body.T @ (r.T @ (ground-vehicle)-np.array(cfg.camera.offset_body_m))
    s = SIDES[color]/2
    points = np.array([[-s,s,0.], [s,s,0.], [s,-s,0.], [-s,-s,0.]])
    q, _ = cv2.projectPoints(points, rv, tv, cal.matrix, cal.distortion)
    q = q.reshape(4,2)
    image = np.full((720,1280,3), 70, np.uint8)
    cv2.fillConvexPoly(image, q.astype(np.int32), (220,65,30) if color=='mavi' else (30,65,220))
    box = tuple(np.r_[q.min(axis=0), q.max(axis=0)]/[1280,720,1280,720])
    frame = Frame(1,100.,100.02,image,(Detection(color+'_hedef',.94,box,2),))
    pose = PoseSample(100.,*angles,*vehicle)
    vision = DualVision(cfg, cal, mount)
    candidates, _ = vision.detect(frame,pose,'center')
    assert len(candidates)==1 and candidates[0].metric is not None
    target = candidates[0].metric
    assert (target.north,target.east,target.ground_down)==pytest.approx(ground,abs=.09)
    assert target.camera_height_m == pytest.approx(-(vehicle+r@np.array(cfg.camera.offset_body_m))[2],abs=.09)
    # Hızlı görevde montajdan bağımsız, ham AI kutusu korunur; metrik hedef yok.
    quick, _ = vision.detect(frame,pose,'quick')
    assert quick[0].bbox==box and quick[0].metric is None


@pytest.mark.parametrize('task', ['ana', 'hizli'])
def test_active_profiles_use_reported_mount(task):
    cfg, options = Options.load(f'config/{task}-gorev.json')
    assert tuple(cfg.camera.offset_body_m)==(.11,0.,.05)
    assert options.camera_mount_yaw_deg==180


@pytest.mark.parametrize('value', [90, -180, None, True, '180'])
def test_unsupported_mount_is_rejected(value):
    with pytest.raises(ValueError,match='kamera montajı'):
        replace(Options(),camera_mount_yaw_deg=value).validate()
