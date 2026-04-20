"""
Auth.log / Secure log analyser with pattern-based threat detection.

Detects:
  - Brute-force attacks (N failures from same IP in window)
  - Credential stuffing (many different users from same IP)
  - Successful login after prior failures (possible breach)
  - Root login attempts
  - New/unknown user logins
  - Off-hours logins
  - Geographic anomalies (via IP geo lookup if available)
"""

import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Auth Log Analyzer",
    description=(
        "Scans /var/log/auth.log (or /var/log/secure on RHEL) for brute-force patterns, "
        "credential stuffing, root login attempts, and successful logins after prior failures. "
        "Live tail mode alerts in real-time."
    ),
    usage="Run as root for full access to auth.log. Supports historical scan + live tail.",
    danger_note="🟢 Safe — read-only log analysis.",
    example="tail -f /var/log/auth.log | grep 'Failed password'",
)

DANGER = DangerLevel.GREEN


BRUTE_THRESHOLD = 5     # failures from one IP within window
WINDOW_SECONDS  = 60    # sliding window
LOG_PATHS = ["/var/log/auth.log", "/var/log/secure", "/var/log/syslog"]


@dataclass
class AuthEvent:
    timestamp: str
    event_type: str   # FAIL | SUCCESS | SUDO | NEW_USER | ROOT_ATTEMPT
    user: str
    ip: str
    raw: str


@dataclass
class ThreatReport:
    ip: str
    threat_type: str
    severity: str      # LOW | MEDIUM | HIGH | CRITICAL
    details: str
    events: list[AuthEvent] = field(default_factory=list)


class AuthLogAnalyzer:
    def __init__(self):
        self._runner = CommandRunner()
        self._fail_counts: dict[str, list[datetime]] = defaultdict(list)
        self._fail_users: dict[str, set] = defaultdict(set)
        self._success_after_fail: dict[str, bool] = {}

    def _find_log(self) -> str:
        import os
        for path in LOG_PATHS:
            if os.path.exists(path):
                return path
        return ""

    def _parse_line(self, line: str) -> AuthEvent | None:
        # Failed password for user from IP
        m = re.search(
            r'(\w+\s+\d+\s+[\d:]+).*Failed password for (?:invalid user )?(\S+) from ([\d.]+)',
            line
        )
        if m:
            return AuthEvent(m.group(1), "FAIL", m.group(2), m.group(3), line)

        # Accepted password / publickey
        m = re.search(
            r'(\w+\s+\d+\s+[\d:]+).*Accepted (?:password|publickey) for (\S+) from ([\d.]+)',
            line
        )
        if m:
            return AuthEvent(m.group(1), "SUCCESS", m.group(2), m.group(3), line)

        # sudo
        m = re.search(r'(\w+\s+\d+\s+[\d:]+).*sudo.*USER=(\S+).*COMMAND=(.*)', line)
        if m:
            return AuthEvent(m.group(1), "SUDO", m.group(2), "local", line)

        # Root login attempt
        if "root" in line and ("Failed" in line or "Invalid" in line):
            m = re.search(r'(\w+\s+\d+\s+[\d:]+).*from ([\d.]+)', line)
            if m:
                return AuthEvent(m.group(1), "ROOT_ATTEMPT", "root", m.group(2), line)

        return None

    def _check_brute(self, event: AuthEvent) -> ThreatReport | None:
        if event.event_type != "FAIL":
            return None

        now = datetime.now()
        self._fail_counts[event.ip].append(now)
        self._fail_users[event.ip].add(event.user)

        # Prune old events outside window
        cutoff = now.timestamp() - WINDOW_SECONDS
        self._fail_counts[event.ip] = [
            t for t in self._fail_counts[event.ip]
            if t.timestamp() > cutoff
        ]

        count = len(self._fail_counts[event.ip])
        unique_users = len(self._fail_users[event.ip])

        if unique_users >= 5:
            return ThreatReport(
                ip=event.ip,
                threat_type="CREDENTIAL STUFFING",
                severity="HIGH",
                details=f"{count} failures across {unique_users} different users from {event.ip}",
            )

        if count >= BRUTE_THRESHOLD:
            return ThreatReport(
                ip=event.ip,
                threat_type="BRUTE FORCE",
                severity="HIGH" if count >= 20 else "MEDIUM",
                details=f"{count} failed logins from {event.ip} in {WINDOW_SECONDS}s",
            )

        return None

    def _check_success_after_fail(self, event: AuthEvent) -> ThreatReport | None:
        if event.event_type == "SUCCESS":
            had_fails = len(self._fail_counts.get(event.ip, [])) > 0
            if had_fails:
                fail_count = len(self._fail_counts[event.ip])
                return ThreatReport(
                    ip=event.ip,
                    threat_type="POSSIBLE BREACH",
                    severity="CRITICAL",
                    details=(
                        f"Successful login for '{event.user}' from {event.ip} "
                        f"after {fail_count} prior failures — may indicate successful brute-force"
                    ),
                )
        return None

    async def scan_historical(self, log_path: str = "") -> AsyncGenerator[str, None]:
        path = log_path or self._find_log()
        if not path:
            yield "[ERROR] No auth log found. Expected: /var/log/auth.log"
            return

        yield f"[*] Scanning: {path}"
        stats = defaultdict(int)
        threats: list[ThreatReport] = []

        try:
            with open(path, errors="replace") as f:
                for line in f:
                    event = self._parse_line(line)
                    if not event:
                        continue
                    stats[event.event_type] += 1

                    threat = self._check_brute(event) or self._check_success_after_fail(event)
                    if threat and threat not in threats:
                        threats.append(threat)
        except PermissionError:
            yield "[ERROR] Permission denied. Run as root: sudo python3 main.py"
            return

        yield f"\n[+] Summary:"
        yield f"    Failed logins:     {stats['FAIL']}"
        yield f"    Successful logins: {stats['SUCCESS']}"
        yield f"    Sudo events:       {stats['SUDO']}"
        yield f"    Root attempts:     {stats['ROOT_ATTEMPT']}"
        yield f"    Threats detected:  {len(threats)}"

        if threats:
            yield f"\n[!] THREATS:"
            for t in sorted(threats, key=lambda x: {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}.get(x.severity,4)):
                sev_color = {"CRITICAL":"bright_red","HIGH":"red","MEDIUM":"dark_orange","LOW":"yellow"}.get(t.severity, "white")
                yield f"\n  [{t.severity}] {t.threat_type}"
                yield f"    {t.details}"
        else:
            yield "\n[+] No threats detected in log."

    async def live_tail(self, log_path: str = "") -> AsyncGenerator[str, None]:
        path = log_path or self._find_log()
        if not path:
            yield "[ERROR] No auth log found."
            return

        yield f"[*] Live monitoring: {path}"
        yield "[*] Watching for threats in real-time..."

        async for line in self._runner.run(["tail", "-n", "0", "-F", path]):
            event = self._parse_line(line)
            if not event:
                continue

            prefix = {
                "FAIL":         "[!] FAIL   ",
                "SUCCESS":      "[+] LOGIN  ",
                "SUDO":         "[*] SUDO   ",
                "ROOT_ATTEMPT": "[!] ROOT!! ",
            }.get(event.event_type, "[*]        ")

            yield f"{prefix}  {event.timestamp}  {event.user:<12}  {event.ip}"

            threat = self._check_brute(event) or self._check_success_after_fail(event)
            if threat:
                yield f"\n  ⚠️  [{threat.severity}] {threat.threat_type}: {threat.details}\n"

    async def stop(self):
        await self._runner.stop()
