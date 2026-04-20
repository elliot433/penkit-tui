from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import on
from textual.message import Message

from core.danger import DangerLevel
from core.config import load as load_config
from ui.widgets.tool_card import ToolCard
from ui.widgets.output_view import OutputView
from ui.widgets.help_panel import ToolHelp
from tools.wifi import WifiScanner, HandshakeCapture, PMKIDAttack, DeauthFlood, EvilTwin
from tools.passwords import HashcatCracker, JohnCracker, detect_hash
from tools.passwords.hydra import HydraCracker
import tools.wifi.scanner as _ws
import tools.wifi.handshake as _wh
import tools.wifi.pmkid as _wp
import tools.wifi.deauth as _wd
import tools.wifi.evil_twin as _wet
import tools.passwords.hashcat as _phc
import tools.passwords.john as _pj
import tools.passwords.hydra as _phydra


TOOL_REGISTRY = {
    "wifi_scan":     (_ws.HELP, _ws.DANGER),
    "wifi_handshake":(_wh.HELP, _wh.DANGER),
    "wifi_pmkid":    (_wp.HELP, _wp.DANGER),
    "wifi_deauth":   (_wd.HELP, _wd.DANGER),
    "wifi_eviltwin": (_wet.HELP, _wet.DANGER),
    "pass_hashcat":  (_phc.HELP, _phc.DANGER),
    "pass_john":     (_pj.HELP, _pj.DANGER),
    "pass_hydra":    (_phydra.HELP, _phydra.DANGER),
}


class HelpRequest(Message):
    def __init__(self, help_info: ToolHelp):
        super().__init__()
        self.help_info = help_info


class ConfirmRequest(Message):
    def __init__(self, tool_id: str, danger: DangerLevel):
        super().__init__()
        self.tool_id = tool_id
        self.danger = danger


