# ŞAFAK UAV — Proje bağlamı ve çalışma kuralları

## DEVİR — 12 Eylül kaybedilen uçuş / zorunlu son-şans kapısı

- Kaybedilen sortie `20260912T114011Z-ana-imx708` kaydı 347 s boyunca
  `WAIT_AUTO`: profilde `9280b849…abd90`, FC'de LAND17 yaklaşık 14,6 m
  taşınmış `c91d1230…e2860a4` rotası vardı. Hiçbir action/PWM/servo
  üretilmedi; ledger boş. 12 mavi + 9 kırmızı aday kameranın çalıştığını
  kanıtlıyor. Kanıt `artifacts/failed-flight-20260912/flight.jsonl`.
- Kırmızı açılış düşüşü görevden önce/no-signal: kumanda kapalıyken
  RC11 ve AUX3 0 us. `FUNCTION61` ancak verici açıkken yaklaşık 1495 us
  verir. Kalıcı garanti donanımsaldır (gecikmeli besleme/anahtar/pim).
  Tornavidayla çevrilen servonun dişli ve horn hizası fiziksel onay ister.
- Flight modu artık rota iki kez aynı okunmadan, digest+Seq kapsamı,
  DISARM/LANDED/tüm preflight, süreli servo 1500±25 us/2 s ve taze gerçek
  OpenCV kare doğrulanmadan açılmaz. Hata `UÇUŞ BAŞLATILMADI` + exit 2;
  tam başarı satırı görülmeden ARM/AUTO yapılmaz. Rota yenilemesi iki eş
  okumadan sonra durur; kendi okumasında geçici görev durumu oluşturmaz.
- Canlı rota/yetkili Pi profili: TAKEOFF1=15 m, WP2–16=15 m, LAND17=1 m,
  tarama3–16, 3,5 m/s, digest `c91d1230de8caeb1ff826a2f941d2c071cc555999379fc6914b9772d9e2860a4`.
  Pi `furkan@172.20.10.6`, görev kapalı. Yerel 421/5, Pi 379 test; tam
  ArduCopter 4.6.3 SITL iki yük+LAND+DONE 119,01 s:
  `artifacts/competition-sitl/20260912T171636-center-complete`.
  Pi yedeği `runtime/before-final-gate-20260912/`; dosya hashleri eş.
- Son canlı başlatma kumanda kapalı/0 us nedeniyle doğru reddedildi.
  Kumanda açık, LOITER, DISARM, yükler takılı değilken 1495–1500 us ve tam
  başarı satırı hâlâ bekleniyor. Kumandasız kamera probe'u reboot sonrası
  geçti: 20 s/1021 kare/50,03 FPS/stale0/hata0; kanıt
  `artifacts/final-preflight-20260912/`. Son JPEG yakın desenli kumaş/yüzeyle
  dolu; saha öncesi lens altı ve kadraj merkezi fiziksel olarak açık
  doğrulanmalı. Servo/ARM/mod/FC parametre komutu
  verilmedi. Profilin yetkili kopyası Pi'dir; Mac config'i Pi'ye rsync
  edilmez. `route_digest` ile görev aynı anda seri portu açmaz.

## DEVİR — 12 Eylül yeni rota / WP2 hızlı transit / 3,5 m/s tarama

- Pi `furkan@192.168.137.145`, proje
  `/home/furkan/Desktop/safak-gorev2-quad`. Görev/kayıt kapalı; FC salt
  okunur kontrolde DISARM/LANDED. `WPNAV_SPEED=1000`, `WPNAV_ACCEL=250`,
  `SERVO9_FUNCTION=58`, `SERVO11_FUNCTION=61`; servo/ARM/mod/parametre
  komutu verilmedi.
- Pi'deki yetkili `ana-imx708.json` kopyasında yalnız start2→3 ve geçici
  tarama hızı 2,5→**3,5 m/s** yapıldı. Seq2'ye transit FC sınırıyla 10 m/s'ye
  kadar; seq3'te DO_CHANGE_SPEED ACK gelmeden arama yok. Controller ve link
  seq2'de hız/hedef devralmayı engeller. Mac profili Pi üzerine rsync edilmedi.
- Canlı yeni rota: TAKEOFF1=15 m, WP2–16=15 m, LAND17=1 m; digest
  `9280b84931937b757c66e66518b76adbdc7156ee2a3ee2839ad446ebf84abd90`.
  Tarama yolu seq3–16 yaklaşık 697 m/199 s. Hedef waypointlerden LAND17'ye
  doğrudan mesafe en çok yaklaşık 195 m.
- Kullanıcı iki yükün fiziksel olarak takılı ve hedef bölgesi→LAND17
  koridorunun boş olduğunu doğruladı. Yeni sortie
  `20260912T114011Z-ana-imx708`; ledger'da 0 kayıt. Pi'de digest yazıldı,
  `start3/end16` ve **EŞLEŞİYOR** geri okundu. Yetkili Pi profili Mac'e
  eşlendi; SHA256 `c8645c7d…24d29` iki tarafta aynı.
- Eski rastgele test waypointleri yalnız `demo.py`/test fixture'larında;
  üretim `competition.main` canlı FC rotasını `search_scope=mission`+digest
  ile kullanır.
- Son profil `--check` eksiksiz; kaynak/test hashleri eş. Yerel
  **415 geçti/5 atlandı**, Pi **373 geçti**.
  IMX708 probe 20 s/1020 kare/50,02 FPS/stale0/hata0/OpenCV p95 3,93 ms.
  Pi yedekleri `runtime/before-fast-transit-3p5-route-20260912/` ve
  `runtime/before-final-route-authorize-20260912/`. Görev başlatılmadı;
  batarya güç döngüsü sonrası önce rota `--profile` kontrolü yapılmalı.

## DEVİR — 12 Eylül panel sade hedef etiketi / HOME irtifası

- `/competition` kutusunda yalnız renk ve varsa PnP mesafesi gösterilir;
  taze HOME-göreli irtifa görüntü ve HTML panelindedir, eski veride `—` olur.
- Pi'ye yedekli dağıtıldı; hashler eş, ilgili 87 ve değişiklik sonrası tam
  373 Pi testi geçti. Pi yedeği
  `runtime/before-panel-label-altitude-20260912/`.

## DEVİR — 12 Eylül AUX1 ana görev saha kurtarma

- Kullanıcı ikinci yükü de taktı. Salt okunur teşhiste AUX3/11 `FUNCTION=0`, çıkış 0 µs; RC11 ise 1495 µs stabil bulundu. Kullanıcı onayıyla yalnız `SERVO11_FUNCTION=61` yazıldı ve geri okundu; servo komutu vermeden AUX3 çıkışı 1495 µs nötr oldu. Bırakma değeri değişmedi: kanal11 800 µs, 0,3 s sonra 1500 µs. ARM/mod/servo komutu verilmedi.
- Aktif iki-yük profil `config/ana-imx708.json`: sortie `20260911T213056Z-ana-imx708`, rota digest `084b315891c3cee52707fd65beb970bd58f77b5505370365e6a8cb3c4dbbc47e`. AUX1-only profil yedek/tek-yük seçeneği olarak korunur.

- Son iki AUX1 uçuşu incelendi. Son uçuşta 15 mavi + 6 kırmızı aday vardı fakat rota parmak izi uyuşmadığı için durum baştan sona `WAIT_AUTO`; duruş/alçalma/servo komutu doğru olarak üretilmedi. Önceki uçuşta kırmızı hedefte duruş ve 2,61→0,38 m merkezleme oldu; merkez kilidi 0,8/1,5 s iken PnP düzlem çözümü kesildi, kalıcı `ABORTED` oldu. Hiç `DESCENDING`, `RELEASE_WAIT` veya PWM yoktu; AUX1 donanım arızası kanıtı yok.
- Ana profillerin geçici AUTO tarama hızı 3,0→2,5 m/s. AUX1-only profilde yalnız kırmızı hedef aktiftir ve mavi yükü kanal9/1800 µs ile bırakır; mavi hedef panelde pasif olarak etiketlenir.
- PnP açı/reprojeksiyon emniyet eşikleri gevşetilmedi. Duruşta PnP ile doğrulanmış sabit yer hedefi, aynı taze OpenCV dörtgeni izlenirken PnP kesilse de sabit koordinatla izlenir. Görsel dörtgen de kaybolursa araç durur; 2,5 s sonra yükü koruyup AUTO taramasına döner ve yeniden deneyebilir; sorti kalıcı kapanmaz.
- 5 m alçalma için PnP yüksekliği ile FC HOME-göreli kamera yüksekliğinin daha küçüğü kullanılır; sahada PnP'nin yaklaşık 1,2 m yüksek okuması aracı 5 m'nin altına daha fazla alçaltamaz. Servo ancak 5 m civarında 3 s kararlı kilitten sonra tetiklenir.
- Canlı FC rotası salt okunur doğrulandı: TAKEOFF1 ve WP2–6 15 m, LAND7 1 m; AUX1 profil digest'i `084b315891c3cee52707fd65beb970bd58f77b5505370365e6a8cb3c4dbbc47e` ve EŞLEŞİYOR. Rota değiştirilmedi.
- Yerel 354 geçti/5 atlandı; Pi 312 geçti. Pi'ye dağıtıldı. Yedek iki tarafta `runtime/before-field-recovery-20260911/`. Eski uçuş süreci yerde/DISARM iken kapatıldı; yeni süreç başlatılmadı. Servo/ARM/mod/FC parametre komutu verilmedi.

## DEVİR — 11 Eylül rota anlık 15 m görünüp 10 m'ye geri döndü

- Kullanıcı `7c96…4c13` digest'li TAKEOFF1/WP2–9=15 m, LAND10 çıktısı paylaştı; salt okunur ilk Pi kontrolü bunu doğruladı. Profil kısa süre bu rotaya eşlendi. Birkaç saniye sonra FC iki ardışık okumada yeniden eski/onaylı TAKEOFF1/WP2–6=10 m, LAND7 ve `517211…bfae` rotasını verdi. Pi'de rota yazan süreç/service yok; değişim dış GCS tarafındandı.
- Kullanıcının önceki açık kararı “takeoff 10 kalsın” ve kararlı canlı FC rotası esas alındı. `ana-aux1-only.json` tekrar start2/end6/digest `517211…bfae` yapıldı ve Pi son salt okunur kontrolünde **EŞLEŞİYOR**. İlgili 89 yerel test geçti. FC rotasına yazı, servo, ARM, mod veya parametre komutu gönderilmedi. Yedek `runtime/before-aux1-route15-20260911/`.

