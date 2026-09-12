# Ana görev ve hızlı görev

## 12 Eylül — kısa tespit boşluklarında etiket korunuyor

OpenCV renk/dörtgen araması motion blur veya ani yaw/pitch/roll nedeniyle 1–3 kare hedefi kaçırdığında etiket artık düşmüyor: renk başına sabit hızlı bir Kalman izi kısa boşluğu köprülüyor, tarama sayacı sıfırlanmıyor. Uzun kayıpta (varsayılan 8 kare) iz gerçekten bırakılıyor. **Tahmin uçuş kanıtı değildir:** köprülenen aday `source='tracked'` / `color_verified=False` olduğu için duruş sonrası doğrulama, merkezleme ve yük bırakma yollarına mevcut `corroborated` koşuluyla zaten giremiyor; gerçek tespitin `bbox` alanı değişmiyor, PnP ham ölçümü görmeye devam ediyor. Sabit kanat (Albatros) kaynaklı "yaklaş → geç → en iyi detection'ı kilitle" mantığı alınmadı; döner kanat hover, geri gidiş, yana kayma ve yaw dönüşünde yön varsayımı taşımaz.

Saha anahtarı: profil JSON'undaki `tracking.enabled`. `false` yazmak anında eski davranışa döndürür. Ayrıntı, parametreler ve debug: [Hedef takibi](HEDEF_TAKIBI.md).

## 11 Eylül — tezgâhta iki yük bırakma doğrulandı, süreli servo entegrasyonu

Kullanıcı mavi AUX1/9=1800us ve kırmızı AUX3/11=yaklaşık0,3s800us→1500us ile iki yükün düştüğünü, ayrıca kırmızının1500us ile durduğunu doğruladı. IMX708 uçuş testi için koda eklenmesini istedi. Beş görev profilinde bu eşleme kaydedildi; IMX708 profilleri actuator=servo, Arducam simulated olarak kaldı. Mavi beklenen FUNCTION58 (tezgâhta okunan RCIN8), kırmızı FUNCTION0; işlev kontrolü bu kesin değerlerle yapılır. Kırmızı MIN800 daha önce FC'ye yazıldı; yeni entegrasyon FC parametresi yazmaz. Her iki servo bench_verified=true; fiziksel uçuş/isabet doğrulaması değildir.

Servo tanımına pulse_s/neutral_pwm/function eklendi. Kırmızı800 ACK+çıkış kanıtı alınsa bile durum SENT kalır; bağlantı döngüsündeki0,3s sonlandırma1500 gönderir, yalnız1500 ACK+çıkış da doğrulanınca ACK_ACCEPTED olur. Eksik ilk kanıt, zaman aşımı/ret UNCERTAIN veya REJECTED üretir; otomatik tekrar yok. Pilot devri veya kontrol döngüsü durması nötr komutunu engellemez; temiz kapanışta etkin darbe nötrlenir. Süreç SIGKILL/güç/USB kaybında yazılım fiziksel duruş garantisi veremez. İki yük sonrası LAND korunur.

Ortak MavlinkLink'e boş tick/shutdown kancaları eklendi; eski Controller/geometri değişmedi. Mavlink özgün kaynağı `archive/legacy-options/mavlink_io-before-servo-pulse.py.txt` altında hash eşlemesine alındı. Yeni9servo testi geçti; önceki tüm247test/5atlama da geçti.

Son Pi kamera envanteri **No cameras available**: IMX708 görülmüyor. Mevcut ana profillerde sortie/rota/kapılar boş; 10Eylül hızlı saha rotası tarihli aday, yeni uçuşa otomatik onaylanmadı. Uçuş uygulaması başlatılmadı. Kamera takılması, ana/hızlı seçimi ve güncel rota doğrulaması bekliyor.

## 11 Eylül — ana görev için iki kamera

Ana IMX708 ve Arducam profilleri ayrıldı; ana center/PnP/alçalma ve hızlı merkezlemesiz akış korunur. Yeni profiller simulated, PWM null. Arducam kimliği/kalibrasyonu/montajı bilinmiyor; `v4l2-observe` yalnız gözlem, uçuş ve bırakma kapalı. IMX708 0 odakta yaklaşık matris kullanır; focus_transfer_verified ve physical_distance_verified false. Kamera kimliği/backend ve kayıt profili eşleşmesi denetlenir; rota ve resume yalnız mission_digest() kullanır.

