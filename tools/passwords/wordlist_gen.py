"""
Smart Wordlist Generator — CUPP-Stil, zielbasiert.

Generiert personalisierte Wortlisten basierend auf:
  - Name, Geburtstag, Partner, Kinder, Haustier
  - Firma, Lieblingsteam, Stadt
  - Domains / Usernames aus OSINT
  - Leet-Speak Varianten (a→4, e→3, i→1, o→0, s→5)
  - Sonderzeichen-Suffixe (!, @, #, 123, 2024, ...)
  - Kombinationen aller Felder

Warum? rockyou.txt versagt bei individuellen Passwörtern.
       Eine zielbasierte Liste mit 5000 Wörtern schlägt rockyou.txt bei
       80% der selbstgewählten Passwörter.

Keine externen Abhängigkeiten — alles Python stdlib.
"""

from __future__ import annotations
import itertools
import os
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator


@dataclass
class TargetProfile:
    """Ziel-Profil für Wordlist-Generierung."""
    # Person
    first_name: str = ""
    last_name: str = ""
    nickname: str = ""
    birthdate: str = ""          # DDMMYYYY oder DD.MM.YYYY oder ähnlich
    partner_name: str = ""
    partner_birthdate: str = ""
    child_names: list[str] = field(default_factory=list)
    pet_names: list[str] = field(default_factory=list)

    # Arbeit / Interesse
    company: str = ""
    job_title: str = ""
    sports_team: str = ""
    hobby: str = ""
    city: str = ""
    country: str = ""

    # Digital
    username: str = ""
    domain: str = ""
    email: str = ""
    phone: str = ""

    # Eigene Wörter
    keywords: list[str] = field(default_factory=list)

    def base_words(self) -> list[str]:
        """Sammelt alle Basis-Wörter aus dem Profil."""
        words = set()

        def add(w: str):
            if w and len(w) >= 2:
                words.add(w.strip())
                words.add(w.strip().lower())
                words.add(w.strip().capitalize())
                words.add(w.strip().upper())

        # Namen
        add(self.first_name)
        add(self.last_name)
        add(self.nickname)
        if self.first_name and self.last_name:
            add(self.first_name + self.last_name)
            add(self.last_name + self.first_name)
            add(self.first_name[0] + self.last_name if self.first_name else "")
            add(self.first_name + self.last_name[0] if self.last_name else "")

        add(self.partner_name)
        for c in self.child_names:
            add(c)
        for p in self.pet_names:
            add(p)

        # Arbeit
        add(self.company)
        add(self.job_title)
        add(self.sports_team)
        add(self.hobby)
        add(self.city)
        add(self.country)

        # Digital
        add(self.username)
        if self.email:
            add(self.email.split("@")[0])
        if self.domain:
            add(self.domain.split(".")[0])
        if self.phone:
            add(re.sub(r'\D', '', self.phone))  # nur Ziffern

        # Eigene Keywords
        for k in self.keywords:
            add(k)

        return [w for w in words if w]


# ── Datum-Varianten ───────────────────────────────────────────────────────────

def _date_variants(datestr: str) -> list[str]:
    """Erstellt viele Varianten aus einem Datum."""
    if not datestr:
        return []

    digits = re.sub(r'\D', '', datestr)
    if len(digits) < 4:
        return []

    variants = []

    if len(digits) >= 8:
        dd   = digits[0:2]
        mm   = digits[2:4]
        yyyy = digits[4:8]
        yy   = yyyy[2:]

        variants += [
            dd + mm + yyyy,   # 15021990
            dd + mm + yy,     # 150290
            mm + dd + yyyy,   # 02151990
            yyyy + mm + dd,   # 19900215
            dd + mm,          # 1502
            mm + yyyy,        # 021990
            dd + yyyy,        # 151990
            yy,               # 90
            yyyy,             # 1990
        ]
    elif len(digits) == 4:
        # Jahr direkt
        variants += [digits, digits[2:]]

    return [v for v in variants if v]


# ── Leet-Speak ────────────────────────────────────────────────────────────────

_LEET = {
    'a': ['4', '@'], 'e': ['3'], 'i': ['1', '!'],
    'o': ['0'], 's': ['5', '$'], 't': ['7'],
    'l': ['1'], 'b': ['8'], 'g': ['9'],
}


def _leet_variants(word: str, max_variants: int = 8) -> list[str]:
    """Erzeugt Leet-Speak-Varianten eines Wortes."""
    if not word or len(word) > 16:
        return []

    results = {word}
    word_lower = word.lower()

    # Einfache Einzel-Substitutionen
    for i, ch in enumerate(word_lower):
        if ch in _LEET:
            for replacement in _LEET[ch]:
                variant = word_lower[:i] + replacement + word_lower[i+1:]
                results.add(variant)
                results.add(variant.capitalize())

    # Doppelte Substitutionen (häufigste: a→4, e→3)
    common = [('a', '4'), ('e', '3'), ('o', '0'), ('i', '1'), ('s', '5')]
    tmp = word_lower
    for char, rep in common:
        tmp = tmp.replace(char, rep)
    if tmp != word_lower:
        results.add(tmp)

    results.discard(word)
    return list(results)[:max_variants]


