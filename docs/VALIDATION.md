# Doğrulama kaydı

Güncelleme: 5 Eylül 2026. Bu dosya devam eden çalışmanın kanıtlarını kaydeder; tamamlanmamış satırlar başarı sayılmaz.

| Gereklilik | Kanıt / mevcut durum |
|---|---|
| Görev 1'e dokunmama | Yeni kod yalnız `safak_gorev2/`; görev dosyası, FC parametresi veya eski proje değiştirilmedi |
| Yüklenen modelin korunması | HEF SHA256 `b43dfac55acae45ce5db26301b6b7e9d63dc9be64e77a2f5069566068db45291`; uygulama başlangıcında kontrol edilir |
| Hailo donanımı | SSH üzerinden `hailortcli fw-control identify`: HAILO8L, firmware/HailoRT 4.20.0 |
| Mevcut ortam | Kullanıcının Desktop ortam betiği etkinleştirildi; Python 3.11, NumPy 1.26.4, OpenCV 4.11.0, pymavlink 2.4.49, Flask 2.2.2 ve referans Hailo import yolu bulundu |
| Kamera | Pi `rpicam-hello --list-cameras` çıktısında IMX219 bulundu |
| Hailo üzerinde yeni uygulama | Pi'deki ayrı klasörden GÖZLEM modunda gerçek IMX219 → `hailonet` → yüklenen HEF → callback zinciri ve HTTP panel çalıştı. Kısa örnekte ~30 bağımsız kare/s; hedef doğruluğu veya saha benchmark'ı değildir. `artifacts/pi/status-initial.json`, `doctor.json` |
| Gerçek hedefle tespit/renk eşlemesi | Laptopta kullanıcı ölçümü 15 cm mavi kare, Hailo'da 20/20 karede class_id=2/mavi_hedef; skor 0,5097, kayıt sırasındaki 0,65 eşiğinin altında; sonraki geçici 0,50 skor koşulunu geçer. Gerçek fiziksel 2 m hedef/negatif örnek doğrulaması bekliyor |
| Gerçek kamera kalibrasyonu/metrik mesafe | Üç seride 115 özgün PNG; 55 seçilmiş kareyle RMS 0,471 px aday kalibrasyon. 60 cm kullanıcı referansında 60,605 cm; sabit 80 cm kullanıcı referansında 80,082 cm hesaplandı. Elde alınan iki 80 cm beyanlı seri uyuşmadı ve ayrı korundu. Gerçek 2 m hedef/operasyon mesafesi doğrulaması bekliyor; uçuş ayarına uygulanmadı |
| Kamera ofseti | Kullanıcı 3 cm arkada, sağ/sol yaklaşık ortada, Pixhawk seviyesinden 5 cm aşağıda bildirdi; config `[-0.03, 0, 0.05]` m. Fiziksel ölçümü agent yapmadı |
| Kontrol ve veri sözleşmeleri | Yerel pytest: 35 test geçti; kilit, müdahale, eski kare, geometri, tek olay, görev ve panel API/hazırlık kontrolleri. Kalibrasyon PNG'sinin kaynak piksellerini koruması, eski kareyi reddetmesi ve uçuş modunda kapalı olması; bilinen kamera matrisinin yeniden bulunması ve düşük toplam RMS içinde saklanan hatalı tek görüntünün reddi de sınandı |
| Tam sentetik akış | Panel API'si `DONE` ve tek `SIMULATED_RELEASE` gösterdi; gerçek Hailo/Pixhawk uçuş kanıtı değildir |
| Gerçek ArduCopter SITL | Resmî Copter-4.6.3, commit `92b0cd788ec29406f26c6f9c31d5ceedbd1cc538` derlendi. Tam görev, pilot müdahalesi, hedef kaybı ve kontrol döngüsü duraklaması senaryoları geçti; ayrıntılar aşağıda |
| Gerçek Pixhawk USB/firmware/parametreler | Kullanıcı sabah USB bağlantısını yaptı. Salt okunur MAVLink ile ArduCopter 4.5.7, quad kimliği, TIMESYNC, parametreler ve 8 maddelik rota okundu; `artifacts/pi/pixhawk-detail-20260905.json`. Uçuş komutu gönderilmedi |
| Panel | Yerel ve Pi Flask HTTP 200, salt okunur API ve gerçek kameradan JPEG doğrulandı; Pi adresi `http://172.20.10.4:8080/` |
| 150 m yayın ve kontrol | Saha testi yapılmadı |
| Fiziksel quad merkezleme/alçalma/Loiter | Uçuş testi yapılmadı |