Yeni yerel kaynaklar Pi'ye dağıtılmadı. Son bilinen IP SSH bağlantısını reddetti; canlı kamera kabulü yok. Servo ertelendi. Ayrıntılı profiller, kayıt komutu, değişen dosyalar ve fiziksel kabul ölçütleri: [İki kamera kabulü](IKI_KAMERA_KABUL.md). Testler [TESTLER](TESTLER.md) içinde.


Tek uygulama: `safak_gorev2.competition.main`. Kullanıcı seçimi yalnız `--task ana` veya `--task hizli`. İki görev de **MOSSE kullanmaz**.

## Ortak başlangıç

1. AUTO'nun izinli tarama bölümünde YOLO veya OpenCV renk+dörtgen adayı en az3 bağımsız kare ve0,10s görülür. OpenCV, YOLO kutusu olmadan da görüntünün tamamını tarar.
2. Kesilen waypoint kaydedilir; GUIDED moduna geçiş istenir.
3. GUIDED doğrulanınca sıfır hız komutu gönderilir. Araç yatayda≤0,20m/s, düşey hız/eğim sınırları içinde en az0,30s kalmalıdır.5s içinde duruş doğrulanmazsa görev LOITER devriyle iptal edilir.
4. Yalnız duruştan **sonraki taze kareler** hedef doğrulamasına katılır. Tekrarlanan kare süre kazandırmaz.
5. Durduktan sonra aynı renk/aynı bölgede **YOLO + OpenCV birlikte** doğrulamalı. İki yöntemin farklı karelerde veya farklı nesnelerde tespit üretmesi kabul edilmez. Renk adayı tek başına yük bıraktırmaz.

**0,10s fiziksel duruş süresi değildir.** Mod geçişi ve frenleme ek mesafe/süre alır. Durmak için de GUIDED kullanılır; bu mod yalnız hedefe gitmek için değildir.

## Seçenek farkı

| | Ana görev (`ana-gorev.json`) | Hızlı görev (`hizli-gorev.json`) |
|---|---|---|
| Durduktan sonra doğrulama | Aynı bölgede YOLO + OpenCV + köşe/PnP;≥6kare ve0,50s | Aynı bölgede YOLO + OpenCV;≥3kare ve0,10s |
| Merkezleme | Var | Yok |
| Alçalma | Var, aday profilde9m kamera yüksekliği | Yok, mevcut irtifada kalır |
| Bırakma | Kararlı merkez/irtifa ve taze hedef | Duruş ve taze kısa hedef doğrulaması |
| İlk yük sonrası | Tarama irtifasına çık, aynı waypoint ile AUTO | İrtifa komutu vermeden aynı waypoint ile AUTO |
| İkinci yük sonrası | Tekrar yükselmeden doğrudan LAND | Doğrudan LAND |

İki görevde de3s içinde hedef doğrulanmazsa yük korunur, aynı waypoint'e dönülür. Aynı renge5s yeniden durma uygulanmaz. Kamera/telemetri kesilmesi veya pilot müdahalesi “yanlış hedef” sayılıp rotaya dönülmez; kontrol bırakılır. Pilot LOITER'a geçtiğinde aynı oturumda kendiliğinden tekrar devralınmaz.

**Hızlı görev hedefin üstünde olmayı ölçmez.** Kadrajın kenarındaki doğru hedef de kısa doğrulamayı geçebilir; isabet belirsizliği ana görevden yüksektir. Ek bir görüntü merkezi şartı eklenmedi. Mavi hedef→kırmızı yük, kırmızı hedef→mavi yük. Tek seferlik kalıcı kayıt sayesinde aynı yüke otomatik ikinci bırakma yok.

**11 Eylül son karar: İki yük komutu da onaylanınca doğrudan LAND waypointine uçulur.** Kalan tarama waypointleri atlanır: GUIDED'deyken `mission_current` ile rotanın LAND sırası seçilir (`SELECT_LAND`), sıra telemetride doğrulanınca AUTO'ya devredilir (`HANDOFF_LAND`), AUTO doğru sırada başladığında `LANDING` olur ve hız komutu sahipliği bırakılır. Yanlış sırada AUTO başlarsa görev iptal edilir. MAVLink katmanı `mission_current` komutunu yalnız GUIDED'de ve yalnız rotanın LAND sırası için uygular. Yeniden yükselme, AUTO dönüşü, kalan waypoint veya bitiş kapısı geçişi yoktur. LAND onayı zaman aşımında görev iptal edilir; rotaya dönülmez. Pilot müdahalesi kalıcı devralma kilidini korur. Yerde DISARM doğrulanınca iki yük tamamlandıysa `DONE`; eksik yük varsa `INCOMPLETE` olur. İki yük tamamlanmadan tarama biterse eski AUTO bitiş/LAND rotası sürer. Servo ACK/PWM fiziksel ayrılma kanıtı değildir; simulated aktüatörde iki temsili bırakma da aynı iniş davranışını tetikler.

