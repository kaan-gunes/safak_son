# Doğrulama — 7 Eylül 2026

## 12 Eylül — zaman eksenli hedef takibi

**387 yerel test geçti, 5 atlandı** (4 Torch, 1 ayrı MOSSE ortamı). Değişiklikten önceki temel 354 geçti/5 atlandı idi; eski 354 testin hepsi aynen geçmeye devam ediyor, 33'ü yeni `tests/test_target_tracking.py` testidir. Kod varsayılanı `tracking.enabled=false` olduğu için mevcut testlerin gördüğü davranış bit bit aynıdır; takip yalnız `config/ana-gorev.json` ve `config/hizli-gorev.json` ile yeni testlerde açıktır. `git diff --check` geçti, korunan eski dosyaların SHA256'ları değişmedi.

Yeni testler: tek kare kaybında etiketin korunması; köprü penceresi → `TEMPORARILY_LOST` → `LOST` sırası ve izin tamamen bırakılması; kayıptan sonra yeniden doğrulama zorunluluğu; tek karelik yanlış tespitin köprülenmemesi; fiziksel olarak imkânsız sıçramanın süzgeci bozmaması; ulaşılabilir hareketin kabulü; süzülmüş merkezin daha az zıplaması ve yanlı olmaması; sabit hızlı hedefte gecikmenin 1280 pikselde ~2,5 pikselin altında kalması; yüksek doluluklu ama tutarsız adayın seçilmemesi; uzun boru hattı boşluğunda izin sıfırlanması; kadrajı terk eden kestirimin etiketi düşürmesi; iki rengin bağımsız izlenmesi; gerçek piksellerden boş kare üzerinden uçtan uca etiket süreklilliği; takip kapalıyken çıktının birebir eski olması; gerçek tespitin `bbox`/`color_fill` alanlarının asla süzgeçle değiştirilmemesi; köprülenen adayın `fresh_candidates()`'e hiç girmemesi ve yük bırakamaması; aynı kare dizisinde köprüleme açıkken hedefin alınıp kapalıyken alınamaması; yapılandırma doğrulaması; saha profillerinin köprü penceresini `max_lock_frame_gap_s` içinde tutması. Panel tarafında `debug_lines()` çıktısı ve gözlem modunda köprülenen etiketin gerçekten çizilmesi ayrıca sınandı.

ArduCopter 4.6.3 hex SITL (loopback, sentetik görüntü, simulated yük), takip AÇIK ve KAPALI ikili karşılaştırma:

| Senaryo | Strateji | Takip | Sonuç |
|---|---|---|---|
| complete | center | kapalı | PASS — DONE, iki SIMULATED yük |
| complete | center | **açık** | PASS — DONE, iki SIMULATED yük |
| complete | quick | kapalı | PASS — DONE, iki SIMULATED yük |
| complete | quick | **açık** | PASS — DONE, iki SIMULATED yük |
| verify-loss | quick | **açık** | PASS — yük komutu 0, aynı seq2/AUTO dönüşü |

`tests/run_competition_sitl.py` yeni `--tracking` bayrağıyla koşulur; `result.json` artık `tracking` alanını taşır.

**Bu turda giderilmeyen, önceden var olan iki bayat senaryo:** `quick/false-target` ve `quick/no-target`. Her ikisi de takip AÇIK ve KAPALI iken **aynı şekilde** başarısız; bu revizyondan bağımsızdır. `false-target` yalnız AI `Detection` kutusunu gizliyor, oysa boru hattı YOLO/AI okumayı bıraktı ve renkli kare çizili kaldığı için yük bırakılıyor. `no-target` inişten sonra `INCOMPLETE` bekliyor, kod `ABORTED` üretiyor; her iki koşuda da yük sayısı 0. Kanıt ve ayrıntı: `artifacts/target-tracking-20260912/summary.json`.

Takip katmanının ölçülen maliyeti Mac'te 2 renk × 3 aday için kare başına ~17 µs (5000 kare). Pi üzerinde ölçüm yapılmadı. Gerçek kamera, gerçek uçuş ve gerçek branda hedefinde blur toleransı **doğrulanmadı**; yukarıdaki kanıt sentetik görüntü ve SITL'dir. Tasarım ve parametre gerekçeleri: [Hedef takibi](HEDEF_TAKIBI.md).