## DEVİR — 11 Eylül düşük bant genişlikli etiketli canlı panel

- Kullanıcı 300 m bağlantıda anlık etiketli kamera görüntüsü istedi. Mevcut `/competition` paneli OpenCV hedef kutusu/rengi ve görev durumunu zaten gösterir. Plain UDP yerine her karesi bağımsız HTTP JPEG tutuldu; bozuk/kayıp kare sonraki kareyi zincir halinde bozmaz ve tarayıcı dışında alıcı gerekmez.
- Ana `competition-base.json` panel çıkışı 960px/8fps/Q65 → **640×360, 4 FPS, JPEG Q35** yapıldı. Kamera/vision kontrol hattı 1280×720@50 FPS kalır; yalnız panel önizlemesi küçülür. Etiket/çerçeve artık küçültmeden sonra çizilir, yazı okunurluğu korunur. Yerel 350 geçti/5 atlandı.
- Erişim aynı ağdan `http://192.168.137.145:8081/competition`. Pi dağıtıldı; 56 ilgili test geçti. Gerçek IMX708 probe: 1018 kare/50,03 FPS, hata yok; örnek etiketli JPEG 11.536 bayt, 4 FPS'te yaklaşık **369 kbit/s**. Kanıt `artifacts/low-bandwidth-panel-20260911/`. 300 m menzil yazılımla garanti edilemez; 2,4 GHz radyo/AP, anten görüş hattı ve RSSI belirleyicidir. Yedek iki tarafta `runtime/before-low-bandwidth-panel-20260911/`.

## DEVİR — 11 Eylül yalnız AUX1 takılı tek-yük sortie'si

- Kullanıcı fiziksel durumu doğruladı: yalnız AUX1/kanal9'daki mavi yük takılı, AUX3 sonra düzeltilecek; AUX1 bırakılabilir. Yeni `config/ana-aux1-only.json`: gerçek servo, sortie `20260911T194157Z-aux1-only`, payloads yalnız `mavi`, canlı rota digest `517211…bfae`, tarama Seq2–6, 3 m/s, hedefte 5 m.
- Controller yalnız kırmızı hedefi kabul eder (kırmızı hedef→mavi/AUX1 yük). Mavi hedef tamamen yok sayılır. AUX1 ACK+çıkış doğrulanınca takılı bütün yükler tamamlanmış sayılır ve doğrudan LAND7 seçilir. AUX3'e PARAM isteği veya servo komutu gönderilmez; link katmanı payload izin listesini ayrıca uygular.
- Genel iki-yük profillerinin davranışı değişmedi; payloads alanı yoksa iki yük varsayılır. Yerel 347 geçti/5 atlandı; Pi ilgili 73 geçti ve yeni profil `--check` eksiksiz. Pi'ye dağıtıldı, yedek iki tarafta `runtime/before-aux1-only-20260911/`. Canlı AUX1 parametre kontrolü yeni süreç açılınca yapılır; eski DONE süreci kapatılmadı.

## DEVİR — 11 Eylül ana OpenCV tarama hızı 3 m/s

- Kullanıcı 10 m'lik yeni rotayı kabul etti ve ana AUTO tarama hızını 1,5→3,0 m/s istedi. `ana-gorev.json`, `ana-imx708.json`, `ana-opencv-test.json` 3,0 m/s oldu; doğrulama üst sınırı yalnız ana görev için 3 m/s'ye çıkarıldı. Kalıcı FC parametresi yazılmadı; komut geçici `MAV_CMD_DO_CHANGE_SPEED` olarak kalır.
- Merkezleme/alçalma limitleri değişmedi: hedefte fren sonrası GUIDED merkezleme, 5 m hedef yükseklik, 0,25 m/s aşağı hız ve 0,2 m/s² ivme sınırı. 3 m/s frenleme hedefin kadrajdan çıkma riskini 1,5 m/s'ye göre artırır.
- Yerel 345 geçti/5 atlandı; Pi ilgili 64 geçti. Yedek iki tarafta `runtime/before-search-speed-3mps-20260911/`. Canlı rota TAKEOFF1/WP2–6=10 m, LAND7 ve digest `517211…bfae`; simulated `ana-opencv-test.json` zaten birebir eşleşiyor. Gerçek servo ana profillerinin digest/sortie'si payload fiziksel durumu doğrulanmadan değiştirilmedi.

## DEVİR — 11 Eylül yeni 15 m rota / 5 m merkezleme yüksekliği

- Ana OpenCV merkezleme görevinde tarama Mission Planner `Seq 2` ile başlayacak; hedef ortalanınca 5 m kamera yüksekliğine inilecek. `ana-gorev.json`, `ana-imx708.json` ve `ana-opencv-test.json` başlangıç2 oldu.
- Ana kontrol `target_camera_height_m=5.0`, güvenlik alt sınırı `minimum_camera_height_m=3.0`; yumuşak iniş 0,25 m/s ve ivme sınırı 0,2 m/s² korundu. 15→5 m ideal iniş yaklaşık 40 s.
- Yeni rota henüz tamamlanmadı: digest, tarama bitiş sırası, sortie, servo ve FC değiştirilmedi. Rota yüklenince canlı rota okunup LAND öncesi son sıra ve digest üç ana profile eşlenmeli. Yerel 344 geçti/5 atlandı; Pi ilgili 115 geçti (hızlı profil sapmasına bağlı 3 envanter örneği seçilmedi). Yedek iki tarafta `runtime/before-5m-descent-20260911/`.
- Pi'de eski `ana-opencv-test` süreci hâlâ açık fakat kontrolde DISARM/LANDED/DONE idi; kapatılmadı. Süreç eski 9 m ayarını bellekte taşır. Yeni rota uçuşundan önce eski terminalde Ctrl+C ve yeniden başlatma şarttır.

## DEVİR — 11 Eylül kırmızı hedefte sert iniş kök nedeni ve acil düzeltme