Gece kullanıcının ısınma endişesi üzerine Pi'de başlatılan gözlem uygulaması kapatıldı; panel de durdu. SoC ölçümü kapatmadan önce 57,85 °C, kısa süre sonra 55,65 °C, `get_throttled=0x0`. Kullanıcı uyurken kamera yeniden başlatılmadı; testler Mac'te sürdü. Kullanıcı sabah hazır olduğunu bildirince gözlem yeniden açıldı. Oda karanlığı nedeniyle gece görüntüleri gerçek hedef tespit başarımı olarak değerlendirilmez.

## ArduCopter entegrasyon deneyleri

`tests/run_sitl.py` yalnız kendisinin başlattığı yerel SITL sürecine bağlanır; gerçek Pixhawk/Pi adresi kabul etmez. Uçuş dinamiği, modlar, görev protokolü ve MAVLink telemetrisi ArduCopter'den gelir. Kamera, kalibrasyon, mavi hedef kutuları ve hedef konumu **sentetiktir**. Simülasyon için kullanılan parametreler ve ARM/görev yükleme komutları yalnız bu test aracında bulunur; üretim uygulamasında bulunmaz.

| Senaryo | Gözlenen sonuç | Yerel kanıt |
|---|---|---|
| Tam akış | AUTO kalkış → GUIDED merkezleme/alçalma → tek temsili bırakma → arama irtifasına çıkış → son LAND → yerde DISARM/DONE | `artifacts/sitl/complete/result.json` ve aynı klasörde `runtime/events.sqlite3` |
| Pilot müdahalesi | Alçalma başında RC mod anahtarı Loiter'a alındı; PILOT_CONTROL, bırakma yok. FC'nin Loiter'a geçişi ve 3 s tekrar devralmama da kontrol edildi | `artifacts/sitl/pilot/result.json` |
| Hedef kaybı | Alçalma başında hedef kaldırıldı; durdurma, ABORTED ve FC Loiter. Bırakma yok | `artifacts/sitl/lost-target/result.json` |
| Karar döngüsü duraklaması | Karar çekirdeği 2 s bekletildi; MAVLink işçisinin komut süresi denetimi hareketi kesti, FC Loiter. Bırakma yok, kontrol yeniden devralınmadı | `artifacts/sitl/control-stall/result.json` |

Tam simülasyon yaklaşık 75 s sürdü. Temsili olayda hesaplanan yatay hata 0,017 m, sentetik hedef konumuna göre hata 0,021 m, tahmini lens yüksekliği 3,721 m idi. Bunlar ideal sentetik kare üzerindeki simülasyon değerleridir; gerçek hedef, IMX219, titreşim, rüzgâr veya yük isabeti doğruluğu vaadi değildir.

Kaynak/protokol incelemesinde TIMESYNC yanıtındaki `tc1=FC zamanı`, `ts1=isteğin yankısı` eşlemesi gerçek ArduCopter koduna göre düzeltildi ve hem birim testinde hem SITL'de doğrulandı. Test başlatıcısı ilk BOOT heartbeat'inde görev yüklemeyi denediğinde `MISSION_NO_SPACE` aldı; otopilot başlangıcının tamamlanmasını bekleyecek şekilde düzeltildi. Loiter devri deneylerinde test pilotunun gazı havada nötre alınır; sıfır gazın Loiter'daki iniş isteği, uygulamanın düşey komutu diye yorumlanmaz.

Panelin HTTP/API kontrolleri, JavaScript/Python/shell sözdizimi ve SIGTERM ile temiz kapanışı da doğrulandı. Birim testleri tek başına uçuşa hazır olma veya 150 m radyo menzili kanıtı değildir. Fiziksel oturumda kalan işler `docs/NEXT_SESSION.md` içindedir.

## Sabah gerçek donanım okuması

Kullanıcı hazır olduğunu bildirince gözlem paneli yeniden açıldı. USB yolu `usb-ArduPilot_fmuv3_3F002B001551383235343838-if00`; gerçek firmware 4.5.7, STABILIZE/DISARM. Hailo görüntüsü ve Pixhawk telemetrisi aynı panelde görüldü; `artifacts/pi/status-connected-20260905.json`. Mod adlarının tamamı pymavlink ArduCopter tablosundan gösteriliyor; gönderilebilen mod listesi değişmedi.

