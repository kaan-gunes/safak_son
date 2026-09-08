# Ana ve hızlı görev — ayar durumu, 8 Eylül 2026

Kaynak: yerel iki profil ve bu oturumdaki kullanıcı beyanı. Pi/canlı araç bu oturumda okunmadı. Bu montaj revizyonu yalnız Mac'te; önceki iki görev sürümü Pi'ye aktarılmıştı.

## Yeni montaj bilgisi işlendi

Kullanıcı lensin yere baktığını, görüntü üstünün drone'un arkasına geldiğini (180°), lens merkezinin Pixhawk merkezinden 11 cm ileri ve 5 cm aşağıda olduğunu, sağ/sol kaymanın sıfır olduğunu açıkça doğruladı.

- Her iki temel profilde `camera.offset_body_m = [0.11, 0.0, 0.05]` (ileri, sağ, aşağı; metre).
- Her iki görev profilinde `camera_mount_yaw_deg = 180`.
- `competition/geometry.py` ana görevde iki rengin PnP sonucunu bu montajla gerçek NED konumuna çevirir. Eğim ve ofset birlikte dönüştürülür; yalnız yaw'a 180° eklenmez. Ham görüntü/kalibrasyon matrisi döndürülmez, aynalama yapılmaz.
- Hızlı görevde aynı montaj kaydı vardır; PnP/merkezleme kullanmadığı için bu ayar hedefe yönelme veya isabet düzeltmesi yapmaz.
- Bunlar kullanıcının ölçüm beyanıdır; görüntüde yön ve gerçek mesafe kontrolü henüz yapılmadı. Pixhawk referansının uçuş kestiricisi konum referansıyla uyumu da canlı incelenmedi.

## Boş veya tamamlanmamış alanlar

| Alan | Ana | Hızlı | Gereken bilgi/iş |
|---|---|---|---|
| Kamera kalibrasyonu | `competition-base.json` hâlâ eski IMX219 adayına bağlı; IMX708 için uygun değil | Bilerek `null`; gerekli değil | Ana için mevcut IMX708, son odak/crop ve mesafe doğrulaması. 5 Eylül IMX708 adayı var ama bugüne uygunluğu kanıtlanmadı. |
| Servo PWM | İki `release_pwm=null`, `bench_verified=false` | Aynı | Her yükte gerçek tutma/bırakma PWM ölçümü ve mekanik ayrılma. Kodda yalnız bırakma PWM alanı var; 180° başlangıcı kendiliğinden uygulamaz. |
| Aktüatör | `simulated` | `simulated` | Fiziksel bırakma için doğrulama sonrası `servo` seçimi gerekir. |
| Rota | `mission_fingerprint`, `search_start_seq`, `search_end_seq=null` | Aynı | Nihai FC rotasını geri okumak; tarama waypoint başlangıcı/sonunu seçmek. Hash'i kullanıcı hesaplamaz. |
| Saha | `entry_gates=[]`, `finish_gate=[]`, `flight_polygon=[]`, `route_reviewed=false` | Aynı | Giriş/bitiş geçiş yönleri, alan sınırları, kalkış/tarama/iniş rotası. Sabit hedef koordinatı gerekmez. |
| Yük oturumu | `sortie_id=null` | Aynı | Yükler takıldığında ortak uçuş kimliği oluşturulur; görev değişiminde aynı kalır. Kullanıcıdan rastgele teknik kimlik istenmez. |
| USB | `link.device=null` | Aynı | Kod tek `/dev/serial/by-id/*` varsa otomatik seçer; birden fazlaysa doğru port belirlenir. `null` tek başına arıza değildir. |
| Eski LAND koridor alanı | `direct_land_corridor_checked=null` | Aynı | Ortak eski yapılandırmada kalmış alan; yeni iki görevde bunun yerine rota/kapı/poligon denetimi kullanılır. Bunu gelişigüzel `true` yapmak gerekmez. |

`--check` dosya/alan kontrolüdür. Ana kalibrasyon dosyasının bulunması güncel sensöre uygunluğunu kanıtlamaz. `simulated` seçildiğinde eksik servo PWM kontrol listesine girmez; dolayısıyla liste fiziksel hazırlığın tümünü göstermez.

## Dolu ama gerçek hex üzerinde kabul edilmemiş ayarlar

