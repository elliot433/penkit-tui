"""
PenKit Health Check — testet was installiert ist und was funktioniert.

Prüft:
  1. Python-Module (alle PenKit-Imports)
  2. Externe Tools (nmap, aircrack-ng, hashcat, ...)
  3. Kali-spezifische Tools
  4. System (root, Interface-Namen, Netz)

Gibt einen übersichtlichen Bericht aus:
  ✓ grün = verfügbar
  ~ gelb = optional, nicht kritisch
  ✗ rot  = fehlt, wichtige Funktion beeinträchtigt
"""

from __future__ import annotations
import asyncio
import importlib
import shutil
import subprocess
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class CheckResult:
    name: str
    status: str    # "ok" | "warn" | "fail"
    detail: str = ""


# ── Python Module ─────────────────────────────────────────────────────────────
PYTHON_MODULES = [
    ("core.danger",              "ok",   "Danger-System"),
    ("core.runner",              "ok",   "Async subprocess runner"),
    ("core.config",              "ok",   "Config laden/speichern"),
    ("tools.wifi",               "ok",   "WiFi-Module"),
    ("tools.passwords",          "ok",   "Password-Module"),
    ("tools.network.scanner",    "ok",   "Network Scanner"),
    ("tools.network.ddos",       "ok",   "DDoS Module"),
    ("tools.network.iot_scanner","ok",   "IoT Scanner"),
    ("tools.web.beef_engine",    "ok",   "BeEF Integration"),
    ("tools.mitm.bettercap_engine", "ok","MITM bettercap"),
    ("tools.mitm.responder_engine", "ok","MITM Responder"),
    ("tools.osint.recon",        "ok",   "OSINT Recon"),
    ("tools.phishing.pages",     "ok",   "Phishing Pages"),
    ("tools.phishing.server",    "ok",   "Phishing Server"),
    ("tools.phishing.smtp_sender","ok",  "SMTP Sender"),
    ("tools.c2.amsi_bypass",     "ok",   "AMSI/ETW Bypass"),
    ("tools.c2.shellcode_engine","ok",   "Shellcode Engine"),
    ("tools.c2.process_hollow",  "ok",   "Process Hollowing"),
    ("tools.c2.payload_builder", "ok",   "Payload Builder"),
    ("tools.c2.telegram_agent",  "ok",   "Telegram C2 Agent"),
    ("tools.joker.kahoot",       "ok",   "Kahoot Tools"),
    ("tools.assistant",          "ok",   "KI-Assistent"),
    ("tools.tutorials",          "ok",   "Tutorials"),
]

# ── Externe Tools ─────────────────────────────────────────────────────────────
# Format: (binary, level, beschreibung, install_cmd)
EXTERNAL_TOOLS = [
    # Kritisch
    ("nmap",           "ok",   "Port/Service Scanner",          "apt install nmap"),
    ("python3",        "ok",   "Python Runtime",                "vorinstalliert"),
    ("curl",           "ok",   "HTTP-Client",                   "apt install curl"),
    ("git",            "ok",   "Version Control",               "apt install git"),
    # WiFi
    ("airmon-ng",      "ok",   "WiFi Monitor-Mode",             "apt install aircrack-ng"),
    ("airodump-ng",    "ok",   "WiFi Packet Capture",           "apt install aircrack-ng"),
    ("aireplay-ng",    "ok",   "WiFi Deauth/Injection",         "apt install aircrack-ng"),
    ("hcxdumptool",    "ok",   "PMKID Capture",                 "apt install hcxdumptool"),
    ("hcxpcapngtool",  "ok",   "PMKID Hash Konvertierung",      "apt install hcxtools"),
    ("hostapd",        "ok",   "Fake Access Point",             "apt install hostapd"),
    # Passwörter
    ("hashcat",        "ok",   "GPU Password Cracker",          "apt install hashcat"),
    ("john",           "ok",   "John the Ripper",               "apt install john"),
    ("hydra",          "ok",   "Online Brute-Force",            "apt install hydra"),
    # Netzwerk/Web
    ("hping3",         "ok",   "SYN/UDP/ICMP Flood",            "apt install hping3"),
    ("ffuf",           "warn", "Web Directory Fuzzer",          "apt install ffuf"),
    ("sqlmap",         "ok",   "SQL Injection",                 "apt install sqlmap"),
    ("nikto",          "ok",   "Web Vulnerability Scanner",     "apt install nikto"),
    ("nuclei",         "warn", "CVE/Template Scanner",          "apt install nuclei"),
    ("wafw00f",        "warn", "WAF Detection",                 "pip3 install wafw00f"),
    # MITM
    ("bettercap",      "ok",   "MITM Framework",                "apt install bettercap"),
    ("responder",      "ok",   "LLMNR/NBT-NS Poisoning",        "apt install responder"),
    # OSINT
    ("theHarvester",   "ok",   "Email/Subdomain Harvesting",    "apt install theharvester"),
    ("sherlock",       "warn", "Username OSINT",                "pip3 install sherlock-project"),
    ("sublist3r",      "warn", "Subdomain Enumeration",         "apt install sublist3r"),
    # BeEF
    ("beef-xss",       "warn", "Browser Exploitation Framework","apt install beef-xss"),
    # Misc
    ("openssl",        "ok",   "SSL/TLS Tools",                 "apt install openssl"),
    ("msfconsole",     "warn", "Metasploit Framework",          "apt install metasploit-framework"),
    ("msfvenom",       "warn", "Payload Generator",             "apt install metasploit-framework"),
    ("pyinstaller",    "warn", "EXE Compiler (Disguise)",       "pip3 install pyinstaller"),
]


