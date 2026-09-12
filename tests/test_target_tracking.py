"""Zaman eksenli hedef takibi: kısa boşluk köprüleme, kayıp ve güvenlik sınırı."""
from dataclasses import replace

import cv2
import numpy as np
import pytest

from conftest import telemetry
from test_competition import options, plan, ready, candidate
from safak_gorev2.competition.config import Options, Tracking, COLORS
from safak_gorev2.competition.controller import DualController
from safak_gorev2.competition.tracking import (CANDIDATE, DETECTED, LOST, TEMP_LOST, TRACKED,
                                               TargetTracker, make_box)
from safak_gorev2.competition.vision import Candidate, DualVision
from safak_gorev2.types import Frame


def tracking(**changes):
    return replace(Tracking(enabled=True), **changes)


def box_at(cx, cy, side=.2):
    return (cx-side/2, cy-side/2, cx+side/2, cy+side/2)


def feed(tracker, steps, color='mavi', start=100., dt=.02):
    """steps: kare başına ((bbox, fill), ...) ya da boş demet. Sonuçları döndürür."""
    return [tracker.update(i, start+i*dt, {color: step})[color] for i, step in enumerate(steps)]


def scene(color='mavi', box=(.3,.2,.7,.8), blank=False, frame_id=1, at=100.):
    image = np.full((720,1280,3), 80, np.uint8)
    if not blank:
        paint = (220,65,30) if color == 'mavi' else (30,65,220)
        a,b,c,d = [round(v*s) for v,s in zip(box,(1280,720,1280,720))]
        cv2.rectangle(image,(a,b),(c,d),paint,-1)
    return Frame(frame_id, at, at+.02, image, (), 'SYNTHETIC')


# ---------------------------------------------------------------- takip çekirdeği

def test_single_missing_frame_keeps_the_label():
    """Kare 1-2 gerçek, kare 3 motion blur, kare 4-5 gerçek: etiket kaybolmaz."""
    tracker = TargetTracker(tracking(), COLORS)
    observation = ((box_at(.5,.5), .9),)
    results = feed(tracker, [observation, observation, (), observation, observation])
    assert [r['state'] for r in results] == [CANDIDATE, DETECTED, TRACKED, DETECTED, DETECTED]
    assert results[2]['bridge'] is not None and results[2]['missed'] == 1
    assert results[3]['bridge'] is None and results[3]['missed'] == 0


def test_bridge_window_then_temporarily_lost_then_lost():
    o = tracking(max_tracking_frames=3, max_missed_frames=6)
    tracker = TargetTracker(o, COLORS)
    observation = ((box_at(.5,.5), .9),)
    results = feed(tracker, [observation]*2 + [()]*8)
    states = [r['state'] for r in results[2:]]
    assert states[:3] == [TRACKED]*3
    assert states[3:6] == [TEMP_LOST]*3
    assert states[6] == LOST and results[-1]['bridge'] is None
    assert not tracker.tracks  # Eski hedef sonsuza kadar tutulmaz.
    assert all(r['bridge'] is None for r in results[5:])


def test_lost_target_must_be_confirmed_again():
    o = tracking(max_tracking_frames=1, max_missed_frames=2, confirmation_frames=2)
    tracker = TargetTracker(o, COLORS)
    observation = ((box_at(.5,.5), .9),)
    feed(tracker, [observation]*2 + [()]*3)
    assert not tracker.tracks
    again = tracker.update(90, 200., {'mavi': observation})['mavi']
    assert again['state'] == CANDIDATE and again['bridge'] is None


def test_single_false_detection_never_bridges():
    """Tek karelik yanlış tespit hedef sayılmaz; sonraki karede köprülenmez."""
    tracker = TargetTracker(tracking(confirmation_frames=2), COLORS)
    results = feed(tracker, [((box_at(.5,.5), .9),), (), ()])
    assert results[0]['state'] == CANDIDATE
    assert all(r['bridge'] is None for r in results[1:])


def test_impossible_jump_is_not_associated_and_does_not_corrupt_the_filter():
    o = tracking(max_jump=.05, max_jump_rate=.5)
    tracker = TargetTracker(o, COLORS)
    near = ((box_at(.5,.5), .9),)
    feed(tracker, [near]*3)
    jumped = tracker.update(3, 100.06, {'mavi': ((box_at(.95,.95), .95),)})['mavi']
    assert jumped['chosen'] is None and jumped['plausible'] == [False]
    assert jumped['state'] == TRACKED  # Sıçrayan ölçüm kare kaybı gibi ele alınır.
    assert jumped['bridge'] is not None
    cx = (jumped['bridge'][0]+jumped['bridge'][2])/2
    assert abs(cx-.5) < .05  # Süzgeç eski konumda kaldı, ışınlanmayı yutmadı.


