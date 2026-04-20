import asyncio
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import on
from textual.message import Message

from core.danger import DangerLevel
from core.config import load as load_config
from ui.widgets.output_view import OutputView
from ui.widgets.tool_card import ToolCard
from ui.widgets.help_panel import ToolHelp
from tools.web import WebFingerprinter, SmartFuzzer, SQLInjector, WebVulnScanner
import tools.web.fingerprint as _wf
import tools.web.fuzzer as _wfz
import tools.web.sqli as _wsql
import tools.web.scanner as _wsc


class WebHelpRequest(Message):
    def __init__(self, info: ToolHelp):
        super().__init__()
        self.help_info = info


class WebTab(Widget):
    DEFAULT_CSS = """
    WebTab {
        layout: horizontal;
        height: 1fr;
    }
    WebTab #web-tools {
        width: 28%;
        border-right: solid #1a1a2e;
        padding: 1;
        overflow-y: auto;
    }
    WebTab #web-params {
        width: 30%;
        border-right: solid #1a1a2e;
        padding: 1;
        overflow-y: auto;
    }
    WebTab #web-output-pane {
        width: 42%;
        padding: 1;
    }
    WebTab .section-title {
        color: #cc6600;
        text-style: bold;
        margin-bottom: 1;
    }
    WebTab .param-label { color: #7777aa; margin-top: 1; }
    WebTab #web-btn-run  { background: #cc6600; color: white; margin-top:1; margin-right:1; }
    WebTab #web-btn-stop { background: #cc2222; color: white; margin-top:1; }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="web-tools"):
            yield Static("🌐 WEB ATTACK", classes="section-title")
            yield ToolCard("web_finger",  "Fingerprinter",         DangerLevel.YELLOW)
            yield ToolCard("web_fuzz",    "Smart Fuzzer (ffuf)",   DangerLevel.ORANGE)
            yield ToolCard("web_sqli",    "SQL Injection (sqlmap)",DangerLevel.ORANGE)
            yield ToolCard("web_scan",    "Vuln Scan (nikto+nuclei)",DangerLevel.ORANGE)
            yield ToolCard("web_full",    "Full Auto Scan",        DangerLevel.ORANGE)

        with Vertical(id="web-params"):
            yield Static("Parameters", classes="section-title")
            yield Static("Select a tool →", id="web-hint")
            yield Vertical(id="web-fields")
            with Horizontal():
                yield Button("▶ Run",  id="web-btn-run",  disabled=True)
                yield Button("■ Stop", id="web-btn-stop", disabled=True)

        with Vertical(id="web-output-pane"):
            yield Static("Output", classes="section-title")
            yield OutputView(id="web-output")

    def _get(self, id_: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{id_}", Input).value.strip() or default
        except Exception:
            return default

    def _clear(self):
        self.query_one("#web-fields").remove_children()
        self.query_one("#web-hint", Static).display = False
        self.query_one("#web-btn-run", Button).disabled = False

    def _build_url_params(self, extra_fields: list[tuple[str, str, str]] = None):
        f = self.query_one("#web-fields")
        f.mount(Label("Target URL:", classes="param-label"))
        f.mount(Input(placeholder="https://target.com", id="web-url"))
        if extra_fields:
            for label, placeholder, id_ in extra_fields:
                f.mount(Label(label, classes="param-label"))
                f.mount(Input(placeholder=placeholder, id=id_))

    @on(ToolCard.Launch)
    def on_launch(self, event: ToolCard.Launch):
        self._active = event.tool_id
        self._clear()
        if event.tool_id == "web_fuzz":
            self._build_url_params([
                ("Extensions:", "php,html,txt,js", "web-ext"),
                ("Filter size (noise):", "e.g. 2145", "web-fs"),
            ])
        elif event.tool_id == "web_sqli":
            self._build_url_params([
                ("WAF (if known):", "cloudflare / modsecurity / empty", "web-waf"),
                ("DB name (optional):", "leave empty to auto-detect", "web-db"),
            ])
        elif event.tool_id in ("web_finger", "web_scan", "web_full"):
            self._build_url_params()

    @on(ToolCard.Help)
    def on_help(self, event: ToolCard.Help):
        map_ = {
            "web_finger": _wf.HELP, "web_fuzz": _wfz.HELP,
            "web_sqli": _wsql.HELP, "web_scan": _wsc.HELP,
            "web_full": _wsc.HELP,
        }
        if event.tool_id in map_:
            self.post_message(WebHelpRequest(map_[event.tool_id]))

    @on(Button.Pressed, "#web-btn-run")
    async def on_run(self):
        if not hasattr(self, "_active"):
            return
        out = self.query_one("#web-output", OutputView)
        out.clear_output()
        self.query_one("#web-btn-stop", Button).disabled = False
        self.query_one("#web-btn-run", Button).disabled = True
        await self._run(self._active, out)
        self.query_one("#web-btn-stop", Button).disabled = True
        self.query_one("#web-btn-run", Button).disabled = False

    @on(Button.Pressed, "#web-btn-stop")
    async def on_stop(self):
        if hasattr(self, "_tool"):
            await self._tool.stop()

    async def _run(self, tool_id: str, out: OutputView):
        url = self._get("web-url")
        if not url:
            out.add_line("[ERROR] URL required")
            return

        if tool_id == "web_finger":
            t = WebFingerprinter()
            self._tool = t
            async for l in t.fingerprint(url):
                out.add_line(l)

        elif tool_id == "web_fuzz":
            ext = self._get("web-ext", "php,html,txt")
            fs  = self._get("web-fs", "")
            t = SmartFuzzer()
            self._tool = t
            async for l in t.fuzz_dirs(url, extensions=ext, filter_size=fs):
                out.add_line(l)

        elif tool_id == "web_sqli":
            waf = self._get("web-waf", "")
            db  = self._get("web-db", "")
            t = SQLInjector()
            self._tool = t
            async for l in t.detect(url, waf):
                out.add_line(l)
            if db:
                async for l in t.dump_creds(url, db, waf):
                    out.add_line(l)

        elif tool_id == "web_scan":
            t = WebVulnScanner()
            self._tool = t
            async for l in t.nikto_scan(url):
                out.add_line(l)

        elif tool_id == "web_full":
            # Full chain: fingerprint → fuzz → scan → sqli
            fp = WebFingerprinter()
            self._tool = fp
            out.add_line("[*] ── Phase 1: Fingerprint ──")
            async for l in fp.fingerprint(url):
                out.add_line(l)

            out.add_line("\n[*] ── Phase 2: Directory Fuzz ──")
            fz = SmartFuzzer()
            self._tool = fz
            async for l in fz.fuzz_dirs(url):
                out.add_line(l)

            out.add_line("\n[*] ── Phase 3: Vuln Scan ──")
            sc = WebVulnScanner()
            self._tool = sc
            async for l in sc.nuclei_scan(url):
                out.add_line(l)

            out.add_line("\n[*] ── Phase 4: SQLi Check ──")
            sq = SQLInjector()
            self._tool = sq
            async for l in sq.detect(url):
                out.add_line(l)
