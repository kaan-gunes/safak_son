ŞAFAK UAV için mevcut DJI veri setimi, bu ek paketteki gerçek uçuş görüntüleriyle birleştir; yeni görüntüleri otomatik etiketleyip görsel olarak kontrol et ve Hailo-8L'ye dönüştürülebilecek iki sınıflı hedef dedektörünü eğit. Yalnız plan yazma: mevcut ortamın izin verdiği veri hazırlama, etiketleme, eğitim ve doğrulama işlerini tamamla. Açıklamaların Türkçe olsun.

Girdiler ve sınır:
- Eski DJI veri setinin klasörünü çalışma alanında bul; yoksa yalnız yolunu sor. Kullanıcı yaklaşık350 görüntü bildirdi, gerçek sayıyı/etiketleri sen say.
- Ek paket: bu dosyanın yanındaki images/ içinde25 özgün1280×720 PNG. selection-manifest.json:9 tam mavi branda,10 kesik mavi branda,6 hedefsiz görüntü. Görsel seçim kategorileri YOLO kutu etiketleri değildir. Bu paket henüz etiketlenmemiştir; eksik txt dosyalarını otomatik olarak “negatif” yorumlama.
- Bu25 dosyanın tamamı aynı IMX219 uçuşundan: capture_group=safak-flight01-20260905. Yeni kamera görüntüsü veya25 bağımsız uçuş değiller. Beyaz taşlı zemindeler; kırmızı pozitif örnek yok. Kırmızı hedef eğitimini eski DJI verisinden koru.
- Model sınıfları tam olarak0:kirmizi_hedef,1:mavi_hedef. Mavi hedef2×2m, kırmızı hedef1×1m; fiziksel boyutları görüntüde sabit piksel boyutuna çevirmeye çalışma. Canlı TAPPAS callback'inde sınıf1/2 görülmesi +1 etiket kaymasındandır; YOLO eğitim sınıflarını1/2 yapma.
- Eski DJI çekimleri asfalt ağırlıklı, yarışma alanı kullanıcı beyanına göre toprak/asfalt ağırlıklı. Ek beyaz zemin görüntülerini gereksiz çoğaltıp ana veriyi bastırma. Kullanıcı rastgele internet/sentetik şekil veri seti eklenmesini istemedi.
- Ham kaynakları koru; ayrı çalışma/çıktı klasörü oluştur. Bu işte Pi uçuş uygulamasına bağlanma, kamera/MAVLink/uçuş başlatma, FC parametresi/rota/kalibrasyon veya aktif HEF değiştirme. Ücretli bulut işini veya veri yüklemeyi kendiliğinden başlatma.

1. Önce veri denetimi:
Görüntüleri açılabilirlik, boyut, SHA256, yinelenen/çok benzer örnekler açısından tara. Paket manifestosuyla25 dosyanın hash'ini doğrula. Eski data.yaml ve gerçek txt etiketlerinin sınıf sırasını karşılaştır; farklıysa yalnız yeni çalışma kopyasında açık bir eşlemeyle bütün etiketleri dönüştür. Sadece YAML'deki isimleri değiştirmek yeterli değildir. Kırmızı/mavi sınıf sayıları, çekim grupları ve kusurları raporla. Panel ekran görüntülerini, review/ önizlemelerini, AI kutusu/yazısı basılmış videodan kareleri ve aynı görüntünün türevlerini eğitim girdisi yapma.

