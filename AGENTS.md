# ŞAFAK UAV — Proje bağlamı ve çalışma kuralları

## 8 Eylül 07:00 — canlı Hailo güncellemesi

Pi `172.20.10.2` aynı SSH kimliğiyle kontrol edildi. Hailo aygıtı/model çıkarımı çalışıyor; sürücü4.20.0 `find_vma` uyarısına resmî kaynakta bulunan iki satır mmap kilidi düzeltmesi uygulandı, çalışan kernel için DKMS yeniden kuruldu. Son40s gerçek kamera testi1174kare/~30FPS/hatasız/yeni kernel uyarısı0. Önceki PCIe kopmasının nedeni veya uzun vadeli çözümü kanıtlanmadı. Kamera/görev/panel kapalı; HailoRT servisi aktif. FC/MAVLink/servo komutu yok; mekanizma henüz takılı değil. Yeni montaj revizyonu hâlâ Pi'ye aktarılmadı. Ayrıntı `docs/HANDOFF.md`, `artifacts/pi/hailo-driver-fix-20260908/REPORT.md`. Kullanıcının yeni kalibrasyon ortamı/zamanı yok; saha rotası yarışma anında Mission Planner'dan girilecek, şimdi koordinat istemeyin.

## 8 Eylül — güncel kamera montajı

Kullanıcı doğruladı: lens yere bakıyor, görüntü üstü drone'un arkasında (180°); lens merkezi Pixhawk'tan 11 cm ileri, 5 cm aşağıda, sağ/sol sıfır. Ana/hızlı profillerde FRD `[0.11,0,0.05]` m ve `camera_mount_yaw_deg=180` yerelde işlendi. Eski geometri değişmeden ayrı `competition/geometry.py` uyarlaması kullanılıyor. 101 ilgili test geçti; yeni revizyon Pi'ye aktarılmadı. Montaj kullanıcı beyanı, fiziksel yön/mesafe doğrulaması değil. Ana IMX708 kalibrasyonu, servo PWM, saha/rota ve Hailo canlı kontrolü açık; ayrıntı `docs/HANDOFF.md` ve `docs/competition/EKSIKLER.md`. Aşağıdaki eski “hex ofseti bilinmiyor” kayıtları tarihli geçmiş oldu.

## Son açık kullanıcı kararı — yalnız ana ve hızlı görev

7 Eylül2026 son talep: “MOSSE'siz hızlı görevi yaz, diğer üç eski seçeneği kaldır.” Önceki yalnız mavi girişi koruma talebi bu açık kaldırma isteğiyle giriş/profiller açısından güncellendi. Günlük seçimler yalnız `--task ana` (`config/ana-gorev.json`, center) ve `--task hizli` (`config/hizli-gorev.json`, quick). Hızlı görev0,10s gör→GUIDED dur→duruştan sonra0,10s taze AI doğrula→merkezleme/alçalma olmadan bırak→aynı AUTO waypoint; MOSSE yok. Ana dur–doğrula/merkezleme korunuyor. Eski quad girişi donanım açmadan hata verir; eski saha/competition-center/competition-sighting profilleri arşivlendi, sighting stratejisi kaldırıldı. `archive/legacy-options/` özgün `.txt` kopyaları ve hashleri içerir. Ortak merkezleme/geometri yordamları silinmedi. `README.md`/`docs/competition/AKIS.md` güncel iki seçenek kılavuzudur; aşağıdaki eski başlatma komutlarını güncel sanmayın. Pi'ye aktarım yapılmadı; canlı donanım ve uçuş hazırlığı doğrulanmadı. En son testler ve açık işler HANDOFF.md/TESTLER.md içinde.

Son güncelleme: 7 Eylül 2026.
Bu dosya, kullanıcının açık isteğiyle yeni proje sohbetlerine bağlam aktarmak için oluşturuldu. Sohbetin birebir dökümü değildir; güncel kararları, kaynakları ve bilinmeyenleri korur. Dosyadaki tarihli bilgiler daha sonra doğrulanan bilgilerle güncellenmelidir.

## EN GÜNCEL — hesap devri ve IMX708, 7 Eylül 2026

**Önce `docs/HANDOFF.md` dosyasını oku.** Bu kısa devir notu, aşağıdaki uzun tarihçeden daha güncel durum ve okuma sırasını verir. Türkçe/kısa yanıt ver; kullanıcıdan projeyi baştan anlatmasını isteme. Mevcut yalnız mavi merkezleme koduna dokunma.

Kullanıcı IMX219'un tamamen kırıldığını, tek seçeneğin IMX708 olduğunu bildirdi. IMX219'a dönüş artık seçenek değildir. Kullanıcı IMX708 kalibrasyonunu yapılmamış olarak tanımladı; dosya kontrolünde5Eylül IMX708 aday matrisi ve kaynakları mevcut bulundu. Bu adayın güncel fiziksel kamera/odak/crop/montaj için geçerliliği bilinmiyor; saha metrik doğrulaması yok. `competition-base.json` hâlâ IMX219 adayı içeriyor; IMX708 merkezlemesine hazır sayılmamalı. Bu güncellemede profil/kod veya gerçek araç değiştirilmedi. 119test/5hexSITL senaryosu geçti; görüntü ve AI kutuları sentetik, gerçek Hailo/kamera/servo uçuş doğrulaması değildir. Ayrıntılar `docs/HANDOFF.md`, `docs/competition/TESTLER.md`. Gazebo kurulmadı; canlı Pi/kamera/ARM bilgisi yeniden okunmalı.

## 7 Eylül — ayrı iki renkli yarışma yazılımı

Kullanıcı mevcut yalnız mavi merkezleme akışının değiştirilmemesini, ayrıca iki renkli merkezleme ve hedef görünce bırakma alternatifi istedi. Yeni paket `safak_gorev2/competition/`; profiller `config/competition-center.json`, `config/competition-sighting.json`, ortak `competition-base.json`. Eski kod/profil içerikleri `docs/competition/legacy-sha256.json` ile korunuyor. Yeni akışlar AUTO TAKEOFF ve sahada tanımlanacak sıralı giriş kapıları/tarama bölümü sonrası iki karşı renkli yükü tek sefer sürer; merkezleme sonrası kesilen AUTO waypoint'e döner, normal bitiş/LAND rotasını atlamaz. Hızlı akış PnP/merkezleme kullanmaz, varsayılan 3 bağımsız kare/en az0,10s doğrulama kullanır; kamera hiç tespit üretemezse çalışmaz. Varsayılan observe/simulated; gerçek sürücü ayrı servo seçeneği, kalıcı yük defteri ve ACK+çıkış PWM takibi içerir. ACK fiziksel düşüş/isabet kanıtı değildir.

Kullanıcı güncel beyanı: yarışma hexacopter; kırmızı yük AUX1, mavi yük AUX2; başlangıç180°, bırakma90°. Yeni profilde MAVLink çıkışları9/10, fakat gerçek bırakma PWM değerleri bilinmiyor (`null`), tezgâh doğrulamasıfalse. Hexacopter kamera FRD ofseti ve gerçek saha rota/kapı/alan koordinatları bilinmediğinden boş bırakıldı; quad ofseti hex'e taşınmadı. Pi'ye dağıtım, gerçek kamera/USB/servo çalıştırma veya uçuş başlatma yapılmadı. Kullanım ve kesin test sonuçları `docs/competition/KULLANIM.md`, `TESTLER.md`; simülasyon sonuçları gerçek araç kabulü değildir. Yalnız yük bırakmak puan garantisi değildir; V6 resmî şartname tekrar kontrol edildi.

5 Eylül19:31 güncellemesi: kullanıcı waypointleri15m yaptığını bildirdi; canlı API seq1–6 z=15, sonLANDseq7 z=0 doğruladı. Uygulama9m kamera yüksekliği hedefi değişmedi. Kaydedici2710 aynı oturumda897 kare/0hata, taze kayıt; flight/WAIT_AUTO/preflightnull, son okuma DISARM/LOITER/landed1. Kullanıcı kalkış/AUTO yapacağını bildirdi; bu okumada kalkış henüz görülmedi.

## 6 Eylül IMX219'a dönüş düzeltildi

Kullanıcı eski kamerayı taktığını doğruladı. Aktifflight2535 hâlâIMX708profilini kullanıyor, kamera başlamıyordu. CanlıDISARM/landed1 doğrulanıp recorder2608 ve başarısızflight2535 temiz kapatıldı. Ayrı config/flight-imx219-new-model.json oluşturuldu: IMX219camera.field-candidate kalibrasyonu, lens_position/sensor_output_size override yok; yeni safakyepyeni.hef hashaynı,acquire0,5/skor0,4/9mhedef aynı. Kısa GÖZLEM2676 ile IMX2191280x720 crop[680,692,1920,1080] kalibrasyonla eşleşti,30FPS,tazeilerleyenframe/HAILO/hatasızkamera/modelhash doğrulandı. Ardından GÖZLEM temiz kapatıldı; kullanıcı kendi flight ve recorder komutlarını yeni profille başlatacak. Uçuşbaşlatılmadı. SonGPS0uyduHDOP99,99/yerelkonumyok; uçuşahazır değil. Önceki an5uyduHDOP11,56idi. Kanıt artifacts/field/imx219-return-20260906/status.json. Montajofseti öncekinominaldeğer; fizikselmontaj tekrar ölçülmedi.


## 6 Eylül — Pi HEF dosyası yeniden adlandırılmış

Kullanıcı modelin aynı klasörde adını değiştirdiğini bildirdi. Pi best_hailo_model/safakyepyeni.hef bulundu; SHA2568433d13e... önceki best.hef ile birebir eşleşti. Yalnız Pi config/flight-imx708.json hef_file yeni ada güncellendi; acquire0,5 korunuyor. Pi profil hash239d7eee293b70236015a1c0860921a2e02f672012a35ff056c3385237020e27, yedek runtime/flight-before-model-rename-1788685516910033871.json. Mac kanıt artifacts/field/acquire-050-20260906/pi-flight-renamed-model.json. Yerel ana profil/model adı best.hef olarak kaldı; Pi'ye eski yolu tekrar dağıtma. Uygulama yeniden başlatılmadı; kullanıcı mevcut hata veren terminali yerdeCtrl+C ile kapatıp aynı launcher komutuyla yeniden açacak.


## 6 Eylül güncel — yeni ağ ve ilk kilit0,5s

Kullanıcı access point IP192.168.137.191 bildirdi; SSH furkan ile doğrulandı. Görev/kayıt süreci görülmedi, localhost8080 kapalı. Yalnız config/flight-imx708.json control.acquire_s varsayılan0,8→açık0,5 yazıldı;6bağımsızkare/center1,5s/release3s/eşik0,4 aynı. Pi yedeği runtime/flight-imx708-before-acquire050-1788684980923134676.json. Pi Config.load ile geri okundu; Mac/Pi SHA256033f418e82cb453f0ebeb3972e6071aa3f547dafe683d27c3383950aa17d5338 eşleşti;23controller/manualtakeoff test geçti. Kanıt artifacts/field/acquire-050-20260906/. Kamera lens değeri hâlâ0,10627710819244385, kullanıcının otomatik odağı kapatma açıklaması yeni uzaknetlik kanıtı sayılmadı. Uygulama/kayıt/kamera/MAVLink başlatılmadı, FC/mod/rota yazılmadı. Kullanıcı NoMachine üzerinden kendisi başlatacak; komutlar aynı.


## Son video incelemesi — kayıtlar Mac’e alındı

Pi yeniden açılınca yalnız salt okunur kayıt alımı yapıldı, uygulama/uçuş başlatılmadı. artifacts/field/video-review/ altında19:31uçuşuseg5/6,19:40uçuşuseg3 ve eşleme/telemetri;6dosya hash eşleşti. Görsel incelemede gerçek mavi branda üzerindeki kutular doğrulandı; branda görünürken tespit aralıklı, belirgin değişken bulanıklık mevcut. Titreşim tek başına kanıtlanmadı; ExposureTime/gain kaydedilmedi. Sabit lens kontrolü var ama uzak netliği bundan garanti edilemez. Sonuç/örnekler REPORT.md/contact.jpg/examples.jpg. GUIDED kilidini aralıklı geçerli hedefler tamamlamıyor. Eşik/odak/FC/kontrol değiştirilmedi. Yeniden açılış sonrası öncekiPID2418/2490 canlı sayılmaz.


## Son durum — 19:49 bağlantı ayrımı ve yeni oturum

Kullanıcı yerde DISARM olduğunu bildirince canlı doğrulandı. panel.js HTTP2s kesilmesini aynı Pixhawk göstergesinde BAĞLANTI YOK diye yazıyordu; yerel ve Pi panel metinleri tarayıcı–Pi kaybı ile bilinmeyen Pixhawk durumunu ayıracak şekilde güncellendi. Yedek runtime/before-link-label/. Kontrol/eşik/model/FC parametresi değişmedi.78test geçti4Torch atlandı; JS syntax geçti.

