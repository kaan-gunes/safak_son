from dataclasses import replace

import cv2
import numpy as np
import pytest

from conftest import telemetry
from test_competition import options, plan, ready, candidate
from safak_gorev2.competition.config import Options, ColorSearch
from safak_gorev2.competition.vision import Candidate, DualVision
from safak_gorev2.types import Detection, Frame


def scene(color='mavi', include_ai_metadata=True, shape='square', box=(.3,.2,.7,.8)):
    image=np.full((720,1280,3),80,np.uint8)
    paint=(220,65,30) if color=='mavi' else (30,65,220)
    a,b,c,d=[round(v*s) for v,s in zip(box,(1280,720,1280,720))]
    if shape=='square': cv2.rectangle(image,(a,b),(c,d),paint,-1)
    if shape=='circle': cv2.circle(image,(640,360),120,paint,-1)
    if shape=='triangle': cv2.fillConvexPoly(image,np.array([[500,450],[640,200],[780,450]]),paint)
    if shape=='outline': cv2.rectangle(image,(a,b),(c,d),paint,6)
    ds=(Detection(color+'_hedef',.95,box),) if include_ai_metadata else ()
    return Frame(1,100.,100.02,image,ds,'SYNTHETIC')


@pytest.mark.parametrize('color',['mavi','kirmizi'])
def test_color_search_is_the_only_candidate_source(cfg,color):
    xs,_=DualVision(cfg).detect(scene(color,include_ai_metadata=False),strategy='quick')
    assert len(xs)==1 and xs[0].color==color and xs[0].source=='opencv'
    assert xs[0].confidence is None and xs[0].metric is None and xs[0].corroborated


@pytest.mark.parametrize('color',['mavi','kirmizi'])
def test_ai_metadata_is_ignored_even_over_same_region(cfg,color):
    xs,_=DualVision(cfg).detect(scene(color),strategy='quick')
    assert len(xs)==1 and xs[0].source=='opencv' and xs[0].confidence is None


@pytest.mark.parametrize('shape',['circle','triangle','outline','blank'])
def test_colored_non_target_shapes_are_rejected_without_ai_fallback(cfg,shape):
    xs,_=DualVision(cfg).detect(scene(shape=shape),strategy='quick')
    assert not xs


@pytest.mark.parametrize('bad',['wrong_color','different_region','low_score','invalid_box'])
def test_ai_metadata_cannot_change_opencv_result(cfg,bad):
    f=scene()
    det=f.detections[0]
    if bad=='wrong_color': det=replace(det,label='kirmizi_hedef')
    if bad=='different_region': det=replace(det,bbox=(.02,.02,.15,.15))
    if bad=='low_score': det=replace(det,confidence=.1)
    if bad=='invalid_box': det=replace(det,bbox=(-.9,.2,.1,.8))
    xs,_=DualVision(cfg).detect(replace(f,detections=(det,)),strategy='quick')
    assert len(xs)==1 and xs[0].source=='opencv' and xs[0].color=='mavi'


@pytest.mark.parametrize('strategy',['quick','center'])
def test_clipped_color_still_confirms_candidate(cfg,strategy):
    # Kenara değen hedef her iki görevde de aday olur; ana görevde ölçümü
    # metrik geometrinin kendi kenar payı reddeder (bkz. test_replay 'border').
    f=scene(box=(0.,.2,.3,.8))
    assert any(x.source=='opencv' for x in DualVision(cfg).detect(f,strategy=strategy)[0])


@pytest.mark.parametrize('color',['mavi','kirmizi'])
def test_box_touching_frame_edge_is_clamped_not_dropped(cfg,color):
    # Gerçek uçuşta mavi hedefin kutusu üst kenarda ymin=-0,01 geldi ve tüm
    # kare eleniyordu; kenara taşan kutu artık kırpılıp doğrulanabiliyor.
    f=scene(color,box=(.3,0.,.7,.6))
    det=replace(f.detections[0],bbox=(.3,-.012,.7,.6))
    xs,_=DualVision(cfg).detect(replace(f,detections=(det,)),strategy='quick')
    assert len(xs)==1 and xs[0].corroborated and xs[0].bbox[1]==0.


def test_ai_box_on_blank_image_does_not_create_candidate(cfg):
    f=scene(shape='blank')
    xs,_=DualVision(cfg).detect(f,strategy='quick')
    assert not xs


