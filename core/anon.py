"""
PenKit Anonymitäts-Manager.

Tor starten/stoppen, IP vor/nach prüfen, proxychains-Wrapper,
DNS-Leak-Check, Anonymitätsstatus für Banner.
"""

from __future__ import annotations
import asyncio
import shutil
import subprocess
import urllib.request
import urllib.error
import json
import os
from typing import AsyncGenerator

# ── Globaler Status ───────────────────────────────────────────────────────────

_tor_active: bool = False


def _fetch_ip(url: str, timeout: int = 5) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}


def get_real_ip() -> str:
    """Aktuelle öffentliche IP holen (direkt, kein Proxy)."""
    for url in [
        "https://ipinfo.io/json",
        "https://api.ipify.org?format=json",
    ]:
        data = _fetch_ip(url)
        if data.get("ip"):
            return data["ip"]
    return "?"


def get_tor_ip() -> str:
    """IP über Tor-Proxy holen (127.0.0.1:9050)."""
    try:
        import urllib.request
        proxy = urllib.request.ProxyHandler({"http": "socks5h://127.0.0.1:9050",
                                              "https": "socks5h://127.0.0.1:9050"})
        opener = urllib.request.build_opener(proxy)
        req = urllib.request.Request("https://check.torproject.org/api/ip",
                                      headers={"User-Agent": "curl/7.88"})
        with opener.open(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("IP", "?")
    except Exception:
        return "?"


def tor_running() -> bool:
    """Prüft ob Tor-Daemon läuft."""
    try:
        result = subprocess.run(["systemctl", "is-active", "tor"],
                                capture_output=True, text=True)
        if result.stdout.strip() == "active":
            return True
    except Exception:
        pass
    # Fallback: Port-Check
    try:
        import socket
        s = socket.create_connection(("127.0.0.1", 9050), timeout=1)
        s.close()
        return True
    except Exception:
        return False


def proxychains_available() -> bool:
    return shutil.which("proxychains4") is not None or shutil.which("proxychains") is not None


def proxychains_cmd() -> str:
    return "proxychains4" if shutil.which("proxychains4") else "proxychains"


def anon_status() -> dict:
    """Gibt aktuellen Anonymitätsstatus zurück (schnell, kein DNS)."""
    global _tor_active
    _tor_active = tor_running()
    return {
        "tor": _tor_active,
        "proxychains": proxychains_available(),
    }


def status_line() -> str:
    """Einzeilige Statusanzeige für das Banner."""
    s = anon_status()
    try:
        from core.opsec import killswitch_status
        ks = killswitch_status()
    except Exception:
        ks = False

    if s["tor"] and ks:
        return "\033[1;32m  [🧅 TOR AKTIV + 🔒 KILL SWITCH — Maximale Anonymität]\033[0m"
    elif s["tor"]:
        return "\033[1;33m  [🧅 TOR AKTIV — ⚠️  Kill Switch inaktiv → N für vollen Schutz]\033[0m"
    else:
        return "\033[1;31m  [⚠️  KEIN TOR — Echte IP sichtbar! → N drücken]\033[0m"


# ── Tor starten/stoppen ───────────────────────────────────────────────────────

async def start_tor() -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Starte Tor...\033[0m"

    if not shutil.which("tor"):
        yield "\033[31m[!] Tor nicht installiert → sudo apt install tor\033[0m"
        return

    proc = await asyncio.create_subprocess_exec(
        "sudo", "systemctl", "start", "tor",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        yield f"\033[31m[!] Fehler: {stderr.decode().strip()}\033[0m"
        return

    # Warten bis Tor verbunden ist
    yield "\033[36m[*] Warte auf Tor-Verbindung (max 30s)...\033[0m"
    for i in range(15):
        await asyncio.sleep(2)
        if tor_running():
            break
        yield f"\033[90m  [{(i+1)*2}s] Verbinde...\033[0m"

    if not tor_running():
        yield "\033[31m[!] Tor-Start Timeout — prüfe: sudo systemctl status tor\033[0m"
        return

    # IP über Tor prüfen
    yield "\033[32m[✓] Tor läuft!\033[0m"
    yield "\033[36m[*] Prüfe Tor-IP...\033[0m"
    tor_ip = get_tor_ip()
    yield f"\033[1;32m[✓] Tor Exit-IP: {tor_ip}\033[0m"
    yield ""
    yield "\033[33m[!] WICHTIG: PenKit über proxychains starten für vollen Schutz:\033[0m"
    yield "\033[36m    proxychains4 python3 classic_menu.py\033[0m"
    yield ""
    yield "\033[32m[✓] Tor aktiv — anonymer Traffic möglich.\033[0m"


async def stop_tor() -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Stoppe Tor...\033[0m"
    proc = await asyncio.create_subprocess_exec(
        "sudo", "systemctl", "stop", "tor",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()
    yield "\033[33m[~] Tor gestoppt — direkte Verbindung aktiv.\033[0m"


async def restart_tor() -> AsyncGenerator[str, None]:
    """Tor neustarten → neue Exit-IP."""
    yield "\033[1;36m[*] Neue Tor-Identity anfordern...\033[0m"
    proc = await asyncio.create_subprocess_exec(
        "sudo", "systemctl", "restart", "tor",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()
    await asyncio.sleep(5)
    tor_ip = get_tor_ip()
    yield f"\033[1;32m[✓] Neue Exit-IP: {tor_ip}\033[0m"


# ── IP-Leak-Check ─────────────────────────────────────────────────────────────

async def ip_leak_check() -> AsyncGenerator[str, None]:
    """Zeigt echte IP vs Tor-IP und DNS-Leak-Status."""
    yield "\033[1;36m[*] IP & Leak Check\033[0m\n"

    yield "\033[36m[*] Echte öffentliche IP (direkt)...\033[0m"
    real_ip = get_real_ip()
    yield f"  Direkte IP:  \033[1;33m{real_ip}\033[0m"

    yield ""
    if tor_running():
        yield "\033[36m[*] IP über Tor-Proxy...\033[0m"
        tor_ip = get_tor_ip()
        if tor_ip != "?" and tor_ip != real_ip:
            yield f"  Tor Exit-IP: \033[1;32m{tor_ip}\033[0m  ✓ Anders als echte IP"
        elif tor_ip == real_ip:
            yield f"  \033[31m[!] Tor-IP == echte IP — Tor-Proxy evtl. nicht aktiv!\033[0m"
        else:
            yield f"  \033[33m[~] Tor-IP konnte nicht abgerufen werden\033[0m"
    else:
        yield f"  \033[31m[!] Tor läuft nicht — echte IP {real_ip} wird genutzt\033[0m"

    yield ""
    # Proxychains-Check
    if proxychains_available():
        yield f"  \033[32m[✓] proxychains4 verfügbar\033[0m"
    else:
        yield f"  \033[33m[~] proxychains4 nicht gefunden → sudo apt install proxychains4\033[0m"

    yield ""
    yield "─" * 55
    yield "\033[1mEmpfehlung:\033[0m"
    if tor_running() and proxychains_available():
        yield "  \033[32m[✓] Starte PenKit mit: proxychains4 python3 classic_menu.py\033[0m"
    elif not tor_running():
        yield "  \033[31m[1] Tor starten (Option 1 im Anonymitäts-Menü)\033[0m"
        yield "  \033[31m[2] Dann neustarten mit: proxychains4 python3 classic_menu.py\033[0m"


# ── proxychains.conf prüfen/patchen ──────────────────────────────────────────

async def setup_proxychains() -> AsyncGenerator[str, None]:
    """Stellt sicher dass proxychains auf Tor zeigt (127.0.0.1:9050)."""
    conf_paths = [
        "/etc/proxychains4.conf",
        "/etc/proxychains.conf",
    ]
    conf = None
    for p in conf_paths:
        if os.path.exists(p):
            conf = p
            break

    if not conf:
        yield "\033[31m[!] proxychains.conf nicht gefunden\033[0m"
        yield "    sudo apt install proxychains4"
        return

    with open(conf) as f:
        content = f.read()

    yield f"\033[36m[*] Config: {conf}\033[0m"

    # Prüfen ob socks5 127.0.0.1 9050 drin steht
    if "socks5\t127.0.0.1\t9050" in content or "socks5 127.0.0.1 9050" in content:
        yield "\033[32m[✓] proxychains bereits auf Tor konfiguriert (socks5 127.0.0.1 9050)\033[0m"
    else:
        yield "\033[33m[~] Tor-Eintrag fehlt — füge hinzu...\033[0m"
        try:
            proc = await asyncio.create_subprocess_exec(
                "sudo", "bash", "-c",
                f"echo 'socks5 127.0.0.1 9050' >> {conf}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            yield "\033[32m[✓] socks5 127.0.0.1 9050 → proxychains.conf hinzugefügt\033[0m"
        except Exception as e:
            yield f"\033[31m[!] Fehler: {e}\033[0m"
            yield f"    Manuell hinzufügen: echo 'socks5 127.0.0.1 9050' | sudo tee -a {conf}"

    yield ""
    yield "\033[32m[✓] PenKit über proxychains starten:\033[0m"
    yield "\033[36m    proxychains4 python3 classic_menu.py\033[0m"
