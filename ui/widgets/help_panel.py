from textual.widget import Widget
from textual.widgets import Static, Button
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual import on
from rich.markdown import Markdown
from dataclasses import dataclass


@dataclass
class ToolHelp:
    name: str
    description: str
    usage: str
    danger_note: str
    example: str


class HelpPanel(Widget):
    """Slide-in help panel for tool documentation."""

    DEFAULT_CSS = """
    HelpPanel {
        dock: right;
        width: 40%;
        background: #0f0f1a;
        border-left: solid #6c63ff;
        padding: 1 2;
        display: none;
        layer: overlay;
    }
    HelpPanel.visible {
        display: block;
    }
    HelpPanel #help-close {
        dock: top;
        width: auto;
        background: #6c63ff;
        color: white;
        margin-bottom: 1;
    }
    HelpPanel #help-content {
        overflow-y: auto;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Button("✕ Close [?]", id="help-close")
        yield Static("", id="help-content")

    def show(self, tool_help: ToolHelp):
        content = f"""# {tool_help.name}

{tool_help.description}

---
## Usage
{tool_help.usage}

## Example
```
{tool_help.example}
```

## Risk
{tool_help.danger_note}
"""
        self.query_one("#help-content", Static).update(Markdown(content))
        self.add_class("visible")

    def show_empty(self):
        self.query_one("#help-content", Static).update("Select a tool and press [?] for documentation.")
        self.add_class("visible")

    def hide(self):
        self.remove_class("visible")

    @on(Button.Pressed, "#help-close")
    def on_close(self):
        self.hide()
