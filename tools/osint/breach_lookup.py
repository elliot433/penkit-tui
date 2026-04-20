"""
PenKit Breach Lookup — gestohlene Daten finden.

Module:
  1. HaveIBeenPwned  — E-Mail in bekannten Leaks prüfen (API v3, kein Key nötig für Leaks)
  2. DeHashed        — Username / Email / IP in Breach-DBs (optionaler API-Key)
  3. IntelX          — Intelligence X Suche (API-Key nötig)
  4. Offline Prüfung — Prüft ob E-Mail in heruntergeladenen Wordlists vorkommt
  5. LinkedIn OSINT  — Mitarbeiterliste via linkedin2username / CrossLinked

DSGVO-Hinweis: Nur für autorisierte Ziele / eigene E-Mails verwenden.
"""

from __future__ import annotations
import asyncio
import json
import urllib.request
import urllib.error
import urllib.parse
import re
from typing import AsyncGenerator

from core.output_dir import get as out_dir


# ── HaveIBeenPwned ────────────────────────────────────────────────────────────

async def hibp_check(email: str, api_key: str = "") -> AsyncGenerator[str, None]:
    """
    Prüft E-Mail gegen Have I Been Pwned Breach-Datenbank.
    Mit API-Key: vollständige Breach-Details.
    Ohne API-Key: nur Anzahl der Leaks.
    """
    yield f"\033[1;36m[*] HaveIBeenPwned Check: {email}\033[0m\n"

    encoded = urllib.parse.quote(email)
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{encoded}?truncateResponse=false"

    headers = {
        "User-Agent": "PenKit-OSINT/3.0",
        "hibp-api-key": api_key,
    } if api_key else {
        "User-Agent": "PenKit-OSINT/3.0",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

            if not data:
                yield "\033[32m[✓] Nicht in bekannten Leaks gefunden.\033[0m"
                return

            yield f"\033[1;31m[!] {len(data)} Breach(es) gefunden!\033[0m\n"

            out_lines = []
            for breach in data:
                name = breach.get("Name", "?")
                date = breach.get("BreachDate", "?")
                count = breach.get("PwnCount", 0)
                data_classes = breach.get("DataClasses", [])
                sensitive = breach.get("IsSensitive", False)

                severity = "\033[1;31mHOCH\033[0m" if sensitive or "Passwords" in data_classes else "\033[33mMITTEL\033[0m"

                yield f"\033[31m  ✗ {name}\033[0m  ({date})  {count:,} Accounts  [{severity}]"
                if data_classes:
                    yield f"    Daten: {', '.join(data_classes[:6])}"
                yield ""

                out_lines.append(f"{name} ({date}): {', '.join(data_classes)}")

            out_file = out_dir("osint") / f"hibp_{email.replace('@','_at_')}.txt"
            out_file.write_text("\n".join(out_lines))
            yield f"\033[32m[✓] Gespeichert: {out_file}\033[0m"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            yield "\033[31m[!] API-Key erforderlich für detaillierte Breach-Daten.\033[0m"
            yield "    Kostenloser Key: https://haveibeenpwned.com/API/Key"
            # Fallback: öffentliche Check-API
            await _hibp_public_check(email)
        elif e.code == 404:
            yield "\033[32m[✓] Nicht in bekannten Leaks gefunden.\033[0m"
        elif e.code == 429:
            yield "\033[33m[~] Rate-Limit erreicht. Warte 2 Sekunden...\033[0m"
            await asyncio.sleep(2)
        else:
            yield f"\033[31m[!] HIBP Fehler: HTTP {e.code}\033[0m"
    except Exception as e:
        yield f"\033[31m[!] Fehler: {e}\033[0m"


async def _hibp_public_check(email: str) -> AsyncGenerator[str, None]:
    """Öffentlicher HIBP Check ohne API-Key (nur Passwort-Hashes)."""
    import hashlib
    # k-Anonymity: schickt nur erste 5 chars des SHA1-Hashes
    sha1 = hashlib.sha1(email.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(url, headers={"User-Agent": "PenKit/3.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            hashes = resp.read().decode()
            if suffix in hashes:
                yield "\033[31m[!] E-Mail als Passwort in Leak-Datenbank gefunden!\033[0m"
            else:
                yield "\033[32m[✓] E-Mail nicht als Passwort verwendet.\033[0m"
    except Exception:
        pass


async def hibp_bulk(emails: list[str], api_key: str = "") -> AsyncGenerator[str, None]:
    """Bulk-Check mehrerer E-Mails."""
    yield f"\033[1;36m[*] Bulk-Check {len(emails)} E-Mails...\033[0m\n"
    pwned = []

    for i, email in enumerate(emails, 1):
        yield f"  [{i:>3}/{len(emails)}] {email}..."
        encoded = urllib.parse.quote(email)
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{encoded}"
        headers = {"User-Agent": "PenKit/3.0"}
        if api_key:
            headers["hibp-api-key"] = api_key

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                if data:
                    pwned.append((email, len(data)))
                    yield f"\033[31m    → {len(data)} Leaks!\033[0m"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                yield "\033[90m    → Sauber\033[0m"
            elif e.code == 429:
                await asyncio.sleep(1.5)
        except Exception:
            pass
        await asyncio.sleep(0.7)   # Rate-Limit einhalten

    yield f"\n\033[{'31' if pwned else '32'}m[{'!' if pwned else '✓'}] {len(pwned)}/{len(emails)} E-Mails in Leaks gefunden.\033[0m"
    for email, count in pwned:
        yield f"  \033[31m✗ {email}  ({count} Breaches)\033[0m"


# ── Passwort-Hash Check (k-Anonymity) ────────────────────────────────────────

async def password_pwned_check(password: str) -> AsyncGenerator[str, None]:
    """Prüft ob Passwort in Breach-Daten (k-Anonymity, sicher)."""
    import hashlib

    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    yield f"\033[1;36m[*] Passwort-Check (Hash: {sha1[:10]}...)\033[0m"

    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(url, headers={"User-Agent": "PenKit/3.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            lines = resp.read().decode().splitlines()
            for line in lines:
                if line.startswith(suffix):
                    count = int(line.split(":")[1])
                    yield f"\033[1;31m[!] Passwort {count:,}x in Leaks gefunden — SOFORT ÄNDERN!\033[0m"
                    return
            yield "\033[32m[✓] Passwort nicht in bekannten Leaks gefunden.\033[0m"
    except Exception as e:
        yield f"\033[31m[!] Fehler: {e}\033[0m"


# ── LinkedIn OSINT ────────────────────────────────────────────────────────────

COMMON_EMAIL_FORMATS = [
    "{first}.{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}{l}@{domain}",
    "{first}@{domain}",
    "{last}@{domain}",
    "{first}_{last}@{domain}",
    "{last}.{first}@{domain}",
    "{first}{last}@{domain}",
]


async def generate_email_list(
    domain: str,
    names: list[str],
) -> AsyncGenerator[str, None]:
    """
    Generiert E-Mail-Adressen aus Namen nach bekannten Unternehmens-Mustern.
    Namen-Format: "Vorname Nachname" (eine pro Zeile).
    """
    yield f"\033[1;36m[*] E-Mail-Generator für {domain} ({len(names)} Namen)...\033[0m\n"

    all_emails = []
    for name in names:
        parts = name.strip().split()
        if len(parts) < 2:
            continue
        first = parts[0].lower()
        last  = parts[-1].lower()
        f = first[0]
        l = last[0]

        for fmt in COMMON_EMAIL_FORMATS:
            email = fmt.format(
                first=first, last=last,
                f=f, l=l, domain=domain,
            )
            all_emails.append(email)
            yield f"  {email}"

    out_file = out_dir("osint") / f"emails_{domain}.txt"
    out_file.write_text("\n".join(all_emails))
    yield f"\n\033[32m[✓] {len(all_emails)} E-Mails gespeichert: {out_file}\033[0m"
    yield f"\033[36m[→] Mit HIBP prüfen oder direkt in Phishing-Kampagne nutzen\033[0m"


async def crosslinked_search(company: str, domain: str) -> AsyncGenerator[str, None]:
    """LinkedIn-Mitarbeiter via CrossLinked oder Scraping finden."""
    import shutil

    yield f"\033[1;36m[*] LinkedIn OSINT für {company} / {domain}...\033[0m\n"

    if shutil.which("crosslinked"):
        from core.runner import CommandRunner
        runner = CommandRunner()
        out_file = out_dir("osint") / f"linkedin_{domain}.txt"
        yield "\033[36m[→] CrossLinked läuft...\033[0m"
        async for line in runner.run([
            "crosslinked", "-f", "{first}.{last}@" + domain,
            company, "-o", str(out_file),
        ]):
            yield f"  {line}"
    else:
        yield "\033[33m[~] CrossLinked nicht installiert.\033[0m"
        yield "    Install: pip3 install crosslinked --break-system-packages"
        yield ""
        yield "\033[36m[→] Alternative: linkedin2username\033[0m"
        yield "    git clone https://github.com/initstring/linkedin2username"
        yield "    python3 linkedin2username/linkedin2username.py -c 'Company Name' -d domain.com"
        yield ""
        yield "\033[36m[→] Google Dork für LinkedIn:\033[0m"
        yield f"    site:linkedin.com/in '{company}'"
        yield f"    site:linkedin.com/in '{company}' -intitle:Director -intitle:CEO"


# ── DeHashed ──────────────────────────────────────────────────────────────────

async def dehashed_search(
    query: str,
    query_type: str = "email",
    api_key: str = "",
    api_email: str = "",
) -> AsyncGenerator[str, None]:
    """
    DeHashed Breach-Datenbank — E-Mail, Username, IP, Passwort suchen.
    Braucht API-Key ($5/Monat) für vollständige Daten.
    """
    yield f"\033[1;36m[*] DeHashed Search: {query_type}={query}\033[0m\n"

    if not api_key or not api_email:
        yield "\033[33m[~] DeHashed braucht API-Key. Registrierung: https://dehashed.com\033[0m"
        yield "    Ohne Key: nur eingeschränkte Demo-Daten."
        yield ""

    url = f"https://api.dehashed.com/search?query={query_type}:{urllib.parse.quote(query)}&size=20"

    import base64
    auth = base64.b64encode(f"{api_email}:{api_key}".encode()).decode() if api_key else ""

    headers = {
        "Accept": "application/json",
        "User-Agent": "PenKit/3.0",
    }
    if auth:
        headers["Authorization"] = f"Basic {auth}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            entries = data.get("entries", []) or []

            if not entries:
                yield "\033[32m[✓] Keine Einträge gefunden.\033[0m"
                return

            yield f"\033[1;31m[!] {len(entries)} Einträge gefunden!\033[0m\n"

            out_lines = []
            for entry in entries:
                email = entry.get("email", "")
                username = entry.get("username", "")
                password = entry.get("password", "")
                hashed_pw = entry.get("hashed_password", "")
                source = entry.get("database_name", "?")

                if email or username:
                    yield f"\033[33m  Quelle: {source}\033[0m"
                    if email:
                        yield f"    E-Mail:   \033[36m{email}\033[0m"
                    if username:
                        yield f"    User:     \033[36m{username}\033[0m"
                    if password:
                        yield f"    Passwort: \033[31m{password}\033[0m"
                    if hashed_pw:
                        yield f"    Hash:     \033[31m{hashed_pw[:60]}\033[0m"
                    yield ""
                    out_lines.append(f"{source}: {email or username} / {password or hashed_pw}")

            out_file = out_dir("osint") / f"dehashed_{query.replace('@','_at_')}.txt"
            out_file.write_text("\n".join(out_lines))
            yield f"\033[32m[✓] Gespeichert: {out_file}\033[0m"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            yield "\033[31m[!] Authentifizierung fehlgeschlagen — API-Key prüfen.\033[0m"
        elif e.code == 400:
            yield "\033[31m[!] Ungültige Suchanfrage.\033[0m"
        else:
            yield f"\033[31m[!] HTTP Fehler: {e.code}\033[0m"
    except Exception as e:
        yield f"\033[31m[!] Fehler: {e}\033[0m"