- Son ana OpenCV uçuş kaydı `competition-2f3a08cb283f45de9e3d9f0866133b76.jsonl`: kırmızı hedefte STOPPING→VERIFYING→INTERCEPT→CENTERING→DESCENDING tamamlandı. Kodun istediği aşağı hız en fazla **0,281 m/s** idi; sert inişin kaynağı bu komut değildi.
- 329,651 s'de hedef/geometri kaybıyla alt Controller `ABORTED` üretti ve eski genel failsafe `GUIDED→LOITER` yaptı. Kumanda AUTO anahtarında fakat gaz kolu düşük olduğu için LOITER sonrası dikey hız yaklaşık **2,59 m/s aşağı** çıktı; araç yere kadar alçaldı. Kanıt yerelde `artifacts/soft-descent-20260911/before-fix-flight.jsonl`.
- Yarışma akışında hedef etkileşimi sırasındaki teknik iptal artık `stop → AUTO (GUIDED beklenir) → revoke` yapar; alt Controller'ın LOITER eylemi `DualController` sınırında değiştirilir. Pilotun gerçek mod müdahalesinde mod zorlanmaz. LAND sırası seçme/devir hatalarında eski "rotaya dönme" yasağı korunur.
- Yarışma MAVLink komut kirası/kapanış failsafe'i de LOITER yerine onaylı AUTO rotasına döner; legacy/genel MavlinkLink LOITER davranışını korur. Ayrıca önceki acil yumuşatma korunuyor: `max_descent_mps=0.25`, `max_accel_mps2=0.2`, 7 örnekli medyan PnP ve aşağı hız aşımında `stop`.
- Yerel tam test: **344 geçti / 5 atlandı**. Pi kritik testleri **125/125** geçti; tam Pi dizisi **301 geçti / 1 mevcut profil sapması** (`hizli-gorev.json` Pi'de start3, yerel/onaylı profilde start2). Ana OpenCV test profili rota digest'iyle eşleşti.
- Düzeltme Pi `furkan@192.168.137.145` üzerine dağıtıldı; öncesinde uçuş uygulaması kapalı ve FC salt okunur kontrolde DISARM idi. Yedek iki tarafta `runtime/before-auto-abort-20260911/`; önceki yumuşatma yedeği iki tarafta `runtime/before-soft-descent-20260911/`. Servo/ARM/mod/FC parametre komutu verilmedi ve uçuş uygulaması başlatılmadı.

## DEVİR — 11 Eylül yarışma hattı yalnız OpenCV

- Kullanıcı açıkça YOLO'yu kaldırıp yalnız OpenCV kullanılmasını istedi. Aktif ana ve hızlı görev kamerayı doğrudan Picamera2/V4L2 → OpenCV hattından alır. Yarışma giriş noktası Hailo backend'ini yüklemez, model dosyasını doğrulamaz ve Frame.detections boş üretilir. Yarışma kaydedicisi de bu profillerde HEF/model bağımlılığı taşımaz.
- Tek görüntü adayı HSV mavi/kırmızı maskesi ile dolu, dışbükey dörtgendir. Hızlı görev ardışık OpenCV kutularını; ana görev aynı bölgeden çıkan köşe/PnP ölçümünü kullanır. Merkezleme, hız/yükseklik kilitleri ve servo güvenlikleri korundu. Görüntüye eklenmiş AI metadata'sı karar zincirinde yok sayılır. Artık kullanılmayan competition/bbox.py kaldırıldı.
- Doğrulama: yerelde 343 geçti/5 atlandı. Pi'de 300 geçti; tek kalan hata bu işten bağımsız mevcut profil sapmasıdır: Pi hizli-gorev.json başlangıç3 ve yerelden farklı digest taşıyor; yerel/onaylı hızlı profil başlangıç2. Rota/digest/sortie bu işte değiştirilmedi.
- Pi gerçek kamera probe'u MAVLink bağlantısız observe/connect=False: 20 s, 1028 kare, 50,02 FPS, stale0, hata0, OpenCV toplam p95 4,08 ms. Kanıt artifacts/opencv-only-20260911/ altında. Ortam karanlıktı: görüntü alanında V medyan 2, p99 8; mevcut min_value=35 ile mavi/kırmızı renk maskesi %0. Bu ışıkta renk tespiti saha kabulü değildir; hedefler güçlü ve homojen aydınlatılmadan uçulmaz. Yedek iki tarafta runtime/before-opencv-only-20260911/.
- Uçuş hâlâ hazır değil: canlı FC'de kırmızı AUX3/11 FUNCTION0 iken profiller FUNCTION61 bekliyor; ayrıca Pi hızlı rota profili sapmış durumda. Servo/ARM/mod/FC parametresi gönderilmedi, görev uçuş modu başlatılmadı.

## DEVİR — 11 Eylül AUX3 açılış hareketi için nötr PWM hazırlığı

- Canlı salt okunur incelemede kırmızı servo AUX3/kanal11 `SERVO11_FUNCTION=0` ve açılış çıkışı `0 us`; alıcı `RC11=1495 us` sabit bulundu. ArduPilot'ta FUNCTION0 normal durumda PWM darbesi üretmez; servo sinyalsizken güç alıp yükü uçuştan önce düşürüyor.
- Beş servo profili kırmızı kanal için `function=61` (RCIN11 passthrough) bekleyecek şekilde hazırlandı. FC ayarı da 61 yapıldığında AUX3 açılışta RC11'in nötre yakın 1495 us değerini üretir; 51–66 işlevlerinde DO_SET_SERVO kullanımı ArduPilot tarafından desteklenir. Kırmızı bırakma 800 us/0,3 s ve yazılım nötrü 1500 us korunur.
- **Canlı FC parametresi henüz değiştirilmedi ve servo komutu gönderilmedi.** Profil artık FUNCTION0 ile uçuşu reddeder. Son adım için kırmızı yük/servo mekanik olarak ayrılmalı, kullanıcıdan FC parametre yazma onayı alınmalı; sonra `SERVO11_FUNCTION=61` yazılıp güç döngüsü ve 1495 us'ta fiziksel duruş tezgâhta doğrulanmalı. İlk enerjilenme seğirmesinin yazılımla mutlak garantisi yoktur; sürerse servo besleme geciktirme/sinyal pull-down ve mekanik emniyet gerekir.
- Yedek iki tarafta `runtime/before-servo-startup-neutral-20260911/`.
- Doğrulama: yerel 351 geçti/5 atlandı; Pi 309 geçti; dağıtılan dosyaların SHA256 değerleri eş.

## DEVİR — 11 Eylül tarama ikinci waypoint geçildikten sonra

Kullanıcı ilk direği Mission Planner sıra 2 yaptığını, taramanın bundan sonra başlamasını istedi. Ana IMX708/genel profillerde `search_start_seq=3`: sıra2'ye giderken hedefe devralma yok; FC sıra3'e geçtiğinde tarama açılır. Hızlı profil başlangıcı2 ve davranışı korundu. Mission kapsamı artık TAKEOFF sonrası seçilen başlangıcı kabul eder; LAND öncesi bitiş ve waypoint komutları zorunlu. İki stratejide sıra2 bekleme/sıra3 duruş regresyonu eklendi. Yerel351 geçti/5 atlandı. Pi test sonucu `runtime/before-search-seq3-20260911/tests-pi.txt` yerel kaydında. İki tarafta aynı adlı yedek var.

Kullanıcı yerde/DISARM olduğunu, rotanın hâlâ düzenlendiğini söyledi. Yeni digest onaylanmadı/okunmadı; sortie/servo/FC değişmedi. Yeni rota tamamlanınca digest ve son tarama sırası eşleştirilmeli. Önceki sohbetin rota güncelleme bloğu başlangıcı TAKEOFF+1'e geri çevirir; ana görevde `start=3`, `end=plan.land_seq-1` kullanılmalı. Yalnız digest yazan route_digest.py başlangıç3'ü korur.

## DEVİR — 11 Eylül 15:05 ana görev kurtarma; hızlı görev korundu

- Kullanıcı hızlı görevi yedek olarak korumamızı istedi. **Hızlı profil/base dosyaları SHA256 ile aynı**, servo/rota/digest/sortie değişmedi. Ana düzeltmeler Pi'ye yüklendi; iki tarafta `runtime/before-center-recovery-20260911/` yedeği var.
- 13:40–13:47 uçuş kayıtları: maviye GUIDED istenmiş fakat 5,7 m/s hızdan fren sırasında 8–9 m ilerlenip hedef kaybedilmiş. Kırmızı duruşunda seyrek PnP doğrulaması 0,5 s kilidi tamamlayamamış; INTERCEPT/servo yok. Buzzer'ın kesin nedeni eski kayıtta yok.
- Yalnız ana IMX708/genel profilde **geçici AUTO tarama hızı 1,5 m/s**, doğrulama süresi 3→8 s. Her AUTO tarama girişinde DO_CHANGE_SPEED ACK beklenir. Kalıcı WPNAV_SPEED=1000 değiştirilmez. Hızlı görev bu komutu üretmez. Alan/rota/RC/taze veri ve pilot korumaları sürer.
- Ana PnP önce eski köşeleri kullanır; yalnız reddedilirse gerçek renk kenarında en çok 3 px alt piksel köşe düzeltmesi dener. Önceki kabul edilen ölçümler ve bütün geometri eşikleri korunur. Ana JSONL artık karar girdisini, köşeleri/pozu ve FC STATUSTEXT'i kaydeder.
- **Yerel 349 geçti/5 atlandı; Pi 307 geçti.** ArduCopter 4.6.3 hexa SITL ana görev iki hedefte merkezleme, iki simulated yük ve LAND/DONE (71,97 s); güncel mission kapsamındaki hızlı görev iki simulated yük ve LAND/DONE (47,07 s), velocity/search_speed yok. Eski field kapsamlı hızlı SITL giriş kapısını doğrulayamadı; üretim hızlı kodu değiştirilmeden güncel saha kapsamıyla test edildi. Önceki “SITL yok” notu güncel değil; macOS binary `/private/tmp/safak-ardupilot-4.6.3/build/sitl/bin/arducopter` mevcut.
- Pi kamera/Hailo: 20 s, 1040 kare, 50,08 FPS, stale0/hata0; MAVLink bağlantısız probe. Canlı rota salt okunur yeniden eş: TAKEOFF1 10 m, waypoint2–6 10 m, LAND7 1 m; digest `b652eeb66c71e0a4ff02d9c9e8c2e8a2c10313974a3089203f62eed45dc51acb`.
- Gerçek uçuşun eşzamanlı videosu olmadığından kırmızı PnP düzeltmesinin saha kabulü **yok**; yaklaşık kalibrasyon sürüyor. Sonraki uçuşta `decision_input.diagnostics` incelenmeli. Kırmızı açılış servosu kullanıcı isteğiyle ertelendi; nötr komutu açıkça reddedilmişti. Canlı FC'ye servo/ARM/mod/parametre yazma komutu verilmedi; uçuş uygulaması başlatılmadı.
- Ayrıntı: `docs/competition/ANA-KURTARMA-20260911.md`; kanıt: `artifacts/center-flight-1347-20260911/`. Ana uçuş komutu ve sortie aynı; yeni dosyalar sonraki süreç açılışında yüklenir.

## DEVİR — 11 Eylül yeni saha: TAKEOFF–LAND arası tüm rota taraması

- **Dağıtım/kontrol tamam:** yerelde 324 geçti / 5 atlandı, Pi’de 282 geçti. Ana profil --check eksiksiz, canlı rota digest eş. Kamera/Hailo 20 s: 1017 kare, 50,06 FPS, stale0, hata0. Görev uçuş süreci başlatılmadı; kamerayı açan yalnız MAVLink bağlantısız probe idi ve temiz kapandı.
- Kullanıcı yeni rota yükledi ve açıkça “takeoffdan lande kadar tara” dedi. Ana IMX708, ana genel ve hızlı profiller `search_scope=mission` olarak güncellendi: 10 m TAKEOFF1, tüm WAYPOINT2–6 taranır, LAND7'de arama biter. Yeni digest `b652eeb66c71e0a4ff02d9c9e8c2e8a2c10313974a3089203f62eed45dc51acb`. LAND satırı z=1 m olarak FC'den okundu; FC rotası değiştirilmedi.
- Mission kapsamı eski saha kapısı/poligonunu uygulamaz; koordinat uydurulmadı. Varsayılan field kapsamında eski kapı/poligon korumaları sürer. Mission kapsamında da rota parmak izi, bütün waypoint aralığı, minimum devralma irtifası, taze telemetri/görüntü, pilot müdahalesi ve yerde başlatma şartları korunur. FC fence ayarları değiştirilmedi.
- Kullanıcı fiziksel durumu doğruladı: yerde/DISARM, yalnız mavi yük takılı; kırmızı güç verilir verilmez, görev açılmadan düşüyor. Salt okunur AUX3/11: FUNCTION0 MIN800 MAX1900 TRIM1500, bildirilen çıkış0; AUX1/9 RCIN8 FUNCTION58, bildirilen çıkış2006. Kırmızı açılış sorununun kesin nedeni henüz doğrulanmadı. Kullanıcı nötr servo denemesini reddetti, ardından kırmızı incelemesini erteleyip uçuş hazırlığı istedi. **Servo/ARM/mod/FC parametre komutu verilmedi.** Servo eşlemeleri, aktüatör seçimi ve sortie kimlikleri değiştirilmedi; ana görev hâlâ gerçek servo profilidir.
- Yedek iki tarafta `runtime/before-full-route-20260911/`; kanıt `artifacts/route-servo-startup-20260911/`. Önceki gerçek uçuş tekrar testi profil bağımlılığından ayrılarak kayıttaki saha ayarlarına sabitlendi. Yeni testler tüm waypointler/iki renk/iki stratejide duruş, TAKEOFF/LAND/düşük irtifa/yanlış digest/eksik aralık/havada başlatmada ret ve link korumalarını kapsar.

## DEVİR — 11 Eylül 13:10 sonrası ana görevde durmama düzeltmesi

- **Yeni kök neden:** 12:47 ve 12:53 ana uçuşlarında AUTO kalkış/giriş noktası poligon dışındaydı. `DualController` giriş kapısından önce kalıcı `ABORTED` oluyordu; sonradan alana girse de aramıyordu. Kayıtlarda toplam **45 mavi + 51 kırmızı** tespit var. Önceki rota parmak izi hatasından ayrı bir sorun.
- **Düzeltme Pi'de:** giriş kapıları geçilmemiş ve henüz kontrol devralınmamışsa poligon dışında komutsuz bekle. Kapı/alan/tarama koşulları sağlanınca arama başlar. Giriş sonrası sınır ihlali, pilot müdahalesi ve MAVLink poligon koruması aynen sürer. Ortak akış iki stratejide düzeltilmiştir.
- **Doğrulama:** iki gerçek kayıtta iki renk ayrı ayrı oynatıldı; dört senaryoda da artık GUIDED duruş isteği oluşuyor. Eski kodla 7 yeni test başarısız, yeni kodla 9/9 başarılı. Yerel **305 geçti / 5 atlandı**, Pi **263 geçti**. Yedek iki tarafta `runtime/before-entry-polygon-20260911/`.
- FC rotası salt okunur yeniden doğrulandı: 15 m, tarama 2–8, LAND 9, digest `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707` ana profille eşleşiyor. Rota/digest/sortie/servo/FC parametreleri değiştirilmedi. Görev/kayıt kapalı; ARM/mod/servo komutu gönderilmedi.
- **Saha sınırı:** son iki uçuşta AUTO geçişindeki seyrek geometri örnekleri 10/46 kabul (~%22), fakat hiç GUIDED duruşu yok. Bu oran duruş sonrası PnP başarımı değildir. Düzeltme sonrası gerçek merkezleme/bırakma henüz uçulmadı; sonraki uçuşta STOPPING/VERIFYING/INTERCEPT verileri ölçülmeli. Kalibrasyon hâlâ deneysel.
- Ayrıntı: `docs/competition/ANA-DURMAMA-20260911.md`. Kanıt: `artifacts/center-investigation-20260911/`. Yeniden oynatma: `tests/test_entry_polygon.py`, kaynak kesitleri `tests/fixtures/entry-polygon-20260911.json`. Diğer ortam/profil/çalıştırma bilgileri aşağıdaki önceki DEVİR bölümünde.

## DEVİR — 11 Eylül 2026 kapanış durumu (yeni sohbet buradan başlasın)

### Ortam
- Yerel: `/Users/kaan/Documents/ChatGPT/last şafak` (venv: `.venv/bin/python`). Pi: `furkan@172.20.10.6`, proje `/home/furkan/Desktop/safak-gorev2-quad`.
- Pi'de her komuttan önce: `cd /home/furkan/Documents/proje/hailo-rpi5-examples && source ./setup_env.sh && cd /home/furkan/Desktop/safak-gorev2-quad && export PYTHONPATH="$PWD/runtime/python:$PWD:$PYTHONPATH"`.
- Pixhawk Cube Orange, by-id `...CubeOrange...-if00`, MAV_TYPE 13 hexa, firmware 4.6.3. Kamera IMX708 CAM1, 1280×720 @50 FPS, sensör modu 2304×1296, LensPosition 0. Model `best_hailo_model/safakyepyeni.hef`.
- FC canlı değerler (salt okunur): `WPNAV_SPEED=1000`, `WPNAV_ACCEL=250`, `SERVO9_FUNCTION=58 MIN1100 MAX1900`, `SERVO11_FUNCTION=0 MIN800 MAX1900`.

### Görev profilleri
- Ana: `config/ana-imx708.json` (strategy=center), hızlı: `config/hizli-gorev.json` (strategy=quick). İkisi de actuator=servo.
- Rota FC'de **15 m**: seq1 TAKEOFF 15, seq2–8 WAYPOINT 15, seq9 LAND. Tarama 2–8. Üç profilin `mission_fingerprint` değeri `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707`.
- Servo eşlemesi (tezgâhta doğrulandı, sahada iki yük düştü): mavi AUX1/kanal9 → 1800 µs; kırmızı AUX3/kanal11 → 800 µs, 0,3 s sonra 1500 µs nötr. Mavi hedef görülünce kırmızı yük, kırmızı hedef görülünce mavi yük bırakılır.
- İki yük kabul edilince kalan tarama waypointleri atlanıp **doğrudan LAND waypointine** uçulur (`SELECT_LAND` → `HANDOFF_LAND` → `LANDING`).

### Saha sonucu
- Hızlı görev sahada **tam başarılı**: iki yük de gerçek servo komutuyla bırakıldı (`20260911T082504Z-hizli-imx708`).
- Ana görev henüz başarılı bir bırakma yapmadı. Son denemede model 25–30 m'de 39 mavi + 60 kırmızı gördü ama profil rota parmak izi eski olduğu için kontrol hiç devralmadı; parmak izi düzeltildi.
- Aktif ana sortie `20260911T093750Z-ana-imx708`; payload ledger'da kaydı yok, yükler takılıysa aynı kimlik kullanılabilir. Ledger `runtime/competition/payload-ledger/payloads.sqlite3`.

### 11 Eylül'de yapılan düzeltmeler (hepsi Pi'de yüklü, testler geçti)
1. `competition/bbox.py` → `clamp_bbox`: kadraj kenarına taşan YOLO kutusu atılmıyor, kırpılıyor; alanının %60'ı kadraj dışındaysa reddediliyor. (Mavi 42 tespitin 35'i eleniyordu.)
2. `color_search.detect(border_px=0)`: kenara değen renk bölgesi aday olmayı engellemiyor; metrik ölçümün kendi kenar payı (`corner_screen`) duruyor.
3. `competition/controller.py`: frenleme (STOPPING) aşamasında kutu örtüşmesi koparsa, seçilen renkten tek aday varsa hedef yeniden yakalanıyor. Doğrulama (VERIFYING) aşamasında kural katı.
4. `competition/controller.py`: ana görevde VERIFYING sırasında PnP çözülmeyen kare veya kısa hız sıçraması birikimi silmiyor, yalnız saymıyor.
5. `controller.py` (legacy, özgün kopya `archive/legacy-options/controller-before-center-hold-gap.py.txt`): merkez/bırakma kilidi geometri boşluğunda silinmiyor; 0,25 s'yi aşmayan boşlukta son hız komutu korunuyor (en çok ~20 cm kör hareket), sonra duruyor, `lost_target_abort_s` (2,5 s) aşılırsa iptal.
6. `competition/link.py`: WPNAV_SPEED üst sınırı iki görevde de 1000 cm/s (kullanıcı kararı; fren ~3 s sürer).
7. `config/competition-base.json` ana görev ayarları: bırakma yüksekliği 9 m sabit; `max_descent_mps` 1,0; `max_climb_mps` 1,0; `interaction_timeout_s` 200; `center_tolerance_m` 0,5; `descent_center_tolerance_m` 0,7; `height_tolerance_m` 1,0; `minimum_camera_height_m` 7,0; `release_horizontal_speed_mps` 0,3; `release_vertical_speed_mps` 0,2; `lost_target_abort_s` 2,5; `max_horizontal_speed_mps` 0,8; **`center_tolerance_height_ratio` 0,05** (kilit toleransı = `max(0,5; 0,05×görsel yükseklik)`; 15 m'de 0,75 m, 9 m'de 0,5 m).
8. `scripts/route_digest.py`: rotayı salt okunur okur, irtifaları ve digest'i yazar; `--profile` karşılaştırır, `--write` yalnız `mission_fingerprint` alanını günceller.

