import argparse
import signal
import threading
import time
from pathlib import Path

from ..controller import telemetry_problem
from dataclasses import asdict, replace

from waitress import create_server, wasyncore
from flask import Response, jsonify, request

from ..link_health import LinkHealth
from ..shared import finite_json
from ..opencv_backend import run_opencv_camera
from ..web import create_app
from .config import Options
from .runtime import CompetitionRuntime
from .route import mission_digest


def build_app(cfg, runtime, options, mode, missing):
    """Yarışma paneli: dondurulmuş Görev 1 panelinin üzerine yazılan görünümler."""
    app = create_app(cfg,runtime.state,runtime.telemetry)
    # Görev 1 paneli dondurulmuş kaynaktır; saha linki ölçümü ve kare ETag'i
    # yalnız bu yarışma uygulamasının üzerine eklenir.
    link_health = LinkHealth()
    @app.before_request
    def link_request_started():
        request.environ['safak.started'] = time.monotonic()
    @app.after_request
    def link_request_finished(response):
        started_at = request.environ.get('safak.started')
        if started_at is not None:
            link_health.record(request.remote_addr,request.path,response.status_code,
                               response.content_length or 0,time.monotonic()-started_at)
        return response
    @app.get('/api/link')
    def link_status():
        return jsonify(finite_json(link_health.snapshot()))
    def competition_frame():
        # Değişmeyen kareyi ikinci kez indirmek dar saha linkinde boşa giden yüktür.
        with runtime.state.jpeg_condition:
            if runtime.state.jpeg is None:
                return Response(status=204)
            jpeg,frame_at,frame_id = (runtime.state.jpeg,runtime.state.jpeg_frame_at,
                                      runtime.state.jpeg_id)
        etag = f'"{frame_id}"'
        if request.headers.get('If-None-Match') == etag:
            response = Response(status=304)
        else:
            response = Response(jpeg,mimetype='image/jpeg')
        response.headers['ETag'] = etag
        response.headers['X-Frame-Id'] = str(frame_id)
        response.headers['X-Frame-Age-Ms'] = str(round(max(0,time.monotonic()-frame_at)*1000))
        return response
    app.view_functions['frame'] = competition_frame
    @app.get('/api/competition')
    def competition_status():
        t = runtime.telemetry.snapshot()
        now = time.monotonic()
        with runtime.state.lock:
            decision = runtime.state.decision
            frame_age = now-runtime.state.frame_at
            times = tuple(runtime.state.frame_times)
            vision_fps = (len(times)-1)/(times[-1]-times[0]) if len(times)>1 and times[-1]>times[0] else 0.
            candidates = [asdict(c) for c in runtime.candidates]
        with runtime.state.jpeg_condition:
            panel_frame_id = runtime.state.jpeg_id
        global_age = now-t.global_at
        relative_alt_m = (t.relative_alt_m if t.relative_alt_m is not None
                          and 0 <= global_age <= cfg.control.telemetry_timeout_s else None)
        return jsonify({'strategy':options.strategy,'actuator':options.actuator,
            'profile_digest':runtime.profile_digest,'camera_contract':runtime.camera_contract,'camera_actual':runtime.state.camera_info,'sortie_id':options.sortie_id,
            'mission_digest':mission_digest(runtime.telemetry.mission) if runtime.telemetry.mission else None,
            'state':decision.state, 'reason':decision.reason, 'flight_mode':t.mode,
            'relative_alt_m':relative_alt_m,
            'frame_fresh':0 <= frame_age <= cfg.control.frame_timeout_s,
            'camera_requested_fps':cfg.camera.fps,'vision_fps':vision_fps if frame_age<=cfg.control.frame_timeout_s else 0.,
            'vision_processing_ms':runtime.vision_processing_ms,'candidates':candidates,
            'panel_frame_id':panel_frame_id,'link':link_health.snapshot(),
            'payloads':runtime.payload_status,'entry_gates_passed':runtime.controller.route.entry_count,
            'finish_passed':runtime.controller.route.finished,'missing':missing})
    def competition_health():
        now = time.monotonic()
        ready = (mode == 'flight' and not missing and runtime.state.backend == 'OPENCV'
                 and 0 <= now-runtime.state.frame_at <= cfg.control.frame_timeout_s
                 and not runtime.state.pipeline_error and runtime.link is not None
                 and runtime.link.hardware_problem() is None
                 and runtime.telemetry.preflight_problem() is None
                 and telemetry_problem(runtime.telemetry.snapshot(), now, cfg) is None
                 and runtime.controller.state not in ('ABORTED','PILOT_CONTROL','DONE','INCOMPLETE'))
        return jsonify({'service':'safak-competition','panel':'ok','mode':mode,
                        'flight_ready':ready,'actuator':options.actuator})
    app.view_functions['health'] = competition_health
    # Eski panelin tek kırmızı yük anlatımı yarışma arayüzüne taşınmaz.
    @app.get('/competition')
    def competition_page():
        return ('<!doctype html><html lang="tr"><meta charset="utf-8"><title>ŞAFAK İki Renk</title>'
                '<style>body{font:20px system-ui;background:#111827;color:#f9fafb;margin:24px}'
                'img{max-width:100%}#phase{font-size:32px;font-weight:bold}p{max-width:960px}</style>'
                '<h1>ŞAFAK — iki renkli görev</h1><p>Mavi hedef → kırmızı yük; kırmızı hedef → mavi yük.</p>'
                '<div id="phase">Panel bağlantısı bekleniyor</div><p id="reason"></p>'
                '<p id="mode"></p><p id="altitude">İrtifa (HOME): —</p><p id="payloads"></p>'
                '<p id="link">Link: —</p><p id="linkwarn" style="color:#fca5a5"></p>'
                '<p>ACK/PWM komut kanıtıdır; fiziksel yük düşüşü doğrulanmaz.</p>'
                '<img src="/frame.jpg" id="video" width="960">'
                '<script src="/competition.js"></script></html>')
    @app.get('/competition.js')
    def competition_script():
        from flask import Response
        return Response('''
const labels = {WAIT_AUTO:"AUTO bekleniyor", SEARCHING:"Hedef aranıyor", SET_SEARCH_SPEED:"Ana tarama hızı ayarlanıyor",
  REQUEST_STOP:"Durma isteniyor", STOPPING:"Frenleniyor", VERIFYING:"Hedef doğrulanıyor",
  INTERCEPT:"Merkezleme başlıyor", CENTERING:"Hedefe merkezleniyor", DESCENDING:"Alçalıyor",
  RELEASE_WAIT:"Yük komutu bekleniyor", CLIMB:"Tarama irtifasına çıkıyor",
  RESUME_SELECT:"Kesilen waypoint seçiliyor", RESUME_AUTO:"Rotaya dönüyor",
  SELECT_LAND:"İki yük tamam; LAND waypointi seçiliyor", HANDOFF_LAND:"AUTO inişine devrediliyor",
  LANDING:"LAND waypointine iniyor",
  AUTO_FINISH:"Bitiş ve iniş rotası", PILOT_CONTROL:"Kontrol pilotta",
  ABORTED:"Görev durduruldu", DONE:"Görev kaydı tamamlandı", INCOMPLETE:"Görev eksik tamamlandı",
  OBSERVING:"Yalnız gözlem; hareket ve bırakma kapalı"};
const el = id => document.getElementById(id);
const BASE_MS = 250, MAX_MS = 2000;
let wait = BASE_MS, failures = 0, shownFrame = null;
const kbit = bps => (Number(bps||0)/1000).toFixed(0)+" kbit/s";
// Zayıf linkte sabit 4 Hz istek yığılma yapar: hata oldukça aralık büyür,
// ilk başarılı yanıtta tekrar 250 ms'ye döner. Kare yalnız değiştiyse istenir.
async function tick(){
  const began = performance.now();
  try {
    const r = await fetch("/api/competition", {cache:"no-store", signal:AbortSignal.timeout(1500)});
    if (!r.ok) throw Error("HTTP");
    const s = await r.json();
    const rtt = Math.round(performance.now()-began);
    failures = 0; wait = BASE_MS;
    el("phase").textContent = labels[s.state] || s.state;
    el("reason").textContent = s.reason;
    el("mode").textContent = "Uçuş modu: "+s.flight_mode+" · "+(s.frame_fresh ? "Görüntü güncel" : "Görüntü güncel değil");
    el("mode").textContent += " · İşlenen: "+Number(s.vision_fps||0).toFixed(1)+" FPS / kamera isteği: "+s.camera_requested_fps;
    el("altitude").textContent = "İrtifa (HOME): "+(Number.isFinite(s.relative_alt_m) ? Number(s.relative_alt_m).toFixed(1)+" m" : "—");
    el("payloads").textContent = "Kırmızı yük: "+(s.payloads.kirmizi || "Bekliyor")+
      " · Mavi yük: "+(s.payloads.mavi || "Bekliyor")+
      (s.actuator === "simulated" ? " · TEMSİLİ BIRAKMA" : " · GERÇEK SERVO");
    const link = s.link || {};
    const wifi = link.wifi, iface = link.interface;
    el("link").textContent = "Link: RTT "+rtt+" ms · panel "+kbit(link.served_bps)+
      (iface ? " · Pi WiFi gönderim "+kbit(iface.tx_bps) : "")+
      (wifi ? " · sinyal "+wifi.signal_dbm+" dBm" : "");
    let warn = "";
    if (iface && iface.tx_bps > 1e6 && link.panel_share_of_tx !== null && link.panel_share_of_tx < .5)
      warn = "UYARI: Linki paylaşan başka bir akış var (uzak masaüstü/NoMachine?); panel bandın küçük kısmını kullanıyor.";
    else if (wifi && wifi.signal_dbm <= -75) warn = "UYARI: WiFi sinyali zayıf ("+wifi.signal_dbm+" dBm).";
    el("linkwarn").textContent = warn;
    if (s.panel_frame_id && s.panel_frame_id !== shownFrame){
      shownFrame = s.panel_frame_id;
      el("video").src = "/frame.jpg?f="+shownFrame;
    }
  } catch(e) {
    failures += 1;
    wait = Math.min(MAX_MS, BASE_MS*Math.pow(2,failures));
    el("phase").textContent = "Pi paneline erişilemiyor; araç durumu bilinmiyor";
    el("reason").textContent = ""; el("mode").textContent = ""; el("altitude").textContent = "İrtifa (HOME): —"; el("payloads").textContent = "";
    el("link").textContent = "Link: yanıt yok ("+failures+" deneme, "+wait+" ms aralık)";
  } finally { setTimeout(tick, wait); }
}
tick();
''',
            mimetype='application/javascript')
    # Varsayılan açılış da iki renk paneline gider.
    app.view_functions['index'] = competition_page
    return app, link_health


