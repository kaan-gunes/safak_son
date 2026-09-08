# Eski görev seçenekleri — arşiv, çalıştırma menüsü değil

Kullanıcının “üç eski seçeneği kaldır, ana görev ve MOSSE'siz hızlı görev kalsın” isteğiyle taşındı.

- Yalnız mavi quad: eski `safak_gorev2.main` girişinin ve saha profillerinin özgün kopyaları `.txt` olarak burada. Aktif giriş donanım açmadan hata verir.
- Eski iki renkli merkezleme: `previous-dual/` altında önceki git sürümünün kaynak kopyaları. Güncel dur–doğrula ana akışı `config/ana-gorev.json` ile devam eder.
- Durmadan görünce bırakma (`sighting`): profil burada arşivlendi, aktif strateji koddan kaldırıldı. Yerine `config/hizli-gorev.json` gelir; o durmadan bırakmaz.

`manifest.json` taşınan dosyaların SHA256 değerlerini içerir. `preserved-paths.json`, önceki koruma manifestosundaki değiştirilen/taşınan dosyaların özgün kopyalarının konumudur. Merkezleme/geometri gibi iki güncel görev tarafından kullanılan ortak kod silinmedi. `config/analysis-tools.json` eski kayıt analizi/kalibrasyon araçları için veri profilidir, görev seçeneği değildir.

Buradaki dosyalar çalıştırılmak için düzenlenmedi; eski profil yolları artık geçerli değildir. Pi üzerinde bu temizlik henüz uygulanmadı.
