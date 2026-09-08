"""Kayıtlı PNG/JSON incelemesi. Kamera, MAVLink, denetleyici veya panel açmaz."""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

import cv2
import numpy as np
from .config import Config
from .geometry import quad_candidates, corner_screen
from .types import Detection


class ReplayError(ValueError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ReplayError(f'Yinelenen JSON anahtarı: {k}')
            d[k] = v
        return d
    try:
        return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ReplayError(f'Sonlu olmayan JSON: {x}')))
    except (OSError, ValueError) as e:
        raise ReplayError(f'JSON okunamadı: {path}: {e}') from e


def load_dataset(source, manifest, camera):
    source = Path(source).resolve()
    m = read_json(manifest)
    names = set()
    for entry in m['files']:
        name = entry['name']
        p = source / name
        if name in names or Path(name).name != name:
            raise ReplayError(f'Yinelenen/güvensiz manifesto yolu: {name}')
        names.add(name)
        if not p.is_file():
            raise ReplayError(f'Eksik kaynak dosya: {name}')
        if p.stat().st_size != entry['bytes'] or sha256(p) != entry['sha256']:
            raise ReplayError(f'Kaynak hash/boyut uyuşmazlığı: {name}')
    pngs = sorted(n for n in names if n.startswith('frame-') and n.endswith('.png'))
    if not pngs:
        raise ReplayError('Manifestoda PNG karesi yok')
    actual = {p.name for p in source.glob('frame-*') if p.suffix in ('.png', '.json')}
    expected = set(pngs) | {str(Path(n).with_suffix('.json')) for n in pngs}
    if not expected <= names or actual != expected:
        raise ReplayError('PNG/JSON çifti eksik veya manifestoda olmayan kare mevcut')
    frames, ids, stream = [], set(), None
    for name in pngs:
        p = source / name
        im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
        if im is None or im.dtype != np.uint8 or im.shape != (camera.height, camera.width, 3):
            raise ReplayError(f'Bozuk PNG veya uyumsuz görüntü boyutu/tipi: {name}')
        meta = read_json(p.with_suffix('.json'))
        try:
            identity = (meta['stream_id'], meta['frame_id'])
            if type(identity[1]) is not int or not isinstance(identity[0], str):
                raise ReplayError(f'Geçersiz kare kimliği: {name}')
            if identity in ids:
                raise ReplayError(f'Yinelenen kare kimliği: {identity}')
            ids.add(identity)
            c = meta['camera']
            if (c['width'], c['height']) != (camera.width, camera.height):
                raise ReplayError(f'JSON görüntü boyutu uyuşmuyor: {name}')
            descriptor = (meta['stream_id'], c)
            if stream is not None and stream != descriptor:
                raise ReplayError(f'Kamera/oturum değişimi: {name}')
            stream = descriptor
            ds = []
            for d in meta['detections']:
                det = Detection(d['label'], float(d['confidence']), tuple(d['bbox']), d['class_id'])
                if (len(det.bbox) != 4 or not all(math.isfinite(v) for v in det.bbox)
                    or not 0 <= det.confidence <= 1 or not math.isfinite(det.confidence)
                    or det.bbox[2] <= det.bbox[0] or det.bbox[3] <= det.bbox[1]
                    or {1:'kirmizi_hedef',2:'mavi_hedef'}.get(det.class_id) != det.label):
                    raise ReplayError(f'Geçersiz tespit: {name}')
                # Letterbox dönüşümü nedeniyle sınır dışı normalize kutular geçerlidir; kırpılmaz.
                ds.append(det)
        except (KeyError, TypeError, ValueError) as e:
            raise ReplayError(f'Bozuk tespit JSON: {name}: {e}') from e
        frames.append({'name':p.stem, 'path':p, 'meta':meta, 'detections':tuple(ds)})
    return frames, len(names)