def test_reachable_motion_is_accepted():
    o = tracking(max_jump=.05, max_jump_rate=3.)
    tracker = TargetTracker(o, COLORS)
    results = [tracker.update(i, 100+i*.02, {'mavi': ((box_at(.5+i*.03,.5), .9),)})['mavi']
               for i in range(5)]
    assert all(r['chosen'] == 0 for r in results)
    assert all(r['state'] in (CANDIDATE, DETECTED) for r in results)


def test_filtered_center_is_smoother_and_unbiased():
    tracker = TargetTracker(tracking(), COLORS)
    rng = np.random.default_rng(7)
    raw, filtered = [], []
    for i in range(40):
        cx = .5+rng.normal(0, .01)
        result = tracker.update(i, 100+i*.02, {'mavi': ((box_at(cx,.5), .9),)})['mavi']
        raw.append(cx)
        filtered.append((result['filtered'][0]+result['filtered'][2])/2)
    raw, filtered = np.array(raw[5:]), np.array(filtered[5:])
    assert np.std(np.diff(filtered)) < np.std(np.diff(raw))       # Daha az zıplama.
    assert np.sqrt(np.mean((filtered-.5)**2)) < np.sqrt(np.mean((raw-.5)**2))  # Gürültü azaldı.


def test_smoothing_does_not_lag_a_moving_target():
    """Düşük gecikme önceliklidir: sabit hızlı harekette kalan hata pikselaltı."""
    tracker = TargetTracker(tracking(), COLORS)
    error = []
    for i in range(25):
        cx = .2+i*.01  # 0,01 normalize/kare = 50 FPS'de yarım kare genişliği/s.
        result = tracker.update(i, 100+i*.02, {'mavi': ((box_at(cx,.5), .9),)})['mavi']
        error.append(abs((result['filtered'][0]+result['filtered'][2])/2-cx))
    assert max(error[10:]) < .002  # 1280 pikselde ~2,5 pikselden az gecikme.


def test_best_candidate_beats_a_brighter_but_inconsistent_blob():
    tracker = TargetTracker(tracking(), COLORS)
    steady = (box_at(.5,.5), .80)
    feed(tracker, [(steady,)]*4)
    result = tracker.update(4, 100.08, {'mavi': (steady, (box_at(.2,.8,.5), .99))})['mavi']
    assert result['chosen'] == 0  # Yüksek doluluklu ama tutarsız aday seçilmedi.


def test_long_pipeline_gap_resets_the_track():
    tracker = TargetTracker(tracking(max_gap_s=.25), COLORS)
    observation = ((box_at(.5,.5), .9),)
    feed(tracker, [observation]*3)
    late = tracker.update(90, 200., {'mavi': observation})['mavi']
    assert late['state'] == CANDIDATE and late['hits'] == 1


def test_prediction_leaving_the_frame_drops_the_label():
    tracker = TargetTracker(tracking(), COLORS)
    steps = [((box_at(.5+i*.2, .5, .1), .9),) for i in range(3)]
    feed(tracker, steps)
    gone = tracker.update(3, 100.06, {'mavi': ()})['mavi']
    assert gone['bridge'] is None and gone['state'] == TEMP_LOST


def test_two_colors_are_tracked_independently():
    tracker = TargetTracker(tracking(), COLORS)
    blue = ((box_at(.3,.3), .9),)
    red = ((box_at(.7,.7), .9),)
    for i in range(3):
        tracker.update(i, 100+i*.02, {'mavi': blue, 'kirmizi': red})
    result = tracker.update(3, 100.06, {'mavi': (), 'kirmizi': red})
    assert result['mavi']['state'] == TRACKED and result['kirmizi']['state'] == DETECTED


def test_make_box_rejects_degenerate_prediction():
    assert make_box(.5, .5, .2, .2) == pytest.approx((.4,.4,.6,.6))
    assert make_box(-.5, .5, .2, .2) is None


# ---------------------------------------------------------------- görüntüden uçtan uca

