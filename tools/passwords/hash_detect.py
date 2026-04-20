import re
from dataclasses import dataclass


@dataclass
class HashInfo:
    hash_type: str
    hashcat_mode: int
    john_format: str
    description: str


HASH_PATTERNS: list[tuple[re.Pattern, HashInfo]] = [
    (re.compile(r'^\$2[ayb]\$.{56}$'),
     HashInfo("bcrypt", 3200, "bcrypt", "bcrypt (cost factor in hash)")),

    (re.compile(r'^\$6\$.{8,16}\$.{86}$'),
     HashInfo("sha512crypt", 1800, "sha512crypt", "SHA-512 crypt (Linux /etc/shadow)")),

    (re.compile(r'^\$5\$.{8,16}\$.{43}$'),
     HashInfo("sha256crypt", 7400, "sha256crypt", "SHA-256 crypt")),

    (re.compile(r'^\$1\$.{0,8}\$.{22}$'),
     HashInfo("md5crypt", 500, "md5crypt", "MD5 crypt (old Linux)")),

    (re.compile(r'^[a-f0-9]{32}$', re.I),
     HashInfo("MD5", 0, "raw-md5", "MD5 (32 hex chars)")),

    (re.compile(r'^[a-f0-9]{40}$', re.I),
     HashInfo("SHA1", 100, "raw-sha1", "SHA-1 (40 hex chars)")),

    (re.compile(r'^[a-f0-9]{64}$', re.I),
     HashInfo("SHA256", 1400, "raw-sha256", "SHA-256 (64 hex chars)")),

    (re.compile(r'^[a-f0-9]{128}$', re.I),
     HashInfo("SHA512", 1700, "raw-sha512", "SHA-512 (128 hex chars)")),

    (re.compile(r'^[a-f0-9]{56}$', re.I),
     HashInfo("SHA224", 1300, "raw-sha224", "SHA-224 (56 hex chars)")),

    (re.compile(r'^[a-f0-9]{96}$', re.I),
     HashInfo("SHA384", 10800, "dynamic_380", "SHA-384 (96 hex chars)")),

    (re.compile(r'^\$NT\$[a-f0-9]{32}$', re.I),
     HashInfo("NT Hash", 1000, "nt", "Windows NT Hash")),

    (re.compile(r'^[a-f0-9]{32}:[a-f0-9]{32}$', re.I),
     HashInfo("NTLM", 1000, "nt", "NTLM Hash")),

    (re.compile(r'^\$P\$[a-zA-Z0-9./]{31}$'),
     HashInfo("phpass", 400, "phpass", "phpBB / WordPress password hash")),

    (re.compile(r'^\$apr1\$.{0,8}\$.{22}$'),
     HashInfo("md5apr1", 1600, "md5crypt-long", "Apache MD5-APR1")),

    (re.compile(r'^[a-zA-Z0-9+/]{27}=$'),
     HashInfo("SHA1 (Base64)", 101, "raw-sha1", "SHA-1 Base64 encoded")),

    (re.compile(r'^[a-f0-9]{16}$', re.I),
     HashInfo("MySQL3.x", 200, "mysql", "MySQL 3.x password hash")),

    (re.compile(r'^\*[A-F0-9]{40}$'),
     HashInfo("MySQL4.1+", 300, "mysql-sha1", "MySQL 4.1+ password hash")),

    (re.compile(r'^[a-zA-Z0-9]{13}$'),
     HashInfo("DES crypt", 1500, "descrypt", "Traditional DES crypt (13 chars)")),

    (re.compile(r'^\$sha1\$\d+\$[a-zA-Z0-9./]{0,48}\$[a-zA-Z0-9./]{28}$'),
     HashInfo("SHA1 crypt (NetBSD)", 5800, "sha1crypt", "SHA-1 crypt NetBSD style")),

    (re.compile(r'^[a-f0-9]{48}$', re.I),
     HashInfo("SHA1 (half)", 110, "dynamic_26", "Possible SHA-1 with salt truncated")),

    (re.compile(r'^[a-zA-Z0-9+/]{43}=$'),
     HashInfo("SHA256 (Base64)", 1401, "dynamic_62", "SHA-256 Base64")),
]


def detect_hash(hash_str: str) -> list[HashInfo]:
    """Return all matching hash types for a given hash string."""
    hash_str = hash_str.strip()
    matches = []
    for pattern, info in HASH_PATTERNS:
        if pattern.match(hash_str):
            matches.append(info)
    if not matches:
        matches.append(HashInfo(
            hash_type="Unknown",
            hashcat_mode=-1,
            john_format="",
            description=f"No pattern matched. Length: {len(hash_str)} chars",
        ))
    return matches
