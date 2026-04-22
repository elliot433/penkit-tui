"""
PenKit Telegram Setup — einmaliger Wizard zum Einrichten des Telegram-Bots.

Was dieser Wizard macht:
  1. Erklärt wie man einen Bot bei @BotFather erstellt
  2. Nimmt den Token entgegen
  3. Findet die Chat-ID automatisch (getUpdates API)
  4. Sendet eine Test-Nachricht zur Bestätigung
  5. Speichert Token + Chat-ID in ~/.config/penkit-tui/config.json

Der Bot wird dann überall in PenKit verwendet:
  - Phishing-Alerts (neue Credentials → Telegram)
  - Post-Exploit Exfil (Keylogger, Screenshots, WiFi-Passwörter)
  - C2 Agent (remote commands via Telegram)
  - Evil Twin Auto-Combo (caught passwords)
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import AsyncGenerator

from core.config import load as cfg_load, save as cfg_save


_BASE = "https://api.telegram.org/bot{token}/{method}"


def _api(token: str, method: str, params: dict | None = None) -> dict:
    url = _BASE.format(token=token, method=method)
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return json.loads(body)
        except Exception:
            return {"ok": False, "description": body}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def validate_token(token: str) -> bool:
    """Prüft ob das Token-Format korrekt ist (keine API-Anfrage nötig)."""
    parts = token.strip().split(":")
    return len(parts) == 2 and parts[0].isdigit() and len(parts[1]) >= 30


def get_bot_info(token: str) -> dict | None:
    """Gibt Bot-Name und Username zurück wenn Token gültig."""
    r = _api(token, "getMe")
    if r.get("ok"):
        return r["result"]
    return None


def get_updates(token: str, offset: int = 0) -> list[dict]:
    """Holt neue Nachrichten — für automatische Chat-ID-Erkennung."""
    r = _api(token, "getUpdates", {"offset": offset, "timeout": 5, "limit": 10})
    if r.get("ok"):
        return r.get("result", [])
    return []


def send_message(token: str, chat_id: str, text: str) -> bool:
    """Sendet eine Textnachricht."""
    r = _api(token, "sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
    return r.get("ok", False)


def load_telegram_config() -> tuple[str, str]:
    """Gibt (token, chat_id) aus config zurück. Leer wenn nicht gesetzt."""
    cfg = cfg_load()
    return cfg.get("telegram_token", ""), cfg.get("telegram_chat_id", "")


def save_telegram_config(token: str, chat_id: str):
    cfg = cfg_load()
    cfg["telegram_token"] = token
    cfg["telegram_chat_id"] = chat_id
    cfg_save(cfg)


async def setup_wizard() -> AsyncGenerator[str, None]:
    """Interaktiver Setup-Wizard — gibt Strings zum Ausgeben zurück."""
    # Nur Schritt-für-Schritt-Texte — die eigentliche Interaktion läuft im Menü.
    # Dieser Generator wird nicht direkt aufgerufen, nur als Referenz.
    yield ""
