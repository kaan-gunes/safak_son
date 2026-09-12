# 11 Eylül — ana görev hedeflerde neden durmadı?

Son iki gerçek ana uçuş incelendi: 12:47 (`competition-5b7d890366c6477f9c087166e1d72c88.jsonl`) ve 12:53 (`competition-f3f53397f11d4991b495ae0373212212.jsonl`). Kaynakların kopyaları, SHA256 değerleri, salt okunur rota sonucu ve test çıktıları `artifacts/center-investigation-20260911/` altında.

## Kök neden

Her iki uçuşta araç AUTO kalkış/giriş sırasında tanımlı uçuş poligonunun dışındaydı. `DualController.step()` AUTO oturumunu başlatır başlatmaz, giriş kapısı henüz geçilmemişken poligon kontrolünde kalıcı `ABORTED` durumuna giriyordu. Daha sonra poligona girip doğru yönde giriş kapısını geçmek bu kilidi açmıyordu. Bu nedenle hedef arama ve GUIDED duruş isteği hiç çalışmadı.

12:47 uçuşunda 22 mavi + 25 kırmızı, 12:53 uçuşunda 23 mavi + 26 kırmızı tespit kaydedilmiş. Sorun bu uçuşlarda hedefleri görememek veya PnP'nin duruşu engellemesi değil; hedef seçimine hiç ulaşılmaması.

Önceki 12:40 uçuşundaki parmak izi uyuşmazlığı ayrı bir olaydır. FC rotası bu incelemede yeniden salt okunur okundu: TAKEOFF ve 2–8 tarama waypointleri 15 m, LAND 9; digest `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707`, ana profille eşleşiyor. Rota/profil kimliği değiştirilmedi.

## Düzeltme ve sınırlar

Giriş kapıları tamamlanmamış ve merkezleme alt kontrolcüsü henüz oluşturulmamışsa, poligon dışı konum artık komutsuz bekleme üretir. AUTO giriş rotasını FC yürütür; uygulama hedef birikimini sıfırlar. Kapı, poligon, tarama sırası ve irtifa şartları tamamlanınca normal arama başlar. Girişten sonra alan dışına çıkmak hâlâ kalıcı iptaldir; MAVLink katmanındaki poligon denetimi değişmedi. Pilot müdahalesi ve havada yeniden başlatma kilitleri korunur. Ortak akıştaki bu düzeltme iki stratejide de geçerli; merkezleme, servo ve hızlı bırakma eşikleri değişmedi.

## Kanıt

`tests/fixtures/entry-polygon-20260911.json` gerçek telemetri ve adayların kalkıştan pilot müdahalesine kadar olan kesitlerini, kaynak hashlerini, profil geometrisini ve okunan rotayı içerir. Testler kapı geçişini elle onaylamaz; kaydedilmiş koordinatlar üzerinden hesaplar. Her renk bağımsız oynatılır ve ilk duruş isteğinde durulur: AUTO uçuş kaydı GUIDED sonrası hareketi doğrulayamaz.

| Uçuş | Mavi hedefte duruş isteği (monotonic s) | Kırmızı hedefte duruş isteği (monotonic s) |
|---|---:|---:|
| 12:47 | 708,387 / seq4 | 712,606 / seq5 |
| 12:53 | 112,593 / seq4 | 116,212 / seq5 |

Dokuz yeni test: dört gerçek kayıt/renk senaryosu; iki stratejide dışarıda ve kapı öncesinde komutsuz bekleme; taramada ve frenlemede alan dışına çıkışta kalıcı iptal; beklemede pilot müdahalesi. Eski kodla 7 başarısız / 2 başarılı, düzeltmeyle 9 başarılı. Tüm yerel testler: **305 başarılı, 5 atlandı** (Torch/MOSSE ortamları eksik). Pi'nin mevcut test dizisi: **263 başarılı**. Yerel ve Pi'deki değişiklik öncesi controller hashleri aynıydı. Yedek iki tarafta `runtime/before-entry-polygon-20260911/`.

## Merkezleme için kalan saha ölçümü

Bu iki uçuşta AUTO geçişindeki kaydedilmiş geometri değerlendirmelerinden 3/15 ve 7/31 kabul edilmiş (toplam 10/46, yaklaşık %22). Reddedilenler: 5 `no_corners`, 28 `metric_geometry`, 3 `border`. Bunlar seyrek JSONL örnekleridir, tüm kamera karelerinin oranı değildir. Araç hiç durmadığı için bu veriden duruş sonrası PnP başarımı veya merkezleme/bırakma sonucu çıkarılamaz; %40 benzetim eşiğiyle doğrudan saha kabul karşılaştırması yapılmaz.

Duruş isteği hatası kayıt tekrarında düzeldi; gerçek GUIDED duruşu, merkezleme ve yük bırakma bu değişiklikle henüz uçulmadı. Kamera kalibrasyonunun deneysel statüsü devam ediyor. Sonraki ana uçuşta özellikle STOPPING/VERIFYING/INTERCEPT geometri verileri ölçülmeli. İncelemede görev/kayıt uygulaması başlatılmadı; ARM, uçuş modu, servo veya FC parametre yazımı yapılmadı.