Son19:40 kaydında235ARM/64AUTO örneği, heartbeat max0,928s ve link_error0. AUTO~12,61s,5geçerli hedefli örnek, kilit tamamlanmadan pilot müdahalesi.19:31 kaydında da464ARM boyunca heartbeat<1s. Radyo telemetri ve hotspot sorunlarının nedeni doğrulanmadı; USB kopması gösterilmedi. Rapor artifacts/field/link-diagnosis/REPORT.md.

Yerde recorder2349/flight2277 temiz kapatılıp yeni flight2418 ve recorder2490 açıldı. Yeni kayıt runtime/recordings/20260905T164803Z-2490;19:49:32 itibarıyla705kare/0hata. SonAPI DISARM/LOITER/landed1 WAIT_AUTO, USB/kamera taze/link_errornull,batarya11,749V,GPS10uydu/HDOP1,15,EKF33599. Güncel bağlantı örneği artifacts/field/link-diagnosis/live.txt. Uzaktaki SSH yeniden gecikiyor; radyo/hotspot giderilmiş veya tüm uçuş hazırlığı tamamlanmış denmedi. Süreçler sonraki işlemde tekrar okunmalı. ARM/mod/rota gönderilmedi.


## Son durum — 19:39 batarya sök/tak sonrası

Kullanıcı yeniden başlattı. Pi uptime<1dk, USB Pixhawk mevcut; önceki süreçler yok. Tek USB okuyucuyla DISARM/LOITER ve WPNAV_SPEED150, RTL_SPEED0, FS_THR_ENABLE1 okundu; FC parametresi değiştirilmedi. GÖZLEM2193 ile taze yer kontrolü ve altı15m waypoint/sonLAND doğrulandı. Ardından yerde temiz kapatılıp flight2277 ve kaydedici2349 açıldı: runtime/recordings/20260905T163839Z-2349.185kare/0hata, WAIT_AUTO/boşactions, preflight/pipeline/link_error null, DISARM/LOITER/landed1, GPS12/HDOP0,87/EKF831/RCsağlıklı,11,871V. IMX708/yeniHEF/eşik0,4/9mhedef aynı. ARM/mod/rota komutu gönderilmedi. Kanıt artifacts/field/imx708-reboot-preparation/.

Önceki 20260905T162900Z-2710 telemetry.jsonl hızlı taramasında kaydedilmiş link_error yok; hedef doğrulama5örnek,SEARCHING232örnek ardından pilot müdahalesi1061örnek. Bu yalnız ilk log bulgusu; kesintisiz bağlantı veya başarı kanıtı değil, video/heartbeat aralıkları henüz incelenmedi. USB kopması nedeni doğrulanmadı, herhangi bir bağlantı yazılımı düzeltmesi yapılmadı. Önceki kayıt güç kesilmesiyle sonlandı; sonvideo bütünlüğü bilinmiyor.


## Son durum — 19:29 yavaş AUTO denemesi hazır

5 Eylül 2026: kullanıcı yeni kamera/model uçuşundan sonra pilot kontrolüyle indiğini, waypoint hızını düşürüp tekrar denemek istediğini bildirdi. Ağ erişimi düzeldikten sonra canlı DISARM/LOITER/landed1 ve PILOT_CONTROL kilidi doğrulandı. Önce kaydedici2530, sonra flight2458 temiz kapatıldı. USB tek okuyucuyla gerçek WPNAV_SPEED=1000 cm/s, RTL_SPEED=0, FS_THR_ENABLE=1 okundu. Kullanıcının hız azaltma isteğiyle yalnız WPNAV_SPEED=150 cm/s yazılıp geri okunarak doğrulandı. Bu kalıcı FC ayarıdır; RTL_SPEED=0 olduğundan RTL yatay hızı da etkilenir. Eski değer1000 kanıtta korunuyor; kendiliğinden geri yükseltme. Tekrar deneme için MISSION_SET_CURRENT=1 onaylandı; rota maddeleri/irtifaları değiştirilmedi. ARM/mod komutu gönderilmedi.

Yeni flight PID2638, kaydedici PID2710. Kayıt `runtime/recordings/20260905T162900Z-2710`, 129→241 video karesi,0hata ve doğru yeniHEF/profil manifestosu doğrulandı. Profil `config/flight-imx708.json`, aynı IMX708 matris/odak/yeniHEF/eşik0,40. Son yer kontrolü WAIT_AUTO/boşactions/preflightnull, DISARM/LOITER/landed1, RCsağlıklı, GPS14uydu/HDOP0,78/EKF831,12,094V ve taze kamera/telemetri. Pilot müdahalesi kilidi yeni oturumla kalktı; havada yeniden başlatılmaz. Uygulama flight modunda; pilot AUTO seçerse koşullarda GUIDED devralabilir. Önceki uçuşun tespit kayıt analizi henüz yapılmadı, yeni denemenin başarısı bilinmiyor. Kanıt `artifacts/field/imx708-slow-preparation/`. Güncel süreçler sonraki işlemde tekrar okunmalı.

---

## CANLI SON DURUM — yeni IMX708/model uçuş uygulaması ve kayıt açık

5 Eylül2026 yaklaşık19:14: kullanıcı bu sohbette AUTO testini açıkça istedi, önceki görüş engelinin bank üzerinde durmaktan kaynaklandığını doğruladı; Loiter kalkıp AUTO deneyeceğini bildirdi. Kısa ağ kesintisi düzeldi. Taze DISARM/LOITER/landed1, sağlıklıRC/GPS/EKF/konum doğrulandı. Yeni `config/flight-imx708.json`, observe-imx708 profilinin yalnız runtime dizini ayrılmış kopyasıdır; IMX708 matrisi/sabit lens0,1062771082/tamcrop2304×1296 sensör modu/yeni best.hef/eşik0,40,10m rota ve9m lens hedefi korunur. Kod/kalibrasyon/HEF hashleri doğrulandı.

GÖZLEM2249 temiz kapatılıp **flight PID2458** açıldı; log `runtime/imx708-flight.log`, runtime `runtime/imx708-flight-new-model`. **Kaydedici PID2530**, `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260905T161354Z-2530`, kayıt ilerliyor/0API hata. Kaydedicinin --config desteği Pi'de eksikti; yerel mevcut record.py, eski dosya `runtime/before-imx708-recorder/` altında yedeklenip dağıtıldı,3record testi geçti. Yeni kayıt manifestosu gerçek best.hef hash8433d13e... ve aktif flight-imx708 profilini gösteriyor; eski model hash'i yazılmıyor. Son API flight/WAIT_AUTO/boş actions, DISARM/LOITER, GPS12uydu/HDOP0.87,batarya12.293V ve güncel görüntü/telemetri. Kanıt `artifacts/field/imx708-flight-preparation/`.

ARM/mod/rota/FC parametre komutu gönderilmedi. Pilot AUTO seçerse geçerli hedef koşullarında GUIDED devralabilir; daha önceki kontrol kapalı notları tarihli geçmiş. Yeni kamera/modelin gerçek branda kabulü ve bu yeni uçuşun başarısı henüz doğrulanmadı. Pilot Loiter müdahalesi aynı süreçte kalıcı kilit yaratır; inip yeniden ARM etmek kilidi sıfırlamaz. Uçuşta yeniden başlatma yapılmaz. Sonraki adım kullanıcının uçuşunu salt okunur takip/sonrasında kayıt incelemesidir.

---

## Son dış ortam yer kontrolü - 5 Eylül2026,19:02 civarı

Kullanıcı uçuşa hazır olduklarını söyleyip kontrol/panel istedi. Pi yeniden açılmış (uptime8dk); önceki43075 yok,8080 kapalıydı. USBve yeni profil/matris/HEF hashleri korundu. Yalnız **GÖZLEM PID2249**, `--mode observe --config config/observe-imx708.json` yeniden başlatıldı; log `runtime/imx708-field-observe-20260905.log`. Canlı DISARM/LOITER/landed1,RCsağlıklı/slot6/LOITER,GPS11uydu/HDOP0,92,EKF831,batarya12,514V,taze kamera/telemetri,IMX708/yeniHEF30FPS ve hatasız akış doğrulandı.8maddeli aynı10m rota/sonLAND okunuyor; rota/parametre/ARM/mod gönderilmedi. Uçuş ve kayıt başlatılmadı.

**Görüntünün çoğunu iki açık renkli yakın yüzey kapatıyor; yalnız aralarında zemin görülüyor, mavi branda yok.** Kullanıcıya kamera görüşünü açması ve gerçek hedefi göstermesi bildirildi. Bu nedenle tüm uçuş/otonom görev hazırlığı tamamlandı denmedi. Yeni modelin gerçek hedefte kabulü hâlâ doğrulanmadı. Panel açık, otomatik kontrol kapalı. Kanıt `artifacts/field/imx708-preflight-20260905/` ikiAPI+PNG/JPEG. Önceki içmekân1,25V/GPS0 ve eskiPID notları güncel değildir. Sonraki işlemde canlı durum tekrar okunmalı.

---

## EN GÜNCEL - Camera Module 3 + yeni best.hef GÖZLEM açık

5 Eylül2026,18:44 civarı: kullanıcı güneş battığını/token azaldığını söyleyip dama çekimini bitirerek yeni modelle uçuş testi hazırlığı istedi. Daha fazla dama istenmedi.45 özgün kare/9 poz grubunun80,8cm referans grubundaki5 karesi çözüm dışında tutuldu. Diğer8 poz/40 klasik köşe karesiyle yeni IMX708 aday kalibrasyon: RMS0,1388px, en kötü kare0,1511px, fx947,950/fy946,868. Ayrı tutulan80,8cm kullanıcı ölçümlü5 karede lens-ekran dik mesafe ortancası79,9239cm; fark-%1,084. Cetvel belirsizliği yok sayılmadı, metre ölçeğinde saha doğrulaması değildir. `artifacts/calibration/imx708-solve-20260905/` kaynak manifestosu, köşe QA, matris ve held-out raporu; eski IMX219 matrisi kullanılmadı.63cm son ölçümü kullanıcı yaklaşık bildirdi; kesin doğrulama sayılmadı.

Kullanıcı `best_hailo_model/` paketini ekledi: `best.hef` SHA2568433d13ecee9d05852178a0f38c057217d5a7f2db4436036b2a978e877c192e2. Pi parse-hef HAILO8L,3context,UINT8NHWC640×640×3,FLOAT32NMS BY_CLASS/2 sınıf doğruladı. metadata0kırmızı/1mavi, NMS0,25; uygulama görev eşiği son0,40 korunuyor. DJI videosundaki yaklaşık0,90 kullanıcı beyanıdır; kutu güven skoru ise başarı yüzdesi değildir. Yeni modelin gerçek branda başarısı henüz kontrol edilmedi.

Kamera ayarına açık sensör modu2304×1296/10bit ve sabit LensPosition0,1062771082 eklendi; kalibrasyonla odak/sensör uyuşmazlığı reddediliyor, başlangıçta odak yerleşmesi bekleniyor.1280×720,tamcrop[0,0,4608,2592],aynalanmamış görüntü aynı. Kullanıcı montaj değişmedi dedi; nominal[-0,03,0,0,05]m FRD ofseti bu güncel beyana dayalı, yeniden hassas ölçüm değil. Kamera yönü kullanıcının sağ/ileri hareketleriyle görüntü sağ/üst yönünde uyumlu.

78 test geçti/4Torch testi atlandı. Pi kod yedeği `runtime/before-imx708-new-model/`.4 dağıtılan kod/config ve HEF hashleri eşleşti. Kamera-only PID2317 temiz kapatıldı. **Aktif GÖZLEM PID43075**, `--mode observe --config config/observe-imx708.json`; log `runtime/imx708-new-model-observe.log`. Yeni matris `config/camera.imx708-candidate.json`; eski uçuş profili değiştirilmedi. Canlı yeniHailo/IMX708 yaklaşık30FPS, aynı sabit odak/crop,taze ilerleyen kareler,pipeline/link hatası yok,actions boş. Son telemetri DISARM/STABILIZE/landed1,GPS0uydu,RCsağlıksız,batarya bildirimi1,251V (gerçek besleme nedeni bilinmiyor); uçuş hazırlığı tamamlanmış sayılmaz. ARM/mod/rota/FC parametresi veya otomatik kontrol başlatılmadı; kaydedici kapalı. Son görüntüde hâlâ dama, tespit boş. Sırada yeni modeli gerçek mavi hedef görüntüsünde gözlemlemek ve kullanıcı dışarıda/batarya-kumanda hazırsa güncel yer kontrolü. Kanıt `artifacts/pi/imx708-new-model-20260905/`. Aktif süreçler sonraki işlemde yeniden okunmalı.

---

## Kamera kalibrasyon paneli açık - 5 Eylül 2026, 17:42 civarı