### Ölçülen gerçek değerler (parametrelerin dayanağı)
- PnP saçılması 10 m'de: yatay sd 0,12 m, görsel yükseklik sd 0,39 m, reprojeksiyon 0,66 px. Gürültü yükseklikle büyür (yatay ≈0,012×h, yükseklik ≈0,0039×h²).
- GUIDED duruşunda araç sürüklenmesi 0,20–0,27 m/s. Fren 1000 cm/s'den ~3 s; WPNAV_ACCEL 250 → ~14° yatış → 15 m'de ~3,8 m görüntü kayması.
- Metrik geometri (PnP) başarımı fren sırasında **%26** ölçüldü. Benzetime göre ana görevin bırakma yapabilmesi için **≥ %40** gerekiyor.
- 25–30 m'de tespit boyutu: mavi ~75 px, kırmızı ~43 px, skor ~0,62.

### Açık işler
1. **Ana görev uçuşu**: uçuştan sonra JSONL'deki `diagnostics` alanından gerçek PnP başarım oranı ölçülmeli. %40'ın altındaysa geometri/kalibrasyon tarafı düzeltilmeli.
2. Kamera kalibrasyonu `config/camera.imx708-infinity-approx.json` hâlâ **yaklaşık/deneysel; saha kabulü yok** (kalibrasyon lens pozisyonu 0,106, çalışma 0,0). Merkezleme doğruluğu bağımsız ölçülmedi.
3. Rota değişirse `scripts/route_digest.py --profile ...` ile kontrol, `--write` ile güncelleme şart; yoksa yazılım devralmaz.
4. Bu makinede ArduPilot SITL yok; doğrulama birim testi + benzetim seviyesinde (yerel 296, Pi 254 test geçiyor).

### Çalışma kuralları
- Kullanıcı kısa ve Türkçe yanıt istiyor; projeyi yeniden anlattırma.
- Kullanıcı açıkça istemeden **yerde servo komutu verme** (yükleri düşürür), **ARM veya uçuş modu komutu gönderme**.
- FC parametresi yazmadan önce sor. Rota/digest/sortie değişikliklerinde fiziksel durumu (yükler takılı mı) kullanıcıya doğrulat.
- Değişiklikleri Pi'ye yükle, iki tarafta da testleri çalıştır, `runtime/before-*` altına yedek al, AGENTS.md ve docs/HANDOFF.md başına özet yaz.
- `docs/competition/legacy-sha256.json` ile korunan dosyalar değişecekse özgün kopya `archive/legacy-options/` altına alınıp `preserved-paths.json` eşlemesine eklenir.

### Çalıştırma
```
# uçuş öncesi rota kontrolü
python scripts/route_digest.py --profile config/ana-imx708.json
# görev (kamerayı bu açar)
export MAVLINK20=1
python -m safak_gorev2.competition.main --config config/ana-imx708.json --mode flight
# kayıt (ayrı terminal, görevden sonra)
python -m safak_gorev2.record --config config/ana-imx708.json --panel-url http://127.0.0.1:8081 --root runtime/recordings
```
Panel `http://172.20.10.6:8081`. Kapatma: önce kayıt, sonra görev (Ctrl+C).

## En güncel — 11 Eylül 15 m rota parmak izi ve "hiçbir şey görmedi" teşhisi

Kullanıcı 25 m denemesinde hiçbir şey görülmediğini bildirdi. Kayıt bunun tersini gösteriyor: `runtime/competition/center-imx708/competition-d84a29d9...1468.jsonl`, 547 kayıt, **39 mavi + 60 kırmızı tespit** (irtifa 24,9–30,0 m; mavi kutu ortalama 75×73 piksel, kırmızı 43×42 piksel; skor ortalama 0,62) ve 115 aday. Yani model yüksekten görüyor.

