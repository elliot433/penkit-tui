"""
PenKit Subdomain Takeover Scanner.

Prüft ob Subdomains auf nicht mehr existierende externe Dienste zeigen:
  GitHub Pages, Netlify, Heroku, Vercel, AWS S3, Fastly, Shopify, Azure,
  Zendesk, Tumblr, WordPress.com, Ghost, Surge.sh, Readme.io, u.v.m.

Ablauf:
  1. Subdomain-Liste von subfinder / amass / crt.sh holen
  2. DNS-CNAME-Records auflösen
  3. CNAME gegen Fingerprint-Datenbank prüfen
  4. HTTP-Response auf Übernahme-Indikatoren prüfen
  5. Übernahmbare Subdomains markieren + Anleitung anzeigen

Braucht: dig/host, optional subfinder/amass
"""

from __future__ import annotations
import asyncio
import json
import shutil
import urllib.request
import urllib.error
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


# ── Fingerprint-Datenbank ─────────────────────────────────────────────────────
# Format: (CNAME-Pattern, HTTP-Response-String, Service, Anleitung)

FINGERPRINTS: list[dict] = [
    {
        "service":    "GitHub Pages",
        "cname":      ["github.io", "github.com"],
        "response":   ["There isn't a GitHub Pages site here", "For root URLs"],
        "takeover":   "GitHub Pages → Repo 'username.github.io' erstellen + CNAME einstellen",
        "difficulty": "Einfach",
    },
    {
        "service":    "Heroku",
        "cname":      ["herokuapp.com", "herokudns.com"],
        "response":   ["No such app", "herokucdn.com/error-pages/no-such-app"],
        "takeover":   "Heroku App mit gleichem Namen erstellen: heroku create <app-name>",
        "difficulty": "Einfach",
    },
    {
        "service":    "Netlify",
        "cname":      ["netlify.app", "netlify.com"],
        "response":   ["Not Found", "netlify"],
        "takeover":   "Netlify-Account erstellen → Custom Domain mit gleichem CNAME verbinden",
        "difficulty": "Einfach",
    },
    {
        "service":    "Vercel",
        "cname":      ["vercel.app", "now.sh", "zeit.co"],
        "response":   ["The deployment could not be found", "vercel.app"],
        "takeover":   "Vercel-Account → neues Projekt → Domain hinzufügen",
        "difficulty": "Einfach",
    },
    {
        "service":    "AWS S3",
        "cname":      ["s3.amazonaws.com", "s3-website"],
        "response":   ["NoSuchBucket", "The specified bucket does not exist"],
        "takeover":   "AWS Console → S3 Bucket mit gleichem Namen erstellen → Static Website aktivieren",
        "difficulty": "Mittel",
    },
    {
        "service":    "Azure",
        "cname":      ["azurewebsites.net", "cloudapp.net", "trafficmanager.net", "blob.core.windows.net"],
        "response":   ["404 Web Site not found", "Microsoft Azure"],
        "takeover":   "Azure Portal → neues Web App Deployment mit gleichem Namen",
        "difficulty": "Mittel",
    },
    {
        "service":    "Shopify",
        "cname":      ["myshopify.com", "shops.myshopify.com"],
        "response":   ["Sorry, this shop is currently unavailable", "only available to people who have been invited"],
        "takeover":   "Shopify-Store mit gleichem myshopify.com-Namen registrieren",
        "difficulty": "Einfach",
    },
    {
        "service":    "Fastly",
        "cname":      ["fastly.net"],
        "response":   ["Fastly error: unknown domain", "Please check that this domain has been added"],
        "takeover":   "Fastly-Account → neue Service-Konfiguration mit dieser Domain",
        "difficulty": "Schwer",
    },
    {
        "service":    "Zendesk",
        "cname":      ["zendesk.com"],
        "response":   ["Help Center Closed", "Bitte versuche es erneut"],
        "takeover":   "Zendesk-Account erstellen + Custom Domain setzen",
        "difficulty": "Mittel",
    },
    {
        "service":    "Tumblr",
        "cname":      ["domains.tumblr.com"],
        "response":   ["There's nothing here.", "tumblr.com"],
        "takeover":   "Tumblr-Account → Custom Domain mit gleichem Namen",
        "difficulty": "Einfach",
    },
    {
        "service":    "Ghost (Pro)",
        "cname":      ["ghost.io"],
        "response":   ["Domain error"],
        "takeover":   "Ghost Pro → neue Publikation mit dieser Domain verbinden",
        "difficulty": "Mittel",
    },
    {
        "service":    "Surge.sh",
        "cname":      ["surge.sh"],
        "response":   ["project not found", "surge.sh"],
        "takeover":   "surge.sh Konto → surge --domain <subdomain.domain.com>",
        "difficulty": "Einfach",
    },
    {
        "service":    "Readme.io",
        "cname":      ["readme.io", "readmessl.com"],
        "response":   ["Project doesnt exist", "readme.io"],
        "takeover":   "ReadMe-Account → Custom Domain im Project-Settings",
        "difficulty": "Einfach",
    },
    {
        "service":    "Unbounce",
        "cname":      ["unbouncepages.com"],
        "response":   ["The requested URL was not found"],
        "takeover":   "Unbounce-Account → Domain hinzufügen",
        "difficulty": "Mittel",
    },
    {
        "service":    "HubSpot",
        "cname":      ["hubspot.com", "hs-sites.com"],
        "response":   ["Domain not found", "does not exist in our system"],
        "takeover":   "HubSpot → Content → Domain & URLs → Domain verbinden",
        "difficulty": "Mittel",
    },
    {
        "service":    "WordPress.com",
        "cname":      ["wordpress.com"],
        "response":   ["Do you want to register"],
        "takeover":   "WordPress.com-Blog mit gleicher Domain + Custom Domain-Mapping",
        "difficulty": "Mittel",
    },
    {
        "service":    "Pantheon",
        "cname":      ["pantheonsite.io"],
        "response":   ["404 error unknown site"],
        "takeover":   "Pantheon-Account → neues Site + Domain hinzufügen",
        "difficulty": "Mittel",
    },
]