Yön kontrolü güncellemesi: kullanıcının drone burnuyla aynı yöne bakarak sağa ve burun yönüne taşıma beyanları, görüntüde sağa ve üste hareketle uyumlu. Yeni kamera için bu iki eksen kullanıcı beyanı+görüntüyle desteklendi; hassas montaj açısı/ofseti ölçülmedi. Sabit odakta4 poz grubu toplandı, yeni matris henüz yok; ayrıntı NEXT_SESSION.md.

5 Eylül17:47 civarı devamı: kullanıcı görüntünün düzeldiğini ve lens-ekran80,8cm/kare25mm olduğunu tekrar doğruladı. Mevcut PID2317'ye SIGUSR1 ile odak kilitlendi; beş taze PNG'de LensPosition0,1062771082 değişmeden ve tam crop ile kaydedildi,5/5 karede9×6 iç köşe bulundu. Görsel incelemede dama net; alt bölümde küçük yansıma var. `artifacts/calibration/calibration-imx708-20260905-reference/` beş PNG+yan dosya+rapor, PNG hashleri Pi ile eşleşti. Bu tek duruşlu referans serisi kalibrasyon çözümü değildir ve yeni matris yoktur. Panel açık/sabit odak; lens sayısı fiziksel mesafe ölçümü sayılmaz. Farklı konum/eğim kareleri ve bağımsız mesafe kontrolleri bekliyor.

Kullanıcının panel isteğiyle ayrı `scripts/camera_panel.py` Pi'de PID2317 ile açıldı; http://172.20.10.4:8080/ . Yalnız Picamera2 ve salt okunur HTTP; Hailo/MAVLink/uçuş uygulaması veya otomatik kontrol açmaz. IMX7081280×720, açıkça2304×1296 sensör modu, tam4608×2592 crop. Taze/ilerleyen kareler ve hata yok doğrulandı. Şu an otomatik odak yalnız önizleme içindir; kalibrasyon için henüz sabitlenmedi. Son PNG'de masa kenarı/zemin var, dama henüz görünmüyor. Önceki kısa test kapalı notu yeni paneli kapsamaz. Kod sözdizimi ve canlı HTTP/PNG kontrolü geçti. Kamera dosyası eski kalibrasyon yüklemez; ana uçuş profilleri değiştirilmedi.

Kullanıcının yazıcısı yok; laptop ekranı kullanılacak. Kullanıcı damaları tam25mm ayarladığını ve80,8cm başlangıç mesafesini bildirdi; bu ölçüler kullanıcı beyanıdır. Desen kadraja geldikten sonra köşe/netlik/yansıma ve odak kontrolü yapılacak. Yeni matris veya mesafe doğrulaması henüz yok. Düz destek kullan; deseni gösterip yakınlaştırmayı sabit tut. Kamera paneli akışı ana uygulamadan ayrıdır; sonraki kalibrasyonun sensör/odak ayarları ana akışa ayrıca uygulanmadan kullanılamaz.

---

## Yeni kamera ön kontrolü - 5 Eylül 2026, 17:30 civarı

Kullanıcı Raspberry Pi Camera Module 3'ü Pi'ye taktığını, kutuda Wide/NoIR yazmadığını bildirdi. SSH üzerinden sensör `imx708`, 4608×2592 ve `imx708.json` tuning dosyası doğrulandı; ticari lens/IR varyantı yalnız sensör adından kesinleştirilmedi. Pi yeni açılmış; kontrol öncesi ve sonrası safak_gorev2/rpicam/libcamera uygulama süreci yok, localhost8080 kapalı. Eski flight2239 artık canlı değil. Uçuş, otomatik kontrol, MAVLink veya Hailo başlatılmadı; yalnız kısa Picamera2 kamera testi yapılıp kapatıldı. Son SoC47,7°C.

Mevcut `create_picamera` açılışı IMX708'de1536×864 sensör modunu seçiyor; listelenen bu mod merkez3072×1728 alanını kullanıyor. Ayrı testte sensör açıkça2304×1296/10bit seçildi:1280×720 RGB888, aynasız, tam `ScalerCrop=[0,0,4608,2592]`,150 farklı sensör zaman damgası, yakalanan akış28,6628FPS. Üç özgün PNG Mac'e alındı ve SHA256 eşleşti. Son görüntü yakındaki açık renkli yüzey; dama/hedef doğrulaması değildir. Kaynak `artifacts/calibration/imx708-precheck-20260905/`, Pi aynı adlı runtime klasörü. Kamera testi sürekli AF ile yapıldı ve lens konumu11-12 arasında değişti; bu kareler kalibrasyon verisi değildir. Eski IMX219 matrisi/ofseti kullanılmadı, uygulama profilleri değiştirilmedi.

Sırada mat kâğıtta düz/sert desteğe sabitlenmiş dama deseni; mevcut A4 PDF yalnız desen olarak kullanılabilir. Gerçek kare kenarları yatay/düşey ölçülecek. Yeni kalibrasyondan önce tam sensör modu ve sabit odak politikası seçilip yakalama/çalışma akışına aynı şekilde uygulanmalı: mevcut varsayılan yakalama/app kodu bu tam alan testini otomatik tekrarlamaz. Otomatik odağı değişen yakın plan kalibrasyonu doğrudan uzak görev odağına taşınmayacak. Yeni matris henüz yok; uçuş/kontrol açılmayacak. Kullanıcıya drone'u sağlam destek üzerinde tutup deseni hareket ettirmesi söylenecek.

---

## Son inceleme — 0,40 denemesinde iki ARM, pilot devri kilidi

5 Eylül 2026: kullanıcı üstünden geçti ama görmedi dedi. `docs/FIELD_FLIGHT_03.md` analizi: aynı PID2239/sortie içinde15:38:08–15:38:52 ve15:39:11–15:40:25 iki ARM aralığı. İlk AUTO ~3,65m; 9,5m devralma sınırına ulaşmadan ~8,33m'de LOITER'a geçilince kalıcı pilot_override açılmış. İkinci ARM/AUTO kilidi sıfırlamamış. 588 ARM örneğinde87mavi kutu,42≥0,40;31kenar/8köşe yok/3metrik geometri reddi,0geçerli hedef. Model gerçek brandayı görüyor; iki metrik ret çevresi tam brandayı gösteriyor. Kesin PnP alt nedeni kayıtta yok. WAIT_AUTO başlığı kilidi gizleyebiliyor; açıklamada pilot kontrolü devri var. Kod/eşik değiştirilmedi. Yerde DISARM doğrulanıp recorder2312 temiz durduruldu; kayıt kapalı. Uçuş uygulaması2239 aynı oturumda ve kilitli; henüz GÖZLEM'e çevrilmedi. Yeni deneme öncesi yerde yeni oturum gerekir, havada kilit sıfırlanmaz. Loglar ve ilgili iki video Mac'te `artifacts/field/flight-03/`;9dosya hash doğrulandı,4erken video yalnızPi'de. Model tek başına neden sayılmamalı.

## Batarya değişimi sonrası canlı durum — 5 Eylül 2026

Pi batarya değişiminde yeniden başladı; önceki PID4509/4582 yok. Eski active.json recording yazısı bayattı, canlı kayıt kanıtı sayılmadı. Kullanıcının “taktık kontrol et uçalım” isteğiyle önce GÖZLEM açılarak DISARM/LOITER/landed1, RC/GPS/EKF/konum ve yeni batarya12,50V doğrulandı. Ardından uçuş uygulaması PID2239, bağımsız yeni kaydedici PID2312 başlatıldı. Son API flight, eşik0,40, WAIT_AUTO/boş eylemler; video yeni `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260905T123707Z-2312` içine gerçekten yazılıyor (81 kare, 0 API hatası). Kanıt `artifacts/field/flight-03-battery-restart/`. Eski kayıt güç kesilerek sonlandı; son MKV'nin bütünlüğü henüz incelenmedi. Uçuş/ARM/mod komutu gönderilmedi. Şimdi uçuş uygulaması aktiftir; pilot AUTO seçerse geçerli koşullarda GUIDED devralabilir. Önceki kapalı/PID bilgileri tarihli geçmiş, yeni işlemde canlı durum tekrar okunmalı.

## Canlı güncelleme — 0,40 eşikli üçüncü uçuş hazırlığı

Kullanıcı dışarıda/kumanda açık bildirip uçuş uygulamasını başlatmayı istedi. Kısa SSH/ağ gecikmesinin ardından yerde DISARM/LOITER/landed1, RC/GPS/EKF ve konum güncelliği doğrulanarak GÖZLEM kapatıldı; `--mode flight --config config/flight.field-candidate.json` PID4509 başlatıldı. Yeni bağımsız video/telemetri kaydedicisi PID4582, kayıt `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260905T123203Z-4582`; yazılan kare sayısı 185, durum recording doğrulandı. Son API WAIT_AUTO, boş eylemler, 0,40 eşik, hatasız Hailo/USB; GPS 11 uydu, HDOP 0.98, batarya 11.45 V. Kanıt `artifacts/field/flight-03-preparation/`. Henüz bu üçüncü uçuşun gerçekleştiği/başarısı doğrulanmadı. ARM veya mod komutu gönderilmedi; pilot manuel Loiter kalkış ve AUTO seçimi yapacak. Uçuş uygulaması artık açık, koşullar sağlanınca GUIDED devralabilir. Başarılı temsili bırakmadan sonra RTL; hedef yoksa mevcut AUTO rotasının son LAND'i geçerlidir. Aşağıdaki kontrol/kayıt kapalı notları bu güncellemeyle tarihli geçmiş. Aktif uygulamayı havada yeniden başlatma; sonraki işlemde canlı durumu oku.

## Son kullanıcı kararı — geçici eşik 0,40

5 Eylül 2026: kullanıcı mevcut kamerayla kısa bir sonraki test için yalnız eşiğin düşürülmesini istedi. `config/flight.field-candidate.json` içinde 0,50 → **0,40** uygulandı; kayıttaki yaklaşık 0,42 tam branda adayını skor kapısından geçirmeyi amaçlar. Köşe/kadraj/geometri/süreli kilit, model, FC/rota aynı; varsayılan ve diğer profiller değiştirilmedi. Pi taze DISARM/landed=1/observe iken profil yedeklendi ve yalnız GÖZLEM yeniden açıldı (PID 4409). Canlı Hailo/API 0,40 ve hatasız akış doğrulandı, Mac/Pi profil hash'i eşleşti. Kanıt `artifacts/field/threshold-040/`. Otomatik kontrol ve video kaydı hâlâ kapalı; yeni uçuş başlamadı. Bu geçici deneme model kaynaklı sorunu tek başına kesinleştirmez; gölge adaylarını da artırabilir. Sonraki plan kullanıcının yeni gelen kamerasını takıp o kameraya özgü kalibrasyon ve model çalışmasıdır; kamera modeli henüz bildirilmedi, eski kamera kalibrasyonu devralınmayacak. Önceki 0,50 sabit tutma talebi bu açık eşik değişikliği isteğiyle bu profil için güncellendi.

## En son saha durumu — 5 Eylül 2026, ikinci uçuş sonrası

Loiter → AUTO gerçek testinin 15:00–15:01 kaydı incelendi; gölgeye yanlış kutular, tam brandada düşük skor ve eşik üstünde kesik kadraj var. İki bağımsız kayıtta geçerli hedef 0; olay defterinde GUIDED/bırakma yok. Dokuz kaynak dosyanın hash'i doğrulandı. `docs/FIELD_FLIGHT_02.md` ve `artifacts/field/flight-02/` güncel kanıt. AI ADAYI ibaresi ve ret teşhisi eklendi, kabul koşulları/eşik/model/FC/rota aynı. 75 test geçti/4 Torch atlandı. Uçuş ve kayıt süreçleri kapatıldı; yalnız GÖZLEM yeni PID4307 ile açıldı. Kaydedici şu anda kapalı, sonraki uçuşta yeniden başlatılmalı. Aşağıdaki eski “uçuş henüz yok” veya aktif uçuş PID notlarını tarihli geçmiş olarak oku. Yeni uçuş veya otomatik kontrol bu incelemede başlatılmadı.

## 1. Önce bunları bil