Kontrol hiç devralmadı: durum baştan sona `WAIT_AUTO` ve gerekçe **"Rota parmak izi onaylanan rotayla eşleşmiyor"**. FC'deki rota 15 m'ye güncellenmişti (seq1 TAKEOFF 15 m, seq2–8 waypoint 15 m, seq9 LAND), profillerdeki parmak izi ise eski 10 m rotasına aitti. Yazılım doğru davrandı; 52. saniyede pilot LOITER aldı.

Canlı rota salt okunur okundu ve üç profilin `mission_fingerprint` alanı `54b32d9b…747fe` → `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707` olarak güncellendi (`scripts/route_digest.py --write`). Araca `--profile` seçeneği eklendi: rota ile profili karşılaştırıp EŞLEŞİYOR/EŞLEŞMİYOR yazar, böylece bu hata uçuştan önce görülür. Rota komutları doğrulandı: tarama bölümü 2–8 yalnız waypoint, LAND 9.

15 m için ayrıca parametre değişikliği gerekmedi; kilit toleransı yükseklikle ölçekleniyor (15 m'de 0,75 m, bırakmada 0,50 m). Benzetim 15 m'den: PnP başarımı %50–%80'de 30–46 s, %40'ta 97 s içinde bırakma; %30 yetmiyor. Test dizisine 15 m eklendi. Yerelde 296, Pi'de 254 test geçti.

Bu sortie (`20260911T093750Z-ana-imx708`) için payload ledger'da kayıt yok — yükler hâlâ takılıysa aynı kimlikle uçulabilir.

## En güncel — 11 Eylül 25 m uçuş ayarı

Kullanıcı 25 m'de uçacağını bildirdi. PnP gürültüsü mesafeyle büyüdüğü için sabit toleranslar bu irtifada kilidi imkânsız kılıyordu: 10 m'de ölçülen 0,12 m yatay saçılma 25 m'de yaklaşık 0,30 m'ye çıkıyor, sabit 0,50 m tolerans 1,5 s kesintisiz kilide yetmiyor. Benzetimde araç 25 m'de 0,04 m hataya kadar merkezleniyor ama 150 s boyunca 24 m'de takılı kalıyordu.

Çözüm: `center_tolerance_height_ratio` (yeni alan, ana profilde 0,05) ile kilit toleransı `max(center_tolerance_m, oran×görsel yükseklik)` olarak hesaplanıyor. 25 m'de 1,25 m, 17 m'de 0,85 m, bırakma yüksekliği 9 m'de 0,45 m — yani sabit 0,50 m baskın kalıyor ve **bırakma isabeti değişmiyor**. Alçalma sapma toleransı aynı oranda ölçekleniyor. `interaction_timeout_s` 150→200 s yapıldı.

Yükseklikle ölçekli gürültü benzetimi (yatay 0,012×h, görsel yükseklik 0,0039×h²): 25 m'den PnP başarımı %50'de 100 s, %60'ta 46 s, %80'de 45 s içinde, 0,03 m'den küçük hatayla 9,4 m'de bırakma. %40'ta 169 s ile ancak 200 s sınırı içinde kalıyor; %30 yetmiyor. Oran 0 iken (eski davranış) 25 m'de bırakma hiç tamamlanmıyor — test bunu koruyor. 35 m'de %60 başarımla 138 s, %80 ile 78 s.

Ana görev için gereken eşik: **PnP başarım oranı en az yaklaşık %40**. 11 Eylül uçuşunda fren sırasında ölçülen %26 yetmez; uçuş JSONL'indeki geometri diagnostics ile gerçek oran ölçülmeli.

25 m rotası için: yeni rota FC'ye yüklendikten sonra digest değişir. Yeni yardımcı `scripts/route_digest.py` rotayı salt okunur okur, irtifaları ve digest'i yazar, `--write <profil>` ile yalnız `mission_fingerprint` alanını günceller (FC'ye komut göndermez, ARM durumda çalışmaz). Rota içeriği gözle doğrulanmadan uçulmaz.

Yerelde 294, Pi'de 252 test geçti. Yedek `runtime/before-25m-20260911/`. Benzetim saha kabulü değildir.

## En güncel — 11 Eylül merkezleme/kamera incelemesi ve ayarı

Kullanıcı merkezlemenin optimal olup olmadığını sordu. 11 Eylül ana uçuşundaki gerçek metrik örnekler ölçüldü (10 m'de, 50–56 s penceresi, 9 örnek): yatay konum saçılması kuzey sd 0,06 m / doğu sd 0,12 m; görsel yükseklik ortalama 9,70 m, sd 0,39 m, aralık 9,04–10,15 m; yeniden izdüşüm hatası ortalama 0,66 piksel. GUIDED duruşunda araç sürüklenmesi 0,20–0,27 m/s ölçülmüştü.

Eski toleranslar bu gürültünün altındaydı: merkez toleransı 0,20 m (gürültü ±0,2 m), yükseklik toleransı 0,25 m (gürültü sd 0,39 m), bırakma yatay hız eşiği 0,20 m/s (sürüklenme 0,27 m/s), alt yükseklik sınırı 8,5 m (9 m hedefte tek gürültülü örnek iptal ettirebiliyordu). Benzetimde eski değerlerle hiçbir PnP başarım oranında bırakma tamamlanmıyor.

Ana profil (`competition-base.json`) ayarlandı: `center_tolerance_m` 0,20→0,50; `descent_center_tolerance_m` 0,30→0,70; `height_tolerance_m` 0,25→1,00; `minimum_camera_height_m` 8,5→7,0; `release_horizontal_speed_mps` 0,20→0,30; `release_vertical_speed_mps` 0,12→0,20; `lost_target_abort_s` 1,0→2,5; `max_horizontal_speed_mps` 0,40→0,80. Bırakma yüksekliği 9 m aynı.

Yapısal iki kusur düzeltildi (`safak_gorev2/controller.py`, özgün kopya `archive/legacy-options/controller-before-center-hold-gap.py.txt` altına alınıp hash eşlemesine eklendi): (1) PnP çözülmeyen her karede merkez/bırakma kilidi siliniyordu, yani 1,5 s ve 3 s kilit için kesintisiz %100 geometri gerekiyordu; artık kilit silinmez, süreklilik `max_lock_frame_gap_s` (0,25 s) boşluk sınırıyla korunur. (2) Geometrisiz her karede hız sıfırlanıyordu; araç adım adım duruyor ve yaklaşma/alçalma neredeyse durma noktasına geliyordu. Artık 0,25 s'yi aşmayan boşlukta son hız komutu korunur (en çok ~20 cm kör hareket), boşluk büyürse durur, uzun kayıpta görev iptal edilir.

Ölçülen gürültüyle benzetim: eski hâlde hiç bırakma yok; yeni hâlde PnP başarımı %40'ta 50 s, %60'ta 43 s, %80'de 32 s içinde 0,04 m'den küçük hatayla ve 9,3–9,5 m yükseklikte bırakma. %26 (uçuşta fren sırasında ölçülen en kötü değer) hâlâ yetmiyor: araç merkezleniyor ve 9,5 m'ye iniyor ama 3 s kilidi tamamlayamıyor. 17 m testinde JSONL'e yazılan geometri diagnostics ile gerçek süzme oranı ölçülmeli; %40'ın altındaysa geometri tarafı iyileştirilmeli.

Yerelde 288, Pi'de 246 test geçti. Yedek `runtime/before-center-tuning-20260911/`. Benzetim saha kabulü değildir; kamera kalibrasyonu hâlâ `yaklaşık/deneysel`.

## En güncel — 11 Eylül ikinci yükten sonra doğrudan LAND waypointi

Kullanıcı isteği: ikinci yük kabul edildikten sonra kalan tarama waypointlerine gidilmesin, doğrudan rotanın LAND waypointine uçulsun. Eski davranış bulunduğu yerde LAND idi. Yeni akış: GUIDED'deyken `mission_current` ile LAND sırası seçilir (`SELECT_LAND`), telemetride sıra doğrulanınca AUTO'ya devredilir (`HANDOFF_LAND`), AUTO doğru sırada başlayınca `LANDING` olur ve hız sahipliği bırakılır. Yanlış sıra, zaman aşımı veya pilot müdahalesi iptal üretir; rotaya dönülmez. MAVLink katmanında `mission_current` yalnız GUIDED'de ve yalnız `mission.land_seq` için uygulanır, bu sınır zaten mevcuttu.

İniş hâlâ görüntüye veya bitiş kapısına bağlı değil; yerde DISARM ile iki yük tamamlandıysa `DONE`. Onaylanmayan ikinci yük inişi tetiklemez. Testler yeni akışa göre güncellendi (`test_land_after_payloads.py` ve üç uçtan uca akış testi); yanlış waypoint ile AUTO başlarsa iptal edildiğini doğrulayan test eklendi. Yerelde 282, Pi'de 240 test geçti. Yedek `runtime/before-direct-land-20260911/`.

## En güncel — 11 Eylül ana görev yüksek irtifa düzenlemesi

Kullanıcı testleri 17 m'de, yarışmayı yüksekten (35 m'ye kadar) uçacağını bildirdi. Eski ana görev parametreleriyle 35 m'den bırakma imkânsızdı: 9 m bırakma yüksekliğine 0,15 m/s ile inmek en az 173 s sürerken merkezleme/alçalma sınırı 90 s idi, yani her deneme zaman aşımıyla iptal olurdu. `config/competition-base.json` içinde ana görev için `max_descent_mps` 0,15→1,0, `max_climb_mps` 0,30→1,0, `interaction_timeout_s` 90→150 yapıldı. Bırakma yüksekliği 9 m ve alt sınır 8,5 m korundu; isabet tasarımı değişmedi. 35 m'den alçalma yaklaşık 35 s sürer. Hızlı görev profili (`hizli-base.json`) bilinçli olarak değiştirilmedi.

Yeni testler: 17 m ve 35 m'den tam alçalma simülasyonu bırakmaya ulaşıyor ve eski değerlerle 35 m senaryosu başarısız oluyor; ana profiller için parametre koruma testi eklendi. Yerelde 280, Pi'de 238 test geçti. Yedek `runtime/before-high-altitude-20260911/`.

Yüksek irtifada açık riskler: 2 m hedef 35 m'den yaklaşık 54×54 piksel (fx≈948); bugünkü başarılı uçuşlarda hedef ≈200 piksel idi, bu boyutta YOLO/OpenCV başarımı denenmedi. Kamera kalibrasyonu hâlâ `yaklaşık/deneysel; saha kabulü yok`, dolayısıyla PnP doğruluğu yükseklikle birlikte bozulabilir. Mevcut rota 10 m; 35 m'lik yeni rota yüklenirse digest değişir ve profildeki `mission_fingerprint` yenilenmelidir. Ana uçuş öncesi `sortie_id` de yenilenmeli (mevcut kimlikte mavi kaydı var).

## En güncel — 11 Eylül ana görev incelemesi ve düzeltmeleri

Hızlı görev sahada tamamlandı: iki yük de gerçek servo komutuyla bırakıldı. Ardından ana (center) görev kodu, 11 Eylül başarısız ana uçuşunun kaydıyla (`artifacts/servo-bench-20260911/failed-flight-20260911.jsonl`, 851 kayıt) incelendi. Bulgular: mavi 42 tespitin 35'i kadraj taşması yüzünden eleniyordu; kırmızı 46 tespitin yalnız 12'sinde metrik geometri çözülüyordu; VERIFYING sırasında hız 0,20–0,23 m/s bandında eşiği aşıp tüm birikimi siliyordu. Bu üç etki birleşince 0,5 s kesintisiz kanıt hiç oluşmadı ve INTERCEPT/merkezleme hiç başlamadı.

Ana görev için uygulananlar: (1) kutu kırpma zaten her iki stratejide geçerli; (2) kenara değen renk bölgesi artık aday olmayı engellemiyor — metrik ölçümün kendi kenar payı `corner_screen`/`min_border_px` ile korunuyor, yani ölçüm kanıtı zayıflamadı; (3) frenleme (STOPPING) aşamasında kutu örtüşmesi koptuğunda, seçilen renkten tek aday varsa hedef yeniden yakalanıyor; (4) VERIFYING'de PnP çözülmeyen kare veya kısa hız sıçraması birikimi **silmiyor**, yalnız sayılmıyor — süreklilik `ContinuousHold`'un 0,25 s boşluk sınırıyla korunuyor. Hedefin kaybı, 0,8 m'yi aşan konum sıçraması ve sayılan her karenin duruş koşulu aynen duruyor; hızlı görevin sahada doğrulanmış davranışı değiştirilmedi.

Altı yeni test gerçek uçuş örüntülerini kullanıyor ve düzeltmeler geri alındığında başarısız oluyor. Yerelde 276, Pi'de 234 test geçti. Yedek `runtime/before-center-verify-20260911/`. Bu makinede ArduPilot SITL yok; doğrulama birim testi seviyesindedir, saha kabulü değildir.

Kullanıcı kararı: saha süresi nedeniyle `WPNAV_SPEED=1000` ana görevde de kalıyor; yazılımdaki 200 cm/s ana görev sınırı kaldırıldı, üst sınır iki görevde de 1000 cm/s (`link.py`). Bu hızda fren yaklaşık 3 s sürer ve hedef kadrajda kayar; risk kullanıcıya bildirildi. Ana uçuş öncesi açık madde: `config/ana-imx708.json` içindeki `sortie_id=20260911T071605Z-ana-imx708` için ledger'da mavi kaydı var, yeni kimlik gerekiyor. Kamera kalibrasyonu hâlâ `yaklaşık/deneysel; saha kabulü yok` (kalibrasyon lens pozisyonu 0,106, çalışma 0,0); merkezleme doğruluğu ölçülmüş değil. Salt okunur FC kontrolü: yerde, DISARM, LOITER; SERVO9 FUNCTION58 MIN1100 MAX1900, SERVO11 FUNCTION0 MIN800 MAX1900. Servo/ARM/mod komutu verilmedi.

## En güncel — 11 Eylül ikinci hızlı uçuş: kırmızı yük bırakıldı, mavi kaldı

Kutu kırpma düzeltmesi işe yaradı: mavi hedef 0,2 s içinde doğrulandı ve **kırmızı yük** AUX3/11 üzerinden bırakıldı (`kirmizi: ACK_ACCEPTED`, 67,5 s). Kayıt `artifacts/servo-bench-20260911/quick-flight-20260911-red-released.jsonl`, sortie `20260911T081342Z-hizli-imx708`.

Mavi yük bırakılamadı. 80,7 s'de kırmızı hedefe duruş istendi; 83,5–86,4 s arasında hedef kesintisiz YOLO+OpenCV doğrulamalı (fill 0,98–1,00) ve hız 0,04–0,27 m/s iken doğrulama zaman aşımına uğradı. Neden hedef kaybı değil, **kutu örtüşmesi zincirinin kopması**: fren sırasında kırmızı hedef 0,6 s içinde kadrajın altından üstüne kaydı (y 0,63→0,02), ardışık kareler arası IoU 0 oldu ve `quick_iou=0,25` eşiği tutmadı. `selected_box` eski konumda donunca duruştan sonraki sabit hedef bir daha eşleşmedi.

Düzeltme `controller.py`: hızlı görevde **yalnız STOPPING aşamasında** ve seçilen renkten tek aday varsa hedef yeniden yakalanır (`verify_hold` sıfırlanır). Duruştan sonra (VERIFYING) kural katı kalır; sıçrayan hedef hâlâ reddedilir. Yeni regresyon testi gerçek uçuş kutu dizisini kullanıyor ve düzeltme olmadan başarısız oluyor. Yerelde 271 test, Pi'de 229 test geçti. Yedek `runtime/before-reacquire-20260911/`.

Sonraki uçuş için: kırmızı yük fiziksel olarak yeniden takılmalı ve profile yeni `sortie_id` yazılmalı; ledger'da bu sortie için kırmızı kaydı var. Görev/kayıt kapalı; servo/ARM/mod komutu verilmedi.

## En güncel — 11 Eylül hızlı uçuş: kırmızı yük neden bırakılmadı

Uçuşta mavi yük kırmızı hedefe doğru şekilde bırakıldı (`mavi: ACK_ACCEPTED`, 64,5 s); kırmızı yük hiç komut almadı. Kayıt `artifacts/servo-bench-20260911/quick-flight-20260911-blue-released.jsonl` (Pi: `runtime/competition/quick-imx708/competition-40d6cabcc9a14a5eb354d87ae3bd23c9.jsonl`, sha256 `dc8682ea…7cb04`). Akış: 46,3 s mavi hedefte GUIDED duruş, 49,7 s VERIFYING, **52,7 s doğrulama başarısız/revoke**; 61,5 s kırmızı hedefte duruş, 64,5 s mavi yük; 76,0 s PILOT_CONTROL (LOITER) ile oturum kapandı, ikinci şans olmadı. Sorun servo/PWM değil: kırmızı yük komutu hiç üretilmedi.

Kök neden iki katı kadraj kuralı. Mavi hedefin YOLO kutusu üst kenarda `ymin ≈ -0,010` (yaklaşık 7 piksel taşma) geliyordu; `0 <= v <= 1` şartı 46 mavi tespitin 38'ini komple attı (kırmızıda yalnız 2). Kalan kareler de OpenCV tarafında `min_border_px=12` ile eleniyordu, çünkü renk bölgesi üst kenara değiyordu. Bu yüzden 0,1 s / 3 kare YOLO+OpenCV doğrulaması hiç oluşmadı.

Düzeltme: yeni `safak_gorev2/competition/bbox.py` içindeki `clamp_bbox` kutuyu [0,1] aralığına kırpar, alanının en az %60'ı kadraj içinde değilse reddeder; `vision.py` ve `runtime.py` bu kırpmayı kullanır. `ColorDetector.detect` artık `border_px` alır: hızlı görevde kenar payı uygulanmaz, ana görevde metrik ölçüm için `min_border_px` korunur. Eski uçuş kutuları yeni kodla yeniden geçirildiğinde mavi kabul 8/46 → 46/46, kırmızı 35/37 → 37/37. Yerelde 270 test geçti (5 atlandı), Pi'de 228 test geçti. Yedek `runtime/before-bbox-clamp-20260911/`. Görev/kayıt kapalı; servo/ARM/mod komutu verilmedi. Bu düzeltme yalnız kod/test doğrulamasıdır, yeni uçuşla saha kabulü yapılmadı.

## En güncel — 11 Eylül ilk ana uçuş teşhisi

Ana merkezleme uçuşu ve kaydı kullanıcı isteğiyle temiz kapatıldı. Kamera/Hailo çalıştı ve hedefler görüldü; iki kez AUTO→GUIDED duruş oldu. Tespit anında hız3–3,7m/s, canlı `WPNAV_SPEED=1000cm/s`; durma yaklaşık3s sürerken hedef/geometri sürekliliği kayboldu.0,5s doğrulama tamamlanmadığı için INTERCEPT/servo aşaması hiç başlamadı. Mission Planner bağlantısızlığı neden değil. Kaydedici kamera hazır olmadan başladığı için çıktı ve video yok. Düzeltmeler Pi'de: kaydedici30s kaynak bekler; preflight `WPNAV_SPEED` değerini1–200cm/s dışında reddeder; center duruş metni düzeltildi; JSONL geometri diagnostics içerir.102 ilgili Pi testi geçti. FC hızı hâlâ1000, değiştirilmedi; yeniden uçuş öncesi150cm/s kararı uygulanmalı. Görev/kayıt kapalı, payload ledger'da bu sortie için servo kaydı yok.

## En güncel — 11 Eylül ana merkezleme uçuş öncesi

Kullanıcı ana merkezlemeyi seçti. IMX708 CAM1'de geçici sürücü yoklamasıyla sensör kimliği `0x0301` verdi; otomatik algılama çalışmadığından `/boot/firmware/config.txt` içine kalıcı `dtoverlay=imx708` eklendi. Reboot sonrası gerçek kamera/Hailo/OpenCV 20 saniye 1015 kare/50,37 FPS/stale0/hata0 ve entegre observe yaklaşık49,9 FPS. Ana profil Pixhawk'ın doğrulanmış `...CubeOrange...-if00` by-id yoluna sabitlendi. Dünkü rota digest'i eş; yerde DISARM/STABILIZE, GPS14/HDOP0,83, EKF831, 16,293V/%99. RC sağlıksız/UNKNOWN; uçuş öncesi kumanda-alıcı/AUTO slotu doğrulanmalı. Servo parametreleri mavi9 FUNCTION58/MIN1100/MAX1900, kırmızı11 FUNCTION0/MIN800/MAX1900 olarak salt okunur doğrulandı; komut gönderilmedi. `sortie_id` yükler yeniden takılınca oluşturulmalı. İki yük sonrası bulunduğu yerde iniş nedeniyle yazılım artık `mission.direct_land_corridor_checked=true` saha onayını zorunlu tutar; mevcut null. IMX708 sonsuz odak kalibrasyonu yaklaşık ve saha metrik kabulü yok. Uçuş süreci kapalı.

## Son durum — 11 Eylül servo entegrasyonu Pi'de, kamera bekleniyor

Servo kodu/profilleri Pi'ye yüklendi; 13dosya hash doğrulandı, **100 ilgili Pi testi geçti**. Önceki yerel247+9test ve gerçek MAVLink servo komutlu hex SITL geçti: `artifacts/competition-sitl/20260911T093947-quick-complete/result.json`; iki ACK_ACCEPTED ve LAND/DONE. Yedek `runtime/before-servo-integration-20260911/`.

Kullanıcı rota dünküyle aynı dedi; canlıFC DISARM iken geri okundu ve digest54b32d9b...747fe birebir eşleşti. TAKEOFF10m, tarama2–8 hepsi10m, LAND9. Ana/ana-imx708/hızlı genel profillerine doğrulanmış rota/kapı/poligon alanları işlendi; sortie_id henüznull, yeni yükleme/oturum seçilmedi. Yeni kamera montajı varsayılmadı. Uçuş uygulaması açılmadı; servo/ARM/mod/rota komutu bu tur yok.

Pi kamera 'No cameras available'. /boot/firmware/config.txt içinde aktif dtoverlay=imx219 bulundu; imx219 chip-id -121 hatası vardı. Eski satır yedeklenip yorumlandı, camera_auto_detect=1 korundu, yerde/DISARM ile Pi reboot edildi. Son envanter yine hiçkamera yok; bootta hiçbir imx sensörü algılanmıyor. Başka overlay zorlanmadı; kullanıcıdan güç kapalıyken IMX708 kablo/mandal kontrolü istendi. boot yedeği runtime/before-servo-integration-20260911/boot-config-before-imx708.txt. IP172.20.10.6 aynı. Ana/hızlı seçimi soruldu, yanıt bekleniyor. Önceki kamera görülmüyor/dağıtım bekliyor notlarında dağıtım artık tamamlandı, kamera sorunu sürüyor.

## 11 Eylül — tezgâhta iki yük bırakma doğrulandı, süreli servo entegrasyonu

Kullanıcı mavi AUX1/9=1800us ve kırmızı AUX3/11=yaklaşık0,3s800us→1500us ile iki yükün düştüğünü, ayrıca kırmızının1500us ile durduğunu doğruladı. IMX708 uçuş testi için koda eklenmesini istedi. Beş görev profilinde bu eşleme kaydedildi; IMX708 profilleri actuator=servo, Arducam simulated olarak kaldı. Mavi beklenen FUNCTION58 (tezgâhta okunan RCIN8), kırmızı FUNCTION0; işlev kontrolü bu kesin değerlerle yapılır. Kırmızı MIN800 daha önce FC'ye yazıldı; yeni entegrasyon FC parametresi yazmaz. Her iki servo bench_verified=true; fiziksel uçuş/isabet doğrulaması değildir.

Servo tanımına pulse_s/neutral_pwm/function eklendi. Kırmızı800 ACK+çıkış kanıtı alınsa bile durum SENT kalır; bağlantı döngüsündeki0,3s sonlandırma1500 gönderir, yalnız1500 ACK+çıkış da doğrulanınca ACK_ACCEPTED olur. Eksik ilk kanıt, zaman aşımı/ret UNCERTAIN veya REJECTED üretir; otomatik tekrar yok. Pilot devri veya kontrol döngüsü durması nötr komutunu engellemez; temiz kapanışta etkin darbe nötrlenir. Süreç SIGKILL/güç/USB kaybında yazılım fiziksel duruş garantisi veremez. İki yük sonrası LAND korunur.

Ortak MavlinkLink'e boş tick/shutdown kancaları eklendi; eski Controller/geometri değişmedi. Mavlink özgün kaynağı `archive/legacy-options/mavlink_io-before-servo-pulse.py.txt` altında hash eşlemesine alındı. Yeni9servo testi geçti; önceki tüm247test/5atlama da geçti.

Son Pi kamera envanteri **No cameras available**: IMX708 görülmüyor. Mevcut ana profillerde sortie/rota/kapılar boş; 10Eylül hızlı saha rotası tarihli aday, yeni uçuşa otomatik onaylanmadı. Uçuş uygulaması başlatılmadı. Kamera takılması, ana/hızlı seçimi ve güncel rota doğrulaması bekliyor.

Kullanıcı yükleri sıfırladığını söyleyip ikisini bırakmamızı istedi. Yeni açılışta yerde/DISARM doğrulandı; sırasıyla mavi AUX1/9'a1800us, kırmızı AUX3/11'e yaklaşık0,3s800us sonra1500us gönderildi. Üç komut ACK kabul; son çıkışlar9=1800,10=0,11=1500. Bu adımda FC parametresi yazılmadı, MIN11=800 okundu. İki yükün fiziksel düşüşü ve kırmızının1500'de durması henüz bilinmiyor; kullanıcı sonucu bekleniyor. Kanıt `artifacts/servo-bench-20260911/both-reloaded-1800-800.txt`; tekrar darbe betiği `red-aux3-800-repeat.py`. Süreçler kapandı. Görev profilleri hâlâsimulated/kırmızı10/null/false; test sonucu otomatik uçuş kabulü değildir.

Kullanıcı900us ile yükün uçta kaldığını söyleyip800 istedi ve kırmızı servonun sonsuz döndüğünü bildirdi. Model henüz bilinmiyor; sürekli dönüş tipi kullanıcı beyanı. Bu nedenle uzun süre800 tutmak yerine kısa darbe uygulandı: yerde/DISARM/FUNCTION0/MIN900/çıkış900 teyidiyle SERVO11_MIN900→800 kalıcı yazıldı/geri okundu; AUX3/11'e800us, yaklaşık0,3s sonra finally bloğunda1500us gönderildi. İki ACK kabul; son servo11_raw=1500. 1500 fiziksel duruşu veya yük düşüşü henüz doğrulanmadı. Kullanıcıya yükün düşüp düşmediği ve servonun durup durmadığı sorulmalı. Maviye komut yok. Kanıt `artifacts/servo-bench-20260911/red-aux3-800-pulse.txt`, betik aynı dizinde. Sürekli dönüş modeli doğrulanırsa görev bırakma kodu süreli sürüş/neutral gerektirir; mevcut tek PWM/ACK mekanizması otomatik kabul edilmemeli. Profiller hâlâ simulated/kırmızı10/null/false.

Kullanıcı1000us ile yükün hâlâ düşmediğini bildirip açıkça900us denemesini istedi. Tek seferlik betik taze yerde/DISARM, FUNCTION0, MIN1000 ve çıkış1000 teyidiyle yalnız SERVO11_MIN1000→900 kalıcı yazdı/geri okudu; AUX3/11'e900us tek komut gönderildi. Fiziksel sonuç bekleniyor. Maviye komut yok. Kanıt `artifacts/servo-bench-20260911/red-aux3-900.txt`, betik aynı klasörde; Pi runtime/before-land-servo-20260911. Bu açık deneme servo modelinin900us uygunluğunun teknik kanıtı değildir. Görev profilleri hâlâ simulated/kırmızı10/null/false; kalıcı AUX3 bırakma eşlemesi henüz yapılmadı.

Kullanıcı1050us adımını çok az buldu. Taze yerde/DISARM, FUNCTION0, MIN1050 ve çıkış1050 teyidiyle yalnız SERVO11_MIN1050→1000 kalıcı yazıldı/geri okundu; AUX3/11'e1000us tek komut ACK kabul ve çıkış1000 doğrulandı. Maviye komut yok. Fiziksel1000 sonucu bekleniyor. Daha düşük PWM öncesi servo model/izinli darbe aralığı ve mekanik kurulum bilinmeli; otomatik sınır genişletme yapma. Kanıt `artifacts/servo-bench-20260911/red-aux3-1000.txt`, tek seferlik betik aynı klasörde. İlk MIN1100, ara1050 ve son1000 kayıtlı. Görev profilleri hâlâ simulated/kırmızı10/null/false; bu fiziksel kabul sonrası düzenlenecek.

Kullanıcı kırmızı AUX3/1100us ile döndüğünü ama az olduğunu, sıfırlamadığını ve biraz daha hareket istediğini bildirdi. Yerde/DISARM ve servo11_raw=1100 doğrulanarak **kalıcı SERVO11_MIN1100→1050** yazıldı ve geri okundu; yalnız AUX3/11'e1050us bir defa gönderildi. ACK kabul ve servo11_raw=1050 doğrulandı; mavi9'a komut yok. Eski MIN1100 kanıtta kayıtlı, kendiliğinden geri değiştirme. Fiziksel1050 sonucu bekleniyor; görev profilleri hâlâ simulated, kırmızı10/null/false, AUX3 kalıcı eşlemesi henüz yapılmadı. Tek seferlik betik ve kanıt `artifacts/servo-bench-20260911/red-aux3-1050-once.py`, `red-aux3-1050.txt`; Pi betiği `runtime/before-land-servo-20260911/` içinde.

Kullanıcı kırmızının AUX3 olduğunu ve maviyle ters yöne hareket istediğini tekrar belirtti. Taze yerde/DISARM denetiminden sonra yalnız AUX3/11'e1100us gönderildi; ACK kabul, servo11_raw=1100 doğrulandı. Mavi9'a komut verilmedi (çıktısı1800). Fiziksel yön/yük sonucu bekleniyor; kanıt `artifacts/servo-bench-20260911/red-aux3-1100.txt`. Kalıcı görev profilleri henüz kırmızı10/simulated/null/false; AUX3 fiziksel kabul sonrası güncelleme gerekli.

Kullanıcı kırmızı AUX2'de hâlâ hareket olmadığını bildirip servoyu AUX3'e taşıdı ve deneme istedi. Bench betiğine kanal11 eklendi/Pi'ye aktarıldı. Taze yerde/DISARM, SERVO11_FUNCTION=0, MIN1100/MAX1900 okundu; yalnız AUX3/11'e1800us gönderildi. ACK kabul ve servo11_raw=1800 doğrulandı. Fiziksel sonuç bekleniyor. Kanıt `artifacts/servo-bench-20260911/red-aux3-1800.txt`. Görev profilleri henüz kırmızı10 olarak kalıyor; AUX3 fiziksel kabul sonrası kalıcı eşleme güncellenmeli.

Kullanıcı son iki kanal denemesinde mavinin düştüğünü doğruladı; kırmızı servonun takılı olmadığını fark edip tekrar deneme istedi. Önceki kırmızı hareketsizliği PWM/yön başarısızlığı olarak yorumlanmamalı. Taze DISARM/ON_GROUND ile yalnız AUX2/10'a tekrar1800us gönderildi; ACK kabul ve servo10_raw=1800. Fiziksel kırmızı sonucu bekleniyor. Kanıt `artifacts/servo-bench-20260911/red-1800-connected.txt`; maviye bu adımda komut yok.

Son kullanıcı iki servonun da sabit olduğunu bildirip ikisine de komut istedi. Taze DISARM/ON_GROUND ile sırayla AUX1/9 ve AUX2/10'a 1800us birer kez gönderildi. Her iki ACK kabul; son servo9_raw=1800, servo10_raw=1800. Fiziksel hareket/yük sonucu henüz bilinmiyor. Kanıt `artifacts/servo-bench-20260911/both-1800.txt`. Önceki kırmızı1800 için kullanıcı hareket yok dedi.

**Son fiziksel geri bildirim:** Kullanıcı mavi1800us ile yükün düştüğünü, kırmızı1100us ile hiç hareket olmadığını doğruladı. İki servoyu sıfırlayıp güç verdiğini bildirdi. Sonraki taze hex/DISARM/STABILIZE/ON_GROUND kontrolünde servo9/10 çıktıları0/0 idi; yalnız kırmızı AUX2/10'a1800us gönderildi, ACK kabul ve servo10_raw=1800 doğrulandı; servo9_raw=0 kaldı. Kırmızı1800 yön/açı/yük sonucu bekleniyor. Betik kapandı. Kanıt `red-1800.txt`, kullanıcı sonuçları `user-feedback.json`; mavi1800 bırakma adayı fiziksel olumlu, profiller henüz simulated/null/false.

### Servo denemesi devamı — mavi1800 / kırmızı1100

Kullanıcı: mavi AUX1 ilk1500us denemesinde doğru yönde yaklaşık30–45° döndü, yeterli değil. Sonraki mavi1800us komutu kesilen tur sırasında **gerçekten gönderildi**, ACK kabul ve servo9_raw=1800 doğrulandı; fiziksel açı/yük sonucu henüz yok. Kullanıcı güç varken başlangıca elle getiremediğini söyleyip kırmızı denemesini istedi. Yeni yerde/DISARM kontrolüyle yalnız AUX2/10'a1100us gönderildi; ACK kabul ve servo10_raw=1100 doğrulandı. Son çıkışlar mavi1800/kırmızı1100us. İki betik de bitti/seri bağlantıyı kapattı. Sıfırlama, ARM/mod/FC parametre yazımı yapılmadı. Kırmızının yön/açı/yük düşüşü bekleniyor; profillerde bench_verified=false/release_pwm=null kalır. Kanıtlar `artifacts/servo-bench-20260911/blue-1800.txt`, `red-1100.txt`.

## 11 Eylül — LAND Pi’ye yüklendi; servo eşlemesi değişti, ilk mavi deneme

Kullanıcı servo testini şimdi açıkça istedi ve eşlemeyi değiştirdi: **mavi yük AUX1/9, kırmızı yük AUX2/10**. Başlangıçları fiziksel 0°, istenen hareket yaklaşık 90°; AUX1 sağa, AUX2 sola kullanıcı beyanı. Eski kırmızı9/mavi10 notları artık tarihli geçmiş. Mavi hedefe kırmızı, kırmızı hedefe mavi yük kuralı değişmedi. Beş görev profilinin yalnız kanal eşlemesi Pi/Mac üzerinde güncellendi; `actuator=simulated`, `release_pwm=null`, `bench_verified=false` korunur.

Pi `furkan@172.20.10.6`, repo `/home/furkan/Desktop/safak-gorev2-quad`. LAND controller/panel ve test dosyaları yedek alınıp hash doğrulanarak yüklendi. Pi’de 69 ilgili test geçti. Eski Pi arşiv eşlemesi önceki kamera revizyonunun 3 kaynak kopyasını göstermiyordu; özgün hash eşleşen arşiv kopyaları/eşleme de aktarıldı. Yedek `runtime/before-land-servo-20260911/`, kanıt `artifacts/servo-bench-20260911/`. Kamera/görev/uçuş başlatılmadı; gerçek ARM/mod/rota/FC parametresi yazılmadı.

Cube if00/ttyACM0 tek okuyucuyla hex/DISARM/LOITER/ON_GROUND doğrulandı. SERVO9_FUNCTION=58, SERVO10_FUNCTION=60 (RC giriş geçişleri), MIN/MAX=1100/1900, TRIM=1500, REVERSED=0; başlangıç çıkışları 982/1495 us. Parametreler değiştirilmedi. Manuel deneme betiği `scripts/servo_bench.py` her komut öncesi taze yerde/DISARM ve kanal işlev/sınır kontrolü yapar; yalnız açık channel+pwm ile bir kez DO_SET_SERVO yollar. ArduPilot’un kabul ettiği Disabled/RC geçiş işlevlerine izin verir; görev yazılımının servo için FUNCTION=0 şartı gevşetilmedi.

**İlk deneme: AUX1/9 mavi → 1500 us tek komut, ACK kabul ve servo9_raw=1500 doğrulandı. AUX2’ye komut yok.** Fiziksel sağ/sol, açı ve yük düşüşü kullanıcının yanıtını bekliyor; bench kabulü yapılmadı. Sıradaki adım bu geri bildirime göre devam; yeniden komut göndermeden taze durum oku. `blue-1500.txt` kanıtı. Betik bağlantıyı kapattı; otomatik tekrarlama/geri döndürme yok.

## 11 Eylül — iki yük sonrası doğrudan LAND

Son kullanıcı isteği: mavi ve kırmızı yük komutları da onaylandıktan sonra ana ve hızlı görev doğrudan **bulunduğu yerde LAND** ister. İlk yükte eski tarama irtifası/aynı waypoint dönüşü korunur. İkinci yükte yükselme, AUTO dönüşü, kalan rota veya bitiş kapısı yoktur. `REQUEST_LAND` taze LAND telemetrisini bekler, `LANDING` hız sahipliğini bırakır; yerde DISARM ile `DONE`. Onaylanmayan yük erken inişi tetiklemez. Pilot devri kilidi ve LAND geçişi zaman aşımı korunur. Eksik yükle tarama biterse eski AUTO/LAND rotası devam eder.

Bu değişiklik yereldedir; Pi'nin son IP'si 172.20.10.6 ve görünen .3 SSH zaman aşımı, .2 bağlantı reddi verdi; bu tur dağıtım yapılmadı. Kamera ayarı/servo/gerçek MAVLink açılmadı. Servo hâlâ simulated/PWM null; ACK/PWM fiziksel ayrılma kanıtı değildir. **247 yerel test geçti/5 atlandı; ana+hızlı 2 hex SITL geçti.** Güncel test kanıtı `artifacts/land-after-payloads-20260911/` içinde; önceki test raporları eski rota bitiş davranışını doğrular.

## 11 Eylül — ana IMX708/Arducam yerel revizyonu

Önce HANDOFF en üstünü ve docs/competition/IKI_KAMERA_KABUL.md oku. Ana/hızlı stratejiler korundu; ayrı ana-imx708/ana-arducam profilleri, kamera/backend ve kayıt kimliği kontrolü, yalnız mission_digest rota/resume. Arducam kimlik/kalibrasyon/montaj null; v4l2-observe uçuş/bırakma kapalı. IMX708 yaklaşık odak aktarımı kabul edilmedi. Servo simulated/PWM null; gerçek araç komutu yok. 233 yerel geçti/5 atlandı, 7 hex SITL geçti. Pi SSH son IP'de reddedildi; yeni revizyon dağıtılmadı/gerçek kamera probe yok. Önceki tarihli canlı ölçümler yeni revizyon kabulü değildir.

## 8 Eylül teknik kontrol — iki görevde sonsuz odak, servo ertelendi

Önce `docs/HANDOFF.md` en üst güncellemesini ve `TEKNIK_KONTROL.md` oku. Kullanıcı iki görevde sonsuz odağı açıkça istedi: manuel LensPosition=0, 50 FPS, tam IMX708 sensör modu Pi'ye aktarıldı. Ana IMX219 bağı kaldırıldı; eski 40 dama karesinden gelen matris `camera.imx708-infinity-approx.json` içinde yaklaşık kullanılıyor. Çekim odağı0,1063; sonsuz odakta yeniden kalibrasyon/metrik kabul yok, özgün aday korundu. 98 ilgili yerel test geçti; canlı ana49,86/hızlı50,03FPS, hata yok; görüntü yakın parçalarla kapalı, uzak netlik doğrulanmadı. MAVLink/servo/uçuş açılmadı. **Kullanıcı servo işini sonraya bıraktı; şimdi servo çalıştırma.** Teknik rehber ve klasör düzeni yapıldı; eski `anlık test/` videoları `archive/field-videos-20260907/`, eğitim ZIP'i `finetune_dataset/` altında. Kanıt `artifacts/camera-review-20260908/`. Aşağıdaki eski ana-IMX219/odak0,1 notları tarihli geçmiş.

## 8 Eylül — en yeni karar:50FPS, YOLO veya OpenCV ile ara; ikisiyle doğrula

Kullanıcı planı açıkça uygulatıp50FPS istedi. Ana/hızlı profiller50FPS. OpenCV YOLO kutusu olmadan tüm görüntüde renk+dörtgen arar; YOLO **veya** OpenCV kararlı adayı duruş başlatır. Duruştan sonra aynı kare/renk/bölgede YOLO **ve** OpenCV zorunlu; yalnızrenk bırakmaz. Ana merkezleme de ortak kanıt kullanır. Yeni kod ve önceki180°/FRD[0.11,0,0.05] montajı Pi'ye dağıtıldı. Yerel209test/5atlama, ana+hızlıhexSITL tam görevleri geçti; canlıPi kamera/Hailo/OpenCV testinde50,03FPS/2151işlenmişkare/hata0. Test sonunda kamera/görev/panel kapalı; gerçek uçuş/servo/MAVLink başlatılmadı. AnaIMX219 kalibrasyonbağı hâlâ açık; yeni renk eşikleri gerçekbrandada doğrulanmadı. Ayrıntı `docs/HANDOFF.md`, `docs/competition/TESTLER.md`, `artifacts/fusion-20260908/`. Aşağıdaki eski30FPS/yalnızAI/“montaj aktarılmadı” ifadeleri tarihli geçmiş.

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