def diagnose(image, detections, camera):
    rows = []
    h,w = image.shape[:2]
    for index, d in enumerate(detections):
        reasons = []
        if d.label != camera.blue_label:
            reasons.append('class')
        if not math.isfinite(d.confidence) or d.confidence < camera.confidence_min:
            reasons.append('score')
        qs = quad_candidates(image, d, camera) if d.label == camera.blue_label else []
        candidates = []
        for q in qs:
            occupancy, rejected = corner_screen(q,w,h,camera)
            candidates.append({'corners':q.tolist(),'occupancy':occupancy,'reasons':list(rejected)})
        geometry_ok = any(not q['reasons'] for q in candidates)
        if d.label == camera.blue_label:
            if not qs:
                reasons.append('no_corners')
            elif not geometry_ok:
                reasons.extend(sorted({r for q in candidates for r in q['reasons']}))
        rows.append({'index':index, **asdict(d), 'candidates':candidates,
                     'reasons':reasons, 'geometry_ok':geometry_ok,
                     'preconditions_ok':not reasons and geometry_ok})
    return rows


def load_annotations(path, frames, camera):
    if not path:
        return {}
    data = read_json(path)
    rows = data['frames']
    by_name = {}
    for row in rows:
        name = row['name']
        if name in by_name or row['category'] not in ('full','clipped','absent','uncertain'):
            raise ReplayError(f'Yinelenen/geçersiz görsel etiket: {name}')
        for box in row['target_boxes_px']:
            x1,y1,x2,y2 = box
            if not (0 <= x1 < x2 <= camera.width and 0 <= y1 < y2 <= camera.height):
                raise ReplayError(f'Geçersiz görsel kutu: {name}')
        by_name[name] = row
    if set(by_name) != {f['name'] for f in frames}:
        raise ReplayError('Görsel etiketler tüm karelerle birebir eşleşmiyor')
    for f in frames:
        if by_name[f['name']]['png_sha256'] != sha256(f['path']):
            raise ReplayError(f'Görsel etiket kaynak hash uyuşmazlığı: {f["name"]}')
    return by_name


def draw(image, rows, title, annotation=None):
    im = image.copy(); h,w = im.shape[:2]
    if annotation:
        for b in annotation['target_boxes_px']:
            x1,y1,x2,y2 = map(int,b)
            cv2.rectangle(im,(x1,y1),(x2,y2),(255,255,0),2)
    for row in rows:
        x1,y1,x2,y2 = np.rint(np.array(row['bbox'])*[w,h,w,h]).astype(int)
        color = (0,190,0) if row['preconditions_ok'] else (0,140,255)
        cv2.rectangle(im,(x1,y1),(x2,y2),color,2)
        for q in row['candidates']:
            cv2.polylines(im,[np.rint(q['corners']).astype(np.int32)],True,(255,0,255),2)
    # Başlık görüntü dışındadır; kadraj sınırındaki hedef/köşeleri örtmez.
    im=cv2.copyMakeBorder(im,34,26*max(1,len(rows)),0,0,cv2.BORDER_CONSTANT,value=(20,20,20))
    cv2.putText(im,title,(8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1)
    for index,row in enumerate(rows):
        text=f'{row["index"]}: {row["label"]}  {row["confidence"]:.7f}  '+(', '.join(row['reasons']) or 'on kosullar uygun')
        cv2.putText(im,text,(8,h+54+index*26),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,180,255),1)
    return im


def stack_comparison(left, right):
    height=max(left.shape[0],right.shape[0])
    images=[cv2.copyMakeBorder(im,0,height-im.shape[0],0,0,cv2.BORDER_CONSTANT,value=(20,20,20))
            for im in (left,right)]
    return np.hstack(images)


def software_manifest():
    root=Path(__file__).resolve().parent
    git = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True)
    return {'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,
            'opencv':cv2.__version__,'git_head':git.stdout.strip() or 'UNBORN',
            'source_sha256':{p.name:sha256(p) for p in sorted(root.glob('*.py'))}}


def summarize(rows, threshold):
    ds=[d for r in rows for d in r['recorded'] if d['label']=='mavi_hedef']
    return {'frames':len(rows),'blue_frames':sum(any(d['label']=='mavi_hedef' for d in r['recorded']) for r in rows),
            'blue_boxes':len(ds),'threshold':threshold,
            'above_threshold_frames':sum(any(d['label']=='mavi_hedef' and d['confidence']>=threshold for d in r['recorded']) for r in rows),
            'geometry_ok_boxes':sum(d['geometry_ok'] for d in ds),
            'preconditions_ok_boxes':sum(d['preconditions_ok'] for d in ds),
            'score_histogram':dict(sorted(Counter(str(d['confidence']) for d in ds).items())),
            'rejection_counts':dict(Counter(r for d in ds for r in d['reasons'])),
            'visual_categories':dict(Counter(r['annotation']['category'] for r in rows if r['annotation'])),
            'scope':'Seyrek kayıt ön koşulları; görev kilidi, PnP, mesafe veya saha geneli başarımı değildir.'}


