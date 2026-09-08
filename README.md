# ŞAFAK UAV — iki görev seçeneği

| Seçenek | Davranış | Profil |
|---|---|---|
| **Ana görev** | 0,1s gör → dur → doğrula → merkezle → alçal → bırak → rotaya dön | `config/ana-gorev.json` |
| **Hızlı görev** | 0,1s gör → dur → kısa doğrula → aynı irtifada bırak → rotaya dön | `config/hizli-gorev.json` |

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

Uçuş modu `--mode flight` ancak gerçek cihaz/rota/servo/kamera doğrulamaları tamamlandığında kullanılır. `actuator=simulated` olsa bile flight gerçek navigasyon yapar. Güncel profiller temsili bırakmadadır; servo PWM ve saha bilgileri henüz tamamlanmadı. **Bu revizyon Pi'ye aktarılmadı; yerel yazılım sonucu gerçek uçuş kabulü değildir.**

## Klasörler

- `safak_gorev2/competition/`: iki güncel görevin uygulaması.
- `config/ana-gorev.json`, `config/hizli-gorev.json`: kullanıcı seçimleri; diğer JSON dosyaları kamera/ortak ayar veya analiz girdileridir.
- `scripts/`: kamera, kayıt ve teşhis yardımcıları. MOSSE dosyası yalnız bağımsız deneydir, göreve bağlı değildir.
- `tests/`: otomatik testler ve yalnız yerel ArduCopter simülasyonu.
- `artifacts/`, `docs/`: kayıtlar, kanıtlar ve açıklamalar.
- `archive/legacy-options/`: eski quad, eski iki renkli akış ve durmadan bırakmanın çalıştırılmayan kaynak kopyaları.

Eski `python -m safak_gorev2.main` artık görev açmaz. Eski `competition-center.json`, `competition-sighting.json`, `flight-*.json` ve quad saha profil adları kaldırıldı. Ortak merkezleme/geometri kodu iki yeni görevin kullandığı destek olarak korundu.

8 Eylül montajı: lens yere bakıyor, görüntü üstü drone'un arkasında (180°); lens Pixhawk merkezinden 11 cm ileri, 5 cm aşağıda, sağ/sol sıfır. Kullanıcı beyanı iki profile işlendi. Bu montaj revizyonu henüz Pi'ye aktarılmadı.

Bilinen açık işler: IMX708 güncel odak/kalibrasyon uyumu, gerçek görüntüde yön kontrolü, gerçek servo PWM, saha rota/kapıları ve son bildirilen Hailo aygıt erişimi sorunu. [Boş ve aday ayarların listesi](docs/competition/EKSIKLER.md).
