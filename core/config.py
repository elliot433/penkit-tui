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
    for candidate in [CONFIG_FILE, _FALLBACK_FILE]:
        if candidate.exists():
            try:
                with open(candidate) as f:
                    data = json.load(f)
                return {**DEFAULTS, **data}
            except Exception:
                continue
    return DEFAULTS.copy()


_FALLBACK_FILE = Path(__file__).parent.parent / "penkit_config.json"


def save(cfg: dict):
    for attempt in [CONFIG_FILE, _FALLBACK_FILE]:
        try:
            attempt.parent.mkdir(parents=True, exist_ok=True)
            with open(attempt, "w") as f:
                json.dump(cfg, f, indent=2)
            return
        except Exception:
            continue


def ensure_output_dir(cfg: dict):
    Path(cfg["output_dir"]).mkdir(parents=True, exist_ok=True)