Uçuş öncesinde kalan somut bulgular: başlangıç TAKEOFF içermeyen mevcut rota, RC_CHANNELS chancount=0, GPS fix=1/0 uydu ve kamera kalibrasyonunun eksikliği. FS_THR_ENABLE=1 değeri bu firmware için RTL anlamına geliyor; yarışmanın RC kaybında kontrollü iniş koşuluyla uyuşmuyor. FS_OPTIONS=16, RC_FS_TIMEOUT=1, FS_GCS_ENABLE=0 okundu. Gerçek FC parametreleri ve mevcut rota değiştirilmedi. [ArduCopter 4.5.7 parametre kaynağı](https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/ArduCopter/Parameters.cpp).

## İlk ekran deseni kaydı

Kullanıcı Mac ekranındaki 100 mm kontrol çizgisini cetvelle 100 mm ölçtüğünü ve kamera yüksekliğinin yaklaşık 40 cm olduğunu bildirdi. Kare kenarlarının yatay/düşey ayrı ölçümü henüz verilmedi. 25 mm kare varsayımı yalnız teşhis hesabında kullanıldı; yaklaşık kamera yüksekliği bağımsız hassas mesafe kanıtı değildir.

Çalışan gözlem panelinden 40 farklı, özgün 1280 × 720 PNG alındı ve Mac'e kopyalandı: `artifacts/calibration/imx219-screen-20260905-a/`. Kamera IMX219, ScalerCrop `[680, 692, 1920, 1080]`; yeni kamera veya yeniden boyutlandırılmış panel JPEG'i kullanılmadı. Kullanıcıya çekimin bittiği ve drone'u elde tutmayı bırakabileceği hemen bildirildi.

OpenCV SB ve klasik köşe bulma incelemesinde 22 aday bulundu. İşaretli görüntülerin görsel incelemesi, SB'nin bulduğu 5 adayda üst kenarı iç köşelerle karıştırdığını gösterdi. 22 adayın teşhis uyarlaması RMS 2,002 px ile 1 px sınırını geçti. Klasik yöntemin 17 adayı ayrı uyarlandığında RMS 0,674 px çıktı; buna rağmen 18 görüntü alt sınırı karşılanmıyor ve yatay/dikey merkez kapsamı yaklaşık 0,287/0,144 ile dikey 0,25 koşulunun altında kalıyor. Düşük RMS tek başına kabul edilmedi; kalibrasyon dosyası veya uçuş ayarı oluşturulmadı. Ham kayıtlar, `detection-report.json` ve `diagnostic-fit.json` korundu. Bu teşhis incelemesi üretimdeki SB çözücüsünü değiştirmedi.

Ek çekimde drone sağlam bir destek üzerinde tutulup desen farklı kadraj bölgelerine ve açılara taşınacak; ekran yansıması azaltılacak ve bütün kareler/kenarlar görünür kalacak. Kayıt sonrası Pi ölçümü 57,1 °C ve `get_throttled=0x0`; bu yalnız o anın ölçümüdür.

## İkinci ve üçüncü ekran deseni kaydı

Kullanıcı hazır olduğunu bildirince 45 ve 30 yeni özgün PNG alındı: `imx219-screen-20260905-b/` ve `imx219-screen-20260905-c/`. Çekim bittiği bildirildi. Kullanıcı Mac'i fiziksel olarak farklı mesafe/açılara taşıdığını ve karelerin tam 25 mm olduğunu bildirdi. Kamera/model/crop üst verisi üç seride aynı kaldı. Ekranda yazılımsal yakınlaştırma sorusunu kullanıcı fiziksel yakınlık olarak yanıtladı; desenin kare ölçüsü 25 mm beyanına dayanıyor.

Klasik köşe bulucunun üç serideki 59 adayı incelendi; dört yüksek artık hatalı kare (`a/018`, `b/002`, `b/031`, `b/042`) teşhis aşamasında ayrıldı. Seçilen 55 özgün kare yeni çözücüyle bağımsız olarak yeniden okundu: RMS 0,47074 px, her görüntü RMS ≤1 px, normalize merkez kapsamı x=0,357/y=0,266. Tahmini düzlem eğimi iki eksende yaklaşık 40°/47° aralık kapsıyor. Beş parçalı sayısal kontrolün ayrılan görüntülerindeki ortalama RMS 0,379–0,440 px; bu seçimden sonra yapılan aynı veri kümesi kontrolüdür, bağımsız fiziksel doğrulama değildir.

