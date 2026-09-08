# MOSSE ve komut çakışması değerlendirmesi — 7 Eylül 2026

Karar: MOSSE kısa tespit boşlukları için denenmeye değer; mevcut uçuşa takılarak sorunun çözüldüğü söylenemez. Komutların üst üste eklenmesi, incelenmiş AUTO uçuşlarının merkezlememesini açıklamıyor. Bu çalışma mevcut mavi merkezleme koduna, yarışma kontrolüne, Pi'ye veya FC ayarlarına dokunmadı.

## İleri gidiş ve merkezleme birbirine ekleniyor mu?

`safak_gorev2/controller.py` SEARCHING durumunda hedef yokken veya doğrulama sürerken navigasyon eylemi üretmiyor; AUTO rotasını Pixhawk yürütüyor. Süre/kare koşulları sağlanınca `claim` ve GUIDED mod isteği oluşuyor. GUIDED görülmeden merkezleme hızı üretilmiyor. `mavlink_io.py` ikinci kez mod kontrolü yapıyor: AUTO'da hız/stop eylemini uygulamıyor. Hızlar bir mesafe kuyruğuna eklenmiyor; geçerli hız hedefi yenileniyor. [ArduPilot AUTO](https://ardupilot.org/copter/docs/auto-mode.html) ve [GUIDED komutları](https://ardupilot.org/dev/docs/copter-commands-in-guided-mode.html) da bu ayrımı açıklar.

`artifacts/field/video-review/REPORT.md` daha önce incelenmiş 5 Eylül kayıtlarında aralıklı geçerli hedefler nedeniyle GUIDED/durma komutu oluşmadığını bildiriyor. Bu tur videolar tekrar açılmadı. Başka yazılımın dışarıdan komut gönderdiği tüm olasılıklar incelenmiş değildir; ancak uygulamamızın her görüntüde ileri git + hedefe git komutlarını biriktirdiği iddiası kodla uyuşmuyor.

Araç yavaşlarsa hedef kadrajda daha uzun kalabilir. Fakat waypointler arası mesafeyi kısaltmak doğrudan hız sınırını düşürmek değildir. Önceki quad'da WPNAV_SPEED 1000→150 cm/s yapılmıştı; bu tarihli bilgi güncel hex ayarı değildir. 0,50 saniyede 1,5 m/s hızla 0,75 m yol alınır; örnek hesap frenleme mesafesini ve haberleşme gecikmesini içermez. Tespit/geometri sürekli reddediliyorsa yavaşlamak tek başına kilit sağlamaz. GUIDED sonrası atalet/frenleme ayrı test konusudur; burada hiç GUIDED'e geçilmemesiyle karıştırılmamalı.

Eklenen iki test: aralıklı hedefler AUTO aramasında navigasyon komutu üretmiyor; kontrol sahipliği alınmış olsa bile AUTO'da hız/stop uygulanmıyor, GUIDED'de hız hedefi kabul ediliyor. `tests/test_auto_guided_separation.py`.

## MOSSE neyi sağlar, neyi sağlamaz?

Model bir karede hedefi bulur; MOSSE sonraki görüntülerde o bölgenin görünüşünü izleyebilir. Modelin bir sonraki karede kutu üretememesi her zaman nesnenin kaybolması değildir. Bu nedenle öneri teknik olarak yerinde.

