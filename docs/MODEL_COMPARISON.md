# Görev 2 — PT, ONNX ve mevcut HEF karşılaştırması

5 Eylül 2026. **İki ayrı bulgu var: gölge yanlış tespiti `.pt` modelinde de mevcut; mevcut HEF ise aynı görüntülerde `.pt` modelinden daha düşük skorlar veriyor.** `.pt` dosyasından bu oturumda üretilen FP32 ONNX, 81/81 karede `.pt` ile eşleşti. Bu yeni ONNX'in eski HEF'i üretirken kullanılan dosya olduğu kanıtlanmış değildir.

Kısa örnek: `028` gerçek tam branda için HEF **0,4158**, PT **0,5952**; `017` insan gölgesi için HEF **0,5097**, PT **0,5439**. Gölge hatasını yalnız Hailo dönüşümüne bağlayamayız. HEF skor düşüşü de sadece “model böyle öğrenmiş” denerek açıklanamaz.

## Ne yapıldı?

Önceki çalışmada Pi üzerinde doğrulanmış **aynı 81 adet 640×640 RGB UINT8 giriş tensörü** kullanıldı. Fotoğraflar farklı yeniden boyutlandırmayla verilmedi. PT/ONNX için yalnız HWC→NCHW ve `/255` FP32 dönüşümü yapıldı. Bu giriş düzeni [Ultralytics'in tensor giriş tanımıyla](https://docs.ultralytics.com/modes/predict/) uyumludur. Ortak karşılaştırmada NMS skor eşiği 0,25, IoU 0,7, sınıflar ayrı, sınıf başına en fazla 100 kutu; görev ön koşulu skoru yine **0,50**.

- Orijinal 168 dosyanın hash'leri ve tamamlanmış Hailo sonucunun 327 çıktısı karşılaştırmadan önce doğrulandı.
- Checkpoint ZIP/pickle türleri önce statik incelendi. Model, `torch.load(weights_only=True)` ve açıkça izin verilen bilinen Torch/YOLOv8 sınıflarıyla yüklendi. Sınırsız pickle yükleyicisi kullanılmadı.
- `.pt` modelindeki sürüm **8.4.37**, paket metadata'sındaki dışa aktarma sürümü **8.4.137**. Her iki runtime sürümüyle 81 kare ayrı ayrı çalıştırıldı. PT ham çıktı dizileri **81/81 bit düzeyinde aynı**; iki sürümün ürettiği ONNX dosyalarının SHA256'sı da aynı. Bu iki Python sürümü arasındaki fark gözlenen düşüşü açıklamıyor.
- `.pt` modelinden yeni, sabit `[1,3,640,640]` girişli, opset 17 FP32 ONNX üretildi. ONNX checker geçti; CPU ONNX Runtime ile tüm karelerde çalıştırıldı. Bu bir Hailo HEF üretimi veya yeniden eğitim değildir.
- PT ve ONNX'in NMS sonrası sınıf/skor/kutuları **81/81** karede `2e-5` toleransla eşleşti. NMS öncesi bütün adaylarda maksimum skor farkı **1,0878×10⁻⁶**, maksimum koordinat farkı **0,002045 giriş pikseli**. Bütün ham dizilerin eşit olduğu iddia edilmez.
- Her karede ham PT/ONNX çıktısı ve **yalnız PT için** sınıf logitleri `.npz` olarak kaydedildi. HEF'in iç logitleri ölçülmedi.

Bu karşılaştırma Mac'teki ayrı `.venv-model` ortamında yapıldı. Pi, kamera, MAVLink, görev denetleyicisi, panel ve uçuş açılmadı. Uçuş uygulamasına CPU/ONNX alternatifi eklenmedi.

## Sonuçlar

| Aynı 81 kayıtlı görüntüde | Mevcut HEF | PT FP32 | Yeni ONNX FP32 |
|---|---:|---:|---:|
| Mavi tespitli kare | 54 | 58 | 58 |
| Mavi kutu | 63 | 79 | 79 |
| En az bir mavi skor ≥0,50 olan kare | 4 | 40 | 40 |
| Skor+köşe+kenar+doluluk ön koşulunu geçen kutu | 0 | 7 | 7 |
| En yüksek mavi skor | 0,509743 | 0,785335 | 0,785335 |
| Elle “tam branda” işaretlenen 9 karede hedefi ≥0,50 ile işaretleyen kare | 0 | 8 | 8 |

“40 eşik üstü kare” doğru/tam hedef anlamına gelmez; gölge ve kesik hedefler de bu sayıya girebilir. Tam branda eşleşmesi, önceki görsel incelemedeki yaklaşık kutuyla IoU≥0,5 üzerinden yapıldı; bu hassas bir eğitim etiketi/benchmark değildir. Belirsiz `015` bu eşleşme hesabına katılmadı. PT'nin ön koşulu geçen 7 kutusu **otonom görev kilidi, PnP, metrik mesafe veya uçuş başarımı değildir**.

HEF ve PT arasında IoU>0,7 ile eşlenen 62 kutunun ortanca IoU'su **0,9805**; ortanca `PT skoru − HEF skoru` **+0,1440**. Kutuların büyük ölçüde aynı yerde, skorların daha düşük olması karşılaştırılmış bir gözlemdir. İki dosyanın bütün ağırlıklarının aynı kökten geldiğinin kesin kanıtı değildir.

### Anlaşılır iki örnek

`028`: gerçek tam branda. HEF 0,4158 ile skor koşulunda kalırken PT 0,5952 ile görüntü ön koşullarını geçiyor.

![028: solda HEF, sağda PT](../artifacts/model-comparison/run-01/images/frame-028.jpg)

`017`: insan gölgesi. Yanlış tespit PT modelinde de var; 0,5439 skoruna rağmen OpenCV dört köşe bulamadığı için reddediliyor.

![017: solda HEF, sağda PT](../artifacts/model-comparison/run-01/images/frame-017.jpg)

`032/035/036` kesilmiş branda örnekleri PT/ONNX'te de kenar koşulundan reddediliyor. `037` tam hedefte PT skoru 0,4960 ve eşik altında; `031` skoru 0,5297 olsa da kenar payı yetersiz. Eşik düşürülmedi.

## Eğitim dosyasında okunan bilgiler

Checkpoint: YOLOv8n tabanlı `DetectionModel`, iki sınıf, **3.011.238 parametre**, stride 8/16/32. Kaydedilmiş eğitim ayarında `imgsz=960`, `epochs=120`, `patience=40` var; eğitim sonuç tablosu 79 satır içeriyor. Strip edilmiş checkpoint `epoch=-1` ve `best_fitness=None` taşıyor; bundan “eğitim yapılmamış” sonucu çıkarılmadı.

Kaydedilmiş eğitim metriği mAP50=0,99316, precision=0,93736, recall=1,0. Bunlar checkpoint içindeki **eski eğitim/validasyon kayıtlarıdır**; veri ayrımı/etiketler bu oturumda incelenmediğinden bağımsız doğrulama veya bu uçuş sahasındaki performans kabul edilmez. Bu karşılaştırmada Hailo ile aynı 640 giriş kullanıldı; 960 girişli yeni HEF seçilmedi.

## Dönüştürmedeki açık nokta

Paketin `metadata.yaml` dosyasında eğitim veri yolu takımın `dataset/data.yaml` dosyasına işaret ediyor; **dışa aktarma argümanı `data: coco128.yaml`**. Resmî PyPI'den alınan Ultralytics **8.4.137** paketindeki `export_hailo` kaynağı incelendi: `data` ile seçilen görüntüler INT8 kalibrasyonunda kullanılıyor; normalizasyon `/255`, optimizasyon seviyesi 2 ve kuantizasyon sonrası finetune tanımlanıyor. Kaynak, temsil edici kalibrasyon görüntülerini istiyor. [Resmî Hailo entegrasyonu](https://docs.ultralytics.com/integrations/hailo/)

Bu yüzden **Hailo için kullanılan kalibrasyon veri seçimi araştırılması gereken somut bir adaydır**. Ancak `coco128.yaml` dosyasının gerçek içeriği ve derleme logu elimizde yok; dosya adından bütün kullanılan görüntüleri bildiğimiz veya kesin kök nedeni bulduğumuz söylenemez. Buradaki kalibrasyon, kamera lens kalibrasyonu değildir; modelin INT8 sayı aralıklarını ayarlayan örnek görüntülerdir.

Ayrıca eski HEF'in bu checkpointten üretildiğini kanıtlayan özgün ONNX/hash/derleme zinciri eksik. Ağ ağırlığı farklılığı, kuantizasyon ve optimizasyon etkileri henüz ayrı ayrı ölçülmedi. Yeni ONNX karşılaştırmasının iyi olması yalnız bu oturumdaki PT→ONNX adımını doğrular.

## Sonraki somut iş

**Son kullanıcı kararı:** Bu model iyileştirme adımları ertelendi; yeni beyaz zemin verisi/eğitim istenmiyor. Mevcut modelle gerçek Görev 2 testi hazırlığına geçiliyor. Güncel saha durumu `NEXT_SESSION.md` başında.

1. Mevcut HEF'in üretim komutu/betiği, özgün ONNX veya HAR, DFC sürümü ve kalibrasyon verisi bulunursa dosya ilişkisini doğrula. Hailo kalibrasyonunda gerçekten hangi görüntülerin kullanıldığını kontrol et.
2. Doğru checkpoint ve temsil edici gerçek hedef/zemin/gölge görüntüleriyle ayrı bir **aday HEF** üret; kaynakları ve FP/quantized HAR aşamalarını sakla. Sonra aynı 81 kareyi karşılaştır; bu küme kalibrasyona katılırsa bağımsız test olarak sunma. Yeni HEF mevcut uçuş modelinin üstüne yazılmamalı.
3. Gölge hatası PT'de de bulunduğundan, eğitim/etiketler ve negatif örnekler ayrıca incelenmeli. Yalnız HEF'i yeniden üretmek bu hatayı çözmüş sayılmaz. Yeniden eğitim bu oturumda başlatılmadı.

Kullanıcıya özgün dönüştürme/eğitim dosyalarının bulunduğu klasör soruldu. Bu dosyalar olmadan yanlış veriyi kullanarak yeni HEF derlenmedi. Fiziksel mesafe/kadraj doğrulaması da hâlâ ayrı adımdır; doğrudan otonom uçuşa geçilmedi.

## Araçlar, kanıt ve test

- Araç: `python -m safak_gorev2.model_compare`. Model kütüphaneleri yalnız komut çalışırken yüklenir. Kamera/FC bağımlılıkları kullanılmaz.
- Sonuç: `artifacts/model-comparison/run-01/`; sürüm kontrolü: `run-export-version/`. Her biri 81 kare, iki formatın ham çıktıları, 81 karşılaştırma görseli, özet, checkpoint bilgisi ve **166 hash'li çıktı** içerir.
- Kilitli kurulum sürümleri: `artifacts/model-comparison/requirements-lock.txt`; Torch 2.14.0, ONNX 1.22.0, ONNX Runtime 1.29.0, NumPy 2.2.6. Dışa aktarma sürümü ikinci çalıştırmada izole paket yolundan 8.4.137 olarak yüklendi.
- Checkpoint SHA256: `ac2ce1094ab8f2583f8e9678677724490e848a5c5c3d7bbab9cc9003b7a0480a`.
- Yeni ONNX SHA256: `bc801e168d58f151b1d9447bf7b8c938c185faf162222179c30120a7a25b57d4`.
- Model ortamında **7 yeni test geçti**: sınıf bazlı NMS/koordinat dönüşümü, boş sonuç, bozuk boyut/NaN, gerçek PT/ONNX/gölge kanıtı, sürüm karşılaştırması ve import sırasında donanım/model runtime açılmaması. Normal uygulama testleri ayrıca çalıştırıldı; model kütüphaneleri bulunmayan ortamda 4 model-runtime testi açıkça atlanır.

Tekrar çalıştırma, proje kökünden:

```bash
.venv-model/bin/python -m safak_gorev2.model_compare \
  --source artifacts/field/flight-01 \
  --hailo-results artifacts/replay/hailo-final \
  --checkpoint safak_v2_hailo_model/safak_v2.pt \
  --annotations docs/replay/flight-01-annotations.json \
  --output artifacts/model-comparison/yeni-sonuc
```

Çıktı klasörü yeni olmalıdır. Gerekli paketler `.venv-model` içinde kurulur; uçuş ortamına Torch/ONNX eklenmez. Test:

```bash
YOLO_CONFIG_DIR=artifacts/model-comparison/test-settings \
.venv-model/bin/python -m pytest --noconftest -q tests/test_model_compare.py
```

Aktif model, eşik 0,50, Görev 1, FC parametreleri, rota, kamera/crop ve kontrol kodu değişmedi.
