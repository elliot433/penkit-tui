# PenKit TUI v3

```
  ██████╗ ███████╗███╗   ██╗██╗  ██╗██╗████████╗
  ██╔══██╗██╔════╝████╗  ██║██║ ██╔╝██║╚══██╔══╝
  ██████╔╝█████╗  ██╔██╗ ██║█████╔╝ ██║   ██║
  ██╔═══╝ ██╔══╝  ██║╚████║██╔═██╗ ██║   ██║
  ██║     ███████╗██║ ╚███║██║  ██╗██║   ██║
  ╚═╝     ╚══════╝╚═╝  ╚══╝╚═╝  ╚═╝╚═╝   ╚═╝
```

> **Authorized Pentesting Toolkit — für Kali Linux**  
> Vollständiges Terminal-UI für professionelle Penetrationstests.  
> ⚠️ Nur für autorisierte Tests auf eigenen oder freigegebenen Systemen verwenden.

---

## Features

### 🧅 Anonymität & Tor
- Tor automatisch starten/stoppen
- Neue Exit-Identity anfordern (neue IP)
- IP & DNS-Leak-Check (echte IP vs Tor-Exit-IP)
- proxychains automatisch konfigurieren
- Banner zeigt immer aktuellen Anonymitätsstatus (rot/grün)

### 📡 WiFi Attacks
- WPA2/WPA3 Handshake Capture + Deauth
- PMKID Attack (kein Client nötig)
- Evil Twin Access Point
- Captive Portal (Passwort-Eingabe-Trick)
- **Auto-Combo:** Deauth + Evil Twin + Captive Portal + Telegram-Alert in einem Schritt
- Reaver WPS Brute-Force
- Beacon Flood (Tausende Fake-SSIDs)
- Auto-Crack Pipeline: Capture → Crack automatisch

### 🌐 Network Intelligence
- Nmap: Quick/Full/Stealth/Version/Vuln Scan
- CVE-Erkennung aus Scan-Output
- Auto-Exploit Suggester (CVE → Metasploit-Modul)
- Netzwerk-Topology-Karte
- Service-basierte Angriffsketten

### 💻 Web Attacks
- SQLmap (automatisch + manuell)
- ffuf Directory Fuzzing
- Nikto Vulnerability Scanner
- XSS Engine (dalfox + XSStrike + eigene Payloads)
- XSS Contexts: HTML, Attribute, JS-String, WAF-Bypass, DOM, Blind, Cookie-Steal, Keylogger
- LFI/RFI Scanner
- BeEF Browser Exploitation Framework
- **Subdomain Takeover Scanner** — 17 Services (GitHub Pages, Heroku, Netlify, Vercel, AWS S3, Azure, Shopify, Fastly, Zendesk, Tumblr, Ghost, Surge.sh, Readme.io, Unbounce, HubSpot, WordPress.com, Pantheon)

### 🔑 Passwords & Hashes
- Hashcat GPU (Auto-Modus + Manuell)
- John the Ripper
- WPA2 .cap Crack
- Hydra Brute-Force (SSH/FTP/RDP/SMB/MySQL/HTTP)
- Smart Wordlist Generator (zielbasiert aus OSINT-Daten)

### ☠️ MITM
- ARP Spoofing
- SSL Strip (HTTPS → HTTP)
- DNS Poisoning
- Credential Harvester (Live-Passwörter im Netzwerk)
- Responder (NTLM Hashes via LLMNR/NBT-NS)
- mitm6 (IPv6 → Domain Admin)
- NTLM Relay (Responder + ntlmrelayx)

### 🔍 OSINT Recon
- theHarvester (E-Mails, Subdomains, IPs)
- Sherlock (Username auf 300+ Plattformen)
- Subdomain Enumeration (Sublist3r + crt.sh + Brute)
- Google Dorks Generator
- Shodan (Device Search, IP Lookup, eigene externe IP)
- **Breach Lookup** (HaveIBeenPwned — k-Anonymity)
- Bulk E-Mail Breach Check
- LinkedIn / E-Mail Generator (Mitarbeiterliste → Firmen-Mails)
- Passwort Breach Check (k-Anonymity — Passwort verlässt nie das Gerät)
- **Instagram OSINT** (instaloader — Profil, Follower, Posts)
- **TikTok OSINT** (Follower, Likes, Videos — kein API-Key)
- **Twitter/X OSINT** (via Nitter — kein Account nötig)
- **Credential Stuffing** (instagram/discord — Proxy-Rotation, Stop-on-Hit)

