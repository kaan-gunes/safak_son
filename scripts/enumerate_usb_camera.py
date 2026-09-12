"""Linux Pi üzerinde salt okunur USB/V4L2 envanteri; kamera açmaz, kontrol yazmaz."""
import argparse
import json
from pathlib import Path
import subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--device',required=True,help='/dev/videoN; yalnız bilgi sorgusu')
p.add_argument('--output',required=True,type=Path)
a=p.parse_args()
commands=[['v4l2-ctl','--list-devices'],['v4l2-ctl','-d',a.device,'--all'],
          ['v4l2-ctl','-d',a.device,'--list-formats-ext'],['v4l2-ctl','-d',a.device,'--list-ctrls-menus'],
          ['udevadm','info','--query=property','--name',a.device],['lsusb']]
results=[]
for cmd in commands:
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
        results.append({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    except (OSError,subprocess.SubprocessError) as e:results.append({'command':cmd,'error':str(e)})
links={str(x):str(x.resolve()) for folder in ('/dev/v4l/by-id','/dev/v4l/by-path') for x in Path(folder).glob('*')}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps({'commands':results,'stable_links':links},ensure_ascii=False,indent=2))
