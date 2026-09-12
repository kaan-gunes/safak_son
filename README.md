# ŞAFAK UAV — iki görev seçeneği

11 Eylül: **[Ana görev: IMX708 / Arducam profilleri ve kabul rehberi](docs/competition/IKI_KAMERA_KABUL.md)**. `--config config/ana-imx708.json` veya `--config config/ana-arducam.json`; bunlar aynı ana görevin kamera varyantlarıdır. Arducam fiziksel kimliği/kalibrasyonu bilinmediği için uçuş ve bırakma kapalı; IMX708 matrisi yaklaşık kalır. Servo simulated. Yeni revizyon henüz Pi'ye dağıtılmadı.

**Teknik kontrolde önce [TEKNIK_KONTROL.md](TEKNIK_KONTROL.md) dosyasını açın:** kod haritası, kamera ayarları, kanıtlar ve açık işler.

| Seçenek | Davranış | Profil |
|---|---|---|
| **Ana görev** | YOLO veya OpenCV ile0,1s gör → dur → ikisiyle doğrula → merkezle → alçal → bırak | `config/ana-gorev.json` |
| **Hızlı görev** | YOLO veya OpenCV ile0,1s gör → dur → ikisiyle kısa doğrula → aynı irtifada bırak | `config/hizli-gorev.json` |

**11 Eylül son karar:** İlk yükten sonra arama rotasına dönülür. İkinci yük komutu da onaylanınca iki görev doğrudan **LAND moduyla bulunduğu yerde iner**; kalan waypoint/bitiş kapısına veya rotadaki LAND koordinatına gitmez. Ana görev ikinci yükten sonra tekrar yükselmez. İki yük tamamlanmamışsa mevcut AUTO rotası ve son LAND geçerlidir. ACK/PWM fiziksel yük ayrılmasını kanıtlamaz; simulated profilde bu koşul temsili bırakma sonuçlarıyla sağlanır.

**MOSSE iki uçuş akışında da yok.** Hızlı görev PnP, merkezleme veya alçalma yapmaz. Hedef görüntünün kenarında olabilir; durmak hedefin üstünde olmayı veya isabeti kanıtlamaz. Mavi hedefe kırmızı yük, kırmızı hedefe mavi yük; her yük tek sefer.

Önce [kısa kullanım ve kütüphane rehberi](docs/competition/AKIS.md), sonra [test sonuçları](docs/competition/TESTLER.md). Yeni sohbette [HANDOFF](docs/HANDOFF.md) ve [AGENTS](AGENTS.md) okunur.

## Başlatma

Pi'nin mevcut Hailo Python ortamında, proje klasöründen:

```bash
python -m safak_gorev2.competition.main --task ana --mode observe
```

veya:

```bash
python -m safak_gorev2.competition.main --task hizli --mode observe
```

Aynı anda yalnız biri çalıştırılır. `observe` kamera/model/panel açar, uçuş veya servo komutu göndermez. Yalnız dosya kontrolü için `--mode observe` yerine `--check` kullanılır. Ortamı ayrıca açmak gerekirse `bash scripts/run_pi.sh /tam/yol/setup_env.sh --task ana --mode observe`; hızlı seçenek için `ana` yerine `hizli`.

Uçuş modu `--mode flight` ancak gerçek cihaz/rota/servo/kamera doğrulamaları tamamlandığında kullanılır. `actuator=simulated` olsa bile flight gerçek navigasyon yapar. Güncel profiller temsili bırakmadadır; servo PWM ve saha bilgileri henüz tamamlanmadı. **8 Eylül50FPS/renk desteği Pi'ye dağıtıldı; gerçek uçuş kabulü değildir.**

## Klasörler

- `safak_gorev2/competition/`: iki güncel görevin uygulaması.
- `config/ana-gorev.json`, `config/hizli-gorev.json`: kullanıcı seçimleri; `ana-imx708.json`/`ana-arducam.json` kamera varyantları, `hizli-saha-20260910.json` tarihli saha profilidir. Diğer JSON dosyaları ortak ayar/kalibrasyon veya analiz girdileridir.
- `scripts/`: kamera, kayıt ve teşhis yardımcıları. MOSSE dosyası yalnız bağımsız deneydir, göreve bağlı değildir.
- `tests/`: otomatik testler ve yalnız yerel ArduCopter simülasyonu.
- `artifacts/`, `docs/`: kayıtlar, kanıtlar ve açıklamalar.
- `archive/legacy-options/`: eski quad, eski iki renkli akış ve durmadan bırakmanın çalıştırılmayan kaynak kopyaları.

Eski `python -m safak_gorev2.main` artık görev açmaz. Eski `competition-center.json`, `competition-sighting.json`, `flight-*.json` ve quad saha profil adları kaldırıldı. Ortak merkezleme/geometri kodu iki yeni görevin kullandığı destek olarak korundu.

8 Eylül montajı: lens yere bakıyor, görüntü üstü drone'un arkasında (180°); lens Pixhawk merkezinden 11 cm ileri, 5 cm aşağıda, sağ/sol sıfır. Kullanıcı beyanı iki profile işlendi ve Pi'ye aktarıldı.

İki profilde kamera isteği50FPS. OpenCV tüm görüntüde renk+dörtgen arar; YOLO kutusu şartı yok. Durduktan sonra aynı kare/bölgede YOLO + OpenCV zorunlu. Ayrı panel/video FPS'i çıkarım hızı değildir; panelde ölçülen işleme FPS'i ayrıca gösterilir.

İki görev manuel sonsuz odak (0) kullanır. Ana artık IMX708 yaklaşık matrise bağlıdır; özgün 0,1063 odaklı dama matrisi korunur, sonsuz odağa aktarımın metrik doğruluğu henüz doğrulanmadı. Son Pi testi ana 49,86 / hızlı 50,03 FPS, hata yok; görüntüyü yakın parçalar kapladığından uzak netlik kabulü yapılmadı.

Bilinen açık işler: uzak netlik/metrik kabul, gerçek branda ve yön kontrolü, servo PWM, Pixhawk portu ve saha rotası. Hailo son kısa testte çalıştı; geçmiş PCIe kopmasının uzun vadeli çözümü kanıtlanmadı. [Boş ve aday ayarların listesi](docs/competition/EKSIKLER.md).
