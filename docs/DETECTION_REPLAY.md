# Görev 2 — 81 kayıtlı kareyle tespit hattı incelemesi

5 Eylül 2026. **0,5097429156303406 skoru mevcut HEF'in erişilebilir NMS çıktısında da var.** Aynı gerçek giriş tensörünün TAPPAS ve doğrudan HailoRT sonuçları 81/81 karede eşleşti. Bu incelemede renk sırası, letterbox, sınıf eşlemesi veya skor çözümlemesinde uygulama hatası kanıtlanmadı. Skoru değiştiren düzeltme, ek sigmoid, çarpan veya eşik değişikliği yapılmadı. Gölge yanlış tespiti devam ediyor; mevcut ikincil kontrol onu reddediyor.

Bu sonuç HEF öncesindeki eğitim, dışa aktarma, kuantizasyon ve derleme aşamalarını birbirinden ayırmaz. Sinir ağının gölgeyi neden bu sınıfa koyduğunun kesin nedeni **BİLİNMİYOR**. Yeniden eğitim ayrı aşamadır.

## Kaynak ve görsel etiketleme

Kaynak `artifacts/field/flight-01/`: 81 özgün 1280 × 720 PNG, eşlenmiş JSON ve `sha256-manifest.json`. Manifestodaki **168 dosya** hem yerel incelemede hem Pi tekrar oynatmasında kontrol edildi. Kaynak kayıtların üzerine yazılmadı. 81 kare kimliği farklı; aynı kamera oturumu. Görüntüler yaklaşık 1 Hz örneklerdir.

Her kare altılı, 640 × 360 inceleme kopyalarında tek tek görsel olarak incelendi; ardından elle işaretlenen yaklaşık kutular toplu görsellerde yeniden kontrol edildi. [Etiket dosyası](replay/flight-01-annotations.json), her kare için PNG hash'i, kategori, görünen branda kutusu ve belirlenen yanlış tespitleri içerir. Kesik hedefin kutusu yalnız görünen parçayı kapsar; görünmeyen kenarlar tahmin edilmedi. Bunlar hassas eğitim/IoU etiketleri değildir.

| Görsel kategori | Kare |
|---|---:|
| Tam branda | 9 |
| Kesilmiş branda | 47 |
| Görünen alanda branda yok | 24 |
| Belirsiz: 015'te çok ince üst kenar parçası | 1 |

Tam görünenler: 028, 031, 034, 037, 038, 039, 040, 041, 046. `031` görsel olarak tamdır ama gerekli 12 px kenar payını sağlayamaz. “Tam görünür” ile “yazılımın geometri ön koşulunu geçer” aynı şey değildir. Belirsiz 015 üzerinden başarı hesabı yapılmadı; bu çalışmada precision/recall veya saha geneli başarı oranı hesaplanmadı.

## Pi'de gerçekten okunan ve ölçülen hat

Pi'deki mevcut canlı `hailo_backend.py` ile yerel dosyanın SHA256'sı eşleşti. Mevcut uygulama başlatılmadı; dosya oynatıcı ayrı `/home/furkan/Desktop/safak-gorev2-replay-20260905` klasöründe çalıştı. Mevcut HEF'e salt okunur sembolik bağlantı kullanıldı. Kamera, MAVLink, görev denetleyicisi ve panel açılmadı.