def test_pixels_keep_the_label_through_a_blank_frame(cfg):
    vision = DualVision(cfg, tracking=tracking())
    for i in range(2):
        xs,_ = vision.detect(scene(frame_id=i, at=100+i*.02), strategy='quick')
        assert len(xs) == 1 and xs[0].source == 'opencv' and xs[0].corroborated
    xs,_ = vision.detect(scene(blank=True, frame_id=2, at=100.04), strategy='quick')
    assert len(xs) == 1 and xs[0].bridged and xs[0].track_state == TRACKED
    assert xs[0].missed == 1 and xs[0].filtered_bbox is not None
    xs,_ = vision.detect(scene(frame_id=3, at=100.06), strategy='quick')
    assert len(xs) == 1 and xs[0].corroborated and not xs[0].bridged


def test_disabled_tracking_returns_the_original_candidates(cfg):
    vision = DualVision(cfg)
    xs,_ = vision.detect(scene(), strategy='quick')
    assert len(xs) == 1 and xs[0].score is None and xs[0].track_state is None
    assert vision.tracker is None
    xs,_ = vision.detect(scene(blank=True, frame_id=2, at=100.02), strategy='quick')
    assert not xs


def test_real_detection_box_is_never_replaced_by_the_filter(cfg):
    vision = DualVision(cfg, tracking=tracking())
    plain = DualVision(cfg)
    for i in range(6):
        frame = scene(frame_id=i, at=100+i*.02, box=(.3+i*.01,.2,.7+i*.01,.8))
        tracked,_ = vision.detect(frame, strategy='quick')
        raw,_ = plain.detect(frame, strategy='quick')
        real = [x for x in tracked if not x.bridged]
        assert [x.bbox for x in real] == [x.bbox for x in raw]
        assert [x.color_fill for x in real] == [x.color_fill for x in raw]
        assert all(x.metric is None for x in real)


# ---------------------------------------------------------------- güvenlik sınırı

def bridged(fid, now, color='mavi', box=(.3,.2,.7,.8), missed=1):
    return Candidate(color, fid, now, None, box, None, 'tracked', False, None,
                     TRACKED, .9, missed, box)


def test_bridged_candidate_is_never_flight_evidence(cfg, options, plan):
    c = DualController(cfg, replace(options, tracking=tracking()))
    x = bridged(1, 100.)
    assert not x.corroborated and x.bridged
    assert c.fresh_candidates((x,), 1, 100.) == []
    assert len(c.bridged_candidates((x,), 1, 100.)) == 1
    # Gerçek aday köprü listesine, köprü adayı gerçek listeye giremez.
    real = candidate(1, 100.)
    assert c.bridged_candidates((real,), 1, 100.) == []
    assert len(c.fresh_candidates((real,), 1, 100.)) == 1


@pytest.mark.parametrize('missed', [0, 4])
def test_bridged_candidate_outside_the_window_is_rejected(cfg, options, missed):
    c = DualController(cfg, replace(options, tracking=tracking(max_tracking_frames=3)))
    assert c.bridged_candidates((bridged(1, 100., missed=missed),), 1, 100.) == []


def test_one_dropped_frame_no_longer_restarts_the_search_counter(cfg, options, plan):
    """Aynı kare dizisi: köprüleme açıkken hedef alınır, kapalıyken alınamaz."""
    def run(enabled):
        o = replace(options, tracking=tracking(enabled=enabled), quick_frames=3, quick_hold_s=.10)
        c = ready(cfg, o, plan)
        for i in range(6):
            now = 100+i*.05
            # Her üçüncü karede OpenCV hedefi kaçırıyor; yerine köprü adayı var.
            xs = ((bridged(i, now),) if i % 3 == 2 else (candidate(i, now),))
            d = c.step(now, telemetry(now), xs, i, now, plan)
            if d.state == 'REQUEST_STOP':
                return i
        return None
    assert run(True) is not None
    assert run(False) is None


def test_bridged_candidate_cannot_verify_or_release(cfg, options, plan):
    c = ready(cfg, replace(options, tracking=tracking()), plan)
    mode = 'AUTO'
    actions, states = [], set()
    for i in range(140):
        now = 100+i*.05
        # Duruş sonrası yalnız köprülenmiş kutu geliyor: gerçek renk kanıtı yok.
        xs = ((candidate(i, now),) if c.state in ('WAIT_AUTO','SEARCHING','REQUEST_STOP','STOPPING')
              else (bridged(i, now),))
        d = c.step(now, telemetry(now, mode=mode), xs, i, now, plan)
        states.add(d.state)
        for a in d.actions:
            actions.append(a.kind)
            if a.kind == 'mode':
                mode = a.values[0]
    assert 'VERIFYING' in states
    assert 'payload' not in actions and 'release' not in actions
    assert 'resume' in actions  # Doğrulanamadı; yük korunarak rotaya dönüldü.


# ---------------------------------------------------------------- yapılandırma

