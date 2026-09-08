"""Aynı kayıtlı Hailo girişleriyle yerel PT/ONNX karşılaştırması; uçuş backend'i değildir."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys

import cv2
import numpy as np
from .config import Config
from .geometry import bbox_iou
from .replay import (ReplayError,sha256,read_json,load_dataset,load_annotations,
                     diagnose,draw,stack_comparison,software_manifest)
from .replay_hailo import unletterbox,letterbox_rgb,compare_detections
from .types import Detection


def load_checkpoint(path):
    """Yalnız bilinen Torch/YOLOv8 tipleri; pickle'da sınırsız kod yükleme yok."""
    import torch
    from ultralytics.nn.tasks import DetectionModel
    from ultralytics.nn.modules import Conv,Concat,C2f,Bottleneck,DFL,SPPF,Detect
    allow=[DetectionModel,Conv,Concat,C2f,Bottleneck,DFL,SPPF,Detect,set,
           torch.nn.Sequential,torch.nn.ModuleList,torch.nn.Conv2d,torch.nn.BatchNorm2d,
           torch.nn.SiLU,torch.nn.MaxPool2d,torch.nn.Upsample,torch.nn.Identity]
    with torch.serialization.safe_globals(allow):
        checkpoint=torch.load(path,map_location='cpu',weights_only=True)
    model=checkpoint.get('ema') or checkpoint['model']
    if type(model) is not DetectionModel or model.names!={0:'kirmizi_hedef',1:'mavi_hedef'}:
        raise ReplayError('Bu araç iki sınıflı ŞAFAK DetectionModel bekliyor')
    return model.float().eval(),checkpoint


def decode_predictions(raw,transform):
    import torch
    from ultralytics.utils.nms import non_max_suppression
    if raw.shape!=(1,6,8400) or not np.isfinite(raw).all():
        raise ReplayError(f'Beklenmeyen 640px YOLOv8 çıktısı: {raw.shape}')
    result=non_max_suppression(torch.from_numpy(raw.copy()),conf_thres=.25,iou_thres=.7,
                              nc=2,multi_label=True,max_det=200,max_time_img=10)[0].numpy()
    counts=Counter();detections=[]
    for x1,y1,x2,y2,score,cls in result:
        c=int(cls)
        if c not in (0,1) or not 0<=score<=1:raise ReplayError('Geçersiz NMS sınıf/skor')
        if counts[c]>=100:continue
        counts[c]+=1
        box=unletterbox(tuple(float(v)/640 for v in (x1,y1,x2,y2)),transform)
        detections.append(Detection(['kirmizi_hedef','mavi_hedef'][c],float(score),box,c+1))
    return detections


def count_results(rows,key):
    blue=[d for row in rows for d in row[key] if d['label']=='mavi_hedef']
    return {'blue_frames':sum(any(d['label']=='mavi_hedef' for d in row[key]) for row in rows),
        'blue_boxes':len(blue),'blue_score_ge_050_frames':sum(any(d['label']=='mavi_hedef' and d['confidence']>=.5 for d in row[key]) for row in rows),
        'preconditions_ok_boxes':sum(d['preconditions_ok'] for d in blue),
        'geometry_ok_boxes':sum(d['geometry_ok'] for d in blue),
        'blue_score_min':min((d['confidence'] for d in blue),default=None),
        'blue_score_max':max((d['confidence'] for d in blue),default=None),
        'blue_score_median':float(np.median([d['confidence'] for d in blue])) if blue else None}