- HailoRT / Python bindings: **4.20.0**; Debian paketi `hailo-tappas-core`: **3.31.0+1-1**; GStreamer: **1.22.0**.
- Gerçekte seçilen postprocess: `/usr/local/hailo/resources/so/libyolo_hailortpp_postprocess.so`; SHA256 `9c679b764cdf4d47c0f4d9747af9344db7d4f578a01de80ced7452b60b6217a7`.
- Bu kaynak `.so`, `/usr/lib/.../libyolo_hailortpp_post.so` ile aynı hash'e sahip değildir. Paketle gelen C++ kaynağı yardımcı referanstır; seçilen ikilinin birebir derleme kaynağı olarak sunulmamıştır. Çalıştırılan ikili üzerinde doğrudan sayısal karşılaştırma yapıldı.
- HEF SHA256: `b43dfac55acae45ce5db26301b6b7e9d63dc9be64e77a2f5069566068db45291`. Tek giriş `safak_v2/input_layer1`, tek dışa açık çıkış `safak_v2/yolov8_nms_postprocess`.
- PNG OpenCV tarafından BGR okunur; canlı dosyadakiyle aynı BGR→RGB dönüşümü uygulanır. Hailonet sink pad'inde **RGB / 640 × 640 × 3 / UINT8** gerçek tensör kopyalanır.
- Kurulu `INFERENCE_PIPELINE_WRAPPER`: `use-letterbox=true`, `resize-method=inter-area`, `internal-offset=true`. Ölçülen dönüşüm: **1280 × 720 → 640 × 360**, üst/alt **140 px**, doldurma **[114,114,114]**. Bu işlemi uygulayan referans tensör, 81 gerçek girişle **bayt bayt aynı** çıktı. Başka boyut/yerleşim sessizce aynı kabul edilmez.
- Hailonet NMS eşikleri **0,25 / IoU 0,7**, FLOAT32 çıktı. Görev adayı eşiği ayrıca **0,50**. İkisi farklı işlevlerdir.
- Model indeksleri `0/1`; uygulamada TAPPAS kimlikleri `1/2`, etiketler `kirmizi_hedef/mavi_hedef`. Her çıktı bu eşlemeyle denetlendi. Bu veri gerçek kırmızı hedef doğrulaması içermez.

Kurulu yardımcı Python dosyaları ve HailoRT kaynağı `artifacts/replay/pi-sources/` altında korundu. Paket/sıcaklık incelemesi ve kaynak hash'leri de oradadır. HailoRT çağrıları kurulu kaynağa göre uyarlandı; [resmî HailoRT Python arayüzü](https://github.com/hailo-ai/hailort/blob/v4.20.0/hailort/libhailort/bindings/python/platform/hailo_platform/pyhailort/pyhailort.py) referans alındı.

## Kare eşlemesi ve NMS erişimi

Her PNG tek tek gönderildi; birleşmiş son çıktı gelmeden sonraki giriş verilmedi. Boş tespit sonuçları da kaydedildi. Son dalın PTS'si özgün giriş kimliğine bağlandı. Crop dalı `CLOCK_TIME_NONE` verdiği için ara aşamalar aynı anda tek olan bekleyen girişe bağlandı; son dal PTS kontrolü ayrıca yapıldı. Yinelenen, eksik veya beklenmeyen çıktı açık hata üretir.