## 11 Eylül — iki yük sonrası doğrudan LAND

Yerel testler: **247 geçti, 5 atlandı** (4 Torch, 1 ayrı MOSSE ortamı). `tests/test_land_after_payloads.py` ana/hızlı ikinci yük onayı, simüle/servo sonucu, LAND telemetri onayı, bitiş kapısı olmadan tamamlama, ret/belirsizlik, mod zaman aşımı, pilot devri ve bayat heartbeat senaryolarını kapsar. Mevcut tam renk/merkezleme testleri ilk yükte rota dönüşünü ve ikinci yükte LAND davranışını doğrular. Korunan eski kaynakların hash testi geçti. Kanıt: `artifacts/land-after-payloads-20260911/local-tests.txt`.

İlk tam test çalışmasında bir eski füzyon testi ikinci yük sonrası AUTO bekliyordu; yeni LAND beklentisine güncellenip tüm testler yeniden geçti. İlk ana SITL'de araç doğru şekilde LAND/DONE oldu; testin DISARM sonrasında waypoint sırasını 2 sanması hatalıydı (otopilot 0'a sıfırladı). Kontrol, havadaki LANDING/seq2 örneğine ve ikinci yük sonrası hiç resume/AUTO/yükselme komutu olmamasına taşındı. Son ana ve hızlı hex SITL yeniden koşuları **2/2 geçti**; ikinci yükten sonra LAND/seq2 → DONE, resume/AUTO/velocity yok. Kesin loglar ve `sitl-summary.json` aynı kanıt klasöründedir. Gerçek araç testi veya Pi dağıtımı değildir.

**Sonuç: 7 yeni ArduCopter 4.6.3 hex SITL senaryosu geçti.** Ana tam görev, hedef yok, yanlış hedef, doğrulama kaybı, pilot müdahalesi ve 10 m rota/9,5 m sınırı; ayrıca hızlı tam görev. Tam görevlerde iki SIMULATED yük, aynı waypoint ile AUTO dönüş ve son LAND doğrulandı. Görüntü/YOLO sentetik; gerçek kamera veya uçuş kabulü değildir.


## 11 Eylül — iki kamera ve recorder revizyonu

**233 yerel test geçti, 5 atlandı:** 4 Torch eksikliği, 1 ayrı MOSSE ortamı. Sözdizimi ve diff biçim kontrolü geçti. Başlangıçta eski profil sayım testi, önceden eklenmiş hızlı saha profilini dışladığı için başarısızdı; iki strateji ve yeni kamera profilleriyle güncellendi. Özgün ortak dosyalar hash korunarak arşivlendi; eski yalnız mavi controller/geometri değişmedi.

Yeni testler: kamera/backend/kalibrasyon çapraz kullanım reddi; Arducam yalnız gözlem ve payload engeli; mission_digest doğrulama ve genel fingerprint reddi (resume dahil), waypoint/irtifa değişikliği; 6 bağımsız kare/0,5 s; 9,49/9,5/10 m sınırı; simulated yükün tek kalıcı kaydı ve sıfır MAVLink çağrısı. Recorder iki profil/sentetik HTTP ve gerçek yerel FFmpeg ile SIGTERM/video kare sayısı, SIGKILL yarım kayıt ve panel kaybını sınar. Bunlar fiziksel kamera veya gerçek Wi-Fi koparma deneyi değildir.

SITL süreç sonuçları ve tam kanıt: [11 Eylül raporu](../../artifacts/dual-camera-20260911/REPORT.md), [senaryo sonuçları](../../artifacts/dual-camera-20260911/sitl-suite.json). Envanter/probe ve kalan fiziksel kabuller [iki kamera rehberinde](IKI_KAMERA_KABUL.md). İlk SITL varsayılan dosya eksikliği denemeleri başarısızdır ve geçti sayılmadı. Yeni fiziksel kamera testi yok; son IP SSH bağlantısını reddetti.


## 8 Eylül —50FPS ve YOLO/OpenCV ortak arama

