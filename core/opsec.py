"""
PenKit OPSEC Suite.

MAC Spoofing, Tor Kill Switch, iptables Firewall,
Hostname Changer, Log/History Cleaner, Session Wipe.
"""

from __future__ import annotations
import asyncio
import os
import random
import shutil
import string
import subprocess
from typing import AsyncGenerator

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode().strip(), stderr.decode().strip()


def _interfaces() -> list[str]:
    """Alle Netzwerk-Interfaces außer lo."""
    try:
        result = subprocess.run(["ip", "-o", "link", "show"],
                                capture_output=True, text=True)
        ifaces = []
        for line in result.stdout.splitlines():
            parts = line.split(":")
            if len(parts) >= 2:
                name = parts[1].strip().split("@")[0]
                if name != "lo":
                    ifaces.append(name)
        return ifaces
    except Exception:
        return []


def _tor_uid() -> str:
    """UID des Tor-Prozesses ermitteln."""
    for name in ["debian-tor", "tor", "_tor"]:
        try:
            import pwd
            return str(pwd.getpwnam(name).pw_uid)
        except Exception:
            pass
    return ""


# ── MAC Spoofing ──────────────────────────────────────────────────────────────

async def mac_spoof(interface: str = "", restore: bool = False) -> AsyncGenerator[str, None]:
    """MAC-Adresse eines Interfaces zufällig ändern oder wiederherstellen."""
    yield "\033[1;36m[*] MAC Address Spoofing\033[0m\n"

    ifaces = _interfaces()
    if not ifaces:
        yield "\033[31m[!] Keine Interfaces gefunden\033[0m"
        return

    if not interface:
        # Erstes nicht-lo Interface nehmen
        interface = ifaces[0]

    yield f"  Interface: \033[33m{interface}\033[0m"

    # Aktuelle MAC anzeigen
    rc, out, _ = await _run(["ip", "link", "show", interface])
    for line in out.splitlines():
        if "link/ether" in line:
            current_mac = line.strip().split()[1]
            yield f"  Aktuelle MAC:  \033[33m{current_mac}\033[0m"
            break

    if restore:
        if not shutil.which("macchanger"):
            yield "\033[31m[!] macchanger nicht gefunden → sudo apt install macchanger\033[0m"
            return
        await _run(["sudo", "ip", "link", "set", interface, "down"])
        rc, out, err = await _run(["sudo", "macchanger", "-p", interface])
        await _run(["sudo", "ip", "link", "set", interface, "up"])
        yield f"\033[32m[✓] Original MAC wiederhergestellt\033[0m"
        return

    if shutil.which("macchanger"):
        await _run(["sudo", "ip", "link", "set", interface, "down"])
        rc, out, err = await _run(["sudo", "macchanger", "-r", interface])
        await _run(["sudo", "ip", "link", "set", interface, "up"])
        for line in out.splitlines():
            if "New MAC" in line:
                new_mac = line.split(":")[1].strip() if ":" in line else line
                yield f"  Neue MAC:      \033[32m{new_mac}\033[0m"
        yield "\033[32m[✓] MAC erfolgreich geändert\033[0m"
    else:
        # Fallback ohne macchanger — manuelle zufällige MAC
        yield "\033[33m[~] macchanger nicht gefunden, nutze ip-Fallback\033[0m"
        # Lokal administrierte MAC (zweites Bit gesetzt, erstes Bit = 0)
        mac_bytes = [random.randint(0, 255) for _ in range(6)]
        mac_bytes[0] = (mac_bytes[0] & 0xFE) | 0x02  # locally administered, unicast
        new_mac = ":".join(f"{b:02x}" for b in mac_bytes)
        await _run(["sudo", "ip", "link", "set", interface, "down"])
        rc, out, err = await _run(["sudo", "ip", "link", "set", interface, "address", new_mac])
        await _run(["sudo", "ip", "link", "set", interface, "up"])
        if rc == 0:
            yield f"  Neue MAC:      \033[32m{new_mac}\033[0m"
            yield "\033[32m[✓] MAC geändert (ip-Fallback)\033[0m"
            yield "\033[33m[~] Tipp: sudo apt install macchanger für bessere Kontrolle\033[0m"
        else:
            yield f"\033[31m[!] Fehler: {err}\033[0m"


