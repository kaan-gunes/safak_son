# Çalışma profilleri

- `ana-gorev.json` → `competition-base.json`: merkezleme ve alçalmalı görev.
- `hizli-gorev.json` → `hizli-base.json`: dur/doğrula, aynı irtifada bırak.
- İkisi 50 FPS, IMX708 tam sensör modu ve manuel sonsuz odak (0) ister.
- Ana `camera.imx708-infinity-approx.json` kullanır: eski 0,1063 odaklı dama matrisinin sonsuz odağa doğrulanmamış aktarımı. Özgün `camera.imx708-candidate.json` korunur.
- `camera.field-candidate.json` eski IMX219 verisidir; güncel iki görev kullanmaz. Analiz ve geçmiş kanıt için korunur.
- `analysis-tools.json` uçuş seçeneği değildir.

Rota, yük oturumu ve fiziksel servo değerleri sahada tamamlanır. [Teknik kontrol rehberi](../TEKNIK_KONTROL.md).

11 Eylül: `ana-imx708.json` ve `ana-arducam.json` aynı center akışının ayrı kamera profilleridir. Arducam temeli `ana-arducam-base.json`; `camera.arducam-unverified.json` kabul eksikliği kaydıdır, kalibrasyon değildir. [Ayrıntı](../docs/competition/IKI_KAMERA_KABUL.md).
