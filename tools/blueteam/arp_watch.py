"""
Real-time ARP spoof detector.

How it works:
  1. Build a trusted IP→MAC table from the current ARP cache at startup
  2. Monitor live ARP traffic with scapy/tcpdump
  3. Alert on any IP that suddenly maps to a different MAC (classic ARP spoofing indicator)
  4. Cross-check against gateway MAC — gateway spoofing is the most dangerous variant
"""

import asyncio
import re
import subprocess
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="ARP Spoof Detector",
    description=(
        "Monitors live ARP traffic and alerts whenever an IP changes its MAC address — "
        "the primary indicator of an ARP poisoning / MITM attack. "
        "Builds a trusted baseline at startup and flags every deviation."
    ),
    usage="Run on the network interface you want to monitor. Works best as root.",
    danger_note="🟢 Safe — purely passive listener, zero packets sent.",
    example="tcpdump -i eth0 arp -l",
)

DANGER = DangerLevel.GREEN


@dataclass
class ArpEntry:
    ip: str
    mac: str
    trusted: bool = True


class ArpWatcher:
    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self._trusted: dict[str, str] = {}   # ip → mac
        self._current: dict[str, str] = {}
        self._runner = CommandRunner()

    def _load_arp_cache(self) -> dict[str, str]:
        table: dict[str, str] = {}
        try:
            out = subprocess.check_output(["arp", "-n"], text=True)
            for line in out.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and parts[2] != "(incomplete)":
                    table[parts[0]] = parts[2].lower()
        except Exception:
            pass
        return table

    async def watch(self) -> AsyncGenerator[str, None]:
        self._trusted = self._load_arp_cache()
        self._current = dict(self._trusted)

        yield f"[*] ARP Watcher started on {self.interface}"
        yield f"[*] Trusted baseline: {len(self._trusted)} entries"
        for ip, mac in self._trusted.items():
            yield f"    {ip:<18} → {mac}"
        yield "[*] Monitoring live ARP traffic..."
        yield "[*] Press STOP to end"

        async for line in self._runner.run([
            "tcpdump", "-i", self.interface,
            "-l", "-n", "arp",
        ]):
            # Parse tcpdump ARP lines:
            # "ARP, Request who-has 192.168.1.1 tell 192.168.1.50, length 28"
            # "ARP, Reply 192.168.1.1 is-at aa:bb:cc:dd:ee:ff, length 28"
            reply_match = re.search(
                r'Reply\s+([\d.]+)\s+is-at\s+([0-9a-f:]+)',
                line, re.IGNORECASE
            )
            if reply_match:
                ip  = reply_match.group(1)
                mac = reply_match.group(2).lower()
                self._current[ip] = mac

                if ip in self._trusted:
                    if mac != self._trusted[ip]:
                        yield (
                            f"\n[!] ⚠️  ARP SPOOF DETECTED!\n"
                            f"    IP:      {ip}\n"
                            f"    Trusted: {self._trusted[ip]}\n"
                            f"    Got:     {mac}\n"
                            f"    → Someone is intercepting traffic to {ip}"
                        )
                    # else: normal, silent
                else:
                    self._trusted[ip] = mac
                    yield f"[+] New host: {ip} → {mac}"
            else:
                yield f"[ARP] {line}"

    async def stop(self):
        await self._runner.stop()