- Kullanıcı promptlarını İngilizce verse bile bütün açıklamaları, raporları ve yanıtları TÜRKÇE yaz. Teknik ürün adlarını ve kod tanımlayıcılarını gerektiği gibi koru.
- Projeyi kullanıcıya baştan anlattırma. Bu bağlamı kullan; yalnızca yürütülecek iş için gerçekten eksik olan bilgiyi sor.
- Kullanıcı yazılıma SIFIRDAN başlamak istiyor. Bu yeni proje, eski kodların onarılması veya yeniden düzenlenmesi projesi değildir.
- Bu dosyanın bulunduğu proje: `/Users/kaan/Documents/ChatGPT/last şafak`.
- Yanlışlıkla ilk sohbetin açıldığı eski proje: `/Users/kaan/Documents/ChatGPT/SAFAK CHAMP`.
- Sohbet sonradan yeni projeye taşındı. Eski projenin okunmuş olması, eski kodları veya mimariyi yeni projeye taşıma yetkisi vermez. Kullanıcı ayrıca istemedikçe eski projeyi temel alma, kodlarını kopyalama, eski ayarlarını devralma veya düzeltmeye girişme.
- 5 Eylül 2026'da bu dosya oluşturulmadan hemen önce yeni klasörde yalnızca `.git` vardı. Bu tarihli başlangıç bilgisidir; gelecekte klasörün hâlâ boş olduğunu varsayma.
- Önceki tamamlanan çalışma onboarding idi. 5 Eylül 2026'daki yeni kullanıcı isteğiyle Görev 2 quad yazılımı geliştiriliyor: `safak_gorev2/`, salt okunur Flask paneli, kamera kalibrasyon aracı ve otomatik testler oluşturuldu. Sentetik tam akış ve 35 birim testi tamamlandı; gerçek ArduCopter 4.6.3 SITL üzerinde tam görev, pilot müdahalesi, hedef kaybı ve karar döngüsü duraklaması senaryoları geçti. SITL görüntüsü/AI kutuları sentetiktir. Yeni uygulama Pi'de ayrı `/home/furkan/Desktop/safak-gorev2-quad` klasöründe GÖZLEM modunda gerçek Hailo/IMX219 ile çalıştırıldı. 5 Eylül sabah oturumunda gerçek Pixhawk USB bağlantısı ve salt okunur parametre/görev/telemetri okuması doğrulandı; kamera kalibrasyonu ve fiziksel uçuş henüz tamamlanmadı. Aynı gün daha sonra pilot kontrollü Loiter uçuşundan 81 gerçek hedef görüntüsü kaydedilip incelendi; otonom Görev 2 uçuşu ve metrik saha doğrulaması henüz yapılmadı. Gerçek FC parametresi/görevi veya eski proje değiştirilmedi. Güncel ayrıntılar `docs/VALIDATION.md` ve `docs/FIELD_FLIGHT_01.md` dosyalarındadır; bu aşama otonom uçuşa hazır olma kanıtı değildir.
- Kullanıcının bu dosyayı oluşturma isteği yalnızca bağlam dosyası yazma yetkisidir. Kendiliğinden yazılım geliştirmeye başlama. Kullanıcı sonraki sohbetinde açıkça tasarım veya uygulama isterse o yeni isteği yetki olarak kabul et; eski onboarding sınırını süresiz bir engel yapma ve verilmiş yetkiyi tekrar tekrar sorma.
- Bilinmeyen değerleri BİLİNMİYOR/UNKNOWN olarak işaretle. Makul görünen sayı üretme. Eski sabitler güncel gerçek değildir.
- Bu dosya bir hafıza özeti ve çalışma rehberidir; resmî şartnamenin, fiziksel ölçümün veya kullanıcının daha sonraki açık talimatının yerine geçmez.

## 2. Kaynak önceliği ve kanıt ayrımı

Kullanıcının belirlediği doğruluk sırası:

1. Güncel resmî TEKNOFEST/TÜBİTAK 2026 şartnamesi ve yetkili resmî açıklamalar.
2. Resmî hazırlık/görev videosu kılavuzu.
3. Kullanıcının mevcut gerçek donanım hakkında açıkça bildirdiği bilgiler.
4. Gerçek donanım yapılandırması ve inceleme kayıtları.
5. Resmî üretici, ArduPilot ve ilgili teknik belgeler.
6. Eski proje raporu.
7. Eski fikirler, varsayımlar, kodlar ve yazılım tarifleri.

PROJE RAPORU GROUND TRUTH DEĞİLDİR. Planlanmış ama yapılmamış işler, eski parçalar, yanlış terimler ve kanıtlanmamış performans iddiaları içerir. Depodaki eski denetim/onarım belgeleri de resmî gereklilik veya yeni tasarım kararı değildir.

Her önemli bilgiyi şu sınıflardan biriyle değerlendir: resmî kural; kullanıcının güncel beyanı; eski belge/kod bulgusu; ölçülmüş fiziksel kanıt; henüz seçilmemiş mühendislik değeri. Kullanıcının beyanını fiziksel olarak kendin doğrulamış gibi sunma. Geçmiş oturumda okunmuş bir belgeyi yeni oturumda bizzat yeniden okumuş gibi anlatma.

## 3. Proje ve hedef

- Takım: ŞAFAK UAV.
- Yarışma: TEKNOFEST 2026 / TÜBİTAK Liseler Arası İHA Yarışması.
- Kategori: Döner Kanat. Uluslararası veya Serbest Görev kurallarını bu kategoriye karıştırma.
- Ana yarışma aracı: özel üretim altı motorlu hexacopter.
- Amaç: iki görevi güvenli ve güvenilir tamamlamak; otonom kalkış + otonom görev uçuşu + otonom iniş ile c = 1 otonomi katsayısını hedeflemek.
- ARM/DISARM, otonom kalkış ve inişten ayrı olarak şartnameye uygun yapılmalıdır.
- Akşam/uçuş yapılamayan zamanlarda ileride ArduPilot SITL ve Mission Planner ile yoğun simülasyon kullanılması düşünülüyor. Bu araçlar bu onboarding sırasında kurulmadı.

## 4. Ana yarışma aracının güncel donanımı

Aşağıdakiler kullanıcının güncel beyanlarıdır:

| Bileşen | Güncel bilgi |
|---|---|
| Gövde | Özel hexacopter, 6 motor |
| Yapısal malzeme | Karbon fiber plakalar; PET-G Carbon Fiber taşıyıcı/montaj parçaları; özel PLA iniş takımı bileşenleri |
| Uçuş kontrolcüsü | Cube Orange+ / Pixhawk Cube Orange+ |
| Uçuş yazılımı | ArduPilot / ArduCopter; kesin sürüm BİLİNMİYOR |
| Motorlar | 6 × SunnySky X4108S 690KV |
| ESC'ler | 6 × Hobbywing 40A; kesin model/revizyon BİLİNMİYOR |
| Batarya | 4S LiPo, 14,8 V nominal, 9000 mAh, 25C |
| Güç dağıtımı | Matek PDB-HEX |
| GPS/pusula | Here 3+, CAN tabanlı |
| Yardımcı bilgisayar | Raspberry Pi 5 |
| Hızlandırıcı | 13 TOPS Hailo, Hailo-8L sınıfı; kesin HAT/modül BİLİNMİYOR |
| Verici | RadioLink AT9S Pro |
| Alıcı | RadioLink R9DS, kullanıcının 9 kanallı olarak tanımladığı alıcı; gerçek çıkış modu doğrulanmadı |
| Telemetri | 3DR 915 MHz; kesin kart/yazılım/şifreleme durumu BİLİNMİYOR |
| Yük mekanizması | İki bağımsız mekanizma; iki adet amaçlanan/mevcut MG90/MG90S sınıfı metal dişli servo |
| Güç kesme | Manuel güç anahtarı/kesici mevcut; gerçek uygulama ve uygunluk doğrulanmadı |

Pervane modeli, gerçek ağırlık, CG, itki payı, regülatör düzeni ve pin/port bağlantıları güncel fiziksel bilgiler olarak doğrulanmış değildir. Here 3+'ın RTK kabiliyeti, RTK'nın kurulu olduğunu veya santimetre doğruluğu elde edildiğini kanıtlamaz.

### Kamera durumu

- Normal/amaçlanan yarışma kamerası Raspberry Pi Camera Module 3.
- Camera Module 3 testlerde hasar gördü.
- Şu an IMX219 tabanlı 8 MP, Jetson/Raspberry Pi tarzı CSI kamera geçici olarak kullanılıyor.
- Kullanıcı geçici kameranın görüntü kalitesini Camera Module 3'ten daha kötü buluyor. Bu kullanıcı gözlemidir; ölçülmüş nihai performans değildir.
- Geçici kameranın lens/FOV çeşidi BİLİNMİYOR. 77° veya 160° olduğunu varsayma. Eski dosyalardaki başka FOV değerlerini de devralma.
- 5 Eylül 2026 kullanıcı beyanı: quad IMX219 aşağı bakıyor, görüntü üstü burun yönünde; lens merkezden 3 cm arkada, sağ/sol yerleşimi yaklaşık ortada, Pixhawk seviyesinden 5 cm aşağıda. Yeni test konfigürasyonunda FRD ofseti `[-0.03, 0.0, 0.05]` m; sağ/sol sıfırı kullanıcının yaklaşık ortada beyanının nominal karşılığıdır, fiziksel hassas ölçüm değildir. 2 × 2 m mavi hedefin yaklaşık 250–260 cm lens mesafesinde kadraja sığdığı gözlemlenmiş; bu lens kalibrasyonu/FOV veya doğrulanmış metrik doğruluk değildir.
- Son kullanılacak Camera Module 3'ün standart/geniş, IR filtreli/NoIR çeşidi de doğrulanmadı.
- Geçici kamera testlerini nihai yarışma kamerasının doğrulaması sayma. Nihai kamera ile tekrar doğrulama gerekecek.

## 5. F450 test platformu

