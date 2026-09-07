# ŞAFAK UAV — proje ve yeni oturuma devir

## Güncel başlangıç — 7 Eylül 2026

**Yeni hesapta/oturumda önce [AGENTS.md](AGENTS.md) ve [kısa devir notunu](docs/HANDOFF.md) okuyun.** Aynı proje klasörünün tamamını koruyun; bu iki metin kod/model/kanıtların yerine geçmez.

- **IMX219 tamamen kırık; tek kamera seçeneği IMX708** (kullanıcının son beyanı). Eski IMX219'a dönüş notları güncel değildir.
- IMX708 için5Eylül tarihli [aday kalibrasyon](config/camera.imx708-candidate.json) var; mevcut kamera/odak/montaja uygunluğu ve görev mesafesinde doğruluğu bilinmiyor. Kalibrasyon tamamlanmış kabul edilmez. Yeni `competition-base.json` hâlâ IMX219'a işaret ediyor; IMX708 merkezlemesi için hazır değil.
- Eski yalnız mavi merkezleme uygulaması korundu. Ayrı iki renkli merkezleme ve merkezlemeden bırakma seçenekleri `safak_gorev2/competition/` altında: [kullanım](docs/competition/KULLANIM.md), [testler](docs/competition/TESTLER.md).
- **119test ve5ArduCopter hexSITL senaryosu geçti.** Gazebo yok; kamera/AI kutuları sentetik. Gerçek görüntü algılama, mekanizma veya hex uçuş kabulü değildir.
- Yarışma hexacopter; kırmızı yük AUX1(9), mavi yük AUX2(10).180°başlangıç/90°bırakma beyan edildi; gerçek PWM değerleri eksik. Hex kamera ofseti ve saha rota/kapıları da bilinmiyor. Pi'ye yeni paket dağıtılmadı, canlı durum bilinmiyor.

Yeni göreve yazılabilecek mesaj:

> AGENTS.md, README.md ve docs/HANDOFF.md dosyalarını oku. IMX219 kırık, yalnız IMX708 kullanılabilir. Eski yalnız mavi merkezleme koduna dokunma. Mevcut IMX708 durumunu ve aday kalibrasyonun uyumunu değerlendir. Türkçe ve kısa yanıt ver.

## Aşağıdaki bölümler: eski quad test uygulamasının tarihli kılavuzu

Aşağıdaki “yalnız mavi”, “servo komutu yok” ve eski test sayıları **yalnız eski quad uygulamasını** anlatır. Yeni iki renkli paketin kapsamı ve güncel donanım için yukarıdaki bağlantıları esas alın.


Bu uygulama F450/quad üzerinde **mavi 2 × 2 m hedefi** Hailo ile bulmak, GUIDED ile merkezlenip alçalmak, kararlı kilitten sonra **kırmızı yük için temsili bırakma** kaydetmek ve mevcut AUTO rotasının son LAND noktasına gitmek için yazılmıştır. Görev 1 kodu veya waypoint görevi içermez. Motor/servo PWM, ARM/DISARM, mission upload/clear ve parametre yazma komutu göndermez.

Gerçek donanım doğrulaması tamamlanmadan uçuşa hazır olduğu kabul edilmez. Güncel kanıt ve açık işler [doğrulama kaydında](docs/VALIDATION.md) tutulur. 35 birim testi ve dört ArduCopter 4.6.3 SITL senaryosu geçti; Pi'de gerçek kamera/Hailo ve ArduCopter 4.5.7 USB telemetrisi gözlem modunda çalıştı. Üç kalibrasyon serisinde toplam 115 özgün görüntü kaydedildi. İncelenip seçilen 55 kareyle RMS 0,471 px aday kalibrasyon üretildi. 60 cm ekran referansında 60,605 cm, sabit 80 cm referansında 80,082 cm hesaplandı; gerçek 2 m hedef ve operasyon mesafesi kontrolü bekliyor. Aday uçuş ayarına uygulanmadı. Fiziksel oturumda kalan işler [burada](docs/NEXT_SESSION.md) özetlenmiştir.

## Akış

