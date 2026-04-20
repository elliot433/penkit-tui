"""
SMTP Sender — verschickt Phishing-Mails direkt aus PenKit.

Unterstützt:
  - Eigener SMTP-Server (Postfix auf Kali, sendgrid, mailgun)
  - Gmail / Outlook als Relay (mit App-Passwort)
  - Bulk-Versand aus Zielliste (TXT, eine Adresse pro Zeile)
  - Personalisierung: {{NAME}} aus CSV (email, name)
  - Rate-Limiting (kein Spam-Filter triggern)
"""

from __future__ import annotations
import asyncio
import csv
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="SMTP Sender",
    description=(
        "Verschickt Phishing-Emails via SMTP. Unterstützt eigene Server, "
        "Gmail/Outlook-Relay und Bulk-Versand mit Personalisierung."
    ),
    usage="SMTP-Daten eingeben, Zielliste laden, Template wählen, senden.",
    danger_note="⛔ BLACK — nur auf autorisierten Zielen.",
    example="smtp.gmail.com:587 mit App-Passwort",
)

DANGER = DangerLevel.BLACK


@dataclass
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False


@dataclass
class SendResult:
    total: int = 0
    sent: int = 0
    failed: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def _load_targets(path: str) -> list[dict]:
    """
    Loads targets from TXT (one email per line) or CSV (email, name columns).
    Returns list of {"email": ..., "name": ...}
    """
    targets = []
    if path.endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email") or row.get("Email") or ""
                name  = row.get("name")  or row.get("Name")  or email.split("@")[0]
                if email:
                    targets.append({"email": email.strip(), "name": name.strip()})
    else:
        with open(path, encoding="utf-8") as f:
            for line in f:
                email = line.strip()
                if "@" in email:
                    targets.append({"email": email, "name": email.split("@")[0]})
    return targets


class SMTPSender:
    def __init__(self, cfg: SMTPConfig):
        self.cfg = cfg

    def _connect(self) -> smtplib.SMTP | smtplib.SMTP_SSL:
        if self.cfg.use_ssl:
            ctx = ssl.create_default_context()
            s = smtplib.SMTP_SSL(self.cfg.host, self.cfg.port, context=ctx)
        else:
            s = smtplib.SMTP(self.cfg.host, self.cfg.port)
            if self.cfg.use_tls:
                s.starttls()
        if self.cfg.username:
            s.login(self.cfg.username, self.cfg.password)
        return s

    async def test_connection(self) -> AsyncGenerator[str, None]:
        yield f"[*] Teste SMTP: {self.cfg.host}:{self.cfg.port}"
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connect)
            yield "[+] SMTP-Verbindung erfolgreich ✓"
        except Exception as e:
            yield f"[!] Verbindung fehlgeschlagen: {e}"

    async def send_campaign(
        self,
        targets_path: str,
        template_name: str,
        phish_url: str,
        from_address: str,
        delay_seconds: float = 2.0,
    ) -> AsyncGenerator[str, None]:
        from tools.phishing.email_templates import render_template

        yield f"[*] Lade Zielliste: {targets_path}"
        try:
            targets = _load_targets(targets_path)
        except Exception as e:
            yield f"[!] Fehler beim Laden: {e}"
            return

        yield f"[+] {len(targets)} Ziele geladen"
        yield f"[*] Template: {template_name}"
        yield f"[*] Phishing-URL: {phish_url}"
        yield f"[*] Verzögerung: {delay_seconds}s zwischen Mails\n"

        result = SendResult(total=len(targets))

        try:
            smtp = await asyncio.get_event_loop().run_in_executor(None, self._connect)
        except Exception as e:
            yield f"[!] SMTP-Verbindung fehlgeschlagen: {e}"
            return

        for i, target in enumerate(targets, 1):
            email = target["email"]
            name  = target["name"]

            subject, from_name, html = render_template(template_name, phish_url, name)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{from_name} <{from_address}>"
            msg["To"]      = email

            msg.attach(MIMEText(html, "html", "utf-8"))

            try:
                smtp.sendmail(from_address, [email], msg.as_string())
                result.sent += 1
                yield f"  [{i}/{result.total}] ✓  {email}"
            except Exception as e:
                result.failed += 1
                result.errors.append(f"{email}: {e}")
                yield f"  [{i}/{result.total}] ✗  {email}  ({e})"

            if delay_seconds > 0 and i < len(targets):
                await asyncio.sleep(delay_seconds)

        try:
            smtp.quit()
        except Exception:
            pass

        yield f"\n[+] Kampagne abgeschlossen:"
        yield f"  Gesendet : {result.sent}/{result.total}"
        yield f"  Fehler   : {result.failed}"
        if result.errors:
            for err in result.errors[:5]:
                yield f"  [!] {err}"


SMTP_PRESETS = {
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "note": "App-Passwort nötig: Google → Sicherheit → App-Passwörter",
    },
    "outlook": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "use_tls": True,
        "note": "Outlook.com oder Office365 Konto",
    },
    "sendgrid": {
        "host": "smtp.sendgrid.net",
        "port": 587,
        "use_tls": True,
        "note": "API-Key als Passwort, Username='apikey'",
    },
    "local": {
        "host": "127.0.0.1",
        "port": 25,
        "use_tls": False,
        "note": "Lokaler Postfix auf Kali: apt install postfix",
    },
}
