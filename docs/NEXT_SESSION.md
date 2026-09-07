## CANLI SON DURUM — yeni IMX708/model uçuş uygulaması ve kayıt açık

5 Eylül2026 yaklaşık19:14: kullanıcı bu sohbette AUTO testini açıkça istedi, önceki görüş engelinin bank üzerinde durmaktan kaynaklandığını doğruladı; Loiter kalkıp AUTO deneyeceğini bildirdi. Kısa ağ kesintisi düzeldi. Taze DISARM/LOITER/landed1, sağlıklıRC/GPS/EKF/konum doğrulandı. Yeni `config/flight-imx708.json`, observe-imx708 profilinin yalnız runtime dizini ayrılmış kopyasıdır; IMX708 matrisi/sabit lens0,1062771082/tamcrop2304×1296 sensör modu/yeni best.hef/eşik0,40,10m rota ve9m lens hedefi korunur. Kod/kalibrasyon/HEF hashleri doğrulandı.

GÖZLEM2249 temiz kapatılıp **flight PID2458** açıldı; log `runtime/imx708-flight.log`, runtime `runtime/imx708-flight-new-model`. **Kaydedici PID2530**, `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260905T161354Z-2530`, kayıt ilerliyor/0API hata. Kaydedicinin --config desteği Pi'de eksikti; yerel mevcut record.py, eski dosya `runtime/before-imx708-recorder/` altında yedeklenip dağıtıldı,3record testi geçti. Yeni kayıt manifestosu gerçek best.hef hash8433d13e... ve aktif flight-imx708 profilini gösteriyor; eski model hash'i yazılmıyor. Son API flight/WAIT_AUTO/boş actions, DISARM/LOITER, GPS12uydu/HDOP0.87,batarya12.293V ve güncel görüntü/telemetri. Kanıt `artifacts/field/imx708-flight-preparation/`.

ARM/mod/rota/FC parametre komutu gönderilmedi. Pilot AUTO seçerse geçerli hedef koşullarında GUIDED devralabilir; daha önceki kontrol kapalı notları tarihli geçmiş. Yeni kamera/modelin gerçek branda kabulü ve bu yeni uçuşun başarısı henüz doğrulanmadı. Pilot Loiter müdahalesi aynı süreçte kalıcı kilit yaratır; inip yeniden ARM etmek kilidi sıfırlamaz. Uçuşta yeniden başlatma yapılmaz. Sonraki adım kullanıcının uçuşunu salt okunur takip/sonrasında kayıt incelemesidir.

---

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

Yakın kadraj: kullanıcı yaklaşık63cm ölçtüğünü belirsizlikle bildirdi; kesin mesafe doğrulaması sayılmadı. `artifacts/calibration/calibration-imx708-20260905-near63-01/` 5 PNG: SB3/5, klasik5/5 köşe buldu, görsel incelemede desen tam/net ve alt dış bölümde küçük yansıma var; iki SB ret karesi silinmedi. Aynı sabit odak/crop/oturum. Toplam9 poz/45 kaynak, SB43 kare. Yalnız teşhis için80,8cm referans grubu dışarıda tutularak diğer8pozdan birer kareyle ilk çözüm yapıldı: RMS0,0844px, fx949,072/fy948,948; bir poz çıkarma deneylerinde fx945,751–950,684. `imx708-preliminary-diagnostic.json` içinde; kabul edilmiş/etkin kalibrasyon değildir, eski matris kullanılmadı. Sırada yakın konumda iki eksenli eğim, ardından resmi çözüm/bağımsız mesafe kontrolü; uçuş kapalı.

İkinci eksendeki eğim de kaydedildi: `artifacts/calibration/calibration-imx708-20260905-tilt-03/`,5/5 karede54 köşe, sabit odak/crop/oturum. Sağ dış kenarda küçük yansıma var; son karede SB/klasik köşe eşleşmesi ortalama0,163px/en çok0,367px ve görsel köşe QA uygun; nihai çözüm artık hatası ayrıca kontrol edilecek. Toplam8 poz grubu/40 kare, matris henüz yok. Sırada yatay/merkez konumda ekranı fiziksel olarak biraz yaklaştırarak daha büyük dama görüntüsü ve ölçek çeşitliliği var; ekran zoomu/25mm ve odak değişmez.

İkinci eğimde belirgin ekran düzlemi eğimi/yamuk perspektif görüldü; `artifacts/calibration/calibration-imx708-20260905-tilt-02/` içinde5 PNG,5/5 tam54 köşe. Kesin eğim derecesi ölçülmedi. Sabit lens0,1062771082/tam crop/aynı oturum korundu. Toplam7 poz grubu/35 kare; yeni matris henüz yok. Sırada eğimi koruyarak çeyrek tur yön değiştirme ile ikinci eksende eğim, sonra ölçek çeşitliliği var.

İlk eğim isteği sonrası `artifacts/calibration/calibration-imx708-20260905-tilt-01/` içine5 PNG alındı;5/5 karede54 köşe, sabit odak/tam crop/aynı oturum. Görselde düzlem içi dönüş belirgin; gerçek20–30° düzlem eğimi ölçülmedi ve doğrulanmış sayılmadı (`board_plane_tilt_deg=null`). Toplam6 poz grubu/30 kare var; çözüm yok. Daha belirgin kenar yükseltme ile perspektif çeşitliliği istenecek. İlk HTTP isteği zaman aşımına uğradı; tekrarında kamera aynı oturumda taze ve hatasızdı, panel yeniden başlatılmadı.

Alt/arka seri de alındı: Mac `artifacts/calibration/calibration-imx708-20260905-rear-01/`,5/5 karede54 köşe. Şimdi5 poz grubu/25 kare var; yinelenen sabit poz kareleri ayrı poz sayılmaz. Kaynak hashleri ve sabit odak/crop kontrol edildi. Poz özeti `artifacts/calibration/imx708-pose-progress.json`. Yeni matris henüz çözülmedi; sırada merkezde ekran düzlemini eğerek açı çeşitliliği ve farklı görüntü ölçekleri var.

Burun/üst konumundan5 PNG daha alındı;5/5 karede54 köşe bulundu, sabit lens/crop/oturum korundu. Mac kaynakları `artifacts/calibration/calibration-imx708-20260905-front-01/`; Pi kopyası bu seri için yok. Kullanıcı drone burnu ile aynı yöne bakarken önce sağa, ardından burun yönüne taşıdığını bildirdi; görüntüde sağ ve üst hareketi buna uyumlu. Bu kullanıcı beyanı + görüntü kanıtıdır; montaj hassas açısı/ofseti ölçülmedi. Mevcut dönüşü değiştirme. Toplam4 poz grubu (referans, sol, sağ, üst); kalibrasyon henüz çözülmedi. Alt bölge, gerçek düzlem eğimleri ve ölçek çeşitliliği bekleniyor.

Sağ/dikey pozdan da5 PNG alındı;5/5 karede54 köşe bulundu, sabit odak/crop/oturum ve kare tazeliği doğrulandı. Kaynaklar yalnız Mac `artifacts/calibration/calibration-imx708-20260905-right-01/` içinde; Pi kopyası bu aşamada oluşturulmadı. Toplam3 poz grubu var (ilk referans/sol/sağ), yeterli bağımsız konum/eğim çeşitliliği henüz yok. Kullanıcı kamera yönünü sordu: panelde ilave hflip/vflip yok (`Transform(identity)`); yeni kameranın görüntü üstü-burun ve sağ-sağ fiziksel eşleşmesi henüz BİLİNMİYOR. Eski IMX219 montaj beyanı yeni kameraya devralınmayacak.

