"""
Auto-Recon Pipeline — vollautomatische Aufklärung.

Ablauf (1 Domain → fertiger Report):
  Phase 1: Subdomain Enumeration     (subfinder + amass + crt.sh API)
  Phase 2: Live-Host Check           (httpx — welche antworten?)
  Phase 3: Port Scan                 (nmap — Services + Versionen)
  Phase 4: Web Fingerprinting        (whatweb + wafw00f)
  Phase 5: Vulnerability Scan        (nuclei — CVE Templates)
  Phase 6: Screenshot                (gowitness / aquatone)
  Phase 7: Report                    (HTML-Report mit allen Findings)

Install (einmalig auf Kali):
  apt install nmap whatweb wafw00f
  go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
  go install github.com/projectdiscovery/httpx/cmd/httpx@latest
  go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
  go install github.com/projectdiscovery/amass/v4/...@latest
  go install github.com/sensepost/gowitness@latest
"""

from __future__ import annotations
import asyncio
import json
import os
import shutil
import urllib.request
from datetime import datetime
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


runner = CommandRunner()


# ── Phase 1: Subdomain Enumeration ───────────────────────────────────────────

async def enumerate_subdomains(domain: str, out_file: str) -> AsyncGenerator[str, None]:
    yield f"\033[1;36m[Phase 1] Subdomain Enumeration → {domain}\033[0m"

    subdomains: set[str] = set()

    # subfinder
    if shutil.which("subfinder"):
        yield "\033[36m  [*] subfinder läuft...\033[0m"
        async for line in runner.run(["subfinder", "-d", domain, "-silent"]):
            sub = line.strip()
            if sub and "." in sub:
                subdomains.add(sub)
        yield f"\033[32m  [+] subfinder: {len(subdomains)} Subdomains\033[0m"
    else:
        yield "\033[33m  [!] subfinder nicht installiert — go install subfinder\033[0m"

    # amass passive
    if shutil.which("amass"):
        prev = len(subdomains)
        yield "\033[36m  [*] amass passive läuft...\033[0m"
        async for line in runner.run(["amass", "enum", "-passive", "-d", domain]):
            sub = line.strip()
            if sub and "." in sub and not sub.startswith("["):
                subdomains.add(sub)
        yield f"\033[32m  [+] amass: +{len(subdomains)-prev} neue Subdomains\033[0m"
    else:
        yield "\033[33m  [!] amass nicht installiert — go install amass\033[0m"

    # crt.sh API (immer verfügbar)
    yield "\033[36m  [*] crt.sh Certificate Transparency...\033[0m"
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent": "PenKit/3.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        prev = len(subdomains)
        for entry in data:
            name = entry.get("name_value", "")
            for sub in name.split("\n"):
                sub = sub.strip().lstrip("*.")
                if sub.endswith(domain):
                    subdomains.add(sub)
        yield f"\033[32m  [+] crt.sh: +{len(subdomains)-prev} neue Subdomains\033[0m"
    except Exception as e:
        yield f"\033[33m  [!] crt.sh Fehler: {e}\033[0m"

    # Ergebnisse speichern
    with open(out_file, "w") as f:
        f.write("\n".join(sorted(subdomains)))

    yield f"\n\033[32m[✓] Phase 1 komplett: {len(subdomains)} Subdomains → {out_file}\033[0m"
    return


# ── Phase 2: Live Host Check ──────────────────────────────────────────────────

