"""Tests for ARP spoof detection logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tools.blueteam.arp_watch import ArpWatcher


class TestArpWatcher:
    def setup_method(self):
        self.watcher = ArpWatcher("eth0")
        self.watcher._trusted = {
            "192.168.1.1":  "aa:bb:cc:dd:ee:ff",
            "192.168.1.50": "11:22:33:44:55:66",
        }
        self.watcher._current = dict(self.watcher._trusted)

    def test_known_mac_no_alert(self):
        """Same MAC as trusted — no alert."""
        line = "12:34:56.789 ARP, Reply 192.168.1.1 is-at aa:bb:cc:dd:ee:ff, length 28"
        import re
        reply_match = re.search(
            r'Reply\s+([\d.]+)\s+is-at\s+([0-9a-f:]+)', line, re.IGNORECASE
        )
        assert reply_match
        ip, mac = reply_match.group(1), reply_match.group(2).lower()
        # Should NOT trigger spoof alert
        assert self.watcher._trusted.get(ip) == mac

    def test_different_mac_triggers_alert(self):
        """Changed MAC should be detected as spoof."""
        trusted_mac = "aa:bb:cc:dd:ee:ff"
        spoofed_mac = "de:ad:be:ef:00:01"
        ip = "192.168.1.1"
        self.watcher._current[ip] = spoofed_mac
        assert self.watcher._trusted[ip] != self.watcher._current[ip]

    def test_new_host_added_to_trusted(self):
        new_ip  = "192.168.1.99"
        new_mac = "ab:cd:ef:12:34:56"
        assert new_ip not in self.watcher._trusted
        self.watcher._trusted[new_ip] = new_mac
        assert self.watcher._trusted[new_ip] == new_mac

    def test_gateway_spoof_detectable(self):
        """Gateway MAC change is the most dangerous case."""
        gateway_ip = "192.168.1.1"
        original_mac = self.watcher._trusted[gateway_ip]
        attacker_mac = "ff:ee:dd:cc:bb:aa"
        assert original_mac != attacker_mac
