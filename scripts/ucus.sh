#!/usr/bin/env bash
# Tek komutluk saha akisi. Ortami kurar, canli rotayi profile yazar, ayarlari
# ve servolari dogrular, yeni sortie kimligi uretir, gorevi baslatir.
# Herhangi bir adim basarisiz olursa DURUR ve sebebini yazar.
#
#   safak            tam akis (rota dogrulama + kontrol + ucus)
#   safak rapor      inis sonrasi ucus raporu + GPS teshisi
#   safak servo      yalniz servo incelemesi (salt okunur)
#   safak durum      yalniz ayarlari goster, FC'ye dokunma
#   safak guncelle   son kodu GitHub'dan cek ve testleri calistir
set -uo pipefail

HAILO_ENV=${HAILO_ENV:-/home/furkan/Documents/proje/hailo-rpi5-examples/setup_env.sh}
PROJE=${PROJE:-/home/furkan/Desktop/safak-gorev2-quad}
PROFIL=${PROFIL:-config/ana-imx708.json}
DAL=${DAL:-hedef-takibi}
HAM=https://raw.githubusercontent.com/kaan-gunes/safak_son/$DAL

dur() { echo; echo "############ DURDURULDU ############"; echo "$*"; echo; exit 1; }
baslik() { echo; echo "--- $* ---"; }

# ---- ortam ----------------------------------------------------------------
# setup_env.sh bazi kontrollerde `exit` cagiriyor. Source edilen bir dosyadaki
# exit bu betigi de oldurur -- ciktisi bastirilmissa sessizce, kod 1 ile.
# O yuzden setup_env.sh source EDILMEZ; yaptigi iki sey dogrudan yapilir:
# Hailo venv'ini etkinlestirmek ve hailo klasorunu PYTHONPATH'e eklemek.
HAILO_DIR=$(dirname "$HAILO_ENV")
VENV=""
for aday in "$HAILO_DIR"/venv_hailo_rpi_examples/bin/activate \
            "$HAILO_DIR"/venv/bin/activate \
            "$HAILO_DIR"/.venv/bin/activate; do
  [ -f "$aday" ] && { VENV=$aday; break; }
done
[ -n "$VENV" ] || dur "Hailo sanal ortami bulunamadi.
Arandi:
  $HAILO_DIR/venv_hailo_rpi_examples/bin/activate
  $HAILO_DIR/venv/bin/activate
  $HAILO_DIR/.venv/bin/activate
Dogru yolu HAILO_ENV ile ver:  HAILO_ENV=/yol/setup_env.sh safak"
# shellcheck disable=SC1090
source "$VENV" || dur "Sanal ortam etkinlestirilemedi: $VENV"
export PYTHONPATH="$HAILO_DIR:${PYTHONPATH:-}"
cd "$PROJE" || dur "Proje klasoru bulunamadi: $PROJE"
export PYTHONPATH="$PWD/runtime/python:$PWD:$PYTHONPATH"
export MAVLINK20=1
python -c "import pymavlink, cv2" 2>/dev/null \
  || dur "Sanal ortam eksik: pymavlink/cv2 yuklenemedi ($VENV).
Elle dene:  source $VENV && python -c 'import pymavlink, cv2'" 

adim=${1:-ucus}

ayarlari_goster() {
  python - "$PROFIL" <<'PY' || return 1
import sys
from safak_gorev2.competition.config import Options
cfg, o = Options.load(sys.argv[1])
cfg.validate()
c = cfg.control
print(f"  sortie      : {o.sortie_id}")
print(f"  rota izi    : {str(o.mission_fingerprint)[:16]}...")
print(f"  tarama      : seq {o.search_start_seq}..{o.search_end_seq}   "
      f"{o.center_search_speed_mps} m/s   tur={o.search_laps}")
print(f"  sure        : gorev {o.mission_deadline_s} s / yeni hedef {o.intercept_deadline_s} s")
print(f"  alcalma     : {c.max_descent_mps} m/s   ivme {c.max_accel_mps2}   "
      f"birakma {c.target_camera_height_m} m")
print(f"  gps payi    : {o.gps_grace_s} s")
print(f"  servo tutma : {o.hold_servos_at_startup}")
print(f"  takip       : {o.tracking.enabled}")
print("  PROFIL GECERLI")
PY
}

