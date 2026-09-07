# Görev 2 — gerçek hedef ve saha kaydı

**Uçuş kaydı tamamlandı ve incelendi:** 81 özgün görüntü, eşleşmiş Hailo kayıtları ve telemetri Mac'e alındı. Güncel sonuç ve sonraki iş [FIELD_FLIGHT_01.md](FIELD_FLIGHT_01.md) içinde; aşağıdaki hazırlık notları tarihsel akıştır. Bu inceleme için ek uçuş gerekmiyor.

Uçuş öncesi bağlantı notu: kullanıcı 3S batarya ve kumanda açık/DISARM/Loiter bildirdi. Sonraki API kontrolünde ağ kesildi, SSH “Host is down” ile kapandı. Hotspot ping'i yanıtlıyor, Pi yanıtlamıyor. Loiter/RC henüz araçtan yeniden okunamadı; yazılımın çalışıp çalışmadığı şu an UNKNOWN. Windows'tan panel erişimi ve telefon–Pi mesafesi bekleniyor. `artifacts/field/20260905-loiter-ground/connectivity-report.json`.

5 Eylül 2026. Laptop ölçümleri tamamlandı; kamera/crop aynı kaldıkça yeniden dama çekimi planlanmıyor. Kullanıcı gerçek 2 × 2 m mavi brandanın ve quad'ın yanında olduğunu, yerde görüntü alınabileceğini bildirdi.

Sonraki kullanıcı açıklaması: ekip atölyede; gerçek brandanın sabit düzende tamamını kadraja sokmak büyük olasılıkla mümkün değil. Kullanıcı bahçeye çıkıp saha testi yapmayı önerdi. Yer kontrolleri ve saha koşulları uygunsa, pilotun Loiter'da tuttuğu quad'dan yalnız GÖZLEM kaydı alınması önerildi.

**Sahaya varış güncellemesi:** kullanıcı test yerine geldiklerini, brandayı serdiklerini ve Windows PC'deki Mission Planner'ı telemetri üzerinden bağladıklarını bildirdi. Bu oturumdaki bağlantı denemesinde Pi'nin `172.20.10.4` SSH sunucusuna ulaşıldı ancak geçerli kimlik doğrulama yok; 8080 paneline bağlantı reddedildi. Yazılımın çalıştığı veya güncel RC/GPS/batarya hazırlığı henüz doğrulanmadı. Kullanıcıya mevcut launcher ile `--mode observe --config config/quad.json` komutu verildi; Pi başlatma/SSH erişimi ile yerdeki Mission Planner durumu bekleniyor. Kanıt: `artifacts/field/20260905T073553Z-arrival/arrival.json`. Uçuş komutu gönderilmedi.

Sonraki güncelleme: kullanıcı SSH erişim bilgisini sağladı, ancak bu kez Pi'nin eski IP'si “No route to host” verdi; parola aşamasına ulaşılamadı. Mac hâlâ `172.20.10.5`; Pi'nin hotspot bağlantısı ve güncel IP'si bekleniyor. Kullanıcı DISARM, 11 uydu, kumanda kapalı/RC bağlı değil bildirdi. Bunlar Mission Planner'a ilişkin kullanıcı beyanları; Pi üzerinden güncel telemetri okunamadı. `network-followup.json` ağ bulgusunu kaydeder; kimlik bilgisi içermez.

**Bağlantı düzeldi ve GÖZLEM başlatıldı:** kullanıcı yeniden denememizi istediğinde SSH aynı IP'de bağlandı. Çalışan uygulama yoktu; Pixhawk USB cihazı doğrulandı. Mevcut launcher ile observe başlatıldı (o anda PID 2174; `runtime/field-observe-20260905T074141Z.log`). Hailo/IMX219 ve ArduCopter 4.5.7 taze veri veriyor. İlk canlı örnekte STABILIZE/DISARM, GPS fix=3, 11 uydu, HDOP 1,32; RC sağlıksız ve batarya 12,52 V. İlk PNG yakın, bulanık yüzey gösteriyor; hedef kontrolü sayılmadı. Kullanıcıdan kumandayı açıp DISARM iken Loiter seçmesi, bataryanın hücre sayısı ve varsa PreArm uyarısı istendi. Kanıt `artifacts/field/20260905-observe-start/`. Kamera/FC/rota ayarı değiştirilmedi; uçuş komutu yok.

## Oturum başlangıcı

Mevcut panel salt okunur olarak kontrol edildi: `observe`, HAILO, IMX219, 1280 × 720, ScalerCrop `[680,692,1920,1080]`, eşik 0,50; taze Pixhawk heartbeat, STABILIZE ve DISARM. İlk PNG'de hâlâ laptop ekranındaki mavi kare vardı. Bu görüntü gerçek branda testi sayılmadı. Kanıt: `artifacts/field/20260905-precheck/`.

## İlk gerçek branda kaydı

Yerde alınabilecek ilk görüntüde quad sağlam destek üzerinde, DISARM durumunda kalır. Laptop ekranı kadrajdan çıkarılır; gerçek branda kameraya gösterilir. İlk kısa seri sınıf/skor ve görünür yüzeyi incelemek içindir. Brandanın tamamı görünmüyorsa mesafe veya metrik merkezleme sonucu kabul edilmez. Drone'u elde uzun süre tutmak veya bütün hedefi sığdırmak için yükseğe kaldırmak bu ilk kayıt için gerekli değildir. Atölyede tam kadrajlı sabit düzen kurmak sonraki çalışmanın önkoşulu yapılmıyor.

