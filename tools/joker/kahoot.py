"""
Kahoot toolkit — WebSocket-based implementation.

KahootFlooder   : Joins a game with N bots via real WebSocket connections.
KahootAutoAnswer: Single bot that listens for questions and answers them.

Protocol: Kahoot uses Bayeux/CometD over WebSocket.
Game PIN → session token → challenge decode → WebSocket → join lobby.

Requires: pip3 install websockets --break-system-packages
"""

import asyncio
import json
import random
import re
import shutil
import string
import subprocess
import time
import urllib.error
import urllib.request
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Kahoot Flooder",
    description=(
        "Floods a Kahoot game lobby with bots via real WebSocket connections. "
        "Also includes Auto-Answer mode. Requires: pip3 install websockets"
    ),
    usage="Enter the Kahoot game PIN and number of bots.",
    danger_note="🟡 Low Risk — disrupts a game session only.",
    example="PIN: 1234567  Bots: 50",
)

DANGER = DangerLevel.YELLOW

KAHOOT_API = "https://kahoot.it/reserve/session/{pin}/?{ts}"
KAHOOT_WS  = "wss://kahoot.it/cometd/{pin}/{token}"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

NAME_PREFIXES = ["xX", "Pro", "Ez", "Bot", "Noob", "King", "God", "Leet", "Dark", "Epic"]
NAME_SUFFIXES = ["Xx", "420", "1337", "999", "_YT", "_TTV", "OP", "GG", "FTW", "WIN"]


def _random_name() -> str:
    prefix = random.choice(NAME_PREFIXES)
    suffix = random.choice(NAME_SUFFIXES)
    mid = "".join(random.choices(string.ascii_uppercase, k=random.randint(2, 5)))
    return f"{prefix}{mid}{suffix}"


def _get_session_token(pin: str) -> tuple[str, str]:
    """Fetch Kahoot session token + challenge JS for a given PIN."""
    ts = int(time.time() * 1000)
    url = KAHOOT_API.format(pin=pin, ts=ts)
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Referer": "https://kahoot.it/",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token = resp.getheader("x-kahoot-session-token", "")
            body = json.loads(resp.read())
            challenge = body.get("challenge", "")
            return token, challenge
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "", "Game not found or not started yet"
        return "", f"HTTP {e.code}"
    except Exception as e:
        return "", str(e)


def _decode_token(token: str, challenge: str) -> str:
    """
    Decode Kahoot session token using the challenge JavaScript.
    Kahoot XORs the base64 token chars using a key derived from the challenge string.

    Strategy:
      1. Try Node.js to evaluate the JS directly (most reliable).
      2. Fall back to extracting the numeric key from the challenge via regex.
    """
    if not token or not challenge:
        return token

    # Strategy 1: Node.js (usually on Kali)
    if shutil.which("node"):
        js = (
            "var _ = function(x){return x;};"
            "var result = '';"
            f"var token = atob({json.dumps(token)});"
            f"{challenge};"
            "process.stdout.write(result || token);"
        )
        try:
            out = subprocess.check_output(
                ["node", "-e", js], timeout=5, stderr=subprocess.DEVNULL
            )
            decoded = out.decode(errors="replace").strip()
            if decoded:
                return decoded
        except Exception:
            pass

    # Strategy 2: regex heuristic — extract the XOR offset from the challenge body
    # Common pattern: _(1234 % 5678, ...) or similar arithmetic
    import base64
    try:
        raw = base64.b64decode(token + "==").decode("latin-1")
    except Exception:
        raw = token

    nums = re.findall(r"\d+", challenge)
    if len(nums) >= 2:
        key = int(nums[0]) % max(int(nums[1]), 1)
        decoded = "".join(chr(ord(c) ^ key) for c in raw)
        # Sanity check: decoded token should be alphanumeric-ish
        if all(32 <= ord(c) < 127 for c in decoded[:20]):
            return decoded

    return raw  # best-effort fallback


