"""Çevrimdışı model karşılaştırmasının NMS/kanıt kontrolleri."""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
import pytest

from safak_gorev2.model_compare import decode_predictions,count_results
from safak_gorev2.replay import ReplayError,sha256
from safak_gorev2.replay_hailo import compare_detections

ROOT=Path(__file__).resolve().parents[1]
TRANSFORM={'tensor_width':640,'tensor_height':640,'resized_width':640,'resized_height':360,'left':0,'top':140}


def test_comparison_module_import_opens_no_hardware_or_model_runtime():
    subprocess.run([sys.executable,'-c',"import sys; import safak_gorev2.model_compare; assert not ({'torch','ultralytics','hailo','picamera2','pymavlink','flask','safak_gorev2.controller'} & set(sys.modules))"],check=True,cwd=ROOT)


def test_synthetic_nms_keeps_classes_and_maps_to_original():
    pytest.importorskip('torch');pytest.importorskip('ultralytics')
    raw=np.zeros((1,6,8400),np.float32)
    raw[0,:,0]=[320,320,320,180,.9,.8]
    raw[0,:,1]=[320,320,320,180,.7,.6]
    result=decode_predictions(raw,TRANSFORM)
    assert len(result)==2
    by_class={d.class_id:d for d in result}
    assert by_class[1].label=='kirmizi_hedef' and by_class[2].label=='mavi_hedef'
    assert by_class[2].confidence==pytest.approx(.8)
    assert by_class[2].bbox==pytest.approx((.25,.25,.75,.75))


def test_empty_prediction_is_retained_as_empty_result():
    pytest.importorskip('torch');pytest.importorskip('ultralytics')
    assert decode_predictions(np.zeros((1,6,8400),np.float32),TRANSFORM)==[]

@pytest.mark.parametrize('raw',[np.zeros((1,6,6),np.float32),np.full((1,6,8400),np.nan,np.float32)])
def test_invalid_raw_shape_or_nan_rejected(raw):
    pytest.importorskip('torch');pytest.importorskip('ultralytics')
    with pytest.raises(ReplayError):decode_predictions(raw,TRANSFORM)


def test_real_pt_onnx_evidence_and_shadow_regression():
    path=ROOT/'artifacts/model-comparison/run-01'
    if not path.exists():pytest.skip('Gerçek model karşılaştırması bu checkout içinde yok')
    manifest=json.loads((path/'run-manifest.json').read_text())
    assert manifest['status']=='complete'
    for name,digest in manifest['outputs_sha256'].items():assert sha256(path/name)==digest
    rows=[json.loads(l) for l in (path/'frames.jsonl').read_text().splitlines()]
    assert len(rows)==81 and len({r['frame_id'] for r in rows})==81
    assert all(r['pt_onnx_detections']['equal'] for r in rows)
    shadow=rows[17]
    assert shadow['pt'][0]['confidence']>.5 and 'no_corners' in shadow['pt'][0]['reasons']
    assert count_results(rows,'hef')['preconditions_ok_boxes']==0
    assert count_results(rows,'pt')['preconditions_ok_boxes']==7
    target=rows[28]
    assert target['hef'][0]['confidence']<.5 <target['pt'][0]['confidence']


def test_runtime_versions_do_not_explain_difference():
    paths=[ROOT/'artifacts/model-comparison'/name/'frames.jsonl' for name in ('run-01','run-export-version')]
    if not all(p.exists() for p in paths):pytest.skip('İki sürümün gerçek karşılaştırma kaydı yok')
    rows=[[json.loads(l) for l in p.read_text().splitlines()] for p in paths]
    assert len(rows[0])==len(rows[1])==81
    for a,b in zip(*rows):
        assert a['name']==b['name'] and compare_detections(a['pt'],b['pt'],tolerance=0)['equal']
