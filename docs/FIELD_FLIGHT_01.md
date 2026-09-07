> 5 Eylül 2026 sonraki inceleme: Bu kaydın Hailo/TAPPAS/doğrudan HailoRT karşılaştırması tamamlandı. 81/81 giriş tensörü doğrulandı ve ham NMS sonuçları birebir eşleşti; 0,5097429156 HEF çıkışında da var. Uygulama hatası kanıtlanmadı, eşik 0,50 kaldı. Ayrıntı: [DETECTION_REPLAY.md](DETECTION_REPLAY.md).

# Görev 2 — ilk gerçek hedef uçuş kaydı

5 Eylül 2026. **Uçuş kaydı bulundu ve Mac'e eksiksiz kopyalandı. Bu inceleme için tekrar uçuş gerekmiyor.**

## Kayıt ve kapsam

Pi'de `runtime/field/20260905T075830Z-loiter/` altında çalışan yerel kaydedici 11:00:08'de ARM, 11:01:29'da DISARM gördü (Türkiye saati). Yaklaşık 81 saniyede 81 özgün 1280 × 720 PNG ve aynı karelere ait Hailo sınıf/skor/kutu JSON'u yazıldı. 81 kare kimliği farklı, kamera oturumu aynı. Bunlar yaklaşık 1 Hz görüntü örnekleridir; sürekli video veya bütün 30 FPS kamera akışı değildir.

Mac kopyası: `artifacts/field/flight-01/`. Pi'de oluşturulan manifestodaki 168 dosyanın SHA256 değerleri Mac'te eşleşti. Yakalama olayları, 179 durum örneği, kayıt betiği ve uçuş çevresinden 503 satırlık uygulama telemetri kesiti de korundu. JSON sonuç: `flight-report.json`; geometri incelemesi: `geometry-screening.json`.

ARM aralığındaki kaydedilmiş telemetri LOITER gösteriyor; uygulama GÖZLEM modundaydı. Kayıt dosyasındaki ALT_HOLD örnekleri ARM öncesindedir. Gerçek görev devralma, GUIDED merkezleme/alçalma veya temsili bırakma yapılmadı. Home'a göre irtifa bağımsız lens–zemin mesafesi kabul edilmedi.

## Bulgular

81 görüntünün tamamı üç toplu inceleme sayfasında gözden geçirildi; kritik 017 ve 035 kareleri özgün boyutta ayrıca incelendi.

| Ölçüt | Sonuç |
|---|---:|
| En az bir mavi tespit içeren kare | 54 / 81 |
| Toplam mavi kutu | 63 |
| Mavi skor aralığı / ortancası | 0,2519–0,5097 / 0,4158 |
| En az bir mavi kutunun 0,50 eşiğini geçtiği kare | 4 |
| 0,65 eşiğini geçen mavi kutu | 0 |
| Skordan bağımsız teşhiste OpenCV köşe + sınır + doluluk koşuluna uyan mavi aday | 8 |
| Hem 0,50 skor hem bu geometri ön koşullarını geçen aday | 0 |

Bu sayılar örneklenen kaydın özetidir; veri seti doğruluğu, precision/recall veya bütün uçuş boyunca hedef bulma oranı değildir. Hedefe yaklaşma, hedefin kadraj dışında kalması ve iniş görüntüleri de 81 kareye dahildir.

Eşiği geçen dört kare ayrı incelendi:

| Kare | Görsel bulgu | Mevcut kodla çevrimdışı kontrol |
|---|---|---|
| `frame-017` | 0,5097 mavi kutu insan gölgesini işaretliyor | OpenCV dört köşeli aday bulamadı |
| `frame-032` | Mavi branda alt kadraj sınırından kesiliyor | Köşeler y=719'a dayanıyor; 12 px kenar payı koşulu reddediyor |
| `frame-035` | Mavi branda üst kadraj sınırından kesiliyor | Köşe y=0; kenar payı koşulu reddediyor |
| `frame-036` | Mavi branda üst kadraj sınırından kesiliyor | Köşeler y=0; kenar payı koşulu reddediyor |

`frame-007` içinde ahşap yüzey üzerinde 0,3198 skorlu kırmızı kutu da var. Bu gerçek kırmızı hedef doğrulaması değildir.

Tam köşe/sınır/doluluk adayları 028, 034, 037, 038, 039, 040, 041 ve 046 karelerinde bulundu; skorları 0,4158–0,4878 aralığında, geçici 0,50 eşiğinin altında. Bunlar düşük skorlu adayların **teşhis amacıyla** mevcut OpenCV koduna verilmesinin sonucudur. Aktif eşik değiştirilmedi.

## Sonuç ve sonraki iş

Kayıt, gerçek brandanın görüntüsünü ve gerçek sahnedeki yanlış tespit örneklerini içeriyor. Mevcut 81 karede skor ve geometri ön koşulları aynı anda sağlanmadı. Bu sonuç, tüm uçuş karelerinin aynı koşulları sağlayamadığını kanıtlamaz; seyrek kayıt görev kilidi testinin yerine geçmez. PnP, çekim anıyla eşlenmiş araç merkezi ve bağımsız fiziksel mesafe bu raporda doğrulanmadı.

Sıradaki iş bu kayıt üzerinden model giriş/çıkış zincirini ve yanlış gölge tespitini incelemek. Özellikle farklı sahnelerde aynı 0,5097429 en yüksek skorunun görülmesi açıklanmamıştır; bundan doğrudan model bozukluğu veya belirli bir ön işleme hatası sonucu çıkarılmadı. Sırf bu uçuşta skorlar düşük diye eşik tekrar düşürülmeyecek. Kontrol kodu, HEF, kalibrasyon/crop ve FC görevi/parametreleri değiştirilmedi.

Dosyalar incelenirken Pi'ye SSH erişimi vardı fakat localhost 8080 bağlantısı reddedildi ve GÖZLEM süreci bulunmadı; mevcut kayıt güvenceye alındı, uygulama yeniden başlatılmadı. Sonraki canlı çalışma öncesinde yeniden GÖZLEM başlatılıp doğrulanmalı.

Görsel inceleme sayfaları: `artifacts/field/flight-01/contact-1.jpg`, `contact-2.jpg`, `contact-3.jpg`. Özgün PNG'ler değiştirilmedi.
