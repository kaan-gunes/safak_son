import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
import subprocess
import sys
import cv2
import numpy as np
import pytest

from safak_gorev2.config import Config,CameraConfig
from safak_gorev2.geometry import corner_screen
from safak_gorev2.replay import ReplayError,load_dataset,sha256,diagnose,run
from safak_gorev2.replay_hailo import letterbox_rgb,unletterbox,compare_detections

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def dataset(tmp_path):
    source=tmp_path/'source';source.mkdir()
    for i in range(2):
        cv2.imwrite(str(source/f'frame-{i:03}.png'),np.zeros((72,128,3),np.uint8))
        (source/f'frame-{i:03}.json').write_text(json.dumps({'frame_id':i,'stream_id':'session',
            'camera':{'width':128,'height':72},'detections':[]}))
    def manifest():
        entries=[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha256(p)} for p in sorted(source.glob('frame-*'))]
        (source/'manifest.json').write_text(json.dumps({'files':entries}))
    manifest()
    return source,manifest,replace(CameraConfig(),width=128,height=72)


def test_empty_detections_keep_frame_identity(dataset):
    src,_,cfg=dataset
    frames,count=load_dataset(src,src/'manifest.json',cfg)
    assert count==4 and [f['meta']['frame_id'] for f in frames]==[0,1]
    assert all(f['detections']==() for f in frames)

@pytest.mark.parametrize('damage',['missing_png','missing_json','bad_png','bad_json','hash','duplicate_id','dimension','json_dimension','extra_frame','duplicate_manifest','duplicate_json_key','nan_score'])
def test_bad_source_fails_explicitly(dataset,damage):
    src,manifest,cfg=dataset
    p=src/'frame-001.json';meta=json.loads(p.read_text())
    if damage=='missing_png':(src/'frame-001.png').unlink()
    elif damage=='missing_json':p.unlink()
    elif damage=='bad_png':(src/'frame-001.png').write_bytes(b'broken');manifest()
    elif damage=='bad_json':p.write_text('{');manifest()
    elif damage=='hash':p.write_text(p.read_text()+' ')
    elif damage=='duplicate_id':meta['frame_id']=0;p.write_text(json.dumps(meta));manifest()
    elif damage=='dimension':cv2.imwrite(str(src/'frame-001.png'),np.zeros((73,128,3),np.uint8));manifest()
    elif damage=='json_dimension':meta['camera']['height']=73;p.write_text(json.dumps(meta));manifest()
    elif damage=='extra_frame':(src/'frame-999.json').write_text('{}')
    elif damage=='duplicate_manifest':
        m=json.loads((src/'manifest.json').read_text());m['files'].append(m['files'][0]);(src/'manifest.json').write_text(json.dumps(m))
    elif damage=='duplicate_json_key':p.write_text('{"frame_id":0,"frame_id":1}');manifest()
    elif damage=='nan_score':
        meta['detections']=[{'class_id':2,'label':'mavi_hedef','bbox':[0,0,1,1],'confidence':float('nan')}];p.write_text(json.dumps(meta));manifest()
    with pytest.raises(ReplayError):load_dataset(src,src/'manifest.json',cfg)


def test_color_letterbox_and_inverse_coordinates():
    im=np.zeros((720,1280,3),np.uint8)
    im[:,:640]=(0,0,255);im[:,640:]=(255,0,0)
    tensor,t=letterbox_rgb(im)
    assert tensor.shape==(640,640,3) and tensor.dtype==np.uint8
    assert np.all(tensor[:140]==114) and np.all(tensor[500:]==114)
    assert tuple(tensor[140,0])==(255,0,0)
    assert tuple(tensor[499,639])==(0,0,255)
    assert unletterbox((0,140/640,1,500/640),t)==pytest.approx((0,0,1,1))
    assert unletterbox((.25,230/640,.5,320/640),t)==pytest.approx((.25,.25,.5,.5))
    assert unletterbox((0,0,1,1),t)[1]<0 # sınır dışı kutu kırpılmaz


