"""
Web vulnerability scanner wrapping nikto + nuclei.

nikto  — broad CVE/misconfig scanner, great first pass
nuclei — template-based, finds real exploitable bugs fast

Auto-chains: nikto quick scan → nuclei critical/high templates → report
"""

import os
from typing import AsyncGenerator
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Vuln Scanner (nikto + nuclei)",
    description=(
        "Two-stage web vulnerability scanner: "
        "nikto for broad CVE/misconfig coverage, then nuclei for template-based "
        "precision. Filters output to show only critical/high findings."
    ),
    usage="Provide full URL. Nuclei auto-updates templates on first run.",
    danger_note="🟠 Medium Risk — sends potentially intrusive probes. Only on authorized targets.",
    example="nuclei -u https://target.com -severity critical,high",
)

DANGER = DangerLevel.ORANGE


class WebVulnScanner:
    def __init__(self):
        self._runner = CommandRunner()

    async def nikto_scan(self, url: str, tuning: str = "x 6") -> AsyncGenerator[str, None]:
        yield f"[*] nikto scan: {url}"
        yield "[*] This takes 3-10 minutes for a full scan"

        cmd = [
            "nikto",
            "-h", url,
            "-Format", "txt",
            "-nointeractive",
            "-Tuning", tuning,   # x=all, 6=injection
        ]

        interesting_prefixes = ("+ ", "OSVDB-", "CVE-", "Server:", "ERROR")
        async for line in self._runner.run(cmd):
            stripped = line.strip()
            if any(stripped.startswith(p) for p in interesting_prefixes):
                if "OSVDB-0" not in stripped:  # filter noisy false positives
                    yield f"[!] {stripped}"
            elif stripped and not stripped.startswith("-"):
                yield stripped

    async def nuclei_scan(
        self,
        url: str,
        severity: str = "critical,high,medium",
        tags: str = "",
    ) -> AsyncGenerator[str, None]:
        yield f"[*] nuclei scan: {url}"
        yield f"[*] Severity filter: {severity}"

        cmd = [
            "nuclei",
            "-u", url,
            "-severity", severity,
            "-silent",
            "-nc",
            "-timeout", "10",
            "-retries", "1",
        ]
        if tags:
            cmd += ["-tags", tags]

        findings = []
        async for line in self._runner.run(cmd):
            stripped = line.strip()
            if not stripped:
                continue
            # nuclei output: [template-id] [proto] [severity] url
            if "] [" in stripped:
                findings.append(stripped)
                severity_part = ""
                if "[critical]" in stripped.lower():
                    severity_part = "CRITICAL"
                elif "[high]" in stripped.lower():
                    severity_part = "HIGH"
                elif "[medium]" in stripped.lower():
                    severity_part = "MEDIUM"
                yield f"[{severity_part or '?'}] {stripped}"
            else:
                yield stripped

        yield f"\n[+] nuclei complete: {len(findings)} finding(s)"

    async def full_scan(self, url: str) -> AsyncGenerator[str, None]:
        yield f"[*] ── Full Web Vulnerability Scan ──"
        yield f"[*] Target: {url}"
        yield ""
        yield "[*] Phase 1: nikto (broad scan)..."
        async for line in self.nikto_scan(url):
            yield line

        yield ""
        yield "[*] Phase 2: nuclei (template-based precision)..."
        async for line in self.nuclei_scan(url):
            yield line

    async def stop(self):
        await self._runner.stop()
