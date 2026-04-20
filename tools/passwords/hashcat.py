import os
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
from .hash_detect import detect_hash
from typing import AsyncGenerator


HELP = ToolHelp(
    name="Hashcat (GPU Cracker)",
    description=(
        "World's fastest password recovery tool using GPU acceleration. "
        "Supports dictionary attacks, rule-based, brute-force, and combination attacks."
    ),
    usage="Provide hash file or single hash. Auto-detects hash type. Uses GPU by default.",
    danger_note="🟡 Low Risk — offline cracking of captured hashes only.",
    example="hashcat -m 22000 handshake.hc22000 rockyou.txt",
)

DANGER = DangerLevel.YELLOW


class HashcatCracker:
    def __init__(self, wordlist: str = "/usr/share/wordlists/rockyou.txt"):
        self.wordlist = wordlist
        self._runner = CommandRunner()

    async def crack(
        self,
        hash_input: str,
        mode: int = -1,
        wordlist: str = "",
        extra_args: list[str] = None,
    ) -> AsyncGenerator[str, None]:
        wl = wordlist or self.wordlist

        if mode == -1:
            matches = detect_hash(hash_input)
            if matches and matches[0].hash_type != "Unknown":
                mode = matches[0].hashcat_mode
                yield f"[+] Detected hash type: {matches[0].hash_type} (mode {mode})"
            else:
                yield "[!] Could not auto-detect hash type. Please specify mode manually."
                return

        hash_file = "/tmp/penkit_hash.txt"
        with open(hash_file, "w") as f:
            f.write(hash_input.strip() + "\n")

        cmd = [
            "hashcat",
            "-m", str(mode),
            "-a", "0",
            hash_file,
            wl,
            "--status",
            "--status-timer=5",
            "--force",
        ]
        if extra_args:
            cmd += extra_args

        yield f"[*] Starting hashcat (mode {mode}) against {os.path.basename(wl)}"
        yield f"[*] Command: {' '.join(cmd)}"

        async for line in self._runner.run(cmd):
            if "Cracked" in line or ":" in line and len(line.split(":")) == 2:
                yield f"[+] CRACKED: {line}"
            elif "Status" in line or "Progress" in line or "Speed" in line:
                yield f"[*] {line}"
            elif "Exhausted" in line:
                yield f"[!] Wordlist exhausted — not found in {os.path.basename(wl)}"
            else:
                yield line

    async def crack_cap(
        self,
        cap_file: str,
        wordlist: str = "",
    ) -> AsyncGenerator[str, None]:
        """Crack WPA2 handshake .cap file directly."""
        wl = wordlist or self.wordlist
        yield f"[*] Cracking WPA2 handshake: {cap_file}"
        yield f"[*] Wordlist: {wl}"

        async for line in self._runner.run([
            "aircrack-ng",
            "-w", wl,
            cap_file,
        ]):
            if "KEY FOUND" in line:
                yield f"[+] {line}"
            else:
                yield line

    async def rules_attack(
        self,
        hash_input: str,
        mode: int,
        wordlist: str = "",
        rules: str = "/usr/share/hashcat/rules/best64.rule",
    ) -> AsyncGenerator[str, None]:
        wl = wordlist or self.wordlist
        hash_file = "/tmp/penkit_hash.txt"
        with open(hash_file, "w") as f:
            f.write(hash_input.strip() + "\n")

        yield f"[*] Rules attack with {os.path.basename(rules)}"
        async for line in self._runner.run([
            "hashcat", "-m", str(mode), "-a", "0",
            "-r", rules,
            hash_file, wl,
            "--status", "--status-timer=5", "--force",
        ]):
            yield line

    async def stop(self):
        await self._runner.stop()
