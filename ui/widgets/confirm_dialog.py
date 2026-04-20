import asyncio
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input, Label
from textual.containers import Vertical, Horizontal
from textual import on
from core.danger import DangerLevel, DANGER_COLORS, DANGER_CONFIRMATIONS


CONFIRMATION_PHRASE = "I confirm this is authorized"


class ConfirmDialog(ModalScreen[bool]):
    """Danger-level confirmation dialog with progressive security checks."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    ConfirmDialog > Vertical {
        width: 60;
        height: auto;
        background: #0f0f1a;
        border: solid #ff4444;
        padding: 2 3;
    }
    ConfirmDialog #title {
        text-style: bold;
        margin-bottom: 1;
        content-align: center middle;
        width: 100%;
    }
    ConfirmDialog #warning {
        color: #ffaa00;
        margin-bottom: 1;
    }
    ConfirmDialog #countdown {
        color: #ff4444;
        text-style: bold;
        content-align: center middle;
        width: 100%;
        margin-bottom: 1;
    }
    ConfirmDialog #ip-input {
        margin-bottom: 1;
    }
    ConfirmDialog #phrase-input {
        margin-bottom: 1;
    }
    ConfirmDialog .btn-row {
        align: center middle;
        height: 3;
        margin-top: 1;
    }
    ConfirmDialog #btn-confirm {
        background: #cc2222;
        color: white;
        margin-right: 2;
    }
    ConfirmDialog #btn-cancel {
        background: #333355;
        color: white;
    }
    """

    def __init__(self, tool_name: str, danger: DangerLevel):
        super().__init__()
        self.tool_name = tool_name
        self.danger = danger
        self.conf = DANGER_CONFIRMATIONS.get(danger, {})
        self._confirmed = False
        self._countdown_done = False

    def compose(self) -> ComposeResult:
        icon, color, label = DANGER_COLORS[self.danger]
        delay = self.conf.get("delay", 0)

        with Vertical():
            yield Static(f"{icon} [{color}]{label}[/{color}]: {self.tool_name}", id="title")
            yield Static(
                "This tool can cause real harm if used without authorization.\n"
                "Only proceed on systems you own or have written permission to test.",
                id="warning"
            )
            yield Static(f"⏳ Starting in {delay}s...", id="countdown")
            if self.conf.get("require_ip"):
                yield Label("Enter target IP/network:")
                yield Input(placeholder="192.168.1.0/24", id="ip-input")
            if self.conf.get("require_typed"):
                yield Label(f'Type exactly: "{CONFIRMATION_PHRASE}"')
                yield Input(placeholder=CONFIRMATION_PHRASE, id="phrase-input")
            with Horizontal(classes="btn-row"):
                yield Button("CONFIRM", id="btn-confirm", disabled=True)
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self):
        asyncio.get_event_loop().create_task(self._countdown())

    async def _countdown(self):
        delay = self.conf.get("delay", 5)
        for i in range(delay, 0, -1):
            try:
                self.query_one("#countdown", Static).update(f"⏳ Starting in {i}s...")
                await asyncio.sleep(1)
            except Exception:
                return
        try:
            self.query_one("#countdown", Static).update("✅ Ready — fill fields and confirm")
            self._countdown_done = True
            self._check_enable_confirm()
        except Exception:
            pass

    def _check_enable_confirm(self):
        if not self._countdown_done:
            return
        if self.conf.get("require_ip"):
            ip_val = self.query_one("#ip-input", Input).value.strip()
            if not ip_val:
                return
        if self.conf.get("require_typed"):
            phrase_val = self.query_one("#phrase-input", Input).value.strip()
            if phrase_val != CONFIRMATION_PHRASE:
                return
        self.query_one("#btn-confirm", Button).disabled = False

    @on(Input.Changed)
    def on_input_changed(self):
        self._check_enable_confirm()

    @on(Button.Pressed, "#btn-confirm")
    def on_confirm(self):
        self.dismiss(True)

    @on(Button.Pressed, "#btn-cancel")
    def on_cancel(self):
        self.dismiss(False)
