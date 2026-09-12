# Zaman eksenli hedef takibi — 12 Eylül 2026

Hızlı uçuşta, ani yaw/pitch/roll'da ve motion blur'da OpenCV renk/dörtgen
araması bazı kareleri kaçırıyordu. Sistem kare-kare çalıştığı için tek kötü
kare etiketi düşürüyor ve biriken tarama kanıtını sıfırlıyordu. Bu revizyon
kısa boşlukları **zaman eksenli bir izle** köprüler; uzun kayıpta hedefi
gerçekten bırakır.

## Temel kural: tahmin uçuş kanıtı değildir

Köprülenen aday `source='tracked'`, `color_verified=False`, `color_fill=None`,
`metric=None` taşır. Mevcut `corroborated` koşulu bunları **duruş sonrası
doğrulama, merkezleme ve yük bırakma yollarından zaten eler**; o yollarda tek
kanıt hâlâ taze OpenCV renk/dörtgen ölçümüdür. Gerçek tespitin `bbox` alanına
dokunulmaz: PnP, köşe ölçümü ve kutu eşleştirmesi ham ölçümü görmeye devam
eder, süzgeç sonucu ayrı `filtered_bbox` alanında yalnız etiket/teşhis için
taşınır. Bu, `MOSSE_DEGERLENDIRME.md` içindeki "tahmini takip tek başına
alçalma/bırakma yetkisi vermemeli" kararının doğrudan uygulanmasıdır.

## Neden Kalman, neden MOSSE/KCF/CSRT değil

Tespiti düşüren şey işlem bütçesi değil, karenin kendisidir (blur, parlama).
Aynı bozuk piksellere korelasyon takipçisi salmak bilgi eklemez; MOSSE ayrıca
`cv2.legacy` (opencv-contrib) ister ve Pi'deki kurulumda yoktur, gri dönüşüm
ve kare kopyası getirir. Bunun yerine **iyi karelerden** öğrenilen sabit hızlı
hareket modeli kullanılır:

- Merkez x ve y için iki bağımsız sabit hızlı Kalman süzgeci (ölçüm = konum).
- Kutu genişlik/yüksekliği için üstel hareketli ortalama (EMA).
- Her gerçek tespitte düzeltme (`correct`) yapılır; sürüklenme birikmez.
- Görüntüye erişilmez, kare kopyalanmaz, model yüklenmez.

Ölçülen maliyet: **2 renk × 3 aday için kare başına ~17 µs** (Mac, 5000 kare).
50 FPS'de kare bütçesi 20 ms; renk/vision aşaması ortanca 3,67 ms. Takip
katmanı bu bütçenin binde birinden azını kullanır.

## Döner kanat farkı

Albatros sabit kanatlıdır; "hedefe yaklaş → geç → uzaklaşınca en iyi
detection'ı kilitle" (`worse_streak`, `DETECTION_TRACK_MAX_SEC`) mantığı
oradan **alınmadı**. Bizim araç hover yapabilir, geri gidebilir, yana
kayabilir, yaw ile hedef etrafında dönebilir. Bu yüzden iz yön/mesafe
varsayımı taşımaz: yalnız son gözlemlerden kestirilen hız ve fiziksel olarak
ulaşılabilir kayma sınırı kullanılır. Albatros'tan alınan fikirler: kısa
boşluk köprüleme, her gerçek tespitte yeniden tohumlama, sabit köprü
penceresi ve saha günü için tek kelimelik kapatma anahtarı.

## Durum makinesi

| Durum | Anlamı | Köprü kutusu |
|---|---|---|
| `CANDIDATE` | Yeni tespit; `confirmation_frames` henüz dolmadı | yok |
| `DETECTED` | Bu karede gerçek OpenCV tespiti var | yok (gerek yok) |
| `TRACKED` | Gerçek tespit yok, kestirim sürüyor | **var** |
| `TEMPORARILY_LOST` | Köprü penceresi doldu, iz hafızası duruyor | yok |
| `LOST` | Kayıp penceresi doldu; iz bırakıldı | yok |

`LOST` sonrası hedef sıfırdan `confirmation_frames` kadar gerçek tespitle
yeniden doğrulanır. Eski etiket sonsuza kadar ekranda kalmaz. Kestirim
kadrajı terk ederse köprü hemen kesilir (`TEMPORARILY_LOST`).

## Denetleyiciye tek dokunuş

`DualController.step()` içinde yalnız **SEARCHING** dalı değişti:

