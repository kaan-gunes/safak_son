"""İki görev için montaj uyarlaması; eski geometri ve ham görüntü korunur."""

from dataclasses import replace
import math

from ..geometry import TargetGeometry


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

    def from_corners(self, frame, detection, corners, pose):
        if self.reversed_mount:
            # R(roll,pitch,yaw) @ Rz(pi) = R(-roll,-pitch,yaw+pi).
            # Ofset de aynı sanal gövdeye çevrilir; NED konumu değişmez.
            # Sadece yaw eklemek eğimli araçta hatalı olur.
            pose = replace(pose, roll=-pose.roll, pitch=-pose.pitch, yaw=pose.yaw+math.pi)
        return super().from_corners(frame, detection, corners, pose)
