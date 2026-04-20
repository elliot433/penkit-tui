from textual.widget import Widget
from textual.widgets import RichLog
from textual.app import ComposeResult
from rich.text import Text


class OutputView(RichLog):
    """Scrollable terminal output widget with color support."""

    DEFAULT_CSS = """
    OutputView {
        background: #0d0d0d;
        color: #00ff41;
        border: solid #1a1a2e;
        padding: 0 1;
        height: 1fr;
        overflow-y: auto;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, highlight=True, markup=True, wrap=True, **kwargs)

    def add_line(self, text: str, style: str = ""):
        if "[ERROR]" in text:
            self.write(Text(text, style="bold red"))
        elif "[+]" in text or "[SUCCESS]" in text:
            self.write(Text(text, style="bold green"))
        elif "[*]" in text or "[INFO]" in text:
            self.write(Text(text, style="cyan"))
        elif "[!]" in text or "[WARN]" in text:
            self.write(Text(text, style="yellow"))
        elif style:
            self.write(Text(text, style=style))
        else:
            self.write(text)

    def clear_output(self):
        self.clear()
        self.write(Text("─" * 60, style="dim"))