def run(args):
    cfg=Config.load(args.config);cfg.verify_model()
    source=Path(args.source).resolve();hef_result=Path(args.hailo_results).resolve()
    frames,source_count=load_dataset(source,source/'sha256-manifest.json',cfg.camera)
    annotations=load_annotations(args.annotations,frames,cfg.camera)
    hm=read_json(hef_result/'run-manifest.json')
    if hm['status']!='complete' or hm['model_sha256']!=cfg.hef_sha256:
        raise ReplayError('Tamamlanmış, aynı HEF ile alınmış sonuç gerekiyor')
    for name,h in hm['outputs_sha256'].items():
        p=hef_result/name
        if not p.resolve().is_relative_to(hef_result) or sha256(p)!=h:
            raise ReplayError('Hailo sonuç hash uyuşmazlığı: '+name)
    hef_rows=[json.loads(l) for l in (hef_result/'frames.jsonl').read_text().splitlines()]
    by_name={r['name']:r for r in hef_rows}
    if len(by_name)!=len(hef_rows) or set(by_name)!={f['name'] for f in frames}:
        raise ReplayError('Hailo ve kaynak kareler birebir eşleşmiyor')
    out=Path(args.output).resolve()
    if out==source or source in out.parents or out==hef_result or hef_result in out.parents:
        raise ReplayError('Yeni sonuç kaynak klasörlerinden ayrı olmalı')
    out.mkdir(parents=True,exist_ok=False)
    os.environ['YOLO_CONFIG_DIR']=str(out/'yolo-settings')
    os.environ['YOLO_AUTOINSTALL']='false'
    import torch,ultralytics,onnx,onnxruntime as ort
    from ultralytics import settings
    settings.update({'sync':False})
    torch.set_num_threads(4)
    manifest={'schema':1,'status':'running','created_utc':datetime.now(timezone.utc).isoformat(),
        'checkpoint_sha256':sha256(args.checkpoint),'hef_sha256':cfg.hef_sha256,
        'source_manifest_sha256':sha256(source/'sha256-manifest.json'),
        'hailo_run_manifest_sha256':sha256(hef_result/'run-manifest.json'),
        'verified_source_files':source_count,'frames_expected':len(frames),'config':asdict(cfg),
        'software':{**software_manifest(),'torch':torch.__version__,'ultralytics':ultralytics.__version__,
                    'onnx':onnx.__version__,'onnxruntime':ort.__version__},
        'scope':'Salt okunur kayıt incelemesi. Yeni ONNX bu checkpointten üretilmiştir; mevcut HEF için kullanılan özgün ONNX olduğu kanıtlanmamıştır.'}
    def save_manifest():
        (out/'run-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    save_manifest()
    try:
        model,checkpoint=load_checkpoint(args.checkpoint)
        (out/'checkpoint-info.json').write_text(json.dumps({k:checkpoint.get(k) for k in
            ['date','version','epoch','best_fitness','train_args','train_metrics','train_results','git']},ensure_ascii=False,indent=2,default=str))
        manifest['model']={'names':model.names,'parameters':sum(p.numel() for p in model.parameters()),
            'architecture':type(model).__name__,'head':type(model.model[-1]).__name__,
            'checkpoint_version':checkpoint.get('version'),'checkpoint_date':checkpoint.get('date')}
        class RawModel(torch.nn.Module):
            def __init__(self,inner):super().__init__();self.inner=inner
            def forward(self,x):return self.inner(x)[0]
        export_model=RawModel(deepcopy(model)).eval()
        dummy=torch.zeros(1,3,640,640)
        with torch.inference_mode():export_model(dummy)
        onnx_path=out/'checkpoint-derived-fp32.onnx'
        torch.onnx.export(export_model,dummy,str(onnx_path),opset_version=17,
            input_names=['images'],output_names=['predictions'],dynamic_axes=None,dynamo=False)
        onnx.checker.check_model(onnx.load(str(onnx_path)))
        manifest['derived_onnx_sha256']=sha256(onnx_path)
        opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
        session=ort.InferenceSession(str(onnx_path),sess_options=opts,providers=['CPUExecutionProvider'])
        if session.get_inputs()[0].shape!=[1,3,640,640]:raise ReplayError('ONNX giriş boyutu uyuşmuyor')
        (out/'raw').mkdir();(out/'images').mkdir()
        rows=[]
        with (out/'frames.jsonl').open('w') as fp:
            for f in frames:
                name=f['name'];hrow=by_name[name]
                if hrow['png_sha256']!=sha256(f['path']) or hrow['frame_id']!=f['meta']['frame_id']:
                    raise ReplayError('Hailo fotoğraf/kimlik uyuşmazlığı')
                tensor=np.load(hef_result/'tensors'/f'{name}-input.npy',allow_pickle=False)
                image=cv2.imread(str(f['path']));reference,transform=letterbox_rgb(image)
                if not np.array_equal(tensor,reference):raise ReplayError('Kaynak ile Hailo giriş tensörü farklı')
                x=np.ascontiguousarray(tensor.transpose(2,0,1)[None],dtype=np.float32)/np.float32(255.)
                with torch.inference_mode():
                    prediction,head=model(torch.from_numpy(x))
                    pt=prediction.numpy().copy()
                ort_raw=session.run(None,{'images':x})[0]
                np.savez_compressed(out/'raw'/f'{name}.npz',pt=pt,onnx=ort_raw,
                                    checkpoint_class_logits=head['scores'].numpy())
                ds_pt=decode_predictions(pt,transform);ds_ort=decode_predictions(ort_raw,transform)
                row={'name':name,'frame_id':f['meta']['frame_id'],'png_sha256':sha256(f['path']),
                    'hailo_input_sha256':sha256(hef_result/'tensors'/f'{name}-input.npy'),
                    'annotation':annotations.get(name),'hef':hrow['replayed'],
                    'pt':diagnose(image,ds_pt,cfg.camera),'onnx':diagnose(image,ds_ort,cfg.camera),
                    'raw_pt_onnx_coordinate_max_abs':float(np.max(np.abs(pt[:,:4]-ort_raw[:,:4]))),
                    'raw_pt_onnx_score_max_abs':float(np.max(np.abs(pt[:,4:]-ort_raw[:,4:]))),
                    'pt_onnx_detections':compare_detections([asdict(d) for d in ds_pt],[asdict(d) for d in ds_ort],tolerance=2e-5),
                    'pt_raw_blue_score_max':float(pt[:,5].max()),
                    'pt_blue_logit_max':float(head['scores'][:,1].max())}
                if row['annotation'] and row['annotation']['category']!='uncertain':
                    gt=[tuple(np.asarray(b)/[cfg.camera.width,cfg.camera.height,cfg.camera.width,cfg.camera.height]) for b in row['annotation']['target_boxes_px']]
                    row['visible_target_matches']={key:[{'confidence':d['confidence'],'iou':max((bbox_iou(d['bbox'],b) for b in gt),default=0),
                         'preconditions_ok':d['preconditions_ok']} for d in row[key] if d['label']=='mavi_hedef' and any(bbox_iou(d['bbox'],b)>=.5 for b in gt)] for key in ('hef','pt','onnx')}
                left=draw(image,row['hef'],name+' / HEF',row['annotation'])
                right=draw(image,row['pt'],'Ayni giris / PT FP32',row['annotation'])
                if not cv2.imwrite(str(out/'images'/f'{name}.jpg'),stack_comparison(left,right)):raise ReplayError('Görsel yazılamadı')
                fp.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');fp.flush();rows.append(row)
                if len(rows)%10==0:print(f'{len(rows)}/{len(frames)} kare karşılaştırıldı',flush=True)
        summary={'frames':len(rows),'hef':count_results(rows,'hef'),'pt':count_results(rows,'pt'),'onnx':count_results(rows,'onnx'),
            'pt_onnx_detections_equal_frames':sum(r['pt_onnx_detections']['equal'] for r in rows),
            'pt_onnx_raw_coordinate_max_abs':max(r['raw_pt_onnx_coordinate_max_abs'] for r in rows),
            'pt_onnx_raw_score_max_abs':max(r['raw_pt_onnx_score_max_abs'] for r in rows),
            'full_target_frames':{key:sum(bool(r.get('visible_target_matches',{}).get(key)) for r in rows if r['annotation'] and r['annotation']['category']=='full') for key in ('hef','pt','onnx')},
            'full_target_ge_050_frames':{key:sum(any(d['confidence']>=.5 for d in r.get('visible_target_matches',{}).get(key,[])) for r in rows if r['annotation'] and r['annotation']['category']=='full') for key in ('hef','pt','onnx')},
            'scope':manifest['scope']}
        (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        manifest['status']='complete';manifest['frames_completed']=len(rows)
        manifest['outputs_sha256']={str(p.relative_to(out)):sha256(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='run-manifest.json'}
        save_manifest();return summary
    except Exception as e:
        manifest['status']='failed';manifest['error']=str(e);save_manifest();raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True);p.add_argument('--hailo-results',required=True)
    p.add_argument('--checkpoint',required=True);p.add_argument('--annotations',required=True)
    p.add_argument('--output',required=True);p.add_argument('--config',default='config/quad.json')
    try:print(json.dumps(run(p.parse_args()),ensure_ascii=False,indent=2))
    except Exception as e:p.exit(2,f'Model karşılaştırma hatası: {e}\n')

if __name__=='__main__':main()