async def _ws_join(pin: str, decoded_token: str, name: str) -> str:
    """
    Attempt a real WebSocket join to Kahoot.
    Returns 'joined', 'rejected:<reason>', or 'error:<msg>'.
    """
    try:
        import websockets
    except ImportError:
        return "no_websockets"

    ws_url = KAHOOT_WS.format(pin=pin, token=decoded_token)
    ua = random.choice(USER_AGENTS)
    try:
        async with websockets.connect(
            ws_url,
            additional_headers={
                "Origin": "https://kahoot.it",
                "User-Agent": ua,
            },
            open_timeout=8,
            ping_interval=None,
        ) as ws:
            # Bayeux handshake
            await ws.send(json.dumps([{
                "channel": "/meta/handshake",
                "version": "1.0",
                "minimumVersion": "1.0",
                "supportedConnectionTypes": ["websocket"],
                "ext": {"ack": True, "timesync": {"l": 0, "o": 0, "tc": 0}},
                "id": "1",
            }]))

            raw = await asyncio.wait_for(ws.recv(), timeout=6)
            resp = json.loads(raw)
            if not resp or not resp[0].get("successful"):
                reason = resp[0].get("error", "handshake refused") if resp else "no response"
                return f"rejected:{reason}"

            client_id = resp[0]["clientId"]

            # Subscribe to game channel
            await ws.send(json.dumps([{
                "channel": "/meta/subscribe",
                "clientId": client_id,
                "subscription": f"/controller/{pin}",
                "id": "2",
            }]))
            await asyncio.wait_for(ws.recv(), timeout=5)

            # Send join message
            join_payload = json.dumps({
                "device": {"userAgent": ua, "screen": {"width": 1920, "height": 1080}},
                "type": "player",
                "name": name,
            })
            await ws.send(json.dumps([{
                "channel": "/service/controller",
                "clientId": client_id,
                "data": {
                    "content": join_payload,
                    "gameid": int(pin),
                    "host": "kahoot.it",
                    "type": "joined",
                    "id": 1,
                },
                "id": "3",
            }]))

            raw = await asyncio.wait_for(ws.recv(), timeout=6)
            resp = json.loads(raw)
            # Check for rejection (name taken, game full, etc.)
            if resp and isinstance(resp, list) and resp[0].get("data"):
                data = resp[0]["data"]
                if isinstance(data, dict) and data.get("type") == "loginResponse":
                    if not data.get("playerName"):
                        return "rejected:name_rejected"
            return "joined"

    except ImportError:
        return "no_websockets"
    except asyncio.TimeoutError:
        return "error:timeout"
    except Exception as e:
        msg = str(e)[:60]
        return f"error:{msg}"


class KahootFlooder:
    def __init__(self):
        self._running = False

    async def flood(
        self,
        pin: str,
        bot_count: int = 50,
        custom_prefix: str = "",
        delay_ms: int = 150,
    ) -> AsyncGenerator[str, None]:
        self._running = True
        yield f"[*] Kahoot Flooder — PIN: {pin}"
        yield f"[*] Bots: {bot_count}  Delay: {delay_ms}ms zwischen Batches"

        # Check websockets
        try:
            import websockets  # noqa: F401
        except ImportError:
            yield "[!] 'websockets' nicht installiert."
            yield "    pip3 install websockets --break-system-packages"
            return

        yield "[*] Session-Token abrufen..."
        token, challenge = await asyncio.get_event_loop().run_in_executor(
            None, _get_session_token, pin
        )

        if not token:
            yield f"[!] Kein Token: {challenge}"
            yield "[!] Prüfe ob PIN gültig und Spiel aktiv ist."
            return

        yield f"[+] Token erhalten ({token[:12]}...)"
        yield "[*] Challenge dekodieren..."
        decoded = await asyncio.get_event_loop().run_in_executor(
            None, _decode_token, token, challenge
        )
        yield f"[+] Decoded token: {decoded[:12]}..."
        yield "[*] Bots werden gestartet...\n"

        joined = 0
        failed = 0

        async def _join_bot(i: int) -> str:
            nonlocal joined, failed
            name = f"{custom_prefix}{i}" if custom_prefix else _random_name()
            result = await _ws_join(pin, decoded, name)
            if result == "joined":
                joined += 1
                return f"[+] Bot {i:>3}: {name:<18} ✓ joined"
            else:
                failed += 1
                return f"[-] Bot {i:>3}: {name:<18} ✗ {result}"

        batch_size = 10
        for batch_start in range(0, bot_count, batch_size):
            if not self._running:
                yield "[*] Abgebrochen."
                break
            batch = range(batch_start, min(batch_start + batch_size, bot_count))
            results = await asyncio.gather(*[_join_bot(i) for i in batch])
            for r in results:
                yield r
            yield f"    → {joined + failed}/{bot_count} versucht  ✓{joined}  ✗{failed}"
            await asyncio.sleep(delay_ms / 1000)

        yield ""
        yield f"[{'+'  if joined > 0 else '!'}] Ergebnis: {joined} Bots gejoined, {failed} fehlgeschlagen"
        if failed == bot_count:
            yield "[*] Alle fehlgeschlagen — Kahoot blockiert ggf. mit CAPTCHA oder PIN abgelaufen"

    async def stop(self):
        self._running = False


