"use strict";
const $ = id => document.getElementById(id);
const names = {STARTING:"Başlatılıyor",WAIT_AUTO:"AUTO bekleniyor",SEARCHING:"Mavi hedef aranıyor",REQUEST_RTL:"RTL onayı bekleniyor",RTL_RETURN:"Kalkış yerine dönüş",REQUEST_GUIDED:"Hedef doğrulandı",CENTERING:"Merkezleniyor",DESCENDING:"Alçalma ve kilit",RELEASE_PENDING:"Temsili bırakma",RETURN_CLIMB:"Arama irtifasına çıkış",RETURN_TRANSIT:"Son LAND'e geçiş",SELECT_LAND:"LAND seçiliyor",HANDOFF_LAND:"AUTO'ya devir",LANDING:"Otonom iniş",DONE:"Test tamamlandı",ABORTED:"Test durduruldu",PILOT_CONTROL:"Kontrol pilotta",OBSERVING:"Gözlem modu"};
const number = (v, digits=1) => typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "—";
const metric = (id,v,unit,digits=1) => { const el=$(id); el.replaceChildren(document.createTextNode(number(v,digits)+" "));const em=document.createElement("em");em.textContent=unit;el.append(em); };
let lastStatus=0,lastImage=0,lastImageId=null,lastImageAge=Infinity,imageUrl=null;
const started=performance.now();
function render(s){
  lastStatus=performance.now(); const t=s.telemetry, a=s.ages_s, d=s.decision;
  const fresh = key => typeof a[key] === "number" && a[key] >= -0.05 && a[key] < (key==="heartbeat"?1.5:["position","attitude","global","rc"].includes(key)?0.6:2);
  $("run-kind").textContent=s.mode==="demo"?"SENTETİK DEMO":s.mode==="flight"?"QUAD · TEMSİLİ YÜK":"GÖZLEM · UÇUŞ KOMUTU YOK";
  $("demo-banner").classList.toggle("hidden",s.mode!=="demo");
  $("link-status").textContent=fresh("heartbeat")?"PIXHAWK BAĞLI":"PIXHAWK GÜNCEL DEĞİL";
  $("link-status").className="pill "+(fresh("heartbeat")?"green":"amber");
  $("state").textContent=names[d.state]||d.state;
  $("reason").textContent=d.reason;
  $("backend").textContent=s.backend;$("fps").textContent=number(s.vision_fps)+" FPS";
  $("geometry").textContent=s.pipeline_error||s.geometry_reason;
  $("lock-time").textContent=number(d.lock_s)+" / "+number(d.lock_required_s)+" sn";
  $("lock").value=d.lock_required_s?Math.min(1,d.lock_s/d.lock_required_s):0;
  metric("error",a.frame!==null&&a.frame<0.3?d.error_m:null,"m",2);
  metric("visual-height",a.frame!==null&&a.frame<0.3?d.camera_height_m:null,"m",2);
  $("flight-mode").textContent=fresh("heartbeat")?t.mode:"—";
  $("armed").textContent=fresh("heartbeat")?(t.armed?"ARM · MOTORLAR ETKİN":"DISARM"):"Veri güncel değil";
  metric("relative-alt",fresh("global")?t.relative_alt_m:null,"m");
  metric("speed",fresh("position")?Math.hypot(t.vn,t.ve):null,"m/s",2);
  $("vertical-speed").textContent="Düşey "+number(fresh("position")?-t.vd:null,2)+" m/s · ↑ pozitif";
  metric("battery",fresh("battery")?t.voltage:null,"V");
  $("battery-extra").textContent=number(fresh("battery")?t.current:null)+" A · "+number(fresh("battery")?t.battery_percent:null,0)+" %";
  $("gps").textContent=fresh("gps")?number(t.satellites,0)+" uydu":"—";
  $("gps-extra").textContent="HDOP "+number(fresh("gps")?t.hdop:null,2)+" · EKF "+(fresh("ekf")&&(t.ekf_flags&23)===23?"HAZIR":"—");
  $("attitude").textContent=fresh("attitude")?number(t.roll*180/Math.PI)+"° / "+number(t.pitch*180/Math.PI)+"°":"—";
  $("heading").textContent="Başlık "+number(fresh("attitude")?(t.yaw*180/Math.PI+360)%360:null,0)+"°";
  $("rc-mode").textContent=fresh("rc")?(t.rc_selected_mode||"—"):"Güncel değil";
  $("firmware").textContent=t.firmware||"—";$("telem-age").textContent=number(a.heartbeat===null?null:a.heartbeat*1000,0)+" ms";
  $("uptime").textContent=Math.floor(s.uptime_s/60)+" dk "+Math.floor(s.uptime_s%60)+" sn";
  $("preflight").textContent=s.preflight||"Görev ve bağlantı denetimleri hazır.";
  $("mission-seq").textContent=fresh("mission")?(t.mission_seq??"—"):"—";$("land-seq").textContent=s.mission?.land_seq??"—";
  if(s.release){$("release").className="release complete";$("release-title").textContent="KIRMIZI YÜK TEMSİLİ OLARAK BIRAKILDI";$("release-detail").textContent=new Date(s.release.at*1000).toLocaleTimeString("tr-TR")+" · Bir kez kaydedildi · Fiziksel servo yok";$("release").querySelector(".release-symbol").textContent="✓";}
  else{$("release").className="release pending";$("release-title").textContent="Temsili bırakma bekleniyor";$("release-detail").textContent="Fiziksel servo komutu gönderilmez.";$("release").querySelector(".release-symbol").textContent="○";}
  const rows=s.events.map(e=>{const li=document.createElement("li"), tm=document.createElement("time"),span=document.createElement("span");tm.textContent=new Date(e.at*1000).toLocaleTimeString("tr-TR");span.textContent=e.message;li.append(tm,span);if(e.kind==="SIMULATED_RELEASE")span.className="green";return li;});
  if(rows.length)$("events").replaceChildren(...rows);
}
async function statusLoop(){try{const r=await fetch("/api/status",{cache:"no-store",signal:AbortSignal.timeout(1500)});if(r.ok)render(await r.json());}catch{}setTimeout(statusLoop,250);}
async function videoLoop(){
 try{const r=await fetch("/frame.jpg",{cache:"no-store",signal:AbortSignal.timeout(1500)});
  if(r.status===200){const id=r.headers.get("X-Frame-Id"),age=Number(r.headers.get("X-Frame-Age-Ms"));
   if(id!==lastImageId){const blob=await r.blob(),next=URL.createObjectURL(blob);$("video").src=next;$("video").style.display="block";$("video-wait").classList.add("hidden");if(imageUrl)URL.revokeObjectURL(imageUrl);imageUrl=next;lastImage=performance.now();lastImageId=id;lastImageAge=age;$("frame-id").textContent="KARE "+id;}
  }
 }catch{}
 setTimeout(videoLoop,1000/Number(document.body.dataset.videoFps));
}
setInterval(()=>{const now=performance.now(),age=lastImageAge+(now-lastImage);$("clock").textContent=new Date().toLocaleTimeString("tr-TR");$("offline").classList.toggle("hidden",(lastStatus?now-lastStatus:now-started)<2000);$("video-stale").classList.toggle("hidden",!lastImage||age<700);$("frame-age").textContent=number(lastImage?age:null,0)+" ms";if(lastStatus&&now-lastStatus>2000){$("link-status").textContent="PİXHAWK DURUMU BİLİNMİYOR · PANEL VERİSİ YOK";$("link-status").className="pill amber";$("lock").value=0;$("lock-time").textContent="Güncel değil";}},100);
statusLoop();videoLoop();
