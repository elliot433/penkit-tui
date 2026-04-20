"""Tests for hash auto-detection — the most critical offline logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tools.passwords.hash_detect import detect_hash


class TestHashDetect:
    def test_md5_lowercase(self):
        result = detect_hash("5f4dcc3b5aa765d61d8327deb882cf99")
        assert any(r.hash_type == "MD5" for r in result)

    def test_md5_uppercase(self):
        result = detect_hash("5F4DCC3B5AA765D61D8327DEB882CF99")
        assert any(r.hash_type == "MD5" for r in result)

    def test_sha1(self):
        result = detect_hash("5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8")
        assert any(r.hash_type == "SHA1" for r in result)

    def test_sha256(self):
        h = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        result = detect_hash(h)
        assert any(r.hash_type == "SHA256" for r in result)

    def test_sha512(self):
        h = "b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86"
        # 127 chars — not matching sha512 exactly, use valid one
        h = "a" * 128
        result = detect_hash(h)
        assert any(r.hash_type == "SHA512" for r in result)

    def test_bcrypt(self):
        result = detect_hash("$2a$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW")
        assert any(r.hash_type == "bcrypt" for r in result)

    def test_sha512crypt(self):
        h = "$6$rounds=5000$salt$" + "a" * 86
        result = detect_hash(h)
        assert any(r.hash_type == "sha512crypt" for r in result)

    def test_ntlm(self):
        result = detect_hash("$NT$5f4dcc3b5aa765d61d8327deb882cf99")
        assert any(r.hash_type == "NT Hash" for r in result)

    def test_unknown_returns_entry(self):
        result = detect_hash("thisisnotahash")
        assert len(result) > 0
        assert result[0].hash_type == "Unknown"

    def test_hashcat_mode_set(self):
        result = detect_hash("5f4dcc3b5aa765d61d8327deb882cf99")  # MD5
        md5_results = [r for r in result if r.hash_type == "MD5"]
        assert md5_results[0].hashcat_mode == 0

    def test_whitespace_stripped(self):
        result = detect_hash("  5f4dcc3b5aa765d61d8327deb882cf99  ")
        assert any(r.hash_type == "MD5" for r in result)