class KahootAutoAnswer:
    """Single bot that joins and randomly answers questions via WebSocket."""

    def __init__(self):
        self._running = False
        self._ws = None

    async def run(
        self, pin: str, name: str = "", strategy: str = "random"
    ) -> AsyncGenerator[str, None]:
        self._running = True
        bot_name = name or _random_name()
        yield f"[*] Auto-Answer Bot: {bot_name}  PIN: {pin}  Strategie: {strategy}"

        try:
            import websockets
        except ImportError:
            yield "[!] pip3 install websockets --break-system-packages"
            return

        token, challenge = await asyncio.get_event_loop().run_in_executor(
            None, _get_session_token, pin
        )
        if not token:
            yield "[!] Kein Token — PIN gültig und Spiel aktiv?"
            return

        decoded = await asyncio.get_event_loop().run_in_executor(
            None, _decode_token, token, challenge
        )

        ws_url = KAHOOT_WS.format(pin=pin, token=decoded)
        yield f"[*] Verbinde: {ws_url[:50]}..."

        try:
            async with websockets.connect(
                ws_url,
                additional_headers={"Origin": "https://kahoot.it"},
                ping_interval=None,
                open_timeout=8,
            ) as ws:
                self._ws = ws

                # Handshake
                await ws.send(json.dumps([{
                    "channel": "/meta/handshake",
                    "version": "1.0",
                    "minimumVersion": "1.0",
                    "supportedConnectionTypes": ["websocket"],
                    "ext": {"ack": True, "timesync": {"l": 0, "o": 0, "tc": 0}},
                    "id": "1",
                }]))
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=6))
                if not resp[0].get("successful"):
                    yield "[!] Handshake fehlgeschlagen"
                    return
                client_id = resp[0]["clientId"]

                # Join
                join_payload = json.dumps({
                    "device": {"userAgent": USER_AGENTS[0], "screen": {"width": 1920, "height": 1080}},
                    "type": "player",
                    "name": bot_name,
                })
                await ws.send(json.dumps([{
                    "channel": "/service/controller",
                    "clientId": client_id,
                    "data": {
                        "content": join_payload,
                        "gameid": int(pin),
                        "host": "kahoot.it",
                        "type": "joined",
                        "id": 1,
                    },
                    "id": "2",
                }]))
                await asyncio.wait_for(ws.recv(), timeout=6)
                yield f"[+] Gejoined als: {bot_name}"
                yield "[*] Warte auf Fragen..."
                yield "[*] Antworten: 0=rot  1=blau  2=gelb  3=grün"

                question_num = 0
                msg_id = 3

                # Connect loop + listen for questions
                while self._running:
                    await ws.send(json.dumps([{
                        "channel": "/meta/connect",
                        "clientId": client_id,
                        "connectionType": "websocket",
                        "id": str(msg_id),
                    }]))
                    msg_id += 1

                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=10)
                        messages = json.loads(raw)
                        for msg in messages:
                            data = msg.get("data", {})
                            if isinstance(data, dict) and data.get("type") == "question":
                                question_num += 1
                                answer = random.randint(0, 3) if strategy == "random" else 0
                                yield f"[?] Frage {question_num} erkannt — antworte mit {answer}"

                                # Send answer
                                await ws.send(json.dumps([{
                                    "channel": "/service/controller",
                                    "clientId": client_id,
                                    "data": {
                                        "gameid": int(pin),
                                        "host": "kahoot.it",
                                        "id": answer,
                                        "type": "quiz",
                                        "meta": {"lag": random.randint(80, 400)},
                                    },
                                    "id": str(msg_id),
                                }]))
                                msg_id += 1
                                yield f"[+] Antwort {answer} gesendet"

                            elif data.get("type") in ("timeup", "revealAnswer"):
                                yield f"[*] Runde {question_num} vorbei"
                    except asyncio.TimeoutError:
                        pass

        except Exception as e:
            yield f"[!] Fehler: {e}"

    async def stop(self):
        self._running = False
        if self._ws:
            await self._ws.close()
