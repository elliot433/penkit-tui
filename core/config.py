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
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def ensure_output_dir(cfg: dict):
    Path(cfg["output_dir"]).mkdir(parents=True, exist_ok=True)
