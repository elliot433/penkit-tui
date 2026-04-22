"""
PenKit MITRE ATT&CK Mapper

Zeigt für jedes PenKit-Tool die zugehörigen ATT&CK Taktiken und Techniken.
Nützlich für:
  - Pentest-Reports (professionelles Tagging)
  - Lernzwecke (verstehen was man eigentlich macht)
  - Compliance / Red-Team-Dokumentation
"""

from __future__ import annotations
from typing import AsyncGenerator

# ── Datenstruktur ─────────────────────────────────────────────────────────────
# (tool_name, kategorie, tactic_id, tactic_name, technique_id, technique_name, kurzbeschreibung)

MAPPINGS: list[tuple[str, str, str, str, str, str, str]] = [
    # ── Reconnaissance ────────────────────────────────────────────────────────
    ("theHarvester",   "OSINT",   "TA0043", "Reconnaissance",      "T1589", "Gather Victim Identity Info", "E-Mails, Namen, Subdomains sammeln"),
    ("Shodan",         "OSINT",   "TA0043", "Reconnaissance",      "T1596", "Search Open Technical DB",    "Shodan/Censys nach exponierten Services"),
    ("OSINT Recon",    "OSINT",   "TA0043", "Reconnaissance",      "T1591", "Gather Victim Org Info",      "LinkedIn, GitHub, breach databases"),
    ("subfinder/amass","OSINT",   "TA0043", "Reconnaissance",      "T1590", "Gather Victim Network Info",  "Subdomain-Enumeration"),
    ("Auto-Recon",     "Recon",   "TA0043", "Reconnaissance",      "T1595", "Active Scanning",             "Nuclei + httpx + subfinder Pipeline"),

    # ── Resource Development ──────────────────────────────────────────────────
    ("Payload Builder","C2",      "TA0042", "Resource Development","T1587", "Develop Capabilities",        "Eigene Payloads / Shellcode bauen"),
    ("Phishing Pages", "Phishing","TA0042", "Resource Development","T1583", "Acquire Infrastructure",      "Fake-Login-Seiten hosten"),
    ("GoPhish",        "Phishing","TA0042", "Resource Development","T1586", "Compromise Accounts",         "Phishing-Kampagnen über GoPhish"),

    # ── Initial Access ────────────────────────────────────────────────────────
    ("Phishing Server","Phishing","TA0001", "Initial Access",      "T1566", "Phishing",                    "Credential Harvest via Fake Login"),
    ("Evilginx",       "Phishing","TA0001", "Initial Access",      "T1566.002","Spearphishing Link",       "2FA-Bypass via Session-Token-Klau"),
    ("BitB Phishing",  "Phishing","TA0001", "Initial Access",      "T1566.002","Spearphishing Link",       "Browser-in-the-Browser Popup"),
    ("Evil Twin",      "WiFi",    "TA0001", "Initial Access",      "T1465", "Rogue Wi-Fi AP",              "Fake AP + Captive Portal"),
    ("Email Kampagne", "Phishing","TA0001", "Initial Access",      "T1566.001","Spearphishing Attachment",  "HTML/Payload per SMTP"),
    ("EternalBlue",    "Network", "TA0001", "Initial Access",      "T1190", "Exploit Public-Facing App",   "MS17-010 SMB RCE"),
    ("Auto-Exploit",   "Network", "TA0001", "Initial Access",      "T1190", "Exploit Public-Facing App",   "CVE-basierter Exploit-Vorschlag"),

    # ── Execution ─────────────────────────────────────────────────────────────
    ("AMSI Bypass",    "C2",      "TA0002", "Execution",           "T1059.001","PowerShell",               "AMSI/ETW patchen → PS unerkannt"),
    ("Process Hollow", "C2",      "TA0002", "Execution",           "T1055.012","Process Hollowing",         "Shellcode in legitimen Prozess"),
    ("Shellcode Engine","C2",     "TA0002", "Execution",           "T1059.001","PowerShell",               "Polymorphic Shellcode generieren"),
    ("UAC Bypass",     "C2",      "TA0002", "Execution",           "T1548.002","Bypass UAC",               "UAC-Bypass für elevated execution"),
    ("Metasploit",     "Network", "TA0002", "Execution",           "T1059",  "Command & Scripting",        "MSF payloads + meterpreter"),
    ("AI Terminal",    "C2",      "TA0002", "Execution",           "T1059",  "Command & Scripting",        "KI wählt + führt Befehle aus"),

    # ── Persistence ──────────────────────────────────────────────────────────
    ("Post-Exploit: Reg","C2",   "TA0003", "Persistence",         "T1547.001","Registry Run Keys",         "HKCU\\Run → Autostart"),
    ("Post-Exploit: Task","C2",  "TA0003", "Persistence",         "T1053.005","Scheduled Task",            "Scheduled Task anlegen"),
    ("Post-Exploit: Svc","C2",   "TA0003", "Persistence",         "T1543.003","Windows Service",           "Malicious Windows Service"),

    # ── Privilege Escalation ──────────────────────────────────────────────────
    ("UAC Bypass",     "C2",      "TA0004", "Privilege Escalation","T1548.002","Bypass UAC",               "Privilege Escalation via UAC-Bypass"),
    ("PrivEsc Scanner","C2",      "TA0004", "Privilege Escalation","T1068",  "Exploit Priv Escalation",    "WinPEAS / auto privesc check"),
    ("Token Impersonation","AD",  "TA0004", "Privilege Escalation","T1134",  "Access Token Manipulation",  "Token Impersonation / Delegation"),
    ("Kerberoasting",  "AD",      "TA0004", "Privilege Escalation","T1558.003","Kerberoasting",             "SPN-Tickets offline cracken"),

    # ── Defense Evasion ───────────────────────────────────────────────────────
    ("AMSI Bypass",    "C2",      "TA0005", "Defense Evasion",     "T1562.001","Impair Defenses: AMSI",     "AMSI + ETW blind schalten"),
    ("Disguise Tool",  "C2",      "TA0005", "Defense Evasion",     "T1036.005","Match Legit Name/Location", "EXE tarnt sich als PDF/Bild"),
    ("Process Hollow", "C2",      "TA0005", "Defense Evasion",     "T1055.012","Process Hollowing",         "Shellcode in svchost.exe"),
    ("OPSEC Suite",    "OPSEC",   "TA0005", "Defense Evasion",     "T1070",  "Indicator Removal",          "Logs löschen, Session Wipe"),
    ("Tor / Anon",     "OPSEC",   "TA0005", "Defense Evasion",     "T1090.003","Multi-hop Proxy",           "Traffic über Tor leiten"),
    ("MAC Spoofing",   "OPSEC",   "TA0005", "Defense Evasion",     "T1562",  "Impair Defenses",            "MAC-Adresse vor Scan ändern"),

    # ── Credential Access ─────────────────────────────────────────────────────
    ("Handshake Capture","WiFi",  "TA0006", "Credential Access",   "T1040",  "Network Sniffing",           "WPA2-Handshake sniffing"),
    ("PMKID Attack",   "WiFi",    "TA0006", "Credential Access",   "T1040",  "Network Sniffing",           "PMKID clientlos sammeln"),
    ("Hashcat",        "Passwords","TA0006","Credential Access",   "T1110.002","Password Cracking",         "GPU-Cracking via Wordlist/Rules"),
    ("Hydra",          "Passwords","TA0006","Credential Access",   "T1110.001","Brute Force",               "Online Brute-Force"),
    ("Responder",      "MITM",    "TA0006", "Credential Access",   "T1557.001","LLMNR/NBT-NS Poisoning",    "NTLMv2-Hashes aus Netz fangen"),
    ("Post-Exploit: Creds","C2",  "TA0006", "Credential Access",   "T1555.003","Credentials from Browser",  "Browser-Passwörter + Cookies"),
    ("Mimikatz/LSASS", "AD",      "TA0006", "Credential Access",   "T1003.001","LSASS Memory",              "Plaintext-Creds aus RAM"),
    ("DCSync",         "AD",      "TA0006", "Credential Access",   "T1003.006","DCSync",                    "Domain-Admin Hash via Replikation"),
    ("WiFi Passwords", "C2",      "TA0006", "Credential Access",   "T1555",  "Credentials from Stores",    "Gespeicherte WiFi-Passwörter"),

    # ── Discovery ─────────────────────────────────────────────────────────────
    ("Nmap Scanner",   "Network", "TA0007", "Discovery",           "T1046",  "Network Service Scanning",   "Port-/Service-/OS-Scan"),
    ("Topology Mapper","Network", "TA0007", "Discovery",           "T1018",  "Remote System Discovery",    "Netzwerk-Topologie-Karte"),
    ("BloodHound",     "AD",      "TA0007", "Discovery",           "T1069.002","Domain Groups",             "AD Angriffspfade visualisieren"),
    ("IoT Scanner",    "Network", "TA0007", "Discovery",           "T1046",  "Network Service Scanning",   "IP-Cams, Router, IPMI entdecken"),
    ("Post-Exploit: Proc","C2",   "TA0007", "Discovery",           "T1057",  "Process Discovery",          "Laufende Prozesse auflisten"),
    ("Keylogger",      "C2",      "TA0009", "Collection",          "T1056.001","Keylogging",               "Tastatureingaben mitschneiden"),
    ("Screenshot",     "C2",      "TA0009", "Collection",          "T1113",  "Screen Capture",             "Desktop-Screenshot via PS1"),
    ("Webcam",         "C2",      "TA0009", "Collection",          "T1125",  "Video Capture",              "Webcam-Snapshot / Live-Stream"),
    ("Clipboard Monitor","C2",    "TA0009", "Collection",          "T1115",  "Clipboard Data",             "Clipboard überwachen"),

    # ── Lateral Movement ──────────────────────────────────────────────────────
    ("Pass-the-Hash",  "AD",      "TA0008", "Lateral Movement",    "T1550.002","Pass the Hash",             "NTLM-Hash direkt zur Auth"),
    ("Pass-the-Ticket","AD",      "TA0008", "Lateral Movement",    "T1550.003","Pass the Ticket",           "Kerberos-Ticket recyclen"),
    ("SMBExec",        "Lateral", "TA0008", "Lateral Movement",    "T1021.002","SMB/Windows Admin Shares",  "Lateral via SMB"),
    ("WMIExec",        "Lateral", "TA0008", "Lateral Movement",    "T1021.003","Distributed COM",           "WMI Remote Execution"),
    ("Golden Ticket",  "AD",      "TA0008", "Lateral Movement",    "T1558.001","Golden Ticket",             "Forged Kerberos TGT"),

    # ── Command & Control ─────────────────────────────────────────────────────
    ("HTTPS Shell",    "C2",      "TA0011", "Command & Control",   "T1071.001","Web Protocols",             "HTTPS Reverse Shell Port 443"),
    ("DNS C2",         "C2",      "TA0011", "Command & Control",   "T1071.004","DNS",                       "C2-Traffic über DNS getunnelt"),
    ("Telegram C2",    "C2",      "TA0011", "Command & Control",   "T1102",  "Web Service",                "Telegram Bot als C2-Kanal"),
    ("Metasploit",     "Network", "TA0011", "Command & Control",   "T1090",  "Proxy",                      "Meterpreter C2 via MSF Handler"),

    # ── Exfiltration ─────────────────────────────────────────────────────────
    ("DNS C2",         "C2",      "TA0010", "Exfiltration",        "T1048.003","Non-App Layer Protocol",    "Daten via DNS exfiltrieren"),
    ("Post-Exploit: WiFi","C2",   "TA0010", "Exfiltration",        "T1048",  "Exfil Over Alt Protocol",    "WiFi-Passwörter → Telegram"),
    ("Browser Passwords","C2",    "TA0010", "Exfiltration",        "T1048",  "Exfil Over Alt Protocol",    "Browser-Creds → Telegram"),

    # ── Impact ────────────────────────────────────────────────────────────────
    ("Deauth Flood",   "WiFi",    "TA0040", "Impact",              "T1498",  "Network Denial of Service",  "802.11 Deauth-Pakete fluten"),
    ("DDoS Tools",     "Network", "TA0040", "Impact",              "T1498",  "Network Denial of Service",  "Slowloris, hping3, wrk"),

    # ── Web ───────────────────────────────────────────────────────────────────
    ("SQLmap",         "Web",     "TA0001", "Initial Access",      "T1190", "Exploit Public-Facing App",   "SQL Injection automatisiert"),
    ("XSS Engine",     "Web",     "TA0001", "Initial Access",      "T1189", "Drive-by Compromise",        "Stored/Reflected/DOM XSS"),
    ("ffuf",           "Web",     "TA0043", "Reconnaissance",      "T1595.003","Wordlist Scanning",        "Web-Fuzzing Dirs/Params/VHosts"),
    ("BeEF",           "Web",     "TA0002", "Execution",           "T1185", "Browser Session Hijacking",   "JavaScript-Hooks im Browser"),

    # ── MITM ─────────────────────────────────────────────────────────────────
    ("ARP Spoofing",   "MITM",    "TA0006", "Credential Access",   "T1557",  "AiTM",                       "bettercap ARP-Poisoning"),
    ("SSL Strip",      "MITM",    "TA0006", "Credential Access",   "T1557.002","AiTM: SSL Strip",           "HTTPS → HTTP downgraden"),
    ("mitm6",          "MITM",    "TA0008", "Lateral Movement",    "T1557",  "AiTM (IPv6)",                "IPv6 DHCP → NTLM Relay"),
]