- F450 quadcopter gövde, 4 motor.
- 5 Eylül saha oturumunda kullanıcı quad bataryasını **3S** olarak doğruladı; kapasite/model BİLİNMİYOR. İlk saha telemetrisinde 12,52 V görüldü. Ana hexacopterin 4S bilgisi değişmedi. Pi, kullanıcının beyanına göre frame güç dağıtımından UBEC ile besleniyor; UBEC çıkış V/A, Pi güç girişi ve yük altında gerilim henüz BİLİNMİYOR.
- Pixhawk 2.4.8; gerçek USB MAVLink okumasında ArduCopter 4.5.7 doğrulandı (5 Eylül 2026 sabah).
- Raspberry Pi 5, 13 TOPS/Hailo-8L sınıfı hızlandırıcı, kamera ve entegrasyon için gerekli navigasyon/haberleşme donanımı.
- 5 Eylül 2026 kullanıcı beyanı: quad Loiter'da problemsiz uçuyor; kumanda anahtarıyla AUTO/Loiter geçişi yapılabiliyor. Pi–Pixhawk bağlantısı USB. ArduCopter önce kullanıcı tarafından yaklaşık 4.x olarak bildirildi; sonraki USB okuması 4.5.7 gösterdi. Lidar/sonar yok. Test hedefi ve iniş alanı açık, aynı düz zeminde.
- 5 Eylül 2026 SSH okuma kanıtı: Pi Debian 12 Bookworm/aarch64; HAILO8L, HailoRT/cihaz firmware 4.20.0; IMX219. Kullanıcının `/home/furkan/Desktop/hailoenvtest/hailo-rpi5-examples/setup_env.sh` betiği etkinleştirildiğinde Python 3.11, NumPy 1.26.4, OpenCV 4.11.0, pymavlink 2.4.49, Flask 2.2.2 ve `detection.py` içindeki Hailo importları bulunuyor. Betiğin etkinleştirdiği ortamın modül yolları `/home/furkan/Documents/proje/hailo-rpi5-examples/venv_hailo_rpi_examples/` altına işaret ediyor; kullanıcı ortamı değiştirilmedi. Eksik waitress 3.0.2 yalnız yeni uygulamanın `runtime/python/` klasörüne eklendi. İlk incelemede Pixhawk USB seri cihazı görünmedi.
- Kullanıcının aynı geceki açık sınırı: Pixhawk ile Pi şu anda bağlı değil; pervaneler takılı ve kullanıcı uyuyacağı için bu gece bağlamak istemiyor. Gerçek Pixhawk bağlantısı/uçuş denemesi için tekrar talepte bulunma; yerel yazılım/SITL ve kamera gözlem çalışması ilerleyebilir. Gerçek bağlantı, kalibrasyon ve uçuş doğrulaması kullanıcı hazır olduğunda yapılacak.
- Kullanıcının sonraki ısınma endişesi üzerine başlattığımız Pi kamera/Hailo gözlem süreci kapatıldı; 8080 paneli de durdu. SSH ölçümünde kapatma öncesi SoC sıcaklığı 57,85 °C, kısa süre sonra 55,65 °C; `get_throttled=0x0`. Kullanıcı uyurken testler Mac'teki SITL üzerinde sürdürülüyor; kamera/Hailo'yu kendiliğinden yeniden açma. Kullanıcı ışıkların kapalı olduğunu bildirdi; karanlık görüntü hedef başarımı kanıtı değildir.
- 5 Eylül sabah güncellemesi: kullanıcı uyandığını, Pixhawk USB bağlantısını yaptığını ve çalışmaya hazır olduğunu bildirdi. Geceki bağlantı/kamera açmama sınırı bu yeni oturum için geçerli değildir. Ağ değişimi düzelince Pi 172.20.10.4 ve Mac 172.20.10.5 üzerinden bağlantı sağlandı. USB cihazı `usb-ArduPilot_fmuv3_3F002B001551383235343838-if00` (ttyACM0). GÖZLEM paneli yeniden açıldı; ArduCopter 4.5.7, STABILIZE, DISARM, TIMESYNC ve Hailo/IMX219 birlikte doğrulandı; kısa sıcaklık örneği 51,8 °C. Uçuş komutu verilmedi.
- Gerçek quad parametre okuması: MIS_RESTART=0, GUID_TIMEOUT=3, FLTMODE_CH=9; FLTMODE4=AUTO, FLTMODE6=LOITER. RC_CHANNELS chancount=0 ve GPS fix=1/0 uydu görüldü; fiziksel RC/GPS hazırlığı doğrulanmadı. FS_THR_ENABLE=1 (bu sürümde RTL), FS_OPTIONS=16, RC_FS_TIMEOUT=1, FS_GCS_ENABLE=0. RC kaybında yarışmanın kontrollü iniş koşuluyla uyumsuz RTL ayarı kaydedildi; parametre değiştirilmedi. Mevcut görev home dahil 8 madde: altı 10 m waypoint ve son LAND; başlangıç TAKEOFF yok. Görev değiştirilmedi. Kanıt `artifacts/pi/pixhawk-detail-20260905.json`.
- Kalibrasyon için A4 yatay, 10×7 kare / 9×6 iç köşe, 25 mm nominal kareli PDF hazırlandı: `output/pdf/imx219-kalibrasyon-a4-25mm.pdf`. Kullanıcı Mac ekranındaki kontrol çizgisini fiziksel 100 mm ölçtüğünü ve kamera yüksekliğinin yaklaşık 40 cm olduğunu bildirdi; tek karenin yatay/düşey ölçümü verilmedi. Aynı IMX219 akışından 40 özgün PNG kaydedildi: `artifacts/calibration/imx219-screen-20260905-a/`. Ekran yansıması bazı köşeleri yanlış buldurdu; 17 klasik aday kaldı, kadrajın düşey kapsamı da yetersiz. İlk seri kalibrasyon olarak uygulanmadı. Kullanıcı drone'u elde tutarken yorulduğunu söyledi; çekim bitince bırakabileceği bildirildi. Sonraki ek çekimde drone sağlam destek üzerinde durmalı, desen hareket ettirilmeli. Ayrıntılar `docs/VALIDATION.md` içinde. Tek cetvel görüntüsü tam lens kalibrasyonu sayılmıyor.
- Aynı gün ek çekim: 45+30 yeni kareyle toplam 115 özgün PNG korundu. Kullanıcı kareleri tam 25 mm bildirdi. İncelenen 55 kare `artifacts/calibration/imx219-screen-20260905-review/camera.candidate.json` adayını verdi: RMS 0,471 px, kadraj/açı çeşitliliği eşikleri geçti; gerçek lens–ekran mesafesiyle doğrulama bekliyor, uçuş ayarına uygulanmadı. Sonraki 18 bağımsız karede kullanıcının 60 cm lens–ekran dik mesafe beyanıyla hesap ortancası 60,605 cm karşılaştırıldı; fark yaklaşık +6 mm/%1,01, yalnız bu ekran kurulumunda. Kanıt `artifacts/calibration/imx219-distance-check-01/distance-report.json`. 80 cm beyanlı iki sonraki seri uyuşmadı: 18 karenin 14 uygun adayında 73,213 cm; kullanıcının ikinci “80 al hemen şimdi” mesajından sonra alınan 10 karenin 9 uygun adayında 71,878 cm ortanca. Kanıtlar `imx219-distance-check-02/03` klasörlerinde. Kamera/crop aynı; mesafe doğrulaması tamamlanmadı. Kullanıcı lens ile dama ekranı arasını ölçtüğünü doğruladı. Sayısal ikinci kontrol de yaklaşık 72 cm verdi; ortak kalibrasyon/ölçek hatasını dışlamıyor. Kullanıcı bu iki 80 cm kaydında drone'un elde olduğunu bildirdi. Sonraki sabit 80 cm beyanlı düzende `imx219-distance-check-04` içine 10 yeni kare alındı: aynı matris/25 mm ölçekle tümü uygun, ortanca 80,0818 cm (aralık 80,0692–80,0840). Önceki 8 cm fark bu kayıtta tekrarlanmadı; eski farkın kesin fiziksel nedeni bilinmiyor. 60 cm ve sabit 80 cm ekran kontrolü uyumlu; cetvel belirsizliği bilinmediğinden mm doğruluk garantisi değildir. Sıradaki fiziksel iş gerçek 2 m hedef ve operasyon mesafesi/kadraj kontrolü; aynı 80 cm sorularını tekrar sorma; ardından gerçek 2 m hedef kontrolü gerekli. Mevcut dar crop için 2 m karenin hizalı ideal kadraj sınırı yaklaşık 4,77 m (45° dönük karede yaklaşık 6,75 m); bu emniyet payı içermeyen hesap nedeniyle ilk 3,5 m önerisi mevcut akışta uygun kabul edilmiyor. Gerçek hedef/görüş alanı/yükseklik doğrulanmadan uçuş açılmayacak. Kamera/crop değiştirilmedi.
- Laptop mavi hedef ön kontrolü yapıldı; kullanıcı kareyi 15 × 15 cm ölçtüğünü bildirdi. Aynı sabit düzenek için 80,8 cm yazdı; önceki cetvel referansı 80 cm, hesap 80,0818 cm idi, yeni cetvel ölçümü varsayılmadı. 20/20 gerçek Hailo karesinde mavi_hedef/class_id=2, skor 0,5097; 0/20 kayıt sırasında geçerli 0,65 görev eşiğini geçti. Teşhis amaçlı kamera göreli mesafe ortancası 81,142 cm; görev kilidi/quad merkezleme kanıtı değil. Kanıt `artifacts/blue-target/screen-check-02/blue-report.json` ve eşlenmiş PNG/JSON. Bu kayıt sırasında eşik/aktif 2 m hedef ayarı değiştirilmedi; sırada gerçek hedef yüzeyi/negatif örnek/kadraj kontrolü var. Gözlem uygulaması yeniden başlatılınca kopmuş Pixhawk telemetrisi düzeldi; son örnekte taze heartbeat, STABILIZE/DISARM. Kamera ayarı değişmezse yeni dama çekimi planlanmıyor.
- 5 Eylül 2026 son kullanıcı beyanı: eğitim için brandaları DJI drone ile beton zeminde farklı irtifa ve açılardan kendileri çekmiş; planlanan uçuş sahası beyaz taşlı. Veri seti bu oturumda incelenmedi; laptopta 0,5097 skorun nedenini bu koşullara kesin bağlama. Kullanıcının geçici eşik düşürme isteği uygulandı: quad test yapılandırmasında `camera.confidence_min=0.50` (önce 0,65); genel kod varsayılanı 0,65. Kayıtlı 20/20 mavi kare yeni skor koşulunu geçiyor; bu tam görev kabulü veya yanlış pozitif doğrulaması değildir. Geometri, tazelik, bağımsız kare ve kilit koşulları korunuyor. Pi gözlem uygulaması yeniden açıldı (o anda PID 3422); canlı API 0,50 eşiği, taze kamera/heartbeat ve hatasız Hailo/USB gösterdi. Kanıt `artifacts/pi/status-threshold-050-20260905.json`; 35 test geçti. Eşik gerçek saha pozitif/negatif örnekleriyle yeniden değerlendirilecek.
- 5 Eylül devam oturumu: kullanıcı laptop ölçümlerini tamamlanmış kabul ederek gerçek hedef/saha çalışmasına geçilmesini istedi. Branda ve quad atölyede yanında; tam brandayı sabit düzende kadraja sokmak büyük olasılıkla mümkün olmadığından bahçede test önerdi. Sonraki adım dışarıda yerde DISARM iken RC/GPS ve bağlantı okuması; hazırlık uygunsa pilot kontrollü Loiter sırasında yalnız GÖZLEM görüntüsü alınması önerildi. Henüz dışarıda hazır bildirimi, gerçek branda kaydı veya uçuş yok. İlk canlı kontrol observe/STABILIZE/DISARM, taze Hailo/USB, eşik 0,50, RC sağlıksız ve GPS 0 uydu gösterdi; PNG'de laptop ekranı vardı. Kanıt `artifacts/field/20260905-precheck/`, akış `docs/FIELD_SESSION.md`. Mevcut %88 kadraj doluluk koşuluyla ideal pinhole sınırları hizalı 2 m kare için 5,42 m, 45° için 7,67 m hesaplandı; bunlar eğim/distorsiyon/hareket payı veya uçuş irtifası önerisi değildir. Kamera/FC/rota ayarı değiştirilmedi.
- Aynı gün ilk gerçek hedef uçuş kaydı bulundu: Pi yerel kaydedicisi 11:00:08–11:01:29 (Türkiye saati) ARM–DISARM aralığında 81 özgün PNG ve eşleşmiş Hailo JSON'u yazdı. ARM sırasındaki kaydedilmiş telemetri LOITER, uygulama GÖZLEM; otonom merkezleme/alçalma/bırakma yapılmadı. Mac'te `artifacts/field/flight-01/` içine kopyalanan 168 kaynak dosyanın SHA256'sı doğrulandı. 54 karede 63 mavi kutu; 0,50 eşiğini yalnız dört kare geçti. 017'de kutu insan gölgesinde (OpenCV dört köşe yok); 032/035/036'da branda kadraj kenarından kesik (kenar payı reddi). Örneklenen 81 karede skor + köşe/sınır/doluluk ön koşullarını birlikte geçen aday yok. Düşük skorlu sekiz aday teşhis amacıyla geometri ön koşulunu geçti; aktif eşik değiştirilmedi. 1 Hz PNG ve 5 Hz civarı uygulama logu bütün kamera kareleri/görev kilidi veya bağımsız fiziksel mesafe doğrulaması değildir. Rapor `docs/FIELD_FLIGHT_01.md`. Mevcut kayıt üzerinden model giriş/çıkış zinciri ve yanlış gölge tespiti incelenebilir; bu inceleme için yeniden uçuş istenmiyor. Son dosya kontrolünde SSH açık, localhost 8080 kapalı ve GÖZLEM süreci yoktu; yeniden başlatılmadı. Kimlik bilgileri dosyalara yazılmadı, FC/rota/HEF/kamera ayarları değiştirilmedi.
- Tek tek test aracı motor/ESC/batarya/GNSS/RC modellerini ana araçtan varsayarak doldurma.
- Pi/Hailo/kamera ve diğer ekipmanların iki araç arasında taşındığı mı, iki ayrı takım mı olduğu BİLİNMİYOR.
- F450, ana hexacopteri geliştirme sırasında riske atmamak için YAZILIM/ENTEGRASYON TEST PLATFORMUDUR.
- F450 testi; test edilen kurulumdaki görüntü işleme, bağlantı ve görev etkileşimi hakkında kanıt sağlayabilir. Hexacopterin uçuşa hazır olduğunu kanıtlamaz.
- Körlemesine taşınmayacaklar: mixer/frame ayarları, motor numarası/yönü, PID, filtreler, hover gazı, ivme/hız sınırları, frenleme, titreşim, yük dinamiği, CG, batarya/akım davranışı, nihai görev hızı ve iniş davranışı.
- Mission ve vision mantığının mümkün olduğu kadar hava aracından bağımsız tutulması isteniyor; bunun için henüz yeni mimari tasarlanmadı.

5 Eylül 2026 — kayıtlı uçuş teşhisi tamamlandı: `replay recorded|hailo` aracı 81 kare ve 168 kaynak hash'ini doğruluyor; 54 mavi kare/63 kutu/4 eşik üstü kare yeniden üretildi. Gerçek Pi'de recorded/replay 81/81, TAPPAS ham NMS/doğrudan HailoRT NMS 81/81 eşleşti. RGB UINT8 640×640 giriş; 640×360 içerik, 140 px üst/alt ve 114 dolgu 81/81 bayt eşleşmesiyle doğrulandı. 0,5097429156 HEF NMS sonucunda da var; renk/ölçek/sınıf/skor çözümleme hatası kanıtlanmadı. Eğitim ile dönüştürme hatası ayrıştırılmadı. Gölge/kesik hedef retleri korundu, geçerli ön koşul adayı 0, eşik 0,50 ve HEF değişmedi. Yalnız geometri sınır/doluluk şartları teşhisle ortak yardımcıya alındı; 56 test geçti. Kamera, panel, MAVLink ve kontrol açılmadı; Pi'de ayrı replay klasörü kullanıldı, mevcut uygulamaya dağıtım yok. Rapor `docs/DETECTION_REPLAY.md`, etiketler `docs/replay/flight-01-annotations.json`, kanıt `artifacts/replay/`. Yeniden eğitim ayrı aşama; yeni uçuş başlatılmayacak.