def main():
    parser = argparse.ArgumentParser(description='ŞAFAK — yalnız OpenCV renk/dörtgen kullanan iki hedef görevi')
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--task', choices=('ana','hizli'), help='Ana merkezleme veya durup bırakan hızlı görev')
    selection.add_argument('--config', help='Bu iki görevden biri için sahada doldurulmuş profil')
    parser.add_argument('--mode', choices=('observe','flight'), default='observe')
    parser.add_argument('--check', action='store_true', help='Dosyaları denetle; kamera/USB/servo açma')
    args = parser.parse_args()
    path = args.config or str(Path(__file__).resolve().parents[2]/'config'/f'{args.task}-gorev.json')
    try:
        cfg, options = Options.load(path)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error('Profil açılamadı; yalnız ana/hizli görev destekleniyor: '+str(error))
    missing = options.missing(cfg)
    if args.check:
        import json
        from ..camera_contract import camera_manifest
        print(json.dumps(camera_manifest(cfg.camera), ensure_ascii=False, indent=2))
        print(f'Strateji: {options.strategy}; aktüatör: {options.actuator}; sortie: {options.sortie_id}')
        print('Rota: yalnız mission_digest(); MissionPlan.fingerprint kabul edilmez. --check canlı rota okumaz.')
        print('Eksik: '+('; '.join(missing) if missing else 'yok; canlı doğrulama ayrıca gerekli'))
        return 2 if missing else 0
    if args.mode == 'flight' and missing:
        parser.error('Uçuş yapılandırması eksik: '+'; '.join(missing))
    runtime = CompetitionRuntime(cfg,args.mode,options)
    if args.mode == 'flight' and runtime.payload_status:
        runtime.close()
        parser.error('Bu sortie_id için yük kaydı var. Yeni yükleme doğrulanmadan kimliği değiştirmeyin.')
    app, link_health = build_app(cfg,runtime,options,args.mode,missing)
    def shutdown(*_):
        runtime.stop.set()
    signal.signal(signal.SIGINT,shutdown)
    signal.signal(signal.SIGTERM,shutdown)
    sockets = {}
    # Kopan saha linkinde yarım kalan bağlantı varsayılan 120 s yerine 20 s'de
    # kapanır; yer istasyonu yeniden bağlanınca sıra beklemez.
    server = create_server(app,host=cfg.web.host,port=cfg.web.port,map=sockets,threads=4,
                           channel_timeout=20,connection_limit=24)
    def serve():
        sampled = 0.
        try:
            while not runtime.stop.is_set():
                wasyncore.loop(timeout=.2,count=1,map=sockets,use_poll=server.adj.asyncore_use_poll)
                if time.monotonic()-sampled >= 1.:
                    sampled = time.monotonic()
                    link_health.sample_interface()
        finally:
            server.task_dispatcher.shutdown(timeout=2)
            wasyncore.close_all(sockets)
    thread = threading.Thread(target=serve,daemon=True)
    thread.start()
    runtime.start()
    camera_gate_thread = None
    if args.mode == 'flight':
        print('Zorunlu ön kontrol: canlı rota iki kez okunuyor; servo nötrü ve DISARM doğrulanıyor...',
              flush=True)
        problem = runtime.wait_for_flight_preflight()
        if problem:
            runtime.fail_preflight(problem)
            runtime.close()
            thread.join(timeout=3)
            return 2
        print('Rota/servo/DISARM tamam; kamera ilk taze karesi bekleniyor. Henüz ARM etmeyin.', flush=True)
        def open_camera_gate():
            camera_problem = runtime.wait_for_camera_preflight()
            if camera_problem:
                runtime.fail_preflight(camera_problem)
                return
            print('UÇUŞ ÖN KONTROLÜ TAMAM: ROTA İKİ KEZ EŞ / SERVO NÖTR / KAMERA AKTİF / DISARM. '
                  'Mission Planner rotasını artık değiştirmeyin; şimdi ARM/AUTO yapılabilir.', flush=True)
        camera_gate_thread = threading.Thread(target=open_camera_gate, name='flight-preflight', daemon=True)
        camera_gate_thread.start()
    print(f'Görev: {"ANA" if options.strategy == "center" else "HIZLI"} / {options.actuator}; panel portu {cfg.web.port}',flush=True)
    failed = False
    try:
        run_opencv_camera(cfg,runtime.mailbox,runtime.state,runtime.stop)
    except Exception as e:
        failed = True
        runtime.state.pipeline_error = str(e)
        if runtime.link:
            runtime.link.failure = str(e)
        print(f'HATA: {e}',flush=True)
    finally:
        failed = failed or runtime.flight_preflight_failure is not None
        runtime.close()
        if camera_gate_thread:
            camera_gate_thread.join(timeout=2)
        thread.join(timeout=3)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
