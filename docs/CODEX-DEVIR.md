# Codex / yeni sohbet açılış promptu — ŞAFAK UAV

Aşağıdaki metni yeni sohbetin ilk mesajı olarak yapıştır.

---

ŞAFAK UAV projesine kaldığımız yerden devam et.

Önce şu dosyaların **yalnız en üstteki DEVİR bölümünü** oku:
- `AGENTS.md`
- `docs/HANDOFF.md`

Yerel proje: `/Users/kaan/Documents/ChatGPT/last şafak`
Raspberry Pi: `furkan@172.20.10.6` — proje yolu `/home/furkan/Desktop/safak-gorev2-quad`

Özet durum:
- Hızlı görev (`config/hizli-gorev.json`, strategy=quick) sahada tamamlandı: iki yük de gerçek servo komutuyla bırakıldı.
- Ana görev (`config/ana-imx708.json`, strategy=center) henüz başarılı bırakma yapmadı. Son denemede model 25–30 m'de 39 mavi + 60 kırmızı gördü, fakat profildeki rota parmak izi eski olduğu için kontrol hiç devralmadı. Parmak izi düzeltildi, FC'deki rota 15 m.
- Bugün yapılan düzeltmeler: kadraj taşan kutuların kırpılması, kenar payının aday oluşturmayı engellememesi, frenlerken hedefin yeniden yakalanması, doğrulama/merkezleme kilidinin PnP boşluklarında silinmemesi, merkezleme toleranslarının ölçülen gürültüye göre ayarlanması ve yükseklikle ölçeklenmesi, ikinci yükten sonra doğrudan LAND waypointine uçulması. Hepsi Pi'de yüklü; yerelde 296, Pi'de 254 test geçiyor.

Şu anki öncelik: **ana görev uçuşu**. Uçuştan sonra uçuş JSONL'indeki `diagnostics` alanından gerçek PnP (metrik geometri) başarım oranını ölç. Benzetime göre bırakmanın tamamlanması için bu oranın en az **%40** olması gerekiyor; son ölçüm %26 idi. Düşükse geometri/kalibrasyon tarafını düzelt.

Kurallar:
- Kısa ve Türkçe yanıt ver, projeyi bana yeniden anlatma.
- Ben açıkça istemeden **yerde servo komutu verme** (yükleri düşürür), **ARM veya uçuş modu komutu gönderme**, FC parametresi yazma.
- Değişiklikleri Pi'ye yükle, iki tarafta testleri çalıştır, `runtime/before-*` altına yedek al, AGENTS.md ve docs/HANDOFF.md başına kısa özet ekle.
- `docs/competition/legacy-sha256.json` ile korunan dosyaları değiştireceksen özgün kopyayı `archive/legacy-options/` altına alıp `preserved-paths.json` eşlemesine ekle.

Uçuş öncesi rota kontrolü (Pi'de):
```
cd /home/furkan/Documents/proje/hailo-rpi5-examples && source ./setup_env.sh
cd /home/furkan/Desktop/safak-gorev2-quad
export PYTHONPATH="$PWD/runtime/python:$PWD:$PYTHONPATH"
python scripts/route_digest.py --profile config/ana-imx708.json
```

Görev (kamerayı bu açar):
```
export MAVLINK20=1
python -m safak_gorev2.competition.main --config config/ana-imx708.json --mode flight
```

Kayıt (ayrı terminal, görev açıldıktan sonra):
```
python -m safak_gorev2.record --config config/ana-imx708.json --panel-url http://127.0.0.1:8081 --root runtime/recordings
```

---

Ek bilgi gerekirse `AGENTS.md` içindeki DEVİR bölümünün altındaki tarihli kayıtlar kronolojik geçmişi içerir.