async def run_health_check() -> AsyncGenerator[str, None]:
    results: list[CheckResult] = []

    # ── Python Module ──────────────────────────────────────────────────────
    yield "[*] Prüfe Python-Module..."
    ok = warn = fail = 0
    for module, level, desc in PYTHON_MODULES:
        try:
            importlib.import_module(module)
            results.append(CheckResult(module, "ok", desc))
            ok += 1
        except ImportError as e:
            results.append(CheckResult(module, "fail", f"{desc} — {e}"))
            fail += 1
        except Exception as e:
            results.append(CheckResult(module, "warn", f"{desc} — {e}"))
            warn += 1

    yield f"  Module: {ok} OK  |  {warn} Warnung  |  {fail} Fehler"

    # ── Externe Tools ──────────────────────────────────────────────────────
    yield "[*] Prüfe externe Tools..."
    tool_ok = tool_warn = tool_fail = []
    tool_ok, tool_warn, tool_fail = [], [], []

    for binary, level, desc, install in EXTERNAL_TOOLS:
        found = shutil.which(binary) is not None
        if found:
            tool_ok.append((binary, desc))
        elif level == "warn":
            tool_warn.append((binary, desc, install))
        else:
            tool_fail.append((binary, desc, install))

    yield f"  Tools: {len(tool_ok)} installiert  |  {len(tool_warn)} optional fehlt  |  {len(tool_fail)} fehlt"

    # ── System-Checks ──────────────────────────────────────────────────────
    yield "[*] Prüfe System..."
    import os
    is_root = os.geteuid() == 0
    yield f"  Root-Rechte: {'✓ JA' if is_root else '✗ NEIN (sudo -E python3 classic_menu.py)'}"

    # Netzwerk-Interfaces
    try:
        import socket
        hostname = socket.gethostname()
        yield f"  Hostname: {hostname}"
    except Exception:
        pass

    # rockyou.txt
    rockyou = "/usr/share/wordlists/rockyou.txt"
    rockyou_gz = rockyou + ".gz"
    if os.path.exists(rockyou):
        size = os.path.getsize(rockyou) // 1024 // 1024
        yield f"  rockyou.txt: ✓ ({size} MB)"
    elif os.path.exists(rockyou_gz):
        yield f"  rockyou.txt: ~ komprimiert (entpacken: gunzip {rockyou_gz})"
    else:
        yield f"  rockyou.txt: ✗ nicht gefunden"

    # ── Detaillierter Report ───────────────────────────────────────────────
    yield ""
    yield "═" * 60
    yield "INSTALLIERTE TOOLS:"
    yield "═" * 60
    for binary, desc in tool_ok:
        yield f"  ✓  {binary:<20}  {desc}"

    if tool_warn:
        yield ""
        yield "OPTIONALE TOOLS (nicht kritisch):"
        for binary, desc, install in tool_warn:
            yield f"  ~  {binary:<20}  {desc}"
            yield f"     Install: {install}"

    if tool_fail:
        yield ""
        yield "FEHLENDE TOOLS (wichtige Funktionen eingeschränkt):"
        for binary, desc, install in tool_fail:
            yield f"  ✗  {binary:<20}  {desc}"
            yield f"     Install: {install}"

    fail_modules = [r for r in results if r.status == "fail"]
    if fail_modules:
        yield ""
        yield "PYTHON-MODUL FEHLER:"
        for r in fail_modules:
            yield f"  ✗  {r.name:<35}  {r.detail}"

    yield ""
    yield "═" * 60
    total_ok = len(tool_ok)
    total = len(EXTERNAL_TOOLS)
    pct = int(total_ok / total * 100)
    yield f"GESAMT: {total_ok}/{total} Tools installiert ({pct}%)"
    if pct == 100:
        yield "🏆 Perfekt! Alle Tools verfügbar."
    elif pct >= 75:
        yield "✓ Gut — Kernfunktionen verfügbar."
    elif pct >= 50:
        yield "~ Basis funktioniert — fehlende Tools installieren."
    else:
        yield "✗ Viele Tools fehlen — apt-get update && apt-get upgrade empfohlen."
    yield "═" * 60