1. Pi'de program uçuş öncesinde başlatılır. Programın DISARM durumunu görmesi gerekir; havada yeniden başlatılan program kontrolü devralmaz.
2. Kamera/Hailo çıkarımı sürekli çalışır. Pilot ARM ve AUTO seçimini yapar. Başlangıç TAKEOFF devam ederken tespit gösterilir; program kalkışı GUIDED ile kesmez.
3. AUTO waypoint uçuşunda mavi hedef bağımsız karelerde doğrulanır. Hedef yoksa AUTO görevine müdahale edilmez.
4. GUIDED modunun gerçekten geldiği doğrulanır. Kamera ofseti ve çekim anındaki Pixhawk duruş/konumu kullanılarak quad merkezinin hedefe yatay hatası hesaplanır.
5. Önce 1,5 s kararlı merkezleme, ardından yavaş alçalma uygulanır. Bırakma yüksekliğinde 3 s kesintisiz kararlı kilit gerekir. Kaybolan, eski, tekrarlanan veya geometrisi belirsiz kare süre kazandırmaz.
6. Yalnız bir **SIMULATED_RELEASE** olayı diske yazılır. Panel ve görüntü üzerinde temsili bırakma görünür. Fiziksel bir servo çıkışı yoktur.
7. Araç hedefe yönelirken kaydedilen arama irtifasına çıkar. Son LAND koordinatına bu irtifada gider. `MISSION_CURRENT` ile son LAND sırası doğrulanır, sonra AUTO'ya geçilir ve inişi ArduCopter yürütür.
8. Kumandadan Loiter veya başka moda geçiş kontrolü pilota verir. Aynı çalıştırmada yeniden otomatik devralma yapılmaz. Otomatik yeniden başlatma servisi kurulmaz.

Bu testte kullanıcının istediği gibi kalkıştan itibaren tespit yapılır. Tam yarışma Görev 2'sinin Direk 2 sonrası tespit koşulunu gerçekleştiren bir yarışma sürümü değildir.

## Dosyalar

| Dosya | İşlev |
|---|---|
| `detection.py` | Kullanıcının verdiği Hailo referansı; değiştirilmedi |
| `safak_v2_hailo_model/` | Kullanıcının yüklediği model paketi; değiştirilmedi |
| `safak_gorev2/hailo_backend.py` | Aynı `GStreamerDetectionApp` ailesi, gerçek `hailonet` çıkarımı |
| `safak_gorev2/geometry.py` | İkincil OpenCV kontrolü, kalibre kamera ile kareden metrik poz |
| `safak_gorev2/controller.py` | Merkezleme, alçalma, kilit ve son LAND'e geçiş kararları |
| `safak_gorev2/mavlink_io.py` | USB MAVLink, zaman eşleme, telemetri, görev okuma, komut süresi denetimi |
| `safak_gorev2/web.py` | Pi'de Flask, laptop tarayıcısında salt okunur panel |
| `config/quad.json` | Ölçülmemiş alanları `null` bırakan başlangıç ayarları |
| `safak_gorev2/calibrate.py` | Aynı kamera akışında kalibrasyon görüntüsü alma ve çözüm |
| `safak_gorev2/doctor.py` | Mevcut Pi/Hailo ortamını değiştirmeden inceleme |

## Başlangıç değerleri ve ölçülecekler

Sayısal kontrol değerleri **mühendislik başlangıç önerileridir**, ölçülmüş uçuş performansı değildir. Kullanıcının 2 m hedefi yaklaşık 2,5–2,6 m lens mesafesinde kadraja sığdırma gözlemi FOV veya kalibrasyon yerine kullanılmadı.

| Ayar | İlk değer / anlam |
|---|---|
| Mavi hedef AI kabul eşiği | Quad test ayarında geçici 0,50; önceki 0,65. Gerçek saha pozitif/negatif örnek doğrulaması bekliyor |
| Görsel bırakma yüksekliği | Lensin hedef düzlemi üzerindeki tahmini düşey yüksekliği 3,5 m |
| Yükseklik toleransı | ±0,25 m; alt sınır 2,9 m |
| Yatay merkez toleransı | 0,20 m; 0,30 m üstünde alçalma kesilir |
| Merkez kilidi / bırakma kilidi | 1,5 s / 3 s kesintisiz |
| Yatay hız / alçalma üst sınırı | 0,40 m/s / 0,15 m/s |
| Bırakmada hız / eğim | Yatay ≤0,20 m/s, düşey ≤0,12 m/s, eğim ≤8° |
| Görüntü yaşı | En fazla 0,30 s; kilit kareleri arası en fazla 0,25 s |
| Kamera ofseti | Kullanıcı: 3 cm geride, sağ/sol yaklaşık ortada, Pixhawk seviyesinden 5 cm aşağıda; FRD `[-0.03, 0, 0.05]` m |
| Son LAND geçiş koridoru | Kullanıcı aynı düz zeminde açık test alanı bildirdi; ayar bu beyana göre `true` |

