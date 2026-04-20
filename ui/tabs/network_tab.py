import asyncio
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button, Switch, TabbedContent, TabPane
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import on
from textual.message import Message
from rich.text import Text

from core.config import load as load_config
from core.danger import DangerLevel
from ui.widgets.output_view import OutputView
from ui.widgets.tool_card import ToolCard
from ui.widgets.help_panel import ToolHelp
from tools.network import NetworkScanner, render_topology, render_host_detail
import tools.network.scanner as _ns

HELP_SCAN = _ns.HELP
DANGER_SCAN = _ns.DANGER


class NetworkHelpRequest(Message):
    def __init__(self, info: ToolHelp):
        super().__init__()
        self.help_info = info


class NetworkTab(Widget):
    DEFAULT_CSS = """
    NetworkTab {
        height: 1fr;
    }
    NetworkTab #top-bar {
        height: auto;
        background: #0a0a14;
        border-bottom: solid #1a1a2e;
        padding: 1 2;
    }
    NetworkTab #target-input {
        width: 35;
    }
    NetworkTab #btn-scan-full {
        background: #6c63ff;
        color: white;
        margin-left: 2;
        width: auto;
    }
    NetworkTab #btn-scan-quick {
        background: #333355;
        color: white;
        margin-left: 1;
        width: auto;
    }
    NetworkTab #btn-stop-net {
        background: #cc2222;
        color: white;
        margin-left: 1;
        width: auto;
    }
    NetworkTab #btn-export {
        background: #1a3a1a;
        color: #44cc44;
        margin-left: 1;
        width: auto;
    }
    NetworkTab #stealth-label {
        content-align: left middle;
        margin-left: 2;
        color: #7777aa;
    }
    NetworkTab #main-area {
        height: 1fr;
        layout: horizontal;
    }
    NetworkTab #left-pane {
        width: 55%;
        border-right: solid #1a1a2e;
    }
    NetworkTab #right-pane {
        width: 45%;
        padding: 1;
    }
    NetworkTab #topology-view {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
        background: #05050f;
    }
    NetworkTab #detail-view {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
        background: #05050f;
    }
    NetworkTab .pane-title {
        color: #6c63ff;
        text-style: bold;
        padding: 0 1;
        background: #0a0a1f;
        height: 3;
        content-align: left middle;
    }
    NetworkTab #host-list {
        height: 25%;
        border-top: solid #1a1a2e;
        overflow-y: auto;
        padding: 0 1;
    }
    NetworkTab .host-entry {
        height: 2;
        padding: 0 1;
        color: #aaaacc;
    }
    NetworkTab .host-entry:hover {
        background: #1a1a3e;
        color: #e0e0ff;
    }
    NetworkTab #scan-output {
        height: 75%;
        background: #0d0d0d;
    }
    """

    def compose(self) -> ComposeResult:
        cfg = load_config()
        with Horizontal(id="top-bar"):
            yield Label("Target:")
            yield Input(
                placeholder="192.168.1.0/24  or  auto-detect",
                id="target-input",
            )
            yield Button("▶ Full Scan",  id="btn-scan-full")
            yield Button("⚡ Quick",     id="btn-scan-quick")
            yield Button("■ Stop",       id="btn-stop-net",  disabled=True)
            yield Button("⬇ Export JSON", id="btn-export",   disabled=True)
            yield Label("Stealth:", id="stealth-label")
            yield Switch(value=False, id="stealth-switch")
            yield Button("?", id="btn-help-net")

        with Horizontal(id="main-area"):
            with Vertical(id="left-pane"):
                yield Static("Scan Output", classes="pane-title")
                yield OutputView(id="scan-output")
                yield Static("Discovered Hosts — click for detail", classes="pane-title")
                yield ScrollableContainer(id="host-list")

            with Vertical(id="right-pane"):
                with TabbedContent(id="right-tabs"):
                    with TabPane("🗺️ Topology", id="tab-topo"):
                        yield Static("[dim]Run a scan to see the network map[/dim]", id="topology-view")
                    with TabPane("🔍 Host Detail", id="tab-detail"):
                        yield Static("[dim]Click a host in the list[/dim]", id="detail-view")

    @on(Button.Pressed, "#btn-scan-full")
    async def on_full_scan(self):
        await self._start_scan(quick=False)

    @on(Button.Pressed, "#btn-scan-quick")
    async def on_quick_scan(self):
        await self._start_scan(quick=True)

    @on(Button.Pressed, "#btn-stop-net")
    async def on_stop(self):
        if hasattr(self, "_scanner"):
            await self._scanner.stop()

    @on(Button.Pressed, "#btn-export")
    async def on_export(self):
        if hasattr(self, "_scanner"):
            path = await self._scanner.export_json()
            self.query_one("#scan-output", OutputView).add_line(f"[+] Exported → {path}", "green")

    @on(Button.Pressed, "#btn-help-net")
    def on_help(self):
        self.post_message(NetworkHelpRequest(HELP_SCAN))

    async def _start_scan(self, quick: bool = False):
        cfg = load_config()
        target = self.query_one("#target-input", Input).value.strip()
        stealth = self.query_one("#stealth-switch", Switch).value
        output = self.query_one("#scan-output", OutputView)

        output.clear_output()
        self.query_one("#btn-scan-full", Button).disabled = True
        self.query_one("#btn-scan-quick", Button).disabled = True
        self.query_one("#btn-stop-net", Button).disabled = False
        self.query_one("#btn-export", Button).disabled = True

        scanner = NetworkScanner(output_dir=cfg.get("output_dir", "/tmp"))
        self._scanner = scanner

        try:
            if quick:
                # Only discovery + basic port scan, skip deep scripts
                async for line in scanner.discover_hosts(target):
                    output.add_line(line)
                    self._update_host_list(scanner)
            else:
                async for line in scanner.full_scan(target, stealth=stealth):
                    output.add_line(line)
                    # Refresh topology after each host is parsed
                    self._update_topology(scanner)
                    self._update_host_list(scanner)
        finally:
            self.query_one("#btn-scan-full", Button).disabled = False
            self.query_one("#btn-scan-quick", Button).disabled = False
            self.query_one("#btn-stop-net", Button).disabled = True
            self.query_one("#btn-export", Button).disabled = False
            self._update_topology(scanner)
            self._update_host_list(scanner)

    def _update_topology(self, scanner: NetworkScanner):
        session = scanner.get_session()
        if session:
            topo_text = render_topology(session, width=80)
            self.query_one("#topology-view", Static).update(topo_text)

    def _update_host_list(self, scanner: NetworkScanner):
        session = scanner.get_session()
        if not session:
            return
        container = self.query_one("#host-list", ScrollableContainer)
        container.remove_children()

        for ip in session.live_hosts:
            host = session.results.get(ip)
            if host:
                port_count = len([s for s in host.services if s.state == "open"])
                cve_count = len(host.cves)
                risk_icon = "🔴" if cve_count > 3 else "🟠" if cve_count > 0 else "🟢"
                label = f"{risk_icon}  {ip:<16}  {port_count} ports  {cve_count} CVEs  {host.os_guess[:20]}"
            else:
                label = f"🟡  {ip:<16}  (not yet scanned)"

            btn = Button(label, id=f"host-{ip.replace('.', '_')}", classes="host-entry")
            container.mount(btn)

    @on(Button.Pressed)
    def on_host_click(self, event: Button.Pressed):
        btn_id = event.button.id or ""
        if btn_id.startswith("host-"):
            ip = btn_id[5:].replace("_", ".")
            if hasattr(self, "_scanner"):
                session = self._scanner.get_session()
                if session and ip in session.results:
                    detail = render_host_detail(session.results[ip])
                    self.query_one("#detail-view", Static).update(detail)
                    self.query_one("#right-tabs", TabbedContent).active = "tab-detail"