5 Eylül devamı: sol/dikey pozisyondaki üst yansıma kullanıcı düzeltmesinden sonra giderildi; `artifacts/calibration/calibration-imx708-20260905-left-01/` içinde5 özgün PNG+yan JSON+rapor alındı,5/5 karede54 köşe bulundu ve Mac/Pi PNG hashleri eşleşti. Sabit lens0,1062771082/tam crop/aynı oturum doğrulandı. Bunlar tek poz grubunun tekrarları; toplam ilk referans+sol olmak üzere2 poz grubu var, yeni kalibrasyon henüz çözülmedi. Bu yeni pozun fiziksel mesafesi ölçülmedi; eski80,8cm beyanı bu poza yeniden atanmadı. Sırada sağ konum, alt/üst bölgeler ve gerçek düzlem eğimleri var. Panel kamera-only/sabit odak açık.

5 Eylül17:47 civarı devamı: kullanıcı görüntünün düzeldiğini ve lens-ekran80,8cm/kare25mm olduğunu tekrar doğruladı. Mevcut PID2317'ye SIGUSR1 ile odak kilitlendi; beş taze PNG'de LensPosition0,1062771082 değişmeden ve tam crop ile kaydedildi,5/5 karede9×6 iç köşe bulundu. Görsel incelemede dama net; alt bölümde küçük yansıma var. `artifacts/calibration/calibration-imx708-20260905-reference/` beş PNG+yan dosya+rapor, PNG hashleri Pi ile eşleşti. Bu tek duruşlu referans serisi kalibrasyon çözümü değildir ve yeni matris yoktur. Panel açık/sabit odak; lens sayısı fiziksel mesafe ölçümü sayılmaz. Farklı konum/eğim kareleri ve bağımsız mesafe kontrolleri bekliyor.

Kullanıcının panel isteğiyle ayrı `scripts/camera_panel.py` Pi'de PID2317 ile açıldı; http://172.20.10.4:8080/ . Yalnız Picamera2 ve salt okunur HTTP; Hailo/MAVLink/uçuş uygulaması veya otomatik kontrol açmaz. IMX7081280×720, açıkça2304×1296 sensör modu, tam4608×2592 crop. Taze/ilerleyen kareler ve hata yok doğrulandı. Şu an otomatik odak yalnız önizleme içindir; kalibrasyon için henüz sabitlenmedi. Son PNG'de masa kenarı/zemin var, dama henüz görünmüyor. Önceki kısa test kapalı notu yeni paneli kapsamaz. Kod sözdizimi ve canlı HTTP/PNG kontrolü geçti. Kamera dosyası eski kalibrasyon yüklemez; ana uçuş profilleri değiştirilmedi.

Kullanıcının yazıcısı yok; laptop ekranı kullanılacak. Kullanıcı damaları tam25mm ayarladığını ve80,8cm başlangıç mesafesini bildirdi; bu ölçüler kullanıcı beyanıdır. Desen kadraja geldikten sonra köşe/netlik/yansıma ve odak kontrolü yapılacak. Yeni matris veya mesafe doğrulaması henüz yok. Düz destek kullan; deseni gösterip yakınlaştırmayı sabit tut. Kamera paneli akışı ana uygulamadan ayrıdır; sonraki kalibrasyonun sensör/odak ayarları ana akışa ayrıca uygulanmadan kullanılamaz.

---

## Yeni kamera ön kontrolü - 5 Eylül 2026, 17:30 civarı

Kullanıcı Raspberry Pi Camera Module 3'ü Pi'ye taktığını, kutuda Wide/NoIR yazmadığını bildirdi. SSH üzerinden sensör `imx708`, 4608×2592 ve `imx708.json` tuning dosyası doğrulandı; ticari lens/IR varyantı yalnız sensör adından kesinleştirilmedi. Pi yeni açılmış; kontrol öncesi ve sonrası safak_gorev2/rpicam/libcamera uygulama süreci yok, localhost8080 kapalı. Eski flight2239 artık canlı değil. Uçuş, otomatik kontrol, MAVLink veya Hailo başlatılmadı; yalnız kısa Picamera2 kamera testi yapılıp kapatıldı. Son SoC47,7°C.

Mevcut `create_picamera` açılışı IMX708'de1536×864 sensör modunu seçiyor; listelenen bu mod merkez3072×1728 alanını kullanıyor. Ayrı testte sensör açıkça2304×1296/10bit seçildi:1280×720 RGB888, aynasız, tam `ScalerCrop=[0,0,4608,2592]`,150 farklı sensör zaman damgası, yakalanan akış28,6628FPS. Üç özgün PNG Mac'e alındı ve SHA256 eşleşti. Son görüntü yakındaki açık renkli yüzey; dama/hedef doğrulaması değildir. Kaynak `artifacts/calibration/imx708-precheck-20260905/`, Pi aynı adlı runtime klasörü. Kamera testi sürekli AF ile yapıldı ve lens konumu11-12 arasında değişti; bu kareler kalibrasyon verisi değildir. Eski IMX219 matrisi/ofseti kullanılmadı, uygulama profilleri değiştirilmedi.

Sırada mat kâğıtta düz/sert desteğe sabitlenmiş dama deseni; mevcut A4 PDF yalnız desen olarak kullanılabilir. Gerçek kare kenarları yatay/düşey ölçülecek. Yeni kalibrasyondan önce tam sensör modu ve sabit odak politikası seçilip yakalama/çalışma akışına aynı şekilde uygulanmalı: mevcut varsayılan yakalama/app kodu bu tam alan testini otomatik tekrarlamaz. Otomatik odağı değişen yakın plan kalibrasyonu doğrudan uzak görev odağına taşınmayacak. Yeni matris henüz yok; uçuş/kontrol açılmayacak. Kullanıcıya drone'u sağlam destek üzerinde tutup deseni hareket ettirmesi söylenecek.

---

## Veri ek paketi teslimi — Claude Code ile eğitim hazırlığı

Kullanıcının isteğiyle ilk uçuşun özgün PNG'lerinden25 kare seçildi:9tam,10kesik mavi branda,6negatif/gölge. `output/dataset-ek-20260905/` ve ZIP'i hazır; dosyalar kaynakla SHA256 eşleşiyor ve görüntüler görsel incelendi. Klasörde yalnız images/ eğitim girdisidir; review/ önizlemesi değildir. YOLO kutu etiketleri henüz yok; `CLAUDE_CODE_PROMPT.md` otomatik etiketleme+25görseli inceleme+DJI verisiyle birleştirme+grup bazlısplit+Hailo-8L uyumlu eğitim/FP32-INT8 doğrulama talimatını içerir. Tüm25kare aynı ilk uçuş grubunda tutulmalı; eğitim/test arasında bölünmemeli. Son panel videoları işlenmiş kutu/yazı içerdiğinden eklenmedi. Yeni kamera verisi/kırmızı pozitif yok; eskiDJI ana veri korunmalı. Eğitim başlatılmadı, modele ve Pi'ye bu paket çalışmasında dokunulmadı. Kaynak ve lisans/sürüm kontrolü için resmî Ultralytics/Google/Hailo belgeleri prompt içinde.

---

## Son inceleme — 0,40 denemesinde iki ARM, pilot devri kilidi