Her seride aynı fiziksel kamera akışının özgün PNG'si ve **aynı kareye ait** Hailo sınıf/skor/kutusu kaydedilir. Mevcut `calibrate capture --panel-url` aracı yalnız görüntü yakalamak için kullanılabilir; bu işlem yeni kalibrasyon çözümü veya ayar değişikliği değildir. Her seri yeni, boş bir klasöre alınır. Fiziksel düzenin hazır olduğu bilgisi gelmeden seri başlatılmaz.

Seri kaydına şunlar eklenir:

| Bilgi | Kayıt biçimi |
|---|---|
| Sahne | Gerçek mavi branda / kırmızı örnek / hedef olmayan zemin |
| Hedefin ölçüsü | Kullanıcının ölçümü ve kaynağı; bilinmiyorsa UNKNOWN |
| Lens–hedef düzlemine dik uzaklık | Ölçüldüyse değer; eğik görüş hattı uzaklığıyla karıştırılmaz |
| Kurulum | Sabit destek, düzlem yönü, görünür köşeler ve ışık durumu |
| Kamera/model | PNG yan dosyası, akış kimliği ve mevcut HEF kimliği |
| Sonuç | Özgün kare sayısı; sınıf/skor dağılımı; 0,50 üstü/eşit kareler; yanlış sınıflar |

Mavi AI kutusu bulunan karelerde OpenCV dört köşe, sınır ve kadraj doluluk denetimleri ayrıca incelenir. Tek başına skor koşulunu geçmek görev kilidi değildir. Kamera göreli teşhis hesabı yapılırsa Pixhawk ile eşlenmiş araç merkezleme doğrulamasından ayrı raporlanır. Yaklaşık 0,5 saniye ve daha seyrek yakalanan PNG serisi, uygulamanın 0,25 saniye kilit kare aralığını doğrulamaz.

## Kadraj ve mesafe

Aday kalibrasyon ile mevcut kodun `max_frame_occupancy=0.88` sınırı birlikte okununca aşağıdaki **ideal hesaplar** elde edildi:

| 2 m karenin görüntüde dönüşü | Tam kadraja sığma, pay yok | Yalnız %88 doluluk koşulu |
|---|---:|---:|
| 0° | 4,77 m | 5,42 m |
| 45° | 6,75 m | 7,67 m |

Hesap `kenar × (|cos θ| + |sin θ|) × max(fx/genişlik, fy/yükseklik)`; doluluk sütununda sonuç 0,88'e bölünür. Lens eksenine dik, düz ve ortalanmış hedef varsayılır. Eğim, distorsiyon, merkezden kayma ve hareket için pay içermez. Bunlar uçuş irtifası önerisi veya fiziksel doğrulama değildir. Hesap kaydı `artifacts/field/20260905-precheck/precheck-report.json` içindedir.

Aktif dosyadaki eski 3,5 m önerisi mevcut crop için uygun kabul edilmiyor. Gerçek hedefte dört görünür köşe ve metre ölçeğinde bağımsız mesafe kontrolü alınmadan kalibrasyon uçuş ayarına taşınmayacak. Kamera/crop değiştirilirse mevcut ölçümlerin uyumu yeniden ele alınır.

## Sonraki kayıtlar ve saha hazırlığı

1. Gerçek mavi yüzeyde ilk sınıf/skor kaydı; tamamı görünüyorsa kadraj denetimi.
2. Mavi branda kadrajdan çıkarıldığında hedef olmayan zemin; özellikle planlanan beyaz taşlı zemin varsa ayrı seri. Kısa bir seride yanlış tespit olmaması saha genelinde yanlış pozitif oranını kanıtlamaz.
3. Kırmızı örnekle sınıf/renk ayrımı. Quad uygulamasının görevi mavi hedef olduğundan kırmızı örnekte mavi hedef kabulü oluşmaması incelenir; kırmızı hedef için mesafe algoritması eklenmez.
4. Tam hedef, bilinen farklı lens–düzlem mesafeleri ve operasyon kadrajı; ardından gözlem modunda kamera/ofset/telemetri birlikteliği.
5. Sahada mevcut RC/GPS, batarya verisi ve bağlantı yeniden okunur. Başlangıç okumasında RC sağlıklı değil, GPS fix=1/0 uydu ve görevde ilk TAKEOFF eksik. **İlk TAKEOFF uyarısı uygulamanın AUTO görev kontrolüdür; FC'nin bütün PreArm kontrollerinin özeti veya pilot kontrollü Loiter kaydının görev şartı değildir.** Gerçek FC PreArm mesajları ayrıca değerlendirilmelidir. Önceki kayıtlı failsafe bulgusu `docs/NEXT_SESSION.md` içinde açık kalıyor. Bu oturumda FC parametresi veya görev yazılmadı.
6. Saha sınırı ve açık son LAND geçişi belirlenince yalnız Görev 2 test rotası hazırlanır. Mevcut rota korunur. Görüntü yaşı ve kopma davranışı sahadaki gerçek haberleşme mesafesinde ölçülür; 150 m hâlâ hedef değerdir.

Quad bırakması temsili olaydır. Bu belge veya yerdeki görüntü kontrolü uçuşa hazır olma sonucu üretmez.

Loiter için konum/GPS, pusula ve titreşim koşulları [ArduPilot Loiter belgesinden](https://ardupilot.org/copter/docs/loiter-mode.html), FC'nin ARM öncesi denetimlerinin kapsamı [Pre-Arm belgesinden](https://ardupilot.org/copter/docs/common-prearm-safety-checks.html) bu devam oturumunda kontrol edildi. ARM engelleri denetimleri kapatarak aşılmayacak.
