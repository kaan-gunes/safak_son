import subprocess
import sys
import cv2
import numpy as np
from safak_gorev2.record import overlay


def test_recorder_import_has_no_flight_or_camera_connection():
    subprocess.run([sys.executable,'-c',"import sys; import safak_gorev2.record; assert not ({'pymavlink','picamera2','hailo','safak_gorev2.controller','safak_gorev2.runtime'} & set(sys.modules))"],check=True)


def test_missing_image_and_telemetry_still_yields_explicit_stale_video_frame():
    data=overlay(None,{},status_age=float('inf'),image_age=float('inf'),wall_time=1,error='Panel unreachable')
    im=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
    assert im.shape==(700,960,3)
    assert im[550:700].max()>0
    assert im[:530].max()==0


def test_overlay_keeps_original_panel_camera_and_telemetry_strip():
    camera=np.full((540,960,3),(200,80,20),np.uint8)
    _,jpg=cv2.imencode('.jpg',camera)
    status={'mode':'observe','telemetry':{'armed':False,'mode':'LOITER'},'vision':{'detections':[],'targets':[]}}
    data=overlay(jpg.tobytes(),status,status_age=.1,image_age=.1,wall_time=1)
    im=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
    assert np.abs(im[100,100].astype(float)-camera[100,100]).max()<5
    assert im[550:700].max()>0