5 Eylül 2026: kullanıcı üstünden geçti ama görmedi dedi. `docs/FIELD_FLIGHT_03.md` analizi: aynı PID2239/sortie içinde15:38:08–15:38:52 ve15:39:11–15:40:25 iki ARM aralığı. İlk AUTO ~3,65m; 9,5m devralma sınırına ulaşmadan ~8,33m'de LOITER'a geçilince kalıcı pilot_override açılmış. İkinci ARM/AUTO kilidi sıfırlamamış. 588 ARM örneğinde87mavi kutu,42≥0,40;31kenar/8köşe yok/3metrik geometri reddi,0geçerli hedef. Model gerçek brandayı görüyor; iki metrik ret çevresi tam brandayı gösteriyor. Kesin PnP alt nedeni kayıtta yok. WAIT_AUTO başlığı kilidi gizleyebiliyor; açıklamada pilot kontrolü devri var. Kod/eşik değiştirilmedi. Yerde DISARM doğrulanıp recorder2312 temiz durduruldu; kayıt kapalı. Uçuş uygulaması2239 aynı oturumda ve kilitli; henüz GÖZLEM'e çevrilmedi. Yeni deneme öncesi yerde yeni oturum gerekir, havada kilit sıfırlanmaz. Loglar ve ilgili iki video Mac'te `artifacts/field/flight-03/`;9dosya hash doğrulandı,4erken video yalnızPi'de. Model tek başına neden sayılmamalı.

---

## Batarya değişimi sonrası canlı durum — 5 Eylül 2026

Pi batarya değişiminde yeniden başladı; önceki PID4509/4582 yok. Eski active.json recording yazısı bayattı, canlı kayıt kanıtı sayılmadı. Kullanıcının “taktık kontrol et uçalım” isteğiyle önce GÖZLEM açılarak DISARM/LOITER/landed1, RC/GPS/EKF/konum ve yeni batarya12,50V doğrulandı. Ardından uçuş uygulaması PID2239, bağımsız yeni kaydedici PID2312 başlatıldı. Son API flight, eşik0,40, WAIT_AUTO/boş eylemler; video yeni `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260905T123707Z-2312` içine gerçekten yazılıyor (81 kare, 0 API hatası). Kanıt `artifacts/field/flight-03-battery-restart/`. Eski kayıt güç kesilerek sonlandı; son MKV'nin bütünlüğü henüz incelenmedi. Uçuş/ARM/mod komutu gönderilmedi. Şimdi uçuş uygulaması aktiftir; pilot AUTO seçerse geçerli koşullarda GUIDED devralabilir. Önceki kapalı/PID bilgileri tarihli geçmiş, yeni işlemde canlı durum tekrar okunmalı.

---

## Canlı güncelleme — 0,40 eşikli üçüncü uçuş hazırlığı

Kullanıcı dışarıda/kumanda açık bildirip uçuş uygulamasını başlatmayı istedi. Kısa SSH/ağ gecikmesinin ardından yerde DISARM/LOITER/landed1, RC/GPS/EKF ve konum güncelliği doğrulanarak GÖZLEM kapatıldı; `--mode flight --config config/flight.field-candidate.json` PID4509 başlatıldı. Yeni bağımsız video/telemetri kaydedicisi PID4582, kayıt `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260905T123203Z-4582`; yazılan kare sayısı 185, durum recording doğrulandı. Son API WAIT_AUTO, boş eylemler, 0,40 eşik, hatasız Hailo/USB; GPS 11 uydu, HDOP 0.98, batarya 11.45 V. Kanıt `artifacts/field/flight-03-preparation/`. Henüz bu üçüncü uçuşun gerçekleştiği/başarısı doğrulanmadı. ARM veya mod komutu gönderilmedi; pilot manuel Loiter kalkış ve AUTO seçimi yapacak. Uçuş uygulaması artık açık, koşullar sağlanınca GUIDED devralabilir. Başarılı temsili bırakmadan sonra RTL; hedef yoksa mevcut AUTO rotasının son LAND'i geçerlidir. Aşağıdaki kontrol/kayıt kapalı notları bu güncellemeyle tarihli geçmiş. Aktif uygulamayı havada yeniden başlatma; sonraki işlemde canlı durumu oku.

---

## Son kullanıcı kararı — geçici eşik 0,40

5 Eylül 2026: kullanıcı mevcut kamerayla kısa bir sonraki test için yalnız eşiğin düşürülmesini istedi. `config/flight.field-candidate.json` içinde 0,50 → **0,40** uygulandı; kayıttaki yaklaşık 0,42 tam branda adayını skor kapısından geçirmeyi amaçlar. Köşe/kadraj/geometri/süreli kilit, model, FC/rota aynı; varsayılan ve diğer profiller değiştirilmedi. Pi taze DISARM/landed=1/observe iken profil yedeklendi ve yalnız GÖZLEM yeniden açıldı (PID 4409). Canlı Hailo/API 0,40 ve hatasız akış doğrulandı, Mac/Pi profil hash'i eşleşti. Kanıt `artifacts/field/threshold-040/`. Otomatik kontrol ve video kaydı hâlâ kapalı; yeni uçuş başlamadı. Bu geçici deneme model kaynaklı sorunu tek başına kesinleştirmez; gölge adaylarını da artırabilir. Sonraki plan kullanıcının yeni gelen kamerasını takıp o kameraya özgü kalibrasyon ve model çalışmasıdır; kamera modeli henüz bildirilmedi, eski kamera kalibrasyonu devralınmayacak. Önceki 0,50 sabit tutma talebi bu açık eşik değişikliği isteğiyle bu profil için güncellendi.

---

# Son durum — ilk AUTO uçuşu incelendi, kontrol kapalı

5 Eylül 2026 15:00–15:01 Loiter → AUTO uçuşu yapıldı. Gölgeye yanlış mavi kutular var; tam branda örneklerinde skor yaklaşık 0,42, eşik üstü AUTO örneklerinde branda kesik. İki bağımsız 5 Hz kayıtta geçerli hedef 0; SQLite olaylarında GUIDED/bırakma yok. Üç MKV ve loglar Mac `artifacts/field/flight-02/` içine alındı, 9 kaynak hash doğrulandı. Rapor: [FIELD_FLIGHT_02.md](FIELD_FLIGHT_02.md).

Ham kutulara AI ADAYI ibaresi ve kareyle eşlenmiş ret teşhisi eklendi; kabul/0,50 eşiği/model/FC/rota değişmedi. 75 test geçti, 4 Torch testi atlandı. Yerde DISARM doğrulandıktan sonra Pi yalnız GÖZLEM ile yeniden açıldı: PID4307, `runtime/post-flight-02-diagnostics.log`. Eski flight4029 ve recorder3787 kapalı; kayıt temiz tamamlandı. Yeni uçuş/kayıt kendiliğinden başlamaz. Yeni uçuş öncesinde canlı durum tekrar okunmalı; aşağıdaki aktif uçuş/kayıt PID notları tarihli geçmiş ve bu güncellemeyle geçersizdir. Dedektörün gölge hatası çözülmüş veya görev başarısı doğrulanmış sayılmaz.

---

# Son pilot tercihi — ayrı Loiter hedef kontrolünü istemiyor

