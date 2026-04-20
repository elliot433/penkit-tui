"""
PenKit Target Map — interaktive Karte mit allen bekannten Infos pro Ziel.

Zeigt:
  - Marker pro Ziel (IP-Geolocation oder GPS-Koordinaten)
  - Popup mit allem was PenKit über das Gerät/die Person weiß:
      IP, Hostname, OS, Browser, Credentials, WLAN, offene Ports...
  - Farb-kodierte Marker: Rot = C2 aktiv, Gelb = Phishing, Blau = OSINT
  - Echtzeit-Update möglich (Datei wird live neu geladen)
  - Exportiert als self-contained HTML → öffnet in jedem Browser

Quellen die automatisch integriert werden:
  - C2 Agent (!sysinfo gibt IP + Stadt + Land)
  - Phishing-Server (IP jedes Opfers)
  - OSINT-Report
  - Manuelle Eingabe

Benötigt: pip3 install folium requests --break-system-packages
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

try:
    from core.danger import DangerLevel
    from ui.widgets.help_panel import ToolHelp
    HELP = ToolHelp(
        name="Target Map",
        description=(
            "Interaktive HTML-Karte mit Markern für alle Ziele. "
            "Zeigt IP, Standort, OS, Credentials und alle bekannten Infos im Popup."
        ),
        usage="Ziel hinzufügen (IP oder GPS), Karte generieren, im Browser öffnen.",
        danger_note="🟡 GELB — nur Visualisierung bereits vorhandener Daten.",
        example="192.168.1.50 → Geolocation automatisch → Marker auf Karte",
    )
    DANGER = DangerLevel.YELLOW
except ImportError:
    HELP = None
    DANGER = None

_DB_PATH = "/tmp/penkit_targets.json"

# Marker-Farben je Typ
MARKER_COLORS = {
    "c2":       "red",
    "phishing": "orange",
    "osint":    "blue",
    "wifi":     "purple",
    "manual":   "gray",
    "iot":      "green",
}

MARKER_ICONS = {
    "c2":       "skull-crossbones",
    "phishing": "fish",
    "osint":    "search",
    "wifi":     "wifi",
    "manual":   "map-marker",
    "iot":      "microchip",
}


@dataclass
class TargetInfo:
    # Identifikation
    label: str                          # Anzeigename
    source: str = "manual"              # c2 | phishing | osint | wifi | iot | manual

    # Standort
    ip: str = ""
    lat: float = 0.0
    lon: float = 0.0
    city: str = ""
    country: str = ""
    isp: str = ""

    # Gerät
    hostname: str = ""
    os: str = ""
    browser: str = ""
    user_agent: str = ""

    # Zugangsdaten
    username: str = ""
    password: str = ""
    wifi_ssid: str = ""
    wifi_password: str = ""

    # Netzwerk
    open_ports: list[int] = field(default_factory=list)
    mac_address: str = ""
    domain: str = ""

    # Meta
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "label": self.label, "source": self.source,
            "ip": self.ip, "lat": self.lat, "lon": self.lon,
            "city": self.city, "country": self.country, "isp": self.isp,
            "hostname": self.hostname, "os": self.os, "browser": self.browser,
            "user_agent": self.user_agent, "username": self.username,
            "password": self.password, "wifi_ssid": self.wifi_ssid,
            "wifi_password": self.wifi_password, "open_ports": self.open_ports,
            "mac_address": self.mac_address, "domain": self.domain,
            "timestamp": self.timestamp, "notes": self.notes, "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TargetInfo":
        t = cls(label=d.get("label", "Unknown"))
        for k, v in d.items():
            if hasattr(t, k):
                setattr(t, k, v)
        return t


# ── Geolocation ───────────────────────────────────────────────────────────────

async def geolocate_ip(ip: str) -> dict:
    """
    Holt Standort-Infos für eine IP via ipinfo.io (kostenlos, kein Key).
    Gibt dict mit lat, lon, city, country, isp zurück.
    """
    from core.runner import CommandRunner
    import json as _json

    result = {"lat": 0.0, "lon": 0.0, "city": "", "country": "", "isp": ""}

    async for line in CommandRunner().run([
        "curl", "-s", "--max-time", "5",
        f"https://ipinfo.io/{ip}/json",
    ]):
        try:
            data = _json.loads(line)
            loc = data.get("loc", "0,0").split(",")
            result["lat"]     = float(loc[0]) if loc[0] else 0.0
            result["lon"]     = float(loc[1]) if len(loc) > 1 else 0.0
            result["city"]    = data.get("city", "")
            result["country"] = data.get("country", "")
            result["isp"]     = data.get("org", "")
            result["hostname"]= data.get("hostname", "")
        except Exception:
            pass

    return result


# ── Datenbank ─────────────────────────────────────────────────────────────────

def load_targets(path: str = _DB_PATH) -> list[TargetInfo]:
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        return [TargetInfo.from_dict(d) for d in data]
    except Exception:
        return []


def save_targets(targets: list[TargetInfo], path: str = _DB_PATH):
    with open(path, "w") as f:
        json.dump([t.to_dict() for t in targets], f, indent=2)


def add_target(target: TargetInfo, path: str = _DB_PATH):
    targets = load_targets(path)
    # Update existing by IP if already there
    for i, t in enumerate(targets):
        if t.ip == target.ip and target.ip:
            targets[i] = target
            save_targets(targets, path)
            return
    targets.append(target)
    save_targets(targets, path)


# ── Auto-Import aus anderen Modulen ──────────────────────────────────────────

def import_from_phishing_log(log_path: str = "/tmp/penkit_phish_creds.json") -> list[TargetInfo]:
    """Liest Phishing-Logs und erstellt TargetInfo-Objekte."""
    targets = []
    if not os.path.exists(log_path):
        return targets
    try:
        with open(log_path) as f:
            creds = json.load(f)
        for c in creds:
            t = TargetInfo(
                label=f"Phishing: {c.get('username', c.get('ip', 'Unknown'))}",
                source="phishing",
                ip=c.get("ip", ""),
                username=c.get("username", ""),
                password=c.get("password", ""),
                user_agent=c.get("user_agent", ""),
                timestamp=c.get("timestamp", ""),
                notes=f"Page: {c.get('page', '?')}",
            )
            targets.append(t)
    except Exception:
        pass
    return targets


def import_from_osint_report(report_path: str) -> list[TargetInfo]:
    """Liest einen OSINT-Report und extrahiert IPs/Domains."""
    targets = []
    if not os.path.exists(report_path):
        return targets
    try:
        with open(report_path) as f:
            content = f.read()
        import re
        domain_m = re.search(r'# OSINT Report: (.+)', content)
        domain    = domain_m.group(1).strip() if domain_m else "unknown"
        ip_list   = re.findall(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', content)
        emails    = re.findall(r'- ([\w.+-]+@[\w.-]+\.\w+)', content)
        for ip in set(ip_list):
            if not ip.startswith("127."):
                t = TargetInfo(
                    label=f"OSINT: {domain} ({ip})",
                    source="osint", ip=ip, domain=domain,
                    notes=f"Emails found: {', '.join(emails[:3])}",
                )
                targets.append(t)
    except Exception:
        pass
    return targets


# ── Karte generieren ──────────────────────────────────────────────────────────

def _popup_html(t: TargetInfo) -> str:
    """Erstellt schönes HTML-Popup für einen Marker."""
    rows = []

    def row(label: str, value: str, danger: bool = False):
        if value:
            color = "#ff4444" if danger else "#333"
            rows.append(
                f'<tr><td style="color:#888;padding:2px 8px 2px 0;font-size:11px">'
                f'<b>{label}</b></td>'
                f'<td style="color:{color};font-size:12px;font-family:monospace">'
                f'{value}</td></tr>'
            )

    source_colors = {
        "c2": "#ff4444", "phishing": "#ff8800",
        "osint": "#4488ff", "wifi": "#aa44ff",
        "manual": "#888888", "iot": "#44aa44",
    }
    sc = source_colors.get(t.source, "#888")

    header = (
        f'<div style="font-family:Arial,sans-serif;min-width:280px;max-width:360px">'
        f'<div style="background:{sc};color:white;padding:8px 12px;border-radius:4px 4px 0 0;'
        f'font-weight:bold;font-size:14px">'
        f'🎯 {t.label}'
        f'</div>'
        f'<div style="padding:8px;background:#f9f9f9;border-radius:0 0 4px 4px">'
        f'<table style="width:100%;border-collapse:collapse">'
    )

    # Standort
    row("IP", t.ip)
    if t.city or t.country:
        row("Standort", f"{t.city}, {t.country}" if t.city else t.country)
    row("ISP", t.isp)
    row("Koordinaten", f"{t.lat:.4f}, {t.lon:.4f}" if t.lat else "")

    # Gerät
    if t.hostname:  row("Hostname", t.hostname)
    if t.os:        row("OS", t.os)
    if t.browser:   row("Browser", t.browser)
    if t.domain:    row("Domain", t.domain)
    if t.mac_address: row("MAC", t.mac_address)
    if t.open_ports:  row("Ports", ", ".join(str(p) for p in t.open_ports))

    # Credentials — rot hervorheben
    if t.username:      row("Username", t.username, danger=True)
    if t.password:      row("Passwort", t.password, danger=True)
    if t.wifi_ssid:     row("WLAN SSID", t.wifi_ssid, danger=True)
    if t.wifi_password: row("WLAN PW", t.wifi_password, danger=True)

    # Meta
    if t.notes:     row("Notiz", t.notes)
    row("Quelle", t.source.upper())
    row("Zeit", t.timestamp[:16].replace("T", " ") if t.timestamp else "")

    footer = '</table></div></div>'
    return header + "".join(rows) + footer


def generate_map(
    targets: list[TargetInfo] | None = None,
    output_path: str = "/tmp/penkit_map.html",
    auto_open: bool = True,
) -> str:
    """
    Generiert interaktive HTML-Karte mit allen Zielen.
    Gibt Pfad zur HTML-Datei zurück.
    """
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        raise ImportError("folium nicht installiert: pip3 install folium --break-system-packages")

    if targets is None:
        targets = load_targets()

    # Karte zentrieren: Mittelpunkt aller Koordinaten
    valid = [(t.lat, t.lon) for t in targets if t.lat != 0 and t.lon != 0]
    if valid:
        center_lat = sum(v[0] for v in valid) / len(valid)
        center_lon = sum(v[1] for v in valid) / len(valid)
        zoom = 4 if len(valid) > 1 else 10
    else:
        center_lat, center_lon, zoom = 50.0, 10.0, 4  # Europa-Übersicht

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",   # Hacker-Stil: dunkle Karte
        prefer_canvas=True,
    )

    # Karte-Titel
    title_html = f"""
    <div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);
         z-index:1000;background:rgba(0,0,0,0.8);color:#00ff41;
         padding:8px 20px;border-radius:4px;font-family:monospace;font-size:14px;
         border:1px solid #00ff41">
        🎯 PenKit Target Map — {len(targets)} Ziel(e)
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Marker-Cluster für viele Ziele
    cluster = MarkerCluster().add_to(m)

    for t in targets:
        if t.lat == 0 and t.lon == 0:
            continue

        color = MARKER_COLORS.get(t.source, "gray")

        popup = folium.Popup(
            folium.IFrame(_popup_html(t), width=380, height=300),
            max_width=400,
        )

        folium.Marker(
            location=[t.lat, t.lon],
            popup=popup,
            tooltip=f"🎯 {t.label} ({t.ip})",
            icon=folium.Icon(
                color=color,
                icon="info-sign",
                prefix="glyphicon",
            ),
        ).add_to(cluster)

    # Legende
    legend_html = """
    <div style="position:fixed;bottom:20px;right:20px;z-index:1000;
         background:rgba(0,0,0,0.85);color:white;padding:12px;
         border-radius:6px;font-family:monospace;font-size:12px;
         border:1px solid #333">
        <b>Legende</b><br>
        <span style="color:#ff4444">● C2 Agent</span><br>
        <span style="color:#ff8800">● Phishing</span><br>
        <span style="color:#4488ff">● OSINT</span><br>
        <span style="color:#aa44ff">● WiFi</span><br>
        <span style="color:#44aa44">● IoT</span><br>
        <span style="color:#888888">● Manuell</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(output_path)

    if auto_open:
        import subprocess
        subprocess.Popen(["xdg-open", output_path],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_path


# ── CLI-Interface für classic_menu ────────────────────────────────────────────

class MapTracker:
    async def add_ip(self, ip: str, label: str, source: str = "manual",
                     extra: dict | None = None) -> AsyncGenerator[str, None]:
        yield f"[*] Geolocating {ip}..."
        geo = await geolocate_ip(ip)

        t = TargetInfo(
            label=label or ip,
            source=source,
            ip=ip,
            lat=geo["lat"],
            lon=geo["lon"],
            city=geo["city"],
            country=geo["country"],
            isp=geo["isp"],
            hostname=geo.get("hostname", ""),
        )
        if extra:
            for k, v in extra.items():
                if hasattr(t, k):
                    setattr(t, k, v)
                else:
                    t.extra[k] = v

        add_target(t)
        if geo["lat"]:
            yield f"[+] {ip} → {geo['city']}, {geo['country']}  ({geo['lat']:.3f}, {geo['lon']:.3f})"
        else:
            yield f"[+] {ip} gespeichert (kein Standort verfügbar — offline/privat?)"

    async def import_all_sources(self) -> AsyncGenerator[str, None]:
        yield "[*] Importiere aus allen PenKit-Quellen..."
        total = 0

        # Phishing
        ph_targets = import_from_phishing_log()
        for t in ph_targets:
            geo = await geolocate_ip(t.ip)
            t.lat, t.lon = geo["lat"], geo["lon"]
            t.city, t.country = geo["city"], geo["country"]
            add_target(t)
        if ph_targets:
            yield f"[+] Phishing: {len(ph_targets)} Ziel(e) importiert"
            total += len(ph_targets)

        # OSINT Reports
        import glob
        for report in glob.glob("/tmp/osint_report_*.md"):
            osint_targets = import_from_osint_report(report)
            for t in osint_targets:
                geo = await geolocate_ip(t.ip)
                t.lat, t.lon = geo["lat"], geo["lon"]
                t.city, t.country = geo["city"], geo["country"]
                add_target(t)
            if osint_targets:
                yield f"[+] OSINT {os.path.basename(report)}: {len(osint_targets)} IP(s)"
                total += len(osint_targets)

        yield f"[+] Gesamt: {total} neue Ziele importiert"

    async def generate(self, output_path: str = "/tmp/penkit_map.html") -> AsyncGenerator[str, None]:
        yield "[*] Prüfe folium..."
        try:
            import folium  # noqa
        except ImportError:
            yield "[!] folium nicht installiert."
            yield "[*] Installiere: pip3 install folium --break-system-packages"
            from core.runner import CommandRunner
            async for line in CommandRunner().run([
                "pip3", "install", "folium", "--break-system-packages", "-q"
            ]):
                if line.strip():
                    yield f"  {line}"

        targets = load_targets()
        if not targets:
            yield "[!] Keine Ziele in Datenbank."
            yield "[*] Zuerst Ziele hinzufügen (Option 1 oder 3)"
            return

        valid = [t for t in targets if t.lat != 0 or t.lon != 0]
        yield f"[*] {len(targets)} Ziel(e) total, {len(valid)} mit Koordinaten"

        yield "[*] Generiere Karte..."
        try:
            path = generate_map(targets, output_path)
            yield f"[+] Karte gespeichert: {path}"
            yield f"[+] Öffne im Browser..."
            yield f"[*] Falls nicht automatisch öffnet: firefox {path}"
        except Exception as e:
            yield f"[!] Fehler: {e}"

    def list_targets(self) -> list[TargetInfo]:
        return load_targets()

    def clear_targets(self):
        save_targets([])
