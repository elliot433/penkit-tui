"""
Port monitor — detects new open ports on this machine since last check.

On first run: records all currently listening ports as baseline.
On subsequent runs / live mode: diffs current state against baseline,
alerts on any new port that appeared or any port that disappeared.
"""

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Port Monitor",
    description=(
        "Snapshots all currently listening ports (TCP+UDP) and watches for changes. "
        "Alerts when a new port opens (possible backdoor, rogue service) "
        "or a known port disappears (service crash, tampering)."
    ),
    usage="First run saves the baseline. Subsequent runs diff against it. Use Live mode for continuous monitoring.",
    danger_note="🟢 Safe — reads local port state only.",
    example="ss -tlnpu",
)

DANGER = DangerLevel.GREEN

BASELINE_FILE = os.path.expanduser("~/.config/penkit-tui/port_baseline.json")

WELL_KNOWN = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL",
    5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB",
    21: "FTP", 25: "SMTP", 53: "DNS", 8080: "HTTP-alt",
    3389: "RDP", 445: "SMB", 139: "NetBIOS",
}

SUSPICIOUS_PORTS = {
    4444, 1337, 31337, 9999, 6666, 6667, 7777,    # common RAT/backdoor ports
    5554, 54321, 12345, 65535,
}


@dataclass
class PortEntry:
    port: int
    proto: str    # tcp / udp
    addr: str     # 0.0.0.0 / 127.0.0.1 / ::
    pid: str
    process: str


def _get_open_ports() -> list[PortEntry]:
    entries: list[PortEntry] = []
    try:
        out = subprocess.check_output(
            ["ss", "-tlnpu"],
            text=True, stderr=subprocess.DEVNULL
        )
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 5:
                continue
            proto = parts[0].lower().split("tcp")[0] or "tcp"
            if "tcp" in parts[0].lower():
                proto = "tcp"
            elif "udp" in parts[0].lower():
                proto = "udp"
            else:
                continue

            local = parts[4] if len(parts) > 4 else ""
            if ":" in local:
                addr, port_str = local.rsplit(":", 1)
            else:
                continue

            try:
                port = int(port_str)
            except ValueError:
                continue

            pid_proc = parts[-1] if len(parts) > 5 else ""
            pid, proc = "", ""
            m_pid = __import__("re").search(r'pid=(\d+)', pid_proc)
            m_proc = __import__("re").search(r'"([^"]+)"', pid_proc)
            if m_pid:
                pid = m_pid.group(1)
            if m_proc:
                proc = m_proc.group(1)

            entries.append(PortEntry(port=port, proto=proto, addr=addr, pid=pid, process=proc))
    except Exception:
        pass
    return entries


class PortMonitor:
    def __init__(self):
        self._runner = CommandRunner()
        self._baseline: dict[str, PortEntry] = {}

    def _key(self, e: PortEntry) -> str:
        return f"{e.proto}:{e.port}"

    def _load_baseline(self) -> dict[str, dict]:
        if os.path.exists(BASELINE_FILE):
            with open(BASELINE_FILE) as f:
                return json.load(f)
        return {}

    def _save_baseline(self, entries: list[PortEntry]):
        os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
        data = {
            self._key(e): {"port": e.port, "proto": e.proto, "addr": e.addr, "process": e.process}
            for e in entries
        }
        with open(BASELINE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    async def snapshot(self) -> AsyncGenerator[str, None]:
        current = _get_open_ports()
        self._save_baseline(current)

        yield f"[+] Baseline saved: {len(current)} ports"
        yield ""
        yield f"  {'PORT':<8} {'PROTO':<6} {'ADDR':<20} {'PROCESS':<20} {'KNOWN AS'}"
        yield f"  {'─'*70}"

        for e in sorted(current, key=lambda x: x.port):
            known = WELL_KNOWN.get(e.port, "")
            suspicious = " ⚠️ SUSPICIOUS" if e.port in SUSPICIOUS_PORTS else ""
            yield f"  {e.port:<8} {e.proto:<6} {e.addr:<20} {e.process:<20} {known}{suspicious}"

    async def diff(self) -> AsyncGenerator[str, None]:
        baseline = self._load_baseline()
        current = _get_open_ports()
        current_map = {self._key(e): e for e in current}

        baseline_keys = set(baseline.keys())
        current_keys  = set(current_map.keys())

        new_ports     = current_keys - baseline_keys
        closed_ports  = baseline_keys - current_keys
        unchanged     = baseline_keys & current_keys

        yield f"[*] Port diff: baseline={len(baseline_keys)}  current={len(current_keys)}"
        yield ""

        if new_ports:
            yield f"[!] NEW PORTS ({len(new_ports)}) — potential rogue services:"
            for key in sorted(new_ports):
                e = current_map[key]
                known = WELL_KNOWN.get(e.port, "unknown service")
                alert = " ⚠️ SUSPICIOUS PORT" if e.port in SUSPICIOUS_PORTS else ""
                yield f"  [NEW] {e.port}/{e.proto}  {e.addr}  {e.process}  ({known}){alert}"
        else:
            yield "[+] No new ports since baseline."

        if closed_ports:
            yield f"\n[*] CLOSED PORTS ({len(closed_ports)}) — services that disappeared:"
            for key in sorted(closed_ports):
                b = baseline[key]
                yield f"  [GONE] {b['port']}/{b['proto']}  {b.get('process','?')}"

        if not new_ports and not closed_ports:
            yield "[+] Port state unchanged."

    async def live_watch(self, interval: int = 10) -> AsyncGenerator[str, None]:
        yield f"[*] Live port monitor — checking every {interval}s"
        yield "[*] Press STOP to end"

        baseline = self._load_baseline()
        if not baseline:
            current = _get_open_ports()
            self._save_baseline(current)
            baseline = {self._key(e): {"port": e.port, "proto": e.proto, "addr": e.addr, "process": e.process} for e in current}
            yield f"[*] No baseline found — created one with {len(baseline)} ports"

        while True:
            await asyncio.sleep(interval)
            current = _get_open_ports()
            current_map = {self._key(e): e for e in current}

            new_ports = set(current_map.keys()) - set(baseline.keys())
            for key in new_ports:
                e = current_map[key]
                alert = " ⚠️ SUSPICIOUS" if e.port in SUSPICIOUS_PORTS else ""
                yield f"\n[!] NEW PORT: {e.port}/{e.proto}  process={e.process}{alert}"

            baseline = {self._key(e): {"port": e.port, "proto": e.proto, "addr": e.addr, "process": e.process} for e in current}

    async def stop(self):
        await self._runner.stop()
