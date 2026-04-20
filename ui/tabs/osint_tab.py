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
from tools.osint import OSINTRecon
import tools.osint.recon as _or


class OSINTHelpRequest(Message):
    def __init__(self, info: ToolHelp):
        super().__init__()
        self.help_info = info


class OSINTTab(Widget):
    DEFAULT_CSS = """
    OSINTTab {
        layout: horizontal;
        height: 1fr;
    }
    OSINTTab #osint-tools { width: 28%; border-right: solid #1a1a2e; padding: 1; overflow-y: auto; }
    OSINTTab #osint-params { width: 30%; border-right: solid #1a1a2e; padding: 1; overflow-y: auto; }
    OSINTTab #osint-output-pane { width: 42%; padding: 1; }
    OSINTTab .section-title { color: #22aaaa; text-style: bold; margin-bottom: 1; }
    OSINTTab .param-label { color: #7777aa; margin-top: 1; }
    OSINTTab #osint-btn-run  { background: #22aaaa; color: #000000; margin-top:1; margin-right:1; }
    OSINTTab #osint-btn-stop { background: #cc2222; color: white; margin-top:1; }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="osint-tools"):
            yield Static("🔍 OSINT", classes="section-title")
            yield ToolCard("osint_harvest",  "theHarvester",         DangerLevel.YELLOW)
            yield ToolCard("osint_sherlock", "Sherlock (usernames)", DangerLevel.YELLOW)
            yield ToolCard("osint_subs",     "Subdomain Enum",       DangerLevel.YELLOW)
            yield ToolCard("osint_dorks",    "Google Dorks",         DangerLevel.GREEN)
            yield ToolCard("osint_full",     "Full Recon Pipeline",  DangerLevel.YELLOW)

        with Vertical(id="osint-params"):
            yield Static("Parameters", classes="section-title")
            yield Static("Select a tool →", id="osint-hint")
            yield Vertical(id="osint-fields")
            with Horizontal():
                yield Button("▶ Run",  id="osint-btn-run",  disabled=True)
                yield Button("■ Stop", id="osint-btn-stop", disabled=True)

        with Vertical(id="osint-output-pane"):
            yield Static("Output", classes="section-title")
            yield OutputView(id="osint-output")

    def _get(self, id_: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{id_}", Input).value.strip() or default
        except Exception:
            return default

    def _clear(self):
        self.query_one("#osint-fields").remove_children()
        self.query_one("#osint-hint", Static).display = False
        self.query_one("#osint-btn-run", Button).disabled = False

    @on(ToolCard.Launch)
    def on_launch(self, event: ToolCard.Launch):
        self._active = event.tool_id
        self._clear()
        f = self.query_one("#osint-fields")
        cfg = load_config()

        if event.tool_id == "osint_sherlock":
            f.mount(Label("Username:", classes="param-label"))
            f.mount(Input(placeholder="john_doe", id="osint-username"))
        elif event.tool_id in ("osint_harvest", "osint_subs", "osint_dorks"):
            f.mount(Label("Domain:", classes="param-label"))
            f.mount(Input(placeholder="example.com", id="osint-domain"))
        elif event.tool_id == "osint_full":
            f.mount(Label("Domain:", classes="param-label"))
            f.mount(Input(placeholder="example.com", id="osint-domain"))
            f.mount(Label("Username (optional):", classes="param-label"))
            f.mount(Input(placeholder="john_doe", id="osint-username"))

    @on(ToolCard.Help)
    def on_help(self, event: ToolCard.Help):
        self.post_message(OSINTHelpRequest(_or.HELP))

    @on(Button.Pressed, "#osint-btn-run")
    async def on_run(self):
        if not hasattr(self, "_active"):
            return
        out = self.query_one("#osint-output", OutputView)
        out.clear_output()
        self.query_one("#osint-btn-stop", Button).disabled = False
        self.query_one("#osint-btn-run", Button).disabled = True
        await self._run(self._active, out)
        self.query_one("#osint-btn-stop", Button).disabled = True
        self.query_one("#osint-btn-run", Button).disabled = False

    @on(Button.Pressed, "#osint-btn-stop")
    async def on_stop(self):
        pass  # OSINT tools are not long-running processes that need killing

    async def _run(self, tool_id: str, out: OutputView):
        cfg = load_config()
        recon = OSINTRecon(cfg.get("output_dir", "/tmp"))

        if tool_id == "osint_harvest":
            domain = self._get("osint-domain")
            if not domain:
                out.add_line("[ERROR] Domain required"); return
            async for l in recon.harvest(domain):
                out.add_line(l)

        elif tool_id == "osint_sherlock":
            username = self._get("osint-username")
            if not username:
                out.add_line("[ERROR] Username required"); return
            async for l in recon.sherlock(username):
                out.add_line(l)

        elif tool_id == "osint_subs":
            domain = self._get("osint-domain")
            if not domain:
                out.add_line("[ERROR] Domain required"); return
            async for l in recon.subdomain_enum(domain):
                out.add_line(l)

        elif tool_id == "osint_dorks":
            domain = self._get("osint-domain")
            if not domain:
                out.add_line("[ERROR] Domain required"); return
            async for l in recon.print_dorks(domain):
                out.add_line(l)

        elif tool_id == "osint_full":
            domain = self._get("osint-domain")
            username = self._get("osint-username", "")
            if not domain:
                out.add_line("[ERROR] Domain required"); return
            async for l in recon.full_recon(domain, username):
                out.add_line(l)