Kullanıcı ek 10 m Loiter hedef kontrolünü istemediğini, manuel Loiter kalkışından sonra doğrudan AUTO'ya geçeceğini bildirdi. Bu son tercih önceki ayrı kontrol talebini değiştirir; fiziksel hedef/kadraj veya sürekli kilit doğrulanmış sayılmaz. Yazılımın skor/köşe/geometri/zaman kilidi koşulları gevşetilmedi. Son canlı kontrol flight/manual/RTL dönüşü/9m hedef, WAIT_AUTO/boş actions, DISARM/LOITER, RC sağlıklı, GPS11uydu/HDOP1,02 ve güncel kamera/telemetri gösterdi. Kanıt `artifacts/field/flight-02-preparation/pilot-auto-intent-*.json`. Kayıt PID3787 recording; biriken API hata sayısı653 hazırlıktaki uygulama kapalı aralıklarını da içeriyor, toplam sıfır hata denmez.

Geçerli hedef bulunursa GUIDED ve kilit sonrası temsili bırakma/RTL; bulunmazsa mevcut AUTO rotası sürer ve rotanın mevcut son LAND maddesi kalır. RTL yalnız başarılı temsili bırakma sonrası veya FC'nin yapılandırılmış failsafe durumları içindir; her başarısız taramada otomatik HOME dönüşü eklendiği söylenmez. Kullanıcıya görev başarısı garanti edilmedi. Aktif uygulamayı havada yeniden başlatma; ilk gerçek uçuş durumunu salt okunur izle.

---

# CANLI SON DURUM — bırakma sonrası RTL sürümü açık

