from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator


HELP = ToolHelp(
    name="WiFi Scanner",
    description="Scans for nearby WiFi networks using airodump-ng. Shows SSID, BSSID, channel, encryption, and signal strength.",
    usage="Requires monitor mode. The interface will be put into monitor mode automatically.",
    danger_note="🟡 Low Risk — passive scan, no packets sent to targets.",
    example="airodump-ng wlan0mon",
)

DANGER = DangerLevel.YELLOW


@dataclass
class AccessPoint:
    bssid: str = ""
    power: str = ""
    channel: str = ""
    encryption: str = ""
    ssid: str = ""
    clients: int = 0


class WifiScanner:
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface
        self.monitor_iface = interface + "mon"
        self._runner = CommandRunner()

    async def enable_monitor(self) -> AsyncGenerator[str, None]:
        yield f"[*] Enabling monitor mode on {self.interface}..."
        runner = CommandRunner()
        async for line in runner.run(["airmon-ng", "start", self.interface]):
            yield line
        yield f"[+] Monitor interface: {self.monitor_iface}"

    async def disable_monitor(self) -> AsyncGenerator[str, None]:
        yield f"[*] Disabling monitor mode..."
        runner = CommandRunner()
        async for line in runner.run(["airmon-ng", "stop", self.monitor_iface]):
            yield line
        yield f"[+] Monitor mode disabled"

    async def scan(self, output_file: str = "/tmp/penkit_scan") -> AsyncGenerator[str, None]:
        yield f"[*] Starting WiFi scan on {self.monitor_iface}"
        yield "[*] Press STOP to end scan and see results"
        async for line in self._runner.run([
            "airodump-ng",
            "--write", output_file,
            "--output-format", "csv",
            self.monitor_iface
        ]):
            yield line

    async def stop(self):
        await self._runner.stop()

    def parse_csv(self, csv_path: str) -> list[AccessPoint]:
        aps = []
        try:
            with open(csv_path + "-01.csv", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            in_ap_section = True
            for line in lines:
                line = line.strip()
                if line.startswith("Station MAC"):
                    in_ap_section = False
                    continue
                if not line or line.startswith("BSSID"):
                    continue
                if in_ap_section:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 14:
                        aps.append(AccessPoint(
                            bssid=parts[0],
                            power=parts[8],
                            channel=parts[3],
                            encryption=parts[5],
                            ssid=parts[13],
                        ))
        except Exception:
            pass
        return aps