Ancak [OpenCV MOSSE](https://docs.opencv.org/4.13.0/d0/d20/classcv_1_1legacy_1_1TrackerMOSSE.html) gri görüntü kullanır; mavi/kırmızı sınıflandırmaz. Gölgeye başlatılırsa gölgeyi de izleyebilir. `update=True` yeni AI doğrulaması veya hedefin doğru olduğu anlamına gelmez. [OpenCV 4.12 kaynak uygulaması](https://github.com/opencv/opencv_contrib/blob/4.12.0/modules/tracking/src/mosseTracker.cpp) sabit pencere boyutuyla merkez kaymasını takip eder; alçalırken ölçek ve perspektif değişimini güvenilir metrik köşe olarak vermez. Kutudan dört köşe uydurup PnP'ye vermek uygun değil.

**Takip kutusunu mevcut geçerli hedef listesine eklemek yapılmadı.** Bu, aynı AI tespitini yeni bağımsız model kanıtı gibi çoğaltırdı. Mevcut kilit koduna bağlı olmayan bu prototip bugün uçuştaki kilit davranışını değiştirmez. Gelecek entegrasyonda hedef kimliğinin kısa süre korunması, güncel görüntüde köşe/geometri doğrulaması ve taze AI kanıtının yaşı ayrı tutulmalı. Tahmini takip tek başına alçalma/bırakma yetkisi vermemeli.

## Hazırlanan somut deney

`scripts/mosse_probe.py`: yalnız dosya okuyan bağımsız araç. Kamera, Hailo, MAVLink, görev denetleyicisi ve panel açmaz. Son model kutusundan itibaren en fazla 0,30 s takip, en fazla 0,15 s görüntü aralığı; bunlar deney tercihleri, uçuşta doğrulanmış sınırlar değil. Başarılı takip süreyi uzatmaz. Takip başarısızsa/eskiyse kutu bırakılır. Yeni AI kutusunda yeniden başlatılır; o anda takip kutusuyla IoU farkı da kaydedilir. Bu araç birden çok hedefin kalıcı kimliğini yönetmez; önceden seçilmiş tek hedef dizisi içindir.

Girdi JSONL, her satırda aynı gerçek görüntüye ait:

```json
{"frame_id": 1, "timestamp_s": 0.0, "image": "0001.png", "detector_bbox_xywh": [100, 100, 80, 80]}
{"frame_id": 2, "timestamp_s": 0.033333, "image": "0002.png", "detector_bbox_xywh": null}
```

Kutu özgün görüntü piksel koordinatlarında x/y/genişlik/yükseklik. Zaman gerçek yakalama zamanı; nominal AVI FPS'sinden uydurulmamalı. AI ile tam kare eşlemesi gerekir. Elle seçilmiş kutu kullanılırsa bunun model deneyi olmadığı ayrıca belirtilmeli. Yakın zamanlı HUD ve telemetriyi aynı sensör karesi sanmayın. Eski 1 Hz PNG kümesi bu kısa aralıklı takip testi için yeterli değil.

Mac'te ayrı ortam hazırlandı; ana OpenCV ve Pi ortamı değiştirilmedi:

```bash
runtime/mosse-env/bin/python scripts/mosse_probe.py --manifest /tam/yol/kareler.jsonl --output /tam/yol/yeni-sonuc
```

Yeni ortam gerekiyorsa mevcut Python ile `python -m venv runtime/mosse-env`, ardından bu ortama `opencv-contrib-python-headless==4.12.0.88 numpy==2.2.6 pytest==8.4.2` kurulur. Hailo ortamının OpenCV paketini bu amaçla değiştirmeyin.

Çıktı: `frames.jsonl`, her kare için kutulu JPEG, sürüm/kaynak SHA256/ayar/sayaç içeren `summary.json`. Model kutusu yeşil, takip turuncu, hepsinde OFFLINE işareti. Her sonuçta `flight_eligible=false`. Mevcut sonuç klasörüne yazma, yinelenen/geri giden kare veya zaman, değişen boyut, bozuk görüntü, kadraj dışı AI kutusu reddedilir. Tamamlanmayan turda özet yoktur; kısmi çıktı başarı sayılmaz.

## Doğrulanan sonuç ve sınırı

- Ana ortamda ilgili controller/IO ve yeni testler: **32 geçti, 1 MOSSE testi contrib olmadığı için atlandı**.
- Ayrı OpenCV contrib 4.12 ortamında MOSSE testleri: **5 geçti**; bunlardan biri gerçek OpenCV takip algoritmasını çalıştırıyor, diğerleri zaman/girdi/kayıp davranışlarını denetliyor.
- Kaydedilmiş yapay 12 karelik deney: 1 başlangıç kutusu, ardından 7 takip karesi; hedef kaldırıldığında kalan 4 karede kutu yok. İlk 8 karede gerçek yapay kutuyla en düşük IoU=1,0. Bu kolay, dokulu ve yavaş öteleme örneği gerçek branda başarısı veya Pi performansı değildir. Kanıt `artifacts/mosse-review-20260907/validation.json` ve `synthetic-result/`.
- `docs/competition/legacy-sha256.json` içindeki tüm korunan dosyalar aynı hash'te.

## Sıradaki aksiyon

Önce son kayıtta bildirilen Hailo aygıt erişimi sorunu giderilip çıkarımın çalıştığı doğrulanmalı; MOSSE kapalı/erişilemeyen modeli onarmaz. Bu tur Pi'ye bağlanılmadı, güncel donanım durumu bilinmiyor.

Ardından temiz, ardışık IMX708 kareleriyle aynı kareye eşlenmiş model kutuları hazırlanıp araç çalıştırılmalı. Son temiz kırmızı/mavi kayıt `runtime/red-blue-camera-recordings/20260907T174756/` Pi'de; o çekimde Hailo kapalı olduğundan yeni çıkarım gerekir. Gerçek branda etiketleriyle boşlukların ne kadarı doğru dolduruluyor, gölgeye kayma ve hedef çıktıktan sonra yanlış takip ölçülmeli. İyileşme varsa ayrı yarışma/gözlem akışında entegrasyon ve mod geçişi testi yapılır. Mevcut mavi merkezleme korunur. Henüz gerçek MOSSE saha karşılaştırması veya uçuş onayı yok.