5 Eylül 2026: kullanıcı son LAND yerine kalkış yerine RTL dönüşü ve failsafe için RTL istedi. Kumanda kaybı olarak ele alınan failsafe mevcut FC’de zaten `FS_THR_ENABLE=1`, `FS_OPTIONS=16`, `RC_FS_TIMEOUT=1`; RTL_ALT=1500 cm, RTL_ALT_FINAL=0, RTL_LOIT_TIME=5000 ms, RTL_CLIMB_MIN=0, RTL_ALT_TYPE=0, RALLY_TOTAL=0 okundu. Düşük batarya eylemi2/RTL, kritik batarya1/LAND; FS_GCS_ENABLE=0. Bunlar değiştirilmedi; bütün failsafe türleri RTL yapıldı denmez. ARM öncesi HOME okundu ama ARM sonrası HOME henüz doğrulanmadı. Kanıt `artifacts/field/flight-02-preparation/rtl-preparation-20260905.json`. RTL davranışı ve home [ArduPilot RTL belgesi](https://ardupilot.org/copter/docs/rtl-mode.html), RC kaybı [radio failsafe belgesi](https://ardupilot.org/copter/docs/radio-failsafe.html) ile karşılaştırıldı; kurulu 4.5.7 parametre isimleri/değerleri esas alındı.

`mission.return_mode="rtl"` eklendi; varsayılan son LAND akışı korunuyor. Yalnız temsili bırakmanın diske yazılması doğrulandıktan sonra RTL istenir; taze RTL heartbeat doğrulanınca Pi komut sahipliğini bırakır. Otomatik dönüş/iniş FC’dedir. Loiter müdahalesi kalıcı PILOT_CONTROL; onaylanmayan RTL geçişi iptal edilir. RTL dönüşü sonunda taze DISARM/landed=1 görülmeden DONE sayılmaz. 74 test geçti/4 model-runtime atlandı. Manuel kalkış + tam görev + RTL entegrasyonu gerçek yerel 4.6.3 SITL’de geçti: `artifacts/sitl/manual-rtl/complete/result.json`; son mod RTL/DISARM/landed1, sentetik HOME yatay farkı 0,028 m (fiziksel doğruluk iddiası değil).

Yalnız yerde DISARM/Loiter doğrulanarak Pi kodu yedeklendi (`runtime/before-rtl`) ve yenilendi. **Aktif uçuş uygulaması PID 4029**, `--mode flight --config config/flight.field-candidate.json`, log `runtime/field-manual-rtl-20260905.log`; profil hash `e3f5d40c5afa5cd7b95d18322f9dbebed40bfb2ba88f747ee2442cb3933a9beb`. Canlı API flight/manual/return_mode=rtl, hedef9m, WAIT_AUTO/boş actions, DISARM/LOITER, RC sağlıklı, GPS13uydu/HDOP0,81 gösterdi. Son kayıt `rtl-flight-ground.json`. FC görevi/parametresi ve ARM komutu gönderilmedi. Tarama10m, lens hedef9m, alt sınır8,5m, devralma alt irtifası9,5m korunuyor.

Kullanıcı kalkınca doğrudan AUTO’ya geçmek istedi; **önce Loiter’da10m tam branda/kadraj/geçerli hedef doğrulaması, bundan önce AUTO’ya geçmemesi** tekrar bildirildi. Henüz gerçek uçuş/temsilî bırakma başarısı doğrulanmadı. Bir sonraki adım bu Loiter uçuşunu okumaktır; uygulama uçuş modunda olduğundan AUTO’ya alınırsa geçerli koşullarda devralabilir. Eski LAND/GÖZLEM/PID notları aşağıda tarihli geçmiş.

Kaydedici PID3787 bağımsız sürüyor; video oturumuna `rtl-software-config.zip` ve `rtl-start-ground-status.json` eklendi. Kısa uygulama geçişlerinde API hata satırları kaydedilmesi beklenen davranıştır; video önceki kareyi canlı göstermez.

---

# CANLI DURUM — manuel kalkışlı uçuş uygulaması açık

5 Eylül 2026 dışarıdaki son yer kontrolü: kullanıcı kumanda açık/Loiter seçili bildirdi; Pi bunu doğrudan doğruladı: DISARM/LOITER/landed=1, RC sağlıklı/slot 6/LOITER, GPS 11 uydu/3D fix/HDOP 1,00, EKF 831; Hailo ve telemetri güncel, hata yok. Kullanıcının uçuş yazılımını başlatma isteğiyle GÖZLEM temiz kapatıldı; **`--mode flight --config config/flight.field-candidate.json`** başlatıldı. O anda PID **3841**, log `runtime/field-manual-flight-20260905.log`. Canlı API flight/manual, hedef lens yüksekliği 9 m, WAIT_AUTO/boş actions, yerde DISARM/LOITER gösterdi. Uçuşa geçilmiş veya fiziksel hedef doğrulanmış sayılmaz.

Aktif test profili: tarama rotası 10 m (mevcut FC rotası), devralma relative-alt alt sınırı 9,5 m, lens hedefi 9 m, görsel alt sınır 8,5 m; eşik 0,50. Eski 3,5 m kullanılmıyor. Pi profil hash'i `18f603fd4ce25164b691ea62cf24532324ba40f5d924fb2013264c37c6448cc3`; açılış kanıtı `runtime/flight-start-20260905/`, Mac kanıtı `artifacts/field/flight-02-preparation/flight-mode-ground-*.json`. FC parametresi, rota veya ARM komutu gönderilmedi.

**Sıradaki aşama pilot kontrollü Loiter'da 10 m tam branda/kadraj ve geçerli hedef kontrolüdür. Kullanıcıya bunu doğrulamadan AUTO'ya geçmemesi söylenecek.** Yazılım Loiter'da kontrol devralmaz; kumanda AUTO'ya alınırsa koşullar sağlandığında GUIDED devralması mümkün hale gelir. Bu yüzden artık “otomatik kontrol kapalı/gözlem” deme: uçuş modu açık fakat yerde/Loiter'da bekliyor. Yerde DISARM görülmüştür. Pilot devrinin aynı çalıştırmada kalıcı olduğu korunur.

Kaydedici PID 3787 uygulama yeniden başlatılırken açık kaldı; son JSONL içinde `mode=flight` doğrulandı. Asıl kayıt `runtime/recordings/20260905T113439Z-3787/`; aktif uçuş profili ve başlangıç yer durumu bu klasöre de eklendi. Kayıt/gözlem eski PID notlarını aşağıda tarihli geçmiş olarak oku; canlı işlemler öncesi yeniden doğrula.

---

# Etiketli video ve uçuş log kaydı açık

5 Eylül 2026: kullanıcı dışarı çıkmadan Pi'de bu uçuşun ekran/video ve uçuş loglarının kaydedilmesini istedi. `safak_gorev2.record` ayrı süreç olarak eklendi; kamera veya MAVLink açmaz, localhost panelini okur. Etiketli panel kamera JPEG'i + saat/mod/ARM/GPS/RC/irtifa/AI kutu ve geçerli hedef sayısı HUD'u 960×700, 8 FPS MJPEG/MKV olarak 30 saniyelik parçalara kaydeder. Bu tarayıcı penceresinin birebir piksel kaydı veya tam 30 FPS ham görüntü değildir. Telemetri/API JSONL yaklaşık 5 Hz; her video karesinin kaynak kimliği, yaşı, tekrar durumu ve zaman damgası ayrı JSONL'dedir. ARM/DISARM geçişleri taze heartbeat ile işaretlenir. Yazılım/config ZIP'i ve HEF hash'i oturumda saklanır. Mevcut uygulamanın `telemetry-*.jsonl` ve olay SQLite kayıtları da sürer; Pixhawk DataFlash `.BIN` indirildiği iddia edilmez.

Pi denemesi `runtime/recording-check/20260905T113216Z-3756`: 35 saniye, iki okunabilir MKV (30+5 s), 280 video karesi, 176 telemetri örneği, 0 görüntü/API hatası. ffprobe tüm kareleri okudu, önizleme görsel olarak incelendi. Testte Hailo minimum örnek FPS 29,79, kısa sıcaklık 58,2 °C/throttled=0x0. Yerel kanıt `artifacts/field/recording-check/`. Yeni bağımsız kayıt aracı için 3 test geçti; uçuş kontrol kodu bu eklemede değişmedi.

Asıl kayıt Pi'de o anda PID **3787** ile başlatıldı, bağımsız süreç ve yerel HTTP kullanır; laptop/SSH bağlantısından ve gözlem→uçuş uygulama yeniden başlatmasından bağımsız sürer. Güncel durum `/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/active.json`, süreç logu `runtime/flight-video-recorder.log`. Kayda son vermek için yalnız doğrulanan kaydedici PID'sine SIGTERM gönderilir; video düzgün kapatılır. Uçuş sonunda kaydı durdurup manifest/video/logları doğrulayarak Mac'e kopyala. Pi güç kaybında otomatik yeniden başlatma servisi kurulmadı; tekrar açılışta kaydediciyi yeniden doğrula/başlat. Kaynak uygulama kapalıysa hata/eksik görüntü işaretli kayıt tutar; eski görüntüyü canlıymış gibi sunmaz. Disk 1 GB altına inerse hata durumuyla kaydı kapatır, uçuşa komut vermez.

Kamera/görev uygulaması hâlâ GÖZLEM (son PID 3625), otomatik kontrol kapalı. Kullanıcıya dışarıdaki yer kontrollerine geçebilecekleri bildirilecek; yeni dışarıda hazır bildirimi bekleniyor. 10 m rota, gerçek GPS/RC/Loiter ve tam hedef doğrulaması sonrasında değerlendirilecek. Kaydın çalışması uçuşa hazır olma kanıtı değildir.

---

# Güncel öncelik — mevcut modelle gerçek Görev 2 testi hazırlığı

5 Eylül 2026, son kullanıcı kararı: yeniden eğitim/HEF incelemesi ertelendi. Kullanıcı yaklaşık 350 DJI fotoğrafıyla asfalt zeminde ilk modeli eğittiklerini; beyaz taşlı test alanından 30 küsur mavi branda fotoğrafı ekleyip yeniden eğittiklerini ve verilen modelin bu son sürüm olduğunu bildirdi. Yarışma alanını toprak/asfalt ağırlıklı gördükleri için yeni beyaz zemin verisi eklemek istemiyorlar. Bunlar kullanıcı beyanıdır; veri seti bu oturumda incelenmedi. Önceki “beton” açıklamasını güncel zemin tanımı olarak kullanma. Model kararsızlığını yalnız zemin farkına kesin bağlama.

Kullanıcı 1–2 gün kaldığını, pilot/quad/branda hazırlığıyla gerçek Görev 2 testine geçmek istediğini bildirdi. Son yanıt: Pixhawk açık ve bağlı, batarya ve mavi branda hazır. Bu yeni istek saha hazırlığını yetkilendirir; ARM veya otomatik kontrol kendiliğinden başlatılmadı. Görev 1 değişmez.

Pi'de GÖZLEM yeniden açıldı. İlk güncel kayıt `artifacts/field/flight-02-preparation/status-initial.json`: DISARM/STABILIZE, GPS fix 1 / 0 uydu, RC sağlıksız, yerel konum verisi yok; TAKEOFF içermeyen rota reddediliyor. Kamera/Hailo ve USB güncel, aynı crop, eşik 0,50. Kullanıcıdan yerde kumandayı açıp Loiter seçmesi ve açık gökyüzü altında GPS beklemesi istendi. Görev 2 rota dosyası soruldu; yanıt bekleniyor. Bu anlık durumu gelecekte tekrar doğrula.

Yerel `config/observe-field.json` aday kamera matrisini yalnız gözlem değerlendirmesi için bağlar; matris `config/camera.field-candidate.json` içinde kaynakla aynıdır. Ekranda 60 cm/sabit 80 cm kontrolleri mevcut; gerçek 2 m hedef/metre ölçeği doğrulanmış sayılmaz. Eski 3,5 m alçalma hedefi bu crop'ta 2 m brandayı kadrajda tutamaz; bu ayarla otomatik uçuş açılmamalı. Uygun test yüksekliği ve başlangıç TAKEOFF/tarama/son LAND rotası saha ile birlikte doğrulanmalı. Rota veya FC parametresi yazılmadı.

PT/ONNX karşılaştırması tamamlandı: aynı 81 gerçek Hailo girişinde PT ve yeni ONNX 81/81 eşleşti; tam 9 brandada skor ≥0,50 HEF 0, PT 8. 017 gölgesi PT'de de var. İki Ultralytics sürümü aynı sonucu verdi. Mevcut HEF'in checkpoint/dönüştürme kökeni kesinleştirilmedi, yeni HEF üretilmedi. Ayrıntı [MODEL_COMPARISON.md](MODEL_COMPARISON.md). Aşağıdaki kayıtlı teşhis tamamlanmıştır; daha fazla eğitim araştırması güncel öncelik değildir.

## Son saha hazırlığı güncellemesi

Kullanıcı TAKEOFF kullanmayacağını; manuel kalkıp kumandadan AUTO'ya geçeceğini açıkladı. `mission.takeoff_mode="manual"` yalnız bu quad testinde eklendi; varsayılan `auto` ve TAKEOFF denetimi korunuyor. Manuel seçenekte ilk gerçek rota maddesi waypoint olmalı, TAKEOFF olmamalı, son LAND açık koordinat taşımalı. DISARM görülmesi, havada/yeterli irtifada olma, AUTO/RC seçimi, bağımsız hedef kilidi ve pilot devri korunuyor. Görev 1'e dokunulmadı.

66 test geçti; model ortamı isteyen 4 test bu normal ortamda atlandı. Yeni manuel kalkış akışı gerçek yerel ArduCopter 4.6.3 SITL'de pilot RC ile Loiter kalkış → AUTO → GUIDED merkezleme/alçalma → tek temsili bırakma → son LAND/DONE olarak geçti: `artifacts/sitl/manual-takeoff/complete/result.json`. Bu deney sentetik görüntüyle 6 m arama / 3,5 m hedef simülasyon değerlerindedir; önerilen gerçek 10/9 m ve fiziksel kamera/HEF başarısını doğrulamaz.

Pi gözlem uygulaması güncel DISARM doğrulandıktan sonra temiz kapatılıp değişen 5 dosya yedeklenerek yenilendi. Yedek `runtime/before-manual-takeoff/`; yeni süreç o anda PID 3521, `--mode observe --config config/observe-field.json`, log `runtime/field-calibrated-observe-20260905.log`. Canlı API `takeoff_mode=manual`, preflight/pipeline_error boş, kalibrasyonlu gözlem ve aynı Hailo/crop gösterdi. GPS/yerel konum olmadığından metrik hedef henüz hesaplanamıyor. Güncel kayıt `status-calibrated.json`.

Pixhawk'tan okunan rota home + altı 10 m waypoint + açık koordinatlı son LAND (seq 7); TAKEOFF yok ve manuel seçenekle kabul edildi. Görev yüklenmedi/değiştirilmedi. Kullanıcıya tarama için 10 m başlangıç adayı söylendi; hedefin gerçek kadrajı pilot kontrollü görüntüyle teyit edilecek. `config/flight.field-candidate.json` yalnız Mac'te hazırlanan, dağıtılmamış adaydır: lens hedefi 9 m, alt sınır 8,5 m, devralma relative-alt alt sınırı 9,5 m. Henüz etkin uçuş ayarı değildir; gerçek hedef/mesafe ile birlikte değerlendirilmelidir. Eski 3,5 m hedef kullanılmayacak.

Kullanıcı son yanıtında binanın içinde olduklarını ve kumandanın kapalı olduğunu açıkladı; GPS 0 uydu/RC sağlıksız okumasının bağlamı budur. Yazılım hazırlığı sonrası dışarı çıkacaklar. Dışarıdaki yer kontrollerine geçebilecekleri bildirildi; henüz dışarıda hazır yanıtı yok. Kullanıcı AUTO/GUIDED sırasında Loiter ile kontrolü alabilmeyi özellikle sordu. GUIDED→Loiter manuel kalkış SITL deneyi geçti; AUTO taraması sırasında da kalıcı kilit için eksik durum bulundu ve düzeltildi. Son test toplamı 68 geçti, model runtime isteyen 4 atlandı; AUTO taraması Loiter regresyonu ve bekleyen claim komutunun engellenmesi kapsandı. AUTO taraması Loiter SITL deneyi de PILOT_CONTROL/gerçek SITL LOITER ile geçti. Son Controller/MAVLink düzeltmesi Pi’ye DISARM iken yedeklenerek dağıtıldı. Son GÖZLEM PID 3625, log `runtime/field-calibrated-observe-final-20260905.log`; değişen 5 kod dosyasının Pi/Mac hashleri aynı. Kanıt `artifacts/field/flight-02-preparation/deployment.json` ve `status-final.json`. Hailo/USB güncel, manuel rota kabul ediliyor; kontrol kapalı. Dışarıdaki yer kontrollerine geçebilecekleri bildirildi. GÖZLEM açık; otomatik kontrol, ARM, uçuş veya gerçek yük komutu gönderilmedi. Sonraki canlı adımda bu durumu yeniden okuyun.

---

# Güncel sonuç — kayıtlı görüntüyle hat doğrulaması tamamlandı

5 Eylül 2026: Kullanıcının kayıtlı 81 kareyle teşhis planı uygulandı. `python -m safak_gorev2.replay recorded|hailo` eklendi; 168 kaynak hash'i, 81 kimlik, 54 mavi kare / 63 kutu / 4 eşik üstü kare yeniden üretildi. Pi'de aynı gerçek 640×640 RGB UINT8 tensörle TAPPAS ve doğrudan HailoRT karşılaştırıldı: 81/81 ham NMS birebir aynı; recorded/replay 81/81 eşleşti. 0,5097429156 HEF NMS sonucunda zaten var. 114 dolgulu, 140 px üst/alt letterbox dönüşümü 81/81 tensörle bayt bayt eşleşti. Renk/ölçek/sınıf/skor çözümleme hatası kanıtlanmadı; HEF ve eşik 0,50 değişmedi. Gölge 017 ve kesik hedef 032/035/036 mevcut şartlarla reddediliyor; tam kabul ön koşulunu geçen aday 0. Geometri sınır/doluluk şartları ortak teşhis yardımcısına alındı, kabul davranışı değişmedi. 56 test geçti. 81 görsel etiket: 9 tam, 47 kesik, 24 hedefsiz, 1 belirsiz. Eğitim etiketi veya saha geneli başarı ölçümü değil.

Ayrıntı ve kullanım: [DETECTION_REPLAY.md](DETECTION_REPLAY.md). Yerel kanıt `artifacts/replay/`; Pi'de ayrı `/home/furkan/Desktop/safak-gorev2-replay-20260905/results-final`. Kamera/panel/MAVLink/kontrol açılmadı; mevcut uygulamaya dağıtım yapılmadı. Eski “sıradaki iş tespit hattı incelemesi” notları aşağıda tarihlidir ve bu sonuçla tamamlanmıştır. Sonraki model aşamasında veri/etiketler, checkpoint–ONNX–HEF ilişkisi, DFC/alls/kalibrasyon verisi/derleme kayıtları gerekir; yeniden eğitim başlatılmadı. Gerçek 2 m hedefle sabit mesafe/kadraj kontrolü ayrıca planlanacak; bu çalışma yeni uçuş yetkisi olarak yorumlanmayacak.

---

# Sonraki fiziksel oturum

**Güncel sonuç — uçuş kaydı kurtarıldı ve incelendi:** 11:00:08–11:01:29 (Türkiye saati) Loiter uçuşundan 81 özgün PNG, eşleşmiş Hailo JSON ve telemetri Mac'te `artifacts/field/flight-01/` içine alındı; 168 kaynak dosyanın SHA256'sı eşleşti. Yeniden uçuş bu inceleme için gerekmiyor. 54 karede mavi tespit var; 0,50 eşiğini geçen dört karenin biri insan gölgesi, diğer üçü kenardan kesilmiş branda. Mevcut OpenCV köşe/sınır/doluluk kontrolleri bu dört adayı reddediyor. Düşük skorlu sekiz aday sadece teşhis amacıyla geometri ön koşulunu geçti; eşik 0,50 kaldı. Ayrıntı [FIELD_FLIGHT_01.md](FIELD_FLIGHT_01.md).

Sıradaki iş kaydedilmiş gerçek görüntülerle model giriş/çıkış zinciri ve yanlış gölge tespitini incelemek; otomatik kontrolü açmak veya sırf skor düşük diye eşik düşürmek değil. Kullanıcı son bağlantı geri geldiğinde UBEC ayrıntısını erteleyip uçuş testine geçmek istedi; bu bilgi fiziksel güç doğrulaması sayılmadı. Son kontrolde SSH erişilebilir ama GÖZLEM süreci yok ve localhost 8080 kapalı; uygulama yeniden başlatılmadı. Sonraki canlı işlem öncesinde durumu tekrar kontrol edin.

**Uçuş öncesindeki bağlantı kesintisi notu:** kullanıcı quad bataryasını **3S**, kumandayı açık ve aracı DISARM/Loiter bildirdi. Bu yanıtın ardından API okuması zaman aşımına uğradı; açık SSH oturumu “Host is down” ile kapandı. Mac'ten hotspot `172.20.10.1` iki ping'i yanıtladı; Pi `172.20.10.4` yanıtlamadı. Loiter geçişi ve sağlıklı RC henüz Pi'den doğrulanamadı. Bu ağ kesintisi, aşağıda başlatıldığı doğrulanan GÖZLEM'in durduğunu kanıtlamaz. Kullanıcı Windows ve Mac'ten panelin açılmadığını, hotspot'un yakın olduğunu bildirdi. Pi frame güç dağıtımından UBEC ile besleniyor; çıkış V/A, Pi güç girişi ve güç ışığı davranışı soruldu, yanıt bekleniyor. IPv6 SSH denemesi de zaman aşımına uğradı; kesintinin nedeni belirlenmedi. Uçuş kaydı alınmadı. Kanıt `artifacts/field/20260905-loiter-ground/connectivity-report.json`.

**Kesintiden önce doğrulanan GÖZLEM başlangıcı:** kullanıcı test yerine ulaştıklarını, gerçek brandayı serdiklerini ve Windows PC'de Mission Planner'ı telemetriyle bağladıklarını bildirdi. Geçici ağ kesintisinden sonra kullanıcı tekrar denememizi istedi; `172.20.10.4` SSH bağlantısı kuruldu. Kimlik bilgileri dosyalara kaydedilmedi. Çalışan uygulama olmadığı ve Pixhawk USB'nin bulunduğu okundu; mevcut launcher ile `--mode observe --config config/quad.json` başlatıldı (o anda PID 2174; log `runtime/field-observe-20260905T074141Z.log`). Canlı API gerçek HAILO/IMX219, aynı crop, eşik 0,50, ArduCopter 4.5.7, STABILIZE/DISARM, GPS fix=3, 11 uydu, HDOP 1,32, taze duruş/konum/heartbeat ve hatasız bağlantı gösterdi. RC henüz sağlıksız; kullanıcı kumandanın kapalı olduğunu bildirmişti. Batarya 12,52 V; quad bataryasının hücre sayısı soruldu, yanıt bekleniyor. Kullanıcıdan kumandayı açıp DISARM iken Loiter seçmesi ve varsa Mission Planner PreArm uyarısını bildirmesi istendi. Kanıt `artifacts/field/20260905-observe-start/`. İlk PNG yakındaki bulanık yüzeyi gösteriyor; gerçek tam branda/uçuş kaydı değil. Hazırlık ve saha koşulları doğrulanınca pilot kontrollü Loiter'da GÖZLEM kaydı öneriliyor; otomatik merkezleme/alçalma açılmadı.

5 Eylül 2026 devam oturumu: kullanıcı laptop ölçümlerinin tamamlandığını ve gerçek 2 × 2 m mavi branda ile quad'ın yanında olduğunu bildirdi. Sonraki açıklamasında atölyede tam brandayı sabit düzende kadraja sokmanın büyük olasılıkla mümkün olmadığını, bahçeye çıkıp test yapabileceklerini söyledi. Sıradaki adım bahçede **yerde, DISARM iken RC/GPS ve bağlantı kontrolü**; hazırlıklar uygunsa pilot kontrollü Loiter sırasında GÖZLEM görüntüsü alınması önerildi. Kullanıcının dışarıda hazır bildirimi bekleniyor; uçuş veya gerçek branda kaydı henüz yapılmadı. Gerçek hedef/saha kayıt akışı [FIELD_SESSION.md](FIELD_SESSION.md) içinde. İlk canlı ön kontrolde observe, DISARM ve taze Hailo/USB doğrulandı; PNG'de hâlâ laptop ekranı vardı. Kamera/crop değişmedi.

Pi'deki yeni uygulama `/home/furkan/Desktop/safak-gorev2-quad` klasöründedir. Kullanıcı sabah uyandığını, Pixhawk USB bağlantısını yaptığını ve hazır olduğunu bildirince kamera/Hailo ve panel gözlem modunda yeniden açıldı. Otomatik başlatma servisi kurulmadı. Eski Hailo ortamı korunuyor. SSH parolası hiçbir proje dosyasına yazılmadı.

## Güncel geçici eşik

5 Eylül 2026: kullanıcının isteğiyle quad test ayarındaki `camera.confidence_min` 0,65 → **0,50** yapıldı ve Pi gözlem uygulamasına uygulandı. Genel `CameraConfig` varsayılanı 0,65 kalıyor. Kullanıcı brandaların eğitim fotoğraflarını DJI ile beton zeminde farklı irtifa/açılardan çektiklerini, gelecek saha zemininin beyaz taşlı olduğunu bildirdi. Bu, veri seti incelemesi veya düşük skorun kesin nedeninin tespiti değildir. Kayıtlı 20/20 mavi kare yeni skor koşulunu geçer; geometri/tazelik/merkezleme/süreli kilit koşulları ayrıca gerekli. Gerçek saha pozitif/negatif örnekleriyle eşik yeniden değerlendirilecek; kabul edilmiş uçuş başarımı sayma. 35 test geçti. Son canlı API 0,50, taze kamera ve heartbeat, hatasız Hailo/USB gösterdi. Kanıt `artifacts/pi/status-threshold-050-20260905.json`; o andaki PID 3422, daha sonra yeniden doğrulanmalı. Son sıcaklık 57,6 °C, throttled=0x0.

## Önce gerçek görüntü ve kalibrasyon

Laptop ön kontrolü alındı: kullanıcı mavi kareyi 15 × 15 cm ölçtüğünü, aynı sabit kamera/ekran düzenini kullandığını ve mesafenin 80,8 cm olduğunu bildirdi (önceki cetvel 80 cm, hesap 80,0818 cm; yeni cetvel ölçümü varsayılmadı). `artifacts/blue-target/screen-check-02/` içinde 20 özgün PNG ve aynı karelerin gerçek Hailo tespit JSON'ları var: 20/20 mavi_hedef, skor 0,5097; kayıt sırasında geçerli 0,65 eşiğini 0/20 geçti. Teşhis amaçlı AI ROI + OpenCV kare + kamera göreli PnP ile ortanca 81,142 cm. Bu, görev kabulü/quad merkezleme veya gerçek 2 m hedef doğrulaması değil. Bu kayıt sırasında eşik ve aktif 2 m ayarı değiştirilmedi; sonraki geçici eşik değişikliği yukarıda. Ekran ön kontrolü tamamlandı; sırada gerçek yüzey/negatif örnek ve görüş alanı kontrolü var. Mevcut kamera ayarı değişmezse yeni dama çekimi planlanmıyor.

Yakalama aracı artık her PNG için kare kimliği, oturum, backend ve gerçek AI kutularını JSON yan dosyasında saklıyor. Panel API ve telemetri kayıtları ham tespitleri de gösteriyor. 35 test geçti. Önceki çekim oturumunda gözlem uygulaması PID 3281 olarak aynı Hailo ortamında yeniden başlatıldı; yaklaşık 46 dakika önce kopmuş Pixhawk bağlantısı yeniden kuruldu. Son kontrolde taze heartbeat, STABILIZE/DISARM ve bağlantı hatası yok. PID'nin gelecekte hâlâ aynı sürece ait olduğunu varsayma.

Işıklı ortamda mavi 2 × 2 m hedef ve kırmızı bir örnek gösterilerek modelin sınıf/renk eşlemesi kontrol edilecek. Bugünkü donanım deneyi yalnız gerçek kamera ve HEF çıkarım hattının çalışmasını kanıtladı. Uçuşa özgü hedef doğruluğu ölçülmedi.

Mevcut IMX219 için 55 incelenmiş kareyle RMS 0,471 px aday kalibrasyon hazır: `artifacts/calibration/imx219-screen-20260905-review/camera.candidate.json`. Toplam 115 özgün görüntü A/B/C serilerinde korundu; ilk 40 karelik seri tek başına yeterli değildi. Sonraki 75 kareyle kadraj/açı çeşitliliği sağlandı; seçim manifestosu ve teşhis raporu review klasöründe. Kullanıcı kareleri 25 mm bildirdi. Ekran deseniyle 60 cm ve sabit 80 cm karşılaştırmaları kaydedildi; gerçek 2 m hedef ve operasyon mesafesi doğrulaması bekliyor. Aday uçuş config'ine uygulanmadı.

İlk mesafe karşılaştırması alındı: kalibrasyona katılmayan 18 kare ve kullanıcının 60 cm lens–ekran dik mesafe beyanı. Hesap ortancası 60,605 cm; fark +0,605 cm (yaklaşık %1,01). Sonraki “80 cm” beyanlı iki kayıtta uyuşmazlık var: `imx219-distance-check-02` 18 karenin 14'ünde 73,213 cm ortanca, `imx219-distance-check-03` 10 karenin 9'unda 71,878 cm ortanca. İkinci kayıt kullanıcının “tamam 80 al hemen şimdi” mesajından hemen sonra alındı. Kamera/crop aynı, son işaretli köşeler gözle incelendi. Dosyalar `artifacts/calibration/` altında, her birinde `distance-report.json` var.

Sonraki **sabit 80 cm** kontrolü alındı: kullanıcı ikisini de sabitlediğini bildirince `imx219-distance-check-04` içine 10 farklı özgün kare kaydedildi. Aynı matris ve kare ölçeğiyle tümünde uygun köşeler, ortanca 80,0818 cm, aralık 80,0692–80,0840 cm bulundu. Görsel inceleme yapıldı; kamera/crop aynı. Önceki 8 cm fark bu kayıtta yok; eldeki kayıtların farkını tek bir nedene kesin bağlama. Cetvel belirsizliği bilinmediğinden bu farktan milimetre doğruluk garantisi üretme. Son kısa kaydın bittiği bildirildi. Sıradaki fiziksel iş gerçek 2 m mavi hedef, metre ölçeğindeki mesafe ve kadraj kontrolüdür; kullanıcıya yeniden aynı 80 cm sorularını sorma.

Gerekirse çalışan gözlem panelinden `calibrate capture --panel-url http://127.0.0.1:8080` aynı kameranın özgün PNG'lerini alır; yeni ve boş bir oturum klasörü kullan. Doğrudan kamera yakalamadan önce ise uygulama kapatılmalıdır. `solve --detector classic` seçeneği eklendi; her görüntünün RMS'i de ≤1 px olmalı. 35 test geçti.

Kullanıcının yaklaşık 40 cm beyanı mevcut elle tutulan kamera/desen düzeneği içindir; hassas doğrulama mesafesi sayılmaz. Çözümden sonra 2 m hedefin bilinen farklı lens mesafeleriyle sonuç karşılaştırılacak. Varsayımsal odak uzaklığıyla uçuş açılmayacak.

Yeni görüş alanı bulgusu: bu crop'ta fx/fy yaklaşık 1720/1719 px. 2 m kare için ideal, hizalı ve paysız düşey kadraj sınırı yaklaşık 4,77 m; kare 45° dönükse yaklaşık 6,75 m. İlk 3,5 m değeri mevcut akışta uçuşa uygun kabul edilmiyor. Gerçek hedefle görüş alanı ve görev yüksekliği birlikte kararlaştırılmalı; sırf kalibrasyon dosyası oluştu diye mevcut yükseklikle uçuşu açma. Kamera/crop değiştirilirse yeniden değerlendirme gerekir.

Kamera montajı şu kullanıcı beyanıyla ayarlı: 3 cm geride, yaklaşık ortada ve Pixhawk seviyesinden 5 cm aşağıda. Nihai kamera/montaj değişince kalibrasyon ve ofset tekrar ele alınır.

## Pixhawk okundu; fiziksel hazırlık bekliyor

Gözlem modunda gerçek USB yolu, ArduCopter 4.5.7, RC mod kanalı 9, TIMESYNC ve mevcut rota okundu. Kanıt `artifacts/pi/pixhawk-detail-20260905.json`. Mevcut görevde başlangıç TAKEOFF yok; home dahil sekiz maddede altı waypoint ve son LAND var. Görev 1'e veya mevcut rotaya dokunma. Görev 2 test rotasında başlangıç TAKEOFF, tarama waypoint'i ve açık koordinatlı son LAND gerekir.

Okuma sırasında STABILIZE/DISARM, RC_CHANNELS chancount=0 ve GPS fix=1/0 uydu görüldü. RC/GPS'nin test için hazırlanması gerekiyor; alıcının neden veri vermediği henüz belirlenmedi. FS_THR_ENABLE=1 mevcut sürümde RTL seçiyor ve yarışmanın RC kaybında kontrollü iniş koşuluyla uyuşmuyor. Uygulama gerçek araca parametre veya rota yüklemedi; bu bulguları düzeltilmiş sayma.

Kumandadan Loiter'a geçiş ve mevcut alıcının kayıp davranışı, gerçek araç üzerindeki kontrol testlerinin parçasıdır. Simülasyon motor/ESC ayarı, quad kararlılığı veya fiziksel RC doğrulaması yerine geçmez.

## Uçuşta ölçülecekler

- Merkezleme ve yükseklik tahmininin gerçek hedef üzerindeki hatası; 3,5 m başlangıç yüksekliğinin görüş alanına uygunluğu.
- Kararsızlık, hedef kaybı ve kumanda müdahalesinde alçalmanın kesilmesi; yalnız kararlı kilitte tek temsili olay.
- Temsili olaydan sonra arama irtifasına çıkış ve aynı açık/düz alandaki son LAND'e geçiş.
- Telefon erişim noktası + TL-WN722N v1 ile hedeflenen saha mesafesinde görüntü yaşı/kopma davranışı. 150 m henüz doğrulanmadı.

Quad'da fiziksel servo yok; yazılımın verdiği bırakma ibaresi temsili olaydır. Kalibrasyon ve gerçek araç denetimleri tamamlanana kadar `observe` kullanılır. Gözlem açma ve sonraki uçuş yapılandırma komutları `README.md` içinde bulunur.
