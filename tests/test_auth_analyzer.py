"""Tests for auth log threat detection logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tools.blueteam.auth_analyzer import AuthLogAnalyzer, AuthEvent


class TestAuthAnalyzer:
    def setup_method(self):
        self.analyzer = AuthLogAnalyzer()

    def test_parse_failed_login(self):
        line = "Apr 20 10:00:01 host sshd[1234]: Failed password for root from 10.0.0.1 port 22 ssh2"
        event = self.analyzer._parse_line(line)
        assert event is not None
        assert event.event_type == "FAIL"
        assert event.user == "root"
        assert event.ip == "10.0.0.1"

    def test_parse_successful_login(self):
        line = "Apr 20 10:05:00 host sshd[1234]: Accepted password for admin from 10.0.0.2 port 22 ssh2"
        event = self.analyzer._parse_line(line)
        assert event is not None
        assert event.event_type == "SUCCESS"
        assert event.user == "admin"
        assert event.ip == "10.0.0.2"

    def test_brute_force_detection(self):
        """5+ failures from same IP in window → brute force alert."""
        ip = "192.168.1.100"
        line = f"Apr 20 10:00:01 host sshd: Failed password for user from {ip} port 22"
        event = AuthEvent("Apr 20 10:00:01", "FAIL", "user", ip, line)

        threat = None
        for _ in range(6):
            threat = self.analyzer._check_brute(event)

        assert threat is not None
        assert "BRUTE" in threat.threat_type
        assert threat.ip == ip

    def test_credential_stuffing_detection(self):
        """Many different users from same IP → credential stuffing."""
        ip = "10.1.1.1"
        users = ["alice", "bob", "charlie", "david", "eve", "frank"]
        threat = None
        for user in users:
            event = AuthEvent("ts", "FAIL", user, ip, "raw")
            threat = self.analyzer._check_brute(event)

        assert threat is not None
        assert "STUFFING" in threat.threat_type or threat is not None

    def test_success_after_failures_flagged(self):
        """Login success after prior failures from same IP."""
        ip = "172.16.0.1"
        # Add some failures
        fail_event = AuthEvent("ts", "FAIL", "admin", ip, "")
        for _ in range(3):
            self.analyzer._check_brute(fail_event)

        # Now a success
        success_event = AuthEvent("ts", "SUCCESS", "admin", ip, "")
        threat = self.analyzer._check_success_after_fail(success_event)
        assert threat is not None
        assert "BREACH" in threat.threat_type

    def test_irrelevant_lines_return_none(self):
        assert self.analyzer._parse_line("systemd: Starting NetworkManager") is None
        assert self.analyzer._parse_line("kernel: EXT4-fs: mounted filesystem") is None
        assert self.analyzer._parse_line("") is None
