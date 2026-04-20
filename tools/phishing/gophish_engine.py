"""
GoPhish integration — manage campaigns, templates, results via GoPhish REST API.

GoPhish läuft lokal auf Kali (Port 3333 admin, Port 80/443 phishing).
Install: wget https://github.com/gophish/gophish/releases/latest → ./gophish

Workflow:
  1. Sending Profile erstellen (SMTP)
  2. Email Template hochladen
  3. Landing Page (Fake Login) hochladen
  4. Ziel-Liste importieren
  5. Kampagne starten
  6. Live-Ergebnisse: wer hat geklickt, wer hat Credentials eingegeben
"""

from __future__ import annotations
import asyncio
import json
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="GoPhish Engine",
    description=(
        "Steuert GoPhish-Kampagnen: Sending Profiles, Email Templates, "
        "Landing Pages und Live-Ergebnisse (Clicks, Credentials) — alles aus PenKit."
    ),
    usage="GoPhish muss lokal laufen. Start: ./gophish (gibt API-Key aus)",
    danger_note="⛔ BLACK — Phishing-Kampagnen nur auf autorisierten Zielen.",
    example="API Key aus GoPhish-Output, dann Kampagne konfigurieren.",
)

DANGER = DangerLevel.BLACK

GOPHISH_URL = "http://127.0.0.1:3333"


@dataclass
class CampaignConfig:
    name: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    from_address: str
    targets: list[str]          # ["felix@example.com", ...]
    email_subject: str
    template_name: str          # aus TEMPLATES dict
    landing_page: str           # aus PAGES dict
    phish_url: str              # http://<kali-ip>/


@dataclass
class CampaignResult:
    campaign_id: int = 0
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    submitted: int = 0
    credentials: list[dict] = field(default_factory=list)


class GoPhishEngine:
    def __init__(self, api_key: str, base_url: str = GOPHISH_URL):
        self.api_key = api_key
        self.base_url = base_url
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def _curl(self, method: str, path: str, data: dict | None = None) -> list[str]:
        """Returns curl command as list for CommandRunner."""
        cmd = [
            "curl", "-sk",
            "-X", method,
            "-H", f"Authorization: Bearer {self.api_key}",
            "-H", "Content-Type: application/json",
        ]
        if data:
            cmd += ["-d", json.dumps(data)]
        cmd.append(f"{self.base_url}/api/{path}")
        return cmd

    async def check_connection(self) -> AsyncGenerator[str, None]:
        yield "[*] Verbindung zu GoPhish prüfen..."
        async for line in CommandRunner().run(self._curl("GET", "campaigns/")):
            if '"id"' in line or '"name"' in line:
                yield "[+] GoPhish erreichbar ✓"
                return
            elif "refused" in line.lower() or "failed" in line.lower():
                yield "[!] GoPhish nicht erreichbar!"
                yield "[*] Starte mit: cd /opt/gophish && ./gophish"
                return

    async def create_sending_profile(self, cfg: CampaignConfig) -> AsyncGenerator[str, None]:
        yield f"[*] Sending Profile erstellen: {cfg.smtp_host}:{cfg.smtp_port}"
        data = {
            "name": f"penkit_{cfg.name}",
            "host": f"{cfg.smtp_host}:{cfg.smtp_port}",
            "from_address": cfg.from_address,
            "username": cfg.smtp_user,
            "password": cfg.smtp_pass,
            "ignore_cert_errors": True,
        }
        async for line in CommandRunner().run(self._curl("POST", "smtp/", data)):
            if '"id"' in line:
                yield "[+] Sending Profile erstellt"
            elif line.strip():
                yield line

    async def upload_landing_page(self, name: str, html: str) -> AsyncGenerator[str, None]:
        yield f"[*] Landing Page hochladen: {name}"
        data = {
            "name": name,
            "html": html,
            "capture_credentials": True,
            "capture_passwords": True,
            "redirect_url": "https://google.com",
        }
        async for line in CommandRunner().run(self._curl("POST", "pages/", data)):
            if '"id"' in line:
                yield "[+] Landing Page hochgeladen"
            elif line.strip():
                yield line

    async def get_results(self, campaign_id: int) -> AsyncGenerator[str, None]:
        yield f"[*] Ergebnisse für Kampagne {campaign_id}:"
        async for line in CommandRunner().run(
            self._curl("GET", f"campaigns/{campaign_id}/results")
        ):
            try:
                data = json.loads(line)
                results = data.get("results", [])
                clicked = [r for r in results if r.get("status") == "Clicked Link"]
                submitted = [r for r in results if r.get("status") == "Submitted Data"]
                yield f"[+] Emails gesendet : {len(results)}"
                yield f"[+] Links geklickt  : {len(clicked)}"
                yield f"[+] Credentials     : {len(submitted)}"
                for r in submitted:
                    yield f"  ► {r.get('email')}  →  {r.get('details', {})}"
            except Exception:
                if line.strip():
                    yield line

    async def live_monitor(self, campaign_id: int, interval: int = 30) -> AsyncGenerator[str, None]:
        """Pollt alle `interval` Sekunden neue Ergebnisse."""
        yield f"[*] Live-Monitor gestartet (alle {interval}s)  Ctrl+C zum Stoppen"
        seen_submitted = set()
        try:
            while True:
                async for line in CommandRunner().run(
                    self._curl("GET", f"campaigns/{campaign_id}/results")
                ):
                    try:
                        data = json.loads(line)
                        for r in data.get("results", []):
                            if r.get("status") == "Submitted Data":
                                key = r.get("email", "") + str(r.get("details", ""))
                                if key not in seen_submitted:
                                    seen_submitted.add(key)
                                    yield f"[!!!] NEUE CREDENTIALS: {r.get('email')} → {r.get('details')}"
                    except Exception:
                        pass
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            yield "[*] Monitor beendet."
