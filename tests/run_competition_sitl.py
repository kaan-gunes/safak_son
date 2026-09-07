"""Yalnız kendi başlattığı loopback hexacopter SITL; sentetik kamera, gerçek MAVLink servo komutları."""
import argparse
from dataclasses import replace, asdict
import json
import math
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_sitl import wait_message, send_command
import cv2
import numpy as np
from pymavlink import mavutil

from safak_gorev2.config import Config
from safak_gorev2.demo import demo_calibration
from safak_gorev2.geometry import CAMERA_TO_BODY, body_to_ned, TargetGeometry
from safak_gorev2.mavlink_io import validate_mission
from safak_gorev2.types import MissionItem, Frame, Detection
from safak_gorev2.shared import finite_json
from safak_gorev2.competition.config import Options, Servo, SIDES
from safak_gorev2.competition.runtime import CompetitionRuntime
from safak_gorev2.competition.route import mission_digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ardupilot',type=Path,required=True)
    parser.add_argument('--strategy',choices=('center','sighting'),required=True)
    parser.add_argument('--scenario',choices=('complete','pilot','lost-target','control-stall'),default='complete')
    args=parser.parse_args()
    root=Path('artifacts/competition-sitl')/(time.strftime('%Y%m%dT%H%M%S')+'-'+args.strategy+'-'+args.scenario)
    root.mkdir(parents=True)
    root=root.resolve()
    binary=args.ardupilot.resolve()/'build/sitl/bin/arducopter'
    for port in (5890,5892,5899):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            probe.bind(('127.0.0.1',port))
    defaults=root/'sitl-only.parm'
    defaults.write_text('\n'.join(['FRAME_CLASS 2','SERIAL1_PROTOCOL 2','MIS_RESTART 0','GUID_TIMEOUT 1',
        'FLTMODE_CH 5','FLTMODE1 5','FLTMODE6 3','FS_THR_ENABLE 3','AUTO_OPTIONS 3',
        'WPNAV_SPEED 60','WPNAV_ACCEL 60','SIM_GPS_DELAY 0',
        'SERVO9_FUNCTION 0','SERVO10_FUNCTION 0','SERVO9_MIN 1000','SERVO9_MAX 2000',
        'SERVO10_MIN 1000','SERVO10_MAX 2000'])+'\n')
    log=(root/'autopilot.log').open('w')
    proc=subprocess.Popen([str(binary),'--model','hexa','--home','41,29,50,0','--speedup','1',
        '--serial0','tcp:5890','--serial1','tcp:5892','--rc-in-port','5899','--wipe',
        '--defaults',str(args.ardupilot.resolve()/'Tools/autotest/default_params/copter.parm')+','+str(defaults)],
        cwd=root,stdout=log,stderr=subprocess.STDOUT)
    rt=ground=None
    stop=threading.Event(); throttle=[1000]; slot=[2000]; hidden=[False]
    try:
        until=time.monotonic()+20
        while True:
            try:
                ground=mavutil.mavlink_connection('tcp:127.0.0.1:5890',source_system=255,source_component=190)
                break
            except OSError:
                if time.monotonic()>until or proc.poll() is not None: raise
                stop.wait(.1)
        while wait_message(ground,'HEARTBEAT').system_status==1: pass
        def radio():
            while not stop.wait(.1):
                ground.mav.heartbeat_send(6,8,0,0,4)
                ground.mav.rc_channels_override_send(1,1,1500,1500,throttle[0],1500,slot[0],1500,1500,1500)
        threading.Thread(target=radio,daemon=True).start()
        items=[MissionItem(0,16,0,410000000,290000000,0),MissionItem(1,22,3,0,0,6),
               MissionItem(2,16,3,410000000,290001670,6),MissionItem(3,16,3,410000000,290000000,6),
               MissionItem(4,21,3,410000000,290000000,0)]
        ground.mav.mission_count_send(1,1,len(items))
        for _ in range(20):
            msg=wait_message(ground,['MISSION_REQUEST_INT','MISSION_REQUEST','MISSION_ACK'])
            if msg.get_type()=='MISSION_ACK':
                assert msg.type==0; break
            item=items[msg.seq]
            ground.mav.mission_item_int_send(1,1,item.seq,item.frame,item.command,0,1,0,0,0,0,item.x,item.y,item.z)
        else: raise RuntimeError('Görev ACK gelmedi')
        items=[replace(x,z=float(x.z)) for x in items]
        plan=validate_mission(items)
        cal=demo_calibration()
        cp=root/'camera.json'
        cp.write_text(json.dumps({'schema':1,'projection':'pinhole','width':1280,'height':720,
            'camera_matrix':cal.matrix.tolist(),'distortion':cal.distortion.tolist(),
            'camera_model':cal.camera_model,'scaler_crop':cal.scaler_crop,'rms_px':cal.rms_px}))
        cfg=Config()
        cfg=replace(cfg,camera=replace(cfg.camera,offset_body_m=(-.03,0,.05),calibration_file=str(cp)),
            mission=replace(cfg.mission,direct_land_corridor_checked=True),
            link=replace(cfg.link,device='tcp:127.0.0.1:5892'),runtime_dir=str(root/'runtime'))
        opts=Options(strategy=args.strategy,actuator='servo',vehicle_type=13,sortie_id='sitl-only',
            mission_fingerprint=mission_digest(plan),search_start_seq=2,search_end_seq=2,route_reviewed=True,
            entry_gates=(((40.9999,29.000012),(41.0001,29.000012)),),
            finish_gate=((41.0001,29.000024),(40.9999,29.000024)),
            flight_polygon=((40.99,28.99),(41.01,28.99),(41.01,29.01),(40.99,29.01)),
            servos={'kirmizi':Servo(9,1700,True),'mavi':Servo(10,1800,True)})
        rt=CompetitionRuntime(cfg,'flight',opts)
        rt.start()
        def camera():
            fid=0; last=-1
            while not stop.wait(.04):
                t=rt.telemetry.snapshot(); at=min(t.attitude_at,t.position_at)
                if at<=last: continue
                pose=rt.telemetry.pose_at(at,.1)
                if pose is None: continue
                last=at
                image=np.full((720,1280,3),(55,70,55),np.uint8); ds=[]
                r=body_to_ned(pose.roll,pose.pitch,pose.yaw)
                for color, east, paint in [('mavi',4.,(210,70,20)),('kirmizi',8.,(20,50,220))]:
                    geom=TargetGeometry(replace(cfg.camera,target_side_m=SIDES[color]),cal)
                    tv=CAMERA_TO_BODY.T@(r.T@(np.array([0.,east,0.])-np.array([pose.north,pose.east,pose.down]))
                                           -np.array(cfg.camera.offset_body_m))
                    if tv[2]<=1 or hidden[0]: continue
                    ro=np.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,-1.]])
                    rv,_=cv2.Rodrigues(CAMERA_TO_BODY.T@r.T@ro)
                    q,_=cv2.projectPoints(geom.object_points,rv,tv,cal.matrix,cal.distortion); q=q.reshape(4,2)
                    if not np.isfinite(q).all() or np.max(np.abs(q))>100000: continue
                    cv2.fillConvexPoly(image,q.astype(np.int32),paint)
                    box=tuple(np.clip(np.array([*q.min(axis=0),*q.max(axis=0)])/[1280,720,1280,720],0,1))
                    if box[0]<box[2] and box[1]<box[3]: ds.append(Detection(color+'_hedef',.95,box))
                fid+=1
                rt.mailbox.put(Frame(fid,at,time.monotonic(),image,tuple(ds),'SITL SYNTHETIC'))
        threading.Thread(target=camera,daemon=True).start()
        until=time.monotonic()+55
        while time.monotonic()<until:
            t=rt.telemetry.snapshot()
            if rt.link.failure: raise RuntimeError(rt.link.failure)
            if (rt.telemetry.preflight_problem() is None and rt.link.hardware_problem() is None
                    and t.gps_fix and t.gps_fix>=3 and t.ekf_flags&23==23 and t.rc_healthy): break
            stop.wait(.2)
        else: raise RuntimeError(str(rt.telemetry.preflight_problem())+' / '+str(rt.link.hardware_problem()))
        actual=rt.telemetry.mission
        (root/'mission-comparison.json').write_text(json.dumps({'expected':[vars(x) for x in plan.items], 'actual':[vars(x) for x in actual.items]},indent=2))
        if mission_digest(actual) != mission_digest(plan):
            raise RuntimeError('SITL rota parmak izi farklı; mission-comparison.json')
        stop.wait(.5)
        ground.mav.set_mode_send(1,1,3)
        stop.wait(1.)
        send_command(ground,400,1)
        arm_deadline=time.monotonic()+12
        arm_messages=[]
        while time.monotonic()<arm_deadline:
            msg=ground.recv_match(type=['COMMAND_ACK','STATUSTEXT','HEARTBEAT'],blocking=True,timeout=.2)
            if msg:
                if msg.get_type()=='STATUSTEXT': arm_messages.append(msg.text)
                if msg.get_type()=='COMMAND_ACK' and msg.command==400:
                    arm_messages.append('ARM ACK '+str(msg.result))
            if rt.telemetry.snapshot().armed: break
        else: raise RuntimeError('SITL ARM başarısız: '+str(arm_messages))
        start=time.monotonic(); previous=None; states=[]; injected=False
        while time.monotonic()-start<200:
            t=rt.telemetry.snapshot(); d=rt.state.decision
            if t.armed and t.landed==2: throttle[0]=1500
            if d.state!=previous:
                item={'state':d.state,'reason':d.reason,'seconds':round(time.monotonic()-start,2),
                      'mode':t.mode,'seq':t.mission_seq,'payloads':rt.payload_status.copy()}
                print(json.dumps(item,ensure_ascii=False),flush=True); states.append(item); previous=d.state
            if not injected and d.state=='DESCENDING' and args.scenario!='complete':
                injected=True
                if args.scenario=='pilot': slot[0]=1000
                if args.scenario=='lost-target': hidden[0]=True
                if args.scenario=='control-stall':
                    original=rt.controller.step
                    def stalled(*values,**kwargs):
                        stop.wait(1.5); rt.controller.step=original
                        return original(*values,**kwargs)
                    rt.controller.step=stalled
            if d.state in ('DONE','INCOMPLETE','ABORTED','PILOT_CONTROL'):
                result={'strategy':args.strategy,'scenario':args.scenario,'states':states,
                        'payloads':rt.payload_status,'final_state':d.state,'synthetic_vision':True,
                        'servo_outputs_are_simulated':True,'firmware':t.firmware}
                (root/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
                if args.scenario=='complete':
                    assert d.state=='DONE' and rt.payload_status=={'kirmizi':'ACK_ACCEPTED','mavi':'ACK_ACCEPTED'},result
                else:
                    stop.wait(1.)
                    assert injected and d.state in ('ABORTED','PILOT_CONTROL') and not rt.payload_status,result
                    assert rt.telemetry.snapshot().mode=='LOITER' and not rt.link.owned
                print('SITL PASS '+str(root),flush=True)
                return
            stop.wait(.1)
        raise TimeoutError(str(rt.state.decision))
    finally:
        stop.set()
        if rt: rt.close()
        if ground: ground.close()
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        log.close()


if __name__=='__main__': main()
