# Ana görev — iki kamera, 11 Eylül 2026

## Uygulanan davranış

**11 Eylül sonraki kullanıcı kararı:** Aşağıdaki eski tam rota davranışı değişti. İlk yük sonrası rota dönüşü korunur; ikinci yük komutu onaylanınca ana ve hızlı görev doğrudan bulunduğu yerde LAND ister. Ana tekrar yükselmez; kalan waypoint/bitiş kapısı izlenmez. Güncel akış [AKIS.md](AKIS.md) içindedir. Aşağıdaki testler bu değişiklikten önceki tarihli kanıttır.

Ana görev center olarak korunur: AUTO → YOLO veya OpenCV kararlı aday → GUIDED duruş → aynı kare/renk/bölgede ortak kanıt ve PnP (en az 6 bağımsız kare, 0,50 s) → merkezleme → alçalma → simulated bırakma → tarama irtifası → aynı waypoint ile AUTO ve kalan LAND. Hızlı görev en az 3 kare/0,10 s ortak doğrulamadan sonra durduğu irtifada simulated bırakır; PnP/merkezleme/alçalma yoktur. OpenCV arama genişliği en fazla 640 pikseldir; aday incelemesi tam çözünürlükte kalır.

Rota sözleşmesi ve resume eylemi artık yalnız `mission_digest()` kullanır. Profil alanının adı geriye uyum için `mission_fingerprint` kaldı. Genel `MissionPlan.fingerprint` reddedilir ve hata bunun nedenini açıklar. HOME değişikliği digest'i değiştirmez; waypoint/irtifa değişikliği değiştirir. Saha dosyasındaki eski onay başka ana profile kopyalanmadı; yeniden okuma/onay gerekir. `/dev/ttyACM0` yalnız 10 Eylül saha profilinde korundu, yeni ana profilde doğrulanmış portmuş gibi atanmadı.

## Kamera profilleri

| Alan | `ana-imx708.json` | `ana-arducam.json` |
|---|---|---|
| Temel | `competition-base.json` | `ana-arducam-base.json` |
| Kimlik/backend | imx708 / Picamera2 | null / v4l2-observe aday adaptörü |
| Boyut/FPS | 1280×720, 50 FPS isteği | 1280×720, 50 FPS yalnız istek; destek kanıtı yok |
| Sensör/odak | 2304×1296, manuel LensPosition=0 | null; IMX708 ayarları reddedilir |
| Kalibrasyon | camera.imx708-infinity-approx.json | calibration_file=null |
| Montaj | kullanıcı beyanı 180°, FRD [0.11,0,0.05] | yön/ofset null, yeniden ölçüm/onay gerekli |
| Metrik durum | yaklaşık/deneysel | PnP/merkezleme/uçuş/bırakma kapalı |
| Aktüatör | simulated; PWM null | simulated; PWM null |

`--task ana` mevcut `ana-gorev.json` üzerinden aynı IMX708 temelini kullanır. Yeni profiller üçüncü bir görev değildir. `camera.arducam-unverified.json` yalnız kabul eksikliği kaydıdır; matris içermez ve kalibrasyon olarak yüklenmez. USB adaptörü yalnız kesin by-id/by-path, udev ID_SERIAL, VID:PID ve FOURCC sağlandığında açılabilir; başka backend/cihaza geçmez. Ürün adından sensör, lens veya AF desteği çıkarılmadı.

IMX708 sayısal matrisi 0,1062771082 odakta çekilen 40 eski dama karesinden gelir; runtime odak 0'dır. `focus_transfer_verified=false`, `physical_distance_verified=false` korunur. Kamera sözleşmesi API, olay ve görev kayıtlarında yaklaşık/deneysel olarak görünür. Uzak netlik ve saha metrik doğruluğu kabul edilmiş değildir.

USB `read()` dönüş zamanı exposure zamanı değildir. Bu nedenle kalibrasyon dosyası sonradan eklenmiş olsa da `v4l2-observe` uçuşa açılmaz. Gerçek zaman damgası, lens/crop, montaj ve metrik geometri kabulü ayrıca geliştirilip test edilmelidir. Mevcut adaptörün gerçek Arducam'da kararlı çalışması henüz doğrulanmadı.

## Kayıt

Pi üzerinde, etkin uygulamayla **aynı görev profilini** verin; örnek IMX708 gözlem:

```bash
python -m safak_gorev2.record --config config/ana-imx708.json --panel-url http://127.0.0.1:8081 --root runtime/recordings
```

Özel saha profili kullanılıyorsa recorder'a da o profil verilir. Yarışma recorder'ı loopback dışındaki panel adresini reddeder. Böylece kullanıcı bilgisayarının/Wi-Fi'nin bağlantısından bağımsız Pi üzerinde çalışır. Kamera varyantları ayrı alt dizinlere yazılır; yük defteri ise aynı fiziksel sortie için kameralar arasında ortak tutulur, kamera değiştirerek ikinci bırakma açılmaz.

Manifest schema 2: profil ve temel config hash'i, etkin config+options digest'i, kamera sözleşmesi ve okunan kimliği/backend, HEF dosyasının gerçek hash'i, kalibrasyon hash'i, onaylı/canlı mission digest, sortie, commit/diff durumu, kaynak arşivi, görüntü/telemetri hata sayısı, segment listesi ve kapanış durumu. Aktif profil/kimlik uyumsuzluğu reddedilir. Başladıktan sonra uyumsuzluk oluşursa kayıt failed kapanır. Panel kaybında boş/eski görüntü açıkça işaretlenir; veri varmış gibi gösterilmez.

