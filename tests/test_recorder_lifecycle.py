"""Gerçek yerel FFmpeg süreci; fiziksel kamera/ağ/FC gerektirmez."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import shutil
import pytest
import cv2


def test_competition_recorder_waits_for_camera(monkeypatch):
    from safak_gorev2 import record
    expected={'profile_digest':'p','camera_contract':{'identity':'imx708','backend':'picamera2'},
              'strategy':'center','actuator':'servo','sortie_id':'s'}
    replies=[dict(expected,camera_actual=None),
             dict(expected,camera_actual={'identity':'imx708','backend':'picamera2'})]
    monkeypatch.setattr(record,'get',lambda _:(json.dumps(replies.pop(0)).encode(),{}))
    actual=record.wait_recording_source(expected,'http://127.0.0.1:1',1)
    assert actual['camera_actual']['identity']=='imx708'


def executable_env(tmp_path):
    env = os.environ.copy()
    if not shutil.which('ffmpeg'):
        import imageio_ffmpeg
        (tmp_path/'ffmpeg').symlink_to(imageio_ffmpeg.get_ffmpeg_exe())
        env['PATH']=str(tmp_path)+os.pathsep+env['PATH']
    return env


def wait_frames(root, process):
    until=time.monotonic()+15
    while time.monotonic()<until:
        if process.poll() is not None:
            raise AssertionError(process.communicate())
        active=root/'active.json'
        if active.exists():
            body=json.loads(active.read_text())
            if body['video_frames'] >= 3: return Path(body['directory'])
        time.sleep(.1)
    raise AssertionError('Kayıt ilerlemedi')


@pytest.mark.parametrize('kill', [False, True])
def test_onboard_unreachable_panel_sigterm_and_partial(tmp_path,kill):
    root=tmp_path/'recordings'
    proc=subprocess.Popen([sys.executable,'-m','safak_gorev2.record','--root',str(root),
        '--panel-url','http://127.0.0.1:1'],env=executable_env(tmp_path),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out=wait_frames(root,proc)
        if kill:
            os.killpg(proc.pid,signal.SIGKILL)
        else:
            proc.send_signal(signal.SIGTERM)
        stdout,stderr=proc.communicate(timeout=15)
        manifest=json.loads((out/'manifest.json').read_text())
        if kill:
            assert manifest['status']=='recording'  # Çökmede complete yazılamaz.
            assert manifest.get('segment_integrity') != 'ffmpeg clean close'
        else:
            assert proc.returncode==0,stderr
            assert manifest['status']=='complete'
            assert manifest['status_errors']>0 and manifest['image_errors']>0
            assert manifest['segments'] and manifest['segment_integrity']=='ffmpeg clean close'
            count=0
            for video in out.glob('video-*.mkv'):
                cap=cv2.VideoCapture(str(video))
                while cap.read()[0]: count+=1
                cap.release()
            assert count==manifest['video_frames'] and count>=3
            rows=[json.loads(x) for x in (out/'video-frames.jsonl').read_text().splitlines()]
            assert len(rows)==count and all(r['error'] for r in rows)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait()


@pytest.mark.parametrize('variant',['imx708','arducam-ezbox-swift'])
def test_two_profile_recording_manifest_sigterm(tmp_path,variant):
    from dataclasses import asdict
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    import numpy as np
    from safak_gorev2.competition.config import Options
    from safak_gorev2.record import profile_manifest
    profile='config/ana-imx708.json' if variant=='imx708' else 'config/ana-arducam.json'
    cfg,o=Options.load(profile)
    base=asdict(cfg)
    if variant!='imx708':
        # Sentetik fixture kimliği; fiziksel Arducam beyanı değildir.
        base['camera'].update(identity='FIXTURE_USB',device='/dev/v4l/by-id/FIXTURE_USB',
                              usb_vid_pid='0000:0000',pixel_format='MJPG')
    base_path=tmp_path/'base.json';base_path.write_text(json.dumps(base))
    data=json.loads(Path(profile).read_text());data['base_config']=str(base_path)
    data['sortie_id']='fixture-sortie';data['mission_fingerprint']='f'*64
    selected=tmp_path/'profile.json';selected.write_text(json.dumps(data))
    metadata=profile_manifest(selected)
    contract=metadata['camera_contract']
    actual=dict(metadata,camera_actual={'identity':contract['identity'],'backend':contract['backend'],'scope':'SYNTHETIC FIXTURE'})
    _,jpg=cv2.imencode('.jpg',np.zeros((540,960,3),np.uint8))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_GET(self):
            body=(json.dumps(actual).encode() if self.path=='/api/competition' else
                  json.dumps({'ages_s':{'heartbeat':.01},'telemetry':{'armed':False}}).encode() if self.path=='/api/status' else jpg.tobytes())
            self.send_response(200);self.send_header('X-Frame-Id',str(time.monotonic_ns()))
            self.send_header('X-Frame-Age-Ms','1');self.send_header('Content-Length',str(len(body)));self.end_headers()
            self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    root=tmp_path/'recordings'
    proc=subprocess.Popen([sys.executable,'-m','safak_gorev2.record','--config',str(selected),
        '--root',str(root),'--panel-url',f'http://127.0.0.1:{server.server_port}'],
        env=executable_env(tmp_path),stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out=wait_frames(root/variant,proc)
        proc.send_signal(signal.SIGTERM);_,stderr=proc.communicate(timeout=15)
        assert proc.returncode==0,stderr
        m=json.loads((out/'manifest.json').read_text())
        assert m['status']=='complete' and m['sortie_id']=='fixture-sortie'
        assert m['camera_actual']['identity']==contract['identity']
        assert m['camera_contract']==contract and m['profile_digest']==metadata['profile_digest']
        assert m['mission_digest_actual']==m['mission_digest']=='f'*64
        assert m['status_errors']==m['image_errors']==0
    finally:
        if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        server.shutdown();server.server_close();worker.join(timeout=2)