Kanıt klasörü `artifacts/calibration/imx219-screen-20260905-review/`: özgün dosya hash'li `selection-manifest.json`, `diagnostic-fit.json`, seçilen dosyalar ve `camera.candidate.json`. Adaydaki fx/fy yaklaşık 1720,10/1718,53 px; üretim `solve --detector classic` ile yeniden üretildi. Çözücü artık toplam RMS düşük olsa bile tek görüntünün 1 px üstü hatasını reddediyor. Değişiklik sonrası 35 test geçti. Aday dosyada `physical_distance_verified=false`; aktif config hâlâ kalibrasyonsuz gözlem modunda.

Mevcut dar akışta 2 m hedef için ideal, eksenlerle hizalı pinhole düşey kadraj sınırı `2*fy/720` ile yaklaşık 4,77 m. Bu mesafe emniyet payı, distorsiyon veya eğim hesabı değildir; 45° dönmüş bir kare için ideal sınır yaklaşık 6,75 m olur. Dolayısıyla ilk 3,5 m bırakma önerisi mevcut akışla uygun kabul edilmiyor. Görüş alanı/gerçek hedef ve görev yüksekliği birlikte doğrulanacak; kamera/crop değiştirilmedi.

Son Pi örneği 57,1 °C, `get_throttled=0x0`.

## 60 cm ekran mesafesi karşılaştırması

Kullanıcı kayıt alınmasını istedi; kalibrasyon çözümüne katılmayan 18 yeni özgün kare `artifacts/calibration/imx219-distance-check-01/` içine kaydedildi. Kullanıcı o sırada lens–ekran dik mesafesini 60 cm bildirdi. 25 mm kare ve aday matrisle 18 karenin tümünde köşeler bulundu; tek kare RMS aralığı 0,137–0,347 px. Kameranın ekran düzlemine dik uzaklığının ortancası 60,605 cm; karelerdeki aralık 60,066–61,046 cm. Kullanıcının 60 cm değeriyle ortanca fark +0,605 cm, yaklaşık %1,01. Cetvel ölçümünün belirsizliği bildirilmedi; kare aralığı hareketi de içerebilir.

Bu tek kurulum, tek mesafe ve ekran deseni kontrolüdür; 2 m hedef, uçuş mesafesi, ofset/telemetri veya santimetre isabet doğrulaması değildir. `distance-report.json` referansın kullanıcı beyanı olduğunu ve kapsamı kaydeder.

## 80 cm beyanlı iki kayıt — uyuşmazlık açık

Kullanıcı “hazır 80 cm” bildirince 18 yeni kare `imx219-distance-check-02/` içine alındı. Başlangıçta dama kadrajdan kesildiği için konumu düzeltmesi istendi. 14 geometrik uygun karede hesap ortancası 73,213 cm, aralık 69,633–76,928 cm çıktı; bu hareketli seri onay olarak kullanılmadı.

Kullanıcı tekrar “tamam 80 al hemen şimdi” dediğinde hemen 10 yeni kare `imx219-distance-check-03/` içine alındı. Dokuz kare RMS ≤1 px koşulunu sağladı; ortanca dik mesafe 71,878 cm, aralık 71,629–73,369 cm. Beyan edilen 80 cm ile fark −8,122 cm (−%10,15). İşaretli köşeler görsel olarak incelendi; kamera/model/crop önceki kayıtlarla aynı. Ham veriler ve iki ayrı `distance-report.json` korundu; uyuşmazlık gizlenmedi veya 80 cm'ye uydurmak için matris/ölçek değiştirilmedi.

Kalibrasyonun fiziksel mesafe doğrulaması tamamlanmadı. Kullanıcı lens ile dama ekranı arasını ölçtüğünü doğruladı. Kullanıcı kayıt sırasında drone'un elde tutulduğunu, neredeyse dik olduğunu ve en fazla birkaç cm yukarı/aşağı oynadığını bildirdi. Bu beyan 8 cm farkı tek başına açıklayan kanıt sayılmadı. Sonraki doğrulama, aynı sabit destekte duran drone ve ölçülmüş iki lens–ekran mesafesiyle yapılacak; tam 80 cm şart değil. Uyuşmazlığın ölçüm, düzenek, ekran ölçeği veya kalibrasyondan kaynaklandığı henüz belirlenmedi. Aday aktif uçuş yapılandırmasına geçirilmedi.