Standart `hailofilter` tensörleri çıkıştan önce kaldırır. Yalnız tekrar oynatıcıda `remove-tensors=false` ile ömrü uzatıldı; bu parametre canlı uygulamaya taşınmadı. Bu davranış [TAPPAS filtre kaynağında](https://github.com/hailo-ai/tappas/blob/v3.31.0/core/hailo/plugins/filter/gsthailofilter.cpp) tanımlıdır. HailoNMS tensörünün Python buffer görünümü `(2,100,0)` biçimindeydi; bu boş HWC görünümü gerçek NMS kaydı sanılmadı. Doğrulanan sürüm/topoloji için geçerli FLOAT32 sınıf sayacı + `ymin,xmin,ymax,xmax,score` kayıtları, sınıf başına en fazla 100 kutu sınırıyla salt okunur kopyalandı. Kullanılmayan tampon kuyruğu kaydedilmedi.

Her karede giriş `.npy`, geçerli NMS öneki `.bin` ve aşama izleri JSON olarak saklandı. TAPPAS kapatıldıktan sonra **kaydedilen aynı giriş tensörü** `InferVStreams` ile doğrudan HailoRT'ye verildi. Ağ içi logit/aktivasyon ölçüldüğü iddia edilmedi.

## Sayısal önce/sonra karşılaştırması

Buradaki “sonra”, aynı HEF ve aynı koşullarla bağımsız tekrar çıkarımdır; yeni eğitilmiş/düzeltilmiş model değildir.

| Ölçüt | Kayıt | Tekrar çıkarım |
|---|---:|---:|
| Kare sayısı | 81 | 81 |
| En az bir mavi kutu içeren kare | 54 | 54 |
| Mavi kutu | 63 | 63 |
| En az bir mavi skor ≥ 0,50 olan kare | 4 | 4 |
| Skordan bağımsız köşe/sınır/doluluk ön koşulunu geçen mavi aday | 8 | 8 |
| Skor ve bu geometri ön koşullarını birlikte geçen aday | 0 | 0 |

**81/81** kayıtlı tespit sonucu tekrar çıkarımla eşleşti. **81/81** TAPPAS ham NMS kaydı doğrudan HailoRT NMS değeriyle birebir aynı. Uygulamanın özgün görüntüye dönüştürülmüş kutuları ile doğrudan NMS'den dönüştürülen kutuların maksimum mutlak farkı **8,6096 × 10⁻⁸** normalize birim; karşılaştırma toleransı `2e-6`. Skorlar aynıdır; bu fark kayan nokta koordinat aritmetiğindedir. 1280 px ölçekte yaklaşık 0,00011 px üst sınırına karşılık gelir; bu **fiziksel görüntüleme doğruluğu iddiası değildir**.

0,5097429156303406 değeri dört karede aynı kaldı. Skor değişiminin uygulama/panel/çözümleyicide oluştuğuna dair kanıt yok; ilk erişilebilir HEF NMS sonucunda zaten var. Bu kaydın en yüksek skoru olması, ağın bütün olası girdilerindeki matematiksel tavanını kanıtlamaz.

## Gölge, kesik hedef ve düşük skor

| Kare | Görsel ve sayısal sonuç | Tekrar oynatma ret nedeni |
|---|---|---|
| 017 | İnsan gölgesi; skor 0,5097429156 | `no_corners` |
| 032 | Alt kenardan kesilen branda; aynı skor | `border` |
| 035 / 036 | Üst kenardan kesilen branda; aynı skor | `border` |
| 028 | Tam branda; skor 0,4157749414, geometri uygun | `score` |
| 031 | Tam branda; skor 0,4024701416, kenara fazla yakın | `score`, `border` |

017'nin kutusu gerçek brandaya taşınmıyor; gölge üzerinde kalıyor ve doğrudan HEF sonucu da aynı. 050/051/073/074'teki düşük skorlu insan/gölge kutuları ve 007'deki kırmızı sınıflı ahşap yüzey de görsel etiket dosyasında yanlış tespit olarak işaretlendi. Çalışma, bu sınırlı negatif örnekleri doğru tam hedef kabul etmedi; başka gölgelerin her zaman reddedileceğini kanıtlamaz.

63 mavi kutuda bağımsız teşhis sayımları: **59 skor**, **29 köşe bulunamaması**, **26 kenar payı**, **10 kadraj doluluğu** reddi. Bir aday birden fazla nedenle reddedilebilir; toplamları 63 olmak zorunda değildir. Köşe yoksa kenar/doluluk “geçti” olarak yorumlanmaz; o testler uygulanamamıştır.

Karşılaştırma görselleri `artifacts/replay/comparison-images/` altında tüm 81 kare için vardır. Turuncu AI kutusu, mor OpenCV köşeleri, camgöbeği elle yaklaşık işaretlenmiş branda kutusudur. Örnekler: [017 gölge](../artifacts/replay/comparison-images/frame-017.jpg), [028 tam branda](../artifacts/replay/comparison-images/frame-028.jpg), [032 kesik branda](../artifacts/replay/comparison-images/frame-032.jpg), [035 kesik branda](../artifacts/replay/comparison-images/frame-035.jpg). Başlıklar görüntünün dışına eklenir; kadraj sınırındaki köşeler örtülmez. Bu çizimler doğrulanmış `results-final` kaydından yeniden çıkarım yapılmadan `scripts/render_replay_comparison.py` ile üretildi; `render-manifest.json` kaynak sonuç ve görsel hash'lerini tutar.

## Yazılım değişikliği ve testler

- `python -m safak_gorev2.replay recorded|hailo` eklendi. Kaynak çiftleri/hash'ler/kamera boyutu/oturum/kimlik denetlenir; sonuçlar yeni klasöre yazılır. Hailo yoksa CPU'ya geçmez ve açık hata verir.
- `replay_hailo.py` gerçek yardımcı hat, tensör izi, ham NMS ve doğrudan HailoRT karşılaştırmasını sağlar. Ham NMS okuyucusu doğrulanan HailoRT 4.20.0/topoloji ile sınırlandırılmıştır; başka sürüm için uyarlama gerekir.
- Mevcut `geometry.py` kenar ve doluluk şartları `corner_screen` ortak fonksiyonuna çıkarıldı. Replay ve mevcut geometrik kabul aynı şartları kullanır; sayılar ve kabul davranışı değişmedi. Teşhis skoru düşük adayda da geometriyi inceler; canlı uçuşta bu, skor kapısını atlamak anlamına gelmez.
- **56 test geçti:** mevcut 35 test ve 21 yeni durum. Eksik/bozuk PNG/JSON, hash, yinelenen kimlik/anahtar/manifesto, boyut uyumsuzluğu, NaN, boş tespit kimliği, renk/letterbox/ters koordinat, gölge/kesik hedef, kaynak sayımları, ortak şartların değişmemesi ve kaydedilmiş gerçek Hailo karşılaştırması kapsandı. Gerçek veri mevcut değilse yalnız gerçek veri gerektiren testler açıkça atlanır.

Kanıtlanan bir canlı tespit hatası olmadığı için `hailo_backend.py` değişmedi. FC parametreleri/rota, Görev 1, kontrol kodu, kamera/crop, kalibrasyon ve HEF değişmedi. Eşik **0,50** kaldı. Pi'deki aktif uygulama klasörüne düzeltme dağıtımı veya yeniden başlatma yapılmadı.

## Tekrar çalıştırma

Proje kökünde yerel kayıt analizi:

```bash
.venv/bin/python -m safak_gorev2.replay recorded \
  --source artifacts/field/flight-01 \
  --annotations docs/replay/flight-01-annotations.json \
  --output artifacts/replay/yeni-recorded-sonucu
```

Pi'de mevcut Hailo ortamını etkinleştirdikten sonra, tekrar oynatma proje kökünde:

```bash
python -m safak_gorev2.replay hailo \
  --source /home/furkan/Desktop/safak-gorev2-quad/runtime/field/20260905T075830Z-loiter \
  --annotations flight-01-annotations.json \
  --hailo-env /home/furkan/Desktop/hailoenvtest/hailo-rpi5-examples/.env \
  --output yeni-hailo-sonucu
```

Çıktı klasörü önceden bulunmamalıdır. `run-manifest.json` durum, yazılım/model/config/hash bilgileri; `frames.jsonl` kimlik ve tüm aday teşhisleri; `summary.json` sayımlar; `images/` karşılaştırmalar; Hailo modunda `tensors/` gerçek aşama verilerini içerir. Başarısız denemeler `status=failed` ile kalır; tamamlanmış sonuç yerine kullanılmaz. `results-01/02/03` prob uyarlaması, `results-04` sonuç manifestosu serileştirme sorunu sırasında durdu. `results-05` ve `results-final` başarıyla tamamlandı; bu ara araç sorunları canlı tespit hattı hatası olarak sayılmadı.

## Ayrı sonraki aşama

Sonraki PT/ONNX karşılaştırması ayrıca tamamlandı: [MODEL_COMPARISON.md](MODEL_COMPARISON.md). Aşağıdaki PT çalıştırılmadığı bilgisi yalnız ilk replay aşamasının tarihli kapsamıdır. Kullanıcının güncel önceliği model eğitimi değil, mevcut modelle saha hazırlığıdır.

Eğitim/dönüştürme ayrımını yapmak için gerçek eğitim ve doğrulama görselleri/etiketleri, kullanılan `data.yaml`, eğitim komutu/ayarları ve metrikler; HEF'le ilişkisi doğrulanmış checkpoint ve ONNX; dışa aktarma komutu/sürümleri; Hailo Dataflow Compiler sürümü, model script/`.alls`, kalibrasyon veri kümesi, varsa FP/quantized HAR ve derleme/kuantizasyon raporları gerekir. Mevcut `.pt` bu çalışmada deserialize edilmedi veya çalıştırılmadı. Bu dosyalarla aynı görüntülerin FP/ONNX/kuantize/HEF çıktıları karşılaştırılabilir. Yeniden eğitim başlatılmadı.

Sonraki fiziksel doğrulama ayrı oturumda gerçek 2 m hedef, sabit destek, bilinen lens–hedef dik mesafesi ve hedefin kadrajda tam kaldığı farklı yönlerle planlanmalı; kamera/crop aynı tutulmalı ve görüntüdeki dört kenar/kenar payı kontrol edilmelidir. Elde olmayan yükseklik/geometri için sayı uydurulmadı. Bu rapor yeni uçuş veya otomatik kontrol başlatma adımı değildir.

Yaklaşık 1 Hz olan bu küçük küme sürekli hedef kilidini, tüm saha başarı oranını, metrik mesafe doğruluğunu veya otonom uçuşa hazır olmayı doğrulamaz.
