"""
PenKit AI Assistant — natürlichsprachliche Tool-Empfehlungen.

Kein LLM, kein API-Key, kein Internet nötig.
Funktioniert via gewichteter Keyword-Analyse auf Deutsch + Englisch.

Beispiel-Fragen:
  "Ich will eine Webseite zum Absturz bringen"
  "Wie finde ich den Standort einer Person?"
  "Ich will WLAN-Passwort knacken"
  "Jemand soll auf einen Link klicken und ich bekomme Zugriff"
  "Wie belausche ich den Netzwerkverkehr?"
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class ToolRecommendation:
    tool_name: str
    menu_path: str          # z.B. "Netzwerk → DDoS"
    danger_level: str
    short_desc: str
    steps: list[str]
    tips: list[str]


# ── Wissensbasis ──────────────────────────────────────────────────────────────
# Format: (keywords_de, keywords_en, recommendation)

_KB: list[tuple[list[str], list[str], ToolRecommendation]] = [

    # DDoS / Server runternehmen
    (
        ["seite runternehmen", "server runternehmen", "webseite lahmlegen",
         "absturz bringen", "offline nehmen", "überlasten", "überfluten",
         "ddos", "dos", "angriff server", "webseite angreifen"],
        ["take down", "ddos", "flood", "overload", "crash server", "dos attack"],
        ToolRecommendation(
            tool_name="DDoS / Stress-Test",
            menu_path="Netzwerk → DDoS (Option 6)",
            danger_level="⛔ SCHWARZ",
            short_desc="Überlastet einen Server mit massiven Anfragen bis er nicht mehr antwortet.",
            steps=[
                "Hauptmenü → 2 (Netzwerk) → 6 (DDoS)",
                "Methode wählen:",
                "  Slowloris → am besten gegen Apache-Server (hält Verbindungen offen)",
                "  HTTP Flood → maximale Requests/sec via asyncio",
                "  hping3    → SYN-Flood auf Kernel-Ebene, sehr schnell",
                "Ziel-IP + Port + Dauer eingeben",
                "Bestätigung eintippen",
            ],
            tips=[
                "Slowloris braucht wenig Bandbreite aber braucht ~200 offene Verbindungen",
                "HTTP Flood ist am effektivsten gegen ungeschützte Web-Apps",
                "hping3 --rand-source fälscht Quell-IPs → schwerer zu blockieren",
                "Cloudflare/CDN schützen den Origin-Server → vorher echte IP finden",
            ],
        )
    ),

    # WLAN / WiFi knacken
    (
        ["wlan knacken", "wlan passwort", "wifi passwort", "wifi knacken",
         "wpa2 knacken", "handshake", "wlan hacken", "netzwerk einbrechen",
         "passwort netzwerk", "router passwort"],
        ["crack wifi", "wpa2", "wifi password", "handshake capture", "wlan hack"],
        ToolRecommendation(
            tool_name="WiFi Attacks",
            menu_path="WiFi (Option 1)",
            danger_level="🟠 ORANGE",
            short_desc="Knackt WPA2/3-Passwörter via Handshake-Capture oder PMKID-Attack.",
            steps=[
                "Hauptmenü → 1 (WiFi)",
                "Option 1: WiFi-Scanner → Ziel-Netzwerk + BSSID notieren",
                "Option 3: PMKID Attack → kein Client nötig, schnellste Methode",
                "  ODER Option 2: Handshake Capture → Client muss im Netz sein",
                "Danach: Passwörter (Option 4) → Hashcat → Handshake-Datei cracken",
                "Wordlist: rockyou.txt (auf Kali vorinstalliert: /usr/share/wordlists/)",
            ],
            tips=[
                "PMKID braucht keinen verbundenen Client — deutlich schneller",
                "GPU-Cracking mit Hashcat ist 100x schneller als CPU",
                "Schwache Passwörter (< 8 Zeichen, nur Zahlen) in Sekunden geknackt",
                "WPA3 ist deutlich resistenter — Evil Twin als Alternative",
            ],
        )
    ),

    # Standort / GPS / Location
    (
        ["standort herausfinden", "person orten", "gps verfolgen", "location",
         "wo ist jemand", "ip orten", "adresse herausfinden", "handy orten",
         "live standort"],
        ["find location", "track person", "gps", "locate ip", "geolocation"],
        ToolRecommendation(
            tool_name="OSINT Recon + C2 Geolocation",
            menu_path="OSINT (Option 6) ODER C2 Agent → !sysinfo",
            danger_level="🟡 GELB / ⛔ SCHWARZ",
            short_desc="IP-Geolocation via OSINT oder exakte GPS-Koordinaten via C2-Agent.",
            steps=[
                "Methode A — IP-Geolocation (nur ungefähr, Stadt-Level):",
                "  OSINT (Option 6) → Ziel-Domain eingeben → IP wird geolokalisiert",
                "",
                "Methode B — Exakter Standort via C2 (braucht Zugriff auf Gerät):",
                "  C2 → Telegram Agent generieren → auf Ziel-PC deployen",
                "  Dann im Telegram: !sysinfo → gibt IP + Stadt + Land",
                "",
                "Methode C — Phishing-Link mit Standort-Capture:",
                "  Phishing (Option 7) → Server starten → Link mit ?page=google schicken",
                "  Beim Öffnen: IP + User-Agent → Geolocation via ipinfo.io",
            ],
            tips=[
                "IP-Geolocation zeigt nur Stadt, nicht exakte Adresse",
                "Mobilgeräte mit GPS liefern via Browser-API genaue Koordinaten",
                "BeEF (Web → Option 6) kann GPS via Browser-Permission abfragen",
                "Exakte Hausnummer ist nur via physischem Zugriff / ISP möglich",
            ],
        )
    ),

    # Phishing / Zugangsdaten stehlen
    (
        ["phishing", "login seite", "fake seite", "passwort stehlen",
         "credentials", "zugangsdaten", "link schicken", "jemand soll klicken",
         "email schicken", "google fake", "instagram fake"],
        ["phishing", "fake login", "steal password", "credentials", "spear phishing"],
        ToolRecommendation(
            tool_name="Phishing Suite",
            menu_path="Phishing (Option 7)",
            danger_level="⛔ SCHWARZ",
            short_desc="Fake-Login-Pages (Google/MS/Instagram/Apple/Bank) + Email-Kampagnen.",
            steps=[
                "Hauptmenü → 7 (Phishing)",
                "Option 1: Server starten → Seite wählen (z.B. google)",
                "Phishing-Link: http://<deine-Kali-IP>:8080/?page=google",
                "Link an Ziel schicken (Email, WhatsApp, QR-Code)",
                "Credentials erscheinen sofort im Terminal wenn jemand eingibt",
                "",
                "Für Email-Kampagnen:",
                "  Option 2 → SMTP-Daten + Zielliste + Template wählen",
                "  Template 'google_security' sieht am überzeugendsten aus",
            ],
            tips=[
                "URL-Shortener (bit.ly) macht den Link glaubwürdiger",
                "Eigene Domain + HTTPS = kaum erkennbar als Phishing",
                "Template 'it_department' funktioniert gut in Firmen-Umgebungen",
                "GoPhish (Option 3) für professionelle Multi-Ziel-Kampagnen",
            ],
        )
    ),

    # Netzwerk belauschen / MITM
    (
        ["belauschen", "abhören", "netzwerk mitlesen", "traffic", "mitm",
         "man in the middle", "passwörter sniffing", "https entschlüsseln",
         "netzwerk überwachen", "arp spoofing"],
        ["sniff", "intercept", "mitm", "man in the middle", "ssl strip", "arp spoof"],
        ToolRecommendation(
            tool_name="MITM",
            menu_path="MITM (Option 5)",
            danger_level="🔴 ROT",
            short_desc="ARP-Spoofing leitet Netzverkehr durch Kali, SSL-Strip entschlüsselt HTTPS.",
            steps=[
                "Hauptmenü → 5 (MITM)",
                "Option 1: bettercap ARP-Spoof → Ziel-IP + Gateway eingeben",
                "  → Gesamter Traffic fließt durch Kali",
                "Option 2: Responder → fängt NTLMv2-Hashes in Windows-Netzen",
                "  → Öffnet einen separaten Terminal mit Live-Output",
                "Captured Hashes → Passwords-Modul → Hashcat cracken",
            ],
            tips=[
                "Beide Geräte (Kali + Ziel) müssen im selben Netz sein",
                "HTTPS zeigt Zertifikat-Warnung im Browser des Opfers",
                "Responder ist am effektivsten in Unternehmensnetzen",
                "bettercap caplet 'hstshijack' umgeht HSTS teilweise",
            ],
        )
    ),

    # Zugriff auf Windows PC / RAT / Fernzugriff
    (
        ["fernzugriff", "zugriff auf pc", "windows hacken", "rat", "backdoor",
         "reverse shell", "meterpreter", "pc übernehmen", "zugang verschaffen",
         "payload", "trojaner"],
        ["remote access", "rat", "backdoor", "reverse shell", "windows hack", "payload"],
        ToolRecommendation(
            tool_name="C2 / RAT Payloads",
            menu_path="C2 (Option 9)",
            danger_level="⛔ SCHWARZ",
            short_desc="Erstellt Windows-Payloads die Fernzugriff via Telegram geben.",
            steps=[
                "Hauptmenü → 9 (C2)",
                "Schritt 1: Option 8 → Telegram Bot einrichten (Token + Chat-ID)",
                "Schritt 2: Option 7 → Telegram C2 Agent generieren",
                "  → Gibt .ps1 Datei aus",
                "Schritt 3: Payload auf Ziel bringen:",
                "  Option 1 (Full Package) → erstellt HTA/BAT/Macro + ANLEITUNG.txt",
                "Schritt 4: Payload ausführen → Agent erscheint in Telegram",
                "  → !help für alle Befehle",
            ],
            tips=[
                "Option 7 (Telegram Agent) ist am einfachsten zu steuern",
                "!persist macht den Agent dauerhaft (bleibt nach Neustart aktiv)",
                "Full Package (Option 1) + Disguise (Option 6) = kaum erkennbar",
                "AMSI Bypass (Option 4) vor dem Ausführen = Defender blind",
            ],
        )
    ),

    # Browser hacken / XSS
    (
        ["browser hacken", "javascript", "xss", "beef", "webseite angreifen",
         "browser kontrolle", "cookies stehlen", "session hijacking",
         "webcam browser", "tastatur browser"],
        ["xss", "beef", "browser exploit", "javascript inject", "cookie steal"],
        ToolRecommendation(
            tool_name="BeEF Browser Exploitation",
            menu_path="Web (Option 3) → BeEF (Option 6)",
            danger_level="⛔ SCHWARZ",
            short_desc="Hookt Browser via JS, ermöglicht Keylogger/Screenshot/Webcam/Cookies.",
            steps=[
                "Hauptmenü → 3 (Web) → 6 (BeEF)",
                "Option 1: BeEF starten",
                "Option 2: Hook-Payload generieren → JS-Zeile kopieren",
                "Hook einschleusen via:",
                "  A) XSS-Lücke auf Ziel-Webseite",
                "  B) MITM → bettercap injiziert JS automatisch",
                "  C) Phishing-Seite → Hook-JS in HTML einbauen",
                "Option 3: Gehookte Browser anzeigen",
                "Option 4: Befehl wählen (Keylogger, Screenshot, Webcam...)",
            ],
            tips=[
                "BeEF + MITM = alle Browser im Netz hookbar ohne XSS",
                "Webcam-Zugriff braucht Browser-Permission (erscheint als Popup)",
                "Keylogger läuft unsichtbar solange Tab offen ist",
                "HTTPS-Seiten: Browser blockiert unsicheres JS → MITM mit gültigem Cert",
            ],
        )
    ),

    # Passwort knacken
    (
        ["passwort knacken", "hash knacken", "passwort cracken", "hashcat",
         "john the ripper", "wordlist", "brute force", "passwort hash",
         "md5 knacken", "sha256 knacken"],
        ["crack password", "hashcat", "john", "brute force", "hash crack", "wordlist"],
        ToolRecommendation(
            tool_name="Passwords & Hashes",
            menu_path="Passwörter (Option 4)",
            danger_level="🟡 GELB",
            short_desc="Auto-Hash-Erkennung, Hashcat GPU-Cracking, John, Hydra Brute-Force.",
            steps=[
                "Hauptmenü → 4 (Passwörter)",
                "Option 1: Hash-Typ automatisch erkennen → Hash einfügen",
                "Option 2: Hashcat → Hash-Datei + Wordlist",
                "  Beste Wordlist: /usr/share/wordlists/rockyou.txt",
                "Option 3: John the Ripper → alternativ, gut für NTLM/bcrypt",
                "Option 4: Hydra → Online-Brute-Force (SSH/FTP/HTTP/RDP...)",
            ],
            tips=[
                "GPU-Cracking (Hashcat) ist 100-10000x schneller als CPU",
                "MD5/NTLM: Milliarden/s mit guter GPU",
                "bcrypt/scrypt: viel langsamer, nur schwache Passwörter knackbar",
                "Erst Wordlist, dann Regeln (rockyou + best64.rule), dann Brute-Force",
                "Online (Hydra): 3-5 Versuche/s max um Lockout zu vermeiden",
            ],
        )
    ),

    # OSINT / Person recherchieren
    (
        ["person recherchieren", "info über person", "person finden", "osint",
         "email suchen", "social media suchen", "profil finden",
         "username suchen", "sherlock", "hintergrund check"],
        ["osint", "find person", "social media", "username search", "recon"],
        ToolRecommendation(
            tool_name="OSINT Recon",
            menu_path="OSINT (Option 6)",
            danger_level="🟡 GELB",
            short_desc="Emails, Subdomains, Usernames auf 300+ Plattformen, automatischer Report.",
            steps=[
                "Hauptmenü → 6 (OSINT)",
                "Für Domain-Recon:",
                "  Option 1 oder 2 → Domain eingeben (z.B. example.com)",
                "  → Findet Emails, Subdomains, IPs automatisch",
                "Für Person/Username:",
                "  Option 3 → Username eingeben",
                "  → Sherlock prüft 300+ Plattformen (Instagram, TikTok, GitHub...)",
                "Option 4: Google Dorks → spezielle Suchanfragen für versteckte Infos",
                "Option 5: Auto-Report → alles in einer Markdown-Datei",
            ],
            tips=[
                "Kombiniere Domain-Recon + Username-Suche für vollständiges Bild",
                "Google Dorks: 'site:domain.com filetype:pdf' findet versteckte Docs",
                "HaveIBeenPwned: prüft ob Email in Datenleck",
                "GitHub Dorks: findet oft API-Keys + Passwörter in Repos",
            ],
        )
    ),

    # IoT / Router angreifen
    (
        ["router hacken", "iot hacken", "kamera hacken", "standard passwort",
         "default passwort", "heimnetz angreifen", "smart home hacken",
         "nas hacken", "ip kamera"],
        ["router hack", "iot attack", "default credentials", "ip camera", "nas exploit"],
        ToolRecommendation(
            tool_name="IoT Scanner",
            menu_path="Netzwerk (Option 2) → IoT Scanner (Option 5)",
            danger_level="🔴 ROT",
            short_desc="Findet IoT-Geräte im Netz, testet 65+ Default-Credential-Kombinationen.",
            steps=[
                "Hauptmenü → 2 (Netzwerk) → 5 (IoT Scanner)",
                "Ziel eingeben: 192.168.1.0/24 (komplettes Heimnetz)",
                "Scanner findet automatisch:",
                "  → Offene Ports (23/80/8080/554/...)",
                "  → Hersteller-Erkennung (TP-Link, Hikvision, FRITZ!Box...)",
                "  → Default-Creds testen (admin/admin, root/root, ...)",
                "Ergebnis: Liste aller Geräte mit gefundenen Login-Daten",
            ],
            tips=[
                "Standard-Passwörter ändern ist die häufigste vergessene Sicherheit",
                "Port 23 (Telnet) = fast immer Default-Creds, sehr unsicher",
                "IP-Kameras: Port 554 (RTSP) gibt oft Live-Stream ohne Login",
                "Nach Login: Admin-Einstellungen ändern, Firmware prüfen",
            ],
        )
    ),
]


def _normalize(text: str) -> str:
    return text.lower().strip()


def _score(question: str, keywords_de: list[str], keywords_en: list[str]) -> int:
    q = _normalize(question)
    score = 0
    all_kw = keywords_de + keywords_en
    for kw in all_kw:
        kw_norm = _normalize(kw)
        if kw_norm in q:
            # Längere Keywords = mehr Punkte (spezifischer)
            score += len(kw_norm.split())
    return score


def ask(question: str) -> list[ToolRecommendation]:
    """
    Gibt sortierte Liste von Tool-Empfehlungen zurück.
    Beste Übereinstimmung zuerst.
    """
    scored: list[tuple[int, ToolRecommendation]] = []
    for kw_de, kw_en, rec in _KB:
        s = _score(question, kw_de, kw_en)
        if s > 0:
            scored.append((s, rec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:3]]  # Top 3