Aynı 80 cm beyanlı serinin 004. karesinde üç sayısal kontrol de yaklaşık 72 cm verdi: ITERATIVE 72,183 cm; IPPE 72,300 cm; distorsiyon sıfır sayıldığında 72,018 cm. Basit, yaklaşık önden bakış piksel ölçeği 72,388 cm. Bu yöntemler aynı kamera matrisi/desen ölçeğini paylaştığı için ortak kalibrasyon hatasını dışlamaz; yalnız tek PnP yöntemine veya distorsiyon düzeltmesine özgü bir fark görünmedi. Kanıt `imx219-distance-check-03/algorithm-crosscheck.json`.

## Sabit 80 cm kontrolü

Kullanıcı lens–dama mesafesinin tam 80 cm olduğunu ve ikisini de sabitlediğini bildirdi. Hemen 10 farklı özgün PNG alındı: `artifacts/calibration/imx219-distance-check-04/`. Kamera kare kimlikleri 90506–90842; IMX219, 1280×720 ve ScalerCrop önceki kayıtlarla aynı. İşaretli köşeler görsel olarak incelendi. **Aynı kalibrasyon matrisi ve aynı 25 mm kare ölçeği değiştirilmeden** 10 karenin tamamında uygun poz bulundu.

Ekran düzlemine dik mesafe ortancası 80,0818 cm; aralık 80,0692–80,0840 cm. 80 cm kullanıcı referansıyla fark +0,0818 cm (yaklaşık %0,102). Görüntü RMS aralığı 0,0747–0,0873 px. Bu dar kare aralığı, sabit sahnedeki hesap kararlılığıdır; cetvelin belirsizliği bilinmediğinden milimetre düzeyinde mutlak doğruluk kanıtı değildir.

Önceki yaklaşık 8 cm fark bu sabit kontrol kaydında tekrarlanmadı. Elde alınan kayıtların neden farklı çıktığı fiziksel olarak kesinleştirilmedi; veriler silinmedi ve matris o değerlere uydurulmadı. 60 cm ile bu sabit 80 cm kontrolü ekran deseni ölçeğinde uyum sağladı. Sıradaki ihtiyaç gerçek 2 m mavi hedefin kadraja sığması, planlanacak metre ölçeğindeki mesafeler ve kamera/ofset/telemetriyle birlikte hedef geometrisinin doğrulanmasıdır. 3,5 m başlangıç önerisi mevcut dar crop için hâlâ uygun kabul edilmiyor. FC/rota/kamera ayarı değiştirilmedi; uygulama gözlem modunda.

## Laptopta 15 cm mavi hedef ön kontrolü

Kullanıcının hazır bildirimi üzerine ilk 10 özgün PNG `artifacts/blue-target/screen-check-01/` içine kaydedildi. Kullanıcı mavi karenin iki kenarının 15 cm olduğunu ve kamera/ekran konumunun önceki sabit düzenle aynı kaldığını bildirdi; mesafeyi 80,8 cm diye yazdı. Önceki cetvel referansı 80 cm, hesap sonucu 80,0818 cm idi. Olası ondalık karışıklığı raporda korundu; yeni bağımsız cetvel ölçümü varsayılmadı.

İlk panel JPEG'inde `mavi_hedef 0.51` görüldü. Ham AI kutularını aynı özgün görüntüyle eşleyerek kaydetmek için gözlem PNG yanıtına kareye ait tespit, backend ve oturum üst verileri eklendi; yakalama aracı bunları `frame-NNN.json` yan dosyalarına yazıyor. Geri giden kare kimliğini/oturum değişimini reddediyor. Panel JSON'una ve olay dışı telemetri kaydına ham tespitler de eklendi. Kare/eşleşme testi güçlendirildi, 35 test geçti. Hedef kabul eşiği, aktif 2 m hedef ayarı ve kontrol mantığı değiştirilmedi.