def test_matching_checks_class_score_missing_and_empty():
    a={'class_id':2,'bbox':[.1,.2,.4,.5],'confidence':.5097429156}
    assert compare_detections([],[])['equal']
    assert compare_detections([a],[a])['equal']
    for b in ({**a,'confidence':.9},{**a,'class_id':1},{**a,'bbox':[.2,.2,.4,.5]}):
        assert not compare_detections([a],[b])['equal']
    assert not compare_detections([a],[])['equal']


def test_border_and_occupancy_reasons_are_independent():
    q=np.array([[0.,0.],[1279.,0.],[1279.,719.],[0.,719.]])
    occupancy,reasons=corner_screen(q,1280,720,CameraConfig())
    assert set(reasons)=={'border','occupancy'}


def test_replay_import_does_not_load_flight_or_hardware():
    script="import sys; import safak_gorev2.replay; import safak_gorev2.replay_hailo; assert not ({'picamera2','pymavlink','hailo','gi','flask','safak_gorev2.controller','safak_gorev2.main'} & set(sys.modules))"
    subprocess.run([sys.executable,'-c',script],check=True,cwd=ROOT)


def field_frames():
    src=ROOT/'artifacts/field/flight-01'
    if not src.is_dir():pytest.skip('Gerçek uçuş kaydı bu checkout içinde yok')
    cfg=Config.load(ROOT/'config/quad.json')
    return load_dataset(src,src/'sha256-manifest.json',cfg.camera)[0],cfg.camera


def test_field_counts_and_shadow_clipping_regression():
    frames,cfg=field_frames()
    blue=[[d for d in f['detections'] if d.label=='mavi_hedef'] for f in frames]
    assert len(frames)==81
    assert sum(bool(ds) for ds in blue)==54
    assert sum(map(len,blue))==63
    assert sum(any(d.confidence>=.5 for d in ds) for ds in blue)==4
    by_name={f['name']:f for f in frames}
    for n,reason in [('017','no_corners'),('032','border'),('035','border'),('036','border')]:
        f=by_name['frame-'+n]
        rows=diagnose(cv2.imread(str(f['path'])),f['detections'],cfg)
        high=[r for r in rows if r['confidence']>=.5]
        assert high and all(reason in r['reasons'] and not r['preconditions_ok'] for r in high)


def test_shared_geometry_conditions_unchanged_on_field():
    frames,cfg=field_frames();accepted=0
    for f in frames:
        for d in diagnose(cv2.imread(str(f['path'])),f['detections'],cfg):
            for q in d['candidates']:
                corners=np.array(q['corners']);w,h=1280,720
                old=(corners[:,0].min()>=cfg.min_border_px and corners[:,1].min()>=cfg.min_border_px
                     and corners[:,0].max()<=w-cfg.min_border_px and corners[:,1].max()<=h-cfg.min_border_px
                     and max(np.ptp(corners[:,0])/w,np.ptp(corners[:,1])/h)<=cfg.max_frame_occupancy)
                assert old == (not q['reasons'])
            accepted+=d['geometry_ok']
    assert accepted==8


def test_field_annotations_cover_every_source_and_exclude_uncertain():
    from safak_gorev2.replay import load_annotations
    frames,cfg=field_frames()
    annotations=load_annotations(ROOT/'docs/replay/flight-01-annotations.json',frames,cfg)
    assert len(annotations)==81
    assert annotations['frame-015']['category']=='uncertain'
    assert annotations['frame-017']['false_detections'][0]['reason']=='insan gölgesi'


def test_hardware_evidence_regression_when_available():
    path=ROOT/'artifacts/replay/hailo-verified-05/frames.jsonl'
    if not path.is_file():pytest.skip('Gerçek Hailo tekrar oynatma kanıtı yok')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows)==81
    assert len({row['frame_id'] for row in rows})==81
    for row in rows:
        assert compare_detections(row['recorded'],row['replayed'])['equal']
        assert row['trace']['reference_tensor_equal']
        assert row['trace']['packed_nms_equals_direct']
        assert row['trace']['comparison']['equal']
    assert rows[17]['trace']['direct_nms'][1][0][-1]==.5097429156303406