case "$adim" in
  durum)
    baslik "AYARLAR"; ayarlari_goster || dur "Profil gecersiz."
    exit 0 ;;

  guncelle)
    baslik "GUNCELLEME"
    for f in safak_gorev2/competition/config.py safak_gorev2/competition/controller.py \
             safak_gorev2/competition/link.py safak_gorev2/competition/runtime.py \
             safak_gorev2/competition/route.py safak_gorev2/config.py \
             scripts/route_digest.py scripts/ucus_raporu.py scripts/gps_teshis.py \
             scripts/servo_teshis.py scripts/kilit_teshis.py scripts/ucus.sh \
             tests/test_competition.py tests/test_gps_grace.py tests/test_servo_hold.py; do
      curl -fsSL -o "$f" "$HAM/$f" && echo "  $f" || echo "  ATLANDI: $f"
    done
    chmod +x scripts/ucus.sh
    baslik "TESTLER"
    python -m pytest tests/ -q || dur "Testler gecmedi. Ucma, ciktiyi Claude'a yolla."
    echo; echo "Guncelleme tamam."
    exit 0 ;;

  rapor)
    baslik "UCUS RAPORU"; python scripts/ucus_raporu.py
    baslik "GPS TESHISI"; python scripts/gps_teshis.py
    exit 0 ;;

  servo)
    pgrep -af 'competition\.main' >/dev/null && dur "Gorev sureci calisiyor; servo incelemesi FC portunu ikinci kez acar. Once Ctrl+C."
    python scripts/servo_teshis.py
    exit $? ;;

  ucus) ;;
  *) dur "Bilinmeyen adim: $adim   (ucus | rapor | servo | durum | guncelle)" ;;
esac

# =========================== TAM AKIS ======================================
echo "====================================================================="
echo " SAFAK saha akisi   profil: $PROFIL"
echo " $(python -V 2>&1)   klasor: $PWD"
echo "====================================================================="

baslik "1/5  Calisan gorev sureci var mi"
if pgrep -af 'competition\.main' >/dev/null; then
  pgrep -af 'competition\.main' | sed 's/^/  /'
  dur "Gorev sureci zaten calisiyor. Once onu Ctrl+C ile kapat."
fi
echo "  temiz"

baslik "2/5  Canli rota okunuyor ve profile yaziliyor"
echo "  (arac DISARM olmali; Mission Planner'da rotayi YAZDIGINDAN emin ol)"
python scripts/route_digest.py --write "$PROFIL" || \
  dur "Rota okunamadi/yazilamadi. Arac DISARM mi? Mission Planner rotayi FC'ye yazdi mi?"
echo
echo "  >> Yukarida 'search_start_seq' satiri VARSA dur ve Claude'a soyle."

baslik "3/5  Ayarlar"
ayarlari_goster || dur "Profil gecersiz."

baslik "4/5  Servolar (salt okunur)"
if ! python scripts/servo_teshis.py; then
  dur "Servo birakma tarafinda. Kumandada o kanalin kolunu diger uca al, tekrar dene."
fi

baslik "5/5  Yeni sortie kimligi"
python - "$PROFIL" <<'PY' || dur "sortie_id yazilamadi."
import datetime, json, pathlib, sys
p = pathlib.Path(sys.argv[1])
d = json.loads(p.read_text())
d['sortie_id'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-ana-imx708'
p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n')
print('  '+d['sortie_id'])
PY

echo
echo "====================================================================="
echo " HER SEY HAZIR. Gorev baslatiliyor."
echo " Tam basari satirini GORMEDEN ARM/AUTO yapma."
echo " Panel: http://172.20.10.6:8081   (uydu >= 12, HDOP <= 1.0 bekle)"
echo " Inis sonrasi:  safak rapor"
echo "====================================================================="
echo
exec python -m safak_gorev2.competition.main --config "$PROFIL" --mode flight