Lidar/sonar yoktur. Metrik mesafe bilinen hedef ölçüsü, dört görünür köşe ve kamera kalibrasyonundan tahmin edilir. Hedefin kutusunun ortası tek başına mesafe ölçümü sayılmaz. Lensin arka taraftaki ofseti, quad merkezine göre hata hesabına eklenir. Home'a göre irtifa panelde ayrı gösterilir.

5 Eylül 2026'da kullanıcı eşik değerinin şimdilik düşürülmesini istedi; `config/quad.json` içinde `camera.confidence_min=0.50` seçildi. Kullanıcı, eğitim brandalarının DJI ile beton zeminde farklı irtifa/açılardan çekildiğini ve test sahasının beyaz taşlı olduğunu bildirdi. Bu koşullar ile düşük laptop skoru arasındaki neden ilişkisi ölçülmedi. Geçici değer saha başarımı garantisi değildir; OpenCV geometri, bağımsız kare, tazelik, merkezleme ve süreli kilit koşulları ayrıca uygulanır. Genel sınıf varsayılanı 0,65 kalır; bu değişiklik quad test yapılandırmasına özeldir.

İlk kalibrasyon adayı mevcut 1280 × 720 / ScalerCrop `[680,692,1920,1080]` akışının dar görüşünü gösterdi: eksenlerle hizalı 2 m kare için ideal pinhole hesabında, pay olmadan yaklaşık 4,77 m lens yüksekliği gerekiyor. Hedefin görüntüde dönmesi veya aracın eğilmesi gereken yüksekliği artırabilir. Yukarıdaki 3,5 m ilk önerisi bu akış için uçuşa uygun kabul edilmiyor; gerçek hedef üzerinde görüş alanı ve yükseklik birlikte doğrulanmalı. Kamera/crop bu oturumda değiştirilmedi.

## Pi'de mevcut Hailo ortamıyla çalıştırma

Uygulama Pi'de `/home/furkan/Desktop/safak-gorev2-quad` klasörüne kuruldu. Kullanıcının `/home/furkan/Desktop/hailoenvtest/hailo-rpi5-examples/setup_env.sh` betiği SSH üzerinden doğrulandı ve kullanıldı. Betik, mevcut Documents altındaki Hailo sanal ortamını etkinleştiriyor; bu ortam değiştirilmedi. Eksik `waitress` yalnız yeni uygulamanın `runtime/python/` klasörüne eklendi.

Yeni proje Pi'de ayrı klasörde bulunmalıdır. Launcher, verdiğiniz ortam betiğini kendi dizininde `source` eder; sonra bu proje dizinine döner:

```bash
cd /home/furkan/Desktop/safak-gorev2-quad
bash scripts/run_pi.sh /home/furkan/Desktop/hailoenvtest/hailo-rpi5-examples/setup_env.sh --mode observe
```

Ortam zaten etkinse:

```bash
python -m safak_gorev2.doctor --config config/quad.json
python -m safak_gorev2.main --mode observe --config config/quad.json
```

`observe` varsayılandır. Gerçek Hailo kamerasını ve telemetriyi gösterir, uçuş hareketi komutu göndermez. Hailo importu/HEF/çıkarım hatasında hata gösterir; `.pt`, ONNX veya CPU dedektörüne geçmez. AI dışındaki OpenCV doğrulama, JPEG kodlama, Flask ve görev mantığı doğal olarak Pi CPU'sunda çalışır.

Gerekli Python modülleri: `flask`, `waitress`, `pymavlink`, mevcut `numpy`, `cv2`, `picamera2`, `gi`, `hailo` ve kullanıcının dosyasındaki `hailo_apps.hailo_app_python...` paketi. GStreamer/Hailo sürücüleri `pip install` ile yeniden kurulmaz. `doctor` hangi bağımlılığın eksik olduğunu raporlar.

## Kalibrasyon

Kamera montajı ve görüntü ayarları sabitken, düz satranç tahtası kullanılır. **İç köşe** sayısı ve fiziksel bir karenin cetvelle ölçülen kenarı gerekir. Tahtayı farklı mesafe/açılarda ve kadrajın köşe/kenarlarında gösterin. Drone sağlam bir destek üzerinde durabilir; elde uzun süre tutulması gerekmez. Düz ekranda gösterilen desende yakınlaştırma sabit tutulmalı, karelerin yatay/düşey boyutu ölçülmeli ve yansıma engellenmelidir.

Gözlem paneli açıkken aynı kameranın özgün 1280 × 720 PNG kareleri alınabilir. Bu yöntem ikinci kamera bağlantısı açmaz; eski/yinelenen kareyi ve değişen kamera/crop bilgisini reddeder:

