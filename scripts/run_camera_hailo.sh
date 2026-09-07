#!/usr/bin/env bash
set -eo pipefail
cd /home/furkan/Documents/proje/hailo-rpi5-examples
source ./setup_env.sh
export HAILO_ENV_FILE="$PWD/.env"
cd /home/furkan/Desktop/safak-gorev2-quad
export PYTHONPATH="$PWD/runtime/python:$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec python scripts/camera_hailo_panel.py