async def check_live_hosts(subs_file: str, out_file: str) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[Phase 2] Live-Host Check (HTTP/HTTPS)\033[0m"

    if not os.path.exists(subs_file):
        yield f"\033[33m  [!] {subs_file} nicht gefunden — Phase 1 zuerst\033[0m"
        return

    if shutil.which("httpx"):
        yield "\033[36m  [*] httpx prüft welche Hosts antworten...\033[0m"
        live_count = 0
        async for line in runner.run([
            "httpx", "-l", subs_file, "-o", out_file,
            "-status-code", "-title", "-tech-detect", "-silent",
        ]):
            if line.strip():
                live_count += 1
                yield f"\033[32m  [+] {line.strip()}\033[0m"
        yield f"\n\033[32m[✓] Phase 2: {live_count} Live-Hosts → {out_file}\033[0m"
    else:
        yield "\033[33m  [!] httpx nicht installiert. Fallback: nmap ping-scan\033[0m"
        subs = open(subs_file).read().splitlines()[:50]
        async for line in runner.run(["nmap", "-sn", "--open"] + subs):
            if "Nmap scan" in line or "report for" in line:
                yield f"\033[36m  {line.strip()}\033[0m"
        yield "\033[32m[✓] Phase 2 komplett (nmap fallback)\033[0m"


# ── Phase 3: Port Scan ────────────────────────────────────────────────────────

async def port_scan(live_file: str, out_file: str, fast: bool = False) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[Phase 3] Port Scan + Service Detection\033[0m"

    if not os.path.exists(live_file):
        yield f"\033[33m  [!] {live_file} nicht gefunden\033[0m"
        return

    # Hosts aus httpx-Output extrahieren (URLs → IPs/Hostnamen)
    hosts: list[str] = []
    with open(live_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("http"):
                host = line.split("//")[-1].split("/")[0].split(":")[0]
                if host:
                    hosts.append(host)

    if not hosts:
        yield "\033[33m  [!] Keine Hosts aus Phase 2 gefunden\033[0m"
        return

    yield f"\033[36m  [*] Scanne {len(hosts)} Hosts...\033[0m"

    flags = ["-sV", "--open", "-oN", out_file]
    if fast:
        flags += ["-F", "-T4"]
    else:
        flags += ["--top-ports", "1000", "-T4"]

    async for line in runner.run(["nmap"] + flags + hosts[:20]):
        line = line.strip()
        if line and not line.startswith("#"):
            if "open" in line:
                yield f"\033[32m  {line}\033[0m"
            elif "Nmap scan" in line or "report" in line:
                yield f"\033[33m  {line}\033[0m"

    yield f"\n\033[32m[✓] Phase 3: Port Scan → {out_file}\033[0m"


# ── Phase 4: Web Fingerprinting ───────────────────────────────────────────────

async def web_fingerprint(live_file: str, out_file: str) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[Phase 4] Web Fingerprinting (whatweb + wafw00f)\033[0m"

    if not os.path.exists(live_file):
        yield f"\033[33m  [!] {live_file} nicht gefunden\033[0m"
        return

    urls: list[str] = []
    with open(live_file) as f:
        for line in f:
            url = line.strip().split()[0]
            if url.startswith("http"):
                urls.append(url)

    results: list[str] = []

    for url in urls[:15]:
        yield f"\033[36m  [*] {url}\033[0m"

        if shutil.which("whatweb"):
            async for line in runner.run(["whatweb", "--color=never", "-q", url]):
                if line.strip():
                    yield f"\033[32m      WhatWeb: {line.strip()}\033[0m"
                    results.append(f"whatweb|{url}|{line.strip()}")

        if shutil.which("wafw00f"):
            async for line in runner.run(["wafw00f", url, "-q"]):
                if "is behind" in line or "No WAF" in line:
                    yield f"\033[33m      WAF: {line.strip()}\033[0m"
                    results.append(f"wafw00f|{url}|{line.strip()}")

    with open(out_file, "w") as f:
        f.write("\n".join(results))

    yield f"\n\033[32m[✓] Phase 4: Fingerprinting → {out_file}\033[0m"


# ── Phase 5: Nuclei Vulnerability Scan ───────────────────────────────────────

async def nuclei_scan(live_file: str, out_file: str, severity: str = "medium,high,critical") -> AsyncGenerator[str, None]:
    yield f"\033[1;36m[Phase 5] Nuclei Vulnerability Scan ({severity})\033[0m"

    if not shutil.which("nuclei"):
        yield "\033[33m  [!] nuclei nicht installiert:\033[0m"
        yield "\033[36m      go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest\033[0m"
        yield "\033[36m      nuclei -update-templates\033[0m"
        return

    if not os.path.exists(live_file):
        yield f"\033[33m  [!] {live_file} nicht gefunden\033[0m"
        return

    yield "\033[36m  [*] nuclei Templates updaten...\033[0m"
    async for _ in runner.run(["nuclei", "-update-templates", "-silent"]):
        pass

    yield "\033[36m  [*] Nuclei scan läuft (kann Minuten dauern)...\033[0m"
    findings = 0
    async for line in runner.run([
        "nuclei", "-l", live_file,
        "-severity", severity,
        "-o", out_file,
        "-silent", "-nc",
    ]):
        line = line.strip()
        if line:
            findings += 1
            if "critical" in line.lower():
                yield f"\033[31m  [CRITICAL] {line}\033[0m"
            elif "high" in line.lower():
                yield f"\033[33m  [HIGH] {line}\033[0m"
            else:
                yield f"\033[36m  [MEDIUM] {line}\033[0m"

    yield f"\n\033[32m[✓] Phase 5: {findings} Findings → {out_file}\033[0m"


# ── Phase 6: Screenshots ──────────────────────────────────────────────────────

async def take_screenshots(live_file: str, out_dir_path: str) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[Phase 6] Screenshots (gowitness)\033[0m"

    gowitness_path = os.path.expanduser("~/.go/bin/gowitness")
    if not shutil.which("gowitness") and not os.path.exists(gowitness_path):
        yield "\033[33m  [!] gowitness nicht installiert:\033[0m"
        yield "\033[36m      go install github.com/sensepost/gowitness@latest\033[0m"
        return

    tool = "gowitness" if shutil.which("gowitness") else gowitness_path
    os.makedirs(out_dir_path, exist_ok=True)

    yield "\033[36m  [*] Screenshots werden aufgenommen...\033[0m"
    count = 0
    async for line in runner.run([
        tool, "file", "-f", live_file,
        "--screenshot-path", out_dir_path,
        "--disable-db",
    ]):
        if "screenshot" in line.lower() or "error" in line.lower():
            count += 1
            yield f"\033[36m  {line.strip()}\033[0m"

    yield f"\n\033[32m[✓] Phase 6: Screenshots → {out_dir_path}/\033[0m"


# ── Vollständige Pipeline ─────────────────────────────────────────────────────

async def full_pipeline(
    domain: str,
    fast: bool = False,
    skip_nuclei: bool = False,
    skip_screenshots: bool = True,
) -> AsyncGenerator[str, None]:
    """
    Vollautomatische Recon-Pipeline: Domain → fertiger Report.
    fast=True: schneller aber weniger gründlich.
    """
    base = out_dir()
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = os.path.join(base, f"recon_{domain}_{ts}")
    os.makedirs(work, exist_ok=True)

    subs_file   = os.path.join(work, "subdomains.txt")
    live_file   = os.path.join(work, "live_hosts.txt")
    nmap_file   = os.path.join(work, "portscan.txt")
    fp_file     = os.path.join(work, "fingerprint.txt")
    nuclei_file = os.path.join(work, "vulnerabilities.txt")
    shots_dir   = os.path.join(work, "screenshots")

    yield f"\033[1;35m╔══════════════════════════════════════════════════╗\033[0m"
    yield f"\033[1;35m║  AUTO-RECON PIPELINE — {domain:<26}║\033[0m"
    yield f"\033[1;35m╚══════════════════════════════════════════════════╝\033[0m"
    yield f"\033[90m  Output: {work}\033[0m\n"

    # Phase 1
    async for line in enumerate_subdomains(domain, subs_file):
        yield line
    yield ""

    # Phase 2
    async for line in check_live_hosts(subs_file, live_file):
        yield line
    yield ""

    # Phase 3
    async for line in port_scan(live_file, nmap_file, fast=fast):
        yield line
    yield ""

    # Phase 4
    async for line in web_fingerprint(live_file, fp_file):
        yield line
    yield ""

    # Phase 5
    if not skip_nuclei:
        async for line in nuclei_scan(live_file, nuclei_file):
            yield line
        yield ""

    # Phase 6
    if not skip_screenshots:
        async for line in take_screenshots(live_file, shots_dir):
            yield line
        yield ""

    # Zusammenfassung
    yield "\033[1;32m╔══════════════════════════════════════════════════╗\033[0m"
    yield "\033[1;32m║              RECON ABGESCHLOSSEN                 ║\033[0m"
    yield "\033[1;32m╚══════════════════════════════════════════════════╝\033[0m"

    def count_lines(path: str) -> int:
        try:
            return sum(1 for _ in open(path) if _.strip())
        except Exception:
            return 0

    yield f"\033[36m  Subdomains gefunden:  {count_lines(subs_file)}\033[0m"
    yield f"\033[36m  Live-Hosts:           {count_lines(live_file)}\033[0m"
    yield f"\033[36m  Vulnerabilities:      {count_lines(nuclei_file) if not skip_nuclei else 'übersprungen'}\033[0m"
    yield f"\033[36m  Output-Verzeichnis:   {work}\033[0m"
    yield ""
    yield f"\033[33m  Nächste Schritte:\033[0m"
    yield f"\033[36m  cat {subs_file}   # alle Subdomains\033[0m"
    yield f"\033[36m  cat {live_file}   # Live-Hosts\033[0m"
    yield f"\033[36m  cat {nuclei_file} # Vulnerabilities\033[0m"
