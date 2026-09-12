# Yeni sohbet promptu — ana görev, IMX708 ve Arducam EZBOX Swift

Aşağıdaki metni yeni Codex sohbetine tek parça halinde ver:

```text
Bu projede kaldığımız yerden devam et ve işi yalnız raporlamakla kalmayıp kodu/testleri tamamla.

Proje dizini:
/Users/kaan/Documents/ChatGPT/last şafak

ÖNCE OKU:
1. AGENTS.md
2. docs/HANDOFF.md dosyasının en üst güncel bölümü
3. TEKNIK_KONTROL.md
4. README.md
5. docs/competition/AKIS.md
6. docs/competition/TESTLER.md
7. docs/competition/EKSIKLER.md
8. config/README.md

Sonra git durumunu ve mevcut diffleri incele. Çalışma ağacı kirli; kullanıcıya ait hiçbir değişikliği silme, geri alma veya ezme. Bu prompttaki bilgilerle belgeler arasında çelişki varsa önce gerçek kodu, configleri ve testleri incele; yeni doğrulanan bilgiyi tarih belirterek devir belgelerine işle.

ANA HEDEF

Benim asıl hedefim hızlı görev değil, `strategy: "center"` kullanan ANA görevdir. Ana görev uçtan uca şu akışı yapmalı:

AUTO TAKEOFF ve Mission Planner'daki AUTO rotası → onaylı tarama alanına giriş → YOLO veya OpenCV ile hedef arama → kararlı adayda GUIDED ile durma → araç gerçekten durduktan sonra aynı kare/renk/bölgede YOLO ve OpenCV ortak doğrulaması → PnP/metrik konum doğrulaması → hedef üzerinde merkezleme → kontrollü alçalma → bırakma koşullarını doğrulama → yükü yalnız sanal olarak bırakılmış kaydetme → kesilen aynı AUTO waypoint'ine dönme → kalan AUTO görevi ve LAND.

Hızlı görev bugün saha testi için kullanıldı. Onu silme veya bozma; regresyon referansı olarak koru. Fakat ana görevi hızlı görevin `strategy: quick` davranışına çevirmeye çalışma. Ana görevde PnP, merkezleme ve alçalma korunacak.

ÇOK ÖNEMLİ GÜVENLİK VE YETKİ SINIRI

- Servolar şu anda fiziksel olarak bozuk/ertelenmiş durumda. Bütün yeni profillerde `actuator: "simulated"` kalacak.
- Kırmızı kanal 9, mavi kanal 10 bilgisi kayıt amaçlı korunabilir; `release_pwm: null` ve `bench_verified: false` kalacak.
- Servo PWM değeri uydurma, servo komutu gönderme, fiziksel çıkış açma veya gerçek bırakma yapma.
- Ben ayrıca açıkça istemeden gerçek araca ARM/DISARM, uçuş modu, görev/rota, FC parametresi, servo veya navigasyon komutu gönderme. Kod ve simülasyon testleri yapılabilir.
- Pilot müdahalesi her zaman üstün olmalı. Kumandadan kontrol alınmamalı; pilot override ve bayat telemetri/kamera fail-closed davranışı korunmalı ve test edilmeli.
- `flight` modu, aktüatör simulated olsa bile gerçek navigasyon komutu gönderebilir. Bu nedenle masa/kod kontrollerinde yanlışlıkla `flight` başlatma.

BUGÜNKÜ HIZLI SAHA TESTİNDEN KODDA KORUNACAK DERSLER

Bugünkü saha profilleri:
- config/hizli-saha-base-20260910.json
- config/hizli-saha-20260910.json

Bu dosyaları ve ilgili diffleri mutlaka incele. Hızlı saha temelinde doğru Pixhawk bağlantısı `/dev/ttyACM0` olarak canlı doğrulandı; cihaz Cube Orange, MAV_TYPE 13 ve ArduPilot 4.6.3 idi. Reboot veya donanım değişiminden sonra portu tekrar doğrulamadan sabit doğru kabul etme. Sessizce `/dev/ttyACM1` veya otomatik başka porta geçme.

İlk saha denemesinde önemli bir hazırlık hatası oldu: profile yanlışlıkla bütün `MissionPlan.fingerprint` değeri yazıldı. Yarışma kontrolcüsünün beklediği değer `safak_gorev2.competition.route.mission_digest()` sonucudur. Bu yüzden ilk uçuş fail-closed kaldı ve `Rota parmak izi onaylanan rotayla eşleşmiyor` dedi; hedefler görülmesine rağmen GUIDED/duruş gerçekleşmedi. Bu ayrımı kod, test ve belgelerde açıklaştır:

- Saha profiline yazılan `mission_fingerprint`, yalnız projenin `mission_digest()` sözleşmesiyle üretilmeli.
- HOME/seq0 dahil bütün Mission Planner planının başka bir genel fingerprint'ini kullanma.
- Digest, rota uygulamasının normalizasyonuyla hesaplanmalı; özellikle float32 irtifa normalizasyonunu elle taklit etmeye çalışma.
- Yanlış hash'te sistem fail-closed kalmalı.
- Mission Planner rotayı veya irtifayı değiştirirse eski hash yeniden kullanılmamalı; canlı görev yeniden okunup digest yeniden hesaplanmalı ve kullanıcı rotayı yeniden onaylamalı.

Bugün Mission Planner, WP2–WP8 irtifalarını 17 m'den 10 m'ye değiştirdi. Son onaylı 10 m rota digest'i:
`54b32d9b5dfb71d3cf3f0d7d829cac5e1aaed76d9f7c3e906aada5534a6747fe`

Son hızlı saha sortie kimliği:
`hizli-saha-20260910-03`

Bugünkü saha sözleşmesi yalnız aynı görev gerçekten yüklüyse yeniden kullanılabilir:
- search_start_seq: 2
- search_end_seq: 8
- entry gate:
  [[38.34134467136891, 38.42196479003001],
   [38.34131888861974, 38.42242174082246]]
- finish gate:
  [[38.34063098286252, 38.42220201562241],
   [38.340660533479344, 38.42174543582037]]
- flight polygon:
  [[38.34152294789823, 38.42202450136515],
   [38.340488467097515, 38.421692894472905],
   [38.34040085210177, 38.42213719863485],
   [38.341435332902485, 38.422468805527096]]

Bu koordinatları yarınki rota aynıymış gibi körlemesine ana profile gömme. Önce canlı Mission Planner görevi ile sıra, koordinat, komut ve irtifaların aynı olduğunu doğrula. Fark varsa yeni rotayı okuyup digest/gate/polygon sözleşmesini yeniden oluştur ve rota onayını benden al.

İlk yanlış-hash uçuş kaydı Pi'de:
`/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260910T145841Z-2528`
Kayıt complete, 3558 kare, 0 API hatasıydı. Model mavi için yaklaşık 0.526 ve 0.636 skorlar gördü, OpenCV doğrulamaları da vardı; fakat hash kontrolü rota güncellemesinden önce fail ettiği için giriş kapısı sayacı ilerlemedi. Doğru hash ile offline replay, WP2'de giriş ve WP4 civarında REQUEST_STOP üretti. Bu, ilk gerçek uçuşun durduğu anlamına gelmez; yalnız offline replay bulgusudur.

İkinci, düzeltilmiş saha kaydı Pi'de:
`/home/furkan/Desktop/safak-gorev2-quad/runtime/recordings/20260910T152021Z-4726`
Kayıt SIGTERM ile temiz kapandı, complete, 2493 kare, 0 API hatasıydı. Uçuş sırasında Wi-Fi aralıklı koptu; onboard uygulama/kayıt bundan bağımsızdı. Bu ikinci kaydın görev sonucunu analiz etmeden başarı ilan etme.

ORTAK GÖRÜNTÜ İŞLEME DAVRANIŞI

Mevcut güncel tasarımı koru ve ana göreve eksiksiz uygula:

- Kamera hedefi 50 FPS.
- YOLO/Hailo ve OpenCV renk+dörtgen işleme aynı görüntü akışında birlikte çalışır.
- Arama aşamasında YOLO VEYA kararlı OpenCV adayının bulunması duruş talebini başlatabilir.
- Duruştan sonra bırakma/merkezleme kanıtı için aynı hedefte, aynı renkte ve aynı kare/bölgede YOLO VE OpenCV birlikte zorunludur.
- Yalnız YOLO ile veya yalnız renk/OpenCV ile yük bırakma yok.
- Eski karelerin, farklı renklerin veya farklı nesnelerin kanıtlarını birleştirme.
- Hızlı görev PnP/merkezleme/alçalma yapmaz.
- Ana görev ortak YOLO+OpenCV kanıtına ek olarak PnP/metrik doğrulama yapar ve merkezleme boyunca ortak kanıtı sürdürür.
- MOSSE'yi geri getirme.

Korunacak başlangıç davranışları/eşikleri mevcut config ve koddan okunmalı. Mevcut özet:
- Arama: en az 3 bağımsız kare ve en az 0.10 s.
- Duruş kabulü: yatay hız en fazla 0.20 m/s, en az 0.30 s kararlılık.
- Duruş zaman aşımı: 5 s.
- Duruş sonrası doğrulama zaman aşımı: 3 s.
- Tekrar deneme gecikmesi: 5 s.
- Ana acquire/metrik doğrulama: en az 6 bağımsız kare ve en az 0.50 s.
- Ana center hold: 1.5 s.
- Ana release hold: 3 s.
- Ana hedef kamera yüksekliği: 9.0 m.
- minimum camera height: 8.5 m.
- minimum intercept relative altitude: 9.5 m.
- maksimum yatay merkezleme hızı: 0.4 m/s.
- maksimum alçalma: 0.15 m/s.
- YOLO confidence_min: 0.4.
- Aynı hedef eşleme IoU'su ve renk/dörtgen eşikleri için gerçek güncel kaynak kodu esas al.

ÖNEMLİ İRTİFA SINIRI

Bugünkü görev waypointleri 10 m. Ana görevde `minimum_intercept_relative_alt_m=9.5` olduğu için devralma sınırında yalnız yaklaşık 0.5 m marj var. `target_camera_height_m=9.0` ve `minimum_camera_height_m=8.5` ile ilişkiyi dikkatle incele. Bu değerleri sessizce değiştirme. Ana görevin 10 m rotada gerçekten merkezleme/alçalma durumuna geçip geçemediğini SITL ve birim testle kanıtla; sınır/tutarsızlık varsa net raporla ve güvenli, açık config düzeltmesi öner. Gerçek uçuşta deneme yapma.

İKİ KAMERA İÇİN AYRI VE KARIŞMAYAN PROFİLLER

Ana görevin iki ayrı kamera varyantını oluştur ve ayrı kaydet:

1. Raspberry Pi Camera Module 3 / IMX708
2. Arducam EZBOX Swift (yeni kamera)

Proje yapısına uygunsa şu adları kullan:
- config/ana-imx708-base.json
- config/ana-imx708-saha.json
- config/ana-arducam-ezbox-swift-base.json
- config/ana-arducam-ezbox-swift-saha.json

Gerekirse isimleri mevcut config loader'ın kurallarına uydur ama iki kamerayı dosya adında ve manifestte açıkça ayır. Ortak controller/vision/route/payload kodunu kopyalayıp iki ayrı kod tabanı oluşturma. Kamera backend ve kamera özel ayarları profilden seçilsin; davranış tek ortak ana kontrolcüde kalsın.

Her profil/manifest şu kimlikleri açıkça kaydetsin ve başlangıçta doğrulasın:
- beklenen kamera/backend türü,
- cihaz yolu veya kamera indeksi,
- çözünürlük ve gerçek piksel formatı,
- istenen FPS ve ölçülen FPS,
- crop/sensor mode bilgisi destekleniyorsa,
- lens/focus yöntemi destekleniyorsa,
- calibration dosyası ve hash'i,
- HEF dosyası ve SHA256,
- görev digest'i ve sortie kimliği,
- actuator'ın simulated olduğu.

Yanlış kamera takılıysa veya seçilen backend açılamıyorsa başka kameraya sessiz fallback yapma. Fail-closed ve anlaşılır hata üret. Aynı anda birden fazla `/dev/video*` düğümü varsa yalnız sıraya bakarak yanlış node seçme; kimlik/VID:PID/ürün adı ve gerçekten video-capture özelliğiyle eşle.

IMX708 VARYANTI

Mevcut bilinen ayarlar:
- 1280x720 çıktı
- 50 FPS hedefi
- sensor_output_size: [2304, 1296]
- tam crop: [0, 0, 4608, 2592] (backend/metadata içinde doğrula)
- manuel LensPosition: 0.0, yani istenen sonsuz odak
- camera_mount_yaw_deg: 180
- offset_body_m: [0.11, 0.0, 0.05] metre FRD
- lens yere bakıyor; görüntü üstü drone'un arka yönü
- kalibrasyon: config/camera.imx708-infinity-approx.json

Bu kalibrasyon kesin kabul edilmiş değildir. Sayısal matris, LensPosition yaklaşık 0.1062771082 ile çekilen 40 dama karesinden gelen eski adaydır; runtime LensPosition 0.0'dır. `focus_transfer_verified=false` ve `physical_distance_verified=false` korunmalı. Sonsuz odakta yeniden kalibre edilmiş, uzak netliği doğrulanmış veya metrik merkezleme kabul edilmiş gibi davranma. Ana görev PnP için bu matrisi kullanacaksa yaklaşık/deneysel niteliği log ve dokümana yazılsın; gerçek saha kabulü ayrıca gereklidir.

ARDUCAM EZBOX SWIFT VARYANTI

Bu yeni kameranın tam sensörü, çözünürlüğü, lensi, görüş açısı, otomatik/manüel odak desteği, crop davranışı, USB VID:PID'si ve Linux backend'i henüz bu promptta doğrulanmış değildir. IMX708 ayarlarını buna kopyalama.

Pi ve kamera erişilebilir olduğunda salt okunur/donanımı hareket ettirmeyen şekilde şunları gerçek cihazdan belirle:
- `v4l2-ctl --list-devices`, `--all`, desteklenen format/çözünürlük/FPS listesi,
- `/dev/v4l/by-id` ve `/dev/v4l/by-path` sabit kimlikleri,
- USB VID:PID/ürün adı,
- V4L2, GStreamer, OpenCV veya başka hangi backend'in kararlı çalıştığı,
- gerçek teslim edilen çözünürlük, pixel format, FPS, zaman damgası ilerlemesi ve frame drop,
- focus/exposure kontrollerinin gerçekten desteklenip desteklenmediği.

Ürün adından sensör modeli veya odak kontrolü uydurma. Gerekirse güncel resmî Arducam ürün belgesine bak ama fiziksel cihaz enumerasyonunu esas al.

Arducam için:
- IMX708 `LensPosition`, Picamera2 sensor mode veya ScalerCrop alanlarını destekliyormuş gibi yazma.
- IMX708 iç kamera matrisi/distorsiyonunu asla kullanma.
- Ayrı Arducam kalibrasyon dosyası ve ayrı montaj kabulü oluştur.
- Kalibrasyon henüz yoksa `calibration_file: null`/doğrulanmamış durum açık olsun ve ANA merkezleme/PnP aşaması fail-closed kalsın; yalnız görüntü akışı, kayıt ve YOLO/OpenCV gözlem testleri yapılabilir.
- Kamera net değilse önce kontrollü masa/dış ortam görüntüsüyle odak, pozlama, hareket bulanıklığı ve gerçek hedef görünürlüğünü değerlendir. Yazılımsal keskinleştirmeyi fiziksel netliğin yerine kabul etme.
- Kamera montajı fiziksel olarak IMX708 ile aynı değilse 180° ve [0.11, 0.0, 0.05] değerlerini körlemesine kullanma; yeniden ölç/benim onayımı iste.

YOLO VE OPENCV AYNI ANDA ÇALIŞMASI

İkisini aynı anda çalıştırmak tasarım gereğidir ve IMX708'de gerçek kısa testte yaklaşık 50 FPS çalışmıştır; fakat yeni Arducam için bunu varsayma. Her kamera varyantında en az 20–60 saniyelik kamera + Hailo YOLO + OpenCV + JPEG/telemetri probe yap ve ölç:
- gerçek işlenmiş FPS,
- capture→result gecikmesi medyan/p95,
- OpenCV süresi,
- Hailo çıkarım süresi,
- CPU/sıcaklık/throttling,
- düşen/bayat kare ve hata sayısı.

İş yükü 50 FPS'i sürdüremiyorsa hedef doğrulama güvenliğini düşürmeden darboğazı raporla. OpenCV'nin en fazla 640 px genişlikte arayıp adayları tam çözünürlükte inceleyen mevcut tasarımını koru. Paralellik veya frame-skipping yapılacaksa eski karelerin ortak kanıt sayılmamasını test et.

KAYIT

Uçuşta aktif kayıt alınması gerekiyor; daha sonra analiz edeceğiz. Mevcut recorder ve panel kodunu incele:
- panel/HUD kaydı yaklaşık 8 FPS olabilir; bu, kamera/çıkarımın 50 FPS olduğu anlamına gelmez,
- telemetri yaklaşık 5 Hz olabilir,
- kayıt manifestosu doğru kamera profilini, kamera kimliğini, HEF hash'ini, calibration hash'ini, mission digest'i, sortie kimliğini ve yazılım commit/diff durumunu yazmalı,
- `complete/recording`, kare sayısı, segment eşlemesi ve hata sayısı güvenilir olmalı,
- SIGTERM ile temiz kapanış ve bozuk/yarım segment davranışı test edilmeli,
- Wi-Fi kopsa bile onboard kayıt devam etmeli,
- iki kamera varyantının kayıt dizinleri/manifestleri karışmamalı.

Eğer gerçek 50 FPS ham/işlenmiş uçuş videosu ayrıca isteniyorsa bunun panelin 8 FPS kaydından farklı olduğunu açıkça belirt; depolama bant genişliği, segmentleme ve zaman damgası doğruluğunu ölçmeden “50 FPS kayıt var” deme.

YAPILACAK KOD İŞİ

1. Mevcut `ana`, `hizli`, saha profilleri, config loader, camera backend, runtime, controller, route digest ve recorder kodunu incele.
2. Bugünkü hızlı saha düzeltmelerinden ortak ve ana göreve ait olanları ortak altyapıya güvenle taşı. Hızlı göreve özel kısa doğrulama/merkezlemesiz davranışı ana göreve taşımama.
3. Ana görev için IMX708 ve Arducam EZBOX Swift profillerini ayrı oluştur.
4. Kamera kimliği/backend seçimini config ve manifestte açık, doğrulanabilir ve fail-closed yap.
5. `MissionPlan.fingerprint` ile `mission_digest()` karışıklığını önleyen kod doğrulaması, CLI mesajı ve regresyon testi ekle.
6. Ana YOLO+OpenCV+PnP ortak kanıt, merkezleme, alçalma, aynı waypoint'e AUTO dönüş ve simulated bırakma akışını gözden geçir; açık hata varsa düzelt.
7. Pilot override, mod sahipliği, bayat veri, bağlantı kopması, duramama, doğrulama timeout'u ve yanlış kamera/kalibrasyon korumalarını test et.
8. Recorder'ın iki kamera profilini doğru kaydettiğini ve temiz kapandığını test et.
9. `--check` çıktısını kamera/kalibrasyon/rota/servo-simülasyon durumunu açık gösterecek şekilde doğrula.
10. README, HANDOFF, AKIS, TESTLER ve EKSIKLER belgelerini güncelle. Gerçek test ile simülasyonu kesin ayır.

ZORUNLU TESTLER

- Tüm yerel pytest paketi.
- İlgili config/schema testleri.
- Yanlış genel MissionPlan fingerprint'inin reddedildiği test.
- Doğru `mission_digest()` değerinin kabul edildiği test.
- Mission Planner irtifa/waypoint değişince eski digest'in reddedildiği test.
- IMX708 ve Arducam profilinin birbirinin calibration/backend ayarını kullanmadığı test.
- Yanlış/eksik kamera kimliğinde silent fallback olmadığı test.
- Arducam calibration yokken PnP/merkezleme/bırakmanın fail-closed kaldığı test.
- Search aşamasında YOLO veya OpenCV; stop sonrası YOLO ve OpenCV zorunluluğu.
- Ana görevde en az 6 bağımsız taze ortak+metrik kare ve 0.5 s doğrulama.
- Eski/bayat/farklı renk/farklı bölge kanıtlarının birleşmediği test.
- 10 m rota ile 9.5 m intercept sınırının center state'e etkisi.
- Pilot LOITER/manuel müdahalesinin kontrolü kalıcı olarak pilota bırakması; aynı havadaki süreçte tekrar devralmama.
- Simulated actuator'ın hiçbir MAVLink servo/PWM komutu üretmediği test.
- Simulated bırakmanın olay defterine doğru renk/yük/sortie ile yalnız bir kere yazıldığı test.
- Kesilen aynı AUTO waypoint'ine dönüş ve kalan LAND rotasının korunması.
- Kayıt manifestosu, Wi-Fi'den bağımsız kayıt ve SIGTERM temiz kapanış testleri.
- ArduCopter 4.6.3 hex SITL'de ana tam görev, hedef yok, yanlış hedef, doğrulama kaybı, pilot override ve 10 m sınır senaryoları.

Gerçek kamera/Pi mevcut değilse donanım doğrulamasını yapılmış gibi yazma. Donanımsız yapılabilecek kod, test, fixture ve fail-closed profilleri tamamla; yalnız gerçek cihaz gerektiren maddeleri kesin komut ve kabul ölçütleriyle açık bırak.

KABUL ÖLÇÜTLERİ

İşi ancak şu durumda tamamlanmış say:
- Ana görev ortak kontrolcüyle center/PnP/alçalma akışını koruyor.
- Hızlı görev bozulmamış ve regresyon testleri geçiyor.
- IMX708 ile Arducam profilleri gerçekten ayrı ve çapraz kullanım fail-closed.
- IMX708'in yaklaşık kalibrasyon sınırı dürüstçe korunuyor.
- Arducam calibration yoksa gerçek merkezleme/bırakma “hazır” denmiyor.
- Servo tamamen simulated; PWM/gerçek servo komutu yok.
- Rota hash'i yalnız `mission_digest()` ile doğrulanıyor.
- Pilot kontrolü her koşulda üstün.
- Kayıt doğru profil/kimlik/hashlerle analiz edilebilir.
- Tüm test sonuçları sayıları ve atlama nedenleriyle raporlanmış.
- Gerçek donanım, kısa probe, SITL ve sentetik test kanıtları birbirine karıştırılmamış.

ÇALIŞMA ŞEKLİ

Önce kısa bir mevcut durum ve uygulanacak dosya planı çıkar; sonra benden tekrar aynı bilgileri istemeden kodu uygula. Güvenli yerel değişiklikleri ve testleri kendin tamamla. Yeni kameranın fiziksel kimliği/kalibrasyonu veya yeni saha rotası gibi gerçekten benden/donanımdan veri gerektiren noktada uydurma yapma; fail-closed bırakıp tam olarak hangi ölçüm/onayın gerektiğini söyle.

Yanıtların Türkçe olsun. Son raporda:
- değiştirilen dosyaları,
- iki kamera profilinin farklarını,
- ana ve hızlı akış farkını,
- test sonuçlarını,
- gerçek uçuş öncesi kalan fiziksel kabulleri,
- hiçbir servo/PWM/ARM/mod/rota komutu gönderilmediğini
kısa ama teknik olarak net biçimde yaz.
```