**209test geçti,5atlandı** (4Torch,1ayrı MOSSE ortamı). Yeni `test_color_fusion.py`33test; YOLO kutusu olmadan iki renkli arama, tek karede/bölgede ortak doğrulama, daire/üçgen/boş çerçeve reddi, HSV kırmızı sarımı, farklı bölge/renk/düşük skor/kadraj dışı kutu, eski renk kanıtının yeni YOLO'ya taşınmaması, iki stratejide yalnız OpenCV ile durma ve eksik ortak kanıtta rotaya dönme kapsanıyor. Ayrıca gerçek görüntü piksellerinden başlayıp yalnız OpenCV duruşu→YOLO/OpenCV doğrulaması→iki temsili yük→AUTO dönüşü uçtan uca birim testte geçti. Eski korunan kaynak hashleri aynı. Python/JavaScript sözdizimi ve `git diff --check` geçti.

Pi'nin Hailo Python ortamında ilk dağıtımda124ilgili test geçti (son ek uçtan uca testten önce). Sistem `python3` ortamında pytest yok; paket kurulmadı, mevcut Hailo ortamı kullanıldı. Son aktarım/kontrol kaydı `artifacts/fusion-20260908/` içinde.

Yeni kodla ArduCopter4.6.3hexSITL:

- [Hızlı tam görev](../../artifacts/competition-sitl/20260908T072604-quick-complete/result.json): iki servoACK/PWM, kesilen waypoint'e dönüş ve iniş; DONE.
- [Ana tam görev](../../artifacts/competition-sitl/20260908T072851-center-complete/result.json): iki hedefte ortak doğrulama/merkezleme/alçalma, iki servoACK/PWM, rota dönüş ve iniş; DONE.
- [Duruşta YOLO kaybı](../../artifacts/competition-sitl/20260908T073247-quick-false-target/result.json): renkli hedef görüntüsü sürerken VERIFYING sırasında YOLO kutuları kaldırıldı; yük komutu0, aynı seq2/AUTO dönüşü geçti.

Tam görevlerde erken/kenardaki adaylar ortak kanıtı tamamlayamadığında yük korunarak rotaya dönüldü; sonraki karşılaşmalar doğrulandı. Görüntü/AI ve servo simülasyondur. Simülasyonun kalibrasyon/irtifa/kamera ayarları sentetiktir; gerçek anaIMX708 kalibrasyonu kabulü değildir.

