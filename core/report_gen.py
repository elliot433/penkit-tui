"""
PenKit HTML Report Generator — alle Scan-Ergebnisse in einem professionellen Report.

Liest alle Dateien aus ~/penkit-output/ und generiert:
  - Übersichts-Dashboard (gefundene Hosts, CVEs, Credentials, etc.)
  - Detaillierte Sektionen pro Kategorie
  - Farbcodierung nach Kritikalität
  - Exportierbar als standalone HTML (keine externen Dependencies)
"""

from __future__ import annotations
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from core.output_dir import ROOT, DIRS, list_files


_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #0d0d0d; color: #e0e0e0; }
.header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px 40px;
          border-bottom: 2px solid #e94560; }
.header h1 { color: #e94560; font-size: 28px; letter-spacing: 2px; }
.header .meta { color: #888; font-size: 13px; margin-top: 8px; }
.container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
.dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
             gap: 16px; margin-bottom: 40px; }
.stat-card { background: #1a1a2e; border: 1px solid #2a2a4e; border-radius: 8px;
             padding: 20px; text-align: center; }
.stat-card .num { font-size: 36px; font-weight: bold; }
.stat-card .label { font-size: 12px; color: #888; margin-top: 4px; text-transform: uppercase; }
.red    { color: #e94560; } .orange { color: #ff7700; }
.yellow { color: #ffd700; } .green  { color: #00cc66; } .blue { color: #4fc3f7; }
.section { background: #111; border: 1px solid #222; border-radius: 8px;
           margin-bottom: 24px; overflow: hidden; }
.section-header { background: #1a1a2e; padding: 14px 20px; border-bottom: 1px solid #222;
                  cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
.section-header h2 { font-size: 16px; color: #4fc3f7; }
.section-content { padding: 16px 20px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #1a1a2e; padding: 10px 12px; text-align: left; color: #888;
     font-weight: 600; text-transform: uppercase; font-size: 11px; }
td { padding: 9px 12px; border-bottom: 1px solid #1a1a1a; }
tr:hover td { background: #151525; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
.badge-critical { background: #3d0010; color: #ff3366; border: 1px solid #e94560; }
.badge-high     { background: #3d1500; color: #ff7700; border: 1px solid #ff7700; }
.badge-medium   { background: #3d3000; color: #ffd700; border: 1px solid #ffd700; }
.badge-low      { background: #003d10; color: #00cc66; border: 1px solid #00cc66; }
.badge-info     { background: #00233d; color: #4fc3f7; border: 1px solid #4fc3f7; }
pre { background: #0a0a0a; border: 1px solid #222; border-radius: 4px; padding: 12px;
      font-size: 12px; overflow-x: auto; color: #aaa; white-space: pre-wrap; }
.cred-row td:nth-child(2) { color: #ff7700; font-family: monospace; }
.cred-row td:nth-child(3) { color: #e94560; font-family: monospace; }
.timeline { list-style: none; padding: 0; }
.timeline li { padding: 8px 0; border-bottom: 1px solid #1a1a1a; font-size: 13px; }
.timeline li span { color: #888; font-size: 11px; }
.tag { display: inline-block; background: #1a1a2e; border: 1px solid #2a2a4e;
       border-radius: 4px; padding: 2px 6px; font-size: 11px; margin: 2px; }
"""

_JS = """
document.querySelectorAll('.section-header').forEach(h => {
    h.addEventListener('click', () => {
        const content = h.nextElementSibling;
        const arrow = h.querySelector('.arrow');
        if (content.style.display === 'none') {
            content.style.display = 'block';
            arrow.textContent = '▼';
        } else {
            content.style.display = 'none';
            arrow.textContent = '▶';
        }
    });
});
"""


def _badge(level: str) -> str:
    l = level.lower()
    return f'<span class="badge badge-{l}">{level.upper()}</span>'


def _section(title: str, icon: str, content: str, count: int = 0) -> str:
    count_html = f' <span class="badge badge-info">{count}</span>' if count else ""
    return (
        f'<div class="section">'
        f'<div class="section-header"><h2>{icon} {title}{count_html}</h2>'
        f'<span class="arrow">▼</span></div>'
        f'<div class="section-content">{content}</div>'
        f'</div>'
    )


def _parse_exploits_json(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text()).get("cves", [])
    except Exception:
        return []


def _parse_creds_json(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _read_file_safe(path: Path, max_bytes: int = 32768) -> str:
    try:
        text = path.read_bytes()[:max_bytes].decode(errors="replace")
        return text
    except Exception:
        return ""


def _ansi_strip(text: str) -> str:
    return re.sub(r'\033\[[0-9;]*m', '', text)


async def generate_report(title: str = "PenKit Pentest Report") -> AsyncGenerator[str, None]:
    """Generiert kompletten HTML-Report aus ~/penkit-output/."""

    yield "\033[1;36m[*] Sammle Daten aus ~/penkit-output/...\033[0m"

    now = datetime.now()
    sections_html = []
    stats = {
        "cves": 0, "creds": 0, "payloads": 0,
        "wifi_caps": 0, "osint_entries": 0, "files_total": 0,
    }

    # ── CVE / Exploit-Findings ─────────────────────────────────────────────
    exploit_files = list(DIRS["network"].glob("exploits_*.json"))
    if exploit_files:
        rows = []
        for f in exploit_files:
            cves = _parse_exploits_json(f)
            for cve in cves:
                stats["cves"] += 1
                cvss = cve.get("cvss", 0)
                risk = "critical" if cvss >= 9 else "high" if cvss >= 7 else "medium" if cvss >= 4 else "low"
                msf = "<br>".join(f'<code class="tag">{m}</code>' for m in cve.get("msf", [])[:3])
                rows.append(
                    f'<tr><td>{cve.get("id","?")}</td>'
                    f'<td>{_badge(risk)} {cvss:.1f}</td>'
                    f'<td>{cve.get("port","?")} / {cve.get("service","?")}</td>'
                    f'<td>{msf or "—"}</td></tr>'
                )

        table = (
            '<table><tr><th>CVE</th><th>CVSS</th><th>Port/Service</th><th>Metasploit Module</th></tr>'
            + "".join(rows) + '</table>'
        )
        sections_html.append(_section("CVE Findings", "🎯", table, stats["cves"]))
        yield f"  CVEs: {stats['cves']}"

    # ── Credentials ────────────────────────────────────────────────────────
    cred_files = list(DIRS["passwords"].glob("*.json")) + list(Path("/tmp").glob("penkit_phish_creds.json"))
    if cred_files:
        rows = []
        for f in cred_files:
            creds = _parse_creds_json(f)
            for c in creds:
                stats["creds"] += 1
                rows.append(
                    f'<tr class="cred-row">'
                    f'<td>{c.get("time","?")}</td>'
                    f'<td>{c.get("username","") or c.get("user","")}</td>'
                    f'<td>{c.get("password","") or c.get("pass","")}</td>'
                    f'<td>{c.get("source","phishing")}</td></tr>'
                )

        if rows:
            table = (
                '<table><tr><th>Zeit</th><th>Username</th><th>Passwort</th><th>Quelle</th></tr>'
                + "".join(rows) + '</table>'
            )
            sections_html.append(_section("Erbeutete Credentials", "🔑", table, stats["creds"]))
            yield f"  Credentials: {stats['creds']}"

    # ── Scan-Outputs ───────────────────────────────────────────────────────
    scan_files = list(DIRS["network"].glob("autoscan_*.txt"))
    if scan_files:
        tabs = []
        for f in scan_files[:5]:
            content = _ansi_strip(_read_file_safe(f))
            hostname = f.stem.replace("autoscan_", "").replace("_", ".")
            tabs.append(f'<div style="margin-bottom:12px"><strong style="color:#4fc3f7">{hostname}</strong><pre>{content[:4000]}</pre></div>')
        sections_html.append(_section("Nmap Scan-Ergebnisse", "🗺️", "".join(tabs), len(scan_files)))
        yield f"  Scans: {len(scan_files)}"

    # ── WiFi ──────────────────────────────────────────────────────────────
    wifi_files = list(DIRS["wifi"].glob("*.cap")) + list(DIRS["wifi"].glob("*.hc22000"))
    if wifi_files:
        stats["wifi_caps"] = len(wifi_files)
        rows = [
            f'<tr><td>{f.name}</td><td>{f.stat().st_size // 1024} KB</td>'
            f'<td>{datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}</td></tr>'
            for f in wifi_files
        ]
        table = '<table><tr><th>Datei</th><th>Größe</th><th>Erstellt</th></tr>' + "".join(rows) + '</table>'
        sections_html.append(_section("WiFi Captures", "📡", table, stats["wifi_caps"]))

    # ── OSINT ─────────────────────────────────────────────────────────────
    osint_files = list(DIRS["osint"].glob("*.txt")) + list(DIRS["osint"].glob("*.json"))
    if osint_files:
        stats["osint_entries"] = len(osint_files)
        items = []
        for f in osint_files[:10]:
            size = f.stat().st_size
            items.append(f'<li><span class="tag">{f.suffix}</span> {f.name} <span>({size} Bytes)</span></li>')
        sections_html.append(_section("OSINT Daten", "🔍", f'<ul class="timeline">{"".join(items)}</ul>', stats["osint_entries"]))

    # ── Payloads ──────────────────────────────────────────────────────────
    payload_files = list(DIRS["payloads"].glob("*"))
    if payload_files:
        stats["payloads"] = len(payload_files)
        items = [
            f'<li><span class="tag">{f.suffix or "no-ext"}</span> {f.name} '
            f'<span>({f.stat().st_size // 1024} KB)</span></li>'
            for f in payload_files if f.is_file()
        ]
        sections_html.append(_section("Generierte Payloads", "💀", f'<ul class="timeline">{"".join(items)}</ul>', stats["payloads"]))

    # ── Alle Dateien Übersicht ─────────────────────────────────────────────
    all_files = []
    for cat, path in DIRS.items():
        for f in path.glob("*"):
            if f.is_file():
                all_files.append((cat, f))
    stats["files_total"] = len(all_files)

    # ── Dashboard ─────────────────────────────────────────────────────────
    dashboard_html = (
        f'<div class="dashboard">'
        f'<div class="stat-card"><div class="num red">{stats["cves"]}</div><div class="label">CVEs gefunden</div></div>'
        f'<div class="stat-card"><div class="num orange">{stats["creds"]}</div><div class="label">Credentials</div></div>'
        f'<div class="stat-card"><div class="num yellow">{stats["payloads"]}</div><div class="label">Payloads</div></div>'
        f'<div class="stat-card"><div class="num green">{stats["wifi_caps"]}</div><div class="label">WiFi Captures</div></div>'
        f'<div class="stat-card"><div class="num blue">{stats["osint_entries"]}</div><div class="label">OSINT Einträge</div></div>'
        f'<div class="stat-card"><div class="num">{stats["files_total"]}</div><div class="label">Dateien gesamt</div></div>'
        f'</div>'
    )

    # ── HTML zusammenbauen ─────────────────────────────────────────────────
    if not sections_html:
        sections_html.append(
            _section("Keine Daten", "📭",
                     '<p style="color:#888;padding:20px">Noch keine Scan-Ergebnisse in ~/penkit-output/.<br>'
                     'Führe zuerst Scans durch (Netzwerk, WiFi, OSINT...).</p>')
        )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="header">
  <h1>🎯 {title}</h1>
  <div class="meta">
    Generiert: {now.strftime('%d.%m.%Y %H:%M')} &nbsp;|&nbsp;
    PenKit TUI v3 &nbsp;|&nbsp;
    Ziel-System: autorisiert
  </div>
</div>
<div class="container">
{dashboard_html}
{"".join(sections_html)}
</div>
<script>{_JS}</script>
</body>
</html>"""

    # Speichern
    out_path = ROOT / f"report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    out_path.write_text(html, encoding="utf-8")

    yield f"\n\033[1;32m[✓] Report erstellt: {out_path}\033[0m"
    yield f"\033[36m[→] Öffnen: firefox {out_path} &\033[0m"
    yield f"    Dashboard: {stats['cves']} CVEs | {stats['creds']} Creds | {stats['files_total']} Dateien"
