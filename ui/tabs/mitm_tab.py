from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import on
from textual.message import Message

from core.danger import DangerLevel
from core.config import load as load_config
from ui.widgets.output_view import OutputView
from ui.widgets.tool_card import ToolCard
from ui.widgets.help_panel import ToolHelp
from tools.mitm import BettercapEngine, ResponderEngine
import tools.mitm.bettercap_engine as _mbc
import tools.mitm.responder_engine as _mre


class MitmHelpRequest(Message):
    def __init__(self, info: ToolHelp):
        super().__init__()
        self.help_info = info


class MitmTab(Widget):
    DEFAULT_CSS = """
    MitmTab {
        layout: horizontal;
        height: 1fr;
    }
    MitmTab #mitm-tools { width: 28%; border-right: solid #1a1a2e; padding: 1; overflow-y: auto; }
    MitmTab #mitm-params { width: 30%; border-right: solid #1a1a2e; padding: 1; overflow-y: auto; }
    MitmTab #mitm-output-pane { width: 42%; padding: 1; }
    MitmTab .section-title { color: #aa2222; text-style: bold; margin-bottom: 1; }
    MitmTab .param-label { color: #7777aa; margin-top: 1; }
    MitmTab #mitm-btn-run  { background: #aa2222; color: white; margin-top:1; margin-right:1; }
    MitmTab #mitm-btn-stop { background: #cc2222; color: white; margin-top:1; }
    """

    def compose(self) -> ComposeResult:
        cfg = load_config()
        with ScrollableContainer(id="mitm-tools"):
            yield Static("☠️  MITM", classes="section-title")
            yield ToolCard("arp_spoof",   "ARP Spoof",              DangerLevel.RED)
            yield ToolCard("ssl_strip",   "SSL Strip",              DangerLevel.RED)
            yield ToolCard("dns_poison",  "DNS Poison",             DangerLevel.RED)
            yield ToolCard("cred_harvest","Credential Harvester",   DangerLevel.RED)
            yield ToolCard("responder",   "Responder (NTLM)",       DangerLevel.RED)

        with Vertical(id="mitm-params"):
            yield Static("Parameters", classes="section-title")
            yield Static("Select a tool →", id="mitm-hint")
            yield Vertical(id="mitm-fields")
            with Horizontal():
                yield Button("▶ Run",  id="mitm-btn-run",  disabled=True)
                yield Button("■ Stop", id="mitm-btn-stop", disabled=True)

        with Vertical(id="mitm-output-pane"):
            yield Static("Live Output", classes="section-title")
            yield OutputView(id="mitm-output")

    def _get(self, id_: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{id_}", Input).value.strip() or default
        except Exception:
            return default

    def _clear(self):
        self.query_one("#mitm-fields").remove_children()
        self.query_one("#mitm-hint", Static).display = False
        self.query_one("#mitm-btn-run", Button).disabled = False

    def _base_params(self, extra: list[tuple] = None):
        cfg = load_config()
        f = self.query_one("#mitm-fields")
        f.mount(Label("Interface:", classes="param-label"))
        f.mount(Input(value=cfg.get("interface", "eth0"), id="mitm-iface"))
        f.mount(Label("Victim IP/range (empty = all):", classes="param-label"))
        f.mount(Input(placeholder="192.168.1.50 or 192.168.1.0/24", id="mitm-target"))
        if extra:
            for lbl, ph, id_ in extra:
                f.mount(Label(lbl, classes="param-label"))
                f.mount(Input(placeholder=ph, id=id_))

    @on(ToolCard.Launch)
    def on_launch(self, event: ToolCard.Launch):
        self._active = event.tool_id
        self._clear()
        if event.tool_id == "dns_poison":
            self._base_params([
                ("Domains to hijack:", "*.facebook.com,*.google.com", "mitm-domains"),
                ("Redirect IP:", "your IP (auto if empty)", "mitm-redirect"),
            ])
        elif event.tool_id == "responder":
            f = self.query_one("#mitm-fields")
            cfg = load_config()
            f.mount(Label("Interface:", classes="param-label"))
            f.mount(Input(value=cfg.get("interface", "eth0"), id="mitm-iface"))
        else:
            self._base_params()

    @on(ToolCard.Help)
    def on_help(self, event: ToolCard.Help):
        map_ = {
            "arp_spoof": _mbc.HELP, "ssl_strip": _mbc.HELP,
            "dns_poison": _mbc.HELP, "cred_harvest": _mbc.HELP,
            "responder": _mre.HELP,
        }
        if event.tool_id in map_:
            self.post_message(MitmHelpRequest(map_[event.tool_id]))

    @on(Button.Pressed, "#mitm-btn-run")
    async def on_run(self):
        if not hasattr(self, "_active"):
            return
        out = self.query_one("#mitm-output", OutputView)
        out.clear_output()
        self.query_one("#mitm-btn-stop", Button).disabled = False
        self.query_one("#mitm-btn-run", Button).disabled = True
        await self._run(self._active, out)
        self.query_one("#mitm-btn-stop", Button).disabled = True
        self.query_one("#mitm-btn-run", Button).disabled = False

    @on(Button.Pressed, "#mitm-btn-stop")
    async def on_stop(self):
        if hasattr(self, "_tool"):
            await self._tool.stop()

    async def _run(self, tool_id: str, out: OutputView):
        iface  = self._get("mitm-iface", "eth0")
        target = self._get("mitm-target", "")
        cfg = load_config()

        if tool_id == "responder":
            t = ResponderEngine(iface)
            self._tool = t
            async for l in t.capture():
                out.add_line(l)
            return

        t = BettercapEngine(iface, cfg.get("output_dir", "/tmp"))
        self._tool = t

        if tool_id == "arp_spoof":
            async for l in t.arp_spoof(target):
                out.add_line(l)
        elif tool_id == "ssl_strip":
            async for l in t.ssl_strip(target):
                out.add_line(l)
        elif tool_id == "dns_poison":
            domains  = self._get("mitm-domains", "*")
            redirect = self._get("mitm-redirect", "")
            async for l in t.dns_poison(target, domains, redirect):
                out.add_line(l)
        elif tool_id == "cred_harvest":
            async for l in t.harvest_creds(target):
                out.add_line(l)
