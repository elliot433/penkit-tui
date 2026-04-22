from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
from typing import AsyncGenerator


HELP = ToolHelp(
    name="Deauth Flood",
    description=(
        "Sends 802.11 deauthentication frames to disconnect clients from an AP. "
        "Used to force WPA2 handshake capture or as a standalone DoS test."
    ),
    usage="BSSID required. Client MAC optional (FF:FF:FF:FF:FF:FF = all clients). Count 0 = continuous.",
    danger_note="🔴 High Risk — actively disconnects devices. Only on networks you own.",
    example="aireplay-ng --deauth 0 -a AA:BB:CC:DD:EE:FF wlan0mon",
)

DANGER = DangerLevel.RED


class DeauthFlood:
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface
        self._runner = CommandRunner()

    async def flood(
        self,
        bssid: str,
        client: str = "FF:FF:FF:FF:FF:FF",
        count: int = 0,
    ) -> AsyncGenerator[str, None]:
        target_desc = "all clients" if client == "FF:FF:FF:FF:FF:FF" else client
        count_desc = "continuous" if count == 0 else f"{count} frames"

        yield f"[!] Deauth flood: {bssid} → {target_desc} ({count_desc})"
        yield f"[!] Interface: {self.interface}"

        async for line in self._runner.run([
            "aireplay-ng",
            "--deauth", str(count),
            "-a", bssid,
            "-c", client,
            self.interface,
        ]):
            yield line

    async def stop(self):
        await self._runner.stop()