```bash
python -m safak_gorev2.calibrate capture --panel-url http://127.0.0.1:8080 \
  --folder runtime/calibration-imx219 --count 40 --interval 0.5
```

Doğrudan kamera yakalama seçeneği için önce normal uygulama kapatılmalıdır:

```bash
python -m safak_gorev2.calibrate capture --folder runtime/calibration-imx219
python -m safak_gorev2.calibrate solve --folder runtime/calibration-imx219 \
  --cols 9 --rows 6 --square-mm 25 --output config/camera.local.json
```

Buradaki `9`, `6`, `25` **örnek tahta değerleridir**; kendi tahtanızın iç köşe sayıları ve ölçülmüş kenarıyla değiştirin. En az 18 uygun farklı görüntü ve RMS ≤1 px gerekir. Çözümün düşük RMS vermesi mesafenin sahada doğru ölçüldüğünü tek başına kanıtlamaz; 2 m hedef üzerinde cetvelle bilinen farklı lens mesafeleriyle ayrıca karşılaştırılır. Kamera modeli, çözünürlük veya ScalerCrop değişirse uygulama eski kalibrasyonu kullanmayı reddeder.

Panelden alınan her PNG yanında aynı kareye ait Hailo sınıf/skor/kutu, kare/oturum kimliği ve yaşını içeren JSON kaydı tutulur. Oturum değişimi veya geri giden kare kimliği yakalamayı durdurur.

`--detector classic` seçeneği klasik OpenCV köşe bulma ve subpiksel iyileştirme kullanır; varsayılan `sb` yöntemidir. Toplam RMS yanında her görüntünün RMS hatası da en fazla 1 px olmalıdır. Araç hatalı kareleri sessizce atmaz: başarısız kareler görsel olarak incelenmeli, seçim kaydı tutulmalı ve seçilen özgün görüntülerle yeniden çözülmelidir. Her iki yöntemin köşe eşleşmeleri de gözden geçirilmelidir.

## Uçuş yapılandırması

`config/quad.json` dosyasını `config/flight.local.json` olarak kopyalayın. Şu alanları gerçek bilgilerle tamamlayın:

- `camera.calibration_file`: `config/camera.local.json`.
- `camera.offset_body_m`: uçuş referans merkezinden lense `[ileri, sağ, aşağı]`, metre. Kullanıcının montaj beyanı `[-0.03, 0, 0.05]` olarak girildi; sağ/sol sıfırı yaklaşık merkezde olmanın nominal karşılığıdır. Montaj değişirse güncellenir.
- `link.device`: Pi'deki Pixhawk'ın gerçek `/dev/serial/by-id/...` USB yolu. Sistem yalnız bir böyle seri cihaz varsa otomatik seçebilir; birden fazla cihazı tahmin etmez.
- `mission.direct_land_corridor_checked`: mevcut açık/düz test alanı için kullanıcı beyanıyla `true`; saha değişirse yeniden değerlendirilir.

```bash
bash scripts/run_pi.sh /home/furkan/Desktop/hailoenvtest/hailo-rpi5-examples/setup_env.sh \
  --mode flight --config config/flight.local.json
```

Firmware kimliği, `MIS_RESTART`, `GUID_TIMEOUT`, RC mod kanalı ve görev listesi otopilottan okunur. `MIS_RESTART=0`, pozitif ve ≤3 s `GUID_TIMEOUT`, etkin RC kaybı failsafe'i, ilk TAKEOFF ve son açık koordinatlı LAND gereklidir. Uygulama bu parametreleri değiştirmez. RC kaybı davranışının fiziksel/yarışma uygunluğu ayrıca mevcut araç üzerinde doğrulanır; programın Loiter'a geçmesi RC kaybı failsafe'inin yerine geçmez.

Programın iç kontrol döngüsü durursa bağlantı işçisi kısa ömürlü hız komutunu sürdürmez. Pi bütünüyle kapanır veya USB koparsa otopilotun gerçek GUIDED/GCS/RC failsafe ayarları devreye girer; bunların yalnızca yazılım dosyasından çalıştığı iddia edilmez.

## Yer istasyonu paneli

