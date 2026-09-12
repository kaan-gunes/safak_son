# ŞAFAK UAV — yeni sohbet için güncel devir, 8 Eylül 2026

## DEVİR — 12 Eylül ANA GÖREV İLK BAŞARILI UÇUŞU (buradan başla)

**Ana görev sahada ilk kez tamamlandı.** Sortie `20260912T064602Z-ana-imx708`,
`DONE`, iki yük de `ACK_ACCEPTED`, 270,5 s (sınır 510 s). Kayıt:
`artifacts/first-successful-center-20260912/`.

### Bu oturumda ne değişti

1. **Zaman eksenli hedef takibi** (`safak_gorev2/competition/tracking.py`, yeni).
   Renk başına sabit hızlı Kalman; OpenCV 1–3 kare kaçırınca etiket düşmüyor,
   uzun kayıpta (8 kare) iz bırakılıyor. **Tahmin uçuş kanıtı üretmez:**
   köprülenen aday `source='tracked'`/`color_verified=False` olduğu için mevcut
   `corroborated` koşuluyla doğrulama/merkezleme/bırakma yollarına giremiyor.
   Gerçek tespitin `bbox` alanı değişmiyor, PnP ham ölçümü görüyor.
   Denetleyicide yalnız SEARCHING dalı değişti: kaçan karede sayaç sıfırlanmaz,
   ama artmaz da. Ayrıntı: `docs/competition/HEDEF_TAKIBI.md`.
   Uçuş kanıtı: DETECTED=860, TRACKED=57, maliyet 0,074 ms ortanca.

2. **`max_plane_tilt_deg` 15 → 30** (`config/competition-base.json`).
   **Bırakamamanın asıl sebebi buydu.** Önceki uçuşta metrik ölçüm karelerin
   yalnız %27'sinde kabul ediliyordu; retlerin %71,5'i düzlem eğimi kapısıydı,
   reprojeksiyon yalnız %1,5 (yani kalibrasyon sağlam). Ölçülen eğim ortanca
   21,2°, sınır 15°. Hata kamera çerçevesinde zaten vardı (19,2° ≈ NED 18,9°)
   ve araç düzdü (roll 1,1°, pitch 0,5°) → montaj/poz dönüşümü suçsuz.
   Ortalama normalden sapma 16° → sabit kayma değil, **gürültü**: yere dik
   bakan kamerada tam altındaki düz karenin düzlem normali kötü koşullanır.
   Kayıttan 456 köşe denemesi yeniden çözülerek doğrulandı: sınır yükselince
   ölçülen kamera yüksekliği dağılımı **bozulmuyor, hafifçe daralıyor**
   (p10 9,11→9,55; p90 15,68→15,47) ve poz belirsizliği reddi hiç tetiklenmiyor.
   Uçuşta sonuç: **%27 → %73 kabul.**

