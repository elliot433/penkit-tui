"""
OSINT recon pipeline — auto-chained, result-aware.

Pipeline:
  1. theHarvester  — emails, subdomains, IPs from OSINT sources
  2. Sherlock      — username across 300+ platforms
  3. Sublist3r     — subdomain enumeration
  4. Google Dorks  — pre-built high-value dorks run via googler/linkfinder
  5. Auto-Report   — structured markdown report from all findings

Everything chains: harvested emails → sherlock username check.
Discovered subdomains → fed back to network scanner.
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="OSINT Recon",
    description=(
        "Auto-chained OSINT pipeline: harvests emails/subdomains/IPs, "
        "checks usernames across 300+ platforms (Sherlock), enumerates subdomains, "
        "and generates a structured recon report."
    ),
    usage="Provide target domain (e.g. example.com) or username. Results chain automatically.",
    danger_note="🟡 Low Risk — queries public OSINT sources only. No direct target contact.",
    example="theHarvester -d example.com -b all",
)

DANGER = DangerLevel.YELLOW


HIGH_VALUE_DORKS = [
    'site:{domain} filetype:pdf',
    'site:{domain} filetype:xls OR filetype:xlsx OR filetype:csv',
    'site:{domain} inurl:admin OR inurl:login OR inurl:panel',
    'site:{domain} ext:sql OR ext:db OR ext:backup',
    'site:{domain} "password" OR "credentials" filetype:txt',
    'site:{domain} inurl:wp-admin OR inurl:wp-login',
    '"@{domain}" filetype:pdf OR filetype:doc',
    'site:{domain} -www',  # subdomains
    '"{domain}" site:pastebin.com OR site:github.com',
    '"{company}" site:linkedin.com/in',
]


@dataclass
class OSINTResult:
    target: str
    emails: list[str] = field(default_factory=list)
    subdomains: list[str] = field(default_factory=list)
    ips: list[str] = field(default_factory=list)
    usernames_found: dict[str, list[str]] = field(default_factory=dict)  # username → platforms
    dorks: list[str] = field(default_factory=list)


class OSINTRecon:
    def __init__(self, output_dir: str = "/tmp"):
        self.output_dir = output_dir
        self._result = OSINTResult(target="")

    async def harvest(self, domain: str) -> AsyncGenerator[str, None]:
        self._result.target = domain
        yield f"[*] theHarvester: {domain}"

        sources = "bing,crtsh,dnsdumpster,hackertarget,rapiddns,sublist3r,urlscan"
        out_file = os.path.join(self.output_dir, "penkit_harvest.json")

        async for line in CommandRunner().run([
            "theHarvester",
            "-d", domain,
            "-b", sources,
            "-f", out_file,
            "-l", "500",
        ]):
            # Parse emails
            email_m = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', line)
            for e in email_m:
                if e not in self._result.emails:
                    self._result.emails.append(e)
                    yield f"[+] Email: {e}"

            # Parse subdomains
            if f".{domain}" in line:
                sub_m = re.findall(r'[\w.-]+\.' + re.escape(domain), line)
                for s in sub_m:
                    if s not in self._result.subdomains:
                        self._result.subdomains.append(s)
                        yield f"[+] Subdomain: {s}"

            # Parse IPs
            ip_m = re.findall(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', line)
            for ip in ip_m:
                if ip not in self._result.ips and not ip.startswith("127."):
                    self._result.ips.append(ip)
                    yield f"[+] IP: {ip}"

            elif line.strip():
                yield line

        yield f"\n[+] Harvest done: {len(self._result.emails)} emails, {len(self._result.subdomains)} subdomains, {len(self._result.ips)} IPs"

    async def sherlock(self, username: str) -> AsyncGenerator[str, None]:
        yield f"[*] Sherlock: checking '{username}' across 300+ platforms..."
        out_file = os.path.join(self.output_dir, f"sherlock_{username}.txt")

        async for line in CommandRunner().run([
            "sherlock",
            username,
            "--output", out_file,
            "--print-found",
            "--no-color",
        ]):
            if "[+]" in line or "http" in line.lower():
                yield f"[FOUND] {line.strip()}"
                if username not in self._result.usernames_found:
                    self._result.usernames_found[username] = []
                url_m = re.search(r'https?://\S+', line)
                if url_m:
                    self._result.usernames_found[username].append(url_m.group(0))
            elif "[-]" not in line and line.strip():
                yield line

        count = len(self._result.usernames_found.get(username, []))
        yield f"\n[+] Sherlock done: {username} found on {count} platforms"
        if count > 0:
            yield f"[+] Full results: {out_file}"

    async def subdomain_enum(self, domain: str) -> AsyncGenerator[str, None]:
        yield f"[*] Subdomain enumeration: {domain}"

        # Try sublist3r first
        async for line in CommandRunner().run([
            "sublist3r", "-d", domain, "-t", "10", "-o",
            os.path.join(self.output_dir, "penkit_subdomains.txt"),
        ]):
            if "." in line and domain in line:
                sub = line.strip()
                if sub not in self._result.subdomains:
                    self._result.subdomains.append(sub)
                    yield f"[+] {sub}"
            elif line.strip():
                yield line

        # Also try crt.sh via curl (passive, very reliable)
        yield "[*] Checking crt.sh (Certificate Transparency logs)..."
        async for line in CommandRunner().run([
            "curl", "-s",
            f"https://crt.sh/?q=%.{domain}&output=json",
        ]):
            try:
                records = json.loads(line)
                for r in records:
                    name = r.get("name_value", "")
                    for sub in name.split("\n"):
                        sub = sub.strip().lstrip("*.")
                        if sub.endswith(domain) and sub not in self._result.subdomains:
                            self._result.subdomains.append(sub)
                            yield f"[+] {sub}  (crt.sh)"
            except Exception:
                pass

    async def print_dorks(self, domain: str, company: str = "") -> AsyncGenerator[str, None]:
        yield f"[*] Google Dorks for: {domain}"
        yield "[*] Copy these into your browser or googler:"
        yield ""
        for dork in HIGH_VALUE_DORKS:
            formatted = dork.format(domain=domain, company=company or domain)
            yield f"  {formatted}"
        yield ""
        yield "[*] Run with googler: googler --np '<dork>'"

    async def full_recon(self, domain: str, username: str = "") -> AsyncGenerator[str, None]:
        yield f"[*] ══ Full OSINT Recon: {domain} ══"
        async for l in self.harvest(domain):
            yield l
        yield ""
        async for l in self.subdomain_enum(domain):
            yield l
        yield ""
        async for l in self.print_dorks(domain):
            yield l

        # Auto-sherlock harvested emails as usernames
        if self._result.emails:
            yield "\n[*] Auto-Sherlock from harvested emails..."
            for email in self._result.emails[:3]:
                user = email.split("@")[0]
                yield f"\n[*] Checking username: {user}"
                async for l in self.sherlock(user):
                    yield l

        if username:
            yield f"\n[*] Checking provided username: {username}"
            async for l in self.sherlock(username):
                yield l

        async for l in self.generate_report(domain):
            yield l

    async def generate_report(self, domain: str) -> AsyncGenerator[str, None]:
        report_path = os.path.join(self.output_dir, f"osint_report_{domain}.md")
        r = self._result
        content = f"""# OSINT Report: {domain}

## Emails ({len(r.emails)})
{chr(10).join(f'- {e}' for e in r.emails) or '_None found_'}

## Subdomains ({len(r.subdomains)})
{chr(10).join(f'- {s}' for s in r.subdomains[:50]) or '_None found_'}

## IPs ({len(r.ips)})
{chr(10).join(f'- {ip}' for ip in r.ips) or '_None found_'}

## Usernames Found
{chr(10).join(f'### {u}{chr(10)}' + chr(10).join(f'- {p}' for p in platforms) for u, platforms in r.usernames_found.items()) or '_None checked_'}

## Recommended Next Steps
- Run network scanner on discovered IPs: {', '.join(r.ips[:5])}
- Check each subdomain for web services
- Cross-reference emails with HaveIBeenPwned
"""
        with open(report_path, "w") as f:
            f.write(content)
        yield f"\n[+] Report saved: {report_path}"

    def get_result(self) -> OSINTResult:
        return self._result
