"""
Searchsploit / CVE Engine — Exploit-DB Integration.

Sucht Exploits für:
  - CVE-Nummern (z.B. CVE-2021-44228)
  - Software + Version (z.B. Apache 2.4.49)
  - Nmap-Output (parst automatisch alle Services + sucht Exploits)

Voraussetzungen:
  apt install exploitdb   # searchsploit
  oder: git clone https://github.com/offensive-security/exploitdb /opt/exploitdb
"""

from __future__ import annotations
import re
import shutil
from typing import AsyncGenerator

from core.runner import CommandRunner

runner = CommandRunner()


# ── Searchsploit Wrapper ──────────────────────────────────────────────────────

async def search_exploit(query: str) -> AsyncGenerator[str, None]:
    """Searchsploit für einen Begriff oder CVE."""
    if not shutil.which("searchsploit"):
        yield "\033[33m[!] searchsploit nicht installiert:\033[0m"
        yield "\033[36m    apt install exploitdb\033[0m"
        return

    yield f"\033[1;36m[*] Searchsploit: {query}\033[0m\n"
    async for line in runner.run(["searchsploit", "--color", query]):
        line = line.strip()
        if line and "------" not in line:
            if "Remote" in line or "RCE" in line or "Overflow" in line:
                yield f"\033[31m  {line}\033[0m"
            elif "Local" in line or "Privilege" in line:
                yield f"\033[33m  {line}\033[0m"
            elif "Webapps" in line or "SQL" in line or "XSS" in line:
                yield f"\033[36m  {line}\033[0m"
            else:
                yield f"\033[90m  {line}\033[0m"


async def get_exploit(edb_id: str, show: bool = True) -> AsyncGenerator[str, None]:
    """Exploit-Code anzeigen oder in Datei speichern."""
    if not shutil.which("searchsploit"):
        yield "\033[33m[!] searchsploit nicht installiert\033[0m"
        return

    if show:
        yield f"\033[1;36m[*] Exploit #{edb_id}\033[0m\n"
        async for line in runner.run(["searchsploit", "-x", edb_id]):
            yield f"\033[36m  {line}\033[0m"
    else:
        import os
        from core.output_dir import get as out_dir
        out = os.path.join(out_dir(), f"exploit_{edb_id}.py")
        async for _ in runner.run(["searchsploit", "-m", edb_id, "--dest", out_dir()]):
            pass
        yield f"\033[32m[✓] Exploit kopiert: {out}\033[0m"


# ── Nmap-Output automatisch auswerten ────────────────────────────────────────

def parse_nmap_services(nmap_output: str) -> list[tuple[str, str, str]]:
    """
    Parst Nmap-Output und extrahiert (Host, Port, Service+Version).
    Gibt Liste von (host, port, service_string) zurück.
    """
    results: list[tuple[str, str, str]] = []
    current_host = ""

    for line in nmap_output.splitlines():
        # Nmap report for 192.168.1.1
        m = re.search(r"Nmap scan report for (.+)", line)
        if m:
            current_host = m.group(1).strip()
            continue

        # 80/tcp   open  http    Apache httpd 2.4.49
        m = re.match(r"(\d+)/\w+\s+open\s+\S+\s+(.*)", line)
        if m and current_host:
            port    = m.group(1)
            service = m.group(2).strip()
            if service:
                results.append((current_host, port, service))

    return results


async def auto_exploit_search(nmap_file: str) -> AsyncGenerator[str, None]:
    """
    Liest Nmap-Output-Datei, extrahiert Services und sucht automatisch Exploits.
    """
    import os
    if not os.path.exists(nmap_file):
        yield f"\033[33m[!] Datei nicht gefunden: {nmap_file}\033[0m"
        return

    yield "\033[1;36m[*] Auto-Exploit-Search aus Nmap-Output\033[0m"
    yield f"\033[90m    Datei: {nmap_file}\033[0m\n"

    nmap_content = open(nmap_file).read()
    services = parse_nmap_services(nmap_content)

    if not services:
        yield "\033[33m[!] Keine Services im Nmap-Output gefunden\033[0m"
        return

    yield f"\033[36m  [*] {len(services)} Services gefunden — durchsuche Exploit-DB...\033[0m\n"

    searched: set[str] = set()
    for host, port, service in services:
        # Kürze Service für Suche: "Apache httpd 2.4.49 ((Debian))" → "Apache 2.4.49"
        clean = re.sub(r"\s*\(.*?\)", "", service).strip()
        parts = clean.split()
        query = " ".join(parts[:3]) if len(parts) >= 2 else clean

        if query in searched:
            continue
        searched.add(query)

        yield f"\033[33m[{host}:{port}] {service}\033[0m"
        yield f"\033[90m  → Suche: {query}\033[0m"

        count = 0
        async for line in runner.run(["searchsploit", "--color", query]):
            line = line.strip()
            if line and "------" not in line and "Exploits:" not in line and "Shellcodes:" not in line:
                count += 1
                if "Remote" in line or "RCE" in line:
                    yield f"  \033[31m[!] {line}\033[0m"
                else:
                    yield f"  \033[36m    {line}\033[0m"

        if count == 0:
            yield f"  \033[90m    (keine Treffer)\033[0m"
        yield ""


