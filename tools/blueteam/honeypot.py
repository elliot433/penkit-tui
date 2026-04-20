"""
Multi-port honeypot that simulates common services to catch port-scanners
and attackers probing your network.

Fake services:
  - SSH (port 2222 default, pretends to be OpenSSH 7.4)
  - HTTP (port 8888, fake Apache login page)
  - FTP (port 2121, accepts anonymous then logs)
  - Telnet (port 2323, fake router login)

Every connection is logged with: timestamp, src IP, src port, banner/data sent.
Configurable alert threshold: N connections from same IP → alert.
"""

import asyncio
import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Honeypot Suite",
    description=(
        "Runs fake SSH, HTTP, FTP, and Telnet services that log every connection attempt. "
        "Detects port scanners, brute-force bots, and targeted attackers. "
        "Configurable alert threshold per source IP."
    ),
    usage="Choose which services to enable and on which ports. All listeners are fake — no real service is exposed.",
    danger_note="🟢 Safe — passive listener only. Logs are saved locally.",
    example="Listening on SSH:2222  HTTP:8888  FTP:2121  Telnet:2323",
)

DANGER = DangerLevel.GREEN

LOG_PATH = os.path.expanduser("~/penkit-captures/honeypot.log")

FAKE_BANNERS = {
    "ssh":    b"SSH-2.0-OpenSSH_7.4\r\n",
    "ftp":    b"220 FTP server ready\r\n",
    "telnet": b"\xff\xfb\x01\xff\xfb\x03\xff\xfd\x18\xff\xfd\x1f\r\nRouter> ",
}

FAKE_HTTP_RESPONSE = (
    b"HTTP/1.1 200 OK\r\n"
    b"Server: Apache/2.4.6 (CentOS)\r\n"
    b"Content-Type: text/html\r\n\r\n"
    b"<html><head><title>Login</title></head>"
    b"<body><form method=POST><input name=user><input type=password name=pass>"
    b"<input type=submit value=Login></form></body></html>\r\n"
)


@dataclass
class HoneypotHit:
    timestamp: str
    service: str
    src_ip: str
    src_port: int
    data: str


class Honeypot:
    def __init__(
        self,
        ssh_port: int = 2222,
        http_port: int = 8888,
        ftp_port: int = 2121,
        telnet_port: int = 2323,
        alert_threshold: int = 3,
    ):
        self.ports = {
            "ssh":    ssh_port,
            "http":   http_port,
            "ftp":    ftp_port,
            "telnet": telnet_port,
        }
        self.alert_threshold = alert_threshold
        self._servers: list[asyncio.AbstractServer] = []
        self._hit_counts: dict[str, list[HoneypotHit]] = {}
        self._output_queue: asyncio.Queue[str] = asyncio.Queue()
        self._running = False
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    def _log(self, hit: HoneypotHit):
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({
                "ts": hit.timestamp, "svc": hit.service,
                "ip": hit.src_ip, "port": hit.src_port, "data": hit.data
            }) + "\n")

    async def _handle_client(self, service: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        src_ip, src_port = writer.get_extra_info("peername", ("?", 0))
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Send fake banner
        try:
            if service == "http":
                raw = await asyncio.wait_for(reader.read(512), timeout=3)
                writer.write(FAKE_HTTP_RESPONSE)
            elif service in FAKE_BANNERS:
                writer.write(FAKE_BANNERS[service])
                raw = await asyncio.wait_for(reader.read(256), timeout=5)
            else:
                raw = await asyncio.wait_for(reader.read(256), timeout=3)
            await writer.drain()
            data = raw.decode(errors="replace").strip()[:200]
        except (asyncio.TimeoutError, ConnectionResetError):
            data = "(no data / timeout)"
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

        hit = HoneypotHit(ts, service, src_ip, src_port, data)
        self._log(hit)

        # Track hits per IP
        if src_ip not in self._hit_counts:
            self._hit_counts[src_ip] = []
        self._hit_counts[src_ip].append(hit)

        msg = f"[HIT] {service.upper():8} ← {src_ip}:{src_port}  {ts}"
        if data and data != "(no data / timeout)":
            msg += f"\n       Data: {data[:80]}"
        await self._output_queue.put(msg)

        count = len(self._hit_counts[src_ip])
        if count == self.alert_threshold:
            await self._output_queue.put(
                f"\n  ⚠️  ALERT: {src_ip} has hit honeypot {count} times — likely scanner/attacker\n"
            )

    async def start(self) -> AsyncGenerator[str, None]:
        self._running = True
        services_started = []

        for service, port in self.ports.items():
            try:
                srv = await asyncio.start_server(
                    lambda r, w, svc=service: self._handle_client(svc, r, w),
                    "0.0.0.0",
                    port,
                )
                self._servers.append(srv)
                services_started.append(f"{service.upper()}:{port}")
            except OSError as e:
                yield f"[!] Could not bind {service} on :{port} — {e}"

        if not services_started:
            yield "[ERROR] No honeypot services could start. Try different ports or run as root."
            return

        yield f"[+] Honeypot active on: {', '.join(services_started)}"
        yield f"[+] Alert threshold: {self.alert_threshold} hits/IP"
        yield f"[+] Log file: {LOG_PATH}"
        yield "[*] Waiting for connections..."

        while self._running:
            try:
                msg = await asyncio.wait_for(self._output_queue.get(), timeout=1.0)
                yield msg
            except asyncio.TimeoutError:
                continue

    async def stop(self):
        self._running = False
        for srv in self._servers:
            srv.close()
            try:
                await srv.wait_closed()
            except Exception:
                pass
        self._servers.clear()
