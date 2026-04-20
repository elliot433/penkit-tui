"""
Target fingerprinter — first thing that runs before any web attack.

Detects: WAF, CMS (WordPress/Joomla/Drupal/etc.), framework, server,
tech stack, interesting headers, robots.txt secrets, and auto-routes
to the best follow-up scanner.
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Web Fingerprinter",
    description=(
        "Identifies WAF, CMS, server technology, and framework before any attack. "
        "Combines whatweb + wafw00f + curl header analysis. "
        "Auto-recommends the best follow-up tool for the detected stack."
    ),
    usage="Provide full URL. HTTP and HTTPS supported. Scans passively first.",
    danger_note="🟡 Low Risk — sends standard HTTP requests, nothing destructive.",
    example="whatweb -a 3 https://target.com",
)

DANGER = DangerLevel.YELLOW

# CMS → recommended follow-up tools
CMS_TOOLS = {
    "wordpress": ["wpscan", "sqlmap", "ffuf"],
    "joomla":    ["joomscan", "sqlmap", "ffuf"],
    "drupal":    ["droopescan", "sqlmap", "ffuf"],
    "magento":   ["magescan", "sqlmap"],
    "phpbb":     ["sqlmap", "ffuf"],
}


@dataclass
class FingerResult:
    url: str
    server: str = ""
    cms: str = ""
    waf: str = ""
    framework: str = ""
    technologies: list[str] = field(default_factory=list)
    interesting_paths: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class WebFingerprinter:
    def __init__(self):
        self._runner = CommandRunner()
        self._result = FingerResult(url="")

    async def fingerprint(self, url: str) -> AsyncGenerator[str, None]:
        self._result = FingerResult(url=url)
        yield f"[*] Target: {url}"
        yield "[*] ── Step 1: WAF Detection ──"
        async for line in self._detect_waf(url):
            yield line

        yield "\n[*] ── Step 2: Technology Stack ──"
        async for line in self._whatweb(url):
            yield line

        yield "\n[*] ── Step 3: Header Analysis ──"
        async for line in self._header_analysis(url):
            yield line

        yield "\n[*] ── Step 4: Robots / Sitemap ──"
        async for line in self._check_robots(url):
            yield line

        yield "\n[+] ── Recommendations ──"
        for rec in self._build_recommendations():
            yield f"  → {rec}"

    async def _detect_waf(self, url: str) -> AsyncGenerator[str, None]:
        async for line in CommandRunner().run(["wafw00f", url]):
            if "is behind" in line.lower():
                waf = re.search(r'behind (.+)', line, re.I)
                if waf:
                    self._result.waf = waf.group(1).strip()
                yield f"[!] WAF detected: {self._result.waf}"
            elif "no waf" in line.lower() or "not protected" in line.lower():
                yield "[+] No WAF detected"
            elif line.strip():
                yield line

    async def _whatweb(self, url: str) -> AsyncGenerator[str, None]:
        async for line in CommandRunner().run(["whatweb", "-a", "3", "--color=never", url]):
            # Parse key fields
            for cms in ["WordPress", "Joomla", "Drupal", "Magento", "phpBB", "Typo3"]:
                if cms.lower() in line.lower():
                    self._result.cms = cms.lower()
                    yield f"[+] CMS detected: {cms}"
            for framework in ["Laravel", "Django", "Rails", "ASP.NET", "Spring", "Express"]:
                if framework.lower() in line.lower():
                    self._result.framework = framework
                    yield f"[+] Framework: {framework}"
            if "Apache" in line or "nginx" in line or "IIS" in line:
                m = re.search(r'(Apache|nginx|IIS)[^\s,\]]*', line)
                if m:
                    self._result.server = m.group(0)
                    yield f"[+] Server: {self._result.server}"
            elif line.strip():
                yield line

    async def _header_analysis(self, url: str) -> AsyncGenerator[str, None]:
        async for line in CommandRunner().run([
            "curl", "-sI", "--max-time", "10",
            "-A", "Mozilla/5.0",
            url,
        ]):
            line_lower = line.lower()
            # Flag interesting / dangerous headers
            if "x-powered-by" in line_lower:
                yield f"[+] {line.strip()}  ← leaks technology"
            elif "server:" in line_lower:
                yield f"[+] {line.strip()}"
            elif "strict-transport-security" not in line_lower and "x-frame-options" not in line_lower:
                if "set-cookie" in line_lower and "httponly" not in line_lower:
                    yield f"[!] Cookie without HttpOnly: {line.strip()}"
                elif line.strip():
                    yield f"    {line.strip()}"

    async def _check_robots(self, url: str) -> AsyncGenerator[str, None]:
        base = url.rstrip("/")
        for path in ["/robots.txt", "/sitemap.xml", "/.git/HEAD", "/.env"]:
            r = CommandRunner()
            async for line in r.run([
                "curl", "-so", "/dev/null", "-w", "%{http_code}",
                "--max-time", "5", f"{base}{path}"
            ]):
                code = line.strip()
                if code == "200":
                    yield f"[+] Found: {base}{path}"
                    self._result.interesting_paths.append(path)
                    # Fetch content for robots.txt
                    if "robots" in path:
                        r2 = CommandRunner()
                        async for l2 in r2.run(["curl", "-s", "--max-time", "5", f"{base}{path}"]):
                            if "Disallow" in l2 or "Allow" in l2:
                                yield f"    {l2.strip()}"
                elif code in ("301", "302", "403"):
                    yield f"[*] {code}: {base}{path}"

    def _build_recommendations(self) -> list[str]:
        recs = []
        if self._result.waf:
            recs.append(f"WAF present ({self._result.waf}) — use evasion: ffuf -fw, sqlmap --tamper=space2comment")
        if self._result.cms:
            tools = CMS_TOOLS.get(self._result.cms, ["sqlmap", "ffuf"])
            recs.append(f"CMS: {self._result.cms} → run: {', '.join(tools)}")
        if "/.git/HEAD" in self._result.interesting_paths:
            recs.append("Git repo exposed! → git-dumper https://target.com/.git/ /tmp/dump")
        if "/.env" in self._result.interesting_paths:
            recs.append("/.env exposed — likely contains DB credentials and API keys!")
        if not self._result.waf:
            recs.append("No WAF — direct scanning safe: nikto, nuclei, sqlmap")
        if not recs:
            recs.append("Run: nikto + ffuf for baseline recon")
        return recs

    def get_result(self) -> FingerResult:
        return self._result

    async def stop(self):
        await self._runner.stop()