| Ayar | Mevcut değer / dayanak |
|---|---|
| Araç ve yükler | Hex `vehicle_type=13`; kırmızı yük AUX1/9, mavi yük AUX2/10: kullanıcı beyanı, gerçek çıkış eşlemesi kontrol edilmeli. |
| Hedef eşlemesi | Mavi hedef→kırmızı yük; kırmızı hedef→mavi yük. Metrik hedef kenarları mavi 2 m, kırmızı 1 m olarak kodlu. |
| Model | Yeni HEF SHA256 `8433d13e…`; AI eşiği 0,40. Geçmiş dosya/çıkarım kanıtları mevcut, güncel iki renkli performans ve Hailo aygıt sağlığı henüz doğrulanmadı. |
| Hızlı kamera | 1280×720, 30 FPS isteği, sensör 2304×1296, sabit lens 0,1. Son gözlemden alınan aday başlangıç; gerçek güncel FPS/netlik kabulü değil. |
| Ana kamera | 1280×720/30 FPS; açık sensör modu ve lens değeri yok. Eski kalibrasyon bağı nedeniyle IMX708 ayar paketi henüz tamamlanmadı. |
| İlk görme | ≥3 kare/0,10 s: kullanıcının seçtiği davranış. Kutular arasında IoU≥0,25: mühendislik eşiği. |
| Duruş | Yatay ≤0,20 m/s, ≥0,30 s kararlılık; zaman aşımı 5 s. Gerçek fren mesafesi/süresi ölçülmedi. |
| Doğrulama | Ana ≥6 kare/0,50 s; hızlı ≥3 kare/0,10 s. Zaman aşımı 3 s, aynı renge yeniden durma beklemesi 5 s. |
| İrtifa | Ana lens yüksekliği hedefi 9 m, tolerans 0,25 m, alt sınır 8,5 m. Her iki görevde devralma alt sınırı home'a göre 9,5 m. Hızlı görev irtifa değiştirmez. Bunlar güncel saha onayı değil. |
| Ana merkezleme | Merkez toleransı 0,20 m, alçalma merkez toleransı 0,30 m; merkezde 1,5 s, bırakma kararlılığı 3 s. |
| Ana hız/kazanç | Yatay en çok 0,40 m/s; alçalma 0,15, çıkış 0,30 m/s; ivme sınırı 0,35 m/s². `kp_xy=0.35`, `kd_xy=0.30`, `kp_height=0.30`: hex üzerinde ayarlanmış değerler değil. |
| Bırakma hareket sınırları | Yatay 0,20 m/s, düşey 0,12 m/s, eğim 8°; kontrol eğimi 15°. Servo ACK bekleme 2 s. Fiziksel ayrılma veya isabet ölçümü yok. |
| Görüntü/geometri eşikleri | Reprojeksiyon 2,5 px; hedef düzlemi eğimi 15°; en az 900 px²; kenar 12 px; kadraj doluluğu en çok 0,88. Sentetik testler var, yeni montajla gerçek hedef kabulü yok. |
| Zaman eşleme | Kare yaşı 0,30 s, kilit kare aralığı 0,25 s, telemetri yaşı 0,60 s, heartbeat 1,5 s, poz eşleme toleransı 0,10 s; kontrol 20 Hz. Gerçek uçtan uca gecikme bu sayılardan çıkarılamaz. |

## Kullanıcıdan gereken somut bilgiler

1. Ana görev için mevcut IMX708 ile sabit odakta net görüntü ve bilinen gerçek mesafede doğrulama imkânı; kalibrasyon adayının uygunluğunu birlikte kontrol etmek gerekir.
2. İki servo için tutma ve bırakmanın gerçek mikro­saniye PWM değerleri / mekanizma testi. 180° ve 90° bilgileri zaten biliniyor, PWM karşılığı varsayılmayacak.
3. Nihai saha rotası ve sınırları, giriş/bitiş çizgileri, tarama waypointleri; kullanılacak tarama irtifası ve hız tercihi. FC ayarları geri okunmalı; eski quad hızı hex değeri sayılmamalı.
4. Bağlantı aşamasında güncel Pi erişimi; Hailo çıkarımı, kamera yönü, Pixhawk firmware/parametre/RC durumu canlı kontrol edilmeli. Bunlar kullanıcıdan ezbere sayısal değer olarak istenmez.

Montaj ölçülerini yeniden istemeye gerek yok. Her iki renk ve farklı araç eğimleriyle yerel testler yön/ofset dönüşümünü doğruladı; gerçek uçuş, Hailo veya servo denemesi yapılmadı.
