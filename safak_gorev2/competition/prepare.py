"""Mission Planner WPL dosyasını yerelde denetler; FC'ye bağlanmaz/yüklemez."""
import argparse
import json
from pathlib import Path

from ..mavlink_io import validate_mission
from ..types import MissionItem
from .route import mission_digest


def read_wpl(path):
    lines=Path(path).read_text().splitlines()
    if not lines or lines[0].strip()!='QGC WPL 110':
        raise ValueError('Mission Planner QGC WPL 110 dosyası gerekli')
    items=[]
    for line in lines[1:]:
        if not line.strip(): continue
        fields=line.split()
        if len(fields)!=12: raise ValueError('Görev satırında 12 alan gerekli')
        seq,frame,command=int(fields[0]),int(fields[2]),int(fields[3])
        if command not in (16,22,21):
            raise ValueError('Bu sürüm yalnız TAKEOFF / WAYPOINT / son LAND rotasını destekler')
        # Parmak izi MissionItem alanlarına bağlıdır. Saklanmayan parametreleri kabul etme.
        if (any(float(v)!=0 for v in fields[4:7]) or int(fields[11])!=1
                or float(fields[7]) not in ((-1,0,1) if command == 21 else (0,))):
            raise ValueError('WPL param1–4 sıfır, autocontinue=1 olmalı; gizli görev eylemi kabul edilmez')
        items.append(MissionItem(seq,command,frame,round(float(fields[8])*1e7),round(float(fields[9])*1e7),float(fields[10])))
    return validate_mission(items)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mission',required=True)
    args=p.parse_args()
    plan=read_wpl(args.mission)
    print(json.dumps({'mission_fingerprint':mission_digest(plan),'takeoff_seq':plan.takeoff_seq,
                      'land_seq':plan.land_seq,'items':[vars(x) for x in plan.items]},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
