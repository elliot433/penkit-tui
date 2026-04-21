#!/usr/bin/env python3
"""
PenKit Web UI — Modern browser interface.
Run:  python3 web_app.py
Open: http://localhost:8080
"""
import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nicegui import ui, app as _app

# ── ANSI → plain text (log widget doesn't do HTML) ───────────────────────────
_ANSI = re.compile(r'\033\[[0-9;]*[mK]')
def strip_ansi(s: str) -> str:
    return _ANSI.sub('', s)


# ── Global output log (shared across tools) ───────────────────────────────────
_output_log: ui.log | None = None
_running = False

async def stream_tool(gen):
    global _running
    _running = True
    if _output_log:
        _output_log.clear()
        _output_log.push("▶  Starting…")
    try:
        async for line in gen:
            if _output_log:
                _output_log.push(strip_ansi(line))
            await asyncio.sleep(0)
    except Exception as e:
        if _output_log:
            _output_log.push(f"[ERROR] {e}")
    finally:
        _running = False
        if _output_log:
            _output_log.push("■  Done.")


# ── Tool registry ─────────────────────────────────────────────────────────────
# Each tool: id, name, icon, badge (🔴/🟠/🟡), desc, inputs[], run lambda
# Input types: text | number | select | password | switch

CATEGORIES = [
    {
        "id": "wifi", "label": "WiFi Attacks", "icon": "wifi", "color": "#f97316",
        "tools": [
            {
                "id": "wifi_scan", "name": "WiFi Scanner", "icon": "radar",
                "badge": "🟠", "desc": "Alle Netzwerke in Reichweite scannen (airodump-ng)",
                "inputs": [
                    {"id": "iface", "label": "Interface", "type": "text", "default": "wlan0"},
                ],
                "run": lambda v: __import__('tools.wifi', fromlist=['WifiScanner']).WifiScanner(v["iface"]).scan(),
            },
            {
                "id": "deauth", "name": "Deauth Attack", "icon": "wifi_off",
                "badge": "🔴", "desc": "Client vom Netzwerk trennen (aireplay-ng)",
                "inputs": [
                    {"id": "iface",  "label": "Interface",    "type": "text", "default": "wlan0mon"},
                    {"id": "bssid",  "label": "BSSID (AP)",   "type": "text", "default": ""},
                    {"id": "client", "label": "Client MAC",   "type": "text", "default": "FF:FF:FF:FF:FF:FF"},
                    {"id": "count",  "label": "Pakete",       "type": "number", "default": 100},
                ],
                "run": lambda v: _deauth(v),
            },
            {
                "id": "handshake", "name": "Handshake Capture", "icon": "handshake",
                "badge": "🔴", "desc": "WPA2-Handshake aufzeichnen → dann cracken",
                "inputs": [
                    {"id": "iface",   "label": "Interface (monitor)", "type": "text", "default": "wlan0mon"},
                    {"id": "bssid",   "label": "BSSID",               "type": "text", "default": ""},
                    {"id": "channel", "label": "Kanal",               "type": "number", "default": 6},
                    {"id": "out",     "label": "Output-Name",         "type": "text", "default": "capture"},
                ],
                "run": lambda v: _handshake(v),
            },
            {
                "id": "evil_twin", "name": "Evil Twin", "icon": "cell_tower",
                "badge": "⛔", "desc": "Gefälschter AP + Captive Portal (Passwörter abgreifen)",
                "inputs": [
                    {"id": "ssid",  "label": "SSID (Netzwerkname)", "type": "text", "default": ""},
                    {"id": "iface", "label": "Interface",           "type": "text", "default": "wlan1"},
                ],
                "run": lambda v: _evil_twin(v),
            },
        ],
    },
    {
        "id": "network", "label": "Network Intel", "icon": "lan", "color": "#3b82f6",
        "tools": [
            {
                "id": "nmap_scan", "name": "Nmap Scanner", "icon": "search",
                "badge": "🟠", "desc": "Ports, Services, OS-Detection, CVE-Check",
                "inputs": [
                    {"id": "target",  "label": "Ziel (IP/CIDR)",        "type": "text", "default": "192.168.1.0/24"},
                    {"id": "profile", "label": "Profil", "type": "select",
                     "options": ["Schnell (-F)", "Standard", "Vollständig (-A)", "Stealth (-sS)", "UDP (-sU)"],
                     "default": "Standard"},
                ],
                "run": lambda v: _nmap(v),
            },
            {
                "id": "auto_exploit", "name": "Auto Exploit Chain", "icon": "auto_fix_high",
                "badge": "⛔", "desc": "Nmap → CVE-Match → Metasploit automatisch",
                "inputs": [
                    {"id": "target", "label": "Ziel-IP", "type": "text", "default": "192.168.1.100"},
                    {"id": "lhost",  "label": "Kali-IP (LHOST)", "type": "text", "default": "192.168.1.50"},
                ],
                "run": lambda v: _import_run('tools.network.auto_exploit', 'auto_exploit_chain', v["target"], v["lhost"]),
            },
            {
                "id": "lateral", "name": "Lateral Movement", "icon": "swap_horiz",
                "badge": "⛔", "desc": "Pass-the-Hash, NTLM Relay, Pivot, SMBExec",
                "inputs": [
                    {"id": "target",   "label": "Ziel-IP",          "type": "text", "default": ""},
                    {"id": "domain",   "label": "Domain",           "type": "text", "default": "WORKGROUP"},
                    {"id": "username", "label": "Username",         "type": "text", "default": "Administrator"},
                    {"id": "nt_hash",  "label": "NT-Hash",          "type": "text", "default": ""},
                    {"id": "kali_ip",  "label": "Kali-IP",          "type": "text", "default": ""},
                    {"id": "lport",    "label": "LPORT",            "type": "number", "default": 4444},
                ],
                "run": lambda v: _import_run('tools.network.lateral_movement', 'pth_wizard',
                                              v["target"], v["domain"], v["username"], "", v["nt_hash"],
                                              v["kali_ip"], int(v["lport"])),
            },
        ],
    },
    {
        "id": "web", "label": "Web Attacks", "icon": "language", "color": "#8b5cf6",
        "tools": [
            {
                "id": "web_fp", "name": "Fingerprinting", "icon": "fingerprint",
                "badge": "🟡", "desc": "Tech-Stack, Server, WAF, CMS, Plugins erkennen",
                "inputs": [
                    {"id": "url", "label": "URL", "type": "text", "default": "https://example.com"},
                ],
                "run": lambda v: _import_run('tools.web.fingerprint', 'fingerprint', v["url"]),
            },
            {
                "id": "sqli", "name": "SQL Injection", "icon": "storage",
                "badge": "🔴", "desc": "SQLmap automatisch — Datenbanken, Tabellen, Dump",
                "inputs": [
                    {"id": "url",    "label": "URL mit Parameter",     "type": "text", "default": ""},
                    {"id": "level",  "label": "Level (1-5)",           "type": "number", "default": 1},
                    {"id": "risk",   "label": "Risk (1-3)",            "type": "number", "default": 1},
                    {"id": "dump",   "label": "Datenbank dumpen",      "type": "switch", "default": False},
                ],
                "run": lambda v: _import_run('tools.web.sqli', 'run_sqlmap', v["url"], int(v["level"]), int(v["risk"]), bool(v["dump"])),
            },
            {
                "id": "fuzzer", "name": "Directory Fuzzer", "icon": "folder_open",
                "badge": "🟠", "desc": "ffuf / gobuster — versteckte Pfade finden",
                "inputs": [
                    {"id": "url",      "label": "URL (mit FUZZ)",          "type": "text", "default": "https://example.com/FUZZ"},
                    {"id": "wordlist", "label": "Wordlist",                "type": "text", "default": "/usr/share/wordlists/dirb/common.txt"},
                    {"id": "ext",      "label": "Erweiterungen (.php,bak)","type": "text", "default": "php,html,txt"},
                    {"id": "threads",  "label": "Threads",                 "type": "number", "default": 50},
                ],
                "run": lambda v: _import_run('tools.web.fuzzer', 'fuzz', v["url"], v["wordlist"], v["ext"], int(v["threads"])),
            },
            {
                "id": "xss", "name": "XSS Scanner", "icon": "code",
                "badge": "🔴", "desc": "Reflected, Stored, DOM XSS — dalfox + custom",
                "inputs": [
                    {"id": "url",    "label": "URL",                  "type": "text", "default": ""},
                    {"id": "param",  "label": "Parameter (optional)", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.web.xss_engine', 'xss_scan', v["url"], v["param"]),
            },
        ],
    },
    {
        "id": "passwords", "label": "Passwords", "icon": "lock_open", "color": "#eab308",
        "tools": [
            {
                "id": "hashcat", "name": "Hashcat GPU", "icon": "bolt",
                "badge": "🟠", "desc": "Hashes cracken mit GPU (WPA2, NTLM, MD5, SHA1...)",
                "inputs": [
                    {"id": "hash_file", "label": "Hash-Datei",    "type": "text", "default": ""},
                    {"id": "wordlist",  "label": "Wordlist",      "type": "text", "default": "/usr/share/wordlists/rockyou.txt"},
                    {"id": "mode",      "label": "Hash-Typ", "type": "select",
                     "options": ["22000 (WPA2)", "1000 (NTLM)", "0 (MD5)", "100 (SHA1)", "1800 (sha512crypt)", "3200 (bcrypt)"],
                     "default": "22000 (WPA2)"},
                    {"id": "rules",     "label": "Rules (best64)", "type": "switch", "default": False},
                ],
                "run": lambda v: _hashcat(v),
            },
            {
                "id": "hydra", "name": "Hydra Brute-Force", "icon": "vpn_key",
                "badge": "🔴", "desc": "Login-Brute-Force gegen SSH, FTP, HTTP, RDP...",
                "inputs": [
                    {"id": "target",   "label": "Ziel-IP",     "type": "text", "default": ""},
                    {"id": "service",  "label": "Dienst", "type": "select",
                     "options": ["ssh", "ftp", "http-post-form", "rdp", "smtp", "mysql", "vnc", "telnet"],
                     "default": "ssh"},
                    {"id": "userlist", "label": "User-Liste",  "type": "text", "default": "/usr/share/wordlists/metasploit/unix_users.txt"},
                    {"id": "passlist", "label": "Pass-Liste",  "type": "text", "default": "/usr/share/wordlists/rockyou.txt"},
                    {"id": "threads",  "label": "Threads",     "type": "number", "default": 16},
                ],
                "run": lambda v: _import_run('tools.passwords.hydra', 'brute', v["target"], v["service"],
                                              v["userlist"], v["passlist"], int(v["threads"])),
            },
            {
                "id": "hash_detect", "name": "Hash Erkennung", "icon": "search",
                "badge": "🟢", "desc": "Hash-Typ automatisch erkennen + Crack-Befehl",
                "inputs": [
                    {"id": "hash_value", "label": "Hash-Wert", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.passwords.hash_detect', 'detect_and_suggest', v["hash_value"]),
            },
        ],
    },
    {
        "id": "osint", "label": "OSINT Recon", "icon": "travel_explore", "color": "#06b6d4",
        "tools": [
            {
                "id": "osint_recon", "name": "Full Recon", "icon": "manage_search",
                "badge": "🟡", "desc": "E-Mail Harvesting, DNS, WHOIS, Subdomains, ASN",
                "inputs": [
                    {"id": "target", "label": "Domain / Name / E-Mail", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.osint.recon', 'full_recon', v["target"]),
            },
            {
                "id": "shodan", "name": "Shodan Lookup", "icon": "satellite_alt",
                "badge": "🟡", "desc": "Shodan — offene Ports, Services, Vuln-Tags",
                "inputs": [
                    {"id": "query",   "label": "IP oder Suchbegriff",   "type": "text", "default": ""},
                    {"id": "api_key", "label": "Shodan API Key",        "type": "password", "default": ""},
                ],
                "run": lambda v: _import_run('tools.osint.shodan_lookup', 'shodan_search', v["query"], v["api_key"]),
            },
            {
                "id": "breach", "name": "Breach Lookup", "icon": "no_encryption",
                "badge": "🟡", "desc": "E-Mail / Domain in bekannten Leaks prüfen (HIBP)",
                "inputs": [
                    {"id": "target", "label": "E-Mail oder Domain", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.osint.breach_lookup', 'check_breach', v["target"]),
            },
            {
                "id": "social", "name": "Social Media OSINT", "icon": "groups",
                "badge": "🟡", "desc": "Instagram, TikTok, Twitter, Snapchat — Profile analysieren",
                "inputs": [
                    {"id": "platform", "label": "Platform", "type": "select",
                     "options": ["instagram", "tiktok", "twitter", "snapchat"],
                     "default": "instagram"},
                    {"id": "username", "label": "Username", "type": "text", "default": ""},
                ],
                "run": lambda v: _social_osint(v),
            },
        ],
    },
    {
        "id": "phishing", "label": "Phishing", "icon": "phishing", "color": "#ef4444",
        "tools": [
            {
                "id": "phish_server", "name": "Phishing Server", "icon": "dns",
                "badge": "⛔", "desc": "Fake Login-Seite starten + Telegram-Alert bei Treffer",
                "inputs": [
                    {"id": "page",     "label": "Seite", "type": "select",
                     "options": ["google", "microsoft", "instagram", "apple", "facebook", "discord", "steam"],
                     "default": "google"},
                    {"id": "port",     "label": "Port",             "type": "number", "default": 80},
                    {"id": "tg_token", "label": "Telegram Token",   "type": "text", "default": ""},
                    {"id": "tg_chat",  "label": "Telegram Chat-ID", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.phishing.server', 'start_server',
                                              v["page"], int(v["port"]), v["tg_token"], v["tg_chat"]),
            },
            {
                "id": "evilginx", "name": "Evilginx 2FA-Bypass", "icon": "security",
                "badge": "⛔", "desc": "Reverse Proxy — Session-Cookie abfangen, 2FA umgehen",
                "inputs": [
                    {"id": "phishlet",  "label": "Phishlet", "type": "select",
                     "options": ["google", "microsoft", "apple", "instagram", "github", "discord", "twitter", "paypal", "amazon"],
                     "default": "google"},
                    {"id": "domain",    "label": "Phishing-Domain", "type": "text", "default": ""},
                    {"id": "server_ip", "label": "Server-IP",       "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.phishing.evilginx', 'evilginx_wizard',
                                              v["phishlet"], v["domain"], v["server_ip"]),
            },
        ],
    },
    {
        "id": "c2", "label": "C2 / RAT", "icon": "bug_report", "color": "#dc2626",
        "tools": [
            {
                "id": "msf_payload", "name": "Payload Builder", "icon": "memory",
                "badge": "⛔", "desc": "msfvenom — Windows/Linux/Android Payloads + AV Bypass",
                "inputs": [
                    {"id": "lhost",   "label": "LHOST (Kali-IP)", "type": "text", "default": ""},
                    {"id": "lport",   "label": "LPORT",           "type": "number", "default": 4444},
                    {"id": "payload", "label": "Payload-Typ", "type": "select",
                     "options": ["windows/x64/meterpreter/reverse_https",
                                 "windows/x64/shell_reverse_tcp",
                                 "linux/x64/meterpreter/reverse_tcp",
                                 "android/meterpreter/reverse_https",
                                 "python/meterpreter/reverse_tcp"],
                     "default": "windows/x64/meterpreter/reverse_https"},
                    {"id": "format",  "label": "Format", "type": "select",
                     "options": ["exe", "exe-service", "dll", "ps1", "vba", "hta-web", "elf", "raw"],
                     "default": "exe"},
                ],
                "run": lambda v: _import_run('tools.network.msf_integration', 'generate_payload_menu',
                                              v["lhost"], int(v["lport"]), v["payload"], v["format"]),
            },
            {
                "id": "uac_bypass", "name": "UAC Bypass Suite", "icon": "shield",
                "badge": "⛔", "desc": "fodhelper, eventvwr, CMSTP, Token Steal, Potato",
                "inputs": [
                    {"id": "method", "label": "Methode", "type": "select",
                     "options": ["fodhelper", "eventvwr", "sdclt", "computerdefaults", "cmstp", "token_steal", "juicy_potato"],
                     "default": "fodhelper"},
                    {"id": "cmd", "label": "Auszuführender Befehl", "type": "text", "default": "cmd.exe"},
                ],
                "run": lambda v: _uac_bypass(v),
            },
            {
                "id": "privesc", "name": "PrivEsc Scanner", "icon": "upgrade",
                "badge": "⛔", "desc": "WinPEAS-ähnlicher Scanner — 15+ Vektoren automatisch",
                "inputs": [
                    {"id": "kali_ip", "label": "Kali-IP (für Exfil)", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.c2.privesc_scanner', 'generate_scanner_ps1', v["kali_ip"], ""),
            },
            {
                "id": "post_exploit", "name": "Spionage Suite", "icon": "visibility",
                "badge": "⛔", "desc": "Keylogger, Screenshot, Webcam, Browser-Passwörter (PS1)",
                "inputs": [
                    {"id": "module", "label": "Modul", "type": "select",
                     "options": ["keylogger", "screenshot", "webcam", "browser_passwords", "wifi_passwords", "clipboard"],
                     "default": "screenshot"},
                    {"id": "tg_token", "label": "Telegram Token (optional)", "type": "text", "default": ""},
                    {"id": "tg_chat",  "label": "Telegram Chat-ID",          "type": "text", "default": ""},
                ],
                "run": lambda v: _post_exploit(v),
            },
        ],
    },
    {
        "id": "recon", "label": "Auto-Recon / CVE", "icon": "radar", "color": "#10b981",
        "tools": [
            {
                "id": "full_pipeline", "name": "Auto-Recon Pipeline", "icon": "auto_awesome",
                "badge": "🔴", "desc": "Domain → Subdomains → Ports → Web → Nuclei → Report",
                "inputs": [
                    {"id": "domain",   "label": "Target-Domain",  "type": "text", "default": ""},
                    {"id": "fast",     "label": "Schnell-Modus",  "type": "switch", "default": False},
                    {"id": "nuclei",   "label": "Nuclei Scan",    "type": "switch", "default": True},
                ],
                "run": lambda v: _import_run('tools.recon.auto_recon', 'full_pipeline',
                                              v["domain"], bool(v["fast"]), not bool(v["nuclei"])),
            },
            {
                "id": "cve_lookup", "name": "CVE Details + EPSS", "icon": "policy",
                "badge": "🟡", "desc": "CVSS Score, Beschreibung, Exploit-Wahrscheinlichkeit",
                "inputs": [
                    {"id": "cve_id", "label": "CVE-Nummer (z.B. CVE-2021-44228)", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.recon.searchsploit_engine', 'cve_lookup', v["cve_id"]),
            },
            {
                "id": "searchsploit", "name": "Searchsploit", "icon": "manage_search",
                "badge": "🔴", "desc": "Exploit-DB Suche nach Software oder CVE",
                "inputs": [
                    {"id": "query", "label": "Suchbegriff (z.B. Apache 2.4.49)", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.recon.searchsploit_engine', 'search_exploit', v["query"]),
            },
        ],
    },
    {
        "id": "cloud", "label": "Cloud Attacks", "icon": "cloud", "color": "#64748b",
        "tools": [
            {
                "id": "s3_enum", "name": "S3 Bucket Enum", "icon": "inventory_2",
                "badge": "🔴", "desc": "Öffentliche AWS S3 Buckets für Unternehmen finden",
                "inputs": [
                    {"id": "company", "label": "Unternehmensname", "type": "text", "default": ""},
                    {"id": "region",  "label": "AWS Region",       "type": "text", "default": "us-east-1"},
                ],
                "run": lambda v: _import_run('tools.cloud.aws_recon', 'enumerate_s3_buckets', v["company"], v["region"]),
            },
            {
                "id": "ec2_creds", "name": "EC2 Metadata Theft", "icon": "key",
                "badge": "⛔", "desc": "169.254.169.254 — IAM-Credentials via SSRF/Shell",
                "inputs": [
                    {"id": "ssrf_url", "label": "SSRF-URL (leer = Anleitung)", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.cloud.aws_recon', 'steal_ec2_credentials', v["ssrf_url"]),
            },
            {
                "id": "github_scan", "name": "GitHub Secret Scan", "icon": "code",
                "badge": "🔴", "desc": "truffleHog / gitleaks — API Keys in Repos finden",
                "inputs": [
                    {"id": "target", "label": "GitHub User oder User/Repo", "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.cloud.aws_recon', 'github_secret_scan', v["target"]),
            },
        ],
    },
    {
        "id": "mobile", "label": "Mobile Attacks", "icon": "smartphone", "color": "#a855f7",
        "tools": [
            {
                "id": "airdrop", "name": "AirDrop Recon", "icon": "bluetooth_searching",
                "badge": "🟡", "desc": "iOS-Gerätename, MAC, SHA256-Hash passiv sniffing",
                "inputs": [],
                "run": lambda v: _import_run('tools.mobile.ios_attack', 'airdrop_recon'),
            },
            {
                "id": "mdm_profile", "name": "MDM Config Profile", "icon": "phonelink_setup",
                "badge": "⛔", "desc": "VPN + Proxy ohne Jailbreak — iOS Traffic interception",
                "inputs": [
                    {"id": "org",       "label": "Organisations-Name", "type": "text", "default": "IT Sicherheit GmbH"},
                    {"id": "domain",    "label": "Phishing-Domain",    "type": "text", "default": "secure-update.net"},
                    {"id": "server_ip", "label": "Server-IP",          "type": "text", "default": ""},
                ],
                "run": lambda v: _import_run('tools.mobile.ios_attack', 'mdm_setup_guide', v["domain"], v["server_ip"]),
            },
            {
                "id": "apk_wizard", "name": "Android APK Wizard", "icon": "android",
                "badge": "⛔", "desc": "Meterpreter APK generieren, signieren, per QR verteilen",
                "inputs": [
                    {"id": "lhost", "label": "LHOST (Kali-IP)", "type": "text", "default": ""},
                    {"id": "lport", "label": "LPORT",           "type": "number", "default": 4444},
                ],
                "run": lambda v: _import_run('tools.mobile.android_attack', 'show_apk_wizard',
                                              v["lhost"], int(v["lport"])),
            },
            {
                "id": "adb", "name": "ADB Exploitation", "icon": "usb",
                "badge": "⛔", "desc": "USB-Debugging + Netzwerk-ADB → Daten, Screenshots, APK",
                "inputs": [],
                "run": lambda v: _import_run('tools.mobile.android_attack', 'adb_exploitation'),
            },
        ],
    },
    {
        "id": "blueteam", "label": "Blue Team", "icon": "shield_moon", "color": "#0ea5e9",
        "tools": [
            {
                "id": "arp_watch", "name": "ARP Watch", "icon": "monitor_heart",
                "badge": "🟢", "desc": "ARP-Spoofing erkennen — Alarm bei neuem Gerät",
                "inputs": [
                    {"id": "iface", "label": "Interface", "type": "text", "default": "eth0"},
                ],
                "run": lambda v: _import_run('tools.blueteam.arp_watch', 'watch', v["iface"]),
            },
            {
                "id": "honeypot", "name": "Honeypot", "icon": "pest_control",
                "badge": "🟢", "desc": "Fake SSH/FTP/HTTP — loggt alle Verbindungsversuche",
                "inputs": [
                    {"id": "port",    "label": "Port",    "type": "number", "default": 22},
                    {"id": "service", "label": "Dienst", "type": "select",
                     "options": ["ssh", "ftp", "http", "smtp"],
                     "default": "ssh"},
                ],
                "run": lambda v: _import_run('tools.blueteam.honeypot', 'start_honeypot',
                                              v["service"], int(v["port"])),
            },
        ],
    },
]


# ── Tool helper runners ───────────────────────────────────────────────────────

async def _import_run(module_path, func_name, *args):
    import importlib
    mod = importlib.import_module(module_path)
    fn  = getattr(mod, func_name)
    result = fn(*args)
    if hasattr(result, '__aiter__'):
        async for line in result:
            yield line
    else:
        yield str(result)

async def _deauth(v):
    from tools.wifi import WifiScanner
    async for line in WifiScanner(v["iface"]).deauth(v["bssid"], v["client"], int(v["count"])):
        yield line

async def _handshake(v):
    from tools.wifi import WifiScanner
    async for line in WifiScanner(v["iface"]).capture_handshake(v["bssid"], int(v["channel"]), v["out"]):
        yield line

async def _evil_twin(v):
    from tools.wifi.evil_twin import EvilTwin
    async for line in EvilTwin(v["iface"], v["ssid"]).start():
        yield line

async def _nmap(v):
    profile_map = {
        "Schnell (-F)": "fast",
        "Standard": "standard",
        "Vollständig (-A)": "full",
        "Stealth (-sS)": "stealth",
        "UDP (-sU)": "udp",
    }
    from tools.network.scanner import NetworkScanner
    async for line in NetworkScanner().scan(v["target"], profile_map.get(v["profile"], "standard")):
        yield line

async def _hashcat(v):
    mode = v["mode"].split()[0]
    from tools.passwords.hashcat import run_hashcat
    async for line in run_hashcat(v["hash_file"], v["wordlist"], mode, bool(v["rules"])):
        yield line

async def _social_osint(v):
    from tools.osint import social_osint
    platform = v["platform"]
    username = v["username"]
    if platform == "instagram":
        async for line in social_osint.instagram_recon(username):
            yield line
    elif platform == "tiktok":
        async for line in social_osint.tiktok_recon(username):
            yield line
    elif platform == "twitter":
        async for line in social_osint.twitter_recon(username):
            yield line
    elif platform == "snapchat":
        async for line in social_osint.snapchat_profile(username):
            yield line

async def _uac_bypass(v):
    from tools.c2 import uac_bypass
    method_map = {
        "fodhelper":        uac_bypass.uac_fodhelper,
        "eventvwr":         uac_bypass.uac_eventvwr,
        "sdclt":            uac_bypass.uac_sdclt,
        "computerdefaults": uac_bypass.uac_computerdefaults,
        "token_steal":      uac_bypass.uac_token_steal,
        "juicy_potato":     uac_bypass.uac_juicy_potato,
    }
    fn = method_map.get(v["method"], uac_bypass.uac_fodhelper)
    result = fn(v["cmd"])
    if isinstance(result, str):
        for line in result.splitlines():
            yield line
    else:
        async for line in result:
            yield line

async def _post_exploit(v):
    from tools.c2 import post_exploit
    mod_map = {
        "keylogger":         post_exploit.keylogger_ps1,
        "screenshot":        post_exploit.screenshot_ps1,
        "webcam":            post_exploit.webcam_ps1,
        "browser_passwords": post_exploit.browser_passwords_ps1,
        "wifi_passwords":    post_exploit.wifi_passwords_ps1,
        "clipboard":         post_exploit.clipboard_monitor_ps1,
    }
    fn = mod_map.get(v["module"], post_exploit.screenshot_ps1)
    result = fn(v.get("tg_token",""), v.get("tg_chat",""))
    for line in result.splitlines():
        yield line


# ── Build input widget and return value-getter ────────────────────────────────

def build_inputs(inputs: list) -> dict:
    """Renders input widgets and returns a dict of {id: ui_element}."""
    widgets = {}
    for inp in inputs:
        itype   = inp.get("type", "text")
        label   = inp["label"]
        default = inp.get("default", "")
        iid     = inp["id"]

        if itype == "text":
            w = ui.input(label=label, value=str(default)).classes('w-full')
        elif itype == "password":
            w = ui.input(label=label, value=str(default), password=True).classes('w-full')
        elif itype == "number":
            w = ui.number(label=label, value=default).classes('w-full')
        elif itype == "select":
            opts = inp.get("options", [])
            w = ui.select(options=opts, label=label, value=default).classes('w-full')
        elif itype == "switch":
            w = ui.switch(text=label, value=bool(default))
        else:
            w = ui.input(label=label, value=str(default)).classes('w-full')

        widgets[iid] = w
    return widgets


def get_values(widgets: dict) -> dict:
    result = {}
    for k, w in widgets.items():
        result[k] = w.value
    return result


# ── Main UI ───────────────────────────────────────────────────────────────────

BADGE_COLOR = {"🟢": "#22c55e", "🟡": "#eab308", "🟠": "#f97316", "🔴": "#ef4444", "⛔": "#dc2626"}
DANGER_TEXT  = {"🟢": "Low", "🟡": "Medium", "🟠": "High", "🔴": "Critical", "⛔": "Root Only"}

@ui.page('/')
def main_page():
    global _output_log

    ui.add_head_html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    """)

    ui.add_css("""
    :root {
        --bg-primary:   #070b14;
        --bg-sidebar:   #0b1020;
        --bg-card:      #0f1929;
        --bg-card-hover:#131f33;
        --bg-terminal:  #020408;
        --accent:       #00ff88;
        --accent-dim:   #00cc6a;
        --danger:       #ff4444;
        --warn:         #ffaa00;
        --text:         #e2e8f0;
        --text-dim:     #64748b;
        --border:       #1a2744;
    }
    body, .nicegui-content { background: var(--bg-primary) !important; font-family: 'Inter', sans-serif !important; }
    .q-drawer { background: var(--bg-sidebar) !important; border-right: 1px solid var(--border) !important; }
    .penkit-logo { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 600;
                   background: linear-gradient(135deg, #00ff88, #00aaff); -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent; letter-spacing: 3px; }
    .cat-item { display: flex; align-items: center; gap: 10px; padding: 10px 16px;
                border-radius: 8px; cursor: pointer; color: var(--text-dim);
                transition: all 0.2s; font-size: 13px; font-weight: 500; margin: 2px 8px; }
    .cat-item:hover { background: var(--bg-card); color: var(--text); }
    .cat-item.active { background: rgba(0,255,136,0.1); color: var(--accent);
                       border-left: 3px solid var(--accent); padding-left: 13px; }
    .tool-card { background: var(--bg-card) !important; border: 1px solid var(--border) !important;
                 border-radius: 12px !important; cursor: pointer !important;
                 transition: all 0.2s !important; padding: 0 !important; }
    .tool-card:hover { border-color: var(--accent) !important; transform: translateY(-2px);
                       box-shadow: 0 8px 24px rgba(0,255,136,0.1) !important; }
    .tool-name { font-weight: 600; color: var(--text); font-size: 14px; }
    .tool-desc { color: var(--text-dim); font-size: 12px; line-height: 1.5; margin-top: 4px; }
    .badge-pill { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 99px;
                  letter-spacing: 0.5px; }
    .terminal-out { background: var(--bg-terminal) !important; font-family: 'JetBrains Mono', monospace !important;
                    font-size: 12px !important; color: #00ff88 !important;
                    border: 1px solid var(--border) !important; border-radius: 8px !important; }
    .q-dialog .q-card { background: var(--bg-card) !important; border: 1px solid var(--border) !important;
                         border-radius: 16px !important; }
    .q-field__label { color: var(--text-dim) !important; }
    .q-field__native { color: var(--text) !important; }
    .q-field__control { background: var(--bg-sidebar) !important; }
    .run-btn { background: linear-gradient(135deg, #00ff88, #00cc6a) !important;
               color: #000 !important; font-weight: 700 !important; font-size: 13px !important;
               border-radius: 8px !important; }
    .section-title { font-size: 22px; font-weight: 600; color: var(--text); letter-spacing: 0.5px; }
    .section-sub   { font-size: 13px; color: var(--text-dim); margin-top: 4px; }
    .q-scrollarea__content { padding: 0 !important; }
    """)

    # ── State ─────────────────────────────────────────────────────────────────
    active_cat = {'id': CATEGORIES[0]['id']}

    # ── Layout ────────────────────────────────────────────────────────────────
    with ui.left_drawer(fixed=True, elevated=False).style('width:220px'):
        # Logo
        with ui.element('div').style('padding: 20px 16px 12px'):
            ui.html('<div class="penkit-logo">PENKIT</div>')
            ui.html('<div style="color:#64748b;font-size:11px;margin-top:2px;font-family:JetBrains Mono">v3.0 · Web UI</div>')

        ui.separator().style('border-color: #1a2744; margin: 8px 0')

        # Category nav
        cat_buttons: dict[str, ui.element] = {}
        content_area = None  # forward ref

        def make_nav_click(cat_id):
            def click():
                active_cat['id'] = cat_id
                for cid, el in cat_buttons.items():
                    el.classes(replace='cat-item active' if cid == cat_id else 'cat-item')
                render_category(cat_id)
            return click

        for cat in CATEGORIES:
            with ui.element('div').classes('cat-item').on('click', make_nav_click(cat['id'])) as btn:
                ui.icon(cat['icon']).style(f'color:{cat["color"]};font-size:18px')
                ui.label(cat['label']).style('flex:1')
            cat_buttons[cat['id']] = btn

        # set first active
        cat_buttons[CATEGORIES[0]['id']].classes(add='active')

        ui.separator().style('border-color: #1a2744; margin: 8px 0')

        # Quick links
        def start_classic():
            ui.notify('Starte classic_menu.py im Terminal: python3 classic_menu.py', type='info', timeout=5000)

        ui.element('div').classes('cat-item').on('click', start_classic).style('margin-top:auto') \
            .add(ui.icon('terminal').style('color:#64748b;font-size:18px')) \
            .add(ui.label('Classic TUI').style('color:#64748b;font-size:13px'))

    # ── Main content ──────────────────────────────────────────────────────────
    with ui.column().classes('w-full').style('padding: 24px; gap: 0'):

        # Header row
        with ui.row().classes('w-full items-center').style('margin-bottom:24px; gap: 12px'):
            header_title = ui.html('<div class="section-title">WiFi Attacks</div>')
            header_sub   = ui.html('<div class="section-sub">Netzwerke scannen, Handshakes, Evil Twin</div>')
            ui.space()
            status_badge = ui.html('<div style="background:rgba(0,255,136,0.1);border:1px solid #00ff88;'
                                   'color:#00ff88;font-size:11px;padding:4px 12px;border-radius:99px;'
                                   'font-family:JetBrains Mono">● READY</div>')

        # Tool cards grid
        cards_area = ui.element('div').style(
            'display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px'
        )

        # Terminal output panel
        ui.separator().style('border-color:#1a2744;margin:24px 0 16px')
        with ui.row().classes('w-full items-center').style('margin-bottom:8px'):
            ui.html('<div style="color:#64748b;font-size:12px;font-family:JetBrains Mono">OUTPUT TERMINAL</div>')
            ui.space()
            ui.button('Clear', on_click=lambda: _output_log.clear() if _output_log else None) \
              .style('background:transparent;color:#64748b;border:1px solid #1a2744;'
                     'font-size:11px;padding:2px 10px;border-radius:6px')

        _output_log = ui.log(max_lines=500).classes('w-full terminal-out').style('height:280px')

    # ── Render function ───────────────────────────────────────────────────────
    def render_category(cat_id: str):
        cat = next((c for c in CATEGORIES if c['id'] == cat_id), CATEGORIES[0])
        header_title.set_content(f'<div class="section-title">{cat["label"]}</div>')
        header_sub.set_content(f'<div class="section-sub">{len(cat["tools"])} Tools verfügbar</div>')

        cards_area.clear()
        with cards_area:
            for tool in cat['tools']:
                badge_col = BADGE_COLOR.get(tool['badge'], '#64748b')
                danger_txt = DANGER_TEXT.get(tool['badge'], '')

                with ui.card().classes('tool-card').on('click', make_tool_click(tool)):
                    with ui.element('div').style('padding:16px'):
                        with ui.row().classes('items-center').style('margin-bottom:10px;gap:8px'):
                            ui.icon(tool['icon']).style(f'color:{cat["color"]};font-size:20px')
                            ui.html(f'<div class="tool-name">{tool["name"]}</div>')
                            ui.space()
                            ui.html(f'<div class="badge-pill" style="background:{badge_col}22;color:{badge_col}">'
                                    f'{danger_txt}</div>')
                        ui.html(f'<div class="tool-desc">{tool["desc"]}</div>')

    def make_tool_click(tool: dict):
        async def click():
            with ui.dialog().props('maximized=false persistent') as dialog, \
                 ui.card().style('min-width:520px;max-width:700px;padding:24px'):

                # Dialog header
                with ui.row().classes('w-full items-center').style('margin-bottom:16px'):
                    ui.icon(tool['icon']).style('font-size:24px;color:var(--accent)')
                    ui.html(f'<div style="font-size:18px;font-weight:600;color:#e2e8f0;margin-left:8px">'
                            f'{tool["name"]}</div>')
                    ui.space()
                    ui.button(icon='close', on_click=dialog.close) \
                      .style('background:transparent;color:#64748b')

                ui.html(f'<div style="color:#64748b;font-size:13px;margin-bottom:20px">{tool["desc"]}</div>')
                ui.separator().style('border-color:#1a2744;margin-bottom:16px')

                # Inputs
                widgets = {}
                if tool['inputs']:
                    with ui.column().classes('w-full').style('gap:12px'):
                        widgets = build_inputs(tool['inputs'])
                else:
                    ui.html('<div style="color:#64748b;font-size:13px;margin-bottom:8px">Keine Eingaben nötig.</div>')

                ui.separator().style('border-color:#1a2744;margin:16px 0')

                # Run button
                run_btn = ui.button('▶  AUSFÜHREN', on_click=None).classes('run-btn w-full')

                async def do_run():
                    values = get_values(widgets)
                    dialog.close()
                    _output_log.clear()
                    _output_log.push(f"▶ {tool['name']} gestartet…")
                    status_badge.set_content(
                        '<div style="background:rgba(255,170,0,0.1);border:1px solid #ffaa00;'
                        'color:#ffaa00;font-size:11px;padding:4px 12px;border-radius:99px;'
                        'font-family:JetBrains Mono">● RUNNING</div>'
                    )
                    try:
                        gen = tool['run'](values)
                        async for line in gen:
                            _output_log.push(strip_ansi(line))
                            await asyncio.sleep(0)
                    except Exception as e:
                        _output_log.push(f"[ERROR] {e}")
                    finally:
                        status_badge.set_content(
                            '<div style="background:rgba(0,255,136,0.1);border:1px solid #00ff88;'
                            'color:#00ff88;font-size:11px;padding:4px 12px;border-radius:99px;'
                            'font-family:JetBrains Mono">● READY</div>'
                        )

                run_btn.on('click', do_run)
            dialog.open()

        return click

    # Initial render
    render_category(CATEGORIES[0]['id'])


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n  \033[92mPenKit Web UI\033[0m")
    print("  \033[90mhttp://localhost:8080\033[0m\n")
    ui.run(
        host='127.0.0.1',
        port=8080,
        title='PenKit v3',
        favicon='🛡️',
        dark=True,
        reload=False,
        show=False,
    )