class RedTeamTab(Widget):
    DEFAULT_CSS = """
    RedTeamTab {
        layout: horizontal;
        height: 1fr;
    }
    RedTeamTab #tool-list {
        width: 35%;
        border-right: solid #1a1a2e;
        padding: 1;
        overflow-y: auto;
    }
    RedTeamTab #tool-params {
        width: 30%;
        border-right: solid #1a1a2e;
        padding: 1;
        overflow-y: auto;
    }
    RedTeamTab #tool-output {
        width: 35%;
        padding: 1;
    }
    RedTeamTab .section-title {
        color: #6c63ff;
        text-style: bold;
        margin-bottom: 1;
    }
    RedTeamTab .param-label {
        color: #aaaacc;
        margin-top: 1;
    }
    RedTeamTab #btn-stop {
        background: #cc2222;
        color: white;
        margin-top: 1;
    }
    RedTeamTab #btn-run {
        background: #6c63ff;
        color: white;
        margin-top: 1;
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        cfg = load_config()

        with ScrollableContainer(id="tool-list"):
            yield Static("🔴 RED TEAM", classes="section-title")
            yield Static("── WiFi ──", classes="section-title")
            yield ToolCard("wifi_scan",     "WiFi Scanner",          DangerLevel.YELLOW)
            yield ToolCard("wifi_handshake","Handshake Capture",     DangerLevel.ORANGE)
            yield ToolCard("wifi_pmkid",    "PMKID Attack",          DangerLevel.ORANGE)
            yield ToolCard("wifi_deauth",   "Deauth Flood",          DangerLevel.RED)
            yield ToolCard("wifi_eviltwin", "Evil Twin + Portal",    DangerLevel.RED)
            yield Static("── Passwords ──", classes="section-title")
            yield ToolCard("pass_hashcat",  "Hashcat (GPU)",         DangerLevel.YELLOW)
            yield ToolCard("pass_john",     "John the Ripper",       DangerLevel.YELLOW)
            yield ToolCard("pass_hydra",    "Hydra (Network Brute)", DangerLevel.ORANGE)

        with Vertical(id="tool-params"):
            yield Static("Parameters", classes="section-title")
            yield Static("Select a tool to configure →", id="param-hint")
            yield Vertical(id="param-fields")
            with Horizontal():
                yield Button("▶ Run", id="btn-run", disabled=True)
                yield Button("■ Stop", id="btn-stop", disabled=True)

        with Vertical(id="tool-output"):
            yield Static("Output", classes="section-title")
            yield OutputView(id="output")

    def _clear_params(self):
        self.query_one("#param-fields").remove_children()
        self.query_one("#param-hint", Static).display = True
        self.query_one("#btn-run", Button).disabled = True

    def _build_params_wifi_scan(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Interface:", classes="param-label"))
        fields.mount(Input(value=cfg.get("interface", "wlan0"), id="p-iface", placeholder="wlan0"))

    def _build_params_wifi_handshake(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Monitor Interface:", classes="param-label"))
        fields.mount(Input(value=cfg.get("monitor_interface", "wlan0mon"), id="p-mon-iface"))
        fields.mount(Label("Target BSSID:", classes="param-label"))
        fields.mount(Input(placeholder="AA:BB:CC:DD:EE:FF", id="p-bssid"))
        fields.mount(Label("Channel:", classes="param-label"))
        fields.mount(Input(placeholder="6", id="p-channel", value="6"))
        fields.mount(Label("Client MAC (optional):", classes="param-label"))
        fields.mount(Input(placeholder="FF:FF:FF:FF:FF:FF", id="p-client", value="FF:FF:FF:FF:FF:FF"))

    def _build_params_wifi_pmkid(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Interface:", classes="param-label"))
        fields.mount(Input(value=cfg.get("interface", "wlan0"), id="p-iface"))
        fields.mount(Label("Target BSSID (optional):", classes="param-label"))
        fields.mount(Input(placeholder="Leave empty for all APs", id="p-bssid"))

    def _build_params_wifi_deauth(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Monitor Interface:", classes="param-label"))
        fields.mount(Input(value=cfg.get("monitor_interface", "wlan0mon"), id="p-mon-iface"))
        fields.mount(Label("Target BSSID:", classes="param-label"))
        fields.mount(Input(placeholder="AA:BB:CC:DD:EE:FF", id="p-bssid"))
        fields.mount(Label("Client MAC:", classes="param-label"))
        fields.mount(Input(placeholder="FF:FF:FF:FF:FF:FF (all clients)", id="p-client", value="FF:FF:FF:FF:FF:FF"))
        fields.mount(Label("Count (0 = continuous):", classes="param-label"))
        fields.mount(Input(placeholder="0", id="p-count", value="0"))

    def _build_params_wifi_eviltwin(self):
        fields = self.query_one("#param-fields")
        fields.mount(Label("Interface:", classes="param-label"))
        fields.mount(Input(placeholder="wlan0", id="p-iface", value="wlan0"))
        fields.mount(Label("Target SSID:", classes="param-label"))
        fields.mount(Input(placeholder="Network name to clone", id="p-ssid"))
        fields.mount(Label("Channel:", classes="param-label"))
        fields.mount(Input(placeholder="6", id="p-channel", value="6"))

    def _build_params_pass_hashcat(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Hash or hash file path:", classes="param-label"))
        fields.mount(Input(placeholder="5f4dcc3b5aa765d61d8327deb882cf99 or /path/to/hash.txt", id="p-hash"))
        fields.mount(Label("Wordlist:", classes="param-label"))
        fields.mount(Input(value=cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt"), id="p-wordlist"))
        fields.mount(Label("Mode (-1 = auto-detect):", classes="param-label"))
        fields.mount(Input(placeholder="-1", id="p-mode", value="-1"))

    def _build_params_pass_john(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Hash or file path:", classes="param-label"))
        fields.mount(Input(placeholder="hash or /etc/shadow", id="p-hash"))
        fields.mount(Label("Wordlist:", classes="param-label"))
        fields.mount(Input(value=cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt"), id="p-wordlist"))
        fields.mount(Label("Format (auto if empty):", classes="param-label"))
        fields.mount(Input(placeholder="bcrypt / raw-md5 / etc.", id="p-format"))

    def _build_params_pass_hydra(self):
        cfg = load_config()
        fields = self.query_one("#param-fields")
        fields.mount(Label("Target IP:", classes="param-label"))
        fields.mount(Input(placeholder="192.168.1.1", id="p-target"))
        fields.mount(Label("Protocol:", classes="param-label"))
        fields.mount(Input(placeholder="ssh / ftp / rdp / smb / mysql / http-post-form", id="p-proto", value="ssh"))
        fields.mount(Label("Username (or leave empty for defaults):", classes="param-label"))
        fields.mount(Input(placeholder="admin", id="p-user"))
        fields.mount(Label("Password list:", classes="param-label"))
        fields.mount(Input(value=cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt"), id="p-wordlist"))
        fields.mount(Label("Port (0 = default):", classes="param-label"))
        fields.mount(Input(placeholder="0", id="p-port", value="0"))

    PARAM_BUILDERS = {
        "wifi_scan":     _build_params_wifi_scan,
        "wifi_handshake":_build_params_wifi_handshake,
        "wifi_pmkid":    _build_params_wifi_pmkid,
        "wifi_deauth":   _build_params_wifi_deauth,
        "wifi_eviltwin": _build_params_wifi_eviltwin,
        "pass_hashcat":  _build_params_pass_hashcat,
        "pass_john":     _build_params_pass_john,
        "pass_hydra":    _build_params_pass_hydra,
    }

    def _get_input(self, id_: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{id_}", Input).value.strip() or default
        except Exception:
            return default

    @on(ToolCard.Launch)
    def on_launch(self, event: ToolCard.Launch):
        self._active_tool = event.tool_id
        self._clear_params()
        self.query_one("#param-hint", Static).display = False

        builder = self.PARAM_BUILDERS.get(event.tool_id)
        if builder:
            builder(self)

        self.query_one("#btn-run", Button).disabled = False
        help_info, danger = TOOL_REGISTRY.get(event.tool_id, (None, DangerLevel.GREEN))
        if danger in (DangerLevel.ORANGE, DangerLevel.RED, DangerLevel.BLACK):
            self.post_message(ConfirmRequest(event.tool_id, danger))

    @on(ToolCard.Help)
    def on_help(self, event: ToolCard.Help):
        help_info, _ = TOOL_REGISTRY.get(event.tool_id, (None, None))
        if help_info:
            self.post_message(HelpRequest(help_info))

    @on(Button.Pressed, "#btn-run")
    async def on_run(self):
        if not hasattr(self, "_active_tool"):
            return
        output = self.query_one("#output", OutputView)
        output.clear_output()
        self.query_one("#btn-stop", Button).disabled = False
        self.query_one("#btn-run", Button).disabled = True
        await self._run_tool(self._active_tool, output)
        self.query_one("#btn-stop", Button).disabled = True
        self.query_one("#btn-run", Button).disabled = False

    @on(Button.Pressed, "#btn-stop")
    async def on_stop(self):
        if hasattr(self, "_current_tool_obj"):
            await self._current_tool_obj.stop()

    async def _run_tool(self, tool_id: str, output: OutputView):
        cfg = load_config()

        if tool_id == "wifi_scan":
            iface = self._get_input("p-iface", cfg.get("interface", "wlan0"))
            tool = WifiScanner(iface)
            self._current_tool_obj = tool
            async for line in tool.enable_monitor():
                output.add_line(line)
            async for line in tool.scan():
                output.add_line(line)

        elif tool_id == "wifi_handshake":
            iface = self._get_input("p-mon-iface", cfg.get("monitor_interface", "wlan0mon"))
            bssid = self._get_input("p-bssid")
            channel = self._get_input("p-channel", "6")
            if not bssid:
                output.add_line("[ERROR] BSSID required")
                return
            tool = HandshakeCapture(iface, cfg.get("output_dir", "/tmp"))
            self._current_tool_obj = tool
            async for line in tool.capture(bssid, channel):
                output.add_line(line)

        elif tool_id == "wifi_pmkid":
            iface = self._get_input("p-iface", cfg.get("interface", "wlan0"))
            bssid = self._get_input("p-bssid", "")
            tool = PMKIDAttack(iface, cfg.get("output_dir", "/tmp"))
            self._current_tool_obj = tool
            async for line in tool.capture(bssid):
                output.add_line(line)

        elif tool_id == "wifi_deauth":
            iface = self._get_input("p-mon-iface", cfg.get("monitor_interface", "wlan0mon"))
            bssid = self._get_input("p-bssid")
            client = self._get_input("p-client", "FF:FF:FF:FF:FF:FF")
            count = int(self._get_input("p-count", "0"))
            if not bssid:
                output.add_line("[ERROR] BSSID required")
                return
            tool = DeauthFlood(iface)
            self._current_tool_obj = tool
            async for line in tool.flood(bssid, client, count):
                output.add_line(line)

        elif tool_id == "wifi_eviltwin":
            iface = self._get_input("p-iface", "wlan0")
            ssid = self._get_input("p-ssid")
            channel = self._get_input("p-channel", "6")
            if not ssid:
                output.add_line("[ERROR] SSID required")
                return
            tool = EvilTwin(iface, cfg.get("output_dir", "/tmp"))
            self._current_tool_obj = tool
            async for line in tool.start(ssid, channel):
                output.add_line(line)

        elif tool_id == "pass_hashcat":
            hash_val = self._get_input("p-hash")
            wordlist = self._get_input("p-wordlist", cfg.get("wordlist", ""))
            mode = int(self._get_input("p-mode", "-1"))
            if not hash_val:
                output.add_line("[ERROR] Hash or file path required")
                return
            tool = HashcatCracker(wordlist)
            self._current_tool_obj = tool
            async for line in tool.crack(hash_val, mode, wordlist):
                output.add_line(line)

        elif tool_id == "pass_john":
            hash_val = self._get_input("p-hash")
            wordlist = self._get_input("p-wordlist", cfg.get("wordlist", ""))
            fmt = self._get_input("p-format", "")
            if not hash_val:
                output.add_line("[ERROR] Hash or file path required")
                return
            tool = JohnCracker(wordlist)
            self._current_tool_obj = tool
            async for line in tool.crack(hash_val, fmt, wordlist):
                output.add_line(line)

        elif tool_id == "pass_hydra":
            target   = self._get_input("p-target")
            protocol = self._get_input("p-proto", "ssh")
            username = self._get_input("p-user", "")
            wordlist = self._get_input("p-wordlist", cfg.get("wordlist", ""))
            port     = int(self._get_input("p-port", "0"))
            if not target:
                output.add_line("[ERROR] Target IP required")
                return
            tool = HydraCracker()
            self._current_tool_obj = tool
            async for line in tool.crack(target, protocol, username, "", wordlist, port):
                output.add_line(line)