3. **Tarama hızı isteği kendini yeniliyor.** Otopilot `DO_CHANGE_SPEED`'i
   `ACCEPTED` dönüp AUTO bacağı yeniden başlayınca `WPNAV_SPEED`'e dönüyordu
   (bir duruş 6,75 m/s'de olup görevi iptal etmişti). Ölçülen hız isteği
   `search_speed_margin_mps` kadar aşarsa istek yenileniyor. Uçuşta tarama hızı
   ortanca 2,24, en yüksek 2,55 m/s — sapma yok.
   `center_search_speed_mps` üst sınırı 3 → **8 m/s**; `stop_timeout_s` 5 → 8 s.

4. **Görev süresi ve tur başa sarma.** `mission_deadline_s=510` (8:30) dolunca
   yarım kalan her iş bırakılıp LAND waypointine gidilir; `intercept_deadline_s=450`
   sonrası yeni hedefe durulmaz; `search_laps=3` tarama bölümünü tekrarlar
   (yük kaldıysa `search_start_seq`'e döner). Sayaç **AUTO devralma anından**
   başlar — yarışma saati daha erken başlıyorsa 510 düşürülmeli.
   Süre sonu SITL'de uçtu; **tur başa sarma gerçek uçuşta henüz tetiklenmedi.**

5. **`scripts/route_digest.py --write` artık `search_start_seq`/`search_end_seq`
   alanlarını da rotadan türetiyor.** Rota uzayınca parmak izi güncellense bile
   tarama aralığı eski kalıyor ve denetleyici hiç devralmıyordu; sahada iki kez
   bu oldu (10 m → 15 m geçişinde LAND seq 6'dan 8'e taşındı).

6. **Yeni teşhis araçları.** `scripts/ucus_raporu.py` (durum akışı, fren
   mesafesi, bırakma anı, takip kanıtı, **bütün karar sebepleri sayılarıyla**)
   ve `scripts/pnp_teshis.py` (PnP ret sebepleri). İkisi de yalnız kaydı okur,
   `python3` ile çalışır, görev çalışırken güvenlidir.

### Doğrulanan çalışan ayarlar (12 Eylül uçuşu)

| Alan | Değer |
|---|---|
| Rota | 15 m, TAKEOFF seq1, tarama **seq 2–7**, LAND seq8, digest `0c63f72a…` |
| `max_plane_tilt_deg` | **30.0** |
| `center_search_speed_mps` | 2.5 (FC `WPNAV_SPEED=1000` kalabilir) |
| `stop_timeout_s` | 8.0 |
| `tracking` | enabled, köprü≤3 kare, kayıp>8 kare, onay 2 kare |
| `search_laps` / `mission_deadline_s` | 3 / 510 s |

### Saha işletim sırası (Pi terminali)

```bash
# 0) Rota Mission Planner'da DEĞİŞTİYSE (görev kapalı, araç DISARM):
python scripts/route_digest.py --write config/ana-imx708.json
# 1) Yükler yeniden takıldıysa YENİ sortie_id (defterde kaydı olan kimlik reddedilir)
# 2) Ortam:
cd /home/furkan/Documents/proje/hailo-rpi5-examples && source ./setup_env.sh \
  && cd /home/furkan/Desktop/safak-gorev2-quad \
  && export PYTHONPATH="$PWD/runtime/python:$PWD:$PYTHONPATH"
# 3) python -m safak_gorev2.competition.main --config config/ana-imx708.json --check
# 4) ... --mode flight
# 5) İniş sonrası: python3 scripts/ucus_raporu.py && python3 scripts/pnp_teshis.py
```

**İkinci uçuş için program MUTLAKA yeniden başlatılmalı:** iniş sonrası durum
`DONE`/`INCOMPLETE` kalıcıdır, aynı süreç bir daha devralmaz.

### Tuzaklar (bu oturumda ikisine de düşüldü)

- **Profil dosyalarının yetkili kopyası Pi'dedir.** Mac'ten `config/*.json`
  rsync'lemek `sortie_id`, `mission_fingerprint` ve `search_end_seq` gibi saha
  alanlarını ezer. Pi'de düzenle, Mac'e çek.
- **`route_digest.py` ile görev süreci aynı anda çalışamaz.** İkisi de
  Pixhawk'ın USB portunu açar; çakışınca MAVLink düşer
  (`multiple access on port`). Önce `pgrep -af competition.main` ile bak.

### Açık işler

- **`max_descent_mps=0.25` en büyük zaman gideri.** 15 m→5 m alçalma ~40 s;
  hedef başına. Büyük sahada 0,8–1,0 m/s değerlendirilmeli. **Kullanıcı kararı
  bekliyor, değiştirilmedi.**
- Büyük saha için irtifa/hız seçimi. Fren modeli `v²/(2·2,5)+0,3v` saha
  kaydıyla doğrulandı (2,49 m/s→1,9 m; 7,04 m/s→11,9 m). Hedefin frenden sonra
  kadrajda kalması için: 10 m'de 4,6 m/s, 15 m'de 5,8 m/s, 20 m'de 6,8 m/s,
  25 m'de 7,7 m/s. 1 m'lik kırmızı hedef ~30 m'de alan eşiğine dayanır.
- PnP hâlâ %27 reddediyor (%98'i `metric_geometry`). 35° ile ~%85 olur;
  73% ile görev tamamlandığı için zorlanmadı.
- `tests/run_competition_sitl.py` `quick/false-target` ve `quick/no-target`
  senaryoları **bu oturumdan bağımsız olarak** bozuk; takip açık/kapalı aynı
  şekilde başarısız. `false-target` yalnız AI kutusunu gizliyor ama boru hattı
  AI okumuyor; `no-target` `INCOMPLETE` bekleyip `ABORTED` alıyor.
- Tur başa sarma (`search_laps>1`) gerçek uçuşta hiç tetiklenmedi.

### Testler

Mac 408 geçti / 5 atlandı (4 Torch, 1 ayrı MOSSE ortamı). Pi'nin Hailo
ortamında 106 ilgili test geçti. Takip maliyeti Pi'de 33,9 µs/kare; tam vision
aşaması takip açıkken 4,51 ms, kapalıyken 4,68 ms (fark gürültü içinde).
Ayrıntı `docs/competition/TESTLER.md` ve `docs/competition/HEDEF_TAKIBI.md`.


## DEVİR — 12 Eylül AUX3 açılış nötrü ve iki-yük profil

- Kullanıcı ikinci yükü taktı. AUX3/11 `FUNCTION=0` ve çıkış 0 µs, RC11 ise 1495 µs stabil bulundu. Kullanıcı onayıyla yalnız `SERVO11_FUNCTION=61` yazılıp geri okundu; AUX3 servo komutu olmadan 1495 µs nötr çıkışa geçti. Uçuş bırakması kanal11 800 µs/0,3 s, ardından 1500 µs olarak aynıdır. ARM/mod/servo komutu verilmedi.
- Aktif iki-yük profil `config/ana-imx708.json`, sortie `20260911T213056Z-ana-imx708`, digest `084b315891c3cee52707fd65beb970bd58f77b5505370365e6a8cb3c4dbbc47e`. AUX1-only profil tek-yük yedeği olarak korunur.

## DEVİR — 11 Eylül rota anlık 15 m görünüp 10 m'ye geri döndü

- Kullanıcı `7c96…4c13` digest'li TAKEOFF1/WP2–9=15 m, LAND10 çıktısı paylaştı; salt okunur ilk Pi kontrolü bunu doğruladı. Profil kısa süre bu rotaya eşlendi. Birkaç saniye sonra FC iki ardışık okumada yeniden eski/onaylı TAKEOFF1/WP2–6=10 m, LAND7 ve `517211…bfae` rotasını verdi. Pi'de rota yazan süreç/service yok; değişim dış GCS tarafındandı.
- Kullanıcının önceki açık kararı “takeoff 10 kalsın” ve kararlı canlı FC rotası esas alındı. `ana-aux1-only.json` tekrar start2/end6/digest `517211…bfae` yapıldı ve Pi son salt okunur kontrolünde **EŞLEŞİYOR**. İlgili 89 yerel test geçti. FC rotasına yazı, servo, ARM, mod veya parametre komutu gönderilmedi. Yedek `runtime/before-aux1-route15-20260911/`.

## DEVİR — 11 Eylül düşük bant genişlikli etiketli canlı panel

- Kullanıcı 300 m bağlantıda anlık etiketli kamera görüntüsü istedi. Mevcut `/competition` paneli OpenCV hedef kutusu/rengi ve görev durumunu zaten gösterir. Plain UDP yerine her karesi bağımsız HTTP JPEG tutuldu; bozuk/kayıp kare sonraki kareyi zincir halinde bozmaz ve tarayıcı dışında alıcı gerekmez.
- Ana `competition-base.json` panel çıkışı 960px/8fps/Q65 → **640×360, 4 FPS, JPEG Q35** yapıldı. Kamera/vision kontrol hattı 1280×720@50 FPS kalır; yalnız panel önizlemesi küçülür. Etiket/çerçeve artık küçültmeden sonra çizilir, yazı okunurluğu korunur. Yerel 350 geçti/5 atlandı.
- Erişim aynı ağdan `http://192.168.137.145:8081/competition`. Pi dağıtıldı; 56 ilgili test geçti. Gerçek IMX708 probe: 1018 kare/50,03 FPS, hata yok; örnek etiketli JPEG 11.536 bayt, 4 FPS'te yaklaşık **369 kbit/s**. Kanıt `artifacts/low-bandwidth-panel-20260911/`. 300 m menzil yazılımla garanti edilemez; 2,4 GHz radyo/AP, anten görüş hattı ve RSSI belirleyicidir. Yedek iki tarafta `runtime/before-low-bandwidth-panel-20260911/`.

## DEVİR — 11 Eylül yalnız AUX1 takılı tek-yük sortie'si

- Kullanıcı fiziksel durumu doğruladı: yalnız AUX1/kanal9'daki mavi yük takılı, AUX3 sonra düzeltilecek; AUX1 bırakılabilir. Yeni `config/ana-aux1-only.json`: gerçek servo, sortie `20260911T194157Z-aux1-only`, payloads yalnız `mavi`, canlı rota digest `517211…bfae`, tarama Seq2–6, 3 m/s, hedefte 5 m.
- Controller yalnız kırmızı hedefi kabul eder (kırmızı hedef→mavi/AUX1 yük). Mavi hedef tamamen yok sayılır. AUX1 ACK+çıkış doğrulanınca takılı bütün yükler tamamlanmış sayılır ve doğrudan LAND7 seçilir. AUX3'e PARAM isteği veya servo komutu gönderilmez; link katmanı payload izin listesini ayrıca uygular.
- Genel iki-yük profillerinin davranışı değişmedi; payloads alanı yoksa iki yük varsayılır. Yerel 347 geçti/5 atlandı; Pi ilgili 73 geçti ve yeni profil `--check` eksiksiz. Pi'ye dağıtıldı, yedek iki tarafta `runtime/before-aux1-only-20260911/`. Canlı AUX1 parametre kontrolü yeni süreç açılınca yapılır; eski DONE süreci kapatılmadı.

## DEVİR — 11 Eylül ana OpenCV tarama hızı 3 m/s

- Kullanıcı 10 m'lik yeni rotayı kabul etti ve ana AUTO tarama hızını 1,5→3,0 m/s istedi. `ana-gorev.json`, `ana-imx708.json`, `ana-opencv-test.json` 3,0 m/s oldu; doğrulama üst sınırı yalnız ana görev için 3 m/s'ye çıkarıldı. Kalıcı FC parametresi yazılmadı; komut geçici `MAV_CMD_DO_CHANGE_SPEED` olarak kalır.
- Merkezleme/alçalma limitleri değişmedi: hedefte fren sonrası GUIDED merkezleme, 5 m hedef yükseklik, 0,25 m/s aşağı hız ve 0,2 m/s² ivme sınırı. 3 m/s frenleme hedefin kadrajdan çıkma riskini 1,5 m/s'ye göre artırır.
- Yerel 345 geçti/5 atlandı; Pi ilgili 64 geçti. Yedek iki tarafta `runtime/before-search-speed-3mps-20260911/`. Canlı rota TAKEOFF1/WP2–6=10 m, LAND7 ve digest `517211…bfae`; simulated `ana-opencv-test.json` zaten birebir eşleşiyor. Gerçek servo ana profillerinin digest/sortie'si payload fiziksel durumu doğrulanmadan değiştirilmedi.

## DEVİR — 11 Eylül yeni 15 m rota / 5 m merkezleme yüksekliği

- Ana OpenCV merkezleme görevinde tarama Mission Planner `Seq 2` ile başlayacak; hedef ortalanınca 5 m kamera yüksekliğine inilecek. `ana-gorev.json`, `ana-imx708.json` ve `ana-opencv-test.json` başlangıç2 oldu.
- Ana kontrol `target_camera_height_m=5.0`, güvenlik alt sınırı `minimum_camera_height_m=3.0`; yumuşak iniş 0,25 m/s ve ivme sınırı 0,2 m/s² korundu. 15→5 m ideal iniş yaklaşık 40 s.
- Yeni rota henüz tamamlanmadı: digest, tarama bitiş sırası, sortie, servo ve FC değiştirilmedi. Rota yüklenince canlı rota okunup LAND öncesi son sıra ve digest üç ana profile eşlenmeli. Yerel 344 geçti/5 atlandı; Pi ilgili 115 geçti (hızlı profil sapmasına bağlı 3 envanter örneği seçilmedi). Yedek iki tarafta `runtime/before-5m-descent-20260911/`.
- Pi'de eski `ana-opencv-test` süreci hâlâ açık fakat kontrolde DISARM/LANDED/DONE idi; kapatılmadı. Süreç eski 9 m ayarını bellekte taşır. Yeni rota uçuşundan önce eski terminalde Ctrl+C ve yeniden başlatma şarttır.

## DEVİR — 11 Eylül kırmızı hedefte sert iniş acil düzeltmesi

- `competition-2f3a08cb283f45de9e3d9f0866133b76.jsonl` kaydında merkezleme çalıştı. Kod DESCENDING'de en çok 0,281 m/s aşağı hız istedi. Sert iniş, 329,651 s'deki hedef kaybı sonrası eski `GUIDED→LOITER` iptalinden sonra başladı; LOITER'da düşük gazla gerçek vd yaklaşık 2,59 m/s'ye çıktı.
- Yarışma hedef etkileşimi iptali artık sıfır hızdan sonra onaylı AUTO rotasına döner ve sahipliği bırakır; alt merkezleme Controller'ın LOITER eylemi yarışma sınırında değiştirilir. Komut kirası/kapanış failsafe'i de yalnız CompetitionLink'te AUTO'dur. Pilot mod müdahalesi zorlanmaz; LAND seçim hatasında rotaya dönülmez.
- Yumuşak alçalış korumaları da aktif: 0,25 m/s limit, 0,2 m/s² ivme rampası, 7 PnP örneği medyanı ve aşağı hız aşımında stop. Yerel tam test **344 geçti / 5 atlandı**; Pi kritik testleri **125/125** geçti. Pi tam dizisi 301 geçti, yalnız daha önceden bilinen hızlı profil start2/start3 sapması kaldı. Kanıt `artifacts/soft-descent-20260911/before-fix-flight.jsonl`.
- Düzeltme Pi `192.168.137.145` üzerine yüklendi; öncesinde uygulama kapalı ve FC DISARM idi. Ana OpenCV test profili rota digest'iyle eşleşti. Yedek iki tarafta `runtime/before-auto-abort-20260911/`. Uçuş/servo/ARM/mod/FC parametresi gönderilmedi.

## DEVİR — 11 Eylül yarışma hattı yalnız OpenCV

- Kullanıcı açıkça YOLO'yu kaldırıp yalnız OpenCV kullanılmasını istedi. Aktif ana ve hızlı görev kamerayı doğrudan Picamera2/V4L2 → OpenCV hattından alır. Yarışma giriş noktası Hailo backend'ini yüklemez, model dosyasını doğrulamaz ve Frame.detections boş üretilir. Yarışma kaydedicisi de bu profillerde HEF/model bağımlılığı taşımaz.
- Tek görüntü adayı HSV mavi/kırmızı maskesi ile dolu, dışbükey dörtgendir. Hızlı görev ardışık OpenCV kutularını; ana görev aynı bölgeden çıkan köşe/PnP ölçümünü kullanır. Merkezleme, hız/yükseklik kilitleri ve servo güvenlikleri korundu. Görüntüye eklenmiş AI metadata'sı karar zincirinde yok sayılır. Artık kullanılmayan competition/bbox.py kaldırıldı.
- Doğrulama: yerelde 343 geçti/5 atlandı. Pi'de 300 geçti; tek kalan hata bu işten bağımsız mevcut profil sapmasıdır: Pi hizli-gorev.json başlangıç3 ve yerelden farklı digest taşıyor; yerel/onaylı hızlı profil başlangıç2. Rota/digest/sortie bu işte değiştirilmedi.
- Pi gerçek kamera probe'u MAVLink bağlantısız observe/connect=False: 20 s, 1028 kare, 50,02 FPS, stale0, hata0, OpenCV toplam p95 4,08 ms. Kanıt artifacts/opencv-only-20260911/ altında. Ortam karanlıktı: görüntü alanında V medyan 2, p99 8; mevcut min_value=35 ile mavi/kırmızı renk maskesi %0. Bu ışıkta renk tespiti saha kabulü değildir; hedefler güçlü ve homojen aydınlatılmadan uçulmaz. Yedek iki tarafta runtime/before-opencv-only-20260911/.
- Uçuş hâlâ hazır değil: canlı FC'de kırmızı AUX3/11 FUNCTION0 iken profiller FUNCTION61 bekliyor; ayrıca Pi hızlı rota profili sapmış durumda. Servo/ARM/mod/FC parametresi gönderilmedi, görev uçuş modu başlatılmadı.

## DEVİR — 11 Eylül AUX3 açılış hareketi için nötr PWM hazırlığı

- Canlı salt okunur incelemede AUX3/11 `FUNCTION=0`, çıkış `0 us`, RC11 ise sabit `1495 us`. FUNCTION0 PWM üretmediğinden kırmızı servo uygulama başlamadan sinyalsiz kalıyor.
- Ana IMX708/genel/Arducam ve hızlı profillerde kırmızı servo beklentisi `function=61` (RCIN11 passthrough) yapıldı; 800 us/0,3 s bırakma ve 1500 us sonlandırma korunuyor. Test düzenekleri de gerçek işlevi bekliyor.
- **FC parametresi ve fiziksel servo henüz değiştirilmedi/test edilmedi.** Mevcut FUNCTION0 ile yeni profil uçuşu güvenli biçimde reddeder. Kırmızı yük ayrıldıktan ve kullanıcı parametre yazımını onayladıktan sonra `SERVO11_FUNCTION=61` uygulanıp yeniden enerjileme tezgâhta gözlenmeli. İlk enerji anındaki hareket sürerse donanımsal besleme geciktirme/pull-down ve mekanik emniyet gerekir. Yedek: `runtime/before-servo-startup-neutral-20260911/`.
- Doğrulama: yerel 351 geçti/5 atlandı; Pi 309 geçti; dağıtılan dosyaların SHA256 değerleri eş.

## DEVİR — 11 Eylül tarama ikinci waypoint geçildikten sonra

Kullanıcı ilk direği Mission Planner sıra 2 yaptığını, taramanın bundan sonra başlamasını istedi. Ana IMX708/genel profillerde `search_start_seq=3`: sıra2'ye giderken hedefe devralma yok; FC sıra3'e geçtiğinde tarama açılır. Hızlı profil başlangıcı2 ve davranışı korundu. Mission kapsamı artık TAKEOFF sonrası seçilen başlangıcı kabul eder; LAND öncesi bitiş ve waypoint komutları zorunlu. İki stratejide sıra2 bekleme/sıra3 duruş regresyonu eklendi. Yerel351 geçti/5 atlandı. Pi test sonucu `runtime/before-search-seq3-20260911/tests-pi.txt` yerel kaydında. İki tarafta aynı adlı yedek var.

Kullanıcı yerde/DISARM olduğunu, rotanın hâlâ düzenlendiğini söyledi. Yeni digest onaylanmadı/okunmadı; sortie/servo/FC değişmedi. Yeni rota tamamlanınca digest ve son tarama sırası eşleştirilmeli. Önceki sohbetin rota güncelleme bloğu başlangıcı TAKEOFF+1'e geri çevirir; ana görevde `start=3`, `end=plan.land_seq-1` kullanılmalı. Yalnız digest yazan route_digest.py başlangıç3'ü korur.

## DEVİR — 11 Eylül 15:05 ana görev kurtarma; hızlı görev korundu

- Kullanıcı hızlı görevi yedek olarak korumamızı istedi. **Hızlı profil/base dosyaları SHA256 ile aynı**, servo/rota/digest/sortie değişmedi. Ana düzeltmeler Pi'ye yüklendi; iki tarafta `runtime/before-center-recovery-20260911/` yedeği var.
- 13:40–13:47 uçuş kayıtları: maviye GUIDED istenmiş fakat 5,7 m/s hızdan fren sırasında 8–9 m ilerlenip hedef kaybedilmiş. Kırmızı duruşunda seyrek PnP doğrulaması 0,5 s kilidi tamamlayamamış; INTERCEPT/servo yok. Buzzer'ın kesin nedeni eski kayıtta yok.
- Yalnız ana IMX708/genel profilde **geçici AUTO tarama hızı 1,5 m/s**, doğrulama süresi 3→8 s. Her AUTO tarama girişinde DO_CHANGE_SPEED ACK beklenir. Kalıcı WPNAV_SPEED=1000 değiştirilmez. Hızlı görev bu komutu üretmez. Alan/rota/RC/taze veri ve pilot korumaları sürer.
- Ana PnP önce eski köşeleri kullanır; yalnız reddedilirse gerçek renk kenarında en çok 3 px alt piksel köşe düzeltmesi dener. Önceki kabul edilen ölçümler ve bütün geometri eşikleri korunur. Ana JSONL artık karar girdisini, köşeleri/pozu ve FC STATUSTEXT'i kaydeder.
- **Yerel 349 geçti/5 atlandı; Pi 307 geçti.** ArduCopter 4.6.3 hexa SITL ana görev iki hedefte merkezleme, iki simulated yük ve LAND/DONE (71,97 s); güncel mission kapsamındaki hızlı görev iki simulated yük ve LAND/DONE (47,07 s), velocity/search_speed yok. Eski field kapsamlı hızlı SITL giriş kapısını doğrulayamadı; üretim hızlı kodu değiştirilmeden güncel saha kapsamıyla test edildi. Önceki “SITL yok” notu güncel değil; macOS binary `/private/tmp/safak-ardupilot-4.6.3/build/sitl/bin/arducopter` mevcut.
- Pi kamera/Hailo: 20 s, 1040 kare, 50,08 FPS, stale0/hata0; MAVLink bağlantısız probe. Canlı rota salt okunur yeniden eş: TAKEOFF1 10 m, waypoint2–6 10 m, LAND7 1 m; digest `b652eeb66c71e0a4ff02d9c9e8c2e8a2c10313974a3089203f62eed45dc51acb`.
- Gerçek uçuşun eşzamanlı videosu olmadığından kırmızı PnP düzeltmesinin saha kabulü **yok**; yaklaşık kalibrasyon sürüyor. Sonraki uçuşta `decision_input.diagnostics` incelenmeli. Kırmızı açılış servosu kullanıcı isteğiyle ertelendi; nötr komutu açıkça reddedilmişti. Canlı FC'ye servo/ARM/mod/parametre yazma komutu verilmedi; uçuş uygulaması başlatılmadı.
- Ayrıntı: `docs/competition/ANA-KURTARMA-20260911.md`; kanıt: `artifacts/center-flight-1347-20260911/`. Ana uçuş komutu ve sortie aynı; yeni dosyalar sonraki süreç açılışında yüklenir.

## DEVİR — 11 Eylül yeni saha: TAKEOFF–LAND arası tüm rota taraması

- **Dağıtım/kontrol tamam:** yerelde 324 geçti / 5 atlandı, Pi’de 282 geçti. Ana profil --check eksiksiz, canlı rota digest eş. Kamera/Hailo 20 s: 1017 kare, 50,06 FPS, stale0, hata0. Görev uçuş süreci başlatılmadı; kamerayı açan yalnız MAVLink bağlantısız probe idi ve temiz kapandı.
- Kullanıcı yeni rota yükledi ve açıkça “takeoffdan lande kadar tara” dedi. Ana IMX708, ana genel ve hızlı profiller `search_scope=mission` olarak güncellendi: 10 m TAKEOFF1, tüm WAYPOINT2–6 taranır, LAND7'de arama biter. Yeni digest `b652eeb66c71e0a4ff02d9c9e8c2e8a2c10313974a3089203f62eed45dc51acb`. LAND satırı z=1 m olarak FC'den okundu; FC rotası değiştirilmedi.
- Mission kapsamı eski saha kapısı/poligonunu uygulamaz; koordinat uydurulmadı. Varsayılan field kapsamında eski kapı/poligon korumaları sürer. Mission kapsamında da rota parmak izi, bütün waypoint aralığı, minimum devralma irtifası, taze telemetri/görüntü, pilot müdahalesi ve yerde başlatma şartları korunur. FC fence ayarları değiştirilmedi.
- Kullanıcı fiziksel durumu doğruladı: yerde/DISARM, yalnız mavi yük takılı; kırmızı güç verilir verilmez, görev açılmadan düşüyor. Salt okunur AUX3/11: FUNCTION0 MIN800 MAX1900 TRIM1500, bildirilen çıkış0; AUX1/9 RCIN8 FUNCTION58, bildirilen çıkış2006. Kırmızı açılış sorununun kesin nedeni henüz doğrulanmadı. Kullanıcı nötr servo denemesini reddetti, ardından kırmızı incelemesini erteleyip uçuş hazırlığı istedi. **Servo/ARM/mod/FC parametre komutu verilmedi.** Servo eşlemeleri, aktüatör seçimi ve sortie kimlikleri değiştirilmedi; ana görev hâlâ gerçek servo profilidir.
- Yedek iki tarafta `runtime/before-full-route-20260911/`; kanıt `artifacts/route-servo-startup-20260911/`. Önceki gerçek uçuş tekrar testi profil bağımlılığından ayrılarak kayıttaki saha ayarlarına sabitlendi. Yeni testler tüm waypointler/iki renk/iki stratejide duruş, TAKEOFF/LAND/düşük irtifa/yanlış digest/eksik aralık/havada başlatmada ret ve link korumalarını kapsar.

## DEVİR — 11 Eylül 13:10 sonrası ana görevde durmama düzeltmesi

- **Yeni kök neden:** 12:47 ve 12:53 ana uçuşlarında AUTO kalkış/giriş noktası poligon dışındaydı. `DualController` giriş kapısından önce kalıcı `ABORTED` oluyordu; sonradan alana girse de aramıyordu. Kayıtlarda toplam **45 mavi + 51 kırmızı** tespit var. Önceki rota parmak izi hatasından ayrı bir sorun.
- **Düzeltme Pi'de:** giriş kapıları geçilmemiş ve henüz kontrol devralınmamışsa poligon dışında komutsuz bekle. Kapı/alan/tarama koşulları sağlanınca arama başlar. Giriş sonrası sınır ihlali, pilot müdahalesi ve MAVLink poligon koruması aynen sürer. Ortak akış iki stratejide düzeltilmiştir.
- **Doğrulama:** iki gerçek kayıtta iki renk ayrı ayrı oynatıldı; dört senaryoda da artık GUIDED duruş isteği oluşuyor. Eski kodla 7 yeni test başarısız, yeni kodla 9/9 başarılı. Yerel **305 geçti / 5 atlandı**, Pi **263 geçti**. Yedek iki tarafta `runtime/before-entry-polygon-20260911/`.
- FC rotası salt okunur yeniden doğrulandı: 15 m, tarama 2–8, LAND 9, digest `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707` ana profille eşleşiyor. Rota/digest/sortie/servo/FC parametreleri değiştirilmedi. Görev/kayıt kapalı; ARM/mod/servo komutu gönderilmedi.
- **Saha sınırı:** son iki uçuşta AUTO geçişindeki seyrek geometri örnekleri 10/46 kabul (~%22), fakat hiç GUIDED duruşu yok. Bu oran duruş sonrası PnP başarımı değildir. Düzeltme sonrası gerçek merkezleme/bırakma henüz uçulmadı; sonraki uçuşta STOPPING/VERIFYING/INTERCEPT verileri ölçülmeli. Kalibrasyon hâlâ deneysel.
- Ayrıntı: `docs/competition/ANA-DURMAMA-20260911.md`. Kanıt: `artifacts/center-investigation-20260911/`. Yeniden oynatma: `tests/test_entry_polygon.py`, kaynak kesitleri `tests/fixtures/entry-polygon-20260911.json`. Diğer ortam/profil/çalıştırma bilgileri aşağıdaki önceki DEVİR bölümünde.

## DEVİR — 11 Eylül 2026 kapanış durumu (yeni sohbet buradan başlasın)

### Ortam
- Yerel: `/Users/kaan/Documents/ChatGPT/last şafak` (venv: `.venv/bin/python`). Pi: `furkan@172.20.10.6`, proje `/home/furkan/Desktop/safak-gorev2-quad`.
- Pi'de her komuttan önce: `cd /home/furkan/Documents/proje/hailo-rpi5-examples && source ./setup_env.sh && cd /home/furkan/Desktop/safak-gorev2-quad && export PYTHONPATH="$PWD/runtime/python:$PWD:$PYTHONPATH"`.
- Pixhawk Cube Orange, by-id `...CubeOrange...-if00`, MAV_TYPE 13 hexa, firmware 4.6.3. Kamera IMX708 CAM1, 1280×720 @50 FPS, sensör modu 2304×1296, LensPosition 0. Model `best_hailo_model/safakyepyeni.hef`.
- FC canlı değerler (salt okunur): `WPNAV_SPEED=1000`, `WPNAV_ACCEL=250`, `SERVO9_FUNCTION=58 MIN1100 MAX1900`, `SERVO11_FUNCTION=0 MIN800 MAX1900`.

### Görev profilleri
- Ana: `config/ana-imx708.json` (strategy=center), hızlı: `config/hizli-gorev.json` (strategy=quick). İkisi de actuator=servo.
- Rota FC'de **15 m**: seq1 TAKEOFF 15, seq2–8 WAYPOINT 15, seq9 LAND. Tarama 2–8. Üç profilin `mission_fingerprint` değeri `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707`.
- Servo eşlemesi (tezgâhta doğrulandı, sahada iki yük düştü): mavi AUX1/kanal9 → 1800 µs; kırmızı AUX3/kanal11 → 800 µs, 0,3 s sonra 1500 µs nötr. Mavi hedef görülünce kırmızı yük, kırmızı hedef görülünce mavi yük bırakılır.
- İki yük kabul edilince kalan tarama waypointleri atlanıp **doğrudan LAND waypointine** uçulur (`SELECT_LAND` → `HANDOFF_LAND` → `LANDING`).

### Saha sonucu
- Hızlı görev sahada **tam başarılı**: iki yük de gerçek servo komutuyla bırakıldı (`20260911T082504Z-hizli-imx708`).
- Ana görev henüz başarılı bir bırakma yapmadı. Son denemede model 25–30 m'de 39 mavi + 60 kırmızı gördü ama profil rota parmak izi eski olduğu için kontrol hiç devralmadı; parmak izi düzeltildi.
- Aktif ana sortie `20260911T093750Z-ana-imx708`; payload ledger'da kaydı yok, yükler takılıysa aynı kimlik kullanılabilir. Ledger `runtime/competition/payload-ledger/payloads.sqlite3`.

### 11 Eylül'de yapılan düzeltmeler (hepsi Pi'de yüklü, testler geçti)
1. `competition/bbox.py` → `clamp_bbox`: kadraj kenarına taşan YOLO kutusu atılmıyor, kırpılıyor; alanının %60'ı kadraj dışındaysa reddediliyor. (Mavi 42 tespitin 35'i eleniyordu.)
2. `color_search.detect(border_px=0)`: kenara değen renk bölgesi aday olmayı engellemiyor; metrik ölçümün kendi kenar payı (`corner_screen`) duruyor.
3. `competition/controller.py`: frenleme (STOPPING) aşamasında kutu örtüşmesi koparsa, seçilen renkten tek aday varsa hedef yeniden yakalanıyor. Doğrulama (VERIFYING) aşamasında kural katı.
4. `competition/controller.py`: ana görevde VERIFYING sırasında PnP çözülmeyen kare veya kısa hız sıçraması birikimi silmiyor, yalnız saymıyor.
5. `controller.py` (legacy, özgün kopya `archive/legacy-options/controller-before-center-hold-gap.py.txt`): merkez/bırakma kilidi geometri boşluğunda silinmiyor; 0,25 s'yi aşmayan boşlukta son hız komutu korunuyor (en çok ~20 cm kör hareket), sonra duruyor, `lost_target_abort_s` (2,5 s) aşılırsa iptal.
6. `competition/link.py`: WPNAV_SPEED üst sınırı iki görevde de 1000 cm/s (kullanıcı kararı; fren ~3 s sürer).
7. `config/competition-base.json` ana görev ayarları: bırakma yüksekliği 9 m sabit; `max_descent_mps` 1,0; `max_climb_mps` 1,0; `interaction_timeout_s` 200; `center_tolerance_m` 0,5; `descent_center_tolerance_m` 0,7; `height_tolerance_m` 1,0; `minimum_camera_height_m` 7,0; `release_horizontal_speed_mps` 0,3; `release_vertical_speed_mps` 0,2; `lost_target_abort_s` 2,5; `max_horizontal_speed_mps` 0,8; **`center_tolerance_height_ratio` 0,05** (kilit toleransı = `max(0,5; 0,05×görsel yükseklik)`; 15 m'de 0,75 m, 9 m'de 0,5 m).
8. `scripts/route_digest.py`: rotayı salt okunur okur, irtifaları ve digest'i yazar; `--profile` karşılaştırır, `--write` yalnız `mission_fingerprint` alanını günceller.

### Ölçülen gerçek değerler (parametrelerin dayanağı)
- PnP saçılması 10 m'de: yatay sd 0,12 m, görsel yükseklik sd 0,39 m, reprojeksiyon 0,66 px. Gürültü yükseklikle büyür (yatay ≈0,012×h, yükseklik ≈0,0039×h²).
- GUIDED duruşunda araç sürüklenmesi 0,20–0,27 m/s. Fren 1000 cm/s'den ~3 s; WPNAV_ACCEL 250 → ~14° yatış → 15 m'de ~3,8 m görüntü kayması.
- Metrik geometri (PnP) başarımı fren sırasında **%26** ölçüldü. Benzetime göre ana görevin bırakma yapabilmesi için **≥ %40** gerekiyor.
- 25–30 m'de tespit boyutu: mavi ~75 px, kırmızı ~43 px, skor ~0,62.

### Açık işler
1. **Ana görev uçuşu**: uçuştan sonra JSONL'deki `diagnostics` alanından gerçek PnP başarım oranı ölçülmeli. %40'ın altındaysa geometri/kalibrasyon tarafı düzeltilmeli.
2. Kamera kalibrasyonu `config/camera.imx708-infinity-approx.json` hâlâ **yaklaşık/deneysel; saha kabulü yok** (kalibrasyon lens pozisyonu 0,106, çalışma 0,0). Merkezleme doğruluğu bağımsız ölçülmedi.
3. Rota değişirse `scripts/route_digest.py --profile ...` ile kontrol, `--write` ile güncelleme şart; yoksa yazılım devralmaz.
4. Bu makinede ArduPilot SITL yok; doğrulama birim testi + benzetim seviyesinde (yerel 296, Pi 254 test geçiyor).

### Çalışma kuralları
- Kullanıcı kısa ve Türkçe yanıt istiyor; projeyi yeniden anlattırma.
- Kullanıcı açıkça istemeden **yerde servo komutu verme** (yükleri düşürür), **ARM veya uçuş modu komutu gönderme**.
- FC parametresi yazmadan önce sor. Rota/digest/sortie değişikliklerinde fiziksel durumu (yükler takılı mı) kullanıcıya doğrulat.
- Değişiklikleri Pi'ye yükle, iki tarafta da testleri çalıştır, `runtime/before-*` altına yedek al, AGENTS.md ve docs/HANDOFF.md başına özet yaz.
- `docs/competition/legacy-sha256.json` ile korunan dosyalar değişecekse özgün kopya `archive/legacy-options/` altına alınıp `preserved-paths.json` eşlemesine eklenir.

### Çalıştırma
```
# uçuş öncesi rota kontrolü
python scripts/route_digest.py --profile config/ana-imx708.json
# görev (kamerayı bu açar)
export MAVLINK20=1
python -m safak_gorev2.competition.main --config config/ana-imx708.json --mode flight
# kayıt (ayrı terminal, görevden sonra)
python -m safak_gorev2.record --config config/ana-imx708.json --panel-url http://127.0.0.1:8081 --root runtime/recordings
```
Panel `http://172.20.10.6:8081`. Kapatma: önce kayıt, sonra görev (Ctrl+C).

## En güncel — 11 Eylül 15 m rota parmak izi ve "hiçbir şey görmedi" teşhisi

Kullanıcı 25 m denemesinde hiçbir şey görülmediğini bildirdi. Kayıt bunun tersini gösteriyor: `runtime/competition/center-imx708/competition-d84a29d9...1468.jsonl`, 547 kayıt, **39 mavi + 60 kırmızı tespit** (irtifa 24,9–30,0 m; mavi kutu ortalama 75×73 piksel, kırmızı 43×42 piksel; skor ortalama 0,62) ve 115 aday. Yani model yüksekten görüyor.

Kontrol hiç devralmadı: durum baştan sona `WAIT_AUTO` ve gerekçe **"Rota parmak izi onaylanan rotayla eşleşmiyor"**. FC'deki rota 15 m'ye güncellenmişti (seq1 TAKEOFF 15 m, seq2–8 waypoint 15 m, seq9 LAND), profillerdeki parmak izi ise eski 10 m rotasına aitti. Yazılım doğru davrandı; 52. saniyede pilot LOITER aldı.

Canlı rota salt okunur okundu ve üç profilin `mission_fingerprint` alanı `54b32d9b…747fe` → `60ce13f81939f3a669faebf0e9de6658b2e285f54f6703b701fc662dde842707` olarak güncellendi (`scripts/route_digest.py --write`). Araca `--profile` seçeneği eklendi: rota ile profili karşılaştırıp EŞLEŞİYOR/EŞLEŞMİYOR yazar, böylece bu hata uçuştan önce görülür. Rota komutları doğrulandı: tarama bölümü 2–8 yalnız waypoint, LAND 9.

15 m için ayrıca parametre değişikliği gerekmedi; kilit toleransı yükseklikle ölçekleniyor (15 m'de 0,75 m, bırakmada 0,50 m). Benzetim 15 m'den: PnP başarımı %50–%80'de 30–46 s, %40'ta 97 s içinde bırakma; %30 yetmiyor. Test dizisine 15 m eklendi. Yerelde 296, Pi'de 254 test geçti.

Bu sortie (`20260911T093750Z-ana-imx708`) için payload ledger'da kayıt yok — yükler hâlâ takılıysa aynı kimlikle uçulabilir.

## En güncel — 11 Eylül 25 m uçuş ayarı

Kullanıcı 25 m'de uçacağını bildirdi. PnP gürültüsü mesafeyle büyüdüğü için sabit toleranslar bu irtifada kilidi imkânsız kılıyordu: 10 m'de ölçülen 0,12 m yatay saçılma 25 m'de yaklaşık 0,30 m'ye çıkıyor, sabit 0,50 m tolerans 1,5 s kesintisiz kilide yetmiyor. Benzetimde araç 25 m'de 0,04 m hataya kadar merkezleniyor ama 150 s boyunca 24 m'de takılı kalıyordu.

Çözüm: `center_tolerance_height_ratio` (yeni alan, ana profilde 0,05) ile kilit toleransı `max(center_tolerance_m, oran×görsel yükseklik)` olarak hesaplanıyor. 25 m'de 1,25 m, 17 m'de 0,85 m, bırakma yüksekliği 9 m'de 0,45 m — yani sabit 0,50 m baskın kalıyor ve **bırakma isabeti değişmiyor**. Alçalma sapma toleransı aynı oranda ölçekleniyor. `interaction_timeout_s` 150→200 s yapıldı.

Yükseklikle ölçekli gürültü benzetimi (yatay 0,012×h, görsel yükseklik 0,0039×h²): 25 m'den PnP başarımı %50'de 100 s, %60'ta 46 s, %80'de 45 s içinde, 0,03 m'den küçük hatayla 9,4 m'de bırakma. %40'ta 169 s ile ancak 200 s sınırı içinde kalıyor; %30 yetmiyor. Oran 0 iken (eski davranış) 25 m'de bırakma hiç tamamlanmıyor — test bunu koruyor. 35 m'de %60 başarımla 138 s, %80 ile 78 s.

Ana görev için gereken eşik: **PnP başarım oranı en az yaklaşık %40**. 11 Eylül uçuşunda fren sırasında ölçülen %26 yetmez; uçuş JSONL'indeki geometri diagnostics ile gerçek oran ölçülmeli.

25 m rotası için: yeni rota FC'ye yüklendikten sonra digest değişir. Yeni yardımcı `scripts/route_digest.py` rotayı salt okunur okur, irtifaları ve digest'i yazar, `--write <profil>` ile yalnız `mission_fingerprint` alanını günceller (FC'ye komut göndermez, ARM durumda çalışmaz). Rota içeriği gözle doğrulanmadan uçulmaz.

Yerelde 294, Pi'de 252 test geçti. Yedek `runtime/before-25m-20260911/`. Benzetim saha kabulü değildir.

## En güncel — 11 Eylül merkezleme/kamera incelemesi ve ayarı

Kullanıcı merkezlemenin optimal olup olmadığını sordu. 11 Eylül ana uçuşundaki gerçek metrik örnekler ölçüldü (10 m'de, 50–56 s penceresi, 9 örnek): yatay konum saçılması kuzey sd 0,06 m / doğu sd 0,12 m; görsel yükseklik ortalama 9,70 m, sd 0,39 m, aralık 9,04–10,15 m; yeniden izdüşüm hatası ortalama 0,66 piksel. GUIDED duruşunda araç sürüklenmesi 0,20–0,27 m/s ölçülmüştü.

Eski toleranslar bu gürültünün altındaydı: merkez toleransı 0,20 m (gürültü ±0,2 m), yükseklik toleransı 0,25 m (gürültü sd 0,39 m), bırakma yatay hız eşiği 0,20 m/s (sürüklenme 0,27 m/s), alt yükseklik sınırı 8,5 m (9 m hedefte tek gürültülü örnek iptal ettirebiliyordu). Benzetimde eski değerlerle hiçbir PnP başarım oranında bırakma tamamlanmıyor.

Ana profil (`competition-base.json`) ayarlandı: `center_tolerance_m` 0,20→0,50; `descent_center_tolerance_m` 0,30→0,70; `height_tolerance_m` 0,25→1,00; `minimum_camera_height_m` 8,5→7,0; `release_horizontal_speed_mps` 0,20→0,30; `release_vertical_speed_mps` 0,12→0,20; `lost_target_abort_s` 1,0→2,5; `max_horizontal_speed_mps` 0,40→0,80. Bırakma yüksekliği 9 m aynı.

Yapısal iki kusur düzeltildi (`safak_gorev2/controller.py`, özgün kopya `archive/legacy-options/controller-before-center-hold-gap.py.txt` altına alınıp hash eşlemesine eklendi): (1) PnP çözülmeyen her karede merkez/bırakma kilidi siliniyordu, yani 1,5 s ve 3 s kilit için kesintisiz %100 geometri gerekiyordu; artık kilit silinmez, süreklilik `max_lock_frame_gap_s` (0,25 s) boşluk sınırıyla korunur. (2) Geometrisiz her karede hız sıfırlanıyordu; araç adım adım duruyor ve yaklaşma/alçalma neredeyse durma noktasına geliyordu. Artık 0,25 s'yi aşmayan boşlukta son hız komutu korunur (en çok ~20 cm kör hareket), boşluk büyürse durur, uzun kayıpta görev iptal edilir.

Ölçülen gürültüyle benzetim: eski hâlde hiç bırakma yok; yeni hâlde PnP başarımı %40'ta 50 s, %60'ta 43 s, %80'de 32 s içinde 0,04 m'den küçük hatayla ve 9,3–9,5 m yükseklikte bırakma. %26 (uçuşta fren sırasında ölçülen en kötü değer) hâlâ yetmiyor: araç merkezleniyor ve 9,5 m'ye iniyor ama 3 s kilidi tamamlayamıyor. 17 m testinde JSONL'e yazılan geometri diagnostics ile gerçek süzme oranı ölçülmeli; %40'ın altındaysa geometri tarafı iyileştirilmeli.

Yerelde 288, Pi'de 246 test geçti. Yedek `runtime/before-center-tuning-20260911/`. Benzetim saha kabulü değildir; kamera kalibrasyonu hâlâ `yaklaşık/deneysel`.

## En güncel — 11 Eylül ikinci yükten sonra doğrudan LAND waypointi

Kullanıcı isteği: ikinci yük kabul edildikten sonra kalan tarama waypointlerine gidilmesin, doğrudan rotanın LAND waypointine uçulsun. Eski davranış bulunduğu yerde LAND idi. Yeni akış: GUIDED'deyken `mission_current` ile LAND sırası seçilir (`SELECT_LAND`), telemetride sıra doğrulanınca AUTO'ya devredilir (`HANDOFF_LAND`), AUTO doğru sırada başlayınca `LANDING` olur ve hız sahipliği bırakılır. Yanlış sıra, zaman aşımı veya pilot müdahalesi iptal üretir; rotaya dönülmez. MAVLink katmanında `mission_current` yalnız GUIDED'de ve yalnız `mission.land_seq` için uygulanır, bu sınır zaten mevcuttu.

İniş hâlâ görüntüye veya bitiş kapısına bağlı değil; yerde DISARM ile iki yük tamamlandıysa `DONE`. Onaylanmayan ikinci yük inişi tetiklemez. Testler yeni akışa göre güncellendi (`test_land_after_payloads.py` ve üç uçtan uca akış testi); yanlış waypoint ile AUTO başlarsa iptal edildiğini doğrulayan test eklendi. Yerelde 282, Pi'de 240 test geçti. Yedek `runtime/before-direct-land-20260911/`.

## En güncel — 11 Eylül ana görev yüksek irtifa düzenlemesi

Kullanıcı testleri 17 m'de, yarışmayı yüksekten (35 m'ye kadar) uçacağını bildirdi. Eski ana görev parametreleriyle 35 m'den bırakma imkânsızdı: 9 m bırakma yüksekliğine 0,15 m/s ile inmek en az 173 s sürerken merkezleme/alçalma sınırı 90 s idi, yani her deneme zaman aşımıyla iptal olurdu. `config/competition-base.json` içinde ana görev için `max_descent_mps` 0,15→1,0, `max_climb_mps` 0,30→1,0, `interaction_timeout_s` 90→150 yapıldı. Bırakma yüksekliği 9 m ve alt sınır 8,5 m korundu; isabet tasarımı değişmedi. 35 m'den alçalma yaklaşık 35 s sürer. Hızlı görev profili (`hizli-base.json`) bilinçli olarak değiştirilmedi.

Yeni testler: 17 m ve 35 m'den tam alçalma simülasyonu bırakmaya ulaşıyor ve eski değerlerle 35 m senaryosu başarısız oluyor; ana profiller için parametre koruma testi eklendi. Yerelde 280, Pi'de 238 test geçti. Yedek `runtime/before-high-altitude-20260911/`.

Yüksek irtifada açık riskler: 2 m hedef 35 m'den yaklaşık 54×54 piksel (fx≈948); bugünkü başarılı uçuşlarda hedef ≈200 piksel idi, bu boyutta YOLO/OpenCV başarımı denenmedi. Kamera kalibrasyonu hâlâ `yaklaşık/deneysel; saha kabulü yok`, dolayısıyla PnP doğruluğu yükseklikle birlikte bozulabilir. Mevcut rota 10 m; 35 m'lik yeni rota yüklenirse digest değişir ve profildeki `mission_fingerprint` yenilenmelidir. Ana uçuş öncesi `sortie_id` de yenilenmeli (mevcut kimlikte mavi kaydı var).

## En güncel — 11 Eylül ana görev incelemesi ve düzeltmeleri

Hızlı görev sahada tamamlandı: iki yük de gerçek servo komutuyla bırakıldı. Ardından ana (center) görev kodu, 11 Eylül başarısız ana uçuşunun kaydıyla (`artifacts/servo-bench-20260911/failed-flight-20260911.jsonl`, 851 kayıt) incelendi. Bulgular: mavi 42 tespitin 35'i kadraj taşması yüzünden eleniyordu; kırmızı 46 tespitin yalnız 12'sinde metrik geometri çözülüyordu; VERIFYING sırasında hız 0,20–0,23 m/s bandında eşiği aşıp tüm birikimi siliyordu. Bu üç etki birleşince 0,5 s kesintisiz kanıt hiç oluşmadı ve INTERCEPT/merkezleme hiç başlamadı.

Ana görev için uygulananlar: (1) kutu kırpma zaten her iki stratejide geçerli; (2) kenara değen renk bölgesi artık aday olmayı engellemiyor — metrik ölçümün kendi kenar payı `corner_screen`/`min_border_px` ile korunuyor, yani ölçüm kanıtı zayıflamadı; (3) frenleme (STOPPING) aşamasında kutu örtüşmesi koptuğunda, seçilen renkten tek aday varsa hedef yeniden yakalanıyor; (4) VERIFYING'de PnP çözülmeyen kare veya kısa hız sıçraması birikimi **silmiyor**, yalnız sayılmıyor — süreklilik `ContinuousHold`'un 0,25 s boşluk sınırıyla korunuyor. Hedefin kaybı, 0,8 m'yi aşan konum sıçraması ve sayılan her karenin duruş koşulu aynen duruyor; hızlı görevin sahada doğrulanmış davranışı değiştirilmedi.

Altı yeni test gerçek uçuş örüntülerini kullanıyor ve düzeltmeler geri alındığında başarısız oluyor. Yerelde 276, Pi'de 234 test geçti. Yedek `runtime/before-center-verify-20260911/`. Bu makinede ArduPilot SITL yok; doğrulama birim testi seviyesindedir, saha kabulü değildir.

Kullanıcı kararı: saha süresi nedeniyle `WPNAV_SPEED=1000` ana görevde de kalıyor; yazılımdaki 200 cm/s ana görev sınırı kaldırıldı, üst sınır iki görevde de 1000 cm/s (`link.py`). Bu hızda fren yaklaşık 3 s sürer ve hedef kadrajda kayar; risk kullanıcıya bildirildi. Ana uçuş öncesi açık madde: `config/ana-imx708.json` içindeki `sortie_id=20260911T071605Z-ana-imx708` için ledger'da mavi kaydı var, yeni kimlik gerekiyor. Kamera kalibrasyonu hâlâ `yaklaşık/deneysel; saha kabulü yok` (kalibrasyon lens pozisyonu 0,106, çalışma 0,0); merkezleme doğruluğu ölçülmüş değil. Salt okunur FC kontrolü: yerde, DISARM, LOITER; SERVO9 FUNCTION58 MIN1100 MAX1900, SERVO11 FUNCTION0 MIN800 MAX1900. Servo/ARM/mod komutu verilmedi.

## En güncel — 11 Eylül ikinci hızlı uçuş: kırmızı yük bırakıldı, mavi kaldı

Kutu kırpma düzeltmesi işe yaradı: mavi hedef 0,2 s içinde doğrulandı ve **kırmızı yük** AUX3/11 üzerinden bırakıldı (`kirmizi: ACK_ACCEPTED`, 67,5 s). Kayıt `artifacts/servo-bench-20260911/quick-flight-20260911-red-released.jsonl`, sortie `20260911T081342Z-hizli-imx708`.

Mavi yük bırakılamadı. 80,7 s'de kırmızı hedefe duruş istendi; 83,5–86,4 s arasında hedef kesintisiz YOLO+OpenCV doğrulamalı (fill 0,98–1,00) ve hız 0,04–0,27 m/s iken doğrulama zaman aşımına uğradı. Neden hedef kaybı değil, **kutu örtüşmesi zincirinin kopması**: fren sırasında kırmızı hedef 0,6 s içinde kadrajın altından üstüne kaydı (y 0,63→0,02), ardışık kareler arası IoU 0 oldu ve `quick_iou=0,25` eşiği tutmadı. `selected_box` eski konumda donunca duruştan sonraki sabit hedef bir daha eşleşmedi.

Düzeltme `controller.py`: hızlı görevde **yalnız STOPPING aşamasında** ve seçilen renkten tek aday varsa hedef yeniden yakalanır (`verify_hold` sıfırlanır). Duruştan sonra (VERIFYING) kural katı kalır; sıçrayan hedef hâlâ reddedilir. Yeni regresyon testi gerçek uçuş kutu dizisini kullanıyor ve düzeltme olmadan başarısız oluyor. Yerelde 271 test, Pi'de 229 test geçti. Yedek `runtime/before-reacquire-20260911/`.

Sonraki uçuş için: kırmızı yük fiziksel olarak yeniden takılmalı ve profile yeni `sortie_id` yazılmalı; ledger'da bu sortie için kırmızı kaydı var. Görev/kayıt kapalı; servo/ARM/mod komutu verilmedi.

## En güncel — 11 Eylül hızlı uçuş: kırmızı yük neden bırakılmadı

Uçuşta mavi yük kırmızı hedefe doğru şekilde bırakıldı (`mavi: ACK_ACCEPTED`, 64,5 s); kırmızı yük hiç komut almadı. Kayıt `artifacts/servo-bench-20260911/quick-flight-20260911-blue-released.jsonl` (Pi: `runtime/competition/quick-imx708/competition-40d6cabcc9a14a5eb354d87ae3bd23c9.jsonl`, sha256 `dc8682ea…7cb04`). Akış: 46,3 s mavi hedefte GUIDED duruş, 49,7 s VERIFYING, **52,7 s doğrulama başarısız/revoke**; 61,5 s kırmızı hedefte duruş, 64,5 s mavi yük; 76,0 s PILOT_CONTROL (LOITER) ile oturum kapandı, ikinci şans olmadı. Sorun servo/PWM değil: kırmızı yük komutu hiç üretilmedi.

Kök neden iki katı kadraj kuralı. Mavi hedefin YOLO kutusu üst kenarda `ymin ≈ -0,010` (yaklaşık 7 piksel taşma) geliyordu; `0 <= v <= 1` şartı 46 mavi tespitin 38'ini komple attı (kırmızıda yalnız 2). Kalan kareler de OpenCV tarafında `min_border_px=12` ile eleniyordu, çünkü renk bölgesi üst kenara değiyordu. Bu yüzden 0,1 s / 3 kare YOLO+OpenCV doğrulaması hiç oluşmadı.

Düzeltme: yeni `safak_gorev2/competition/bbox.py` içindeki `clamp_bbox` kutuyu [0,1] aralığına kırpar, alanının en az %60'ı kadraj içinde değilse reddeder; `vision.py` ve `runtime.py` bu kırpmayı kullanır. `ColorDetector.detect` artık `border_px` alır: hızlı görevde kenar payı uygulanmaz, ana görevde metrik ölçüm için `min_border_px` korunur. Eski uçuş kutuları yeni kodla yeniden geçirildiğinde mavi kabul 8/46 → 46/46, kırmızı 35/37 → 37/37. Yerelde 270 test geçti (5 atlandı), Pi'de 228 test geçti. Yedek `runtime/before-bbox-clamp-20260911/`. Görev/kayıt kapalı; servo/ARM/mod komutu verilmedi. Bu düzeltme yalnız kod/test doğrulamasıdır, yeni uçuşla saha kabulü yapılmadı.

## En güncel — 11 Eylül ilk ana uçuş teşhisi

Kullanıcı ana merkezleme uçuşunda aracın merkezlemediğini ve servoların dönmediğini bildirdi; uçuş ve kayıt süreçleri temiz kapatıldı. Uçuş JSONL'i `artifacts/servo-bench-20260911/failed-flight-20260911.jsonl`. Kamera/Hailo çalıştı, 91 örnekte AI tespiti vardı; rota/giriş kapısı ve AUTO/GUIDED geçişleri çalıştı. İki hedef için GUIDED duruş denendi fakat tespit anında yatay hız yaklaşık3–3,7m/s idi. Pixhawk salt okunur kontrolde `WPNAV_SPEED=1000cm/s` bulundu; önceki150cm/s ayarı korunmamış. Durma yaklaşık3s sürdü; mavi kadrajdan çıktı, kırmızı metrik geometri aralıklı kaldı.0,5s kesintisiz doğrulama oluşmadığından yazılım güvenli biçimde AUTO rotaya döndü; INTERCEPT/RELEASE_WAIT veya servo komutu hiç oluşmadı. Mission Planner'ın bağlı olmaması neden değil; Pi taze USB MAVLink aldı.

Kaydedici kamera hazır olmadan tek kimlik kontrolü yaptığı için `Kayıt gerçek kamera kimliği/backend ile eşleşmiyor veya kamera başlamadı` ile hemen çıktı; bu uçuşun ayrı video kaydı yok. Kaydedici artık kaynağı30s bekler. MAVLink preflight artık `WPNAV_SPEED` okur ve1–200cm/s dışında devralmayı reddeder. Center STOPPING metni düzeltildi, competition JSONL'e geometri diagnostics eklendi. Yerel ve Pi'de102 ilgili test geçti; düzeltmeler Pi'ye yüklendi. Görev/kayıt kapalı. FC `WPNAV_SPEED` henüz değiştirilmedi ve1000; yeniden uçuş öncesi kullanıcıyla150cm/s kararı uygulanmalı. Aynı sortie yük komutu üretmediği için payload ledger'da kayıt yok; fiziksel yükler hâlâ takılıysa aynı sortie kullanılabilir.

## En güncel — 11 Eylül ana merkezleme uçuş öncesi

Kullanıcı ana merkezlemeyi seçti. IMX708 fiziksel olarak CAM1'de; otomatik algılama sensör overlay'ini eklemediği için geçici `dtoverlay imx708` yoklamasında sensör kimliği `0x0301` ve 4608×2592 doğrulandı. `/boot/firmware/config.txt` içine kalıcı `dtoverlay=imx708` eklendi, reboot sonrası kamera görüldü. Gerçek ana profil kamera/Hailo/OpenCV testi 20 saniyede 1015 kare, 50,37 FPS, stale0, hata0; entegre observe yaklaşık49,9 FPS. Görüntü merkezi açık, iniş takımları iki kenarda. Kanıt `artifacts/servo-bench-20260911/preflight-imx708-camera.jpg`; Pi sonucu `runtime/preflight-20260911-imx708-camera.json`.

Ana profil Pixhawk bağlantısı doğrulanmış `...CubeOrange...-if00` by-id yoluna sabitlendi. Entegre observe: DISARM/STABILIZE/yerde, rota digest `54b32d9b...747fe` dünkü rota ile eş, GPS14/HDOP0,83, EKF831, 16,293V/%99, firmware4.6.3, pipeline/link/preflight hata yok. RC telemetrisi sağlıksız/UNKNOWN; kumanda-alıcı açılıp AUTO slotu canlı doğrulanmadan uçuş yok. Servo salt okunur tekrar kontrolde mavi9 FUNCTION58 MIN1100/MAX1900, kırmızı11 FUNCTION0 MIN800/MAX1900 ve araç yerde/DISARM; servo komutu gönderilmedi.

Profilde `sortie_id=null`; iki yük yeniden fiziksel takıldıktan sonra yeni tek kullanımlık kimlik yazılmalı. İki yük sonrası bulunduğu yerde LAND için `Options.missing`, `mission.direct_land_corridor_checked=true` saha onayını artık zorunlu tutar; mevcut değer null. 85 ilgili yerel test geçti; bu son güvenlik kapısı Pi'ye dağıtılacak. IMX708 sonsuz odak matrisi hâlâ yaklaşık/saha metrik kabulü yok. Uçuş/görev/kayıt süreci kapalı; ARM/mod/servo komutu verilmedi.

## Son durum — 11 Eylül servo entegrasyonu Pi'de, kamera bekleniyor

Servo kodu/profilleri Pi'ye yüklendi; 13dosya hash doğrulandı, **100 ilgili Pi testi geçti**. Önceki yerel247+9test ve gerçek MAVLink servo komutlu hex SITL geçti: `artifacts/competition-sitl/20260911T093947-quick-complete/result.json`; iki ACK_ACCEPTED ve LAND/DONE. Yedek `runtime/before-servo-integration-20260911/`.

Kullanıcı rota dünküyle aynı dedi; canlıFC DISARM iken geri okundu ve digest54b32d9b...747fe birebir eşleşti. TAKEOFF10m, tarama2–8 hepsi10m, LAND9. Ana/ana-imx708/hızlı genel profillerine doğrulanmış rota/kapı/poligon alanları işlendi; sortie_id henüznull, yeni yükleme/oturum seçilmedi. Yeni kamera montajı varsayılmadı. Uçuş uygulaması açılmadı; servo/ARM/mod/rota komutu bu tur yok.

Pi kamera 'No cameras available'. /boot/firmware/config.txt içinde aktif dtoverlay=imx219 bulundu; imx219 chip-id -121 hatası vardı. Eski satır yedeklenip yorumlandı, camera_auto_detect=1 korundu, yerde/DISARM ile Pi reboot edildi. Son envanter yine hiçkamera yok; bootta hiçbir imx sensörü algılanmıyor. Başka overlay zorlanmadı; kullanıcıdan güç kapalıyken IMX708 kablo/mandal kontrolü istendi. boot yedeği runtime/before-servo-integration-20260911/boot-config-before-imx708.txt. IP172.20.10.6 aynı. Ana/hızlı seçimi soruldu, yanıt bekleniyor. Önceki kamera görülmüyor/dağıtım bekliyor notlarında dağıtım artık tamamlandı, kamera sorunu sürüyor.

## 11 Eylül — tezgâhta iki yük bırakma doğrulandı, süreli servo entegrasyonu

Kullanıcı mavi AUX1/9=1800us ve kırmızı AUX3/11=yaklaşık0,3s800us→1500us ile iki yükün düştüğünü, ayrıca kırmızının1500us ile durduğunu doğruladı. IMX708 uçuş testi için koda eklenmesini istedi. Beş görev profilinde bu eşleme kaydedildi; IMX708 profilleri actuator=servo, Arducam simulated olarak kaldı. Mavi beklenen FUNCTION58 (tezgâhta okunan RCIN8), kırmızı FUNCTION0; işlev kontrolü bu kesin değerlerle yapılır. Kırmızı MIN800 daha önce FC'ye yazıldı; yeni entegrasyon FC parametresi yazmaz. Her iki servo bench_verified=true; fiziksel uçuş/isabet doğrulaması değildir.

Servo tanımına pulse_s/neutral_pwm/function eklendi. Kırmızı800 ACK+çıkış kanıtı alınsa bile durum SENT kalır; bağlantı döngüsündeki0,3s sonlandırma1500 gönderir, yalnız1500 ACK+çıkış da doğrulanınca ACK_ACCEPTED olur. Eksik ilk kanıt, zaman aşımı/ret UNCERTAIN veya REJECTED üretir; otomatik tekrar yok. Pilot devri veya kontrol döngüsü durması nötr komutunu engellemez; temiz kapanışta etkin darbe nötrlenir. Süreç SIGKILL/güç/USB kaybında yazılım fiziksel duruş garantisi veremez. İki yük sonrası LAND korunur.

Ortak MavlinkLink'e boş tick/shutdown kancaları eklendi; eski Controller/geometri değişmedi. Mavlink özgün kaynağı `archive/legacy-options/mavlink_io-before-servo-pulse.py.txt` altında hash eşlemesine alındı. Yeni9servo testi geçti; önceki tüm247test/5atlama da geçti.

Son Pi kamera envanteri **No cameras available**: IMX708 görülmüyor. Mevcut ana profillerde sortie/rota/kapılar boş; 10Eylül hızlı saha rotası tarihli aday, yeni uçuşa otomatik onaylanmadı. Uçuş uygulaması başlatılmadı. Kamera takılması, ana/hızlı seçimi ve güncel rota doğrulaması bekliyor.

Kullanıcı yükleri sıfırladığını söyleyip ikisini bırakmamızı istedi. Yeni açılışta yerde/DISARM doğrulandı; sırasıyla mavi AUX1/9'a1800us, kırmızı AUX3/11'e yaklaşık0,3s800us sonra1500us gönderildi. Üç komut ACK kabul; son çıkışlar9=1800,10=0,11=1500. Bu adımda FC parametresi yazılmadı, MIN11=800 okundu. İki yükün fiziksel düşüşü ve kırmızının1500'de durması henüz bilinmiyor; kullanıcı sonucu bekleniyor. Kanıt `artifacts/servo-bench-20260911/both-reloaded-1800-800.txt`; tekrar darbe betiği `red-aux3-800-repeat.py`. Süreçler kapandı. Görev profilleri hâlâsimulated/kırmızı10/null/false; test sonucu otomatik uçuş kabulü değildir.

Kullanıcı900us ile yükün uçta kaldığını söyleyip800 istedi ve kırmızı servonun sonsuz döndüğünü bildirdi. Model henüz bilinmiyor; sürekli dönüş tipi kullanıcı beyanı. Bu nedenle uzun süre800 tutmak yerine kısa darbe uygulandı: yerde/DISARM/FUNCTION0/MIN900/çıkış900 teyidiyle SERVO11_MIN900→800 kalıcı yazıldı/geri okundu; AUX3/11'e800us, yaklaşık0,3s sonra finally bloğunda1500us gönderildi. İki ACK kabul; son servo11_raw=1500. 1500 fiziksel duruşu veya yük düşüşü henüz doğrulanmadı. Kullanıcıya yükün düşüp düşmediği ve servonun durup durmadığı sorulmalı. Maviye komut yok. Kanıt `artifacts/servo-bench-20260911/red-aux3-800-pulse.txt`, betik aynı dizinde. Sürekli dönüş modeli doğrulanırsa görev bırakma kodu süreli sürüş/neutral gerektirir; mevcut tek PWM/ACK mekanizması otomatik kabul edilmemeli. Profiller hâlâ simulated/kırmızı10/null/false.

Kullanıcı1000us ile yükün hâlâ düşmediğini bildirip açıkça900us denemesini istedi. Tek seferlik betik taze yerde/DISARM, FUNCTION0, MIN1000 ve çıkış1000 teyidiyle yalnız SERVO11_MIN1000→900 kalıcı yazdı/geri okudu; AUX3/11'e900us tek komut gönderildi. Fiziksel sonuç bekleniyor. Maviye komut yok. Kanıt `artifacts/servo-bench-20260911/red-aux3-900.txt`, betik aynı klasörde; Pi runtime/before-land-servo-20260911. Bu açık deneme servo modelinin900us uygunluğunun teknik kanıtı değildir. Görev profilleri hâlâ simulated/kırmızı10/null/false; kalıcı AUX3 bırakma eşlemesi henüz yapılmadı.

Kullanıcı1050us adımını çok az buldu. Taze yerde/DISARM, FUNCTION0, MIN1050 ve çıkış1050 teyidiyle yalnız SERVO11_MIN1050→1000 kalıcı yazıldı/geri okundu; AUX3/11'e1000us tek komut ACK kabul ve çıkış1000 doğrulandı. Maviye komut yok. Fiziksel1000 sonucu bekleniyor. Daha düşük PWM öncesi servo model/izinli darbe aralığı ve mekanik kurulum bilinmeli; otomatik sınır genişletme yapma. Kanıt `artifacts/servo-bench-20260911/red-aux3-1000.txt`, tek seferlik betik aynı klasörde. İlk MIN1100, ara1050 ve son1000 kayıtlı. Görev profilleri hâlâ simulated/kırmızı10/null/false; bu fiziksel kabul sonrası düzenlenecek.

Kullanıcı kırmızı AUX3/1100us ile döndüğünü ama az olduğunu, sıfırlamadığını ve biraz daha hareket istediğini bildirdi. Yerde/DISARM ve servo11_raw=1100 doğrulanarak **kalıcı SERVO11_MIN1100→1050** yazıldı ve geri okundu; yalnız AUX3/11'e1050us bir defa gönderildi. ACK kabul ve servo11_raw=1050 doğrulandı; mavi9'a komut yok. Eski MIN1100 kanıtta kayıtlı, kendiliğinden geri değiştirme. Fiziksel1050 sonucu bekleniyor; görev profilleri hâlâ simulated, kırmızı10/null/false, AUX3 kalıcı eşlemesi henüz yapılmadı. Tek seferlik betik ve kanıt `artifacts/servo-bench-20260911/red-aux3-1050-once.py`, `red-aux3-1050.txt`; Pi betiği `runtime/before-land-servo-20260911/` içinde.

Kullanıcı kırmızının AUX3 olduğunu ve maviyle ters yöne hareket istediğini tekrar belirtti. Taze yerde/DISARM denetiminden sonra yalnız AUX3/11'e1100us gönderildi; ACK kabul, servo11_raw=1100 doğrulandı. Mavi9'a komut verilmedi (çıktısı1800). Fiziksel yön/yük sonucu bekleniyor; kanıt `artifacts/servo-bench-20260911/red-aux3-1100.txt`. Kalıcı görev profilleri henüz kırmızı10/simulated/null/false; AUX3 fiziksel kabul sonrası güncelleme gerekli.

Kullanıcı kırmızı AUX2'de hâlâ hareket olmadığını bildirip servoyu AUX3'e taşıdı ve deneme istedi. Bench betiğine kanal11 eklendi/Pi'ye aktarıldı. Taze yerde/DISARM, SERVO11_FUNCTION=0, MIN1100/MAX1900 okundu; yalnız AUX3/11'e1800us gönderildi. ACK kabul ve servo11_raw=1800 doğrulandı. Fiziksel sonuç bekleniyor. Kanıt `artifacts/servo-bench-20260911/red-aux3-1800.txt`. Görev profilleri henüz kırmızı10 olarak kalıyor; AUX3 fiziksel kabul sonrası kalıcı eşleme güncellenmeli.

Kullanıcı son iki kanal denemesinde mavinin düştüğünü doğruladı; kırmızı servonun takılı olmadığını fark edip tekrar deneme istedi. Önceki kırmızı hareketsizliği PWM/yön başarısızlığı olarak yorumlanmamalı. Taze DISARM/ON_GROUND ile yalnız AUX2/10'a tekrar1800us gönderildi; ACK kabul ve servo10_raw=1800. Fiziksel kırmızı sonucu bekleniyor. Kanıt `artifacts/servo-bench-20260911/red-1800-connected.txt`; maviye bu adımda komut yok.

Son kullanıcı iki servonun da sabit olduğunu bildirip ikisine de komut istedi. Taze DISARM/ON_GROUND ile sırayla AUX1/9 ve AUX2/10'a 1800us birer kez gönderildi. Her iki ACK kabul; son servo9_raw=1800, servo10_raw=1800. Fiziksel hareket/yük sonucu henüz bilinmiyor. Kanıt `artifacts/servo-bench-20260911/both-1800.txt`. Önceki kırmızı1800 için kullanıcı hareket yok dedi.

**Son fiziksel geri bildirim:** Kullanıcı mavi1800us ile yükün düştüğünü, kırmızı1100us ile hiç hareket olmadığını doğruladı. İki servoyu sıfırlayıp güç verdiğini bildirdi. Sonraki taze hex/DISARM/STABILIZE/ON_GROUND kontrolünde servo9/10 çıktıları0/0 idi; yalnız kırmızı AUX2/10'a1800us gönderildi, ACK kabul ve servo10_raw=1800 doğrulandı; servo9_raw=0 kaldı. Kırmızı1800 yön/açı/yük sonucu bekleniyor. Betik kapandı. Kanıt `red-1800.txt`, kullanıcı sonuçları `user-feedback.json`; mavi1800 bırakma adayı fiziksel olumlu, profiller henüz simulated/null/false.

### Servo denemesi devamı — mavi1800 / kırmızı1100

Kullanıcı: mavi AUX1 ilk1500us denemesinde doğru yönde yaklaşık30–45° döndü, yeterli değil. Sonraki mavi1800us komutu kesilen tur sırasında **gerçekten gönderildi**, ACK kabul ve servo9_raw=1800 doğrulandı; fiziksel açı/yük sonucu henüz yok. Kullanıcı güç varken başlangıca elle getiremediğini söyleyip kırmızı denemesini istedi. Yeni yerde/DISARM kontrolüyle yalnız AUX2/10'a1100us gönderildi; ACK kabul ve servo10_raw=1100 doğrulandı. Son çıkışlar mavi1800/kırmızı1100us. İki betik de bitti/seri bağlantıyı kapattı. Sıfırlama, ARM/mod/FC parametre yazımı yapılmadı. Kırmızının yön/açı/yük düşüşü bekleniyor; profillerde bench_verified=false/release_pwm=null kalır. Kanıtlar `artifacts/servo-bench-20260911/blue-1800.txt`, `red-1100.txt`.

## 11 Eylül — LAND Pi’ye yüklendi; servo eşlemesi değişti, ilk mavi deneme

Kullanıcı servo testini şimdi açıkça istedi ve eşlemeyi değiştirdi: **mavi yük AUX1/9, kırmızı yük AUX2/10**. Başlangıçları fiziksel 0°, istenen hareket yaklaşık 90°; AUX1 sağa, AUX2 sola kullanıcı beyanı. Eski kırmızı9/mavi10 notları artık tarihli geçmiş. Mavi hedefe kırmızı, kırmızı hedefe mavi yük kuralı değişmedi. Beş görev profilinin yalnız kanal eşlemesi Pi/Mac üzerinde güncellendi; `actuator=simulated`, `release_pwm=null`, `bench_verified=false` korunur.

Pi `furkan@172.20.10.6`, repo `/home/furkan/Desktop/safak-gorev2-quad`. LAND controller/panel ve test dosyaları yedek alınıp hash doğrulanarak yüklendi. Pi’de 69 ilgili test geçti. Eski Pi arşiv eşlemesi önceki kamera revizyonunun 3 kaynak kopyasını göstermiyordu; özgün hash eşleşen arşiv kopyaları/eşleme de aktarıldı. Yedek `runtime/before-land-servo-20260911/`, kanıt `artifacts/servo-bench-20260911/`. Kamera/görev/uçuş başlatılmadı; gerçek ARM/mod/rota/FC parametresi yazılmadı.

Cube if00/ttyACM0 tek okuyucuyla hex/DISARM/LOITER/ON_GROUND doğrulandı. SERVO9_FUNCTION=58, SERVO10_FUNCTION=60 (RC giriş geçişleri), MIN/MAX=1100/1900, TRIM=1500, REVERSED=0; başlangıç çıkışları 982/1495 us. Parametreler değiştirilmedi. Manuel deneme betiği `scripts/servo_bench.py` her komut öncesi taze yerde/DISARM ve kanal işlev/sınır kontrolü yapar; yalnız açık channel+pwm ile bir kez DO_SET_SERVO yollar. ArduPilot’un kabul ettiği Disabled/RC geçiş işlevlerine izin verir; görev yazılımının servo için FUNCTION=0 şartı gevşetilmedi.

**İlk deneme: AUX1/9 mavi → 1500 us tek komut, ACK kabul ve servo9_raw=1500 doğrulandı. AUX2’ye komut yok.** Fiziksel sağ/sol, açı ve yük düşüşü kullanıcının yanıtını bekliyor; bench kabulü yapılmadı. Sıradaki adım bu geri bildirime göre devam; yeniden komut göndermeden taze durum oku. `blue-1500.txt` kanıtı. Betik bağlantıyı kapattı; otomatik tekrarlama/geri döndürme yok.

## 11 Eylül — iki yük sonrası doğrudan LAND

Son kullanıcı isteği: mavi ve kırmızı yük komutları da onaylandıktan sonra ana ve hızlı görev doğrudan **bulunduğu yerde LAND** ister. İlk yükte eski tarama irtifası/aynı waypoint dönüşü korunur. İkinci yükte yükselme, AUTO dönüşü, kalan rota veya bitiş kapısı yoktur. `REQUEST_LAND` taze LAND telemetrisini bekler, `LANDING` hız sahipliğini bırakır; yerde DISARM ile `DONE`. Onaylanmayan yük erken inişi tetiklemez. Pilot devri kilidi ve LAND geçişi zaman aşımı korunur. Eksik yükle tarama biterse eski AUTO/LAND rotası devam eder.

Bu değişiklik yereldedir; Pi'nin son IP'si 172.20.10.6 ve görünen .3 SSH zaman aşımı, .2 bağlantı reddi verdi; bu tur dağıtım yapılmadı. Kamera ayarı/servo/gerçek MAVLink açılmadı. Servo hâlâ simulated/PWM null; ACK/PWM fiziksel ayrılma kanıtı değildir. **247 yerel test geçti/5 atlandı; ana+hızlı 2 hex SITL geçti.** Güncel test kanıtı `artifacts/land-after-payloads-20260911/` içinde; önceki test raporları eski rota bitiş davranışını doğrular.

## 11 Eylül — ana görev için iki kamera

233 yerel test geçti/5 atlandı (4 Torch, 1 ayrı MOSSE); 7 yeni hex SITL senaryosu geçti. Ana ve hızlı tam görevler simulated yüklerle LAND tamamladı. Kesin kanıt `artifacts/dual-camera-20260911/REPORT.md`.

Ana IMX708 ve Arducam profilleri ayrıldı; ana center/PnP/alçalma ve hızlı merkezlemesiz akış korunur. Yeni profiller simulated, PWM null. Arducam kimliği/kalibrasyonu/montajı bilinmiyor; `v4l2-observe` yalnız gözlem, uçuş ve bırakma kapalı. IMX708 0 odakta yaklaşık matris kullanır; focus_transfer_verified ve physical_distance_verified false. Kamera kimliği/backend ve kayıt profili eşleşmesi denetlenir; rota ve resume yalnız mission_digest() kullanır.

Yeni yerel kaynaklar Pi'ye dağıtılmadı. Son bilinen IP SSH bağlantısını reddetti; canlı kamera kabulü yok. Servo ertelendi. Ayrıntılı profiller, kayıt komutu, değişen dosyalar ve fiziksel kabul ölçütleri: [İki kamera kabulü](competition/IKI_KAMERA_KABUL.md). Testler [TESTLER](competition/TESTLER.md) içinde.


## Önce bu özeti oku — son geçerli durum

**En son — kamera sabitlendi:** Kullanıcı kamerayı takıp sabitlediğini bildirdi. Aynı Pi 172.20.10.2 üzerinde önce süreçlerin kapalı olduğu okundu; ana profille 20 saniyelik `connect=False` kamera/Hailo/OpenCV/JPEG testi yapılıp kapatıldı. 959 işlenmiş kare, 50,0296 FPS, hata yok; gerçek IMX708 tam crop/2304×1296 sensör, manuel LensPosition=0 doğrulandı. MAVLink/servo/uçuş açılmadı. Görüntünün orta alanında zemin açık, yanlarda iniş takımı ve alt kenarda beyaz kablo görünüyor. Önceki görüşü büyük ölçüde kapatan yakın yüzey notu artık geçmiş; uzak netlik, gerçek branda, montaj yönü/metrik ofset kabulü hâlâ yapılmadı. Kullanıcıdan yeni ofset ölçüsü gelmedi; kayıtlı 180°/[0.11,0,0.05] korundu. Kanıt `artifacts/camera-mounted-20260908/` (rapor, son görüntü, kare kaydı; üç dosya Pi/Mac hash eşleşti). Servo işi ertelenmiş durumda.

### Sonraki güncelleme — teknik kontrol, sonsuz odak ve klasör düzeni

Son kullanıcı durumu: **kamerayı yapıştırıp sabitliyorlar**. Süreli kamera testleri kapandı; sabitleme sırasında tekrar kamera açma. Son dosya kontrollerinde 98 yerel + **98 Pi testi geçti**. İlk Pi test denemesinde dağıtılmamış iki test dosyası eksikti; eksikler aktarılıp tekrar geçti, ilk log korundu. Son okuma: kamera/Python görev süreci yok, 8080/8081 kapalı, 58,7°C / throttled 0x0. Teknik rehber/devir dâhil 15 belge ve kanıt dosyası da Pi'ye hash doğrulanarak kopyalandı (`docs-deployment.json`; bu nottan önceki dağıtım). Son belge eşlemesi `final-docs-deployment.json` içinde. Kamera/servo testi sonraki kullanıcı isteğini bekliyor.

Kullanıcı eski IMX708 dama fotoğraflarının kullanılmasını ve **iki görevde de sonsuz odak** istedi; ayrıca teknik kontrol için klasörü düzenlemeyi istedi. Servo çalışmasını açıkça sonraya bıraktı. **Bu bölüm aşağıdaki sabah özetini günceller:** ana artık IMX219 matrisine bağlı değil; iki görevde `lens_position=0.0`, manuel odak, 2304×1296 sensör modu ve 50 FPS var. Yeni ayarlar Pi'ye aktarıldı.

- 40 özgün dama karesinin SHA256 ve çekim ayarları doğrulandı; 8 poz yeniden çözüldü. Yeni RMS 0,1338 px; özgün aday 0,1388 px. Matris birebir tekrarlanmadı (fx/fy farkı yaklaşık %0,04/%0,06), farkın nedeni kesinleştirilmedi. Ayrı 5 yakın referansta özgün aday yaklaşık 79,92 cm, kullanıcı ölçüsü 80,8 cm; ölçüm belirsizliği bilinmiyor. Rapor/yeniden çözüm betiği `artifacts/camera-review-20260908/` içinde.
- **Sonsuz odakta kalibrasyon yaklaşık:** özgün `config/camera.imx708-candidate.json` değiştirilmedi. Ana `config/camera.imx708-infinity-approx.json` kullanır; sayısal K/distorsiyon aynı, `calibration_capture_lens_position=0.10627710819244385` çekim odağını, `lens_position=0` çalışma odağını belirtir. `focus_transfer_verified=false`, `physical_distance_verified=false`. Sonsuz odakta yeniden kalibrasyon yapılmış gibi anlatma; yakın dama verisi uzak mesafe/netlik kanıtı değildir. Önce ana için çekim odağı önerilmişti; kullanıcı açıkça sonsuz istediğinde iki profil de 0 yapıldı.
- Güncel ayarlarla **98 ilgili yerel test geçti**. Pi iki ayrı 20 saniyelik kamera/Hailo/OpenCV/JPEG testinde ana 899 çıkarım/895 işlenmiş kare, **49,86 FPS**; hızlı 968/968, **50,03 FPS**. İkisi hata yok, gerçek stream manuel lens 0 ve tam crop ile eşleşti. Görüşün çoğunu yakın parçalar kaplıyor; uzak netlik ve gerçek branda/PnP yükü doğrulanmadı. `ana/report.json`, `hizli/report.json`, son görüntüler ve loglar aynı kanıt dizininde.
- Pi yeniden açılmıştı; ilk SSH zaman aşımından sonra aynı **172.20.10.2** ve doğrulanmış SSH kimliğiyle bağlanıldı. Dağıtımın 5 dosyası hash eşleşti; yedek `runtime/before-camera-infinity-20260908T142105/`; `deployment.json`. Son 20 saniyelik testler kapandı. **MAVLink/servo/ARM/mod/rota açılmadı veya gönderilmedi.** Sonraki işlemde canlı durum tekrar okunmalı.
- Kök `TEKNIK_KONTROL.md`: hakem için kaynak okuma sırası, görev akışı, kamera/kalibrasyon sınırları ve test bağlantıları. `config/README.md`, `archive/README.md` eklendi. `anlık test/` → `archive/field-videos-20260907/`; kök eğitim ZIP'i → `finetune_dataset/safak_finetune_dataset.zip`; gevşek `:memory:.ses` → `archive/local-cleanup-20260908/memory.ses`. Taşınan içerikler hash ile doğrulandı; manifest `archive/local-cleanup-20260908/moves.json`. Kod/model/kalibrasyon kanıt yolları korundu. Bu klasör taşımaları yerel Mac içindir; Pi'nin kişisel kayıtları taşınmadı.
- Kullanıcının mekanizma fotoğraflarında iki kolun **birbirinden dışa açılması** isteniyor; ikinci fotoğrafın oku burun yönünü gösteriyor. Fotoğraf üzerinden PWM artış yönü/kanal kesinleştirilmedi. Görseller `artifacts/mechanism-20260908/` içine korundu. **Servo testi şu anda istenmiyor; kullanıcı dönünce devam et.** Yeni odağın saha kabulü, doğru Pixhawk portu/telemetri, gerçek branda, servo ve yarışma rotası açık kalıyor. Kullanıcı teknik kontrole gidiyor; gereksiz yeni bilgi/kalibrasyon çekimi isteme.

### Sabah özeti — yukarıdaki değişiklikler önceliklidir

Kullanıcı kısa Türkçe yanıt istiyor; projeyi baştan anlattırma. Bu bölüm aşağıdaki tarihçeden önceliklidir. Son istek, yapılan değişiklikleri yeni sohbetin hatırlaması için bu dosyada toplamaktı. Bu son düzenleme yalnız yerel devir belgesidir; yeni donanım işlemi yapılmadı.

### Kullanıcının kararları ve uygulanan kod

- Yalnız iki görev var: `python -m safak_gorev2.competition.main --task ana|hizli`. Profiller `config/ana-gorev.json` ve `config/hizli-gorev.json`; temel ayarlar `config/competition-base.json` ve `config/hizli-base.json`. Eski girişleri/profilleri yeniden etkinleştirme. MOSSE yok. Korunan ortak `safak_gorev2/controller.py` ve `geometry.py` değiştirilmedi.
- **İki temel profilde kamera 50 FPS.** Hızlı görevde IMX708 1280×720, sensör 2304×1296, tam crop `[0,0,4608,2592]`, sabit lens 0,1 korunuyor. 120 FPS için kırpılmış moda geçilmedi. Panel JPEG 8 FPS, tarayıcı yaklaşık 4 Hz, ayrı panel kaydedicisi 8 FPS; bunlar çıkarım hızından ayrıdır. Kullanıcının havada videoda 16 FPS görmesi, çıkarımın 16 FPS olduğunu kanıtlamaz. Panel/API artık istenen kamera FPS'sini ve ölçülen işleme FPS'sini ayrı gösterir.
- **Aramada YOLO VEYA kararlı OpenCV adayı → duruş → aynı hedefte YOLO VE OpenCV doğrulaması.** İkisi görüntü akışı boyunca birlikte çalışır. Arama en az 3 bağımsız kare/0,10 saniye; GUIDED isteğinden sonra telemetride yatay hız ≤0,20 m/s ve en az 0,30 saniye kararlılık beklenir. 0,10 saniye fiziksel frenleme süresi değildir.
- Duruş sonrası hızlı görev en az 3 taze kare/0,10 saniye ortak kanıtla, mevcut bırakma koşulları da sağlanırsa aynı irtifada bırakır; PnP, merkezleme veya alçalma yapmaz. Ana görev ayrıca PnP/metrik doğrulama (profilde en az 6 kare/0,50 saniye), merkezleme ve alçalma ister; merkezleme boyunca ortak kanıt sürmelidir. 3 saniyede doğrulanmayan adayda yük bırakılmaz, aynı AUTO waypoint'e dönülür; tekrar deneme gecikmesi 5 saniye. Pilot devri, bayat kamera/telemetri ve duramama korumaları korunur.
- `safak_gorev2/competition/color_search.py` bütün görüntüyü en çok 640 piksel genişlikte HSV + dörtgenle tarar; renk başına en çok 6 bölgeyi tam çözünürlükte inceler. Başlangıç eşikleri: mavi H 90–135, kırmızı H 0–12/168–179, S≥70, V≥35, doluluk≥0,75, en-boy oranı≤2,5; alan/kadraj korumaları da sürer. Bunlar **sahada gerçek brandayla doğrulanmamış mühendislik değerleridir**.
- `competition/vision.py` aynı kare, aynı renk ve IoU≥0,5 ile bire bir eşleştirir. OpenCV tek başına aday üretebilir; AI güven skoru `null`, doluluk ayrı kaydedilir. Yalnız renk ya da yalnız YOLO ile bırakılmaz. Eski kare veya başka nesnedeki kanıt birleştirilmez. OpenCV, YOLO tespitine bağımlı değildir; ancak mevcut mimaride Hailo sonrası kareyi kullandığından **Hailo akışı tamamen bozulursa bağımsız yedek kamera hattı olarak çalışmaz**.
- `competition/config.py`, `controller.py`, `runtime.py` ve panel akışı bu füzyona uyarlandı; kaynak/doğrulama/işleme süresi kaydediliyor. Panel kutuları işlenmiş ilgili kareyle birlikte gösteriliyor. `tests/test_color_fusion.py` 33 test içeriyor.

### Kamera montajı — kullanıcı doğruladı, tekrar sorma

Lens yere bakıyor; görüntünün üstü drone'un arkasına gelecek şekilde **180° ters**. Lens merkezi Pixhawk merkezinden **11 cm ileri, 5 cm aşağı, sağ/sol sıfır**. İki temel profilde `camera.offset_body_m=[0.11,0.0,0.05]`, iki görev profilinde `camera_mount_yaw_deg=180` var. **Bu değişiklikler Pi'ye de aktarıldı.**

`competition/geometry.py` içindeki `MountedTargetGeometry`, korunan eski geometrinin üzerine montaj dönüşümünü uygular: 180° için sanal ofset `(-ileri,-sağ,aşağı)` ve poz `(-roll,-pitch,yaw+pi)`. Böylece eğim ve ofset birlikte ele alınır; ham görüntü/kalibrasyon matrisi döndürülmez. Hızlı görev metrik geometri kullanmaz. Ölçüler kullanıcı beyanıdır; gerçek yön/mesafe kabulü henüz yapılmadı. Montaj test dosyasında 19 test var.

### Tamamlanan doğrulama ve dağıtım

Son kesin kayıt: `artifacts/fusion-20260908/summary.json` ve `fusion-verification-20260908.json`.

- **209 yerel test geçti, 5 atlandı** (4 Torch ortamı, 1 ayrı MOSSE ortamı); **125 Pi testi geçti**. İlk 124 sayısı ara sonuçtur. Python/JS sözdizimi ve korunan kaynak hash kontrolleri geçti.
- **3 ArduCopter 4.6.3 hex SITL senaryosu geçti:** `20260908T072604-quick-complete`, `20260908T072851-center-complete`, `20260908T073247-quick-false-target`; kanıtlar `artifacts/competition-sitl/` altında. Tam görevlerde iki bırakma ACK/PWM, rotaya dönüş ve iniş; yanlış hedefte OpenCV sürerken YOLO kaldırıldı, sıfır bırakma ve aynı waypoint/AUTO dönüşü doğrulandı. Görüntü, YOLO ve servo etkileri simüledir; gerçek saha kabulü değildir.
- Pi dağıtımı sonunda **22 dosyanın ve 4 kanıt dosyasının SHA256 eşleşmesi** doğrulandı. İlk 16 dosya sayısı ara dağıtımdır. Manifest `artifacts/fusion-20260908/manifest.json`; Pi yedeği `runtime/before-fusion-20260908T072743/`. Bu sayılar dağıtım anına aittir; bu son yerel HANDOFF düzenlemesi dağıtımdan sonradır.
- **Gerçek Pi testi: 45,42 saniyede 2152 çıkarım / 2151 işlenmiş kare, 50,03 FPS.** Hızlı runtime gözlemde `start(connect=False)` ile gerçek IMX708 + Hailo + OpenCV + JPEG kodlama çalıştı. İşleme ortancası 3,67 ms, p95 6,78 ms; yakalama→sonuç ortancası 42,57 ms, p95 49,39 ms. CPU yaklaşık 1,27 çekirdek eşdeğeri. Uygulama hatası ve yeni çekirdek uyarısı sıfır. Son kare kapanışta tüketilmediği için sayaç farkı 1.
- Canlı testte MAVLink, HTTP istemcisi, ayrı video kaydedicisi ve ana görevin PnP yükü yoktu. Görüntü yakın açık yüzey/araç parçalarıydı; gerçek brandada doğruluk veya uçuşta sürekli 50 FPS garantisi yok. Rapor: `artifacts/fusion-20260908/fusion-probe-20260908T072828/report.json`; aynı dizinde kare kayıtları ve son görüntü var. Test logları: `local-tests.log`, `fusion-pi-tests-final-20260908.log`.

### Hailo onarımı ve son bağlantı bilgisi

Pi son doğrulanan adresi `furkan@172.20.10.2`; proje `/home/furkan/Desktop/safak-gorev2-quad`. SSH örneği: `ssh -o BatchMode=yes -o ConnectTimeout=6 -o StrictHostKeyChecking=yes -o HostKeyAlias=192.168.197.121 furkan@172.20.10.2`. IP ve canlı süreçler sonraki işlemde yeniden kontrol edilmeli.

HAILO8L/HailoRT/driver 4.20.0; kernel `6.12.75+rpt-rpi-2712`. `find_vma` uyarısına resmî upstream'deki `mmap_read_lock/unlock` iki satırlık düzeltmesi `/usr/src/hailo_pci-4.20.0/linux/vdma/memory.c` içine uygulandı. Yalnız çalışan kernel için DKMS yeniden kuruldu, yalnız Hailo modülü yeniden yüklendi; reboot yok. Son srcversion `DDE5580B51751E55E460F6D`. İlk testteki 42 uyarı sonraki testlerde tekrarlanmadı. **Eski PCIe kopmasının nedeni veya uzun süreli kesin çözümü kanıtlanmadı.** Paket güncellemesi yamayı ezebilir. Pi yedeği `runtime/hailo-driver-fix-20260908/`, yerel rapor `artifacts/pi/hailo-driver-fix-20260908/REPORT.md`.

Pi HEF yolu `best_hailo_model/safakyepyeni.hef`, SHA256 `8433d13ecee9d05852178a0f38c057217d5a7f2db4436036b2a978e877c192e2`; modeli değiştirme/eski adı Pi'ye geri yazma. Rastgele veriyle ayrı model testi 104,02 FPS verdi; kamera FPS'si değildir. Mevcut Hailo ortamı `/home/furkan/Documents/proje/hailo-rpi5-examples/setup_env.sh`; Pi testleri buradaki mevcut venv ile çalıştı, sistem Python'unda pytest yok. Başlatıcı `scripts/run_pi.sh` bu ortam yolunu alır.

**Test bitiminde kamera/görev/panel/kayıt kapalı, 8080/8081 dinleyicisi yok, HailoRT sistem servisi aktifti.** Son sıcaklık 53,2°C, throttled `0x0`; bunlar tarihli okumadır. Bu çalışmada gerçek MAVLink açılmadı, ARM okunmadı; servo, ARM, mod, rota veya FC parametre komutu gönderilmedi.

### Açık işler ve yeni sohbetin devam noktası

1. **Ana görev kalibrasyonu hâlâ açık:** `competition-base.json` eski IMX219 `camera.field-candidate.json` dosyasına bağlı. IMX219 kırık; IMX708 tek seçenek. Ana görev gerçek IMX708 merkezlemesine hazır sayılmamalı. Kullanıcının yeni kalibrasyon yapacak zamanı/ortamı yok; tekrar dama çekimi isteme. İnternette bu fiziksel kameraya doğrudan geçerli evrensel matris bulunmadı; Raspberry Pi tuning dosyası PnP kalibrasyonu değil. Kendi `config/camera.imx708-candidate.json` adayımız mevcut: 40 kare/8 poz, RMS 0,1388 px, 1280×720/tam crop/2304×1296, sabit lens 0,1062771082, `physical_distance_verified=false`. Güncel kurulum/odak/görev mesafesine uygunluğu doğrulanmadı; ana profile sessizce geçirilmedi. Araştırma: `docs/competition/IMX708_HAZIR_KALIBRASYON.md`.
2. **Servo canlı testini kullanıcıyla daha sonra yapacağız:** kullanıcı “sen çevir, ben OK/not OK diyeyim” dedi; son beyanında yük mekanizması henüz takılı değildi. Hazır olduğu sonraki aşamada canlı yer durumu kontrol edilerek devam edilecek. Kırmızı yük AUX1/çıkış 9, mavi yük AUX2/çıkış 10; başlangıç 180°, bırakma 90° kullanıcı beyanı. Gerçek PWM değerleri `null`, tezgâh doğrulaması false, actuator simulated. Dereceden PWM uydurma; fiziksel bırakma doğrulanmadı.
3. **Pixhawk port seçimi açık:** Cube Orange iki USB arayüzü `if00`/`if02` (son ttyACM0/1) olarak göründü. `link.device=null` tek cihaz otomatik seçimi ikisi varken yeterli değil; sonraki bağlantıda doğru port doğrulanıp seçilecek. Güncel ARM/firmware/parametre durumu okunmadı.
4. **Saha rotası yarışma anında verilecek ve kullanıcı Mission Planner'dan girecek.** Koordinatları şimdi isteme/uydurma. Yazılım gerçek FC görevini okuyup arama sıraları, giriş/bitiş kapıları, alan ve rota eşleşmesini o zaman yapılandıracak; hedef koordinatlarının önceden bilinmesi gerekmiyor. “Gerçek hex” kullanıcının altı motorlu yarışma aracıdır, ayrı bir cihaz değildir. Güncel irtifa/hız ve gerçek araç kabulü eski quad/SITL değerlerinden varsayılmaz.
5. Gerçek branda üzerinde HSV/şekil eşikleri, model başarısı, uzak netlik ve montaj yönü henüz kabul edilmedi. Yazılım ve kısa masa testi tamamlandı; gerçek otonom görev/isabet kanıtı yok. Güncel açıklamalar `docs/competition/AKIS.md`, `TESTLER.md`, `EKSIKLER.md` içinde.

---

## Tarihli geçmiş — yukarıdaki güncel özetle çelişen eski durumları uygulama

Aşağıdaki “en güncel”, “30 FPS”, “aktarılmadı” ve eski PID/kalibrasyon/başlatma notları yazıldıkları ana aittir. Güncel kararların yerine geçmez.

## 8 Eylül 07:00 — canlı Hailo çalışıyor, sürücü uyarısı düzeltildi

Kullanıcı kalibrasyon yapacak zaman/ortam olmadığını, saha rotasının yarışma anında Mission Planner'dan girileceğini, yük mekanizmasının henüz takılı olmadığını bildirdi. Servo canlı testi sonraki adım; bu tur servo/MAVLink/uçuş komutu yok. İnternette mevcut kameraya doğrudan geçerli evrensel IMX708 PnP kalibrasyonu bulunmadı; resmî tuning dosyası PnP matrisi değil. Kendi 5 Eylül adayımız mevcut; güncel uygunluğu bilinmiyor, ana profil değiştirilmedi. Araştırma `docs/competition/IMX708_HAZIR_KALIBRASYON.md`.

Pi aynı SSH anahtarıyla `172.20.10.2` bulundu. Önce Hailo4.20.0/HAILO8L aygıt kimliği ve model hash'i doğrulandı. Önceki PCIe kopması bu açılışta yok; model15s rastgele veriyle1561çıkarım, ilk gerçek kamera testi1141kare/~30FPS/hatasız. Fakat çekirdekte42`find_vma` uyarısı vardı. Resmî Hailo kaynak kodundaki mmap_read_lock/unlock düzeltmesi Pi `/usr/src/hailo_pci-4.20.0/linux/vdma/memory.c` içine iki satır olarak taşındı; çalışan kernel6.12.75+rpt-rpi-2712 için DKMS build/install, yalnız Hailo modülü yeniden yükleme yapıldı. Pi reboot/firmware/model/FC değişimi yok. Yedekler Pi/Mac `artifacts/pi/hailo-driver-fix-20260908/` eşleniğinde; ayrıntı REPORT.md. Çalışan modül srcversion `DDE5580B51751E55E460F6D`. Paket güncellemesi yerel yamayı ezebilir.

Son40s kamera testi1174kare/30,004FPS/errornull, yeni kernel uyarısı0/hata0;15kanıt dosyası hash eşleşti. Yalnız yakın yüzey/araç parçaları görüntüsü, branda doğruluğu veya metrik kabul yok. **Son kamera/test/görev/panel süreçleri kapalı, HailoRT servisi aktif.** SoC54,9°C/throttled0x0. Eski kopmanın nedeni veya uzun süreli çözümü kanıtlanmış değil. Pixhawk iki USB arayüzüyle (if00/if02) göründü; MAVLink/ARM okunmadı. Görevlerin `link.device=null` otomatik tek cihaz seçimi bu iki arayüzle yeterli değil; sonraki bağlantıda doğru port seçilecek. Önceki montaj/ofset revizyonu Pi'ye henüz aktarılmadı.

## 8 Eylül — ters kamera montajı ve ofset yerelde işlendi

Kullanıcı açıkça doğruladı: lens yere bakıyor, görüntü üstü drone'un arkasında (180° ters); lens merkezi Pixhawk merkezinden 11 cm ileri, 5 cm aşağıda, sağ/sol sıfır. İki temel profile `offset_body_m=[0.11,0,0.05]`, iki görev profiline `camera_mount_yaw_deg=180` yazıldı. `competition/geometry.py` eski geometriyi değiştirmeden sanal gövde dönüşümüyle iki rengin PnP hesabında ters montajı/eğimi/ofseti birlikte uygular; runtime bu ayarı kullanır. Ham görüntü ve kalibrasyon matrisi döndürülmez. Hızlı görev geometri kullanmaz; ofset/yön yalnız kayıtlı montaj bilgisidir.

`tests/test_camera_mount.py`, mevcut geometri, competition, pause_verify ve quick testleri: **101 geçti**. Yeni 19 test içinde iki renk×iki montaj×üç eğim izdüşümü, iki etkin profil ve geçersiz montaj reddi var. Korunan eski dosyaların hash testi geçti. Gerçek araç/kamera/Hailo/servo veya SITL bu turda çalıştırılmadı; **yeni montaj revizyonu Pi'ye aktarılmadı**. Önceki iki görev dağıtımı aşağıdaki tarihli kayıtta korunuyor.

Montaj artık bilinmiyor değildir; kullanıcı ölçüm beyanıdır, gerçek görüntüyle yön/mesafe kabulü bekliyor. Ana profil hâlâ IMX219 aday kalibrasyonuna bağlı; IMX708 merkezleme hazır değil. Servo PWM, rota/kapı/poligon ve güncel Hailo doğrulaması açık. Boş alanlar ve dolu mühendislik adayları ayrıntılı olarak `docs/competition/EKSIKLER.md` içinde. Kullanıcıdan montaj ölçülerini tekrar istemeyin.

## 8 Eylül — iki görev Pi'ye dağıtıldı, süreçler kapalı

Kullanıcı Pi'yi açtı ve bağlantı bilgilerini verdi. Başlangıç192.168.139.121; ağ değişince aynı MAC/SSH kimlikli Pi192.168.197.121 üzerinden işlem tamamlandı. Proje `/home/furkan/Desktop/safak-gorev2-quad`. Önce çalışan görev/kamera olmadığı görüldü.75dosya aktarıldı ve SHA256 eşleşti; Pi'nin mevcut Python3.11/OpenCV4.11 ortamında99ilgili test geçti. Waitress zaten `runtime/python` altında; yeni paket kurulmadı. Yeni başlatıcı Hailo ortamını açıp `--task hizli --check` kontrolünü doğru yaptı. Eski quad girişi donanım açmadan exit2; aktif profiller yalnız ana-gorev/hizli-gorev. Eski saha profilleri arşivlendi. Özgün Pi dosyaları `runtime/before-two-task-20260907T235924/` ve kaldırılan profiller `archive/pi-before-two-task/` altında. Eski Finder `._` yan dosyaları da arşivlendi; koruma testinde Linux'a ait olmayan `.DS_Store` kapsam dışı, uygulama/profil hashleri denetleniyor.

Kanıt `artifacts/pi/two-task-deploy-20260907/pi-verification.json`, yerel manifest ve Pi `runtime/two-task-deployment.json`. Model safakyepyeni.hef SHA2568433d13e… korundu. **Son okumada görev/kamera/kayıt süreci ve8080/8081dinleyicisi yok.** Uçuş, kamera, Hailo çıkarımı veya servo başlatılmadı; ARM/FC bağlantısı okunmadı. Hailo aygıt dosyası görünüyor ama çıkarım/aygıt sağlığı doğrulanmadı. Ana görevde kalibrasyon/hexofset, iki görevde saha/servo açık işleri sürüyor; dosya kontrolü bunları tamamlandı saymıyor. Aşağıdaki “Pi'ye aktarılmadı” notları tarihli geçmiş oldu. Güncel NoMachine komutu proje klasöründe: `bash scripts/run_pi.sh /home/furkan/Documents/proje/hailo-rpi5-examples/setup_env.sh --task hizli --mode observe`; ana için `--task ana`. Yalnız birini çalıştırın.

## En güncel — MOSSE'siz hızlı görev ve yalnız iki seçenek

Son doğrulama: hızlı görev için4hexSITL senaryosu geçti (tam görev232754, hedef kaybında rota dönüşü233235, duruşta pilot devri233335, karar döngüsü duraklaması233432).157test geçti/5atlandı. `artifacts/quick-task-20260907/` son yazılım hashleri/giriş kontrolü/sonuç özetini içerir. İlk hedef-kaybı SITL testinde seyrek durum örneklemesi nedeniyle test iddiası hatalıydı; üretim kontrolü değiştirilmeden test gerçek komut kaydıyla düzeltildi, tekrar geçti. Güncel test raporu TESTLER.md.

Kullanıcı “MOSSE'siz hızlı görevi yaz, diğer üç eski seçeneği kaldır” dedi. Yerelde seçimler artık **`--task ana` / `config/ana-gorev.json`** ve **`--task hizli` / `config/hizli-gorev.json`**. Tek giriş `safak_gorev2.competition.main`. Ana akış önceki dur–doğrula/merkezlemeyi sürdürür. Hızlı akış0,10s/≥3kare AI adayı→GUIDED/sıfır hız→ölçülen duruş≥0,30s→duruştan sonraki0,10s/≥3kare aynı renk AI→aynı irtifada tek yük komutu→aynı AUTO waypoint. PnP/MOSSE/merkezleme/alçalma yok. Hedef3s doğrulanmazsa yük korunarak rota sürer; kesinti/pilot devri ayrı iptal koşullarıdır. Link de bırakma anında GUIDED/sahiplik/hız/eğim/irtifayı tekrar denetler. Kadraj kenarındaki hedefte isabet garantisi yok.

Eski quad girişi devre dışı (donanım açmadan hata); eski flight/quad/observe saha profilleri ve competition-center/sighting adları kaldırıldı. `sighting` stratejisi artık kabul edilmiyor. Üç eski seçeneğin özgün kaynakları `archive/legacy-options/` altında `.txt`; hash manifestosu var. Kullanıcının açık kaldırma isteği eski giriş/profil koruma talebini güncelledi. Ortak merkezleme/geometri kodu ve model/kayıt kaynakları korundu. Önceki koruma hashlerinin taşınan yolları `preserved-paths.json` ile doğrulanıyor. `analysis-tools.json` yalnız kayıt analizi/kalibrasyon girdisi. Güncel kısa kılavuz README.md ve docs/competition/AKIS.md; aşağıdaki eski komut/profil tarihçesini yeniden etkinleştirmeyin.

157test geçti/5atlandı. Hızlı tam görev hexSITL'de iki ACK+PWM/rotaya dönüş/inişle geçti (`20260907T232754-quick-complete`). Diğer güncel senaryolar TESTLER.md'de. **Pi'ye dağıtım, gerçek araç komutu, kamera veya bağlantı onarımı yapılmadı.** Yeni hızlı temel profil IMX7082304×1296/tam alan/1280×720/sabit lens0,1 başlangıcını kullanır, kalibrasyon/ofset null; güncel uzak netlik doğrulanmadı. Ana profil eski kamera adayına bağlı kaldığı için IMX708 merkezleme kabulü yok. Servo PWM, saha rota/kapıları ve Hailo erişim arızası açık. Aktif süreç/IP bilgisi güncel okunmadan işlem yapılmaz.

## En yeni kullanıcı isteği —0,10s gör, dur, doğrula

Kullanıcı kodun anlaşılmadığını ve0,10s hedef gördükten sonra önce durup doğrulama, doğruysa merkezleme/bırakma, değilse AUTO'ya dönüş istedi. Bu davranış ayrı `competition` merkezleme akışına yerelde uygulandı; eski yalnız mavi dosyaları/hashleri korundu. Giriş `safak_gorev2.competition.main`, profil `competition-center.json`. `vision.py` ham AI kutusunu geometri reddinde de korur. `controller.py` aday≥3kare/0,10s →REQUEST_STOP(GUIDED isteği)→STOPPING(sıfır hız, telemetride≤0,20m/s ve0,30s kararlılık)→VERIFYING(duruştan sonraki taze AI+köşe/PnP≥6kare/0,50s)→merkezleme.3s doğrulanmazsa yükü korur, aynı waypoint'i geri okuyup AUTO'ya döner; aynı renge5s yeniden durma yok.5s duramazsa/kamera-telemetri kesilirse görev iptal, yanlış hedef gibi kör AUTO devri yapılmaz.0,10s fiziksel frenleme süresi değildir. GUIDED durmak için de kullanılır; merkezleme için ikinci mod geçişi gerekmez. MOSSE entegre edilmedi.

Panel artık açık Türkçe aşama/neden/mod ve iki yük durumunu gösteriyor. Kütüphane/okuma rehberi `docs/competition/AKIS.md`; test sonucu `TESTLER.md`. Yerel142test geçti/5atlandı; yeni ArduCopter4.6.3hexSITL tam görev, yanlış hedefte aynı waypoint dönüşü, duruşta pilot devri geçti. Ayrıntı/sonraki testler TESTLER.md içinde. Güncel yazılım manifestosu `artifacts/pause-verify-20260907/`. Pi'ye dağıtım/bağlantı veya gerçek araç işlemi yok. **IMX708 güncel odak/kalibrasyon uyumu, hex ofseti, gerçek servo PWM, rota/kapılar ve son Hailo erişim sorunu hâlâ açık; yerel kod tamamlanması uçuşa hazır beyanı değildir.** Ortak kamera profili hâlâ eski aday; kullanıcıdan projeyi yeniden anlatmasını istemeden bu açık bilgilerle devam edin.

## 7 Eylül — MOSSE önerisi incelendi, yalnız yerel prototip

Dur–doğrula revizyonunun son testi de geçti: `20260907T222328-center-pause-stall` sırasında karar döngüsü1,5s bekletildi; komut zaman aşımı LOITER'a geçirdi, kontrol bırakıldı, yük komutu yok. Böylece yeni revizyonda4hexSITL senaryosu geçti. Son durum PILOT_CONTROL etiketiyle kaydediliyor; burada gerçek pilot müdahalesi değil yazılım zaman aşımı kaynaklı mod değişimidir.

Kullanıcı MOSSE ve ileri/merkezleme komutlarının çakışması önerilerini araştırıp aksiyon istedi. `docs/MOSSE_DEGERLENDIRME.md` raporu ve ayrı `scripts/mosse_probe.py` eklendi. AUTO aramasında kontrol eylemi yok; GUIDED görülmeden merkezleme hızı uygulanmıyor, iki yeni davranış testiyle doğrulandı. Daha önceki raporda ilgili uçuşlar GUIDED'e ulaşmamış; bu tur eski videolar yeniden incelenmedi. MOSSE en fazla0,30s boşluk/0,15s kare aralığıyla yalnız dosyalarda takip ediyor; takip AI kanıtı veya PnP hedefi sayılmıyor, uçuşa bağlı değil. Ana ortam ilgili32test geçti/1contrib testi atlandı; ayrı `runtime/mosse-env` OpenCV contrib4.12 ile5MOSSEtesti geçti. Yapay12karede1başlangıç+7doğru takip, nesne kaldırılınca4boş; gerçek branda/blur/gölge başarısı kanıtı değil. Kanıt `artifacts/mosse-review-20260907/`. Korunan eski dosyaların hashleri aynı; Pi/FC/profil/yarışma kodu değiştirilmedi. Hailo son aygıt arızası bu çalışmada giderilmedi, canlı durum okunmadı. Sırada çalışan çıkarımla temiz gerçek kareler üzerinde karşılaştırma; mevcut yalnız mavi koduna kendiliğinden entegre etmeyin.

## En güncel durum

- Kullanıcı son mesajında **IMX219'un tamamen kırıldığını, tek seçeneğin IMX708 olduğunu** bildirdi. IMX219'a dönmeyi önermeyin. IMX708'in şu anda fiziksel olarak bağlı/çalışır olduğu bu oturumda canlı okunmadı.
- Kullanıcı IMX708 kalibrasyonunun yapılmadığını düşünüyor. Dosya kanıtıyla ayrım: **5 Eylül'den bir IMX708 aday kalibrasyonu mevcut**, fakat mevcut kamera/odak/montaj ve görev mesafesi için geçerliliği doğrulanmış değil. Aynı fiziksel IMX708 olup olmadığı da güncel olarak bilinmiyor. Kullanıcının beyanını yok saymayın; eski adayın bugünkü kuruluma uyduğunu varsaymayın.
- Aday: `config/camera.imx708-candidate.json`; 1280×720, tam crop `[0,0,4608,2592]`, sensör modu2304×1296, sabit LensPosition0,1062771082; 40 kare/8poz, RMS0,1388px. `physical_distance_verified=false`. Kaynaklar `artifacts/calibration/imx708-solve-20260905/`. Lens sayısı fiziksel netlik/mesafe kanıtı değildir.
- **Yeni `config/competition-base.json` hâlâ IMX219 aday kalibrasyonunu gösteriyor. IMX708 ile merkezleme için hazır değil.** Bu devir sırasında kod/profil değiştirilmedi. Önce sensör/odak/crop ve mevcut IMX708 adayının uyumu gözlemde doğrulanmalı; uygun değilse yeniden kalibrasyon yapılmalı. Eski IMX219 matrisini IMX708'e taşımayın. `sighting` seçeneği kalibrasyon/PnP kullanmaz; yine de çalışan kamera ve gerçek hedef tespiti gerekir.
- Yarışma aracı özel hexacopter, Cube Orange+, Pi5/Hailo-8L. Quad saha uçuşu ve ofseti hex için doğrulama değildir. Hex firmware, güncel parametreler, kamera FRD ofseti ve saha rotası bilinmiyor.
- Kullanıcının servo planı: **AUX1 kırmızı yük, AUX2 mavi yük**, MAVLink çıkışları9/10. Başlangıç180°, bırakma90° beyan edildi; gerçek mikro­saniye PWM değerleri ve tezgâh doğrulaması **eksik**. 90°=1500µs diye varsaymayın.
- Kullanıcı yarışmaya ilk talebinde 7 saat kaldığını söyledi. Bu tarihli beyanı yeni oturumda yeniden 7 saat kalmış gibi sunmayın. Az token nedeniyle kısa Türkçe yanıt istiyor.

## Yazılım ve korunacak sınırlar

1. Kullanıcı **yalnız mavi hedefi ortalayan mevcut yazılıma dokunulmamasını** istedi. `safak_gorev2.main`, mevcut `controller.py`, `geometry.py`, saha profilleri korundu; `docs/competition/legacy-sha256.json` önceki içerikleri doğrular.
2. Yeni ayrı paket `safak_gorev2/competition/`. `competition-center.json`: iki renkli metrik merkezleme/alçalma/bırakma. `competition-sighting.json`: kısa tespit doğrulaması sonrası merkezlemeden bırakma; varsayılan3bağımsızkare/en az0,10s. Mavi2×2m hedef→kırmızı yük; kırmızı1×1m hedef→mavi yük. Sıra sabit değil.
3. İki yük için tek seferlik kalıcı defter; gerçek sürücü servo ACK+çıktı PWM doğrulaması kullanır. Bu fiziksel düşüş/isabet kanıtı değildir. Varsayılan `observe`/`simulated`. `flight`+`simulated` gerçek navigasyon komutu gönderebilir; masaüstü demo sanmayın.
4. Merkezleme sonrasında tarama irtifasına çıkılır, kesilen AUTO waypoint'e dönülür; ikinci yükten sonra doğrudan RTL'ye atlanmaz. Gerçek sahada hazırlanmış AUTO TAKEOFF/tarama/bitiş/LAND rotası ve giriş/bitiş kapıları gereklidir; koordinatlar uydurulmadı. Görev1 iki sekiz rotası bu paket tarafından üretilmez.
5. Program yerde DISARM görmeden devralmaz. Pilot müdahalesi kilidi aynı çalıştırmada kalıcıdır; havada yeniden başlatma/kilit sıfırlama yapılmaz. Gerçek araca işlem öncesi canlı durum tekrar okunur; tarihli PID/IP/ARM durumlarını güncel sanmayın.

## Testlerin gerçekten gösterdiği

**119 test geçti, Torch olmadığı için4eski model karşılaştırma testi atlandı.** ArduCopter4.6.3'ün kendi hexacopter SITL modeliyle5senaryo geçti: center tam görev, sighting tam görev, pilot müdahalesi, hedef kaybı, kontrol döngüsü kesintisi. Gazebo kullanılmadı. Kamera kareleri ve AI kutuları sentetikti; gerçek Hailo çıkarım doğruluğu test edilmedi. Uçuş modları/MAVLink ve simüle servo çıkışları ArduCopter'de çalıştı. Gerçek hex uçuşu/yük ayrılması/isabet doğrulanmadı. Kanıt `docs/competition/TESTLER.md`, `artifacts/competition-sitl/`.

Önceki uçuşlarda değişken bulanıklık, aralıklı tespit, geometri reddi ve ayrı bir uçuşta pilot devri kilidi vardı. Tek neden kamera diye kanıt yok. Son bulanık kayıtlar IMX708'e ait: `artifacts/field/video-review/REPORT.md`. IMX219 ret analizi `docs/FIELD_FLIGHT_03.md`. Gazebo eklemekten önce gerçek IMX708→Hailo→branda tespitinin gözlemde doğrulanması önerildi; Gazebo kurulumu başlatılmadı.

## Sonraki çalışma

Önce `AGENTS.md`, bu dosya ve `docs/competition/KULLANIM.md`/`TESTLER.md` okunmalı. İlgili kod ve kanıtlara ihtiyaç oldukça bakılmalı; kullanıcıdan projeyi yeniden anlatması istenmemeli. Öncelik mevcut IMX708 donanım/odak/görüntü durumunu ve aday kalibrasyon uyumunu ayırmak, gerçek branda tespitini gözlemde görmek. Kamera arızası/odak/pozlama/titreşim/model kaynaklarını kanıtsız kesinleştirmeyin. Servo PWM, hex ofseti (merkezleme için), saha rotası ve mekanizma doğrulaması sonra tamamlanmalı. Bu oturumda Pi'ye dağıtım veya gerçek araç komutu gönderilmedi; yeni canlı durum bilinmiyor.

Pi'de bilinen proje `/home/furkan/Desktop/safak-gorev2-quad`; son bildirilmiş IP192.168.137.191 güncel kabul edilmez. Pi model adı `best_hailo_model/safakyepyeni.hef`; Mac'te `best.hef`. Beklenen SHA256 `8433d13ecee9d05852178a0f38c057217d5a7f2db4436036b2a978e877c192e2`. Yeni paket yalnız hash'i eş olan bu adlar arasında dosya okuma uyumu sağlar. Eski yanlış model yolu Pi'ye yeniden dağıtılmamalı.

## Hesap geçişi

Yeni hesapta aynı yerel proje klasörünü açın: `/Users/kaan/Documents/ChatGPT/last şafak`. Yalnız iki Markdown dosyasını değil **bütün proje klasörünü** koruyun; kodlar, config, modeller ve kanıtlar bunların dışındadır. Eski sohbet geçmişinin otomatik erişilebilir olmasına güvenmeyin; yeni göreve aşağıdaki mesajı verin:

> AGENTS.md, README.md ve docs/HANDOFF.md dosyalarını oku. Sonra docs/competition/KULLANIM.md ve TESTLER.md üzerinden devam et. IMX219 tamamen kırık, tek seçenek IMX708. Eski yalnız mavi merkezleme yazılımına dokunma. Önce IMX708'in mevcut durumunu ve eski aday kalibrasyonun uyumunu değerlendir. Türkçe ve kısa yanıt ver.

AGENTS.md uzundur; kritik devir özeti bu kısa dosyada tutulur. [Resmî Codex yönerge belgesi](https://developers.openai.com/codex/guides/agents-md) proje yönergelerinin nasıl okunduğunu açıklar. Yerel dosyalara erişim olmadan yalnız dosya adlarını yazmak içeriklerini sağlamaz.

## 7 Eylül — yurtta yalnız kamera ve panel hızı

Kullanıcı uçuş/test izni olmadığını, sonrasında yalnız kamera görüntüsüne izin olduğunu bildirdi. Windows yer istasyonu yanında değil. Canlı SSH anahtarı eski kayıtla eşleşen Pi `192.168.139.121`, Wi-Fi SSID `test`, ağ geçidi `192.168.139.225`; Mac `192.168.139.254`. TP-Link/Windows paylaşım zinciri doğrulanmadı, ağ değiştirilmedi. Bu adresler sonraki oturumda tekrar okunmalı. Araç ARM/yer durumu okunmadı, varsayılmadı.

Yalnız `scripts/camera_panel.py` açık, son PID3927, port8080; Hailo/MAVLink/servo açılmadı. IMX7081280×720/tamcrop/sensör2304×1296, sürekli AF önizleme; eski sabit odak kalibrasyonuna uyum kanıtı değildir. Kullanıcının 1FPS şikâyetinde kamera30,1FPS ölçüldü. Yalnız kamera panelinde JPEG üretim sınırı ve indirme sonrası sabit125ms bekleme düzeltildi; 15FPS hedefli, gerçek görüntülenen bağımsız kareleri sayan panel göstergesi eklendi. JPEG kimlik/yaş başlıkları artık JPEG'in kendisine ait. Tarayıcıda kamera30,0FPS/panel12,9FPS görüldü. Python/JS sözdizimi kontrolü geçti; Pi/Mac dosya hash eşleşti. Pi yedeği `runtime/camera-panel-before-fps-20260907.py`, yeni log `runtime/camera-only-fps-20260907.log`. Eski yalnız mavi uygulama/profiller değiştirilmedi. Bu önizleme düzeltmesi önceki uçuş tespit/kilit sorununu açıklamaz veya çözülmüş saydırmaz.

Kullanıcı yüklerle toplam4kg ve yükler100g bildirdi; her yükün100g olduğu ayrıca doğrulanmadı. Bunlar tartım kanıtı değildir.

## Son kullanıcı yönlendirmesi — kayıt incelemesi durduruldu

Kullanıcı düzgün kayıt olmadığını söyleyerek incelemeyi açıkça durdurdu; yeni Codex hesabına geçmek için başlangıç promptu istedi. Kayıt incelemesine kendiliğinden devam etmeyin. Kısmen indirilen dosyalar `artifacts/field/crash-review-20260906/` altında; bütünlük karşılaştırması tamamlanmadı, kesin kaza analizi yok. Ön bulgu: en son dosya oturumu095448/IMX219 tamamen DISARM; son ARM içeren oturum090839/IMX708, 6Eylül12:15–12:16. Bu ikinci oturumda kaydedilen470ARM telemetri örneğinde Hailo yaklaşık30FPS,45tespitli örnek,0geçerli hedef; retler26köşe/11kenar/5metrik/3skor. Görsellerde dalgalı çizgiler ve branda kenarları görülüyor; fiziksel nedeni veya kullanıcının kastettiği kaza oturumu kesinleştirilmedi. Bu ön bulgular bugünkü kameranın görev yeterliliğini doğrulamaz. Kullanıcının iptaliyle aktarım durduruldu.

Yalnız kamera paneli son açılan süreçte açık bırakıldı; hesap geçişi Pi sürecini kendiliğinden kapatmaz. Yeni oturumda IP/PID/akış canlı tekrar okunmalı. Kullanıcı yalnız kamera gözlemine izin verdi; gerçek Hailo veya uçuş/servo denemesi için geniş yetki varsayılmamalı.

## 7 Eylül — ayrı pozlama test paneli hazır

Kullanıcı eski videoyu tekrar izlememeyi, yalnız kamerayla pozlama testine ilerlemeyi istedi; Pi/IMX708 açık dedi. Canlı `192.168.139.121` SSH anahtarı önceden bilinen Pi ile eşleşti. Eski panel/görev süreci yok,8080 kapalıydı. Yeni ayrı `scripts/shutter_test_panel.py` Pi'ye aynı proje yolunda aktarıldı ve kamera-only önizleme açıldı. IMX7081280×720/tamcrop2304×1296 sensör modu, taze kare/hata yok; ilk okuma ExposureTime9993µs, gain1,219 ve sürekli AF. Bu anlık değer eski uçuşun pozlamasını kanıtlamaz. Mevcut mavi merkezleme kodu/profilleri değiştirilmedi.

**Pozlama testi henüz başlamadı; kullanıcı uzak sahneyi yerleştirecek.** Panel http://192.168.139.121:8080/ . Yeni süreç için SIGUSR1 tek tur testi başlatır: mevcut odağı kilitler; AUTO referans ve10000/4000/2000/1000µs, her aşama14s (3s yerleşme,5s sabit,6s hafif hareket). Önizlemede Türkçe yönlendirme. Sensör sınırları içinde referans pozlama×gain ürününden manuel gain seçilir. `runtime/shutter-tests/<timestamp>/` içine ~10FPS JPEG dizisi+her karenin gerçek metadata'sı ve istenen/uygulanan değer uyum işareti yazılır. Video konteyneri değil, zaman damgalı görüntü dizisidir. Bitince AE geri açılır, odak sabit kalır. Sözdizimi ve canlı kamera önizlemesi kontrol edildi; tam test henüz yürütülmedi. ARM/MAVLink/Hailo/servo açılmadı. Sonraki adım kullanıcı hazır dediğinde uzak netliği gözlemleyip SIGUSR1 ile başlatmak; test başlamadan kullanıcının kamera sahnesi hazır olmalı.

Kullanıcı elle uzak sahneye tuttuğunu ve “başlat” dediğini bildirdi. SIGUSR1 ile test tamamlandı: Pi `runtime/shutter-tests/20260907T170901/`,442JPEG+metadata, beş aşamanın tümü var;442/442istenen pozlama/gain/odak toleranslarıyla eşleşiyor. LensPosition0,3200082779 tüm kayıtlarda sabit. AUTO medyan374µs; manuel gerçek medyanlar9993/3981/1977/988µs, gain tümünde1,122807. Bu sahne çok aydınlık: AUTO zaten önerilen1000µs'den kısa; manuel uzun pozlamalar aşırı parlak olabilir, görseller henüz incelenmedi. Bu nedenle henüz kazanan ayar veya eski uçuşun bulanıklık nedeni ilan edilmedi. Mac metadata/manifest `artifacts/calibration/shutter-20260907/`; JPEG'ler Pi'de. Test bitti, AE önizlemeye geri döndü, odak sabit kaldı; kullanıcıya artık sabit tutması gerekmediği söylendi. Panel açık, Hailo/uçuş/servo kapalı.

Test karşılaştırması: her aşamanın SABİT/HAREKET bölümünden ortadaki birer kare (toplam10) Mac'e alındı; `artifacts/calibration/shutter-20260907/comparison.jpg` görsel olarak incelendi. AUTO referans bu örneklerde detay/pozlama açısından en kullanılabilir görüntü;10000/4000µs ciddi aşırı pozlama,2000µs belirgin parlak alan kaybı,1000µs de AUTO'dan daha fazla parlak alan kaybı gösteriyor. Gain zaten minimumdaydı. Bu aydınlık sahnede sabit1/500 veya1/1000 önerilmez; kontrollü eş parlaklık sağlanamadığından salt hareket bulanıklığı kıyaslaması sayılmaz. Mevcut önizleme otomatik pozlama+sabit odakta bırakıldı. Daha düşük ışık/zemin ve gerçek hedef doğrulaması yapılmadan uçuş ayarı veya kamera sağlamlığı kararı verilmedi. Kullanıcının eski video incelememe talebi korundu.

## 7 Eylül — canlı yalnız kamera + Hailo paneli

Kullanıcı gerçek mavi brandaya aşağıdan bakacak arkadaşlarıyla pencere testi önerdi; modeli şimdi açmayı ve kamera ayarlarını birlikte değerlendirmeyi açıkça istedi. Ayrı `scripts/camera_hailo_panel.py`, `scripts/run_camera_hailo.sh`, `config/camera-hailo-only.json` oluşturuldu; eski backend yalnız ithal edildi, değiştirilmedi. Ana uygulama/controller/MAVLink/servo başlatılmaz. Önce shutter panel2767 temiz kapatıldı; yeni panel8080 üzerinde Hailo ile açıldı. HEF safakyepyeni.hef SHA2568433d13e… doğrulandı. IMX7081280×720/tamcrop/sensör2304×1296; sabit lens0,3200082779, otomatik pozlama, kalibrasyon yok/PnP yok; kutu gösterim eşiği0,40. Yeni ayarlar yalnız bu ayrı profilde. Mevcut sabit odak uzak sahne testinden, branda için ayrıca netlik kabulü yapılmadı.

Canlı frame233/taze54ms/HAILO/errornull doğrulandı; o an kutu yok. Kullanıcıya modeli açtığımız, şimdi brandaya çevirebileceği ve paneli yenilemesi söylendi. Panelde anlık ExposureTime/gain gösterilir; `live_camera_metadata` en son kamera karesine aittir, çıkarım karesiyle kesin eşleme iddiası yok. Kayıt `runtime/camera-hailo-only/20260907T172243`: her çıkarımın ham tespitleri JSONL, saniyede1kutulu JPEG. Tam video veya kare eşli pozlama kaydı değildir. Kullanıcı kamerayı tutmayı bekliyor; sıradaki iş taze branda görüntüsünü görüp tespit/odak/pozlamayı değerlendirmek. Hailo kurulumu mevcut `/home/furkan/Documents/proje/hailo-rpi5-examples/setup_env.sh`; uçuş izni yok.

Kullanıcı “kayıt almaya başla kamerayı ayarla” dedi. Ayrı camera_hailo_panel güncellendi:1280×720 MJPEG AVI30FPS nominal/30ssegment; gerçek frame_id/captured_at ve video sıra bilgisi JSONL. Gerçek işleme kare hızı nominal30'dan düşük olabilir, süre için captured_at kullanılmalı. Her kayda en son kamera metadata'sı `latest_camera_metadata_unmatched` olarak yazılır; kesin çıkarım karesi eşlemesi değildir. JSON kontrol dosyasından yalnız LensPosition/ExposureValue sensör sınırları içinde uygulanır; ana backend değişmedi, ayrı proxy kullanılır. Önceki Hailo süreci16797 temiz kapatılıp yeni kayıt `runtime/camera-hailo-only/20260907T172545` başlatıldı. Video2169kare/errornull, iki kapanmış segment83/78MB ve üçüncü ilerleyen dosya doğrulandı; decode kontrolü henüz yok.

Canlı brandada0,64kutusu görsel doğrulandı. Pozlama~1ms idi. EV−0,5 ve lens0,32→0→0,1 denendi; kamera/brandanın duruşu değiştiğinden kontrollü netlik veya başarı üstünlüğü kanıtlanmadı. Branda gölgede olduğundan EV0'a dönüldü. **Son geçici gözlem ayarı LensPosition0,1 (gerçek0,10000000149), AE açık/EV0; gerçek pozlama1336µs/gain1,1228; anlık mavi kutu0,509.** Kalıcı uçuş ayarı değildir. Kontrol dosyası Pi `runtime/camera-hailo-controls.json`; Mac ayrı profil başlangıç lens0,32, kontrol dosyası açılıştan sonra override eder. Panel sabit odak/AE; uçuş kodu ve profilleri değiştirilmedi. Yeni görseller/status `artifacts/calibration/branda-live-20260907/`. Video kaydı açık bırakıldı; sonraki adım kullanıcı kadrajı sabit tuttuğunda gölge/güneş tespitini kıyaslamak, kayıt bitince temiz kapatmak. Her süreç yeniden canlı okunmalı.

Kullanıcı brandayı toplattığını, artık konuşmak istediğini söyledi;0,51skor ve eski modele yeni görüntülerle eğitim/veri artırma hakkında soruyor. Video/Hailo paneli PID20004 SIGTERM ile temiz kapatıldı;8080 dinleyicisi ve süreç yok doğrulandı. Kayıtlar Pi'de korunuyor. Yeni model klasöründe .pt yok; `safak_v2_hailo_model/safak_v2.pt` eski modelin eğitim ağırlığı mevcut. Son kayıtların JPEG/video görüntüsü AI kutu/yazıları içerir; doğrudan eğitim verisi gibi kullanılmamalı, temiz kareler veya işaretli alanı dışlayan güvenilir seçim gerekir. Yeni modelin orijinal .pt ve eğitim verisi kullanıcıdan öğrenilmeli; eğitim başlatılmadı.

## 7 Eylül — kırmızı/mavi yeni çekim, Hailo arızası ve temiz kamera kaydı

Kullanıcı daha dik/gölgesiz kırmızı+mavi testini kayıtla açmamızı ve klasör konumunu istedi. Hailo yeniden açılışında /dev/hailo0 error6/device disconnected ve segfault; başka Hailo süreci yoktu. PCIe aygıtı lspci'de görünüyordu. Yalnız hailo_pci modülü kaldırılıp yeniden yüklendi; yeniden probe “Failed reading device BARs, device may be disconnected” verdi. İkinci Hailo açılışı cihaz0/status74ile başarısız. Pi yeniden başlatılmadı, fiziksel neden doğrulanmadı; kayıt sırasında yeniden başlatmayın.

Kullanıcıyı bekletmemek için açıklanarak ayrı `scripts/camera_record_panel.py` açıldı: **model kapalı**, yalnız IMX7081280×720/sensör2304×1296/tamcrop/sabitLens0,1/otomatikpozlama. **Yeni aktif kayıt Pi `/home/furkan/Desktop/safak-gorev2-quad/runtime/red-blue-camera-recordings/20260907T174756/`**;30s MJPEG AVI segmentleri, her gerçek video karesiyle eşlenmiş metadata frames.jsonl, manifest. Video üstüne kutu/yazı çizilmiyor, daha sonra çıkarım/eğitim için temiz görüntü. Nominal30FPS, gerçek zaman SensorTimestamp üzerinden. API72kare/errornull ardından ilerleme doğrulandı. Kullanıcıya “kayıt açıldı, şimdi tut, paneli yenile; canlı AI yok” söylendi. Önceki kutulu kayıtlarla karıştırmayın. Panel8080açık; uçuş/MAVLink/servo yok. Test bittiğinde sadece kaydı bitirip önizlemeyi açık tutma beklentisi var; mevcut ayrı script kayıt+önizlemeyi birlikte yürütür, temiz kayıt kapanışı sonrası camera_panel ile önizleme açılabilir. Hailo onarımı yeni çekimden sonra.

Kullanıcı30s daha kayıt sonra bağlantı onarımı istedi. Kayıt25292 SIGTERM ile kapandı: **4017kare/267,003692s gerçek zaman**,9AVI; tüm segmentlerin ilk ve son kareleri OpenCV ile açıldı, bildirilen toplam kare sayısı JSONL ile eşleşti. Yaklaşık15FPSgerçek yakalama, AVI nominal30FPS; video hızlı oynayabilir, analizde SensorTimestamp kullanın. Sonra ayrı önizleme31083açıldı; kullanıcı “kapa kapa model niye çalışmadı” deyince o da SIGTERM ile kapatıldı. **Şu an8080kapalı, kayıt/kamera/model kapalı.**

Hailo özel PCIe FLR reset denendi (hailo_pci unload→0001:01:00.0/reset→reload),65,5s sonunda “not ready…giving up”; yeniden probe BAR okuma hatası devam. Sürücü4.20.0/kernel6.12.75; geçmiş dmesg'de hailo_vdma_buffer_map/find_vma uyarıları var, kök neden/uyumsuzluk kanıtı değil. Anlık throttled0x0/SoC48,3°C. Kanıt `artifacts/pi/hailo-disconnect-20260907/dmesg.txt` (reset tamamlanmasından önce alınan günlük). Yeniden başlatma/güç döngüsü yapılmadı; sonraki adım Pi/Hailo temiz güç döngüsü ve tekrar aygıt kimliği, sonra model çıkarımı. Kamera branda tespiti değil aygıt erişimi engeli; model dosyası değiştirilmedi.
## 12 Eylül 2026 — AUX1 ana görev saha kurtarma

Son iki AUX1 kaydında servo arızası bulunmadı: PWM isteği hiç oluşmamıştı. Son uçuş rota digest uyuşmazlığıyla `WAIT_AUTO` kaldı. Önceki uçuşta kırmızı hedefte durup merkezlendi, fakat PnP kesilince alçalmadan kalıcı iptal oldu.

Düzeltmeler Pi'de: ana tarama hızı 2,5 m/s; PnP emniyet eşiklerini gevşetmeden, duruşta doğrulanmış sabit hedef aynı OpenCV dörtgeniyle izlenmeye devam eder; görsel hedef de kaybolursa AUTO rotasına dönüp tekrar denenir. Alçalma yüksekliği PnP ve FC irtifasının muhafazakâr küçüğüyle sınırlıdır; hedef 5 m. Panel aktif kırmızı/pasif mavi hedefi ayırır.

Canlı rota: TAKEOFF1/WP2–6 15 m, LAND7 1 m; AUX1-only digest `084b315891c3cee52707fd65beb970bd58f77b5505370365e6a8cb3c4dbbc47e`, EŞLEŞİYOR. Yerel 354 geçti/5 atlandı, Pi 312 geçti. Yedek `runtime/before-field-recovery-20260911/`. Uygulama kapalı; servo/ARM/mod/parametre yazılmadı.
