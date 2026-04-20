from textual.widget import Widget
from textual.widgets import Static, Button
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual import on
from core.danger import DangerLevel, DANGER_COLORS


class ToolCard(Widget):
    """A single tool entry with danger badge, launch and help buttons."""

    DEFAULT_CSS = """
    ToolCard {
        height: auto;
        border: solid #1a1a2e;
        margin-bottom: 1;
        padding: 0 1;
        background: #0a0a14;
    }
    ToolCard:hover {
        border: solid #6c63ff;
        background: #0f0f1e;
    }
    ToolCard .tool-header {
        height: 3;
        align: left middle;
    }
    ToolCard .tool-name {
        width: 1fr;
        content-align: left middle;
        color: #e0e0ff;
        text-style: bold;
    }
    ToolCard .tool-danger {
        width: auto;
        content-align: center middle;
        margin-right: 1;
    }
    ToolCard .btn-launch {
        width: auto;
        background: #6c63ff;
        color: white;
        margin-right: 1;
    }
    ToolCard .btn-help {
        width: auto;
        background: #1a1a2e;
        color: #aaaacc;
    }
    """

    class Launch(Message):
        def __init__(self, tool_id: str):
            super().__init__()
            self.tool_id = tool_id

    class Help(Message):
        def __init__(self, tool_id: str):
            super().__init__()
            self.tool_id = tool_id

    def __init__(self, tool_id: str, name: str, danger: DangerLevel, **kwargs):
        super().__init__(**kwargs)
        self.tool_id = tool_id
        self.tool_name = name
        self.danger = danger

    def compose(self) -> ComposeResult:
        icon, color, label = DANGER_COLORS[self.danger]
        with Horizontal(classes="tool-header"):
            yield Static(f"{icon} {self.tool_name}", classes="tool-name")
            yield Static(f"[{color}]{label}[/{color}]", classes="tool-danger")
            yield Button("▶ Run", classes="btn-launch", id=f"launch-{self.tool_id}")
            yield Button("?", classes="btn-help", id=f"help-{self.tool_id}")

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed):
        btn_id = event.button.id or ""
        if btn_id.startswith("launch-"):
            self.post_message(self.Launch(self.tool_id))
        elif btn_id.startswith("help-"):
            self.post_message(self.Help(self.tool_id))
