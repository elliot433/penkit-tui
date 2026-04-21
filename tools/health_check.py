"""
PenKit Health Check — testet was installiert ist und was funktioniert.

Prüft:
  1. Python-Module (alle PenKit-Imports)
  2. Externe Tools nach Kategorie
  3. System (root, interfaces, wordlists, disk)
  4. Sonderchecks (Ollama, Go, dalfox PATH, Evilginx)
  5. Reliability Guide

Status:
  ✓ grün = verfügbar
  ~ gelb = optional, nicht kritisch
  ✗ rot  = fehlt, wichtige Funktion eingeschränkt
"""

from __future__ import annotations
import asyncio
import importlib
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class CheckResult:
    name: str
    status: str    # "ok" | "warn" | "fail"
    detail: str = ""


# ── Python Module ──────────────────────────────────────────────────────────────
PYTHON_MODULES = [
    # Core
    ("core.danger",                   "ok",   "Danger-System"),
    ("core.runner",                   "ok",   "Async subprocess runner"),
    ("core.config",                   "ok",   "Config laden/speichern"),
    ("core.report_gen",               "ok",   "HTML Report Generator"),
    ("core.anon",                     "ok",   "Tor / Anonymität"),
    ("core.opsec",                    "ok",   "OPSEC Suite"),
    # WiFi
    ("tools.wifi",                    "ok",   "WiFi-Module"),
    # Passwörter
    ("tools.passwords",               "ok",   "Password-Module"),
    # Netzwerk
    ("tools.network.scanner",         "ok",   "Network Scanner"),
    ("tools.network.topology",        "ok",   "Topology Mapper"),
    ("tools.network.ad_suite",        "ok",   "Active Directory Suite"),
    ("tools.network.auto_exploit",    "ok",   "Auto-Exploit Suggester"),
    ("tools.network.lateral_movement","ok",   "Lateral Movement Wizard"),
    ("tools.network.msf_integration", "ok",   "Metasploit Integration"),
    # Web
    ("tools.web.beef_engine",         "ok",   "BeEF Integration"),
    ("tools.web.xss_engine",          "ok",   "XSS Engine (dalfox)"),
    ("tools.web.subdomain_takeover",  "ok",   "Subdomain Takeover Scanner"),
    # MITM
    ("tools.mitm.bettercap_engine",   "ok",   "MITM bettercap"),
    ("tools.mitm.responder_engine",   "ok",   "MITM Responder"),
    # OSINT
    ("tools.osint.recon",             "ok",   "OSINT Recon"),
    ("tools.osint.social_osint",      "ok",   "Social Media OSINT"),
    # Phishing
    ("tools.phishing.pages",          "ok",   "Phishing Pages"),
    ("tools.phishing.server",         "ok",   "Phishing Server"),
    ("tools.phishing.smtp_sender",    "ok",   "SMTP Sender"),
    ("tools.phishing.evilginx",       "ok",   "Evilginx 2FA-Bypass"),
    ("tools.phishing.gophish_engine", "ok",   "GoPhish Integration"),
    # C2
    ("tools.c2.amsi_bypass",          "ok",   "AMSI/ETW Bypass"),
    ("tools.c2.shellcode_engine",     "ok",   "Shellcode Engine"),
    ("tools.c2.process_hollow",       "ok",   "Process Hollowing"),
    ("tools.c2.payload_builder",      "ok",   "Payload Builder"),
    ("tools.c2.telegram_agent",       "ok",   "Telegram C2 Agent"),
    ("tools.c2.evasion",              "ok",   "Advanced Evasion Suite"),
    ("tools.c2.uac_bypass",           "ok",   "UAC Bypass Suite"),
    ("tools.c2.privesc_scanner",      "ok",   "Auto-PrivEsc Scanner"),
    ("tools.c2.post_exploit",         "ok",   "Post-Exploitation Suite"),
    # Blue Team
    ("tools.blueteam",                "ok",   "Blue Team Tools"),
    # Joker
    ("tools.joker.kahoot",            "ok",   "Kahoot Tools"),
    # Mobile
    ("tools.mobile.ios_attack",       "ok",   "iOS Attack Suite"),
    ("tools.mobile.android_attack",   "ok",   "Android Attack Suite"),
    # Recon / CVE
    ("tools.recon.auto_recon",        "ok",   "Auto-Recon Pipeline"),
    ("tools.recon.searchsploit_engine","ok",  "Searchsploit / CVE Engine"),
    # Cloud
    ("tools.cloud.aws_recon",         "ok",   "AWS / Cloud Attack Suite"),
    # Sonstiges
    ("tools.assistant",               "ok",   "KI-Assistent"),
    ("tools.tutorials",               "ok",   "Tutorials"),
    ("tools.ai_terminal",             "ok",   "AI Attack Terminal"),
    ("tools.map_tracker",             "ok",   "Target Map"),
]