5 Eylül 2026 son güncelleme — kullanıcı önceliği gerçek Görev 2 testi hazırlığına çevirdi; 1–2 gün kaldığını bildirdi. Yaklaşık 350 DJI/asfalt fotoğrafıyla ilk eğitim, beyaz taşlı alandan 30 küsur mavi branda fotoğrafıyla ek eğitim yapıldığını ve verilen modelin son sürüm olduğunu açıkladı. Yarışma alanı kullanıcı incelemesine göre toprak/asfalt; daha fazla beyaz zemin verisi/eğitim istemiyor. Bu beyan önceki “beton” tarifini günceller; veri incelenmiş veya skor sorununun tek nedeni kanıtlanmış sayılmaz. PT/ONNX karşılaştırmasında aynı 81 Hailo girişinde PT–yeni ONNX eşleşti, 9 tam brandadan HEF 0/PT 8 eşiği geçti, gölge PT'de de var; `docs/MODEL_COMPARISON.md`. Yeniden eğitim/HEF derleme yapılmadı ve şimdilik ertelendi. Kullanıcı Pixhawk/batarya/branda hazır bildirdi; GÖZLEM açıldı. İlk güncel okuma DISARM/STABILIZE, GPS 0 uydu, RC sağlıksız, mevcut rotada TAKEOFF yok; uçuş/kontrol açılmadı. Kalibrasyonlu gözlem hazırlığı ve kadraja uygun görev yüksekliği/rota doğrulaması sırada. Eski 3,5 m ayarı 2 m hedefin tam kadraj koşuluyla uyumsuz; kendiliğinden uçuşa uygulanmaz. Güncel saha durumu `docs/NEXT_SESSION.md` başında.

5 Eylül 2026 saha hazırlığı devamı: kullanıcı açıkça manuel kalkış sonrası AUTO tarama istedi; TAKEOFF kullanılmayacak. `mission.takeoff_mode=manual` quad test seçeneği eklendi; varsayılan otonom TAKEOFF korunuyor. 66 test geçti (Torch gerektiren 4 test normal ortamda atlandı); manuel Loiter kalkış/AUTO/GUIDED/temsili bırakma/LAND akışı gerçek yerel 4.6.3 SITL'de sentetik görüntüyle geçti. Pi'de yalnız kalibrasyonlu GÖZLEM açıldı (`config/observe-field.json`); kod yedeği alındı, kontrol açılmadı. Okunan gerçek rota altı 10 m waypoint + son LAND; değiştirilmedi. Kullanıcıya 10 m tarama adayı bildirildi; fiziksel kadraj teyidi bekliyor. 9 m lens hedefli uçuş adayı yalnız Mac'te, etkinleştirilmedi. Son yer okuması GPS 0 uydu/RC sağlıksız/DISARM/STABILIZE; kullanıcıdan kumanda/açık gökyüzü/PreArm yanıtı bekleniyor. Güncel ayrıntı `docs/NEXT_SESSION.md`.

5 Eylül son kullanıcı yanıtı: bina içindeler, kumanda kapalı; yazılım hazırlığı sonrası dışarı çıkacaklar. GPS/RC eksikliği bu bağlamda okunmalı. AUTO/GUIDED sırasında Loiter ile pilot kontrolünü özellikle istiyor. Manuel kalkış + GUIDED→Loiter SITL geçti. AUTO taraması sırasında Loiter sonrası tekrar devralma kilidinin eksik olduğu regresyonla kanıtlandı ve Controller/MAVLink katmanlarında düzeltildi; son testler 68 geçti/4 model-runtime atlandı. SITL AUTO taraması pilot devri de geçti; düzeltme Pi’ye yalnız GÖZLEM modunda dağıtıldı, 5 değişen kod dosyasının hashleri Mac ile eşleşti. Son GÖZLEM PID 3625; canlı Hailo/USB ve manuel rota kabulü doğrulandı. Dışarıda GPS/gerçek kumanda/Loiter ve hedef kontrolü bekleniyor; uçuş/kontrol açılmadı.

5 Eylül 2026 kayıt eklemesi: kullanıcı uçuşun video ve loglarını Pi'de istedi. Bağımsız `safak_gorev2.record` localhost panelden etiketli kamera+telemetri HUD videosunu 8 FPS/30 s MKV parçalarıyla, API telemetrisini yaklaşık 5 Hz ve kaynak kare/zaman damgalarını JSONL ile kaydediyor. Kamera/MAVLink/kontrol açmaz. Pi'de 35 s deneme 280 video/176 telemetri örneği ve sıfır hata verdi; ffprobe ve görsel QA geçti, 3 yeni kayıt testi geçti. Asıl kaydedici o anda PID 3787, durum `runtime/recordings/active.json`; uygulama GÖZLEM kalıyor. Kayıt SSH/laptop ve uygulama yeniden başlatmasından bağımsız; Pi yeniden açılırsa servis yok, süreç tekrar doğrulanmalı. Uçuş sonrası kaydı SIGTERM ile kapatıp dosyaları güvenceye al. Ayrıntı `docs/NEXT_SESSION.md` başında.

5 Eylül dışarıdaki son doğrulama: gerçek DISARM/LOITER, RC sağlıklı/slot6/LOITER, GPS 11 uydu/HDOP1,00, EKF831, taze Hailo/USB doğrulandı. Kullanıcının başlatma isteğiyle Pi’de `--mode flight --config config/flight.field-candidate.json` açıldı (o anda PID3841); canlı API WAIT_AUTO, actions boş, DISARM/LOITER. Profil: 10 m mevcut rota, devralma alt irtifası9,5 m, lens hedefi9 m/alt sınır8,5 m, eşik0,50. Eski3,5 m kullanılmıyor. Artık GÖZLEM değil; Loiter’da bekleyen uçuş uygulaması var. ARM/rota/FC parametresi gönderilmedi. Önce pilot Loiter10m tam hedef/kadraj kontrolü, doğrulanmadan AUTO’ya geçilmemesi bildirilecek. Kaydedici3787 devam ediyor ve mode=flight kaydı doğrulandı. En güncel başlık `docs/NEXT_SESSION.md`; eski PID/mod bilgilerini güncel sanma.

5 Eylül EN SON: kullanıcı bırakma sonrası son LAND yerine RTL istedi. `mission.return_mode=rtl` eklendi; diskte temsili bırakma doğrulaması→RTL isteği→taze RTL doğrulaması→Pi sahipliği bırakma→FC dönüş/iniş. 74 test ve manuel kalkışlı tam RTL SITL geçti. Pi yerde DISARM/Loiter iken güncellendi; **aktif flight PID4029**, profil9m/return_mode=rtl, son API GPS13/HDOP0,81, RC sağlıklı/LOITER, WAIT_AUTO. RC failsafe zaten1/RTL; RTL_ALT1500cm, FINAL0/iniş, RALLY_TOTAL0; FC parametresi değişmedi. Düşük bataryaRTL/kritikbataryaLAND, GCSfailsafe0; bütün failsafelerRTL denmez. Kullanıcıya önce pilot Loiter10m hedef kontrolü, doğrulanmadan AUTO’ya geçmemesi tekrar bildirildi. Kaydedici3787 sürüyor. Güncel kaynak `docs/NEXT_SESSION.md` başı; eski LAND dönüşü/PID’ler güncel değildir.

## 6. Sorumluluk paylaşımı ve mevcut strateji

ArduPilot/uçuş kontrolcüsü: rate ve attitude kontrolü; konum kontrolü; EKF ve GPS/navigasyon füzyonu; motor karışımı ve motor çıkışları; temel uçuş kontrolü; AUTO görevleri ve waypoint takibi; kalkış/iniş yürütme; temel otopilot güvenlik işlevleri.

Raspberry Pi 5: kamera görüntüsü alma; Hailo çıkarımı; hedef tespiti/doğrulama/takip; Görev 2'nin görev düzeyindeki kararları; AUTO aramadan geçici hedef etkileşimine geçme; yaklaşma/hizalanma; doğru yük seçimi ve bırakma komutu; yer istasyonuna canlı görüntü işleme bilgisi.

Pi tek tek motorların PWM değerlerini hesaplamamalı. Servo yük komutu ile motor kontrolünü karıştırma. Araç stabilizasyonu uçuş kontrolcüsünde kalır.

AUTO: ArduPilot'ta saklanan ve yürütülen önceden hazırlanmış görev.
GUIDED: yardımcı bilgisayar/yer istasyonu/Lua tarafından dinamik hareket veya navigasyon komutları.
PX4 aracı gibi düşünme; “Offboard”u ArduCopter modu olarak kullanma. AUTO'ya dönüşte devam/yeniden başlama davranışı yazılım sürümü ve ayarlara bağlıdır; otomatik olarak doğru tarama devamı garantisi sayılmaz.

### Görev 1 tercihi

Mission Planner + ArduPilot AUTO ana çözümdür. Gerçek ihtiyaç ortaya çıkmadıkça Pi için özel Görev 1 navigasyon yazılımı yazılması istenmiyor. Takım, gereken parkur koordinatlarını alıp görevi hazırlayacak; uçuşu otopilot yürütecek.

Mevcut niyet: kurala uygun manuel ARM; otonom kalkış; doğru parkur ve iki tam yatay sekiz; gerekli son direk dönüşü ve bitiş çizgisi; otonom iniş; kurala uygun DISARM. Bunlar mevcut yaklaşımın aktarımıdır, hazırlanmış waypoint görevi değildir.

### Görev 2 tercihi

Mission Planner'da hazırlanmış AUTO parkur/tarama rotası + Pi görüntü işleme + hedef etkileşiminde geçici GUIDED kontrolü.

5 Eylül 2026 — yeni ilk uygulama kapsamı: Görev 1'e dokunulmayacak. Kullanıcı quad'da AUTO kalkıştan itibaren sürekli mavi 2 × 2 m hedef taraması, GUIDED merkezleme ve alçalma, süreli kilit sonrası temsili bırakma, ardından rotanın son LAND noktasına gidiş/iniş istedi. Quad'da servo yok; bırakma yalnız temsili panel/kayıt olayıdır. Yazılım kalkış sırasında tespiti gösterir; TAKEOFF bitmeden GUIDED devralmaz. İlk mühendislik önerileri: 3,5 m tahmini lens yüksekliği, 1,5 s merkez kilidi, 3 s kesintisiz bırakma kilidi, en fazla 0,4 m/s yatay ve 0,15 m/s alçalma. Bunlar fiziksel uçuşla doğrulanmadı. Son LAND'e geçmeden önce hedefe yönelme anındaki arama irtifasına çıkılır. Pilot Loiter'a geçtiğinde devralma kilitlenir. Tam yarışma akışı aşağıda gelecek hedef olarak korunur; bu sürekli tespit yapan quad testi yarışmanın Direk 2 sonrası tespit koşulunu uygulayan sürüm sayılmaz.

Canlı panel kararı (kullanıcı): Flask Pi üzerinde, salt okunur panel laptop tarayıcısında Pi IP adresiyle. Başlatma uçuş öncesinde Pi terminalinden, panelden etkileşim yok. Pi/laptop aynı telefon hotspot'unda; Pi'de TP-Link TL-WN722N v1 harici adaptör bildirildi. Yaklaşık 150 m menzil hedefi var, saha ölçümü yapılmadı. İlk gerçek Pi gözleminde kamera–Hailo–panel akışı çalıştı; bu örnekte yaklaşık 30 işlenmiş kare/s görülmesi hedef doğruluğu/uçuş veya saha benchmark'ı değildir.

İstenen kavramsal akış: kurala uygun ARM ve otonom kalkış; başlangıç parkurunu tamamlama; Direk 2 dışarıdan doğru alındıktan sonra hedef tespitinin görev için uygun hale gelmesi; AUTO tarama; geçerli hedefin doğrulanması; geçici GUIDED yaklaşma/hizalanma; doğru hedef/yük ve güvenli koşullar doğrulandıktan sonra tek bırakma; AUTO taramaya devam; diğer hedef; gerekli parkur/bitiş geçişi ve otonom iniş; kurala uygun DISARM.

- Hedef koordinatlarını önceden sabitleme. Koordinatlar yarışma gereği bilinmez.
- Kameranın bütün alanı sıfırdan kendi başına gezdirmesi amaçlanmıyor; normal tarama yolu AUTO'da.
- Hedef bulunmadığında AUTO tarama devam eder.
- Şartnamenin “Direk 2 dışarıdan alındıktan sonra tespit” koşulunu yalnızca bir waypoint indeksine eşitleme. Eski kodda erkenden çalışan çıkarımın sonuçlarını kullanmamakla yetinmenin hakemce kabul edildiği doğrulanmadı. Sürekli görüntü alma ile izin verilen hedef tespitini ayır.
- Son yaklaşım, hizalama, bırakma ve aramaya devam yöntemleri henüz kesinleşmedi. Bu özetten yeni durum makinesi veya algoritma tasarlanmış sonucu çıkarma.

## 7. Görüntü işleme ve yük mantığı

Tercih: KAMERA → Hailo üzerinde AI dedektör → kutu/sınıf/güven → OpenCV ile ikincil doğrulama → birden çok bağımsız karede zamansal doğrulama → onaylı hedef.

