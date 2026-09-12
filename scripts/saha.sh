#!/usr/bin/env bash
# Saha işletim sırası. Pi'de tek giriş noktası: her adım aynı ortamı kurar,
# çakışan süreçleri kontrol eder ve ne yaptığını yazar.
#
#   bash scripts/saha.sh durum     FC/profil/süreçleri oku, hiçbir şey başlatma
#   bash scripts/saha.sh rota      Mission Planner'da rota DEĞİŞTİYSE digest yaz
#   bash scripts/saha.sh kontrol   uçuş öncesi tam kapı (--check)
#   bash scripts/saha.sh ucus      görevi başlat (--mode flight)
#   bash scripts/saha.sh gozlem    kamera/tespit bak, uçuş yok (--mode observe)
#   bash scripts/saha.sh rapor     iniş sonrası uçuş raporu + PnP teşhisi
#   bash scripts/saha.sh test      Pi'de testleri çalıştır
set -euo pipefail

HAILO_ENV="${HAILO_ENV:-/home/furkan/Documents/proje/hailo-rpi5-examples/setup_env.sh}"
PROJE="${PROJE:-/home/furkan/Desktop/safak-gorev2-quad}"
PROFIL="${PROFIL:-config/ana-imx708.json}"

adim=${1:-}
[ -n "$adim" ] || { sed -n '2,11p' "$0" | sed 's/^# \?//'; exit 2; }

# --- ortam: her adımda aynı, elle kurmaya gerek yok ---------------------------
[ -f "$HAILO_ENV" ] || { echo "HATA: Hailo ortamı yok: $HAILO_ENV"; exit 1; }
# shellcheck disable=SC1090
cd "$(dirname "$HAILO_ENV")" && source "$(basename "$HAILO_ENV")" >/dev/null
cd "$PROJE"
export PYTHONPATH="$PWD/runtime/python:$PWD:${PYTHONPATH:-}"
export MAVLINK20=1
echo "ortam: $(python -V 2>&1)  proje: $PWD  profil: $PROFIL"

# --- FC portunu iki süreç birden açamaz --------------------------------------
gorev_calisiyor() { pgrep -af 'competition\.main' >/dev/null 2>&1; }
port_bos_ister() {
  if gorev_calisiyor; then
    echo
    echo "DURDURULDU: görev süreci çalışıyor, '$adim' Pixhawk portunu ikinci"
    echo "kez açardı ve canlı MAVLink bağlantısı düşerdi."
    pgrep -af 'competition\.main' | sed 's/^/  /'
    echo "Önce görevi Ctrl+C ile kapat, sonra tekrar dene."
    exit 1
  fi
}

case "$adim" in
  durum)
    echo "--- süreçler ---"
    pgrep -af 'competition\.main|safak_gorev2\.record' | sed 's/^/  /' || echo "  yok"
    echo "--- profilde kritik alanlar ---"
    python - "$PROFIL" <<'PY'
import sys
from safak_gorev2.competition.config import Options
# Gercek yukleyici: base_config'i cozer, kod varsayilanlarini uygular ve
# dogrular. Yani bu adim ayni zamanda profilin gecerliligini de kanitlar.
cfg, opt = Options.load(sys.argv[1])
cfg.validate()
c = cfg.control
for k in ('sortie_id','search_start_seq','search_end_seq','center_search_speed_mps',
          'search_laps','mission_deadline_s','intercept_deadline_s'):
    print(f"  {k:26} {getattr(opt, k, None)}")
print(f"  {'mission_fingerprint':26} {str(getattr(opt,'mission_fingerprint',None))[:16]}...")
for k in ('max_descent_mps','max_accel_mps2','max_climb_mps','kp_height',
          'target_camera_height_m','height_tolerance_m','minimum_camera_height_m'):
    print(f"  {k:26} {getattr(c, k)}")
print(f"  alcalma kurali             kp*v={c.kp_height*c.max_descent_mps:.3f} <= accel={c.max_accel_mps2}"
      f"  | durma={c.max_descent_mps**2/(2*c.max_accel_mps2):.2f} m <= pencere={c.height_tolerance_m} m")
print(f"  takip                      enabled={opt.tracking.enabled} debug={opt.tracking.debug}")
print("  profil DOGRULANDI")
PY
    ;;
  rota)
    port_bos_ister
    echo ">>> rota digest'i ve tarama kapsamı profile yazılıyor"
    python scripts/route_digest.py --write "$PROFIL"
    ;;
  kontrol)
    port_bos_ister
    echo ">>> uçuş kapısı: tam başarı satırı görülmeden ARM/AUTO yok"
    python -m safak_gorev2.competition.main --config "$PROFIL" --check
    ;;
  ucus)
    port_bos_ister
    echo ">>> görev başlıyor. İKİNCİ UÇUŞ İÇİN BU SÜRECİ YENİDEN BAŞLAT."
    python -m safak_gorev2.competition.main --config "$PROFIL" --mode flight
    ;;
  gozlem)
    port_bos_ister
    echo ">>> gözlem: kamera ve tespit açık, uçuş komutu üretilmez"
    python -m safak_gorev2.competition.main --config "$PROFIL" --mode observe
    ;;
  rapor)
    echo ">>> uçuş raporu"; python scripts/ucus_raporu.py
    echo; echo ">>> PnP teşhisi"; python scripts/pnp_teshis.py
    ;;
  test)
    python -m pytest tests/ -q
    ;;
  *)
    echo "bilinmeyen adım: $adim"; sed -n '2,11p' "$0" | sed 's/^# \?//'; exit 2 ;;
esac