# ── DNS CNAME auflösen ────────────────────────────────────────────────────────

async def resolve_cname(subdomain: str) -> str | None:
    """Löst CNAME-Record eines Subdomains auf."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "dig", "+short", "CNAME", subdomain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        cname = stdout.decode().strip().rstrip(".")
        return cname if cname else None
    except Exception:
        return None


async def check_http_response(subdomain: str, timeout: int = 5) -> str:
    """Lädt HTTP-Antwort eines Subdomains."""
    try:
        req = urllib.request.Request(
            f"http://{subdomain}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(4096).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return str(e)
    except Exception:
        # HTTPS versuchen
        try:
            req = urllib.request.Request(
                f"https://{subdomain}",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return resp.read(4096).decode(errors="replace")
        except Exception:
            return ""


def check_fingerprint(cname: str, response: str) -> dict | None:
    """Prüft ob CNAME + Response auf übernahmbaren Dienst hindeutet."""
    cname_lower = cname.lower()
    resp_lower  = response.lower()

    for fp in FINGERPRINTS:
        # CNAME-Match
        cname_match = any(pattern in cname_lower for pattern in fp["cname"])
        # Response-Match (Beweis dass Dienst nicht belegt ist)
        resp_match = any(indicator.lower() in resp_lower for indicator in fp["response"])

        if cname_match and resp_match:
            return fp
        if cname_match and not response:
            # CNAME zeigt auf Service aber keine HTTP-Antwort = wahrscheinlich frei
            return {**fp, "confidence": "low", "takeover": fp["takeover"] + " (HTTP-Antwort leer — manuell prüfen)"}

    return None


# ── Subdomain-Sammler ─────────────────────────────────────────────────────────

async def get_subdomains(domain: str) -> list[str]:
    """Sammelt Subdomains via subfinder/amass/crt.sh."""
    subdomains = set()

    # Methode 1: subfinder
    if shutil.which("subfinder"):
        proc = await asyncio.create_subprocess_exec(
            "subfinder", "-d", domain, "-silent",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()
        for line in stdout.decode().splitlines():
            if line.strip():
                subdomains.add(line.strip())

    # Methode 2: amass
    if shutil.which("amass") and len(subdomains) < 10:
        proc = await asyncio.create_subprocess_exec(
            "amass", "enum", "-passive", "-d", domain,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()
        for line in stdout.decode().splitlines():
            if "." in line and domain in line:
                subdomains.add(line.strip())

    # Methode 3: crt.sh API (kein Tool nötig)
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent": "PenKit/3.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            for entry in data:
                name = entry.get("name_value", "")
                for sub in name.split("\n"):
                    sub = sub.strip().lstrip("*.")
                    if sub.endswith(domain) and sub != domain:
                        subdomains.add(sub)
    except Exception:
        pass

    return sorted(subdomains)


# ── Haupt-Scanner ─────────────────────────────────────────────────────────────

async def scan(
    domain: str,
    subdomain_file: str = "",
    max_concurrent: int = 20,
) -> AsyncGenerator[str, None]:
    """Vollständiger Subdomain-Takeover-Scan."""
    yield f"\033[1;36m[*] Subdomain Takeover Scanner: {domain}\033[0m\n"

    # Subdomains sammeln
    if subdomain_file:
        import os
        if os.path.exists(subdomain_file):
            with open(subdomain_file) as f:
                subdomains = [l.strip() for l in f if l.strip() and domain in l]
        else:
            yield f"\033[31m[!] Datei nicht gefunden: {subdomain_file}\033[0m"
            return
    else:
        yield "\033[36m[*] Sammle Subdomains (crt.sh + subfinder + amass)...\033[0m"
        subdomains = await get_subdomains(domain)
        yield f"  {len(subdomains)} Subdomains gefunden\n"

    if not subdomains:
        yield "\033[33m[~] Keine Subdomains gefunden.\033[0m"
        yield "    Install subfinder: apt install subfinder"
        return

    # Semaphore für parallele Checks
    sem = asyncio.Semaphore(max_concurrent)
    vulnerable: list[dict] = []
    checked = 0

    async def check_one(sub: str):
        nonlocal checked
        async with sem:
            cname = await resolve_cname(sub)
            if not cname:
                checked += 1
                return

            response = await check_http_response(sub)
            fp = check_fingerprint(cname, response)

            if fp:
                vulnerable.append({
                    "subdomain": sub,
                    "cname": cname,
                    "service": fp["service"],
                    "difficulty": fp.get("difficulty", "?"),
                    "takeover": fp["takeover"],
                })
            checked += 1

    yield f"\033[36m[*] Prüfe {len(subdomains)} Subdomains (parallel)...\033[0m\n"

    tasks = [asyncio.create_task(check_one(sub)) for sub in subdomains]

    # Fortschritt anzeigen
    last_report = 0
    while tasks:
        done, tasks_set = await asyncio.wait(list(tasks), timeout=2.0, return_when=asyncio.FIRST_COMPLETED)
        tasks = list(tasks_set)
        if checked - last_report >= 10:
            yield f"\033[90m  [{checked}/{len(subdomains)}] Geprüft...\033[0m"
            last_report = checked

    await asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True)

    # Report
    yield "\n" + "═" * 60
    if vulnerable:
        yield f"\033[1;31m[!] {len(vulnerable)} ÜBERNEHMBARE SUBDOMAINS GEFUNDEN!\033[0m\n"

        for item in vulnerable:
            diff_color = "\033[32m" if item["difficulty"] == "Einfach" else "\033[33m" if item["difficulty"] == "Mittel" else "\033[31m"
            yield f"\033[1;32m✓ {item['subdomain']}\033[0m"
            yield f"  Service:    \033[33m{item['service']}\033[0m  [{diff_color}{item['difficulty']}\033[0m]"
            yield f"  CNAME:      {item['cname']}"
            yield f"  Übernahme:  \033[36m{item['takeover']}\033[0m"
            yield ""

        out_file = out_dir("network") / f"subdomain_takeover_{domain}.json"
        out_file.write_text(json.dumps(vulnerable, indent=2))
        yield f"\033[32m[✓] Report: {out_file}\033[0m"
    else:
        yield f"\033[32m[✓] Keine übernahmbaren Subdomains gefunden ({checked} geprüft).\033[0m"

    yield "═" * 60
