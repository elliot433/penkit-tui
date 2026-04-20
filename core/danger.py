from enum import Enum


class DangerLevel(Enum):
    GREEN = 0       # Safe, passive, no authorization needed
    YELLOW = 1      # Low risk, own network only
    ORANGE = 2      # Medium risk — 5s delay + OK
    RED = 3         # High risk — 10s delay + CONFIRM + target IP
    BLACK = 4       # Extreme — 30s + typed sentence + exact description


DANGER_COLORS = {
    DangerLevel.GREEN:  ("🟢", "green",       "Safe"),
    DangerLevel.YELLOW: ("🟡", "yellow",      "Low Risk"),
    DangerLevel.ORANGE: ("🟠", "dark_orange",  "Medium Risk"),
    DangerLevel.RED:    ("🔴", "red",          "High Risk"),
    DangerLevel.BLACK:  ("⛔", "bright_red",   "EXTREME"),
}


DANGER_CONFIRMATIONS = {
    DangerLevel.ORANGE: {"delay": 5,  "require_ok": True,  "require_ip": False, "require_typed": False},
    DangerLevel.RED:    {"delay": 10, "require_ok": True,  "require_ip": True,  "require_typed": False},
    DangerLevel.BLACK:  {"delay": 30, "require_ok": True,  "require_ip": True,  "require_typed": True},
}