## Kullanılan kütüphaneler

| Kütüphane | Görevi |
|---|---|
| Picamera2 / libcamera | Kamera, pozlama ve odak |
| HailoRT + TAPPAS / GStreamer (`gi`) | HEF üzerinden YOLO çıkarımı |
| OpenCV (`cv2`) | Görüntü işlemleri; ana görevde köşe ve PnP |
| NumPy | Sayısal hesaplar |
| pymavlink | Pixhawk telemetrisi, mod/hız/servo komutları |
| Flask + Waitress | Salt okunur panel |
| SQLite (Python `sqlite3`) | Tek seferlik yük kayıtları |
| pytest | Yerel testler |

DroneKit ve MOSSE uçuşta kullanılmaz. MOSSE deney dosyası yalnız ayrı dosya analizi aracıdır.

## Kod nereden okunur?

- `main.py`: iki görev seçimi, başlangıç, panel.
- `controller.py`: `begin_stop` → `stop_and_verify` → ana görevde `INTERCEPT`, hızlıda `request_release` → ilk yükte rota dönüşü; ikinci yükte `SELECT_LAND`/`HANDOFF_LAND`/`LANDING`.
- `vision.py`: AI adayları; ana görev için ayrıca geometri. Hızlı görev kalibrasyon yüklemez.
- `link.py`: MAVLink gönderimi; hızlı görevde mod/hız/irtifa/RC kontrollerini bırakma anında yeniden yapar.
- `runtime.py`: kamera, karar, panel ve kayıt döngülerini bağlar.
- `route.py`, `payload.py`: onaylanan rota ve tek seferlik yük defteri.

Bunların tamamı `safak_gorev2/competition/` altında. Ortak eski `controller.py` ve `geometry.py`, ana merkezin hesap yordamları olarak kalır; ayrı eski uçuş seçeneği değildir. Eski quad girişi donanım açmadan hata verir. Tarihli dosyalar `archive/legacy-options/` altında çalıştırılmayan `.txt` kopyalarıdır.

## Komutlar

Proje klasöründe, Pi'nin Hailo Python ortamıyla yalnız dosya kontrolü:

```bash
python -m safak_gorev2.competition.main --task ana --check
python -m safak_gorev2.competition.main --task hizli --check
```

Gözlem için bunlardan **birini** seçin:

```bash
python -m safak_gorev2.competition.main --task ana --mode observe
python -m safak_gorev2.competition.main --task hizli --mode observe
```

Gözlemde kamera/model/panel çalışır, uçuş ve yük komutu gönderilmez. Panel `http://PI_IP:8081/`. Kayıtlar `runtime/competition/center-imx708/` veya `runtime/competition/quick-imx708/`; iki görev aynı `runtime/competition/payload-ledger/` yük defterini paylaşır. Mevcut kaydedici ayrı terminalde `python -m safak_gorev2.record --config config/ana-imx708.json --panel-url http://127.0.0.1:8081` (ana) veya `--config config/hizli-gorev.json --panel-url http://127.0.0.1:8081` (hızlı) ile açılabilir. Görev kayıtları ile video kaydedici ayrı süreçlerdir.

Kamera isteği iki profilde **50 FPS**. Panel JPEG üretimi8FPS, tarayıcı yenilemesi yaklaşık4Hz, ayrı panel kaydı8FPS; bunlar kamera/çıkarım FPS'i değildir. Panelde “İşlenen FPS / kamera isteği” ayrı gösterilir. Uçuş videosundaki düşük akıştan çıkarımın aynı hızda olduğu sonucuna varılmaz.

Hailo ortamı henüz açılmadıysa:

```bash
bash scripts/run_pi.sh /tam/yol/setup_env.sh --task hizli --mode observe
```