Eski gözlem sürecinde Pixhawk bağlantı hatası ve yaklaşık 2786 s eski telemetri vardı; USB cihazı işletim sisteminde görünüyordu. Süreç SIGTERM ile temiz kapatıldı ve yeni sürüm aynı Hailo ortamından yalnız `observe` modunda başlatıldı. USB bağlantısı yeniden kuruldu; `panel-after-restart.json` örneğinde heartbeat yaşı yaklaşık 0,34 s, bağlantı hatası yok, STABILIZE/DISARM. Eski veriler güncel sayılmadı. İlk sıcaklık örneği 58,2 °C, throttled=0x0.

Yeniden başlatma sonrası `screen-check-02/` içinde 20 özgün PNG ve aynı karelerin JSON tespitleri kaydedildi (Hailo kamera kimlikleri 1313–2045). Tüm karelerde class_id=2 / mavi_hedef, skor 0,5097429. **0/20 kare kayıt sırasında geçerli 0,65 görev kabul eşiğini geçti.** Bu pozitif örnekler, gerçek hedef başarımı veya yanlış pozitif oranı ölçümü değildir; skor doğruluk yüzdesi olarak yorumlanmaz.

Düşük skorlu gerçek Hailo ROI adaylarında ikincil OpenCV kare çıkarımı ayrıca teşhis amacıyla çalıştırıldı. Kullanıcı ölçümü 0,15 m kenar ve değişmeyen kamera matrisiyle 20/20 adayda kamera göreli PnP hesaplandı: düzleme dik mesafe ortancası 81,142 cm, aralık 80,925–81,142 cm. Güncel 80,8 cm beyanıyla fark yaklaşık +0,342 cm; önceki 80 cm cetvel referansıyla +1,142 cm. Lens optik eksenlerine göre hedef merkezi yaklaşık 2,36 cm sağda / 5,49 cm görüntüde aşağıda bulundu; bu, Pixhawk duruş/konum füzyonuyla doğrulanmış quad merkezleme hatası değildir. Tam görev geometri kabulü veya kilit başarılı sayılmadı; eşik düşürülmedi.

Kanıt `artifacts/blue-target/screen-check-02/blue-report.json`, ham kareler/yan dosyalar ve güncel panel kaydıdır. Sıradaki çalışma gerçek 2 m hedef yüzeyi, negatif örnekler ve uygun görüş alanı/operasyon mesafesi doğrulamasıdır; mevcut dar crop için 3,5 m hâlâ uygun kabul edilmiyor. Aktif uygulama kalibrasyonsuz gözlem modunda; aday matris bu teşhiste yerelde kullanıldı.

## Geçici quad test eşiği — 5 Eylül 2026

Kullanıcı, eğitim brandalarının DJI drone ile beton zeminde çeşitli irtifa/açılardan çekildiğini, mevcut test sahasının beyaz taşlı olduğunu bildirdi ve AI kabul eşiğinin şimdilik düşürülmesini istedi. Veri seti incelenmedi; düşük laptop skorunun nedeni doğrulanmadı. `config/quad.json` içinde `camera.confidence_min=0.50` açıkça ayarlandı; önce genel varsayılan 0,65 kullanılıyordu. Genel sınıf varsayılanı, model/HEF, geometri, tazelik, bağımsız kare, süreli kilit, 2 m hedef ve diğer kontrol değerleri değişmedi.

`screen-check-02` yan dosyalarındaki 20/20 mavi tespit yeni skor koşulunu geçiyor. Bu yalnız skor karşılaştırmasıdır; tam görev kabulü, merkezleme, bırakma veya yanlış pozitif oranı testi değildir. Gerçek saha pozitif/negatif örnekleriyle geçici eşik yeniden değerlendirilecek.

35 mevcut test geçti (0,24 s). Yapılandırma Pi'ye aktarıldı; mevcut observe süreci DISARM/taze heartbeat doğrulandıktan sonra normal SIGTERM ile kapatılıp aynı Hailo ortamında yeniden başlatıldı (o anda PID 3422). Canlı panel API'si observe, eşik 0,50, görüntü yaşı 0,048 s, heartbeat yaşı 0,895 s ve boş pipeline/link hataları gösterdi. Kanıt `artifacts/pi/status-threshold-050-20260905.json`. Son SoC sıcaklığı 57,6 °C ve throttled=0x0. Gerçek FC parametresi/görevi değiştirilmedi, uçuş komutu gönderilmedi.

## Sahada GÖZLEM başlangıcı — 5 Eylül 2026

