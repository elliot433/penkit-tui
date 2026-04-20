"""
Shodan Intelligence — findet verwundbare Geräte und offene Services global.

Shodan ist die mächtigste Suchmaschine für Internet-connected Devices.
Findet in Sekunden: offene Kameras, Router, ICS/SCADA, ungesicherte DBs etc.

Methoden:
  1. Shodan CLI (shodancli) — benötigt API-Key (free tier: 100 queries/Tag)
  2. Shodan Web Scraper (kein Key) — begrenzt aber funktional
  3. Shodan-Alternative: Censys, Fofa, ZoomEye (alle als Fallback)

Installation: pip3 install shodan --break-system-packages
API-Key: https://account.shodan.io/ (kostenlos registrieren)
"""

from __future__ import annotations
import json
import os
import re
from typing import AsyncGenerator

from core.runner import CommandRunner

runner = CommandRunner()

_KEY_FILE = os.path.expanduser("~/.penkit_shodan_key")


# ── API-Key Management ────────────────────────────────────────────────────────

def save_api_key(key: str):
    with open(_KEY_FILE, "w") as f:
        f.write(key.strip())
    os.chmod(_KEY_FILE, 0o600)


def load_api_key() -> str:
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE) as f:
            return f.read().strip()
    return os.environ.get("SHODAN_API_KEY", "")


# ── Shodan CLI Wrapper ────────────────────────────────────────────────────────

