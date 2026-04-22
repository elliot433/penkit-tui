import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "penkit-tui"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Zentrales Output-Verzeichnis
OUTPUT_ROOT = Path.home() / "penkit-output"

DEFAULTS = {
    "interface": "wlan0",
    "monitor_interface": "wlan0mon",
    "output_dir": str(OUTPUT_ROOT),
    "wifi_dir": str(OUTPUT_ROOT / "wifi"),
    "payloads_dir": str(OUTPUT_ROOT / "payloads"),
    "osint_dir": str(OUTPUT_ROOT / "osint"),
    "wordlist": "/usr/share/wordlists/rockyou.txt",
    "last_target": "",
}


def load() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return DEFAULTS.copy()


def save(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except PermissionError:
        # Config-Datei gehört anderem User (z.B. nach sudo-Run) — Rechte fixen
        try:
            os.chmod(CONFIG_DIR, 0o755)
            if CONFIG_FILE.exists():
                os.chmod(CONFIG_FILE, 0o644)
            with open(CONFIG_FILE, "w") as f:
                json.dump(cfg, f, indent=2)
        except PermissionError:
            # Letzter Ausweg: im Projektverzeichnis speichern
            fallback = Path(__file__).parent.parent / "penkit_config.json"
            with open(fallback, "w") as f:
                json.dump(cfg, f, indent=2)


def ensure_output_dir(cfg: dict):
    Path(cfg["output_dir"]).mkdir(parents=True, exist_ok=True)
