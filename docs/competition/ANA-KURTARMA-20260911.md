# 11 Eylül — ana görevde hedefi geçme ve doğrulamada kalma

Kullanıcı hızlı görevi yedek olarak korumamızı istedi. Bu düzeltmede hızlı profil dosyaları, servo eşlemeleri, rota/digest ve sortie kimlikleri değiştirilmedi. Canlı FC'ye servo, ARM, mod veya parametre yazma komutu gönderilmedi.

## Gerçek uçuş bulgusu

Kanıtlar `artifacts/center-flight-1347-20260911/` altında. `competition-7a12eeafdea64b76bfaaf6685ff50777.jsonl` dosyasında 1219; `competition-b4d4dec10a1d4aba983c21c511546a2f.jsonl` dosyasında 459 geçerli kayıt var. İkincinin son sıfır dolgulu satırı geçersiz; analizde atlandı.

- Maviye gerçekten GUIDED duruş istenmiş. İki uçuşta başlangıç hızı yaklaşık 5,7 m/s; duruş doğrulamasına kadar 3,8–4,0 saniyede 8,1–9,1 metre yol alınmış. Mavi kadrajdan çıkarken kırmızı görünür olmuş. İlk doğrulamada seçilen renk hâlâ mavi.
- Son uçuşun kırmızı VERIFYING bölümünde örneklenen geometri tanılarının yalnız 7/30'u kabul edilmiş. Gerçek kararın kilidi 0,36/0,50 saniyeye kadar çıkıp kopmuş; 3 saniyelik doğrulama zaman aşımıyla AUTO'ya dönülmüş. INTERCEPT/merkezleme ve yük komutu yok.
- Eski JSONL, karar girdisiyle aynı anda alınmış görüntüyü garanti etmiyordu. Bu yüzden üst düzey aday ile karar gerekçesi bazen farklı karelere ait. Rapor oranları kaydedilen örneklerin oranıdır, bütün 50 FPS akışının oranı değildir.
- Buzzer'ın kesin sebebi kayıtlı değil. Tekrarlayan AUTO/GUIDED geçişleri gözleniyor, fakat eski günlükte FC STATUSTEXT bulunmadığından bunun buzzer sebebi olduğu kanıtlanamaz.

## Uygulanan ana görev düzeltmesi

`ana-imx708.json` ve `ana-gorev.json`: `center_search_speed_mps=1.5`, `verify_timeout_s=8.0`.

Ana görev AUTO başladığında ve her GUIDED→AUTO tarama dönüşünde MAV_CMD_DO_CHANGE_SPEED (178, tür=groundspeed) ile geçici 1,5 m/s ister. Taze ACK kabulü gelmeden hedefe kontrol devralmaz. Ret, süre aşımı veya pilot müdahalesinde iptal eder. DISARM, gözlem, yanlış rota, yanlış RC slotu, LAND sırası ve hızlı stratejide komut uygulanmaz. Field kapsamındaki giriş öncesi alan dışı bekleme de komutsuz kalır. PARAM_SET yok; kalıcı WPNAV_SPEED=1000 değiştirilmez. ArduCopter 4.6.3 AUTO başlangıcında geçici hızını yeniden kurduğu için ana görev her dönüşte isteği yineler.

Metrik geometride önce mevcut kontur köşeleriyle aynı PnP çözümü denenir; önceden kabul edilen ölçümler aynen korunur. Yalnız bu başarısızsa gerçek renk kenarında cornerSubPix ölçümü denenir. Köşe en fazla 3 piksel kayabilir; aynı kenar payı, düzlem eğimi, pozitif derinlik, belirsizlik ve reprojeksiyon koşulları uygulanır. Kırmızı kanal mevcut renk uyarlamasıyla mavi konuma taşınır. Hızlı görev bu geometri yolunu çağırmaz.

Ana JSONL'e `decision_input`, `search_speed`, `fc_messages`, ölçümün `pose` ve `corner_trials` alanları eklendi. Sonraki uçuşta karar anındaki seçilen renk/kare/kilit ve FC mesajları birlikte incelenebilir. Hızlı JSONL biçimi korunur.

## Doğrulama ve sınırlar

- Yerel: **349 geçti, 5 atlandı**. Pi: **307 geçti**. Önceki kontrolcüyle ilgili 61 akış/servo testi de geçti; güncel tam dizide aynı testler mevcut.
- Sentetik köşe gürültüsü: 0°/180° montaj, 10/15 m ve 1/2 m hedefler; geri kazanılan ölçümlerde yatay hata <0,10 m, yükseklik hatası <0,50 m. Önceden kabul edilen ölçümler değişmiyor. Bu, gerçek saha kalibrasyonu değildir.
- ArduCopter 4.6.3 hexa SITL ana görev: `20260911T145743-center-ten-meter`. İki hedefte INTERCEPT→CENTERING→DESCENDING, iki simulated yük, LAND waypointine devir ve 71,97 s'de DONE. Kalıcı WPNAV_SPEED=1000 kaldı ve geçici hız en az iki kez kabul edildi. Kamera ve yükler sentetik; fiziksel servo komutu yok.
- Güncel mission kapsamındaki hızlı SITL: `20260911T150246-quick-complete`, iki simulated yük ve 47,07 s'de DONE; velocity/search_speed komutu yok.
- İlk hızlı SITL denemesi eski field kapısından giriş bekleyerek INCOMPLETE oldu. Güncel saha mission kapsamına geçtiği için test aracı ayrıca `--mission-scope` ile güncel akışı sınar; bu amaçla üretim hızlı kodu değiştirilmedi.
- Pi kamera/Hailo, MAVLink bağlantısız 20 saniye: 1040 kare, 50,08 FPS, stale=0, hata yok. Bu probe duruş sonrası PnP başarımını ölçmez.
- Yedek: iki makinede `runtime/before-center-recovery-20260911/`. Hızlı profil ve base dosyalarının SHA256 değerleri önceki yedekle birebir aynı.

Gerçek başarısız uçuşun eşzamanlı görüntüsü yok; köşe düzeltmesinin o kırmızı hedefi kurtaracağı henüz kanıtlanmış değildir. Kamera kalibrasyonu yaklaşık/deneysel kalır. Yeni ana uçuşta `decision_input.diagnostics` ile duruş sonrası gerçek geometri sürekliliği ölçülmeli. Kırmızı servonun açılış sorunu kullanıcı isteğiyle ertelendi. Uçuş süreci başlatılmadı.
