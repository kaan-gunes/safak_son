# Doğrulama — 7 Eylül 2026

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