```
Eskiden: bu karede aday yoksa  -> holds[renk].reset(), boxes.pop(renk)
Şimdi:   bu karede aday yoksa ama köprü kutusu varsa
         -> boxes[renk] = köprü kutusu, kare atlanır
         (sayaç ne sıfırlanır ne ARTAR)
```

Yani biriken tarama kanıtı tek kötü karede silinmez, ama gereken bağımsız kare
sayısı (`quick_frames`) yine **yalnız gerçek tespitlerden** gelir. Süreklilik
bundan sonra `ContinuousHold`'un kendi boşluk sınırıyla
(`control.max_lock_frame_gap_s = 0,25 s`) korunur; sonsuza kadar değil.

`STOPPING`, `VERIFYING`, `INTERCEPT`, `RELEASE_WAIT` dalları **hiç
değişmedi**. `fresh_candidates()` da değişmedi; köprülenen adaylar ayrı
`bridged_candidates()` süzgecinden geçer ve yalnız bu tek noktada kullanılır.

## Aday skoru

İz yokken skor ham renk doluluğudur; sıralama bugünküyle birebir aynıdır. İz
varken skor `fill_weight*doluluk + (1-fill_weight)*süreklilik` olur;
süreklilik = kestirime yakınlık × alan tutarlılığı. Böylece birden çok aday
arasından zamanla tutarlı olan seçilir. Fiziksel olarak imkânsız sıçrama
(`max_jump + max_jump_rate*dt` üstü) yapan ölçüm **izle ilişkilendirilmez**:
süzgeci bozmaz, köprüyü tazelemez. Aday listeden atılmaz — gerçek hedefin
sert bir yaw'dan sonra sessizce yok sayılmaması için — ama denetleyicinin
mevcut IoU eşleştirmesi onu zaten eler.

## Yapılandırma

`config/ana-gorev.json` ve `config/hizli-gorev.json` içinde `tracking` bloğu.
**`"enabled": false` yazmak sistemi anında eski davranışa döndürür.**
Kod varsayılanı `enabled=false`'tur; yalnız bu iki saha profili açar.

