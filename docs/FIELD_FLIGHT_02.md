# Görev 2 — Loiter → AUTO uçuş incelemesi

5 Eylül 2026. **Model gölgeye kutu çizdi; uygulama hedef etkileşimine geçmedi. GUIDED, merkezleme, bırakma ve bırakma sonrası RTL gerçekleşmedi.** Bu uçuş görev başarısı değildir.

## Kanıt

Pi kaydı `runtime/recordings/20260905T113439Z-3787/`. ARM görülen örnekler Türkiye saati 15:00:19,734–15:01:30,433; yaklaşık 70,7 saniye. ARM aralığı kalkış öncesi/iniş sonrası örnekleri de içerir. Mac: `artifacts/field/flight-02/`. Üç 30 saniyelik MKV, ARM API kesiti, video indeksi, seçim/tespit JSON'ları, kapanmış uygulama telemetrisi ve SQLite olay yedeği alındı. Dokuz dosyanın Pi SHA256 değeri doğrulandı (`hash-verification.json`). Kaynaklar korunuyor.

| Ölçüm | Sonuç |
|---|---:|
| ARM API örneği | 354 |
| API mod örnekleri | 63 LOITER / 291 AUTO |
| API mavi kutu | 45 |
| Ayrı uygulama logunda ARM örneği / mavi kutu | 354 / 46 |
| Uygulama logunda skor ≥0,50 mavi kutu | 10 |
| Her iki kayıtta örneklenmiş geçerli hedef | 0 |
| Uygulama logunda örneklenmiş kontrol eylemi | 0 |
| Olay defteri | WAIT_AUTO → SEARCHING → PILOT_CONTROL |
| ARM API örneklerinde hatalı pipeline | 0 |
| Örneklenmiş en düşük kamera işleme hızı | 29,87 FPS |
| En yüksek HOME'a göre irtifa | 10,446 m |

API ve uygulama logu bağımsız yaklaşık 5 Hz örneklenir; kutu sayıları aynı olmak zorunda değildir. Olay defterinde GUIDED veya temsili bırakma olayı yok. Bu sayıların bütün 30 FPS çıkarımlarını kapsadığı iddia edilmez. HOME'a göre irtifa bağımsız lens–zemin mesafesi değildir.

## Görüntü bulguları

Üç videonun birer saniyelik 90 önizlemesi ve 45 API adayına zamanca en yakın video kareleri gözle incelendi. Görsel etiketler `visual-review.json`; genel sayfalar `contact-51/52/53.jpg`, aday sayfaları `candidates-0/1/2.jpg`, karşılaştırma `findings.jpg`.

- Kalkış sırasında bankın gölgesine mavi kutu çiziliyor. AUTO sonuna yakın insan gölgesinde de düşük skorlu mavi kutular var. Bunlar gerçek branda değil; loglarda kabul edilmiş hedef yok.
- Branda gerçekten görünüyor. Yakın tam görünümün API örnekleri fid9593/9599: skor 0,4158/0,4191, aktif 0,50 altında. Panel videosundaki yakın tam görüntülerde de düşük skor var.
- Eşik üstü AUTO örnekleri fid9803/9809/10139: skor 0,5097, kutu alt sınırı özgün normalize koordinatta 1'i aşıyor. Yakın video kareleri brandanın sağ/alt kadrajdan kesildiğini gösteriyor. Bunlar tam hedef/mesafe hesabını doğrulamaz.
- Video ile API aynı anda farklı kamera karelerini örnekleyebilir. `visual-review.json` iki kaynak kimliğini ve zaman farkını korur. Video JPEG'i sıkıştırılmış/ölçeklenmiş ve kutularla işaretlidir; buradan özgün PNG varmış gibi tam geometri tekrar oynatma yapılmadı. Eski yazılım ret alt nedenlerini kaydetmediğinden, bu uçuşa sonradan ölçülmüş kesin OpenCV ret nedeni atanmıyor.

## Uygulanan revizyon

Kayıt görüntüsündeki ham mavi kutu, görev tarafından kabul edilmiş hedef gibi anlaşılabiliyordu. Kutulara **AI ADAYI** ibaresi eklendi. Geometri doğrulama döngüsü her aday için skor, sınıf, dört köşe bulunamaması, kenar payı, doluluk veya metrik geometri ret bilgisini üretir; API ve uygulama JSONL kayıtlarına aynı kareyle yazılır. Panel genel “bekleniyor” yerine mevcut ret nedenlerini gösterir. Skor eşiğinde elenen aday için diğer aşamalar çalıştırılmış gibi rapor verilmez. Geometri kabulü ayrıca zamansal görev kilidi gerektiğini belirtir. RTL durumlarının panelde Türkçe isimleri tamamlandı.

Kabul koşulları, model, 0,50 eşiği, kamera/crop, uçuş hareket mantığı, FC parametreleri ve rota değişmedi. Yeniden eğitim yapılmadı. Dedektörün yanlış gölge kutusu bu revizyonla giderilmiş sayılmaz. Kayıt bu sorunu çözen bir yazılım hatası kanıtlamadı; eşiği düşürmek veya kesik brandayı tam kabul etmek uygulanmadı.

75 test geçti; normal ortamda Torch bulunmadığından dört model testi atlandı. Yeni regresyon aynı sentetik hedefin teşhis açık/kapalı kabulünün birebir aynı kaldığını ve düşük skor/köşesiz görüntü retlerini doğruladı. Kanıt `tests-diagnostics.txt`.

Pi'de taze DISARM/landed=1 ve observe doğrulandıktan sonra eski kod `runtime/before-flight02-diagnostics/` içine yedeklendi, beş dosya güncellendi ve **yalnız GÖZLEM** yeniden açıldı. Yeni PID 4307; log `runtime/post-flight-02-diagnostics.log`. Dağıtım ve son canlı kontrol dosyaları bu inceleme klasöründe. Eski uçuş PID4029 ve kayıt PID3787 kapalıdır; sonraki uçuş için kayıt yeniden başlatılmalıdır. Kayıt toplam 15485 video karesiyle temiz tamamlandı; hazırlıktaki kapalı uygulama aralıklarını da içeren 653 API hata sayacı sıfırmış gibi sunulmaz. Pixhawk DataFlash BIN indirilmedi.

## Sonraki karar

Sıradaki saha değerlendirmesinde tam brandanın kadraj içinde kalması ve yeterli skorla sürekli geçerli hedef oluşması gösterilmeli. Mevcut kayıtta düşük skor ve kesik kadraj birlikte engel; yalnız kontrol kodunu değiştirerek görev başarısı vaat edilemez. Bu inceleme yeni uçuş veya kontrol başlatmadı. Gerçek merkezleme, 9 m lens yüksekliği, temsili bırakma ve RTL henüz uçuşta doğrulanmadı.