@pytest.mark.parametrize('values', [{'confirmation_frames': 0}, {'max_tracking_frames': 9, 'max_missed_frames': 4},
                                    {'max_gap_s': 0}, {'smoothing_alpha': 1.5}, {'min_score': 2.},
                                    {'measurement_noise': float('nan')}, {'enabled': 'evet'},
                                    {'max_jump': 1.5}, {'process_accel': -1}])
def test_invalid_tracking_settings_rejected(values):
    with pytest.raises(ValueError):
        Tracking(**values).validate()


def test_field_profiles_enable_tracking_within_the_lock_gap():
    for task in ('ana', 'hizli'):
        cfg, o = Options.load(f'config/{task}-gorev.json')
        assert o.tracking.enabled is True and o.tracking.debug is False
        assert o.tracking.max_tracking_frames < o.tracking.max_missed_frames
        # Köprü penceresi kilit boşluğu sınırının içinde kalmalı.
        assert o.tracking.max_tracking_frames/cfg.camera.fps <= cfg.control.max_lock_frame_gap_s
        assert o.tracking.max_gap_s <= cfg.control.frame_timeout_s


# ---------------------------------------------------------------- panel / teşhis

def test_debug_lines_report_state_center_missed_and_score():
    from safak_gorev2.competition.runtime import CompetitionRuntime
    real = Candidate('mavi',5,100.,None,(.3,.2,.7,.8),None,'opencv',True,.93,DETECTED,.91,0,(.31,.21,.69,.79))
    lines = CompetitionRuntime.debug_lines(real)
    assert lines[0].startswith('DETECTION') and 'kacan=0' in lines[0] and 'skor=0.91' in lines[0]
    assert 'ham=(0.500,0.500)' in lines[1] and 'suzulmus=' in lines[1]
    assert CompetitionRuntime.debug_lines(bridged(6, 100.02))[0].startswith('TRACKING')
    bare = Candidate('mavi',5,100.,None,(.3,.2,.7,.8),None,'opencv',True,.93)
    assert CompetitionRuntime.debug_lines(bare)[0] == '-'  # Takip kapalıyken sayı uydurulmaz.


def test_panel_candidate_label_contains_only_color_and_metric_distance():
    from safak_gorev2.competition.runtime import CompetitionRuntime
    from safak_gorev2.types import Target
    metric = Target(5,100.,.9,1.,2.,3.,5.24,.4,((0.,0.),)*4,(.3,.2,.7,.8),.95)
    measured = Candidate('mavi',5,100.,None,(.3,.2,.7,.8),metric,'opencv',True,.93)
    tracked = Candidate('kirmizi',6,100.02,None,(.3,.2,.7,.8),None,'tracked',False,None)
    assert CompetitionRuntime.candidate_label(measured) == 'MAVI / 5.2 m'
    assert CompetitionRuntime.candidate_label(tracked) == 'KIRMIZI'
    assert 'OPENCV' not in CompetitionRuntime.candidate_label(measured)


def test_observe_runtime_draws_the_bridged_label(cfg, options, tmp_path):
    """Boş karede panel etiketi kaybolmaz ve boru hattı hata vermez."""
    import time
    from safak_gorev2.competition.runtime import CompetitionRuntime
    o = replace(options, tracking=tracking(debug=True))
    rt = CompetitionRuntime(replace(cfg, runtime_dir=str(tmp_path/'track')), 'observe', o)
    rt.start(connect=False)
    try:
        base = time.monotonic()
        for i, blank in enumerate((False, False, True)):
            image = np.full((720,1280,3), 80, np.uint8)
            if not blank:
                cv2.rectangle(image,(180,180),(380,380),(220,65,30),-1)
            rt.mailbox.put(Frame(i+1, time.monotonic(), time.monotonic(), image, (), 'OPENCV'))
            until = time.monotonic()+2
            while time.monotonic() < until and (rt.processed_frame is None
                                                or rt.processed_frame.id != i+1):
                time.sleep(.005)
            assert rt.processed_frame is not None and rt.processed_frame.id == i+1
        until = time.monotonic()+1
        while time.monotonic() < until and not any(x.bridged for x in rt.candidates):
            time.sleep(.01)
        assert [x.bridged for x in rt.candidates] == [True]
        assert rt.candidates[0].track_state == TRACKED and rt.candidates[0].missed == 1
        until = time.monotonic()+1
        while time.monotonic() < until and rt.state.jpeg is None:
            time.sleep(.01)
        assert rt.state.jpeg is not None and rt.state.pipeline_error is None
        assert time.monotonic()-base < 10
    finally:
        rt.close()