@pytest.mark.parametrize('strategy',['center','quick'])
@pytest.mark.parametrize('after',['opencv','missing','wrong_source','alternating','malformed'])
def test_stop_requires_fresh_opencv_after_measured_stop(cfg,options,plan,strategy,after):
    c=ready(cfg,replace(options,strategy=strategy),plan)
    mode='AUTO';seen=[];actions=[]
    for i in range(130):
        now=100+i*.05
        # İlk duruş ve son doğrulama yalnız OpenCV renk/dörtgen kanıtıdır.
        x=Candidate('mavi',i,now,None,(.3,.2,.7,.8),source='opencv',color_verified=True,color_fill=.95)
        if c.state=='VERIFYING':
            if after=='missing' or (after=='alternating' and i%2==0):
                xs=()
            else:
                x=candidate(i,now,metric=strategy=='center')
                if after=='wrong_source': x=replace(x,source='ai',confidence=.95)
                if after=='malformed': x=replace(x,color_fill=float('nan'))
                xs=(x,)
        else:
            xs=(x,)
        d=c.step(now,telemetry(now,mode=mode),xs,i,now,plan)
        seen.append(c.state)
        for a in d.actions:
            actions.append(a.kind)
            if a.kind=='mode': mode=a.values[0]
        if c.state in ('INTERCEPT','RELEASE_WAIT') or 'resume' in actions: break
    assert 'REQUEST_STOP' in seen and 'STOPPING' in seen and 'VERIFYING' in seen
    if after=='opencv':
        assert c.state==('INTERCEPT' if strategy=='center' else 'RELEASE_WAIT')
    else:
        assert 'payload' not in actions and 'velocity' not in actions
        assert 'resume' in actions


def test_no_color_result_is_carried_to_later_frame(cfg):
    v=DualVision(cfg)
    xs,_=v.detect(scene(include_ai_metadata=False),strategy='quick')
    assert xs[0].source=='opencv'
    f=replace(scene(shape='blank'),id=2,captured_at=100.02)
    xs,_=v.detect(f,strategy='quick')
    assert not xs


def test_hsv_red_wrap_and_dim_but_visible_target(cfg):
    v=DualVision(cfg)
    for hue in (0,179,110):
        f=scene(include_ai_metadata=False)
        hsv=np.zeros((720,1280,3),np.uint8)
        hsv[150:500,400:800]=(hue,160,70)
        f=replace(f,image=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR))
        xs,_=v.detect(f,strategy='quick')
        assert len(xs)==1 and xs[0].color==('mavi' if hue==110 else 'kirmizi')


def test_active_profiles_request_fifty_fps():
    for task in ('ana','hizli'):
        cfg,o=Options.load(f'config/{task}-gorev.json')
        assert cfg.camera.fps==50 and o.color_search.match_iou==.5


def test_pixels_to_color_stop_to_dual_verified_two_payloads(cfg,options,plan):
    vision=DualVision(cfg)
    c=ready(cfg,options,plan)
    mode='AUTO';statuses={};released=[];stop_sources=[];seq=2
    for i in range(180):
        now=100+i*.05
        color='mavi' if 'mavi' not in c.done else 'kirmizi'
        f=replace(scene(color,include_ai_metadata=False),id=i,captured_at=now)
        xs,_=vision.detect(f,strategy='quick')
        d=c.step(now,telemetry(now,mode=mode,mission_seq=seq),xs,i,now,plan,release_status=statuses)
        for a in d.actions:
            if a.kind=='claim': stop_sources.append({x.source for x in xs})
            if a.kind=='mode': mode=a.values[0]
            if a.kind in ('mission_current','resume'): seq=a.values[0]
            if a.kind=='payload':
                assert any(x.corroborated for x in xs)
                released.append(a.values[:2]);statuses[a.values[0]]='SIMULATED'
        if c.state=='LANDING':break
    assert stop_sources==[{'opencv'},{'opencv'}]
    assert released==[('kirmizi','mavi'),('mavi','kirmizi')]
    assert mode=='AUTO' and seq==plan.land_seq
    assert c.state=='LANDING'


@pytest.mark.parametrize('values',[{'width':0},{'max_candidates':100},{'min_saturation':0},
                                  {'min_fill':float('nan')},{'match_iou':.1},{'max_aspect':float('inf')}])
def test_invalid_color_search_settings_rejected(values):
    with pytest.raises(ValueError): ColorSearch(**values).validate()
