# ŞAFAK UAV — teknik kontrol için kod rehberi

11 Eylül güncel kamera/backend/rota/kayıt revizyonu: [iki kamera kabul rehberi](docs/competition/IKI_KAMERA_KABUL.md). Yeni kod yereldedir; aşağıdaki 8 Eylül canlı ölçümleri yeni Arducam testi değildir.

8 Eylül 2026. İki güncel görev aynı kamera, Hailo ve uçuş bağlantısı altyapısını kullanır. Ana görev merkezler/alçalır; hızlı görev durduğu irtifada bırakır. Aşağıdaki bağlantılar incelenen gerçek kaynak dosyalarına gider.

## Kod okuma sırası

| Sıra | Dosya | Görevi |
|---|---|---|
| 1 | [Giriş](safak_gorev2/competition/main.py) | `--task ana` / `--task hizli`, gözlem/uçuş seçimi ve panel |
| 2 | [Ana profil](config/ana-gorev.json), [hızlı profil](config/hizli-gorev.json) | İki görevin süreleri, rota ve yük ayarları |
| 3 | [Durum makinesi](safak_gorev2/competition/controller.py) | Arama → duruş → doğrulama → ilk yükte aynı AUTO waypoint, ikinci yükte doğrudan LAND |
| 4 | [Renk arama](safak_gorev2/competition/color_search.py), [görüş birleştirme](safak_gorev2/competition/vision.py) | Bağımsız OpenCV renk/dörtgen adayları ve aynı karede YOLO eşlemesi |
| 5 | [Kamera/Hailo](safak_gorev2/hailo_backend.py), [runtime](safak_gorev2/competition/runtime.py) | Kare zamanı, çıkarım, işleme, bayat veri denetimi |
| 6 | [Montaj dönüşümü](safak_gorev2/competition/geometry.py), [ortak geometri](safak_gorev2/geometry.py) | Ana görevde dört köşeden PnP ve kamera/gövde/NED dönüşümleri |
| 7 | [Araç bağlantısı](safak_gorev2/competition/link.py), [rota](safak_gorev2/competition/route.py) | MAVLink, mod/sahiplik, tarama ve kapı denetimleri |
| 8 | [Yük defteri](safak_gorev2/competition/payload.py) | Tek seferlik yük kaydı; ACK/PWM izleme |

## Görüntü ve karar akışı

Kamera → Hailo YOLO + OpenCV renk/dörtgen → kararlı aday → GUIDED duruş → taze çift kanıt.

- Arama: YOLO **veya** OpenCV; en az 3 ayrı kare ve 0,10 saniye.
- Duruş: ölçülen yatay hız ≤0,20 m/s, en az 0,30 saniye kararlılık. 0,10 saniye fiziksel durma süresi değildir.
- Doğrulama: aynı kare, renk ve bölgede YOLO **ve** OpenCV. Salt renk ile bırakma yok.
- Ana: metrik doğrulama → merkezleme → alçalma → bırakma; ilk yükte tarama irtifası/aynı rota, ikinci yükte yeniden yükselmeden LAND.
- Hızlı: kısa çift doğrulama → aynı irtifada bırakma; ilk yükte aynı rota, ikinci yükte LAND. Merkezleme/alçalma/PnP yok.
- LAND bulunduğu yerde iniştir; ikinci yük sonrası kalan rota/bitiş kapısı atlanır. İki yük tamamlanmazsa mevcut AUTO son LAND rotası sürer. Bu son karar 11 Eylül kullanıcı isteğidir.
- Doğrulama zaman aşımında yük korunur; pilot devri ve bayat veri ayrıca ele alınır. MOSSE yok.

## Kamera ve kalibrasyon

İki profil: IMX708, 1280×720, 50 FPS isteği, 2304×1296 sensör modu, tam görüş alanı ve **manuel sonsuz odak `LensPosition=0`**. Lens yere bakar, görüntü üstü arka yönündedir (180°); lens merkezi Pixhawk'tan 11 cm ileri, 5 cm aşağı, sağ/sol sıfır. Montaj ölçüleri kullanıcı beyanıdır.

