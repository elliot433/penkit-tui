# PenKit TUI v3

```
  ██████╗ ███████╗███╗   ██╗██╗  ██╗██╗████████╗
  ██╔══██╗██╔════╝████╗  ██║██║ ██╔╝██║╚══██╔══╝
  ██████╔╝█████╗  ██╔██╗ ██║█████╔╝ ██║   ██║
  ██╔═══╝ ██╔══╝  ██║╚████║██╔═██╗ ██║   ██║
  ██║     ███████╗██║ ╚███║██║  ██╗██║   ██║
  ╚═╝     ╚══════╝╚═╝  ╚══╝╚═╝  ╚═╝╚═╝   ╚═╝
```

> **Authorized Pentesting Toolkit für Kali Linux**  
> Vollständiges Pentesting-Framework mit Terminal-UI und modernem Browser-Interface.  
> ⚠️ Nur für autorisierte Tests auf eigenen oder freigegebenen Systemen.

---

## Inhalt

- [Features](#features)
- [Schnellstart](#schnellstart)
- [Vollständige Installation](#vollständige-installation)
- [Menü-Übersicht](#menü-übersicht)
- [Web UI](#web-ui)
- [Alle Tools im Detail](#alle-tools-im-detail)
- [Disclaimer](#disclaimer)

---

## Features

Zwei Interfaces — ein Backend:

| Interface | Start | Beschreibung |
|-----------|-------|-------------|
| **Terminal TUI** | `sudo python3 classic_menu.py` | Klassisches ASCII-Menü, nummernbasiert |
| **Web UI** | `python3 web_app.py` | Browser-App auf `localhost:8080`, Maus-klickbar |

**18 Tool-Kategorien · 100+ integrierte Tools · Vollständig auf Deutsch**

---

## Schnellstart

```bash
git clone https://github.com/elliot433/penkit-tui.git
cd penkit-tui
sudo python3 classic_menu.py
```

Beim ersten Start: **H → Option 3** — zeigt alle Install-Befehle auf einmal.

---

## Vollständige Installation

### Schritt 1 — apt Pakete
```bash
sudo apt install -y nmap aircrack-ng hashcat john hydra ffuf sqlmap nikto \
  bettercap responder netexec adb exploitdb whatweb subfinder amass bloodhound \
  libimobiledevice-utils awscli golang-go socat openssl gitleaks \
  tor proxychains4 hostapd dnsmasq python3-impacket
```

### Schritt 2 — Go-Tools
```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/hahwul/dalfox/v2@latest
go install github.com/kgretzky/evilginx/v3@latest
go install github.com/sensepost/gowitness@latest
nuclei -update-templates
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc && source ~/.bashrc
```

### Schritt 3 — pip3 Pakete
```bash
pip3 install instaloader pypykatz requests flask bs4 \
  nicegui boto3 pyicloud mitm6 wafw00f --break-system-packages
```

### Schritt 4 — Ollama (KI-Terminal, optional)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

### Schritt 5 — Evilginx Phishlets (optional)
```bash
git clone https://github.com/An0nUD4Y/Evilginx2-Phishlets ~/.evilginx/phishlets
```

### Starten
```bash
# Terminal TUI (root empfohlen für WiFi/Netzwerk-Tools)
sudo python3 classic_menu.py

# Web UI (ohne root)
python3 web_app.py
# → Browser: http://localhost:8080
```

---

## Menü-Übersicht

| Taste | Kategorie | Tools |
|-------|-----------|-------|
| `1` | 📡 WiFi Attacks | WPA2/3 Crack, Handshake, PMKID, Deauth, Evil Twin, WPS |
| `2` | 🌐 Network Intelligence | Nmap, CVE-Check, Topology, Auto-Exploit |
| `3` | 💻 Web Attacks | SQLi, ffuf, Nikto, XSS, LFI, BeEF, Subdomain Takeover |
| `4` | 🔑 Passwords & Hashes | Hashcat GPU, John, Hydra, Hash-Erkennung |
| `5` | ☠️ MITM | ARP Spoof, SSL Strip, Responder, DNS Poison, NTLM Relay |
| `6` | 🔍 OSINT Recon | Shodan, Breach-Lookup, HIBP, Instagram/TikTok/Twitter |
| `7` | 🎣 Phishing Suite | Fake Login (11 Seiten), Telegram-Alert, Evilginx 2FA-Bypass |
| `8` | 🔵 Blue Team | ARP Watch, Auth-Log, Honeypot, Port Monitor |
| `9` | 💀 C2 / RAT | AMSI Bypass, Shellcode, Process Hollow, HTTPS Shell |
| `W` | 🏰 Active Directory | Kerberoast, PtH, BloodHound, DCSync, Golden Ticket |
| `P` | 🔥 Post-Exploitation | LSASS Dump, Keylogger, Screenshot, Webcam, Browser-PW |
| `L` | 🔀 Lateral Movement | PTH, PTT, SMBExec, WMIExec, NTLM Relay, Pivot/Tunnel |
| `X` | 💣 Metasploit | Payloads, Multi/Handler, Top-Exploits, Post-Module RC |
| `K` | 📱 Mobile Attacks | iOS (AirDrop, MDM, iCloud), Android (APK, ADB, drozer) |
| `V` | 🔭 Auto-Recon / CVE | Subfinder+httpx+Nuclei Pipeline, Searchsploit, EPSS |
| `C` | ☁️ Cloud Attacks | S3 Buckets, EC2 Metadata, AWS Keys, GitHub Secrets |
| `N` | 🧅 Anonymität / OPSEC | Tor, Kill Switch, MAC Spoofing, Hostname, Log Wipe |
| `J` | 🃏 Joker / Pranks | Fake BSOD, Kahoot Bot, Browser Chaos |
| `A` | 🧠 AI Attack Terminal | Ollama-basiert, KI startet Angriffe automatisch |
| `?` | 🤖 KI-Assistent | Tool-Empfehlung per Frage |
| `H` | 🏥 Health Check | Tool-Status, Auto-Fix, Schnell-Install, Web UI starten |
| `T` | 📚 Tutorials | Schritt-für-Schritt Anleitungen |
| `M` | 🗺️ Target Map | Interaktive Karte mit Ziel-IPs + Credentials |
| `R` | 📊 HTML Report | Alle Scans → professioneller HTML-Report |
| `O` | 📁 Output-Verzeichnis | `~/penkit-output/` — alle gespeicherten Dateien |

---

## Web UI

```bash
python3 web_app.py
```

Browser öffnen: **http://localhost:8080**

- Linke Sidebar mit allen Kategorien
- Tool-Cards im Grid mit Danger-Level Badge
- Klick auf Tool → Dialog mit Eingabefeldern
- Live-Output Terminal (JetBrains Mono, Neon-Grün)
- Dark Cyberpunk Theme

Das Terminal-TUI und die Web UI laufen komplett unabhängig voneinander. Beide nutzen dieselben Tool-Module.

---

## Alle Tools im Detail

### 📡 WiFi Attacks

| Tool | Beschreibung |
|------|-------------|
| WiFi Scanner | airodump-ng — alle APs + Signal + WPS-Status |
| Handshake Capture | WPA2-Handshake mit automatischem Deauth |
| PMKID Attack | Clientless — kein verbundener Client nötig (hcxdumptool) |
| Deauth Flood | aireplay-ng — Clients vom Netzwerk trennen |
| Evil Twin + Portal | Fake-AP + Captive Portal → Passwort-Eingabe |
| WPS Scan | wash — WPS-fähige Router finden |
| Pixie-Dust Attack | WPS-PIN offline cracken (Sekunden) |
| Reaver | WPS-PIN online brute-force |
| Beacon Flood | mdk4 — Tausende Fake-SSIDs |
| Auto-Crack Pipeline | Capture → Deauth → Handshake → Crack automatisch |
| Auto-Combo | Deauth + Evil Twin + Portal + Telegram-Alert |

### 🌐 Network Intelligence

| Tool | Beschreibung |
|------|-------------|
| Nmap Scanner | Quick / Full / Stealth / Version / Vuln / UDP |
| CVE-Check | Nmap-Output → automatisch CVE-Matches |
| Auto-Exploit | CVE → passendes Metasploit-Modul vorschlagen |
| Topology Map | Netzwerk-Topologie visualisieren |
| IoT Scanner | Shodan-ähnlich im lokalen Netz |
| Lateral Movement | PTH, PTT, SMBExec, WMIExec, DCOM, NTLM Relay |
| Metasploit Integration | Payloads, Handler, Top-Exploits, Post-Modules |
| DNS C2 | DNS-over-HTTPS C2-Kanal (Cloudflare/Google DNS) |

### 💻 Web Attacks

| Tool | Beschreibung |
|------|-------------|
| Fingerprinting | whatweb, wafw00f, Wappalyzer-ähnlich |
| Directory Fuzzer | ffuf — versteckte Pfade, Parameter, VHosts |
| SQL Injection | SQLmap — automatisch + alle Datenbanken dumpen |
| XSS Engine | dalfox + 8 Kontexte + WAF-Bypass + Cookie-Steal |
| Nikto | Web-Vulnerability-Scanner |
| BeEF | Browser Exploitation Framework |
| Subdomain Takeover | 17 Services — GitHub Pages, Heroku, Netlify, S3, Azure... |
| LFI/RFI Scanner | Local/Remote File Inclusion |

### 🔑 Passwords & Hashes

| Tool | Beschreibung |
|------|-------------|
| Hash-Erkennung | 21 Typen automatisch erkennen |
| Hashcat | GPU-Crack — WPA2, NTLM, MD5, SHA, bcrypt... |
| John the Ripper | CPU-basiert, viele Formate |
| Hydra | SSH/FTP/RDP/SMB/MySQL/HTTP/SMTP brute-force |
| Wordlist Generator | Zielbasiert aus OSINT-Daten (Namen, Geburtstag...) |

### 🔍 OSINT Recon

| Tool | Beschreibung |
|------|-------------|
| theHarvester | E-Mails, Subdomains, IPs aus öffentlichen Quellen |
| Sherlock | Username auf 300+ Plattformen |
| Subdomain Enumeration | Sublist3r + crt.sh + Brute-Force |
| Google Dorks | Fertige Dork-Queries für Ziel generieren |
| Shodan | Verwundbare Geräte weltweit + IP-Lookup |
| Breach Lookup | HaveIBeenPwned — k-Anonymity, kein API-Key nötig |
| Passwort Breach Check | SHA1-Prefix — Passwort verlässt nie das Gerät |
| LinkedIn E-Mail Generator | Mitarbeiterliste → Firmen-E-Mail-Muster |
| Instagram OSINT | instaloader — Profil, Follower, Posts, Stories |
| TikTok OSINT | Follower, Likes, Videos — kein API-Key |
| Twitter/X OSINT | Via Nitter — kein Account nötig |
| Snapchat OSINT | Public API + Snapcode-Download + Location Tracker |
| WhatsApp Tracker | Online-Status-Tracking via Selenium |
| Credential Stuffing | Instagram/Discord — Proxy-Rotation, Stop-on-Hit |

### 🎣 Phishing Suite

**11 pixel-perfekte Login-Seiten:**

| Seite | Design |
|-------|--------|
| Google | Offizielles weißes Google-Design |
| Microsoft | MS-Login mit blauem Branding |
| Instagram | Gradient lila/orange |
| Apple | Minimalistisch, Apple-typisch |
| Bank | Generische Banking-Seite |
| TikTok | Schwarz/Rot mit Social-Login |
| Snapchat | Gelb mit Ghost-Emoji |
| Discord | Dark Mode #313338 |
| Twitter/X | Schwarz mit 𝕏 Logo |
| WhatsApp | Grün mit Sicherheits-Trick |
| Steam | Dark Blue Steam-Design |

**Weitere Phishing-Features:**
- Automatischer **Telegram-Alert** bei Credential-Capture (Token + Chat-ID)
- **Evilginx 2FA-Bypass** — 12 Phishlets (Google, Microsoft, Apple, PayPal, Amazon, Instagram, GitHub, Discord, Twitter, Facebook, LinkedIn, O365)
- E-Mail Phishing-Kampagnen (SMTP/Sendgrid)
- GoPhish Integration

### 💀 C2 / RAT Payloads

| Tool | Beschreibung |
|------|-------------|
| AMSI/ETW Bypass | PowerShell — umgeht Windows Defender |
| Fileless Shellcode | Injection ohne Datei auf Disk |
| Process Hollowing | Payload in legitimen Prozess einschleusen |
| Payload Disguise | Icon-Changer, Fake-Extensions (.pdf.exe) |
| HTTPS Shell Port 443 | Metasploit / PS SslStream / OpenSSL / socat / DNS-C2 |
| **UAC Bypass Suite** | fodhelper, eventvwr, sdclt, CMSTP, Token Steal, Juicy Potato |
| **Auto-PrivEsc Scanner** | 15+ Vektoren automatisch prüfen (WinPEAS-ähnlich) |
| **Spionage Suite** | Keylogger, Screenshot, Webcam, Browser-PW, WiFi-PW, Clipboard (PS1) |

### 🏰 Active Directory

| Angriff | Tool |
|---------|------|
| SMB Enumeration | NetExec/CrackMapExec |
| Password Spraying | NetExec — kein Lockout-Risiko |
| Kerberoasting | GetUserSPNs → Hashcat -m 13100 |
| AS-REP Roasting | GetNPUsers → Hashcat -m 18200 |
| Pass-the-Hash | impacket-psexec / NetExec |
| Secrets Dump | SAM + LSA + NTDS.dit |
| BloodHound | AD-Angriffspfade visualisieren |
| LDAP Dump | Alle User/Gruppen/Computer |
| DCSync | Alle Hashes replizieren |
| Golden Ticket | Kerberos Persistence |

### 🔥 Post-Exploitation (Windows Ziele)

Alle Payloads als **standalone PowerShell** — kein Tool-Upload nötig, Living off the Land.

| Modul | Funktion |
|-------|---------|
| Keylogger | SetWindowsHookEx — alle Tastenanschläge |
| Screenshot | System.Windows.Forms — sofortiger Desktop-Screenshot |
| Webcam | WIA COM-Interface + ffmpeg Fallback |
| Browser Passwords | DPAPI-Decrypt Chrome/Edge + Firefox + cmdkey |
| WiFi Passwords | netsh wlan show profiles — alle gespeicherten WLANs |
| Clipboard Monitor | Erkennt Passwörter/Tokens/Crypto-Wallets automatisch |
| LSASS Dump | comsvcs.dll MiniDump — AV-safe, kein Mimikatz |
| Persistence | Registry / Scheduled Task / WMI / Startup |

Optional: Telegram-Versand aller Ergebnisse an eigenen Bot.

### 🔀 Lateral Movement

| Methode | Beschreibung |
|---------|-------------|
| Pass-the-Hash | impacket-psexec, NetExec, Evil-WinRM, Metasploit |
| Pass-the-Ticket | Kerberos-Ticket stehlen + nutzen |
| SMBExec | Remote Command Execution via SMB |
| WMIExec | Remote Execution via WMI |
| DCOM Exec | 4 DCOM-Methoden |
| NTLM Relay | Responder + ntlmrelayx → automatisch weiterleiten |
| SSH Tunnel | sshuttle — transparenter Tunnel |
| SOCKS Proxy | chisel / ligolo-ng — Netzwerk pivoten |
| Port Forwarding | SSH-basiert, Remote-Bind |
| proxychains | Automatische Konfiguration |

### 📱 Mobile Attacks

**iOS (ohne Jailbreak):**

| Tool | Beschreibung |
|------|-------------|
| AirDrop Recon | Gerätename, MAC, SHA256-Hash passiv sniffing |
| MDM Config Profile | .mobileconfig — VPN + Proxy ohne Jailbreak |
| KARMA WiFi Attack | hostapd-karma — iOS Auto-Connect-Exploit |
| Apple ID Brute-Force | pyicloud — credential stuffing + Rate-Limit bypass |
| iCloud Backup Forensik | MVT + libimobiledevice — Pegasus-Check |
| Smishing Payloads | 6 SMS-Vorlagen für Apple ID / iCloud Phishing |

**Android:**

| Tool | Beschreibung |
|------|-------------|
| Meterpreter APK | Generieren, signieren, per QR-Code verteilen |
| ADB Exploitation | USB-Debugging + Netzwerk-ADB (Port 5555) |
| drozer Framework | App-Schwachstellen, Content Provider SQL-Injection |
| Android Forensik | ALEAPP, androidqf, SQLite WhatsApp-DBs |

### 🔭 Auto-Recon Pipeline

Vollautomatisch: **Domain eingeben → fertiger Report**

```
Phase 1: Subdomain Enumeration  (subfinder + amass + crt.sh)
Phase 2: Live-Host Check        (httpx)
Phase 3: Port Scan              (nmap --top-ports 1000)
Phase 4: Web Fingerprinting     (whatweb + wafw00f)
Phase 5: Vulnerability Scan     (nuclei — CVE Templates)
Phase 6: Screenshots            (gowitness)
Phase 7: Report                 (alle Ergebnisse in ~/penkit-output/)
```

**CVE Engine:**
- Searchsploit: Software + Version → Exploit-DB
- CVE Lookup: CVSS Score + Beschreibung + **EPSS** (Exploit-Wahrscheinlichkeit in %)
- Auto-Exploit aus Nmap-Output: alle Services automatisch in Exploit-DB suchen
- Top CVEs 2024 (Log4Shell, PAN-OS, ConnectWise, Apache ActiveMQ...)

### ☁️ Cloud Attacks

| Tool | Beschreibung |
|------|-------------|
| S3 Bucket Enumeration | 17 Varianten automatisch testen — öffentliche Buckets lesen/schreiben |
| EC2 Metadata Theft | `169.254.169.254` — IAM-Credentials via SSRF oder Shell |
| AWS Credential Validator | Gestohlene Keys auf IAM-Berechtigungen prüfen |
| GitHub Secret Scan | truffleHog / gitleaks — API Keys, AWS Keys, Passwörter in Repos |

### 🧅 Anonymität & OPSEC

| Feature | Beschreibung |
|---------|-------------|
| Tor starten/stoppen | automatische Konfiguration |
| Neue Identity | Neue Exit-IP ohne Neustart |
| IP & DNS Leak Check | Zeigt echte IP vs. Tor-Exit-IP |
| proxychains Config | Automatisch für alle Tools einrichten |
| Kill Switch | iptables blockt alles außer Tor-Traffic |
| MAC Spoofing | Alle Interfaces zufällig |
| Hostname Ändern | Zufälliger Windows-ähnlicher Name |
| Log Cleaner | bash_history + auth.log + system logs |
| Session Wipe | Captures, Keys, temp-Dateien löschen |
| OPSEC Score | 0–100 Bewertung der aktuellen Situation |

### 🏥 Health Check

- Prüft 50+ externe Tools nach Kategorie
- Prüft alle Python-Module des Projekts
- Prüft pip-Pakete (nicegui, boto3, pyicloud...)
- Sonderchecks: Ollama-Modelle, dalfox PATH, evilginx, nuclei Templates, Web UI
- **Auto-Fix**: fehlende apt/pip Tools automatisch installieren
- **Schnell-Install Guide**: alle Befehle auf einen Blick
- **Web UI starten**: direkt aus dem Menü per Klick
- Reliability Guide: wann klappen welche Tools (ehrliche Einschätzung)

---

## Voraussetzungen

- **Kali Linux** (empfohlen) oder Debian-basiertes Linux
- **Python 3.10+**
- **Root-Rechte** für WiFi / MITM / Netzwerk-Angriffe
- **Kali VirtualBox** mit ALFA AWUS036ACH für WiFi-Angriffe

---

## Projektstruktur

```
penkit-tui/
├── classic_menu.py          # Terminal TUI (Haupteinstieg)
├── web_app.py               # Browser Web UI (localhost:8080)
├── core/
│   ├── runner.py            # Async subprocess CommandRunner
│   ├── danger.py            # 5-stufiges Danger-System
│   ├── anon.py              # Tor / Anonymität
│   ├── opsec.py             # OPSEC Suite
│   ├── report_gen.py        # HTML Report Generator
│   └── output_dir.py        # ~/penkit-output/ Manager
└── tools/
    ├── wifi/                # WiFi Attacks
    ├── network/             # Network Intel + Lateral Movement + Metasploit
    ├── web/                 # Web Attacks
    ├── passwords/           # Passwörter & Hashes
    ├── mitm/                # MITM Suite
    ├── osint/               # OSINT Recon
    ├── phishing/            # Phishing Suite + Evilginx
    ├── c2/                  # C2 / RAT / Post-Exploitation
    ├── blueteam/            # Blue Team Defense
    ├── mobile/              # iOS + Android Attacks
    ├── recon/               # Auto-Recon Pipeline + CVE Engine
    ├── cloud/               # AWS / Cloud Attacks
    ├── joker/               # Joker / Pranks
    ├── health_check.py      # Health Check
    ├── tutorials.py         # Tutorials
    ├── assistant.py         # KI-Assistent
    └── ai_terminal.py       # AI Attack Terminal (Ollama)
```

---

## Disclaimer

Dieses Tool ist ausschließlich für **autorisierte Penetrationstests** auf Systemen gedacht, für die eine ausdrückliche schriftliche Genehmigung vorliegt. Der Einsatz gegen fremde Systeme ohne Erlaubnis ist in Deutschland strafbar (§ 202a ff. StGB) und kann zu Freiheitsstrafe führen. Der Autor übernimmt keinerlei Verantwortung für Missbrauch oder illegalen Einsatz.