**Canlı Pi hız testi:** hızlı profil50FPS, gerçek IMX708→Hailo→OpenCV ve panelJPEG üretimiyle45,42s.2152çıkarım,2151işlenmiş kare; her iki akış **50,03FPS**. Kapanışta son çıkarım tüketilmeden test sonlandı. Renk/vision aşaması ortanca3,67ms, p95=6,78ms; yakalama→tam sonuç ortanca42,57ms, p95=49,39ms. İşlem CPU yükü tek çekirdek ölçeğinde%126,6 (yaklaşık1,27çekirdek; makinenin tamamının%126'sı değil). Hata/kopma/yeni çekirdek uyarısı0. Kalibrasyonsuz hızlı görev testidir; gerçek anaPnP yükü, HTTP istemcisi ve ayrı video kaydı ölçüme dahil değil. Görüntü/ışık ve aday sayısına bağlı işlem yükü değişebilir; uçuşta50FPS garantisi değildir. Kanıt [report.json](../../artifacts/fusion-20260908/fusion-probe-20260908T072828/report.json).

Sensör2304×1296/tamcrop4608×2592,1280×720,sabitLens0,1 korundu. Yeni montaj180°/FRD[0.11,0,0.05] ve ortak arama Pi'ye aktarıldı. Görev/servo/MAVLink veya uçuş başlatılmadı; kamera testi kapanınca panel/kamera süreci bırakılmadı. Gerçek branda hedeflerinin yeni renk eşikleriyle kabulü henüz yapılmadı. Ana profil eskiIMX219 kalibrasyonuna bağlı kaldığı için gerçekIMX708 merkezleme hazırlığı tamamlanmadı.

## 8 Eylül — 180° kamera montajı / 11 cm ileri, 5 cm aşağı

`.venv/bin/python -m pytest -q tests/test_camera_mount.py tests/test_geometry.py tests/test_competition.py tests/test_pause_verify.py tests/test_quick_task.py`: **101 geçti**. Yeni montaj testleri bağımsız optik izdüşümle iki renk, normal/180° montaj ve üç araç eğiminde hedef NED konumunu/kamera yüksekliğini sınar; hızlı görev ham kutuyu korur ve metrik hedef üretmez. Etkin iki profilin kullanıcı montajını yüklemesi ve desteklenmeyen açının reddi de sınandı. Korunan eski geometri/kontrol kaynaklarının hash testi geçti. Bu tur tam test paketi veya SITL yeniden çalıştırılmadı; gerçek donanım/Pi dağıtımı/uçuş denemesi yapılmadı. Önceki sonuçlar aşağıda tarihli kanıttır.

## Son revizyon: yalnız ana ve MOSSE'siz hızlı görev

**157test geçti,5atlandı** (4Torch,1ayrı contrib/MOSSE ortamı). `test_quick_task.py` yeni hızlı akışın metrik hedef olmadan iki renkli tam görevini, hiç hız/irtifa yönlendirmesi vermeden durup bırakmasını, duruş sonrası yeni AI zorunluluğunu, kayıp/yanlış renk/sıçrama/aralıklı/tekrarlanan karelerde bırakmamasını, link'te tekrar hız/mod/eğim/irtifa kontrolünü ve yalnız iki aktif görev profilini doğrular. Mevcut ana merkezleme ve diğer testler de aynı çalıştırmada geçti. Eski quad girişi donanım modüllerini yüklemeden hata verir; kaldırılan profil reddedilir; arşiv özgün hashleri tutar. Kanıt `artifacts/quick-task-20260907/entry-checks.json`.

Yeni hızlı tam görev: [20260907T232754-quick-complete/result.json](../../artifacts/competition-sitl/20260907T232754-quick-complete/result.json). ArduCopter4.6.3hexSITL, iki renk için duruş/kısa AI doğrulaması, iki simüle servo ACK+PWM, aynı waypoint/AUTO ve iniş: DONE. Merkezleme veya alçalma aşamasına girilmedi. Kamera/AI ve fiziksel servo simülasyondur; gerçek Hailo, kamera, yük düşüşü veya isabet kanıtı değildir.

Hızlı görevde duruştan sonra AI kaybolması: [20260907T233235-quick-false-target/result.json](../../artifacts/competition-sitl/20260907T233235-quick-false-target/result.json). VERIFYING sırasında taze görüntüler sürerken AI kutuları kaldırıldı; yük komutu yok, aynı seq2/AUTO'ya dönüş doğrulandı. İlk test çalıştırması ara `RESUME_SELECT` durumunu10Hz ekran örneklemesinde göremediği için başarısız olmuştu; kodun dönüşü gerçekleşmişti. Test bu kısa durumu örneklemede aramak yerine doğrudan `resume` komut kaydı ve güncelAUTO/seq doğrulamasını kullanacak şekilde düzeltildi; yukarıdaki tekrar geçti. Hızlı görev bu testte gerçek gölge sınıflandırmasını değerlendirmez.

Hızlı görevde frenlerken pilot devri: [20260907T233335-quick-pause-pilot/result.json](../../artifacts/competition-sitl/20260907T233335-quick-pause-pilot/result.json), yük komutu yok; LOITER ve kontrol sahipliğinin bırakılması doğrulandı. Frenlerken karar döngüsü1,5s duraklatma: [20260907T233432-quick-pause-stall/result.json](../../artifacts/competition-sitl/20260907T233432-quick-pause-stall/result.json), komut zaman aşımı LOITER'a geçirdi; yük komutu yok, kontrol bırakıldı. Son durum etiketi PILOT_CONTROL bu ikinci senaryoda insan müdahalesi değil mod değişiminin denetleyicide görülmesidir. **Yeni hızlı görev için4hexSITL senaryosu geçti.**

Yeniden çalıştırma: `.venv/bin/python tests/run_competition_sitl.py --ardupilot /tmp/safak-ardupilot-4.6.3 --strategy quick`. `--strategy center` güncel ana görevi sınar. Eski `sighting` seçimi kaldırıldı. Aşağıdaki eski test sayıları/strateji isimleri tarihli kanıttır; güncel kullanım için AKIS.md okunur.

## Yeni dur–doğrula akışı

**142 test geçti; 4 Torch testi ve ayrı contrib ortamı isteyen 1 MOSSE testi atlandı.** MOSSE bu uçuş değişikliğine bağlı değil; kendi ayrı ortamındaki test sonucu `docs/MOSSE_DEGERLENDIRME.md` içinde. Python ve panel JavaScript sözdizimi, `git diff --check` geçti. Korunan eski dosyalarda SHA256 farkı yok. Yeni durumlar için `tests/test_pause_verify.py` içindeki17test; 0,10s ham AI adayı, yinelenen kare, GUIDED cevabı, ölçülen duruş, geometri reddi/kutu sıçraması/aralıklı kanıt, aynı waypoint'e dönüş, tekrar deneme beklemesi, doğrulama sonrası merkezleme, pilot müdahalesi, kamera kesintisi ve zaman aşımı davranışlarını kapsıyor.

Bu turda ArduCopter4.6.3 hexacopter SITL ile yeniden çalıştırılanlar:

| Senaryo | Sonuç | Kanıt |
|---|---|---|
| Yeni center tam görev | İki renk için duruş/doğrulama/merkezleme, iki servo ACK+PWM, AUTO dönüş ve iniş: DONE | [result.json](../../artifacts/competition-sitl/20260907T221449-center-complete/result.json) |
| Yanlış hedef | AI kutusu var, geometrisi doğrulanmıyor; durdu,3s doğrulama sonunda aynı seq2 AUTO'ya döndü, yük komutu yok | [result.json](../../artifacts/competition-sitl/20260907T221922-center-false-target/result.json) |
| Frenlerken pilot devri | PILOT_CONTROL; sonra LOITER/kontrol bırakma ve yük komutu yok doğrulandı | [result.json](../../artifacts/competition-sitl/20260907T222056-center-pause-pilot/result.json) |
| Frenlerken karar döngüsü1,5s duraklatıldı | Komut zaman aşımı LOITER'a geçirdi, kontrol bırakıldı, yük komutu yok | [result.json](../../artifacts/competition-sitl/20260907T222328-center-pause-stall/result.json) |

Duraklama deneyinde denetleyici LOITER mod değişimini gördüğünde son durumu `PILOT_CONTROL` olarak kaydeder; bu senaryoda mod değişimini pilot değil komut zaman aşımı koruması başlatmıştır. Durum adı tek başına fiziksel pilot müdahalesi kanıtı değildir.

Tam görevde ilk erken adaylar kadraj/geometri koşullarını tamamlamadığı için reddedildi; AUTO'ya dönüş ve sonraki tekrar denemelerde iki hedefin kabulü görüldü. Başarı için geometri kuralları kaldırılmadı. Bütün bu görüntüler/AI kutuları sentetik, servo çıkışları simülasyondur. Gerçek hedef sınıflandırması, Hailo, kamera, mekanizma ve hex uçuş kabulü değildir. Güncel yazılım hashleri `artifacts/pause-verify-20260907/software-sha256.json`; bu revizyon Pi'ye dağıtılmadı.

Yeni senaryolar: aynı SITL komutuna `--scenario false-target`, `pause-pilot` veya `pause-stall` eklenir. Deney programı yalnız kendi açtığı loopback simülasyona bağlanır. Sonraki tarihli tablolar önceki sürümün geçmiş kanıtlarıdır.

## Önceki sürümün sonuçları

**119 test geçti; Torch kurulu olmadığı için mevcut model karşılaştırmasının 4 testi atlandı.** Bunların 41 tanesi yeni yarışma testidir. Eski kod/profil SHA256 karşılaştırmasında değişiklik yok.

Yeni kapsam: iki renk ve iki sıra, doğru karşı yük eşlemesi, tek sefer bırakma, eski/gelecek/yinelenen kare, kutu sıçraması, uçuş/rota kapıları, pilot kilidi, hedef kaybı, dönüş ve AUTO yeniden katılma, ACK+PWM, yanlış kaynak, zaman aşımı, motor çıkışını reddetme, strateji değişiminde kalıcı defter, salt okunur iki renkli çalışma ve kırmızı hedefin 1 m metrik geometrisi.

## Yerel ArduCopter 4.6.3 hexacopter SITL

Kendi başlatılan loopback SITL kullanıldı. Uçuş dinamiği, AUTO/GUIDED/LAND ve MAVLink servo komutları ArduCopter üzerinde yürütüldü; kamera görüntüleri ve AI kutuları sentetik, servo çıkışları simülasyondur. Her iki tam akışta iki ayrı servo için ACK ve PWM doğrulandı; parkur bitişi ve iniş görüldü.

| Senaryo | Sonuç | Kanıt |
|---|---|---|
| center/complete | DONE | [result.json](../../artifacts/competition-sitl/20260907T120111-center-complete/result.json) |
| sighting/complete | DONE | [result.json](../../artifacts/competition-sitl/20260907T120437-sighting-complete/result.json) |
| center/pilot | PILOT_CONTROL | [result.json](../../artifacts/competition-sitl/20260907T120725-center-pilot/result.json) |
| center/lost-target | ABORTED | [result.json](../../artifacts/competition-sitl/20260907T120828-center-lost-target/result.json) |
| center/control-stall | PILOT_CONTROL | [result.json](../../artifacts/competition-sitl/20260907T120933-center-control-stall/result.json) |

Pilot, hedef kaybı ve döngü kesintisi deneylerinin her birinde yük komutu oluşmadığı, SITL LOITER ve kontrol bırakma davranışı deney programınca doğrulandı. İlk geliştirme denemeleri HOME satırının FC açılışında değişmesini ve ArduCopter LAND param4 normalizasyonunu ortaya çıkardı; bunlar yeni pakette düzeltildi ve tam akışlar ardından geçti. Eski mavi algoritması değiştirilmedi.

Yeniden çalıştırma:

```bash
python -m pytest -q
python tests/run_competition_sitl.py --ardupilot /tmp/safak-ardupilot-4.6.3 --strategy center
python tests/run_competition_sitl.py --ardupilot /tmp/safak-ardupilot-4.6.3 --strategy sighting
```

Diğer senaryolar `--strategy center --scenario pilot`, `lost-target`, `control-stall` ile seçilir. Test yalnız başlattığı yerel SITL adreslerine bağlanır; gerçek araç adresi parametresi yoktur.

## Gerçek araç kabulü yapılmadı

Gerçek iki renkli Hailo başarısı, yeni hexacopter kamera montajı/merkezleme uçuşu, fiziksel servo açı/PWM ve yük ayrılması/isabeti doğrulanmadı. Gerçek araca dağıtım veya komut gönderilmedi. Gerçek PWM değerleri, kamera ofseti (merkezleme için), saha rotası ve alan/giriş/bitiş koordinatları tamamlanmadan fiziksel uçuş profili hazır değildir. Parametrelerin ve RC failsafe davranışının sahada doğrulanması ayrıca gerekir.
# 8 Eylül — sonsuz odak ve eski dama verisi incelemesi

Son kamera profil düzenlemesinde 98 ilgili yerel test geçti. 40 özgün dama karesinin hashleri eşleşti; yeniden çözüm RMS 0,1338 px, önceki aday 0,1388 px. Matrisler yakın ancak birebir değil; odak uzunluğu farkları %0,04/%0,06. Özgün matris korunup kullanıcı talebiyle sonsuz odak için yaklaşık kopyası kullanıldı; odak aktarımı fiziksel olarak doğrulanmadı.

Pi'de iki ayrı 20 saniyelik kamera/Hailo/OpenCV/JPEG testi: ana 895 işlenmiş kare / 49,86 FPS, hızlı 968 / 50,03 FPS; iki akışta manuel LensPosition=0, tam IMX708 crop, uygulama hatası yok. MAVLink açılmadı. Yakın parçalar görüşü kaplıyor; gerçek hedef/PnP yükü/uzak netlik testi değildir. Kanıt `artifacts/camera-review-20260908/`; önceki test sayıları aşağıda kendi revizyonlarına aittir.
