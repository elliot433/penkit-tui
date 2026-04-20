"""
Prank payload generator.

Generates self-contained scripts (Python / PowerShell / Bash) that can be
delivered to a target via USB, email, or C2 and executed locally.

All pranks:
  - Are purely cosmetic / reversible (no data deletion, no persistence)
  - Include a built-in undo / cleanup function
  - Run after an optional timer delay

Generated payloads:
  Linux/Mac : Python3 scripts
  Windows   : PowerShell scripts (.ps1)
"""

from typing import AsyncGenerator
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Prank Payload Generator",
    description=(
        "Generates harmless prank scripts for Linux/Mac (Python) and Windows (PowerShell). "
        "Fake BSOD, Fake Virus Scan, Rickroll, Mouse chaos, etc. "
        "All pranks are cosmetic and reversible. Includes optional timer delay."
    ),
    usage="Select prank type, target OS, and optional delay. Download generated script.",
    danger_note="🟡 Low Risk — cosmetic only, no data harm, all effects are reversible.",
    example="Generated: fake_virus.ps1  Run: powershell -File fake_virus.ps1",
)

DANGER = DangerLevel.YELLOW


# ── Windows PowerShell Payloads ───────────────────────────────────────────────

PS_FAKE_BSOD = r"""
# PenKit Prank: Fake BSOD
# Reversible: press Esc or wait {duration}s
Add-Type -AssemblyName System.Windows.Forms
$form = New-Object System.Windows.Forms.Form
$form.BackColor = [System.Drawing.Color]::Blue
$form.WindowState = 'Maximized'
$form.FormBorderStyle = 'None'
$form.TopMost = $true
$label = New-Object System.Windows.Forms.Label
$label.ForeColor = [System.Drawing.Color]::White
$label.Font = New-Object System.Drawing.Font("Consolas", 16)
$label.AutoSize = $true
$label.Location = New-Object System.Drawing.Point(100, 150)
$label.Text = @"
:( Your PC ran into a problem and needs to restart.
We're just collecting some error info, and then we'll restart for you.

0% complete

Stop code: CRITICAL_PROCESS_DIED
"@
$form.Controls.Add($label)
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = {duration}000
$timer.Add_Tick({{ $form.Close(); $timer.Stop() }})
$form.Add_KeyDown({{ if($_.KeyCode -eq 'Escape'){{ $form.Close() }} }})
$timer.Start()
$form.ShowDialog()
"""

PS_FAKE_VIRUS = r"""
# PenKit Prank: Fake Virus Scan
# Shows a fake security scan finding "999 viruses"
Add-Type -AssemblyName System.Windows.Forms
$files = @("C:\Windows\System32\kernel32.dll","C:\Users\Public\Documents\report.pdf",
           "C:\Program Files\Chrome\chrome.exe","C:\Windows\explorer.exe",
           "C:\Users\$env:USERNAME\Downloads\setup.exe")
$viruses = @("Trojan.GenericKD.47291","Backdoor.IRC.Bot","Ransomware.WannaCry",
             "Spyware.AgentTesla","Rootkit.ZeroAccess","Worm.Conficker")
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "`n[*] PenKit Security Suite v3.7.1" -ForegroundColor Cyan
Write-Host "[*] Starting deep system scan...`n" -ForegroundColor Cyan
$count = 0
for($i = 0; $i -lt 50; $i++) {
    $f = $files[$i % $files.Length]
    $v = $viruses[$i % $viruses.Length]
    $count++
    Write-Host "[THREAT] $f" -ForegroundColor Red -NoNewline
    Write-Host "  --> $v" -ForegroundColor Yellow
    Start-Sleep -Milliseconds 120
}
Write-Host "`n[!!!] SCAN COMPLETE: $count THREATS DETECTED [!!!]" -ForegroundColor Red
Write-Host "Your system is critically infected. Call 1-800-FAKE-HELP now!" -ForegroundColor Yellow
Write-Host "`n[Press any key to 'clean'...]"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host "`n[*] Just kidding - this was a prank by your admin :)" -ForegroundColor Green
"""

PS_RICKROLL = r"""
# PenKit Prank: Rickroll
Start-Process "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show(
    "Never gonna give you up!`nNever gonna let you down!",
    "You've been Rick Rolled!",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
)
"""

PS_100_TABS = r"""
# PenKit Prank: 100 Browser Tabs
$url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
Write-Host "[*] Opening {count} tabs..."
for($i = 0; $i -lt {count}; $i++) {
    Start-Process $url
    Start-Sleep -Milliseconds 200
}
"""

PS_FAKE_UPDATE = r"""
# PenKit Prank: Fake Windows Update Screen
Add-Type -AssemblyName System.Windows.Forms
$form = New-Object System.Windows.Forms.Form
$form.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
$form.WindowState = 'Maximized'
$form.FormBorderStyle = 'None'
$form.TopMost = $true
$progress = 0
$label = New-Object System.Windows.Forms.Label
$label.ForeColor = [System.Drawing.Color]::White
$label.Font = New-Object System.Drawing.Font("Segoe UI", 22)
$label.TextAlign = 'MiddleCenter'
$label.Dock = 'Fill'
$label.Text = "Working on updates`n0% complete`n`nDon't turn off your PC"
$form.Controls.Add($label)
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 800
$timer.Add_Tick({
    $progress += [math]::Floor((Get-Random -Minimum 1 -Maximum 4))
    if($progress -gt 100) { $progress = 100 }
    $label.Text = "Working on updates`n$progress% complete`n`nDon't turn off your PC"
    if($progress -ge 100) {
        Start-Sleep -Seconds 2
        $form.Close()
    }
})
$form.Add_KeyDown({ if($_.KeyCode -eq 'Escape') { $form.Close() } })
$timer.Start()
$form.ShowDialog()
"""

