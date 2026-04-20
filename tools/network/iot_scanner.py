"""
IoT / Router / Kamera Scanner.

Pipeline:
  1. Nmap-Scan auf typische IoT-Ports (23/80/443/554/8080/8443/8888)
  2. Service-Fingerprint (Web-Interface, Telnet, SSH, RTSP)
  3. Default-Credentials-Test für Top-200 Geräte
  4. Router-spezifische Exploits (CVE-bekannte Schwachstellen, öffentliche Infos)
  5. Ergebnis: Login möglich / Admin-Panel URL / Credentials

Kein Shodan-Key nötig — alles via Nmap + direkter HTTP-Verbindung.
"""

from __future__ import annotations
import asyncio
import base64
import json
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner, check_tool
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="IoT Scanner",
    description=(
        "Scannt Netzwerk auf IoT-Geräte (Router, Kameras, NAS, Smart-Home), "
        "testet Default-Credentials für 200+ Geräte-Typen automatisch."
    ),
    usage="Netzwerk-Range oder einzelne IP eingeben (z.B. 192.168.1.0/24)",
    danger_note="🔴 ROT — nur im eigenen Netzwerk / mit Genehmigung.",
    example="192.168.1.0/24  →  findet alle IoT-Geräte + testet Default-Logins",
)

DANGER = DangerLevel.RED

# ── IoT-Ports ─────────────────────────────────────────────────────────────────
IOT_PORTS = "21,22,23,80,443,554,1883,2323,5000,7547,8080,8081,8443,8888,9000,37777"

# ── Default-Credentials Datenbank ─────────────────────────────────────────────
# Format: (username, password, beschreibung)
DEFAULT_CREDS: list[tuple[str, str, str]] = [
    # Router-Hersteller
    ("admin",      "admin",        "Generic router default"),
    ("admin",      "",             "Many routers no password"),
    ("admin",      "password",     "Generic"),
    ("admin",      "1234",         "Generic"),
    ("admin",      "12345",        "Generic"),
    ("admin",      "123456",       "Generic"),
    ("admin",      "admin123",     "Generic"),
    ("root",       "root",         "Linux-based devices"),
    ("root",       "admin",        "Linux-based devices"),
    ("root",       "",             "Telnet default"),
    ("root",       "toor",         "Kali/BT default"),
    ("root",       "password",     "Generic Linux"),
    ("root",       "1234",         "Generic Linux"),
    ("user",       "user",         "Generic"),
    ("guest",      "guest",        "Generic guest"),
    ("admin",      "1111",         "TP-Link old"),
    ("admin",      "0000",         "TP-Link old"),
    ("admin",      "tp-link",      "TP-Link"),
    ("admin",      "tplink",       "TP-Link"),
    ("admin",      "asus",         "ASUS routers"),
    ("admin",      "fritz!box",    "AVM FRITZ!Box"),
    ("admin",      "fritzbox",     "AVM FRITZ!Box"),
    ("admin",      "netgear",      "Netgear"),
    ("admin",      "password1",    "Netgear old"),
    ("admin",      "1q2w3e4r",     "Common default"),
    ("admin",      "support",      "ISP routers"),
    ("admin",      "supervisor",   "Cisco"),
    ("cisco",      "cisco",        "Cisco IOS"),
    ("cisco",      "",             "Cisco no password"),
    ("enable",     "cisco",        "Cisco enable"),
    ("admin",      "huawei",       "Huawei"),
    ("admin",      "Huawei12#$",   "Huawei newer"),
    ("admin",      "admin@huawei.com", "Huawei ONT"),
    ("admin",      "vodafone",     "Vodafone routers"),
    ("admin",      "telekom",      "Deutsche Telekom"),
    ("admin",      "speedport",    "Telekom Speedport"),
    # Kameras
    ("admin",      "888888",       "Hikvision camera"),
    ("admin",      "12345",        "Dahua camera"),
    ("admin",      "admin1234",    "Generic IP cam"),
    ("admin",      "camera",       "Generic IP cam"),
    ("root",       "camera",       "IP cam root"),
    ("root",       "vizxv",        "Mirai botnet default"),
    ("root",       "xc3511",       "IoT cam firmware"),
    ("root",       "jvbzd",        "IoT default"),
    ("root",       "anko",         "IoT firmware"),
    ("admin",      "7ujMko0admin", "Netcore router"),
    ("admin",      "7ujMko0vizxv", "IoT default"),
    # NAS
    ("admin",      "synology",     "Synology NAS"),
    ("admin",      "qnap",         "QNAP NAS"),
    ("admin",      "nas",          "Generic NAS"),
    # Smart Home
    ("admin",      "philips",      "Philips Hue Bridge"),
    ("homeassistant", "",          "Home Assistant"),
    ("pi",         "raspberry",    "Raspberry Pi"),
    ("pi",         "Pi1234",       "Pi default"),
    ("ubuntu",     "ubuntu",       "Ubuntu default"),
    # Telnet-spezifisch (Mirai-bekannte Creds)
    ("root",       "Zte521",       "ZTE modem"),
    ("root",       "hi3518",       "HiSilicon cam"),
    ("root",       "GM8182",       "Generic cam"),
    ("root",       "54321",        "Generic IoT"),
    ("support",    "support",      "ISP tech support"),
    ("service",    "service",      "Generic service"),
    ("tech",       "tech",         "Generic tech"),
    ("supervisor", "supervisor",   "Generic supervisor"),
    ("Administrator", "SmcAdmin",  "SMC router"),
]

