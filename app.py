from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding
from textual import on

from ui.tabs.red_team import RedTeamTab, HelpRequest, ConfirmRequest
from ui.tabs.network_tab import NetworkTab, NetworkHelpRequest
from ui.tabs.web_tab import WebTab, WebHelpRequest
from ui.tabs.mitm_tab import MitmTab, MitmHelpRequest
from ui.tabs.osint_tab import OSINTTab, OSINTHelpRequest
from ui.tabs.blue_team import BlueTeamTab
from ui.tabs.joker import JokerTab
from ui.widgets.help_panel import HelpPanel
from ui.widgets.confirm_dialog import ConfirmDialog
from core.danger import DangerLevel


class PenKitApp(App):
    TITLE = "PenKit TUI"
    SUB_TITLE = "v3 — Authorized Pentesting Framework"
    CSS_PATH = "assets/app.tcss"

    BINDINGS = [
        Binding("q",     "quit",               "Quit"),
        Binding("ctrl+c","quit",               "Quit"),
        Binding("?",     "toggle_help",        "Help",      show=False),
        Binding("1",     "switch_tab('red')",  "WiFi+Pass", show=True),
        Binding("2",     "switch_tab('net')",  "Network",   show=True),
        Binding("3",     "switch_tab('web')",  "Web",       show=True),
        Binding("4",     "switch_tab('mitm')", "MITM",      show=True),
        Binding("5",     "switch_tab('osint')", "OSINT",    show=True),
        Binding("6",     "switch_tab('blue')", "Blue",      show=True),
        Binding("7",     "switch_tab('joker')", "Joker",    show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(id="tabs"):
            with TabPane("🔴 Red Team",  id="red"):
                yield RedTeamTab()
            with TabPane("🌐 Network",   id="net"):
                yield NetworkTab()
            with TabPane("💻 Web",       id="web"):
                yield WebTab()
            with TabPane("☠️  MITM",     id="mitm"):
                yield MitmTab()
            with TabPane("🔍 OSINT",     id="osint"):
                yield OSINTTab()
            with TabPane("🔵 Blue Team", id="blue"):
                yield BlueTeamTab()
            with TabPane("🃏 Joker",     id="joker"):
                yield JokerTab()
        yield HelpPanel(id="help-panel")
        yield Footer()

    def action_toggle_help(self):
        panel = self.query_one(HelpPanel)
        if "visible" in panel.classes:
            panel.hide()
        else:
            panel.show_empty()

    def action_switch_tab(self, tab_id: str):
        self.query_one("#tabs", TabbedContent).active = tab_id

    # Route all help messages to the help panel
    @on(HelpRequest)
    @on(NetworkHelpRequest)
    @on(WebHelpRequest)
    @on(MitmHelpRequest)
    @on(OSINTHelpRequest)
    def on_any_help(self, event):
        self.query_one(HelpPanel).show(event.help_info)

    @on(ConfirmRequest)
    async def on_confirm_request(self, event: ConfirmRequest):
        if event.danger in (DangerLevel.GREEN, DangerLevel.YELLOW):
            return
        result = await self.push_screen_wait(
            ConfirmDialog(event.tool_id.replace("_", " ").title(), event.danger)
        )
        if not result:
            self.notify("Tool cancelled.", severity="warning")