# ── Suffix/Prefix Listen ──────────────────────────────────────────────────────

_SUFFIXES = [
    "1", "12", "123", "1234", "12345",
    "!", "!!", "123!", "1!", "2024", "2025", "2023", "2022",
    "01", "007", "99", "00", "69",
    "@", "#", "_", ".", "-",
    "1990", "1991", "1992", "1993", "1994", "1995", "1996",
    "1997", "1998", "1999", "2000", "2001", "2002", "2003",
    "2004", "2005",
]

_PREFIXES = [
    "!", "1", "123", "the", "my", "i", "mr", "dr",
]

_COMMON_APPENDS = [
    "password", "pass", "pwd", "pw", "login",
    "admin", "root", "user", "qwerty", "abc", "test",
    "web", "mail", "ftp", "sql", "db",
]


# ── Hauptgenerator ────────────────────────────────────────────────────────────

async def generate(
    profile: TargetProfile,
    output_path: str = "/tmp/penkit_wordlist.txt",
    min_length: int = 6,
    max_length: int = 20,
    include_leet: bool = True,
    include_combinations: bool = True,
    include_dates: bool = True,
) -> AsyncGenerator[str, None]:
    """
    Generiert personalisierte Wordlist aus Ziel-Profil.
    Streamt Fortschritt als async generator.
    """
    yield "[*] Sammle Basis-Wörter..."
    base_words = profile.base_words()
    yield f"[+] {len(base_words)} Basis-Wörter gesammelt"

    all_words: set[str] = set(base_words)

    # Datums-Varianten
    if include_dates:
        yield "[*] Generiere Datums-Varianten..."
        date_strings = []
        for date_field in [profile.birthdate, profile.partner_birthdate]:
            date_strings += _date_variants(date_field)

        # Kombiniere Namen + Datum
        for word in base_words[:30]:  # Top-Wörter
            for date in date_strings[:20]:
                all_words.add(word + date)
                all_words.add(date + word)

        for d in date_strings:
            all_words.add(d)

        yield f"[+] {len(date_strings)} Datums-Varianten"

    # Suffix/Prefix
    yield "[*] Füge Suffixe/Präfixe hinzu..."
    suffix_words = set()
    for word in list(base_words)[:50]:
        for s in _SUFFIXES:
            suffix_words.add(word + s)
            suffix_words.add(word.lower() + s)
            suffix_words.add(word.capitalize() + s)
        for p in _PREFIXES[:5]:
            suffix_words.add(p + word)
    all_words.update(suffix_words)
    yield f"[+] {len(suffix_words)} Suffix-Varianten"

    # Leet-Speak
    if include_leet:
        yield "[*] Generiere Leet-Speak-Varianten..."
        leet_words = set()
        for word in list(base_words)[:40]:
            for lv in _leet_variants(word):
                leet_words.add(lv)
                for s in ["!", "123", "1", "2024"]:
                    leet_words.add(lv + s)
        all_words.update(leet_words)
        yield f"[+] {len(leet_words)} Leet-Varianten"

    # 2-Wort Kombinationen
    if include_combinations and len(base_words) >= 2:
        yield "[*] Generiere Wort-Kombinationen..."
        combo_words = set()
        top = [w for w in base_words if len(w) >= 3][:20]
        for w1, w2 in itertools.combinations(top, 2):
            combo_words.add(w1 + w2)
            combo_words.add(w2 + w1)
            combo_words.add(w1.capitalize() + w2.capitalize())
            for s in ["!", "123", "1"]:
                combo_words.add(w1 + w2 + s)
        all_words.update(combo_words)
        yield f"[+] {len(combo_words)} Kombinationen"

    # Filtern nach Länge
    yield "[*] Filtere nach Länge..."
    filtered = [
        w for w in all_words
        if min_length <= len(w) <= max_length
        and not w.isspace()
    ]
    filtered.sort(key=lambda w: (
        # Priorisierung: kurze mit Sonderzeichen zuerst
        len(w),
        not any(c.isdigit() for c in w),
        not any(c in '!@#$' for c in w),
    ))

    yield f"[*] Schreibe {len(filtered)} Passwörter → {output_path}..."
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered) + "\n")

    size_kb = os.path.getsize(output_path) // 1024
    yield f"[+] Wordlist gespeichert: {output_path} ({size_kb} KB, {len(filtered)} Einträge)"
    yield ""
    yield "════ TOP 10 KANDIDATEN ════"
    for i, w in enumerate(filtered[:10], 1):
        yield f"  {i:>2}. {w}"
    yield ""
    yield f"[*] Nutze mit hashcat:"
    yield f"    hashcat -m <MODE> <HASH> {output_path}"
    yield f"[*] Oder mit hydra:"
    yield f"    hydra -L users.txt -P {output_path} ssh://<TARGET>"
