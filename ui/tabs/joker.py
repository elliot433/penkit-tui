from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import on

from core.danger import DangerLevel
from core.config import load as load_config
from ui.widgets.output_view import OutputView
from ui.widgets.tool_card import ToolCard
from tools.joker import KahootFlooder, KahootAutoAnswer, GoogleFormsBomber, SlidoBomber, PrankPayloadGenerator


class JokerTab(Widget):
    DEFAULT_CSS = """
    JokerTab {
        layout: horizontal;
        height: 1fr;
    }
    JokerTab #joker-tools { width: 28%; border-right: solid #1a1a2e; padding: 1; overflow-y: auto; }
    JokerTab #joker-params { width: 30%; border-right: solid #1a1a2e; padding: 1; overflow-y: auto; }
    JokerTab #joker-output-pane { width: 42%; padding: 1; }
    JokerTab .section-title { color: #44cc44; text-style: bold; margin-bottom: 1; }
    JokerTab .section-sub   { color: #228822; margin-bottom: 1; margin-top: 1; }
    JokerTab .param-label   { color: #7777aa; margin-top: 1; }
    JokerTab #joker-btn-run  { background: #228822; color: white; margin-top:1; margin-right:1; }
    JokerTab #joker-btn-stop { background: #cc2222; color: white; margin-top:1; }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="joker-tools"):
            yield Static("🃏 JOKER", classes="section-title")
            yield Static("── Kahoot ──", classes="section-sub")
            yield ToolCard("kahoot_flood",  "Kahoot Flooder",      DangerLevel.YELLOW)
            yield ToolCard("kahoot_answer", "Kahoot Auto-Answer",  DangerLevel.YELLOW)
            yield Static("── Forms ──", classes="section-sub")
            yield ToolCard("gforms_bomb",   "Google Forms Bomber", DangerLevel.YELLOW)
            yield ToolCard("slido_bomb",    "Slido Q&A Flooder",   DangerLevel.YELLOW)
            yield Static("── Pranks ──", classes="section-sub")
            yield ToolCard("prank_bsod",    "Fake BSOD (Win)",     DangerLevel.YELLOW)
            yield ToolCard("prank_virus",   "Fake Virus Scan",     DangerLevel.YELLOW)
            yield ToolCard("prank_update",  "Fake Win Update",     DangerLevel.YELLOW)
            yield ToolCard("prank_rickroll","Rickroll (Win)",      DangerLevel.YELLOW)
            yield ToolCard("prank_100tabs", "100 Browser Tabs",    DangerLevel.YELLOW)
            yield ToolCard("prank_disco",   "Disco Terminal (Lin)",DangerLevel.GREEN)

        with Vertical(id="joker-params"):
            yield Static("Parameters", classes="section-title")
            yield Static("Select a tool →", id="joker-hint")
            yield Vertical(id="joker-fields")
            with Horizontal():
                yield Button("▶ Run",  id="joker-btn-run",  disabled=True)
                yield Button("■ Stop", id="joker-btn-stop", disabled=True)

        with Vertical(id="joker-output-pane"):
            yield Static("Output", classes="section-title")
            yield OutputView(id="joker-output")

    def _get(self, id_: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{id_}", Input).value.strip() or default
        except Exception:
            return default

    def _clear(self):
        self.query_one("#joker-fields").remove_children()
        self.query_one("#joker-hint", Static).display = False
        self.query_one("#joker-btn-run", Button).disabled = False

    @on(ToolCard.Launch)
    def on_launch(self, event: ToolCard.Launch):
        self._active = event.tool_id
        self._clear()
        f = self.query_one("#joker-fields")

        if event.tool_id == "kahoot_flood":
            f.mount(Label("Kahoot Game PIN:", classes="param-label"))
            f.mount(Input(placeholder="1234567", id="j-pin"))
            f.mount(Label("Number of bots:", classes="param-label"))
            f.mount(Input(value="100", id="j-count"))
            f.mount(Label("Name prefix (optional):", classes="param-label"))
            f.mount(Input(placeholder="Bot (random if empty)", id="j-prefix"))
            f.mount(Label("Delay between bots (ms):", classes="param-label"))
            f.mount(Input(value="100", id="j-delay"))

        elif event.tool_id == "kahoot_answer":
            f.mount(Label("Kahoot Game PIN:", classes="param-label"))
            f.mount(Input(placeholder="1234567", id="j-pin"))
            f.mount(Label("Bot name:", classes="param-label"))
            f.mount(Input(placeholder="(random)", id="j-name"))

        elif event.tool_id == "gforms_bomb":
            f.mount(Label("Google Form URL:", classes="param-label"))
            f.mount(Input(placeholder="https://docs.google.com/forms/d/e/.../viewform", id="j-url"))
            f.mount(Label("Submission count:", classes="param-label"))
            f.mount(Input(value="50", id="j-count"))
            f.mount(Label("Custom answer (optional):", classes="param-label"))
            f.mount(Input(placeholder="(random words if empty)", id="j-answer"))
            f.mount(Label("Delay between submissions (ms):", classes="param-label"))
            f.mount(Input(value="300", id="j-delay"))

        elif event.tool_id == "slido_bomb":
            f.mount(Label("Slido Event ID:", classes="param-label"))
            f.mount(Input(placeholder="abc123", id="j-event-id"))
            f.mount(Label("Custom question (optional):", classes="param-label"))
            f.mount(Input(placeholder="(random questions if empty)", id="j-question"))
            f.mount(Label("Submission count:", classes="param-label"))
            f.mount(Input(value="20", id="j-count"))

        elif event.tool_id in ("prank_bsod", "prank_virus", "prank_update",
                               "prank_rickroll", "prank_100tabs", "prank_disco"):
            f.mount(Label("Delay before activation (sec, 0=instant):", classes="param-label"))
            f.mount(Input(value="0", id="j-delay-sec"))
            if event.tool_id == "prank_100tabs":
                f.mount(Label("Number of tabs:", classes="param-label"))
                f.mount(Input(value="100", id="j-tabs-count"))
            f.mount(Label("Output directory:", classes="param-label"))
            cfg = load_config()
            f.mount(Input(value=cfg.get("output_dir", "/tmp"), id="j-out-dir"))

    @on(Button.Pressed, "#joker-btn-run")
    async def on_run(self):
        if not hasattr(self, "_active"):
            return
        out = self.query_one("#joker-output", OutputView)
        out.clear_output()
        self.query_one("#joker-btn-stop", Button).disabled = False
        self.query_one("#joker-btn-run", Button).disabled = True
        await self._run(self._active, out)
        self.query_one("#joker-btn-stop", Button).disabled = True
        self.query_one("#joker-btn-run", Button).disabled = False

    @on(Button.Pressed, "#joker-btn-stop")
    async def on_stop(self):
        if hasattr(self, "_tool"):
            await self._tool.stop()

    async def _run(self, tool_id: str, out: OutputView):
        cfg = load_config()

        if tool_id == "kahoot_flood":
            pin    = self._get("j-pin")
            count  = int(self._get("j-count", "100"))
            prefix = self._get("j-prefix", "")
            delay  = int(self._get("j-delay", "100"))
            if not pin:
                out.add_line("[ERROR] Kahoot PIN required"); return
            t = KahootFlooder()
            self._tool = t
            async for l in t.flood(pin, count, prefix, delay):
                out.add_line(l)

        elif tool_id == "kahoot_answer":
            pin  = self._get("j-pin")
            name = self._get("j-name", "")
            if not pin:
                out.add_line("[ERROR] Kahoot PIN required"); return
            t = KahootAutoAnswer()
            self._tool = t
            async for l in t.run(pin, name):
                out.add_line(l)

        elif tool_id == "gforms_bomb":
            url    = self._get("j-url")
            count  = int(self._get("j-count", "50"))
            answer = self._get("j-answer", "")
            delay  = int(self._get("j-delay", "300"))
            if not url:
                out.add_line("[ERROR] Form URL required"); return
            t = GoogleFormsBomber()
            self._tool = t
            async for l in t.bomb_google(url, count, answer, delay):
                out.add_line(l)

        elif tool_id == "slido_bomb":
            event_id = self._get("j-event-id")
            question = self._get("j-question", "")
            count    = int(self._get("j-count", "20"))
            if not event_id:
                out.add_line("[ERROR] Slido Event ID required"); return
            t = SlidoBomber()
            self._tool = t
            async for l in t.flood_qa(event_id, question, count):
                out.add_line(l)

        else:
            # Prank payload generators
            prank_map = {
                "prank_bsod":    "fake_bsod",
                "prank_virus":   "fake_virus_win",
                "prank_update":  "fake_update",
                "prank_rickroll":"rickroll",
                "prank_100tabs": "100_tabs",
                "prank_disco":   "disco_terminal",
            }
            prank_id = prank_map.get(tool_id, "")
            if not prank_id:
                out.add_line("[ERROR] Unknown prank"); return

            delay_sec  = int(self._get("j-delay-sec", "0"))
            custom     = self._get("j-tabs-count", "")
            out_dir    = self._get("j-out-dir", cfg.get("output_dir", "/tmp"))

            gen = PrankPayloadGenerator()
            async for l in gen.generate(prank_id, out_dir, delay_sec, custom):
                out.add_line(l)
