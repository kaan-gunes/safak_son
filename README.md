# ŞAFAK

Raspberry Pi üzerinde Python 3.11+ ile:

```bash
sudo apt install python3-venv python3-picamera2 python3-opencv
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e .
```

Gözlem (uçuş komutu göndermez):

```bash
bash scripts/saha.sh gozlem
```

Ana görev:

```bash
bash scripts/saha.sh kontrol
bash scripts/saha.sh ucus
```

Panel: `http://<PI_IP>:8081/competition`