2. Otomatik etiketleme ve görsel düzeltme:
Mevcut kullanılabilir öğretmen dedektör/segmentasyon araçlarıyla yeni25 görüntüye taslak kutu üret. Araç yoksa ortamı inceleyip uygun yöntemi seç; renk/segmentasyon yalnız etiket taslağına yardımcı olabilir. Eski HEF veya PT tahminlerini ground truth kabul etme: bu model insan/bank gölgesine mavi hedef diyebiliyor. Canlı uçuş eşiği0,40'ı eğitim/auto-label eşiği sanma.
- Her yeni görüntüyü ve çizilmiş taslak etiketlerini açarak kontrol et; düşük güvenli ve kaçırılmış hedefleri de düzelt. Bu küçük pakette yalnız birkaç örneğe bakıp tamamını doğru ilan etme.
- Bütün görünür hedefleri etiketle. Branda üzerindeki kırışıklık/parlama yüzünden bir brandaya birden çok kutu verme.
- Gölge, insan, ayakkabı, bank, bidon ve benzer renkli başka nesne hedef değildir. Bidon varsa kutuyu bidonu da içermek için genişletme; hedef branda sınırını esas al.
- Kadrajdan kesik ama tanınabilir branda da mavi hedeftir. Görüntü içinde kalan sınırlarını etiketle; kadraj dışında hayalî tamamlanmış kutu üretme. Dedektörün kesik hedefi öğrenmesi, uçuşta kesik hedefin bırakma için kabul edilmesi anlamına gelmez.
- Manifestoda negative olan6 görüntüyü de kendin kontrol et; gerçekten hedef yoksa negatif kabul edip açıkça boş YOLO txt üret. Pozitif etiket atlanmasını “negatif” diye gizleme.
- Etiket formatı class_id x_center y_center width height; normalize koordinatlar0–1, pozitif kutu boyutları, görüntü sınırları içinde. Kararsız örneği reason ile review_pending'e ayır; kesin etiket gibi eğitimde kullanma.
- Son25 görüntü için görüntü başına inceleme durumu, hedef sayısı ve çizili etiket önizlemesi üret. Eski etiketleri de sınıf/zemin/çekim grubuna göre örnekleyip yanlış eşleme veya ciddi hata bulursan ilgili grubu geniş incele.

3. Eğitim/doğrulama/test ayrımı:
Aynı uçuşun komşu karelerini farklı kümelere rastgele dağıtma. Yeni25 görüntünün tamamını aynı grupta tut; bu ek paketi eğitim için kullanıyorsan test başarısını yine bunlardan hesaplama. DJI görüntülerini de uçuş/çekim serisi ve yakın benzerlik gruplarına göre ayır. Türev/augmentasyonları kaynakla aynı kümede tut. Split manifestosunu sabitle ve veri sızıntısını denetle. Bağımsız test grubu yoksa bunu açıkça bildir; eğitim görüntülerinde ölçülen skoru saha başarısı diye sunma. Her iki sınıfın bağımsız değerlendirmede temsil edilmesini kontrol et. Hailo INT8 kalibrasyonu için ayrılacak görüntüler eğitim grubundan gelsin; nihai test görüntülerini kullanma.

4. Hailo uyumlu eğitim:
Önce GPU/VRAM, işletim sistemi ve mevcut paketleri oku; izole ortam ve sabitlenmiş sürümler kullan. Hedef donanım Raspberry Pi5 + HAILO8L; önceki ölçülen HailoRT4.20.0. Eğitimden önce seçeceğin mimarinin bu hedef için ONNX→Hailo dönüşüm yolunu resmî belgelerle doğrula. YOLOv8n makul başlangıç adayıdır; sadece en yeni diye farklı/end-to-end mimariye geçme. Hailo Model Zoo'nun güncel master dalını körlemesine kurma: Hailo-8/8L için uyumlu v2.x Model Zoo ve v3.x DFC hattının kesin sürüm eşleşmesini kontrol et.
Temiz, uyumlu pretrained checkpoint'ten iki sınıflı fine-tune başlat. 640×640 giriş, doğru letterbox ve RGB dönüşümünü açıkça kaydet. Donanıma göre batch seç, kısa smoke eğitimle etiket/loss/export sorunlarını yakala; ardından süreye uygun tam eğitimi yap. Epoch, patience, optimizer, learning rate ve seed'i kaydet; keyfî uzun eğitim veya geniş hiperparametre taraması yapma. En iyi checkpoint'i yalnız validation sonucuyla seç; test setiyle ayar arama.
Döndürme, perspektif, ölçek, pozlama ve hareket bulanıklığı gerçek uçuşu temsil etsin. Sınıf renkle tanımlandığı için maviyi kırmızıya/kırmızıyı maviye dönüştürecek hue veya kanal dönüşümleri kullanma. Geometrik dönüşümlerde kutuları doğru taşı. Örnek eğitim mozaiklerini görsel olarak denetle.

