from dataclasses import asdict
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


class CompetitionRuntime(Runtime):
    def __init__(self, cfg, mode, options):
        super().__init__(cfg, mode)
        self.options = options
        self.controller = DualController(cfg, options)
        self.payload_ledger = PayloadLedger(Path(cfg.runtime_dir).parent/'payload-ledger', options.sortie_id or 'observe')
        self.candidates = ()
        self.processed_frame = None
        self.payload_status = self.payload_ledger.statuses()
        self.state.mode = mode

    def start(self, connect=True):
        if connect:
            self.link = CompetitionLink(self.cfg, self.telemetry, self.mode == 'flight', self.stop,
                                        self.options, self.payload_ledger)
            self.link.start()
        super().start(connect=False)

    def vision_loop(self):
        calibration = (Calibration.load(self.cfg.camera.calibration_file)
                       if self.options.strategy == 'center' and self.cfg.camera.calibration_file
                       and self.cfg.camera.offset_body_m is not None else None)
        vision = DualVision(self.cfg, calibration)
        last = -1
        while not self.stop.is_set():
            frame = self.mailbox.get_after(last)
            if frame is None:
                continue
            last = frame.id
            pose = self.telemetry.pose_at(frame.captured_at, self.cfg.control.exposure_sync_tolerance_s)
            candidates, diagnostics = (), []
            if 0 <= time.monotonic()-frame.captured_at <= self.cfg.control.frame_timeout_s:
                candidates, diagnostics = vision.detect(frame, pose, self.options.strategy)
            with self.state.lock:
                self.processed_frame = frame
                self.candidates = candidates
                self.state.vision(frame, tuple(x.metric for x in candidates if x.metric),
                    'İki renk / '+self.options.strategy+'; bırakma için uçuş/rota doğrulaması ayrıca gerekli', diagnostics)

    def control_loop(self):
        previous = None
        interval = 1/self.cfg.control.rate_hz
        while not self.stop.is_set():
            now = time.monotonic()
            t = self.telemetry.snapshot()
            with self.state.lock:
                fid, at, _ = self.state.vision_snapshot()
                candidates = self.candidates
            if self.link:
                self.payload_status = self.link.snapshot_status()
            if self.mode == 'observe':
                decision = Decision('OBSERVING', 'İki renk izleniyor; uçuş ve servo komutu kapalı')
            else:
                problem = self.state.pipeline_error or self.telemetry.preflight_problem()
                if self.link:
                    problem = problem or self.link.hardware_problem()
                decision = self.controller.step(now, t, candidates, fid, at, self.telemetry.mission,
                                                problem, self.payload_status)
                if self.link:
                    self.link.route_authorized = self.controller.route.entered and not self.controller.route.finished
                    self.link.submit(decision.actions)
            with self.state.lock:
                self.state.decision = decision
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
            frame = self.mailbox.get_after(last)
            if frame is None:
                continue
            last = frame.id
            image = frame.image.copy()
            h,w = image.shape[:2]
            for d in frame.detections:
                if len(d.bbox) != 4 or not all(isinstance(v,(int,float)) and 0 <= v <= 1 for v in d.bbox):
                    continue
                x1,y1,x2,y2 = [round(v*size) for v,size in zip(d.bbox,(w,h,w,h))]
                color = (255,120,0) if d.label == 'mavi_hedef' else (0,60,255)
                cv2.rectangle(image,(x1,y1),(x2,y2),color,2)
                cv2.putText(image,f'AI {d.label} {d.confidence:.2f}',(max(0,x1),max(22,y1-8)),
                            cv2.FONT_HERSHEY_SIMPLEX,.6,color,2)
            lines = [self.options.strategy+' / '+self.options.actuator+' / '+self.state.decision.state,
                     'KIRMIZI YUK: '+self.payload_status.get('kirmizi','BEKLIYOR'),
                     'MAVI YUK: '+self.payload_status.get('mavi','BEKLIYOR'),
                     'ACK/PWM = komut kaniti; fiziksel dusus sensoru YOK']
            cv2.rectangle(image,(0,h-110),(w,h),(20,20,20),-1)
            for i,line in enumerate(lines):
                cv2.putText(image,line,(12,h-88+i*24),cv2.FONT_HERSHEY_SIMPLEX,.55,(230,230,230),1)
            width = min(w,self.cfg.web.width)
            image = cv2.resize(image,(width,round(h*width/w)))
            ok, encoded = cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,self.cfg.web.jpeg_quality])
            if ok:
                self.state.jpeg_put(encoded.tobytes(),frame.captured_at,frame.id)
            self.stop.wait(1/self.cfg.web.fps)

    def record_loop(self):
        path = self.ledger.path.parent / f'competition-{self.sortie_id}.jsonl'
        with path.open('a', buffering=1) as stream:
            while not self.stop.wait(.2):
                with self.state.lock:
                    body = {'wall_time':time.time(),'monotonic':time.monotonic(),'strategy':self.options.strategy,
                            'actuator':self.options.actuator,'frame_id':self.state.frame_id,'frame_at':self.state.frame_at,
                            'detections':[asdict(d) for d in self.state.detections],
                            'candidates':[asdict(c) for c in self.candidates],
                            'decision':asdict(self.state.decision),'payloads':self.payload_status.copy(),
                            'telemetry':asdict(self.telemetry.snapshot()),
                            'entry_gates_passed':self.controller.route.entry_count,
                            'finish_passed':self.controller.route.finished}
                stream.write(json.dumps(finite_json(body),ensure_ascii=False)+'\n')
