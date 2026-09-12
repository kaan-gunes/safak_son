from dataclasses import asdict
from collections import deque
from pathlib import Path
import json
import time

import cv2

from ..geometry import Calibration
from ..runtime import Runtime
from ..shared import finite_json
from ..types import Decision
from .config import PAYLOAD
from .controller import DualController
from .link import CompetitionLink
from .payload import PayloadLedger
from .vision import DualVision
from ..camera_contract import camera_manifest, metric_missing, profile_digest


class CompetitionRuntime(Runtime):
    def __init__(self, cfg, mode, options):
        if mode == "flight" and metric_missing(cfg.camera):
            raise ValueError("; ".join(metric_missing(cfg.camera)))
        super().__init__(cfg, mode)
        self.options = options
        self.camera_contract = camera_manifest(cfg.camera)
        self.profile_digest = profile_digest(cfg, options)
        self.state.event("CAMERA_CONTRACT", self.camera_contract["metric_status"], **self.camera_contract)
        self.controller = DualController(cfg, options)
        self.payload_ledger = PayloadLedger(Path(cfg.runtime_dir).parent/'payload-ledger', options.sortie_id or 'observe')
        self.candidates = ()
        self.processed_frame = None
        self.vision_processing_ms = 0.
        self.tracking_ms = 0.
        self.performance_samples = deque(maxlen=10000)
        self.payload_status = self.payload_ledger.statuses()
        self.decision_input = None
        self.state.mode = mode

    def start(self, connect=True):
        if connect:
            self.link = CompetitionLink(self.cfg, self.telemetry, self.mode == 'flight', self.stop,
                                        self.options, self.payload_ledger)
            self.link.start()
        super().start(connect=False)

    def vision_loop(self):
        calibration = (Calibration.load(self.cfg.camera.calibration_file)
                       if not metric_missing(self.cfg.camera) and self.options.strategy == 'center' and self.cfg.camera.calibration_file
                       and self.cfg.camera.offset_body_m is not None else None)
        vision = DualVision(self.cfg, calibration, self.options.camera_mount_yaw_deg,
                            self.options.color_search, self.options.tracking)
        last = -1
        while not self.stop.is_set():
            frame = self.mailbox.get_after(last)
            if frame is None:
                continue
            last = frame.id
            pose = self.telemetry.pose_at(frame.captured_at, self.cfg.control.exposure_sync_tolerance_s)
            candidates, diagnostics = (), []
            began = time.monotonic()
            if 0 <= time.monotonic()-frame.captured_at <= self.cfg.control.frame_timeout_s:
                candidates, diagnostics = vision.detect(frame, pose, self.options.strategy)
            with self.state.lock:
                self.processed_frame = frame
                self.candidates = candidates
                self.vision_processing_ms = (time.monotonic()-began)*1000
                self.tracking_ms = vision.tracking_ms
                self.performance_samples.append({'frame_id':frame.id,'captured_at':frame.captured_at,
                    'processed_at':time.monotonic(),'vision_ms':self.vision_processing_ms,
                    'tracking_ms':vision.tracking_ms,
                    'opencv_ms':vision.opencv_ms if 0 <= began-frame.captured_at <= self.cfg.control.frame_timeout_s else None,
                    'stale':not 0 <= began-frame.captured_at <= self.cfg.control.frame_timeout_s})
                self.state.vision(frame, tuple(x.metric for x in candidates if x.metric),
                    'Yalnız OpenCV renk/dörtgen / '+self.options.strategy, diagnostics)

    def control_loop(self):
        previous = None
        interval = 1/self.cfg.control.rate_hz
        while not self.stop.is_set():
            now = time.monotonic()
            t = self.telemetry.snapshot()
            with self.state.lock:
                fid, at, _ = self.state.vision_snapshot()
                candidates = self.candidates
                diagnostics = self.state.diagnostics
            if self.link:
                self.payload_status = self.link.snapshot_status()
            if self.mode == 'observe':
                decision = Decision('OBSERVING', 'İki renk izleniyor; uçuş ve servo komutu kapalı')
            else:
                problem = self.state.pipeline_error or self.telemetry.preflight_problem()
                if self.link:
                    problem = problem or self.link.hardware_problem()
                decision = self.controller.step(now, t, candidates, fid, at, self.telemetry.mission,
                                                problem, self.payload_status,
                                                self.link.snapshot_search_speed_status() if self.link else None)
                if self.link:
                    self.link.route_authorized = self.controller.route.entered and not self.controller.route.finished
                    self.link.submit(decision.actions)
            with self.state.lock:
                self.state.decision = decision
                if self.options.strategy == 'center':
                    self.decision_input = {'monotonic': now, 'frame_id': fid, 'frame_at': at,
                        'telemetry': asdict(t), 'candidates': [asdict(x) for x in candidates],
                        'diagnostics': diagnostics, 'selected': self.controller.selected,
                        'verify_count': self.controller.verify_hold.count,
                        'verify_elapsed': self.controller.verify_hold.elapsed,
                        'decision': asdict(decision)}
            signature = (decision.state, tuple(sorted(self.payload_status.items())))
            if signature != previous:
                body = self.state.event('COMPETITION_STATE', decision.reason, state=decision.state,
                                        payloads=self.payload_status.copy())
                self.disk.submit(self.ledger.record, 'COMPETITION_STATE', body)
                previous = signature
            self.stop.wait(max(0, interval-(time.monotonic()-now)))

    def render_loop(self):
        last = -1
        while not self.stop.is_set():
            with self.state.lock:
                frame, candidates = self.processed_frame, self.candidates
            if frame is None or frame.id <= last:
                self.stop.wait(.01)
                continue
            last = frame.id
            source_h, source_w = frame.image.shape[:2]
            width = min(source_w,self.cfg.web.width)
            image = cv2.resize(frame.image,(width,round(source_h*width/source_w)))
            h,w = image.shape[:2]
            debug = self.options.tracking.debug
            for candidate in candidates:
                if not candidate.color_verified and not candidate.bridged:
                    continue
                a,b,c,d = [round(v*s) for v,s in zip(candidate.bbox,(w,h,w,h))]
                active = candidate.color in self.controller.required_targets
                color = (0,220,220) if active else (130,130,130)
                if candidate.bridged:
                    # Tahmin kutusu her zaman turuncu ve TAKIP yazılıdır; operatör
                    # bunu gerçek renk doğrulaması sanmasın.
                    color = (0,150,255) if active else (110,110,140)
                cv2.rectangle(image,(a,b),(c,d),color,2)
                label = ('TAKIP ' if candidate.bridged else
                         'AKTIF HEDEF ' if active else 'PASIF HEDEF ')+candidate.color
                cv2.putText(image,label,(max(0,a),min(h-120,d+20)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,2)
                if debug:
                    for offset,text in enumerate(self.debug_lines(candidate)):
                        cv2.putText(image,text,(max(0,a),min(h-116,d+38+offset*16)),
                                    cv2.FONT_HERSHEY_SIMPLEX,.4,color,1)
            lines = [self.options.strategy+' / '+self.options.actuator+' / '+self.state.decision.state,
                     'KIRMIZI YUK: '+self.payload_status.get('kirmizi','BEKLIYOR'),
                     'MAVI YUK: '+self.payload_status.get('mavi','BEKLIYOR'),
                     'ACK/PWM = komut kaniti; fiziksel dusus sensoru YOK']
            if self.options.tracking.debug:
                lines.append('TAKIP '+('ACIK' if self.options.tracking.enabled else 'KAPALI')
                             +f' / {self.tracking_ms:.2f} ms / kopru<={self.options.tracking.max_tracking_frames} kare')
            cv2.rectangle(image,(0,h-110),(w,h),(20,20,20),-1)
            for i,line in enumerate(lines):
                cv2.putText(image,line,(12,h-88+i*24),cv2.FONT_HERSHEY_SIMPLEX,.55,(230,230,230),1)
            ok, encoded = cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,self.cfg.web.jpeg_quality])
            if ok:
                self.state.jpeg_put(encoded.tobytes(),frame.captured_at,frame.id)
            self.stop.wait(1/self.cfg.web.fps)

    @staticmethod
    def debug_lines(candidate):
        """Ham merkez, suzulmus merkez, kacan kare ve skor; yalniz debug modunda."""
        ascii_state = {'CANDIDATE':'ADAY','DETECTED':'DETECTION','TRACKED':'TRACKING',
                       'TEMPORARILY_LOST':'TEMP LOST','LOST':'LOST'}
        raw = ((candidate.bbox[0]+candidate.bbox[2])/2, (candidate.bbox[1]+candidate.bbox[3])/2)
        box = candidate.filtered_bbox
        out = [(ascii_state.get(candidate.track_state,candidate.track_state or '-')
                +('' if candidate.missed is None else f' kacan={candidate.missed}')
                +('' if candidate.score is None else f' skor={candidate.score:.2f}'))]
        out.append(f'ham=({raw[0]:.3f},{raw[1]:.3f})'+('' if box is None else
                   f' suzulmus=({(box[0]+box[2])/2:.3f},{(box[1]+box[3])/2:.3f})'))
        return out

    def record_loop(self):
        path = self.ledger.path.parent / f'competition-{self.sortie_id}.jsonl'
        with path.open('a', buffering=1) as stream:
            while not self.stop.wait(.2):
                with self.state.lock:
                    body = {'wall_time':time.time(),'monotonic':time.monotonic(),'strategy':self.options.strategy,
                            'actuator':self.options.actuator,'sortie_id':self.options.sortie_id,
                            'tracking':asdict(self.options.tracking),
                            'camera_contract':self.camera_contract,'camera_actual':self.state.camera_info,'frame_id':self.state.frame_id,'frame_at':self.state.frame_at,
                            'detections':[asdict(d) for d in self.state.detections],
                            'candidates':[asdict(c) for c in self.candidates],
                            'diagnostics':self.state.diagnostics,
                            'vision_processing_ms':self.vision_processing_ms,
                            'tracking_ms':self.tracking_ms,
                            'decision':asdict(self.state.decision),'payloads':self.payload_status.copy(),
                            'telemetry':asdict(self.telemetry.snapshot()),
                            'entry_gates_passed':self.controller.route.entry_count,
                            'finish_passed':self.controller.route.finished}
                    if self.options.strategy == 'center':
                        body['decision_input'] = self.decision_input
                        body['fc_messages'] = self.link.snapshot_fc_messages() if self.link else []
                        body['search_speed'] = self.link.snapshot_search_speed_status() if self.link else None
                stream.write(json.dumps(finite_json(body),ensure_ascii=False)+'\n')