Gerçek uçuş modunu seçmek için `--mode flight` kullanılır; eksik alanlar tamamlanmadan başlamaz. `actuator=simulated` fiziksel bırakma yapmaz, **flight modunda gerçek navigasyon yapar**. Özel saha profili için `--task` yerine `--config /tam/yol/profil.json` kullanılabilir; yalnız `center` veya `quick` stratejisi kabul edilir, `sighting` kaldırıldı.

## Saha profilinde tamamlanacaklar

- Gerçek USB cihazı ve hexacopter kimliği/sürümü/parametreleri.
- `sortie_id`: yüklerin takıldığı uçuşa özel kimlik; görev değiştirince aynı kalır. Yeniden yüklemeden kimliği değiştirerek ikinci bırakma açılmaz.
- `mission_fingerprint`, `search_start_seq`, `search_end_seq`: FC'den geri okunmuş, tarama aralığı belirlenmiş rota.
- `entry_gates`, `finish_gate`, `flight_polygon`, `route_reviewed`: sahada tanımlı giriş/bitiş ve uçuş alanı. Konumlar uydurulmaz. Rota için AUTO TAKEOFF, WAYPOINT ve son LAND gerekir; program rota yüklemez.
- Servo tezgâh denemesi başladı; görev profillerinde simulated korunur. İleride ayrı fiziksel kabul yapılırsa `actuator=servo`, yüklerin ölçülmüş `release_pwm` değerleri ve `bench_verified=true`. 11 Eylül yeni eşleme: AUX1/mavi yük=çıkış9, AUX2/kırmızı yük=çıkış10. İlk mavi1500us denemesi ACK/PWM kabul edildi; fiziksel sonuç bekleniyor. Derece bilgisi PWM sayısı değildir. FC'de işlev0/MIN/MAX okuması gerekir. ACK+PWM fiziksel ayrılma/isabet kanıtı değildir.
- Ana görev: mevcut IMX708'in odak/crop/montajına uygun kalibrasyon. **Ana temel profil hâlâ eski kalibrasyon adayını içeriyor; hazır sayılmaz.** 8 Eylül kullanıcı beyanıyla lens FRD ofseti `[0.11,0,0.05]` m ve yere bakan kameranın 180° ters montajı iki profile işlendi; gerçek görüntüyle yön kontrolü bekliyor.
- Hızlı görev: PnP/ofset gerekmez. Yeni `hizli-base.json` IMX708 tam sensör2304×1296,1280×720,manuel sonsuz odak0 ile başlar; bu son kamera gözleminden alınmış başlangıç tercihidir, güncel uzak netlik/uçuş doğrulaması değildir. Eski quad ofseti taşınmadı.

Boş alanlar ve dolu aday değerlerin ayrıntılı listesi: [EKSIKLER.md](EKSIKLER.md). Hızlı profilde montaj/ofset kaydı vardır; merkezleme yapmadığından isabet düzeltmesi olarak kullanılmaz.

8 Eylül: Hailo sürücüsünün `find_vma` uyarısı ayrı onarımla giderildi; kısa canlı çıkarım çalışıyor. Yeni50FPS/renk desteği ve önceki ters montaj revizyonu Pi'ye yedeklenerek dağıtıldı. Gerçek servo veya uçuş başlatılmadı. Yerel test/simülasyon ve gerçek FPS sonuçları `TESTLER.md` içinde. Önceki PCIe kopmasının kalıcı giderildiği veya gerçek hedef isabeti iddia edilmez.

## OpenCV adaylarının sınırları

Küçük görüntüde (en çok640piksel genişlik) HSV renk maskesi ve dörtgen araması yapılır. Renk başına en çok6aday bölge tam çözünürlükte yeniden denetlenir. Başlangıç HSV aralıkları mavi H90–135, kırmızı H0–12 veya168–179; S≥70/V≥35. Dörtgen renk doluluğu≥0,75, en/boy oranı≤2,5; kamera kenar/alan/doluluk sınırları korunur. Bunlar yeni montaj ve yarışma ışığında ölçülmüş kabul değerleri değildir.

YOLO/OpenCV aynı karede, aynı renk ve kutu IoU≥0,50 ile bire bir eşleştirilir. `source=opencv` adayında AI güveni `null` olur; renk doluluğu `color_fill` ayrı tutulur. `color_verified` ve kaynak panel/kayıtta görünür. Ana merkezleme boyunca da metrik hedef için ortak doğrulama gerekir. Kamera/Hailo akışı kesilirse mevcut iptal davranışı korunur; bu özellik Hailo arızasında bağımsız uçuş yedeği değildir.
