"""Yer istasyonu bağlantısının ölçülmesi.

Panelin kendi ürettiği HTTP yükü ile arayüzün toplam yükü ayrı ayrı sayılır:
panel 4 FPS/Q35'te yaklaşık 0,4 Mbit/s'tir, arayüz bunun çok üstünde veri
taşıyorsa darboğaz paneli değil aynı WiFi'yi paylaşan başka bir akıştır
(NoMachine/VNC uzak masaüstü, rsync, güncelleme). Ölçüm salt okunurdur;
hiçbir servisi kapatmaz, kendi başına uçuş kabulü değildir.
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from pathlib import Path

# Uzak masaüstü/ekran paylaşımı: saha linkini paylaşan bilinen ağır akışlar.
CLIENT_TTL_S = 300.
HEAVY_STREAM_PROCESSES = ("nxserver", "nxnode", "nxexec", "x11vnc", "vncserver",
                          "wayvnc", "rustdesk", "anydesk", "teamviewerd")


def _read(path: Path) -> str | None:
    try:
        return path.read_text()
    except OSError:
        return None


def wireless_signal(root: Path = Path("/")) -> dict | None:
    """/proc/net/wireless: sinyal dBm ve biriken retry/misc sayaçları."""
    text = _read(root / "proc/net/wireless")
    if not text:
        return None
    for line in text.splitlines()[2:]:
        name, _, rest = line.partition(":")
        fields = rest.split()
        if not name.strip() or len(fields) < 9:
            continue
        try:
            return {"interface": name.strip(),
                    "quality": float(fields[1].rstrip(".")),
                    "signal_dbm": float(fields[2].rstrip(".")),
                    "retry": int(fields[7]), "misc": int(fields[8])}
        except ValueError:
            continue
    return None


def interface_bytes(interface: str, root: Path = Path("/")) -> tuple[int, int] | None:
    base = root / "sys/class/net" / interface / "statistics"
    rx, tx = _read(base / "rx_bytes"), _read(base / "tx_bytes")
    if rx is None or tx is None:
        return None
    try:
        return int(rx), int(tx)
    except ValueError:
        return None


def heavy_stream_processes(root: Path = Path("/")) -> list[str]:
    """Aynı linki paylaşan uzak masaüstü süreçleri; yalnız isim listesi döner."""
    found = []
    proc = root / "proc"
    try:
        entries = sorted(proc.iterdir())
    except OSError:
        return found
    for entry in entries:
        if not entry.name.isdigit():
            continue
        comm = (_read(entry / "comm") or "").strip().lower()
        if not comm:
            continue
        for known in HEAVY_STREAM_PROCESSES:
            if known in comm and known not in found:
                found.append(known)
    return found


class LinkHealth:
    """Panel isteklerini ve arayüz yükünü kayan pencerede sayar."""

    def __init__(self, window_s: float = 20., root: Path = Path("/"), clock=time.monotonic):
        self.window_s = window_s
        self.root = Path(root)
        self.clock = clock
        self.lock = threading.Lock()
        self.created = clock()
        self.requests: deque = deque()
        self.clients: dict[str, dict] = {}
        self._wifi: dict | None = None
        self._wifi_at = -math.inf
        self._counters: tuple[float, int, int] | None = None
        self._interface_bps: dict | None = None

    def record(self, client: str | None, path: str, status: int, size: int, seconds: float) -> None:
        now = self.clock()
        with self.lock:
            self.requests.append((now, int(size), float(seconds), status))
            self._trim(now)
            entry = self.clients.setdefault(client or "?", {"requests": 0, "bytes": 0, "errors": 0,
                                                            "last_at": now, "slowest_ms": 0.})
            entry["requests"] += 1
            entry["bytes"] += int(size)
            entry["last_at"] = now
            entry["slowest_ms"] = max(entry["slowest_ms"], seconds * 1000)
            if status >= 500:
                entry["errors"] += 1

    def _trim(self, now: float) -> None:
        while self.requests and now - self.requests[0][0] > self.window_s:
            self.requests.popleft()
        # Uzun oturumda ayrılmış istemciler sayımda birikmesin.
        for name in [n for n, entry in self.clients.items() if now - entry["last_at"] > CLIENT_TTL_S]:
            del self.clients[name]

    def sample_interface(self) -> None:
        """1 Hz'de çağrılır: sinyal ve arayüzün toplam bayt hızını günceller."""
        now = self.clock()
        wifi = wireless_signal(self.root)
        counters = interface_bytes(wifi["interface"], self.root) if wifi else None
        with self.lock:
            self._wifi, self._wifi_at = wifi, now if wifi else self._wifi_at
            if counters and self._counters:
                previous_at, rx, tx = self._counters
                span = now - previous_at
                if span > 0 and counters[0] >= rx and counters[1] >= tx:
                    self._interface_bps = {"rx_bps": (counters[0] - rx) * 8 / span,
                                           "tx_bps": (counters[1] - tx) * 8 / span,
                                           "span_s": span}
            if counters:
                self._counters = (now, counters[0], counters[1])

    def snapshot(self) -> dict:
        now = self.clock()
        with self.lock:
            self._trim(now)
            window = list(self.requests)
            wifi = dict(self._wifi) if self._wifi else None
            interface = dict(self._interface_bps) if self._interface_bps else None
            clients = {name: {**entry, "idle_s": now - entry["last_at"]}
                       for name, entry in self.clients.items()}
        # Hız her zaman gözlem penceresine bölünür; tek yeni istek anlık
        # bölmeyle megabitlik sahte bir değer üretmesin.
        span = max(1., min(self.window_s, now - self.created))
        served_bps = sum(item[1] for item in window) * 8 / span
        slowest = max((item[2] for item in window), default=0.)
        panel_share = None
        if interface and interface["tx_bps"] > 0:
            panel_share = min(1., served_bps / interface["tx_bps"])
        return {"window_s": self.window_s, "requests": len(window),
                "served_bps": served_bps, "slowest_response_ms": slowest * 1000,
                "wifi": wifi, "interface": interface, "panel_share_of_tx": panel_share,
                "clients": clients}
