"""
PenKit Output Directory Manager.

Alle Dateien werden strukturiert in ~/penkit-output/ gespeichert.
Kein /tmp-Chaos mehr.

Struktur:
  ~/penkit-output/
  ├── wifi/         — Handshakes (.cap), PMKID (.hc22000), Monitor-Logs
  ├── passwords/    — Hash-Dateien, gecrackte Passwörter, Wordlists
  ├── payloads/     — C2 Payloads (PS1, HTA, BAT, VBA, EXE)
  ├── phishing/     — Credential-Logs, Server-Logs, Templates
  ├── osint/        — Recon-Reports, Subdomain-Listen, Email-Listen
  ├── network/      — Nmap-Scans, Topology, CVE-Reports
  ├── mitm/         — Credential-Captures, PCAP-Dateien
  ├── maps/         — Interaktive HTML-Karten
  ├── wordlists/    — Generierte Wortlisten
  └── logs/         — Alle Tool-Logs
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

# Haupt-Verzeichnis
ROOT = Path.home() / "penkit-output"

# Unterverzeichnisse
DIRS = {
    "wifi":      ROOT / "wifi",
    "passwords": ROOT / "passwords",
    "payloads":  ROOT / "payloads",
    "phishing":  ROOT / "phishing",
    "osint":     ROOT / "osint",
    "network":   ROOT / "network",
    "mitm":      ROOT / "mitm",
    "maps":      ROOT / "maps",
    "wordlists": ROOT / "wordlists",
    "logs":      ROOT / "logs",
}


def setup() -> Path:
    """Erstellt alle Verzeichnisse beim ersten Aufruf."""
    ROOT.mkdir(parents=True, exist_ok=True)
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    return ROOT


def get(category: str) -> Path:
    """Gibt den Pfad für eine Kategorie zurück. Erstellt ihn wenn nötig."""
    path = DIRS.get(category, ROOT / category)
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_file(category: str, name: str, ext: str = "") -> Path:
    """
    Erstellt einen neuen Dateipfad mit Timestamp.
    z.B. new_file("wifi", "handshake", "cap") → ~/penkit-output/wifi/handshake_20240420_153045.cap
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{ts}{('.' + ext) if ext else ''}"
    return get(category) / filename


def new_session_dir(category: str, name: str = "") -> Path:
    """
    Erstellt ein neues Session-Verzeichnis mit Timestamp.
    z.B. new_session_dir("payloads") → ~/penkit-output/payloads/session_20240420_153045/
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{name}_" if name else ""
    d = get(category) / f"{prefix}{ts}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_files(category: str, pattern: str = "*") -> list[Path]:
    """Listet Dateien einer Kategorie auf."""
    d = get(category)
    return sorted(d.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


def summary() -> str:
    """Zeigt Übersicht aller gespeicherten Dateien."""
    setup()
    lines = [f"📁 PenKit Output: {ROOT}", ""]
    total_files = 0
    total_size = 0
    for name, path in DIRS.items():
        files = list(path.glob("**/*")) if path.exists() else []
        file_count = len([f for f in files if f.is_file()])
        size = sum(f.stat().st_size for f in files if f.is_file())
        size_kb = size // 1024
        if file_count > 0:
            lines.append(f"  {name:<12}  {file_count:>4} Datei(en)  {size_kb:>6} KB")
        total_files += file_count
        total_size += size
    lines.append("")
    lines.append(f"  Gesamt: {total_files} Dateien  |  {total_size // 1024 // 1024} MB")
    return "\n".join(lines)


# Beim Import automatisch aufsetzen
setup()