Ana profil [sonsuz odak için yaklaşık IMX708 matrisi](config/camera.imx708-infinity-approx.json) kullanır. Bu dosyanın sayısal matrisi, [5 Eylül özgün adayından](config/camera.imx708-candidate.json) değiştirilmeden alınmıştır. **Dama çekim odağı 0,1062771082, çalışma odağı 0'dır.** `calibration_capture_lens_position` gerçek çekim ayarını, `lens_position` istenen çalışma ayarını belirtir. `focus_transfer_verified=false` ve `physical_distance_verified=false`: sonsuz odakta yeni kalibrasyon veya saha metrik kabulü yapılmış değildir. Hızlı görev matris kullanmaz.

40 özgün kare SHA256 ile doğrulandı, 8 poz yeniden çözüldü. Yeniden çözüm RMS 0,1338 px; önceki aday 0,1388 px. Odak uzunlukları farkı yaklaşık %0,04/%0,06; çözümler birebir aynı değildir, farkın nedeni kesinleştirilmedi. Ayrı 5 yakın referans karesinde eski matris yaklaşık 79,92 cm verdi (kullanıcı ölçüsü 80,8 cm; ölçüm belirsizliği bilinmiyor). Bu sonuç uçuş mesafesinde doğruluk kanıtı değildir. [İnceleme kaydı](artifacts/camera-review-20260908/review.json).

Raspberry Pi, 0 konumunu sonsuz olarak tanımlar; odak mesafesi ayarının yaklaşık olduğunu da belirtir. Sonsuz ayarı tek başına netlik garantisi değildir. [Resmî kamera belgesi](https://www.raspberrypi.com/documentation/computers/camera_software.html#lens-position).

## Kontrol ve kanıt

Dosya kontrolü (kamera/USB/servo açmaz):

```bash
python -m safak_gorev2.competition.main --task ana --check
python -m safak_gorev2.competition.main --task hizli --check
```

Rota/oturum alanları henüz boş olduğu için `--check` eksikleri bildirip çıkış kodu 2 döndürür. Bu bir Python çalıştırma hatası değildir. Varsayılan aktüatör `simulated`; fiziksel servo ayarı tamamlanmış değildir. `flight` modu simulated yükle bile gerçek navigasyon komutu gönderebilir.

- [Test raporu](docs/competition/TESTLER.md): önceki 209 yerel/125 Pi testi ve 3 hex SITL senaryosu. SITL görüntü ve yük sonuçları simüledir.
- [Son kamera incelemesi](artifacts/camera-review-20260908/): yeniden çözüm, profil dağıtım hashleri ve süreli gerçek kamera testleri.
- Son kamera profilleriyle 98 ilgili test hem yerelde hem Pi'de geçti. Gerçek görüntü akışı ana 49,86 / hızlı 50,03 FPS; ikisi manuel lens 0 ve hatasız. Son görüntülerde yakın parçalar görüşü kaplıyor; uzak netlik/gerçek hedef kabulü yapılmadı. Testler kapalıdır.
- [Açık işler](docs/competition/EKSIKLER.md): uzak netlik/metrik kabul, gerçek branda, port/telemetri, servo ve yarışma rotası.
- [Devir notu](docs/HANDOFF.md): yeni sohbetin devam noktası ve tarihli geçmiş.

## Klasör düzeni

`config/` çalışma profilleri; `safak_gorev2/` uygulama; `tests/` testler; `scripts/` yardımcılar; `docs/` açıklamalar; `artifacts/` test/kalibrasyon kanıtları; `runtime/` çalışma kayıtları; `best_hailo_model/` güncel modeldir. `finetune_dataset/` eğitim verisi ve ZIP'ini içerir. Eski saha videoları `archive/field-videos-20260907/`, eski çalıştırma seçenekleri `archive/legacy-options/` altındadır. Eski kayıtlar silinmemiştir; taşınan dosyalar hash ile doğrulanmıştır.