5. Değerlendirme ve dönüşüm:
Sınıf başına precision, recall, AP50 ve AP50–95; gölge/hedefsiz örneklerde yanlış pozitifler; kaçan küçük/kesik hedefler ve skor dağılımını raporla. Zemin/kamera gruplarındaki sonuçları sayılarıyla göster. Eski model varsa aynı ayrılmış görüntülerde karşılaştır. Yeni25 eğitimdeyse bu25 üzerindeki önce/sonra karşılaştırmasını sadece eğitim teşhisi diye işaretle.
Önceki projede aynı81 giriş tensöründe PT ve yeni FP32 ONNX eşleşmiş, mevcut HEF belirgin farklı sonuç vermişti. Bu yüzden yalnız PT'nin mAP değeriyle işi bitirme. Yeni best.pt ve ondan üretilmiş FP32 ONNX'i aynı tensörlerde sınıf/kutu/skor olarak karşılaştır; toleransı ve farkları kaydet. Çıktıyı yalnız conf=0,40 filtresinden sonra karşılaştırıp alt skorlu hataları gizleme.
DFC/derleme ortamı varsa aynı checkpoint kökeninden, gerçek temsilî eğitim görüntüleriyle INT8 kalibrasyonu yap; rastgele görüntü veya ilgisiz COCO kalibrasyonu kullanma. RGB/BGR, padding, resize, normalization ve NMS'i canlı hatla karşılaştır; çift normalizasyon yapma. Hailo-8L için derle ve mümkünse aynı girişlerde FP32→INT8 emulator→HEF karşılaştırması yap. 0,5097 gibi tekrar eden skorları çarpan/ek sigmoid/eşik oynamasıyla düzeltmeye çalışma. Derleyici/donanım yoksa PT/ONNX teslimini tamamla, HEF aşamasını eksik bağımlılıklarıyla açıkça bekleyen iş olarak bırak; doğrulanmamış HEF üretildi iddiasında bulunma. Aktif drone modelini değiştirme.

Teslim:
- İncelenmiş birleştirilmiş YOLO veri seti, labels, data.yaml ve kaynak/etiket/split manifestoları.
- Etiket inceleme önizlemeleri ve review_pending listesi.
- Eğitim komutu/ayarları, sürüm kilidi, seed, best.pt, last.pt, ONNX, eğitim logları ve değerlendirme raporu.
- Dönüşüm yapılabildiyse ALLS/YAML/NMS ayarları, INT8 kalibrasyon görüntü manifestosu, DFC/Model Zoo/HailoRT sürümleri ve HEF doğrulama sonuçları.
- Bütün model dosyalarının SHA256'ları ve PT→ONNX→HEF köken zinciri. Eksik ölçümleri açıkça belirt; yüksek mAP'yi otonom uçuş başarısı veya mesafe doğruluğu diye sunma.

Başvurulacak resmî kaynaklar (kurulu sürüme göre doğrula):
- YOLO kutu biçimi: https://docs.ultralytics.com/datasets/detect/
- Eğitim önerileri: https://docs.ultralytics.com/guides/model-training-tips/
- Veri ayrımı/sızıntı: https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets
- Hailo sürüm uyumluluğu: https://github.com/hailo-ai/hailo_model_zoo
- Hailo YOLOv8 eğitimi: seçtiğin Hailo-8L uyumlu Model Zoo sürümündeki training/yolov8/README.rst.