async def mac_spoof_all() -> AsyncGenerator[str, None]:
    """Alle Interfaces auf einmal spoofing."""
    yield "\033[1;36m[*] Alle Interfaces MAC-Spoofing\033[0m\n"
    ifaces = _interfaces()
    for iface in ifaces:
        async for line in mac_spoof(iface):
            yield line
        yield ""


# ── Tor Kill Switch ───────────────────────────────────────────────────────────

_KILLSWITCH_ACTIVE = False

async def killswitch_enable() -> AsyncGenerator[str, None]:
    """
    Aktiviert Tor Kill Switch via iptables.
    Blockiert ALLEN Traffic außer Tor — wenn Tor abbricht, kein Leak.
    """
    global _KILLSWITCH_ACTIVE
    yield "\033[1;36m[*] Tor Kill Switch aktivieren\033[0m\n"
    yield "  Blockiert alles außer Tor-Traffic — kein IP-Leak möglich.\n"

    tor_uid = _tor_uid()
    if not tor_uid:
        yield "\033[31m[!] Tor-UID nicht gefunden — ist Tor installiert?\033[0m"
        yield "    sudo apt install tor"
        return

    yield f"  Tor UID: {tor_uid}"

    cmds = [
        # Flush existing rules
        ["sudo", "iptables", "-F", "OUTPUT"],
        # Allow loopback
        ["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        # Allow Tor process itself (so Tor can connect to the network)
        ["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", tor_uid, "-j", "ACCEPT"],
        # Allow established/related connections
        ["sudo", "iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        # Block everything else
        ["sudo", "iptables", "-A", "OUTPUT", "-j", "DROP"],
    ]

    for cmd in cmds:
        rc, out, err = await _run(cmd)
        if rc != 0 and err:
            yield f"\033[33m[~] {' '.join(cmd[2:])}: {err}\033[0m"

    _KILLSWITCH_ACTIVE = True
    yield "\033[1;32m[✓] Kill Switch AKTIV\033[0m"
    yield "  → Nur Tor-Traffic erlaubt"
    yield "  → Bei Tor-Ausfall: kein Traffic = kein IP-Leak"
    yield ""
    yield "\033[33m[!] PenKit jetzt über proxychains starten:\033[0m"
    yield "\033[36m    proxychains4 python3 classic_menu.py\033[0m"


async def killswitch_disable() -> AsyncGenerator[str, None]:
    """Kill Switch deaktivieren — normaler Traffic wieder erlaubt."""
    global _KILLSWITCH_ACTIVE
    yield "\033[1;36m[*] Kill Switch deaktivieren\033[0m"

    cmds = [
        ["sudo", "iptables", "-F", "OUTPUT"],
        ["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"],
    ]
    for cmd in cmds:
        await _run(cmd)

    _KILLSWITCH_ACTIVE = False
    yield "\033[33m[~] Kill Switch deaktiviert — direkter Traffic möglich\033[0m"
    yield "\033[31m[!] Deine echte IP ist jetzt wieder sichtbar!\033[0m"


def killswitch_status() -> bool:
    """Prüft ob Kill Switch aktiv ist (iptables OUTPUT DROP vorhanden)."""
    try:
        result = subprocess.run(
            ["sudo", "iptables", "-L", "OUTPUT", "-n"],
            capture_output=True, text=True
        )
        return "DROP" in result.stdout
    except Exception:
        return False


# ── Hostname Changer ──────────────────────────────────────────────────────────

FAKE_HOSTNAMES = [
    "DESKTOP-7X2K9P", "LAPTOP-3QR8M1", "PC-HOME-4521",
    "WORKSTATION-9A", "WIN-K3J7PLMN", "MSEDGEWIN10",
    "DESKTOP-WIN11", "USER-PC-2024", "OFFICE-PC-7",
    "HOME-DESKTOP-3", "LAPTOP-FELIX", "NB-PERSONAL",
]

async def hostname_change(new_name: str = "") -> AsyncGenerator[str, None]:
    """Hostname auf zufälligen Windows-ähnlichen Namen ändern."""
    yield "\033[1;36m[*] Hostname Changer\033[0m\n"

    rc, current, _ = await _run(["hostname"])
    yield f"  Aktueller Hostname: \033[33m{current}\033[0m"

    if not new_name:
        new_name = random.choice(FAKE_HOSTNAMES)

    yield f"  Neuer Hostname:     \033[32m{new_name}\033[0m"

    rc, _, err = await _run(["sudo", "hostnamectl", "set-hostname", new_name])
    if rc == 0:
        yield "\033[32m[✓] Hostname geändert\033[0m"
        yield f"  \033[90mWird in Netzwerkscans als '{new_name}' erscheinen\033[0m"
    else:
        yield f"\033[31m[!] Fehler: {err}\033[0m"
        # Fallback
        rc2, _, _ = await _run(["sudo", "hostname", new_name])
        if rc2 == 0:
            yield "\033[32m[✓] Hostname geändert (Fallback)\033[0m"


async def hostname_restore() -> AsyncGenerator[str, None]:
    """Hostname auf kali zurücksetzen."""
    yield "\033[1;36m[*] Hostname zurücksetzen\033[0m"
    rc, _, err = await _run(["sudo", "hostnamectl", "set-hostname", "kali"])
    if rc == 0:
        yield "\033[32m[✓] Hostname → kali\033[0m"
    else:
        yield f"\033[31m[!] {err}\033[0m"


# ── Log & History Cleaner ─────────────────────────────────────────────────────

LOG_FILES = [
    "/var/log/auth.log",
    "/var/log/syslog",
    "/var/log/kern.log",
    "/var/log/dpkg.log",
    "/var/log/apt/history.log",
    "/var/log/wtmp",
    "/var/log/btmp",
    "/var/log/lastlog",
    "/var/log/faillog",
    "/var/log/messages",
]

HISTORY_FILES = [
    "~/.bash_history",
    "~/.zsh_history",
    "~/.python_history",
    "~/.local/share/recently-used.xbel",
    "~/.recently-used",
]

async def clean_logs() -> AsyncGenerator[str, None]:
    """System-Logs leeren."""
    yield "\033[1;36m[*] System-Logs löschen\033[0m\n"
    cleaned = 0
    for log in LOG_FILES:
        if os.path.exists(log):
            rc, _, err = await _run(["sudo", "truncate", "-s", "0", log])
            if rc == 0:
                yield f"  \033[32m[✓] {log}\033[0m"
                cleaned += 1
            else:
                yield f"  \033[33m[~] {log}: {err}\033[0m"
        else:
            yield f"  \033[90m[–] {log} (nicht vorhanden)\033[0m"

    yield f"\n\033[32m[✓] {cleaned} Log-Dateien geleert\033[0m"


async def clean_history() -> AsyncGenerator[str, None]:
    """Shell-History und zuletzt geöffnete Dateien löschen."""
    yield "\033[1;36m[*] Shell-History löschen\033[0m\n"

    # Laufende Shell-History löschen
    yield "  \033[36m[*] Laufende Bash-History...\033[0m"
    await _run(["bash", "-c", "history -c"])

    cleaned = 0
    for hfile in HISTORY_FILES:
        path = os.path.expanduser(hfile)
        if os.path.exists(path):
            try:
                open(path, "w").close()
                yield f"  \033[32m[✓] {hfile}\033[0m"
                cleaned += 1
            except Exception as e:
                rc, _, _ = await _run(["sudo", "truncate", "-s", "0", path])
                if rc == 0:
                    yield f"  \033[32m[✓] {hfile} (sudo)\033[0m"
                    cleaned += 1

    yield f"\n\033[32m[✓] {cleaned} History-Dateien geleert\033[0m"
    yield "\033[33m[!] Aktuelles Terminal: history -c && exit (dann neu öffnen)\033[0m"


# ── Session Wipe ─────────────────────────────────────────────────────────────

WIPE_DIRS = [
    "/tmp",
    "/var/tmp",
    "~/.cache/mozilla",
    "~/.cache/chromium",
    "~/.config/chromium",
]

WIPE_PATTERNS = [
    "~/*.pcap",
    "~/*.cap",
    "~/*.hccapx",
    "/tmp/penkit_*",
    "/tmp/*.pem",
    "/tmp/*.key",
    "/tmp/key.pem",
    "/tmp/cert.pem",
    "/tmp/socat.*",
    "/tmp/.p",
]

async def session_wipe(wipe_output: bool = False) -> AsyncGenerator[str, None]:
    """
    Temporäre Dateien, Captures, Keys, Cache sicher löschen.
    wipe_output=True löscht auch ~/penkit-output/ komplett.
    """
    yield "\033[1;36m[*] Session Wipe\033[0m\n"
    wiped = 0

    # Temp-Patterns
    yield "  \033[36m[*] Temporäre Dateien...\033[0m"
    import glob
    for pattern in WIPE_PATTERNS:
        for f in glob.glob(os.path.expanduser(pattern)):
            try:
                if os.path.isfile(f):
                    # Überschreiben vor löschen (sicherer als nur rm)
                    size = os.path.getsize(f)
                    with open(f, "wb") as fh:
                        fh.write(b"\x00" * size)
                    os.remove(f)
                    yield f"  \033[32m[✓] {f}\033[0m"
                    wiped += 1
            except Exception:
                await _run(["sudo", "rm", "-f", f])

    # /tmp leeren
    yield "\n  \033[36m[*] /tmp aufräumen...\033[0m"
    rc, _, _ = await _run(["sudo", "find", "/tmp", "-maxdepth", "1",
                            "-name", "penkit*", "-delete"])
    rc2, _, _ = await _run(["sudo", "find", "/tmp", "-maxdepth", "1",
                             "-name", "*.pem", "-delete"])
    rc3, _, _ = await _run(["sudo", "find", "/tmp", "-maxdepth", "1",
                             "-name", "*.key", "-delete"])
    yield "  \033[32m[✓] /tmp PenKit-Dateien entfernt\033[0m"

    # penkit-output optional
    if wipe_output:
        from core.output_dir import ROOT
        rc, _, err = await _run(["rm", "-rf", str(ROOT)])
        if rc == 0:
            yield f"  \033[32m[✓] {ROOT} gelöscht\033[0m"
        else:
            yield f"  \033[31m[!] {err}\033[0m"

    yield f"\n\033[32m[✓] Session Wipe abgeschlossen — {wiped} Dateien sicher gelöscht\033[0m"


# ── OPSEC Status ─────────────────────────────────────────────────────────────

def opsec_score() -> tuple[int, list[str]]:
    """
    Berechnet OPSEC-Score 0-100 und gibt Warnungen zurück.
    Wird im Anonymitäts-Menü angezeigt.
    """
    from core.anon import tor_running, proxychains_available
    score = 0
    warnings = []

    if tor_running():
        score += 40
    else:
        warnings.append("Tor nicht aktiv — echte IP sichtbar")

    if killswitch_status():
        score += 25
    else:
        warnings.append("Kill Switch inaktiv — IP-Leak bei Tor-Ausfall möglich")

    if proxychains_available():
        score += 15
    else:
        warnings.append("proxychains4 nicht installiert")

    # Hostname nicht 'kali'
    try:
        hn = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()
        if hn.lower() not in ("kali", ""):
            score += 10
        else:
            warnings.append(f"Hostname ist '{hn}' — in Netzwerkscans sichtbar")
    except Exception:
        pass

    # History-Check: bash_history leer?
    hist = os.path.expanduser("~/.bash_history")
    if os.path.exists(hist) and os.path.getsize(hist) == 0:
        score += 10
    else:
        warnings.append("Bash-History nicht geleert")

    return min(score, 100), warnings
