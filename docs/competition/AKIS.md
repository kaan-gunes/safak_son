# Ana görev ve hızlı görev

Tek uygulama: `safak_gorev2.competition.main`. Kullanıcı seçimi yalnız `--task ana` veya `--task hizli`. İki görev de **MOSSE kullanmaz**.

## Ortak başlangıç

1. AUTO'nun izinli tarama bölümünde aynı renkli AI kutusu en az3 bağımsız kare ve0,10s görülür.
2. Kesilen waypoint kaydedilir; GUIDED moduna geçiş istenir.
3. GUIDED doğrulanınca sıfır hız komutu gönderilir. Araç yatayda≤0,20m/s, düşey hız/eğim sınırları içinde en az0,30s kalmalıdır.5s içinde duruş doğrulanmazsa görev LOITER devriyle iptal edilir.
4. Yalnız duruştan **sonraki taze kareler** hedef doğrulamasına katılır. Tekrarlanan kare süre kazandırmaz.

**0,10s fiziksel duruş süresi değildir.** Mod geçişi ve frenleme ek mesafe/süre alır. Durmak için de GUIDED kullanılır; bu mod yalnız hedefe gitmek için değildir.

## Seçenek farkı

| | Ana görev (`ana-gorev.json`) | Hızlı görev (`hizli-gorev.json`) |
|---|---|---|
| Durduktan sonra doğrulama | Aynı renk AI + köşe/PnP;≥6kare ve0,50s | Aynı renk AI;≥3kare ve0,10s |
| Merkezleme | Var | Yok |
| Alçalma | Var, aday profilde9m kamera yüksekliği | Yok, mevcut irtifada kalır |
| Bırakma | Kararlı merkez/irtifa ve taze hedef | Duruş ve taze kısa hedef doğrulaması |
| Sonrası | Tarama irtifasına çık, aynı waypoint ile AUTO | İrtifa komutu vermeden aynı waypoint ile AUTO |

İki görevde de3s içinde hedef doğrulanmazsa yük korunur, aynı waypoint'e dönülür. Aynı renge5s yeniden durma uygulanmaz. Kamera/telemetri kesilmesi veya pilot müdahalesi “yanlış hedef” sayılıp rotaya dönülmez; kontrol bırakılır. Pilot LOITER'a geçtiğinde aynı oturumda kendiliğinden tekrar devralınmaz.

**Hızlı görev hedefin üstünde olmayı ölçmez.** Kadrajın kenarındaki doğru hedef de kısa doğrulamayı geçebilir; isabet belirsizliği ana görevden yüksektir. Ek bir görüntü merkezi şartı eklenmedi. Mavi hedef→kırmızı yük, kırmızı hedef→mavi yük. Tek seferlik kalıcı kayıt sayesinde aynı yüke otomatik ikinci bırakma yok. İki yük sonrası mevcut bitiş/LAND rotası sürer.

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
- `controller.py`: `begin_stop` → `stop_and_verify` → ana görevde `INTERCEPT`, hızlıda `request_release` → `RESUME_SELECT`/`RESUME_AUTO`.
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

Gözlemde kamera/model/panel çalışır, uçuş ve yük komutu gönderilmez. Panel `http://PI_IP:8081/`. Kayıtlar `runtime/competition/center/` veya `runtime/competition/quick/`; iki görev aynı `runtime/competition/payload-ledger/` yük defterini paylaşır. Mevcut kaydedici ayrı terminalde `python -m safak_gorev2.record --config config/competition-base.json` (ana) veya `--config config/hizli-base.json` (hızlı) ile açılabilir. Görev kayıtları ile video kaydedici ayrı süreçlerdir.

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
- Gerçek bırakma için `actuator=servo`, yüklerin ölçülmüş `release_pwm` değerleri ve `bench_verified=true`. AUX1/kırmızı yük=çıkış9, AUX2/mavi yük=çıkış10. Derece bilgisi PWM sayısı değildir. FC'de işlev0/MIN/MAX okuması gerekir. ACK+PWM fiziksel ayrılma/isabet kanıtı değildir.
- Ana görev: mevcut IMX708'in odak/crop/montajına uygun kalibrasyon. **Ana temel profil hâlâ eski kalibrasyon adayını içeriyor; hazır sayılmaz.** 8 Eylül kullanıcı beyanıyla lens FRD ofseti `[0.11,0,0.05]` m ve yere bakan kameranın 180° ters montajı iki profile işlendi; gerçek görüntüyle yön kontrolü bekliyor.
- Hızlı görev: PnP/ofset gerekmez. Yeni `hizli-base.json` IMX708 tam sensör2304×1296,1280×720,sabit lens0,1 ile başlar; bu son kamera gözleminden alınmış başlangıç tercihidir, güncel uzak netlik/uçuş doğrulaması değildir. Eski quad ofseti taşınmadı.

Boş alanlar ve dolu aday değerlerin ayrıntılı listesi: [EKSIKLER.md](EKSIKLER.md). Hızlı profilde montaj/ofset kaydı vardır; merkezleme yapmadığından isabet düzeltmesi olarak kullanılmaz.

Son bildirilen Hailo aygıt erişimi arızası yazılım revizyonuyla çözülmüş değildir. Pi'ye dağıtım, gerçek servo veya uçuş bu çalışmada yapılmadı. Yerel test/simülasyon kanıtları `TESTLER.md` içinde; geçmiş uçuş başarı beyanı yerine kullanılmaz.