SIGTERM FFmpeg'i temiz kapatır; segment listesi/kare sayısı denetlenir. SIGKILL/güç kesintisinde manifest `recording` kalabilir: bu **canlı süreç veya tamamlanmış video kanıtı değildir**; PID/başlangıç ve segment bütünlüğü ayrıca kontrol edilir. Önceki kayıtlar otomatik onarılmış sayılmaz. HUD video 8 FPS, telemetri yaklaşık 5 Hz'dir; 50 FPS ham video sağlanmadı. Gerçek 50 FPS kayıt için depolama/segment/zaman damgası ölçümü ayrı iştir.

## Gerçek cihazda kalan kabul ve kesin komutlar

11 Eylül salt okunur SSH denemesinde son bilinen `172.20.10.2:22` bağlantıyı reddetti. Yeni fiziksel kamera/Hailo testi, Pi dağıtımı veya gerçek FC işlemi yapılmadı. Güncel erişim sağlanınca Pi üzerinde önce salt okunur envanter:

```bash
v4l2-ctl --list-devices
ls -l /dev/v4l/by-id /dev/v4l/by-path
lsusb
# Listede gerçekten bulunan video düğümünü kullanın; video0 varsaymayın.
python scripts/enumerate_usb_camera.py --device /dev/videoN --output artifacts/usb-enumeration.json
```

Envanter her komutun çıktısını/çıkış kodunu kaydeder: `--all`, `--list-formats-ext`, `--list-ctrls-menus`, udev ürün/USB kimliği, sabit bağlantılar. Kimlik, FOURCC, desteklenen boyut/FPS gerçek çıktıdan doldurulur. Sensör/lens/FOV cihaz çıktısından belirlenemiyorsa tam ürün kodu/resmî belgeyle ayrıca doğrulanır; ürün adı yeterli değildir. Odak/pozlama ayarı bu betikte yazılmaz.

Mevcut Hailo ortamında, uçuş veya MAVLink açmadan:

```bash
python scripts/probe_competition_camera.py --config config/ana-imx708.json --seconds 30 --output artifacts/probe-imx708.json
# Arducam kimlik/format alanları gerçek envanterden doldurulduktan sonra:
python scripts/probe_competition_camera.py --config config/ana-arducam.json --seconds 30 --output artifacts/probe-arducam.json
```

Probe `observe/connect=False` kullanır; Hailo/OpenCV/JPEG/görev telemetrisi üretir, FC'ye bağlanmaz. Gerçek FC telemetrisi yükü bu ölçüme dahil değildir. Ölçüler: gerçek işlenen FPS, capture→Hailo-result median/p95, OpenCV renk/PnP toplamı, tüm vision süresi, Hailo elemanı sink→src zamanı (kuyruk dahil), yakalama/çıkarım/işleme sayıları, bayat kare, sıcaklık/throttling ve CPU. Kapanışta işlenmeyen kareler ayrı adlandırılır; sensördeki fiziksel frame drop diye kesinleştirilmez. USB gecikmesi read tesliminden ölçülür; poz gecikmesi değildir. Performans enstrümantasyonu yerelde eklendi, Pi'de henüz çalıştırılmadı.

Kabul: 20–60 s süren her varyantta görüntü boyutu/format/kimlik sabit, zaman damgaları ilerliyor, hata ve bayat kare yok; 50 FPS sürdürülemiyorsa ölçülen değer/darboğaz raporlanır ve hedef doğrulama koşulları gevşetilmez. Gerçek uzak branda görünürlüğü, kontrollü hareket/netlik/pozlama, montaj yönü ve ölçülen FRD ofset, bağımsız metrik uzaklık ayrıca doğrulanır. Yazılımsal keskinlik fiziksel odak kabulü değildir. Yeni saha koordinatları veya rota uydurulmadı. Servo işi ertelendi.

## Değişen kaynaklar

- Ortak: `config.py`, `camera_contract.py`, `v4l2_camera.py`, `hailo_backend.py`, `record.py`.
- Yarışma: `config.py`, `main.py`, `route.py`, `link.py`, `controller.py`, `runtime.py`, `vision.py`.
- Profiller: yeni ana IMX708/Arducam; IMX708 temel ve hızlı saha temelinde açık kamera kimliği. Eski yalnız mavi `controller.py`, `geometry.py`, `mavlink_io.py` değişmedi.
- Yardımcılar: `enumerate_usb_camera.py`, `probe_competition_camera.py`; testler ve SITL sürücüsü; README/HANDOFF/AKIS/TESTLER/EKSIKLER.
- Bu taleple güncellenen üç eski ortak dosyanın özgün HEAD içerikleri `archive/legacy-options/*-before-dual-camera.py.txt` altında eski SHA256'larıyla korundu; koruma manifestosu yeniden hashlenerek eski içerikmiş gibi değiştirilmedi.

Test sayıları ve yeni SITL kanıtları `TESTLER.md` ve `artifacts/dual-camera-20260911/` içindedir. Gerçek araca servo/PWM/ARM/mod/rota/FC parametresi gönderilmedi. SITL kendi loopback aracına ARM/mod/rota gönderir; yük eylemleri yalnız simulated'dır.