def run(args):
    cfg = Config.load(args.config)
    cfg.verify_model()
    source=Path(args.source).resolve(); manifest=Path(args.manifest or source/'sha256-manifest.json')
    frames,count=load_dataset(source,manifest,cfg.camera)
    annotations=load_annotations(args.annotations,frames,cfg.camera)
    out=Path(args.output).resolve()
    if out==source or source in out.parents:
        raise ReplayError('Çıktı kaynak kayıt klasörünün dışında olmalı')
    out.mkdir(parents=True,exist_ok=False)
    info={'schema':1,'status':'running','backend':args.backend,'created_utc':datetime.now(timezone.utc).isoformat(),
          'source':str(source),'manifest_sha256':sha256(manifest),'verified_source_files':count,
          'config':asdict(cfg),'model_sha256':sha256(cfg.hef_file),'labels_sha256':sha256(cfg.labels_file),
          'annotations_sha256':sha256(args.annotations) if args.annotations else None,
          'software':software_manifest(),'frames_expected':len(frames)}
    def save_manifest():
        (out/'run-manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
    save_manifest()
    try:
        inference={}
        if args.backend=='hailo':
            from .replay_hailo import replay_hailo
            inference,info['hailo']=replay_hailo(frames,cfg,out,args.hailo_env)
            if set(inference)!={f['name'] for f in frames}:
                raise ReplayError('Hailo giriş/çıkış kare eşleşmesi eksik')
        (out/'images').mkdir()
        results=[]
        with (out/'frames.jsonl').open('w') as fp:
            for f in frames:
                im=cv2.imread(str(f['path']))
                old=diagnose(im,f['detections'],cfg.camera)
                row={'name':f['name'],'frame_id':f['meta']['frame_id'],'stream_id':f['meta']['stream_id'],
                     'png_sha256':sha256(f['path']),'recorded':old,'annotation':annotations.get(f['name'])}
                left=draw(im,old,f'{f["name"]} recorded',row['annotation'])
                if inference:
                    trace=inference[f['name']]
                    new=diagnose(im,[Detection(**d) for d in trace['application']],cfg.camera)
                    row['replayed']=new;row['trace']=trace
                    from .replay_hailo import compare_detections
                    row['recorded_comparison']=compare_detections(old,new)
                    right=draw(im,new,'TAPPAS replay',row['annotation'])
                else:
                    right=draw(im,old,'Ayni kayit / ayrintili ret nedenleri',row['annotation'])
                cv2.imwrite(str(out/'images'/f'{f["name"]}.jpg'),stack_comparison(left,right))
                fp.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');results.append(row)
        summary=summarize(results,cfg.camera.confidence_min)
        if inference:
            summary['replay_frames']=len(inference)
            summary['direct_comparison']=info['hailo']['comparison']
            summary['recorded_equal_frames']=sum(r['recorded_comparison']['equal'] for r in results)
            summary['replayed_counts']=summarize([{**r,'recorded':r['replayed']} for r in results],cfg.camera.confidence_min)
        (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False))
        info['status']='complete';info['frames_completed']=len(results)
        info['outputs_sha256']={str(p.relative_to(out)):sha256(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='run-manifest.json'}
        save_manifest()
        return summary
    except Exception as e:
        info['status']='failed';info['error']=str(e);save_manifest();raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('backend',choices=['recorded','hailo'])
    p.add_argument('--source',required=True);p.add_argument('--manifest')
    p.add_argument('--output',required=True);p.add_argument('--config',default='config/quad.json')
    p.add_argument('--annotations');p.add_argument('--hailo-env')
    args=p.parse_args()
    try:
        print(json.dumps(run(args),ensure_ascii=False,indent=2))
    except Exception as e:
        p.exit(2,f'Tekrar oynatma hatası: {e}\n')

if __name__=='__main__':
    main()