# ── Externe Tools ──────────────────────────────────────────────────────────────
# Format: (binary, level, kategorie, beschreibung, install_cmd)
EXTERNAL_TOOLS = [
    # ── Basis ──────────────────────────────────────────────────────────────────
    ("nmap",              "ok",   "Basis",     "Port/Service/OS Scanner",            "apt install nmap"),
    ("python3",           "ok",   "Basis",     "Python Runtime",                      "vorinstalliert"),
    ("curl",              "ok",   "Basis",     "HTTP-Client",                         "apt install curl"),
    ("git",               "ok",   "Basis",     "Version Control",                     "apt install git"),
    ("go",                "warn", "Basis",     "Go Compiler (Evilginx, dalfox)",      "apt install golang-go"),
    # ── WiFi ───────────────────────────────────────────────────────────────────
    ("airmon-ng",         "ok",   "WiFi",      "WiFi Monitor-Mode",                   "apt install aircrack-ng"),
    ("airodump-ng",       "ok",   "WiFi",      "WiFi Packet Capture",                 "apt install aircrack-ng"),
    ("aireplay-ng",       "ok",   "WiFi",      "WiFi Deauth/Injection",               "apt install aircrack-ng"),
    ("hcxdumptool",       "ok",   "WiFi",      "PMKID Capture",                       "apt install hcxdumptool"),
    ("hcxpcapngtool",     "ok",   "WiFi",      "PMKID Hash Konvertierung",            "apt install hcxtools"),
    ("hostapd",           "ok",   "WiFi",      "Fake Access Point (Evil Twin)",       "apt install hostapd"),
    ("dnsmasq",           "ok",   "WiFi",      "Fake DHCP/DNS (Evil Twin)",           "apt install dnsmasq"),
    # ── Passwörter ─────────────────────────────────────────────────────────────
    ("hashcat",           "ok",   "Passwörter","GPU Password Cracker",                "apt install hashcat"),
    ("john",              "ok",   "Passwörter","John the Ripper",                     "apt install john"),
    ("hydra",             "ok",   "Passwörter","Online Brute-Force",                  "apt install hydra"),
    # ── Netzwerk / Recon ───────────────────────────────────────────────────────
    ("hping3",            "ok",   "Netzwerk",  "SYN/UDP/ICMP Flood",                  "apt install hping3"),
    ("subfinder",         "warn", "Netzwerk",  "Subdomain Finder",                    "apt install subfinder"),
    ("amass",             "warn", "Netzwerk",  "Subdomain Enumeration",               "apt install amass"),
    # ── Web ────────────────────────────────────────────────────────────────────
    ("ffuf",              "ok",   "Web",       "Web Directory/Parameter Fuzzer",      "apt install ffuf"),
    ("sqlmap",            "ok",   "Web",       "SQL Injection",                       "apt install sqlmap"),
    ("nikto",             "ok",   "Web",       "Web Vulnerability Scanner",           "apt install nikto"),
    ("nuclei",            "warn", "Web",       "CVE/Template Scanner",                "apt install nuclei"),
    ("wafw00f",           "warn", "Web",       "WAF Detection",                       "pip3 install wafw00f"),
    ("dalfox",            "warn", "Web",       "XSS Scanner (im PATH?)",              "go install github.com/hahwul/dalfox/v2@latest"),
    # ── MITM ───────────────────────────────────────────────────────────────────
    ("bettercap",         "ok",   "MITM",      "MITM Framework",                      "apt install bettercap"),
    ("responder",         "ok",   "MITM",      "LLMNR/NBT-NS Poisoning",              "apt install responder"),
    ("mitm6",             "warn", "MITM",      "IPv6 MITM / NTLM Relay",              "pip3 install mitm6"),
    # ── Active Directory / Lateral Movement ────────────────────────────────────
    ("netexec",           "ok",   "AD/Lateral","Swiss Army Knife für AD",             "apt install netexec"),
    ("evil-winrm",        "warn", "AD/Lateral","WinRM PTH Shell",                     "gem install evil-winrm"),
    ("sshuttle",          "warn", "AD/Lateral","Transparenter SSH Tunnel",            "apt install sshuttle"),
    # ── Metasploit ─────────────────────────────────────────────────────────────
    ("msfconsole",        "warn", "Metasploit","Metasploit Framework",                "apt install metasploit-framework"),
    ("msfvenom",          "warn", "Metasploit","MSF Payload Generator",               "apt install metasploit-framework"),
    # ── OSINT ──────────────────────────────────────────────────────────────────
    ("theHarvester",      "ok",   "OSINT",     "Email/Subdomain Harvesting",          "apt install theharvester"),
    ("sherlock",          "warn", "OSINT",     "Username OSINT (300+ Plattformen)",   "pip3 install sherlock-project"),
    ("sublist3r",         "warn", "OSINT",     "Subdomain Enumeration",               "apt install sublist3r"),
    # ── Phishing / C2 ──────────────────────────────────────────────────────────
    ("evilginx",          "warn", "Phishing",  "2FA-Bypass Reverse Proxy",            "go install github.com/kgretzky/evilginx/v3@latest"),
    ("socat",             "ok",   "C2",        "Versatile Socket Tool",               "apt install socat"),
    ("openssl",           "ok",   "C2",        "SSL/TLS Tools",                       "apt install openssl"),
    ("pyinstaller",       "warn", "C2",        "EXE Compiler (Disguise-Tool)",        "pip3 install pyinstaller"),
    # ── Mobile ─────────────────────────────────────────────────────────────────
    ("adb",               "warn", "Mobile",    "Android Debug Bridge",                "apt install adb"),
    ("ideviceinfo",       "warn", "Mobile",    "iOS USB Forensik (libimobiledevice)", "apt install libimobiledevice-utils"),
    # ── Cloud / Recon ──────────────────────────────────────────────────────────
    ("aws",               "warn", "Cloud",     "AWS CLI (S3, IAM, EC2)",              "apt install awscli"),
    ("searchsploit",      "warn", "Recon",     "Exploit-DB Suche",                    "apt install exploitdb"),
    ("whatweb",           "warn", "Recon",     "Web Fingerprinting",                  "apt install whatweb"),
    ("httpx",             "warn", "Recon",     "HTTP Probe (Live-Host-Check)",        "go install github.com/projectdiscovery/httpx/cmd/httpx@latest"),
    ("gowitness",         "warn", "Recon",     "Web Screenshots",                     "go install github.com/sensepost/gowitness@latest"),
    ("gitleaks",          "warn", "Cloud",     "Git Secret Scanner",                  "apt install gitleaks"),
    # ── AI / Extras ────────────────────────────────────────────────────────────
    ("ollama",            "warn", "AI",        "Lokales KI-Modell (AI Terminal)",     "curl -fsSL https://ollama.com/install.sh | sh"),
    ("beef-xss",          "warn", "Web",       "Browser Exploitation Framework",      "apt install beef-xss"),
    # ── BloodHound ─────────────────────────────────────────────────────────────
    ("bloodhound",        "warn", "AD",        "AD Attack Path Visualizer",           "apt install bloodhound"),
]