Kullanıcı test yerine ulaştıklarını, gerçek brandayı serdiklerini ve Windows Mission Planner'ı telemetriyle bağladıklarını bildirdi. Geçici bağlantı kesintisinden sonra kullanıcının tekrar deneme isteğiyle `172.20.10.4` SSH bağlantısı kuruldu. Çalışan Görev 2 uygulaması bulunmadı; önceki USB kimliğine sahip Pixhawk seri cihazı görüldü. GÖZLEM, mevcut proje ve Hailo ortamı değiştirilmeden launcher ile başlatıldı; o anda PID 2174, log `runtime/field-observe-20260905T074141Z.log`. Başlatma öncesi sıcaklık 46,1 °C, throttled=0x0.

Canlı panel ve eşlenmiş özgün PNG/AI yan dosyası `artifacts/field/20260905-observe-start/` içine kaydedildi. Gerçek HAILO, IMX219, 1280 × 720 ve önceki crop; eşik 0,50, kalibrasyon dosyası hâlâ null. ArduCopter 4.5.7, STABILIZE/DISARM, GPS fix=3, 11 uydu, HDOP 1,32; taze duruş/yerel konum/heartbeat ve boş pipeline/link hataları. RC sağlıksız; kullanıcı kumandanın kapalı olduğunu bildirdi. Batarya telemetrisi 12,52 V; quad bataryasının hücre sayısı henüz bilinmiyor. İlk PNG'de yakın, bulanık yüzey görülüyor; tam gerçek hedef doğrulaması sayılmadı.

Sıradaki fiziksel kontrol kumanda açıldıktan sonra DISARM Loiter geçişi, Mission Planner PreArm uyarıları ve batarya/saha durumudur. Panelin başlangıç TAKEOFF uyarısı özel AUTO görev denetimidir; FC'nin bütün PreArm sonuçlarını veya Loiter hazırlığını temsil etmez. Saha uçuşu/temsili bırakma henüz kaydedilmedi. Kamera, eşik, FC parametresi ve görev değişmedi; uçuş komutu gönderilmedi. Bu başlatmada kod değişmediği için yazılım testleri yeniden çalıştırılmadı.


## İlk gerçek branda uçuş kaydı incelendi — 5 Eylül 2026

Kullanıcı yapılan uçuşun kaydedilip kaydedilmediğini sordu. Pi yeniden erişilebilir olunca yerel kaydedicide 11:00:08–11:01:29 (Türkiye saati) ARM–DISARM aralığından 81 özgün PNG ve aynı karelerin Hailo JSON'ları bulundu. Kaydedici DISARM görülünce normal tamamlanmış; hata kaydı boş. 81 kare kimliği farklı, akış aynı. Mac'te `artifacts/field/flight-01/` içine kopyalanan 168 kaynak dosyanın SHA256 değerleri eşleşti. 179 durum örneği ve uçuş çevresinden 503 uygulama telemetri satırı da korundu. ARM aralığındaki mod LOITER; ALT_HOLD örnekleri ARM öncesinde.

54 karede 63 mavi kutu, skor ortancası 0,4158. Yalnız dört kare 0,50 skor eşiğini geçti; 0,65'i geçen yok. Özgün görüntü incelemesinde 017'de mavi kutunun insan gölgesini işaretlediği görüldü; mevcut OpenCV dört köşeli aday üretmedi. 032/035/036'daki yüksek skorlu branda adayları kadraj kenarından kesildiği için kenar payı koşulunu geçmedi. Mevcut kodun skor + köşe/sınır/doluluk ön koşullarını birlikte geçen aday bu 81 karede yok. Skordan bağımsız teşhis için incelenen sekiz düşük skorlu aday geometri ön koşullarını geçti; eşik değiştirilmedi.

Bu yaklaşık 1 Hz görüntü örneklemesi bütün kamera akışını/görev kilidini doğrulamaz. PnP, zaman eşlenmiş araç merkezleme veya bağımsız fiziksel mesafe bu incelemede test edilmedi. Rapor `docs/FIELD_FLIGHT_01.md`, sayısal sonuç `flight-report.json`, geometri ayrıntısı `geometry-screening.json`. Otonom uçuşa hazır olma sonucu üretilmedi. Kullanıcıya mevcut kayıt üzerinden çalışılabileceği ve bu inceleme için tekrar uçuş gerekmediği bildirildi. Son dosya incelemesinde SSH vardı, localhost 8080 bağlantısı reddedildi ve GÖZLEM süreci yoktu; uygulama yeniden açılmadı.
