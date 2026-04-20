import os
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp
from .hash_detect import detect_hash
from typing import AsyncGenerator


HELP = ToolHelp(
    name="John the Ripper",
    description=(
        "Classic CPU-based password cracker. Great for complex formats, "
        "/etc/shadow, ZIP/RAR files, and formats hashcat doesn't support."
    ),
    usage="Supports auto-detection. Works well on shadow files directly.",
    danger_note="🟡 Low Risk — offline cracking only.",
    example="john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt",
)

DANGER = DangerLevel.YELLOW


class JohnCracker:
    def __init__(self, wordlist: str = "/usr/share/wordlists/rockyou.txt"):
        self.wordlist = wordlist
        self._runner = CommandRunner()

    async def crack(
        self,
        hash_input: str,
        fmt: str = "",
        wordlist: str = "",
    ) -> AsyncGenerator[str, None]:
        wl = wordlist or self.wordlist
        hash_file = "/tmp/penkit_john.txt"
        with open(hash_file, "w") as f:
            f.write(hash_input.strip() + "\n")

        if not fmt:
            matches = detect_hash(hash_input)
            if matches and matches[0].john_format:
                fmt = matches[0].john_format
                yield f"[+] Detected format: {fmt}"

        cmd = ["john", "--wordlist=" + wl, hash_file]
        if fmt:
            cmd.append(f"--format={fmt}")

        yield f"[*] Starting John the Ripper"
        yield f"[*] Wordlist: {os.path.basename(wl)}"

        async for line in self._runner.run(cmd):
            if "password hash" in line.lower() or "g " in line:
                yield f"[+] CRACKED: {line}"
            else:
                yield line

        yield "[*] Showing found passwords:"
        async for line in CommandRunner().run(["john", "--show", hash_file]):
            yield f"[+] {line}"

    async def crack_shadow(self, shadow_file: str, wordlist: str = "") -> AsyncGenerator[str, None]:
        wl = wordlist or self.wordlist
        yield f"[*] Cracking /etc/shadow: {shadow_file}"
        async for line in self._runner.run([
            "john", "--wordlist=" + wl, shadow_file
        ]):
            yield line

    async def crack_zip(self, zip_file: str, wordlist: str = "") -> AsyncGenerator[str, None]:
        wl = wordlist or self.wordlist
        hash_file = "/tmp/penkit_zip.hash"
        yield f"[*] Extracting hash from {zip_file}..."
        async for line in CommandRunner().run(["zip2john", zip_file]):
            if ":" in line:
                with open(hash_file, "w") as f:
                    f.write(line + "\n")
                yield f"[+] Hash extracted"
                break
            yield line

        yield f"[*] Cracking ZIP password..."
        async for line in self._runner.run(["john", "--wordlist=" + wl, hash_file]):
            yield line

    async def stop(self):
        await self._runner.stop()
