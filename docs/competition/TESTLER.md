# Doğrulama — 7 Eylül 2026

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