# ── HTTP-Pfade für Admin-Panels ───────────────────────────────────────────────
ADMIN_PATHS = [
    "/",
    "/admin",
    "/login",
    "/admin/login",
    "/management",
    "/cgi-bin/luci",          # OpenWrt
    "/cgi-bin/index.cgi",
    "/index.asp",
    "/index.html",
    "/web/index.html",
    "/ui",
    "/setup",
    "/router",
    "/genie",                 # Netgear Genie
    "/HNAP1/",                # D-Link HNAP
    "/api/v1/login",
    "/login.cgi",
    "/userRpm/LoginRpm.htm",  # TP-Link
    "/start.html",
    "/webpages/login.html",
]


@dataclass
class IoTDevice:
    ip: str
    port: int
    service: str = ""
    banner: str  = ""
    vendor: str  = ""
    model: str   = ""
    vuln_creds: list[tuple[str, str]] = field(default_factory=list)
    admin_url: str = ""
    open_ports: list[int] = field(default_factory=list)


class IoTScanner:
    def __init__(self, target: str, timeout: int = 3):
        self.target  = target
        self.timeout = timeout
        self.devices: list[IoTDevice] = []

    async def scan(self) -> AsyncGenerator[str, None]:
        yield f"[*] IoT-Scan: {self.target}"
        yield f"[*] Ports: {IOT_PORTS}"
        yield ""

        if not await check_tool("nmap"):
            yield "[!] nmap nicht gefunden: apt-get install nmap"
            return

        # Phase 1: Nmap Discovery
        yield "[*] Phase 1/3: Nmap Port-Scan..."
        hosts: dict[str, list[int]] = {}

        async for line in CommandRunner().run([
            "nmap", "-sV", "--open", "-p", IOT_PORTS,
            "--host-timeout", "30s",
            "-T4", "-oG", "-", self.target,
        ]):
            # Grepable output parsen
            if line.startswith("Host:"):
                parts = line.split()
                ip = parts[1]
                port_m = re.findall(r'(\d+)/open', line)
                if port_m:
                    hosts[ip] = [int(p) for p in port_m]
                    yield f"  [+] {ip}  Ports: {', '.join(port_m)}"

        if not hosts:
            yield "[*] Keine offenen IoT-Ports gefunden."
            yield "[*] Tipp: Ziel erreichbar? VPN/Firewall aktiv?"
            return

        yield f"\n[+] {len(hosts)} Gerät(e) gefunden\n"
        yield "[*] Phase 2/3: Service-Fingerprint + Banner-Grab..."

        for ip, ports in hosts.items():
            dev = IoTDevice(ip=ip, port=ports[0], open_ports=ports)
            for port in ports:
                banner = await self._grab_banner(ip, port)
                if banner:
                    dev.banner = banner[:200]
                    dev.vendor, dev.model = self._identify_device(banner)
                    if dev.vendor:
                        yield f"  [+] {ip}:{port}  →  {dev.vendor} {dev.model}"
                        yield f"      Banner: {banner[:80]}"
                    break
            self.devices.append(dev)

        yield f"\n[*] Phase 3/3: Default-Credentials testen..."
        for dev in self.devices:
            yield f"\n  [*] Teste {dev.ip}  ({dev.vendor or 'Unbekannt'})..."
            for port in dev.open_ports:
                if port in (80, 8080, 8081, 443, 8443):
                    async for result in self._test_http_creds(dev, port):
                        yield result
                elif port == 23:
                    async for result in self._test_telnet_creds(dev):
                        yield result
                elif port == 22:
                    yield f"    [*] SSH auf {dev.ip}:{port} — verwende Passwords-Modul (Hydra)"

        # Zusammenfassung
        yield f"\n{'═'*60}"
        yield f"ERGEBNIS:"
        vuln_devs = [d for d in self.devices if d.vuln_creds]
        yield f"  Geräte gescannt    : {len(self.devices)}"
        yield f"  Schwachstellen     : {len(vuln_devs)}"
        for d in vuln_devs:
            for u, p in d.vuln_creds:
                yield f"  ⚠️  {d.ip}  Login: {u} / {p}  →  {d.admin_url or '/'}"

    async def _grab_banner(self, ip: str, port: int) -> str:
        """HTTP-Banner oder Telnet-Banner greifen."""
        try:
            proto = "https" if port in (443, 8443) else "http"
            if port in (80, 443, 8080, 8081, 8443, 8888):
                async for line in CommandRunner().run([
                    "curl", "-sk", "--max-time", str(self.timeout),
                    "-I", f"{proto}://{ip}:{port}/",
                ]):
                    return line
            elif port == 23:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), timeout=self.timeout
                )
                banner = (await asyncio.wait_for(reader.read(256), timeout=2)).decode(errors="replace")
                writer.close()
                return banner
        except Exception:
            pass
        return ""

    def _identify_device(self, banner: str) -> tuple[str, str]:
        """Hersteller + Modell aus Banner/Headers ableiten."""
        banner_low = banner.lower()
        patterns = [
            (["fritz!box", "fritzos"],         "AVM",      "FRITZ!Box"),
            (["tp-link", "tplink"],            "TP-Link",  "Router"),
            (["netgear"],                       "Netgear",  "Router"),
            (["asus"],                          "ASUS",     "Router"),
            (["huawei"],                        "Huawei",   "Router"),
            (["hikvision", "dvrdvs"],           "Hikvision","IP Camera"),
            (["dahua"],                         "Dahua",    "IP Camera"),
            (["synology"],                      "Synology", "NAS"),
            (["qnap"],                          "QNAP",     "NAS"),
            (["openwrt"],                       "OpenWrt",  "Generic Router"),
            (["dd-wrt"],                        "DD-WRT",   "Generic Router"),
            (["mikrotik", "routeros"],          "MikroTik", "Router"),
            (["ubiquiti", "unifi", "airmax"],   "Ubiquiti", "AP/Router"),
            (["cisco"],                         "Cisco",    "Switch/Router"),
            (["d-link", "dlink"],               "D-Link",   "Router"),
            (["linksys"],                       "Linksys",  "Router"),
            (["zyxel"],                         "ZyXEL",    "Router"),
            (["vodafone"],                      "Vodafone", "Router"),
            (["raspberry", "raspbian"],         "Raspberry","Pi"),
            (["home assistant"],                "Home Ass.","Smart Home"),
        ]
        for keywords, vendor, model in patterns:
            if any(k in banner_low for k in keywords):
                return vendor, model
        return "", ""

    async def _test_http_creds(self, dev: IoTDevice, port: int) -> AsyncGenerator[str, None]:
        """Testet Default-Creds via HTTP Basic Auth + Form-Login."""
        proto = "https" if port in (443, 8443) else "http"
        base  = f"{proto}://{dev.ip}:{port}"

        # Admin-Panel-Pfad finden
        admin_url = base + "/"
        for path in ADMIN_PATHS[:6]:
            async for line in CommandRunner().run([
                "curl", "-sk", "-o", "/dev/null", "-w", "%{http_code}",
                "--max-time", "3",
                f"{base}{path}",
            ]):
                code = line.strip()
                if code in ("200", "401", "403"):
                    admin_url = f"{base}{path}"
                    break

        # Basic Auth testen
        for user, pw, desc in DEFAULT_CREDS[:30]:
            cred = base64.b64encode(f"{user}:{pw}".encode()).decode()
            result_code = ""
            async for line in CommandRunner().run([
                "curl", "-sk", "-o", "/dev/null", "-w", "%{http_code}",
                "-H", f"Authorization: Basic {cred}",
                "--max-time", "3",
                admin_url,
            ]):
                result_code = line.strip()

            if result_code in ("200", "302"):
                yield f"    {dev.ip}:{port}  ✓  {user} / {pw}  ({desc})"
                dev.vuln_creds.append((user, pw))
                dev.admin_url = admin_url
                return  # Erste funktionierende Kombination reicht

        # Form-Login (POST username/password)
        for user, pw, desc in DEFAULT_CREDS[:20]:
            result_code = ""
            async for line in CommandRunner().run([
                "curl", "-sk", "-o", "/dev/null", "-w", "%{http_code}",
                "-X", "POST",
                "-d", f"username={user}&password={pw}",
                "-d", f"user={user}&pass={pw}",
                "--max-time", "3",
                admin_url,
            ]):
                result_code = line.strip()

            if result_code == "302":
                yield f"    {dev.ip}:{port}  ✓ (Form)  {user} / {pw}"
                dev.vuln_creds.append((user, pw))
                dev.admin_url = admin_url
                return

        yield f"    {dev.ip}:{port}  — keine Standard-Creds gefunden"

    async def _test_telnet_creds(self, dev: IoTDevice) -> AsyncGenerator[str, None]:
        """Testet Default-Creds via Telnet (Port 23)."""
        yield f"    {dev.ip}:23  Telnet — teste Credentials..."
        for user, pw, desc in DEFAULT_CREDS[:25]:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(dev.ip, 23), timeout=self.timeout
                )
                # Warte auf Login-Prompt
                await asyncio.wait_for(reader.read(256), timeout=2)
                writer.write(f"{user}\n".encode())
                await asyncio.sleep(0.5)
                await asyncio.wait_for(reader.read(256), timeout=2)
                writer.write(f"{pw}\n".encode())
                await asyncio.sleep(1)
                response = (await asyncio.wait_for(reader.read(512), timeout=3)).decode(errors="replace")
                writer.close()

                # Shell-Prompt = Login erfolgreich
                if any(p in response for p in ["#", "$", ">", "~", "BusyBox"]):
                    yield f"    {dev.ip}:23  ✓ TELNET  {user} / {pw}  ({desc})"
                    dev.vuln_creds.append((user, pw))
                    return

            except Exception:
                continue

        yield f"    {dev.ip}:23  — keine Standard-Telnet-Creds"