# ── Gruppierung ───────────────────────────────────────────────────────────────
def _group_by_tactic() -> dict[str, list[tuple]]:
    grouped: dict[str, list[tuple]] = {}
    for m in MAPPINGS:
        tactic = f"{m[2]}  {m[3]}"
        grouped.setdefault(tactic, []).append(m)
    return dict(sorted(grouped.items()))


def _group_by_category() -> dict[str, list[tuple]]:
    grouped: dict[str, list[tuple]] = {}
    for m in MAPPINGS:
        grouped.setdefault(m[1], []).append(m)
    return dict(sorted(grouped.items()))


# ── Anzeige ───────────────────────────────────────────────────────────────────
async def show_mitre_map(mode: str = "tactic", search: str = "") -> AsyncGenerator[str, None]:
    R   = "\033[0m"
    G   = "\033[92m"
    C   = "\033[96m"
    Y   = "\033[93m"
    RD  = "\033[91m"
    DIM = "\033[2m"
    B   = "\033[1m"
    W   = "\033[97m"

    data = MAPPINGS
    if search:
        s = search.lower()
        data = [m for m in data if s in m[0].lower() or s in m[1].lower()
                or s in m[4].lower() or s in m[5].lower() or s in m[6].lower()]
        if not data:
            yield f"{Y}[!] Kein Ergebnis für '{search}'{R}"
            return
        yield f"{G}[+] {len(data)} Treffer für '{search}'{R}\n"

    if mode == "category":
        grouped = _group_by_category()
        for cat, items in grouped.items():
            if search and not any(m in items for m in data):
                continue
            yield f"\n{B}{C}  ▸ {cat}{R}"
            yield f"  {DIM}{'─'*74}{R}"
            for m in items:
                if search and m not in data:
                    continue
                tid   = f"{m[4]:<12}"
                tname = f"{m[5]:<35}"
                tool  = f"{m[0]:<22}"
                desc  = m[6]
                yield f"  {G}{tool}{R}  {Y}{tid}{R}  {W}{tname}{R}  {DIM}{desc}{R}"
    else:
        grouped = _group_by_tactic()
        for tactic, items in grouped.items():
            display = [m for m in items if m in data] if search else items
            if not display:
                continue
            tactic_id, tactic_name = tactic.split("  ", 1)
            yield f"\n{B}{RD}  ◈ {tactic_id}  {tactic_name}{R}"
            yield f"  {DIM}{'─'*74}{R}"
            for m in display:
                tid   = f"{m[4]:<12}"
                tname = f"{m[5]:<35}"
                tool  = f"{m[0]:<22}"
                desc  = m[6]
                yield f"  {G}{tool}{R}  {Y}{tid}{R}  {C}{tname}{R}  {DIM}{desc}{R}"

    yield ""
    yield f"  {DIM}Gesamt: {len(MAPPINGS)} Mappings · {len(set(m[2] for m in MAPPINGS))} Taktiken · {len(set(m[4] for m in MAPPINGS))} Techniken{R}"
    yield f"  {DIM}Referenz: https://attack.mitre.org/{R}"


async def get_tool_techniques(tool_name: str) -> AsyncGenerator[str, None]:
    """Zeigt alle ATT&CK-Techniken für ein bestimmtes Tool."""
    async for line in show_mitre_map(mode="tactic", search=tool_name):
        yield line
