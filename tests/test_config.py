"""Tests for config load/save."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import core.config as cfg_mod


class TestConfig:
    def test_defaults_returned_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg_mod, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(cfg_mod, "CONFIG_DIR",  tmp_path)
        result = cfg_mod.load()
        assert "interface" in result
        assert "wordlist"  in result
        assert result["interface"] == "wlan0"

    def test_save_and_reload(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg_mod, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(cfg_mod, "CONFIG_DIR",  tmp_path)
        cfg_mod.save({"interface": "wlan1", "wordlist": "/custom/path.txt"})
        result = cfg_mod.load()
        assert result["interface"] == "wlan1"
        assert result["wordlist"]  == "/custom/path.txt"

    def test_missing_keys_filled_with_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg_mod, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(cfg_mod, "CONFIG_DIR",  tmp_path)
        cfg_mod.save({"interface": "eth0"})
        result = cfg_mod.load()
        # Keys not saved should fall back to defaults
        assert "wordlist" in result
        assert "output_dir" in result

    def test_corrupt_file_returns_defaults(self, tmp_path, monkeypatch):
        bad_file = tmp_path / "config.json"
        bad_file.write_text("THIS IS NOT JSON {{{{")
        monkeypatch.setattr(cfg_mod, "CONFIG_FILE", bad_file)
        monkeypatch.setattr(cfg_mod, "CONFIG_DIR",  tmp_path)
        result = cfg_mod.load()
        assert result["interface"] == "wlan0"
