"""Doğrulanmış replay sonucunu, yeniden çıkarım yapmadan yeni klasöre çizer."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from safak_gorev2.replay import draw,sha256,stack_comparison


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();results=Path(a.results);source=Path(a.source);out=Path(a.output)
    m=json.loads((results/'run-manifest.json').read_text())
    if m['status']!='complete':raise ValueError('Tamamlanmış sonuç gerekiyor')
    for name,digest in m['outputs_sha256'].items():
        if sha256(results/name)!=digest:raise ValueError('Sonuç hash uyuşmazlığı: '+name)
    rows=[json.loads(line) for line in (results/'frames.jsonl').read_text().splitlines()]
    for row in rows:
        if sha256(source/(row['name']+'.png'))!=row['png_sha256']:raise ValueError('Kaynak PNG hash uyuşmazlığı')
    out.mkdir(parents=True,exist_ok=False)
    for row in rows:
        im=cv2.imread(str(source/(row['name']+'.png')))
        left=draw(im,row['recorded'],row['name']+' / Kayit',row['annotation'])
        right=draw(im,row.get('replayed',row['recorded']),'Ayni PNG / Hailo tekrar cikarim',row['annotation'])
        if not cv2.imwrite(str(out/(row['name']+'.jpg')),stack_comparison(left,right)):raise ValueError('Görsel yazılamadı')
    info={'source_run_manifest_sha256':sha256(results/'run-manifest.json'),
          'render_source_sha256':sha256(Path(__file__).parents[1]/'safak_gorev2/replay.py'),
          'images_sha256':{f.name:sha256(f) for f in sorted(out.glob('*.jpg'))},'inference_rerun':False}
    (out/'render-manifest.json').write_text(json.dumps(info,indent=2))
    print(f'{len(rows)} karşılaştırma çizildi; yeniden çıkarım yok.')

if __name__=='__main__':main()