# ── CVE MITRE Lookup ──────────────────────────────────────────────────────────

async def cve_lookup(cve_id: str) -> AsyncGenerator[str, None]:
    """
    CVE-Detailinfo von MITRE + NVD API.
    Zeigt: Beschreibung, CVSS, EPSS (Exploit-Wahrscheinlichkeit), Referenzen.
    """
    import urllib.request, json

    cve_id = cve_id.upper().strip()
    yield f"\033[1;36m[*] CVE Lookup: {cve_id}\033[0m\n"

    # NVD API v2
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PenKit/3.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        vuln = data["vulnerabilities"][0]["cve"]
        desc = next(
            (d["value"] for d in vuln["descriptions"] if d["lang"] == "en"),
            "Keine Beschreibung"
        )

        yield f"\033[33mBeschreibung:\033[0m"
        yield f"\033[36m  {desc[:300]}{'...' if len(desc)>300 else ''}\033[0m\n"

        metrics = vuln.get("metrics", {})
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if key in metrics:
                m = metrics[key][0]["cvssData"]
                score = m.get("baseScore", "?")
                severity = m.get("baseSeverity", "?")
                vector = m.get("vectorString", "?")
                color = "\033[31m" if float(score) >= 9 else "\033[33m" if float(score) >= 7 else "\033[36m"
                yield f"\033[33mCVSS Score:\033[0m {color}{score} ({severity})\033[0m"
                yield f"\033[36m  {vector}\033[0m\n"
                break

        refs = vuln.get("references", [])[:5]
        if refs:
            yield f"\033[33mReferenzen:\033[0m"
            for ref in refs:
                yield f"\033[36m  {ref['url']}\033[0m"

    except Exception as e:
        yield f"\033[33m[!] NVD API Fehler: {e}\033[0m"

    # Searchsploit für diesen CVE
    yield ""
    yield f"\033[33mExploit-DB Treffer:\033[0m"
    if shutil.which("searchsploit"):
        found = False
        async for line in runner.run(["searchsploit", "--color", cve_id]):
            line = line.strip()
            if line and "------" not in line and "Exploits:" not in line:
                found = True
                yield f"\033[31m  {line}\033[0m"
        if not found:
            yield f"\033[90m  (kein Exploit in Exploit-DB)\033[0m"
    else:
        yield f"\033[33m  searchsploit nicht installiert\033[0m"

    # EPSS Score
    yield ""
    yield f"\033[33mEPSS (Exploit-Wahrscheinlichkeit in 30 Tagen):\033[0m"
    try:
        epss_url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
        req = urllib.request.Request(epss_url, headers={"User-Agent": "PenKit/3.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            epss_data = json.loads(resp.read())
        if epss_data.get("data"):
            score = float(epss_data["data"][0]["epss"])
            pct = float(epss_data["data"][0]["percentile"])
            color = "\033[31m" if score > 0.5 else "\033[33m" if score > 0.1 else "\033[36m"
            yield f"{color}  {score:.1%} Wahrscheinlichkeit (Percentile: {pct:.0%})\033[0m"
    except Exception:
        yield "\033[90m  (EPSS nicht verfügbar)\033[0m"


# ── Top CVEs des Jahres ───────────────────────────────────────────────────────

TOP_CVES_2024 = [
    ("CVE-2024-3400",  "Palo Alto PAN-OS — RCE via GlobalProtect (CVSS 10.0)",      "critical"),
    ("CVE-2024-21887", "Ivanti Connect Secure — Command Injection (CVSS 9.1)",       "critical"),
    ("CVE-2024-1709",  "ConnectWise ScreenConnect — Auth Bypass (CVSS 10.0)",        "critical"),
    ("CVE-2023-44487", "HTTP/2 Rapid Reset — DDoS (CVSS 7.5)",                       "high"),
    ("CVE-2023-46604", "Apache ActiveMQ — RCE (CVSS 10.0)",                          "critical"),
    ("CVE-2021-44228", "Log4Shell — Log4j RCE (CVSS 10.0)",                          "critical"),
    ("CVE-2022-47966", "ManageEngine — RCE via SAML (CVSS 9.8)",                     "critical"),
    ("CVE-2023-20198", "Cisco IOS XE — Privilege Escalation (CVSS 10.0)",            "critical"),
]

async def show_top_cves() -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Top CVEs — hochkritische aktuelle Exploits\033[0m\n"
    for cve_id, desc, severity in TOP_CVES_2024:
        color = "\033[31m" if severity == "critical" else "\033[33m"
        yield f"  {color}[{cve_id}]\033[0m  {desc}"
    yield ""
    yield "\033[36m  searchsploit <CVE-ID>  — Exploit-Code holen\033[0m"
    yield "\033[36m  Option 3 im Menü       — CVE Details + EPSS abrufen\033[0m"