# ── Python-Pip Module Check ────────────────────────────────────────────────────
PIP_MODULES = [
    ("instaloader",  "Instagram OSINT"),
    ("pypykatz",     "LSASS Dump Analyse"),
    ("impacket",     "AD / SMB / NTLM Tools"),
    ("requests",     "HTTP Library"),
    ("flask",        "Phishing Server"),
    ("bs4",          "HTML Parser (BeautifulSoup)"),
    ("nicegui",      "Web UI (python3 web_app.py)"),
    ("boto3",        "AWS Python SDK (Cloud Attacks)"),
    ("pyicloud",     "Apple iCloud API (iOS Brute-Force)"),
    ("trufflehog",   "Git Secret Scanner (GitHub Leaks)"),
]


async def run_health_check() -> AsyncGenerator[str, None]:
    results: list[CheckResult] = []

    # ── Python Module ──────────────────────────────────────────────────────────
    yield "[*] Prüfe PenKit Python-Module..."
    ok = warn = fail = 0
    failed_modules = []
    for module, level, desc in PYTHON_MODULES:
        try:
            importlib.import_module(module)
            results.append(CheckResult(module, "ok", desc))
            ok += 1
        except ImportError as e:
            results.append(CheckResult(module, "fail", f"{desc} — {e}"))
            failed_modules.append((module, desc, str(e)))
            fail += 1
        except Exception as e:
            results.append(CheckResult(module, "warn", f"{desc} — {e}"))
            warn += 1

    yield f"  Module: {ok} ✓  |  {warn} ⚠  |  {fail} ✗"

    # ── Externe Tools nach Kategorie ───────────────────────────────────────────
    yield "[*] Prüfe externe Tools..."
    tool_ok: list[tuple] = []
    tool_warn: list[tuple] = []
    tool_fail: list[tuple] = []

    for binary, level, cat, desc, install in EXTERNAL_TOOLS:
        found = shutil.which(binary) is not None
        if found:
            tool_ok.append((binary, cat, desc))
        elif level == "warn":
            tool_warn.append((binary, cat, desc, install))
        else:
            tool_fail.append((binary, cat, desc, install))

    yield f"  Tools: {len(tool_ok)} ✓  |  {len(tool_warn)} optional fehlt  |  {len(tool_fail)} kritisch fehlt"

    # ── Pip Module ─────────────────────────────────────────────────────────────
    yield "[*] Prüfe Python-Pakete (pip)..."
    pip_ok, pip_fail = [], []
    for pkg, desc in PIP_MODULES:
        try:
            importlib.import_module(pkg)
            pip_ok.append((pkg, desc))
        except ImportError:
            pip_fail.append((pkg, desc))

    yield f"  pip: {len(pip_ok)} ✓  |  {len(pip_fail)} fehlt"

    # ── System-Checks ──────────────────────────────────────────────────────────
    yield "[*] Prüfe System..."

    is_root = os.geteuid() == 0
    yield f"  Root-Rechte: {'✓ JA' if is_root else '✗ NEIN — sudo -E python3 classic_menu.py'}"

    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        yield f"  Hostname: {hostname}  |  IP: {local_ip}"
    except Exception:
        pass

    # Wordlists
    rockyou = "/usr/share/wordlists/rockyou.txt"
    if os.path.exists(rockyou):
        size = os.path.getsize(rockyou) // 1024 // 1024
        yield f"  rockyou.txt: ✓ ({size} MB)"
    elif os.path.exists(rockyou + ".gz"):
        yield f"  rockyou.txt: ~ komprimiert → gunzip {rockyou}.gz"
    else:
        yield f"  rockyou.txt: ✗ nicht gefunden"

    # Disk Space
    try:
        stat = os.statvfs("/")
        free_gb = stat.f_bavail * stat.f_frsize / 1024**3
        color = "✓" if free_gb > 10 else ("~" if free_gb > 3 else "✗")
        yield f"  Disk (frei): {color} {free_gb:.1f} GB"
    except Exception:
        pass

    # ── Sonderchecks ──────────────────────────────────────────────────────────
    yield "[*] Sonderchecks..."

    # Ollama
    if shutil.which("ollama"):
        try:
            proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            models = [l.split()[0] for l in proc.stdout.strip().split("\n")[1:] if l.strip()]
            if models:
                yield f"  Ollama: ✓ Modelle: {', '.join(models[:3])}"
            else:
                yield f"  Ollama: ~ installiert, kein Modell → ollama pull llama3.2"
        except Exception:
            yield f"  Ollama: ~ installiert (kein Status)"
    else:
        yield f"  Ollama: ✗ nicht installiert → curl -fsSL https://ollama.com/install.sh | sh"

    # dalfox PATH
    if shutil.which("dalfox"):
        yield "  dalfox: ✓ im PATH"
    elif os.path.exists(os.path.expanduser("~/go/bin/dalfox")):
        yield "  dalfox: ~ ~/go/bin/dalfox vorhanden → PATH fehlt"
        yield "         Fix: echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc && source ~/.bashrc"
    else:
        yield "  dalfox: ✗ nicht installiert → go install github.com/hahwul/dalfox/v2@latest"

    # Evilginx
    if shutil.which("evilginx"):
        yield "  evilginx: ✓ im PATH"
    elif os.path.exists(os.path.expanduser("~/go/bin/evilginx")):
        yield "  evilginx: ~ ~/go/bin/evilginx vorhanden → PATH fehlt"
    else:
        yield "  evilginx: ~ nicht installiert → go install github.com/kgretzky/evilginx/v3@latest"

    # impacket
    try:
        importlib.import_module("impacket")
        yield "  impacket: ✓ (Python-Bibliothek)"
    except ImportError:
        if shutil.which("impacket-psexec"):
            yield "  impacket: ✓ (System-Paket)"
        else:
            yield "  impacket: ✗ → apt install python3-impacket"

    # Evilginx Phishlets
    phishlets_dir = os.path.expanduser("~/.evilginx/phishlets")
    if os.path.isdir(phishlets_dir) and os.listdir(phishlets_dir):
        count = len([f for f in os.listdir(phishlets_dir) if f.endswith(".yaml")])
        yield f"  Evilginx Phishlets: ✓ {count} Phishlets in {phishlets_dir}"
    else:
        yield f"  Evilginx Phishlets: ~ fehlen → git clone https://github.com/An0nUD4Y/Evilginx2-Phishlets {phishlets_dir}"

    # Go-Tools PATH check
    go_bin = os.path.expanduser("~/go/bin")
    go_tools = ["subfinder", "httpx", "nuclei", "amass", "gowitness"]
    missing_go = [t for t in go_tools if not shutil.which(t) and not os.path.exists(os.path.join(go_bin, t))]
    if missing_go:
        yield f"  Go-Tools fehlen: {', '.join(missing_go)}"
        yield f"  → PATH prüfen: export PATH=$PATH:~/go/bin"
    else:
        present = [t for t in go_tools if shutil.which(t) or os.path.exists(os.path.join(go_bin, t))]
        yield f"  Go-Tools: ✓ {', '.join(present)}"

    # nuclei Templates
    nuclei_tpl = os.path.expanduser("~/.local/nuclei-templates")
    nuclei_tpl2 = os.path.expanduser("~/nuclei-templates")
    if os.path.isdir(nuclei_tpl) or os.path.isdir(nuclei_tpl2):
        yield "  Nuclei Templates: ✓ vorhanden"
    else:
        yield "  Nuclei Templates: ~ fehlen → nuclei -update-templates"

    # Web UI check
    try:
        importlib.import_module("nicegui")
        yield "  Web UI (NiceGUI): ✓ → python3 web_app.py → http://localhost:8080"
    except ImportError:
        yield "  Web UI (NiceGUI): ~ nicht installiert → pip3 install nicegui --break-system-packages"

    # ── Detaillierter Report ───────────────────────────────────────────────────
    yield ""
    yield "═" * 62

    # Nach Kategorie gruppieren
    from collections import defaultdict
    by_cat: dict[str, list] = defaultdict(list)
    for t in tool_ok:
        by_cat[t[1]].append(t)

    for cat in ["Basis", "WiFi", "Passwörter", "Netzwerk", "Web", "MITM",
                "AD/Lateral", "Metasploit", "OSINT", "Phishing", "C2", "Mobile",
                "Cloud", "Recon", "AD", "AI"]:
        items = by_cat.get(cat, [])
        if items:
            yield f"✓ {cat}: {', '.join(b for b, _, _ in items)}"

    if tool_warn:
        yield ""
        yield "~ OPTIONALE TOOLS (nicht installiert):"
        for binary, cat, desc, install in tool_warn:
            yield f"  ~  {binary:<22} [{cat}]  {desc}"
            yield f"       {install}"

    if tool_fail:
        yield ""
        yield "✗ FEHLENDE TOOLS (kritisch):"
        for binary, cat, desc, install in tool_fail:
            yield f"  ✗  {binary:<22} [{cat}]  {desc}"
            yield f"       {install}"

    if pip_fail:
        yield ""
        yield "~ FEHLENDE PIP-PAKETE:"
        for pkg, desc in pip_fail:
            yield f"  ~  {pkg:<22} {desc}"
            yield f"       pip3 install {pkg} --break-system-packages"

    if failed_modules:
        yield ""
        yield "✗ PYTHON-MODUL FEHLER:"
        for mod, desc, err in failed_modules:
            yield f"  ✗  {mod:<35} {desc}"

    yield ""
    yield "═" * 62
    total_ok = len(tool_ok)
    total = len(EXTERNAL_TOOLS)
    pct = int(total_ok / total * 100)
    yield f"GESAMT: {total_ok}/{total} Tools ({pct}%)  |  {len(pip_ok)}/{len(PIP_MODULES)} pip-Pakete"
    if pct >= 90:
        yield "🏆 Exzellent — fast alles verfügbar!"
    elif pct >= 70:
        yield "✓ Gut — Kernfunktionen alle verfügbar."
    elif pct >= 50:
        yield "~ Basis funktioniert — optionale Tools installieren."
    else:
        yield "✗ Viele Tools fehlen — apt update && apt upgrade empfohlen."
    yield "═" * 62

    # ── Reliability Guide ─────────────────────────────────────────────────────
    yield ""
    yield "═" * 62
    yield "WANN KLAPPEN DIE TOOLS — EHRLICHER GUIDE:"
    yield "═" * 62
    yield ""
    yield "✅ IMMER ZUVERLÄSSIG:"
    yield "  Hashcat / John       — Offline, lokal. Klappt immer wenn Hash korrekt."
    yield "  Hydra                — Klappt immer. Nur langsam bei Rate-Limiting."
    yield "  Nmap                 — Klappt immer. Root für SYN-Scan nötig."
    yield "  Phishing Server      — Reines Python. Klappt 100%."
    yield "  AMSI/ETW Bypass PS1  — Generierter Code. Klappt auf Win 10/11."
    yield "  Telegram C2 Agent    — Klappt wenn Token + Chat-ID stimmt."
    yield "  UAC Bypass           — fodhelper/computerdefaults: Win10/11 meist zuverlässig."
    yield "  WiFi Passwords PS1   — netsh wlan: klappt immer (kein Admin nötig)."
    yield "  Browser Passwords    — DPAPI: klappt für Chrome v79 und älter direkt."
    yield "                          Chrome v80+: Master Key nötig → Telegram Agent nutzen."
    yield "  Keylogger PS1        — SetWindowsHookEx: klappt auf Win 10/11 ohne Admin."
    yield "  Screenshot PS1       — System.Windows.Forms: klappt immer."
    yield "  WiFi PTH/Crack       — klappt wenn Handshake aufgezeichnet + schwaches PW."
    yield ""
    yield "⚠️  MEISTENS — aber mit Bedingungen:"
    yield "  WiFi Handshake       — ✓ wenn Client aktiv verbunden ist."
    yield "                          ✗ kein Client → kein Handshake (dann PMKID versuchen)."
    yield "  PMKID                — ✓ bei ~70% der WPA2-Router. ✗ bei WPA3 / neueren APs."
    yield "  Pass-the-Hash        — ✓ wenn SMB-Signing deaktiviert. ✗ mit SMB-Signing."
    yield "  NTLM Relay           — ✓ in AD ohne SMB-Signing + ohne EPA."
    yield "                          ✗ wenn SMB-Signing erzwungen (moderne AD-Defaults)."
    yield "  Auto-PrivEsc Scanner — ✓ findet echte Vektoren. ✗ wenn System gut gehärtet."
    yield "  UAC Bypass           — ✓ Win10/11 Standard. ✗ Win11 23H2+ mit neuen Defaults."
    yield "  Evilginx 2FA-Bypass  — ✓ wenn Opfer Phishing-Link öffnet + keine Cert-Warning."
    yield "                          ✗ wenn Ziel-Site Advanced AiTM-Detection hat (Cloudflare)."
    yield "  Lateral Movement     — ✓ im internen Netz. ✗ wenn SMB-Firewall aktiv."
    yield "  Responder            — ✓ in alten AD-Netzen. ✗ wenn LLMNR/NBT-NS deaktiviert."
    yield "  Bettercap ARP/SSL    — ✓ im LAN. ✗ wenn Switch Port-Security aktiv."
    yield "  Metasploit Exploits  — ✓ für ungepatchte Systeme. ✗ bei gepatchten Systemen."
    yield "  Process Hollowing    — ✓ Win10 Home/Pro. ✗ Win11 + EDR (CrowdStrike etc.)."
    yield "  Webcam (WIA)         — ✓ auf 90% der Windows-Systeme mit Kamera."
    yield "                          ✗ wenn Kamera durch Gruppenrichtlinie gesperrt."
    yield ""
    yield "🎲  VARIABEL — stark vom Ziel abhängig:"
    yield "  SQLmap               — ✓ wenn echte SQLi vorhanden. ✗ bei WAF ohne Bypass."
    yield "  nikto/nuclei         — ✓ findet bekannte Lücken. ✗ bei gepatchten Servern."
    yield "  Evil Twin            — ✓ wenn Nutzer verbindet + kein 802.1X."
    yield "  Shodan               — ✓ mit API-Key voll nutzbar. ✗ ohne = nur Demos."
    yield "  Snapchat Location    — ✓ wenn Ghost Mode aus. ✗ wenn Ghost Mode an."
    yield "  WhatsApp Online Track— ✓ wenn Datenschutzeinst. 'Alle' zeigt. ✗ bei 'Niemand'."
    yield "  AI Terminal (Ollama) — ✓ wenn Modell installiert. Qualität: llama3.2 > mistral."
    yield ""
    yield "❌  HÄUFIGE FEHLERQUELLEN:"
    yield "  [1] Kein root         → sudo -E python3 classic_menu.py"
    yield "  [2] Monitor-Mode      → airmon-ng start wlan0 (vor WiFi-Angriffen)"
    yield "  [3] rockyou fehlt     → gunzip /usr/share/wordlists/rockyou.txt.gz"
    yield "  [4] dalfox PATH       → echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc"
    yield "  [5] BSSID falsch      → genau so eingeben wie im Scanner (Groß/Kleinschrift!)"
    yield "  [6] SMB-Signing       → netexec smb <ziel> --gen-relay-list targets.txt"
    yield "  [7] Kali veraltet     → apt update && apt full-upgrade"
    yield "  [8] Ollama kein Modell→ ollama pull llama3.2"
    yield "  [9] Evilginx DNS      → Wildcard-DNS: * → Server-IP setzen"
    yield " [10] Chrome PW v80+    → Telegram C2 Agent nutzen (hat direkten DPAPI-Zugriff)"
    yield " [11] Go-Tools kein PATH→ echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc && source ~/.bashrc"
    yield " [12] Nuclei keine Tpl  → nuclei -update-templates"
    yield " [13] Web UI startet nicht → pip3 install nicegui --break-system-packages"
    yield " [14] S3 Enum langsam   → normal, wartet auf HTTP-Timeouts (5s pro Bucket)"
    yield " [15] iOS MDM blockt    → Profil muss HTTPS sein + Let's Encrypt Zertifikat"
    yield "═" * 62
    yield ""
    yield "SCHNELL-INSTALL — alles auf einmal:"
    yield "═" * 62
    yield "  # Basis (apt):"
    yield "  sudo apt install -y nmap aircrack-ng hashcat john hydra ffuf sqlmap nikto"
    yield "  sudo apt install -y bettercap responder netexec adb exploitdb whatweb"
    yield "  sudo apt install -y subfinder amass bloodhound libimobiledevice-utils awscli"
    yield ""
    yield "  # Go-Tools:"
    yield "  go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    yield "  go install github.com/projectdiscovery/httpx/cmd/httpx@latest"
    yield "  go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
    yield "  go install github.com/hahwul/dalfox/v2@latest"
    yield "  go install github.com/kgretzky/evilginx/v3@latest"
    yield "  go install github.com/sensepost/gowitness@latest"
    yield "  nuclei -update-templates"
    yield "  echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc && source ~/.bashrc"
    yield ""
    yield "  # pip3:"
    yield "  pip3 install instaloader pypykatz requests flask bs4 nicegui boto3 pyicloud --break-system-packages"
    yield ""
    yield "  # Ollama (KI):"
    yield "  curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2"
    yield "═" * 62
