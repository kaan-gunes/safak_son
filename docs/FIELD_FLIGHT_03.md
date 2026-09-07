# 0,40 eşikli deneme — model gördü, devralma kilitliydi

5 Eylül 2026. **Bu kayıt yalnız modelin düşük başarımıyla açıklanamaz. Pilot devri kilidi devralmayı engellemiş; ayrıca skor eşiğini geçen görüntüler geometri kontrollerinde reddedilmiştir.** GUIDED merkezleme, alçalma veya temsili bırakma yapılmadı. Bu incelemede kod/eşik/FC/rota değiştirilmedi.

## Oturum ve zaman çizgisi

Batarya değişiminden sonra açılan uygulama PID2239, sortie `3ac323c5966b402388a836bec57ac80e`; kayıt PID2312, `runtime/recordings/20260905T123707Z-2312/`. Aynı uygulama çalıştırmasında iki ARM aralığı görüldü. Türkiye saati:

| Zaman | Kaydedilen durum |
|---|---|
| 15:38:08,611 | İlk ARM, LOITER |
| 15:38:26,461 | AUTO; HOME'a göre yaklaşık 3,65 m, 9,5 m devralma alt sınırının altında |
| 15:38:31,885 | LOITER, yaklaşık 8,33 m; “Pilot kontrolü geri aldı; bu çalıştırmada tekrar devralınmaz” |
| 15:38:52,564 | DISARM |
| 15:39:11,419 | İkinci ARM; uygulama yeniden başlatılmamış, pilot devri kilidi korunmuş |
| 15:39:20,445 | AUTO, yaklaşık 2,18 m; kilit hâlâ etkin |
| 15:39:23,856 | LOITER |
| 15:39:32,487 | Tekrar AUTO; sonrasında yaklaşık 10 m tarama, fakat kilit hâlâ etkin |
| 15:40:25,464 | DISARM |

`MavlinkLink.ingest/RC_CHANNELS` içinde armed/AUTO iken pilotun mod anahtarı değişmesi `pilot_override=True` yapar. Bu bayrak aynı süreçte DISARM/ARM veya tekrar AUTO ile sıfırlanmaz. Kullanıcının önceki “Loiter'a çekince tamamen kontrol bende olsun” talebiyle uygulanan davranıştır. İlk AUTO'da devralma yüksekliğine ulaşmadan Loiter'a dönülmüş; ikinci kalkışta kilit zaten açıktır. Kilit kaldırılmış olsa görev kesin başarılırdı sonucu çıkarılamaz, çünkü geometri de hedef kabul etmemiştir.

## Algılama ve retler

Yaklaşık 5 Hz uygulama logundaki ARM durumunda 588 örnek/588 farklı kaynak kare kimliği değerlendirildi:

| Ölçüm | Sayı |
|---|---:|
| Mavi AI kutusu | 87 |
| 0,40 skor eşiğini geçen mavi kutu | 42 |
| Skor altında kalan mavi kutu | 45 |
| Eşik üstü: kadraj kenarı retleri | 31 |
| Eşik üstü: dört köşe bulunamaması | 8 |
| Eşik üstü: metrik geometri retleri | 3 |
| Geçerli metrik hedef | 0 |

İki ek mavi olmayan sınıf reddi ayrı kaydedildi. Bu sayılar bütün 30 FPS çıkarımların veya saha geneli doğruluğun ölçümü değildir. Karar durumu 588 ARM örneğinde WAIT_AUTO kaldı; 439 örneğin açıklaması pilot devri kilidiydi. Bu, programın donduğu anlamına gelmiyor: yeni kare ve retler işlemeye devam etmiş. Ancak panelin büyük durum yazısının WAIT_AUTO kalması kilidi yeterince açık göstermiyor; açıklama alanındaki kilit bilgisi durum başlığına da taşınmalı. Bu bir görünürlük eksikliğidir; kilidin kaldırılması önerilmez.

Metrik ret örnekleri:

- 15:39:51,145, fid4940, skor0,4124.
- 15:39:57,966, fid5145, skor0,4318.
- 15:40:09,606, fid5494, skor0,4191.

Son iki örneğe yakın panel video karelerinde gerçek branda bütün olarak görünüyor. Dolayısıyla “hiç görmedi” veya “bütün hedefler kesikti” doğru değil. `metric_geometry` köşe/sınır aşaması sonrasında metrik çözümün kabul edilmediğini gösterir; mevcut kayıt poz çözümündeki eğim, reprojeksiyon veya belirsizlik alt nedenini saklamıyor. Kesin alt neden BİLİNMİYOR. Kamera kalibrasyonu bozuk veya model tek neden diye hüküm verilemez.

## Kayıt ve inceleme sınırı

`artifacts/field/flight-03/`: uygulama/ARM logu, SQLite olay yedeği, durum, özet, video indeksi ve manifest. İlgili 0005/0006 videoları (60 saniye) Mac'e alındı; 60 adet 1 Hz genel önizleme ve üç metrik ret çevresi büyütülerek gözle incelendi. Toplam dokuz alınmış dosyanın Pi SHA256'sı eşleşti. İlk ARM bölümlerini içeren 0001–0004 videoları Pi'de korunuyor; Mac'e alınmış veya gözle incelenmiş sayılmadı. `hash-verification.json` yerel doğrulanan/uzakta kalan dosyaları ayrı listeler.

`metric-0/1/2.jpg` özgün Hailo girişleri değildir: 960×540 JPEG kamera + HUD video kaydından çıkarılmış görüntülerdir. Video kaynak kimlikleri4937/5144/5493, log kimlikleri4940/5145/5494; eşleşme zaman yakınlığıdır, aynı çıkarım karesi değildir. Bu yüzden video üstündeki skor logla birebir eşit varsayılmaz. Üçüncü video karesindeki veri yaşı uyarısı korundu. Bu dosyalar üzerinden özgün köşeler yeniden ölçülmüş gibi gösterilmedi. Eşleme `video-matches.json`.

İnceleme başında taze DISARM/landed1 doğrulandı; kaydediciye SIGTERM ile temiz kapanış verildi. Video kaydı artık kapalı. Uygulama flight modunda aynı PID2239/sortie ile bırakıldı; pilot devri kilidi aynı süreçte kalıcı. Yeni kontrol/uçuş başlatılmadı; sonraki işlemde canlı durum yeniden okunmalı.

## Sonraki iş

1. Pilot devri kilidini panel durum başlığında açık göstermek; yeni denemeyi yalnız yerde yeni uygulama oturumuyla hazırlamak. Havada kilit sıfırlanmaz.
2. Üç metrik ret için köşe ve PnP alt nedenlerini aynı özgün kareyle kaydederek ayırmak. Geometri koşullarını neden bilinmeden gevşetmemek.
3. Kullanıcının planladığı yeni kameraya geçişte o kameraya özgü kalibrasyon ve gerçek hedef/mesafe kontrolünü yapmak. Model çalışması bundan ayrı değerlendirilmeli.

Bu uçuş eşiğin düşürülmesinin tek başına yeterli olmadığını gösteriyor. Sürekli kilit, 9 m mesafe doğruluğu, bırakma veya RTL başarısı henüz kanıtlanmadı.