### 🎣 Phishing Suite
**11 pixel-perfekte Login-Seiten:**
| Seite | Design |
|-------|--------|
| Google | Weißes Google-Design |
| Microsoft | Offizielles MS-Layout |
| Instagram | Gradient lila/orange |
| Apple | Apple-typisch minimalistisch |
| Bank | Generische Banking-Seite |
| TikTok | Schwarz/Rot mit Social-Login |
| Snapchat | Gelb mit Ghost-Emoji |
| Discord | Dark Mode #313338 |
| Twitter/X | Schwarz mit 𝕏 Logo |
| WhatsApp | Grün mit Sicherheits-Trick |
| Steam | Dark Blue Steam-Design |

- Automatischer **Telegram-Alert** bei Credential-Capture
- E-Mail Phishing-Kampagnen (Sendgrid/SMTP)
- Ngrok-Integration für öffentliche URLs

### 💀 C2 / RAT Payloads
- AMSI Bypass (PowerShell)
- Fileless Shellcode Injection
- Process Hollowing
- Payload Disguise (Icon-Changer, Fake-Extensions)
- **HTTPS Reverse Shell (Port 443):**
  - Metasploit HTTPS Handler (beste Stabilität)
  - PowerShell SslStream Shell (kein MSF nötig)
  - OpenSSL TLS Pipes (kein Upload nötig)
  - socat TLS (Linux/Windows)
  - DNS over HTTPS C2 (ultra-stealthy, via Cloudflare/Google DNS)

### 🏰 Active Directory
- SMB Enumeration (NetExec/CrackMapExec)
- Password Spraying
- **Kerberoasting** (Hashcat -m 13100)
- **AS-REP Roasting** (Hashcat -m 18200)
- Pass-the-Hash
- Secrets Dump (SAM + LSA + NTDS.dit via impacket)
- BloodHound Daten sammeln (AD-Angriffspfade)
- LDAP Dump (alle User/Gruppen/Computer)
- DCSync (alle Hashes replizieren)
- Golden Ticket (Kerberos Persistence)

### 🔥 Post-Exploitation
- LSASS Dump (comsvcs.dll MiniDump — kein Mimikatz, AV-safe)
- LSASS Analyse (pypykatz)
- Persistence: Registry / Scheduled Task / WMI / Startup
- LOLBAS Übersicht (Living off the Land)
- Exfil Payloads generieren (DNS, HTTP, SMB, Cloud)

### 🔵 Blue Team Defense
- ARP Spoof Detector (Live)
- Auth Log Analyse (historisch + live)
- Port Monitor (Baseline + Diff)
- Honeypot Suite

### 🃏 Joker / Pranks
- Fake BSOD
- Kahoot Bot
- Browser Chaos
- u.v.m.

### 🛠️ System
- **KI-Assistent** — Tool-Empfehlung per Frage
- **AI Attack Terminal** — KI startet Angriffe automatisch (Ollama)
- **Health Check** — Prüft alle installierten Tools + Auto-Fix
- **Target Map** — Interaktive Karte mit Ziel-Infos (IP, Credentials, OS)
- **HTML Report Generator** — Alle Scans → professioneller Report

---

## Installation

```bash
# Repo klonen
git clone https://github.com/elliot433/penkit-tui.git
cd penkit-tui

# Python-Abhängigkeiten
pip3 install -r requirements.txt --break-system-packages
pip3 install instaloader pypykatz --break-system-packages

# System-Tools
sudo apt install -y subfinder amass bloodhound python3-impacket \
  netexec socat hostapd dnsmasq aircrack-ng tor proxychains4 golang-go

# dalfox (XSS Scanner)
go install github.com/hahwul/dalfox/v2@latest
export PATH=$PATH:~/go/bin

# Starten
python3 classic_menu.py
```

---

## Anonymes Starten (empfohlen)

```bash
# 1. PenKit starten → N → Tor starten
python3 classic_menu.py

# 2. Neu starten mit Tor-Proxy
proxychains4 python3 classic_menu.py
```

Das Banner zeigt immer ob Tor aktiv ist.

---

## Voraussetzungen

- Kali Linux (empfohlen) oder anderes Debian-basiertes Linux
- Python 3.10+
- Root-Rechte für WiFi/MITM/Netzwerk-Angriffe

---

## Disclaimer

Dieses Tool ist ausschließlich für **autorisierte Penetrationstests** auf Systemen gedacht, für die du ausdrückliche Genehmigung hast. Der Einsatz gegen fremde Systeme ohne Erlaubnis ist illegal und strafbar. Der Autor übernimmt keine Verantwortung für Missbrauch.
