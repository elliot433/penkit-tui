"""
Live ASCII topology map rendered inside the Textual TUI.

Layout algorithm:
  - Gateway at centre-top
  - Discovered hosts arranged in a ring below
  - Each node shows: IP, OS icon, open port count, risk colour
  - Edges drawn with box-drawing characters
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.network.scanner import ScanSession, HostResult

from core.danger import DangerLevel


OS_ICONS = {
    "windows": "🪟",
    "linux":   "🐧",
    "macos":   "🍎",
    "android": "🤖",
    "router":  "📡",
    "printer": "🖨️",
    "unknown": "❓",
}

RISK_COLORS = {
    "critical": "bright_red",
    "high":     "red",
    "medium":   "dark_orange",
    "low":      "yellow",
    "clean":    "green",
}


def _os_icon(os_guess: str) -> str:
    low = os_guess.lower()
    if "windows" in low:  return OS_ICONS["windows"]
    if "linux" in low:    return OS_ICONS["linux"]
    if "mac" in low or "darwin" in low: return OS_ICONS["macos"]
    if "android" in low:  return OS_ICONS["android"]
    if "router" in low or "cisco" in low or "juniper" in low: return OS_ICONS["router"]
    return OS_ICONS["unknown"]


def _host_risk(host: "HostResult") -> str:
    if not host.cves:
        return "clean" if host.services else "clean"
    max_score = max((c.get("score", 0) for c in host.cves), default=0)
    if max_score >= 9:   return "critical"
    if max_score >= 7:   return "high"
    if max_score >= 4:   return "medium"
    return "low"


def _node_lines(ip: str, host: "HostResult", width: int = 20) -> list[str]:
    """Return lines for a single host node box."""
    icon = _os_icon(host.os_guess)
    risk = _host_risk(host)
    color = RISK_COLORS[risk]
    port_count = len([s for s in host.services if s.state == "open"])
    hostname_short = host.hostname[:12] + "…" if len(host.hostname) > 13 else host.hostname

    top    = "┌" + "─" * (width - 2) + "┐"
    bottom = "└" + "─" * (width - 2) + "┘"
    ip_line     = f"│ {icon} {ip:<{width-6}} │"
    host_line   = f"│  {hostname_short:<{width-4}} │" if hostname_short else f"│{' '*(width-2)}│"
    os_short    = (host.os_guess[:width-5] + "…") if len(host.os_guess) > width-4 else host.os_guess
    os_line     = f"│  [{color}]{os_short}[/{color}]"
    port_line   = f"│  Ports: {port_count}  CVEs: {len(host.cves):<{width-14}} │"

    return [top, ip_line, host_line, port_line, bottom]


def render_topology(session: "ScanSession", width: int = 100) -> str:
    """
    Render full ASCII topology as a rich markup string.
    Gateway at top-centre, hosts in a row below, edges connecting them.
    """
    if not session:
        return "[dim]No scan data yet.[/dim]"

    lines: list[str] = []

    # Title bar
    lines.append(f"[bold cyan]{'─'*width}[/bold cyan]")
    lines.append(f"[bold cyan]  NETWORK TOPOLOGY  —  {session.target}  —  {len(session.live_hosts)} hosts[/bold cyan]")
    lines.append(f"[bold cyan]{'─'*width}[/bold cyan]")
    lines.append("")

    # Gateway node
    gw = session.gateway or "?.?.?.?"
    gw_label = f"[bold yellow]┌──────────────────┐[/bold yellow]"
    gw_body  = f"[bold yellow]│  📡  GATEWAY      │[/bold yellow]"
    gw_ip    = f"[bold yellow]│  {gw:<16} │[/bold yellow]"
    gw_bot   = f"[bold yellow]└──────────────────┘[/bold yellow]"
    indent_gw = " " * max(0, (width // 2) - 10)
    for l in [gw_label, gw_body, gw_ip, gw_bot]:
        lines.append(indent_gw + l)
    lines.append(indent_gw + " " * 9 + "[yellow]│[/yellow]")

    if not session.results:
        lines.append("")
        lines.append("[dim]  Waiting for deep scan results…[/dim]")
        return "\n".join(lines)

    # Connector line spanning all hosts
    hosts_list = list(session.results.items())
    node_w = 22
    cols = min(len(hosts_list), max(1, width // (node_w + 2)))

    connector = indent_gw + " " * 9 + "[yellow]" + "├" + "─" * (min(cols, len(hosts_list)) * (node_w + 2) - 2) + "┤" + "[/yellow]"
    lines.append(connector)

    # Render host nodes in rows
    for row_start in range(0, len(hosts_list), cols):
        row = hosts_list[row_start:row_start + cols]

        # Build node boxes for this row
        node_boxes: list[list[str]] = []
        for ip, host in row:
            node_boxes.append(_node_lines(ip, host, node_w))

        max_h = max(len(b) for b in node_boxes)
        for box in node_boxes:
            while len(box) < max_h:
                box.append("│" + " " * (node_w - 2) + "│")

        # Print side-by-side
        for li in range(max_h):
            row_line = "  "
            for box_idx, box in enumerate(node_boxes):
                risk = _host_risk(row[box_idx][1])
                color = RISK_COLORS[risk]
                row_line += f"[{color}]{box[li]}[/{color}]  "
            lines.append(row_line)

        lines.append("")

    # Legend
    lines.append("[dim]  Risk: [bright_red]■ CRITICAL[/bright_red]  [red]■ HIGH[/red]  [dark_orange]■ MEDIUM[/dark_orange]  [yellow]■ LOW[/yellow]  [green]■ CLEAN[/green][/dim]")
    lines.append("")

    return "\n".join(lines)


def render_host_detail(host: "HostResult") -> str:
    """Detailed single-host view with all services and CVEs."""
    lines: list[str] = []
    icon = _os_icon(host.os_guess)
    risk = _host_risk(host)
    color = RISK_COLORS[risk]

    lines.append(f"[bold {color}]{'═'*60}[/bold {color}]")
    lines.append(f"[bold]{icon}  {host.ip}[/bold]" + (f"  [dim]({host.hostname})[/dim]" if host.hostname else ""))
    if host.os_guess:
        lines.append(f"[dim]OS: {host.os_guess} ({host.os_confidence}%)[/dim]")
    if host.mac:
        lines.append(f"[dim]MAC: {host.mac}  {host.vendor}[/dim]")
    lines.append("")

    if host.services:
        lines.append("[bold cyan]Open Ports:[/bold cyan]")
        for svc in sorted(host.services, key=lambda s: s.port):
            version_str = f"{svc.product} {svc.version}".strip()
            lines.append(f"  [cyan]{svc.port:>5}/{svc.protocol:<4}[/cyan]  {svc.name:<12}  {version_str}")
        lines.append("")

    if host.cves:
        lines.append("[bold red]CVEs:[/bold red]")
        for cve in sorted(host.cves, key=lambda c: c.get("score", 0), reverse=True)[:10]:
            score = cve.get("score", 0)
            sev_color = "bright_red" if score >= 9 else "red" if score >= 7 else "dark_orange"
            lines.append(f"  [{sev_color}]{cve['id']}  CVSS {score:.1f}[/{sev_color}]  port {cve['port']}")
        lines.append("")

    if host.attack_chain:
        lines.append("[bold yellow]Attack Chain:[/bold yellow]")
        for i, step in enumerate(host.attack_chain, 1):
            lines.append(f"  {i}. {step.get('name', '')}  {step.get('risk', '')}")
            lines.append(f"     [dim]$ {step.get('cmd', '')}[/dim]")

    return "\n".join(lines)