- Sinir ağı BİRİNCİL dedektördür. OpenCV İKİNCİL kontrol katmanıdır.
- Aydınlatma, gölge ve beyaz dengesi değişimleri nedeniyle katı HSV segmentasyonu ilk sert eleme kapısı olarak istenmiyor.
- OpenCV renk, geometri, ROI tutarlılığı ve makullük kontrolü için değerlendirilebilir; algoritma/eşik seçilmedi.
- Takım kendi eğittiği hedef dedektörünü kullanmayı amaçlıyor. Eski rapordaki YOLOv8 Nano adını kesin çalışan model olarak kabul etme.
- 5 Eylül 2026 — kullanıcı önceki yazılımcının modelini bu test için yüklediğini bildirdi. Yeni proje içindeki `safak_v2_hailo_model/` paketinde `.hef`, `.pt`, `metadata.yaml`, `nms_config.json` statik olarak incelendi. `.pt` deserialize edilmedi/çalıştırılmadı. Daha sonra Pi'de `parse-hef`, HAILO8L, UINT8 NHWC 640 × 640 × 3 giriş ve iki sınıflı YOLOv8 NMS çıkışını doğruladı; HEF gerçek Hailo gözlem zincirinde çalıştı. Model indeksleri `0: kirmizi_hedef`, `1: mavi_hedef`; TAPPAS NMS çözümleyicisi +1 eklediğinden callback sınıfları 1/2, etiket listesi `[unlabeled, kirmizi_hedef, mavi_hedef]`. İki dosyanın aynı ağı temsil etmesi ve renk eşlemesinin gerçek hedefle doğruluğu henüz doğrulanmadı. Paketin kullanılması eski uygulama kodunun devralınması değildir.
- Aynı gün sonraki doğrulama: `.hef` yeni uygulamada gerçek Pi/Hailo-8L üzerinde açıldı ve kamera callback'i çalıştı. `.pt` yine çalıştırılmadı. TAPPAS NMS callback sınıf kimlikleri model indeksine +1 eklediği için yeni `hailo_labels.json` eşlemesi `unlabeled, kirmizi_hedef, mavi_hedef` biçimindedir; gerçek hedeflerle renk doğruluğu henüz denenmedi. Kullanıcının `detection.py` dosyası değiştirilmeden referans olarak tutuldu. Kamera/Hailo gerçek ortam raporu ve ilk durum kaydı `artifacts/pi/` altındadır. Kalibrasyon/mesafe ve uçuş doğrulaması bekliyor.
- 13 TOPS değeri FPS veya uçtan uca gecikme ölçümü değildir. Önceki “30 FPS” ve “100 ms” iddiaları kanıtlanmış değildir; gecikme ve işleme hızı ayrı ölçütlerdir.
- Gerçek performans ancak gerçek Pi 5 + hızlandırıcı + kullanılan model + kamera zinciri üzerinde ölçüldüğünde bilinir. Onboarding sırasında benchmark yapılmadı.

| Gerçek hedef | Doğru yük |
|---|---|
| 2 × 2 metre MAVİ KARE | KIRMIZI yük |
| 1 × 1 metre KIRMIZI KARE | MAVİ yük |

İki yük ve iki bağımsız bırakma mekanizması var. Hedef sırası sabit değil. Tek yanlış/kararsız tespit bırakmayı tetiklememeli; yanlış yük, aynı yüke tekrarlı komut ve aynı yükün birden fazla bırakılmış sayılması önlenmesi gereken davranışlardır. Kesin bırakma koşulları, servo kanalları/PWM değerleri ve fiziksel bırakma geri bildirimi henüz belirlenmiş/doğrulanmış değil.

Yer istasyonunda aynı izinli fiziksel kameradan canlı, etiketlenmiş hedef görüntüsüyle görüntü işleme kanıtı sağlanmalı. Kutu, sınıf, güven ve hedef durumu yararlı amaçlanan bilgiler; kesin yayın mimarisi veya zorunlu tek arayüz değildir. Eski GStreamer UDP/Mission Planner anlatımını değişmez karar sayma.

## 8. Şartnameden doğrulanmış başlıca kurallar

Kontrol tarihi 5 Eylül 2026. Kullanıcının verdiği V4 (20 Mayıs 2026, 82 PDF sayfası) ve resmî sayfadaki V6 (30 Haziran 2026, 80 PDF sayfası) tamamen okundu ve karşılaştırıldı. Görev/güvenlik/puanlama açısından §8–11'de esaslı değişiklik bulunmadı. V6 idari işlemler ve takvimde değişiklikler içeriyor. Daha sonraki resmî sürüm/duyuru varsa onu kullan.

### Parkur, süre ve puanlama

- Görev 1 YÜKSÜZ. Kalkış çizgisinden Direk 2'ye ilerleme, Direk 2'yi dışarıdan alma, direkleri içeride bırakan art arda İKİ TAM yatay sekiz, sonrasında Şekil 8'e uygun Direk 2 arkasından/dışından dönüş ve başlangıç/bitiş çizgisi geçişi gerekir.
- İniş iki direk arasındaki uygun alanda yapılabilir. Şekil 8 ve 9 gerçek yön/koordinat uydurmak için değil, gerekli geometriyi anlamak için kullanılmalı.
- Görev 1 başarılmadan Görev 2 denenemez. Görev 2 tamamlanmadan derece ödülü alınamaz.
- Liseler Arası Döner Kanat için üçüncü yük alma görevi yok; uluslararası kategorinin isteğe bağlı üçüncü görevini karıştırma.
- Görev 2 kare hedefleri her ikinci görev uçuşu öncesinde rastgele yeniden konumlandırılır; şekildeki konumlar örnektir. Sabit kanat hedefleri de aynı alanda bulunabilir, yanlış hedef olarak alınmamalı.
- Planlanan yaklaşık 30 × 100 m tarama alanı ve 150 m direk arası kesin saha ölçüsü değildir. Nihai saha sınırları/koordinatları henüz bu bağlamda yok; tampon bölge varsayma.
- Kurulum en fazla 8 dakika, uçuşa hazırlık ayrıca en fazla 8 dakika. GPS/ARM uçuşa hazırlık kapsamındadır. Kutuda önceden çalışan güç sistemi olamaz.
- Hazırlıkta güç açma/kesme dışındaki ek müdahalenin süresi + 10 saniye kurulum süresine eklenir.
- Görev 1 en fazla 5 dakika, Görev 2 en fazla 10 dakika.
- Uçuş süresi başlangıç/bitiş çizgisinden hareketle başlar, gereken son çizgi geçişiyle durur. Sonraki inişte kırım olması başarıyı yine etkiler.
- İki görev için en fazla toplam 4 uçuş hakkı; her görevin en iyi puanlı uçuşu değerlendirilir.
- c: tamamen manuel 0,5; otonom uçuşla manuel kalkış ve/veya iniş 0,7; otonom kalkış/uçuş/iniş 1.
- Liseler Arası puan dağılımı: video 10, Görev 1 30, Görev 2 70; toplam 110, cezalar hariç. Tam puanlar otomatik değil, karşılaştırmalı oranlar vardır.
- Tablo 5 Görev 1 ağırlıkları: kutu hacmi 6, kurulum 6, yüksüz ağırlık 6, uçuş süresi 12. Görev 2: aynı ilk üç unsur 4'er, yük ağırlığı 20, mavi hedef doğruluğu 10, kırmızı hedef doğruluğu 20, uçuş süresi 8. Katsayı ve cezalar uygulanır.
- Direği bir kez içeriden alma: görev tamamlanırsa 10 puan ceza. İkinci kez: uçuş başarısız. Manevranın tamamlanmaması Görev 1'i başarısız yapar.

### Yük, kamera, kanıt ve paketleme

- İkinci görevde iki yük zorunlu; renk hariç ağırlık/diğer özellikleri aynı olmalı. Farklı uçuşlarda iki önceden beyan edilmiş yük ağırlığı yapılandırması denenebilir.
- Yüklerde ilave işaret/şerit/QR veya aktif/pasif elektronik bileşen olamaz. İzin verilen paraşüt gibi pasif sistemler yükle aynı renk olmalı. Yükler parçalanmamalı.
- İsabet ilk çarpma noktası veya aracın bırakma anı değil, yükün SON DURDUĞU NOKTA üzerinden hedef merkezine göre ölçülür. Döner kanat için ölçüm sınırı 10 m; dışı ilgili isabet puanını alamaz. Parçalanan yük de isabet puanı alamaz.
- Görüntü işleme için yardımcı bilgisayara entegre TEK kamera. Alanı görüntüleyen ikinci kamera yasak. Video çekimi için dış çekim kameraları ile görevde alanı tarayan kameraları karıştırma.
- Hedefin görüntü işlemeyle tespit edildiği yer istasyonunda anlık etiketlenmiş görüntüyle hakemlere kanıtlanmalı. Kanıt olmadan isabet olsa bile hedef isabet puanı alınamaz. Görev sonrası log istenmemesi, canlı kanıtın yerine geçmez.
- Döner kanat muhafaza kutusu dikdörtgen/kare prizma; kapalı, sağlam ve bir kişi tarafından taşınabilir olmalı. Yer istasyonu ve kumanda hariç, yükler dahil tüm araç bileşenleri kutuda olmalı. Montaj aletlerinin kutuda olması zorunlu değil. Hacim dış ölçülerden hesaplanır.
- Kutuda olması gerekirken dışarıdan eklenen malzeme ve sportmenlik dışı davranış için ilgili 0–5 puan cezaları vardır.

### Güvenlik ve teknik kontrol

- Ana araç toplam kalkış ağırlığı yükler dahil en fazla 4 kg. Rapordaki hesap bunu fiziksel olarak doğrulamaz.
- Azami irtifa AGL 120 m; görev sırasında yere değmemek koşuluyla genel alt irtifa sınırı yok. Seçilecek görev irtifası BİLİNMİYOR.
- Motor ARM/DISARM kumanda üzerindeki STICK HAREKETLERİYLE yapılmalı. Otonom kalkış/iniş ile manuel ARM/DISARM çelişmez. Otopilotun otomatik disarm davranışını da uygunluğu doğrulanmış sayma.
- RC sinyali kaybında en fazla 5 saniyede failsafe. Döner kanat için “yarım gaz - kontrollü iniş”; RC-LOSS FAILSAFE İÇİN RTL SEÇİLEMEZ. Hakem emrinde gaz kesilmesi ayrıca belirtilir. Bu ifadeden sabit %50 motor PWM/gaz parametresi üretme.
- NORMAL GÖREV DÖNÜŞÜ ile RC KAYBI farklı olaylardır. Normal dönüş/iniş parkur, bitiş ve saha kurallarına uymalı; normal dönüş fikri RC kaybında RTL'yi meşrulaştırmaz.
- Failsafe yerde verici kapatılarak kontrol edilir. Gerçek alıcı kayıp işareti, FC tepkisi ve kontrollü iniş davranışı doğrulanmalı; RSSI düşüşü tek başına bunları kanıtlamaz.
- RC ve telemetri için uçtan uca şifreleme zorunluluğu var. Frekans atlama, spread spectrum, binding veya MAVLink2 signing şifreleme kanıtı değildir. MAVLink imzalama kimlik/bütünlük doğrulamasıdır, içerik şifrelemez. “3DR 915” ismi aktif şifrelemeyi kanıtlamaz; SiK desteği sürüm/donanım/yapılandırmaya bağlıdır.
- Erişilebilir entegre Power On/Off anahtarı, harici kesici gerektirmeden en fazla 2 saniyede güç kesebilmeli; teknik kontrolde gösterilmeli. Mevcut manuel kesicinin uygunluğu henüz kanıtlanmadı.
- Teknik kontrole pervaneler sökülmüş, bütün uçuş ekipmanı ve kullanılacak/onaylanacak bataryalarla girilir. Uygun yedek bataryalar aynı kapasite/model/ağırlık koşullarına tabidir.
- Motor/pervane/ESC ve görevler arasında itki sistemi değiştirme kısıtları vardır. Beyan edilmemiş yüklerle uçuş geçersizdir. Yarışma sürecindeki donanım/yazılım değişiklikleri DDK/hakem onayına tabidir.
- İnişte donanımsal bütünlük korunmalı; pervane kırılması istisna olarak kabul edilebilir. Kırım sonrası yeniden teknik kontrol gerekir. Hakem güvenlik nedeniyle uçuşu durdurabilir; müdahale emrine uyulmalı.
- Ana araçta önemli değişikliklerden sonra ön test yapılmadan yarışmaya gelinmesi kabul edilmiş güvenli süreç değildir. Test uçuşları için şartnamedeki pilot kaydı, izin, saha, görüş ve gündüz koşulları ayrıca dikkate alınmalı.

### Hazırlık ve görev videosu