| Alan | Saha değeri | Anlamı |
|---|---|---|
| `enabled` | `true` | Takip katmanı. `false` = eski akış, bit bit aynı. |
| `debug` | `false` | Panel üstü teşhis metni + terminalde durum geçişi. |
| `confirmation_frames` | 2 | Köprülemeden önce istenen gerçek tespit sayısı. |
| `max_tracking_frames` | 3 | Tahminle köprülenen en fazla ardışık kare (50 FPS'de 60 ms). |
| `max_missed_frames` | 8 | Bu kareden sonra iz tamamen bırakılır (50 FPS'de 160 ms). |
| `history_size` | 8 | Tutulan son gerçek tespit kaydı. |
| `max_gap_s` | 0,25 | İki kare arası en büyük boşluk; aşılırsa iz sıfırlanır. |
| `bridge_search` | `true` | Köprülenen kare tarama sayacını sıfırlamasın. |

Koddaki diğer varsayılanlar (`competition/config.py`): `smoothing_alpha=0,45`,
`measurement_noise=0,004` (normalize; 1280 pikselde ~5 px),
`process_accel=8,0` kare genişliği/s², `max_jump=0,12`, `max_jump_rate=3,0`
kare genişliği/s, `min_score=0,0`, `fill_weight=0,6`. Hepsi profil JSON'undan
geçersiz kılınabilir ve `Tracking.validate()` ile sınırlanır.

`max_jump_rate=3,0` gerekçesi: 5 m irtifada ~60° yatay görüş açısıyla kadraj
genişliği ~5,8 m; 5 m/s yatay hız ≈ 0,86 kare/s, 90°/s yaw ≈ 1,5 kare/s.
3,0 kare/s ikisinin toplamının üstünde bir paydır.

## Debug

`"debug": true` yapıldığında:

- Panel kutusunun altında iki satır: durum (`DETECTION` / `TRACKING` /
  `ADAY` / `TEMP LOST` / `LOST`), `kacan=`, `skor=`, `ham=(x,y)`,
  `suzulmus=(x,y)`.
- Alt bilgi şeridinde `TAKIP ACIK/KAPALI / <ms> / kopru<=N kare`.
- Terminalde her durum geçişi: `[TAKIP] kare 512 mavi: DETECTED -> TRACKED`.

`false` iken hiçbiri yazılmaz. Köprülenen kutu debug kapalıyken de çizilir —
ama her zaman **turuncu ve `TAKIP <renk>`** etiketiyle, gerçek tespitin
camgöbeği `AKTIF HEDEF` etiketinden ayırt edilebilsin diye.

Kayıtlar: `competition-<sortie>.jsonl` içindeki her aday artık `track_state`,
`score`, `missed`, `filtered_bbox` taşır; kare kaydında `tracking_ms` vardır.

## Sınırlar

- Bu bir çoklu hedef kimlik yöneticisi değildir: renk başına tek iz tutulur.
- Köprüleme yalnız kısa OpenCV boşluğunu tolere eder; kapalı/bozuk kamerayı,
  yanlış renk eşiğini veya odak sorununu onarmaz.
- Gerçek saha görüntüsüyle blur toleransı henüz ölçülmedi; aşağıdaki kanıt
  sentetik görüntü ve SITL'dir, uçuş kabulü değildir.

---

# Tarama turu ve görev süresi — 12 Eylül 2026

## Görev süresi (10 dakikalık yarışma penceresi)

Sayaç **AUTO devralma anından** (`self.started_at`, pratikte AUTO kalkış)
başlar. İki sınır vardır:

| Ayar | Saha değeri | Ne yapar |
|---|---|---|
| `mission_deadline_s` | 510 (8:30) | Yarım kalan merkezleme/alçalma/tur dahil **her iş bırakılır**, LAND waypointine gidilir. |
| `intercept_deadline_s` | 450 (7:30) | Bu andan sonra **yeni** hedefe durulmaz; başlamış iş sürer. |
| `search_laps` | 3 | Tarama bölümü en çok bu kadar kez uçulur. |

`null` yazmak ilgili sınırı kapatır. Kod varsayılanları `search_laps=1`,
iki süre de `None` — yani eski davranış. `search_laps > 1` iken
`mission_deadline_s` **zorunludur**; aksi halde profil reddedilir. Tur sayısı
tek başına bir güvenlik ağı değildir, süre sınırı esas koruyucudur.

**Dikkat:** sayaç bizim gördüğümüz AUTO kalkıştan başlar. Yarışma saatin
daha erken başlıyorsa (hakem işareti, ARM anı) 510'u o farkı çıkararak azalt.

Süre dolduğunda akış: `TIME_LAND_CLAIM` (AUTO iken GUIDED istenir) →
`SELECT_LAND` → `HANDOFF_LAND` → `LANDING`. Kontrol zaten bizdeyse
(merkezleme/alçalma sürüyorsa) doğrudan `SELECT_LAND`'e geçilir.
`RELEASE_WAIT` hariç tutulur: yük komutu en fazla `release_ack_timeout_s`
içinde sonuçlanır ve sonucu deftere yazılmalıdır; süre sonu bir sonraki
adımda devreye girer.

## Tarama turunu başa sarma

Tarama bölümü bitip (`mission_seq > search_end_seq`) takılı yüklerden biri
hâlâ duruyorsa, AUTO'nun bitiş/LAND rotasına bırakmak yerine:

`RELAP_CLAIM` (claim + GUIDED) → `RESUME_SELECT` (mission_set_current →
`search_start_seq`) → `RESUME_AUTO` → `SEARCHING`.

`RESUME_SELECT`/`RESUME_AUTO` mevcut, denenmiş yol; yalnız girişi yeni.
`route.finished` GUIDED'deyken sıfırlanır, böylece ikinci tur için tarama ve
yük izni geri gelir. Yük komutu verilmiş renkler `requested` içinde kaldığı
için ikinci kez denenmez.

## Doğrulama

* 408 yerel test geçti / 5 atlandı (öncesi 387/5). Yeni
  `tests/test_lap_and_deadline.py` 21 test.
* Süre sonu SITL'de uçtu: 40 s sınırla `SEARCHING` → `TIME_LAND_CLAIM` →
  `HANDOFF_LAND` → `LANDING` → `INCOMPLETE`, yük komutu 0.
* Ana görev tam senaryosu süre sınırı ve 3 tur açıkken **DONE**, iki yük.
* **Tur başa sarma SITL'de sınanamadı.** SITL rotasında `search_end_seq`
  zorunlu olarak `land_seq-1` olduğu için tarama biter bitmez araç LAND
  kalemine geçiyor ve kayıt penceresi kapanıyor. Bunun yerine birim testler
  tüm zinciri, ayrıca iki test komutun gerçekten MAVLink'e
  (`mission_set_current_send`) ulaştığını doğruluyor. Gerçek uçuşta bu yolun
  ilk kanıtı alınmadı.
* Birim test, `RELAP_CLAIM` sırasında AUTO modunun izinli modlar arasında
  olmamasından doğan gerçek bir hatayı yakaladı (uçuşta pilot müdahalesi
  sanılıp iptal ederdi); düzeltildi.