Flask **Pi üzerinde** çalışır. Laptop aynı telefon erişim noktasına bağlanır ve mevcut ağda [Pi paneli](http://172.20.10.4:8080/) açılır; DHCP adresi değişirse yeni Pi IP'si kullanılır. Panel dış internet/CDN gerektirmez, komut düğmesi veya uçuş yazma API'si içermez. Uygulama terminalden başlatılır.

Video JPEG olarak bir kez kodlanır; istemciler aynı son kareyi alır. Tarayıcı eski kareleri sıraya dizmez. Ağ kesildiğinde panel açıkça bayat görüntü/telemetri gösterir; panelin kopması Pi üzerindeki görevi kilitlemez. Varsayılan yayın 960 px genişlik, 8 FPS ve JPEG kalite 65'tir. 150 m telefon hotspot bağlantısı veya TL-WN722N v1 menzili bu masaüstü testleriyle doğrulanmış değildir; saha ölçümü gerekir. Paneldeki kare yaşı, ağ ve görüntü gecikmesini değerlendirmeye yardımcı olur.

## Yerel sentetik demo ve testler

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[desktop,test]'
python -m safak_gorev2.main --mode demo
python -m pytest -q
```

Demo yalnız `127.0.0.1:8080` üzerinde açılır; sentetik kamera ve telemetri kullanır. Sayısal demo donanımı gerçek F450 ayarı değildir. `runtime/demo/` kayıtları gerçek uçuş kayıtlarından ayrıdır.

Olaylar `runtime/events.sqlite3`, zaman eşlenmiş ölçümler `runtime/telemetry-*.jsonl` içine yazılır. Temsili olay, uçuş/çalıştırma kimliği başına veritabanındaki benzersiz kısıtla korunur. Kod mimarisi ve birincil teknik kaynaklar [mimari notunda](docs/ARCHITECTURE.md) açıklanır.

Gerçek ArduCopter simülasyon deneyi, yerelde derlenmiş Copter-4.6.3 kaynak klasörüyle çalıştırılır:

```bash
python tests/run_sitl.py --ardupilot /tmp/safak-ardupilot-4.6.3 --scenario complete
```

Diğer senaryolar `pilot`, `lost-target`, `control-stall` değerleridir. Bu araç yalnız kendi yerel SITL sürecine komut verir. Demo ile SITL ayrı doğrulama katmanlarıdır; ikisinde de görüntü sentetiktir.

## Kayıtlı görüntüyle tespit hattı incelemesi

Kamera/FC/panel açmadan `python -m safak_gorev2.replay recorded|hailo` kullanılabilir.
81 karelik gerçek Hailo karşılaştırması, kaynak doğrulama, komutlar ve sınırlar:
[docs/DETECTION_REPLAY.md](docs/DETECTION_REPLAY.md). Eşik 0,50 kalır; yeniden eğitim ayrı aşamadır.

## Manuel kalkışlı quad saha testi

Kullanıcının son test tercihi manuel kalkıştan sonra kumandadan AUTO'ya geçmektir. `mission.takeoff_mode="manual"` ile TAKEOFF içermeyen, waypoint ile başlayan ve açık koordinatlı LAND ile biten rota kabul edilir. Varsayılan `auto` hâlâ TAKEOFF gerektirir. Program yerde DISARM durumunu görmeli; Loiter'da, yerde, minimum devralma irtifasının altında veya havada yeni başlatıldığında devralmaz.

`config/observe-field.json` mevcut aday matrisle yalnız saha gözleminde kullanılır. `config/flight.field-candidate.json` henüz fiziksel kadraj/mesafe teyidi almamış yerel adaydır; uçuşa hazır ilanı değildir. Güncel saha adımı ve açık işler `docs/NEXT_SESSION.md` başındadır.

Manuel kalkış simülasyonu (yalnız yerel SITL, sentetik görüntü):

```bash
python tests/run_sitl.py --ardupilot /tmp/safak-ardupilot-4.6.3 --takeoff-mode manual --scenario complete --output artifacts/sitl/manual-takeoff-yeni
```

## Pi'de bağımsız uçuş videosu/log kaydı

Mevcut Hailo Python ortamında, proje kökünde:

```bash
python -m safak_gorev2.record --root runtime/recordings
```

Etiketli kamera ve telemetri HUD'u 8 FPS/30 saniyelik MKV parçaları; yaklaşık 5 Hz API logu, video kare/zaman eşlemesi, yazılım/config kopyası ve model hash'i kaydedilir. Kaydedici kamera veya MAVLink bağlantısı açmaz. `runtime/recordings/active.json` güncel PID/durum/klasörü gösterir; aynı kökte ikinci kaydedici reddedilir. SIGTERM temiz kapatır. SSH'den bağımsız başlatılmalıdır; Pi açılış servisi yoktur. Video tarayıcının birebir ekran kopyası veya bütün kamera karelerinin kaydı değildir.