- Görev 1 uçuşu ve iki tam sekiz havada, kesintisiz kalkış/uçuş/inişle gösterilir. Uçuş bölümü en fazla 5 dk, hazırlık/bilgilendirme en fazla 15 dk, toplam 20 dk; MP4/HD, müziksiz. Gerçek Görev 2'nin 10 dk sınırı ile video bölümünü karıştırma.
- Eş zamanlı üç görüntü: hava aracı; pilotun yüzü ile el/kumanda hareketleri; doğrudan yer istasyonu ekran kaydı. Bu, ek bir operasyonel tarama kamerasına izin değildir.
- Görev 2 mekanizması yerde gösterilebilir; bu gerçek yarışma görevinin yerine geçmez. Videoda gösterilen mekanizmayla teknik kontrole getirilen mekanizma tutarlı olmalı.
- Rapor-video-nihai araç farkları açıklanmalı. Kılavuz ana boyutsal/yapısal/aviyonik özelliklerde %15 sınırı ve radikal itki değişikliği yasağı içeriyor; belirli bir değişimin uygunluğunu kendiliğinden ilan etme.
- Eski yerel 12 sayfalık kılavuzun üniversite/karma takım alanları, güncel 13 sayfalık kılavuzda okul/kurum şeklinde düzeltilmiş. Temel teknik içerik korunuyor.

## 9. Eski bilgilerden taşınmaması gerekenler

Bu bölüm eski projeyi yeniden kullanmak için değil, yanlış varsayımların tekrarını önlemek içindir.

- Eski rapor: 10.000 mAh/65C. Güncel: 9000 mAh/25C.
- Eski rapor: PLA taşıyıcı eklemler. Güncel: PET-G CF taşıyıcı/montaj parçaları, PLA iniş bileşenleri.
- Eski raporda motor sayısı, üçüncü görev, servo şema etiketleri ve besleme etiketlerinde iç tutarsızlıklar var. Bunları gerçek bağlantı kabul etme.
- Rapordaki 3584 g yüksüz/3784 g yüklü, hız/menzil/güç ve motor kaybında güvenli iniş iddiaları eCalc/eski varsayımlardır. Uçuşa hazır olma, ölçülmüş performans veya motor kaybı kontrolü kanıtı değildir.
- PDB-HEX için rapordaki “264 A sürekli” ve bağımsız 3 A/5 A çift BEC iddiaları üreticiyle uyuşmuyor. Üretici 140 A sürekli/264 A burst ve seçilebilir Vx regülatörü tanımlar. Gerçek revizyon/besleme ayrıca doğrulanmalı.
- Pi 5'te dahili donanımsal H.264 kodlayıcı yok. Eski yayın anlatımı bu varsayıma dayanamaz.
- MAVSDK-Python/asyncio/Offboard, RSSI düşüşünde RTL, imzalamayı şifreleme sayma, yük sonrası dinamik PID, balistik/GPS bırakma, piksel merkezleme, GStreamer UDP ve eski benchmark sayıları yeni yazılımın otomatik gerekliliği değildir.
- Eski kaynak kod pymavlink/GUIDED, görüntüden GPS projeksiyonu/kümeleme ve servo komutları kullanıyordu; varsayılan NCNN, Hailo isteğe bağlıydı. Güncel tercih Hailo birincil çıkarım.
- Eski Hailo üst verisi `safak_v2`, iki sınıf, 640 × 640, hailo8l; NCNN üst verisi YOLOv8n ile ilişkili 512 × 512 bildiriyordu. Bunlar eski dosya üst verileridir; mevcut çalışan model seçimi değildir. Export araç sürümü YOLO mimarisi sürümü sanılmamalı. Veri seti/etiket yönergelerinde tutarsızlıklar vardı.
- Eski uygulamada başarısız hizalama/zaman aşımından sonra bırakmaya devam etme, fiziksel bırakma yerine küme bazlı kayıt, tekrar aynı Hailo karesini okuma ve waypoint indeksini direk geçişi sayma sorunları görüldü. Bunlar yeni projede bu kodun bulunduğu veya çalıştığı anlamına gelmez.
- MAVLink GLOBAL_POSITION_INT.relative_alt, home'a göre irtifadır; gerçek AGL/yerden mesafe değildir. Eski kod yanlış adlandırıyordu. Mesafe sensörü fiziksel olarak doğrulanmış değil.
- Eski fake Pixhawk/simülasyon yardımcıları gerçek SITL veya yükün son durma noktası ölçümü değildir. Kaynak dosyasının varlığı testin gerçekten yapıldığını kanıtlamaz.
- Eski denetim/onarım raporlarının bazıları özgün raporu görmeden yazılmıştı. Özel Görev 1 programı, özel sayaç, belli durum makinesi veya belirli eşikleri zorunlu sayan yorumları devralma. Kuralın istediği sonuçla önerilen uygulama tekniğini ayır.

## 10. Açık bilinmeyenler

Onboarding sırasında gerçek uçuş/tezgâh logu, güncel otopilot parametre çıktısı, eğitim veri seti veya ölçülmüş benchmark kaydı bulunmadı. Başka yerde bulunmadığını iddia etme; kullanıcı bunları daha sonra sağlayabilir.

- İki FC'nin kesin firmware/build/parametreleri, estimator ve sensör yapılandırmaları.
- Ana ve test aracının gerçek kablolaması, Pi bağlantı portu/protokolü/baud/sinyal seviyesi ve bağlantı yönlendirmesi.
- ESC revizyonu, pervane, frame/motor numaraları/yönleri; ölçülmüş itki/akım/sıcaklık, titreşim, tune, filtreler, hover gazı, uçuş zarfı.
- Güncel boyutlar ve parça ağırlıkları; yüksüz/yüklü toplam kütle; iki/tek/sıfır yükte CG; yapısal testler ve uçuş kanıtı.
- Gerçek PDB/BEC/regülatör/power module düzeni; Pi/Hailo/servo/FC beslemeleri; sigorta, akım/gerilim ölçümü, anahtarın tüm gerekli hatları kesmesi ve 2 saniye testi.
- RC/alıcı/telemetri revizyonları, çıkış modu, gerçek kayıp işareti/failsafe, şifreleme desteği/aktifliği ve hakemce kabul edilen kanıt.
- GNSS/pusula/CAN/RTK durumu, kalibrasyon, rangefinder varlığı ve gerçek AGL kaynağı.
- Geçici ve nihai kamera çeşidi/FOV, montaj geometrisi, lens kalibrasyonu/distorsiyon, crop/resize, çözünürlük, pozlama/odak, bağımsız kare ve telemetri zaman eşleşmesi.
- Pi OS, HailoRT/hailo-apps ve diğer runtime sürümleri; kesin Hailo kartı; veri seti/checkpoint/HEF ilişkisi; etiket/ön işleme; gerçek doğruluk ve gecikme.
- Nihai yük ağırlığı/malzeme/ölçüleri; servo modeli/kanalı/PWM, fiziksel renk eşlemesi, mekanizma tutma/sıkışma/bırakma davranışı, bırakma gecikmesi/geri bildirimi.
- Nihai görev/tarama/bırakma irtifası, arama/sekiz/yaklaşma hızları, Guided hizalama kazançları, AI güven eşiği, doğrulama kare sayısı ve bırakma eşikleri. Bunlar gelecekte seçilecek değerlerdir; kullanıcıdan hepsini şimdi seçmesini isteme.
- Nihai saha koordinatları/sınırları/direk arası/yön/iniş konumu, erken tespit yorumuna dair resmî açıklama. Hedeflerin uçuş öncesi bilinmemesi tasarım gereği; sabit hedef koordinatı isteme.
- Son yayın/yer istasyonu yöntemi, saha menzili/gecikmesi ve canlı görüntü işleme kanıtı.
- Kabul edilmiş videodaki yapılandırma, sonrasındaki değişiklikler ve resmî onaylar; iki platform arasında hangi donanımların ortak olduğu.

Gelecek iş için gerekirse önce mevcut firmware/parametre/test kayıtlarını, gerçek bağlantıları, kamera/model kimliğini, ölçülmüş kütle/yük bilgilerini ve resmî onayları netleştir. Önceki sohbetin sonunda bu konulardaki sorular henüz yanıtlanmamıştı. Hepsini her yeni sohbette yeniden listeleme; işe bağlı olanları sor.

## 11. Kaynaklara erişim

Önceki oturumda aşağıdaki belgelerin tamamı okundu; görev diyagramları, skor tabloları ve proje raporu görselleri de incelendi. Bu dosya teknik çalışma sırasında ilgili birincil sayfalara dönmenin yerine geçmez. Yerel yollar bu bilgisayara özeldir; erişilemeyen dosyayı okumuş gibi davranma.

- Kullanıcının tam başlangıç isteği: `/Users/kaan/.codex/attachments/d6c91ae2-aab1-40a0-996e-9519e738a5e2/pasted-text.txt`. Bu dosyada kullanıcının eski onboarding talebi var; daha sonraki proje taşıma, Türkçe yanıt ve bağlam dosyası isteği bu AGENTS.md'de korunuyor. Eski “dosya yazma” kısıtı bu bağlam dosyası için kullanıcı tarafından açıkça kaldırıldı.
- Verilen V4: `/Users/kaan/Downloads/2026_İHA_Yarışmaları_Şartnamesi_TR_v4_SRqBb_260904_191751.pdf`.
- Yerel video kılavuzu: `/Users/kaan/Downloads/2026_LİSELER_ARASI_İHA_SABİT_VE_DÖNER_KANAT_GÖREV_KATEGORİLERİ_GÖREV_VİDEO.pdf`.
- Eski özgün rapor: `/Users/kaan/Downloads/TkRfULkzptaRWhDOiXENnjzT9JYCVyb6_260904_191155.pdf`.
- [Resmî yarışma sayfası](https://teknofest.org/tr/yarismalar/liseler-arasi-insansiz-hava-araclari-yarismasi/).
- [İncelenen resmî V6](https://cdn.teknofest.org/media/upload/userFormUpload/2026_%C4%B0HA_Yar%C4%B1%C5%9Fmalar%C4%B1_%C5%9Eartnamesi_TR_v6_n7Mv5.pdf).
- [Güncel olarak incelenen video kılavuzu](https://cdn.teknofest.org/media/upload/userFormUpload/2026_L%C4%B0SELER_ARASI_%C4%B0HA_SAB%C4%B0T_VE_D%C3%96NER_KANAT_HAZ._VE_G%C3%96REV_V%C4%B0DEOSU_HAZIRLAM.pdf).
- Şartname referansları: §8.3 genel/yük/süre/otonomi; §9 teknik kontrol/RC/güç; §10.2.2 Liseler Arası Döner Kanat; §11.2 puan; §14.1 güncel sürüm. Şekil 8, V4 PDF sayfa 56/basılı 55, V6 PDF sayfa 55/basılı 54. Şekil 9: V4 59/58, V6 58/57. Tablo 5: V4 64/63, V6 63/62.
- [ArduCopter AUTO](https://ardupilot.org/copter/docs/auto-mode.html), [GUIDED](https://ardupilot.org/copter/docs/ac2_guidedmode.html), [RC failsafe](https://ardupilot.org/copter/docs/radio-failsafe.html), [irtifa tanımları](https://ardupilot.org/copter/docs/common-understanding-altitude.html).
- [MAVLink signing](https://mavlink.io/en/guide/message_signing.html), [MAVLink şifreleme açıklaması](https://mavlink.io/en/about/faq.html), [SiK kaynak kodu](https://github.com/ArduPilot/SiK/blob/master/Firmware/radio/packet.c).
- [Matek PDB-HEX](https://www.mateksys.com/?portfolio=pdb-hex), [CubePilot Here 3/3+](https://github.com/CubePilot/cubepilot-docs/blob/master/here-3/here-3-manual.md).
- [Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/), [Hailo/Raspberry Pi AI donanımı](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html), [Hailo model belgeleri](https://github.com/hailo-ai/hailo_model_zoo).
- [Pi 5 H.264 kodlama teknik belgesi](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf).

## 12. Bu bağlamın bakımı

- Kullanıcı yeni bir donanım gerçeği veya karar bildirirse ilgili bölümü tarih/kaynakla güncel tut; eski ve yeni değerleri aynı anda güncelmiş gibi bırakma.
- Ölçüm yapıldıysa test edilen araç, koşullar ve kanıt dosyasını belirt. F450 veya simülasyon sonucunu ana araç doğrulaması yapma.
- Yeni tasarım/uygulama açıkça istendiğinde mevcut aşama bilgisini güncelle; tamamlanmamış işi tamamlandı sayma.
- Yalnızca kesinleşmiş kararları “karar”, önerileri “öneri”, eski bulguları “eski” olarak kaydet. Yeni sohbetler eski varsayımları yanlışlıkla güncel bilgiye dönüştürmemeli.
- Hassas anahtar/parola veya gereksiz kişisel bilgi ekleme. Bu dosyada paylaşılabilir proje bağlamını tut.
- Bu AGENTS.md'yi makul boyutta tut. Tüm sohbet çıktısını veya eski kaynak kodlarını buraya yığma.
