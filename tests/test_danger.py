"""Tests for danger level system."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.danger import DangerLevel, DANGER_COLORS, DANGER_CONFIRMATIONS


class TestDangerSystem:
    def test_all_levels_have_colors(self):
        for level in DangerLevel:
            assert level in DANGER_COLORS
            icon, color, label = DANGER_COLORS[level]
            assert icon
            assert color
            assert label

    def test_orange_requires_ok_no_ip(self):
        conf = DANGER_CONFIRMATIONS[DangerLevel.ORANGE]
        assert conf["require_ok"] is True
        assert conf["require_ip"] is False
        assert conf["require_typed"] is False
        assert conf["delay"] == 5

    def test_red_requires_ip(self):
        conf = DANGER_CONFIRMATIONS[DangerLevel.RED]
        assert conf["require_ip"] is True
        assert conf["require_typed"] is False
        assert conf["delay"] == 10

    def test_black_requires_everything(self):
        conf = DANGER_CONFIRMATIONS[DangerLevel.BLACK]
        assert conf["require_ok"] is True
        assert conf["require_ip"] is True
        assert conf["require_typed"] is True
        assert conf["delay"] == 30

    def test_green_yellow_not_in_confirmations(self):
        assert DangerLevel.GREEN  not in DANGER_CONFIRMATIONS
        assert DangerLevel.YELLOW not in DANGER_CONFIRMATIONS

    def test_level_ordering(self):
        assert DangerLevel.GREEN.value  < DangerLevel.YELLOW.value
        assert DangerLevel.YELLOW.value < DangerLevel.ORANGE.value
        assert DangerLevel.ORANGE.value < DangerLevel.RED.value
        assert DangerLevel.RED.value    < DangerLevel.BLACK.value