# ── Linux/Mac Python Payloads ─────────────────────────────────────────────────

PY_FAKE_VIRUS = r"""#!/usr/bin/env python3
# PenKit Prank: Fake Virus Scan (Linux/Mac Terminal)
import time, random, sys

files = ["/etc/passwd", "/home/user/Documents/taxes.pdf", "/usr/bin/python3",
         "/var/log/syslog", "/home/user/.ssh/id_rsa", "/etc/shadow"]
viruses = ["Trojan.Linux.Mirai","Backdoor.Tsunami","Rootkit.Jynx2",
           "Ransomware.Linux.Encoder","Cryptominer.XMRig","Worm.Linux.Agent"]

print("\033[96m[*] PenKit Security Suite v3.7.1\033[0m")
print("\033[96m[*] Starting deep scan...\033[0m\n")
count = 0
for i in range(40):
    f = random.choice(files)
    v = random.choice(viruses)
    count += 1
    print(f"\033[91m[THREAT] {f}\033[0m  →  \033[93m{v}\033[0m")
    time.sleep(0.15)

print(f"\n\033[91m[!!!] SCAN COMPLETE: {count} THREATS FOUND [!!!]\033[0m")
print("\033[93mYour system is critically infected!\033[0m")
input("\n[Press Enter to 'clean'...]")
print("\n\033[92m[*] Just kidding - this was a prank! :)\033[0m\n")
"""

PY_FORK_BOMB_SAFE = r"""#!/usr/bin/env python3
# PenKit Prank: Harmless fork bomb simulation (FAKE - just prints)
import time
print("[*] Initiating... just kidding, this is fake.")
for i in range(20):
    print(f"  [fork] spawning process {1337+i}... ", end="", flush=True)
    time.sleep(0.2)
    print("done")
print("\n[*] Your system is fine. This was a prank.")
"""

PY_DISCO_TERMINAL = r"""#!/usr/bin/env python3
# PenKit Prank: Rainbow disco terminal
import time, sys, random
colors = ['\033[91m','\033[92m','\033[93m','\033[94m','\033[95m','\033[96m']
reset = '\033[0m'
msg = "  🎉  YOU'VE BEEN PRANKED BY YOUR SYSADMIN  🎉  "
print("\033[2J\033[H")  # clear screen
for _ in range(60):
    c = random.choice(colors)
    print(f"\r{c}{msg}{reset}", end="", flush=True)
    time.sleep(0.1)
print(f"\n\n{random.choice(colors)}Have a nice day! :){reset}\n")
"""


class PrankPayloadGenerator:

    PAYLOADS = {
        "fake_bsod":      ("Windows",   "fake_bsod.ps1",     PS_FAKE_BSOD),
        "fake_virus_win": ("Windows",   "fake_virus.ps1",    PS_FAKE_VIRUS),
        "rickroll":       ("Windows",   "rickroll.ps1",      PS_RICKROLL),
        "100_tabs":       ("Windows",   "100_tabs.ps1",      PS_100_TABS),
        "fake_update":    ("Windows",   "fake_update.ps1",   PS_FAKE_UPDATE),
        "fake_virus_lin": ("Linux/Mac", "fake_virus.py",     PY_FAKE_VIRUS),
        "disco_terminal": ("Linux/Mac", "disco.py",          PY_DISCO_TERMINAL),
    }

    async def generate(
        self,
        prank_id: str,
        output_dir: str = "/tmp",
        delay_sec: int = 0,
        custom_param: str = "",
    ) -> AsyncGenerator[str, None]:
        if prank_id not in self.PAYLOADS:
            yield f"[ERROR] Unknown prank: {prank_id}"
            return

        platform, filename, template = self.PAYLOADS[prank_id]
        content = template

        # Apply parameters
        content = content.replace("{duration}", str(delay_sec or 10))
        content = content.replace("{count}", str(int(custom_param) if custom_param.isdigit() else 100))

        # Add optional delay wrapper
        if delay_sec > 0 and platform == "Windows":
            content = f"Start-Sleep -Seconds {delay_sec}\n" + content
        elif delay_sec > 0 and platform == "Linux/Mac":
            content = f"import time; time.sleep({delay_sec})\n" + content

        import os
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w") as f:
            f.write(content)

        yield f"[+] Payload generated: {out_path}"
        yield f"[+] Platform: {platform}"
        yield f"[+] Prank: {prank_id.replace('_', ' ').title()}"
        if delay_sec:
            yield f"[+] Delay: {delay_sec}s before activation"
        yield ""

        if platform == "Windows":
            yield f"[*] Deliver & run with:"
            yield f"    powershell -ExecutionPolicy Bypass -File {filename}"
        else:
            yield f"[*] Deliver & run with:"
            yield f"    chmod +x {filename} && python3 {filename}"

        yield ""
        yield "[*] File content preview:"
        for line in content.splitlines()[:15]:
            yield f"    {line}"
        if len(content.splitlines()) > 15:
            yield f"    ... ({len(content.splitlines())} lines total)"
