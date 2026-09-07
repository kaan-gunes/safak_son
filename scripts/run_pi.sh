#!/usr/bin/env bash
# Mevcut Hailo ortamını kullanır; ortamı ve Pixhawk parametrelerini değiştirmez.
set -eo pipefail
if [ "$#" -lt 1 ]; then
  echo "Kullanım: bash scripts/run_pi.sh /tam/yol/setup_env.sh [--mode observe|flight] [--config config/flight.local.json]" >&2
  exit 2
fi
SAFAK_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAFAK_ENV_SCRIPT="$1"
shift
if [ ! -f "$SAFAK_ENV_SCRIPT" ]; then
  echo "Hailo ortam betiği bulunamadı: $SAFAK_ENV_SCRIPT" >&2
  exit 2
fi
SAFAK_ENV_DIR="$(cd "$(dirname "$SAFAK_ENV_SCRIPT")" && pwd)"
SAFAK_ENV_NAME="$(basename "$SAFAK_ENV_SCRIPT")"
cd "$SAFAK_ENV_DIR"
source "./$SAFAK_ENV_NAME"
if [ -f "$SAFAK_ENV_DIR/.env" ]; then
  export HAILO_ENV_FILE="$SAFAK_ENV_DIR/.env"
fi
cd "$SAFAK_PROJECT_DIR"
export PYTHONPATH="$SAFAK_PROJECT_DIR/runtime/python:$SAFAK_PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec python -m safak_gorev2.main "$@"
