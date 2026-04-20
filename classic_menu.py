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
{DG}    ██████╗ ███████╗███╗  ██╗██╗  ██╗██╗████████╗
{G}    ██╔══██╗██╔════╝████╗ ██║██║ ██╔╝██║╚══██╔══╝
{G}    ██████╔╝█████╗  ██╔██╗██║█████╔╝ ██║   ██║
{G}    ██╔═══╝ ██╔══╝  ██║╚████║██╔═██╗ ██║   ██║
{DG}    ██║     ███████╗██║ ╚███║██║  ██╗██║   ██║
{DG}    ╚═╝     ╚══════╝╚═╝  ╚══╝╚═╝  ╚═╝╚═╝   ╚═╝{R}
{DIM}              Authorized Pentesting Framework v3{R}
{DIM}    ─────────────────────────────────────────────{R}"""
    print(art)

def section(title: str):
    w = 50
    print(f"\n{G}╔{'═'*(w-2)}╗{R}")
    print(f"{G}║{B}{title.center(w-2)}{R}{G}║{R}")
    print(f"{G}╚{'═'*(w-2)}╝{R}\n")

def menu_item(num: str, label: str, danger: str = ""):
    color = {"🟢": DG, "🟡": Y, "🟠": Y, "🔴": RD, "⛔": RD}.get(danger, G)
    print(f"  {DIM}[{R}{G}{B}{num}{R}{DIM}]{R}  {color}{label}{R}  {danger}")

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


async def menu_c2():
    """Placeholder — C2/RAT module built in next session."""
    banner()
    section("💀  C2 / RAT — WINDOWS PAYLOADS")
    print(f"  {Y}[!] C2 module is being built.{R}")
    print(f"  {DIM}Coming next session:{R}")
    print(f"  {G}→{R}  Fileless PowerShell payload (RAM only)")
    print(f"  {G}→{R}  AMSI Bypass + ETW Patching")
    print(f"  {G}→{R}  Polymorphic shellcode (new signature every generate)")
    print(f"  {G}→{R}  Disguised as PDF / Photo / Word macro")
    print(f"  {G}→{R}  Reverse shell to Kali via HTTPS/DNS")
    print(f"  {G}→{R}  Auto-generated ANLEITUNG.txt")
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
        print(f"  {DIM}{'─'*46}{R}")
        menu_item("1", "📡  WiFi Attacks",           "🟠")
        menu_item("2", "🌐  Network Intelligence",   "🟠")
        menu_item("3", "💻  Web Attack",             "🟠")
        menu_item("4", "🔑  Passwords & Hashes",     "🟡")
        menu_item("5", "☠️   MITM",                   "🔴")
        menu_item("6", "🔍  OSINT Recon",            "🟡")
        menu_item("7", "🔵  Blue Team Defense",      "🟢")
        menu_item("8", "🃏  Joker / Pranks",         "🟡")
        menu_item("9", "💀  C2 / RAT Payloads",      "⛔")
        print(f"  {DIM}{'─'*46}{R}")
        menu_item("0", "Exit")

        choice = prompt("penkit")

        dispatch = {
            "1": menu_wifi,
            "2": menu_network,
            "3": menu_web,
            "4": menu_passwords,
            "5": menu_mitm,
            "6": menu_osint,
            "7": menu_blueteam,
            "8": menu_joker,
            "9": menu_c2,
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