class ShodanLookup:
    """
    Shodan-Integration für PenKit.

    Recherchiert:
    - IP-Adressen: offene Ports, Banner, Vulns, Standort
    - Suchbegriffe: findet alle Geräte eines Typs weltweit
    - Eigenes Netzwerk: was sieht Shodan von DIR aus dem Internet?
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or load_api_key()

    async def _check_shodan_available(self) -> bool:
        """Prüft ob shodan CLI verfügbar ist."""
        import shutil
        return shutil.which("shodan") is not None

    async def setup_key(self, key: str) -> AsyncGenerator[str, None]:
        """Konfiguriert Shodan API-Key."""
        save_api_key(key)
        self.api_key = key
        yield "[*] Initialisiere Shodan API..."
        async for line in runner.run(["shodan", "init", key]):
            yield f"  {line}"
        yield "[+] API-Key gespeichert und konfiguriert"

    async def lookup_ip(self, ip: str) -> AsyncGenerator[str, None]:
        """Holt alle Shodan-Infos zu einer IP."""
        if not self.api_key:
            yield "[!] Kein API-Key — nutze curl Fallback..."
            async for line in self._curl_lookup(ip):
                yield line
            return

        yield f"[*] Shodan Lookup: {ip}"
        yield "─" * 60

        if not await self._check_shodan_available():
            yield "[!] shodan CLI nicht installiert"
            yield "[*] Installiere: pip3 install shodan --break-system-packages"
            async for line in self._curl_lookup(ip):
                yield line
            return

        async for line in runner.run(["shodan", "host", ip]):
            if line.strip():
                yield f"  {line}"

    async def search(
        self,
        query: str,
        limit: int = 20,
        country: str = "",
    ) -> AsyncGenerator[str, None]:
        """Sucht nach Geräten mit Shodan-Query."""
        full_query = query
        if country:
            full_query += f" country:{country}"

        yield f"[*] Shodan Suche: '{full_query}'"
        yield f"[*] Limit: {limit} Ergebnisse"
        yield "─" * 60

        if not self.api_key:
            yield "[!] Kein API-Key — erweiterte Suche benötigt Key"
            yield "[*] Kostenlos registrieren: https://account.shodan.io/"
            yield "[*] Zeige Basis-Ergebnisse via Web-Scraper..."
            async for line in self._web_search(query, limit):
                yield line
            return

        if not await self._check_shodan_available():
            yield "[!] shodan CLI nicht installiert: pip3 install shodan --break-system-packages"
            return

        async for line in runner.run([
            "shodan", "search", "--fields",
            "ip_str,port,org,country_code,product,version,vulns",
            full_query
        ]):
            if line.strip():
                yield f"  {line}"

    async def search_with_python(
        self,
        query: str,
        limit: int = 20,
        country: str = "",
    ) -> AsyncGenerator[str, None]:
        """Sucht via Python shodan-Modul (strukturiertere Ausgabe)."""
        full_query = query
        if country:
            full_query += f" country:{country}"

        yield f"[*] Shodan API Suche: '{full_query}'"
        yield "─" * 60

        try:
            import shodan  # type: ignore
        except ImportError:
            yield "[!] shodan Python-Modul nicht gefunden"
            yield "[*] pip3 install shodan --break-system-packages"
            return

        if not self.api_key:
            yield "[!] API-Key benötigt. Option 1 → API-Key eingeben."
            return

        try:
            api = shodan.Shodan(self.api_key)
            results = api.search(full_query, limit=limit)
            count = results.get("total", 0)
            yield f"[+] {count} Ergebnisse gefunden (zeige {limit})"
            yield ""

            for match in results.get("matches", []):
                ip       = match.get("ip_str", "?")
                port     = match.get("port", "?")
                org      = match.get("org", "?")
                country  = match.get("location", {}).get("country_name", "?")
                product  = match.get("product", "")
                version  = match.get("version", "")
                vulns    = list(match.get("vulns", {}).keys())
                hostname = ", ".join(match.get("hostnames", [])[:2])

                service = f"{product} {version}".strip() or "?"
                vuln_str = f"  🔴 CVEs: {', '.join(vulns[:3])}" if vulns else ""

                yield f"  {ip:<18} :{port:<6} | {org:<25} | {country:<15} | {service}"
                if hostname:
                    yield f"    Hostname: {hostname}"
                if vuln_str:
                    yield vuln_str

        except Exception as e:
            yield f"[!] Fehler: {e}"

    async def my_ip_info(self) -> AsyncGenerator[str, None]:
        """Was sieht Shodan von der eigenen externen IP?"""
        yield "[*] Ermittle externe IP..."

        # Externe IP holen
        external_ip = ""
        async for line in runner.run(["curl", "-s", "--max-time", "5", "https://api.ipify.org"]):
            external_ip = line.strip()

        if not external_ip:
            yield "[!] Externe IP konnte nicht ermittelt werden"
            return

        yield f"[+] Externe IP: {external_ip}"
        yield "[*] Shodan-Lookup der eigenen IP..."
        yield "─" * 60
        async for line in self.lookup_ip(external_ip):
            yield line

    async def _curl_lookup(self, ip: str) -> AsyncGenerator[str, None]:
        """Fallback: nutzt ipinfo.io wenn kein Shodan-Key vorhanden."""
        yield f"[*] Fallback: ipinfo.io für {ip}"
        async for line in runner.run([
            "curl", "-s", "--max-time", "8", f"https://ipinfo.io/{ip}/json"
        ]):
            try:
                data = json.loads(line)
                yield f"  IP:       {data.get('ip', '?')}"
                yield f"  Hostname: {data.get('hostname', '?')}"
                yield f"  Org:      {data.get('org', '?')}"
                yield f"  Stadt:    {data.get('city', '?')}, {data.get('country', '?')}"
                yield f"  Region:   {data.get('region', '?')}"
                if data.get("loc"):
                    yield f"  GPS:      {data['loc']}"
            except Exception:
                if line.strip():
                    yield f"  {line}"

    async def _web_search(self, query: str, limit: int = 10) -> AsyncGenerator[str, None]:
        """
        Zeigt Beispiel-Queries ohne API.
        Echter Web-Scraper würde Shodan ToS verletzen → nur Hilfestellung.
        """
        yield "[*] Shodan Query-Beispiele (ohne API-Key):"
        yield ""

        examples = {
            "Offene Webcams":      "webcamXP country:DE",
            "Ungesichertes MySQL": "port:3306 MySQL country:DE",
            "Default Credentials": f"title:\"Router Login\" country:DE",
            "RDP offen":           "port:3389 os:windows country:DE",
            "Elasticsearch offen": "port:9200 elastic",
            "Jenkins offen":       "title:\"Dashboard [Jenkins]\"",
            "FTP anonym":          "port:21 230 Anonymous",
            "VNC kein Passwort":   "port:5900 VNC Authentication disabled",
            "Telnet offen":        "port:23 telnet",
            "SCADA/ICS":           "port:102 SCADA Siemens",
        }

        yield f"  Dein Query:  shodan search '{query}'"
        yield ""
        yield "  Weitere nützliche Queries:"
        for name, q in examples.items():
            yield f"  → {name:<25}  {q}"

        yield ""
        yield "[*] Mit API-Key: alle Queries liefern echte IPs + Ports + Banners"
        yield "[*] API-Key: https://account.shodan.io/ (kostenlos, 100 Queries/Tag)"


# ── Spezialisierte Suchen ─────────────────────────────────────────────────────

PRESET_SEARCHES = {
    "Offene Webcams (DE)":      "webcamXP country:DE",
    "Ungesicherte DBs (DE)":    "port:27017 MongoDB country:DE",
    "Default-Login Router":     "title:\"router\" http.title:\"login\" country:DE",
    "Offenes RDP":              "port:3389 country:DE",
    "Offenes SMB":              "port:445 country:DE",
    "Jenkins CI offen":         "title:\"Dashboard [Jenkins]\"",
    "Elastic Search ungesich.": "port:9200 elasticsearch",
    "VNC ohne Passwort":        "port:5900 authentication disabled",
    "FRITZ!Box exposed":        "http.title:\"FRITZ!Box\" country:DE",
    "Telnet offen":             "port:23 telnet country:DE",
    "Kubernetes API":           "port:6443 kubernetes",
    "Apache Solr offen":        "port:8983 solr",
    "Citrix Gateway":           "title:\"Citrix Gateway\"",
    "ICS SCADA Siemens":        "port:102 Siemens",
    "Kamera Hikvision":         "product:\"Hikvision IP Camera\" country:DE",
}
