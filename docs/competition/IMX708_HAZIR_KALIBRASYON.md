# IMX708 hazır kalibrasyon araştırması — 8 Eylül 2026

Kullanıcı yeni dama kalibrasyonu yapacak zaman/ortam olmadığını bildirdi. Yeni çekim istenmedi. İnternet araştırmasında mevcut kameraya doğrudan doğrulanmış kalibrasyon sayılabilecek evrensel bir IMX708 PnP matrisi bulunmadı.

[Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/) standart/geniş açılı ve IR filtreli/filtresiz çeşitlere sahiptir; sensör adının aynı olması lensin aynı olduğunu tek başına göstermez. [Resmî Pi 5 IMX708 tuning dosyası](https://github.com/raspberrypi/libcamera/blob/main/src/ipa/rpi/pisp/data/imx708.json) pozlama, renk, lens gölgeleme ve odak işleme ayarları içerir; uygulamanın istediği `camera_matrix`/`distortion` PnP kalibrasyonu değildir.

[OpenCV kalibrasyon belgesi](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) kamera matrisinin belirli kameraya özgü olduğunu açıklar. Başka bir kameradan alınan değerleri kendi kameramızda ölçülmüş gibi kabul edemeyiz. Teknik lens/FOV değerinden yaklaşık matris üretmek de ölçülmüş distorsiyon ve metrik doğruluk sağlamaz.

## Eldeki daha uygun aday

Projedeki `config/camera.imx708-candidate.json`, 5 Eylül IMX708 çekiminden üretilmiştir: 40 kare/8 poz, RMS 0,1388 px; 1280×720, tam crop 4608×2592, sensör modu 2304×1296, sabit LensPosition 0,1062771082. `physical_distance_verified=false`; görev mesafesinde kabul edilmemiştir. Yeni çekim yapmadan değerlendirilebilecek ilk aday budur. İnternetteki başka cihaz matrisine göre kendi geçmiş çekimimize dayanması avantajdır; bugünkü fiziksel kamera/odak için geçerliliği hâlâ bilinmiyor.

8 Eylül canlı kamera/Hailo testi hızlı profilin LensPosition 0,1 ayarında yapıldı; bunu adayın 0,1062771082 odağıyla birebir eşleşmiş saymadık. Ana profil veya kalibrasyon dosyası bu araştırmada değiştirilmedi. 180° montaj düzeltmesi önceki turda ayrı geometri dönüşümüne işlendi; kamera matrisini görüntüyle birlikte keyfî çevirmeyi gerektirmez.

Hızlı görev PnP kullanmaz, kamera kalibrasyonu bu seçenek için zorunlu değildir. Ana görevin eski IMX219 matrisini IMX708'e aitmiş gibi kullanmak uygun değildir; hazır aday kullanımı da saha doğrulaması yapılmış anlamına gelmez.

## Kullanıcının diğer açıklamaları

Saha rotası yarışma anında verilecek ve Mission Planner'dan girilecek. Şimdi koordinat beklenmiyor. Yazılım FC'den rotayı okur; tarama waypoint aralığı, giriş/bitiş kapıları ve uçuş alanı o zaman eşlenir. Bunlar programın rotayı yeniden çizmesi için değil, hedefte devralmayı izinli bölüme sınırlamak ve aynı waypoint'e dönmek içindir.

“Gerçek hex” kullanıcının altı motorlu yarışma aracıdır. Önceki quad/simülasyon sonuçları onun üzerinde ölçülmüş hız/fren mesafesi veya merkezleme başarısı değildir. Yük mekanizması şu anda takılı değil; kullanıcı sonraki adımda canlı servo testi istiyor, bu turda servo komutu gönderilmedi.
