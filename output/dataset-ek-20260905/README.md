# DJI veri setine ek gerçek uçuş görüntüleri

25 özgün, işaretsiz1280×720 PNG seçildi. Kaynak:5 Eylül2026 ilk IMX219/Loiter uçuşu.9 tam mavi branda,10 kenardan kesilmiş branda,6 hedefsiz/gölge örneği. Seçilen tüm görüntüler görsel olarak incelendi; kaynak ve kopya SHA256'ları eşleşti. Görüntüleri kırpma, yeniden boyutlandırma, kutu/yazı silme veya renk düzenleme yapılmadı.

Eğitime girecek görüntüler yalnız `images/` içindedir. `review/selection-contact.jpg` yazılı küçük önizlemedir; eğitim görüntüsü değildir. `selection.csv` ve `selection-manifest.json` dosyaları kaynak kimliği, kategori ve hash'leri içerir.

**Henüz YOLO etiketleri yok.** `full/clipped/negative` bir görüntü seçimi kategorisidir; sınıf kimliği/kutu etiketi değildir. Etiketsiz pozitifleri negatif diye eğitim aracına vermeyin. Önce `CLAUDE_CODE_PROMPT.md` içeriğiyle otomatik etiketleme ve görsel denetim yaptırın; sonra eski DJI veri setinin çalışma kopyasına ekleyin. Bu paket mevcut yaklaşık350 DJI görüntüsünün yerine geçmez.

Tam kareler:028,031,034,037,038,039,040,041,046.
Kesik kareler:022,026,032,035,042,048,051,057,062,070.
Negatifler:007,011,016,073,074,079. Bunlarda görülen gölge/insan/bank hedef değildir.

Tümü aynı uçuş grubudur. Bazı komşu kareler görünüm olarak benzer kalır; 25 görüntü25 bağımsız senaryo değildir. Aynı grubu eğitim ve test arasında bölmeyin. Eğitime eklerseniz bağımsız test görüntüleri başka uçuş/gruplardan gelmelidir. Bu pakette kırmızı hedef pozitifleri ve yeni kamera görüntüsü yok; eski veri setinde kırmızı sınıf korunmalı, yeni kamera başarısı ayrıca ölçülmelidir.

Son iki uçuşun panel videolarında kutu/yazı görüntüye işlendiğinden bunlar pakete alınmadı. İlk81 özgün kare içinden seçilmeyen56 kare belirsizlik, aşırı tekrar, çok küçük görünür hedef, çok yakın/kesik görüntü veya düşük ek çeşitlilik nedeniyle dışarıda tutuldu; kaynaklar silinmedi. Skor0,40/0,50'yi geçme şartı seçim ölçütü yapılmadı; insan gözüyle gerçek hedef değerlendirildi.

Kullanım:ZIP'i açın. Claude Code'u eski DJI veri setinize erişebilen klasörde açın. `CLAUDE_CODE_PROMPT.md` dosyasının tamamını gönderin ve ek paket klasörünü belirtin. Doğrudan veri yükleme aracına klasör seçerken sadece images/ yolunu kullanın; önce etiketleme gerektiğini unutmayın.
