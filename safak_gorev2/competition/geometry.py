"""İki görev için montaj uyarlaması; eski geometri ve ham görüntü korunur."""

from dataclasses import replace
import math
import cv2
import numpy as np

from ..geometry import TargetGeometry, order_corners


class MountedTargetGeometry(TargetGeometry):
    def __init__(self, cfg, calibration, mount_yaw_deg=0):
        if type(mount_yaw_deg) is not int or mount_yaw_deg not in (0, 180):
            raise ValueError('Yere bakan kamera montajı 0 veya 180 derece olmalı')
        self.reversed_mount = mount_yaw_deg == 180
        if self.reversed_mount and cfg.offset_body_m is not None:
            forward, right, down = cfg.offset_body_m
            # Sanal gövde ileri/sağ eksenleri gerçek gövdenin tersidir.
            cfg = replace(cfg, offset_body_m=(-forward, -right, down))
        super().__init__(cfg, calibration)
        self.trials = []

    def refine_corners(self, image, corners):
        """Gerçek renk kenarında alt piksel ölçümü; kutudan köşe uydurulmaz."""
        q = order_corners(corners)
        if not np.isfinite(q).all():
            return q
        h, w = image.shape[:2]
        if q.min() < 7 or (q[:, 0] > w-7).any() or (q[:, 1] > h-7).any():
            return q
        # Küçük ROI: 50 FPS'de tam görüntüyü float'a çevirmeye gerek yok.
        left, top = np.floor(q.min(axis=0)-7).astype(int)
        right, bottom = np.ceil(q.max(axis=0)+8).astype(int)
        roi = image[top:bottom, left:right].astype(np.float32)
        blue, green, red = cv2.split(roi)
        contrast = np.uint8(np.clip(blue-np.maximum(green, red), 0, 255))
        refined = np.float32(q-[left, top]).reshape(4, 1, 2)
        cv2.cornerSubPix(contrast, refined, (4, 4), (-1, -1),
                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 20, .01))
        refined = refined.reshape(4, 2).astype(np.float64)+[left, top]
        # Başka kenara kayan ölçüm kabul edilmez. Sonrasında eski PnP'nin
        # sınır, düzlem eğimi, reprojeksiyon ve belirsizlik kontrolleri uygulanır.
        if not np.isfinite(refined).all() or np.linalg.norm(refined-q, axis=1).max() > 3:
            return q
        return refined

    def detect(self, frame, pose, diagnostics=None):
        self.trials = []
        result = super().detect(frame, pose, diagnostics)
        if diagnostics is not None:
            for detail in diagnostics:
                detail['corner_trials'] = [trial for trial in self.trials
                    if trial['bbox'] == frame.detections[detail['index']].bbox]
        return result

    def from_corners(self, frame, detection, corners, pose):
        if self.reversed_mount:
            # R(roll,pitch,yaw) @ Rz(pi) = R(-roll,-pitch,yaw+pi).
            # Ofset de aynı sanal gövdeye çevrilir; NED konumu değişmez.
            # Sadece yaw eklemek eğimli araçta hatalı olur.
            pose = replace(pose, roll=-pose.roll, pitch=-pose.pitch, yaw=pose.yaw+math.pi)
        refined = self.refine_corners(frame.image, corners)
        target = super().from_corners(frame, detection, corners, pose)
        method = 'contour'
        if target is None:
            target = super().from_corners(frame, detection, refined, pose)
            method = 'subpixel'
        self.trials.append({'bbox': detection.bbox, 'raw': np.asarray(corners).tolist(),
                            'refined': refined.tolist(), 'method': method,
                            'accepted': target is not None})
        return target
