import asyncio
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button, Switch, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import on

from core.danger import DangerLevel
from ui.widgets.output_view import OutputView
from ui.widgets.tool_card import ToolCard
from tools.blueteam import ArpWatcher, PortMonitor, AuthLogAnalyzer, Honeypot


class BlueTeamTab(Widget):
    DEFAULT_CSS = """
    BlueTeamTab {
        layout: horizontal;
        height: 1fr;
    }
    BlueTeamTab #bt-tool-list {
        width: 30%;
        border-right: solid #1a1a2e;
        padding: 1;
        overflow-y: auto;
    }
    BlueTeamTab #bt-params {
        width: 25%;
        border-right: solid #1a1a2e;
        padding: 1;
        overflow-y: auto;
    }
    BlueTeamTab #bt-output {
        width: 45%;
        padding: 1;
    }
    BlueTeamTab .section-title {
        color: #4444cc;
        text-style: bold;
        margin-bottom: 1;
    }
    BlueTeamTab .param-label {
        color: #7777aa;
        margin-top: 1;
    }
    BlueTeamTab #bt-btn-run {
        background: #4444cc;
        color: white;
        margin-top: 1;
        margin-right: 1;
    }
    BlueTeamTab #bt-btn-stop {
        background: #cc2222;
        color: white;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="bt-tool-list"):
            yield Static("🔵 BLUE TEAM", classes="section-title")
            yield ToolCard("arp_watch",    "ARP Spoof Detector",   DangerLevel.GREEN)
            yield ToolCard("auth_scan",    "Auth Log Analyzer",    DangerLevel.GREEN)
            yield ToolCard("auth_live",    "Auth Log — Live Tail", DangerLevel.GREEN)
            yield ToolCard("port_snap",    "Port Snapshot",        DangerLevel.GREEN)
            yield ToolCard("port_diff",    "Port Diff",            DangerLevel.GREEN)
            yield ToolCard("port_live",    "Port Monitor — Live",  DangerLevel.GREEN)
            yield ToolCard("honeypot",     "Honeypot Suite",       DangerLevel.GREEN)

        with Vertical(id="bt-params"):
            yield Static("Parameters", classes="section-title")
            yield Static("Select a tool →", id="bt-param-hint")
            yield Vertical(id="bt-param-fields")
            with Horizontal():
                yield Button("▶ Run",  id="bt-btn-run",  disabled=True)
                yield Button("■ Stop", id="bt-btn-stop", disabled=True)

        with Vertical(id="bt-output"):
            yield Static("Output", classes="section-title")
            yield OutputView(id="bt-output-view")

    def _get_input(self, id_: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{id_}", Input).value.strip() or default
        except Exception:
            return default

    def _clear_params(self):
        self.query_one("#bt-param-fields").remove_children()
        self.query_one("#bt-param-hint", Static).display = False
        self.query_one("#bt-btn-run", Button).disabled = False

    def _build_arp_params(self):
        f = self.query_one("#bt-param-fields")
        f.mount(Label("Interface:", classes="param-label"))
        f.mount(Input(placeholder="eth0", id="bt-iface", value="eth0"))

    def _build_auth_params(self):
        f = self.query_one("#bt-param-fields")
        f.mount(Label("Log path (leave empty for auto):", classes="param-label"))
        f.mount(Input(placeholder="/var/log/auth.log", id="bt-logpath"))

    def _build_honeypot_params(self):
        f = self.query_one("#bt-param-fields")
        f.mount(Label("SSH port (fake):", classes="param-label"))
        f.mount(Input(value="2222", id="bt-hp-ssh"))
        f.mount(Label("HTTP port (fake):", classes="param-label"))
        f.mount(Input(value="8888", id="bt-hp-http"))
        f.mount(Label("FTP port (fake):", classes="param-label"))
        f.mount(Input(value="2121", id="bt-hp-ftp"))
        f.mount(Label("Telnet port (fake):", classes="param-label"))
        f.mount(Input(value="2323", id="bt-hp-telnet"))
        f.mount(Label("Alert threshold (hits/IP):", classes="param-label"))
        f.mount(Input(value="3", id="bt-hp-thresh"))

    PARAM_BUILDERS = {
        "arp_watch":  _build_arp_params,
        "auth_scan":  _build_auth_params,
        "auth_live":  _build_auth_params,
        "port_snap":  None,
        "port_diff":  None,
        "port_live":  None,
        "honeypot":   _build_honeypot_params,
    }

    @on(ToolCard.Launch)
    def on_launch(self, event: ToolCard.Launch):
        self._active_tool = event.tool_id
        self._clear_params()
        builder = self.PARAM_BUILDERS.get(event.tool_id)
        if builder:
            builder(self)

    @on(Button.Pressed, "#bt-btn-run")
    async def on_run(self):
        if not hasattr(self, "_active_tool"):
            return
        output = self.query_one("#bt-output-view", OutputView)
        output.clear_output()
        self.query_one("#bt-btn-stop", Button).disabled = False
        self.query_one("#bt-btn-run", Button).disabled = True
        await self._run_tool(self._active_tool, output)
        self.query_one("#bt-btn-stop", Button).disabled = True
        self.query_one("#bt-btn-run", Button).disabled = False

    @on(Button.Pressed, "#bt-btn-stop")
    async def on_stop(self):
        if hasattr(self, "_current_tool"):
            await self._current_tool.stop()

    async def _run_tool(self, tool_id: str, output: OutputView):
        if tool_id == "arp_watch":
            iface = self._get_input("bt-iface", "eth0")
            tool = ArpWatcher(iface)
            self._current_tool = tool
            async for line in tool.watch():
                output.add_line(line)

        elif tool_id == "auth_scan":
            log_path = self._get_input("bt-logpath", "")
            tool = AuthLogAnalyzer()
            self._current_tool = tool
            async for line in tool.scan_historical(log_path):
                output.add_line(line)

        elif tool_id == "auth_live":
            log_path = self._get_input("bt-logpath", "")
            tool = AuthLogAnalyzer()
            self._current_tool = tool
            async for line in tool.live_tail(log_path):
                output.add_line(line)

        elif tool_id == "port_snap":
            tool = PortMonitor()
            self._current_tool = tool
            async for line in tool.snapshot():
                output.add_line(line)

        elif tool_id == "port_diff":
            tool = PortMonitor()
            self._current_tool = tool
            async for line in tool.diff():
                output.add_line(line)

        elif tool_id == "port_live":
            tool = PortMonitor()
            self._current_tool = tool
            async for line in tool.live_watch():
                output.add_line(line)

        elif tool_id == "honeypot":
            tool = Honeypot(
                ssh_port=int(self._get_input("bt-hp-ssh", "2222")),
                http_port=int(self._get_input("bt-hp-http", "8888")),
                ftp_port=int(self._get_input("bt-hp-ftp", "2121")),
                telnet_port=int(self._get_input("bt-hp-telnet", "2323")),
                alert_threshold=int(self._get_input("bt-hp-thresh", "3")),
            )
            self._current_tool = tool
            async for line in tool.start():
                output.add_line(line)
